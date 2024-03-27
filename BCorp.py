import os
import datadotworld as dw
import pandas as pd
import country_converter as coco
import polars as pl
import streamlit as st
import numpy as np
from sklearn.preprocessing import MinMaxScaler

DATA_CACHE_PATH = "/tmp/bcorp_data.parquet"

###with help from chat
activities_industries = {
    'employment placement & HR': 'Business Services',
    'Information, communication & technology': 'Technology',
    'Professional & technical services': 'Business Services',
    'Computer programming services': 'Technology',
    'Human health & social work': 'Healthcare and Pharmaceuticals',
    'Healthcare and Pharmaceuticals': 'Healthcare and Pharmaceuticals',
    'Retail': 'Consumer Goods',
    'Management consultant - for-profits': 'Business Services',
    'Education': 'Education, Non-Profit, Government, Public etc.',
    'Transportation & storage' : 'Transportation and Logistics',
    'Publishing - Print': 'Media and Entertainment',
    'Rental & Repair': 'Consumer Services',
    'Waste Management & Recycling': 'Environment and Energy',
    'Wholesale': 'Consumer Goods',
    'Administrative & support services': 'Business Services',
    'Real estate, design & building': 'Real Estate',
    'Energy': 'Environment and Energy',
    'Energy, Heating & Cooling': 'Environment and Energy',
    'Food products': 'Consumer Goods',
    'Arts, entertainment & recreation': 'Leisure and Recreation',
    'Manufactured Goods': 'Consumer Goods',
    'Agricultural Processing': 'Agriculture and Forestry',
    'Accommodation & food service' :'Media and Entertainment',
    'Education & training services': 'Education, Non-Profit, Government, Public etc.',
    'Other retail sale': 'Consumer Goods',
    'Rent/lease: other goods': 'Business Services',
    'Construction': 'Construction and Materials',
    'Architecture design & planning': 'Construction and Materials',
    'Personal care products': 'Consumer Goods',
    'Environmental consulting': 'Environment and Energy',
    'Investment advising': 'Financial Services and Banking',
    'Civil engineering': 'Construction and Materials',
    'Agriculture, forestry & fishing': 'Agriculture and Fishing',
    'Accounting & auditing': 'Business Services',
    'Other services': 'Business Services',
    'Other business support': 'Business Services',
    'Apparel': 'Consumer Goods',
    'Higher education': 'Education, Non-Profit, Government, Public etc.',
    'Sports goods': 'Consumer Goods',
    'Deposit bank - Developed Markets': 'Financial Services and Banking',
    'Financial & insurance activities': 'Financial Services and Banking',
    'Other renewable energy installation': 'Environment and Energy',
    'Legal activities': 'Business Services',
    'Transportation support': 'Transportation and Logistics',
    'Furniture': 'Consumer Goods',
    'Veterinary activities': 'Agriculture and Fishing',
    'Other financial services': 'Financial Services and Banking',
    'Other manufacturing': 'Industrial and Manufacturing',
    'Textiles': 'Consumer Goods',
    'Life insurance': 'Financial Services and Banking',
    'Other info service activities': 'Technology',
    'Equity investing - Developed Markets': 'Financial Services and Banking',
    'Travel agency & related': 'Leisure and Recreation',
    'Advertising & market research': 'Business Services',
    'Technology-based support services': 'Technology',
    'Beverages': 'Agriculture and Fishing',
    'Other transport equipment': 'Industrial and Manufacturing',
    'Books or other media': 'Media and Entertainment',
    'Restaurants & food service': 'Consumer Services',
    'Hairdressing & other beauty services': 'Consumer Services',
    'Film, TV & music production': 'Media and Entertainment',
    'General retail via Internet': 'Consumer Goods',
    'Computer & electronic products': 'Technology',
    'Other professional, scientific & tech': 'Business Services',
    'Health insurance': 'Healthcare and Pharmaceuticals',
    'Rubber & plastics products': 'Industrial and Manufacturing',
    'Pharmaceutical products': 'Healthcare and Pharmaceuticals',
    'Facilities & cleaning services': 'Business Services',
    'Software publishing and SaaS platforms': 'Technology',
    'Chemicals & chemical products': 'Industrial and Manufacturing',
    'Other human health': 'Education, Non-Profit, Government, Public etc.',
    'Emergency services': 'Healthcare and Pharmaceuticals',
    'Home health care': 'Healthcare and Pharmaceuticals',
    'Printing & recorded media': 'Media and Entertainment',
    'Other power generation': 'Environment and Energy',
    'Scientific R&D': 'Education, Non-Profit, Government, Public etc.',
    'Web portals': 'Technology',
    'Real estate - leased property': 'Real Estate',
    'Other personal services': 'Consumer Services',
    'Engineering': 'Construction and Materials',
    'Medical & dental practice': 'Healthcare and Pharmaceuticals',
    'Paper & paper products': 'Industrial and Manufacturing',
    'Accommodation': 'Consumer Services',
    'Waste collection': 'Environment and Energy',
    'Social networks & info sharing': 'Technology',
    'Other install & construction': 'Construction and Materials',
    'Design & building': 'Construction and Materials',
    'Computers & electronics': 'Technology',
    'Wood & wood products': 'Industrial and Manufacturing',
    'Growing perennial crops': 'Agriculture and Forestry',
    'Cleaning products': 'Consumer Goods',
    'Social Work': 'Education, Non-Profit, Government, Public etc.',
    'Telecommunications': 'Telecommunications',
    'Laundry & dry-cleaning': 'Consumer Services',
    'Publishing - newspapers & magazines': 'Media and Entertainment',
    'Educational support': 'Education, Non-Profit, Government, Public etc.',
    'Equity investing - Emerging Markets': 'Financial Services and Banking',
    'Waste treatment & disposal': 'Environment and Energy',
    'Other education': 'Education, Non-Profit, Government, Public etc.',
    'Membership organizations': 'Education, Non-Profit, Government, Public etc.',
    'Pension/retirement plans': 'Financial Services and Banking',
    'Mobile applications': 'Technology',
    'Data processing & hosting': 'Technology',
    'Solar panel installation': 'Environment and Energy',
    'Machinery & equipment': 'Industrial and Manufacturing',
    'Pre- & primary education': 'Education, Non-Profit, Government, Public etc.',
    'Landscape services': 'Consumer Services',
    'Medical & dental supplies': 'Healthcare and Pharmaceuticals',
    'Postal & courier activities': 'Transportation and Logistics',
    'Arts & entertainment': 'Leisure and Recreation',
    'Real estate development': 'Real Estate',
    'Other publishing activities': 'Media and Entertainment',
    'Electrical equipment': 'Industrial and Manufacturing',
    'Materials recovery & recycling': 'Environment and Energy',
    'Agricultural support/post-harvest': 'Agriculture and Forestry',
    'Other insurance services': 'Financial Services and Banking',
    'Other/general wholesale trade': 'Business Services',
    'Construction': 'Construction and Materials',
    'Financial transaction processing': 'Financial Services and Banking',
    'Contracting & building': 'Construction and Materials'}

def load_data() -> pl.DataFrame:
    if os.path.exists(DATA_CACHE_PATH):
        return pl.read_parquet(DATA_CACHE_PATH)
    else:
        sql_query = "SELECT * FROM `b_corp_impact_data`"
        result_set = dw.query("blab/b-corp-impact-data", sql_query)
        df = result_set.dataframe
        df.to_parquet(DATA_CACHE_PATH)
        return pl.from_pandas(df)

def process_data() -> pl.DataFrame:
    df = load_data()
    df = df.filter(
    (pl.col("current_status").cast(str) == "certified") & (pl.col("certification_cycle") == 1)
    )

    # Convert relevant columns to numeric type, preserving NaN values
    df = df.with_columns(
        [
            pl.col("^(ia_|impact_area_|overall_score).*$").cast(pl.Float64, strict=False)
        ]
    )

    # Consolidate rows, treating NaN values as zeros
    consolidated_columns = {
        "B Corp Impact - Community Diversity & Inclusion": [
            "ia_community_it_diversity_equity_inclusion",
            "ia_community_it_diversity_inclusion"
        ],
        "B Corp Impact - Community Involvement": [
            "ia_community_it_local_involvement",
            "ia_community_it_local_economic_development",
            "ia_community_it_economic_impact",
            "ia_community_it_national_economic_development",
            "ia_workers_it_workforce_development"
        ],
        "B Corp Impact - Customers Impact In Need & Underserved": [
            "ia_customers_it_basic_services_for_the_underserved",
            "ia_customers_it_business_model_and_engagement",
            "ia_customers_it_impact_improvement",
            "ia_customers_it_serving_in_need_populations",
            "ia_customers_it_serving_underserved_populations",
            "ia_customers_it_serving_underserved_populations_direct",
            "ia_customers_it_support_for_underserved_purpose_driven_enterprises"
        ],
        "B Corp Impact - Customer Education": [
            "ia_customers_it_education",
            "ia_customers_it_educational_models_and_engagement",
            "ia_customers_it_educational_outcomes",
            "ia_customers_it_student_outcomes",
            "ia_customers_it_student_experience"
        ],
        "B Corp Impact - Customers Health": [
            "ia_customers_it_health",
            "ia_customers_it_health_outcomes",
            "ia_customers_it_health_wellness_improvement"
        ],
        "B Corp Impact - Governance Board Diversity": [
            "ia_governance_it_governance",
            "ia_governance_it_corporate_accountability"
        ],
        "B Corp Impact - Governance Ethics": [
            "ia_governance_it_ethics_transparency",
            "ia_governance_it_ethics"
        ],
        "B Corp Impact - Workers Development & Communication": [
            "ia_workers_it_job_flexibility_corporate_culture",
            "ia_workers_it_engagement_satisfaction",
            "ia_workers_it_career_development",
            "ia_workers_it_management_worker_communication",
            "ia_workers_it_training_education"
        ],
        "B Corp Impact - Workers Benefits": [
            "ia_workers_it_worker_benefits",
            "ia_workers_it_benefits"
        ],
        "B Corp Impact - Workers Fair Pay": [
            "ia_workers_it_compensation_wages",
            "ia_workers_it_financial_security"
        ],
        "B Corp Impact - Workers Health & Safety": [
            "ia_workers_it_occupational_health_safety",
            "ia_workers_it_human_rights_labor_policy",
            "ia_workers_it_health_wellness_safety"
        ],
        "B Corp Impact - Workers Worker Owned": [
            "ia_workers_it_worker_ownership",
            "ia_workers_it_worker_owned"
        ]
    }

    for new_col, old_cols in consolidated_columns.items():
        expressions = [pl.col(col) for col in old_cols]
        sum_expression = pl.fold(pl.lit(0), lambda acc, expr: acc + expr.fill_null(pl.lit(0)), expressions)
        all_null_mask = pl.fold(pl.lit(True), lambda acc, expr: acc & expr.is_null(), expressions)
        final_expression = pl.when(all_null_mask).then(None).otherwise(sum_expression)
        df = df.with_columns(final_expression.alias(new_col))



    # Drop unnecessary columns
    columns_to_drop = [
        "certification_cycle",
        "current_status",
        "date_certified",
        "products_and_services",
        "company_id",
        "assessment_year",
        "state",
        "sector",
        "assessment_year",
        "impact_area_community_na_score",
        "impact_area_customers_na_score",
        "impact_area_environment_na_score",
        "impact_area_governance_na_score",
        "impact_area_workers_na_score",
        "ia_community_it_diversity_equity_inclusion",
        "ia_community_it_diversity_inclusion",
        "ia_community_it_local_involvement",
        "ia_community_it_local_economic_development",
        "ia_community_it_economic_impact",
        "ia_community_it_national_economic_development",
        "ia_workers_it_workforce_development",
        "ia_customers_it_basic_services_for_the_underserved",
        "ia_customers_it_business_model_and_engagement",
        "ia_customers_it_impact_improvement",
        "ia_customers_it_serving_in_need_populations",
        "ia_customers_it_serving_underserved_populations",
        "ia_customers_it_serving_underserved_populations_direct",
        "ia_customers_it_support_for_underserved_purpose_driven_enterprises",
        "ia_customers_it_education",
        "ia_customers_it_educational_models_and_engagement",
        "ia_customers_it_educational_outcomes",
        "ia_customers_it_student_outcomes",
        "ia_customers_it_student_experience",
        "ia_customers_it_health",
        "ia_customers_it_health_outcomes",
        "ia_customers_it_health_wellness_improvement",
        "ia_governance_it_governance",
        "ia_governance_it_corporate_accountability",
        "ia_governance_it_ethics_transparency",
        "ia_governance_it_ethics",
        "ia_workers_it_job_flexibility_corporate_culture",
        "ia_workers_it_engagement_satisfaction",
        "ia_workers_it_career_development",
        "ia_workers_it_management_worker_communication",
        "ia_workers_it_training_education",
        "ia_workers_it_worker_benefits",
        "ia_workers_it_benefits",
        "ia_workers_it_compensation_wages",
        "ia_workers_it_financial_security",
        "ia_workers_it_occupational_health_safety",
        "ia_workers_it_human_rights_labor_policy",
        "ia_workers_it_health_wellness_safety",
        "ia_workers_it_worker_ownership",
        "ia_workers_it_worker_owned"
    ]
    df = df.drop(columns_to_drop)

    # Rename columns
    rename_dict = {
        "company_name": "Company",
        "date_first_certified": "First Certified as B Corp",
        "overall_score": "B Corp Impact - Overall Score",
        "b_corp_profile": "B Corp Webpage",
        "impact_area_community": "B Corp Impact - Community",
        "impact_area_customers": "B Corp Impact - Customers",
        "impact_area_environment": "B Corp Impact - Environment",
        "impact_area_governance": "B Corp Impact - Governance",
        "impact_area_workers": "B Corp Impact - Workers"
    }
    df = df.rename(rename_dict)

    new_column_names = {
        col: "B Corp Impact - " + col.replace("ia_", "").replace("_it_", " ").replace("_", " ").title()
        for col in df.columns if "ia_" in col
    }
    df = df.rename(new_column_names)

    return df

def scale_data(df: pl.DataFrame) -> pl.DataFrame:
    minmax = MinMaxScaler(feature_range=(0, 1))
    arr_df = df.select(pl.col("^B Corp Impact.*$"))
    arr = arr_df.to_numpy()
    mask = ~pl.DataFrame(arr).select(pl.col('*').is_null()).to_numpy()
    arr_2d = arr[mask].reshape(-1, arr.shape[1])
    minmax.fit(arr_2d)

    scaled_arr = arr.copy()
    scaled_arr[mask] = minmax.transform(arr_2d).reshape(-1)

    df = pl.concat(
        [
            df.select(pl.exclude(arr_df.columns)),
            pl.from_numpy(scaled_arr, schema=arr_df.schema)
        ],
        how='horizontal'
    )

    return df

df = process_data()
df = scale_data(df)

###Def Industries
def industries(df, activities_industries):
    # Step 1: Map 'industry' to 'Industry'
    df = df.with_columns(pl.col('industry').apply(activities_industries.get).alias('Industry'))
    df = df.with_columns(pl.when(pl.col('Industry').is_null() & pl.col('industry_category').apply(activities_industries.get).is_not_null())
                        .then(pl.col('industry_category').apply(activities_industries.get))
                        .otherwise(pl.col('Industry')).alias('Industry'))
    df = df.with_columns(pl.when(pl.col('Industry').is_null() & pl.col('Company').apply(activities_industries.get).is_not_null())
                        .then(pl.col('Company').apply(activities_industries.get))
                        .otherwise(pl.col('Industry')).alias('Industry'))
    return df
df = industries(df, activities_industries)
df = df.drop('industry_category', 'industry')


###Def Countries
df = df.with_columns(pl.col('country').apply(lambda x: 'Netherlands' if x == 'Netherlands The' else ('Croatia' if x == 'Croatia (Hrvatska)' else x)).alias('country'))
unique_countries = df['country'].unique()
converted_names = coco.convert(names=unique_countries, to='name_short')
converted_continents = coco.convert(names=unique_countries, to='Continent_7')
name_mapping = dict(zip(unique_countries, converted_names))
continent_mapping = dict(zip(unique_countries, converted_continents))
df =df.with_columns(pl.col('country').apply(lambda x: name_mapping.get(x, x)).alias('Country'))
df = df.with_columns(pl.col('country').apply(lambda x: continent_mapping.get(x, x)).alias('Region'))


###Def Size
df = df.to_pandas()
def calculate_size_score(row):
    size = row['size']
    country = row['country']
    region = row.get('Region', None)

    # Corrected logic for size comparison
    if size == '0' or size == '1-9':
        if region == 'Europe' or country == 'Ireland':
            return -10
        elif country == 'United Kingdom':
            return -5
        else:
            return -15
    elif size == '10-49':
        if region == 'Europe' or country == 'Ireland':
            return 0
        elif country == 'United Kingdom':
            return 10
        else:
            return -10
    elif size == '50-249':
        if region == 'Europe' or country == 'Ireland':
            return 5
        elif country == 'United Kingdom':
            return 15
        else:
            return 0
    elif size == '250-999':
        if region == 'Europe' or country == 'Ireland' or country == 'United States':
            return 15
        elif country == 'United Kingdom':
            return 25
        else:
            return 0
    elif size == '1000+':
        if region == 'Europe' or country == 'Ireland' or country == 'United States':
            return 10
        elif country == 'United Kingdom':
            return 15
        else:
            return 5
    else:
        return 0

# Assuming df is your DataFrame and already converted to a pandas DataFrame
# Apply the fixed function
df['size_score'] = df.apply(lambda row: calculate_size_score(row), axis=1)

# Normalizing size_score to get Size Score between 0 and 1
min_val_size = df['size_score'].min()
max_val_size = df['size_score'].max()
df['Size Score'] = (df['size_score'] - min_val_size) / (max_val_size - min_val_size)




#def industry_score
def industry_score(args):
    industry, country, Region = args
    if industry == 'Healthcare and Pharmaceuticals':
        if country == 'United Kingdom':
            return 50
        elif Region == 'Europe' or country in ['Ireland', 'United States']:
            return 30
        else:
            return 10
    if industry in ['Consumer Goods', 'Media and Entertainment', 'Leisure and Recreation']:
        if country == 'United Kingdom':
            return 20
        elif Region == 'Europe' or country in ['Ireland', 'United States']:
            return 20
        else:
            return -10
    if industry in ['Financial Services and Banking','Consumer Services', 'Technology' ]:
        if country == 'United Kingdom':
            return 10
        elif Region == 'Europe' or country in ['Ireland', 'United States']:
            return 0
        else:
            return -15
    if industry in ['Business Services', 'Telecommunications', 'Real Estate', 'Education, Non-Profit, Government, Public etc']:
        if country == 'United Kingdom':
            return 5
        elif Region == 'Europe' or country in ['Ireland', 'United States']:
            return -5
        else:
            return -20
    if industry in ['Construction and Materials', 'Agriculture and Forestry', 'Transportation and Logistics','Industrial and Manufacturing', 'Automotive and Parts']:
        if country == 'United Kingdom':
            return 5
        else:
            return -30
    if industry in ['Environment and Energy']:
        if country == 'United Kingdom':
            return 0
        elif Region == 'Europe' or country in ['Ireland', 'United States']:
            return -10
        else:
            return -40
    if industry in ['Aerospace and Defense', 'Tobacco']:
        if country == 'United Kingdom':
            return 0
        elif Region == 'Europe' or country in ['Ireland', 'United States']:
            return -20
        else:
            return -50
    return -30
df['industry_score'] = df[['Industry', 'Country', 'Region']].apply(industry_score, axis=1)
min_val_industry = df['industry_score'].min()
max_val_industry = df['industry_score'].max()
df['Industry Score'] = (df['industry_score'] - min_val_industry) / (max_val_industry - min_val_industry)

##filter
if 'B Corp Impact - Overall Score' in df.columns:
    bottom_quartile = df['B Corp Impact - Overall Score'].quantile(0.25)
    top_quartile = df['B Corp Impact - Overall Score'].quantile(0.75)

    # Define the bottom and top quartiles
    cond_europe = df['Region'].isin(['Europe', 'Great Britain & Ireland'])
    cond_bottom_quartile = df['B Corp Impact - Overall Score'] <= bottom_quartile
    df = df[df['Size Score'] >= 0]
    df = df[~(cond_europe & cond_bottom_quartile)]
else:
    print("The 'B Corp Impact - Overall Score' column does not exist in the dataframe.")


##columns
quad_columns = ['Size Score', 'Industry Score','B Corp Impact - Community Designed To Give', 'B Corp Impact - Customer Education',
                'B Corp Impact - Community Diversity & Inclusion', 'B Corp Impact - Customers', 'B Corp Impact - Community', 'B Corp Impact - Overall Score', 'B Corp Impact - Customers Health'
                ]

double_columns = ['B Corp Impact - Community Supply Chain Poverty Alleviation', 'B Corp Impact - Customers Quality And Continuous Improvement',
                  'B Corp Impact - Community Designed For Charitable Giving',
                  'B Corp Impact - Community Microdistribution Poverty Alleviation','B Corp Impact - Customers Improved Impact',
                  'B Corp Impact - Customers Privacy And Consumer Protection', 'B Corp Impact - Customers Economic Empowerment For The Underserved',
                  'B Corp Impact - Environment', 'B Corp Impact - Customers Positive Impact', 'B Corp Impact - Community Job Creation', 'B Corp Impact - Workers Benefits',
                  'B Corp Impact - Community Producer Cooperative', 'B Corp Impact - Governance Mission Engagement',
                  'B Corp Impact - Customers Arts Medculture',
                  'B Corp Impact - Customers Marketing Recruiting And Transparency','B Corp Impact - Customers Mission Lock',
                  'B Corp Impact - Workers Fair Pay']

triple_columns = ['B Corp Impact - Governance', 'B Corp Impact - Workers',
                'B Corp Impact - Community Civic Engagement Giving', 'B Corp Impact - Governance Mission Locked',
                'B Corp Impact - Community Involvement', 'B Corp Impact - Governance Ethics',
                'B Corp Impact - Customers Customer Stewardship',
                'B Corp Impact - Workers Health & Safety',
                'B Corp Impact - Customers Impact In Need & Underserved', 'B Corp Impact - Governance Transparency']
culture_columns = [
        'B Corp Impact - Overall Score', 'B Corp Impact - Customers', 'B Corp Impact - Community', 'B Corp Impact - Workers', 'Size Score', 'Industry Score',
        'B Corp Impact - Workers Health & Safety', 'B Corp Impact - Customer Education',
        'B Corp Impact - Customers Mission Lock','B Corp Impact - Customers Health',
        'B Corp Impact - Customers Positive Impact', 'B Corp Impact - Customers Quality And Continuous Improvement',
        'B Corp Impact - Community Designed To Give', 'B Corp Impact - Community Diversity & Inclusion',
        'B Corp Impact - Community Civic Engagement Giving', 'B Corp Impact - Environment Toxin Reduction Remediation',
        'B Corp Impact - Environment Training Collaboration', 'B Corp Impact - Workers Worker Owned', 'B Corp Impact - Customers Arts Medculture', 'B Corp Impact - Environment Green Investing',
        'B Corp Impact - Governance Board Diversity'

]

capacity_columns = ['B Corp Impact - Customers', 'B Corp Impact - Workers', 'B Corp Impact - Community Job Creation','B Corp Impact - Community Designed For Charitable Giving', 'Size Score',
                        'B Corp Impact - Workers Fair Pay',
                    'B Corp Impact - Customers Impact In Need & Underserved', 'B Corp Impact - Customers Customer Stewardship', 'B Corp Impact - Community Microfranchise Poverty Alleviation',
                    'B Corp Impact - Workers Benefits',  'B Corp Impact - Workers Development & Communication', 'B Corp Impact - Community Supply Chain Management',
                     'B Corp Impact - Environment Environmental Education Information'
]

conduct_columns = ['B Corp Impact - Governance', 'B Corp Impact - Governance Transparency', 'B Corp Impact - Community Involvement', 'Industry Score',
                   'B Corp Impact - Community Microdistribution Poverty Alleviation','B Corp Impact - Customers Improved Impact',
                   'B Corp Impact - Governance Ethics', 'B Corp Impact - Governance Board Diversity', 'B Corp Impact - Customers Customer Stewardship',
                   'B Corp Impact - Customers Privacy And Consumer Protection', 'B Corp Impact - Customers Marketing Recruiting And Transparency',
                    'B Corp Impact - Environment Safety', 'B Corp Impact - Environment Inputs', 'B Corp Impact - Environment Outputs','B Corp Impact - Governance Mission Engagement']


collaboration_columns = ['B Corp Impact - Community', 'B Corp Impact - Customers', 'B Corp Impact - Overall Score',
                         'B Corp Impact - Governance Mission Locked',
                         'B Corp Impact - Community Producer Cooperative', 'B Corp Impact - Customers Leadership Outreach',
                         'B Corp Impact - Customers Economic Empowerment For The Underserved',
                         'B Corp Impact - Community Supply Chain Poverty Alleviation',
                         'B Corp Impact - Community Designed For Charitable Giving',
                          'B Corp Impact - Community Suppliers Distributors Product',
                          'B Corp Impact - Customers Mission Aligned Exit',
                          'Size Score', 'Industry Score', 'B Corp Impact - Environment Community',
                          'B Corp Impact - Workers Health & Safety',
                          'B Corp Impact - Community Civic Engagement Giving'
                         ]
df_copy = df.copy()
def calculate_scores(df, culture_columns, capacity_columns, conduct_columns, collaboration_columns, double_columns, triple_columns, quad_columns):
    df_copy[double_columns] *= 2
    df_copy[triple_columns] *= 3
    df_copy[quad_columns] *= 4

    scores = {}
    for group_name, columns in zip(
        ['Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score'],
        [culture_columns, capacity_columns, conduct_columns, collaboration_columns]
    ):
        actual_scores = df_copy[columns]
        actual_scores = actual_scores.mask(actual_scores.isnull(), 0)
        actual_sum = actual_scores.sum(axis=1)
        max_scores = df_copy[columns].notnull().astype(int)
        max_sum = max_scores.sum(axis=1)
        scores[group_name] = actual_sum.div(max_sum.replace(0, 1)).mul(100)

    scores_df = pd.DataFrame(scores)
    return pd.concat([df_copy, scores_df], axis=1)

def adjust_scores(row, lower_quantile, upper_quantile, size_lower_quantile, size_upper_quantile, apply_country=True, apply_industry=True, apply_size=True):
    adjusted_scores = {}
    for score_name in ['Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score']:
        base_score = row[score_name]

        if row['B Corp Impact - Overall Score'] <= lower_quantile:
            base_score *= 0.8
        elif row['B Corp Impact - Overall Score'] >= upper_quantile:
            base_score *= 1.20

        if apply_country and 'Country' in row:
            if row['Country'] == 'United Kingdom':
                base_score *= 1.20
            else:
                base_score *= 0.9

        if apply_industry and 'Industry' in row and score_name in ['Culture Score', 'Collaboration Score']:
            if row['Industry'] == 'Healthcare and Pharmaceuticals':
                base_score *= 1.35
            elif row['Industry'] in ['Consumer Goods', 'Media and Entertainment']:
                base_score *= 1.15
            elif row['Industry'] in ['Consumer Services']:
                base_score *= 1.05

        if apply_size and 'Size Score' in row and score_name in ['Culture Score', 'Capacity Score', 'Conduct Score']:
            if row['Size Score'] <= size_lower_quantile:
                base_score *= 0.70
            elif row['Size Score'] >= size_upper_quantile:
                base_score *= 1.10

        adjusted_scores[score_name] = base_score

    return pd.Series(adjusted_scores)

# Calculate the scores
df_with_scores = calculate_scores(df_copy, culture_columns, capacity_columns, conduct_columns, collaboration_columns, double_columns, triple_columns, quad_columns)

# Adjust the scores
lower_quantile = df_with_scores['B Corp Impact - Overall Score'].quantile(0.30)
upper_quantile = df_with_scores['B Corp Impact - Overall Score'].quantile(0.90)
size_lower_quantile = df_with_scores['Size Score'].quantile(0.25)
size_upper_quantile = df_with_scores['Size Score'].quantile(0.75)

adjusted_scores_df = df_with_scores.apply(lambda row: adjust_scores(row, lower_quantile, upper_quantile, size_lower_quantile, size_upper_quantile, apply_country=True, apply_industry=True, apply_size=True), axis=1)

# Create a new DataFrame with the adjusted scores
df = pd.concat([df, adjusted_scores_df], axis=1)

def normalize_scores_0_100(df, column_names):
    for column_name in column_names:
        min_score = df[column_name].min()
        max_score = df[column_name].max()
        df[column_name + ' Normalized'] = df[column_name].apply(lambda x: 100 * (x - min_score) / (max_score - min_score))
    return df

df = normalize_scores_0_100(df, ['Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score'])
def calculate_oracle_score(row):
    culture_weight = 0.40
    capacity_weight = 0.20
    conduct_weight = 0.20
    collaboration_weight = 0.20

    oracle_score = (
        row['Culture Score Normalized'] * culture_weight +
        row['Capacity Score Normalized'] * capacity_weight +
        row['Conduct Score Normalized'] * conduct_weight +
        row['Collaboration Score Normalized'] * collaboration_weight
    )
    return oracle_score

df['Oracle Score'] = df.apply(calculate_oracle_score, axis=1)

#format
df['PrivPub'] = 'Private'
columns_to_drop2 = ["size_score","industry_score","country"]
df = df.drop(columns=[col for col in columns_to_drop2 if col in df.columns])
rename_dict2 = {"size": "Employees", "website": "Website","city": "City","description": "Description", 'PrivPub': 'Public or Private'}
df = df.rename(columns=rename_dict2)
df['B Corp'] = 1
background_cols = ['Company', 'B Corp', 'Public or Private', 'Industry', 'Region', 'Country', 'City', 'Employees', 'Description', 'Website', 'B Corp Webpage','First Certified as B Corp']
score_cols0 = ['Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score', 'Oracle Score','Culture Score Normalized', 'Capacity Score Normalized', 'Conduct Score Normalized', 'Collaboration Score Normalized','B Corp Impact - Overall Score', 'B Corp Impact - Community', 'B Corp Impact - Customers', 'B Corp Impact - Environment', 'B Corp Impact - Governance', 'B Corp Impact - Workers', 'Size Score', 'Industry Score', 'B Corp Impact - Customers Customer Stewardship','B Corp Impact - Governance Mission Locked','B Corp Impact - Governance Mission Engagement', 'B Corp Impact - Community Civic Engagement Giving', 'B Corp Impact - Community Supply Chain Management', 'B Corp Impact - Environment Water', 'B Corp Impact - Environment Land Life', 'B Corp Impact - Environment Air Climate' ]
all_cols = list(df.columns)
score_cols1 = [col for col in all_cols if col not in background_cols + score_cols0]
new_column_order = background_cols + score_cols0 + score_cols1
df = df[new_column_order]

##use employees as a proxy for Size
def categorize_by_size(size):
     if size == '1-9' or size == '10-49':
        return 'Micro'
     elif size == '50-249':
        return 'Small'
     elif size =='250-999' or size == '1000+':
        return 'Medium'
     else:
        return 'Unknown'
df['Company Size'] = df['Employees'].apply(categorize_by_size)

##new dataframe for Public
df2 = pd.read_csv('Oraclesdgin.csv')
# Function to remove unnamed columns and capitalize the first letter of each word in column names
def clean_dataframe(dataframe):
    # Remove unnamed columns
    dataframe = dataframe.loc[:, ~dataframe.columns.str.contains('^Unnamed')]
    # Capitalize the first letter of each word in column names
    dataframe.columns = dataframe.columns.str.title()
    return dataframe

# Clean both dataframes
df2 = clean_dataframe(df2)
df2.rename(columns={'Privpub': 'Public or Private'}, inplace=True)
df2.rename(columns={'Employees (Demandbase Estimate)': 'Employees'}, inplace=True)
df2.drop(columns=['Isin', 'Duplicate Isin', 'Region', 'Geography'], inplace=True)
df2.rename(columns={'Continent': 'Region'}, inplace=True)
merged_df = pd.merge(df, df2,
                     on=['Company', 'Country', 'Description', 'Company Size','Website', 'Employees', 'Industry',
                         'Public or Private', 'Industry Score', 'Size Score', 'Culture Score',
                         'Capacity Score', 'Conduct Score', 'Collaboration Score',
                         'Culture Score Normalized', 'Capacity Score Normalized',
                         'Conduct Score Normalized', 'Collaboration Score Normalized',
                         'Oracle Score', 'Region'],
                     how='outer')
merged_df.drop(['Culture Score', 'Conduct Score', 'Capacity Score', 'Collaboration Score','Size Score', 'Industry Score','Size Score Normalized', 'Industry Score Normalized'], axis=1, inplace=True)
columns_to_rename = {
    'Culture Score Normalized': 'Culture Score',
    'Conduct Score Normalized': 'Conduct Score',
    'Capacity Score Normalized': 'Capacity Score',
    'Collaboration Score Normalized': 'Collaboration Score'}
merged_df.rename(columns=columns_to_rename, inplace=True)
columns_to_transform = [
    "B Corp",
    "Member Of Business In The Community Uk",
    "Member Full Abpi",
    "Member Affiliate Abpi"
]
for column in columns_to_transform:
    merged_df[column] = merged_df[column].apply(lambda x: 'Yes' if x == 1 else 'No')

st.dataframe(merged_df, hide_index = True)
