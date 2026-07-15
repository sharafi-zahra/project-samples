import pandas as pd
import numpy as np
import scipy.stats as stats
from scipy.stats import ttest_ind

def native_img_comparison(df, vars):
    df = df.copy()
    df_img = df[df['img']==1]
    df_nat = df[df['img']==0]

    rslt = pd.DataFrame(columns=['Immigrant Avg', 'Immigrant Std', 'Immigrant N', 'Native Avg', 'Native Std', 'Native N', 'p-value'])

    for var in vars:
        if var not in df.columns:
            raise KeyError(f"Variable '{var}' not found in DataFrame")
        df_img_var = df_img[var].dropna()
        df_nat_var = df_nat[var].dropna()
        img_mean, img_std, img_n = df_img_var.mean(), df_img_var.std(), df_img_var.count()
        nat_mean, nat_std, nat_n = df_nat_var.mean(), df_nat_var.std(), df_nat_var.count()
        _, pval = ttest_ind(df_img_var, df_nat_var, equal_var=False)
        rslt.loc[var] = [img_mean, img_std, img_n, nat_mean, nat_std, nat_n, pval]

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