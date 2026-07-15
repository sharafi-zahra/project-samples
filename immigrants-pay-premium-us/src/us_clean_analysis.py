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

# ================================================================
# STEP 1: REMOVE VOCATIONAL / NON-GRADUATE SCHOOLS
# ================================================================
# Explicit exclusion list: cosmetology, beauty, vocational, community colleges
EXCLUDE_SCHOOLS = {
    'Platt College-Anaheim',
    'Porter and Chester Institute of Stratford',
    'North-West College-Riverside',
    'The Fab School',
    'NTMA Training Centers of Southern California',
    'Porterville College',
    'Palladium Technical Academy',
    'Ponca City Beauty College',
    'P B Cosmetology Education Center',
    'Macomb Community College',
    'Pomona Unified School District Adult and Career Education',
    'Omega Institute of Cosmetology',
    'Community College of Baltimore County',
    'Elaine Sterling Institute',
    'European Academy of Cosmetology and Hairdressing',
    'Oceanside College of Beauty',
    'M-DCPS The English Center',
    'Coastal Bend College',
    'Ridgewater College',
    'Howard College',
    'Pima Community College',
    'El Paso Community College',
    'Des Moines Area Community College',
    'Elizabeth Grady School of Esthetics and Massage Therapy',
    'Lakeland Community College',
    'Northern Virginia Community College',
    'Wake Technical Community College',
    'Wayne Community College',
    'Bridgewater State University',  # state college, not grad school
}

us_clean = us[~us['graduate_school'].isin(EXCLUDE_SCHOOLS)].copy()
removed = len(us) - len(us_clean)
print('=' * 68)
print('SAMPLE AFTER REMOVING VOCATIONAL / COMMUNITY COLLEGE SCHOOLS')
print('=' * 68)
print(f'  Removed {removed} cells ({removed/len(us)*100:.1f}%)')
print(f'  Remaining: {len(us_clean)} cells')
print(f'  Native: {(us_clean["immigrant"]==0).sum()}  |  Immigrant: {(us_clean["immigrant"]==1).sum()}')

# ================================================================
# STEP 2: EXPERIENCE IMBALANCE CHECK
# ================================================================
print()
print('=' * 68)
print('EXPERIENCE IMBALANCE: immigrants vs natives')
print('=' * 68)
exp = us_clean.groupby('immigrant')['avg_experience'].agg(['mean','median','std'])
exp.index = ['Native','Immigrant']
print(exp.round(2))
gap_yrs = exp.loc['Native','mean'] - exp.loc['Immigrant','mean']
print(f'\nNatives have {gap_yrs:.2f} more years of experience on average.')
print('Correlation avg_experience <-> avg_pay:', round(us_clean['avg_pay'].corr(us_clean['avg_experience']), 3))

print('\nExperience by major:')
exp_maj = us_clean.groupby(['graduate_major','immigrant'])['avg_experience'].mean().unstack().round(2)
exp_maj.columns = ['Native_exp','Immigrant_exp']
exp_maj['Gap_yrs'] = (exp_maj['Native_exp'] - exp_maj['Immigrant_exp']).round(2)
print(exp_maj)

# ================================================================
# STEP 3: REGRESSION COMPARISON
#   Model A: school + degree + major FE  (original, no experience)
#   Model B: school + degree + major FE + avg_experience
# ================================================================
print()
print('=' * 68)
print('REGRESSION: before vs after controlling for experience')
print('  Dep var: log(avg_pay)   Sample: cleaned US data')
print('=' * 68)

# School FE via within-school demeaning (avoids SVD failure with 1000+ dummies)
def within_demean(data, group_col, cols):
    d = data.copy()
    means = d.groupby(group_col)[cols].transform('mean')
    for c in cols:
        d[c + '_w'] = d[c] - means[c]
    return d

demean_cols = ['log_pay', 'immigrant', 'avg_experience']
uw = within_demean(us_clean, 'graduate_school', demean_cols)

# Add degree and major dummies (still needed after school demeaning)
formula_A = 'log_pay_w ~ immigrant_w + C(graduate_degree) + C(graduate_major)'
formula_B = 'log_pay_w ~ immigrant_w + avg_experience_w + C(graduate_degree) + C(graduate_major)'

mA = smf.ols(formula_A, data=uw).fit()
mB = smf.ols(formula_B, data=uw).fit()

def fmt_imm(m, key='immigrant_w'):
    b  = m.params[key]
    p  = m.pvalues[key]
    ci = m.conf_int().loc[key]
    gap = (np.exp(b)-1)*100
    cil = (np.exp(ci[0])-1)*100
    ciu = (np.exp(ci[1])-1)*100
    sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
    return f'gap={gap:+.1f}%  CI[{cil:+.1f}%,{ciu:+.1f}%]  p={p:.4f} {sig}'

print(f'\nModel A — school+degree+major FE, NO experience control:')
print(f'  Immigrant: {fmt_imm(mA)}   R2={mA.rsquared:.3f}  N={int(mA.nobs)}')

exp_b = mB.params['avg_experience_w']
exp_p = mB.pvalues['avg_experience_w']
exp_sig = '***' if exp_p<.01 else '**' if exp_p<.05 else '*' if exp_p<.10 else 'ns'
print(f'\nModel B — school+degree+major FE, WITH experience control:')
print(f'  Immigrant:  {fmt_imm(mB)}   R2={mB.rsquared:.3f}  N={int(mB.nobs)}')
print(f'  Experience: coeff={exp_b:+.4f}  p={exp_p:.4f} {exp_sig}  (~{(np.exp(exp_b)-1)*100:.1f}% pay per extra year)')

# ================================================================
# STEP 4: BY MAJOR — with experience control
# ================================================================
print()
print('=' * 68)
print('IMMIGRANT PREMIUM BY MAJOR (with experience control, clean sample)')
print('  Controls: school FE + degree FE + avg_experience')
print('=' * 68)

rows = []
for major in sorted(us_clean['graduate_major'].unique()):
    sub = us_clean[us_clean['graduate_major'] == major]
    if sub['immigrant'].nunique() < 2 or len(sub) < 10:
        continue
    try:
        m = smf.ols('log_pay ~ immigrant + avg_experience + C(graduate_school) + C(graduate_degree)',
                    data=sub).fit()
        b  = m.params['immigrant']
        p  = m.pvalues['immigrant']
        ci = m.conf_int().loc['immigrant']
        gap = (np.exp(b)-1)*100
        cil = (np.exp(ci[0])-1)*100
        ciu = (np.exp(ci[1])-1)*100
        sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
        n_nat = int((sub['immigrant']==0).sum())
        n_imm = int((sub['immigrant']==1).sum())
        rows.append({'Major': major, 'N_native': n_nat, 'N_imm': n_imm,
                     'gap_%': round(gap,1), 'ci_lo': round(cil,1),
                     'ci_hi': round(ciu,1), 'p': round(p,4), 'sig': sig})
    except:
        pass

res = pd.DataFrame(rows).set_index('Major').sort_values('gap_%', ascending=False)
print(res.to_string())

# ================================================================
# STEP 5: TIER ANALYSIS — clean sample with experience
# ================================================================
print()
print('=' * 68)
print('TIER ANALYSIS (clean sample, with experience control)')
print('=' * 68)

ivy_elite = {
    'Harvard University','Massachusetts Institute of Technology',
    'Stanford University','Princeton University','Yale University',
    'Columbia University in the City of New York','University of Pennsylvania',
    'Cornell University','Dartmouth College','Brown University',
    'Duke University','Northwestern University','University of Chicago',
    'California Institute of Technology','Johns Hopkins University'
}
top50 = {
    'University of California-Berkeley','University of California-Los Angeles',
    'University of Michigan-Ann Arbor','Carnegie Mellon University',
    'New York University','Georgetown University','Vanderbilt University',
    'Emory University','Rice University','University of Notre Dame',
    'Washington University in St Louis','University of Virginia-Main Campus',
    'Tufts University','Boston University','Brandeis University',
    'Tulane University of Louisiana','University of Rochester',
    'Case Western Reserve University','Northeastern University',
    'University of Wisconsin-Madison','University of Illinois at Urbana-Champaign',
    'The University of Texas at Austin','Purdue University-Main Campus',
    'Ohio State University-Main Campus','University of Florida',
    'University of Georgia','University of North Carolina at Chapel Hill',
    'Georgia Institute of Technology-Main Campus',
    'University of California-San Diego','University of California-Davis',
    'Rensselaer Polytechnic Institute','Worcester Polytechnic Institute',
    'Stevens Institute of Technology','University of Minnesota-Twin Cities',
    'Pennsylvania State University-Main Campus',
    'University of California-Santa Barbara'
}

def tier(s):
    if s in ivy_elite: return '1. Ivy/Elite'
    if s in top50:     return '2. Top 50'
    return '3. Other'

us_clean['tier'] = us_clean['graduate_school'].apply(tier)

print('\nCell counts:')
tc = us_clean.groupby(['tier','immigrant']).size().unstack(fill_value=0)
tc.columns = ['Native','Immigrant']
tc['Total'] = tc.sum(axis=1)
print(tc)

print('\nAverage experience by tier and immigrant status:')
print(us_clean.groupby(['tier','immigrant'])['avg_experience'].mean().unstack().round(2))

print('\nRegression by tier (school + degree + major FE + experience):')
for t in ['1. Ivy/Elite','2. Top 50','3. Other']:
    sub = us_clean[us_clean['tier']==t].copy()
    if sub['immigrant'].nunique() < 2 or len(sub) < 20:
        print(f'  {t}: insufficient data')
        continue
    m = smf.ols('log_pay ~ immigrant + avg_experience + C(graduate_degree) + C(graduate_major)',
                data=sub).fit()
    b  = m.params['immigrant']
    p  = m.pvalues['immigrant']
    ci = m.conf_int().loc['immigrant']
    gap = (np.exp(b)-1)*100
    cil = (np.exp(ci[0])-1)*100
    ciu = (np.exp(ci[1])-1)*100
    sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
    print(f'  {t}: gap={gap:+.1f}%  CI[{cil:+.1f}%, {ciu:+.1f}%]  p={p:.4f} {sig}  N={int(m.nobs)}')
