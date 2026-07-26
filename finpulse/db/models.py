"""
db/models.py

Two tables:
- Company: one row per company, holds the latest fundamentals snapshot.
  Updated in place every time ingestion runs.
- PriceHistory: one row per company per trading day. Appended over time,
  used to render historical price charts.
"""

from sqlalchemy import Column, Integer, String, Float, BigInteger, Date, DateTime, UniqueConstraint
from db.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, unique=True, nullable=False, index=True)
    price = Column(Float, nullable=True)
    market_cap = Column(BigInteger, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    eps = Column(Float, nullable=True)
    last_updated = Column(DateTime, nullable=True)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)

    __table_args__ = (UniqueConstraint("ticker", "date", name="uq_ticker_date"),)


if __name__ == "__main__":
    from db.database import engine
    Base.metadata.create_all(engine)
    print("Tables created successfully.")
