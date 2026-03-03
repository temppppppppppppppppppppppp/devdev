"""
Bible Builder - 설정집 생성 도구
================================
인터뷰 방식으로 Bible(bi) 파일 생성
AI 추천 + 사용자 선택/수정

사용법:
    python tools/bible_builder.py --output path/to/output_bi.json --genre investment
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google-genai 패키지가 없습니다. pip install google-genai")


class BibleBuilder:
    """Bible 설정집 생성 도구"""

    GENRES = {
        "investment": {
            "name": "투자물",
            "hud_type": "FinanceHUD",
            "archetypes": ["회귀 + 투자", "현대 재벌물", "금융 스릴러", "복수 + 투자"],
            "typical_settings": ["1990년대 IMF", "2008년 금융위기", "현대 주식시장", "가상화폐"],
        },
        "wuxia": {
            "name": "무협",
            "hud_type": "MartialHUD",
            "archetypes": ["정통 무협", "회귀 무협", "현대 무협", "사이버펑크 무협"],
            "typical_settings": ["중원 강호", "변방 소문파", "마교", "황실"],
        },
        "hunter": {
            "name": "헌터물",
            "hud_type": "HunterHUD",
            "archetypes": ["회귀 헌터", "각성 헌터", "던전 공략", "타워 클라이밍"],
            "typical_settings": ["현대 한국", "이세계", "포스트 아포칼립스", "게임 시스템"],
        },
    }

    def __init__(self, output_path: str, genre: str = "investment"):
        self.output_path = Path(output_path)
        self.genre = genre
        self.genre_info = self.GENRES.get(genre, self.GENRES["investment"])
        self.bible = {}

        # Gemini 클라이언트
        if GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                self.model = "gemini-2.5-flash"
            else:
                self.client = None
                print("⚠️ GOOGLE_API_KEY 환경변수가 없습니다.")
        else:
            self.client = None

    def _call_llm(self, prompt: str, temperature: float = 0.9) -> str:
        """LLM 호출"""
        if not self.client:
            return None

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=8192,
                ),
            )
            return response.text
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            return None

    def _parse_json(self, text: str) -> dict:
        """JSON 파싱 (```json 제거)"""
        if not text:
            return {}
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            return {}

    def _show_options(self, options: list, prompt_text: str) -> str:
        """옵션 표시 및 선택"""
        print(f"\n{prompt_text}")
        for i, opt in enumerate(options, 1):
            if isinstance(opt, dict):
                print(f"  [{i}] {opt.get('label', opt)}")
                if opt.get("desc"):
                    print(f"      → {opt['desc']}")
            else:
                print(f"  [{i}] {opt}")
        print("  [0] 직접 입력")

        choice = input("\n선택: ").strip()

        if choice == "0":
            return input("직접 입력: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                opt = options[idx]
                return opt.get("label", opt) if isinstance(opt, dict) else opt
        except ValueError:
            pass

        return options[0] if options else ""

    def _confirm_or_edit(self, label: str, value: Any) -> Any:
        """확인 또는 수정"""
        if isinstance(value, dict):
            print(f"\n📋 {label}:")
            for k, v in value.items():
                print(f"  {k}: {v}")
        elif isinstance(value, list):
            print(f"\n📋 {label}:")
            for item in value[:5]:
                print(f"  - {item}")
            if len(value) > 5:
                print(f"  ... 외 {len(value) - 5}개")
        else:
            print(f"\n📋 {label}: {value}")

        choice = input("[Enter] 승인 / [e] 수정: ").strip().lower()

        if choice == "e":
            if isinstance(value, dict):
                key = input("수정할 키: ").strip()
                if key in value:
                    new_val = input(f"새 값 ({key}): ").strip()
                    value[key] = new_val
            elif isinstance(value, list):
                action = input("[a] 추가 / [d] 삭제 / [r] 전체 교체: ").strip().lower()
                if action == "a":
                    new_item = input("추가할 항목: ").strip()
                    value.append(new_item)
                elif action == "d":
                    idx = int(input("삭제할 번호 (1부터): ").strip()) - 1
                    if 0 <= idx < len(value):
                        value.pop(idx)
                elif action == "r":
                    new_list = input("새 목록 (쉼표 구분): ").strip().split(",")
                    value = [x.strip() for x in new_list]
            else:
                value = input("새 값: ").strip() or value

        return value

    # ===========================================
    # Step 1: 기본 정보
    # ===========================================

    def step1_basic_info(self) -> dict:
        """Step 1: 기본 프로젝트 정보"""
        print("\n" + "=" * 60)
        print("📝 Step 1: 기본 정보")
        print("=" * 60)

        # 제목
        title = input("\n작품 제목: ").strip()
        if not title:
            title = "미정"

        # 아키타입
        archetype = self._show_options(self.genre_info["archetypes"], f"🎭 장르 아키타입 ({self.genre_info['name']})")

        # 로그라인 - AI 추천
        print("\n🤖 로그라인 추천 생성 중...")
        logline_options = self._generate_logline_options(title, archetype)

        if logline_options:
            logline = self._show_options(logline_options, "📜 로그라인 선택")
        else:
            logline = input("로그라인 직접 입력: ").strip()

        # 분량
        print("\n📊 분량 설정")
        total_episodes = input("총 에피소드 수 (기본 200): ").strip()
        total_episodes = int(total_episodes) if total_episodes.isdigit() else 200

        eps_per_arc = input("Arc당 에피소드 (기본 5): ").strip()
        eps_per_arc = int(eps_per_arc) if eps_per_arc.isdigit() else 5

        meta_info = {
            "title": title,
            "grand_objective": logline,
            "genre_archetype": f"{self.genre} + {archetype}",
            "logline": logline,
            "total_episodes": total_episodes,
            "episodes_per_arc": eps_per_arc,
            "arcs_per_volume": 5,
        }

        return self._confirm_or_edit("MetaInfo", meta_info)

    def _generate_logline_options(self, title: str, archetype: str) -> list:
        """로그라인 옵션 생성"""
        prompt = f"""웹소설 로그라인을 3개 추천해주세요.

장르: {self.genre_info["name"]}
아키타입: {archetype}
제목: {title}

JSON 형식:
```json
[
  {{"label": "로그라인1", "desc": "포인트 설명"}},
  {{"label": "로그라인2", "desc": "포인트 설명"}},
  {{"label": "로그라인3", "desc": "포인트 설명"}}
]
```

규칙:
1. 1-2문장으로 핵심 컨셉 전달
2. 주인공의 목표와 장애물 명시
3. 차별화 포인트 포함

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        return self._parse_json(response) or []

    # ===========================================
    # Step 2: 주인공
    # ===========================================

    def step2_protagonist(self, meta_info: dict) -> dict:
        """Step 2: 주인공 설정"""
        print("\n" + "=" * 60)
        print("🦸 Step 2: 주인공")
        print("=" * 60)

        # 이름
        name = input("\n주인공 이름: ").strip() or "미정"

        # AI 추천
        print("\n🤖 주인공 설정 추천 생성 중...")
        protag_options = self._generate_protagonist_options(meta_info, name)

        if protag_options:
            print("\n추천 설정:")
            for i, opt in enumerate(protag_options, 1):
                print(f"\n  [{i}] {opt.get('edge', '')[:50]}...")
                print(f"      욕망: {opt.get('desire', '')[:50]}")
                print(f"      위기: {opt.get('crisis', '')[:50]}")
            print("  [0] 직접 입력")

            choice = input("\n선택: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(protag_options):
                selected = protag_options[int(choice) - 1]
            else:
                selected = self._manual_protagonist_input(name)
        else:
            selected = self._manual_protagonist_input(name)

        core_identity = {
            "protagonist": name,
            "protagonist_faction": selected.get("faction", "독립"),
            "edge": selected.get("edge", ""),
            "desire": selected.get("desire", ""),
            "crisis": selected.get("crisis", ""),
        }

        return self._confirm_or_edit("CoreIdentity", core_identity)

    def _generate_protagonist_options(self, meta_info: dict, name: str) -> list:
        """주인공 설정 옵션 생성"""
        prompt = f"""웹소설 주인공 설정을 3개 추천해주세요.

장르: {self.genre_info["name"]}
로그라인: {meta_info.get("logline", "")}
주인공 이름: {name}

JSON 형식:
```json
[
  {{
    "faction": "소속/세력",
    "edge": "주인공만의 강점 (미래지식, 특수능력 등)",
    "desire": "핵심 욕망/목표",
    "crisis": "초기 위기 상황"
  }},
  ...
]
```

규칙:
1. edge는 장르에 맞는 차별화 포인트
2. desire는 스토리를 이끄는 동기
3. crisis는 초반 텐션을 만드는 장애물

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        return self._parse_json(response) or []

    def _manual_protagonist_input(self, name: str) -> dict:
        """수동 주인공 입력"""
        return {
            "faction": input("소속/세력: ").strip() or "독립",
            "edge": input("강점 (엣지): ").strip() or "",
            "desire": input("욕망/목표: ").strip() or "",
            "crisis": input("초기 위기: ").strip() or "",
        }

    # ===========================================
    # Step 3: 상업적 코드
    # ===========================================

    def step3_commercial_code(self, meta_info: dict, core_identity: dict) -> dict:
        """Step 3: 상업적 코드"""
        print("\n" + "=" * 60)
        print("💰 Step 3: 상업적 코드")
        print("=" * 60)

        print("\n🤖 상업적 코드 추천 생성 중...")

        prompt = f"""웹소설 상업적 코드를 추천해주세요.

장르: {self.genre_info["name"]}
로그라인: {meta_info.get("logline", "")}
주인공 강점: {core_identity.get("edge", "")}

JSON 형식:
```json
{{
  "cider_point": "독자가 통쾌함을 느끼는 포인트 (구체적으로)",
  "success_device": "성공의 증거 (수익률, 레벨업, 명성 등)",
  "attitude": "주인공의 태도 (능동적 설계자/수동적 반응자/복수귀 등)"
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        commercial = self._parse_json(response)

        if not commercial:
            commercial = {
                "cider_point": input("사이다 포인트: ").strip(),
                "success_device": input("성공의 증거: ").strip(),
                "attitude": input("주인공 태도: ").strip(),
            }

        return self._confirm_or_edit("CommercialCode", commercial)

    # ===========================================
    # Step 4: 장르별 HUD
    # ===========================================

    def step4_genre_hud(self, core_identity: dict) -> dict:
        """Step 4: 장르별 HUD 초기 상태"""
        print("\n" + "=" * 60)
        print(f"📊 Step 4: {self.genre_info['hud_type']}")
        print("=" * 60)

        if self.genre == "investment":
            return self._build_finance_hud(core_identity)
        elif self.genre == "wuxia":
            return self._build_martial_hud(core_identity)
        elif self.genre == "hunter":
            return self._build_hunter_hud(core_identity)
        else:
            return {}

    def _build_finance_hud(self, core_identity: dict) -> dict:
        """투자물 HUD"""
        name = core_identity.get("protagonist", "주인공")

        print("\n💵 초기 재정 상태")
        total_assets = input("총 자산 (예: 50만원): ").strip() or "50만원"
        debt = input("부채 (예: 3000만원, 없으면 엔터): ").strip() or "없음"

        print("\n🤖 투자 스타일 추천 생성 중...")
        prompt = f"""투자물 주인공의 투자 스타일을 추천해주세요.

주인공: {name}
강점: {core_identity.get("edge", "")}

JSON 형식:
```json
{{
  "investment_style": "투자 스타일 (예: 미래 지식 기반 역발상 투자)",
  "risk_tolerance": "리스크 성향 (저위험/중위험/고위험/극고위험)"
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        style = self._parse_json(response) or {}

        hud = {
            "Protagonist": {
                "actual_truth": {
                    "name": name,
                    "alias": "없음",
                    "age": int(input("나이: ").strip() or "28"),
                    "rank": input("초기 직위 (예: 무직): ").strip() or "무직",
                    "financial_status": {
                        "total_assets": total_assets,
                        "liquid_cash": total_assets,
                        "stocks": [],
                        "real_estate": [],
                        "foreign_currency": {"USD": 0, "JPY": 0},
                        "debt": debt,
                    },
                    "portfolio_history": [
                        {
                            "episode": 0,
                            "month": input("시작 시점 (예: 1996-01): ").strip() or "1996-01",
                            "total_assets": total_assets,
                            "event": "시작점",
                        }
                    ],
                    "investment_style": style.get("investment_style", "미정"),
                    "risk_tolerance": style.get("risk_tolerance", "중위험"),
                    "network_level": {
                        "financial_sector": 0,
                        "political_sector": 0,
                        "business_sector": 0,
                        "underground_sector": 0,
                    },
                    "credentials": [],
                    "current_objective": input("당장의 목표: ").strip() or "종잣돈 불리기",
                    "mid_term_goal": input("중기 목표: ").strip() or "자본 확보",
                    "final_goal": input("최종 목표: ").strip() or "정상에 서기",
                    "causal_injuries": input("트라우마/약점: ").strip() or "없음",
                },
                "public_reputation": {
                    "identity": input("외부에 알려진 신분: ").strip() or "평범한 청년",
                    "wealth_level": "빈곤층",
                    "perceived_influence": "없음",
                    "credit_rating": input("신용등급: ").strip() or "일반",
                },
            }
        }

        return hud

    def _build_martial_hud(self, core_identity: dict) -> dict:
        """무협 HUD"""
        name = core_identity.get("protagonist", "주인공")

        print("\n⚔️ 초기 무공 상태")

        hud = {
            "Protagonist": {
                "actual_truth": {
                    "name": name,
                    "alias": input("별호 (없으면 엔터): ").strip() or "없음",
                    "age": int(input("나이: ").strip() or "20"),
                    "rank": input("초기 경지 (예: 삼류): ").strip() or "삼류",
                    "martial_arts": [],
                    "internal_energy": int(input("내공 수치 (0-100): ").strip() or "10"),
                    "faction": input("문파/세력: ").strip() or "무소속",
                    "reputation": {"righteous": 0, "evil": 0, "neutral": 50},
                    "injuries": [],
                    "current_objective": input("당장의 목표: ").strip() or "생존",
                    "final_goal": input("최종 목표: ").strip() or "무림 정상",
                },
                "public_reputation": {
                    "identity": input("강호에 알려진 신분: ").strip() or "무명 협객",
                    "rank_perception": "말류",
                    "fame_level": 0,
                },
            }
        }

        return hud

    def _build_hunter_hud(self, core_identity: dict) -> dict:
        """헌터물 HUD"""
        name = core_identity.get("protagonist", "주인공")

        print("\n🎮 초기 헌터 상태")

        hud = {
            "Protagonist": {
                "actual_truth": {
                    "name": name,
                    "hunter_name": input("헌터명 (없으면 엔터): ").strip() or name,
                    "age": int(input("나이: ").strip() or "25"),
                    "rank": input("초기 등급 (E/D/C/B/A/S): ").strip() or "E",
                    "class": input("직업 (전사/마법사/궁수/힐러 등): ").strip() or "미각성",
                    "level": int(input("레벨 (1-100): ").strip() or "1"),
                    "skills": [],
                    "stats": {"strength": 10, "agility": 10, "intelligence": 10, "vitality": 10, "luck": 10},
                    "guild": input("소속 길드: ").strip() or "무소속",
                    "balance": input("잔고: ").strip() or "100만원",
                    "current_objective": input("당장의 목표: ").strip() or "각성/생존",
                    "final_goal": input("최종 목표: ").strip() or "최강의 헌터",
                },
                "public_reputation": {
                    "identity": input("대외적 신분: ").strip() or "E급 헌터",
                    "rank_perception": "E급",
                    "fame_level": 0,
                },
            }
        }

        return hud

    # ===========================================
    # Step 5: 세계 상태
    # ===========================================

    def step5_world_state(self, hud: dict) -> dict:
        """Step 5: 세계 상태"""
        print("\n" + "=" * 60)
        print("🌍 Step 5: 세계 상태")
        print("=" * 60)

        # 기본 설정
        setting = self._show_options(self.genre_info["typical_settings"], "🏛️ 배경 선택")

        era = input("시대/시점 (예: 1996년 1월): ").strip() or "현대"
        location = input("시작 장소: ").strip() or "미정"

        world_state = {"CurrentEra": era, "CurrentLocation": location, "setting": setting, "KarmaMatrix": {}}

        # 장르별 추가 정보
        if self.genre == "investment":
            world_state["economic_context"] = self._build_economic_context(era)

        return self._confirm_or_edit("WorldState", world_state)

    def _build_economic_context(self, era: str) -> dict:
        """경제 컨텍스트 구축"""
        print("\n📈 경제 상황 설정")

        return {
            "kospi": int(input("KOSPI 지수 (예: 850): ").strip() or "1000"),
            "usd_krw": int(input("USD/KRW 환율 (예: 780): ").strip() or "1200"),
            "interest_rate": input("금리 (예: 12%): ").strip() or "5%",
            "upcoming_events": [],  # Step 7에서 채움
        }

    # ===========================================
    # Step 6: NPC
    # ===========================================

    def step6_npcs(self, meta_info: dict, core_identity: dict) -> list:
        """Step 6: 주요 NPC"""
        print("\n" + "=" * 60)
        print("👥 Step 6: 주요 NPC")
        print("=" * 60)

        print("\n🤖 NPC 추천 생성 중...")

        prompt = f"""웹소설 주요 NPC를 5명 추천해주세요.

장르: {self.genre_info["name"]}
로그라인: {meta_info.get("logline", "")}
주인공: {core_identity.get("protagonist", "")}
주인공 위기: {core_identity.get("crisis", "")}

JSON 형식:
```json
[
  {{
    "name": "이름",
    "role": "역할 (메인 빌런/조력자/히로인/멘토/라이벌)",
    "desc": "간단한 설명 (100자 이내)",
    "relationship": "주인공과의 관계",
    "weakness": "약점"
  }},
  ...
]
```

필수 역할:
1. 메인 빌런 1명
2. 조력자 1명
3. 히로인/러브라인 1명
4. 멘토 또는 라이벌 1명
5. 초반 장애물 1명

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        npcs = self._parse_json(response) or []

        if not npcs:
            print("\n수동 입력:")
            npcs = []
            for role in ["메인 빌런", "조력자", "히로인", "멘토", "초반 장애물"]:
                print(f"\n  [{role}]")
                npcs.append(
                    {
                        "name": input("    이름: ").strip() or f"{role}",
                        "role": role,
                        "desc": input("    설명: ").strip() or "",
                        "relationship": input("    관계: ").strip() or "",
                        "weakness": input("    약점: ").strip() or "",
                    }
                )

        # NPC 검토
        print("\n생성된 NPC:")
        for i, npc in enumerate(npcs, 1):
            print(f"  [{i}] {npc['name']} ({npc['role']})")
            print(f"      {npc.get('desc', '')[:60]}...")

        action = input("\n[Enter] 승인 / [a] 추가 / [d] 삭제 / [e] 수정: ").strip().lower()

        if action == "a":
            new_npc = {
                "name": input("이름: ").strip(),
                "role": input("역할: ").strip(),
                "desc": input("설명: ").strip(),
                "relationship": input("관계: ").strip(),
                "weakness": input("약점: ").strip(),
            }
            npcs.append(new_npc)
        elif action == "d":
            idx = int(input("삭제할 번호: ").strip()) - 1
            if 0 <= idx < len(npcs):
                npcs.pop(idx)
        elif action == "e":
            idx = int(input("수정할 번호: ").strip()) - 1
            if 0 <= idx < len(npcs):
                field = input("수정할 필드 (name/role/desc): ").strip()
                new_val = input("새 값: ").strip()
                if field in npcs[idx]:
                    npcs[idx][field] = new_val

        return npcs

    # ===========================================
    # Step 7: 역사 이벤트 (투자물)
    # ===========================================

    def step7_historical_events(self, world_state: dict) -> list:
        """Step 7: 역사 이벤트 (투자물 전용)"""
        if self.genre != "investment":
            return []

        print("\n" + "=" * 60)
        print("📅 Step 7: 활용 가능한 역사 이벤트")
        print("=" * 60)

        era = world_state.get("CurrentEra", "")

        print("\n🤖 역사 이벤트 추천 생성 중...")

        prompt = f"""투자물에서 활용 가능한 역사적 경제 이벤트를 추천해주세요.

시작 시점: {era}

JSON 형식:
```json
[
  {{"month": "YYYY-MM", "event": "이벤트명", "impact": "시장 영향"}},
  ...
]
```

규칙:
1. 시작 시점 이후 이벤트만
2. 10개 내외
3. 실제 역사 기반
4. 투자에 활용 가능한 것

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        events = self._parse_json(response) or []

        if not events:
            print("\n역사 이벤트를 수동으로 추가하세요.")
            events = []
            while True:
                month = input("월 (YYYY-MM, 종료=엔터): ").strip()
                if not month:
                    break
                event = input("이벤트: ").strip()
                impact = input("영향: ").strip()
                events.append({"month": month, "event": event, "impact": impact})

        print("\n생성된 이벤트:")
        for e in events[:10]:
            print(f"  {e['month']}: {e['event']} → {e['impact']}")

        return events

    # ===========================================
    # Step 8: 장르 규칙
    # ===========================================

    def step8_genre_rules(self) -> dict:
        """Step 8: 장르 규칙"""
        print("\n" + "=" * 60)
        print("📜 Step 8: 장르 규칙")
        print("=" * 60)

        print("\n🤖 장르 규칙 생성 중...")

        prompt = f"""웹소설 {self.genre_info["name"]} 장르의 규칙을 정의해주세요.

JSON 형식:
```json
{{
  "must_include": ["필수 요소1", "필수 요소2", "필수 요소3"],
  "forbidden": ["금지 사항1", "금지 사항2", "금지 사항3"],
  "tension_devices": ["긴장 장치1", "긴장 장치2", "긴장 장치3"]
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        rules = self._parse_json(response)

        if not rules:
            rules = {"must_include": [], "forbidden": [], "tension_devices": []}

        return self._confirm_or_edit("GenreRules", rules)

    # ===========================================
    # Step 9: 씨앗 (복선)
    # ===========================================

    def step9_seeds(self, npcs: list, meta_info: dict) -> list:
        """Step 9: 초기 씨앗 (복선)"""
        print("\n" + "=" * 60)
        print("🌱 Step 9: 복선 씨앗")
        print("=" * 60)

        print("\n🤖 복선 씨앗 추천 생성 중...")

        npc_names = [n["name"] for n in npcs]

        prompt = f"""스토리 복선 씨앗을 추천해주세요.

장르: {self.genre_info["name"]}
로그라인: {meta_info.get("logline", "")}
주요 NPC: {", ".join(npc_names)}

JSON 형식:
```json
[
  {{
    "id": "S-001",
    "category": "인물|사건|아이템|세계관",
    "description": "복선 내용",
    "planted_ep": 1,
    "target_harvest_ep": 30
  }},
  ...
]
```

4-5개 추천. JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        seeds = self._parse_json(response) or []

        # 기본 필드 추가
        for seed in seeds:
            seed["status"] = "active"
            seed["echo_count"] = 0
            seed["harvested_ep"] = None

        print("\n생성된 복선:")
        for s in seeds:
            print(f"  [{s['id']}] {s['category']}: {s['description'][:50]}...")

        return seeds

    # ===========================================
    # 최종 조립 및 저장
    # ===========================================

    def assemble_bible(self, components: dict) -> dict:
        """Bible 조립"""
        bible = {
            "_schema_version": "2.0",
            "_schema_description": f"{self.genre_info['name']} 장르 Bible",
            "_last_updated": "",
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": components.get("meta_info", {}),
                    "CoreIdentity": components.get("core_identity", {}),
                    "CommercialCode": components.get("commercial_code", {}),
                },
                "protagonist_config": {
                    "world_origin": "현대인" if self.genre == "investment" else "강호인",
                    "incarnation_type": "회귀자",
                },
                self.genre_info["hud_type"]: components.get("hud", {}),
                "WorldState": components.get("world_state", {}),
                "AssetLibrary": {
                    "KeyNPCs": components.get("npcs", []),
                    "KeyItems": [],
                    "KeyLocations": [],
                    "Persona": "",
                    "SpeechStyle": {"tone": "", "vocabulary": "", "inner_monologue": ""},
                },
                "Seeds": components.get("seeds", []),
                "GenreRules": components.get("genre_rules", {}),
            },
        }

        # 투자물 전용
        if self.genre == "investment":
            bible["MasterBible"]["HistoricalEvents"] = {
                "_description": "투자물에서 활용 가능한 실제 역사적 이벤트 DB",
                "events": components.get("historical_events", []),
            }

        return bible

    def save_bible(self, bible: dict):
        """Bible 저장"""
        from datetime import datetime

        bible["_last_updated"] = datetime.now().strftime("%Y-%m-%d")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(bible, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 저장 완료: {self.output_path}")

    # ===========================================
    # 메인 실행
    # ===========================================

    def run(self):
        """전체 파이프라인 실행"""
        print("\n" + "=" * 60)
        print(f"🚀 Bible Builder 시작 ({self.genre_info['name']})")
        print("=" * 60)

        components = {}

        # Step 1: 기본 정보
        components["meta_info"] = self.step1_basic_info()

        # Step 2: 주인공
        components["core_identity"] = self.step2_protagonist(components["meta_info"])

        # Step 3: 상업적 코드
        components["commercial_code"] = self.step3_commercial_code(components["meta_info"], components["core_identity"])

        # Step 4: 장르별 HUD
        components["hud"] = self.step4_genre_hud(components["core_identity"])

        # Step 5: 세계 상태
        components["world_state"] = self.step5_world_state(components["hud"])

        # Step 6: NPC
        components["npcs"] = self.step6_npcs(components["meta_info"], components["core_identity"])

        # Step 7: 역사 이벤트 (투자물)
        components["historical_events"] = self.step7_historical_events(components["world_state"])

        # Step 8: 장르 규칙
        components["genre_rules"] = self.step8_genre_rules()

        # Step 9: 복선 씨앗
        components["seeds"] = self.step9_seeds(components["npcs"], components["meta_info"])

        # 조립
        bible = self.assemble_bible(components)

        # 최종 확인
        print("\n" + "=" * 60)
        print("📋 최종 확인")
        print("=" * 60)
        print(f"  제목: {components['meta_info'].get('title')}")
        print(f"  장르: {components['meta_info'].get('genre_archetype')}")
        print(f"  주인공: {components['core_identity'].get('protagonist')}")
        print(f"  NPC: {len(components['npcs'])}명")
        print(f"  복선: {len(components['seeds'])}개")

        if input("\n저장하시겠습니까? [Enter] 예 / [n] 아니오: ").strip().lower() != "n":
            self.save_bible(bible)
        else:
            print("취소됨")

        print("\n🎉 완료!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Bible Builder")
    parser.add_argument("--output", required=True, help="출력 Bible JSON 경로")
    parser.add_argument(
        "--genre", default="investment", choices=["investment", "wuxia", "hunter"], help="장르 (기본: investment)"
    )

    args = parser.parse_args()

    builder = BibleBuilder(output_path=args.output, genre=args.genre)
    builder.run()


if __name__ == "__main__":
    main()
