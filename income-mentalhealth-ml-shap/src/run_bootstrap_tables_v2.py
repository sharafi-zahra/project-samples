# -*- coding: utf-8 -*-
"""
Bootstrap Tables v2 — improved tuning.

Changes vs v1:
  1. RandomizedSearchCV (n_iter=40) replaces GridSearchCV — wider parameter space
  2. GradientBoostingClassifier added as 5th model (LightGBM unavailable offline)
  3. Wider grids: larger n_estimators, subsample/colsample for XGBoost,
     L1/L2 options for LogReg, min_samples controls for tree models
"""
import sys, os, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, r'C:\Users\sharafi')
os.chdir(r'C:\Users\sharafi')

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
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE

# ── helpers from mod ──────────────────────────────────────────────────────────
prepare     = mod.prepare_ML_dataset_inline
feat_select = mod.SHAP_feature_selection
wc_qcut     = mod.within_country_qcut
wc_std      = mod.within_country_standardize
Data_income_raw = mod.Data_income_raw
Data_mental_raw = mod.Data_mental_raw
Data_comb_base  = mod.Data_comb_base
sex_lookup      = mod.sex_lookup

I_RANGE = 50
MODELS  = ["Regression", "DecisionTree", "RandomForest", "XGBoost"]
RAND_ITER = 40   # RandomizedSearchCV iterations per model


# =============================================================================
# 1. Improved build + tune (replaces mod versions)
# =============================================================================

def build_model(model_name, params, seed):
    if model_name == "Regression":
        solver = "saga" if params.get("penalty") == "l1" else "lbfgs"
        return LogisticRegression(
            max_iter=50000, random_state=seed,
            C=params["C"], penalty=params.get("penalty", "l2"), solver=solver)
    elif model_name == "DecisionTree":
        return DecisionTreeClassifier(
            random_state=seed,
            max_depth=params["max_depth"],
            min_samples_split=params.get("min_samples_split", 2),
            min_samples_leaf=params.get("min_samples_leaf", 1))
    elif model_name == "RandomForest":
        return RandomForestClassifier(
            random_state=seed,
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            criterion=params["criterion"],
            min_samples_split=params.get("min_samples_split", 2),
            min_samples_leaf=params.get("min_samples_leaf", 1))
    elif model_name == "XGBoost":
        return XGBClassifier(
            random_state=seed,
            learning_rate=params["learning_rate"],
            n_estimators=params["n_estimators"],
            max_depth=params["max_depth"],
            subsample=params.get("subsample", 1.0),
            colsample_bytree=params.get("colsample_bytree", 1.0),
            use_label_encoder=False, eval_metric='logloss')
    else:
        raise ValueError(f"Unknown model: {model_name}")


def param_grids():
    return {
        "Regression": {
            "C":       [0.001, 0.01, 0.1, 1, 10, 100],
            "penalty": ["l1", "l2"],
        },
        "DecisionTree": {
            "max_depth":        [None, 5, 10, 15, 20, 30],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf":  [1, 2, 4],
        },
        "RandomForest": {
            "n_estimators":     [100, 200, 300, 500],
            "max_depth":        [None, 5, 10, 15, 20, 30],
            "criterion":        ["gini", "log_loss", "entropy"],
            "min_samples_split": [2, 5, 10],
            "min_samples_leaf":  [1, 2, 4],
        },
        "XGBoost": {
            "learning_rate":    [0.001, 0.005, 0.01, 0.05, 0.1, 0.2],
            "n_estimators":     [100, 200, 300, 500],
            "max_depth":        [3, 5, 7, 10, 15],
            "subsample":        [0.6, 0.7, 0.8, 1.0],
            "colsample_bytree": [0.6, 0.7, 0.8, 1.0],
        },
    }


def tune_model(model_name, X_train, y_train, seed, n_iter=RAND_ITER):
    sm = SMOTE(random_state=seed)
    Xs, ys = sm.fit_resample(X_train, y_train)
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)

    if model_name == "Regression":
        base = LogisticRegression(max_iter=50000, random_state=seed, solver="saga")
    elif model_name == "DecisionTree":
        base = DecisionTreeClassifier(random_state=seed)
    elif model_name == "RandomForest":
        base = RandomForestClassifier(random_state=seed, n_jobs=-1)
    elif model_name == "XGBoost":
        base = XGBClassifier(use_label_encoder=False, eval_metric='logloss',
                             random_state=seed)
    grid = param_grids()[model_name]
    rs = RandomizedSearchCV(base, grid, n_iter=n_iter, scoring="roc_auc",
                            cv=inner_cv, n_jobs=-1, verbose=0,
                            random_state=seed, refit=True)
    rs.fit(Xs, ys)
    return rs.best_params_


# =============================================================================
# 2. Table formatting (updated for 5 models)
# =============================================================================

def latex_table2(results_income, results_mental):
    model_order = [("Regression", "Logistic Regression"),
                   ("DecisionTree", "Decision Tree"),
                   ("RandomForest", "Random Forest"),
                   ("XGBoost",      "XGBoost"),
                   ]
    rows = []
    for task_label, res in [("Mental Health", results_mental),
                             ("Income",        results_income)]:
        best_auc = max(np.mean(res[m]['auc']) for m in res)
        for i, (m, label) in enumerate(model_order):
            auc = np.mean(res[m]['auc'])
            f1  = np.mean(res[m]['f1'])
            acc = np.mean(res[m]['acc'])
            tl  = f"\\multirow{{4}}{{*}}{{{task_label}}}" if i == 0 else ""
            if auc == best_auc:
                row = (f"  {tl} & \\textbf{{{label}}} & "
                       f"\\textbf{{{auc:.3f}}} & \\textbf{{{f1:.3f}}} & "
                       f"\\textbf{{{acc:.3f}}} \\\\")
            else:
                row = f"  {tl} & {label} & {auc:.3f} & {f1:.3f} & {acc:.3f} \\\\"
            rows.append(row)
        rows.append("\\midrule")
    rows.pop()
    body = "\n".join(rows)
    return (
        "\\begin{table}[ht]\n"
        "\\caption{Performance Comparison of ML Models (within-country cutoffs)}\n"
        "\\label{table_ML_1}\n\\centering\n"
        "\\begin{tabular}{llccc}\n\\toprule\n"
        "\\multicolumn{5}{c}{\\textbf{Model Performance Metrics}} \\\\\n"
        "\\midrule\n"
        "\\textbf{Target Variable} & \\textbf{Model} & "
        "\\textbf{ROC-AUC} & \\textbf{F1-Score} & \\textbf{Accuracy} \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n\\end{tabular}\n"
        "\\parbox{0.9\\linewidth}{\\scriptsize\\textbf{Notes:} "
        "Means over 50 bootstrap iterations. "
        "Within-country median (main text) or 25th-percentile (appendix) cutoff. "
        "Hyperparameters tuned once via RandomizedSearchCV (40 iterations, 3-fold CV).}\n"
        "\\end{table}"
    )


def latex_table3(res_f_inc, res_m_inc, res_f_mnt, res_m_mnt):
    model_order = [("Regression",  "Logistic Regression"),
                   ("DecisionTree","Decision Tree"),
                   ("RandomForest","Random Forest"),
                   ("XGBoost",     "XGBoost"),
                   ]
    rows = []
    for task_label, res_f, res_m in [
            ("Mental Health", res_f_mnt, res_m_mnt),
            ("Income",        res_f_inc, res_m_inc)]:
        best_f = max(np.mean(res_f[m]['auc']) for m in res_f)
        best_m = max(np.mean(res_m[m]['auc']) for m in res_m)
        for sg, res, best in [("Female", res_f, best_f),
                               ("Male",   res_m, best_m)]:
            for i, (m, label) in enumerate(model_order):
                auc = np.mean(res[m]['auc'])
                f1  = np.mean(res[m]['f1'])
                acc = np.mean(res[m]['acc'])
                tl  = (f"\\multirow{{8}}{{*}}{{{task_label}}}"
                       if sg == "Female" and i == 0 else "")
                sl  = f"\\multirow{{4}}{{*}}{{{sg}}}" if i == 0 else ""
                if auc == best:
                    row = (f"  {tl} & {sl} & \\textbf{{{label}}} & "
                           f"\\textbf{{{auc:.3f}}} & \\textbf{{{f1:.3f}}} & "
                           f"\\textbf{{{acc:.3f}}} \\\\")
                else:
                    row = (f"  {tl} & {sl} & {label} & "
                           f"{auc:.3f} & {f1:.3f} & {acc:.3f} \\\\")
                rows.append(row)
        rows.append("\\midrule")
    rows.pop()
    body = "\n".join(rows)
    return (
        "\\begin{table}[ht]\n"
        "\\caption{Heterogeneity Analyses by Sex (within-country cutoffs)}\n"
        "\\label{table_ML_2}\n\\centering\n"
        "\\begin{tabular}{lllccc}\n\\toprule\n"
        "\\multicolumn{6}{c}{\\textbf{Model Performance by Subgroup}} \\\\\n"
        "\\midrule\n"
        "\\textbf{Target} & \\textbf{Subgroup} & \\textbf{Model} & "
        "\\textbf{ROC-AUC} & \\textbf{F1} & \\textbf{Accuracy} \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n\\end{tabular}\n\\end{table}"
    )


# =============================================================================
# 3. Data preparation (same as v1)
# =============================================================================

def prepare_datasets(quantile_upper):
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

    mnt = Data_mental_raw.copy()
    mnt['mental_health_score_bin2'] = wc_qcut(mnt, 'mental_health_score', quantile_upper)
    Data_mental_comb = mnt[['childid', 'mental_health_score',
                              'mental_health_score_bin2', 'country']].copy()

    base = Data_comb_base.copy()
    scale_cols = [c for c in base.select_dtypes(include='number').columns if c != 'sex']
    base = wc_std(base, scale_cols, country_col='country')
    base_ml = base.drop(columns=['country'], errors='ignore')

    Data_ML_income = pd.merge(base_ml, Data_income_comb, on='childid')
    Data_ML_mental = pd.merge(base_ml, Data_mental_comb, on='childid')
    tv_inc = list(Data_income_comb.columns)
    tv_mnt = list(Data_mental_comb.columns)

    female_ids = set(sex_lookup.loc[sex_lookup['sex'] == 1, 'childid'])
    male_ids   = set(sex_lookup.loc[sex_lookup['sex'] == 0, 'childid'])
    female_inc = Data_ML_income[Data_ML_income['childid'].isin(female_ids)].copy()
    male_inc   = Data_ML_income[Data_ML_income['childid'].isin(male_ids)].copy()
    female_mnt = Data_ML_mental[Data_ML_mental['childid'].isin(female_ids)].copy()
    male_mnt   = Data_ML_mental[Data_ML_mental['childid'].isin(male_ids)].copy()

    return (Data_ML_income, Data_ML_mental, tv_inc, tv_mnt,
            female_inc, male_inc, female_mnt, male_mnt)


# =============================================================================
# 4. Pre-tuning
# =============================================================================

def pretune_all(Data, target_vars, target_var, seed=42):
    _, _, _, _, X, y = prepare(Data, target_vars, target_var,
                                test_size=0.1, random_state=seed)
    tuned = {}
    for model_name in MODELS:
        print(f"      {model_name} ...", end=' ', flush=True)
        fs_model = "LogReg" if model_name == "Regression" else model_name
        feats  = feat_select(X, y, stepsize=5, model=fs_model,
                             val_size=0.2, random_state=seed, use_smote=True)
        params = tune_model(model_name, X[feats], y, seed=seed)
        tuned[model_name] = (params, feats)
        print(f"done  ({len(feats)} features)", flush=True)
    return tuned


# =============================================================================
# 5. Bootstrap loop
# =============================================================================

def bootstrap_fixed(Data, target_vars, target_var, tuned,
                    i_range=50, test_size=0.1, seed=24,
                    bootstrap_threshold=0.95, checkpoint_path=None):
    results = {m: {'auc': [], 'f1': [], 'acc': []} for m in MODELS}

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
            feats_ok = [f for f in feats if f in X_train.columns and f in X_test.columns]
            clf = build_model(model_name, params, seed=seed + i)
            sm  = SMOTE(random_state=seed + i)
            Xs, ys = sm.fit_resample(X_train[feats_ok], y_train)
            clf.fit(Xs, ys)
            pp   = clf.predict_proba(X_test[feats_ok])[:, 1]
            pred = (pp >= 0.5).astype(int)
            results[model_name]['auc'].append(roc_auc_score(y_test, pp))
            results[model_name]['f1'].append(f1_score(y_test, pred, zero_division=0))
            results[model_name]['acc'].append(accuracy_score(y_test, pred))

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
# 6. Variant runner
# =============================================================================

def run_variant(quantile_upper, label):
    print(f"\n{'='*65}")
    print(f"  VARIANT: {label}  (quantile_upper={quantile_upper})")
    print(f"{'='*65}")

    outdir = os.path.join('results', label + '_v2')
    ckdir  = os.path.join(outdir, 'checkpoints')
    os.makedirs(ckdir, exist_ok=True)

    print("\nPreparing datasets...", flush=True)
    (Data_ML_income, Data_ML_mental, tv_inc, tv_mnt,
     female_inc, male_inc, female_mnt, male_mnt) = prepare_datasets(quantile_upper)
    print(f"  Income N={len(Data_ML_income)}  Mental N={len(Data_ML_mental)}")

    tasks = [
        ("Income (full)",  Data_ML_income, tv_inc, 'income_score_bin2',        42),
        ("Mental (full)",  Data_ML_mental, tv_mnt, 'mental_health_score_bin2', 42),
        ("Income Female",  female_inc,     tv_inc, 'income_score_bin2',        44),
        ("Income Male",    male_inc,       tv_inc, 'income_score_bin2',        44),
        ("Mental Female",  female_mnt,     tv_mnt, 'mental_health_score_bin2', 44),
        ("Mental Male",    male_mnt,       tv_mnt, 'mental_health_score_bin2', 44),
    ]
    tuned = {}
    for i, (name, data, tv, tvar, seed) in enumerate(tasks, 1):
        print(f"\n[{i}/6] Pre-tuning: {name}", flush=True)
        tuned[name] = pretune_all(data, tv, tvar, seed=seed)

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

    t2 = latex_table2(boot["Income (full)"], boot["Mental (full)"])
    with open(os.path.join(outdir, 'table2.tex'), 'w') as f:
        f.write(t2)
    print("\nTable 2 saved.")

    t3 = latex_table3(boot["Income Female"], boot["Income Male"],
                      boot["Mental Female"], boot["Mental Male"])
    with open(os.path.join(outdir, 'table3.tex'), 'w') as f:
        f.write(t3)
    print("Table 3 saved.")

    print(f"\n--- Summary: {label} ---")
    for task_label, key in [("Income",        "Income (full)"),
                             ("Mental Health", "Mental (full)")]:
        res = boot[key]
        for m in MODELS:
            print(f"  {task_label} | {m:15s} | "
                  f"AUC={np.mean(res[m]['auc']):.3f}  "
                  f"F1={np.mean(res[m]['f1']):.3f}  "
                  f"Acc={np.mean(res[m]['acc']):.3f}")

    print(f"\nVariant '{label}' complete. Results in: results/{label}_v2/")


# =============================================================================
# 7. Run
# =============================================================================
run_variant(0.5,  'median')
run_variant(0.25, 'q25')

print("\nAll done.")
