import pandas as pd
import numpy as np

def add_codings(df, mapping_df, col_name, new_col_name=None):
    # Create a dictionary for mapping values to labels
    wert_to_label = dict(zip(mapping_df[mapping_df['Frage'] == col_name]['Wert'],
                             mapping_df[mapping_df['Frage'] == col_name]['Label']))
    
    # Convert column to numeric, preserving NaN
    df[col_name] = pd.to_numeric(df[col_name], errors='coerce').astype('Int64')  # Keeps NaN as <NA>
    
    # Convert to string, ensuring <NA> remains unchanged
    str_col = df[col_name].astype(str).apply(lambda x: wert_to_label.get(x, x) if x != '<NA>' else x)

    str_col = str_col.replace('<NA>', np.nan)
    # Assign to the specified new column or default label column
    if new_col_name:
        df[new_col_name] = str_col
    else:
        df[col_name + '_label'] = str_col
    
    return df

def restrict_wage(df, var, lower=15, upper=150):
    df = df.copy()
    df = df[(df[var] >= lower) & (df[var] <= upper)]
    return df
