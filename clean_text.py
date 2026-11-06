"""Step 3: remove transcriber apparatus from data/body_text/ into data/clean_text/.

Footnotes and the "[Methodology: ...]" preamble are already gone: they are in
a smaller font, which extract_text.py drops when writing data/body_text/.

Transcriber conventions handled (see test_clean_text.py for examples):
  * header ("Southern Campaign(s) American Revolution Pension Statements",
    "Pension Application of ...", "Transcribed [and annotated] by ...")
  * every [...] insertion: [sic: Cornwallis], [probably Tappan NY],
    [26 Dec 1776], [Certifications omitted.], [p 3], etc. For [sic: ...] the
    original spelling written before the bracket is kept. A "[" the
    transcriber never closed is removed to the end of its paragraph.
  * page markers in parentheses: (p 4), (p6), (pp. 3-4)
  * a trailing transcriber "NOTE:" block at the end of the document
  * headers of addenda and appended records later in the file
    ("Addendum to ...", "South Carolina Audited Accounts relating to ...")
  * Fold3 and other URLs, and "_____" divider lines
  * ↑ ↓ marks around interlined words (the words are kept)
  * "{" "}" used to draw braces in court headings, curly quotes,
    superscript ordinals extracted as "3 rd", and hard line wraps

Transcriber notes with substance are saved, not discarded, to
data/notes_text/<code>.txt, one note per paragraph. Many documents in a file
(often the widow's own declaration, marriage bonds, family records) were
summarized in a note such as "[p 14: Mary Bagwell, widow, filed ...]" rather
than transcribed. These are kept apart from clean_text because they are the
transcriber's modern wording, not period text. Saved: bracketed notes of
NOTE_MIN_WORDS or more (except [sic: ...] and the [Methodology: ...]
preamble) and any trailing "NOTE:" block.

Usage:
    python clean_text.py
"""

import csv
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
RAW_DIR = PROJECT_DIR / "data" / "body_text"
CLEAN_DIR = PROJECT_DIR / "data" / "clean_text"
NOTES_DIR = PROJECT_DIR / "data" / "notes_text"
METADATA_CSV = PROJECT_DIR / "metadata.csv"
NEW_COLUMNS = ["widow_material", "widow_evidence", "transcriber"]

# widow_material: the best widow material in the file, checked in this order.
#   transcribed     her own application, in period language (clean_text)
#   summary_only    her application, only as a transcriber summary (notes_text)
#   heirs_claim     children/heirs claimed her pension after she died
#   testimony_only  others swear she is the widow / the couple were married
#   none            nothing beyond e.g. "His widow was pensioned in a like amount"
# Found by keyword patterns, so some files will be misclassified; widow_evidence
# holds the matched passage so labels can be checked by hand.

# A child or administrator claiming after the widow died ("that he is the son
# of", "the declaration of ... Administrator of Elizabeth Adtkinson deceased").
# Their declarations cite the same widows' acts as hers, so the weaker
# "transcribed" patterns only count when no such claimant appears.
HEIRS_CLAIMANT = re.compile(
    r"\bthat (he|she|they|I|we) (is|are|am) the (only |surviving |legal |lawful |sole |eldest |youngest )*"
    r"(sons?|daughters?|children|child|heirs?|administrat\w+|executo\w+|grand ?children)\b|"
    r"\b(for|to) the (surviving )?(children|heirs) of\b|"
    r"\b(children|heirs|administrat\w+|executo\w+) of\b[^.]{0,60}\bdecea?sed\b",
    re.IGNORECASE)
# (label, where to look, pattern, unless this pattern is also found there)
WIDOW_PATTERNS = [
    # Her own declaration: phrases only the widow (or her clerk) would use.
    ("transcribed", "clean", re.compile(
        r"\bshe is the (widow|relict)|"
        r"\bthat she (is|was|remains) (the |a )?(widow|relict)|"
        r"\bshe (further |also )?(declares|deposes)\b|"
        r"\bI am the (widow|relict)|\bmy (late|said|deceased|aforesaid) husband\b|"
        r"\bwho is the (widow|relict) of\b|\brelict of the late\b",
        re.IGNORECASE | re.DOTALL), None),
    # Weaker: also found in heirs' declarations ("her marriage with" the soldier).
    ("transcribed", "clean", re.compile(
        r"\bthat her (late |deceased |said |aforesaid )?husband\b|"
        r"\bher (first |second |said )?(intermarriage|marriage) (with|to)\b|"
        r"\b(on|upon) her (solemn )?oath|\bwidow of the (said|late)\b|"
        r"\bbenefit of the (provision|act).{0,200}\bwidows?\b|"
        r"\bappeared.{0,250}\b(widow|relict)\b",
        re.IGNORECASE | re.DOTALL), HEIRS_CLAIMANT),
    ("summary_only", "notes", re.compile(
        r"\b(applied|filed|files|petitioned|made (an |a )?(application|declaration)|declared)\b.{0,250}"
        r"\b(widow\w*|relict|that she|she (was )?married|her (late |deceased )?husband)\b|"
        # not a woman witness: "gave testimony that she was well acquainted with",
        # "testified that she was present at the marriage"
        r"\b(gave testimony|testified|deposed|made oath) that she\b"
        r"(?! (was |is |has been )?(well |personally |intimately )?(acquainted|knew|know|present))|"
        r"\b(widow\w*|relict)\b.{0,100}\b(applied|filed|application)\b|"
        r"\bher (application|declaration|claim|petition)\b|"
        r"\bstated that\b.{0,40}\bshe (was |had been )?married\b|"
        r"\b(restoration|increase|renewal|continuation) of her pension\b",
        re.IGNORECASE | re.DOTALL), None),
    # Heirs: often a child's declaration in period language, recognizable by the
    # widow having died before the claim ("his widow Mary Bolick died ...").
    ("heirs_claim", "both", re.compile(
        r"\b(applied|application|claim\w*)\b.{0,200}"
        r"\b(surviving child\w*|children of|heirs?|by right of (his|her|their) mother|"
        r"due (his|her|their) (mother|late mother))\b|"
        r"\b(children|heirs|administrat\w+) of\b.{0,150}\b(applied|application|claim\w*)\b|"
        r"\b(on |in )?behalf of (himself|herself|themselves).{0,80}\bheirs\b|\bheirs of (the )?said\b|"
        r"\bclaim as (the )?(son|daughter|child|heir|administrat\w+)\b|"
        r"\bas the (son|daughter|child|heir)s? (and (administrator|heir) )?of\b|"
        r"\bin the name of (his|her|their) (late )?mother\b|\bchildren and heirs\b|\bheirs at law\b|"
        r"\bleaving (the following )?children\b|" + HEIRS_CLAIMANT.pattern,
        re.IGNORECASE | re.DOTALL), None),
    # In an heir's own declaration; a transcriber's "the widow died" alone is not a claim.
    ("heirs_claim", "clean", re.compile(
        r"\bwidow\b(?! was pensioned).{0,100}\b(died|departed this life|is now dead|is dead)\b",
        re.IGNORECASE | re.DOTALL), None),
    ("testimony_only", "both", re.compile(
        r"\b(is|was|remains) (the |his )?(widow|relict)\b|\brelict\b|\bintermarried\b|"
        r"\b(was|were) (lawfully )?married\b|\bhusband and wife\b|\bhis widow\b(?! was pensioned)|"
        r"\bin support of (the |her )?(widow'?s )?(application|claim|declaration)\b|"
        r"\bat the (marriage|wedding) of\b|\bwidow of\b|"
        r"\b(before|prior to|since) their marriage\b|\bacquainted with\b.{0,60}\band his wife\b",
        re.IGNORECASE | re.DOTALL), None),
]
EVIDENCE_CHARS = 220
TRANSCRIBER = re.compile(r"Transcribed (?:and annotated )?by (.+)", re.IGNORECASE)
# Name ends at ";", a revision note or date, or a final period (not initials: "C. Leon Harris").
TRANSCRIBER_END = re.compile(r";|\.?\s+(?=rev|\d)|\.?\s*$", re.IGNORECASE)
NOTE_MIN_WORDS = 7  # shorter brackets are clarifications: [Robert], [probably Tappan NY]
SKIPPED_NOTE = re.compile(r"^\[\s*(sic\b|Methodology\b)", re.IGNORECASE)

HEADER_END = re.compile(r"^.*\bTranscribed\b.*\bby\b.*$(?:\n.*\brev'?d\b.*$|\n\s*[\d/]+\s*$)?",
                        re.IGNORECASE | re.MULTILINE)
HEADER_SEARCH_CHARS = 600  # the header is always at the top of the first page
# Many files continue with an addendum or other records, each under its own
# header ("Southern Campaign ... Addendum to ...", "South Carolina Audited
# Accounts relating to ..."). Files are cleaned section by section, so each
# header is removed and a closing NOTE ends at the next section.
SECTION_START = re.compile(
    r"^[^\n]*(Southern Campaigns? American Revolution|Audited Accounts? relating to)[^\n]*$|"
    r"^\s*Addend(um|a) (and notes )?to\b[^\n]*$",
    re.IGNORECASE | re.MULTILINE)
# A "Transcribed by" line also starts a section, unless it is part of a header.
TRANSCRIBED_LINE = re.compile(r"^[^\n]{0,100}\bTranscribed (and annotated )?by\b[^\n]*$",
                              re.IGNORECASE | re.MULTILINE)
BRACKET = re.compile(r"\[[^\[\]]*\]", re.DOTALL)  # innermost [...] only
# A "[" the transcriber never closed. It runs to the end of its paragraph or a
# "_____" divider line. If its first line is only a label ("[pp 5-6: family
# record:", or a stray "[" from a typo such as "[[ 12]"), only that line is
# removed, since period text (a family record, a declaration) follows it.
# Otherwise it is a transcriber note: removed from clean text, kept in notes.
UNCLOSED_BRACKET = re.compile(r"\[.*?(?=\n\s*\n|\n\s*_{5,}|\Z)", re.DOTALL)
UNCLOSED_LABEL_WORDS = 4
# (p 4), (pp. 3-4), and page notes such as (p12 ff) or (p8 details extracted, ...)
PAGE_MARKER = re.compile(r"\(\s*pp?\.?\s*\d+[^()]{0,300}\)")
URL = re.compile(r"\S*(https?://|www\.)\S*")
RULE = re.compile(r"_{5,}")  # divider lines between documents
INSERTION_ARROWS = re.compile(r"[↑↓]")
# Uppercase only: C. Leon Harris closes files with "NOTE:"/"NOTES:" (once "NOTE;"), sometimes
# on the same line as the last signature, and in short files before midway.
TRAILING_NOTE = re.compile(r"\bNOTES?\s*[:;]")
NOTE_MIN_POSITION = 0.2  # ignore a NOTE: label right at the top of a file
SPACED_ORDINAL = re.compile(r"\b(\d+) (st|nd|rd|th|d)\b")
QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def sections(text: str) -> list[str]:
    """Split a file at each document header (the first section starts at 0)."""
    headers = {m.start() for m in SECTION_START.finditer(text)}
    lines = {m.start() for m in TRANSCRIBED_LINE.finditer(text)}
    starts = [0]
    for pos in sorted(headers | lines):
        if pos == 0:
            continue
        # a "Transcribed by" line just after a header belongs to that header
        if pos in headers or pos >= starts[-1] + HEADER_SEARCH_CHARS:
            starts.append(pos)
    return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]


def strip_header(text: str) -> str:
    m = HEADER_END.search(text[:HEADER_SEARCH_CHARS])
    if m:
        return text[m.end():]
    m = SECTION_START.match(text)  # a header with no "Transcribed by" line
    return text[m.end():] if m else text


def blank_brackets(text: str) -> tuple[str, list[tuple[int, str]]]:
    """Blank out every closed [...] and return (blanked text, [(position, bracket)]).

    Innermost first, so nested brackets ([p 12: ... [sic, Baird] ...]) are found
    whole. Blanking with spaces keeps positions, so notes stay in document order.
    """
    found = []
    while True:
        new = BRACKET.sub(lambda m: found.append((m.start(), m.group(0))) or " " * len(m.group(0)),
                          text)
        if new == text:
            return text, found
        text = new


def is_unclosed_label(segment: str) -> bool:
    first = segment.split("\n", 1)[0][1:].strip()
    return len(first.split()) <= UNCLOSED_LABEL_WORDS or first.endswith((":", ";"))


def unclosed_spans(text: str) -> list[tuple[int, int, bool]]:
    """(start, end, is_note) for each unclosed "[": a note runs to its paragraph's
    end; a label is just its first line, and the search continues after it."""
    spans, pos = [], 0
    while m := UNCLOSED_BRACKET.search(text, pos):
        if is_unclosed_label(m.group(0)):
            line_end = text.find("\n", m.start())
            end = m.end() if line_end == -1 or line_end > m.end() else line_end
            spans.append((m.start(), end, False))
        else:
            end = m.end()
            spans.append((m.start(), end, True))
        pos = max(end, m.start() + 1)
    return spans


def strip_unclosed(text: str) -> str:
    for start, end, _ in reversed(unclosed_spans(text)):
        text = text[:start] + " " + text[end:]
    return text


def strip_brackets(text: str) -> str:
    text = strip_unclosed(blank_brackets(text)[0])
    return text.replace("]", " ")


def strip_page_markers(text: str) -> str:
    return PAGE_MARKER.sub(" ", text)


def split_trailing_note(text: str, min_position: float = NOTE_MIN_POSITION) -> tuple[str, str]:
    """Split text into (body, trailing NOTE: block or "")."""
    for m in TRAILING_NOTE.finditer(text):
        if m.start() >= len(text) * min_position:
            return text[:m.start()], text[m.start():]
    return text, ""


def strip_trailing_note(text: str, min_position: float = NOTE_MIN_POSITION) -> str:
    return split_trailing_note(text, min_position)[0]


def note_min_position(i: int) -> float:
    # An addendum may be nothing but notes ("Addenda to Henry Field W8811\nNOTES: ...").
    return NOTE_MIN_POSITION if i == 0 else 0.0


def extract_notes(text: str) -> list[str]:
    """Return the substantive transcriber notes in text, brackets removed."""
    notes = []
    for i, section in enumerate(sections(text)):
        body, trailing = split_trailing_note(strip_header(section), note_min_position(i))
        blanked, found = blank_brackets(body)
        found += [(start, blanked[start:end] + "]") for start, end, is_note in unclosed_spans(blanked)
                  if is_note]
        for _, note in sorted(found):
            if len(note.split()) >= NOTE_MIN_WORDS and not SKIPPED_NOTE.match(note):
                notes.append(note[1:-1])
        if trailing:
            notes.append(trailing)
    return [" ".join(n.translate(QUOTES).split()) for n in notes]


def normalize(text: str) -> str:
    text = text.translate(QUOTES)
    text = text.replace("}", " ").replace("{", " ")
    text = INSERTION_ARROWS.sub(" ", text)
    text = SPACED_ORDINAL.sub(r"\1\2", text)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)  # word broken across lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def clean_section(text: str, min_note_position: float = NOTE_MIN_POSITION) -> str:
    text = strip_header(text)
    text = strip_trailing_note(text, min_note_position)
    text = strip_brackets(text)
    text = strip_page_markers(text)
    text = URL.sub(" ", text)
    return RULE.sub(" ", text)


def clean(text: str) -> str:
    return normalize("\n\n".join(clean_section(s, note_min_position(i))
                                 for i, s in enumerate(sections(text))))


def classify_widow(cleaned: str, notes: list[str]) -> tuple[str, str]:
    """Return (widow_material label, matched passage) for one file."""
    cleaned = " ".join(cleaned.split())  # so phrases match across line breaks
    sources = {"clean": [cleaned], "notes": notes, "both": [cleaned, *notes]}
    for label, where, pattern, unless in WIDOW_PATTERNS:
        for text in sources[where]:
            m = pattern.search(text)
            if m and not (unless and unless.search(text)):
                start = max(0, m.start() - 60)
                return label, " ".join(text[start:start + EVIDENCE_CHARS].split())
    return "none", ""


def widow_material(cleaned: str, notes: list[str]) -> str:
    return classify_widow(cleaned, notes)[0]


def transcriber(text: str) -> str:
    m = TRANSCRIBER.search(text[:HEADER_SEARCH_CHARS])
    if not m:
        return ""
    name = m.group(1)
    return name[:TRANSCRIBER_END.search(name).start()].strip()


def update_metadata(found: dict[str, dict]):
    """Add NEW_COLUMNS to metadata.csv for every PDF that has been processed."""
    with METADATA_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames + [c for c in NEW_COLUMNS if c not in reader.fieldnames]
        rows = list(reader)
    for row in rows:
        row.update(found.get(Path(row["pdf_filename"]).stem, {}))
    with METADATA_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    paths = sorted(RAW_DIR.glob("*.txt"))
    with_notes = 0
    found = {}
    for path in paths:
        text = path.read_text(encoding="utf-8")
        cleaned = clean(text)
        notes = extract_notes(text)
        (CLEAN_DIR / path.name).write_text(cleaned, encoding="utf-8")
        (NOTES_DIR / path.name).write_text("\n\n".join(notes), encoding="utf-8")
        with_notes += bool(notes)
        label, evidence = classify_widow(cleaned, notes)
        found[path.stem] = {"widow_material": label, "widow_evidence": evidence,
                            "transcriber": transcriber(text)}
    update_metadata(found)
    print(f"Cleaned {len(paths)} files into {CLEAN_DIR}")
    print(f"Saved transcriber notes for {with_notes} files into {NOTES_DIR}")
    print(f"Updated {', '.join(NEW_COLUMNS)} in {METADATA_CSV.name}")


if __name__ == "__main__":
    main()
