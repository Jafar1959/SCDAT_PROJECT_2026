import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
# from datetime import date, timedelta
import plotly.graph_objects as go
import calendar
from pathlib import Path, PureWindowsPath    # << for Window & Mac OS path-slash '\' or '/'
import numpy as np
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode

from scdat_colors_26 import color_hex
import scdat_data_26 as data
import scdat_utils_26 as utils


def get_two_year_forecast(datafile_location, current_year, previous_year):

    current_month_no = date.today().month
    formatted_month_no = f"{current_month_no:02}"   # Format the current month number with leading zero if necessary
    current_month_name = calendar.month_name[current_month_no]

    current_forecast_month = formatted_month_no + '_' + current_month_name[0:3] + '-' + str(current_year)
    previous_forecast_month = formatted_month_no + '_' + current_month_name[0:3] + '-' + str(previous_year)

    df_current = data.forecast_df(datafile_location, current_forecast_month)
    df_current = df_current[['SKU', 'SUPPLIER', 'FORECAST']]

    df_previous = data.forecast_df(datafile_location, previous_forecast_month)
    df_previous = df_previous[['SKU', 'FORECAST']]

    df = pd.merge(df_previous, df_current, on='SKU', how='outer')
    df = df[['SKU', 'SUPPLIER', 'FORECAST_x', 'FORECAST_y']]
    df = df.rename(columns={'FORECAST_x': str(previous_year), 'FORECAST_y': str(current_year)})

    return df


def get_two_year_sale(datafile_location, current_year, previous_year):

    current_month_no = date.today().month

    # get current year total sale =========================================
    values_current = data.yearly_sales_df(datafile_location, current_year)
    df_current = values_current[0]
    df_current = df_current[['SKU', 'SUPPLIER', 'TOTAL', 'PRICE']]

    # get the columns of the previous year up to current month
    months = list(range(1, current_month_no + 1))  # Create a list of months [1, 2, ..., 11]
    months = months[:current_month_no]

    # st.write(months)

    month_names = list(calendar.month_name)[1:]  # Get a list of all month names

    cols = ['SKU']
    for i in range(0, len(months)):
        cols.append(month_names[i][0:3] + '-' + str(previous_year)[2:4])

    values_previous = data.yearly_sales_df(datafile_location, previous_year)
    df_previous = values_previous[0]
    df_previous = df_previous[cols]     # get columns up to current month

    current_date = datetime.now()
    total_days_in_month = calendar.monthrange(current_year, current_date.month)[1]

    # Calculate the elapsed percentage
    elapsed_days = current_date.day
    elapsed_percentage = (elapsed_days / total_days_in_month)

    df_previous[cols[len(cols)-1]] = df_previous.apply(lambda x: round(x.iloc[current_month_no] * elapsed_percentage, 0), axis=1)

    column_list = df_previous.iloc[:, 1:]   # get all columns except 1st one 'SKU'

    # df_previous['TOTAL'] = df_previous[cols].sum(axis=1)
    df_previous['TOTAL'] = column_list.sum(axis=1)

    # st.write(df_previous)

    df_previous = df_previous[['SKU', 'TOTAL']]

    df = pd.merge(df_previous, df_current, on='SKU', how='outer')
    df = df[['SKU', 'SUPPLIER', 'TOTAL_x', 'TOTAL_y', 'PRICE']]

    df = df.rename(columns={'TOTAL_x': str(previous_year), 'TOTAL_y': str(current_year)})
    df['Change'] = round((df[str(current_year)] - df[str(previous_year)]) * 100/df[str(previous_year)], 2)

    # st.write(df)

    return df


def get_months_elapsed():

    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day

    total_days = calendar.monthrange(current_year, current_month)

    month_elapsed = (current_month - 1) + (current_day-1)/total_days[1]

    return month_elapsed


def get_header_color(change):

    if change <= -10:
        header_highlight = color_hex(234)

    elif -10 < change <= - 5:
        header_highlight = color_hex(299)

    elif -5 < change <= 5:
        header_highlight = color_hex(134)

    elif 5 < change <= 10:
        header_highlight = color_hex(93)

    elif change > 10:
        header_highlight = color_hex(140)

    else:
        header_highlight = color_hex(146)

    return header_highlight


def filter_dataframe(df, supplier, model):

    if supplier != 'ALL':
        df = df[df["SUPPLIER"] == supplier]

    if model.upper()[0:2] == 'RV':
        df = df.loc[lambda row: row['SKU'].str.startswith(model.upper())]

    elif model.upper()[0:2] != 'RV' and model.upper() != 'ALL':
        df = df.loc[lambda row: row['SKU'].str.endswith(model.upper())]

    df.reset_index(drop=True, inplace=True)  # order index
    df.index = range(1, df.shape[0] + 1)
    return df


def filter_custom_sku_list(datafile_location, df):
    # create product list df
    file_path = Path(PureWindowsPath(datafile_location + "Sales\\Monthly_Sales\\SKU_List.xlsx"))
    df_sku = pd.read_excel(file_path, sheet_name='Sheet1', header=0)
    df_sku = df_sku.dropna()

    sku_list = df_sku['SKU'].to_list()

    sku_list_upper = [word.upper() for word in sku_list]

    df_filtered = df[df['SKU'].isin(sku_list_upper)]

    return df_filtered

def reduced_top_margin():
    # reduced top margin << ============================================
    st.markdown("""
           <style>
               .block-container {
                   margin-top: -3.2rem !important;
               }
           </style>
           """, unsafe_allow_html=True)
    return

def format_header_txt(txt, less_10, less_05, less_05_more_05, more_05, more_10, total_change_txt):
    reduced_top_margin()

    df = pd.DataFrame({txt: [],
                       '< -10% (' + str(less_10) + ')': [],
                       '< -5% (' + str(less_05) + ')': [],
                       '-5% to 5% (' + str(less_05_more_05) + ')': [],
                       '> 5% (' + str(more_05) + ')': [],
                       '> 10% (' + str(more_10) + ')': [],
                       'Overall ' + total_change_txt: [],
                       })

    col1, col2 = st.columns([5, 0.97])

    fig = go.Figure(data=[go.Table(
        columnwidth=[50, 8, 7, 10, 7, 8, 9],

        header=dict(values=list(df.columns),
                    fill_color=[color_hex(363), color_hex(234), color_hex(299), color_hex(134), color_hex(93), color_hex(140), color_hex(118)],
                    font=dict(family="Arial", size=15, color='white'),
                    line_color='white',
                    height=22,
                    align=['left', 'center']),
           )])

    fig.update_layout(height=33, margin=dict(l=0, r=0, b=0, t=0))

    with col1:

        st.plotly_chart(fig)    #, use_container_width=True)

    return

def display_product_chit_OLD(datafile_location):

    current_year = date.today().year

    # current_year1 = date.today().year
    # years = [current_year1 - i for i in range(0, 5)]  # previous 4 years
    # current_year = st.sidebar.selectbox("Select a year:", years)

    previous_year = current_year - 1

    months_elapsed = get_months_elapsed()

    df_sale = get_two_year_sale(datafile_location, current_year, previous_year)

    df_sale = df_sale.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]

    supplier_list = df_sale['SUPPLIER'].tolist()
    supplier_list.append('ALL')
    supplier_list = list(set(supplier_list))
    supplier_list.sort()

    # Create a checkbox
    checked = st.sidebar.checkbox("Custom SKU List", value=False)

    if checked:
        st.sidebar.write("Update ../Monthly_Sales/SKU_List.xlsx")
        df_filtered = filter_custom_sku_list(datafile_location, df_sale)

    else:
        supplier = st.sidebar.selectbox("SUPPLIER", supplier_list)
        model = st.sidebar.text_input("MODEL / COLOR", "ALL")

        df_filtered = filter_dataframe(df_sale, supplier, model)  # st.write(df_sale)

    df_filtered = df_filtered.sort_values([str(current_year), 'SKU'], ascending=[False, True])   # sort based on current year sales
    df_filtered.reset_index(drop=True, inplace=True)
    df_filtered.index = range(1, df_filtered.shape[0] + 1)

    # st.write(df_filtered)
    # st.stop()

    if len(df_filtered) > 50:
        n = st.sidebar.number_input('START INDEX', min_value=1, max_value=501, step=50)
        n1 = n
        n2 = n + 49
        df1 = df_filtered[n1 - 1:n2].copy()

    else:
        df1 = df_filtered.copy()
        n1 = 1
        n2 = len(df1)

    sku_list = df1['SKU'].tolist()

    # create appropriate header ==============================
    if checked:
        txt = str(previous_year) + ' & ' + str(current_year) + ' Sales Comparison | Model: Selected | ' + utils.get_todays_date() + ' | ' + str(n1)\
              + ' - ' + str(n2)

    else:
        txt = str(previous_year) + ' & ' + str(current_year) + ' Sales Comparison | ' + 'Supplier: ' + supplier + ' | Model: ' + model.upper() + ' | '\
           + utils.get_todays_date() + ' | ' + str(n1) + ' - ' + str(n2)   # + str(round(months_elapsed, 1)) + " Month Average"

    total_change = (df1[str(current_year)].sum() - df1[str(previous_year)].sum()) * 100/df1[str(previous_year)].sum()

    if total_change > 0:

        total_change_txt = str(round(total_change, 0))[:-2] + '% \u2B06'  # bold up arrow
    else:
        total_change_txt = str(round(total_change, 0) * -1)[:-2] + '% \u2B07'    # bold down arrow

    change_list = df1['Change'].tolist()

    less_10 = sum(1 for num in change_list if num <= -10)
    less_05 = sum(1 for num in change_list if -10 < num <= -5)
    less_05_more_05 = sum(1 for num in change_list if -5 < num <= 5)
    more_05 = sum(1 for num in change_list if 5 < num <= 10)
    more_10 = sum(1 for num in change_list if num > 10)

    format_header_txt(txt, less_10, less_05, less_05_more_05, more_05, more_10, total_change_txt)

    mygrid = utils.make_grid(10, 6)  # (row, col)
    row = 0
    col = 0

    for i in range(0, len(df1)):

        df_sale_temp = df1[df1['SKU'] == sku_list[i]]
        # st.write(df_sale_temp)

        df = pd.DataFrame({sku_list[i]: ['Total Sale', 'Avg. Monthly Sale'],
                          previous_year: [df_sale_temp.iloc[0][2], round(df_sale_temp.iloc[0][2]/months_elapsed, 0)],
                          current_year: [df_sale_temp.iloc[0][3], round(df_sale_temp.iloc[0][3]/months_elapsed, 0)]

                           })

        change = df_sale_temp.iloc[0][5]
        header_highlight = get_header_color(change)

        fig = go.Figure(data=[go.Table(
            columnwidth=[12, 8],

            header=dict(values=list(df.columns),
                        fill_color=[color_hex(19),  color_hex(56), header_highlight],  # header_color,
                        font=dict(family="Arial", size=12, color='white'),
                        line_color='white',
                        height=22,
                        align=['center']),

            cells=dict(
                values=[df[sku_list[i]], df[previous_year], df[current_year]],
                # values=[df_summary],
                font=dict(family="Arial", size=11, color='black'),
                height=22,
                fill_color=[color_hex(201), color_hex(186), color_hex(12)],
                line_color='white',
                align=['left', 'center']))
                ])

        fig.update_layout(height=69, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig, width='stretch')

        col = col + 1

        if col == 5:
            col = 0
            row = row + 1

    utils.download_csv(df1, 'Download ' + str(len(df1)))
    utils.download_csv(df_filtered, 'Download All')

    ytd_sales_summary(df_filtered, current_year, previous_year, months_elapsed, supplier)
    return

def display_product_chit(datafile_location):
    # ===================== Setup =====================
    current_year = date.today().year
    previous_year = current_year - 1
    months_elapsed = get_months_elapsed()

    # Load and pre-filter data
    df_sale = get_two_year_sale(datafile_location, current_year, previous_year)
    df_sale = df_sale[~df_sale['SKU'].str.startswith('RVA')]

    # ===================== Sidebar Filters =====================
    supplier_list = sorted(set(df_sale['SUPPLIER']).union({'ALL'}))

    checked = st.sidebar.checkbox("Custom SKU List", value=False)

    if checked:
        st.sidebar.write("Update ../Monthly_Sales/SKU_List.xlsx")
        df_filtered = filter_custom_sku_list(datafile_location, df_sale)
        supplier = "Selected"
        model = "Selected"
    else:
        supplier = st.sidebar.selectbox("SUPPLIER", supplier_list)
        model = st.sidebar.text_input("MODEL / COLOR", "ALL")
        df_filtered = filter_dataframe(df_sale, supplier, model)

    # ===================== Sorting =====================
    df_filtered = df_filtered.sort_values(
        [str(current_year), 'SKU'],
        ascending=[False, True]
    ).reset_index(drop=True)

    df_filtered.index += 1  # start index from 1

    # ===================== Pagination =====================
    total_rows = len(df_filtered)

    if total_rows > 50:
        start = st.sidebar.number_input('START INDEX', min_value=1, max_value=501, step=50)
        end = start + 49
        df1 = df_filtered.iloc[start - 1:end]
    else:
        start, end = 1, total_rows
        df1 = df_filtered.copy()

    # ===================== Header =====================
    base_txt = f"{previous_year} & {current_year} Sales Comparison"

    if checked:
        txt = f"{base_txt} | Model: Selected | {utils.get_todays_date()} | {start} - {end}"
    else:
        txt = f"{base_txt} | Supplier: {supplier} | Model: {model.upper()} | {utils.get_todays_date()} | {start} - {end}"

    # ===================== Summary Metrics =====================
    prev_sum = df1[str(previous_year)].sum()
    curr_sum = df1[str(current_year)].sum()

    total_change = ((curr_sum - prev_sum) / prev_sum * 100) if prev_sum != 0 else 0

    arrow = '\u2B06' if total_change > 0 else '\u2B07'
    total_change_txt = f"{abs(round(total_change))}% {arrow}"

    change_series = df1['Change']

    less_10 = (change_series <= -10).sum()
    less_05 = ((change_series > -10) & (change_series <= -5)).sum()
    mid = ((change_series > -5) & (change_series <= 5)).sum()
    more_05 = ((change_series > 5) & (change_series <= 10)).sum()
    more_10 = (change_series > 10).sum()

    format_header_txt(txt, less_10, less_05, mid, more_05, more_10, total_change_txt)

    # ===================== Grid =====================
    mygrid = utils.make_grid(10, 6)

    # Pre-extract values (avoid repeated DataFrame filtering)
    records = df1.to_dict('records')

    # st.write(records)
    # st.stop()

    row = col = 0

    for rec in records:
        sku = rec['SKU']
        prev_val = rec[str(previous_year)]
        curr_val = rec[str(current_year)]
        change = rec['Change']

        # Prepare mini table data
        df = pd.DataFrame({
            sku: ['Total Sale', 'Avg. Monthly Sale'],
            previous_year: [prev_val, round(prev_val / months_elapsed, 0)],
            current_year: [curr_val, round(curr_val / months_elapsed, 0)]
        })

        header_highlight = get_header_color(change)

        fig = go.Figure(data=[go.Table(
            columnwidth=[12, 8],
            header=dict(
                values=list(df.columns),
                fill_color=[color_hex(19), color_hex(56), header_highlight],
                font=dict(family="Arial", size=12, color='white'),
                line_color='white',
                height=22,
                align=['center']
            ),
            cells=dict(
                values=[df[col] for col in df.columns],
                font=dict(family="Arial", size=11, color='black'),
                height=22,
                fill_color=[color_hex(201), color_hex(186), color_hex(12)],
                line_color='white',
                align=['left', 'center']
            )
        )])

        fig.update_layout(height=69, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig, width='stretch')

        # Grid positioning
        col += 1
        if col == 5:
            col = 0
            row += 1

    # ===================== Downloads =====================
    col1, col2 = st.columns([1, 1])
    with col1:
        utils.download_csv(df1, f'Download {len(df1)}')
    with col2:
        utils.download_csv(df_filtered, 'Download All')

    # ===================== Summary =====================
    ytd_sales_summary(df_filtered, current_year, previous_year, months_elapsed, supplier)

    return

def ytd_sales_summary_OLD(df, current_year, previous_year, month_elapsed, supplier):

    # st.write(df)

    df['MONTHLY'] = round(df[str(current_year)]/month_elapsed, 0)

    df_sink = df.loc[lambda row: ~ row['SKU'].str.startswith('RVB6', 'RVF')]
    df_tub = df.loc[lambda row: row['SKU'].str.startswith('RVB6')]
    df_faucet = df.loc[lambda row: row['SKU'].str.startswith('RVF')]

    df_summary = pd.DataFrame({})

    chunk_size = st.sidebar.number_input('CHUNK SIZE', min_value=10, max_value=50, step=5, value=50)
    total_rows = min(len(df_sink), 450)

    for n in range(0, total_rows, chunk_size):
        df_50 = df_sink.iloc[n:n + chunk_size]

    # for n in range(0, n2, 50):
        # df_50 = df_sink[n:n+50]

        # st.write(df_50)
        # st.write(len(df_50))

        df_50.reset_index(drop=True, inplace=True)
        df_50.index = range(1, df_50.shape[0] + 1)

        sale_highest = df_50.iloc[0][6]
        sale_lowest = df_50.iloc[min(len(df_50)-1, 49)][6]

        total_previous_year = df_50[str(previous_year)].sum()
        total_current_year = df_50[str(current_year)].sum()

        # n3 = min(len(df_sink), (n + chunk_size))
        n3 = min(total_rows, (n + chunk_size))

        df_sink_temp = pd.DataFrame({'S/N': [str(n+1) + ' - ' + str(n3)],
                                     'Sales/Month': [str(sale_highest)[:-2] + ' - ' + str(sale_lowest)[:-2]],
                                     str(previous_year): [total_previous_year],
                                     str(current_year): [total_current_year],
                                     })

        if n == 0:
            df_summary = df_sink_temp

        else:
            df_summary = pd.concat([df_summary, df_sink_temp])

    if supplier in ('ALL', 'Nicos', 'Wisdom'):  # add Bathtub row if.....++++++++++++++++++++++++

        sale_highest_tub = df_tub.iloc[0][6]
        sale_lowest_tub = df_tub.iloc[len(df_tub)-1][6]
        total_previous_year_tub = df_tub[str(previous_year)].sum()
        total_current_year_tub = df_tub[str(current_year)].sum()

        df_tub_temp = pd.DataFrame({'S/N': ['BATHTUB'],
                                    'Sales/Month': [str(sale_highest_tub)[:-2] + ' - ' + str(sale_lowest_tub)[:-2]],
                                    str(previous_year): [total_previous_year_tub],
                                    str(current_year): [total_current_year_tub],
                                    })

        df_summary = pd.concat([df_summary, df_tub_temp])

    if supplier in 'ALL':  # add Faucet row if..... +++++++++++++++++++++++++++++++++++++++++

        sale_highest_faucet = df_faucet.iloc[0][6]
        sale_lowest_faucet = df_faucet.iloc[len(df_tub)-1][6]
        total_previous_year_faucet = df_faucet[str(previous_year)].sum()
        total_current_year_faucet = df_faucet[str(current_year)].sum()

        df_faucet_temp = pd.DataFrame({'S/N': ['FAUCET'],
                                    'Sales/Month': [str(sale_highest_faucet)[:-2] + ' - ' + str(sale_lowest_faucet)[:-2]],
                                    str(previous_year): [total_previous_year_faucet],
                                    str(current_year): [total_current_year_faucet],
                                    })

        df_summary = pd.concat([df_summary, df_faucet_temp])

    # calculate 'Difference' and 'Percentage' ==================================================================
    df_summary['Difference'] = df_summary[str(current_year)] - df_summary[str(previous_year)]

    df_summary['Percentage'] = round(df_summary['Difference'] * 100/df_summary[str(previous_year)], 2)

    # df_summary['Percentage'] = df_summary['Percentage'].replace([np.inf, -np.inf, np.nan], 'New')   # If division by Zero > Change value to 'New'

    df_summary['Percentage'] = [    # replace inf with 'New'
        "New" if (v is None or v == "" or (isinstance(v, float) and np.isinf(v)))
        else f"{v:.2f}"
        for v in df_summary['Percentage']]

    df_summary = df_summary.fillna(0)

    # Add alternating 'color1' and 'color2' values in a new column
    if len(df_summary) > 1:
        df_summary['color'] = ['rgb(240, 248, 255)' if i % 2 == 0 else 'rgb(189, 215, 231)' for i in range(len(df_summary))]
    else:
        df_summary['color'] = ['rgb(189, 215, 231)']

    cols = df_summary.columns
    font_colors = [color_hex(121) if v < 0 else 'black' for v in df_summary['Difference']]

    fig = go.Figure(data=[go.Table(
         columnwidth=[16, 18, 16, 16, 18],
         header=dict(values=[cols[0], cols[1], cols[2], cols[3], cols[4], cols[5]],
                    fill_color=[color_hex(234)] + [color_hex(66)] * 3 + [color_hex(390)],
                    line_color='white',
                    font_color='white',
                    font_size=18,
                    height=34,
                    align=['center']),
         cells=dict(
            values=[df_summary['S/N'], df_summary['Sales/Month'], df_summary[str(previous_year)], df_summary[str(current_year)],
                    df_summary['Difference'], df_summary['Percentage']],
            # format=[None, None, None, None, None, ".2f"],

        font_size=20,
            font=dict(color=[font_colors]),
            height=40,
            fill_color=[df_summary.color],
            line_color='white',
            align=['center', 'center', 'right']))
        ])

    # add outer boarder around the table
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,  # full canvas
        line=dict(color=color_hex(39), width=3),
        layer="above"
    )

    fig.update_layout(height=len(df_summary) * 40 + 35, margin=dict(l=0, r=0, b=0, t=0))

    col1, col2, col3 = st.columns([1, 0.8, 0.4])

    with col1:
        txt = 'YTD | Sales Summary ' + str(previous_year) + ' & ' + str(current_year) + ' | ' + 'Supplier: ' + supplier + ' | ' + \
              utils.get_todays_date()

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:2%; line-height:0em; '
            f'margin-top:10px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig, width='stretch')

    utils.download_csv(df_summary, 'Download Summary')
    st.write('')
    st.write('')

    display_supplier_wise_summary(df, current_year, previous_year, col2)
    return

def ytd_sales_summary(df, current_year, previous_year, month_elapsed, supplier):

    # ===================== Preprocessing =====================
    # Create monthly sales column (vectorized)
    df['MONTHLY'] = (df[str(current_year)] / month_elapsed).round(0)

    # Split dataset into categories using vectorized string filters
    df_sink = df[~df['SKU'].str.startswith(('RVB6', 'RVF'))]
    df_tub = df[df['SKU'].str.startswith('RVB6')]
    df_faucet = df[df['SKU'].str.startswith('RVF')]

    # ===================== Chunk Summary (Sink) =====================
    chunk_size = st.sidebar.number_input(
        'CHUNK SIZE', min_value=10, max_value=50, step=5, value=50
    )

    total_rows = min(len(df_sink), 450)

    summary_rows = []  # collect rows → faster than concat

    for start in range(0, total_rows, chunk_size):
        end = min(total_rows, start + chunk_size)

        df_chunk = df_sink.iloc[start:end]

        if df_chunk.empty:
            continue

        # Get highest & lowest monthly sales in chunk
        monthly_vals = df_chunk['MONTHLY']
        sale_highest = int(monthly_vals.iloc[0])
        sale_lowest = int(monthly_vals.iloc[-1])

        # Aggregate totals
        total_prev = df_chunk[str(previous_year)].sum()
        total_curr = df_chunk[str(current_year)].sum()

        summary_rows.append({
            'S/N': f"{start + 1} - {end}",
            'Sales/Month': f"{sale_highest} - {sale_lowest}",
            str(previous_year): total_prev,
            str(current_year): total_curr
        })

    # ===================== Additional Categories =====================
    def add_category_row(df_cat, label):
        """Helper to summarize a category (bathtub/faucet)"""
        if df_cat.empty:
            return None

        monthly_vals = df_cat['MONTHLY']
        return {
            'S/N': label,
            'Sales/Month': f"{int(monthly_vals.iloc[0])} - {int(monthly_vals.iloc[-1])}",
            str(previous_year): df_cat[str(previous_year)].sum(),
            str(current_year): df_cat[str(current_year)].sum()
        }

    # Add bathtub summary if applicable
    if supplier in ('ALL', 'Nicos', 'Wisdom'):
        row = add_category_row(df_tub, 'BATHTUB')
        if row:
            summary_rows.append(row)

    # Add faucet summary if applicable
    if supplier == 'ALL':
        row = add_category_row(df_faucet, 'FAUCET')
        if row:
            summary_rows.append(row)

    # ===================== Build Summary DataFrame =====================
    df_summary = pd.DataFrame(summary_rows)

    # ===================== Calculations =====================
    df_summary['Difference'] = (
        df_summary[str(current_year)] - df_summary[str(previous_year)]
    )

    # Avoid division by zero
    df_summary['Percentage'] = np.where(
        df_summary[str(previous_year)] == 0,
        "New",
        ((df_summary['Difference'] * 100) / df_summary[str(previous_year)]).round(2)
    )

    # Format percentage column
    df_summary['Percentage'] = df_summary['Percentage'].apply(
        lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x
    )

    # ===================== Styling =====================
    # Alternating row colors
    df_summary['color'] = [
        'rgb(240, 248, 255)' if i % 2 == 0 else 'rgb(189, 215, 231)'
        for i in range(len(df_summary))
    ]

    # Color negative values differently
    font_colors = [
        color_hex(121) if v < 0 else 'black'
        for v in df_summary['Difference']
    ]

    # ===================== Plotly Table =====================
    cols = df_summary.columns

    fig = go.Figure(data=[go.Table(
        columnwidth=[16, 18, 16, 16, 18],
        header=dict(
            values=cols[:6],
            fill_color=[color_hex(234)] + [color_hex(66)] * 3 + [color_hex(390)],
            line_color='white',
            font_color='white',
            font_size=18,
            height=34,
            align=['center']
        ),
        cells=dict(
            values=[df_summary[col] for col in cols[:6]],
            font_size=20,
            font=dict(color=[font_colors]),
            height=40,
            fill_color=[df_summary['color']],
            line_color='white',
            align=['center', 'center', 'right']
        )
    )])

    # Add border
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,
        line=dict(color=color_hex(39), width=3),
        layer="above"
    )

    fig.update_layout(
        height=len(df_summary) * 40 + 35,
        margin=dict(l=0, r=0, b=0, t=0)
    )

    # ===================== UI Display =====================
    col1, col2, col3 = st.columns([1, 0.8, 0.4])

    with col1:
        txt = f"YTD | Sales Summary {previous_year} & {current_year} | Supplier: {supplier} | {utils.get_todays_date()}"

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
            f'margin-top:10px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig, width='stretch')

    # ===================== Downloads =====================
    utils.download_csv(df_summary, 'Download Summary')
    st.write('')

    # ===================== Additional Summary =====================
    display_supplier_wise_summary(df, current_year, previous_year, col2)

    return

def display_supplier_wise_summary(df, current_year, previous_year, col2):

    df = df.groupby('SUPPLIER').aggregate({str(previous_year): 'sum', str(current_year): 'sum'}).reset_index()
    df['Difference'] = df[str(current_year)] - df[str(previous_year)]
    df['Percentage'] = round(df['Difference'] * 100 / df[str(previous_year)], 2)

    df['Percentage'] = [
        "New" if (v is None or v == "" or (isinstance(v, float) and np.isinf(v)))
        else f"{v:.2f}"
        for v in df['Percentage']]

    if len(df) > 1:
        df['color'] = ['rgb(240, 248, 255)' if i % 2 == 0 else 'rgb(255, 231, 186)' for i in range(len(df))]
    else:
        df['color'] = ['rgb(255, 231, 186)']

    with col2:
        txt = 'YTD | Supplier-wise Sales Summary ' + str(previous_year) + ' & ' + str(current_year)

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
            f'margin-top:10px"> {txt} </p>', unsafe_allow_html=True)

        cols = df.columns
        font_colors = [color_hex(121) if v < 0 else 'black' for v in df['Difference']]

        fig = go.Figure(data=[go.Table(
            columnwidth=[20, 12, 12, 16, 16],
            header=dict(values=[cols[0], cols[1], cols[2], cols[3], cols[4]],
                        fill_color=[color_hex(234)] + [color_hex(66)] * 2 + [color_hex(390)],
                        line_color='white',
                        font_color='white',
                        font_size=18,
                        height=34,
                        align=['left', 'center']),

            cells=dict(
                values=[df['SUPPLIER'], df[str(previous_year)], df[str(current_year)], df['Difference'], df['Percentage']],
               #format=[None, None, None, None, ".2f"],
                font_size=14,
                font=dict(color=[font_colors]),
                height=26,
                fill_color=[df.color],
                line_color='white',
                align=['left', 'right']))
        ])

        # add outer boarder around the table
        fig.add_shape(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,  # full canvas
            line=dict(color=color_hex(32), width=3),
            layer="above"
        )

        fig.update_layout(height=len(df) * 26 + 34, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, width='stretch')

    return


def display_return_product_chit_OLD(datafile_location):

    def get_total_return(sku, df):
        df_temp = df[df['SKU'] == sku]
        if len(df_temp) > 0:
            total_return = df_temp['SKU'].count()
        else:
            total_return = 0
        return total_return

    def get_total_condition(sku, df, condition):
        df_temp = df[df['SKU'] == sku]
        df_temp = df_temp[df_temp['CONDITION'] == condition]

        if len(df_temp) > 0:
            total_condition = df_temp['SKU'].count()
        else:
            total_condition = 0
        return total_condition

    current_year = date.today().year
    previous_year = current_year - 1

    current_month = utils.get_short_month_name(date.today().month)

    df_scan = data.return_scan_df(datafile_location)
    # st.write(df_scan)
    # st.stop()

    cutoff_date = date.today() - timedelta(days=30)
    # st.write(cutoff_date)

    df_scan_30days = df_scan[df_scan['RETURN DATE'] >= cutoff_date]
    # st.write(df_scan_30days)

    start_of_year = date.today().replace(month=1, day=1)

    df_scan = df_scan[df_scan['RETURN DATE'] >= start_of_year]      # get scan file from 1st day of the year


    df_2year = get_two_year_sale(datafile_location, current_year, previous_year)
    df_2year = df_2year[['SKU', str(current_year)]]

    # st.write(df_2year)

    df_30days = data.last_30_days_sales_df(datafile_location, current_month, str(current_year))
    df_30days = df_30days[['SKU', 'SUPPLIER', 'TOTAL_30_DAYS']]

    # st.write(df_30days)

    df = pd.merge(df_2year, df_30days, on=["SKU"], how='left')
    df = df[['SKU', 'SUPPLIER', str(current_year), 'TOTAL_30_DAYS']]

    df = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # remove accessories <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # st.write(df)

    df['YTD Return'] = df.apply(lambda x: get_total_return(x.iloc[0].strip(), df_scan), axis=1)

    # st.write(df)
    # st.stop()

    df['Return %'] = df['YTD Return'] * 100/df[str(current_year)]
    df['Return %'] = round(df['Return %'], 2)

    df['30days Return'] = df.apply(lambda x: get_total_return(x.iloc[0], df_scan_30days), axis=1)
    df['30days Return %'] = df['30days Return'] * 100 / df['TOTAL_30_DAYS']
    df['30days Return %'] = round(df['30days Return %'], 2)

    df['YTD Unopend'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan, 'New'), axis=1)
    df['YTD Quality Checked'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan, 'QC'), axis=1)
    df['YTD Broken'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan, 'Broken'), axis=1)
    df['YTD Refurbished'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan, 'Refurbished'), axis=1)
    df['YTD Open Box'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan, 'Open Box'), axis=1)

    df['30d Unopend'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan_30days, 'New'), axis=1)
    df['30d Quality Checked'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan_30days, 'QC'), axis=1)
    df['30d Broken'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan_30days, 'Broken'), axis=1)
    df['30d Refurbished'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan_30days, 'Refurbished'), axis=1)
    df['30d Open Box'] = df.apply(lambda x: get_total_condition(x.iloc[0], df_scan_30days, 'Open Box'), axis=1)

    df['Damage %'] = round(df['YTD Broken'] * 100/df['YTD Return'], 0)

    df = df.fillna(0)

    # st.write(df)

    df_filtered = df[df[str(current_year)] > 10]    # 60 - 5 pcs. per month <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    sort_type = st.sidebar.radio('SORT BY', ['Return Percentage', 'Damage Percentage'])

    total_sale = df[str(current_year)].sum()
    total_return = df['YTD Return'].sum()
    return_percent = round(total_return * 100/total_sale, 1)

    total_new = df['YTD Unopend'].sum()
    new_percent = round(total_new * 100/total_return, 1)

    total_qc = df['YTD Quality Checked'].sum()
    qc_percent = round(total_qc * 100/total_return, 1)

    total_refurb = df['YTD Refurbished'].sum()
    refurb_percent = round(total_refurb * 100 / total_return, 1)

    total_open_box = df['YTD Open Box'].sum()
    open_box_percent = round(total_open_box * 100 / total_return, 1)

    total_damage = df['YTD Broken'].sum()
    damage_percent = round(total_damage * 100 / total_return, 1)

    total_missing = total_return - (total_new + total_qc + total_refurb + total_open_box + total_damage)
    missing_percent = round(total_missing * 100 / total_return, 1)

    all_data = [total_return, return_percent, total_new, new_percent, total_qc, qc_percent, total_refurb, refurb_percent, total_open_box,
                open_box_percent, total_damage, damage_percent, total_missing, missing_percent]

    txt = 'Returned: ' + ut.format_num(str(total_return)) + ' [' + str(return_percent) + '%] '
    txt = txt + ' | New: ' + ut.format_num(str(total_new)) + ' [' + str(new_percent) + '%] '
    txt = txt + ' | QC: ' + ut.format_num(str(total_qc)) + ' [' + str(qc_percent) + '%] '
    txt = txt + ' | Refurbish: ' + ut.format_num(str(total_refurb)) + ' [' + str(refurb_percent) + '%] '
    txt = txt + ' | Open Box: ' + ut.format_num(str(total_open_box)) + ' [' + str(open_box_percent) + '%] '
    txt = txt + ' | Damage: ' + ut.format_num(str(total_damage)) + ' [' + str(damage_percent) + '%] '
    txt = txt + ' | Missing: ' + ut.format_num(str(total_missing)) + ' [' + str(missing_percent) + '%] '
    txt = txt + ' | ' + ut.get_todays_date()

    if sort_type == 'Return Percentage':
        df_filtered = df_filtered.sort_values('Return %', ascending=False)

        txt = 'YTD Return Percentage | ' + txt

    elif sort_type == 'Damage Percentage':
        df_filtered = df_filtered.sort_values('Damage %', ascending=False)

        txt = 'YTD Damage Percentage | ' + txt

    df_filtered.reset_index(drop=True, inplace=True)
    df_filtered.index = range(1, df_filtered.shape[0] + 1)

    # ============================ Display Chit =========================================================
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 16px ;border-radius:1%;'
        f' line-height:0em; margin-top:5px"> {txt} </p>',
        unsafe_allow_html=True)

    mygrid = ut.make_grid(10, 6)  # (row, col)
    row = 0
    col = 0

    sku_list = df_filtered['SKU'].tolist()

    df_filtered = df_filtered[0:24]

    for i in range(0, len(df_filtered)):

        df_temp = df_filtered[df_filtered['SKU'] == sku_list[i]]

        ytd_sale = df_temp.iloc[0][2]
        ytd_return = df_temp.iloc[0][4]
        ytd_return_percent = round(df_temp.iloc[0][5], 0)
        ytd_unopened = df_temp.iloc[0][8]
        ytd_quality_checked = df_temp.iloc[0][9]
        ytd_broken = df_temp.iloc[0][10]
        ytd_refurbished = df_temp.iloc[0][11]
        ytd_openbox = df_temp.iloc[0][12]

        day30_sale = round(df_temp.iloc[0][3], 0)
        day30_return = df_temp.iloc[0][6]
        day30_return_percent = round(df_temp.iloc[0][7], 0)
        day30_unopened = df_temp.iloc[0][13]
        day30_quality_checked = df_temp.iloc[0][14]
        day30_broken = df_temp.iloc[0][15]
        day30_refurbished = df_temp.iloc[0][16]
        day30_openbox = df_temp.iloc[0][17]

        df1 = pd.DataFrame({sku_list[i]: ['Sale', 'Return', 'Return %', 'Unopened', 'Quality Checked', 'Damaged', 'Refurbushed', 'Open Box'],
                           current_year: [ytd_sale, ytd_return, ytd_return_percent, ytd_unopened,  ytd_quality_checked, ytd_broken, ytd_refurbished,
                                          ytd_openbox],
                           'Last 30 Days': [day30_sale, day30_return, day30_return_percent, day30_unopened,  day30_quality_checked, day30_broken,
                                            day30_refurbished, day30_openbox]

                           })

        # st.write(df1)

        df1['Color1'] = ''  # add a blank column 'Color'
        df1['Color2'] = ''
        df1['Color3'] = ''

        # set color for all rows
        for c in range(0, len(df1)):
            df1.at[c, 'Color1'] = 'rgb(211, 211, 211)'
            df1.at[c, 'Color2'] = 'rgb(180, 238, 180)'
            df1.at[c, 'Color3'] = 'rgb(178, 223, 238)'

        # set color for specific rows
        if sort_type == 'Return Percentage':
            df1.at[2, 'Color1'] = 'rgb(255, 182, 193)'
            df1.at[2, 'Color2'] = 'rgb(255, 182, 193)'
            df1.at[2, 'Color3'] = 'rgb(255, 182, 193)'

        elif sort_type == 'Damage Percentage':
            df1.at[1, 'Color1'] = 'rgb(255, 182, 193)'
            df1.at[1, 'Color2'] = 'rgb(255, 182, 193)'
            df1.at[1, 'Color3'] = 'rgb(255, 182, 193)'

            df1.at[5, 'Color1'] = 'rgb(255, 182, 193)'
            df1.at[5, 'Color2'] = 'rgb(255, 182, 193)'
            df1.at[5, 'Color3'] = 'rgb(255, 182, 193)'

        # st.write(df1)

        cols = df1.columns

        fig = go.Figure(data=[go.Table(
              columnwidth=[13, 8, 11],

              header=dict(values=(cols[0], cols[1], cols[2]),   #list(df1.columns),
                        fill_color=[color_hex(118), color_hex(140), color_hex(56)],  # header_color,
                        font=dict(family="Arial", size=12, color='white'),
                        line_color='white',
                        height=22,
                        align=['left', 'center']),

              cells=dict(
                values=[df1[sku_list[i]], df1[current_year], df1['Last 30 Days']],
                # values=[df_summary],
                font=dict(family="Arial", size=11, color='black'),
                height=22,
                fill_color=[df1['Color1'], df1['Color2'], df1['Color3']],
                line_color='white',
                align=['left', 'center']))
        ])

        fig.update_layout(height=200, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig, use_container_width=True)

        col = col + 1

        if col == 6:
            col = 0
            row = row + 1

    # ============================= Display Table =====================================
    return_product_wise_summary(df, all_data)

    AgGrid(df, fit_columns_on_grid_load=True)
    ut.download_csv(df, 'Download Data')

    df_scan['RETURN DATE'] = pd.to_datetime(df_scan['RETURN DATE'])
    df_scan['RETURN DATE'] = df_scan['RETURN DATE'].dt.strftime('%Y-%m-%d')  # convert str to date format

    df_scan = df_scan.sort_values('RETURN DATE', ascending=False)
    AgGrid(df_scan, fit_columns_on_grid_load=True)
    ut.download_csv(df_scan, 'Download Return Scan Data')

    return


def return_product_wise_summary_OLD(df, all_data):

    txt = 'YTD - Product-wise Return Summary | ' + ut.get_todays_date()

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
        f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

    st.write('')

    current_year = date.today().year

    mygrid = ut.make_grid(10, 5)  # (row, col)
    row = 0
    col = 0

    product_list = ['ALL', 'RVH', 'RVM', 'RVG', 'RVL', 'RVB', 'RVB6', 'RVF']
    txt_list = ['All Sink, Tub & Faucet', 'Handmade Sink', 'Drawn Sink', 'Granite Sink', 'Fireclay Sink', 'Bathroom Sink',
                'Bathtub', 'Faucet']

    for i in range(0, len(product_list)):

        if i == 0:  # get data for all models
            total_return = all_data[0]
            return_percent = all_data[1]
            total_new = all_data[2]
            new_percent = all_data[3]
            total_qc = all_data[4]
            qc_percent = all_data[5]
            total_refurb = all_data[6]
            refurb_percent = all_data[7]
            total_open_box = all_data[8]
            open_box_percent = all_data[9]
            total_damage = all_data[10]
            damage_percent = all_data[11]
            total_missing = all_data[12]
            missing_percent = all_data[13]

        else:
            df_temp = df.loc[lambda row: row['SKU'].str.startswith(product_list[i])]

            if product_list[i] == 'RVB':
                df_temp = df_temp.loc[lambda row: ~ row['SKU'].str.startswith('RVB6')]

            total_sale = df_temp[str(current_year)].sum()
            total_return = df_temp['YTD Return'].sum()
            return_percent = round(total_return * 100 / total_sale, 1)

            total_new = df_temp['YTD Unopend'].sum()
            new_percent = round(total_new * 100 / total_return, 1)

            total_qc = df_temp['YTD Quality Checked'].sum()
            qc_percent = round(total_qc * 100 / total_return, 1)

            total_refurb = df_temp['YTD Refurbished'].sum()
            refurb_percent = round(total_refurb * 100 / total_return, 1)

            total_open_box = df_temp['YTD Open Box'].sum()
            open_box_percent = round(total_open_box * 100 / total_return, 1)

            total_damage = df_temp['YTD Broken'].sum()
            damage_percent = round(total_damage * 100 / total_return, 1)

            total_missing = total_return - (total_new + total_qc + total_refurb + total_open_box + total_damage)
            missing_percent = round(total_missing * 100 / total_return, 1)

        df1 = pd.DataFrame({'ITEMS': ['Return', 'New', 'QC', 'Refurbish', 'Open Box', 'Damage', 'Missing'],
                            'QTY': [total_return, total_new, total_qc, total_refurb, total_open_box, total_damage, total_missing],
                            '%': [return_percent, new_percent, qc_percent, refurb_percent, open_box_percent, damage_percent, missing_percent]

                            })

        # st.write(df1)
        df1 = df1.replace('None', 0).fillna(0)

        fig = go.Figure(data=[go.Table(
            columnwidth=[13, 8, 8],

            header=dict(values=list(df1.columns),
                        fill_color=[color_hex(135), color_hex(140), color_hex(56)],  # header_color,
                        font=dict(family="Arial", size=14, color='white'),
                        line_color='white',
                        height=28,
                        align=['left', 'center']),

            cells=dict(
                values=[df1['ITEMS'], df1['QTY'], df1['%']],
                font=dict(family="Arial", size=14, color='black'),
                height=28,
                fill_color=[color_hex(17), color_hex(102), color_hex(185)],
                line_color='white',
                align=['left', 'center']))
                ])

        # add outer boarder around the table
        fig.add_shape(
            type="rect",
            xref="paper", yref="paper",
            x0=0, y0=0, x1=1, y1=1,  # full canvas
            line=dict(color=color_hex(32), width=3),
            layer="above"
        )

        fig.update_layout(height=224, margin=dict(l=0, r=0, b=0, t=0))

        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:-5px"> {txt_list[i]} </p>', unsafe_allow_html=True)

        mygrid[row][col].plotly_chart(fig, use_container_width=True)

        col = col + 1

        if col == 4:
            col = 0
            row = row + 1
    return
