# FinPulse

FinPulse is a stock market monitoring platform for 20 NSE-listed Indian companies. It includes:

- A **FastAPI** backend serving company snapshots, price history, and market summary data.
- A **Streamlit** dashboard displaying charts, comparisons, and an in-app assistant.
- A **LangGraph/Anthropic** chatbot that answers questions using the app's own stock data.
- A **SQLite** database with two tables: `companies` and `price_history`.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Local Development](#local-development)
- [Deployment](#deployment)
- [API Endpoints](#api-endpoints)
- [Dashboard](#dashboard)
- [Chatbot](#chatbot)
- [Data Ingestion](#data-ingestion)
- [Debugging](#debugging)
- [Implementation Details](#implementation-details)
- [Future Improvements](#future-improvements)

---

## Architecture

FinPulse is built as a decoupled application with three main layers:

1. **Data ingestion layer**
   - Fetches market data using Yahoo Finance via `yfinance`.
   - Writes latest company snapshots to `companies`.
   - Appends daily OHLCV rows to `price_history`.

2. **Backend layer**
   - `FastAPI` app exposes REST endpoints.
   - Uses `SQLAlchemy` with SQLite by default.
   - Includes separate routers for stocks, summaries, and chatbot routes.

3. **Frontend layer**
   - `Streamlit` dashboard consumes the backend API.
   - Displays charts, summaries, comparisons, and chat interaction.

The chatbot uses a LangGraph agent and calls tools that query the database directly.

---

## Project Structure

```
README.md
requirements.txt
app.py                   # Streamlit deployment entrypoint
finpulse/
  api/
    main.py
    schemas.py
    routes/
      stocks.py
      summary.py
  chatbot/
    agent.py
    routes.py
    tools.py
  data/
    fetch_stock.py
  db/
    database.py
    models.py
  ingestion/
    companies.py
    ingest.py
  dashboard/
    app.py
```

### Key components

- `finpulse/db/models.py`
  - `Company`: current snapshot of each tracked company.
  - `PriceHistory`: historical daily OHLCV rows by ticker and date.

- `finpulse/db/database.py`
  - SQLAlchemy engine and session setup.
  - Reads `DATABASE_URL` from the environment.

- `finpulse/ingestion/ingest.py`
  - Orchestrates data fetch and database writes.
  - Uses ticker list from `finpulse/ingestion/companies.py`.

- `finpulse/api/main.py`
  - Application entrypoint and router registration.
  - Includes startup table creation and debug endpoints.

- `finpulse/dashboard/app.py` and `app.py`
  - Streamlit dashboards for local and deployed usage.

- `finpulse/chatbot/agent.py`
  - LangGraph ReAct agent with tool-based DB queries.

---

## Setup

1. Create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment variables:

```bash
cp .env.example .env
```

4. Add your Anthropic API key to `.env` if chatbot functionality is required:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

5. If you use Streamlit Cloud, configure `API_URL` in Streamlit secrets.

---

## Local Development

### Create database tables

```bash
python -m finpulse.db.models
```

### Run ingestion

```bash
python -m finpulse.ingestion.ingest
```

This populates `finpulse.db` using the tracked tickers. The app also supports a mock seeder endpoint in `finpulse/api/main.py`.

### Run the API

```bash
uvicorn finpulse.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Run the Streamlit dashboard locally

```bash
streamlit run finpulse/dashboard/app.py
```

Default local apps:

- Streamlit dashboard: `http://localhost:8501`
- FastAPI docs: `http://localhost:8000/docs`

---

## Deployment

### Render backend

The backend can be deployed on Render with `python -m finpulse.ingestion.mock_ingest` or via the built-in `/debug/run_mock_ingest` endpoint.

### Streamlit frontend

The deployed dashboard reads `API_URL` from Streamlit secrets or environment variables.

### Recommended deployment flow

1. Deploy backend.
2. Ensure the backend is reachable.
3. Seed the database using the debug endpoint:

```bash
curl -s -X POST https://your-backend-url/_debug/run_mock_ingest
```

4. Point Streamlit app at the backend via `API_URL`.

---

## API Endpoints

### `GET /stocks`

Returns the tracked company snapshot list.

### `GET /stocks/{ticker}`

Returns a single company snapshot plus historical price data.

### `GET /market-summary`

Returns aggregated metrics:

- `total_companies`
- `average_pe_ratio`
- `top_gainer`
- `top_loser`
- `highest_market_cap`

### `POST /_debug/run_mock_ingest`

Seeds mock data for 20 companies and returns row counts.

### `GET /_debug/db_counts`

Returns counts of the `companies` and `price_history` tables.

---

## Dashboard

The Streamlit dashboard provides:

- Company selection dropdown
- Financial metrics (price, market cap, P/E, EPS)
- Candlestick price chart
- Full list of tracked companies
- Market summary metrics
- Comparison tab for side-by-side ticker comparison
- Chat assistant tab for natural language queries

---

## Chatbot

The chatbot is implemented using a LangGraph agent that:

- uses DB-backed tools in `finpulse/chatbot/tools.py`
- answers questions from internal stock data only
- does not search the open web
- returns short, concise responses

The chatbot route is exposed at `POST /chat`.

---

## Data Ingestion

### Primary ingestion

- The ingestion pipeline uses `yfinance` to fetch stock data.
- Latest metadata is stored in `companies`.
- Historical OHLCV rows are stored in `price_history`.
- The pipeline is designed to avoid duplicate rows with a unique constraint.

### Mock seeding

To avoid rate-limit issues during development or deployment, a mock seeder can populate 20 companies with realistic synthetic history.

---

## Implementation Notes

- `finpulse/db/database.py` builds the SQLAlchemy engine from `DATABASE_URL`.
- `sqlite:///finpulse.db` is the default local database URL.
- The FastAPI startup event ensures tables are created automatically.
- The Streamlit app fetches from the backend rather than reading the DB directly.
- The frontend and chatbot are intentionally separated from direct DB access.

---

## Troubleshooting

- If `/stocks` returns an empty list, run `/debug/run_mock_ingest` or `python -m finpulse.ingestion.ingest`.
- If the dashboard shows a fetch error, verify `API_URL` is correct and reachable.
- If the chatbot fails, ensure `ANTHROPIC_API_KEY` is set and valid.

---

## Future Improvements

- Replace SQLite with Postgres or Supabase for persistence.
- Add scheduled ingestion using a cron job or scheduler.
- Add authentication and per-user watchlists.
- Expand the chatbot with sector-level comparisons and richer trading insights.

---

## License

Use this project for learning and prototyping. Adjust licensing as needed for production deployments.
