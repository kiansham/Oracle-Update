#utils
import pandas as pd
import numpy as np
import streamlit as st
import math
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from streamlit_echarts import st_echarts
import Levenshtein
from streamlit_option_menu import option_menu
from streamlit_server_state import server_state, server_state_lock
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

display_columns = ['Company', 'Country', 'Industry', 'Region',
            'Company Size', 'Employees (Estimate)','Public Or Private', 
            'Oracle Score', 'Culture Score', 
            'Capacity Score', 'Conduct Score', 'Collaboration Score', 
            'B Corp',  'Sdg 1: Aligned', 'Sdg 1: Misaligned',
            'Sdg 2: Aligned', 'Sdg 2: Misaligned',
            'Sdg 3: Aligned', 'Sdg 3: Misaligned',
            'Sdg 4: Aligned', 'Sdg 4: Misaligned',
            'Sdg 5: Aligned', 'Sdg 5: Misaligned',
            'Sdg 6: Aligned', 'Sdg 6: Misaligned',
            'Sdg 7: Aligned', 'Sdg 7: Misaligned',
            'Sdg 8: Aligned', 'Sdg 8: Misaligned',
            'Sdg 9: Aligned', 'Sdg 9: Misaligned',
            'Sdg 10: Aligned', 'Sdg 10: Misaligned',
            'Sdg 11: Aligned', 'Sdg 11: Misaligned',
            'Sdg 12: Aligned', 'Sdg 12: Misaligned',
            'Sdg 13: Aligned', 'Sdg 13: Misaligned',
            'Sdg 14: Aligned', 'Sdg 14: Misaligned',
            'Sdg 15: Aligned', 'Sdg 15: Misaligned', 
            'Description', 'Website']

def format_dataframe(df, display_columns):
    df = df[display_columns]
    new_column_names = {col: col.replace('Sdg', 'SDG') for col in df.columns if 'Sdg' in col}
    df.rename(columns=new_column_names, inplace=True)
    df['B Corp'] = df['B Corp'].replace({1: 'Yes', 0: 'No'})
    return df

def load_data(file_path, display_columns):
    try:
        df = pd.read_csv(file_path)
        df = df[display_columns]
        new_column_names = {col: col.replace('Sdg', 'SDG') for col in df.columns if 'Sdg' in col}
        df.rename(columns=new_column_names, inplace=True)
        df['B Corp'] = df['B Corp'].replace({1: 'Yes', 0: 'No'})
        return df
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
file = "oraclecomb.csv"
df = load_data(file, display_columns)



def filter_dataframe(df, b_corp_filter, company_names, regions, industries, company_sizes, oracle_range, culture_range, capacity_range, conduct_range, collaboration_range):
    temp_df = df 
    if b_corp_filter is not None:
        temp_df = temp_df[temp_df['B Corp'] == b_corp_filter]
    if company_names:
        temp_df = temp_df[temp_df['Company'].isin(company_names)]
    if regions:
        temp_df = temp_df[temp_df['Region'].isin(regions)]
    if industries:
        temp_df = temp_df[temp_df['Industry'].isin(industries)]
    if company_sizes:
        temp_df = temp_df[temp_df['Company Size'].isin(company_sizes)]
    if oracle_range:
        temp_df = temp_df[(temp_df['Oracle Score'] >= oracle_range[0]) & (temp_df['Oracle Score'] <= oracle_range[1])]
    if culture_range:
        temp_df = temp_df[(temp_df['Culture Score'] >= culture_range[0]) & (temp_df['Culture Score'] <= culture_range[1])]
    if capacity_range:
        temp_df = temp_df[(temp_df['Capacity Score'] >= capacity_range[0]) & (temp_df['Capacity Score'] <= capacity_range[1])]
    if conduct_range:
        temp_df = temp_df[(temp_df['Conduct Score'] >= conduct_range[0]) & (temp_df['Conduct Score'] <= conduct_range[1])]
    if collaboration_range:
        temp_df = temp_df[(temp_df['Collaboration Score'] >= collaboration_range[0]) & (temp_df['Collaboration Score'] <= collaboration_range[1])]
    return temp_df

def create_filters(df):
    # Company and score filters
    col1, col2 = st.columns(2, gap="small")
    with col1:
        with st.expander('Company Trait Filters'):
            is_b_corp = st.checkbox(value=False, label='Only Display Designated B Corps', key='b_corp')
            b_corp_filtered = 'Yes' if is_b_corp else None
            selected_companies = st.multiselect('Select by Company Name', options=df['Company'].unique(), key='company_name')
            selected_regions = st.multiselect('Select by Region', options=df['Region'].unique(), key='region')
            selected_industries = st.multiselect('Select by Industry', options=df['Industry'].unique(), key='industry')
            selected_size = st.multiselect('Select by Company Size', options=df['Company Size'].unique(), key='company_size')
    with col2:
        with st.expander('Company Score Filters'):
            selected_oracle = st.slider('Oracle Score', min_value=0, max_value=100, value=(0, 100))
            selected_culture = st.slider('Culture Score', min_value=0, max_value=100, value=(0, 100))
            selected_capacity = st.slider('Capacity Score', min_value=0, max_value=100, value=(0, 100))
            selected_conduct = st.slider('Conduct Score', min_value=0, max_value=100, value=(0, 100))
            selected_collaboration = st.slider('Collaboration Score', min_value=0, max_value=100, value=(0, 100))

    return b_corp_filtered, selected_companies, selected_regions, selected_industries, selected_size, selected_oracle, selected_culture, selected_capacity, selected_conduct, selected_collaboration

def get_filtered_data(df, b_corp_filtered, selected_companies, selected_regions, selected_industries, selected_size, selected_oracle, selected_culture, selected_capacity, selected_conduct, selected_collaboration):
    # Filter dataframe
    filtered_data = filter_dataframe(df, b_corp_filtered, selected_companies, selected_regions, selected_industries, selected_size, selected_oracle, selected_culture, selected_capacity, selected_conduct, selected_collaboration)
    return filtered_data

###Create all the metrics
company_data  = None
score_columns = ['Oracle Score', 'Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score'] 
selected_score = "Oracle Score"
def calculate_stats(df, filtered_data, selected_score):
    if selected_score not in df.columns:
        return None
    total_companies = len(df)
    total_filtered_companies = len(filtered_data)
    percentage_of_companies_shown = total_filtered_companies / total_companies * 100
    total_uk_companies = len(df[df['Country'] == 'United Kingdom'])
    total_filtered_uk_companies = len(filtered_data[filtered_data['Country'] == 'United Kingdom'])
    percentage_of_uk_companies_shown = total_filtered_uk_companies / total_uk_companies * 100
    most_companies_country = df['Country'].value_counts().idxmax()
    most_companies_count = df['Country'].value_counts().max()
    highest_avg_score_country = df.groupby('Country')['Oracle Score'].mean().idxmax()
    highest_avg_score_value = df.groupby('Country')['Oracle Score'].mean().max()
    lowest_avg_score_country = df.groupby('Country')['Oracle Score'].mean().idxmin()
    lowest_avg_score_value = df.groupby('Country')['Oracle Score'].mean().min()
    uk_avg_score = df[df['Country'] == 'United Kingdom']['Oracle Score'].mean()
    highest_oracle_score = filtered_data['Oracle Score'].max()
    highest_oracle_score_change = highest_oracle_score - df['Oracle Score'].max()
    median_oracle_score = filtered_data['Oracle Score'].median()
    median_oracle_score_change = median_oracle_score - df['Oracle Score'].median()
    average_scores_industry = filtered_data.groupby('Industry')[selected_score].mean().reset_index()
    average_scores_region = filtered_data.groupby('Region')[selected_score].mean().reset_index()
    average_scores_size = filtered_data.groupby('Company Size')[selected_score].mean().reset_index()
    overall_average_industry = filtered_data[selected_score].mean()
    overall_average_region = filtered_data[selected_score].mean()
    overall_average_size = filtered_data[selected_score].mean()
    region_counts = df['Region'].value_counts()
    regions = region_counts.index.tolist()
    region_country_counts = df.groupby(['Region', 'Country']).size().unstack(fill_value=0).reset_index()
    industry_median_scores = df.groupby('Industry')[selected_score].median()
    highest_industry = industry_median_scores.idxmax()
    lowest_industry = industry_median_scores.idxmin()
    max_score = df[selected_score].max()
    min_score = df[selected_score].min()
    median_score = df[selected_score].median()
    mean_score = df[selected_score].mean()
    highest_company = df[df[selected_score] == max_score]['Company'].values[0]
    lowest_company = df[df[selected_score] == min_score]['Company'].values[0]
    return {
        "total_companies": total_companies,
        "most_companies_country": most_companies_country,
        "most_companies_count": most_companies_count,
        "highest_avg_score_country": highest_avg_score_country,
        "highest_avg_score_value": highest_avg_score_value,
        "lowest_avg_score_country": lowest_avg_score_country,
        "lowest_avg_score_value": lowest_avg_score_value,
        "uk_avg_score": uk_avg_score,
        "region_country_counts": region_country_counts,
        "total_filtered_companies": total_filtered_companies,
        "percentage_of_companies_shown": percentage_of_companies_shown,
        "total_uk_companies": total_uk_companies,
        "total_filtered_uk_companies": total_filtered_uk_companies,
        "percentage_of_uk_companies_shown": percentage_of_uk_companies_shown,
        "highest_oracle_score": highest_oracle_score,
        "highest_oracle_score_change": highest_oracle_score_change,
        "median_oracle_score": median_oracle_score,
        "median_oracle_score_change": median_oracle_score_change,
        "average_scores_industry": average_scores_industry,
        "average_scores_region": average_scores_region,
        "average_scores_size": average_scores_size,
        "overall_average_industry": overall_average_industry,
        "overall_average_region": overall_average_region,
        "overall_average_size": overall_average_size,
        "region_counts": region_counts,
        "regions": regions,
        "industry_median_scores": industry_median_scores,
        "highest_industry": highest_industry,
        "max_score": max_score,
        "min_score": min_score,
        "median_score": median_score,
        "mean_score": mean_score,
        "lowest_industry": lowest_industry,
        "highest_company": highest_company,
        "lowest_company": lowest_company}

print(df)
#bullet chart
def bullet(filtered_data, stats, selected_score): 
    stats = calculate_stats(df, filtered_data, selected_score)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[stats['min_score'], stats['median_score'], stats['mean_score'], stats['max_score']],
        y=[selected_score]*4,
        text=['Min', 'Median', 'Mean', 'Max'],
        mode='markers+text',
        textposition="top center",
        marker=dict(color=['blue', 'red', 'green', 'orange'], size=10),
        showlegend=False
    ))

    fig.update_layout(
        shapes=[
            dict(type="line", xref="x", yref="y",
                x0=stats['min_score'], y0=-0.25, x1=stats['min_score'], y1=0.25,
                line=dict(color="blue", width=3)),
            dict(type="line", xref="x", yref="y",
                x0=stats['median_score'], y0=-0.25, x1=stats['median_score'], y1=0.25,
                line=dict(color="red", width=3)),
            dict(type="line", xref="x", yref="y",
                x0=stats['mean_score'], y0=-0.25, x1=stats['mean_score'], y1=0.25,
                line=dict(color="green", width=3)),
            dict(type="line", xref="x", yref="y",
                x0=stats['max_score'], y0=-0.25, x1=stats['max_score'], y1=0.25,
                line=dict(color="orange", width=3)),
        ],
        xaxis=dict(range=[stats['min_score'] - 5, stats['max_score'] + 5], autorange=False),
        yaxis=dict(showticklabels=False, range=[-0.5, 0.5]),
        title=f"Bullet Chart for {selected_score}"
    )
    st.plotly_chart(fig)

##make a couple of bar charts
def generate_chart(filtered_data, stats, selected_score, chart_type):
    stats = {}
    stats[selected_score] = calculate_stats(df, filtered_data, selected_score)
    if selected_score not in df.columns:
        return None
    if chart_type == 'size':
        data_key = 'average_scores_size'
        category = 'Company Size'
        overall_average_key = 'overall_average_size'
        orientation = 'v'
        chart_width = 400
    elif chart_type == 'region':
        data_key = 'average_scores_region'
        category = 'Region'
        overall_average_key = 'overall_average_region'
        orientation = 'h'
        chart_width = 700
    elif chart_type == 'industry':
        data_key = 'average_scores_industry'
        category = 'Industry'
        overall_average_key = 'overall_average_industry'
        orientation = 'v'
        chart_width = 1150
    else:
        raise ValueError("Invalid chart type. Choose from 'size', 'region', or 'industry'.")

    df_for_chart = stats[selected_score][data_key]
    fig = px.bar(df_for_chart, x=category, y=selected_score, orientation=orientation, 
             title=f'Average {selected_score} by {category}', color=category, width=chart_width)
    overall_average = stats[selected_score][overall_average_key]

    if chart_type == 'region':
        fig.add_vline(x=overall_average, line_dash="dot", annotation_text="Avg", 
                      annotation_position="top right" if chart_type != 'industry' else "bottom right")
    else:
        fig.add_hline(y=overall_average, line_dash="dot", annotation_text="Avg", 
                      annotation_position="top right" if chart_type != 'industry' else "bottom right")

    fig.update_layout(xaxis_title='', yaxis_title='', showlegend=False)    
    st.plotly_chart(fig, use_container_width=True)

##Create swarm chart
def create_strip_plot(filtered_data, selected_score):
    swarm = px.strip(
    filtered_data,
    x=selected_score,
    color='Industry',
    hover_name = 'Company',
    orientation='h',
    stripmode='overlay')
    swarm.update_layout(
    title=f'Swarm Plot of {selected_score}',
    xaxis_title=selected_score,
    yaxis_title='Count',
    autosize=False,
    width=1150,  
    height=600, 
    title_font=dict(size=20),  
    xaxis_tickfont=dict(size=14),  
    yaxis_tickfont=dict(size=14),
    xaxis=dict(range=[0,100]),
    legend=dict(
        x=0.0,
        y=-0.5,
        font=dict(size=14),
        xanchor='left',
        yanchor='bottom',
        orientation='h'))
    return swarm

#company selectbox for charting
def create_company_selectbox(df, key):
    df_sorted = df.sort_values(by='Oracle Score', ascending=False)
    companies_sorted = df_sorted['Company'].unique()
    if companies_sorted.size == 0:
        return None
    dive_company_index = np.where(companies_sorted == 'AstraZeneca')[0][0] if 'AstraZeneca' in companies_sorted else 0
    dive_company_index = int(dive_company_index)
    option = st.selectbox("Please select a Company from the List to find out more", options=companies_sorted, index=dive_company_index, key=key)
    return option

#more checking
def calculate_metrics(df, selected_score):
    selected_score_columns = ['Oracle Score', 'Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score'] 
    if selected_score not in selected_score_columns:
        return None
    return 

#Clean messy country naming
def find_closest_match(country, recognized_countries):
    scores = [Levenshtein.ratio(country.lower(), mapped_country.lower()) for mapped_country in recognized_countries]
    max_index = scores.index(max(scores))
    
    if scores[max_index] > 0.7:
        return recognized_countries[max_index]
    else:
        return country
    
@st.cache_data
def calculate_country_metrics(df, selected_country='United Kingdom'):
    if 'Country' not in df.columns:
        return None
    filtered_data2 = df.groupby('Country').filter(lambda x: len(x) > 20)
    total_countries = df['Country'].nunique()
    total_filtered_countries = filtered_data2['Country'].nunique()
    percentage_of_countries_shown = total_filtered_countries / total_countries * 100
    total_companies_in_selected_country = len(df[df['Country'] == selected_country])
    total_filtered_companies_in_selected_country = len(filtered_data2[filtered_data2['Country'] == selected_country])
    percentage_of_selected_country_companies_shown = total_filtered_companies_in_selected_country / total_companies_in_selected_country * 100 if total_companies_in_selected_country > 0 else 0
    most_companies_country = filtered_data2['Country'].value_counts().idxmax()
    most_companies_count = filtered_data2['Country'].value_counts().max()
    highest_avg_score_country = filtered_data2.groupby('Country')['Oracle Score'].mean().idxmax()
    highest_avg_score_value = filtered_data2.groupby('Country')['Oracle Score'].mean().max()
    lowest_avg_score_country = filtered_data2.groupby('Country')['Oracle Score'].mean().idxmin()
    lowest_avg_score_value = filtered_data2.groupby('Country')['Oracle Score'].mean().min()
    return {
        "total_countries": total_countries,
        "total_filtered_countries": total_filtered_countries,
        "percentage_of_countries_shown": percentage_of_countries_shown,
        "total_companies_in_selected_country": total_companies_in_selected_country,
        "total_filtered_companies_in_selected_country": total_filtered_companies_in_selected_country,
        "percentage_of_selected_country_companies_shown": percentage_of_selected_country_companies_shown,
        "most_companies_country": most_companies_country,
        "most_companies_count": most_companies_count,
        "highest_avg_score_country": highest_avg_score_country,
        "highest_avg_score_value": highest_avg_score_value,
        "lowest_avg_score_country": lowest_avg_score_country,
        "lowest_avg_score_value": lowest_avg_score_value
    }

#heatmap
def plot_choropleth(country_counts):
    fig = px.choropleth(country_counts,
                        locations="Country",
                        locationmode='country names',
                        color='count',
                        color_discrete_sequence=px.colors.qualitative.Plotly,
                        hover_data=['Country', 'count'])

    fig.update_layout(title_text='Global Distribution of Companies in Analysis',
                      hoverlabel=dict(
                          bgcolor="white",
                          font_size=14,
                          font_family="Arial"
                      ),
                      width=550)
    return fig


##guage and guage options chart creation###
def create_gauge_chart(score, median_oracle_score, title):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        delta={'reference': median_oracle_score}, #THIS IS NOT WORKING
        title={'text': title},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [{'range': [0, median_oracle_score], 'color': 'lightgray'}]  # AND THIS
        }))
    fig.update_layout(width=400, height=300)
    return fig
def create_gauge_options(score, median_oracle_score, title):
        options = {
            "tooltip": {
                "formatter": '{a} <br/>{b} : {c}%'
            },
            "series": [{
                "name": title,
                "type": 'gauge',
                'axisLine': {
                'lineStyle': {
                'width': '25',
                'color': [
                    ['0.3', '#fd666d'],
                    ['0.7', '#37a2da'],
                    ['1', '#67e0e3']
                ]
                }
            },
                "startAngle": 180,
                "endAngle": 0,
                "progress": {
                    "show": "true"
                },
                "radius": '100%',
                "itemStyle": {
                    "color": 'auto'
                },
                "colorBy": "data",
                "progress": {
                    "show": "true",
                    "roundCap": "true",
                    "width": 0
                },
                "pointer": {
                    "length": '50%',
                    "width": 8,
                    "offsetCenter": [0, '5%']
                },
                "detail": {
                    "valueAnimation": "true",
                    "fontWeight": "normal",
                    "formatter": '{value:.2f}'.format(value=score),
                    "offsetCenter": [0, '40%'],
                    "valueAnimation": "true",
                },
                "data": [{
                    "value": score,
                    "name": title}],
                "center": ["30%", "66%"],
                "animation": "true",
                "animationDuration": "2000",
                'fontSize': '18'
                

            }]
        }
        return options

##create radar chart
def create_radar_chart(df, scores, score_columns, selected_company, option, show_median=False, show_comparison=False):
    radar_data = pd.DataFrame(dict(Score=scores, Dimension=score_columns))
    radar_data['angle'] = radar_data['Score'] / radar_data['Score'].sum() * 2 * math.pi
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=score_columns,
        fill='toself',
        name=f'{option}',
        marker=dict(color='rgba(255, 0, 0, 0.5)')
    ))
    if show_median:
        median_scores = df[score_columns].median().tolist()
        fig.add_trace(go.Scatterpolar(
            r=median_scores,
            theta=score_columns,
            fill='toself',
            name='Median Pillar Scores',
            marker=dict(color='rgba(0, 255, 0, 0.5)')  
        ))
    if show_comparison:
        compare_scores = df[df['Company'] == selected_company][score_columns].iloc[0].tolist()
        fig.add_trace(go.Scatterpolar(
            r=compare_scores,
            theta=score_columns,
            fill='toself',
            name=selected_company,
            marker=dict(color='rgba(0, 0, 255, 0.5)')
        ))
    fig.update_layout(polar=dict(
        radialaxis=dict(visible=True, range=[0, 100])), showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.5,
            xanchor="left",
            x=0))
    return fig

##function for Text on SDG_Expander
def sdg_expander():
    with st.expander('Click To Expand For More Information on Complete SDG Definitions and Revenue Alignment Methodology :world_map:'):
        st.markdown('The United Nations Sustainable Development Goals (UN SDGs) were adopted by the UN in 2015 as a blueprint to achieve a better and more sustainable future for all.\n\n'

        'SDG metrics in this tool include data on both **SDG alignment** (positive impacts) and **SDG misalignment** (negative impacts), based on products and services. A product or service can align with more than one SDG and is deemed Strongly, Moderately, or Weakly Aligned/Misaligned.\n\n'

        'The alignment for each SDG is calculated as follows:'
        '- Strongly aligned products have a clear direct impact on the SDG.'
        '- Moderately aligned products have a lesser direct impact.'
        '- Weakly aligned products have an indirect impact.'
        
        '**Revenue share calculation**:'
        'Revenue share = \n\n'
        'revenue from products that are strongly (mis)aligned with SDG X + \n\n'
        'revenue from products that are moderately (mis)aligned with SDG X * 0.5 + \n\n'
        'revenue from products that are weakly (mis)aligned with SDG X * 0.25 \n\n'

        '**Sustainable Development Goals:**'
        '1. **SDG 1: No Poverty** - End poverty in all its forms everywhere.\n\n'
        '2. **SDG 2: Zero Hunger** - End hunger, achieve food security and improved nutrition and promote sustainable agriculture.\n\n'
        '3. **SDG 3: Good Health and Well-being** - Ensure healthy lives and promote well-being for all at all ages.\n\n'
        '4. **SDG 4: Quality Education** - Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all.\n\n'
        '5. **SDG 5: Gender Equality** - Achieve gender equality and empower all women and girls.\n\n'
        '6. **SDG 6: Clean Water and Sanitation** - Ensure availability and sustainable management of water and sanitation for all. \n\n'
        '7. **SDG 7: Affordable and Clean Energy** - Ensure access to affordable, reliable, sustainable, and modern energy for all. \n\n'
        '8. **SDG 8: Decent Work and Economic Growth** - Promote sustained, inclusive, and sustainable economic growth, full and productive employment, and decent work for all. \n\n'
        '9. **SDG 9: Industry, Innovation, and Infrastructure** - Build resilient infrastructure, promote inclusive and sustainable industrialization, and foster innovation.\n\n'
        '10. **SDG 10: Reduced Inequalities** - Reduce inequality within and among countries.\n\n'
        '11. **SDG 11: Sustainable Cities and Communities** - Make cities and human settlements inclusive, safe, resilient, and sustainable.\n\n'
        '12. **SDG 12: Responsible Consumption and Production** - Ensure sustainable consumption and production patterns.\n\n'
        '13. **SDG 13: Climate Action** - Take urgent action to combat climate change and its impacts.\n\n'
        '14. **SDG 14: Life Below Water** - Conserve and sustainably use the oceans, seas, and marine resources for sustainable development.\n\n'
        '15. **SDG 15: Life on Land** - Protect, restore, and promote sustainable use of terrestrial ecosystems, sustainably manage forests, combat desertification and halt and reverse land degradation and halt biodiversity loss.')


##Create SDG_Chart###
@st.cache_resource
def create_sdg_chart(df, show_all_data):
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=("Misaligned", "Aligned"))
    colors = px.colors.qualitative.Pastel
    largest_aligned_sdg = None
    largest_aligned_value = 0
    largest_misaligned_sdg = None
    largest_misaligned_value = 0
    for i in range(1, 16):
        sdg_aligned_key = f'SDG {i}: Aligned'
        sdg_misaligned_key = f'SDG {i}: Misaligned'
        if sdg_aligned_key in df.columns and sdg_misaligned_key in df.columns:
            aligned_value = df[sdg_aligned_key].iloc[0]
            misaligned_value = df[sdg_misaligned_key].iloc[0]
            if aligned_value > largest_aligned_value:
                largest_aligned_sdg = f'Sdg {i}'
                largest_aligned_value = aligned_value
            if misaligned_value > largest_misaligned_value:
                largest_misaligned_sdg = f'Sdg {i}'
                largest_misaligned_value = misaligned_value
            if not show_all_data and (aligned_value == 0 and misaligned_value == 0):
                continue
            fig.add_trace(go.Bar(
                y=[f'SDG {i}'],
                x=[aligned_value], 
                name=f'SDG {i} Alignment',
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=[f'SDG {i} Aligned: {aligned_value*100:.2f}%' if aligned_value != 0 else ''],
                textposition='outside'
            ), 1, 2)
            fig.add_trace(go.Bar(
                y=[f'SDG {i}'],
                x=[misaligned_value],
                name=f'',
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=[f'SDG {i} Misaligned: {misaligned_value*100:.2f}%' if misaligned_value != 0 else ''],  
                textposition='outside'  # Display the text outside the bars
            ), 1, 1)
            sdg_labels = [f'Sdg {i}' for i in range(1, 16) if f'Sdg {i}: Aligned' in df.columns or f'Sdg {i}: Misaligned' in df.columns]
            fig.update_layout(showlegend=False,
        margin=dict(l=10, r=10, t=20, b=20),
        autosize=True,  
        width=1250,
        height=350)
            fig.update_xaxes(tickformat=".0%")
            fig.update_xaxes(range=[-1, 0], tickformat=".0%", row=1, col=1)
            fig.update_xaxes(range=[0, 1], tickformat=".0%", row=1, col=2)
            fig.update_yaxes(tickvals=sdg_labels, ticktext=sdg_labels, autorange="reversed", row=1, col=1)
            fig.update_yaxes(tickvals=sdg_labels, ticktext=sdg_labels, autorange="reversed", row=1, col=2)
    return fig, largest_aligned_sdg, largest_aligned_value, largest_misaligned_sdg, largest_misaligned_value
def SDG_Impact_Alignment(df, option):
    company_data = df[df['Company'] == option]
    sdg_columns = [f'SDG {i}: Aligned' for i in range(1, 16)] + [f'SDG {i}: Misaligned' for i in range(1, 16)]
    if company_data[sdg_columns].empty or company_data[sdg_columns].isna().all().all():
        st.warning('No SDG data available for this company.')
        return
    show_all_data = st.toggle("Show All Data", value=True)
    fig, largest_aligned_sdg, largest_aligned_value, largest_misaligned_sdg, largest_misaligned_value = create_sdg_chart(company_data, show_all_data)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("Largest SDG Detraction")
        st.markdown(f"###### {largest_misaligned_sdg if largest_misaligned_sdg else 'None'}   {largest_misaligned_value:.0%}")
    with col2:
        st.markdown("Largest SDG Contribution")
        st.markdown(f"###### {largest_aligned_sdg if largest_aligned_sdg else 'None'} - {largest_aligned_value:.0%}")
    st.markdown('')
    st.markdown(f"#### Plotted Revenue Alignment/Misalignment to SDGs")
    st.plotly_chart(fig)

def intro_page():
    col1 , col2 = st.columns(2)
    with col1:
        st.subheader("Oracle Tool: Introduction")
        st.markdown(f'###### Welcome! :wave:')
        st.markdown('This Tool has been designed to assist Oracle in Filtering through potential corporate partners.\n\n'
            'It contains over 6,000 companies and assesses them based on our 4 C Framework represented by the **Oracle Score** and its subcomponents the\n\n'
              '**- Culture Score** **- Capactiy Score** **- Conduct Score** **- Collaboration Score**.')
        st.divider()
        st.subheader('Things to Note')
        st.markdown('The Oracle Score is an estimation and the scores should merely give a guide to companies that may be useful to reach out to.\n\n'
                    'Please note that navigating between pages will reset the view while navigating between tabs will keep the filters intact.\n\n' 
                    'If an error occurs it is likely interaction between different filters. Please reset filters and try again.\n\n'
            ':black_circle_for_record: **To better Understand terminology, data sources or calcultations used, please refer to the additional tabs above this page** :top:.\n\n')
        st.markdown('We are working to provide complete background information as downloadables and through visualisation in the app. We are also refactoring code and will will update Oracle when available')
    with col2:
        st.subheader('Navigation')
        st.markdown(f'###### Where do you want to go? :wave:\n\n'           
                '**To Get Started** :page_facing_up: Use the **sidebar** on the left of the page to start exploring.')

        st.markdown('Navigate between one of two main sections:\n\n'
                ':one: **Aggregate Data** :bar_chart: :mag:\n\n'
                'Consists of two embedded tabs. In this section you can filter the database based on a number of different criteria. Data will automatically update as you adjust the filter values. Tables are editable and downloadable.'
                'This section also contains a number of charts and statistics to help you understand the data shapre & distribution giving users chance to break down the Oracle Score in to its subcomponents.'
                'This page is useful for giving users a well rounded view of the universe!\n\n'
                
                ':two: **Company Deep Dive** :factory::eyes:\n\n' 
                'The page allows us to select a company from the dropdown and see a detailed overview of the company including performance on our 4Cs framework.' 
                'Users can assess a Company performance across scores relative to a selected peer or the median of the universe.' 
                'Lastly, users are shown a visual of company contribution to SDGs.' 
                'This page is useful for understanding why a Company is rated as they are, what they might have in common with Oracle and is a launchpad to further research. \n\n')


