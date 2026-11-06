# ==============================================================================
# Topic modeling the Revolutionary War pension applications (revwarapps.org)
#
# Same method as the Maize topic model (~/Desktop/maize-topic-modeling) and the
# 8500 topic modeling worksheet (topicpractice.R): tidytext to tokenize,
# topicmodels' LDA with Gibbs sampling, then beta (words per topic) and gamma
# (topics per document).
#
# Documents are chunks of about CHUNK_SIZE words, cut in reading order from
# each application (DECISIONS.md 2). The text is ../data/clean_text/ (one file
# per application, transcriber brackets and notes removed by ../clean_text.py),
# joined with ../metadata.csv.
#
# The files have no date, so instead of topics over time this compares topics
# across the kind of widow material in each file (widow_material, from
# ../clean_text.py) and across transcribers (DECISIONS.md 5).
#
# To run: change K below, then source this file in RStudio or run
#   Rscript topic_model.R
# Everything is saved in output/k<K>/, so runs with different K don't
# overwrite each other.
# ==============================================================================

library(tidyverse)
library(tidytext)
library(topicmodels)

# --- Settings (change these) --------------------------------------------------

K <- 12                 # number of topics
CHUNK_SIZE <- 500       # words per document
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

# Where the cleaned applications and their metadata are
CORPUS_FOLDER <- "../data/clean_text"
METADATA_CSV <- "../metadata.csv"

# ------------------------------------------------------------------------------

# Optional: give K on the command line instead (Rscript topic_model.R 20)
k_arg <- suppressWarnings(as.integer(commandArgs(trailingOnly = TRUE)[1]))
if (!is.na(k_arg)) K <- k_arg

# Run from this script's folder, whether sourced in RStudio or run with Rscript
script_dir <- tryCatch(dirname(sys.frame(1)$ofile), error = function(e) NULL)
if (is.null(script_dir)) {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
  script_dir <- if (length(file_arg)) dirname(file_arg) else "."
}
setwd(script_dir)

out_dir <- file.path("output", paste0("k", K))
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ==============================================================================
# LOAD THE APPLICATIONS AND THEIR METADATA
# ==============================================================================

files <- list.files(CORPUS_FOLDER, pattern = "\\.txt$", full.names = TRUE)
if (length(files) == 0) stop("No .txt files in ", CORPUS_FOLDER, ". Run ../clean_text.py first.")

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

# File names are pension codes, e.g. w10287.txt -> W10287
applications <- tibble(path = files) %>%
  mutate(code = toupper(tools::file_path_sans_ext(basename(path))),
         text = map_chr(path, read_file)) %>%
  left_join(metadata, by = "code") %>%
  mutate(name = replace_na(name, ""),
         transcriber = replace_na(transcriber, "(unknown)"),
         widow_material = replace_na(widow_material, "(not checked)"),
         label = str_squish(paste(code, name))) %>%
  arrange(code)

# ==============================================================================
# CUT EACH APPLICATION INTO ~CHUNK_SIZE-WORD DOCUMENTS
# ==============================================================================

# Tokenize first (keeping every word, in order), then number the chunks,
# so each chunk has CHUNK_SIZE words of running text before stopwords go
tokens <- applications %>%
  select(code, label, transcriber, widow_material, text) %>%
  unnest_tokens(word, text) %>%
  group_by(code) %>%
  mutate(chunk = (row_number() - 1) %/% CHUNK_SIZE + 1) %>%
  ungroup() %>%
  mutate(document = sprintf("%s_c%03d", code, chunk))

chunk_info <- tokens %>%
  distinct(document, code, label, transcriber, widow_material, chunk)

cat(nrow(applications), "applications,", nrow(tokens), "words,", nrow(chunk_info), "documents\n")

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
  left_join(chunk_info, by = "document")
write_csv(pension_docs, file.path(out_dir, "document_topics.csv"))

# Average each topic's share across an application's chunks
topics_by_application <- pension_docs %>%
  group_by(code, label, transcriber, widow_material, topic) %>%
  summarise(gamma = mean(gamma), .groups = "drop")
write_csv(topics_by_application, file.path(out_dir, "topics_by_application.csv"))

# The chunks that are most about each topic: read these to label a topic
top_documents <- pension_docs %>%
  group_by(topic) %>%
  slice_max(gamma, n = 5, with_ties = FALSE) %>%
  ungroup() %>%
  select(topic, gamma, document, label, widow_material)
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

group_plot("widow_material",
           paste0("Topic Share by Widow Material in the File (k = ", K, ")"),
           "topics_by_widow_material")

# Transcribers with at least 10 files: a check that topics aren't one
# transcriber's conventions
big_transcribers <- applications %>% count(transcriber) %>% filter(n >= 10) %>% pull(transcriber)
topics_by_application <- topics_by_application %>% filter(transcriber %in% big_transcribers)
group_plot("transcriber",
           paste0("Topic Share by Transcriber (k = ", K, ")"),
           "topics_by_transcriber")

cat("\nSaved to", out_dir, "\n")
