import requests
from datetime import datetime
from typing import Any


COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["bitcoin", "ethereum", "solana"]
COIN_SYMBOLS: dict[str, str] = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
}


def fetch_prices(coins: list[str]) -> dict[str, Any]:
    """Fetch current USD prices and 24h change for the given coins from CoinGecko."""
    params = {
        "ids": ",".join(coins),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    response = requests.get(COINGECKO_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def format_coin_line(coin: str, price_data: dict[str, Any]) -> str:
    """Format a single coin's price and 24h change as a display string."""
    symbol = COIN_SYMBOLS[coin]
    price = price_data["usd"]
    change = price_data["usd_24h_change"]
    sign = "+" if change >= 0 else ""
    return f"  {symbol}: ${price:,.2f} ({sign}{change:.1f}%)"


def print_prices(prices: dict[str, Any]) -> None:
    """Print formatted prices for all tracked coins with a timestamp header."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Crypto Prices — {timestamp}")
    print("-" * 30)
    for coin in COINS:
        print(format_coin_line(coin, prices[coin]))
    print("-" * 30)


def main() -> None:
    """Fetch and display current cryptocurrency prices."""
    prices = fetch_prices(COINS)
    print_prices(prices)


if __name__ == "__main__":
    main()
