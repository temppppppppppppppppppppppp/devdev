from .base_strategy import BaseStrategy


class ComposerStrategy(BaseStrategy):
    @property
    def genre_name(self):
        return "COMPOSER"

    def get_system_prompt(self) -> str:
        genre_rules = self.law.get("composer", {})

        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        ctx = self.studio.project

        selected_tone = getattr(ctx, "selected_tone", {})
        tone_name = selected_tone.get("name", "음악 전문가물")
        tone_guide = selected_tone.get("writer", "음악의 감동과 업계의 냉혹함이 교차하는 문체")

        # 2. 주인공 정보 인출
        bible_root = ctx.master_bible.get("MasterBible", ctx.master_bible)
        hud = bible_root.get("ComposerHUD", bible_root.get("composer_hud", {}))
        protagonist = hud.get("Protagonist", hud.get("main", {}))

        mc_name = protagonist.get("Name", protagonist.get("name", "작곡가"))
        mc_desc = protagonist.get("description", "천재적 음악 감각의 작곡가")

        return f"""
        [COMPOSER GENRE GUIDELINE]
        1. 장르 필수 요소: {", ".join(genre_rules.get("mandatory", []))}
        2. 주인공: {mc_name} ({mc_desc})

        [📜 세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.

        [집필 지침]:
        - 주인공 {mc_name}의 음악적 성장과 업계 생존기를 중심으로 서사를 전개하라.
        - 음악 창작 과정(작곡/편곡/프로듀싱)을 구체적이고 감각적으로 묘사하라.
        - 음악 업계(기획사, 차트, 시상식, 저작권)의 메카닉스를 사실적으로 반영하라.
        - 선택된 '{tone_name}' 톤에 맞춰 창작의 고뇌와 성공의 쾌감을 극대화하라.
        - 현대 한국 배경이므로 K-POP, 스트리밍, SNS 등 현대 문물을 자연스럽게 사용 가능하다.
        - 음악을 글로 전달: 멜로디/리듬의 감각적 묘사, 청중의 반응, 감정 전달에 집중하라.
        - 저작권, 계약, 수익 분배 등 음악 산업의 현실적 측면도 사실적으로 다뤄라.
        """
