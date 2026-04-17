import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

from main import fetch_prices, COINS, COIN_SYMBOLS
from validator import validate_prices

DATA_FILE = Path("data/prices.csv")
REFRESH_INTERVAL = 60  # seconds


def append_prices(prices: dict) -> None:
    DATA_FILE.parent.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        {
            "timestamp": timestamp,
            "symbol": COIN_SYMBOLS[coin],
            "price": prices[coin]["usd"],
            "change_24h": round(prices[coin]["usd_24h_change"], 2),
        }
        for coin in COINS
    ]
    df = pd.DataFrame(rows)
    df.to_csv(DATA_FILE, mode="a", header=not DATA_FILE.exists(), index=False)


def load_history() -> pd.DataFrame | None:
    if not DATA_FILE.exists():
        return None
    df = pd.read_csv(DATA_FILE, parse_dates=["timestamp"])
    return df


def render_price_card(symbol: str, price: float, change: float) -> None:
    color = "green" if change >= 0 else "red"
    sign = "+" if change >= 0 else ""
    st.markdown(
        f"""
        <div style="border:1px solid #ddd; border-radius:8px; padding:16px; text-align:center;">
            <h3 style="margin:0">{symbol}</h3>
            <p style="font-size:1.6rem; margin:4px 0">${price:,.2f}</p>
            <p style="color:{color}; margin:0">{sign}{change:.2f}%</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Crypto Price Dashboard", layout="wide")
    st.title("Crypto Price Dashboard")

    with st.spinner("Fetching latest prices…"):
        try:
            prices = fetch_prices(COINS)
            validate_prices(prices)
            append_prices(prices)
        except Exception as e:
            st.error(f"Failed to fetch prices: {e}")
            prices = None

    if prices is not None:
        cols = st.columns(3)
        for col, coin in zip(cols, COINS):
            symbol = COIN_SYMBOLS[coin]
            with col:
                render_price_card(
                    symbol,
                    prices[coin]["usd"],
                    prices[coin]["usd_24h_change"],
                )

    st.divider()

    history = load_history()
    if history is None or history.empty:
        st.info("No historical data yet — prices will appear here after the first successful fetch.")
    else:
        st.subheader("Price History")
        pivot = history.pivot_table(index="timestamp", columns="symbol", values="price")
        st.line_chart(pivot)

    time.sleep(REFRESH_INTERVAL)
    st.rerun()


if __name__ == "__main__":
    main()
