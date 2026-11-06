# Topic Modeling: Revolutionary War Pension Applications

LDA topic models of the pension-application transcriptions downloaded from
[revwarapps.org](https://revwarapps.org/) (2,062 files as of 5 Nov 2026, almost all widow "W" files), in R,
using the same method as the Maize topic model (`~/Desktop/maize-topic-modeling`) and the 8500 topic
modeling worksheet. Decisions and open questions are in `DECISIONS.md`.

## Running it

1. Open `topic_model.R` and set `K` (the number of topics) at the top, or give it on the
   command line: `Rscript topic_model.R 20`.
2. Run it, either by sourcing it in RStudio or from this folder:

   ```bash
   Rscript topic_model.R
   ```

   At K = 20 it takes about 5 minutes.

3. Read the results in `output/k<K>/`:

| File | What it is |
|---|---|
| `top_words.csv` | The 10 top words for each topic (also printed when the script runs) |
| `top_words.png` | Bar charts of each topic's top 12 words (beta) |
| `top_documents.csv` | The 5 chunks most about each topic: read these to label a topic |
| `topics_by_widow_material.png` / `.csv` | Average topic share by the kind of widow material in the file |
| `topics_by_transcriber.png` / `.csv` | Average topic share by transcriber (a check on transcription habits) |
| `topics_by_application.csv` | Every application's average share of every topic |
| `document_topics.csv` | Every chunk's share of every topic |
| `model.rds` | The fitted model: `readRDS("output/k20/model.rds")` |

A run with a different `K` goes in its own folder, so you can compare them.

## Other settings

At the top of `topic_model.R`:

- `CHUNK_SIZE`: words per document (default 500)
- `EXTRA_STOPWORDS`: words to drop on top of tidytext's stopword list (legal formula words,
  abbreviations, common first names)
- `DROP_OWN_SURNAMES`: drop each file's own applicant surname from that file only (default `TRUE`)
- `SEED`, `ITER`, `BURNIN`: Gibbs sampling settings from the worksheet

## Differences from the Maize script

- **Text:** `../data/clean_text/` (transcriber brackets and notes removed by `../clean_text.py`),
  joined with `../metadata.csv` by pension code.
- **Documents:** 500-word chunks instead of 1,000, because a file averages about 1,200 words.
- **No topics over time:** the files have no date field. The time plot is replaced by heat maps
  of topic share by `widow_material` and by transcriber.
- **New output:** `top_documents.csv`, the chunks to read when naming each topic.

The scripts read whatever is in `../data/clean_text/`, so rerun after more files are downloaded,
extracted and cleaned.
