# -*- coding: utf-8 -*-
"""
For each task (mental health, income), runs one SHAP pass and outputs:
  - feature rank
  - mean |SHAP| (importance)
  - mean SHAP (direction: positive = high feature value → above-median outcome)
  - correlation(feature_value, SHAP_value): sign tells us direction cleanly
"""
import sys, os, warnings, types
warnings.filterwarnings('ignore')
sys.path.insert(0, r'C:\Users\sharafi')
os.chdir(r'C:\Users\sharafi')

src = open('full_analysis_within_country.py', encoding='utf-8').read()
src = src.replace("run_analysis(quantile_upper=0.5,  label='median')   # main text", "pass")
src = src.replace("run_analysis(quantile_upper=0.25, label='q25')       # appendix", "pass")
src = src.replace('print("\\nAll done.")', "")
mod = types.ModuleType('m')
exec(compile(src, 'full_analysis_within_country.py', 'exec'), mod.__dict__)

import numpy as np, pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

RENAME = mod.RENAME

def run_shap_direction(Data_ML, target_vars, target_var, label, n_top=10):
    prepare  = mod.prepare_ML_dataset_inline
    tune     = mod.param_tuning_train_only
    build    = mod.build_final_model

    _, _, _, _, X, y = prepare(Data_ML, target_vars, target_var,
                                test_size=0.3, random_state=42)
    X_tr, y_tr = X, y
    best_p = tune("RandomForest", X_tr, y_tr, seed=42, cv=3)
    sm = SMOTE(sampling_strategy='auto', k_neighbors=5, random_state=42)
    Xs, ys = sm.fit_resample(X_tr, y_tr)
    Xs = pd.DataFrame(Xs, columns=X_tr.columns)
    clf = build("RandomForest", best_p, seed=42)
    clf.fit(Xs, ys)

    Xr = X.rename(columns=RENAME)
    exp = shap.TreeExplainer(clf)
    sv  = exp.shap_values(Xr, check_additivity=False)
    if isinstance(sv, list):
        sv = np.array(sv[1] if len(sv) > 1 else sv[0])
    else:
        sv = np.array(sv)
    if sv.ndim == 3:
        sv = sv[:, :, 1]

    sv_df  = pd.DataFrame(sv,  columns=Xr.columns)
    feat_df = pd.DataFrame(Xr.values, columns=Xr.columns)

    mean_abs  = sv_df.abs().mean()
    top_feats = mean_abs.nlargest(n_top).index.tolist()

    print(f"\n{'='*65}")
    print(f"  {label}  —  top {n_top} features")
    print(f"{'='*65}")
    print(f"{'Rank':<5} {'Feature':<38} {'mean|SHAP|':>10} {'corr(val,shap)':>14}  Direction")
    print(f"{'-'*65}")
    for rank, feat in enumerate(top_feats, 1):
        m_abs  = mean_abs[feat]
        corr   = float(feat_df[feat].squeeze().corr(sv_df[feat].squeeze()))
        if abs(corr) < 0.05:
            direction = "mixed / nonlinear"
        elif corr > 0:
            direction = "HIGH value => ABOVE median (better)"
        else:
            direction = "HIGH value => BELOW median (worse)"
        print(f"{rank:<5} {feat:<38} {m_abs:>10.4f} {corr:>14.3f}  {direction}")

# ── prepare median datasets ───────────────────────────────────────────────────
import numpy as np
within_country_qcut       = mod.within_country_qcut
within_country_standardize= mod.within_country_standardize
Data_income_raw           = mod.Data_income_raw
Data_mental_raw           = mod.Data_mental_raw
Data_comb_base            = mod.Data_comb_base

QUANTILE_UPPER = 0.5

inc = Data_income_raw.copy()
exclude_ids = []
for cty in inc['country'].unique():
    mask  = inc['country'] == cty
    med_c = np.median(inc.loc[mask, 'income_score'].dropna())
    exc   = mask & (inc['enrschr5'] == 1) & (inc['income_score'] < med_c)
    exclude_ids.extend(inc.loc[exc, 'childid'].tolist())
inc = inc[~inc['childid'].isin(exclude_ids)].copy()
inc['income_score_bin2'] = within_country_qcut(inc, 'income_score', QUANTILE_UPPER)
Data_income_comb = inc[['childid','income_score','income_score_bin2','enrschr5','country']].copy()

mnt = Data_mental_raw.copy()
mnt['mental_health_score_bin2'] = within_country_qcut(mnt, 'mental_health_score', QUANTILE_UPPER)
Data_mental_comb = mnt[['childid','mental_health_score','mental_health_score_bin2','country']].copy()

base = Data_comb_base.copy()
scale_cols = [c for c in base.select_dtypes(include='number').columns if c != 'sex']
base = within_country_standardize(base, scale_cols, country_col='country')
base_ml = base.drop(columns=['country'], errors='ignore')

Data_ML_income = pd.merge(base_ml, Data_income_comb, on='childid')
Data_ML_mental = pd.merge(base_ml, Data_mental_comb, on='childid')

tv_inc = list(Data_income_comb.columns)
tv_mnt = list(Data_mental_comb.columns)

run_shap_direction(Data_ML_mental, tv_mnt, 'mental_health_score_bin2',
                   'MENTAL HEALTH', n_top=10)
run_shap_direction(Data_ML_income,  tv_inc, 'income_score_bin2',
                   'INCOME',        n_top=10)
