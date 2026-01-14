import sqlite3
from datetime import datetime

# check for duplicates
def is_processed(message_id):
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM processed_emails WHERE message_id = ?', (message_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result is not None  # Returns True if ID exists

# save the state
def mark_as_processed(message_id):
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'INSERT INTO processed_emails (message_id, processed_at) VALUES (?, ?)',
            (message_id, datetime.utcnow().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # ID already exists
        pass
    finally:
        conn.close()

# get last run timestamp
def get_last_run_timestamp():
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT timestamp FROM last_run WHERE id = 1')
    result = cursor.fetchone()
    
    conn.close()
    return result[0] if result else None

# update last run timestamp
def update_last_run_timestamp():
    conn = sqlite3.connect('state.db')
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT OR REPLACE INTO last_run (id, timestamp) VALUES (1, ?)
    ''', (timestamp,))
    
    conn.commit()
    conn.close()
    return timestamp