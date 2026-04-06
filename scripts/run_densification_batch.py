#!/usr/bin/env python3
"""
Densification Batch Runner
기존 tr_batch_harness.py의 prompt 기능을 확장하여,
Block Densification Mapping 데이터를 프롬프트에 강제 주입하는 래퍼 스크립트.
"""

import argparse
import json
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.narrative_router.artifact_paths import canonical_tr_path  # noqa: E402

def load_mapping(mapping_file: Path):
    with open(mapping_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_injection_for_block(block_id: int, mapping_data: dict) -> str:
    injection_text = ""
    for rule in mapping_data.get("arc_densification_rules", []):
        if block_id in rule.get("blocks", []):
            injection_text += f"\n[CRITICAL DENSIFICATION DIRECTIVE FOR BLOCK {block_id}]\n"
            injection_text += f"1. Historical Event: {rule.get('historical_injection')}\n"
            injection_text += f"2. Bigshot Opponent: {rule.get('bigshot_injection')}\n"
            injection_text += f"3. Key Item: {rule.get('item_injection')}\n"
            if "tactical_focus" in rule:
                injection_text += f"4. Tactical Focus: {rule.get('tactical_focus')}\n"
            break
            
    # 특수 오류 수정(C-02 등) 반영
    for fix in mapping_data.get("special_fixes", []):
        if fix.get("block_id") == block_id:
            injection_text += f"\n[AUDIT FIX REQUIRED]: {fix.get('fix_note')}\n"
            
    return injection_text

def run_batch(start_block: int, batch_size: int, draft_path: Path, roadmap_path: Path, mode: str):
    print(f"--- Starting Densification Batch for Blocks {start_block} to {start_block+batch_size-1} ---")
    
    # 1. 원본 프롬프트 생성 (기존 하네스 호출)
    cmd_prompt = [
        sys.executable, "scripts/tr_batch_harness.py", "prompt",
        "--draft", str(draft_path),
        "--roadmap", str(roadmap_path),
        "--start", str(start_block),
        "--batch-size", str(batch_size),
        "--mode", mode
    ]
    
    result = subprocess.run(cmd_prompt, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error generating base prompt:", result.stderr)
        return
        
    base_prompt = result.stdout
    
    # 2. 덴시피케이션 지침 주입
    mapping_data = load_mapping(Path("config/smart_retrieval/block_densification_mapping.json"))
    
    injections = ""
    for b in range(start_block, start_block + batch_size):
        injections += get_injection_for_block(b, mapping_data)
        
    if injections:
        densified_prompt = base_prompt + "\n\n=========================================\n" \
                           + "=== 🚨 DENSIFICATION HARNESS INJECTIONS ===\n" \
                           + "=========================================\n" \
                           + "You MUST integrate the following specific elements into the generated JSON blocks. " \
                           + "DO NOT use generic templates. Ensure distinct tactical moves and high character density.\n" \
                           + injections
    else:
        densified_prompt = base_prompt

    # 3. 생성된 프롬프트를 임시 파일로 저장하여 AI(Gemini CLI)에게 전달하기 쉽게 만듦
    out_file = Path(f"tmp_densify_prompt_b{start_block}.txt")
    out_file.write_text(densified_prompt, encoding="utf-8")
    print(f"✅ Densification Prompt saved to {out_file.name}")
    print(f"👉 To generate: cat {out_file.name} | gemini-cli --model {mode} > out_b{start_block}.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument(
        "--draft",
        type=Path,
        default=canonical_tr_path("chaebol_allowance_zero", root=ROOT).relative_to(ROOT),
    )
    parser.add_argument("--roadmap", type=Path, default=Path("bible/chaebol_allowance_zero_bi.json"))
    parser.add_argument("--mode", type=str, default="pro", choices=["flash", "pro"])
    args = parser.parse_args()
    
    run_batch(args.start, args.batch_size, args.draft, args.roadmap, args.mode)
