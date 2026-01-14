import os
import sys
import pickle

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config


class SheetsService:
    """Handles Google Sheets API operations for logging email data."""
    
    def __init__(self):
        self.service = None
        self.spreadsheet_id = config.SPREADSHEET_ID
        self.sheet_name = config.SHEET_NAME
        self.authenticate()
    
    def authenticate(self):
        """Authenticate using OAuth 2.0 and create Sheets API service."""
        creds = None
        
        # Load existing token if available
        if os.path.exists(config.TOKEN_FILE):
            with open(config.TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(config.CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"Credentials file not found at {config.CREDENTIALS_FILE}. "
                        "Please download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.CREDENTIALS_FILE, config.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for future runs
            with open(config.TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('sheets', 'v4', credentials=creds)
    
    def initialize_sheet(self):
        """
        Initialize the sheet with headers if it's empty or create headers.
        
        Returns:
            bool: True if initialization successful, False otherwise.
        """
        try:
            # Check if sheet has headers
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A1:D1'
            ).execute()
            
            values = result.get('values', [])
            
            # If no headers, add them
            if not values:
                headers = [['Sender Email', 'Subject', 'Date', 'Body']]
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f'{self.sheet_name}!A1:D1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                print("✓ Headers added to sheet")
            
            return True
        
        except HttpError as error:
            print(f"Error initializing sheet: {error}")
            return False
    
    def get_existing_emails(self):
        """
        Retrieve all existing email data from the sheet to check for duplicates.
        
        Returns:
            set: Set of tuples (sender_email, subject, date) for duplicate checking.
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A2:C'  # Skip header row
            ).execute()
            
            values = result.get('values', [])
            
            # Create set of unique identifiers (sender, subject, date)
            existing = set()
            for row in values:
                if len(row) >= 3:
                    existing.add((row[0], row[1], row[2]))
            
            return existing
        
        except HttpError as error:
            print(f"Error reading existing emails: {error}")
            return set()
    
    def append_emails(self, parsed_emails):
        """
        Append parsed email data to the sheet, avoiding duplicates.
        
        Args:
            parsed_emails (list): List of parsed email dictionaries.
        
        Returns:
            int: Number of emails successfully added.
        """
        if not parsed_emails:
            return 0
        
        try:
            # Get existing emails to prevent duplicates
            existing_emails = self.get_existing_emails()
            
            # Prepare rows to append
            rows_to_add = []
            for email in parsed_emails:
                email_key = (
                    email['sender_email'],
                    email['subject'],
                    email['date']
                )
                
                # Only add if not already in sheet
                if email_key not in existing_emails:
                    rows_to_add.append([
                        email['sender_email'],
                        email['subject'],
                        email['date'],
                        email['body']
                    ])
            
            if not rows_to_add:
                print("⚠ All emails already exist in sheet (duplicates prevented)")
                return 0
            
            # Append rows to sheet
            body = {'values': rows_to_add}
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f'{self.sheet_name}!A:D',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updates = result.get('updates', {})
            rows_added = updates.get('updatedRows', 0)
            
            return rows_added
        
        except HttpError as error:
            print(f"Error appending to sheet: {error}")
            return 0
    
    def verify_spreadsheet_access(self):
        """
        Verify that the spreadsheet exists and is accessible.
        
        Returns:
            bool: True if accessible, False otherwise.
        """
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            title = spreadsheet.get('properties', {}).get('title', 'Unknown')
            print(f"✓ Connected to spreadsheet: '{title}'")
            return True
        
        except HttpError as error:
            print(f"✗ Error accessing spreadsheet: {error}")
            print(f"  Make sure SPREADSHEET_ID in config.py is correct")
            return False
