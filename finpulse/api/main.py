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


@app.get("/")
def root():
    return {"status": "ok", "message": "FinPulse API is running"}
