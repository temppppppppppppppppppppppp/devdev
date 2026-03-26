#!/usr/bin/env python3
import json
import re
from pathlib import Path
from tr_batch_harness import bundle_size, as_text

def get_tokens(text):
    """단순 토큰화 (조사 제외 및 2글자 이상 추출)"""
    return set(re.findall(r'[가-힣A-Za-z0-9]{2,}', as_text(text)))

def calculate_similarity(text1, text2):
    """Jaccard Similarity 측정"""
    set1 = get_tokens(text1)
    set2 = get_tokens(text2)
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)

def check_densification_gate(current_block, previous_blocks, min_chars=800, max_similarity=0.3):
    """덴시피케이션 게이트 검증"""
    # 1. 글자 수 검사
    size = bundle_size(current_block)
    if size < min_chars:
        return False, f"글자 수 미달: {size}/{min_chars}"

    # 2. 유사도 검사 (직전 3개 블록과 비교)
    curr_content = " ".join([as_text(current_block.get("content", {}).get(f)) for f in ["event_villain", "solution", "reward"]])
    for prev in previous_blocks:
        prev_content = " ".join([as_text(prev.get("content", {}).get(f)) for f in ["event_villain", "solution", "reward"]])
        sim = calculate_similarity(curr_content, prev_content)
        if sim > max_similarity:
            return False, f"유사도 초과: {sim:.2f} (Block {prev.get('block_id')}와 유사)"

    # 3. 필수 필드 존재 여부 (장르별 확장 필드)
    ext = current_block.get("martial_ext") or current_block.get("genre_ext") or {}
    # blockguide: historical_event 필수 / wuxguide: action_type 또는 opponent 필수
    has_genre_field = bool(
        (ext.get("historical_event") and ext["historical_event"].get("name"))
        or ext.get("action_type")
        or (isinstance(ext.get("opponent"), dict) and ext["opponent"].get("name"))
    )
    if not has_genre_field:
        return False, "장르 확장 필드 누락 (historical_event 또는 action_type/opponent)"

    return True, "PASS"

if __name__ == "__main__":
    # 테스트용 로직 (실제 연동 시 삭제 가능)
    print("Densification Gate Module Loaded.")
