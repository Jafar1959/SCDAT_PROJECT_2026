import streamlit as st
import pandas as pd
from pathlib import Path, PureWindowsPath    # for Window & Mac OS path-slash '\' or '/'
import os
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode, GridUpdateMode    #, DataReturnMode
import plotly.graph_objects as go
import calendar

import scdat_data_26 as data
import scdat_utils_26 as utils


def check_flagship_models (datafile_location, year, df, m):
    # values = data.yearly_sales_df(datafile_location, year)
    df1, *_ = data.yearly_sales_df(datafile_location, year)

    # st.write(df1)
    # st.stop()

    df1 = (
        # df1.sort_values("REVENUE", ascending=False, ignore_index=True)
        df1.sort_values("TOTAL", ascending=False, ignore_index=True)
        .set_axis(range(1, len(df1) + 1))
    )

    df_50 = df1[0:50].copy()
    df_100 = df1[50:100].copy()
    df_200 = df1[100:200].copy()

    for i in range (0, len(df)):
        sku = df.iloc[i][0]

        df3 = df_50[df_50['SKU'] == sku]
        df4 = df_100[df_100['SKU'] == sku]
        df5 = df_200[df_200['SKU'] == sku]

        if len(df3) > 0:
            df.loc[i, m] = round(df.iloc[i][m]*1.15, 0)     # increase Qty 15% for 1 - 50

        elif len(df4) > 0:
            df.loc[i, m] = round(df.iloc[i][m]*1.1, 0)      # increase Qty 10% for 51 - 100

        elif len(df5) > 0:
            df.loc[i, m] = round(df.iloc[i][m] * 1.0, 0)    # no increase 101 - 150

        else:
            df.loc[i, m] = round(df.iloc[i][m] * 0.9, 0)    # reduce Qty by 10% for 151 - rest

    return df


def loading_plan(forecast, total, m1_loading, m2_loading, m3_loading, m4_loading, m5_loading, m6_loading,
                 stock_level_month, month_factor):

    # LOADING QTY CALCULATIONS
    loading = 0

    # for 2nd month
    if month_factor == 2:

        carryover_m2 = max(total - forecast, 0)

        carryover_m3 = max(carryover_m2 + m1_loading - forecast, 0)

        loading = int(stock_level_month * forecast - carryover_m3)

        # control very high loading qty
        if loading > 2 * forecast:
            loading = int(loading * 0.7)

    # for 3rd month
    elif month_factor == 3:

        # carryover_m2 = total - forecast
        # if carryover_m2 < 0:
        #     carryover_m2 = 0

        carryover_m2 = max(total - forecast, 0)

        # carryover_m3 = carryover_m2 + m1_loading - forecast
        # if carryover_m3 < 0:
        #     carryover_m3 = 0

        carryover_m3 = max(carryover_m2 + m1_loading - forecast, 0)


        # carryover_m4 = carryover_m3 + m2_loading - forecast
        # if carryover_m4 < 0:
        #     carryover_m4 = 0

        carryover_m4 = max(carryover_m3 + m2_loading - forecast, 0)

        loading = int(stock_level_month * forecast - carryover_m4)

    # for 4th month
    elif month_factor == 4:

        # carryover_m2 = total - forecast
        # if carryover_m2 < 0:
        #     carryover_m2 = 0

        carryover_m2 = max(total - forecast, 0)

        # carryover_m3 = carryover_m2 + m1_loading - forecast
        # if carryover_m3 < 0:
        #     carryover_m3 = 0

        carryover_m3 = max(carryover_m2 + m1_loading - forecast, 0)

        # carryover_m4 = carryover_m3 + m2_loading - forecast
        # if carryover_m4 < 0:
        #     carryover_m4 = 0

        carryover_m4 = max(carryover_m3 + m2_loading - forecast,0)

        # carryover_m5 = carryover_m4 + m3_loading - forecast
        # if carryover_m5 < 0:
        #     carryover_m5 = 0

        carryover_m5 = max(carryover_m4 + m3_loading - forecast, 0)


        loading = int(stock_level_month * forecast - carryover_m5)

    # for 5th month
    elif month_factor == 5:

        carryover_m2 = total - forecast
        if carryover_m2 < 0:
            carryover_m2 = 0

        carryover_m3 = carryover_m2 + m1_loading - forecast
        if carryover_m3 < 0:
            carryover_m3 = 0

        carryover_m4 = carryover_m3 + m2_loading - forecast
        if carryover_m4 < 0:
            carryover_m4 = 0

        carryover_m5 = carryover_m4 + m3_loading - forecast
        if carryover_m5 < 0:
            carryover_m5 = 0

        carryover_m6 = carryover_m5 + m4_loading - forecast
        if carryover_m6 < 0:
            carryover_m6 = 0

        loading = int(stock_level_month * forecast - carryover_m6)


    # for 6th month
    elif month_factor == 6:

        carryover_m2 = total - forecast
        if carryover_m2 < 0:
            carryover_m2 = 0

        carryover_m3 = carryover_m2 + m1_loading - forecast
        if carryover_m3 < 0:
            carryover_m3 = 0

        carryover_m4 = carryover_m3 + m2_loading - forecast
        if carryover_m4 < 0:
            carryover_m4 = 0

        carryover_m5 = carryover_m4 + m3_loading - forecast
        if carryover_m5 < 0:
            carryover_m5 = 0

        carryover_m6 = carryover_m5 + m4_loading - forecast
        if carryover_m6 < 0:
            carryover_m6 = 0

        carryover_m7 = carryover_m6 + m5_loading - forecast
        if carryover_m7 < 0:
            carryover_m7 = 0

        loading = int(stock_level_month * forecast - carryover_m7)


    # for 7th month
    elif month_factor == 7:

        carryover_m2 = total - forecast
        if carryover_m2 < 0:
            carryover_m2 = 0

        carryover_m3 = carryover_m2 + m1_loading - forecast
        if carryover_m3 < 0:
            carryover_m3 = 0

        carryover_m4 = carryover_m3 + m2_loading - forecast
        if carryover_m4 < 0:
            carryover_m4 = 0

        carryover_m5 = carryover_m4 + m3_loading - forecast
        if carryover_m5 < 0:
            carryover_m5 = 0

        carryover_m6 = carryover_m5 + m4_loading - forecast
        if carryover_m6 < 0:
            carryover_m6 = 0

        carryover_m7 = carryover_m6 + m5_loading - forecast
        if carryover_m7 < 0:
            carryover_m7 = 0

        carryover_m8 = carryover_m7 + m6_loading - forecast
        if carryover_m8 < 0:
            carryover_m8 = 0

        loading = int(stock_level_month * forecast - carryover_m8)

    if loading < 2:
        loading = 0

    # if loading !=0 and loading < min_loading:
    #     loading = min_loading

    # min_loading_factor = min_loading * 0.4  # 40% of min loading
    #
    # if loading > 0:
    #     if loading <= min_loading_factor:
    #         loading = 0
    #     elif min_loading_factor < loading < min_loading:
    #         loading = min_loading

    return loading


def row_color(gb):
    gb.configure_grid_options(
        getRowStyle=JsCode("""
                function(params) {
                    if (params.node.rowIndex % 2 === 0) {
                        return {
                            'backgroundColor': '#FFFFFF'
                        };
                    } else {
                        return {
                            'backgroundColor': '#E8E8E8'
                        };
                    }
                }
                 """)
    )
    return gb


def column_header_color(df, gb):
    # define columns header class ___________________________
    gb.configure_column(df.columns[0], headerClass="sku-header")
    gb.configure_column(df.columns[1], headerClass="all-header")
    gb.configure_column(df.columns[2], headerClass="all-header")
    gb.configure_column(df.columns[3], headerClass="all-header")
    gb.configure_column(df.columns[4], headerClass="all-header")
    gb.configure_column(df.columns[5], headerClass="month-stock")
    gb.configure_column("PRIORITY", headerClass="priority-header")

    gb.configure_column(df.columns[7], headerClass="current-month")
    gb.configure_column(df.columns[8], headerClass="all-header")
    gb.configure_column(df.columns[9], headerClass="all-header")
    gb.configure_column(df.columns[10], headerClass="all-header")
    gb.configure_column(df.columns[11], headerClass="all-header")
    gb.configure_column(df.columns[12], headerClass="all-header")
    gb.configure_column(df.columns[13], headerClass="all-header")

    # set AgGrid header font & background colors_____________
    custom_css = {
        ".sku-header": {
            "background-color": "#B2DFEE",
            "color": "black"
        },

        ".all-header": {
            "background-color": "#CFCFCF",
            "color": "black"
        },

        ".priority-header": {
            "background-color": "#FFB6C1",
            "color": "black"
        },
        ".current-month": {
            "background-color": "#8FBC8F",
            "color": "black"
        },
        ".month-stock": {
            "background-color": "#FFDEAD",
            "color": "black"
        },
    }

    grid_options = gb.build()

    return grid_options, custom_css


def priority_style():
    # set color based on the value in the PRIORITY column
    return JsCode("""
    function(params) {
        const colors = {
            LOW: '#008B00',
            MEDIUM: '#EEAD0E',
            HIGH: '#FF0000'
        };

        return { 
            color: colors[params.data.PRIORITY] || '#000000',
            fontWeight: 'bold',
            textAlign: 'center',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
            };
    }
    
    """)


def priority_style_sku():
    # set color based on the value in the PRIORITY column
    return JsCode("""
    function(params) {
        const colors = {
            LOW: '#008B00',
            MEDIUM: '#EEAD0E',
            HIGH: '#FF0000'
        };

        return { 
            color: colors[params.data.PRIORITY] || '#000000',
            fontWeight: 'bold',
            textAlign: 'left',
            display: 'flex',
            justifyContent: 'left',
            alignItems: 'left'
            };
    }

    """)


def sub_header_table(df):
    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[70] + [70] * (len(df.columns) - 1),
                header=dict(
                    values=[f"<b>{c}</b>" for c in df.columns],
                    fill_color="#5F9EA0",
                    font=dict(color="white", size=14),
                    align=["left"] + ["center"] * (len(df.columns) - 1),
                    line_color="black",
                    height=20
                ),
                cells=dict(
                    values=[df[c] for c in df.columns],
                    fill_color="#F0FFFF",
                    font=dict(color="black", size=14),
                    align=["left"] + ["center"] * (len(df.columns) - 1),
                    line_color="black",
                    height=25
                ),
            )
        ]
    )


    fig.update_layout(height=len(df)*25+40, margin=dict(l=0, r=0, t=0, b=0))

    return fig


def summary_sub_header(df):
    # create summary file for sub-header table ________________________________________
    cols = df.columns
    df_rva = df[df['SKU'].str.startswith('RVA', na=False)]  # accessories
    df_rvf = df[df['SKU'].str.startswith('RVF', na=False)]  # faucets
    df_rvf_parts = df[df['SKU'].str.startswith('RVP', na=False)]  # faucets
    df_tub = df[df['SKU'].str.startswith('RVB6', na=False)]  # bathtubs

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP', 'RVF', 'RVB6')  # accessories, boxes, dummy faucets, faucet parts, faucet, tub
    df_sink = utils.exclude_sku_prefixes(df, prefixes)

    all_txt = ['Accessories', 'Sink', 'Faucet', 'Faucet Parts', 'Bathtub']
    all_data = [df_rva, df_sink, df_rvf, df_rvf_parts, df_tub]

    # define lists ___________
    items = []
    count = []
    col1 = []
    col2 = []
    col3 = []
    col4 = []
    # col5 = [] # MONTH
    # col6 = [] # PRIORITY
    col7 = []
    col8 = []
    col9 = []
    col10 = []
    col11 = []
    col12 = []
    col13 = []

    for i in range(0, 5):
        # get appropriate text and datafile ___________
        txt = all_txt[i]
        data1 = all_data[i]

        # calculate column totals ______________________
        total_sku = int(data1['SKU'].count())
        total_col1 = int(data1[cols[1]].sum())
        total_col2 = int(data1[cols[2]].sum())
        total_col3 = int(data1[cols[3]].sum())
        total_col4 = int(data1[cols[4]].sum())
        # total_col5 = int(data1[cols[5]].sum())
        # total_col6 = int(data1[cols[6]].sum())
        total_col7 = int(data1[cols[7]].sum())
        total_col8 = int(data1[cols[8]].sum())
        total_col9 = int(data1[cols[9]].sum())
        total_col10 = int(data1[cols[10]].sum())
        total_col11 = int(data1[cols[11]].sum())
        total_col12 = int(data1[cols[12]].sum())
        total_col13 = int(data1[cols[13]].sum())

        # append to list ____________________
        items.append(txt)
        count.append(total_sku)
        col1.append(total_col1)
        col2.append(total_col2)
        col3.append(total_col3)
        col4.append(total_col4)
        # col5.append(total_col5)
        # col6.append(total_col6)
        col7.append(total_col7)
        col8.append(total_col8)
        col9.append(total_col9)
        col10.append(total_col10)
        col11.append(total_col11)
        col12.append(total_col12)
        col13.append(total_col13)

    # create summary dataframe __________________
    df_sub = pd.DataFrame({
        'ITEMS': items,
        'COUNT': count,
        cols[1]: col1,
        cols[2]: col2,
        cols[3]: col3,
        cols[4]: col4,
        # cols[5]: col5,
        # cols[6]: col6,
        cols[7]: col7,
        cols[8]: col8,
        cols[9]: col9,
        cols[10]: col10,
        cols[11]: col11,
        cols[12]: col12,
        cols[13]: col13,

    })

    # filter and sort dataframe __________
    df_sub = (
        df_sub.loc[df_sub['COUNT'].ne(0)]
        .sort_values('ITEMS')
    )

    return df_sub


def display_loading_plan(datafile_location, forecast_month):
    forecast_year = forecast_month[7:12]

    path = datafile_location + 'Projection\\' + forecast_year + '\\' + forecast_month + '\\'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort()

    file = st.sidebar.selectbox("SELECT DATA SOURCE FILE", source_files)

    file_path = path + file

    # get forecast data __________________
    df_data = pd.read_excel(Path(PureWindowsPath(file_path)), sheet_name='Jafar_Data', header=1)

    # filter the line contain FORECAST=0 and TOTAL/Total/Sink Only
    df_data = df_data[
        (df_data['FORECAST'] != 0) &
        (~df_data['SKU'].isin(['TOTAL', 'Total', 'Sink Only']))
        ]


    cols = df_data.columns

    # get col SKU [0], Forecast [8] and Current month Loading Qty [9]
    df_data = df_data[['SKU', 'FORECAST', cols[9]]]

    # create existing inventory dataframe
    df_existing = (
        data.inventory_df(datafile_location)
        .rename(columns={'Existing Qty': 'EXISTING QTY'})
        [['SKU', 'EXISTING QTY']]
    )

    # merge dataframes with existing
    df = df_data.merge(df_existing, on=["SKU"], how='left')

    # create incoming dataframe
    df_incoming, *_ = data.container_df(datafile_location)

    df_incoming = (
        df_incoming[df_incoming['STATE'].ne('Received In Warehouse')]
        .groupby('SKU', as_index=False)['QTY']
        .sum()
        .rename(columns={'QTY': 'INCOMING QTY'})
    )

    df = df.merge(df_incoming, on=["SKU"], how='left')

    df = df.fillna(0)

    # calculate total
    df['TOTAL'] = df['EXISTING QTY'] + df['INCOMING QTY']
    df['MONTH'] = (df['TOTAL']/df['FORECAST']).round(2)

    # calculate priority ___________________________
    high_limit = 2.5
    low_limit = 4.0

    df['PRIORITY'] = np.select(
        [
            df['MONTH'].lt(high_limit),
            df['MONTH'].gt(low_limit)
        ],
        [
            'HIGH',
            'LOW'
        ],
        default='MEDIUM'
    )

    # re-arrange columns _______________
    df = df[['SKU', 'FORECAST', 'EXISTING QTY', 'INCOMING QTY', 'TOTAL', 'MONTH', 'PRIORITY', cols[9]]]

    # st.write(df.columns)

    # create 7-months list starting from month name in col[9] ________________________
    start_month = str(cols[9])
    months_all = list(calendar.month_name)[1:]
    start = months_all.index(start_month.title())

    months = [
        months_all[(start + i) % 12]
        for i in range(7)
    ]

    # st.write(months)

    # get buffer-stock level value
    stock_level_month = st.sidebar.number_input("BUFFER STOCK LEVEL",
                                                min_value=1.0,
                                                max_value=None,
                                                value=2.5,
                                                step=0.01
                                          )

    # select flagship year _______________
    current_year = datetime.today().year
    years = [str(current_year - i) for i in range(2)]
    year = st.sidebar.selectbox("FLAGSHIP YEAR", years)

    # calculate loading qty for 2nd month ______________________________
    df[months[1].upper()] = df.apply(
        lambda x: loading_plan(x.iloc[1],
                               x.iloc[4],
                               x.iloc[7],
                               0, 0, 0, 0, 0,
                               stock_level_month,
                               2),
        axis=1)

    # 1. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, int(year), df, months[1].upper())

    # calculate loading qty for 3rd month ______________________________
    df[months[2].upper()] = df.apply(
        lambda x: loading_plan(x.iloc[1],
                               x.iloc[4],
                               x.iloc[7],
                               x.iloc[8],
                               0, 0, 0, 0,
                               stock_level_month,
                               3),

        axis=1)

    # 2. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, int(year), df, months[2].upper())

    # calculate loading qty for 3rd month ______________________________
    df[months[3].upper()] = df.apply(
        lambda x: loading_plan(x.iloc[1],
                               x.iloc[4],
                               x.iloc[7],
                               x.iloc[8],
                               x.iloc[9],
                               0, 0, 0,
                               stock_level_month,
                               4),
        axis=1)

    # 3. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, int(year), df, months[3].upper())

    # calculate loading qty for 4th month ______________________________
    df[months[4].upper()] = df.apply(
        lambda x: loading_plan(x.iloc[1],
                               x.iloc[4],
                               x.iloc[7],
                               x.iloc[8],
                               x.iloc[9],
                               x.iloc[10],
                               0, 0,
                               stock_level_month,
                               5),
        axis=1)

    # 4. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, int(year), df, months[4].upper())

    # calculate loading qty for 5th month______________________________
    df[months[5].upper()] = df.apply(
        lambda x: loading_plan(x.iloc[1],
                               x.iloc[4],
                               x.iloc[7],
                               x.iloc[8],
                               x.iloc[9],
                               x.iloc[10],
                               x.iloc[11],
                               0,
                               stock_level_month,
                               6),
        axis=1)

    # calculate loading qty for 5th month______________________________
    df[months[6].upper()] = df.apply(
        lambda x: loading_plan(x.iloc[1],
                               x.iloc[4],
                               x.iloc[7],
                               x.iloc[8],
                               x.iloc[9],
                               x.iloc[10],
                               x.iloc[11],
                               x.iloc[12],
                               stock_level_month,
                               7),
        axis=1)

    # remove 0 or blank from SKU
    df = df[
        df['SKU'].notna() &
        df['SKU'].astype(str).str.strip().ne('') &
        df['SKU'].astype(str).str.strip().ne('0')
        ]

    # sort on SKU
    df = (
        df.sort_values('SKU')
        .reset_index(drop=True)
        .set_axis(range(1, len(df) + 1))
    )

    supplier_name = file.split('_')
    txt = 'Loading Plan | ' + supplier_name[1] + ' | ' + 'Buffer Stock ' + str(
        round(stock_level_month, 2)) + ' months'

    utils.show_header(txt)

    # create summary table for sub-header____________
    df_sub = summary_sub_header(df)

    # create plotly fig from summary dataframe _____________
    fig = sub_header_table(df_sub)

    st.plotly_chart(fig, width='stretch')

    # _________________ Set Color Style based of STATUS values _____________________
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column("SKU", cellStyle=priority_style_sku())
    gb.configure_column("MONTH", cellStyle=priority_style())
    gb.configure_column("PRIORITY", cellStyle=priority_style())
    gb.configure_grid_options = row_color(gb)

    # set column header color __________
    grid_options, custom_css = column_header_color(df, gb)

    height = len(df) * 35
    if height > 620:
        height = 620

    #AgGrid(df, gridOptions=gb.build(), custom_css=custom_css, height=height, allow_unsafe_jscode=True)
    AgGrid(df, gridOptions=grid_options, custom_css=custom_css, height=height, allow_unsafe_jscode=True)
    utils.download_csv(df, 'Download Loading Plan')
    return


