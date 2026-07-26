"""
chatbot/tools.py

LangChain tools the agent can call to answer questions using FinPulse's
own database — not the open web. Each tool queries the DB directly and
returns a short, structured string (not raw rows) so the LLM has less
to summarize, which keeps final answers short.
"""

from langchain_core.tools import tool
from db.database import SessionLocal
from db.models import Company, PriceHistory


@tool
def get_company_snapshot(ticker: str) -> str:
    """Get the latest price, market cap, P/E ratio, and EPS for a given
    NSE ticker (e.g. 'RELIANCE.NS' or just 'RELIANCE')."""
    ticker = ticker.upper().strip()
    if not ticker.endswith(".NS"):
        ticker += ".NS"

    session = SessionLocal()
    try:
        company = session.query(Company).filter_by(ticker=ticker).first()
        if not company:
            return f"No data found for {ticker}."
        return (
            f"{company.ticker}: price=₹{company.price}, "
            f"market_cap=₹{company.market_cap}, "
            f"pe_ratio={company.pe_ratio}, eps={company.eps}"
        )
    finally:
        session.close()


@tool
def compare_companies(ticker_a: str, ticker_b: str) -> str:
    """Compare two companies' price, market cap, P/E ratio, and EPS side by side."""
    session = SessionLocal()
    try:
        results = []
        for t in (ticker_a, ticker_b):
            t = t.upper().strip()
            if not t.endswith(".NS"):
                t += ".NS"
            company = session.query(Company).filter_by(ticker=t).first()
            if company:
                results.append(
                    f"{company.ticker}: price=₹{company.price}, "
                    f"market_cap=₹{company.market_cap}, pe={company.pe_ratio}, eps={company.eps}"
                )
            else:
                results.append(f"{t}: no data")
        return " | ".join(results)
    finally:
        session.close()


@tool
def get_market_summary() -> str:
    """Get an overall market summary: number of companies tracked,
    average P/E ratio, and the company with the highest market cap."""
    session = SessionLocal()
    try:
        companies = session.query(Company).all()
        if not companies:
            return "No market data available yet."

        pe_values = [c.pe_ratio for c in companies if c.pe_ratio is not None]
        avg_pe = sum(pe_values) / len(pe_values) if pe_values else None

        by_cap = sorted([c for c in companies if c.market_cap is not None], key=lambda c: c.market_cap)
        highest_cap = by_cap[-1].ticker if by_cap else "N/A"

        return (
            f"Tracking {len(companies)} companies. "
            f"Average P/E ratio: {round(avg_pe, 2) if avg_pe else 'N/A'}. "
            f"Highest market cap: {highest_cap}."
        )
    finally:
        session.close()


@tool
def get_price_trend(ticker: str) -> str:
    """Get the recent price trend (first vs latest close in stored history)
    for a given ticker, to describe if it has gone up or down recently."""
    ticker = ticker.upper().strip()
    if not ticker.endswith(".NS"):
        ticker += ".NS"

    session = SessionLocal()
    try:
        rows = (
            session.query(PriceHistory)
            .filter_by(ticker=ticker)
            .order_by(PriceHistory.date)
            .all()
        )
        if not rows:
            return f"No price history for {ticker}."

        first, last = rows[0], rows[-1]
        change_pct = ((last.close - first.close) / first.close) * 100 if first.close else None
        direction = "up" if change_pct and change_pct > 0 else "down"
        return (
            f"{ticker} moved from ₹{first.close} on {first.date} to "
            f"₹{last.close} on {last.date} ({direction} {abs(round(change_pct, 2)) if change_pct else '?'}%)."
        )
    finally:
        session.close()


ALL_TOOLS = [get_company_snapshot, compare_companies, get_market_summary, get_price_trend]
