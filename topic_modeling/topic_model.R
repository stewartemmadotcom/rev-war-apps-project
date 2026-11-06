# ==============================================================================
# Topic modeling the Revolutionary War pension applications (revwarapps.org)
#
# Same method as the Maize topic model (~/Desktop/maize-topic-modeling) and the
# 8500 topic modeling worksheet (topicpractice.R): tidytext to tokenize,
# topicmodels' LDA with Gibbs sampling, then beta (words per topic) and gamma
# (topics per document).
#
# Documents are the widow's own declarations, one per document (DECISIONS.md 6):
# ../data/widow_text/ holds one file per application with one declaration per
# paragraph (../split_documents.py). Declarations under MIN_WORDS are dropped.
# With FORM_REMOVED, the same declarations are read from
# ../data/widow_text_noform/, where the words of the acts' form phrases have
# been taken out (../text_reuse/04_form_and_her_words.py; DECISIONS.md 6.3).
# Joined with ../metadata.csv.
#
# With CORPUS = "whole", the documents are every document in every file
# (../data/doc_text/, or ../data/doc_text_noform/ from ../remove_form.py), with
# their types from ../documents.csv; types in EXCLUDED_TYPES are left out
# (DECISIONS.md 11), and topics are also compared by document type.
#
# The files have no date, so instead of topics over time this compares topics
# across transcribers (DECISIONS.md 5, 6.5).
#
# To run: change K and FORM_REMOVED below, then source this file in RStudio or run
#   Rscript topic_model.R            # K and FORM_REMOVED as set below
#   Rscript topic_model.R 12 noform  # K = 12, form removed
#   Rscript topic_model.R 30 noform whole  # the whole corpus
# Everything is saved in output/<corpus>_k<K>/ or output/<corpus>_k<K>_noform/,
# so runs with different settings don't overwrite each other.
# ==============================================================================

library(tidyverse)
library(tidytext)
library(topicmodels)

# --- Settings (change these) --------------------------------------------------

K <- 12                 # number of topics (DECISIONS.md 6.4, open)
CORPUS <- "widow"       # "widow": her declarations (6); "whole": every document (11)
EXCLUDED_TYPES <- c("other")  # whole corpus only (DECISIONS.md 11.3)
FORM_REMOVED <- FALSE   # TRUE: read the declarations without the acts' form phrases
MIN_WORDS <- 100        # shorter declarations are dropped (DECISIONS.md 6.2)
SEED <- 12345
ITER <- 2000
BURNIN <- 1000

# Words to drop on top of tidytext's stop_words (DECISIONS.md 3)
EXTRA_STOPWORDS <- c(
  # Legal formula of the declarations and affidavits
  "county", "aforesaid", "declaration", "declares", "declarant", "sworn", "subscribed",
  "day", "personally", "appeared", "duly", "doth", "oath", "saith", "deponent", "affiant",
  "court", "law", "resident", "hundred", "wit", "s'd",
  # Abbreviations
  "wm", "capt", "col", "colo", "gen'l",
  # First names used 200+ times ("Henry" is left in: Henry County, Patrick Henry)
  "john", "william", "james", "thomas", "joseph", "george", "samuel", "robert", "mary",
  "benjamin", "elizabeth", "charles", "david", "richard", "jacob", "daniel", "edward",
  "peter", "nancy", "sarah", "andrew"
)

# Drop each file's own applicant surname (and its spellings in alt_names) from
# that file only, so a family name repeated through its own file doesn't make
# a topic, but "Colonel Brown" in someone else's file stays (DECISIONS.md 3.3)
DROP_OWN_SURNAMES <- TRUE

# Where the documents and their metadata are
METADATA_CSV <- "../metadata.csv"
DOCUMENTS_CSV <- "../documents.csv"

# ------------------------------------------------------------------------------

# Optional: give K, and "noform", on the command line instead
cli <- commandArgs(trailingOnly = TRUE)
k_arg <- suppressWarnings(as.integer(cli[1]))
if (!is.na(k_arg)) K <- k_arg
if ("noform" %in% cli) FORM_REMOVED <- TRUE
if ("whole" %in% cli) CORPUS <- "whole"

CORPUS_FOLDER <- if (CORPUS == "whole") "../data/doc_text" else "../data/widow_text"
NOFORM_FOLDER <- paste0(CORPUS_FOLDER, "_noform")

# Run from this script's folder, whether sourced in RStudio or run with Rscript
script_dir <- tryCatch(dirname(sys.frame(1)$ofile), error = function(e) NULL)
if (is.null(script_dir)) {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
  script_dir <- if (length(file_arg)) dirname(file_arg) else "."
}
setwd(script_dir)

out_dir <- file.path("output", paste0(CORPUS, "_k", K, if (FORM_REMOVED) "_noform" else ""))
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ==============================================================================
# LOAD THE APPLICATIONS AND THEIR METADATA
# ==============================================================================

files <- list.files(CORPUS_FOLDER, pattern = "\\.txt$", full.names = TRUE)
if (length(files) == 0) stop("No .txt files in ", CORPUS_FOLDER, ". Run ../split_documents.py first.")
if (FORM_REMOVED && !dir.exists(NOFORM_FOLDER))
  stop("No ", NOFORM_FOLDER, ". Run ",
       if (CORPUS == "whole") "../remove_form.py" else "../text_reuse/04_form_and_her_words.py",
       " first.")

metadata <- read_csv(METADATA_CSV, show_col_types = FALSE) %>%
  transmute(code = toupper(code),
            name = str_squish(paste(first_name, last_name)),
            transcriber = replace_na(transcriber, "(unknown)"),
            widow_material = replace_na(widow_material, "(not checked)")) %>%
  distinct(code, .keep_all = TRUE)

# Each file's own surnames, one word per row: last_name plus the spellings in
# alt_names ("Abernathy; Abernathey"), split into words ("Baury de Bellerive")
own_surnames <- read_csv(METADATA_CSV, show_col_types = FALSE) %>%
  transmute(code = toupper(code),
            names = paste(last_name, replace_na(alt_names, ""))) %>%
  unnest_tokens(word, names) %>%
  filter(nchar(word) > 2, !word %in% c("de", "van", "von", "the")) %>%
  distinct(code, word)

# One row per declaration: the paragraphs of each file. File names are pension
# codes, e.g. w10287.txt -> W10287; declarations are W10287_d1, W10287_d2, ...
read_declarations <- function(folder) {
  tibble(path = file.path(folder, basename(files))) %>%
    mutate(code = toupper(tools::file_path_sans_ext(basename(path))),
           text = map(path, ~ str_split(read_file(.x), "\n\n")[[1]])) %>%
    select(-path) %>%
    unnest_longer(text, indices_to = "n") %>%
    mutate(document = sprintf("%s_d%d", code, n))
}

declarations <- read_declarations(CORPUS_FOLDER) %>%
  mutate(words = str_count(text, "\\S+"),
         opening = str_trunc(str_squish(text), 300))

if (CORPUS == "whole") {
  # Each document's type from documents.csv (same files, same numbering)
  doc_types <- read_csv(DOCUMENTS_CSV, show_col_types = FALSE) %>%
    transmute(document = sprintf("%s_d%d", toupper(tools::file_path_sans_ext(pdf_filename)), doc),
              type)
  declarations <- declarations %>%
    inner_join(doc_types, by = "document") %>%
    filter(!type %in% EXCLUDED_TYPES)
} else {
  declarations <- declarations %>% mutate(type = "widow_declaration")
}

declarations <- declarations %>% filter(words >= MIN_WORDS)
cat(nrow(declarations), "documents of", MIN_WORDS, "words or more from",
    n_distinct(declarations$code), "applications\n")

if (FORM_REMOVED) {
  # Same declarations, same numbering, with the form words taken out
  declarations <- declarations %>%
    select(-text) %>%
    inner_join(read_declarations(NOFORM_FOLDER) %>% select(document, text), by = "document")
}

declarations <- declarations %>%
  left_join(metadata, by = "code") %>%
  mutate(name = replace_na(name, ""),
         transcriber = replace_na(transcriber, "(unknown)"),
         widow_material = replace_na(widow_material, "(not checked)"),
         label = str_squish(paste(code, name)))

doc_info <- declarations %>%
  select(document, code, label, type, transcriber, widow_material, words, opening)

tokens <- declarations %>%
  select(document, code, text) %>%
  unnest_tokens(word, text)

cat(nrow(tokens), "words", if (FORM_REMOVED) "after removing the form" else "", "\n")

# ==============================================================================
# CLEAN AND BUILD THE DOCUMENT-TERM MATRIX
# ==============================================================================

tidy_pensions <- tokens %>%
  filter(str_detect(word, "[a-z']$")) %>%        # keep only words
  anti_join(stop_words, by = "word") %>%         # remove stopwords
  filter(!word %in% EXTRA_STOPWORDS) %>%
  filter(!grepl("[0-9]", word))                  # remove numbers

if (DROP_OWN_SURNAMES) {
  before <- nrow(tidy_pensions)
  tidy_pensions <- tidy_pensions %>% anti_join(own_surnames, by = c("code", "word"))
  cat("Dropped", before - nrow(tidy_pensions), "uses of applicants' own surnames\n")
}

pension_dtm <- tidy_pensions %>%
  count(document, word) %>%
  cast_dtm(document, word, n)

# ==============================================================================
# FIT THE MODEL
# ==============================================================================

cat("Fitting LDA with k =", K, "(this can take several minutes) ...\n")
pension_lda <- LDA(pension_dtm,
                   k = K,
                   method = "Gibbs",
                   control = list(seed = SEED, iter = ITER, burnin = BURNIN))
saveRDS(pension_lda, file.path(out_dir, "model.rds"))

# ==============================================================================
# EXAMINE THE TOPICS (BETA)
# ==============================================================================

pension_topics <- tidy(pension_lda, matrix = "beta")

top_terms <- pension_topics %>%
  group_by(topic) %>%
  slice_max(beta, n = 10, with_ties = FALSE) %>%
  ungroup() %>%
  arrange(topic, desc(beta))

# One line per topic, easy to read and label
top_terms %>%
  group_by(topic) %>%
  summarise(top_words = paste(term, collapse = ", ")) %>%
  write_csv(file.path(out_dir, "top_words.csv")) %>%
  { for (i in seq_len(nrow(.))) cat(sprintf("Topic %2d: %s\n", .$topic[i], .$top_words[i])) }

top_plot <- pension_topics %>%
  group_by(topic) %>%
  slice_max(beta, n = 12, with_ties = FALSE) %>%
  ungroup() %>%
  mutate(term = reorder_within(term, beta, topic)) %>%
  ggplot(aes(beta, term, fill = factor(topic))) +
  geom_col(show.legend = FALSE) +
  facet_wrap(~ topic, scales = "free") +
  scale_y_reordered() +
  labs(title = paste0("Top Words in Pension Application Topics (k = ", K, ")"),
       x = "Beta (word-topic probability)", y = NULL)
ggsave(file.path(out_dir, "top_words.png"), top_plot, width = 14, height = 10)

# ==============================================================================
# TOPICS PER DOCUMENT AND APPLICATION (GAMMA)
# ==============================================================================

pension_docs <- tidy(pension_lda, matrix = "gamma") %>%
  left_join(doc_info, by = "document")
write_csv(pension_docs, file.path(out_dir, "document_topics.csv"))

# Average each topic's share across an application's declarations
topics_by_application <- pension_docs %>%
  group_by(code, label, transcriber, widow_material, topic) %>%
  summarise(gamma = mean(gamma), .groups = "drop")
write_csv(topics_by_application, file.path(out_dir, "topics_by_application.csv"))

# The declarations that are most about each topic: read these to label a topic
top_documents <- pension_docs %>%
  group_by(topic) %>%
  slice_max(gamma, n = 5, with_ties = FALSE) %>%
  ungroup() %>%
  select(topic, gamma, document, label, type, words, opening)
write_csv(top_documents, file.path(out_dir, "top_documents.csv"))

# ==============================================================================
# TOPICS BY GROUP (instead of over time: the files have no dates)
# ==============================================================================

# Average share of each topic in each group of applications, as a heat map
group_plot <- function(group_col, title, file) {
  by_group <- topics_by_application %>%
    group_by(group = .data[[group_col]], topic) %>%
    summarise(gamma = mean(gamma), files = n(), .groups = "drop") %>%
    mutate(group = paste0(group, " (", files, ")"))
  write_csv(by_group, file.path(out_dir, paste0(file, ".csv")))
  p <- by_group %>%
    ggplot(aes(x = factor(topic), y = group, fill = gamma)) +
    geom_tile() +
    scale_fill_viridis_c() +
    theme_minimal() +
    labs(title = title, x = "Topic", y = NULL, fill = "Average\nproportion\n(gamma)")
  ggsave(file.path(out_dir, paste0(file, ".png")), p, width = 12, height = 4)
}

# By document type, averaging over documents (not applications): which topics
# belong to soldiers, widows, witnesses (DECISIONS.md 11.5)
if (CORPUS == "whole") {
  by_type <- pension_docs %>%
    group_by(type, topic) %>%
    summarise(gamma = mean(gamma), documents = n(), .groups = "drop") %>%
    mutate(group = paste0(type, " (", documents, ")"))
  write_csv(by_type, file.path(out_dir, "topics_by_type.csv"))
  type_plot <- by_type %>%
    ggplot(aes(x = factor(topic), y = group, fill = gamma)) +
    geom_tile() +
    scale_fill_viridis_c() +
    theme_minimal() +
    labs(title = paste0("Topic Share by Document Type (k = ", K, ")"),
         x = "Topic", y = NULL, fill = "Average\nproportion\n(gamma)")
  ggsave(file.path(out_dir, "topics_by_type.png"), type_plot, width = 14, height = 4)
}

# Transcribers with at least 10 files: a check that topics aren't one
# transcriber's conventions
big_transcribers <- declarations %>% distinct(code, transcriber) %>% count(transcriber) %>%
  filter(n >= 10) %>% pull(transcriber)
topics_by_application <- topics_by_application %>% filter(transcriber %in% big_transcribers)
group_plot("transcriber",
           paste0("Topic Share by Transcriber (k = ", K, ")"),
           "topics_by_transcriber")

cat("\nSaved to", out_dir, "\n")
