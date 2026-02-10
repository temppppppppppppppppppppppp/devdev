"""
[V60.97] Bible Extractor - 원고 역설계 에이전트

기존 원고에서 Bible(설정집)을 역추출하는 에이전트.
신작이 아닌 기존작 계속 집필 시 사용.

사용법:
    extractor = BibleExtractor(context, client)
    bible = extractor.extract_from_manuscript(manuscript_text, genre="investment")
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from .base_agent import BaseAgent


class BibleExtractor(BaseAgent):
    """
    [V60.97] 원고에서 Bible 역추출 에이전트

    원고 텍스트를 분석하여 MasterBible JSON 구조를 생성합니다.
    """

    def __init__(self, context, client, model_tier: str = "gemini-2.5-pro"):
        super().__init__(context, client, model_tier)

        # 장르별 HUD 타입
        self.genre_hud_map = {
            "wuxia": "MartialHUD",
            "hunter": "HunterHUD",
            "investment": "FinanceHUD"
        }

        # 추출 통계
        self.stats = {
            "chunks_processed": 0,
            "npcs_found": 0,
            "items_found": 0,
            "seeds_found": 0
        }

    def _parse_response(self, response: str) -> Any:
        """LLM 응답 파싱 (문자열 → dict/list)"""
        if not response:
            return None

        # 이미 dict/list면 그대로 반환
        if isinstance(response, (dict, list)):
            return response

        # 문자열이면 JSON 파싱 시도
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # JSON 블록 추출 시도
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except (json.JSONDecodeError, ValueError):  # [V64.P4] JSON parse fallback
                    pass

            # { 또는 [ 로 시작하는 부분 추출
            start_idx = -1
            for i, c in enumerate(response):
                if c in '{[':
                    start_idx = i
                    break

            if start_idx >= 0:
                try:
                    return json.loads(response[start_idx:])
                except (json.JSONDecodeError, ValueError):  # [V64.P4] JSON parse fallback
                    pass

            print(f"      [WARN] JSON 파싱 실패, 응답 일부: {response[:200]}...")
            return None

    def extract_from_manuscript(
        self,
        manuscript: str,
        genre: str = "wuxia",
        episode_delimiter: str = None,
        extract_mode: str = "starting_point"  # "starting_point" | "current_state"
    ) -> Dict[str, Any]:
        """
        원고에서 Bible 추출

        Args:
            manuscript: 원고 텍스트 (여러 화 포함 가능)
            genre: 장르 ("wuxia", "hunter", "investment")
            episode_delimiter: 에피소드 구분자 (None이면 자동 감지)
            extract_mode: 추출 모드
                - "starting_point": 1화 시작 시점 상태 추출 (Bible 용도)
                - "current_state": 현재 시점 상태 추출 (WorldState 업데이트 용도)

        Returns:
            MasterBible 구조의 딕셔너리
        """
        print(f"\n[BibleExtractor] 역설계 시작 (장르: {genre}, 모드: {extract_mode})")
        print(f"   원고 길이: {len(manuscript):,}자")

        # 1. 에피소드 분리
        episodes = self._split_episodes(manuscript, episode_delimiter)
        print(f"   감지된 에피소드: {len(episodes)}개")

        if not episodes:
            print("   [ERROR] 에피소드 분리 실패")
            return self._create_empty_bible(genre)

        # 2. 1차 추출: 기본 정보 (제목, 장르, 주인공 등)
        print(f"\n   [Phase 1] 기본 정보 추출 중...")
        basic_info = self._extract_basic_info(episodes[0], genre)

        # 3. 2차 추출: NPC 목록
        print(f"   [Phase 2] NPC 추출 중...")
        npcs = self._extract_npcs(episodes, genre)
        self.stats["npcs_found"] = len(npcs)
        print(f"      발견된 NPC: {len(npcs)}명")

        # 4. 3차 추출: 세계 설정 & 관계
        print(f"   [Phase 3] 세계 설정 추출 중...")
        world_state = self._extract_world_state(episodes, extract_mode)

        # 5. 4차 추출: 아이템 & 복선
        print(f"   [Phase 4] 아이템/복선 추출 중...")
        items, seeds = self._extract_items_and_seeds(episodes)
        self.stats["items_found"] = len(items)
        self.stats["seeds_found"] = len(seeds)
        print(f"      아이템: {len(items)}개, 복선: {len(seeds)}개")

        # 6. 5차 추출: 주인공 상세 HUD
        print(f"   [Phase 5] 주인공 HUD 추출 중...")
        protagonist_hud = self._extract_protagonist_hud(episodes, genre, extract_mode)

        # 7. 6차 추출: 문체 분석
        print(f"   [Phase 6] 문체 분석 중...")
        speech_style = self._extract_speech_style(episodes[0])

        # 8. Bible 조립
        print(f"\n   [Final] Bible 조립 중...")
        bible = self._assemble_bible(
            basic_info=basic_info,
            npcs=npcs,
            world_state=world_state,
            items=items,
            seeds=seeds,
            protagonist_hud=protagonist_hud,
            speech_style=speech_style,
            genre=genre
        )

        print(f"\n[BibleExtractor] 역설계 완료!")
        self._print_stats()

        return bible

    def _split_episodes(self, manuscript: str, delimiter: str = None) -> List[str]:
        """에피소드 분리"""
        if delimiter:
            parts = manuscript.split(delimiter)
            return [p.strip() for p in parts if p.strip()]

        # 자동 감지 패턴들
        patterns = [
            r'(?:^|\n)ⓚ\s*제?\s*(\d+)\s*화',  # ⓚ 제1화 or ⓚ 1화
            r'(?:^|\n)#\s*(\d+)',               # #001, #1
            r'(?:^|\n)제\s*(\d+)\s*화',          # 제1화
            r'(?:^|\n)Episode\s*(\d+)',          # Episode 1
            r'(?:^|\n)ep\.?\s*(\d+)',            # ep.1, ep 1
        ]

        for pattern in patterns:
            matches = list(re.finditer(pattern, manuscript, re.IGNORECASE | re.MULTILINE))
            if len(matches) >= 2:
                episodes = []
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(manuscript)
                    episodes.append(manuscript[start:end].strip())
                return episodes

        # 구분자 못 찾으면 전체를 1개 에피소드로
        return [manuscript]

    def _extract_basic_info(self, first_episode: str, genre: str) -> Dict:
        """기본 정보 추출 (1화 기반)"""
        prompt = f"""다음 소설 1화를 분석하여 기본 정보를 추출하세요.

[원고]
{first_episode[:8000]}

[추출 항목]
1. title: 작품 제목 (없으면 추정)
2. protagonist: 주인공 이름
3. protagonist_faction: 주인공 소속
4. grand_objective: 주인공의 궁극적 목표
5. logline: 한 문단 요약
6. edge: 주인공만의 차별화 포인트
7. desire: 핵심 욕망
8. crisis: 초기 위기 상황
9. cider_point: 독자가 쾌감을 느끼는 순간
10. attitude: 주인공 태도 유형 (능동적 설계자/수동적 반응자/위악자)
11. world_origin: 주인공 출신 (원시인/현대인)
12. incarnation_type: 환생 유형 (회귀자/빙의자/환생자/없음)

[출력 형식]
JSON으로만 응답하세요.
"""

        response = self.ask(prompt, temperature=0.3)
        result = self._parse_response(response)

        if isinstance(result, dict):
            print(f"      [OK] 기본 정보 추출 완료: {result.get('title', '?')}")
            return result

        # 기본값 반환
        print(f"      [WARN] 기본 정보 추출 실패, 기본값 사용")
        return {
            "title": "제목 미상",
            "protagonist": "주인공",
            "protagonist_faction": "미상",
            "grand_objective": "",
            "logline": "",
            "edge": "",
            "desire": "",
            "crisis": "",
            "cider_point": "",
            "attitude": "능동적 설계자",
            "world_origin": "현대인",
            "incarnation_type": "없음"
        }

    def _extract_npcs(self, episodes: List[str], genre: str) -> List[Dict]:
        """NPC 목록 추출"""
        # 전체 에피소드에서 샘플링 (토큰 제한)
        sample_text = ""
        for i, ep in enumerate(episodes[:5]):  # 최대 5화
            sample_text += f"\n[{i+1}화]\n{ep[:3000]}\n"

        prompt = f"""다음 소설에서 등장하는 주요 NPC(주인공 제외)를 추출하세요.

[원고 샘플]
{sample_text[:15000]}

[추출 항목 - 각 NPC마다]
- name: 이름
- role: 역할 (부친, 라이벌, 멘토, 적대자, 조력자 등)
- desc: 인물 설명 (성격, 동기, 주인공과의 관계)
- status: 현재 상태 (활동중/사망/실종 등)
- relation_to_protagonist: 주인공과의 관계 점수 (-100 ~ 100)

[출력 형식]
JSON 배열로만 응답하세요.
[{{"name": "...", "role": "...", ...}}, ...]
"""

        response = self.ask(prompt, temperature=0.3)
        result = self._parse_response(response)

        if isinstance(result, list):
            print(f"      [OK] NPC {len(result)}명 추출")
            return result
        elif isinstance(result, dict) and "npcs" in result:
            npcs = result["npcs"]
            print(f"      [OK] NPC {len(npcs)}명 추출")
            return npcs
        elif isinstance(result, dict):
            # 단일 NPC가 반환된 경우
            return [result]

        print(f"      [WARN] NPC 추출 실패")
        return []

    def _extract_world_state(self, episodes: List[str], mode: str) -> Dict:
        """세계 설정 추출"""
        # 모드에 따라 1화 또는 마지막 화 분석
        target_ep = episodes[0] if mode == "starting_point" else episodes[-1]

        prompt = f"""다음 소설에서 세계 설정을 추출하세요.

[원고]
{target_ep[:6000]}

[추출 항목]
1. current_era: 시간 배경 (예: "1996년 10월", "정사대전 5년 전")
2. current_location: 현재 위치
3. major_factions: 주요 세력 목록 (이름과 주인공과의 관계)
4. ongoing_conflicts: 진행 중인 갈등
5. economic_context: 경제적 배경 (재벌물인 경우)
6. power_system: 힘의 체계 (무협/헌터의 경우)

[출력 형식]
JSON으로만 응답하세요.
"""

        response = self.ask(prompt, temperature=0.3)
        result = self._parse_response(response)

        if isinstance(result, dict):
            print(f"      [OK] 세계 설정 추출 완료: {result.get('current_era', '?')}")
            return result

        print(f"      [WARN] 세계 설정 추출 실패")
        return {
            "current_era": "",
            "current_location": "",
            "major_factions": [],
            "ongoing_conflicts": [],
            "economic_context": "",
            "power_system": ""
        }

    def _extract_items_and_seeds(self, episodes: List[str]) -> Tuple[List[Dict], List[Dict]]:
        """아이템과 복선 추출"""
        sample_text = "\n".join([ep[:2000] for ep in episodes[:5]])

        prompt = f"""다음 소설에서 중요 아이템과 복선(떡밥)을 추출하세요.

[원고 샘플]
{sample_text[:12000]}

[추출 항목]
1. items: 중요 아이템 목록
   - item: 아이템 이름
   - desc: 설명 및 중요성

2. seeds: 복선/떡밥 목록
   - id: S-001 형식
   - category: 분류 (비기/인물/사건/아이템)
   - description: 복선 내용
   - status: active/dormant

[출력 형식]
JSON으로만 응답하세요.
{{"items": [...], "seeds": [...]}}
"""

        response = self.ask(prompt, temperature=0.4)
        result = self._parse_response(response)

        if isinstance(result, dict):
            items = result.get("items", [])
            seeds = result.get("seeds", [])

            # Seeds에 기본 필드 추가
            for i, seed in enumerate(seeds):
                if "id" not in seed:
                    seed["id"] = f"S-{i+1:03d}"
                if "planted_ep" not in seed:
                    seed["planted_ep"] = 1
                if "echo_count" not in seed:
                    seed["echo_count"] = 0
                if "harvested_ep" not in seed:
                    seed["harvested_ep"] = None

            print(f"      [OK] 아이템 {len(items)}개, 복선 {len(seeds)}개 추출")
            return items, seeds

        print(f"      [WARN] 아이템/복선 추출 실패")
        return [], []

    def _extract_protagonist_hud(self, episodes: List[str], genre: str, mode: str) -> Dict:
        """주인공 상세 HUD 추출"""
        target_ep = episodes[0] if mode == "starting_point" else episodes[-1]

        hud_type = self.genre_hud_map.get(genre, "FinanceHUD")

        if genre == "wuxia":
            hud_template = """
- realm: 무공 경지 (삼류/이류/일류/절정/화경/현경/신경)
- internal_energy: 내공 수준
- mental_method: 수련 심법
- martial_arts: 보유 무공 목록
- equipment: 현재 무기
- injuries: 부상 상태
- inventory: 소지품 목록
"""
        elif genre == "hunter":
            hud_template = """
- awakening_grade: 각성 등급 (F~S)
- mana: 마나 수치
- skills: 스킬 목록
- equipment: 현재 장비
- inventory: 소지품 목록
"""
        else:  # investment
            hud_template = """
- total_assets: 총 자산
- main_portfolio: 주력 투자 영역
- network_level: 인맥 수준
- wealth: 유동 자금 상태
- inventory: 보유 정보/자산 목록
"""

        prompt = f"""다음 소설에서 주인공의 상세 상태를 추출하세요.

[원고]
{target_ep[:6000]}

[추출 항목 - {hud_type}]
- name: 이름
- alias: 별명/칭호
- rank: 사회적 지위
{hud_template}
- current_objective: 현재 단기 목표
- causal_injuries: 현재 컨디션/제약

그리고 세간에 알려진 평판:
- public_identity: 세간에 알려진 정체
- perceived_power: 세간이 인식하는 능력

[출력 형식]
JSON으로만 응답하세요.
{{"actual_truth": {{...}}, "public_reputation": {{...}}}}
"""

        response = self.ask(prompt, temperature=0.3)
        result = self._parse_response(response)

        if isinstance(result, dict):
            print(f"      [OK] 주인공 HUD 추출 완료")
            return result

        print(f"      [WARN] 주인공 HUD 추출 실패")
        return {"actual_truth": {}, "public_reputation": {}}

    def _extract_speech_style(self, first_episode: str) -> Dict:
        """문체 분석"""
        prompt = f"""다음 소설의 문체를 분석하세요.

[원고]
{first_episode[:4000]}

[분석 항목]
1. tone: 어조 (냉소적/유머러스/진지한/서정적 등)
2. vocabulary: 어휘 특성 (고어체/현대어/전문용어/구어체 등)
3. pov: 시점 (1인칭/3인칭 제한/3인칭 전지)
4. sentence_style: 문장 스타일 (간결함/만연체/대화 중심 등)
5. notable_patterns: 특징적인 패턴 (반복 표현, 독특한 묘사 등)

[출력 형식]
JSON으로만 응답하세요.
"""

        response = self.ask(prompt, temperature=0.4)
        result = self._parse_response(response)

        if isinstance(result, dict):
            print(f"      [OK] 문체 분석 완료: {result.get('tone', '?')}")
            return result

        print(f"      [WARN] 문체 분석 실패")
        return {
            "tone": "중립적",
            "vocabulary": "현대어",
            "pov": "3인칭",
            "sentence_style": "간결함",
            "notable_patterns": []
        }

    def _assemble_bible(
        self,
        basic_info: Dict,
        npcs: List[Dict],
        world_state: Dict,
        items: List[Dict],
        seeds: List[Dict],
        protagonist_hud: Dict,
        speech_style: Dict,
        genre: str
    ) -> Dict:
        """최종 Bible 조립"""

        hud_type = self.genre_hud_map.get(genre, "FinanceHUD")

        # KarmaMatrix 생성
        karma_matrix = {}
        for npc in npcs:
            name = npc.get("name", "")
            if name:
                karma_matrix[name] = {
                    "relation_score": npc.get("relation_to_protagonist", 0),
                    "status": npc.get("status", "활동중")
                }

        # 세력 정보도 KarmaMatrix에 추가
        for faction in world_state.get("major_factions", []):
            if isinstance(faction, dict):
                name = faction.get("name", "")
                if name and name not in karma_matrix:
                    karma_matrix[name] = {
                        "relation_score": faction.get("relation", 0),
                        "status": faction.get("status", "중립")
                    }

        # NPC를 KeyNPCs 형식으로 변환
        key_npcs = []
        for npc in npcs:
            key_npc = {
                "name": npc.get("name", ""),
                "role": npc.get("role", ""),
                "desc": npc.get("desc", ""),
                f"NPC_{genre.capitalize()}_HUD": {
                    "status": npc.get("status", "활동중"),
                    "trait": npc.get("trait", "")
                }
            }
            key_npcs.append(key_npc)

        # Bible 구조 조립
        bible = {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {
                        "title": basic_info.get("title", "제목 미상"),
                        "grand_objective": basic_info.get("grand_objective", ""),
                        "genre_archetype": f"{genre} + {basic_info.get('sub_genre', '성장물')}",
                        "logline": basic_info.get("logline", "")
                    },
                    "CoreIdentity": {
                        "protagonist": basic_info.get("protagonist", "주인공"),
                        "protagonist_faction": basic_info.get("protagonist_faction", ""),
                        "edge": basic_info.get("edge", ""),
                        "desire": basic_info.get("desire", ""),
                        "crisis": basic_info.get("crisis", "")
                    },
                    "CommercialCode": {
                        "cider_point": basic_info.get("cider_point", ""),
                        "success_device": basic_info.get("success_device", ""),
                        "attitude": basic_info.get("attitude", "능동적 설계자")
                    }
                },

                "protagonist_config": {
                    "world_origin": basic_info.get("world_origin", "현대인"),
                    "incarnation_type": basic_info.get("incarnation_type", "없음")
                },

                hud_type: {
                    "Protagonist": protagonist_hud
                },

                "WorldState": {
                    "CurrentEra": world_state.get("current_era", ""),
                    "CurrentLocation": world_state.get("current_location", ""),
                    "KarmaMatrix": karma_matrix
                },

                "AssetLibrary": {
                    "KeyNPCs": key_npcs,
                    "KeyItems": items,
                    "Persona": speech_style.get("pov", "3인칭"),
                    "SpeechStyle": {
                        "tone": speech_style.get("tone", ""),
                        "vocabulary": speech_style.get("vocabulary", "")
                    }
                },

                "Seeds": seeds
            }
        }

        return bible

    def _create_empty_bible(self, genre: str) -> Dict:
        """빈 Bible 템플릿 생성"""
        hud_type = self.genre_hud_map.get(genre, "FinanceHUD")

        return {
            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": {"title": "", "grand_objective": "", "genre_archetype": "", "logline": ""},
                    "CoreIdentity": {"protagonist": "", "protagonist_faction": "", "edge": "", "desire": "", "crisis": ""},
                    "CommercialCode": {"cider_point": "", "success_device": "", "attitude": ""}
                },
                "protagonist_config": {"world_origin": "", "incarnation_type": ""},
                hud_type: {"Protagonist": {"actual_truth": {}, "public_reputation": {}}},
                "WorldState": {"CurrentEra": "", "CurrentLocation": "", "KarmaMatrix": {}},
                "AssetLibrary": {"KeyNPCs": [], "KeyItems": [], "Persona": "", "SpeechStyle": {}},
                "Seeds": []
            }
        }

    def _print_stats(self):
        """통계 출력"""
        print(f"\n[추출 통계]")
        print(f"   처리 청크: {self.stats['chunks_processed']}")
        print(f"   발견 NPC: {self.stats['npcs_found']}명")
        print(f"   발견 아이템: {self.stats['items_found']}개")
        print(f"   발견 복선: {self.stats['seeds_found']}개")


def create_bible_extractor(context, client, model_tier: str = "gemini-2.5-pro"):
    """BibleExtractor 생성 헬퍼"""
    return BibleExtractor(context, client, model_tier)
