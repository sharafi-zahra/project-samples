import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import sys
sys.stdout.reconfigure(encoding='utf-8')
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv(r'C:\Users\sharafi\Dropbox\Immigrants_J&Z\Data\Avg_pay_by_graduate_school_undergraduate_country.csv', index_col=0)
df['immigrant'] = (df['country_bachelors'] != df['country_work']).astype(int)
us = df[df['country_work'] == 'United States'].copy()
us['log_pay'] = np.log(us['avg_pay'])

# Helper: run OLS within a subset, return key stats
def run_ols(data, formula='log_pay ~ immigrant + C(graduate_school) + C(graduate_degree)'):
    if data['immigrant'].nunique() < 2 or len(data) < 10:
        return None
    try:
        m = smf.ols(formula, data=data).fit()
        b  = m.params['immigrant']
        p  = m.pvalues['immigrant']
        ci = m.conf_int().loc['immigrant']
        return {
            'N': int(m.nobs),
            'N_native': int((data['immigrant']==0).sum()),
            'N_imm': int((data['immigrant']==1).sum()),
            'gap_%': round((np.exp(b)-1)*100, 1),
            'ci_lo': round((np.exp(ci[0])-1)*100, 1),
            'ci_hi': round((np.exp(ci[1])-1)*100, 1),
            'p': round(p, 4),
            'sig': '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
        }
    except:
        return None

# ================================================================
# 1. DISTRIBUTION CHECK: within-cell gaps (same school+degree+major)
# ================================================================
print('=' * 68)
print('1. DISTRIBUTION OF WITHIN-CELL GAPS (same school, degree, major)')
print('   How spread out are immigrant vs native pay differences?')
print('=' * 68)
us['cell'] = us['graduate_school'] + '||' + us['graduate_degree'] + '||' + us['graduate_major']
paired = (us.groupby(['cell', 'immigrant'])['avg_pay'].mean().unstack())
paired.columns = ['native_pay', 'immigrant_pay']
paired = paired.dropna()
paired['gap_pct'] = ((paired['immigrant_pay'] - paired['native_pay']) / paired['native_pay'] * 100)

print(f'\nCells with both groups: {len(paired)}')
print('\nDistribution of immigrant-native gap within same cell:')
desc = paired['gap_pct'].describe(percentiles=[.10,.25,.50,.75,.90])
for k,v in desc.items():
    print(f'  {k:6s}: {v:+.1f}%')

print(f'\nCells where immigrants earn MORE: {(paired["gap_pct"]>0).sum()} ({(paired["gap_pct"]>0).mean()*100:.0f}%)')
print(f'Cells where immigrants earn LESS: {(paired["gap_pct"]<0).sum()} ({(paired["gap_pct"]<0).mean()*100:.0f}%)')

print('\nTop 15 cells with HIGHEST immigrant premium:')
top = paired.nlargest(15, 'gap_pct')[['native_pay','immigrant_pay','gap_pct']].round(0)
print(top.to_string())

print('\nTop 15 cells with LARGEST immigrant penalty:')
bot = paired.nsmallest(15, 'gap_pct')[['native_pay','immigrant_pay','gap_pct']].round(0)
print(bot.to_string())

# ================================================================
# 2. BY GRADUATE MAJOR
# ================================================================
print()
print('=' * 68)
print('2. IMMIGRANT PREMIUM BY GRADUATE MAJOR')
print('   Controls: graduate school FE + degree type FE')
print('=' * 68)
rows = []
for major in sorted(us['graduate_major'].unique()):
    sub = us[us['graduate_major'] == major]
    r = run_ols(sub)
    if r:
        r['Major'] = major
        rows.append(r)

res = pd.DataFrame(rows).set_index('Major')
res = res.sort_values('gap_%', ascending=False)
print(res[['N','N_native','N_imm','gap_%','ci_lo','ci_hi','p','sig']].to_string())

# ================================================================
# 3. BY DEGREE TYPE
# ================================================================
print()
print('=' * 68)
print('3. IMMIGRANT PREMIUM BY DEGREE TYPE')
print('   Controls: graduate school FE + major FE')
print('=' * 68)
rows = []
for deg in sorted(us['graduate_degree'].unique()):
    sub = us[us['graduate_degree'] == deg]
    r = run_ols(sub, formula='log_pay ~ immigrant + C(graduate_school) + C(graduate_major)')
    if r:
        r['Degree'] = deg
        rows.append(r)

res2 = pd.DataFrame(rows).set_index('Degree')
res2 = res2.sort_values('gap_%', ascending=False)
print(res2[['N','N_native','N_imm','gap_%','ci_lo','ci_hi','p','sig']].to_string())

# ================================================================
# 4. BY BACHELOR'S COUNTRY (top origin countries)
# ================================================================
print()
print('=' * 68)
print('4. IMMIGRANT PREMIUM BY BACHELOR COUNTRY (vs US natives)')
print('   Controls: graduate school FE + degree FE + major FE')
print('   Each row: US natives vs immigrants from that specific country')
print('=' * 68)
top_origins = us[us['immigrant']==1]['country_bachelors'].value_counts()
top_origins = top_origins[top_origins >= 5].index.tolist()

rows = []
for origin in top_origins:
    sub = us[(us['immigrant']==0) | (us['country_bachelors']==origin)].copy()
    r = run_ols(sub, formula='log_pay ~ immigrant + C(graduate_school) + C(graduate_degree) + C(graduate_major)')
    if r:
        r['Bachelor_country'] = origin
        rows.append(r)

res3 = pd.DataFrame(rows).set_index('Bachelor_country')
res3 = res3.sort_values('gap_%', ascending=False)
print(res3[['N','N_native','N_imm','gap_%','ci_lo','ci_hi','p','sig']].to_string())

# ================================================================
# 5. MAJOR x IMMIGRANT INTERACTION (main regression with interactions)
# ================================================================
print()
print('=' * 68)
print('5. INTERACTION: immigrant x graduate_major')
print('   Does the premium differ significantly across fields?')
print('   Controls: school FE + degree FE')
print('=' * 68)
m_int = smf.ols(
    'log_pay ~ immigrant * C(graduate_major) + C(graduate_school) + C(graduate_degree)',
    data=us
).fit()

# Extract immigrant x major interaction terms
params = m_int.params
pvals  = m_int.pvalues
coefs  = [(k, params[k], pvals[k]) for k in params.index if 'immigrant:C(graduate_major)' in k]

# Base category effect (immigrant alone)
base_b = params['immigrant']
base_p = pvals['immigrant']
base_gap = (np.exp(base_b)-1)*100
print(f'  Base (Arts & Humanities -- reference major): {base_gap:+.1f}%  p={base_p:.4f}')
print()
print('  Additional effect vs reference major (interaction terms):')
for name, coef, p in sorted(coefs, key=lambda x: -x[1]):
    major = name.replace("immigrant:C(graduate_major)[T.", "").rstrip("]")
    total_gap = (np.exp(base_b + coef)-1)*100
    sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
    print(f'    {major:25s}  total gap={total_gap:+.1f}%  interaction p={p:.4f} {sig}')

print(f'\n  Overall model R2={m_int.rsquared:.3f}  N={int(m_int.nobs)}')
