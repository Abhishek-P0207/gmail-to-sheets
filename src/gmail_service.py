import os
import sys
import pickle
from datetime import datetime
import base64

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
        
        self.service = build('gmail', 'v1', credentials=creds)
    
    def get_unread_emails(self, after_timestamp=None):
        """
        Fetch unread emails from the Inbox, optionally filtering by timestamp.
        
        Args:
            after_timestamp (str, optional): ISO format timestamp to fetch emails after.
        
        Returns:
            list: List of email dictionaries with id, subject, sender, date, and snippet.
        """
        try:
            # Build query for unread emails in inbox
            query = 'is:unread in:inbox'
            
            # Add timestamp filter if provided
            if after_timestamp:
                dt = datetime.fromisoformat(after_timestamp)
                date_str = dt.strftime('%Y/%m/%d')
                query += f' after:{date_str}'
            
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                return []
            
            emails = []
            for message in messages:
                email_data = self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
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
            body = self.get_full_body(message['payload'])
            
            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
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

    def get_full_body(self, message_payload):
        """
        Recursively extracts the plain text body from the message payload.
        """
        # 1. Check if the body data is in the top-level payload
        body_data = message_payload.get('body', {}).get('data')
        
        # 2. If not, look through the parts (common in multipart emails)
        if not body_data and 'parts' in message_payload:
            for part in message_payload['parts']:
                if part['mimeType'] == 'text/plain': # Prioritize plain text
                    body_data = part.get('body', {}).get('data')
                    break
                elif part['mimeType'] == 'text/html': # Fallback to HTML
                    body_data = part.get('body', {}).get('data')

        if body_data:
            # Gmail uses base64url encoding
            decoded_bytes = base64.urlsafe_b64decode(body_data)
            return decoded_bytes.decode('utf-8')
        
        return "No content found"
    
    def mark_emails_as_read(self, message_ids):
        """
        Mark multiple emails as read by removing the UNREAD label using batch modify.
        
        Args:
            message_ids (list): List of Gmail message IDs to mark as read.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not message_ids:
            return True
        
        try:
            # Use batchModify to remove UNREAD label from multiple messages
            self.service.users().messages().batchModify(
                userId='me',
                body={
                    'ids': message_ids,
                    'removeLabelIds': ['UNREAD']
                }
            ).execute()
            
            print(f"✓ Marked {len(message_ids)} emails as read in Gmail")
            return True
        
        except HttpError as error:
            print(f"Error marking emails as read: {error}")
            return False
