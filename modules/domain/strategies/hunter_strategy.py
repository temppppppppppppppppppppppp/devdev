from .base_strategy import BaseStrategy


class HunterStrategy(BaseStrategy):
    @property
    def genre_name(self):
        return "HUNTER"

    def get_system_prompt(self) -> str:
        genre_rules = self.law.get("hunter", {})

        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        ctx = self.studio.project

        selected_tone = getattr(ctx, "selected_tone", {})
        tone_name = selected_tone.get("name", "일반 헌터물")
        tone_guide = selected_tone.get("writer", "긴박한 전투와 각성의 문체")

        # 2. 주인공 정보 인출
        bible_root = ctx.master_bible.get("MasterBible", ctx.master_bible)
        hud = bible_root.get("HunterHUD", bible_root.get("hunter_hud", {}))
        protagonist = hud.get("Protagonist", hud.get("main", {}))

        mc_name = protagonist.get("Name", protagonist.get("name", "각성자"))
        mc_desc = protagonist.get("description", "각성한 헌터")

        return f"""
        [HUNTER GENRE GUIDELINE]
        1. 장르 필수 요소: {", ".join(genre_rules.get("mandatory", []))}
        2. 주인공: {mc_name} ({mc_desc})

        [📜 세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.

        [집필 지침]:
        - 주인공 {mc_name}의 각성 능력과 성장 과정을 중심으로 서사를 전개하라.
        - 한글 전용 헌터물 문체를 유지하라. (한자 병기 금지)
        - 선택된 '{tone_name}' 톤에 맞춰 전투의 긴박감과 성장의 카타르시스를 극대화하라.
        - 던전, 길드, 랭크 시스템 등 헌터물 고유의 세계관 요소를 일관성 있게 표현하라.
        - 현대적 배경이므로 스마트폰, 인터넷 등의 현대 문물은 자연스럽게 사용 가능하다.
        """
