import csv
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from main import COINS, COIN_SYMBOLS, fetch_prices
from validator import ValidationError, validate_prices

DATA_FILE = Path("data/prices.csv")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def append_prices(prices: dict) -> None:
    DATA_FILE.parent.mkdir(exist_ok=True)
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
    write_header = not DATA_FILE.exists()
    with DATA_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "symbol", "price", "change_24h"])
        if write_header:
            writer.writeheader()
        writer.writerows(rows)
    return timestamp, rows


def fetch_job() -> None:
    try:
        prices = fetch_prices(COINS)
        validate_prices(prices)
        timestamp, rows = append_prices(prices)
        summary = ", ".join(
            f"{r['symbol']}=${r['price']:,.0f}" for r in rows
        )
        logger.info("✅ [%s] Fetched prices: %s", timestamp, summary)
    except ValidationError as exc:
        logger.error("❌ Validation error: %s", exc)
    except Exception as exc:
        logger.error("❌ Fetch error: %s", exc)


def main() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_job, "interval", hours=1, id="fetch_prices")
    scheduler.start()

    # Run immediately without waiting for the first interval
    fetch_job()

    def _shutdown(signum, frame):
        logger.info("Shutting down scheduler…")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Scheduler running. Next fetch in 1 hour. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
