import json
import re
import sys

def amplify_number(match):
    # 매치된 텍스트 중 숫자만 추출
    num_str = re.sub(r'[^0-9.]', '', match.group())
    if not num_str:
        return match.group()
        
    original_num = float(num_str)
    # 스낵컬쳐에 맞게 금액을 5~10배 정도 뻥튀기
    new_num = original_num * 10
    
    # 정수면 소수점 제거
    if new_num.is_integer():
        new_num = int(new_num)
        
    # 원래 포맷(억, 조 등 단위) 복구
    unit = match.group().replace(num_str, '')
    return f"{new_num:,}{unit}"

def automate_snack_culture(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for i, block in enumerate(data):
        # Block 1~6은 이미 수작업 했으므로 스킵
        if i < 6:
            continue
            
        # 1. 금액 뻥튀기 (자산 인플레)
        # 억, 조 단위의 숫자를 10배로 증가
        for key in ['content', 'stakes', 'power_shift', 'genre_ext']:
            if key == 'genre_ext':
                ext = block.get('genre_ext', {})
                for ext_key in ['capital_before', 'capital_after', 'capital_delta', 'profit_loss']:
                    if ext_key in ext and isinstance(ext[ext_key], str):
                        ext[ext_key] = re.sub(r'\d+(,\d+)*(\.\d+)?(억|조|천억|백억|만)', amplify_number, ext[ext_key])
            else:
                if key in block:
                    if isinstance(block[key], str):
                        block[key] = re.sub(r'\d+(,\d+)*(\.\d+)?(억|조|천억|백억|만)', amplify_number, block[key])
                    elif isinstance(block[key], dict):
                        for sub_key, sub_val in block[key].items():
                            if isinstance(sub_val, str):
                                block[key][sub_key] = re.sub(r'\d+(,\d+)*(\.\d+)?(억|조|천억|백억|만)', amplify_number, sub_val)

        # 2. 갈등 요소 너프 (사이다 극대화)
        if 'stakes' in block and isinstance(block['stakes'], str):
            block['stakes'] += " (하지만 벼락부자가 된 시우의 압도적 자본력 앞에 모든 리스크는 사실상 무의미하다.)"
            
        # 3. 악당 약화
        if 'content' in block and 'event_villain' in block['content']:
            villain_text = block['content']['event_villain']
            if "위기" in villain_text or "압박" in villain_text or "공격" in villain_text:
                 block['content']['event_villain'] += " 그러나 시우는 코웃음도 치지 않을 하찮은 도발에 불과했다."

        # 4. 감정적 쾌감 (Cider) 주입
        if 'callback' in block:
             block['callback'].append("전생의 비참함과 대비되는, 현재의 무자비하고 압도적인 자본의 폭력")
             
        if 'emotional_beat' in block:
            block['emotional_beat']['intensity'] = 10
            
        if 'tension_level' in block:
            block['tension_level'] = max(3, block['tension_level'] - 2) # 긴장감(스트레스)은 낮춤 (고구마 방지)
            
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
if __name__ == "__main__":
    _src = sys.argv[1] if len(sys.argv) > 1 else "treatments/골든루트_tr_block_ALL_v2_snack.json"
    _dst = sys.argv[2] if len(sys.argv) > 2 else _src.replace(".json", "_out.json")
    if _src == _dst:
        _dst = _src.replace(".json", "_out.json")
        if _dst == _src:
            _dst = f"{_src}.out"
    automate_snack_culture(_src, _dst)
    print(f"Snack culture automation completed: {_src} -> {_dst}")
