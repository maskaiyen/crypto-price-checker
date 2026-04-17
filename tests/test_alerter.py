import pytest
from unittest.mock import patch, MagicMock

import alerter
from alerter import should_alert, send_alert, send_slack_alert, check_and_alert


MOCK_PRICES = {
    "bitcoin": {"usd": 83000.0, "usd_24h_change": 7.5},   # above threshold
    "ethereum": {"usd": 1800.0, "usd_24h_change": -2.0},  # below threshold
    "solana": {"usd": 120.0,  "usd_24h_change": -6.0},    # above threshold (negative)
}


# --- should_alert ---

def test_should_alert_true_when_above_threshold():
    assert should_alert("BTC", 5.0) is True


def test_should_alert_true_when_well_above_threshold():
    assert should_alert("BTC", 7.5) is True


def test_should_alert_false_when_below_threshold():
    assert should_alert("ETH", 2.0) is False


def test_should_alert_false_when_just_below_threshold():
    assert should_alert("ETH", 4.99) is False


def test_should_alert_true_for_negative_change_at_threshold():
    assert should_alert("SOL", -5.0) is True


def test_should_alert_true_for_negative_change_above_threshold():
    assert should_alert("SOL", -6.0) is True


def test_should_alert_false_for_small_negative_change():
    assert should_alert("SOL", -1.5) is False


# --- send_alert: missing env vars ---

def test_send_alert_skips_when_env_vars_missing(caplog):
    with patch.dict("os.environ", {}, clear=True):
        send_alert("BTC", 83000.0, 7.5)

    assert "Alert skipped" in caplog.text
    assert "BTC" in caplog.text


def test_send_alert_skips_when_only_from_set(caplog):
    env = {"ALERT_EMAIL_FROM": "from@example.com"}
    with patch.dict("os.environ", env, clear=True):
        send_alert("BTC", 83000.0, 7.5)

    assert "Alert skipped" in caplog.text


def test_send_alert_does_not_call_smtp_when_env_missing():
    with patch.dict("os.environ", {}, clear=True), \
         patch("alerter.smtplib.SMTP") as mock_smtp:
        send_alert("BTC", 83000.0, 7.5)

    mock_smtp.assert_not_called()


# --- send_alert: SMTP interaction ---

def test_send_alert_calls_smtp_with_correct_host():
    env = {
        "ALERT_EMAIL_FROM": "from@example.com",
        "ALERT_EMAIL_TO": "to@example.com",
        "ALERT_EMAIL_PASSWORD": "secret",
    }
    mock_smtp = MagicMock()
    with patch.dict("os.environ", env), \
         patch("alerter.smtplib.SMTP", return_value=mock_smtp.__enter__.return_value) as smtp_cls:
        smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_alert("BTC", 83000.0, 7.5)

    smtp_cls.assert_called_once_with("smtp.gmail.com", 587)


def test_send_alert_calls_starttls_and_login():
    env = {
        "ALERT_EMAIL_FROM": "from@example.com",
        "ALERT_EMAIL_TO": "to@example.com",
        "ALERT_EMAIL_PASSWORD": "secret",
    }
    mock_smtp = MagicMock()
    with patch.dict("os.environ", env), \
         patch("alerter.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_alert("BTC", 83000.0, 7.5)

    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("from@example.com", "secret")


def test_send_alert_subject_contains_symbol_and_change():
    env = {
        "ALERT_EMAIL_FROM": "from@example.com",
        "ALERT_EMAIL_TO": "to@example.com",
        "ALERT_EMAIL_PASSWORD": "secret",
    }
    mock_smtp = MagicMock()
    sent_messages = []
    mock_smtp.send_message.side_effect = lambda msg: sent_messages.append(msg)

    with patch.dict("os.environ", env), \
         patch("alerter.smtplib.SMTP") as smtp_cls:
        smtp_cls.return_value.__enter__ = lambda s: mock_smtp
        smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        send_alert("BTC", 83000.0, 7.5)

    assert len(sent_messages) == 1
    assert "BTC" in sent_messages[0]["Subject"]
    assert "+7.5%" in sent_messages[0]["Subject"]


# --- check_and_alert: send_alert ---

def test_check_and_alert_calls_send_alert_for_coins_above_threshold():
    with patch("alerter.send_alert") as mock_send, \
         patch("alerter.send_slack_alert"):
        check_and_alert(MOCK_PRICES)

    called_symbols = {call.args[0] for call in mock_send.call_args_list}
    assert "BTC" in called_symbols   # +7.5%
    assert "SOL" in called_symbols   # -6.0%


def test_check_and_alert_skips_coins_below_threshold():
    with patch("alerter.send_alert") as mock_send, \
         patch("alerter.send_slack_alert"):
        check_and_alert(MOCK_PRICES)

    called_symbols = {call.args[0] for call in mock_send.call_args_list}
    assert "ETH" not in called_symbols  # -2.0%


def test_check_and_alert_send_alert_call_count():
    with patch("alerter.send_alert") as mock_send, \
         patch("alerter.send_slack_alert"):
        check_and_alert(MOCK_PRICES)

    assert mock_send.call_count == 2


# --- send_slack_alert: missing env var ---

def test_send_slack_alert_skips_when_env_var_missing(caplog):
    with patch.dict("os.environ", {}, clear=True):
        send_slack_alert("BTC", 83000.0, 7.5)

    assert "Slack alert skipped" in caplog.text
    assert "BTC" in caplog.text


def test_send_slack_alert_does_not_call_requests_when_env_missing():
    with patch.dict("os.environ", {}, clear=True), \
         patch("alerter.requests.post") as mock_post:
        send_slack_alert("BTC", 83000.0, 7.5)

    mock_post.assert_not_called()


# --- send_slack_alert: requests.post interaction ---

def test_send_slack_alert_calls_post_with_correct_url():
    env = {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"}
    with patch.dict("os.environ", env), \
         patch("alerter.requests.post") as mock_post:
        send_slack_alert("BTC", 83000.0, 7.5)

    mock_post.assert_called_once()
    assert mock_post.call_args.args[0] == "https://hooks.slack.com/services/TEST"


def test_send_slack_alert_payload_contains_symbol():
    env = {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"}
    with patch.dict("os.environ", env), \
         patch("alerter.requests.post") as mock_post:
        send_slack_alert("BTC", 83000.0, 7.5)

    payload = mock_post.call_args.kwargs["json"]
    assert "BTC" in payload["text"]


def test_send_slack_alert_payload_contains_price():
    env = {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"}
    with patch.dict("os.environ", env), \
         patch("alerter.requests.post") as mock_post:
        send_slack_alert("BTC", 83000.0, 7.5)

    payload = mock_post.call_args.kwargs["json"]
    assert "83,000.00" in payload["text"]


def test_send_slack_alert_payload_contains_change():
    env = {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/TEST"}
    with patch.dict("os.environ", env), \
         patch("alerter.requests.post") as mock_post:
        send_slack_alert("BTC", 83000.0, 7.5)

    payload = mock_post.call_args.kwargs["json"]
    assert "+7.5%" in payload["text"]


# --- check_and_alert: send_slack_alert ---

def test_check_and_alert_calls_slack_alert_for_coins_above_threshold():
    with patch("alerter.send_alert"), \
         patch("alerter.send_slack_alert") as mock_slack:
        check_and_alert(MOCK_PRICES)

    called_symbols = {call.args[0] for call in mock_slack.call_args_list}
    assert "BTC" in called_symbols
    assert "SOL" in called_symbols


def test_check_and_alert_skips_slack_for_coins_below_threshold():
    with patch("alerter.send_alert"), \
         patch("alerter.send_slack_alert") as mock_slack:
        check_and_alert(MOCK_PRICES)

    called_symbols = {call.args[0] for call in mock_slack.call_args_list}
    assert "ETH" not in called_symbols


def test_check_and_alert_calls_both_alerts_for_triggered_coins():
    with patch("alerter.send_alert") as mock_email, \
         patch("alerter.send_slack_alert") as mock_slack:
        check_and_alert(MOCK_PRICES)

    assert mock_email.call_count == 2
    assert mock_slack.call_count == 2
