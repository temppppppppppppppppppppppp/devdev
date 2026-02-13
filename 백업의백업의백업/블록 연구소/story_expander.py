"""
Story Expander v3 - 다중 장르 스토리 확장 도구
==============================================
대강의 컨셉 입력 → Bible + Treatment 자동 생성

지원 장르:
- investment: 투자물 (회귀 투자, 재벌물)
- wuxia: 무협 (정통/회귀 무협)
- hunter: 헌터물 (던전물, 각성물)

사용법:
    python story_expander.py --output-dir outputs/my_project

새 장르 추가:
    1. genres/{genre_id}/ 폴더 생성
    2. __init__.py에 {Genre}Genre 클래스 정의
    3. genres/__init__.py에 등록
"""

import io
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Windows UTF-8 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 현재 폴더를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

# 스피너 유틸 임포트
try:
    from utils.spinner import (
        PhaseIndicator,
        ProgressBar,
        Spinner,
        print_error,
        print_header,
        print_info,
        print_success,
        print_table,
        print_tip,
        print_warning,
    )

    SPINNER_AVAILABLE = True
except ImportError as e:
    SPINNER_AVAILABLE = False
    print(f"[!] 스피너 로드 실패: {e}")

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("[!] google-genai 패키지가 없습니다. pip install google-genai")

# 장르 모듈 임포트
try:
    from genres import get_genre, list_genres

    GENRES_AVAILABLE = True
except ImportError:
    GENRES_AVAILABLE = False
    print("[!] genres 모듈을 찾을 수 없습니다.")


class StoryExpander:
    """스토리 확장기 - 컨셉 → Bible + Treatment"""

    def __init__(self, output_dir: str, genre_id: str = None):
        self.output_dir = Path(output_dir)
        self.genre_id = genre_id
        self.genre = None
        self.advisor = None
        self.concept = ""
        self.extracted = {}
        self.bible = {}
        self.treatment = []
        self.used_figures = []

        # Gemini 클라이언트
        if GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                self.model = "gemini-2.5-flash"
            else:
                self.client = None
                print("[!] GOOGLE_API_KEY 없음")
        else:
            self.client = None

    def _call_llm(self, prompt: str, temperature: float = 0.85, max_tokens: int = 8192, spinner_msg: str = None) -> str:
        """LLM 호출"""
        if not self.client:
            return None

        spinner = None
        if SPINNER_AVAILABLE and spinner_msg:
            spinner = Spinner(spinner_msg, style="braille")
            spinner.start()

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            if spinner:
                spinner.stop(f"{spinner_msg} 완료")
            return response.text
        except Exception as e:
            if spinner:
                spinner.stop()
            if SPINNER_AVAILABLE:
                print_error(f"LLM 오류: {e}")
            else:
                print(f"[X] LLM 오류: {e}")
            return None

    def _parse_json(self, text: str) -> Any:
        """JSON 파싱"""
        if not text:
            return None
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except:
            return None

    # ===========================================
    # Phase 0: 장르 선택 및 컨셉 입력
    # ===========================================

    def phase0_select_genre(self) -> str:
        """장르 선택"""
        if SPINNER_AVAILABLE:
            print_header("Phase 0: 장르 선택", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 0: 장르 선택")
            print("=" * 60)

        if not GENRES_AVAILABLE:
            if SPINNER_AVAILABLE:
                print_warning("장르 모듈 로드 실패. 기본값 사용.")
            else:
                print("[!] 장르 모듈 로드 실패. 기본값 사용.")
            return "investment"

        genres = list_genres()

        print("\n사용 가능한 장르:")
        genre_list = list(genres.keys())
        for i, (gid, info) in enumerate(genres.items(), 1):
            print(f"  [{i}] {info['name']} ({gid})")
            print(f"      {info['desc']}")

        choice = input("\n선택 (번호 또는 ID): ").strip()

        # 번호로 선택
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(genre_list):
                selected = genre_list[idx]
            else:
                selected = "investment"
        # ID로 선택
        elif choice in genres:
            selected = choice
        else:
            selected = "investment"

        self.genre_id = selected
        self.genre = get_genre(selected)

        if SPINNER_AVAILABLE:
            print_success(f"선택된 장르: {self.genre.GENRE_NAME}")
        else:
            print(f"\n[v] 선택된 장르: {self.genre.GENRE_NAME}")

        return selected

    def phase0_input_concept(self) -> str:
        """컨셉 입력"""
        if SPINNER_AVAILABLE:
            print_header("스토리 컨셉 입력", style="simple")
        else:
            print("\n" + "=" * 60)
            print("[*] 스토리 컨셉 입력")
            print("=" * 60)

        genre_info = self.genre.get_genre_info()

        print(f"""
장르: {genre_info["name"]}
아키타입 예시: {", ".join(genre_info["archetypes"][:3])}

대강의 스토리 컨셉을 자유롭게 입력하세요.
예시:
""")

        # 장르별 예시
        if self.genre_id == "investment":
            print("  - 재벌 3세가 비참하게 죽고 회귀, IMF 직전으로 돌아와서...")
            print("  - 무명 트레이더가 2008년 금융위기를 예측해서...")
        elif self.genre_id == "wuxia":
            print("  - 망한 소문파 출신이 회귀해서 문파를 재건...")
            print("  - 마교에 몰살당한 후 과거로 돌아가 복수...")
        elif self.genre_id == "hunter":
            print("  - E급 헌터가 죽고 회귀, 숨겨진 던전의 위치를 알고 있어...")
            print("  - 각성 실패한 줄 알았는데 유일무이한 능력 각성...")

        print("\n[여러 줄 입력 가능. 빈 줄 입력 시 완료]")

        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)

        self.concept = "\n".join(lines)
        if SPINNER_AVAILABLE:
            print_success(f"입력된 컨셉 ({len(self.concept)}자)")
        else:
            print(f"\n[v] 입력된 컨셉 ({len(self.concept)}자)")
        return self.concept

    def phase0_analyze_concept(self) -> dict:
        """컨셉 분석"""
        if SPINNER_AVAILABLE:
            print_info("컨셉 분석 시작...")
        else:
            print("\n[*] 컨셉 분석 중...")

        genre_info = self.genre.get_genre_info()
        power_template = self.genre.get_power_progression_template()

        prompt = f"""다음 스토리 컨셉을 분석해서 핵심 요소를 추출하세요.

## 장르: {genre_info["name"]}
## 컨셉
{self.concept}

## 추출할 요소 (JSON)
```json
{{
  "title_suggestions": ["제목 후보1", "제목 후보2", "제목 후보3"],

  "protagonist": {{
    "background": "출신/배경",
    "death_cause": "사망 원인 (회귀물인 경우)",
    "regression_point": "회귀 시점 (회귀물인 경우)",
    "starting_condition": "시작 상태",
    "unique_edge": "주인공만의 강점",
    "main_goal": "최종 목표",
    "personality_hints": "성격"
  }},

  "timeline": {{
    "start_era": "시작 시점",
    "story_span": "예상 스토리 기간"
  }},

  "major_plot_points": ["주요 플롯 포인트1", "플롯2", "플롯3"],

  "power_progression": {{
    "initial": "초기 상태",
    "mid": "중반 상태",
    "final": "최종 상태"
  }},

  "suggested_antagonists": [{{"type": "유형", "desc": "설명"}}],
  "themes": ["테마1", "테마2"],
  "tone": "작품 톤"
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt, spinner_msg="컨셉 분석")
        self.extracted = self._parse_json(response) or {}

        if self.extracted:
            timeline = self.extracted.get("timeline", {})
            start_era = timeline.get("start_era", "")

            # 어드바이저 초기화
            self.advisor = self.genre.get_advisor(start_era)

            if SPINNER_AVAILABLE:
                print_success("컨셉 분석 완료")
            else:
                print("\n[v] 컨셉 분석 완료")
            print(f"  제목 후보: {', '.join(self.extracted.get('title_suggestions', []))}")

            # 장르별 추천 표시
            self._show_advisor_recommendations(1)

        return self.extracted

    def _show_advisor_recommendations(self, block_num: int):
        """어드바이저 추천 표시"""
        if not self.advisor:
            return

        if SPINNER_AVAILABLE:
            print_header("전략 어드바이저 추천", style="simple")
        else:
            print("\n" + "-" * 40)
            print("[!] 전략 어드바이저 추천")
            print("-" * 40)

        advice = self.advisor.generate_block_advice(block_num, used_figures=self.used_figures)

        if self.genre_id == "investment":
            inv = advice.get("investment", {})
            print(f"\n[Phase] {inv.get('current_phase', '')}")
            for item in inv.get("hot_investments", [])[:3]:
                if SPINNER_AVAILABLE:
                    print_success(f"{item['type']}: {item['reason']}")
                else:
                    print(f"  [v] {item['type']}: {item['reason']}")
            for avoid in inv.get("avoid", [])[:2]:
                if SPINNER_AVAILABLE:
                    print_error(f"회피: {avoid}")
                else:
                    print(f"  [X] 회피: {avoid}")

        elif self.genre_id == "wuxia":
            martial = advice.get("martial_growth", {})
            print(f"\n[Phase] {martial.get('phase', '')}")
            print(f"  목표 경지: {martial.get('target_rank', '')}")
            for training in martial.get("recommended_training", [])[:3]:
                if SPINNER_AVAILABLE:
                    print_success(training)
                else:
                    print(f"  [v] {training}")

        elif self.genre_id == "hunter":
            growth = advice.get("growth", {})
            dungeon = advice.get("dungeon", {})
            print(f"\n[Phase] {growth.get('phase', '')}")
            print(f"  목표 등급: {growth.get('target_rank', '')}")
            print(f"  추천 던전: {dungeon.get('type', '')} ({dungeon.get('rank', '')})")

        # 인물 추천
        figures = advice.get("suggested_figures", [])
        if figures:
            if SPINNER_AVAILABLE:
                print_info("등장 추천 인물:")
            else:
                print("\n[*] 등장 추천 인물:")
            for fig in figures[:2]:
                print(f"  - {fig.get('name', '')}: {fig.get('story_hook', '')[:40]}...")

        if SPINNER_AVAILABLE:
            print_tip(advice.get("overall_tip", ""))
        else:
            print(f"\n[Tip] {advice.get('overall_tip', '')}")

    # ===========================================
    # Phase 1: Bible 생성
    # ===========================================

    def phase1_generate_bible(self) -> dict:
        """Bible 생성"""
        if SPINNER_AVAILABLE:
            print_header("Phase 1: Bible 생성", style="double")
            # 단계 표시
            phases = ["메타 정보", "주인공 상세", "상업 코드", "HUD 초기화", "NPC 생성", "세계 상태", "복선 씨앗"]
            indicator = PhaseIndicator(phases)
            indicator.show()
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 1: Bible 생성")
            print("=" * 60)

        meta_info = self._generate_meta_info()
        if SPINNER_AVAILABLE:
            indicator.next()
            indicator.show()

        protagonist = self._generate_protagonist_detail()
        if SPINNER_AVAILABLE:
            indicator.next()
            indicator.show()

        commercial = self._generate_commercial_code()
        if SPINNER_AVAILABLE:
            indicator.next()
            indicator.show()

        hud = self._generate_initial_hud(protagonist)
        if SPINNER_AVAILABLE:
            indicator.next()
            indicator.show()

        npcs = self._generate_npcs()
        if SPINNER_AVAILABLE:
            indicator.next()
            indicator.show()

        world_state = self._generate_world_state()
        events = self.genre.get_historical_events(self.extracted.get("timeline", {}).get("start_era", ""))
        rules = self.genre.get_genre_rules()
        if SPINNER_AVAILABLE:
            indicator.next()
            indicator.show()

        seeds = self._generate_seeds(npcs)
        if SPINNER_AVAILABLE:
            indicator.complete()
            indicator.show()

        self.bible = {
            "_schema_version": "2.0",
            "_genre": self.genre_id,
            "_generated_from": "story_expander_v3",
            "_last_updated": datetime.now().strftime("%Y-%m-%d"),
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": meta_info,
                    "CoreIdentity": protagonist.get("core", {}),
                    "CommercialCode": commercial,
                },
                "protagonist_config": protagonist.get("config", {}),
                self.genre.HUD_TYPE: hud,
                "WorldState": world_state,
                "AssetLibrary": {
                    "KeyNPCs": npcs,
                    "KeyItems": [],
                    "KeyLocations": [],
                    "Persona": protagonist.get("persona", ""),
                    "SpeechStyle": protagonist.get("speech", {}),
                },
                "Seeds": seeds,
                "HistoricalEvents": {"events": events[:20]},
                "GenreRules": rules,
                "RomanceRules": self.genre.get_romance_rules(),
            },
        }

        return self.bible

    def _generate_meta_info(self) -> dict:
        """메타 정보"""
        if SPINNER_AVAILABLE:
            print_info("메타 정보 설정...")
        else:
            print("\n  [*] 메타 정보...")

        titles = self.extracted.get("title_suggestions", ["무제"])
        print("\n  제목 후보:")
        for i, t in enumerate(titles, 1):
            print(f"    [{i}] {t}")
        print("    [0] 직접 입력")

        choice = input("  선택: ").strip()
        if choice == "0":
            title = input("  제목: ").strip()
        elif choice.isdigit() and 1 <= int(choice) <= len(titles):
            title = titles[int(choice) - 1]
        else:
            title = titles[0]

        proto = self.extracted.get("protagonist", {})

        return {
            "title": title,
            "grand_objective": proto.get("main_goal", ""),
            "genre_archetype": f"{self.genre_id} + {self.extracted.get('tone', '')}",
            "logline": f"{proto.get('background', '주인공')} - {proto.get('main_goal', '')}",
            "total_episodes": 200,
            "episodes_per_arc": 5,
        }

    def _generate_protagonist_detail(self) -> dict:
        """주인공 상세"""
        if SPINNER_AVAILABLE:
            print_info("주인공 상세 생성...")
        else:
            print("\n  [*] 주인공 상세...")

        proto = self.extracted.get("protagonist", {})
        romance_rules = self.genre.get_romance_rules()

        prompt = f"""주인공 상세 설정을 생성하세요.

## 기본 정보
{json.dumps(proto, ensure_ascii=False, indent=2)}

## 장르: {self.genre.GENRE_NAME}

## 로맨스 규칙
주인공은 여성에게 호감을 표현하지 않음: {romance_rules.get("protagonist", {}).get("shows_interest", False)}

## 출력 (JSON)
```json
{{
  "name": "이름",
  "age": 나이,
  "core": {{
    "protagonist": "이름",
    "protagonist_faction": "소속",
    "edge": "강점",
    "desire": "욕망",
    "crisis": "초기 위기"
  }},
  "config": {{
    "world_origin": "출신",
    "incarnation_type": "회귀자/전생자/일반"
  }},
  "persona": "성격/말투",
  "speech": {{
    "tone": "말투",
    "vocabulary": "어휘"
  }}
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt, spinner_msg="주인공 설정 생성")
        result = self._parse_json(response) or {}

        name = result.get("name", "주인공")
        print(f"\n  주인공 이름: {name}")
        new_name = input("  [Enter] 승인 / 새 이름: ").strip()
        if new_name:
            result["name"] = new_name
            if "core" in result:
                result["core"]["protagonist"] = new_name

        return result

    def _generate_commercial_code(self) -> dict:
        """상업적 코드"""
        if SPINNER_AVAILABLE:
            print_info("상업 코드 분석...")
        else:
            print("\n  [*] 상업적 코드...")

        prompt = f"""웹소설 상업적 코드:

장르: {self.genre.GENRE_NAME}
주인공 강점: {self.extracted.get("protagonist", {}).get("unique_edge", "")}

JSON:
```json
{{"cider_point": "통쾌함 포인트", "success_device": "성공의 증거", "attitude": "주인공 태도"}}
```
"""
        response = self._call_llm(prompt, temperature=0.7, max_tokens=1000, spinner_msg="상업 코드")
        return self._parse_json(response) or {}

    def _generate_initial_hud(self, protagonist: dict) -> dict:
        """초기 HUD"""
        if SPINNER_AVAILABLE:
            print_info("HUD 초기화...")
        else:
            print("\n  [*] HUD 초기화...")

        proto_info = {
            "name": protagonist.get("name", "주인공"),
            "age": protagonist.get("age", 25),
            **self.extracted.get("protagonist", {}),
        }

        timeline = self.extracted.get("timeline", {})
        if "start_era" in timeline:
            proto_info["start_month"] = timeline["start_era"]

        return self.genre.build_initial_hud(proto_info)

    def _generate_npcs(self) -> list:
        """NPC 생성"""
        if SPINNER_AVAILABLE:
            print_info("NPC 생성...")
        else:
            print("\n  [*] NPC 생성...")

        npc_roles = self.genre.get_npc_roles()
        real_figures = self.genre.get_real_figures()
        romance_rules = self.genre.get_romance_rules()

        # 실존 인물 풀
        figure_pool = []
        for category, figures in real_figures.items():
            figure_pool.extend(figures[:5])

        prompt = f"""웹소설 NPC를 12명 생성하세요.

## 장르: {self.genre.GENRE_NAME}

## 주인공
- 배경: {self.extracted.get("protagonist", {}).get("background", "")}
- 목표: {self.extracted.get("protagonist", {}).get("main_goal", "")}

## 필수 역할
{json.dumps(npc_roles, ensure_ascii=False)}

## 실존 인물 모티브 후보 (최소 4명 사용)
{json.dumps(figure_pool, ensure_ascii=False)}

## 로맨스 규칙
- 주인공은 여성에게 호감 표현 안 함
- 여성 NPC는 주인공에게 호감 가능
- 히로인 아키타입: {json.dumps(romance_rules.get("female_npcs", {}).get("archetypes", []), ensure_ascii=False)}

## 출력 (JSON)
```json
[
  {{
    "name": "이름",
    "role": "역할",
    "desc": "설명 (100자)",
    "real_motif": "실존 모티브" 또는 null,
    "gender": "남/여",
    "romantic_interest_in_protagonist": true/false,
    "protagonist_interest_in_them": false,
    "appearance_timing": "초반/중반/후반"
  }}
]
```

12명 모두 출력. JSON만 출력.
"""
        response = self._call_llm(prompt, max_tokens=12000, spinner_msg="NPC 생성")
        npcs = self._parse_json(response) or []

        # 로맨스 규칙 강제
        for npc in npcs:
            npc["protagonist_interest_in_them"] = False

        # 통계
        real_count = sum(1 for n in npcs if n.get("real_motif"))
        if SPINNER_AVAILABLE:
            print_success(f"생성된 NPC: {len(npcs)}명 (실존 모티브: {real_count}명)")
        else:
            print(f"\n  생성된 NPC: {len(npcs)}명 (실존 모티브: {real_count}명)")

        # NPC 테이블 표시
        if SPINNER_AVAILABLE and npcs:
            headers = ["#", "이름", "역할", "모티브", "호감"]
            rows = []
            for i, npc in enumerate(npcs[:8], 1):
                motif = npc.get("real_motif", "-") or "-"
                interest = "O" if npc.get("romantic_interest_in_protagonist") else "-"
                rows.append([str(i), npc["name"], npc["role"], motif, interest])
            print()
            print_table(headers, rows)
            if len(npcs) > 8:
                print(f"    ... 외 {len(npcs) - 8}명")
        else:
            for i, npc in enumerate(npcs[:8], 1):
                motif = f" [{npc.get('real_motif')}]" if npc.get("real_motif") else ""
                interest = " <3" if npc.get("romantic_interest_in_protagonist") else ""
                print(f"    [{i}] {npc['name']} ({npc['role']}){motif}{interest}")
            if len(npcs) > 8:
                print(f"    ... 외 {len(npcs) - 8}명")

        # 사용된 인물 기록
        for npc in npcs:
            if npc.get("real_motif"):
                self.used_figures.append(npc["real_motif"])

        return npcs

    def _generate_world_state(self) -> dict:
        """세계 상태"""
        timeline = self.extracted.get("timeline", {})
        return {"CurrentEra": timeline.get("start_era", ""), "CurrentLocation": "시작 위치", "KarmaMatrix": {}}

    def _generate_seeds(self, npcs: list) -> list:
        """복선 씨앗"""
        if SPINNER_AVAILABLE:
            print_info("복선 씨앗 생성...")
        else:
            print("\n  [*] 복선 씨앗...")

        prompt = f"""복선 씨앗 6개:

컨셉: {self.concept[:300]}
NPC: {[n["name"] for n in npcs[:8]]}

JSON: [{{"id": "S-001", "category": "인물|사건", "description": "복선", "planted_ep": 1, "target_harvest_ep": 30}}]
"""
        response = self._call_llm(prompt, max_tokens=2000, spinner_msg="복선 씨앗")
        return self._parse_json(response) or []

    # ===========================================
    # Phase 2: Treatment 생성
    # ===========================================

    def phase2_generate_treatment(self) -> list:
        """Treatment 생성"""
        if SPINNER_AVAILABLE:
            print_header("Phase 2: Treatment 생성 (60 블록)", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 2: Treatment 생성 (60 블록)")
            print("=" * 60)

        skeleton = self._generate_treatment_skeleton()
        detailed = self._generate_treatment_details(skeleton)
        self.treatment = self._extract_treatment_metadata(detailed)

        if SPINNER_AVAILABLE:
            print_success(f"Treatment 생성 완료: {len(self.treatment)}개 블록")

        return self.treatment

    def _generate_treatment_skeleton(self) -> list:
        """뼈대 생성"""
        if SPINNER_AVAILABLE:
            print_info("60블록 스켈레톤 생성...")
        else:
            print("\n  [*] 60블록 뼈대...")

        # Arc별 어드바이저 추천
        arc_recs = []
        if hasattr(self.advisor, "get_arc_recommendations"):
            arc_recs = self.advisor.get_arc_recommendations(10)
        else:
            for arc in range(1, 11):
                block_num = (arc - 1) * 6 + 1
                advice = self.advisor.generate_block_advice(block_num)
                arc_recs.append(
                    {"arc": arc, "blocks": f"{block_num}-{block_num + 5}", "advice": advice.get("overall_tip", "")}
                )

        events = self.bible.get("MasterBible", {}).get("HistoricalEvents", {}).get("events", [])[:10]
        npcs = self.bible.get("MasterBible", {}).get("AssetLibrary", {}).get("KeyNPCs", [])[:8]
        power = self.genre.get_power_progression_template()

        prompt = f"""60개 블록 뼈대를 생성하세요.

## 장르: {self.genre.GENRE_NAME}
## 컨셉
{self.concept}

## Arc별 어드바이저 추천
{json.dumps(arc_recs, ensure_ascii=False, indent=2)}

## 성장 곡선
{json.dumps(power, ensure_ascii=False)}

## 주요 NPC
{json.dumps([n["name"] + " (" + n["role"] + ")" for n in npcs], ensure_ascii=False)}

## 활용 가능한 이벤트
{json.dumps([e.get("event", "") for e in events], ensure_ascii=False)}

## 출력 (JSON)
```json
[
  {{"block_id": "Block 1", "title": "제목", "summary": "요약", "arc": 1}},
  ...
]
```

60개 블록 모두 출력. JSON만.
"""
        response = self._call_llm(prompt, max_tokens=20000, temperature=0.9, spinner_msg="60블록 스켈레톤")
        skeleton = self._parse_json(response) or []

        if SPINNER_AVAILABLE:
            print_success(f"스켈레톤: {len(skeleton)}개 블록")
        else:
            print(f"\n  생성: {len(skeleton)}개 블록")

        return skeleton

    def _generate_treatment_details(self, skeleton: list) -> list:
        """상세 생성"""
        if SPINNER_AVAILABLE:
            print_info("상세 콘텐츠 생성...")
        else:
            print("\n  [*] 상세 content...")

        detailed = []
        batch_size = 5
        total_batches = (len(skeleton) + batch_size - 1) // batch_size

        # 프로그레스 바 초기화
        if SPINNER_AVAILABLE:
            progress = ProgressBar(total_batches, "블록 상세 생성")

        for batch_idx in range(0, len(skeleton), batch_size):
            batch = skeleton[batch_idx : batch_idx + batch_size]
            start_block = batch_idx + 1

            if SPINNER_AVAILABLE:
                progress.update(message=f"Block {start_block}-{start_block + len(batch) - 1}")
            else:
                print(f"    Batch: Block {start_block}-{start_block + len(batch) - 1}")

            prev_summary = ""
            if detailed:
                prev_summary = "\n".join(
                    [f"- {b['block_id']}: {b.get('content', {}).get('reward', '')[:30]}" for b in detailed[-3:]]
                )

            skeleton_text = "\n".join([f"- {b['block_id']}: {b['title']} - {b['summary']}" for b in batch])

            romance_rules = self.genre.get_romance_rules()
            romance_reminder = f"""
## 로맨스 규칙
- 주인공 호감 표현: {romance_rules.get("protagonist", {}).get("shows_interest", False)}
- 여성 NPC → 주인공 호감: 가능
"""

            prompt = f"""블록 상세:

## 장르: {self.genre.GENRE_NAME}

## 이전 블록
{prev_summary if prev_summary else "(첫 배치)"}

## 이번 블록
{skeleton_text}

{romance_reminder}

## 출력 (JSON)
```json
[
  {{
    "block_id": "Block {start_block}",
    "title": "제목",
    "content": {{
      "context": "배경 (200자)",
      "event_villain": "장애물 (200자)",
      "solution": "해결 (200자)",
      "reward": "결과 (100자)"
    }}
  }}
]
```

JSON만.
"""
            response = self._call_llm(
                prompt, temperature=0.85, spinner_msg=f"Block {start_block}-{start_block + len(batch) - 1} 생성"
            )
            batch_result = self._parse_json(response) or []

            if batch_result:
                detailed.extend(batch_result)
            else:
                for b in batch:
                    detailed.append(
                        {
                            "block_id": b["block_id"],
                            "title": b["title"],
                            "content": {"context": b["summary"], "event_villain": "", "solution": "", "reward": ""},
                        }
                    )

        if SPINNER_AVAILABLE:
            progress.finish(f"상세 생성 완료: {len(detailed)}개 블록")

        return detailed

    def _extract_treatment_metadata(self, blocks: list) -> list:
        """메타데이터 추출"""
        if SPINNER_AVAILABLE:
            print_info("메타데이터 추출...")
        else:
            print("\n  [*] 메타데이터...")

        genre_ext_schema = self.genre.get_genre_ext_schema() if hasattr(self.genre, "get_genre_ext_schema") else {}

        enriched = []

        # 프로그레스 바 초기화
        if SPINNER_AVAILABLE:
            progress = ProgressBar(len(blocks), "메타데이터 추출")

        for i, block in enumerate(blocks):
            if SPINNER_AVAILABLE:
                progress.update(message=f"Block {i + 1}/{len(blocks)}")
            elif i % 15 == 0:
                print(f"    {i + 1}/{len(blocks)}")

            content = block.get("content", {})

            prompt = f"""메타데이터 추출:

Block: {block["block_id"]}
Content: {json.dumps(content, ensure_ascii=False)[:400]}

장르별 확장 필드:
{json.dumps(genre_ext_schema, ensure_ascii=False)}

JSON:
```json
{{"stakes": "위험", "tension_level": 7, "genre_ext": {{...}}}}
```
"""
            response = self._call_llm(
                prompt, temperature=0.3, max_tokens=1000, spinner_msg=f"메타 {i + 1}/{len(blocks)}"
            )
            metadata = self._parse_json(response) or {}

            enriched.append(
                {"block_id": block["block_id"], "title": block["title"], "content": block["content"], **metadata}
            )

        if SPINNER_AVAILABLE:
            progress.finish(f"메타데이터 추출 완료: {len(enriched)}개")

        return enriched

    # ===========================================
    # Phase 3: 저장
    # ===========================================

    def phase3_save(self):
        """저장"""
        if SPINNER_AVAILABLE:
            print_header("Phase 3: 저장", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 3: 저장")
            print("=" * 60)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Bible
        bible_path = self.output_dir / "bible.json"
        with open(bible_path, "w", encoding="utf-8") as f:
            json.dump(self.bible, f, ensure_ascii=False, indent=2)
        if SPINNER_AVAILABLE:
            print_success(f"Bible: {bible_path}")
        else:
            print(f"\n  [v] Bible: {bible_path}")

        # Treatment
        treatment_output = {
            "_schema_version": "2.0",
            "_genre": self.genre_id,
            "_bible_ref": "bible.json",
            "work_name": self.bible.get("MasterBible", {}).get("ProjectData", {}).get("MetaInfo", {}).get("title", ""),
            "total_blocks": len(self.treatment),
            "treatments": self.treatment,
        }

        treatment_path = self.output_dir / "treatment.json"
        with open(treatment_path, "w", encoding="utf-8") as f:
            json.dump(treatment_output, f, ensure_ascii=False, indent=2)
        if SPINNER_AVAILABLE:
            print_success(f"Treatment: {treatment_path}")
        else:
            print(f"  [v] Treatment: {treatment_path}")

        # Summary
        summary = {
            "title": self.bible.get("MasterBible", {}).get("ProjectData", {}).get("MetaInfo", {}).get("title", ""),
            "genre": self.genre_id,
            "concept": self.concept[:500],
            "npc_count": len(self.bible.get("MasterBible", {}).get("AssetLibrary", {}).get("KeyNPCs", [])),
            "real_figures_used": self.used_figures,
            "block_count": len(self.treatment),
            "generated_at": datetime.now().isoformat(),
        }

        summary_path = self.output_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        if SPINNER_AVAILABLE:
            print_success(f"Summary: {summary_path}")
        else:
            print(f"  [v] Summary: {summary_path}")

    # ===========================================
    # 메인 실행
    # ===========================================

    def run(self):
        """전체 파이프라인"""
        if SPINNER_AVAILABLE:
            print_header("Story Expander v3 - 다중 장르 지원", style="star")
        else:
            print("\n" + "=" * 60)
            print("[*] Story Expander v3 - 다중 장르 지원")
            print("=" * 60)

        # Phase 0
        self.phase0_select_genre()
        self.phase0_input_concept()
        self.phase0_analyze_concept()

        # Phase 1
        self.phase1_generate_bible()

        # Phase 2
        self.phase2_generate_treatment()

        # Phase 3
        self.phase3_save()

        if SPINNER_AVAILABLE:
            print_header("완료!", style="star")
            print_success(f"출력 폴더: {self.output_dir}")
            print_info("  - bible.json")
            print_info("  - treatment.json")
            print_info("  - summary.json")
        else:
            print("\n" + "=" * 60)
            print("[v] 완료!")
            print("=" * 60)
            print(f"\n출력: {self.output_dir}")
            print("  - bible.json")
            print("  - treatment.json")
            print("  - summary.json")


class ReverseExpander:
    """역설계 - 기존 원고 → Bible + Treatment 추출"""

    def __init__(self, input_file: str, output_dir: str, genre_id: str = None):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.genre_id = genre_id
        self.genre = None
        self.advisor = None
        self.raw_text = ""
        self.episodes = []
        self.bible = {}
        self.treatment = []

        # Gemini 클라이언트
        if GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                self.model = "gemini-2.5-flash"
            else:
                self.client = None
        else:
            self.client = None

    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 8192, spinner_msg: str = None) -> str:
        """LLM 호출"""
        if not self.client:
            return None

        spinner = None
        if SPINNER_AVAILABLE and spinner_msg:
            spinner = Spinner(spinner_msg, style="braille")
            spinner.start()

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            if spinner:
                spinner.stop(f"{spinner_msg} 완료")
            return response.text
        except Exception as e:
            if spinner:
                spinner.stop()
            if SPINNER_AVAILABLE:
                print_error(f"LLM 오류: {e}")
            else:
                print(f"[X] LLM 오류: {e}")
            return None

    def _parse_json(self, text: str) -> Any:
        """JSON 파싱"""
        if not text:
            return None
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except:
            return None

    # ===========================================
    # Phase 0: 파일 로드 및 에피소드 분리
    # ===========================================

    def phase0_load_and_parse(self):
        """원고 로드 및 에피소드 분리"""
        if SPINNER_AVAILABLE:
            print_header("Phase 0: 원고 로드", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 0: 원고 로드")
            print("=" * 60)

        # 파일 읽기
        with open(self.input_file, encoding="utf-8") as f:
            self.raw_text = f.read()

        if SPINNER_AVAILABLE:
            print_success(f"파일 로드: {self.input_file.name} ({len(self.raw_text):,}자)")
        else:
            print(f"[v] 파일 로드: {self.input_file.name} ({len(self.raw_text):,}자)")

        # 에피소드 분리 (ⓚ 제N화 패턴)
        import re

        episode_pattern = r"ⓚ\s*제(\d+)화[.\s]*([^\n]*)"
        matches = list(re.finditer(episode_pattern, self.raw_text))

        for i, match in enumerate(matches):
            ep_num = int(match.group(1))
            ep_title = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(self.raw_text)
            ep_content = self.raw_text[start_pos:end_pos].strip()

            self.episodes.append(
                {"ep_num": ep_num, "title": ep_title, "content": ep_content, "char_count": len(ep_content)}
            )

        if SPINNER_AVAILABLE:
            print_success(f"에피소드 분리: {len(self.episodes)}개")
            if self.episodes:
                print_table(
                    ["#", "제목", "글자수"],
                    [[str(ep["ep_num"]), ep["title"][:20], f"{ep['char_count']:,}"] for ep in self.episodes[:5]],
                )
                if len(self.episodes) > 5:
                    print(f"    ... 외 {len(self.episodes) - 5}개")
        else:
            print(f"[v] 에피소드 분리: {len(self.episodes)}개")
            for ep in self.episodes[:5]:
                print(f"    [{ep['ep_num']}] {ep['title']} ({ep['char_count']:,}자)")

    def phase0_select_genre(self) -> str:
        """장르 선택 (자동 감지 지원)"""
        if self.genre_id:
            self.genre = get_genre(self.genre_id)
            return self.genre_id

        if SPINNER_AVAILABLE:
            print_header("장르 선택", style="simple")
        else:
            print("\n[*] 장르 선택")

        genres = list_genres()
        genre_list = list(genres.keys())

        print("\n사용 가능한 장르:")
        print("  [0] 자동 감지 (AI가 원고 분석)")
        for i, (gid, info) in enumerate(genres.items(), 1):
            print(f"  [{i}] {info['name']} ({gid})")

        choice = input("\n선택: ").strip()

        if choice == "0":
            # 자동 감지
            selected = self._auto_detect_genre()
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(genre_list):
                selected = genre_list[idx]
            else:
                selected = "investment"
        elif choice in genres:
            selected = choice
        else:
            selected = "investment"

        self.genre_id = selected
        self.genre = get_genre(selected)

        if SPINNER_AVAILABLE:
            print_success(f"선택: {self.genre.GENRE_NAME}")

        # 어드바이저 초기화
        self.advisor = self.genre.get_advisor("")

        return selected

    def _auto_detect_genre(self) -> str:
        """원고에서 장르 자동 감지"""
        sample = self.raw_text[:5000]

        prompt = f"""다음 원고의 장르를 판별하세요.

## 원고 샘플
{sample}

## 가능한 장르
- investment: 투자물, 재벌물, 금융 회귀물
- wuxia: 무협, 강호, 무림
- hunter: 헌터물, 던전물, 각성물, 게이트물

## 출력 (JSON)
```json
{{"genre": "investment 또는 wuxia 또는 hunter", "confidence": 0.0-1.0, "reason": "판단 근거"}}
```
JSON만 출력.
"""
        response = self._call_llm(prompt, temperature=0.3, spinner_msg="장르 자동 감지")
        result = self._parse_json(response) or {}

        detected = result.get("genre", "investment")
        confidence = result.get("confidence", 0)
        reason = result.get("reason", "")

        if SPINNER_AVAILABLE:
            print_success(f"감지된 장르: {detected} (신뢰도: {confidence:.0%})")
            print_info(f"근거: {reason[:50]}...")
        else:
            print(f"[v] 감지: {detected} ({confidence:.0%})")

        return detected

    # ===========================================
    # Phase 1: Bible 역추출
    # ===========================================

    def phase1_extract_bible(self):
        """원고에서 Bible 역추출"""
        if SPINNER_AVAILABLE:
            print_header("Phase 1: Bible 역추출", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 1: Bible 역추출")
            print("=" * 60)

        # 샘플 에피소드 (처음 3개)
        sample_text = "\n\n---\n\n".join(
            [f"[{ep['ep_num']}화: {ep['title']}]\n{ep['content'][:3000]}" for ep in self.episodes[:3]]
        )

        # 1. 기본 정보 추출
        meta_info = self._extract_meta_info(sample_text)

        # 2. 주인공 정보 추출
        protagonist = self._extract_protagonist(sample_text)

        # 3. NPC 추출
        npcs = self._extract_npcs(sample_text)

        # 4. 세계관/타임라인 추출
        world_state = self._extract_world_state(sample_text)

        # 5. 초기 HUD 생성 (장르별 프로필 반영)
        hud_input = {"name": protagonist.get("name", "주인공"), "age": protagonist.get("age", 25), **protagonist}

        # 장르별 프로필 병합
        if self.genre_id == "investment" and "finance_profile" in protagonist:
            hud_input.update(protagonist["finance_profile"])
        elif self.genre_id == "wuxia" and "martial_profile" in protagonist:
            hud_input.update(protagonist["martial_profile"])
        elif self.genre_id == "hunter" and "hunter_profile" in protagonist:
            hud_input.update(protagonist["hunter_profile"])

        # 세계 상태에서 시작 시점 추출
        if world_state.get("CurrentEra"):
            hud_input["start_month"] = world_state["CurrentEra"]

        hud = self.genre.build_initial_hud(hud_input)

        # Bible 조립
        self.bible = {
            "_schema_version": "2.0",
            "_genre": self.genre_id,
            "_generated_from": "reverse_expander",
            "_source_file": str(self.input_file.name),
            "_last_updated": datetime.now().strftime("%Y-%m-%d"),
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": meta_info,
                    "CoreIdentity": protagonist.get("core", {}),
                    "CommercialCode": protagonist.get("commercial", {}),
                },
                "protagonist_config": protagonist.get("config", {}),
                self.genre.HUD_TYPE: hud,
                "WorldState": world_state,
                "AssetLibrary": {
                    "KeyNPCs": npcs,
                    "KeyItems": [],
                    "KeyLocations": [],
                    "Persona": protagonist.get("persona", ""),
                    "SpeechStyle": protagonist.get("speech", {}),
                },
                "GenreRules": self.genre.get_genre_rules(),
                "RomanceRules": self.genre.get_romance_rules(),
            },
        }

        if SPINNER_AVAILABLE:
            print_success("Bible 역추출 완료")

        return self.bible

    def _extract_meta_info(self, sample_text: str) -> dict:
        """메타 정보 추출"""
        prompt = f"""다음 원고에서 작품 메타 정보를 추출하세요.

## 원고 샘플
{sample_text[:5000]}

## 출력 (JSON)
```json
{{
  "title": "작품 제목",
  "grand_objective": "주인공의 최종 목표",
  "genre_archetype": "장르 + 서브장르",
  "logline": "한 줄 요약",
  "tone": "작품 톤 (복수/성장/코미디 등)",
  "themes": ["테마1", "테마2"]
}}
```
JSON만 출력.
"""
        response = self._call_llm(prompt, spinner_msg="메타 정보 추출")
        return self._parse_json(response) or {}

    def _extract_protagonist(self, sample_text: str) -> dict:
        """주인공 정보 추출 (장르별 필드 포함)"""

        # 장르별 주인공 필드 예시
        genre_specific = self._get_protagonist_genre_fields()

        prompt = f"""다음 원고에서 주인공 정보를 추출하세요.

## 장르: {self.genre.GENRE_NAME}

## 원고 샘플
{sample_text[:5000]}

## 출력 (JSON)
```json
{{
  "name": "이름",
  "age": 나이,
  "core": {{
    "protagonist": "이름",
    "protagonist_faction": "소속",
    "edge": "강점/치트키",
    "desire": "욕망",
    "crisis": "초기 위기"
  }},
  "config": {{
    "world_origin": "출신",
    "incarnation_type": "회귀자/전생자/일반"
  }},
  "persona": "성격",
  "speech": {{"tone": "말투", "vocabulary": "어휘 수준"}},
  "commercial": {{
    "cider_point": "통쾌함 포인트",
    "success_device": "성공 증명 방식",
    "attitude": "태도"
  }},
  {genre_specific}
}}
```
JSON만 출력.
"""
        response = self._call_llm(prompt, spinner_msg="주인공 추출")
        return self._parse_json(response) or {}

    def _get_protagonist_genre_fields(self) -> str:
        """장르별 주인공 추가 필드"""
        if self.genre_id == "investment":
            return """"finance_profile": {
    "initial_capital": "초기 자본",
    "investment_style": "투자 스타일",
    "future_knowledge": "미래 지식 범위",
    "target_capital": "목표 자본"
  }"""
        elif self.genre_id == "wuxia":
            return """"martial_profile": {
    "initial_rank": "초기 경지 (말류/삼류/이류 등)",
    "martial_arts": ["무공1", "무공2"],
    "internal_energy": "내공 수치",
    "faction": "소속 문파"
  }"""
        elif self.genre_id == "hunter":
            return """"hunter_profile": {
    "initial_rank": "초기 등급 (E/D/C/B/A/S)",
    "level": 1,
    "class": "직업 (검사/마법사/힐러 등)",
    "skills": ["스킬1"],
    "unique_ability": "고유 능력"
  }"""
        else:
            return """"genre_profile": {}"""

    def _extract_npcs(self, sample_text: str) -> list:
        """NPC 추출"""
        romance_rules = self.genre.get_romance_rules()

        prompt = f"""다음 원고에서 등장인물(NPC)을 추출하세요.

## 원고 샘플
{sample_text[:6000]}

## 로맨스 규칙
- 주인공은 여성에게 호감 표현 안 함
- 여성 NPC는 주인공에게 호감 가능

## 출력 (JSON)
```json
[
  {{
    "name": "이름",
    "role": "역할 (멘토/빌런/히로인/조력자 등)",
    "desc": "설명 (100자)",
    "gender": "남/여",
    "relationship_to_protagonist": "관계",
    "romantic_interest_in_protagonist": true/false,
    "protagonist_interest_in_them": false,
    "real_motif": "실존 모티브 또는 null"
  }}
]
```
등장하는 모든 인물 추출. JSON만 출력.
"""
        response = self._call_llm(prompt, max_tokens=12000, spinner_msg="NPC 추출")
        npcs = self._parse_json(response) or []

        # 로맨스 규칙 강제
        for npc in npcs:
            npc["protagonist_interest_in_them"] = False

        if SPINNER_AVAILABLE:
            print_success(f"NPC 추출: {len(npcs)}명")
        else:
            print(f"[v] NPC: {len(npcs)}명")

        return npcs

    def _extract_world_state(self, sample_text: str) -> dict:
        """세계 상태 추출"""
        prompt = f"""다음 원고에서 세계관/배경 정보를 추출하세요.

## 원고 샘플
{sample_text[:4000]}

## 출력 (JSON)
```json
{{
  "CurrentEra": "시대 배경 (예: 1996년)",
  "CurrentLocation": "주요 장소",
  "WorldSetting": "세계관 설명",
  "KeyOrganizations": ["조직1", "조직2"],
  "EconomicContext": "경제적 배경"
}}
```
JSON만 출력.
"""
        response = self._call_llm(prompt, spinner_msg="세계관 추출")
        return self._parse_json(response) or {}

    # ===========================================
    # Phase 2: Treatment 역추출
    # ===========================================

    def phase2_extract_treatment(self):
        """에피소드별 Treatment 역추출"""
        if SPINNER_AVAILABLE:
            print_header("Phase 2: Treatment 역추출", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 2: Treatment 역추출")
            print("=" * 60)

        if SPINNER_AVAILABLE:
            progress = ProgressBar(len(self.episodes), "Treatment 추출")

        for i, ep in enumerate(self.episodes):
            if SPINNER_AVAILABLE:
                progress.update(message=f"에피소드 {ep['ep_num']}")

            block = self._extract_episode_block(ep)
            self.treatment.append(block)

        if SPINNER_AVAILABLE:
            progress.finish(f"Treatment 추출 완료: {len(self.treatment)}개 블록")

        return self.treatment

    def _extract_episode_block(self, episode: dict) -> dict:
        """단일 에피소드 → 블록 변환 (장르별 스키마 적용)"""

        # 장르별 확장 스키마
        genre_ext_schema = {}
        if hasattr(self.genre, "get_genre_ext_schema"):
            genre_ext_schema = self.genre.get_genre_ext_schema()

        # 장르별 추가 필드 예시
        genre_ext_example = self._get_genre_ext_example()

        prompt = f"""다음 에피소드를 Treatment 블록 형식으로 변환하세요.

## 장르: {self.genre.GENRE_NAME}

## 에피소드 {episode["ep_num"]}화: {episode["title"]}
{episode["content"][:4000]}

## 장르별 확장 필드 (genre_ext)
{json.dumps(genre_ext_schema, ensure_ascii=False, indent=2)}

## 출력 (JSON)
```json
{{
  "block_id": "Block {episode["ep_num"]}",
  "title": "{episode["title"]}",
  "content": {{
    "context": "배경/상황 (200자)",
    "event_villain": "갈등/장애물 (200자)",
    "solution": "해결 방식 (200자)",
    "reward": "결과/보상 (100자)"
  }},
  "stakes": "위험 요소",
  "tension_level": 1-10,
  "key_scenes": ["씬1", "씬2", "씬3"],
  "genre_ext": {genre_ext_example}
}}
```
JSON만 출력.
"""
        response = self._call_llm(prompt, temperature=0.5, spinner_msg=f"Block {episode['ep_num']}")
        block = self._parse_json(response) or {}

        if not block:
            block = {
                "block_id": f"Block {episode['ep_num']}",
                "title": episode["title"],
                "content": {"context": episode["content"][:200], "event_villain": "", "solution": "", "reward": ""},
                "genre_ext": {},
            }

        return block

    def _get_genre_ext_example(self) -> str:
        """장르별 확장 필드 예시 반환"""
        if self.genre_id == "investment":
            return """{
    "capital_before": "이전 자본",
    "capital_after": "이후 자본",
    "investment_type": "투자 유형 (주식/부동산/사업 등)",
    "returns": "수익률",
    "key_deal": "핵심 거래"
  }"""
        elif self.genre_id == "wuxia":
            return """{
    "internal_energy_before": "이전 내공",
    "internal_energy_after": "이후 내공",
    "martial_arts_gained": "획득 무공",
    "rank_change": "경지 변화 (말류→삼류 등)",
    "battle_outcome": "승/패/무"
  }"""
        elif self.genre_id == "hunter":
            return """{
    "level_before": "이전 레벨",
    "level_after": "이후 레벨",
    "exp_gained": "획득 경험치",
    "skills_gained": "획득 스킬",
    "items_gained": "획득 아이템",
    "dungeon_cleared": "클리어 던전"
  }"""
        else:
            return "{}"

    # ===========================================
    # Phase 3: 저장
    # ===========================================

    def phase3_save(self):
        """저장"""
        if SPINNER_AVAILABLE:
            print_header("Phase 3: 저장", style="double")
        else:
            print("\n" + "=" * 60)
            print("[*] Phase 3: 저장")
            print("=" * 60)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Bible
        bible_path = self.output_dir / "bible.json"
        with open(bible_path, "w", encoding="utf-8") as f:
            json.dump(self.bible, f, ensure_ascii=False, indent=2)
        if SPINNER_AVAILABLE:
            print_success(f"Bible: {bible_path}")
        else:
            print(f"[v] Bible: {bible_path}")

        # Treatment
        treatment_output = {
            "_schema_version": "2.0",
            "_genre": self.genre_id,
            "_source_file": str(self.input_file.name),
            "total_blocks": len(self.treatment),
            "treatments": self.treatment,
        }

        treatment_path = self.output_dir / "treatment.json"
        with open(treatment_path, "w", encoding="utf-8") as f:
            json.dump(treatment_output, f, ensure_ascii=False, indent=2)
        if SPINNER_AVAILABLE:
            print_success(f"Treatment: {treatment_path}")
        else:
            print(f"[v] Treatment: {treatment_path}")

    # ===========================================
    # 메인 실행
    # ===========================================

    def run(self):
        """역설계 파이프라인"""
        if SPINNER_AVAILABLE:
            print_header("Story Expander v3 - 역설계 모드", style="star")
        else:
            print("\n" + "=" * 60)
            print("[*] Story Expander v3 - 역설계 모드")
            print("=" * 60)

        # Phase 0
        self.phase0_load_and_parse()
        self.phase0_select_genre()

        # Phase 1
        self.phase1_extract_bible()

        # Phase 2
        self.phase2_extract_treatment()

        # Phase 3
        self.phase3_save()

        if SPINNER_AVAILABLE:
            print_header("역설계 완료!", style="star")
            print_success(f"출력 폴더: {self.output_dir}")
        else:
            print("\n[v] 역설계 완료!")
            print(f"출력: {self.output_dir}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Story Expander v3")
    parser.add_argument("--output-dir", default="outputs/new_project")
    parser.add_argument("--genre", default=None, help="장르 ID (생략 시 선택 메뉴)")
    parser.add_argument("--reverse", default=None, help="역설계 모드: 원고 파일 경로")

    args = parser.parse_args()

    if args.reverse:
        # 역설계 모드
        expander = ReverseExpander(input_file=args.reverse, output_dir=args.output_dir, genre_id=args.genre)
    else:
        # 일반 모드
        expander = StoryExpander(output_dir=args.output_dir, genre_id=args.genre)

    expander.run()


if __name__ == "__main__":
    main()
