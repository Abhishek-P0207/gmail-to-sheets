import os
import sys
import pickle
from datetime import datetime
import base64
from bs4 import BeautifulSoup

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
    
    def get_unread_emails(self, after_timestamp=None, subject_filter=None):
        """
        Fetch unread emails from the Inbox, optionally filtering by timestamp and subject.
        
        Args:
            after_timestamp (str, optional): ISO format timestamp to fetch emails after.
            subject_filter (str, optional): Subject keyword to filter emails (Gmail search syntax).
        
        Returns:
            list: List of email dictionaries with id, subject, sender, date, and body.
        
        Examples:
            - subject_filter="invoice" - emails with "invoice" in subject
            - subject_filter="Order #" - emails with "Order #" in subject
        """
        try:
            # Build query for unread emails in inbox
            query = 'is:unread in:inbox'
            
            # Add timestamp filter if provided
            if after_timestamp:
                dt = datetime.fromisoformat(after_timestamp)
                date_str = dt.strftime('%Y/%m/%d')
                query += f' after:{date_str}'
            
            # Add subject filter if provided
            if subject_filter:
                query += f' subject:"{subject_filter}"'
            
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
        Recursively extracts and cleans the email body.
        """
        body_data = None
        is_html = False

        # 1. Check top-level payload
        if 'body' in message_payload and message_payload['body'].get('data'):
            body_data = message_payload['body']['data']
            is_html = message_payload.get('mimeType') == 'text/html'
        
        # 2. Look through multipart parts
        if not body_data and 'parts' in message_payload:
            for part in message_payload['parts']:
                # Prioritize plain text if available
                if part['mimeType'] == 'text/plain':
                    body_data = part.get('body', {}).get('data')
                    is_html = False
                    break
                # Fallback to HTML if no plain text is found yet
                elif part['mimeType'] == 'text/html':
                    body_data = part.get('body', {}).get('data')
                    is_html = True

        if body_data:
            # Decode the Base64url data
            decoded_text = base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            if is_html:
                soup = BeautifulSoup(decoded_text, 'html.parser')
                # Remove scripts and styles
                for script_or_style in soup(["script", "style"]):
                    script_or_style.decompose()
                text = soup.get_text(separator=' ').strip()
                lines = text.splitlines()
                clean_lines = [line.strip() for line in lines if line.strip()]
                return "\n".join(clean_lines)
            
            return decoded_text.strip()
        
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
