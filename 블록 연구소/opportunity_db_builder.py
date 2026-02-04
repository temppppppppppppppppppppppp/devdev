#!/usr/bin/env python3
"""
기회 DB 구축 도구
- 회귀물/재벌물용 역사적 투자/사업 기회 데이터베이스
- LLM 기반 자동 생성 + 의존성 그래프
"""

import sys
import os
import json
import time
import argparse
import threading
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# 전역 종료 플래그
SHUTDOWN_REQUESTED = False

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ─────────────────────────────────────────────
# 스피너
# ─────────────────────────────────────────────
class Spinner:
    """간단한 CLI 스피너"""
    def __init__(self):
        self.spinning = False
        self.thread = None
        self.message = ""
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0

    def _spin(self):
        while self.spinning:
            frame = self.frames[self.current % len(self.frames)]
            print(f"\r{frame} {self.message}", end="", flush=True)
            self.current += 1
            time.sleep(0.1)

    def start(self, message: str = ""):
        self.message = message
        self.spinning = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def update(self, message: str):
        self.message = message

    def stop(self, final_message: str = None):
        self.spinning = False
        if self.thread:
            self.thread.join()
        if final_message:
            print(f"\r✓ {final_message}          ")
        else:
            print(f"\r✓ {self.message}          ")


spinner = Spinner()

# Google AI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
PRIMARY_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "gemini-2.5-flash"

CATEGORIES = {
    "real_estate": {
        "name": "부동산",
        "subcategories": ["재개발", "분양", "경매", "상가", "토지"]
    },
    "stock": {
        "name": "주식/금융",
        "subcategories": ["IPO", "우량주", "작전주", "선물/옵션", "채권"]
    },
    "forex_commodity": {
        "name": "외환/원자재",
        "subcategories": ["환율", "금", "석유", "원자재"]
    },
    "crypto": {
        "name": "암호화폐",
        "subcategories": ["비트코인", "알트코인", "ICO", "NFT"]
    },
    "it_tech": {
        "name": "IT/기술",
        "subcategories": ["인터넷", "모바일", "반도체", "AI", "플랫폼"]
    },
    "manufacturing": {
        "name": "제조업",
        "subcategories": ["자동차", "배터리", "디스플레이", "조선", "철강"]
    },
    "retail_distribution": {
        "name": "유통/소매",
        "subcategories": ["홈쇼핑", "이커머스", "편의점", "프랜차이즈"]
    },
    "content_media": {
        "name": "콘텐츠/미디어",
        "subcategories": ["게임", "엔터테인먼트", "웹툰/웹소설", "방송"]
    },
    "finance_service": {
        "name": "금융서비스",
        "subcategories": ["보험", "카드", "핀테크", "대부업"]
    },
    "crisis_event": {
        "name": "위기/이벤트",
        "subcategories": ["IMF", "금융위기", "버블붕괴", "팬데믹", "전쟁"]
    }
}

# 시대별 범위
ERA_RANGES = [
    {"name": "1970년대", "start": 1970, "end": 1979},
    {"name": "1980년대", "start": 1980, "end": 1989},
    {"name": "1990년대", "start": 1990, "end": 1999},
    {"name": "2000년대", "start": 2000, "end": 2009},
    {"name": "2010년대", "start": 2010, "end": 2019},
    {"name": "2020년대", "start": 2020, "end": 2025},
]

# ─────────────────────────────────────────────
# 스키마
# ─────────────────────────────────────────────
OPPORTUNITY_SCHEMA = '''
{
  "id": "OPP_XXX",
  "name": "기회 이름 (구체적이고 시점 포함, 예: '삼성전자 IPO 투자 (1975)', '강남 재개발 초기 매입 (1980년대)')",
  "category": "대분류",
  "subcategory": "소분류",

  "entity": {
    "type": "company/asset/market/event/policy",
    "name": "핵심 엔티티명 (예: 삼성전자, 강남부동산, 비트코인, IMF)",
    "sector": "산업/분야 (예: 반도체, 부동산, 암호화폐)"
  },

  "entry_phase": "initial/growth/peak/decline/revival (이 시점에 진입하면 어느 단계인지)",

  "timeline": {
    "real_event_year": 실제 발생/피크 연도(정수),
    "korea_timing": 한국 기준 연도(정수),
    "earliest_possible": 기술적으로 가능한 최초 연도(정수),
    "golden_window": {"start": 시작연도, "end": 종료연도},
    "obsolete_after": 더이상 유효하지 않은 연도(정수 또는 null)
  },

  "requirements": {
    "min_capital": "최소 자본금 (한글, 예: 1억, 100억, 1조)",
    "capital_tier": "개인/소규모/중소기업/대기업/재벌급",
    "prerequisites": [
      {"name": "선행조건1", "critical": true/false},
      {"name": "선행조건2", "critical": true/false}
    ],
    "skills_needed": ["필요 역량1", "필요 역량2"],
    "legal_barriers": ["법적 장벽1", "법적 장벽2"],
    "time_to_execute": "실행까지 예상 기간"
  },

  "returns": {
    "profit_type": "수익 유형 (시세차익/배당/사업수익/독점수익 등)",
    "profit_timeline": "수익 실현 시점",
    "peak_roi": "최대 수익률 (예: 500%, 10배, 100배)",
    "risk_level": "low/medium/high/extreme",
    "failure_probability": 0.0~1.0 사이 실수
  },

  "historical_context": {
    "real_winner": "실제 역사에서 성공한 주체",
    "real_losers": ["실패한 주체들"],
    "why_others_failed": "다른 이들이 실패한 이유",
    "key_insight": "핵심 통찰 (회귀자가 알아야 할 것)"
  },

  "story_hooks": {
    "conflicts": ["주요 갈등 요소1", "주요 갈등 요소2"],
    "complications": ["예상치 못한 문제1", "문제2"],
    "dramatic_moments": ["극적인 순간1", "순간2"],
    "villain_candidates": ["잠재적 악역1", "악역2"]
  },

  "regression_notes": {
    "future_knowledge_value": "low/medium/high/very_high",
    "butterfly_risk": "low/medium/high (역사 변동 위험)",
    "detection_risk": "low/medium/high (미래지식 들킬 위험)",
    "alt_history_impact": "역사가 바뀌면 어떻게 되는지"
  },

  "related_opportunities": ["연관 기회 이름1", "연관 기회 이름2"],
  "enables": ["이 기회가 열어주는 후속 기회1", "후속 기회2"],
  "tags": ["태그1", "태그2", "태그3"]
}
'''

# ─────────────────────────────────────────────
# LLM 클래스
# ─────────────────────────────────────────────
class OpportunityLLM:
    def __init__(self, api_key: str, model: str = PRIMARY_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, temperature: float = 0.7) -> Optional[dict]:
        """JSON 응답 생성"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json"
                )
            )
            text = response.text.strip()
            return json.loads(text)
        except Exception as e:
            print(f"  [!] LLM 오류: {e}")
            return None

    def generate_text(self, prompt: str, temperature: float = 0.7) -> Optional[str]:
        """텍스트 응답 생성"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature
                )
            )
            return response.text.strip()
        except Exception as e:
            print(f"  [!] LLM 오류: {e}")
            return None


# ─────────────────────────────────────────────
# 기회 생성 프롬프트
# ─────────────────────────────────────────────
def build_category_prompt(category_key: str, category_info: dict, era: dict) -> str:
    """카테고리+시대별 기회 생성 프롬프트"""
    return f'''당신은 한국 경제사 전문가입니다.

## 작업
{era["name"]} ({era["start"]}~{era["end"]}) 한국에서 있었던 **{category_info["name"]}** 분야의
주요 투자/사업 기회를 5~10개 생성해주세요.

## 소분류 참고
{", ".join(category_info["subcategories"])}

## 요구사항
1. **실제 역사적 사실**에 기반할 것
2. 회귀물 소설에서 활용 가능한 구체적 기회
3. 다양한 자본 규모 (개인~재벌급) 포함
4. 성공 사례와 실패 사례 모두 포함

## 출력 형식
다음 JSON 스키마를 정확히 따라주세요:

{{"opportunities": [
{OPPORTUNITY_SCHEMA}
]}}

## 주의사항
- id는 "OPP_" + 3자리 숫자 (예: OPP_001)
- 모든 연도는 정수로
- 한국 상황에 맞게 (글로벌 이벤트도 한국 관점에서)
- related_opportunities, enables는 이름으로 (나중에 연결)

{era["name"]} {category_info["name"]} 분야 기회들을 생성해주세요.
'''


def build_dependency_prompt(opportunities: list) -> str:
    """의존성 그래프 생성 프롬프트"""
    opp_list = "\n".join([f"- {o['id']}: {o['name']} ({o['timeline']['korea_timing']})"
                          for o in opportunities])

    return f'''다음은 회귀물용 기회 목록입니다:

{opp_list}

## 작업
이 기회들 간의 **의존성 관계**를 분석해주세요.

의존성이란:
- A를 해야 B가 가능해지는 관계
- A에서 번 돈/경험/인맥이 B의 선행조건이 되는 관계

## 출력 형식
```json
{{
  "dependencies": [
    {{"from": "OPP_001", "to": "OPP_005", "relation": "자본축적", "description": "부동산으로 번 돈이 사업 자본금이 됨"}},
    {{"from": "OPP_003", "to": "OPP_007", "relation": "기술축적", "description": "PC 경험이 인터넷 사업의 기반"}}
  ]
}}
```

relation 유형:
- 자본축적: 돈이 필요
- 기술축적: 기술/노하우 필요
- 인맥축적: 네트워크/관계 필요
- 시장선점: 먼저 자리잡아야 함
- 라이선스: 사업권/허가 필요

명확한 의존관계만 추출해주세요.
'''


# ─────────────────────────────────────────────
# 메인 빌더
# ─────────────────────────────────────────────
class OpportunityDBBuilder:
    def __init__(self, api_key: str, output_dir: Path, model: str = PRIMARY_MODEL):
        self.llm = OpportunityLLM(api_key, model)
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.db = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "model": model,
            "opportunities": [],
            "dependencies": [],
            "categories": CATEGORIES,
            "era_ranges": ERA_RANGES
        }

        self.id_counter = 1

    def generate_category_era(self, category_key: str, era: dict, progress_str: str = "") -> list:
        """특정 카테고리+시대의 기회 생성"""
        category_info = CATEGORIES[category_key]

        spinner.start(f"{progress_str} [{era['name']}] {category_info['name']} 생성 중...")

        prompt = build_category_prompt(category_key, category_info, era)
        result = self.llm.generate(prompt, temperature=0.8)

        if not result or "opportunities" not in result:
            spinner.stop(f"{progress_str} [{era['name']}] {category_info['name']} - 실패!")
            return []

        opportunities = result["opportunities"]

        # ID 재할당 (중복 방지)
        for opp in opportunities:
            opp["id"] = f"OPP_{self.id_counter:03d}"
            opp["_source_category"] = category_key
            opp["_source_era"] = era["name"]
            self.id_counter += 1

        spinner.stop(f"{progress_str} [{era['name']}] {category_info['name']} - {len(opportunities)}개")
        return opportunities

    def generate_all(self, categories: list = None, eras: list = None):
        """전체 생성"""
        if categories is None:
            categories = list(CATEGORIES.keys())
        if eras is None:
            eras = ERA_RANGES

        # 이미 완료된 조합 확인
        completed = set()
        for opp in self.db["opportunities"]:
            key = (opp.get("_source_category"), opp.get("_source_era"))
            completed.add(key)

        total = len(categories) * len(eras)
        current = 0
        skipped = 0

        for category_key in categories:
            # 종료 요청 확인
            if SHUTDOWN_REQUESTED:
                print(f"\n⚠️  중단 요청됨. 현재까지 {len(self.db['opportunities'])}개 저장 중...")
                break

            print(f"\n{'='*50}")
            print(f"[{CATEGORIES[category_key]['name']}]")
            print(f"{'='*50}")

            for era in eras:
                # 종료 요청 확인
                if SHUTDOWN_REQUESTED:
                    break

                current += 1
                progress_str = f"({current}/{total})"

                # 이미 완료된 조합이면 스킵
                if (category_key, era["name"]) in completed:
                    print(f"  {progress_str} [{era['name']}] - 이미 완료, 스킵")
                    skipped += 1
                    continue

                opportunities = self.generate_category_era(category_key, era, progress_str)
                self.db["opportunities"].extend(opportunities)

                # Rate limit 방지
                time.sleep(1)

            # 카테고리 끝날 때마다 중간 저장
            self._auto_save()

        if skipped > 0:
            print(f"\n  (스킵: {skipped}개 조합 이미 완료)")

        print(f"\n{'='*50}")
        print(f"기회 생성 완료: 총 {len(self.db['opportunities'])}개")
        print(f"{'='*50}")

    def _auto_save(self):
        """중간 저장"""
        backup_path = self.output_dir / "opportunity_db_backup.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        print(f"  [자동저장] {len(self.db['opportunities'])}개 → {backup_path.name}")

    def generate_dependencies(self):
        """의존성 그래프 생성"""
        if len(self.db["opportunities"]) == 0:
            print("기회가 없습니다.")
            return

        print(f"\n{'='*50}")
        print("의존성 그래프 생성")
        print(f"{'='*50}")

        total_eras = len([e for e in ERA_RANGES if len([o for o in self.db["opportunities"] if o.get("_source_era") == e["name"]]) >= 2])
        current_era = 0

        # 시대별로 묶어서 처리 (한번에 너무 많으면 품질 저하)
        for era in ERA_RANGES:
            era_opps = [o for o in self.db["opportunities"]
                       if o.get("_source_era") == era["name"]]

            if len(era_opps) < 2:
                continue

            current_era += 1
            spinner.start(f"({current_era}/{total_eras}) [{era['name']}] {len(era_opps)}개 기회 의존성 분석 중...")

            prompt = build_dependency_prompt(era_opps)
            result = self.llm.generate(prompt, temperature=0.5)

            if result and "dependencies" in result:
                self.db["dependencies"].extend(result["dependencies"])
                spinner.stop(f"({current_era}/{total_eras}) [{era['name']}] - {len(result['dependencies'])}개 의존성")
            else:
                spinner.stop(f"({current_era}/{total_eras}) [{era['name']}] - 실패")

            time.sleep(1)

        print(f"\n의존성 관계 완료: 총 {len(self.db['dependencies'])}개")

    def save(self):
        """저장"""
        # 메인 DB
        db_path = self.output_dir / "opportunity_db.json"
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        print(f"\n저장: {db_path}")

        # 의존성 그래프 (별도)
        if self.db["dependencies"]:
            graph_path = self.output_dir / "dependency_graph.json"
            graph = {
                "nodes": [{"id": o["id"], "name": o["name"], "year": o["timeline"]["korea_timing"]}
                         for o in self.db["opportunities"]],
                "edges": self.db["dependencies"]
            }
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(graph, f, ensure_ascii=False, indent=2)
            print(f"저장: {graph_path}")

        # 통계
        stats_path = self.output_dir / "build_stats.json"
        stats = {
            "total_opportunities": len(self.db["opportunities"]),
            "total_dependencies": len(self.db["dependencies"]),
            "by_category": {},
            "by_era": {},
            "created": datetime.now().isoformat()
        }
        for opp in self.db["opportunities"]:
            cat = opp.get("_source_category", "unknown")
            era = opp.get("_source_era", "unknown")
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            stats["by_era"][era] = stats["by_era"].get(era, 0) + 1

        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"저장: {stats_path}")

    def load_existing(self, path: Path) -> bool:
        """기존 DB 로드"""
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                self.db = json.load(f)
            self.id_counter = len(self.db.get("opportunities", [])) + 1
            print(f"기존 DB 로드: {len(self.db['opportunities'])}개 기회")
            return True
        return False


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="회귀물용 기회 DB 구축")
    parser.add_argument("--output", "-o", default="libraries/_opportunity_db", help="출력 폴더")
    parser.add_argument("--model", "-m", default=PRIMARY_MODEL, help=f"모델 (기본: {PRIMARY_MODEL})")
    parser.add_argument("--categories", "-c", nargs="+", help="특정 카테고리만 (예: real_estate stock)")
    parser.add_argument("--eras", "-e", nargs="+", help="특정 시대만 (예: 1980년대 1990년대)")
    parser.add_argument("--skip-deps", action="store_true", help="의존성 그래프 생성 스킵")
    parser.add_argument("--resume", "-r", action="store_true", help="기존 DB에 이어서 추가")
    args = parser.parse_args()

    # API 키
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("GOOGLE_API_KEY 없음")
        sys.exit(1)

    output_dir = Path(args.output)

    # 카테고리 필터
    categories = args.categories if args.categories else list(CATEGORIES.keys())

    # 시대 필터
    eras = ERA_RANGES
    if args.eras:
        eras = [e for e in ERA_RANGES if e["name"] in args.eras]

    # Ctrl+C 핸들러
    def signal_handler(sig, frame):
        global SHUTDOWN_REQUESTED
        if SHUTDOWN_REQUESTED:
            print("\n\n강제 종료!")
            sys.exit(1)
        print("\n\n⚠️  Ctrl+C 감지! 현재 작업 완료 후 저장하고 종료합니다...")
        print("   (한번 더 누르면 강제 종료)")
        SHUTDOWN_REQUESTED = True

    signal.signal(signal.SIGINT, signal_handler)

    # 배너
    print()
    print("=" * 55)
    print("  기회 DB 구축 도구 (회귀물/재벌물 전용)")
    print("=" * 55)
    print(f"  모델     : {args.model}")
    print(f"  출력     : {output_dir}")
    print(f"  카테고리 : {len(categories)}개")
    for cat_key in categories:
        print(f"             - {CATEGORIES[cat_key]['name']}")
    print(f"  시대     : {len(eras)}개")
    for era in eras:
        print(f"             - {era['name']}")
    print(f"  총 작업  : {len(categories) * len(eras)}번 LLM 호출 예정")
    print("-" * 55)
    print("  💡 Ctrl+C로 중단해도 진행분 자동 저장됨")
    print("  💡 --resume 옵션으로 이어서 가능")
    print("=" * 55)
    print()

    builder = OpportunityDBBuilder(api_key, output_dir, args.model)

    # 기존 DB 로드
    if args.resume:
        builder.load_existing(output_dir / "opportunity_db.json")

    # 생성
    builder.generate_all(categories, eras)

    # 의존성 (중단 안 됐을 때만)
    if not args.skip_deps and not SHUTDOWN_REQUESTED:
        builder.generate_dependencies()

    # 저장
    builder.save()

    print()
    print("=" * 55)
    print("  완료!")
    print("=" * 55)


if __name__ == "__main__":
    main()
