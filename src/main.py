import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gmail_service import GmailService
from sheets_service import SheetsService
from email_parser import EmailStateManager, parse_email_data
import config


def main():
    """Main execution flow for Gmail-to-Sheets automation."""
    
    print("Starting Gmail-to-Sheets Automation...")
    print("=" * 60)
    
    # Verify configuration
    if config.SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
        print("\n⚠ ERROR: Please configure SPREADSHEET_ID in config.py")
        print("  1. Create a Google Sheet")
        print("  2. Copy the ID from the URL")
        print("  3. Update SPREADSHEET_ID in config.py")
        return
    
    # Initialize Gmail service
    print("\n1. Authenticating with Gmail API...")
    gmail = GmailService()
    print("✓ Gmail authentication successful")
    
    # Initialize Sheets service
    print("\n2. Authenticating with Google Sheets API...")
    sheets = SheetsService()
    
    # Verify spreadsheet access
    if not sheets.verify_spreadsheet_access():
        print("\n⚠ ERROR: Cannot access spreadsheet. Please check:")
        print("  - SPREADSHEET_ID is correct in config.py")
        print("  - You have edit access to the spreadsheet")
        print("  - Google Sheets API is enabled in Google Cloud Console")
        return
    
    # Initialize sheet with headers
    print("\n3. Initializing spreadsheet...")
    sheets.initialize_sheet()
    
    # Initialize state manager
    print("\n4. Loading state manager...")
    state_manager = EmailStateManager()
    last_run = state_manager.get_last_run_timestamp()
    if last_run:
        print(f"✓ State manager initialized (last run: {last_run})")
    else:
        print("✓ State manager initialized (first run)")
    
    # Fetch unread emails since last run
    print("\n5. Fetching new emails from Inbox...")
    subject_filter = None
    exclude_noreply = True
    
    unread_emails = gmail.get_unread_emails(
        after_timestamp=last_run, 
        subject_filter=subject_filter,
        exclude_noreply=exclude_noreply
    )
    
    filter_msg = []
    if subject_filter:
        filter_msg.append(f"subject containing '{subject_filter}'")
    if exclude_noreply:
        filter_msg.append("excluding no-reply emails")
    
    if filter_msg:
        print(f"✓ Found {len(unread_emails)} emails ({', '.join(filter_msg)})")
    else:
        print(f"✓ Found {len(unread_emails)} emails since last run")
    
    # Filter out already processed emails
    print("\n6. Filtering new emails...")
    new_emails = state_manager.filter_new_emails(unread_emails)
    print(f"✓ {len(new_emails)} new emails to process")
    
    if not new_emails:
        print("\n✓ No new emails to process. Exiting.")
        return
    
    # Parse email data
    print("\n7. Parsing email data...")
    parsed_emails = [parse_email_data(email) for email in new_emails]
    print(f"✓ Parsed {len(parsed_emails)} emails")
    
    # Display parsed data for verification
    if parsed_emails:
        print("\n📧 Sample of parsed emails:")
        for i, email in enumerate(parsed_emails[:2], 1):  # Show first 2
            print(f"\n  Email {i}:")
            print(f"    Sender: {email['sender_email']}")
            print(f"    Subject: {email['subject'][:50]}..." if len(email['subject']) > 50 else f"    Subject: {email['subject']}")
            print(f"    Date: {email['date']}")
            print(f"    Body: {email['body'][:80]}..." if len(email['body']) > 80 else f"    Body: {email['body']}")
    
    # Add to Google Sheets
    print("\n8. Adding emails to Google Sheets...")
    rows_added = sheets.append_emails(parsed_emails)
    print(f"✓ Added {rows_added} rows to spreadsheet")
    
    # Mark emails as processed and update last run timestamp
    print("\n9. Updating state...")
    for email in new_emails:
        state_manager.mark_as_processed(email['id'])
    state_manager.update_last_run_timestamp()
    gmail.mark_emails_as_read([email['id'] for email in new_emails])
    print("✓ State updated")
    
    print("\n" + "=" * 60)
    print("✓ Process completed successfully!")
    print("\nSummary:")
    print(f"  - Total unread emails: {len(unread_emails)}")
    print(f"  - New emails processed: {len(new_emails)}")
    print(f"  - Rows added to sheet: {rows_added}")
    print("=" * 60)


if __name__ == '__main__':
    main()
