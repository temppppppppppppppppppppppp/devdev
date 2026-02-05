import sqlite3
import json

db_path = r"C:\Users\PC\Desktop\글도비\projects\팽가 망나니 가문 재건\project_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Anchors ---")
cursor.execute("SELECT key, value FROM anchors")
for row in cursor.fetchall():
    key = row[0]
    val = row[1]
    print(f"Key: {key}")
    if key == 'bible':
        bible_data = json.loads(val)
        # Extract NPC names from bible if possible
        if 'characters' in bible_data:
            print("Found characters in bible")
            for char in bible_data['characters']:
                print(f"  - {char.get('name') or char.get('이름')}")
        elif 'npc' in bible_data:
             for npc in bible_data['npc']:
                print(f"  - {npc.get('name') or npc.get('이름')}")
        else:
            print("Bible keys:", bible_data.keys())

conn.close()
