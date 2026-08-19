import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode, GridUpdateMode    #, DataReturnMode
from functools import reduce

import scdat_data_26 as data
import scdat_utils_26 as utils
from scdat_utils_26 import color_hex


def sidebar_text(text, size=14, align="left", margin="-3px"):
    st.sidebar.markdown(
        f"""
        <p style="
            font-family: Book Antiqua;
            color: {color_hex(13)};
            text-align: {align};
            font-size: {size}px;
            border-radius: 1%;
            line-height: 1em;
            margin-top: {margin};
        ">
            {text}
        </p>
        """,
        unsafe_allow_html=True
    )


def get_30d_incoming(datafile_location):
    now = datetime.now()
    start_date = now.date()
    end_date = start_date + timedelta(days=25)  # actually 25 days

    df, *_ = data.container_df(datafile_location)

    # df = df[df['STATE'] != 'Received In Warehouse']
    # df = df[df['ODDO_ETA'] >= start_date]
    # df = df[df['ODDO_ETA'] <= end_date]
    # df = df[['SKU', 'QTY']]
    # df = df.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    # df = df.rename(columns={'QTY': 'Incoming Qty'})

    df = (
        df.loc[
            (df['STATE'] != 'Received In Warehouse') &
            df['ODDO_ETA'].between(start_date, end_date),
            ['SKU', 'QTY']
        ]
        .groupby('SKU', as_index=False)['QTY']
        .sum()
        .rename(columns={'QTY': 'Incoming Qty'})
    )

    return df


def three_months_avg_fba_sales(datafile_location):

    month_avg = st.sidebar.number_input('MONTHS-AVERAGE SALE', value=2, step=1)

    today = datetime.today()
    previous_3_months = [
        (today - relativedelta(months=i)).strftime("%B %Y")
        for i in range(month_avg, 0, -1)
    ]

    dfs = []

    for period in previous_3_months:
        month, year = period.split()

        df_month = (
            data.one_month_sales_df(datafile_location, month, year)
            [['SKU', 'AMAZON', 'TOTAL']]
            .rename(columns={
                'AMAZON': f'AMAZON-{month}',
                'TOTAL': f'TOTAL-{month}'
            })
        )

        dfs.append(df_month)

    # Merge all dataframes on SKU
    df = reduce(lambda left, right: left.merge(right, on='SKU', how='outer'), dfs)

    # Calculate 3-month averages
    amazon_cols = [c for c in df.columns if c.startswith('AMAZON-')]
    total_cols = [c for c in df.columns if c.startswith('TOTAL-')]

    df['AMAZON SALES'] = df[amazon_cols].mean(axis=1).round(0)
    df['TOTAL SALES'] = df[total_cols].mean(axis=1).round(0)

    # st.write(df)
    # st.stop()


    # month = previous_3_months[0].split()[0]
    # year = previous_3_months[0].split()[1]
    #
    #
    # df1 = (
    #     data.one_month_sales_df(datafile_location, month, str(year))[
    #         ['SKU', 'AMAZON', 'TOTAL']
    #     ]
    #     .rename(columns={
    #         'AMAZON': 'AMAZON-' + month,
    #         'TOTAL': 'TOTAL-' + month
    #     })
    # )
    #
    # month = previous_3_months[1].split()[0]
    # year = previous_3_months[1].split()[1]
    #
    # df2 = (
    #     data.one_month_sales_df(datafile_location, month, str(year))[
    #         ['SKU', 'AMAZON', 'TOTAL']
    #     ]
    #     .rename(columns={
    #         'AMAZON': 'AMAZON-' + month,
    #         'TOTAL': 'TOTAL-' + month
    #     })
    # )
    #
    # df = pd.merge(df1, df2, on=["SKU"], how='outer')
    #
    # month = previous_3_months[2].split()[0]
    # year = previous_3_months[2].split()[1]
    #
    # df3 = (
    #     data.one_month_sales_df(datafile_location, month, str(year))[
    #         ['SKU', 'AMAZON', 'TOTAL']
    #     ]
    #     .rename(columns={
    #         'AMAZON': 'AMAZON-' + month,
    #         'TOTAL': 'TOTAL-' + month
    #     })
    # )
    #
    # df = pd.merge(df, df3, on=["SKU"], how='outer')
    #
    # cols = df.columns
    #
    # df['AMAZON SALES'] = ((df[cols[1]] + df[cols[3]] + df[cols[5]])/3).round(0)
    # df['TOTAL SALES'] = ((df[cols[2]] + df[cols[4]] + df[cols[6]])/3).round(0)
    #

    # st.write(df)
    # st.stop()



    # now = datetime.now()
    #
    # prev_date = now.replace(day=1) - timedelta(days=1)
    #
    # previous_month = prev_date.month
    # year = prev_date.year
    #
    # month = utils.get_long_month_name(previous_month)
    #
    # df = (
    #     data.one_month_sales_df(datafile_location, month, str(year))[
    #         ['SKU', 'AMAZON', 'TOTAL']
    #     ]
    #     .rename(columns={
    #         'AMAZON': 'AMAZON SALES',
    #         'TOTAL': 'TOTAL SALES'
    #     })
    # )

    # _____ Sidebar Display _________________
    # Separator
    line = "_" * 22

    sidebar_text(line, size=18, align="center", margin="-10px")

    # Title
    sidebar_text(
        f"Amazon & Total Sales:<br><br>"
        f"AVG ({previous_3_months[0]} - {previous_3_months[month_avg - 1]})",
        size=14,
        align="left",
        margin="-3px"
    )

    # Separator
    sidebar_text(line, size=18, align="center", margin="-10px")

    return df


def get_fba_loading_qty(existing_qty, incoming_qty, amazon_sales, total_fba_stock, total_sales, month_factor):

    # calculate available quantity for FBA loading =========================
    available_qty_for_fba = 0

    if 0 < total_sales <= 50:
        if (existing_qty + incoming_qty) >= 2.5 * total_sales:
            available_qty_for_fba = existing_qty - total_sales
        else:
            available_qty_for_fba = existing_qty - 2.5 * total_sales

    elif 50 < total_sales <= 150:
        if existing_qty + incoming_qty >= 2 * total_sales:
            available_qty_for_fba = existing_qty - total_sales
        else:
            available_qty_for_fba = existing_qty - 2 * total_sales

    elif 150 < total_sales <= 300:
        if existing_qty + incoming_qty >= 1.75 * total_sales:
            available_qty_for_fba = existing_qty - total_sales
        else:
            available_qty_for_fba = existing_qty - 1.75 * total_sales

    elif 300 < total_sales <= 350:
            if existing_qty + incoming_qty >= 1.5 * total_sales:
                available_qty_for_fba = existing_qty - total_sales
            else:
                available_qty_for_fba = existing_qty - 1.5 * total_sales

    elif 350 < total_sales <= 400:
        if existing_qty + incoming_qty >= 1.25 * total_sales:
            available_qty_for_fba = existing_qty - total_sales
        else:
            available_qty_for_fba = existing_qty - 1.25 * total_sales

    elif total_sales > 400:
        available_qty_for_fba = existing_qty - 500

    # set available qty to 0
    if available_qty_for_fba < 4:
        available_qty_for_fba = 0

    # calculate FBA loading qty =======================================
    if amazon_sales == 0 and total_fba_stock == 0:
        loading_qty = 4
    else:
        loading_qty = amazon_sales * month_factor - total_fba_stock

    # set max limit
    if loading_qty > available_qty_for_fba:
        loading_qty = available_qty_for_fba

    # round to multiple of 4
    if loading_qty < 0:
        loading_qty = 0

    elif 0 < loading_qty < 4:
        loading_qty = 4

    elif loading_qty >= 4:
        if loading_qty % 4 != 0:
            loading_qty = loading_qty + (4 - loading_qty % 4)

    return round(loading_qty, 0)


def get_wh_quantity(datafile_location):
    (
        df_wh,
        df_wh1,
        df_wh2,
        df_wh3,
        df_wh4,
        df_accessories,
        df_box,
        df_refurb,
        df_container,
        df_retail,
        retail_models,
        df_faucet,
        df_bathtub,
        df_faucet_parts

     ) = data.wh_wise_inventory_df(datafile_location)

    def summarize_wh(df, name):
        return (
            df[['SKU', 'QTY']]
            .groupby('SKU', as_index=False)['QTY']
            .sum()
            .rename(columns={'QTY': name})
        )

    df_wh1 = summarize_wh(df_wh1, 'WH1')
    df_wh2 = summarize_wh(df_wh2, 'WH2')
    df_wh3 = summarize_wh(df_wh3, 'WH3')
    df_wh4 = summarize_wh(df_wh4, 'WH4')
    df_acc = summarize_wh(df_accessories, 'PARTS')


    df = (
        df_wh1
        .merge(df_wh2, on='SKU', how='outer')
        .merge(df_wh3, on='SKU', how='outer')
        .merge(df_wh4, on='SKU', how='outer')
        .merge(df_acc, on='SKU', how='outer')
    )

    df = df.fillna(0)

    return df


    # # create WH wise inventory dataframe ======================================
    # # WH-1 ================
    # get_df = data.wh_wise_inventory_df_NEW(datafile_location)
    # df_wh1 = get_df[1]
    # df_wh1 = df_wh1.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    # df = pd.merge(df, df_wh1, on=["SKU"], how='left')
    # df = df.fillna(0)
    # df.columns = (['SKU', 'SUPPLIER', 'EXISTING', 'INCOMING (30d)', 'AMAZON SALES', 'FBA STOCK', 'TOTAL SALES', 'LOADING QTY', 'WH1'])
    #
    # df_wh2 = get_df[2]
    # df_wh2 = df_wh2.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    # df = pd.merge(df, df_wh2, on=["SKU"], how='left')
    # df = df.fillna(0)
    # df.columns = (['SKU', 'SUPPLIER', 'EXISTING', 'INCOMING (30d)', 'AMAZON SALES', 'FBA STOCK', 'TOTAL SALES', 'LOADING QTY', 'WH1', 'WH2'])
    #
    # # WH-3 =========================
    # df_wh3 = get_df[3]
    # df_wh3 = df_wh3.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    # df = pd.merge(df, df_wh3, on=["SKU"], how='left')
    # df = df.fillna(0)
    # df.columns = (['SKU', 'SUPPLIER', 'EXISTING', 'INCOMING (30d)', 'AMAZON SALES', 'FBA STOCK', 'TOTAL SALES', 'LOADING QTY', 'WH1', 'WH2', 'WH3'])
    #
    # # WH-4 ===========================
    # df_wh4 = get_df[4]
    # df_wh4 = df_wh4.groupby('SKU')['QTY'].sum().to_frame().reset_index()
    # df = pd.merge(df, df_wh4, on=["SKU"], how='left')
    # df = df.fillna(0)
    # df.columns = (['SKU', 'SUPPLIER', 'EXISTING', 'INCOMING (30d)', 'AMAZON SALES', 'FBA STOCK', 'TOTAL SALES', 'LOADING QTY', 'WH1', 'WH2', 'WH3',
    #                'WH4'])
    #
    # df = df.sort_values('SKU', ascending=True)
    # df.reset_index(drop=True, inplace=True)
    # df.index = range(1, df.shape[0] + 1)
    #
    # st.markdown(
    #     f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
    #     f' line-height:0em; margin-top:5px"> FBA Loading Plan based on {month} Sales</p>', unsafe_allow_html=True)
    #
    # AgGrid(df, height=650,
    #        fit_columns_on_grid_load=True,
    #        # theme='blue',  # Add theme color to the table
    #        # enable_enterprise_modules=True,
    #        # reload_data=True,
    #        # editable=True
    #        )
    #
    # ut.download_csv(df, 'Download FBA Loading Qty')
    #
    # df_sink = df.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    # total_sku_sink = df_sink['SKU'].count()
    # existing_sink = df_sink['EXISTING'].sum()
    # incoming_sink = df_sink['INCOMING (30d)'].sum()
    # amazon_sales_sink = df_sink['AMAZON SALES'].sum()
    # fba_stock_sink = df_sink['FBA STOCK'].sum()
    # total_loading_sink = df_sink['LOADING QTY'].sum()
    # total_wh1_sink = df_sink['WH1'].sum()
    # total_wh2_sink = df_sink['WH2'].sum()
    # total_wh4_sink = df_sink['WH4'].sum()
    #
    # df_acc = df.loc[lambda row: row['SKU'].str.startswith('RVA')]
    # total_sku_acc = df_acc['SKU'].count()
    # existing_acc = df_acc['EXISTING'].sum()
    # incoming_acc = df_acc['INCOMING (30d)'].sum()
    # amazon_sales_acc = df_acc['AMAZON SALES'].sum()
    # fba_stock_acc = df_acc['FBA STOCK'].sum()
    # total_loading_acc = df_acc['LOADING QTY'].sum()
    # total_wh1_acc = df_acc['WH1'].sum()
    # total_wh2_acc = df_acc['WH2'].sum()
    # total_wh4_acc = df_acc['WH4'].sum()
    #
    # df_summary = pd.DataFrame({'PRODUCT': ['SINK', 'ACCESSORIES'],
    #                        'SKU': [total_sku_sink, total_sku_acc],
    #                        'EXISTING': [existing_sink, existing_acc],
    #                        'INCOMING (30d)': [incoming_sink, incoming_acc],
    #                        'AMAZON SALES': [amazon_sales_sink, amazon_sales_acc],
    #                        'FBA STOCK': [fba_stock_sink, fba_stock_acc ],
    #                        'LOADING QTY': [total_loading_sink, total_loading_acc],
    #                        'WH1': [total_wh1_sink, total_wh1_acc],
    #                        'WH2': [total_wh2_sink, total_wh2_acc],
    #                        'WH4': [total_wh4_sink, total_wh4_acc],
    #                        })
    #
    # # st.write(df_summary)
    #
    # fig = go.Figure(data=[go.Table(
    #     columnwidth=[18],
    #
    #     header=dict(values=list(df_summary.columns),
    #                 fill_color=color_hex(118),
    #                 line_color='white',
    #                 font_color='white',
    #                 font_size=14,
    #                 height=28,
    #                 align=['left', 'center']),
    #     cells=dict(
    #         values=[df_summary.PRODUCT, df_summary.SKU, df_summary.EXISTING, df_summary['INCOMING (30d)'],
    #                 df_summary['AMAZON SALES'], df_summary['FBA STOCK'], df_summary['LOADING QTY'],
    #                 df_summary.WH1, df_summary.WH2, df_summary.WH4 ],
    #         font_size=14,
    #         height=28,
    #         fill_color=color_hex(17),
    #         line_color='white',
    #         align=['left', 'center']))
    # ])
    #
    # fig.update_layout(height=90, margin=dict(l=0, r=0, b=0, t=0))
    # st.plotly_chart(fig, use_container_width=True)
    #
    # # display non FBA SKU with sales > 4 =================================
    # df_product = data.product_df(datafile_location)
    # df_product = df_product[df_product['FBA'] != 'FBA']
    # df_product = df_product[['SKU', 'SUPPLIER', 'FBA']]
    # df_product = df_product.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    #
    # df_sales2 = df_sales[df_sales['TOTAL SALES'] > 4].copy()
    #
    # df_sales2 = pd.merge(df_product, df_sales2, on=["SKU"], how='left')
    # df_sales2 = df_sales2.loc[lambda row: ~ row['SKU'].str.startswith('RVA')]
    # df_sales2 = df_sales2[['SKU', 'SUPPLIER', 'AMAZON SALES', 'TOTAL SALES']]
    # df_sales2 = df_sales2[df_sales2['TOTAL SALES'] > 0]
    #
    # df_sales2 = df_sales2.sort_values(['TOTAL SALES', 'SKU'], ascending=[False, True])
    # df_sales2.reset_index(drop=True, inplace=True)
    # df_sales2.index = range(1, df_sales2.shape[0] + 1)
    # df_sales2 = df_sales2.fillna(0)
    #
    # st.markdown(
    #     f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 18px ;border-radius:1%;'
    #     f' line-height:0em; margin-top:10px"> Product with Total Sales > = 5</p>', unsafe_allow_html=True)
    #
    # col1, col2 = st.columns([1,2])
    # with col1:
    #     AgGrid(df_sales2, fit_columns_on_grid_load=True)
    #
    # return
    #


def fba_list(datafile_location):
    # merge FBA, WH, 30-days-incoming inventory and previous month FBA sales ___________
    df = (
        data.fba_inventory_df(datafile_location)[
            ['SKU', 'SUPPLIER', 'TOTAL FBA STOCK']
        ]
        .merge(
            data.inventory_df(datafile_location)[['SKU', 'Existing Qty']],
            on='SKU',
            how='left'
        )
        .merge(
            get_30d_incoming(datafile_location),
            on='SKU',
            how='left'
        )
        .merge(
            three_months_avg_fba_sales(datafile_location),
            on='SKU',
            how='left'
        )
    )

    df = df.fillna(0)
    # re-arrange and rename columns _______________
    df = (
        df[
            ['SKU', 'SUPPLIER', 'Existing Qty', 'Incoming Qty',
             'AMAZON SALES', 'TOTAL FBA STOCK', 'TOTAL SALES']
        ]
        .rename(columns={
            'Existing Qty': 'EXISTING',
            'Incoming Qty': 'INCOMING (30d)',
            'TOTAL FBA STOCK': 'FBA STOCK'
        })
    )

    month_factor = st.sidebar.number_input('MONTH FACTOR', value=2.0, step=0.1)

    # calculate loading qty ________________________
    df['LOADING QTY'] = df.apply(
        lambda x: get_fba_loading_qty(
            x['EXISTING'],
            x['INCOMING (30d)'],
            x['AMAZON SALES'],
            x['FBA STOCK'],
            x['TOTAL SALES'],
            month_factor
        ),
        axis=1
    )

    # add WH inventory ___________________
    df_wh = get_wh_quantity(datafile_location)

    df = df.merge(df_wh, on='SKU', how='left')

    df = df.fillna(0)

    utils.show_header('FBA LIST')

    display_fba_list(df)

    return


def sub_header_table(df):
    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[70] + [70] * (len(df.columns) - 1),
                header=dict(
                    values=[f"<b>{c}</b>" for c in df.columns],
                    fill_color="#5F9EA0",
                    font=dict(color="white", size=14),
                    align=["left"] + ["center"] * (len(df.columns) - 1),
                    line_color="black",
                    height=20
                ),
                cells=dict(
                    values=[df[c] for c in df.columns],
                    fill_color="#F0FFFF",
                    font=dict(color="black", size=14),
                    align=["left"] + ["center"] * (len(df.columns) - 1),
                    line_color="black",
                    height=25
                ),
            )
        ]
    )


    fig.update_layout(height=len(df)*25+40, margin=dict(l=0, r=0, t=0, b=0))

    return fig


def column_header_color(df, gb):
    # define columns header class ___________________________
    gb.configure_column(df.columns[0], headerClass="sku-header")
    gb.configure_column(df.columns[1], headerClass="all-header")
    gb.configure_column(df.columns[2], headerClass="all-header")
    gb.configure_column(df.columns[3], headerClass="all-header")
    gb.configure_column(df.columns[4], headerClass="all-header")
    gb.configure_column("FBA STOCK", headerClass="fba-stock-header")

    gb.configure_column(df.columns[6], headerClass="all-header")
    gb.configure_column("LOADING QTY", headerClass="loading-qty-header")

    gb.configure_column(df.columns[8], headerClass="all-header")
    gb.configure_column(df.columns[9], headerClass="all-header")
    gb.configure_column(df.columns[10], headerClass="all-header")
    gb.configure_column(df.columns[11], headerClass="all-header")
    gb.configure_column(df.columns[12], headerClass="all-header")

    # set AgGrid header font & background colors_____________
    custom_css = {
        ".sku-header": {
            "background-color": "#B2DFEE",
            "color": "black"
        },

        ".all-header": {
            "background-color": "#CFCFCF",
            "color": "black"
        },

        ".fba-stock-header": {
            "background-color": "#8FBC8F",
            "color": "black"
        },
        ".loading-qty-header": {
            "background-color": "#FFE7BA",
            "color": "black"
        },
    }

    grid_options = gb.build()

    return grid_options, custom_css


def row_color(gb):
    gb.configure_grid_options(
        getRowStyle=JsCode("""
                function(params) {
                    if (params.node.rowIndex % 2 === 0) {
                        return {
                            'backgroundColor': '#FFFFFF'
                        };
                    } else {
                        return {
                            'backgroundColor': '#E8E8E8'
                        };
                    }
                }
                 """)
    )
    return gb


def display_fba_list(df):

    cols = df.columns
    df_rva = df[df['SKU'].str.startswith('RVA', na=False)]  # accessories
    df_rvf = df[df['SKU'].str.startswith('RVF', na=False)]  # faucets
    df_tub = df[df['SKU'].str.startswith('RVB6', na=False)]  # bathtubs

    prefixes = ('RVA', 'RBX', 'RDM', 'RVP', 'RVF', 'RVB6')  # accessories, boxes, dummy faucets, faucet parts, faucet, tub
    df_sink = utils.exclude_sku_prefixes(df, prefixes)

    # create summary dataframe ___________________________
    all_txt = ['Accessories', 'Sink', 'Faucet', 'Bathtub']
    all_data = [df_rva, df_sink, df_rvf, df_tub]

    # define lists ___________
    items = []
    count = []
    # col1 = [] # SUPPLIER
    col2 = []
    col3 = []
    col4 = []
    col5 = []
    col6 = []
    col7 = []


    for i in range(0, 4):
        # get appropriate text and datafile ___________
        txt = all_txt[i]
        data = all_data[i]

        # calculate column totals ______________________
        total_sku = int(data['SKU'].count())
        #total_col1 = int(data[cols[1]].count())
        total_col2 = int(data[cols[2]].sum())
        total_col3 = int(data[cols[3]].sum())
        total_col4 = int(data[cols[4]].sum())
        total_col5 = int(data[cols[5]].sum())
        total_col6 = int(data[cols[6]].sum())
        total_col7 = int(data[cols[7]].sum())
        # total_col8 = int(data[cols[8]].sum())
        # total_col9 = int(data[cols[9]].sum())
        # total_col10 = int(data[cols[10]].sum())
        # total_col11 = int(data[cols[11]].sum())

        # append to list ____________________
        items.append(txt)
        count.append(total_sku)
        # col1.append(total_col1)
        col2.append(total_col2)
        col3.append(total_col3)
        col4.append(total_col4)
        col5.append(total_col5)
        col6.append(total_col6)
        col7.append(total_col7)

    # create summary dataframe __________________
    df_sub = pd.DataFrame({
        'ITEMS': items,
        'COUNT': count,
        # cols[1]: col1,
        cols[2]: col2,
        cols[3]: col3,
        cols[4]: col4,
        cols[5]: col5,
        cols[6]: col6,
        cols[7]: col7,
        # cols[8]: col8,
        # cols[9]: col9,
        # cols[10]: col10,
        # cols[11]: col11,

    })

    # filter and sort dataframe __________
    df_sub = (
        df_sub.loc[df_sub['COUNT'].ne(0)]
        .sort_values('ITEMS')
    )

    fig = sub_header_table(df_sub)

    gb = GridOptionsBuilder.from_dataframe(df)

    # set alternative row color _____________
    gb.configure_grid_options= row_color(gb)

    # set column header color __________
    grid_options, custom_css = column_header_color(df, gb)

    col1, col2 = st.columns([3, 0.1])

    with col1:
        # show summary ______________________
        st.plotly_chart(fig, width='stretch')

        # show details data _______________________
        height = len(df) * 35
        if height > 610:
            height = 610
        # AgGrid(df, gridOptions=gb.build(), custom_css=custom_css, height=height, allow_unsafe_jscode=True)
        AgGrid(df, gridOptions=grid_options, custom_css=custom_css, height=height, allow_unsafe_jscode=True)

    utils.download_csv(df, 'Download FBA List')

    return


