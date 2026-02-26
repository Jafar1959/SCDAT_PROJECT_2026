import streamlit as st

# import streamlit.components.v1 as components

from datetime import datetime

from pathlib import Path, PureWindowsPath    # << for Window & Mac OS path-slash '\' or '/'
from PIL import Image
import time


from scdat_colors_26 import color_hex
import scdat_utils_26 as utils
import scdat_figures_26 as fg
import scdat_data_26 as data
import scdat_backorder_26 as bk
import scdat_sales_forecast_26 as sf
import scdat_cargo_control_dashboard as cc
import scdat_sales_forecast_dashboard_26 as sfd
import scdat_inventory_count_26 as inv_count
import scdat_product_chit_26 as chit



# ============= my variables =========================
CURRENT_MONTH = 'Jan'
CURRENT_YEAR = '2026'
FORECAST_MONTH = '01_Jan-2026'
SUPPLIERS = ['ALL',
            'Aquacubic',
            'Bomeijia',
            'CAE Sanitary',
            'Carysil',
            'Changie',
            'Elleci',
            'Galassia',
            'Huayi',
            'Nicos',
            'Plados',
            'Speed',
            'Speed Vietnam',
            'Stile Libero',
            'UAE Fireclay',
            'Wisdom',
            'Xindeli',
            'Yalos',
            ]
SUPPLIERS.sort()

def configure_my_streamlit_page(logo):
    # define menu elements
    my_menu = {'Get Help': 'https://docs.streamlit.io/library/api-reference',
               'About': 'Supply Chain Data Analytic Tool: Developed by Jafar Sadique'
               }

    # set tab name
    st.set_page_config(page_title="SCDAT", page_icon=logo, layout='wide',
                       initial_sidebar_state='expanded', menu_items=my_menu)

    # Hide footer only
    hide_streamlit_style = """
                <style>
                # header {visibility: hidden;}  # it will hide Deploy and three dots 
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # condense the layout << ============================================
    reduce_header_height_style = """
            <style>
                div.block-container {
                    padding-top: 0rem !important;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 0rem;
                }
            </style>
        """
    st.markdown(reduce_header_height_style, unsafe_allow_html=True)

    # fixed sidebar size, color ============================================
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { 
                min-width: 250px;
                max-width: 250px;
            }
            
            [data-testid="stSidebar"] { 
                background-color: #68838B;  /* Background color */
                color: #FFFFFF;             /* Text color */
                padding: 0px;
            }

           [data-testid="stSidebar"] {
               border-right: 5px solid #CD9B1D; /* sidebar boarder and color */
           }
        </style>
                """, unsafe_allow_html=True)

    # markdown font style, size & color ==============================================
    st.markdown("""
            <style>
            [data-testid="stSidebar"] h1 {
                font-size: 58px;
                color:  #FFD700;
                font-weight: bold;
                font-family: 'Cooper Black';
                text-align:center;
                margin-top:-60px;
            }
            </style>
        """, unsafe_allow_html=True)

    st.sidebar.markdown("<h1>SCDAT</h1>", unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(170)}; text-align:center; font-size: 13px ;border-radius:1%;'
        f' line-height:0em; margin-top:-20px"> Supply Chain Data Analytic Tool </p>',
        unsafe_allow_html=True)

    # show current date with two lines <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-28px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; text-align:center; font-size: 16px ;border-radius:1%;'
        f' line-height:0em; margin-top:-23px"> {utils.get_todays_date()} </p>',
        unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-32px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    # show current and forecast month <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    #bottom = st.sidebar.container()
    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(16)}; text-align:center; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-25px"> < Current Configuration >', unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-22px"> Current Month - &nbsp{CURRENT_MONTH} , {CURRENT_YEAR}', unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 14px ;border-radius:1%;'
        f' line-height:0em; margin-top:-22px"> Forecast Month - &nbsp{FORECAST_MONTH}', unsafe_allow_html=True)

    st.sidebar.markdown(
        f'<p style="font-family: Book Antiqua; color: {color_hex(13)}; text-align:center; font-size: 18px ;border-radius:1%;'
        f' line-height:0em; margin-top:-30px"> {"_________________________"} </p>',
        unsafe_allow_html=True)

    # Inject custom CSS to style the selectbox text <<<<<<<<<<<<<<<<<<<<<<<<<<<
    st.markdown("""
            <style>
            /* Target the selectbox label */
            [data-testid="stWidgetLabel"] {
                color: #F8F8FF;  /* label text */
                font-weight: bold;
            }

            /* Target the dropdown options */
            div[data-baseweb="select"] > div {
                color: #104E8B;  /* color option text */
                font-size: 14px !important;
            }

            </style>
        """, unsafe_allow_html=True)

    # Inject custom CSS to style the TextInputBox <<<<<<<<<<<<<<<<<<<
    st.markdown("""
        <style>
        div[data-testid="stTextInput"] input {
            color: #8B0000;           /* Text color #1a73e8 */
            font-size: 16px;          /* Font size */
            height: 40px;             /* Box height */
            width: 300px;             /* Box width */
            # border: 3px solid #1a73e8; /* Optional: border color */
            # border-radius: 5px;       /* Optional: rounded corners */
        }
        </style>
    """, unsafe_allow_html=True)

    return

def opening_dashboard(datafile_location):
    start = time.perf_counter()     # start runtime counter

    # display image at the center of the screen
    image_path = Path(PureWindowsPath(datafile_location + "Images\\SCDAT2.png"))

    col1, col2, col3, col4 = st.columns([0.5, 2, 1.3, 0.1])

    with col2:
        st.image(str(image_path), width=750)

    # display data file status table
    with col3:
        txt =  'Data File Status | ' + utils.get_todays_date()

        st.markdown(
            f'<p style="font-family: Book Antiqua; color: {color_hex(67)}; text-align:center; font-size: 18px ;border-radius:2%; '
            f'line-height:0em; margin-top:10px"> {txt} </p>', unsafe_allow_html=True)

        fig = fg.data_file_status(datafile_location)
        # st.plotly_chart(fig, use_container_width=True)    # method deprecated <<<<<<<<<<<<<
        st.plotly_chart(fig, width='stretch')

    end = time.perf_counter()  # stop runtime counter
    st.sidebar.write(f"Runtime: {end - start:.2f} seconds")  # show runtime seconds

    return

def display_choices():
    if choice == 'Select Choice':
        opening_dashboard(DATAFILE_LOCATION)

    elif choice == 'Cargo Control Dashboard':
        menu0_1 = ["Select Choice",
                   "Received Containers",
                   "ETA Changes",
                   "PO - BOL Matching",
                   # "Tariff Summary",
                   # "Customs Payment Update",
                   # "ZAxis Import Files",
                   # "WH Layout",
                   # "MTS Rate Graph"
                    ]
        choice1 = st.sidebar.selectbox("CHOICE", menu0_1)

        display_choice1(choice1)

    elif choice == "Sales Analysis Dashboard":
        menu0_2 = ['Select Choice',
                   'Inventory',
                   'Sales Forecast',
                   'Sales Trend',
                   'Sales Anatomy',
                   'Product Chit',
                   'Backorder List',
                   'Inventory Count - Step 1',
                   'Inventory Count - Step 2',

                  ]
        choice2 = st.sidebar.selectbox("CHOICE", menu0_2)

        display_choice2(choice2)
    return

def display_choice1(choice1):
    if choice1 == "Select Choice":
        cc.dashboard_container_loading(DATAFILE_LOCATION)

    elif choice1 == "Received Containers":
        cc.dashboard_container_received(DATAFILE_LOCATION)

    elif choice1 == "ETA Changes":
        cc.dashboard_ccs_mts_eta_mismatch(DATAFILE_LOCATION)

    elif choice1 == "PO - BOL Matching":
        cc.dashboard_po_bol_matching(DATAFILE_LOCATION)

    return

def display_choice2(choice1):
    if choice1 == "Select Choice":
        # create header line
        st.markdown("""
            <div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-30px;">
                Under Construction
            </div>
            <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
            """, unsafe_allow_html=True)

        sfd.inventory_dashboard(DATAFILE_LOCATION, FORECAST_MONTH, SUPPLIERS)

    elif choice1 == "Inventory":
        sfd.inventory_distribution_pie_summary(DATAFILE_LOCATION, FORECAST_MONTH, SUPPLIERS)

    elif choice1 == "Sales Trend":
        fg.sales_trend_graph(DATAFILE_LOCATION, SUPPLIERS, FORECAST_MONTH)

    elif choice1 == "Backorder List":
        bk.backorder_analysis(DATAFILE_LOCATION)

    elif choice1 == "Sales Anatomy":
        sfd.sales_anatomy_dashboard(DATAFILE_LOCATION)

    elif choice1 == "Inventory Count - Step 1":
        inv_count.display_recount_list(DATAFILE_LOCATION)

    elif choice1 == "Inventory Count - Step 2":
        inv_count.display_recount_analysis()

    elif choice1 == 'Product Chit':
        chit.display_product_chit(DATAFILE_LOCATION)

    return
    #
    #
    #
    # elif choice == "2. Sales Forecast Dashboard":
    #     menu0_2 = ["Select Choice",
    #                "Inventory Monitoring",
    #                "One Month Sales",
    #                "Sales Report",
    #                "6-Month Inventory History",
    #                "Sales Anatomy",
    #                "Sales Forecast",
    #                "4-Month Loading Plan",
    #                'FBA Loading Plan',
    #                'Backorder List',
    #                'Recount List',
    #                'Recount Analysis',
    #                "Warehouse wise Inventory",
    #                "Shipment Modelling",
    #                "Existing & Incoming Inventory",
    #                "Received Inventory",
    #                'Box Inventory',
    #                'Box Order Qty',
    #                'Box Inventory Count Sheet',
    #                "Datafeed Products",
    #                "Flagship Models",
    #                "Annual Flagship Models",
    #                "Average Sales Trend",
    #                "Dealer Sales Report",
    #                "Dealer Sales Graph",
    #                "6-Month Sales Graph",
    #                "Maruf Data_1",
    #                "Maruf Data_2",
    #                "Balance Order Qty",
    #                "Elleci-China Accessories",
    #                "Dealer-wise SKU Sales",
    #                "Inventory Balance Sheet",
    #                "Supplier-wise Returns",
    #                "Geo Locations",
    #                "Top-Seller",
    #                "Product Chit",
    #                "Return Product Chit",
    #                "Vendor Bills",
    #                "Product Internal Transfer",
    #                #"Universal Dashboard",
    #                #"General Dashboard",
    #                #"Inventory Level Projection",
    #                #"Transfer List",
    #                #'Forecast Vs Sales',
    #
    #                # "ZEN Purchase Orders",
    #                #"Inventory Dashboard 70%",
    #                # "Loading Priority",
    #                # "Actual Loading",
    #                # "Missing Supplier"
    #                #'Negative Inventory',
    #                #'Customer Review',
    #                #'Word Cloud',
    #                #'Speed Production Plan Summary',
    #                ]
    #     choice2 = st.sidebar.selectbox("CHOICE", menu0_2)
    #     display_choice2(choice2)
    #
    # elif choice == "4. Warehouse Layout":
    #     layout.display_wh_layout(DATAFILE_LOCATION)

    # return

# ========= error handler is used to get correct google_drive_name ==================
try:
    google_drive_name = 'Google Drive'  # FOR MY MAC COMPUTER

    # all data file location in the HDD
    DATAFILE_LOCATION = google_drive_name + '\\My Drive\\STREAMLIT\\SalesForecast_DataFiles\\'

    # display logo on streamlit tab
    page_logo = Image.open(Path(PureWindowsPath(DATAFILE_LOCATION + "Images\\SCDAT_Logo.png")))


except:
    google_drive_name = 'G:'  # FOR MY WINDOWS COMPUTER

    DATAFILE_LOCATION = google_drive_name + '\\My Drive\\STREAMLIT\\SalesForecast_DataFiles\\'

    # display logo on streamlit tab
    page_logo = Image.open(Path(PureWindowsPath(DATAFILE_LOCATION + "Images\\SCDAT_Logo.png")))

configure_my_streamlit_page(page_logo)

menu0 = ['Select Choice',
         'Cargo Control Dashboard',
         'Sales Analysis Dashboard',
         'Warehouse Layout',
         ]

choice = st.sidebar.selectbox("CHOICE", menu0)

# ============= FOR TESTING ONLY ======================================
# data.monthly_container_loading(DATAFILE_LOCATION)

# =====================================================================

display_choices()


