from .base_strategy import BaseStrategy

class InvestmentStrategy(BaseStrategy):
    @property
    def genre_name(self): return "INVESTMENT"

    def get_system_prompt(self):
        genre_rules = self.law.get('investment', {})
        
        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        ctx = self.studio.project 
        
        selected_tone = getattr(ctx, 'selected_tone', {}) 
        tone_name = selected_tone.get('name', '일반 투자물')
        tone_guide = selected_tone.get('writer', '긴장감 넘치는 금융 전쟁의 문체') 

        # 2. 주인공 정보 인출
        bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)
        hud = bible_root.get('FinanceHUD', bible_root.get('finance_hud', {}))
        protagonist = hud.get('Protagonist', hud.get('main', {}))
        
        mc_name = protagonist.get('Name', protagonist.get('name', '투자자'))
        mc_desc = protagonist.get('description', '야심찬 투자자')
        
        return f"""
        [INVESTMENT GENRE GUIDELINE]
        1. 장르 필수 요소: {', '.join(genre_rules.get('mandatory', []))}
        2. 주인공: {mc_name} ({mc_desc})
        
        [📜 세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.
        
        [집필 지침]: 
        - 주인공 {mc_name}의 투자 전략과 자본 증식 과정을 중심으로 서사를 전개하라.
        - 한글 전용 투자물 문체를 유지하라. (한자 병기 금지)
        - 선택된 '{tone_name}' 톤에 맞춰 금융 전쟁의 긴장감과 승리의 쾌감을 극대화하라.
        - 주식, 부동산, M&A 등 투자물 고유의 전문 용어를 정확하고 설득력 있게 사용하라.
        - 시장의 논리와 경제 상식에 기반한 개연성 있는 투자 전략을 묘사하라.
        - 현대적 배경이므로 금융 시스템, 뉴스, SNS 등의 현대 문물은 자연스럽게 사용 가능하다.
        """
