"""
api/schemas.py

Pydantic models defining the shape of API responses.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class CompanyOut(BaseModel):
    ticker: str
    price: Optional[float]
    market_cap: Optional[int]
    pe_ratio: Optional[float]
    eps: Optional[float]
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


class PriceHistoryOut(BaseModel):
    date: date
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]

    class Config:
        from_attributes = True


class CompanyDetailOut(BaseModel):
    company: CompanyOut
    history: List[PriceHistoryOut]


class MarketSummaryOut(BaseModel):
    total_companies: int
    average_pe_ratio: Optional[float]
    top_gainer: Optional[str]
    top_loser: Optional[str]
    highest_market_cap: Optional[str]
