"""
Genre Library Builder v2.1
==========================
Core + Extension 고밀도 구조로 장르별 블록/바이블 라이브러리 구축.
회귀물 여부는 LLM이 원고를 보고 자동 감지.

사용법:
    # 10개 전부 병렬 처리
    python tools/genre_library_builder.py -i "연구소/재벌물" -o "libraries/재벌물" -g investment -w 10

    # 다른 장르
    python tools/genre_library_builder.py -i "연구소/무협물" -o "libraries/무협물" -g wuxia -w 10
    python tools/genre_library_builder.py -i "연구소/헌터물" -o "libraries/헌터물" -g hunter -w 10
"""

import os
import sys

# Windows UTF-8 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
import argparse
import time
import re
import ast  # JSON 자가 치유용
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from google import genai
from google.genai import types

# Rich 라이브러리 (스피너/상황판)
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ rich 라이브러리 없음. 기본 출력 모드로 동작.")


# ─────────────────────────────────────────────
# 진행 상황 추적기
# ─────────────────────────────────────────────
class ProgressTracker:
    """10개 작품 병렬 처리 상황판 + 로그 파일"""

    def __init__(self, work_names: list[str], log_path: Path = None):
        self.work_names = work_names
        self.status = {name: {"phase": "대기", "progress": 0, "blocks": 0, "detail": ""} for name in work_names}
        self.lock = Lock()
        self.console = Console() if RICH_AVAILABLE else None
        self.log_path = log_path
        self.start_time = datetime.now()

        # 로그 파일 초기화
        if self.log_path:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(f"=== Genre Library Builder 시작: {self.start_time.isoformat()} ===\n")
                f.write(f"작품 수: {len(work_names)}\n\n")

    def update(self, work_name: str, phase: str, progress: int = 0, blocks: int = 0, detail: str = ""):
        with self.lock:
            self.status[work_name] = {
                "phase": phase,
                "progress": progress,
                "blocks": blocks,
                "detail": detail
            }

            # 로그 파일에 기록
            if self.log_path:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                log_line = f"[{elapsed:7.1f}s] {work_name:15} | {phase:8} | {progress:3}% | {blocks:3}블록 | {detail}\n"
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(log_line)

    def render_table(self) -> Table:
        """Rich 테이블 렌더링"""
        table = Table(title="📊 Genre Library Builder - 작업 현황", show_header=True)
        table.add_column("작품", style="cyan", width=15)
        table.add_column("상태", style="magenta", width=12)
        table.add_column("진행", justify="right", width=8)
        table.add_column("블록", justify="right", width=6)
        table.add_column("상세", style="dim", width=30)

        phase_emoji = {
            "대기": "⏳",
            "로딩": "📂",
            "아크분석": "🔍",
            "블록분할": "✂️",
            "추출중": "📝",
            "Bible": "📖",
            "완료": "✅",
            "실패": "❌"
        }

        with self.lock:
            for name in self.work_names:
                s = self.status[name]
                emoji = phase_emoji.get(s["phase"], "🔄")
                progress_str = f"{s['progress']}%" if s['progress'] > 0 else "-"
                blocks_str = str(s['blocks']) if s['blocks'] > 0 else "-"
                table.add_row(
                    name[:14],
                    f"{emoji} {s['phase']}",
                    progress_str,
                    blocks_str,
                    s['detail'][:28] if s['detail'] else ""
                )

        return table

    def print_simple(self):
        """Rich 없을 때 기본 출력"""
        print("\n" + "="*60)
        print("📊 작업 현황")
        print("="*60)
        with self.lock:
            for name in self.work_names:
                s = self.status[name]
                print(f"  {name[:15]:15} | {s['phase']:8} | {s['progress']:3}% | {s['blocks']:3}블록 | {s['detail'][:20]}")
        print("="*60)

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
PRIMARY_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_DELAY = 5

DEFAULT_WORKERS = 3
ARC_SIZE = 10
HIERARCHICAL_THRESHOLD = 30

# ─────────────────────────────────────────────
# 장르별 Extension 정의 (고밀도 v2.1)
# ─────────────────────────────────────────────
CORE_FIELDS = '''
  // ═══ CORE (공통) ═══
  "content": {
    "context": "상황/배경 - 주인공 현재 상태, 장소, 시간 (3-5문장)",
    "event_villain": "갈등/위기 - 적대 요소, 장애물, 위협 (3-5문장)",
    "solution": "해결 - 주인공의 대응, 전략, 행동 (3-5문장)",
    "reward": "보상 - 물리적/정신적 성장, 획득물 (2-4문장)"
  },
  "stakes": "판돈/리스크 - 실패 시 잃는 것 (없으면 null)",
  "power_shift": {
    "protagonist": "주인공 권력/지위 변화 (없으면 null)",
    "antagonist": "적대자 권력/지위 변화 (없으면 null)"
  },
  "relationship_delta": [
    {"target": "대상", "before": "이전관계", "after": "이후관계"}
  ],
  "foreshadow": ["심은 복선들 (없으면 빈 배열)"],
  "callback": ["회수한 복선들 (없으면 빈 배열)"],
  "emotional_beat": {
    "type": "감정비트 (tension/catharsis/despair/triumph/revelation/betrayal 중 하나)",
    "intensity": "강도 1-10"
  },
  "tension_level": "긴장도 1-10",
  "pov_character": "시점 캐릭터",
  "location": {
    "place": "장소명",
    "type": "장소유형 (실내/실외/회의실/전장/etc)"
  },
  "time_span": {
    "duration": "소요시간 (1일/1주/1달/etc)",
    "in_story_time": "작중시간 (1997년 10월 등, 모르면 null)"
  }'''

REGRESSION_FIELDS = '''
  // ═══ REGRESSION (회귀/빙의/환생 감지 시에만 채움) ═══
  // 주인공이 미래지식/전생기억을 가진 경우에만 해당 필드 채움. 아니면 전체 null.
  "regression_ext": {
    "is_regressor": "회귀자/빙의/환생 여부 (true/false) - 원고에서 판단",
    "regression_type": "유형 (회귀/빙의/환생/타임슬립/null)",
    "timeline_knowledge": {
      "info_used": "사용한 미래 정보 (없으면 null)",
      "accuracy": "정확/부분변경/완전변경",
      "source": "정보출처 (직접경험/소문/기록)"
    },
    "butterfly_effect": {
      "original_event": "원래 역사 (없으면 null)",
      "changed_event": "바뀐 결과",
      "ripple_effect": "파급효과"
    },
    "death_flag": {
      "avoided": "회피한 사망플래그 (없으면 null)",
      "method": "회피방법"
    },
    "regression_hint": {
      "slip_up": "회귀자 암시 실수 (없으면 null)",
      "suspicion_from": "의심하는 캐릭터"
    },
    "future_prep": {
      "action": "미래 대비 행동 (없으면 null)",
      "target_event": "대비하는 미래사건"
    }
  }'''

GENRE_EXTENSIONS = {
    "investment": {
        "name": "재벌물/투자물",
        "ext_fields": '''
  // ═══ EXTENSION (재벌물/투자물) ═══
  "genre_ext": {
    "type": "investment",
    "capital_before": "시작 자산 (예: 10억)",
    "capital_after": "종료 자산",
    "profit_loss": "손익 (예: +90억)",

    "method": "돈 버는 방법 (주식선점/M&A/부동산/사업인수/IPO/etc)",
    "investment_type": "투자유형 (주식/부동산/선물/옵션/암호화폐/etc)",

    "deal_type": "거래유형 (협상/경쟁입찰/적대적인수/우호적인수/etc)",
    "leverage_used": ["레버리지 (정보/인맥/자금력/권력/협박/etc)"],

    "opponent": {
      "name": "상대방",
      "type": "상대유형 (경쟁재벌/가족/정부/외국자본/etc)",
      "weakness_exploited": "공략한 약점"
    },

    "historical_event": {
      "name": "사건명 (IMF/오일쇼크/비트코인/etc, 없으면 null)",
      "year": "연도",
      "how_exploited": "활용방법"
    },

    "time_pressure": "시간제약 (없으면 null)",
    "knowledge_used": "미래지식 (없으면 null)",
    "risk_level": "리스크 (극고위험/고위험/중위험/저위험)",
    "business_sector": "사업섹터 (IT/제조/금융/유통/건설/etc)",

    // ═══ 퓨전 요소 (마법/이능력/시스템) ═══
    "special_ability": {
      "has_ability": "이능력/마법/시스템 보유 여부 (true/false)",
      "ability_type": "능력유형 (마법/이능력/시스템창/스킬/null)",
      "ability_name": "능력명 (없으면 null)",
      "ability_source": "능력 획득 경로 (용/신/시스템/각성/etc, 없으면 null)",
      "ability_used_for": "능력 활용 용도 (사업/상품개발/정보획득/전투/etc)"
    }
  }''',
        "bible_prompt": """
## 재벌물/투자물 Bible 추출
- money_methods: [{name, description, typical_era, risk_level, frequency}]
- historical_events: [{name, year, how_exploited, profit_potential}]
- investment_types: [{name, description, common_strategies}]
- business_sectors: [섹터명들]
- deal_types: [{name, description, typical_scenario}]
- protagonist_archetypes: [{type, background, advantages}]
- antagonist_archetypes: [{type, description, typical_weakness}]
- typical_timeline: {start_era, end_era, key_periods}
- leverage_types: [{name, description, effectiveness}]
- special_abilities: [{type, name, source, usage}] (마법/이능력/시스템 등 비현실 요소, 없으면 빈 배열)
- fusion_elements: {has_fantasy: true/false, fantasy_type: "마법/이능력/시스템/null", description}
"""
    },

    "wuxia": {
        "name": "무협물",
        "ext_fields": '''
  // ═══ EXTENSION (무협물) ═══
  "genre_ext": {
    "type": "wuxia",

    "martial_arts": {
      "used": ["사용한 무공들"],
      "acquired": "습득한 무공 (없으면 null)",
      "type": "무공계열 (검/도/권/장/암기/내공/etc)"
    },

    "power_level": {
      "before": "시작 경지 (후천3성/화경초입/etc)",
      "after": "종료 경지",
      "breakthrough": true/false
    },

    "combat": {
      "type": "전투유형 (비무/암습/대전/공성/암살/etc)",
      "scale": "규모 (일대일/소규모/대규모/전면전)",
      "outcome": "결과 (완승/신승/무승부/패배/전략적후퇴)"
    },

    "sect_politics": {
      "involved_sects": ["관련 문파들"],
      "alliance_change": "동맹변화 (없으면 null)",
      "sect_standing": "문파내 지위변화"
    },

    "treasure": {
      "gained": ["획득 보물/영약/비급"],
      "lost": ["잃은 것들"],
      "type": "보물유형 (영약/신병/비급/내단/etc)"
    },

    "injury_status": {
      "received": "입은 부상 (없으면 null)",
      "inflicted": "가한 부상",
      "recovery": "회복상태"
    },

    "qi_cultivation": {
      "method": "수련법 (없으면 null)",
      "progress": "내공진전",
      "side_effect": "부작용"
    },

    "reputation_change": {
      "jianghu_fame": "강호명성 변화",
      "title_gained": "얻은 별호 (없으면 null)"
    }
  }''',
        "bible_prompt": """
## 무협물 Bible 추출
- martial_arts_systems: [{name, type, characteristics, famous_users}]
- power_level_system: [{level_name, description, typical_abilities}]
- sects: [{name, alignment, specialty, location, notable_figures}]
- treasure_types: [{category, examples, effects}]
- combat_styles: [{name, characteristics, counter_style}]
- protagonist_archetypes: [{type, background, typical_growth_path}]
- antagonist_archetypes: [{type, motivation, typical_techniques}]
- world_structure: {regions, power_hierarchy, major_conflicts}
- cultivation_methods: [{name, effects, risks}]
- titles_and_rankings: [{title, requirements, prestige_level}]
"""
    },

    "hunter": {
        "name": "헌터물/던전물",
        "ext_fields": '''
  // ═══ EXTENSION (헌터물) ═══
  "genre_ext": {
    "type": "hunter",

    "dungeon": {
      "name": "던전명 (없으면 null)",
      "grade": "등급 (SSS~F)",
      "type": "유형 (일반/보스/레이드/비밀/이벤트)",
      "clear_status": "클리어상태 (최초/재도전/실패)"
    },

    "raid": {
      "type": "레이드유형 (솔로/파티/길드/연합)",
      "party_size": "파티인원",
      "role": "역할 (탱커/딜러/힐러/서포터/올라운더)"
    },

    "skill": {
      "used": ["사용 스킬들"],
      "acquired": "획득 스킬 (없으면 null)",
      "evolved": "진화 스킬 (없으면 null)",
      "skill_type": "스킬계열 (물리/마법/소환/버프/패시브/etc)"
    },

    "rank": {
      "before": "시작 랭크",
      "after": "종료 랭크",
      "evaluation_type": "평가방식 (재각성/승급시험/실적)"
    },

    "loot": {
      "items": ["획득 아이템"],
      "grade": "최고등급 아이템",
      "value": "추정가치",
      "magic_stones": "마석 획득량"
    },

    "guild": {
      "name": "소속 길드 (없으면 null)",
      "position": "길드내 직위",
      "guild_event": "길드이벤트 (가입/탈퇴/창설/전쟁)"
    },

    "monster": {
      "boss_name": "보스명 (없으면 null)",
      "boss_grade": "보스등급",
      "special_ability": "특수능력"
    },

    "awakening": {
      "type": "각성유형 (최초/재각성/이중각성/etc, 없으면 null)",
      "trigger": "각성트리거",
      "new_ability": "새능력"
    },

    "hunter_politics": {
      "association_relation": "협회관계",
      "rival_guilds": ["경쟁길드"],
      "government_relation": "정부관계"
    },

    "survival_status": {
      "party_casualties": "파티피해 (없으면 null)",
      "near_death": true/false,
      "recovery_method": "회복방법"
    }
  }''',
        "bible_prompt": """
## 헌터물 Bible 추출
- rank_system: [{rank_name, requirements, privileges, population_ratio}]
- skill_categories: [{category, subcategories, famous_skills}]
- dungeon_types: [{grade, characteristics, typical_rewards, danger_level}]
- monster_taxonomy: [{category, grades, notable_species}]
- guild_types: [{type, characteristics, famous_examples}]
- awakening_types: [{type, trigger_conditions, rarity}]
- loot_system: [{category, grades, typical_sources}]
- protagonist_archetypes: [{type, initial_condition, growth_pattern}]
- antagonist_archetypes: [{type, motivation, threat_level}]
- world_structure: {gate_system, association_structure, international_relations}
- hunter_economy: {income_sources, major_expenses, wealth_distribution}
"""
    }
}


# ─────────────────────────────────────────────
# LLM 클라이언트
# ─────────────────────────────────────────────
class TreatmentLLM:
    def __init__(self, api_key: str, model: str = PRIMARY_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.current_model = model

    def ask(self, prompt: str, temperature: float = 0.3) -> dict:
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

                if "quota" in error_msg or "429" in error_msg:
                    if self.current_model != FALLBACK_MODEL:
                        print(f"    ⚠️ {self.current_model} → {FALLBACK_MODEL} 폴백")
                        self.current_model = FALLBACK_MODEL
                        continue

                if attempt < MAX_RETRIES - 1:
                    print(f"    ⚠️ 재시도 {attempt+1}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    return {"error": str(e)}

        return {}

    def _parse_json(self, text: str) -> dict:
        """
        [V2.1] 자가 치유(Self-Healing) JSON 파서
        base_agent.py의 _extract_json_robust 로직 통합
        """
        if not text or not isinstance(text, str):
            return {"parsing_error": True, "content": "Empty or Invalid Input"}

        text = text.strip()

        # 1. 괄호/따옴표 쌍 검사 및 강제 폐쇄
        open_braces = text.count('{')
        close_braces = text.count('}')
        if open_braces > close_braces:
            text += '}' * (open_braces - close_braces)

        open_brackets = text.count('[')
        close_brackets = text.count(']')
        if open_brackets > close_brackets:
            text += ']' * (open_brackets - close_brackets)

        quote_count = len(re.findall(r'(?<!\\)"', text))
        if quote_count % 2 != 0:
            text += '"'

        try:
            # 2. 마크다운 코드블록 제거 및 JSON 블록 추출
            clean_text = re.sub(r'```json\s*|```\s*', '', text)
            json_pattern = re.compile(r'(\{.*\}|\[.*\])', re.DOTALL)
            match = json_pattern.search(clean_text)
            raw_json = match.group(1) if match else clean_text

            # 3. 3단계 파싱 시도
            # Stage 1: json.loads (strict=False)
            try:
                return json.loads(raw_json, strict=False)
            except Exception:
                pass

            # Stage 2: ast.literal_eval (Python 리터럴)
            try:
                # null/true/false → Python 변환
                processed = re.sub(r':\s*null\b', ': None', raw_json)
                processed = re.sub(r':\s*true\b', ': True', processed)
                processed = re.sub(r':\s*false\b', ': False', processed)
                return ast.literal_eval(processed)
            except Exception:
                pass

            # Stage 3: 정규식 강제 추출
            print(f"    ⚠️ [JSON Parser] 정규식 폴백 사용 (길이: {len(raw_json)}자)")

            # content 필드 추출 시도
            content_match = re.search(r'"content"\s*:\s*\{([^}]+)\}', raw_json, re.DOTALL)
            if content_match:
                # 핵심 필드들 추출
                result = {"content": {}, "repaired": True}
                for field in ["context", "event_villain", "solution", "reward"]:
                    field_match = re.search(rf'"{field}"\s*:\s*"(.*?)"(?=\s*[,}}])', raw_json, re.DOTALL)
                    if field_match:
                        result["content"][field] = field_match.group(1).replace('\\n', '\n').strip()
                return result

            # 일반 키-값 추출
            kv_pattern = r'"(\w+)"\s*:\s*"(.*?)"(?=\s*[,}\]])'
            found_pairs = re.findall(kv_pattern, raw_json, re.DOTALL)
            if found_pairs:
                print(f"    → 정규식으로 {len(found_pairs)}개 키-값 추출")
                return {k: v.replace('\\n', '\n').strip() for k, v in found_pairs}

            return {"parsing_error": True, "raw": raw_json[:500]}

        except Exception as e:
            return {"parsing_error": True, "error": str(e), "raw": text[:300]}


# ─────────────────────────────────────────────
# 원고 로더
# ─────────────────────────────────────────────
def load_manuscripts(work_path: Path) -> list[dict]:
    manuscripts = []
    files = sorted(
        [f for f in work_path.glob("*.txt") if "합본" not in f.name],
        key=lambda f: f.name
    )

    for i, f in enumerate(files, 1):
        try:
            text = f.read_text(encoding="utf-8")
            match = re.search(r'(\d+)', f.stem)
            ep_num = int(match.group(1)) if match else i
            manuscripts.append({"ep_num": ep_num, "text": text, "filename": f.name})
        except Exception as e:
            print(f"    ⚠️ {f.name} 로드 실패: {e}")

    return manuscripts


# ─────────────────────────────────────────────
# Core + Extension Treatment 추출 (고밀도)
# ─────────────────────────────────────────────
def get_treatment_prompt(block: dict, combined_text: str, genre: str) -> str:
    """장르별 고밀도 Treatment 추출 프롬프트 (회귀물 자동 감지)"""

    genre_info = GENRE_EXTENSIONS.get(genre, GENRE_EXTENSIONS["investment"])
    ext_fields = genre_info["ext_fields"]

    return f"""아래 원고를 고밀도 Core + Extension 구조의 Treatment 블록으로 분석.

## 원고
{combined_text}

## JSON 출력 (Core + {genre_info['name']} Extension + 회귀물 자동감지)
{{
  "block_id": "Block {block['block_id']}",
  "title": "[임팩트 있는 블록 제목]",

{CORE_FIELDS},

{ext_fields},

{REGRESSION_FIELDS}
}}

## 주의사항
- 원고에서 확인되는 정보만 채우세요
- 확인 안 되는 필드는 null 또는 빈 배열로
- 추측하지 말고 명시적 정보만 사용
- 각 content 필드는 3-5문장으로 구체적으로
- regression_ext: 주인공이 회귀자/빙의/환생인 경우에만 채움. 일반 주인공이면 is_regressor: false, 나머지 전부 null"""


def extract_treatment(llm: TreatmentLLM, block: dict, manuscripts: list[dict], genre: str) -> dict:
    """블록별 Treatment 추출 (회귀물 자동 감지)"""
    ep_nums = block["episodes"]
    texts = [f"[ep{m['ep_num']}]\n{m['text']}" for m in manuscripts if m["ep_num"] in ep_nums]
    combined = "\n---\n".join(texts)

    if len(combined) > 40000:
        combined = combined[:40000] + "\n...(생략)"

    prompt = get_treatment_prompt(block, combined, genre)
    result = llm.ask(prompt, temperature=0.4)

    if "content" not in result:
        result = {
            "block_id": f"Block {block['block_id']}",
            "title": f"[{block.get('title_hint', '제목없음')}]",
            "content": {"error": "추출실패"},
            "genre_ext": {"type": genre, "error": "추출실패"}
        }

    return result


# ─────────────────────────────────────────────
# Bible 추출 (장르별 고밀도)
# ─────────────────────────────────────────────
def extract_bible(llm: TreatmentLLM, manuscripts: list[dict], work_name: str, genre: str) -> dict:
    """작품에서 Bible 요소 추출 (1화 기준 - 초기 설정 집중)"""

    genre_info = GENRE_EXTENSIONS.get(genre, GENRE_EXTENSIONS["investment"])

    # 1화만 읽음 (초기 설정이 여기 다 있음)
    first_ep = manuscripts[0] if manuscripts else None
    if not first_ep:
        return {}

    ep1_text = first_ep['text'][:8000]  # 1화 전문 또는 앞 8000자

    prompt = f"""'{work_name}' ({genre_info['name']}) 1화에서 세계관/초기 설정을 추출하세요.

[1화]
{ep1_text}

{genre_info['bible_prompt']}

## JSON 출력
1화에서 확인되는 초기 설정만 추출. 없는 항목은 빈 배열 또는 null."""

    return llm.ask(prompt, temperature=0.3)


# ─────────────────────────────────────────────
# 아크 분석
# ─────────────────────────────────────────────
def summarize_arcs(llm: TreatmentLLM, manuscripts: list[dict], work_name: str, genre: str) -> list[dict]:
    """아크 요약 생성"""
    arcs = []
    total = len(manuscripts)
    genre_info = GENRE_EXTENSIONS.get(genre, GENRE_EXTENSIONS["investment"])

    for start_idx in range(0, total, ARC_SIZE):
        end_idx = min(start_idx + ARC_SIZE, total)
        arc_manuscripts = manuscripts[start_idx:end_idx]
        arc_id = len(arcs) + 1
        ep_range = [m["ep_num"] for m in arc_manuscripts]

        combined = ""
        for m in arc_manuscripts:
            preview = m["text"][:1200]
            combined += f"\n[ep{m['ep_num']}]\n{preview}\n---\n"

        prompt = f"""'{work_name}' ({genre_info['name']}) 에피소드 {ep_range[0]}~{ep_range[-1]} 요약.

{combined}

JSON 출력:
{{
  "arc_id": {arc_id},
  "episodes": {ep_range},
  "summary": "핵심 사건 3-4문장 요약",
  "key_events": ["주요 이벤트들"],
  "tension_curve": "긴장도 흐름 (상승/하강/클라이맥스/etc)"
}}"""

        result = llm.ask(prompt, temperature=0.2)
        if "summary" not in result:
            result = {"arc_id": arc_id, "episodes": ep_range, "summary": "요약 실패"}
        arcs.append(result)
        time.sleep(0.3)

    return arcs


def analyze_blocks_from_arcs(llm: TreatmentLLM, arcs: list[dict], manuscripts: list[dict], work_name: str) -> list[dict]:
    """아크 기반 블록 분석"""
    arc_summaries = "\n".join([
        f"[아크{a['arc_id']}] ep{a['episodes'][0]}-{a['episodes'][-1]}: {a.get('summary', 'N/A')}"
        for a in arcs
    ])

    prompt = f"""'{work_name}' 아크 요약을 보고 블록 단위로 분할.

## 아크 요약
{arc_summaries}

## 블록 분할 기준
- 1블록 = 완결된 사건/갈등/해결 사이클
- 1~5개 에피소드를 하나의 블록으로 (가변 페이싱)
- 감정 비트가 완결되는 지점에서 분할

## JSON 출력
{{
  "blocks": [
    {{"block_id": 1, "episodes": [1,2,3], "title_hint": "제목힌트", "emotional_arc": "긴장→해소"}}
  ]
}}

전체: 1~{manuscripts[-1]['ep_num']}. 빠짐없이 연속 할당."""

    result = llm.ask(prompt, temperature=0.2)

    if "blocks" not in result:
        return [{"block_id": a["arc_id"], "episodes": a["episodes"], "title_hint": f"아크{a['arc_id']}"} for a in arcs]

    return result["blocks"]


def analyze_blocks_simple(llm: TreatmentLLM, manuscripts: list[dict], work_name: str) -> list[dict]:
    """소규모 작품용 단순 블록 분석"""
    summaries = "\n".join([
        f"[ep{m['ep_num']}] {m['text'][:800]}..."
        for m in manuscripts[:30]
    ])

    prompt = f"""'{work_name}' 원고를 블록 단위로 분할.

{summaries}

## JSON 출력
{{
  "blocks": [
    {{"block_id": 1, "episodes": [1,2], "title_hint": "제목힌트"}}
  ]
}}

전체: 1~{manuscripts[-1]['ep_num']}"""

    result = llm.ask(prompt, temperature=0.2)

    if "blocks" not in result:
        blocks = []
        eps = [m["ep_num"] for m in manuscripts]
        for i in range(0, len(eps), 3):
            blocks.append({"block_id": len(blocks)+1, "episodes": eps[i:i+3], "title_hint": f"블록{len(blocks)+1}"})
        return blocks

    return result["blocks"]


# ─────────────────────────────────────────────
# 작품 분석
# ─────────────────────────────────────────────
def analyze_single_work(llm: TreatmentLLM, work_name: str, manuscripts: list[dict], genre: str) -> dict:
    """단일 작품 분석 (회귀물 자동 감지)"""
    result = {
        "work_name": work_name,
        "genre": genre,
        "episode_count": len(manuscripts),
        "treatments": [],
        "bible": {}
    }

    if not manuscripts:
        return result

    use_hierarchical = len(manuscripts) >= HIERARCHICAL_THRESHOLD

    if use_hierarchical:
        arcs = summarize_arcs(llm, manuscripts, work_name, genre)
        blocks = analyze_blocks_from_arcs(llm, arcs, manuscripts, work_name)
    else:
        blocks = analyze_blocks_simple(llm, manuscripts, work_name)

    for block in blocks:
        treatment = extract_treatment(llm, block, manuscripts, genre)
        result["treatments"].append(treatment)
        time.sleep(0.3)

    result["bible"] = extract_bible(llm, manuscripts, work_name, genre)

    return result


# ─────────────────────────────────────────────
# 패턴 마이닝 (고밀도)
# ─────────────────────────────────────────────
def build_block_library(all_results: list[dict], llm: TreatmentLLM, genre: str) -> dict:
    """패턴 라이브러리 구축"""

    genre_info = GENRE_EXTENSIONS.get(genre, GENRE_EXTENSIONS["investment"])

    all_blocks = []
    for result in all_results:
        for treatment in result.get("treatments", []):
            all_blocks.append({
                "work": result["work_name"],
                "block_id": treatment.get("block_id"),
                "title": treatment.get("title"),
                "content": treatment.get("content", {}),
                "stakes": treatment.get("stakes"),
                "emotional_beat": treatment.get("emotional_beat"),
                "tension_level": treatment.get("tension_level"),
                "genre_ext": treatment.get("genre_ext", {}),
                "regression_ext": treatment.get("regression_ext")
            })

    print(f"\n📊 총 {len(all_blocks)}개 블록에서 패턴 추출 중...")

    block_summaries = []
    for b in all_blocks:
        ext = b.get("genre_ext", {})
        ext_summary = json.dumps(ext, ensure_ascii=False)[:150] if ext else "N/A"
        emotion = b.get("emotional_beat", {})
        summary = f"- [{b['work']}] {b['title']}: tension={b.get('tension_level')}, emotion={emotion.get('type') if emotion else 'N/A'}, ext={ext_summary}"
        block_summaries.append(summary)

    chunk_size = 60
    all_patterns = []

    for i in range(0, len(block_summaries), chunk_size):
        chunk = block_summaries[i:i+chunk_size]

        prompt = f"""아래 {genre_info['name']} 블록들에서 반복되는 고밀도 패턴을 추출.

{chr(10).join(chunk)}

## JSON 출력
{{
  "patterns": [
    {{
      "pattern_id": "PATTERN_NAME_IN_CAPS",
      "name": "패턴 한글명",
      "description": "패턴 설명",
      "frequency": "등장 횟수",
      "typical_tension": "전형적 긴장도 (1-10)",
      "typical_emotion": "전형적 감정비트",
      "examples": ["예시 블록들"],
      "core_template": {{
        "context": "{{변수}} 템플릿",
        "event_villain": "{{변수}} 템플릿",
        "solution": "{{변수}} 템플릿",
        "reward": "{{변수}} 템플릿"
      }},
      "ext_template": {{
        "주요 extension 필드들의 전형적 패턴"
      }},
      "usage_tip": "이 패턴을 사용할 때 팁"
    }}
  ]
}}

{genre_info['name']} 장르 특성에 집중하여 핵심 패턴을 추출."""

        result = llm.ask(prompt, temperature=0.3)
        if "patterns" in result:
            all_patterns.extend(result["patterns"])
        time.sleep(0.5)

    merged = merge_patterns(all_patterns, llm) if len(all_patterns) > 25 else all_patterns

    return {
        "genre": genre_info['name'],
        "genre_code": genre,
        "schema_version": "2.1",
        "total_works": len(all_results),
        "total_blocks": len(all_blocks),
        "generated_at": datetime.now().isoformat(),
        "patterns": merged
    }


def merge_patterns(patterns: list[dict], llm: TreatmentLLM) -> list[dict]:
    """유사 패턴 통합"""
    pattern_list = "\n".join([f"- {p['pattern_id']}: {p['name']} - {p.get('description', '')[:60]}" for p in patterns])

    prompt = f"""아래 패턴들 중 유사한 것들을 통합.

{pattern_list}

## JSON 출력
{{
  "merged_patterns": [
    {{
      "pattern_id": "MERGED_ID",
      "name": "통합명",
      "description": "통합 설명",
      "original_patterns": ["원본 ID들"],
      "total_frequency": "합산 빈도",
      "importance": "중요도 (핵심/주요/보조)"
    }}
  ]
}}

핵심 패턴 20-30개로 통합. 중요도 순으로 정렬."""

    result = llm.ask(prompt, temperature=0.2)
    return result.get("merged_patterns", patterns[:30])


def build_bible_library(all_results: list[dict], llm: TreatmentLLM, genre: str) -> dict:
    """Bible 라이브러리 구축"""

    genre_info = GENRE_EXTENSIONS.get(genre, GENRE_EXTENSIONS["investment"])
    all_bibles = [r.get("bible", {}) for r in all_results if r.get("bible")]

    print(f"\n📚 {len(all_bibles)}개 작품 Bible 통합 중...")

    combined_data = json.dumps(all_bibles[:15], ensure_ascii=False)[:12000]

    prompt = f"""{genre_info['name']} 작품들의 Bible 데이터를 고밀도로 통합 정리.

## 수집된 데이터
{combined_data}

{genre_info['bible_prompt']}

## JSON 출력
각 항목을 중복 제거하고 빈도순으로 정리.
각 요소에 frequency(등장빈도), importance(중요도) 필드 추가.
핵심 요소들만 추출하여 라이브러리화."""

    result = llm.ask(prompt, temperature=0.3)

    return {
        "genre": genre_info['name'],
        "genre_code": genre,
        "schema_version": "2.1",
        "total_works": len(all_results),
        "generated_at": datetime.now().isoformat(),
        **result
    }


# ─────────────────────────────────────────────
# 병렬 처리
# ─────────────────────────────────────────────
def process_work(args: tuple, tracker: ProgressTracker = None) -> dict:
    work_path, api_key, model, genre = args
    work_name = work_path.name

    def update(phase, progress=0, blocks=0, detail=""):
        if tracker:
            tracker.update(work_name, phase, progress, blocks, detail)

    update("로딩", 0, 0, "원고 로드 중...")

    llm = TreatmentLLM(api_key, model)
    manuscripts = load_manuscripts(work_path)

    if not manuscripts:
        update("실패", 0, 0, "원고 없음")
        return {"work_name": work_name, "episode_count": 0, "treatments": [], "bible": {}}

    update("로딩", 10, 0, f"{len(manuscripts)}화 로드됨")

    result = {
        "work_name": work_name,
        "genre": genre,
        "episode_count": len(manuscripts),
        "treatments": [],
        "bible": {}
    }

    use_hierarchical = len(manuscripts) >= HIERARCHICAL_THRESHOLD

    # 아크/블록 분석
    if use_hierarchical:
        update("아크분석", 15, 0, "아크 요약 생성 중...")
        arcs = summarize_arcs(llm, manuscripts, work_name, genre)
        update("블록분할", 25, 0, f"{len(arcs)}개 아크 → 블록 분할")
        blocks = analyze_blocks_from_arcs(llm, arcs, manuscripts, work_name)
    else:
        update("블록분할", 20, 0, "블록 분할 중...")
        blocks = analyze_blocks_simple(llm, manuscripts, work_name)

    update("추출중", 30, 0, f"{len(blocks)}개 블록 추출 시작")

    # Treatment 추출
    total_blocks = len(blocks)
    for i, block in enumerate(blocks):
        progress = 30 + int((i / total_blocks) * 60)
        update("추출중", progress, i, f"Block {i+1}/{total_blocks}")

        treatment = extract_treatment(llm, block, manuscripts, genre)
        result["treatments"].append(treatment)
        time.sleep(0.3)

    # Bible 추출
    update("Bible", 92, total_blocks, "Bible 추출 중...")
    result["bible"] = extract_bible(llm, manuscripts, work_name, genre)

    update("완료", 100, total_blocks, f"{total_blocks}개 블록 완료")
    return result


def process_work_wrapper(args_with_tracker: tuple) -> dict:
    """ThreadPoolExecutor용 래퍼"""
    args, tracker = args_with_tracker
    return process_work(args, tracker)


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="장르 라이브러리 구축 (Core + Extension 고밀도)")
    parser.add_argument("--input", "-i", required=True, help="작품들이 있는 폴더")
    parser.add_argument("--output", "-o", required=True, help="출력 폴더")
    parser.add_argument("--genre", "-g", required=True, choices=["investment", "wuxia", "hunter"],
                        help="장르 (investment/wuxia/hunter)")
    parser.add_argument("--model", "-m", default=PRIMARY_MODEL, help=f"모델 (기본: {PRIMARY_MODEL})")
    parser.add_argument("--workers", "-w", type=int, default=DEFAULT_WORKERS, help=f"병렬 워커 수 (기본: {DEFAULT_WORKERS})")
    args = parser.parse_args()

    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("❌ GOOGLE_API_KEY 없음")
        sys.exit(1)

    input_path = Path(args.input)
    output_path = Path(args.output)
    genre = args.genre
    genre_info = GENRE_EXTENSIONS[genre]

    works = [d for d in input_path.iterdir() if d.is_dir()]

    print(f"🚀 Genre Library Builder v2.1 (고밀도 + 회귀물 자동감지)")
    print(f"   장르: {genre_info['name']}")
    print(f"   입력: {input_path}")
    print(f"   출력: {output_path}")
    print(f"   모델: {args.model}")
    print(f"   워커: {args.workers}")
    print(f"   작품: {len(works)}개")

    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "raw_treatments").mkdir(exist_ok=True)

    print(f"\n{'='*50}")
    print(f"Phase 1: 작품별 Treatment + Bible 추출 (고밀도)")
    print(f"{'='*50}")

    # 상황판 + 로그 파일 초기화
    work_names = [w.name for w in works]
    log_path = output_path / "build_log.txt"
    tracker = ProgressTracker(work_names, log_path)
    print(f"   로그: {log_path}")

    all_results = []
    work_args = [(w, api_key, args.model, genre) for w in works]

    if RICH_AVAILABLE:
        # Rich 상황판 모드
        console = Console()
        with Live(tracker.render_table(), console=console, refresh_per_second=2) as live:
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                futures = {executor.submit(process_work_wrapper, (arg, tracker)): arg[0].name for arg in work_args}

                for future in as_completed(futures):
                    work_name = futures[future]
                    try:
                        result = future.result()
                        all_results.append(result)

                        raw_path = output_path / "raw_treatments" / f"{work_name}_tr.json"
                        with open(raw_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)

                    except Exception as e:
                        tracker.update(work_name, "실패", 0, 0, str(e)[:30])

                    # 상황판 업데이트
                    live.update(tracker.render_table())
    else:
        # 기본 출력 모드
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(process_work_wrapper, (arg, tracker)): arg[0].name for arg in work_args}

            for future in as_completed(futures):
                work_name = futures[future]
                try:
                    result = future.result()
                    all_results.append(result)

                    raw_path = output_path / "raw_treatments" / f"{work_name}_tr.json"
                    with open(raw_path, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

                    print(f"  ✅ [{work_name}] 완료: {len(result.get('treatments', []))}개 블록")

                except Exception as e:
                    print(f"  ❌ [{work_name}] 실패: {e}")

            # 중간 상황 출력
            tracker.print_simple()

    print(f"\n✅ Phase 1 완료: {len(all_results)}개 작품")

    print(f"\n{'='*50}")
    print(f"Phase 2: 패턴 마이닝 & 라이브러리 구축")
    print(f"{'='*50}")

    llm = TreatmentLLM(api_key, args.model)

    block_library = build_block_library(all_results, llm, genre)
    block_path = output_path / "block_library.json"
    with open(block_path, "w", encoding="utf-8") as f:
        json.dump(block_library, f, ensure_ascii=False, indent=2)
    print(f"  📦 Block Library: {block_path}")

    bible_library = build_bible_library(all_results, llm, genre)
    bible_path = output_path / "bible_library.json"
    with open(bible_path, "w", encoding="utf-8") as f:
        json.dump(bible_library, f, ensure_ascii=False, indent=2)
    print(f"  📖 Bible Library: {bible_path}")

    print(f"\n{'='*50}")
    print(f"✅ 완료!")
    print(f"{'='*50}")
    print(f"   장르: {genre_info['name']} (회귀물 자동감지)")
    print(f"   작품: {len(all_results)}개")
    total_blocks = sum(len(r.get("treatments", [])) for r in all_results)
    print(f"   블록: {total_blocks}개")
    print(f"   패턴: {len(block_library.get('patterns', []))}개")

    # 로그 파일에 최종 결과 기록
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n=== 완료: {datetime.now().isoformat()} ===\n")
        f.write(f"작품: {len(all_results)}개\n")
        f.write(f"블록: {total_blocks}개\n")
        f.write(f"패턴: {len(block_library.get('patterns', []))}개\n")
        for r in all_results:
            f.write(f"  - {r['work_name']}: {len(r.get('treatments', []))}블록, {r.get('episode_count', 0)}화\n")


if __name__ == "__main__":
    main()
