import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


class EmailStateManager:
    """Manages state to track processed emails and prevent duplicates."""
    
    def __init__(self, state_file=None):
        self.state_file = state_file or config.STATE_FILE
        self.processed_ids = self._load_state()
    
    def _load_state(self):
        """Load previously processed email IDs from state file."""
        if not os.path.exists(self.state_file):
            return set()
        
        with open(self.state_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    
    def _save_state(self):
        """Save processed email IDs to state file."""
        with open(self.state_file, 'w') as f:
            for email_id in sorted(self.processed_ids):
                f.write(f"{email_id}\n")
    
    def is_processed(self, email_id):
        """Check if an email has already been processed."""
        return email_id in self.processed_ids
    
    def mark_as_processed(self, email_id):
        """Mark an email as processed and save state."""
        self.processed_ids.add(email_id)
        self._save_state()
    
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
    print(email)
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
        'body': email.get('snippet', '')
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
