from typing import Any

import pandas as pd
from pathlib import Path, PureWindowsPath    # << for Window & Mac OS path-slash '\' or '/'
import os

# import datetime
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
# from datetime import date, timedelta
import calendar

from pandas import Series, DataFrame
from st_aggrid import GridOptionsBuilder, AgGrid    # GridUpdateMode, DataReturnMode

import streamlit as st

# ============== my modules ============================
import scdat_utils_26 as utils

# =============== dfs ====================
def ccs_df(datafile_location):
    path_ccs = Path(PureWindowsPath(datafile_location+ "CCS\\CCS_Copy.xlsx"))
    df = pd.read_excel(path_ccs, sheet_name='Cargo', header=1,
                       skiprows=lambda x: x in [0, 2])  # discard row 1-3 and consider row 4 is header

    df = df.fillna('BLANK')  # replace the empty cell with 'BLANK'
    df = df.replace(r'^\s*$', 'BLANK', regex=True)  # replace the SPACE in cell with 'BLANK'
    df = df[0:2000]

    df = df.astype(str)  # convert entire df to string for Streamlit
    return df

def container_df(datafile_location):
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Container.csv"))

    # read .csv file, select columns and rename columns
    df = (
        pd.read_csv(
            file_path,
            usecols=[
                'Container No.', 'Master Bill Of Lading', 'Estimated At Port Date', 'State',
                'Container Lines/Product SKU', 'Container Lines/Qty To Load',
                'Latest Updates', 'Container Lines/Ship Date'
            ]
        )
        .rename(columns={
            'Container No.': 'PO',
            'Master Bill Of Lading': 'BOL',
            'Estimated At Port Date': 'ODDO_ETA',
            'State': 'STATE',
            'Container Lines/Product SKU': 'SKU',
            'Container Lines/Qty To Load': 'QTY',
            'Latest Updates': 'RECEIVED DATE',
            'Container Lines/Ship Date': 'LOADING DATE'
        })
    )

    # remove space from SKU
    df['SKU'] = df['SKU'].str.strip()

    # forward fill columns
    fill_cols = ['PO', 'BOL', 'ODDO_ETA', 'STATE', 'RECEIVED DATE']
    df[fill_cols] = df[fill_cols].replace(r'^\s*$', pd.NA, regex=True).ffill()

    # remove unwanted PO prefixes
    bad_po_prefix = [
        '0-', 'T', 't',
        '2188HM-C', '2188HM-INCORRECT', '2204HM - CANCEL',
        '2205MM - CANCEL', '2206HM - CANNOT RECEIVE',
        '2241HM - CANNOT RECEIVE', '2241HM - CANCEL',
        '2353 - CANCEL', '2603FC - Cancel',
        '2588HM-CANCEL', '2660RBX', 'Huayi Sample'
    ]

    df = df[~df['PO'].str.startswith(tuple(bad_po_prefix), na=False)]

    # remove unwanted SKUs
    bad_skus = [
        'RVH7417 - DO NOT USE', 'RVH8071 - DO NOT USE',
        'RVH8118 - DO NOT USE', 'RVH8277 - DO NOT USE',
        'RVH8341 [DO NOT USE]', 'RVH8359 - DO NOT USE',
        'RVL2398BK - DO NOT USE', 'RVL2398WH - DO NOT USE'
    ]

    df = df[~df['SKU'].isin(bad_skus)]

    # remove null SKU
    df = df[df['SKU'].notna()]

    # date conversion
    df['ODDO_ETA'] = pd.to_datetime(df['ODDO_ETA']).dt.date

    # extract location
    df['LOCATION'] = df['RECEIVED DATE'].str[13:]

    df['RECEIVED DATE'] = (
        pd.to_datetime(df['RECEIVED DATE'].str[:10])
        .dt.date
    )

    # sort
    df = df.sort_values('PO', ascending=True)

    # split datasets
    df_incoming = df[df['STATE'] != 'Received In Warehouse']
    df_received = df[df['STATE'] == 'Received In Warehouse']

    return df_incoming, df_received, df

def product_df(datafile_location):
    # create product list df
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Product_List.xlsx"))
    df = pd.read_excel(file_path, sheet_name='Sheet1', header=0)

    # remove discontinued items
    df = df[df["Status"] != 'Discontinued']
    df = df[df["Status"] != 'ON HOLD']

    df = df[['Model', 'Supplier', 'Material', 'Product', 'Mounting', 'Bowl', 'Collection', 'FBA', 'Status']]
    df.columns = (['SKU', 'SUPPLIER', 'MATERIAL', 'PRODUCT', 'MOUNTING', 'BOWL', 'COLLECTION', 'FBA', 'STATUS'])
    df['SKU'] = df['SKU'].fillna('VOID')
    df = df[df["SKU"] != 'VOID']
    df['SUPPLIER'] = df['SUPPLIER'].fillna('VOID')
    df = df[df["SUPPLIER"] != 'VOID']
    return df

def inventory_df(datafile_location):
    # table definition [Internal Reference, Name, Quantity on Hand, Vendors/Vendor, Sales Price]
    # create df from Oddo export Inventory.csv and merge with df_product
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Inventory.csv"))
    df_inventory = pd.read_csv(file_path)

    df_inventory = df_inventory[['Internal Reference', 'Quantity On Hand']]

    # change column name
    df_inventory.columns = (['SKU', 'Existing Qty'])

    df_inventory['SKU'] = df_inventory['SKU'].replace(r'^\s*$', None, regex=True)   # treat blanks as NaN and drop them
    df_inventory = df_inventory.dropna(subset=['SKU'])

    # df_inventory = df_inventory['SKU'].fillna('BLANK')  # replace the empty cell with 'BLANK'
    # df_inventory = df_inventory[df_inventory['SKU'] != 'BLANK']

    df_inventory['SKU'] = df_inventory.apply(lambda x: x.iloc[0].strip(), axis=1)   # remove space from SKU

    # df_inventory = df_inventory.fillna('VOID')

    # remove the SKU that does not start with RV
    df_inventory = df_inventory.loc[lambda row: row['SKU'].str.startswith('RV')]

    df_product = product_df(datafile_location)

    df = pd.merge(df_product, df_inventory, on=["SKU"], how='left')

    df = df.sort_values('SKU', ascending=True)

    return df

def fba_inventory_df(datafile_location):
    # create df from Oddo export WH_Inventory_Qty.csv
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\FBA_Inventory.csv"))
    df = pd.read_csv(file_path, encoding='latin-1')

    df = df[['sku', 'afn-total-quantity', 'afn-reserved-quantity', 'afn-unsellable-quantity']]

    df['TOTAL FBA STOCK'] = df['afn-total-quantity'] - df['afn-reserved-quantity'] - df['afn-unsellable-quantity']

    df = df[['sku', 'TOTAL FBA STOCK']]
    df.columns = (['SKU', 'TOTAL FBA STOCK'])
    df = df.loc[lambda row: row['SKU'].str.startswith('RV')]

    df_product = product_df(datafile_location)
    df_product = df_product[df_product['FBA'] == 'FBA']

    df = pd.merge(df_product, df, on=["SKU"], how='left')

    df = df.sort_values('SKU', ascending=True)
    df = df.fillna(0)
    return df

def mts_df(datafile_location):
    path_mts = Path(PureWindowsPath(datafile_location + "CCS\\Shipment_Report.xlsx"))
    df = pd.read_excel(path_mts, sheet_name='ShipmentInfoModel', header=0)
    df = df[['ShipmentNo', 'HBL', 'OriginETD', 'DestinationETA', 'Shipper', 'Container']]
    df.columns = (['Shipment#', 'BOL', 'MTS_ETD', 'MTS_ETA', 'SHIPPER', 'CONTAINERS'])

    # convert to datetime format contains (MM/DD/YYYY HH:MM:SS AM/PM)
    df['MTS_ETD'] = pd.to_datetime(df['MTS_ETD'], format="%m/%d/%Y %I:%M:%S %p")
    df['MTS_ETD'] = pd.to_datetime(df['MTS_ETD']).dt.date

    df['MTS_ETA'] = pd.to_datetime(df['MTS_ETA'], format="%m/%d/%Y %I:%M:%S %p")
    df['MTS_ETA'] = pd.to_datetime(df['MTS_ETA']).dt.date

    df = df.sort_values('Shipment#', ascending=False)
    df = df[0:120]  # from row 0 to 120

    # remove unwanted Shipment#
    df = df[df['Shipment#'] != 'S2246201']  # Not relevant item
    df = df[df['Shipment#'] != 'S2246199']  # Not relevant item
    df = df[df['Shipment#'] != 'S2247651']  # Plados accessories shipment by air
    df = df[df['Shipment#'] != 'S2354069']  # Not relevant item
    df = df[df['Shipment#'] != 'S2355131']  # Not relevant item
    df = df[df['Shipment#'] != 'S2360823']  # Not relevant item
    df = df[df['Shipment#'] != 'S2363627']  # Not relevant item

    return df

def amazon_df(datafile_location, month, year):

    month_no = utils.get_month_no(month)

    if month_no <= 9:
        month_no_str = '0' + str(month_no)
    else:
        month_no_str = str(month_no)

    file_path = Path(PureWindowsPath(datafile_location + 'Amazon\\' + year + '_' + month_no_str + '_Amazon.csv'))

    # create Amazon df
    df = pd.read_csv(file_path, encoding='latin-1')

    df = df[df['order-status'] == 'Shipped']
    df = df[['sku', 'quantity']]
    df = df.loc[lambda row: row['sku'].str.startswith('RV')]

    # st.write(df)
    # st.stop()

    df.columns = (['SKU', 'QTY'])

    # remove '-' and '_' from sku
    for r in range(0, len(df)):
        # sku_long = df.iloc[r][0]
        sku_long = df.iloc[r, 0]
        sku = utils.format_sku(sku_long)
        df.iloc[r, 0] = sku

    df = df.groupby('SKU')['QTY'].sum().to_frame().reset_index()

    return df

def zen_df(datafile_location, month, year):
    month_no = utils.get_month_no(month)

    if month_no <= 9:
        month_no_str = '0' + str(month_no)
    else:
        month_no_str = str(month_no)

    file_path = Path(PureWindowsPath(datafile_location + 'Oddo\\' + year + '_' + month_no_str + '_Oddo.csv'))
    df = pd.read_csv(file_path)
    df = df[['Reference', 'Product SKU', 'Quantity', 'Creation Date', 'Dealer', 'Status']]
    df.columns = (['REF', 'SKU', 'QTY', 'DATE', 'DEALER', 'STATUS'])

    df = df.loc[lambda row: row['REF'].str.startswith('C')]  # GET RECORDS STARTS WITH C0015...

    df = df[df["STATUS"] != 'Cancelled']
    df = df[df["STATUS"] != 'Draft']

    # filter data for one month
    df['DATE'] = pd.to_datetime(df['DATE'])
    # df = df[df['DATE'].dt.month == get_month_no(month)]

    df.reset_index(drop=True, inplace=True)  # order index

    # manage sku and qty like xxxx, xxxx and 1,1
    # get col values in list
    ref = df['REF'].to_list()
    sku = df['SKU'].to_list()
    qty = df['QTY'].to_list()
    date = df['DATE'].to_list()
    dealer = df['DEALER'].to_list()
    status = df['STATUS'].to_list()

    # create new lists
    new_REF = []
    new_SKU = []
    new_QTY = []
    new_DATE = []
    new_DEALER = []
    new_STATUS = []

    for r in range(len(ref)):
        new_ref = ref[r]
        new_sku = sku[r]
        new_qty = qty[r]
        new_date = date[r]
        new_dealer = dealer[r]
        new_status = status[r]

        sku1 = str(new_sku).split(',')
        qty1 = str(new_qty).split(',')

        for j in range(len(sku1)):
            new_REF.append(new_ref)
            new_DATE.append(new_date)
            new_DEALER.append(new_dealer)
            new_STATUS.append(new_status)

            new_SKU.append(sku1[j])

            #new_QTY.append(int(qty1[j]))
            new_QTY.append(qty1[j])

    # modified df
    df_new = pd.DataFrame({'REF': new_REF, 'SKU': new_SKU, 'QTY': new_QTY, 'DATE': new_DATE, 'DEALER': new_DEALER,
                           'STATUS': new_STATUS})

    df_new = df_new.loc[lambda row: row['SKU'].str.startswith('RV')]

    df_new['QTY'] = df_new['QTY'].astype(float)

    df_new.index = range(1, df_new.shape[0] + 1)

    return df_new

def wh_wise_inventory_df(datafile_location):
    # --------------- create dataframe from WH_Inventory_Qty.csv --------------------------
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\WH_Inventory_Qty.csv"))
    df_wh = pd.read_csv(file_path)

    # -------------- Change column name & select columns ------------------------------
    df_wh = df_wh.rename(columns={
        'Product/Internal Reference': 'SKU',
        'Location': 'LOCATION',
        'Inventoried Quantity': 'QTY'
    })[['SKU', 'LOCATION', 'QTY']]

    # ---------------- exclude locations and remove blank SKUs ------------------------
    excluded_locations = [
        'AMZ/Stock',
        'WH1/Output',
        'WH1/Quality Check',
        'WH1/Stock',
        'WH1/Stock/DAMAGED',
        'WH1/Stock/Virtual-WH5'
    ]

    df_wh = df_wh[
        ~df_wh['LOCATION'].isin(excluded_locations) & df_wh['SKU'].notna()
        ]

    # --------------- add suppliers name --------------------------------------------------------------
    df_product = product_df(datafile_location)[['SKU', 'SUPPLIER']]

    df_wh = (
        df_wh
        .merge(df_product, on='SKU', how='left')
        .sort_values(['LOCATION', 'SKU'])
        .rename(columns={'LOCATION': 'WH_LOCATION'})
    )

    # -------------------- get location string only --------------------------------------------------
    df_wh['LOCATION'] = df_wh['WH_LOCATION'].str.rsplit('/', n=1).str[-1]

    # ----------------- get accessories inventory only ----------------------------------------------
    df_accessories = df_wh[df_wh['SKU'].str.startswith('RVA')]

    # ----------------- Bathtubs only -------------------------------------------------------------
    df_bathtub = df_wh.loc[lambda row: row['SKU'].str.startswith('RVB6')]

    # ----------------- Faucets only ------------------------------------------------------------
    df_faucet = df_wh.loc[lambda row: row['SKU'].str.startswith('RVF')]

    # ------------------- Faucet Parts only  -----------------------------------------------------------
    df_faucet_parts = df_wh.loc[lambda row: row['SKU'].str.startswith('RVP')]

    # ------------------- Packing Box ------------------------------------------------------------------
    df_box = df_wh.loc[lambda row: row['SKU'].str.startswith('RBX')]

    # ----------------- Refurbished Inventory only ----------------------------------------------------
    df_refurb = df_wh.loc[lambda row: row['SKU'].str.endswith('-REFURB')]

    # ----------------------- Lowes Retail Models only ---------------------------------------------------
    retail_models = ['RVA9001LM', 'RVH180051LM', 'RVH183001LM', 'RVH185841LM', 'RVH165301BL', 'RVG11080BK', 'RVG123061BK']
    df_retail = df_wh[df_wh['SKU'].isin(retail_models)]

    prefixes = (
        'RVA',  # accessories
        'RVP',  # faucet parts
        'RDM',  # dummy faucet
        'RBX',  # packing boxes
        'RVF',  # faucets
        'RVB6', # bathtubs
        'OPEN-BOX'  # openbox
        )

    df_sink = utils.exclude_sku_prefixes(df_wh, prefixes)
    df_sink = df_sink.loc[lambda row: ~ row['SKU'].str.endswith('-REFURB')]     # remove refurb skus

    # st.write(df_sink)
    # utils.download_csv(df_sink, 'Download Sink Data')
    # st.stop()

    # -------------- get WH1 inventory only (P, Q, P-RECEIVING) -------------------------------------
    df_wh1 = df_sink[df_sink['LOCATION'].str.startswith(('P', 'Q', 'P-R'))]

    # --------------- WH3 inventory only, location T only  ------------------------------------------
    df_wh3 = df_sink[df_sink['LOCATION'].str.startswith('T')]

    # ----------------- WH4 inventory only, locations J, K and L-FLOOR -----------------------------
    df_wh4 = df_sink[df_sink['LOCATION'].str.startswith(('J', 'K', 'L-F'))]

    # ------------ WH2 - HOUSTON inventory only ----------------------------------------------------
    df_wh2 = df_sink[df_sink['LOCATION'].str.startswith(('G', 'H', 'F-F'))]

    # location L-CONTAINER only  << ======================================================
    df_container = df_sink[df_sink['LOCATION'].str.startswith('L-CON')]

    return df_wh, df_wh1, df_wh2, df_wh3, df_wh4, df_accessories, df_box, df_refurb, df_container, df_retail, retail_models, df_faucet, \
        df_bathtub, df_faucet_parts


def sc_summary_df_OLD(datafile_location, supplier, model):

    # ----------------- df_CCS for incoming containers only ---------------------------------------
    df_ccs = ccs_df(datafile_location)
    df_ccs = df_ccs[df_ccs['Delivered Date'] == 'BLANK']
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date']]
    df_ccs = df_ccs.rename(columns={'CONTAINER NO.': 'PO', 'FROM': 'SUPPLIER'})

    # --------------- INCOMING CONTAINERS ONLY --------------------------------
    df_container = container_df(datafile_location)
    df_container = df_container[df_container['STATE'] != 'Received In Warehouse']

    df_container = df_container.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # remove all accessories
    df_container = df_container.loc[lambda row: ~ row['SKU'].str.startswith('RVP')]     # remove faucet accessories

    df_container = df_container.rename(columns={'ODDO_ETA': 'ZEN_ETA'})
    df_container['PO'] = df_container.apply(lambda x: str(x.iloc[0])[0:4], axis=1)      # keep only first 4-digit of container no.

    # ------------------- MERGE (CCS + CONTAINER) -----------------------------------------------
    df_ccs_container = pd.merge(df_ccs, df_container, on=["PO"], how='left')
    df_ccs_container = df_ccs_container[['PO', 'SUPPLIER', 'Loading Date', 'ZEN_ETA', 'SKU', 'QTY']]
    df_ccs_container = df_ccs_container.fillna(0)
    df_ccs_container = df_ccs_container[df_ccs_container['ZEN_ETA'] != 0]

    # --------------------- QUERY ON SUPPLIER --------------------------------------------------
    df = df_ccs_container.copy()    # make a copy of the merge file

    if supplier == 'Speed':     # query on supplier ================================
        df = df[df['SUPPLIER'].isin(['Speed', 'Speed (Vietta)'])]
    elif supplier != 'ALL':
        df = df[df['SUPPLIER'] == supplier]


    if model != 'ALL':   # query on model or color ================================

        df = df.loc[
            lambda row: row['SKU'].str.startswith(model.upper()) |
                        row['SKU'].str.endswith(model.upper())
        ]

    total_incoming_qty = df['QTY'].sum()

    df_container_no = df.drop_duplicates(subset=['PO'], keep='first')
    incoming_containers = df_container_no['PO'].count()

    # ------------------ SUMMARY DATAFRAME ------------------------------------------------
    df_summary = pd.DataFrame({'Ocean': [total_incoming_qty],
                               'Containers': [incoming_containers],
                               })

    # datafile columns: df = [PO, SUPPLIER, Loading Date, ZEN_ETA, SKU, QTY]
    # datafile columns: df_summary = [Ocean, Containers]
    return df, df_summary


def monthly_incoming_and_received_qty_OLD(datafile_location, supplier, model):
    first_day = datetime.today().replace(day=1)
    first_day = first_day.strftime("%Y-%m-%d")


    st.write(first_day)

    # ----------------- df_CCS for incoming containers only ---------------------------------------
    df_ccs = ccs_df(datafile_location)
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date']]
    df_ccs = df_ccs.rename(columns={'CONTAINER NO.': 'PO', 'FROM': 'SUPPLIER'})

    # --------------- INCOMING CONTAINERS ONLY --------------------------------
    df_container = container_df(datafile_location)
    df_container = df_container.rename(columns={'ODDO_ETA': 'ZEN_ETA'})     # change column name

    df_container = df_container.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]  # remove all accessories
    df_container = df_container.loc[lambda row: ~ row['SKU'].str.startswith('RVP')]  # remove faucet accessories

    df_container['PO'] = df_container['PO'].astype(str).str.extract(r"(\d{4})")
    # df_container['PO'] = df_container.apply(lambda x: str(x.iloc[0])[0:4], axis=1)  # keep only first 4-digit of container no.

    df_in_ocean = df_container[df_container['STATE'] != 'Received In Warehouse']
    df_in_ocean = pd.merge(df_ccs, df_in_ocean, on=["PO"], how='left')
    df_in_ocean = df_in_ocean[df_in_ocean['SUPPLIER'] != 'BLANK']
    df_in_ocean = df_in_ocean[['PO', 'SUPPLIER', 'Loading Date', 'ZEN_ETA', 'SKU', 'QTY']]

    df_received = df_container[df_container['STATE'] == 'Received In Warehouse']
    df_received = pd.merge(df_received, df_container, on=["PO"], how='left')

    st.dataframe(df_in_ocean)
    st.dataframe(df_received)
    st.stop()

    df_container = df_container.rename(columns={'ODDO_ETA': 'ZEN_ETA'})
    df_container['PO'] = df_container.apply(lambda x: str(x.iloc[0])[0:4], axis=1)      # keep only first 4-digit of container no.

    # ------------------- MERGE (CCS + CONTAINER) -----------------------------------------------
    df_ccs_container = pd.merge(df_ccs, df_container, on=["PO"], how='left')
    df_ccs_container = df_ccs_container[['PO', 'SUPPLIER', 'Loading Date', 'ZEN_ETA', 'SKU', 'QTY']]
    df_ccs_container = df_ccs_container.fillna(0)
    df_ccs_container = df_ccs_container[df_ccs_container['ZEN_ETA'] != 0]

    # --------------------- QUERY ON SUPPLIER --------------------------------------------------
    df = df_ccs_container.copy()    # make a copy of the merge file

    if supplier == 'Speed':     # query on supplier ================================
        df = df[df['SUPPLIER'].isin(['Speed', 'Speed (Vietta)'])]
    elif supplier != 'ALL':
        df = df[df['SUPPLIER'] == supplier]


    if model != 'ALL':   # query on model or color ================================

        df = df.loc[
            lambda row: row['SKU'].str.startswith(model.upper()) |
                        row['SKU'].str.endswith(model.upper())
        ]

    total_incoming_qty = df['QTY'].sum()

    df_container_no = df.drop_duplicates(subset=['PO'], keep='first')
    incoming_containers = df_container_no['PO'].count()

    # ------------------ SUMMARY DATAFRAME ------------------------------------------------
    df_summary = pd.DataFrame({'Ocean': [total_incoming_qty],
                               'Containers': [incoming_containers],
                               })

    # datafile columns: df = [PO, SUPPLIER, Loading Date, ZEN_ETA, SKU, QTY]
    # datafile columns: df_summary = [Ocean, Containers]
    return # df, df_summary

def inocean_container_df(datafile_location, df):

    df_qty = container_wise_incoming_qty(datafile_location)
    df_qty = df_qty.groupby('PO')['QTY'].sum().to_frame().reset_index()

    df = df.rename(columns={'CONTAINER NO.': 'PO'})
    df = pd.merge(df, df_qty, on=['PO'], how='left')

    # df_monthly_group = df.groupby(['FROM', 'Loading Date'])['PO'].count().to_frame().reset_index()
    df['Loading Date'] = df['Loading Date'].astype(str)

    df_monthly_group = df.groupby(['FROM', 'Loading Date']).agg({
        'PO': 'count',
        'QTY': 'sum'
        }).reset_index()

    st.write(df_monthly_group)
    # st.write(df_monthly_group.columns)
    # st.stop()


    list1 = df_monthly_group['Loading Date'].to_list()
    month_list = list(set(list1))   # remove duplicate from list1
    month_list.sort()

    # get previous & current year container loading data
    df = pd.DataFrame({})
    for m in month_list:
        df_temp = df_monthly_group[df_monthly_group['Loading Date'] == m]
        df_temp = df_temp[['FROM', 'PO', 'QTY']]

        month_no = int(m[-2:])  # get month number
        year = m[2:4]  # get month number
        month_name = date(1900, month_no, 1).strftime('%b') # get short month name
        df_temp = df_temp.rename(columns={'PO': month_name.upper() + '-' + year +' Loaded'})
        df_temp = df_temp.rename(columns={'QTY': month_name.upper() + '-' + year +' Qty'})

        if  m == month_list[0]:
            df = df_temp
        else:
            df = pd.merge(df, df_temp, on=['FROM'], how='outer')

    df = df.fillna('')

    # df_filtered = df.iloc[:,-4:]    # get only last 4 columns

    df_filtered = pd.concat([
        df.iloc[:, [0]],  # First column
        df.iloc[:, -8:]  # Last 4 columns
        ], axis=1)

    st.write(df_filtered)



    return df_filtered, df


def monthly_container_loading_OLD(datafile_location):
    current_year = datetime.today().year
    start_date = pd.to_datetime(str(current_year - 1) + '-01-01')

    df_ccs = ccs_df(datafile_location)

    df = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date']]

    df = df[df['Loading Date'] != 'BLANK']

    df['Loading Date'] = pd.to_datetime(df['Loading Date'])

    df = df[df['Loading Date'] >= start_date]

    df['Loading Date'] = df['Loading Date'].dt.to_period('M')   # remove date from the 'Loading Date' - 2025-01, 2025-02

    df_monthly_group = df.groupby('Loading Date')['CONTAINER NO.'].count().to_frame().reset_index()

    df_monthly_group.reset_index(drop=True, inplace=True)
    df_monthly_group.index = range(1, df_monthly_group.shape[0] + 1)

    df_monthly_group['Loading Date'] = df_monthly_group['Loading Date'].astype(str)     # convert period to str

    # st.write(df_ccs)  # all CCS data
    # st.write(df)  # date removed from 'Loading Date'
    # st.write(df_monthly_group)    # data number of container per month

    inocean_container_df(datafile_location, df)

    return df_monthly_group, df_ccs, df

def container_wise_incoming_qty(datafile_location):
    df_container = container_df(datafile_location)
    
    df_container = df_container[['PO', 'QTY', 'RECEIVED DATE', 'STATE']]
    df_container['PO'] = df_container['PO'].str[:4]

    # st.write(df_container)
    # st.stop()
    return df_container

def backorder_df(datafile_location):
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Backorder.csv"))
    df = pd.read_csv(file_path, encoding='latin-1')

    df = df[['Source Document', 'Scheduled Date', 'Product SKU', 'Quantity', 'Dealer', 'Status']]
    df = df.fillna('VOID')

    df['Scheduled Date'] = pd.to_datetime(df['Scheduled Date'])
    df['Scheduled Date'] = df['Scheduled Date'].dt.date
    df = df.groupby(['Source Document', 'Product SKU', 'Scheduled Date', 'Dealer'])['Quantity'].sum().to_frame().reset_index()
    df = df[['Source Document', 'Scheduled Date', 'Product SKU', 'Quantity', 'Dealer']]

    df = df.rename(columns={'Product SKU': 'SKU'})
    df = df.sort_values('Source Document', ascending=True)
    df.reset_index(drop=True, inplace=True)
    df.index = range(1, df.shape[0] + 1)
    # st.dataframe(df)
    # st.stop()
    return df

def sales_trend_df(datafile_location, supplier, model, month_list):
    df_sales = pd.DataFrame({})

    for i in range (0, len(month_list)):
        m = str(month_list[i])[:3]      # get month short name from month_list like Jan, Feb ....
        y = str(month_list[i])[-2:]     # get month two digit year like 25, 26 ....

        month_num = datetime.strptime(m, "%b").month    # get month number from short month name

        month_num = f"{month_num:02}"   # format month number as '01', '02' etc

        file_name = y + month_num + '_Sales_' + str(month_list[i]) + '.csv'     # generate monthly sales file name

        path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY\\' + file_name    # read monthly sales file
        df = pd.read_csv(Path(PureWindowsPath(path)))
        df = df[['SKU', 'SUPPLIER', 'AMAZON', 'ODDO', 'TOTAL']]

        df1 = utils.supplier_model_query(df, supplier, model)  # query on supplier & model / color

        if len(df1) == 0:

            df1 = pd.DataFrame({'SKU':[0],
                               'SUPPLIER':[0],
                               'AMAZON': [0],
                               'ODDO': [0],
                               'TOTAL':[0],
                               'MONTH':month_list[i]})

        else:
            df1['MONTH'] = month_list[i]

        if i == 0:
            df_sales = df1

        else:
            df_sales = pd.concat([df_sales, df1])

    df_sink = df_sales[~df_sales['SKU'].astype(str).str.contains("RVA")]    # <<<<<<<<<< Remove RVA for mixed type data

    df_summary = df_sink.groupby('MONTH', sort=False)['TOTAL'].sum().to_frame().reset_index()
    df_summary = df_summary.rename(columns={'TOTAL': 'SALES'})
    df_summary["12M_AVG"] = df_summary["SALES"].rolling(window=12).mean()

    # st.write(df_summary)
    # st.stop()

    return df_summary, df_sales

def forecast_trend_df(datafile_location, supplier, model, month_list):

    dfs = []

    for i in range(0 , len(month_list)):

        # find Forecast_Month ===================================================
        month_name = month_list[i]
        year = '20' + month_name[-2:]       # like year 2025

        month_no = datetime.strptime(month_name[:3], "%b").month    # get month number from short name 'Jan'

        month_no = f"{int(month_no):02}"    # convert month number to 2-digit '01'

        forecast_month = month_no + '_' + month_name[:3] + '-' + year   # create forecast month '11_Nov-2025'
        # st.write(forecast_month)

        df = forecast_df(datafile_location, forecast_month, supplier)
        df = df[['SKU', 'SUPPLIER', 'FORECAST', 'MONTH']]
        dfs.append(df)

    df_forecast: Series | DataFrame | Any = pd.concat(dfs, ignore_index=True)
    model = model.upper()
    if model != 'ALL':  # query on model or color
        df_forecast = df_forecast.loc[
            lambda row: row['SKU'].str.startswith(model.upper()) |
                        row['SKU'].str.endswith(model.upper())
        ]

    # df_sink = df_forecast[~df_forecast['SKU'].astype(str).str.contains("RVA")]      # <<<<<<<<<< REMOVE RVA <<<<<<<<<<<<<<

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')  # accessories, boxes, dummy faucets, faucet parts
    df_sink = utils.exclude_sku_prefixes(df_forecast, prefixes)
    #
    df_sink = df_sink.groupby('MONTH', sort=False)['FORECAST'].sum().to_frame().reset_index()
    #
    # st.write(df_sink)
    # st.write(df_forecast)
    # # st.stop()

    return df_sink, df_forecast

def loading_trend_df(datafile_location, supplier, model, month_names):
    values = container_df(datafile_location)      # get container data ===================================
    df_container = values[2]

    df_container = df_container[['SKU', 'QTY', 'PO', 'STATE', 'RECEIVED DATE']]
    df_container['PO'] = df_container['PO'].str[:4]      # get only first 4 digit of PO

    df_ccs = ccs_df(datafile_location)      # get CCS data =====================================================
    df_ccs = df_ccs[df_ccs["Loading Date"] != 'BLANK']
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date']]
    df_ccs = df_ccs.rename(columns={'CONTAINER NO.': 'PO', 'FROM': 'SUPPLIER', 'Loading Date': 'LOADING DATE'})

    df_ccs['LOADING DATE'] = pd.to_datetime(df_ccs['LOADING DATE'])
    df_ccs['LOADING DATE'] = df_ccs['LOADING DATE'].dt.date     # remove timestamp

    # merge to get supplier name
    df = pd.merge(df_container, df_ccs, on=["PO"], how='left')
    df = df[['PO', 'SUPPLIER', 'SKU', 'QTY', 'LOADING DATE', 'RECEIVED DATE', 'STATE']]

    exclude_prefixes = ('RVA', 'RBX', 'RDM', 'RVP')     # remove all accessories, packing boxes, dummy faucet & faucet parts
    df = df[~df['SKU'].str.startswith(exclude_prefixes)]

    df = df.dropna(subset='SUPPLIER')       # remove row with SUPPLIER = null

    df['SUPPLIER'] = df['SUPPLIER'].replace('Speed (Vietta)', 'Speed')      # replace Speed (Vietta) --> Speed

    df_received = df[df['STATE'] == 'Received In Warehouse'].copy()     # get container received data ================

    df_received['RECEIVED DATE'] = pd.to_datetime(df_received['RECEIVED DATE'])
    df_received['RECEIVED DATE'] = df_received['RECEIVED DATE'].dt.to_period('M')       # remove date

    df_received = utils.supplier_model_query(df_received, supplier, model)      # query on supplier & model

    df_received = df_received.groupby('RECEIVED DATE')['QTY'].sum().to_frame().reset_index()

    df_received['RECEIVED DATE'] = df_received['RECEIVED DATE'].astype(str)     # convert 'period' type data to str

    df_received['RECEIVED DATE'] = pd.to_datetime(df_received['RECEIVED DATE'], format='%Y-%m').dt.strftime('%b-%y')    # convert 2024-03 to Mar-24

    df_received = df_received[df_received['RECEIVED DATE'].isin(month_names)]

    df_loading = df.copy()      # get container loading data =======================================================

    df_loading['LOADING DATE'] = pd.to_datetime(df_loading['LOADING DATE'])
    df_loading['LOADING DATE'] = df_loading['LOADING DATE'].dt.to_period('M')       # remove date

    df_loading = utils.supplier_model_query(df_loading, supplier, model)        # query on supplier & model

    df_loading = df_loading.groupby('LOADING DATE')['QTY'].sum().to_frame().reset_index()

    df_loading['LOADING DATE'] = df_loading['LOADING DATE'].astype(str)  # convert 'period' type data to str

    df_loading['LOADING DATE'] = pd.to_datetime(df_loading['LOADING DATE'], format='%Y-%m').dt.strftime('%b-%y')  # convert 2024-03 to

    df_loading = df_loading[df_loading['LOADING DATE'].isin(month_names)]

    return df_loading, df_received


def forecast_df(datafile_location, forecast_month, supplier='ALL'):
    # read all Projection files and create a df as per forecast month
    y = forecast_month.split('-')
    year = y[1]     # find year
    short_month_name = y[0][3:6]    # find month name

    path = datafile_location + 'Projection\\' + year + '\\' + forecast_month + '\\'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort()

    # filter source_files by supplier ======================================================
    if supplier != 'ALL':

        source_files = [x for x in source_files if supplier.upper() in str(x)]  # source_file for selected supplier only

    if supplier == 'Speed':

        source_files = [f for f in source_files if supplier.upper() in f]
        source_files = [f for f in source_files if 'SPEED VIETNAM' not in f]  # remove from list
        source_files = [f for f in source_files if 'SPEED_RVA' not in f]      # remove from list

    if len(source_files) == 0:      # if supplier not found in the source_file return empty dataframe
        long_month_name = datetime.strptime(short_month_name, "%b").strftime("%B")

        months = list(calendar.month_name)  # get list of 12 months

        start_index = months.index(long_month_name)  # Find index of the starting month

        six_month_list = []
        for i in range(6):  # Generate 6 months backward
            idx = (start_index - i)
            six_month_list.append(months[idx])

        df_forecast = pd.DataFrame({'SKU': [0],  # create a empty dataframe
                           six_month_list[0].upper(): [0],
                           six_month_list[1].upper(): [0],
                           six_month_list[2].upper(): [0],
                           six_month_list[3].upper(): [0],
                           six_month_list[4].upper(): [0],
                           six_month_list[5].upper(): [0],
                           'AVERAGE': [0],
                           'FORECAST': [1],
                           'SUPPLIER': supplier.upper(),
                           'MONTH': forecast_month[3:6] + '-' + forecast_month[-2:]
                           })
        return df_forecast

    else:   # read all source_file and append
        df_forecast = pd.DataFrame({})

        for j in range(0, len(source_files)):

            file_path = datafile_location + 'Projection\\' + year + '\\' + forecast_month + '\\' + str(source_files[j])

            df = pd.read_excel(Path(PureWindowsPath(file_path)), sheet_name='Jafar_Data', header=1)

            df = df.iloc[:, :9]     # get first 9 columns only

            value1 = 'TOTAL'
            df = df[~ df['SKU'].str.contains(value1.upper(), case=False, na=False)]  # remove TOTAL row, if any

            value2 = 'SINK ONLY'
            df = df[~ df['SKU'].str.contains(value2.upper(), case=False, na=False)]  # remove SINK ONLY row, if any

            df['SUPPLIER'] = supplier.upper()
            df['MONTH'] = forecast_month[3:6] + '-' + forecast_month[-2:]

            if j == 0:
                df_forecast = df

            else:
                df_forecast = pd.concat([df_forecast, df])      # append all suppliers forecast


    return df_forecast

def one_month_sales_df(datafile_location, month, year):

    # create Amazon df
    df_amazon = amazon_df(datafile_location, month, year)

    # create oddo df
    df_oddo = zen_df(datafile_location, month, year)

    # remove Amazon data from Oddo (Amazon data taken from Amazon website)
    df_oddo = df_oddo[df_oddo["DEALER"] != 'Amazon']

    df_oddo = df_oddo.groupby(['SKU'])['QTY'].sum().to_frame().reset_index()

    # merge Amazon & Oddo sales
    df = pd.merge(df_amazon, df_oddo, on=["SKU"], how='outer')

    if len(df_amazon) > 0:
        df.columns = (['SKU', 'AMAZON', 'ODDO'])

    else:
        df.columns = (['AMAZON', 'SKU', 'ODDO'])
        df = df[['SKU', 'AMAZON', 'ODDO']]

    df = df.fillna(0)  # replace al n/a by 0

    # create Total sale col
    df['TOTAL'] = df['AMAZON'] + df['ODDO']
    df = df.sort_values('SKU', ascending=True)  # sort on 'sku'

    # get SKU that starts with 'RV'
    df = df.loc[lambda row: row['SKU'].str.startswith('RV')]

    # merge with product_df to get supplier
    df_product = product_df(datafile_location)
    df = pd.merge(df_product, df, on=["SKU"], how='left')

    # add unit Dealer Cost col
    df_price = price_list_df(datafile_location)
    df = pd.merge(df, df_price, on=["SKU"], how='left')
    df = df.fillna(0)
    df = df.rename(columns={'PRICE': 'UNIT PRICE'})

    #st.write(df)
    return df


def price_list_df(datafile_location):

    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Inventory.csv"))
    df = pd.read_csv(file_path, header=0)
    df = df[['Internal Reference', 'Sales Price']]

    df = df.rename(columns={'Sales Price': 'PRICE', 'Internal Reference': 'SKU'})
    df = df.fillna(0)
    df = df[df['SKU'] != 0]

    df = df[df['PRICE'] != 0]
    df = df.loc[lambda row: row['SKU'].str.startswith('RV')]

    #st.write(df)
    #st.stop()

    return df


def sales_anatomy_df(datafile_location, month, year):
    df_price = price_list_df(datafile_location)
    df_price = df_price.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]

    df_sales = one_month_sales_df(datafile_location, month, year)
    df_sales = df_sales.loc[lambda row: row['SKU'].str.startswith('RV')]
    df_sales = df_sales.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df_sales = df_sales.fillna(0)
    df_sales = df_sales[df_sales['TOTAL'] != 0]

    total_zen = df_sales['ODDO'].sum()
    total_fba = df_sales['AMAZON'].sum()

    df = pd.merge(df_sales, df_price, on=["SKU"], how='left')

    df = df.fillna(0)

    df['PRICE'] = df['PRICE'].astype(int)
    df['TURNOVER'] = df['PRICE'] * df['TOTAL']
    df['TURNOVER_%'] = df['TURNOVER'] * 100/df['TURNOVER'].sum()

    # st.write(df)
    # st.write(df_price)
    # st.stop()

    # ------------------------ create price wise sales summary -------------------
    step = 50
    price = []
    sku = []
    sale = []
    turnover_percent = []
    for i in range(0, df['PRICE'].max(), step):
        price.append(i)
        df_temp = df[df['PRICE'] > i]
        df_temp = df_temp[df_temp['PRICE'] <= i + step]
        sku.append(df_temp['SKU'].count())
        sale.append(df_temp['TOTAL'].sum())
        turnover_percent.append(round(df_temp['TURNOVER_%'].sum(), 2))

    df_price_sum = pd.DataFrame({'PRICE': price,
                                 'SKU': sku,
                                 'SALES': sale,
                                 'TURNOVER_%': turnover_percent
                                 })

    #st.write(df['TURNOVER'].sum())
    #st.write(max(turnover))
    #st.write(df_price_sum['TURNOVER_%'].tolist())
    # ------------------------ create product summary --------------------------
    df_product_sum = []
    items = ['PRODUCT', 'MATERIAL', 'MOUNTING', 'BOWL', 'COLLECTION']

    for i in range(0, len(items)):
        x = items[i]
        df_product_sum.append(df.groupby([x]).aggregate({'TOTAL': 'sum', 'SKU': 'count'}).reset_index())
        # df_product_sum[i] = df_product_sum[i].sort_values(x, ascending=True)

        index = len(df_product_sum[i]) + 1
        df_product_sum[i].loc[index] = ['TOTAL SALES', df_product_sum[i]['TOTAL'].sum(), df_product_sum[i]['SKU'].sum()]
        df_product_sum[i] = df_product_sum[i][[x, 'SKU', 'TOTAL']]

        # st.write(df_product_sum[i])

    arr = [df_price_sum, df_product_sum, total_zen, total_fba, df]

    # st.write(arr)

    return arr


def yearly_sales_df(datafile_location, year):
    # get list of monthly sales file and sort
    path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort()

    file_list = []

    for i in range (0, len(source_files)):

        if str(source_files[i])[0:2] == str(year)[2:4]:
            file_list.append(source_files[i])

    df_product = product_df(datafile_location)
    df_product = df_product[['SKU', 'SUPPLIER', 'STATUS']]

    # calculate all months sale of the year ==============================
    df_sales = pd.DataFrame({})

    for i in range(0, len(file_list)):

        file_name = str(file_list[i])  # get file name
        s = file_name.split('_')  # split file name based on '_'
        month_name = s[2][:-4]  # get last portion and remove .csv

        path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY\\' + file_list[i]

        df = pd.read_csv(Path(PureWindowsPath(path)))
        df = df[['SKU', 'TOTAL']]
        df = df.rename(columns={'TOTAL': month_name})

        if i == 0:
            df_sales = pd.merge(df_product, df, on=["SKU"], how='left')

        else:
            df_sales = pd.merge(df_sales, df, on=["SKU"], how='outer')

    df_sales = df_sales.fillna(0)
    df_sales = df_sales[df_sales['SUPPLIER'] != 0]

    df_sales['TOTAL'] = df_sales.sum(numeric_only=True, axis=1)

    # +++++++++++ calculate month elapsed in the current year to calculate average +++++++++++++++++++++++++++++++
    today = date.today()

    date1 = date(year, 1, 1)    # first day of the year

    date2 = today   # today's date

    total_days = calendar.monthrange (year, today.month)

    delta = relativedelta(date2, date1)
    month_elapsed = delta.months + delta.days/total_days[1]

    if today.year > year:   # for previous year calculation
        df_sales['AVERAGE'] = round(df_sales['TOTAL']/12, 0)
        month_elapsed = 12

    else:   # for current year calculation
        df_sales['AVERAGE'] = round(df_sales['TOTAL']/month_elapsed, 0)
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    df_price = price_list_df(datafile_location)

    df_sales = pd.merge(df_sales, df_price, on=["SKU"], how='left')
    df_sales = df_sales.fillna(0)

    df_sales['REVENUE'] = round(df_sales['TOTAL'] * df_sales['PRICE']/1000, 2)

    # st.write(df_sales)
    return df_sales, year, month_elapsed


def lowes_sales(datafile_location):
    utils.show_header("Lowe's Sales")
    month_elapsed = utils.get_month_elapsed()
    st.write('Month Elapsed = ' + str(round(month_elapsed,2)))

    path = Path(PureWindowsPath(datafile_location + "LOWES\\Lowe's Sales.xlsx"))
    df = pd.read_excel(path, sheet_name='SALES', header=0)
    df = df[['Day', 'SKU', 'Sales Units - TY']]
    df['Day'] = df['Day'].dt.strftime('%Y-%m')
    df = df.rename(columns={'Sales Units - TY': 'Sales'})

    df_monthly: object = df.groupby(['Day', 'SKU'])['Sales'].count().to_frame().reset_index()

    df_monthly['Day'] = df_monthly['Day'].astype(str)

    month_list = df_monthly['Day'].tolist()
    months = list(dict.fromkeys(month_list))

    df1 = pd.DataFrame({})
    for m in months:
        # st.write(m)
        df_temp = df_monthly[df_monthly['Day'] == m]
        df_temp = df_temp.rename(columns={'Sales': m})
        df_temp = df_temp[['SKU', m]]
        # st.write(df_temp)

        if months.index(m) == 0:
            df1 = df_temp
        else:
            df1 = pd.merge(df1, df_temp, on=["SKU"], how='outer')

    df1 = df1.fillna(0)

    # ============ Total Sales & Monthly Sales ==================
    cols = df1.columns[1:]
    df1['Total'] = df1[cols].sum(axis=1)
    df1['Monthly'] = round(df1['Total'] / month_elapsed, 0)

    # ======================== ADD INVENTORY ===================================
    df_inventory = inventory_df(datafile_location)
    df_inventory = df_inventory[['SKU', 'COLLECTION', 'Existing Qty']]
    df_inventory = df_inventory[df_inventory['COLLECTION'] == 'Lowes']
    df_inventory = df_inventory.drop(columns=['COLLECTION'])

    df_inventory = df_inventory.rename(columns={'Existing Qty': 'WH'})

    df1 = pd.merge(df1, df_inventory, on=["SKU"], how='left')
    # ======================== ADD INCOMING ===================================
    values = container_df(datafile_location)
    df_incoming = values[0]
    df_incoming = df_incoming[['SKU', 'QTY']]
    df_incoming = df_incoming.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    df_incoming = df_incoming.rename(columns={'QTY': 'INCOMING'})

    df1 = pd.merge(df1, df_incoming, on=["SKU"], how='left')

    # =======================+ ADD TOTAL ROW & SHOW TABLE ================================
    df1.loc['Total'] = df1.sum(numeric_only=True)
    df1.loc['Total', df1.columns[0]] = 'TOTAL'

    AgGrid(df1, height=270)
    utils.download_csv(df1, 'Download')
    return

def inventory_level_projection_df_OLD(datafile_location, current_month, current_year, forecast_month, supplier, model):

    return_factor = 0.06  # 6% return
    wh_sales_factor = 0.7  # 70% sales at WH
    fba_send_factor = 0.26  # 26% inventory send to Amazon

    values = weekly_arrival_df(datafile_location, supplier) #current_month, current_year, forecast_month, supplier)
    df = values[0]  # df for the Bar Chart

    # get weekly incoming quantities
    weekly_incoming = df['QTY'].to_list()

    # get current inventory and current month sale
    df2 = sc_summary_inventory_df(datafile_location, current_month, current_year, forecast_month, supplier, model)

    wh_inventory = df2.iloc[0][0]
    current_month_sales = df2.iloc[0][3]
    last_30_days_sales = df2.iloc[0][4]

    # now = datetime.datetime.now()
    # now_days = now.day

    # sales_per_week = round(current_month_sales * 7/(now_days-1), 0)
    # sales_per_week = round(current_month_sales * 7/30, 0)
    avg_sales_per_week = round(last_30_days_sales * 7/30, 0)

    weekly_projection = []
    current_inventory = wh_inventory
    for j in range(0, len(weekly_incoming)):
        projection = round((current_inventory + weekly_incoming[j] * (1 - fba_send_factor) + avg_sales_per_week * return_factor -
                            avg_sales_per_week * wh_sales_factor), 0)

        current_inventory = projection
        weekly_projection.append(projection)

    df['PROJECTION'] = weekly_projection

    return df, avg_sales_per_week, wh_inventory, current_month_sales

def weekly_arrival_df_OLD(datafile_location, supplier):

    def get_week_range(start, end):
        start = start + timedelta(days=1)
        s = str(start).split('-')

        e = str(end).split('-')

        week_range = s[1] + '/' + s[2] + ' - ' + e[1] + '/' + e[2]
        return week_range

    value = sc_summary_container_df(datafile_location, supplier)
    df = value[0]
    #st.write(df)

    df_supplier = df
    if supplier != 'ALL' and supplier != 'Speed':
        df_supplier = df[df['SUPPLIER'] == supplier]

    if supplier == 'Speed':
        df_supplier = df[(df['SUPPLIER'] == 'Speed') | (df['SUPPLIER'] == 'Speed (Vietta)')]

    # calculates dates for next 6 weeks ------------------------------
    today = date.today()
    end_of_week0 = today - timedelta(days=1)
    end_of_week1 = today + timedelta(days=7)
    end_of_week2 = today + timedelta(days=14)
    end_of_week3 = today + timedelta(days=21)
    end_of_week4 = today + timedelta(days=28)
    end_of_week5 = today + timedelta(days=35)
    end_of_week6 = today + timedelta(days=42)
    end_of_week7 = today + timedelta(days=49)
    end_of_week8 = today + timedelta(days=56)
    end_of_week9 = today + timedelta(days=63)
    end_of_week10 = today + timedelta(days=70)

    # st.write(end_of_week1)

    # get week1 incoming container list
    df_week1 = df_supplier[df_supplier['ZEN_ETA'] <= end_of_week1]
    # st.write(df_week1)
    df_week1 = df_week1.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week1_total = df_week1['QTY'].sum()
    df_w1 = df_week1.drop_duplicates(subset=['PO'], keep='first')
    week1_containers = df_w1['PO'].count()

    # get week2 incoming container list
    df_week2 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week1]
    df_week2 = df_week2[df_week2['ZEN_ETA'] <= end_of_week2]
    df_week2 = df_week2.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week2_total = df_week2['QTY'].sum()
    df_w2 = df_week2.drop_duplicates(subset=['PO'], keep='first')
    week2_containers = df_w2['PO'].count()

    # get week3 incoming container list
    df_week3 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week2]
    df_week3 = df_week3[df_week3['ZEN_ETA'] <= end_of_week3]
    df_week3 = df_week3.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week3_total = df_week3['QTY'].sum()
    df_w3 = df_week3.drop_duplicates(subset=['PO'], keep='first')
    week3_containers = df_w3['PO'].count()

    # get week4 incoming container list
    df_week4 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week3]
    df_week4 = df_week4[df_week4['ZEN_ETA'] <= end_of_week4]
    df_week4 = df_week4.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week4_total = df_week4['QTY'].sum()
    df_w4 = df_week4.drop_duplicates(subset=['PO'], keep='first')
    week4_containers = df_w4['PO'].count()

    # get week5 incoming container list
    df_week5 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week4]
    df_week5 = df_week5[df_week5['ZEN_ETA'] <= end_of_week5]
    df_week5 = df_week5.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week5_total = df_week5['QTY'].sum()
    df_w5 = df_week5.drop_duplicates(subset=['PO'], keep='first')
    week5_containers = df_w5['PO'].count()

    # get week6 incoming container list
    df_week6 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week5]
    df_week6 = df_week6[df_week6['ZEN_ETA'] <= end_of_week6]
    df_week6 = df_week6.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week6_total = df_week6['QTY'].sum()
    df_w6 = df_week6.drop_duplicates(subset=['PO'], keep='first')
    week6_containers = df_w6['PO'].count()

    # get week7 incoming container list
    df_week7 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week6]
    df_week7 = df_week7[df_week7['ZEN_ETA'] <= end_of_week7]
    df_week7 = df_week7.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week7_total = df_week7['QTY'].sum()
    df_w7 = df_week7.drop_duplicates(subset=['PO'], keep='first')
    week7_containers = df_w7['PO'].count()

    # get week8 incoming container list
    df_week8 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week7]
    df_week8 = df_week8[df_week8['ZEN_ETA'] <= end_of_week8]
    df_week8 = df_week8.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week8_total = df_week8['QTY'].sum()
    df_w8 = df_week8.drop_duplicates(subset=['PO'], keep='first')
    week8_containers = df_w8['PO'].count()

    # get week9 incoming container list
    df_week9 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week8]
    df_week9 = df_week9[df_week9['ZEN_ETA'] <= end_of_week9]
    df_week9 = df_week9.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week9_total = df_week9['QTY'].sum()
    df_w9 = df_week9.drop_duplicates(subset=['PO'], keep='first')
    week9_containers = df_w9['PO'].count()

    # get week10 incoming container list
    df_week10 = df_supplier[df_supplier['ZEN_ETA'] > end_of_week9]
    df_week10 = df_week10[df_week10['ZEN_ETA'] <= end_of_week10]
    df_week10 = df_week10.groupby(['PO', 'SUPPLIER', 'ZEN_ETA'])['QTY'].sum().to_frame().reset_index()
    week10_total = df_week10['QTY'].sum()
    df_w10 = df_week10.drop_duplicates(subset=['PO'], keep='first')
    week10_containers = df_w10['PO'].count()

    week1 = get_week_range(end_of_week0, end_of_week1)
    week2 = get_week_range(end_of_week1, end_of_week2)
    week3 = get_week_range(end_of_week2, end_of_week3)
    week4 = get_week_range(end_of_week3, end_of_week4)
    week5 = get_week_range(end_of_week4, end_of_week5)
    week6 = get_week_range(end_of_week5, end_of_week6)
    week7 = get_week_range(end_of_week6, end_of_week7)
    week8 = get_week_range(end_of_week7, end_of_week8)
    week9 = get_week_range(end_of_week8, end_of_week9)
    week10 = get_week_range(end_of_week9, end_of_week10)


    df_summary = pd.DataFrame({'WEEK': [week1, week2, week3, week4, week5, week6, week7, week8, week9, week10],
                               'CONTAINER': [week1_containers, week2_containers, week3_containers, week4_containers, week5_containers,
                                             week6_containers, week7_containers, week8_containers, week9_containers, week10_containers],
                               'QTY': [week1_total, week2_total, week3_total, week4_total, week5_total, week6_total, week7_total, week8_total,
                                       week9_total, week10_total]
                               })

    return df_summary, df_week1, df_week2, df_week3, df_week4, df_week5, df_week6, df_week7, df_week8

def sc_summary_container_df(datafile_location, supplier):
    # --------- Provide Sink Data only --------------------------
    # ----------------- CCS incoming only ---------------------------------------
    df_ccs = ccs_df(datafile_location)
    df_ccs = df_ccs[df_ccs['Delivered Date'] == 'BLANK']
    df_ccs = df_ccs[df_ccs['CONTAINER NO.'] != 'BLANK']
    # df_ccs = df_ccs[df_ccs['CONTAINER NO.'] != 'BLANK']
    # st.write(df_ccs)
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date']]
    df_ccs = df_ccs.rename(columns={'CONTAINER NO.': 'PO', 'FROM': 'SUPPLIER'})
    # df_ccs['PO'] = df_ccs.apply(lambda x: str(x.iloc[0])[:-2], axis=1) ----------- blocled on 05/28/2024

    # st.write(df_ccs)
    # st.stop()

    # --------------- INCOMING CONTAINERS ONLY --------------------------------
    df_container = container_df(datafile_location)
    df_container = df_container[df_container['STATE'] != 'Received In Warehouse']

    # exceptions = ['RVA1018BN', 'RVA1018MB']
    # df_container = df_container.loc[
    #     lambda row: ~ row['SKU'].str.startswith('RVA') | row['SKU'].isin(exceptions)
    # ]

    df_container = df_container.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df_container = df_container.loc[lambda row: ~ row['SKU'].str.startswith('RVP')]     # faucet accessories

    df_container = df_container.rename(columns={'ODDO_ETA': 'ZEN_ETA'})
    df_container['PO'] = df_container.apply(lambda x: str(x.iloc[0])[0:4], axis=1)

    # st.write(df_container)

    # ------------------- MERGE (CCS + CONTAINER) -----------------------------------------------
    df_ccs_container = pd.merge(df_ccs, df_container, on=["PO"], how='left')
    df_ccs_container = df_ccs_container[['PO', 'SUPPLIER', 'Loading Date', 'ZEN_ETA', 'SKU', 'QTY']]
    df_ccs_container = df_ccs_container.fillna(0)
    df_ccs_container = df_ccs_container[df_ccs_container['ZEN_ETA'] != 0]

    # --------------------- QUERY ON SUPPLIER --------------------------------------------------
    df = df_ccs_container

    # st.write(df_ccs_container)
    # st.stop()

    if supplier != 'ALL' and supplier != 'Speed':
        df = df[df['SUPPLIER'] == supplier]

    if supplier == 'Speed':
        df = df[(df['SUPPLIER'] == 'Speed') | (df['SUPPLIER'] == 'Speed (Vietta)')]

    incoming_qty = df['QTY'].sum()

    df_container_no = df.drop_duplicates(subset=['PO'], keep='first')
    incoming_containers = df_container_no['PO'].count()


    # ------------------ SUMMARY DATAFRAME ------------------------------------------------
    df_summary = pd.DataFrame({'Ocean': [incoming_qty],
                               'Containers': [incoming_containers],
                               })

    # st.write(df_summary)
    # st.stop()

    return df, df_summary


def weekly_container_arrival_df(datafile_location, supplier, model):
    # get sku and supplier list
    df_product = product_df(datafile_location)[['SKU', 'SUPPLIER']]

    # unpack container_df
    df_ocean, *_ = container_df(datafile_location)

    # merge to add supplier
    df_ocean = pd.merge(df_ocean, df_product, on=["SKU"], how='left')[['PO', 'SKU', 'SUPPLIER', 'ODDO_ETA', 'QTY']]

    # remove all accessories, packing boxes, dummy faucet & faucet parts
    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')
    df_ocean = utils.exclude_sku_prefixes(df_ocean, prefixes)

    # filter based on supplier/model/color
    df = utils.supplier_model_query(df_ocean, supplier, model)

    # Ensure datetime
    df['ODDO_ETA'] = pd.to_datetime(df['ODDO_ETA'])

    # get first date of the df
    today = pd.to_datetime(date.today())

    if not df.empty:
        start_date = min(df['ODDO_ETA'].iloc[0], today)
    else:
        start_date = today

    # generate 8 x 7 = 56 dates from the first date if less
    dates = [start_date + timedelta(days=i) for i in range(56)]

    # create dataframe with 56 dates and merge with df
    df_56 = pd.DataFrame({'ODDO_ETA': dates})
    df = pd.merge(df_56, df, on=["ODDO_ETA"], how='left')
    df = df.fillna(0)

    # Create week-of-month
    df['week_of_month'] = (df['ODDO_ETA'].dt.day - 1) // 7 + 1

    df['month'] = df['ODDO_ETA'].dt.to_period('M')
    df['month_week'] = df['month'].astype(str) + ' W' + df['week_of_month'].astype(str)


    # split df
    df_po = df[['PO', 'month_week']]
    df_po = df_po[df['PO'] != 0]
    df_po = df_po.drop_duplicates(subset='PO')
    df_po = df_po.groupby('month_week')['PO'].count()

    df_qty = df[['QTY', 'month_week']]
    df_qty = df_qty.groupby('month_week', as_index=False)['QTY'].sum()

    df_sum = pd.merge(df_qty, df_po, on=["month_week"], how='left')
    df_sum['PO_QTY'] = df_sum['QTY'].astype(int).astype(str) + ' [' + df_sum['PO'].astype(str) + ']'
    df_sum['PO_QTY'] = df_sum['PO_QTY'].str.replace('.0]', ']', regex=False)

    # st.write(df)    # all data
    # st.write(df_sum)    # summary data
    # st.stop()

    return df, df_sum


def get_date_parts():
    # today = pd.to_datetime("2026-03-31")      # test case
    today = date.today()
    back_30_date = today - timedelta(days=30)

    # st.write(today)
    # st.write(back_30_date)

    return calendar.month_abbr[today.month], today.year, today.day, calendar.month_abbr[back_30_date.month], back_30_date.year, back_30_date.day

def last_30_days_sales_df(datafile_location, supplier, model):
    # unpack data
    current_month, current_year, current_date, back_30_month, back_30_year, back_30_date = get_date_parts()

    # get sales data
    current = str(current_month) + '-' + str(current_year)

    df_current = (one_month_sales_df(datafile_location, current_month, str(current_year))
                  .loc[:, ['SKU', 'SUPPLIER', 'TOTAL']]
                  .rename(columns={'TOTAL': current})
                 )

    if current_date < 30:   # get sales value from previous month
        previous = str(back_30_month) + '-' + str(back_30_year)

        df_back_30_day = (one_month_sales_df(datafile_location, back_30_month, str(back_30_year))
                      .loc[:, ['SKU', 'TOTAL']]
                      .rename(columns={'TOTAL': previous})
                      )
        # merge
        df_sales = df_current.merge(df_back_30_day, on='SKU', how='outer')

        # get total days of back_30_month
        month_num = datetime.strptime(back_30_month, "%b").month
        _, total_days = calendar.monthrange(back_30_year, month_num)

        # st.write(total_days)

        factor = (total_days - back_30_date + 1) / total_days   # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< Need to check
        df_sales['30_Day_Sale'] = round(df_sales[current] + df_sales[previous] * factor, 0)

    else:   # get 30 days sales value from current month only
        df_sales = df_current

        df_sales['30_Day_Sale'] = round(df_sales[current] * 30/(current_date-1), 0)     # use one day less

    # df_sales['Weekly_Sale'] = round(df_sales['30_Day_Sale'] * 7/30, 2)

    df_sales = utils.supplier_model_query(df_sales, supplier, model)

    # st.write(df_sales)
    # st.stop()

    return df_sales

def low_inventory_df(datafile_location, forecast_month, supplier, model):

    # --------------- LOAD INVENTORY DATA  ---------------------------
    df_inventory = (inventory_df(datafile_location)[['SKU', 'SUPPLIER', 'Existing Qty']]
                    .rename(columns={'Existing Qty': 'WH_QTY'})
                    )

    # --------------- LOAD FORECAST DATA ---------------------------
    df_forecast = forecast_df(datafile_location, forecast_month)[['SKU', 'FORECAST']]

    # ------------------- MERGE FORECAST & INVENTORY --------------
    df = (
        df_forecast
        .merge(df_inventory, on='SKU', how='left')
        .fillna({'WH_QTY': 0, 'FORECAST': 0})
    )

    # ============ CALCULATE WH STOCK IN MONTH (Avoid divide-by-zero) ============================
    df['MONTH'] = (df['WH_QTY'] / df['FORECAST'].replace(0, pd.NA)).fillna(0).round(2)

    # =================== FILTER BY SUPPLIER, MODEL AND COLOR ===================================
    df = utils.supplier_model_query(df, supplier, model)  # query on supplier and model

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')  # accessories, boxes, dummy faucets, faucet parts
    df_sink = utils.exclude_sku_prefixes(df, prefixes)
    df_accessories = df.loc[lambda row: row['SKU'].str.startswith('RVA')]

    df_1m = (df_sink[df_sink['MONTH'] <= 1]
            .rename(columns={'MONTH': 'stock'})
             )

    # st.write(df_1m)
    sku_list = df_1m['SKU'].tolist()

    # st.write(sku_list)

    # get incoming inventory
    df, _ = weekly_container_arrival_df(datafile_location, supplier, model)

    df = df[df['SKU'].isin(sku_list)]

    # st.write(df)

    df = df[['SKU', 'QTY', 'month']]
    df = df[df['SKU'] != 0]
    # st.write(df)

    df_1m = (
        df_1m
        .merge(df, on='SKU', how='left')
        .fillna({'WH_QTY': 0, 'QTY':0, 'FORECAST': 0})
    )[['SKU', 'FORECAST', 'WH_QTY', 'QTY','month']]

    # df_1m["month"] = df_1m["month"].astype(str)

    # st.write(df_1m)

    # Base table with all SKUs (ensures all SKUs are included)
    base = df_1m[["SKU", "FORECAST", "WH_QTY"]].drop_duplicates()

    # st.write(base)

    # Replace missing months with a placeholder (optional)
    df_1m["month"] = df_1m["month"].fillna("")

    #df_1m["month"] = df_1m["month"].astype(str)

    # st.write(df_1m)

    # Pivot table to aggregate quantities by SKU and month
    pivot = df_1m.pivot_table(
        index=["SKU"],  # "FORECAST", "WH_QTY"],
        columns="month",
        values="QTY",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    # st.write(pivot)

    result = (
        base
        .merge(pivot, on="SKU", how="left")
        .fillna(0)
        .sort_values(by="FORECAST", ascending=False)  # 👈 sort after merge
    )


    # st.write(result)

    return result, df_accessories
