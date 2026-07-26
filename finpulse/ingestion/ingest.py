"""
ingestion/ingest.py

Loops over tracked companies, fetches fresh data via yfinance, and
writes it into the database:
- companies table: upserted (update if exists, insert if new)
- price_history table: appended, de-duplicated on (ticker, date)

Includes a small delay between tickers to reduce the chance of
Yahoo Finance rate-limiting the run.
"""

import argparse
import random
import time
from datetime import datetime

from db.database import SessionLocal
from db.models import Company, PriceHistory
from data.fetch_stock import get_stock_snapshot, get_stock_history
from ingestion.companies import COMPANIES

DELAY_BETWEEN_TICKERS_SECONDS = 180


def ingest_company(ticker: str, session):
    snapshot = get_stock_snapshot(ticker)

    existing = session.query(Company).filter_by(ticker=ticker).first()
    if existing:
        existing.price = snapshot["price"]
        existing.market_cap = snapshot["market_cap"]
        existing.pe_ratio = snapshot["pe_ratio"]
        existing.eps = snapshot["eps"]
        existing.last_updated = datetime.now()
    else:
        session.add(Company(
            ticker=snapshot["ticker"],
            price=snapshot["price"],
            market_cap=snapshot["market_cap"],
            pe_ratio=snapshot["pe_ratio"],
            eps=snapshot["eps"],
            last_updated=datetime.now(),
        ))

    history = get_stock_history(ticker)
    for _, row in history.iterrows():
        row_date = row["Date"].date() if hasattr(row["Date"], "date") else row["Date"]

        exists = (
            session.query(PriceHistory)
            .filter_by(ticker=ticker, date=row_date)
            .first()
        )
        if exists:
            continue

        session.add(PriceHistory(
            ticker=ticker,
            date=row_date,
            open=row["Open"],
            high=row["High"],
            low=row["Low"],
            close=row["Close"],
            volume=row["Volume"],
        ))


def run_ingestion(tickers: list[str], delay: float = DELAY_BETWEEN_TICKERS_SECONDS):
    session = SessionLocal()
    for i, ticker in enumerate(tickers):
        try:
            print(f"[{i+1}/{len(tickers)}] Ingesting {ticker}...")
            ingest_company(ticker, session)
            session.commit()
        except Exception as e:
            print(f"  Failed for {ticker}: {e}")
            session.rollback()
        time.sleep(delay + random.uniform(5, 15))

    session.close()
    print("Ingestion complete.")


def parse_args():
    parser = argparse.ArgumentParser(description="Run FinPulse ingestion in smaller batches")
    parser.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of tickers to ingest, e.g. RELIANCE.NS,TCS.NS",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="First index of the tracked ticker list to ingest",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of tickers to ingest from the start index; 0 means all remaining",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DELAY_BETWEEN_TICKERS_SECONDS,
        help="Seconds to wait between tickers",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = COMPANIES[args.start: args.start + args.count] if args.count else COMPANIES[args.start:]

    if not tickers:
        raise SystemExit("No tickers selected for ingestion.")

    print(f"Ingesting {len(tickers)} tickers: {tickers}")
    run_ingestion(tickers=tickers, delay=args.delay)
