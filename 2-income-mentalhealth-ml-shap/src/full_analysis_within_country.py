# -*- coding: utf-8 -*-
"""
full_analysis_within_country.py

Complete reanalysis with within-country cutoffs and within-country feature
standardization, addressing the referee comment:
  "Are income and mental health thresholds computed within-country or pooled?"

TWO VARIANTS (each saved to its own folder):
  results/median/   main text  – within-country median (50 / 50 split)
  results/q25/      appendix   – within-country 25th pct (25 / 75 split)

Each folder contains:
  table2.tex               LaTeX ML model comparison
  table3.tex               LaTeX sex-stratified comparison
  fig1_mental_summary.png  SHAP beeswarm – mental health
  fig1_mental_bar.png      Mean SHAP bar  – mental health
  fig1_income_summary.png  SHAP beeswarm – income
  fig1_income_bar.png      Mean SHAP bar  – income
  fig2_mental_hetero.png   Sex-stratified SHAP – mental health
  fig2_income_hetero.png   Sex-stratified SHAP – income
  vif_income.csv / vif_mental.csv

Runtime: roughly 4-8 h per variant (50 bootstrap iterations × 4 models with
         inner SHAP feature selection and hyperparameter tuning).
         Set I_RANGE to a smaller value for a quick test run.
"""

import os, sys, warnings, pickle
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from functools import reduce
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import (train_test_split, KFold,
                                     StratifiedKFold, GridSearchCV)
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, f1_score, roc_auc_score,
                              recall_score, precision_score,
                              average_precision_score)
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import shap
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ─── runtime knob ────────────────────────────────────────────────────────────
I_RANGE = 50          # bootstrap iterations for Tables 2 & 3  (set to 3 for quick test)
SHAP_SPLITS   = 5     # KFold splits for SHAP repeated CV (Figure 1)
SHAP_REPEATS  = 3     # CV repetitions for SHAP repeated CV
ROOT = './20241002_datasets/'
# ─────────────────────────────────────────────────────────────────────────────

# =============================================================================
# SECTION 1 – Rename dictionary (inlined from Functions.py)
# =============================================================================
RENAME = {
    "fatal_inj_or_illn":                      "Fatal injury or illness",
    "reported_health_level":                   "Self-reported health level",
    "literacy":                                "Literacy",
    "shock_food_decrease":                     "Shock-decrease in food availability",
    "hhsize":                                  "Number of household members",
    "childs_alive":                            "Proportion of children alive",
    "theft_of_property":                       "Property theft incident",
    "victim_of_crime":                         "Crime victim",
    "changes_econ_cond_endo":                  "Negative economic shock",
    "natural_desaster":                        "Natural disaster",
    "health_death_shock":                      "Death of family member",
    "negative_incidents":                      "Divorce or separation within family",
    "migration_shock":                         "Resettlement or forced migration",
    "own_house_or_land":                       "Property ownership",
    "momage":                                  "Age of child's mother",
    "momedu":                                  "Education of child's mother",
    "dadage":                                  "Age of child's father",
    "dadedu":                                  "Education of child's father",
    "daddead":                                 "Father deceased",
    "join":                                    "Joined with community members",
    "authorit":                                "Communication with local authority",
    "hq":                                      "House quality",
    "sv":                                      "Access to services index",
    "cd":                                      "Consumer durable index",
    "zbfa":                                    "BMI for age",
    "zhfa":                                    "Height for age",
    "fbfa":                                    "BMI for age",
    "fhfa":                                    "Height for age",
    "fwfa":                                    "Weight for age",
    "living_standard":                         "Household living standard",
    "pop":                                     "Community population",
    "twndis":                                  "Distance to nearest town",
    "waste":                                   "Industrial waste problem",
    "airpol":                                  "Air pollution problem",
    "watpol":                                  "Water pollution problem",
    "contsoil":                                "Soil erosion problem",
    "legal":                                   "Legal support availability",
    "conclive":                                "Councillor lives in community",
    "safety":                                  "Community crime level",
    "comm_groups":                             "Number of community groups",
    "garbage_taken_by_truck":                  "Garbage collection by truck",
    "paved_roads_in_community":                "Paved roads in community",
    "drinking_water_from_public_or_private_well": "Drinking water source",
    "oremit":                                  "Sent money outside last year",
    "debt":                                    "Anyone in household having debts",
    "sex":                                     "Sex",
    "seemom":                                  "Frequency of seeing mother",
    "seedad":                                  "Frequency of seeing father",
    "schtyp":                                  "Type of school (private or public)",
    "namewrk":                                 "Child done activity for money or goods",
    "chores":                                  "Child does housekeeping daily",
}

# save as pickle so SHAP_repeated_CV can load it if needed
os.makedirs('results', exist_ok=True)
pickle.dump(RENAME, open('rename_dict_v3.sav', 'wb'))

# =============================================================================
# SECTION 2 – Value-replacement dictionaries
# =============================================================================
schtyp_dict   = {"public":1,"private":0,"n/a - not currently in school":np.nan,"nk":np.nan}
seedad_dict   = {"daily":5,"weekly":4,"monthly":3,"less than monthly":2,
                 "not in the last 6 months":1,"n/a father dead":0}
seemom_dict   = {"daily":5,"weekly":4,"monthly":3,"less than monthly":2,
                 "not in the last 6 months":1,"n/a - mother dead":0}
daddead_dict  = {"in the household":0,"not in the household":1,"father dead":2}
enrschr5_dict = {"no":0,"yes, attending regularly":1,"no, but attending part-time":0,
                 "yes, but attending irregularly":1,"n/a":np.nan,88:np.nan,3:np.nan}
yesno_dict    = {"yes":1,"Yes":1,"no":0,"No":0,"yes exists":1,
                 "n/a under 5yrs":np.nan,"refused to answer":np.nan,
                 77:np.nan,"nk":np.nan,"NK":np.nan}
sex_dict      = {"male":0,"female":1}
education_dict= {"none":0,"grade 1":1,"grade 2":2,"grade 3":3,"grade 4":4,
                 "grade 5":5,"grade 6":6,"grade 7":7,"grade 8":8,"grade 9":9,
                 "grade 10":10,"grade 11":11,"grade 12":12,"adult literacy":7,
                 "technical, pedagogical, cetpro (incomplete)":7,
                 "post-secondary, vocational":7,"university":13,
                 "university (incomplete)":13,"university (complete)":13,
                 "vocational, technical college":13,
                 "technical, pedagogical, cetpro (complete)":13,
                 "other":np.nan,"religious education":np.nan}
levlread_dict = {"can't read anything":0,"reads letters":1,"reads word":2,
                 "reads sentence":3,79:np.nan,"Refused to answer":np.nan,
                 "refused to answer":np.nan}
levlwrit_dict = {"no":0,"yes with difficulty or errors":1,
                 "yes without difficulty or errors":2,79:np.nan,
                 "Refused to answer":np.nan,"refused to answer":np.nan}
same_better_worse_dict = {"Worse":0,"worse":0,"Same":1,"same":1,
                          "Better":2,"better":2,99:np.nan}
very_poor_to_very_good_dict = {"very poor":0,"poor":1,"average":2,"good":3,
                               "very good":4,"Very poor":0,"Poor":1,
                               "Average":2,"Good":3,"Very good":4}
agree_dict    = {"Strongly disagree":1,"Disagree":2,"More or less":3,
                 "Agree":4,"Strongly agree":5,"Refused to answer":np.nan,
                 "NK":np.nan,"strongly disagree":1,"disagree":2,
                 "more or less":3,"agree":4,"strongly agree":5,
                 "refused to answer":np.nan,"nk":np.nan,
                 88:np.nan,77:np.nan,79:np.nan}
invert_5_classes_dict = {1:5,2:4,4:2,5:1}
notatall_to_serious_problem_dict = {"not at all":0,"doesn't affect the community":0,
                                    "Not at all":0,"only a little":1,"slightly":1,
                                    "Slightly":1,"severely":2,"Severely":2,
                                    "serious problem":2,"missing":np.nan}
dontknow_notmentioned_dict = {"not mentioned":np.nan,"don`t know":np.nan,
                              "don't know":np.nan,
                              "not applicable, community is part of the capital":np.nan,
                              "dk":np.nan,"na":np.nan}
high_medium_low_dict = {"high":2,"medium":1,"low":0,"missing":np.nan}
payment_periods = {1:"Per hour",2:"Per day",3:"Per week",4:"Per month",
                   5:"Per year",6:"Per piece",7:"Other, specify",
                   79:"Refused to answer",88:"NA",1.0:"Per hour",2.0:"Per day",
                   3.0:"Per week",4.0:"Per month",5.0:"Per year",
                   6.0:"Per piece",7.0:"Other, specify"}
conversion_factors = {"Per hour":160,"Per day":20,"Per week":4.33,"Per month":1,
                      "Per year":1/12,"Per piece":np.nan,"NA":np.nan,
                      "Other, specify":1,"N/A":1,np.nan:np.nan}
exchange = {'ET':0.0458,'PE':0.2965,'IN':0.0149,'VN':0.04}

# =============================================================================
# SECTION 3 – Data helpers
# =============================================================================
def col_values_to_lower(Data):
    for col in Data.columns:
        if col not in ('childid','childcode','CHILDID','CHILDCODE'):
            try:
                if Data[col].dtype == object:
                    Data[col] = Data[col].str.lower()
            except Exception:
                pass
    return Data


def combine_disparate_data(Data_ET, Data_IN, Data_PE, Data_VN):
    datasets = [Data_ET, Data_IN, Data_PE, Data_VN]
    for ds in datasets:
        ds.columns = [c.lower() for c in ds.columns]
    col_lists = [list(ds.columns) for ds in datasets]
    inter = set.intersection(*[set(c) for c in col_lists])
    ordered = [c for c in col_lists[0] if c in inter]
    reduced = [ds[[c for c in ds.columns if c in inter]].copy() for ds in datasets]
    return pd.concat([ds[ordered] for ds in reduced], ignore_index=True)


def import_and_merge_constr_dataset(Constr_ET=None, Constr_IN=None,
                                    Constr_PE=None, Constr_VN=None):
    rename_map = {'wi_new':'wi','hq_new':'hq','sv_new':'sv','cd_new':'cd',
                  'elecq_new':'elecq','toiletq_new':'toiletq',
                  'drwaterq_new':'drwaterq'}
    for ds in [Constr_ET, Constr_VN]:
        if ds is not None:
            ds.rename(columns={k:v for k,v in rename_map.items()
                                if k in ds.columns}, inplace=True)
    parts = [ds for ds in [Constr_ET, Constr_IN, Constr_PE, Constr_VN]
             if ds is not None]
    inter = set.intersection(*[set(ds.columns) for ds in parts])
    reduced = [ds[[c for c in ds.columns if c in inter]].copy() for ds in parts]
    return pd.concat(reduced, ignore_index=True)


# =============================================================================
# SECTION 4 – ML helper functions (inlined from Functions.py and ML_analyses_experiment.py)
# =============================================================================

def build_final_model(model_name, params, seed):
    if model_name == "Regression":
        return LogisticRegression(max_iter=50000, C=params["C"], random_state=seed)
    elif model_name == "DecisionTree":
        return DecisionTreeClassifier(max_depth=params["max_depth"], random_state=seed)
    elif model_name == "RandomForest":
        return RandomForestClassifier(n_estimators=params["n_estimators"],
                                      max_depth=params["max_depth"],
                                      criterion=params["criterion"],
                                      random_state=seed)
    elif model_name == "XGBoost":
        return XGBClassifier(learning_rate=params["learning_rate"],
                             max_depth=params["max_depth"],
                             n_estimators=params["n_estimators"],
                             random_state=seed,
                             use_label_encoder=False,
                             eval_metric='logloss')
    else:
        raise ValueError(f"Unknown model: {model_name}")


def param_tuning_train_only(ML_model, X_train, y_train, seed, cv=3):
    smote = SMOTE(random_state=seed)
    X_s, y_s = smote.fit_resample(X_train, y_train)
    inner_cv = StratifiedKFold(n_splits=cv, shuffle=True, random_state=seed)

    if ML_model == "XGBoost":
        param_grid = [{'learning_rate':[0.005,0.01,0.05,0.1],
                       'n_estimators':[50,100,200],
                       'max_depth':[None,5,10,20],
                       'random_state':[seed]}]
        model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    elif ML_model == "Regression":
        param_grid = [{'C':[0.01,0.1,1]}]
        model = LogisticRegression(max_iter=50000, random_state=seed)
    elif ML_model == "DecisionTree":
        param_grid = [{'max_depth':[None,5,10,20]}]
        model = DecisionTreeClassifier(random_state=seed)
    elif ML_model == "RandomForest":
        param_grid = [{'n_estimators':[50,100,200],
                       'max_depth':[None,5,10,20],
                       'criterion':["gini","log_loss","entropy"]}]
        model = RandomForestClassifier(random_state=seed)
    else:
        raise ValueError(f"Unknown model: {ML_model}")

    gs = GridSearchCV(model, param_grid, scoring="roc_auc",
                      cv=inner_cv, n_jobs=-1, verbose=0)
    gs.fit(X_s, y_s)
    return gs.best_params_


def SHAP_feature_selection(X_train, y_train, stepsize=5, model="RandomForest",
                            val_size=0.2, random_state=12345, use_smote=True):
    X_train = X_train.copy()
    y_train = pd.Series(y_train).copy()
    X_itr, X_val, y_itr, y_val = train_test_split(
        X_train, y_train, test_size=val_size,
        random_state=random_state, stratify=y_train)
    X_cur = X_itr.copy(); X_vv = X_val.copy()
    best_auc = -np.inf; best_features = X_cur.columns.tolist()
    subtractor = stepsize

    for _ in range(1, 80):
        if use_smote:
            sm = SMOTE(random_state=random_state)
            Xf, yf = sm.fit_resample(X_cur, y_itr)
            Xf = pd.DataFrame(Xf, columns=X_cur.columns)
            yf = pd.Series(yf)
        else:
            Xf, yf = X_cur.copy(), y_itr.copy()

        if model == "XGBoost":
            clf = XGBClassifier(use_label_encoder=False,
                                eval_metric='logloss',
                                random_state=random_state)
        elif model == "DecisionTree":
            clf = DecisionTreeClassifier(random_state=random_state)
        elif model == "RandomForest":
            clf = RandomForestClassifier(random_state=random_state)
        else:  # LogReg
            clf = LogisticRegression(max_iter=1000, random_state=random_state)
        clf.fit(Xf, yf)

        if hasattr(clf, "predict_proba"):
            ys = clf.predict_proba(X_vv)[:, 1]
        else:
            ys = clf.decision_function(X_vv)
        auc = roc_auc_score(y_val, ys)
        if auc > best_auc:
            best_auc = auc; best_features = X_cur.columns.tolist()

        if subtractor >= X_cur.shape[1]:
            break

        if model in ["XGBoost","DecisionTree","RandomForest"]:
            # No background data — fast path-dependent TreeSHAP; background
            # would add a full background-expectation pass over every sample
            # and make each inner FS step ~100× slower.
            exp = shap.TreeExplainer(clf)
            sv = exp.shap_values(Xf, check_additivity=False)
            if isinstance(sv, list):
                sv = sv[1] if len(sv) > 1 else sv[0]
        else:
            exp = shap.LinearExplainer(clf, Xf)
            sv = exp.shap_values(Xf)
        sv = np.array(sv)
        if sv.ndim > 2:
            sv = sv[..., 0]
        mean_abs = np.abs(sv).mean(axis=0)
        order = np.argsort(mean_abs)[::-1]
        keep = X_cur.columns[order[:-subtractor]].tolist()
        X_cur = X_cur[keep]; X_vv = X_vv[keep]
        subtractor += stepsize

    return best_features


def prepare_ML_dataset_inline(Input_data, target_vars_list, target_var,
                               test_size=0.1, random_state=42):
    """Simplified version of prepare_ML_dataset (rename_vars=None, smote=False)."""
    ALWAYS_EXCLUDE = {'commid', 'country'}
    exclude = set(target_vars_list) | ALWAYS_EXCLUDE
    data = Input_data.loc[~Input_data[target_var].isna()].copy()
    y = data[target_var].astype(int)
    X = data.loc[:, ~data.columns.isin(exclude)].copy()
    X = X.select_dtypes(include='number')      # drop any residual string columns
    X.dropna(axis=1, how='all', inplace=True)  # drop all-NaN columns (median=NaN)
    X.fillna(X.median(numeric_only=True), inplace=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state)
    return X_train, y_train, X_test, y_test, X, y


def ML_comparison_v3(Data, models, target_vars_list, target_var,
                     test_size=0.1, i_range=50,
                     bootstrap_threshold=0.95, seed=24):
    """Bootstrap ML comparison (Tables 2 & 3)."""
    results = {m: {'auc':[], 'f1':[], 'acc':[]} for m in models}

    for i in range(i_range):
        if i % 10 == 0:
            print(f"  iteration {i}/{i_range}"); sys.stdout.flush()
        Data_boot = Data.sample(frac=bootstrap_threshold,
                                random_state=seed+i).sort_index()
        X_train, y_train, X_test, y_test, _, _ = prepare_ML_dataset_inline(
            Data_boot, target_vars_list, target_var,
            test_size=test_size, random_state=seed+i)

        for model_name in models:
            fs_model = "LogReg" if model_name == "Regression" else model_name
            feats = SHAP_feature_selection(X_train, y_train, stepsize=5,
                                           model=fs_model, val_size=0.2,
                                           random_state=seed+i, use_smote=True)
            params = param_tuning_train_only(model_name, X_train[feats],
                                             y_train, seed=seed+i, cv=3)
            clf = build_final_model(model_name, params, seed=seed+i)
            sm = SMOTE(random_state=seed+i)
            Xs, ys = sm.fit_resample(X_train[feats], y_train)
            clf.fit(Xs, ys)
            pp = clf.predict_proba(X_test[feats])[:, 1]
            pred = (pp >= 0.5).astype(int)
            results[model_name]['auc'].append(roc_auc_score(y_test, pp))
            results[model_name]['f1'].append(f1_score(y_test, pred, zero_division=0))
            results[model_name]['acc'].append(accuracy_score(y_test, pred))

    return results


def SHAP_repeated_CV_inline(Data, X, y, n_splits, CV_repeats, outdir,
                             prefix, max_features=10, seed=1000):
    """Adapted SHAP_repeated_CV – uses inline RENAME dict, saves figs."""
    Data = Data.loc[~Data[y.name].isna()].copy().reset_index(drop=True)
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)

    np.random.seed(seed)
    random_states = np.random.randint(10000, size=CV_repeats)

    shap_per_cv = {s: {r: None for r in range(CV_repeats)} for s in X.index}

    for rep_idx in range(CV_repeats):
        print(f"    SHAP CV repeat {rep_idx+1}/{CV_repeats}")
        kf = KFold(n_splits=n_splits, shuffle=True,
                   random_state=random_states[rep_idx])
        for fold_idx, (tr_ix, te_ix) in enumerate(kf.split(Data)):
            Xtr = X.iloc[tr_ix].copy(); Xte = X.iloc[te_ix].copy()
            ytr = y.iloc[tr_ix].copy(); yte = y.iloc[te_ix].copy()

            best_p = param_tuning_train_only(
                "RandomForest", Xtr, ytr, seed=seed+rep_idx+fold_idx, cv=3)
            sm = SMOTE(sampling_strategy='auto', k_neighbors=5,
                       random_state=seed+rep_idx+fold_idx)
            Xs, ys = sm.fit_resample(Xtr, ytr)
            Xs = pd.DataFrame(Xs, columns=Xtr.columns)

            clf = build_final_model("RandomForest", best_p,
                                    seed=seed+rep_idx+fold_idx)
            clf.fit(Xs, ys)

            Xte_r = Xte.rename(columns=RENAME)
            Xs_r  = Xs.rename(columns=RENAME)

            # Use TreeExplainer without background data (path-dependent TreeSHAP)
            # — avoids an expensive O(n_background × n_test) conditional-expectation
            # pass that made each fold take ~90 seconds instead of ~1-2 seconds.
            exp = shap.TreeExplainer(clf)
            sv_raw = exp.shap_values(Xte_r, check_additivity=False)
            if isinstance(sv_raw, list):
                sv = np.array(sv_raw[1] if len(sv_raw) > 1 else sv_raw[0])
            else:
                sv = np.array(sv_raw)
            if sv.ndim == 3:
                sv = sv[:, :, 1]

            for li, gi in enumerate(te_ix):
                shap_per_cv[gi][rep_idx] = sv[li]

    avg_sv = []
    for obs in range(len(Data)):
        df_obs = pd.DataFrame.from_dict(shap_per_cv[obs])
        avg_sv.append(df_obs.median(axis=1).values)

    shap_matrix = np.vstack(avg_sv)
    X_plot = X.rename(columns=RENAME)

    # summary (beeswarm)
    fig1, _ = plt.subplots(figsize=(10, 7))
    shap.summary_plot(shap_matrix, X_plot, show=False, max_display=max_features)
    plt.grid(True, axis='both', color='gray', linestyle='--',
             linewidth=0.5, alpha=0.7)
    plt.tight_layout()
    fig1.savefig(os.path.join(outdir, f'{prefix}_summary.png'), dpi=300,
                 bbox_inches='tight')
    plt.close(fig1)

    # bar plot
    fig2, _ = plt.subplots(figsize=(4, 7))
    shap.summary_plot(shap_matrix, X_plot, plot_type="bar", show=False,
                      max_display=max_features)
    plt.grid(True, axis='both', color='gray', linestyle='--',
             linewidth=0.5, alpha=0.7)
    plt.xlabel("mean SHAP values")
    plt.tight_layout()
    fig2.savefig(os.path.join(outdir, f'{prefix}_bar.png'), dpi=300,
                 bbox_inches='tight')
    plt.close(fig2)

    summary_df = pd.DataFrame({
        'Feature': X_plot.columns,
        'MeanAbsSHAP': np.abs(shap_matrix).mean(axis=0)
    }).sort_values('MeanAbsSHAP', ascending=False).reset_index(drop=True)

    return avg_sv, summary_df


def shap_hetero_plot(avg_shap_female, avg_shap_male, X_female, X_male,
                     outpath, n_features=25):
    """Horizontal grouped bar chart of male vs female mean |SHAP|."""
    X_f = X_female.rename(columns=RENAME)
    X_m = X_male.rename(columns=RENAME)
    feat_names = X_f.columns.tolist()

    mean_f = np.mean(np.abs(np.vstack(avg_shap_female)), axis=0)
    mean_m = np.mean(np.abs(np.vstack(avg_shap_male)),   axis=0)

    # order by female SHAP descending, take top n_features
    order = np.argsort(mean_f)[::-1][:n_features]
    feats_sorted  = [feat_names[i] for i in reversed(order)]
    vals_f_sorted = [mean_f[i]     for i in reversed(order)]
    vals_m_sorted = [mean_m[i]     for i in reversed(order)]

    fig, ax = plt.subplots(figsize=(8, max(6, n_features * 0.35)))
    bh = 0.35
    pos1 = np.arange(len(feats_sorted))
    pos2 = pos1 + bh
    ax.barh(pos1, vals_f_sorted, height=bh, color="indianred",  label="Females")
    ax.barh(pos2, vals_m_sorted, height=bh, color="steelblue",  label="Males")
    ax.set_yticks(pos1 + bh/2)
    ax.set_yticklabels(feats_sorted, fontsize=9)
    ax.grid(visible=True, axis='both', linestyle='-.', color='gray', alpha=0.7)
    ax.set_xlabel('SHAP Value')
    ax.set_xlim(0, 0.03)
    ax.legend()
    plt.tight_layout()
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)


def compute_vif(X, task_name, continuous_threshold=5):
    X_num = X.select_dtypes(include=[np.number])
    cont_cols = [c for c in X_num.columns if X_num[c].nunique() > continuous_threshold]
    Xc = X_num[cont_cols].fillna(X_num[cont_cols].median())
    Xc = Xc.loc[:, Xc.std() > 0].dropna(axis=1)
    print(f"  VIF: {task_name} – {Xc.shape[1]} continuous features, "
          f"{len(Xc)} observations")
    vals = []
    for i in range(Xc.shape[1]):
        try:
            vals.append(variance_inflation_factor(Xc.values.astype(float), i))
        except Exception:
            vals.append(np.nan)
    df = pd.DataFrame({'Feature': Xc.columns, 'VIF': vals})
    df['Feature'] = df['Feature'].map(lambda x: RENAME.get(x, x))
    return df.sort_values('VIF', ascending=False).reset_index(drop=True)


def latex_table2(results_income, results_mental):
    """Return LaTeX for Table 2."""
    model_order = [("Regression",       "Logistic Regression"),
                   ("DecisionTree",      "Decision Tree"),
                   ("RandomForest",      "Random Forest"),
                   ("XGBoost",           "XGBoost")]
    rows = []
    for task_label, res in [("Mental Health", results_mental),
                             ("Income",        results_income)]:
        best_auc = max(np.mean(res[m]['auc']) for m in res)
        for i, (m, label) in enumerate(model_order):
            auc = np.mean(res[m]['auc'])
            f1  = np.mean(res[m]['f1'])
            acc = np.mean(res[m]['acc'])
            bold = auc == best_auc
            tl = f"\\multirow{{4}}{{*}}{{{task_label}}}" if i == 0 else ""
            if bold:
                row = (f"  {tl} & \\textbf{{{label}}} & "
                       f"\\textbf{{{auc:.3f}}} & "
                       f"\\textbf{{{f1:.3f}}} & "
                       f"\\textbf{{{acc:.3f}}} \\\\")
            else:
                row = f"  {tl} & {label} & {auc:.3f} & {f1:.3f} & {acc:.3f} \\\\"
            rows.append(row)
        rows.append("\\midrule")
    rows.pop()  # remove last \midrule
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
        "Within-country median (main text) or 25th-percentile (appendix) cutoff.}\n"
        "\\end{table}"
    )


def latex_table3(results_female_income, results_male_income,
                 results_female_mental, results_male_mental):
    """Return LaTeX for Table 3 (heterogeneity by sex)."""
    model_order = [("Regression",  "Logistic Regression"),
                   ("DecisionTree","Decision Tree"),
                   ("RandomForest","Random Forest"),
                   ("XGBoost",     "XGBoost")]
    rows = []
    for task_label, res_f, res_m in [
            ("Mental Health", results_female_mental, results_male_mental),
            ("Income",        results_female_income, results_male_income)]:
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
                bold = (auc == best)
                if bold:
                    row = (f"  {tl} & {sl} & \\textbf{{{label}}} & "
                           f"\\textbf{{{auc:.3f}}} & "
                           f"\\textbf{{{f1:.3f}}} & "
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
# SECTION 5 – Within-country utilities
# =============================================================================

def within_country_qcut(df, score_col, quantile_upper):
    """
    Classify observations as 0 (below quantile_upper within country)
    or 1 (above), using per-country thresholds.

    quantile_upper: 0.5 for median split, 0.25 for bottom-25% split
    The cutpoints list is [0, quantile_upper, 1.0].
    """
    result = pd.Series(np.nan, index=df.index, dtype=float)
    for country in df['country'].unique():
        mask = df['country'] == country
        vals = df.loc[mask, score_col]
        try:
            result[mask] = pd.qcut(
                vals, [0, quantile_upper, 1.0],
                labels=[0, 1], duplicates='drop'
            ).astype(float)
        except Exception as e:
            print(f"  qcut warning for {country}: {e}")
    return result


def within_country_standardize(df, numeric_cols, country_col='country'):
    """StandardScaler applied independently within each country."""
    df = df.copy()
    for country in df[country_col].unique():
        mask = df[country_col] == country
        scaler = StandardScaler()
        df.loc[mask, numeric_cols] = scaler.fit_transform(
            df.loc[mask, numeric_cols])
    return df


# =============================================================================
# SECTION 6 – Data loading  (runs once, shared across both variants)
# =============================================================================
print("=" * 60)
print("LOADING DATA")
print("=" * 60)

Data_ET_cl_r1 = pd.read_stata(ROOT+'r1_oc/ethiopia/etchildlevel8yrold.dta')
Data_IN_cl_r1 = pd.read_stata(ROOT+'r1_oc/india/inchildlevel8yrold.dta')
Data_PE_cl_r1 = pd.read_stata(ROOT+'r1_oc/peru/pechildlevel8yrold.dta')
Data_VN_cl_r1 = pd.read_stata(ROOT+'r1_oc/vietnam/vnchildlevel8yrold.dta')
Data_PE_cl_r1.rename(columns={'placeid':'commid'}, inplace=True)

Data_ET_cl_r2 = pd.read_stata(ROOT+'r2_oc/ethiopia/etchildlevel12yrold.dta')
Data_IN_cl_r2 = pd.read_stata(ROOT+'r2_oc/india/inchildlevel12yrold.dta')
Data_PE_cl_r2 = pd.read_stata(ROOT+'r2_oc/peru/pechildlevel12yrold.dta',
                               convert_categoricals=False)
Data_VN_cl_r2 = pd.read_stata(ROOT+'r2_oc/vietnam/vnchildlevel12yrold.dta',
                               convert_categoricals=False)

Data_ET_cl_r5 = pd.read_stata(ROOT+'ethiopia_r5/etoc_ch_anon/et_r5_occh_olderchild.dta')
Data_IN_cl_r5 = pd.read_stata(ROOT+'india_r5/inoc_ch_anon/in_r5_occh_olderchild.dta',
                               convert_categoricals=False)
Data_PE_cl_r5 = pd.read_stata(ROOT+'peru_r5/pe_oc_ch_anon/pe_r5_occh_olderchild.dta',
                               convert_categoricals=False)
Data_VN_cl_r5 = pd.read_stata(ROOT+'vietnam_r5/vnoc_ch_anon/vn_r5_occh_olderchild.dta',
                               convert_categoricals=False)

Data_ET_act_r5 = pd.read_stata(ROOT+'ethiopia_r5/etoc_ch_anon/et_r5_occh_activity.dta')
Data_IN_act_r5 = pd.read_stata(ROOT+'india_r5/inoc_ch_anon/in_r5_occh_activity.dta',
                                convert_categoricals=False)
Data_PE_act_r5 = pd.read_stata(ROOT+'peru_r5/pe_oc_ch_anon/pe_r5_occh_activity.dta',
                                convert_categoricals=False)
Data_VN_act_r5 = pd.read_stata(ROOT+'vietnam_r5/vnoc_ch_anon/vn_r5_occh_activity.dta',
                                convert_categoricals=False)

Data_ET_com_r1 = pd.read_stata(ROOT+'r1_comm/ethiopia/et_r1_community_main.dta')
Data_IN_com_r1 = pd.read_stata(ROOT+'r1_comm/india/india_r1_community.dta')
Data_PE_com_r1 = pd.read_stata(ROOT+'r1_comm/peru/pe_r1_comm_level.dta')
for col in Data_PE_com_r1.columns:
    if col[:5] in ['pwate','pgarb','pshop','proad','ppubt','pcomg']:
        Data_PE_com_r1.rename(columns={col: col[1:]}, inplace=True)

vn_comm_dir = ROOT+'r1_comm/vietnam/'
vn_comm_list = []
for fname in os.listdir(vn_comm_dir):
    if fname.endswith('.dta') and fname != 'desktop.ini':
        try:
            tmp = pd.read_stata(vn_comm_dir + fname)
            if ('commid' in tmp.columns and
                    len(set(tmp['commid'])) == len(tmp['commid'])):
                if 'formno' in tmp.columns:
                    tmp.drop('formno', axis=1, inplace=True)
                vn_comm_list.append(tmp)
        except Exception:
            pass
Data_VN_com_r1 = vn_comm_list[0]
for ds in vn_comm_list[1:]:
    new_cols = [c for c in ds.columns
                if c not in Data_VN_com_r1.columns or c == 'commid']
    Data_VN_com_r1 = pd.merge(Data_VN_com_r1, ds[new_cols],
                               how='left', on='commid')

Constr_ET = pd.read_stata(ROOT+'Constructed/ethiopia_constructed.dta',
                          convert_categoricals=False)
Constr_IN = pd.read_stata(ROOT+'Constructed/india_constructed.dta',
                          convert_categoricals=False)
Constr_PE = pd.read_stata(ROOT+'Constructed/peru_constructed.dta',
                          convert_categoricals=False)
Constr_VN = pd.read_stata(ROOT+'Constructed/vietnam_constructed.dta',
                          convert_categoricals=False)
print("All files loaded.")

# ── CHILDCODE prefix alignment ──────────────────────────────────────────────
for prefix, ds in zip(['ET','PE','IN','VN'],
                      [Data_ET_cl_r5, Data_PE_cl_r5,
                       Data_IN_cl_r5, Data_VN_cl_r5]):
    ds['CHILDCODE'] = ds['CHILDCODE'].astype(str)
    new_codes = []
    for row in ds['CHILDCODE']:
        if len(row) == 5:
            new_codes.append(prefix + '0' + row)
        elif len(row) == 6:
            new_codes.append(prefix + row)
        else:
            new_codes.append(row)
    ds['CHILDCODE'] = new_codes

for prefix, ds in zip(['ET','PE','IN','VN'],
                      [Data_ET_act_r5, Data_PE_act_r5,
                       Data_IN_act_r5, Data_VN_act_r5]):
    ds.columns = [c.lower() for c in ds.columns]
    new_codes = []
    for row in ds['childcode'].astype(str):
        if len(row) == 5:
            new_codes.append(prefix + '0' + row)
        elif len(row) == 6:
            new_codes.append(prefix + row)
        else:
            new_codes.append(row)
    ds['childcode'] = new_codes

# ── Add country identifier BEFORE combine_disparate_data ─────────────────────
for ds, cty in zip([Data_ET_cl_r1, Data_IN_cl_r1,
                    Data_PE_cl_r1, Data_VN_cl_r1],
                   ['ET','IN','PE','VN']):
    ds['Country'] = cty

# ── Combine datasets ──────────────────────────────────────────────────────────
Data_VN_cl_r1.replace(['Not mentioned','N/A','Missing'], np.nan, inplace=True)
Data_VN_cl_r2.replace(['Not mentioned','N/A','Missing'], np.nan, inplace=True)

Data_r1 = combine_disparate_data(Data_ET_cl_r1, Data_IN_cl_r1,
                                  Data_PE_cl_r1, Data_VN_cl_r1)
Data_r2 = combine_disparate_data(Data_ET_cl_r2, Data_IN_cl_r2,
                                  Data_PE_cl_r2, Data_VN_cl_r2)
Data_r5 = combine_disparate_data(Data_ET_cl_r5, Data_IN_cl_r5,
                                  Data_PE_cl_r5, Data_VN_cl_r5)

Data_community_r1 = combine_disparate_data(Data_ET_com_r1, Data_IN_com_r1,
                                            Data_PE_com_r1, Data_VN_com_r1)
Data_community_r1 = col_values_to_lower(Data_community_r1)

Data_constr    = import_and_merge_constr_dataset(Constr_ET, Constr_IN,
                                                  Constr_PE, Constr_VN)
Data_constr_oc = Data_constr.loc[Data_constr['yc'] == 0].copy()
Data_constr_oc = col_values_to_lower(Data_constr_oc)
Data_constr_oc_r1 = Data_constr_oc.loc[Data_constr_oc['round'] == 1].copy()
print("Data combined.")

# =============================================================================
# SECTION 7 – Income raw score (country-tagged, before binarisation)
# =============================================================================
for ds in [Data_PE_act_r5, Data_IN_act_r5, Data_VN_act_r5]:
    if ds['hwpaidr5'].dtype != object:
        ds['hwpaidr5'] = ds['hwpaidr5'].map(payment_periods)

for prefix, ds in zip(['ET','PE','IN','VN'],
                      [Data_ET_act_r5, Data_PE_act_r5,
                       Data_IN_act_r5, Data_VN_act_r5]):
    ds['erncshr5'] = ds.apply(
        lambda x: x['erncshr5'] * conversion_factors.get(x['hwpaidr5'], np.nan),
        axis=1)
    ds['erncshr5'] = ds['erncshr5'] * exchange[prefix]
    ds['_country'] = prefix.lower()

Data_income_raw = pd.concat([
    Data_ET_act_r5[['childcode','actr5','pymrecr5','erncshr5','_country']],
    Data_PE_act_r5[['childcode','actr5','pymrecr5','erncshr5','_country']],
    Data_IN_act_r5[['childcode','actr5','pymrecr5','erncshr5','_country']],
    Data_VN_act_r5[['childcode','actr5','pymrecr5','erncshr5','_country']],
])
Data_income_raw = Data_income_raw.loc[
    Data_income_raw['actr5'].notna() & (Data_income_raw['actr5'] != 88)]
Data_income_raw.loc[
    (Data_income_raw['pymrecr5']==0)|(Data_income_raw['pymrecr5']=='None'),
    'erncshr5'] = 0
Data_income_raw = Data_income_raw.groupby('childcode').agg(
    income_score=('erncshr5','sum'),
    country=('_country','first')
).reset_index().rename(columns={'childcode':'childid'})
Data_income_raw.loc[Data_income_raw['income_score'] > 10000, 'income_score'] = 10000

# Enrolled children lookup
Enrolled_r5 = Data_r5[['childcode','enrschr5']].copy()
Enrolled_r5['enrschr5'] = Enrolled_r5['enrschr5'].replace(enrschr5_dict)
Enrolled_r5.rename(columns={'childcode':'childid'}, inplace=True)
Data_income_raw = pd.merge(Data_income_raw, Enrolled_r5, on='childid')

# =============================================================================
# SECTION 8 – Mental health raw score (country-tagged, before binarisation)
# =============================================================================
mental_health_vars   = ['feay05r5','feay20r5','feay28r5','cdprssr5',
                        'cemstbr5','crelaxr5','cwryltr5','cgtnrvr5']
mental_health_invert = ['feay05r5','feay20r5','feay28r5','cdprssr5',
                        'cwryltr5','cgtnrvr5']
for col in mental_health_vars:
    Data_r5[col] = pd.to_numeric(
        Data_r5[col].replace(agree_dict), errors='coerce')
    if col in mental_health_invert:
        Data_r5[col] = Data_r5[col].replace(invert_5_classes_dict)

Data_mental_raw = Data_r5[['childcode'] + mental_health_vars].copy()
Data_mental_raw['mental_health_score'] = Data_mental_raw[mental_health_vars].mean(axis=1)
Data_mental_raw = Data_mental_raw[['childcode','mental_health_score']].rename(
    columns={'childcode':'childid'})
scaler_mh = MinMaxScaler()
Data_mental_raw['mental_health_score'] = scaler_mh.fit_transform(
    Data_mental_raw['mental_health_score'].values.reshape(-1,1))

# add country from childid prefix
Data_mental_raw['country'] = Data_mental_raw['childid'].str[:2].str.lower()
Data_income_raw['country']  = Data_income_raw['country'].str.lower()
print("Raw target scores built.")

# Lowercase all string values in the child-level and constructed datasets so
# every replace-dict lookup (yesno_dict, daddead_dict, etc.) hits regardless
# of the original capitalisation in the Stata files.
Data_r1         = col_values_to_lower(Data_r1)
Data_constr_oc_r1 = col_values_to_lower(Data_constr_oc_r1)

# =============================================================================
# SECTION 9 – Feature engineering (round-1 features, same as original pipeline)
# =============================================================================

# Living standard
for c in ['elecq','toiletq','drwaterq']:
    Data_constr_oc_r1[c] = Data_constr_oc_r1[c].replace(yesno_dict)
Data_constr_oc_r1['living_standard'] = \
    Data_constr_oc_r1[['elecq','toiletq','drwaterq']].mean(1)

# Health
Expl_health_r1 = pd.merge(
    Data_r1[['childid','healthy','mightdie']],
    Data_constr_oc_r1[['childid','chmightdie','chhprob','fwfa','fhfa','fbfa']],
    on='childid')
Expl_health_r1 = (Expl_health_r1.replace(same_better_worse_dict)
                                  .replace(yesno_dict)
                                  .replace(very_poor_to_very_good_dict))
for c in ['fwfa','fhfa','fbfa','healthy','mightdie','chmightdie','chhprob']:
    Expl_health_r1[c] = pd.to_numeric(Expl_health_r1[c], errors='coerce')
Expl_health_r1['fatal_inj_or_illn']    = \
    Expl_health_r1[['mightdie','chmightdie','chhprob']].mean(axis=1)
Expl_health_r1['reported_health_level'] = Expl_health_r1['healthy']
Expl_health_r1.drop(['mightdie','chmightdie','chhprob','healthy'],
                     axis=1, inplace=True)

# Schooling
Data_constr_oc_r1['levlread'].replace(levlread_dict, inplace=True)
Data_constr_oc_r1['levlwrit'].replace(levlwrit_dict, inplace=True)
Expl_schooling_r1 = Data_constr_oc_r1[['childid','levlread','levlwrit']].copy()
Expl_schooling_r1['literacy'] = Expl_schooling_r1[['levlread','levlwrit']].sum(axis=1)
Expl_schooling_r1.drop(['levlread','levlwrit'], axis=1, inplace=True)

# Nutrition
Data_constr_oc_r1['shecon14'] = Data_constr_oc_r1['shecon14'].replace(yesno_dict)
Expl_nutrition_r1 = (Data_constr_oc_r1[['childid','shecon14']]
                     .rename(columns={'shecon14':'shock_food_decrease'}).copy())
Expl_nutrition_r1['shock_food_decrease'] = pd.to_numeric(
    Expl_nutrition_r1['shock_food_decrease'], errors='coerce')

# HH characteristics
Data_r1['debt'].replace(yesno_dict,   inplace=True)
Data_r1['oremit'].replace(yesno_dict, inplace=True)
Data_r1['chdalive'] = Data_r1['chdalive'].replace(
    {'section 3 missing from questionnaire':np.nan,'nk':np.nan})
Data_r1['chdalive'] = pd.to_numeric(Data_r1['chdalive'], errors='coerce')
Data_r1['chdborn']  = pd.to_numeric(
    Data_r1['chdborn'].replace({'nk':np.nan,'NK':np.nan}), errors='coerce')
Expl_hh_char_r1 = pd.merge(
    Data_r1[['childid','chdalive','chdborn','debt','oremit']],
    Data_constr_oc_r1[['childid','hhsize']], on='childid')
Expl_hh_char_r1['childs_alive'] = (Expl_hh_char_r1['chdalive'] /
                                    Expl_hh_char_r1['chdborn']).round(2)
Expl_hh_char_r1.drop(['chdalive','chdborn'], axis=1, inplace=True)

# Shocks
Expl_shocks_r1 = Data_constr_oc_r1[['childid','shcrime3','shcrime4']].copy()
for c in ['shcrime3','shcrime4']:
    Expl_shocks_r1[c].replace(yesno_dict, inplace=True)
Expl_shocks_r1['theft_of_property'] = \
    Expl_shocks_r1[['shcrime3','shcrime4']].sum(axis=1)
Expl_shocks_r1 = Expl_shocks_r1[['childid','theft_of_property']]
for src, tgt in [('shcrime8','victim_of_crime'),('shenv9','natural_desaster'),
                 ('shfam7','negative_incidents'),('shfam14','migration_shock')]:
    tmp = Data_constr_oc_r1[['childid',src]].copy()
    tmp[src].replace(yesno_dict, inplace=True)
    tmp.rename(columns={src:tgt}, inplace=True)
    Expl_shocks_r1 = pd.merge(Expl_shocks_r1,
                               tmp[['childid',tgt]], on='childid')
tmp = Data_constr_oc_r1[['childid','shecon3','shecon5','shenv6']].copy()
for c in ['shecon3','shecon5','shenv6']:
    tmp[c].replace(yesno_dict, inplace=True)
tmp['changes_econ_cond_endo'] = tmp[['shecon3','shecon5','shenv6']].sum(axis=1)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1,
                           tmp[['childid','changes_econ_cond_endo']], on='childid')
tmp = Data_constr_oc_r1[['childid','shfam12','shfam13']].copy()
for c in ['shfam12','shfam13']:
    tmp[c].replace(yesno_dict, inplace=True)
tmp['health_death_shock'] = tmp[['shfam12','shfam13']].sum(axis=1)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1,
                           tmp[['childid','health_death_shock']], on='childid')
for c in Expl_shocks_r1.columns:
    if c != 'childid':
        Expl_shocks_r1[c] = pd.to_numeric(Expl_shocks_r1[c], errors='coerce')

# Economic status
Expl_econ_status_r1 = pd.merge(
    Data_constr_oc_r1[['childid','ownlandhse']],
    Data_r1[['childid','ownhouse']], on='childid')
Expl_econ_status_r1['ownlandhse'] = pd.to_numeric(
    Expl_econ_status_r1['ownlandhse'].replace(yesno_dict), errors='coerce')
Expl_econ_status_r1['ownhouse'] = pd.to_numeric(
    Expl_econ_status_r1['ownhouse'].replace(yesno_dict), errors='coerce')
Expl_econ_status_r1['own_house_or_land'] = \
    Expl_econ_status_r1[['ownlandhse','ownhouse']].mean(axis=1).round(2)
Expl_econ_status_r1 = Expl_econ_status_r1[['childid','own_house_or_land']]

# Caregiver
Expl_caregiver_r1 = pd.merge(
    Data_constr_oc_r1[['childid','momage','momedu','dadage','dadedu']],
    Data_r1[['childid','daddead','join','authorit','seemom','seedad',
              'schtyp','namewrk','chores']], on='childid')
for col, dct in [('momedu',education_dict),('dadedu',education_dict),
                 ('daddead',daddead_dict),('join',yesno_dict),
                 ('authorit',yesno_dict),('seemom',seemom_dict),
                 ('seedad',seedad_dict),('schtyp',schtyp_dict),
                 ('namewrk',yesno_dict),('chores',yesno_dict)]:
    Expl_caregiver_r1[col].replace(dct, inplace=True)

# Sex
Expl_sex = Data_r1[['childid','sex']].copy()
Expl_sex['sex'].replace(sex_dict, inplace=True)

# Community
comm_cols = ['commid','pop','twndis','waste','airpol','watpol','contsoil',
             'legal','conclive','thfcrm','violcrm','yuthcrm','proscrm',
             'comcrm','speccrm','water1','water2','water3','water4',
             'garb1','garb2','garb3','garb4',
             'road1','road2','road3','road4',
             'comgrp1','comgrp2','comgrp3','comgrp4',
             'comgrp5','comgrp6','comgrp7','comgrp8']
avail = [c for c in comm_cols if c in Data_community_r1.columns]
Expl_community_r1 = Data_community_r1[avail].copy()
for c in avail:
    Expl_community_r1[c].replace(notatall_to_serious_problem_dict, inplace=True)
    Expl_community_r1[c].replace(yesno_dict, inplace=True)
    Expl_community_r1[c].replace(dontknow_notmentioned_dict, inplace=True)

for grp, out in [(['thfcrm','violcrm','yuthcrm','proscrm','comcrm','speccrm'],'safety'),
                 (['comgrp1','comgrp2','comgrp3','comgrp4',
                   'comgrp5','comgrp6','comgrp7','comgrp8'],'comm_groups'),
                 (['garb1','garb2','garb3','garb4'],'_garb'),
                 (['road1','road2','road3','road4'],'_road'),
                 (['water1','water2','water3','water4'],'_water')]:
    grp = [c for c in grp if c in Expl_community_r1.columns]
    if not grp:
        continue
    if out == 'safety':
        Expl_community_r1['safety'] = Expl_community_r1[grp].sum(axis=1)
    elif out == 'comm_groups':
        Expl_community_r1['comm_groups'] = Expl_community_r1[grp].sum(axis=1)
    elif out == '_garb':
        Expl_community_r1['garbage_taken_by_truck'] = (
            Expl_community_r1.get('garb1', pd.Series(0)) == 1).astype(int)
    elif out == '_road':
        Expl_community_r1['paved_roads_in_community'] = (
            Expl_community_r1.get('road1', pd.Series(0)) == 1).astype(int)
    elif out == '_water':
        Expl_community_r1['drinking_water_from_public_or_private_well'] = (
            (Expl_community_r1.get('water1', pd.Series(0)) == 1) |
            (Expl_community_r1.get('water2', pd.Series(0)) == 1) |
            (Expl_community_r1.get('water3', pd.Series(0)) == 1)
        ).astype(int)
    Expl_community_r1.drop(grp, axis=1, inplace=True)

for c in Expl_community_r1.columns:
    if c != 'commid':
        Expl_community_r1[c] = pd.to_numeric(
            Expl_community_r1[c], errors='coerce')
Expl_community_r1['commid'] = Expl_community_r1['commid'].astype(str).str.lower()

print("Feature engineering done.")

# =============================================================================
# SECTION 10 – Build base feature matrix (unscaled, with country tag)
# =============================================================================
constr_feats = ['childid','hq','sv','cd','zbfa','zhfa','living_standard']
avail_constr = [c for c in constr_feats if c in Data_constr_oc_r1.columns]

dfs_to_merge = [
    Expl_health_r1, Expl_schooling_r1, Expl_nutrition_r1,
    Expl_hh_char_r1, Expl_shocks_r1, Expl_econ_status_r1,
    Expl_caregiver_r1, Expl_sex,
    Data_constr_oc_r1[avail_constr],
]

Data_comb_base = reduce(lambda L, R: pd.merge(L, R, on='childid'), dfs_to_merge)
# carry commid and country
r1_meta = Data_r1[['childid','commid','country']].copy()
r1_meta['commid']  = r1_meta['commid'].astype(str).str.lower()
r1_meta['country'] = r1_meta['country'].astype(str).str.lower()
Data_comb_base = pd.merge(Data_comb_base, r1_meta, on='childid')
Data_comb_base = pd.merge(Data_comb_base, Expl_community_r1, on='commid')

print(f"Base feature matrix: {Data_comb_base.shape}")

# Save original sex values BEFORE any scaling (used for sex split below)
sex_lookup = Data_comb_base[['childid','sex']].copy()

# =============================================================================
# SECTION 11 – Per-variant analysis function
# =============================================================================

def run_analysis(quantile_upper, label):
    """
    quantile_upper : 0.5 → within-country median split (main text)
                     0.25 → within-country 25th-pct split (appendix)
    label          : 'median' or 'q25'
    """
    outdir = os.path.join('results', label)
    os.makedirs(outdir, exist_ok=True)
    print()
    print("=" * 60)
    print(f"VARIANT: {label}  (quantile upper = {quantile_upper})")
    print("=" * 60)

    # ── 1. Within-country target construction ─────────────────────────────
    # Income: enrolled-student exclusion per country THEN within-country qcut
    inc = Data_income_raw.copy()
    exclude_ids = []
    for cty in inc['country'].unique():
        mask = inc['country'] == cty
        med_c = np.median(inc.loc[mask, 'income_score'].dropna())
        exc_mask = mask & (inc['enrschr5'] == 1) & (inc['income_score'] < med_c)
        exclude_ids.extend(inc.loc[exc_mask, 'childid'].tolist())
    inc = inc[~inc['childid'].isin(exclude_ids)].copy()
    inc['income_score_bin2'] = within_country_qcut(
        inc, 'income_score', quantile_upper)
    Data_income_comb = inc[['childid','income_score',
                             'income_score_bin2','enrschr5','country']].copy()

    # Mental health: within-country qcut
    mnt = Data_mental_raw.copy()
    mnt['mental_health_score_bin2'] = within_country_qcut(
        mnt, 'mental_health_score', quantile_upper)
    Data_mental_comb = mnt[['childid','mental_health_score',
                              'mental_health_score_bin2','country']].copy()

    n0_inc = (Data_income_comb['income_score_bin2']==0).sum()
    n1_inc = (Data_income_comb['income_score_bin2']==1).sum()
    n0_mnt = (Data_mental_comb['mental_health_score_bin2']==0).sum()
    n1_mnt = (Data_mental_comb['mental_health_score_bin2']==1).sum()
    print(f"Income  target: class 0 = {n0_inc}, class 1 = {n1_inc}")
    print(f"Mental  target: class 0 = {n0_mnt}, class 1 = {n1_mnt}")

    # ── 2. Within-country feature standardization ─────────────────────────
    base = Data_comb_base.copy()
    numeric_cols = base.select_dtypes(include='number').columns.tolist()
    # exclude sex from scaling (binary, will be used for sex split)
    scale_cols = [c for c in numeric_cols if c != 'sex']
    base = within_country_standardize(base, scale_cols, country_col='country')

    # ── 3. Merge with targets ──────────────────────────────────────────────
    target_vars_income = list(Data_income_comb.columns)
    target_vars_mental = list(Data_mental_comb.columns)

    # Drop country from base before merge — both base and target frames carry
    # 'country'; keeping it in base would create country_x/country_y which are
    # string columns that land in the ML feature matrix and crash tree models.
    base_ml = base.drop(columns=['country'], errors='ignore')
    Data_ML_income = pd.merge(base_ml, Data_income_comb, on='childid')
    Data_ML_mental = pd.merge(base_ml, Data_mental_comb, on='childid')
    print(f"ML income shape:  {Data_ML_income.shape}")
    print(f"ML mental shape:  {Data_ML_mental.shape}")

    # ── 4. Sex splits (needed for Figures and Table 3) ────────────────────
    def sex_split(Data_ML, target_vars):
        merged = pd.merge(Data_ML, sex_lookup, on='childid',
                          suffixes=('','_orig'))
        sex_col = 'sex_orig' if 'sex_orig' in merged.columns else 'sex'
        female = merged.loc[merged[sex_col] == 1].drop(
            ['sex','sex_orig'], axis=1, errors='ignore').copy()
        male   = merged.loc[merged[sex_col] == 0].drop(
            ['sex','sex_orig'], axis=1, errors='ignore').copy()
        tv = [v for v in target_vars if v != 'sex']
        return female, male, tv

    female_inc, male_inc, tv_inc = sex_split(Data_ML_income, target_vars_income)
    female_mnt, male_mnt, tv_mnt = sex_split(Data_ML_mental, target_vars_mental)

    # ── 5. Figure 1 – SHAP plots ───────────────────────────────────────────
    print("\nRunning SHAP for Figure 1..."); sys.stdout.flush()

    _, _, _, _, X_inc, y_inc = prepare_ML_dataset_inline(
        Data_ML_income, target_vars_income, 'income_score_bin2',
        test_size=0.3, random_state=42)
    print("  SHAP – income..."); sys.stdout.flush()
    SHAP_repeated_CV_inline(
        Data_ML_income, X_inc, y_inc,
        n_splits=SHAP_SPLITS, CV_repeats=SHAP_REPEATS,
        outdir=outdir, prefix='fig1_income', max_features=10, seed=1000)

    _, _, _, _, X_mnt, y_mnt = prepare_ML_dataset_inline(
        Data_ML_mental, target_vars_mental, 'mental_health_score_bin2',
        test_size=0.3, random_state=42)
    print("  SHAP – mental health..."); sys.stdout.flush()
    SHAP_repeated_CV_inline(
        Data_ML_mental, X_mnt, y_mnt,
        n_splits=SHAP_SPLITS, CV_repeats=SHAP_REPEATS,
        outdir=outdir, prefix='fig1_mental', max_features=10, seed=1000)
    print("  Figure 1 saved."); sys.stdout.flush()

    # ── 6. Figure 2 – Sex-stratified SHAP ─────────────────────────────────
    print("\nRunning sex-stratified SHAP for Figure 2..."); sys.stdout.flush()

    def get_XY(Data_sub, tv, target_var, random_state=42):
        _, _, _, _, X, y = prepare_ML_dataset_inline(
            Data_sub, tv, target_var, test_size=0.3,
            random_state=random_state)
        return X, y

    Xf_mnt, yf_mnt = get_XY(female_mnt, tv_mnt, 'mental_health_score_bin2')
    Xm_mnt, ym_mnt = get_XY(male_mnt,   tv_mnt, 'mental_health_score_bin2')
    print("  SHAP – mental Female..."); sys.stdout.flush()
    avg_f_mnt, _ = SHAP_repeated_CV_inline(
        female_mnt, Xf_mnt, yf_mnt,
        SHAP_SPLITS, SHAP_REPEATS,
        outdir=outdir, prefix='fig2_mental_female', max_features=10)
    print("  SHAP – mental Male..."); sys.stdout.flush()
    avg_m_mnt, _ = SHAP_repeated_CV_inline(
        male_mnt, Xm_mnt, ym_mnt,
        SHAP_SPLITS, SHAP_REPEATS,
        outdir=outdir, prefix='fig2_mental_male', max_features=10)
    shap_hetero_plot(avg_f_mnt, avg_m_mnt, Xf_mnt, Xm_mnt,
                     os.path.join(outdir, 'fig2_mental_hetero.png'),
                     n_features=25)

    Xf_inc, yf_inc = get_XY(female_inc, tv_inc, 'income_score_bin2')
    Xm_inc, ym_inc = get_XY(male_inc,   tv_inc, 'income_score_bin2')
    print("  SHAP – income Female..."); sys.stdout.flush()
    avg_f_inc, _ = SHAP_repeated_CV_inline(
        female_inc, Xf_inc, yf_inc,
        SHAP_SPLITS, SHAP_REPEATS,
        outdir=outdir, prefix='fig2_income_female', max_features=10)
    print("  SHAP – income Male..."); sys.stdout.flush()
    avg_m_inc, _ = SHAP_repeated_CV_inline(
        male_inc, Xm_inc, ym_inc,
        SHAP_SPLITS, SHAP_REPEATS,
        outdir=outdir, prefix='fig2_income_male', max_features=10)
    shap_hetero_plot(avg_f_inc, avg_m_inc, Xf_inc, Xm_inc,
                     os.path.join(outdir, 'fig2_income_hetero.png'),
                     n_features=25)
    print("  Figure 2 saved."); sys.stdout.flush()

    # ── 7. VIF ────────────────────────────────────────────────────────────
    print("\nComputing VIF..."); sys.stdout.flush()
    ALWAYS_EXCL_VIF = set(target_vars_income) | {'commid','country'}
    X_vif_inc = Data_ML_income.loc[:,
        ~Data_ML_income.columns.isin(ALWAYS_EXCL_VIF)].copy()
    ALWAYS_EXCL_VIF2 = set(target_vars_mental) | {'commid','country'}
    X_vif_mnt = Data_ML_mental.loc[:,
        ~Data_ML_mental.columns.isin(ALWAYS_EXCL_VIF2)].copy()

    vif_inc = compute_vif(X_vif_inc, "Income")
    vif_mnt = compute_vif(X_vif_mnt, "Mental Health")
    vif_inc.to_csv(os.path.join(outdir, 'vif_income.csv'), index=False)
    vif_mnt.to_csv(os.path.join(outdir, 'vif_mental.csv'), index=False)

    pd.set_option('display.float_format', '{:.2f}'.format)
    print(f"\nVIF – Income ({label}):")
    print(vif_inc.to_string(index=False))
    print(f"\nVIF – Mental Health ({label}):")
    print(vif_mnt.to_string(index=False))
    sys.stdout.flush()

    # ── 8. Table 2 – main ML comparison ───────────────────────────────────
    print("\nRunning ML comparison (Table 2)..."); sys.stdout.flush()
    models = ["Regression","DecisionTree","RandomForest","XGBoost"]

    print("  Income..."); sys.stdout.flush()
    res_income = ML_comparison_v3(
        Data_ML_income, models, target_vars_income,
        'income_score_bin2', test_size=0.1,
        i_range=I_RANGE, bootstrap_threshold=0.95, seed=24)

    print("  Mental health..."); sys.stdout.flush()
    res_mental = ML_comparison_v3(
        Data_ML_mental, models, target_vars_mental,
        'mental_health_score_bin2', test_size=0.1,
        i_range=I_RANGE, bootstrap_threshold=0.95, seed=24)

    t2 = latex_table2(res_income, res_mental)
    with open(os.path.join(outdir, 'table2.tex'), 'w') as f:
        f.write(t2)
    print("  Table 2 saved."); sys.stdout.flush()
    print("\n  -- Table 2 summary --")
    for task, res in [("Income", res_income), ("Mental", res_mental)]:
        for m in models:
            print(f"  {task} | {m:15s} | "
                  f"AUC={np.mean(res[m]['auc']):.3f}  "
                  f"F1={np.mean(res[m]['f1']):.3f}  "
                  f"Acc={np.mean(res[m]['acc']):.3f}")
    sys.stdout.flush()

    # ── 9. Table 3 – sex-stratified ────────────────────────────────────────
    print("\nRunning sex-stratified analysis (Table 3)..."); sys.stdout.flush()

    print("  Income Female..."); sys.stdout.flush()
    res_f_inc = ML_comparison_v3(
        female_inc, models, tv_inc, 'income_score_bin2',
        test_size=0.1, i_range=I_RANGE, bootstrap_threshold=0.95, seed=44)
    print("  Income Male..."); sys.stdout.flush()
    res_m_inc = ML_comparison_v3(
        male_inc, models, tv_inc, 'income_score_bin2',
        test_size=0.1, i_range=I_RANGE, bootstrap_threshold=0.95, seed=44)
    print("  Mental Female..."); sys.stdout.flush()
    res_f_mnt = ML_comparison_v3(
        female_mnt, models, tv_mnt, 'mental_health_score_bin2',
        test_size=0.1, i_range=I_RANGE, bootstrap_threshold=0.95, seed=44)
    print("  Mental Male..."); sys.stdout.flush()
    res_m_mnt = ML_comparison_v3(
        male_mnt, models, tv_mnt, 'mental_health_score_bin2',
        test_size=0.1, i_range=I_RANGE, bootstrap_threshold=0.95, seed=44)

    t3 = latex_table3(res_f_inc, res_m_inc, res_f_mnt, res_m_mnt)
    with open(os.path.join(outdir, 'table3.tex'), 'w') as f:
        f.write(t3)
    print("  Table 3 saved."); sys.stdout.flush()

    print(f"\n{'='*60}")
    print(f"VARIANT '{label}' COMPLETE. Results in: results/{label}/")
    print(f"{'='*60}")
    sys.stdout.flush()


# =============================================================================
# SECTION 12 – Execute both variants
# =============================================================================
run_analysis(quantile_upper=0.5,  label='median')   # main text
run_analysis(quantile_upper=0.25, label='q25')       # appendix

print("\nAll done.")
