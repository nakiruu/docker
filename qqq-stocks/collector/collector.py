#!/usr/bin/env python3
"""
Real-time QQQ (Nasdaq-100) stock data collector for InfluxDB.

Data source: Yahoo Finance via yfinance (free, ~1-min delayed during market hours).
Holdings source: Wikipedia Nasdaq-100 page, with a hardcoded fallback.
"""

import os
import time
import logging
from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger(__name__)

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "http://influxdb:8086")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "qqq-stock-token-change-me")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "stocks")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "qqq")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))

# Nasdaq-100 components — used when Wikipedia is unreachable (updated 2025-Q1)
FALLBACK_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "ADBE", "QCOM", "INTU", "CSCO", "AMGN", "TXN", "AMAT", "ISRG",
    "BKNG", "MU", "LRCX", "ADI", "PANW", "REGN", "VRTX", "GILD", "KLAC", "MELI",
    "MDLZ", "SNPS", "CDNS", "ADP", "PYPL", "CTAS", "FTNT", "MRVL", "KDP", "ORLY",
    "ABNB", "PAYX", "PCAR", "IDXX", "ROST", "DXCM", "CPRT", "WDAY", "ODFL", "MNST",
    "FAST", "BIIB", "CTSH", "VRSK", "EA", "EXC", "ON", "ZS", "CRWD", "MCHP",
    "NXPI", "XEL", "GEHC", "CDW", "TTD", "DLTR", "MRNA", "TEAM", "ANSS", "WBD",
    "ILMN", "ALGN", "ENPH", "DDOG", "ROP", "CHTR", "SBUX", "LULU", "CEG", "CCEP",
    "DASH", "APP", "ARM", "PLTR", "SMCI", "INTC", "HOOD", "MSTR",
]


def get_qqq_tickers() -> list[str]:
    """Fetch current Nasdaq-100 tickers from Wikipedia."""
    try:
        tables = pd.read_html("https://en.wikipedia.org/wiki/Nasdaq-100")
        for table in tables:
            for col in ("Ticker", "Symbol", "Ticker symbol", "Stock Symbol"):
                if col in table.columns:
                    tickers = table[col].dropna().str.strip().tolist()
                    if len(tickers) >= 90:
                        log.info("Fetched %d tickers from Wikipedia", len(tickers))
                        return tickers
    except Exception as exc:
        log.warning("Wikipedia fetch failed: %s", exc)

    log.info("Using fallback ticker list (%d tickers)", len(FALLBACK_TICKERS))
    return list(FALLBACK_TICKERS)


def fetch_latest_bars(tickers: list[str]) -> dict[str, dict]:
    """
    Download the most recent 1-minute OHLCV bar for every ticker.

    yfinance batches all tickers in a single HTTP request, so this is
    fast even for 100 symbols.  During market hours the last bar is the
    current (in-progress) minute, giving effectively real-time prices.
    """
    data = yf.download(
        tickers=tickers,
        period="1d",
        interval="1m",
        auto_adjust=True,
        progress=False,
        threads=True,
        group_by="ticker",
    )

    records: dict[str, dict] = {}
    single = len(tickers) == 1

    for ticker in tickers:
        try:
            df = data if single else data[ticker]
            df = df.dropna(how="all")
            if df.empty:
                continue
            row = df.iloc[-1]
            ts = df.index[-1]
            # Convert to UTC-aware datetime
            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")
            records[ticker] = {
                "timestamp": ts.to_pydatetime(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]),
            }
        except Exception as exc:
            log.debug("Skipping %s: %s", ticker, exc)

    return records


def write_records(write_api, records: dict[str, dict]) -> None:
    """Batch-write OHLCV records to InfluxDB."""
    points = [
        Point("stock_price")
        .tag("ticker", ticker)
        .field("open", r["open"])
        .field("high", r["high"])
        .field("low", r["low"])
        .field("close", r["close"])
        .field("volume", r["volume"])
        .time(r["timestamp"], WritePrecision.SECONDS)
        for ticker, r in records.items()
    ]
    if points:
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=points)


def wait_for_influxdb(client: InfluxDBClient, retries: int = 30, delay: int = 5) -> None:
    for attempt in range(1, retries + 1):
        try:
            client.ping()
            log.info("InfluxDB is ready")
            return
        except Exception:
            log.info("Waiting for InfluxDB… (%d/%d)", attempt, retries)
            time.sleep(delay)
    raise RuntimeError("InfluxDB did not become ready in time")


def main() -> None:
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    wait_for_influxdb(client)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    tickers = get_qqq_tickers()
    log.info("Monitoring %d QQQ tickers, polling every %ds", len(tickers), POLL_INTERVAL)

    holdings_refreshed_at = time.monotonic()

    while True:
        loop_start = time.monotonic()

        # Refresh the holdings list once per day
        if time.monotonic() - holdings_refreshed_at > 86_400:
            tickers = get_qqq_tickers()
            holdings_refreshed_at = time.monotonic()

        try:
            records = fetch_latest_bars(tickers)
            write_records(write_api, records)
            log.info(
                "Wrote %d/%d tickers to InfluxDB at %s",
                len(records),
                len(tickers),
                datetime.now(timezone.utc).strftime("%H:%M:%SZ"),
            )
        except Exception as exc:
            log.error("Collection error: %s", exc)

        elapsed = time.monotonic() - loop_start
        sleep_for = max(0.0, POLL_INTERVAL - elapsed)
        log.info("Next poll in %.0fs", sleep_for)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
