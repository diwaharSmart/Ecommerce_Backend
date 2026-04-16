import sqlite3
import os

db_path = 'uat_db.sqlite3'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
else:
    print(f"Checking {db_path} (Size: {os.path.getsize(db_path)} bytes)")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for table in tables:
        print(f" - {table[0]}")
    conn.close()
