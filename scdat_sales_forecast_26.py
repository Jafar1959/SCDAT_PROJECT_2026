# ======================== LIBRARY IMPORTS =======================
import streamlit as st
import pandas as pd
import base64
from statistics import mean
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import glob

import datetime
from datetime import datetime   #, timedelta
from time import strftime
import numpy as np
# from time import sleep

import openpyxl
# from openpyxl.styles import Font
# from openpyxl.styles import Alignment

import os
import plotly.graph_objects as go
import plotly.express as px

from st_aggrid import GridOptionsBuilder, AgGrid, JsCode, GridUpdateMode    #, DataReturnMode

from screeninfo import get_monitors

from pathlib import Path, PureWindowsPath    # for Window & Mac OS path-slash '\' or '/'

import calendar
# from calendar import monthrange

import math

# import tensorflow as tf
# ============== my modules ============================
# from scdat_colors_26 import color_hex
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex

import scdat_data_26 as data

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


def two_years_sales(datafile_location, suppliers):
    folder = datafile_location + "\Sales\Monthly_Sales\MONTHLY"

    # Read all CSV files matching your pattern
    files = glob.glob(folder + "\*_Sales_*.csv")
    files.sort()
    # files = files[-25:-1]   # get 24 months from previous month
    files = files[-25:]   # get 25 months including current month

    all_data = []

    # ______Get active product list ___________________________________________
    df_product = data.product_df(datafile_location)[['SKU','SUPPLIER']]

    # Remove Faucet Parts (RVP), Packing Box (RBX) and Display (RDM)
    prefixes = ('RBX', 'RDM')   # RVP
    df_product = utils.exclude_sku_prefixes(df_product, prefixes)

    suppliers.remove('ALL')
    supplier = st.sidebar.selectbox("SUPPLIER", suppliers)

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    df_product = utils.supplier_model_query(df_product, supplier, model)

    # _______ Read all sale files ___________________________________________
    for file in files:
        month_str = file.split("_Sales_")[1].replace(".csv", "")

        # Read the file
        df = pd.read_csv(file, encoding='latin1')[['SKU', 'TOTAL']]

        df = pd.merge(df_product, df, on=["SKU"], how='left')
        df = df.fillna(0)

        # Add Month column
        df["Month"] = month_str

        # Append to list
        all_data.append(df)

    # Combine all months
    final_df = pd.concat(all_data, ignore_index=True)

    # Convert Month to datetime (important for forecasting)
    final_df["Month"] = pd.to_datetime(final_df["Month"], format="%b-%y")

    # Sort
    final_df = final_df.sort_values(["SKU", "Month"])

    return final_df


def holtwinter_forecast(datafile_location, suppliers):

    df_2y = two_years_sales(datafile_location, suppliers)[['SKU', 'SUPPLIER', 'TOTAL', 'Month']]

    # _____________ Remove current month data ________________________
    current_month = pd.Timestamp.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    df = df_2y[df_2y["Month"] < current_month]


    # df["Month"] = pd.to_datetime(df["Month"])

    # Pivot table __ SKU vs MONTH ___
    df_out = (
        df.pivot_table(
            index="SKU",
            columns="Month",
            values="TOTAL",
            aggfunc="sum",
            fill_value=0
        )
        .reset_index()
    )

    df_out.columns = [
        col.strftime("%Y-%m") if isinstance(col, pd.Timestamp) else col
        for col in df_out.columns
    ]
    # st.write(df_out)
    
    # Remove the column name created by pivot
    df_out.columns.name = None


    df = df.sort_values(["SUPPLIER", "SKU", "Month"])

    # _____________ Remove all data of the current month ________________________
    # current_month = pd.Timestamp.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # df = df[df["Month"] < current_month]

    results = []
    alpha = 0.7  # High emphasis on recent data - alpha
    beta = 0.2  # weight to the newest trend - beta
    gamma = 0.2  # from the newest observation- gamma
    periods = 12    # None

    # st.write(df)
    # utils.download_csv(df, 'Download"')
    # st.stop()

    for sku, group in df.groupby("SKU"):
        supplier = group["SUPPLIER"].iloc[0]
        group = group.set_index("Month").asfreq("MS")
        # st.write(group)

        model = ExponentialSmoothing(
            group["TOTAL"],
            trend="add",
            seasonal="add",
            seasonal_periods=periods
        )   #.fit(

        model = model.fit(
            smoothing_level=alpha,
            smoothing_trend=beta,
            smoothing_seasonal=gamma,
            optimized=False         # False - It uses exactly the above values, True - alpha = 0.41, beta = 0.17, gamma = 0.28
        )

        # Single forecast value = next month
        forecast_value = model.forecast(1).iloc[0]

        results.append({"SKU": sku,
                        "SUPPLIER": supplier,
                        "Holt-Winter": forecast_value})


    single_forecast_df = pd.DataFrame(results)

    single_forecast_df["Holt-Winter"] = single_forecast_df["Holt-Winter"].clip(lower=1).round(0)

    df_hw = pd.merge(df_out, single_forecast_df, on=["SKU"], how='left')

    # move SUPPLIER column to 2nd position ____
    col_to_move = "SUPPLIER"

    cols = df_hw.columns.tolist()
    cols.remove(col_to_move)
    cols.insert(1, col_to_move)  # position 2 (index 1)

    df_hw = df_hw[cols]

    # _________ sidebar info ________________
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-16px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    txt1 = 'smoothing_level: '  + '\u03B1' + ' = ' + str(alpha)
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:left; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-12px"> {txt1} </p>',
        unsafe_allow_html=True)

    txt2 = 'smoothing_trend: '  + '\u03B2' + ' = ' + str(beta)
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:left; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-11px"> {txt2} </p>',
        unsafe_allow_html=True)

    txt3 = 'smoothing_seasonal: '  + '\u03B3' + ' = ' + str(gamma)
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:left; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-11px"> {txt3} </p>',
        unsafe_allow_html=True)

    txt4 = 'seasonal_periods = ' + str(periods)
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:left; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-11px"> {txt4} </p>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-18px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    # st.sidebar.write('smoothing_level: '  + '\u03B1' + ' = ' + str(alpha))
    # st.sidebar.write('smoothing_trend: '  + '\u03B2' + ' = ' + str(beta))
    # st.sidebar.write('smoothing_seasonal: '  + '\u03B3' + ' = ' + str(gamma))
    # st.sidebar.write('seasonal_periods = '  + str(periods))

    return df_2y, df_hw


def sales_forecast(datafile_location, suppliers):

    suppliers.extend(["Kangde Silicone", "LB Plast"])

    df_2y, df_hw = holtwinter_forecast(datafile_location, suppliers)

    # drop holt-winter column
    df_6m = df_hw.drop('Holt-Winter', axis=1)

    month_name = datetime.now().strftime("%B")

    st.markdown("""
    <style>
    /* Checkbox label */
    div[data-testid="stCheckbox"] label p {
        font-size: 13px;
        color: #FFFFFF;
        font-weight: normal;
    }
    </style>
    """, unsafe_allow_html=True)

    choice = st.sidebar.checkbox('Include ' +  month_name + ' Projected Sales')

    if choice:
        # _____________ Get current month projected sales data ________________________
        current_month = pd.Timestamp.today().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        df_current = df_2y[df_2y["Month"] == current_month]
        df_current['Month']= pd.to_datetime(df_current['Month']).dt.strftime("%Y-%m")

        df_1m = (
            df_current.pivot(index='SKU', columns='Month', values='TOTAL')
            .reset_index()
            .rename_axis(None, axis=1)
        )

        # Current date
        today = datetime.today()

        # Current day of the month
        current_day = today.day

        # Total days in the current month
        total_days = calendar.monthrange(today.year, today.month)[1]

        cols = df_1m.columns
        df_1m[cols[1]] = (df_1m[cols[1]] * total_days/(current_day-1)).round(0)

        df_1m = df_1m.rename(columns={cols[1]: str(cols[1]) + ' [Projected]' })

        df_6m = pd.merge(df_6m, df_1m, on=["SKU"], how='outer')


    # get 6-months sales only
    df_6m = pd.concat([df_6m.iloc[:, :2], df_6m.iloc[:, -6:]], axis=1)

    # calculate average
    cols = df_6m.columns[2:8]
    df_6m['AVERAGE'] = df_6m[cols].mean(axis=1).round(0)

    # calculate average of top-three months
    df_6m['TOP3_AVG'] = (
        df_6m.iloc[:, 2:8]
        .apply(lambda row: row.nlargest(3).mean(), axis=1)
    )

    # calculate average of last-three months
    df_6m['LAST3_AVG'] = df_6m.iloc[:, 5:8].mean(axis=1)

    # weighted average 40% - 60%
    top3 = 0.45
    last3 = 0.55

    df_6m['FORECAST'] = (df_6m['TOP3_AVG'] * top3 + df_6m['LAST3_AVG'] * last3).round(0)

    # if FORECAST < AVERAGE then FORECAST = AVERAGE & if FORECAST <=0 then FORECAST = 1
    df_6m['FORECAST'] = (
        df_6m['FORECAST']
        .clip(lower=1)
        .combine(df_6m['AVERAGE'], max)
    )

    # merge with Holt-Winter
    df_hw = df_hw[['SKU', 'Holt-Winter']]
    df_show = pd.merge(df_6m, df_hw, on=["SKU"], how='outer')

    supplier = df_show.loc[0,'SUPPLIER']
    df_show = df_show.drop(['SUPPLIER', 'TOP3_AVG', 'LAST3_AVG'], axis=1)

    df_show = df_show.rename(columns={'Holt-Winter': 'HOLT-WINTER'})

    gb = GridOptionsBuilder.from_dataframe(df_show)

    # set column color___________________________
    # bg_color = {
    #     "FORECAST": "#FFFFFF",
    #     "HOLT-WINTER": "#FFFFFF",
    #     "AVERAGE": "#FFFFFF",
    # }

    # for col, color in bg_color.items():
    #     gb.configure_column(
    #         col,
    #         cellStyle={
    #             "backgroundColor": color
    #         }
    #     )

    # for alternative row color _____________
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

    # define columns header class ___________________________
    gb.configure_column(df_show.columns[0], headerClass="sku-header")
    gb.configure_column(df_show.columns[1], headerClass="month-header")
    gb.configure_column(df_show.columns[2], headerClass="month-header")
    gb.configure_column(df_show.columns[3], headerClass="month-header")
    gb.configure_column(df_show.columns[4], headerClass="month-header")
    gb.configure_column(df_show.columns[5], headerClass="month-header")
    gb.configure_column(df_show.columns[6], headerClass="month-header")
    gb.configure_column("FORECAST", headerClass="forecast-header")
    gb.configure_column("HOLT-WINTER", headerClass="hw-header")
    gb.configure_column("AVERAGE", headerClass="average-header")

    # set AgGrid header font & background colors_____________
    custom_css = {
        ".sku-header": {
            "background-color": "#B2DFEE",
            "color": "black"
        },

        ".month-header": {
            "background-color": "#CFCFCF",
            "color": "black"
        },

        ".forecast-header": {
            "background-color": "#FFE7BA",
            "color": "black"
        },
        ".hw-header": {
            "background-color": "#F0FFF0",
            "color": "black"
        },
        ".average-header": {
            "background-color": "#B2DFEE",
            "color": "black"
        },

    }

    utils.show_header(supplier.upper() + " SALES FORECAST")

    # create summary file for sub-header table ________________________________________
    cols = df_show.columns
    df_rva = df_show[df_show['SKU'].str.startswith('RVA', na=False)]    # accessories
    df_rvf = df_show[df_show['SKU'].str.startswith('RVF', na=False)]    # faucets
    df_rvf_parts = df_show[df_show['SKU'].str.startswith('RVP', na=False)]    # faucets
    df_tub = df_show[df_show['SKU'].str.startswith('RVB6', na=False)]   # bathtubs

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP', 'RVF', 'RVB6')  # accessories, boxes, dummy faucets, faucet parts, faucet, tub
    df_sink = utils.exclude_sku_prefixes(df_show, prefixes)

    all_txt = ['Accessories', 'Sink', 'Faucet', 'Faucet Parts', 'Bathtub']
    all_data = [df_rva, df_sink, df_rvf, df_rvf_parts, df_tub]

    # define lists ___________
    items = []
    count = []
    col1 = []
    col2 = []
    col3 = []
    col4 = []
    col5 = []
    col6 = []
    col7 = []
    col8 = []
    col9 = []

    for i in range(0,5):

        # get appropriate text and datafile ___________
        txt = all_txt[i]
        data = all_data[i]

        # calculate column totals ______________________
        total_sku = int(data['SKU'].count())
        total_col1 = int(data[cols[1]].sum())
        total_col2 = int(data[cols[2]].sum())
        total_col3 = int(data[cols[3]].sum())
        total_col4 = int(data[cols[4]].sum())
        total_col5 = int(data[cols[5]].sum())
        total_col6 = int(data[cols[6]].sum())
        total_col7 = int(data[cols[7]].sum())
        total_col8 = int(data[cols[8]].sum())
        total_col9 = int(data[cols[9]].sum())

        # append to list ____________________
        items.append(txt)
        count.append(total_sku)
        col1.append(total_col1)
        col2.append(total_col2)
        col3.append(total_col3)
        col4.append(total_col4)
        col5.append(total_col5)
        col6.append(total_col6)
        col7.append(total_col7)
        col8.append(total_col8)
        col9.append(total_col9)

    # create summary dataframe __________________
    df_sub = pd.DataFrame({
            'ITEMS': items,
            'COUNT': count,
            cols[1]: col1,
            cols[2]: col2,
            cols[3]: col3,
            cols[4]: col4,
            cols[5]: col5,
            cols[6]: col6,
            cols[7]: col7,
            cols[8]: col8,
            cols[9]: col9,

            })

    # filter and sort dataframe __________
    df_sub = (
        df_sub.loc[df_sub['COUNT'].ne(0)]
        .sort_values('ITEMS')
    )

    # create plotly fig from summary dataframe _____________
    fig = sub_header_table(df_sub)

    col1, col2 = st.columns([7, 0.2])

    # show = df_sink
    # txt = 'Sink'
    #
    #
    # total_sku = show['SKU'].count()
    # total_col1 = int(show[cols[1]].sum())
    # total_col2 = int(show[cols[2]].sum())
    # total_col3 = int(show[cols[3]].sum())
    # total_col4 = int(show[cols[4]].sum())
    # total_col5 = int(show[cols[5]].sum())
    # total_col6 = int(show[cols[6]].sum())
    # total_avg = int(show['AVERAGE'].sum())
    # total_forecast = int(show['FORECAST'].sum())
    # total_holtwinter = int(show['HOLT-WINTER'].sum())


    #with col1:
        # utils.sub_headers([
        #     {"text": txt, "value": total_sku , "color": "#FFFFFF", "bg_color":"#8B2252"},
        #     {"text": cols[1], "value": total_col1, "color": "#FFFFFF"},
        #     {"text": cols[2], "value": total_col2, "color": "#FFFFFF"},
        #     {"text": cols[3], "value": total_col3, "color": "#FFFFFF"},
        #     {"text": cols[4], "value": total_col4, "color": "#FFFFFF"},
        #     {"text": cols[5], "value": total_col5, "color": "#FFFFFF"},
        #     {"text": cols[6], "value": total_col6, "color": "#FFFFFF"},
        #     {"text": "AVERAGE", "value": total_avg, "color": "#FFFFFF", "bg_color":"#ED7D31"},
        #     {"text": "FORECAST", "value": total_forecast, "color": "#FFFFFF", "bg_color":"#4F81BD"},
        #     {"text": "H.WINTER", "value": total_holtwinter, "color": "#FFFFFF", "bg_color": "#70AD47"},
        # ])

    with col1:
        st.plotly_chart(fig, width='stretch')

        height = len(df_show)*35
        if height > 600:
            height=600
        AgGrid(df_show, gridOptions=gb.build(), custom_css=custom_css, height=height, allow_unsafe_jscode=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-10px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    txt1 = 'TOP3_AVG = ' + str(top3)
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:left; font-size: 12px ;border-radius:1%;'
        f' line-height:0em; margin-top:-5px"> {txt1} </p>',
        unsafe_allow_html=True)

    txt2 = 'LAST3_AVG = ' + str(last3)
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:left; font-size: 12px ;border-radius:1%;'
        f' line-height:0em; margin-top:-1px"> {txt2} </p>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-10px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    # st.sidebar.write('TOP3_AVG = ' + str(top3))
    # st.sidebar.write('LAST3_AVG = ' + str(last3))

    # display download links side-by-side ________________
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        utils.download_csv(df_show, "Download Forecast")
    with col2:
        utils.download_csv(df_hw, "Download Holt-Winter Forecast")

    with col3:
        utils.download_csv(df_6m, "Download J-S Forecast")

    return
