"""
FinPulse Dashboard - Streamlit Frontend
Main entry point for Streamlit Cloud deployment.

This dashboard connects to the FastAPI backend to display:
- Stock price data and charts
- Market summaries
- Company comparisons
- AI-powered chatbot for stock queries

For local development: streamlit run app.py
For Streamlit Cloud: Deploy this repo directly
"""

import os
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def _load_runtime_secrets():
    """Load deployment secrets from Streamlit Cloud into the environment."""
    for key in ("API_URL", "ANTHROPIC_API_KEY", "CHATBOT_MODEL"):
        if os.getenv(key):
            continue
        try:
            value = st.secrets[key]
        except Exception:
            continue
        if value:
            os.environ[key] = str(value)


_load_runtime_secrets()

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="FinPulse",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 FinPulse — Stock Market Dashboard")
st.caption("Real-time tracking of 20 NSE-listed Indian companies with AI-powered insights")

# Create tabs
tab_dashboard, tab_compare, tab_chat = st.tabs(["Dashboard", "Compare", "Chat Assistant"])

# ---------- Dashboard tab ----------
with tab_dashboard:
    st.subheader("Company Overview")
    
    try:
        stocks_resp = requests.get(f"{API_URL}/stocks", timeout=10)
        stocks_resp.raise_for_status()
        stocks = stocks_resp.json()
    except Exception as e:
        st.error(f"❌ Could not reach API at {API_URL}. Please check that the backend is running. Error: {e}")
        stocks = []

    if stocks:
        tickers = [s["ticker"] for s in stocks]
        selected = st.selectbox("Select a company", tickers, key="dashboard_ticker")

        try:
            detail_resp = requests.get(f"{API_URL}/stocks/{selected}", timeout=10)
            detail = detail_resp.json()
            company = detail["company"]
            history = pd.DataFrame(detail["history"])

            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Price (₹)", f"{company['price']:,.2f}" if company['price'] else "N/A")
            with col2:
                market_cap_cr = f"{(company['market_cap'] or 0) / 1e7:,.0f}" if company["market_cap"] else "N/A"
                st.metric("Market Cap (₹ Cr)", market_cap_cr)
            with col3:
                st.metric("P/E Ratio", f"{company['pe_ratio']:.2f}" if company['pe_ratio'] else "N/A")
            with col4:
                st.metric("EPS", f"{company['eps']:.2f}" if company['eps'] else "N/A")

            # Chart
            if not history.empty:
                history["date"] = pd.to_datetime(history["date"])
                fig = go.Figure(data=[go.Candlestick(
                    x=history["date"],
                    open=history["open"],
                    high=history["high"],
                    low=history["low"],
                    close=history["close"],
                )])
                fig.update_layout(
                    title=f"{selected} — Price History",
                    xaxis_title="Date",
                    yaxis_title="Price (₹)",
                    height=500,
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 No historical data yet for this ticker. Run the ingestion pipeline to populate data.")

            # All companies table
            st.subheader("All Tracked Companies")
            st.dataframe(
                pd.DataFrame(stocks),
                use_container_width=True,
                hide_index=True
            )

            # Market summary
            try:
                summary = requests.get(f"{API_URL}/market-summary", timeout=10).json()
                st.subheader("Market Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Tracked Companies", summary.get('total_companies', 0))
                with col2:
                    avg_pe = summary.get('average_pe_ratio')
                    st.metric("Avg P/E", f"{avg_pe:.2f}" if avg_pe else "N/A")
                with col3:
                    st.metric("Top Gainer", summary.get('top_gainer', 'N/A'))
                with col4:
                    st.metric("Highest Market Cap", summary.get('highest_market_cap', 'N/A'))
            except Exception as e:
                st.warning(f"Could not fetch market summary: {e}")

        except Exception as e:
            st.error(f"Error loading company details: {e}")

    else:
        st.warning("⚠️ No companies found. The database appears empty. Run the ingestion pipeline to populate data.")

# ---------- Compare tab ----------
with tab_compare:
    st.subheader("Compare Companies")
    
    try:
        stocks_resp = requests.get(f"{API_URL}/stocks", timeout=10)
        stocks = stocks_resp.json()
    except:
        stocks = []

    if stocks:
        tickers = [s["ticker"] for s in stocks]
        col1, col2 = st.columns(2)
        
        with col1:
            ticker_a = st.selectbox("Company A", tickers, key="compare_a")
        with col2:
            ticker_b = st.selectbox("Company B", tickers, index=min(1, len(tickers)-1), key="compare_b")

        comparison_data = [s for s in stocks if s["ticker"] in (ticker_a, ticker_b)]
        
        if comparison_data:
            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True, hide_index=True)
        else:
            st.info("Select valid companies to compare.")
    else:
        st.info("📊 No data available for comparison yet.")

# ---------- Chat tab ----------
with tab_chat:
    st.subheader("FinPulse AI Assistant")
    st.caption("Ask about any tracked stock — answers use only FinPulse's own data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for role, message in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(message)

    # Chat input
    user_input = st.chat_input("Ask about stocks (e.g., 'What is the P/E ratio of RELIANCE?')")
    
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        
        with st.chat_message("user"):
            st.write(user_input)

        try:
            response = requests.post(
                f"{API_URL}/chat",
                json={"message": user_input},
                timeout=15
            )
            response.raise_for_status()
            bot_reply = response.json()["reply"]
            
            st.session_state.chat_history.append(("assistant", bot_reply))
            
            with st.chat_message("assistant"):
                st.write(bot_reply)
                
        except Exception as e:
            error_msg = f"❌ Chat error: {e}"
            st.error(error_msg)
            st.session_state.chat_history.pop()  # Remove user message on error
