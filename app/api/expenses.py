from fastapi import APIRouter, HTTPException
from app.models.expense import ExpenseInput, ExpenseResponse, AnalyticsRequest, AnalyticsResponse

router = APIRouter(prefix="/api/v1", tags=["expenses"])

@router.post("/expenses", response_model=ExpenseResponse)
async def add_expense(expense_input: ExpenseInput):
    """
    Parse natural language expense text and save to Google Sheets
    
    Example input: "eat banana for lunch at 12:30, paid $2.10"
    """
    return ExpenseResponse(
            success=True,
            message="Expense successfully recorded in row 1",
            expense="",
            row_number=1
        )

@router.post("/analytics", response_model=AnalyticsResponse)
async def get_analytics(request: AnalyticsRequest):
    """
    Answer questions about spending patterns
    
    Examples:
    - "How much did I spend on food this month?"
    - "What's my spending by category?"
    - "Show me my monthly spending trend"
    """
    try:
        return AnalyticsResponse(
            success=True,
            message="Example",
            data="data",
            visualization="vistual"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics: {str(e)}"
        )

@router.get("/expenses/{user_id}")
async def get_user_expenses(
    user_id: str,
    start_date: str = None,
    end_date: str = None,
    category: str = None
):
    """
    Get all expenses for a user with optional filtering
    """
    expenses = list()
    return {
        "success": True,
        "count": len(expenses),
        "expenses": expenses
    }
    

@router.get("/spending/total/{user_id}")
async def get_total_spending(
    user_id: str,
    start_date: str = None,
    end_date: str = None
):
    """
    Get total spending for a user
    """
    try:
        return {
            "success": True,
            "user_id": user_id,
            "total_spending": 100,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate total spending: {str(e)}"
        )

@router.get("/spending/category/{user_id}")
async def get_spending_by_category(
    user_id: str,
    start_date: str = None,
    end_date: str = None
):
    """
    Get spending breakdown by category
    """
    try:
        return {
            "success": True,
            "user_id": user_id,
            "category_breakdown": "food",
            "total": 100,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get category breakdown: {str(e)}"
        )

@router.get("/search/{user_id}")
async def search_expenses(user_id: str, q: str):
    """
    Search expenses by description, category, or tags
    """
    try:
        return {
            "success": True,
            "query": q,
            "count": 1,
            "results": []
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search expenses: {str(e)}"
        )
