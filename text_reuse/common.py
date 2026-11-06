"""
Shared helpers for the text-reuse scripts.

Adapted from the session-laws version in ~/Desktop/11-Text-Reuse. The corpus
here is the widow's own documents from the revwarapps.org pension transcriptions:
one file per application in ../data/widow_text/, holding only the declarations,
petitions and letters in which the widow speaks (../split_documents.py), with
transcriber brackets and notes already removed (../clean_text.py). See
DECISIONS.md 1.

Session laws come split into sections ("Sec. 1 ..."). Pension files don't: a
file is one run of declarations, affidavits and certificates, and its blank
lines are mostly page breaks that fall mid-sentence. So read_windows() cuts
each file into overlapping passages of WINDOW words, starting every STEP
words, and those passages are what the scripts compare:

    {"code": "W10287", "name": "William Aaron", "transcriber": "C. Leon Harris",
     "start": 300, "text": "That he enlisted in the Army ...", "year_guess": 1777}

year_guess is the first year (1740-1899) written in the passage, or 0 if there
isn't one. It is rough: only step 3 uses it, to put versions in order.
"""

import csv
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
CORPUS_FOLDER = PROJECT_DIR / "data" / "widow_text"  # DECISIONS.md 1.1
METADATA_CSV = PROJECT_DIR / "metadata.csv"
OUTPUT_FOLDER = SCRIPT_DIR / "output"

WINDOW = 80     # words per passage
STEP = 20       # a new passage starts every STEP words (so passages overlap a lot:
                # a shared document is caught whichever way it lines up)

# Same word pattern as the session-laws scripts: runs of letters, with
# apostrophes and hyphens inside
WORD = re.compile(r"[a-z]+(?:['-][a-z]+)*")

# Rough keywords for passages about the widow and the marriage. Step 2 searches
# every passage; it uses these only to pick which results to print.
WIDOW_WORDS = re.compile(
    r"\b(widows?|relict|my (?:late|deceased|said) husband|intermarried|"
    r"(?:was|were) (?:lawfully )?married|married to the said|marriage)\b",
    re.IGNORECASE)

YEAR = re.compile(r"\b(1[78]\d\d)\b")


def read_metadata():
    """code -> {"name": ..., "transcriber": ...} from ../metadata.csv."""
    people = {}
    if METADATA_CSV.exists():
        with open(METADATA_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = f"{row['first_name']} {row['last_name']}".strip()
                people[row["code"].upper()] = {"name": name,
                                               "transcriber": row.get("transcriber", "")}
    return people


def read_text(path):
    """A file as one line: hyphens at line ends rejoined ("Regi-\\nment"),
    then every run of whitespace squeezed to one space."""
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return " ".join(text.split())


def read_windows():
    """Every passage of every file, in file order."""
    files = sorted(CORPUS_FOLDER.glob("*.txt"))
    if not files:
        raise SystemExit(f"No text files in {CORPUS_FOLDER}. "
                         "Run ../clean_text.py and ../split_documents.py first.")
    people = read_metadata()
    windows = []
    for path in files:
        code = path.stem.upper()
        person = people.get(code, {"name": "", "transcriber": ""})
        words = read_text(path).split()
        # Short files still get one passage; otherwise the last passage ends
        # at the end of the file
        starts = list(range(0, max(len(words) - WINDOW, 0) + 1, STEP))
        if starts[-1] + WINDOW < len(words):
            starts.append(len(words) - WINDOW)
        for start in starts:
            text = " ".join(words[start:start + WINDOW])
            year = YEAR.search(text)
            windows.append({"code": code, "name": person["name"],
                            "transcriber": person["transcriber"] or "(unknown)",
                            "start": start, "text": text,
                            "year_guess": int(year.group(1)) if year else 0})
    return windows


def phrases(text, n):
    """Every run of n words in the text, as a set."""
    words = WORD.findall(text.lower())
    starts = range(len(words) - n + 1)
    return {" ".join(words[i:i + n]) for i in starts}


def jaccard(a, b):
    """Shared pieces / all the different pieces (0 if neither has any)."""
    if not a | b:
        return 0.0
    return len(a & b) / len(a | b)


def cite(w):
    """A short citation for a passage, e.g. 'W10287 (William Aaron), words 300-450'."""
    who = f" ({w['name']})" if w["name"] else ""
    return f"{w['code']}{who}, words {w['start']}-{w['start'] + len(w['text'].split())}"
