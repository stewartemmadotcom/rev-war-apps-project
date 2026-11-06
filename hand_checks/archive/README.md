# Archived hand-check rounds (do not cite)

These three stratified samples (about 10 files per `widow_material` label) were used
while developing the widow-material detector in `clean_text.py`. They are kept for the
record only.

| File | Files | How it was used |
|---|---|---|
| `widow_check_sample_round1.csv` | 45 | Patterns were tuned to it |
| `widow_check_sample_round2.csv` | 50 | Patterns were tuned to it |
| `widow_check_sample_round3.csv` | 50 | Held out (40/50 agreement), against a detector version that has since changed |

Why they are superseded:

- **Tuning data.** Rounds 1 and 2 shaped the patterns, so scores on them are optimistic.
- **Judged from incomplete notes.** The `claude_label` judgments were made before a fix
  to `clean_text.py` that saves transcriber notes containing nested or unclosed brackets.
  Before that fix, many summaries of the widow's application were missing from
  `data/notes_text/`, so some of these labels are wrong (often `none` or
  `testimony_only` where the file really has a `summary_only` note).
- **Strata no longer match.** Files were drawn 10 per label using the old labels. Most
  old `none` and `testimony_only` files are now `summary_only`.

For the current accuracy figure, use `widow_check_sample_random200.csv` in the project
root, and the independent check in `hand_check_200/` once it is returned. To score the
rare labels, draw a fresh stratified sample from the current labels, excluding these
files:

    python make_widow_check_sample.py --seed 5 --out widow_check_sample_rare.csv \
        --exclude widow_check_sample_random200.csv hand_checks/archive/*.csv
