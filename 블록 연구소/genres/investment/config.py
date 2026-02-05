"""
Investment Genre - 설정 파일
============================
투자 전략, 로맨스 규칙, 장르 규칙, NPC 역할
"""

# 시대별 투자 전략
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

# 로맨스 규칙
ROMANCE_RULES = {
    "protagonist": {
        "shows_interest": False,
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

# 장르 규칙
GENRE_RULES = {
    "must_include": [
        "자본 변화가 명확히 추적되어야 함",
        "투자 논리가 설득력 있어야 함 (미래지식만으로 X)",
        "리스크와 보상의 균형",
        "적대자도 합리적인 판단을 해야 함"
    ],
    "forbidden": [
        "말도 안 되는 수익률 (1000배 등이 너무 쉽게)",
        "법적 문제 무시 (내부자거래 등 합리화 필요)",
        "경제 상식에 어긋나는 전개",
        "주인공이 여성에게 먼저 호감 표현"
    ],
    "tension_devices": [
        "투자 실패 위기",
        "미래 지식이 틀릴 뻔한 순간",
        "적대자의 역공",
        "신원 노출 위기",
        "조력자의 배신 가능성"
    ]
}

# 필수 NPC 역할
NPC_ROLES = [
    {"role": "메인 빌런", "count": "1-2명", "desc": "가문 내부 또는 라이벌 재벌"},
    {"role": "서브 빌런", "count": "2-3명", "desc": "각 아크별 장애물"},
    {"role": "조력자", "count": "2-3명", "desc": "비서, 부하, 동료"},
    {"role": "히로인", "count": "2-3명", "desc": "주인공에게 호감, 주인공은 무관심"},
    {"role": "멘토/귀인", "count": "1-2명", "desc": "실존 인물 모티브 권장"},
    {"role": "업계 거물", "count": "3-4명", "desc": "실존 인물 모티브 필수"}
]

# 성장 곡선 템플릿
POWER_PROGRESSION = {
    "initial": {
        "phase": "바닥",
        "capital_range": "0 ~ 1억",
        "network": "없음",
        "reputation": "무명",
        "blocks": "1-10"
    },
    "early": {
        "phase": "종잣돈 확보",
        "capital_range": "1억 ~ 100억",
        "network": "업계 입문",
        "reputation": "떠오르는 신예",
        "blocks": "11-20"
    },
    "mid": {
        "phase": "도약",
        "capital_range": "100억 ~ 1000억",
        "network": "업계 인정",
        "reputation": "젊은 거물",
        "blocks": "21-35"
    },
    "late": {
        "phase": "지배",
        "capital_range": "1000억 ~ 조 단위",
        "network": "정재계 인맥",
        "reputation": "업계 전설",
        "blocks": "36-50"
    },
    "final": {
        "phase": "정점",
        "capital_range": "수조 ~ 글로벌",
        "network": "세계적 네트워크",
        "reputation": "역사에 남을 인물",
        "blocks": "51-60"
    }
}
