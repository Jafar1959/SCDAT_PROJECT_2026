import pandas as pd
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid
from datetime import date, timedelta
from pathlib import Path, PureWindowsPath    # << for Window & Mac OS path-slash '\' or '/'

import scdat_utils_26 as utils
import scdat_data_26 as data

def forecast_fba_wh_incoming_df (datafile_location, forecast_month):

    month = forecast_month.split("_")[1].split("-")[0]
    # year = forecast_month.split("-")[1]

    df_forecast = data.forecast_df(datafile_location, forecast_month)
    df_forecast = df_forecast.rename(columns={'AVERAGE': '6M-AVERAGE'})

    df_fba = data.fba_inventory_df(datafile_location)[['SKU', 'TOTAL FBA STOCK']]
    df_fba = df_fba.rename(columns={'TOTAL FBA STOCK': 'FBA STOCK'})

    df_inventory = data.inventory_df(datafile_location)[['SKU', 'Existing Qty']]
    df_inventory = df_inventory.rename(columns={'Existing Qty': 'WH'})

    df_incoming, *_ = data.container_df(datafile_location)
    df_incoming = df_incoming[['SKU', 'QTY']]
    df_incoming = df_incoming.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    df_incoming = df_incoming.rename(columns={'QTY': 'INCOMING'})

    df = (
        df_forecast
        .merge(df_fba, on="SKU", how="left")
        .merge(df_inventory, on="SKU", how="left")
        .merge(df_incoming, on="SKU", how="left")
        .drop(columns=["SUPPLIER", "MONTH"], errors="ignore")
        .fillna(0)
    )

    # move FBA STOCK column to two place right__________________
    pos = df.columns.get_loc("FBA STOCK")
    col = df.pop("FBA STOCK")
    df.insert(pos + 2, "FBA STOCK", col)

    df['WH STOCK (M)'] = (df['WH']/df['FORECAST']).round(2)
    df = df.rename(columns={'FORECAST': month.upper() + ' FORECAST'})

    df = df.sort_values('SKU', ascending=True)

    return df

def display_maruf_data(datafile_location, forecast_month):

    df = forecast_fba_wh_incoming_df(datafile_location, forecast_month)
    total_sku = df['SKU'].count()

    txt = 'Six-Months Sale, Forecast, Inventory, Incoming, FBA Stock & WH Stock | Total SKU: ' + str(total_sku)
    utils.show_header(txt)

    col1, col2 = st.columns([3, 0.06])

    with col1:
        AgGrid(df, height=680, fit_columns_on_grid_load=True)
        utils.download_csv(df, 'Download Data')
    return


def display_maruf_data_2(datafile_location):
    path_ccs = Path(PureWindowsPath(datafile_location + "CCS\\CCS_Copy.xlsx"))
    df = pd.read_excel(path_ccs, sheet_name='Cargo', header=1,
                       skiprows=lambda x: x in [0, 2])  # discard row 1-3 and consider row 4 is header

    df = df.fillna('BLANK')  # replace the empty cell with 'BLANK'
    df = df.replace(r'^\s*$', 'BLANK', regex=True)  # replace the SPACE in cell with 'BLANK'

    df = df.applymap(str)  # convert entire df to string for Streamlit
    df = df[df['Delivered Date'] != 'BLANK']
    df['Delivered Date'] = pd.to_datetime(df['Delivered Date'])
    df['Delivered Date'] = df['Delivered Date'].dt.date


    start_date = st.sidebar.date_input("Select Start Date", value=date.today() - timedelta(days=7))
    end_date = st.sidebar.date_input("Select End Date")

    df_filtered = df[
        df["Delivered Date"].between(start_date, end_date)
    ]

    result = (
        df_filtered["FROM"]
        .value_counts()
        .reindex(sorted(df["FROM"].unique()), fill_value=0)
        .to_frame()
        .T
    )

    # remove suppliers name with zero value
    result = result.loc[:, (result != 0).any(axis=0)]

    result.index = [f"{start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}"]
    result.index.name = "Date"

    # txt = 'Container Received ' + str([f"{start_date:%Y-%m-%d} to {end_date:%Y-%m-%d}"])
    txt = 'Container Received: ' + str(start_date) + ' to ' + str(end_date)
    utils.show_header(txt)

    col1, col2 = st.columns([3, 0.06])

    with col1:

        st.dataframe(result)
        #st.write(df_filtered)

        df_show = (
            df_filtered
            [["CONTAINER NO.",
              "FROM",
              "MTS File Ref",
              "Container #",
              "Loading Date",
              "Delivered Date",
              "Invoice#",
              "Invoice Amount"]]
                    )
        AgGrid(df_show, height=500, fit_columns_on_grid_load=True)

    return
