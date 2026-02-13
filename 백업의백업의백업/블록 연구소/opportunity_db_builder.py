#!/usr/bin/env python3
"""
기회 DB 구축 도구 V2.0
- 회귀물/재벌물용 역사적 투자/사업 기회 데이터베이스
- LLM 기반 자동 생성 + 다층 의존성 그래프
- 심층 조사 모드 지원
"""

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# 전역 종료 플래그
SHUTDOWN_REQUESTED = False

# Windows UTF-8
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ─────────────────────────────────────────────
# 로깅 설정
# ─────────────────────────────────────────────
def setup_logging(output_dir: Path) -> logging.Logger:
    """파일 + 콘솔 로깅 설정"""
    output_dir.mkdir(parents=True, exist_ok=True)
    log_file = output_dir / f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logger = logging.getLogger("OpportunityDB")
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러 (상세)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

    # 콘솔 핸들러 (간략)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# ─────────────────────────────────────────────
# 스피너 + 프로그레스
# ─────────────────────────────────────────────
class ProgressTracker:
    """진행 상황 추적기"""

    def __init__(self):
        self.spinning = False
        self.thread = None
        self.message = ""
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0
        self.total_tasks = 0
        self.completed_tasks = 0
        self.total_opportunities = 0
        self.total_api_calls = 0
        self.start_time = None
        self.errors = []

    def _spin(self):
        while self.spinning:
            frame = self.frames[self.current % len(self.frames)]
            elapsed = ""
            if self.start_time:
                secs = int(time.time() - self.start_time)
                elapsed = f" [{secs // 60}m {secs % 60}s]"
            print(f"\r{frame} {self.message}{elapsed}    ", end="", flush=True)
            self.current += 1
            time.sleep(0.1)

    def start(self, message: str = ""):
        self.message = message
        self.spinning = True
        if not self.start_time:
            self.start_time = time.time()
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def update(self, message: str):
        self.message = message

    def stop(self, final_message: str = None):
        self.spinning = False
        if self.thread:
            self.thread.join()
        if final_message:
            print(f"\r✓ {final_message}              ")
        else:
            print(f"\r✓ {self.message}              ")

    def add_opportunity(self, count: int = 1):
        self.total_opportunities += count

    def add_api_call(self):
        self.total_api_calls += 1

    def add_error(self, error: str):
        self.errors.append(error)

    def get_summary(self) -> dict:
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "total_opportunities": self.total_opportunities,
            "total_api_calls": self.total_api_calls,
            "elapsed_seconds": int(elapsed),
            "elapsed_formatted": f"{int(elapsed) // 60}m {int(elapsed) % 60}s",
            "errors": self.errors,
        }


progress = ProgressTracker()

# Google AI
try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
PRIMARY_MODEL = "gemini-2.5-pro"
FALLBACK_MODEL = "gemini-2.5-flash"

# ─────────────────────────────────────────────
# 확장된 카테고리 (20개)
# ─────────────────────────────────────────────
CATEGORIES = {
    # === 금융/투자 ===
    "real_estate": {
        "name": "부동산",
        "description": "토지, 건물, 재개발/재건축 등 부동산 투자",
        "target_count": 15,  # 시대당 목표 생성 수
        "subcategories": [
            "재개발/재건축",
            "신도시/택지",
            "상가/오피스",
            "토지투자",
            "경매/공매",
            "분양권",
            "오피스텔/도시형생활주택",
            "해외부동산",
            "리츠/부동산펀드",
            "임대사업",
        ],
    },
    "stock_equity": {
        "name": "주식/지분투자",
        "description": "상장주식, 비상장주식, 지분투자",
        "target_count": 20,
        "subcategories": [
            "IPO/공모주",
            "우량주/블루칩",
            "성장주",
            "가치주",
            "배당주",
            "테마주/작전주",
            "비상장주식",
            "스팩(SPAC)",
            "해외주식",
            "ETF/ETN",
        ],
    },
    "derivatives_forex": {
        "name": "파생상품/외환",
        "description": "선물, 옵션, 외환, 원자재 투자",
        "target_count": 12,
        "subcategories": [
            "주가지수선물",
            "개별주식옵션",
            "통화선물/옵션",
            "원자재선물",
            "외환(FX)거래",
            "금/은 투자",
            "원유/에너지",
            "농산물",
            "ELS/DLS",
        ],
    },
    "crypto_blockchain": {
        "name": "암호화폐/블록체인",
        "description": "비트코인, 알트코인, 블록체인 사업",
        "target_count": 12,
        "subcategories": [
            "비트코인",
            "이더리움",
            "알트코인",
            "ICO/IEO",
            "NFT",
            "디파이(DeFi)",
            "거래소/플랫폼",
            "채굴/스테이킹",
            "블록체인 서비스",
        ],
    },
    "alternative_investment": {
        "name": "대체투자",
        "description": "미술품, 와인, 수집품 등 대체자산",
        "target_count": 8,
        "subcategories": [
            "미술품/골동품",
            "와인/위스키",
            "명품/시계",
            "자동차/클래식카",
            "음악저작권",
            "영화/드라마 투자",
            "스포츠선수 계약",
            "희귀품/수집품",
        ],
    },
    # === 산업/제조 ===
    "it_tech": {
        "name": "IT/기술",
        "description": "소프트웨어, 하드웨어, 인터넷 서비스",
        "target_count": 18,
        "subcategories": [
            "포털/검색",
            "소셜미디어",
            "이커머스플랫폼",
            "클라우드/SaaS",
            "AI/머신러닝",
            "빅데이터",
            "사이버보안",
            "핀테크",
            "에듀테크",
            "모바일앱",
            "게임개발",
            "VR/AR/메타버스",
        ],
    },
    "semiconductor_electronics": {
        "name": "반도체/전자",
        "description": "반도체, 디스플레이, 전자부품",
        "target_count": 12,
        "subcategories": [
            "메모리반도체",
            "시스템반도체(파운드리)",
            "반도체장비",
            "반도체소재",
            "디스플레이패널",
            "2차전지/배터리",
            "전자부품",
            "PCB/기판",
        ],
    },
    "manufacturing": {
        "name": "중공업/제조",
        "description": "자동차, 조선, 철강, 기계",
        "target_count": 12,
        "subcategories": [
            "자동차완성차",
            "자동차부품",
            "조선/해양",
            "철강/비철금속",
            "기계/로봇",
            "항공우주",
            "방위산업",
            "섬유/의류제조",
        ],
    },
    "energy_resources": {
        "name": "에너지/자원",
        "description": "석유, 가스, 신재생에너지, 광물",
        "target_count": 10,
        "subcategories": [
            "석유/가스개발",
            "정유/석유화학",
            "신재생에너지",
            "원자력",
            "광물/희토류",
            "탄소배출권",
            "수소경제",
            "ESS/전력저장",
        ],
    },
    "bio_healthcare": {
        "name": "바이오/헬스케어",
        "description": "제약, 바이오텍, 의료기기, 헬스케어",
        "target_count": 12,
        "subcategories": [
            "신약개발",
            "바이오시밀러",
            "의료기기",
            "진단키트",
            "디지털헬스케어",
            "원격의료",
            "병원/요양",
            "건강기능식품",
        ],
    },
    # === 서비스/유통 ===
    "retail_distribution": {
        "name": "유통/소매",
        "description": "오프라인/온라인 유통, 프랜차이즈",
        "target_count": 12,
        "subcategories": [
            "백화점/쇼핑몰",
            "대형마트/슈퍼",
            "편의점",
            "홈쇼핑/T커머스",
            "온라인쇼핑몰",
            "소셜커머스",
            "프랜차이즈본사",
            "물류/배송",
        ],
    },
    "food_beverage": {
        "name": "식품/음료",
        "description": "식품제조, 외식, 음료",
        "target_count": 10,
        "subcategories": [
            "식품제조",
            "음료/주류",
            "외식프랜차이즈",
            "카페/베이커리",
            "배달플랫폼",
            "밀키트/간편식",
            "유기농/친환경",
            "수입식품",
        ],
    },
    "content_entertainment": {
        "name": "콘텐츠/엔터테인먼트",
        "description": "게임, 영화, 음악, 웹툰 등 콘텐츠 산업",
        "target_count": 12,
        "subcategories": [
            "게임(PC/모바일/콘솔)",
            "영화제작/배급",
            "드라마/예능제작",
            "음악/엔터기획사",
            "웹툰/웹소설플랫폼",
            "OTT/스트리밍",
            "유튜브/MCN",
            "이스포츠",
            "공연/페스티벌",
        ],
    },
    "travel_leisure": {
        "name": "여행/레저",
        "description": "여행, 호텔, 항공, 레저",
        "target_count": 10,
        "subcategories": [
            "여행사/OTA",
            "항공사",
            "호텔/리조트",
            "카지노/복합리조트",
            "테마파크",
            "골프장",
            "스포츠센터",
            "아웃도어/캠핑",
        ],
    },
    "education": {
        "name": "교육/입시",
        "description": "사교육, 에듀테크, 평생교육",
        "target_count": 10,
        "subcategories": [
            "입시학원",
            "어학원/유학",
            "온라인강의",
            "에듀테크",
            "유아교육",
            "직업훈련",
            "자격증/공무원",
            "기업교육",
        ],
    },
    "beauty_fashion": {
        "name": "뷰티/패션",
        "description": "화장품, 패션, 명품",
        "target_count": 10,
        "subcategories": [
            "화장품제조",
            "K-뷰티브랜드",
            "패션브랜드",
            "스포츠웨어",
            "명품유통",
            "뷰티플랫폼",
            "헤어/네일샵",
            "성형/피부과",
        ],
    },
    # === 인프라/건설 ===
    "construction_infra": {
        "name": "건설/인프라",
        "description": "건설, SOC, 인프라 투자",
        "target_count": 10,
        "subcategories": [
            "주택건설",
            "상업/오피스건설",
            "토목/SOC",
            "플랜트",
            "건설자재",
            "인테리어/리모델링",
            "스마트시티",
            "데이터센터",
        ],
    },
    # === 금융서비스 ===
    "financial_services": {
        "name": "금융서비스",
        "description": "은행, 보험, 증권, 핀테크",
        "target_count": 12,
        "subcategories": [
            "은행/저축은행",
            "증권사",
            "자산운용",
            "보험사",
            "캐피탈/리스",
            "P2P금융",
            "간편결제",
            "로보어드바이저",
        ],
    },
    # === 위기/이벤트 ===
    "crisis_event": {
        "name": "위기/특수상황",
        "description": "경제위기, 버블, 팬데믹 등 특수 상황",
        "target_count": 15,
        "subcategories": [
            "IMF외환위기",
            "글로벌금융위기",
            "유럽재정위기",
            "코로나팬데믹",
            "부동산버블/붕괴",
            "주식시장폭락",
            "환율급변",
            "전쟁/지정학리스크",
            "자연재해",
            "정권교체/정책변화",
        ],
    },
    # === 신산업/미래 ===
    "emerging_future": {
        "name": "신산업/미래기술",
        "description": "신기술, 미래산업, 혁신 분야",
        "target_count": 10,
        "subcategories": [
            "자율주행",
            "드론/UAM",
            "우주산업",
            "양자컴퓨팅",
            "합성생물학",
            "푸드테크",
            "스마트팜",
            "탄소중립기술",
        ],
    },
}

# ─────────────────────────────────────────────
# 시대별 범위 (확장)
# ─────────────────────────────────────────────
ERA_RANGES = [
    {"name": "1960년대", "start": 1960, "end": 1969, "context": "경제개발5개년계획, 수출주도성장 시작"},
    {"name": "1970년대", "start": 1970, "end": 1979, "context": "중화학공업 육성, 새마을운동, 오일쇼크"},
    {"name": "1980년대", "start": 1980, "end": 1989, "context": "3저호황, 민주화, 88올림픽"},
    {"name": "1990년대", "start": 1990, "end": 1999, "context": "주식시장개방, IMF외환위기, IT붐 시작"},
    {"name": "2000년대", "start": 2000, "end": 2009, "context": "닷컴버블, 글로벌금융위기, 스마트폰혁명"},
    {"name": "2010년대", "start": 2010, "end": 2019, "context": "스마트폰전성기, K-콘텐츠, 4차산업혁명"},
    {"name": "2020년대", "start": 2020, "end": 2025, "context": "코로나팬데믹, AI혁명, 금리대전환"},
]

# ─────────────────────────────────────────────
# 확장된 스키마
# ─────────────────────────────────────────────
OPPORTUNITY_SCHEMA = """
{
  "id": "OPP_XXX",
  "name": "기회 이름 (매우 구체적으로, 예: '삼성전자 IPO 청약 (1975.6)', '강남 압구정동 재개발 초기 매입 (1982)')",
  "category": "대분류 키",
  "subcategory": "소분류",

  "entity": {
    "type": "company/asset/market/event/policy/technology",
    "name": "핵심 엔티티명 (실제 기업명, 자산명 등)",
    "ticker": "주식 종목코드 (해당시)",
    "sector": "산업/분야",
    "scale": "대기업/중견기업/중소기업/스타트업/개인사업"
  },

  "entry_phase": "seed/initial/growth/peak/decline/revival",

  "timeline": {
    "discovery_date": "기회 발견 가능 시점 (YYYY-MM 또는 YYYY)",
    "optimal_entry": "최적 진입 시점 (YYYY-MM 또는 YYYY)",
    "peak_date": "정점/피크 시점",
    "exit_deadline": "늦어도 이때까진 청산 (YYYY-MM 또는 YYYY)",
    "korea_timing": 한국 기준 핵심 연도(정수),
    "golden_window": {"start": 시작연도, "end": 종료연도, "months": "핵심 월 (예: 3-6월)"},
    "warning_signs": ["하락/종료 신호1", "신호2"]
  },

  "financials": {
    "min_capital": "최소 필요 자본 (구체적 금액, 예: 5000만원, 3억원)",
    "optimal_capital": "최적 투자금",
    "max_exposure": "최대 투입 권장액",
    "capital_tier": "개인소액/개인거액/소규모법인/중소기업/중견기업/대기업/재벌급",
    "leverage_possible": true/false,
    "leverage_ratio": "가능한 레버리지 비율 (예: 1:3)",
    "liquidity": "high/medium/low (현금화 용이성)",
    "holding_period": "권장 보유 기간"
  },

  "returns": {
    "profit_type": "시세차익/배당/사업수익/로열티/독점수익/복합",
    "conservative_roi": "보수적 예상 수익률",
    "expected_roi": "기대 수익률",
    "best_case_roi": "최상 시나리오 수익률 (실제 역사 기준)",
    "profit_timeline": "수익 실현까지 기간",
    "cashflow_pattern": "일시/정기/불규칙",
    "tax_consideration": "세금 관련 고려사항"
  },

  "risk_assessment": {
    "overall_risk": "very_low/low/medium/high/very_high/extreme",
    "failure_probability": 0.0~1.0,
    "max_loss": "최대 손실 시나리오",
    "risk_factors": [
      {"factor": "리스크 요인1", "probability": "high/medium/low", "impact": "high/medium/low"},
      {"factor": "리스크 요인2", "probability": "high/medium/low", "impact": "high/medium/low"}
    ],
    "hedging_options": ["헷지 방법1", "헷지 방법2"],
    "exit_strategy": "손절/청산 전략"
  },

  "requirements": {
    "prerequisites": [
      {"name": "선행조건1", "type": "자본/기술/인맥/라이선스/경험", "critical": true/false, "how_to_obtain": "획득 방법"}
    ],
    "skills_needed": ["필요 역량/지식1", "역량2"],
    "connections_needed": ["필요 인맥/네트워크1", "인맥2"],
    "legal_requirements": ["법적 요건1", "요건2"],
    "regulatory_barriers": ["규제 장벽1", "장벽2"],
    "time_to_setup": "준비 기간",
    "execution_complexity": "low/medium/high/very_high"
  },

  "historical_context": {
    "real_winners": [
      {"name": "실제 성공자1", "strategy": "그들의 전략", "profit": "실제 수익"}
    ],
    "real_losers": [
      {"name": "실패자1", "mistake": "실패 원인"}
    ],
    "market_size": "당시 시장 규모",
    "competition_level": "경쟁 강도",
    "key_events": ["관련 핵심 사건1", "사건2"],
    "government_policy": "관련 정부 정책",
    "social_context": "사회적 맥락/분위기"
  },

  "execution_playbook": {
    "step_by_step": [
      {"step": 1, "action": "구체적 행동1", "timing": "시기", "resources": "필요 자원"},
      {"step": 2, "action": "구체적 행동2", "timing": "시기", "resources": "필요 자원"}
    ],
    "critical_decisions": ["핵심 의사결정 포인트1", "포인트2"],
    "common_mistakes": ["흔한 실수1", "실수2"],
    "success_metrics": ["성공 지표1", "지표2"]
  },

  "failure_scenarios": [
    {
      "scenario": "실패 시나리오1",
      "trigger": "발생 조건",
      "probability": "high/medium/low",
      "consequence": "결과",
      "recovery": "회복 방법"
    }
  ],

  "alternative_strategies": [
    {
      "name": "대안 전략1",
      "description": "설명",
      "pros": ["장점1"],
      "cons": ["단점1"],
      "when_to_use": "적용 상황"
    }
  ],

  "story_hooks": {
    "dramatic_moments": ["극적인 순간/장면1", "순간2"],
    "conflicts": ["갈등 요소1", "갈등2"],
    "complications": ["예상치 못한 문제/반전1", "문제2"],
    "villain_candidates": ["잠재적 악역/경쟁자1", "악역2"],
    "ally_candidates": ["잠재적 조력자1", "조력자2"],
    "moral_dilemmas": ["윤리적 딜레마1"],
    "plot_twists": ["가능한 반전1"]
  },

  "regression_strategy": {
    "future_knowledge_value": "low/medium/high/very_high/game_changing",
    "optimal_regression_year": "이 기회 노리려면 최소 이 연도로 회귀해야 함",
    "preparation_time_needed": "회귀 후 준비 기간",
    "butterfly_risk": "low/medium/high (역사 변동 위험)",
    "detection_risk": "low/medium/high (미래지식 발각 위험)",
    "detection_avoidance": ["발각 회피 방법1", "방법2"],
    "alt_history_impact": "역사가 바뀌면 어떻게 되는지",
    "synergy_opportunities": ["이 기회와 시너지 나는 다른 기회들"]
  },

  "economic_context": {
    "gdp_growth": "당시 GDP 성장률",
    "inflation": "물가상승률",
    "interest_rate": "기준금리",
    "exchange_rate": "환율 (USD/KRW)",
    "unemployment": "실업률",
    "real_estate_index": "부동산 지수/시세",
    "stock_index": "종합주가지수"
  },

  "related_opportunities": ["연관 기회 이름1", "이름2"],
  "enables": ["이 기회가 열어주는 후속 기회1", "후속2"],
  "blocked_by": ["이 기회를 막는 선행 실패1"],
  "conflicts_with": ["동시 추구 어려운 기회1"],

  "tags": ["태그1", "태그2", "태그3"],
  "confidence_score": 0.0~1.0 (이 정보의 신뢰도),
  "data_sources": ["정보 출처1", "출처2"]
}
"""

# ─────────────────────────────────────────────
# 의존성 관계 유형
# ─────────────────────────────────────────────
DEPENDENCY_TYPES = {
    "capital_flow": "자본 축적 (A에서 번 돈이 B의 자본금)",
    "skill_transfer": "기술/역량 이전 (A 경험이 B에 필요)",
    "network_leverage": "인맥 활용 (A에서 만난 사람이 B에 핵심)",
    "market_access": "시장 접근권 (A가 B 시장 진입 자격 부여)",
    "timing_sequence": "시간 순서 (A가 끝나야 B 시작 가능)",
    "license_grant": "라이선스/허가 (A가 B의 사업권 부여)",
    "synergy": "시너지 (A+B 동시 추구 시 효과 배가)",
    "hedge": "헷지 (A 실패 시 B가 보험)",
    "conflict": "상충 (A 하면 B 불가능)",
    "chain_reaction": "연쇄 반응 (A 성공이 B 기회 생성)",
}


# ─────────────────────────────────────────────
# LLM 클래스
# ─────────────────────────────────────────────
class OpportunityLLM:
    def __init__(self, api_key: str, model: str = PRIMARY_MODEL, logger: logging.Logger = None):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.fallback_model = FALLBACK_MODEL
        self.logger = logger or logging.getLogger("OpportunityDB")

    def generate(self, prompt: str, temperature: float = 0.7, retry_count: int = 3) -> dict | None:
        """JSON 응답 생성 (재시도 + 폴백)"""
        models_to_try = [self.model, self.fallback_model]

        for model in models_to_try:
            for attempt in range(retry_count):
                try:
                    progress.add_api_call()
                    response = self.client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature, response_mime_type="application/json"
                        ),
                    )
                    text = response.text.strip()
                    result = json.loads(text)
                    self.logger.debug(f"API 성공: {model}, 시도 {attempt + 1}")
                    return result
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON 파싱 실패 ({model}, 시도 {attempt + 1}): {e}")
                    # JSON 복구 시도
                    try:
                        text = response.text.strip()
                        # 흔한 문제 수정
                        text = text.replace("'", '"')
                        if not text.startswith("{"):
                            start = text.find("{")
                            if start != -1:
                                text = text[start:]
                        if not text.endswith("}"):
                            end = text.rfind("}")
                            if end != -1:
                                text = text[: end + 1]
                        return json.loads(text)
                    except:
                        pass
                except Exception as e:
                    self.logger.warning(f"API 오류 ({model}, 시도 {attempt + 1}): {e}")
                    if "quota" in str(e).lower() or "rate" in str(e).lower():
                        time.sleep(30)  # 할당량 초과 시 대기
                    else:
                        time.sleep(2)

        progress.add_error(f"LLM 호출 실패: {prompt[:100]}...")
        return None

    def generate_text(self, prompt: str, temperature: float = 0.7) -> str | None:
        """텍스트 응답 생성"""
        try:
            progress.add_api_call()
            response = self.client.models.generate_content(
                model=self.model, contents=prompt, config=types.GenerateContentConfig(temperature=temperature)
            )
            return response.text.strip()
        except Exception as e:
            self.logger.error(f"LLM 텍스트 오류: {e}")
            return None


# ─────────────────────────────────────────────
# 프롬프트 빌더
# ─────────────────────────────────────────────
def build_deep_research_prompt(category_key: str, category_info: dict, era: dict, existing_names: list = None) -> str:
    """심층 조사 프롬프트"""
    existing_str = ""
    if existing_names:
        existing_str = (
            f"\n\n## 이미 생성된 기회 (중복 피할 것)\n{chr(10).join(['- ' + n for n in existing_names[:30]])}"
        )

    return f"""당신은 한국 경제사, 산업사, 투자 역사 전문가입니다.

## 작업
{era["name"]} ({era["start"]}~{era["end"]}) 한국의 **{category_info["name"]}** 분야에서
실제로 있었던 투자/사업 기회를 **{category_info["target_count"]}개** 이상 심층 조사하여 생성해주세요.

## 시대 배경
{era.get("context", "")}

## 소분류 참고
{", ".join(category_info["subcategories"])}

## 핵심 요구사항

### 1. 실증적 정확성
- **실제 기업명, 실제 날짜, 실제 금액** 사용 (가상 X)
- 역사적 사실에 기반한 구체적 수치와 타임라인
- 당시 물가/환율 반영한 현실적 금액

### 2. 다양성 확보
- **자본 규모**: 소액(수백만원) ~ 재벌급(수조원) 골고루
- **리스크 수준**: 안전 ~ 고위험 골고루
- **성공/실패**: 대박 사례 + 쪽박 사례 모두 포함
- **소분류**: 가능한 모든 소분류 커버

### 3. 회귀물 활용성
- 회귀자가 "그때 그걸 알았더라면" 느낄 수 있는 기회
- 구체적인 진입 시점과 청산 시점
- 당시에는 몰랐지만 나중에 드러난 정보 포함

### 4. 서사적 풍부함
- 드라마틱한 순간, 갈등, 반전 요소
- 악역/조력자 후보
- 윤리적 딜레마
{existing_str}

## 출력 형식
다음 JSON 스키마를 **정확히** 따라주세요. 모든 필드를 채워주세요:

{{"opportunities": [
{OPPORTUNITY_SCHEMA}
]}}

## 중요 주의사항
- id는 "OPP_" + 3자리 숫자 (예: OPP_001) - 나중에 재할당됨
- 모든 연도/날짜는 **정수** 또는 "YYYY-MM" 문자열
- 금액은 **당시 기준** 한글 표기 (예: "1억원", "50만원")
- related_opportunities, enables 등은 **기회 이름**으로 (ID 아님)
- confidence_score는 정보의 확실성 (0.5 미만이면 추측)
- 최소 {category_info["target_count"]}개 이상 생성

{era["name"]} {category_info["name"]} 분야의 실제 역사적 기회들을 상세히 생성해주세요.
"""


def build_supplementary_prompt(
    category_key: str, category_info: dict, era: dict, existing_opportunities: list, target_subcategories: list
) -> str:
    """보충 생성 프롬프트 (누락된 소분류)"""
    existing_names = [o.get("name", "") for o in existing_opportunities]

    return f"""당신은 한국 경제사 전문가입니다.

## 작업
{era["name"]} {category_info["name"]} 분야에서 다음 **소분류**에 해당하는 기회가 부족합니다.
이 소분류들에 집중하여 추가 기회를 생성해주세요.

## 보충 필요 소분류
{", ".join(target_subcategories)}

## 이미 있는 기회 (중복 피할 것)
{chr(10).join(["- " + n for n in existing_names[:20]])}

## 요구사항
- 위 소분류별 최소 1-2개씩
- 실제 역사적 사실 기반
- 구체적 기업명, 날짜, 금액

## 출력 형식
{{"opportunities": [
{OPPORTUNITY_SCHEMA}
]}}

누락된 소분류의 기회들을 생성해주세요.
"""


def build_dependency_analysis_prompt(opportunities: list, analysis_type: str = "full") -> str:
    """다층 의존성 분석 프롬프트"""
    opp_summary = "\n".join(
        [
            f"- {o['id']}: {o['name']} ({o.get('timeline', {}).get('korea_timing', '?')}) - {o.get('category', '?')}"
            for o in opportunities[:50]  # 최대 50개
        ]
    )

    dep_types = "\n".join([f"- {k}: {v}" for k, v in DEPENDENCY_TYPES.items()])

    return f"""다음은 회귀물용 투자/사업 기회 목록입니다:

{opp_summary}

## 작업
이 기회들 간의 **다층적 의존성 관계**를 분석해주세요.

## 의존성 유형
{dep_types}

## 분석 요청
1. **직접 의존성**: A를 해야 B가 가능한 명확한 관계
2. **시너지 관계**: A+B 동시 추구 시 효과 배가
3. **상충 관계**: A를 하면 B가 어려워지는 관계
4. **연쇄 경로**: A→B→C 같은 다단계 경로

## 출력 형식
```json
{{
  "dependencies": [
    {{
      "from": "OPP_001",
      "to": "OPP_005",
      "type": "capital_flow",
      "strength": "strong/medium/weak",
      "description": "상세 설명",
      "bidirectional": false
    }}
  ],
  "synergy_clusters": [
    {{
      "name": "클러스터명",
      "opportunities": ["OPP_001", "OPP_003"],
      "synergy_effect": "시너지 효과 설명"
    }}
  ],
  "optimal_paths": [
    {{
      "name": "경로명 (예: 부동산→IT 코스)",
      "sequence": ["OPP_001", "OPP_003", "OPP_007"],
      "total_potential": "총 잠재 수익",
      "difficulty": "난이도"
    }}
  ]
}}
```

명확한 관계만 추출해주세요. 추측은 strength를 "weak"로.
"""


def build_cross_category_prompt(all_opportunities: list) -> str:
    """카테고리 간 연결 분석"""
    # 카테고리별 샘플링
    by_category = {}
    for opp in all_opportunities:
        cat = opp.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(opp)

    summary_lines = []
    for cat, opps in by_category.items():
        cat_name = CATEGORIES.get(cat, {}).get("name", cat)
        samples = opps[:5]
        for o in samples:
            summary_lines.append(f"- [{cat_name}] {o['id']}: {o['name']}")

    return f"""다음은 다양한 분야의 투자/사업 기회들입니다:

{chr(10).join(summary_lines[:60])}

## 작업
**다른 카테고리 간**의 연결 관계를 찾아주세요.

예시:
- 부동산 수익 → IT 투자 자금
- 제조업 인맥 → 금융 투자 정보
- 위기 상황 → 특정 산업 기회

## 출력 형식
```json
{{
  "cross_category_links": [
    {{
      "from_category": "real_estate",
      "to_category": "it_tech",
      "from_opportunity": "OPP_XXX",
      "to_opportunity": "OPP_YYY",
      "link_type": "capital_flow/skill_transfer/network_leverage/timing",
      "description": "연결 설명"
    }}
  ],
  "recommended_portfolios": [
    {{
      "name": "포트폴리오명",
      "theme": "테마 설명",
      "opportunities": ["OPP_001", "OPP_050", "OPP_100"],
      "rationale": "조합 근거"
    }}
  ]
}}
```
"""


# ─────────────────────────────────────────────
# 메인 빌더
# ─────────────────────────────────────────────
class OpportunityDBBuilder:
    def __init__(self, api_key: str, output_dir: Path, model: str = PRIMARY_MODEL):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = setup_logging(output_dir)
        self.llm = OpportunityLLM(api_key, model, self.logger)

        self.db = {
            "version": "2.0",
            "created": datetime.now().isoformat(),
            "model": model,
            "opportunities": [],
            "dependencies": [],
            "synergy_clusters": [],
            "optimal_paths": [],
            "cross_category_links": [],
            "recommended_portfolios": [],
            "categories": CATEGORIES,
            "era_ranges": ERA_RANGES,
            "dependency_types": DEPENDENCY_TYPES,
        }

        self.id_counter = 1

    def generate_category_era(self, category_key: str, era: dict, existing_names: list = None) -> list:
        """특정 카테고리+시대의 기회 심층 생성"""
        category_info = CATEGORIES[category_key]
        target_count = category_info["target_count"]

        progress.start(f"[{era['name']}] {category_info['name']} 심층 조사 중... (목표: {target_count}개)")

        # 1단계: 메인 생성
        prompt = build_deep_research_prompt(category_key, category_info, era, existing_names)
        result = self.llm.generate(prompt, temperature=0.8)

        opportunities = []
        if result and "opportunities" in result:
            opportunities = result["opportunities"]

        # 2단계: 소분류 커버리지 체크 및 보충
        if opportunities:
            covered_subcats = set()
            for opp in opportunities:
                subcat = opp.get("subcategory", "")
                covered_subcats.add(subcat)

            missing_subcats = set(category_info["subcategories"]) - covered_subcats

            if missing_subcats and len(opportunities) < target_count:
                progress.update(
                    f"[{era['name']}] {category_info['name']} 보충 생성 중... (누락: {len(missing_subcats)}개 소분류)"
                )

                supp_prompt = build_supplementary_prompt(
                    category_key, category_info, era, opportunities, list(missing_subcats)
                )
                supp_result = self.llm.generate(supp_prompt, temperature=0.9)

                if supp_result and "opportunities" in supp_result:
                    opportunities.extend(supp_result["opportunities"])

        # ID 재할당 및 메타데이터
        for opp in opportunities:
            opp["id"] = f"OPP_{self.id_counter:04d}"
            opp["_source_category"] = category_key
            opp["_source_era"] = era["name"]
            opp["_generated_at"] = datetime.now().isoformat()
            self.id_counter += 1

        progress.add_opportunity(len(opportunities))
        progress.stop(f"[{era['name']}] {category_info['name']} - {len(opportunities)}개 생성")

        self.logger.info(f"생성 완료: {era['name']} {category_info['name']} = {len(opportunities)}개")

        return opportunities

    def generate_all(self, categories: list = None, eras: list = None, deep_mode: bool = True):
        """전체 생성"""
        if categories is None:
            categories = list(CATEGORIES.keys())
        if eras is None:
            eras = ERA_RANGES

        # 진행 상황 계산
        total_combinations = len(categories) * len(eras)
        completed = set()
        for opp in self.db["opportunities"]:
            key = (opp.get("_source_category"), opp.get("_source_era"))
            completed.add(key)

        self.logger.info(f"시작: {len(categories)}개 카테고리 × {len(eras)}개 시대 = {total_combinations}개 조합")

        current = 0
        for category_key in categories:
            if SHUTDOWN_REQUESTED:
                self.logger.warning("중단 요청됨")
                break

            cat_info = CATEGORIES[category_key]
            print(f"\n{'=' * 60}")
            print(
                f"[{cat_info['name']}] - 소분류 {len(cat_info['subcategories'])}개, 목표 {cat_info['target_count']}개/시대"
            )
            print(f"{'=' * 60}")

            for era in eras:
                if SHUTDOWN_REQUESTED:
                    break

                current += 1

                # 이미 완료된 조합 스킵
                if (category_key, era["name"]) in completed:
                    print(f"  ({current}/{total_combinations}) [{era['name']}] - 이미 완료, 스킵")
                    continue

                # 기존 이름 수집 (중복 방지용)
                existing_names = [o.get("name", "") for o in self.db["opportunities"]]

                opportunities = self.generate_category_era(category_key, era, existing_names)
                self.db["opportunities"].extend(opportunities)

                # Rate limit 방지
                time.sleep(2)

            # 카테고리 완료 시 자동 저장
            self._auto_save()

        print(f"\n{'=' * 60}")
        print(f"기회 생성 완료: 총 {len(self.db['opportunities'])}개")
        print(f"{'=' * 60}")

    def generate_dependencies(self, deep_analysis: bool = True):
        """의존성 그래프 생성"""
        if len(self.db["opportunities"]) < 2:
            self.logger.warning("기회가 2개 미만이어서 의존성 분석 스킵")
            return

        print(f"\n{'=' * 60}")
        print("다층 의존성 분석")
        print(f"{'=' * 60}")

        # 1단계: 시대별 분석
        for era in ERA_RANGES:
            if SHUTDOWN_REQUESTED:
                break

            era_opps = [o for o in self.db["opportunities"] if o.get("_source_era") == era["name"]]

            if len(era_opps) < 2:
                continue

            progress.start(f"[{era['name']}] {len(era_opps)}개 기회 의존성 분석 중...")

            prompt = build_dependency_analysis_prompt(era_opps)
            result = self.llm.generate(prompt, temperature=0.5)

            if result:
                if "dependencies" in result:
                    self.db["dependencies"].extend(result["dependencies"])
                if "synergy_clusters" in result:
                    self.db["synergy_clusters"].extend(result["synergy_clusters"])
                if "optimal_paths" in result:
                    self.db["optimal_paths"].extend(result["optimal_paths"])

                progress.stop(f"[{era['name']}] - {len(result.get('dependencies', []))}개 의존성")
            else:
                progress.stop(f"[{era['name']}] - 분석 실패")

            time.sleep(1)

        # 2단계: 카테고리 간 분석
        if deep_analysis and not SHUTDOWN_REQUESTED:
            progress.start("카테고리 간 연결 분석 중...")

            cross_prompt = build_cross_category_prompt(self.db["opportunities"])
            cross_result = self.llm.generate(cross_prompt, temperature=0.6)

            if cross_result:
                if "cross_category_links" in cross_result:
                    self.db["cross_category_links"] = cross_result["cross_category_links"]
                if "recommended_portfolios" in cross_result:
                    self.db["recommended_portfolios"] = cross_result["recommended_portfolios"]
                progress.stop(f"카테고리 간 연결 - {len(cross_result.get('cross_category_links', []))}개")
            else:
                progress.stop("카테고리 간 분석 실패")

        print("\n의존성 분석 완료:")
        print(f"  - 의존성: {len(self.db['dependencies'])}개")
        print(f"  - 시너지 클러스터: {len(self.db['synergy_clusters'])}개")
        print(f"  - 최적 경로: {len(self.db['optimal_paths'])}개")
        print(f"  - 카테고리간 연결: {len(self.db['cross_category_links'])}개")

    def _auto_save(self):
        """중간 자동 저장"""
        backup_path = self.output_dir / "opportunity_db_backup.json"
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        self.logger.debug(f"자동저장: {len(self.db['opportunities'])}개 → {backup_path.name}")
        print(f"  [자동저장] {len(self.db['opportunities'])}개 기회")

    def save(self):
        """최종 저장"""
        # 메인 DB
        db_path = self.output_dir / "opportunity_db.json"
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
        print(f"\n저장: {db_path}")

        # 의존성 그래프 (시각화용)
        if self.db["dependencies"]:
            graph_path = self.output_dir / "dependency_graph.json"
            graph = {
                "nodes": [
                    {
                        "id": o["id"],
                        "name": o["name"],
                        "year": o.get("timeline", {}).get("korea_timing"),
                        "category": o.get("category"),
                        "subcategory": o.get("subcategory"),
                        "risk": o.get("risk_assessment", {}).get("overall_risk"),
                        "roi": o.get("returns", {}).get("expected_roi"),
                    }
                    for o in self.db["opportunities"]
                ],
                "edges": self.db["dependencies"],
                "clusters": self.db["synergy_clusters"],
                "paths": self.db["optimal_paths"],
            }
            with open(graph_path, "w", encoding="utf-8") as f:
                json.dump(graph, f, ensure_ascii=False, indent=2)
            print(f"저장: {graph_path}")

        # 카테고리별 분리 저장
        by_category_dir = self.output_dir / "by_category"
        by_category_dir.mkdir(exist_ok=True)

        for cat_key in CATEGORIES.keys():
            cat_opps = [o for o in self.db["opportunities"] if o.get("_source_category") == cat_key]
            if cat_opps:
                cat_path = by_category_dir / f"{cat_key}.json"
                with open(cat_path, "w", encoding="utf-8") as f:
                    json.dump(cat_opps, f, ensure_ascii=False, indent=2)

        # 시대별 분리 저장
        by_era_dir = self.output_dir / "by_era"
        by_era_dir.mkdir(exist_ok=True)

        for era in ERA_RANGES:
            era_opps = [o for o in self.db["opportunities"] if o.get("_source_era") == era["name"]]
            if era_opps:
                era_path = by_era_dir / f"{era['name']}.json"
                with open(era_path, "w", encoding="utf-8") as f:
                    json.dump(era_opps, f, ensure_ascii=False, indent=2)

        # 통계
        stats = self._generate_stats()
        stats_path = self.output_dir / "build_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"저장: {stats_path}")

        # 요약 리포트
        self._generate_report(stats)

    def _generate_stats(self) -> dict:
        """통계 생성"""
        stats = {
            "build_info": {
                "version": self.db["version"],
                "model": self.db["model"],
                "created": self.db["created"],
                "completed": datetime.now().isoformat(),
            },
            "totals": {
                "opportunities": len(self.db["opportunities"]),
                "dependencies": len(self.db["dependencies"]),
                "synergy_clusters": len(self.db["synergy_clusters"]),
                "optimal_paths": len(self.db["optimal_paths"]),
                "cross_category_links": len(self.db["cross_category_links"]),
            },
            "by_category": {},
            "by_era": {},
            "by_subcategory": {},
            "by_risk_level": {},
            "by_capital_tier": {},
            "coverage": {"categories_covered": 0, "eras_covered": 0, "subcategories_covered": 0},
            "api_stats": progress.get_summary(),
        }

        # 카테고리별
        for opp in self.db["opportunities"]:
            cat = opp.get("_source_category", "unknown")
            era = opp.get("_source_era", "unknown")
            subcat = opp.get("subcategory", "unknown")
            risk = opp.get("risk_assessment", {}).get("overall_risk", "unknown")
            capital = opp.get("financials", {}).get("capital_tier", "unknown")

            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
            stats["by_era"][era] = stats["by_era"].get(era, 0) + 1
            stats["by_subcategory"][subcat] = stats["by_subcategory"].get(subcat, 0) + 1
            stats["by_risk_level"][risk] = stats["by_risk_level"].get(risk, 0) + 1
            stats["by_capital_tier"][capital] = stats["by_capital_tier"].get(capital, 0) + 1

        stats["coverage"]["categories_covered"] = len(stats["by_category"])
        stats["coverage"]["eras_covered"] = len(stats["by_era"])
        stats["coverage"]["subcategories_covered"] = len(stats["by_subcategory"])

        return stats

    def _generate_report(self, stats: dict):
        """텍스트 리포트 생성"""
        report_path = self.output_dir / "BUILD_REPORT.txt"

        lines = [
            "=" * 60,
            "기회 DB 구축 리포트",
            "=" * 60,
            "",
            f"버전: {stats['build_info']['version']}",
            f"모델: {stats['build_info']['model']}",
            f"생성일: {stats['build_info']['created']}",
            f"완료일: {stats['build_info']['completed']}",
            "",
            "-" * 60,
            "총계",
            "-" * 60,
            f"기회: {stats['totals']['opportunities']}개",
            f"의존성: {stats['totals']['dependencies']}개",
            f"시너지 클러스터: {stats['totals']['synergy_clusters']}개",
            f"최적 경로: {stats['totals']['optimal_paths']}개",
            f"카테고리간 연결: {stats['totals']['cross_category_links']}개",
            "",
            "-" * 60,
            "카테고리별",
            "-" * 60,
        ]

        for cat, count in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
            cat_name = CATEGORIES.get(cat, {}).get("name", cat)
            lines.append(f"  {cat_name}: {count}개")

        lines.extend(
            [
                "",
                "-" * 60,
                "시대별",
                "-" * 60,
            ]
        )

        for era, count in stats["by_era"].items():
            lines.append(f"  {era}: {count}개")

        lines.extend(
            [
                "",
                "-" * 60,
                "API 통계",
                "-" * 60,
                f"총 API 호출: {stats['api_stats']['total_api_calls']}회",
                f"소요 시간: {stats['api_stats']['elapsed_formatted']}",
                f"오류 수: {len(stats['api_stats']['errors'])}개",
                "",
                "=" * 60,
            ]
        )

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"저장: {report_path}")
        print("\n".join(lines[-15:]))

    def load_existing(self, path: Path) -> bool:
        """기존 DB 로드"""
        if path.exists():
            with open(path, encoding="utf-8") as f:
                self.db = json.load(f)
            self.id_counter = len(self.db.get("opportunities", [])) + 1
            self.logger.info(f"기존 DB 로드: {len(self.db['opportunities'])}개 기회")
            print(f"기존 DB 로드: {len(self.db['opportunities'])}개 기회")
            return True
        return False


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="회귀물/재벌물용 기회 DB 심층 구축 도구 V2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 전체 생성 (20개 카테고리 × 7개 시대)
  python opportunity_db_builder.py

  # 특정 카테고리만
  python opportunity_db_builder.py -c real_estate stock_equity it_tech

  # 특정 시대만
  python opportunity_db_builder.py -e 1990년대 2000년대

  # 중단 후 이어서
  python opportunity_db_builder.py --resume

  # 의존성 분석만 (기존 DB 사용)
  python opportunity_db_builder.py --deps-only
        """,
    )
    parser.add_argument("--output", "-o", default="libraries/_opportunity_db", help="출력 폴더")
    parser.add_argument("--model", "-m", default=PRIMARY_MODEL, help=f"모델 (기본: {PRIMARY_MODEL})")
    parser.add_argument("--categories", "-c", nargs="+", help="특정 카테고리만")
    parser.add_argument("--eras", "-e", nargs="+", help="특정 시대만")
    parser.add_argument("--skip-deps", action="store_true", help="의존성 분석 스킵")
    parser.add_argument("--deps-only", action="store_true", help="의존성 분석만 실행")
    parser.add_argument("--resume", "-r", action="store_true", help="기존 DB에 이어서")
    parser.add_argument("--list-categories", action="store_true", help="카테고리 목록 출력")
    args = parser.parse_args()

    # 카테고리 목록 출력
    if args.list_categories:
        print("\n사용 가능한 카테고리:")
        print("-" * 50)
        for key, info in CATEGORIES.items():
            print(f"  {key:25} | {info['name']:15} | 목표 {info['target_count']}개/시대")
            print(f"    소분류: {', '.join(info['subcategories'][:5])}...")
        print("\n사용 가능한 시대:")
        print("-" * 50)
        for era in ERA_RANGES:
            print(f"  {era['name']} ({era['start']}-{era['end']}): {era.get('context', '')}")
        return

    # API 키
    env_path = Path(r"C:\Users\PC\Desktop\글도비\.env")
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("GOOGLE_API_KEY 없음")
        sys.exit(1)

    output_dir = Path(args.output)

    # 카테고리/시대 필터
    categories = args.categories if args.categories else list(CATEGORIES.keys())
    eras = ERA_RANGES
    if args.eras:
        eras = [e for e in ERA_RANGES if e["name"] in args.eras]

    # Ctrl+C 핸들러
    def signal_handler(sig, frame):
        global SHUTDOWN_REQUESTED
        if SHUTDOWN_REQUESTED:
            print("\n\n강제 종료!")
            sys.exit(1)
        print("\n\n⚠️  Ctrl+C 감지! 현재 작업 완료 후 저장합니다...")
        print("   (한번 더 누르면 강제 종료)")
        SHUTDOWN_REQUESTED = True

    signal.signal(signal.SIGINT, signal_handler)

    # 배너
    total_target = sum(CATEGORIES[c]["target_count"] for c in categories) * len(eras)

    print()
    print("=" * 65)
    print("  기회 DB 심층 구축 도구 V2.0")
    print("  (회귀물/재벌물 전용 - 역사적 투자 기회 데이터베이스)")
    print("=" * 65)
    print(f"  모델       : {args.model}")
    print(f"  출력       : {output_dir}")
    print(f"  카테고리   : {len(categories)}개")
    for cat_key in categories[:5]:
        ci = CATEGORIES[cat_key]
        print(f"               - {ci['name']} (목표 {ci['target_count']}개/시대)")
    if len(categories) > 5:
        print(f"               ... 외 {len(categories) - 5}개")
    print(f"  시대       : {len(eras)}개")
    for era in eras:
        print(f"               - {era['name']}")
    print(f"  예상 생성  : 약 {total_target}개 기회")
    print("-" * 65)
    print("  💡 Ctrl+C로 중단해도 진행분 자동 저장")
    print("  💡 --resume 옵션으로 이어서 가능")
    print("  💡 --list-categories로 전체 목록 확인")
    print("=" * 65)
    print()

    builder = OpportunityDBBuilder(api_key, output_dir, args.model)

    # 기존 DB 로드
    if args.resume or args.deps_only:
        loaded = builder.load_existing(output_dir / "opportunity_db.json")
        if not loaded:
            loaded = builder.load_existing(output_dir / "opportunity_db_backup.json")

    # 기회 생성
    if not args.deps_only:
        builder.generate_all(categories, eras)

    # 의존성 분석
    if not args.skip_deps:
        builder.generate_dependencies(deep_analysis=True)

    # 저장
    builder.save()

    print()
    print("=" * 65)
    print("  완료!")
    summary = progress.get_summary()
    print(f"  총 기회: {summary['total_opportunities']}개")
    print(f"  API 호출: {summary['total_api_calls']}회")
    print(f"  소요 시간: {summary['elapsed_formatted']}")
    if summary["errors"]:
        print(f"  오류: {len(summary['errors'])}개")
    print("=" * 65)


if __name__ == "__main__":
    main()
