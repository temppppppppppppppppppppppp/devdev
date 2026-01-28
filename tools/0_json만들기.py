import json
import re
import os

# ==============================================================================
# 1. 파일 경로 설정
# ==============================================================================
input_file_path = r'C:\Users\wjjo\Desktop\wuxia_Studio_v26\treatments\팽가 망나니, 가문재건_리트.txt'
output_file_path = r'C:\Users\wjjo\Desktop\wuxia_Studio_v26\treatments\팽가 망나니, 가문재건.json'

# ==============================================================================
# 2. 파싱 로직 (개선된 버전)
# ==============================================================================
def parse_story_file(file_path):
    if not os.path.exists(file_path):
        print(f"오류: 파일을 찾을 수 없습니다. 경로: {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_lines = f.readlines()

    json_blocks = []
    current_block = {}

    # 필드 매핑용 사전 (코드 중복 방지)
    field_map = {
        "CONTEXT:": "context",
        "EVENT/VILLAIN:": "event_villain",
        "SOLUTION:": "solution",
        "REWARD:": "reward"
    }

    for line in raw_lines:
        # 1. 태그 제거 정규표현식 수정 (예: <tag> 형태나 특수 기호 제거)
        # 기존 코드의 r"\" 형태는 문법 오류를 일으킵니다.
        clean_line = re.sub(r'<[^>]+>', '', line).strip() 
        
        if not clean_line:
            continue

        # 2. 블록 시작 감지
        if clean_line.startswith("Block"):
            # 새 블록이 시작될 때 이전 블록이 남아있다면 저장 (안전장치)
            if current_block and "block_id" in current_block:
                json_blocks.append(current_block)

            try:
                if ':' in clean_line:
                    header_part, title_part = clean_line.split(':', 1)
                else:
                    header_part, title_part = clean_line, "제목 없음"
                
                current_block = {
                    "block_id": header_part.strip(),
                    "title": title_part.strip(),
                    "content": {}
                }
            except Exception as e:
                print(f"헤더 파싱 중 건너뜀: {clean_line} ({e})")
                continue

        # 3. 각 필드 데이터 매핑
        else:
            for prefix, key in field_map.items():
                if clean_line.startswith(prefix):
                    current_block["content"][key] = clean_line.replace(prefix, "").strip()
                    
                    # REWARD가 마지막 필드라고 가정하고 리스트에 추가
                    if key == "reward":
                        json_blocks.append(current_block)
                        current_block = {} # 초기화
                    break

    # 루프가 끝난 후 미처 추가되지 않은 마지막 블록 처리
    if current_block and "block_id" in current_block and current_block not in json_blocks:
        json_blocks.append(current_block)

    return json_blocks

# ==============================================================================
# 3. 실행 및 저장
# ==============================================================================
print("파일 변환을 시작합니다...")
final_data = parse_story_file(input_file_path)

if final_data:
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    
    print(f"\n성공! 총 {len(final_data)}개의 블록이 변환되었습니다.")
    print(f"저장된 위치: {output_file_path}")
else:
    print("변환된 데이터가 없습니다. 텍스트 파일 내용을 확인해주세요.")