import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch

from database import init_db, insert_prices, get_history


MOCK_PRICES = {
    "bitcoin": {"usd": 83000.0, "usd_24h_change": 2.5},
    "ethereum": {"usd": 1800.0, "usd_24h_change": -1.2},
    "solana": {"usd": 120.0, "usd_24h_change": 5.3},
}


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "prices.db"


# --- init_db ---

def test_init_db_creates_file(db_path):
    init_db(db_path)
    assert db_path.exists()


def test_init_db_creates_prices_table(db_path):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        assert cur.fetchone() is not None


def test_init_db_correct_columns(db_path):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("PRAGMA table_info(prices)")
        columns = {row[1] for row in cur.fetchall()}
    assert columns == {"id", "timestamp", "symbol", "price", "change_24h"}


def test_init_db_idempotent(db_path):
    init_db(db_path)
    init_db(db_path)  # should not raise
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prices'")
        assert cur.fetchone() is not None


# --- insert_prices ---

def test_insert_prices_stores_three_rows(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        insert_prices(MOCK_PRICES, db_path)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM prices")
        assert cur.fetchone()[0] == 3


def test_insert_prices_correct_values(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        insert_prices(MOCK_PRICES, db_path)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT symbol, price, change_24h FROM prices ORDER BY symbol")
        rows = {r[0]: (r[1], r[2]) for r in cur.fetchall()}

    assert rows["BTC"] == (83000.0, 2.5)
    assert rows["ETH"] == (1800.0, -1.2)
    assert rows["SOL"] == (120.0, 5.3)


def test_insert_prices_returns_timestamp_and_rows(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        timestamp, rows = insert_prices(MOCK_PRICES, db_path)

    assert timestamp == "2026-04-17 12:00:00"
    assert len(rows) == 3
    symbols = {r["symbol"] for r in rows}
    assert symbols == {"BTC", "ETH", "SOL"}


# --- get_history ---

def test_get_history_returns_none_when_no_db(db_path):
    assert get_history(db_path) is None


def test_get_history_returns_dataframe(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        insert_prices(MOCK_PRICES, db_path)

    df = get_history(db_path)
    assert df is not None
    assert set(df.columns) >= {"timestamp", "symbol", "price", "change_24h"}


def test_get_history_correct_row_count(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        insert_prices(MOCK_PRICES, db_path)

    df = get_history(db_path)
    assert len(df) == 3


# --- multiple inserts accumulate ---

def test_multiple_inserts_accumulate(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        insert_prices(MOCK_PRICES, db_path)
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 13:00:00"
        insert_prices(MOCK_PRICES, db_path)

    df = get_history(db_path)
    assert len(df) == 6


def test_multiple_inserts_preserve_all_timestamps(db_path):
    with patch("database.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 12:00:00"
        insert_prices(MOCK_PRICES, db_path)
        mock_dt.now.return_value.strftime.return_value = "2026-04-17 13:00:00"
        insert_prices(MOCK_PRICES, db_path)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT DISTINCT timestamp FROM prices ORDER BY timestamp")
        timestamps = [r[0] for r in cur.fetchall()]

    assert timestamps == ["2026-04-17 12:00:00", "2026-04-17 13:00:00"]
