import os
import re
import sys

# Configuration
TARGET_DIR = r"C:\Users\wjjo\Desktop\글도비\projects\팽가 망나니 가문 재건\drafts"
BACKUP_EXT = ".bak"

# Patterns to detect
# 1. English characters (A-Z, a-z) - often not in Wuxia unless specific context
REGEX_ENGLISH = re.compile(r'[a-zA-Z]+')
# 2. Numbers (0-9) - Wuxia usually uses Chinese numerals (일, 이, 삼...), but arabic might be okay depending on style. Flagging for review.
REGEX_NUMBERS = re.compile(r'[0-9]+')

# 3. Modern words list (Extendable)
MODERN_TERMS = [
    "핸드폰", "스마트폰", "TV", "텔레비전", "카메라", "컴퓨터", "인터넷", 
    "아파트", "엘리베이터", "버스", "택시", "비행기", "공항", 
    "빌딩", "콘크리트", "아스팔트", "플라스틱", "비닐", 
    "마이크", "스피커", "라디오", "뉴스", "방송", 
    "아이스크림", "초콜릿", "커피", "주스", "콜라", "사이다",
    "담배", "라이터", # Proper Wuxia uses terms like '초', '화절자' etc.
    "총", "권총", "소총", # Unless it's a modern fusion
    "병원", "의사", "간호사", # '의원', '의원', '의녀' etc.
    "경찰", "형사", # '관아', '포졸', '포두'
    "대통령", "국회의원", 
    "만원", "천원", "백원", # Currency: '냥', '분', '전'
    "킬로미터", "미터", "센티미터", # '리', '장', '척'
    "킬로그램", "그램", # '근', '관'
    "시간", "분", "초", # '시진', '각' (Though '시간' is sometimes accepted, strict Wuxia uses '시진')
    "일요일", "월요일", # Date formats are different
]

def scan_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(".txt"):
                files.append(os.path.join(root, filename))
    return files

def check_content(content):
    issues = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Check Modern Terms
        for term in MODERN_TERMS:
            if term in line:
                issues.append({
                    'line_num': i + 1,
                    'line_content': line,
                    'type': 'Modern Term',
                    'match': term,
                    'start_index': line.find(term)
                })
        
        # Check English
        for match in REGEX_ENGLISH.finditer(line):
            issues.append({
                'line_num': i + 1,
                'line_content': line,
                'type': 'English',
                'match': match.group(),
                'start_index': match.start()
            })
            
        # Check Numbers
        for match in REGEX_NUMBERS.finditer(line):
            issues.append({
                'line_num': i + 1,
                'line_content': line,
                'type': 'Number',
                'match': match.group(),
                'start_index': match.start()
            })
            
    return issues, lines

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print(f"Scanning directory: {TARGET_DIR}")
    files = scan_files(TARGET_DIR)
    
    if not files:
        print("No text files found.")
        return

    print(f"Found {len(files)} files.")
    
    for file_path in files:
        print(f"\nProcessing: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        issues, lines = check_content(content)
        
        if not issues:
            print("  No issues found.")
            continue
            
        modified = False
        
        # Sort issues by line number then index (reverse to not mess up indices when replacing? actually we edit lines, so reverse only matters if multiple edits per line)
        # For simplicity, we'll re-scan the line after an edit or process one by one carefully.
        # Let's process issues. To handle multiple edits in one line, we need to be careful.
        # A simple approach: Group issues by line index.
        
        issues_by_line = {}
        for issue in issues:
            ln = issue['line_num'] - 1 # 0-indexed
            if ln not in issues_by_line:
                issues_by_line[ln] = []
            issues_by_line[ln].append(issue)
            
        sorted_line_indices = sorted(issues_by_line.keys())
        
        for line_idx in sorted_line_indices:
            line_issues = issues_by_line[line_idx]
            # Process one issue at a time for this line.
            # If line changes, we might invalid other matches indices.
            # So we will loop until the user is done with this line or we fixed them all.
            
            # Actually, simplest is to just show the line and ask to rewrite IT if deemed necessary.
            
            current_line = lines[line_idx]
            original_line = current_line
            
            print(f"\nFile: {os.path.basename(file_path)}")
            print(f"Line {line_idx+1}: {current_line.strip()}")
            
            detected_terms = set()
            for issue in line_issues:
                detected_terms.add(f"{issue['type']}: '{issue['match']}'")
            
            print(f"Detected: {', '.join(detected_terms)}")
            
            while True:
                action = input("Action [e]dit, [s]kip line, [i]gnore rest of file, [q]uit: ").lower().strip()
                
                if action == 's':
                    break
                elif action == 'i':
                    # Skip the rest of this file
                    return # Exit the check_content loop or handle effectively? 
                    # Wait, we are in main loop here iterating over lines.
                    # We need to signal to break the outer loop.
                    # Let's change the logic slightly.
                    pass 
                elif action == 'e':
                    new_line = input(f"Edit line (enter to keep original):\n> ")
                    if new_line.strip():
                        lines[line_idx] = new_line
                        modified = True
                        print("Line updated.")
                    break
                elif action == 'q':
                    print("Quitting...")
                    sys.exit(0)
                else:
                    print("Invalid option.")
            
            if action == 'i':
                break # Breaks the line loop, effectively skipping to save prompt

        if modified:
            save = input(f"Save changes to {os.path.basename(file_path)}? [y/n]: ").lower()
            if save == 'y':
                # Backup first
                backup_path = file_path + BACKUP_EXT
                try:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(content) # Write original content
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    print(f"Saved. Backup created at {backup_path}")
                except Exception as e:
                    print(f"Error saving file: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
