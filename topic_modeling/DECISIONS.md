# Decision log

**Sections 6 onward (2026-11-05) replace the corpus and document decisions in sections 2 and 4
for the current runs.** Sections 1, 3 and 5 still apply unless a later entry says otherwise.

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

---

## 6. Corpus: the widow's own declarations (2026-11-05)

**6.1 Source text: `../data/widow_text/`** (from `../split_documents.py`): only the documents in
which the widow is the speaker. 1,491 files, 2,029 declarations, about 830,000 words. Replaces
2.1 (whole files in `../data/clean_text/`, which mixed in the soldier's declaration, witnesses
and records). Same corpus as the text reuse (`../text_reuse/DECISIONS.md` 1.1).
- *Alternative:* whole files, 4,753 files, about 6 million words; topics would mostly be about
  the soldiers' service.

**6.2 Document unit: each declaration whole.** A file's widow documents are separate
paragraphs in `widow_text/`; each is one document (`W1234_d1`, `W1234_d2`, ...). Declarations
under 100 words (about 60) are dropped as too short to have topics (`MIN_WORDS`). Replaces 2.2
(500-word chunks).
- *Reasoning:* one declaration is one act of speaking, so its topic shares describe that
  declaration. The median is 349 words (most 185 to 690), so chunking isn't needed.
- *Alternatives:* 500-word chunks; one document per file (joins declarations made years apart).

**6.3 Form language: two runs, with and without the acts' form phrases.**
- *With form:* the declarations as they are, with the stopword lists in section 3.
- *Without form:* the words inside the 164 five-word phrases found in more than 10% of files
  (`../text_reuse/DECISIONS.md` 3.1, `../text_reuse/output/02_boilerplate.csv`) are removed
  first, by `../text_reuse/04_form_and_her_words.py`, which writes `../data/widow_text_noform/`.
- *Reasoning:* comparing the two shows what the form does to the topics. Measured before the
  run: with the form, "act", "congress", "passed", "obtain", "benefit" and "provision" are among
  the top 40 words; without it, "battle", "heard", "regiment", "colonel", "born" and "believes"
  rise into the top 40.

**6.4 Kept from the earlier runs, not yet revisited:** stopwords (3.1, 3.2), dropping each
file's own surname (3.3), no stemming or spelling normalisation (3.4), Gibbs settings (1.1).
**Open:** K. The first runs use K = 12, the last setting used.

**6.5 Groups compared: transcriber only.** The `widow_material` heat map is dropped: nearly all
widow declarations come from `transcribed` files, so it no longer separates anything.

## 7. What the first widow runs showed (K = 12, 2026-11-05)

Not decisions; recorded so the open questions below have their evidence. 1,973 declarations
(100+ words) from 1,478 applications: 844,072 words with the form, 694,801 without.

- **With the form, two topics are the acts' templates**: "widow, july, married, act, passed,
  congress, proof, died, obtain, benefit" (the 1838 act's opening) and "act, january, married,
  widows, pensions, previous, granting, entitled, leaving, marriage" (its title, and the rule
  that the marriage was before 1 January 1794). Removing the form takes both away.
- **Without the form, the space goes to**: married life and family ("married, widow, lived,
  time, death, father, wife, brother, acquainted"), and two writing conventions rather than
  content: dates written out in words ("aged, eighty, seventy, ... seventeen, eighteen,
  ninety", led by Maryland courts' "twenty second day ... one thousand eight hundred and
  thirty six") and signatures and jurats ("mark, aged, jp, written, acting", led by North
  Carolina and Tennessee justices).
- **In both runs**: his war (british, tories, indians, river, battle); militia tours (months,
  captain, tour, company, marched); the family record (record, born, marriage, family,
  children, bible); South Carolina and Georgia service; the Virginia line, land and pay; and
  how she knows ("husband, service, time, heard, recollect, battle, entered, officers,
  recollects"), led by declarations from Spotsylvania and Essex counties, Virginia.
- **Place and clerk shape topics.** Several topics are led by one state's or one county's
  declarations, as the text reuse found for wording (`../text_reuse/DECISIONS.md` 4).

## 8. Open questions from the first widow runs

- **8.1 With or without the form** for the runs to analyse. Without loses the act templates
  but gains family and knowledge topics.
- **8.2 Number words** ("seventy", "eighty", "eighteen", "twenty") as stopwords, so dates and
  ages written in words don't make a topic.
- **8.3 Signature and jurat words** below the 10% form line ("mark", "jp", "acting", "written",
  "peace") as stopwords.
- **8.4 State and county names.** Keep (place is part of the story) or drop (so topics are
  about content, and place is compared afterwards).
- **8.5 K.** 12 so far; try fewer and more once the stopwords are settled.

## 9. Runs at K = 20 (2026-11-05)

Both versions rerun at K = 20 (`output/widow_k20/`, `output/widow_k20_noform/`), everything
else as in section 6. Topics were paired across the two runs by the cosine similarity of their
word weights. Labels are Claude's readings of the top words, to be checked against
`top_documents.csv`.

- **17 of 20 pairs match closely (0.83 or more)**, one loosely (0.59). As at K = 12, the two
  with-form topics without a match are the 1838 act's wording (its opening oath; its title and
  marriage rule). Without the form, their place goes to "marching and coming home" and "where
  she lived, what she was told" (husband, georgia, resided, believes, informed).
- **New compared with K = 12** (no close match among the 12 without-form topics): officers and
  command; birth and marriage dates; petitions to a state legislature ("honorable,
  petitioner"); Charleston and prisoners; months and his death; where she lived and what she
  was told. K = 20 splits the earlier broad topics: the war into officers, marching and
  Charleston; the family into dates and the family record.
- **The writing habits stay**: dates and ages in words, and North Carolina and Tennessee jurats,
  are still topics at K = 20 (8.2, 8.3).

## 10. Runs at K = 30 (2026-11-05)

Both versions rerun at K = 30 (`output/widow_k30/`, `output/widow_k30_noform/`), paired as in
section 9.

- **19 of 30 pairs match closely (0.83 or more)**, 5 loosely (0.5 to 0.8), and 6 weakly or not
  at all, against 17 of 20 at K = 20. The two runs agree less as K rises.
- **New compared with K = 20**, among the without-form topics: battles and wounds (Guilford);
  Kentucky; enlistment and discharge; officers' rank and commission; pay office certificates;
  evidence and papers sent to the department; coming home from the army; where he served and
  what she believes.
- **Signs of too many topics:** first names lead some topics ("jane", "henry", "ann",
  "alexander"), place and clerk topics multiply (Ohio's "a.d., ss"; Tennessee justices), the
  family record splits into near-duplicates (births; marriage evidence), and leftover act
  words make their own topic ("widows, acts, pensions").

## 11. The whole corpus, by document (2026-11-06)

A second corpus, alongside the widow runs (section 6), to see which topics belong to soldiers,
widows and witnesses.

**11.1 Source text: every document `../split_documents.py` found**, written to
`../data/doc_text/` (one file per application, one document per paragraph, in the order of
`../documents.csv`). 4,752 files, 19,552 documents, about 6 million words.

**11.2 Document unit: each document whole, 100 words or more** (`MIN_WORDS`).
- *Alternatives:* 500-word chunks of whole files (the earliest runs; a chunk can join the end
  of one document to the start of the next); one document per file (4,752 documents, each
  mixing soldier, widow and witnesses).

**11.3 Document types: all but `other`.** Soldier's declarations, widow's declarations,
testimony, records and heirs' claims go in. `other` (3,567 documents, median 51 words) is mostly
fragments and splitter leftovers.
- *Alternatives:* everything; declarations only (soldiers, widows, heirs).

**11.4 Form removed across all types, by the same rule as the widows**: words inside a 5-word
phrase found in more than 10% of files are removed first (`../remove_form.py`, which writes
`../data/doc_text_noform/` and `output/whole_boilerplate.csv`). The phrases are counted over
the included types, so the soldiers' 1832 oath and the courts' certificates count as form as
well as the widows' acts.
- *Alternatives:* stopwords only (as in the earliest whole-file runs); both.

**11.5 Groups compared: document type and transcriber.** K = 30 for the first run; stopwords,
surnames and Gibbs settings as in 6.4.

## 12. First whole-corpus run (K = 30, form removed, 2026-11-06)

`output/whole_k30_noform/`. 13,482 documents of 100+ words from 4,737 applications, 4,645,553
words after removing the form; about 9 minutes. Topic share by document type is in
`topics_by_type.csv` / `.png`. Labels are Claude's readings of the top words.

- **Soldiers' declarations** lean to the war itself: marching against the British and Tories
  (7.8% of a declaration, against 2-3% elsewhere), drafted tours and marching home (7.5%),
  Indian expeditions and forts, battles (Guilford, Camden), Yorktown and Richmond, where he
  lived and moved, North Carolina courts, answers to the court's questions.
- **Widows' declarations and heirs' claims** share one dominant topic: marriage, his death and
  children (11.6% and 15.5%, against 1-4% elsewhere). Widows also lean to "what she recollects,
  believes", ages and dates in words, and the acts; heirs to what relatives heard and knew, and
  bounty land and petitions.
- **Testimony** leans to property and poverty, continental enlistment, witnesses and jurats,
  and militia tours.
- **Records** lean to certificates and the pay office (8.8%), birth dates (8.0%), and answers to
  the court's questions.
- **Shares look flat (mostly 2-4%)**: with Gibbs LDA's default prior, each document spreads
  over many topics, so a type's distinctive topics show as 4-15% against about 3%.

**Splitter labels to keep in mind** (`../split_documents.py`): "property and poverty" (the 1820
schedules of a soldier's property) leans to testimony, and "answers to the court's questions"
(the 1832 interrogatories) to records, so some soldiers' documents are typed as testimony or
records. Topics by type are only as good as the types.

**Open:** K for the whole corpus; whether to run it with the form for comparison; the stopword
questions in section 8 apply here too (names lead topic 26: henry, smith, lewis).
