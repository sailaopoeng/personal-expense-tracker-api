import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import base64
import io
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from app.services.sheets_service import GoogleSheetsService
from app.services.ai_service import GoogleAIService

class AnalyticsService:
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.ai_service = GoogleAIService()
    
    async def answer_query(self, query: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Answer user queries about spending patterns using AI-powered parsing
        """
        # Parse query using AI to understand intent and requirements
        parsed_query = await self.ai_service.parse_analytics_query(query)
        
        # Route to appropriate analysis based on AI parsing results
        if parsed_query["analysis_type"] == "comparison":
            result = await self._handle_comparison_analysis(parsed_query, user_id)
        elif parsed_query["analysis_type"] == "trend":
            result = await self._handle_trend_analysis(parsed_query, user_id)
        elif parsed_query["analysis_type"] == "category_breakdown":
            result = await self._handle_category_analysis(parsed_query, user_id)
        elif parsed_query["analysis_type"] == "total":
            result = await self._handle_total_analysis(parsed_query, user_id)
        elif parsed_query["analysis_type"] == "period_analysis":
            result = await self._handle_period_analysis(parsed_query, user_id)
        else:
            # Default to category breakdown
            result = await self._handle_category_analysis(parsed_query, user_id)
        
        # Add query metadata to the result
        result["query"] = query
        result["parsed_intent"] = parsed_query
        result["start_date"] = None
        result["end_date"] = None
        
        # Extract date range from time periods if available
        if parsed_query.get("time_periods") and len(parsed_query["time_periods"]) > 0:
            first_period = parsed_query["time_periods"][0]
            result["start_date"] = first_period.get("start_date")
            result["end_date"] = first_period.get("end_date")
        
        return result
    
    async def _handle_comparison_analysis(self, parsed_query: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle comparison-based analysis"""
        comparison_type = parsed_query.get("comparison_type")
        time_periods = parsed_query.get("time_periods", [])
        
        if comparison_type == "time_periods" and len(time_periods) >= 2:
            return await self._compare_time_periods(time_periods, user_id, parsed_query)
        elif comparison_type == "categories_over_time":
            return await self._compare_categories_over_time(time_periods, parsed_query.get("categories"), user_id, parsed_query)
        else:
            # Fallback to regular period analysis
            return await self._handle_period_analysis(parsed_query, user_id)
    
    async def _handle_trend_analysis(self, parsed_query: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle trend analysis"""
        time_periods = parsed_query.get("time_periods", [])
        granularity = parsed_query.get("granularity", "day")
        
        if time_periods:
            period = time_periods[0]
            start_date = self._parse_date(period.get("start_date"))
            end_date = self._parse_date(period.get("end_date"))
        else:
            start_date, end_date = None, None
        
        return await self._trend_analysis(user_id, start_date, end_date, granularity)
    
    async def _handle_category_analysis(self, parsed_query: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle category breakdown analysis"""
        time_periods = parsed_query.get("time_periods", [])
        categories = parsed_query.get("categories")
        
        if time_periods:
            period = time_periods[0]
            start_date = self._parse_date(period.get("start_date"))
            end_date = self._parse_date(period.get("end_date"))
        else:
            start_date, end_date = None, None
        
        return await self._category_analysis(user_id, start_date, end_date, categories)
    
    async def _handle_total_analysis(self, parsed_query: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle total spending analysis"""
        time_periods = parsed_query.get("time_periods", [])
        categories = parsed_query.get("categories")
        
        if time_periods:
            period = time_periods[0]
            start_date = self._parse_date(period.get("start_date"))
            end_date = self._parse_date(period.get("end_date"))
        else:
            start_date, end_date = None, None
        
        return await self._total_spending_analysis(user_id, start_date, end_date, categories)
    
    async def _handle_period_analysis(self, parsed_query: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle period-based analysis"""
        granularity = parsed_query.get("granularity", "month")
        time_periods = parsed_query.get("time_periods", [])
        
        if time_periods:
            period = time_periods[0]
            start_date = self._parse_date(period.get("start_date"))
            end_date = self._parse_date(period.get("end_date"))
        else:
            start_date, end_date = None, None
        
        if granularity == "month":
            return await self._monthly_analysis(user_id, start_date, end_date)
        elif granularity == "week":
            return await self._weekly_analysis(user_id, start_date, end_date)
        elif granularity == "year":
            return await self._yearly_analysis(user_id, start_date, end_date)
        else:
            return await self._trend_analysis(user_id, start_date, end_date, granularity)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            return None
    
    async def _compare_time_periods(self, time_periods: List[Dict], user_id: str, parsed_query: Dict) -> Dict[str, Any]:
        """Compare spending across multiple time periods"""
        period_data = []
        
        for period in time_periods:
            start_date = self._parse_date(period.get("start_date"))
            end_date = self._parse_date(period.get("end_date"))
            
            # Get spending data for this period
            total_spending = await self.sheets_service.get_total_spending(user_id, start_date, end_date)
            expenses = await self.sheets_service.get_expenses(user_id, start_date, end_date)
            
            # Get category breakdown if requested
            category_data = None
            if parsed_query.get("include_category_breakdown", False):
                category_data = await self.sheets_service.get_spending_by_category(user_id, start_date, end_date)
            
            period_data.append({
                "label": period.get("label", f"{start_date} to {end_date}"),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "total_spending": total_spending,
                "transaction_count": len(expenses),
                "average_per_transaction": total_spending / len(expenses) if expenses else 0,
                "category_breakdown": category_data
            })
        
        # Create comparison visualization
        chart_type = parsed_query.get("chart_type", "comparison_bar")
        visualization = self._create_comparison_chart(period_data, chart_type)
        
        # Calculate insights
        insights = self._generate_comparison_insights(period_data)
        
        return {
            "message": f"Comparison analysis across {len(period_data)} periods",
            "analysis_type": "comparison",
            "data": {
                "periods": period_data,
                "insights": insights
            },
            "visualization": visualization
        }
    
    async def _compare_categories_over_time(self, time_periods: List[Dict], categories: Optional[List[str]], user_id: str, parsed_query: Dict) -> Dict[str, Any]:
        """Compare categories across time periods"""
        comparison_data = []
        
        for period in time_periods:
            start_date = self._parse_date(period.get("start_date"))
            end_date = self._parse_date(period.get("end_date"))
            
            # Get category breakdown for this period
            category_spending = await self.sheets_service.get_spending_by_category(user_id, start_date, end_date)
            
            # Filter by specific categories if requested
            if categories:
                category_spending = {cat: category_spending.get(cat, 0) for cat in categories}
            
            comparison_data.append({
                "period": period.get("label", f"{start_date} to {end_date}"),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "categories": category_spending
            })
        
        # Create side-by-side comparison chart
        visualization = self._create_category_comparison_chart(comparison_data)
        
        return {
            "message": f"Category comparison across {len(comparison_data)} periods",
            "analysis_type": "category_comparison",
            "data": {
                "periods": comparison_data,
                "insights": self._generate_category_comparison_insights(comparison_data)
            },
            "visualization": visualization
        }
    
    def _create_comparison_chart(self, period_data: List[Dict], chart_type: str) -> str:
        """Create comparison visualization"""
        if chart_type == "side_by_side":
            # Create side-by-side bar chart
            labels = [period["label"] for period in period_data]
            values = [period["total_spending"] for period in period_data]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=labels,
                y=values,
                name="Total Spending",
                text=[f"${val:.2f}" for val in values],
                textposition='auto'
            ))
            
            fig.update_layout(
                title="Spending Comparison Across Periods",
                xaxis_title="Time Periods",
                yaxis_title="Amount ($)"
            )
        else:
            # Default comparison bar chart
            labels = [period["label"] for period in period_data]
            values = [period["total_spending"] for period in period_data]
            
            fig = px.bar(
                x=labels,
                y=values,
                title="Period Spending Comparison",
                labels={'x': 'Time Periods', 'y': 'Amount ($)'}
            )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        return img_base64
    
    def _create_category_comparison_chart(self, comparison_data: List[Dict]) -> str:
        """Create category comparison chart across periods"""
        # Prepare data for grouped bar chart
        all_categories = set()
        for period_data in comparison_data:
            all_categories.update(period_data["categories"].keys())
        
        fig = go.Figure()
        
        # Add a bar trace for each period
        for period_data in comparison_data:
            period_name = period_data["period"]
            categories = [cat for cat in all_categories]
            values = [period_data["categories"].get(cat, 0) for cat in categories]
            
            fig.add_trace(go.Bar(
                name=period_name,
                x=categories,
                y=values,
                text=[f"${val:.2f}" for val in values],
                textposition='auto'
            ))
        
        fig.update_layout(
            title="Category Spending Comparison Across Periods",
            xaxis_title="Categories",
            yaxis_title="Amount ($)",
            barmode='group'
        )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        return img_base64
    
    def _generate_comparison_insights(self, period_data: List[Dict]) -> List[str]:
        """Generate insights from period comparison"""
        insights = []
        
        if len(period_data) < 2:
            return insights
        
        # Compare spending between periods
        amounts = [p["total_spending"] for p in period_data]
        if len(amounts) >= 2:
            diff = amounts[1] - amounts[0]
            percent_change = (diff / amounts[0] * 100) if amounts[0] > 0 else 0
            
            if diff > 0:
                insights.append(f"Spending increased by ${diff:.2f} ({percent_change:.1f}%) between periods")
            elif diff < 0:
                insights.append(f"Spending decreased by ${abs(diff):.2f} ({abs(percent_change):.1f}%) between periods")
            else:
                insights.append("Spending remained the same between periods")
        
        # Find highest and lowest spending periods
        max_period = max(period_data, key=lambda x: x["total_spending"])
        min_period = min(period_data, key=lambda x: x["total_spending"])
        
        if max_period != min_period:
            insights.append(f"Highest spending: {max_period['label']} (${max_period['total_spending']:.2f})")
            insights.append(f"Lowest spending: {min_period['label']} (${min_period['total_spending']:.2f})")
        
        return insights
    
    def _generate_category_comparison_insights(self, comparison_data: List[Dict]) -> List[str]:
        """Generate insights from category comparison"""
        insights = []
        
        if len(comparison_data) < 2:
            return insights
        
        # Find categories with biggest changes
        all_categories = set()
        for period in comparison_data:
            all_categories.update(period["categories"].keys())
        
        for category in all_categories:
            amounts = [period["categories"].get(category, 0) for period in comparison_data]
            if len(amounts) >= 2 and amounts[0] > 0:
                diff = amounts[1] - amounts[0]
                percent_change = (diff / amounts[0] * 100)
                
                if abs(percent_change) > 20:  # Significant change
                    if diff > 0:
                        insights.append(f"{category.title()} spending increased by {percent_change:.1f}%")
                    else:
                        insights.append(f"{category.title()} spending decreased by {abs(percent_change):.1f}%")
        
        return insights
    
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
    
    async def _category_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date], categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze spending by category with optional category filtering"""
        category_spending = await self.sheets_service.get_spending_by_category(
            user_id, start_date, end_date
        )
        
        if not category_spending:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Filter by specific categories if requested
        if categories:
            category_spending = {cat: category_spending.get(cat, 0) for cat in categories if cat in category_spending}
        
        # Create pie chart
        if category_spending:
            fig = px.pie(
                values=list(category_spending.values()),
                names=list(category_spending.keys()),
                title="Spending by Category"
            )
            
            # Convert to base64
            img_bytes = fig.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
        else:
            img_base64 = None
        
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
    
    async def _total_spending_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date], categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze total spending with optional category filtering"""
        if categories:
            # If specific categories requested, get category breakdown and sum only those
            category_spending = await self.sheets_service.get_spending_by_category(user_id, start_date, end_date)
            total = sum(category_spending.get(cat, 0) for cat in categories)
            expenses = await self.sheets_service.get_expenses(user_id, start_date, end_date)
            # Filter expenses by category
            filtered_expenses = []
            for expense in expenses:
                if expense.get('Category', '').lower() in [cat.lower() for cat in categories]:
                    filtered_expenses.append(expense)
            expenses = filtered_expenses
        else:
            total = await self.sheets_service.get_total_spending(user_id, start_date, end_date)
            expenses = await self.sheets_service.get_expenses(user_id, start_date, end_date)
        
        period = "all time"
        if start_date and end_date:
            period = f"from {start_date} to {end_date}"
        elif start_date:
            period = f"since {start_date}"
        elif end_date:
            period = f"until {end_date}"
        
        category_msg = ""
        if categories:
            category_msg = f" for {', '.join(categories)}"
        
        return {
            "message": f"Total spending{category_msg} {period}: ${total:.2f}",
            "data": {
                "total_amount": total,
                "transaction_count": len(expenses),
                "average_per_transaction": total / len(expenses) if expenses else 0,
                "filtered_categories": categories
            },
            "visualization": None
        }
    
    async def _trend_analysis(self, user_id: str, start_date: Optional[date], end_date: Optional[date], granularity: str = "day") -> Dict[str, Any]:
        """Analyze spending trends over time with configurable granularity"""
        spending_data = await self.sheets_service.get_spending_by_time_period(
            user_id, granularity, start_date, end_date
        )
        
        if not spending_data:
            return {
                "message": "No expenses found for the specified period.",
                "data": {},
                "visualization": None
            }
        
        # Create line chart for trend
        fig = px.line(
            x=list(spending_data.keys()),
            y=list(spending_data.values()),
            title=f"{granularity.title()} Spending Trend",
            labels={'x': granularity.title(), 'y': 'Amount ($)'}
        )
        
        # Add trend line for daily data
        if granularity == "day":
            dates = list(spending_data.keys())
            amounts = list(spending_data.values())
            
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
            "message": f"Spending trend analysis by {granularity}",
            "data": {
                f"{granularity}_breakdown": spending_data,
                f"total_{granularity}s": len(spending_data),
                f"average_{granularity}ly": sum(spending_data.values()) / len(spending_data)
            },
            "visualization": img_base64
        }
