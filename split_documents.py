"""Step 5: split each cleaned file into its documents and pull out the widow's own.

A pension file is a bundle of documents: the soldier's declaration, the widow's
declaration, witnesses' affidavits, clerks' certificates, family records, heirs'
claims. data/clean_text/ keeps them run together. This script finds where each
document starts, labels each one by who is speaking, and writes:

  data/widow_text/<code>.txt  the widow's own declaration(s), petition(s) or letter(s),
                              for files that have any (one per paragraph)
  documents.csv               every document found: file, position, type, length and
                              its opening words, for checking the boundaries by hand

Where documents start:
  * after a line that closes a document (a signature such as "S/ Ann Brown",
    "Ann herXmark Broach", "... JP", or "Sworn to and subscribed ..."), at the next
    line that is not itself a signature ("Richard Cheshire being duly sworn ...")
  * at a heading or opening formula ("State of North Carolina, Caswell County",
    "On this 7th day of ...", "Personally appeared ...", "This day came ...",
    "We ... certify ...", "To the Honorable ...") when it is a short heading line
    or the line before it ends a sentence. A cue in the middle of a sentence
    ("... in the County of Caswell") does not start a document.

Document types (checked in this order):
  heirs_claim          a child, heir, administrator or executor claiming
  widow_declaration    the widow speaking: "doth on her oath", "That she is the widow
                       of ...", "She further declares", "I am the widow", her mark
  soldier_declaration  the soldier's own application ("on his oath ... relinquishes
                       every claim ...")
  testimony            anyone else swearing to something (witnesses, a woman witness
                       "well acquainted with ...")
  record               family records, certificates, certified copies and the like
  other                anything else (letters, fragments)

Found by keyword patterns, so boundaries and types will sometimes be wrong; read
documents.csv against the PDF to check them. Run clean_text.py first.

Usage:
    python split_documents.py
"""

import collections
import csv
import re
from pathlib import Path

from clean_text import HEIRS_CLAIMANT

PROJECT_DIR = Path(__file__).parent
CLEAN_DIR = PROJECT_DIR / "data" / "clean_text"
WIDOW_DIR = PROJECT_DIR / "data" / "widow_text"
DOCUMENTS_CSV = PROJECT_DIR / "documents.csv"
FIELDS = ["pdf_filename", "doc", "type", "words", "first_line", "opening"]
OPENING_CHARS = 160
HEADING_MAX_WORDS = 12  # a cue line this short is a heading, wherever it falls
HEIRS_CHARS = 600  # an heir names himself near the start of his declaration
SENTENCE_END = (".", ":", ";", "!", "?", '"', "'")
TAIL_MAX_WORDS = 30  # a shorter piece without an opening formula belongs to the document before

START = re.compile(
    r"^((The )?(State|Commonwealth|Territory|District) of\b|"
    r"(?-i:[A-Z])[A-Za-z.'& ]{2,30} (County|District|Parish)\b|"
    r"On (this|the) .{0,20}\bday\b|On this\b|"
    r"Personally (appeared|came)\b|Be it (known|remembered)\b|Before (me|the)\b|"
    r"This day\b|Know all men\b|"
    r"I,? [A-Z][^,]{0,60},? (do )?(hereby )?(certify|depose|declare)\b|We,? |"
    r"To the (Hon|Commissioner|Senate|House|President|Secretary|Governor|General Assembly)|"
    r"The (humble )?(petition|memorial)\b)", re.IGNORECASE)
END = re.compile(
    r"^S/|\b(his|her) ?X ?mark\b|\b(his|her)Xmark\b|^Sworn\b|"
    r"\bsubscribed\b.{0,60}(aforesaid|written|before)|"
    r"\b(JP|J\.P|Clerk|Clk|C\.?S\.?C|Justice of the Peace|Notary Public)\.?\s*$",
    re.IGNORECASE)

FLAGS = re.IGNORECASE | re.DOTALL
WIDOW = re.compile(
    r"\b(on|upon) her (solemn )?oath|\bshe is the (widow|relict)|"
    r"\bthat she (is|was|remains) (the |a )?(widow|relict)|"
    r"\bshe (further |also )?(declares|deposes|states|saith)\b|\bthis (declarant|deponent) (further )?(declares|states)\b.{0,40}\bshe\b|"
    r"\bher ?X ?mark\b|\bherXmark\b|\bI am the (widow|relict)|\bmy (late|said|deceased|aforesaid) husband\b|"
    r"\bher (late |said |deceased )?husband\b|\bhumbly sheweth that her\b|\brelict of\b",
    FLAGS)
STRONG_WIDOW = re.compile(
    r"\bshe is the (widow|relict)|\bthat she (is|was|remains) (the |a )?(widow|relict)|"
    r"\bI am the (widow|relict)|\bmy (late|said|deceased|aforesaid) husband\b|"
    r"\bher (late |said |deceased |aforesaid )?husband\b|\bshe was married to\b",
    FLAGS)
WOMAN_WITNESS = re.compile(
    r"\bthat she (was|is|has been) (well |personally |intimately )?(acquainted|present)\b|"
    r"\bthat she knew\b|\bthat she (saw|heard)\b", FLAGS)
MAN = re.compile(
    r"\b(on|upon) his (solemn )?oath|\bhis ?X ?mark\b|\bhisXmark\b|"
    r"\bhe (further |also )?(declares|deposes|states|saith)\b|"
    r"\bthat he (was|is|has been) (well |personally )?acquainted\b|\bthat he knew\b", FLAGS)
SOLDIER = re.compile(
    r"\brelinquish(es)? every claim|\bthis declarant\b.{0,80}\b(entered|enlisted|volunteered|drafted)\b|"
    r"\bpassed (on )?(the )?7(th)? (day of )?June,? 1832\b|\bJune 7(th)?,? 1832\b",
    FLAGS)
# Who is speaking: the first oath formula names the declarant's sex.
DECLARANT = re.compile(
    r"\b(on|upon) (?P<a>his|her) (solemn |corporal )?oaths?\b|"
    r"\b(?P<b>he|she),? (being|having been) (first |also )?(duly |legally )?sworn\b|"
    r"\b(sworn|deposeth|deposes|saith|says|states|declares|maketh oath|makes oath)\b"
    r"[^.]{0,40}?\bthat (?P<c>he|she)\b|"
    r"\bpersonally (appeared|came)\b[^.]{0,40}?\b(?P<d>Mr|Mrs|Miss)\b", FLAGS)
CERTIFIES = re.compile(r"\b(do|doth|does) (hereby )?certify\b", re.IGNORECASE)
CERTIFY_CHARS = 250  # a certificate says so in its opening
WIDOW_NAMED = re.compile(r"\b(widow|relict) of\b", re.IGNORECASE)
HEIRS_HERE = re.compile(
    HEIRS_CLAIMANT.pattern + r"|\b(son|daughter|heir)s? (and (heir|administrator) )?of the late\b|"
    r"\bthat (she|he) is the (only )?(daughter|son|child)\b", re.IGNORECASE)
RECORD = re.compile(
    r"\bwas born\b|\bI (do )?(hereby )?certify\b|\bwe (do )?(hereby )?certify\b|"
    r"\bcertificate\b|\ba true copy\b|\bmarriage (bond|license|licence)\b", FLAGS)


def lines_of(text: str) -> list[str]:
    return [line for line in text.split("\n") if line.strip()]


def is_start(line: str, previous: str | None) -> bool:
    if previous is None:
        return False
    if END.search(previous):
        # after a signature or jurat, anything that is not itself one begins a document
        return not END.search(line) and line[:1].isupper()
    if not START.match(line):
        return False
    return len(line.split()) <= HEADING_MAX_WORDS or previous.rstrip().endswith(SENTENCE_END)


def split(text: str) -> list[tuple[int, str]]:
    """Return (first line number, text) for each document in a cleaned file."""
    lines = lines_of(text)
    docs, current, first = [], [], 0
    for i, line in enumerate(lines):
        previous = lines[i - 1] if i else None
        if current and is_start(line, previous):
            # a heading line just before a start ("State of Virginia" then
            # "On this ...") already began this document
            docs.append((first, "\n".join(current)))
            current, first = [], i
        current.append(line)
    if current:
        docs.append((first, "\n".join(current)))
    return merge_headings(docs)


def is_heading(text: str) -> bool:
    """True for a run of short heading lines ("STATE OF VIRGINIA," / "Pittsylvania COUNTY")."""
    return all(len(line.split()) <= HEADING_MAX_WORDS and START.match(line)
               for line in text.split("\n"))


def merge_headings(docs: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Join a lone heading to the document after it, and a short tail that does not
    open like a document (the end of a jurat, "Test: S/ ...") to the one before it."""
    merged = []
    for first, text in docs:
        if merged and is_heading(merged[-1][1]):
            prev_first, prev_text = merged.pop()
            merged.append((prev_first, prev_text + "\n" + text))
        elif merged and len(text.split()) <= TAIL_MAX_WORDS and not START.match(text):
            prev_first, prev_text = merged.pop()
            merged.append((prev_first, prev_text + "\n" + text))
        else:
            merged.append((first, text))
    return merged


def declarant(text: str) -> str:
    """'f', 'm' or '' from the first oath formula in a document. A declarant named in
    the opening as someone's widow ("Sarah Williams, widow of William Williams ...
    doth on his oath", a clerk's slip) is the widow."""
    m = DECLARANT.search(text)
    if WIDOW_NAMED.search(text[:m.start() if m else HEIRS_CHARS]):
        return "f"
    if not m:
        return ""
    word = next(g for g in m.group("a", "b", "c", "d") if g).lower()
    return "f" if word in ("her", "she", "mrs", "miss") else "m"


def doc_type(text: str) -> str:
    text = " ".join(text.split())  # phrases often break across lines
    widow = len(WIDOW.findall(text))
    man = len(MAN.findall(text))
    sex = declarant(text)
    if HEIRS_HERE.search(text[:HEIRS_CHARS]) and not STRONG_WIDOW.search(text[:HEIRS_CHARS]):
        return "heirs_claim"
    if CERTIFIES.search(text[:CERTIFY_CHARS]) and sex != "f":
        return "record"  # "I Joseph Chilton a Justice of the peace ... do certify that ..."
    if sex == "m":
        widow = 0  # a man testifying about her ("her husband ...") is not the widow
    elif sex == "f":
        man = 0  # the widow describing her husband's service ("he enlisted ...")
    if widow and widow >= man and (STRONG_WIDOW.search(text) or not WOMAN_WITNESS.search(text)):
        return "widow_declaration"
    if SOLDIER.search(text) and man >= widow:
        return "soldier_declaration"
    if man or widow or re.search(r"\b(sworn|oath|affirm)", text, re.IGNORECASE):
        return "testimony" if not RECORD.search(text[:300]) else "record"
    if RECORD.search(text):
        return "record"
    return "other"


def main():
    WIDOW_DIR.mkdir(parents=True, exist_ok=True)
    rows, counts, files_with_widow = [], collections.Counter(), 0
    for path in sorted(CLEAN_DIR.glob("*.txt")):
        docs = split(path.read_text(encoding="utf-8"))
        widow_docs = []
        for n, (first, text) in enumerate(docs, start=1):
            kind = doc_type(text)
            counts[kind] += 1
            if kind == "widow_declaration":
                widow_docs.append(" ".join(text.split()))
            rows.append({"pdf_filename": path.stem + ".pdf", "doc": n, "type": kind,
                         "words": len(text.split()), "first_line": first + 1,
                         "opening": " ".join(text.split())[:OPENING_CHARS]})
        out = WIDOW_DIR / path.name
        if widow_docs:
            out.write_text("\n\n".join(widow_docs), encoding="utf-8")
            files_with_widow += 1
        elif out.exists():
            out.unlink()
    with DOCUMENTS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Split {len({r['pdf_filename'] for r in rows})} files into {len(rows)} documents: "
          f"{dict(counts.most_common())}")
    print(f"Wrote widow documents for {files_with_widow} files into {WIDOW_DIR}")


if __name__ == "__main__":
    main()
