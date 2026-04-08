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


# --- format_change ---

def test_format_change_positive():
    assert main.format_change(2.5) == "+2.5%"

def test_format_change_negative():
    assert main.format_change(-1.2) == "-1.2%"

def test_format_change_zero():
    assert main.format_change(0.0) == "+0.0%"


# --- print_prices ---

def test_print_prices_output(capsys):
    main.print_prices(MOCK_PRICES)
    captured = capsys.readouterr()
    assert "BTC: $83,000 (+2.5%)" in captured.out
    assert "ETH: $1,800 (-1.2%)" in captured.out
    assert "SOL: $120 (+5.3%)" in captured.out


def test_print_prices_coin_order(capsys):
    main.print_prices(MOCK_PRICES)
    captured = capsys.readouterr()
    btc_pos = captured.out.index("BTC")
    eth_pos = captured.out.index("ETH")
    sol_pos = captured.out.index("SOL")
    assert btc_pos < eth_pos < sol_pos


# --- main ---

def test_main_calls_fetch_and_print():
    with patch("main.fetch_prices", return_value=MOCK_PRICES) as mock_fetch, \
         patch("main.print_prices") as mock_print:
        main.main()

    mock_fetch.assert_called_once_with(main.COINS)
    mock_print.assert_called_once_with(MOCK_PRICES)
