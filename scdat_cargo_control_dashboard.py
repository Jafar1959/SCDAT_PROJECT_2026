import streamlit as st
import pandas as pd
from datetime import datetime
from datetime import date, timedelta
import time
from st_aggrid import GridOptionsBuilder, AgGrid
import numpy as np


from scdat_colors_26 import color_hex
import scdat_utils_26 as utils
import scdat_figures_26 as fg
import scdat_data_26 as data

def dashboard_container_loading(datafile_location):
    start = time.perf_counter()     # start runtime counter

    utils.show_header('Container Loading')

    with st.spinner('Loading...'):  # show spinner

        col1, col2, col3 = st.columns([4.1, 0.8, 0.1])

        with col2:  # display monthly container loading =================================
            values = fg.monthly_container_loading(datafile_location)
            fig1 = values[0]    # YTD Container Loading
            container_this_year = values[1]     # YTD Total Containers Loaded

            container_per_month = round(container_this_year/utils.get_month_elapsed(), 1)   # Average Containers per Month

            txt = str(datetime.today().year) + ' | YTD Container Loading'
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 18px ;border-radius:1%;'
                f' line-height:0em; margin-top:-5px"> {txt} </p>', unsafe_allow_html=True)

            st.plotly_chart(fig1, width='stretch')

            txt2 = 'Months Elapsed = ' + str(round(utils.get_month_elapsed(), 2))

            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
                f' line-height:0em; margin-top:-5px"> {txt2} </p>',  unsafe_allow_html=True)

            #st.write('Months Elapsed = ' + str(round(utils.get_month_elapsed(), 2)))

        with col1:      # display container loading and receiving status for 5-months =======================================
            txt = 'Incoming Container Details | YTD Total Containers: ' + str(container_this_year) + ' (' +str(container_per_month) + '/month) ' +\
                  ' | ' + utils.get_todays_date()
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
                f' line-height:0em; margin-top:-5px">{txt}</p>', unsafe_allow_html=True)

            fig = fg.container_dashboard(datafile_location)
            st.plotly_chart(fig, width='stretch')

        end = time.perf_counter()   # stop runtime counter
        st.sidebar.write(f"Runtime: {end - start:.2f} seconds")     # show runtime seconds

    return

def dashboard_container_received(datafile_location):
    start = time.perf_counter()  # start runtime counter

    utils.show_header(' Container Received')

    start_date = datetime.today().date() - timedelta(days=5)    # start_date = today - 5 days

    date1 = st.sidebar.date_input("CONTAINER RECEIVED AFTER", start_date)

    # ================= get CCS Container Received Info =================================
    df_ccs = data.ccs_df(datafile_location)
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'MTS File Ref', 'Delivered Date']]
    df_ccs.columns = (['CONTAINER', 'FROM', 'BOL', 'DELIVERY DATE'])    # rename columns

    df_ccs = df_ccs[df_ccs["DELIVERY DATE"] != "BLANK"]     # keep only received containers
    df_ccs['DELIVERY DATE'] = pd.to_datetime(df_ccs['DELIVERY DATE']).dt.date

    df_ccs = df_ccs[df_ccs["DELIVERY DATE"] >= date1]       # filter by start date

    df_ccs = df_ccs.sort_values('CONTAINER', ascending=True)
    df_ccs.reset_index(drop=True, inplace=True)
    df_ccs.index = range(1, df_ccs.shape[0] + 1)

    # st.write(df_ccs)

    # ================= get ZEN Container Received Info =================================
    df_zen = data.container_df(datafile_location)

    df_zen = df_zen[['PO', 'BOL', 'STATE', 'RECEIVED DATE', 'LOCATION']]
    df_zen = df_zen[df_zen['STATE'] == 'Received In Warehouse']     # keep only received containers

    df_zen = df_zen.drop_duplicates(subset=['PO'], keep='first')
    df_zen = df_zen[['PO', 'BOL', 'RECEIVED DATE', 'LOCATION']]

    df_zen = df_zen.rename(columns={'PO': 'CONTAINER'})

    df_zen = df_zen[df_zen["RECEIVED DATE"] >= date1]

    df_zen = df_zen.sort_values('CONTAINER', ascending=True)
    df_zen.reset_index(drop=True, inplace=True)
    df_zen.index = range(1, df_zen.shape[0] + 1)

    with st.spinner('Loading...'):

        col1, col2, col3 = st.columns([1, 1, 0.05])  # =============================================================
        with col1:
            text = 'CCS | Received after ' + str(date1) + ' | Containers ' + str(df_ccs['CONTAINER'].count())
            st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:2%; '
            f'line-height:0em; '
            f'margin-top:6px"> {text} </p>', unsafe_allow_html=True)

            # build AgGrid options
            gb = GridOptionsBuilder.from_dataframe(df_ccs)
            gb.configure_grid_options(rowHeight=30)
            gb.configure_grid_options(headerHeight=25)
            gb.configure_grid_options(enableCellTextSelection=True)
            grid_options = gb.build()

            height = len(df_ccs) * 30 + 30

            df_ccs['DELIVERY DATE'] = pd.to_datetime(df_ccs['DELIVERY DATE'])  # convert str to date format
            df_ccs['DELIVERY DATE'] = df_ccs['DELIVERY DATE'].dt.strftime('%Y-%m-%d')  # convert str to date format

            AgGrid(df_ccs, grid_options, height=height, fit_columns_on_grid_load=True)

        with col2:
            text2 = 'ZEN | Received after ' + str(date1) + ' | Containers ' + str(df_zen['CONTAINER'].count())
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:2%; '
                f'line-height:0em; '
                f'margin-top:6px"> {text2} </p>', unsafe_allow_html=True)

            # build AgGrid options
            gb = GridOptionsBuilder.from_dataframe(df_zen)
            gb.configure_grid_options(rowHeight=30)
            gb.configure_grid_options(headerHeight=25)
            gb.configure_grid_options(enableCellTextSelection=True)
            gb.configure_column("CONTAINER", width=80)
            gb.configure_column("BOL", width=80)
            gb.configure_column("RECEIVED DATE", width=70)

            grid_options = gb.build()

            height = len(df_zen) * 30 + 30

            df_zen['RECEIVED DATE'] = pd.to_datetime(df_zen['RECEIVED DATE'])  # convert str to date format
            df_zen['RECEIVED DATE'] = df_zen['RECEIVED DATE'].dt.strftime('%Y-%m-%d')  # convert str to date format

            AgGrid(df_zen, grid_options, height=height, fit_columns_on_grid_load=True)

        end = time.perf_counter()  # stop runtime counter
        st.sidebar.write(f"Runtime: {end - start:.2f} seconds")  # show runtime seconds

    return

def dashboard_ccs_mts_eta_mismatch(datafile_location):
    start = time.perf_counter()  # start runtime counter

    utils.show_header('ETA Mismatch')

    df_ccs = data.ccs_df(datafile_location)

    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'MTS File Ref', 'ETA Destination Port', 'Delivered Date']]
    df_ccs = df_ccs[df_ccs["MTS File Ref"] != "BLANK"]  # BOL ref not blank
    df_ccs = df_ccs[df_ccs["Delivered Date"] == "BLANK"]  # Not yet delivered
    df_ccs.columns = (['CONTAINER', 'FROM', 'BOL', 'CCS_ETA', 'Delivered Date'])
    df_ccs['CONTAINER'] = df_ccs.apply(lambda x: str(x.iloc[0])[0:4], axis=1)

    df_mts = data.mts_df(datafile_location)

    df = pd.merge(df_ccs, df_mts, on=["BOL"], how='inner')
    df = df[['CONTAINER', 'FROM', 'BOL', 'CCS_ETA', 'MTS_ETA']]

    df['CCS_ETA'] = pd.to_datetime(df['CCS_ETA'])
    df['MTS_ETA'] = pd.to_datetime(df['MTS_ETA'])

    df['DAYS'] = (df['CCS_ETA'] - df['MTS_ETA']) / np.timedelta64(1, 'D')

    df = df[df['DAYS'] != 0]

    # remove time from datetime
    df['CCS_ETA'] = df['CCS_ETA'].dt.strftime('%Y-%m-%d')  # convert str to date format
    df['MTS_ETA'] = df['MTS_ETA'].dt.strftime('%Y-%m-%d')  # convert str to date format

    df = df.sort_values('CONTAINER', ascending=True)
    df.reset_index(drop=True, inplace=True)  # order index
    df.index = range(1, df.shape[0] + 1)

    with st.spinner('Loading...'):
        col1, col2, col3 = st.columns([2, 2, 0.1])

        with col1:
            text = 'CCS - MTS ETA Changes | Total Changes ' + str(df['CONTAINER'].count())
            # header_text(text)
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
                f'margin-top:5px"> {text} </p>', unsafe_allow_html=True)

            # build AgGrid options
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_grid_options(rowHeight=30)
            gb.configure_grid_options(headerHeight=25)
            gb.configure_grid_options(enableCellTextSelection=True)
            grid_options = gb.build()

            height = len(df) * 30 + 30

            AgGrid(df, grid_options, height=height, fit_columns_on_grid_load=True)

            utils.download_csv(df, 'CCS & MTS Changes')

        with col2:

            df1 = display_zen_mts_eta_mismatch(datafile_location, df_mts)

            text2 = 'ZEN - MTS ETA Changes | Total Changes ' + str(df1['BOL'].count())
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
                f'margin-top:5px"> {text2} </p>', unsafe_allow_html=True)

            # build AgGrid options
            gb = GridOptionsBuilder.from_dataframe(df1)
            gb.configure_grid_options(rowHeight=30)
            gb.configure_grid_options(headerHeight=25)
            gb.configure_grid_options(enableCellTextSelection=True)
            grid_options = gb.build()

            height = len(df1) * 30 + 30

            AgGrid(df1, grid_options, height=height, fit_columns_on_grid_load=True)

            utils.download_csv(df1, 'Download ZEN & MTS Changes')

            end = time.perf_counter()  # stop runtime counter
            st.sidebar.write(f"Runtime: {end - start:.2f} seconds")  # show runtime seconds

    return

def display_zen_mts_eta_mismatch(datafile_location, df_mts):
    # called from function "dashboard_ccs_mts_eta_mismatch()"

    df = data.container_df(datafile_location)

    # remove Received POs
    df = df[df['STATE'] != 'Received In Warehouse']

    df_zen = df.drop_duplicates(subset=['BOL'], keep='first')

    df = pd.merge(df_zen, df_mts, on=["BOL"], how='inner')

    df = df[['BOL', 'ODDO_ETA', 'MTS_ETA']]

    df['ODDO_ETA'] = pd.to_datetime(df['ODDO_ETA'])
    df['MTS_ETA'] = pd.to_datetime(df['MTS_ETA'])

    df['WH_ETA'] = df['MTS_ETA'] + timedelta(+7)

    df = df[df['ODDO_ETA'] != df['WH_ETA']]

    df['DAYS'] = (df['ODDO_ETA'] - df['WH_ETA']) / np.timedelta64(1, 'D')

    # remove time stamp
    df['ODDO_ETA'] = df['ODDO_ETA'].dt.strftime('%Y-%m-%d')  # convert str to date format
    df['MTS_ETA'] = df['MTS_ETA'].dt.strftime('%Y-%m-%d')  # convert str to date format
    df['WH_ETA'] = df['WH_ETA'].dt.strftime('%Y-%m-%d')  # convert str to date format

    df = df.sort_values('MTS_ETA', ascending=True)
    df.reset_index(drop=True, inplace=True)  # order index
    df.index = range(1, df.shape[0] + 1)
    return df

def dashboard_po_bol_matching(datafile_location):
    start = time.perf_counter()  # start runtime counter

    utils.show_header('BOL - PO Matching')

    df_mts = data.mts_df(datafile_location)

    # convert to datetime format
    df_mts['MTS_ETD'] = pd.to_datetime(df_mts['MTS_ETD'])
    df_mts['MTS_ETD'] = df_mts['MTS_ETD'].dt.strftime('%Y-%m-%d')  # convert str to date format

    df_mts['MTS_ETA'] = pd.to_datetime(df_mts['MTS_ETA'])
    df_mts['MTS_ETA'] = df_mts['MTS_ETA'].dt.strftime('%Y-%m-%d')  # convert str to date format

    df_ccs = data.ccs_df(datafile_location)
    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'MTS File Ref']]
    df_ccs.columns = (['CONTAINER NO.', 'FROM', 'BOL'])
    df_ccs = df_ccs[df_ccs["BOL"] != "BLANK"]

    # remove leading and trailing space
    df_ccs['BOL'] = df_ccs["BOL"].str.strip()

    df = pd.merge(df_mts, df_ccs, on=["BOL"], how='outer')
    df['Shipment#'] = df['Shipment#'].fillna('VOID')
    df = df[df["Shipment#"] != "VOID"]

    df['CONTAINER NO.'] = df['CONTAINER NO.'].fillna('')
    df['FROM'] = df['FROM'].fillna('')

    # add po no. and supplier in PO# column
    df['PO#'] = df['CONTAINER NO.'] + ' - ' + df['FROM']

    df_no_po = df[df["CONTAINER NO."] == ""]
    df_with_po = df[df["CONTAINER NO."] != ""]

    df_with_po = df_with_po[['Shipment#', 'BOL', 'MTS_ETD', 'MTS_ETA', 'SHIPPER', 'CONTAINERS', 'PO#']]

    po_no = st.sidebar.text_input("PO#", "ALL")

    df_po = df_with_po.copy()

    if po_no.upper() != 'ALL':
        df_with_po = df_po.loc[lambda row: row['PO#'].str.startswith(po_no[0:4])]
    else:
        df_with_po = df_po

    df_with_po = df_with_po.sort_values('PO#', ascending=False)
    df_with_po.reset_index(drop=True, inplace=True)
    df_with_po.index = range(1, df_with_po.shape[0] + 1)

    text = 'MTS BOL & CCS PO# Matching | Total Shipment ' + str(df_with_po['PO#'].count())
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
        f'margin-top:5px"> {text} </p>', unsafe_allow_html=True)

    # build AgGrid options
    gb = GridOptionsBuilder.from_dataframe(df_with_po)
    gb.configure_grid_options(rowHeight=30)
    gb.configure_grid_options(headerHeight=25)
    gb.configure_grid_options(enableCellTextSelection=True)
    gb.configure_column('Shipment#', wrapText=False, width=50)
    gb.configure_column('BOL', wrapText=False, width=50)
    gb.configure_column('MTS_ETD', wrapText=False, width=50)
    gb.configure_column('MTS_ETA', wrapText=False, width=50)
    gb.configure_column('SHIPPER', wrapText=False, width=150)
    gb.configure_column('CONTAINERS', wrapText=False, width=200)
    gb.configure_column('PO#', wrapText=False, width=80)
    grid_options = gb.build()

    col1, col2 = st.columns([4.5, 0.1])  # =============================================================

    with col1:
        df_with_po = df_with_po[['Shipment#', 'BOL', 'MTS_ETD', 'MTS_ETA', 'SHIPPER', 'CONTAINERS', 'PO#']]
        AgGrid(df_with_po, grid_options, height=500, fit_columns_on_grid_load=True)

    df_no_po = df_no_po[['Shipment#', 'BOL', 'MTS_ETD', 'MTS_ETA', 'SHIPPER', 'CONTAINERS', 'PO#']]
    df_no_po = df_no_po.sort_values('Shipment#', ascending=False)
    df_no_po.reset_index(drop=True, inplace=True)
    df_no_po.index = range(1, df_no_po.shape[0] + 1)

    text1 = 'BOL - PO Mismatch | Total Shipment ' + str(df_no_po['PO#'].count())

    with col1:
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
            f'margin-top:5px"> {text1} </p>', unsafe_allow_html=True)

    # build AgGrid options
    gb = GridOptionsBuilder.from_dataframe(df_no_po)
    gb.configure_grid_options(rowHeight=30)
    gb.configure_grid_options(headerHeight=25)
    gb.configure_grid_options(enableCellTextSelection=True)
    gb.configure_column('Shipment#', wrapText=False, width=50)
    gb.configure_column('BOL', wrapText=False, width=50)
    gb.configure_column('MTS_ETD', wrapText=False, width=50)
    gb.configure_column('MTS_ETA', wrapText=False, width=50)
    gb.configure_column('SHIPPER', wrapText=False, width=150)
    gb.configure_column('CONTAINERS', wrapText=False, width=200)
    gb.configure_column('PO#', wrapText=False, width=80)
    grid_options = gb.build()

    if len(df_no_po) > 0:
        height = len(df_no_po) * 30 + 25 + 1
        if height > 180:
            height = 180
    else:
        height = 80

    with col1:
        AgGrid(df_no_po, grid_options, height=height, fit_columns_on_grid_load=True)

    utils.download_csv(df_no_po, 'Download Data with no PO#')

    end = time.perf_counter()  # stop runtime counter
    st.sidebar.write(f"Runtime: {end - start:.2f} seconds")  # show runtime seconds

    return
