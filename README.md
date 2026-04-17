# Crypto Price Checker

Fetches and displays the current USD prices of BTC, ETH, and SOL using the [CoinGecko public API](https://www.coingecko.com/en/api). No API key required.

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Example output

```
Crypto Prices — 2026-04-06 14:32:01
------------------------------
  BTC   $   83,500.00
  ETH   $    1,590.00
  SOL   $      120.45
------------------------------
```

## Dashboard

An interactive Streamlit dashboard is included for visualizing live and historical prices.

![Dashboard](docs/dashboard.png)

**What it shows:**

- **Price cards** for BTC, ETH, and SOL — current USD price with 24h change highlighted in green (positive) or red (negative)
- **Historical line chart** — one line per coin, plotted from every price snapshot saved since first run
- **Auto-refresh** — the page reloads every 60 seconds to pull the latest prices

**Run the dashboard:**

```bash
streamlit run dashboard.py
```

Price history is written to `data/prices.csv` and accumulates across runs.

## Run with Docker

**Prerequisites:** [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)

```bash
docker compose up --build
```

Open **http://localhost:8501** in your browser.

Price history persists in `./data/prices.csv` on your local machine between container restarts.

## Project Structure

```
crypto-price-checker/
├── main.py              # CLI entry point — fetch, validate, and print prices as JSON
├── validator.py         # ValidationError and validate_prices() for API response checks
├── dashboard.py         # Streamlit dashboard — price cards, historical chart, auto-refresh
├── Dockerfile           # python:3.11-slim image, exposes port 8501
├── docker-compose.yml   # dashboard service with port mapping and data volume
├── requirements.txt     # Runtime and test dependencies
├── data/
│   └── prices.csv       # Auto-generated — price snapshots appended on each fetch
└── tests/
    ├── test_main.py     # Tests for fetching, formatting, and the main pipeline
    └── test_validator.py # Tests for all validation rules and edge cases
```
