import re

class Cleaner:
    def __init__(self, studio_system):
        self.studio = studio_system
        
    def polish(self, raw_text):
        print("   🧹 [Cleaner] 가독성 최적화 및 줄바꿈 정돈 중...")
        
        # 1. 불필요한 소제목 및 메타데이터([...]) 제거
        # (앞선 작업 결과를 이어받기 위해 변수를 'text'로 유지)
        text = re.sub(r'\[.*?\]', '', raw_text)
        
        # 2. 한자 제거 및 괄호 제거
        # (반드시 앞서 가공된 'text'를 입력값으로 사용해야 함)
        text = re.sub(r'[\u4e00-\u9fff]|\(|\)', '', text)
        
        # 3. 줄바꿈 정돈 (2행 간격 표준화)
        symbol = self.studio.law.get('common', {}).get('system_standard', {}).get('scene_transition', '%%%%')
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        result_lines = []
        for line in lines:
            if line == symbol:
                result_lines.append(f"\n{symbol}\n")
            else:
                result_lines.append(line)
        
        return "\n\n".join(result_lines).strip()

    def remove_hanja(self, text):
        """한자 및 괄호만 제거하는 유틸리티 메서드"""
        return re.sub(r'[\u4e00-\u9fff]|\(|\)', '', text)