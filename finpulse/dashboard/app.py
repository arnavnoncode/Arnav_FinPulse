"""
dashboard/app.py

Streamlit dashboard for FinPulse. Talks ONLY to the FastAPI backend
(never touches the DB directly) so the API layer is genuinely exercised.

Run with: streamlit run dashboard/app.py
Requires the API to be running (uvicorn api.main:app --reload).
"""

import os
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="FinPulse", layout="wide")
st.title("📈 FinPulse — Stock Market Dashboard")

tab_dashboard, tab_compare, tab_chat = st.tabs(["Dashboard", "Compare", "Chat Assistant"])

# ---------- Dashboard tab ----------
with tab_dashboard:
    try:
        stocks_resp = requests.get(f"{API_URL}/stocks", timeout=10)
        stocks_resp.raise_for_status()
        stocks = stocks_resp.json()
    except Exception as e:
        st.error(f"Could not reach API at {API_URL}. Is it running? ({e})")
        stocks = []

    if stocks:
        tickers = [s["ticker"] for s in stocks]
        selected = st.selectbox("Select a company", tickers)

        detail_resp = requests.get(f"{API_URL}/stocks/{selected}", timeout=10)
        detail = detail_resp.json()
        company = detail["company"]
        history = pd.DataFrame(detail["history"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Price (₹)", company["price"])
        col2.metric("Market Cap (₹ Cr)", f"{(company['market_cap'] or 0) / 1e7:,.0f}" if company["market_cap"] else "N/A")
        col3.metric("P/E Ratio", company["pe_ratio"])
        col4.metric("EPS", company["eps"])

        if not history.empty:
            history["date"] = pd.to_datetime(history["date"])
            fig = go.Figure(data=[go.Candlestick(
                x=history["date"],
                open=history["open"],
                high=history["high"],
                low=history["low"],
                close=history["close"],
            )])
            fig.update_layout(title=f"{selected} — Price History", xaxis_title="Date", yaxis_title="Price (₹)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No historical data yet for this ticker — run ingestion first.")

        st.subheader("All Tracked Companies")
        st.dataframe(pd.DataFrame(stocks), use_container_width=True)

        try:
            summary = requests.get(f"{API_URL}/market-summary", timeout=10).json()
            st.subheader("Market Summary")
            st.json(summary)
        except Exception:
            pass
    else:
        st.warning("No companies found. Run `python -m ingestion.ingest` first to populate the database.")

# ---------- Compare tab ----------
with tab_compare:
    if stocks:
        tickers = [s["ticker"] for s in stocks]
        c1, c2 = st.columns(2)
        ticker_a = c1.selectbox("Company A", tickers, key="cmp_a")
        ticker_b = c2.selectbox("Company B", tickers, index=min(1, len(tickers) - 1), key="cmp_b")

        rows = [s for s in stocks if s["ticker"] in (ticker_a, ticker_b)]
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No data to compare yet.")

# ---------- Chat tab ----------
with tab_chat:
    st.caption("Ask about any tracked stock — answers are kept short and only use FinPulse's own data.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    user_input = st.chat_input("e.g. What's TCS's P/E ratio?")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        with st.chat_message("user"):
            st.write(user_input)

        try:
            resp = requests.post(f"{API_URL}/chat", json={"message": user_input}, timeout=30)
            resp.raise_for_status()
            reply = resp.json()["reply"]
        except Exception as e:
            reply = f"Chatbot error: {e}"

        st.session_state.chat_history.append(("assistant", reply))
        with st.chat_message("assistant"):
            st.write(reply)
