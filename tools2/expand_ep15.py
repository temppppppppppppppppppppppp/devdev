"""EP15 확장 - 중복 제거 후 분량 채우기"""
import os, sys, json, sqlite3
from pathlib import Path
from dotenv import load_dotenv

# [manual-only] Host-bound helper. Not part of the live app/runtime path.

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types

# DB에서 스타일 가이드 + EP15 원고 로드
conn = sqlite3.connect("projects/재벌물/project_data.db")
cur = conn.cursor()

cur.execute("SELECT data FROM anchors WHERE key = 'style_guide'")
row = cur.fetchone()
from modules.core.stage0.style_extractor import StyleGuide
guide = StyleGuide.from_dict(json.loads(row[0]))
STYLE_PROMPT = guide.to_prompt()

cur.execute("SELECT content FROM manuscripts WHERE ep_num=15")
original = cur.fetchone()[0]
conn.close()

# 첫 %%%% 이전 부분만 추출
lines = original.split('\n')
cut_idx = next(i for i, l in enumerate(lines) if '%%%%' in l)
first_half = '\n'.join(lines[:cut_idx]).rstrip()

print(f"Style Guide: {len(STYLE_PROMPT)} chars")
print(f"EP15 first half: {len(first_half):,} chars")
print("=" * 60)

# LLM 호출
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODELS = ["gemini-3-pro-preview", "gemini-2.5-pro", "gemini-2.5-flash"]

prompt = f"""당신은 한국 웹소설 전문 작가입니다.

## 임무
아래 [기존 원고]는 제15화의 **전반부**입니다.
이 원고의 내용을 **100% 유지**하면서, 후반부를 추가하여 **완성된 한 편의 에피소드**로 만드세요.

## 배경 설명
- 주인공 한시우는 IMF 외환위기를 이용해 한국에서 막대한 부를 쌓은 회귀자(미래 기억 보유)
- 15화는 한국 편의 마무리. 다음 16화부터 미국 실리콘밸리 편이 시작됨
- 15화 제목: "굿바이, IMF"

## 추가할 후반부 내용 (마음다짐 + 한국 마무리)
기존 원고 뒤에 이어서 다음 내용을 자연스럽게 추가:
1. 행정관이 떠난 뒤, 최강석과 한시우의 대화 - 미국행 준비 상황 점검
2. 한시우가 혼자 사무실에서 지난 1년반을 회고 - IMF 때 어떻게 여기까지 왔는지 간단 회상
3. 퇴근길 또는 밤, 서울 야경을 보며 마음다짐 - "이 나라는 이제 괜찮다. 내 무대는 더 넓어져야 한다"는 결의
4. 마지막: 미국행을 앞두고 긴장감과 기대감이 공존하는 엔딩

## 절대 규칙
1. 기존 원고의 모든 대사와 사건을 그대로 유지
2. 공항 장면, 비행기 장면, 미국 도착 장면은 절대 쓰지 마라 (16화에서 다룸)
3. 스티브 잡스를 직접 만나는 장면 쓰지 마라 (16화 이후에서 다룸)
4. 분량: 전체 4,800~5,200자
5. 고유명사 유지: 한시우, 최강석, 댄 킴, SW 인베스트먼트, 송경반도체
6. *** 로 장면 구분 (%%%% 사용 금지)
7. 에피소드 제목 "제15화. 굿바이, IMF" 유지

## [문체 DNA]
{STYLE_PROMPT}

## [기존 원고 - 전반부]
{first_half}

## 출력
완성된 제15화 전문을 출력하세요. 기존 전반부 + 새로운 후반부를 합쳐서 하나의 원고로.
설명이나 주석 없이 원고 텍스트만 출력.
"""

result = None
for model in MODELS:
    try:
        print(f"Trying {model}...")
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=16000,
            )
        )
        if response.text and len(response.text) > 3000:
            result = response.text
            print(f"  -> OK: {len(result):,} chars from {model}")
            break
        else:
            print(f"  -> Too short: {len(response.text or '')} chars")
    except Exception as e:
        print(f"  -> Failed: {e}")

if result:
    # 결과 저장 (테스트용)
    out_path = Path("tools2/ep15_expanded.txt")
    out_path.write_text(result, encoding='utf-8')
    print(f"\nSaved to {out_path}")
    print(f"Total: {len(result):,} chars")

    # 마지막 10줄 미리보기
    result_lines = result.strip().split('\n')
    print(f"Lines: {len(result_lines)}")
    print("\n--- Last 10 lines ---")
    for l in result_lines[-10:]:
        print(l)
else:
    print("\n[FAIL] All models failed")
