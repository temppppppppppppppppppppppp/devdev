import sqlite3
import json
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

db_path = r"C:\Users\PC\Desktop\글도비\projects\팽가 망나니 가문 재건\project_data.db"
if not os.path.exists(db_path):
    print(f"Error: DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

npcs = set()

# 1. From anchors (bible)
cursor.execute("SELECT data FROM anchors WHERE key = 'bible'")
row = cursor.fetchone()
if row:
    try:
        data = json.loads(row['data'])
        # Deep search for names
        def find_names(obj):
            if isinstance(obj, dict):
                # Try common keys
                name = obj.get('name') or obj.get('이름') or obj.get('npc_name')
                if name and isinstance(name, str):
                    npcs.add(name)
                for v in obj.values():
                    find_names(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_names(item)
        
        find_names(data)
    except Exception as e:
        print(f"Bible parse error: {e}")

# 2. From encyclopedia
try:
    cursor.execute("SELECT item FROM encyclopedia")
    for row in cursor.fetchall():
        npcs.add(row['item'])
except:
    pass

# 3. From karma_status
try:
    cursor.execute("SELECT npc_name FROM karma_status")
    for row in cursor.fetchall():
        npcs.add(row['npc_name'])
except:
    pass

# Sort and print
sorted_npcs = sorted(list(npcs))
print("--- MASTER NPC LIST ---")
for name in sorted_npcs:
    print(name)

conn.close()
