import pytest
from validator import validate_prices, ValidationError


VALID_PRICES = {
    "bitcoin": {"usd": 83000.00, "usd_24h_change": 2.5},
    "ethereum": {"usd": 1800.00, "usd_24h_change": -1.2},
    "solana": {"usd": 120.00, "usd_24h_change": 5.3},
}


def test_valid_data_passes():
    validate_prices(VALID_PRICES)  # should not raise


def test_empty_response_raises():
    with pytest.raises(ValidationError, match="empty"):
        validate_prices({})


def test_missing_bitcoin_raises():
    prices = {k: v for k, v in VALID_PRICES.items() if k != "bitcoin"}
    with pytest.raises(ValidationError, match="bitcoin"):
        validate_prices(prices)


def test_missing_ethereum_raises():
    prices = {k: v for k, v in VALID_PRICES.items() if k != "ethereum"}
    with pytest.raises(ValidationError, match="ethereum"):
        validate_prices(prices)


def test_missing_solana_raises():
    prices = {k: v for k, v in VALID_PRICES.items() if k != "solana"}
    with pytest.raises(ValidationError, match="solana"):
        validate_prices(prices)


def test_negative_price_raises():
    prices = {**VALID_PRICES, "bitcoin": {"usd": -1.0, "usd_24h_change": 2.5}}
    with pytest.raises(ValidationError, match="Invalid price"):
        validate_prices(prices)


def test_zero_price_raises():
    prices = {**VALID_PRICES, "bitcoin": {"usd": 0, "usd_24h_change": 2.5}}
    with pytest.raises(ValidationError, match="Invalid price"):
        validate_prices(prices)


def test_change_below_minus_100_raises():
    prices = {**VALID_PRICES, "ethereum": {"usd": 1800.0, "usd_24h_change": -100.1}}
    with pytest.raises(ValidationError, match="out of range"):
        validate_prices(prices)


def test_change_above_1000_raises():
    prices = {**VALID_PRICES, "solana": {"usd": 120.0, "usd_24h_change": 1000.1}}
    with pytest.raises(ValidationError, match="out of range"):
        validate_prices(prices)


def test_change_at_boundary_minus_100_passes():
    prices = {**VALID_PRICES, "bitcoin": {"usd": 83000.0, "usd_24h_change": -100.0}}
    validate_prices(prices)  # should not raise


def test_change_at_boundary_1000_passes():
    prices = {**VALID_PRICES, "bitcoin": {"usd": 83000.0, "usd_24h_change": 1000.0}}
    validate_prices(prices)  # should not raise


def test_non_numeric_price_raises():
    prices = {**VALID_PRICES, "bitcoin": {"usd": "not_a_number", "usd_24h_change": 2.5}}
    with pytest.raises(ValidationError, match="Invalid price"):
        validate_prices(prices)


def test_non_numeric_change_raises():
    prices = {**VALID_PRICES, "bitcoin": {"usd": 83000.0, "usd_24h_change": None}}
    with pytest.raises(ValidationError, match="out of range"):
        validate_prices(prices)
