"""
Wuxia Genre - 무협 장르 모듈
============================
정통 무협, 회귀 무협, 현대 무협

특징:
- 무공 성장 어드바이저
- 역사적 무림인 / 가상 고수 DB
- 강호 이벤트
- 무공/경지 추적 HUD
"""

from genres.base_genre import BaseGenre
from typing import Dict, List


class WuxiaAdvisor:
    """무협 전략 어드바이저"""

    def __init__(self, start_era: str):
        self.start_era = start_era
        self.used_figures = []

    def get_martial_recommendations(self, current_block: int, total_blocks: int = 60) -> dict:
        """무공 성장 추천"""
        progress = current_block / total_blocks

        if progress < 0.2:
            return {
                "phase": "입문기",
                "recommended_training": ["기초 내공", "기본 검술", "경공 입문"],
                "target_rank": "삼류",
                "advice": "기초를 탄탄히. 사부 찾기가 급선무."
            }
        elif progress < 0.4:
            return {
                "phase": "성장기",
                "recommended_training": ["내공 축적", "무파 무공", "실전 경험"],
                "target_rank": "이류",
                "advice": "실전에서 깨달음을 얻어야 합니다."
            }
        elif progress < 0.6:
            return {
                "phase": "도약기",
                "recommended_training": ["비전 무공", "내공 심화", "무공 융합"],
                "target_rank": "일류",
                "advice": "고수들과의 대결로 한계를 깨세요."
            }
        elif progress < 0.8:
            return {
                "phase": "절정기",
                "recommended_training": ["절정 무공", "자기만의 초식", "심법 완성"],
                "target_rank": "절정",
                "advice": "자신만의 길을 찾아야 할 때입니다."
            }
        else:
            return {
                "phase": "화경/초월",
                "recommended_training": ["무의 경지", "무아지경", "천인합일"],
                "target_rank": "화경/초절정",
                "advice": "기술을 넘어 도(道)의 영역입니다."
            }

    def get_figure_recommendation(self, current_block: int, used_figures: List[str] = None) -> List[dict]:
        """등장 추천 인물"""
        # TODO: 실제 무림 고수 DB 구축 후 구현
        return [
            {"name": "은거 고수", "role": "멘토", "story_hook": "주인공에게 비전 전수"},
            {"name": "전대 마교 교주", "role": "빌런", "story_hook": "부활 또는 후계자"}
        ]

    def generate_block_advice(self, block_num: int, block_info: dict = None, used_figures: List[str] = None) -> dict:
        """블록별 어드바이스"""
        martial_rec = self.get_martial_recommendations(block_num)
        return {
            "block_num": block_num,
            "martial_growth": martial_rec,
            "overall_tip": martial_rec.get("advice", "")
        }


class WuxiaGenre(BaseGenre):
    """무협 장르"""

    GENRE_ID = "wuxia"
    GENRE_NAME = "무협"
    GENRE_DESC = "정통 무협, 회귀 무협, 현대 무협, 무림 쟁패"

    HUD_TYPE = "MartialHUD"

    ARCHETYPES = [
        "정통 무협",
        "회귀 무협",
        "현대 무협",
        "사이버펑크 무협",
        "마교 루트",
        "문파 재건"
    ]

    TYPICAL_SETTINGS = [
        "중원 강호",
        "변방 소문파",
        "마교 본산",
        "황실/조정",
        "천하제일대회",
        "비경/동굴"
    ]

    def get_advisor(self, start_era: str):
        return WuxiaAdvisor(start_era)

    def get_historical_events(self, start_era: str) -> List[Dict]:
        """강호 이벤트"""
        return [
            {"month": "001", "event": "무림맹 창설", "impact": "정파 연합"},
            {"month": "010", "event": "마교 침공", "impact": "강호 혼란"},
            {"month": "020", "event": "천하제일대회", "impact": "고수 집결"},
            {"month": "030", "event": "비급 출현", "impact": "쟁탈전 시작"},
            {"month": "040", "event": "무림맹주 교체", "impact": "정파 분열"},
            {"month": "050", "event": "마교 분열", "impact": "혼란의 시대"},
        ]

    def get_real_figures(self) -> Dict[str, List[Dict]]:
        """전설적 인물"""
        return {
            "legendary": [
                {"name": "무당 진인", "field": "검술", "trait": "검선"},
                {"name": "소림 방장", "field": "권법", "trait": "금강불괴"},
                {"name": "전대 마교주", "field": "마공", "trait": "천마"},
            ],
            "historical": [
                {"name": "장삼풍", "real": "무당파 창시자", "trait": "태극권"},
                {"name": "달마", "real": "소림 시조", "trait": "역근경"},
            ]
        }

    def get_figure_appearance_guide(self) -> Dict[str, Dict]:
        """인물 등장 가이드"""
        return {
            "mentors": {
                "은거 고수": {
                    "peak_relevance": ["초반"],
                    "story_hook": "주인공에게 비전 전수",
                    "meeting_scenario": "절벽 아래 / 동굴 속 / 주막",
                    "personality": "괴팍하지만 실력은 인정"
                }
            },
            "rivals": {
                "천재 무인": {
                    "peak_relevance": ["중반", "후반"],
                    "story_hook": "주인공과 라이벌 관계",
                    "meeting_scenario": "대회 / 우연한 대결"
                }
            }
        }

    def get_romance_rules(self) -> Dict:
        """로맨스 규칙"""
        return {
            "protagonist": {
                "shows_interest": False,
                "priority": "무공/복수 > 로맨스",
                "typical_response": ["무공 수련에 집중", "의리로 대함"]
            },
            "female_npcs": {
                "can_show_interest": True,
                "archetypes": [
                    {"type": "무림 여협", "trait": "당당하지만 주인공에게 약함"},
                    {"type": "문파 영애", "trait": "정혼 관계 / 정략"},
                    {"type": "마녀", "trait": "악연으로 시작, 정 생김"},
                ]
            }
        }

    def get_genre_rules(self) -> Dict:
        return {
            "must_include": [
                "무공 경지가 명확히 추적되어야 함",
                "수련 과정이 설득력 있어야 함",
                "고수일수록 신중한 행동"
            ],
            "forbidden": [
                "경지 뛰어넘는 승리 (합리적 이유 없이)",
                "무공 즉석 터득 (수련 없이)",
                "내공 무한"
            ],
            "tension_devices": [
                "상성 관계",
                "부상/내상",
                "비급 쟁탈",
                "문파 위기"
            ]
        }

    def get_npc_roles(self) -> List[Dict]:
        return [
            {"role": "사부/멘토", "count": "1-2명", "desc": "주인공에게 무공 전수"},
            {"role": "메인 빌런", "count": "1-2명", "desc": "마교 또는 사파 고수"},
            {"role": "라이벌", "count": "1-2명", "desc": "경쟁하며 성장"},
            {"role": "동료", "count": "2-3명", "desc": "함께 모험"},
            {"role": "히로인", "count": "1-2명", "desc": "무림 여협"},
        ]

    def get_power_progression_template(self) -> Dict:
        return {
            "initial": {"rank": "말류/삼류", "blocks": "1-10"},
            "early": {"rank": "삼류→이류", "blocks": "11-20"},
            "mid": {"rank": "이류→일류", "blocks": "21-35"},
            "late": {"rank": "일류→절정", "blocks": "36-50"},
            "final": {"rank": "절정→화경", "blocks": "51-60"}
        }

    def build_initial_hud(self, protagonist_info: Dict) -> Dict:
        """Martial HUD 초기화"""
        return {
            "Protagonist": {
                "actual_truth": {
                    "name": protagonist_info.get("name", "주인공"),
                    "alias": protagonist_info.get("alias", "없음"),
                    "age": protagonist_info.get("age", 18),
                    "rank": protagonist_info.get("rank", "말류"),
                    "martial_arts": [],
                    "internal_energy": protagonist_info.get("internal_energy", 10),
                    "faction": protagonist_info.get("faction", "무소속"),
                    "reputation": {"righteous": 0, "evil": 0, "neutral": 50},
                    "injuries": [],
                    "current_objective": protagonist_info.get("current_objective", "생존"),
                    "final_goal": protagonist_info.get("final_goal", "무림 정상")
                },
                "public_reputation": {
                    "identity": protagonist_info.get("public_identity", "무명 소협"),
                    "rank_perception": "말류",
                    "fame_level": 0
                }
            }
        }

    def get_genre_ext_schema(self) -> Dict:
        """장르별 확장 메타데이터"""
        return {
            "internal_energy_before": "이전 내공",
            "internal_energy_after": "이후 내공",
            "martial_arts_gained": "획득 무공",
            "rank_change": "경지 변화",
            "battle_outcome": "승/패/무",
            "injuries_gained": "부상"
        }
