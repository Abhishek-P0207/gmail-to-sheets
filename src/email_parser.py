import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from db.init import init_db
from db.queries import (
    is_processed as db_is_processed, 
    mark_as_processed as db_mark_as_processed,
    get_last_run_timestamp,
    update_last_run_timestamp
)


class EmailStateManager:
    """Manages state to track processed emails and prevent duplicates using SQLite database."""
    
    def __init__(self):
        # Initialize the database
        init_db()
    
    def get_last_run_timestamp(self):
        """Get the timestamp of the last successful run."""
        return get_last_run_timestamp()
    
    def update_last_run_timestamp(self):
        """Update the last run timestamp to current time."""
        return update_last_run_timestamp()
    
    def is_processed(self, email_id):
        """Check if an email has already been processed."""
        return db_is_processed(email_id)
    
    def mark_as_processed(self, email_id):
        """Mark an email as processed in the database."""
        db_mark_as_processed(email_id)
    
    def filter_new_emails(self, emails):
        """
        Filter out emails that have already been processed.
        
        Args:
            emails (list): List of email dictionaries with 'id' field.
        
        Returns:
            list: Only emails that haven't been processed yet.
        """
        return [email for email in emails if not self.is_processed(email['id'])]


def parse_email_data(email):
    # print(email)
    """
    Parse email data into a structured format for spreadsheet insertion.
    Extracts the four critical fields: Sender's Email, Subject, Date/Time, and Plain Text Body.
    
    Args:
        email (dict): Email data from Gmail API.
    
    Returns:
        dict: Parsed email data with sender_email, subject, date, and body.
    """
    # Extract sender email from "Name <email@example.com>" format
    sender = email.get('sender', '')
    sender_email = extract_email_address(sender)
    
    return {
        'sender_email': sender_email,
        'subject': email.get('subject', ''),
        'date': email.get('date', ''),
        'body': email.get('body', '')
    }


def extract_email_address(sender_string):
    """
    Extract email address from sender string.
    
    Args:
        sender_string (str): Sender in format "Name <email@example.com>" or "email@example.com"
    
    Returns:
        str: Just the email address.
    """
    import re
    
    # Match email in angle brackets: "Name <email@example.com>"
    match = re.search(r'<([^>]+)>', sender_string)
    if match:
        return match.group(1)
    
    # If no angle brackets, check if the whole string is an email
    if '@' in sender_string:
        return sender_string.strip()
    
    return sender_string
