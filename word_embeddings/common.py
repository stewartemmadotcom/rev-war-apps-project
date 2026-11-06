"""Shared helpers: load every seed's model, and nearest words they agree on."""

from collections import Counter
from pathlib import Path

from gensim.models import Word2Vec

SCRIPT_DIR = Path(__file__).parent
MODEL_FOLDER = SCRIPT_DIR / "models"
PLOT_FOLDER = SCRIPT_DIR / "plots"


def load_models(name):
    """Every models/<name>_seed<N>.model, as {seed: model}."""
    paths = sorted(MODEL_FOLDER.glob(f"{name}_seed*.model"))
    if not paths:
        raise SystemExit(f"No models named {name}_seed*.model in models/. "
                         "Train them first with 01_train_model.py.")
    return {p.stem.split("_seed")[-1]: Word2Vec.load(str(p)) for p in paths}


def stable_neighbours(models, positive, n):
    """The n nearest words to the average of `positive` in each model, keeping
    only words that are in every model's top n. Returns [(word, mean score)],
    best first, and the share of the first model's top n that survived."""
    tops = []
    for model in models.values():
        tops.append(dict(model.wv.most_similar(positive=positive, topn=n)))
    counts = Counter(w for top in tops for w in top)
    agreed = [w for w, c in counts.items() if c == len(tops)]
    scored = sorted(((w, sum(top[w] for top in tops) / len(tops)) for w in agreed),
                    key=lambda ws: -ws[1])
    return scored, len(agreed) / n
