# -*- coding: utf-8 -*-
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

import pandas as pd, numpy as np

ids  = set(mod.Data_comb_base['childid'])
r1   = mod.Data_r1
c1   = mod.Data_constr_oc_r1
sl   = mod.sex_lookup

def ms(col, df):
    v = pd.to_numeric(df.loc[df['childid'].isin(ids), col], errors='coerce').dropna()
    return v.mean(), v.std(), len(v)

# sex
s = sl[sl['childid'].isin(ids)]
male_mean = float((s['sex'] == 0).sum()) / len(s)
pct_female = (1 - male_mean) * 100

# household (from constr r1)
hhsize   = ms('hhsize',   c1)
momage   = ms('momage',   c1)
dadage   = ms('dadage',   c1)
chdborn  = ms('chdborn',  r1)
chdalive = ms('chdalive', r1)

# schooling (from constr r1)
levlread = ms('levlread', c1)
levlwrit = ms('levlwrit', c1)

# anthropometric (from constr r1)
bmi = ms('fbfa', c1)
hgt = ms('fhfa', c1)

def fmt(t):
    return f"{t[0]:.3f}  ({t[1]:.3f})  n={t[2]}"

print(f"\nN = {len(ids)}")
print(f"Gender (1=male) mean = {male_mean:.3f}   Female = {pct_female:.1f}%")
print(f"Household size:           {fmt(hhsize)}")
print(f"Mother's age:             {fmt(momage)}")
print(f"Father's age:             {fmt(dadage)}")
print(f"Children born:            {fmt(chdborn)}")
print(f"Children surviving:       {fmt(chdalive)}")
print(f"Reading skill (levlread): {fmt(levlread)}")
print(f"Writing skill (levlwrit): {fmt(levlwrit)}")
print(f"BMI-for-age z-score:      {fmt(bmi)}")
print(f"Height-for-age z-score:   {fmt(hgt)}")
