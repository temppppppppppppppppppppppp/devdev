"""
[V40 Multi-Genre] 장르별 Guard의 공통 기능을 제공하는 추상 클래스
"""

import re
from abc import ABC, abstractmethod

class BaseGuard(ABC):
    """장르 독립적 Guard 추상 인터페이스"""
    
    def __init__(self):
        self.FORBIDDEN_TERMS = []
        self.ALLOWED_TERMS = []
        self.MANDATORY_CONCEPTS = []
    
    @abstractmethod
    def get_genre_name(self):
        """장르 이름 반환"""
        pass
    
    def convert_to_numeric(self, text):
        """한글/한자 수사를 숫자로 변환 (무협 전용이지만 공통으로 제공)"""
        if not text or not isinstance(text, (str, int, float)): return 0.0
        if isinstance(text, (int, float)): return float(text)

        clean_text = text.replace(" ", "")

        # 1. [V40.1 Critical Fix] 제로 가드 - 정확한 매칭으로 변경
        # "0"을 부분 문자열로 체크하면 "80", "5.0" 등이 모두 0이 됨!
        zero_keywords = ["영", "무", "없음", "소멸"]
        if any(keyword in clean_text for keyword in zero_keywords):
            return 0.0
        # 정확히 "0" 또는 "0.0"인 경우만 체크 (아라비아 숫자 추출 전에)
        if clean_text in ["0", "0.0", "0.", ".0"]:
            return 0.0

        # 2. 단위 멀티플라이어 (갑자 대응)
        unit_multiplier = 1.0
        if "갑자" in clean_text:
            unit_multiplier = 60.0
        
        # 3. 아라비아 숫자 우선 처리
        digit_match = re.search(r'([0-9\.]+)', clean_text)
        if digit_match:
            try:
                val = float(digit_match.group(1)) * unit_multiplier
                if '반' in clean_text: val += (30.0 if "갑자" in clean_text else 0.5)
                return val
            except: pass

        # 4. 한글 수사 정밀 파싱
        num_map = {'일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9}
        total = 0.0
        
        if '십' in clean_text:
            idx = clean_text.find('십')
            prefix = clean_text[idx-1] if idx > 0 else None
            total += (num_map.get(prefix, 1) * 10)
            if idx + 1 < len(clean_text):
                suffix = clean_text[idx+1]
                total += num_map.get(suffix, 0)
        else:
            for char, val in num_map.items():
                if char in clean_text:
                    total = float(val)
                    break

        # 5. '반' 처리
        if '반' in clean_text:
            total += 0.5

        # 6. 최종 산출
        final_val = (total if total > 0 else 1.0) * unit_multiplier
        return float(final_val)
    
    def validate_v20_manuscript(self, content):
        """원고 검증 (장르별 커스터마이징 가능)"""
        issues = []
        
        # 1. 괄호 검출 (한자 예외 처리)
        parentheses_matches = re.findall(r'\((.*?)\)', content)
        for inside in parentheses_matches:
            if re.search(r'[^\u4e00-\u9fff]', inside):
                issues.append(f"장르 부적격 괄호 설명 발견: ({inside})")

        # 2. 알파벳(영어) 노출 절대 금지 (장르에 따라 완화 가능)
        if self._should_check_english():
            if re.search(r'[a-zA-Z]', content):
                english_words = re.findall(r'[a-zA-Z]+', content)
                issues.append(f"외국어(영어) 노출: {', '.join(english_words[:3])}...")

        # 3. 금기어 검사
        for term in self.FORBIDDEN_TERMS:
            if term in content:
                issues.append(f"장르 파괴 금기어 발견: '{term}'")

        # 4. 숫자(아라비아 숫자) 미변환 검사 (장르에 따라 완화 가능)
        if self._should_check_numbers():
            if re.search(r'\d+', content):
                numbers = re.findall(r'\d+', content)
                issues.append(f"미변환 숫자 발견: {', '.join(numbers[:5])}...")

        return {
            "is_pure": len(issues) == 0,
            "issues": issues
        }
    
    @abstractmethod
    def get_v20_purism_prompt(self):
        """장르별 순혈주의 프롬프트 생성"""
        pass
    
    def _should_check_english(self):
        """영어 검증 여부 (장르별 오버라이드 가능)"""
        return True
    
    def _should_check_numbers(self):
        """숫자 검증 여부 (장르별 오버라이드 가능)"""
        return True
