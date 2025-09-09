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
```

Edit `.env` with your actual values:
- `GOOGLE_AI_API_KEY`: Your Google AI API key
- `GOOGLE_SERVICE_ACCOUNT_JSON`: Path to your GCP service account JSON file
- `GOOGLE_SHEET_ID`: Your Google Sheet ID
- `STATIC_PASSWORD`: Your static Password to authenticate the api calls
- `JWT_SECRET_KEY`: Your Secret Key for JWT signature

### 3. Setup Google Cloud Platform

1. **Create a GCP Project** and enable the following APIs:
   - Google Sheets API
   - Google Drive API

2. **Create a Service Account**:
   - Go to IAM & Admin → Service Accounts
   - Create a new service account
   - Download the JSON key file
   - Place it in your project directory and update the path in `.env`

3. **Setup Google Sheets**:
   - Create a new Google Sheet
   - Share it with your service account email (found in the JSON file)
   - Copy the Sheet ID from the URL and add it to `.env`

### 4. Get Google AI API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

### 5. Run the Application

```bash
# From the project root
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Documentation

- **[Interactive API Docs](http://localhost:8000/docs)** - Swagger/OpenAPI documentation (when server is running)

## API Usage

### Add an Expense

```bash
curl -X POST "http://localhost:8000/api/v1/expenses" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "text": "eat banana lunch at $3.5 at 12:30",
    "user_id": "john_doe"
  }'
```

### Get Analytics

```bash
curl -X POST "http://localhost:8000/api/v1/analytics" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "query": "How much did I spend on food this month?",
    "user_id": "john_doe"
  }'
```

### Get All Expenses

```bash
curl "http://localhost:8000/api/v1/expenses/john_doe?start_date=2024-01-01&category=food"
```


## Example Natural Language Inputs

The AI can parse various natural language formats:

- "eat banana lunch at $3.5 at 12:30"
- "Bought coffee for $4.50 this morning"
- "Uber ride to downtown $15.75"
- "Grocery shopping at Walmart $67.89"
- "Netflix subscription $15.99 monthly"
- "Gas station fill up $45.20 yesterday"

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate with static password and get access token |
| POST | `/auth/verify` | Verify if a token is valid |
| POST | `/api/v1/expenses` | Add a new expense |
| POST | `/api/v1/analytics` | Get spending analytics |
| GET | `/api/v1/expenses/{user_id}` | Get user expenses |
| GET | `/api/v1/spending/total/{user_id}` | Get total spending |
| GET | `/api/v1/spending/category/{user_id}` | Get spending by category |
| GET | `/api/v1/search/{user_id}?q=query` | Search expenses |
| GET | `/docs` | Interactive API documentation |

## Expense Categories

The system automatically categorizes expenses into:
- Food
- Transportation
- Entertainment
- Utilities
- Shopping
- Groceries
- Healthcare
- Education
- Travel
- Subscription
- Family
- Other

## Analytics Queries

You can ask questions like:
- "How much did I spend this month?"
- "What's my spending by category?"
- "Show me my weekly spending trend"
- "How much did I spend on food last month?"
- "What's my average daily spending?"

## 📁 Project Structure

```
personal-expense-tracker-api/
├── app/                          # Main application
│   ├── api/                      # API endpoints
│   │   |── auth.py               # Authentication-related endpoints
│   │   └── expenses.py           # Expense-related endpoints
│   ├── core/                     # Core configuration
│   │   |── config.py             # Settings and configuration
│   │   └── dependencies.py       # Helper to authentication
│   ├── models/                   # Pydantic models
│   │   |── auth.py               # Auth models
│   │   └── expense.py            # Data models
│   ├── services/                 # Business logic
│   │   ├── ai_service.py         # Google AI integration
│   │   |── analytics_service.py  # Analytics and visualizations
│   │   ├── auth_service.py       # Authentication services
│   │   └── sheets_service.py     # Google Sheets integration
│   └── main.py                   # FastAPI application
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## 📄 License

This project is licensed under the MIT License.