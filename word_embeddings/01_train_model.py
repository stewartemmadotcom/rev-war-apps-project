#!/usr/bin/env python3
"""
Step 1: Train word2vec models on the pension applications
=========================================================

Adapted from the Maize word embeddings (~/Desktop/maize-word-embeddings).
Reads every file in ../data/clean_text/ (one pension application per file,
transcriber brackets and notes removed by ../clean_text.py), splits the text
into words, and trains gensim's Word2Vec.

The corpus is small (about 1.3 million words), so a word's nearest neighbours
can change from one training run to the next. This trains one model per seed
in SEEDS, saved as models/<MODEL_NAME>_seed<N>.model, so 02 can show which
neighbours every model agrees on (DECISIONS.md 2).

You may see "Exception ignored in: 'gensim.models.word2vec_inner.our_dot_float'"
a few times while it trains. It's a known, harmless gensim bug (issue #3665):
the model still trains correctly.
"""

import os
import re
import time
from pathlib import Path

from gensim.models import Word2Vec

SCRIPT_DIR = Path(__file__).parent

# --- Change these --------------------------------------------------------------

CORPUS_FOLDER = SCRIPT_DIR.parent / "data" / "clean_text"
MODEL_NAME = "pensions"
SEEDS = [42, 7, 2026]   # one model per seed

# --- Training settings (keep them the same for every model you'll compare) -----

VECTOR_SIZE = 100   # how many numbers (dimensions) describe each word
WINDOW = 5          # how many words on each side count as "context"
MIN_COUNT = 10      # ignore words that appear fewer times than this
SG = 1              # 1 = skip-gram (predict the neighbors from the word); 0 = CBOW
EPOCHS = 15         # how many times to read through the whole corpus

# -------------------------------------------------------------------------------

MODEL_FOLDER = SCRIPT_DIR / "models"

# A "word" is a run of letters, optionally joined by an apostrophe or hyphen
# (so "s'd" and "dec'd" stay whole). Numbers are ignored.
WORD = re.compile(r"[a-z]+(?:['-][a-z]+)*")


def read_corpus(folder):
    """Turn every file into lists of lowercased words. The files' blank lines
    are mostly page breaks, not paragraphs, so each file is read whole (with
    words hyphenated across a line end rejoined) and cut into chunks of 1,000
    words, since word2vec reads at most 10,000 words at a time."""
    sentences = []
    files = sorted(folder.glob("*.txt"))
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
        text = text.replace("’", "'")
        words = WORD.findall(text.lower())
        for i in range(0, len(words), 1000):
            sentences.append(words[i:i + 1000])
    return files, sentences


def main():
    if not CORPUS_FOLDER.exists():
        print(f"Can't find {CORPUS_FOLDER}. Run ../clean_text.py first, or change CORPUS_FOLDER.")
        return

    print(f"Reading {CORPUS_FOLDER} ...")
    files, sentences = read_corpus(CORPUS_FOLDER)
    total_words = sum(len(s) for s in sentences)
    print(f"  {len(files)} files, {total_words:,} words")

    MODEL_FOLDER.mkdir(exist_ok=True)
    for seed in SEEDS:
        print(f"\nTraining with seed {seed} ...")
        start = time.time()
        model = Word2Vec(
            sentences=sentences,
            vector_size=VECTOR_SIZE,
            window=WINDOW,
            min_count=MIN_COUNT,
            sg=SG,
            epochs=EPOCHS,
            workers=os.cpu_count(),   # use every processor core to speed it up
            seed=seed,
        )
        model_path = MODEL_FOLDER / f"{MODEL_NAME}_seed{seed}.model"
        model.save(str(model_path))
        print(f"  done in {time.time() - start:.0f} seconds; vocabulary: {len(model.wv):,} words "
              f"(each appears at least {MIN_COUNT} times)")
        print(f"  saved {model_path.relative_to(SCRIPT_DIR)}")

    # A quick check that the model learned something sensible
    print("\nQuick check, the 8 words closest to 'enlisted' (last model):")
    for word, score in model.wv.most_similar("enlisted", topn=8):
        print(f"  {word:20} {score:.3f}")


if __name__ == "__main__":
    main()
