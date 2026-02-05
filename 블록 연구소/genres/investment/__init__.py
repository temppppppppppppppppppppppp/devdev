"""
Investment Genre - 투자물 장르 모듈
===================================
회귀 투자, 재벌물, 금융 스릴러

특징:
- 시대별 투자 전략 어드바이저
- 실존 금융인/재벌/테크 거물 DB
- IMF, 금융위기 등 역사 이벤트
- 자본 추적 HUD
"""

from genres.base_genre import BaseGenre
from genres.investment.advisor import InvestmentAdvisor
from genres.investment.figures import REAL_FIGURES, FIGURE_APPEARANCE_GUIDE
from genres.investment.events import HISTORICAL_EVENTS
from genres.investment.config import (
    INVESTMENT_STRATEGIES,
    ROMANCE_RULES,
    GENRE_RULES,
    NPC_ROLES,
    POWER_PROGRESSION
)
from typing import Dict, List


class InvestmentGenre(BaseGenre):
    """투자물 장르"""

    GENRE_ID = "investment"
    GENRE_NAME = "투자물"
    GENRE_DESC = "회귀 투자, 재벌물, 금융 스릴러, 경제 복수극"

    HUD_TYPE = "FinanceHUD"

    ARCHETYPES = [
        "회귀 + 투자",
        "현대 재벌물",
        "금융 스릴러",
        "복수 + 투자",
        "재벌가 암투",
        "월스트리트 정복"
    ]

    TYPICAL_SETTINGS = [
        "1990년대 IMF",
        "2008년 금융위기",
        "현대 주식시장",
        "가상화폐 시대",
        "1980년대 버블",
        "닷컴 버블"
    ]

    def get_advisor(self, start_era: str):
        """투자 전략 어드바이저"""
        return InvestmentAdvisor(start_era)

    def get_historical_events(self, start_era: str) -> List[Dict]:
        """시대별 역사 이벤트"""
        all_events = []
        for category, events in HISTORICAL_EVENTS.items():
            all_events.extend(events)

        # 시작 시점 이후만 필터
        if start_era:
            all_events = [e for e in all_events if e["month"] >= start_era]

        return sorted(all_events, key=lambda x: x["month"])

    def get_real_figures(self) -> Dict[str, List[Dict]]:
        """실존 인물 DB"""
        return REAL_FIGURES

    def get_figure_appearance_guide(self) -> Dict[str, Dict]:
        """인물 등장 가이드"""
        return FIGURE_APPEARANCE_GUIDE

    def get_romance_rules(self) -> Dict:
        """로맨스 규칙"""
        return ROMANCE_RULES

    def get_genre_rules(self) -> Dict:
        """장르 규칙"""
        return GENRE_RULES

    def get_npc_roles(self) -> List[Dict]:
        """필수 NPC 역할"""
        return NPC_ROLES

    def get_power_progression_template(self) -> Dict:
        """성장 곡선"""
        return POWER_PROGRESSION

    def build_initial_hud(self, protagonist_info: Dict) -> Dict:
        """Finance HUD 초기화"""
        name = protagonist_info.get("name", "주인공")
        start_month = protagonist_info.get("start_month", "1996-01")
        initial_assets = protagonist_info.get("initial_assets", "50만원")
        debt = protagonist_info.get("debt", "없음")

        return {
            "Protagonist": {
                "actual_truth": {
                    "name": name,
                    "alias": "없음",
                    "age": protagonist_info.get("age", 28),
                    "rank": protagonist_info.get("rank", "무직"),

                    "financial_status": {
                        "total_assets": initial_assets,
                        "liquid_cash": initial_assets,
                        "stocks": [],
                        "real_estate": [],
                        "foreign_currency": {"USD": 0, "JPY": 0},
                        "debt": debt
                    },

                    "portfolio_history": [
                        {
                            "episode": 0,
                            "month": start_month,
                            "total_assets": initial_assets,
                            "event": "시작점"
                        }
                    ],

                    "investment_style": protagonist_info.get("investment_style", "미래 지식 기반 투자"),
                    "risk_tolerance": protagonist_info.get("risk_tolerance", "고위험"),

                    "network_level": {
                        "financial_sector": 0,
                        "political_sector": 0,
                        "business_sector": 0,
                        "underground_sector": 0
                    },

                    "credentials": [],
                    "current_objective": protagonist_info.get("current_objective", "종잣돈 불리기"),
                    "mid_term_goal": protagonist_info.get("mid_term_goal", "자본 확보"),
                    "final_goal": protagonist_info.get("final_goal", "재벌/거물"),
                    "causal_injuries": protagonist_info.get("trauma", "없음")
                },

                "public_reputation": {
                    "identity": protagonist_info.get("public_identity", "평범한 청년"),
                    "wealth_level": "빈곤층",
                    "perceived_influence": "없음",
                    "credit_rating": protagonist_info.get("credit_rating", "일반")
                }
            }
        }

    def get_genre_ext_schema(self) -> Dict:
        """장르별 확장 메타데이터 스키마"""
        return {
            "capital_before": "이전 자본",
            "capital_after": "이후 자본",
            "capital_delta": "+/- 변화",
            "investment_type": "주식|부동산|외환|암호화폐|사업",
            "method": "투자 방법",
            "risk_level": "저|중|고|극고",
            "leverage": "레버리지 여부"
        }
