# Personal Expense Tracker API

AI-powered personal expense tracker that parses natural language input and stores expenses in Google Sheets.

__Still work in progress. will not work yet__

## start up

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env

Edit `.env` with your actual values:
- `GOOGLE_AI_API_KEY`: Your Google AI API key
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Path to your GCP service account JSON file
- `GOOGLE_SHEET_ID`: Your Google Sheet ID

