import pandas as pd
import streamlit as st
import os
import plotly.graph_objects as go
import plotly.express as px
from streamlit_echarts import st_echarts
from streamlit_option_menu import option_menu
from streamlit_server_state import server_state, server_state_lock
from utils import intro_page, externaldata, create_filters, get_filtered_data, format_dataframe, display_columns, calculate_stats, bullet, SDG_Impact_Alignment, selected_score, create_radar_chart, create_strip_plot, generate_chart, create_company_selectbox, create_gauge_options, sdg_expander, find_closest_match, plot_choropleth
from st_aggrid import GridOptionsBuilder, AgGrid
from st_aggrid.shared import GridUpdateMode, DataReturnMode


##loading and setting up stuff
st.set_page_config(
    page_title="Oracle Partnerships with Purpose Filtering", 
    page_icon="mag", 
    layout="wide", 
    initial_sidebar_state="expanded")


    
def load_data():
    try:
        df = pd.read_csv('oraclecomb2.csv')
    except FileNotFoundError:
        df = pd.read_csv('oraclecomb.csv')
    df = format_dataframe(df, display_columns)
    return df


def aggframe(): 
    st.subheader("Oracle Score Dashboard")
    st.markdown('Use the Filters Below to Dynamically Narrow the Data Universe of Companies')
    df = load_data()
    st.session_state["updated_df"] = st.data_editor(st.session_state['initial_df'], num_rows= 'dynamic')
    print(df)
    filters = create_filters(df)    
    filtered_data = get_filtered_data(df, *filters).sort_values(by='Oracle Score', ascending=False)
    st.session_state['filtered_data'] = filtered_data    
    stats = calculate_stats(df, filtered_data, selected_score)
    st.markdown('Stats for Current Filtered Universe')  
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Total Companies", value=f"{stats['total_filtered_companies']:,}")
    col2.metric(label="UK Companies", value=f"{stats['total_filtered_uk_companies']:,}")
    col3.metric(label="Highest Oracle Score", value="{:.2f}".format(stats['highest_oracle_score']))
    col4.metric(label="Median Oracle Score", value="{:.2f}".format(stats['median_oracle_score']))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader('Data Table')
    with col2:
        edit_option = st.toggle('Edit Data', value = False)
    if edit_option:
        with st.form(key='my_form'):
            st.markdown('Please Enter Your Edits on the Table and Click Submit')
            df = st.data_editor(st.session_state['df'], hide_index=True)
            submitted = st.form_submit_button(label="Submit")
            if submitted:
                st.write("Edited dataframe:", st.session_state['df']) 
                st.warning('You are using an edited source document.')
    with col3:
        reset_option = st.toggle('Delete Edits', value=False)
        if reset_option:
            df = pd.read_csv('oraclecomb.csv')
            df.to_csv('oraclecomb2.csv', index=False)
            st.sidebar.success('Data has been reset to original source.')
    
    st.dataframe(filtered_data, use_container_width=True, hide_index=True)
   
    col1, col2 = st.columns([6,3])
    with col2:
        csv = filtered_data.to_csv(index=False)
        st.download_button(
            label="Download Displayed Data",
            data=csv,
            file_name='oraclecombfiltered.csv',
            mime='text/csv')
        
def analysis1():
    df = load_data()
    filtered_data = st.session_state['filtered_data']
    st.subheader('Select a Score Category to See its Distribution and the Top 5 Best Performing Companies')
    score_columns = ['Oracle Score', 'Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score']
    filtered_data = st.session_state['filtered_data']
    selected_score = st.selectbox('Click To Select Score Category', score_columns)
    stats = calculate_stats(df, filtered_data, selected_score)
    st.markdown(f'Top 5 Companies for {selected_score}')
    st.caption(f'These are the Top 5 Companies on the {selected_score}. The arrow shows the distance from the median score value.')
    top_5_companies = filtered_data.nlargest(5, selected_score)
    cols = st.columns(5) 
    for i, row in enumerate(top_5_companies.iterrows()):
        label = f"{row[1]['Company']}"  
        value = row[1][selected_score] 
        cols[i].metric(label=label, value="{:.2f}".format(value), delta = "{:.2f}".format(value - filtered_data[selected_score].median()))
    num_of_columns = 5
    for j in range(len(top_5_companies), num_of_columns):
        cols[j].empty()
    st.divider()
    st.subheader(f'Swarm Chart of {selected_score}')
    st.markdown(f'This chart shows the distribution of scores for the {selected_score}.  Each industry type is colour coded. Hover over a value for more information including company name')          
    with st.expander('Click To Expand For More Information About Swarm Charts'):
            st.markdown('Swarm Charts are often used to display distribution on metrics.\n\n'
            'For example, in a business context, a swarm chart could display customer ratings for different products. Each dot represents a customer rating, and a dense cluster of dots at a high rating level indicates a well-received product.\n\n'
            'In our Case they show how companies by industry perform across our 4 Cs and the Oracle Score.\n\n'
            'Swarm charts can quickly highlight patterns in the distribution of scores. This makes them useful for understanding how the scores are distributed which assists in helping us get a feel for the general feel of the distribtution while clearly marking out potential outliers')
    st.session_state['filtered_data'] = filtered_data
    swarm_plot = create_strip_plot(filtered_data, selected_score)
    st.plotly_chart(swarm_plot)
    st.divider()
    st.subheader(f'Mean, Median, Highest and Lowest Score on {selected_score}')
    stats = calculate_stats(df, filtered_data, selected_score)
    col1, col2, col3 = st.columns([1,1.5,4])
    with col1:
        st.metric(label="Median", value=f"{stats['median_score']:.2f}", delta ="None", delta_color="off")
        st.metric(label="Mean", value=f"{stats['mean_score']:.2f}", delta =f"{stats['mean_score'] - stats['median_score']:.2f}")
        st.metric(label="Highest Score", value=f"{stats['max_score']:.2f}", delta =f"{stats['max_score'] - stats['median_score']:.2f}")
        st.metric(label="Lowest Score", value=f"{stats['min_score']:.2f}", delta =f"{stats['min_score'] - stats['median_score']:.2f}")
    with col2:
        st.text('Highest Industry (by median):')
        st.markdown(f'##### {stats["highest_industry"]}')   
        st.markdown("")
        st.markdown("")
        st.text('Highest Company:')
        st.markdown(f'##### {stats["highest_company"]}')   
        st.markdown("")
        st.markdown("")
        st.text('Lowest Industry (by median):')
        st.markdown(f'##### {stats["lowest_industry"]}') 
        st.markdown("")
        st.markdown("")
        st.text('Lowest Company:')
        st.markdown(f'##### {stats["lowest_company"]}')
    with col3:
        bullet(filtered_data, stats, selected_score)

    st.subheader(f"{selected_score} by Industry")
    st.markdown(f'This chart shows the Average Scores across Industries for {selected_score}.  Each industry type is colour coded.')          
    stats = calculate_stats(df, filtered_data, selected_score)
    generate_chart(df, stats, selected_score, "industry")
    filtered_data2 = df.groupby('Country').filter(lambda x: len(x) > 20)
    score_columns = ['Oracle Score', 'Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score']
    st.subheader(f'{selected_score} Coverage: Regional Concentrations')
    col1, col2, col3 = st.columns([1, 2, 1.5], gap='small')
    with col1:
            df_gapminder = px.data.gapminder()
            recognized_countries = df_gapminder['country'].unique()
            df['Mapped Country'] = df['Country'].apply(lambda country: find_closest_match(country, recognized_countries))
            df['Country'] = df['Mapped Country']            
            country_counts = filtered_data2['Country'].value_counts().reset_index()
            country_counts.columns = ['Country', 'count']
            df = filtered_data2.groupby('Country').filter(lambda x: len(x) > 20)
            st.markdown('')
            st.metric(label="UK Companies Rated", value=f"{stats['total_uk_companies']:d}")
            st.markdown('')
            st.metric(label="Average UK Company Score", value=f"{stats['uk_avg_score']:.2f}")
            st.markdown('')
            st.metric(label="Region With Most Companies Rated", value=f"{stats['most_companies_country']} - {stats['most_companies_count']:,}")
    with col2:
        st.plotly_chart(plot_choropleth(country_counts))
    avg_scores = filtered_data2.groupby('Country')[selected_score].mean().round(2).reset_index()
    with col3:
        st.dataframe(
            avg_scores.sort_values(by=selected_score, ascending=False).head(10),
            column_order=["Country", selected_score],
            hide_index=True,
            width=480,
            column_config={
                "Country": st.column_config.TextColumn("Country"),
                selected_score: st.column_config.ProgressColumn(
                    selected_score,
                    format="%f",
                    min_value=0,
                    max_value=max(avg_scores[selected_score].max(), 1),
                )
            }
        )

def deepdive():
    df = load_data()
    st.subheader("Company Deep Dive")
    score_columns = ['Oracle Score', 'Culture Score', 'Capacity Score', 'Conduct Score', 'Collaboration Score']
    option = create_company_selectbox(df, "Company")  
    if option:
        company_data = df[df['Company'] == option]
        median_oracle_score = df['Oracle Score'].median()
    st.divider()
    st.subheader(f'Company Overview - {option}')
    website = company_data['Website'].iloc[0]
    st.markdown(f"{website}")
    col1, col2 = st.columns([50,50])
    with col1:
        st.markdown(f"##### Oracle Score")
    with col2:
        st.markdown(f"##### Oracle Score Components")
    col1, col2, col3 = st.columns([50,25,25])
    with col1:
        oracle_score = company_data['Oracle Score'].values[0]
        st_echarts(options=create_gauge_options(oracle_score, median_oracle_score, 'Oracle Score'), key="oracle_score")
    with col2:
        culture_delta = float(company_data['Culture Score'].iloc[0]) - df['Culture Score'].median()
        capacity_delta = float(company_data['Capacity Score'].iloc[0]) - df['Capacity Score'].median()
        conduct_delta = float(company_data['Conduct Score'].iloc[0]) - df['Conduct Score'].median()
        collaboration_delta = float(company_data['Collaboration Score'].iloc[0]) - df['Collaboration Score'].median()
        st.metric("Culture Score", "{:.2f}".format(company_data['Culture Score'].iloc[0]), "{:.2f}".format(culture_delta))
        st.markdown("") #note to self format these better
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.metric("Capacity Score", "{:.2f}".format(company_data['Capacity Score'].iloc[0]), "{:.2f}".format(capacity_delta))    
    with col3:
        st.metric("Conduct Score", "{:.2f}".format(company_data['Conduct Score'].iloc[0]), "{:.2f}".format(conduct_delta))
        st.markdown('')
        st.markdown("")
        st.markdown("")
        st.markdown("")
        st.metric("Collaboration Score", "{:.2f}".format(company_data['Collaboration Score'].iloc[0]), "{:.2f}".format(collaboration_delta))
    cola, colb, colc, cold, colz = st.columns(5)
    with cola: 
        st.markdown("Industry")
        industry_text = company_data['Industry'].iloc[0]
        st.markdown(f"###### {industry_text}")
    with colb:
        st.markdown('Region')
        geo_text = company_data['Region'].iloc[0]
        st.markdown(f"###### {geo_text}")
    with colc: 
        st.markdown(f'Company Size')
        size = company_data['Company Size'].iloc[0]
        st.markdown(f"###### {size}")
    with cold:
        st.markdown(f'Employees')
        employees = company_data['Employees (Estimate)'].iloc[0]
        st.markdown(f"###### {employees}")
    with colz:
        if company_data is not None and 'B Corp' in company_data.columns:
            b_corp_status = "Certified B Corp" if company_data['B Corp'].iloc[0] == 1 else "Not a Certified B Corp"
        else:
            b_corp_status = "Not a Certified B Corp"
            st.markdown("B Corp Status")
        st.markdown(f'B Corp Status')
        st.markdown(f"###### {b_corp_status}")
    st.markdown(f"###### Description")
    description = company_data['Description'].iloc[0]
    st.caption(f"{description}. Source: Company or Wikipedia")
    col1, col2 = st.columns([1.25, 1])
    with col1:
        st.subheader(f'Radar Plot - {option}')
        st.markdown('This chart shows the company\'s scores across each Component of the Oracle Score.\n\n'
        'Users can add any company from the database as an overlay to compare scores.\n\n'
        'Additionally, users can toggle the median scores to see how the company compares to the median of the universe.')
        scores = company_data[score_columns].iloc[0].tolist()
        selected_company = create_company_selectbox(df, 'Comparator')
        with st.expander('Click To Expand For More Information About Radar Charts'):
            st.markdown('Radar Charts are often used in business and sports to display performance metrics.\n\n'
            'For example, in business, they could compare different products or companies across a range of attributes like price, quality, and customer satisfaction.\n\n'
            'In sports, they might compare athletes across various skills like speed, strength, and agility.\n\n'
            'In our Case they show how a company performs across our 4 C\s.\n\n'
            'Radar charts can quickly highlight areas of strength and weakness. This makes them useful in situations where you want to assess the overall balance of a subject\s attributes, like is a company performing well on one metric but abysmally on another?\n\n'
            'One of the most significant functions of radar charts is their ability to overlay multiple subjects for direct comparison.\n\n'
            'This overlay can provide a clear visual representation of how different subjects compare across the same set of variables. For example, you could overlay the performance metrics of different departments within a company to see which areas each department excels or needs improvement in.')
    with col2: 
            st.markdown('')
            st.markdown('')
            st.markdown('')
            st.markdown('')
            col1, col2 = st.columns([1, 1])
            with col1:
                show_median = st.toggle('Show Median Scores', value=False)
            with col2:
                show_comparison = st.toggle('Show Selected Comparator', value=False)
            radar_chart = create_radar_chart(df, scores, score_columns, selected_company, option, show_median, show_comparison)
            st.plotly_chart(radar_chart)

    st.subheader(f'SDG Revenue Alignment - {option}')
    sdg_expander()
    SDG_Impact_Alignment(df, option)

styles = {
    "container": {"margin": "0px !important", "padding": "0!important", "align-items": "stretch", "background-color": "#fafafa"},
    "icon": {"color": "black", "font-size": "14px"}, 
    "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
    "nav-link-selected": {"background-color": "lightblue", "font-size": "14px", "font-weight": "normal", "color": "black", },
}

st.subheader('Oracle Partnerships with Purpose Tool')
menu = {
    'title': 'Navigation',
    'items': { 
        'Introduction & Instructions' : {
            'action': None, 'item_icon': 'house', 'submenu': {
                'title': None,
                'items': { 
                    'Introduction' : {'action': intro_page, 'item_icon': 'journal-richtext', 'submenu': None},
                    '3rd Party Data Used' : {'action': externaldata, 'item_icon': 'database-dash', 'submenu': None},
                    'Proprietary Data Logic' : {'action': "", 'item_icon': 'database-check', 'submenu': None},
                },
                'menu_icon': 'filter-circle',
                'default_index': 0,
                'with_view_panel': 'main',
                'orientation': 'horizontal',
                'styles': styles
            }
        },
        'Aggregate Data' : {
            'action': None, 'item_icon': 'tablet-landscape', 'submenu': {
                'title': None,
                'items': { 
                    'Filter Universe' : {'action': aggframe, 'item_icon': 'funnel', 'submenu': None},
                    'Analyse Universe' : {'action': analysis1, 'item_icon': 'file-earmark-check', 'submenu': None}
                },
                'menu_icon': 'postcard',
                'default_index': 0,
                'with_view_panel': 'main',
                'orientation': 'horizontal',
                'styles': styles
            }
        },
        'Company Deep Dive' : {
            'action': None, 'item_icon': 'crosshair', 'submenu': {
                'title': None,
                'items': { 
                    'Company Deep Dive' : {'action': deepdive, 'item_icon': 'radar', 'submenu': None}                
                    },
                'menu_icon': 'crosshair',
                'default_index': 0,
                'with_view_panel': 'main',
                'orientation': 'horizontal',
                'styles': styles
            }
        }
    },
    'menu_icon': 'search',
    'default_index': 0,
    'with_view_panel': 'sidebar',
    'orientation': 'vertical',
    'styles': styles
}

def show_menu(menu):
    def _get_options(menu):
        options = list(menu['items'].keys())
        return options

    def _get_icons(menu):
        icons = [v.get('item_icon', 'default_icon') for _k, v in menu['items'].items()]
        return icons

    kwargs = {
        'menu_title': menu['title'] ,
        'options': _get_options(menu),
        'icons': _get_icons(menu),
        'menu_icon': menu['menu_icon'],
        'default_index': menu['default_index'],
        'orientation': menu['orientation'],
        'styles': menu['styles']
    }

    with_view_panel = menu['with_view_panel']
    if with_view_panel == 'sidebar':
        with st.sidebar:
            menu_selection = option_menu(**kwargs)
    elif with_view_panel == 'main':
        menu_selection = option_menu(**kwargs)


    if menu['items'][menu_selection]['submenu']:
        show_menu(menu['items'][menu_selection]['submenu'])

    if menu['items'][menu_selection]['action']:
        menu['items'][menu_selection]['action']()

show_menu(menu)
st.write('Kian 2024. :gear: :mag: for Oracle.')