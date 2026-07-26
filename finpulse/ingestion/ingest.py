"""
ingestion/ingest.py

Loops over tracked companies, fetches fresh data via yfinance, and
writes it into the database:
- companies table: upserted (update if exists, insert if new)
- price_history table: appended, de-duplicated on (ticker, date)

Includes a small delay between tickers to reduce the chance of
Yahoo Finance rate-limiting the run.
"""

import time
from datetime import datetime

from db.database import SessionLocal
from db.models import Company, PriceHistory
from data.fetch_stock import get_stock_snapshot, get_stock_history
from ingestion.companies import COMPANIES

DELAY_BETWEEN_TICKERS_SECONDS = 3


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


def run_ingestion():
    session = SessionLocal()
    for i, ticker in enumerate(COMPANIES):
        try:
            print(f"[{i+1}/{len(COMPANIES)}] Ingesting {ticker}...")
            ingest_company(ticker, session)
            session.commit()
        except Exception as e:
            print(f"  Failed for {ticker}: {e}")
            session.rollback()
        time.sleep(DELAY_BETWEEN_TICKERS_SECONDS)

    session.close()
    print("Ingestion complete.")


if __name__ == "__main__":
    run_ingestion()
