from .base_strategy import BaseStrategy


class CookingStrategy(BaseStrategy):
    @property
    def genre_name(self):
        return "COOKING"

    def get_system_prompt(self) -> str:
        genre_rules = self.law.get("cooking", {})

        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        ctx = self.studio.project

        selected_tone = getattr(ctx, "selected_tone", {})
        tone_name = selected_tone.get("name", "요리 전문가물")
        tone_guide = selected_tone.get("writer", "요리의 감동과 식당 경영의 현실이 교차하는 문체")

        # 2. 주인공 정보 인출
        bible_root = ctx.master_bible.get("MasterBible", ctx.master_bible)
        hud = bible_root.get("CookingHUD", bible_root.get("cooking_hud", {}))
        protagonist = hud.get("Protagonist", hud.get("main", {}))

        mc_name = protagonist.get("Name", protagonist.get("name", "요리사"))
        mc_desc = protagonist.get("description", "천재적 미각의 요리사")

        return f"""
        [COOKING GENRE GUIDELINE]
        1. 장르 필수 요소: {", ".join(genre_rules.get("mandatory", []))}
        2. 주인공: {mc_name} ({mc_desc})

        [세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.

        [집필 지침]:
        - 주인공 {mc_name}의 요리 성장과 식당 경영기를 중심으로 서사를 전개하라.
        - 요리 과정(식재료 선별/손질/조리/플레이팅)을 오감으로 구체적으로 묘사하라.
        - 식당 경영(인력/원가/고객/경쟁)의 메카닉스를 사실적으로 반영하라.
        - 선택된 '{tone_name}' 톤에 맞춰 요리의 감동과 성장의 쾌감을 극대화하라.
        - 현대 한국 배경이므로 배달앱, SNS, 미슐랭 등 현대 문물을 자연스럽게 사용 가능하다.
        - 요리를 글로 전달: 맛/향/질감의 감각적 묘사, 손님의 반응, 감정 전달에 집중하라.
        - 식자재 수급, 원가 관리, 인건비 등 식당 경영의 현실적 측면도 사실적으로 다뤄라.
        """
