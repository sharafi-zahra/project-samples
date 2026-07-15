import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import ttest_ind

def male_female_comparison(df, vars):
    df = df.copy()
    df_female = df[df['Gender']=='Female']
    df_male = df[df['Gender']=='Male']

    rslt = pd.DataFrame(columns=['Female Avg', 'Female Std', 'Female N', 'Male Avg', 'Male Std', 'Male N', 'p-value'])

    for var in vars:
        if var not in df.columns:
            raise KeyError(f"Variable '{var}' not found in DataFrame")
        df_female_var = df_female[var].dropna()
        df_male_var = df_male[var].dropna()
        female_mean, female_std, female_n = df_female_var.mean(), df_female_var.std(), df_female_var.count()
        male_mean, male_std, male_n = df_male_var.mean(), df_male_var.std(), df_male_var.count()
        _, pval = ttest_ind(df_female_var, df_male_var, equal_var=False)
        rslt.loc[var] = [female_mean, female_std, female_n, male_mean, male_std, male_n, pval]

    return rslt

def likert_comparison(df, var,q_range):
    df = df.copy()
    vars = [f'{var}{i}' for i in range(1, q_range+1)]
    df[f'{var}_avg'] = df[vars].mean(axis=1)
    df[f'{var}_std'] = df[vars].std(axis=1)
    devs = [f'{var}{i}_devs' for i in range(1, q_range+1)]
    # Demean
    df[devs] = (df[vars].sub(df[f'{var}_avg'], axis=0))
    # Normalize
    df[devs] = df[devs].div(df[f'{var}_std'], axis=0)
    return df, devs