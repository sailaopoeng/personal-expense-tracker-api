from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime, date, time, timedelta
import json
import re
import pytz
from app.core.config import settings
from app.models.expense import ParsedExpense, ExpenseCategory

class GoogleAIService:
    def __init__(self):
        genai.configure(api_key=settings.google_ai_api_key)
        # self.model = genai.GenerativeModel('gemini-pro')
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.singapore_tz = pytz.timezone('Asia/Singapore')
    
    def _convert_to_singapore_time(self, dt: datetime) -> datetime:
        """Convert datetime to Singapore timezone"""
        if dt.tzinfo is None:
            # If naive datetime, assume it's UTC
            dt = pytz.UTC.localize(dt)
        
        # Convert to Singapore time
        singapore_dt = dt.astimezone(self.singapore_tz)
        return singapore_dt
    
    def _get_current_singapore_time(self) -> datetime:
        """Get current time in Singapore timezone"""
        utc_now = datetime.now(pytz.UTC)
        return self._convert_to_singapore_time(utc_now)
    
    async def parse_expense_text(self, text: str) -> ParsedExpense:
        """
        Parse natural language expense text using Google AI
        """
        current_sg_time = self._get_current_singapore_time()
        
        prompt = f"""
        Parse the following expense text into structured data. Extract all relevant information and return a JSON response.
        
        Text: "{text}"
        
        Please extract and return the following information in JSON format:
        {{
            "timestamp": "ISO datetime string (if time mentioned, otherwise current Singapore time)",
            "amount": "numeric amount (required)",
            "currency": "currency code (ALWAYS use SGD unless specifically mentioned otherwise in the text)",
            "category": "one of: food, transportation, entertainment, utilities, shopping, groceries, healthcare, education, travel, subscription, family, other",
            "subcategory": "more specific category if applicable",
            "description": "clear description of the expense",
            "tags": ["relevant", "tags", "as", "array"],
            "location": "location if mentioned",
            "payment_method": "cash, card, online, etc. if mentioned",
            "notes": "any additional notes or context"
        }}
        
        Rules:
        - If no time is specified, use current Singapore time
        - If no date is specified, assume today
        - Amount is required and must be a number
        - Currency must ALWAYS be SGD unless the user explicitly mentions another currency (USD, EUR, etc.)
        - Category must be one of the specified options
        - Description should be clear and concise
        - Tags should be relevant keywords
        - Return only valid JSON
        - All times should be in Singapore timezone (GMT+8)
        
        Current Singapore datetime for reference: {current_sg_time.isoformat()}
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_text = self._extract_json_from_response(response.text)
            parsed_data = json.loads(json_text)
            
            # Convert to ParsedExpense model
            expense = self._convert_to_expense_model(parsed_data)
            return expense
            
        except Exception as e:
            # Fallback parsing if AI fails
            return self._fallback_parse(text)
    
    async def parse_analytics_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language analytics query to extract specific requirements
        """
        current_sg_time = self._get_current_singapore_time()
        current_date = current_sg_time.date()
        
        prompt = f"""
        Parse the following analytics query to understand what the user wants to analyze about their expenses.
        
        Query: "{query}"
        Current date: {current_date}
        
        Extract and return the following information in JSON format:
        {{
            "analysis_type": "one of: comparison, trend, category_breakdown, total, period_analysis",
            "comparison_type": "if comparison: time_periods, categories, categories_over_time, null",
            "time_periods": [
                {{
                    "label": "descriptive name for the period",
                    "start_date": "YYYY-MM-DD or null",
                    "end_date": "YYYY-MM-DD or null"
                }}
            ],
            "categories": ["list of specific categories if mentioned, or null for all"],
            "granularity": "day, week, month, year",
            "specific_insights": ["list of specific things user wants to know"],
            "chart_type": "pie, bar, line, comparison_bar, side_by_side",
            "include_category_breakdown": true/false
        }}
        
        Examples:
        - "compare this month vs last month" → comparison of two time periods
        - "compare food and transportation spending last 3 months" → category comparison over time
        - "show me July vs August expenses by category" → category comparison between specific months
        - "how much did I spend on food in the last two weeks" → category analysis for specific period
        - "compare my spending pattern between weekdays and weekends" → pattern comparison
        - "show daily expenses for the past week" → trend analysis
        
        Important rules:
        1. For "this month" use current month from start to today
        2. For "last month" use the complete previous month
        3. For "last X days/weeks/months" count backwards from today
        4. When comparing periods, create separate entries in time_periods array
        5. If categories are mentioned specifically, include them in categories array
        6. Choose appropriate chart_type based on the analysis needed
        
        Return only valid JSON, no explanations.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Clean up the response text
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            parsed_result = json.loads(result_text)
            return parsed_result
            
        except Exception as e:
            print(f"Error parsing analytics query: {e}")
            # Fallback to simple parsing
            return self._fallback_query_parsing(query)
    
    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON from AI response text"""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json_match.group()
        
        # If no JSON found, assume the entire response is JSON
        return response_text.strip()
    
    def _convert_to_expense_model(self, data: Dict[str, Any]) -> ParsedExpense:
        """Convert parsed data to ParsedExpense model"""
        # Parse timestamp and convert to Singapore time
        timestamp_str = data.get('timestamp', self._get_current_singapore_time().isoformat())
        
        try:
            # Parse the timestamp
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            timestamp = datetime.fromisoformat(timestamp_str)
            
            # Convert to Singapore time if not already
            singapore_timestamp = self._convert_to_singapore_time(timestamp)
            
        except Exception as e:
            # Fallback to current Singapore time if parsing fails
            singapore_timestamp = self._get_current_singapore_time()
        
        # Ensure category is valid
        category = data.get('category', 'other').lower()
        if category not in [cat.value for cat in ExpenseCategory]:
            category = 'other'
        
        # Ensure currency is SGD unless explicitly specified otherwise
        currency = data.get('currency', 'SGD').upper()
        if currency not in ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'MYR', 'THB', 'IDR', 'PHP', 'VND']:
            currency = 'SGD'  # Default to SGD for any unrecognized currency
        
        return ParsedExpense(
            timestamp=singapore_timestamp,
            date=singapore_timestamp.date(),
            time=singapore_timestamp.time(),
            amount=float(data['amount']),
            currency=currency,
            category=ExpenseCategory(category),
            subcategory=data.get('subcategory'),
            description=data.get('description', 'Expense'),
            tags=data.get('tags', []),
            location=data.get('location'),
            payment_method=data.get('payment_method'),
            notes=data.get('notes'),
            user_id="default_user"
        )
    
    def _fallback_parse(self, text: str) -> ParsedExpense:
        """Fallback parsing if AI fails"""
        # Simple regex to extract amount
        amount_match = re.search(r'\$?(\d+\.?\d*)', text)
        amount = float(amount_match.group(1)) if amount_match else 0.0
        
        # Simple category detection
        category = 'other'
        text_lower = text.lower()
        if any(word in text_lower for word in ['eat', 'food', 'lunch', 'dinner', 'breakfast', 'restaurant']):
            category = 'food'
        elif any(word in text_lower for word in ['transport', 'taxi', 'bus', 'train', 'grab']):
            category = 'transportation'
        elif any(word in text_lower for word in ['shop', 'buy', 'purchase']):
            category = 'shopping'
        elif any(word in text_lower for word in ['kids', 'toys']):
            category = 'family'
        
        # Use current Singapore time
        singapore_time = self._get_current_singapore_time()
        
        return ParsedExpense(
            timestamp=singapore_time,
            date=singapore_time.date(),
            time=singapore_time.time(),
            amount=amount,
            currency='SGD',
            category=ExpenseCategory(category),
            description=text,
            tags=[],
            user_id="default_user"
        )
    
    def _fallback_query_parsing(self, query: str) -> Dict[str, Any]:
        """
        Fallback method for parsing analytics queries when AI fails
        """
        query_lower = query.lower()
        
        # Default response structure
        result = {
            "analysis_type": "category_breakdown",
            "comparison_type": None,
            "time_periods": [{"label": "all time", "start_date": None, "end_date": None}],
            "categories": None,
            "granularity": "month",
            "specific_insights": [],
            "chart_type": "pie",
            "include_category_breakdown": True
        }
        
        # Detect comparison patterns
        if any(word in query_lower for word in ['vs', 'versus', 'compare', 'comparison']):
            result["analysis_type"] = "comparison"
            result["comparison_type"] = "time_periods"
            result["chart_type"] = "comparison_bar"
        
        # Detect time periods
        if 'this month' in query_lower and 'last month' in query_lower:
            today = date.today()
            result["time_periods"] = [
                {"label": "This Month", "start_date": today.replace(day=1).isoformat(), "end_date": today.isoformat()},
                {"label": "Last Month", "start_date": (today.replace(day=1) - timedelta(days=1)).replace(day=1).isoformat(), 
                 "end_date": (today.replace(day=1) - timedelta(days=1)).isoformat()}
            ]
        
        return result