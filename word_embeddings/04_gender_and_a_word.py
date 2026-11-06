#!/usr/bin/env python3
"""
Step 4: Which words near a target word lean toward women, and which toward men?
===============================================================================

Adapted from the Maize word embeddings. Following Schmidt, "Rejecting the
gender binary: a vector-space operation" (2015).

Every word gets two scores:

  1. How close it is to TARGET (e.g. "property"): cosine similarity.
  2. Which way it leans on a women <-> men direction. The direction is the
     average of WOMEN_WORDS minus the average of MEN_WORDS, so a positive
     score leans toward the women words and a negative score toward the men.

Both scores are averaged over every model 01 trained (one per seed), so a
lean that only one model shows counts for less.

Read the results with the corpus in mind: most of the text is men's own
declarations and clerks' forms, and a widow's own words survive in only
about a third of the files. "Leans toward women" here mostly means "used
in the paperwork about wives and widows".
"""

import webbrowser

import matplotlib
matplotlib.use("Agg")                 # draw to a file, not a window
import matplotlib.pyplot as plt
import numpy as np

from common import PLOT_FOLDER, SCRIPT_DIR, load_models

# --- Settings ------------------------------------------------------------------

MODEL_NAME = "pensions"
TARGET = "property"

WOMEN_WORDS = ["she", "her", "herself", "wife", "widow", "woman", "mother", "daughter"]
MEN_WORDS = ["he", "his", "him", "himself", "husband", "man", "father", "son"]

NEAR_SHARE = 0.05       # look at the 5% of words closest to TARGET
MIN_COUNT = 30          # skip rarer words
SHOW = 20               # how many words to list on each side
PLOT_LABELS = 15        # how many of those to label on the plot

OPEN_PLOTS = True

# -------------------------------------------------------------------------------


def unit(vector):
    """Scale a vector to length 1, so only its direction matters."""
    return vector / np.linalg.norm(vector)


def scores(wv, words, women, men):
    """Closeness to TARGET and gender lean for each word, in one model."""
    gender_direction = unit(np.mean(wv[women], axis=0) - np.mean(wv[men], axis=0))
    vectors = np.array([unit(wv[w]) for w in words])
    return vectors @ unit(wv[TARGET]), vectors @ gender_direction, \
        float(unit(wv[TARGET]) @ gender_direction)


def main():
    models = load_models(MODEL_NAME)
    wv = next(iter(models.values())).wv
    if TARGET not in wv:
        print(f"'{TARGET}' isn't in the vocabulary.")
        return
    women = [w for w in WOMEN_WORDS if w in wv]
    men = [w for w in MEN_WORDS if w in wv]
    print(f"Models: {MODEL_NAME}, seeds {', '.join(models)}")
    print(f"Women words: {', '.join(women)}")
    print(f"Men words:   {', '.join(men)}")

    words = [w for w in wv.index_to_key
             if wv.get_vecattr(w, "count") >= MIN_COUNT and w not in women + men + [TARGET]]
    results = [scores(m.wv, words, women, men) for m in models.values()]
    closeness = np.mean([r[0] for r in results], axis=0)   # 1. how close to TARGET
    gender = np.mean([r[1] for r in results], axis=0)      # 2. + leans women, - leans men
    target_lean = np.mean([r[2] for r in results])

    # Keep only the words closest to TARGET, then sort them by gender score
    cutoff = np.quantile(closeness, 1 - NEAR_SHARE)
    near = [i for i in range(len(words)) if closeness[i] >= cutoff]
    lean_women = sorted(near, key=lambda i: gender[i], reverse=True)[:SHOW]
    lean_men = sorted(near, key=lambda i: gender[i])[:SHOW]

    print(f"\nThe {len(near)} words closest to '{TARGET}' (similarity {cutoff:.2f} or more), "
          f"sorted by which way they lean:")
    print("\n  Lean toward WOMEN:")
    print("   " + ", ".join(f"{words[i]} ({gender[i]:+.2f})" for i in lean_women))
    print("\n  Lean toward MEN:")
    print("   " + ", ".join(f"{words[i]} ({gender[i]:+.2f})" for i in lean_men))
    print(f"\n  ('{TARGET}' itself scores {target_lean:+.2f})")

    # Plot: gender score across, closeness to TARGET up the side
    fig, ax = plt.subplots(figsize=(13, 9))
    ax.scatter(gender[near], closeness[near], s=10, color="#c5cad3")
    for i in lean_women[:PLOT_LABELS]:
        ax.annotate(words[i], (gender[i], closeness[i]), fontsize=12, color="#8e44ad",
                    xytext=(3, 3), textcoords="offset points")
    for i in lean_men[:PLOT_LABELS]:
        ax.annotate(words[i], (gender[i], closeness[i]), fontsize=12, color="#2a6f97",
                    xytext=(3, 3), textcoords="offset points")
    ax.axvline(0, color="#8a93a6", lw=1, ls="--")
    ax.set_xlabel("← leans toward men words          leans toward women words →", fontsize=13)
    ax.set_ylabel(f"similarity to '{TARGET}'", fontsize=13)
    ax.set_title(f"Words closest to '{TARGET}', by gender lean ({MODEL_NAME})", fontsize=15)
    ax.spines[["top", "right"]].set_visible(False)

    PLOT_FOLDER.mkdir(exist_ok=True)
    plot_path = PLOT_FOLDER / f"gender_{TARGET}_{MODEL_NAME}.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"\nSaved the plot to {plot_path.relative_to(SCRIPT_DIR)}")
    if OPEN_PLOTS:
        webbrowser.open(plot_path.resolve().as_uri())


if __name__ == "__main__":
    main()
