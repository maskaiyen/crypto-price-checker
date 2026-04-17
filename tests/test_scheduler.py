import csv
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import scheduler
from validator import ValidationError


MOCK_PRICES = {
    "bitcoin": {"usd": 83000.0, "usd_24h_change": 2.5},
    "ethereum": {"usd": 1800.0, "usd_24h_change": -1.2},
    "solana": {"usd": 120.0, "usd_24h_change": 5.3},
}


@pytest.fixture(autouse=True)
def tmp_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(scheduler, "DATA_FILE", tmp_path / "prices.csv")


# --- fetch_job: success ---

def test_fetch_job_success_logs_prices(caplog):
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices"), \
         patch("scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        scheduler.fetch_job()

    assert "✅" in caplog.text
    assert "BTC=$83,000" in caplog.text
    assert "ETH=$1,800" in caplog.text
    assert "SOL=$120" in caplog.text


def test_fetch_job_success_writes_csv():
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices"), \
         patch("scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        scheduler.fetch_job()

    rows = list(csv.DictReader(scheduler.DATA_FILE.open()))
    assert len(rows) == 3
    symbols = {r["symbol"] for r in rows}
    assert symbols == {"BTC", "ETH", "SOL"}


def test_fetch_job_success_csv_header():
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices"), \
         patch("scheduler.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        scheduler.fetch_job()

    header = scheduler.DATA_FILE.read_text().splitlines()[0]
    assert header == "timestamp,symbol,price,change_24h"


# --- fetch_job: ValidationError ---

def test_fetch_job_handles_validation_error(caplog):
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices", side_effect=ValidationError("Missing coin: bitcoin")):
        scheduler.fetch_job()

    assert "❌" in caplog.text
    assert "Missing coin: bitcoin" in caplog.text


def test_fetch_job_validation_error_does_not_write_csv():
    with patch("scheduler.fetch_prices", return_value=MOCK_PRICES), \
         patch("scheduler.validate_prices", side_effect=ValidationError("bad data")):
        scheduler.fetch_job()

    assert not scheduler.DATA_FILE.exists()


# --- fetch_job: network error ---

def test_fetch_job_handles_network_error(caplog):
    with patch("scheduler.fetch_prices", side_effect=ConnectionError("network unreachable")):
        scheduler.fetch_job()

    assert "❌" in caplog.text
    assert "network unreachable" in caplog.text


def test_fetch_job_network_error_does_not_write_csv():
    with patch("scheduler.fetch_prices", side_effect=ConnectionError("network unreachable")):
        scheduler.fetch_job()

    assert not scheduler.DATA_FILE.exists()
