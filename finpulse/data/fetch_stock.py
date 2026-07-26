"""
data/fetch_stock.py

Wraps yfinance to fetch live fundamentals and historical price data
for a single stock ticker.
"""

import random
import time

import yfinance as yf

# NOTE: yfinance 1.x talks to Yahoo over curl_cffi with browser impersonation,
# which is what Yahoo now requires - a plain requests/requests_cache session
# gets blanket HTTP 429s. So we no longer pass a custom session; yfinance
# manages its own transport, cookies/crumb, and caching internally.


def _is_rate_limit_error(err: Exception) -> bool:
    """True if the exception looks like a Yahoo 429 / rate-limit response."""
    msg = str(err).lower()
    return "too many requests" in msg or "rate limit" in msg or "429" in msg


def _with_retries(fn, *, retries: int = 8, base_delay: float = 10.0):
    """
    Call fn(), retrying on rate-limit errors with exponential backoff
    (base_delay, 2x, 4x, ...). Non-rate-limit errors are raised immediately.
    """
    for attempt in range(retries):
        try:
            return fn()
        except Exception as err:
            if not _is_rate_limit_error(err) or attempt == retries - 1:
                raise
            wait = base_delay * (2 ** attempt) + random.uniform(5, 15)
            print(f"    rate limited, backing off {wait:.0f}s "
                  f"(retry {attempt + 1}/{retries - 1})...")
            time.sleep(wait)


def get_stock_snapshot(ticker: str) -> dict:
    """
    Fetch current fundamentals for a single stock.

    Returns a dict with keys: ticker, price, market_cap, pe_ratio, eps.
    Any field yfinance doesn't have for this ticker is returned as None
    rather than raising an error.
    """
    stock = yf.Ticker(ticker)
    info = _with_retries(lambda: stock.info)

    return {
        "ticker": ticker,
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "eps": info.get("trailingEps"),
    }


def get_stock_history(ticker: str, period: str = "6mo"):
    """
    Fetch historical daily price data for a stock.

    Returns a pandas DataFrame with columns:
    Date, Open, High, Low, Close, Volume (Date as a normal column, not index).
    """
    stock = yf.Ticker(ticker)
    history = _with_retries(lambda: stock.history(period=period))
    history = history.reset_index()
    return history


if __name__ == "__main__":
    snapshot = get_stock_snapshot("RELIANCE.NS")
    print(snapshot)

    history = get_stock_history("RELIANCE.NS")
    print(history.head())
