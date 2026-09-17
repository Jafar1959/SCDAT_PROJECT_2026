import streamlit as st
import pandas as pd
from datetime import timedelta
from st_aggrid import GridOptionsBuilder, AgGrid  # , DataReturnMode
from st_aggrid import JsCode
import html as html_lib
import gdown
from pathlib import Path

import scdat_utils_26 as utils

def display_my_attendance(datafile_location):
    file_path = datafile_location + "Attendance\My_Attendance.csv"

    df = pd.read_csv(file_path)

    # Make sure date/time columns are datetime
    df['Check In'] = pd.to_datetime(df['Check In'])
    df['Check Out'] = pd.to_datetime(df['Check Out'])

    # Extract date
    df['Date'] = df['Check In'].dt.date

    # ____________________ Add Date Selection ____________
    max_date = df['Date'].max()
    min_date = max_date - pd.Timedelta(days=15)

    start_date = st.sidebar.date_input(
        "Start Date",
        value=min_date,
        min_value=min_date,
        max_value=max_date
    )

    end_date = st.sidebar.date_input(
        "End Date",
        value=max_date,
        min_value=min_date,
        max_value=max_date
    )

    # st.write(df)

    if start_date > end_date:
        st.error("Start Date cannot be greater than End Date")
        st.stop()

    df = df[
        (df['Date'] >= start_date) &
        (df['Date'] <= end_date)
        ].copy()

    # Sort by employee and check-in time
    df = df.sort_values(['Employee', 'Check In'])

    # -------------------------------------------------------
    # Create Clock-In / Clock-Out columns
    # -------------------------------------------------------
    # Number each work session within each employee/day
    df['Session'] = df.groupby(['Employee', 'Date']).cumcount() + 1

    # Clock-In columns
    clock_in = df.pivot(
        index=['Employee', 'Date'],
        columns='Session',
        values='Check In'
    )

    # Clock-Out columns
    clock_out = df.pivot(
        index=['Employee', 'Date'],
        columns='Session',
        values='Check Out'
    )

    # Rename columns
    clock_in.columns = [f'Clock-In-{i}' for i in clock_in.columns]
    clock_out.columns = [f'Clock-Out-{i}' for i in clock_out.columns]

    # Combine
    result = pd.concat([clock_in, clock_out], axis=1)

    # -------------------------------------------------------
    # Calculate Break Time
    # -------------------------------------------------------

    result['Break Time'] = pd.Timedelta(0)

    max_sessions = df['Session'].max()

    for i in range(1, max_sessions):
        out_col = f'Clock-Out-{i}'
        in_col = f'Clock-In-{i + 1}'

        if out_col in result.columns and in_col in result.columns:
            result['Break Time'] += (
                    result[in_col] - result[out_col]
            ).fillna(pd.Timedelta(0))

    # -------------------------------------------------------
    # Calculate Worked Hours
    # -------------------------------------------------------
    result['Worked Hours'] = pd.Timedelta(0)

    for i in range(1, max_sessions + 1):
        in_col = f'Clock-In-{i}'
        out_col = f'Clock-Out-{i}'

        if in_col in result.columns and out_col in result.columns:
            result['Worked Hours'] += (
                    result[out_col] - result[in_col]
            ).fillna(pd.Timedelta(0))

    # -------------------------------------------------------
    # Format output
    # -------------------------------------------------------
    result = result.reset_index()

    result['Date'] = pd.to_datetime(result['Date']).dt.strftime('%d-%b-%y')

    # Convert timedelta to hours
    result['Break Time'] = (
            result['Break Time'].dt.total_seconds() / 3600
    ).round(2)

    result['Worked Hours'] = (
            result['Worked Hours'].dt.total_seconds() / 3600
    ).round(2)

    # Format clock times
    for col in result.columns:
        if col.startswith('Clock-In') or col.startswith('Clock-Out'):
            result[col] = pd.to_datetime(result[col]).dt.strftime('%H:%M')

    # -------------------------------------------------------
    # Reorder columns
    # -------------------------------------------------------
    clock_columns = []

    for i in range(1, max_sessions + 1):
        if f'Clock-In-{i}' in result.columns:
            clock_columns.append(f'Clock-In-{i}')
        if f'Clock-Out-{i}' in result.columns:
            clock_columns.append(f'Clock-Out-{i}')

    result = result[
        ['Date'] + clock_columns + ['Break Time', 'Worked Hours']
        ]

    result ['Day'] = pd.to_datetime(result["Date"]).dt.day_name()

    cols = result.columns.tolist()

    last_col = cols[-1]  # get last column name
    cols.remove(last_col)  # remove it from current position
    cols.insert(1, last_col)
    result = result[cols]

    # txt = 'Attendance | ' + str(start_date) + ' to ' + str(end_date)\
    #       + ' | Total Days: ' + str(result['Date'].count()) \
    #       + ' | Work Hours: ' + str(result['Worked Hours'].sum().round(2)) \
    #       + ' | Break Hours: ' + str(result['Break Time'].sum().round(2))
    #
    # utils.show_header(txt)

    col1, col2 = st.columns([3, 0.2])

    with col1:

        display_headers(result, start_date, end_date)

        # day_style = JsCode("""
        # function(params) {
        #     if (params.value === 'Monday') {
        #         return {
        #             color: 'blue',
        #         };
        #     }
        #     return {};
        # }
        # """)
        #
        # gb = GridOptionsBuilder.from_dataframe(result)
        #
        # gb.configure_column(
        #     "Day",
        #     cellStyle=day_style
        # )
        #
        # grid_options = gb.build()
        #
        # st.write('')
        # AgGrid(
        #     result,
        #     gridOptions=grid_options,
        #     allow_unsafe_jscode=True
        # )

        # test_html(result)
        display_attendance_data(result)
        st.write("")
        utils.download_csv(result, "My Attendance")

    return

def display_headers(result, start_date, end_date):
    # ---------------------------------------------------------
    # ATTENDANCE SUMMARY
    # ---------------------------------------------------------
    total_days = result['Date'].count()

    work_hours = pd.to_numeric(
        result["Worked Hours"], errors="coerce"
    ).sum()

    break_hours = pd.to_numeric(
        result["Break Time"], errors="coerce"
    ).sum()

    hr = int(work_hours)
    minutes = int((work_hours - hr) * 60)
    seconds = round((((work_hours - hr) * 60) - minutes) * 60)
    if seconds == 60:
        minutes = minutes + 1
        seconds = 0

    work_hr_min_sec = f"{hr:02d}:{minutes:02d}:{seconds:02d}"


    # ---------------------------------------------------------
    # HEADER
    # ---------------------------------------------------------
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #174A7C, #1F5D96);
            border-radius: 10px;
            padding: 10px 21px;
            margin-bottom: 16px;
            color: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        ">
            <div style="
                font-size: 27px;
                font-weight: 700;
                letter-spacing: 0.3px;
            ">
                📅 My Attendance
                <span style="margin: 0 12px; opacity: 0.8;">|</span>
                <span style="font-size: 20px; font-weight: 500;">
                    {start_date} to {end_date}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # KPI CARDS
    # ---------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #F3F9FF, #EAF4FD);
                border: 1px solid #CDE5FA;
                border-radius: 12px;
                padding: 14px 24px;
                height: 95px;
            ">
                <div style="
                    font-size: 16px;
                    color: #174A7C;
                    font-weight: 600;
                ">
                    📅 &nbsp; Total Days
                </div>
                <div style="
                    font-size: 32px;
                    font-weight: 700;
                    color: #174A7C;
                    margin-top: 4px;
                ">
                    {total_days}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #F2FBF6, #EAF8F0);
                border: 1px solid #CDEEDB;
                border-radius: 12px;
                padding: 14px 24px;
                height: 95px;
            ">
                <div style="
                    font-size: 16px;
                    color: #147A4A;
                    font-weight: 600;
                ">
                    🕐 &nbsp; Work Hours
                </div>
                <div style="
                    font-size: 32px;
                    font-weight: 700;
                    color: #14844F;
                    margin-top: 4px;
                ">
                    {work_hours:.2f}
                <span style="
                    font-size: 16px;
                    font-weight: 400;
                     margin-top: 4px;">
                    [{work_hr_min_sec}]
                </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #FFF8F0, #FFF1E4);
                border: 1px solid #FFD8B0;
                border-radius: 12px;
                padding: 14px 24px;
                height: 95px;
            ">
                <div style="
                    font-size: 16px;
                    color: #A8440A;
                    font-weight: 600;
                ">
                    ☕ &nbsp; Break Hours
                </div>
                <div style="
                    font-size: 32px;
                    font-weight: 700;
                    color: #E65C00;
                    margin-top: 4px;
                ">
                    {break_hours:.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    return

def display_attendance_data(result):

    # ---------------------------------------------------------
    # TABLE CSS
    # ---------------------------------------------------------
    st.markdown(
        """
        <style>

        /* Table container */
        .attendance-table {
            border: 1px solid #C9E1F5;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 1px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }

        /* Header */
        .attendance-header {
            background: linear-gradient(90deg, #245F96, #2E6EA8);
            color: white;
            font-weight: 700;
            padding: 13px 10px;
            font-size: 14px;
        }

        /* Rows */
        .attendance-row {
            display: grid;
            grid-template-columns:
                1.0fr
                1.1fr
                1.1fr
                1.1fr
                1.1fr
                1.1fr
                0.8fr
                0.8fr;

            align-items: center;
            min-height: 40px;
            font-size: 14px;
            color: #17212B;
            border-bottom: 1px solid #E5EDF5;
        }

        .attendance-row:nth-child(even) {
            background: #F5F9FD;
        }

        .attendance-row:nth-child(odd) {
            background: white;
        }

        .attendance-cell {
            padding: 8px 12px;
        }

        /* Day badge */
        .day-badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 18px;
            background: #E4F3FD;
            color: #1470A8;
            font-weight: 600;
            text-align: center;
            min-width: 105px;
        }

        /* Monday */
        .monday {
            background: #DCE3FF;
            color: #2445D8;
        }

        /* Break */
        .break-badge {
            display: inline-block;
            background: #FFF0DF;
            color: #B94A00;
            padding: 6px 18px;
            border-radius: 12px;
            font-weight: 700;
            text-align: center;
            min-width: 65px;
        }

        /* Worked */
        .worked-badge {
            display: inline-block;
            background: #DCEEFF;
            color: #1266A3;
            padding: 6px 18px;
            border-radius: 12px;
            font-weight: 700;
            text-align: center;
            min-width: 65px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )
    # ---------------------------------------------------------
    # BUILD HTML TABLE
    # ---------------------------------------------------------
    html = """
    <div class="attendance-table">

    <div class="attendance-row attendance-header">
        <div class="attendance-cell">📅 Date</div>
        <div class="attendance-cell">📅 Day</div>
        <div class="attendance-cell">🕐 Clock-In-1</div>
        <div class="attendance-cell">🕐 Clock-Out-1</div>
        <div class="attendance-cell">🕐 Clock-In-2</div>
        <div class="attendance-cell">🕐 Clock-Out-2</div>
        <div class="attendance-cell">🎂 Break Time</div>
        <div class="attendance-cell">🕐 Worked Hours</div>
    </div>
    """

    # ---------------------------------------------------------
    # DISPLAY TABLE HEADER ONLY
    # ---------------------------------------------------------
    st.markdown(html, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # ADD DATA ROWS
    # ---------------------------------------------------------
    result = result.fillna("-")
    table = ""
    for _, row in result.iterrows():

        #date = html_lib.escape(str(row["Date"]))
        # day = html_lib.escape(str(row["Day"]))

        # clock_in_1 = html_lib.escape(str(row["Clock-In-1"]))
        # clock_out_1 = html_lib.escape(str(row["Clock-Out-1"]))
        # Clock_in_2 = html_lib.escape(str(row["Clock-In-2"]))
        # clock_out_2 = html_lib.escape(str(row["Clock-Out-2"]))

        # break_time = pd.to_numeric(
        #     row["Break Time"],
        #     errors="coerce"
        # )

        # worked_hours = pd.to_numeric(
        #     row["Worked Hours"],
        #     errors="coerce"
        # )

        day_class = "monday" if row["Day"] == "Monday" else ""

        html1 = f"""
        <div class="attendance-row">
            <div class="attendance-cell">
                <b>{row["Date"]}</b>
            </div>
            <div class="attendance-cell">
                <span class="day-badge {day_class}">
                    {row["Day"]}
            </div>
            <div class="attendance-cell">
                {row["Clock-In-1"]}
            </div>
            <div class="attendance-cell">
                {row["Clock-Out-1"]}
            </div>
            <div class="attendance-cell">
                 {row["Clock-In-2"]}
            </div>
            <div class="attendance-cell">
                 {row["Clock-Out-2"]}
            </div>
            <div class="attendance-cell">
                {row["Break Time"]:.2f}
            </div>
            <div class="attendance-cell">
                <span class="break-badge">
                    {row["Worked Hours"]:.2f}
            </div>
        </div>
        """
        table = table + html1
    # ---------------------------------------------------------
    # CLOSE TABLE
    # ---------------------------------------------------------
    # table += """
    # </div>
    # """
    # ---------------------------------------------------------
    # DISPLAY ONCE
    # ---------------------------------------------------------
    st.markdown(table, unsafe_allow_html=True)

    return


def test_html(df):

    # Example data
    # df = pd.DataFrame({
    #     "AA": [10, 30],
    #     "BB": [20, 40],
    #     "CC": [50, 60],
    #     "DD": [70, 80]
    # })

    # Start HTML table
    html = """
    <style>
    .my-table {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        font-size: 14px;
    }

    .my-table th {
        background-color: #f2f2f2;
        color: #333;
        text-align: center;
        padding: 8px;
        border-bottom: 2px solid #ccc;
    }

    .my-table td {
        text-align: center;
        padding: 8px;
        border-bottom: 1px solid #ddd;
    }

    .my-table tr:hover {
        background-color: #f5f5f5;
    }
    </style>

    <table class="my-table">
        <thead>
            <tr>
                <th>AA</th>
                <th>BB</th>
                <th>CC</th>
                <th>DD</th>
                <th>EE</th>
            </tr>
        </thead>
        <tbody>
    """
    st.markdown(html, unsafe_allow_html=True)

    # Add rows
    table = ""
    for _, row in df.iterrows():
        html1 = f"""
            <tr>
                <td>{row["Date"]}</td>
                <td>{row["Day"]}</td>
                <td>{row["Clock-In-1"]}</td>
                <td>{row["Clock-Out-1"]}</td>
                <td>{row["Clock-In-2"]}</td>
                 <td>{row["Clock-Out-2"]}</td>
                 <td>{row["Break Time"]}</td>
                 <td>{row["Worked Hours"]}</td>
            </tr>
        """
        table = table + html1

    # Close table
    html1 += """
        </tbody>
        </table>
    """

    # Display in Streamlit
    st.markdown(table, unsafe_allow_html=True)

    return
