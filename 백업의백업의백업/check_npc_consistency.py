import sqlite3
import json
import os
import sys
import re
from pathlib import Path

# Ensure UTF-8 output for Korean characters
sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = r"C:\Users\PC\Desktop\글도비"
DB_PATH = Path(PROJECT_ROOT) / "projects" / "팽가 망나니 가문 재건" / "project_data.db"
BLUEPRINTS_DIR = Path(PROJECT_ROOT) / "projects" / "팽가 망나니 가문 재건" / "plans" / "blueprints"
ERROR_REPORT_PATH = Path(PROJECT_ROOT) / "npc에러.txt"

def get_master_npcs():
    if not DB_PATH.exists():
        print(f"Error: DB not found at {DB_PATH}")
        return set()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    npcs = set()

    # 1. Deep extraction from ALL anchors
    cursor.execute("SELECT data FROM anchors")
    for row in cursor.fetchall():
        try:
            data = json.loads(row['data'])
            def deep_find(obj):
                if isinstance(obj, dict):
                    # common keys for names in this system
                    for k in ['name', '이름', 'npc_name', 'target', 'item']:
                        val = obj.get(k)
                        if val and isinstance(val, str) and len(val.strip()) >= 2:
                            # Heuristic: If it looks like a person's name or a defined entity
                            # We'll include it to reduce false positives
                            npcs.add(val.strip())
                    for v in obj.values():
                        deep_find(v)
                elif isinstance(obj, list):
                    for item in obj:
                        deep_find(item)
            deep_find(data)
        except:
            pass

    # 2. From encyclopedia (specifically NPC category if possible, but we'll take all as reference)
    try:
        cursor.execute("SELECT item FROM encyclopedia")
        for row in cursor.fetchall():
            npcs.add(row['item'])
    except:
        pass

    # 3. From karma_status (NPC centric table)
    try:
        cursor.execute("SELECT npc_name FROM karma_status")
        for row in cursor.fetchall():
            npcs.add(row['npc_name'])
    except:
        pass

    conn.close()
    
    # Core protagonist name variations
    npcs.update(["팽무진", "무진", "주인공"])
    
    # Filter out noise (brief descriptions or non-names that accidentally got in)
    # Most Korean names are 2-4 characters.
    refined_npcs = set()
    for n in npcs:
        # Remove parenthetical asides like "(가주)" or "(숙부)" for matching
        clean_name = re.sub(r'\(.*?\)', '', n).strip()
        if clean_name:
            refined_npcs.add(clean_name)
            refined_npcs.add(n) # Keep original too
            
    return refined_npcs

def scan_blueprint(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract names from characters: ['Name1', 'Name2']
    char_list_matches = re.findall(r"characters: \[(.*?)\]", content)
    found_in_metadata = set()
    for match in char_list_matches:
        names = [n.strip().strip("'").strip('"') for n in match.split(',')]
        found_in_metadata.update(names)
    
    return found_in_metadata

def check_consistency():
    master_npcs = get_master_npcs()
    
    errors = []
    blueprint_files = sorted(list(BLUEPRINTS_DIR.glob("blueprint_*.txt")))
    
    for bp_file in blueprint_files:
        metadata_names = scan_blueprint(bp_file)
        
        for name in metadata_names:
            # Check if name or base name (without (role)) is in master
            clean_name = re.sub(r'\(.*?\)', '', name).strip()
            
            # Simple membership check
            if name in master_npcs or clean_name in master_npcs:
                continue
                
            # If not found, report as unknown
            errors.append(f"[{bp_file.name}] Unknown NPC: {name}")

    if errors:
        with open(ERROR_REPORT_PATH, 'w', encoding='utf-8') as f:
            f.write(f"--- Found {len(errors)} Unknown NPC references in Blueprints ---\n")
            f.write("Note: These names were not found in the Master Bible or Encyclopedia.\n\n")
            f.write("\n".join(errors))
        print(f"Results recorded in {ERROR_REPORT_PATH}")
    else:
        if ERROR_REPORT_PATH.exists():
            os.remove(ERROR_REPORT_PATH)
        print("Consistency check passed. No unknown NPCs found.")

if __name__ == "__main__":
    check_consistency()
