import json
import pytest
from unittest.mock import patch, MagicMock

import main


MOCK_PRICES = {
    "bitcoin": {"usd": 83000.00, "usd_24h_change": 2.5},
    "ethereum": {"usd": 1800.00, "usd_24h_change": -1.2},
    "solana": {"usd": 120.00, "usd_24h_change": 5.3},
}


# --- fetch_prices ---

def test_fetch_prices_returns_data():
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_PRICES

    with patch("main.requests.get", return_value=mock_response) as mock_get:
        result = main.fetch_prices(main.COINS)

    mock_get.assert_called_once_with(
        main.COINGECKO_URL,
        params={
            "ids": "bitcoin,ethereum,solana",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
        },
        timeout=10,
    )
    mock_response.raise_for_status.assert_called_once()
    assert result == MOCK_PRICES


def test_fetch_prices_raises_on_http_error():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")

    with patch("main.requests.get", return_value=mock_response):
        with pytest.raises(Exception, match="404 Not Found"):
            main.fetch_prices(main.COINS)


def test_fetch_prices_raises_on_network_error():
    with patch("main.requests.get", side_effect=ConnectionError("network error")):
        with pytest.raises(ConnectionError):
            main.fetch_prices(main.COINS)


# --- format_prices_json ---

def test_format_prices_json_is_valid_json():
    with patch("main.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-07 12:00:00"
        result = main.format_prices_json(MOCK_PRICES)

    parsed = json.loads(result)
    assert isinstance(parsed, dict)


def test_format_prices_json_timestamp():
    with patch("main.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-07 12:00:00"
        result = main.format_prices_json(MOCK_PRICES)

    parsed = json.loads(result)
    assert parsed["timestamp"] == "2026-04-07 12:00:00"


def test_format_prices_json_values():
    with patch("main.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-07 12:00:00"
        result = main.format_prices_json(MOCK_PRICES)

    parsed = json.loads(result)
    assert parsed["prices"]["BTC"]["usd"] == 83000.00
    assert parsed["prices"]["BTC"]["usd_24h_change"] == 2.5
    assert parsed["prices"]["ETH"]["usd"] == 1800.00
    assert parsed["prices"]["ETH"]["usd_24h_change"] == -1.2
    assert parsed["prices"]["SOL"]["usd"] == 120.00
    assert parsed["prices"]["SOL"]["usd_24h_change"] == 5.3


def test_format_prices_json_all_symbols_present():
    with patch("main.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-07 12:00:00"
        result = main.format_prices_json(MOCK_PRICES)

    parsed = json.loads(result)
    assert set(parsed["prices"].keys()) == {"BTC", "ETH", "SOL"}


# --- print_prices ---

def test_print_prices_outputs_json(capsys):
    with patch("main.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-07 12:00:00"
        main.print_prices(MOCK_PRICES)

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert parsed["timestamp"] == "2026-04-07 12:00:00"
    assert "BTC" in parsed["prices"]


# --- main ---

def test_main_calls_fetch_and_print():
    with patch("main.fetch_prices", return_value=MOCK_PRICES) as mock_fetch, \
         patch("main.print_prices") as mock_print:
        main.main()

    mock_fetch.assert_called_once_with(main.COINS)
    mock_print.assert_called_once_with(MOCK_PRICES)
