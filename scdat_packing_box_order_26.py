import streamlit as st
import pandas as pd
from pathlib import Path, PureWindowsPath
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex

def box_list(datafile_location):

    file_path = Path(PureWindowsPath(f"{datafile_location}Inventory\\Product_List.xlsx"))

    df = (pd.read_excel(
            file_path,
            sheet_name='Sheet1',
            usecols=['Model', 'Supplier', 'Status', 'BOX CODE']
            )
        .loc[lambda d: ~d['Model'].str.startswith('RVA', na=False)]
        .loc[lambda d: ~d['Status'].isin(['Discontinued', 'ON HOLD'])]
        .assign(**{'BOX CODE': lambda d: d['BOX CODE'].fillna('[RBX----]')})
        .rename(columns={'Model': 'SKU'})
        )

    return df

def box_inventory(datafile_location):
    file_path = Path(PureWindowsPath(f"{datafile_location}Inventory\\Inventory.csv"))

    df = (pd.read_csv(
                    file_path,
                    usecols=['Internal Reference', 'Quantity On Hand']
                    )
        .rename(columns={'Internal Reference': 'SKU', 'Quantity On Hand': 'Existing Qty' })
        .loc[lambda d: d['SKU'].str.startswith('RBX', na=False)]
        .rename(columns={'SKU': 'BOX CODE'})

    )

    return df

def forecast(datafile_location, forecast_month):
    df = (
        data.forecast_df(datafile_location, forecast_month)
        .loc[lambda d: ~d['SKU'].str.startswith('RVA', na=False),
        ['SKU', 'FORECAST']]
    )
    return df

def show_sub_header(total_forecast, total_required, total_wh, total_order):
    col_a, col_b, col_c, col_d, col_e = st.columns([1, 1, 1, 1, 2.1])
    color = [color_hex(19), color_hex(19), color_hex(19), color_hex(19)]
    font = '18px'
    cols = [col_a, col_b, col_c, col_d, col_e]
    txt = [ 'FORECAST: ' + utils.format_num(total_forecast),
            'TOTAL REQUIRED: ' + utils.format_num(total_required),
            'TOTAL WH: ' + utils.format_num(total_wh),
            'TOTAL ORDER: ' + utils.format_num(total_order),
             ]

    for i in range (0, len(cols)-1):
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    display:inline-block;
                    background-color:#f0f0f0;
                    border:1px solid #CFCFCF;
                    padding:2px 6px;
                    border-radius:10px;
                    font-family: Arial Bold;
                    color:{color[i]};
                    text-align:center;
                    font-size:{font};            
                    margin:0;
                    margin-top:-15px;
                ">
                    {txt[i]}
                </div>
                """,
                unsafe_allow_html=True
            )
    st.markdown("<br>", unsafe_allow_html=True)
    return

def display_box_order_qty(datafile_location, suppliers, forecast_month):

    suppliers.remove("ALL")     # _________ Remove 'ALL' from suppliers _________
    supplier = st.sidebar.selectbox("SUPPLIER", suppliers)
    number = st.sidebar.number_input("% OF FORECAST", value=2)

    # _________ Load Data ______________________________
    df1 = box_list(datafile_location)        # _______________ get box code list
    df_box_code = df1[df1['BOX CODE'] != '[RBX----]']

    df_forecast = forecast(datafile_location, forecast_month)   # ____________ get forecast

    # ______________ Merge Box Code and Forecast ____________
    df = (
        pd.merge(df_box_code, df_forecast, on='SKU', how='outer')
        .fillna(0)
    )

    # __________ Remove color code from SKU but not 'LM" ________________
    mask = ~ df['SKU'].str.endswith('LM', na=False)
    df.loc[mask, 'SKU'] = df.loc[mask, 'SKU'].str.replace(r'\D+$', '', regex=True)

    # _____________ filter by supplier ____________________
    df = df[df['Supplier'] == supplier]

    # ________________ Create SKU list by BOX CODE ___________
    df_sku = (
        df.groupby('BOX CODE')['SKU']
        .unique()
        .apply(lambda x: ' | '.join(x))
        .reset_index(name='SKU')
    )

    # ___________ Forecast summary by BOX CODE _____________
    df_summary = (
        df.groupby('BOX CODE', as_index=False)['FORECAST']
        .sum()
        .sort_values('BOX CODE')
    )

    # ______________ Calculate required quantity _____________
    df_summary['QTY REQUIRED'] = (
            df_summary['FORECAST'] * number * 6 / 100
    ).round(0)

    # ___________ Merge inventory _____________
    df_inventory = (
        box_inventory(datafile_location)
        .rename(columns={'Existing Qty': 'WH QTY'})
    )

    df_summary = (
        df_summary
        .merge(df_inventory, on='BOX CODE', how='left')
        .merge(df_sku, on='BOX CODE', how='left')
    )

    # ___________ Fill missing warehouse qty _________________
    df_summary['WH QTY'] = df_summary['WH QTY'].fillna(0)

    # _____________ Calculate order qty ____________________
    df_summary['ORDER QTY'] = (
            df_summary['QTY REQUIRED'] - df_summary['WH QTY']
    )

    # Final column order
    df_summary = df_summary[
        ['BOX CODE', 'FORECAST', 'QTY REQUIRED', 'WH QTY', 'ORDER QTY', 'SKU']
    ]

    # _____________ Display ________________________________________________
    utils.show_header(supplier + ' Packing Box Order')
    show_sub_header(df_summary['FORECAST'].sum(),
                    df_summary['QTY REQUIRED'].sum(),
                    df_summary['WH QTY'].sum(),
                    df_summary['ORDER QTY'].loc[df_summary['ORDER QTY'] > 0].sum(),
                    )

    col1, col2, _ = st.columns([2, 1, 0.3])

    with col1:
        # __________ Configure AgGrid column size _____________
        gb = GridOptionsBuilder.from_dataframe(df_summary)

        gb.configure_column("BOX CODE", width=100)
        gb.configure_column("FORECAST", width=100, type=["numericColumn"])
        gb.configure_column("QTY REQUIRED", width=100, type=["numericColumn"])
        gb.configure_column("WH QTY", width=80, type=["numericColumn"])
        gb.configure_column("ORDER QTY", width=100, type=["numericColumn"])
        gb.configure_column("SKU", width=350)

        grid_options = gb.build()


        AgGrid(
            df_summary,
            gridOptions=grid_options,
            fit_columns_on_grid_load=False,
            height=min(len(df_summary)*40, 500) + 2
            )

        utils.download_csv(df_summary, 'Download')

    with col2:
        df1 = df1.loc[df1['Supplier'] == supplier]

        AgGrid(df1,
               height=min(len(df1)*40, 500),
               fit_columns_on_grid_load=True
               )

    return
