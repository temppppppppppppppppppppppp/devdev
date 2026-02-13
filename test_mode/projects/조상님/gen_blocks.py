"""
고금제일의 조상님 — 트리트먼트 블록 생성기
Gemini 2.5 Pro API를 사용하여 B04~B50 상세 트리트먼트 블록을 생성합니다.

사용법:
  python gen_blocks.py              # B04부터 순차 생성
  python gen_blocks.py --start 10   # B10부터 생성
  python gen_blocks.py --start 10 --end 15  # B10~B15만 생성
"""

import argparse
import io
import json
import re
import sys
import time
from pathlib import Path

# --- stdout UTF-8 강제 ---
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

# --- 경로 ---
PROJECT_DIR = Path(__file__).parent
TREATMENT_DIR = PROJECT_DIR / "treatment"
BIBLE_PATH = PROJECT_DIR / "bible.txt"
OUTLINE_PATH = PROJECT_DIR / "macro_outline.txt"
ENV_PATH = PROJECT_DIR / ".env"
PROGRESS_PATH = PROJECT_DIR / "treatment" / "_progress.json"


# --- API 키 로드 ---
def load_api_key():
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GOOGLE_API_KEY"):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(".env에서 GOOGLE_API_KEY를 찾을 수 없습니다.")


# --- Gemini 클라이언트 초기화 ---
def init_client():
    from google import genai

    api_key = load_api_key()
    client = genai.Client(api_key=api_key)
    return client


# --- 파일 로드 ---
def load_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_existing_blocks():
    """기존 블록 파일들을 번호순으로 로드"""
    blocks = {}
    for p in sorted(TREATMENT_DIR.glob("block_*.txt")):
        m = re.match(r"block_(\d+)\.txt", p.name)
        if m:
            num = int(m.group(1))
            blocks[num] = load_text(p)
    return blocks


# --- 매크로 아웃라인에서 특정 블록 정보 추출 ---
def extract_block_outline(outline_text, block_num):
    """매크로 아웃라인에서 해당 블록 번호의 섹션을 추출"""
    pattern = rf"### B{block_num:02d}\b.*?(?=### B\d|## Act|## 보스|## 성장|$)"
    m = re.search(pattern, outline_text, re.DOTALL)
    if m:
        return m.group(0).strip()
    # B19~B22 같은 범위 형식도 처리
    pattern2 = r"### B\d+~B\d+.*?(?=### B\d|## Act|## 보스|## 성장|$)"
    for m2 in re.finditer(pattern2, outline_text, re.DOTALL):
        text = m2.group(0)
        # 범위에 block_num이 포함되는지 확인
        range_match = re.match(r"### B(\d+)~B(\d+)", text)
        if range_match:
            start, end = int(range_match.group(1)), int(range_match.group(2))
            if start <= block_num <= end:
                return text.strip()
    return f"(B{block_num:02d} 아웃라인 정보 없음 — 자유롭게 창작)"


# --- 프롬프트 구성 ---
def build_prompt(bible, outline, block_outline, prev_blocks, block_num):
    # 이전 3개 블록만 컨텍스트로 사용 (토큰 절약)
    context_blocks = []
    for i in range(max(1, block_num - 3), block_num):
        if i in prev_blocks:
            context_blocks.append(prev_blocks[i])

    context_text = "\n\n---\n\n".join(context_blocks) if context_blocks else "(이전 블록 없음)"

    prompt = f"""당신은 무협 웹소설 '고금제일의 조상님'의 시나리오 작가입니다.
아래 자료를 참고하여 Block {block_num} (챕터 {(block_num - 1) * 5 + 1}~{block_num * 5}화)의 상세 트리트먼트를 작성하세요.

## 작성 규칙
1. 아래 포맷을 **정확히** 따르세요.
2. [핵심 전략]은 이 블록의 가장 인상적인 전투/전략을 구체적으로 묘사하세요 (무공명, 신체 동작, 감각 묘사 포함).
3. [상황/맥락]은 오감(시각/청각/후각/촉각/미각)을 활용한 장면 묘사를 포함하세요.
4. [적대자/위기]는 적의 무공, 경지, 전술, 심리를 구체적으로 서술하세요.
5. [해결/전투]는 전투의 흐름을 시간순으로 묘사하세요. 의성어/의태어를 적극 활용하세요.
6. [성장/경지]는 캐릭터별 현재 경지와 변화를 명시하세요.
7. 이전 블록과의 연결성을 유지하되, 반복을 피하세요.
8. 한국어로 작성하세요.

## 출력 포맷
```
# Block {block_num}: [제목]

[핵심 전략]
(3~5문장)

[상황/맥락]
(5~8문장, 오감 묘사 포함)

[적대자/위기]
(적의 이름, 경지, 무공, 전술, 심리를 구체적으로)

[해결/전투]
(전투 흐름을 시간순으로 3~5단계로 서술)

[성장/경지] (캐릭터: 현재 경지 → 변화)
(성장 내용 2~3문장)
```

---

## 바이블 (세계관/캐릭터 설정)
{bible}

---

## 이 블록의 매크로 아웃라인
{block_outline}

---

## 이전 블록 컨텍스트 (직전 3개)
{context_text}

---

위 정보를 바탕으로 Block {block_num}의 상세 트리트먼트를 작성하세요.
매크로 아웃라인의 핵심 이벤트는 반드시 포함하되, 디테일(전투 묘사, 감각 묘사, 대사, 심리 묘사)은 창작하세요.
"""
    return prompt


# --- 응답 후처리 ---
def clean_response(text):
    """마크다운 코드블록 래핑 제거"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


# --- 진행 상황 저장/로드 ---
def load_progress():
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"completed": [], "failed": []}


def save_progress(progress):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


# --- 메인 생성 루프 ---
def generate_blocks(start=4, end=50):
    print(f"\n{'=' * 60}")
    print("  고금제일의 조상님 — 트리트먼트 블록 생성기")
    print(f"  범위: B{start:02d} ~ B{end:02d}")
    print(f"{'=' * 60}\n")

    # 파일 로드
    print("[1/3] 바이블 & 아웃라인 로드...")
    bible = load_text(BIBLE_PATH)
    outline = load_text(OUTLINE_PATH)
    print(f"  바이블: {len(bible):,}자")
    print(f"  아웃라인: {len(outline):,}자")

    # 기존 블록 로드
    print("[2/3] 기존 블록 로드...")
    existing_blocks = load_existing_blocks()
    print(f"  기존 블록: {len(existing_blocks)}개 ({', '.join(f'B{k:02d}' for k in sorted(existing_blocks.keys()))})")

    # Gemini 클라이언트
    print("[3/3] Gemini 2.5 Pro 연결...")
    client = init_client()
    print("  연결 완료!\n")

    progress = load_progress()
    total = end - start + 1
    success = 0
    failed = 0

    for block_num in range(start, end + 1):
        idx = block_num - start + 1

        # 이미 존재하면 스킵
        block_path = TREATMENT_DIR / f"block_{block_num:03d}.txt"
        if block_path.exists():
            print(f"[{idx}/{total}] B{block_num:02d} — 이미 존재, 스킵")
            existing_blocks[block_num] = load_text(block_path)
            success += 1
            continue

        print(f"[{idx}/{total}] B{block_num:02d} 생성 중...", end=" ", flush=True)

        # 아웃라인 추출
        block_outline = extract_block_outline(outline, block_num)

        # 프롬프트 구성
        prompt = build_prompt(bible, outline, block_outline, existing_blocks, block_num)

        # API 호출
        t0 = time.time()
        try:
            response = client.models.generate_content(
                model="gemini-2.5-pro",
                contents=prompt,
                config={
                    "temperature": 0.8,
                    "max_output_tokens": 4096,
                },
            )
            elapsed = time.time() - t0
            result = clean_response(response.text)

            # 검증: 필수 섹션 존재 확인
            required = ["[핵심 전략]", "[상황/맥락]", "[적대자/위기]", "[해결/전투]", "[성장/경지]"]
            missing = [s for s in required if s not in result]
            if missing:
                print(f"경고 — 누락 섹션: {missing}")
                # 그래도 저장은 함

            # 저장
            with open(block_path, "w", encoding="utf-8") as f:
                f.write(result + "\n")

            existing_blocks[block_num] = result
            success += 1
            progress["completed"].append(block_num)
            save_progress(progress)

            print(f"OK ({elapsed:.1f}초, {len(result):,}자)")

        except Exception as e:
            elapsed = time.time() - t0
            print(f"실패 ({elapsed:.1f}초) — {e}")
            failed += 1
            progress["failed"].append(block_num)
            save_progress(progress)

            # 429 에러 (할당량 초과) 시 대기
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                wait = 60
                print(f"  할당량 초과 감지 — {wait}초 대기...")
                time.sleep(wait)
            elif "404" in err_str:
                print("  모델을 찾을 수 없습니다. 모델명을 확인하세요.")
                sys.exit(1)
            else:
                time.sleep(5)

        # API 호출 간격 (rate limit 방지)
        time.sleep(3)

    # 요약
    print(f"\n{'=' * 60}")
    print("  생성 완료!")
    print(f"  성공: {success}/{total}")
    print(f"  실패: {failed}/{total}")
    if progress["failed"]:
        print(f"  실패 블록: {progress['failed']}")
        print(f"  재시도: python gen_blocks.py --start {min(progress['failed'])} --end {max(progress['failed'])}")
    print(f"{'=' * 60}\n")


# --- CLI ---
def main():
    parser = argparse.ArgumentParser(description="트리트먼트 블록 생성기")
    parser.add_argument("--start", type=int, default=4, help="시작 블록 번호 (기본: 4)")
    parser.add_argument("--end", type=int, default=50, help="종료 블록 번호 (기본: 50)")
    args = parser.parse_args()

    if args.start < 1 or args.end > 50 or args.start > args.end:
        print("오류: 블록 범위는 1~50이어야 합니다.")
        sys.exit(1)

    TREATMENT_DIR.mkdir(exist_ok=True)
    generate_blocks(args.start, args.end)


if __name__ == "__main__":
    main()
