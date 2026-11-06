#!/usr/bin/env python3
"""
Step 3: Find spelling variants
==============================

New for the pension corpus. Writers spelled as they heard ("inlisted",
"deponant", "malitia", "volenteer"), and the transcribers kept those
spellings. A model can't tell that "inlisted" is "enlisted", but it learns
that they are used in the same places. So a spelling variant is a word that is

  1. close in meaning: in every model's top NEIGHBOURS for the word, and
  2. close in spelling: a string similarity of at least SPELLING (0-1).

Words that only add an ending ("enlist" / "enlisted", "volunteer" /
"volunteers") are left out: those are forms of a word, not variants.

Prints the variants of WORD, then saves candidates for every word used at
least MIN_USES times to output/spelling_variants.csv. They are candidates
to check by hand, not corrections: "married" / "marred" would pass both tests.
"""

import csv
from difflib import SequenceMatcher

from common import SCRIPT_DIR, load_models, stable_neighbours

# --- Settings ------------------------------------------------------------------

MODEL_NAME = "pensions"
WORD = "enlisted"          # print this word's variants first
NEIGHBOURS = 30            # how far down each model's nearest-word list to look
SPELLING = 0.75            # how alike the spellings must be (1.0 = identical)
MIN_USES = 50              # words this common or more go into the CSV

# -------------------------------------------------------------------------------

OUTPUT = SCRIPT_DIR / "output" / "spelling_variants.csv"
ENDINGS = ("s", "es", "ed", "d", "ing", "ly", "'s", "er", "ers", "ment", "ments", "ion", "ions")


def just_an_ending(a, b):
    short, long = sorted((a, b), key=len)
    return long.startswith(short) and long[len(short):] in ENDINGS


def variants(models, word):
    """[(variant, meaning score, spelling score, uses)] for one word."""
    first = next(iter(models.values()))
    if word not in first.wv:
        return []
    found = []
    for other, meaning in stable_neighbours(models, [word], NEIGHBOURS)[0]:
        spelling = SequenceMatcher(None, word, other).ratio()
        if spelling >= SPELLING and not just_an_ending(word, other):
            found.append((other, meaning, spelling, first.wv.get_vecattr(other, "count")))
    return found


def main():
    models = load_models(MODEL_NAME)
    first = next(iter(models.values()))
    wv = first.wv

    print(f"Spelling variants of '{WORD}' "
          f"(used {wv.get_vecattr(WORD, 'count') if WORD in wv else 0:,} times):")
    for other, meaning, spelling, uses in variants(models, WORD):
        print(f"   {other:18} meaning {meaning:.2f}  spelling {spelling:.2f}  {uses:,} uses")

    common = [w for w in wv.index_to_key if wv.get_vecattr(w, "count") >= MIN_USES]
    print(f"\nChecking the {len(common):,} words used at least {MIN_USES} times ...")
    rows, seen = [], set()
    for word in common:
        for other, meaning, spelling, uses in variants(models, word):
            pair = tuple(sorted((word, other)))
            if pair in seen:
                continue
            seen.add(pair)
            rows.append({"word": word, "word_uses": wv.get_vecattr(word, "count"),
                         "variant": other, "variant_uses": uses,
                         "meaning": round(meaning, 3), "spelling": round(spelling, 3)})
    rows.sort(key=lambda r: -r["meaning"])

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows):,} candidate pairs. The 30 closest in meaning:\n")
    for r in rows[:30]:
        print(f"   {r['word']:16} {r['variant']:16} meaning {r['meaning']:.2f}  "
              f"({r['word_uses']:,} / {r['variant_uses']:,} uses)")
    print(f"\nSaved {OUTPUT.relative_to(SCRIPT_DIR)}")


if __name__ == "__main__":
    main()
