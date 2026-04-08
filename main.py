import requests
from datetime import datetime


COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["bitcoin", "ethereum", "solana"]
COIN_SYMBOLS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
}


def fetch_prices(coins):
    params = {
        "ids": ",".join(coins),
        "vs_currencies": "usd",
        "include_24hr_change": "true",
    }
    response = requests.get(COINGECKO_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def format_change(change):
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


def print_prices(prices):
    for coin in COINS:
        symbol = COIN_SYMBOLS[coin]
        price = prices[coin]["usd"]
        change = prices[coin]["usd_24h_change"]
        print(f"{symbol}: ${price:,.0f} ({format_change(change)})")


def main():
    prices = fetch_prices(COINS)
    print_prices(prices)


if __name__ == "__main__":
    main()
