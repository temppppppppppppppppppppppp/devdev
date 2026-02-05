"""
Treatment Extractor v2.0
========================
원고에서 Treatment 블록을 자동 추출하는 도구.
LLM이 스토리 흐름을 분석해 가변 페이싱으로 블록을 분할함.

[v2.0] 계층적 처리 추가 - 대용량 원고(50화+) 지원

사용법:
    python tools/treatment_extractor.py --input "원고폴더/" --output "output.json"
    python tools/treatment_extractor.py --input "단일파일.txt" --output "output.json"
    python tools/treatment_extractor.py --input "원고폴더/" --output "output.json" --arc-size 10
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from google.genai import types

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
PRIMARY_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY = 5

# 계층 처리 기준
HIERARCHICAL_THRESHOLD = 50  # 50화 이상이면 계층 처리
DEFAULT_ARC_SIZE = 10        # 아크당 에피소드 수

# ─────────────────────────────────────────────
# LLM 클라이언트
# ─────────────────────────────────────────────
class TreatmentLLM:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.current_model = PRIMARY_MODEL

    def ask(self, prompt: str, temperature: float = 0.3) -> dict:
        """LLM에 질의하고 JSON 응답 반환"""
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        response_mime_type="application/json"
                    )
                )
                return self._parse_json(response.text)

            except Exception as e:
                error_msg = str(e).lower()

                # 할당량 초과 → 폴백
                if "quota" in error_msg or "429" in error_msg:
                    if self.current_model != FALLBACK_MODEL:
                        print(f"  ⚠️ {self.current_model} 할당량 초과 → {FALLBACK_MODEL}로 폴백")
                        self.current_model = FALLBACK_MODEL
                        continue

                # 재시도
                if attempt < MAX_RETRIES - 1:
                    print(f"  ⚠️ 오류 발생, {RETRY_DELAY}초 후 재시도... ({attempt+1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    raise RuntimeError(f"LLM 호출 실패: {e}")

        return {}

    def _parse_json(self, text: str) -> dict:
        """JSON 파싱 (자가 치유)"""
        text = text.strip()

        # 마크다운 코드블록 제거
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', text)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            return {"error": "JSON 파싱 실패", "raw": text[:500]}


# ─────────────────────────────────────────────
# 원고 로더
# ─────────────────────────────────────────────
def load_manuscripts(input_path: str) -> list[dict]:
    """
    원고 로드. 반환: [{"ep_num": 1, "text": "..."}, ...]
    """
    path = Path(input_path)
    manuscripts = []

    if path.is_file():
        # 단일 파일
        text = path.read_text(encoding="utf-8")
        manuscripts.append({"ep_num": 1, "text": text, "filename": path.name})

    elif path.is_dir():
        # 폴더 내 모든 txt 파일 (합본 제외)
        files = sorted(
            [f for f in path.glob("*.txt") if "합본" not in f.name],
            key=lambda f: f.name
        )
        for i, f in enumerate(files, 1):
            text = f.read_text(encoding="utf-8")
            import re
            match = re.search(r'(\d+)', f.stem)
            ep_num = int(match.group(1)) if match else i
            manuscripts.append({"ep_num": ep_num, "text": text, "filename": f.name})

    else:
        raise FileNotFoundError(f"경로를 찾을 수 없음: {input_path}")

    print(f"📚 {len(manuscripts)}개 원고 로드 완료")
    return manuscripts


# ─────────────────────────────────────────────
# Phase 0: 아크 요약 (계층 처리용)
# ─────────────────────────────────────────────
def summarize_arcs(llm: TreatmentLLM, manuscripts: list[dict], arc_size: int) -> list[dict]:
    """
    대용량 원고를 arc_size 단위로 묶어서 요약.
    반환: [{"arc_id": 1, "episodes": [1-10], "summary": "..."}, ...]
    """
    print(f"\n📖 Phase 0: 아크 요약 생성 중 ({arc_size}화 단위)...")

    arcs = []
    total_eps = len(manuscripts)

    for start_idx in range(0, total_eps, arc_size):
        end_idx = min(start_idx + arc_size, total_eps)
        arc_manuscripts = manuscripts[start_idx:end_idx]

        arc_id = len(arcs) + 1
        ep_range = [m["ep_num"] for m in arc_manuscripts]

        print(f"  [{arc_id}] 에피소드 {ep_range[0]}-{ep_range[-1]} 요약 중...")

        # 해당 아크의 원고 결합 (앞부분만)
        combined = ""
        for m in arc_manuscripts:
            preview = m["text"][:1500]  # 각 에피소드 앞 1500자
            combined += f"\n[에피소드 {m['ep_num']}]\n{preview}\n---\n"

        prompt = f"""당신은 웹소설 스토리 분석가입니다.
아래 에피소드들(ep {ep_range[0]}~{ep_range[-1]})을 읽고 핵심 내용을 요약하세요.

## 원고
{combined}

## 출력 형식 (JSON)
{{
  "arc_id": {arc_id},
  "episodes": {ep_range},
  "summary": "이 구간의 핵심 사건/갈등/해결을 3-5문장으로 요약",
  "key_events": ["주요 사건1", "주요 사건2", ...],
  "characters_involved": ["등장인물1", "등장인물2", ...]
}}"""

        result = llm.ask(prompt, temperature=0.2)

        if "summary" not in result:
            result = {
                "arc_id": arc_id,
                "episodes": ep_range,
                "summary": f"에피소드 {ep_range[0]}-{ep_range[-1]} 구간",
                "key_events": [],
                "characters_involved": []
            }

        arcs.append(result)
        time.sleep(0.5)  # API 속도 제한

    print(f"  ✅ {len(arcs)}개 아크 요약 완료")
    return arcs


# ─────────────────────────────────────────────
# Phase 1: 블록 경계 분석
# ─────────────────────────────────────────────
def analyze_block_boundaries_simple(llm: TreatmentLLM, manuscripts: list[dict]) -> list[dict]:
    """
    소규모 원고용 (50화 미만): 직접 분석
    """
    print("\n🔍 Phase 1: 블록 경계 분석 중 (단순 모드)...")

    summaries = []
    for m in manuscripts:
        preview = m["text"][:2000] + ("..." if len(m["text"]) > 2000 else "")
        summaries.append(f"[에피소드 {m['ep_num']}]\n{preview}\n")

    combined = "\n---\n".join(summaries)

    prompt = f"""당신은 웹소설 스토리 분석가입니다.
아래 원고들을 읽고, 스토리 흐름에 따라 "블록(Block)" 단위로 묶어주세요.

## 블록 분할 기준
- 하나의 블록 = 하나의 완결된 사건/갈등/해결 사이클
- 에피소드 1~5개를 하나의 블록으로 묶을 수 있음 (가변 페이싱)
- 스토리 전환점, 새로운 갈등 시작점에서 블록을 나눔

## 원고 목록
{combined}

## 출력 형식 (JSON)
{{
  "blocks": [
    {{
      "block_id": 1,
      "episodes": [1, 2],
      "title_hint": "블록 제목 힌트 (15자 이내)",
      "reason": "이 에피소드들을 묶은 이유"
    }},
    ...
  ],
  "total_episodes": {len(manuscripts)}
}}

모든 에피소드가 빠짐없이 할당되어야 합니다."""

    result = llm.ask(prompt, temperature=0.2)

    if "blocks" not in result:
        print("  ⚠️ 블록 분석 실패, 기본 분할 적용 (2개씩)")
        blocks = []
        for i in range(0, len(manuscripts), 2):
            eps = [manuscripts[j]["ep_num"] for j in range(i, min(i+2, len(manuscripts)))]
            blocks.append({"block_id": len(blocks)+1, "episodes": eps, "title_hint": f"블록 {len(blocks)+1}"})
        return blocks

    print(f"  ✅ {len(result['blocks'])}개 블록으로 분할됨")
    return result["blocks"]


def analyze_block_boundaries_hierarchical(llm: TreatmentLLM, arcs: list[dict], manuscripts: list[dict]) -> list[dict]:
    """
    대용량 원고용 (50화 이상): 아크 요약 기반 분석
    """
    print("\n🔍 Phase 1: 블록 경계 분석 중 (계층 모드)...")

    # 아크 요약들을 결합
    arc_summaries = ""
    for arc in arcs:
        arc_summaries += f"""
[아크 {arc['arc_id']}] 에피소드 {arc['episodes'][0]}-{arc['episodes'][-1]}
요약: {arc.get('summary', 'N/A')}
주요 사건: {', '.join(arc.get('key_events', []))}
---
"""

    prompt = f"""당신은 웹소설 스토리 분석가입니다.
아래 아크 요약들을 보고, 전체 스토리를 "블록(Block)" 단위로 나눠주세요.

## 블록 분할 기준
- 하나의 블록 = 하나의 완결된 사건/갈등/해결 사이클
- 1~5개 에피소드를 하나의 블록으로 (가변 페이싱)
- 아크 경계를 참고하되, 아크 내에서도 세분화 가능

## 아크 요약
{arc_summaries}

## 전체 에피소드 범위: 1 ~ {manuscripts[-1]['ep_num']}

## 출력 형식 (JSON)
{{
  "blocks": [
    {{
      "block_id": 1,
      "episodes": [1, 2, 3],
      "title_hint": "블록 제목 (15자 이내)",
      "arc_ref": 1
    }},
    ...
  ],
  "total_blocks": "예상 블록 수"
}}

모든 에피소드가 빠짐없이 순서대로 할당되어야 합니다.
에피소드는 연속된 숫자여야 합니다 (예: [5,6,7] O, [5,7,9] X)"""

    result = llm.ask(prompt, temperature=0.2)

    if "blocks" not in result:
        # 폴백: 아크 = 블록
        print("  ⚠️ 블록 분석 실패, 아크 단위로 폴백")
        blocks = []
        for arc in arcs:
            blocks.append({
                "block_id": arc["arc_id"],
                "episodes": arc["episodes"],
                "title_hint": f"아크 {arc['arc_id']}"
            })
        return blocks

    print(f"  ✅ {len(result['blocks'])}개 블록으로 분할됨")

    # 블록별 에피소드 출력
    for b in result["blocks"][:10]:  # 처음 10개만 출력
        print(f"     Block {b['block_id']}: ep {b['episodes'][0]}-{b['episodes'][-1]} - {b.get('title_hint', '')}")
    if len(result["blocks"]) > 10:
        print(f"     ... 외 {len(result['blocks'])-10}개")

    return result["blocks"]


# ─────────────────────────────────────────────
# Phase 2: Treatment 추출
# ─────────────────────────────────────────────
def extract_treatment_block(llm: TreatmentLLM, block_info: dict, manuscripts: list[dict]) -> dict:
    """
    단일 블록의 Treatment 추출.
    """
    ep_nums = block_info["episodes"]

    # 해당 에피소드들의 원고 결합
    texts = []
    for m in manuscripts:
        if m["ep_num"] in ep_nums:
            texts.append(f"[에피소드 {m['ep_num']}]\n{m['text']}")

    combined_text = "\n\n---\n\n".join(texts)

    # 토큰 제한: 너무 길면 앞부분만
    if len(combined_text) > 50000:
        combined_text = combined_text[:50000] + "\n\n... (이하 생략)"

    prompt = f"""당신은 웹소설 기획 전문가입니다.
아래 원고를 읽고 Treatment 블록 형식으로 요약해주세요.

## 원고
{combined_text}

## Treatment 블록 형식
{{
  "block_id": "Block {block_info['block_id']}",
  "title": "[블록 제목 - 핵심 사건을 담은 임팩트 있는 제목]",
  "content": {{
    "context": "상황/배경 설명. 주인공의 현재 상태, 장소, 시간적 배경, 감각적 묘사를 구체적으로 서술. (3-5문장)",
    "event_villain": "이 블록의 핵심 갈등/위기/적대 요소. 악역이나 장애물이 어떤 위협을 가하는지, 구체적인 계략과 수단까지 상세히. (3-5문장)",
    "solution": "주인공이 문제를 어떻게 해결하는지. 구체적인 행동, 전략, 사용한 능력/기술을 서술. (3-5문장)",
    "reward": "해결 후 얻는 보상/결과/성장. 물리적 보상(재화, 지위, 능력)과 정신적 성장, 관계 변화를 모두 포함. (2-4문장)"
  }}
}}

원고의 내용을 충실히 반영하되, 기획 문서답게 핵심만 압축해서 작성하세요."""

    result = llm.ask(prompt, temperature=0.4)

    # 검증 및 보정
    if "content" not in result:
        result = {
            "block_id": f"Block {block_info['block_id']}",
            "title": f"[{block_info.get('title_hint', '제목 없음')}]",
            "content": result if isinstance(result, dict) else {"error": "추출 실패"}
        }

    return result


def extract_all_treatments(llm: TreatmentLLM, blocks: list[dict], manuscripts: list[dict]) -> list[dict]:
    """
    모든 블록의 Treatment 추출.
    """
    print("\n📝 Phase 2: Treatment 추출 중...")

    treatments = []
    total = len(blocks)

    for i, block in enumerate(blocks):
        ep_range = f"{block['episodes'][0]}-{block['episodes'][-1]}" if len(block['episodes']) > 1 else str(block['episodes'][0])
        print(f"  [{i+1}/{total}] Block {block['block_id']} (ep {ep_range}) 처리 중...")

        treatment = extract_treatment_block(llm, block, manuscripts)
        treatments.append(treatment)

        # API 속도 제한 방지
        if i < total - 1:
            time.sleep(1)

        # 진행률 표시 (10개마다)
        if (i + 1) % 10 == 0:
            print(f"      ... {i+1}/{total} 완료 ({(i+1)/total*100:.1f}%)")

    print(f"  ✅ {len(treatments)}개 Treatment 블록 추출 완료")
    return treatments


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="원고에서 Treatment 블록 추출")
    parser.add_argument("--input", "-i", required=True, help="원고 파일 또는 폴더 경로")
    parser.add_argument("--output", "-o", required=True, help="출력 JSON 파일 경로")
    parser.add_argument("--model", "-m", default=PRIMARY_MODEL, help=f"사용할 모델 (기본: {PRIMARY_MODEL})")
    parser.add_argument("--arc-size", "-a", type=int, default=DEFAULT_ARC_SIZE, help=f"아크 크기 (기본: {DEFAULT_ARC_SIZE})")
    parser.add_argument("--force-hierarchical", "-H", action="store_true", help="강제 계층 처리")
    args = parser.parse_args()

    # 환경변수 로드
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY가 설정되지 않음")
        sys.exit(1)

    # LLM 초기화
    global PRIMARY_MODEL
    PRIMARY_MODEL = args.model
    llm = TreatmentLLM(api_key)

    print(f"🚀 Treatment Extractor v2.0 시작")
    print(f"   모델: {PRIMARY_MODEL}")
    print(f"   입력: {args.input}")
    print(f"   출력: {args.output}")
    print(f"   아크 크기: {args.arc_size}")

    # 1. 원고 로드
    manuscripts = load_manuscripts(args.input)

    if not manuscripts:
        print("❌ 로드된 원고가 없음")
        sys.exit(1)

    # 2. 계층 처리 여부 결정
    use_hierarchical = args.force_hierarchical or len(manuscripts) >= HIERARCHICAL_THRESHOLD
    print(f"   처리 모드: {'계층(Hierarchical)' if use_hierarchical else '단순(Simple)'}")

    # 3. 블록 경계 분석
    if use_hierarchical:
        # Phase 0: 아크 요약
        arcs = summarize_arcs(llm, manuscripts, args.arc_size)

        # Phase 1: 아크 기반 블록 분석
        blocks = analyze_block_boundaries_hierarchical(llm, arcs, manuscripts)
    else:
        # Phase 1: 직접 분석
        blocks = analyze_block_boundaries_simple(llm, manuscripts)

    # 4. Treatment 추출
    treatments = extract_all_treatments(llm, blocks, manuscripts)

    # 5. 저장
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(treatments, f, ensure_ascii=False, indent=4)

    print(f"\n✅ 완료! {output_path}에 저장됨")
    print(f"   총 {len(treatments)}개 블록")

    # 요약 통계
    ep_counts = [len(b["episodes"]) for b in blocks]
    print(f"   블록당 에피소드: 평균 {sum(ep_counts)/len(ep_counts):.1f}개, 최소 {min(ep_counts)}개, 최대 {max(ep_counts)}개")


if __name__ == "__main__":
    main()
