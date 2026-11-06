#!/usr/bin/env python3
"""
Step 2: What language do the pension applications share?
========================================================

Compares every passage of every pension file with every other passage, the
way Kellen Funk and Lincoln Mullen compared nineteenth-century codes of civil
procedure in "The Spine of American Law" (2018), with their settings (5-word
phrases, 120 minhashes, 60 bands). Adapted from the session-laws version.

  0. Boilerplate: break each passage into 5-word phrases. A phrase found in
     more than BOILERPLATE of the files is a formula: mostly the oath and
     wording the pension acts required ("doth on his oath make the following
     declaration in order to obtain the benefit of the act of congress"). In
     the pension files those formulas are a finding in themselves, so they are
     printed and saved before being set aside.
  1. MinHash: turn each remaining phrase into a number. For each of 120 hash
     functions, keep the smallest hashed value: the passage's signature. The
     share of signature numbers two passages have in common estimates their
     Jaccard similarity.
  2. LSH: cut each signature into 60 bands of 2 numbers. Passages that match
     on a whole band land in the same bucket and become candidates. Only
     candidates get compared.
  3. For each passage, keep its best match from a DIFFERENT file. (The
     session laws used "from an earlier year"; these files have no reliable
     date, and a file often repeats its own documents.) Passages linked by
     matches, directly or through others, form a family; so do overlapping
     matched passages in the same file (one long shared document).

Prints how many files share a passage with another file, by transcriber, then
the families spread across the most files and the families whose text matches
LOOK_FOR. LOOK_FOR doesn't change the search; it only picks what to print.

Results: output/02_boilerplate.csv and output/02_families.csv.

To try another match threshold without editing MATCH, give it on the command
line; the families then go to their own file:
    python 02_reuse_minhash.py 0.3      # -> output/02_families_match0.3.csv
"""

import csv
import re
import sys
import zlib
from collections import Counter, defaultdict

import numpy as np

from common import OUTPUT_FOLDER, SCRIPT_DIR, WIDOW_WORDS, cite, phrases, read_windows

# --- Change these --------------------------------------------------------------

N = 5                   # words per phrase
HASHES = 120            # numbers in each signature
BANDS = 60              # bands per signature (HASHES / BANDS numbers per band)
MATCH = 0.5             # a match shares at least this share of its phrases
                        # (Jaccard; DECISIONS.md 3.2, open)
BOILERPLATE = 0.10      # phrases in more than this share of files are formulas
                        # (DECISIONS.md 3.1)
LOOK_FOR = WIDOW_WORDS.pattern  # second list: families with these words (a regex,
                                # e.g. r"\bcherokee\b"; case doesn't matter)
TOP_N = 15              # families to print in each list
TOP_FORMULAS = 25       # boilerplate phrases to print

# -------------------------------------------------------------------------------

MIN_PHRASES = 10        # passages with fewer distinctive phrases get no signature
ROWS = HASHES // BANDS
PRIME = 4294967291      # the largest prime below 2**32
CHUNK = 500             # rows compared at a time inside a big bucket (saves memory)

# 120 hash functions of the form (a * x + b) % PRIME, with random a and b.
# (623 is the seed Funk and Mullen used in R; Python's random numbers differ.)
rng = np.random.default_rng(623)
A = rng.integers(1, 2**31, size=(HASHES, 1), dtype=np.uint64)
B = rng.integers(0, 2**32, size=(HASHES, 1), dtype=np.uint64)


def minhash(numbers):
    """A passage's signature: for each hash function, the smallest hashed phrase."""
    x = numbers.astype(np.uint64)
    return ((A * x + B) % PRIME).min(axis=1)


def main():
    global MATCH
    families_name = "02_families.csv"
    if len(sys.argv) > 1:
        MATCH = float(sys.argv[1])
        families_name = f"02_families_match{sys.argv[1]}.csv"
    print(f"Match threshold: {MATCH}")
    print("Reading the corpus...")
    windows = read_windows()
    codes = np.array([w["code"] for w in windows])
    n_files = len(set(codes))
    print(f"   {len(windows):,} passages from {n_files:,} files")

    # Every passage's phrases, each turned into a number (crc32 is a quick,
    # standard way to turn text into a number). Remember one wording per number
    # so the formulas can be printed.
    numbered, wording = [], {}
    files_with = Counter()          # phrase number -> how many files use it
    seen_in_file = defaultdict(set)
    for w in windows:
        phrase_set = phrases(w["text"], N)
        numbers = []
        for p in phrase_set:
            x = zlib.crc32(p.encode())
            wording.setdefault(x, p)
            numbers.append(x)
            seen_in_file[w["code"]].add(x)
        numbered.append(np.array(numbers, dtype=np.uint32))
    for in_file in seen_in_file.values():
        files_with.update(in_file)

    limit = BOILERPLATE * n_files
    print(f"0. Boilerplate: phrases found in more than {BOILERPLATE:.0%} of files "
          f"({limit:.0f})...")
    boilerplate = {x for x, c in files_with.items() if c > limit}
    print(f"   {len(boilerplate):,} phrases set aside. The most widespread:\n")
    formulas = sorted(boilerplate, key=lambda x: -files_with[x])
    for x in formulas[:TOP_FORMULAS]:
        print(f"   {files_with[x] / n_files:4.0%}  {wording[x]}")
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    with open(OUTPUT_FOLDER / "02_boilerplate.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["phrase", "files", "share_of_files"])
        for x in formulas:
            writer.writerow([wording[x], files_with[x], round(files_with[x] / n_files, 3)])

    print("\n1. MinHash: a signature for every passage...")
    signatures = np.zeros((len(windows), HASHES), dtype=np.uint32)
    usable = []
    for i, numbers in enumerate(numbered):
        distinctive = [x for x in numbers.tolist() if x not in boilerplate]
        if len(distinctive) >= MIN_PHRASES:
            signatures[i] = minhash(np.array(distinctive))
            usable.append(i)
    print(f"   {len(usable):,} passages have at least {MIN_PHRASES} distinctive phrases")

    print(f"2. LSH: {BANDS} bands, comparing the passages in each bucket...")
    best_score = np.zeros(len(windows))
    best_match = np.full(len(windows), -1)
    for band in range(BANDS):
        columns = signatures[:, band * ROWS:(band + 1) * ROWS]
        buckets = defaultdict(list)
        for i in usable:
            buckets[columns[i].tobytes()].append(i)
        for members in buckets.values():
            if len(members) < 2:
                continue
            m = np.array(members)
            sig = signatures[m]
            for lo in range(0, len(m), CHUNK):
                rows = m[lo:lo + CHUNK]
                # A table with a row for each passage in this chunk and a column
                # for each passage in the bucket: the share of signature numbers
                # they have in common (≈ Jaccard)
                score = (sig[lo:lo + CHUNK, None, :] == sig[None, :, :]).mean(axis=2)
                # Each row only looks at columns from other files
                score[codes[rows][:, None] == codes[m][None, :]] = 0
                top = score.argmax(axis=1)
                top_score = score.max(axis=1)
                better = top_score > best_score[rows]
                best_score[rows[better]] = top_score[better]
                best_match[rows[better]] = m[top[better]]

    # 3. Families: passages joined by matches, directly or through others
    # (union-find: every passage points toward a representative)
    matched = best_score >= MATCH
    parent = list(range(len(windows)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in np.flatnonzero(matched):
        parent[root(i)] = root(best_match[i])
    # Overlapping matched passages in the same file are one longer shared
    # passage, so they belong to the same family too
    for i in range(1, len(windows)):
        if matched[i] and matched[i - 1] and codes[i] == codes[i - 1]:
            parent[root(i)] = root(i - 1)
    families = defaultdict(list)
    for i in np.flatnonzero(matched | np.isin(np.arange(len(windows)), best_match[matched])):
        families[root(i)].append(i)

    files_matched = set(codes[matched])
    print(f"\n{matched.sum():,} passages share at least {MATCH:.0%} of their distinctive "
          f"phrases with a passage in another file.")
    print(f"{len(files_matched):,} of {n_files:,} files ({len(files_matched) / n_files:.0%}) "
          f"have at least one such passage.\n")
    print("By transcriber (a check that matches aren't one transcriber's habits):")
    by_transcriber = defaultdict(set)
    for w in windows:
        by_transcriber[w["transcriber"]].add(w["code"])
    for name, files in sorted(by_transcriber.items(), key=lambda kv: -len(kv[1])):
        if len(files) >= 5:
            share = len(files & files_matched) / len(files)
            print(f"  {name:25s} {share:4.0%}  of {len(files):,} files")

    def file_count(members):
        return len({codes[k] for k in members})

    ranked = sorted(families.values(), key=lambda fam: (-file_count(fam), -len(fam)))
    look_for = re.compile(LOOK_FOR, re.IGNORECASE)
    looked_for = [(r, fam) for r, fam in enumerate(ranked, 1)
                  if any(look_for.search(windows[k]["text"]) for k in fam)]

    rows = []
    for heading, numbered_families in [
            ("Families spread across the most files", list(enumerate(ranked, 1))),
            ("Families with LOOK_FOR words (numbered by rank in the list above)", looked_for)]:
        print(f"\n{heading}:\n")
        for rank, fam in numbered_families[:TOP_N]:
            fam = sorted(fam, key=lambda k: (codes[k], windows[k]["start"]))
            w = windows[fam[0]]
            file_list = sorted({codes[k] for k in fam})
            print(f"{rank:5d}. {len(fam)} passages in {len(file_list)} files: "
                  f"{', '.join(file_list[:8])}{' ...' if len(file_list) > 8 else ''}")
            print(f"       e.g. {cite(w)}")
            print(f"       \"{w['text'][:220]}...\"\n")
    for rank, fam in enumerate(ranked, 1):
        for k in sorted(fam, key=lambda k: (codes[k], windows[k]["start"])):
            w = windows[k]
            has_match = best_match[k] >= 0 and best_score[k] > 0
            rows.append({"family": rank, "files_in_family": file_count(fam),
                         "code": w["code"], "name": w["name"], "start_word": w["start"],
                         "text": w["text"],
                         "best_match": cite(windows[best_match[k]]) if has_match else "",
                         "score": round(best_score[k], 2) if has_match else ""})

    path = OUTPUT_FOLDER / families_name
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {path.relative_to(SCRIPT_DIR)} and output/02_boilerplate.csv")
    print("Follow one passage across files with 03_reuse_trace_clause.py.")


if __name__ == "__main__":
    main()
