import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import plotly.graph_objects as go

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex

def stock_status_OLD(x):
    if x < 50:
        return "Low"
    elif x < 150:
        return "Medium"
    else:
        return "High"

def last_30days_sales(df_sales, df_current_month, current_month, months, days_elapsed):
    previous_month = months[-2]
    previous_month = pd.to_datetime(previous_month, format='%b-%y')

    start_date = pd.Timestamp(previous_month)
    days_in_previous_month = calendar.monthrange(start_date.year, start_date.month)[1]

    # ____________ Get current month sale upto yesterday ______________________________
    df1 = (
        df_sales.loc[df_sales['MONTH'] == current_month, ['SKU', 'SUPPLIER', 'TOTAL']]
        .rename(columns={'TOTAL': 'Total - Current'})
    )

    # ____________ Get previous month sale  ______________________________
    if days_elapsed < 31:
        df2 = (
            df_sales.loc[df_sales['MONTH'] == previous_month, ['SKU', 'TOTAL']]
            .rename(columns={'TOTAL': 'Total - Previous'})
        )

    # ____________ Merge current and previous month data ______________________________
    df_last_30d = (
        df1.merge(df2, on='SKU', how='outer')
        .fillna(0)
    )

    # _______________ Calculate proportional 30-days sales ___________________
    df_last_30d['30-DAYS'] = (df_last_30d['Total - Current'] +
                              df_last_30d['Total - Previous'] * (31 - days_elapsed) / days_in_previous_month).round(2)

    df_last_30d = df_last_30d[['SKU', 'SUPPLIER', '30-DAYS']]

    return df_last_30d

def last_60days_sales(df_sales, df_current_month, current_month, months, days_elapsed):
    start_month = months[-3]
    start_month = pd.to_datetime(start_month, format='%b-%y')

    start_date = pd.Timestamp(start_month)
    days_in_start_month = calendar.monthrange(start_date.year, start_date.month)[1]

    # st.write(start_month)
    # st.write(current_month)

    # ________________ Get Start Month Sale (two months back) _____________________
    df_start_month = (
        df_sales.loc[df_sales['MONTH'] == start_month][['SKU', 'TOTAL', 'MONTH']]
        .rename(columns={'TOTAL': 'Start Month'})
    )

    # ____________ Merge Current and Previous Month Sales Data _______
    df_current_month = df_current_month.drop(columns=['MONTH'])
    df_start_month = df_start_month.drop(columns=['MONTH'])

    df_one_month = (
        df_current_month.merge(df_start_month, on='SKU', how='outer')
        .fillna(0)
    )

    # _______________ Calculate proportional one-month sales ___________________
    df_one_month['TOTAL'] = (df_one_month['End Month'] +
                             df_one_month['Start Month'] * (31 - days_elapsed) / days_in_start_month).round(2)

    df_one_month = df_one_month[['SKU', 'SUPPLIER', 'TOTAL']]

    #  ______________ Get mid-Months Sale Only ___________________
    df_mid_month = (
        df_sales.loc[
            (df_sales['MONTH'] > start_month) &
            (df_sales['MONTH'] < current_month)
            ][['SKU', 'SUPPLIER', 'TOTAL', 'MONTH']]
    )

    df_mid_month = df_mid_month.drop(columns=['MONTH'])

    # st.write(df_mid_month)

    # _____________ Add one month sale ________________________
    df_last_60d = pd.concat([df_mid_month, df_one_month], ignore_index=True)
    df_last_60d = df_last_60d.groupby(['SKU', 'SUPPLIER'])['TOTAL'].sum().to_frame().reset_index()
    df_last_60d = df_last_60d.rename(columns={'TOTAL': '60-DAYS'})

    # st.write(df_last_60d)

    return df_last_60d

def yearly_sales(datafile_location):

    # _____________ create 13-months name list __________________
    start = datetime.now()

    months = [
        (start - relativedelta(months=i)).strftime("%b-%y")
        for i in range(13)
    ]

    months = months[::-1]  # << Reverse month order to oldest → newest

    # ________________ Get 13-Months Sales Data for ALL Supplier and ALL Models _____________________________
    _, df_sales = data.sales_trend_df(datafile_location, 'ALL', 'ALL', months)

    # ___________________ convert MONTH to datetime format ________________
    df_sales['MONTH'] = pd.to_datetime(df_sales['MONTH'], format='%b-%y')

    current_month = df_sales['MONTH'].max()

    today = date.today()
    days_elapsed = today.day

    # ________________ Get Current Month Sale _____________________
    df_current_month = (
        df_sales.loc[df_sales['MONTH'] == current_month][['SKU', 'SUPPLIER', 'TOTAL', 'MONTH']]
        .rename(columns={'TOTAL': 'End Month'})
    )

    # ________________ Get Start Month Sale _____________________
    start_month = df_sales['MONTH'].min()
    start_date = pd.Timestamp(start_month)
    days_in_start_month = calendar.monthrange(start_date.year, start_date.month)[1]

    df_start_month = (
        df_sales.loc[df_sales['MONTH'] == start_month][['SKU', 'TOTAL', 'MONTH']]
        .rename(columns={'TOTAL': 'Start Month'})
    )

    # ____________ Merge Current and Previous Month Sales Data _______
    df_one_month = (
        df_current_month.merge(df_start_month, on='SKU', how='outer')
        .fillna(0)
        )

   # _______________ Calculate proportional one-month sales ___________________
    df_one_month['TOTAL'] = (df_one_month['End Month'] +
                                   df_one_month['Start Month'] * (31 - days_elapsed) / days_in_start_month).round(2)

    df_one_month = df_one_month[['SKU', 'SUPPLIER', 'TOTAL']]

    # ______________ Get ALL months Sale between Current and Start Month ___________________
    df_mid_months = (
        df_sales.loc[
                    (df_sales['MONTH'] > start_month) &
                    (df_sales['MONTH'] < current_month)
                    ][['SKU', 'SUPPLIER', 'TOTAL']]
                    )

    # _____________ Add one month sale ________________________
    df_annual = pd.concat([df_mid_months, df_one_month], ignore_index=True)
    df_annual = df_annual.groupby(['SKU', 'SUPPLIER'])['TOTAL'].sum().to_frame().reset_index()
    df_annual = df_annual.rename(columns={'TOTAL': 'ANNUAL'})


    # _______________ Get Last 60 Days Sale Data _________________________________
    df_last_60d = last_60days_sales(df_sales, df_current_month, current_month, months, days_elapsed)

    # _______________ Get Last 30 Days Sale Data _________________________________
    df_last_30d = last_30days_sales(df_sales, df_current_month, current_month, months, days_elapsed)

    return df_annual, df_last_60d, df_last_30d

def display_inventory_monitoring(datafile_location, suppliers):

    df_annual, df_last_60d, df_last_30d = yearly_sales(datafile_location)

    df_annual = df_annual.drop(columns=['SUPPLIER'])
    df_last_60d = df_last_60d.drop(columns=['SUPPLIER'])

    # ____________ Merge 30-days and 60-Days data ______________________________
    df = (
        df_last_30d.merge(df_last_60d, on='SKU', how='outer')
        .fillna(0)
    )

    # ____________ Merge with Annual data ______________________________
    df = (
        df.merge(df_annual, on='SKU', how='outer')
        .fillna(0)
    )

    # _________________ Get Inventory Data ____________________________________
    df_inventory = (
        data.inventory_df(datafile_location)
        .loc[:, ['SKU', 'SUPPLIER', 'Existing Qty']]
        .rename(columns={'Existing Qty': 'WH'})
    )

    df_inventory = df_inventory.drop(columns=['SUPPLIER'])

    df = pd.merge(df, df_inventory, on=["SKU"], how='outer')

    # df = df.fillna(0)

    df['STOCK WEEK'] = (df['WH']/(df['30-DAYS'] * 7/30)).replace([np.inf, -np.inf], 0).fillna(0)

    # _________________ Get Incoming Inventory Data ____________________________________
    df_incoming, df_received, _ = data.container_df(datafile_location)
    df_incoming = df_incoming[['SKU', 'QTY']]

    df_incoming = df_incoming.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    df_incoming = df_incoming.rename(columns={'QTY': 'INCOMING'})

    df = pd.merge(df, df_incoming, on=["SKU"], how='left').fillna(0)

    df['TOTAL'] = df['WH'].astype(int) + df['INCOMING'].astype(int)

    df['STOCK WEEK (INCOMING)'] = (df['TOTAL'] / (df['30-DAYS'] * 7 / 30)).replace([np.inf, -np.inf], 0).fillna(0)


    df[['ANNUAL', '60-DAYS']] = df[['ANNUAL', '60-DAYS']].round(0)
    df[['30-DAYS', 'STOCK WEEK', 'STOCK WEEK (INCOMING)']] = df[['30-DAYS', 'STOCK WEEK', 'STOCK WEEK (INCOMING)']].round(2)

    # ______________ Create Dropdown Menu ______________________
    suppliers.extend(["Kangde Silicone", "LB Plast"])
    suppliers.sort()

    supplier = st.sidebar.selectbox("SUPPLIER", suppliers)
    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    # _____________ Query on Supplier & Model/Color ___________________________________________
    df = utils.supplier_model_query(df, supplier, model)
    # st.write(df)
    # st.stop()

    # ____________ Set STATUS based on "STOCK WEEK (INCOMING) & "WH" _________________________
    df["STATUS"] = pd.cut(
        df["STOCK WEEK (INCOMING)"],
        bins=[-float("inf"), 9, 14, 18, float("inf")],      # Low: < 9 w, Moderate: 9-14 w, Satisfactory: 14-18 w, Excess: > 18 w
        labels=["Low", "Moderate", "Satisfactory", "Excess"]
    )

    df.loc[
        (df["STOCK WEEK (INCOMING)"] == 0) & (df["TOTAL"] > 2),
        "STATUS"
    ] = "Excess"


    df = df[['SKU', 'STATUS', 'SUPPLIER', 'WH', 'INCOMING', 'TOTAL', 'ANNUAL', '60-DAYS', '30-DAYS', 'STOCK WEEK', 'STOCK WEEK (INCOMING)']]

    df = df.sort_values(['STATUS', 'STOCK WEEK (INCOMING)'], ascending = [True, True])

    gb = GridOptionsBuilder.from_dataframe(df)

    # _________________ Set Color Style based of STATUS values _____________________
    status_style = JsCode("""
    function(params) {
        let status = params.data.STATUS;

        if (status === 'Low') {
            return {'color': '#FF3030'};
        } else if (status === 'Moderate') {
            return {'color': '#EEAD0E'};
        } else if (status === 'Satisfactory') {
            return {'color': '#2E8B57'};
        } else if (status === 'Excess') {
            return {'color': '#8B3626'};
        }
    }
    """)

    gb.configure_column("STATUS", cellStyle=status_style)
    gb.configure_column("SKU", cellStyle=status_style)
    gb.configure_column("STOCK WEEK (INCOMING)", cellStyle=status_style)

    # _________________ Make Cells Copyable _____________________
    gb.configure_grid_options(
        enableCellTextSelection=True,  # highlight + copy text
        enableRangeSelection=True,  # select multiple cells
        clipboard=True,  # Ctrl+C support
        allowContextMenuWithControlKey=True  # right‑click copy
    )

    grid_options = gb.build()

    txt = supplier + ' - Stock Level Monitoring'
    utils.show_header(txt)

    # --------------------- Display Sub-headers ---------------------------------------
    sink_mask = ~df['SKU'].str.startswith(('RVA', 'RDM', 'RVB6'))
    tub_mask = df['SKU'].str.startswith('RVB6')
    faucet_mask = df['SKU'].str.startswith('RVF')
    acc_mask = df['SKU'].str.startswith('RVA')

    sink_counts = (
        df.loc[sink_mask, 'STATUS']
        .value_counts()
        .reindex(['Low', 'Moderate', 'Satisfactory', 'Excess'], fill_value=0)
    )

    tub_counts = (
        df.loc[tub_mask, 'STATUS']
        .value_counts()
        .reindex(['Low', 'Moderate', 'Satisfactory', 'Excess'], fill_value=0)
    )

    faucet_counts = (
        df.loc[faucet_mask, 'STATUS']
        .value_counts()
        .reindex(['Low', 'Moderate', 'Satisfactory', 'Excess'], fill_value=0)
    )

    acc_counts = (
        df.loc[acc_mask, 'STATUS']
        .value_counts()
        .reindex(['Low', 'Moderate', 'Satisfactory', 'Excess'], fill_value=0)
    )

    total_sink = sink_mask.sum()
    total_tub = tub_mask.sum()
    total_faucet = faucet_mask.sum()
    total_acc = acc_mask.sum()

    if supplier == 'ALL':
        loop = 4
        bkg_color = ["#458B74", # Sink
                     "#6495ED", # Bathtub
                     "#CD9B1D", # Faucet
                     "#68838B", # Accessories
                     ]

        txt = ['SINK', 'BATHTUB', 'FAUCET', 'ACCESSORIES']
        total = [total_sink, total_tub, total_faucet, total_acc]
        low = [sink_counts['Low'], tub_counts['Low'], faucet_counts['Low'], acc_counts['Low']]
        moderate = [sink_counts['Moderate'], tub_counts['Moderate'], faucet_counts['Moderate'], acc_counts['Moderate']]
        reliable = [sink_counts['Satisfactory'], tub_counts['Satisfactory'], faucet_counts['Satisfactory'], acc_counts['Satisfactory']]
        strong = [sink_counts['Excess'], tub_counts['Excess'], faucet_counts['Excess'], acc_counts['Excess']]

    elif supplier in {"Nicos", "Wisdom"}:
        loop = 3
        bkg_color = ["#458B74",  # Sink
                     "#6495ED",  # Bathtub
                     "#68838B",  # Accessories
                     ]

        txt = ['SINK', 'BATHTUB', 'ACCESSORIES']
        total = [total_sink, total_tub, total_acc]
        low = [sink_counts['Low'], tub_counts['Low'], acc_counts['Low']]
        moderate = [sink_counts['Moderate'], tub_counts['Moderate'], acc_counts['Moderate']]
        reliable = [sink_counts['Satisfactory'], tub_counts['Satisfactory'], acc_counts['Satisfactory']]
        strong = [sink_counts['Excess'], tub_counts['Excess'], acc_counts['Excess']]

    elif supplier in {"CAE Sanitary", "Huayi"}:
        loop = 2
        bkg_color = ["#CD9B1D",  # Faucet
                     "#68838B",  # Accessories
                     ]

        txt = ['FAUCET', 'ACCESSORIES']
        total = [total_faucet, total_acc]
        low = [faucet_counts['Low'], acc_counts['Low']]
        moderate = [faucet_counts['Moderate'], acc_counts['Moderate']]
        reliable = [faucet_counts['Satisfactory'], acc_counts['Satisfactory']]
        strong = [faucet_counts['Excess'], acc_counts['Excess']]

    elif supplier in {"Kangde Silicone", "LB Plast"}:
        loop = 1
        bkg_color = ["#68838B",  # Accessories
                     ]

        txt = ['ACCESSORIES']
        total = [total_acc]
        low = [acc_counts['Low']]
        moderate = [acc_counts['Moderate']]
        reliable = [acc_counts['Satisfactory']]
        strong = [acc_counts['Excess']]


    else:
        loop = 2
        bkg_color = ["#458B74",  # Sink
                     "#68838B",  # Accessories
                     ]

        txt = ['SINK', 'ACCESSORIES']
        total = [total_sink, total_acc]
        low = [sink_counts['Low'], acc_counts['Low']]
        moderate = [sink_counts['Moderate'], acc_counts['Moderate']]
        reliable = [sink_counts['Satisfactory'], acc_counts['Satisfactory']]
        strong = [sink_counts['Excess'], acc_counts['Excess']]


    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    cols = [col1, col2, col3, col4]

    for i in range (0, loop):
        html = f"""
        <table style="
            border-collapse: collapse;
            border-radius: 8px;
            border: 1px solid black;
            width: 90%;
            text-align: center;
            font-family: Arial;
            overflow: hidden;
        ">
            <tr>
                <th colspan="4" style="
                    border:1px solid black;
                    padding:2px;
                    background-color:{bkg_color[i]};
                    color: {"#FFF8DC"};
                    font-size:16px;
                ">
                    {txt[i]}: {total[i]}
                </th>
            </tr>
            <tr>
                <td style="
                    border:1px solid black;padding:2px;
                    font-size:14px;
                    ">
                    Low: {low[i]}
                </td>
                <td style="
                    border:1px solid black;padding:2px;
                    font-size:14px;
                    ">
                    Moderate: {moderate[i]}
                </td>
                <td style="
                    border:1px solid black;padding:2px;
                    font-size:14px;
                    ">
                    Satisfactory: {reliable[i]}
                </td>
                <td style="
                    border:1px solid black;padding:2px;
                    font-size:14px;
                    ">
                    Excess: {strong[i]}
                </td>
            </tr>
        </table>
        """

        with cols[i]:
            st.markdown(html, unsafe_allow_html=True)

    # ________________ Remove Discontinued Product and Display Table ________________________
    df_product = data.product_df(datafile_location)[['SKU']]
    df = df[df['SKU'].isin(df_product['SKU'])]

    AgGrid(
        df,
        gridOptions=grid_options,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True,
        height=600,
        )

    utils.download_csv(df, 'Download Stock Level')

    return