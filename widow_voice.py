"""List the W files whose widow material is transcribed, by the voice it is written in.

Widows' declarations were written down by a clerk, justice or attorney. Most
are in the third person ("That she is the widow of ..."); some are in her own
first person ("my husband died ..."), and some slip between the two. Letters
she wrote or dictated are also first person. This is the closest the files
come to her own words.

  first_person   only first-person widow phrases found
  mixed          both first- and third-person phrases (often a third-person
                 declaration with first-person passages, or a separate letter)
  third_person   only third-person phrases ("she further declares")
  check          neither; often actually a child's or administrator's claim

Found by keyword patterns: a first-person phrase may come from a female
witness rather than the widow, so read the evidence column before relying on
a label.

Writes widow_voice.csv. Run clean_text.py first.

Usage:
    python widow_voice.py
"""

import collections
import csv
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
METADATA_CSV = PROJECT_DIR / "metadata.csv"
CLEAN_DIR = PROJECT_DIR / "data" / "clean_text"
OUT_CSV = PROJECT_DIR / "widow_voice.csv"
FIELDS = ["code", "last_name", "first_name", "pdf_url", "voice",
          "first_person_count", "third_person_count", "evidence"]
EVIDENCE_CHARS = 220

FIRST_PERSON = re.compile(
    r"\bI am the (widow|relict)|"
    r"\bmy (late |said |deceased |aforesaid |first |former |beloved )?husband\b|"
    r"\bI was (lawfully )?married\b|\bI (intermarried|married)\b|\bwe were (lawfully )?married\b|"
    r"\bmy (marriage|intermarriage)\b|\bI\b.{0,60}\bwidow of\b",
    re.IGNORECASE | re.DOTALL)
THIRD_PERSON = re.compile(
    r"\bthat she (is|was) the (widow|relict)|\bher (late |said |deceased |aforesaid )?husband\b|"
    r"\bshe (further |also )?(declares|deposes|saith|states)",
    re.IGNORECASE)


def evidence(text: str, m) -> str:
    start = max(0, m.start() - 60)
    return " ".join(text[start:start + EVIDENCE_CHARS].split())


def classify_voice(text: str) -> tuple[str, int, int, str]:
    """Return (voice, first-person count, third-person count, evidence)."""
    first = list(FIRST_PERSON.finditer(text))
    third = list(THIRD_PERSON.finditer(text))
    if first:
        voice = "mixed" if third else "first_person"
        return voice, len(first), len(third), evidence(text, first[0])
    if third:
        return "third_person", 0, len(third), evidence(text, third[0])
    return "check", 0, 0, ""


def main():
    with METADATA_CSV.open(newline="", encoding="utf-8") as f:
        rows = {r["pdf_filename"]: r for r in csv.DictReader(f)
                if r["code_prefix"] == "W" and r.get("widow_material") == "transcribed"}
    out = []
    for name, r in sorted(rows.items()):
        text = " ".join((CLEAN_DIR / (Path(name).stem + ".txt")).read_text(encoding="utf-8").split())
        voice, n_first, n_third, ev = classify_voice(text)
        out.append({**r, "voice": voice, "first_person_count": n_first,
                    "third_person_count": n_third, "evidence": ev or r["widow_evidence"]})
    order = {"first_person": 0, "mixed": 1, "third_person": 2, "check": 3}
    out.sort(key=lambda r: (order[r["voice"]], -int(r["first_person_count"]), r["code"]))
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(out)
    counts = collections.Counter(r["voice"] for r in out)
    print(f"Wrote {len(out)} files to {OUT_CSV.name}: {dict(counts)}")


if __name__ == "__main__":
    main()
