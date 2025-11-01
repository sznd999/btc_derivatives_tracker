import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BTC Derivatives Real-Time Tracker", layout="wide")
st.title("BTC Derivatives Real-Time Tracker")

# Auto-refresh every 30 seconds
st_autorefresh(interval=30000, key="datarefresh")

def get_global_long_short():
    url = "https://fapi.binance.com/futures/data/globalLongShortAccountRatio"
    params = {"symbol": "BTCUSDT", "period": "5m", "limit": 1}
    try:
        data = requests.get(url, params=params).json()
        return data[0] if data else None
    except Exception:
        return None

def get_open_interest():
    url = "https://fapi.binance.com/futures/data/openInterestHist"
    params = {"symbol": "BTCUSDT", "period": "5m", "limit": 24}
    try:
        data = requests.get(url, params=params).json()
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception:
        return pd.DataFrame()

def get_liquidations():
    url = "https://fapi.binance.com/futures/data/liquidationOrders"
    params = {"symbol": "BTCUSDT", "limit": 20}
    try:
        data = requests.get(url, params=params).json()
        df = pd.DataFrame(data)
        return df
    except Exception:
        return pd.DataFrame()

# Fetch data
longshort = get_global_long_short()
oi_df = get_open_interest()
liq_df = get_liquidations()

col1, col2, col3 = st.columns(3)
if longshort:
    col1.metric("Long Account Ratio", float(longshort['longAccountRatio']))
    col2.metric("Short Account Ratio", float(longshort['shortAccountRatio']))
    ts = datetime.fromtimestamp(longshort['timestamp'] / 1000.0)
    col3.metric("Timestamp", ts.strftime('%Y-%m-%d %H:%M:%S'))

st.subheader("Open Interest History")
if not oi_df.empty:
    # Use sumOpenInterestValue if available, convert to float
    if 'sumOpenInterestValue' in oi_df.columns:
        st.line_chart(oi_df.set_index('timestamp')['sumOpenInterestValue'].astype(float))
    else:
        st.dataframe(oi_df)

st.subheader("Recent Liquidations")
if not liq_df.empty:
    st.dataframe(liq_df)

st.write("Last updated:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
