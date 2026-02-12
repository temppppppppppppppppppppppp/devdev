from .base_strategy import BaseStrategy

class WuxiaStrategy(BaseStrategy):
    @property
    def genre_name(self): return "WUXIA"

    def get_system_prompt(self) -> str:
        genre_rules = self.law.get('wuxia', {})
        
        # 1. 컨텍스트 및 선택된 톤(Tone) 인출
        # [수정] context_manager -> project 로 변경
        ctx = self.studio.project 
        
        selected_tone = getattr(ctx, 'selected_tone', {}) 
        tone_name = selected_tone.get('name', '일반 무협')
        tone_guide = selected_tone.get('writer', '긴박한 호흡의 문체') 

        # 2. 주인공 정보 인출 (ProjectContext 구조에 맞춰 수정)
        # [수정] get_mc_name() 대신 master_bible에서 직접 접근
        bible_root = ctx.master_bible.get('MasterBible', ctx.master_bible)
        hud = bible_root.get('MartialHUD', bible_root.get('martial_hud', {}))
        protagonist = hud.get('Protagonist', hud.get('main', {}))
        
        mc_name = protagonist.get('Name', protagonist.get('name', '주인공'))
        # [수정] ctx.bible -> ctx.master_bible, 경로 수정
        mc_desc = protagonist.get('description', '강호를 유람하는 무인')
        
        return f"""
        [WUXIA GENRE GUIDELINE]
        1. 장르 필수 요소: {', '.join(genre_rules.get('mandatory', []))}
        2. 주인공: {mc_name} ({mc_desc})
        
        [📜 세부 집필 톤(Tone) 지침: {tone_name}]
        - {tone_guide}를 최우선 문체 원칙으로 삼는다.
        
        [집필 지침]: 
        - 주인공 {mc_name}의 신분과 성격에 최적화된 서사와 대사를 구사하라.
        - 한글 전용 무협 문체를 유지하라. (한자 병기 금지)
        - 선택된 '{tone_name}' 톤에 맞춰 어휘의 밀도와 비장미를 조절하라.
        """