#!/usr/bin/env python3
"""Build Phase 0, TR, and BI assets for `망국 황자는 조선을 산다`."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.core.response_schemas import validate_bible_structure, validate_treatment_structure

WORK_ID = "fallen_prince_buys_joseon"
TITLE = "망국 황자는 조선을 산다"
PROTAGONIST_NAME = "이강윤"

PHASE0_PATH = ROOT / "treatments" / f"{WORK_ID}_phase0_design.json"
TR_PATH = ROOT / "treatments" / f"{WORK_ID}_tr_block_070_draft.json"
TR_TITLE_PATH = ROOT / "treatments" / f"{TITLE}_tr_block_070_draft.json"
BI_PATH = ROOT / "bible" / f"0_bi_{WORK_ID}.json"

ROYAL = "AH-1905-1910-KR_ROYAL_ASSETS_EXILE-B01"
EU = "AH-1907-1936-EU_FINANCE_PORTS-B01"
COLONIAL = "AH-1910-1938-KR_COLONIAL_ASSET_TAKEOVER-B01"
BANK_FX = "AH-1900-1950-BANKING_FX-B01"
MARINE = "AH-1900-1950-MARINE_INSURANCE-B01"
RAIL = "AH-1900-1950-RAIL_INFRA-B01"
HUBS = "AH-1900-1950-SH_KR_MANCHURIA-HUBS-B01"


def format_eok(value: int) -> str:
    sign = "-" if value < 0 else ""
    amount = abs(value)
    if amount >= 10_000:
        jo, eok = divmod(amount, 10_000)
        return f"{sign}{jo}조{eok}억" if eok else f"{sign}{jo}조"
    return f"{sign}{amount}억"


def format_profit(delta: int) -> str:
    if delta == 0:
        return "변동 없음"
    return f"{format_eok(abs(delta))} 증가" if delta > 0 else f"{format_eok(abs(delta))} 감소"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def unique_in_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def hist(name: str | None, year: int | None, how_exploited: str | None, source: str | None) -> dict[str, Any]:
    return {
        "name": name,
        "year": year,
        "how_exploited": how_exploited,
        "source": source,
    }


def source_binding(core: list[str], support: list[str] | None = None) -> dict[str, list[str]]:
    return {
        "core": deepcopy(core),
        "support": deepcopy(support or []),
    }


def block_numbers(block_range: str) -> tuple[int, int]:
    start, end = block_range.split("-")
    return int(start), int(end)


def slot(
    title: str,
    function: str,
    time: str,
    location: str,
    sector: str,
    deal_type: str,
    method: str,
    opponent: str,
    targets: list[str],
    event: dict[str, Any],
    emotion: str,
    intensity: int,
    tension: int,
    duration: str,
    success: str,
    *,
    foreshadow: list[str] | None = None,
    callback: list[str] | None = None,
    sources: dict[str, list[str]] | None = None,
    partner: str | None = None,
    risk: str = "중위험",
) -> dict[str, Any]:
    return {
        "title": title,
        "function": function,
        "time": time,
        "location": location,
        "sector": sector,
        "deal_type": deal_type,
        "method": method,
        "opponent": opponent,
        "targets": targets,
        "event": event,
        "emotion": emotion,
        "intensity": intensity,
        "tension": tension,
        "duration": duration,
        "success": success,
        "foreshadow": foreshadow or [],
        "callback": callback or [],
        "sources": deepcopy(sources or source_binding([], [])),
        "partner": partner,
        "risk": risk,
    }


def opponent_type(name: str) -> str:
    if "총독부" in name or "통감부" in name:
        return "식민지 행정"
    if "군부" in name or "관동군" in name:
        return "군사 권력"
    if "은행" in name or "브로커" in name:
        return "금융 경쟁자"
    if "해운" in name or "선주" in name:
        return "해운 카르텔"
    return "정치·금융 연합"


PROJECT = {
    "title_ko": TITLE,
    "core_premise": "독살당한 대한제국 서출 황자 이강윤이 1907년으로 회귀해 유럽의 해운, 보험, 외환, 군수 계약을 장악한 뒤 총독부가 굴리는 철도, 은행, 광산, 토지를 역으로 사들이며 조선의 실소유주가 된다.",
    "format": "대체역사 황실 자본 제국 성장물",
    "logline": "칼로 빼앗긴 나라를 통장으로 되찾겠다고 결심한 황자는 유럽에서 전쟁과 공황을 자산으로 바꾸고, 돌아와 총독부의 장부를 통째로 먹어 치운다.",
    "start_year": 1907,
    "end_year": 1938,
}

STARTER_COMPANY = {
    "name": "하우스 오브 강윤",
    "state": "황실 내부 비밀 금고와 유학생 명분만 남은 미약한 사적 자산 네트워크",
    "assets": [
        "황실 금고 열쇠 일부",
        "헤이그 밀사 경로에 얽힌 인맥",
        "중립국 유학 명분",
        "회귀자가 아는 전쟁·공황의 타이밍",
    ],
    "liabilities": [
        "통감부 감시",
        "공식 권력 부재",
        "황실 내부 불신",
        "합방 전까지의 촉박한 시간",
    ],
}

SETTING = {
    "group_background": "대한제국 붕괴와 일제 식민지화, 1차대전, 전간기 해운 붐, 대공황, 만주 진출, 국가총동원까지 이어지는 격변기 동아시아와 유럽 금융권이 무대다. 조선을 지배하는 것은 군복만이 아니라 선하증권, 창고증권, 채권, 담보, 외환 허가와 같은 문서다.",
    "execution_doctrine": "명분보다 병목, 충성보다 소유권, 독립보다 현금흐름을 먼저 쥔다.",
    "starter_company": STARTER_COMPANY,
}

PROTAGONIST = {
    "name": PROTAGONIST_NAME,
    "status": "대한제국 황실의 서출 황자",
    "public_image": "유학생으로 내보내면 무력해질 애매한 황족",
    "true_strength": "황실 내부 자산 흐름과 식민지 장부의 약점을 동시에 알고, 전쟁과 공황의 시간을 자산배치로 바꾸는 회귀자",
    "true_weakness": "감정으로 움직이면 모든 판을 잃는다는 걸 알아 지나치게 냉혹해지고, 사람을 쓰더라도 끝내 믿지는 못한다.",
    "initial_goal": "1907년에서 1910년 사이 황실의 이동 가능한 자산을 중립국으로 먼저 빼내 생존 자본을 만든다.",
    "mid_goal": "유럽 금융과 해운, 보험, 군수 계약으로 조선 밖에서 조선을 살 돈줄을 만든다.",
    "final_goal": "총독부, 군부, 친일 재벌이 쥔 철도와 은행, 광산, 창고, 언론의 소유권과 담보권을 자기 계열 아래로 묶는다.",
    "age_at_start": 17,
}

SOURCE_MANIFEST = {
    "work_id": WORK_ID,
    "genre": "alt_history",
    "catalog_scope": "AH-*",
    "core_sources": [ROYAL, EU, COLONIAL],
    "support_sources": [BANK_FX, MARINE, RAIL, HUBS],
    "why_selected": {
        "opening": "헤이그 특사 파문, 한국은행 설립, 역둔토 국유화, 합방 전 데드라인을 이용한 황실 자산 반출",
        "midgame": "로테르담·앤트워프·취리히·런던의 선적금융, 재보험, 외환, BIS, 금본위 변동, 대공황",
        "payoff": "동양척식, 조선은행, 창고증권, 철도 예정선, 만주 금융 분리, 국가총동원 아래의 식민지 자산 인수",
    },
}

DB_PREP_PACKET = {
    "history_engine": [
        "1907년 헤이그 특사 실패와 고종 강제 퇴위는 황실 독자 행동력의 붕괴이자 비공식 자산 이동의 마지막 창을 뜻한다.",
        "1909년 한국은행 설립과 1910년 합방은 공식 금융 경로를 일본 행정 아래로 묶는 데드라인이다.",
        "1914년 전쟁 발발, 1915년 루시타니아, 1917년 잠수함전은 해운과 보험을 전쟁 자산으로 바꾼다.",
        "1925년 금본위 복귀, 1929~1932년 대공황, 1931년 파운드 절하, 1934년 스위스 은행비밀법은 유럽 자산배치의 핵심 타이밍이다.",
        "1931년 창고증권 제도화, 1935년 통화권 분리, 1937년 만주 20지점 이관, 1938년 국가총동원은 식민지 장부를 다시 쓰는 계기다.",
    ],
    "business_engine": [
        "해운-보험-재보험-선적금융은 한 몸처럼 움직인다.",
        "조선에서는 토지보다 등기, 창고증권, 측선 허가, 철도 예정선 도면, 담보 실행권이 실제 돈이 된다.",
        "만주 특수는 현지 본체보다 조선 후방 창고, 선로, 전력, 제분, 제지 자산을 쥘 때 더 안정적이다.",
    ],
    "npc_engine": [
        "황실 회계선, 로테르담 선주, 취리히 자산관리인, 상하이 무기상, 경성 등기 변호사, 총독부 재무관, 조선은행 회계선, 오쿠라구미 투자책임자, 마쓰오카 요스케를 핵심 축으로 쓴다.",
    ],
    "crisis_engine": [
        "공식 경로 차단, 영일동맹 외교 리스크, 전쟁위험 할증, 운임 붕괴, 금본위 붕괴, 담보 재평가, 중복 담보, 전시 동원, 지점 이관이 장기 위기 사다리다.",
    ],
    "location_engine": [
        "경성, 인천, 부산, 로테르담, 앤트워프, 런던, 취리히, 바젤, 상하이, 대련, 신의주, 봉천을 기능별로 분리해 쓴다.",
    ],
}

NPC_STATE_START = {
    "한예담": "황실 장부를 몰래 옮겨 적는 궁중 회계 보조",
    "헨드릭 판데르벨트": "동양 황족을 가볍게 보는 로테르담 선주",
    "소피 아들러": "고객의 출신보다 돈의 냄새를 먼저 맡는 취리히 자산관리인",
    "최무진": "어느 깃발 아래서도 무기를 팔 수 있는 상하이 중개상",
    "민도식": "아버지의 땅을 지키려다 채무에 눌린 경성 지주 2세",
    "이토 마사유키": "황실 자산을 장부째 일본 손아귀에 넣으려는 통감부 재무관",
    "에드워드 블레이크": "동양 왕자를 장난감쯤으로 보는 영국 해운 재벌 후계자",
    "구도 겐이치": "총독부의 문서와 인허가를 쥔 경제국 관료",
    "오쿠라 다카시": "오쿠라구미의 조선·만주 투자 책임자",
    "윤창식": "등기와 경매 공고를 돈으로 읽는 경성 변호사",
    "마쓰오카 요스케": "제국의 외교지도를 자산지도로 보는 일본 정치인",
}

NPC_STAGE_TEXT = {
    "한예담": [
        "궁 안의 금고와 장부 위치를 함께 숨기는 공범",
        "황실 잔존 자산을 해외 송금 구조로 바꾸는 실무선",
        "경성과 상하이를 잇는 비공식 회계 라인의 관리자",
        "총독부 장부의 빈칸을 읽어내는 내부 설계자",
    ],
    "헨드릭 판데르벨트": [
        "이강윤에게 배를 빌려주며 수익을 먼저 보는 선주",
        "강윤 자본에 점점 기대는 유럽 물류 파트너",
        "지분과 노선을 동시에 빼앗길 위기에 선 채 거래를 이어 가는 종속 동맹",
        "로테르담 네트워크를 강윤 계열 아래 편입시키는 매개",
    ],
    "소피 아들러": [
        "위험한 자산도 구조만 좋으면 맡아 주는 취리히 창구",
        "스위스 계좌와 우회 법인을 묶는 핵심 파트너",
        "전쟁과 공황을 거치며 강윤 자산의 최종 정산 창구가 되는 동반자",
        "조선 귀환 이후에도 유럽 자산을 끝까지 묶어 두는 최후의 보관인",
    ],
    "최무진": [
        "현금과 총알을 동시에 굴리는 상하이 브로커",
        "연락선과 군수품 목록을 강윤에게 먼저 넘기는 정보상",
        "더러운 일은 처리하되 강윤 손에 칼을 쥐여 주지 않는 외부 실행선",
        "전시 조달 계약을 강윤에게 유리한 담보 구조로 엮는 하부망 책임자",
    ],
    "민도식": [
        "가문의 지분과 토지를 지키지 못해 휘청이는 경성 지주 2세",
        "강윤의 자본에 기대 가명 법인을 돌리는 현지 명의인",
        "지주 사회 내부 정보를 강윤 쪽으로 흘리는 경성 거점",
        "조선 내 배당과 월세 수입을 걷는 현지 집사",
    ],
    "이토 마사유키": [
        "황실 자산의 마지막 흐름을 틀어막으려는 통감부 재무관",
        "강윤의 유럽 자금줄을 뒤늦게 눈치채는 초반 적대자",
        "합방 이후에도 이왕직 장부로 반격하려는 집착의 관료",
        "초반에 놓친 한 번의 금고 열쇠 때문에 끝내 패배하는 구세력",
    ],
    "에드워드 블레이크": [
        "동양 왕자를 싸게 집어삼키려는 영국 해운 후계자",
        "운임과 보험 시장에서 강윤에게 번번이 한발 늦는 경쟁자",
        "대공황을 맞고 강윤에게 부두와 선복을 넘기는 패자",
        "후반엔 강윤을 유럽 해운 질서의 동등한 주인으로 인정한다.",
    ],
    "구도 겐이치": [
        "총독부 서류와 인허가를 칼처럼 쓰는 경제국 관료",
        "철도 예정선과 담보 실행 문서를 지렛대로 버티는 적수",
        "전시 동원 아래서도 장부만은 자기 손에 남길 수 있다고 믿는 관료",
        "강윤이 이미 조선의 현금흐름을 장악했음을 늦게 깨닫는 최후의 적",
    ],
    "오쿠라 다카시": [
        "오쿠라구미의 돈으로 조선과 만주를 묶으려는 투자책임자",
        "강윤과 같은 자산을 노리며 담보권 싸움을 벌이는 경쟁자",
        "강윤과 군수·광산·전력 자산 포트폴리오를 두고 충돌하는 중후반 적",
        "결국 더 비싼 가격을 써도 병목을 못 쥔 쪽이 진다는 교훈이 되는 패자",
    ],
    "윤창식": [
        "경매 공고와 등기부를 돈보다 빨리 읽는 경성 변호사",
        "강윤의 가명 법인과 담보 실행을 설계하는 법률 실무자",
        "문서 한 장으로 역세권과 창고권을 넘기는 기술자",
        "강윤이 황제 대신 채권자가 되는 길을 완성하는 서류 설계자",
    ],
    "마쓰오카 요스케": [
        "제국 외교를 무역노선과 자산 배치로 읽는 정치가",
        "대륙 구상을 강윤과 거래하면서도 언젠가 통제하려는 국가 권력",
        "전시 국가와 사적 자본이 서로를 이용하는 국면의 상징",
        "조선의 수익을 위해선 강윤을 완전히 배제할 수 없음을 인정하는 인물",
    ],
}

ARCS: list[dict[str, Any]] = []

CAPITAL_START = 4
CAPITAL_DELTAS = [
    0, 2, 2, 2, 2, 2, 0, 6, 8, 8,
    10, 14, 12, 16, -12, 20, 24, 28, 36, 56,
    36, 40, 50, 60, -40, 70, 80, 90, 100, 114,
    70, 80, 90, 110, -50, 120, 140, 160, 190, 210,
    160, -80, 200, 220, 240, 260, -60, 300, 280, 320,
    300, 360, 400, 440, -240, 520, 600, 640, 720, 860,
    500, 600, 700, 760, -260, 1000, 1120, 1240, 1280, 1060,
]

ARCS.extend(
    [
        {
            "arc_id": "ARC-01",
            "title": "황실 금고를 빼돌리다",
            "block_range": "1-10",
            "time_window": "1907년 8월~1910년 8월",
            "front_sectors": ["황실 자산", "외교 경로", "금·외환"],
            "support_sectors": ["무역/상사", "중립국 유학", "비공식 송금"],
            "main_opponents": ["이토 마사유키", "통감부 재무선", "황실 내부 배신자"],
            "new_npcs": ["한예담", "이토 마사유키"],
            "emotion_curve": "독살의 기억 -> 회귀 -> 금고 선점 -> 탈출",
            "quiet_blocks": [6],
            "defeat_blocks": [],
            "knowledge_used": "헤이그 특사 실패, 한국은행 설립, 합방 시한을 미리 아는 회귀 지식",
            "default_sources": source_binding([ROYAL], [BANK_FX]),
            "default_partner": "헤이그 밀사 경로",
            "blocks": [
                slot(
                    "피 맛과 계약서",
                    "1936년 취리히에서 독살당한 이강윤이 1907년 8월 궁으로 돌아와 이번 생의 첫 원칙을 세운다.",
                    "1907년 8월 3일",
                    "취리히 호텔 스위트룸 / 경운궁 침전",
                    "황실 자산",
                    "회귀 후 자산 선점 선언",
                    "죽기 전에 본 계약서 문구와 독의 시간차를 기억한 채 금고부터 챙긴다.",
                    "이토 마사유키",
                    ["한예담"],
                    hist("헤이그 특사 파견과 고종 강제 퇴위", 1907, "퇴위 압박이 시작되기 전 황실 자산을 손댈 마지막 며칠을 확보한다.", ROYAL),
                    "rebirth",
                    9,
                    8,
                    "3일",
                    "회귀 우위로 첫 주도권을 되찾는다.",
                    foreshadow=["Block 69에서 취리히 독살의 배후 문장이 다시 열린다.", "Block 3의 금고 열쇠는 Block 68의 실소유주 선언까지 이어진다."],
                    sources=source_binding([ROYAL], [BANK_FX]),
                    partner="헤이그 밀사 잔류 인맥",
                ),
                slot(
                    "거울 속 열일곱",
                    "열일곱 황자의 얼굴과 몸으로 깨어난 강윤이 황실 내부의 시선과 동선을 다시 읽는다.",
                    "1907년 8월 초",
                    "경운궁 후원과 내장원 복도",
                    "황실 자산",
                    "궁중 동선 은닉",
                    "감시선이 아직 느슨한 틈에 통감부보다 먼저 금고와 장부의 위치를 재조합한다.",
                    "이토 마사유키",
                    ["한예담"],
                    hist("정미7조약 체결과 차관 정치 시작", 1907, "차관 정치가 본격화되기 전 궁내부 문서를 갈라놓아야 한다.", ROYAL),
                    "resolve",
                    6,
                    6,
                    "2일",
                    "황실 안에서 움직일 숨통을 확보한다.",
                    foreshadow=["Block 31에서 경성 가명 법인이 궁중 동선 은닉과 같은 논리로 다시 작동한다."],
                    callback=["Block 1에서 세운 '금고부터 챙긴다'는 원칙을 실제 행동으로 옮긴다."],
                ),
                slot(
                    "금고 열쇠",
                    "한예담과 손잡고 황실 금고의 열쇠와 별도 장부를 먼저 확보한다.",
                    "1907년 8월 중순",
                    "내장원 금고방",
                    "황실 자산",
                    "금고 분리 확보",
                    "보석과 금괴보다 장부와 열쇠를 함께 쥐어야 이후 송금 구조까지 설계할 수 있다고 판단한다.",
                    "황실 내부 배신자",
                    ["한예담"],
                    hist("역둔토 국유지 편입과 황실 토지 자산 최종 해체", 1908, "토지가 묶이기 전 이동 가능한 현금성 자산만 떼어낸다.", ROYAL),
                    "alliance",
                    7,
                    7,
                    "4일",
                    "휴대 가능한 황실 자산의 실체를 손에 넣는다.",
                    foreshadow=["Block 5의 마지막 추수, Block 66의 조선 월세는 모두 이 금고 장부에서 출발한다."],
                ),
                slot(
                    "헤이그의 잔금",
                    "헤이그 특사 실패 뒤 남은 외교 경비와 인맥을 자산 반출용 통로로 바꾼다.",
                    "1907년 8월 하순",
                    "한성 / 블라디보스토크행 연락 사무소",
                    "외교 경로",
                    "밀사 경로 전용",
                    "외교 실패로 버려진 밀사 경로가 오히려 비공식 송금엔 가장 안전하다는 점을 이용한다.",
                    "이토 마사유키",
                    ["한예담"],
                    hist("헤이그 특사 파견과 고종 강제 퇴위", 1907, "밀사 경로를 외교가 아니라 송금 경로로 재해석한다.", ROYAL),
                    "deception",
                    7,
                    7,
                    "1주",
                    "죽은 외교선을 살아 있는 자금선으로 바꾼다.",
                    foreshadow=["Block 16의 중립국 계좌, Block 52의 스위스 비밀계좌는 모두 이 우회 경로를 확장한 결과다."],
                ),
                slot(
                    "역둔토 마지막 추수",
                    "국유지로 넘어가기 전 역둔토 소작료를 최대한 현금으로 긁어모은다.",
                    "1908년 봄",
                    "경기·황해 역둔토 수납 거점",
                    "황실 자산",
                    "소작료 현금화",
                    "땅은 못 가져가도 마지막 소작료는 가져갈 수 있다는 계산으로 지방 수납선을 먼저 장악한다.",
                    "통감부 재무선",
                    ["한예담"],
                    hist("역둔토 국유지 편입과 황실 토지 자산 최종 해체", 1908, "토지 본체 대신 마지막 현금흐름을 수거한다.", ROYAL),
                    "pressure",
                    7,
                    8,
                    "3주",
                    "움직일 수 없는 땅을 움직일 수 있는 금으로 바꾼다.",
                    foreshadow=["Block 32의 토지조사 뒤편, Block 44의 쌀값 한 칸에서 이 장부가 다시 쓰인다."],
                ),
                slot(
                    "군대 해산의 밤",
                    "군대 해산과 정미의병의 혼란 속에 금고 분산분을 개항장으로 옮긴다.",
                    "1907년 9월",
                    "한성 남문 밖 / 인천 항구 창고",
                    "비공식 송금",
                    "혼란기 운송",
                    "혼란이 곧 감시의 공백이라는 사실을 알고 가장 시끄러운 밤에 가장 조용한 짐을 뺀다.",
                    "이토 마사유키",
                    ["한예담"],
                    hist("대한제국 군대 해산과 정미의병 봉기", 1907, "물리적 혼란을 운송 은폐막으로 사용한다.", ROYAL),
                    "foreshadowing",
                    5,
                    6,
                    "2일",
                    "실탄보다 먼저 움직이는 병참 감각을 익힌다.",
                    callback=["Block 4에서 살린 밀사 경로를 이번엔 인천 창고 운송선으로 연결한다."],
                ),
                slot(
                    "백동화 대신 금",
                    "화폐 정리 사업의 기억을 이용해 백동화 대신 금과 파운드 자산으로 갈아탄다.",
                    "1908년 하반기",
                    "제물포 상사 객주",
                    "금·외환",
                    "화폐 전환 선매매",
                    "액면가보다 가치가 낮아질 화폐를 들고 있느니 금과 파운드로 바꿔 중립국으로 넘기는 편이 낫다고 본다.",
                    "통감부 재무선",
                    ["한예담"],
                    hist("대한제국 화폐 정리 사업 백동화 교환 비율", 1905, "백동화 가치 하락을 거꾸로 이용해 금 매집 시점을 앞당긴다.", BANK_FX),
                    "realization",
                    6,
                    5,
                    "10일",
                    "황실 비자금의 통화 형태를 제국 밖 기준으로 바꾼다.",
                    foreshadow=["Block 42의 파운드 절하, Block 56의 통화권 분리에서 다시 외환 판단력이 시험된다."],
                ),
                slot(
                    "제일은행 밖",
                    "한국은행 설립이 다가오자 공식 금융권 바깥에서 자산을 세탁하고 분산한다.",
                    "1909년 초",
                    "한성 제일은행 앞 / 민간 상사회관",
                    "금·외환",
                    "비공식 송금 구조",
                    "한국은행과 조선은행 체계에 잡히는 순간 끝이라는 걸 알기에 은행 밖 장부와 상사 어음을 활용한다.",
                    "이토 마사유키",
                    ["한예담"],
                    hist("한국은행 설립과 조선 금융 체계 재편", 1909, "중앙은행 전환 전에 비공식 자산을 제도권 밖으로 뺀다.", ROYAL),
                    "pressure",
                    7,
                    7,
                    "2주",
                    "은행 밖에서만 가능한 마지막 세탁을 끝낸다.",
                ),
                slot(
                    "로테르담행 학생",
                    "네덜란드 유학생 명분으로 강윤 자신과 자산의 일부를 로테르담으로 보낸다.",
                    "1909년 말",
                    "인천항 / 로테르담행 객선",
                    "무역/상사",
                    "유학생 위장 출국",
                    "황족 망명은 막혀도 유학생 출국은 아직 막히지 않았다는 제도 틈을 쓴다.",
                    "이토 마사유키",
                    ["한예담", "헨드릭 판데르벨트"],
                    hist("영일동맹에 따른 중립국 경유 자산 이전의 외교적 제약", 1907, "영국 대신 네덜란드와 스위스로 분산 예치를 택한다.", ROYAL),
                    "breakthrough",
                    8,
                    7,
                    "3주",
                    "자산뿐 아니라 자신까지 제국 밖으로 빼낸다.",
                    foreshadow=["Block 11의 화물선 매입, Block 43의 로테르담 저점 매수는 모두 이 출국으로 가능해진다."],
                ),
                slot(
                    "합방 전야 장부",
                    "합방 직전 남은 자산을 장부상으론 사라지게 만들고 실물은 이미 유럽으로 넘긴다.",
                    "1910년 8월",
                    "경성 / 로테르담 정산창구",
                    "비공식 송금",
                    "합방 직전 장부 절단",
                    "합방 이후엔 어떤 공식 경로도 남지 않으므로 장부상 손실로 보이게 하고 실물은 살아 있게 만든다.",
                    "이토 마사유키",
                    ["한예담", "소피 아들러"],
                    hist("한일합방조약 체결과 대한제국 소멸", 1910, "합방 공포 직전까지 자산 이전을 마감한다.", ROYAL),
                    "triumph",
                    8,
                    8,
                    "5일",
                    "합방을 막진 못해도 합방 뒤 쓸 실탄을 지킨다.",
                    callback=["Block 8에서 은행 밖으로 뺀 돈이 결국 합방 당일에도 살아남는다."],
                ),
            ],
        },
        {
            "arc_id": "ARC-02",
            "title": "전쟁은 배를 가진 놈이 먹는다",
            "block_range": "11-20",
            "time_window": "1911년 1월~1918년 11월",
            "front_sectors": ["해운", "보험", "선적금융"],
            "support_sectors": ["재보험", "중립국 계좌", "군수 하청"],
            "main_opponents": ["에드워드 블레이크", "영국 해운 카르텔"],
            "new_npcs": ["헨드릭 판데르벨트", "소피 아들러"],
            "emotion_curve": "선복 확보 -> 전쟁 발발 -> 보험 전쟁 -> 병목 장악",
            "quiet_blocks": [],
            "defeat_blocks": [15],
            "knowledge_used": "전쟁위험요율, 잠수함전, 전시 보험 판례를 미리 알고 선복과 보험을 함께 산다.",
            "default_sources": source_binding([EU], [MARINE]),
            "default_partner": "로테르담 선주조합",
            "blocks": [
                slot("헐값의 화물선", "대륙 항로에서 밀려난 낡은 화물선을 헨드릭에게서 싸게 넘겨받는다.", "1911년 봄", "로테르담 조선소", "해운", "노후 화물선 매입", "배 그 자체보다 선하증권과 보험을 묶을 그릇을 먼저 사들인다.", "에드워드 블레이크", ["헨드릭 판데르벨트"], hist("영국 해상보험법(Marine Insurance Act 1906) 제정", 1906, "영국법 준거 보험 구조를 미리 이해한 채 선박 매입 계약을 짠다.", MARINE), "alliance", 6, 6, "2주", "남들이 버린 선복에서 첫 유럽 현금흐름을 만든다.", foreshadow=["Block 20의 빈 선복, Block 23의 전후 해운 붐은 이 첫 선박에서 시작된다."]),
                slot("로테르담 선하증권", "강윤은 배보다 선하증권과 화환어음이 더 오래 간다는 걸 증명하려 한다.", "1912년 여름", "로테르담 항만 창고", "선적금융", "선하증권 담보 대출", "화물을 담보로 돈을 먼저 당기고, 돈으로 다시 배를 돌리는 순환을 만든다.", "에드워드 블레이크", ["헨드릭 판데르벨트"], hist("항만에서 은행으로 이어지는 선적서류 담보 구조", 1912, "로테르담 선하증권을 런던 인수어음 시장과 연결한다.", EU), "realization", 6, 6, "10일", "배를 가진 선주에서 서류를 가진 금융업자로 한발 옮긴다.", foreshadow=["Block 28의 조선 관련 어음, Block 40의 총독부 채권자 구조가 여기서 예행연습된다."]),
                slot("앤트워프 재보험", "앤트워프 재보험 브로커와 손잡아 해상위험을 다시 쪼갠다.", "1913년 초", "앤트워프 보험 중개거리", "보험", "재보험 세션 체결", "강윤은 위험을 혼자 먹지 않고 런던과 대륙에 흩뿌리는 쪽이 더 오래 산다는 걸 안다.", "영국 해운 카르텔", ["소피 아들러"], hist("보험에서 재보험으로 이어지는 세션 구조", 1913, "앤트워프와 런던을 잇는 재보험 네트워크를 자기 배와 묶는다.", MARINE), "alliance", 6, 6, "2주", "배 하나의 위험을 여러 도시의 돈으로 나눠 먹는 법을 익힌다."),
                slot("전쟁 전 선복", "사라예보 이전 마지막 평온 속에서 강윤은 전쟁 전 선복을 장기용선으로 잠근다.", "1914년 6월", "런던 발틱거래소", "해운", "장기용선 선매입", "평온할 때 잠가 둔 선복이 전쟁이 시작되는 순간 가장 비싼 자산이 된다고 본다.", "에드워드 블레이크", ["헨드릭 판데르벨트", "소피 아들러"], hist("전시 이전 선복 확보", 1914, "전쟁 전 정상 운임으로 장기 계약을 잠근다.", EU), "countdown", 8, 8, "3주", "전쟁 전 마지막 평시 가격을 자기 것으로 만든다.", foreshadow=["Block 15의 모라토리엄, Block 17의 전쟁위험요율에서 이 계약이 폭발한다."]),
                slot("모라토리엄의 아침", "전쟁 발발과 함께 런던의 지급정지가 걸리며 계약과 어음이 동시에 얼어붙는다.", "1914년 8월", "런던 시티 정산실", "선적금융", "전시 유동성 방어", "이미 잠가 둔 선복이 있어도 결제가 멈추면 배는 떠도 돈이 돌지 않는다는 현실을 맞는다.", "영국 해운 카르텔", ["소피 아들러"], hist("전시 모라토리엄과 금융시장 동결", 1914, "전쟁 초기 지급정지 국면에서 중립국 계좌로 유동성을 옮긴다.", EU), "defeat", 8, 9, "6일", "선복은 살아도 결제선이 멈추면 패배한다는 사실을 배운다.", callback=["Block 14에서 잠근 선복이 있어도 현금창구가 닫히면 아무 소용 없다는 점이 드러난다."]),
                slot("중립국 계좌", "영국 시장이 얼어붙자 취리히와 암스테르담의 중립국 계좌를 본격 가동한다.", "1914년 가을", "취리히 프라이빗 뱅크", "금·외환", "중립국 분산 예치", "파운드보다 계좌 관할권이 중요해진 순간, 강윤은 스위스와 네덜란드에 결제선을 이중으로 깐다.", "영국 해운 카르텔", ["소피 아들러"], hist("중립국 금융축의 가치 상승", 1914, "영국 대신 취리히·로테르담 결제축을 만든다.", EU), "breakthrough", 8, 7, "2주", "유럽 전시 결제선의 우회도로를 확보한다.", foreshadow=["Block 51의 BIS 복도, Block 52의 은행비밀법이 이 계좌 구조를 확장한다."]),
                slot("전쟁위험요율", "강윤은 전쟁위험 할증률을 읽고 배를 띄울지 세울지 결정하는 쪽으로 올라선다.", "1915년 초", "런던 Lloyd's 인접 보험실", "보험", "전쟁위험 인수", "운임보다 보험료가 큰 돈이 되는 순간을 보고 직접 인수 대신 브로커·재보험 지위를 먼저 먹는다.", "에드워드 블레이크", ["소피 아들러", "헨드릭 판데르벨트"], hist("전쟁위험 가산료 체제", 1915, "항해별 위험요율을 기반으로 선박 운항 자체를 통제한다.", MARINE), "escalation", 8, 8, "2주", "배를 가진 자가 아니라 위험표를 쥔 자가 시장을 지배한다."),
                slot("잠수함 보험", "루시타니아 이후 강윤은 잠수함전을 보험 계약 문구로 계산하기 시작한다.", "1915년 5월", "런던 / 앤트워프 공동정산선", "보험", "잠수함전 면책 분리", "일반 해상위험과 전쟁위험의 경계선을 먼저 그어 두고, 그 틈에서 브로커 수수료와 정보 우위를 동시에 챙긴다.", "영국 해운 카르텔", ["소피 아들러"], hist("루시타니아호 침몰과 전쟁보험 분쟁", 1915, "면책 조항 해석 차이를 이용해 클레임 협상권을 쥔다.", MARINE), "deception", 7, 8, "10일", "누가 돈을 내는지 정하는 문장 하나가 배 한 척 값이 된다는 걸 증명한다."),
                slot("호송선단 계약", "1917년 잠수함전이 극심해지자 강윤은 호송선단 우선 배정 계약에 매달린다.", "1917년 봄", "런던 해군 수송 보조창구", "해운", "호송 우선권 계약", "배를 더 사는 대신 살아서 도착할 배를 확보하는 쪽으로 전략을 바꾼다.", "영국 해운 카르텔", ["헨드릭 판데르벨트"], hist("1917년 연합국 상선 격침 톤수 급증", 1917, "격침표를 바탕으로 안전한 회차와 보험조건을 계산한다.", EU), "pressure", 7, 8, "3주", "전쟁 후반엔 선박 수보다 안전 회차가 더 비싸다는 사실을 이용한다."),
                slot("빈 선복이 금이 된다", "1918년 말 종전 직전에도 살아남은 선복은 곧 금 그 자체가 된다.", "1918년 11월", "로테르담 부두", "해운", "전시 잔존 선복 매각", "끝까지 버틴 선복을 비싼 운임과 높은 재보험료가 붙은 상태로 정리해 현금으로 전환한다.", "에드워드 블레이크", ["헨드릭 판데르벨트", "소피 아들러"], hist("전시 말기 선복 부족", 1918, "살아남은 선박과 보험 관계를 한꺼번에 비싸게 정리한다.", EU), "triumph", 9, 8, "2주", "강윤은 전쟁이 끝나기도 전에 전후 호황에 쓸 자본을 현금으로 바꾼다.", callback=["Block 11의 낡은 화물선이 Block 20에서는 황금 선복이 된다."]),
            ],
        },
        {
            "arc_id": "ARC-03",
            "title": "총보다 증권이 오래 간다",
            "block_range": "21-30",
            "time_window": "1918년 11월~1924년 12월",
            "front_sectors": ["은행/금융", "해운", "식민지 채권"],
            "support_sectors": ["상하이 연락선", "조선 관련 어음", "취리히 예치"],
            "main_opponents": ["에드워드 블레이크", "유럽 브로커 연합"],
            "new_npcs": ["최무진"],
            "emotion_curve": "전후 정산 -> 투기 정점 -> 폭락 -> 은행 설립",
            "quiet_blocks": [],
            "defeat_blocks": [25],
            "knowledge_used": "전후 해운 붐과 1920년 운임 붕괴, 조선은행 부실 장부, 상하이 외환 혼란을 한 번에 연결한다.",
            "default_sources": source_binding([EU], [BANK_FX]),
            "default_partner": "취리히 프라이빗 뱅크",
            "blocks": [
                slot("격침표와 생존표", "강윤은 전시 격침 통계와 생존 선박 데이터를 손에 쥔 채 전후 정산을 시작한다.", "1918년 겨울", "런던 해운보험 기록실", "은행/금융", "전후 손실표 정산", "남들에겐 슬픔의 목록이지만 강윤에겐 다음 가격표를 정하는 데이터다.", "유럽 브로커 연합", ["소피 아들러"], hist("전후 손실 데이터 집계", 1918, "격침표를 전후 자산평가 자료로 전환한다.", EU), "aftermath", 5, 6, "2주", "죽은 배들의 목록이 살아남은 자산의 가격을 정한다."),
                slot("정전 뒤 매각장", "정전 직후 버려지는 전시 자산을 강윤은 경매장에서 주워 담는다.", "1919년 초", "런던 해운 자산 매각장", "은행/금융", "전후 부실자산 매입", "전쟁이 끝났다고 다 같은 가격을 받을 수 없는 자산만 골라낸다.", "에드워드 블레이크", ["소피 아들러"], hist("종전 후 전시 자산 정리", 1919, "손실을 견디지 못한 선주들의 매각장을 저가 매수의 창으로 본다.", EU), "opportunity", 6, 6, "3주", "정전은 평화가 아니라 할인판매의 개시라는 걸 보여 준다."),
                slot("전후 해운 붐", "억눌린 수요가 폭발하자 강윤은 살아남은 선복을 가장 비싼 시기에 돌린다.", "1919년 하반기", "로테르담 부두 / 발틱 운임시장", "해운", "전후 용선 재배치", "배를 오래 들고 있는 대신 가장 비싼 회차에 다시 태워 현금 회수를 앞당긴다.", "에드워드 블레이크", ["헨드릭 판데르벨트"], hist("전후 해운 붐과 선박 투기", 1919, "운임 급등을 이용해 용선료와 보험료를 동시 회수한다.", EU), "triumph", 8, 7, "1달", "전후 광풍을 남들보다 먼저 현금화한다.", foreshadow=["Block 24의 최고점 매도, Block 25의 운임 붕괴는 같은 파동의 양 끝이다."]),
                slot("가장 비싼 선박", "누구나 더 오를 거라 믿을 때 강윤은 가장 비싼 배를 가장 먼저 판다.", "1920년 초", "앤트워프 매각 협상실", "해운", "선박 고점 매도", "배에 애정을 두지 않고 회수 가능한 최대 가격표만 본다.", "에드워드 블레이크", ["헨드릭 판데르벨트"], hist("중고선 가격 3~5배 급등", 1920, "선박 버블 고점에서 실물을 종이로 바꾼다.", EU), "deception", 7, 7, "2주", "광풍의 중심에서 한발 먼저 빠져나온다."),
                slot("운임 붕괴", "1920년 후반 운임이 무너지며 떠들썩하던 선주들이 순식간에 채권자 앞에 선다.", "1920년 말", "로테르담 채권자 회의실", "은행/금융", "운임 폭락 대응", "시장 붕괴를 알았어도 너무 일찍 팔지 못한 일부 선복과 대출 라인이 흔들리며 강윤도 손실을 감수한다.", "유럽 브로커 연합", ["헨드릭 판데르벨트"], hist("전후 해운 붐과 선박 투기", 1920, "운임 붕괴 구간에서 배 대신 채권자 지위를 확보하는 쪽으로 선회한다.", EU), "defeat", 8, 8, "1달", "시장을 이겨도 파동 전체를 거스를 수는 없다는 대가를 치른다.", callback=["Block 23의 호황은 Block 25에서 그대로 반대편 칼날이 된다."]),
                slot("취리히 머천트뱅크", "강윤은 배에서 번 돈을 취리히의 사설 은행 구조로 옮겨 자체 금융 회로를 만든다.", "1921년 봄", "취리히 프라이빗 뱅크", "은행/금융", "머천트뱅크 설립", "운임이 아니라 어음과 담보를 먹는 쪽이 더 오래 간다는 결론으로 선회한다.", "유럽 브로커 연합", ["소피 아들러"], hist("바젤-취리히 금융축 부상", 1921, "개별 선박이 아니라 거래 전체를 인수하는 금융축으로 이동한다.", EU), "breakthrough", 8, 7, "6주", "강윤은 선주가 아니라 거래를 인수하는 사람으로 격을 바꾼다.", foreshadow=["Block 51의 BIS 복도, Block 52의 은행비밀법이 이 축을 확장한다."]),
                slot("상하이 연락선", "상하이 연락선과 최무진을 통해 강윤은 동아시아 어음과 군수품 목록을 받기 시작한다.", "1922년 초", "상하이 조계 연락선 선창", "무역/상사", "동아시아 연락선 지분", "조선으로 바로 들어가지 않고 상하이와 조계 금융을 경유해 정보를 먹는다.", "유럽 브로커 연합", ["최무진"], hist("중국 은행·무역 결제 혼란과 상하이 조계 금융 허브", 1922, "상하이 연락선과 조계 자금을 통해 조선 관련 거래를 우회 포착한다.", BANK_FX), "alliance", 7, 6, "3주", "조선을 직접 밟지 않고도 조선 돈의 냄새를 맡는 라인을 만든다."),
                slot("조선 관련 어음", "강윤은 식민지 조선 회사와 연결된 어음과 보험증권을 조용히 사 모은다.", "1923년", "취리히 / 상하이 공동정산선", "은행/금융", "식민지 어음 매집", "실물 자산에 바로 손대기보다 먼저 채권과 어음을 먹어 장부의 위쪽을 차지한다.", "유럽 브로커 연합", ["최무진", "소피 아들러"], hist("항만-은행-선적서류 담보 구조", 1923, "선적금융 문서를 통해 조선 관련 기업의 부실을 먼저 잡는다.", EU), "pressure", 7, 7, "1달", "조선을 직접 사기 전에 조선을 담보로 잡은 종이를 먼저 모은다."),
                slot("조선은행 부실표", "강윤은 조선은행의 부실채권과 감자 압력을 미리 읽고 경성 복귀 준비를 끝낸다.", "1924년", "취리히 분석실", "은행/금융", "부실채권 선별", "식민지 본체보다 은행 장부가 더 빨리 흔들린다는 판단 아래 회수 가능한 채권부터 골라낸다.", "구도 겐이치", ["소피 아들러"], hist("조선은행 부실채권 정리와 감자", 1924, "52.2% 불량채권 비율이 주는 공포를 이용해 후일 담보권 매집 명부를 만든다.", COLONIAL), "realization", 6, 6, "2주", "경성에 돌아갈 명분이 아니라 장부를 준비한다.", foreshadow=["Block 55의 조선은행 감자표, Block 60의 총독부 담보표가 여기서 이어진다."]),
                slot("조선을 담보로", "강윤은 결국 조선을 구하는 대신 조선을 담보로 잡기로 결심한다.", "1924년 겨울", "취리히 자산관리실", "은행/금융", "식민지 담보 포트폴리오 설계", "국가와 민족이 아니라 담보권과 배당권의 언어로 조선을 읽어야 이길 수 있다고 결론내린다.", "구도 겐이치", ["소피 아들러", "최무진"], hist("동아권업주식회사 명목자본과 불입자본 괴리", 1921, "실물보다 장부가 먼저 부풀어 오른 식민지 회사를 담보권 인수 대상으로 본다.", COLONIAL), "triumph", 8, 7, "2주", "경성 복귀는 감상이 아니라 포트폴리오 실행 단계가 된다.", callback=["Block 22의 매각장, Block 28의 어음 매집이 모두 경성 복귀 설계도로 수렴한다."]),
            ],
        },
    ]
)


def ordered_arcs() -> list[dict[str, Any]]:
    return sorted(ARCS, key=lambda arc: arc["arc_id"])


def auto_relation_after(name: str, appearance_idx: int, title: str) -> str:
    stages = NPC_STAGE_TEXT.get(name, [f"{title} 이후 강윤과의 거래선이 더 짙어진다."])
    stage = stages[min(appearance_idx, len(stages) - 1)]
    return f"{title} 이후 {stage}"


def location_type(place: str) -> str:
    if "은행" in place or "정산" in place or "금융" in place:
        return "금융 거점"
    if "항" in place or "부두" in place or "선창" in place:
        return "항만 거점"
    if "철도" in place or "역" in place or "측선" in place:
        return "철도 거점"
    if "공장" in place or "광산" in place:
        return "생산 거점"
    if "총독부" in place or "도면실" in place or "열람실" in place:
        return "행정 거점"
    return "사업 거점"


def source_alias(source: str) -> str:
    mapping = {
        ROYAL: "황실 자산 장부",
        EU: "유럽 선적금융",
        COLONIAL: "식민지 담보표",
        BANK_FX: "외환 차익 구조",
        MARINE: "해상보험 문구",
        RAIL: "철도·창고 병목",
        HUBS: "상하이-만주 허브",
    }
    return mapping.get(source, source)


def weakness_for_slot(spec: dict[str, Any]) -> str:
    sector = spec["sector"]
    if sector == "해운":
        return "선박 숫자는 세어도 선복이 지나가는 결제선과 보험 문구를 같이 못 챙긴다."
    if sector == "보험":
        return "위험을 가격표로만 보고, 재보험과 정보 우위가 만드는 실제 통제권은 늦게 본다."
    if sector == "철도/인프라":
        return "도면과 허가는 알지만 측선·창고·환적처럼 돈이 머무는 시간을 과소평가한다."
    if sector == "금·외환":
        return "통화만 보고 관할권과 장부 위치가 만드는 생존 차이는 늦게 읽는다."
    return "실물과 권력을 보지만 장부 우선순위와 병목 결합이 만드는 지배력은 뒤늦게 이해한다."


def build_leverage_used(arc: dict[str, Any], spec: dict[str, Any]) -> list[str]:
    items = [
        spec["deal_type"],
        spec["method"].split(" ", 1)[0],
        arc["front_sectors"][0],
        arc["knowledge_used"].split("،" if "،" in arc["knowledge_used"] else ",")[0],
    ]
    for source in spec["sources"]["core"] + spec["sources"]["support"]:
        items.append(source_alias(source))
    if spec["partner"]:
        items.append(spec["partner"])
    return unique_in_order(items)[:5]


def format_delta(delta: int) -> str:
    return f"+{format_eok(delta)}" if delta > 0 else format_eok(delta)


def build_relationship_delta(
    spec: dict[str, Any],
    relation_tracker: dict[str, str],
    appearance_tracker: dict[str, int],
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for name in spec["targets"]:
        before = relation_tracker.get(name, f"{name}은 아직 강윤과 정식 거래를 열지 않은 상태다.")
        idx = appearance_tracker.get(name, 0)
        after = auto_relation_after(name, idx, spec["title"])
        appearance_tracker[name] = idx + 1
        relation_tracker[name] = after
        out.append({"target": name, "before": before, "after": after})
    return out


def flatten_slots() -> list[tuple[dict[str, Any], dict[str, Any], int]]:
    rows: list[tuple[dict[str, Any], dict[str, Any], int]] = []
    block_no = 1
    for arc in ordered_arcs():
        for spec in arc["blocks"]:
            rows.append((arc, spec, block_no))
            block_no += 1
    return rows


def build_treatment() -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    relation_tracker = deepcopy(NPC_STATE_START)
    appearance_tracker = {name: 0 for name in NPC_STATE_START}
    current = CAPITAL_START

    for arc, spec, block_no in flatten_slots():
        before = current
        delta = CAPITAL_DELTAS[block_no - 1]
        after = before + delta
        current = after
        rel = build_relationship_delta(spec, relation_tracker, appearance_tracker)
        event = spec["event"]
        outcome = "늘어난다" if delta > 0 else "줄어든다" if delta < 0 else "유지된다"
        reward_tail = "가격표보다 우선순위가 먼저 움직이는 판을 손에 넣는다." if delta >= 0 else "대신 다음 단계에서 더 비싼 권리를 쥘 수 있는 실패의 값을 산다."
        blocks.append(
            {
                "block_id": f"Block {block_no}",
                "title": spec["title"],
                "content": {
                    "context": f"{spec['time']}, {spec['location']}. {spec['function']} {event['name']}의 여파를 {event['how_exploited']}",
                    "event_villain": f"{spec['opponent']}은 강윤이 {spec['deal_type']}로 {spec['sector']} 주도권을 넓히기 전에 문서와 인허가, 가격표를 먼저 잠그려 든다.",
                    "solution": f"강윤은 {spec['method']} {arc['knowledge_used']}를 앞세워 {spec['deal_type']}를 구조화하고, {source_alias(spec['sources']['core'][0]) if spec['sources']['core'] else spec['sector']} 쪽 문서를 자신에게 유리한 순서로 재배치한다.",
                    "reward": f"동원 가능 자본은 {format_eok(before)}에서 {format_eok(after)}로 {outcome}. {spec['success']} {reward_tail}",
                },
                "stakes": f"이번 {spec['deal_type']}에서 밀리면 {arc['title']} 전체가 흔들리고, {spec['sector']} 병목은 {spec['opponent']} 쪽으로 넘어간다.",
                "power_shift": {
                    "protagonist": f"강윤은 {spec['method']}로 {spec['sector']}의 가격 결정권과 문서 우선순위를 더 깊게 움켜쥔다." if delta >= 0 else f"강윤은 한 차례 손실을 감수하지만 {spec['sector']}의 약한 고리를 더 분명히 본다.",
                    "antagonist": f"{spec['opponent']}은 강윤을 멈추려 했지만 병목의 본체가 무엇인지 늦게 읽는다." if delta >= 0 else f"{spec['opponent']}은 이번엔 시간을 벌지만 강윤이 어디를 노리는지까지 숨기진 못한다.",
                },
                "relationship_delta": rel,
                "foreshadow": deepcopy(spec["foreshadow"]),
                "callback": deepcopy(spec["callback"]),
                "emotional_beat": {"type": spec["emotion"], "intensity": spec["intensity"]},
                "tension_level": spec["tension"],
                "pov_character": PROTAGONIST_NAME,
                "location": {"place": spec["location"], "type": location_type(spec["location"])},
                "time_span": {"duration": spec["duration"], "in_story_time": spec["time"]},
                "genre_ext": {
                    "type": "alt_history_investment",
                    "capital_before": format_eok(before),
                    "capital_after": format_eok(after),
                    "capital_delta": format_delta(delta),
                    "profit_loss": format_profit(delta),
                    "method": spec["method"],
                    "deal_type": spec["deal_type"],
                    "leverage_used": build_leverage_used(arc, spec),
                    "source_binding": deepcopy(spec["sources"]),
                    "opponent": {
                        "name": spec["opponent"],
                        "type": opponent_type(spec["opponent"]),
                        "weakness_exploited": weakness_for_slot(spec),
                    },
                    "historical_event": deepcopy(event),
                    "time_pressure": f"{spec['time']} 안에 {spec['deal_type']}을 마무리하지 못하면 다음 블록에서 먼저 가격을 부를 쪽은 {spec['opponent']}이다.",
                    "knowledge_used": arc["knowledge_used"],
                    "risk_level": spec["risk"],
                    "business_sector": spec["sector"],
                    "section_rotation": f"{arc['arc_id']} - {arc['title']}",
                    "success_pattern": spec["success"],
                    "global_partner": {
                        "name": spec["partner"] or arc["default_partner"],
                        "cadence": f"{arc['arc_id']} 핵심 파트너",
                        "objective": f"{spec['deal_type']}과 {spec['sector']}를 함께 묶어 강윤 쪽으로 우선순위를 이동시킨다.",
                    },
                },
                "regression_ext": {
                    "is_regressor": True,
                    "regression_type": "회귀",
                    "execution_doctrine": SETTING["execution_doctrine"],
                },
            }
        )
    return blocks


def build_phase0(treatment: list[dict[str, Any]]) -> dict[str, Any]:
    arcs_payload: list[dict[str, Any]] = []
    for arc in ordered_arcs():
        start_block, end_block = block_numbers(arc["block_range"])
        arcs_payload.append(
            {
                "arc_id": arc["arc_id"],
                "title": arc["title"],
                "block_range": arc["block_range"],
                "time_window": arc["time_window"],
                "capital_target": f"{treatment[start_block - 1]['genre_ext']['capital_before']} -> {treatment[end_block - 1]['genre_ext']['capital_after']}",
                "front_sectors": deepcopy(arc["front_sectors"]),
                "support_sectors": deepcopy(arc["support_sectors"]),
                "main_opponents": deepcopy(arc["main_opponents"]),
                "new_npcs": deepcopy(arc["new_npcs"]),
                "emotion_curve": arc["emotion_curve"],
                "quiet_blocks": deepcopy(arc["quiet_blocks"]),
                "defeat_blocks": deepcopy(arc["defeat_blocks"]),
                "source_binding": deepcopy(arc["default_sources"]),
                "partner_anchor": arc["default_partner"],
                "block_slots": [
                    {"block": start_block + idx, "title": spec["title"], "function": spec["function"]}
                    for idx, spec in enumerate(arc["blocks"])
                ],
            }
        )
    return {
        "project": deepcopy(PROJECT),
        "setting": deepcopy(SETTING),
        "protagonist": deepcopy(PROTAGONIST),
        "phase0_design": {
            "source_manifest": deepcopy(SOURCE_MANIFEST),
            "db_prep_packet": deepcopy(DB_PREP_PACKET),
            "arc_source_map": deepcopy(ARC_SOURCE_MAP),
            "arc_design": deepcopy(arcs_payload),
            "arcs": arcs_payload,
            "npc_timeline": deepcopy(NPC_TIMELINE),
            "foreshadow_map": deepcopy(FORESHADOW_MAP),
            "partner_location_sector_distribution": {
                "front_sector_by_arc": [
                    {"arc_id": arc["arc_id"], "front": deepcopy(arc["front_sectors"]), "support": deepcopy(arc["support_sectors"])}
                    for arc in ordered_arcs()
                ],
                "partners": deepcopy(PARTNERS),
                "location_pool": unique_in_order([spec["location"] for arc in ordered_arcs() for spec in arc["blocks"]]),
                "deal_type_rotation": [
                    {"arc_id": arc["arc_id"], "deal_types": [spec["deal_type"] for spec in arc["blocks"]]}
                    for arc in ordered_arcs()
                ],
            },
            "capital_curve": capital_curve_points(),
            "defeat_blocks": defeat_block_summaries(),
            "opponent_transition_plan": deepcopy(OPPONENT_TRANSITION_PLAN),
        },
    }


def build_portfolio_history(treatment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checkpoints = [1, 10, 20, 30, 40, 50, 60, 70]
    return [
        {
            "episode": 0,
            "block": block_no,
            "month": treatment[block_no - 1]["time_span"]["in_story_time"],
            "total_assets": treatment[block_no - 1]["genre_ext"]["capital_after"],
            "event": treatment[block_no - 1]["title"],
        }
        for block_no in checkpoints
    ]


def build_key_npcs() -> list[dict[str, Any]]:
    out = [
        {
            "name": PROTAGONIST_NAME,
            "role": "주인공",
            "desc": PROJECT["core_premise"],
            "first_block": 1,
            "final_status": PROTAGONIST["final_goal"],
            "key_turning_points": [
                {"block": 1, "event": "독살 직전 기억을 들고 1907년으로 돌아온다."},
                {"block": 30, "event": "조선을 담보로 읽는 금융가가 되기로 결심한다."},
                {"block": 68, "event": "경성의 실소유주 구조를 완성한다."},
                {"block": 70, "event": "조선을 사러 왔다고 선언한다."},
            ],
        }
    ]
    for npc in NPC_TIMELINE:
        out.append(
            {
                "name": npc["name"],
                "role": npc["role"],
                "desc": npc["final_status"],
                "first_block": npc["first_block"],
                "final_status": npc["final_status"],
                "key_turning_points": deepcopy(npc["turning_points"]),
            }
        )
    return out


def build_arc_sheets(phase0: dict[str, Any]) -> list[dict[str, Any]]:
    sheets: list[dict[str, Any]] = []
    for arc in phase0["phase0_design"]["arcs"]:
        sheets.append(
            {
                "arc_id": arc["arc_id"],
                "title": arc["title"],
                "block_range": arc["block_range"],
                "time_window": arc["time_window"],
                "capital_target": arc["capital_target"],
                "front_sectors": deepcopy(arc["front_sectors"]),
                "support_sectors": deepcopy(arc["support_sectors"]),
                "main_opponents": deepcopy(arc["main_opponents"]),
                "new_npcs": deepcopy(arc["new_npcs"]),
                "emotion_curve": arc["emotion_curve"],
                "quiet_blocks": deepcopy(arc["quiet_blocks"]),
                "defeat_blocks": deepcopy(arc["defeat_blocks"]),
                "source_binding": deepcopy(arc["source_binding"]),
                "partner_anchor": arc["partner_anchor"],
            }
        )
    return sheets


def build_historical_events(phase0: dict[str, Any], treatment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for arc in phase0["phase0_design"]["arcs"]:
        start_block, end_block = block_numbers(arc["block_range"])
        out.append(
            {
                "type": "arc",
                "arc_id": arc["arc_id"],
                "title": arc["title"],
                "time_window": arc["time_window"],
                "block_range": arc["block_range"],
                "entry_event": treatment[start_block - 1]["title"],
                "exit_event": treatment[end_block - 1]["title"],
            }
        )
    for block_no in [4, 8, 15, 18, 25, 35, 42, 45, 52, 57, 62, 70]:
        block = treatment[block_no - 1]
        out.append(
            {
                "type": "historical_hook",
                "block": block_no,
                "title": block["title"],
                "historical_event": deepcopy(block["genre_ext"]["historical_event"]),
            }
        )
    return out


def build_business_lines() -> list[str]:
    return unique_in_order(
        [sector for arc in ordered_arcs() for sector in arc["front_sectors"] + arc["support_sectors"]]
        + ["가명 법인", "배당·월세 회수", "담보 실행", "결제선 통합"]
    )


def build_bible(phase0: dict[str, Any], treatment: list[dict[str, Any]]) -> dict[str, Any]:
    business_lines = build_business_lines()
    final_capital = treatment[-1]["genre_ext"]["capital_after"]
    return {
        "_schema_version": "2.0",
        "_schema_description": "Bible synchronized output from phase0 and treatment draft",
        "_last_updated": date.today().isoformat(),
        "_genre": "alt_history",
        "MasterBible": {
            "ProjectData": {
                "MetaInfo": {
                    "title": TITLE,
                    "grand_objective": PROJECT["core_premise"],
                    "genre_archetype": PROJECT["format"],
                    "logline": PROJECT["logline"],
                    "total_episodes": 350,
                    "episodes_per_arc": 5,
                    "arcs_per_volume": 5,
                },
                "CoreIdentity": {
                    "protagonist": PROTAGONIST_NAME,
                    "protagonist_faction": "황실 비공식 자산선 (초기) -> 조선 핵심 결제선을 장악한 하우스 오브 강윤 (후기)",
                    "edge": PROTAGONIST["true_strength"],
                    "desire": PROTAGONIST["initial_goal"],
                    "crisis": "황자라는 이름은 남았지만 공식 권력은 없고, 합방 전까지 자산을 못 빼면 모든 판이 끝난다.",
                },
                "CommercialCode": {
                    "cider_point": "망국의 황자가 나라를 구하는 대신 나라의 현금흐름과 소유권을 통째로 사들이는 쾌감",
                    "success_device": "해운·보험·외환·담보·철도·창고 병목 독점",
                    "attitude": "명분보다 병목, 충성보다 소유권, 독립보다 현금흐름을 먼저 쥐는 냉혹한 회귀자",
                },
            },
            "protagonist_config": {
                "world_origin": PROTAGONIST["status"],
                "incarnation_type": "회귀",
                "special_talent": {
                    "name": "전쟁과 공황의 타이밍을 자산배치로 바꾸는 감각",
                    "description": PROTAGONIST["true_strength"],
                    "limits": PROTAGONIST["true_weakness"],
                },
                "start_point": {
                    "year": PROJECT["start_year"],
                    "month": "1907년 8월",
                    "age": PROTAGONIST["age_at_start"],
                    "context": "취리히 독살의 기억을 들고 헤이그 특사 파문 직후의 궁으로 돌아온다.",
                },
            },
            "FinanceHUD": {
                "_description": "황실 자산, 유럽 금융, 식민지 담보, 병목 자산 지배력을 추적하는 HUD",
                "Protagonist": {
                    "actual_truth": {
                        "name": PROTAGONIST_NAME,
                        "alias": "애매한 황족 (초기) -> 조선의 실소유주 (후기)",
                        "age": PROTAGONIST["age_at_start"],
                        "rank": "대한제국 서출 황자 / 하우스 오브 강윤",
                        "financial_status": {
                            "mobilizable_capital": treatment[0]["genre_ext"]["capital_before"],
                            "total_assets": treatment[0]["genre_ext"]["capital_before"],
                            "max_assets": final_capital,
                            "company": STARTER_COMPANY["name"],
                            "company_state": STARTER_COMPANY["state"],
                            "business_lines": business_lines,
                            "debt": "황실 붕괴, 통감부 감시, 황실 내부 불신, 합방 시한",
                        },
                        "portfolio_history": build_portfolio_history(treatment),
                        "investment_style": SETTING["execution_doctrine"],
                        "risk_tolerance": "정치와 전쟁의 위험을 감수하되 이름 대신 문서와 담보로 움직인다.",
                        "credentials": [PROTAGONIST["status"], "회귀자", STARTER_COMPANY["name"]],
                        "current_objective": PROTAGONIST["mid_goal"],
                        "mid_term_goal": PROTAGONIST["mid_goal"],
                        "final_goal": PROTAGONIST["final_goal"],
                        "causal_injuries": "1936년 취리히 독살과 합방의 기억이 모든 선택의 바닥에 남아 있다.",
                    }
                },
            },
            "MartialHUD": {
                "_alias_note": "compat alias",
                "Protagonist": {"actual_truth": {"name": PROTAGONIST_NAME, "alias": "황제가 아닌 채권자", "age": PROTAGONIST["age_at_start"], "rank": "하우스 오브 강윤 수장"}},
            },
            "WorldState": {
                "CurrentEra": treatment[0]["time_span"]["in_story_time"],
                "CurrentLocation": treatment[0]["location"]["place"],
                "era_window": f"{PROJECT['start_year']}년~{PROJECT['end_year']}년",
                "group_background": SETTING["group_background"],
                "execution_doctrine": SETTING["execution_doctrine"],
                "starter_company": deepcopy(STARTER_COMPANY),
                "source_manifest": deepcopy(SOURCE_MANIFEST),
                "opponent_transition_plan": deepcopy(OPPONENT_TRANSITION_PLAN),
                "front_sector_by_arc": phase0["phase0_design"]["partner_location_sector_distribution"]["front_sector_by_arc"],
            },
            "AssetLibrary": {
                "KeyNPCs": build_key_npcs(),
                "StarterCompany": deepcopy(STARTER_COMPANY),
                "ArcSheets": build_arc_sheets(phase0),
                "Partners": deepcopy(PARTNERS),
                "LocationPool": deepcopy(phase0["phase0_design"]["partner_location_sector_distribution"]["location_pool"]),
                "DealTypeRotation": deepcopy(phase0["phase0_design"]["partner_location_sector_distribution"]["deal_type_rotation"]),
                "BusinessAxis": {
                    "front_sectors": business_lines,
                    "execution_doctrine": SETTING["execution_doctrine"],
                    "group_assets": deepcopy(STARTER_COMPANY["assets"]),
                    "group_liabilities": deepcopy(STARTER_COMPANY["liabilities"]),
                },
            },
            "AltHistoryWorld": {
                "source_manifest": deepcopy(SOURCE_MANIFEST),
                "db_prep_packet": deepcopy(DB_PREP_PACKET),
                "arc_source_map": deepcopy(ARC_SOURCE_MAP),
            },
            "Seeds": deepcopy(FORESHADOW_MAP),
            "HistoricalEvents": build_historical_events(phase0, treatment),
            "GenreRules": {
                "core_mode": PROJECT["format"],
                "growth_rule": "황실 자산 반출 -> 유럽 해운·보험 -> 식민지 채권 -> 경성 담보권 -> 대공황 저가 매집 -> 전시 병목 독점 -> 실소유주 선언으로 상승한다.",
                "reward_rule": "승리는 자본 증가, 우선순위 장악, 결제선 통합의 세 층위로 측정한다.",
                "risk_rule": "실패는 외환 동결, 운임 붕괴, 중복 담보, 정책은행 타이밍, 국가권력과의 마지막 협상에서 온다.",
                "talent_rule": "강윤의 힘은 회귀 지식과 장부 감각뿐이며 초자연적 개입은 없다.",
            },
            "plot_roadmap": deepcopy(treatment),
        },
    }


def verify(phase0: dict[str, Any], treatment: list[dict[str, Any]], bible: dict[str, Any]) -> None:
    tr_valid, tr_errors, _ = validate_treatment_structure(treatment)
    bible_valid, bible_errors, _ = validate_bible_structure(bible)
    if not tr_valid:
        raise ValueError(f"treatment validation failed: {tr_errors}")
    if not bible_valid:
        raise ValueError(f"bible validation failed: {bible_errors}")
    if len(treatment) != 70:
        raise ValueError(f"expected 70 treatment blocks, got {len(treatment)}")
    if len(phase0["phase0_design"]["arcs"]) != 7:
        raise ValueError("phase0 arc count mismatch")
    if bible["MasterBible"]["ProjectData"]["CoreIdentity"]["protagonist"] != bible["MasterBible"]["FinanceHUD"]["Protagonist"]["actual_truth"]["name"]:
        raise ValueError("BI protagonist mismatch")
    serialized = json.dumps({"phase0": phase0, "treatment": treatment, "bible": bible}, ensure_ascii=False)
    if "???" in serialized or "�" in serialized:
        raise ValueError("garbled UTF-8 token detected")


def main() -> int:
    treatment = build_treatment()
    phase0 = build_phase0(treatment)
    bible = build_bible(phase0, treatment)
    verify(phase0, treatment, bible)
    write_json(PHASE0_PATH, phase0)
    write_json(TR_PATH, treatment)
    write_json(TR_TITLE_PATH, treatment)
    write_json(BI_PATH, bible)
    print(f"[OK] wrote {PHASE0_PATH}")
    print(f"[OK] wrote {TR_PATH}")
    print(f"[OK] wrote {TR_TITLE_PATH}")
    print(f"[OK] wrote {BI_PATH}")
    return 0


if __name__ == "__main__" and "ARC_SOURCE_MAP" in globals():
    raise SystemExit(main())

ARCS.extend(
    [
        {
            "arc_id": "ARC-06",
            "title": "일본 군부와 재벌을 동시에 물다",
            "block_range": "51-60",
            "time_window": "1933년 1월~1937년 6월",
            "front_sectors": ["은행/금융", "보험", "광산/자원", "철도/인프라"],
            "support_sectors": ["스위스 계좌", "만주 금융분리", "전력·제지", "군수 하청"],
            "main_opponents": ["오쿠라 다카시", "마쓰오카 요스케", "구도 겐이치"],
            "new_npcs": ["오쿠라 다카시", "마쓰오카 요스케"],
            "emotion_curve": "비밀계좌 -> 국가와 거래 -> 통화권 분리 -> 장부 장악",
            "quiet_blocks": [59],
            "defeat_blocks": [55],
            "knowledge_used": "BIS, 스위스 은행비밀법, 만주 금융망 분리, 조선은행 감자와 지점 이관의 타이밍을 이용한다.",
            "default_sources": source_binding([EU, COLONIAL], [BANK_FX, MARINE]),
            "default_partner": "취리히 프라이빗 뱅크 / 오쿠라구미 경쟁선",
            "blocks": [
                slot("BIS 복도", "바젤 BIS 복도에서 강윤은 중앙은행급 정보가 어디서 새는지 본다.", "1933년 초", "바젤 BIS 본부 복도", "은행/금융", "국제금융 정보선 확보", "직접 들어갈 수 없더라도 누가 누구를 기다리는지만 보면 다음 통화 방향이 읽힌다고 본다.", "마쓰오카 요스케", ["소피 아들러"], hist("국제결제은행(BIS) 바젤 설립", 1930, "중앙은행 정보가 스위스 금융축으로 모이는 구조를 활용한다.", EU), "realization", 6, 6, "1주", "강윤의 전장은 부두에서 중앙은행 복도로까지 넓어진다.", foreshadow=["Block 52의 은행비밀법, Block 62의 국가총동원 장부는 모두 여기서 얻은 정보선이 이어진다."]),
                slot("스위스 은행비밀법", "1934년 은행비밀법 시행과 함께 강윤은 익명 계좌를 전면 재배치한다.", "1934년 11월", "취리히 호숫가 은행", "은행/금융", "비밀계좌 구조화", "중립국 예치가 단순 보관이 아니라 정치와 전쟁을 견디는 보호막이 되는 순간을 붙잡는다.", "오쿠라 다카시", ["소피 아들러"], hist("스위스 은행비밀법 제정", 1934, "자산 은닉이 아니라 자산 생존 구조를 합법 장벽으로 만든다.", EU), "breakthrough", 8, 7, "2주", "강윤 자산은 이제 전쟁이 와도 이름보다 구조가 먼저 살아남는다."),
                slot("보험증권의 이름", "강윤은 자기 이름 대신 보험증권과 재보험 세션의 이름으로 움직인다.", "1934년 겨울", "런던 / 취리히 재보험 교차선", "보험", "전쟁위험 재보험 우회", "국가와 군부가 직접 못 먹는 계약 이름 아래로 위험과 수익을 동시에 숨긴다.", "오쿠라 다카시", ["소피 아들러", "최무진"], hist("보험에서 재보험으로 이어지는 세션 구조", 1934, "전쟁위험과 일반위험을 분리해 자신의 실명 노출 없이 수익을 챙긴다.", MARINE), "deception", 7, 7, "2주", "강윤은 얼굴이 아니라 증권 이름으로 제국을 굴리기 시작한다."),
                slot("북선 펄프공장", "만주와 북선의 물류를 묶는 제지·펄프 공장은 겉보기보다 훨씬 전략적인 자산이었다.", "1935년 초", "북선 제지화학 공업지대", "광산/자원", "펄프·전력 연계 공장 매입", "목재와 화학, 전력, 철도가 함께 움직이는 공장을 사면 전쟁기에도 쉽게 대체되지 않는다고 본다.", "오쿠라 다카시", ["민도식"], hist("북선제지화학공업 자본금 2,000만 원", 1935, "북선 공업 자산을 후방 병참 포트폴리오로 편입한다.", COLONIAL), "alliance", 7, 7, "3주", "강윤은 광산이 아니라 광산을 먹이는 전력과 펄프를 먼저 쥔다."),
                slot("조선은행 감자표", "감자표를 과신한 강윤은 한 차례 계산을 빗나가며 자금이 묶인다.", "1935년 봄", "경성 조선은행 인근 정산실", "은행/금융", "은행 구조조정 베팅", "감자 이후 회복 속도를 너무 빨리 본 탓에 일부 채권 포지션이 묶이며 손실을 감수한다.", "구도 겐이치", ["윤창식"], hist("조선은행 감자 후 자본금 4,000만 원", 1925, "감자 이후에도 식민지 은행 장부는 정치와 정책에 휘둘린다는 사실을 다시 확인한다.", COLONIAL), "defeat", 8, 8, "2주", "장부를 읽는 실력만으로 정책은행의 타이밍까지 지배할 순 없다는 대가를 치른다."),
                slot("통화권 분리", "조선은행권의 만주 유통이 끊기며 조선 장부와 만주 장부를 분리해 먹을 기회가 열린다.", "1935년 여름", "신의주 / 봉천 결제선", "은행/금융", "장부 분리 구조화", "같은 자산이라도 어느 장부에 묶이느냐에 따라 회수 속도와 가치가 달라지는 틈을 만든다.", "마쓰오카 요스케", ["소피 아들러", "최무진"], hist("조선은행권의 만주 유통이 중지됨", 1935, "만주 장부와 조선 장부를 분리해 담보는 조선에 남기고 수익은 북방에서 먹는다.", COLONIAL), "pressure", 7, 7, "2주", "국경이 아니라 장부를 갈라 자산 통제권을 쥔다.", callback=["Block 7의 외환 감각과 Block 42의 통화 충격 대응이 여기서 식민지 장부 재편으로 이어진다."]),
                slot("만주 20지점", "강윤은 조선은행 만주 20지점 이관 직전 고객군과 담보를 먼저 골라낸다.", "1937년 1월", "봉천 / 신경 은행 지점망", "은행/금융", "이관 전 고객 선점", "간판이 바뀌면 고객은 당황하지만 장부와 담보는 반드시 누군가 먼저 줍는다.", "마쓰오카 요스케", ["최무진", "오쿠라 다카시"], hist("조선은행 만주 20지점이 만주흥업은행으로 넘어감", 1937, "지점 이전기의 결제 공백을 우량 담보 선점 기회로 본다.", COLONIAL), "escalation", 8, 8, "3주", "은행 간판이 바뀌는 순간 강윤은 장부 밖에서 고객을 낚아챈다."),
                slot("오쿠라구미의 그림자", "오쿠라구미는 강윤과 똑같은 병목 자산을 노리지만 항상 한 걸음 늦다.", "1936년 봄", "경성 / 대련 공동투자선", "광산/자원", "병목 자산 경쟁 입찰", "광산 자체가 아니라 운송과 전력, 담보 실행 순위를 먼저 잡은 쪽이 이긴다는 점이 승부를 가른다.", "오쿠라 다카시", ["오쿠라 다카시"], hist("만주사변 뒤 철도·광산·전력 권리가 다시 배열됨", 1932, "현지 광권보다 조선 후방의 운송·전력 자산을 묶는 편이 더 안전하다는 구조를 실전에서 증명한다.", COLONIAL), "confrontation", 8, 8, "2주", "오쿠라구미는 돈은 많아도 병목을 먼저 못 쥔 탓에 밀린다."),
                slot("마쓰오카의 지도", "마쓰오카는 외교지도를 펼치고 강윤은 그 위에 자산지도를 겹쳐 본다.", "1936년 가을", "도쿄 외교 살롱", "은행/금융", "외교-자산 교차 거래", "강윤은 제국의 외교 구상과 자산 배치를 서로 이용할 수 있지만 끝내 같은 편은 아니라는 걸 분명히 한다.", "마쓰오카 요스케", ["마쓰오카 요스케"], hist("엔블록과 전시 외환 통제의 강화 조짐", 1936, "제국의 통화·외교권 구상을 자기 자산 배치의 선행지표로 사용한다.", BANK_FX), "quiet", 5, 5, "1주", "국가 권력과 사적 자본이 서로를 재료로 삼는 법을 확인한다."),
                slot("총독부 담보표", "강윤은 총독부가 손대는 모든 회사의 담보표와 우선순위를 한 장으로 정리한다.", "1937년 6월", "경성 금융 조사실", "은행/금융", "담보표 통합 분석", "개별 자산이 아니라 담보표 전체를 읽어야 누가 실제 조선을 굴리는지 보인다고 판단한다.", "구도 겐이치", ["윤창식", "구도 겐이치"], hist("식민지 행정과 은행, 철도, 광산이 결합된 담보 구조", 1937, "총독부와 은행, 상사가 얽힌 담보표를 통합해 실행 순위를 다시 쓴다.", COLONIAL), "triumph", 8, 7, "2주", "강윤은 총독부 장부를 보는 사람이 아니라 다시 쓰는 사람으로 올라선다.", callback=["Block 29의 조선은행 부실표가 Block 60에서 총독부 전체 담보표로 확장된다."]),
            ],
        },
        {
            "arc_id": "ARC-07",
            "title": "식민지 조선의 실소유주",
            "block_range": "61-70",
            "time_window": "1937년 7월~1938년 12월",
            "front_sectors": ["군수/방산", "전력", "철도/인프라", "은행/금융"],
            "support_sectors": ["국가총동원", "광산/자원", "언론·월세", "장기계약"],
            "main_opponents": ["구도 겐이치", "마쓰오카 요스케", "오쿠라 다카시"],
            "new_npcs": [],
            "emotion_curve": "전쟁 개시 -> 국가총동원 -> 실소유주 증명 -> 무혈복수",
            "quiet_blocks": [],
            "defeat_blocks": [65],
            "knowledge_used": "중일전쟁과 국가총동원이 시장 논리를 죽이고 병목 설비의 협상력을 폭증시킨다는 걸 끝까지 활용한다.",
            "default_sources": source_binding([COLONIAL], [RAIL, BANK_FX]),
            "default_partner": "경성 배당·월세 회수망",
            "blocks": [
                slot("중일전쟁 첫 배당", "전쟁이 시작되자 군수 주문보다 먼저 배당과 우선배정권이 움직인다.", "1937년 7월", "경성 / 부산 군수 수송선", "군수/방산", "전시 수송 우선권 확보", "총알을 팔기보다 총알이 지나갈 선로와 창고, 보험과 전기를 묶는 편이 낫다고 본다.", "구도 겐이치", ["오쿠라 다카시", "최무진"], hist("중일전쟁 발발과 대륙병참 수송 체계 강화", 1937, "군수 최우선 체제가 민간 병목 자산의 협상력을 폭증시키는 구간을 먹는다.", RAIL), "escalation", 8, 8, "2주", "전쟁은 강윤에게 총이 아니라 배당과 우선권의 언어로 온다."),
                slot("국가총동원의 장부", "1938년 국가총동원이 시작되자 개별 회사는 포트폴리오의 부속품으로 바뀐다.", "1938년 봄", "경성 총동원 배정실", "은행/금융", "전시 포트폴리오 재배치", "국가가 필요한 병목을 이미 쥐고 있으면 직접 경영보다 큰 협상력을 갖는다는 걸 실전에서 확인한다.", "구도 겐이치", ["윤창식", "마쓰오카 요스케"], hist("국가총동원으로 수송·광산·전력 자산이 전시 포트폴리오화", 1938, "수익률보다 대체불가능성을 기준으로 자산 가치를 다시 매긴다.", COLONIAL), "pressure", 8, 8, "3주", "국가의 장부가 바뀌는 순간 강윤 자산의 협상력은 더 커진다."),
                slot("군수보다 전기", "강윤은 군수회사보다 전력회사를 더 먼저 지킨다.", "1938년 초여름", "경성 전력회사 이사회", "전력", "전력 우선배정 계약", "전기 없인 군수도 못 움직인다는 사실을 알고 전력 우선권을 담보로 군부를 상대한다.", "오쿠라 다카시", ["민도식"], hist("전시 자산 가치가 국가 우선순위에 따라 재해석되는 구조", 1938, "군수 그 자체보다 군수를 살리는 전력과 저장 설비를 우선 장악한다.", COLONIAL), "resolve", 7, 7, "2주", "강윤은 총알보다 스위치를 쥔 사람이 더 강하다는 걸 입증한다."),
                slot("광산보다 선로", "광산의 생산보다 선로 배정이 더 큰 돈이 되는 시기가 왔다.", "1938년 여름", "평북 인입선 / 광산 하역장", "철도/인프라", "광산 연계 선로권 확보", "광산은 누구나 탐내지만 선로와 인입선은 놓치는 경우가 많다는 걸 다시 이용한다.", "오쿠라 다카시", ["민도식", "윤창식"], hist("철도/인프라가 광산·자원 가치의 절반 이상을 만드는 구조", 1938, "광권이 아니라 인입선과 환적권을 통해 실질 지배권을 얻는다.", RAIL), "breakthrough", 8, 7, "3주", "광산의 주인이 아니라 광산을 움직이는 선로의 주인이 된다.", callback=["Block 35의 철도 예정선 실패를 Block 64의 실물 선로로 뒤집는다."]),
                slot("총독부의 연장신청", "총독부는 강윤 계열 자금과 설비 없이는 연장 공사를 못 하게 되자 처음으로 부탁하러 온다.", "1938년 가을", "경성 총독부 청사", "은행/금융", "총독부 연장신청 담판", "승리 직전이라 방심한 강윤은 일부 조건을 너무 세게 불러 협상이 하루 틀어지고, 그 사이 적이 마지막 반격의 시간을 번다.", "구도 겐이치", ["구도 겐이치"], hist("국가가 필요한 병목 설비를 미리 쥐면 높은 협상력을 얻는 구조", 1938, "강윤이 이미 우위여도 국가 권력과의 마지막 가격 협상은 위험하다는 점을 드러낸다.", COLONIAL), "defeat", 8, 8, "1주", "이긴 뒤의 협상도 방심하면 역으로 물릴 수 있다는 마지막 경고를 받는다."),
                slot("조선의 월세", "강윤은 조선을 해방시키지 않았지만 조선의 월세를 걷기 시작한다.", "1938년 10월", "경성 배당·월세 회수망", "은행/금융", "배당·월세 회수 체계 통합", "토지, 창고, 전기, 선로, 항만, 언론에서 나오는 현금흐름을 하나의 회수망으로 묶는다.", "구도 겐이치", ["민도식", "한예담"], hist("창고증권, 전기, 철도, 담보권의 결합 수익 구조", 1938, "각 자산의 배당과 월세를 같은 통장으로 모아 조선 전체를 현금흐름으로 환산한다.", COLONIAL), "triumph", 9, 7, "2주", "조선은 더 이상 지도가 아니라 월세표가 된다."),
                slot("황제가 아닌 채권자", "강윤은 복위보다 채권자 지위를 택한다.", "1938년 11월", "경성 / 취리히 공동정산선", "은행/금융", "최종 우선순위 확정", "황제라는 이름은 국가를 부르지만 채권자라는 위치는 총독부와 재벌을 동시에 무릎 꿇린다고 판단한다.", "마쓰오카 요스케", ["소피 아들러", "윤창식"], hist("국가와 기업이 모두 담보와 채권 순위 아래 놓이는 전시 금융 구조", 1938, "정체성보다 우선순위가 강하다는 사실로 최종 포지션을 고정한다.", COLONIAL), "realization", 8, 7, "1주", "강윤은 황좌가 아니라 조선의 현금흐름표 꼭대기를 고른다."),
                slot("경성의 실소유주", "경성의 은행, 철도, 창고, 전기, 언론은 각기 다른 간판을 달았지만 결제선은 강윤에게 닿는다.", "1938년 12월 초", "경성 중앙정산실", "은행/금융", "결제선 통합 선언", "이제 소유권은 한 번에 공개할 필요도 없고, 결제선과 우선순위가 모두 같은 곳을 향하면 그걸로 충분하다고 본다.", "구도 겐이치", ["한예담", "윤창식", "민도식"], hist("식민지 자산이 전시 포트폴리오로 묶이는 구조", 1938, "강윤 계열 결제선이 조선 핵심 자산 대부분을 통과하도록 완성한다.", COLONIAL), "triumph", 9, 8, "2주", "강윤은 이름 없이도 경성의 실소유주가 된다.", callback=["Block 31의 가명 법인 구조가 마침내 Block 68에서 실소유주 구조가 된다."]),
                slot("피맛 없는 복수", "독살당하던 밤의 복수는 칼이 아니라 배당표와 지급 연장 승인서로 끝난다.", "1938년 12월 중순", "경성 / 취리히 서명선", "은행/금융", "복수의 정산", "죽음의 기억을 이용해 사람을 죽이는 대신 살아남아야 할 자산만 골라 상대를 굶겨 죽인다.", "이토 마사유키", ["한예담", "소피 아들러"], hist("헤이그 이후 막혔던 황실 자산 경로의 완전 역전", 1938, "처음엔 빼돌려야 했던 돈이 이제는 조선 전체의 결제선이 되어 돌아온다.", ROYAL), "aftermath", 7, 7, "1주", "복수는 피맛이 아니라 이자와 배당의 맛으로 끝난다.", callback=["Block 1의 취리히 독살, Block 4의 헤이그 잔금, Block 52의 비밀계좌가 모두 여기서 회수된다."]),
                slot("나는 조선을 산다", "강윤은 누구도 부정할 수 없는 장부 위에서 조선을 구하러 온 게 아니라 사러 왔다고 선언한다.", "1938년 12월 말", "경성 중앙정산실 / 취리히 결제선", "은행/금융", "실소유주 선언", "독립운동가도, 허수아비 황제도 아닌 채권자이자 결제선의 주인으로 최종 위치를 확정한다.", "구도 겐이치", ["한예담", "소피 아들러", "윤창식"], hist("국가총동원 체제 아래 병목 자산의 협상력 극대화", 1938, "국가가 필요한 병목을 모두 묶어 조선 전체를 결제선 하나로 환산한다.", COLONIAL), "triumph", 10, 8, "3일", "칼로 빼앗긴 조선을 통장으로 사들이는 서사의 결론이다.", callback=["Block 10의 합방 전야 장부에서 지킨 돈이 Block 70에서 조선 전체를 사는 장부가 된다."]),
            ],
        },
    ]
)

NPC_TIMELINE: list[dict[str, Any]] = [
    {"name": "한예담", "role": "황실 회계 보조", "first_block": 1, "final_status": "강윤의 조선 내 회계선과 배당 회수망을 설계하는 핵심 실무자", "turning_points": [{"block": 3, "event": "황실 금고 열쇠와 별도 장부를 함께 확보한다."}, {"block": 31, "event": "경성 가명 법인 구조를 황실 장부 방식으로 다시 짠다."}, {"block": 68, "event": "경성의 결제선이 모두 강윤 쪽으로 수렴하는 구조를 완성한다."}]},
    {"name": "헨드릭 판데르벨트", "role": "로테르담 선주", "first_block": 9, "final_status": "강윤 계열 해운망에 편입된 로테르담 물류 파트너", "turning_points": [{"block": 11, "event": "낡은 화물선을 싸게 넘기며 첫 거래를 튼다."}, {"block": 23, "event": "전후 해운 붐 구간에서 강윤과 함께 운임 광풍을 탄다."}, {"block": 43, "event": "대공황 저점 매수 국면에서 부두권 일부를 강윤 쪽에 넘긴다."}]},
    {"name": "소피 아들러", "role": "취리히 자산관리인", "first_block": 10, "final_status": "유럽 자산과 비밀계좌를 끝까지 묶어 두는 최후의 정산 창구", "turning_points": [{"block": 16, "event": "중립국 계좌 구조를 본격 가동한다."}, {"block": 26, "event": "취리히 머천트뱅크 설립에 협력한다."}, {"block": 52, "event": "스위스 은행비밀법 아래 강윤 자산의 익명 구조를 완성한다."}]},
    {"name": "최무진", "role": "상하이 무기상", "first_block": 27, "final_status": "군수품 목록과 연락선을 쥔 동아시아 외부 실행선", "turning_points": [{"block": 27, "event": "상하이 연락선과 조계 금융선 정보를 넘긴다."}, {"block": 57, "event": "만주 20지점 이관 국면에서 고객군을 강윤 쪽으로 돌린다."}, {"block": 61, "event": "전시 수송선 배당 구조를 강윤에게 유리하게 엮는다."}]},
    {"name": "민도식", "role": "경성 지주 2세", "first_block": 31, "final_status": "조선 내 토지·창고·월세 회수망을 운영하는 현지 명의인", "turning_points": [{"block": 34, "event": "상환일을 넘긴 지주의 자산을 강윤 쪽으로 돌리는 데 협력한다."}, {"block": 48, "event": "측선과 제분소 패키지 자산을 묶는 현지 명의인이 된다."}, {"block": 66, "event": "조선의 월세 회수망을 실무로 운영한다."}]},
    {"name": "이토 마사유키", "role": "통감부 재무관", "first_block": 1, "final_status": "초기에 황실 금고를 놓친 탓에 끝내 강윤을 막지 못한 구질서의 상징", "turning_points": [{"block": 4, "event": "헤이그 잔금 경로를 추적하지만 놓친다."}, {"block": 10, "event": "합방 전야 장부 절단을 눈치채지만 되돌리지 못한다."}, {"block": 69, "event": "취리히 독살의 기억이 피맛 없는 복수로 되돌아온다."}]},
    {"name": "에드워드 블레이크", "role": "영국 해운 재벌 후계자", "first_block": 11, "final_status": "유럽 해운 질서에서 강윤과 같은 판에 섰지만 먼저 시장을 읽지 못해 진 패자", "turning_points": [{"block": 14, "event": "전쟁 전 선복을 비싸게 잠그려다 강윤에게 한발 늦는다."}, {"block": 25, "event": "운임 붕괴 속에서 부실을 강윤보다 크게 뒤집어쓴다."}, {"block": 41, "event": "빈 부두의 가격을 버티지 못하고 자산을 판다."}]},
    {"name": "구도 겐이치", "role": "총독부 경제국 관료", "first_block": 29, "final_status": "강윤을 통제하는 대신 조건을 구걸해야 하는 총독부 실무자", "turning_points": [{"block": 35, "event": "철도 예정선 도면으로 강윤에게 첫 실질 손실을 안긴다."}, {"block": 60, "event": "총독부 담보표가 강윤 손에 넘어가는 걸 확인한다."}, {"block": 65, "event": "총독부 연장신청을 들고 강윤 앞에 선다."}]},
    {"name": "오쿠라 다카시", "role": "오쿠라구미 투자 책임자", "first_block": 54, "final_status": "더 큰 자본을 들고도 병목을 먼저 못 쥔 탓에 밀린 재벌형 적대자", "turning_points": [{"block": 54, "event": "북선 펄프공장을 두고 강윤과 같은 표적을 노린다."}, {"block": 58, "event": "오쿠라구미의 그림자처럼 따라붙지만 선로·전력 우선권에서 밀린다."}, {"block": 63, "event": "군수보다 전기를 더 높게 본 강윤의 계산에 패배한다."}]},
    {"name": "윤창식", "role": "경성 등기 변호사", "first_block": 31, "final_status": "가명 법인, 담보 실행, 경매, 배당 회수까지 설계하는 서류 기술자", "turning_points": [{"block": 37, "event": "등기와 경매를 하나의 흐름으로 강윤에게 설명한다."}, {"block": 47, "event": "중복 담보 함정을 계기로 문서 검증 체계를 다시 짠다."}, {"block": 67, "event": "황제가 아닌 채권자라는 최종 위치를 법률 구조로 고정한다."}]},
    {"name": "마쓰오카 요스케", "role": "일본 외교·정치 권력", "first_block": 59, "final_status": "강윤을 완전히 배제할 수 없음을 인정하는 국가 권력", "turning_points": [{"block": 51, "event": "BIS 복도 정보선에서 강윤과 같은 지도를 보게 된다."}, {"block": 59, "event": "외교지도를 자산지도와 포개는 강윤의 계산을 확인한다."}, {"block": 67, "event": "황제가 아닌 채권자라는 위치가 더 위협적임을 이해한다."}]},
]

FORESHADOW_MAP = [
    {"id": "F1", "name": "황실 금고 열쇠", "seed_block": 3, "hint_blocks": [31, 66], "payoff_block": 68, "summary": "처음엔 금고를 여는 도구였던 열쇠가 후반엔 조선 전체 결제선의 원형이 된다."},
    {"id": "F2", "name": "헤이그 밀사 경로", "seed_block": 4, "hint_blocks": [16, 52], "payoff_block": 69, "summary": "외교 실패의 잔해였던 밀사 경로가 유럽 비밀계좌와 복수의 정산선으로 재탄생한다."},
    {"id": "F3", "name": "역둔토 소작 장부", "seed_block": 5, "hint_blocks": [32, 44], "payoff_block": 66, "summary": "황실 마지막 소작료 장부가 후반 조선의 월세 수입 구조를 설계하는 원형이 된다."},
    {"id": "F4", "name": "로테르담 선하증권 라인", "seed_block": 12, "hint_blocks": [28, 43], "payoff_block": 68, "summary": "선하증권 담보 구조가 후반 식민지 자산 결제선 통합의 핵심 논리로 확장된다."},
    {"id": "F5", "name": "경성 가명 법인", "seed_block": 31, "hint_blocks": [46, 58], "payoff_block": 68, "summary": "가명 법인 구조가 후반 경성 전체를 강윤 계열 결제선 아래 숨기는 법적 틀로 커진다."},
    {"id": "F6", "name": "창고증권 실행권", "seed_block": 45, "hint_blocks": [56, 60], "payoff_block": 66, "summary": "창고증권 우선순위가 월세와 배당을 걷는 최종 회수망의 뼈대가 된다."},
]

PARTNERS = [
    {"name": "로테르담 선주조합", "role": "해운·선복·부두권 협상 파트너", "key_blocks": [11, 20, 43]},
    {"name": "앤트워프 재보험 브로커단", "role": "전쟁위험과 재보험 세션 파트너", "key_blocks": [13, 17, 18]},
    {"name": "취리히 프라이빗 뱅크", "role": "중립국 계좌, 비밀계좌, 최종 정산 파트너", "key_blocks": [16, 26, 52]},
    {"name": "상하이 연락선", "role": "동아시아 어음·군수품·조계 금융 정보 파트너", "key_blocks": [27, 57, 61]},
    {"name": "경성 등기·경매 법률선", "role": "가명 법인, 경매, 담보 실행 파트너", "key_blocks": [31, 37, 67]},
    {"name": "경성 배당·월세 회수망", "role": "조선 내 현금흐름 최종 회수 파트너", "key_blocks": [40, 66, 68]},
]

ARC_SOURCE_MAP = [
    {"arc_id": "ARC-01", "core_sources": [ROYAL], "support_sources": [BANK_FX], "purpose": "황실 자산 반출과 합방 전 데드라인"},
    {"arc_id": "ARC-02", "core_sources": [EU], "support_sources": [MARINE], "purpose": "전쟁 전 선복, 전쟁위험요율, 해상보험"},
    {"arc_id": "ARC-03", "core_sources": [EU], "support_sources": [BANK_FX], "purpose": "전후 해운 붐과 폭락, 상하이 연락선, 식민지 어음"},
    {"arc_id": "ARC-04", "core_sources": [COLONIAL], "support_sources": [RAIL], "purpose": "경성 복귀, 경매, 등기, 철도 예정선, 창고권"},
    {"arc_id": "ARC-05", "core_sources": [EU, COLONIAL], "support_sources": [BANK_FX, RAIL], "purpose": "대공황, 파운드 절하, 곡물 담보, 측선과 창고"},
    {"arc_id": "ARC-06", "core_sources": [EU, COLONIAL], "support_sources": [BANK_FX, MARINE], "purpose": "BIS, 은행비밀법, 만주 금융망 분리, 북선 공업 자산"},
    {"arc_id": "ARC-07", "core_sources": [COLONIAL], "support_sources": [RAIL, BANK_FX], "purpose": "국가총동원, 전력·선로 병목, 월세 회수망 완성"},
]

OPPONENT_TRANSITION_PLAN = [
    {
        "phase": "1-10",
        "opponents": ["이토 마사유키", "통감부 재무선", "황실 내부 배신자"],
        "logic": "황실 자산을 합방 이전에 완전히 동결하려는 초반 적대축",
    },
    {
        "phase": "11-30",
        "opponents": ["에드워드 블레이크", "영국 해운 카르텔", "유럽 브로커 연합"],
        "logic": "유럽 해운·보험·선적금융에서 동양 황자를 눌러 죽이려는 성장기 적대축",
    },
    {
        "phase": "31-70",
        "opponents": ["구도 겐이치", "오쿠라 다카시", "마쓰오카 요스케"],
        "logic": "총독부, 재벌, 군부, 외교 권력이 조선의 실질 소유권을 놓고 충돌하는 후반 적대축",
    },
]


if __name__ == "__main__":
    from scripts import build_fallen_prince_buys_joseon_assets as _self

    raise SystemExit(_self.main())


def capital_curve_points() -> list[dict[str, Any]]:
    checkpoints = [1, 10, 20, 30, 40, 50, 60, 70]
    current = CAPITAL_START
    values: dict[int, int] = {1: CAPITAL_START}
    for idx, delta in enumerate(CAPITAL_DELTAS, start=1):
        current += delta
        values[idx + 1] = current
    return [{"block": block, "capital": format_eok(values[block])} for block in checkpoints]


def defeat_block_summaries() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    running = 0
    for arc in ARCS:
        for spec in arc["blocks"]:
            running += 1
            if CAPITAL_DELTAS[running - 1] < 0:
                out.append(
                    {
                        "block": running,
                        "success_pattern": "실패" if running in (15, 25, 35, 42, 47, 55, 65) else "부분 성공",
                        "summary": spec["function"],
                    }
                )
    return out



ARCS.extend(
    [
        {
            "arc_id": "ARC-04",
            "title": "총독부의 등기부를 사들이다",
            "block_range": "31-40",
            "time_window": "1925년 1월~1928년 12월",
            "front_sectors": ["식민지 행정", "은행/금융", "철도/인프라"],
            "support_sectors": ["가명 법인", "경매", "전기·창고"],
            "main_opponents": ["구도 겐이치", "친일 지주 연합", "동양척식 라인"],
            "new_npcs": ["민도식", "윤창식", "구도 겐이치"],
            "emotion_curve": "경성 잠입 -> 문서전 -> 담보권 확대 -> 총독부 채권자",
            "quiet_blocks": [37],
            "defeat_blocks": [35],
            "knowledge_used": "토지조사 이후의 문서 체계, 조선은행 감자 압박, 철도 예정선과 역세권 가치 변화를 먼저 읽는다.",
            "default_sources": source_binding([COLONIAL], [RAIL]),
            "default_partner": "경성 등기·경매 법률선",
            "blocks": [
                slot("경성의 가명 법인", "강윤은 황자로 복귀하지 않고 가명 법인 여러 개로 경성에 들어온다.", "1925년 1월", "경성 중구 상사회관", "식민지 행정", "가명 법인 설립", "황족의 이름은 감시를 부르고 법인의 이름은 서류를 부른다는 점을 이용한다.", "구도 겐이치", ["민도식", "윤창식"], hist("식민지 행정이 자산을 금융상품으로 바꾸는 구조", 1925, "가명 법인으로 등기와 담보 실행의 실명 리스크를 피한다.", COLONIAL), "deception", 7, 7, "2주", "경성 복귀를 정체 공개가 아니라 문서 침투로 시작한다.", foreshadow=["Block 68의 경성 실소유주 선언은 이 가명 법인 구조를 끝까지 밀어붙인 결과다."]),
                slot("토지조사 뒤편", "토지조사사업이 끝난 뒤 누가 진짜 소유주인지보다 누가 문서를 쥐었는지가 더 중요해진다.", "1925년 봄", "경성 토지대장 열람실", "식민지 행정", "토지대장 선별 열람", "강윤은 땅값보다 명의가 꼬인 필지를 먼저 고른다.", "구도 겐이치", ["윤창식", "민도식"], hist("토지조사사업 이후 국유 경작지와 문서화된 권리", 1919, "등기와 지세 자료를 담보 대상 명부로 다시 읽는다.", COLONIAL), "realization", 6, 6, "10일", "식민지 조선은 이미 장부 나라가 되었다는 걸 확인한다."),
                slot("경매 공고 한 장", "강윤은 신문 하단의 경매 공고 한 장에서 다음 역세권의 주인을 찾는다.", "1925년 여름", "경성 법원 게시판", "은행/금융", "경매 입찰 선점", "사람들이 기사 제목을 읽을 때 그는 경매 공고와 채권 순위를 먼저 읽는다.", "친일 지주 연합", ["윤창식"], hist("은행권과 담보 실행의 빠른 회수 구조", 1925, "경매 공고를 담보권 사냥의 실무 지도처럼 쓴다.", COLONIAL), "pressure", 6, 6, "1주", "강윤은 처음으로 경성의 자산을 공개 경매장에서 낚아챈다."),
                slot("친일지주의 상환일", "강윤은 지주의 체면이 아니라 상환일을 공격한다.", "1926년 초", "경성 / 용산 채권 협상실", "은행/금융", "연체채권 우회 매입", "돈이 모자란 지주에게 직접 돈을 빌려주는 대신 그의 채권자를 산다.", "친일 지주 연합", ["민도식"], hist("조선은행 부실채권 정리와 감자", 1925, "은행이 못 들고 갈 부실채권을 사서 우선순위를 바꾼다.", COLONIAL), "alliance", 7, 7, "2주", "사람을 설득하지 않고 만기일을 설득해 자산을 이동시킨다."),
                slot("철도 예정선 도면", "예정선 도면을 잘못 읽은 척한 날, 강윤은 측선 후보지를 놓치고 손실을 본다.", "1926년 가을", "총독부 철도국 도면실 인근", "철도/인프라", "예정선 주변 부지 선점", "정보 우위를 믿고 너무 일찍 들어갔다가 노선 변경과 인허가 지연을 한 번에 맞는다.", "구도 겐이치", ["윤창식", "구도 겐이치"], hist("철도 예정선 정보가 역세권 가치의 선행 신호가 되는 구조", 1926, "도면 정보만 믿고 들어가면 행정 최종결정 하나에 흔들린다는 대가를 치른다.", RAIL), "defeat", 8, 8, "3주", "도면은 읽어도 권력 없인 선로를 못 깐다는 사실을 배운다.", foreshadow=["Block 48의 측선과 제분소, Block 64의 광산보다 선로에서 이 실패가 뒤집힌다."]),
                slot("창고가 역을 먹는다", "강윤은 역세권 땅보다 창고증권과 입출고 권리가 먼저라는 걸 깨닫는다.", "1927년 초", "경성역 배후 창고군", "철도/인프라", "창고권 선점", "역 그 자체보다 창고가 화물을 붙잡는 시간이 더 길다는 점을 파고든다.", "구도 겐이치", ["민도식", "윤창식"], hist("철도역과 창고의 결합 구조", 1927, "역 주변 창고를 선점해 화차 배정과 환적 정보를 먼저 잡는다.", RAIL), "breakthrough", 8, 7, "2주", "역을 못 먹어도 역 앞 창고를 먹으면 화물 흐름이 따라온다."),
                slot("경성 등기 변호사", "윤창식은 강윤에게 경매, 등기, 채권 실행을 하나의 흐름으로 보여 준다.", "1927년 봄", "경성 종로 변호사 사무실", "식민지 행정", "등기·경매 자문 독점", "강윤은 법률비용을 아끼지 않고 등기와 담보 실행 속도를 돈으로 산다.", "친일 지주 연합", ["윤창식"], hist("식민지 행정에서 문서화가 곧 자산화라는 구조", 1927, "실물보다 문서와 기한을 쥔 사람이 이긴다.", COLONIAL), "quiet", 5, 4, "10일", "경성에서 처음으로 자기 편 서류 설계자를 얻는다.", callback=["Block 31의 가명 법인이 윤창식의 손에서 실제 실행 기계로 바뀐다."]),
                slot("동양척식 잔금표", "동양척식 계열 토지와 회사의 잔금표를 읽으며 강윤은 일본 자본의 약한 고리를 찾는다.", "1928년 초", "경성 동양척식 관련 장부선", "은행/금융", "식민지 회사 잔금 인수", "명목자본보다 실제 불입과 잔금 일정의 틈을 읽고 들어간다.", "동양척식 라인", ["민도식", "윤창식"], hist("동아권업주식회사 명목자본과 불입자본 괴리", 1921, "실제 불입자본보다 과장된 외형을 담보권 매집의 표적으로 삼는다.", COLONIAL), "pressure", 7, 7, "2주", "식민지 개발회사의 겉과 속이 얼마나 다른지 돈으로 확인한다."),
                slot("전기회사 우선주", "강윤은 광산보다 먼저 전기를, 토지보다 먼저 우선주를 산다.", "1928년 여름", "경성 전기회사 주주총회장", "은행/금융", "우선주·배당권 매입", "사람들은 경영권을 쫓을 때 강윤은 전기와 선로를 멈추지 않게 하는 우선권을 사 모은다.", "동양척식 라인", ["민도식"], hist("전력과 철도, 광산이 전시 이전부터 한 포트폴리오로 묶이기 시작하는 구조", 1928, "배당보다 병목이 중요한 자산을 고른다.", COLONIAL), "alliance", 7, 6, "2주", "표면 지분보다 실제 멈출 수 없는 자산을 선점한다."),
                slot("총독부의 채권자", "1928년 말 강윤은 드디어 총독부가 굴리는 회사를 빚으로부터 조르는 위치에 선다.", "1928년 겨울", "경성 총독부 인근 금융사무실", "은행/금융", "총독부 연계 회사 채권자 지위 확보", "정면 충돌 대신 총독부가 원하는 물류와 전력, 창고 회사의 채권자를 먼저 먹는다.", "구도 겐이치", ["윤창식", "구도 겐이치"], hist("식민지 행정에서 은행·철도·인허가가 하나로 묶이는 구조", 1928, "총독부가 직접 가진 것이 아니라 굴려야 하는 회사의 채권자를 장악한다.", COLONIAL), "triumph", 8, 7, "2주", "황제가 아닌 채권자가 되는 길이 처음 현실이 된다.", callback=["Block 30의 '조선을 담보로'라는 결심이 Block 40에서 첫 형태를 갖춘다."]),
            ],
        },
        {
            "arc_id": "ARC-05",
            "title": "대공황, 제국은 헐값이 된다",
            "block_range": "41-50",
            "time_window": "1929년 1월~1932년 12월",
            "front_sectors": ["은행/금융", "항만", "창고", "철도/인프라"],
            "support_sectors": ["쌀·곡물 담보", "환율", "부두 매입"],
            "main_opponents": ["에드워드 블레이크", "구도 겐이치", "친일 지주 연합"],
            "new_npcs": [],
            "emotion_curve": "폭락 감지 -> 파운드 충격 -> 담보권 사냥 -> 저가 제국",
            "quiet_blocks": [],
            "defeat_blocks": [42, 47],
            "knowledge_used": "대공황, 파운드 절하, 쌀값 하락, 창고증권 제도화를 미리 알고 공황을 사냥한다.",
            "default_sources": source_binding([EU, COLONIAL], [BANK_FX, RAIL]),
            "default_partner": "로테르담 항만 금융선",
            "blocks": [
                slot("빈 부두의 가격", "강윤은 비어 버린 부두와 창고의 가격표를 먼저 읽는다.", "1929년 가을", "로테르담 공실 부두", "항만", "부두·창고 저가 매입", "물동량이 줄수록 진짜 값은 줄어드는 게 아니라 손바뀜 속도가 빨라진다고 본다.", "에드워드 블레이크", ["헨드릭 판데르벨트"], hist("대공황과 유럽 무역금융 붕괴", 1929, "로테르담 물동량 급감 구간을 저가 매집의 시작점으로 삼는다.", EU), "aftermath", 6, 6, "3주", "공황은 공포가 아니라 인수 속도의 문제라고 판단한다."),
                slot("파운드가 미끄러진 날", "1931년 9월 파운드가 금본위를 이탈하자 강윤도 일부 포지션을 잃는다.", "1931년 9월", "런던 / 취리히 외환실", "금·외환", "파운드 이탈 대응", "파운드 절하를 예측했어도 모든 계약을 중립통화로 옮기지 못한 탓에 손실과 환차익이 동시에 터진다.", "에드워드 블레이크", ["소피 아들러"], hist("영국 금본위 이탈과 파운드 평가절하", 1931, "파운드 포지션을 프랑과 달러로 바꿔 뒀지만 잔여 계약은 손실로 남는다.", EU), "defeat", 8, 8, "1주", "환율을 이겨도 계약 만기는 한순간에 흔들릴 수 있다는 걸 다시 배운다.", callback=["Block 7의 금 전환, Block 16의 중립국 계좌가 있었기에 전부 무너지진 않는다."]),
                slot("로테르담 저점 매수", "강윤은 공황이 가장 깊을 때 로테르담 저점 자산을 쓸어 담는다.", "1931년 가을", "로테르담 부두권 경매장", "항만", "저점 부두권 매수", "경기 회복 시점을 맞히려 하지 않고 살아남을 자산의 위치만 본다.", "에드워드 블레이크", ["헨드릭 판데르벨트"], hist("1932년 로테르담 항만 화물처리량 2,600만 톤 저점", 1932, "빈 부두를 임대수익과 담보가치 양쪽에서 계산한다.", EU), "breakthrough", 8, 7, "2주", "불황의 바닥에서 물류의 목을 더 굵게 움켜쥔다."),
                slot("쌀값 한 칸", "쌀값 한 칸이 내려가자 조선의 농지와 창고 담보 명부가 줄줄이 흔들린다.", "1930년 겨울", "경성 곡물상회 / 조선은행 대출창구", "은행/금융", "곡물 담보 재평가", "강윤은 쌀 본체보다 쌀이 머무는 창고와 선로 접근권을 골라 잡는다.", "친일 지주 연합", ["민도식"], hist("쌀값 하락으로 농지·창고 담보가 재평가됨", 1930, "곡물 담보가 흔들릴 때 저장 설비와 운송권부터 사냥한다.", COLONIAL), "pressure", 7, 7, "2주", "농지보다 창고가 더 빠르게 소유주를 바꾼다는 사실을 증명한다."),
                slot("창고증권 한 장", "강윤은 곡물보다 창고증권 한 장이 더 빨리 사람을 굴복시킨다는 걸 이용한다.", "1931년 봄", "경성 창고업자 조합", "철도/인프라", "창고증권 담보 인수", "입고된 물건보다 증권과 실행 순위가 더 중요하다고 보고 문서부터 사 모은다.", "구도 겐이치", ["윤창식", "민도식"], hist("조선농업창고업령으로 창고증권 담보가 제도화", 1931, "보관소를 채권과 경매의 관문으로 재해석한다.", COLONIAL), "realization", 7, 7, "2주", "창고가 단순 보관소에서 금융 장치로 변한 순간을 붙잡는다.", foreshadow=["Block 56의 통화권 분리, Block 66의 조선 월세에 창고증권 수익 구조가 이어진다."]),
                slot("연체 명부", "연체 명부를 들고 있는 쪽이 공황기의 진짜 실력자다.", "1931년 여름", "경성 / 부산 은행 연체자료실", "은행/금융", "연체채권 명부 선점", "강윤은 부동산 광고가 아니라 연체 명부에서 다음 인수 대상을 고른다.", "친일 지주 연합", ["윤창식"], hist("조선은행 감자 후 자본금 축소와 연체 정리 압박", 1931, "연체 명부를 통해 담보 실행 타이밍을 먼저 읽는다.", COLONIAL), "pressure", 7, 7, "10일", "공황기의 지도는 지도책이 아니라 연체표라는 걸 보여 준다."),
                slot("중복 담보 함정", "같은 창고와 같은 곡물이 중복 담보로 잡힌 사실이 터지며 강윤도 한 번 물린다.", "1931년 가을", "경성 창고증권 정산선", "은행/금융", "중복 담보 정리", "문서가 표준화됐다고 해서 정직해진 건 아니며, 강윤도 한 차례 허위 입고와 이중 담보에 휘말린다.", "구도 겐이치", ["윤창식"], hist("창고증권 제도화의 역면인 중복 담보 위험", 1931, "문서 자체를 다시 검증하는 실무 체계를 갖추기 전 손실을 본다.", COLONIAL), "defeat", 8, 8, "2주", "문서의 시대에도 결국 문서를 검증할 사람을 먼저 쥐어야 한다는 교훈을 얻는다.", callback=["Block 45에서 먹은 창고증권 구조가 바로 다음 칼날이 되어 돌아온다."]),
                slot("측선과 제분소", "강윤은 역세권보다 측선과 제분소가 붙은 자산을 통째로 묶는다.", "1932년 초", "경성 외곽 측선 부지", "철도/인프라", "측선·제분소 패키지 매입", "곡물 창고만 갖고는 부족하고 측선과 가공설비까지 묶어야 병목이 된다고 판단한다.", "구도 겐이치", ["민도식"], hist("철도 인프라와 창고, 가공시설의 결합 구조", 1932, "측선 허가와 제분소 배후 창고를 묶어 회전율을 장악한다.", RAIL), "breakthrough", 8, 7, "3주", "공황기의 진짜 값은 토지가 아니라 연결선에 있음을 보여 준다.", callback=["Block 35에서 도면으로만 쫓다가 실패한 선로를 이제 실물 측선으로 뒤집는다."]),
                slot("배당보다 병목", "강윤은 배당 잘 나오는 회사보다 멈출 수 없는 병목 설비를 더 높게 친다.", "1932년 여름", "경성 / 취리히 공동투자 회의", "은행/금융", "병목 자산 재배치", "겉보기 수익률보다 전시와 공황 양쪽에서 죽지 않을 자산만 남긴다.", "오쿠라 다카시", ["소피 아들러"], hist("철도·창고·전력 결합 자산의 전략성 부각", 1932, "배당보다 우선배정권과 실행권을 기준으로 포트폴리오를 재편한다.", COLONIAL), "resolve", 6, 6, "2주", "강윤의 제국이 단순 투기물이 아니라 병목 컬렉션으로 변한다."),
                slot("헐값의 제국", "1932년 말 강윤은 대공황 속에서 이미 조선과 유럽 양쪽의 헐값 자산을 제국으로 엮어 버린다.", "1932년 겨울", "경성 / 로테르담 / 취리히 공동정산선", "은행/금융", "공황 자산 통합 포트폴리오", "값싸게 산 자산을 함부로 올려치지 않고, 연결해 둘 때만 진짜 제국이 된다고 본다.", "오쿠라 다카시", ["소피 아들러", "윤창식"], hist("대공황기 자산가치 붕괴와 현금 우위", 1932, "조선의 창고·철도·전기와 유럽의 항만·금융자산을 하나의 결제선으로 묶는다.", EU), "triumph", 9, 7, "3주", "공황을 버틴 자가 제국의 밑그림을 완성한다.", callback=["Block 41에서 보기 시작한 빈 부두, Block 44의 쌀값 붕괴, Block 48의 측선 매입이 모두 한 장부로 합쳐진다."]),
            ],
        },
    ]
)
