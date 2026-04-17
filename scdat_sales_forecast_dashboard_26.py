import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode
import pandas as pd
import time
import plotly.graph_objects as go
import calendar
from datetime import datetime
from plotly.subplots import make_subplots
import statistics

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_colors_26 import color_hex

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

    utils.show_header(' Inventory')

    # get total forecast quantity for stock calculation << ==========================================
    df_forecast = data.forecast_df(datafile_location, forecast_month)

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
    df_parts = values[5]
    df_box = values[6]
    df_refurb = values[7]
    df_l_container = values[8]
    df_retail = values[9]
    retail_models = values[10]
    df_faucet = values[11]
    df_bathtub = values[12]

    # st.write(df_wh['QTY'].sum())
    total_wh1 = utils.format_num(df_wh1['QTY'].sum())
    total_wh4 = utils.format_num(df_wh4['QTY'].sum())
    total_parts = utils.format_num(df_parts['QTY'].sum())
    total_wh2 = utils.format_num(df_wh2['QTY'].sum())
    total_box = utils.format_num(df_box['QTY'].sum())
    total_refurb = utils.format_num(df_refurb['QTY'].sum())
    total_wh3 = utils.format_num(df_wh3['QTY'].sum())
    total_l_container = utils.format_num(df_l_container['QTY'].sum())
    total_lowes_model = utils.format_num(df_retail['QTY'].sum())
    total_faucets = utils.format_num(df_faucet['QTY'].sum())
    total_bathtubs = utils.format_num(df_bathtub['QTY'].sum())

    df_all = pd.DataFrame({'WH1': [total_wh1],
                           'WH2': [total_wh2],
                           'WH3': [total_wh3],
                           'WH4': [total_wh4],
                           'L-CONTAINER': [total_l_container],
                           'REFURBISHED': [total_refurb],
                           'ACCESSORIES': [total_parts],
                           'PACKING BOX': [total_box],
                           'LOWES MODELS': [total_lowes_model],
                           'FAUCETS': [total_faucets],
                           'BATHTUBS': [total_bathtubs],

                           })
    stock = round((df_wh1['QTY'].sum() + df_wh2['QTY'].sum() + df_wh3['QTY'].sum() + df_wh4['QTY'].sum())/forecast, 2)

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
        f' line-height:0em; margin-top:-10px"> Warehouse Inventory Mix | Stock: {stock} month | {utils.get_todays_date()}</p>',
        unsafe_allow_html=True)

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
                    df_all['ACCESSORIES'], df_all['PACKING BOX'], df_all['LOWES MODELS'], df_all['FAUCETS'], df_all['BATHTUBS']],

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
        utils.download_csv(df_wh1, 'Download WH1')
        utils.download_csv(df_wh2, 'Download WH2')
        utils.download_csv(df_wh3, 'Download WH3')
        utils.download_csv(df_wh4, 'Download WH4')
        utils.download_csv(df_fba, 'Download FBA')
        utils.download_csv(values[9], 'Download LOWES')
        utils.download_csv(values[11], 'Download FAUCETS')
        utils.download_csv(values[12], 'Download BATHTUBS')

        utils.download_csv(df_l_container, 'Download L-CONTAINER')
        utils.download_csv(df_parts, 'Download PARTS')
        utils.download_csv(df_refurb, 'Download REFURBISHED')
        utils.download_csv(df_box, 'Download PACKING BOX')

    return

def median_table(df_sales_and_price):
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

def sales_anatomy_dashboard(datafile_location):
    utils.show_header('Sales Anatomy')

    months = list(calendar.month_name)[1:]
    current_month_idx = datetime.now().month

    current_year = datetime.now().year
    years = [current_year - i for i in range(3)]

    month = st.sidebar.selectbox("Select a Month", months, current_month_idx-1)

    year = st.sidebar.selectbox("Select a Year", years)

    arr = data.sales_anatomy_df(datafile_location, month, str(year))

    col1, col2 = st.columns([4.4, 1])

    with col1:

        if month == months[current_month_idx-1]  and year == current_year:

            txt = month + ' - ' + str(year) + ' | Sales Anatomy | ' +  utils.get_todays_date()

        else:
            txt = month + ' - ' + str(year) + ' | Sales Anatomy'

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(280)}; text-align:left; font-size: 20px ;border-radius:1%;'
            f' line-height:0em; margin-top:0px"> {txt} </p>',
            unsafe_allow_html=True)

        # --------------- PRICE DISTRIBUTION BAR GRAPH -------------------------------
        df_price = arr[0]
        total_zen = arr[2]
        total_fba = arr[3]

        df_price_less_1k = df_price[df_price['PRICE'] <= 1000].copy()

        df_price_greater_1k = df_price[df_price['PRICE'] > 1000].copy()

        sku_greater_1k = df_price_greater_1k['SKU'].sum()
        sales_greater_1k = df_price_greater_1k['SALES'].sum()
        turnover_greater_1k = df_price_greater_1k['TURNOVER_%'].sum()

        # df_price_less_1k.loc[len(df_price_less_1k)-1] = ['1000', sku_greater_1k, sales_greater_1k, turnover_greater_1k]
        df_price_less_1k.loc[len(df_price_less_1k)-1] = [1000, sku_greater_1k, sales_greater_1k, turnover_greater_1k]



        # add REMARK = SALES [SKU]
        df_price_less_1k['REMARK'] = df_price_less_1k.apply(lambda x: str(utils.format_num(x.iloc[2])) +
                                                            ' [' + str(utils.format_num(x.iloc[1])) + ']', axis=1)

        fig1 = make_subplots(specs=[[{"secondary_y": True}]])

        fig1.add_trace(go.Bar(x=df_price_less_1k['PRICE'],
                              y=df_price_less_1k['SALES'],
                              marker_color=color_hex(10),
                              name='SALES',
                              text=df_price_less_1k['REMARK'],
                              ),
                       secondary_y=False
                       )

        fig1.update_traces(textposition="outside")

        fig1.update_layout(xaxis_title='DEALER COST', yaxis_title='QTY SOLD [SKU]',
                           font=dict(
                               family="Book Antiqua",
                               size=14,
                               color=color_hex(10)),  # color1),
                           )

        fig1.update_yaxes(range=[0, df_price_less_1k['SALES'].max() * 1.1])

        x_axis = df_price_less_1k['PRICE'].tolist()

        fig1.update_layout(
            xaxis=dict(
                # tickmode='linear',
                tickmode='array',
                tick0=25,
                tickvals=x_axis,
                # dtick=25
            ))

        # ================= TURNOVER % =========================
        fig1.add_trace(go.Scatter(x=df_price_less_1k['PRICE'],
                                  y=df_price_less_1k['TURNOVER_%'],
                                 #fill='tozeroy',  # fill down to xaxis
                                 #fillcolor='rgba(255, 127, 36, 0.1)',
                                 mode='lines',
                                 line={'dash': 'solid', 'color': color_hex(47)},
                                 name="REVENUE %"
                                  ),
                                secondary_y=True
                       )

        fig1.update_yaxes(title_text="REVENUE %", range=[0, df_price_less_1k['TURNOVER_%'].max() * 1.1], secondary_y=True)
        fig1.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=13), x=0.45, y=0.85))

        fig1.update_xaxes(
            tickangle=90,  # rotates the tick labels
            #showgrid=True,
            gridwidth=0.5,
            gridcolor='lightgrey',
        )

        fig1.update_yaxes(
            showgrid=True,
            gridwidth=2,
            gridcolor='lightgrey',
            secondary_y=False
        )

        fig1.update_yaxes(
            # dtick="M1",  # sets minimal interval to month
            # tickformat="%d-%b-%Y",  # "%b %Y",  # sets the date format
            # tickangle=90,  # rotates the tick labels
            showgrid=True,
            gridwidth=1,
            gridcolor=color_hex(344),
            secondary_y=True
        )

        fig1.update_layout(height=480, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig1, width='stretch')

    with col2:
        # ======================== ZEN & FBA SALES PIE ================================
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(91)}; text-align: center; font-size: 16px ;border-radius:1%;'
            f' line-height:0em; margin-top:0px">ZEN & FBA SALES  </p>', unsafe_allow_html=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Pie(
            labels=['ZEN SALES', 'FBA SALES'],
            values=[total_zen, total_fba],
            showlegend=False,
            hole=0.50,
                            ),
                       )

        fig2.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=14), x=0.72, y=0.5))

        fig2.update_traces(textposition='inside', textinfo='percent',
                           marker=dict(colors=[color_hex(280), color_hex(117)], line=dict(color='white', width=1.5)))

        fig2.add_annotation(x=0.5, y=0.55,
                            text='ZEN: ' + str(utils.format_num(total_zen)),
                            font=dict(size=16, family='Book Antiqua', color=color_hex(280)),
                            showarrow=False)

        fig2.add_annotation(x=0.5, y=0.45,
                            text='FBA: ' + str(utils.format_num(total_fba)),
                            font=dict(size=16, family='Book Antiqua', color=color_hex(117)),
                            showarrow=False)

        fig2.update_layout(height=200, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig2, width='stretch')

        # ======================== MEDIAN PRICE SALES ================================
        st.write('')
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(91)}; text-align: center; font-size: 16px ;border-radius:1%;'
            f' line-height:0em; margin-top:-5px"> MEDIAN COST SALES</p>', unsafe_allow_html=True)

        median_table(arr[4])

    # ====================== PRODUCT, MATERIA, MOUNTING & BOWL ================================================
    col_a, col_b, col_c, col_d, col_e = st.columns([1, 1, 1, 1, 1])
    with col_a:
        # -------------- PRODUCT TABLE -------------------------------------------
        df = arr[1]
        df_product = df[0]
        df_product['Color1'] = ''

        # set bg colors ==================================
        for c in range(0, len(df_product)-1):
            df_product.at[c, 'Color'] = 'rgb(209, 238, 238)'

        df_product.at[len(df_product), 'Color'] = 'rgb(154, 192, 205)'

        cols = df_product.columns

        fig = go.Figure()

        fig.add_trace(go.Table(
            columnwidth=[18, 10, 14],

            header=dict(values=(cols[0], cols[1], cols[2]), #list(df_product.columns),
                        fill_color=color_hex(118),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=25,
                        align=['left', 'center']),
            cells=dict(
                values=[df_product.PRODUCT, df_product.SKU, df_product.TOTAL],
                font_size=14,
                height=25,
                fill_color=[df_product['Color']],
                line_color='white',
                align=['left', 'right'])),
            # row=1, col=1,
        )

        fig.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_c:
        # -------------- MOUNTING -------------------------------------------
        df = arr[1]
        df_mount = df[2]

        # set bg colors ==================================
        for c in range(0, len(df_mount) - 1):
            df_mount.at[c, 'Color'] = 'rgb(255, 228, 196)'  # color 16

        df_mount.at[len(df_mount), 'Color'] = 'rgb(238, 197, 145)'  # color 34

        cols = df_mount.columns

        fig = go.Figure()
        fig.add_trace(go.Table(
            columnwidth=[18, 10, 14],

            header=dict(values=(cols[0], cols[1], cols[2]),
                        fill_color=color_hex(234),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=25,
                        align=['left', 'center']),
            cells=dict(
                values=[df_mount.MOUNTING, df_mount.SKU, df_mount.TOTAL],
                font_size=14,
                height=25,
                fill_color=[df_mount['Color']],
                line_color='white',
                align=['left', 'right'])),
                # row=1, col=2
                )

        fig.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        # -------------- MATERIAL -------------------------------------------
        df = arr[1]
        df_material = df[1]
        df_material.at[1, 'MATERIAL'] = 'Color SS'

        # set bg colors ==================================
        for c in range(0, len(df_material) - 1):
            df_material.at[c, 'Color'] = 'rgb(209, 238, 238)'

        df_material.at[len(df_material), 'Color'] = 'rgb(154, 192, 205)'

        cols = df_material.columns
        # st.write(df_material)
        # st.stop()

        fig = go.Figure()
        fig.add_trace(go.Table(
            columnwidth=[18, 10, 14],

            header=dict(values=(cols[0], cols[1], cols[2]),
                        fill_color=color_hex(75),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=25,
                        align=['left', 'center']),
            cells=dict(
                values=[df_material.MATERIAL, df_material.SKU, df_material.TOTAL],
                font_size=14,
                height=25,
                fill_color=[df_material['Color']],
                line_color='white',
                align=['left', 'right'])),
            #row=1, col=3,
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        # -------------- BOWL -------------------------------------------
        df = arr[1]
        df_bowl = df[3]
        blank_row = pd.DataFrame([[None] * len(df_bowl.columns)], columns=df_bowl.columns)

        # Split the DataFrame: all but last row, then last row
        df_bowl_top = df_bowl.iloc[:-1]
        df_bowl_bottom = df_bowl.iloc[-1:]

        # Concatenate: top + blank + blank + bottom
        df_bowl = pd.concat([df_bowl_top, blank_row], ignore_index=True)
        df_bowl = pd.concat([df_bowl, blank_row, df_bowl_bottom], ignore_index=True)

        df_bowl.fillna('', inplace=True)

        # set bg colors ==================================
        for c in range(0, len(df_bowl) - 1):
            df_bowl.at[c, 'Color'] = 'rgb(255, 228, 196)'  # color 16

        df_bowl.at[len(df_bowl)-1, 'Color'] = 'rgb(238, 197, 145)'  # color 34

        cols = df_bowl.columns

        fig = go.Figure()
        fig.add_trace(go.Table(
            columnwidth=[18, 10, 14],

            header=dict(values=(cols[0], cols[1], cols[2]),
                        fill_color=color_hex(10),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=25,
                        align=['left', 'center']),
            cells=dict(
                values=[df_bowl.BOWL, df_bowl.SKU, df_bowl.TOTAL],
                font_size=14,
                height=25,
                fill_color=[df_bowl['Color']],
                line_color='white',
                align=['left', 'right'])),
            # row=2, col=2,
        )

        # height = len(df_product) * 28 + 28
        fig.update_layout(height=300, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig, use_container_width=True)

    # -------------- COLLECTION TABLE -------------------------------------------
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(280)}; text-align:left; font-size: 20px ;border-radius:1%;'
        f' line-height:0em; margin-top:12px"> {month} | Sales Anatomy: Collection | {utils.get_todays_date()}</p>', unsafe_allow_html=True)

    mygrid = utils.make_grid(5, 5)  # (rows, cols)
    col = 0
    row = 0

    df = arr[1]
    df_collection = df[4]

    total_rows = len(df_collection)

    # st.stop()
    # ++++++++++++++++++++++++++++ ADJUST CHUNK SIZE +++++++++++++++++++++++++++++++++++++++++++
    if total_rows % 4 == 0:
        chunk_size = int(total_rows/4)

    else:
        blank_row = pd.DataFrame([[None] * len(df_collection.columns)], columns=df_collection.columns)

        # Split the DataFrame: all but last row, then last row
        df_collection_top = df_collection.iloc[:-1]
        df_collection_bottom = df_collection.iloc[-1:]

        if total_rows % 4 == 3:
            # Concatenate: top + blank
            df_collection = pd.concat([df_collection_top, blank_row], ignore_index=True)

        elif total_rows % 4 == 2:
            # Concatenate: top + blank * 2 + bottom
            df_collection = pd.concat([df_collection_top, blank_row], ignore_index=True)
            df_collection = pd.concat([df_collection, blank_row], ignore_index=True)

        elif total_rows % 4 == 1:
            # Concatenate: top + blank * 3 + bottom
            df_collection = pd.concat([df_collection_top, blank_row], ignore_index=True)
            df_collection = pd.concat([df_collection, blank_row], ignore_index=True)
            df_collection = pd.concat([df_collection, blank_row], ignore_index=True)

        # Concatenate: top + bottom
        df_collection = pd.concat([df_collection, df_collection_bottom], ignore_index=True)
        df_collection.fillna('', inplace=True)

        # resize chunk -----------------
        chunk_size = int(len(df_collection) / 4)

    # set bg colors ==================================
    for c in range(0, len(df_collection) - 1):
        df_collection.at[c, 'Color'] = 'rgb(255, 228, 196)'  # color 16

        df_collection.at[len(df_collection)-1, 'Color'] = 'rgb(238, 197, 145)'  # color 34

    # ================ DISPLAY FIGURE ==================================================
    for n in range(0, total_rows, chunk_size):
        df_chunk = df_collection.iloc[n:n + chunk_size]
        # st.write(df_chunk)

        cols = df_chunk.columns

        fig = go.Figure(data=[go.Table(
            columnwidth=[16, 10, 12],

            header=dict(values=(cols[0], cols[1], cols[2]),
                        fill_color=color_hex(234),
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=24,
                        align=['left', 'center']),
            cells=dict(
                values=[df_chunk.COLLECTION, df_chunk.SKU, df_chunk.TOTAL],
                font_size=14,
                height=24,
                fill_color=[df_chunk['Color']],
                line_color='white',
                align=['left', 'right']))
        ])

        height = len(df_chunk) * 25 + 24
        fig.update_layout(height=height, margin=dict(l=0, r=0, b=0, t=3))
        mygrid[row][col].plotly_chart(fig, use_container_width=True)
        col = col + 1
    utils.download_csv(df_collection, 'Download Collection')

    # =================Items Sold ===========================================
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(280)}; text-align:left; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:1px"> Items Sold </p>', unsafe_allow_html=True)

    col_f, col_g = st.columns([1, 1])
    with col_f:
        df_dealer_cost = arr[4]
        df_dealer_cost = df_dealer_cost[['SKU', 'SUPPLIER', 'PRODUCT', 'PRICE']]
        df_dealer_cost = df_dealer_cost.sort_values('SKU', ascending=True)

        # build AgGrid options
        gb = GridOptionsBuilder.from_dataframe(df_dealer_cost)
        gb.configure_grid_options(rowHeight=25)
        gb.configure_grid_options(headerHeight=25)
        gb.configure_grid_options(enableCellTextSelection=True)
        grid_options = gb.build()

        height = 450
        AgGrid(df_dealer_cost, grid_options, height=height, fit_columns_on_grid_load=True)

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(210)}; text-align:left; font-size: 16px ;border-radius:1%;'
            f' line-height:0em; margin-top:1px"> Sku Count | {len(df_dealer_cost)} </p>', unsafe_allow_html=True)

    # col4, col5 = st.columns(2)
    with col_g:
        df_turnover = df_price
        df_turnover = df_turnover.rename(columns={'PRICE': 'PRICE RANGE'})
        AgGrid(df_turnover, hight=550, fit_columns_on_grid_load=True)

        df_above_1k = df_turnover[df_turnover['PRICE RANGE'] >= 1000]
        st.write('Above 1k | ' + str(round(df_above_1k['TURNOVER_%'].sum(), 2)) + ' %')

    return
