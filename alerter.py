import logging
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Any

import requests

from main import COINS, COIN_SYMBOLS

ALERT_THRESHOLD = 5.0

logger = logging.getLogger(__name__)


def should_alert(symbol: str, change_24h: float) -> bool:
    return abs(change_24h) >= ALERT_THRESHOLD


def send_alert(symbol: str, price: float, change_24h: float) -> None:
    email_from = os.environ.get("ALERT_EMAIL_FROM")
    email_to = os.environ.get("ALERT_EMAIL_TO")
    password = os.environ.get("ALERT_EMAIL_PASSWORD")

    if not all([email_from, email_to, password]):
        logger.warning(
            "Alert skipped for %s: ALERT_EMAIL_FROM, ALERT_EMAIL_TO, and "
            "ALERT_EMAIL_PASSWORD must all be set.",
            symbol,
        )
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sign = "+" if change_24h >= 0 else ""

    msg = EmailMessage()
    msg["Subject"] = f"🚨 Crypto Alert: {symbol} moved {change_24h:+.1f}%"
    msg["From"] = email_from
    msg["To"] = email_to
    msg.set_content(
        f"Crypto Price Alert\n"
        f"------------------\n"
        f"Symbol:      {symbol}\n"
        f"Price:       ${price:,.2f}\n"
        f"24h Change:  {sign}{change_24h:.2f}%\n"
        f"Timestamp:   {timestamp}\n"
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(email_from, password)
        smtp.send_message(msg)

    logger.info("📧 Alert sent for %s (%s%.1f%%)", symbol, sign, abs(change_24h))


def send_slack_alert(symbol: str, price: float, change_24h: float) -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        logger.warning("Slack alert skipped for %s: SLACK_WEBHOOK_URL is not set.", symbol)
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"🚨 *Crypto Alert*\n"
        f"*{symbol}*: ${price:,.2f} ({change_24h:+.1f}%)\n"
        f"Time: {timestamp}"
    )
    requests.post(webhook_url, json={"text": text}, timeout=10)
    logger.info("💬 Slack alert sent for %s (%+.1f%%)", symbol, change_24h)


def check_and_alert(prices: dict[str, Any]) -> None:
    for coin in COINS:
        symbol = COIN_SYMBOLS[coin]
        change_24h = prices[coin]["usd_24h_change"]
        if should_alert(symbol, change_24h):
            send_alert(symbol, prices[coin]["usd"], change_24h)
            send_slack_alert(symbol, prices[coin]["usd"], change_24h)
