import pandas as pd
from pathlib import Path, PureWindowsPath
import os
from datetime import datetime
import calendar
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
import time

from scdat_colors_26 import color_hex
import scdat_utils_26 as utils
import scdat_data_26 as data

import streamlit as st

def get_file_date(path):
    dt = os.path.getmtime(path)  # get date and time number
    dt = datetime.fromtimestamp(dt)  # convert to date & time
    date1 = dt.date()
    time1 = dt.time()
    return date1, time1

def data_file_status(datafile_location):
    # ================= return a plotly table with data file status =================================
    # get current month number, short month name and year
    today = datetime.now().date()
    current_month_no = today.month  # int
    short_month_name = calendar.month_abbr[current_month_no]    # str
    current_year = today.year   # int

    # convert month number to two digit - '01', '02' ----------
    month_no_str = '0' + str(current_month_no) if current_month_no < 10 else str(current_month_no)

    # define file path --------------------
    file_prefix = str(current_year) + '_' + month_no_str + '_'

    file_paths = ['CCS\\CCS_Copy.xlsx',
                  # 'CCS\\Entry_Summary.csv',
                  'CCS\\Shipment_Report.xlsx',
                  'Inventory\\Container.csv',
                  'Inventory\\Inventory.csv',
                  'Inventory\\FBA_Inventory.csv',
                  'Inventory\\WH_Inventory_Qty.csv',
                  'Inventory\\Inventory_History.xlsx',
                  'Inventory\\Backorder.csv',
                  'Inventory\\ZEN_Purchase_Order.csv',
                  'Inventory\\Returns.csv',
                  'Inventory\\Return SCAN responses.xlsx',
                  'Amazon\\' + file_prefix + 'Amazon.csv',
                  'Oddo\\' + file_prefix + 'Oddo.csv',
                  'Sales\\Monthly_Sales\\MONTHLY\\' + str(current_year)[2:4] + month_no_str + '_Sales_' + short_month_name +
                  '-' + str(current_year)[2:4] + '.csv',
                  'Sales\\Monthly_Sales\\Dealers_Order.csv',
                  ]

    # create dataframe with all file path ---------------------------
    df = pd.DataFrame({})
    for i in range(0, len(file_paths)):
        f = file_paths[i].split('\\')
        folder = f[0]

        file = f[1]
        if file == 'Monthly_Sales' and f[2] == 'MONTHLY':
            file = f[3]
        elif file == 'Monthly_Sales':
            file = f[2]

        path = Path(PureWindowsPath(datafile_location + file_paths[i]))
        values = get_file_date(path)
        date1 = values[0]
        time1 = values[1]
        time1_str = str(time1)[0:5]

        d = '0'
        status = ''
        if date1 < today:
            d = str(today - date1).split(' ')

            status = d[0] + ' ' + d[1][:-1] + ' old'

        if d[0] == '0':
            status = ''

        dt = str(date1).split(' ')
        date_str = dt[0]
        df1 = pd.DataFrame({'Folder': [folder],
                            'File Name': [file],
                            'Date': [date_str],
                            'Time': [time1_str],
                            'Status': [status],
                            })

        df = pd.concat([df, df1])

    # Add alternating 'color1' and 'color2' values in the rows
    if len(df) > 1:
        df['Color'] = ['rgb(245, 255, 250)' if i % 2 == 0 else 'rgb(224, 238, 224)' for i in range(len(df))]

    cols = df.columns
    # ========== Display Plotly Table ===========================
    fig = go.Figure(data=[go.Table(
        columnwidth=[14, 30, 15, 15, 15],

        header=dict(values=[cols[0], cols[1], cols[2], cols[3], cols[4]],
                    fill_color=[color_hex(196)],
                    line_color='white',
                    font_color='black',
                    font_size=16,
                    height=35,
                    align=['left', 'left', 'center', 'center', 'center']),
        cells=dict(values=[df.Folder, df['File Name'], df.Date, df.Time, df.Status],
                   font_size=14,
                   height=35,
                   fill_color=[df['Color']],
                   line_color='white',
                   align=['left', 'left', 'center', 'center', 'left']))
                ])

    # add outer boarder around the table
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,  # full canvas
        line=dict(color=color_hex(32), width=3),
        layer="above"
        )

    fig.update_layout(height=len(df)*35 + 35, margin=dict(l=0, r=0, b=0, t=0))
    return fig


def container_dashboard(datafile_location):

    # get incoming containers from CCS =====================
    df_ccs = data.ccs_df(datafile_location)
    df_ccs = df_ccs[df_ccs['Loading Date'] != 'BLANK']

    df_ccs = df_ccs[['CONTAINER NO.', 'FROM', 'Loading Date', 'Delivered Date']]
    df_ccs = df_ccs.rename(columns={'CONTAINER NO.': 'PO', 'FROM': 'Supplier'})

    df_ccs['Loading Date'] = pd.to_datetime(df_ccs['Loading Date'])
    df_ccs['Loading Date'] = df_ccs['Loading Date'].dt.to_period('M')

    # create month-wise container loading dataframe ========================
    df_loading = df_ccs.groupby(['Loading Date', 'Supplier'])['PO'].count().to_frame().reset_index()

    # # create month-wise container receiving dataframe ========================
    df_receiving = df_ccs[df_ccs['Delivered Date'] != 'BLANK']  # received POs only
    df_receiving = df_receiving.groupby(['Loading Date', 'Supplier'])['PO'].count().to_frame().reset_index()

    # merge Loading and Receiving df ==================================
    df1 = pd.merge(df_loading, df_receiving, on=['Loading Date', 'Supplier'], how='left')
    df1 = df1.rename(columns={'PO_x': 'Loading', 'PO_y': 'Receiving'})

    # get current month and previous 3 month like 2025-11, 2025-10 etc. ==========================================
    now = datetime.now()     # Get current date
    month_list = [(now - relativedelta(months=i)).strftime('%Y-%m') for i in range(5)]  # Generate current and previous 4 months in YYYY-MM format
    month_list.reverse()

    # split dataframe month wise and add side-by-side =====================================
    df2 = pd.DataFrame({})

    for m in month_list:
        df_temp = df1[df1['Loading Date'] == m]
        df_temp = df_temp.rename(columns={'Loading': 'Loaded (' + str(m) + ')', 'Receiving': 'Received (' + str(m) + ')'})

        # st.write(df_temp)
        df_temp = df_temp.drop('Loading Date', axis=1)      # drop column 'Loading Date'

        if m == month_list[0]:
            df2 = df_temp
        else:
            df2 = pd.merge(df2, df_temp, on='Supplier', how='outer')

    # calculate the total in-ocean containers: Loaded = (col 1, 3, 5, 7) - Received (2, 4, 6, 8)
    df2['In-Ocean Container'] = df2.iloc[:, [1, 3, 5, 7, 9]].sum(axis=1) - df2.iloc[:, [2, 4, 6, 8, 10]].sum(axis=1)

    # get total inocean quantity per supplier from container_df ======================
    df_container = data.container_df(datafile_location)
    df_ocean = df_container[df_container['STATE'] != 'Received In Warehouse']   # get in-ocean containers only

    df_ocean = df_ocean[['PO', 'SKU', 'QTY']]
    df_ocean = df_ocean.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]     # remove accessories
    df_ocean = df_ocean.loc[lambda row: ~ row['SKU'].str.startswith('RVP')]     # remove faucet accessories
    df_ocean = df_ocean.loc[lambda row: ~ row['SKU'].str.startswith('RBX')]     # remove packing box

    df_ocean['PO'] = df_ocean['PO'].str[:4]     # keep only 4-digit of PO similar to CCS

    df_ocean = df_ocean.groupby('PO')['QTY'].sum().to_frame().reset_index()     # consolidate after removing -A or -B, if any

    df_ocean = pd.merge(df_ocean, df_ccs, on=["PO"], how='left')    # get supplier name per container number

    df_ocean = df_ocean.groupby('Supplier')['QTY'].sum().to_frame().reset_index()   # get in-ocean quantity per supplier

    df2 = pd.merge(df2, df_ocean, on=["Supplier"], how='left')    # add in-ocean quantity per supplier

    df2 = df2.rename(columns={'QTY': 'In-Ocean Qty'})
    df2['In-Ocean Qty'] = df2['In-Ocean Qty'].fillna(0)

    # Calculate totals for all columns except the first ====================
    totals = df2.iloc[:, 1:].sum()
    total_row = pd.DataFrame([['Total'] + totals.tolist()], columns=df2.columns) # Create a new row with a label in the first column
    df2 = pd.concat([df2, total_row], ignore_index=True)    # Append to the original DataFrame

    # create plotly table ==============================
    df2['In-Ocean Qty'] = df2['In-Ocean Qty'].apply(lambda x: f"{round(x):,}")      # format number and remove floating point like 12,345

    df2 = df2.fillna('')        # replace null by ''
    df2['In-Ocean Container'] = df2['In-Ocean Container'].replace(0, '')        # replace zero by ''

    fig = go.Figure(data=[go.Table(
        columnwidth=[18] + [15]*10,

        header=dict(values=df2.columns,
                    fill_color=[color_hex(135)] + [color_hex(60)]*4 + [color_hex(46)]*2 +[color_hex(113)]*2 + [color_hex(60)]*2 + [color_hex(238)]
                               + [color_hex(113)],
                    line_color='white',
                    font_color='white',
                    font_size=14,
                    height=35,
                    align=['left', 'center']),

        cells=dict(values=[df2[col] for col in df2.columns],
                   font_size=16,
                   height=35,
                   fill_color=[color_hex(17)] + [color_hex(150)]*4 + [color_hex(262)]*2 +[color_hex(185)]*2 + [color_hex(150)]*2 + ['lightpink'] + [
                       'lightblue'],
                   line_color='white',
                   align=['left'] + ['center']*11 + ['right']))
        ])

    height = len(df2) * 35 + 35 + 20
    fig.update_layout(width=1565, height=height, margin=dict(l=0, r=0, b=0, t=0))

    return fig


def monthly_container_loading(datafile_location):
    current_year = datetime.today().year
    start_date = pd.to_datetime(str(current_year) + '-01-01')

    df_ccs = data.ccs_df(datafile_location)
    df = df_ccs[['CONTAINER NO.', 'Loading Date']]

    df = df[df['Loading Date'] != 'BLANK']

    df['Loading Date'] = pd.to_datetime(df['Loading Date'])

    df = df[df['Loading Date'] >= start_date]
    df['Loading Date'] = df['Loading Date'].dt.to_period('M')
    df_monthly_group: object = df.groupby('Loading Date')['CONTAINER NO.'].count().to_frame().reset_index()

    df_monthly_group.reset_index(drop=True, inplace=True)
    df_monthly_group.index = range(1, df_monthly_group.shape[0] + 1)

    # set color for alternative rows
    if len(df_monthly_group) > 1:
        df_monthly_group['bg_color'] = ['rgb(189, 215, 231)' if i % 2 == 0 else 'rgb(255, 228, 196)' for i in range(len(df_monthly_group))]
        df_monthly_group['font_color'] = ['rgb(139, 34, 82)' if i % 2 == 0 else 'rgb(69, 139, 116)' for i in range(len(df_monthly_group))]

    # add total line and color ++++++++++++++++
    index = len(df_monthly_group) + 1
    total_container = df_monthly_group['CONTAINER NO.'].sum()
    df_monthly_group.loc[index] = ['Total', total_container, color_hex(10), color_hex(417)]  # add total, bg & font colors

    df_monthly_group['Loading Date'] = df_monthly_group['Loading Date'].astype(str)

    # ====================================================================
    fig = go.Figure(data=[go.Table(
        columnwidth=[16, 14],
        header=dict(values=['Month', 'Container'],
                    fill_color=[color_hex(135)],
                    line_color='white',
                    font_color='white',
                    font_size=18,
                    height=34,
                    align=['center']),
        cells=dict(
            values=[df_monthly_group['Loading Date'], df_monthly_group['CONTAINER NO.']],
            font_size=18,
            height=36,
            font_color=[df_monthly_group.font_color],
            fill_color=[df_monthly_group.bg_color],
            line_color='white',
            align=['center', 'center']))
    ])

    fig.update_layout(height=len(df_monthly_group) * 40 + 34, margin=dict(l=0, r=0, b=0, t=0))

    return fig, total_container


def sales_trend_graph(datafile_location, supplier, forecast_month):
    start = time.perf_counter()  # start runtime counter

    number_of_months_in_display = st.sidebar.number_input("MONTHS IN DISPLAY", min_value=6, max_value=24, value=13)

    supplier = st.sidebar.selectbox("SUPPLIER", supplier)

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    show_forecast = st.sidebar.checkbox('SHOW FORECAST', value=True)
    show_loading = st.sidebar.checkbox('SHOW LOADING', value=True)
    show_received = st.sidebar.checkbox('SHOW RECEIVED', value=True)

    # get sales data ==================================================================================
    values = data.sales_trend_df(datafile_location, supplier, model, number_of_months_in_display)
    df_sales = values[0]
    df_sales_all = values[1]

    # st.write(df_sales)
    # st.stop()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_sales['MONTH'],
                             y=df_sales['SALES'],
                             mode='lines',
                             line={'dash': 'solid', 'color': 'darkred'},
                             name="SALES",
                             ))

    # get forecast data ===============================================================================
    month_names = df_sales['MONTH'].tolist()
    values1 = data.forecast_trend_df(datafile_location, supplier, model, month_names)

    df_forecast = values1[0]
    df_forecast_all = values1[1]

    # st.write(df_forecast)
    if show_forecast:
        fig.add_trace(go.Scatter(x=df_forecast['MONTH'],
                                 y=df_forecast['FORECAST'],
                                 # fill='tozeroy',  # fill down to xaxis
                                 fillcolor='rgba(240, 128, 128, 0.2)',
                                 mode='lines',
                                 line={'dash': 'solid', 'color': 'grey'},
                                 name="FORECAST"))


    y_axis_max = max([df_sales['SALES'].max(), df_forecast['FORECAST'].max()])      # get max value for y-axis

    fig.update_yaxes(range=[0, y_axis_max])

    average_sales = round(df_sales['SALES'].sum() / len(df_sales), 0)

    fig.add_hline(y=average_sales, line_width=1, line_dash='solid',
                  annotation_text=str(len(df_sales)) + '-MONTH AVG. SALES | ' + utils.format_num(str(average_sales)),
                  annotation_font_size=14,
                  annotation_font_color=color_hex(140),
                  line_color="green")

    # get loading and received data ===================================================================
    values2 = data.loading_trend_df(datafile_location, supplier, model, month_names)
    df_loading = values2[0]
    df_received = values2[1]

    if show_loading:
        fig.add_trace(go.Bar(x=df_loading['LOADING DATE'],      # add qty loading bar
                             y=df_loading['QTY'],
                             text=df_loading['QTY'],
                             textposition='inside',
                             textfont=dict(
                                 size=11,
                                 family='Arial',
                                 color='black'),
                             marker=dict(color='#FFD39B'),
                             name="QTY LOADED",
                             ))

    if show_received:
        fig.add_trace(go.Bar(x=df_received['RECEIVED DATE'],    # add qty received bar
                             y=df_received['QTY'],
                             text=df_received['QTY'],
                             textposition='inside',
                             textfont=dict(
                                 size=11,
                                 family='Arial',
                                 color='black'),
                                marker=dict(color='#9BCD9B'),
                             name="QTY RECEIVED",
                                 ))

    y_axis_max = max([df_sales['SALES'].max(), df_forecast['FORECAST'].max(), df_loading['QTY'].max(), df_received['QTY'].max()])  #max value for y-axis

    fig.update_yaxes(range=[0, y_axis_max])

    col1, col2 = st.columns([3, 1])

    with col1:
        txt = 'Sales Trend | Supplier: ' + supplier + ' | Model: ' + model.upper() + ' | '+ utils.get_todays_date()

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(67)}; text-align:center; font-size: 18px ;border-radius:2%; '
            f'line-height:0em; margin-top:10px"> {txt} </p>', unsafe_allow_html=True)

        fig.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=13), x=0.1, y=0.9))
        fig.update_layout(width=340, height=410, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, use_container_width=True)

    utils.download_csv(df_sales_all, 'Download Sales')
    utils.download_csv(df_forecast_all, 'Download Forecast')

    end = time.perf_counter()  # stop runtime counter
    st.sidebar.write(f"Runtime: {end - start:.2f} seconds")  # show runtime seconds

    return
