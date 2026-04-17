import logging
import signal
import sys
import time
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from alerter import check_and_alert
from database import insert_prices
from main import COINS, fetch_prices
from validator import ValidationError, validate_prices

DB_PATH = Path("data/prices.db")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def fetch_job() -> None:
    try:
        prices = fetch_prices(COINS)
        validate_prices(prices)
        timestamp, rows = insert_prices(prices, DB_PATH)
        summary = ", ".join(
            f"{r['symbol']}=${r['price']:,.0f}" for r in rows
        )
        logger.info("✅ [%s] Fetched prices: %s", timestamp, summary)
        check_and_alert(prices)
    except ValidationError as exc:
        logger.error("❌ Validation error: %s", exc)
    except Exception as exc:
        logger.error("❌ Fetch error: %s", exc)


def main() -> None:
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_job, "interval", hours=1, id="fetch_prices")
    scheduler.start()

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
