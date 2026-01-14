import os
import sys
import pickle

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

class GmailService:
    """Handles Gmail API authentication and email fetching operations."""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate using OAuth 2.0 and create Gmail API service."""
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
                # token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_unread_emails(self):
        """
        Fetch all unread emails from the Inbox.
        
        Returns:
            list: List of email dictionaries with id, subject, sender, date, and snippet.
        """
        try:
            # Query for unread emails in inbox
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread in:inbox',
                maxResults=20
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            emails = []
            for message in messages:
                email_data = self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            print(emails)
            
            return emails
        
        except HttpError as error:
            print(f"An error occurred: {error}")
            return []
    
    def _get_email_details(self, message_id):
        """
        Fetch detailed information for a specific email.
        
        Args:
            message_id (str): The Gmail message ID.
        
        Returns:
            dict: Email details including id, subject, sender, date, and snippet.
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # print(message)
            
            headers = message['payload']['headers']
            
            # Extract relevant headers
            subject = self._get_header_value(headers, 'Subject')
            sender = self._get_header_value(headers, 'From')
            date = self._get_header_value(headers, 'Date')
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'snippet': message.get('snippet', '')
            }
        
        except HttpError as error:
            print(f"Error fetching email {message_id}: {error}")
            return None
    
    def _get_header_value(self, headers, name):
        """Extract header value by name from email headers."""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return ''
