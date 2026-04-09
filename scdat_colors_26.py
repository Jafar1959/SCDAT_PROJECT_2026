import pandas as pd
import os

import streamlit as st

# http: // fillster.com / colorcodes / colorchart.html
 
# Get the directory of the current script
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define the file path
file_path = os.path.join(base_dir, 'scdat_color_chart.xlsx')

def color_hex(color_no)
    df = pd.read_excel(file_path, sheet_name='Color')
    df = df[['Color', 'Color Name', 'Color RGB', 'Color HEX']]
    df = df[df['Color'] == color_no]
    # hex1 = df.iloc[0][3]
    hex1 = df.iloc[0, 3]
    return hex1

def color_rgb(color_no):
#fsbjfbsdhbfdhbfdhbdfhbf
    df = pd.read_excel(file_path, sheet_name='Color')
    df = df[['Color', 'Color Name', 'Color RGB', 'Color HEX']]
    df = df[df['Color'] == color_no]
    rgb = df.iloc[0][2]
    return rgb

def color_name(color_no):
    df = pd.read_excel(file_path, sheet_name='Color')
    df = df[['Color', 'Color Name', 'Color RGB', 'Color HEX']]
    df = df[df['Color'] == color_no]
    color_name = df.iloc[0][1]
    return color_name
