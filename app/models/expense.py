from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORTATION = "transportation"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    SHOPPING = "shopping"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FAMILY = "family"
    TRAVEL = "travel"
    SUBSCRIPTION = "subscription"
    OTHER = "other"

class ExpenseInput(BaseModel):
    text: str
    user_id: Optional[str] = "default_user"

class ParsedExpense(BaseModel):
    timestamp: datetime
    date: date
    time: time
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
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class AnalyticsResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None
    visualization: Optional[str] = None  # base64 encoded image

class SpendingSummary(BaseModel):
    total_amount: float
    category_breakdown: dict
    time_period: str
    transaction_count: int
