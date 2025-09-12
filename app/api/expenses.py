from fastapi import APIRouter, HTTPException, Depends
from app.models.expense import ExpenseInput, ExpenseResponse, AnalyticsRequest, AnalyticsResponse, ParsedExpense
from app.services.ai_service import GoogleAIService
from app.services.sheets_service import GoogleSheetsService
from app.services.analytics_service import AnalyticsService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["expenses"])

# Initialize services
ai_service = GoogleAIService()
sheets_service = GoogleSheetsService()
analytics_service = AnalyticsService()

@router.post("/expenses", response_model=ExpenseResponse)
async def add_expense(expense_input: ExpenseInput, current_user: str = Depends(get_current_user)):
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
async def get_analytics(request: AnalyticsRequest, current_user: str = Depends(get_current_user)):
    """
    Answer questions about spending patterns
    
    Examples:
    - "How much did I spend on food this month?"
    - "What's my spending by category?"
    - "Show me my monthly spending trend"
    """
    try:
        result = await analytics_service.answer_query(
            request.query, 
            request.user_id
        )
        
        return AnalyticsResponse(
            success=True,
            message=result["message"],
            data=result["data"],
            visualization=result["visualization"],
            query=result["query"],
            start_date=result["start_date"],
            end_date=result["end_date"],
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate analytics: {str(e)}"
        )

@router.get("/expenses/{user_id}")
async def get_user_expenses(
    user_id: str,
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
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
    current_user: str = Depends(get_current_user),
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
async def search_expenses(user_id: str, q: str, current_user: str = Depends(get_current_user)):
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

@router.put("/expenses/row/{row_number}")
async def update_expense_by_row(
    row_number: int, 
    expense_input: ParsedExpense, 
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing expense by row number using direct field input
    """
    try:
        # First check if the row exists
        existing_expense = await sheets_service.get_expense_by_row(row_number)
        if not existing_expense:
            raise HTTPException(
                status_code=404,
                detail=f"Expense at row {row_number} not found"
            )
        
        # Convert ParsedExpense to ParsedExpense format
        from datetime import datetime
        from app.models.expense import ParsedExpense
        
        # Set timestamp if not provided
        if expense_input.timestamp is None:
            if expense_input.date and expense_input.time:
                expense_input.timestamp = datetime.combine(expense_input.date, expense_input.time)
            else:
                expense_input.timestamp = datetime.now()
        
        # Extract date and time from timestamp
        current_date = expense_input.date or expense_input.timestamp.date()
        current_time = expense_input.time or expense_input.timestamp.time()
        
        # Create ParsedExpense object
        parsed_expense = ParsedExpense(
            timestamp=expense_input.timestamp,
            date=current_date,
            time=current_time,
            amount=expense_input.amount,
            currency=expense_input.currency,
            category=expense_input.category,
            subcategory=expense_input.subcategory,
            description=expense_input.description,
            tags=expense_input.tags,
            location=expense_input.location,
            payment_method=expense_input.payment_method,
            notes=expense_input.notes,
            user_id=expense_input.user_id
        )
        
        # Update the expense
        success = await sheets_service.update_expense(row_number, parsed_expense)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update expense at row {row_number}"
            )
        
        return {
            "success": True,
            "message": f"Expense at row {row_number} successfully updated",
            "expense": parsed_expense,
            "row_number": row_number
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update expense: {str(e)}"
        )

@router.delete("/expenses/row/{row_number}")
async def delete_expense_by_row(
    row_number: int, 
    current_user: str = Depends(get_current_user)
):
    """
    Delete an expense by row number
    """
    try:
        # First check if the row exists
        existing_expense = await sheets_service.get_expense_by_row(row_number)
        if not existing_expense:
            raise HTTPException(
                status_code=404,
                detail=f"Expense at row {row_number} not found"
            )
        
        # Delete the expense
        success = await sheets_service.delete_expense(row_number)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete expense at row {row_number}"
            )
        
        return {
            "success": True,
            "message": f"Expense at row {row_number} successfully deleted",
            "deleted_expense": existing_expense
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete expense: {str(e)}"
        )

@router.get("/expenses/row/{row_number}")
async def get_expense_by_row(
    row_number: int, 
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific expense by row number
    """
    try:
        expense = await sheets_service.get_expense_by_row(row_number)
        
        if not expense:
            raise HTTPException(
                status_code=404,
                detail=f"Expense at row {row_number} not found"
            )
        
        return {
            "success": True,
            "expense": expense
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve expense: {str(e)}"
        )
