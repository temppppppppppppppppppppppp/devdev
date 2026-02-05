"""
Hunter Genre - 헌터물 장르 모듈
===============================
던전물, 헌터 각성, 타워 클라이밍

특징:
- 레벨/스탯 성장 어드바이저
- 유명 헌터 / 길드 DB
- 던전/게이트 이벤트
- 헌터 스탯 추적 HUD
"""

from genres.base_genre import BaseGenre
from typing import Dict, List


class HunterAdvisor:
    """헌터물 전략 어드바이저"""

    def __init__(self, start_era: str):
        self.start_era = start_era
        self.used_figures = []

    def get_growth_recommendations(self, current_block: int, total_blocks: int = 60) -> dict:
        """성장 추천"""
        progress = current_block / total_blocks

        if progress < 0.15:
            return {
                "phase": "각성기",
                "recommended_activity": ["각성", "기본 훈련", "E급 던전"],
                "target_rank": "E급",
                "advice": "생존이 우선. 무리한 도전 금지."
            }
        elif progress < 0.3:
            return {
                "phase": "성장기",
                "recommended_activity": ["D급 던전", "파티 사냥", "스킬 습득"],
                "target_rank": "D급",
                "advice": "경험치 축적이 중요합니다."
            }
        elif progress < 0.5:
            return {
                "phase": "도약기",
                "recommended_activity": ["C급 던전", "솔로잉", "길드 가입"],
                "target_rank": "C급",
                "advice": "자신만의 전투 스타일을 확립하세요."
            }
        elif progress < 0.7:
            return {
                "phase": "일류기",
                "recommended_activity": ["B급 던전", "레이드 참가", "유니크 스킬"],
                "target_rank": "B급",
                "advice": "상위 랭커들과 네트워크를 구축하세요."
            }
        elif progress < 0.85:
            return {
                "phase": "최정상",
                "recommended_activity": ["A급 던전", "레이드 리딩", "길드 운영"],
                "target_rank": "A급",
                "advice": "국가급 위협에 대응할 준비를 하세요."
            }
        else:
            return {
                "phase": "전설",
                "recommended_activity": ["S급 던전", "세계적 위협 대응", "새로운 경지"],
                "target_rank": "S급",
                "advice": "인류 최강의 수호자가 되세요."
            }

    def get_figure_recommendation(self, current_block: int, used_figures: List[str] = None) -> List[dict]:
        """등장 추천 인물"""
        return [
            {"name": "S급 헌터", "role": "멘토/라이벌", "story_hook": "주인공의 잠재력 발견"},
            {"name": "길드장", "role": "조력자/장애물", "story_hook": "영입 제안 또는 갈등"}
        ]

    def get_dungeon_recommendation(self, current_block: int) -> dict:
        """던전 추천"""
        progress = current_block / 60

        if progress < 0.2:
            return {"rank": "E-D급", "type": "고블린 던전", "reward": "기본 마석"}
        elif progress < 0.4:
            return {"rank": "D-C급", "type": "언데드 던전", "reward": "장비/스킬북"}
        elif progress < 0.6:
            return {"rank": "C-B급", "type": "보스 던전", "reward": "유니크 아이템"}
        elif progress < 0.8:
            return {"rank": "B-A급", "type": "레이드 던전", "reward": "레전드리 장비"}
        else:
            return {"rank": "A-S급", "type": "세계급 위협", "reward": "신화급 보상"}

    def generate_block_advice(self, block_num: int, block_info: dict = None, used_figures: List[str] = None) -> dict:
        """블록별 어드바이스"""
        growth_rec = self.get_growth_recommendations(block_num)
        dungeon_rec = self.get_dungeon_recommendation(block_num)
        return {
            "block_num": block_num,
            "growth": growth_rec,
            "dungeon": dungeon_rec,
            "overall_tip": growth_rec.get("advice", "")
        }


class HunterGenre(BaseGenre):
    """헌터물 장르"""

    GENRE_ID = "hunter"
    GENRE_NAME = "헌터물"
    GENRE_DESC = "던전물, 헌터 각성, 타워 클라이밍, 게이트물"

    HUD_TYPE = "HunterHUD"

    ARCHETYPES = [
        "회귀 헌터",
        "각성 헌터",
        "던전 공략",
        "타워 클라이밍",
        "시스템물",
        "길드 경영"
    ]

    TYPICAL_SETTINGS = [
        "현대 한국",
        "대재앙 이후",
        "게이트 출현 세계",
        "던전 내부",
        "헌터 협회",
        "탑 내부"
    ]

    def get_advisor(self, start_era: str):
        return HunterAdvisor(start_era)

    def get_historical_events(self, start_era: str) -> List[Dict]:
        """주요 이벤트"""
        return [
            {"month": "001", "event": "첫 게이트 출현", "impact": "세계 변화 시작"},
            {"month": "005", "event": "S급 던전 브레이크", "impact": "국가급 피해"},
            {"month": "010", "event": "헌터 협회 창설", "impact": "체계화"},
            {"month": "020", "event": "대형 레이드", "impact": "랭커 연합 결성"},
            {"month": "030", "event": "탑 출현", "impact": "새로운 도전"},
            {"month": "040", "event": "외계 침공", "impact": "인류 위기"},
            {"month": "050", "event": "신급 존재 등장", "impact": "차원이 다른 위협"},
        ]

    def get_real_figures(self) -> Dict[str, List[Dict]]:
        """유명 헌터"""
        return {
            "korean_rankers": [
                {"name": "국가대표 S급", "field": "검술", "trait": "한국 최강"},
                {"name": "길드장", "field": "마법", "trait": "대형 길드 운영"},
                {"name": "솔로 랭커", "field": "암살", "trait": "신비주의"},
            ],
            "global_rankers": [
                {"name": "미국 1위", "field": "총기", "trait": "화력 최강"},
                {"name": "중국 대장로", "field": "무술", "trait": "전통 무술 계승"},
                {"name": "유럽 마탑주", "field": "마법", "trait": "마법 연구"},
            ]
        }

    def get_figure_appearance_guide(self) -> Dict[str, Dict]:
        """인물 등장 가이드"""
        return {
            "mentors": {
                "은퇴한 S급": {
                    "peak_relevance": ["초반"],
                    "story_hook": "주인공의 재능 발견, 훈련",
                    "meeting_scenario": "던전에서 우연히 / 협회 소개"
                }
            },
            "rivals": {
                "천재 신인": {
                    "peak_relevance": ["중반"],
                    "story_hook": "같은 시기 각성, 경쟁 관계"
                }
            }
        }

    def get_romance_rules(self) -> Dict:
        return {
            "protagonist": {
                "shows_interest": False,
                "priority": "성장/생존 > 로맨스",
                "typical_response": ["레벨업에 집중", "던전이 먼저"]
            },
            "female_npcs": {
                "can_show_interest": True,
                "archetypes": [
                    {"type": "파티원 힐러", "trait": "함께 성장하며 정 생김"},
                    {"type": "길드 부마스터", "trait": "능력에 반함"},
                    {"type": "S급 여헌터", "trait": "강한 자에게만 관심"},
                ]
            }
        }

    def get_genre_rules(self) -> Dict:
        return {
            "must_include": [
                "레벨/스탯이 명확히 추적되어야 함",
                "성장에 합리적 근거 (경험치, 아이템 등)",
                "던전 난이도에 맞는 보상"
            ],
            "forbidden": [
                "근거 없는 레벨 점프",
                "무한 스탯 치트",
                "죽음에서 페널티 없이 부활"
            ],
            "tension_devices": [
                "던전 브레이크",
                "파티 전멸 위기",
                "랭킹 경쟁",
                "길드 전쟁",
                "PK/배신"
            ]
        }

    def get_npc_roles(self) -> List[Dict]:
        return [
            {"role": "멘토", "count": "1명", "desc": "고랭커 선배"},
            {"role": "메인 빌런", "count": "1-2명", "desc": "악역 헌터/보스 몬스터"},
            {"role": "라이벌", "count": "1-2명", "desc": "경쟁 헌터"},
            {"role": "파티원", "count": "3-4명", "desc": "탱커/딜러/힐러/서포터"},
            {"role": "히로인", "count": "1-2명", "desc": "여헌터"},
        ]

    def get_power_progression_template(self) -> Dict:
        return {
            "initial": {"rank": "각성 전/E급", "level": "1-10", "blocks": "1-10"},
            "early": {"rank": "E→D급", "level": "10-30", "blocks": "11-20"},
            "mid": {"rank": "D→C급", "level": "30-50", "blocks": "21-35"},
            "late": {"rank": "C→B→A급", "level": "50-80", "blocks": "36-50"},
            "final": {"rank": "A→S급", "level": "80-100+", "blocks": "51-60"}
        }

    def build_initial_hud(self, protagonist_info: Dict) -> Dict:
        """Hunter HUD 초기화"""
        return {
            "Protagonist": {
                "actual_truth": {
                    "name": protagonist_info.get("name", "주인공"),
                    "hunter_name": protagonist_info.get("hunter_name", ""),
                    "age": protagonist_info.get("age", 25),
                    "rank": protagonist_info.get("rank", "E급"),
                    "class": protagonist_info.get("class", "미정"),
                    "level": protagonist_info.get("level", 1),
                    "skills": [],
                    "stats": {
                        "strength": 10,
                        "agility": 10,
                        "intelligence": 10,
                        "vitality": 10,
                        "luck": 10
                    },
                    "guild": protagonist_info.get("guild", "무소속"),
                    "balance": protagonist_info.get("balance", "100만원"),
                    "equipment": [],
                    "current_objective": protagonist_info.get("current_objective", "각성/생존"),
                    "final_goal": protagonist_info.get("final_goal", "최강의 헌터")
                },
                "public_reputation": {
                    "identity": protagonist_info.get("public_identity", "신인 헌터"),
                    "rank_perception": "E급",
                    "fame_level": 0
                }
            }
        }

    def get_genre_ext_schema(self) -> Dict:
        """장르별 확장 메타데이터"""
        return {
            "level_before": "이전 레벨",
            "level_after": "이후 레벨",
            "exp_gained": "획득 경험치",
            "skills_gained": "획득 스킬",
            "items_gained": "획득 아이템",
            "dungeon_cleared": "클리어 던전",
            "rank_change": "등급 변화"
        }
