# Revolutionary War widow pension applications

Building a corpus of Southern Revolutionary War widow (W) pension applications from the
transcriptions at [revwarapps.org](https://revwarapps.org/), used here with the site
maintainers' permission, for topic modeling, text reuse and word embedding work.

## Pipeline

| Step | Script | Output |
|---|---|---|
| 1. Collect the index and PDFs | not included in this repository | `metadata.csv`, `code_lookup.csv`, `data/pdfs/` |
| 2. Extract text (drops footnotes by font size) | `extract_text.py` | `data/raw_text/`, `data/body_text/` |
| 3. Remove transcriber apparatus; save transcriber notes; label widow material | `clean_text.py` | `data/clean_text/`, `data/notes_text/`, new columns in `metadata.csv` |
| 4. List files with the widow's declaration, by voice | `widow_voice.py` | `widow_voice.csv` |

`data/` is not in the repository (about 600 MB). With the PDFs in `data/pdfs/`, re-create
the rest by running steps 2 to 4.

Tests for the cleaning rules: `python -m pytest test_clean_text.py`

## Widow material labels

`clean_text.py` gives every file one `widow_material` label: `transcribed`,
`summary_only`, `heirs_claim`, `testimony_only` or `none`. Definitions are in the
"Label definitions" sheet of `hand_check_200/Hand_Check_200.xlsx`.

## Hand checks

- `make_widow_check_sample.py` draws samples (stratified, or `--random N`) and scores them
  with a 95% confidence interval.
- `widow_check_sample_random200.csv` is a random sample of 200 files. Claude's labels
  agree with the detector on 192 of 197 (97%, CI 94 to 99%).
- `hand_check_200/` is the blind version of that sample for a human checker (the PDFs
  are not in the repository). `import_hand_check.py` reads the returned workbook back in.
- Rounds 1 to 3 were used to tune the patterns, and were judged before a notes fix, so
  they are kept for the record but should not be cited.

## Analysis

- `topic_modeling/`: R topic models (see its README and DECISIONS)
- `text_reuse/`: shared-passage detection
- `word_embeddings/`: word2vec models

Generated output and trained models in these folders are not in the repository.
