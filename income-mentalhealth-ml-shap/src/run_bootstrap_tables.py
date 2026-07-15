# -*- coding: utf-8 -*-
"""
Standalone bootstrap for Tables 2 & 3.

Key optimisations vs the original ML_comparison_v3:
  1. Feature selection   — run ONCE per (task, subgroup), not per iteration
  2. Hyperparameter tune — run ONCE per (task, subgroup, model), not per iteration
  3. Checkpointing       — saves a CSV every 10 iterations; resumes automatically
  4. Both variants       — median (main text) and q25 (appendix) in one run

Expected runtime: ~1-2 h total (vs 15-20 h in the original).
"""
import sys, os, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, r'C:\Users\sharafi')
os.chdir(r'C:\Users\sharafi')

# ── load main script (skip run_analysis calls) ────────────────────────────────
import types
src = open('full_analysis_within_country.py', encoding='utf-8').read()
src = src.replace("run_analysis(quantile_upper=0.5,  label='median')   # main text", "pass")
src = src.replace("run_analysis(quantile_upper=0.25, label='q25')       # appendix", "pass")
src = src.replace('print("\\nAll done.")', "")
mod = types.ModuleType('m')
exec(compile(src, 'full_analysis_within_country.py', 'exec'), mod.__dict__)

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, f1_score, accuracy_score
from imblearn.over_sampling import SMOTE

# ── pull helpers from mod ─────────────────────────────────────────────────────
prepare       = mod.prepare_ML_dataset_inline
tune          = mod.param_tuning_train_only
build         = mod.build_final_model
feat_select   = mod.SHAP_feature_selection
latex_t2      = mod.latex_table2
latex_t3      = mod.latex_table3
wc_qcut       = mod.within_country_qcut
wc_std        = mod.within_country_standardize
Data_income_raw = mod.Data_income_raw
Data_mental_raw = mod.Data_mental_raw
Data_comb_base  = mod.Data_comb_base
sex_lookup      = mod.sex_lookup

I_RANGE = 50
MODELS  = ["Regression", "DecisionTree", "RandomForest", "XGBoost"]


# =============================================================================
# 1. Data preparation
# =============================================================================

def prepare_datasets(quantile_upper):
    # Income — exclude enrolled-below-median edge cases
    inc = Data_income_raw.copy()
    exclude_ids = []
    for cty in inc['country'].unique():
        mask  = inc['country'] == cty
        med_c = np.median(inc.loc[mask, 'income_score'].dropna())
        exc   = mask & (inc['enrschr5'] == 1) & (inc['income_score'] < med_c)
        exclude_ids.extend(inc.loc[exc, 'childid'].tolist())
    inc = inc[~inc['childid'].isin(exclude_ids)].copy()
    inc['income_score_bin2'] = wc_qcut(inc, 'income_score', quantile_upper)
    Data_income_comb = inc[['childid', 'income_score', 'income_score_bin2',
                             'enrschr5', 'country']].copy()

    # Mental health
    mnt = Data_mental_raw.copy()
    mnt['mental_health_score_bin2'] = wc_qcut(mnt, 'mental_health_score', quantile_upper)
    Data_mental_comb = mnt[['childid', 'mental_health_score',
                              'mental_health_score_bin2', 'country']].copy()

    # Base features — within-country standardised
    base = Data_comb_base.copy()
    scale_cols = [c for c in base.select_dtypes(include='number').columns if c != 'sex']
    base = wc_std(base, scale_cols, country_col='country')
    base_ml = base.drop(columns=['country'], errors='ignore')

    Data_ML_income = pd.merge(base_ml, Data_income_comb, on='childid')
    Data_ML_mental = pd.merge(base_ml, Data_mental_comb, on='childid')

    tv_inc = list(Data_income_comb.columns)
    tv_mnt = list(Data_mental_comb.columns)

    # Sex subgroups
    female_ids = set(sex_lookup.loc[sex_lookup['sex'] == 1, 'childid'])
    male_ids   = set(sex_lookup.loc[sex_lookup['sex'] == 0, 'childid'])

    female_inc = Data_ML_income[Data_ML_income['childid'].isin(female_ids)].copy()
    male_inc   = Data_ML_income[Data_ML_income['childid'].isin(male_ids)].copy()
    female_mnt = Data_ML_mental[Data_ML_mental['childid'].isin(female_ids)].copy()
    male_mnt   = Data_ML_mental[Data_ML_mental['childid'].isin(male_ids)].copy()

    return (Data_ML_income, Data_ML_mental, tv_inc, tv_mnt,
            female_inc, male_inc, female_mnt, male_mnt)


# =============================================================================
# 2. One-time pre-tuning
# =============================================================================

def pretune_all(Data, target_vars, target_var, seed=42):
    """
    Returns {model_name: (best_params, selected_features)}.
    Feature selection and GridSearchCV each run exactly once.
    """
    _, _, _, _, X, y = prepare(Data, target_vars, target_var,
                                test_size=0.1, random_state=seed)
    tuned = {}
    for model_name in MODELS:
        print(f"      {model_name} ...", end=' ', flush=True)
        fs_model = "LogReg" if model_name == "Regression" else model_name
        feats  = feat_select(X, y, stepsize=5, model=fs_model,
                             val_size=0.2, random_state=seed, use_smote=True)
        params = tune(model_name, X[feats], y, seed=seed, cv=3)
        tuned[model_name] = (params, feats)
        print(f"done  ({len(feats)} features selected)")
    return tuned


# =============================================================================
# 3. Bootstrap loop — fixed params + fixed features + checkpointing
# =============================================================================

def bootstrap_fixed(Data, target_vars, target_var, tuned,
                    i_range=50, test_size=0.1, seed=24,
                    bootstrap_threshold=0.95, checkpoint_path=None):
    results = {m: {'auc': [], 'f1': [], 'acc': []} for m in MODELS}

    # Resume from checkpoint if it exists
    start_i = 0
    if checkpoint_path and os.path.exists(checkpoint_path):
        ck = pd.read_csv(checkpoint_path)
        for m in MODELS:
            sub = ck[ck['model'] == m].sort_values('iter')
            results[m]['auc'] = sub['auc'].tolist()
            results[m]['f1']  = sub['f1'].tolist()
            results[m]['acc'] = sub['acc'].tolist()
        if results[MODELS[0]]['auc']:
            start_i = min(len(results[m]['auc']) for m in MODELS)
            print(f"      Resuming from iteration {start_i}/{i_range}")

    for i in range(start_i, i_range):
        if i % 10 == 0:
            print(f"      iteration {i}/{i_range}", flush=True)

        Data_boot = Data.sample(frac=bootstrap_threshold,
                                random_state=seed + i).sort_index()
        X_train, y_train, X_test, y_test, _, _ = prepare(
            Data_boot, target_vars, target_var,
            test_size=test_size, random_state=seed + i)

        for model_name in MODELS:
            params, feats = tuned[model_name]
            # Guard: keep only features present after this bootstrap sample
            feats_ok = [f for f in feats if f in X_train.columns and f in X_test.columns]

            clf = build(model_name, params, seed=seed + i)
            sm  = SMOTE(random_state=seed + i)
            Xs, ys = sm.fit_resample(X_train[feats_ok], y_train)
            clf.fit(Xs, ys)

            pp   = clf.predict_proba(X_test[feats_ok])[:, 1]
            pred = (pp >= 0.5).astype(int)
            results[model_name]['auc'].append(roc_auc_score(y_test, pp))
            results[model_name]['f1'].append(f1_score(y_test, pred, zero_division=0))
            results[model_name]['acc'].append(accuracy_score(y_test, pred))

        # Save checkpoint every 10 completed iterations
        if checkpoint_path and (i + 1) % 10 == 0:
            rows = []
            for m in MODELS:
                for j, (a, f, c) in enumerate(zip(results[m]['auc'],
                                                   results[m]['f1'],
                                                   results[m]['acc'])):
                    rows.append({'model': m, 'iter': j, 'auc': a, 'f1': f, 'acc': c})
            pd.DataFrame(rows).to_csv(checkpoint_path, index=False)
            print(f"      checkpoint saved ({i + 1} iterations)", flush=True)

    return results


# =============================================================================
# 4. Full variant runner
# =============================================================================

def run_variant(quantile_upper, label):
    print(f"\n{'='*65}")
    print(f"  VARIANT: {label}  (quantile_upper={quantile_upper})")
    print(f"{'='*65}")

    outdir = os.path.join('results', label)
    ckdir  = os.path.join(outdir, 'checkpoints')
    os.makedirs(ckdir, exist_ok=True)

    # ── data ──────────────────────────────────────────────────────────────────
    print("\nPreparing datasets...", flush=True)
    (Data_ML_income, Data_ML_mental, tv_inc, tv_mnt,
     female_inc, male_inc, female_mnt, male_mnt) = prepare_datasets(quantile_upper)
    print(f"  Income N={len(Data_ML_income)}  Mental N={len(Data_ML_mental)}")

    # ── pre-tune (6 tasks × 4 models = 24 GridSearchCV calls, done once) ─────
    tasks = [
        ("Income (full)",    Data_ML_income, tv_inc, 'income_score_bin2',    42),
        ("Mental (full)",    Data_ML_mental, tv_mnt, 'mental_health_score_bin2', 42),
        ("Income Female",    female_inc,     tv_inc, 'income_score_bin2',    44),
        ("Income Male",      male_inc,       tv_inc, 'income_score_bin2',    44),
        ("Mental Female",    female_mnt,     tv_mnt, 'mental_health_score_bin2', 44),
        ("Mental Male",      male_mnt,       tv_mnt, 'mental_health_score_bin2', 44),
    ]
    tuned = {}
    for i, (name, data, tv, tvar, seed) in enumerate(tasks, 1):
        print(f"\n[{i}/6] Pre-tuning: {name}", flush=True)
        tuned[name] = pretune_all(data, tv, tvar, seed=seed)

    # ── bootstrap loops ───────────────────────────────────────────────────────
    runs = [
        ("Income (full)",  Data_ML_income, tv_inc, 'income_score_bin2',        24, 'ck_income.csv'),
        ("Mental (full)",  Data_ML_mental, tv_mnt, 'mental_health_score_bin2', 24, 'ck_mental.csv'),
        ("Income Female",  female_inc,     tv_inc, 'income_score_bin2',        44, 'ck_f_inc.csv'),
        ("Income Male",    male_inc,       tv_inc, 'income_score_bin2',        44, 'ck_m_inc.csv'),
        ("Mental Female",  female_mnt,     tv_mnt, 'mental_health_score_bin2', 44, 'ck_f_mnt.csv'),
        ("Mental Male",    male_mnt,       tv_mnt, 'mental_health_score_bin2', 44, 'ck_m_mnt.csv'),
    ]
    boot = {}
    for name, data, tv, tvar, seed, ck_file in runs:
        print(f"\nBootstrap — {name}  ({I_RANGE} iterations)...", flush=True)
        boot[name] = bootstrap_fixed(
            data, tv, tvar, tuned[name],
            i_range=I_RANGE, seed=seed,
            checkpoint_path=os.path.join(ckdir, ck_file))

    # ── tables ────────────────────────────────────────────────────────────────
    t2 = latex_t2(boot["Income (full)"], boot["Mental (full)"])
    with open(os.path.join(outdir, 'table2.tex'), 'w') as f:
        f.write(t2)
    print("\nTable 2 saved.")

    t3 = latex_t3(boot["Income Female"], boot["Income Male"],
                  boot["Mental Female"], boot["Mental Male"])
    with open(os.path.join(outdir, 'table3.tex'), 'w') as f:
        f.write(t3)
    print("Table 3 saved.")

    # ── console summary ───────────────────────────────────────────────────────
    print(f"\n--- Summary: {label} ---")
    for task_label, key in [("Income",        "Income (full)"),
                             ("Mental Health", "Mental (full)")]:
        res = boot[key]
        for m in MODELS:
            print(f"  {task_label} | {m:15s} | "
                  f"AUC={np.mean(res[m]['auc']):.3f}  "
                  f"F1={np.mean(res[m]['f1']):.3f}  "
                  f"Acc={np.mean(res[m]['acc']):.3f}")

    print(f"\nVariant '{label}' complete. Results in: results/{label}/")


# =============================================================================
# 5. Run
# =============================================================================
run_variant(0.5,  'median')
run_variant(0.25, 'q25')

print("\nAll done.")
