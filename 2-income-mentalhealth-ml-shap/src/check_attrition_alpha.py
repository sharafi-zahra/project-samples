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

# ── Attrition ─────────────────────────────────────────────────────────────────
r1_ids   = set(mod.Data_r1['childid'].unique())
r5_ids   = set(mod.Data_r5['childcode'].unique())
retained = r1_ids & r5_ids
N_R1  = len(r1_ids)
N_R5  = len(retained)
pct   = N_R5 / N_R1 * 100
print(f"\nAttrition:")
print(f"  N Round 1 (older cohort): {N_R1}")
print(f"  N Round 5 (retained):     {N_R5}  ({pct:.1f}%)")
print(f"  Analytical sample (base): {len(mod.Data_comb_base)}")

# ── Cronbach's alpha ──────────────────────────────────────────────────────────
# mod.Data_r5 has already been processed and inverted by the exec
mental_vars = ['feay05r5','feay20r5','feay28r5','cdprssr5',
               'cemstbr5','crelaxr5','cwryltr5','cgtnrvr5']

r5  = mod.Data_r5.copy()
mh  = r5[['childcode'] + mental_vars].copy()
for c in mental_vars:
    mh[c] = pd.to_numeric(mh[c], errors='coerce')
mh  = mh.dropna(subset=mental_vars)

items     = mh[mental_vars].values.astype(float)
k         = items.shape[1]
item_vars = items.var(axis=0, ddof=1)
total_var = items.sum(axis=1).var(ddof=1)
alpha     = (k / (k - 1)) * (1 - item_vars.sum() / total_var)

np.random.seed(42)
alphas_boot = []
for _ in range(2000):
    samp = items[np.random.choice(len(items), len(items), replace=True)]
    iv   = samp.var(axis=0, ddof=1)
    tv   = samp.sum(axis=1).var(ddof=1)
    alphas_boot.append((k / (k - 1)) * (1 - iv.sum() / tv))
ci_lb = np.percentile(alphas_boot, 2.5)
ci_ub = np.percentile(alphas_boot, 97.5)

label = ("excellent" if alpha >= 0.9 else "good" if alpha >= 0.8
         else "acceptable" if alpha >= 0.7 else "questionable" if alpha >= 0.6
         else "poor")

print(f"\nCronbach's alpha (n={len(mh)}, k={k} items):")
print(f"  alpha = {alpha:.3f}")
print(f"  95% CI: {ci_lb:.3f} - {ci_ub:.3f}")
print(f"  Reliability: {label}")

# item-level stats for sanity check
print("\nItem means (should all be 1-5 scale):")
for c in mental_vars:
    print(f"  {c}: mean={mh[c].mean():.2f} sd={mh[c].std():.2f} n={mh[c].notna().sum()}")
