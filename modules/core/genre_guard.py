import re

class GenreGuard:
    """[V30 Sovereign Purism] 무협의 순혈성을 보존하고 괄호 내 불순물 및 현대어를 차단하는 최종 파수꾼"""

    # V30 확장 금기어 목록 (게임, 현대 행정, 물리학 용어 통합)
    FORBIDDEN_TERMS = [
        "상태창", "시스템", "로그", "퀘스트", "스킬", "마나", "서클", "스테이터스", 
        "레벨업", "경험치", "아이템 파밍", "레이드", "던전", "포션", "귀환 주문서", 
        "데이터", "바이러스", "현대적 비속어", "영어 직역투", "MARTIAL HUD", "스마트폰", "모세의 기적",
        "분자", "원자", "세포", "DNA", "유전자", "물리학", "화학", "중력", "가속도", 
        "산소", "탄소", "미생물", "트라우마", "스트레스", "메커니즘", "프로세스", "인터페이스",
        "에너지", "벡터", "중력장", "운동 에너지", "진공", "시멘트", "저작권", "저작권 침해", "중력","입자",
        "포탄", "쓰나미", "물류", "비자금", "투자", "청구서", "질량","엔진","계산기","펌프질","전송","임계점","폼",
        "로직","계산기","제로","0.1초","브리핑","데이터","3차원","45도","90도","중력","타깃","매커니즘","경동맥","근섬유",
        "포커스","브랜드","1초"
    ]

    # V20 필수 묘사 권장 사항
    MANDATORY_CONCEPTS = [
        "진기(眞氣)와 내공의 운용", "초식(招式)의 형상화", "강호의 은원(恩怨)", "항렬과 예법"
    ]


    def convert_to_numeric(self, text) -> float:
        if not text or not isinstance(text, (str, int, float)): return 0.0
        if isinstance(text, (int, float)): return float(text)

        clean_text = text.replace(" ", "")
        
        # 1. 🛡️ 제로 가드 (Zero-Guard)
        if any(z in clean_text for z in ["영", "무", "없", "소멸", "0"]):
            return 0.0

        # 2. 🎡 단위 멀티플라이어 (갑자 대응)
        unit_multiplier = 1.0
        if "갑자" in clean_text:
            unit_multiplier = 60.0
        
        # 3. 🔢 아라비아 숫자 우선 처리 (예: "1.5 갑자")
        digit_match = re.search(r'([0-9\.]+)', clean_text)
        if digit_match:
            try:
                val = float(digit_match.group(1)) * unit_multiplier
                if '반' in clean_text: val += (30.0 if "갑자" in clean_text else 0.5)
                return val
            except (ValueError, TypeError): pass

        # 4. 🧠 한글 수사 정밀 파싱 (십진법 대응)
        # 0124 매니페스토: "이십"은 12가 아니라 20이다.
        num_map = {'일': 1, '이': 2, '삼': 3, '사': 4, '오': 5, '육': 6, '칠': 7, '팔': 8, '구': 9}
        total = 0.0
        
        if '십' in clean_text:
            idx = clean_text.find('십')
            # '십' 앞의 숫자 처리 (예: '이'십 -> 2 * 10)
            prefix = clean_text[idx-1] if idx > 0 else None
            total += (num_map.get(prefix, 1) * 10)
            # '십' 뒤의 숫자 처리 (예: 십'오' -> 10 + 5)
            if idx + 1 < len(clean_text):
                suffix = clean_text[idx+1]
                total += num_map.get(suffix, 0)
        else:
            # 단일 수사 (일, 이, 삼...)
            for char, val in num_map.items():
                if char in clean_text:
                    total = float(val)
                    break

        # 5. 🌗 '반' 처리 (한글 모드)
        if '반' in clean_text:
            total += 0.5

        # 6. 🏁 최종 산출
        # "갑자" 단독 입력 시 total이 0이므로 기본값 1.0 부여
        final_val = (total if total > 0 else 1.0) * unit_multiplier
        return float(final_val)
    


    def validate_v20_manuscript(self, content: str) -> dict:
        """[Stage 4] 원고 내 금기어, 숫자 표기, 괄호 부연 설명 정밀 검수"""
        issues = []
        
        # 1. 괄호 검출 및 한자 예외 처리 로직 (V30.1 하드닝 패치)
        # 모든 괄호를 찾은 뒤, 그 안의 내용이 '순수 한자'가 아니면 즉시 검출합니다.
        parentheses_matches = re.findall(r'\((.*?)\)', content)
        for inside in parentheses_matches:
            # 한자 범위(\u4e00-\u9fff) 이외의 글자(영어, 숫자, 특수문자, 공백 등)가 포함되어 있는지 확인
            # 한자가 섞여 있더라도 영어/숫자가 하나라도 있으면 차단합니다.
            if re.search(r'[^\u4e00-\u9fff]', inside):
                issues.append(f"장르 부적격 괄호 설명 발견: ({inside})")

        # 2. 알파벳(영어) 노출 절대 금지 (괄호 밖 영어도 차단)
        if re.search(r'[a-zA-Z]', content):
            english_words = re.findall(r'[a-zA-Z]+', content)
            issues.append(f"외국어(영어) 노출: {', '.join(english_words[:3])}...")

        awkward_units = re.findall(r'(일|이|삼|사|오|육|칠|팔|구|십)\s*달', content)
        if awkward_units:
            for unit in awkward_units:
                issues.append(f"수사-단위 불일치 발견: '{unit} 달' -> '일 월(一月)' 또는 '한 달'로 수정 요망")

        # 3. 금기어 검사 (확장된 FORBIDDEN_TERMS 기준)
        for term in self.FORBIDDEN_TERMS:
            if term in content:
                issues.append(f"장르 파괴 금기어 발견: '{term}'")

        # 4. 숫자(아라비아 숫자) 미변환 검사
        # V20/V30 표준: 원고 내 모든 수치는 한글로 표기해야 함 (예: 100근 -> 일백 근)
        if re.search(r'\d+', content):
            numbers = re.findall(r'\d+', content)
            issues.append(f"미변환 숫자 발견: {', '.join(numbers[:5])}...")

        return {
            "is_pure": len(issues) == 0,
            "issues": issues
        }

    def get_v20_purism_prompt(self) -> str:
        """에이전트들에게 주입할 순혈주의 지침 프롬프트 생성"""
        return f"""
[🛡️ V30 무협 순혈주의 절대 준수 (Purism Enforcement)]

1. **괄호 부연 설명 절대 금지**: 단어 옆에 (Anchor), (10cm), (100근) 등 괄호를 써서 영어/수치를 보충하는 행위를 엄금한다. 한자 표기용 괄호만 허용한다.
2. **과학/현대 용어 절대 금지**: 현대 과학/물리 지식을 무협적 개념으로 '번역'하여 서술하라.
   - 분자/원자/세포/질량 → 미진(微塵), 근원(根源), 기(氣)의 입자, 무게
   - 중력/압력/에너지 → 천근추(千斤墜), 태산 같은 기세, 공압(空壓), 기운
   - 투자/물류/비자금 → 밑천, 보급/운송, 사재(私財)/뒷돈
3. **게임 시스템 용어 금지**: {', '.join(self.FORBIDDEN_TERMS[:10])} 등 상태창류 단어를 쓰면 즉시 파기한다.
4. **수치 표기**: 모든 숫자(거리, 무게, 인원, 날짜 등)는 반드시 '한글'로만 표기하라. (예: 100근 X -> 일백 근 O)
5. **언어 순혈주의**: 영어, 외래어, 현대적 비속어는 금지한다. 오직 정통 무협의 어휘만 허용한다.
"""