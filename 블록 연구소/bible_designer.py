#!/usr/bin/env python3
"""
Bible & Block 자동 설계 도구 v2.0
- 스키마 고정 + LLM 보조 생성
- 입력 모드: 자동/선택/직접입력
- block_schema.json 연동 (장르별 Core + Extension)
- opportunity_db.json 연동 (역사적 기회 추천)
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, List, Dict
from dotenv import load_dotenv

# Windows UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Google AI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai not installed")

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
PRIMARY_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "gemini-2.5-flash"

# 외부 스키마/DB 경로
BLOCK_SCHEMA_PATH = Path(__file__).parent.parent / "libraries" / "_core" / "block_schema.json"
OPPORTUNITY_DB_PATH = Path(__file__).parent.parent / "libraries" / "_opportunity_db" / "opportunity_db.json"


# ─────────────────────────────────────────────
# 외부 스키마/DB 로더
# ─────────────────────────────────────────────
class BlockSchemaLoader:
    """block_schema.json 로더 - 장르별 Core + Extension"""

    def __init__(self, schema_path: Path = BLOCK_SCHEMA_PATH):
        self.schema = {}
        self.core = {}
        self.extensions = {}

        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self.schema = json.load(f)
            self.core = self.schema.get("core", {}).get("fields", {})
            self.extensions = self.schema.get("extensions", {})
            print(f"  ✓ block_schema.json 로드됨")
            print(f"    - Core 필드: {len(self.core)}개")
            print(f"    - Extensions: {list(self.extensions.keys())}")
        else:
            print(f"  ⚠ block_schema.json 없음: {schema_path}")

    def get_genre_schema(self, genre_tags: List[str]) -> Dict:
        """장르 태그에 맞는 스키마 반환 (Core + 해당 Extension)"""
        schema = {"core": self.core}

        # 장르 매핑
        genre_map = {
            "재벌": "investment",
            "투자": "investment",
            "회귀": "regression",
            "무협": "wuxia",
            "헌터": "hunter",
            "던전": "hunter",
            "게이트": "hunter"
        }

        for tag in genre_tags:
            ext_key = genre_map.get(tag)
            if ext_key and ext_key in self.extensions:
                schema[ext_key] = self.extensions[ext_key].get("fields", {})

        return schema

    def get_block_template(self, genre_tags: List[str]) -> Dict:
        """장르에 맞는 빈 블록 템플릿 생성"""
        schema = self.get_genre_schema(genre_tags)
        template = {"core": {}}

        # Core 필드 초기화
        for key in self.core.keys():
            template["core"][key] = None

        # Extension 필드 초기화
        for ext_name, ext_fields in schema.items():
            if ext_name != "core":
                template[ext_name] = {}
                for key in ext_fields.keys():
                    template[ext_name][key] = None

        return template


class OpportunityDB:
    """opportunity_db.json 로더 - 역사적 기회 추천"""

    def __init__(self, db_path: Path = OPPORTUNITY_DB_PATH):
        self.db = {}
        self.opportunities = []

        if db_path.exists():
            with open(db_path, "r", encoding="utf-8") as f:
                self.db = json.load(f)
            self.opportunities = self.db.get("opportunities", [])
            print(f"  ✓ opportunity_db.json 로드됨: {len(self.opportunities)}개 기회")
        else:
            print(f"  ⚠ opportunity_db.json 없음: {db_path}")
            print(f"    → opportunity_db_builder.py로 생성하세요")

    def query(self, year: int = None, capital_tier: str = None,
              category: str = None, limit: int = 10) -> List[Dict]:
        """조건에 맞는 기회 검색"""
        results = []

        for opp in self.opportunities:
            # 연도 필터
            if year:
                timeline = opp.get("timeline", {})
                earliest = timeline.get("earliest_possible", 9999)
                obsolete = timeline.get("obsolete_after", 9999) or 9999
                if not (earliest <= year <= obsolete):
                    continue

            # 자본 필터
            if capital_tier:
                req_tier = opp.get("requirements", {}).get("capital_tier", "")
                tier_order = ["개인", "소규모", "중소기업", "대기업", "재벌급"]
                try:
                    req_idx = tier_order.index(req_tier) if req_tier in tier_order else 0
                    cap_idx = tier_order.index(capital_tier) if capital_tier in tier_order else 0
                    if req_idx > cap_idx:
                        continue
                except:
                    pass

            # 카테고리 필터
            if category:
                if opp.get("category", "") != category:
                    continue

            results.append(opp)

            if len(results) >= limit:
                break

        return results

    def get_opportunity_path(self, start_year: int, goal: str,
                             start_capital: str = "개인") -> List[Dict]:
        """목표까지의 기회 경로 추천"""
        # 간단한 경로 추천 (의존성 그래프 기반은 추후 구현)
        available = self.query(year=start_year, capital_tier=start_capital, limit=20)

        # 목표 관련 키워드로 필터
        goal_keywords = goal.lower().split()
        scored = []

        for opp in available:
            score = 0
            opp_text = json.dumps(opp, ensure_ascii=False).lower()
            for kw in goal_keywords:
                if kw in opp_text:
                    score += 1

            if score > 0:
                scored.append((score, opp))

        # 점수순 정렬
        scored.sort(key=lambda x: -x[0])
        return [opp for _, opp in scored[:5]]

    def format_opportunity_for_prompt(self, opp: Dict) -> str:
        """기회를 프롬프트용 텍스트로 변환"""
        timeline = opp.get("timeline", {})
        req = opp.get("requirements", {})
        returns = opp.get("returns", {})
        hooks = opp.get("story_hooks", {})

        return f"""
【{opp.get('name', '?')}】
- 카테고리: {opp.get('category', '?')} / {opp.get('subcategory', '?')}
- 시기: {timeline.get('golden_window', {}).get('start', '?')}~{timeline.get('golden_window', {}).get('end', '?')}
- 필요자본: {req.get('min_capital', '?')} ({req.get('capital_tier', '?')})
- 예상수익: {returns.get('peak_roi', '?')}
- 위험도: {returns.get('risk_level', '?')}
- 핵심통찰: {opp.get('historical_context', {}).get('key_insight', '?')}
- 갈등요소: {', '.join(hooks.get('conflicts', [])[:3])}
"""

# ─────────────────────────────────────────────
# 고정 스키마
# ─────────────────────────────────────────────
BIBLE_SCHEMA = {
    "meta": {
        "title": "",
        "genre_tags": [],
        "target_episodes": 0,
        "episode_length": 0,
        "created_at": ""
    },
    "timeline": {
        "start_year": 0,
        "regression_from_year": None,
        "story_span_years": 0
    },
    "protagonist": {
        "name": "",
        "age_at_start": 0,
        "archetype": "",
        "personality_tags": [],
        "fatal_flaw": "",
        "past_life": {
            "profession": "",
            "expertise": [],
            "death_cause": ""
        },
        "current_life": {
            "family_position": "",
            "starting_capital": "",
            "starting_connections": "",
            "starting_reputation": ""
        },
        "regression_abilities": {
            "memory_clarity": "",
            "knowledge_areas": [],
            "proof_items": []
        },
        "goals": {
            "ultimate_goal": "",
            "motivation": "",
            "success_condition": ""
        }
    },
    "family": {
        "family_name": "",
        "family_rank": "",
        "family_business": "",
        "family_atmosphere": "",
        "members": []
    },
    "allies": [],
    "rivals": [],
    "romance": {
        "type": "",
        "interests": []
    },
    "world_state": {
        "era_description": "",
        "major_events_upcoming": [],
        "business_landscape": "",
        "political_climate": ""
    },
    "tone": {
        "overall": "",
        "comedy_ratio": "",
        "realism_level": "",
        "violence_level": ""
    }
}

BLOCK_SCHEMA = {
    "initial_arc": {
        "episodes": {"start": 1, "end": 0},
        "title": "",
        "objectives": [],
        "first_business": {
            "type": "",
            "capital_needed": "",
            "expected_return": "",
            "timeline": ""
        },
        "key_events": [],
        "character_introductions": [],
        "conflicts": [],
        "ending_state": ""
    },
    "expansion_strategy": {
        "type": "",
        "description": "",
        "target_industries": []
    },
    "final_arc": {
        "episodes": {"start": 0, "end": 0},
        "title": "",
        "final_enemy": {
            "name": "",
            "type": "",
            "threat_level": "",
            "motivation": ""
        },
        "showdown_type": "",
        "victory_condition": "",
        "ending_type": "",
        "loose_ends": []
    }
}


# ─────────────────────────────────────────────
# LLM 클래스
# ─────────────────────────────────────────────
class DesignerLLM:
    def __init__(self, api_key: str, model: str = PRIMARY_MODEL,
                 opportunity_db: OpportunityDB = None,
                 block_schema: BlockSchemaLoader = None):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.context = {}  # 누적 컨텍스트
        self.opportunity_db = opportunity_db
        self.block_schema = block_schema

    def set_context(self, key: str, value: Any):
        """컨텍스트 저장 (이후 생성에 반영)"""
        self.context[key] = value

    def generate_options(self, field_name: str, field_description: str, count: int = 4) -> list:
        """선택지 생성"""
        context_str = json.dumps(self.context, ensure_ascii=False, indent=2) if self.context else "없음"

        prompt = f"""당신은 웹소설 기획 전문가입니다.

## 현재까지 설정된 컨텍스트
{context_str}

## 작업
"{field_name}" 항목에 대한 선택지 {count}개를 생성해주세요.
설명: {field_description}

## 출력 형식 (JSON)
{{"options": [
  {{"label": "선택지 제목", "value": "저장될 값", "description": "설명"}},
  ...
]}}

컨텍스트에 맞는 창의적이고 다양한 선택지를 제안해주세요.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return result.get("options", [])
        except Exception as e:
            print(f"  [!] 선택지 생성 실패: {e}")
            return []

    def auto_generate(self, field_name: str, field_description: str, expected_type: str = "string") -> Any:
        """자동 생성"""
        context_str = json.dumps(self.context, ensure_ascii=False, indent=2) if self.context else "없음"

        type_hint = {
            "string": "문자열",
            "number": "숫자",
            "list": "배열 (JSON 배열 형태)",
            "object": "객체 (JSON 객체 형태)"
        }.get(expected_type, "문자열")

        prompt = f"""당신은 웹소설 기획 전문가입니다.

## 현재까지 설정된 컨텍스트
{context_str}

## 작업
"{field_name}" 항목을 자동 생성해주세요.
설명: {field_description}
기대 타입: {type_hint}

## 출력 형식 (JSON)
{{"value": 생성된_값}}

컨텍스트와 잘 어울리는 값을 생성해주세요.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return result.get("value")
        except Exception as e:
            print(f"  [!] 자동 생성 실패: {e}")
            return None

    def generate_family_members(self, family_info: dict) -> list:
        """가족 구성원 생성"""
        context_str = json.dumps(self.context, ensure_ascii=False, indent=2)

        prompt = f"""당신은 웹소설 기획 전문가입니다.

## 현재까지 설정
{context_str}

## 가문 정보
{json.dumps(family_info, ensure_ascii=False, indent=2)}

## 작업
가족 구성원들을 생성해주세요. 주인공과의 관계, 갈등 요소, 성격 등을 포함.

## 출력 형식 (JSON)
{{"members": [
  {{
    "name": "이름",
    "relation": "관계 (아버지/어머니/형/누나/동생 등)",
    "age": 나이,
    "personality": "성격",
    "stance_to_protagonist": "주인공에 대한 태도 (협조적/중립/적대적)",
    "role_in_story": "스토리에서의 역할",
    "potential_conflict": "잠재적 갈등 요소"
  }},
  ...
]}}

재벌가 드라마에 맞는 복잡한 가족 관계를 만들어주세요.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return result.get("members", [])
        except Exception as e:
            print(f"  [!] 가족 생성 실패: {e}")
            return []

    def generate_npcs(self, npc_type: str, count: int = 3) -> list:
        """NPC (조력자/라이벌) 생성"""
        context_str = json.dumps(self.context, ensure_ascii=False, indent=2)

        role_desc = "주인공을 돕는 조력자" if npc_type == "ally" else "주인공과 대립하는 라이벌"

        prompt = f"""당신은 웹소설 기획 전문가입니다.

## 현재까지 설정
{context_str}

## 작업
{role_desc} {count}명을 생성해주세요.

## 출력 형식 (JSON)
{{"npcs": [
  {{
    "name": "이름",
    "role": "역할 (비서/변호사/투자파트너/경쟁사 후계자 등)",
    "affiliation": "소속",
    "age": 나이,
    "personality": "성격",
    "first_meeting": "주인공과의 첫 만남 상황",
    "motivation": "동기/목적",
    "special_skill": "특기/강점",
    "weakness": "약점",
    "arc_involvement": "주요 활약 시점 (초반/중반/후반)"
  }},
  ...
]}}

다양한 백그라운드와 역할을 가진 캐릭터들을 만들어주세요.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return result.get("npcs", [])
        except Exception as e:
            print(f"  [!] NPC 생성 실패: {e}")
            return []

    def get_opportunity_recommendations(self, year: int, capital_tier: str = "개인",
                                         goal: str = None) -> str:
        """Opportunity DB에서 추천 기회 가져오기"""
        if not self.opportunity_db or not self.opportunity_db.opportunities:
            return ""

        # 연도와 자본에 맞는 기회 검색
        opportunities = self.opportunity_db.query(
            year=year,
            capital_tier=capital_tier,
            limit=5
        )

        if not opportunities:
            return ""

        # 프롬프트용 텍스트 생성
        opp_text = "\n## 활용 가능한 역사적 기회 (참고용)\n"
        opp_text += f"(시작년도 {year}년, 자본규모 {capital_tier} 기준)\n\n"

        for opp in opportunities:
            opp_text += self.opportunity_db.format_opportunity_for_prompt(opp)

        opp_text += "\n※ 위 기회들을 참고하여 현실적이고 드라마틱한 첫 사업을 설계하세요.\n"
        return opp_text

    def generate_initial_arc(self, bible: dict) -> dict:
        """초기 Arc 생성 (Opportunity DB 연동)"""

        # Opportunity DB에서 추천 받기
        start_year = bible.get("timeline", {}).get("start_year", 1985)
        family_rank = bible.get("family", {}).get("family_rank", "ordinary")

        # 가문 규모에 따른 자본 티어 매핑
        rank_to_capital = {
            "top5_chaebol": "재벌급",
            "top10_chaebol": "대기업",
            "mid_chaebol": "중소기업",
            "new_rich": "소규모",
            "ordinary": "개인",
            "fallen": "개인"
        }
        capital_tier = rank_to_capital.get(family_rank, "개인")

        # 추천 기회 텍스트
        opportunity_section = self.get_opportunity_recommendations(start_year, capital_tier)

        prompt = f"""당신은 웹소설 기획 전문가입니다.

## Bible 설정
{json.dumps(bible, ensure_ascii=False, indent=2)}
{opportunity_section}
## 작업
초기 Arc (1화 ~ 약 50화)를 설계해주세요.
- 주인공이 첫 발을 내딛는 과정
- 첫 번째 사업/투자 (위 역사적 기회 참고)
- 주요 캐릭터 소개
- 초기 갈등 구조

## 출력 형식 (JSON)
{{
  "episodes": {{"start": 1, "end": 50}},
  "title": "Arc 제목",
  "objectives": ["목표1", "목표2", ...],
  "first_business": {{
    "type": "사업 유형",
    "opportunity_ref": "참고한 역사적 기회 ID (있으면)",
    "capital_needed": "필요 자본",
    "expected_return": "예상 수익",
    "timeline": "소요 기간",
    "key_steps": ["단계1", "단계2", ...],
    "historical_accuracy": "실제 역사와의 일치도 (high/medium/low)"
  }},
  "key_events": [
    {{"episode": 1, "event": "이벤트 설명", "impact": "영향"}},
    ...
  ],
  "character_introductions": [
    {{"name": "캐릭터명", "episode": 5, "context": "등장 상황"}},
    ...
  ],
  "conflicts": [
    {{"type": "갈등 유형", "parties": ["당사자들"], "resolution_hint": "해결 방향"}},
    ...
  ],
  "ending_state": "초기 Arc 종료 시 상태"
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"  [!] 초기 Arc 생성 실패: {e}")
            return {}

    def generate_final_arc(self, bible: dict, initial_arc: dict) -> dict:
        """말기 Arc 생성 (Opportunity DB 연동)"""

        # 말기 시점의 역사적 배경 추천
        start_year = bible.get("timeline", {}).get("start_year", 1985)
        target_episodes = bible.get("meta", {}).get("target_episodes", 500)

        # 대략적인 말기 연도 추정 (50화당 1년 기준)
        years_span = target_episodes // 50
        final_year = start_year + years_span

        final_opp_section = ""
        if self.opportunity_db and self.opportunity_db.opportunities:
            final_opps = self.opportunity_db.query(year=final_year, capital_tier="재벌급", limit=3)
            if final_opps:
                final_opp_section = f"\n## 말기 시점({final_year}년경)의 역사적 배경\n"
                for opp in final_opps:
                    final_opp_section += f"- {opp.get('name')}: {opp.get('story_hooks', {}).get('conflicts', [''])[0]}\n"

        prompt = f"""당신은 웹소설 기획 전문가입니다.

## Bible 설정
{json.dumps(bible, ensure_ascii=False, indent=2)}

## 초기 Arc (참고)
{json.dumps(initial_arc, ensure_ascii=False, indent=2)}
{final_opp_section}
## 작업
말기 Arc (클라이맥스 ~ 엔딩, 추정 {final_year}년경)를 설계해주세요.
- 최종 보스와의 대결
- 모든 복선 회수
- 결말

## 출력 형식 (JSON)
{{
  "episodes": {{"start": 450, "end": 500}},
  "title": "Arc 제목",
  "final_enemy": {{
    "name": "최종 적 이름",
    "type": "유형 (경쟁사 회장/정치인/외국 자본 등)",
    "organization": "소속",
    "threat_level": "위협 수준",
    "motivation": "적의 동기",
    "resources": ["적의 무기/자원들"],
    "weakness": "약점"
  }},
  "showdown_type": "대결 방식 (경영권 분쟁/M&A/기술전쟁/법정싸움 등)",
  "key_battles": [
    {{"episode": 460, "battle": "전투/대결 설명", "outcome": "결과"}},
    ...
  ],
  "victory_condition": "승리 조건",
  "ending_type": "엔딩 유형 (해피/오픈/비터스윗)",
  "ending_scene": "마지막 장면 설명",
  "epilogue_hints": ["에필로그 힌트들"]
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"  [!] 말기 Arc 생성 실패: {e}")
            return {}


# ─────────────────────────────────────────────
# 인터랙티브 디자이너
# ─────────────────────────────────────────────
class BibleDesigner:
    def __init__(self, llm: DesignerLLM,
                 block_schema: BlockSchemaLoader = None,
                 opportunity_db: OpportunityDB = None):
        self.llm = llm
        self.bible = json.loads(json.dumps(BIBLE_SCHEMA))  # Deep copy
        self.blocks = json.loads(json.dumps(BLOCK_SCHEMA))
        self.block_schema = block_schema
        self.opportunity_db = opportunity_db

    def ask_field(self, field_name: str, description: str,
                  field_type: str = "string",
                  predefined_options: list = None) -> Any:
        """
        필드 입력받기
        - A: 알아서 만들기 (LLM)
        - S: 선택하기 (LLM 추천 or 미리 정의된 선택지)
        - D: 직접 입력
        """
        print(f"\n{'─'*50}")
        print(f"📝 {field_name}")
        print(f"   {description}")
        print(f"{'─'*50}")
        print("   [A] 알아서 만들기 (AI)")
        print("   [S] 선택지에서 고르기")
        print("   [D] 직접 입력")

        while True:
            choice = input("\n선택 (A/S/D): ").strip().upper()

            if choice == 'A':
                # 자동 생성
                print("   ⏳ AI가 생성 중...")
                value = self.llm.auto_generate(field_name, description, field_type)
                if value:
                    print(f"   ✨ 생성됨: {value}")
                    confirm = input("   사용할까요? (Y/n): ").strip().lower()
                    if confirm != 'n':
                        return value
                    else:
                        continue
                else:
                    print("   생성 실패. 다시 선택해주세요.")
                    continue

            elif choice == 'S':
                # 선택지
                if predefined_options:
                    options = predefined_options
                else:
                    print("   ⏳ 선택지 생성 중...")
                    options = self.llm.generate_options(field_name, description)

                if not options:
                    print("   선택지 생성 실패. 직접 입력해주세요.")
                    choice = 'D'
                else:
                    for i, opt in enumerate(options, 1):
                        if isinstance(opt, dict):
                            print(f"   [{i}] {opt.get('label', opt.get('value', ''))}")
                            if opt.get('description'):
                                print(f"       └─ {opt['description']}")
                        else:
                            print(f"   [{i}] {opt}")

                    while True:
                        sel = input("\n   번호 선택: ").strip()
                        try:
                            idx = int(sel) - 1
                            if 0 <= idx < len(options):
                                selected = options[idx]
                                if isinstance(selected, dict):
                                    return selected.get('value', selected.get('label'))
                                return selected
                        except:
                            pass
                        print("   잘못된 선택입니다.")

            if choice == 'D':
                # 직접 입력
                if field_type == "list":
                    print("   (쉼표로 구분하여 입력)")
                    raw = input("   입력: ").strip()
                    return [x.strip() for x in raw.split(",") if x.strip()]
                elif field_type == "number":
                    while True:
                        raw = input("   입력 (숫자): ").strip()
                        try:
                            return int(raw)
                        except:
                            print("   숫자를 입력해주세요.")
                else:
                    return input("   입력: ").strip()

    def design_bible(self):
        """Bible 설계 시작"""
        print("\n" + "="*60)
        print("  📖 Bible 설계 시작")
        print("="*60)

        # 1. 메타 정보
        print("\n\n▶ PART 1: 기본 정보")

        self.bible["meta"]["title"] = self.ask_field(
            "작품 제목",
            "웹소설 제목을 정해주세요"
        )
        self.llm.set_context("title", self.bible["meta"]["title"])

        self.bible["meta"]["genre_tags"] = self.ask_field(
            "장르 태그",
            "장르를 선택해주세요 (회귀, 재벌, 복수, 로맨스 등)",
            field_type="list",
            predefined_options=[
                {"label": "회귀 + 재벌", "value": ["회귀", "재벌", "투자"]},
                {"label": "회귀 + 재벌 + 복수", "value": ["회귀", "재벌", "복수"]},
                {"label": "빙의 + 재벌", "value": ["빙의", "재벌", "가문"]},
                {"label": "현대 + 투자물", "value": ["현대", "투자", "주식"]},
            ]
        )
        self.llm.set_context("genre", self.bible["meta"]["genre_tags"])

        self.bible["meta"]["target_episodes"] = self.ask_field(
            "목표 회차",
            "총 몇 화를 목표로 할까요?",
            field_type="number",
            predefined_options=[
                {"label": "300화 (단편)", "value": 300},
                {"label": "500화 (중편)", "value": 500},
                {"label": "800화 (장편)", "value": 800},
                {"label": "1000화+ (대하)", "value": 1000},
            ]
        )

        # 2. 타임라인
        print("\n\n▶ PART 2: 시간 설정")

        self.bible["timeline"]["start_year"] = self.ask_field(
            "시작 연도",
            "이야기가 시작되는 연도",
            field_type="number",
            predefined_options=[
                {"label": "1980년", "value": 1980},
                {"label": "1985년", "value": 1985},
                {"label": "1990년", "value": 1990},
                {"label": "1997년 (IMF)", "value": 1997},
                {"label": "2000년", "value": 2000},
                {"label": "2008년 (금융위기)", "value": 2008},
            ]
        )
        self.llm.set_context("start_year", self.bible["timeline"]["start_year"])

        if "회귀" in self.bible["meta"]["genre_tags"]:
            self.bible["timeline"]["regression_from_year"] = self.ask_field(
                "회귀 전 시점",
                "주인공이 회귀하기 전 시점 (미래)",
                field_type="number",
                predefined_options=[
                    {"label": "2020년", "value": 2020},
                    {"label": "2023년", "value": 2023},
                    {"label": "2025년", "value": 2025},
                    {"label": "2030년", "value": 2030},
                ]
            )
            self.llm.set_context("regression_from", self.bible["timeline"]["regression_from_year"])

        # 3. 주인공
        print("\n\n▶ PART 3: 주인공 설정")

        self.bible["protagonist"]["name"] = self.ask_field(
            "주인공 이름",
            "주인공의 이름을 정해주세요"
        )
        self.llm.set_context("protagonist_name", self.bible["protagonist"]["name"])

        self.bible["protagonist"]["age_at_start"] = self.ask_field(
            "시작 나이",
            "이야기 시작 시점의 나이",
            field_type="number",
            predefined_options=[
                {"label": "18세 (고3)", "value": 18},
                {"label": "22세 (대학생)", "value": 22},
                {"label": "25세 (사회초년생)", "value": 25},
                {"label": "30세", "value": 30},
                {"label": "35세", "value": 35},
            ]
        )

        self.bible["protagonist"]["archetype"] = self.ask_field(
            "주인공 아키타입",
            "주인공의 기본 유형",
            predefined_options=[
                {"label": "천재형", "value": "genius", "description": "처음부터 뛰어난 능력, 먼치킨 성향"},
                {"label": "노력형", "value": "hardworker", "description": "꾸준한 성장, 고난 극복"},
                {"label": "복수형", "value": "avenger", "description": "과거의 한을 풀기 위해"},
                {"label": "소시민형", "value": "everyman", "description": "평범했으나 기회를 잡음"},
            ]
        )
        self.llm.set_context("archetype", self.bible["protagonist"]["archetype"])

        self.bible["protagonist"]["personality_tags"] = self.ask_field(
            "성격 태그",
            "주인공의 성격 특성들",
            field_type="list"
        )

        self.bible["protagonist"]["fatal_flaw"] = self.ask_field(
            "치명적 약점",
            "주인공의 약점 (없으면 '없음')",
            predefined_options=[
                {"label": "가족", "value": "가족을 통한 협박에 약함"},
                {"label": "트라우마", "value": "특정 상황에서 판단력 저하"},
                {"label": "도덕성", "value": "비윤리적 수단 사용 불가"},
                {"label": "건강", "value": "신체적 한계"},
                {"label": "없음 (먼치킨)", "value": "없음"},
            ]
        )

        # 주인공 전생
        if "회귀" in self.bible["meta"]["genre_tags"] or "빙의" in self.bible["meta"]["genre_tags"]:
            print("\n   ─ 전생 정보 ─")
            self.bible["protagonist"]["past_life"]["profession"] = self.ask_field(
                "전생 직업",
                "회귀/빙의 전 직업"
            )
            self.llm.set_context("past_profession", self.bible["protagonist"]["past_life"]["profession"])

            self.bible["protagonist"]["past_life"]["expertise"] = self.ask_field(
                "전생 전문분야",
                "전생에서 쌓은 전문 지식/기술",
                field_type="list"
            )

        # 4. 가문
        print("\n\n▶ PART 4: 가문/배경 설정")

        self.bible["family"]["family_rank"] = self.ask_field(
            "가문 규모",
            "출신 가문의 규모/지위",
            predefined_options=[
                {"label": "5대 재벌", "value": "top5_chaebol", "description": "삼성/현대/LG급"},
                {"label": "10대 재벌", "value": "top10_chaebol", "description": "한화/롯데급"},
                {"label": "중견 재벌", "value": "mid_chaebol", "description": "업계 3-5위권"},
                {"label": "신흥 부자", "value": "new_rich", "description": "1세대 부자"},
                {"label": "평범한 가정", "value": "ordinary", "description": "특별한 배경 없음"},
                {"label": "몰락한 가문", "value": "fallen", "description": "과거의 영광만"},
            ]
        )
        self.llm.set_context("family_rank", self.bible["family"]["family_rank"])

        self.bible["family"]["family_atmosphere"] = self.ask_field(
            "가문 분위기",
            "가문 내 주인공에 대한 태도",
            predefined_options=[
                {"label": "협조적", "value": "supportive", "description": "든든한 지원군"},
                {"label": "방관적", "value": "neutral", "description": "알아서 하라는 식"},
                {"label": "적대적", "value": "hostile", "description": "생존 경쟁"},
                {"label": "복합적", "value": "mixed", "description": "일부 아군, 일부 적"},
            ]
        )

        # 가족 구성원 생성
        print("\n   ⏳ 가족 구성원 생성 중...")
        self.bible["family"]["members"] = self.llm.generate_family_members({
            "rank": self.bible["family"]["family_rank"],
            "atmosphere": self.bible["family"]["family_atmosphere"],
            "protagonist": self.bible["protagonist"]["name"]
        })

        if self.bible["family"]["members"]:
            print("\n   생성된 가족 구성원:")
            for m in self.bible["family"]["members"]:
                stance_emoji = {"협조적": "💚", "중립": "💛", "적대적": "❤️"}.get(m.get("stance_to_protagonist", ""), "⚪")
                print(f"   {stance_emoji} {m.get('name')} ({m.get('relation')}) - {m.get('personality')}")

            edit = input("\n   수정할까요? (y/N): ").strip().lower()
            if edit == 'y':
                # TODO: 수정 로직
                pass

        # 5. 조연 (조력자/라이벌)
        print("\n\n▶ PART 5: 주요 조연")

        # 조력자
        print("\n   ─ 조력자 ─")
        ally_choice = input("   조력자 생성: [A]자동 [D]직접입력 [S]스킵: ").strip().upper()
        if ally_choice == 'A':
            print("   ⏳ 조력자 생성 중...")
            self.bible["allies"] = self.llm.generate_npcs("ally", 3)
            for a in self.bible["allies"]:
                print(f"   💚 {a.get('name')} ({a.get('role')}) - {a.get('special_skill')}")
        elif ally_choice == 'D':
            # TODO: 직접 입력 로직
            pass

        # 라이벌
        print("\n   ─ 라이벌 ─")
        rival_choice = input("   라이벌 생성: [A]자동 [D]직접입력 [S]스킵: ").strip().upper()
        if rival_choice == 'A':
            print("   ⏳ 라이벌 생성 중...")
            self.bible["rivals"] = self.llm.generate_npcs("rival", 3)
            for r in self.bible["rivals"]:
                print(f"   ❤️ {r.get('name')} ({r.get('role')}) - {r.get('motivation')}")

        # 6. 목표
        print("\n\n▶ PART 6: 목표 설정")

        self.bible["protagonist"]["goals"]["ultimate_goal"] = self.ask_field(
            "최종 목표",
            "주인공의 궁극적 목표"
        )
        self.llm.set_context("ultimate_goal", self.bible["protagonist"]["goals"]["ultimate_goal"])

        self.bible["protagonist"]["goals"]["motivation"] = self.ask_field(
            "동기",
            "왜 그 목표를 추구하는가?"
        )

        # 7. 톤
        print("\n\n▶ PART 7: 톤 & 분위기")

        self.bible["tone"]["overall"] = self.ask_field(
            "전체 톤",
            "작품의 전반적인 분위기",
            predefined_options=[
                {"label": "진지/하드", "value": "serious"},
                {"label": "밸런스", "value": "balanced"},
                {"label": "가벼움/코믹", "value": "light"},
                {"label": "다크", "value": "dark"},
            ]
        )

        self.bible["tone"]["realism_level"] = self.ask_field(
            "현실성",
            "역사/경제 현실 반영 수준",
            predefined_options=[
                {"label": "극사실", "value": "realistic", "description": "실제 기업/인물 모티브"},
                {"label": "반사실", "value": "semi-realistic", "description": "현실 기반 가공"},
                {"label": "판타지", "value": "fantasy", "description": "자유로운 설정"},
            ]
        )

        print("\n" + "="*60)
        print("  ✅ Bible 설계 완료!")
        print("="*60)

        return self.bible

    def show_opportunity_recommendations(self):
        """현재 설정에 맞는 역사적 기회 추천 표시"""
        if not self.opportunity_db or not self.opportunity_db.opportunities:
            print("   (opportunity_db 없음 - 일반 모드로 진행)")
            return

        start_year = self.bible.get("timeline", {}).get("start_year", 1985)
        family_rank = self.bible.get("family", {}).get("family_rank", "ordinary")

        # 자본 티어 매핑
        rank_to_capital = {
            "top5_chaebol": "재벌급",
            "top10_chaebol": "대기업",
            "mid_chaebol": "중소기업",
            "new_rich": "소규모",
            "ordinary": "개인",
            "fallen": "개인"
        }
        capital_tier = rank_to_capital.get(family_rank, "개인")

        opportunities = self.opportunity_db.query(
            year=start_year,
            capital_tier=capital_tier,
            limit=5
        )

        if opportunities:
            print(f"\n   ─ {start_year}년, {capital_tier} 규모에서 가능한 기회 ─")
            for i, opp in enumerate(opportunities, 1):
                timeline = opp.get("timeline", {})
                returns = opp.get("returns", {})
                golden = timeline.get("golden_window", {})
                print(f"   [{i}] {opp.get('name', '?')}")
                print(f"       시기: {golden.get('start', '?')}~{golden.get('end', '?')} | ROI: {returns.get('peak_roi', '?')}")
            print()

    def design_blocks(self):
        """Block 구조 설계"""
        print("\n" + "="*60)
        print("  📦 Block 구조 설계")
        print("="*60)

        # 역사적 기회 추천 표시
        self.show_opportunity_recommendations()

        # 초기 Arc
        print("\n\n▶ 초기 Arc 설계")
        arc_choice = input("   [A]자동 생성 (기회DB 활용) [D]직접 설계: ").strip().upper()

        if arc_choice == 'A':
            print("   ⏳ 초기 Arc 생성 중... (역사적 기회 참조)")
            self.blocks["initial_arc"] = self.llm.generate_initial_arc(self.bible)

            print("\n   생성된 초기 Arc:")
            print(f"   제목: {self.blocks['initial_arc'].get('title')}")
            print(f"   목표: {self.blocks['initial_arc'].get('objectives')}")
            first_biz = self.blocks['initial_arc'].get('first_business', {})
            print(f"   첫 사업: {first_biz.get('type')}")
            if first_biz.get('opportunity_ref'):
                print(f"   참조 기회: {first_biz.get('opportunity_ref')}")

        # 확장 전략
        print("\n\n▶ 중기 확장 전략")
        self.blocks["expansion_strategy"]["type"] = self.ask_field(
            "확장 전략",
            "중반부 사업 확장 방식",
            predefined_options=[
                {"label": "문어발식", "value": "octopus", "description": "다양한 산업에 진출"},
                {"label": "수직계열화", "value": "vertical", "description": "한 산업 완전 장악"},
                {"label": "플랫폼형", "value": "platform", "description": "생태계 구축"},
                {"label": "M&A 사냥꾼", "value": "mna", "description": "인수합병 위주"},
                {"label": "기술 선점", "value": "tech", "description": "미래 기술 투자"},
            ]
        )

        # 말기 Arc
        print("\n\n▶ 말기 Arc 설계")
        final_choice = input("   [A]자동 생성 [D]직접 설계: ").strip().upper()

        if final_choice == 'A':
            print("   ⏳ 말기 Arc 생성 중...")
            self.blocks["final_arc"] = self.llm.generate_final_arc(
                self.bible,
                self.blocks["initial_arc"]
            )

            print("\n   생성된 말기 Arc:")
            print(f"   제목: {self.blocks['final_arc'].get('title')}")
            print(f"   최종 적: {self.blocks['final_arc'].get('final_enemy', {}).get('name')}")
            print(f"   대결 방식: {self.blocks['final_arc'].get('showdown_type')}")
            print(f"   엔딩: {self.blocks['final_arc'].get('ending_type')}")

        print("\n" + "="*60)
        print("  ✅ Block 구조 설계 완료!")
        print("="*60)

        return self.blocks

    def save(self, output_dir: Path):
        """저장"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 메타 업데이트
        self.bible["meta"]["created_at"] = datetime.now().isoformat()

        # Bible 저장
        bible_path = output_dir / "bible.json"
        with open(bible_path, "w", encoding="utf-8") as f:
            json.dump(self.bible, f, ensure_ascii=False, indent=2)
        print(f"\n저장됨: {bible_path}")

        # Blocks 저장 (장르별 스키마 포함)
        blocks_output = {
            "_schema_version": "2.0",
            "_genre_tags": self.bible.get("meta", {}).get("genre_tags", []),
            "arcs": self.blocks
        }

        # 장르별 블록 스키마 추가
        if self.block_schema:
            genre_tags = self.bible.get("meta", {}).get("genre_tags", [])
            genre_schema = self.block_schema.get_genre_schema(genre_tags)
            blocks_output["_block_schema"] = genre_schema
            blocks_output["_block_template"] = self.block_schema.get_block_template(genre_tags)

        blocks_path = output_dir / "blocks.json"
        with open(blocks_path, "w", encoding="utf-8") as f:
            json.dump(blocks_output, f, ensure_ascii=False, indent=2)
        print(f"저장됨: {blocks_path}")

        # 사용된 기회 목록 저장 (있으면)
        if self.opportunity_db and self.opportunity_db.opportunities:
            start_year = self.bible.get("timeline", {}).get("start_year", 1985)
            used_opps = self.opportunity_db.query(year=start_year, limit=10)
            if used_opps:
                opps_path = output_dir / "available_opportunities.json"
                with open(opps_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "start_year": start_year,
                        "opportunities": used_opps
                    }, f, ensure_ascii=False, indent=2)
                print(f"저장됨: {opps_path} ({len(used_opps)}개 기회)")


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    print()
    print("="*60)
    print("  📖 Bible & Block 자동 설계 도구 v2.0")
    print("     (block_schema + opportunity_db 통합)")
    print("="*60)

    # API 키
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("GOOGLE_API_KEY 없음")
        sys.exit(1)

    # 외부 스키마/DB 로드
    print("\n[시스템 초기화]")
    block_schema = BlockSchemaLoader()
    opportunity_db = OpportunityDB()

    # DB 상태 출력
    if opportunity_db.opportunities:
        print(f"  → 기회 DB 활성화: {len(opportunity_db.opportunities)}개 기회 로드됨")
    else:
        print("  → 기회 DB 없음 (opportunity_db_builder.py로 생성 가능)")

    # 출력 경로
    print("\n프로젝트 이름을 입력하세요 (폴더명으로 사용됩니다)")
    project_name = input("프로젝트명: ").strip()
    if not project_name:
        project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    output_dir = Path(__file__).parent.parent / "projects" / project_name

    # LLM 초기화 (opportunity_db, block_schema 전달)
    llm = DesignerLLM(
        api_key,
        opportunity_db=opportunity_db,
        block_schema=block_schema
    )
    designer = BibleDesigner(
        llm,
        block_schema=block_schema,
        opportunity_db=opportunity_db
    )

    # Bible 설계
    bible = designer.design_bible()

    # Block 설계
    blocks = designer.design_blocks()

    # 저장
    designer.save(output_dir)

    print("\n" + "="*60)
    print("  🎉 설계 완료!")
    print(f"  📁 저장 위치: {output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
