"""
Investment Figures - 실존 인물 데이터베이스
==========================================
테크 거물, 투자 거장, 한국 재벌, 글로벌 비즈니스
"""

# 실존 인물 데이터베이스 (NPC 생성용)
REAL_FIGURES = {
    "tech": [
        {"name": "스티브 잡스", "real": "Steve Jobs", "field": "IT/애플", "era": "1976-2011", "trait": "비전과 디자인 집착"},
        {"name": "빌 게이츠", "real": "Bill Gates", "field": "IT/MS", "era": "1975-현재", "trait": "독점 전략의 귀재"},
        {"name": "제프 베조스", "real": "Jeff Bezos", "field": "이커머스/아마존", "era": "1994-현재", "trait": "장기 투자, 고객 집착"},
        {"name": "일론 머스크", "real": "Elon Musk", "field": "전기차/우주", "era": "2002-현재", "trait": "미친 도전, 트위터 중독"},
        {"name": "마크 저커버그", "real": "Mark Zuckerberg", "field": "SNS/메타", "era": "2004-현재", "trait": "냉정한 확장주의"},
        {"name": "손정의", "real": "Masayoshi Son", "field": "투자/소프트뱅크", "era": "1981-현재", "trait": "비전펀드, 대담한 베팅"},
        {"name": "마윈", "real": "Jack Ma", "field": "이커머스/알리바바", "era": "1999-현재", "trait": "말빨, 서민 출신 성공"},
        {"name": "래리 페이지", "real": "Larry Page", "field": "검색/구글", "era": "1998-현재", "trait": "기술 중심, 문샷 프로젝트"},
        {"name": "세르게이 브린", "real": "Sergey Brin", "field": "검색/구글", "era": "1998-현재", "trait": "알고리즘 천재"},
        {"name": "젠슨 황", "real": "Jensen Huang", "field": "반도체/엔비디아", "era": "1993-현재", "trait": "AI 혁명의 핵심"},
    ],
    "finance": [
        {"name": "워렌 버핏", "real": "Warren Buffett", "field": "가치투자", "era": "1956-현재", "trait": "장기 가치투자의 신"},
        {"name": "조지 소로스", "real": "George Soros", "field": "헤지펀드", "era": "1969-현재", "trait": "환투기, 영란은행 붕괴"},
        {"name": "레이 달리오", "real": "Ray Dalio", "field": "헤지펀드", "era": "1975-현재", "trait": "원칙주의, 올웨더"},
        {"name": "칼 아이칸", "real": "Carl Icahn", "field": "행동주의 투자", "era": "1968-현재", "trait": "기업 사냥꾼"},
        {"name": "피터 린치", "real": "Peter Lynch", "field": "펀드매니저", "era": "1977-1990", "trait": "마젤란펀드 전설"},
        {"name": "짐 로저스", "real": "Jim Rogers", "field": "상품투자", "era": "1973-현재", "trait": "퀀텀펀드 공동창업"},
        {"name": "존 폴슨", "real": "John Paulson", "field": "헤지펀드", "era": "1994-현재", "trait": "서브프라임 공매도로 전설"},
        {"name": "마이클 버리", "real": "Michael Burry", "field": "가치투자", "era": "2000-현재", "trait": "빅쇼트의 주인공"},
    ],
    "korean_chaebol": [
        {"name": "이건희", "real": "삼성 회장", "field": "삼성그룹", "era": "1987-2020", "trait": "신경영, 반도체 1위"},
        {"name": "정주영", "real": "현대 창업주", "field": "현대그룹", "era": "1946-2001", "trait": "불도저, 소 팔아 상경"},
        {"name": "정몽구", "real": "현대차 회장", "field": "현대자동차", "era": "1999-현재", "trait": "품질경영"},
        {"name": "구본무", "real": "LG 회장", "field": "LG그룹", "era": "1995-2018", "trait": "정도경영"},
        {"name": "신격호", "real": "롯데 창업주", "field": "롯데그룹", "era": "1948-2020", "trait": "일본에서 시작"},
        {"name": "김우중", "real": "대우 창업주", "field": "대우그룹", "era": "1967-1999", "trait": "세계경영, IMF 몰락"},
        {"name": "최종현", "real": "SK 회장", "field": "SK그룹", "era": "1973-1998", "trait": "석유화학에서 통신으로"},
        {"name": "조중훈", "real": "한진 창업주", "field": "한진그룹", "era": "1945-2002", "trait": "항공/물류 제국"},
    ],
    "global_business": [
        {"name": "리카싱", "real": "Li Ka-shing", "field": "부동산/항만", "era": "1950-현재", "trait": "아시아 최고 부자"},
        {"name": "루퍼트 머독", "real": "Rupert Murdoch", "field": "미디어", "era": "1952-현재", "trait": "미디어 제국"},
        {"name": "버나드 아르노", "real": "Bernard Arnault", "field": "명품/LVMH", "era": "1984-현재", "trait": "명품 제국의 황제"},
        {"name": "앤디 그로브", "real": "Andy Grove", "field": "반도체/인텔", "era": "1968-2016", "trait": "편집광만이 살아남는다"},
        {"name": "잭 웰치", "real": "Jack Welch", "field": "복합기업/GE", "era": "1981-2001", "trait": "경영의 신, 구조조정의 달인"},
    ]
}

# 실존 인물 등장 타이밍 가이드
FIGURE_APPEARANCE_GUIDE = {
    "tech_founders": {
        "스티브 잡스": {
            "peak_relevance": ["1997", "2001", "2007", "2010"],
            "story_hook": "1997년 애플 복귀, 2001년 아이팟, 2007년 아이폰",
            "meeting_scenario": "실리콘밸리 투자 미팅 / 애플 투자자 행사",
            "personality": "비전에 집착, 무례할 정도로 직설적, 디자인 광",
            "what_they_want": "혁신적인 아이디어, 디자인 감각 있는 파트너",
            "signature_line": "Stay hungry, stay foolish",
            "death": "2011-10"
        },
        "빌 게이츠": {
            "peak_relevance": ["1995", "2000", "2008"],
            "story_hook": "1995년 윈도우95, 2000년 MS 정점, 이후 자선사업",
            "meeting_scenario": "MS 파트너십 / 다보스 포럼",
            "personality": "분석적, 경쟁적, 독서광",
            "what_they_want": "기술적 우위, 시장 지배력"
        },
        "제프 베조스": {
            "peak_relevance": ["1997", "2005", "2015", "2020"],
            "story_hook": "1997년 아마존 IPO, 2005년 AWS, 2015년 1위 부자",
            "meeting_scenario": "이커머스 투자 / 우주 사업 협력",
            "personality": "장기적 사고, 고객 집착, 웃음소리 특이",
            "what_they_want": "혁신적인 물류/기술 솔루션"
        },
        "일론 머스크": {
            "peak_relevance": ["2008", "2013", "2020", "2022"],
            "story_hook": "2008년 테슬라 위기, 2013년 성공, 2020년 폭등, 2022년 트위터",
            "meeting_scenario": "전기차/우주 투자 / 트위터에서 DM",
            "personality": "미친 도전, 트위터 중독, 밈 좋아함, 수면 부족",
            "what_they_want": "화성 이주, 지속가능 에너지, 관심"
        },
        "손정의": {
            "peak_relevance": ["1996", "2000", "2017"],
            "story_hook": "1996년 야후 투자, 2000년 알리바바, 2017년 비전펀드",
            "meeting_scenario": "아시아 투자 파트너십 / 소프트뱅크 미팅",
            "personality": "300년 비전, 대담한 베팅, 감정적",
            "what_they_want": "AI와 미래 기술, 야심찬 창업자"
        },
        "마윈": {
            "peak_relevance": ["1999", "2014", "2019"],
            "story_hook": "1999년 알리바바, 2014년 IPO, 2019년 은퇴",
            "meeting_scenario": "중국 이커머스 진출 / 항저우 방문",
            "personality": "말빨, 영어 교사 출신, 서민적",
            "what_they_want": "중국 시장 파트너, 글로벌 확장",
            "warning": "2020년 이후 중국 정부와 마찰"
        }
    },
    "investors": {
        "워렌 버핏": {
            "peak_relevance": ["always"],
            "story_hook": "오마하의 현인, 버크셔 해서웨이",
            "meeting_scenario": "버크셔 주주총회 / 오마하 방문",
            "personality": "검소, 장기투자, 유머러스, 체리콕 마시며 신문 읽기",
            "what_they_want": "좋은 경영진, 해자가 있는 기업, 적정 가격",
            "signature_line": "다른 사람들이 탐욕스러울 때 두려워하고, 두려워할 때 탐욕스러워라"
        },
        "조지 소로스": {
            "peak_relevance": ["1992", "1997", "2008"],
            "story_hook": "1992년 영란은행 격파, 1997년 아시아 외환위기",
            "meeting_scenario": "헤지펀드 서밋 / 환투기 협력",
            "personality": "철학적, 반성적, 공격적 투자",
            "what_they_want": "시장의 불균형, 레버리지 기회",
            "warning": "한국에서는 악역 이미지"
        },
        "레이 달리오": {
            "peak_relevance": ["2008", "2017"],
            "story_hook": "2008년 금융위기 예측, 원칙(Principles) 저자",
            "meeting_scenario": "브릿지워터 방문 / 원칙 세미나",
            "personality": "원칙주의, 급진적 투명성, 명상",
            "what_they_want": "아이디어 다툼, 원칙에 기반한 의사결정"
        },
        "피터 린치": {
            "peak_relevance": ["1977", "1985", "1990"],
            "story_hook": "마젤란펀드 전설, 연평균 29% 수익률",
            "meeting_scenario": "피델리티 방문 / 투자 강연",
            "personality": "일상에서 투자 아이디어, 직접 발로 뛰기",
            "what_they_want": "숨겨진 성장주, 10루타",
            "retirement": "1990"
        },
        "칼 아이칸": {
            "peak_relevance": ["1985", "2000", "2013"],
            "story_hook": "기업 사냥꾼, 행동주의 투자",
            "meeting_scenario": "적대적 인수 협력 / 주주 행동주의",
            "personality": "공격적, 집요함, 두려움을 모름",
            "what_they_want": "저평가된 기업, 무능한 경영진"
        }
    },
    "korean_chaebol": {
        "이건희": {
            "peak_relevance": ["1993", "1997", "2010"],
            "story_hook": "1993년 신경영, 삼성전자 반도체 1위",
            "meeting_scenario": "삼성 협력사 미팅 / 재계 행사",
            "personality": "과묵, 결단력, 새벽형",
            "what_they_want": "기술력, 글로벌 경쟁력",
            "signature_line": "마누라와 자식 빼고 다 바꿔라",
            "death": "2020-10"
        },
        "정주영": {
            "peak_relevance": ["1970", "1985", "1998"],
            "story_hook": "소 팔아 상경, 현대 건설/자동차/조선",
            "meeting_scenario": "현대 건설 현장 / 재계 행사",
            "personality": "불도저, 해보기나 했어?, 근성",
            "what_they_want": "도전정신, 불가능에 대한 집념",
            "signature_line": "이봐, 해봤어?",
            "death": "2001-03"
        },
        "김우중": {
            "peak_relevance": ["1980", "1990", "1999"],
            "story_hook": "세계경영, 대우그룹 해체",
            "meeting_scenario": "대우 해외 진출 / 개도국 사업",
            "personality": "공격적 확장, 글로벌, 자신감",
            "what_they_want": "해외 시장, 대담한 비전",
            "warning": "1999년 몰락, 이후 도피"
        }
    }
}
