from .base_strategy import BaseStrategy


class MedicalStrategy(BaseStrategy):
    @property
    def genre_name(self): return "MEDICAL"

    def get_system_prompt(self):
        genre_rules = self.law.get('medical', {})

        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        ctx = self.studio.project

        selected_tone = getattr(ctx, 'selected_tone', {})
        tone_name = selected_tone.get('name', '의학 성장물')
        tone_guide = selected_tone.get('writer', '생사의 긴장감과 의사의 성장이 교차하는 문체')

        # 2. 주인공 정보 인출
        bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)
        hud = bible_root.get('MedicalHUD', bible_root.get('medical_hud', {}))
        protagonist = hud.get('Protagonist', hud.get('main', {}))

        mc_name = protagonist.get('Name', protagonist.get('name', '의사'))
        mc_desc = protagonist.get('description', '천재적 의술의 의사')

        return f"""
        [MEDICAL GENRE GUIDELINE]
        1. 장르 필수 요소: {', '.join(genre_rules.get('mandatory', []))}
        2. 주인공: {mc_name} ({mc_desc})

        [세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.

        [집필 지침]:
        - 주인공 {mc_name}의 의사 성장과 병원 내 여정을 중심으로 서사를 전개하라.
        - 수술 장면을 긴장감 넘치게 묘사하라: 바이탈 수치, 메스의 촉감, 출혈, 시간 압박.
        - 진단 과정(문진/검사/판독/컨퍼런스)을 의학적 정확성으로 묘사하라.
        - 병원 정치(과장경쟁/수련의갈등/교수임용/인수합병)의 메카닉스를 사실적으로 반영하라.
        - 선택된 '{tone_name}' 톤에 맞춰 생명을 다루는 무게감과 의사의 성장을 극대화하라.
        - 현대 대학병원 배경이므로 원격진료, AI 진단, 로봇수술 등 현대 의학을 자연스럽게 사용 가능하다.
        - 환자-의사 관계, 의료 윤리, 번아웃 등 의사의 인간적 고뇌를 입체적으로 그려라.
        """
