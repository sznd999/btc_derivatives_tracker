import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import date

# Set page config
st.set_page_config(page_title="Crypto Narrative Dashboard", layout="wide")

st.title("Crypto Narrative Dashboard")

# Define narratives and token ids (CoinGecko)
NARRATIVES = {
    "BlueChip": ["bitcoin", "ethereum"],
    "DeFi": ["uniswap", "aave"],
    "Layer2": ["arbitrum", "optimism"],
    "Stablecoin": ["tether", "usd-coin"],
    "Memecoin": ["dogecoin", "pepe"]
}

def fetch_prices(token_id, days=730):
    url = f"https://api.coingecko.com/api/v3/coins/{token_id}/market_chart"
    params = {"vs_currency": "usd", "days": days}
    try:
        r = requests.get(url, params=params)
        data = r.json().get("prices", [])
        df = pd.DataFrame(data, columns=["timestamp", "price"])
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms").dt.date
        df = df.drop(columns=["timestamp"]).set_index("date").resample("1D").ffill()
        return df["price"]
    except Exception:
        return pd.Series(dtype=float)

@st.cache_data(ttl=3600)
def load_data():
    # fetch and compute cumulative returns per narrative
    price_dict = {}
    for narrative, tokens in NARRATIVES.items():
        price_series_list = []
        for token in tokens:
            series = fetch_prices(token)
            price_series_list.append(series.rename(token))
        df_tokens = pd.concat(price_series_list, axis=1)
        returns = df_tokens.pct_change().mean(axis=1) + 1
        price_dict[narrative] = returns.cumprod()
    prices = pd.DataFrame(price_dict)
    prices.dropna(inplace=True)
    return prices

with st.spinner("Loading data..."):
    prices = load_data()

# compute log returns
returns = np.log(prices / prices.shift(1)).dropna()
trading_days = 365
annual_returns = returns.mean() * trading_days
annual_vol = returns.std() * np.sqrt(trading_days)
sharpe = annual_returns / annual_vol
inv_vol = 1 / annual_vol
risk_weights = inv_vol / inv_vol.sum()

summary = pd.DataFrame({
    "Annualised Return": annual_returns,
    "Annualised Volatility": annual_vol,
    "Sharpe Ratio": sharpe,
    "Risk Parity Weight": risk_weights
})

# Display metrics
st.header("Narrative Metrics")
for narrative in summary.index:
    cols = st.columns(4)
    cols[0].metric(f"{narrative} Return", f"{summary.loc[narrative, 'Annualised Return']:.2%}")
    cols[1].metric(f"{narrative} Volatility", f"{summary.loc[narrative, 'Annualised Volatility']:.2%}")
    cols[2].metric(f"{narrative} Sharpe", f"{summary.loc[narrative, 'Sharpe Ratio']:.2f}")
    cols[3].metric(f"{narrative} Weight", f"{summary.loc[narrative, 'Risk Parity Weight']:.2%}")

st.subheader("Risk Parity Weights")
st.bar_chart(risk_weights)

st.subheader("Cumulative Returns by Narrative")
st.line_chart(prices / prices.iloc[0])

st.subheader("Summary Table")
st.dataframe(
    summary.style
    .format("{:.2%}", subset=["Annualised Return", "Annualised Volatility", "Risk Parity Weight"])
    .format("{:.2f}", subset=["Sharpe Ratio"])
)

st.write("Last updated:", date.today().strftime("%Y-%m-%d"))
