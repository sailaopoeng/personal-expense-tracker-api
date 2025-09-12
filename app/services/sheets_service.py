import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from app.core.config import settings
from app.models.expense import ParsedExpense

class GoogleSheetsService:
    def __init__(self):
        print("Initializing Google Sheets Service...")
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        try:
            print(f"Loading credentials from: {settings.google_service_account_json}")
            self.credentials = Credentials.from_service_account_file(
                settings.google_service_account_json, 
                scopes=self.scope
            )
            
            self.gc = gspread.authorize(self.credentials)
            print(f"Opening Google Sheet with ID: {settings.google_sheet_id}")
            self.sheet = self.gc.open_by_key(settings.google_sheet_id)
            print(f"Sheet title: {self.sheet.title}")
            
            self.worksheet = self._get_or_create_worksheet()
            print(f"Using worksheet: {self.worksheet.title}")
            
            self._setup_headers()
            print("Google Sheets Service initialized successfully")
            
        except Exception as e:
            print(f"Error initializing Google Sheets Service: {e}")
            raise
    
    def _get_or_create_worksheet(self):
        """Get or create the expenses worksheet"""
        try:
            print(f"Looking for worksheet: {settings.worksheet_name}")
            worksheet = self.sheet.worksheet(settings.worksheet_name)
            print(f"Found existing worksheet: {worksheet.title}")
            return worksheet
        except gspread.WorksheetNotFound:
            print(f"Worksheet '{settings.worksheet_name}' not found, creating new one...")
            worksheet = self.sheet.add_worksheet(
                title=settings.worksheet_name, 
                rows=1000, 
                cols=15
            )
            print(f"Created new worksheet: {worksheet.title}")
            return worksheet
    
    def _setup_headers(self):
        """Setup headers if the worksheet is empty or headers are missing"""
        try:
            all_values = self.worksheet.get_all_values()
            
            # Expected headers
            expected_headers = [
                'Timestamp', 'Date', 'Time', 'Amount', 'Currency', 
                'Category', 'Subcategory', 'Description', 'Tags', 
                'Location', 'Payment Method', 'Notes', 'User ID'
            ]
            
            # Check if worksheet is empty or headers are missing/incorrect
            setup_needed = False
            
            if not all_values:
                print("Worksheet is empty, setting up headers...")
                setup_needed = True
            elif len(all_values) == 0:
                print("No rows found, setting up headers...")
                setup_needed = True
            elif not all_values[0] or all_values[0] != expected_headers:
                print("Headers missing or incorrect, setting up headers...")
                print(f"Current first row: {all_values[0] if all_values else 'None'}")
                setup_needed = True
            else:
                print("Headers already exist and are correct")
                
            if setup_needed:
                # If there are existing values but headers are wrong, clear and start fresh
                if all_values and all_values[0] != expected_headers:
                    print("Clearing worksheet and adding correct headers...")
                    self.worksheet.clear()
                    
                self.worksheet.append_row(expected_headers)
                print(f"Headers set up successfully: {expected_headers}")
                
        except Exception as e:
            print(f"Error setting up headers: {e}")
            # Fallback: try to add headers anyway
            try:
                expected_headers = [
                    'Timestamp', 'Date', 'Time', 'Amount', 'Currency', 
                    'Category', 'Subcategory', 'Description', 'Tags', 
                    'Location', 'Payment Method', 'Notes', 'User ID'
                ]
                self.worksheet.append_row(expected_headers)
                print("Headers added as fallback")
            except Exception as fallback_error:
                print(f"Fallback header setup also failed: {fallback_error}")
                raise
    
    async def add_expense(self, expense: ParsedExpense) -> int:
        """Add a new expense to the sheet and return row number"""
        # Format timestamp in a readable Singapore time format
        # Remove timezone info for cleaner display in sheets since we know it's Singapore time
        singapore_timestamp = expense.timestamp.replace(tzinfo=None)
        singapore_date = expense.date
        singapore_time = expense.time
        
        row_data = [
            singapore_timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Readable format without timezone
            singapore_date.strftime('%Y-%m-%d'),  # Date in YYYY-MM-DD format
            singapore_time.strftime('%H:%M:%S'),  # Time in HH:MM:SS format
            expense.amount,
            expense.currency,
            expense.category.value,
            expense.subcategory or '',
            expense.description,
            ', '.join(expense.tags),
            expense.location or '',
            expense.payment_method or '',
            expense.notes or '',
            expense.user_id
        ]
        
        self.worksheet.append_row(row_data)
        
        # Get the row number of the newly added expense
        all_records = self.worksheet.get_all_values()
        return len(all_records)
    
    async def get_expenses(
        self, 
        user_id: str = "default_user",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get expenses with optional filtering"""
        
        # Get all records as dataframe
        records = self.worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if df.empty:
            return []
        
        # Add row numbers (starting from row 2 since row 1 is headers)
        df['row_number'] = range(2, len(df) + 2)
        
        # Filter by user_id
        df = df[df['User ID'] == user_id]
        
        # Convert date column to datetime for filtering
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Apply date filters
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        # Apply category filter
        if category:
            df = df[df['Category'].str.lower() == category.lower()]
        
        # Convert back to list of dictionaries
        return df.to_dict('records')
    
    async def get_spending_by_category(
        self, 
        user_id: str = "default_user",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """Get spending breakdown by category"""
        
        expenses = await self.get_expenses(user_id, start_date, end_date)
        df = pd.DataFrame(expenses)
        
        if df.empty:
            return {}
        
        # Convert Amount to numeric
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        
        # Group by category and sum amounts
        category_spending = df.groupby('Category')['Amount'].sum().to_dict()
        
        return category_spending
    
    async def get_spending_by_time_period(
        self,
        user_id: str = "default_user",
        period: str = "month",  # day, week, month, year
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, float]:
        """Get spending breakdown by time period"""
        
        expenses = await self.get_expenses(user_id, start_date, end_date)
        df = pd.DataFrame(expenses)
        
        if df.empty:
            return {}
        
        # Convert columns to appropriate types
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Group by time period
        if period == "day":
            df['Period'] = df['Date'].dt.strftime('%Y-%m-%d')
        elif period == "week":
            df['Period'] = df['Date'].dt.strftime('%Y-W%U')
        elif period == "month":
            df['Period'] = df['Date'].dt.strftime('%Y-%m')
        elif period == "year":
            df['Period'] = df['Date'].dt.strftime('%Y')
        else:
            raise ValueError("Period must be one of: day, week, month, year")
        
        # Group by period and sum amounts
        period_spending = df.groupby('Period')['Amount'].sum().to_dict()
        
        return period_spending
    
    async def get_total_spending(
        self,
        user_id: str = "default_user",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> float:
        """Get total spending for a user in a date range"""
        
        expenses = await self.get_expenses(user_id, start_date, end_date)
        df = pd.DataFrame(expenses)
        
        if df.empty:
            return 0.0
        
        # Convert Amount to numeric and sum
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        total = df['Amount'].sum()
        
        return float(total)
    
    async def search_expenses(
        self,
        query: str,
        user_id: str = "default_user"
    ) -> List[Dict[str, Any]]:
        """Search expenses by description, category, or tags"""
        
        expenses = await self.get_expenses(user_id)
        df = pd.DataFrame(expenses)
        
        if df.empty:
            return []
        
        # Create a searchable text column
        df['searchable'] = (
            df['Description'].astype(str) + ' ' +
            df['Category'].astype(str) + ' ' +
            df['Subcategory'].astype(str) + ' ' +
            df['Tags'].astype(str) + ' ' +
            df['Notes'].astype(str)
        ).str.lower()
        
        # Filter by query
        mask = df['searchable'].str.contains(query.lower(), na=False)
        filtered_df = df[mask]
        
        # Remove the searchable column and return (keeping row_number)
        filtered_df = filtered_df.drop('searchable', axis=1)
        return filtered_df.to_dict('records')

    async def update_expense(self, row_number: int, expense: ParsedExpense) -> bool:
        """Update an existing expense by row number"""
        try:
            # Check if row exists
            all_values = self.worksheet.get_all_values()
            if row_number < 1 or row_number > len(all_values):
                return False
            
            # Prepare row data (same format as add_expense)
            row_data = [
                expense.timestamp.isoformat(),
                expense.date.isoformat(),
                expense.time.isoformat(),
                expense.amount,
                expense.currency,
                expense.category.value,
                expense.subcategory or '',
                expense.description,
                ', '.join(expense.tags),
                expense.location or '',
                expense.payment_method or '',
                expense.notes or '',
                expense.user_id
            ]
            
            # Update the specific row (row_number is 1-based)
            self.worksheet.update(f'A{row_number}:M{row_number}', [row_data])
            return True
            
        except Exception as e:
            print(f"Error updating expense at row {row_number}: {e}")
            return False

    async def delete_expense(self, row_number: int) -> bool:
        """Delete an expense by row number"""
        try:
            # Check if row exists and is not the header
            all_values = self.worksheet.get_all_values()
            if row_number <= 1 or row_number > len(all_values):
                return False
            
            # Delete the specific row (row_number is 1-based)
            self.worksheet.delete_rows(row_number)
            return True
            
        except Exception as e:
            print(f"Error deleting expense at row {row_number}: {e}")
            return False

    async def get_expense_by_row(self, row_number: int) -> Optional[Dict[str, Any]]:
        """Get a specific expense by row number"""
        try:
            # Check if row exists and is not the header
            all_values = self.worksheet.get_all_values()
            if row_number <= 1 or row_number > len(all_values):
                return None
            
            # Get headers and the specific row
            headers = all_values[0]
            row_data = all_values[row_number - 1]  # Convert to 0-based index
            
            # Create dictionary from headers and row data
            expense_dict = dict(zip(headers, row_data))
            expense_dict['row_number'] = row_number
            
            return expense_dict
            
        except Exception as e:
            print(f"Error getting expense at row {row_number}: {e}")
            return None
