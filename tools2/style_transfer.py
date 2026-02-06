"""
Style Transfer - 기존 원고에 문체 DNA 적용
기존 원고의 내용(플롯/대화/사건)은 100% 유지하면서 문체만 교체.
"""
import os, sys, json, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types

# ── 설정 ──
INPUT_DIR = Path("projects/재벌물/drafts")
OUTPUT_DIR = Path("블록 연구소/ep1_15_transfer")
START_EP = 1
END_EP = 15
MODELS = ["gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"]

# ── 스타일 가이드 로드 (DB) ──
import sqlite3
conn = sqlite3.connect("projects/재벌물/project_data.db")
cur = conn.cursor()
cur.execute("SELECT data FROM anchors WHERE key = 'style_guide'")
row = cur.fetchone()
conn.close()

if not row:
    print("[ERROR] style_guide not found in DB")
    sys.exit(1)

from modules.core.stage0.style_extractor import StyleGuide
guide = StyleGuide.from_dict(json.loads(row[0]))
STYLE_PROMPT = guide.to_prompt()

print(f"Style Guide loaded: {len(STYLE_PROMPT)} chars")
print(f"Episodes: {START_EP} ~ {END_EP}")
print(f"Output: {OUTPUT_DIR}")
print("=" * 60)

# ── LLM 클라이언트 ──
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_with_fallback(prompt: str, max_tokens: int = 16000) -> str:
    """모델 폴백 체인으로 생성"""
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=max_tokens,
                )
            )
            if response.text and len(response.text) > 1000:
                return response.text
            print(f"  [!] {model}: 응답 너무 짧음 ({len(response.text or '')}자), 다음 모델...")
        except Exception as e:
            print(f"  [!] {model} 실패: {e}")
            time.sleep(2)
    return ""


def style_transfer(original: str, ep_num: int) -> str:
    """기존 원고에 문체 DNA 적용 - 분량 유지 버전"""
    original_len = len(original)
    min_len = int(original_len * 0.93)
    prompt = f"""당신은 한국 웹소설 전문 리라이터입니다.

## 임무
아래 [원본 원고]의 **내용을 100% 유지**하면서, [문체 DNA]에 맞게 **문체만 교체**하세요.

## 핵심: 분량 유지 전략
- 원본: {original_len:,}자. 결과물은 **최소 {min_len:,}자 이상** 필수.
- 미사여구/배경묘사를 줄인 만큼 → **대화문을 추가**하여 분량 보존
- 서술로 설명하던 정보 → 등장인물 간 대화로 전환 (대화비율 40~50% 목표)
- 내면독백을 짧고 날카롭게 바꾸되, 삭제하지 말 것

## 절대 규칙
1. 플롯, 사건, 대화 내용, 캐릭터 행동을 절대 변경하지 마라
2. 새로운 장면이나 캐릭터를 추가하지 마라
3. 기존 장면이나 대화를 삭제하지 마라
4. 고유명사(인물명, 기업명, 지명)를 변경하지 마라
5. %%%% 또는 *** 장면 구분선 그대로 유지
6. 제목 행(제N화. ~) 그대로 유지

## 변경 대상
- "마치 ~처럼", "~인 듯", "~하는 것만 같았다" → 삭제하고 직접적 서술
- 감정/풍경 미사여구 → 행동/대사로 대체
- 설명조 나레이션 → 캐릭터 대화로 정보 전달
- 만연체(접속사 연결 장문) → 단문으로 끊기
- 추상적 수치 → 구체적 숫자 명시

## [문체 DNA]
{STYLE_PROMPT}

## [원본 원고] (제{ep_num}화)
{original}

## 출력
리라이트된 원고 전문만 출력하세요. 설명이나 주석 없이 원고 텍스트만.
반드시 {min_len:,}자 이상 작성할 것.
"""
    return generate_with_fallback(prompt)


# ── 메인 루프 ──
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
success = 0
failed = 0

for ep in range(START_EP, END_EP + 1):
    input_file = INPUT_DIR / f"ep_{ep:04d}.txt"
    output_file = OUTPUT_DIR / f"ep_{ep:04d}.txt"

    if not input_file.exists():
        print(f"[SKIP] ep_{ep:04d}.txt 없음")
        continue

    if output_file.exists():
        print(f"[SKIP] ep_{ep:04d}.txt 이미 완료")
        success += 1
        continue

    original = input_file.read_text(encoding='utf-8')
    original_len = len(original)

    print(f"\n[{ep:04d}] 처리 중... (원본 {original_len:,}자)", flush=True)

    result = style_transfer(original, ep)

    if result and len(result) > 1000:
        output_file.write_text(result, encoding='utf-8')
        result_len = len(result)
        ratio = result_len / original_len * 100
        print(f"  -> 완료: {result_len:,}자 ({ratio:.0f}%)")
        success += 1
    else:
        print(f"  -> [FAIL] 결과 없음 또는 너무 짧음")
        failed += 1

    time.sleep(1)  # rate limit

print(f"\n{'='*60}")
print(f"완료: {success}편 성공, {failed}편 실패")
print(f"출력: {OUTPUT_DIR}")
