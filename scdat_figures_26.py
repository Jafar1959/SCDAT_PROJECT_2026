import pandas as pd
from pathlib import Path, PureWindowsPath
import os
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


import calendar
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dateutil.relativedelta import relativedelta
import time

from scdat_colors_26 import color_hex
import scdat_utils_26 as utils
import scdat_data_26 as data
import scdat_sales_forecast_dashboard_26 as sfd

import streamlit as st

def get_file_date(path):
    dt = os.path.getmtime(path)  # get date and time number
    dt = datetime.fromtimestamp(dt)  # convert to date & time
    date1 = dt.date()
    time1 = dt.time()
    return date1, time1

def data_file_status_OLD(datafile_location):
    # ================= return a plotly table with data file status =================================
    # get current month number, short month name and year
    today = datetime.now().date()
    current_month_no = today.month  # int
    short_month_name = calendar.month_abbr[current_month_no]    # str
    current_year = today.year   # int

    # convert month number to two digit - '01', '02' ----------
    # month_no_str = '0' + str(current_month_no) if current_month_no < 10 else str(current_month_no)
    month_no_str = f"{current_month_no:02d}"

    # define file path --------------------
    # file_prefix = str(current_year) + '_' + month_no_str + '_'
    file_prefix = f"{current_year}_{month_no_str}_"

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
                  "LOWES\\Lowe's Sales.xlsx",
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

def data_file_status(datafile_location):
    today = datetime.now().date()
    current_month_no = today.month
    short_month_name = calendar.month_abbr[current_month_no]
    current_year = today.year

    month_no_str = f"{current_month_no:02d}"
    file_prefix = f"{current_year}_{month_no_str}_"

    file_paths = [
        'CCS\\CCS_Copy.xlsx',
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
        f'Amazon\\{file_prefix}Amazon.csv',
        f'Oddo\\{file_prefix}Oddo.csv',
        f"Sales\\Monthly_Sales\\MONTHLY\\{str(current_year)[2:]}{month_no_str}_Sales_{short_month_name}-{str(current_year)[2:]}.csv",
        'Sales\\Monthly_Sales\\Dealers_Order.csv',
        "LOWES\\Lowe's Sales.xlsx",
    ]

    rows = []

    for path_str in file_paths:

        # Split path to extract folder and file name
        parts = path_str.split('\\')
        folder = parts[0]

        # Handle nested folder structure (Monthly_Sales case)
        if 'Monthly_Sales' in parts:
            file = parts[-1]  # always take last part as file name
        else:
            file = parts[1]

        # Build full file path using Windows-style path handling
        full_path = Path(PureWindowsPath(datafile_location + path_str))

        # Get file's last modified date and time
        date1, time1 = get_file_date(full_path)

        # Format time (HH:MM)
        time_str = str(time1)[:5]

        # Convert date to string
        date_str = str(date1)

        # Calculate how many days old the file is
        delta_days = (today - date1).days

        # Create status text (only if file is older than today)
        status = f"{delta_days} day{'s' if delta_days != 1 else ''} old" if delta_days > 0 else ""

        # Append row data
        rows.append({
            'Folder': folder,
            'File Name': file,
            'Date': date_str,
            'Time': time_str,
            'Status': status
        })

    # Create DataFrame
    df = pd.DataFrame(rows)

    # alternating row colors (vectorized, faster)
    df['Color'] = ['rgb(245, 255, 250)' if i % 2 == 0 else 'rgb(224, 238, 224)' for i in range(len(df))]

    # Create Plotly table
    fig = go.Figure(data=[go.Table(
        columnwidth=[14, 30, 15, 15, 15],

        # Table header styling
        header=dict(
            values=df.columns[:5],
            fill_color=color_hex(196),
            line_color='white',
            font_color='black',
            font_size=16,
            height=35,
            align=['left', 'left', 'center', 'center', 'center']
        ),

        # Table cell styling and data
        cells=dict(
            values=[df[col] for col in df.columns[:5]],
            font_size=14,
            height=35,
            fill_color=[df['Color']],
            line_color='white',
            align=['left', 'left', 'center', 'center', 'left']
        )
    )])

    # Add outer border around the table
    fig.add_shape(
        type="rect",
        xref="paper", yref="paper",
        x0=0, y0=0, x1=1, y1=1,
        line=dict(color=color_hex(32), width=3),
        layer="above"
    )

    # Adjust layout height dynamically based on number of rows
    fig.update_layout(
        height=len(df) * 35 + 35,
        margin=dict(l=0, r=0, b=0, t=0)
    )

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
    values = data.container_df(datafile_location)
    df_ocean = values[0]   # get in-ocean containers only

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
        columnwidth=[18] + [14]*10,

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

    df_ccs = data.ccs_df(datafile_location)
    df = df_ccs[['CONTAINER NO.', 'Loading Date']]

    df = df[df['Loading Date'] != 'BLANK']

    df['Loading Date'] = pd.to_datetime(df['Loading Date'])

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

    start_date = str(date.today().year) + '- 01'
    df_monthly_group = df_monthly_group[df_monthly_group['Loading Date'] >= start_date]     # container loaded from 1st January onwards

    total_container = df_monthly_group['CONTAINER NO.'].sum()

    df_monthly_group.loc[index] = ['Total', total_container, color_hex(10), color_hex(417)]  # add total, bg & font colors

    df_monthly_group['Loading Date'] = df_monthly_group['Loading Date'].astype(str)

    # st.write(df_monthly_group)

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

    fig.update_layout(height=len(df_monthly_group) * 36 + 34 + 7, margin=dict(l=0, r=0, b=0, t=0))

    return fig, total_container

def sales_trend_graph(datafile_location, supplier, forecast_month):

    # ============== CREATE CHOICES ======================
    # create 36-months name list,start from the previous month
    start = datetime.now() - relativedelta(months=1)

    months = [
        (start - relativedelta(months=i)).strftime("%b-%y")
        for i in range(36)
    ]

    # Reverse to oldest → newest
    months = months[::-1]

    start_month = st.sidebar.selectbox("MONTH START", months, index=len(months)-13)
    end_month = st.sidebar.selectbox("MONTH END", months, index=len(months)-1)

    start_index = months.index(start_month)
    end_index = months.index(end_month)

    month_list = months[start_index: end_index + 1]

    # st.write(month_list)
    # number_of_months_in_display = st.sidebar.number_input("MONTHS IN DISPLAY", min_value=6, max_value=24, value=13)

    supplier = st.sidebar.selectbox("SUPPLIER", supplier)

    utils.show_header(supplier + ' Sales Trend')

    model = st.sidebar.text_input("MODEL / COLOR", "ALL")

    show_forecast = st.sidebar.checkbox('SHOW FORECAST', value=True)
    show_loading = st.sidebar.checkbox('SHOW LOADING', value=True)
    show_received = st.sidebar.checkbox('SHOW RECEIVED', value=True)

    # get months list - start from previous month ============================
    # start = datetime.now() - relativedelta(months=1)
    #
    # month_list = [
    #     (start - relativedelta(months=i)).strftime("%b-%y")
    #     for i in range(number_of_months_in_display)
    #              ]
    #
    # # sort the months list by keeping the month order
    # month_list = sorted(
    #     month_list,
    #     key=lambda x: datetime.strptime(x, "%b-%y")
    #                    )
    #
    # st.write(month_list)

    # get sales data Summary [MONTH, SALES] and Sales by SKU [SKU, SUPPLIER, AMAZON, ODDO, TOTAL, MONTH] based on month_list =======================
    # df_sales_summary, df_sales_sku = data.sales_trend_df(datafile_location, supplier, model, month_list)
    df_sales_summary, df_sales_sku = data.sales_trend_df(datafile_location, supplier, model, months)

    df_sales_summary = df_sales_summary[df_sales_summary['MONTH'].isin(month_list)]

    # st.write(df_sales_summary)

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

    # get forecast data ===============================================================================
    values1 = data.forecast_trend_df(datafile_location, supplier, model, month_list)

    df_forecast_summary = values1[0]    # MONTH | FORECAST
    df_sink_sku = values1[1]    # SKU | SUPPLIER | FORECAST | MONTH

    df_sink = df_sink_sku[~df_sink_sku['SKU'].astype(str).str.contains("RVA")]
    total_sku = df_sink['SKU'].unique()
    total_sku = total_sku.tolist()
    total_sku = [x for x in total_sku if x != 0]
    # st.write(total_sku)
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

    # fig.add_hline(y=average_sales, line_width=1, line_dash='solid',
    #               # annotation_text=str(len(df_sales)) + '-MONTH AVG. SALES | ' + utils.format_num(str(average_sales)),
    #               # annotation_font_size=14,
    #               # annotation_font_color=color_hex(140),
    #               line_color=color_hex(56))

    # get loading and received data ===================================================================
    df_loading, df_received = data.loading_trend_df(datafile_location, supplier, model, month_list)

    # df_loading = values2[0]
    average_loading = round(df_loading['QTY'].sum() / len(df_sales_summary), 0)

    # df_received = values2[1]
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

    # --------------------- CREATE SUB HEADERS ------------------------------------------------------------------------
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
            # st.markdown(
            #  f'<p style="border:1px solid #CFCFCF; padding:10px; border-radius:8px; font-family: Arial Bold; color: {color[i]}; '
            #  f'text-align:center; font-size: {font} ;border-radius:2%; '
            #  f'line-height:0em; margin-top:-15px"> {txt[i]} </p>', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div style="
                    display:inline-block;
                    border:1px solid #CFCFCF;
                    padding:2px 6px;
                    border-radius:12px;
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

    # ==================== DISPLAY SALES, SHIPMENT, RECEIVED FIGURES =====================================================
    col1, col2 = st.columns([3, 0.15])
    with col1:

        fig.update_layout(legend=dict(title_font_family="Book Antiqua", font=dict(size=13), x=0.1, y=0.9))
        fig.update_layout(width=340, height=410, margin=dict(l=0, r=0, b=0, t=0))

        st.plotly_chart(fig, width='stretch')

    # ====================== DISPLAY INVENTORY, IN-OCEAN & WEEKLY ARRIVAL =======================================================================
    # col_m, col_n, col_o, col_p = st.columns([1, 0.7, 1, 0.1])
    col3, col4, col5, col6 = st.columns([1, 0.7, 1, 0.1])
    with col3:
        txt = 'Warehouse Inventory Mix'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        sfd.inventory_dashboard(datafile_location, forecast_month, supplier, model)

    with col4:
        txt = 'In-ocean & Received Quantity'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        values = container_loading_graph(datafile_location, supplier, model)
        df_ocean = values[0]

        # st.write(df_ocean)
        # utils.download_csv(df_ocean, 'df_ocean')

        df_received = values[1]

    with col5:

        fig, fig1 = weekly_container_arrival_chart(datafile_location, supplier, model)

        txt = 'Weekly Container Arrival'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:5px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig, width='stretch')

    utils.show_header(supplier)

    col7, col8, col9, col10 = st.columns([1, 0.7, 1, 0.1])

    with col7:
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

    with col7:
        txt = 'Inventory < 1 Month Forecast | Total SKU: ' + str(len(df_low))
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:25px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig, width='stretch')

        utils.download_csv(df_low, 'Download Low')

    with col8:
        txt = 'Container Arrival Schedule'
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
                f' line-height:0em; margin-top:25px"> {txt} </p>', unsafe_allow_html=True)

        st.plotly_chart(fig1, width='stretch')


    with col9:
        txt = 'Weekly Inventory Projection'
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(306)}; text-align:left; font-size: 18px ;border-radius:1%;'
            f' line-height:0em; margin-top:25px"> {txt} </p>', unsafe_allow_html=True)

        inventory_level_projection_graph(datafile_location, supplier, model)



    # ==================== DISPLAY DOWNLOAD LINKS =====================================================
    col_w, col_x, col_y, col_z = st.columns([1, 1, 1, 1])
    with col_w:
        utils.download_csv(df_sales_sku, 'Download Sales')
        utils.download_csv(df_ocean, 'Download Container In-Ocean')

    with col_x:
        utils.download_csv(df_sink_sku, 'Download Forecast')
        utils.download_csv(df_received, 'Download Container Received')

    with col_y:
        utils.download_csv(df_loading, 'Download Shipment')

    with col_z:
        utils.download_csv(df_received, 'Download Received')

    # end = time.perf_counter()  # stop runtime counter
    # st.sidebar.write(f"Runtime: {end - start:.2f} seconds")  # show runtime seconds

    return

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

def _container_loading_prep(df_raw, df_product, supplier, model, exclude_prefixes):
    df = pd.merge(df_raw, df_product, on=["SKU"], how="left")[
        ["PO", "SKU", "SUPPLIER", "LOADING DATE", "QTY"]
    ]

    df = utils.exclude_sku_prefixes(df, exclude_prefixes)

    df = utils.supplier_model_query(df, supplier, model)
    df["LOADING DATE"] = pd.to_datetime(df["LOADING DATE"]).dt.to_period("M")
    return df

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
        'ALL': 50000,
        'Aquacubic': 2500,
        'Bomeijia': 600,
        'Carysil': 150,
        'Changie': 300,
        'Elleci': 5000,
        'Galassia': 500,
        'Nicos': 250,
        'Plados': 300,
        'Speed': 30000,
        'Speed Vietnam': 9000,
        'Stile Libero': 1250,
        'UAE Fireclay': 250,
        'Wisdom': 70,
        'Xindeli': 2000,
        'Yalos': 100,
        'Huayi': 1000,
        'CAE Sanitary': 400
    }

    h_line = supplier_limits.get(supplier, 0)

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP')     # accessories, boxes, dummy faucets, faucet parts

    df_inventory = data.inventory_df(datafile_location)[['SKU', 'SUPPLIER', 'Existing Qty']]
    df_inventory = utils.supplier_model_query(df_inventory, supplier, model)

    df_inventory = utils.exclude_sku_prefixes(df_inventory, prefixes)

    total_inventory = df_inventory['Existing Qty'].sum()


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
    fig.update_layout(height=360, margin=dict(l=0, r=0, b=0, t=0))
    st.plotly_chart(fig, width='stretch')
    # st.write(df_sum)

    return fig


def inventory_level_projection_table_OLD(datafile_location, current_month, current_year, forecast_month, supplier, model):
    values = data.inventory_level_projection_df(datafile_location, current_month, current_year, forecast_month, supplier, model)
    df = values[0]

    avg_sales_per_week = values[1]
    wh_inventory = values[2]
    current_month_sales = values[3]

    df = df[['WEEK', 'PROJECTION']]
    df = df.rename(columns={'WEEK': 'DATE'})
    df['DATE'] = df.apply(lambda x: str(x.iloc[0])[7:13], axis=1)

    now = datetime.now()
    current_date = str(now)[5:7] + '/' + str(now)[8:10]

    df1 = pd.DataFrame({'DATE': [current_date], 'PROJECTION': [wh_inventory]})

    df = pd.concat([df1, df])

    fig2 = inventory_level_projection_graph(df, supplier, avg_sales_per_week, current_month_sales)

    return fig2, df


def test():
    import streamlit as st
    import pandas as pd
    import plotly.express as px

    st.set_page_config(page_title="SKU Forecast Dashboard", layout="wide")

    # ---------------------------------------------------------
    # Example forecast tables (replace with your real tables)
    # ---------------------------------------------------------
    df1 = pd.DataFrame({
        "SKU": ["A", "B"],
        "Jan": [100, None],
        "Feb": [120, None],
        "Mar": [140, 90],
        "Apr": [160, None],
        "May": [180, None],
        "Jun": [None, None],
        "Jul": [None, None],
        "Aug": [None, None],
        "Sep": [None, None],
        "Oct": [None, None],
        "Nov": [None, None],
        "Dec": [None, None],
    })

    df2 = pd.DataFrame({
        "SKU": ["C"],
        "Jan": [None],
        "Feb": [None],
        "Mar": [None],
        "Apr": [None],
        "May": [None],
        "Jun": [None],
        "Jul": [None],
        "Aug": [None],
        "Sep": [None],
        "Oct": [None],
        "Nov": [110],
        "Dec": [130],
    })

    df3 = pd.DataFrame({
        "SKU": ["A"],
        "Jan": [None],
        "Feb": [None],
        "Mar": [None],
        "Apr": [None],
        "May": [200],
        "Jun": [210],
        "Jul": [220],
        "Aug": [230],
        "Sep": [240],
        "Oct": [250],
        "Nov": [260],
        "Dec": [270],
    })

    # ---------------------------------------------------------
    # Combine all forecast tables
    # ---------------------------------------------------------
    def melt_forecast(df):
        return df.melt(id_vars="SKU", var_name="Month", value_name="Forecast")

    combined_long = pd.concat([
        melt_forecast(df1),
        melt_forecast(df2),
        melt_forecast(df3)
    ], ignore_index=True)

    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    master = combined_long.pivot_table(
        index="SKU",
        columns="Month",
        values="Forecast",
        aggfunc="first"
    ).reindex(columns=month_order).fillna(0)

    # ---------------------------------------------------------
    # Sidebar filters
    # ---------------------------------------------------------
    st.sidebar.header("Filters")

    sku_list = ["ALL SKUs"] + sorted(master.index.tolist())
    selected_sku = st.sidebar.selectbox("Select SKU", sku_list)

    start_month = st.sidebar.selectbox("Start Month", month_order)
    end_month = st.sidebar.selectbox("End Month", month_order)

    start_idx = month_order.index(start_month)
    end_idx = month_order.index(end_month)

    # ---------------------------------------------------------
    # Filter data
    # ---------------------------------------------------------
    if selected_sku == "ALL SKUs":
        filtered = master.loc[:, month_order[start_idx:end_idx + 1]].sum()
    else:
        filtered = master.loc[selected_sku, month_order[start_idx:end_idx + 1]]

    # ---------------------------------------------------------
    # Dashboard
    # ---------------------------------------------------------
    title_label = "All SKUs Combined" if selected_sku == "ALL SKUs" else f"SKU: {selected_sku}"
    st.title("SKU Forecast Dashboard")
    st.subheader(f"{title_label} | Months: {start_month}–{end_month}")

    # Metrics
    total_forecast = filtered.sum()
    avg_forecast = filtered.mean()

    col1, col2 = st.columns(2)
    col1.metric("Total Forecast", f"{total_forecast:,.0f}")
    col2.metric("Average Forecast", f"{avg_forecast:,.0f}")

    # Chart
    fig = px.line(
        x=filtered.index,
        y=filtered.values,
        markers=True,
        title=f"Forecast Trend ({title_label})"
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Forecast")
    st.plotly_chart(fig, use_container_width=True)

    # Table
    st.subheader("Filtered Forecast Data")
    st.dataframe(filtered)
    return
