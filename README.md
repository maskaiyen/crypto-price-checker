# Crypto Price Checker

A lightweight command-line tool that fetches live cryptocurrency prices from the CoinGecko public API and outputs structured JSON. Built to demonstrate clean Python architecture, external API integration, and defensive data validation.

## Overview

Crypto Price Checker queries real-time USD prices and 24-hour percentage changes for Bitcoin, Ethereum, and Solana. It validates the API response before processing, ensuring the pipeline never silently produces bad output. Results are printed as formatted JSON, making the tool easy to compose with other scripts or monitoring workflows.

No API key required.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| HTTP client | `requests` |
| Output format | JSON (via `json` stdlib) |
| Testing | `pytest` with `unittest.mock` |
| Storage | SQLite (via `sqlite3` stdlib + `pandas`) |
| Scheduling | APScheduler `BackgroundScheduler` |
| API | CoinGecko Free Public API |

## Features

- **Live price data** — fetches current USD prices for BTC, ETH, and SOL
- **24h change tracking** — includes percentage change over the last 24 hours
- **JSON output** — structured, timestamped output ready for piping or logging
- **Data validation** — validates every API response before use; raises a typed `ValidationError` on bad data
- **SQLite database storage** — price history stored in a local SQLite database, shared by the dashboard and scheduler
- **Comprehensive test suite** — 44 unit tests covering fetching, formatting, validation logic, database operations, scheduling, and error handling
- **Streamlit dashboard** — live price cards with 24h change colouring, historical line chart, and 60-second auto-refresh
- **Scheduled execution** — background job fetches prices every hour, with an immediate first run and graceful Ctrl+C shutdown
- **Docker support** — single `docker compose up --build` to run the dashboard in a container with persistent data

## Installation

```bash
git clone https://github.com/maskaiyen/crypto-price-checker.git
cd crypto-price-checker
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

**Example output:**

```json
{
  "timestamp": "2026-04-17 14:32:01",
  "prices": {
    "BTC": {
      "usd": 83500.0,
      "usd_24h_change": 1.2
    },
    "ETH": {
      "usd": 1590.0,
      "usd_24h_change": -0.8
    },
    "SOL": {
      "usd": 120.45,
      "usd_24h_change": 3.1
    }
  }
}
```

## Running Tests

```bash
pytest
```

All 44 tests use mocked network calls and do not require an internet connection.

## Dashboard

An interactive Streamlit dashboard for visualizing live and historical prices.

**What it shows:**

- **Price cards** for BTC, ETH, and SOL — current USD price with 24h change highlighted in green (positive) or red (negative)
- **Historical line chart** — one line per coin, plotted from every price snapshot saved since first run
- **Auto-refresh** — the page reloads every 60 seconds to pull the latest prices

**Run the dashboard:**

```bash
streamlit run dashboard.py
```

Price history is written to `data/prices.db` and accumulates across runs.

## Scheduler

`scheduler.py` runs as a long-lived process that fetches and stores prices automatically.

**What it does:**

- Fetches and validates prices immediately on startup — no waiting for the first interval
- Re-fetches every hour using APScheduler's `BackgroundScheduler`
- Inserts each snapshot into `data/prices.db` (shared with the dashboard)
- Logs a success line with prices on each run, or an error message if the fetch or validation fails
- Shuts down gracefully on `Ctrl+C` or `SIGTERM`

**Run:**

```bash
python scheduler.py
```

**Example log output:**

```
✅ [2026-04-17 12:00:00] Fetched prices: BTC=$83,000, ETH=$1,800, SOL=$120
Scheduler running. Next fetch in 1 hour. Press Ctrl+C to stop.
```

## Run with Docker

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

```bash
docker compose up --build
```

Open **http://localhost:8501** in your browser.

Price history persists in `./data/prices.db` on your local machine between container restarts.

## Project Structure

```
crypto-price-checker/
├── main.py              # CLI entry point — fetch, validate, and print prices as JSON
├── validator.py         # ValidationError and validate_prices() for API response checks
├── database.py          # SQLite layer — init_db, insert_prices, get_history
├── dashboard.py         # Streamlit dashboard — price cards, historical chart, auto-refresh
├── scheduler.py         # Hourly price fetcher — APScheduler job, DB insert, structured logs
├── Dockerfile           # python:3.11-slim image, exposes port 8501
├── docker-compose.yml   # dashboard service with port mapping and data volume
├── requirements.txt     # Runtime and test dependencies
├── data/
│   └── prices.db        # Auto-generated — SQLite database of price snapshots
└── tests/
    ├── test_main.py      # Tests for fetching, formatting, and the main pipeline
    ├── test_validator.py # Tests for all validation rules and edge cases
    ├── test_database.py  # Tests for init_db, insert_prices, get_history, and accumulation
    └── test_scheduler.py # Tests for job success, ValidationError, and network error handling
```

## Design Decisions

### Why SQLite instead of CSV?

CSV is simple but fragile: concurrent writes corrupt it, there is no schema enforcement, and querying historical data requires loading the entire file into memory. SQLite solves all three problems with zero operational overhead — it is a single file, needs no server, and ships with Python's standard library. Using `sqlite3` directly (rather than an ORM) keeps the dependency count low while giving the project a proper relational foundation that can be queried, filtered, and extended without changing the storage format.

### Why add a validation layer?

The CoinGecko free API is unauthenticated and unguaranteed. Responses can be malformed, incomplete, or return unexpected values — especially under rate limits or outages. Without validation, these failures would either cause a cryptic `KeyError` deep in the formatting logic, or worse, silently produce incorrect output (e.g., a zero or negative price rendered as if it were real).

### What `ValidationError` does

`ValidationError` is a dedicated exception class that makes failure intent explicit. Rather than letting a `KeyError` or `TypeError` propagate with no context, the validation layer raises `ValidationError` with a descriptive message identifying exactly which coin and which field failed. This makes errors easy to catch, log, and handle at the application boundary.

### How it protects the pipeline

`validate_prices()` runs immediately after `fetch_prices()` and before any formatting or output. It enforces four invariants:

1. **Non-empty response** — guards against empty `{}` returned on API errors
2. **All coins present** — ensures BTC, ETH, and SOL are all in the response
3. **Positive price** — a zero or negative price indicates corrupt data
4. **Bounded 24h change** — changes outside `[-100%, +1000%]` are statistically implausible and signal bad data

If any check fails, execution stops before a single byte of output is written. The pipeline is all-or-nothing: either the data is trustworthy, or it is rejected.
