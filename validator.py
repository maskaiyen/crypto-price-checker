from typing import Any

EXPECTED_COINS = ["bitcoin", "ethereum", "solana"]


class ValidationError(Exception):
    pass


def validate_prices(prices: dict[str, Any]) -> None:
    """Validate a CoinGecko price response dict.

    Raises ValidationError if any check fails:
    - Response must not be empty
    - All expected coins must be present
    - Price (usd) must be a positive number
    - 24h change must be between -100% and +1000%
    """
    if not prices:
        raise ValidationError("Response is empty")

    for coin in EXPECTED_COINS:
        if coin not in prices:
            raise ValidationError(f"Missing expected coin: {coin}")

        data = prices[coin]
        price = data.get("usd")
        if not isinstance(price, (int, float)) or price <= 0:
            raise ValidationError(f"Invalid price for {coin}: {price!r}")

        change = data.get("usd_24h_change")
        if not isinstance(change, (int, float)) or not (-100 <= change <= 1000):
            raise ValidationError(f"24h change out of range for {coin}: {change!r}")
