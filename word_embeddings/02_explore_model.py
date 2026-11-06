#!/usr/bin/env python3
"""
Step 2: Explore the models (following Schmidt)
==============================================

Adapted from the Maize word embeddings. Three ways of looking inside the
models, as before, with one change: every result is checked against all the
models 01 trained (one per seed), and only the neighbours that EVERY model
puts in its top list are shown. With a corpus this small, a neighbour that
only one model finds may be chance.

  1. Nearest words: the words whose vectors are closest to one word.
     (Schmidt: nearest_to(chronam_vectors[["funny"]]))

  2. Nearest to several words at once: average a few seed words into one
     vector and find the words closest to it, to map out a semantic field.

  3. A "non-optimal positioning of words in space": flatten the 100
     dimensions down to 2 and plot WORD with its nearest neighbors (from the
     first model). 2 dimensions can't hold all the relationships.

Change the settings below and run it again.
"""

import webbrowser

import matplotlib
matplotlib.use("Agg")                 # draw to a file, not a window
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

from common import PLOT_FOLDER, SCRIPT_DIR, load_models, stable_neighbours

# --- Settings ------------------------------------------------------------------

MODEL_NAME = "pensions"               # models/<MODEL_NAME>_seed*.model

WORD = "militia"                      # 1. nearest words to this word (also used in 3.)
TOP_N = 15

# 2. a semantic field: household goods in the 1820 property schedules
SEED_WORDS = ["pot", "kettle", "bed", "cow", "plough"]   # ("spider" has too few uses)
FIELD_SIZE = 25

PLOT_COUNT = 40                       # 3. how many of WORD's nearest neighbors to plot

OPEN_PLOTS = True                     # open the plot automatically when it's saved

# -------------------------------------------------------------------------------

LOOK = 3    # each model's top TOP_N * LOOK words are compared, so near-ties still agree


def nearest_words(models, word, n):
    """1. The n words closest to one word, that every model agrees on."""
    print(f"\n1. Nearest words to '{word}'  (1.0 = identical direction, 0 = unrelated)")
    first = next(iter(models.values()))
    if word not in first.wv:
        print(f"   '{word}' isn't in the vocabulary (fewer than 10 uses, or misspelled).")
        return
    print(f"   ('{word}' is used {first.wv.get_vecattr(word, 'count'):,} times)")
    scored, _ = stable_neighbours(models, [word], n * LOOK)
    for neighbor, score in scored[:n]:
        print(f"   {neighbor:22} {score:.3f}")
    print(f"   ({len(scored)} of each model's top {n * LOOK} are shared by all {len(models)} models)")


def nearest_to_several(models, seeds, n):
    """2. Average several words into one vector and find what's near it."""
    first = next(iter(models.values()))
    found = [w for w in seeds if w in first.wv]
    missing = [w for w in seeds if w not in first.wv]
    print(f"\n2. Words nearest to the average of {found}")
    if missing:
        print(f"   (not in the vocabulary, skipped: {missing})")
    if not found:
        return
    scored, _ = stable_neighbours(models, found, n * LOOK)
    print("   " + ", ".join(w for w, _ in scored[:n]))


def plot_positioning(models, word, count):
    """3. Plot `word` and its `count` nearest neighbors in 2 dimensions."""
    seed, model = next(iter(models.items()))
    if word not in model.wv:
        print(f"\n3. Can't plot: '{word}' isn't in the vocabulary.")
        return
    words = [word] + [w for w, _ in model.wv.most_similar(word, topn=count)]
    vectors = model.wv[words]

    # PCA finds the 2 directions that spread these words out the most
    points = PCA(n_components=2).fit_transform(vectors)

    fig, ax = plt.subplots(figsize=(13, 9))
    ax.scatter(points[1:, 0], points[1:, 1], s=8, color="#8a93a6")
    for (x, y), neighbor in zip(points[1:], words[1:]):
        ax.annotate(neighbor, (x, y), fontsize=11, xytext=(3, 3), textcoords="offset points")
    ax.scatter(points[0, 0], points[0, 1], s=60, color="#c0392b", zorder=3)   # the word itself
    ax.annotate(word, points[0], fontsize=15, fontweight="bold", color="#c0392b",
                xytext=(5, 5), textcoords="offset points", zorder=4)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(f"'{word}' and its {count} nearest neighbors, "
                 f"flattened to 2 dimensions ({MODEL_NAME}, seed {seed})")
    ax.spines[["top", "right"]].set_visible(False)

    PLOT_FOLDER.mkdir(exist_ok=True)
    path = PLOT_FOLDER / f"neighbors_{word}_{MODEL_NAME}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    print(f"\n3. Saved the plot to {path.relative_to(SCRIPT_DIR)}")
    if OPEN_PLOTS:
        webbrowser.open(path.resolve().as_uri())


def main():
    models = load_models(MODEL_NAME)
    first = next(iter(models.values()))
    print(f"Models: {MODEL_NAME}, seeds {', '.join(models)}  ({len(first.wv):,} words)")

    nearest_words(models, WORD, TOP_N)
    nearest_to_several(models, SEED_WORDS, FIELD_SIZE)
    plot_positioning(models, WORD, PLOT_COUNT)


if __name__ == "__main__":
    main()
