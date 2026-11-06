# Decision log

Research and data decisions for text reuse on the Revolutionary War pension applications, made by
Emma Stewart (researcher). Claude (coding assistant) proposed options and wrote code; it did
not decide. Entries marked **Open** are defaults set up so the scripts run. They aren't
decisions yet.

---

## 1. Corpus (2026-11-05)

**1.1 The widow's own documents: `../data/widow_text/`**, written by `../split_documents.py`.
1,491 files, about 831,000 words: only the declarations, petitions and letters in which the
widow is the speaker. The soldier's declaration, witnesses' affidavits, certificates and
records are left out.
- *Reasoning:* the question is which parts of her declaration were the acts' form and which
  were hers, and which widows' declarations were written with the same wording.
- *Alternatives:* whole files (`../data/clean_text/`, 4,753 files, about 6 million words),
  better for tracing official forms and witnesses through the paperwork; or both, run
  separately and compared.
- The earlier runs (2,062 whole files, before the cleaning fixes) are superseded.

## 2. Purpose of the first run (2026-11-05)

**2.1 Both:** (a) separate the acts' form language from the rest of each declaration, and
(b) find clusters of declarations that share unusual wording (the same clerk, court or
claims agent writing for several widows).

## 3. Settings

**3.1 Boilerplate line: a 5-word phrase in more than 10% of files is form**
(`BOILERPLATE = 0.10` in `02_reuse_minhash.py`). Measured on the widow documents before
choosing:

| Line | Phrases counted as form | Share of a typical declaration |
|---|---|---|
| 25% of files | 89 | 16% |
| **10% of files** | **164** | **21%** |
| 5% of files (the earlier setting) | 345 | 27% |
| 2% of files | 1,067 | 35% |

- *Reasoning:* 10% catches the acts' required oath and conditions ("duly sworn according to
  law", "that she was not married to [him prior to his leaving the service]", "and that she has
  remained [a widow]") but leaves court- and clerk-level habits ("acting justices of the
  peace") to be found as shared wording. At 5%, common first names start to cross the line
  ("is the widow of william", 147 files).

**3.2 Match threshold: two passages match if they share at least half their 5-word phrases**
(`MATCH = 0.5`, Jaccard). **Open.** Lower (0.3) finds looser copies of the same form;
higher finds only near-identical passages.

**3.3 Passages of 80 words, a new one every 20 words** (`WINDOW`, `STEP` in `common.py`),
carried over from the whole-file runs. **Open.** A widow's declaration is about 470 words
(median), so it gives about 20 overlapping passages.

## 4. What the first run showed (2026-11-05)

Not decisions; recorded so the open questions below have their evidence.

- **Form is 18% of all words; 21% of a typical declaration** (median; middle half 13% to 32%).
  The most template-like are short declarations (W7589, 77% form). 107 files are under 5% form:
  petitions to a state legislature (W10185), but also family records the splitter took for
  her declaration (W1466, W11044).
- **At `MATCH = 0.5`, 45 files (3%) share a passage with another file** beyond the form.
  Similar by transcriber (Graves 2%, Harris 4%), so it is not one transcriber's habit.
- **A claims agent's or clerk's wording for her memories.** "She recollects distinctly hearing
  him repeat over and over again that he was a considerable length of time in actual service,
  was engaged in many battles, and suffered many hardships and privations. That from bodily
  infirmity, old age, and the consequent loss of memory, she cannot call to recollection the
  particulars ..." appears in declarations from Halifax, Charlotte, Campbell and Lunenburg
  counties, Virginia, 1839-1843 (W6339, W8130, W18929, W7505, W3865, W5508), transcribed by both
  Harris and Graves.
- **Not reuse, but artifacts:** the same file under two codes (W6992 and W8665; W18396 and
  W19616, which hold the declarations of two widows of one man), and a Virginia certificate of
  service attached to the end of her declaration by the splitter (family 1, 10 files).

**Second run, `MATCH = 0.3`** (`python 02_reuse_minhash.py 0.3`, saved to
`output/02_families_match0.3.csv`; the 0.5 results are kept in `02_families.csv`):

- **297 files (20%)** share a passage with another file beyond the form, up from 45. Again even
  across transcribers (Graves 20%, Harris 19%).
- **Two kinds of family.** Counties and years were read from each family's declarations (a rough
  count from the opening lines):
  - *Local*, in one county or a few neighbouring ones over a few years: a clerk's or agent's own
    version of the declaration. Lunenburg, Charlotte and Buckingham counties, Virginia, 1838-1844
    (27 files, family 2) and the "hardships and privations" wording, now 10 files (family 6);
    Bedford and Chesterfield counties, Virginia, 1839-1842 (9); the federal court in Charleston,
    1836-1838 (8); Johnston County, North Carolina, 1842-1847 (7, and another 5); Woodford,
    Shelby and Jessamine counties, Kentucky, 1843 (5).
  - *Spread out*, in many states over decades: looser versions of the acts' forms that fell
    under the 10% line (families 1, 3, 4: 30, 20 and 19 files), and federal certificates quoted
    into the declaration (family 11, "Department of the Interior ... I certify").
- So at 0.3 a family's spread over places and years is what tells a local writer from a form.

**Tracing the Lunenburg/Charlotte family** (`03_reuse_trace_clause.py`, page
`output/03_trace_lunenburg_charlotte.html`). Its own wording, "for which length of time she
claims a pension. In support of her claim she refers to ...", is in 20 widows' declarations,
all in Southside Virginia: Charlotte and Lunenburg counties from 1839 (with Halifax), Nottoway
in 1840, Campbell from 1841, Buckingham in 1842, Halifax again in 1844. The same block carries
"for the same reason she cannot state precisely how long he was in actual service" and the
"hardships and privations" wording. One writer, or one office's template, moving west from
Charlotte and Lunenburg over five years.

## 5. Open questions from the first run

- **5.1 Match threshold.** 0.5 finds near-copies (45 files); 0.3 finds the local clusters and
  looser forms (297 files). The default stays 0.5 until decided; 0.3 is run separately.
- **5.2 Duplicate files.** Drop one of each pair that holds the same documents, or keep both.
- **5.3 Records taken for her declaration.** Fix the splitter for family records and attached
  certificates, or leave them and note it.
