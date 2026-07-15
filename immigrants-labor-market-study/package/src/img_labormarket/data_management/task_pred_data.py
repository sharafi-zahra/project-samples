import pytask
import pandas as pd
import numpy as np
from scipy.stats import ttest_ind
from scipy import stats
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

from pathlib import Path
from img_labormarket.config import SRC, BLD
from img_labormarket.data_management.help_data import *


# Load the data
depends_on = [
    SRC / 'data' / 'dataset14.xlsx',
    SRC / 'data' / 'ValueCodings.xlsx',
    SRC / 'data' / 'ColumnLabels.xlsx',
    SRC / 'data' / 'CPI_Germany.xlsx'
]
produces = BLD / 'data' / 'clean_data.csv'

@pytask.mark.depends_on(depends_on)
@pytask.mark.produces(produces)
def task_prepare_data(depends_on,produces):
    # Load the data
    df = pd.read_excel(depends_on[0])
    # Remove data from analysis 
    del df['Q69r1oe']
    # Load the value codings
    mapping_df = pd.read_excel(depends_on[1])
    mapping_df['Frage'].fillna(method='ffill',inplace=True)

    # Generate img dummy
    df = construct_immigrant_dummy(df)
    # Nationality
    df = assign_nationality(df, mapping_df)

    # Add labels
    df = add_codings(df, mapping_df, 'Q1','Gender')
    df = add_codings(df, mapping_df, 'Q4_1','Degree')
    df['DegreeCompact'] = df['Degree'].replace({'Diplom':'Master','Magister':'Master'})
    # Field of Study
    df = recode_degrees(df)
    df['StudyFieldCluster'] = df['StudyField'].apply(assign_fine_cluster_grid)


    # Graduation Year
    df = add_codings(df, mapping_df, 'Q7_1r1','GradYear')
    # Job Search Duration
    df['job_search_months'] = df['Q19r1']
    # Start Job
    df['StartJobMonth'] = df['Q30r1']
    df = add_codings(df, mapping_df,'Q30_1r1','StartJobYear')
    # Graduation
    df['GradJobMonth'] = df['Q7r1']
    df = add_codings(df, mapping_df,'Q7_1r1','GradYear')

    df['DiffGradJobStart'] = (df['StartJobYear'].astype(int) - df['GradYear'].astype(int))*12 + (df['StartJobMonth'].astype(int) - df['GradJobMonth'].astype(int))

    # Wages
    # Read in CPI
    cpi = pd.read_excel(depends_on[3])
    df['StartYear'] = df['StartJobYear'].astype(int)
    df = pd.merge(df,cpi,left_on='StartYear',right_on='Year',how='left')
    df['first_wage'] = df['Q36r1']
    df['real_first_wage'] = (df['first_wage'] / df['CPI'])*100
    # Use potential monthly entries too
    df['new_first_wage'] = np.where(df['first_wage']<10,df['first_wage']*12,df['first_wage'])
    df['new_real_first_wage'] = (df['new_first_wage'] / df['CPI'])*100
    # Log Wage
    df['log_first_wage'] = np.where(df['first_wage'] > 0, np.log(df['first_wage']), np.nan)
    df['log_real_first_wage'] = np.where(df['real_first_wage'] > 0, np.log(df['real_first_wage']), np.nan)
    
    df['log_new_first_wage'] = np.where(df['new_first_wage'] > 0, np.log(df['new_first_wage']), np.nan)
    df['log_new_real_first_wage'] = np.where(df['new_real_first_wage'] > 0, np.log(df['new_real_first_wage']), np.nan)

    df['reservation_wage'] = df['Q26r1']
    df['real_reservation_wage'] = (df['reservation_wage'] / df['CPI'])*100

    # GPA
    df['GPA'] = df['Q13r1'].str.replace(',', '.').astype(float)
    # Age
    df = add_codings(df, mapping_df, 'Q64', 'Age')
    df['new_age'] = df['Age'].replace({'35-49 years':'35 years or older','50 years or older':'35 years or older'})

    # Job requires college degree
    df['job_requirement_college_degree'] = df['Q39'].apply(recode_requirement)

    # No applications
    df = add_codings(df,mapping_df,'Q22','no_applications')
    # Search distance
    df = add_codings(df, mapping_df, 'Q20', 'search_distance')

    # Outside Option
    df = comp_outside_option(df)

    # Minimum Wage
    df = add_min_wage(df)

    # Sector
    df = add_codings(df,mapping_df,'Q31_1','sector')
    # Code Other: into existing or clear bins
    df = handcode_sectors(df)
    # Language First Job
    df = add_codings(df, mapping_df, 'Q32r2','language_first_job')

    # Export it
    df.to_csv(produces,index=False)


def construct_immigrant_dummy(df):
    df['new_Q2'] = pd.to_numeric(df['new_Q2'], errors='coerce')
    df['new_Q3'] = pd.to_numeric(df['new_Q3'], errors='coerce')
    df['Q2_1c1'] = pd.to_numeric(df['Q2_1c1'], errors='coerce')
    df['Q3_1c1'] = pd.to_numeric(df['Q3_1c1'], errors='coerce')
    # Old values
    df['q2_old'] = np.where(((df['Q2_1c1'].notna()) & (df['Q2_1c1'] != 'FAIL') & (df['Q2_1c1'] != 'No Match')), 
                            np.where(df['Q2_1c1'] == 36, 1, 2), np.nan)
    df['q3_old'] = np.where(((df['Q3_1c1'].notna()) & (df['Q3_1c1'] != 'FAIL') & (df['Q3_1c1'] != 'No Match')), 
                            np.where(df['Q3_1c1'] == 36, 1, 2), np.nan)
    
    # Generating immigrant dummy
    df['img'] = np.where(
        ((df['q2_old'].isna()) & (df['q3_old'].isna())) & ((df['new_Q2'].isna()) & (df['new_Q3'].isna())),np.nan,
        np.where(
            ((df['new_Q2'] == 1) | (df['new_Q3'] == 1)) | ((df['q2_old'] == 1) | (df['q3_old'] == 1)), 
            0, 
            1
        ))
    ## Generating alternative dummies for possible use
    # Only classify if we have full info
    df['img_full_info'] = np.where(
        ((df['q2_old'].isna()) | (df['q3_old'].isna())) & ((df['new_Q2'].isna()) | (df['new_Q3'].isna())),np.nan,
        np.where(
            ((df['new_Q2'] == 1) | (df['new_Q3'] == 1)) | ((df['q2_old'] == 1) | (df['q3_old'] == 1)), 
            0, 
            1
        ))
    # Based on schooling only
    df['img_school'] = np.where(
        ((df['q3_old'].isna()) & (df['new_Q3'].isna())),np.nan,
        np.where(
            ((df['new_Q3'] == 1) | (df['q3_old'] == 1)), 
            0, 
            1
        ))
    # Based on birth only
    df['img_birth'] = np.where(
        ((df['q2_old'].isna()) & (df['new_Q2'].isna())),np.nan,
        np.where(
            ((df['new_Q2'] == 1) | (df['q2_old'] == 1)), 
            0, 
            1
        ))
    return df 

def assign_nationality(df, mapping_df):
    # Code
    df['born_country_code'] = np.where(df['new_Q2'] == 1, 36, 
                                 np.where(((df['Q2_1c1'].notna())&(df['Q2_1c1']!='FAIL')&(df['Q2_1c1']!='No Match')),df['Q2_1c1'], 
                                          df['Q70_1c1']))
    df['school_country_code'] = np.where(df['new_Q3'] == 1, 36, 
                                 np.where(((df['Q3_1c1'].notna())&(df['Q3_1c1']!='FAIL')&(df['Q3_1c1']!='No Match')),df['Q3_1c1'], 
                                          df['Q71_1c1']))
    # Actual country names
    # Create a dictionary for mapping values to labels
    wert_to_label = dict(zip(mapping_df[mapping_df['Frage'] == 'Q3_1c1']['Wert'],
                             mapping_df[mapping_df['Frage'] == 'Q3_1c1']['Label']))
    
    # Convert column to numeric, preserving NaN
    df['born_country'] = pd.to_numeric(df['born_country_code'], errors='coerce').astype('Int64')  # Keeps NaN as <NA>
    df['school_country'] = pd.to_numeric(df['school_country_code'], errors='coerce').astype('Int64')  # Keeps NaN as <NA>
    
    # Convert to string, ensuring <NA> remains unchanged
    df['born_country'] = df['born_country'].astype(str).apply(lambda x: wert_to_label.get(x, x) if x != '<NA>' else np.nan)
    df['school_country'] = df['school_country'].astype(str).apply(lambda x: wert_to_label.get(x, x) if x != '<NA>' else np.nan)

    # Labeling as EU or Non-EU
    eu_countries = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia", "Finland", "France",
    "Germany", "Greece", "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands",
    "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"
    }
    df["born_region"] = df["born_country"].apply(lambda x: "EU" if x in eu_countries else "Non-EU")

    return df

def recode_degrees(df):
    df = df.copy()
    degree_dict = {'Q6r1':'Engineering',
    'Q6r2':'Economics',
    'Q6r3':'Business',
    'Q6r4':'Finance',
    'Q6r5':'Management',
    'Q6r6':'Biology',
    'Q6r7':'Chemistry',
    'Q6r8':'Physics',
    'Q6r9':'Mathematics',
    'Q6r10':'Computer Science',
    'Q6r11':'Psychology',
    'Q6r12':'Education',
    'Q6r13':'Sociology',
    'Q6r14':'Political Science',
    'Q6r15':'Law',
    'Q6r16':'Medical Studies',
    'Q6r17':'Pharmaceutical Studies',
    }

    for old,new in degree_dict.items():
        df[new] = df[old]

    # Step 2: Replace 1s with column names, 0s with NaN
    degree_columns = list(degree_dict.values())
    df[degree_columns] = df[degree_columns].apply(lambda col: col.map(lambda x: col.name if x == 1 else np.nan))

    # Step 3: Create 'Fields of Study' column by combining non-null values into a list
    df['StudyField'] = df[degree_columns].apply(lambda row: row.dropna().tolist(), axis=1)

    return df 

# Step 4: Assign clusters based on the list of fields
def assign_cluster(fields):
    stem = {'Engineering', 'Biology', 'Chemistry', 'Physics', 'Mathematics', 'Computer Science','Medical Studies', 'Pharmaceutical Studies'}
    business = {'Business', 'Economics', 'Finance', 'Management'}
    social = {'Education', 'Sociology', 'Political Science', 'Law','Psychology'}

    if any(f in stem for f in fields):
        return 'STEM & Applied Sciences'
    elif any(f in business for f in fields):
        return 'Business & Economics'
    elif any(f in social for f in fields):
        return 'Social Sciences & Law'
    else:
        return 'Other'
    
def assign_new_cluster(fields):
    stem = {'Engineering', 'Biology', 'Chemistry', 'Physics', 'Mathematics', 'Computer Science','Medical Studies', 'Pharmaceutical Studies'}
    business = {'Business', 'Economics', 'Finance', 'Management'}
    social = {'Education', 'Sociology', 'Political Science', 'Law','Psychology'}

    if any(f in business for f in fields):
        return 'Business & Economics'
    elif any(f in stem for f in fields):
        return 'STEM & Applied Sciences'
    elif any(f in social for f in fields):
        return 'Social Sciences & Law'
    else:
        return 'Other'

def assign_fine_cluster_grid(fields):
    applied_stem = {'Engineering','Computer Science'}
    natural_science = {'Biology', 'Chemistry', 'Physics', 'Mathematics','Medical Studies', 'Pharmaceutical Studies'}
    #life_sciences = {'Medical Studies', 'Pharmaceutical Studies'}
    business = {'Business', 'Economics', 'Finance', 'Management'}
    social = {'Education', 'Sociology', 'Political Science', 'Law','Psychology'}

    if any(f in applied_stem for f in fields):
        return 'Engineering & CS'
    elif any(f in natural_science for f in fields):
        return 'Natural & Life Sciences'
    elif any(f in business for f in fields):
        return 'Business & Economics'
    elif any(f in social for f in fields):
        return 'Social Sciences & Law'
    else:
        return 'Other'
    
def comp_outside_option(df,last_val=40000):
    # Mapping of answer to value. The values are the midpoints of the categories except for the last one
    mapping = {
    1: 300,
    2: 900,
    3: 1800,
    4: 2950,
    5: 4200,
    6: 5400,
    7: 7500,
    8: 10500,
    9: 15000,
    10: 21000,
    11: 30000,
    12: last_val, 
    }

    # Ersetzen der Werte in der Spalte 'Q45_b' durch die Mittelpunkte
    df['RawOutsideOption'] = df['Q45_b'].replace(mapping)
    # Bedingte Logik basierend auf den Werten in 'Q1_label'
    df['OutsideOption'] = np.where(df['Q45_a'] == 1, df['RawOutsideOption'] ,
                            np.where(df['Q45_a'] == 2, 0,
                                     np.where(df['Q45_a'] == 3, -df['RawOutsideOption'] , np.nan)))
    return df

def recode_requirement(value):
    # Neue Kodierung: 1 = Kein Universitätsabschluss erforderlich, 2 = Universitätsabschluss erforderlich, 6 = Ich weiß es nicht
    if value in [1, 2, 3]:
        return 0
    elif value in [4, 5]:
        return 1
    elif value == 6:
        return np.nan
    else:
        return np.nan
    
def add_min_wage(df):
    # 
    min_hrl_wage_dict = {
        2018: 8.84,	
        2019: 9.19,	
        2020: 9.35,	
        2021: 9.60,	
        2022: 10.45,	
        2023: 12.00,	
        2024: 12.41,	
        2025: 12.82,
    }
    # Ensure StartJobYear is an integer column
    df['StartJobYear'] = pd.to_numeric(df['StartJobYear'], errors='coerce')
    min_weeks = 45
    min_hours = 35
    df['min_wage'] = df['StartJobYear'].apply(lambda x: (min_hrl_wage_dict.get(x, np.nan)*min_weeks*min_hours)/1000)
    return df

def handcode_sectors(df):
    df = df.copy()
    # Define a mapping for "Answer" to corresponding "Sector"
    answer_to_sector = {
        'Marktforschung':'Other', 
        'Ingenieursdienstleistungen':'Manufacturing and Industrial Engineering',
        'Soziales Dienste':'Public Sector', 
        'Verkehrsplanung':'Public Sector', 
        'Lean Management':'Other', 
        'Chemie':'Chemistry',
        'Öffentlicher Dienst': 'Public Sector', 
        'Rechtsdienstleister':'Other', 
        'Biotech':'Other',
        'Freizeitgestaltung':'Other', 
        'Gebäudemanagement':'Other', 
        'Lebensmittel':'Other',
        'Personaldienstleistung': 'HR', 
        'Versicherung': 'Financial Services and Banking', 
        'Baubranche': 'Construction and Real Estate Development',
        '(Online-)Handel': 'Telecommunications', 
        'Wirtschaftsprüfung': 'Financial Services and Banking', 
        'Construction': 'Construction and Real Estate Development',
        'Public Sector/Government': 'Public Sector', 
        'Bildung und Soziales':'Public Sector',
        'Arbeitssicherhet':'Other', 
        'Seefahrt':'Other', 
        'FMCG':'Other', 
        'Nachhaltigkeit im Handel':'Other',
        'Tourismus':'Other', 
        'Automobil':'Manufacturing and Industrial Engineering', 
        'Qualitätsmanagement':'Other', 
        'Hr':'HR',
        'Agrar und Gartenbau':'Other', 
        'Regionalentwicklung und -förderung':'Other',
        'Einzelhandel':'Other', 
        'Öffentliche Verwaltung':'Public Sector', 
        'Landschaftsarchitektur':'Other',
        'Mobilität':'Other', 
        'Öffentlicher Dienst Stadtbauamt':'Public Sector', 
        'Politik':'Public Sector',
        'Projektmanagement':'Other', 
        'Gastronomie Management':'Other',
        'Versicherung (Lebensversicherung)':'Financial Services and Banking', 
        'Politik und Verwaltung':'Public Sector',
        'Politikberatung und Programmmanagement':'Public Sector', 
        'Personalmanagement':'HR',
        'Verlagsbranche':'Other', 
        'Schienenfahrzeugtechnik':'Other', 
        'Steuern': 'Financial Services and Banking',
        'Assistant to management':'Other',
        'Mitarbeiter bei BLG Logistics. Neben job':'Logistics and Supply Chain Management', 
        'Quality Management':'Other',
        'Media and entertainment':'Other', 
        'Non profit sector':'Other', 
        'FANG':'Other',
        'Venture Capital': 'Financial Services and Banking', 
        'Einzelhandelsmanagement':'Other',
        'Hardwareentwicklung':'Technology and Software Development', 
        'Aviation':'Other', 
        'Art Gallery':'Other', 
        'Architecture':'Other',
        'International cooperation':'Other', 
        'Market Research':'Other',
        'Sport consumer goods':'Other', 
        'Scientific research':'Science sector',
        'Automative Engineering':'Manufacturing and Industrial Engineering',
        'Education/University administration support':'Public Sector', 
        'Hr and recruiting':'HR',
        'Financial Services and Banking':'Financial Services and Banking', 
        'Forschung & Entwicklung':'Other', 
        'Education':'Public Sector', 
        'Automotive':'Manufacturing and Industrial Engineering',
        'Journalism':'Other', 
        'Food':'Other', 
        'Sales advisor':'Other', 
        'Medical technology':'Healthcare and Pharmaceuticals',
        'Language services':'Other', 
        'EPR and environment sustainability':'Other',
        'Analytical Chemistry':'Chemistry', 
        'Graphic and Motion Design':'Other',
        'Railway Engineering':'Manufacturing and Industrial Engineering', 
        'Research and Education':'Science sector', 
        'R&D industrial':'Manufacturing and Industrial Engineering',
        'Mechanical Engineering':'Manufacturing and Industrial Engineering', 
        'Mobility':'Other',
        'Certification body/Supply chain control':'Logistics and Supply Chain Management'
    # Add more mappings as needed
    }

    # Only replace "Other" values in "Sector" based on the mapping
    df["new_sector"] = df["sector"].replace("Others:", np.nan)  # Temporarily set "Other" to NaN
    df["new_sector"] = df["new_sector"].fillna(df["Q31_1r12oe"].map(answer_to_sector))  # Fill NaN with map

    coarse_sector_dict = {
    'Technology and Software Development':'Technology and Software Development',
    np.nan:'Other',
    'Science sector':'Science',
    'Consulting':'Consulting',
    'Manufacturing and Industrial Engineering':'Engineering',
    'Financial Services and Banking':'Finance and Banking',
    'Marketing and Advertising':'Marketing and Advertising',
    'Healthcare and Pharmaceuticals':'Healthcare and Pharmaceuticals',
    'Logistics and Supply Chain Management':'Other',
    'Civil Engineering':'Engineering',
    'Energy and Utilities':'Other',
    'Construction and Real Estate Development':'Other',
    'Telecommunications':'Other'  
    }
    df["sector_coarse"] = df["new_sector"].map(coarse_sector_dict)
    df['sector_coarse'] = df['sector_coarse'].fillna('Not Specified')

    return df