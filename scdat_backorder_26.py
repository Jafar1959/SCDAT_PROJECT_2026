import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode
import pandas as pd

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_colors_26 import color_hex
def backorder_analysis(datafile_location):
    # create header line
    st.markdown("""
    <div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-30px;">
        Backorders
    </div>
    <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
    """, unsafe_allow_html=True)

    df_backorder = data.backorder_df(datafile_location)     # get backorder data

    df_inventory = data.inventory_df(datafile_location)     # get inventory data
    df_inventory = df_inventory[['SKU', 'Existing Qty']]

    # copy inventory value from df_inventory to df_backorder
    inventory_map = df_inventory.set_index('SKU')['Existing Qty']
    df_backorder['Existing Qty'] = df_backorder['SKU'].map(inventory_map)
    df_backorder = df_backorder.fillna(0)

    # st.write(df_backorder)
    # st.write(df_inventory)

    # create a unique list of backorder 'Source Document' number
    source_doc_list = df_backorder['Source Document'].to_list()
    unique_doc_list = list(set(source_doc_list))
    unique_doc_list.sort()

    # find availability of inventory for all SKU for a particular 'Source Document' -> True (no inventory for all sku), False (inventory available)
    my_dict = {}
    for d in unique_doc_list:
        df_temp = df_backorder[df_backorder['Source Document'] == d]
        has_zero = (df_temp['Existing Qty'] == 0).any() or (df_temp['Existing Qty'] == 1).any()
        my_dict[d] = has_zero

    # add boolean data True or False to a new column
    df_backorder['Not Closable'] = df_backorder['Source Document'].map(my_dict)

    # filter closable backorder (not True)
    df_closable = df_backorder[ ~ df_backorder['Not Closable'] ]

    # st.write(df_backorder)
    # st.write(df_closable)

    # create a unique list of backorder 'Source Document' number
    source_doc_closable = df_closable['Source Document'].to_list()
    unique_doc_closable = list(set(source_doc_closable))

    total_closable_backorder = len(unique_doc_closable)
    total_backorder_qty = df_closable['Quantity'].sum()

    df_closable = df_closable.drop('Not Closable', axis=1)

    df_closable['Scheduled Date'] = pd.to_datetime(df_closable['Scheduled Date'])
    df_closable['Scheduled Date'] = df_closable['Scheduled Date'].dt.strftime('%Y-%m-%d')  # convert str to date format

    col1, col2, col3, col4 = st.columns([3, 0.6, 1, 0.1])
    with col1:
        txt = 'Closable Backorder List | Backorder: ' + str(total_closable_backorder) + \
              ' | Qty: ' + str(total_backorder_qty) + ' | ' + utils.get_todays_date()
        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(146)}; text-align:left; font-size: 18px ;border-radius:2%; line-height:0em;'
            f' margin-top:-10px">{txt}</p>', unsafe_allow_html=True)

        # Build grid options
        gb = GridOptionsBuilder.from_dataframe(df_closable)

        # Set column widths
        gb.configure_column("Source Document", width=200, cellStyle={"textAlign": "left"})
        gb.configure_column("Scheduled Date", width=200)
        gb.configure_column("SKU", width=150)
        gb.configure_column("Quantity", width=150, cellStyle={"textAlign": "center"}),
        gb.configure_column("Dealer", width=380)
        gb.configure_column("Existing Qty", width=150)

        gridOptions = gb.build()

        # set header color and alignment
        custom_css = {
            ".ag-theme-streamlit.ag-header": {
                "background-color": "#8B0A50"  # header color
                          },
            ".ag-header-cell-label": {
                "color": "#008B8B",
                "justify-content": ["left", "left", "left", "left"],
                                     }
                    }

        AgGrid(df_closable, gridOptions=gridOptions, custom_css=custom_css, height=650, fit_columns_on_grid_load=True)

        utils.download_csv(df_closable, 'Download Closable Backorders')

    with col2:

        month_wise_backorder(df_backorder)

    with col3:

        dealer_wise_backorder(df_backorder)

    return


def month_wise_backorder(df):
    df1 = df.copy()

    df1['Scheduled Date'] = pd.to_datetime(df1['Scheduled Date'])

    df2 = df1.drop_duplicates(subset=['Source Document'], keep='first')     # remove duplicate 'Source Document' numbers

    df2['Scheduled Date'] = df2['Scheduled Date'].dt.to_period('M')      # remove date from 'Scheduled Date'

    df2 = df2.groupby('Scheduled Date')['Source Document'].count().to_frame().reset_index()

    df2['Scheduled Date'] = df2['Scheduled Date'].astype(str)

    df2 = df2.rename(columns={'Source Document': 'Backorder', 'Scheduled Date': 'Month'})


    txt = 'Month-wise | Total: ' + str(df2['Backorder'].sum())

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(146)}; text-align:center; font-size: 16px ;border-radius:2%; line-height:0em;'
        f' margin-top:-10px">{txt}</p>', unsafe_allow_html=True)

    # Build grid options
    gb = GridOptionsBuilder.from_dataframe(df2)

    # Set column widths
    gb.configure_column("Month", width=150)
    gb.configure_column("Backorder", width=180)

    gridOptions = gb.build()

    # set header color and alignment
    custom_css = {
        ".ag-theme-streamlit.ag-header": {
            "background-color": "#8B0A50"  # header color
        },
        ".ag-header-cell-label": {
            "color": "#008B8B",
            "justify-content": ["left", "center"]
        }
    }
    AgGrid(df2, gridOptions=gridOptions, custom_css=custom_css, height=650, fit_columns_on_grid_load=True)
    utils.download_csv(df2, 'Download')

    return


def dealer_wise_backorder(df):

    df1 = df.copy()
    df2 = df1.drop_duplicates(subset=['Source Document'], keep='first')  # remove duplicate 'Source Document' numbers
    df2 = df2.groupby('Dealer')['Source Document'].count().to_frame().reset_index()

    df2 = df2.rename(columns={'Source Document': 'Backorder'})

    txt = 'Dealer-wise | Total: ' + str(df2['Backorder'].sum())

    st.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(146)}; text-align:center; font-size: 16px ;border-radius:2%; line-height:0em;'
        f' margin-top:-10px">{txt}</p>', unsafe_allow_html=True)

    # Build grid options
    gb = GridOptionsBuilder.from_dataframe(df2)

    # Set column widths
    gb.configure_column("Dealer", width=150)
    gb.configure_column("Backorder", width=65)

    gridOptions = gb.build()

    # set header color and alignment
    custom_css = {
        ".ag-theme-streamlit.ag-header": {
            "background-color": "#8B0A50"  # header color
        },
        ".ag-header-cell-label": {
            "color": "#008B8B",
            "justify-content": ["center", "left"]
        }
    }

    AgGrid(df2, gridOptions=gridOptions, custom_css=custom_css, height=650, fit_columns_on_grid_load=True)
    utils.download_csv(df2, 'Download')

    return