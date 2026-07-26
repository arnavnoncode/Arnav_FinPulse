"""
api/routes/stocks.py

Endpoints:
- GET /stocks              -> list of all tracked companies (latest snapshot)
- GET /stocks/{ticker}     -> one company's snapshot + its price history
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Company, PriceHistory
from api.schemas import CompanyOut, CompanyDetailOut

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[CompanyOut])
def list_stocks(db: Session = Depends(get_db)):
    companies = db.query(Company).order_by(Company.ticker).all()
    return companies


@router.get("/{ticker}", response_model=CompanyDetailOut)
def get_stock(ticker: str, db: Session = Depends(get_db)):
    company = db.query(Company).filter_by(ticker=ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

    history = (
        db.query(PriceHistory)
        .filter_by(ticker=ticker.upper())
        .order_by(PriceHistory.date)
        .all()
    )

    return {"company": company, "history": history}
