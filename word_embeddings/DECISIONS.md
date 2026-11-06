# Decision log

Research and data decisions for word embeddings on the Revolutionary War pension applications, made
by Emma Stewart (researcher). Claude (coding assistant) proposed options and wrote code; it did
not decide. Entries marked **Open** are defaults set up so the scripts run. They aren't
decisions yet.

---

## 1. Method (2026-11-05)

**1.1 word2vec in gensim, following the Maize word embeddings** and Schmidt's explorations: skip-gram,
100 dimensions, window 5, minimum count 10, 15 epochs.
- *Reasoning:* the same method and settings as the earlier project, so results can be read the same way.
- **Open:** the window and minimum count. A wider window would weigh topics over word usage.

**1.2 Purpose: exploratory.** Used to find spelling variants, map vocabularies (service, poverty,
marriage) and check what the topic model suggests, not as evidence on its own.

## 2. Stability (2026-11-05)

**2.1 Three models with different seeds (42, 7, 2026), and only agreed neighbours are shown.**
With about 2.5 million words, a word's neighbours vary between training runs. `02` and `03` keep
only words in every model's top list. `04` averages the scores of all three.
- *Alternative:* one model, as in Maize (faster, but chance neighbours look like findings).

## 3. Corpus

**3.1 Source text:** `../data/clean_text/`, the same files as the topic model and text reuse (2,062 as of 5 Nov 2026).
Transcriber summaries (`../data/notes_text/`) are left out (modern wording).

**3.2 Units:** each file read whole and cut into 1,000-word chunks (word2vec's input limit). The
files' blank lines are page breaks, so Maize's paragraph split doesn't apply.

**3.3 Kept as is:** spelling, names and formula language. Lowercased; numbers dropped.
**Open:** whether to normalise spellings using `output/spelling_variants.csv` (checked by hand).

## 4. Environment

**4.1 A separate `venv` (Python 3.13) in this folder.** gensim 4.4 doesn't build on Python 3.14,
which the project's `.venv` uses.
