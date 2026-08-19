import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode

import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import datetime
from datetime import date
from datetime import datetime

#from dateutil.relativedelta import relativedelta
#from datetime import date, timedelta

import calendar
import os

import statistics
from pathlib import Path, PureWindowsPath    # for Window & Mac OS path-slash '\' or '/'
import math
import glob

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex

# from scdat_colors_26 import color_hex

SUPPLIER_LIST = ["ALL",
                 "Speed",
                 "Speed Vietnam",
                 "Elleci",
                 "Stile Libero",
                 "Plados",
                 "Aquacubic",
                 "Xindeli",
                 "Galassia",
                 "Nicos",
                 "Bomeijia",
                 "Yalos",
                 "Wisdom",
                 "Carysil",
                 "UAE Fireclay",
                 "Changie",
                 "Huayi",
                 "CAE Sanitary"
                 ]
SUPPLIER_LIST.sort()


def select_month():
    month_names = list(calendar.month_name)[1:]
    current_month_no = date.today().month
    return st.sidebar.selectbox("MONTH", month_names, index=current_month_no - 1)

def select_year():
    current_year = date.today().year
    years = [current_year - i for i in range(3)]
    return st.sidebar.selectbox("YEAR", years)


def filter_dataframe(df, supplier, model):
    if supplier != 'ALL':
        df = df[df["SUPPLIER"] == supplier]
    if model.upper() != 'ALL':
        df = df.loc[lambda row: row['SKU'].str.startswith(model.upper())]
        df.reset_index(drop=True, inplace=True)  # order index
        df.index = range(1, df.shape[0] + 1)
    return df

def display_one_month_sales(datafile_location):
    # __________ Create Select Box Inputs _____________________-
    month = select_month()
    year = select_year()
    supplier = st.sidebar.selectbox("SUPPLIER", SUPPLIER_LIST)
    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    # ____________ Read Data File ________________________________
    df = data.one_month_sales_df(datafile_location, month, str(year)).fillna(0)

    # ____________ Filter as per Supplier or Models _______________
    df_filtered = utils.supplier_model_query(df, supplier, model)

    # _________ Calculate Totals _________________________________
    total_amazon = df_filtered['AMAZON'].sum()
    total_zen = df_filtered['ODDO'].sum()
    total_sales = df_filtered['TOTAL'].sum()

    total_sink = df_filtered.loc[
        ~df_filtered['SKU'].str.startswith('RVA', na=False), 'TOTAL'
    ].sum()

    total_accessories = total_sales - total_sink

    # --- Header Text ---
    base_text = f"Monthly Sales | {month}-{year}"

    if model.upper() == 'ALL':
        base_text += f" | Supplier: {supplier}"
    else:
        base_text += f" | Model: {model.upper()}"

    metrics_text = (
        f" | Amazon Sales: {utils.format_num(total_amazon)}"
        f" | ZEN Sales: {utils.format_num(total_zen)}"
        f" | Sink: {utils.format_num(total_sink)}"
        f" | Accessories: {utils.format_num(total_accessories)}"
        f" | Total: {utils.format_num(total_sales)}"
    )

    full_text = base_text + metrics_text

    # st.markdown(
    #     f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; '
    #     f'text-align:left; font-size: 18px; border-radius:2%; line-height:0em; margin-top:5px">'
    #     f'{full_text}</p>',
    #     unsafe_allow_html=True
    # )

    # txt = " Warehouse Inventory Mix | Stock: " + str(stock) + " month | " + utils.get_todays_date()
    utils.show_header(full_text)

    # --- AgGrid Setup ---
    column_settings = {
        'SKU': 100, 'SUPPLIER': 115, 'MATERIAL': 100, 'PRODUCT': 200,
        'MOUNTING': 120, 'BOWL': 90, 'COLLECTION': 120, 'STATUS': 90,
        'FBA': 80, 'AMAZON': 80, 'ODDO': 80, 'TOTAL': 80
    }

    gb = GridOptionsBuilder.from_dataframe(df_filtered)

    for col, width in column_settings.items():
        if col in df_filtered.columns:  # safer
            gb.configure_column(col, wrapText=False, width=width)

    grid_options = gb.build()

    height = min(max(len(df_filtered) * 30 + 25, 80), 700)

    AgGrid(
        df_filtered,
        gridOptions=grid_options,
        height=height,
        fit_columns_on_grid_load=True
    )

    # --- Download ---
    utils.download_csv(df_filtered, f"Download Sales {month}-{year}")

def sales_anatomy_dashboard(datafile_location):

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

        # st.markdown(
        #     f'<p style="font-family: Book Antiqua; color: {color_hex(280)}; text-align:left; font-size: 20px ;border-radius:1%;'
        #     f' line-height:0em; margin-top:0px"> {txt} </p>',
        #     unsafe_allow_html=True)

        utils.show_header(txt)

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

    with col2:      # _____________ ZEN & FBA SALES PIE __________________________

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(91)}; text-align: center; font-size: 16px ;border-radius:1%;'
            f' line-height:0em; margin-top:0px">ZEN & AMAZON SALES  </p>', unsafe_allow_html=True)

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
                            text='AMAZON: ' + str(utils.format_num(total_fba)),
                            font=dict(size=12, family='Book Antiqua', color=color_hex(117)),
                            showarrow=False)

        fig2.update_layout(height=210, margin=dict(l=0, r=0, b=0, t=0))
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

def current_month_sales_graph(datafile_location, forecast_month, suppliers):

    s = forecast_month
    month = s.split("_")[1].split("-")[0]  # 'Apr'
    current_month = calendar.month_name[list(calendar.month_abbr).index(month)]
    year = s.split("_")[1].split("-")[1]

    df1 = data.one_month_sales_df(datafile_location, current_month, year)
    df1 = df1[['SKU', 'TOTAL']]

    suppliers.remove("ALL")

    suppliers.extend(["KANGDE SILICONE", "SPEED_RVA", 'LB Plast'])

    df_list = []
    for s in suppliers:
        temp = data.forecast_df(datafile_location, forecast_month, s)
        temp = temp[['SKU', 'FORECAST', 'SUPPLIER']]

        df_list.append(temp)

    df2 = pd.concat(df_list, ignore_index=True)
    df2 = df2[df2['SKU'] !=0]

    df = pd.merge(df2, df1, on=["SKU"], how='left')
    df = df[['SKU', 'SUPPLIER', 'FORECAST', 'TOTAL']]

    # ________ get FBA sales _______________________________
    df_fba, df_nonfba = data.amazon_fba_nonfba_df(datafile_location, month, year)

    # st.write(df_fba)

    df = pd.merge(df, df_fba, on=["SKU"], how='left')

    # ______________ Remove Lines If SKU has BOTH NaN + empty strings ______________________
    df = df[df['SKU'].notna() & (df['SKU'].str.strip() != '')]

    # ___________Create a copy _________________________________
    df_all = df.copy()


    # ___________ Get All Accessories Data Only _________________________________________
    df_acc = df.loc[lambda row: row['SKU'].str.startswith('RVA')]   # all accessories
    forecast_acc = df_acc['FORECAST'].sum()
    total_acc = df_acc['TOTAL'].sum()
    total_acc_fba = df_acc['FBA QTY'].sum()


    # _____________ Remove All Accessories Data ________________________________________
    # df = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # remove all accessories

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')  # accessories, boxes, dummy faucets, faucet parts
    df = utils.exclude_sku_prefixes(df, prefixes)

    # ______________ Group by Suppliers __________________________________________
    df = df.groupby(['SUPPLIER'])[['FORECAST', 'TOTAL', 'FBA QTY']].sum().reset_index()  # <<<<<<<<<< change in syntex

    # ______________ Add Accessories Data at the Bottom _________________________
    df.loc[len(df)] = ["ACCESSORIES", forecast_acc, total_acc, total_acc_fba]      # add all accessories


    # _____________ Get FBA Sales % ___________________________________________
    df['FBA_PERCENT'] = round(df['FBA QTY'] * 100 / df['FORECAST'], 2)

    # _____________ Get Remaining Sales % ____________________________________
    df['PERCENT'] = round((df['TOTAL']-df['FBA QTY']) * 100 / df['FORECAST'], 2)

    # ____________ Calculate % Left _______________________________________
    df['PERCENT_LEFT'] = round(100 - df['PERCENT'] - df['FBA_PERCENT'], 2)

    # _____________ If % is less than Zero then make it Zero _________________________
    df['PERCENT_LEFT'] = df['PERCENT_LEFT'].clip(lower=0)

    df = df.rename(columns={'TOTAL': 'TOTAL SALES'})

    # st.write(df)
    total_fba_percent = str((df['FBA QTY'].sum() * 100/df['TOTAL SALES'].sum()).round(1))

    fig = go.Figure()

    fig.add_trace(go.Bar(       # _____________ FBA Percentage ______________________
        y=df['FBA_PERCENT'],
        x=df['SUPPLIER'],
        name='FBA Sales (' + total_fba_percent + '%)',
        # text=df['FBA QTY'],
        marker=dict(
            color=color_hex(275),
            line=dict(color='rgba(0, 139, 139, 1.0)', width=1),
        )
    ))

    fig.add_trace(go.Bar(       # _____________ Total Percentage ______________________
        y=df['PERCENT'],
        x=df['SUPPLIER'],
        name='Total Sales',
        # text=df['PERCENT'].astype(str) + ' %',
        text=df['TOTAL SALES'],
        marker=dict(
            color=color_hex(66),
            line=dict(color='rgba(0, 139, 139, 1.0)', width=1),
        ),

    ))

    fig.add_trace(go.Bar(       # _____________ Forecast Percentage (100%)  ______________________
        y=df['PERCENT_LEFT'],
        x=df['SUPPLIER'],
        name='Forecast',
        text=df['FORECAST'],
        marker=dict(
            color='white',  # 'rgba(160, 178, 139, 0.4)',
            line=dict(color='rgba(0, 139, 139, 1.0)', width=1),
        )
    ))

    fig.update_layout(barmode='stack')
    fig.update_traces(textposition="inside")
    fig.update_layout(xaxis_title='', yaxis_title='PERCENTAGE (%)',
                       font=dict(
                           family="Arial",
                           size=12,
                           color=color_hex(118)),  # 'black'),
                       )

    fig.update_layout(
        legend=dict(
            orientation="h",  # horizontal legend
            yanchor="bottom",
            y=1.02,  # slightly above the plot
            xanchor="center",
            x=0.5,  # centered horizontally

            font = dict(
             family="Arial Black",
             size=16,
             color="black",
                 )
            )
        )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="lightgray",
        gridwidth=3,
        griddash="dot",  # "solid", "dot", "dash", "dashdot"
        layer = "above traces",
    )

    now = datetime.now()
    total_days = calendar.monthrange(now.year, now.month)[1]
    target = now.day * 100 / total_days
    target = math.floor(target)

    # ________________ calculate total sales from one month sale (df1) ____________________________
    total_faucet = df1[df1["SKU"].str.startswith("RVF")]['TOTAL'].sum()
    total_bathtub = df1[df1["SKU"].str.startswith("RVB6")]['TOTAL'].sum()
    total_accessories = df1[df1["SKU"].str.startswith("RVA")]['TOTAL'].sum()
    total_sink = df1['TOTAL'].sum() - (total_faucet + total_bathtub + total_accessories)

    # _______________ Calculate Projected Sales _________________________________________
    if now.day == 1:
        projection_factor = 1

    else:
        projection_factor = total_days / (now.day - 1)

    sink_projected = total_sink * projection_factor
    bathtub_projected = total_bathtub * projection_factor
    faucet_projected = total_faucet * projection_factor
    accessories_projected = total_accessories * projection_factor

    # ______________ Create Annotation Text _____________________________________
    annotation_text = utils.get_todays_date() + " >> "\
                      + ' Sink: ' + str(utils.format_num(total_sink)) \
                      + ' | Bathtub: ' + str(utils.format_num(total_bathtub)) \
                      + ' | Faucet: ' + str(utils.format_num(total_faucet)) \
                      + ' | Accessories: ' + str(utils.format_num(total_accessories)) + ' '\


    if 5 <= target <= 100:      # ______ horizontal line is visible if the condition met _______
        fig.add_hline(y=target, line_width=1, line_dash="dash", line_color=color_hex(238),
                      annotation_text=annotation_text,
                      annotation_font=dict(
                          family="Arial Black",    #, sans-serif",  # font family
                          size=15,  # font size
                          color="black" # color_hex(274)  # font color
                      )
                      )

    # ______________________ Display Bar Graph ____________________________________
    col1, col2 = st.columns([1, 0.1])
    with col1:

        utils.show_header(month + ' Sales | Projected > '
                          + 'Sink: ' + str(utils.format_num(sink_projected))
                          + ' , Bathtub: ' + str(utils.format_num(bathtub_projected))
                          + ' , Faucet: ' + str(utils.format_num(faucet_projected))
                          + ' , Accessories: ' + str(utils.format_num(accessories_projected))
                          # + ' | ' + utils.get_todays_date()
                          )
        fig.update_layout(height=700, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, width='stretch')

        txt = 'Bar Graph Data'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        AgGrid(df)      # ____________ Show Bar Graph Data ________________
        utils.download_csv(df, 'Download Graph Data')

        utils.download_csv(df_all, 'Download df_all')
        utils.download_csv(df1, 'Download Sales')
        utils.download_csv(df2, 'Download Forecast')
      
    return

def display_quarterly_report_OLD(datafile_location, df, df_revenue_data):

    # st.write(df)

    first_year = df[0:1].iloc[0][0]
    first_year = first_year[4:7]

    total_rows = len(df)
    last_year = df[total_rows - 1: total_rows].iloc[0][0]
    last_year = last_year[4:7]

    q1 = ['Jan', 'Feb', 'Mar']
    q2 = ['Apr', 'May', 'Jun']
    q3 = ['Jul', 'Aug', 'Sep']
    q4 = ['Oct', 'Nov', 'Dec']

    quarters = [q1, q2, q3, q4]

    df_all_quarter = pd.DataFrame({'Supplier': []})

    for y in range(int(first_year), int(last_year)-1, -1):

        quarter_no = 1

        for m in range(0, len(quarters)):
            m1 = quarters[m][0] + '-' + str(y)
            m2 = quarters[m][1] + '-' + str(y)
            m3 = quarters[m][2] + '-' + str(y)

            df_quarter = df[(df['Month'] == m1) | (df['Month'] == m2) | (df['Month'] == m3)]

            if len(df_quarter) > 0:
                df_quarter = df_quarter.sum(numeric_only=True, axis=0).to_frame().reset_index()

                q = '20' + str(y) + '-' + 'Q' + str(quarter_no)
                df_quarter.columns = (['Supplier', q])

                df_all_quarter = pd.merge(df_all_quarter, df_quarter, on=['Supplier'], how='outer')

                quarter_no += 1

    df1 = df_all_quarter.set_index('Supplier').transpose().reset_index()
    df1 = df1.rename(columns={'index': 'Quarter'})
    df1 = df1.sort_values('Quarter', ascending=False)

    # st.write(df1)

    col1, col2 = st.columns([7.0, 1])
    with col1:
        text = 'Quarterly Sales Report'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
            f'margin-top:1px"> {text} </p>', unsafe_allow_html=True)

        cols = df1.columns
        fig = go.Figure(data=[go.Table(
        #columnwidth=[15, 18, 18, 16, 16, 16, 16, 14, 16, 16, 20, 18, 16, 16, 14, 14, 18, 18],

        columnwidth=[14,    # Quarter
                     16,    # Aquacubic
                     14,    # Bomeijia
                     20,    # CAE Sanitary
                     13,    # Carysil
                     14,    # Changie
                     12,    # Elleci
                     14,    # Galassia
                     11,    # Huayi
                     12,    # Nicos
                     13,    # Plados
                     13,    # Speed
                     22,    # Speed Vietnam
                     17,    # Stile Libero
                     19,    # UAE Fireclay
                     12,    # Wisdom
                     12,    # Xindeli
                     10,    # Yalos
                     12,    # Sink
                     16,    # Accessories
                     14],   # Revenue

        header=dict(values=list(cols),
                    fill_color=[color_hex(118)] + [color_hex(66)]*17 + [color_hex(234)] + ['grey'] + [color_hex(47)],
                    line_color='white',
                    font_color='white',
                    font_size=13,
                    height=28,
                    align=['left', 'center']),
        cells=dict(
            values=[df1[cols[0]], df1[cols[1]], df1[cols[2]], df1[cols[3]], df1[cols[4]],
                    df1[cols[5]], df1[cols[6]], df1[cols[7]], df1[cols[8]], df1[cols[9]], df1[cols[10]], df1[cols[11]], df1[cols[12]],
                    df1[cols[13]], df1[cols[14]], df1[cols[15]], df1[cols[16]], df1[cols[17]], df1[cols[18]], df1[cols[19]], df1[cols[20]]],
            font_size=13,
            height=28,
            fill_color=['lightblue'] + [color_hex(12)]*17 + ['lightpink', 'lightgrey'] + [color_hex(16)],
            line_color='white',
            align=['left', 'right']))
    ])
        fig.update_layout(width=700, height=8 * 28 - 3, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, use_container_width=True)
        ut.download_csv(df1, 'Download Quarterly Sales Report')

    # st.write(df1)
    # st.stop()
    display_supplier_wise_quarterly_report(datafile_location, df1, df_revenue_data)

    return


def display_sales_report_OLD(datafile_location, supplier_list):

    values = data.quarterly_revenue_df(datafile_location)
    df_revenue = values[0]
    df_revenue_data = values[1]

    supplier_list.sort()
    # st.write(supplier_list)
    # st.stop()

    col1, col2 = st.columns([6.4, 1])

    path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY' + '\\'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort(reverse=True)

    df_all_month = pd.DataFrame({})

    for i in range(0, len(source_files)):

        file_path = path + str(source_files[i])

        # get month name from file name
        file_name = str(source_files[i])  # get file name
        month_name = file_name.split('_')  # split file name based on '_'
        month_name = month_name[2][:-4]  # get last portion and remove .csv

        df = pd.read_csv(Path(PureWindowsPath(file_path)))

        df = df[['SKU', 'SUPPLIER', 'TOTAL']]

        df_sink = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
        df_accessories = df.loc[lambda row: row['SKU'].str.startswith('RVA')]

        df_all_supplier = pd.DataFrame({'Month': []})

        for j in range(0, len(supplier_list)):
            supplier = supplier_list[j]
            df_supplier = df_sink[df_sink['SUPPLIER'] == supplier]

            total_sales = df_supplier['TOTAL'].sum()

            df_month = pd.DataFrame({'Month': [month_name],
                                     supplier: [total_sales],
                                     })

            df_all_supplier = pd.merge(df_all_supplier, df_month, on=["Month"], how='outer')

        df_all_supplier['Sink'] = df_all_supplier.sum(numeric_only=True, axis=1)
        df_all_supplier['Accessories'] = df_accessories['TOTAL'].sum()

        df_all_month = pd.concat([df_all_month, df_all_supplier])

    # Add alternating 'color1' and 'color2' values in a new column
    if len(df_all_month) > 1:
        df_all_month['color'] = ['rgb(240, 248, 255)' if i % 2 == 0 else 'rgb(189, 215, 231)' for i in range(len(df_all_month))]
    else:
        df_all_month['color'] = ['rgb(189, 215, 231)']


    # st.write(df_all_month)
    #
    # df_transposed = df_all_month.T
    # st.write(df_transposed)
    #
    # st.stop()
    # col1, col2 = st.columns([2, 1])

    # with col1:
    cols = df_all_month.columns
    fig = go.Figure(data=[go.Table(

        columnwidth=[12,    # Month
                     16,    # Aquacubic
                     14,    # Bomeijia
                     19,    # CAE Sanitary
                     13,    # Carysil
                     14,    # Changie
                     12,    # Elleci
                     14,    # Galassia
                     11,    # Huayi
                     12,    # Nicos
                     13,    # Plados
                     13,    # Speed
                     21,    # Speed Vietnam
                     17,    # Stile Libero
                     18,    # UAE Fireclay
                     12,    # Wisdom
                     12,    # Xindeli
                     11,    # Yalos
                     12,    # Sink
                     16],   # Accessories

        header=dict(values=list(cols)[:-1],
                    fill_color=[color_hex(118)] + [color_hex(66)] * 17 + [color_hex(234), 'grey'],
                    line_color='white',
                    font_color='white',
                    font_size=13,
                    height=30,

                    align=['left', 'center']),
        cells=dict(
            values=[df_all_month[cols[0]], df_all_month[cols[1]], df_all_month[cols[2]], df_all_month[cols[3]], df_all_month[cols[4]],
                    df_all_month[cols[5]], df_all_month[cols[6]], df_all_month[cols[7]], df_all_month[cols[8]], df_all_month[cols[9]],
                    df_all_month[cols[10]], df_all_month[cols[11]], df_all_month[cols[12]], df_all_month[cols[13]], df_all_month[cols[14]],
                    df_all_month[cols[15]], df_all_month[cols[16]], df_all_month[cols[17]], df_all_month[cols[18]], df_all_month[cols[19]]
                    ],
            font_size=14,
            height=30,
            fill_color=[df_all_month.color],
            line_color='white',
            align=['left', 'right']))
    ])

    total_rows = len(df_all_month)
    first_month = df_all_month['Month'].tail(total_rows).values[0]
    last_month = df_all_month['Month'].tail(total_rows - 12).values[0]

    with col1:
        text = '13-Month Sales Report | ' + first_month + ' to ' + last_month + ' | ' + utils.get_todays_date()    # + ' | Total Months: 12' # + str(
        # len(' \                                                                                         'source_files))
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
            f'margin-top:4px"> {text} </p>', unsafe_allow_html=True)

        fig.update_layout(height=14*30-3, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, use_container_width=True)

        ut.download_csv(df_all_month, 'Download Sales Report')

    df_all_month = pd.merge(df_all_month, df_revenue, on=["Month"], how='left')
    # st.write(df_all_month)
    # st.stop()

    display_quarterly_report(datafile_location, df_all_month, df_revenue_data)

    return df_revenue_data

def display_sales_report_monthly(datafile_location):
    # ______________ Get file list in the directory 'Sales\\Monthly_Sales\\MONTHLY' _________________
    path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY' + '\\'
    source_files = os.listdir(Path(PureWindowsPath(path)))
    source_files.sort(reverse=True)

    # ____________ Get current price ________________________________
    # current_price = data.price_list_df(datafile_location)

    # _______________ Read all sales file and append _____________________
    df = pd.DataFrame({})
    df_sku = pd.DataFrame({})

    for i in range(0, len(source_files)):

        file_path = path + str(source_files[i])

        # ___________ get month name from file name _______________________
        file_name = str(source_files[i])  # get file name
        month_name = file_name.rsplit('_', 1)[-1].removesuffix('.csv')

        # st.write(month_name)
        # st.write(file_path)

        df_temp = pd.read_csv(
            Path(PureWindowsPath(file_path)),
            usecols=['SKU', 'SUPPLIER', 'TOTAL'],
            encoding='latin1',
        )

        # _______________ Remove Accessories (RVA), Faucet Parts (RVP), Packing Box (RBX) and Display (RDM) __________________
        prefixes = ('RVA', 'RVP', 'RBX', 'RDM')
        df_sink = utils.exclude_sku_prefixes(df_temp, prefixes)

        # ______________ Transpose data - Suppliers in column __________________
        df_sink = (
            df_sink.groupby('SUPPLIER', as_index=True)['TOTAL']
            .sum()
            .to_frame()
            .T
        )

        # ______________ Add total Sink Column __________________________
        df_sink['Total'] = df_sink.sum(axis=1)

        # _____________ Add accessories data in column _________________________
        df_accessories = df_temp.loc[lambda row: row['SKU'].str.startswith('RVA')]
        df_sink['Accessories'] = df_accessories['TOTAL'].sum()

        # ______________ Insert month name in the first column _______________
        df_sink.insert(0, 'MONTH', month_name)
        df_temp.insert(0, 'MONTH', month_name)

        # ___________ Reset index ________________________________
        df_sink = df_sink.reset_index(drop=True)

        if i == 0:
            df = df_sink
            df_sku = df_temp
        else:
            df = pd.concat([df, df_sink], ignore_index=True)
            df_sku = pd.concat([df_sku, df_temp], ignore_index=True)

    df = df.fillna(0)
    df_sku = df_sku.fillna(0)

    # _____________ Add alternating 'color1' and 'color2' values in a new column _________________
    if len(df) > 1:
        df['color'] = ['rgb(240, 248, 255)' if i % 2 == 0 else 'rgb(189, 215, 231)' for i in range(len(df))]
    else:
        df['color'] = ['rgb(189, 215, 231)']

    # ___________________ Create plotly table __________________________

    cols = df.columns
    fig = go.Figure(data=[go.Table(

        columnwidth=[12,    # Month
                     16,    # Aquacubic
                     14,    # Bomeijia
                     19,    # CAE Sanitary
                     13,    # Carysil
                     14,    # Changie
                     12,    # Elleci
                     14,    # Galassia
                     11,    # Huayi
                     12,    # Nicos
                     13,    # Plados
                     13,    # Speed
                     21,    # Speed Vietnam
                     17,    # Stile Libero
                     18,    # UAE Fireclay
                     12,    # Wisdom
                     12,    # Xindeli
                     11,    # Yalos
                     12,    # Sink
                     16],   # Accessories

        header=dict(values=list(cols)[:-1],
                    fill_color=[color_hex(118)] + [color_hex(66)] * 17 + [color_hex(234), 'grey'],
                    line_color='white',
                    font_color='white',
                    font_size=13,
                    height=30,

                    align=['left', 'center']),
        cells=dict(
            values=[df[c] for c in cols[:20]], # from cols[0] --> cols[19]
            font_size=14,
            height=30,
            fill_color=[df.color],
            line_color='white',
            align=['left', 'right']))
        ])

    # ______________ Display ____________________________
    col1, col2 = st.columns([14, 1])

    with col1:
        total_rows = len(df)
        first_month = df['MONTH'].tail(total_rows).values[0]
        last_month = df['MONTH'].tail(total_rows - 12).values[0]

        txt = '13-Month Sales Report | ' + first_month + ' to ' + last_month + ' | ' + utils.get_todays_date()    # + ' | Total Months: 12' # + str(
        utils.show_header(txt)

        fig.update_layout(height=14*30-3, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, width='stretch')

        utils.download_csv(df, 'Download Monthly Sales Report')

        df_quarter = display_sales_report_quarterly(df)
        display_quarterly_sales_report_supplier_wise(df_quarter, df_sku)


    return df

def display_sales_report_quarterly(df):
    header_txt = "Quarterly Report"
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(164)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em;'
        f' margin-top:5px">{header_txt}</p>', unsafe_allow_html=True)

    df['MONTH'] = pd.to_datetime(df['MONTH'], format='%b-%y')

    df_quarter = (
        df.groupby(df['MONTH'].dt.to_period('Q'))
        .sum(numeric_only=True)
        .sort_index(ascending=False)
    )

    df_quarter.index = (
            'Q' + df_quarter.index.quarter.astype(str)
            + '-' +
            df_quarter.index.year.astype(str)
    )

    quarter_colors = {
        'Q1': '#FFDEAD',  # 263
        'Q2': '#ADD8E6',  # 184
        'Q3': '#FFE4E1',  # 258
        'Q4': '#D3D3D3',  # 201
    }

    df_quarter['COLOR'] = (
        df_quarter.index.to_series()
        .str.extract(r'(Q\d)')[0]
        .map(quarter_colors)
    )

    df_quarter = df_quarter.reset_index()

    # ___________________ Create plotly table __________________________

    cols = df_quarter.columns
    fig = go.Figure(data=[go.Table(

        columnwidth=[14,  # Month
                     16,  # Aquacubic
                     14,  # Bomeijia
                     19,  # CAE Sanitary
                     13,  # Carysil
                     14,  # Changie
                     12,  # Elleci
                     14,  # Galassia
                     11,  # Huayi
                     12,  # Nicos
                     13,  # Plados
                     13,  # Speed
                     21,  # Speed Vietnam
                     17,  # Stile Libero
                     18,  # UAE Fireclay
                     12,  # Wisdom
                     12,  # Xindeli
                     11,  # Yalos
                     12,  # Sink
                     16],  # Accessories

        header=dict(values=list(cols)[:-1],
                    fill_color=[color_hex(118)] + [color_hex(66)] * 17 + [color_hex(234), 'grey'],
                    line_color='white',
                    font_color='white',
                    font_size=13,
                    height=30,

                    align=['left', 'center']),
        cells=dict(
            values=[df_quarter[c] for c in cols[:20]],   # from cols[0] --> cols[19]
            font_size=14,
            height=30,
            fill_color=[df_quarter.COLOR],
            line_color='white',
            align=['left', 'right']))
    ])

    fig.update_layout(height=15 * 30 - 3, margin=dict(l=0, r=0, b=0, t=0))

    st.plotly_chart(fig, width='stretch')

    utils.download_csv(df_quarter, 'Download Quarterly Sales Report')

    # display_quarterly_sales_report_supplier_wise(df_quarter)

    return df_quarter

def display_quarterly_sales_report_supplier_wise(df, df_sku):
    df = df.rename(columns={'Total': 'All Suppliers'})

    # ___________ Get suppliers name from column name ______________________
    suppliers = df.columns.tolist()
    suppliers.remove('MONTH')
    suppliers.remove('COLOR')

    # _______________ Move 'All Suppliers' to the first of the list _____________________
    idx = suppliers.index("All Suppliers")
    suppliers.insert(0, suppliers.pop(idx))

    # _____________ Show heading _____________________________________________________
    text = 'Quarterly Sales Summary | ' + utils.get_todays_date()
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(234)}; text-align:left; font-size: 20px ;border-radius:2%; line-height:0em; '
        f'margin-top:10px"> {text} </p>', unsafe_allow_html=True)

    st.write("")

    # ___________________ Create Grid for display _______________________
    mygrid = utils.make_grid(7, 5)
    col = row = 0

    for i in range (0, len(suppliers)):
        supplier = suppliers[i]

        df_out = (
            df[['MONTH', supplier]]
            .assign(
                YEAR=lambda x: x['MONTH'].str[-4:],
                QUARTER=lambda x: x['MONTH'].str[:2]
            )
            .pivot(
                index='YEAR',
                columns='QUARTER',
                values=supplier
            )
            .reset_index()
        )


        # _______________ Calculate Total and replace zero by "" __________________
        df_out = df_out.fillna(0)
        df_out['Total'] = df_out['Q1'] + df_out['Q2'] + df_out['Q3'] + df_out['Q4']
        df_out = df_out.replace(0, "")

        # ____________ Sort descending by year __________________________
        df_out = df_out.sort_values('YEAR', ascending=False)

        cols = df_out.columns

        fig = go.Figure(data=[go.Table(
                columnwidth=[16, 18],

                header=dict(values=list(cols),
                        fill_color=[color_hex(234)] + [color_hex(66)] * 4 + [color_hex(118)],
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=28,
                        align=['left', 'center']),

                cells=dict(
                    values=[df_out[c] for c in cols[:6]],   # from cols[0] --> cols[5]
                    font_size=13,
                    height=28,
                    fill_color=['lightpink'] + [color_hex(12)] * 4 + ['lightblue'],
                    line_color='white',
                    align=['center', 'right']))
                    ])

        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(25)}; text-align:left; font-size: 18px ;border-radius:2%; '
            f'line-height:0em; margin-top:0px"> {supplier} </p>', unsafe_allow_html=True)

        fig.update_layout(width=700, height=len(df_out) * 28 + 28, margin=dict(l=0, r=0, b=0, t=0))

        mygrid[row][col].plotly_chart(fig, use_container_width=True)

        # ____________ Grid positioning _______________
        col += 1
        if col == 5:
            col = 0
            row += 1

    # ___________________ Display Product-Level Summary _____________________
    txt = "Product-Level Summary"
    mygrid[row][col].markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(25)}; text-align:left; font-size: 18px ;border-radius:2%; '
        f'line-height:0em; margin-top:0px"> {txt} </p>', unsafe_allow_html=True)
    fig1 = display_sales_report_product_level_summary(df_sku)

    mygrid[row][col].plotly_chart(fig1, width='stretch')

    return


def display_sales_report_product_level_summary(df):
    # st.write(df)

    # _______________ Remove accessories ____________________________
    prefixes = ('RVA', 'RVP', 'RBX', 'RDM')
    df = utils.exclude_sku_prefixes(df, prefixes)

    df['MATERIAL'] = df['SKU'].str[:3]
    df['MATERIAL'] = (df['MATERIAL']
        .str.replace('RVH', 'HM', regex=False)
        .str.replace('RVU', 'HM', regex=False)
        .str.replace('RVQ', 'HM', regex=False)
        .str.replace('RVM', 'MM', regex=False)
        .str.replace('RVG', 'GR', regex=False)
        .str.replace('RVL', 'FC', regex=False)
                      )


    df = df.groupby(['MONTH', 'MATERIAL'])['TOTAL'].sum().to_frame().reset_index()
    # st.write(df)
    # st.stop()


    # Convert MONTH to datetime
    df['MONTH'] = pd.to_datetime(df['MONTH'], format='%b-%y')

    # Extract year
    df['YEAR'] = df['MONTH'].dt.year

    # Create summary table
    df_summary = (
        df.pivot_table(
            index='YEAR',
            columns='MATERIAL',
            values='TOTAL',
            aggfunc='sum',
            fill_value=0
        )
    )

    # Add total column
    df_summary['TOTAL'] = df_summary.sum(axis=1)

    # Optional: order columns
    sku_cols = sorted(df['MATERIAL'].unique())
    df_summary = df_summary.reindex(columns=sku_cols + ['TOTAL'])

    # Convert YEAR from index to column
    df_summary = df_summary.reset_index()

    # Remove column header name
    df_summary.columns.name = None
    df_summary = df_summary.sort_values('YEAR', ascending=False)

    cols = df_summary.columns

    fig = go.Figure(data=[go.Table(
        columnwidth=[16, 14, 16, 18, 16, 14, 14, 16],

        header=dict(values=list(cols),
                    fill_color=[color_hex(234)] + [color_hex(66)] * 6 + [color_hex(118)],
                    line_color='white',
                    font_color='white',
                    font_size=11,
                    height=28,
                    align=['left', 'center']),

        cells=dict(
            values=[df_summary[c] for c in cols[:9]],  # from cols[0] --> cols[5]
            font_size=11,
            height=28,
            fill_color=['lightpink'] + [color_hex(12)] * 6 + ['lightblue'],
            line_color='white',
            align=['center', 'center']))
    ])

    fig.update_layout(height=len(df_summary) * 28 + 28, margin=dict(l=0, r=0, b=0, t=0))

    utils.download_csv(df_summary, 'Download Product-Level Summary')

    return fig


def display_annual_flagship(datafile_location):

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    # get today's date
    # today = date.today()
    # year = st.sidebar.number_input("YEAR", min_value=2021, max_value=today.year, value=today.year)

    year = select_year()

    values = data.yearly_sales_df(datafile_location, year)
    df_all = values[0]
    df_all = df_all.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # <<<<< Remove accessories <<<<<<<<<<<<<<<<<<<<<<<<<

    year = values[1]
    month_elapsed = values[2]

    df_all = df_all.sort_values('REVENUE', ascending=False)

    total_revenue = df_all['REVENUE'].sum()

    df_all = df_all[['SKU', 'SUPPLIER', 'STATUS', 'TOTAL', 'AVERAGE', 'PRICE', 'REVENUE']]
    df_all.reset_index(drop=True, inplace=True)
    df_all.index = range(1, df_all.shape[0] + 1)

    launch_date = st.sidebar.selectbox("LAUNCH DATE", ['ALL', '2024', '2025', '2026'])

    # df_all = df_all[df_all['STATUS'] != 0]
    # df_all = df_all[df_all['STATUS'] != 'New Model']

    # calculate % revenue of each-50 SKU ++++++++++++++++++++++++++++++++++++
    percent_revenue = []
    for i in range (0, len(df_all), 50):
        df_50 = df_all[i:i+50]
        total_revenue_50 = df_50['REVENUE'].sum()
        percent_revenue_50 = round(total_revenue_50 * 100 / total_revenue, 2)
        percent_revenue.append(percent_revenue_50)

    # calculate total revenue 1 -200
    total_percent_revenue1 = round(percent_revenue[0] + percent_revenue[1] + percent_revenue[2] + percent_revenue[3], 2)  # <<<<<<<<<<<<<<<

    # calculate total revenue 201-400
    total_percent_revenue2 = round(percent_revenue[4] + percent_revenue[5] + percent_revenue[6] + percent_revenue[7], 2)  # <<<<<<<<<<<<<<<

    # filter by launch date ++++++++++++++++++++++++++++++++++++++++++++++++
    if launch_date != 'ALL':
        df_all['Launch Year'] = df_all.apply(lambda x: x.iloc[2][0:4], axis=1).copy()
        df_all = df_all[df_all['Launch Year'] >= launch_date]

    # filter by model / color ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    if model.upper()[0:2] == 'RV':
        text = 'YTD ' + str(year) + ' | Model: ' + model.upper()
        df = df_all.loc[lambda row: row['SKU'].str.startswith(model.upper())]
        if len(df)>50:
            n = st.sidebar.number_input('START INDEX', min_value=1, max_value=501, step=50)
            df = df[n-1:n+49]

    elif model.upper() == 'ALL':
        n = st.sidebar.number_input('START INDEX', min_value=1, max_value=501, step=50)

        # calculate index for percent_revenue array
        arr_index = int(n / 50)
        text = 'YTD ' + str(year) + ' | ' + str(n) + ' - ' + str(n + 49) + ' Top-Selling Models | Revenue: ' + str(percent_revenue[arr_index]) + '%'
        df = df_all[n-1:n+49]

    else:
        text = 'YTD ' + str(year) + ' | Color: ' + model.upper() + ' Sales'
        df = df_all.loc[lambda row: row['SKU'].str.endswith(model.upper())]
        if len(df) > 50:
            n = st.sidebar.number_input('START INDEX', min_value=1, max_value=501, step=50)
            df = df[n - 1:n + 49]

    index_list = df.index.tolist()

    if launch_date != 'ALL':
        text = 'Launched in ' + launch_date + ' or after |' + str(n) + ' - ' + str(n + 49) + ' Top-Selling Models | '

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:2%; line-height:0em; '
        f'margin-top:5px"> {text + " | "  + ut.get_todays_date() + " | " + str(round(month_elapsed,1)) + " Month Average"} </p>',
        unsafe_allow_html=True)

    # create single column table
    mygrid = ut.make_grid(6, 10)  # (row, col)
    row = 0
    col = 0


    for i in range(0, len(df)):

        sku = df.iloc[i][0]

        supplier = str(df.iloc[i][1])
        launch = str(df.iloc[i][2])
        total_sales = 'Total Sales ' + ut.format_num(str(df.iloc[i][3]))
        avg_sales = ut.format_num(str(df.iloc[i][4]))
        price = 'Unit Price: $ ' + ut.format_num(str(df.iloc[i][5]))
        revenue = 'Revenue: ' + str(df.iloc[i][6]) + ' k'

        # create dataframe for each product ticket ++++++++++++++++++++
        df_summary = pd.DataFrame({(str(index_list[i]) + '. ' + sku): [supplier + ' [' + launch + ']',
                                                               revenue,
                                                               total_sales + ' [Avg. ' + avg_sales + ']',
                                                               price,
                                                               ]})


        # =========== CONDITIONAL FORMATTING HEADER COLORS ===============================================
        body_color = color_hex(12)  # 154)

        header_highlight = color_hex(118)

        if supplier == 'Aquacubic':
            header_highlight = color_hex(211)

        elif supplier == 'Elleci':
            header_highlight = color_hex(111)

        elif supplier == 'Galassia':
            header_highlight = color_hex(159)

        elif supplier == 'Nicos':
            header_highlight = color_hex(165)

        elif supplier == 'Plados':
            header_highlight = color_hex(227)

        elif supplier == 'Speed Vietnam':
            header_highlight = color_hex(83)

        elif supplier == 'Stile Libero':
            header_highlight = color_hex(75)

        elif supplier == 'Xindeli':
            header_highlight = color_hex(217)

        elif supplier == 'Bomeijia':
            header_highlight = color_hex(135)

        elif supplier == 'Yalos':
            header_highlight = color_hex(156)

        elif supplier == 'Wisdom':
            header_highlight = color_hex(269)

        elif supplier == 'UAE Fireclay':
            header_highlight = color_hex(272)

        # =============== PLOTLY FIG for PRODUCT TICKET ======================================
        fig = go.Figure(data=[go.Table(
            columnwidth=[10, 10],

            header=dict(values=list(df_summary.columns),
                        fill_color=header_highlight,  # header_color,
                        font=dict(family="Arial", size=12, color='white'),
                        line_color='white',
                        height=24,
                        align=['center']),
            cells=dict(
                values=[df_summary],
                font=dict(family="Arial", size=11, color='black'),
                # font_size=12,
                height=24,
                fill_color=body_color,
                line_color='white',
                align=['left']))
        ])

        height = 24 * len(df_summary) + 20  #24
        fig.update_layout(height=height, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig, use_container_width=True)

        col = col + 1
        if col == 9:
            col = 0
            row = row + 1

    # +++++++ fig1: REVENUE SUMMARY-1 (1 - 200) ++++++++++++++++++++++++++++++++++++++++++
    if model.upper() == 'ALL' and launch_date =='ALL': # show fig1 & fig2
        fig1 = go.Figure(data=[go.Table(
            columnwidth=[10, 8],

            header=dict(values=list(['REVENUE', str(total_percent_revenue1) + '%']),
                        fill_color=[color_hex(72), color_hex(67)],  # header_color,
                        font=dict(family="Arial", size=12, color='white'),
                        line_color='white',
                        height=24,
                        align=['left', 'right']),
            cells=dict(

                values=[[['1 - 50'], ['51 - 100'], ['101 - 150'], ['151 - 200']],
                        [[str(percent_revenue[0]) + '%'], [str(percent_revenue[1]) + '%'], [str(percent_revenue[2]) + '%'],
                         [str(percent_revenue[3]) + '%']]
                        ],

                font=dict(family="Arial", size=12, color='black'),
                # font_size=10,
                height=24,  #24,
                fill_color=[color_hex(93), color_hex(303)],
                line_color='white',
                align=['left', 'right']))
                ])

        fig1.update_layout(height=120, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig1, use_container_width=True)

        # +++++++ fig2: SHOW REVENUE SUMMARY-2 (201 - 400) ++++++++++++++++++++++++++++++++++++++++++
        col = col + 1
        fig2 = go.Figure(data=[go.Table(
            columnwidth=[10, 8],

            header=dict(values=list(['REVENUE', str(total_percent_revenue2) + '%']),
                        fill_color=[color_hex(72), color_hex(67)],  # header_color,
                        font=dict(family="Arial", size=12, color='white'),
                        line_color='white',
                        height=24,
                        align=['left', 'right']),
            cells=dict(

                values=[[['201 - 250'], ['251 - 300'], ['301 - 350'], ['351 - 400']],
                        [[str(percent_revenue[4]) + '%'], [str(percent_revenue[5]) + '%'], [str(percent_revenue[6]) + '%'],
                         [str(percent_revenue[7]) + '%']]
                        ],

                font=dict(family="Arial", size=12, color='black'),
                # font_size=10,
                height=24,  # 24,
                fill_color=[color_hex(93), color_hex(303)],
                line_color='white',
                align=['left', 'right']))
        ])

        fig2.update_layout(height=120, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig2, use_container_width=True)

    else:
        col = col - 1

    # +++++++ fig3: SHOW SKU COUNT PER SUPPLIER (1-4) +++++++++++++++++++++++++++++++
    df_count = df.copy()
    df_count = df_count.groupby('SUPPLIER')['SKU'].count().to_frame().reset_index()
    df_count = df_count.sort_values(['SKU', 'SUPPLIER'], ascending=[False, True])
    df_count1 = df_count[0:4]

    col = col + 1

    fig3 = go.Figure(data=[go.Table(
            columnwidth=[14, 6],

            header=dict(values=list(['SUPPLIER', 'SKU']),
                        fill_color=[color_hex(396), color_hex(67)],  # header_color,
                        font=dict(family="Arial", size=12, color='white'),
                        line_color='white',
                        height=24,
                        align=['left', 'right']),
            cells=dict(

                values=[df_count1['SUPPLIER'], df_count1['SKU']],

                font=dict(family="Arial", size=12, color='black'),
                # font_size=10,
                height=24,  # 24,
                fill_color=[color_hex(392), color_hex(303)],
                line_color='white',
                align=['left', 'right']))
        ])

    fig3.update_layout(height=120, margin=dict(l=0, r=0, b=0, t=0))

    mygrid[row][col].plotly_chart(fig3, use_container_width=True)

    # +++++++ fig4: SHOW SKU COUNT PER SUPPLIER (5-8) +++++++++++++++++++++++++++++++
    df_count2 = df_count[4:8] # len(df_count)]
    # st.write(df_count2)

    if len(df_count2) > 0:

        col = col + 1

        fig4 = go.Figure(data=[go.Table(
            columnwidth=[14, 6],

            header=dict(values=list(['SUPPLIER', 'SKU']),
                    fill_color=[color_hex(396), color_hex(67)],  # header_color,
                    font=dict(family="Arial", size=12, color='white'),
                    line_color='white',
                    height=24,
                    align=['left', 'right']),
            cells=dict(

                values=[df_count2['SUPPLIER'], df_count2['SKU']],

                font=dict(family="Arial", size=12, color='black'),
                # font_size=10,
                height=24,  # 24,
                fill_color=[color_hex(392), color_hex(303)],
                line_color='white',
                align=['left', 'right']))
        ])

        fig4.update_layout(height=120, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig4, use_container_width=True)

    # +++++++ fig5: SHOW SKU COUNT PER SUPPLIER (8-End) +++++++++++++++++++++++++++++++
    df_count3 = df_count[8:len(df_count)]

    if len(df_count3) > 0:
        col = col + 1

        fig5 = go.Figure(data=[go.Table(
            columnwidth=[14, 6],

            header=dict(values=list(['SUPPLIER', 'SKU']),
                            fill_color=[color_hex(396), color_hex(67)],  # header_color,
                            font=dict(family="Arial", size=12, color='white'),
                            line_color='white',
                            height=24,
                            align=['left', 'right']),
            cells=dict(

                    values=[df_count3['SUPPLIER'], df_count3['SKU']],

                    font=dict(family="Arial", size=12, color='black'),
                    # font_size=10,
                    height=24,  # 24,
                    fill_color=[color_hex(392), color_hex(303)],
                    line_color='white',
                    align=['left', 'right']))
            ])

        fig5.update_layout(height=120, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig5, use_container_width=True)

    # Display data table <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    col1, col2 = st.columns([1,0.8])
    with col1:
        index_list1 = [item for item in range(1, len(df_all) + 1)]
        df_show = df_all.copy()
        df_show['INDEX'] = index_list1
        df_show = df_show[['INDEX', 'SKU', 'SUPPLIER', 'TOTAL', 'AVERAGE', 'PRICE', 'REVENUE']]

        AgGrid(df_show, fit_columns_on_grid_load=True)
        ut.download_csv(df_show, 'Download')
    return

def avg_sales_trend_graph(datafile_location, supplier):   #, supplier='ALL', model='ALL'):

    # get list of monthly sales file and sort
    path1 = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY'
    source_files1 = os.listdir(Path(PureWindowsPath(path1)))
    source_files1.sort()

    month = []
    total = []
    revenue = []

    df_price = data.price_list_df(datafile_location)


    for i in range(0, len(source_files1)):  # end at previous month

        file_name = str(source_files1[i])  # get file name
        s = file_name.split('_')  # split file name based on '_'
        month_name = s[2][:-4]  # get last portion and remove .csv

        path = datafile_location + 'Sales\\Monthly_Sales\\MONTHLY\\' + source_files1[i]

        df_sales = pd.read_csv(Path(PureWindowsPath(path)))
        df_sales = df_sales.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
        df_sales = df_sales[['SKU', 'SUPPLIER', 'TOTAL']]

        df_sales = df_sales.fillna(0)

        if supplier == 'ALL':
            df_sales = pd.merge(df_sales, df_price, on=["SKU"], how='outer')
            df_sales['REVENUE'] = df_sales['TOTAL'] * df_sales['PRICE']

            total_revenue = df_sales['REVENUE'].sum()
            total_sale = df_sales['TOTAL'].sum()

            revenue.append(total_revenue)
            month.append(month_name)
            total.append(total_sale)

        elif supplier != 'ALL':
            df_sales = df_sales[df_sales['SUPPLIER'] == supplier]

            total_sale = df_sales['TOTAL'].sum()

            month.append(month_name)
            total.append(total_sale)


    if supplier == 'ALL':
        df = pd.DataFrame({'MONTH': month,
                       'TOTAL SALE': total,
                        'REVENUE': revenue
                       })
    else:
        df = pd.DataFrame({'MONTH': month,
                           'TOTAL SALE': total,
                           })

    # remove current month
    df = df[0:len(df)-1]

    # st.write(df)
    # st.stop()

    df_with_rev = pd.DataFrame({})

    if supplier == 'ALL':

        df_total_sale = df['TOTAL SALE']  # get only the TOTAL SALE col for rolling operation
        df_revenue = df['REVENUE'] # get only the REVENUE col for rolling operation

        df['RUNNING AVG_6'] = df_total_sale.rolling(6, min_periods=1).mean(numeric_only=True)
        df['RUNNING AVG_12'] = df_total_sale.rolling(12, min_periods=1).mean(numeric_only=True)

        df['REVENUE_6'] = df_revenue.rolling(6, min_periods=1).mean(numeric_only=True)
        df['REVENUE_12'] = df_revenue.rolling(12, min_periods=1).mean(numeric_only=True)
        df_with_rev = df[len(df)-6:len(df)].copy()

        # st.write(df_with_rev)
        # st.write(df)
        # st.stop()
        six_month_avg = str(ut.format_num(df_with_rev.iloc[5][3]))
        twelve_month_avg = str(ut.format_num(df_with_rev.iloc[5][4]))

        text = 'Download Link for all Data Files'
        st.write('')
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(234)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
            f'margin-top:-10px"> {text} </p>', unsafe_allow_html=True)

    elif supplier != 'ALL':
        # 12-month running average
        df_total_sale = df['TOTAL SALE']  # get only the TOTAL SALE col for rolling operation
        df['RUNNING AVG_6'] = df_total_sale.rolling(6, min_periods=1).mean(numeric_only=True)
        df['RUNNING AVG_12'] = df_total_sale.rolling(12, min_periods=1).mean(numeric_only=True)

        df = df[len(df) - 6:len(df)]

        six_month_avg = str(ut.format_num(df.iloc[5][2]))
        twelve_month_avg = str(ut.format_num(df.iloc[5][3]))

    ut.download_csv(df, 'Download ' + supplier)

    # take last 6-month
    df = df[len(df)-6:len(df)]

    # st.write(df)
    # st.stop()


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['MONTH'],
                             y=df['RUNNING AVG_12'],
                             mode='lines',
                             line={'dash': 'solid', 'color': color_hex(66)},
                             name="12m Average (" + twelve_month_avg + '/mo)',
                             ))

    fig.add_trace(go.Scatter(x=df['MONTH'],
                             y=df['RUNNING AVG_6'],
                             mode='lines',
                             line={'dash': 'solid', 'color': color_hex(84)},
                             name="6m Average (" + six_month_avg + '/mo)',
                             ))

    fig.update_xaxes(
        dtick="M1",  # sets minimal interval to month
        tickformat="%d-%b-%Y",  # "%b %Y",  # sets the date format
        # tickangle=90,  # rotates the tick labels
        showgrid=True,
        gridwidth=2,
        #mirror = True,
        showline=True,
                  )

    fig.update_layout(
        # xaxis_title="MONTHS",
        yaxis_title="Avg Sales",
        # legend_title="LEGEND:",
        # showlegend = False,
        font=dict(
            family="Book Antiqua",
            size=12,
            color='Black'),
                    )
    fig.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=12), x=0.1, y=0.07))  # << LEGEND POSITION


    return fig, df_with_rev


def display_avg_sales_trend_graph(datafile_location):

    text = 'Average Sales Trend | ' + ut.get_todays_date()
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(234)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
        f'margin-top:5px"> {text} </p>', unsafe_allow_html=True)

    st.write('')

    mygrid = ut.make_grid(4, 5)  # (row, col)
    col = 0
    row = 0

    for i in range(0, len(SUPPLIER_LIST)):
        values = avg_sales_trend_graph(datafile_location, SUPPLIER_LIST[i])
        fig = values[0]

        if SUPPLIER_LIST[i] == 'ALL':
            df_with_rev = values[1].copy()
            # st.write(df_with_rev)

        fig.update_layout(width=700, height=160, margin=dict(l=0, r=0, b=0, t=0)) # <<<<<<< All suppliers

        txt = SUPPLIER_LIST[i]
        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(116)}; text-align:center; font-size: 18px ;border-radius:2%; '
            f'line-height:0em; margin-top:0px"> {txt} </p>', unsafe_allow_html=True)

        mygrid[row][col].plotly_chart(fig, use_container_width=True)


        if col < 4:
            col += 1

        else:
            col = 0
            row += 1

    txt = 'Revenue' # <<<<<<<<<<<<<< REVENUE <<<<<<<<<<<<<<<<<<<<<
    mygrid[row][col].markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(286)}; text-align:center; font-size: 18px ;border-radius:2%; '
        f'line-height:0em; margin-top:0px"> {txt} </p>', unsafe_allow_html=True)

    # st.write(df_with_rev)
    six_month_rev = str(round(df_with_rev.iloc[5][5]/1000000,2))
    twelve_month_rev = str(round(df_with_rev.iloc[5][6]/1000000,2))

    # Display revenue
    fig1 = go.Figure()

    fig1.add_trace(go.Scatter(x=df_with_rev['MONTH'],
                              y=df_with_rev['REVENUE_12'],
                              mode='lines',
                              line={'dash': 'solid', 'color': color_hex(66)},
                              name="12m Average (" + twelve_month_rev + '/mo)',
                              ))

    fig1.add_trace(go.Scatter(x=df_with_rev['MONTH'],
                              y=df_with_rev['REVENUE_6'],
                              mode='lines',
                              line={'dash': 'solid', 'color': color_hex(84)},
                              name="6m Average (" + six_month_rev + '/mo)',
                              ))

    fig1.update_xaxes(
        dtick="M1",  # sets minimal interval to month
        tickformat="%d-%b-%Y",  # "%b %Y",  # sets the date format
        # tickangle=90,  # rotates the tick labels
        showgrid=True,
        gridwidth=2,
        # mirror = True,
        showline=True,
    )
    fig1.update_layout(
        # xaxis_title="MONTHS",
        yaxis_title="Avg Revenue",
        # legend_title="LEGEND:",
        # showlegend = False,
        font=dict(
            family="Book Antiqua",
            size=12,
            color='Black'),
    )
    fig1.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=12), x=0.1, y=0.07))  # << LEGEND POSITION

    fig1.update_layout(width=500, height=160, margin=dict(l=0, r=0, b=0, t=0))   # <<<< Revenue only

    mygrid[row][col].plotly_chart(fig1, use_container_width=True)

    ut.download_csv(df_with_rev, 'Download ' + 'Revenue')

    return


def display_dealer_wise_quarterly_report(datafile_location):

    # years = ['2026', '2025']

    current_year = datetime.now().year

    years = [current_year, current_year - 1]
    years = list(map(str, years))   # convert the list element to str

    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    current_year = str(datetime.now().year)
    current_month = datetime.now().month

    # create dealer order from sales in USD ======================
    file_path = Path(PureWindowsPath(datafile_location + "Sales\\Monthly_Sales\\Dealers_Order.csv"))
    df_dealer = pd.read_csv(file_path, encoding='latin-1')

    df_dealer.loc[df_dealer['Customer'] == 'Cabinets To Go, Megan Collier', 'Customer'] = 'Cabinets To Go' # <<<<<<<< =============

    df_dealer = df_dealer.groupby('Customer')['Total'].sum().to_frame().reset_index()
    df_dealer = df_dealer.sort_values('Total', ascending=False)
    df_dealer.reset_index(drop=True, inplace=True)
    df_dealer.index = range(1, df_dealer.shape[0] + 1)

    df_dealer1 = df_dealer[0:24]    # take top 24 dealers only

    # >>>>>>>>>>> change the dealer name 'Cabinets To Go, Megan Collier' to 'Megan Collier' in the df_dealer1 <<<<<<<<<<<<<<
    # df_dealer1.loc[df_dealer1['Customer'] == 'Cabinets To Go, Megan Collier', 'Customer'] = 'Megan Collier'

    # st.write(df_dealer1)
    # st.stop()

    dealers = df_dealer1['Customer'].to_list() # make a dealer list

    text = current_year + ' YTD | Dealer Quarterly Sales Summary | ' + ut.get_todays_date()

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 20px ;border-radius:2%; line-height:0em; '
        f'margin-top:10px"> {text} </p>', unsafe_allow_html=True)

    st.write('')

    mygrid = ut.make_grid(6,5) #(5, 4)  # (rows, cols)
    col = 0
    row = 0

    for d in range (0, len(dealers)): # run for all dealers

        for y in range (0, len(years)): # run for all year

            # limit month number for the current year
            if years[y] == current_year:
                no_of_months = current_month
            else:
                no_of_months = 12

            for m in range(0, no_of_months): # run for all month

                if dealers[d] == 'Amazon':
                    df = data.amazon_df(datafile_location, months[m], years[y])

                else:
                    df = data.zen_df(datafile_location, months[m], years[y])

                    df ['DEALER'] = df.apply(lambda x: str(x.iloc[4]).upper(), axis=1) # convert dealer name to upper case
                    df.replace ('MEGAN COLLIER', 'CABINETS TO GO', inplace=True) # <<<<<<<<<<<<<<<< ============================

                    # st.write(df)
                    # st.stop()

                    df = df.loc[lambda row: row['DEALER'].str.startswith(dealers[d].upper())] # query with dealer name


                month_name = str(months[m])[0:3] + '-' + years[y][2:4] # get month name for column header like Jan-24

                if len(df) > 0:
                    df1 = df.groupby('SKU')['QTY'].sum().to_frame().reset_index()

                    df1 = df1.rename(columns={'QTY': month_name})

                else:
                    df = df[['SKU', 'QTY']]
                    df['QTY'] = 0
                    df1 = df.rename(columns={'QTY': month_name})
                    # st.write(df)

                # merge for 12 months
                if m == 0:
                    df2 = df1.copy()

                else:
                    if len(df) > 0:
                        df2 = pd.merge(df2, df1, on=["SKU"], how='outer')
                    else:
                        df2[month_name] = 0

            df2 = df2.fillna(0)
            # st.write(df2)

            df2 = df2.loc[lambda row: ~ row['SKU'].str.startswith('RVA')] # remove accessories

            # for current year create blank columns for the rest of the months
            if years[y] == current_year:

                for m2 in range (current_month+1, 13):
                    short_month_name = ut.get_short_month_name(m2)
                    df2[short_month_name + '-' + current_year[2:4]] = 0

            # arrange columns in order
            cols = ['SKU',
                    str(months[0])[0:3] + '-' + years[y][2:4],
                    str(months[1])[0:3] + '-' + years[y][2:4],
                    str(months[2])[0:3] + '-' + years[y][2:4],
                    str(months[3])[0:3] + '-' + years[y][2:4],
                    str(months[4])[0:3] + '-' + years[y][2:4],
                    str(months[5])[0:3] + '-' + years[y][2:4],
                    str(months[6])[0:3] + '-' + years[y][2:4],
                    str(months[7])[0:3] + '-' + years[y][2:4],
                    str(months[8])[0:3] + '-' + years[y][2:4],
                    str(months[9])[0:3] + '-' + years[y][2:4],
                    str(months[10])[0:3] + '-' + years[y][2:4],
                    str(months[11])[0:3] + '-' + years[y][2:4],
                    ]

            # create Q1 df
            q1 = 'Q1' + '-' + years[y][2:4]
            df_q1 = df2[[cols[0], cols[1], cols[2], cols[3]]].copy()
            df_q1[q1] = df2[cols[1]] + df2[cols[2]] + df2[cols[3]]
            df_q1 = df_q1[['SKU', q1]]

            # create Q2 df
            q2 = 'Q2' + '-' + years[y][2:4]
            df_q2 = df2[[cols[0], cols[4], cols[5], cols[6]]].copy()
            df_q2[q2] = df2[cols[4]] + df2[cols[5]] + df2[cols[6]]
            df_q2 = df_q2[['SKU', q2]]

            df_quarter = pd.merge(df_q1, df_q2, on=["SKU"], how='outer')

            # create Q3 df
            q3 = 'Q3' + '-' + years[y][2:4]
            df_q3 = df2[[cols[0], cols[7], cols[8], cols[9]]].copy()
            df_q3[q3] = df2[cols[7]] + df2[cols[8]] + df2[cols[9]]
            df_q3 = df_q3[['SKU', q3]]

            df_quarter = pd.merge(df_quarter, df_q3, on=["SKU"], how='outer')

            # create Q4 df
            q4 = 'Q4' + '-' + years[y][2:4]
            df_q4 = df2[[cols[0], cols[10], cols[11], cols[12]]].copy()
            df_q4[q4] = df2[cols[10]] + df2[cols[11]] + df2[cols[12]]
            df_q4 = df_q4[['SKU', q4]]

            df_quarter = pd.merge(df_quarter, df_q4, on=["SKU"], how='outer')

            df_quarter['TOTAL'] = df_quarter[q1] + df_quarter[q2] + df_quarter[q3] + df_quarter[q4]
            df_quarter = df_quarter.sort_values('SKU', ascending=True)

            # st.write(df_quarter)
            #st.stop()

            q1_sum = df_quarter[q1].sum()
            q2_sum = df_quarter[q2].sum()
            q3_sum = df_quarter[q3].sum()
            q4_sum = df_quarter[q4].sum()
            total = df_quarter['TOTAL'].sum()

            # st.write(q1_sum)
            # st.write(q2_sum)
            # st.write(q3_sum)
            # st.write(q4_sum)

            df_table = pd.DataFrame({'Year': [years[y]],
                                 'Q1': [q1_sum],
                                 'Q2': [q2_sum],
                                 'Q3': [q3_sum],
                                 'Q4': [q4_sum],
                                 'Total': [total],

                                 })

            if y == 0:
                df_table1 = df_table.copy()

            else:
                df_table1 = pd.concat([df_table1, df_table])


            # AgGrid(df_quarter)
            ut.download_csv(df_quarter, '4 Quarter: ' + dealers[d].upper() + '-' + years[y])

            # AgGrid(df2, fit_columns_on_grid_load=True)
            ut.download_csv(df2, '12 Months: ' + dealers[d].upper() + '-' + years[y])

            # replace 0 by blank ('')
            df_table1['Q1'].replace(to_replace=0, value='', inplace=True)
            df_table1['Q2'].replace(to_replace=0, value='', inplace=True)
            df_table1['Q3'].replace(to_replace=0, value='', inplace=True)
            df_table1['Q4'].replace(to_replace=0, value='', inplace=True)

            cols = df_table1.columns

            fig = go.Figure(data=[go.Table(
                columnwidth=[18, 18],

                header=dict(values=list(cols),
                            fill_color=[color_hex(357)] + [color_hex(66)] * 4 + [color_hex(118)],
                            line_color='white',
                            font_color='white',
                            font_size=14,
                            height=28,
                            align=['left', 'center']),
                cells=dict(
                    values=[df_table1[cols[0]], df_table1[cols[1]], df_table1[cols[2]], df_table1[cols[3]], df_table1[cols[4]], df_table1[cols[5]]],
                    font_size=14,
                    height=28,
                    fill_color=[color_hex(304)] + [color_hex(12)] * 4 + ['lightblue'],
                    line_color='white',
                    align=['left', 'right']))
               ])


        # get dealers sales in USD
        dealer_sales = df_dealer[df_dealer['Customer'] == dealers[d]].iloc[0][1]
        dealer_sales = round(dealer_sales/1000, 0)

        txt2 = str(d+1) + '. ' + dealers[d].upper()  + ' ($ ' + str(ut.format_num(dealer_sales)) + 'k)'
        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(240)}; text-align:left; font-size: 14px ;border-radius:2%; '
            f'line-height:0em; margin-top:0px"> {txt2} </p>', unsafe_allow_html=True)

        fig.update_layout(width=700, height=len(df_table1) * 28 + 28, margin=dict(l=0, r=0, b=0, t=0))

        mygrid[row][col].plotly_chart(fig, use_container_width=True)

        if col < 3:
            col += 1

        else:
            col = 0
            row += 1

    st.write(df_dealer)
    ut.download_csv(df_dealer, 'Dealer List')

    return


def display_dealer_wise_6_month_sales_graph(datafile_location):

    current_year = datetime.now().year
    current_month = datetime.now().month
    years = [current_year - i for i in range(3)]    # get list of 3 years, such as 2025(current), 2024, 2023
    years.reverse()

    months = calendar.month_name[1:]  # get list of all months name

    # create dealer order from sales in USD ======================
    file_path = Path(PureWindowsPath(datafile_location + "Sales\\Monthly_Sales\\Dealers_Order.csv"))
    df_dealer = pd.read_csv(file_path, encoding='latin-1')

    df_dealer.loc[df_dealer['Customer'] == 'Cabinets To Go, Megan Collier', 'Customer'] = 'Cabinets To Go' # <<<<<<<< =============

    df_dealer = df_dealer.groupby('Customer')['Total'].sum().to_frame().reset_index()
    df_dealer = df_dealer.sort_values('Total', ascending=False)
    df_dealer.reset_index(drop=True, inplace=True)
    df_dealer.index = range(1, df_dealer.shape[0] + 1)

    df_dealer1 = df_dealer[0:20]   # take top 20 dealers only

    dealers = df_dealer1['Customer'].to_list()  # make a dealer list

    index_list = df_dealer1.index.tolist()
    # st.write(index_list)
    # st.stop()
    #
    # dealers.remove('eBay')
    # dealers.remove('The Sink Boutique')
    # dealers.remove('Casita Travel Trailers')
    # st.write(dealers)
    # st.stop()

    # ==========================================================
    text = 'Average Sales Trend | ' + ut.get_todays_date()

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 22px ;border-radius:2%; line-height:0em; '
        f'margin-top:10px"> {text} </p>', unsafe_allow_html=True)

    st.write('')

    mygrid = ut.make_grid(4, 5)  # (rows, cols)
    col = 0
    row = 0

    for d in range (0, len(dealers)): # run for all dealers

        for y in range(0, len(years)): # run for all year

            # limit month number for the current year
            if years[y] == current_year:
                no_of_months = current_month
            else:
                no_of_months = 12

            for m in range(0, no_of_months): # run for all month

                year = str(years[y])
                month = months[m]

                if dealers[d] == 'Amazon':
                    df = data.amazon_df(datafile_location, month, year)

                else:
                    df = data.zen_df(datafile_location, months[m], str(years[y]))

                    df ['DEALER'] = df.apply(lambda x: str(x.iloc[4]).upper(), axis=1) # convert dealer name to upper case
                    # st.write(df)

                    df.replace ('MEGAN COLLIER', 'CABINETS TO GO', inplace=True) # <<<<<<<<<<<<<<<< ============================

                    df = df.loc[lambda row: row['DEALER'].str.startswith(dealers[d].upper())] # query with dealer name

                month_name = month[0:3] + '-' + year[2:4] # get month name for column header like Jan-23

                if len(df) > 0:
                    df1 = df.groupby('SKU')['QTY'].sum().to_frame().reset_index()

                    df1 = df1.rename(columns={'QTY': month_name})

                else:
                    df = df[['SKU', 'QTY']]
                    df['QTY'] = 0
                    df1 = df.rename(columns={'QTY': month_name})
                    # st.write(df)

                # merge for 12 months
                if m == 0:
                    df2 = df1.copy()


                else:
                    if len(df) > 0:
                        df2 = pd.merge(df2, df1, on=["SKU"], how='outer')
                    else:
                        df2[month_name] = 0

            df2 = df2.fillna(0)

            df2 = df2.loc[lambda row: ~ row['SKU'].str.startswith('RVA')] # remove accessories

            if years[y] == years[0]: # current year -2 <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                df_a = df2.copy()

            if years[y] == years[1]: # current year - 1  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                df_b = df2.copy()

            elif years[y] == years[2]: # current year <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                df_c = df2.copy()

        # merge data file of 2024 & 2025
        df3 = pd.merge(df_a, df_b, on=["SKU"], how='outer')
        df3 = pd.merge(df3, df_c, on=["SKU"], how='outer')
        df3 = df3.fillna(0)

        # Pop the column you want to shift
        column_to_shift = df3.pop('SKU')

        # Insert the column at the beginning (index 0)
        df3.insert(0, 'SKU', column_to_shift)

        ut.download_csv(df3, dealers[d].upper() + '_Download')
        # st.stop()

        # add TOTAL row at the bottom

        cols = df3.columns

        list = ['TOTAL']
        for i in range(1, len(cols)):
            list.append(df3[cols[i]].sum())

        index = len(df3) + 1

        df3.loc[index] = list


        # get only TOTAL
        df3 = df3[df3['SKU'] == 'TOTAL'].copy()


        # convert 2-row table to 2-col table
        total = []
        for j in range (0, df3.shape[1]):
            total.append(df3.iloc[0][j])

        cols = df3.columns

        df4 = pd.DataFrame({'MONTH': cols,
                           'TOTAL': total
                           })

        df4 = df4[1:len(df4)-1].copy()  # remove the current month data

        # st.write(df4)
        # st.stop()

        df_total_sale = df4['TOTAL']  # get only the TOTAL col for rolling operation

        #df4['RUNNING AVG_6'] = df_total_sale.rolling(6, min_periods=1).mean(numeric_only=True)
        df4['RUNNING AVG_6'] = df_total_sale.rolling(6, min_periods=1).mean()       # changed on 11/19/2025

        #df4['RUNNING AVG_12'] = df_total_sale.rolling(12, min_periods=1).mean(numeric_only=True)
        df4['RUNNING AVG_12'] = df_total_sale.rolling(12, min_periods=1).mean()     # changed on 11/19/2025

        df4 = df4[len(df4)-6: len(df4)]

        last_6m_avg = ut.format_num(round(df4.iloc[5][2],0))
        last_12m_avg = ut.format_num(round(df4.iloc[5][3],0))

        #st.stop()

        # Display graphs =======================================================================
        # txt = str(d+1) + ' ' + dealers[d].upper()
        txt = '[' + str(index_list[d]) + ']' + ' ' + dealers[d].upper()

        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(116)}; text-align:left; font-size: 14px ;border-radius:2%; '
            f'line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=df4['MONTH'],
                                  y=df4['RUNNING AVG_12'],
                                  mode='lines',
                                  line={'dash': 'solid', 'color': color_hex(66)},
                                  name="12m Average (" + str(last_12m_avg) + '/mo)',
                                   ))

        fig1.add_trace(go.Scatter(x=df4['MONTH'],
                                  y=df4['RUNNING AVG_6'],
                                  mode='lines',
                                  line={'dash': 'solid', 'color': color_hex(84)},
                                  name="6m Average (" + str(last_6m_avg) + '/mo)',
                                  ))
        fig1.update_xaxes(
            dtick="M1",  # sets minimal interval to month
            tickformat="%d-%b-%Y",  # "%b %Y",  # sets the date format
            showgrid=True,
            gridwidth=2,
            showline=True,
        )

        fig1.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=12), x=0.1, y=0.1))  # << LEGEND POSITION

        fig1.update_layout(height=160, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig1, use_container_width=True)

        if col < 4:
            col += 1

        else:
            col = 0
            row += 1
    return


def six_month_sales_graph(datafile_location):

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")
    year = date.today().year

    # get yearly sales data for current year =================
    values = data.yearly_sales_df(datafile_location, year)
    df1 = values[0].copy()
    df1 = df1.drop(['SUPPLIER', 'STATUS', 'AVERAGE', 'TOTAL', 'REVENUE'], axis=1)

    # get yearly sales data for previous year ================
    values = data.yearly_sales_df(datafile_location, year-1)
    df2 = values[0].copy()
    df2 = df2.drop(['AVERAGE', 'TOTAL', 'PRICE', 'REVENUE'], axis=1)

    # merge previous year and current year data ==============
    df_all = pd.merge(df2, df1, on=["SKU"], how='outer')

    total_cols = df_all.shape[1]  # total columns
    cols = df_all.columns

    cols_to_select = ['SKU',
                      'SUPPLIER',
                      'STATUS',
                      cols[total_cols-8],
                      cols[total_cols-7],
                      cols[total_cols-6],
                      cols[total_cols-5],
                      cols[total_cols-4],
                      cols[total_cols-3],
                      cols[total_cols-1],
                      ]

    df_all = df_all[cols_to_select]

    # add TOTAL, AVERAGE & REVENUE columns ======================
    df_all['TOTAL'] = df_all[cols_to_select[:-1]].sum(axis=1)
    df_all['AVERAGE'] = round(df_all[cols_to_select[:-1]].mean(axis=1), 2)
    df_all['REVENUE'] = round(df_all['TOTAL'] * df_all['PRICE']/1000, 2)

    # filter / sort as per choice ===========================
    product = st.sidebar.radio('Select Product', ('ALL', 'Sinks', 'Accessories'), index=0)
    order = st.sidebar.radio('Select Order', ('Order by SKU', 'Order by Sales Qty', 'Order by Revenue'), index=0)

    df = df_all.copy()

    if order == 'Order by Sales Qty':
        df = df_all.sort_values('TOTAL', ascending=False)

    elif order == 'Order by Revenue':
        df = df_all.sort_values('REVENUE', ascending=False)

    if product == 'Sinks':
        df = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]

    elif product == 'Accessories':
        df = df.loc[lambda row: row['SKU'].str.startswith('RVA')]

    df.reset_index(drop=True, inplace=True)
    df.index = range(1, df.shape[0] + 1)

    # filter by model / color ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    if model.upper()[0:2] == 'RV':
        text = 'Model: ' + model.upper()
        df = df.loc[lambda row: row['SKU'].str.startswith(model.upper())]
        if len(df) > 25:
            n1 = st.sidebar.number_input('START INDEX', min_value=1, max_value=len(df), step=25)
            df = df[n1 - 1:n1 + 24]

    elif model.upper() == 'ALL':
        n2 = st.sidebar.number_input('START INDEX', min_value=1, max_value=len(df_all), step=25)

        text = str(n2) + ' - ' + str(n2 + 24) + ' Top-Selling Models'
        df = df[n2 - 1:n2 + 24]

    else:
        text = 'Color: ' + model.upper() + ' Sales'
        df = df.loc[lambda row: row['SKU'].str.endswith(model.upper())]
        if len(df) > 25:
            n3 = st.sidebar.number_input('START INDEX', min_value=1, max_value=len(df), step=25)
            df = df[n3 - 1:n3 + 24]

    index_list = df.index.tolist()

    total_cols = df.shape[1]
    cols = df.columns

    text1 = '6-Month Sales Trend | ' + text + ' | ' + ut.get_todays_date()

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 20px ;border-radius:2%; line-height:0em; '
        f'margin-top:5px"> {text1} </p>', unsafe_allow_html=True)

    mygrid = ut.make_grid(5, 6)  # (cols, rows)
    col = 0
    row = 0

    for i in range(0, len(df)):

        df_temp = df[df['SKU'] == df.iloc[i][0]]

        df_graph = pd.DataFrame({'MONTH': [cols[total_cols-10], cols[total_cols-9], cols[total_cols-8], cols[total_cols-7],
                                           cols[total_cols-6], cols[total_cols-5]],

                                'SALE': [df_temp.iloc[0][total_cols-10], df_temp.iloc[0][total_cols-9], df_temp.iloc[0][total_cols-8],
                                         df_temp.iloc[0][total_cols-7], df_temp.iloc[0][total_cols-6], df_temp.iloc[0][total_cols-5]]
                                 })

        avg_sales = round(df_temp.iloc[0][total_cols-2], 0)

        sku = str(df.iloc[i][0])
        launch_date = str(df.iloc[i][2])
        text = str(index_list[i]) + ' ' + sku + ' | ' + launch_date

        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(117)}; text-align:left; font-size: 14px ;border-radius:2%; line-height:0em; '
            f'margin-top:9px"> {text} </p>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_graph['MONTH'],
                                 y=df_graph['SALE'],
                                 mode='lines',
                                 line={'dash': 'solid', 'color': color_hex(66)},
                                 ))

        fig.add_hline(y=avg_sales, line_width=1, line_dash="dash", line_color=color_hex(140),
                      annotation_text='6-Month Avg. ' + str(ut.format_num(avg_sales)),
                      annotation_font_size=14,
                      annotation_font_color=color_hex(280),
                      )

        fig.update_layout(height=110, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig, use_container_width=True)
        if col < 4:
            col += 1

        else:
            col = 0
            row += 1

    col1, col2 = st.columns([4, 1])
    with col1:
        txt = f'Data File:  {cols[total_cols-10]} ~ {cols[total_cols-5]}'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 14px ;border-radius:2%; line-height:0em; '
            f'margin-top:8px"> {txt} </p>', unsafe_allow_html=True)

        # build AgGrid options
        gb = GridOptionsBuilder.from_dataframe(df_all)
        column_settings = {
            'SKU': 120, 'SUPPLIER': 110, 'STATUS': 80,
            cols[total_cols-10]: 80, cols[total_cols-9]: 80,
            cols[total_cols-8]: 80, cols[total_cols-7]: 80,
            cols[total_cols-6]: 80, cols[total_cols-5]: 80,
            'PRICE': 90, 'TOTAL': 90, 'AVERAGE': 90, 'REVENUE': 90
        }
        for column, width in column_settings.items():
            gb.configure_column(column, wrapText=False, width=width)

        grid_options = gb.build()

        AgGrid(df_all, grid_options, height=400, fit_columns_on_grid_load=True)

    ut.download_csv(df_all, 'Download File')
    return


def display_dealer_wise_sku_sales(datafile_location):
    # current_year = datetime.now().year
    # current_month = datetime.now().month
    # years = [current_year - i for i in range(3)]  # get list of 3 years, such as 2025(current), 2024, 2023
    # years.reverse()
    # st.write(years)
    # st.stop()

    years = ['2025']    #, '2024']  # , '2023']
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    current_year = str(datetime.now().year)
    current_month = datetime.now().month

    # create dealer order from sales in USD =================================================
    file_path = Path(PureWindowsPath(datafile_location + "Sales\\Monthly_Sales\\Dealers_Order.csv"))
    df_dealer = pd.read_csv(file_path, encoding='latin-1')

    # Datafile definition >> [Customer, Total, Delivery Address/State, Delivery Address/Zip, Products, Order Lines]

    # >>>>>>>>>>> change the dealer name 'Cabinets To Go, Megan Collier' to 'Cabinets to Go <<<<<<<<<<<<<<
    df_dealer.loc[df_dealer['Customer'] == 'Cabinets To Go, Megan Collier', 'Customer'] = 'Cabinets To Go'
    df_dealer = df_dealer.groupby('Customer')['Total'].sum().to_frame().reset_index()

    df_dealer = df_dealer.sort_values('Total', ascending=False)
    df_dealer.reset_index(drop=True, inplace=True)
    df_dealer.index = range(1, df_dealer.shape[0] + 1)

    df_dealer1 = df_dealer[0:11]  # take top 10 dealers only

    # st.write(df_dealer1)
    # st.stop()

    dealers = df_dealer1['Customer'].to_list() # make a dealer list
    dealers.remove('eBay')
    dealers.reverse()
    # st.write(dealers)
    # st.stop()

    # get the top-100 SKU list ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    values = data.yearly_sales_df(datafile_location, 2025)
    df_100 = values[0]
    df_100 = df_100.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]  # <<<<<<<<<<<<<<<<<<<<<<<<<

    df_100 = df_100.sort_values('REVENUE', ascending=False)
    df_100.reset_index(drop=True, inplace=True)
    df_100.index = range(1, df_100.shape[0] + 1)
    df_100 = df_100[['SKU', 'SUPPLIER', 'STATUS']]

    sku_max = 24 * 18    # multiple of 24
    df_100 = df_100[0:sku_max]
    # st.write(df_100)
    # st.stop()

    n = st.sidebar.number_input('START INDEX', min_value=1, max_value=sku_max-23, step=24)

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    if model.upper() == 'ALL':

        text = current_year + ' YTD | Dealer-wise SKU Sales [' + str(n) + ' - ' + str(n+23) + '] | '  + ut.get_todays_date()
    else:
        text = current_year + ' YTD | Dealer-wise SKU Sales [' + model.upper() + '] | '  + ut.get_todays_date()


    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em; '
        f'margin-top:3px"> {text} </p>', unsafe_allow_html=True)

    st.write('')
    # st.stop()

    mygrid = ut.make_grid(6, 6)  # (5, 4)  # (rows, cols)
    col = 0
    row = 0

    for d in range(0, len(dealers)):  # run for all dealers

        for y in range(0, len(years)):  # run for all year

            # limit month number for the current year
            if years[y] == current_year:
                no_of_months = current_month
            else:
                no_of_months = 12

            for m in range(0, no_of_months):  # run for all month

                if dealers[d] == 'Amazon':
                    df = data.amazon_df(datafile_location, months[m], years[y])


                else:
                    df = data.zen_df(datafile_location, months[m], years[y])

                    df['DEALER'] = df.apply(lambda x: str(x.iloc[4]).upper(), axis=1)  # convert dealer name to upper case

                    df = df.loc[lambda row: row['DEALER'].str.startswith(dealers[d].upper())]  # query with dealer name

                month_name = str(months[m])[0:3] + '-' + years[y][2:4]  # get month name for column header like Jan-24
                df = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]  # query with dealer name


                if len(df) > 0:
                    df1 = df.groupby(['SKU'])['QTY'].sum().to_frame().reset_index()

                    df1 = df1.rename(columns={'QTY': month_name})

                else:
                    df = df[['SKU', 'QTY']]
                    df['QTY'] = 0
                    df1 = df.rename(columns={'QTY': month_name})

                # merge for 12 months
                if m == 0:
                    # df2 = df1.copy()
                    df2 = pd.merge(df_100, df1, on=["SKU"], how='left') # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
                else:
                    if len(df) > 0:
                        df2 = pd.merge(df2, df1, on=["SKU"], how='left')

                    else:
                        df2[month_name] = 0

            df2 = df2.fillna(0)

            cols = df2.columns
            # st.write(df2)

            # create sum column with dealer name
            df2[dealers[d]] = df2[cols[3:]].sum(axis=1)

            df2 = df2[['SKU', dealers[d]]]
            # st.write(df2)
            # st.stop()

            if d == 0:  #dealers[d] == 'Amazon':
                df_all = df2
            else:
                df_all = pd.merge(df_all, df2, on=["SKU"], how='outer')

    df_all = df_all.fillna(0)
    df_all = df_all.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]  # <<<<<<<<<<<<<<<<<<<<<<<<<

    # st.write(df_all)
    # st.stop()

    df_all.reset_index(drop=True, inplace=True)
    df_all.index = range(1, df_all.shape[0] + 1)

    # st.write(df_all)
    # st.stop()

    txt = 'Datafile' + ' [1 - ' + str(sku_max) + ']'
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:2%; '
        f'line-height:0em; margin-top:0px"> {txt} </p>', unsafe_allow_html=True)

    st.write(df_all)
    ut.download_csv(df_all, 'Download Datafile')
    st.write('')

    if model.upper() == 'ALL':
        df_temp = df_all[n - 1:n + 23].copy()

    elif model.upper()[0:2] == 'RV':
        df_temp = df_all.loc[lambda row: row['SKU'].str.startswith(model.upper())]

    else:
        df_temp = df_all.loc[lambda row: row['SKU'].str.endswith(model.upper())]


    txt = 'Datafile' + ' [ ' + model.upper() + ']'
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 18px ;border-radius:2%; '
        f'line-height:0em; margin-top:0px"> {txt} </p>', unsafe_allow_html=True)

    st.write(df_temp)
    ut.download_csv(df_temp, 'Download Datafile')

    if len(df_temp) > 24:
        df_24 = df_temp[n - 1:n + 23].copy()

    else:
        df_24 = df_temp

    # st.write(df_24)

    for i in range (0,len(df_24)):

        sku = df_24.iloc[i][0]
        df_sku = df_24[df_24['SKU'] == sku]     #df_24.iloc[i][0]]

        index = df_sku.index

        loc1 = str(index).find('[')     # Int64Index([97], dtype='int64')
        loc2 = str(index).find(']')     # Int64Index([97], dtype='int64')

        index = str(index)[loc1:loc2+1]

        k = int(index[1:-1])

        sku = index + ' ' + df_sku.iloc[0][0] + ' | ' + df_100.iloc[k-1][2]

        # ============ CONDITIONAL FORMATTING COLOR =================
        supplier = df_100.iloc[k-1][1]

        # st.write(df_100)
        # st.stop()
        # st.write(supplier)

        if supplier == 'Aquacubic':
            header_txt = color_hex(211)

        elif supplier == 'Elleci':
            header_txt = color_hex(111)

        elif supplier == 'Galassia':
            header_txt = color_hex(159)

        elif supplier == 'Nicos':
            header_txt = color_hex(165)

        elif supplier == 'Plados':
            header_txt = color_hex(227)

        elif supplier == 'Speed':
            header_txt = color_hex(118) #9)

        elif supplier == 'Speed Vietnam':
            header_txt = color_hex(83)

        elif supplier == 'Stile Libero':
            header_txt = color_hex(75)

        elif supplier == 'Xindeli':
            header_txt = color_hex(217)

        elif supplier == 'Bomeijia':
            header_txt = color_hex(135)

        elif supplier == 'Yalos':
            header_txt = color_hex(156)

        elif supplier == 'Wisdom':
            header_txt = color_hex(269)


        mygrid[row][col].markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:center; font-size: 14px ;border-radius:2%; '
            f'line-height:0em; margin-top:0px"> {sku} </p>', unsafe_allow_html=True)

        df_sku = df_sku.rename(columns={'HAJOCA / MOORE SUPPLY': 'HAJOCA'})

        cols = df_sku.columns

        values = [df_sku.iloc[0][1],
                  df_sku.iloc[0][2],
                  df_sku.iloc[0][3],
                  df_sku.iloc[0][4],
                  df_sku.iloc[0][5],
                  df_sku.iloc[0][6],
                  df_sku.iloc[0][7],
                  df_sku.iloc[0][8],
                  df_sku.iloc[0][9],
                  df_sku.iloc[0][10],]

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=values,
                          y=cols[1:len(cols)],
                          # text = values,
                          # textposition='auto',  #'outside',
                          orientation = 'h',
                          marker_color= header_txt  #color_hex(9)
                              ))
        fig1.update_xaxes(
            #dtick="M1",  # sets minimal interval to month
            #tickformat="%d-%b-%Y",  # "%b %Y",  # sets the date format
            # tickangle=90,  # rotates the tick labels
            showgrid=True,
            gridwidth=2,
            # mirror = True,
            showline=True,)

        fig1.update_layout(height=180, margin=dict(l=0, r=0, b=0, t=0))
        mygrid[row][col].plotly_chart(fig1, use_container_width=True)

        if col < 5:
            col += 1

        else:
            col = 0
            row += 1

    return

def display_material_wise_revenue(datafile_location):
    years = [2026, 2025, 2024]  # <<< ==== Years to be displayed ========

    for i in range (0, len(years)):
        values = data.yearly_sales_df(datafile_location, years[i])
        df = values[0]

        # st.write(df)
        # st.stop()
        df = df[['SKU', 'REVENUE']]

        df_rvh = df.loc[lambda row: row['SKU'].str.startswith('RVH')]
        total_rvh = df_rvh['REVENUE'].sum()

        df_rvq = df.loc[lambda row: row['SKU'].str.startswith('RVQ')]
        total_rvq = df_rvq['REVENUE'].sum()

        df_rvu = df.loc[lambda row: row['SKU'].str.startswith('RVU')]
        total_rvu = df_rvu['REVENUE'].sum()

        total_hm = total_rvh + total_rvq + total_rvu

        total_hm = round(total_hm/1000, 2)

        df_mm = df.loc[lambda row: row['SKU'].str.startswith('RVM')]
        total_mm = round(df_mm['REVENUE'].sum()/1000, 2)

        df_gr = df.loc[lambda row: row['SKU'].str.startswith('RVG')]
        total_gr =round(df_gr['REVENUE'].sum()/1000, 2)

        df_fc = df.loc[lambda row: row['SKU'].str.startswith('RVL')]
        total_fc = round(df_fc['REVENUE'].sum()/1000, 2)

        df_rvb = df.loc[lambda row: row['SKU'].str.startswith('RVB')]
        total_rvb = round(df_rvb['REVENUE'].sum()/1000, 2)

        df_rvf = df.loc[lambda row: row['SKU'].str.startswith('RVF')]
        total_rvf = round(df_rvf['REVENUE'].sum() / 1000, 2)

        df_rva = df.loc[lambda row: row['SKU'].str.startswith('RVA')]
        total_rva = round(df_rva['REVENUE'].sum() / 1000, 2)

        df_all = pd.DataFrame({'YEAR': ['HM', 'MM', 'GR', 'FC', 'RVB', 'RVF', 'RVA'],
                               str(years[i]): [total_hm, total_mm, total_gr, total_fc, total_rvb, total_rvf, total_rva]})
        df_all = df_all.set_index('YEAR').transpose().reset_index()
        df_all = df_all.rename(columns={'index': 'YEAR'})

        # st.write(df_all)
        # st.stop()

        if i == 0:
            df_all_year = df_all
        else:
            df_all_year = pd.concat([df_all_year, df_all])

    # st.write(df_all_year)
    cols = df_all_year.columns

    fig = go.Figure(data=[go.Table(
        columnwidth=[18, 18],

        header=dict(values=list(cols),
                    fill_color=[color_hex(25)] + [color_hex(83)] * 7,
                    line_color='white',
                    font_color='white',
                    font_size=13,
                    height=28,
                    align=['left', 'center']),
        cells=dict(
            values=[df_all_year[cols[0]], df_all_year[cols[1]], df_all_year[cols[2]], df_all_year[cols[3]], df_all_year[cols[4]],
                    df_all_year[cols[5]], df_all_year[cols[6]], df_all_year[cols[7]]],
            font_size=13,
            height=28,
            fill_color=[color_hex(212)] + [color_hex(262)] * 7,
            line_color='white',
            align=['left', 'right']))
    ])

    fig.update_layout(width=700, height=len(df_all_year) * 28 + 28, margin=dict(l=0, r=0, b=0, t=0))

    return fig


def display_returns(datafile_location):
    st.write ('2024 YTD | R E T U R N S')

    start_date_str = '01-01-2024'
    end_date_str = '12-31-2024'

    start_date = datetime.strptime(start_date_str, '%m-%d-%Y').date()
    end_date = datetime.strptime(end_date_str, '%m-%d-%Y').date()

    st.sidebar.write('Start Date | ' + str(start_date))
    st.sidebar.write('End Date | ' + str(end_date))

    df_returns = data.return_df(datafile_location)

    df_returns = df_returns[df_returns['RETURN DATE'] >= start_date]

    df_returns = df_returns[df_returns['RETURN DATE'] <= end_date]

    df_supplier = df_returns.groupby('SUPPLIER')['QTY'].sum().to_frame().reset_index()

    st.write(df_supplier)
    st.write(df_supplier['QTY'].sum())

    return


def display_top_seller(datafile_location):

    month = select_month()

    year = select_year()

    df1 = data.amazon_df(datafile_location, month, str(year))
    df1['DEALER'] = 'AMAZON'

    df2 = data.zen_df(datafile_location, month, str(year))
    df2['DEALER'] = df2.apply(lambda x: str(x.iloc[4]).upper(), axis=1)  # convert dealer name to upper case
    df2 = df2[df2['DEALER'] != 'AMAZON']
    df2 = df2[['SKU', 'QTY', 'DEALER']]
    df2.replace('MEGAN COLLIER', 'CABINETS TO GO', inplace=True)  # <<<<<<<<<<<<<<<<

    df = pd.concat([df1, df2])
    df = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    df = df.groupby(['DEALER', 'SKU'])['QTY'].sum().to_frame().reset_index()
    df = df.sort_values(['QTY', 'SKU'], ascending=[False, True])
    df.reset_index(drop=True, inplace=True)
    df.index = range(1, df.shape[0] + 1)

    df['DEALER'] = df.apply(lambda x: str(x.iloc[0]).strip(), axis=1)
    df = df.loc[lambda row: ~ row['SKU'].str.endswith('-REFURB')]

    dealer = st.sidebar.text_input('DEALER', 'ALL')
    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    if dealer.upper() != 'ALL':
        df_dealer = df.loc[lambda row: row['DEALER'].str.startswith(dealer.upper())]

    else:
        df_dealer = df.copy()

    if model.upper() == 'ALL':
        df_model = df_dealer.copy()
        txt_sku = 'SKU'

    elif model.upper()[0:2] == 'RV':
        df_model = df_dealer.loc[lambda row: row['SKU'].str.startswith(model.upper())]
        txt_sku = 'SKU'

    else:
        df_model = df_dealer.loc[lambda row: row['SKU'].str.endswith(model.upper())]
        txt_sku = 'Color'

    n1 = df_model['SKU'].tolist()
    n1_unique = list(dict.fromkeys(n1))

    n = min([len(n1_unique), 35])
    # st.write(n)
    # st.write(df_model)

    txt = 'SKU-WISE TOP SELLER | ' + month + '-' + str(year) + ' | ' + txt_sku + ' (' + model.upper() + '): ' + str(len(n1_unique))

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(245)}; text-align:left; font-size: 18px ;border-radius:2%; '
        f'line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

    st.write('')

    mygrid = ut.make_grid(9, 6)  # (5, 4)  # (rows, cols)
    col = 0
    row = 0

    for i in range(0, n):

        sku = df_model['SKU'].tolist()
        sku_unique = list(dict.fromkeys(sku))

        df_temp = df_model[df_model['SKU'] == sku_unique[i]]
        total = df_temp['QTY'].sum()

        df_temp = df_temp[0:2]  # display 1st and 2nd highest

        # for j in range (0, len(df_temp)):
        fig = go.Figure(data=[go.Table(
            columnwidth=[25, 8],

            header=dict(values=['DEALER', 'QTY'],
                        fill_color=[color_hex(357)] + [color_hex(66)] * 4 + [color_hex(118)],
                        line_color='white',
                        font_color='white',
                        font_size=12,
                        height=24,
                        align=['left', 'center']),

            cells=dict(
                    values=[df_temp['DEALER'], df_temp['QTY']],
                    font_size=12,
                    height=24,
                    fill_color=[color_hex(304)] + [color_hex(12)] * 4 + ['lightblue'],
                    line_color='white',
                    align=['left', 'center']))
               ])

        txt2 = str(i+1) + '. ' + str(sku_unique[i]) + ' | ' +  str(ut.format_num(total))
        mygrid[row][col].markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(240)}; text-align:left; font-size: 14px ;border-radius:2%; '
                f'line-height:0em; margin-top:0px"> {txt2} </p>', unsafe_allow_html=True)

        fig.update_layout(width=700, height=80, margin=dict(l=0, r=0, b=0, t=0))

        mygrid[row][col].plotly_chart(fig, use_container_width=True)

        if col < 4:
            col += 1

        else:
            col = 0
            row += 1

    col1, col2 = st.columns([1, 2.2])
    with col1:
        st.write('DATA:')
        # build AgGrid options
        gb = GridOptionsBuilder.from_dataframe(df_model)
        gb.configure_grid_options(rowHeight=25)
        gb.configure_grid_options(headerHeight=25)
        gb.configure_grid_options(enableCellTextSelection=True)
        gb.configure_column('DEALER', wrapText=False, width=200)
        gb.configure_column('SKU', wrapText=False, width=80)
        gb.configure_column('QTY', wrapText=False, width=60)
        grid_options = gb.build()

        AgGrid(df_model, grid_options, height=400, fit_columns_on_grid_load=True)

    return