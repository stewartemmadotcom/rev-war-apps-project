# Text reuse in the Revolutionary War pension applications

The three scripts from `~/Desktop/11-Text-Reuse` (built for North Carolina session laws), adapted to
the pension transcriptions downloaded from [revwarapps.org](https://revwarapps.org/) in this project.
They find passages that different applicants' files share, even when the copies aren't exact.

| Script | What it does | What you change |
|---|---|---|
| `01_reuse_jaccard_by_hand.py` | N-grams, shingles and Jaccard for two 1832-act declarations, step by step | `TEXT_A`, `TEXT_B`, `N`, `K`, `CLEAN` |
| `02_reuse_minhash.py` | Compares every passage of every file: what formulas run through the files, and what passages do different applicants' files share? | `MATCH`, `BOILERPLATE`, `LOOK_FOR` |
| `03_reuse_trace_clause.py` | Follows one passage through every file that has it, labeled by county, and shows what changed | `START`, `SHARE` (or `python 03_reuse_trace_clause.py "passage" name`) |
| `04_form_and_her_words.py` | How much of each declaration is the acts' form, and a page showing form vs. her words | `SAMPLE`, `SEED` |
| `common.py` | Reads the corpus into passages (used by 02) | `WINDOW`, `STEP`, `WIDOW_WORDS` |

**Corpus: the widow's own documents, `../data/widow_text/`** (from `../split_documents.py`).
Decisions, what the first run showed, and open questions are in `DECISIONS.md`.

## Running it

From the project folder (the project's `.venv` already has numpy):

```bash
cd text_reuse
../.venv/bin/python 01_reuse_jaccard_by_hand.py
../.venv/bin/python 02_reuse_minhash.py     # about 10 seconds
../.venv/bin/python 03_reuse_trace_clause.py  # opens a page in your browser
../.venv/bin/python 04_form_and_her_words.py  # after 02
```

Results go to `output/`: `02_boilerplate.csv` (formula phrases and how many files use them),
`02_families.csv` (every shared passage, grouped into families), `03_trace.html`,
`04_form_share.csv` (each file's share of form words) and `04_form_view.html`.

The scripts read whatever is in `../data/widow_text/`, so rerun them after `../clean_text.py`
and `../split_documents.py`.

## How it differs from the session-laws version

- **Unit: overlapping passages, not sections.** The laws come split into `Sec.` sections. A pension
  file is one run of declarations, affidavits and certificates, and its blank lines are mostly page
  breaks. So `common.py` cuts each file into passages of 80 words, starting every 20 words. With
  150-word passages a shared affidavit of 100 words rarely lined up well enough to score 0.5.
- **Best match from another file, not an earlier year.** The files have no reliable date, and a file
  often repeats its own documents, so `02` keeps each passage's best match from a *different* file.
- **Families.** Passages linked by matches, directly or through others, form a family. So do
  overlapping matched passages in the same file (one long shared document).
- **Boilerplate is reported, not just dropped.** A phrase in more than 5% of files (`BOILERPLATE`) is
  a formula: the oaths the pension acts required ("being first duly sworn according to law doth on
  his oath make the following declaration in order to obtain the benefit of the act of congress").
  `02` prints and saves them before setting them aside.
- **Step 3 searches whole files** and dates each version by the "On this … day of <Month> <year>"
  heading of the declaration it sits in, reading years in figures or in words ("eighteen hundred &
  thirty eight"). That date is a guess, so the order is rough.

## Things to keep in mind

- **These are transcriptions, not OCR.** There are far fewer errors than in the session laws, but each
  transcriber's habits (spelling kept or modernised, "S/" for signatures) change the n-grams.
  `02` prints the match rate by transcriber as a check.
- **Only the widows whose declarations were transcribed.** About two thirds of the files give her
  application only as a transcriber's summary (`widow_material = summary_only` in
  `../metadata.csv`), so they have no widow document. The corpus is the other third.
- **Shared doesn't mean copied from each other.** Most of what the widows' declarations share is
  the acts' required form, set aside as boilerplate. The rarer finds are local, like one claims
  agent's wording for a widow's memories of service used in several Virginia counties
  (DECISIONS.md 4). Earlier whole-file runs found the 1820 property oath, the 1828 act's Treasury
  form, the NC Secretary of State's certificate of service, and one witness's affidavit written
  into several families' files on the same day; those documents are not in this corpus.
- **Only W (widow) files.** The corpus is the widow applications, not all pension files.

## Credits

Method: Kellen Funk and Lincoln Mullen, "The Spine of American Law," *American Historical Review* 123,
no. 1 (2018): 132–164, [doi:10.1093/ahr/123.1.132](https://doi.org/10.1093/ahr/123.1.132).
Transcriptions: Southern Campaigns Revolutionary War Pension Statements, revwarapps.org (transcribers
named in `../metadata.csv`).
