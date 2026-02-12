import json

class KarmaService:
    def __init__(self, context) -> None:
        self.context = context
        # DB에서 현재 문파 관계 및 주인공 평판 인출
        self.sect_relations = (getattr(context, 'latest_state', None) or {}).get('world', {}).get('sect_relations', {})  # [V70] None 방어

    def get_relationship_report(self, target_sect: str, current_event_context: str = "") -> dict:
        """AI에게 전달할 관계적 팩트 리포트 생성"""
        score = self.sect_relations.get(target_sect, 0)
        reputation = (getattr(self.context, 'latest_state', None) or {}).get('protagonist', {}).get('reputation', '초출')  # [V70] None 방어
        
        # [Fact-Only Report] AI가 이 데이터를 보고 말투를 결정함
        report = {
            "target_sect": target_sect,
            "numeric_relation": score, # -100 ~ 100
            "mc_reputation": reputation,
            "recent_context": current_event_context,
            "instruction": "위 수치와 맥락을 바탕으로, 해당 문파원들이 주인공의 '자기중심적 유능함'에 전율하며 보일 법한 최적의 호칭과 반응을 창조하라."
        }
        return report