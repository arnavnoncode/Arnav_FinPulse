"""
db/database.py

Sets up the database engine, session factory, and declarative base.
Uses SQLite by default (zero config). Set DATABASE_URL env var to switch
to Postgres/Supabase later without changing any other code.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env before any os.getenv call below (or in modules that import this one).
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///finpulse.db")

# check_same_thread=False is only needed for SQLite when used with FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
