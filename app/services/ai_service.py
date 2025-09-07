from typing import Dict, Any, List, Optional
import google.generativeai as genai
from datetime import datetime, date, time
import json
import re
from app.core.config import settings
from app.models.expense import ParsedExpense, ExpenseCategory

class GoogleAIService:
    def __init__(self):
        genai.configure(api_key=settings.google_ai_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def parse_expense_text(self, text: str) -> ParsedExpense:
        """
        Parse natural language expense text using Google AI
        """
        prompt = f"""
        Parse the following expense text into structured data. Extract all relevant information and return a JSON response.
        
        Text: "{text}"
        
        Please extract and return the following information in JSON format:
        {{
            "timestamp": "ISO datetime string (if time mentioned, otherwise current time)",
            "amount": "numeric amount (required)",
            "currency": "currency code (default SGD if not specified)",
            "category": "one of: food, transportation, entertainment, utilities, shopping, healthcare, education, travel, subscription, family, other",
            "subcategory": "more specific category if applicable",
            "description": "clear description of the expense",
            "tags": ["relevant", "tags", "as", "array"],
            "location": "location if mentioned",
            "payment_method": "cash, card, online, etc. if mentioned",
            "notes": "any additional notes or context"
        }}
        
        Rules:
        - If no time is specified, use current time
        - If no date is specified, assume today
        - Amount is required and must be a number
        - Category must be one of the specified options
        - Description should be clear and concise
        - Tags should be relevant keywords
        - Return only valid JSON
        
        Current datetime for reference: {datetime.now().isoformat()}
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
        # Parse timestamp
        timestamp_str = data.get('timestamp', datetime.now().isoformat())
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        # Ensure category is valid
        category = data.get('category', 'other').lower()
        if category not in [cat.value for cat in ExpenseCategory]:
            category = 'other'
        
        return ParsedExpense(
            timestamp=timestamp,
            date=timestamp.date(),
            time=timestamp.time(),
            amount=float(data['amount']),
            currency=data.get('currency', 'SGD'),
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
        
        now = datetime.now()
        return ParsedExpense(
            timestamp=now,
            date=now.date(),
            time=now.time(),
            amount=amount,
            currency='SGD',
            category=ExpenseCategory(category),
            description=text,
            tags=[],
            user_id="default_user"
        )
