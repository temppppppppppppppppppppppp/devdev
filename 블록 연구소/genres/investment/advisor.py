"""
Investment Advisor - 투자 전략 어드바이저
=========================================
시대별 투자 추천, 실존 인물 등장 타이밍, 로맨스 가이드
"""

from typing import Dict, List, Optional
from genres.investment.config import INVESTMENT_STRATEGIES, ROMANCE_RULES
from genres.investment.figures import FIGURE_APPEARANCE_GUIDE
from genres.investment.events import HISTORICAL_EVENTS


class InvestmentAdvisor:
    """투자물 전략 어드바이저"""

    def __init__(self, start_era: str):
        self.start_year = int(start_era[:4]) if start_era else 1996
        self.start_month = start_era
        self.used_figures = []

    def get_investment_recommendations(self, current_block: int, total_blocks: int = 60) -> dict:
        """현재 블록에 맞는 투자 전략 추천"""
        progress = current_block / total_blocks
        years_passed = int(progress * 10)
        current_year = str(self.start_year + years_passed)

        recommendations = {
            "current_phase": "",
            "hot_investments": [],
            "avoid": [],
            "upcoming_events": [],
            "advice": ""
        }

        # 시대별 전략 찾기
        base_strategies = None
        for year_key in sorted(INVESTMENT_STRATEGIES.keys(), reverse=True):
            if int(year_key) <= int(current_year):
                base_strategies = INVESTMENT_STRATEGIES[year_key]
                break

        if base_strategies:
            if progress < 0.3:
                recommendations["current_phase"] = "초기 자본 축적기"
                recommendations["hot_investments"] = base_strategies.get("hot", [])[:2]
                recommendations["advice"] = "위기 전 선제적 포지셔닝이 핵심입니다."
            elif progress < 0.5:
                recommendations["current_phase"] = "위기 활용기"
                recommendations["hot_investments"] = base_strategies.get("hot", [])
                recommendations["avoid"] = base_strategies.get("avoid", [])
                recommendations["advice"] = "남들이 공포에 떨 때가 기회입니다."
            elif progress < 0.7:
                recommendations["current_phase"] = "확장기"
                recommendations["hot_investments"] = base_strategies.get("post_crisis", [])[:2]
                recommendations["advice"] = "회복기에 우량 자산을 저점 매수합니다."
            else:
                recommendations["current_phase"] = "지배기"
                recommendations["hot_investments"] = base_strategies.get("post_crisis", [])
                recommendations["advice"] = "글로벌 확장과 다각화의 시기입니다."

        # 다가오는 이벤트
        for db_name, events in HISTORICAL_EVENTS.items():
            for event in events:
                event_year = int(event["month"][:4])
                if self.start_year <= event_year <= self.start_year + years_passed + 2:
                    if event not in recommendations["upcoming_events"]:
                        recommendations["upcoming_events"].append(event)

        recommendations["upcoming_events"] = sorted(
            recommendations["upcoming_events"],
            key=lambda x: x["month"]
        )[:5]

        return recommendations

    def get_figure_recommendation(self, current_block: int, total_blocks: int = 60,
                                   used_figures: List[str] = None) -> List[dict]:
        """현재 블록에 등장시킬 실존 인물 추천"""
        used_figures = used_figures or self.used_figures
        progress = current_block / total_blocks
        years_passed = int(progress * 10)
        current_year = str(self.start_year + years_passed)

        recommendations = []

        for category, figures in FIGURE_APPEARANCE_GUIDE.items():
            for name, info in figures.items():
                if name in used_figures:
                    continue

                # 사망 체크
                if info.get("death"):
                    death_year = int(info["death"][:4])
                    if int(current_year) > death_year:
                        continue

                # 은퇴 체크
                if info.get("retirement"):
                    retire_year = int(info["retirement"][:4])
                    if int(current_year) > retire_year + 5:
                        continue

                # 적절한 시기인지 체크
                relevance = info.get("peak_relevance", [])
                is_relevant = False

                for rel_year in relevance:
                    if rel_year == "always":
                        is_relevant = True
                        break
                    if abs(int(rel_year) - int(current_year)) <= 3:
                        is_relevant = True
                        break

                if is_relevant:
                    recommendations.append({
                        "name": name,
                        "category": category,
                        "story_hook": info.get("story_hook", ""),
                        "meeting_scenario": info.get("meeting_scenario", ""),
                        "personality": info.get("personality", ""),
                        "what_they_want": info.get("what_they_want", ""),
                        "signature_line": info.get("signature_line", ""),
                        "warning": info.get("warning", None)
                    })

        # 블록 위치에 따른 우선순위
        if progress < 0.2:
            priority_categories = ["korean_chaebol", "investors"]
        elif progress < 0.5:
            priority_categories = ["investors", "korean_chaebol"]
        else:
            priority_categories = ["tech_founders", "investors"]

        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: priority_categories.index(x["category"]) if x["category"] in priority_categories else 99
        )

        return sorted_recommendations[:3]

    def get_romance_guidance(self, female_npc_type: str = None) -> dict:
        """로맨스 가이드라인"""
        guidance = {
            "protagonist_rule": ROMANCE_RULES["protagonist"],
            "female_interest_triggers": ROMANCE_RULES["female_npcs"]["interest_triggers"],
            "tension_devices": ROMANCE_RULES["tension_devices"],
            "recommended_archetype": None,
            "scene_suggestions": []
        }

        if female_npc_type:
            for archetype in ROMANCE_RULES["female_npcs"]["archetypes"]:
                if archetype["type"] in female_npc_type:
                    guidance["recommended_archetype"] = archetype
                    break
        else:
            guidance["recommended_archetype"] = ROMANCE_RULES["female_npcs"]["archetypes"][0]

        guidance["scene_suggestions"] = [
            "히로인이 호감 표시 → 주인공 '바쁘다'고 회피",
            "위기에서 주인공이 히로인을 구함 → 별 말 없이 떠남",
            "다른 남자가 히로인에게 접근 → 주인공은 무관심",
            "술 취한 히로인 본심 고백 → 주인공 못 들은 척"
        ]

        return guidance

    def generate_block_advice(self, block_num: int, block_info: dict = None,
                               used_figures: List[str] = None) -> dict:
        """블록별 종합 어드바이스"""
        investment_rec = self.get_investment_recommendations(block_num)
        figure_rec = self.get_figure_recommendation(block_num, used_figures=used_figures)
        romance_guide = self.get_romance_guidance()

        advice = {
            "block_num": block_num,
            "investment": investment_rec,
            "suggested_figures": figure_rec,
            "romance_reminder": {
                "rule": "주인공은 호감 표현 금지",
                "allowed": "여성 NPC가 주인공에게 호감 보이는 것은 OK"
            },
            "overall_tip": ""
        }

        if block_num <= 5:
            advice["overall_tip"] = "초반부입니다. 주인공의 초기 설정과 동기를 확립하세요."
        elif block_num <= 15:
            advice["overall_tip"] = "성장기입니다. 첫 번째 큰 성공과 조력자 확보가 필요합니다."
        elif block_num <= 30:
            advice["overall_tip"] = "중반입니다. 실존 인물과의 첫 만남을 고려하세요."
        elif block_num <= 45:
            advice["overall_tip"] = "도약기입니다. 대형 투자와 글로벌 확장의 시기입니다."
        else:
            advice["overall_tip"] = "클라이맥스입니다. 최종 목표 달성을 향해 가세요."

        return advice

    def mark_figure_used(self, figure_name: str):
        """사용된 인물 기록"""
        if figure_name not in self.used_figures:
            self.used_figures.append(figure_name)

    def get_arc_recommendations(self, total_arcs: int = 10) -> List[dict]:
        """Arc별 전략 추천"""
        arc_recs = []

        for arc in range(1, total_arcs + 1):
            block_start = (arc - 1) * 6 + 1
            inv_rec = self.get_investment_recommendations(block_start)
            fig_rec = self.get_figure_recommendation(block_start)

            arc_recs.append({
                "arc": arc,
                "blocks": f"{block_start}-{block_start + 5}",
                "phase": inv_rec.get("current_phase", ""),
                "hot_investments": [i["type"] for i in inv_rec.get("hot_investments", [])[:2]],
                "suggested_figures": [f["name"] for f in fig_rec[:2]],
                "advice": inv_rec.get("advice", "")
            })

        return arc_recs
