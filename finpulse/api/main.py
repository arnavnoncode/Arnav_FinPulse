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
