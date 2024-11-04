import streamlit as st
import datetime as dt
import pandas as pd
import pandas_ta as ta
import numpy as np
import time
import yaml
import requests
import plotly.graph_objs as go

# Load YAML configuration
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Set page configuration
st.set_page_config(page_title="Intraday Stock Price Tracker", layout="wide")

# Get intraday trading
def get_intraday_data(stock_name, interval):
    today = dt.datetime.now()
    starttime = round(time.mktime((today.year, today.month, today.day-1, 9, 0, 0, 0, 0, 0)))
    endtime = round(time.time()) + 60
    buy_period = 19
    sell_period = 4
    b_shield = 0.00
    s_shield = 0.00

    header = config['headers']['vietstock']['header_0']
    his_url = config['urls']['history']['vietstock'] + stock_name + '&resolution=' + interval + '&from=' + str(starttime) + '&to=' + str(endtime)
    last_url = config['urls']['last']['vps'] + 'VN30F2411'

    his_response = requests.get(his_url, headers = header)
    last = requests.get(last_url).json()[-1]['lastPrice']
    #last = requests.get(last_url).json()[-1]['last_price'] #hsc

    his_data = his_response.json()
    df = pd.DataFrame(his_data)
    df.loc[len(df)] = {'t': endtime,'o': last,'l': last,'h': last,'c': last,'v': 0, 's': 'ok'}
    
    df['time'] = df['t'].apply(lambda x: dt.datetime.fromtimestamp(x).strftime('%H:%M'))
    df['a'] = df[['h', 'l', 'o', 'c']].mean(axis=1)

    df['HullMA_Long'] = round(ta.hma(df['a'], length=buy_period), 1)
    df['HullMA_Short'] = round(ta.hma(df['a'], length=sell_period), 1)
    
    df['a'] = round(df['a'], 1)

    conditions = [
        ((df['a'] - b_shield) > df['HullMA_Short']) & ((df['a'] - b_shield) > df['HullMA_Long']),  # Buy
        ((df['a'] + s_shield) < df['HullMA_Short'])  # Sell
    ]
    choices = ['LONG', 'SHORT'] # Define choices corresponding to the conditions: 1 for buy, -1 for sell
    df['Signal'] = np.select(conditions, choices, default='...')

    return df

def render_chart(data):
    fig = go.Figure()
    # Close price in blue, Low price in red, High price in green
    fig.add_trace(go.Scatter(x=data['time'], y=data['a'], mode='lines', name='last', line=dict(color='blue'), 
                             customdata=data['Signal'],
                             hovertemplate='last: %{y}<br>%{customdata}<extra></extra>'))
    fig.add_trace(go.Scatter(x=data['time'], y=data['HullMA_Short'], mode='lines', name='hmas', line=dict(color='red'), hovertemplate='hmas: %{y}<extra></extra>'))
    fig.add_trace(go.Scatter(x=data['time'], y=data['HullMA_Long'], mode='lines', name='hmal', line=dict(color='green'), hovertemplate='hmal: %{y}<extra></extra>'))

    # Customize layout
    fig.update_layout(title="", 
                      xaxis_title="", 
                      yaxis_title="", 
                      template="plotly_white",
                      legend=dict(
                          orientation="h",  # Horizontal legend
                          yanchor="top",
                          y=-0.3,
                          xanchor="center",
                          x=0.5),
                      margin=dict(l=40, r=40, t=40, b=40),  # Set margins for wide mode
                      hovermode="x unified"  # Unified hover mode for better readability)
    )
    st.plotly_chart(fig, use_container_width=True)

# Placeholder for the chart
chart_placeholder = st.empty()

# Loop to refresh data and chart every 60 seconds
while True:
    current_time = dt.datetime.now().time()
    # Check if the current time is between 9:00 AM and 3:00 PM
    #if dt.time(8, 0) < current_time < dt.time(15, 0):
    data = get_intraday_data('VN30F1M', '1').tail(45)  # Fetch updated data only during market hours
    st.header(f"{data.iloc[-1]['time']}: price is {data.iloc[-1]['a']} with {data.iloc[-1]['Signal']} signal")
    with chart_placeholder:
        render_chart(data)  # Display updated chart
    
    time.sleep(60)  # Wait for 60 seconds before the next update