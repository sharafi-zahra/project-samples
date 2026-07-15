# -*- coding: utf-8 -*-
"""
Regenerates fig2_income_hetero.png and fig2_mental_hetero.png for the median
variant with two fixes already applied in the main script:
  - fbfa/fhfa/fwfa now have proper labels in RENAME
  - xlim set to (0, 0.03)

Loads the main script as a module (triggers data loading once), then runs
only the sex-stratified SHAP and hetero plot steps.
"""
import sys, os
sys.path.insert(0, r'C:\Users\sharafi')
os.chdir(r'C:\Users\sharafi')

# Import main script as a module — this executes all global-level code
# (data loading, function definitions) but does NOT call run_analysis
# because Section 12 calls are guarded by the exec below.
import importlib.util, types

src = open('full_analysis_within_country.py', encoding='utf-8').read()
# Strip the two run_analysis() calls so import doesn't kick off the full run
src = src.replace(
    "run_analysis(quantile_upper=0.5,  label='median')   # main text", "pass")
src = src.replace(
    "run_analysis(quantile_upper=0.25, label='q25')       # appendix", "pass")
src = src.replace('print("\\nAll done.")', "")

mod = types.ModuleType('main_analysis')
exec(compile(src, 'full_analysis_within_country.py', 'exec'), mod.__dict__)

# ── grab everything we need ──────────────────────────────────────────────────
SHAP_repeated_CV_inline   = mod.SHAP_repeated_CV_inline
shap_hetero_plot          = mod.shap_hetero_plot
prepare_ML_dataset_inline = mod.prepare_ML_dataset_inline
within_country_qcut       = mod.within_country_qcut
within_country_standardize= mod.within_country_standardize
Data_income_raw           = mod.Data_income_raw
Data_mental_raw           = mod.Data_mental_raw
Data_comb_base            = mod.Data_comb_base
sex_lookup                = mod.sex_lookup
RENAME                    = mod.RENAME
SHAP_SPLITS               = mod.SHAP_SPLITS
SHAP_REPEATS              = mod.SHAP_REPEATS

import numpy as np
import pandas as pd

OUTDIR         = os.path.join('results', 'median')
QUANTILE_UPPER = 0.5

print("Rebuilding datasets for median variant..."); sys.stdout.flush()

# ── reproduce data-prep from run_analysis ────────────────────────────────────
inc = Data_income_raw.copy()
exclude_ids = []
for cty in inc['country'].unique():
    mask = inc['country'] == cty
    med_c = np.median(inc.loc[mask, 'income_score'].dropna())
    exc_mask = mask & (inc['enrschr5'] == 1) & (inc['income_score'] < med_c)
    exclude_ids.extend(inc.loc[exc_mask, 'childid'].tolist())
inc = inc[~inc['childid'].isin(exclude_ids)].copy()
inc['income_score_bin2'] = within_country_qcut(inc, 'income_score', QUANTILE_UPPER)
Data_income_comb = inc[['childid','income_score','income_score_bin2','enrschr5','country']].copy()

mnt = Data_mental_raw.copy()
mnt['mental_health_score_bin2'] = within_country_qcut(mnt, 'mental_health_score', QUANTILE_UPPER)
Data_mental_comb = mnt[['childid','mental_health_score','mental_health_score_bin2','country']].copy()

base = Data_comb_base.copy()
scale_cols = [c for c in base.select_dtypes(include='number').columns if c != 'sex']
base = within_country_standardize(base, scale_cols, country_col='country')

target_vars_income = list(Data_income_comb.columns)
target_vars_mental = list(Data_mental_comb.columns)

base_ml = base.drop(columns=['country'], errors='ignore')
Data_ML_income = pd.merge(base_ml, Data_income_comb, on='childid')
Data_ML_mental = pd.merge(base_ml, Data_mental_comb, on='childid')

def sex_split(Data_ML, target_vars):
    merged = pd.merge(Data_ML, sex_lookup, on='childid', suffixes=('','_orig'))
    sex_col = 'sex_orig' if 'sex_orig' in merged.columns else 'sex'
    female = merged.loc[merged[sex_col] == 1].drop(['sex','sex_orig'], axis=1, errors='ignore').copy()
    male   = merged.loc[merged[sex_col] == 0].drop(['sex','sex_orig'], axis=1, errors='ignore').copy()
    tv = [v for v in target_vars if v != 'sex']
    return female, male, tv

female_inc, male_inc, tv_inc = sex_split(Data_ML_income, target_vars_income)
female_mnt, male_mnt, tv_mnt = sex_split(Data_ML_mental, target_vars_mental)

def get_XY(Data_sub, tv, target_var, random_state=42):
    _, _, _, _, X, y = prepare_ML_dataset_inline(
        Data_sub, tv, target_var, test_size=0.3, random_state=random_state)
    return X, y

# ── income hetero ─────────────────────────────────────────────────────────────
print("Income sex-stratified SHAP..."); sys.stdout.flush()
Xf_inc, yf_inc = get_XY(female_inc, tv_inc, 'income_score_bin2')
Xm_inc, ym_inc = get_XY(male_inc,   tv_inc, 'income_score_bin2')
avg_f_inc, _ = SHAP_repeated_CV_inline(
    female_inc, Xf_inc, yf_inc, SHAP_SPLITS, SHAP_REPEATS,
    outdir=OUTDIR, prefix='fig2_income_female', max_features=10)
avg_m_inc, _ = SHAP_repeated_CV_inline(
    male_inc, Xm_inc, ym_inc, SHAP_SPLITS, SHAP_REPEATS,
    outdir=OUTDIR, prefix='fig2_income_male', max_features=10)
shap_hetero_plot(avg_f_inc, avg_m_inc, Xf_inc, Xm_inc,
                 os.path.join(OUTDIR, 'fig2_income_hetero.png'), n_features=25)
print("  -> fig2_income_hetero.png saved"); sys.stdout.flush()

# ── mental hetero ─────────────────────────────────────────────────────────────
print("Mental sex-stratified SHAP..."); sys.stdout.flush()
Xf_mnt, yf_mnt = get_XY(female_mnt, tv_mnt, 'mental_health_score_bin2')
Xm_mnt, ym_mnt = get_XY(male_mnt,   tv_mnt, 'mental_health_score_bin2')
avg_f_mnt, _ = SHAP_repeated_CV_inline(
    female_mnt, Xf_mnt, yf_mnt, SHAP_SPLITS, SHAP_REPEATS,
    outdir=OUTDIR, prefix='fig2_mental_female', max_features=10)
avg_m_mnt, _ = SHAP_repeated_CV_inline(
    male_mnt, Xm_mnt, ym_mnt, SHAP_SPLITS, SHAP_REPEATS,
    outdir=OUTDIR, prefix='fig2_mental_male', max_features=10)
shap_hetero_plot(avg_f_mnt, avg_m_mnt, Xf_mnt, Xm_mnt,
                 os.path.join(OUTDIR, 'fig2_mental_hetero.png'), n_features=25)
print("  -> fig2_mental_hetero.png saved"); sys.stdout.flush()

print("\nDone. Both hetero plots regenerated with fixes.")
