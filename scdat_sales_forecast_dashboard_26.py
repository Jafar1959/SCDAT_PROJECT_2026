import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode
import pandas as pd
import time
import plotly.graph_objects as go
import calendar
from datetime import datetime
from datetime import date

from plotly.subplots import make_subplots
import statistics

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex
from pathlib import Path, PureWindowsPath    # for Window & Mac OS path-slash '\' or '/'

# from scdat_colors_26 import color_hex

def inventory_mix_df(datafile_location, forecast_month, supplier, model):
    # --------------- LOAD INVENTORY DATA  ---------------------------
    df_inventory = (data.inventory_df(datafile_location)[['SKU', 'SUPPLIER', 'Existing Qty']]
                    .rename(columns={'Existing Qty': 'WH_QTY'})
                    )

    # --------------- LOAD FORECAST DATA ---------------------------
    df_forecast = data.forecast_df(datafile_location, forecast_month)[['SKU', 'FORECAST']]

    # ------------------- MERGE FORECAST & INVENTORY --------------
    df = (
        df_forecast
        .merge(df_inventory, on='SKU', how='left')
        .fillna({'WH_QTY': 0, 'FORECAST': 0})
    )

    # ============ CALCULATE WH STOCK IN MONTH (Avoid divide-by-zero) ============================
    df['MONTH'] = (df['WH_QTY'] / df['FORECAST'].replace(0, pd.NA)).fillna(0).round(2)

    # =================== FILTER BY SUPPLIER, MODEL AND COLOR ===================================
    df = utils.supplier_model_query(df, supplier, model)    # query on supplier and model

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')  # accessories, boxes, dummy faucets, faucet parts
    df_sink = utils.exclude_sku_prefixes(df, prefixes)
    df_accessories = df.loc[lambda row: row['SKU'].str.startswith('RVA')]

    # ------------------ TOTALS --------------------------------------
    total_sku = len(df_sink)
    total_forecast = df_sink['FORECAST'].sum()
    total_inventory = df_sink['WH_QTY'].sum()

    total_sku_acc = len(df_accessories)
    total_inventory_acc = df_accessories['WH_QTY'].sum()

    sku_zero = (df_sink['MONTH'] <= 0.23).sum()     # create boolean field and get sum of the TRUE

    # --------------- week < qty < 1m -------------------
    mask_1m = (df_sink['MONTH'] > 0.23) & (df_sink['MONTH'] <= 1)
    sku_1m = mask_1m.sum()
    qty_1m = df_sink.loc[mask_1m, 'WH_QTY'].sum()

    # --------------- 1m < qty < 2m -------------------
    mask_2m = (df_sink['MONTH'] > 1) & (df_sink['MONTH'] <= 2)
    sku_2m = mask_2m.sum()
    qty_2m = df_sink.loc[mask_2m, 'WH_QTY'].sum()

    # --------------- 2m < qty < 3m -------------------
    mask_3m = (df_sink['MONTH'] > 2) & (df_sink['MONTH'] <= 3)
    sku_3m = mask_3m.sum()
    qty_3m = df_sink.loc[mask_3m, 'WH_QTY'].sum()

    # --------------- 3m < qty < 4m -------------------
    mask_4m = (df_sink['MONTH'] > 3) & (df_sink['MONTH'] <= 4)
    sku_4m = mask_4m.sum()
    qty_4m = df_sink.loc[mask_4m, 'WH_QTY'].sum()

    # --------------- qty > 3m -------------------
    mask_3plus = df_sink['MONTH'] > 3
    sku_3plus = mask_3plus.sum()
    qty_3plus = (
            df_sink.loc[mask_3plus, 'WH_QTY']
            - df_sink.loc[mask_3plus, 'FORECAST'] * 3
    ).sum()

    # --------------- qty > 4m -------------------
    mask_4plus = df_sink['MONTH'] > 4
    sku_4plus = mask_4plus.sum()
    qty_4plus = (
            df_sink.loc[mask_4plus, 'WH_QTY']
            - df_sink.loc[mask_4plus, 'FORECAST'] * 3
    ).sum()

    # # week < qty < 1m
    # df_1m = df_sink[df_sink['MONTH'] > 0.23]
    # df_1m = df_1m[df_1m['MONTH'] <= 1]
    # sku_1m = df_1m['SKU'].count()
    # qty_1m = df_1m['WH_QTY'].sum()

    # # 1 < qty < 2m
    # df_2m = df_sink[df_sink['MONTH'] > 1]
    # df_2m = df_2m[df_2m['MONTH'] <= 2]
    # sku_2m = df_2m['SKU'].count()
    # qty_2m = df_2m['WH_QTY'].sum()

    # # 2 < qty < 3m
    # df_3m = df_sink[df_sink['MONTH'] > 2]
    # df_3m = df_3m[df_3m['MONTH'] <= 3]
    # sku_3m = df_3m['SKU'].count()
    # qty_3m = df_3m['WH_QTY'].sum()

    # # 3 < qty < 4m
    # df_4m = df_sink[df_sink['MONTH'] > 3]
    # df_4m = df_4m[df_4m['MONTH'] <= 4]
    # sku_4m = df_4m['SKU'].count()
    # qty_4m = df_4m['WH_QTY'].sum()

    # # qty > 3m
    # df_3plus = df_sink[df_sink['MONTH'] > 3].copy()
    # df_3plus['EXCESS'] = df_3plus['WH_QTY'] - df_3plus['FORECAST'] * 3
    # sku_3plus = df_3plus['SKU'].count()
    # qty_3plus = df_3plus['EXCESS'].sum()

    # # qty > 4m
    # df_4plus = df_sink[df_sink['MONTH'] > 4].copy()
    # df_4plus['EXCESS'] = df_4plus['WH_QTY'] - df_4plus['FORECAST'] * 4
    # sku_4plus = df_4plus['SKU'].count()
    # qty_4plus = df_4plus['EXCESS'].sum()

    df_mix = pd.DataFrame({
                            'Supplier': [supplier],
                            'Total Sku': [total_sku],
                            'Total Forecast': [total_forecast],
                            'Total Qty': [total_inventory],

                            'Qty = 0': [sku_zero],

                            'Sku-1m': [sku_1m], 'Qty-1m': [qty_1m],
                            'Sku-2m': [sku_2m], 'Qty-2m': [qty_2m],
                            'Sku-3m': [sku_3m], 'Qty-3m': [qty_3m],
                            'Sku-4m': [sku_4m], 'Qty-4m': [qty_4m],

                            'Sku-3plus': [sku_3plus], 'Qty-3plus': [qty_3plus],
                            'Sku-4plus': [sku_4plus], 'Qty-4plus': [qty_4plus],

                            'Sku Accessories': [total_sku_acc],
                            'Qty Accessories': [total_inventory_acc],
                           })

    return df, df_mix

def inventory_dashboard(datafile_location, forecast_month, supplier, model):

    # unpack inventory_mix_df
    _, df_pie = inventory_mix_df(datafile_location, forecast_month, supplier, model)

    total_forecast = df_pie.at[0, 'Total Forecast']
    # st.write(total_forecast)
    # st.stop()

    colors = [color_hex(324), color_hex(128), color_hex(200), color_hex(423), color_hex(251), 'darkgreen']

    name1 = 'QTY < 7d  [' + str(df_pie['Qty = 0'].sum()) + ']\n'
    name2 = 'QTY < 1m [' + str(df_pie['Sku-1m'].sum()) + ']\n'
    name3 = 'QTY < 2m [' + str(df_pie['Sku-2m'].sum()) + ']\n'
    name4 = 'QTY < 3m [' + str(df_pie['Sku-3m'].sum()) + ']\n'
    name5 = 'QTY < 4m [' + str(df_pie['Sku-4m'].sum()) + ']\n'
    name6 = 'QTY > 4m [' + str(df_pie['Sku-4plus'].sum()) + ']'

    names = [name1, name2, name3, name4, name5, name6]

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=names,
        values=[df_pie['Qty = 0'].sum(), df_pie['Sku-1m'].sum(), df_pie['Sku-2m'].sum(),
        df_pie['Sku-3m'].sum(), df_pie['Sku-4m'].sum(), df_pie['Sku-4plus'].sum()],

        hole=0.60,

        )),

    fig.update_traces(textposition='inside', textinfo='percent',
                      marker=dict(colors=colors, line=dict(color='white', width=1.5)))

    fig.update_traces(sort=False)

    fig.update_layout(legend=dict(title_font_family="Book Antiqua",

                      font=dict(size=14),
                      x=0,
                      y=0.5,
                      xanchor="left",
                      yanchor="middle",
                      # tracegroupgap=120  # spacing between legend items
                                  ),

                      margin=dict(l=0, r=0, t=0, b=0),  # extra right margin for legend

                      width = 250,
                      height = 315,
                      )

    # ------------- SET X & Y VALUES for ANNOTATION -----------------------------------
    x, y = 0.5, 0.5

    fig.add_annotation(x=x, y=y + 0.25,
                       text='Forecast: ' + str(total_forecast),
                       font=dict(size=17, family='Book Antiqua', color=color_hex(292)),
                       showarrow=False)

    fig.add_annotation(x=x, y=y + 0.13,
                       text='SKU: ' + str(df_pie['Total Sku'].sum()),
                       font=dict(size=17, family='Book Antiqua', color='blue'),
                       showarrow=False)

    fig.add_annotation(x=x, y=y + 0.06,
                       text='Qty: ' + str(df_pie['Total Qty'].sum())[:-2],
                       font=dict(size=20, family='Book Antiqua', color='maroon'),
                       showarrow=False)

    percent = str(round(df_pie['Qty-3plus'].sum() * 100 / df_pie['Total Qty'].sum(), 0))[:-2] + '%'

    fig.add_annotation(x=x, y=y - 0.04,
                       text='> 3m: ' + str(df_pie['Qty-3plus'].sum())[:-2] + ' (' + percent + ')',
                       font=dict(size=16, family='Book Antiqua', color='green'),
                       showarrow=False)

    fig.add_annotation(x=x, y=y - 0.055,
                       text='_____________',
                       font=dict(size=22, family='Book Antiqua', color='lightgrey'),
                       showarrow=False)

    if df_pie['Sku Accessories'].sum() > 0:
        fig.add_annotation(x=x, y=y - 0.19,
                       text='Acc. SKU: ' + str(df_pie['Sku Accessories'].sum()),
                       font=dict(size=16, family='Book Antiqua', color='grey'),
                       showarrow=False)

        fig.add_annotation(x=x, y=y - 0.25,
                       text='Acc. Qty: ' + str(df_pie['Qty Accessories'].sum())[:-2],
                       font=dict(size=14, family='Book Antiqua', color='grey'),
                       showarrow=False)

    st.plotly_chart(fig, width='stretch')

    return

def inventory_distribution_pie_summary(datafile_location, forecast_month, supplier_list):
    # get total forecast quantity for stock calculation << ==========================================
    df_forecast = data.forecast_df(datafile_location, forecast_month)

    # ________________ Remove row If SKU has BOTH NaN + empty strings ____________________________
    df_forecast = df_forecast[df_forecast['SKU'].notna() & (df_forecast['SKU'].str.strip() != '')]

    if len(df_forecast) > 0:
        df_forecast = df_forecast.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]

    forecast = df_forecast['FORECAST'].sum()

    # get Amazon WH Quantity  << ======================================================================
    df_fba = data.fba_inventory_df(datafile_location)
    df_fba = df_fba.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df_fba = df_fba.rename(columns={'TOTAL FBA STOCK': 'QTY'})
    df_fba = df_fba.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()

    # st.write(df_fba)

    # get total WH inventory << =====================================================================
    values = data.wh_wise_inventory_df(datafile_location)

    df_wh1 = values[1]
    df_wh2 = values[2]
    df_wh3 = values[3]
    df_wh4 = values[4]
    df_accessories = values[5]
    df_box = values[6]
    df_refurb = values[7]
    df_l_container = values[8]
    df_retail = values[9]
    retail_models = values[10]
    df_faucet = values[11]
    df_bathtub = values[12]
    df_faucet_parts = values[13]

    # st.write(df_wh['QTY'].sum())
    total_wh1 = utils.format_num(df_wh1['QTY'].sum())
    total_wh4 = utils.format_num(df_wh4['QTY'].sum())
    total_accessories = utils.format_num(df_accessories['QTY'].sum())
    total_wh2 = utils.format_num(df_wh2['QTY'].sum())
    total_box = utils.format_num(df_box['QTY'].sum())
    total_refurb = utils.format_num(df_refurb['QTY'].sum())
    total_wh3 = utils.format_num(df_wh3['QTY'].sum())
    total_l_container = utils.format_num(df_l_container['QTY'].sum())
    total_lowes_model = utils.format_num(df_retail['QTY'].sum())
    total_faucets = utils.format_num(df_faucet['QTY'].sum())
    total_faucets_parts = utils.format_num(df_faucet_parts['QTY'].sum())

    total_bathtubs = utils.format_num(df_bathtub['QTY'].sum())

    df_all = pd.DataFrame({'WH1': [total_wh1],
                           'WH2': [total_wh2],
                           'WH3': [total_wh3],
                           'WH4': [total_wh4],
                           'L-CONTAINER': [total_l_container],
                           'REFURBISHED': [total_refurb],
                           'ACCESSORIES': [total_accessories],
                           'PACKING BOX': [total_box],
                           'LOWES MODELS': [total_lowes_model],
                           'FAUCETS': [total_faucets],
                           'FAUCET PARTS': [total_faucets_parts],
                           'BATHTUBS': [total_bathtubs],

                           })
    stock = round((df_wh1['QTY'].sum() + df_wh2['QTY'].sum() + df_wh3['QTY'].sum() + df_wh4['QTY'].sum())/forecast, 2)

    # st.markdown(
    #     f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
    #     f' line-height:0em; margin-top:0px"> Warehouse Inventory Mix | Stock: {stock} month | {utils.get_todays_date()}</p>',
    #     unsafe_allow_html=True)

    txt = " Warehouse Inventory Mix | Stock: " +  str(stock) + " month | " + utils.get_todays_date()
    utils.show_header(txt)


    fig = go.Figure(data=[go.Table(
        columnwidth=[10, 10, 10, 10, 14],

        header=dict(values=df_all.columns,
                    fill_color=[color_hex(396)], # color_hex(67)],  # header_color,
                    font=dict(family="Arial", size=14, color='white'),
                    line_color='white',
                    height=28,
                    align=['center']),
        cells=dict(

            values=[df_all['WH1'], df_all['WH2'], df_all['WH3'], df_all['WH4'], df_all['L-CONTAINER'], df_all['REFURBISHED'],
                    df_all['ACCESSORIES'], df_all['PACKING BOX'], df_all['LOWES MODELS'], df_all['FAUCETS'], df_all['FAUCET PARTS'],
                    df_all['BATHTUBS']],

            font=dict(family="Arial", size=12, color='black'),
            font_size=14,
            height=28,  # 24,
            fill_color=[color_hex(392)],    # color_hex(303)],
            line_color='white',
            align=['center']))
    ])

    fig.update_layout(height=len(df_all) * 30 + 30, margin=dict(l=0, r=0, b=0, t=0))
    #fig = fig.update_layout(height=55, margin=dict(l=0, r=0, b=0, t=0))

    # get color for each supplier for pie  << ======================================================================
    colors = [''] * len(supplier_list)  # create array with 'blank' elements

    df_colors = pd.DataFrame({'SUPPLIER': supplier_list, 'COLOR': colors})

    df_colors.loc[df_colors['SUPPLIER'] == 'ALL', 'COLOR'] += color_hex(417),
    df_colors.loc[df_colors['SUPPLIER'] == 'Aquacubic', 'COLOR'] += color_hex(274),
    df_colors.loc[df_colors['SUPPLIER'] == 'Bomeijia', 'COLOR'] += color_hex(59),
    df_colors.loc[df_colors['SUPPLIER'] == 'CAE Sanitary', 'COLOR'] += color_hex(185),
    df_colors.loc[df_colors['SUPPLIER'] == 'Carysil', 'COLOR'] += color_hex(96),
    df_colors.loc[df_colors['SUPPLIER'] == 'Changie', 'COLOR'] += color_hex(189),
    df_colors.loc[df_colors['SUPPLIER'] == 'Elleci', 'COLOR'] += color_hex(239),
    df_colors.loc[df_colors['SUPPLIER'] == 'Galassia', 'COLOR'] += color_hex(411),
    df_colors.loc[df_colors['SUPPLIER'] == 'Huayi', 'COLOR'] += color_hex(27),
    df_colors.loc[df_colors['SUPPLIER'] == 'Nicos', 'COLOR'] += color_hex(111),
    df_colors.loc[df_colors['SUPPLIER'] == 'Plados', 'COLOR'] += color_hex(120),
    df_colors.loc[df_colors['SUPPLIER'] == 'Speed', 'COLOR'] += color_hex(97),
    df_colors.loc[df_colors['SUPPLIER'] == 'Speed Vietnam', 'COLOR'] += color_hex(95),
    df_colors.loc[df_colors['SUPPLIER'] == 'Stile Libero', 'COLOR'] += color_hex(17),
    df_colors.loc[df_colors['SUPPLIER'] == 'UAE Fireclay', 'COLOR'] += color_hex(56),
    df_colors.loc[df_colors['SUPPLIER'] == 'Wisdom', 'COLOR'] += color_hex(60),
    df_colors.loc[df_colors['SUPPLIER'] == 'Xindeli', 'COLOR'] += color_hex(406),
    df_colors.loc[df_colors['SUPPLIER'] == 'Yalos', 'COLOR'] += color_hex(25),

    # st.write(df_colors)
    # st.stop()

    # get Austin WH Quantity  << ======================================================================
    df_austin = pd.concat([df_wh1, df_wh3, df_wh4])
    df_austin = df_austin.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df_austin = df_austin.loc[lambda row: ~ row['SKU'].str.startswith('RBX')]   # remove boxes if any
    df_austin = df_austin.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()

    # get Houston WH Quantity  << ======================================================================
    df_houston = df_wh2.copy()
    df_houston = df_houston.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df_houston = df_houston.loc[lambda row: ~ row['SKU'].str.startswith('RBX')]  # remove boxes if any
    df_houston = df_houston.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()

    # get Lowes Retail Models Quantity  << ======================================================================
    df_retail = df_retail.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    df_retail = df_retail.rename(columns={'SKU': 'SUPPLIER'})

    # get Faucet Quantity  << ======================================================================
    df_faucet = df_faucet.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()

    # get Bathtubs Quantity  << ======================================================================
    df_bathtub = df_bathtub.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()

    location = ['Austin WH', 'Houston WH', 'Amazon WH', 'Retail Models', 'Faucets', 'Bathtubs']

    mygrid = utils.make_grid(2, 3)  # (row, col)
    #mygrid = utils.make_grid(1, 4)  # (row, col)
    row = 0
    col = 0

    for i in range(0, len(location)):
        if location[i] == 'Austin WH':
            df_pie = df_austin
            height = 326

        elif location[i] == 'Houston WH':
            df_pie = df_houston
            height = 326

        elif location[i] == 'Amazon WH':
            df_pie = df_fba
            height = 326

        elif location[i] == 'Retail Models':
            df_pie = df_retail
            height = 250

            colors = [''] * len(retail_models)  # create array with 'blank' elements for 5 retail models

            df_colors = pd.DataFrame({'SUPPLIER': retail_models, 'COLOR': colors})
            df_colors.loc[df_colors['SUPPLIER'] == 'RVH180051LM', 'COLOR'] += color_hex(35),  # Speed
            df_colors.loc[df_colors['SUPPLIER'] == 'RVH183001LM', 'COLOR'] += color_hex(81),  # Speed
            df_colors.loc[df_colors['SUPPLIER'] == 'RVH185841LM', 'COLOR'] += color_hex(33),  # Speed
            df_colors.loc[df_colors['SUPPLIER'] == 'RVH165301BL', 'COLOR'] += color_hex(40),  # Aquacubic
            df_colors.loc[df_colors['SUPPLIER'] == 'RVG11080BK', 'COLOR'] += color_hex(97),  # Elleci
            df_colors.loc[df_colors['SUPPLIER'] == 'RVG123061BK', 'COLOR'] += color_hex(95),  # Elleci

        elif location[i] == 'Faucets':
            df_pie = df_faucet
            height = 250

            faucet_suppliers = df_pie['SUPPLIER'].to_list()
            colors = [''] * len(df_pie)  # create array with 'blank' elements for 2 suppliers

            df_colors = pd.DataFrame({'SUPPLIER': faucet_suppliers, 'COLOR': colors})
            df_colors.loc[df_colors['SUPPLIER'] == 'CAE Sanitary', 'COLOR'] += color_hex(185),
            df_colors.loc[df_colors['SUPPLIER'] == 'Huayi', 'COLOR'] += color_hex(27),

        elif location[i] == 'Bathtubs':
            df_pie = df_bathtub
            height = 250

            bathtub_suppliers = df_pie['SUPPLIER'].to_list()
            colors = [''] * len(df_pie)  # create array with 'blank' elements for 2 suppliers

            df_colors = pd.DataFrame({'SUPPLIER': bathtub_suppliers, 'COLOR': colors})

            df_colors.loc[df_colors['SUPPLIER'] == 'Nicos', 'COLOR'] += color_hex(111),
            df_colors.loc[df_colors['SUPPLIER'] == 'Wisdom', 'COLOR'] += color_hex(60),

        df_pie = pd.merge(df_pie, df_colors, on=['SUPPLIER'], how='left')
        df_pie['LEGEND'] = df_pie.apply(lambda x: str(x.iloc[0]) + ' (' + utils.format_num(str(x.iloc[1])) + ')', axis=1)
        df_pie = df_pie.sort_values('QTY', ascending=False)

        # st.write(df_pie)
        # st.stop()

        fig1 = go.Figure()
        fig1.add_trace(go.Pie(
            labels=df_pie['LEGEND'],
            values=df_pie['QTY'],
            hole=0.5,
                        ),
                  )

        fig1.add_annotation(x=0.5, y=0.53,
                       text='TOTAL',
                       font=dict(size=17, family='Book Antiqua', color=color_hex(119)),
                       showarrow=False)

        fig1.add_annotation(x=0.5, y=0.45,
                            text=utils.format_num(str(df_pie['QTY'].sum())),
                            font=dict(size=24, family='Book Antiqua', color=color_hex(119)),
                            showarrow=False)

        # mygrid[row][col].write('')
        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(50)}; text-align:left; font-size: 20px ;border-radius:1%;'
            f' line-height:0em; margin-top:8px"> {location[i]}<p/>', unsafe_allow_html=True)

        # fig1 = fig1.update_layout(height=326, margin=dict(l=0, r=0, b=0, t=0))
        fig1 = fig1.update_layout(height=height, margin=dict(l=0, r=0, b=0, t=0))

        fig1.update_traces(textposition='inside', textinfo='percent',
                                           marker=dict(colors=df_pie['COLOR'], line=dict(color='white', width=1.4)))

        fig1.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=12), orientation='v', x=0.95, y=0.5, yanchor='middle'))

        mygrid[row][col].plotly_chart(fig1, width='stretch')

        col = col + 1
        if col > 2:
            row = row + 1
            col = 0

    col1, col2 = st.columns([2.1, 0.01])
    with col1:
        st.plotly_chart(fig, use_container_width=True)

    # _______________ Show Download Links _____________
    downloads = [
        (df_wh1, "Download WH1"),
        (df_wh2, "Download WH2"),
        (df_wh3, "Download WH3"),
        (df_wh4, 'Download WH4'),
        (df_fba, 'Download FBA'),
        (values[9], 'Download LOWES'),
        (values[11], 'Download FAUCETS'),
        (values[12], 'Download BATHTUBS'),
    ]

    cols = st.columns(len(downloads))

    for col, (df, label) in zip(cols, downloads):
        with col:
            utils.download_csv(df, label)

    downloads = [
        (df_l_container, 'Download L-CONTAINER'),
        (df_accessories, 'Download PARTS'),
        (df_refurb, 'Download REFURBISHED'),
        (df_box, 'Download PACKING BOX')
    ]

    cols = st.columns(len(downloads))

    for col, (df, label) in zip(cols, downloads):
        with col:
            utils.download_csv(df, label)

    # col1, col2, col3 = st.columns([1, 1, 1])
    #
    # with col1:
    #     utils.download_csv(df_wh1, 'Download WH1')
    # with col2:
    #     utils.download_csv(df_wh2, 'Download WH2')
    # with col3:
    #     utils.download_csv(df_wh3, 'Download WH3')
        # utils.download_csv(df_wh4, 'Download WH4')
        # utils.download_csv(df_fba, 'Download FBA')
        # utils.download_csv(values[9], 'Download LOWES')
        # utils.download_csv(values[11], 'Download FAUCETS')
        # utils.download_csv(values[12], 'Download BATHTUBS')
        #
        # utils.download_csv(df_l_container, 'Download L-CONTAINER')
        # utils.download_csv(df_accessories, 'Download PARTS')
        # utils.download_csv(df_refurb, 'Download REFURBISHED')
        # utils.download_csv(df_box, 'Download PACKING BOX')

    # _______ Create Button and Log Data ____________________________
    st.markdown("""
       <style>
       div.stButton > button {
           background-color: #53868B;
           width: 205px;
           height: 45px;
           padding: 5px 15px;
           color: white;
           font-size: 18px;
           font-weight: bold;
           border-radius: 8px;
           border: 2px solid white;
       }

       div.stButton > button:hover {
           background-color: #458B74;
           color: white;
       }
       </style>
       """, unsafe_allow_html=True)

    # _________ Show Inventory Log Graph _____________________
    log_data_graph(datafile_location + 'Inventory\\DAILY INVENTORY LOG.xlsx')

    if st.sidebar.button("LOG INVENTORY DATA"):
        log_inventory(datafile_location)

    return


def log_inventory(datafile_location):
    df = data.inventory_df(datafile_location)[['SKU', 'SUPPLIER', 'Existing Qty']]
    df = df.rename(columns={'Existing Qty': 'QTY'})

    # ______________ Get Sink & Faucet Data ____________________
    prefixes = ('RVA', 'RBX', 'RDM', 'RVP', 'RVB6')  # Accessories, Boxes, Dummy faucets/Display, Faucet parts, Bathtub
    df_sink = utils.exclude_sku_prefixes(df, prefixes)
    df_sink = df_sink.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()
    df_sink = df_sink.set_index('SUPPLIER').T
    df_sink.columns.name = None

    # ______________ Add Nicos Bathtub _______________________
    df_nicos_tub = df[
        (df["SUPPLIER"] == "Nicos") &
        (df["SKU"].str.startswith("RVB6", na=False))
        ]
    total_nicos_tub = df_nicos_tub['QTY'].sum()

    nicos_column_number = df_sink.columns.get_loc("Nicos")
    df_sink.insert(nicos_column_number + 1, "Nicos-Tub", total_nicos_tub)

    # ______________ Add Wisdom Bathtub _______________________
    df_wisdom_tub = df[
        (df["SUPPLIER"] == "Wisdom") &
        (df["SKU"].str.startswith("RVB6", na=False))
        ]
    total_wisdom_tub = df_wisdom_tub['QTY'].sum()

    wisdom_column_number = df_sink.columns.get_loc("Wisdom")
    df_sink.insert(wisdom_column_number + 1, "Wisdom-Tub", total_wisdom_tub)

    # ____________ Add Accessories Data ______________________________
    df_accessories = df.loc[lambda row: row['SKU'].str.startswith('RVA')]
    df_accessories = df_accessories.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()
    df_accessories = df_accessories.set_index('SUPPLIER').T
    df_accessories.columns.name = None
    df_accessories.columns = df_accessories.columns.astype(str) + '_Acc'

    log_data = pd.concat([df_sink, df_accessories], axis=1)

    # _____________ Add FBA Data _________________________
    df_fba = data.fba_inventory_df(datafile_location)[['SKU', 'TOTAL FBA STOCK']]
    prefixes = ('RVA', 'RVF')  # accessories, faucets
    df_fba_sink = utils.exclude_sku_prefixes(df_fba, prefixes)
    df_fba_faucet = df_fba.loc[lambda row: row['SKU'].str.startswith('RVF')]
    df_fba_accessories = df_fba.loc[lambda row: row['SKU'].str.startswith('RVA')]

    log_data['FBA_Sink'] = df_fba_sink['TOTAL FBA STOCK'].sum()
    log_data['FBA_Faucet'] = df_fba_faucet['TOTAL FBA STOCK'].sum()
    log_data['FBA_Acc'] = df_fba_accessories['TOTAL FBA STOCK'].sum()

    # ____________ Add Lowes Models _____________________________
    lowes_sink = ['RVH180051LM', 'RVH183001LM', 'RVH185841LM', 'RVH165301BL', 'RVG11080BK', 'RVG123061BK']      # <<<< Lowes List

    df_lowes_sink = df[df['SKU'].isin(lowes_sink)]
    log_data['Lowes_Sink'] = df_lowes_sink['QTY'].sum()

    lowes_acc = ['RVA9001LM']
    df_lowes_acc = df[df['SKU'].isin(lowes_acc)]
    log_data['Lowes_Acc'] = df_lowes_acc['QTY'].sum()

    # ____________ Add Incoming Sink, Tub & Faucet Qty________________
    df_incoming, *_ = data.container_df(datafile_location)
    df_incoming = df_incoming[['SKU', 'QTY']]

    prefixes = ('RVA', 'RBX', 'RDM', 'RVF', 'RVP', 'RVB6')  # Accessories, Boxes, Dummy faucets/Display, Faucet, Faucet parts, Bathtub
    df_incoming_sink = utils.exclude_sku_prefixes(df_incoming, prefixes)
    df_incoming_sink = df_incoming_sink.groupby('SKU')['QTY'].sum().to_frame().reset_index()

    df_incoming_tub = df_incoming.loc[lambda row: row['SKU'].str.startswith('RVB6')]
    df_incoming_tub = df_incoming_tub.groupby('SKU')['QTY'].sum().to_frame().reset_index()

    df_incoming_faucet = df_incoming.loc[lambda row: row['SKU'].str.startswith('RVF')]
    df_incoming_faucet = df_incoming_faucet.groupby('SKU')['QTY'].sum().to_frame().reset_index()

    df_incoming_acc = df_incoming.loc[lambda row: row['SKU'].str.startswith('RVA')]
    df_incoming_acc = df_incoming_acc.groupby('SKU')['QTY'].sum().to_frame().reset_index()

    log_data['Incoming_Sink'] = df_incoming_sink['QTY'].sum()
    log_data['Incoming_Tub'] = df_incoming_tub['QTY'].sum()
    log_data['Incoming_Faucet'] = df_incoming_faucet['QTY'].sum()
    log_data['Incoming_Acc'] = df_incoming_acc['QTY'].sum()

    # st.write(log_data)
    # st.stop()

    # ______________ Insert Date, Day & Time _____________________
    today = date.today()
    day = today.strftime("%A")
    current_time = datetime.now().strftime("%I:%M:%S %p")

    log_data.insert(0, "DATE", today)
    log_data.insert(1, "DAY", day)
    log_data.insert(2, "TIME", current_time)

    utils.log_data_in_file(datafile_location, log_data, 'Inventory\\DAILY INVENTORY LOG.xlsx')

    return log_data


def log_data_graph(file_path):
    file_path = Path(PureWindowsPath(file_path))
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    df['DATE'] = df['DATE'].dt.strftime('%Y-%m-%d')  # convert str to date format
    df = df.sort_values('DATE', ascending=False)

    # -----------------------------
    # Prepare data
    # -----------------------------
    df["DATE"] = pd.to_datetime(df["DATE"])

    # Sort by date
    df = df.sort_values("DATE")

    # Columns available for selection
    exclude_columns = ["DATE", "DAY", "TIME"]
    quantity_columns = [col for col in df.columns if col not in exclude_columns]

    # __________ Set Range Filter ___________
    range = st.sidebar.selectbox(
        "Log Graph | Select Range",
        ['Last 30-days', 'Last 60-days', 'Last 180-days', 'Last 365-days']
    )

    delta = {
        'Last 30-days': 30,
        'Last 60-days': 60,
        'Last 180-days': 180,
        'Last 365-days': 365

    }.get(range, 30)  # Default = 30 days

    end_date = df["DATE"].max()

    start_date = end_date - pd.Timedelta(days=delta)

    df = df[
        (df["DATE"] >= start_date) &
        (df["DATE"] <= end_date)
        ]

    # -----------------------------
    # Selection box - Multi-Select
    # -----------------------------
    selected_columns = st.sidebar.multiselect(
        "Log Graph | Select Supplier",
        options=quantity_columns,
        default=["Speed Vietnam", "Elleci"]
    )

    column_name = ", ".join(selected_columns)

    # -----------------------------
    # Create Plotly graph
    # -----------------------------
    fig = go.Figure()

    for col in selected_columns:
        fig.add_trace(
            go.Scatter(
                x=df["DATE"],
                y=df[col],
                mode="lines+markers",
                name=col
            )
        )

    # -----------------------------
    # Format graph
    # -----------------------------
    fig.update_layout(
        title=column_name + " | Inventory History | " + range,
        xaxis_title="Date",
        yaxis_title="Quantity",
        hovermode="x unified",
        height=600,
        template="plotly_white",
        legend_title="Supplier / Category"
    )

    fig.update_xaxes(
        tickformat="%m/%d/%Y"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    return


def median_table_OLD(df_sales_and_price):
    df = df_sales_and_price

    # ======== DO NOT DELETE ==========
    # st.write(df)
    # ut.download_csv(df, 'D.Load')
    # ================================

    # Convert PRICE column to integer and calculate the median
    df['PRICE'] = df['PRICE'].astype(int)
    price_arr = df['PRICE'].tolist()
    price_arr.sort()
    median = round(statistics.median(price_arr), 0)

    # Split DataFrame based on the median ==============
    df_less_than_median = df[df['PRICE'] < median]
    df_equal_to_median = df[df['PRICE'] == median]
    df_greater_than_median = df[df['PRICE'] > median]

    # Calculate metrics for prices < median price ==========
    total_sku1 = df_less_than_median['SKU'].count()
    total_sale1 = df_less_than_median['TOTAL'].sum()
    total_turnover1 = round(df_less_than_median['TURNOVER_%'].sum(), 0)

    # Calculate metrics for prices = median price ============
    total_sku3 = df_equal_to_median['SKU'].count()
    total_sale3 = df_equal_to_median['TOTAL'].sum()
    total_turnover3 = round(df_equal_to_median['TURNOVER_%'].sum(), 0)

    # Calculate metrics for prices > median price  =============
    total_sku2 = df_greater_than_median['SKU'].count()
    total_sale2 = df_greater_than_median['TOTAL'].sum()
    total_turnover2 = round(df_greater_than_median['TURNOVER_%'].sum(), 0)

    # Create a summary DataFrame for median comparison
    df_median = pd.DataFrame({'COST': ['< $' + utils.format_num(median), '=  $' + utils.format_num(median), '>  $' + utils.format_num(median)],
                              'SKU': [total_sku1, total_sku3, total_sku2],
                              'SALES QTY': [total_sale1, total_sale3, total_sale2],
                              'REVENUE %': [total_turnover1, total_turnover3, total_turnover2],
                             })

    # Generate the table visualization using Plotly
    fig = go.Figure(data=[go.Table(
            columnwidth=[11, 8, 15, 16],

            header=dict(values=list(df_median.columns),
                    fill_color=color_hex(234),
                    font_color='white',
                    line_color='white',
                    font_size=14,
                    height=28,
                    align=['center']),

            cells=dict(
                    values=[df_median.COST, df_median.SKU, df_median['SALES QTY'], df_median['REVENUE %']],
                    font_size=14,
                    height=28,
                    fill_color=color_hex(220),
                    line_color='white',
                     align=['center']))
            ])

    # Adjust the layout and render the table
    fig.update_layout(width=280, height=120, margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, use_container_width=False)

    # Provide a download option for the DataFrame
    utils.download_csv(df, 'Download Data')
    return



