"""
ingestion/mock_ingest.py

Seed the database with mock stock data for demo/testing purposes.
Useful when Yahoo Finance is rate-limited.
"""

from datetime import datetime, timedelta
import random
from db.database import SessionLocal
from db.models import Company, PriceHistory

MOCK_COMPANIES = {
    "RELIANCE.NS": {"price": 2850.50, "market_cap": 1900000000000, "pe_ratio": 25.3, "eps": 112.5},
    "TCS.NS": {"price": 3520.75, "market_cap": 1450000000000, "pe_ratio": 28.1, "eps": 125.2},
    "HDFCBANK.NS": {"price": 1680.25, "market_cap": 1350000000000, "pe_ratio": 22.5, "eps": 74.6},
    "INFY.NS": {"price": 1850.60, "market_cap": 770000000000, "pe_ratio": 24.8, "eps": 74.5},
    "ICICIBANK.NS": {"price": 975.30, "market_cap": 620000000000, "pe_ratio": 19.2, "eps": 50.8},
    "HINDUNILVR.NS": {"price": 2485.50, "market_cap": 520000000000, "pe_ratio": 65.3, "eps": 38.0},
    "SBIN.NS": {"price": 620.25, "market_cap": 510000000000, "pe_ratio": 8.5, "eps": 72.9},
    "BHARTIARTL.NS": {"price": 1255.75, "market_cap": 405000000000, "pe_ratio": 18.6, "eps": 67.4},
    "ITC.NS": {"price": 425.40, "market_cap": 420000000000, "pe_ratio": 18.3, "eps": 23.2},
    "KOTAKBANK.NS": {"price": 1885.50, "market_cap": 385000000000, "pe_ratio": 21.4, "eps": 88.0},
}


def ingest_mock_data():
    """Populate database with mock stock data for demo purposes."""
    session = SessionLocal()
    
    print("Seeding mock stock data...")
    
    for ticker, snapshot in MOCK_COMPANIES.items():
        # Check if company already exists
        existing = session.query(Company).filter_by(ticker=ticker).first()
        if existing:
            print(f"  {ticker}: already exists, skipping")
            continue
        
        # Add company
        company = Company(
            ticker=ticker,
            price=snapshot["price"],
            market_cap=snapshot["market_cap"],
            pe_ratio=snapshot["pe_ratio"],
            eps=snapshot["eps"],
            last_updated=datetime.now(),
        )
        session.add(company)
        session.commit()
        print(f"  {ticker}: added")
        
        # Add mock 6-month price history
        base_price = snapshot["price"]
        for days_back in range(180, 0, -1):
            date = datetime.now().date() - timedelta(days=days_back)
            
            # Generate realistic price movement (±2% daily)
            close = base_price * (1 + random.uniform(-0.02, 0.02))
            open_price = base_price * (1 + random.uniform(-0.02, 0.02))
            high = max(close, open_price) * (1 + random.uniform(0, 0.01))
            low = min(close, open_price) * (1 - random.uniform(0, 0.01))
            volume = random.randint(1000000, 50000000)
            
            history = PriceHistory(
                ticker=ticker,
                date=date,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=volume,
            )
            session.add(history)
            base_price = close  # Use today's close as tomorrow's starting point
        
        session.commit()
        print(f"  {ticker}: 180 days of mock history added")
    
    session.close()
    print("Mock ingestion complete.")


if __name__ == "__main__":
    ingest_mock_data()
