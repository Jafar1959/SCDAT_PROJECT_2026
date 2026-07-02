import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
# from datetime import date, timedelta
import plotly.graph_objects as go
import calendar
from pathlib import Path, PureWindowsPath    # << for Window & Mac OS path-slash '\' or '/'
import numpy as np
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode

# from scdat_colors_26 import color_hex
import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex



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

def ytd_sales_summary(df, current_year, previous_year, month_elapsed, supplier):

    # ===================== Preprocessing =====================
    # Create monthly sales column (vectorized)
    df['MONTHLY'] = (df[str(current_year)] / month_elapsed).round(0)

    # Split dataset into categories using vectorized string filters
    df_sink = df[~df['SKU'].str.startswith(('RVB6', 'RVF', 'RDM'))]

    # st.write(df_sink)
    # st.stop()

    df_tub = df[df['SKU'].str.startswith('RVB6')]
    df_faucet = df[df['SKU'].str.startswith('RVF')]

    # ===================== Chunk Summary (Sink) =====================
    chunk_size = st.sidebar.number_input(
        'CHUNK SIZE', min_value=10, max_value=50, step=5, value=50
    )

    total_rows = min(len(df_sink), 500) # 450

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
    utils.download_csv(df_sink, 'Download Data File Sink')
    utils.download_csv(df, 'Download Data File ALL')

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
                height=26.5,
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

        fig.update_layout(height=len(df) * 26 + 46, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, width='stretch')

    return


