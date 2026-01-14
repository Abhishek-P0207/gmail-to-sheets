# Gmail-to-Sheets Automation System

A Python-based automation tool that monitors Gmail for new messages and logs details into Google Sheets.

## Features

- **OAuth 2.0 Authentication**: Secure authentication with Gmail and Sheets APIs
- **Duplicate Prevention**: Tracks processed emails to avoid duplicate entries (both in state file and sheet checking)
- **State Management**: Remembers which emails have been processed across runs
- **Plain Text Extraction**: Extracts plain text body from emails (handles multipart messages)
- **Modular Architecture**: Clean separation of concerns across modules

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Google Cloud APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API** and **Google Sheets API**
4. Create **OAuth 2.0 credentials** (Desktop app type)
5. Download the `credentials.json` file
6. Place it in the `credentials/` folder

### 3. Create Google Sheet

1. Create a new Google Sheet or use an existing one
2. Copy the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit
   ```
3. Update `SPREADSHEET_ID` in `config.py`

### 4. Run the Application

```bash
python src/main.py
```

On first run, a browser window will open for OAuth authentication. After authorization, a `token.json` file will be created for future runs.

## Project Structure

```
├── src/
│   ├── gmail_service.py    # Gmail API interaction
│   ├── sheets_service.py   # Google Sheets integration
│   ├── email_parser.py     # Email parsing and state management
│   └── main.py             # Main execution flow
├── credentials/
│   ├── credentials.json    # OAuth credentials (DO NOT COMMIT)
│   └── token.json          # Auto-generated token (DO NOT COMMIT)
├── config.py               # Configuration settings
├── processed_emails.txt    # State file tracking processed emails
└── requirements.txt        # Python dependencies
```

## How It Works

1. **Authentication**: Uses OAuth 2.0 to securely connect to Gmail and Sheets APIs
2. **Fetch Unread Emails**: Retrieves all unread emails from Inbox
3. **State Check**: Filters out emails that have already been processed
4. **Parse Data**: Extracts sender email, subject, date/time, and plain text body
5. **Duplicate Prevention**: Checks sheet for existing entries before adding
6. **Append to Sheet**: Adds new email data as rows to Google Sheet
7. **Update State**: Marks processed emails to prevent duplicates on next run

## Spreadsheet Format

The Google Sheet will have the following columns:

| Sender Email | Subject | Date | Body |
|--------------|---------|------|------|
| user@example.com | Meeting reminder | Mon, 13 Jan 2025 10:30:00 | Full email body text... |

## Security

- All credential files are excluded from version control via `.gitignore`
- OAuth 2.0 tokens are stored locally and never committed
- State file tracks email IDs only (no sensitive content)
- Uses read-only scope for Gmail, edit scope for Sheets only

## Duplicate Prevention

The system implements two layers of duplicate prevention:

1. **State File**: Tracks processed email IDs in `processed_emails.txt`
2. **Sheet Checking**: Verifies (sender, subject, date) combination doesn't exist in sheet

## Current Status

✅ Email fetching with OAuth 2.0  
✅ Plain text body extraction  
✅ Duplicate prevention (state + sheet checking)  
✅ State management  
✅ Google Sheets integration  
✅ Complete automation pipeline
