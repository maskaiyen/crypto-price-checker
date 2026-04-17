import pytest
from unittest.mock import patch

import scheduler
from validator import ValidationError


MOCK_PRICES = {
    "bitcoin": {"usd": 83000.0, "usd_24h_change": 2.5},
    "ethereum": {"usd": 1800.0, "usd_24h_change": -1.2},
    "solana": {"usd": 120.0, "usd_24h_change": 5.3},
}

MOCK_ROWS = [
    {"symbol": "BTC", "price": 83000.0, "change_24h": 2.5},
    {"symbol": "ETH", "price": 1800.0, "change_24h": -1.2},
    {"symbol": "SOL", "price": 120.0, "change_24h": 5.3},
]


# --- fetch_job: success ---

def test_fetch_job_success_logs_prices(caplog):
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices"), \
         patch("scheduler.insert_prices", return_value=("2026-04-17 12:00:00", MOCK_ROWS)):
        scheduler.fetch_job()

    assert "✅" in caplog.text
    assert "BTC=$83,000" in caplog.text
    assert "ETH=$1,800" in caplog.text
    assert "SOL=$120" in caplog.text


def test_fetch_job_success_calls_insert_prices():
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices"), \
         patch("scheduler.insert_prices", return_value=("2026-04-17 12:00:00", MOCK_ROWS)) as mock_insert:
        scheduler.fetch_job()

    mock_insert.assert_called_once_with(MOCK_PRICES, scheduler.DB_PATH)


# --- fetch_job: ValidationError ---

def test_fetch_job_handles_validation_error(caplog):
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices", side_effect=ValidationError("Missing coin: bitcoin")):
        scheduler.fetch_job()

    assert "❌" in caplog.text
    assert "Missing coin: bitcoin" in caplog.text


def test_fetch_job_validation_error_does_not_call_insert(caplog):
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices", side_effect=ValidationError("bad data")), \
         patch("scheduler.insert_prices") as mock_insert:
        scheduler.fetch_job()

    mock_insert.assert_not_called()


# --- fetch_job: network error ---

def test_fetch_job_handles_network_error(caplog):
    with patch("scheduler.fetch_prices", side_effect=ConnectionError("network unreachable")):
        scheduler.fetch_job()

    assert "❌" in caplog.text
    assert "network unreachable" in caplog.text


def test_fetch_job_network_error_does_not_call_insert():
    with patch("scheduler.fetch_prices", side_effect=ConnectionError("network unreachable")), \
         patch("scheduler.insert_prices") as mock_insert:
        scheduler.fetch_job()

    mock_insert.assert_not_called()
