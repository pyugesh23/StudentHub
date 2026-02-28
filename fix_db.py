import sqlite3
import os

def fix():
    db_path = 'instance/database.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("Adding 'email_sent' column to 'event' table...")
        cursor.execute("ALTER TABLE event ADD COLUMN email_sent BOOLEAN DEFAULT 0")
        conn.commit()
        conn.close()
        print("Success! Database schema updated.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Column already exists. No action needed.")
        else:
            print(f"Operational Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fix()
