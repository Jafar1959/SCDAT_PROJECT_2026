# ======================== LIBRARY IMPORTS =======================
import streamlit as st
import pandas as pd
import base64
from statistics import mean

import datetime
from datetime import date, timedelta
from time import strftime
import numpy as np
# from time import sleep

import openpyxl
# from openpyxl.styles import Font
# from openpyxl.styles import Alignment

import os
import plotly.graph_objects as go
import plotly.express as px

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode    #, DataReturnMode

from screeninfo import get_monitors

from pathlib import Path, PureWindowsPath    # for Window & Mac OS path-slash '\' or '/'

import calendar
# from calendar import monthrange

import math

# import tensorflow as tf
# ============== my modules ============================
from scdat_colors_26 import color_hex
import scdat_utils_26 as utils
import scdat_data_26 as data


def sales_forecast(m1, m2, m3, m4, m5, m6, average):
    sales_arr = [m1, m2, m3, m4, m5, m6]

    forecast_arr = sales_arr.copy()
    forecast_arr.sort(reverse=True)

    # average of top 3-month sales
    avg_of_top3_sales = mean([forecast_arr.pop(0), forecast_arr.pop(0), forecast_arr.pop(0)])

    # average of last 3-month sales
    avg_of_last_3month_sales = mean([m4, m5, m6])

    # forecast calculation
    delta = (avg_of_top3_sales - avg_of_last_3month_sales) / 2  # delta is 50% of difference (w.e.f. 1-Feb-2023)

    forecast = avg_of_top3_sales * 1.0 - delta  # 0% increment considered then deduct delta


    if forecast < average:
        # forecast = round(average * 1.05, 0)   # Stopped from 11-Jan-2023
        forecast = average

    forecast = round(forecast, 0)
    return forecast


def sales_forecast_NEW(df):

    df1 = df.drop('SKU', axis=1)    # remove SKU column
    df['top3_avg'] = df1.apply(lambda row: row.nlargest(3).mean(), axis=1)  # get average of top 3 values

    cols_last_3month = df.iloc[:, 4:7].astype(int)      # get last 3 months columns

    df['last3_avg'] = cols_last_3month.mean(axis=1)
    df['FORECAST'] = df['top3_avg'] * 0.80 + df['last3_avg'] * 0.20     # weighted average

    df['FORECAST'] = round(df['FORECAST'], 0)

    df['FORECAST'] = df['FORECAST'].replace(0, 1)       # set 0 value to 1

    return df





def check_flagship_models (datafile_location, year, df, m):
    values = data.yearly_sales_df(datafile_location, year)
    df1 = values[0]
    df1 = df1.sort_values('REVENUE', ascending=False)
    df1.reset_index(drop=True, inplace=True)
    df1.index = range(1, df1.shape[0] + 1)

    df_50 = df1[0:50].copy()
    df_100 = df1[50:100].copy()
    df_200 = df1[100:200].copy()

    for i in range (0, len(df)):
        sku = df.iloc[i][0]

        df3 = df_50[df_50['SKU'] == sku]
        df4 = df_100[df_100['SKU'] == sku]
        df5 = df_200[df_200['SKU'] == sku]

        if len(df3) > 0:
            df.loc[i, m] = round(df.iloc[i][m]*1.15, 0)

        elif len(df4) > 0:
            df.loc[i, m] = round(df.iloc[i][m]*1.1, 0)

        elif len(df5) > 0:
            df.loc[i, m] = round(df.iloc[i][m] * 1.0, 0)

        else:
            df.loc[i, m] = round(df.iloc[i][m] * 0.9, 0)

    return df


def loading_plan(forecast, total, m1_loading, m2_loading, m3_loading, m4_loading, m5_loading, m6_loading,
                 stock_level_month, month_factor, min_loading):

    # LOADING QTY CALCULATIONS
    loading = 0

    # for 2nd month
    if month_factor == 2:

        carryover_m2 = total - forecast
        if carryover_m2 < 0:
            carryover_m2 = 0

        carryover_m3 = carryover_m2 + m1_loading - forecast
        if carryover_m3 < 0:
            carryover_m3 = 0

        loading = int(stock_level_month * forecast - carryover_m3)

        # control very high loading qty
        #if loading > 2.20 * forecast:
        #    loading = int(0.8 * loading)

        if loading > 2.0 * forecast:
            loading = int(0.7 * loading)

    # for 3rd month
    elif month_factor == 3:

        carryover_m2 = total - forecast
        if carryover_m2 < 0:
            carryover_m2 = 0

        carryover_m3 = carryover_m2 + m1_loading - forecast
        if carryover_m3 < 0:
            carryover_m3 = 0

        carryover_m4 = carryover_m3 + m2_loading - forecast
        if carryover_m4 < 0:
            carryover_m4 = 0

        loading = int(stock_level_month * forecast - carryover_m4)

    # for 4th month
    elif month_factor == 4:

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

    min_loading_factor = min_loading * 0.4  # 40% of min loading

    if loading > 0:
        if loading <= min_loading_factor:
            loading = 0
        elif min_loading_factor < loading < min_loading:
            loading = min_loading

    return loading * 1.0


def display_sales_forecast(datafile_location):
    # create header line
    st.markdown("""
                <div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-30px;">
                    Sales Forecasting
                </div>
                <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
                """, unsafe_allow_html=True)

    # get forecast input file list
    path = datafile_location + 'Projection\\Input_files\\'
    source_file = os.listdir(Path(PureWindowsPath(path)))
    source_file.sort()

    # source_file.remove('.DS_Store')   # Don't delete. Required when use Mac <<<<<<<<<<<<<<<<<<<<<

    file = st.sidebar.selectbox("SELECT DATA SOURCE FILE", source_file)
    file_path = path + file

    # get supplier name from source file
    p1 = file.find('_')
    supplier_name = file[3:p1]

    df_data = pd.read_excel(Path(PureWindowsPath(file_path)), sheet_name='Sheet1', header=1)

    # select first 7 columns only
    df_data = df_data.iloc[:, :7]

    # remove TOTAL/Total row if any
    df_data = df_data[~ df_data.apply(lambda row: row.astype(str).str.upper().eq('TOTAL').any(), axis=1)]

    df_data = df_data.fillna(0)

    six_months = df_data.iloc[:, 1:7]   # create list of columns for 6-months only

    df_data = sales_forecast_NEW(df_data) # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # df_data['AVERAGE'] = round(six_months.mean(axis=1), 0)  # calculate average of 6-months

    # st.write(df_data)

    # get forecast value from def sales_forecast
    # 1 = month1, 2 = month2, 3 = month3, 4 = month4, 5 = month5, 6 = month6, 7 = average
    df_data['FORECAST_2'] = df_data.apply(
        lambda x: sales_forecast(x.iloc[1], x.iloc[2], x.iloc[3], x.iloc[4], x.iloc[5], x.iloc[6], x.iloc[7]), axis=1)


    st.write(df_data)
    utils.download_csv(df_data, 'Download')
    st.stop()

    df = df_data.sort_values('SKU', ascending=True)
    df.reset_index(drop=True, inplace=True)
    df.index = range(1, df.shape[0] + 1)

    forecast_month = utils.get_month_no(cols[6])
    forecast_month = forecast_month + 1
    if forecast_month > 12:
        forecast_month = 1

    forecast_month = utils.get_long_month_name(forecast_month)

    df_inventory = data.inventory_df(datafile_location)
    df_inventory = df_inventory[['SKU', 'STATUS']]
    df = pd.merge(df, df_inventory, on=["SKU"], how='left')
    df['STATUS'] = df['STATUS'].fillna('')
    df = df.rename(columns={'STATUS': 'LAUNCH DATE'})
    #st.write(df)

    text1 = 'Sales Forecast | ' + supplier_name + ' | ' + forecast_month
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(300)}; text-align:left; font-size: 20px ;border-radius:1%;'
        f' line-height:0em; margin-top:5px"> {text1} </p>', unsafe_allow_html=True)

    # build AgGrid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(rowHeight=25)
    gb.configure_grid_options(headerHeight=25)
    gb.configure_grid_options(enableCellTextSelection=True)
    gb.configure_column('SKU', wrapText=False, width=250)
    gb.configure_column('LAUNCH DATE', wrapText=False, width=350)
    #gb.configure_column('FORECAST', wrapText=False, width=150)
    #gb.configure_column('MONTH', wrapText=False, width=150)  # , type=[00.00], precision=5)
    grid_options = gb.build()

    height = len(df) * 25 + 28
    if height > 650:
        height = 650

    col1, col2 = st.columns([3.5, 1])

    with col1:
        AgGrid(df, grid_options, height=height, fit_columns_on_grid_load=True)  #, theme='fresh')  # theme='blue', 'fresh', 'light'
        ut.download_csv(df, 'Download Forecast')
        cols = df.columns

        df_sink = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]

        sku_sink = df_sink['SKU'].count()
        m1_sink = df_sink[cols[1]].sum()
        m2_sink = df_sink[cols[2]].sum()
        m3_sink = df_sink[cols[3]].sum()
        m4_sink = df_sink[cols[4]].sum()
        m5_sink = df_sink[cols[5]].sum()
        m6_sink = df_sink[cols[6]].sum()
        average_sink = df_sink[cols[7]].sum()
        forecast_sink = df_sink[cols[8]].sum()

        df_acc = df.loc[lambda row: row['SKU'].str.startswith('RVA')]

        sku_acc = df_acc['SKU'].count()
        m1_acc = df_acc[cols[1]].sum()
        m2_acc = df_acc[cols[2]].sum()
        m3_acc = df_acc[cols[3]].sum()
        m4_acc = df_acc[cols[4]].sum()
        m5_acc = df_acc[cols[5]].sum()
        m6_acc = df_acc[cols[6]].sum()
        average_acc = df_acc[cols[7]].sum()
        forecast_acc = df_acc[cols[8]].sum()


        df_summary = pd.DataFrame({'PRODUCT': ['SINK', 'ACCESSORIES'],
                                   'SKU': [sku_sink, sku_acc],
                                    cols[1]: [m1_sink, m1_acc],
                                    cols[2]: [m2_sink, m2_acc],
                                    cols[3]: [m3_sink, m3_acc],
                                    cols[4]: [m4_sink, m4_acc],
                                    cols[5]: [m5_sink, m5_acc],
                                    cols[6]: [m6_sink, m6_acc],
                                    'AVERAGE': [average_sink, average_acc],
                                    'FORECAST': [forecast_sink, forecast_acc],

                                   })

        fig = go.Figure(data=[go.Table(
            columnwidth=[18],

            header=dict(values=list(df_summary.columns),
                        fill_color=color_hex(118),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=28,
                        align=['left', 'center']),
            cells=dict(
                values=[df_summary.PRODUCT, df_summary['SKU'], df_summary[cols[1]], df_summary[cols[2]], df_summary[cols[3]],
                        df_summary[cols[4]], df_summary[cols[5]], df_summary[cols[6]], df_summary.AVERAGE, df_summary.FORECAST],
                font_size=14,
                height=28,
                fill_color=color_hex(17),
                line_color='white',
                align=['left', 'center']))
        ])

        fig.update_layout(height=90, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)

    return


def display_loading_plan(datafile_location, forecast_month):
    forecast_year = forecast_month[7:12]
    # st.write(forecast_year)
    # st.stop()
    path = datafile_location + 'Projection\\' + forecast_year + '\\' + forecast_month + '\\'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort()

    file = st.sidebar.selectbox("SELECT DATA SOURCE FILE", source_files)

    file_path = path + file

    df_data = pd.read_excel(Path(PureWindowsPath(file_path)), sheet_name='Jafar_Data', header=1)

    df_data = df_data[df_data['FORECAST'] != 0]

    # filter the line contain TOTAL/Total/Sink Only
    df_data = df_data[df_data['SKU'] != 'TOTAL']
    df_data = df_data[df_data['SKU'] != 'Total']
    df_data = df_data[df_data['SKU'] != 'Sink Only']

    cols = df_data.columns

    # get col SKU [0], Forecast [8] and Current month Loading Qty [9]
    df_data = df_data[[cols[0], cols[8], cols[9]]]

    # convert forecast to int type
    df_data['FORECAST'] = df_data['FORECAST'].astype(int) * 1.00

    df_data[cols[9]] = df_data[cols[9]].astype(int) * 1.00

    # create existing inventory dataframe
    df_existing = data.inventory_df(datafile_location)
    df_existing = df_existing.rename(columns={'Existing Qty': 'EXISTING QTY'})
    df_existing = df_existing[['SKU', 'EXISTING QTY']]

    # merge dataframes with existing
    df = pd.merge(df_data, df_existing, on=["SKU"], how='left')

    # create incoming dataframe
    df_incoming = data.container_df(datafile_location)

    # removed received containers
    df_incoming = df_incoming[df_incoming['STATE'] != 'Received In Warehouse']

    df_incoming = df_incoming.groupby(['SKU'])['QTY'].sum().to_frame().reset_index()
    df_incoming.columns = (['SKU', 'INCOMING QTY'])

    # merge dataframe with incoming
    df = pd.merge(df, df_incoming, on=["SKU"], how='left')

    df = df.fillna(0)

    # convert col value to int
    df['EXISTING QTY'] = df['EXISTING QTY'].astype(int) * 1.00
    df['INCOMING QTY'] = df['INCOMING QTY'].astype(int) * 1.00

    # calculate total
    df['TOTAL'] = df['EXISTING QTY'] + df['INCOMING QTY']

    # calculate month of stock  and round up to two digit (TOTAL/FORECAST)
    df['MONTH'] = df.apply(lambda x: round(x.iloc[5] / x.iloc[1], 2), axis=1)

    # calculate priority
    c1 = df['MONTH'] < 2.5   # HIGH
    c2 = df['MONTH'] > 4.0   # Low = HIGH + 1.5 month

    condition1 = [c1, c2]
    choice1 = ['HIGH', 'Low']
    df['PRIORITY'] = np.select(condition1, choice1, default='Medium')  # , default='Tie' )

    df = df[['SKU', 'FORECAST', 'EXISTING QTY', 'INCOMING QTY', 'TOTAL', 'MONTH', 'PRIORITY', cols[9]]]

    cols = df.columns

    # months = month_circular_array(get_month_no(cols[7]), 5)
    months = ut.month_circular_array(ut.get_month_no(cols[7]), 7)

    m1 = cols[7]
    m2 = ut.get_short_month_name(months[1]).upper()
    m3 = ut.get_short_month_name(months[2]).upper()
    m4 = ut.get_short_month_name(months[3]).upper()
    m5 = ut.get_short_month_name(months[4]).upper()
    m6 = ut.get_short_month_name(months[5]).upper()
    m7 = ut.get_short_month_name(months[6]).upper()

    supplier_name = file.split('_')

    stock_level_month = st.sidebar.number_input("BUFFER STOCK LEVEL", min_value=1.0, max_value=None, value=2.5,
                                                step=0.01)

    min_loading = st.sidebar.number_input("MINIMUM LOADING QTY", min_value=0, max_value=None, value=0, step=1)

    df[m2] = df.apply(
        lambda x: loading_plan(x.iloc[1], x.iloc[4], x.iloc[7], 0, 0, 0, 0, 0, stock_level_month, 2, min_loading),
        axis=1)

    today = datetime.date.today()
    year = st.sidebar.number_input("FLAGSHIP YEAR", min_value=2021, max_value=today.year, value=today.year)

    # 1. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, year, df, m2)
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    df[m3] = df.apply(
        lambda x: loading_plan(x.iloc[1], x.iloc[4], x.iloc[7], x.iloc[8], 0, 0, 0, 0, stock_level_month, 3,
                               min_loading), axis=1)

    # 2. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, year, df, m3)
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    df[m4] = df.apply(
        lambda x: loading_plan(x.iloc[1], x.iloc[4], x.iloc[7], x.iloc[8], x.iloc[9], 0, 0, 0, stock_level_month, 4,
                               min_loading), axis=1)


    # 3. ++++++++++ increase 15% for 1-50 and 10% for 51-100 flagship models +++++++++++++++++++++++++++++++++++++++++++++++
    df = check_flagship_models(datafile_location, year, df, m4)
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


    df[m5] = df.apply(lambda x: loading_plan(x.iloc[1], x.iloc[4], x.iloc[7], x.iloc[8], x.iloc[9], x.iloc[10], 0, 0,
                                             stock_level_month, 5, min_loading), axis=1)

    df[m6] = df.apply(
        lambda x: loading_plan(x.iloc[1], x.iloc[4], x.iloc[7], x.iloc[8], x.iloc[9], x.iloc[10], x.iloc[11], 0,
                               stock_level_month, 6, min_loading), axis=1)

    df[m7] = df.apply(
        lambda x: loading_plan(x.iloc[1], x.iloc[4], x.iloc[7], x.iloc[8], x.iloc[9], x.iloc[10], x.iloc[11],
                               x.iloc[12], stock_level_month, 7, min_loading), axis=1)

    # select required columns
    df = df[['SKU', 'FORECAST', 'EXISTING QTY', 'INCOMING QTY', 'TOTAL', 'MONTH', 'PRIORITY', m1, m2, m3, m4, m5, m6,
             m7]]  # , 'REMAINING ORDER QTY']]

    df = df.sort_values('SKU', ascending=True)
    df.reset_index(drop=True, inplace=True)
    df.index = range(1, df.shape[0] + 1)

    text = '4 - Months Loading Plan | ' + supplier_name[1] + ' | ' + 'Buffer Stock ' + str(
        round(stock_level_month, 2)) + ' months | Min. Loading ' + str(min_loading)
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
        f' line-height:0em; margin-top:5px"> {text}</p>',
        unsafe_allow_html=True)

    # # build AgGrid options
    # options = build_AgGrid_options(df, 30, 25)
    # gridOptions = options[0]
    # height = options[1]

    col1, col2 = st.columns([4.5, 1])

    with col1:
        cols = df.columns
        # build AgGrid options
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_grid_options(rowHeight=28)
        gb.configure_grid_options(headerHeight=25)
        gb.configure_grid_options(enableCellTextSelection=True)
        gb.configure_column('SKU', wrapText=False, width=130)
        gb.configure_column('FORECAST', wrapText=False, width=140)
        gb.configure_column('EXISTING QTY', wrapText=False, width=170)
        gb.configure_column('INCOMING QTY', wrapText=False, width=190)
        gb.configure_column('TOTAL', wrapText=False, width=130)
        gb.configure_column('MONTH', wrapText=False, width=150)
        gb.configure_column('PRIORITY', wrapText=False, width=150)
        gb.configure_column(cols[7], wrapText=False, width=100)
        gb.configure_column(cols[8], wrapText=False, width=100)
        gb.configure_column(cols[9], wrapText=False, width=100)
        gb.configure_column(cols[10], wrapText=False, width=100)
        gb.configure_column(cols[11], wrapText=False, width=100)
        gb.configure_column(cols[12], wrapText=False, width=100)
        gb.configure_column(cols[13], wrapText=False, width=100)
        grid_options = gb.build()

        height = len(df) * 28 + 30
        if height > 650:
            height = 650

        AgGrid(df, grid_options, height=height, fit_columns_on_grid_load=True)
        ut.download_csv(df, '4-Month Loading Plan')

        # calculate total on sink only
        df_sink = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
        total_sink_sku = df_sink['SKU'].count()
        total_sink_forecast = df_sink['FORECAST'].sum()
        total_sink_existing = df_sink['EXISTING QTY'].sum()
        total_sink_incoming = df_sink['INCOMING QTY'].sum()
        total_sink = df_sink['TOTAL'].sum()

        total_sink_m1 = df_sink[m1].sum()
        total_sink_m2 = df_sink[m2].sum()
        total_sink_m3 = df_sink[m3].sum()
        total_sink_m4 = df_sink[m4].sum()
        total_sink_m5 = df_sink[m5].sum()
        total_sink_m6 = df_sink[m6].sum()
        total_sink_m7 = df_sink[m7].sum()

        df_acc = df.loc[lambda row: row['SKU'].str.startswith('RVA')]
        total_acc_sku = df_acc['SKU'].count()
        total_acc_forecast = df_acc['FORECAST'].sum()
        total_acc_existing = df_acc['EXISTING QTY'].sum()
        total_acc_incoming = df_acc['INCOMING QTY'].sum()
        total_acc = df_acc['TOTAL'].sum()

        total_acc_m1 = df_acc[m1].sum()
        total_acc_m2 = df_acc[m2].sum()
        total_acc_m3 = df_acc[m3].sum()
        total_acc_m4 = df_acc[m4].sum()
        total_acc_m5 = df_acc[m5].sum()
        total_sink_m6 = df_sink[m6].sum()
        total_sink_m7 = df_sink[m7].sum()

        # loading plan summary <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        df_summary = pd.DataFrame({'PRODUCT': ['SINK', 'ACCESSORIES'],
                                   'SKU': [total_sink_sku, total_acc_sku],
                                   'FORECAST': [total_sink_forecast, total_acc_forecast],
                                   'EXISTING': [total_sink_existing, total_acc_existing],
                                   'INCOMING': [total_sink_incoming, total_acc_incoming],
                                   'TOTAL': [total_sink, total_acc],
                                    m1: [total_sink_m1, total_acc_m1],
                                    m2: [total_sink_m2, total_acc_m2],
                                    m3: [total_sink_m3, total_acc_m3],
                                    m4: [total_sink_m4, total_acc_m4],
                                    m5: [total_sink_m5, total_acc_m5],
                                   # m6: [total_sink_m6],
                                   # m7: [total_sink_m7],
                                   # 'LOADING': [total_sink_m1 + total_sink_m2 + total_sink_m3 + total_sink_m4 + total_sink_m5 + total_sink_m6 + total_sink_m7],
                                   # 'BALANCE': [remaining_order],
                                   # 'ORDER QTY': [total_order]
                               })

        fig = go.Figure(data=[go.Table(
            columnwidth=[18],

            header=dict(values=list(df_summary.columns),
                        fill_color=color_hex(118),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=28,
                        align=['left', 'center']),
            cells=dict(
                values=[df_summary.PRODUCT, df_summary.SKU, df_summary.FORECAST, df_summary.EXISTING, df_summary.INCOMING, df_summary.TOTAL,
                        df_summary[m1], df_summary[m2], df_summary[m3], df_summary[m4], df_summary[m5]],
                font_size=14,
                height=28,
                fill_color=color_hex(17),
                line_color='white',
                align=['left', 'center']))
        ])

        fig.update_layout(height=90, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)
    return

