# Streamlit Cloud Deployment Guide

## Prerequisites

1. **GitHub Account** - Your code must be on GitHub
2. **Streamlit Account** - Sign up at [streamlit.io](https://streamlit.io)
3. **Deployed Backend** - The FastAPI backend must be running somewhere accessible

## Step 1: Deploy the FastAPI Backend

The Streamlit dashboard requires the FastAPI backend to be running. Choose one of these options:

### Option A: Deploy to Heroku (Free tier available)
```bash
# 1. Create a Procfile in the root directory:
echo "web: uvicorn finpulse.api.main:app --host 0.0.0.0 --port \$PORT" > Procfile

# 2. Push to GitHub and connect to Heroku
# 3. Set environment variable: DATABASE_URL for production database
```

### Option B: Deploy to Railway.app (Free tier)
```bash
# 1. Connect your GitHub repo
# 2. Set start command: uvicorn finpulse.api.main:app --host 0.0.0.0 --port 8000
# 3. Add environment variables
```

### Option C: Deploy to Render.com (Free tier)
```bash
# Similar to Railway - connect repo and set start command
```

## Step 2: Deploy Streamlit Dashboard

### Via Web UI (Easiest)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub account
4. Select:
   - **Repository**: `arnavnoncode/Arnav_FinPulse`
   - **Branch**: `main`
   - **Main file path**: `app.py`

5. Click "Deploy"

### Via Streamlit CLI

```bash
streamlit login  # Authenticate with your Streamlit account

streamlit deploy \
  --repo-url https://github.com/arnavnoncode/Arnav_FinPulse \
  --repo-branch main \
  --repo-main-file-path app.py
```

## Step 3: Configure Secrets

After deployment on Streamlit Cloud:

1. Go to your app's settings
2. Click "Secrets"
3. Add the required values:
   ```toml
   API_URL = "https://your-deployed-backend.com"
   ANTHROPIC_API_KEY = "your_real_anthropic_key"
   CHATBOT_MODEL = "claude-sonnet-4-6"
   ```

Replace `your-deployed-backend.com` with your actual deployed API URL.

If you are deploying the FastAPI backend separately, set the same variables in that platform's environment settings as well.

## Step 4: Test the Deployment

1. Visit your Streamlit Cloud URL
2. Verify the dashboard loads
3. Check that data is fetching from the API
4. Test the chatbot (if backend is properly configured)

## Troubleshooting

### "Could not reach API" Error

- Verify the backend is deployed and running
- Check that `API_URL` in Streamlit secrets matches your deployed backend
- Ensure CORS is enabled on the backend (it is by default in `api/main.py`)

### Missing Database Data

- Run the ingestion pipeline on your backend:
  ```bash
  python -m finpulse.ingestion.ingest
  ```

### Port Issues

- Streamlit Cloud runs on port 8501
- Your backend should be accessible from the internet (not localhost)

## Environment Variables

The app uses these environment variables (set in Streamlit Cloud):

- `API_URL`: URL of your deployed FastAPI backend
- Optional: `ANTHROPIC_API_KEY` if chatbot needs to be enabled

## Local Testing Before Deployment

```bash
# Create .streamlit/secrets.toml locally
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit and add your backend URL
echo 'API_URL = "http://localhost:8000"' > .streamlit/secrets.toml

# Run locally
streamlit run app.py
```

## Performance Tips

1. **Caching**: The app uses `@st.cache_data` for API calls (consider adding if needed)
2. **Timeouts**: API requests have 10-15 second timeouts
3. **Database**: Use PostgreSQL/Supabase in production instead of SQLite

## Production Checklist

- [ ] Backend deployed and running
- [ ] Database populated with initial data
- [ ] Secrets configured in Streamlit Cloud
- [ ] CORS properly configured
- [ ] Error handling tested
- [ ] Chatbot tested with Anthropic API key (if used)

## More Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [FastAPI on Heroku](https://devcenter.heroku.com/articles/getting-started-with-python)
