import sqlite3
from datetime import datetime

def init_db():
    # This creates a file named 'state.db' in your project folder
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()
    
    # Create a table to store processed message IDs with timestamp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            message_id TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL
        )
    ''')
    
    # Create a table to store the last run timestamp
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_run (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()