#!/usr/bin/env python3
"""
Step 4: Which words of each declaration are form, and which are hers?
=====================================================================

Uses the boilerplate phrases from step 2 (output/02_boilerplate.csv: 5-word
phrases in more than BOILERPLATE of the files; DECISIONS.md 3.1). Every word of
a widow's declaration that falls inside one of those phrases is form; the rest
is what the form leaves to her (and to the clerk writing it down): names,
places, dates, her memories of his service, her reasons.

Results:
  output/04_form_share.csv  every file: words, form words, share that is form
  output/04_form_view.html  SAMPLE declarations with the form greyed out, to read

Run 02_reuse_minhash.py first.
"""

import csv
import html
import random
import re
import statistics

from common import CORPUS_FOLDER, OUTPUT_FOLDER, SCRIPT_DIR, WORD, read_metadata, read_text

# --- Change these --------------------------------------------------------------

N = 5           # words per phrase (same as step 2)
SAMPLE = 25     # declarations shown in the HTML page
SEED = 1        # which ones (change for a different sample)

# -------------------------------------------------------------------------------

BOILERPLATE_CSV = OUTPUT_FOLDER / "02_boilerplate.csv"


def form_mask(words, formulas):
    """True for each word inside a boilerplate phrase."""
    mask = [False] * len(words)
    for i in range(len(words) - N + 1):
        if " ".join(words[i:i + N]) in formulas:
            for j in range(i, i + N):
                mask[j] = True
    return mask


def marked_html(text, formulas):
    """The text with form words in <span class=form>; everything else as it is."""
    spans = list(WORD.finditer(text.lower()))
    mask = form_mask([m.group(0) for m in spans], formulas)
    out, pos = [], 0
    for m, is_form in zip(spans, mask):
        out.append(html.escape(text[pos:m.start()]))
        word = html.escape(text[m.start():m.end()])
        out.append(f'<span class="form">{word}</span>' if is_form else word)
        pos = m.end()
    out.append(html.escape(text[pos:]))
    return "".join(out)


def main():
    if not BOILERPLATE_CSV.exists():
        raise SystemExit("Run 02_reuse_minhash.py first: it writes output/02_boilerplate.csv.")
    with open(BOILERPLATE_CSV, newline="", encoding="utf-8") as f:
        formulas = {row["phrase"] for row in csv.DictReader(f)}
    print(f"{len(formulas):,} boilerplate phrases from step 2")

    people = read_metadata()
    rows, texts = [], {}
    for path in sorted(CORPUS_FOLDER.glob("*.txt")):
        code = path.stem.upper()
        text = read_text(path)
        words = WORD.findall(text.lower())
        if not words:
            continue
        form = sum(form_mask(words, formulas))
        rows.append({"code": code, "name": people.get(code, {}).get("name", ""),
                     "words": len(words), "form_words": form,
                     "form_share": round(form / len(words), 3)})
        texts[code] = text

    OUTPUT_FOLDER.mkdir(exist_ok=True)
    with open(OUTPUT_FOLDER / "04_form_share.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    shares = [r["form_share"] for r in rows]
    total, form = sum(r["words"] for r in rows), sum(r["form_words"] for r in rows)
    q = statistics.quantiles(shares, n=4)
    print(f"{len(rows):,} files, {total:,} words; {form / total:.0%} of all words are form")
    print(f"Share of a declaration that is form: median {statistics.median(shares):.0%} "
          f"(middle half {q[0]:.0%} to {q[2]:.0%})")
    print("Most form (almost all template):")
    for r in sorted(rows, key=lambda r: -r["form_share"])[:5]:
        print(f"   {r['form_share']:4.0%}  {r['code']} {r['name']} ({r['words']} words)")
    print("Least form (mostly her own account, or a letter):")
    for r in sorted(rows, key=lambda r: r["form_share"])[:5]:
        print(f"   {r['form_share']:4.0%}  {r['code']} {r['name']} ({r['words']} words)")

    sample = random.Random(SEED).sample(rows, min(SAMPLE, len(rows)))
    parts = []
    for r in sorted(sample, key=lambda r: r["form_share"]):
        parts.append(f"<h2>{html.escape(r['code'])} {html.escape(r['name'])} "
                     f"<small>{r['form_share']:.0%} form, {r['words']} words</small></h2>"
                     f"<p>{marked_html(texts[r['code']], formulas)}</p>")
    page = f"""<!doctype html><meta charset="utf-8"><title>Form and her words</title>
<style>body{{font:16px/1.6 Georgia,serif;max-width:46em;margin:2em auto;padding:0 1em;color:#111}}
.form{{color:#aaa}} h2{{font-size:1.1em;margin-top:2.5em}} small{{color:#666;font-weight:normal}}</style>
<h1>Form and her words</h1>
<p>{len(sample)} widows' declarations, sorted from least to most form. Grey words are inside a
phrase found in more than the boilerplate share of files (DECISIONS.md 3.1); black words are
the rest.</p>
{''.join(parts)}"""
    path = OUTPUT_FOLDER / "04_form_view.html"
    path.write_text(page, encoding="utf-8")
    print(f"Saved output/04_form_share.csv and {path.relative_to(SCRIPT_DIR)}")


if __name__ == "__main__":
    main()
