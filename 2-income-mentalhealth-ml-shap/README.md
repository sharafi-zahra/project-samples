# Classifying and Understanding Adult Life Outcomes in Low- and Middle-Income Countries

Code behind a paper training ML classifiers on childhood survey data (Young Lives study;
Ethiopia, India, Peru, Vietnam) to predict whether an individual falls above or below the
within-country median on two adult outcomes measured 14 years later — **income** and
**mental health** — then using SHAP to surface which childhood factors drive those
predictions, including how predictive pathways diverge by sex.

## Data

- Young Lives study, older cohort: round 1 (age 8) features predicting round 5 (age 22)
  outcomes, n = 3,665 children (3,722 at round 1; 88.7% retained to round 5).
- **Income**: monthly salary (`erncshr5`), converted to USD via 2016 market exchange rates.
- **Mental health**: composite of 8 Likert items from the round-5 psychosocial battery
  (negatively-worded items reverse-coded), Cronbach's α = 0.684.
- Both targets are binarized via a **within-country** median split (each country's own
  median, not a pooled cross-country threshold), with a bottom-quartile (25th percentile)
  split as a robustness check.

## Approach

- **Two-stage feature selection**: 46 candidate features chosen via development-economics
  domain knowledge (health, education, nutrition, household resources, neighborhood,
  environment), then narrowed per model/task by SHAP-based backward elimination (removing
  the lowest-|SHAP| features in increasing batches, keeping whichever iteration maximizes
  held-out ROC-AUC on an inner 20% validation split).
- **Models compared**: **Logistic Regression, Decision Tree, Random Forest, and XGBoost** —
  hyperparameters tuned via 3-fold CV, SMOTE oversampling for class balance, feature
  selection and tuning re-run independently within each bootstrap iteration's training
  partition only (to prevent leakage).
- **Validation**: 50-iteration bootstrap (95% resampling); ROC-AUC, F1, and accuracy
  averaged across iterations.
- **Significance testing**: pairwise Wilcoxon signed-rank tests on per-iteration AUC,
  Bonferroni-corrected across 12 comparisons (6 model pairs × 2 tasks), α = 0.0042
  (`run_wilcoxon.py`).
- **Explainability**: SHAP values via repeated 5-fold CV (3 repeats), reporting global
  feature importance plus separate rankings for female/male subgroups to check for
  heterogeneous predictive pathways (`extract_shap_directions.py`, `regen_hetero.py`).
- **Diagnostics**: variance-inflation-factor checks for multicollinearity (`vif_analysis.py`),
  panel-attrition and scale-reliability checks, descriptive stats, sex-balance checks
  (`check_*.py`).

## Key results

- Income is classified more accurately than mental health (Random Forest ROC-AUC 0.671 vs.
  Logistic Regression ROC-AUC 0.610) — ensemble methods edge out linear models for income,
  while regularization outperforms complexity for the noisier mental-health signal.
- **Sex is by far the strongest predictor of both outcomes**: being female is associated
  with below-median predicted mental health and income alike.
- Beyond sex, maternal education is the most consistent cross-outcome predictor, pointing to
  an intergenerational human-capital channel.
- Predictive pathways diverge by sex: maternal education and physical development indicators
  dominate female income predictions, while early household economic shocks dominate for
  males; mental health is more driven by community/relational features for females and
  material household conditions for males.
- Sex-stratified models never beat the pooled model for either outcome — the larger pooled
  sample wins in both cases, despite the sex-specific SHAP differences above.
- The bottom-quartile robustness check (Appendix G) reproduces the same qualitative ranking
  of models and the same income-vs-mental-health performance gap.
- A Streamlit prototype decision-support dashboard (community/child-level risk views built on
  these classifications) is publicly deployed at
  [life-outcome-dashboard.streamlit.app](https://life-outcome-dashboard.streamlit.app) — its
  source isn't included in this repo.

## Files

| File | Purpose | Maps to paper |
|---|---|---|
| `full_analysis_within_country.py` | Main pipeline: data loading, feature engineering, model training, SHAP, VIF, LaTeX table + figure generation. Runtime ~4-8h per variant (median split + bottom-quartile). | Methods, Results, Appendix A–D, F |
| `run_bootstrap_tables.py` | Standalone, optimized bootstrap run for the 4-model comparison table (Table 2/3), with checkpointing so long runs resume automatically. | Table 2, Table 3 |
| `run_bootstrap_tables_v2.py`, `_v3.py`, `run_bootstrap_nosex.py` | Exploratory variants (5th model/Gradient Boosting, country-dummy features, sex-excluded features respectively) — **not** reflected in the published paper, which reports only the original 4-model, within-country design. Kept here for provenance. | — |
| `run_wilcoxon.py` | Generates the pairwise Wilcoxon significance tables from bootstrap checkpoint CSVs. | Appendix E (Tables A6, A7, A11) |
| `vif_analysis.py` | Standalone multicollinearity diagnostics on the model feature matrix. | Appendix F (Table A8) |
| `extract_shap_directions.py` | Reports each feature's importance and direction of effect (via SHAP correlation sign). | Results — SHAP direction discussion |
| `regen_hetero.py` | Regenerates the sex-stratified SHAP heterogeneity figures. | Figure 2 |
| `combine_fig1.py` | Combines the four SHAP panel figures into one pixel-aligned 2×2 figure. | Figure 1 |
| `check_attrition_alpha.py` | Panel attrition tracking (3,722 → 3,665 → 3,254) and Cronbach's α for the mental-health composite. | Data Pre-processing — Panel attrition, Mental health |
| `check_descriptives.py` | Descriptive statistics of household/child/community characteristics. | Table 1 |
| `check_sex.py` | Confirms the near-even male/female split underlying the sex-stratified analysis. | Results — heterogeneity analyses intro |
| `ML_analyses_experiment.py` | Earlier draft of the analysis (by a collaborator, "janmo"), predating the referee-comment fix. Uses pooled (not within-country) thresholds/standardization, external `Data_import_experiment`/`Functions.py` modules not included here, and a leave-one-country-out bootstrap evaluation that was later dropped. `full_analysis_within_country.py` is the fully self-contained, updated version that superseded it. | Superseded — see note below |

## Notes

- Scripts were run from a fixed local path (`C:\Users\sharafi`) and expect a dataset directory
  (`20241002_datasets/`) that is **not included** in this repo — no participant data is
  published here, only the analysis code.
- The `run_bootstrap_*` / `check_*` / SHAP scripts work by loading `full_analysis_within_country.py`
  as a module and monkey-patching out its top-level `run_analysis(...)` calls, so each script can
  reuse the data-loading and modeling code without re-running the whole pipeline.
- `ML_analyses_experiment.py` is included for provenance/comparison only; it does not run
  against the current data pipeline (missing external module dependencies) and its results are
  superseded by `full_analysis_within_country.py`.
