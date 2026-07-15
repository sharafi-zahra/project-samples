# Immigrants in the Labor Market — Survey Analysis

Analysis of a survey comparing early labor-market outcomes between immigrant and native
university graduates in Germany: starting wages, job-search behavior, beliefs about wage gaps,
and perceived reasons for differing outcomes.

This project exists in two forms: early exploratory notebooks (`src/`) and a later, properly
structured analysis package (`package/`) built on [pytask](https://pytask-dev.readthedocs.io/).

## `src/` — exploratory notebooks

- **`ttest.ipynb`** — earliest pass: builds the immigrant/native indicator from two screening
  questions, then runs group t-tests across a handful of key outcome variables (reservation
  wage, starting salary, expected future earnings, perceived wage gaps).
- **`overview20250127.ipynb`** / **`overview20250130.ipynb`** — fuller, iterative analysis
  (20250130 is the more complete version):
  - Builds the immigrant dummy and recodes value-labeled survey responses using a codebook
    mapping table.
  - Cleans wages (drops sub-minimum-wage and implausibly high responses) and restricts
    comparisons to comparable degree levels (mainly Master's students).
  - **Mincer-style wage regressions** (`statsmodels`, HC1 robust SE) on log starting salary,
    controlling for gender and degree.
  - Degree-field clustering (STEM / Business & Economics / Social Sciences & Law) to compare
    outcomes within comparable fields of study.
  - Group comparisons (t-test, Mann-Whitney U, Fisher's exact test) across job-search behavior
    (applications sent, search radius, time to first offer, offer acceptance), beliefs about
    wage gaps and career prospects, self-assessed risk tolerance/confidence, and which factors
    respondents believe drove their job-search outcomes.

## `package/` — `img_labormarket` analysis pipeline

A proper reproducible-research package built with `pytask`:

- **`src/img_labormarket/config.py`** — project paths (`SRC`/`BLD` convention).
- **`src/img_labormarket/data_management/`** — `task_pred_data.py` builds the cleaned analysis
  dataset from the raw survey export: constructs the immigrant dummy (with several variants —
  full-info-only, schooling-based, birth-based), maps respondent nationality to EU/non-EU,
  recodes degree field into subject clusters, computes CPI-deflated real wages and a
  minimum-wage benchmark by year, and hand-codes free-text industry/sector responses into
  consistent categories. `help_data.py` holds shared coding/labeling and wage-restriction helpers.
- **`src/img_labormarket/analysis/`** — the main analysis notebooks (`overview`, `descriptives`,
  `wages`, `job_search`, `personality_and_beliefs`), each isolating one part of the
  immigrant/native comparison, plus a parallel **`Gender analysis/`** subfolder repeating the
  comparisons split by gender. `help_analysis.py` / `help_analysis_new.py` hold shared
  comparison and Likert-scale helper functions.

## Notes

- Notebooks are included as code only — all cell outputs have been stripped, since the original
  outputs contained actual (unpublished) study results from a co-authored project. Re-running
  requires the underlying survey dataset and codebook, which are not included here.
- Column names are raw survey question IDs (e.g. `Q36r1`, `Q45_a`); the notebooks recode and
  label these using a separate value-codings mapping file (not included).
- One hardcoded dictionary entry in `task_pred_data.py`'s sector-recoding map contained a raw,
  offensive free-text survey response as a key — removed before publishing here.
