import sqlite3
import os

db_path = os.path.join('instance', 'database.db')
if not os.path.exists(db_path):
    # Try alternate path if first one fails
    db_path = 'app/instance/database.db'
    if not os.path.exists(db_path):
        db_path = 'database.db'

print(f"Checking database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if google_id column exists
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'google_id' not in columns:
        print("Adding 'google_id' column to 'user' table...")
        cursor.execute("ALTER TABLE user ADD COLUMN google_id VARCHAR(100)")
        conn.commit()
        print("Column added successfully.")
    else:
        print("'google_id' column already exists.")
        
    conn.close()
except Exception as e:
    print(f"Error updating database: {e}")
