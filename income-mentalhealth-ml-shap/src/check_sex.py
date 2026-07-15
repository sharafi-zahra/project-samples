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

base_ids = set(mod.Data_comb_base['childid'].unique())
sl = mod.sex_lookup[mod.sex_lookup['childid'].isin(base_ids)].copy()
n = len(sl)
n_female = int((sl['sex'] == 1).sum())
pct = n_female / n * 100
print(f"Base N = {n}")
print(f"Female = {n_female}  ({pct:.1f}%)")
print(f"Male   = {n - n_female}  ({100-pct:.1f}%)")
