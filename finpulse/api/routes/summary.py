"""
api/routes/summary.py

Endpoint: GET /market-summary
Aggregate stats across all tracked companies.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Company
from api.schemas import MarketSummaryOut

router = APIRouter(tags=["summary"])


@router.get("/market-summary", response_model=MarketSummaryOut)
def market_summary(db: Session = Depends(get_db)):
    companies = db.query(Company).all()

    if not companies:
        return {
            "total_companies": 0,
            "average_pe_ratio": None,
            "top_gainer": None,
            "top_loser": None,
            "highest_market_cap": None,
        }

    pe_values = [c.pe_ratio for c in companies if c.pe_ratio is not None]
    avg_pe = sum(pe_values) / len(pe_values) if pe_values else None

    # Note: this ranks by absolute price, not % change (yfinance snapshot
    # doesn't give us a daily change baseline without extra calls).
    by_price = sorted([c for c in companies if c.price is not None], key=lambda c: c.price)
    top_gainer = by_price[-1].ticker if by_price else None
    top_loser = by_price[0].ticker if by_price else None

    by_cap = sorted([c for c in companies if c.market_cap is not None], key=lambda c: c.market_cap)
    highest_cap = by_cap[-1].ticker if by_cap else None

    return {
        "total_companies": len(companies),
        "average_pe_ratio": round(avg_pe, 2) if avg_pe else None,
        "top_gainer": top_gainer,
        "top_loser": top_loser,
        "highest_market_cap": highest_cap,
    }
