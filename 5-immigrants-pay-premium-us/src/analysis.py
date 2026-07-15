import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import sys
sys.stdout.reconfigure(encoding='utf-8')
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv(r'C:\Users\sharafi\Dropbox\Immigrants_J&Z\Data\Avg_pay_by_graduate_school_undergraduate_country.csv', index_col=0)
df['immigrant'] = (df['country_bachelors'] != df['country_work']).astype(int)

target = ['United States', 'United Kingdom', 'Canada', 'Australia', 'Germany']
d = df[df['country_work'].isin(target)].copy()
d['log_pay'] = np.log(d['avg_pay'])

# ================================================================
# 1. SAMPLE OVERVIEW
# ================================================================
print('=' * 68)
print('1. SAMPLE OVERVIEW')
print('   Note: each row = one cell-level average, not an individual worker.')
print('   A cell = unique (grad school x degree x major x bachelor country).')
print('=' * 68)
counts = d.groupby(['country_work','immigrant']).size().unstack(fill_value=0)
counts.columns = ['Native cells','Immigrant cells']
counts['Total cells'] = counts.sum(axis=1)
print(counts)

# ================================================================
# 2. RAW (UNADJUSTED) PAY GAP
# ================================================================
print()
print('=' * 68)
print('2. UNADJUSTED AVERAGE PAY BY GROUP (local currency, cell means)')
print('=' * 68)
raw = d.groupby(['country_work','immigrant'])['avg_pay'].mean().unstack()
raw.columns = ['Native avg pay','Immigrant avg pay']
raw['Raw gap %'] = ((raw['Immigrant avg pay'] - raw['Native avg pay']) / raw['Native avg pay'] * 100).round(1)
currencies = df[df['country_work'].isin(target)].groupby('country_work')['currency'].first()
raw['Currency'] = currencies
print(raw.round(0))

# ================================================================
# 3. WITHIN-CELL COMPARISON (same school x degree x major)
# ================================================================
print()
print('=' * 68)
print('3. WITHIN-CELL COMPARISON (same school, degree, major)')
print('   Cells that have BOTH an immigrant and a native average.')
print('=' * 68)
d['cell'] = d['graduate_school'] + '||' + d['graduate_degree'] + '||' + d['graduate_major']
paired = (d.groupby(['country_work','cell','immigrant'])['avg_pay']
           .mean().unstack())
paired.columns = ['native_pay','immigrant_pay']
paired = paired.dropna()
paired['gap_pct'] = ((paired['immigrant_pay'] - paired['native_pay']) / paired['native_pay'] * 100).round(1)

summary = paired.groupby('country_work')['gap_pct'].agg(
    Mean=lambda x: round(x.mean(), 1),
    Median=lambda x: round(x.median(), 1),
    N_cells='count'
)
print(summary)

# ================================================================
# 4. OLS REGRESSION
# ================================================================
print()
print('=' * 68)
print('4. OLS REGRESSION  |  dep var: log(avg_pay)')
print('   immigrant + school FE + degree FE + major FE')
print('   Data: cell-level averages -- all cells weighted equally.')
print('   Standard errors are OLS (unit of obs = cell average).')
print('=' * 68)

results = []
for country in target:
    sub = d[d['country_work']==country].copy()
    n_imm = int(sub['immigrant'].sum())
    n_nat = int(len(sub) - n_imm)

    if sub['immigrant'].nunique() < 2:
        print(f'  {country}: no variation in immigrant status -- skipped')
        continue

    # Germany / small samples: drop school FE
    if country == 'Germany' or len(sub) < 50:
        formula = 'log_pay ~ immigrant + C(graduate_degree) + C(graduate_major)'
        model_note = 'degree+major FE only (too few obs for school FE)'
    else:
        formula = 'log_pay ~ immigrant + C(graduate_school) + C(graduate_degree) + C(graduate_major)'
        model_note = 'school+degree+major FE'

    try:
        m = smf.ols(formula, data=sub).fit()
        b  = m.params['immigrant']
        p  = m.pvalues['immigrant']
        ci = m.conf_int().loc['immigrant']
        gap = (np.exp(b)-1)*100
        cil = (np.exp(ci[0])-1)*100
        ciu = (np.exp(ci[1])-1)*100
        sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
        curr = d[d['country_work']==country]['currency'].iloc[0]

        results.append({
            'Country': country, 'Currency': curr,
            'N_cells': int(m.nobs), 'N_native': n_nat, 'N_immigrant': n_imm,
            'Pay_gap_%': round(gap,1),
            'CI_lower_%': round(cil,1), 'CI_upper_%': round(ciu,1),
            'p_value': round(p,4), 'Sig': sig, 'R2': round(m.rsquared,3),
            'Controls': model_note
        })

        print(f'  {country}  ({model_note})')
        print(f'    N = {int(m.nobs)} cells  ({n_nat} native, {n_imm} immigrant)')
        print(f'    Immigrant gap = {gap:+.1f}%   95% CI [{cil:+.1f}%, {ciu:+.1f}%]   p={p:.4f} {sig}   R2={m.rsquared:.3f}')
        print()
    except Exception as e:
        print(f'  {country}: error -- {e}')

# ================================================================
# 5. POOLED REGRESSION
# ================================================================
print('=' * 68)
print('5. POOLED REGRESSION (all 5 countries)')
print('   Dep var: log(avg_pay) standardized within each country')
print('   Controls: country FE + degree FE + major FE')
print('   (School FE omitted to allow pooling across countries)')
print('=' * 68)

d['log_pay_std'] = d.groupby('country_work')['log_pay'].transform(
    lambda x: (x - x.mean()) / x.std())

pool = smf.ols(
    'log_pay_std ~ immigrant + C(country_work) + C(graduate_degree) + C(graduate_major)',
    data=d).fit()

b  = pool.params['immigrant']
p  = pool.pvalues['immigrant']
ci = pool.conf_int().loc['immigrant']
sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
print(f'  N = {int(pool.nobs)} cells')
print(f'  Immigrant coeff = {b:+.3f} SD   95% CI [{ci[0]:+.3f}, {ci[1]:+.3f}]   p={p:.4f} {sig}   R2={pool.rsquared:.3f}')
print(f'  Interpretation: immigrants earn {b:+.3f} within-country SDs of log pay')
print(f'  relative to natives, after controlling for degree type and field.')

# ================================================================
# 6. SUMMARY TABLE
# ================================================================
print()
print('=' * 68)
print('6. SUMMARY TABLE')
print('=' * 68)
res_df = pd.DataFrame(results)
print(res_df[['Country','Currency','N_cells','N_native','N_immigrant',
              'Pay_gap_%','CI_lower_%','CI_upper_%','p_value','Sig','R2']].to_string(index=False))
print()
print('Pay_gap_%: % difference in immigrant vs native avg pay,')
print('  controlling for graduate school, degree type, and major.')
print('  (* p<.10  ** p<.05  *** p<.01, OLS standard errors)')
print()
print('Data note: unit of observation is a cell-level average,')
print('  not an individual worker. Cells are weighted equally.')
print('  Results should be interpreted as differences in group-average')
print('  pay across cells with equivalent graduate education profiles.')
