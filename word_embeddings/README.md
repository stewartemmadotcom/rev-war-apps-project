# Word Embeddings: Revolutionary War Pension Applications

Train word2vec models on the pension transcriptions downloaded from
[revwarapps.org](https://revwarapps.org/) (2,062 files as of 5 Nov 2026, about 2.48 million words), using the scripts
from the Maize word embeddings (`~/Desktop/maize-word-embeddings`). Decisions and open questions are in
`DECISIONS.md`.

| Script | What it does | What you change |
|---|---|---|
| `01_train_model.py` | Trains one model per seed on `../data/clean_text/` | `SEEDS`, training settings |
| `02_explore_model.py` | Nearest words, a semantic field, a 2D plot, keeping only neighbours every model agrees on | `WORD`, `SEED_WORDS` |
| `03_spelling_variants.py` | Finds words close in both meaning and spelling ("inlisted" / "enlisted") | `WORD`, `SPELLING`, `MIN_USES` |
| `04_gender_and_a_word.py` | Which words near a target word lean toward women vs. men | `TARGET`, the two word lists |
| `common.py` | Loads the models and finds the neighbours they agree on | |

## Running it

This folder has its own `venv` (Python 3.13), because gensim won't install on the project's
Python 3.14 `.venv`.

```bash
cd word_embeddings
source venv/bin/activate
python 01_train_model.py        # about 40 seconds for three models
python 02_explore_model.py
python 03_spelling_variants.py
python 04_gender_and_a_word.py
```

The models are already trained in `models/`. Rerun `01` after more files are downloaded and cleaned.
Plots go to `plots/` and the variant list to `output/spelling_variants.csv`.

## Differences from the Maize scripts

- **Three models, not one.** The corpus is small, so `01` trains one model per seed, and `02`–`04`
  show only the neighbours that every model agrees on, or average over all of them.
- **No periods.** The files have no reliable dates, so there are no period models and no
  alignment or change-over-time scripts (Maize's `03` and `04`).
- **No prep step.** `../clean_text.py` already made the corpus. `01` reads each file whole, rejoins
  words split across line ends, and cuts it into 1,000-word chunks, because blank lines in these
  files are page breaks, not paragraphs.
- **New: `03_spelling_variants.py`.** It finds the writers' own spellings of a word, as candidates
  for normalising spelling in the topic model and text reuse.

## Things to keep in mind

- **Small vocabulary:** 6,356 words at `MIN_COUNT = 10`. Rarer words (including "spider") have no
  vector at all.
- **Formula.** The oaths repeat so often that their words sit close together ("duly", "personally",
  "aforesaid"). That reflects the paperwork, not shared meaning.
- **Variants are candidates.** `03` also finds pairs like "cows" / "sows" and "removed" / "moved".
  Check them by hand before using any of them to normalise spelling.
- **Gender results describe the paperwork.** Most of the text is men's declarations and clerks'
  forms, and a widow's own words survive in only about a third of the files.
