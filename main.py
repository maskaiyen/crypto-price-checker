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
    }
    response = requests.get(COINGECKO_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def print_prices(prices):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Crypto Prices — {timestamp}")
    print("-" * 30)
    for coin in COINS:
        symbol = COIN_SYMBOLS[coin]
        price = prices[coin]["usd"]
        print(f"  {symbol:4s}  ${price:>12,.2f}")
    print("-" * 30)


def main():
    prices = fetch_prices(COINS)
    print_prices(prices)


if __name__ == "__main__":
    main()
