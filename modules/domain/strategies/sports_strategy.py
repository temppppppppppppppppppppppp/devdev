from .base_strategy import BaseStrategy


class SportsStrategy(BaseStrategy):
    @property
    def genre_name(self):
        return "SPORTS"

    def get_system_prompt(self) -> str:
        genre_rules = self.law.get("sports", {})

        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        ctx = self.studio.project

        selected_tone = getattr(ctx, "selected_tone", {})
        tone_name = selected_tone.get("name", "스포츠 성장물")
        tone_guide = selected_tone.get("writer", "스포츠의 열정과 성장통이 교차하는 문체")

        # 2. 주인공 정보 인출
        bible_root = ctx.master_bible.get("MasterBible", ctx.master_bible)
        hud = bible_root.get("SportsHUD", bible_root.get("sports_hud", {}))
        protagonist = hud.get("Protagonist", hud.get("main", {}))

        mc_name = protagonist.get("Name", protagonist.get("name", "선수"))
        mc_desc = protagonist.get("description", "무한한 잠재력의 선수")

        return f"""
        [SPORTS GENRE GUIDELINE]
        1. 장르 필수 요소: {", ".join(genre_rules.get("mandatory", []))}
        2. 주인공: {mc_name} ({mc_desc})

        [세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.

        [집필 지침]:
        - 주인공 {mc_name}의 선수 성장과 팀 스포츠 여정을 중심으로 서사를 전개하라.
        - 경기 장면을 역동적으로 묘사하라: 속도감, 신체 감각, 관중 분위기, 전술 해석.
        - 훈련/재활 과정(체력훈련/기술연습/전술분석/부상재활)을 리얼리즘으로 구체적으로 묘사하라.
        - 스포츠 산업(이적/연봉/스폰서/미디어/팬덤)의 메카닉스를 사실적으로 반영하라.
        - 선택된 '{tone_name}' 톤에 맞춰 승부의 쾌감과 좌절의 고통을 극대화하라.
        - 현대 한국 배경이므로 SNS, 유튜브, OTT 중계 등 현대 문물을 자연스럽게 사용 가능하다.
        - 팀 역학(동료/라이벌/감독/코치)의 인간적 갈등과 유대를 입체적으로 그려라.
        """
