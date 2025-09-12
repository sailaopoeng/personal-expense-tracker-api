from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date as date_type, time as time_type
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORTATION = "transportation"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SHOPPING = "shopping"
    GROCERIES = "groceries"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    TRAVEL = "travel"
    SUBSCRIPTION = "subscription"
    FAMILY = "family"
    OTHER = "other"

class ExpenseInput(BaseModel):
    text: str
    user_id: Optional[str] = "default_user"

class ParsedExpense(BaseModel):
    timestamp: datetime
    date: date_type
    time: time_type
    amount: float
    currency: str = "SGD"
    category: ExpenseCategory
    subcategory: Optional[str] = None
    description: str
    tags: List[str] = []
    location: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    user_id: str = "default_user"

class ExpenseResponse(BaseModel):
    success: bool
    message: str
    expense: Optional[ParsedExpense] = None
    row_number: Optional[int] = None

class AnalyticsRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default_user"
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None

class AnalyticsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    visualization: Optional[str] = None  # base64 encoded image
    query: Optional[str] = None
    start_date: Optional[date_type] = None
    end_date: Optional[date_type] = None

class SpendingSummary(BaseModel):
    total_amount: float
    category_breakdown: dict
    time_period: str
    transaction_count: int
