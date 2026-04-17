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
| API | CoinGecko Free Public API |

## Features

- **Live price data** — fetches current USD prices for BTC, ETH, and SOL
- **24h change tracking** — includes percentage change over the last 24 hours
- **JSON output** — structured, timestamped output ready for piping or logging
- **Data validation** — validates every API response before use; raises a typed `ValidationError` on bad data
- **Comprehensive test suite** — unit tests cover fetching, formatting, validation logic, and the full main pipeline

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

All tests use mocked network calls and do not require an internet connection.

## Project Structure

```
crypto-price-checker/
├── main.py              # Entry point — orchestrates fetch, validate, and print
├── validator.py         # Validation layer — ValidationError and validate_prices()
├── requirements.txt     # Runtime and test dependencies
└── tests/
    ├── test_main.py     # Tests for fetching, formatting, and the main pipeline
    └── test_validator.py # Tests for all validation rules and edge cases
```

## Design Decisions

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
