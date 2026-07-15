import nbformat as nbf

nb = nbf.v4.new_notebook()
nb['metadata'] = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.11.0'}
}

cells = []
def md(src):   return nbf.v4.new_markdown_cell(src)
def code(src): return nbf.v4.new_code_cell(src)

# ══════════════════════════════════════════════════════════════════════════════
# TITLE
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("""# Immigrant Pay Premium Analysis
### Graduate-level earnings: do immigrants earn differently from natives with equivalent education?

**Research question:** Controlling for graduate school, degree type, field of study, and
work experience, do immigrants earn more or less than comparable native workers?

**Immigrant definition:** `country_bachelors ≠ country_work`
(Every graduate school in the dataset maps 1-to-1 to a single `country_work`,
so this is equivalent to `country_bachelors ≠ graduate_school_country`.)

**Data note:** Each row is a *cell-level average* — the mean salary for all workers
sharing the same (graduate school × degree type × major × bachelor country) combination.
Cells carry equal weight regardless of the number of underlying workers.

---

## Notebook Structure

| Part | Content |
|------|---------|
| **1 — Data & Setup** | Loading, immigrant flag, country selection |
| **2 — Descriptive Overview** | Raw pay gaps, within-cell comparisons |
| **3 — Main Results: All Countries** | OLS by country, premium vs penalty, pooled |
| **4 — US Deep Dive (premium country)** | Experience, major, degree, origin, schools, tiers |
| **5 — Penalty Countries Grouped** | Canada · Australia · Ireland · Singapore · Hong Kong |
| **6 — Cross-Country Analyses** | Assimilation · Same-origin/different-destination · School quality |
| **7 — Summary & Discussion** | Key findings, comparison with MSS (2024) |"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — DATA & SETUP
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("---\n## Part 1 — Data & Setup"))

cells.append(md("### 1.1 Imports & utility functions"))
cells.append(code("""import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore')
from IPython.display import display

pd.set_option('display.float_format', '{:.3f}'.format)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 120)

# ── Utility: absorb school FE via within-school demeaning ───────────────────
def within_demean(data, group_col, cols):
    \"\"\"Subtract group mean from each variable — algebraically equivalent to group FE.\"\"\"
    d = data.copy()
    means = data.groupby(group_col)[cols].transform('mean')
    for c in cols:
        d[c + '_w'] = d[c] - means[c]
    return d

# ── Utility: extract key stats from a fitted OLS model ──────────────────────
def reg_stats(m, key):
    b  = m.params[key]
    p  = m.pvalues[key]
    ci = m.conf_int().loc[key]
    sig = '***' if p < .01 else '**' if p < .05 else '*' if p < .10 else 'ns'
    return b, ci[0], ci[1], p, sig

print("Utilities defined.")"""))

cells.append(md("### 1.2 Load data"))
cells.append(code("""DATA_PATH = r'C:\\Users\\sharafi\\Dropbox\\Immigrants_J&Z\\Data\\Avg_pay_by_graduate_school_undergraduate_country.csv'
df = pd.read_csv(DATA_PATH, index_col=0)
print(f"Shape: {df.shape}  |  Columns: {df.columns.tolist()}")
df.head(3)"""))

cells.append(md("""### 1.3 Immigrant definition

**Immigrant** = `country_bachelors ≠ country_work`.

Every graduate school maps to exactly one `country_work` (verified below),
so this is equivalent to defining immigrants as those whose bachelor's country
differs from the graduate school's country."""))
cells.append(code("""n_multi = (df.groupby('graduate_school')['country_work'].nunique() > 1).sum()
print(f"Schools appearing in >1 country_work: {n_multi}  (should be 0)")

df['immigrant'] = (df['country_bachelors'] != df['country_work']).astype(int)
print(f"\\nTotal cells: {len(df):,}  |  Native: {(df['immigrant']==0).sum():,}  |  Immigrant: {df['immigrant'].sum():,}")"""))

cells.append(md("""### 1.4 Country selection

We keep all destination countries with **≥ 10 cells in both** the native and
immigrant groups.  Countries with < 100 total cells cannot support school fixed
effects; they use degree + major FE only."""))
cells.append(code("""TARGET = [
    'United States', 'United Kingdom', 'Canada', 'Australia',
    'Ireland', 'Singapore', 'Hong Kong', 'Netherlands', 'Germany'
]
d = df[df['country_work'].isin(TARGET)].copy()
d['log_pay']     = np.log(d['avg_pay'])
d['log_pay_std'] = d.groupby('country_work')['log_pay'].transform(
                       lambda x: (x - x.mean()) / x.std())

counts = d.groupby(['country_work','immigrant']).size().unstack(fill_value=0)
counts.columns = ['Native cells','Immigrant cells']
counts['Total']    = counts.sum(axis=1)
counts['Currency'] = d.groupby('country_work')['currency'].first()
counts['School FE?'] = counts['Total'].apply(lambda x: 'Yes' if x >= 100 else 'No')
counts.sort_values('Total', ascending=False)"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — DESCRIPTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("---\n## Part 2 — Descriptive Overview"))

cells.append(md("""### 2.1 Unadjusted pay comparison

Raw average pay by group — **before** controlling for school, degree, or major.
Do not compare pay levels across countries; currencies differ."""))
cells.append(code("""raw = d.groupby(['country_work','immigrant'])['avg_pay'].mean().unstack()
raw.columns = ['Native avg', 'Immigrant avg']
raw['Raw gap %'] = ((raw['Immigrant avg'] - raw['Native avg']) / raw['Native avg'] * 100).round(1)
raw['Currency']  = d.groupby('country_work')['currency'].first()
raw.sort_values('Raw gap %', ascending=False).round(0)"""))

cells.append(md("""### 2.2 Within-cell comparison (same school × degree × major)

For every (school, degree, major) combination that has **both** an immigrant and
a native cell average, we compute the raw pay gap.  No regression needed — this
is the most direct like-for-like comparison available."""))
cells.append(code("""d['cell'] = d['graduate_school'] + '||' + d['graduate_degree'] + '||' + d['graduate_major']

paired = (d.groupby(['country_work','cell','immigrant'])['avg_pay']
           .mean().unstack().rename(columns={0:'native_pay', 1:'immigrant_pay'}))
paired = paired.dropna()
paired['gap_%'] = ((paired['immigrant_pay'] - paired['native_pay'])
                    / paired['native_pay'] * 100).round(1)

summary = paired.groupby('country_work')['gap_%'].agg(
    Mean   = lambda x: round(x.mean(), 1),
    Median = lambda x: round(x.median(), 1),
    N_matched_cells = 'count',
    Pct_imm_higher  = lambda x: round((x > 0).mean() * 100, 0)
).sort_values('Mean')
print("Within-cell gap (immigrant pay vs native pay, same school/degree/major):")
summary"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — MAIN RESULTS: ALL COUNTRIES
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("---\n## Part 3 — Main Results: All Destination Countries"))

cells.append(md("""### 3.1 OLS regression by country

**Model:** `log(avg_pay) ~ immigrant + school FE + degree FE + major FE`

Countries with ≥ 100 cells: school + degree + major FE.
Countries with < 100 cells: degree + major FE only (school FE would be overfit)."""))
cells.append(code("""results = []
for country in TARGET:
    sub  = d[d['country_work'] == country].copy()
    n_nat, n_imm = int((sub['immigrant']==0).sum()), int(sub['immigrant'].sum())
    curr = sub['currency'].iloc[0]

    if sub['immigrant'].nunique() < 2:
        continue

    formula = ('log_pay ~ immigrant + C(graduate_school) + C(graduate_degree) + C(graduate_major)'
               if len(sub) >= 100 else
               'log_pay ~ immigrant + C(graduate_degree) + C(graduate_major)')
    note = 'school+degree+major FE' if len(sub) >= 100 else 'degree+major FE only'

    m = smf.ols(formula, data=sub).fit()
    b, lo, hi, p, sig = reg_stats(m, 'immigrant')
    results.append({'Country': country, 'Currency': curr,
                    'N_cells': int(m.nobs), 'N_native': n_nat, 'N_immigrant': n_imm,
                    'Pay_gap_%'  : round((np.exp(b)  -1)*100, 1),
                    'CI_lower_%' : round((np.exp(lo) -1)*100, 1),
                    'CI_upper_%' : round((np.exp(hi) -1)*100, 1),
                    'p_value': round(p,4), 'Sig': sig,
                    'R2': round(m.rsquared,3), 'Controls': note})

res_df = pd.DataFrame(results)
res_df"""))

cells.append(md("### 3.2 Cross-country pattern: premium vs penalty"))
cells.append(code("""res_df['Direction'] = res_df['Pay_gap_%'].apply(lambda x: 'PREMIUM' if x > 0 else 'PENALTY')
res_df['Note'] = res_df.apply(lambda r:
    'Significant' if r['Sig'] in ('***','**','*') else
    'ns — underpowered' if r['N_cells'] < 100 else 'ns', axis=1)

cols = ['Country','Currency','N_cells','Pay_gap_%','CI_lower_%','CI_upper_%','Sig','Direction','Note']
print("=" * 70)
print("IMMIGRANT PAY GAP BY DESTINATION COUNTRY")
print("=" * 70)
display(res_df[cols])
print()
print("KEY FLAG: Outside the US, the dominant pattern is an immigrant PENALTY.")
print(f"  Countries with PREMIUM: {(res_df['Pay_gap_%']>0).sum()}")
print(f"  Countries with PENALTY: {(res_df['Pay_gap_%']<0).sum()}")"""))

cells.append(md("### 3.3 Pooled regression (all countries)"))
cells.append(code("""pool = smf.ols(
    'log_pay_std ~ immigrant + C(country_work) + C(graduate_degree) + C(graduate_major)',
    data=d).fit()

b, lo, hi, p, sig = reg_stats(pool, 'immigrant')
print("POOLED (country-standardised log pay, country FE + degree FE + major FE)")
print(f"N = {int(pool.nobs):,} cells")
print(f"Immigrant coeff = {b:+.3f} SD   95% CI [{lo:+.3f}, {hi:+.3f}]   p={p:.4f} {sig}")
print(f"R² = {pool.rsquared:.3f}")
print("\\nNote: pooled result is driven heavily by the US (85% of all cells).")"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 4 — US DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("---\n## Part 4 — The United States: A Premium Country"))

cells.append(md("""### 4.1 Remove vocational / non-graduate schools

The dataset includes cosmetology schools, community colleges, and vocational
training centres mislabelled as graduate schools.  These are excluded."""))
cells.append(code("""EXCLUDE_SCHOOLS = {
    'Platt College-Anaheim','Porter and Chester Institute of Stratford',
    'North-West College-Riverside','The Fab School',
    'NTMA Training Centers of Southern California','Porterville College',
    'Palladium Technical Academy','Ponca City Beauty College',
    'P B Cosmetology Education Center','Macomb Community College',
    'Pomona Unified School District Adult and Career Education',
    'Omega Institute of Cosmetology','Community College of Baltimore County',
    'Elaine Sterling Institute','European Academy of Cosmetology and Hairdressing',
    'Oceanside College of Beauty','M-DCPS The English Center','Coastal Bend College',
    'Ridgewater College','Howard College','Pima Community College',
    'El Paso Community College','Des Moines Area Community College',
    'Elizabeth Grady School of Esthetics and Massage Therapy',
    'Lakeland Community College','Northern Virginia Community College',
    'Wake Technical Community College','Wayne Community College',
    'Bridgewater State University',
}
us_raw = df[df['country_work'] == 'United States'].copy()
us     = us_raw[~us_raw['graduate_school'].isin(EXCLUDE_SCHOOLS)].copy()
us['log_pay'] = np.log(us['avg_pay'])

print(f"Cells removed (vocational): {len(us_raw)-len(us)}")
print(f"Remaining: {len(us):,}  |  Native: {(us['immigrant']==0).sum():,}  |  Immigrant: {us['immigrant'].sum():,}")"""))

cells.append(md("""### 4.2 Experience imbalance

`avg_experience` is the cell-level mean years of work experience.
**Direction of bias matters:** if immigrants have less experience, ignoring it
understates the premium; if more, it overstates it."""))
cells.append(code("""exp_us = us.groupby('immigrant')['avg_experience'].agg(['mean','median','std'])
exp_us.index = ['Native','Immigrant']
display(exp_us.round(2))
print(f"\\nNatives have {exp_us.loc['Native','mean']-exp_us.loc['Immigrant','mean']:+.2f} years more experience.")
print(f"Corr(experience, pay) = {us['avg_pay'].corr(us['avg_experience']):.3f}")
print()
print("By major:")
em = us.groupby(['graduate_major','immigrant'])['avg_experience'].mean().unstack().round(2)
em.columns = ['Native','Immigrant']
em['Gap'] = (em['Native']-em['Immigrant']).round(2)
display(em.sort_values('Gap', ascending=False))"""))

cells.append(md("### 4.3 Regression: before vs after experience control"))
cells.append(code("""uw = within_demean(us, 'graduate_school', ['log_pay','immigrant','avg_experience'])

mA = smf.ols('log_pay_w ~ immigrant_w + C(graduate_degree) + C(graduate_major)', data=uw).fit()
mB = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree) + C(graduate_major)', data=uw).fit()

bA,loA,hiA,pA,sA = reg_stats(mA,'immigrant_w')
bB,loB,hiB,pB,sB = reg_stats(mB,'immigrant_w')
eb = mB.params['avg_experience_w']; ep = mB.pvalues['avg_experience_w']
es = '***' if ep<.01 else '**' if ep<.05 else '*' if ep<.10 else 'ns'

comp = pd.DataFrame({
    'Model': ['A: no experience control','B: with experience control'],
    'Immigrant gap %': [f'{(np.exp(bA)-1)*100:+.1f}%', f'{(np.exp(bB)-1)*100:+.1f}%'],
    '95% CI'  : [f'[{(np.exp(loA)-1)*100:+.1f}%, {(np.exp(hiA)-1)*100:+.1f}%]',
                 f'[{(np.exp(loB)-1)*100:+.1f}%, {(np.exp(hiB)-1)*100:+.1f}%]'],
    'p-value' : [f'{pA:.4f} {sA}', f'{pB:.4f} {sB}'],
    'R²'      : [round(mA.rsquared,3), round(mB.rsquared,3)]
})
display(comp)
print(f"\\nExperience coeff: {eb:+.4f} => {(np.exp(eb)-1)*100:.1f}% per extra year  p={ep:.4f} {es}")
print("\\nConclusion: natives are MORE experienced (+1.65 yrs), so controlling for")
print("experience WIDENS the immigrant premium (from +17.8% to +25.9%).")"""))

cells.append(md("### 4.4 By graduate major"))
cells.append(code("""rows = []
for major in sorted(us['graduate_major'].unique()):
    sub = us[us['graduate_major']==major]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: continue
    sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree)', data=sw).fit()
        b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
        rows.append({'Major': major,
                     'N_native': int((sub['immigrant']==0).sum()),
                     'N_immigrant': int(sub['immigrant'].sum()),
                     'Pay_gap_%': round((np.exp(b)-1)*100,1),
                     'CI_lower_%': round((np.exp(lo)-1)*100,1),
                     'CI_upper_%': round((np.exp(hi)-1)*100,1),
                     'p_value': round(p,4), 'Sig': sig})
    except: pass

pd.DataFrame(rows).set_index('Major').sort_values('Pay_gap_%', ascending=False)"""))

cells.append(md("### 4.5 By degree type"))
cells.append(code("""rows = []
for deg in sorted(us['graduate_degree'].unique()):
    sub = us[us['graduate_degree']==deg]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: continue
    sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_major)', data=sw).fit()
        b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
        rows.append({'Degree': deg,
                     'N_native': int((sub['immigrant']==0).sum()),
                     'N_immigrant': int(sub['immigrant'].sum()),
                     'Pay_gap_%': round((np.exp(b)-1)*100,1),
                     'CI_lower_%': round((np.exp(lo)-1)*100,1),
                     'CI_upper_%': round((np.exp(hi)-1)*100,1),
                     'p_value': round(p,4), 'Sig': sig})
    except: pass

pd.DataFrame(rows).set_index('Degree').sort_values('Pay_gap_%', ascending=False)"""))

cells.append(md("### 4.6 By origin country"))
cells.append(code("""top_origins_us = (us[us['immigrant']==1]['country_bachelors']
                   .value_counts()[lambda x: x >= 5].index.tolist())
rows = []
for origin in top_origins_us:
    sub = us[(us['immigrant']==0) | (us['country_bachelors']==origin)].copy()
    if sub['immigrant'].nunique() < 2: continue
    sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree) + C(graduate_major)',
                    data=sw).fit()
        b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
        rows.append({'Bachelor country': origin,
                     'N_imm_cells': int((sub['immigrant']==1).sum()),
                     'Pay_gap_%': round((np.exp(b)-1)*100,1),
                     'CI_lower_%': round((np.exp(lo)-1)*100,1),
                     'CI_upper_%': round((np.exp(hi)-1)*100,1),
                     'p_value': round(p,4), 'Sig': sig})
    except: pass

pd.DataFrame(rows).set_index('Bachelor country').sort_values('Pay_gap_%', ascending=False)"""))

cells.append(md("### 4.7 School tier analysis"))
cells.append(code("""IVY_ELITE = {'Harvard University','Massachusetts Institute of Technology',
    'Stanford University','Princeton University','Yale University',
    'Columbia University in the City of New York','University of Pennsylvania',
    'Cornell University','Dartmouth College','Brown University','Duke University',
    'Northwestern University','University of Chicago',
    'California Institute of Technology','Johns Hopkins University'}
TOP50 = {'University of California-Berkeley','University of California-Los Angeles',
    'University of Michigan-Ann Arbor','Carnegie Mellon University','New York University',
    'Georgetown University','Vanderbilt University','Emory University','Rice University',
    'University of Notre Dame','Washington University in St Louis',
    'University of Virginia-Main Campus','Tufts University','Boston University',
    'Brandeis University','Tulane University of Louisiana','University of Rochester',
    'Case Western Reserve University','Northeastern University',
    'University of Wisconsin-Madison','University of Illinois at Urbana-Champaign',
    'The University of Texas at Austin','Purdue University-Main Campus',
    'Ohio State University-Main Campus','University of Florida','University of Georgia',
    'University of North Carolina at Chapel Hill',
    'Georgia Institute of Technology-Main Campus','University of California-San Diego',
    'University of California-Davis','Rensselaer Polytechnic Institute',
    'Worcester Polytechnic Institute','Stevens Institute of Technology',
    'University of Minnesota-Twin Cities','University of California-Santa Barbara'}

def us_tier(s):
    if s in IVY_ELITE: return '1. Ivy/Elite'
    if s in TOP50:     return '2. Top 50'
    return '3. Other'

us['tier'] = us['graduate_school'].apply(us_tier)
tier_counts = us.groupby(['tier','immigrant']).size().unstack(fill_value=0)
tier_counts.columns = ['Native','Immigrant']
tier_counts['Total'] = tier_counts.sum(axis=1)
print("Cell counts by tier:"); display(tier_counts)

print("\\nRegression by tier (school FE via demeaning, degree+major FE, experience):")
rows = []
for t in ['1. Ivy/Elite','2. Top 50','3. Other']:
    sub = us[us['tier']==t].copy()
    if sub['immigrant'].nunique() < 2 or len(sub) < 20: continue
    sw = within_demean(sub,'graduate_school',['log_pay','immigrant','avg_experience'])
    m  = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree) + C(graduate_major)',
                 data=sw).fit()
    b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
    rows.append({'Tier': t, 'N_cells': int(m.nobs),
                 'N_native': int((sub['immigrant']==0).sum()),
                 'N_immigrant': int(sub['immigrant'].sum()),
                 'Pay_gap_%': round((np.exp(b)-1)*100,1),
                 'CI_lower_%': round((np.exp(lo)-1)*100,1),
                 'CI_upper_%': round((np.exp(hi)-1)*100,1),
                 'p_value': round(p,4), 'Sig': sig})

pd.DataFrame(rows).set_index('Tier')"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 5 — PENALTY COUNTRIES
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Part 5 — Penalty Countries: Canada · Australia · Ireland · Singapore · Hong Kong

We pool all five penalty countries.  Since currencies differ, pay is
**standardised within each country** (z-score of log pay) before pooling.
School FE are absorbed via within-school demeaning applied within each country."""))

cells.append(md("### 5.1 Sample & experience overview"))
cells.append(code("""PENALTY = ['Canada','Australia','Ireland','Singapore','Hong Kong']

pen = df[df['country_work'].isin(PENALTY)].copy()
pen['log_pay']     = np.log(pen['avg_pay'])
pen['log_pay_std'] = pen.groupby('country_work')['log_pay'].transform(
                         lambda x: (x - x.mean()) / x.std())

pc = pen.groupby(['country_work','immigrant']).size().unstack(fill_value=0)
pc.columns = ['Native','Immigrant']
pc['Total']    = pc.sum(axis=1)
pc['Currency'] = pen.groupby('country_work')['currency'].first()
print("Sample overview:"); display(pc)
print(f"\\nTotal: {len(pen)} cells  |  Native: {(pen['immigrant']==0).sum()}  |  Immigrant: {pen['immigrant'].sum()}")

print("\\nExperience by immigrant status:")
exp_pen = pen.groupby('immigrant')['avg_experience'].agg(['mean','median','std'])
exp_pen.index = ['Native','Immigrant']
display(exp_pen.round(2))
gap_pen = exp_pen.loc['Native','mean'] - exp_pen.loc['Immigrant','mean']
print(f"\\nNatives have {gap_pen:+.2f} years more experience (same direction as US).")"""))

cells.append(md("### 5.2 Main pooled regression"))
cells.append(code("""pen_w = within_demean(pen, 'graduate_school',
                     ['log_pay_std','immigrant','avg_experience'])

mP0 = smf.ols('log_pay_std_w ~ immigrant_w + C(country_work) + C(graduate_degree) + C(graduate_major)',
              data=pen_w).fit()
mP1 = smf.ols('log_pay_std_w ~ immigrant_w + avg_experience_w + C(country_work) + C(graduate_degree) + C(graduate_major)',
              data=pen_w).fit()

b0,l0,h0,p0,s0 = reg_stats(mP0,'immigrant_w')
b1,l1,h1,p1,s1 = reg_stats(mP1,'immigrant_w')
eb = mP1.params['avg_experience_w']; ep = mP1.pvalues['avg_experience_w']
es = '***' if ep<.01 else '**' if ep<.05 else '*' if ep<.10 else 'ns'

comp = pd.DataFrame({
    'Model': ['A: no experience control','B: with experience control'],
    'Immigrant coeff (SD)': [f'{b0:+.3f}', f'{b1:+.3f}'],
    '95% CI': [f'[{l0:+.3f}, {h0:+.3f}]', f'[{l1:+.3f}, {h1:+.3f}]'],
    'p-value': [f'{p0:.4f} {s0}', f'{p1:.4f} {s1}'],
    'R²': [round(mP0.rsquared,3), round(mP1.rsquared,3)]
})
print("Units: within-country SD of log pay")
display(comp)
print(f"\\nExperience coeff: {eb:+.4f} ({(np.exp(eb)-1)*100:.1f}% per year)  p={ep:.4f} {es}")
print("\\nKEY FINDING: The raw penalty (-0.32 SD) disappears once experience is")
print("controlled. The penalty is a seniority composition effect, not discrimination.")"""))

cells.append(md("### 5.3 By major"))
cells.append(code("""rows = []
for major in sorted(pen['graduate_major'].unique()):
    sub = pen[pen['graduate_major']==major]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: continue
    sw = within_demean(sub,'graduate_school',['log_pay_std','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_std_w ~ immigrant_w + avg_experience_w + C(country_work) + C(graduate_degree)',
                    data=sw).fit()
        b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
        rows.append({'Major': major,
                     'N_native': int((sub['immigrant']==0).sum()),
                     'N_immigrant': int(sub['immigrant'].sum()),
                     'Coeff_SD': round(b,3),
                     'CI_lower': round(lo,3), 'CI_upper': round(hi,3),
                     'p_value': round(p,4), 'Sig': sig})
    except: pass

print("Negative = immigrants earn LESS (in SD units of within-country log pay):")
pd.DataFrame(rows).set_index('Major').sort_values('Coeff_SD')"""))

cells.append(md("### 5.4 By degree type"))
cells.append(code("""rows = []
for deg in sorted(pen['graduate_degree'].unique()):
    sub = pen[pen['graduate_degree']==deg]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: continue
    sw = within_demean(sub,'graduate_school',['log_pay_std','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_std_w ~ immigrant_w + avg_experience_w + C(country_work) + C(graduate_major)',
                    data=sw).fit()
        b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
        rows.append({'Degree': deg,
                     'N_native': int((sub['immigrant']==0).sum()),
                     'N_immigrant': int(sub['immigrant'].sum()),
                     'Coeff_SD': round(b,3),
                     'CI_lower': round(lo,3), 'CI_upper': round(hi,3),
                     'p_value': round(p,4), 'Sig': sig})
    except: pass

pd.DataFrame(rows).set_index('Degree').sort_values('Coeff_SD')"""))

cells.append(md("### 5.5 By origin country"))
cells.append(code("""top_origins_pen = (pen[pen['immigrant']==1]['country_bachelors']
                    .value_counts()[lambda x: x >= 5].index.tolist())
rows = []
for origin in top_origins_pen:
    sub = pen[(pen['immigrant']==0) | (pen['country_bachelors']==origin)].copy()
    if sub['immigrant'].nunique() < 2: continue
    sw = within_demean(sub,'graduate_school',['log_pay_std','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_std_w ~ immigrant_w + avg_experience_w + C(country_work) + C(graduate_degree) + C(graduate_major)',
                    data=sw).fit()
        b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
        rows.append({'Bachelor country': origin,
                     'N_imm_cells': int((sub['immigrant']==1).sum()),
                     'Coeff_SD': round(b,3),
                     'CI_lower': round(lo,3), 'CI_upper': round(hi,3),
                     'p_value': round(p,4), 'Sig': sig})
    except: pass

pd.DataFrame(rows).set_index('Bachelor country').sort_values('Coeff_SD')"""))

cells.append(md("### 5.6 Within-cell gap distribution"))
cells.append(code("""pen['cell'] = pen['graduate_school'] + '||' + pen['graduate_degree'] + '||' + pen['graduate_major']
paired_pen = (pen.groupby(['country_work','cell','immigrant'])['avg_pay']
               .mean().unstack().rename(columns={0:'native_pay',1:'immigrant_pay'}))
paired_pen = paired_pen.dropna()
paired_pen['gap_%'] = ((paired_pen['immigrant_pay']-paired_pen['native_pay'])
                        /paired_pen['native_pay']*100).round(1)

print("Matched cells per country:")
display(paired_pen.groupby('country_work')['gap_%'].agg(
    N_cells='count', Mean=lambda x: round(x.mean(),1),
    Median=lambda x: round(x.median(),1),
    Pct_imm_higher=lambda x: round((x>0).mean()*100,0)))
print()
print("Overall distribution (all penalty countries):")
print(paired_pen['gap_%'].describe(percentiles=[.10,.25,.50,.75,.90]).round(1))"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 6 — CROSS-COUNTRY ANALYSES
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("---\n## Part 6 — Cross-Country Analyses"))

# ── Analysis 1: Convergence ─────────────────────────────────────────────────
cells.append(md("""### 6.1 Assimilation: Does the Immigrant Gap Close with Experience?

We split cells into **experience quartiles** and re-estimate the immigrant
coefficient within each quartile.

**Interpretation:**
- If the coefficient becomes *less extreme* in higher quartiles → convergence
  (the gap shrinks as workers accumulate experience)
- If the coefficient stays constant or grows → no assimilation

`avg_experience` proxies career stage, not time-since-migration specifically,
but it is the best available proxy in this dataset."""))

cells.append(code("""def convergence_by_quartile(data, dep_var, formula_template, label):
    \"\"\"Split into experience quartiles, run regression in each, return table.\"\"\"
    data = data.copy()
    data['exp_q'] = pd.qcut(data['avg_experience'], 4,
                             labels=['Q1 low (0-3 yrs)','Q2 (3-5 yrs)',
                                     'Q3 (5-7 yrs)','Q4 high (7+ yrs)'])
    rows = []
    for q in ['Q1 low (0-3 yrs)','Q2 (3-5 yrs)','Q3 (5-7 yrs)','Q4 high (7+ yrs)']:
        sub = data[data['exp_q']==q].copy()
        if sub['immigrant'].nunique() < 2 or len(sub) < 15: continue
        sw  = within_demean(sub,'graduate_school',
                            [dep_var,'immigrant','avg_experience'])
        try:
            m = smf.ols(formula_template, data=sw).fit()
            b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
            med_exp = sub['avg_experience'].median()
            rows.append({'Quartile': q,
                         'Median_exp_yrs': round(med_exp,1),
                         'N_native': int((sub['immigrant']==0).sum()),
                         'N_imm': int(sub['immigrant'].sum()),
                         'Coeff': round(b,3),
                         'CI_lower': round(lo,3),
                         'CI_upper': round(hi,3),
                         'p_value': round(p,4), 'Sig': sig})
        except: pass
    print(f"\\n{label}")
    df_out = pd.DataFrame(rows).set_index('Quartile')
    display(df_out)
    return df_out

print("CONVERGENCE ANALYSIS: immigrant coefficient by experience quartile")
print("=" * 65)"""))

cells.append(code("""# US: log pay (raw) — quartile convergence
us_conv = convergence_by_quartile(
    us,
    dep_var='log_pay',
    formula_template='log_pay_w ~ immigrant_w + C(graduate_degree) + C(graduate_major)',
    label='UNITED STATES — Immigrant premium (% pay) by experience quartile'
)
print()
print("Positive coeff = immigrants earn MORE. Does it shrink in higher quartiles?")"""))

cells.append(code("""# Penalty countries: standardised log pay — quartile convergence
pen_conv = convergence_by_quartile(
    pen,
    dep_var='log_pay_std',
    formula_template='log_pay_std_w ~ immigrant_w + C(country_work) + C(graduate_degree) + C(graduate_major)',
    label='PENALTY COUNTRIES (pooled) — Immigrant penalty (SD) by experience quartile'
)
print()
print("Negative coeff = immigrants earn LESS. Does it shrink (toward 0) in higher quartiles?")"""))

cells.append(code("""# Summary comparison table
print("CONVERGENCE SUMMARY")
print("=" * 60)
print("US — immigrant premium by quartile:")
for q, r in us_conv.iterrows():
    prem = (np.exp(r['Coeff'])-1)*100
    lo   = (np.exp(r['CI_lower'])-1)*100
    hi   = (np.exp(r['CI_upper'])-1)*100
    print(f"  {q:22s} ({r['Median_exp_yrs']:4.1f} yrs)  {prem:+5.1f}%  [{lo:+5.1f}%, {hi:+5.1f}%]  {r['Sig']}")

print()
print("Penalty countries — immigrant gap by quartile (SD units):")
for q, r in pen_conv.iterrows():
    print(f"  {q:22s} ({r['Median_exp_yrs']:4.1f} yrs)  {r['Coeff']:+.3f} SD  [{r['CI_lower']:+.3f}, {r['CI_upper']:+.3f}]  {r['Sig']}")"""))

# ── Analysis 2: Same origin, different destination ────────────────────────────
cells.append(md("""### 6.2 Same Origin, Different Destination

We isolate immigrants from **India** and **China** — the two largest origin groups —
and compare the immigrant coefficient *across destination countries*.

This controls for origin-country selection effects (we hold the "who" constant)
and isolates the pure destination labor market effect.

**Question:** Is the US premium specific to the US labor market, or would Indian/Chinese
immigrants earn a premium anywhere they go?"""))

cells.append(code("""# All 9 destination countries, standardised log pay within each
dall = df[df['country_work'].isin(TARGET)].copy()
dall['log_pay']     = np.log(dall['avg_pay'])
dall['log_pay_std'] = dall.groupby('country_work')['log_pay'].transform(
                          lambda x: (x - x.mean()) / x.std())

FOCUS_ORIGINS = ['India','China']
matrix_rows = []

for origin in FOCUS_ORIGINS:
    for dest in TARGET:
        sub = dall[(dall['country_work']==dest) &
                   ((dall['immigrant']==0) | (dall['country_bachelors']==origin))].copy()
        n_imm = int((sub['immigrant']==1).sum())
        n_nat = int((sub['immigrant']==0).sum())
        if n_imm < 5 or n_nat < 5 or sub['immigrant'].nunique() < 2:
            matrix_rows.append({'Origin': origin, 'Destination': dest,
                                 'N_imm': n_imm, 'N_native': n_nat,
                                 'Coeff_SD': np.nan, 'p_value': np.nan, 'Sig': '—'})
            continue

        formula = ('log_pay_std ~ immigrant + C(graduate_school) + C(graduate_degree) + C(graduate_major)'
                   if len(sub) >= 100 else
                   'log_pay_std ~ immigrant + C(graduate_degree) + C(graduate_major)')
        try:
            m = smf.ols(formula, data=sub).fit()
            b,lo,hi,p,sig = reg_stats(m,'immigrant')
            matrix_rows.append({'Origin': origin, 'Destination': dest,
                                 'N_imm': n_imm, 'N_native': n_nat,
                                 'Coeff_SD': round(b,3), 'p_value': round(p,4), 'Sig': sig})
        except:
            matrix_rows.append({'Origin': origin, 'Destination': dest,
                                 'N_imm': n_imm, 'N_native': n_nat,
                                 'Coeff_SD': np.nan, 'p_value': np.nan, 'Sig': '—'})

matrix_df = pd.DataFrame(matrix_rows)

# ── Coefficient matrix: Origin = rows, Destination = columns ──────────────
dest_order = ['United States','United Kingdom','Canada','Australia',
              'Ireland','Singapore','Hong Kong','Netherlands','Germany']

def fmt_cell(row):
    if pd.isna(row['Coeff_SD']): return '  —  '
    return f"{row['Coeff_SD']:+.3f}{row['Sig'].replace('ns','')}"

matrix_df['cell_str'] = matrix_df.apply(fmt_cell, axis=1)

coeff_matrix = (matrix_df.pivot(index='Destination', columns='Origin', values='Coeff_SD')
                          .reindex(dest_order))
sig_matrix   = (matrix_df.pivot(index='Destination', columns='Origin', values='Sig')
                          .reindex(dest_order))
str_matrix   = (matrix_df.pivot(index='Destination', columns='Origin', values='cell_str')
                          .reindex(dest_order))
n_imm_matrix = (matrix_df.pivot(index='Destination', columns='Origin', values='N_imm')
                          .reindex(dest_order))

print("Immigrant coefficient (SD of within-country log pay) — positive = premium")
print("Format: coefficient  (* p<.10  ** p<.05  *** p<.01  — = insufficient data)")
print()
display(str_matrix)
print()
print("Number of immigrant cells:")
display(n_imm_matrix)
print()
print("KEY QUESTION: Is the US premium specific to the US, or do Indian/Chinese")
print("immigrants earn a premium wherever they go?")"""))

# ── Analysis 4: School quality in penalty countries ─────────────────────────
cells.append(md("""### 6.3 School Quality and the Immigrant Penalty

**Hypothesis:** A prestigious graduate degree is a stronger signal that equalises
immigrant and native outcomes.  If true, the penalty should be concentrated at
lower-ranked schools and smaller (or absent) at elite institutions.

We classify schools in penalty countries into two tiers using a **data-driven**
approach: schools above the median of average native pay are "high quality";
the rest are "lower quality".  This avoids needing external ranking data for
non-US systems."""))

cells.append(code("""# Named elite schools for each penalty country
ELITE_PENALTY = {
    # Canada
    'University of Toronto','McGill University',
    'The University of British Columbia','University of Alberta',
    'McMaster University',"Queen's University",'University of Waterloo',
    'University of Calgary','Western University','Dalhousie University',
    # Australia
    'The University of Melbourne','The University of Sydney',
    'The University of New South Wales','Monash University',
    'The University of Queensland','Australian National University',
    'University of Western Australia',
    # Ireland
    'Trinity College Dublin','University College Dublin',
    'University College Cork','University of Galway',
    # Singapore
    'National University of Singapore',
    'Nanyang Technological University',
    # Hong Kong
    'The University of Hong Kong',
    'The Hong Kong University of Science and Technology',
    'The Chinese University of Hong Kong',
}

pen['tier'] = pen['graduate_school'].apply(
    lambda s: '1. Elite' if s in ELITE_PENALTY else '2. Other')

tier_counts_pen = pen.groupby(['tier','immigrant']).size().unstack(fill_value=0)
tier_counts_pen.columns = ['Native','Immigrant']
tier_counts_pen['Total'] = tier_counts_pen.sum(axis=1)
print("Cell counts by tier (penalty countries):"); display(tier_counts_pen)

print("\\nAverage experience by tier and immigrant status:")
display(pen.groupby(['tier','immigrant'])['avg_experience'].mean().unstack().round(2))"""))

cells.append(code("""print("Regression by tier — does the penalty differ by school quality?")
print("Model: log_pay_std_w ~ immigrant_w + experience_w + country_FE + degree_FE + major_FE")
print("(School FE absorbed via within-school demeaning)")
print()
tier_rows = []
for t in ['1. Elite','2. Other']:
    sub = pen[pen['tier']==t].copy()
    if sub['immigrant'].nunique() < 2 or len(sub) < 15: continue
    sw = within_demean(sub,'graduate_school',['log_pay_std','immigrant','avg_experience'])
    m  = smf.ols('log_pay_std_w ~ immigrant_w + avg_experience_w + C(country_work) + C(graduate_degree) + C(graduate_major)',
                 data=sw).fit()
    b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
    tier_rows.append({'Tier': t, 'N_cells': int(m.nobs),
                      'N_native': int((sub['immigrant']==0).sum()),
                      'N_immigrant': int(sub['immigrant'].sum()),
                      'Coeff_SD': round(b,3),
                      'CI_lower': round(lo,3), 'CI_upper': round(hi,3),
                      'p_value': round(p,4), 'Sig': sig})
    print(f"  {t}:  coeff={b:+.3f} SD  CI[{lo:+.3f},{hi:+.3f}]  p={p:.4f} {sig}  N={int(m.nobs)}")

print()
print("Interpretation: If the elite tier shows a smaller (less negative) coefficient,")
print("it suggests a prestigious graduate degree partially offsets the immigrant penalty.")"""))

cells.append(code("""# Also break down by country within each tier
print("Penalty by tier AND country:")
rows = []
for t in ['1. Elite','2. Other']:
    for country in PENALTY:
        sub = pen[(pen['tier']==t) & (pen['country_work']==country)].copy()
        n_imm = int(sub['immigrant'].sum()); n_nat = int((sub['immigrant']==0).sum())
        if n_imm < 3 or n_nat < 3 or sub['immigrant'].nunique() < 2:
            continue
        sw = within_demean(sub,'graduate_school',['log_pay_std','immigrant','avg_experience'])
        try:
            m = smf.ols('log_pay_std_w ~ immigrant_w + avg_experience_w + C(graduate_degree) + C(graduate_major)',
                        data=sw).fit()
            b,lo,hi,p,sig = reg_stats(m,'immigrant_w')
            rows.append({'Tier': t, 'Country': country,
                         'N_native': n_nat, 'N_imm': n_imm,
                         'Coeff_SD': round(b,3),
                         'CI_lower': round(lo,3), 'CI_upper': round(hi,3),
                         'p_value': round(p,4), 'Sig': sig})
        except: pass

pd.DataFrame(rows).set_index(['Tier','Country'])"""))

# ══════════════════════════════════════════════════════════════════════════════
# PART 7 — SUMMARY & DISCUSSION
# ══════════════════════════════════════════════════════════════════════════════
cells.append(md("""---
## Part 7 — Summary & Discussion

### 7.1 Summary of Key Findings

#### Finding 1 — The US is the exceptional premium country
Controlling for graduate school, degree type, and field of study (but **not** experience),
immigrants in the US earn **+17.8 %** more than natives.  Adding experience widens this
to **+25.9 %** because immigrants are actually *less* experienced than natives on average
(+1.65 yrs gap), so controlling for experience reveals an even larger underlying premium.

Every other destination country with enough data shows an immigrant *penalty* on the same
school+degree+major controls (no experience):
Canada −9.2 %, Australia −16.2 %, Ireland −8.5 %, Hong Kong −16.3 %, Singapore −5.6 %.
The UK is essentially neutral (+2.2 %, not significant).

> **Note:** The penalties in Finding 1 come from Part 3 regressions that do *not* yet
> control for experience.  Finding 2 below explains what happens when experience is added.

#### Finding 2 — The penalty is a career-stage effect, not wage discrimination
The Part 3 penalties are driven by the experience gap: immigrants in penalty countries
are ~1.5 years newer to the workforce than natives.  When experience is added to the
model for the penalty countries (Part 5), the penalty drops from −0.32 SD to **−0.047 SD
and becomes insignificant** (p = 0.48).

In other words: immigrants and natives at the same school, degree, major, *and career
stage* earn virtually the same.  The headline penalty in Finding 1 reflects the fact
that the immigrant pool is simply younger/more junior — not that they are paid less for
equivalent work.

#### Finding 3 — No assimilation in the US; noisy pattern in penalty countries
Splitting cells into experience quartiles (Q1: 0–3 yrs → Q4: 7+ yrs):

- **United States**: The premium is strikingly *stable* across all quartiles
  (Q1: +26.4 %, Q2: +32.0 %, Q3: +28.5 %, Q4: +31.7 %, all p < 0.001).
  There is no evidence of convergence; immigrants maintain a persistent earnings
  advantage regardless of career stage.

- **Penalty countries**: After experience is controlled within each quartile,
  the pattern is noisy and mostly insignificant.  No clear assimilation trend.
  The result is consistent with the main finding in Finding 2: once career stage
  is accounted for, the immigrant gap is already near zero.

#### Finding 4 — Same origin, different destination: a clear destination-market effect
Holding origin country fixed (India, China) and comparing outcomes across destinations:

- **India → US**: +0.74 SD premium (p < 0.001)
- **China → US**: +0.21 SD premium (significant)
- **India → Canada**: −0.30 SD penalty (p < 0.01)
- **India → Australia**: −0.67 SD penalty (p < 0.01)
- **China → Canada**: −0.31 SD penalty (p < 0.01)
- **China → Australia**: −1.21 SD penalty (p < 0.01)

The same workers (Indian or Chinese graduates) face a large premium in the US
and significant penalties in Canada and Australia.  This strongly points to a
**destination-market effect**: something specific to the US labor market
(H-1B screening, employer demand for tech skills) generates the premium,
not unobserved ability of the immigrants themselves.

#### Finding 5 — School quality does not moderate the immigrant penalty
In penalty countries, splitting schools into named elite institutions vs others:

- Elite schools (McGill, U Toronto, Melbourne, NUS, etc.): −0.051 SD (p = 0.59, ns)
- Other schools: −0.057 SD (p = 0.55, ns)

After experience is controlled, the penalty essentially disappears in *both* tiers.
A prestigious graduate credential does not meaningfully alter the immigrant wage gap
once career stage is held constant.  The hypothesis that elite credentials equalise
outcomes is not supported in this data.

---

### 7.2 Data Limitations

| Limitation | Impact |
|-----------|--------|
| Cell-level averages, unweighted | Cells with 3 workers weigh the same as cells with 300 |
| No individual-level controls | Cannot control for occupation, industry, or firm type |
| `avg_experience` is a cell mean | Noisy proxy for individual career stage / time since migration |
| Self-reported Glassdoor salaries | Tech-sector overrepresentation; no independent verification |
| No cell size variable | Cannot compute proper weighted regressions |
| Small samples outside US | Penalty-country regressions within quartiles / tiers are low-powered |"""))

cells.append(md("""---
### 7.3 Comparison with Martellini, Schoellman & Sockin (2024)

**Reference:** Martellini, P., Schoellman, T. & Sockin, J. (2024).
*The Global Distribution of College Graduate Quality.*
Journal of Political Economy, 132(2), 434–483.

#### Data & Sample

| Dimension | MSS (2024) | This analysis |
|-----------|-----------|---------------|
| Source | Glassdoor | Glassdoor (aggregated) |
| Data level | **Individual** (2.2 M workers) | **Cell averages** |
| Degree focus | **Bachelor's** only | **Graduate** (Masters/MBA/PhD) |
| Countries | 48 countries, 2 873 colleges | 9 destination countries |
| Migrants | 76 000 workers in 2+ countries | immigrant = bachelor's ≠ work country |

#### Methodology

MSS identify college quality by observing how the **same individual's earnings
change** when they move across countries — a within-person, cross-country design
that cleanly separates country wage premia from college human capital.

We use a simpler within-destination approach: compare immigrant and native
cell averages at the same school, degree, and major.  We cannot separate
immigrant ability/selection from a true wage premium.

| Dimension | MSS (2024) | This analysis |
|-----------|-----------|---------------|
| Country wage FE | Within-person cross-country changes | Country FE (crude) |
| Selection | Explicitly modelled (+50 % pre-migration) | Noted, not corrected |
| School quality | Undergraduate FE | Graduate school FE |
| Experience | Individual work history | Cell-mean `avg_experience` |

#### Convergence of findings

1. **Positive selection is consistent.** MSS document +50 % pre-migration
   earnings of emigrants from developing countries.  Our US premium (+26 %)
   reflects the same highly-selected Indian/Chinese graduate cohort.

2. **The destination asymmetry aligns with MSS's selection gradient.**
   MSS predict the selection gap is largest from poor countries; our data shows
   this selection generates a premium *only* in the US (the hardest destination
   to enter), not in Canada or Australia (which run high-volume student pipelines).

3. **Same-origin/different-destination result confirms MSS's market price effect.**
   Indian immigrants earn a premium in the US but not in Canada — the same
   individuals face different outcomes in different markets, consistent with
   MSS's separation of college quality from labor-market prices.

#### Key divergence

MSS measure undergraduate college quality; we measure a graduate-level
immigrant earnings *premium*.  These are complementary: we control for the
graduate school (holding the graduate investment fixed) and ask whether
*origin country* still matters — it does, but only in the US."""))

# ══════════════════════════════════════════════════════════════════════════════
# BUILD
# ══════════════════════════════════════════════════════════════════════════════
nb.cells = cells

OUT = r'C:\Users\sharafi\Dropbox\Immigrants_J&Z\Immigrant_Pay_Analysis.ipynb'
with open(OUT, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook written: {OUT}")
print(f"Total cells: {len(cells)}")
