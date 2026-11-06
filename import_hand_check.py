"""Read a returned hand_check_200/Hand_Check_200.xlsx and score it.

Copies the group member's labels into the human_label column of
widow_check_sample_random200.csv, then reports how often the detector, and
Claude's earlier check, agree with them.

Usage:
    python import_hand_check.py [path/to/Hand_Check_200.xlsx]
    python make_widow_check_sample.py --score --out widow_check_sample_random200.csv
"""

import collections
import csv
import sys
from pathlib import Path

from openpyxl import load_workbook

from make_widow_check_sample import wilson

PROJECT_DIR = Path(__file__).parent
WORKBOOK = PROJECT_DIR / "hand_check_200" / "Hand_Check_200.xlsx"
SAMPLE_CSV = PROJECT_DIR / "widow_check_sample_random200.csv"
FIRST_ROW = 5  # first data row on the Checking sheet
CODE_COL, LABEL_COL, CONF_COL, COMMENT_COL = 2, 6, 7, 9


def read_workbook(path: Path) -> dict[str, dict]:
    ws = load_workbook(path, data_only=True)["Checking"]
    found = {}
    for row in ws.iter_rows(min_row=FIRST_ROW, values_only=True):
        code = row[CODE_COL - 1]
        if code:
            found[code] = {"label": (row[LABEL_COL - 1] or "").strip(),
                           "confidence": (row[CONF_COL - 1] or "").strip(),
                           "comment": (row[COMMENT_COL - 1] or "").strip()}
    return found


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else WORKBOOK
    checked = read_workbook(path)
    with SAMPLE_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    for r in rows:
        r["human_label"] = checked.get(r["code"], {}).get("label", "")
    with SAMPLE_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    done = [r for r in rows if r["human_label"]]
    print(f"{len(done)} of {len(rows)} files labeled in {path.name}")
    for other, name in [("widow_material", "detector"), ("claude_label", "Claude's check")]:
        pairs = [r for r in done if r[other]]
        k = sum(r[other] == r["human_label"] for r in pairs)
        if pairs:
            low, high = wilson(k, len(pairs))
            print(f"  {name:15} agrees on {k}/{len(pairs)} ({k / len(pairs):.0%}; "
                  f"95% CI {low:.0%}-{high:.0%})")
    conf = collections.Counter(checked[r["code"]]["confidence"] or "(blank)" for r in done)
    print("  confidence:", dict(conf))


if __name__ == "__main__":
    main()
