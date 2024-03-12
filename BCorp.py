import datadotworld as dw
import pandas as pd
import numpy as np


def load_data():
    sql_query = 'SELECT * FROM `b_corp_impact_data`'
    result_set = dw.query('blab/b-corp-impact-data', sql_query)
    df = result_set.dataframe
    return df

def numericdataframe(df):
    # Get columns that should be numeric and convert them to numeric? Not sure if this is working.
    for col in df.columns:
        if col.startswith(('ia_', 'impact_area_', 'overall_score')):
            df[col] = pd.to_numeric(df[col], errors='coerce')

    print(df['ia_workers_it_compensation_wages'].value_counts()) ###this has data but isn't being added to the dataframe in workers fair pay but has data
    print(df['ia_workers_it_financial_security'].value_counts()) ##ditto

    print(df.head(100))
    print(df.dtypes)
    # Filter DataFrame
    new_columns = {}
    new_columns['B Corp Impact - Community Diversity & Inclusion'] = (df['ia_community_it_diversity_equity_inclusion'] + df['ia_community_it_diversity_inclusion'])
    new_columns['B Corp Impact - Community Involvement'] = (df['ia_community_it_local_involvement'] + df['ia_community_it_local_economic_development'] + df['ia_community_it_economic_impact'] + df['ia_community_it_national_economic_development'] + df['ia_workers_it_workforce_development'])
    new_columns['B Corp Impact - Customers Impact In Need & Underserved'] = (df['ia_customers_it_basic_services_for_the_underserved'] + df['ia_customers_it_business_model_and_engagement'] + df['ia_customers_it_impact_improvement'] + df['ia_customers_it_serving_in_need_populations'] + df['ia_customers_it_serving_underserved_populations'] + df['ia_customers_it_serving_underserved_populations_direct'] + df['ia_customers_it_support_for_underserved_purpose_driven_enterprises'])
    new_columns['B Corp Impact - Customer Education'] = (df['ia_customers_it_education'] + df['ia_customers_it_educational_models_and_engagement'] + df['ia_customers_it_educational_outcomes'] + df['ia_customers_it_student_outcomes'] + df['ia_customers_it_student_experience'])
    new_columns['B Corp Impact - Customers Health'] = (df['ia_customers_it_health'] + df['ia_customers_it_health_outcomes'] + df['ia_customers_it_health_wellness_improvement'])
    new_columns['B Corp Impact - Governance Board Diversity'] = (df['ia_governance_it_governance'] + df['ia_governance_it_corporate_accountability'])
    new_columns['B Corp Impact - Goverance Ethics'] = (df['ia_governance_it_ethics_transparency'] + df['ia_governance_it_ethics'])
    new_columns['B Corp Impact - Workers Development & Communication'] = (df['ia_workers_it_job_flexibility_corporate_culture'] + df['ia_workers_it_engagement_satisfaction'] + df['ia_workers_it_career_development'] + df['ia_workers_it_management_worker_communication'] + df['ia_workers_it_training_education'])
    new_columns['B Corp Impact - Workers Benefits'] = (df['ia_workers_it_worker_benefits'] + df['ia_workers_it_benefits'])
    new_columns['B Corp Impact - Workers Fair Pay'] = (df['ia_workers_it_compensation_wages'] + df['ia_workers_it_financial_security'])
    new_columns['B Corp Impact - Workers Health & Safety'] = (df['ia_workers_it_occupational_health_safety'] + df['ia_workers_it_human_rights_labor_policy'] + df['ia_workers_it_health_wellness_safety'])
    new_columns['B Corp Impact - Workers Worker Owned'] = (df['ia_workers_it_worker_ownership'] + df['ia_workers_it_worker_owned'])
    new_columns_df = pd.DataFrame(new_columns)
    new_columns_df.index = df.index
    df = pd.concat([df, new_columns_df], axis=1)
    return df


def format_data(df):
##drop columns that are useless or that are included in collated columns above.
    columns_to_drop = [
    'certification_cycle', 'current_status', 'date_certified', 'products_and_services',
    'company_id', 'assessment_year', 'state', 'sector', 'assessment_year',
    'impact_area_community_na_score', 'impact_area_customers_na_score',
    'impact_area_environment_na_score', 'impact_area_governance_na_score',
    'impact_area_workers_na_score',
    'ia_community_it_diversity_equity_inclusion', 'ia_community_it_diversity_inclusion',
    'ia_community_it_local_involvement', 'ia_community_it_local_economic_development', 'ia_community_it_economic_impact', 'ia_community_it_national_economic_development', 'ia_workers_it_workforce_development',
    'ia_customers_it_basic_services_for_the_underserved', 'ia_customers_it_business_model_and_engagement', 'ia_customers_it_impact_improvement', 'ia_customers_it_serving_in_need_populations', 'ia_customers_it_serving_underserved_populations', 'ia_customers_it_serving_underserved_populations_direct', 'ia_customers_it_support_for_underserved_purpose_driven_enterprises',
    'ia_customers_it_education', 'ia_customers_it_educational_models_and_engagement', 'ia_customers_it_educational_outcomes', 'ia_customers_it_student_outcomes', 'ia_customers_it_student_experience',
    'ia_customers_it_health', 'ia_customers_it_health_outcomes', 'ia_customers_it_health_wellness_improvement',
    'ia_governance_it_governance', 'ia_governance_it_corporate_accountability',
    'ia_governance_it_ethics_transparency', 'ia_governance_it_ethics',
    'ia_workers_it_job_flexibility_corporate_culture', 'ia_workers_it_engagement_satisfaction', 'ia_workers_it_career_development', 'ia_workers_it_management_worker_communication', 'ia_workers_it_training_education',
    'ia_workers_it_worker_benefits', 'ia_workers_it_benefits',
    'ia_workers_it_compensation_wages', 'ia_workers_it_financial_security',
    'ia_workers_it_occupational_health_safety', 'ia_workers_it_human_rights_labor_policy', 'ia_workers_it_health_wellness_safety',
    'ia_workers_it_worker_ownership', 'ia_workers_it_worker_owned']

    #filter only for most recent assessments (stop double counting companies)
    df = df[(df['current_status'] == 'certified') & (df['certification_cycle'] == 1)]
    df = df.drop(columns=columns_to_drop)

    #rename some columns
    rename_dict = {
        'company_name': 'Company',
        'date_first_certified': 'First Certified as B Corp',
        'overall_score': 'B Corp Impact - Overall Score',
        'b_corp_profile': 'B Corp Webpage',
        'impact_area_community': 'B Corp Impact - Community',
        'impact_area_customers': 'B Corp Impact - Customers',
        'impact_area_environment': 'B Corp Impact - Environment',
        'impact_area_governance': 'B Corp Impact - Governance',
        'impact_area_workers': 'B Corp Impact - Workers'
    }
    df.rename(columns=rename_dict, inplace=True)
    new_column_names = {
        col: 'B Corp Impact - ' + col.replace('ia_', '').replace('_it_', ' ').replace('_', ' ').title()
        for col in df.columns if 'ia_' in col
    }
    df.rename(columns=new_column_names, inplace=True)

    # Capitalise each word in the column titles for the remaining columns
    df.columns = df.columns.str.replace('_', ' ').str.title()

    #Scale data
    for col in df.columns:
        if col.startswith('B Corp Impact'):
            df[col] = pd.to_numeric(df[col], errors='coerce')
            non_blank_values = df[col].dropna()

            if non_blank_values.empty:
                continue

            min_value = non_blank_values.min()
            max_value = non_blank_values.max()
            if max_value == min_value:
                continue
            df[col] = (df[col] - min_value) / (max_value - min_value)
    return df


def process_data():
    df = load_data()
    df = numericdataframe(df)
    df = format_data(df)
    return df

if __name__ == "__main__":
    df = process_data()
    print(df.head())
