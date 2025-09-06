from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Personal Expense Tracker API"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Google AI
    google_ai_api_key: str
    
    # Google Sheets
    google_service_account_json: str
    google_sheet_id: str
    worksheet_name: str = "expenses"
    
    # Default timezone
    default_timezone: str = "UTC"
    
    class Config:
        env_file = ".env"

settings = Settings()
