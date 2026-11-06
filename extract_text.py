"""Step 2: extract text from data/pdfs/*.pdf.

Writes two versions of each document:
  data/raw_text/<code>.txt   all text on the page
  data/body_text/<code>.txt  only text in the document's main font size

Transcribers set footnotes, footnote numbers and the "[Methodology: ...]"
preamble in a smaller font than the transcription itself, so dropping
smaller-than-body text removes them reliably. Short superscript letters are
kept, since they belong to the word before them: ordinals ("20th") and
period abbreviations ("Saml", "Genl").

Writes extraction_log.csv with page count, character count and status for
each PDF, so empty (image-only) or broken files are easy to find.

Usage:
    python extract_text.py          # skip PDFs already extracted
    python extract_text.py --force  # re-extract everything
"""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

import pymupdf

PROJECT_DIR = Path(__file__).parent
PDF_DIR = PROJECT_DIR / "data" / "pdfs"
TEXT_DIR = PROJECT_DIR / "data" / "raw_text"
BODY_DIR = PROJECT_DIR / "data" / "body_text"
LOG_CSV = PROJECT_DIR / "extraction_log.csv"
MIN_CHARS = 200  # less than this almost certainly means a scan or a broken file
BODY_SIZE_RATIO = 0.9  # spans smaller than this fraction of the body size are dropped
SUPERSCRIPT_LETTERS = re.compile(r"^\s*[a-z]{1,3}\s*$")


def lines_of_spans(doc):
    """Yield (page_number, [spans]) for every line, in reading order."""
    for page_no, page in enumerate(doc):
        for block in page.get_text("dict", sort=True)["blocks"]:
            for line in block.get("lines", []):
                yield page_no, line["spans"]


def body_font_size(doc) -> float:
    sizes = Counter()
    for _, spans in lines_of_spans(doc):
        for s in spans:
            sizes[round(s["size"], 1)] += len(s["text"].strip())
    return sizes.most_common(1)[0][0] if sizes else 0.0


def body_text(doc) -> str:
    min_size = body_font_size(doc) * BODY_SIZE_RATIO
    out, current_page = [], 0
    for page_no, spans in lines_of_spans(doc):
        if page_no != current_page:
            out.append("")
            current_page = page_no
        kept = ""
        for s in spans:
            if s["size"] >= min_size:
                kept += s["text"]
            elif SUPERSCRIPT_LETTERS.match(s["text"]) and re.search(r"\w$", kept):
                kept += s["text"].lstrip()  # superscript: 20th, Saml, Genl
        if kept.strip():
            out.append(kept)
    return "\n".join(out)


def extract(pdf_path: Path) -> tuple[str, str, int]:
    with pymupdf.open(pdf_path) as doc:
        pages = [page.get_text("text", sort=True) for page in doc]
        return "\n".join(pages), body_text(doc), len(pages)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    BODY_DIR.mkdir(parents=True, exist_ok=True)
    log = []
    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        out_path = TEXT_DIR / (pdf_path.stem + ".txt")
        body_path = BODY_DIR / (pdf_path.stem + ".txt")
        if out_path.exists() and body_path.exists() and not args.force:
            continue
        try:
            text, body, n_pages = extract(pdf_path)
        except Exception as e:  # corrupt PDFs shouldn't stop the run
            log.append({"pdf_filename": pdf_path.name, "pages": 0, "chars": 0,
                        "status": f"error: {e}"})
            continue
        out_path.write_text(text, encoding="utf-8")
        body_path.write_text(body, encoding="utf-8")
        status = "ok" if len(text.strip()) >= MIN_CHARS else "too little text"
        log.append({"pdf_filename": pdf_path.name, "pages": n_pages,
                    "chars": len(text), "status": status})

    new_file = not LOG_CSV.exists() or args.force
    with LOG_CSV.open("w" if new_file else "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["pdf_filename", "pages", "chars", "status"])
        if new_file:
            writer.writeheader()
        writer.writerows(log)

    problems = [r for r in log if r["status"] != "ok"]
    print(f"Extracted {len(log)} PDFs into {TEXT_DIR}; {len(problems)} need attention")
    for r in problems:
        print(f"  {r['pdf_filename']}: {r['status']}")


if __name__ == "__main__":
    main()
