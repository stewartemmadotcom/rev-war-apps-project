#!/usr/bin/env python3
"""
Step 3: How does one passage vary from file to file?
====================================================

Finds every pension file that contains most of the words of START (a few
words from the passage you want to follow), puts them in rough date order,
and compares each version with the one before it: how similar they are, and
which words were added or cut.

Spelling and transcription differences are fine: a file only needs SHARE of
START's 3-word phrases. Each file is cut down to the sentence that best
matches START plus the next ones.

The files have no date field, so each version is dated by the "On this ...
day of <Month> <year>" heading of the declaration it sits in (see
date_near()), with the year in figures or in words ("eighteen hundred &
thirty eight"). Years before 1818 and "18th day of March 1818", the
residence date in the 1818 act's oath, are skipped. Versions with no date go
last. Treat the order as rough.

The page (output/03_trace.html) shows every version, with the changes from
the version before highlighted, and opens in your browser.
"""

import difflib
import html
import re
import webbrowser

from common import (CORPUS_FOLDER, OUTPUT_FOLDER, SCRIPT_DIR, jaccard, phrases, read_metadata,
                    read_text)

# --- Change these --------------------------------------------------------------

# The 1820 act's property oath: the passage found in the most files by step 2
START = "have not since that time by gift sale or in any manner whatever disposed of my property"
# Other passages to try (from output/02_families.csv):
#   one witness's affidavit in three families' files (W5046, W5635, W5636):
#     "personally appeared Mr. William Arthur a respectable resident of the County of Henry"
#   the North Carolina Secretary of State's certificate of service:
#     "do hereby certify that it appears from the muster-rolls of the Continental line"
#   a widow's declaration under the act of 7 July 1838:
#     "doth on her oath make the following declaration in order to obtain the benefit"
SHARE = 0.6             # share of START's 3-word phrases a file must contain
SENTENCES = 2           # how many sentences to show, starting with the match

OPEN_IN_BROWSER = True

# -------------------------------------------------------------------------------

TOKEN = re.compile(r"\S+")
MONTHS = ("January|February|March|April|May|June|July|August|September|October|"
          "November|December|Jan|Feb|Mar|Apr|Aug|Sept?|Oct|Nov|Dec")

# Years written in words: "eighteen hundred & thirty eight",
# "one thousand eight hundred and forty", "Eighteen hundred and thirty-nine"
UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9}
TEENS = {"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
         "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fourty": 40, "fifty": 50, "sixty": 60,
        "seventy": 70, "eighty": 80, "ninety": 90}
CENTURY = r"(?:one thousand,? (?:seven|eight) hundred|(?:seventeen|eighteen) hundred)"
WORD_YEAR = (rf"{CENTURY}(?:,? (?:and|&) |,? )?"
             rf"(?:(?:{'|'.join(TENS)})(?:[- ](?:{'|'.join(UNITS)}))?|"
             rf"{'|'.join(TEENS)}|{'|'.join(UNITS)})?")
DATE = re.compile(rf"day,? (?:of )?({MONTHS})[a-z']*\.?,? (?:in the year (?:of our Lord )?|A\.? ?D\.?,? )?"
                  rf"(1[78]\d\d|{WORD_YEAR})\b", re.IGNORECASE)


def to_year(written):
    """'1838' or 'eighteen hundred & thirty eight' -> 1838."""
    if written.isdigit():
        return int(written)
    words = re.findall(r"[a-z]+", written.lower())
    year = 1700 if "seven" in words[:2] or "seventeen" in words[:1] else 1800
    rest = words[words.index("hundred") + 1:]
    for word in rest:
        year += UNITS.get(word, 0) + TEENS.get(word, 0) + TENS.get(word, 0)
    return year


def sentences_of(text):
    return re.split(r"(?<=[.:;])\s+", text)


def excerpt(text, target):
    """The sentence that best matches START, the ones after it, and where it starts."""
    sentences = sentences_of(text)
    scores = [len(target & phrases(s, 3)) for s in sentences]
    best = scores.index(max(scores))
    start = len(" ".join(sentences[:best]))
    return " ".join(sentences[best:best + SENTENCES]), start


def date_near(text, start):
    """A year for the passage at position start. Only years from 1818 on
    count (the pension acts start then; earlier dates are usually service
    dates). In order of preference:
      1. the nearest "On this ... day of <Month> <year>" before the passage
         or in its first lines: the heading of the declaration it belongs to ("sworn on the day and
         year above written")
      2. the nearest "this ... day of" date after it (a dated signature)
      3. the nearest date of any kind (a death, a marriage)"""
    candidates = []
    for m in DATE.finditer(text, max(start - 4000, 0), start + 3000):
        year = to_year(m.group(2))
        if year < 1818 or (m.group(1).lower().startswith("mar") and year == 1818):
            continue
        dated_paper = re.search(r"\bthis\b", text[max(m.start() - 25, 0):m.start()], re.I)
        if dated_paper and m.start() < start + 400:   # the heading, or in the first lines
            rank = (0, abs(start - m.start()))
        elif dated_paper and m.start() - start < 3000:
            rank = (1, m.start() - start)
        elif abs(m.start() - start) < 1000:
            rank = (2, abs(m.start() - start))
        else:
            continue
        candidates.append((rank, year))
    return min(candidates)[1] if candidates else 9999


def changes(old, new):
    """The new text as HTML: words added since the old version in green,
    words cut from it in red (struck through)."""
    a, b = TOKEN.findall(old), TOKEN.findall(new)
    out = []
    matcher = difflib.SequenceMatcher(None, [w.lower() for w in a], [w.lower() for w in b],
                                      autojunk=False)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        if op == "equal":
            out.append(html.escape(" ".join(b[j1:j2])))
            continue
        if i2 > i1:
            out.append(f'<del>{html.escape(" ".join(a[i1:i2]))}</del>')
        if j2 > j1:
            out.append(f'<ins>{html.escape(" ".join(b[j1:j2]))}</ins>')
    return " ".join(out)


def main():
    people = read_metadata()
    target = phrases(START, 3)
    found = []
    for path in sorted(CORPUS_FOLDER.glob("*.txt")):
        text = read_text(path)
        shared = target & phrases(text, 3)
        if len(shared) / len(target) >= SHARE:
            code = path.stem.upper()
            passage, start = excerpt(text, target)
            name = people.get(code, {}).get("name", "")
            found.append({"code": code, "name": name, "year": date_near(text, start),
                          "text": passage})
    found.sort(key=lambda f: (f["year"], f["code"]))
    if not found:
        print("No files found. Try a lower SHARE or different words in START.")
        return

    print(f"\"{START}\": {len(found)} files\n")
    parts, previous = [], None
    for f in found:
        year = str(f["year"]) if f["year"] != 9999 else "n.d."
        label = f"{year}  {f['code']} ({f['name']})"
        if previous is None:
            similarity, body = "", html.escape(f["text"])
            print(f"  {label:40s}       {f['text'][:80]}")
        else:
            score = jaccard(phrases(previous, 3), phrases(f["text"], 3))
            similarity = f" &middot; 3-gram Jaccard with the version before: {score:.2f}"
            body = changes(previous, f["text"])
            print(f"  {label:40s} {score:.2f}  {f['text'][:80]}")
        url = f"https://revwarapps.org/{f['code'].lower()}.pdf"
        parts.append(f"<h2>{html.escape(label)}</h2>"
                     f"<p class='title'><a href='{url}'>{url}</a>{similarity}</p><p>{body}</p>")
        previous = f["text"]

    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(START)}</title>
<style>
 body {{ font-family: Georgia, serif; max-width: 900px; margin: 2em auto; padding: 0 1em;
        line-height: 1.6; color: #141d2e; }}
 h1, h2, .title {{ font-family: Helvetica, Arial, sans-serif; }}
 h2 {{ margin-top: 2em; border-top: 1px solid #ddd; padding-top: 1em; }}
 .title {{ color: #555; font-size: 0.9em; }}
 ins {{ background: #c6f6d5; text-decoration: none; }}
 del {{ background: #fed7d7; }}
</style></head><body>
<h1>“{html.escape(START)}”</h1>
<p>{len(found)} files, in rough date order. <ins>Green</ins>: added since the version before.
<del>Red</del>: cut since the version before.</p>
{''.join(parts)}
</body></html>"""
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    path = OUTPUT_FOLDER / "03_trace.html"
    path.write_text(page, encoding="utf-8")
    print(f"\nSaved {path.relative_to(SCRIPT_DIR)}")
    if OPEN_IN_BROWSER:
        webbrowser.open(path.resolve().as_uri())


if __name__ == "__main__":
    main()
