"""
Investment Events - 역사 이벤트 데이터베이스
============================================
1990년대 한국, 2000년대 글로벌, 2010년대 테크, 2020년대
"""

HISTORICAL_EVENTS = {
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
        {"month": "2009-01", "event": "비트코인 탄생", "impact": "암호화폐 시작", "investment_tip": "비트코인 채굴/매수"},
        {"month": "2009-03", "event": "미국 양적완화", "impact": "주식시장 바닥", "investment_tip": "미국 우량주 풀매수"},
    ],
    "2010s_tech": [
        {"month": "2010-04", "event": "아이패드 출시", "impact": "태블릿 시대", "investment_tip": "애플 생태계"},
        {"month": "2012-05", "event": "페이스북 IPO", "impact": "SNS 시대", "investment_tip": "SNS 광고 기업"},
        {"month": "2012-09", "event": "테슬라 모델S", "impact": "전기차 본격화", "investment_tip": "테슬라 장기 투자"},
        {"month": "2014-09", "event": "알리바바 IPO", "impact": "중국 IT 굴기", "investment_tip": "중국 플랫폼"},
        {"month": "2015-06", "event": "중국 주식 폭락", "impact": "차이나 쇼크", "investment_tip": "중국 회피"},
        {"month": "2016-06", "event": "브렉시트", "impact": "유럽 불확실성", "investment_tip": "파운드 공매도"},
        {"month": "2017-12", "event": "비트코인 2만달러", "impact": "암호화폐 버블", "investment_tip": "고점 매도"},
        {"month": "2018-01", "event": "암호화폐 폭락", "impact": "코인 겨울", "investment_tip": "BTC 저점 매수"},
        {"month": "2019-12", "event": "코로나19 발생", "impact": "팬데믹 시작", "investment_tip": "원격/바이오 준비"},
    ],
    "2020s": [
        {"month": "2020-03", "event": "코로나 팬데믹 선언", "impact": "글로벌 폭락 후 급반등", "investment_tip": "폭락 시 풀매수"},
        {"month": "2020-08", "event": "테슬라 주식분할", "impact": "개미 투자 열풍", "investment_tip": "테슬라 보유"},
        {"month": "2020-11", "event": "화이자 백신 발표", "impact": "리오프닝 기대", "investment_tip": "여행/항공 저점 매수"},
        {"month": "2021-01", "event": "게임스탑 사태", "impact": "밈주식, 개미 혁명", "investment_tip": "밈주식 단타"},
        {"month": "2021-04", "event": "코인베이스 IPO", "impact": "암호화폐 제도권 진입", "investment_tip": "암호화폐 거래소"},
        {"month": "2021-11", "event": "메타버스 선언", "impact": "메타 주가 고점", "investment_tip": "메타 고점 매도"},
        {"month": "2022-02", "event": "러시아 우크라이나 전쟁", "impact": "에너지/곡물 급등", "investment_tip": "원자재 투자"},
        {"month": "2022-05", "event": "루나/테라 붕괴", "impact": "암호화폐 대폭락", "investment_tip": "스테이블코인 회피"},
        {"month": "2022-11", "event": "ChatGPT 출시", "impact": "AI 혁명 시작", "investment_tip": "AI 관련주 풀매수"},
        {"month": "2023-03", "event": "SVB 파산", "impact": "은행 위기", "investment_tip": "은행주 단기 회피"},
        {"month": "2023-05", "event": "엔비디아 폭등", "impact": "AI 칩 독점", "investment_tip": "엔비디아 보유"},
        {"month": "2024-01", "event": "비트코인 ETF 승인", "impact": "암호화폐 제도권 완전 진입", "investment_tip": "비트코인 장기 보유"},
    ]
}
