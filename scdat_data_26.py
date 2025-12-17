import pandas as pd
from pathlib import Path, PureWindowsPath    # << for Window & Mac OS path-slash '\' or '/'
import os

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
import calendar
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

    df = df.map(str)  # convert entire df to string for Streamlit
    return df

def container_df(datafile_location):
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Container.csv"))
    df = pd.read_csv(file_path)

    df = df[['Container No.', 'Master Bill Of Lading', 'Estimated At Port Date', 'State', 'Container Lines/Product SKU',
             'Container Lines/Qty To Load', 'Latest Updates']]

    # change column name
    df.columns = (['PO', 'BOL', 'ODDO_ETA', 'STATE', 'SKU', 'QTY', 'RECEIVED DATE'])

    # remove space from SKU
    df['SKU'] = df['SKU'].str.strip()

    # convert space to blank and copy the value from above row (if blank)
    df['PO'] = df['PO'].replace(r'^\s*$', pd.NA, regex=True)
    # df['PO'] = df['PO'].fillna(method='ffill')    # method deprecated <<<<<<<<<<<<<
    df['PO'] = df['PO'].ffill()     # use method forward fill

    # st.write(df)
    # st.stop()

    df['BOL'] = df['BOL'].replace(r'^\s*$', pd.NA, regex=True)
    # df['BOL'] = df['BOL'].fillna(method='ffill')
    df['BOL'] = df['BOL'].ffill()

    df['ODDO_ETA'] = df['ODDO_ETA'].replace(r'^\s*$', pd.NA, regex=True)
    # df['ODDO_ETA'] = df['ODDO_ETA'].fillna(method='ffill')
    df['ODDO_ETA'] = df['ODDO_ETA'].ffill()

    df['STATE'] = df['STATE'].replace(r'^\s*$', pd.NA, regex=True)
    # df['STATE'] = df['STATE'].fillna(method='ffill')
    df['STATE'] = df['STATE'].ffill()

    df['RECEIVED DATE'] = df['RECEIVED DATE'].replace(r'^\s*$', pd.NA, regex=True)
    df['RECEIVED DATE'] = df['RECEIVED DATE'].ffill()

    # get rows where 'PO' not (~) starts with '0-' , 'Test' or 'test'
    df = df.loc[lambda row: ~ row['PO'].str.startswith('0-')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('T')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('t')]

    # remove unwanted rows --------------------------------------------------
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2188HM-C')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2188HM-INCORRECT')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2204HM - CANCEL')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2205MM - CANCEL')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2206HM - CANNOT RECEIVE')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2241HM - CANNOT RECEIVE')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2241HM - CANCEL')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2353 - CANCEL')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2603FC - Cancel')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2588HM-CANCEL')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('2660RBX')]
    df = df.loc[lambda row: ~ row['PO'].str.startswith('Huayi Sample')]

    df = df[df['SKU'] != 'RVH7417 - DO NOT USE']
    df = df[df['SKU'] != 'RVH8071 - DO NOT USE']
    df = df[df['SKU'] != 'RVH8118 - DO NOT USE']
    df = df[df['SKU'] != 'RVH8277 - DO NOT USE']
    df = df[df['SKU'] != 'RVH8341 [DO NOT USE]']
    df = df[df['SKU'] != 'RVH8359 - DO NOT USE']
    df = df[df['SKU'] != 'RVL2398BK - DO NOT USE']
    df = df[df['SKU'] != 'RVL2398WH - DO NOT USE']

    df = df[df['SKU'].notna()]  # keep only rows where SKU is not null.

    df['ODDO_ETA'] = pd.to_datetime(df['ODDO_ETA'])
    df['ODDO_ETA'] = df['ODDO_ETA'].dt.date

    df['RECEIVED DATE'] = df['RECEIVED DATE'].str[:10]
    df['RECEIVED DATE'] = pd.to_datetime(df['RECEIVED DATE'])
    df['RECEIVED DATE'] = df['RECEIVED DATE'].dt.date

    df = df.sort_values('PO', ascending=True)

    return df

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

    df_inventory = df_inventory.fillna('BLANK')  # replace the empty cell with 'BLANK'
    df_inventory = df_inventory[df_inventory['SKU'] != 'BLANK']

    df_inventory['SKU'] = df_inventory.apply(lambda x: x.iloc[0].strip(), axis=1)

    df_inventory = df_inventory.fillna('VOID')

    # remove the SKU that does not start with RV
    df_inventory = df_inventory.loc[lambda row: row['SKU'].str.startswith('RV')]

    df_product = product_df(datafile_location)

    df = pd.merge(df_product, df_inventory, on=["SKU"], how='left')

    df = df.sort_values('SKU', ascending=True)

    return df


def sc_summary_container_df_OLD(datafile_location, df_ccs1, supplier):

    # ----------------- filter df_CCS for incoming containers only ---------------------------------------
    df_ccs = df_ccs1[df_ccs1['Delivered Date'] == 'BLANK']
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

    # st.write(df)
    # st.write(df_summary)
    # st.stop()

    return df, df_summary


def inocean_container_df_OLD(datafile_location, df):

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

def sales_trend_df(datafile_location, supplier, model, number_of_months_in_display):
    # read all sales file and create df based on number_of_months_in_display

    # get list of monthly sales file and sort ==============================
    path1 = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY'
    source_files1 = os.listdir(Path(PureWindowsPath(path1)))
    source_files1.sort()

    start_index = len(source_files1) - number_of_months_in_display - 1  # Start from previous month

    df_sales = pd.DataFrame({})

    for i in range(start_index, len(source_files1)):  # end at previous month

        file_name = str(source_files1[i])  # get file name
        s = file_name.split('_')  # split file name based on '_'
        month_name = s[2][:-4]  # get last portion and remove .csv

        path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY\\' + source_files1[i]

        df = pd.read_csv(Path(PureWindowsPath(path)))
        df = df[['SKU', 'SUPPLIER', 'AMAZON', 'ODDO', 'TOTAL']]

        df = utils.supplier_model_query(df, supplier, model)    # query on supplier & model / color

        df['MONTH'] = month_name

        if i == start_index:
            df_sales = df

        else:
            df_sales = pd.concat([df_sales, df])

    # st.write(df_sales) <<<<<<<<<<<<<<<<<<< need to add all month if data are not available <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # st.stop()

    df_sink = df_sales.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # <<<<<<<<<< REMOVE RVA

    df_summary = df_sink.groupby('MONTH')['TOTAL'].sum().to_frame().reset_index()
    df_summary = df_summary.rename(columns={'TOTAL': 'SALES'})

    month_names = df_summary['MONTH'].tolist()
    month_names = sorted(month_names, key=lambda x: datetime.strptime(x, "%b-%y"))      # sort month names list

    df_summary['MONTH'] = pd.Categorical(df_summary['MONTH'], categories=month_names, ordered=True)     # sort dataframe as per the list
    df_summary = df_summary.sort_values('MONTH')

    df_summary = df_summary.iloc[:-1]   # remove current month

    return df_summary, df_sales

def forecast_trend_df(datafile_location, supplier, model, month_names):

    df_forecast = pd.DataFrame({})

    for i in range(0, len(month_names)):

        month_name = month_names[i]
        year = '20' + month_name[-2:]       # like year 2025

        month_no = datetime.strptime(month_name[:3], "%b").month    # get month number from short name 'Jan'

        month_no = f"{int(month_no):02}"    # convert month number to 2-digit '01'

        forecast_month = month_no + '_' + month_name[:3] + '-' + year   # create forecast month '11_Nov-2025'

        path = datafile_location + 'Projection\\' + year + '\\' + forecast_month + '\\'

        # st.write(path)
        source_files = os.listdir(Path(PureWindowsPath(path)))
        source_files.sort()

        if supplier.upper() == 'ALL':
            st.write('Supplier == ALL')
            st.stop()

        elif supplier == 'Speed':

            forecast_file = [f for f in source_files if supplier.upper() in f]
            forecast_file = [f for f in forecast_file if 'SPEED VIETNAM' not in f]      # remove from list
            forecast_file = [f for f in forecast_file if 'SPEED_RVA' not in f]      # remove from list

        else:

            forecast_file = [f for f in source_files if supplier.upper() in f]

            st.write(forecast_file)

        file_path = datafile_location + 'Projection\\' + year + '\\' + forecast_month + '\\' + forecast_file[0]
        df = pd.read_excel(Path(PureWindowsPath(file_path)), sheet_name='Jafar_Data', header=1)

        df = df.iloc[:, [0, 8]]     # take FORECAST column only
        df = df.rename(columns={'FORECAST': month_name})

        if i == 0:
            df_forecast = df

        else:
            df_forecast = pd.merge(df_forecast, df, on=["SKU"], how='outer')

    df_forecast['SUPPLIER'] = supplier      # add supplier name
    df_forecast = utils.supplier_model_query(df_forecast, supplier, model)    # query on supplier & model / color

    df_sink = df_forecast.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]  # <<<<<<<<<< REMOVE RVA <<<<<<<<<<<<<<


    value1 = 'TOTAL'
    df_sink = df_sink[~ df_sink['SKU'].str.contains(value1.upper(), case=False, na=False)]  # remove TOTAL row, if any

    totals = df_sink[month_names].select_dtypes(include='number').sum()     # Calculate totals only for numeric columns

    totals['SKU'] = 'FORECAST'

    df_sink = pd.concat([df_sink, pd.DataFrame([totals])], ignore_index=True)   # append total row at the bottom

    df_sink = df_sink.iloc[[-1]].reset_index(drop=True)     # keep Total row only

    df_sink = df_sink.drop('SUPPLIER', axis=1)  # drop column supplier

    df_sink = df_sink.T     # transpose

    df_sink.columns = df_sink.iloc[0]   # first row as header

    df_sink = df_sink[1:].reset_index()

    df_sink = df_sink.rename(columns={'index': 'MONTH'})

    # st.write(df_forecast)
    # st.stop()

    return df_sink, df_forecast


def loading_trend_df(datafile_location, supplier, model, month_names):
    df_container = container_df(datafile_location)      # get container data ===================================

    df_container = df_container[['SKU', 'QTY', 'PO', 'STATE', 'RECEIVED DATE']]
    df_container['PO'] = df_container['PO'].str[:4]      # get only first 4 digit of PO

    df_ccs = ccs_df(datafile_location)      # get CCS data =====================================================
    df_ccs = df_ccs[df_ccs["Loading Date"] != 'BLANK']
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date']]
    df_ccs = df_ccs.rename(columns={'CONTAINER NO.': 'PO', 'FROM': 'SUPPLIER', 'Loading Date': 'LOADING DATE'})

    df_ccs['LOADING DATE'] = pd.to_datetime(df_ccs['LOADING DATE'])
    df_ccs['LOADING DATE'] = df_ccs['LOADING DATE'].dt.date     # remove timestamp

    df = pd.merge(df_container, df_ccs, on=["PO"], how='left')
    df = df[['PO', 'SUPPLIER', 'SKU', 'QTY', 'LOADING DATE', 'RECEIVED DATE', 'STATE']]

    df = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # remove accessories
    df = df.loc[lambda row: ~ row['SKU'].str.startswith('RBX')]     # remove packing boxes

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

    # st.write(df_container)
    # st.write(df_ccs)
    # st.write(df)
    # st.write(df_received)
    # st.write(df_loading)
    # st.stop()   # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #
    # # MONTH, LOADING
    # # df1 = container_plus_ccs_df(datafile_location)
    # df1 = df1.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    # df1 = df1.loc[lambda row: ~ row['SKU'].str.startswith('RBX')]   # empty boxes
    #
    # df_loading = df1
    #
    # # 5 = 'LOADING DATE'
    # # st.write(df_loading)
    # df_loading['LOADING MONTH'] = df_loading.apply(lambda x: str(x.iloc[5])[0:7], axis=1)
    #
    # #st.write(df_loading)
    #
    # df_received = df1[df1['STATE'] == 'Received In Warehouse'].copy()
    #
    # # 6 = 'RECEIVED DATE'
    # df_received['RECEIVED MONTH'] = df_received.apply(lambda x: str(x.iloc[6])[0:7], axis=1)
    #
    # # st.write(df_received)
    #
    # loading = []
    # received = []
    # container_loading = []
    # container_received = []
    #
    # for i in range(0, len(month_names)):
    #
    #     month_name = month_names[i]
    #     year = '20' + month_name[-2:]
    #
    #     month_no = datetime.datetime.strptime(month_name[:3], "%b").month
    #
    #     if month_no < 10:
    #         month_no = '0' + str(month_no)
    #     else:
    #         month_no = str(month_no)
    #
    #     year_month = year + '-' + month_no
    #
    #     df_monthly_loading = df_loading[df_loading['LOADING MONTH'] == year_month].copy()
    #     df_monthly_received = df_received[df_received['RECEIVED MONTH'] == year_month].copy()
    #
    #     #st.write(df)
    #     # st.stop()
    #
    #     if model.upper() != 'ALL':
    #         df_monthly_loading = df_monthly_loading[df_monthly_loading['SKU'] == model.upper()]
    #         df_monthly_received = df_monthly_received[df_monthly_received['SKU'] == model.upper()]
    #
    #     if supplier != 'ALL' and supplier != 'Speed':
    #
    #         if len(df_monthly_loading) > 0:
    #             df_monthly_loading = df_monthly_loading[df_monthly_loading['SUPPLIER'] == supplier].copy()
    #
    #         if len(df_monthly_received) > 0:
    #             df_monthly_received = df_monthly_received[df_monthly_received['SUPPLIER'] == supplier].copy()
    #
    #     if supplier == 'Speed':
    #         df_monthly_loading = df_monthly_loading[(df_monthly_loading['SUPPLIER'] == 'Speed') | (df_monthly_loading['SUPPLIER'] == 'Speed (Vietta)')]
    #         df_monthly_received = df_monthly_received[(df_monthly_received['SUPPLIER'] == 'Speed') | (df_monthly_received['SUPPLIER'] == 'Speed (Vietta)')]
    #
    #     total_loading = df_monthly_loading['QTY'].sum()
    #     total_received = df_monthly_received['QTY'].sum()
    #     loading.append(total_loading)
    #     received.append(total_received)
    #
    #     df_container_loading = df_monthly_loading.drop_duplicates(subset=['PO'], keep='first')
    #     total_container_loading = df_container_loading['PO'].count()
    #     container_loading.append(total_container_loading)
    #
    #     df_container_received = df_monthly_received.drop_duplicates(subset=['PO'], keep='first')
    #     total_container_received = df_container_received['PO'].count()
    #     container_received.append(total_container_received)
    #
    # df = pd.DataFrame({'MONTH': month_names,
    #                    'LOADING': loading,
    #                    'RECEIVED': received,
    #                    'CONTAINER (L)': container_loading,
    #                    'CONTAINER (R)': container_received,
    #                    })
    # st.write(df)
    return df_loading, df_received


def forecast_df(datafile_location, forecast_month):
    # read all Projection files and create a df as per forecast month
    y = forecast_month.split('-')
    year = y[1]

    path = datafile_location + 'Projection\\' + year + '\\' + forecast_month + '\\'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort()

    new_source_files = []
    for i in range(0, len(source_files)):
        if source_files[i][0:1] == '0' or source_files[i][0:1] == '1':
            new_source_files.append(source_files[i])

    df_forecast = pd.DataFrame({})

    for j in range(0, len(new_source_files)):
        file_path = datafile_location + 'Projection\\' + year + '\\' + forecast_month + '\\' + str(new_source_files[j])

        s = file_path.split('_')
        supplier = s[3]

        df = pd.read_excel(Path(PureWindowsPath(file_path)), sheet_name='Jafar_Data', header=1)

        df = df.iloc[:, :9]     # get first 9 columns only

        value1 = 'TOTAL'
        df = df[~ df['SKU'].str.contains(value1.upper(), case=False, na=False)]  # remove TOTAL row, if any

        value2 = 'SINK ONLY'
        df = df[~ df['SKU'].str.contains(value2.upper(), case=False, na=False)]  # remove SINK ONLY row, if any

        df['SUPPLIER'] = supplier
        df['MONTH'] = forecast_month[3:6] + '-' + forecast_month[-2:]


        if j == 0:
            df_forecast = df

        else:
            df_forecast = pd.concat([df_forecast, df])      # append all suppliers forecast


    df_forecast = df_forecast[df_forecast['FORECAST'] != 0]

    # st.write(df_forecast)
    # st.stop()

    return df_forecast

