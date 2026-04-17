import json
import requests
from datetime import datetime
from typing import Any

from validator import validate_prices


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


def format_prices_json(prices: dict[str, Any]) -> str:
    """Format prices as a JSON string with timestamp and per-symbol data."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return json.dumps(
        {
            "timestamp": timestamp,
            "prices": {
                COIN_SYMBOLS[coin]: {
                    "usd": prices[coin]["usd"],
                    "usd_24h_change": round(prices[coin]["usd_24h_change"], 1),
                }
                for coin in COINS
            },
        },
        indent=2,
    )


def print_prices(prices: dict[str, Any]) -> None:
    """Print prices as JSON to stdout."""
    print(format_prices_json(prices))


def main() -> None:
    """Fetch and display current cryptocurrency prices as JSON."""
    prices = fetch_prices(COINS)
    validate_prices(prices)
    print_prices(prices)


if __name__ == "__main__":
    main()
