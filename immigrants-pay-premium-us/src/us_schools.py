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
# 1. SCHOOL OVERVIEW: cell counts by immigrant status
# ================================================================
print('=' * 72)
print('1. SCHOOL-LEVEL OVERVIEW (US only)')
print('   Sorted by total immigrant cells descending')
print('=' * 72)
school_counts = (us.groupby(['graduate_school', 'immigrant'])
                   .size().unstack(fill_value=0)
                   .rename(columns={0: 'native', 1: 'immigrant'}))
school_counts['total'] = school_counts.sum(axis=1)
school_counts['both_groups'] = (school_counts['native'] > 0) & (school_counts['immigrant'] > 0)

print(f'\nTotal schools: {len(school_counts)}')
print(f'Schools with ONLY native cells:    {(school_counts["immigrant"]==0).sum()}')
print(f'Schools with ONLY immigrant cells: {(school_counts["native"]==0).sum()}')
print(f'Schools with BOTH groups:          {school_counts["both_groups"].sum()}')

print('\nTop 40 schools by immigrant cell count:')
top40 = school_counts.sort_values('immigrant', ascending=False).head(40)
print(top40.to_string())

# ================================================================
# 2. WITHIN-SCHOOL GAP: raw avg pay difference (same school)
# ================================================================
print()
print('=' * 72)
print('2. WITHIN-SCHOOL RAW PAY GAP')
print('   Schools with >= 3 native AND >= 3 immigrant cells')
print('=' * 72)

school_pay = (us.groupby(['graduate_school', 'immigrant'])['avg_pay']
               .mean().unstack()
               .rename(columns={0: 'native_avg', 1: 'immigrant_avg'}))
school_pay = school_pay.dropna()
school_pay['gap_%'] = ((school_pay['immigrant_avg'] - school_pay['native_avg'])
                        / school_pay['native_avg'] * 100).round(1)

# Merge cell counts
school_pay = school_pay.join(school_counts[['native', 'immigrant']])
school_pay = school_pay[(school_pay['native'] >= 3) & (school_pay['immigrant'] >= 3)]
school_pay = school_pay.sort_values('gap_%', ascending=False)

print(f'\nSchools meeting threshold: {len(school_pay)}')
print()
print(school_pay[['native', 'immigrant', 'native_avg', 'immigrant_avg', 'gap_%']]
      .round(0).to_string())

# ================================================================
# 3. WITHIN-SCHOOL WITHIN-CELL GAP (same school + degree + major)
# ================================================================
print()
print('=' * 72)
print('3. WITHIN-SCHOOL WITHIN-CELL GAP (same school, degree, major)')
print('   For each school: mean gap across matched degree-major cells')
print('   Schools with >= 2 matched cells')
print('=' * 72)

us['cell'] = us['graduate_school'] + '||' + us['graduate_degree'] + '||' + us['graduate_major']
paired = (us.groupby(['graduate_school', 'cell', 'immigrant'])['avg_pay']
           .mean().unstack()
           .rename(columns={0: 'native_pay', 1: 'immigrant_pay'}))
paired = paired.dropna()
paired['gap_%'] = ((paired['immigrant_pay'] - paired['native_pay'])
                    / paired['native_pay'] * 100)

school_cell_summary = paired.groupby('graduate_school')['gap_%'].agg(
    mean_gap=lambda x: round(x.mean(), 1),
    median_gap=lambda x: round(x.median(), 1),
    n_matched_cells='count',
    pct_imm_higher=lambda x: round((x > 0).mean() * 100, 0)
)
school_cell_summary = school_cell_summary[school_cell_summary['n_matched_cells'] >= 2]
school_cell_summary = school_cell_summary.sort_values('mean_gap', ascending=False)

print(f'\nSchools with >= 2 matched cells: {len(school_cell_summary)}')
print()
print(school_cell_summary.to_string())

# ================================================================
# 4. REGRESSION: immigrant premium per school
#    log(pay) ~ immigrant + degree FE + major FE  (within each school)
# ================================================================
print()
print('=' * 72)
print('4. REGRESSION: immigrant premium within each school')
print('   log(pay) ~ immigrant + degree FE + major FE')
print('   Schools with >= 5 native AND >= 5 immigrant cells')
print('=' * 72)

eligible = school_counts[
    (school_counts['native'] >= 5) & (school_counts['immigrant'] >= 5)
].index.tolist()

print(f'\nSchools meeting threshold: {len(eligible)}')

rows = []
for school in eligible:
    sub = us[us['graduate_school'] == school].copy()
    try:
        m = smf.ols('log_pay ~ immigrant + C(graduate_degree) + C(graduate_major)',
                    data=sub).fit()
        b  = m.params['immigrant']
        p  = m.pvalues['immigrant']
        ci = m.conf_int().loc['immigrant']
        gap = (np.exp(b) - 1) * 100
        cil = (np.exp(ci[0]) - 1) * 100
        ciu = (np.exp(ci[1]) - 1) * 100
        sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
        rows.append({
            'School': school,
            'N_native': int((sub['immigrant']==0).sum()),
            'N_imm': int((sub['immigrant']==1).sum()),
            'gap_%': round(gap, 1),
            'ci_lo': round(cil, 1),
            'ci_hi': round(ciu, 1),
            'p': round(p, 4),
            'sig': sig,
            'R2': round(m.rsquared, 3)
        })
    except Exception as e:
        pass

res = pd.DataFrame(rows).set_index('School')
res = res.sort_values('gap_%', ascending=False)
print()
print(res.to_string())

# ================================================================
# 5. SCHOOL TIER ANALYSIS
# ================================================================
print()
print('=' * 72)
print('5. SCHOOL TIER ANALYSIS')
print('   Classify schools into tiers, compare immigrant premium')
print('=' * 72)

# Classify schools into broad tiers based on well-known rankings
ivy_elite = [
    'Harvard University', 'Massachusetts Institute of Technology',
    'Stanford University', 'Princeton University', 'Yale University',
    'Columbia University', 'University of Pennsylvania', 'Cornell University',
    'Dartmouth College', 'Brown University', 'Duke University',
    'Northwestern University', 'University of Chicago',
    'California Institute of Technology', 'Johns Hopkins University'
]

top50 = [
    'University of California-Berkeley', 'University of California-Los Angeles',
    'University of Michigan-Ann Arbor', 'Carnegie Mellon University',
    'New York University', 'Georgetown University', 'Vanderbilt University',
    'Emory University', 'Rice University', 'University of Notre Dame',
    'Washington University in St Louis', 'University of Virginia',
    'Wake Forest University', 'Tufts University', 'Boston University',
    'Brandeis University', 'Tulane University of Louisiana',
    'University of Rochester', 'Case Western Reserve University',
    'Northeastern University', 'Lehigh University',
    'University of Wisconsin-Madison', 'University of Illinois at Urbana-Champaign',
    'University of Texas at Austin', 'Purdue University-Main Campus',
    'Ohio State University-Main Campus', 'Penn State University Park',
    'University of Minnesota-Twin Cities', 'University of Florida',
    'University of Georgia', 'University of North Carolina at Chapel Hill',
    'William & Mary', 'Georgia Institute of Technology-Main Campus',
    'University of California-San Diego', 'University of California-Davis',
    'University of California-Santa Barbara', 'Rensselaer Polytechnic Institute',
    'Worcester Polytechnic Institute', 'Stevens Institute of Technology'
]

def tier(school):
    if school in ivy_elite:
        return '1. Ivy/Elite'
    elif school in top50:
        return '2. Top 50'
    else:
        return '3. Other'

us['tier'] = us['graduate_school'].apply(tier)

print('\nCell counts by tier:')
tier_counts = us.groupby(['tier','immigrant']).size().unstack(fill_value=0)
tier_counts.columns = ['native','immigrant']
tier_counts['total'] = tier_counts.sum(axis=1)
print(tier_counts)

print('\nAverage pay by tier and immigrant status:')
tier_pay = us.groupby(['tier','immigrant'])['avg_pay'].mean().unstack()
tier_pay.columns = ['native_avg','immigrant_avg']
tier_pay['raw_gap_%'] = ((tier_pay['immigrant_avg']-tier_pay['native_avg'])/tier_pay['native_avg']*100).round(1)
print(tier_pay.round(0))

print('\nRegression by tier (degree + major FE):')
for t in ['1. Ivy/Elite', '2. Top 50', '3. Other']:
    sub = us[us['tier']==t].copy()
    if sub['immigrant'].nunique() < 2 or len(sub) < 20:
        print(f'  {t}: insufficient data')
        continue
    m = smf.ols('log_pay ~ immigrant + C(graduate_degree) + C(graduate_major)', data=sub).fit()
    b  = m.params['immigrant']
    p  = m.pvalues['immigrant']
    ci = m.conf_int().loc['immigrant']
    gap = (np.exp(b)-1)*100
    cil = (np.exp(ci[0])-1)*100
    ciu = (np.exp(ci[1])-1)*100
    sig = '***' if p<.01 else '**' if p<.05 else '*' if p<.10 else 'ns'
    print(f'  {t}: gap={gap:+.1f}%  CI[{cil:+.1f}%,{ciu:+.1f}%]  p={p:.4f} {sig}  N={int(m.nobs)}')
