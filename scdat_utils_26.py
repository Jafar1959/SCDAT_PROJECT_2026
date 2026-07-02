import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder

import datetime
from datetime import datetime, date
import base64

from functools import lru_cache
from pathlib import Path
import re
from calendar import month_abbr
from calendar import month_name
from calendar import monthrange

@lru_cache(maxsize=1)
def _load_color_map():
    file_path = Path(__file__).resolve().parent /"scdat_color_chart.xlsx"

    return (
        pd.read_excel(
            file_path,
            sheet_name="Color",
            usecols=["Color", "Color HEX"]
        )
        .set_index("Color")["Color HEX"]
        .to_dict()
    )


def color_hex(color_no):
    return _load_color_map().get(color_no)


def get_todays_date():
    return datetime.today().strftime("%a, %B %d, %Y")


def get_month_elapsed():
    now = datetime.now()
    return (now.month - 1) + (now.day / monthrange(now.year, now.month)[1])


def get_month_no(month):
    return datetime.strptime(
        month.strip(),
        "%B" if len(month.strip()) > 3 else "%b"
    ).month


def format_sku(sku):
    return re.split(r"[-_]", str(sku), maxsplit=1)[0]


def format_num(x):
    num = str(int(float(x)))
    return f"{int(num):,}" if len(num) >= 4 else num


def download_csv(df, text, filename="Jafar_Data.csv"):
    csv_data = df.to_csv(index=False).encode()
    b64 = base64.b64encode(csv_data).decode()

    st.markdown(
        f'<a href="data:file/csv;base64,{b64}" download="{filename}">'
        f'{text} (.csv)</a>',
        unsafe_allow_html=True
    )


def make_grid(cols, rows):
    return [st.columns(rows) for _ in range(cols)]

def exclude_sku_prefixes(df, prefixes):
    df = df[~df["SKU"].str.startswith(prefixes, na=False)]
    return df


def show_header(txt, top_margin = "-45px"):

    st.markdown(f"""
                    <div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:{top_margin};">
                        {txt}
                    </div>
                    <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:5px;">
                    """, unsafe_allow_html=True)
    return


def supplier_model_query(df, supplier, model):
    # st.write(supplier)
    # st.write(df)
    model = model.upper()

    if model != 'ALL':
        # search model or color
        df = df.loc[
            lambda row: row['SKU'].str.startswith(model.upper()) |
                        row['SKU'].str.endswith(model.upper())
        ]


    if supplier != 'ALL':
        df = df[df['SUPPLIER'] == supplier]
    return df


def get_short_month_name(month):
    return month_abbr[month]


def get_long_month_name(month):
    return month_name[month]


def month_circular_array(start_month, total_month):
    start = start_month - 1
    return [(start + i) % 12 + 1 for i in range(total_month)]

# _______________ Function not Optimized (OLD) __________________________________
def get_month_and_year_OLD(forecast_month):
    month = ''
    year = ''

    month = get_long_month_name(int(forecast_month[0:2]))
    year = forecast_month[-4:]

    return month, year

def get_month_elapsed_OLD():
    now = datetime.now()

    # Days in current month
    today = datetime.today()
    days_in_month = monthrange(today.year, today.month)[1]

    # Fractional month progress
    fraction = now.day / days_in_month

    # Total months elapsed as float
    months_elapsed = now.month - 1 + fraction

    return months_elapsed

def get_month_no_OLD(month):
    month_name = month

    if len(month_name) > 3:
        datetime_object = datetime.strptime(month_name, "%B")
    else:
        datetime_object = datetime.strptime(month_name, "%b")

    month_no = datetime_object.month

    return month_no

def get_forecast_month_OLD(month, year):
    month_no = get_month_no(month)
    month_no = ('0' + str(month_no))[-2:]
    forecast_month = month_no + '_' + month[0:3] + '-' + year
    return forecast_month

def format_sku_OLD(sku):
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

def format_num_OLD(x):
    n = str(x).split('.')
    num = n[0]
    if len(num) < 4:
        num = num
    elif len(num) < 7:
        num = num[0: len(num)-3] + ',' + num[-3:]

    return num

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

def download_csv_OLD(df, text):
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

def format_sku_2_OLD(sku):
    #st.write(sku)
    sku = str(sku)
    sku = sku[1:len(sku)]

    # find dash '['
    location = sku.find(']')
    if location > 0:
        sku = sku[0:location]
    return sku

def get_short_month_name_OLD(month):
    month = date(1900, month, 1).strftime('%b')
    return month

def get_long_month_name_OLD(month):
    month = datetime.date(1900, month, 1).strftime('%B')
    return month

def make_grid_OLD(cols, rows):
    # function to make any grid
    grid = [0]*cols
    for i in range(cols):
        with st.container():
            grid[i] = st.columns(rows)
    return grid

def month_circular_array_OLD(start_month, total_month):
    assert start_month > 0
    assert start_month < 13

    months = [0] * total_month
    start_month -= 1

    for i in range(total_month):
        months[i] = (start_month % 12) + 1
        start_month += 1

    return months


