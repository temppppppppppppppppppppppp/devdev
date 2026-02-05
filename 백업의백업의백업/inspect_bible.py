import sqlite3
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = r"C:\Users\PC\Desktop\글도비\projects\팽가 망나니 가문 재건\project_data.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
row = cursor.fetchone()
if row:
    data = json.loads(row['data'])
    # Print keys to understand structure
    print("Bible Keys:", data.keys())
    if 'characters' in data:
        print("Characters found in 'characters' key")
    if 'npcs' in data:
        print("Characters found in 'npcs' key")
    
    # Print a sample of the characters if possible
    chars = data.get('characters') or data.get('npcs') or []
    print("Sample Character Data:", json.dumps(chars[:2], ensure_ascii=False, indent=2))

conn.close()
