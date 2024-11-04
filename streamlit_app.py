import streamlit as st
import datetime as dt
import pandas as pd
import pandas_ta as ta
import numpy as np
import time
import yaml
import altair as alt
import requests

# Load YAML configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

today = dt.datetime.now()
starttime = round(time.mktime((today.year, today.month, today.day, 9, 0, 0, 0, 0, 0)))
endtime = round(time.time()) + 60
buy_period = 19
sell_period = 4
b_shield = 0.00
s_shield = 0.00

def get_intraday_data(stock_name, interval):

    header = config['headers']['vietstock']['header_0']
    url = config['urls']['vietstock']['history'] + stock_name + '&resolution=' + interval + '&from=' + str(starttime) + '&to=' + str(endtime)        
    response = requests.get(url, headers = header)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df['time'] = df['t'].apply(lambda x: dt.datetime.fromtimestamp(x).strftime('%H:%M'))
        df['average'] = df[['h', 'l', 'o', 'c']].mean(axis=1)
        df['HullMA_Short'] = round(ta.hma(df['average'], length=buy_period), 1)
        df['HullMA_Long'] = round(ta.hma(df['average'], length=sell_period), 1)
        df['average'] = round(df['average'], 1)

        conditions = [
            ((df['average'] - b_shield) > df['HullMA_Short']) & ((df['average'] - b_shield) > df['HullMA_Long']),  # Buy
            ((df['average'] + s_shield) < df['HullMA_Long'])  # Sell
        ]
        choices = [1, -1] # Define choices corresponding to the conditions: 1 for buy, -1 for sell
        df['Signal'] = np.select(conditions, choices, default=0)

        return df
    else:
        print("error request")
    return df

# Set page configuration
st.set_page_config(page_title="Intraday Stock Price Tracker", layout="wide")

# Function to fetch data for a specific stock symbol
#@st.cache_data(ttl=60)  # Cache the data for 60 seconds

# Function to render chart
#def render_chart(data):
#    st.line_chart(data[['t', 'c']].set_index('t'))

# JavaScript code to auto-refresh the specific component every 60 seconds

# Display stock data
st.title("Intraday Stock Price Tracker for AAPL")
st.write("Auto-refreshing every 60 seconds")

# Placeholder for the chart
#chart_placeholder = st.empty()

# Load data and render the chart initially
data = get_intraday_data('VN30F1M', '1')
st.write(data)
#with chart_placeholder:
#    render_chart(data)

# Inject the JavaScript for auto-refresh
#st.components.v1.html(auto_refresh_code)
