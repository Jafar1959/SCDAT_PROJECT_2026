import streamlit as st
import pandas as pd

from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex


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

    # ------------ Calculate WH Stock in Month (Avoid divide-by-zero) _____________________
    df['MONTH'] = (df['WH_QTY'] / df['FORECAST'].replace(0, pd.NA)).fillna(0).round(2)

    # =================== FILTER BY SUPPLIER, MODEL AND COLOR ===================================
    df = utils.supplier_model_query(df, supplier, model)    # query on supplier and model

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')  # accessories, boxes, dummy faucets, faucet parts
    df_sink = utils.exclude_sku_prefixes(df, prefixes)

    # _____________ Remove rows If SKU has BOTH NaN + empty strings _____________________
    df = df[df['SKU'].notna() & (df['SKU'].str.strip() != '')]
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


def _container_loading_prep(df_raw, df_product, supplier, model, exclude_prefixes):
    df = pd.merge(df_raw, df_product, on=["SKU"], how="left")[
        ["PO", "SKU", "SUPPLIER", "LOADING DATE", "QTY"]
    ]

    df = utils.exclude_sku_prefixes(df, exclude_prefixes)

    df = utils.supplier_model_query(df, supplier, model)
    df["LOADING DATE"] = pd.to_datetime(df["LOADING DATE"]).dt.to_period("M")
    return df


def extend_to_four_months(month_list):
    # Convert strings to datetime
    dates = [datetime.strptime(m, "%b-%y") for m in month_list]

    # Add months until length is 4
    while len(dates) < 4:
        last = dates[-1]
        # Calculate next month (handle year rollover)
        year = last.year + (last.month // 12)
        month = (last.month % 12) + 1
        next_date = datetime(year, month, 1)
        dates.append(next_date)

    # Convert back to required format and limit to 4
    return [d.strftime("%b-%y") for d in dates[:4]]


def container_loading_graph(datafile_location, supplier, model):

    exclude_prefixes = ('RVA', 'RBX', 'RDM', 'RVP')  # accessories, packing boxes, dummy faucet & faucet parts

    df_product = data.product_df(datafile_location)[['SKU', 'SUPPLIER']]
    df_incoming, df_received_raw, _ = data.container_df(datafile_location)

    df_ocean = _container_loading_prep(df_incoming, df_product, supplier, model, exclude_prefixes)  # filter datafile
    df_ocean_copy = df_ocean.copy()

    df_ocean = (
        df_ocean.groupby("LOADING DATE", sort=False)["QTY"]
        .sum()
        .rename("OCEAN")
        .reset_index()
    )

    ocean_month_periods = df_ocean["LOADING DATE"].unique()

    df_received = _container_loading_prep(df_received_raw, df_product, supplier, model, exclude_prefixes)   # filter datafile
    df_received = df_received[df_received["LOADING DATE"].isin(ocean_month_periods)]
    df_received_copy = df_received.copy()

    df_received = (
        df_received.groupby("LOADING DATE", sort=False)["QTY"]
        .sum()
        .rename("RECEIVED")
        .reset_index()
    )

    df = pd.merge(df_ocean, df_received, on=["LOADING DATE"], how="outer")
    df = df.fillna(0)
    df = df.sort_values("LOADING DATE", ascending=True)

    df["LOADING DATE"] = df["LOADING DATE"].dt.strftime("%b-%y")

    if len(df) == 0:
        today = datetime.today()
        current_month = today.strftime("%b-%y")
        df = pd.DataFrame(
            {"LOADING DATE": [current_month], "OCEAN": [0], "RECEIVED": [0]}
        )

    df["LOADING DATE"] = df["LOADING DATE"].astype(str)

    extended = extend_to_four_months(df["LOADING DATE"].tolist())
    extra_labels = extended[len(df) :]
    if extra_labels:
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    {
                        "LOADING DATE": extra_labels,
                        "OCEAN": 0,
                        "RECEIVED": 0,
                    }
                ),
            ],
            ignore_index=True,
        )

    # ================== create Plotly figure =================================
    fig = go.Figure()

    # received bars
    fig.add_trace(go.Bar(
        x=df["LOADING DATE"],
        y=df["RECEIVED"],
        text=df['RECEIVED'],
        textposition='inside',
        textfont=dict(size=11, family='Arial', color='black'),
        marker=dict(color=color_hex(153), line=dict(color=color_hex(154), width=1)),
        name="Received"
    ))

    # not received bars
    fig.add_trace(go.Bar(
        x=df["LOADING DATE"],
        y=df["OCEAN"],
        text=df['OCEAN'] + df['RECEIVED'],
        textposition='inside',
        textfont=dict(size=11, family='Arial', color='black'),
        marker=dict(color=color_hex(21), line=dict(color=color_hex(154), width=1)),
        name="In Ocean"
    ))

    # stack the bars
    fig.update_layout(
        barmode="stack",
        # title="Container Quantity by Month",
        # xaxis_title="Month",
        # yaxis_title="Quantity"
    )

    # position legend to top-right
    fig.update_layout(
        legend=dict(
            x=0.70,
            y=0.90
        )
    )

    if all(y == 0 for y in df['OCEAN']):
        fig.update_yaxes(range=[0, 1], dtick=1)  # force visible range
    else:
        fig.update_yaxes(range=[0, None])

    fig.update_layout(height=315, margin=dict(l=0, r=0, b=0, t=0))

    st.plotly_chart(fig, width='stretch')

    # st.dataframe(df_ocean)
    # st.dataframe(df_received)
    # st.dataframe(df)

    return df_ocean_copy, df_received_copy


def weekly_container_arrival_chart(datafile_location, supplier, model):

    # unpack data
    df, df_sum = data.weekly_container_arrival_df(datafile_location, supplier, model)

    # st.write(df)
    # utils.download_csv(df, "DLLLL")

    # ================== create Plotly figure =================================
    fig = go.Figure()

    # received bars
    fig.add_trace(go.Bar(
        x=df_sum['month_week'],
        y=df_sum['QTY'],
        text=df_sum['PO_QTY'],
        textposition='inside',
        textfont=dict(size=11, family='Arial', color='black'),
        marker=dict(color=color_hex(190), line=dict(color=color_hex(187), width=1)),
        #name="Received"
    ))

    if all(y == 0 for y in df['QTY']):
        fig.update_yaxes(range=[0, 1], dtick=1)  # force visible range
    else:
        fig.update_yaxes(range=[0, None])

    fig.update_layout(height=344, margin=dict(l=0, r=0, b=0, t=0))

    # st.plotly_chart(fig, width='stretch')


    # -------------------- Incoming Container Chart -----------------

    df_filtered = df[df['PO'] != 0].copy()

    # st.write(df)

    # 2. Convert date (optional but recommended)
    df_filtered['ODDO_ETA'] = pd.to_datetime(df_filtered['ODDO_ETA'])

    # 3. Group and aggregate
    df_summary = (
        df_filtered
        .groupby(['ODDO_ETA', 'PO'], as_index=False)['QTY']
        .sum()
    )

    # 4. Format date only (no time)
    df_summary['ODDO_ETA'] = df_summary['ODDO_ETA'].dt.strftime('%Y-%m-%d')

    # 5. Create Plotly table
    fig1 = go.Figure(data=[go.Table(
        header=dict(
            values=['DATE', 'PO', 'TOTAL QTY'],
            fill_color=[color_hex(97)],
            line_color='white',
            font_color='white',
            font_size=14,
            height=30,
            align='center',
                ),

        cells=dict(
            values=[
                df_summary['ODDO_ETA'],
                df_summary['PO'],
                df_summary['QTY']
            ],
            font_size=14,
            height=30,

            fill_color=[['white', '#f2f2f2'] * (len(df_summary) // 2 + 1)],
            align='center'
        )
    )])

    fig1.update_layout(height=500, margin=dict(l=0, r=0, b=0, t=0))

    # st.plotly_chart(fig1, width='stretch')

    return fig, fig1


def inventory_level_projection_graph(datafile_location, supplier, model):   #df, supplier, avg_sales_per_week, current_month_sales):
    supplier_limits = {
        'ALL': 60000,
        'Aquacubic': 2500,
        'Bomeijia': 600,
        'Carysil': 300,
        'CAE Sanitary': 400,
        'Changie': 400,
        'Elleci': 6000,
        'Galassia': 500,
        'Huayi': 1000,
        'Nicos': 300,
        'Plados': 300,
        'Speed': 30000,
        'Speed Vietnam': 12000,
        'Stile Libero': 1250,
        'UAE Fireclay': 250,
        'Wisdom': 70,
        'Xindeli': 2500,
        'Yalos': 100,
        }

    h_line = supplier_limits.get(supplier, 0)

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')     # accessories, boxes, dummy faucets, faucet parts

    df_inventory = data.inventory_df(datafile_location)[['SKU', 'SUPPLIER', 'Existing Qty']]
    df_inventory = utils.supplier_model_query(df_inventory, supplier, model)

    df_inventory = utils.exclude_sku_prefixes(df_inventory, prefixes)

    # st.write(df_inventory)

    total_inventory = df_inventory['Existing Qty'].sum()

    # st.write(total_inventory)

    df, df_sum = data.weekly_container_arrival_df(datafile_location, supplier, model)
    df_sum = df_sum[['month_week', 'QTY']]
    qty_arr = df_sum['QTY'].tolist()

    # st.write(df_sum)
    # st.write(qty_arr)
    # st.stop()

    df_30d_sale = data.last_30_days_sales_df(datafile_location, supplier, model)

    df_30d_sale = utils.exclude_sku_prefixes(df_30d_sale, prefixes)

    avg_weekly_sale = round(df_30d_sale['30_Day_Sale'].sum() * 7/30, 2)

    # st.write(df_30d_sale)
    # st.write(avg_weekly_sale)
    # st.stop()

    inventory_level: list = [round(total_inventory, 2)]

    for i in range(0, len(qty_arr)):
        qty_new =round(inventory_level[i] + qty_arr[i] - avg_weekly_sale, 2)
        if qty_new < 0:
            qty_new = 0
        inventory_level.append(qty_new)

    inventory_level.pop()   # remove last value of the list

    # st.write(inventory_level)

    df_sum['inventory_level'] = inventory_level


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sum['month_week'],
                             y=df_sum['inventory_level'],
                             fill='tozeroy',  # fill down to xaxis
                             fillcolor='rgba(100, 149, 237, 0.2)',
                             mode='lines',
                             line={'dash': 'solid', 'color': color_hex(10)},
                             name=""
                             ))

    if model.upper() == 'ALL' and max(df_sum['inventory_level']) >= h_line:
        fig.add_annotation(x=7, y=h_line,
                       text='Max Inventory | ' + str(utils.format_num(h_line)),
                       font=dict(size=14, family='Book Antiqua',
                                 color=color_hex(10)),
                       showarrow=False)

    y = max(df_sum['inventory_level'])/2

    fig.add_annotation(x=3, y=y * 0.9,  #h_line/1.6,
                       text='Average Sales/Week: ' + str(utils.format_num(avg_weekly_sale)),
                       font=dict(size=14, family='Book Antiqua', color='Maroon'),
                       showarrow=False,
                       align="left"
                       )

    # now = datetime.now()
    # total_days = calendar.monthrange(now.year, now.month)[1]

    fig.add_annotation(x=3, y=y * 0.7,
                       text='Last 30 days Sales: ' + str(utils.format_num(round(avg_weekly_sale *30/7, 0))),
                       font=dict(size=14, family='Book Antiqua', color='Maroon'),
                       showarrow=False,
                       align="left"
                       )

    # current_inventory = df.iloc[0, 1]
    #
    fig.add_annotation(x=3, y=y * 0.5,
                       text='Stock: ' + str(round(total_inventory/avg_weekly_sale, 2)) + ' weeks',
                       font=dict(size=14, family='Book Antiqua', color=color_hex(125)),
                       showarrow=False,
                       align = "left"
                       )
    #
    fig.update_yaxes(gridwidth=2)
    fig.update_xaxes(
        # dtick="M1",  # sets minimal interval to month
        # tickformat="%d-%b-%Y",  # "%b %Y",  # sets the date format
        # tickangle=90,  # rotates the tick labels
        # tickvals=df_sum['month_week'],
        showgrid=True,
        gridwidth=2,
                    )

    fig.update_layout(xaxis_title="", yaxis_title="Inventory",
                      font=dict(
                          family="Book Antiqua",
                          size=15,
                          color='black'),
                      )
    fig.update_layout(height=400, margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, width='stretch')

    # st.write(df_sum)

    return fig


def sales_trend_graph(datafile_location, suppliers, forecast_month):
    # _____________ create 36-months name list,start from the previous month __________________
    start = datetime.now() - relativedelta(months=1)

    months = [
        (start - relativedelta(months=i)).strftime("%b-%y")
        for i in range(36)
    ]

    months = months[::-1]    # << Reverse month order to oldest → newest

    start_month = st.sidebar.selectbox("MONTH START", months, index=len(months)-13)
    end_month = st.sidebar.selectbox("MONTH END", months, index=len(months)-1)

    start_index = months.index(start_month)
    end_index = months.index(end_month)

    month_list = months[start_index: end_index + 1]

    supplier = st.sidebar.selectbox("SUPPLIER", suppliers)

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    show_forecast = st.sidebar.checkbox('SHOW FORECAST', value=True)
    show_loading = st.sidebar.checkbox('SHOW LOADING', value=True)
    show_received = st.sidebar.checkbox('SHOW RECEIVED', value=True)

    # _______________ Get sales data _________________________________________
    df_sales_summary, df_sales_sku = data.sales_trend_df(datafile_location, supplier, model, months)

    # st.write(df_sales_summary)
    # st.write(df_sales_sku)
    # st.stop()

    df_sales_summary = df_sales_summary[df_sales_summary['MONTH'].isin(month_list)]


    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sales_summary['MONTH'],
                             y=df_sales_summary['SALES'],
                             mode='lines',
                             line={'dash': 'solid', 'color': 'darkred'},
                             name="SALES",
                             ))

    fig.add_trace(go.Scatter(x=df_sales_summary['MONTH'],
                             y=df_sales_summary['12M_AVG'],
                             mode='lines',
                             line={'dash': 'solid', 'color': 'blue'},
                             name="12M RUNNING AVG",
                             ))

    fig.add_annotation(
        x=len(df_sales_summary)-1,
        y=df_sales_summary.iloc[-1, 1],    # value of 2nd col and last row
        text=str(utils.format_num(round(df_sales_summary.iloc[-1, 1], 0))),
        showarrow=False,
        yshift=10,
        font=dict(
            color="maroon",
            size=14,
            family="Arial Black")
        )

    fig.add_annotation(     # _____________ show first value of running average ____________
        x = len(df_sales_summary)-12,
        y = df_sales_summary.iloc[-12, 2],   # value of 3rd col and last row
        text = str(utils.format_num(round(df_sales_summary.iloc[-12, 2], 0))),
        showarrow = False,
        yshift=10,
        font=dict(
            color="blue",
            size=14,
            family="Arial Black")
            )

    fig.add_annotation( # _____________ show last value of running average _______________
        x=len(df_sales_summary) - 1,
        y=df_sales_summary.iloc[-1, 2],  # value of 3rd col and last row
        text=str(utils.format_num(round(df_sales_summary.iloc[-1, 2], 0))),
        showarrow=False,
        yshift=10,
        font=dict(
            color="blue",
            size=14,
            family="Arial Black")
        )

    # _______________ Get forecast data _________________________________________________
    values1 = data.forecast_trend_df(datafile_location, supplier, model, month_list)

    df_forecast_summary = values1[0]    # MONTH | FORECAST
    df_sink_sku = values1[1]    # SKU | SUPPLIER | FORECAST | MONTH

    df_sink = df_sink_sku[~df_sink_sku['SKU'].astype(str).str.contains("RVA")]
    total_sku = df_sink['SKU'].unique()
    total_sku = total_sku.tolist()
    total_sku = [x for x in total_sku if x != 0]

    total_sku = len(total_sku)

    if show_forecast:
        fig.add_trace(go.Scatter(x=df_forecast_summary['MONTH'],
                                 y=df_forecast_summary['FORECAST'],
                                 # fill='tozeroy',  # fill down to xaxis
                                 fillcolor='rgba(240, 128, 128, 0.2)',
                                 mode='lines',
                                 line={'dash': 'dash', 'color': 'grey'},
                                 name="FORECAST"))

    y_axis_max = max([df_sales_summary['SALES'].max(), df_forecast_summary['FORECAST'].max()])      # get max value for y-axis

    fig.update_yaxes(range=[0, y_axis_max])

    average_sales = round(df_sales_summary['SALES'].sum() / len(df_sales_summary), 0)

    # _____________ Get loading and received data _____________________________________________
    df_loading, df_received = data.loading_trend_df(datafile_location, supplier, model, month_list)

    average_loading = round(df_loading['QTY'].sum() / len(df_sales_summary), 0)

    average_received = round(df_received['QTY'].sum() / len(df_sales_summary), 0)

    if show_loading:
        fig.add_trace(go.Bar(x=df_loading['LOADING DATE'],      # add qty loading bar
                             y=df_loading['QTY'],
                             text=df_loading['QTY'],
                             textposition='inside',
                             textfont=dict(size=11, family='Arial', color='black'),
                             marker=dict(color=color_hex(21), line=dict(color=color_hex(33), width=1)),
                             name="QTY LOADED",
                             ))

    if show_received:
        fig.add_trace(go.Bar(x=df_received['RECEIVED DATE'],    # add qty received bar
                             y=df_received['QTY'],
                             text=df_received['QTY'],
                             textposition='inside',
                             textfont=dict(size=11, family='Arial', color='black'),
                             marker=dict(color=color_hex(153), line=dict(color=color_hex(96), width=1)),
                             name="QTY RECEIVED",
                                 ))

    y_axis_max = max([df_sales_summary['SALES'].max(), df_forecast_summary['FORECAST'].max(), df_loading['QTY'].max(), df_received['QTY'].max()])

    fig.update_yaxes(range=[0, y_axis_max])

    # ____________________________ Display Page-1: Title  _____________________________________________
    utils.show_header(supplier + ' Sales Trend || ' + utils.get_todays_date(), "-45px")

    # --------------------- Display Sub-headers -------------------------------------------------------------
    col_a, col_b, col_c, col_d, col_e, col_f = st.columns([1, 1, 1, 1, 1, 0.18])
    color = [color_hex(19), color_hex(19), color_hex(56), color_hex(35), color_hex(96)]
    font = '18px'
    cols = [col_a, col_b, col_c, col_d, col_e, col_f]
    txt = [ 'MODEL: ' + model.upper(),
            'TOTAL SKU: ' + utils.format_num(str(total_sku)),
            str(len(df_sales_summary)) + 'M AVG. SALES: ' + utils.format_num(str(average_sales)),
            'AVG. SHIPMENT: ' + utils.format_num(str(average_loading)),
            'AVG. RECEIVED: ' + utils.format_num(str(average_received)),
             ]

    for i in range (0, len(cols)-1):
        with cols[i]:
            st.markdown(
                f"""
                <div style="
                    display:inline-block;
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

    # ____________________________ Display Page-1: Sales Trend  _____________________________________________
    col1, col2 = st.columns([3, 0.15])
    with col1:

        fig.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=13), x=0.15, y=1.0))
        fig.update_layout(height=370, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, width='stretch')

    # -------------------- Display Page-1: Inventory Mix, In-Ocean and Weekly Arrival _____________________
    col3, col4, col5, col6 = st.columns([1, 0.7, 1, 0.1])
    with col3:      # ______________ Display Inventory Mix _______________________
        txt = 'Warehouse Inventory Mix'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        inventory_dashboard(datafile_location, forecast_month, supplier, model)

    with col4:      # _______________ Display In-ocean & Received Qty ________________
        txt = 'In-ocean & Received Quantity'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        df_ocean, df_received = container_loading_graph(datafile_location, supplier, model)
        # df_ocean = values[0]

        # st.write(df_ocean)
        # utils.download_csv(df_ocean, 'df_ocean')

        # df_received = values[1]

    with col5:      # _______________ Display Weekly Container Arrival ________________________

        fig, fig1 = weekly_container_arrival_chart(datafile_location, supplier, model)

        txt = 'Weekly Container Arrival'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig, width='stretch')

    # ------------- Display Page-2: Inventory < 1 Month, Container Arrival Schedule, Weekly Projection -------
    utils.show_header(supplier + ' ... p/2', top_margin = "15px")

    col7, col8, col9, col10 = st.columns([1, 0.7, 1, 0.1])

    with col7:      # _________________ Inventory < 1-Month Forecast ______________________________________
        df_low, _ = data.low_inventory_df(datafile_location, forecast_month, supplier, model)
        # st.write(df_low)

        df_low.columns = [str(col) for col in df_low.columns]   # convert column heading to str
        cols = df_low.columns

        # st.write(cols)
        # add row colors
        df_low['bg_color'] = ['rgb(255, 255, 255)' if i % 2 == 0 else 'rgb(255, 228, 196)' for i in range(len(df_low))]

        fig = go.Figure(data=[go.Table(
            columnwidth=[16, 14],
            header=dict(values=cols, #df_low.columns,
                        fill_color=[color_hex(135)],
                        line_color='white',
                        font_color='white',
                        font_size=14,
                        height=30,
                        align=['left', 'center']),
            cells=dict(
                values=[df_low[col] for col in cols],
                font_size=14,
                height=30,
                # font_color=[df_monthly_group.font_color],
                fill_color=[df_low.bg_color],
                # line_color='white',
                align=['left', 'center']))
        ])

        fig.update_layout(height=500, margin=dict(l=0, r=0, b=0, t=0))

        txt = 'Inventory < 1 Month Forecast | Total SKU: ' + str(len(df_low))
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:4px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig, width='stretch')


    with col8:      # _______________________ Container Arrival Schedule ____________________________
        txt = 'Container Arrival Schedule'
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
                f' line-height:0em; margin-top:4px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig1, width='stretch')


    with col9:      # ____________________ Weekly Inventory Projection ____________________________________
        txt = 'Weekly Inventory Projection'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:28px"> {txt} </p>', unsafe_allow_html=True)

        inventory_level_projection_graph(datafile_location, supplier, model)

    # _________________ Display Download Links __________________________________________________
    txt = 'Data Download Links _______________________'
    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 20px ;border-radius:1%;'
        f' line-height:0em; margin-top:28px"> {txt} </p>', unsafe_allow_html=True)

    utils.download_csv(df_sales_sku, 'Download Sales Data')
    utils.download_csv(df_sink_sku, 'Download Forecast Data')

    utils.download_csv(df_ocean, 'Download Container In-Ocean')
    utils.download_csv(df_received, 'Download Container Received')


    utils.download_csv(df_loading, 'Download Monthly Shipment Data')
    utils.download_csv(df_received, 'Download Monthly Received Data')

    utils.download_csv(df_low, 'Download Low Inventory')

    return
