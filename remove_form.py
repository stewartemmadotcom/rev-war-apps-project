"""Remove the form language from every document, for the whole-corpus topic model.

Form is any 5-word phrase found in more than BOILERPLATE of the files, counted over
the documents whose type is included (topic_modeling/DECISIONS.md 11.3, 11.4): the
soldiers' 1832 oath, the widows' acts, the courts' certificates. This is the same
rule text_reuse/04_form_and_her_words.py uses for the widow documents alone, with the
same word pattern, so the two corpora are treated alike.

Reads data/doc_text/ and documents.csv (from split_documents.py). Writes:
  data/doc_text_noform/<code>.txt   the same documents, one per paragraph, with the
                                    form words cut out
  topic_modeling/output/whole_boilerplate.csv
                                    the form phrases and how many files use them

Usage:
    python remove_form.py
"""

import collections
import csv
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DOC_DIR = PROJECT_DIR / "data" / "doc_text"
NOFORM_DIR = PROJECT_DIR / "data" / "doc_text_noform"
DOCUMENTS_CSV = PROJECT_DIR / "documents.csv"
BOILERPLATE_CSV = PROJECT_DIR / "topic_modeling" / "output" / "whole_boilerplate.csv"

N = 5                     # words per phrase
BOILERPLATE = 0.10        # a phrase in more than this share of files is form
EXCLUDED_TYPES = {"other"}  # their phrases aren't counted (DECISIONS.md 11.3)

# Same word pattern as text_reuse/common.py
WORD = re.compile(r"[a-z]+(?:['-][a-z]+)*")


def phrases(words):
    return {" ".join(words[i:i + N]) for i in range(len(words) - N + 1)}


def form_mask(words, formulas):
    """True for each word inside a form phrase."""
    mask = [False] * len(words)
    for i in range(len(words) - N + 1):
        if " ".join(words[i:i + N]) in formulas:
            for j in range(i, i + N):
                mask[j] = True
    return mask


def without_form(text, formulas):
    """The text with every form word cut out (punctuation and other words kept)."""
    spans = list(WORD.finditer(text.lower()))
    mask = form_mask([m.group(0) for m in spans], formulas)
    out, pos = [], 0
    for m, is_form in zip(spans, mask):
        if is_form:
            out.append(text[pos:m.start()])
            pos = m.end()
    out.append(text[pos:])
    return " ".join("".join(out).split())


def main():
    with DOCUMENTS_CSV.open(newline="", encoding="utf-8") as f:
        types = {(r["pdf_filename"], int(r["doc"])): r["type"] for r in csv.DictReader(f)}

    files = {}
    files_with = collections.Counter()
    for path in sorted(DOC_DIR.glob("*.txt")):
        docs = path.read_text(encoding="utf-8").split("\n\n")
        files[path] = docs
        seen = set()
        for n, doc in enumerate(docs, start=1):
            if types.get((path.stem + ".pdf", n)) not in EXCLUDED_TYPES:
                seen |= phrases(WORD.findall(doc.lower()))
        files_with.update(seen)

    limit = BOILERPLATE * len(files)
    formulas = {p for p, c in files_with.items() if c > limit}
    print(f"{len(formulas):,} phrases in more than {BOILERPLATE:.0%} of {len(files):,} files are form")
    BOILERPLATE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with BOILERPLATE_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["phrase", "files", "share_of_files"])
        for p in sorted(formulas, key=lambda p: -files_with[p]):
            writer.writerow([p, files_with[p], round(files_with[p] / len(files), 3)])
    for p in sorted(formulas, key=lambda p: -files_with[p])[:12]:
        print(f"   {files_with[p] / len(files):4.0%}  {p}")

    NOFORM_DIR.mkdir(parents=True, exist_ok=True)
    total = kept = 0
    for path, docs in files.items():
        stripped = [without_form(doc, formulas) for doc in docs]
        total += sum(len(WORD.findall(d.lower())) for d in docs)
        kept += sum(len(WORD.findall(d.lower())) for d in stripped)
        (NOFORM_DIR / path.name).write_text("\n\n".join(stripped), encoding="utf-8")
    print(f"{1 - kept / total:.0%} of all words were form; wrote {NOFORM_DIR}")


if __name__ == "__main__":
    main()
