from fastapi import APIRouter, HTTPException
from app.models.expense import ExpenseInput, ExpenseResponse, AnalyticsRequest, AnalyticsResponse
from app.services.ai_service import GoogleAIService
from app.services.sheets_service import GoogleSheetsService

router = APIRouter(prefix="/api/v1", tags=["expenses"])

# Initialize services
ai_service = GoogleAIService()
sheets_service = GoogleSheetsService()

@router.post("/expenses", response_model=ExpenseResponse)
async def add_expense(expense_input: ExpenseInput):
    """
    Parse natural language expense text and save to Google Sheets
    
    Example input: "eat banana lunch at $3.5 at 12:30"
    """
    try:
        # Parse the expense using AI
        parsed_expense = await ai_service.parse_expense_text(expense_input.text)
        parsed_expense.user_id = expense_input.user_id
        
        # Save to Google Sheets
        row_number = await sheets_service.add_expense(parsed_expense)
        
        return ExpenseResponse(
            success=True,
            message=f"Expense successfully recorded in row {row_number}",
            expense=parsed_expense,
            row_number=row_number
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process expense: {str(e)}"
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
            message="Dummy",
            data=[],
            visualization="dummy"
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
    try:
        from datetime import datetime
        
        # Parse dates if provided
        start_date_obj = datetime.fromisoformat(start_date).date() if start_date else None
        end_date_obj = datetime.fromisoformat(end_date).date() if end_date else None
        
        expenses = await sheets_service.get_expenses(
            user_id=user_id,
            start_date=start_date_obj,
            end_date=end_date_obj,
            category=category
        )
        
        return {
            "success": True,
            "count": len(expenses),
            "expenses": expenses
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve expenses: {str(e)}"
        )

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
        from datetime import datetime
        
        start_date_obj = datetime.fromisoformat(start_date).date() if start_date else None
        end_date_obj = datetime.fromisoformat(end_date).date() if end_date else None
        
        total = await sheets_service.get_total_spending(
            user_id=user_id,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "total_spending": total,
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
        from datetime import datetime
        
        start_date_obj = datetime.fromisoformat(start_date).date() if start_date else None
        end_date_obj = datetime.fromisoformat(end_date).date() if end_date else None
        
        category_spending = await sheets_service.get_spending_by_category(
            user_id=user_id,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "category_breakdown": category_spending,
            "total": sum(category_spending.values()),
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
        results = await sheets_service.search_expenses(q, user_id)
        
        return {
            "success": True,
            "query": q,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search expenses: {str(e)}"
        )
