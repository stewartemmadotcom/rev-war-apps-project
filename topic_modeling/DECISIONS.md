# Decision log

Research and data decisions for topic modeling the Revolutionary War pension applications, made by
Emma Stewart (researcher). Claude (coding assistant) proposed options and wrote code; it did
not decide. Entries marked **Open** are defaults set up so the script runs. They aren't
decisions yet.

---

## 1. Method (2026-11-05)

**1.1 LDA in R, following the Maize topic model and the 8500 topic modeling worksheet**
(`topicpractice.R`): tidytext to tokenize, `topicmodels::LDA` with Gibbs sampling (seed 12345,
2,000 iterations, 1,000 burn-in), then beta and gamma.
- *Reasoning:* the same method as the earlier project, so the results can be read the same way.

**1.2 Number of topics (K) is set by hand and changed between runs.** Each run is saved
in `output/k<K>/`. **Open:** the first run uses K = 20. Record the K chosen for analysis, and why,
below once decided.

## 2. Corpus and documents (2026-11-05)

**2.1 Source text:** `../data/clean_text/`, 2,062 applications as of 2026-11-05 (almost all W files),
about 2.5 million words. (The first runs, on 1,071 files, are kept in the k20_default_stopwords and k20_extra_stopwords folders.) `clean_text.py` removed the transcribers' headers, bracketed
insertions, page markers and trailing notes. Transcriber summaries (`../data/notes_text/`) are left
out because they are modern wording, not period text.

**2.2 Document unit: chunks of about 500 words**, cut in reading order within each
application (`CHUNK_SIZE`), giving about 6,100 documents. The last chunk of a file is shorter.
- *Alternatives:* one file per document (2,062 documents, but a file mixes the veteran's
  declaration, the widow's declaration and witnesses' affidavits); 1,000-word chunks as in Maize
  (a file averages about 1,200 words, so most files would be one or two chunks).
- **Open.**

## 3. Cleaning for the model

**3.1 Stopwords: tidytext's `stop_words`, plus numbers removed** (as in the worksheet).

**3.2 Extra stopwords (2026-11-05), chosen after reading the first K = 20 run** (kept in
`output/k20_default_stopwords/`), where formula words and first names filled several topics:
- legal formula of declarations and affidavits: county, aforesaid, declaration, declares,
  declarant, sworn, subscribed, day, personally, appeared, duly, doth, oath, saith, deponent,
  affiant, court, law, resident, hundred, wit, s'd
- abbreviations: wm, capt, col, colo, gen'l
- the 21 first names used 200+ times (john, william, james, … nancy, sarah, andrew). "Henry" is
  kept because it is also a place (Henry County) and a person (Patrick Henry).
- *Kept on purpose:* "act" and "congress" (they help tell the pension acts apart), "widow",
  "husband" and "married", month names, and surnames.
  That run is kept in `output/k20_extra_stopwords/`.

**3.3 Each file's own applicant surname is dropped from that file only (2026-11-05)**
(`DROP_OWN_SURNAMES`). The surname is `last_name` in `../metadata.csv` plus the spellings in
`alt_names`. In the run before this, several topics were shaped by surnames (Brown, Bowman, Baker,
Carter, Anderson). A check found that 51–82% of those uses were in the applicant's own file, with
most coming from a few long files (68 of Bowman's 179 uses are in W27663). Only a minority followed a
military rank ("Colonel Brown", "General Butler").
- *Alternative:* drop those surnames everywhere. That would also remove officers who share an
  applicant's name ("Colonel Brown" in another family's file).
- *Not dropped:* other relatives' surnames (a widow's maiden name, a witness), and place names
  (Bedford, Lewis County).

**3.4 No stemming or spelling normalisation.** Period spellings ("Serjeant", "Genl") and the
transcribers' choices stay as they are. **Open.**

## 4. Not in this corpus

Only applications downloaded so far, almost all widow (W) files; the S and R files aren't here yet.
About two thirds of the files give the widow's own application only as a transcriber summary
(`widow_material = summary_only`), so her words are missing from those files.

## 5. No dates

**5.1 Topics are compared across groups, not over time.** The files have no date field, and one
file holds papers from several decades (the veteran's 1818 or 1832 declaration, the widow's 1836–
1850s declaration). The script compares average topic share by `widow_material` and by transcriber
instead. **Open:** a date per chunk could be guessed from "On this … day of …" headings, as
`../text_reuse/03_reuse_trace_clause.py` does.
