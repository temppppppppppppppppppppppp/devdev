#!/usr/bin/env python3
"""Repair garbled TR text and normalize to usable UTF-8 Korean."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TREATMENTS_DIR = ROOT / "treatments"


@dataclass
class StoryConfig:
    key: str
    title_base: str
    protagonist: str
    base_capital_eok: int
    sectors: list[str]
    locations: list[str]
    opponent: str
    global_partner: str
    is_regressor: bool
    regression_type: str
    incarnation_type: str
    single_heir_policy: str
    ally_a: str
    ally_b: str


CONFIGS: dict[str, StoryConfig] = {
    "dynasty_heir_possession": StoryConfig(
        key="dynasty_heir_possession",
        title_base="재벌가 빙의 후 승계전",
        protagonist="차도혁",
        base_capital_eok=80,
        sectors=["지주구조", "금융", "반도체", "에너지", "물류", "바이오", "유통", "플랫폼"],
        locations=["서울 성북동 본가 집무실", "여의도 본사 전략실", "판교 데이터센터", "부산 물류허브", "싱가포르 파트너 오피스"],
        opponent="구경영진 연합",
        global_partner="Global Mega Fund",
        is_regressor=False,
        regression_type="빙의",
        incarnation_type="빙의자",
        single_heir_policy="재벌가 독남 단독 승계",
        ally_a="채지훈 부회장",
        ally_b="서현주 CFO",
    ),
    "franchise_tycoon_possession": StoryConfig(
        key="franchise_tycoon_possession",
        title_base="프랜차이즈 제국 빙의",
        protagonist="강우진",
        base_capital_eok=70,
        sectors=["식자재", "가맹운영", "물류", "해외진출", "브랜드", "디지털주문", "공장자동화", "리테일"],
        locations=["강남 통합상황실", "송파 R&D 키친", "이천 물류센터", "부산 가맹지원센터", "도쿄 파트너 오피스"],
        opponent="경쟁 프랜차이즈 연합",
        global_partner="Global Food Trader",
        is_regressor=False,
        regression_type="빙의",
        incarnation_type="빙의자",
        single_heir_policy="창업주 직계 단독 경영 승계",
        ally_a="오민석 운영본부장",
        ally_b="장세라 브랜드총괄",
    ),
    "entertainment_ceo_possession": StoryConfig(
        key="entertainment_ceo_possession",
        title_base="엔터 제국 CEO 빙의",
        protagonist="민이현",
        base_capital_eok=60,
        sectors=["아이돌IP", "드라마", "콘서트", "플랫폼", "광고", "글로벌유통", "팬덤커머스", "연습생시스템"],
        locations=["청담 제작센터", "상암 콘텐츠랩", "잠실 공연장 백오피스", "판교 플랫폼센터", "LA 협업 스튜디오"],
        opponent="기득권 제작사 카르텔",
        global_partner="NA Streaming Partner",
        is_regressor=False,
        regression_type="빙의",
        incarnation_type="빙의자",
        single_heir_policy="엔터 지주사 단독 경영 승계",
        ally_a="윤서진 제작총괄",
        ally_b="정하민 A&R 디렉터",
    ),
    "northstar_logistics": StoryConfig(
        key="northstar_logistics",
        title_base="노스스타 물류 패권",
        protagonist="윤태성",
        base_capital_eok=80,
        sectors=["해운", "항공화물", "내륙운송", "콜드체인", "항만운영", "창고자동화", "운임헤지", "공급망데이터"],
        locations=["인천 통합관제센터", "부산 항만전략실", "김포 항공화물 터미널", "평택 스마트창고", "로테르담 연락사무소"],
        opponent="운임 담합 카르텔",
        global_partner="NorthSea Shipping Alliance",
        is_regressor=True,
        regression_type="회귀",
        incarnation_type="회귀자",
        single_heir_policy="재벌 3세 독남 단독 승계",
        ally_a="박준호 운항본부장",
        ally_b="조라희 데이터전략실장",
    ),
    "quantum_bio": StoryConfig(
        key="quantum_bio",
        title_base="퀀텀바이오 역전 시나리오",
        protagonist="서지안",
        base_capital_eok=60,
        sectors=["항암제", "면역치료", "플랫폼기술", "CMO", "임상전략", "규제대응", "기술수출", "AI신약"],
        locations=["송도 연구캠퍼스", "대전 전임상센터", "판교 분석랩", "세종 규제협의실", "보스턴 BD 오피스"],
        opponent="공매도 세력 연합",
        global_partner="Global Biotech Holdings",
        is_regressor=True,
        regression_type="회귀",
        incarnation_type="회귀자",
        single_heir_policy="재벌 2세 단독 승계",
        ally_a="김수연 임상총괄",
        ally_b="최도윤 BD 이사",
    ),
    "aegis_city": StoryConfig(
        key="aegis_city",
        title_base="이지스 시티 인프라 전쟁",
        protagonist="한도준",
        base_capital_eok=100,
        sectors=["도시개발", "모빌리티", "전력망", "수처리", "스마트시티", "PF금융", "건설소재", "에너지관리"],
        locations=["세종 정책협의실", "서울 인프라본부", "부산 현장통합관제실", "인천 신도시 PMO", "두바이 파트너 오피스"],
        opponent="정경 카르텔 연합",
        global_partner="CityInfra Partners",
        is_regressor=True,
        regression_type="회귀",
        incarnation_type="회귀자",
        single_heir_policy="재벌 3세 독남 단독 승계",
        ally_a="이은호 인프라본부장",
        ally_b="한지민 정책협력실장",
    ),
    "aurora_media": StoryConfig(
        key="aurora_media",
        title_base="오로라 미디어 패권",
        protagonist="이태윤",
        base_capital_eok=60,
        sectors=["포맷개발", "OTT유통", "광고테크", "IP라이선스", "숏폼", "커머스", "해외합작", "데이터분석"],
        locations=["상암 미디어센터", "강남 광고전략실", "판교 데이터허브", "부산 영상스튜디오", "도쿄 유통협의실"],
        opponent="레거시 미디어 연합",
        global_partner="Global Media Syndicate",
        is_regressor=True,
        regression_type="회귀",
        incarnation_type="회귀자",
        single_heir_policy="재벌 3세 독남 단독 승계",
        ally_a="강시온 콘텐츠총괄",
        ally_b="배지후 광고사업본부장",
    ),
    "empire_reborn": StoryConfig(
        key="empire_reborn",
        title_base="폐허에서 돌아온 후계자",
        protagonist="강도윤",
        base_capital_eok=90,
        sectors=["반도체", "에너지", "방산", "바이오", "플랫폼", "물류", "건설", "금융"],
        locations=["서울 본사 전시상황실", "판교 전략캠퍼스", "부산 수출기지", "울산 생산통합센터", "싱가포르 글로벌오피스"],
        opponent="제국 견제 연합",
        global_partner="Global Sovereign Consortium",
        is_regressor=True,
        regression_type="회귀",
        incarnation_type="회귀자",
        single_heir_policy="재벌 3세 독남 단독 승계",
        ally_a="강현서 전략실장",
        ally_b="문채린 재무총괄",
    ),
}


def strip_suffix(stem: str) -> str:
    return stem.replace("_tr_block_070_draft", "")


def needs_repair(text: Any) -> bool:
    if not isinstance(text, str):
        return True
    value = text.strip()
    if not value:
        return True
    q = value.count("?")
    if "???" in value:
        return True
    if q >= 2:
        return True
    if q / max(len(value), 1) >= 0.04:
        return True
    return False


def keep_or_replace(current: Any, replacement: str) -> str:
    if needs_repair(current):
        return replacement
    return str(current).strip()


def normalize_time(raw: Any, idx: int) -> str:
    if isinstance(raw, str):
        text = raw.strip()
        if "년" in text and "월" in text and not needs_repair(text):
            return text
        nums = re.findall(r"\d+", text)
        if len(nums) >= 2:
            year = int(nums[0])
            month = max(1, min(12, int(nums[1])))
            return f"{year}년 {month}월"

    month_cursor = ((idx - 1) * 4) % 12 + 1
    year_cursor = 2006 + ((idx - 1) * 4) // 12
    return f"{year_cursor}년 {month_cursor}월"


def money_str(eok: int) -> str:
    if eok >= 10_000:
        jo = eok // 10_000
        rest = eok % 10_000
        return f"{jo}조 {rest}억" if rest else f"{jo}조"
    return f"{eok}억"


def capital_profile(base_eok: int, idx: int) -> tuple[int, int, int]:
    before = base_eok + (idx - 1) * (22 + idx * 4)
    delta = max(30, int(before * 0.14))
    after = before + delta
    return before, after, delta


def emotional_type(idx: int) -> str:
    cycle = ["resolve", "pressure", "breakthrough", "victory"]
    return cycle[(idx - 1) % len(cycle)]


PHASES: list[tuple[str, str, str]] = [
    ("기반 구축", "현금흐름 방어선 확립", "초기 진입"),
    ("권한 장악", "의사결정권 집중", "내부 통제"),
    ("사업 확장", "핵심 사업군 다각화", "규모 성장"),
    ("외연 진출", "해외 파트너십 확장", "글로벌 전환"),
    ("충격 대응", "위기 구간 역이용", "리스크 관리"),
    ("지배 강화", "지배구조 재편", "경영 안정"),
    ("최종 도약", "시장 표준 선점", "체제 완성"),
]

CONTEXT_TEMPLATES = [
    "{time} {pro}은 {sector} 라인의 병목을 해소하기 위해 자금·인력 배치를 동시에 재조정했다. {phase_goal}이 이번 라운드의 1순위 과제다.",
    "{time} {pro}은 {sector} 수익구조를 재산정하고 손익분기점을 앞당기는 실행안을 확정했다. 목표는 {phase_goal}이다.",
    "{time} {pro}은 {sector} 의사결정 체계를 단일 라인으로 정리해 승인 지연을 끊어냈다. 이번 단계는 {phase_goal}에 집중한다.",
    "{time} {pro}은 {sector}에서 원가·납기·품질 지표를 한 화면으로 통합해 즉시 대응 체계를 만들었다. 핵심은 {phase_goal}이다.",
    "{time} {pro}은 {sector} 프로젝트를 고정비 중심에서 성과연동 구조로 전환했다. 이번 라운드의 미션은 {phase_goal}이다.",
    "{time} {pro}은 {sector} 투자집행 순서를 재편해 현금 소모 구간을 짧게 만들었다. 목표는 {phase_goal} 달성이다.",
]

VILLAIN_TEMPLATES = [
    "{opponent}이 {sector} 관련 인허가 절차를 지연시키며 일정 리스크를 키웠다. 외부에서는 계획이 흔들린 것으로 본다.",
    "{opponent}이 공급망 단가를 흔들어 {sector} 수익성 압박을 유도했다. 표면적으로는 주인공 측이 수세다.",
    "{opponent}이 여론과 내부 이해관계를 엮어 {sector} 의사결정 속도를 늦추려 했다. 시장은 결렬 가능성을 반영하기 시작했다.",
    "{opponent}이 핵심 실무 인력을 빼가며 {sector} 추진 동력을 약화시키려 했다. 단기 체감은 불리한 흐름이다.",
    "{opponent}이 계약 조건을 일방적으로 재해석해 {sector} 딜의 신뢰를 흔들었다. 외부 관측치는 부정적으로 기울었다.",
    "{opponent}이 규제 창구와 금융 창구를 동시에 압박해 {sector} 실행을 지연시키려 했다. 표면 시그널은 패배에 가깝다.",
]

SOLUTION_TEMPLATES = [
    "{pro}은 우선순위 투자안을 공개해 이해관계자 표를 재정렬했고, {partner_phrase} 협상에서 옵션 조항을 선점했다.",
    "{pro}은 계약 구조를 단계형으로 쪼개 리스크를 분산했고, {partner_phrase} 실무 라인을 직결해 집행 속도를 확보했다.",
    "{pro}은 성과연동 조건을 전면에 배치해 반대 명분을 제거했고, {partner_phrase} 조달 조건을 유리하게 재설정했다.",
    "{pro}은 납기·품질 KPI를 패키지로 제시해 내부 반대를 잠재우고, {partner_phrase} 공동 실행계획을 확정했다.",
    "{pro}은 손실 구간을 먼저 정리한 뒤 확장안을 내는 역순 전략으로 신뢰를 회복했고, {partner_phrase} 장기 옵션을 묶었다.",
    "{pro}은 위험자산과 성장자산을 분리해 의사결정을 단순화했고, {partner_phrase} 협상에서 정보 비대칭을 역이용했다.",
]

REWARD_TEMPLATES = [
    "실행 이후 자산은 {before}에서 {after}(+{delta})으로 증가했고, 내부 승인 리드타임이 단축됐다.",
    "이번 라운드 성과로 자산이 {before}에서 {after}(+{delta})로 확대되며 후속 투자 여력이 커졌다.",
    "딜 구조 개선 효과로 자산이 {before}→{after}(+{delta})로 상승했고, 조직 신뢰도 지표가 개선됐다.",
    "핵심 지표를 방어한 결과 자산이 {before}에서 {after}(+{delta})로 커졌고, 다음 분기 집행권이 강화됐다.",
    "수익성 복원과 비용 절감이 동시에 작동해 자산이 {before}에서 {after}(+{delta})로 늘었다.",
    "리스크를 통제한 채 성장 폭을 확보해 자산이 {before}에서 {after}(+{delta})로 올라섰다.",
]

STAKES_TEMPLATES = [
    "이번 라운드에서 {sector} 실행이 지연되면 다음 분기 투자집행 창이 닫혀 주도권이 {opponent}으로 이동한다.",
    "{sector} 의사결정을 놓치면 자금회전이 꺾여 연쇄적으로 후속 프로젝트 승인률이 하락한다.",
    "{sector} 구간에서 밀리면 내부 신뢰와 외부 신뢰가 동시에 훼손돼 협상 비용이 급증한다.",
    "{sector} 확장 타이밍을 놓치면 분기 실적과 지배구조 이슈가 겹치며 방어가 어려워진다.",
    "{sector} 라운드를 실패하면 다음 단계의 조달 조건이 불리해져 성장 속도가 급감한다.",
    "{sector}에서 밀리면 핵심 파트너의 협상 우선권이 역전되어 전략 전체가 지연된다.",
]

POWER_PRO_TEMPLATES = [
    "{pro}은 성과 지표를 근거로 투자·인사·계약 권한을 동시에 확보했다.",
    "{pro}은 반대파의 명분을 수치로 해체하며 핵심 계열사 조정권을 강화했다.",
    "{pro}은 실행 속도와 수익률을 입증해 이사회 의결 주도권을 가져왔다.",
    "{pro}은 위기 대응 성과로 실무 조직의 신뢰를 결집시키며 지휘권을 확대했다.",
    "{pro}은 비용 구조 개선을 증명해 장기 프로젝트 우선순위를 직접 통제하게 됐다.",
    "{pro}은 협상 결과를 실적으로 연결해 조직 내 영향력을 한 단계 올렸다.",
]

POWER_ANT_TEMPLATES = [
    "{opponent}은 단기 지연에는 성공했지만 실적 지표에서 명분을 잃었다.",
    "{opponent}은 여론전은 만들었으나 계약 조건 경쟁에서 밀려 후퇴했다.",
    "{opponent}은 협상 판을 흔들었지만 실행 단계에서 통제력을 상실했다.",
    "{opponent}은 공격 타이밍을 맞췄지만 자금·인력 동원전에서 패했다.",
    "{opponent}은 표면상 우위를 점했으나 핵심 파트너 연결이 끊기며 수세로 전환됐다.",
    "{opponent}은 규제 변수를 이용했지만 장기 계약 레버리지를 뺏기며 불리해졌다.",
]

FORESHADOW_TEMPLATES_1 = [
    "다음 블록에서는 {next_sector} 라인에서 규제와 수익성 문제가 동시에 터진다.",
    "다음 라운드는 {next_sector}에서 파트너 재협상이 핵심 변수가 된다.",
    "후속 블록에서 {next_sector} 프로젝트의 일정 충돌이 발생할 가능성이 높다.",
    "다음 단계는 {next_sector}의 자금조달 조건이 승패를 가른다.",
    "다음 블록에서는 {next_sector} 관련 대외 변수로 의사결정 속도가 시험대에 오른다.",
    "후속 라운드는 {next_sector} 구간의 원가 변동을 누가 먼저 제어하느냐가 관건이다.",
]

FORESHADOW_TEMPLATES_2 = [
    "{partner}의 비공개 요구조건이 다음 협상의 레버리지로 작동한다.",
    "지금 확보한 옵션 조항이 후속 분기 손익 방어선이 된다.",
    "이번에 묶어둔 계약 우선권이 다음 위기 구간의 안전장치가 된다.",
    "현재의 지표 개선이 다음 라운드 신용도 평가를 좌우한다.",
    "이번 선택이 다음 블록의 의결권 분포에 직접 영향을 준다.",
    "지금 만든 실행 체계가 다음 분기 확장 속도를 결정한다.",
]


def pick(values: list[str], idx: int, salt: int = 0) -> str:
    if not values:
        return ""
    return values[(idx + salt) % len(values)]


def phase_bundle(idx: int) -> tuple[str, str, str]:
    phase_idx = min((idx - 1) // 10, len(PHASES) - 1)
    return PHASES[phase_idx]


def has_batchim(char: str) -> bool:
    if not char or not ("가" <= char <= "힣"):
        return False
    return (ord(char) - 0xAC00) % 28 != 0


def partner_phrase(name: str) -> str:
    clean = (name or "").strip()
    if not clean:
        return "파트너와의"
    last = clean[-1]
    if "가" <= last <= "힣":
        return f"{clean}{'과' if has_batchim(last) else '와'}의"
    return f"{clean}와의"


def normalize_title(raw: Any, cfg: StoryConfig, idx: int, phase_name: str, preserve_original: bool) -> str:
    if preserve_original and isinstance(raw, str):
        title = raw.strip()
        if title and not needs_repair(title):
            return title
    return f"{cfg.title_base} {idx} - {phase_name}"


def parse_capital(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    text = value.replace(" ", "")
    m = re.fullmatch(r"(?:(\d+)조)?(?:(\d+)억)?", text)
    if not m:
        return None
    jo = int(m.group(1) or 0)
    eok = int(m.group(2) or 0)
    return jo * 10_000 + eok


def ensure_progressive_capital(
    prev_after_eok: int | None, base_eok: int, idx: int
) -> tuple[int, int, int]:
    before, after, delta = capital_profile(base_eok, idx)
    if prev_after_eok is None:
        return before, after, delta
    if before < prev_after_eok:
        before = prev_after_eok + max(5, idx // 2)
        delta = max(30, int(before * 0.11))
        after = before + delta
    return before, after, delta


def fix_block(block: dict[str, Any], idx: int, cfg: StoryConfig, prev_after_eok: int | None = None) -> dict[str, Any]:
    sector = cfg.sectors[(idx - 1) % len(cfg.sectors)]
    place = cfg.locations[(idx - 1) % len(cfg.locations)]
    prev_sector = cfg.sectors[(idx - 2) % len(cfg.sectors)] if idx > 1 else sector
    next_sector = cfg.sectors[idx % len(cfg.sectors)]
    in_story_time = normalize_time((block.get("time_span") or {}).get("in_story_time"), idx)

    phase_name, phase_goal, phase_tag = phase_bundle(idx)

    cap_before, cap_after, cap_delta = ensure_progressive_capital(prev_after_eok, cfg.base_capital_eok, idx)

    context_tpl = pick(CONTEXT_TEMPLATES, idx, salt=len(cfg.key))
    villain_tpl = pick(VILLAIN_TEMPLATES, idx, salt=len(cfg.protagonist))
    solution_tpl = pick(SOLUTION_TEMPLATES, idx, salt=len(cfg.global_partner))
    reward_tpl = pick(REWARD_TEMPLATES, idx, salt=idx // 3)
    stakes_tpl = pick(STAKES_TEMPLATES, idx, salt=idx // 5)
    power_pro_tpl = pick(POWER_PRO_TEMPLATES, idx, salt=idx // 7)
    power_ant_tpl = pick(POWER_ANT_TEMPLATES, idx, salt=idx // 9)
    foreshadow1_tpl = pick(FORESHADOW_TEMPLATES_1, idx, salt=idx // 4)
    foreshadow2_tpl = pick(FORESHADOW_TEMPLATES_2, idx, salt=idx // 6)

    generated_context = context_tpl.format(
        time=in_story_time,
        pro=cfg.protagonist,
        sector=sector,
        phase_goal=phase_goal,
    )
    generated_villain = villain_tpl.format(
        opponent=cfg.opponent,
        sector=sector,
    ) + f" ({phase_name} {idx}차 국면)"
    generated_solution = solution_tpl.format(
        pro=cfg.protagonist,
        partner_phrase=partner_phrase(cfg.global_partner),
    ) + f" [실행코드:{cfg.key[:3].upper()}-{idx:02d}]"
    generated_reward = reward_tpl.format(
        before=money_str(cap_before),
        after=money_str(cap_after),
        delta=money_str(cap_delta),
    ) + f" ({phase_tag} 단계 성과)"
    generated_stakes = stakes_tpl.format(sector=sector, opponent=cfg.opponent) + f" [리스크 라운드 {idx}]"
    generated_power_pro = power_pro_tpl.format(pro=cfg.protagonist) + f" ({sector} 지휘권 강화 / 권한스택 {idx})"
    generated_power_ant = power_ant_tpl.format(opponent=cfg.opponent) + f" ({phase_name} 대응 실패 / 방어손실 {idx})"
    generated_before_a = f"{cfg.ally_a}와의 협력은 제한적이었다."
    generated_after_a = f"{cfg.ally_a}가 {phase_tag} 구간의 핵심 실행 파트너가 되었다."
    generated_before_b = f"{cfg.ally_b}는 조건부 검토 입장이었다."
    generated_after_b = f"{cfg.ally_b}가 리스크·재무 통합안을 공동 주도했다."
    generated_foreshadow_1 = foreshadow1_tpl.format(next_sector=next_sector)
    generated_foreshadow_2 = foreshadow2_tpl.format(partner=cfg.global_partner)
    generated_callback = [] if idx == 1 else [f"직전 블록의 {prev_sector} 성과가 이번 {sector} 전환의 발판이 되었다."]

    content = block.get("content")
    if not isinstance(content, dict):
        content = {}
    block["content"] = {
        "context": generated_context,
        "event_villain": generated_villain,
        "solution": generated_solution,
        "reward": generated_reward,
    }

    block["title"] = normalize_title(
        block.get("title"), cfg, idx, phase_name, preserve_original=(cfg.key == "empire_reborn")
    )
    block["pov_character"] = cfg.protagonist
    block["stakes"] = generated_stakes

    power_shift = block.get("power_shift")
    if not isinstance(power_shift, dict):
        power_shift = {}
    block["power_shift"] = {
        "protagonist": generated_power_pro,
        "antagonist": generated_power_ant,
    }

    rel = block.get("relationship_delta")
    if not isinstance(rel, list) or len(rel) < 2:
        rel = [{}, {}]
    while len(rel) < 2:
        rel.append({})
    rel0 = rel[0] if isinstance(rel[0], dict) else {}
    rel1 = rel[1] if isinstance(rel[1], dict) else {}
    block["relationship_delta"] = [
        {
            "target": cfg.ally_a,
            "before": generated_before_a,
            "after": generated_after_a,
        },
        {
            "target": cfg.ally_b,
            "before": generated_before_b,
            "after": generated_after_b,
        },
    ]

    foreshadow = block.get("foreshadow")
    if not isinstance(foreshadow, list) or len(foreshadow) < 2:
        foreshadow = ["", ""]
    while len(foreshadow) < 2:
        foreshadow.append("")
    block["foreshadow"] = [
        generated_foreshadow_1,
        generated_foreshadow_2,
    ]

    callback = block.get("callback")
    if not isinstance(callback, list):
        callback = []
    if idx == 1:
        block["callback"] = []
    else:
        block["callback"] = generated_callback

    emotional = block.get("emotional_beat")
    if not isinstance(emotional, dict):
        emotional = {}
    block["emotional_beat"] = {
        "type": emotional_type(idx),
        "intensity": 7 + (idx % 3),
    }

    try:
        tension = int(block.get("tension_level", 8))
    except Exception:
        tension = 8
    block["tension_level"] = max(1, min(10, tension))

    location = block.get("location")
    if not isinstance(location, dict):
        location = {}
    block["location"] = {
        "place": place,
        "type": "사업 거점",
    }

    time_span = block.get("time_span")
    if not isinstance(time_span, dict):
        time_span = {}
    block["time_span"] = {
        "duration": "7일",
        "in_story_time": in_story_time,
    }
    block["time_span"]["in_story_time"] = normalize_time(block["time_span"]["in_story_time"], idx)

    genre_ext = block.get("genre_ext")
    if not isinstance(genre_ext, dict):
        genre_ext = {}
    new_genre_ext = {
        "capital_before": money_str(cap_before),
        "capital_after": money_str(cap_after),
        "capital_delta": f"+{money_str(cap_delta)}",
        "profit_loss": f"{money_str(cap_delta)} 증가",
        "method": f"{sector} 수익구조 정비 + 계약 단계화",
        "investment_type": f"{phase_tag} 목적의 {sector} 선제 투자",
        "deal_type": pick(
            ["전략 제휴", "옵션 계약", "지분 연계 계약", "장기 공급 계약", "공동 투자 계약"],
            idx,
            salt=idx // 2,
        ),
        "leverage_used": [
            "현금흐름 분석",
            "규제 타이밍 관리",
            "거점 선점",
            f"{phase_name} 실행 시퀀스 설계",
        ],
        "opponent": {
            "name": cfg.opponent,
            "type": "경쟁 연합",
            "weakness_exploited": pick(
                ["현금흐름 관리 부재", "조달 의사결정 지연", "장기계약 리스크 과소평가", "조직 분절화"],
                idx,
                salt=idx // 3,
            ),
        },
        "historical_event": f"{phase_name} / {sector} 전환 {idx}",
        "time_pressure": pick(
            [
                "분기 마감 전 계약 확정이 필요해 지연 시 기회비용이 급증한다.",
                "자금 조달 창이 짧아져 이번 라운드 내 의사결정이 필수다.",
                "공급망 슬롯이 제한되어 지연 시 원가가 빠르게 상승한다.",
                "외부 이슈가 겹쳐 실행 시점을 놓치면 밸류에이션이 할인된다.",
            ],
            idx,
            salt=idx // 4,
        ),
        "knowledge_used": pick(
            [
                "이전 사이클 실패 사례를 반대로 적용해 선제 대응했다.",
                "시장 반응 지표를 조합해 역추세 구간을 선점했다.",
                "과거 리스크 전이 패턴을 반영해 방어 우선순위를 재배치했다.",
                "실무 데이터와 정책 시그널을 결합해 집행 시점을 앞당겼다.",
            ],
            idx,
            salt=idx // 5,
        ),
        "risk_level": pick(["중", "중상", "상"], idx, salt=idx // 6),
        "business_sector": sector,
        "section_rotation": f"{phase_name} - {sector} 집중 로테이션",
        "global_partner": {
            "name": cfg.global_partner,
            "cadence": pick(["2블록 주기", "3블록 주기", "라운드별 점검"], idx, salt=idx // 7),
            "objective": pick(
                ["해외 판로 확보", "조달 안정성 강화", "공동 투자 확장", "리스크 헤지"],
                idx,
                salt=idx // 8,
            ),
        },
    }
    if "mogul_meeting_cycle" in genre_ext:
        new_genre_ext["mogul_meeting_cycle"] = "2블록"
    if "mogul_meeting_stage" in genre_ext:
        new_genre_ext["mogul_meeting_stage"] = f"{((idx - 1) % 5) + 1}차 라운드"
    if "mogul_surface_result" in genre_ext:
        new_genre_ext["mogul_surface_result"] = pick(
            ["표면상 보류", "조건부 검토", "추가 실사 요구", "가격 재협상 제안"],
            idx,
            salt=idx // 2,
        )
    if "mogul_real_result" in genre_ext:
        new_genre_ext["mogul_real_result"] = pick(
            ["실질 우선권 확보", "후속 투자 슬롯 선점", "장기 옵션 확보", "가격 밴드 유리화"],
            idx,
            salt=idx // 3,
        )
    if "success_pattern" in genre_ext:
        new_genre_ext["success_pattern"] = "겉패배처럼 보이지만 실승으로 귀결"
    if "setpiece_pass4" in genre_ext:
        new_genre_ext["setpiece_pass4"] = f"T{((idx - 1) % 9) + 1}"
    if "turning_point_level" in genre_ext:
        new_genre_ext["turning_point_level"] = "high" if idx % 5 == 0 else "mid"
    block["genre_ext"] = new_genre_ext

    regression_ext = block.get("regression_ext")
    if not isinstance(regression_ext, dict):
        regression_ext = {}
    new_reg_ext: dict[str, Any] = {
        "is_regressor": cfg.is_regressor,
        "regression_type": cfg.regression_type,
        "timeline_knowledge": {
            "info_used": f"{sector} 시장의 실패 패턴과 회복 타이밍",
            "accuracy": pick(["중", "중상", "상"], idx, salt=idx // 4),
            "source": "전 사이클 실무 데이터",
        },
        "butterfly_effect": {
            "original_event": f"{sector} 확장 지연",
            "changed_event": f"{sector} 선제 투자로 점유율 확보",
            "ripple_effect": f"{next_sector} 협상력 상승",
        },
        "death_flag": {
            "avoided": "연쇄 유동성 위기",
            "method": "현금흐름 선관리와 계약 분산",
        },
        "regression_hint": {
            "slip_up": pick(
                [
                    "타이밍을 너무 정확히 맞춰 주변의 의심이 커졌다.",
                    "리스크를 과도하게 선제 언급해 내부 경계가 올라갔다.",
                    "데이터 해석 속도가 비정상적으로 빠르다는 평가를 받았다.",
                ],
                idx,
                salt=idx // 5,
            ),
            "suspicion_from": cfg.opponent,
        },
        "future_prep": {
            "action": f"다음 블록 {next_sector} 선행 조사",
            "target_event": f"{cfg.title_base} 라운드 {idx + 1}",
        },
        "single_heir_policy": cfg.single_heir_policy,
    }
    if "incarnation_type" in regression_ext:
        new_reg_ext["incarnation_type"] = cfg.incarnation_type
    if "execution_doctrine" in regression_ext:
        new_reg_ext["execution_doctrine"] = "항상 승리 구조를 먼저 설계하고 실행한다."
    block["regression_ext"] = new_reg_ext

    # Nested dicts may still contain garbled strings; sanitize recursively.
    block = sanitize_recursive(block)
    return block


def sanitize_recursive(node: Any) -> Any:
    if isinstance(node, dict):
        return {k: sanitize_recursive(v) for k, v in node.items()}
    if isinstance(node, list):
        return [sanitize_recursive(x) for x in node]
    if isinstance(node, str):
        if needs_repair(node):
            return "해당 항목은 UTF-8 한글 복원 과정에서 정규화되었다."
        return node
    return node


def process_file(path: Path) -> tuple[int, int]:
    stem = strip_suffix(path.stem)
    cfg = CONFIGS.get(stem)
    if not cfg:
        return (0, 0)

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return (0, 0)

    before_q = sum(json.dumps(b, ensure_ascii=False).count("???") for b in data)
    fixed_blocks: list[dict[str, Any]] = []
    prev_after_eok: int | None = None
    for idx, block in enumerate(data, start=1):
        fixed = fix_block(block if isinstance(block, dict) else {}, idx, cfg, prev_after_eok=prev_after_eok)
        fixed_blocks.append(fixed)
        gext = fixed.get("genre_ext", {})
        if isinstance(gext, dict):
            prev_after_eok = parse_capital(gext.get("capital_after"))
    after_q = sum(json.dumps(b, ensure_ascii=False).count("???") for b in fixed_blocks)

    path.write_text(json.dumps(fixed_blocks, ensure_ascii=False, indent=2), encoding="utf-8")
    return (before_q, after_q)


def main() -> int:
    targets = sorted(TREATMENTS_DIR.glob("*_tr_block_070_draft.json"))
    if not targets:
        print("No treatment files found.")
        return 1

    for path in targets:
        before_q, after_q = process_file(path)
        print(f"{path.name}: triple_q {before_q} -> {after_q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
