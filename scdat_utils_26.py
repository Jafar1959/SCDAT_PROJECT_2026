import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode    #, DataReturnMode

import calendar
import datetime
from datetime import datetime, date
import base64

def get_todays_date():
    day = date.today().strftime("%A")
    month = date.today().strftime("%B")
    date1 = date.today().strftime("%d")
    year = date.today().strftime("%Y")
    date_str = day[0:3] + ', ' + month + ' ' + date1 + ', ' + year
    return date_str

def get_month_and_year(forecast_month):
    month = ''
    year = ''

    month = get_long_month_name(int(forecast_month[0:2]))
    year = forecast_month[-4:]

    return month, year

def get_month_elapsed():
    now = datetime.now()

    # Days in current month
    today = datetime.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    # Fractional month progress
    fraction = now.day / days_in_month

    # Total months elapsed as float
    months_elapsed = now.month - 1 + fraction

    return months_elapsed

def get_month_no(month):
    month_name = month

    if len(month_name) > 3:
        datetime_object = datetime.strptime(month_name, "%B")
    else:
        datetime_object = datetime.strptime(month_name, "%b")

    month_no = datetime_object.month

    return month_no

def get_forecast_month(month, year):
    month_no = get_month_no(month)
    month_no = ('0' + str(month_no))[-2:]
    forecast_month = month_no + '_' + month[0:3] + '-' + year
    return forecast_month

def format_sku(sku):
    sku = str(sku)

    # find dash '-'
    location = sku.find('-')
    if location > 0:
        sku = sku[0:location]

    # find underscore '_'
    location2 = sku.find('_')
    if location2 > 0:
        sku = sku[0:location2]

    return sku

def format_num(x):
    n = str(x).split('.')
    num = n[0]
    if len(num) < 4:
        num = num
    elif len(num) < 7:
        num = num[0: len(num)-3] + ',' + num[-3:]

    return num

def month_circular_array(start_month, total_month):
    assert start_month > 0
    assert start_month < 13

    months = [0] * total_month
    start_month -= 1

    for i in range(total_month):
        months[i] = (start_month % 12) + 1
        start_month += 1

    return months

def get_short_month_name(month):
    month = date(1900, month, 1).strftime('%b')
    return month

def get_long_month_name(month):
    month = datetime.date(1900, month, 1).strftime('%B')
    return month

def get_month_order_OLD(month, year):
    month_order = []
    year = int(year)
    month_no = get_month_no(month)
    for i in range(0, 6):
        month_order.append(month_no)
        month_order.append(year)
        month_no = month_no - 1
        if month_no == 0:
            month_no = 12
            year = year - 1

    return month_order

def download_csv(df, text):
    text = text + ' (.csv)'
    coded_data = base64.b64encode(df.to_csv(index=False).encode()).decode()
    st.markdown(
        f'<a href="data:file/csv;base64,{coded_data}" download="Jafar_Data.csv"> {text}</a>',
        unsafe_allow_html=True
    )
    return


def build_AgGrid_options_OLD(df, row_height=30, header_height=25):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(rowHeight=row_height)
    gb.configure_grid_options(headerHeight=header_height)
    gb.configure_grid_options(enableCellTextSelection=True)
    gridOptions = gb.build()

    if len(df) > 0:
        height = len(df) * row_height + header_height
    else:
        height = 80

    return gridOptions, height

def make_grid(cols, rows):
    # function to make any grid
    grid = [0]*cols
    for i in range(cols):
        with st.container():
            grid[i] = st.columns(rows)
    return grid

def format_sku_2_OLD(sku):
    #st.write(sku)
    sku = str(sku)
    sku = sku[1:len(sku)]

    # find dash '['
    location = sku.find(']')
    if location > 0:
        sku = sku[0:location]
    return sku

def supplier_model_query(df, supplier, model):
    # df['SUPPLIER'].str.upper()
    # supplier = supplier.upper()
    model = model.upper()

    if model != 'ALL':
        # search model or color
        df = df.loc[
            lambda row: row['SKU'].str.startswith(model.upper()) |
                        row['SKU'].str.endswith(model.upper())
        ]

    # st.write(df)
    if supplier != 'ALL':
        df = df[df['SUPPLIER'] == supplier]

    return df

def show_header(txt):

    st.markdown(f"""
                    <div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-45px;">
                        {txt}
                    </div>
                    <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
                    """, unsafe_allow_html=True)
    return