import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode
from pathlib import Path, PureWindowsPath    # for Window & Mac OS path-slash '\' or '/'
import os
from datetime import date
from datetime import datetime, timedelta
import calendar
import numpy as np
import scdat_utils_26 as utils
from scdat_colors_26 import color_hex
import scdat_data_26 as data


def get_scan_data(datafile_location):
    # create dataframe from Inventory Physical Count Sheet

    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Inventory_Physical_Count.xlsx"))
    df = pd.read_excel(file_path, sheet_name='Form Responses 2', header=0)
    df = df[['Timestamp', 'Location (SCAN)', 'Barcode (SCAN)', 'Qty']]
    df.columns = (['Scan Date', 'Location', 'Barcode', 'Qty'])

    # remove leading and trailing spaces and covert to Uppercase ======================
    df['Barcode'] = df.apply(lambda x: str(x.iloc[2]).strip().upper(), axis=1)
    df['Barcode'] = df.apply(lambda x: str(x.iloc[2]).replace(" ", ""), axis=1)     # remove space between words

    df['Location'] = df.apply(lambda x: str(x.iloc[1]).strip().upper(), axis=1)
    df = df[df["Location"] != '']

    # convert scan date to date format
    df['Scan Date'] = pd.to_datetime(df['Scan Date']).dt.date

    # create dataframe of barcodes ======================================
    file_path = Path(PureWindowsPath(datafile_location + "Inventory\\Inventory_Physical_Count.xlsx"))
    df_barcode = pd.read_excel(file_path, sheet_name='codes', header=0)
    df_barcode = df_barcode[['Code', 'SKU']]

    df_barcode.columns = (['Barcode', 'SKU'])
    df_barcode = df_barcode.applymap(str)
    df_barcode['Barcode'] = df_barcode.apply(lambda x: x.iloc[0].upper().strip(), axis=1)
    df_barcode['SKU'] = df_barcode.apply(lambda x: x.iloc[1].upper().strip(), axis=1)
    df_barcode['SKU'] = df_barcode.apply(lambda x: x.iloc[1].upper().strip(), axis=1)
    df_barcode = df_barcode.drop_duplicates(subset=['Barcode'], keep='first')

    df_scan = pd.merge(df, df_barcode, on=["Barcode"], how='left')
    df_scan = df_scan.fillna('VOID')
    df_scan = df_scan[df_scan["SKU"] != 'VOID']
    df_scan = df_scan.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df_scan = df_scan.loc[lambda row: ~ row['SKU'].str.startswith('RBX')]

    return df_scan


def scan_data_wh_filter(df, wh):

    df_wh = pd.DataFrame({})    # empty dataframe

    x = ''
    if wh == 'WH1':
        x = ['P', 'Q', 'P-RE']

    elif wh == 'WH2':
        x = ['G', 'H', 'F-']

    elif wh == 'WH3':
        x = ['T', 'T-F']

    elif wh == 'WH4':
        x = ['J', 'K', 'L-']

    for i in range(0, len(x)):
        df_temp = df.loc[lambda row: row['Location'].str.startswith(x[i])]
        df_wh = pd.concat([df_wh, df_temp])

    df_wh.columns = (['SCAN DATE', 'LOCATION', 'BARCODE', 'QTY', 'SKU'])    # change header to uppercase

    # st.write(df_wh)
    # st.stop()

    return df_wh


def get_zen_inventory(datafile_location, wh):
    # get warehouse-wise inventory
    get_df = data.wh_wise_inventory_df(datafile_location)

    if wh == 'WH1':
        df = get_df[1]

    elif wh == 'WH2':
        df = get_df[2]

    elif wh == 'WH4':
        df = get_df[4]

    df = df[['SKU', 'LOCATION', 'QTY']]

    # if wh == 'WH2':
    #     # df['LOCATION'] = df.apply(lambda x: str(x.iloc[1])[18:len(x.iloc[1])], axis=1)  # remove 'WH1/Stock/Houston/' from location
    #     df['LOCATION'] = df.apply(lambda x: str(x.iloc[1]).rsplit('/', 1)[-1], axis=1)  # get text only after last '/'
    #
    # else:
    #     # df['LOCATION'] = df.apply(lambda x: str(x.iloc[1])[17:len(x.iloc[1])], axis=1)  # remove 'WH1/Stock/Austin/' from location

    df['LOCATION'] = df.apply(lambda x: str(x.iloc[1]).rsplit('/', 1)[-1], axis=1)  # get text only after last '...../G11J1'

    df = df.sort_values(['LOCATION', 'SKU'], ascending=[True, True])
    df.reset_index(drop=True, inplace=True)
    df.index = range(1, df.shape[0] + 1)

    return df


def display_recount_list(datafile_location):
    wh = st.sidebar.selectbox("WAREHOUSE", ['WH1', 'WH2', 'WH3', 'WH4'])
    location = st.sidebar.text_input('LOCATION', 'ALL')

    title_text = wh + " - Inventory Count"
    st.markdown(f"""<div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-45px;">
                                {title_text}
                            </div>
                            <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
                            """, unsafe_allow_html=True)

    start_date = date.today() - timedelta(days=1)
    end_date = date.today()

    start_date = st.sidebar.date_input("START DATE", start_date)
    end_date = st.sidebar.date_input("END DATE", end_date)

    df = get_scan_data(datafile_location)

    # df = df[df['Scan Date'] >= pd.to_datetime(start_date)]
    # df = df[df['Scan Date'] <= pd.to_datetime(end_date)]

    df = df[df['Scan Date'] >= start_date]
    df = df[df['Scan Date'] <= end_date]

    if len(df) == 0:
        st.warning('Scan Data for date range not found. Please select date range')
        return

    df_scan_by_wh = scan_data_wh_filter(df, wh)     # get scan inventory as per selected warehouse

    if len(df_scan_by_wh) == 0:
        st.warning('Scan Data for ' + wh + ' not found. Please select warehouse')
        return

    if location.upper() != 'ALL':
        df_scan = df_scan_by_wh.loc[lambda row: row['LOCATION'].str.startswith(location.upper())].copy()
    else:
        df_scan = df_scan_by_wh.copy()

    col1, col2, col3 = st.columns([2, 1.5, 0.5])

    if location.upper() != 'ALL':
        df_scan1 = df_scan.loc[lambda row: row['LOCATION'].str.startswith(location.upper())].copy()
    else:
        df_scan1 = df_scan.copy()

    df_scan1 = df_scan1.sort_values(['LOCATION', 'SKU'], ascending=[True, True])

    # consolidate data if location and sku are same in the scan file <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    df_consolidated = df_scan1.groupby(['LOCATION', 'SKU'])['QTY'].sum().to_frame().reset_index()
    df_consolidated = df_consolidated.sort_values(['LOCATION', 'SKU'], ascending=[True, True])
    df_consolidated.reset_index(drop=True, inplace=True)
    df_consolidated.index = range(1, df_consolidated.shape[0] + 1)

    with col1:  # display scan data =======================================

        header_txt1 = 'SCAN LOCATIONS: ' + str(len(df_scan1.drop_duplicates(subset=['LOCATION'], keep='first'))) + ' | SCAN QTY: ' +\
                      str(utils.format_num(df_scan1['QTY'].sum()))
        header_txt2 = ' | CONSOLIDATED RECORDS: ' + str(len(df_consolidated)) + ' & QTY: ' + str(utils.format_num(df_consolidated['QTY'].sum()))

        header_txt = header_txt1 + header_txt2
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; line-height:0em;'
            f' margin-top:5px">{header_txt}</p>', unsafe_allow_html=True)

        df_scan1['SCAN DATE'] = pd.to_datetime(df_scan1['SCAN DATE'])
        df_scan1['SCAN DATE'] = df_scan1['SCAN DATE'].dt.strftime('%Y-%m-%d')  # convert str to date format

        AgGrid(df_scan1, height=330, fit_columns_on_grid_load=True)
        utils.download_csv(df_scan1, 'Download Scan Records')

    with col2:  # display ZEN data =======================================

        df_zen = get_zen_inventory(datafile_location, wh)

        header_txt = wh + ' | ZEN LOCATIONS | ' + str(len(df_zen.drop_duplicates(subset=['LOCATION'], keep='first'))) + ' | ZEN QTY | ' + str(
            utils.format_num(df_zen['QTY'].sum()))

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; line-height:0em;'
            f' margin-top:5px">{header_txt}</p>', unsafe_allow_html=True)

        AgGrid(df_zen, height=330, fit_columns_on_grid_load=True)
        utils.download_csv(df_zen, 'Download ZEN Records' )

    with col1:  # display ZEN Qty, Scan Qty & difference (Scan - ZEN) ===============================

        df_join = pd.merge(df_zen, df_consolidated, left_on=['LOCATION', 'SKU'], right_on=['LOCATION', 'SKU'], how='outer')

        df_join = df_join[['LOCATION', 'SKU', 'QTY_x', 'QTY_y']]
        df_join.columns = (['LOCATION', 'SKU', 'ZEN QTY', 'SCAN QTY'])

        df_join['ZEN QTY'] = df_join['ZEN QTY'].fillna(0)
        df_join['SCAN QTY'] = df_join['SCAN QTY'].fillna(0)

        df_join['DIFFERENCE'] = df_join['SCAN QTY'] - df_join['ZEN QTY']

        df_join = df_join.sort_values(['LOCATION', 'SKU'], ascending=True)
        df_join.reset_index(drop=True, inplace=True)
        df_join.index = range(1, df_join.shape[0] + 1)

        header_txt1 = 'LOCATIONS: ' + str(len(df_join.drop_duplicates(subset=['LOCATION'], keep='first')))
        header_txt2 = ' | SCAN QTY: ' + str(utils.format_num(df_join['SCAN QTY'].sum())) + '| ZEN QTY: '
        header_txt3 = str(utils.format_num(df_join['ZEN QTY'].sum())) + ' | DIFFERENCE (SCAN - ZEN ): ' + str(utils.format_num(df_join['DIFFERENCE'].sum()))

        header_txt = header_txt1 + header_txt2 + header_txt3

        st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                f'line-height:0em;">'
                f' {header_txt}</p>', unsafe_allow_html=True)

        AgGrid(df_join, height=330, fit_columns_on_grid_load=True)

        utils.download_csv(df_join, 'Download Difference File')

    with col2:      # display list with difference <> 0 ==========================

        df_join = df_join[df_join['DIFFERENCE'] != 0]

        df_join = df_join.sort_values(['LOCATION', 'SKU'], ascending=True)
        df_join.reset_index(drop=True, inplace=True)
        df_join.index = range(1, df_join.shape[0] + 1)

        header_txt1 = 'RECOUNT LIST | DIFF. <> 0 | ' + 'LOCATIONS: ' + str(len(df_join.drop_duplicates(subset=['LOCATION'], keep='first')))
        header_txt2 = header_txt1 + ' | DIFFERENCE: ' + str(utils.format_num(df_join['DIFFERENCE'].sum()))
        header_txt = header_txt2    # + ' | ZERO LOCATIONS: ' + str(len(df_zero.drop_duplicates(subset=['LOCATION'], keep='first')))

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; line-height:0em;">'
            f' {header_txt}</p>', unsafe_allow_html=True)

        df_join = df_join[['LOCATION', 'SKU', 'ZEN QTY', 'SCAN QTY', 'DIFFERENCE']]
        AgGrid(df_join, height=330, fit_columns_on_grid_load=True)

        utils.download_csv(df_join, 'Download Recount File')

    return


def display_final_inventory(df, index):

    if index == 2 or index == 3 or index == 4:
        df = df[['LOCATION', 'SKU', 'ZEN QTY', 'COUNT1', 'COUNT2']]
        df['INVENTORY'] = df['COUNT2']
        txt1 = '[' + str(index) + '] Inventory Data | Total Record: ' + str(len(df)) + ' | ZEN Total: ' + str(df['ZEN QTY'].sum())
        txt1 = txt1 + ' | Count-2 Total: ' + str(df['COUNT2'].sum()) + ' | Inventory Total: ' + str(df['INVENTORY'].sum())
        #
        st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                     f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

    AgGrid(df, height=330, fit_columns_on_grid_load=True)
    utils.download_csv(df, 'Download Inventory List')

    return


def display_recount_analysis():
    title_text = "Inventory Count - 3rd Count List"
    st.markdown(f"""<div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-45px;">
                                    {title_text}
                                </div>
                                <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
                                """, unsafe_allow_html=True)

    warehouse = 'WH2'
    warehouse = st.sidebar.text_input("Warehouse ...", value=warehouse)

    file_location = "G:\\My Drive\\STREAMLIT\\Meeting@Desktop\\Inventory Count\\"
    file_path1 = "2026\\01_Jan-2026\\" + warehouse + "\\"  # <<<<<<<<<<<<<<<<<<<

    recount_date = '01.30'
    recount_date = st.sidebar.text_input("Inventory Count Date ...", value=recount_date)


    file_name = warehouse + "_Recount_Data-" + recount_date + ".xlsx"   # <<<<<<<<<<<<<<<<<<<

    # file_path = file_location + "2025\\09_Sep-2025\\WH4\\WH4_Count3_Data-09.25.xlsx"  # <<<<<<<<<<<<<<<<<<<<

    file_path1 = st.sidebar.text_input("File Path ..", value=file_path1)
    file_name = st.sidebar.text_input("Recount Data File Name ...", value=file_name)

    file_path = file_location + file_path1 + file_name

    file_path = Path(PureWindowsPath(file_location + file_path))

    # st.sidebar.write(file_path)

    df1 = pd.read_excel(file_path, sheet_name='Jafar_Data', header=0)
    df1 = df1[['LOCATION', 'SKU', 'ZEN QTY', 'COUNT1', 'COUNT2']]
    df1 = df1[df1['LOCATION'] != 'TOTAL']
    df1 = df1.sort_values('LOCATION', ascending=True)

    col1, col2 = st.columns(2)
    with col1:  # show ZEN, Count1 and Count2 data ======================================
        txt1 = '[1] Recount Data | Total Record: ' + str(len(df1)) + ' | ZEN Total: ' + str(df1['ZEN QTY'].sum())
        txt1 = txt1 + ' | Count-1 Total: ' + str(df1['COUNT1'].sum()) + ' | Count-2 Total: ' + str(df1['COUNT2'].sum())

        st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                    f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

        AgGrid(df1, height=330, fit_columns_on_grid_load=True)
        utils.download_csv(df1, 'Download Data')

    with col2:  # show (ZEN - COUNT2) <> 0 data ======================================

        df1['DIFFERENCE2'] = df1['ZEN QTY'] - df1['COUNT2']
        df2 = df1[df1['DIFFERENCE2'] != 0]

        if len(df2) > 0:

            txt1 = '[2] Recount Data (ZEN - Count2) <> 0 | Total Record: ' + str(len(df2)) + ' | Record Difference: ' + str(len(df1) - len(df2))

            st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                    f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

            AgGrid(df2, height=330, fit_columns_on_grid_load=True)
            utils.download_csv(df2, 'Download Data')

        else:
            display_final_inventory(df1, 2)
            return

    with col1:  # show (COUNT1 - COUNT2) <> 0 data ======================================

        df2['COUNT1-2 DIFF'] = df2['COUNT1'] - df2['COUNT2']
        df3 = df2[df2['COUNT1-2 DIFF'] != 0]

        if len(df3) > 0:

            df3 = df3[['LOCATION', 'SKU', 'ZEN QTY', 'COUNT1', 'COUNT2', 'COUNT1-2 DIFF']]

            txt1 = '[3] Recount Data (Count1 - Count2) <> 0 | Total Record: ' + str(len(df3)) + ' | Record Difference: ' + str(len(df2) - len(df3))

            st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                    f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

            AgGrid(df3, height=330, fit_columns_on_grid_load=True)
            utils.download_csv(df3, 'Download Data')

        else:
            display_final_inventory(df2, 3)
            return
#
    with col2:  # show (ZEN TOTAL - COUNT2 TOTAL) <> 0 =======================================

        n = st.sidebar.number_input("Total Inventory Error Filter", min_value=0, max_value=5, value=1, step=1)

        df4 = df3.groupby('SKU').aggregate({'ZEN QTY': 'sum', 'COUNT2': 'sum'}).reset_index()
        df4 = df4.rename(columns={'ZEN QTY': 'TOTAL ZEN', 'COUNT2': 'TOTAL COUNT2'})
        df4['TOTAL DIFF'] = df4['TOTAL ZEN'] - df4['TOTAL COUNT2']
        df4 = df4[(df4['TOTAL DIFF'] < -n) | (df4['TOTAL DIFF'] > n)]

        if len(df4) > 0:
            txt1 = '[4] Recount Data (Total ZEN - Total Count2) <> +/- ' + str(n) + ' | Total SKU: ' + str(len(df4))

            st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                      f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

            AgGrid(df4, height=330, fit_columns_on_grid_load=True)
            utils.download_csv(df4, 'Download Data')

        else:
            display_final_inventory(df3, 4)
            return

    with col1:  # show count3 list =================================================

        if len(df4) > 0:
            sku_list = df4['SKU'].tolist()

            df5 = df3[df3['SKU'].isin(sku_list)]
            df5 = df5[['LOCATION', 'SKU', 'ZEN QTY', 'COUNT1', 'COUNT2']]
            # st.write(df5)
            # st.stop()

            txt1 = '[5] Count 3 List | Total Record: ' + str(len(df5))
            st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                        f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

            AgGrid(df5, height=330, fit_columns_on_grid_load=True)
            utils.download_csv(df5, 'Download Count3 List')

    with col2: # get count3 data =======================================================
        file_name3 = warehouse + "_Count3_Data-" + recount_date + ".xlsx"
        file_name3 = st.sidebar.text_input("3rd Count Data File Name ...", value=file_name3)

        file_path3 = file_location + file_path1 + file_name3

        file_path = Path(PureWindowsPath(file_path3))

        df6 = pd.read_excel(file_path, sheet_name='Jafar_Data', header=0)
        df6 = df6[['LOCATION', 'SKU', 'COUNT3']]

        df6 = df6.sort_values('LOCATION', ascending=True)

        txt1 = '[6] Count 3 Data | Total Record: ' + str(len(df6))
        st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                    f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)
        AgGrid(df6, height=330, fit_columns_on_grid_load=True)
        utils.download_csv(df6, 'Download Count3 Data')

    with col1:  # merge the count3 file df2 = (ZEN - count2) <> 0 ====================================

        df7 = pd.merge(df2, df6, on=['LOCATION', 'SKU'], how='outer')
        df7 = df7[['LOCATION', 'SKU', 'ZEN QTY', 'COUNT1', 'COUNT2', 'COUNT3']]

        df7 = df7.fillna('')

        df7['INVENTORY'] = df7.apply(lambda x: (x[4] if x[5] == '' else x[5]), axis=1)

        # st.write(df7)

        txt1 = '[7] Inventory Data | Total Record: ' + str(len(df7)) + ' | ZEN Total: ' + str(df7['ZEN QTY'].sum())
        txt1 = txt1 + ' | Count-2 Total: ' + str(df7['COUNT2'].sum()) + ' | Inventory Total: ' + str(df7['INVENTORY'].sum())

        st.markdown(f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 16px ;border-radius:2%; '
                    f'line-height:0em; margin-top:5px">{txt1}</p>', unsafe_allow_html=True)

        AgGrid(df7, height=330, fit_columns_on_grid_load=True)
        utils.download_csv(df7, 'Download Inventory List')

    return
