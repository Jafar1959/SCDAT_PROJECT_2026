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

# ============= my variables =========================
CURRENT_MONTH = 'Nov'
CURRENT_YEAR = '2025'
FORECAST_MONTH = '11_Nov-2025'
SUPPLIERS = ['ALL',
            'Aquacubic',
            'CAE Sanitary',
            'Elleci',
            'Huayi',
            'Nicos',
            'Plados',
            'Speed',
            'Speed Vietnam',
            'Stile Libero',
            'Xindeli',
            ]

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
                footer {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # condense the layout << ============================================
    reduce_header_height_style = """
            <style>
                div.block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 0rem;
                }
            </style>
        """

    st.markdown(reduce_header_height_style, unsafe_allow_html=True)

    # reduce_header_height_style = """
    #     <style>
    #         div.block-container {padding-top:0rem;}
    #         div.block-container {padding-bottom:0rem;}
    #         div.block-container {padding-left:1rem;}
    #         div.block-container {padding-right:0rem;}
    #     </style>
    # """
    # st.markdown(reduce_header_height_style, unsafe_allow_html=True)

    # fixed side bar size, color ============================================
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

def dashboard_container_loading(datafile_location):
    start = time.perf_counter()     # start runtime counter

    st.markdown("""
                <div style="font-size:24px; color: #DAA520; font-family: Book Antiqua; font-weight:bold; margin-bottom:0px; margin-top:-30px;">
                    Container Loading
                </div>
                <hr style="border: 1px groove #EEB422;  width: 97.5%; margin-top:0px; margin-bottom:35px;">
                """, unsafe_allow_html=True)

    with st.spinner('Loading...'):  # show spinner

        col1, col2, col3 = st.columns([4.1, 0.8, 0.1])

        with col2:  # display monthly container loading =================================
            values = fg.monthly_container_loading(datafile_location)
            fig1 = values[0]    # YTD Container Loading
            container_this_year = values[1]     # YTD Total Containers Loaded

            # st.write(utils.get_month_elapsed())
            # st.stop()

            container_per_month = round(container_this_year/utils.get_month_elapsed(), 1)   # Average Containers per Month

            txt = str(datetime.today().year) + ' | YTD Container Loading'
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(238)}; text-align:left; font-size: 18px ;border-radius:1%;'
                f' line-height:0em; margin-top:-5px"> {txt} </p>',
                unsafe_allow_html=True)
            st.plotly_chart(fig1, width='stretch')
            st.write('Months Elapsed = ' + str(round(utils.get_month_elapsed(), 2)))

        with col1:      # display container loading and receiving status for 5-months =======================================
            txt = 'Incoming Container Details | YTD Total Containers: ' + str(container_this_year) + ' (' +str(container_per_month) + '/month) ' +\
                  ' | ' + utils.get_todays_date()
            st.markdown(
                f'<p style="font-family: Book Antiqua; color: {color_hex(118)}; text-align:left; font-size: 20px ;border-radius:1%;'
                f' line-height:0em; margin-top:-5px">{txt}</p>', unsafe_allow_html=True)

            fig = fg.container_dashboard(datafile_location)
            st.plotly_chart(fig, width='stretch')

        end = time.perf_counter()   # stop runtime counter
        st.sidebar.write(f"Runtime: {end - start:.2f} seconds")     # show runtime seconds

    return

def display_choices():
    if choice == 'Select Choice':
        opening_dashboard(DATAFILE_LOCATION)

    elif choice == 'Cargo Control Dashboard':
        menu0_1 = ["Select Choice",
                   # "ETA Change",
                   # "PO & BOL Matching",
                   # "Received Containers",
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
                   'Sales Forecast',
                   'Sales Trend',
                   'Backorder List',

                  ]
        choice2 = st.sidebar.selectbox("CHOICE", menu0_2)

        display_choice2(choice2)
    return

def display_choice1(choice1):
    if choice1 == "Select Choice":
        dashboard_container_loading(DATAFILE_LOCATION)

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

    # elif choice1 == "Sales Forecast":
    #     sf.display_sales_forecast(DATAFILE_LOCATION)

    elif choice1 == "Sales Trend":
        fg.sales_trend_graph(DATAFILE_LOCATION, SUPPLIERS, FORECAST_MONTH)

    elif choice1 == "Backorder List":
        bk.backorder_analysis(DATAFILE_LOCATION)
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


