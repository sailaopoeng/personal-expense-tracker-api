import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import base64
import io
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from app.services.sheets_service import GoogleSheetsService

class AnalyticsService:
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
    
    async def answer_query(self, query: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Answer user queries about spending patterns
        """
        query_lower = query.lower()
        
        # Determine time range based on query
        start_date, end_date = self._parse_time_range(query_lower)
        
        # Determine what type of analysis to perform
        if any(word in query_lower for word in ['category', 'categories', 'what', 'where']):
            return await self._category_analysis(user_id, start_date, end_date)
        
        elif any(word in query_lower for word in ['month', 'monthly']):
            return await self._monthly_analysis(user_id, start_date, end_date)
        
        elif any(word in query_lower for word in ['week', 'weekly']):
            return await self._weekly_analysis(user_id, start_date, end_date)
        
        elif any(word in query_lower for word in ['year', 'yearly', 'annual']):
            return await self._yearly_analysis(user_id, start_date, end_date)
        
        elif any(word in query_lower for word in ['total', 'how much', 'spent']):
            return await self._total_spending_analysis(user_id, start_date, end_date)
        
        elif any(word in query_lower for word in ['trend', 'pattern', 'over time']):
            return await self._trend_analysis(user_id, start_date, end_date)
        
        else:
            # Default to category breakdown
            return await self._category_analysis(user_id, start_date, end_date)
    
    def _parse_time_range(self, query: str) -> tuple[Optional[date], Optional[date]]:
        """Parse time range from query"""
        today = date.today()
        
        if 'this month' in query:
            start_date = today.replace(day=1)
            return start_date, today
        
        elif 'last month' in query:
            if today.month == 1:
                start_date = date(today.year - 1, 12, 1)
                end_date = date(today.year - 1, 12, 31)
            else:
                start_date = date(today.year, today.month - 1, 1)
                # Get last day of previous month
                end_date = today.replace(day=1) - timedelta(days=1)
            return start_date, end_date
        
        elif 'this week' in query:
            days_since_monday = today.weekday()
            start_date = today - timedelta(days=days_since_monday)
            return start_date, today
        
        elif 'last week' in query:
            days_since_monday = today.weekday()
            end_date = today - timedelta(days=days_since_monday + 1)
            start_date = end_date - timedelta(days=6)
            return start_date, end_date
        
        elif 'this year' in query:
            start_date = date(today.year, 1, 1)
            return start_date, today
        
        elif 'last year' in query:
            start_date = date(today.year - 1, 1, 1)
            end_date = date(today.year - 1, 12, 31)
            return start_date, end_date
        
        elif 'last 30 days' in query or 'past month' in query:
            start_date = today - timedelta(days=30)
            return start_date, today
        
        elif 'last 7 days' in query or 'past week' in query:
            start_date = today - timedelta(days=7)
            return start_date, today
        
        # Default: no time filter
        return None, None
    
    async def _category_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
        """Analyze spending by category"""
        category_spending = await self.sheets_service.get_spending_by_category(
            user_id, start_date, end_date
        )
        
        if not category_spending:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Create pie chart
        fig = px.pie(
            values=list(category_spending.values()),
            names=list(category_spending.keys()),
            title="Spending by Category"
        )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        total_spending = sum(category_spending.values())
        
        return {
            "message": f"Spending breakdown by category. Total: ${total_spending:.2f}",
            "data": {
                "category_breakdown": category_spending,
                "total": total_spending
            },
            "visualization": img_base64
        }
    
    async def _monthly_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
        """Analyze monthly spending patterns"""
        monthly_spending = await self.sheets_service.get_spending_by_time_period(
            user_id, "month", start_date, end_date
        )
        
        if not monthly_spending:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Create bar chart
        fig = px.bar(
            x=list(monthly_spending.keys()),
            y=list(monthly_spending.values()),
            title="Monthly Spending",
            labels={'x': 'Month', 'y': 'Amount ($)'}
        )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return {
            "message": "Monthly spending analysis",
            "data": {
                "monthly_breakdown": monthly_spending,
                "average_monthly": sum(monthly_spending.values()) / len(monthly_spending)
            },
            "visualization": img_base64
        }
    
    async def _weekly_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
        """Analyze weekly spending patterns"""
        weekly_spending = await self.sheets_service.get_spending_by_time_period(
            user_id, "week", start_date, end_date
        )
        
        if not weekly_spending:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Create line chart
        fig = px.line(
            x=list(weekly_spending.keys()),
            y=list(weekly_spending.values()),
            title="Weekly Spending Trend",
            labels={'x': 'Week', 'y': 'Amount ($)'}
        )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return {
            "message": "Weekly spending analysis",
            "data": {
                "weekly_breakdown": weekly_spending,
                "average_weekly": sum(weekly_spending.values()) / len(weekly_spending)
            },
            "visualization": img_base64
        }
    
    async def _yearly_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
        """Analyze yearly spending patterns"""
        yearly_spending = await self.sheets_service.get_spending_by_time_period(
            user_id, "year", start_date, end_date
        )
        
        if not yearly_spending:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Create bar chart
        fig = px.bar(
            x=list(yearly_spending.keys()),
            y=list(yearly_spending.values()),
            title="Yearly Spending",
            labels={'x': 'Year', 'y': 'Amount ($)'}
        )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return {
            "message": "Yearly spending analysis",
            "data": {
                "yearly_breakdown": yearly_spending,
                "average_yearly": sum(yearly_spending.values()) / len(yearly_spending)
            },
            "visualization": img_base64
        }
    
    async def _total_spending_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
        """Analyze total spending"""
        total = await self.sheets_service.get_total_spending(user_id, start_date, end_date)
        expenses = await self.sheets_service.get_expenses(user_id, start_date, end_date)
        
        period = "all time"
        if start_date and end_date:
            period = f"from {start_date} to {end_date}"
        elif start_date:
            period = f"since {start_date}"
        elif end_date:
            period = f"until {end_date}"
        
        return {
            "message": f"Total spending {period}: ${total:.2f}",
            "data": {
                "total_amount": total,
                "transaction_count": len(expenses),
                "average_per_transaction": total / len(expenses) if expenses else 0
            },
            "visualization": None
        }
    
    async def _trend_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date]) -> Dict[str, Any]:
        """Analyze spending trends over time"""
        daily_spending = await self.sheets_service.get_spending_by_time_period(
            user_id, "day", start_date, end_date
        )
        
        if not daily_spending:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Create line chart for trend
        fig = px.line(
            x=list(daily_spending.keys()),
            y=list(daily_spending.values()),
            title="Daily Spending Trend",
            labels={'x': 'Date', 'y': 'Amount ($)'}
        )
        
        # Add trend line
        dates = list(daily_spending.keys())
        amounts = list(daily_spending.values())
        
        # Calculate simple moving average
        if len(amounts) >= 7:
            ma_7 = []
            for i in range(6, len(amounts)):
                ma_7.append(sum(amounts[i-6:i+1]) / 7)
            
            fig.add_trace(go.Scatter(
                x=dates[6:],
                y=ma_7,
                name="7-day Moving Average",
                line=dict(color='red', width=2)
            ))
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return {
            "message": "Spending trend analysis",
            "data": {
                "daily_breakdown": daily_spending,
                "total_days": len(daily_spending),
                "average_daily": sum(daily_spending.values()) / len(daily_spending)
            },
            "visualization": img_base64
        }
