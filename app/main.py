from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.expenses import router as expenses_router
from app.api.auth import router as auth_router
from app.core.config import settings

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered personal expense tracker with Google Sheets integration"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(expenses_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Personal Expense Tracker API",
        "version": settings.app_version,
        "authentication": {
            "login": "/auth/login",
            "verify": "/auth/verify",
            "note": "All expense endpoints require Bearer token authentication"
        },
        "endpoints": {
            "add_expense": "/api/v1/expenses",
            "get_analytics": "/api/v1/analytics",
            "get_expenses": "/api/v1/expenses/{user_id}",
            "total_spending": "/api/v1/spending/total/{user_id}",
            "category_breakdown": "/api/v1/spending/category/{user_id}",
            "search": "/api/v1/search/{user_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "personal-expense-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug
    )
