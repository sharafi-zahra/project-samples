import nbformat as nbf

nb = nbf.v4.new_notebook()
nb['metadata'] = {
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.11.0'}
}

cells = []
def md(src):   return nbf.v4.new_markdown_cell(src)
def code(src): return nbf.v4.new_code_cell(src)

cells.append(md("""# US Immigrant Pay Premium — What Drives It?

Using `Avg_pay_by_graduate_school_immigrant_status.csv`.
Each cell = average pay for (school × degree × major × immigrant status).

**Key question:** Does the premium vary by field, school tier, or degree type?"""))

# ── SETUP ─────────────────────────────────────────────────────────────────────
cells.append(md("## 1. Setup"))
cells.append(code("""import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import warnings
warnings.filterwarnings('ignore')
from IPython.display import display
pd.set_option('display.float_format', '{:.3f}'.format)

def within_demean(data, group_col, cols):
    d = data.copy()
    means = data.groupby(group_col)[cols].transform('mean')
    for c in cols:
        d[c + '_w'] = d[c] - means[c]
    return d

def reg_stats(m, key):
    b = m.params[key]; p = m.pvalues[key]; ci = m.conf_int().loc[key]
    sig = '***' if p < .01 else '**' if p < .05 else '*' if p < .10 else 'ns'
    return b, ci[0], ci[1], p, sig

DATA = r'C:\\Users\\sharafi\\Dropbox\\Immigrants_J&Z\\Data\\Avg_pay_by_graduate_school_immigrant_status.csv'
df = pd.read_csv(DATA, index_col=0)
us = df[df['country_work'] == 'United States'].copy()
us['log_pay'] = np.log(us['avg_pay'])

EXCLUDE_SCHOOLS = {
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
us = us[~us['graduate_school'].isin(EXCLUDE_SCHOOLS)].copy()

IVY_ELITE = {
    'Harvard University','Massachusetts Institute of Technology','Stanford University',
    'Princeton University','Yale University',
    'Columbia University in the City of New York','University of Pennsylvania',
    'Cornell University','Dartmouth College','Brown University','Duke University',
    'Northwestern University','University of Chicago',
    'California Institute of Technology','Johns Hopkins University'
}
TOP50 = {
    'University of California-Berkeley','University of California-Los Angeles',
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
    'University of Minnesota-Twin Cities','University of California-Santa Barbara'
}
us['tier'] = us['graduate_school'].apply(
    lambda s: '1_Top' if s in IVY_ELITE | TOP50 else '2_Other')

uw = within_demean(us, 'graduate_school', ['log_pay', 'immigrant', 'avg_experience'])

print(f"Cells: {len(us):,}  |  Native: {(us['immigrant']==0).sum():,}  |  Immigrant: {us['immigrant'].sum():,}")"""))

# ── BUILDING CONTROLS ─────────────────────────────────────────────────────────
cells.append(md("""## 2. Building Up Controls (M1–M4)

Each model adds one layer. Dependent variable: log(avg_pay)."""))
cells.append(code("""specs = [
    ('M1: No controls',
     smf.ols('log_pay ~ immigrant', data=us).fit(),
     'immigrant'),
    ('M2: + Degree + Major FE',
     smf.ols('log_pay ~ immigrant + C(graduate_degree) + C(graduate_major)', data=us).fit(),
     'immigrant'),
    ('M3: + School FE',
     smf.ols('log_pay_w ~ immigrant_w + C(graduate_degree) + C(graduate_major)', data=uw).fit(),
     'immigrant_w'),
    ('M4: + Experience  [MAIN]',
     smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree) + C(graduate_major)', data=uw).fit(),
     'immigrant_w'),
]

rows = []
for label, m, key in specs:
    b, lo, hi, p, sig = reg_stats(m, key)
    rows.append({
        'Model': label,
        'Gap_%': f'{(np.exp(b)-1)*100:+.1f}%',
        '95%_CI': f'[{(np.exp(lo)-1)*100:+.1f}%, {(np.exp(hi)-1)*100:+.1f}%]',
        'p_value': round(p, 4), 'Sig': sig,
        'R2': round(m.rsquared, 3), 'N': int(m.nobs)
    })

display(pd.DataFrame(rows).set_index('Model'))
print()
print("M1->M2: +21% -> +15%  (immigrants sort into higher-paying fields/degrees)")
print("M2->M3: +15% -> +12%  (immigrants also attend slightly higher-paying schools)")
print("M3->M4: +12% -> +19%  (immigrants are less experienced; controlling for")
print("                        experience RAISES the estimated premium)")"""))

# ── SCHOOL TIER INTERACTION ───────────────────────────────────────────────────
cells.append(md("## 3. School Tier Interaction (M5)"))
cells.append(code("""m5 = smf.ols(
    'log_pay_w ~ immigrant_w * C(tier) + avg_experience_w + C(graduate_degree) + C(graduate_major)',
    data=uw).fit()

b_base, lo, hi, p_base, sig_base = reg_stats(m5, 'immigrant_w')
b_int = m5.params['immigrant_w:C(tier)[T.2_Other]']
p_int = m5.pvalues['immigrant_w:C(tier)[T.2_Other]']
gap_top   = (np.exp(b_base) - 1) * 100
gap_other = (np.exp(b_base + b_int) - 1) * 100
sig_int   = '***' if p_int<.01 else '**' if p_int<.05 else '*' if p_int<.10 else 'ns'

display(pd.DataFrame({
    'Immigrant premium': [f'{gap_top:+.1f}%', f'{gap_other:+.1f}%', f'{gap_other-gap_top:+.1f}pp'],
    'p': [f'{p_base:.4f} {sig_base}', '—', f'{p_int:.4f} {sig_int}']
}, index=['Top schools (Ivy + Top50)', 'Other schools', 'Difference (Other minus Top)']))
print(f"R2={m5.rsquared:.3f}   N={int(m5.nobs)}")"""))

# ── MAJOR INTERACTION ─────────────────────────────────────────────────────────
cells.append(md("## 4. Field Heterogeneity (M6 — immigrant × major)"))
cells.append(code("""us_b = us.copy()
us_b['graduate_major'] = us_b['graduate_major'].replace({'Business': 'AAA_Business'})
uw_b = within_demean(us_b, 'graduate_school', ['log_pay', 'immigrant', 'avg_experience'])

m6 = smf.ols(
    'log_pay_w ~ immigrant_w * C(graduate_major) + avg_experience_w + C(graduate_degree)',
    data=uw_b).fit()

b_base, lo, hi, p_base, sig_base = reg_stats(m6, 'immigrant_w')
gap_base = (np.exp(b_base) - 1) * 100

ints = [(k, m6.params[k], m6.pvalues[k])
        for k in m6.params.index if 'immigrant_w:C(graduate_major)' in k]

rows = [{'Field': 'Business (reference)',
         'N_immigrant': int(us[us['graduate_major']=='Business']['immigrant'].sum()),
         'Total_gap_%': f'{gap_base:+.1f}%',
         'vs_Business': '—', 'p_interaction': '—', 'Sig': sig_base}]

for name, coef, p_i in sorted(ints, key=lambda x: -(np.exp(b_base + x[1]) - 1)):
    major = name.replace('immigrant_w:C(graduate_major)[T.', '').rstrip(']')
    total = (np.exp(b_base + coef) - 1) * 100
    sig_i = '***' if p_i<.01 else '**' if p_i<.05 else '*' if p_i<.10 else 'ns'
    rows.append({'Field': major,
                 'N_immigrant': int(us[us['graduate_major']==major]['immigrant'].sum()),
                 'Total_gap_%': f'{total:+.1f}%',
                 'vs_Business': f'{total-gap_base:+.1f}pp',
                 'p_interaction': round(p_i, 4), 'Sig': sig_i})

display(pd.DataFrame(rows).set_index('Field'))
n_sig = sum(1 for _,_,p_i in ints if p_i < .05)
print(f"R2={m6.rsquared:.3f}   N={int(m6.nobs)}")
print(f"{n_sig}/{len(ints)} fields differ significantly from Business.")"""))

# ── FIELD x TIER ──────────────────────────────────────────────────────────────
cells.append(md("## 5. Field × School Tier (M7 — separate regressions)"))
cells.append(code("""rows = []
for major in sorted(us['graduate_major'].unique()):
    for tier_label, tier_val in [('Top', '1_Top'), ('Other', '2_Other')]:
        sub = us[(us['graduate_major']==major) & (us['tier']==tier_val)]
        n_imm = int(sub['immigrant'].sum())
        n_nat = int((sub['immigrant']==0).sum())
        if sub['immigrant'].nunique() < 2 or n_imm < 10 or n_nat < 5:
            continue
        sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
        try:
            m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree)',
                        data=sw).fit()
            b, lo, hi, p, sig = reg_stats(m, 'immigrant_w')
            rows.append({'Field': major, 'Tier': tier_label,
                         'N_native': n_nat, 'N_immigrant': n_imm,
                         'Gap_%': f'{(np.exp(b)-1)*100:+.1f}%',
                         '95%_CI': f'[{(np.exp(lo)-1)*100:+.1f}%, {(np.exp(hi)-1)*100:+.1f}%]',
                         'p_value': round(p, 4), 'Sig': sig})
        except:
            pass

display(pd.DataFrame(rows).set_index(['Field','Tier']))"""))

# ── SUMMARY TABLE ─────────────────────────────────────────────────────────────
cells.append(md("## 6. Summary: Immigrant Share, Pay, and Adjusted Premium by Field"))
cells.append(code("""rows = []
for major in sorted(us['graduate_major'].unique()):
    sub = us[us['graduate_major']==major]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: continue
    n_nat = int((sub['immigrant']==0).sum())
    n_imm = int(sub['immigrant'].sum())
    nat_med = sub[sub['immigrant']==0]['avg_pay'].median()
    imm_med = sub[sub['immigrant']==1]['avg_pay'].median()
    sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree)', data=sw).fit()
        b, lo, hi, p, sig = reg_stats(m, 'immigrant_w')
        gap_pct = (np.exp(b)-1)*100
        rows.append({'Field': major,
                     'N_total': n_nat+n_imm,
                     'N_native': n_nat, 'N_immigrant': n_imm,
                     'Imm_share_%': round(n_imm/(n_nat+n_imm)*100, 1),
                     'Native_median_$': int(nat_med),
                     'Imm_median_$': int(imm_med),
                     'Adj_premium_%': round(gap_pct, 1),
                     'Extra_earning_$': int(nat_med*gap_pct/100),
                     'Evidence': sig})
    except: pass

display(pd.DataFrame(rows).sort_values('Imm_share_%', ascending=False).set_index('Field'))"""))

# ── DESCRIPTIVE FIELD SUMMARY ────────────────────────────────────────────────
cells.append(md("## 7. Descriptive Field Summary (Immigrant Share + Dollar Premium)"))
cells.append(code("""rows = []
for major in sorted(us['graduate_major'].unique()):
    sub = us[us['graduate_major']==major]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: continue
    n_nat = int((sub['immigrant']==0).sum())
    n_imm = int(sub['immigrant'].sum())
    nat_med = sub[sub['immigrant']==0]['avg_pay'].median()
    imm_med = sub[sub['immigrant']==1]['avg_pay'].median()
    sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree)', data=sw).fit()
        b, lo, hi, p, sig = reg_stats(m, 'immigrant_w')
        gap_pct = round((np.exp(b)-1)*100, 1)
        rows.append({
            'Field': major,
            'N_total': n_nat+n_imm, 'N_native': n_nat, 'N_immigrant': n_imm,
            'Imm_share_%': round(n_imm/(n_nat+n_imm)*100, 1),
            'Native_median_$': int(nat_med), 'Imm_median_$': int(imm_med),
            'Adj_premium_%': gap_pct,
            'Extra_earning_$': int(nat_med*gap_pct/100),
            'Evidence': sig})
    except: pass

display(pd.DataFrame(rows).sort_values('Imm_share_%', ascending=False).set_index('Field'))"""))

# ── COMPACT FIELD x TIER ──────────────────────────────────────────────────────
cells.append(md("## 8. Compact Field × Tier (side-by-side)"))
cells.append(code("""def get_premium(sub):
    if sub['immigrant'].nunique() < 2 or len(sub) < 10: return None, None, None, None
    sw = within_demean(sub, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree)', data=sw).fit()
        b, lo, hi, p, sig = reg_stats(m, 'immigrant_w')
        nat_med = sub[sub['immigrant']==0]['avg_pay'].median()
        gap_pct = round((np.exp(b)-1)*100, 1)
        gap_usd = int(nat_med * gap_pct/100)
        n_imm = int(sub['immigrant'].sum())
        return gap_pct, gap_usd, sig, n_imm
    except:
        return None, None, None, None

def fmt_tier(pct, usd, sig, n):
    if pct is None: return '—'
    return f'{pct:+.0f}% / ${usd:,} {sig} (n={n})'

rows = []
for major in sorted(us['graduate_major'].unique()):
    sub_all   = us[us['graduate_major']==major]
    sub_top   = us[(us['graduate_major']==major) & (us['tier']=='1_Top')]
    sub_other = us[(us['graduate_major']==major) & (us['tier']=='2_Other')]
    if sub_all['immigrant'].nunique() < 2 or len(sub_all) < 10: continue

    n_nat = int((sub_all['immigrant']==0).sum())
    n_imm = int(sub_all['immigrant'].sum())
    nat_med = sub_all[sub_all['immigrant']==0]['avg_pay'].median()

    sw = within_demean(sub_all, 'graduate_school', ['log_pay','immigrant','avg_experience'])
    try:
        m = smf.ols('log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree)', data=sw).fit()
        b, lo, hi, p, sig = reg_stats(m, 'immigrant_w')
        ov_pct = round((np.exp(b)-1)*100, 1)
        ov_usd = int(nat_med*ov_pct/100)
        overall_str = f'{ov_pct:+.1f}% / ${ov_usd:,} {sig}'
    except: continue

    tp, tu, ts, tn = get_premium(sub_top)
    op, ou, os_, on = get_premium(sub_other)

    rows.append({
        'Field': major,
        'N_total': n_nat+n_imm,
        'Imm_%': round(n_imm/(n_nat+n_imm)*100, 1),
        'Overall_premium': overall_str,
        'Top_schools': fmt_tier(tp, tu, ts, tn),
        'Other_schools': fmt_tier(op, ou, os_, on),
    })

display(pd.DataFrame(rows).sort_values('Imm_%', ascending=False).set_index('Field'))"""))

# ── BUILD ─────────────────────────────────────────────────────────────────────
nb.cells = cells

OUT = r'C:\Users\sharafi\Dropbox\Immigrants_J&Z\US_Premium_DeepDive.ipynb'
with open(OUT, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook written: {OUT}")
print(f"Total cells: {len(cells)}")
