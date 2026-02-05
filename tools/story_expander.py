"""
Story Expander - 궁극의 스토리 확장 도구 (v2)
==============================================
대강의 컨셉 입력 → Bible + Treatment 자동 생성
+ 전략 어드바이저: 투자 추천, 실존 인물 타이밍, 로맨스 규칙

사용법:
    python tools/story_expander.py --output-dir "블록 연구소/new_project" --genre investment
"""

import json
import os
import sys
import io
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Windows UTF-8 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️ google-genai 패키지가 없습니다. pip install google-genai")


# ===========================================
# 전략 어드바이저 데이터베이스
# ===========================================

# 시대별 투자 전략 추천
INVESTMENT_STRATEGIES = {
    "1996": {
        "hot": [
            {"type": "외환 (USD)", "reason": "IMF 직전, 달러 급등 예정 (800→1700)", "timing": "1996-1997", "risk": "중", "return": "200%+"},
            {"type": "금", "reason": "위기 시 안전자산", "timing": "1997-1998", "risk": "저", "return": "50%+"},
            {"type": "공매도 (건설주)", "reason": "한보/삼미 부도 예정", "timing": "1996-1997", "risk": "고", "return": "300%+"},
        ],
        "avoid": ["부동산 (폭락 예정)", "종금사 (파산 예정)", "대기업 주식 (구조조정)"],
        "post_crisis": [
            {"type": "부동산 줍줍", "reason": "IMF 후 헐값 매물", "timing": "1998-1999", "risk": "중", "return": "500%+"},
            {"type": "우량주 바닥", "reason": "삼성전자 등 폭락 후 반등", "timing": "1998", "risk": "중", "return": "1000%+"},
            {"type": "코스닥 IT", "reason": "IT 버블 시작", "timing": "1999", "risk": "고", "return": "2000%+"},
        ]
    },
    "2007": {
        "hot": [
            {"type": "공매도 (금융주)", "reason": "서브프라임 위기 예정", "timing": "2007-2008", "risk": "극고", "return": "500%+"},
            {"type": "금", "reason": "안전자산 수요", "timing": "2008-2011", "risk": "저", "return": "200%+"},
            {"type": "USD", "reason": "위기 시 달러 강세", "timing": "2008", "risk": "중", "return": "30%+"},
        ],
        "avoid": ["부동산 (버블)", "금융주", "레버리지 상품"],
        "post_crisis": [
            {"type": "미국 기술주", "reason": "애플/아마존/구글 저점", "timing": "2009", "risk": "중", "return": "5000%+"},
            {"type": "비트코인", "reason": "2009년 탄생", "timing": "2009-2013", "risk": "극고", "return": "100000%+"},
        ]
    },
    "2019": {
        "hot": [
            {"type": "원격근무 관련주", "reason": "코로나 수혜", "timing": "2020", "risk": "중", "return": "500%+"},
            {"type": "바이오/백신", "reason": "팬데믹", "timing": "2020", "risk": "고", "return": "300%+"},
            {"type": "테슬라", "reason": "전기차 혁명", "timing": "2020", "risk": "고", "return": "1000%+"},
        ],
        "avoid": ["항공/여행/호텔", "오프라인 리테일"],
        "post_crisis": [
            {"type": "AI 관련주", "reason": "ChatGPT 등장 예정", "timing": "2022-2023", "risk": "고", "return": "500%+"},
            {"type": "엔비디아", "reason": "AI 칩 독점", "timing": "2023", "risk": "중", "return": "300%+"},
        ]
    }
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
        "마크 저커버그": {
            "peak_relevance": ["2004", "2012", "2021"],
            "story_hook": "2004년 페이스북 창업, 2012년 IPO, 2021년 메타",
            "meeting_scenario": "SNS 투자 / 메타버스 협력",
            "personality": "냉정, 데이터 중심, 어색한 인간관계",
            "what_they_want": "사용자 데이터, 연결성"
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
            "peak_relevance": ["1977-1990"],
            "story_hook": "마젤란펀드 전설, 연평균 29% 수익률",
            "meeting_scenario": "피델리티 방문 / 투자 강연",
            "personality": "일상에서 투자 아이디어, 직접 발로 뛰기",
            "what_they_want": "숨겨진 성장주, 10루타",
            "retirement": "1990년 은퇴"
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
            "death": "2020-10"
        },
        "정주영": {
            "peak_relevance": ["1970-1998"],
            "story_hook": "소 팔아 상경, 현대 건설/자동차/조선",
            "meeting_scenario": "현대 건설 현장 / 재계 행사",
            "personality": "불도저, 해보기나 했어?, 근성",
            "what_they_want": "도전정신, 불가능에 대한 집념",
            "death": "2001-03"
        },
        "김우중": {
            "peak_relevance": ["1980-1999"],
            "story_hook": "세계경영, 대우그룹 해체",
            "meeting_scenario": "대우 해외 진출 / 개도국 사업",
            "personality": "공격적 확장, 글로벌, 자신감",
            "what_they_want": "해외 시장, 대담한 비전",
            "warning": "1999년 몰락, 이후 도피"
        }
    }
}

# 로맨스 규칙
ROMANCE_RULES = {
    "protagonist": {
        "shows_interest": False,  # 주인공은 절대 호감 표현 안 함
        "accepts_advances": "냉담하게 또는 무관심하게",
        "priority": "사업/복수 > 로맨스",
        "typical_response": [
            "바쁘다는 핑계",
            "관심 없다는 듯한 태도",
            "사업 얘기로 화제 전환",
            "과거의 트라우마 암시"
        ]
    },
    "female_npcs": {
        "can_show_interest": True,
        "interest_triggers": [
            "주인공의 능력에 감탄",
            "주인공의 냉정함에 호기심",
            "위기에서 도움받음",
            "주인공의 숨겨진 면 발견"
        ],
        "archetypes": [
            {"type": "재벌가 영애", "trait": "도도하지만 주인공에게만 약함"},
            {"type": "능력있는 커리어우먼", "trait": "처음엔 라이벌, 점점 호감"},
            {"type": "첫사랑/전처", "trait": "과거 인연, 재회"},
            {"type": "비서/조력자", "trait": "가까이서 지켜보며 마음 생김"},
        ]
    },
    "tension_devices": [
        "히로인이 다가오지만 주인공은 회피",
        "다른 남자가 히로인에게 접근해도 주인공은 무관심",
        "히로인이 오해하고 삐침 → 주인공 모름",
        "위기 순간에만 본심이 살짝 비침"
    ]
}

# 역사 이벤트 DB (기존과 동일하지만 확장)
HISTORICAL_EVENTS_DB = {
    "1990s_korea": [
        {"month": "1996-01", "event": "OECD 가입", "impact": "외국인 투자 개방", "investment_tip": "외국인 선호주 매수"},
        {"month": "1996-04", "event": "한보그룹 부도 조짐", "impact": "건설주 약세", "investment_tip": "건설주 공매도"},
        {"month": "1997-01", "event": "한보철강 부도", "impact": "금융권 위기 시작", "investment_tip": "종금사 회피, 달러 매수"},
        {"month": "1997-03", "event": "삼미그룹 부도", "impact": "연쇄 부도 공포", "investment_tip": "안전자산 이동"},
        {"month": "1997-07", "event": "기아차 부도유예협약", "impact": "대기업 불안 확산", "investment_tip": "대기업주 회피"},
        {"month": "1997-10", "event": "홍콩 증시 폭락", "impact": "아시아 외환위기 본격화", "investment_tip": "달러 풀베팅"},
        {"month": "1997-11", "event": "IMF 구제금융 신청", "impact": "원화 폭락 (800→1700)", "investment_tip": "달러 매도 시점 탐색"},
        {"month": "1997-12", "event": "대통령 선거 (김대중)", "impact": "정권 교체", "investment_tip": "정책 수혜주 분석"},
        {"month": "1998-01", "event": "금 모으기 운동", "impact": "국민적 위기 극복", "investment_tip": "금 매수 후 장기 보유"},
        {"month": "1998-06", "event": "현대차 기아차 인수", "impact": "빅딜 시작", "investment_tip": "인수 대상 기업 저점 매수"},
        {"month": "1998-08", "event": "대우차 GM 매각 추진", "impact": "구조조정 본격화", "investment_tip": "우량기업 헐값 매수"},
        {"month": "1999-01", "event": "대우그룹 해체 시작", "impact": "역대급 부도", "investment_tip": "대우 계열 회피"},
        {"month": "1999-03", "event": "코스닥 열풍", "impact": "IT 버블 시작", "investment_tip": "IT주 단기 투자"},
        {"month": "1999-12", "event": "새천년 Y2K", "impact": "IT 투자 급증", "investment_tip": "IT 서비스 기업"},
    ],
    "2000s_global": [
        {"month": "2000-03", "event": "닷컴 버블 붕괴", "impact": "나스닥 폭락", "investment_tip": "기술주 공매도 후 저점 매수"},
        {"month": "2001-09", "event": "9.11 테러", "impact": "항공/보험 폭락, 방산 급등", "investment_tip": "방산주 매수"},
        {"month": "2003-03", "event": "이라크 전쟁", "impact": "유가 급등", "investment_tip": "에너지주, 원유 선물"},
        {"month": "2004-08", "event": "구글 IPO", "impact": "IT 부활 신호", "investment_tip": "구글 주식 장기 보유"},
        {"month": "2007-06", "event": "아이폰 출시", "impact": "스마트폰 혁명 시작", "investment_tip": "애플, 부품사 투자"},
        {"month": "2007-08", "event": "서브프라임 위기 시작", "impact": "금융주 약세", "investment_tip": "금융주 공매도"},
        {"month": "2008-09", "event": "리먼 브라더스 파산", "impact": "글로벌 금융위기", "investment_tip": "현금 확보, 바닥 대기"},
        {"month": "2009-03", "event": "미국 양적완화", "impact": "주식시장 바닥", "investment_tip": "미국 우량주 풀매수"},
        {"month": "2009-01", "event": "비트코인 탄생", "impact": "암호화폐 시작", "investment_tip": "비트코인 채굴/매수"},
    ],
    "2010s_tech": [
        {"month": "2010-04", "event": "아이패드 출시", "impact": "태블릿 시대", "investment_tip": "애플 생태계"},
        {"month": "2012-05", "event": "페이스북 IPO", "impact": "SNS 시대", "investment_tip": "SNS 광고 기업"},
        {"month": "2012-09", "event": "테슬라 모델S", "impact": "전기차 본격화", "investment_tip": "테슬라 장기 투자"},
        {"month": "2014-09", "event": "알리바바 IPO", "impact": "중국 IT 굴기", "investment_tip": "중국 플랫폼"},
        {"month": "2015-06", "event": "중국 주식 폭락", "impact": "차이나 쇼크", "investment_tip": "중국 회피"},
        {"month": "2017-12", "event": "비트코인 2만달러", "impact": "암호화폐 버블", "investment_tip": "고점 매도"},
        {"month": "2018-01", "event": "암호화폐 폭락", "impact": "코인 겨울", "investment_tip": "BTC 저점 매수"},
        {"month": "2019-12", "event": "코로나19 발생", "impact": "팬데믹 시작", "investment_tip": "원격/바이오 준비"},
    ],
    "2020s": [
        {"month": "2020-03", "event": "코로나 팬데믹 선언", "impact": "글로벌 폭락 후 급반등", "investment_tip": "폭락 시 풀매수"},
        {"month": "2020-11", "event": "화이자 백신 발표", "impact": "리오프닝 기대", "investment_tip": "여행/항공 저점 매수"},
        {"month": "2021-01", "event": "게임스탑 사태", "impact": "밈주식, 개미 혁명", "investment_tip": "밈주식 단타"},
        {"month": "2021-11", "event": "메타버스 선언", "impact": "메타 주가 고점", "investment_tip": "메타 고점 매도"},
        {"month": "2022-02", "event": "러시아 우크라이나 전쟁", "impact": "에너지/곡물 급등", "investment_tip": "원자재 투자"},
        {"month": "2022-11", "event": "ChatGPT 출시", "impact": "AI 혁명 시작", "investment_tip": "AI 관련주 풀매수"},
        {"month": "2023-03", "event": "SVB 파산", "impact": "은행 위기", "investment_tip": "은행주 단기 회피"},
        {"month": "2023-05", "event": "엔비디아 폭등", "impact": "AI 칩 독점", "investment_tip": "엔비디아 보유"},
    ]
}

# 실존 인물 데이터베이스 (NPC 생성용)
REAL_WORLD_FIGURES = {
    "investment": {
        "tech": [
            {"name": "스티브 잡스", "real": "Steve Jobs", "field": "IT/애플", "era": "1976-2011", "trait": "비전과 디자인 집착"},
            {"name": "빌 게이츠", "real": "Bill Gates", "field": "IT/MS", "era": "1975-현재", "trait": "독점 전략의 귀재"},
            {"name": "제프 베조스", "real": "Jeff Bezos", "field": "이커머스/아마존", "era": "1994-현재", "trait": "장기 투자, 고객 집착"},
            {"name": "일론 머스크", "real": "Elon Musk", "field": "전기차/우주", "era": "2002-현재", "trait": "미친 도전, 트위터 중독"},
            {"name": "마크 저커버그", "real": "Mark Zuckerberg", "field": "SNS/메타", "era": "2004-현재", "trait": "냉정한 확장주의"},
            {"name": "손정의", "real": "Masayoshi Son", "field": "투자/소프트뱅크", "era": "1981-현재", "trait": "비전펀드, 대담한 베팅"},
            {"name": "마윈", "real": "Jack Ma", "field": "이커머스/알리바바", "era": "1999-현재", "trait": "말빨, 서민 출신 성공"},
        ],
        "finance": [
            {"name": "워렌 버핏", "real": "Warren Buffett", "field": "가치투자", "era": "1956-현재", "trait": "장기 가치투자의 신"},
            {"name": "조지 소로스", "real": "George Soros", "field": "헤지펀드", "era": "1969-현재", "trait": "환투기, 영란은행 붕괴"},
            {"name": "레이 달리오", "real": "Ray Dalio", "field": "헤지펀드", "era": "1975-현재", "trait": "원칙주의, 올웨더"},
            {"name": "칼 아이칸", "real": "Carl Icahn", "field": "행동주의 투자", "era": "1968-현재", "trait": "기업 사냥꾼"},
            {"name": "피터 린치", "real": "Peter Lynch", "field": "펀드매니저", "era": "1977-1990", "trait": "마젤란펀드 전설"},
            {"name": "짐 로저스", "real": "Jim Rogers", "field": "상품투자", "era": "1973-현재", "trait": "퀀텀펀드 공동창업"},
        ],
        "korean_chaebol": [
            {"name": "이건희", "real": "삼성 회장", "field": "삼성그룹", "era": "1987-2020", "trait": "신경영, 반도체 1위"},
            {"name": "정주영", "real": "현대 창업주", "field": "현대그룹", "era": "1946-2001", "trait": "불도저, 소 팔아 상경"},
            {"name": "정몽구", "real": "현대차 회장", "field": "현대자동차", "era": "1999-현재", "trait": "품질경영"},
            {"name": "구본무", "real": "LG 회장", "field": "LG그룹", "era": "1995-2018", "trait": "정도경영"},
            {"name": "신격호", "real": "롯데 창업주", "field": "롯데그룹", "era": "1948-2020", "trait": "일본에서 시작"},
            {"name": "김우중", "real": "대우 창업주", "field": "대우그룹", "era": "1967-1999", "trait": "세계경영, IMF 몰락"},
        ],
        "global_business": [
            {"name": "리카싱", "real": "Li Ka-shing", "field": "부동산/항만", "era": "1950-현재", "trait": "아시아 최고 부자"},
            {"name": "루퍼트 머독", "real": "Rupert Murdoch", "field": "미디어", "era": "1952-현재", "trait": "미디어 제국"},
            {"name": "버나드 아르노", "real": "Bernard Arnault", "field": "명품/LVMH", "era": "1984-현재", "trait": "명품 제국의 황제"},
        ]
    }
}


class StrategicAdvisor:
    """전략 어드바이저 - 투자/인물/로맨스 추천"""

    def __init__(self, start_era: str):
        self.start_year = int(start_era[:4]) if start_era else 1996
        self.start_month = start_era

    def get_investment_recommendations(self, current_block: int, total_blocks: int = 60) -> dict:
        """현재 블록에 맞는 투자 전략 추천"""
        # 스토리 진행도
        progress = current_block / total_blocks

        # 시대 계산 (60블록 = 약 10년 가정)
        years_passed = int(progress * 10)
        current_year = str(self.start_year + years_passed)

        recommendations = {
            "current_phase": "",
            "hot_investments": [],
            "avoid": [],
            "upcoming_events": [],
            "advice": ""
        }

        # 시대별 전략 찾기
        base_strategies = None
        for year_key in sorted(INVESTMENT_STRATEGIES.keys(), reverse=True):
            if int(year_key) <= int(current_year):
                base_strategies = INVESTMENT_STRATEGIES[year_key]
                break

        if base_strategies:
            if progress < 0.3:
                recommendations["current_phase"] = "초기 자본 축적기"
                recommendations["hot_investments"] = base_strategies.get("hot", [])[:2]
                recommendations["advice"] = "위기 전 선제적 포지셔닝이 핵심입니다."
            elif progress < 0.5:
                recommendations["current_phase"] = "위기 활용기"
                recommendations["hot_investments"] = base_strategies.get("hot", [])
                recommendations["avoid"] = base_strategies.get("avoid", [])
                recommendations["advice"] = "남들이 공포에 떨 때가 기회입니다."
            elif progress < 0.7:
                recommendations["current_phase"] = "확장기"
                recommendations["hot_investments"] = base_strategies.get("post_crisis", [])[:2]
                recommendations["advice"] = "회복기에 우량 자산을 저점 매수합니다."
            else:
                recommendations["current_phase"] = "지배기"
                recommendations["hot_investments"] = base_strategies.get("post_crisis", [])
                recommendations["advice"] = "글로벌 확장과 다각화의 시기입니다."

        # 다가오는 이벤트
        for db_name, events in HISTORICAL_EVENTS_DB.items():
            for event in events:
                event_year = int(event["month"][:4])
                if self.start_year <= event_year <= self.start_year + years_passed + 2:
                    if event not in recommendations["upcoming_events"]:
                        recommendations["upcoming_events"].append(event)

        recommendations["upcoming_events"] = recommendations["upcoming_events"][:5]

        return recommendations

    def get_figure_recommendation(self, current_block: int, total_blocks: int = 60,
                                   used_figures: list = None) -> dict:
        """현재 블록에 등장시킬 실존 인물 추천"""
        used_figures = used_figures or []
        progress = current_block / total_blocks
        years_passed = int(progress * 10)
        current_year = str(self.start_year + years_passed)

        recommendations = []

        for category, figures in FIGURE_APPEARANCE_GUIDE.items():
            for name, info in figures.items():
                if name in used_figures:
                    continue

                # 사망 체크
                if info.get("death"):
                    death_year = int(info["death"][:4])
                    if int(current_year) > death_year:
                        continue

                # 은퇴 체크
                if info.get("retirement"):
                    retire_year = int(info["retirement"][:4])
                    if int(current_year) > retire_year + 5:
                        continue

                # 적절한 시기인지 체크
                relevance = info.get("peak_relevance", [])
                is_relevant = False

                for rel_year in relevance:
                    if rel_year == "always":
                        is_relevant = True
                        break
                    if abs(int(rel_year) - int(current_year)) <= 3:
                        is_relevant = True
                        break

                if is_relevant:
                    recommendations.append({
                        "name": name,
                        "category": category,
                        "story_hook": info.get("story_hook", ""),
                        "meeting_scenario": info.get("meeting_scenario", ""),
                        "personality": info.get("personality", ""),
                        "what_they_want": info.get("what_they_want", ""),
                        "warning": info.get("warning", None)
                    })

        # 블록 위치에 따른 우선순위
        if progress < 0.2:
            # 초반: 멘토 또는 한국 재벌
            priority_categories = ["korean_chaebol", "investors"]
        elif progress < 0.5:
            # 중반: 투자 거물
            priority_categories = ["investors", "korean_chaebol"]
        else:
            # 후반: 글로벌 테크
            priority_categories = ["tech_founders", "investors"]

        sorted_recommendations = sorted(
            recommendations,
            key=lambda x: priority_categories.index(x["category"]) if x["category"] in priority_categories else 99
        )

        return sorted_recommendations[:3]

    def get_romance_guidance(self, female_npc_type: str = None) -> dict:
        """로맨스 가이드라인"""
        guidance = {
            "protagonist_rule": ROMANCE_RULES["protagonist"],
            "female_interest_triggers": ROMANCE_RULES["female_npcs"]["interest_triggers"],
            "tension_devices": ROMANCE_RULES["tension_devices"],
            "recommended_archetype": None,
            "scene_suggestions": []
        }

        # 아키타입 추천
        if female_npc_type:
            for archetype in ROMANCE_RULES["female_npcs"]["archetypes"]:
                if archetype["type"] in female_npc_type:
                    guidance["recommended_archetype"] = archetype
                    break
        else:
            guidance["recommended_archetype"] = ROMANCE_RULES["female_npcs"]["archetypes"][0]

        # 씬 제안
        guidance["scene_suggestions"] = [
            "히로인이 호감 표시 → 주인공 '지금은 바쁘다'고 회피",
            "위기 상황에서 주인공이 히로인을 구함 → 하지만 별 말 없이 떠남",
            "다른 남자가 히로인에게 접근 → 주인공은 무관심하게 지나감 (독자 답답)",
            "술 취한 히로인이 본심 고백 → 주인공 못 들은 척 or 진짜 못 들음"
        ]

        return guidance

    def generate_block_advice(self, block_num: int, block_info: dict,
                               used_figures: list = None) -> dict:
        """블록별 종합 어드바이스"""
        investment_rec = self.get_investment_recommendations(block_num)
        figure_rec = self.get_figure_recommendation(block_num, used_figures=used_figures)
        romance_guide = self.get_romance_guidance()

        advice = {
            "block_num": block_num,
            "investment": investment_rec,
            "suggested_figures": figure_rec,
            "romance_reminder": {
                "rule": "주인공은 호감 표현 금지",
                "allowed": "여성 NPC가 주인공에게 호감 보이는 것은 OK"
            },
            "overall_tip": ""
        }

        # 종합 팁
        if block_num <= 5:
            advice["overall_tip"] = "초반부입니다. 주인공의 초기 설정과 동기를 확립하세요."
        elif block_num <= 15:
            advice["overall_tip"] = "성장기입니다. 첫 번째 큰 성공과 조력자 확보가 필요합니다."
        elif block_num <= 30:
            advice["overall_tip"] = "중반입니다. 실존 인물과의 첫 만남을 고려하세요."
        elif block_num <= 45:
            advice["overall_tip"] = "도약기입니다. 대형 투자와 글로벌 확장의 시기입니다."
        else:
            advice["overall_tip"] = "클라이맥스입니다. 최종 목표 달성을 향해 가세요."

        return advice


class StoryExpander:
    """스토리 확장기 - 컨셉 → Bible + Treatment"""

    def __init__(self, output_dir: str, genre: str = "investment"):
        self.output_dir = Path(output_dir)
        self.genre = genre
        self.concept = ""
        self.extracted = {}
        self.bible = {}
        self.treatment = []
        self.advisor = None
        self.used_figures = []

        if GENAI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.client = genai.Client(api_key=api_key)
                self.model = "gemini-2.5-flash"
            else:
                self.client = None
                print("⚠️ GOOGLE_API_KEY 없음")
        else:
            self.client = None

    def _call_llm(self, prompt: str, temperature: float = 0.85, max_tokens: int = 8192) -> str:
        """LLM 호출"""
        if not self.client:
            return None
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            return response.text
        except Exception as e:
            print(f"❌ LLM 오류: {e}")
            return None

    def _parse_json(self, text: str) -> Any:
        """JSON 파싱"""
        if not text:
            return None
        try:
            json_str = text
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            return json.loads(json_str.strip())
        except:
            return None

    # ===========================================
    # Phase 0: 컨셉 입력 및 분석
    # ===========================================

    def phase0_input_concept(self) -> str:
        """컨셉 입력"""
        print("\n" + "="*60)
        print("🎯 Phase 0: 스토리 컨셉 입력")
        print("="*60)

        print("""
대강의 스토리 컨셉을 자유롭게 입력하세요.
예시:
  - 재벌 3세가 비참하게 죽고 회귀, IMF 직전으로 돌아와서...
  - 무명 트레이더가 2008년 금융위기를 예측해서...

[여러 줄 입력 가능. 빈 줄 입력 시 완료]
""")

        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)

        self.concept = "\n".join(lines)
        print(f"\n📝 입력된 컨셉 ({len(self.concept)}자)")
        return self.concept

    def phase0_analyze_concept(self) -> dict:
        """컨셉 분석"""
        print("\n🤖 컨셉 분석 중...")

        prompt = f"""다음 스토리 컨셉을 분석해서 핵심 요소를 추출하세요.

## 컨셉
{self.concept}

## 추출할 요소 (JSON)
```json
{{
  "title_suggestions": ["제목 후보1", "제목 후보2", "제목 후보3"],

  "protagonist": {{
    "background": "출신/배경",
    "death_cause": "사망 원인 (있으면)",
    "regression_point": "회귀 시점",
    "starting_condition": "시작 상태",
    "unique_edge": "주인공만의 강점",
    "main_goal": "최종 목표",
    "personality_hints": "성격"
  }},

  "timeline": {{
    "start_era": "시작 시대 (예: 1996-01)",
    "key_historical_events": ["활용할 역사 이벤트"],
    "story_span_years": "예상 스토리 기간 (년)"
  }},

  "major_plot_points": ["주요 플롯 포인트"],

  "power_progression": {{
    "initial": "초기 상태",
    "mid": "중반 상태",
    "final": "최종 상태"
  }},

  "suggested_antagonists": [{{"type": "유형", "desc": "설명"}}],
  "themes": ["테마"],
  "tone": "작품 톤"
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        self.extracted = self._parse_json(response) or {}

        if self.extracted:
            print("\n✅ 컨셉 분석 완료")
            timeline = self.extracted.get("timeline", {})
            start_era = timeline.get("start_era", "1996-01")

            # 어드바이저 초기화
            self.advisor = StrategicAdvisor(start_era)

            # 투자 전략 추천 표시
            print("\n" + "-"*40)
            print("💡 전략 어드바이저 추천")
            print("-"*40)

            inv_rec = self.advisor.get_investment_recommendations(1)
            print(f"\n📈 {start_era[:4]}년 시작 추천 투자:")
            for inv in inv_rec.get("hot_investments", [])[:3]:
                print(f"  ✓ {inv['type']}: {inv['reason']}")
                print(f"    → 예상 수익: {inv['return']}, 리스크: {inv['risk']}")

            print(f"\n⚠️ 회피 추천:")
            for avoid in inv_rec.get("avoid", [])[:3]:
                print(f"  ✗ {avoid}")

            print(f"\n🎯 어드바이스: {inv_rec.get('advice', '')}")

        return self.extracted

    # ===========================================
    # Phase 1: Bible 생성
    # ===========================================

    def phase1_generate_bible(self) -> dict:
        """Bible 생성"""
        print("\n" + "="*60)
        print("📖 Phase 1: Bible 생성")
        print("="*60)

        meta_info = self._generate_meta_info()
        protagonist = self._generate_protagonist_detail()
        commercial = self._generate_commercial_code()
        hud = self._generate_initial_hud(protagonist)
        npcs = self._generate_npcs_with_advisor()  # 어드바이저 활용
        world_state = self._generate_world_state()
        events = self._select_historical_events()
        rules = self._generate_genre_rules()
        seeds = self._generate_seeds(npcs)

        self.bible = {
            "_schema_version": "2.0",
            "_generated_from": "story_expander_v2",
            "_last_updated": datetime.now().strftime("%Y-%m-%d"),

            "MasterBible": {
                "ProjectData": {
                    "MetaInfo": meta_info,
                    "CoreIdentity": protagonist["core"],
                    "CommercialCode": commercial
                },
                "protagonist_config": protagonist["config"],
                "FinanceHUD": hud,
                "WorldState": world_state,
                "AssetLibrary": {
                    "KeyNPCs": npcs,
                    "KeyItems": self._generate_key_items(),
                    "KeyLocations": self._generate_key_locations(),
                    "Persona": protagonist.get("persona", ""),
                    "SpeechStyle": protagonist.get("speech", {})
                },
                "Seeds": seeds,
                "HistoricalEvents": {
                    "_description": "활용 가능한 역사 이벤트",
                    "events": events
                },
                "GenreRules": rules,
                "RomanceRules": ROMANCE_RULES  # 로맨스 규칙 추가
            }
        }

        return self.bible

    def _generate_meta_info(self) -> dict:
        """메타 정보 생성"""
        print("\n  📋 메타 정보 생성 중...")

        titles = self.extracted.get("title_suggestions", ["무제"])
        print(f"\n  제목 후보:")
        for i, t in enumerate(titles, 1):
            print(f"    [{i}] {t}")
        print(f"    [0] 직접 입력")

        choice = input("  선택: ").strip()
        if choice == "0":
            title = input("  제목: ").strip()
        elif choice.isdigit() and 1 <= int(choice) <= len(titles):
            title = titles[int(choice) - 1]
        else:
            title = titles[0]

        timeline = self.extracted.get("timeline", {})
        protagonist = self.extracted.get("protagonist", {})

        return {
            "title": title,
            "grand_objective": protagonist.get("main_goal", ""),
            "genre_archetype": f"investment + 회귀물 + {self.extracted.get('tone', '복수극')}",
            "logline": f"{protagonist.get('background', '주인공')}이(가) {timeline.get('start_era', '과거')}로 회귀하여 {protagonist.get('main_goal', '성공')}하는 이야기",
            "total_episodes": 200,
            "episodes_per_arc": 5,
            "arcs_per_volume": 5
        }

    def _generate_protagonist_detail(self) -> dict:
        """주인공 상세"""
        print("\n  🦸 주인공 상세 생성 중...")

        proto = self.extracted.get("protagonist", {})

        prompt = f"""주인공 상세 설정을 생성하세요.

## 기본 정보
{json.dumps(proto, ensure_ascii=False, indent=2)}

## 중요 규칙
- 주인공은 로맨스에 관심 없음
- 여성에게 호감을 표현하지 않음
- 냉철하고 목표 지향적

## 출력 (JSON)
```json
{{
  "name": "한국식 이름",
  "age": 나이,
  "core": {{
    "protagonist": "이름",
    "protagonist_faction": "소속 변화",
    "edge": "핵심 강점",
    "desire": "욕망",
    "crisis": "초기 위기"
  }},
  "config": {{
    "world_origin": "현대인",
    "incarnation_type": "회귀자",
    "regression_point": {{
      "death_year": 2024,
      "death_cause": "사망 원인",
      "return_year": 1996,
      "return_month": "1996-01"
    }}
  }},
  "persona": "말투/성격",
  "speech": {{
    "tone": "말투",
    "vocabulary": "어휘",
    "inner_monologue": "내면 독백"
  }},
  "romance_attitude": "로맨스에 무관심, 사업이 우선"
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        result = self._parse_json(response) or {}

        name = result.get("name", "김현우")
        print(f"\n  주인공 이름: {name}")
        new_name = input("  [Enter] 승인 / 새 이름: ").strip()
        if new_name:
            result["name"] = new_name
            if "core" in result:
                result["core"]["protagonist"] = new_name

        return result

    def _generate_commercial_code(self) -> dict:
        """상업적 코드"""
        print("\n  💰 상업적 코드 생성 중...")

        proto = self.extracted.get("protagonist", {})

        prompt = f"""웹소설 상업적 코드를 생성하세요.

주인공 강점: {proto.get('unique_edge', '')}
톤: {self.extracted.get('tone', '')}

JSON:
```json
{{
  "cider_point": "통쾌함 포인트",
  "success_device": "성공의 증거",
  "attitude": "주인공 태도"
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        return self._parse_json(response) or {}

    def _generate_initial_hud(self, protagonist: dict) -> dict:
        """초기 HUD"""
        print("\n  📊 HUD 초기화 중...")

        proto = self.extracted.get("protagonist", {})
        timeline = self.extracted.get("timeline", {})

        prompt = f"""투자물 HUD를 생성하세요.

시작 상태: {proto.get('starting_condition', '')}
시작 시점: {timeline.get('start_era', '1996-01')}

JSON:
```json
{{
  "Protagonist": {{
    "actual_truth": {{
      "name": "{protagonist.get('name', '주인공')}",
      "alias": "없음",
      "age": {protagonist.get('age', 28)},
      "rank": "초기 직위",
      "financial_status": {{
        "total_assets": "총 자산",
        "liquid_cash": "현금",
        "stocks": [],
        "real_estate": [],
        "foreign_currency": {{"USD": 0, "JPY": 0}},
        "debt": "부채"
      }},
      "portfolio_history": [
        {{"episode": 0, "month": "{timeline.get('start_era', '1996-01')}", "total_assets": "초기자산", "event": "시작점"}}
      ],
      "investment_style": "투자 스타일",
      "risk_tolerance": "리스크 성향",
      "network_level": {{"financial_sector": 0, "political_sector": 0, "business_sector": 0}},
      "current_objective": "당장 목표",
      "final_goal": "최종 목표"
    }},
    "public_reputation": {{
      "identity": "외부 신분",
      "wealth_level": "부유층/중산층/빈곤층"
    }}
  }}
}}
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        return self._parse_json(response) or {}

    def _generate_npcs_with_advisor(self) -> list:
        """NPC 생성 (어드바이저 활용)"""
        print("\n  👥 NPC 생성 중 (어드바이저 추천 활용)...")

        # 어드바이저로부터 추천 인물 받기
        figure_recs = self.advisor.get_figure_recommendation(1, used_figures=[])
        romance_guide = self.advisor.get_romance_guidance()

        print("\n  💡 어드바이저 추천 실존 인물:")
        for i, fig in enumerate(figure_recs[:5], 1):
            print(f"    [{i}] {fig['name']}: {fig['story_hook'][:50]}...")

        # 로맨스 가이드라인 표시
        print("\n  💕 로맨스 규칙:")
        print(f"    - 주인공: 호감 표현 금지")
        print(f"    - 여성 NPC: 주인공에게 호감 표현 가능")
        print(f"    - 추천 아키타입: {romance_guide['recommended_archetype']}")

        # NPC 생성 프롬프트
        antagonists = self.extracted.get("suggested_antagonists", [])
        proto = self.extracted.get("protagonist", {})

        prompt = f"""웹소설 NPC를 15명 생성하세요.

## 주인공 정보
- 배경: {proto.get('background', '')}
- 목표: {proto.get('main_goal', '')}

## 예상 적대자
{json.dumps(antagonists, ensure_ascii=False)}

## 추천 실존 인물 (최소 5명 포함)
{json.dumps(figure_recs, ensure_ascii=False, indent=2)}

## 로맨스 규칙 (필수 준수)
- 주인공은 절대 여성에게 호감을 표현하지 않음
- 여성 NPC는 주인공에게 호감을 보일 수 있음
- 주인공의 반응: "바쁘다", "관심 없다", "사업이 먼저"

## 여성 NPC 아키타입 (2-3명 필수)
1. 재벌가 영애 - 도도하지만 주인공에게만 약함
2. 능력있는 커리어우먼 - 처음엔 라이벌, 점점 호감
3. 비서/조력자 - 가까이서 지켜보며 마음 생김

## 필수 역할 (15명)
1. 메인 빌런 (1-2명) - 가문 내부 또는 라이벌
2. 서브 빌런 (2-3명) - 아크별 장애물
3. 조력자 (2-3명) - 비서, 부하
4. 히로인 (2-3명) - 위 아키타입 참고
5. 멘토/귀인 (1-2명) - 실존 인물 모티브 권장
6. 업계 거물 (3-4명) - 실존 인물 모티브 필수

## 출력 (JSON)
```json
[
  {{
    "name": "이름",
    "role": "역할",
    "desc": "설명",
    "real_motif": "실존 모티브" 또는 null,
    "gender": "남/여",
    "romantic_interest_in_protagonist": true/false,
    "protagonist_interest_in_them": false,
    "NPC_Finance_HUD": {{
      "current_assets": "자산",
      "position": "직위",
      "weakness": "약점",
      "status": "활동중"
    }},
    "appearance_timing": "초반/중반/후반",
    "arc_involvement": [1, 2, 3]
  }},
  ...
]
```

15명 모두 출력. JSON만 출력하세요.
"""
        response = self._call_llm(prompt, max_tokens=16000)
        npcs = self._parse_json(response) or []

        # 검증
        real_count = sum(1 for n in npcs if n.get("real_motif"))
        female_interested = sum(1 for n in npcs if n.get("romantic_interest_in_protagonist"))
        protag_interested = sum(1 for n in npcs if n.get("protagonist_interest_in_them"))

        print(f"\n  생성된 NPC: {len(npcs)}명")
        print(f"  실존 모티브: {real_count}명 ({real_count/max(len(npcs),1)*100:.0f}%)")
        print(f"  주인공에게 호감: {female_interested}명")
        print(f"  주인공이 호감: {protag_interested}명 (규칙상 0이어야 함)")

        if protag_interested > 0:
            print("  ⚠️ 규칙 위반: 주인공이 호감 표현하는 NPC가 있습니다. 수정합니다.")
            for npc in npcs:
                npc["protagonist_interest_in_them"] = False

        # 목록 표시
        print("\n  NPC 목록:")
        for i, npc in enumerate(npcs, 1):
            motif = f" [{npc.get('real_motif')}]" if npc.get('real_motif') else ""
            gender = npc.get('gender', '?')
            interest = " ♥→주인공" if npc.get('romantic_interest_in_protagonist') else ""
            print(f"    [{i:2d}] {npc['name']} ({npc['role']}, {gender}){motif}{interest}")

        # 사용된 실존 인물 기록
        for npc in npcs:
            if npc.get("real_motif"):
                self.used_figures.append(npc["real_motif"])

        return npcs

    def _generate_world_state(self) -> dict:
        """세계 상태"""
        timeline = self.extracted.get("timeline", {})
        return {
            "CurrentEra": timeline.get("start_era", "1996-01"),
            "CurrentLocation": "서울",
            "economic_context": {
                "description": f"{timeline.get('start_era', '1996')[:4]}년 경제 상황"
            },
            "KarmaMatrix": {}
        }

    def _select_historical_events(self) -> list:
        """역사 이벤트 선택"""
        print("\n  📅 역사 이벤트 매칭 중...")

        timeline = self.extracted.get("timeline", {})
        start_era = timeline.get("start_era", "1996-01")

        selected = []
        for db_name, events in HISTORICAL_EVENTS_DB.items():
            for event in events:
                if event["month"] >= start_era:
                    selected.append(event)

        # 투자 팁 표시
        print(f"\n  📈 투자 기회 이벤트:")
        for e in selected[:8]:
            tip = e.get("investment_tip", "")
            if tip:
                print(f"    {e['month']}: {e['event']}")
                print(f"      💡 {tip}")

        return selected

    def _generate_genre_rules(self) -> dict:
        """장르 규칙"""
        return {
            "must_include": [
                "자본 변화가 명확히 추적되어야 함",
                "투자 논리가 설득력 있어야 함",
                "리스크와 보상의 균형"
            ],
            "forbidden": [
                "비현실적 수익률",
                "주인공이 여성에게 먼저 호감 표현",
                "경제 상식에 어긋나는 전개"
            ],
            "tension_devices": [
                "투자 실패 위기",
                "적대자의 역공",
                "히로인이 다가오지만 주인공은 회피"
            ]
        }

    def _generate_seeds(self, npcs: list) -> list:
        """복선 씨앗"""
        print("\n  🌱 복선 씨앗 생성 중...")

        prompt = f"""복선 씨앗 8개를 생성하세요.

컨셉: {self.concept[:300]}
NPC: {[n['name'] for n in npcs[:10]]}

JSON:
```json
[
  {{"id": "S-001", "category": "인물|사건|아이템", "description": "복선", "planted_ep": 1, "target_harvest_ep": 30, "status": "active"}}
]
```

JSON만 출력하세요.
"""
        response = self._call_llm(prompt)
        return self._parse_json(response) or []

    def _generate_key_items(self) -> list:
        """주요 아이템"""
        prompt = f"""투자물 주요 아이템 5개:

JSON: [{{"item": "이름", "desc": "설명"}}]
"""
        response = self._call_llm(prompt, temperature=0.7, max_tokens=1000)
        return self._parse_json(response) or []

    def _generate_key_locations(self) -> list:
        """주요 장소"""
        return [
            {"name": "여의도 증권가", "desc": "금융의 심장"},
            {"name": "강남 오피스", "desc": "주인공의 거점"},
            {"name": "월스트리트", "desc": "글로벌 확장 무대"}
        ]

    # ===========================================
    # Phase 2: Treatment 생성 (어드바이저 활용)
    # ===========================================

    def phase2_generate_treatment(self) -> list:
        """Treatment 생성"""
        print("\n" + "="*60)
        print("📝 Phase 2: Treatment 생성 (60 블록)")
        print("="*60)

        skeleton = self._generate_treatment_skeleton_with_advisor()
        detailed = self._generate_treatment_details_with_advisor(skeleton)
        self.treatment = self._extract_treatment_metadata(detailed)

        return self.treatment

    def _generate_treatment_skeleton_with_advisor(self) -> list:
        """뼈대 생성 (어드바이저 추천 포함)"""
        print("\n  📋 60블록 뼈대 생성 중 (어드바이저 추천 활용)...")

        # Arc별 어드바이저 추천 수집
        arc_recommendations = []
        for arc in range(1, 11):
            block_num = (arc - 1) * 6 + 1
            inv_rec = self.advisor.get_investment_recommendations(block_num)
            fig_rec = self.advisor.get_figure_recommendation(block_num, used_figures=self.used_figures)

            arc_recommendations.append({
                "arc": arc,
                "blocks": f"{(arc-1)*6+1}-{arc*6}",
                "phase": inv_rec.get("current_phase", ""),
                "hot_investments": [i["type"] for i in inv_rec.get("hot_investments", [])[:2]],
                "suggested_figures": [f["name"] for f in fig_rec[:2]],
                "advice": inv_rec.get("advice", "")
            })

        print("\n  💡 Arc별 어드바이저 추천:")
        for rec in arc_recommendations:
            print(f"\n    Arc {rec['arc']} ({rec['blocks']}): {rec['phase']}")
            if rec['hot_investments']:
                print(f"      📈 추천 투자: {', '.join(rec['hot_investments'])}")
            if rec['suggested_figures']:
                print(f"      👤 등장 추천: {', '.join(rec['suggested_figures'])}")

        # 뼈대 생성
        events = self.bible.get("MasterBible", {}).get("HistoricalEvents", {}).get("events", [])[:15]
        npcs = self.bible.get("MasterBible", {}).get("AssetLibrary", {}).get("KeyNPCs", [])[:10]

        prompt = f"""60개 블록 뼈대를 생성하세요.

## 컨셉
{self.concept}

## Arc별 어드바이저 추천 (반드시 반영)
{json.dumps(arc_recommendations, ensure_ascii=False, indent=2)}

## 활용 가능한 역사 이벤트
{json.dumps([e['month'] + ': ' + e['event'] for e in events], ensure_ascii=False)}

## 주요 NPC
{json.dumps([n['name'] + ' (' + n['role'] + ')' for n in npcs], ensure_ascii=False)}

## 로맨스 규칙
- 여성 NPC가 주인공에게 다가와도 주인공은 냉담하게 반응
- 주인공이 먼저 호감 표현하는 장면 금지

## 출력 (JSON)
```json
[
  {{"block_id": "Block 1", "title": "제목", "summary": "요약", "arc": 1, "investment_focus": "투자 유형", "npcs": ["NPC"]}},
  ...
]
```

60개 블록 모두 출력. JSON만 출력하세요.
"""
        response = self._call_llm(prompt, max_tokens=20000, temperature=0.9)
        skeleton = self._parse_json(response) or []

        print(f"\n  생성된 블록: {len(skeleton)}개")

        return skeleton

    def _generate_treatment_details_with_advisor(self, skeleton: list) -> list:
        """상세 생성 (블록별 어드바이저 조언)"""
        print("\n  📖 상세 content 생성 중...")

        detailed = []
        batch_size = 5

        for batch_idx in range(0, len(skeleton), batch_size):
            batch = skeleton[batch_idx:batch_idx + batch_size]
            start_block = batch_idx + 1

            print(f"\n    Batch: Block {start_block}-{start_block + len(batch) - 1}")

            # 배치 첫 블록에 대한 어드바이저 조언
            advice = self.advisor.generate_block_advice(start_block, {}, self.used_figures)

            print(f"      💡 {advice['overall_tip']}")
            if advice['suggested_figures']:
                print(f"      👤 등장 추천: {advice['suggested_figures'][0]['name']}")

            # 이전 블록 요약
            prev_summary = ""
            if detailed:
                prev_summary = "\n".join([
                    f"- {b['block_id']}: {b.get('content', {}).get('reward', '')[:30]}"
                    for b in detailed[-3:]
                ])

            skeleton_text = "\n".join([
                f"- {b['block_id']}: {b['title']} - {b['summary']}"
                for b in batch
            ])

            romance_reminder = """
## 로맨스 규칙 (필수)
- 여성이 주인공에게 호감 표시 → 주인공은 "바쁘다", "지금은 일이 먼저" 등으로 회피
- 주인공이 여성에게 호감 표현하는 장면 절대 금지
"""

            prompt = f"""블록 상세를 생성하세요.

## 이전 블록
{prev_summary if prev_summary else "(첫 배치)"}

## 이번 블록
{skeleton_text}

## 어드바이저 조언
{advice['overall_tip']}

{romance_reminder}

## 출력 (JSON)
```json
[
  {{
    "block_id": "Block {start_block}",
    "title": "제목",
    "content": {{
      "context": "배경 (200-300자)",
      "event_villain": "빌런/장애물 (200-300자)",
      "solution": "해결 (200-300자)",
      "reward": "결과 (100-200자)"
    }}
  }}
]
```

JSON만 출력하세요.
"""
            response = self._call_llm(prompt, temperature=0.85)
            batch_result = self._parse_json(response) or []

            if batch_result:
                detailed.extend(batch_result)
            else:
                for b in batch:
                    detailed.append({
                        "block_id": b["block_id"],
                        "title": b["title"],
                        "content": {"context": b["summary"], "event_villain": "", "solution": "", "reward": ""}
                    })

        return detailed

    def _extract_treatment_metadata(self, blocks: list) -> list:
        """메타데이터 추출"""
        print("\n  🔧 메타데이터 추출 중...")

        enriched = []
        prev_capital = "시작 자산"

        for i, block in enumerate(blocks):
            if i % 10 == 0:
                print(f"    {i+1}/{len(blocks)}")

            content = block.get("content", {})

            prompt = f"""메타데이터 추출:

Block: {block['block_id']}
Content: {json.dumps(content, ensure_ascii=False)[:500]}
이전 자본: {prev_capital}

JSON:
```json
{{
  "stakes": "위험",
  "tension_level": 7,
  "genre_ext": {{
    "capital_before": "{prev_capital}",
    "capital_after": "변화 후",
    "capital_delta": "+/-금액",
    "investment_type": "유형"
  }}
}}
```

JSON만 출력하세요.
"""
            response = self._call_llm(prompt, temperature=0.3, max_tokens=1000)
            metadata = self._parse_json(response) or {}

            if metadata.get("genre_ext", {}).get("capital_after"):
                prev_capital = metadata["genre_ext"]["capital_after"]

            enriched.append({
                "block_id": block["block_id"],
                "title": block["title"],
                "content": block["content"],
                **metadata
            })

        return enriched

    # ===========================================
    # Phase 3: 저장
    # ===========================================

    def phase3_save(self):
        """저장"""
        print("\n" + "="*60)
        print("💾 Phase 3: 저장")
        print("="*60)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Bible
        bible_path = self.output_dir / "bible.json"
        with open(bible_path, 'w', encoding='utf-8') as f:
            json.dump(self.bible, f, ensure_ascii=False, indent=2)
        print(f"\n  ✅ Bible: {bible_path}")

        # Treatment
        treatment_output = {
            "_schema_version": "2.0",
            "_bible_ref": "bible.json",
            "work_name": self.bible.get("MasterBible", {}).get("ProjectData", {}).get("MetaInfo", {}).get("title", ""),
            "total_blocks": len(self.treatment),
            "treatments": self.treatment
        }

        treatment_path = self.output_dir / "treatment.json"
        with open(treatment_path, 'w', encoding='utf-8') as f:
            json.dump(treatment_output, f, ensure_ascii=False, indent=2)
        print(f"  ✅ Treatment: {treatment_path}")

        # 요약
        summary = {
            "title": self.bible.get("MasterBible", {}).get("ProjectData", {}).get("MetaInfo", {}).get("title", ""),
            "concept": self.concept[:500],
            "npc_count": len(self.bible.get("MasterBible", {}).get("AssetLibrary", {}).get("KeyNPCs", [])),
            "real_figures_used": self.used_figures,
            "block_count": len(self.treatment),
            "generated_at": datetime.now().isoformat()
        }

        summary_path = self.output_dir / "summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"  ✅ Summary: {summary_path}")

    # ===========================================
    # 메인 실행
    # ===========================================

    def run(self):
        """전체 파이프라인"""
        print("\n" + "="*60)
        print("🚀 Story Expander v2 - 전략 어드바이저 탑재")
        print("="*60)

        self.phase0_input_concept()
        self.phase0_analyze_concept()
        self.phase1_generate_bible()
        self.phase2_generate_treatment()
        self.phase3_save()

        print("\n" + "="*60)
        print("🎉 완료!")
        print("="*60)
        print(f"\n출력: {self.output_dir}")
        print(f"  - bible.json")
        print(f"  - treatment.json")
        print(f"  - summary.json")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Story Expander v2")
    parser.add_argument("--output-dir", default="블록 연구소/expanded_project")
    parser.add_argument("--genre", default="investment", choices=["investment", "wuxia", "hunter"])

    args = parser.parse_args()

    expander = StoryExpander(output_dir=args.output_dir, genre=args.genre)
    expander.run()


if __name__ == "__main__":
    main()
