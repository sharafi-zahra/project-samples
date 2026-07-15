# -*- coding: utf-8 -*-
"""
Standalone VIF analysis script.
Replicates the full data pipeline from Data_import_experiment.py and
EDA_separate_rounds_oc_experiment.py, then computes VIF on the feature
matrix used for both the income and mental-health classification tasks.
"""

import os, sys, warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from functools import reduce
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ─────────────────────────────────────────────────────────────────────────────
# Dictionaries  (from Functions.py)
# ─────────────────────────────────────────────────────────────────────────────
schtyp_dict   = {"public":1,"private":0,"n/a - not currently in school":np.nan,"nk":np.nan}
seedad_dict   = {"daily":5,"weekly":4,"monthly":3,"less than monthly":2,"not in the last 6 months":1,"n/a father dead":0}
seemom_dict   = {"daily":5,"weekly":4,"monthly":3,"less than monthly":2,"not in the last 6 months":1,"n/a - mother dead":0}
daddead_dict  = {"in the household":0,"not in the household":1,"father dead":2}
enrschr5_dict = {"no":0,"yes, attending regularly":1,"no, but attending part-time":0,"yes, but attending irregularly":1,"n/a":np.nan,88:np.nan,3:np.nan}
yesno_dict    = {"yes":1,"Yes":1,"no":0,"No":0,"yes exists":1,"n/a under 5yrs":np.nan,"refused to answer":np.nan,77:np.nan,"nk":np.nan,"NK":np.nan}
sex_dict      = {"male":0,"female":1}
education_dict= {"none":0,"grade 1":1,"grade 2":2,"grade 3":3,"grade 4":4,"grade 5":5,"grade 6":6,"grade 7":7,"grade 8":8,"grade 9":9,"grade 10":10,"grade 11":11,"grade 12":12,"adult literacy":7,"technical, pedagogical, cetpro (incomplete)":7,"post-secondary, vocational":7,"university":13,"university (incomplete)":13,"university (complete)":13,"vocational, technical college":13,"technical, pedagogical, cetpro (complete)":13,"other":np.nan,"religious education":np.nan}
levlread_dict = {"can't read anything":0,"reads letters":1,"reads word":2,"reads sentence":3,79:np.nan,"Refused to answer":np.nan,"refused to answer":np.nan}
levlwrit_dict = {"no":0,"yes with difficulty or errors":1,"yes without difficulty or errors":2,79:np.nan,"Refused to answer":np.nan,"refused to answer":np.nan}
same_better_worse_dict = {"Worse":0,"worse":0,"Same":1,"same":1,"Better":2,"better":2,99:np.nan}
very_poor_to_very_good_dict = {"very poor":0,"poor":1,"average":2,"good":3,"very good":4,"Very poor":0,"Poor":1,"Average":2,"Good":3,"Very good":4}
agree_dict    = {"Strongly disagree":1,"Disagree":2,"More or less":3,"Agree":4,"Strongly agree":5,"Refused to answer":np.nan,"NK":np.nan,"strongly disagree":1,"disagree":2,"more or less":3,"agree":4,"strongly agree":5,"refused to answer":np.nan,"nk":np.nan,88:np.nan,77:np.nan,79:np.nan}
invert_5_classes_dict = {1:5,2:4,4:2,5:1}
notatall_to_serious_problem_dict = {"not at all":0,"doesn't affect the community":0,"Not at all":0,"only a little":1,"slightly":1,"Slightly":1,"severely":2,"Severely":2,"serious problem":2,"missing":np.nan}
dontknow_notmentioned_dict = {"not mentioned":np.nan,"don`t know":np.nan,"don't know":np.nan,"not applicable, community is part of the capital":np.nan,"dk":np.nan,"na":np.nan}
high_medium_low_dict = {"high":2,"medium":1,"low":0,"missing":np.nan}
citizenship_dict = {"no citizenship":0,"some citizenship":1}

# ─────────────────────────────────────────────────────────────────────────────
# Core functions  (from Functions.py)
# ─────────────────────────────────────────────────────────────────────────────

def col_values_to_lower(Data):
    for i in Data.columns:
        if i not in ('childid','childcode','CHILDID','CHILDCODE'):
            try:
                if Data[i].dtype == object:
                    Data[i] = Data[i].str.lower()
            except Exception:
                pass
    return Data


def combine_disparate_data(Data_ET, Data_IN, Data_PE, Data_VN):
    datasets = [Data_ET, Data_IN, Data_PE, Data_VN]
    for ds in datasets:
        ds.columns = [c.lower() for c in ds.columns]
    col_lists = [list(ds.columns) for ds in datasets]
    inter = set.intersection(*[set(c) for c in col_lists])
    # sort by order in first dataset
    ordered = [c for c in col_lists[0] if c in inter]
    reduced = [ds[[c for c in ds.columns if c in inter]].copy() for ds in datasets]
    for ds in reduced:
        missing = [c for c in ordered if c not in ds.columns]
        for c in missing:
            ds[c] = np.nan
    return pd.concat([ds[ordered] for ds in reduced], ignore_index=True)


def missing_values(Data, threshold, remove=False):
    nan_pct = (Data.isna().sum() / len(Data)) * 100
    above = nan_pct[nan_pct > threshold]
    print(f'  {len(above)} variables with >{threshold}% missing')
    if remove:
        Data.drop(columns=above.index.tolist(), inplace=True)


def import_and_merge_constr_dataset(Constr_ET=None, Constr_IN=None, Constr_PE=None, Constr_VN=None):
    rename_map = {'wi_new':'wi','hq_new':'hq','sv_new':'sv','cd_new':'cd',
                  'elecq_new':'elecq','toiletq_new':'toiletq','drwaterq_new':'drwaterq'}
    for ds in [Constr_ET, Constr_VN]:
        if ds is not None:
            ds.rename(columns={k:v for k,v in rename_map.items() if k in ds.columns}, inplace=True)
    parts = [ds for ds in [Constr_ET, Constr_IN, Constr_PE, Constr_VN] if ds is not None]
    inter = set.intersection(*[set(ds.columns) for ds in parts])
    reduced = [ds[[c for c in ds.columns if c in inter]].copy() for ds in parts]
    return pd.concat(reduced, ignore_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────
ROOT = './20241002_datasets/'
print("Loading raw data files...")

# Round-1 child level
Data_ET_cl_r1 = pd.read_stata(ROOT+'r1_oc/ethiopia/etchildlevel8yrold.dta')
Data_IN_cl_r1 = pd.read_stata(ROOT+'r1_oc/india/inchildlevel8yrold.dta')
Data_PE_cl_r1 = pd.read_stata(ROOT+'r1_oc/peru/pechildlevel8yrold.dta')
Data_VN_cl_r1 = pd.read_stata(ROOT+'r1_oc/vietnam/vnchildlevel8yrold.dta')
Data_PE_cl_r1.rename(columns={'placeid':'commid'}, inplace=True)

# Round-2 child level
Data_ET_cl_r2 = pd.read_stata(ROOT+'r2_oc/ethiopia/etchildlevel12yrold.dta')
Data_IN_cl_r2 = pd.read_stata(ROOT+'r2_oc/india/inchildlevel12yrold.dta')
Data_PE_cl_r2 = pd.read_stata(ROOT+'r2_oc/peru/pechildlevel12yrold.dta', convert_categoricals=False)
Data_VN_cl_r2 = pd.read_stata(ROOT+'r2_oc/vietnam/vnchildlevel12yrold.dta', convert_categoricals=False)

# Round-5 child level
Data_ET_cl_r5 = pd.read_stata(ROOT+'ethiopia_r5/etoc_ch_anon/et_r5_occh_olderchild.dta')
Data_IN_cl_r5 = pd.read_stata(ROOT+'india_r5/inoc_ch_anon/in_r5_occh_olderchild.dta', convert_categoricals=False)
Data_PE_cl_r5 = pd.read_stata(ROOT+'peru_r5/pe_oc_ch_anon/pe_r5_occh_olderchild.dta', convert_categoricals=False)
Data_VN_cl_r5 = pd.read_stata(ROOT+'vietnam_r5/vnoc_ch_anon/vn_r5_occh_olderchild.dta', convert_categoricals=False)

# Round-5 activity level
Data_ET_activity_r5 = pd.read_stata(ROOT+'ethiopia_r5/etoc_ch_anon/et_r5_occh_activity.dta')
Data_IN_activity_r5 = pd.read_stata(ROOT+'india_r5/inoc_ch_anon/in_r5_occh_activity.dta', convert_categoricals=False)
Data_PE_activity_r5 = pd.read_stata(ROOT+'peru_r5/pe_oc_ch_anon/pe_r5_occh_activity.dta', convert_categoricals=False)
Data_VN_activity_r5 = pd.read_stata(ROOT+'vietnam_r5/vnoc_ch_anon/vn_r5_occh_activity.dta', convert_categoricals=False)

# Community round-1
Data_ET_com_r1 = pd.read_stata(ROOT+'r1_comm/ethiopia/et_r1_community_main.dta')
Data_IN_com_r1 = pd.read_stata(ROOT+'r1_comm/india/india_r1_community.dta')
Data_PE_com_r1 = pd.read_stata(ROOT+'r1_comm/peru/pe_r1_comm_level.dta')

# Vietnam community (multiple files - merge those with unique commid)
vn_comm_dir = ROOT+'r1_comm/vietnam/'
Data_list = []
for fname in os.listdir(vn_comm_dir):
    if fname.endswith('.dta') and fname != 'desktop.ini':
        try:
            tmp = pd.read_stata(vn_comm_dir + fname)
            if 'commid' in tmp.columns and len(set(tmp['commid'])) == len(tmp['commid']):
                if 'formno' in tmp.columns:
                    tmp.drop('formno', axis=1, inplace=True)
                Data_list.append(tmp)
        except Exception as e:
            print(f"  Skipping {fname}: {e}")

Data_VN_com_r1 = Data_list[0]
for ds in Data_list[1:]:
    new_cols = [c for c in ds.columns if c not in Data_VN_com_r1.columns or c == 'commid']
    Data_VN_com_r1 = pd.merge(Data_VN_com_r1, ds[new_cols], how='left', on='commid')

# Constructed files
Constr_ET = pd.read_stata(ROOT+'Constructed/ethiopia_constructed.dta', convert_categoricals=False)
Constr_IN = pd.read_stata(ROOT+'Constructed/india_constructed.dta', convert_categoricals=False)
Constr_PE = pd.read_stata(ROOT+'Constructed/peru_constructed.dta', convert_categoricals=False)
Constr_VN = pd.read_stata(ROOT+'Constructed/vietnam_constructed.dta', convert_categoricals=False)

print("All files loaded.")

# ─────────────────────────────────────────────────────────────────────────────
# Align CHILDCODE in r5 datasets
# ─────────────────────────────────────────────────────────────────────────────
for prefix, ds in zip(['ET','PE','IN','VN'], [Data_ET_cl_r5, Data_PE_cl_r5, Data_IN_cl_r5, Data_VN_cl_r5]):
    ds['CHILDCODE'] = ds['CHILDCODE'].astype(str)
    for i, row in enumerate(ds['CHILDCODE']):
        if len(row) == 5:
            ds['CHILDCODE'].iloc[i] = prefix + '0' + row
        elif len(row) == 6:
            ds['CHILDCODE'].iloc[i] = prefix + row

# Lowercase activity childcodes
for prefix, ds in zip(['ET','PE','IN','VN'],
                      [Data_ET_activity_r5, Data_PE_activity_r5, Data_IN_activity_r5, Data_VN_activity_r5]):
    ds.columns = [c.lower() for c in ds.columns]
    ds['childcode'] = ds['childcode'].astype(str)
    for i, row in enumerate(ds['childcode']):
        if len(row) == 5:
            ds['childcode'].iloc[i] = prefix + '0' + row
        elif len(row) == 6:
            ds['childcode'].iloc[i] = prefix + row

# ─────────────────────────────────────────────────────────────────────────────
# Combine disparate datasets
# ─────────────────────────────────────────────────────────────────────────────
Data_VN_cl_r1.replace(['Not mentioned','N/A','Missing'], np.nan, inplace=True)
Data_VN_cl_r2.replace(['Not mentioned','N/A','Missing'], np.nan, inplace=True)

for ds, country in zip([Data_ET_cl_r1, Data_IN_cl_r1, Data_PE_cl_r1, Data_VN_cl_r1], ['ET','IN','PE','VN']):
    ds['Country'] = country

Data_r1 = combine_disparate_data(Data_ET_cl_r1, Data_IN_cl_r1, Data_PE_cl_r1, Data_VN_cl_r1)
Data_r2 = combine_disparate_data(Data_ET_cl_r2, Data_IN_cl_r2, Data_PE_cl_r2, Data_VN_cl_r2)
Data_r5 = combine_disparate_data(Data_ET_cl_r5, Data_IN_cl_r5, Data_PE_cl_r5, Data_VN_cl_r5)

# Peru community column rename
for col in Data_PE_com_r1.columns:
    if col[:5] in ['pwate','pgarb','pshop','proad','ppubt','pcomg']:
        Data_PE_com_r1.rename(columns={col: col[1:]}, inplace=True)

Data_community_r1 = combine_disparate_data(Data_ET_com_r1, Data_IN_com_r1, Data_PE_com_r1, Data_VN_com_r1)
Data_community_r1 = col_values_to_lower(Data_community_r1)

# Constructed
Data_constr     = import_and_merge_constr_dataset(Constr_ET, Constr_IN, Constr_PE, Constr_VN)
Data_constr_oc  = Data_constr.loc[Data_constr['yc'] == 0].copy()
Data_constr_oc  = col_values_to_lower(Data_constr_oc)
Data_constr_oc_r1 = Data_constr_oc.loc[Data_constr_oc['round'] == 1].copy()
Data_constr_oc_r2 = Data_constr_oc.loc[Data_constr_oc['round'] == 2].copy()

print("Data combined.")

# ─────────────────────────────────────────────────────────────────────────────
# Target variable 1: Mental health score  (from Data_import_experiment.py)
# ─────────────────────────────────────────────────────────────────────────────
mental_health_vars   = ['feay05r5','feay20r5','feay28r5','cdprssr5','cemstbr5','crelaxr5','cwryltr5','cgtnrvr5']
mental_health_invert = ['feay05r5','feay20r5','feay28r5','cdprssr5','cwryltr5','cgtnrvr5']

for col in mental_health_vars:
    Data_r5[col] = Data_r5[col].replace(agree_dict)
    Data_r5[col] = pd.to_numeric(Data_r5[col], errors='coerce')
    if col in mental_health_invert:
        Data_r5[col] = Data_r5[col].replace(invert_5_classes_dict)

Data_mental_health_comb = Data_r5[['childcode'] + mental_health_vars].copy()
Data_mental_health_comb['mental_health_score'] = Data_mental_health_comb[mental_health_vars].mean(axis=1)
Data_mental_health_comb = Data_mental_health_comb[['childcode','mental_health_score']].rename(columns={'childcode':'childid'})

scaler_mh = MinMaxScaler()
Data_mental_health_comb['mental_health_score'] = scaler_mh.fit_transform(
    Data_mental_health_comb['mental_health_score'].values.reshape(-1,1))
Data_mental_health_comb['mental_health_score_bin2'] = pd.qcut(
    Data_mental_health_comb['mental_health_score'], [0, 0.25, 1.0], labels=[0,1])

# ─────────────────────────────────────────────────────────────────────────────
# Target variable 2: Income score  (from Data_import_experiment.py)
# ─────────────────────────────────────────────────────────────────────────────
payment_periods = {1:"Per hour",2:"Per day",3:"Per week",4:"Per month",5:"Per year",6:"Per piece",7:"Other, specify",
                   79:"Refused to answer",88:"NA",1.0:"Per hour",2.0:"Per day",3.0:"Per week",4.0:"Per month",
                   5.0:"Per year",6.0:"Per piece",7.0:"Other, specify"}
conversion_factors = {"Per hour":160,"Per day":20,"Per week":4.33,"Per month":1,"Per year":1/12,
                      "Per piece":np.nan,"NA":np.nan,"Other, specify":1,"N/A":1,np.nan:np.nan}

for ds in [Data_PE_activity_r5, Data_IN_activity_r5, Data_VN_activity_r5]:
    if ds['hwpaidr5'].dtype != object:
        ds['hwpaidr5'] = ds['hwpaidr5'].map(payment_periods)

exchange = {'ET':0.0458,'PE':0.2965,'IN':0.0149,'VN':0.04}
for prefix, ds in zip(['ET','PE','IN','VN'],
                      [Data_ET_activity_r5, Data_PE_activity_r5, Data_IN_activity_r5, Data_VN_activity_r5]):
    ds['erncshr5'] = ds.apply(lambda x: x['erncshr5'] * conversion_factors.get(x['hwpaidr5'], np.nan), axis=1)
    ds['erncshr5'] = ds['erncshr5'] * exchange[prefix]

Data_income_comb = pd.concat([
    Data_ET_activity_r5[['childcode','actr5','pymrecr5','erncshr5']],
    Data_PE_activity_r5[['childcode','actr5','pymrecr5','erncshr5']],
    Data_IN_activity_r5[['childcode','actr5','pymrecr5','erncshr5']],
    Data_VN_activity_r5[['childcode','actr5','pymrecr5','erncshr5']],
])
Data_income_comb = Data_income_comb.loc[
    Data_income_comb['actr5'].notna() & (Data_income_comb['actr5'] != 88)]
Data_income_comb.loc[
    (Data_income_comb['pymrecr5']==0)|(Data_income_comb['pymrecr5']=='None'), 'erncshr5'] = 0
Data_income_comb = Data_income_comb.groupby('childcode')['erncshr5'].sum().reset_index()
Data_income_comb.rename(columns={'childcode':'childid','erncshr5':'income_score'}, inplace=True)
Data_income_comb.loc[Data_income_comb['income_score']>10000,'income_score'] = 10000
Data_income_comb['income_score_bin2'] = pd.qcut(
    Data_income_comb['income_score'], [0, 0.25, 1.0], labels=[0,1])

# Remove enrolled children below median income
Enrolled_r5 = Data_r5[['childcode','enrschr5']].copy()
Enrolled_r5['enrschr5'] = Enrolled_r5['enrschr5'].replace(enrschr5_dict)
Enrolled_r5.rename(columns={'childcode':'childid'}, inplace=True)
Data_income_comb = pd.merge(Data_income_comb, Enrolled_r5, on='childid')
med_inc = np.median(Data_income_comb['income_score'])
exclude = Data_income_comb.loc[
    (Data_income_comb['enrschr5']==1)&(Data_income_comb['income_score']<med_inc),'childid']
Data_income_comb = Data_income_comb[~Data_income_comb['childid'].isin(exclude)]

target_vars_list_income = list(Data_income_comb.columns)
target_vars_list_mental = list(Data_mental_health_comb.columns)

print("Target variables built.")

# ─────────────────────────────────────────────────────────────────────────────
# Feature engineering round-1  (from EDA_separate_rounds_oc_experiment.py)
# ─────────────────────────────────────────────────────────────────────────────

# --- Health ---
Expl_health_r1 = pd.merge(
    Data_r1[['childid','healthy','mightdie']],
    Data_constr_oc_r1[['childid','chmightdie','chhprob','fwfa','fhfa','fbfa']],
    on='childid')
Expl_health_r1 = Expl_health_r1.replace(same_better_worse_dict).replace(yesno_dict).replace(very_poor_to_very_good_dict)
for c in ['fwfa','fhfa','fbfa','healthy','mightdie','chmightdie','chhprob']:
    Expl_health_r1[c] = pd.to_numeric(Expl_health_r1[c], errors='coerce')
Expl_health_r1['fatal_inj_or_illn']    = Expl_health_r1[['mightdie','chmightdie','chhprob']].mean(axis=1)
Expl_health_r1['reported_health_level'] = Expl_health_r1['healthy']
Expl_health_r1.drop(['mightdie','chmightdie','chhprob','healthy'], axis=1, inplace=True)

# --- Living standard ---
for c in ['elecq','toiletq','drwaterq']:
    Data_constr_oc_r1[c] = Data_constr_oc_r1[c].replace(yesno_dict)
Data_constr_oc_r1['living_standard'] = Data_constr_oc_r1[['elecq','toiletq','drwaterq']].mean(1)

# --- Schooling ---
Data_constr_oc_r1['levlread'].replace(levlread_dict, inplace=True)
Data_constr_oc_r1['levlwrit'].replace(levlwrit_dict, inplace=True)
Expl_schooling_r1 = Data_constr_oc_r1[['childid','levlread','levlwrit']].copy()
Expl_schooling_r1['literacy'] = Expl_schooling_r1[['levlread','levlwrit']].sum(axis=1)
Expl_schooling_r1.drop(['levlread','levlwrit'], axis=1, inplace=True)

# --- Nutrition ---
Data_constr_oc_r1['shecon14'] = Data_constr_oc_r1['shecon14'].replace(yesno_dict)
Expl_nutrition_r1 = Data_constr_oc_r1[['childid','shecon14']].rename(columns={'shecon14':'shock_food_decrease'}).copy()
Expl_nutrition_r1['shock_food_decrease'] = pd.to_numeric(Expl_nutrition_r1['shock_food_decrease'], errors='coerce')

# --- HH characteristics ---
Data_r1['debt'].replace(yesno_dict, inplace=True)
Data_r1['oremit'].replace(yesno_dict, inplace=True)
Data_r1['chdalive'] = Data_r1['chdalive'].replace({'section 3 missing from questionnaire':np.nan,'nk':np.nan})
Data_r1['chdalive'] = pd.to_numeric(Data_r1['chdalive'], errors='coerce')
Data_r1['chdborn']  = Data_r1['chdborn'].replace({'nk':np.nan,'NK':np.nan})
Data_r1['chdborn']  = pd.to_numeric(Data_r1['chdborn'], errors='coerce')
Expl_hh_char_r1 = pd.merge(
    Data_r1[['childid','chdalive','chdborn','debt','oremit']],
    Data_constr_oc_r1[['childid','hhsize']], on='childid')
Expl_hh_char_r1['childs_alive'] = (Expl_hh_char_r1['chdalive'] / Expl_hh_char_r1['chdborn']).round(2)
Expl_hh_char_r1.drop(['chdalive','chdborn'], axis=1, inplace=True)

# --- Shocks ---
Expl_shocks_r1 = Data_constr_oc_r1[['childid','shcrime3','shcrime4']].copy()
for c in ['shcrime3','shcrime4']:
    Expl_shocks_r1[c].replace(yesno_dict, inplace=True)
Expl_shocks_r1['theft_of_property'] = Expl_shocks_r1[['shcrime3','shcrime4']].sum(axis=1)
Expl_shocks_r1 = Expl_shocks_r1[['childid','theft_of_property']]

tmp = Data_constr_oc_r1[['childid','shcrime8']].copy()
tmp['shcrime8'].replace(yesno_dict, inplace=True)
tmp.rename(columns={'shcrime8':'victim_of_crime'}, inplace=True)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1, tmp[['childid','victim_of_crime']], on='childid')

tmp = Data_constr_oc_r1[['childid','shecon3','shecon5','shenv6']].copy()
for c in ['shecon3','shecon5','shenv6']:
    tmp[c].replace(yesno_dict, inplace=True)
tmp['changes_econ_cond_endo'] = tmp[['shecon3','shecon5','shenv6']].sum(axis=1)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1, tmp[['childid','changes_econ_cond_endo']], on='childid')

tmp = Data_constr_oc_r1[['childid','shenv9']].copy()
tmp['shenv9'].replace(yesno_dict, inplace=True)
tmp.rename(columns={'shenv9':'natural_desaster'}, inplace=True)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1, tmp[['childid','natural_desaster']], on='childid')

tmp = Data_constr_oc_r1[['childid','shfam12','shfam13']].copy()
for c in ['shfam12','shfam13']:
    tmp[c].replace(yesno_dict, inplace=True)
tmp['health_death_shock'] = tmp[['shfam12','shfam13']].sum(axis=1)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1, tmp[['childid','health_death_shock']], on='childid')

tmp = Data_constr_oc_r1[['childid','shfam7']].copy()
tmp['shfam7'].replace(yesno_dict, inplace=True)
tmp.rename(columns={'shfam7':'negative_incidents'}, inplace=True)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1, tmp[['childid','negative_incidents']], on='childid')

tmp = Data_constr_oc_r1[['childid','shfam14']].copy()
tmp['shfam14'].replace(yesno_dict, inplace=True)
tmp.rename(columns={'shfam14':'migration_shock'}, inplace=True)
Expl_shocks_r1 = pd.merge(Expl_shocks_r1, tmp[['childid','migration_shock']], on='childid')

for c in ['theft_of_property','victim_of_crime','changes_econ_cond_endo',
          'natural_desaster','health_death_shock','negative_incidents','migration_shock']:
    Expl_shocks_r1[c] = pd.to_numeric(Expl_shocks_r1[c], errors='coerce')

# --- Economic status ---
Expl_econ_status_r1 = pd.merge(
    Data_constr_oc_r1[['childid','ownlandhse']], Data_r1[['childid','ownhouse']], on='childid')
Expl_econ_status_r1['ownlandhse'] = pd.to_numeric(Expl_econ_status_r1['ownlandhse'].replace(yesno_dict), errors='coerce')
Expl_econ_status_r1['ownhouse']   = pd.to_numeric(Expl_econ_status_r1['ownhouse'].replace(yesno_dict), errors='coerce')
Expl_econ_status_r1['own_house_or_land'] = Expl_econ_status_r1[['ownlandhse','ownhouse']].mean(axis=1).round(2)
Expl_econ_status_r1 = Expl_econ_status_r1[['childid','own_house_or_land']]

# --- Caregiver ---
Expl_caregiver_r1 = pd.merge(
    Data_constr_oc_r1[['childid','momage','momedu','dadage','dadedu']],
    Data_r1[['childid','daddead','join','authorit','seemom','seedad','schtyp','namewrk','chores']],
    on='childid')
Expl_caregiver_r1['momedu'].replace(education_dict, inplace=True)
Expl_caregiver_r1['dadedu'].replace(education_dict, inplace=True)
Expl_caregiver_r1['daddead'].replace(daddead_dict, inplace=True)
Expl_caregiver_r1['join'].replace(yesno_dict, inplace=True)
Expl_caregiver_r1['authorit'].replace(yesno_dict, inplace=True)
Expl_caregiver_r1['seemom'].replace(seemom_dict, inplace=True)
Expl_caregiver_r1['seedad'].replace(seedad_dict, inplace=True)
Expl_caregiver_r1['schtyp'].replace(schtyp_dict, inplace=True)
Expl_caregiver_r1['namewrk'].replace(yesno_dict, inplace=True)
Expl_caregiver_r1['chores'].replace(yesno_dict, inplace=True)

# --- Sex ---
Expl_sex = Data_r1[['childid','sex']].copy()
Expl_sex['sex'].replace(sex_dict, inplace=True)

# --- Community ---
comm_cols = ['commid','pop','twndis','waste','airpol','watpol','contsoil','legal','conclive',
             'thfcrm','violcrm','yuthcrm','proscrm','comcrm','speccrm',
             'water1','water2','water3','water4',
             'garb1','garb2','garb3','garb4',
             'road1','road2','road3','road4',
             'comgrp1','comgrp2','comgrp3','comgrp4','comgrp5','comgrp6','comgrp7','comgrp8']
avail_comm = [c for c in comm_cols if c in Data_community_r1.columns]
Expl_community_r1 = Data_community_r1[avail_comm].copy()
for c in avail_comm:
    Expl_community_r1[c].replace(notatall_to_serious_problem_dict, inplace=True)
    Expl_community_r1[c].replace(yesno_dict, inplace=True)
    Expl_community_r1[c].replace(dontknow_notmentioned_dict, inplace=True)

crime_cols = [c for c in ['thfcrm','violcrm','yuthcrm','proscrm','comcrm','speccrm'] if c in Expl_community_r1.columns]
if crime_cols:
    Expl_community_r1['safety'] = Expl_community_r1[crime_cols].sum(axis=1)
    Expl_community_r1.drop(crime_cols, axis=1, inplace=True)

grp_cols = [c for c in ['comgrp1','comgrp2','comgrp3','comgrp4','comgrp5','comgrp6','comgrp7','comgrp8'] if c in Expl_community_r1.columns]
if grp_cols:
    Expl_community_r1['comm_groups'] = Expl_community_r1[grp_cols].sum(axis=1)
    Expl_community_r1.drop(grp_cols, axis=1, inplace=True)

garb_cols = [c for c in ['garb1','garb2','garb3','garb4'] if c in Expl_community_r1.columns]
if garb_cols:
    Expl_community_r1['garbage_taken_by_truck'] = (Expl_community_r1.get('garb1', 0) == 1).astype(int)
    Expl_community_r1.drop(garb_cols, axis=1, inplace=True)

road_cols = [c for c in ['road1','road2','road3','road4'] if c in Expl_community_r1.columns]
if road_cols:
    Expl_community_r1['paved_roads_in_community'] = (Expl_community_r1.get('road1', 0) == 1).astype(int)
    Expl_community_r1.drop(road_cols, axis=1, inplace=True)

water_cols = [c for c in ['water1','water2','water3','water4'] if c in Expl_community_r1.columns]
if water_cols:
    w1 = Expl_community_r1.get('water1', pd.Series(0, index=Expl_community_r1.index))
    w2 = Expl_community_r1.get('water2', pd.Series(0, index=Expl_community_r1.index))
    w3 = Expl_community_r1.get('water3', pd.Series(0, index=Expl_community_r1.index))
    Expl_community_r1['drinking_water_from_public_or_private_well'] = (
        (w1 == 1) | (w2 == 1) | (w3 == 1)).astype(int)
    Expl_community_r1.drop(water_cols, axis=1, inplace=True)

for c in Expl_community_r1.columns:
    if c != 'commid':
        Expl_community_r1[c] = pd.to_numeric(Expl_community_r1[c], errors='coerce')

Expl_community_r1['commid'] = Expl_community_r1['commid'].astype(str).str.lower()

print("Feature engineering done.")

# ─────────────────────────────────────────────────────────────────────────────
# Merge all features into Data_comb_input_r1
# ─────────────────────────────────────────────────────────────────────────────
constr_feats = ['childid','hq','sv','cd','zbfa','zhfa','living_standard']
avail_constr = [c for c in constr_feats if c in Data_constr_oc_r1.columns]

dfs_to_merge = [
    Expl_health_r1,
    Expl_schooling_r1,
    Expl_nutrition_r1,
    Expl_hh_char_r1,
    Expl_shocks_r1,
    Expl_econ_status_r1,
    Expl_caregiver_r1,
    Expl_sex,
    Data_constr_oc_r1[avail_constr],
]

Data_comb_input_r1 = reduce(lambda L, R: pd.merge(L, R, on='childid'), dfs_to_merge)
r1_commid = Data_r1[['childid','commid']].copy()
r1_commid['commid'] = r1_commid['commid'].astype(str).str.lower()
Data_comb_input_r1 = pd.merge(Data_comb_input_r1, r1_commid, on='childid')
Data_comb_input_r1 = pd.merge(Data_comb_input_r1, Expl_community_r1, on='commid')

# Standardize numeric columns (matching original pipeline)
numeric_cols = Data_comb_input_r1.select_dtypes(include='number').columns.tolist()
scaler_std = StandardScaler()
Data_comb_input_r1[numeric_cols] = scaler_std.fit_transform(Data_comb_input_r1[numeric_cols])

# Build task-specific datasets
Data_comb_oc_r1_income = pd.merge(Data_comb_input_r1, Data_income_comb, on='childid')
Data_comb_oc_r1_mental = pd.merge(Data_comb_input_r1, Data_mental_health_comb, on='childid')

print(f"Data_comb_oc_r1_income shape: {Data_comb_oc_r1_income.shape}")
print(f"Data_comb_oc_r1_mental shape: {Data_comb_oc_r1_mental.shape}")

# ─────────────────────────────────────────────────────────────────────────────
# VIF computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_vif(X, task_name, continuous_threshold=5):
    """Compute VIF for numeric features with >continuous_threshold unique values."""
    # Numeric columns only
    X_num = X.select_dtypes(include=[np.number])
    # Keep only continuous-ish columns
    cont_cols = [c for c in X_num.columns if X_num[c].nunique() > continuous_threshold]
    X_cont = X_num[cont_cols].copy()
    # Impute any residual NaNs with median
    X_cont = X_cont.fillna(X_cont.median())
    # Drop constant columns
    X_cont = X_cont.loc[:, X_cont.std() > 0]
    # Drop columns still all-NaN after imputation
    X_cont = X_cont.dropna(axis=1, how='all')

    print(f"\nComputing VIF for {task_name}  ({X_cont.shape[1]} continuous features, {len(X_cont)} observations)...")

    vif_values = []
    for i in range(X_cont.shape[1]):
        try:
            v = variance_inflation_factor(X_cont.values.astype(float), i)
        except Exception:
            v = np.nan
        vif_values.append(v)

    vif_df = pd.DataFrame({'Feature': X_cont.columns, 'VIF': vif_values})
    vif_df = vif_df.sort_values('VIF', ascending=False).reset_index(drop=True)
    return vif_df


# Get the feature columns (exclude target, childid, commid)
exclude_income = set(target_vars_list_income) | {'childid','commid'}
exclude_mental = set(target_vars_list_mental) | {'childid','commid'}

X_income = Data_comb_oc_r1_income.loc[:, ~Data_comb_oc_r1_income.columns.isin(exclude_income)].copy()
X_mental = Data_comb_oc_r1_mental.loc[:, ~Data_comb_oc_r1_mental.columns.isin(exclude_mental)].copy()

vif_income = compute_vif(X_income, "Income task")
vif_mental = compute_vif(X_mental, "Mental health task")

# ─────────────────────────────────────────────────────────────────────────────
# Results
# ─────────────────────────────────────────────────────────────────────────────
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', '{:.2f}'.format)

# ─────────────────────────────────────────────────────────────────────────────
# Apply human-readable labels (from SHAP plots in the paper)
# ─────────────────────────────────────────────────────────────────────────────
label_map = {
    'zbfa':         'BMI for age',
    'zhfa':         'Height for age',
    'hq':           'House quality',
    'cd':           'Consumer durable index',
    'pop':          'Community population',
    'safety':       'Community crime level',
    'literacy':     'Literacy',
    'momedu':       "Education of child's mother",
    'dadedu':       "Education of child's father",
    'comm_groups':  'Number of community groups',
    'momage':       "Mother's age",
    'dadage':       "Father's age",
    'hhsize':       'Household size',
    'childs_alive': 'Proportion of children alive',
}

for df in [vif_income, vif_mental]:
    df['Feature'] = df['Feature'].map(lambda x: label_map.get(x, x))

print("\n" + "="*60)
print("VIF RESULTS — INCOME TASK (labelled)")
print("="*60)
print(vif_income.to_string(index=False))

print("\n" + "="*60)
print("VIF RESULTS — MENTAL HEALTH TASK (labelled)")
print("="*60)
print(vif_mental.to_string(index=False))

# Save to CSV
os.makedirs('VIF_results', exist_ok=True)
vif_income.to_csv('VIF_results/vif_income.csv', index=False)
vif_mental.to_csv('VIF_results/vif_mental.csv', index=False)
print("\nResults saved to VIF_results/vif_income.csv and VIF_results/vif_mental.csv")
