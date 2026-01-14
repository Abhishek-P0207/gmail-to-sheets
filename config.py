import os

# Gmail API Configuration
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Google Sheets API Configuration
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Combined scopes for both APIs
SCOPES = GMAIL_SCOPES + SHEETS_SCOPES

# Credentials
CREDENTIALS_FILE = os.path.join('../credentials', 'credentials.json')
TOKEN_FILE = 'token.json'

# State Management
STATE_FILE = 'processed_emails.txt'

# Google Sheets Configuration
# Replace with your actual Spreadsheet ID from the URL
# URL format: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
SPREADSHEET_ID = 'Your spreadsheet id'
SHEET_NAME = 'Sheet1'  # Name of the sheet tab
