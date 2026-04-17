import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from main import COINS, COIN_SYMBOLS

DEFAULT_DB_PATH = Path("data/prices.db")


def init_db(db_path: Path) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                price REAL,
                change_24h REAL
            )
        """)


def insert_prices(prices: dict, db_path: Path) -> tuple:
    db_path = Path(db_path)
    init_db(db_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [
        {
            "timestamp": timestamp,
            "symbol": COIN_SYMBOLS[coin],
            "price": prices[coin]["usd"],
            "change_24h": round(prices[coin]["usd_24h_change"], 2),
        }
        for coin in COINS
    ]
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            "INSERT INTO prices (timestamp, symbol, price, change_24h)"
            " VALUES (:timestamp, :symbol, :price, :change_24h)",
            rows,
        )
    return timestamp, rows


def get_history(db_path: Path) -> pd.DataFrame | None:
    db_path = Path(db_path)
    if not db_path.exists():
        return None
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT timestamp, symbol, price, change_24h FROM prices ORDER BY timestamp",
            conn,
            parse_dates=["timestamp"],
        )
    return df if not df.empty else None
