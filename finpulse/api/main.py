"""
api/main.py

FastAPI app entrypoint. Registers all routes (stocks, summary, chatbot)
and sets up CORS so the Streamlit dashboard can call this API.

Run with: uvicorn api.main:app --reload
"""

from dotenv import load_dotenv

# Must run before the chatbot imports below, which read ANTHROPIC_API_KEY at import time.
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import stocks, summary
from chatbot.routes import router as chatbot_router
from db.database import engine
from db.models import Base
import os

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="FinPulse API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(summary.router)
app.include_router(chatbot_router)


@app.on_event("startup")
def create_database_tables() -> None:
    """Ensure SQLite tables exist before the API receives requests."""
    # Ensure tables
    Base.metadata.create_all(bind=engine)

    # Diagnostic logs for deployment troubleshooting
    try:
        print("[startup] CWD:", os.getcwd())
        db_path = os.getenv("DATABASE_URL", "sqlite:///finpulse.db")
        print("[startup] DATABASE_URL:", db_path)
        # If using sqlite, check if the file exists (strip sqlite:///)
        if db_path.startswith("sqlite"):
            path = db_path.split("///")[-1]
            print(f"[startup] sqlite file path: {path}")
            print("[startup] file exists:", os.path.exists(path))
            try:
                print("[startup] repo listing:", os.listdir("."))
            except Exception as e:
                print("[startup] listing failed:", e)
    except Exception as e:
        print("[startup] diagnostics failed:", e)


@app.get("/")
def root():
    return {"status": "ok", "message": "FinPulse API is running"}


@app.get("/_debug/db_counts")
def debug_db_counts():
    """Return counts of key tables to help debug deployed DB state."""
    from db.database import SessionLocal
    from db.models import Company, PriceHistory

    session = SessionLocal()
    try:
        companies = session.query(Company).count()
        history = session.query(PriceHistory).count()
        return {"companies": companies, "price_history_rows": history}
    finally:
        session.close()


@app.post("/_debug/run_mock_ingest")
def run_mock_ingest():
    """Run the mock ingestion routine on demand and return row counts."""
    from db.database import SessionLocal
    from db.models import Company, PriceHistory
    from datetime import datetime, timedelta
    import random

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
        "WIPRO.NS": {"price": 425.60, "market_cap": 310000000000, "pe_ratio": 22.3, "eps": 19.1},
        "MARUTI.NS": {"price": 10750.25, "market_cap": 305000000000, "pe_ratio": 18.7, "eps": 574.6},
        "AXISBANK.NS": {"price": 1020.45, "market_cap": 295000000000, "pe_ratio": 15.2, "eps": 67.2},
        "ADANIGREEN.NS": {"price": 1870.80, "market_cap": 285000000000, "pe_ratio": 32.5, "eps": 57.5},
        "LT.NS": {"price": 3185.50, "market_cap": 270000000000, "pe_ratio": 26.8, "eps": 118.9},
        "ULTRACEMCO.NS": {"price": 9850.75, "market_cap": 265000000000, "pe_ratio": 28.3, "eps": 348.2},
        "EICHERMOT.NS": {"price": 3250.30, "market_cap": 220000000000, "pe_ratio": 21.6, "eps": 150.5},
        "POWERGRID.NS": {"price": 315.60, "market_cap": 210000000000, "pe_ratio": 19.4, "eps": 16.3},
        "GAIL.NS": {"price": 175.45, "market_cap": 125000000000, "pe_ratio": 12.1, "eps": 14.5},
        "ONGC.NS": {"price": 285.20, "market_cap": 185000000000, "pe_ratio": 10.8, "eps": 26.4},
    }

    session = SessionLocal()
    try:
        for ticker, snapshot in MOCK_COMPANIES.items():
            existing = session.query(Company).filter_by(ticker=ticker).first()
            if existing:
                continue
            
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
            
            # Add 180 days of mock history
            base_price = snapshot["price"]
            for days_back in range(180, 0, -1):
                date = datetime.now().date() - timedelta(days=days_back)
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
                base_price = close
            
            session.commit()
    except Exception as e:
        return {"status": "error", "error": f"seeder failed: {e}"}
    finally:
        session.close()

    # Return counts after seeding
    return debug_db_counts()
