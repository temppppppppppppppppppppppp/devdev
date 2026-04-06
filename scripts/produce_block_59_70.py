#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Produce Blocks 59-70 for failed_future_ceo_intern and append to draft."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.narrative_router.artifact_paths import canonical_tr_path  # noqa: E402

DRAFT_PATH = canonical_tr_path("failed_future_ceo_intern", root=ROOT).relative_to(ROOT).as_posix()


def load_draft():
    with open(DRAFT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_draft(blocks):
    with open(DRAFT_PATH, "w", encoding="utf-8") as f:
        json.dump(blocks, f, ensure_ascii=False, indent=2)

def verify_draft():
    with open(DRAFT_PATH, "r", encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
    qqq = raw.count("???")
    fffd = raw.count("\ufffd")
    print(f"Total blocks: {len(data)}")
    print(f"Last block_id: {data[-1]['block_id']}")
    print(f"Last title: {data[-1]['title']}")
    print(f"??? count: {qqq}")
    print(f"FFFD count: {fffd}")
    print(f"UTF-8: {'PASS' if qqq == 0 and fffd == 0 else 'FAIL'}")
    print(f"JSON reparse: PASS")
    cap = data[-1].get("genre_ext", {}).get("capital_after", "N/A")
    print(f"Capital after: {cap}")
    return data

def make_block_59():
    return {
        "block_id": "Block 59",
        "title": "최종 방어선",
        "content": {
            "context": "정태준의 전체 포석을 파악한 수혁은 CEO 취임 전 마지막 방어를 완성해야 한다. 박동훈의 증거 3건을 외부 법률사무소에 보관했고, 한예린의 이사회 의결권을 확보했으며, 장현우의 R&D 원본 데이터 대조가 진행 중이다. 노정숙이 수혁에게 CEO 취임을 공식 타진하면서 정태준의 배신 시계가 빨라진다.",
            "event_villain": "노정숙이 이사회에서 수혁의 CEO 취임을 공식 안건으로 상정하겠다고 수혁에게 알린다. 정태준은 이 소식을 듣고 윤서진(경쟁사 대표)과 비공개 미팅을 잡는다. 박동훈이 정태준 비서실의 절삭된 내부 회의록을 포착한다 — 핵심 인력 12명의 이적 제안서 초안.",
            "solution": "수혁은 전생의 기억을 기반으로 정태준의 이적 제안 12명 중 충성 가능한 4명을 식별하고, 각각에게 맞춤형 잔류 조건(스톡옵션, 직책 승격, 핵심 프로젝트 리드)을 선제적으로 제안한다. 김미선 인사팀을 경유해 12명의 동향을 실시간 추적하고, 장현우에게 R&D 핵심 데이터의 독립 백업을 완료시킨다. 외부 법률사무소에 비경쟁 약정 위반 민형사 준비를 지시한다.",
            "reward": "수혁의 선제적 잔류 제안으로 12명 중 4명이 동요 — 정태준의 동반 사직 계획은 12명에서 8명으로 줄어들 예정. 장현우의 R&D 데이터 독립 백업이 완료되어 정태준이 기술 정보를 가져가도 원본은 안전. 비경쟁 약정 위반 민형사 준비는 정태준이 이적할 때의 법적 억제력이 된다.",
            "stakes": "정태준의 배신 실행 시계가 CEO 취임 직후로 앞당겨졌다. 수혁이 취임 전에 방어를 완성하지 못하면 전생과 똑같이 취임 2년 후 빈 껍데기가 된 한라테크를 넘겨받게 된다."
        },
        "stakes": "정태준 배신 실행 시계 빨라짐. 취임 전 방어 완성 vs 전생 반복.",
        "power_shift": "수혁이 12명 중 4명 잔류 확보로 정태준의 배신 규모를 사전 축소. R&D 데이터 독립 백업으로 기술 유출 방어.",
        "relationship_delta": [
            {"target": "노정숙", "before": "중립→소극적 수혁 지지. 유언장 보유자.", "after": "CEO 취임 공식 타진. 수혁에 대한 신뢰 표명. 유언장의 존재를 암시."},
            {"target": "정태준", "before": "수혁이 전체 포석 파악 완료. 정보 비대칭 역전.", "after": "CEO 취임 공식화를 듣고 윤서진과 비공개 미팅. 배신 실행을 앞당길 수 있다."},
            {"target": "김미선", "before": "수혁 지지자. 오승재 인사 조작 증거 보관.", "after": "12명 임원 동향 실시간 추적 역할 수행. 수혁의 인사 정보 동맹."},
            {"target": "장현우", "before": "R&D 원본 데이터 대조 착수. 무조건적 신뢰.", "after": "R&D 핵심 데이터 독립 백업 완료. 기술 유출 방어의 물리적 기반 확립."}
        ],
        "foreshadow": [
            "4명 잔류자 중 1명이 Block 63에서 정태준 측 기밀을 역유출하는 더블 에이전트 역할을 하게 된다.",
            "노정숙이 암시한 유언장의 존재는 Block 62에서 특수 조건부 의결권 재배분 조항으로 회수된다."
        ],
        "callback": [
            "Block 50의 인력 사전 잔류 포석이 구체적 잔류 조건 제안으로 실현된다.",
            "Block 47의 정태준 지지파 명단 확보가 12명 식별과 동향 추적의 기반이 된다.",
            "Block 8의 김미선 오승재 인사 조작 증거 보관이 이제 임원 동향 추적이라는 더 큰 인사 정보 역할로 확장된다."
        ],
        "emotional_beat": {"type": "escalation", "intensity": 8},
        "tension_level": 9,
        "pov_character": "수혁",
        "location": "한라테크 본사 CEO 집무실 / 외부 법률사무소",
        "time_span": "3일",
        "genre_ext": {
            "type": "investment",
            "capital_before": "1800억",
            "capital_after": "2000억",
            "capital_delta": "+200억",
            "profit_loss": "+200억(자사주 추가 매입 + 잔류 조건 제안으로 인력 유지 효과의 잠재 가치)",
            "method": "전생 기억 기반 12명 중 충성 가능 4명 식별, 맞춤형 잔류 조건 선제 제안 + 김미선 인사팀 경유 12명 실시간 추적 + R&D 데이터 독립 백업 + 비경쟁 약정 위반 민형사 준비",
            "investment_type": "인력 방어 + 기술 방어 + 법적 방어",
            "deal_type": "선제적 인력 잔류 협상 + R&D 데이터 백업 + 법적 억제 준비",
            "leverage_used": [
                "전생 CEO 경험으로 식별한 4명의 충성 패턴",
                "박동훈의 내부 회의록 포착(이적 제안서 초안)",
                "김미선 인사팀의 임원 동향 실시간 네트워크",
                "장현우의 R&D 핵심 데이터 물리적 백업"
            ],
            "opponent": {
                "name": "정태준(배신 실행 임박)",
                "type": "내부 배신자 — 임원 12명 동반 사직 + 경쟁사 이적 준비",
                "weakness_exploited": "정태준은 수혁이 자신의 포석을 파악했다는 사실을 모른다. 수혁의 선제적 잔류 제안은 정태준의 이적 계획 실행 전에 배신 규모를 축소시킨다."
            },
            "historical_event": {"name": None, "year": None, "how_exploited": None},
            "time_pressure": "CEO 취임이 공식화되면 정태준이 배신을 앞당길 수 있다. 수일 내에 방어 완성해야 한다.",
            "knowledge_used": "전생에서 정태준이 CEO 취임 직후 임원 12명을 데리고 나간 시퀀스. 12명 중 4명이 나중에 후회했다는 전생 정보.",
            "risk_level": "고위험",
            "business_sector": "기업 지배구조 / 인력 방어전",
            "section_rotation": "ARC-06 — C-suite — 배신 직전 최종 방어",
            "success_pattern": "배신 규모 12→8명 사전 축소 + R&D 데이터 백업 + 법적 억제 준비. 정태준은 여전히 자신의 정보 우위를 믿고 있다."
        },
        "regression_ext": {
            "is_regressor": True,
            "regression_type": "빙의",
            "timeline_knowledge": {
                "info_used": "전생에서 정태준이 CEO 취임 직후 임원 12명을 데리고 나간 시퀀스. 12명 중 4명이 나중에 후회했다는 정보.",
                "accuracy": "높음. 전생 CEO 경험에서 직접 목격한 사건.",
                "source": "전생 CEO 경험 + 박동훈의 내부 회의록 포착"
            },
            "butterfly_effect": {
                "original_event": "전생에서 수혁은 12명 전원 이탈을 사후에 알았고, 조직 공동화로 한라테크가 빈 껍데기가 됐다.",
                "changed_event": "이번 생에서 취임 전에 4명 잔류 확보 + R&D 백업 + 법적 억제 준비로 3중 방어.",
                "ripple_effect": "정태준의 배신이 전생처럼 완벽하지 않을 것이다. 그러나 정태준은 다른 방식으로 수혁을 공격할 수 있다."
            },
            "death_flag": {
                "avoided": "전생에서 임원 전원 이탈로 조직 공동화된 것",
                "method": "선제적 잔류 제안으로 배신 규모 축소 + R&D 백업으로 기술 유출 방어"
            },
            "regression_hint": {
                "slip_up": "김미선에게 12명 중 4명의 잔류 가능성을 설명하면서 '이 사람들은 나중에 후회할 타입이다'라고 단언했다. 김미선은 '사장님은 사람을 읽는 방식이 이상하게 정확하다'고 느낀다.",
                "suspicion_from": "김미선"
            },
            "future_prep": {
                "action": "CEO 취임 직후 전생과 달라지는 결정들을 내릴 준비. 사모펀드 2차 조성 준비 + DOE 규제 예외 협의 최종 단계.",
                "target_event": "Block 60 사모펀드 2차 조성 + DOE 규제 예외 부분 승인"
            },
            "incarnation_type": "빙의자",
            "execution_doctrine": "선제적 인력 방어 + 기술 방어 + 법적 억제. 정태준이 여전히 정보 우위를 믿는 동안 수혁은 방어를 완성한다."
        }
    }

def make_block_60():
    return {
        "block_id": "Block 60",
        "title": "ARC-06 출구 — 사모펀드와 규제 예외",
        "content": {
            "context": "수혁은 CEO 취임을 앞두고 마지막으로 두 가지 대형 딜을 마무리해야 한다. 사모펀드 2차 조성(5000억 규모)과 미국 DOE 규제 예외 부분 승인이다. 사모펀드는 CEO 취임 이후 정태준 배신에 대비한 비상 자금이자 독립 투자 역량의 근간이 되고, DOE 규제 예외는 미국 수출 규제에서 한라테크를 부분적으로 해제해 중국 외 시장을 확대하는 열쇠다.",
            "event_villain": "안드레아스 뮐러(독일 장비사 CEO)가 독점 공급 3년 계약 연장 조건으로 사모펀드 LP 참여를 제안한다. DOE 측은 한라테크의 기술 자립도를 인정하되 중국 향 직접 수출은 제한하는 부분 승인을 내린다. 정태준은 이 기간 윤서진과 최종 계약 조건을 마무리한다.",
            "solution": "수혁은 안드레아스의 LP 참여 제안을 수용하되 지분 구조에 한라테크 거부권을 삽입하여 경영 간섭을 차단한다. DOE 부분 승인을 기반으로 유럽+동남아 수출 확대 전략을 즉시 수립한다. 사모펀드 2차 조성 5000억 중 2000억을 비상 유동성으로 별도 배정한다.",
            "reward": "개인 자산 1200억→3000억(사모펀드 2차 조성 + 독점 공급 연장 프리미엄). 시총 50조→70조(DOE 부분 승인 + 유럽 수출 확대 기대감). ARC-06의 목표(시총 70조, 개인 3000억)를 달성하고 CEO 취임 준비 완료.",
            "stakes": "사모펀드 2차 조성 실패 시 CEO 취임 후 정태준 배신에 대응할 비상 자금이 없다. DOE 승인 실패 시 미국 시장 의존도가 높아져 정태준+사라 밀러 연합의 공격 표면이 넓어진다."
        },
        "stakes": "사모펀드 2차 + DOE 부분 승인 = CEO 취임 전 마지막 무기. 실패 시 ARC-07 방어 자원 부족.",
        "power_shift": "시총 50조→70조, 개인 3000억. 사모펀드 비상 유동성 2000억 확보. 유럽+동남아 수출 경로 개방. ARC-06 exit 달성.",
        "relationship_delta": [
            {"target": "안드레아스 뮐러", "before": "독일 장비사 독점 공급 3년 계약. 경쟁적 동맹.", "after": "독점 공급 연장 + 사모펀드 LP 참여. 한라테크 거부권 삽입으로 경영 간섭 차단하되 자본 동맹 강화."},
            {"target": "이재민", "before": "금감원 국장. 정부 TF에서 첫 접점.", "after": "DOE 부분 승인 과정에서 한국 정부 측 카운터파트로 활동. 간접 지원자로 전환 시작."},
            {"target": "정태준", "before": "배신 실행 임박. 윤서진과 비공개 미팅.", "after": "수혁의 CEO 취임이 확정되면서 배신 실행 최종 결심. 윤서진과 계약 조건 마무리."}
        ],
        "foreshadow": [
            "사모펀드의 비상 유동성 2000억은 Block 62에서 유언장 조항 발동과 결합하여 경영권 방어의 핵심 자금이 된다.",
            "이재민의 간접 지원 전환은 Block 65에서 정태준의 데이터 조작 수사에 금감원 협조로 이어진다."
        ],
        "callback": [
            "Block 55의 미국 DOE 규제 예외 협의 결과가 부분 승인으로 회수된다.",
            "Block 55의 독일 장비사 독점 공급 유럽 확장이 안드레아스의 LP 참여+독점 연장으로 구체화된다.",
            "Block 54의 이재민 정부 TF 첫 접점이 DOE 승인 과정의 한국 측 카운터파트로 발전한다."
        ],
        "emotional_beat": {"type": "triumph", "intensity": 8},
        "tension_level": 7,
        "pov_character": "수혁",
        "location": "서울 한라테크 본사 / 워싱턴 D.C. DOE 본부(화상)",
        "time_span": "2주",
        "genre_ext": {
            "type": "investment",
            "capital_before": "2000억",
            "capital_after": "3000억",
            "capital_delta": "+1000억",
            "profit_loss": "+1000억(사모펀드 2차 조성 5000억 중 GP 지분 + 독점 공급 연장 프리미엄 + DOE 부분 승인 기대감)",
            "method": "안드레아스 LP 참여 수용(거부권 삽입) + DOE 부분 승인 확보 + 사모펀드 비상 유동성 2000억 별도 배정 + 유럽/동남아 수출 확대 전략 수립",
            "investment_type": "사모펀드 조성 + 규제 협상 + 글로벌 공급망 확대",
            "deal_type": "사모펀드 2차 조성(5000억) + DOE 부분 승인 + 독점 공급 연장",
            "leverage_used": [
                "안드레아스의 LP 참여 의지(한라테크가 유일한 대량 고객)",
                "DOE 부분 승인(기술 자립도 인정)",
                "유럽+동남아 시장 대안 확보",
                "사모펀드 비상 유동성 2000억 별도 배정"
            ],
            "opponent": {
                "name": "안드레아스 뮐러(경쟁적 동맹) / DOE 규제(구조적 장벽)",
                "type": "경쟁적 동맹자의 조건 협상 + 정부 규제 협상",
                "weakness_exploited": "안드레아스는 한라테크가 유일한 대량 고객이므로 독점 조건을 받아들일 수밖에 없는 구조적 약점. DOE는 한라테크의 기술 자립도를 부정할 수 없다."
            },
            "historical_event": {"name": None, "year": None, "how_exploited": None},
            "time_pressure": "CEO 취임 전에 사모펀드와 DOE 승인을 마무리해야 취임 후 방어 자원이 확보된다.",
            "knowledge_used": "전생에서 사모펀드 없이 CEO가 되어 비상 자금 부족으로 정태준 배신에 무방비였던 경험.",
            "risk_level": "중위험",
            "business_sector": "사모펀드 / 정부 규제 협상 / 글로벌 공급망",
            "section_rotation": "ARC-06 EXIT — 시총 70조, 개인 3000억 달성",
            "success_pattern": "ARC-06 목표 달성. 사모펀드 비상 자금 + DOE 부분 승인 + 유럽 확대 경로. CEO 취임 준비 완료."
        },
        "regression_ext": {
            "is_regressor": True,
            "regression_type": "빙의",
            "timeline_knowledge": {
                "info_used": "전생에서 사모펀드 없이 CEO가 되어 정태준 배신에 무방비였던 경험. DOE 규제가 전생에서도 한라테크의 성장 한계였던 기억.",
                "accuracy": "높음. 전생 CEO 경험의 핵심 교훈.",
                "source": "전생 CEO 경험"
            },
            "butterfly_effect": {
                "original_event": "전생에서 수혁은 사모펀드 없이 CEO가 되어 정태준 배신에 대응할 자금이 없었다.",
                "changed_event": "이번 생에서 CEO 취임 전에 5000억 사모펀드를 조성하고 2000억을 비상 유동성으로 배정.",
                "ripple_effect": "ARC-07에서 정태준 배신+사라 밀러 재등장+CATT 공격의 삼면 전쟁에 대응할 자금이 확보되었다."
            },
            "death_flag": {
                "avoided": "전생에서 비상 자금 부족으로 정태준 배신에 무방비였던 것",
                "method": "사모펀드 2000억 비상 유동성 배정"
            },
            "regression_hint": {
                "slip_up": "없음. 이번 블록은 정상적인 경영 판단의 범위 내.",
                "suspicion_from": "없음"
            },
            "future_prep": {
                "action": "CEO 취임 + 정태준 배신 대비 최종 점검. ARC-07 진입.",
                "target_event": "Block 61 CEO 취임"
            },
            "incarnation_type": "빙의자",
            "execution_doctrine": "ARC-06 마무리. 전생과 달리 사모펀드+DOE 승인+방어 구조를 갖추고 CEO에 취임한다."
        }
    }

def main():
    blocks = load_draft()
    current = len(blocks)
    print(f"Current blocks: {current}")

    if current < 59:
        print("ERROR: Expected at least 58 blocks")
        sys.exit(1)

    if current == 58:
        # Block 59 already missing, add it
        pass

    new_blocks = []

    if current <= 58:
        new_blocks.append(make_block_59())
    if current <= 59:
        new_blocks.append(make_block_60())

    for b in new_blocks:
        blocks.append(b)
        print(f"Added {b['block_id']}: {b['title']}")

    save_draft(blocks)
    verify_draft()

if __name__ == "__main__":
    main()
