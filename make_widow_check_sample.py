"""Draw a sample of processed W files for hand-checking the widow_material labels.

Writes widow_check_sample.csv. Open each file's PDF (or data/clean_text and
data/notes_text), decide the correct label yourself, and fill in human_label
(same five labels as widow_material; see clean_text.py). Then run
    python make_widow_check_sample.py --score
to see how often the detector agrees with you. Scoring compares against the
detector's current labels in metadata.csv, so after changing the patterns in
clean_text.py, rerun clean_text.py and score the same sample again.
claude_label holds Claude's own check (--score --column claude_label).

The sample is stratified: up to PER_LABEL files from each label (as labeled
when drawn), so the rare labels get checked too. With --random N it is instead
a simple random sample of N files, so labels appear in proportion to the full
set and agreement estimates overall accuracy directly.

For a fresh sample that skips files already checked:
    python make_widow_check_sample.py --seed 5 --out widow_check_sample_rare.csv \
        --exclude widow_check_sample_random200.csv hand_checks/archive/*.csv
    python make_widow_check_sample.py --score --out widow_check_sample_rare.csv
"""

import argparse
import collections
import csv
import math
import random
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
METADATA_CSV = PROJECT_DIR / "metadata.csv"
SAMPLE_CSV = PROJECT_DIR / "widow_check_sample.csv"
LABELS = ["transcribed", "summary_only", "heirs_claim", "testimony_only", "none"]
PER_LABEL = 10
FIELDS = ["code", "last_name", "first_name", "pdf_url", "widow_material",
          "widow_evidence", "human_label", "claude_label", "comment"]


def draw(seed: int, out: Path, exclude: list[Path], random_n: int = 0):
    checked = set()
    for path in exclude:
        with path.open(newline="", encoding="utf-8") as f:
            checked |= {r["code"] for r in csv.DictReader(f)}
    with METADATA_CSV.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)
                if r["code_prefix"] == "W" and r["widow_material"] and r["code"] not in checked]
    by_file = {r["pdf_filename"]: r for r in rows}  # one row per PDF
    by_label = collections.defaultdict(list)
    for r in by_file.values():
        by_label[r["widow_material"]].append(r)
    rng = random.Random(seed)
    sample = []
    if random_n:
        sample = rng.sample(sorted(by_file.values(), key=lambda r: r["code"]), random_n)
    else:
        for label in LABELS:
            group = sorted(by_label[label], key=lambda r: r["code"])
            sample += rng.sample(group, min(PER_LABEL, len(group)))
    rng.shuffle(sample)  # so labels aren't read in blocks
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in sample:
            writer.writerow({**r, "human_label": "", "claude_label": "", "comment": ""})
    counts = collections.Counter(r["widow_material"] for r in sample)
    print(f"Wrote {len(sample)} files to {out.name}: {dict(counts)}")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% confidence interval for a proportion k/n."""
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def score(column: str, sample_csv: Path):
    with METADATA_CSV.open(newline="", encoding="utf-8") as f:
        current = {r["code"]: r["widow_material"] for r in csv.DictReader(f)}
    with sample_csv.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get(column, "").strip()]
    if not rows:
        print(f"No {column} values filled in yet.")
        return
    agree = collections.Counter()
    total = collections.Counter()
    confusions = collections.Counter()
    for r in rows:
        said, truth = current[r["code"]], r[column].strip()
        total[said] += 1
        if said == truth:
            agree[said] += 1
        else:
            confusions[(said, truth)] += 1
    n_agree = sum(agree.values())
    low, high = wilson(n_agree, len(rows))
    print(f"Agreement: {n_agree}/{len(rows)} ({n_agree / len(rows):.0%}; 95% CI {low:.0%}-{high:.0%})")
    for label in LABELS:
        if total[label]:
            print(f"  detector said {label:15} right {agree[label]}/{total[label]}")
    for (said, truth), n in confusions.most_common():
        print(f"  {n} x detector '{said}' but actually '{truth}'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--score", action="store_true", help="score a filled-in sample")
    parser.add_argument("--column", default="human_label", help="label column to score")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path, default=SAMPLE_CSV, help="sample file to write or score")
    parser.add_argument("--exclude", type=Path, nargs="*", default=[],
                        help="earlier sample files whose codes should not be drawn again")
    parser.add_argument("--random", type=int, default=0, metavar="N",
                        help="draw a simple random sample of N files instead of stratifying")
    args = parser.parse_args()
    score(args.column, args.out) if args.score else draw(args.seed, args.out, args.exclude, args.random)
