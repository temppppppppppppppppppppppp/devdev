#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
office_checkup_next_day TR Block 36-70 production script.
Reads existing 35-block draft, appends blocks 36-70, saves complete 70-block file.
"""

import json
import pathlib

TR_PATH = pathlib.Path(r"C:\Users\User\Desktop\글도비\treatments\office_checkup_next_day_tr_block_070_draft.json")

# ── ARC-04 remainder (36-40): 오세진 축 정리 + 인사 S ──────────

block_36 = {
    "block_id": "Block 36",
    "title": "팀장의 줄",
    "content": {
        "context": "2025년 11월 중순, 한일유통 연말 인사 시즌이 열린다. 오세진은 인사위원회 위원인 경영관리 부서장과 점심을 잡고, 경영기획팀 평가표를 자기 기준으로 다듬기 시작한다. 시혁은 TF룸에서 감사 보고서를 정리하다가 인사팀에서 내려온 평가표 양식을 본다. 양식 자체는 같지만, 올해는 '팀 기여도' 항목의 가중치가 작년보다 올라가 있다. 감각이 작동한다 — 팀 기여도 가중치가 높아지면 개인 성과가 팀 공으로 희석되기 쉽다. 시혁 개인의 TF 성과, 감사 지원, 물류 재설계 기여가 전부 '경영기획팀 성과'로 묶일 수 있다. 오세진이 원하는 구도다. 시혁은 평가표의 가중치가 언제 바뀌었는지를 역추적한다. 3주 전 인사위원회 회의록에 오세진의 건의가 있었다. '팀 기여도를 강화해 협업 문화를 장려하자'는 명목이었다.",
        "event_villain": "오세진은 인사 시즌에 맞춰 가중치를 움직였다. 이것은 시혁 한 명을 겨냥한 것이 아니라, 팀장으로서 팀 성과를 통제하는 정당한 권한 행사처럼 보인다. 하지만 실질 효과는 시혁의 개별 공을 팀장 이름 밑에 묶는 것이다. 동시에 오세진은 인사위원 2명과 점심 모임을 시작한다.",
        "solution": "시혁은 감각으로 읽은 구도를 기록하지 않는다. 대신 전무에게 올린 분기별 프로젝트 기여 리스트를 뽑아 본다. TF 참여 이력, 감사 데이터 요청서 작성자란, 물류 재설계 우선순위표 초안 이력 — 모두 시혁 이름이 문서 상단에 있다. 가중치가 바뀌어도 원본 문서의 이름은 바뀌지 않는다. 시혁은 아직 반격하지 않는다. 먼저 자기 이름이 적힌 문서의 목록을 조용히 만든다.",
        "reward": "시혁이 만든 프로젝트별 기여 문서 목록은 이후 반격의 탄약이 된다. 동시에 오세진의 인사 라인 동원이 어디까지 뻗어 있는지를 처음으로 파악한다. 오세진은 인사위원 접근에 성공했지만, 시혁이 이를 감지한 사실은 모른다."
    },
    "stakes": "인사 가중치가 유지되면 시혁의 올해 모든 공이 팀장 이름 아래 묶인다. 개인 성과로 보여줄 수 없으면 S등급은 물 건너간다.",
    "power_shift": {
        "protagonist": "인사 구도를 감지하고 문서 기반 증거를 조용히 수집 시작.",
        "antagonist": "오세진은 인사 가중치를 움직이는 데 성공했고, 인사위원 2명과 점심 라인을 확보했다."
    },
    "relationship_delta": [
        {
            "target": "오세진(팀장)",
            "before": "공을 가져가려는 팀장이자 이제 물리적으로도 떨어진 상사",
            "after": "인사 시즌에 맞춰 조직적으로 시혁의 성과를 묶으려는 견제자"
        }
    ],
    "foreshadow": [
        "시혁이 만든 기여 문서 목록은 두 블록 뒤에서 전무와 HR팀장 앞에 한 장으로 정리되어 나간다.",
        "오세진의 인사위원 점심 라인은 오래가지 않는다. 실적 없는 네트워크는 인사 시즌이 지나면 소멸한다."
    ],
    "callback": [
        "오세진이 시혁의 공을 가져가는 패턴은 시작부터 있었다. 이번에는 가중치 변경이라는 제도적 수단으로 진화했다.",
        "시혁이 문서 이력을 추적하는 능력은 감사 지원에서 쌓은 데이터 추적 역량의 부산물이다."
    ],
    "emotional_beat": {
        "type": "calculation",
        "intensity": 6
    },
    "tension_level": 7,
    "pov_character": "한시혁",
    "location": {
        "place": "한일유통 경영기획팀 사무실 / 인사팀 회의록 열람실",
        "type": "본사"
    },
    "time_span": {
        "duration": "3일",
        "in_story_time": "2025년 11월 중순"
    },
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv5 예산 발언권 + 체력 부채 심화 + 정밀검사 예약",
        "capital_after": "Lv5 예산 발언권 + 인사 시즌 진입 + 오세진 견제 구도 감지 + 기여 문서 목록 수집",
        "capital_delta": "인사 견제 감지 (소득) + 기여 문서 목록 축적 (소득)",
        "profit_loss": "아직 실질 손실 없음. 오세진 견제 구도를 먼저 읽었다.",
        "method": "인사 가중치 변경 역추적 + 프로젝트별 기여 이력 문서 수집.",
        "investment_type": "정보 수집",
        "deal_type": "인사 라인 방어 준비",
        "leverage_used": [
            "감각을 통한 가중치 변경 동기 추론",
            "프로젝트별 원본 문서 작성자란 이력"
        ],
        "opponent": {
            "name": "오세진",
            "type": "직속 팀장의 제도적 견제",
            "weakness_exploited": "가중치를 바꿔도 원본 문서의 기여자 이름은 바꿀 수 없다"
        },
        "historical_event": {
            "name": None,
            "year": None,
            "how_exploited": None
        },
        "time_pressure": "연말 인사평가까지 약 6주",
        "knowledge_used": "인사위원회 회의록의 가중치 변경 건의 이력",
        "risk_level": "중위험 (인사 시즌 통제력 부재)",
        "business_sector": "경영기획 / 인사",
        "section_rotation": "ARC-04 감각의 흔들림",
        "success_pattern": "적이 제도를 바꿔도 원본은 남는다. 원본을 먼저 수집한다.",
        "special_ability": {
            "has_ability": True,
            "ability_type": "감각",
            "ability_name": "조직 역학 조감",
            "ability_source": "건강검진 이후 발현 (원인 불명)",
            "ability_used_for": "인사 가중치 변경의 진짜 동기와 오세진 인사 라인 동원 범위 파악"
        }
    },
    "regression_ext": {
        "is_regressor": False,
        "regression_type": None,
        "execution_doctrine": "제도가 바뀌어도 원본은 남는다. 원본을 먼저 쥔다."
    },
    "block_no": 36
}

block_37 = {
    "block_id": "Block 37",
    "title": "평가의 벽",
    "content": {
        "context": "2025년 11월 하순, 1차 인사평가 피드백 시즌. 오세진은 경영기획팀 전체 성과서를 작성하면서 시혁의 TF 성과, 감사 지원 기여, 물류 재설계 우선순위표를 모두 '팀 차원의 협업 성과'로 기재한다. 시혁 이름은 본문에 두 번 나오지만, 성과 항목 옆의 주체는 전부 '경영기획팀'이다. 시혁은 인사팀에서 보내 온 자기 평가서를 작성하면서 같은 성과를 개인 항목으로 적었지만, 팀장 확인란에 오세진이 코멘트를 남겼다. '해당 성과는 팀 공동 프로젝트로, 개인 실적 배분이 어려움.' 시혁의 피로가 겹친다. 체력 부채가 쌓인 상태에서 인사 서류까지 막히자, 감각이 살짝 흔들린다. 평가서를 다시 읽는데 오세진의 코멘트가 어떤 효과를 낼지 읽히지 않는다. 이성적으로는 이 코멘트가 S등급을 차단한다는 걸 알지만, 감각이 확인해주지 않는다.",
        "event_villain": "오세진은 팀장 권한 내에서 가장 효과적인 한 수를 둔다. 시혁의 성과를 부정하는 게 아니라 '배분이 어렵다'는 한 줄로 개인 평가를 흐린다. 이것은 거짓이 아니라 관점의 문제이기 때문에 반박하기 어렵다.",
        "solution": "시혁은 이번에는 즉각 반격하지 않는다. 감각이 흔들리는 상태에서 급하게 움직이면 오판할 수 있다는 것을 이미 배웠다. 대신 서정민에게 전화한다. 감사 지원 TF에서 시혁의 기여가 어떤 수준이었는지를 서정민 관점에서 한 문장으로 적어줄 수 있겠냐고 묻는다. 서정민은 '보고서에 네 이름이 안 들어간 게 이상한 수준'이라고 말하고, 서면으로 확인서를 보내준다.",
        "reward": "서정민의 확인서 확보. 이것은 오세진의 '팀 공동 프로젝트' 프레임에 대한 최초의 외부 증언이다. 하지만 이 확인서만으로는 인사위원회를 뒤집기에 부족하다. 시혁은 지금 자기가 진 것을 안다."
    },
    "stakes": "S등급이 막히면 연말 인사에서 올라갈 자리가 없다. 동시에 감각이 체력 부채로 흔들리는 상태에서 인사 전쟁까지 열리면 두 전선을 동시에 유지하기 어렵다.",
    "power_shift": {
        "protagonist": "외부 확인서 1건 확보. 하지만 오세진의 코멘트로 S등급 진입이 사실상 차단된 상태.",
        "antagonist": "오세진은 팀장 권한으로 평가서 코멘트를 넣었다. 제도 안에서의 합법적 방어."
    },
    "relationship_delta": [
        {
            "target": "오세진(팀장)",
            "before": "인사 시즌에 맞춰 조직적으로 시혁의 성과를 묶으려는 견제자",
            "after": "평가서 코멘트로 S등급을 실질 차단한 제도적 적대자"
        },
        {
            "target": "서정민(재무팀 차장)",
            "before": "감사 협업 파트너",
            "after": "감사 협업 파트너 + 시혁의 기여를 외부에서 증명하는 증인"
        }
    ],
    "foreshadow": [
        "서정민의 확인서는 다음 블록에서 시혁이 만드는 '프로젝트별 기여 증명서'의 한 축이 된다.",
        "감각이 인사 서류 앞에서 흔들리는 경험은 감각의 본질에 대한 단서 — 감각은 조직 역학은 읽지만 제도적 결과까지 예측하지는 못한다."
    ],
    "callback": [
        "체력 부채로 감각이 흐려지는 복선이 인사 시즌에서 현실화. 피로 상태에서는 감각의 신뢰도가 떨어진다.",
        "오세진이 시혁의 공을 자기 것으로 가져가는 패턴이 코멘트 한 줄로 압축되어 나타남."
    ],
    "emotional_beat": {
        "type": "frustration",
        "intensity": 7
    },
    "tension_level": 8,
    "pov_character": "한시혁",
    "location": {
        "place": "한일유통 경영기획팀 사무실 / 인사팀 평가서 시스템",
        "type": "본사"
    },
    "time_span": {
        "duration": "1주",
        "in_story_time": "2025년 11월 하순"
    },
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv5 예산 발언권 + 인사 시즌 진입 + 오세진 견제 구도 감지 + 기여 문서 목록 수집",
        "capital_after": "Lv5 예산 발언권 + S등급 진입 차단 상태 + 서정민 확인서 1건",
        "capital_delta": "S등급 차단 (손실) + 외부 확인서 1건 (소득)",
        "profit_loss": "인사 전선에서 실질 패배. 서정민 확인서가 유일한 소득.",
        "method": "감사 협업 파트너에게 기여 확인서를 요청해 외부 증언 확보.",
        "investment_type": "인적 자산 활용",
        "deal_type": "평가 희석 방어",
        "leverage_used": [
            "서정민과의 감사 협업 관계",
            "감사 보고서 내 기여 이력"
        ],
        "opponent": {
            "name": "오세진",
            "type": "팀장 평가 권한",
            "weakness_exploited": "오세진의 코멘트는 팀장 관점일 뿐이다. 외부 협업 파트너의 증언은 팀장이 통제할 수 없다."
        },
        "historical_event": {
            "name": None,
            "year": None,
            "how_exploited": None
        },
        "time_pressure": "인사평가 최종 제출까지 3주",
        "knowledge_used": "감사 지원 TF에서의 실질 기여도에 대한 서정민의 경험",
        "risk_level": "고위험 (S등급 차단은 커리어 정체를 의미)",
        "business_sector": "인사 / 경영기획",
        "section_rotation": "ARC-04 감각의 흔들림",
        "success_pattern": "이번에는 졌다. 하지만 외부 증인은 확보했다.",
        "special_ability": {
            "has_ability": True,
            "ability_type": "감각",
            "ability_name": "조직 역학 조감",
            "ability_source": "건강검진 이후 발현 (원인 불명)",
            "ability_used_for": "오세진의 코멘트가 인사위원회에서 어떤 효과를 내는지 읽으려 했으나 피로로 인해 불완전"
        }
    },
    "regression_ext": {
        "is_regressor": False,
        "regression_type": None,
        "execution_doctrine": "감각이 안 될 때는 사람에게 묻는다. 사람의 증언은 감각보다 제도에 강하다."
    },
    "block_no": 37
}

block_38 = {
    "block_id": "Block 38",
    "title": "한 장의 증명",
    "content": {
        "context": "2025년 12월 초, 시혁은 3일간 야근하며 한 장짜리 문서를 만든다. 올해 자신이 관여한 모든 프로젝트의 before-after를 한 장에 담았다. 물류센터 통합안 저지(억 단위 손실 방지), 물류 재설계 TF 우선순위표(실행률 92%), 감사 데이터 전략 설계(서면 불일치 발견), 분기 예산 편성 기여(예산 3개 항목 반영). 각 항목 옆에는 해당 문서의 작성자란, 전무 CC 이력, 서정민 확인서가 링크되어 있다. 시혁은 이 문서를 전무에게 먼저 보여주고, 같은 날 오후 HR팀장에게도 보낸다. 전무가 묻는다. '이게 다 네가 한 거야?' 시혁이 답한다. '문서 작성자란을 확인하시면 됩니다.' 전무는 문서를 20분간 읽고 HR팀장에게 직접 전화한다.",
        "event_villain": "오세진은 이 문서의 존재를 모른다. 시혁이 전무와 HR팀장을 같은 날 동시에 공략하는 것을 견제할 시간이 없었다.",
        "solution": "시혁은 감각에 의존하지 않았다. 문서, 이력, 링크, 확인서 — 모두 감각 없이도 검증 가능한 증거다. 전무와 HR팀장을 같은 날 잡은 것은 오세진이 중간에 개입할 여유를 주지 않기 위해서였다. 이것은 감각이 아니라 타이밍 설계다.",
        "reward": "전무가 HR팀장에게 전화를 걸었다. 이것은 인사 라인에서 전무가 직접 시혁의 성과를 확인하겠다는 의미다. 오세진의 '팀 공동 프로젝트' 코멘트는 전무의 직접 확인 요청 앞에서 무력화된다. S등급 가능성이 다시 열린다."
    },
    "stakes": "이 문서가 전무를 설득하지 못하면 남은 카드가 없다. 동시에 오세진을 우회해 전무와 HR을 직접 잡는 행위는 팀장과의 관계를 완전히 소각하는 것이다.",
    "power_shift": {
        "protagonist": "before-after 문서를 통해 전무와 HR팀장에게 직접 증명. 오세진의 코멘트 무력화.",
        "antagonist": "오세진은 시혁의 직접 접근을 몰랐고, 전무의 HR 직통 전화로 방어선이 붕괴 시작."
    },
    "relationship_delta": [
        {
            "target": "박전무",
            "before": "시혁을 신뢰하지만 인사까지 직접 개입하진 않던 후원자",
            "after": "시혁의 성과를 직접 확인하고 HR에 전화를 건 적극적 후원자"
        },
        {
            "target": "오세진(팀장)",
            "before": "평가서 코멘트로 S등급을 실질 차단한 제도적 적대자",
            "after": "전무의 직접 개입으로 코멘트가 무력화되기 시작한 후퇴 상태"
        }
    ],
    "foreshadow": [
        "전무가 HR팀장에게 건 전화는 오세진에게 곧 알려진다. 오세진의 마지막 저항이 시작될 것이다.",
        "시혁이 감각 없이 문서와 타이밍만으로 승부한 경험은 이후 더 큰 판에서도 반복될 무기가 된다."
    ],
    "callback": [
        "시혁이 수집했던 프로젝트별 기여 문서 목록이 한 장짜리 증명서로 완성되어 나감.",
        "서정민의 확인서가 문서 안의 공식 링크 중 하나로 들어감."
    ],
    "emotional_beat": {
        "type": "counterattack",
        "intensity": 8
    },
    "tension_level": 8,
    "pov_character": "한시혁",
    "location": {
        "place": "한일유통 전무실 / HR팀장 사무실",
        "type": "본사"
    },
    "time_span": {
        "duration": "3일",
        "in_story_time": "2025년 12월 초"
    },
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv5 예산 발언권 + S등급 진입 차단 상태 + 서정민 확인서 1건",
        "capital_after": "Lv5 예산 발언권 + 전무 직접 확인 + HR팀장 인지 + S등급 가능성 재개",
        "capital_delta": "S등급 재가능 (소득) + 오세진 코멘트 무력화 (소득) + 팀장 관계 소각 (비용)",
        "profit_loss": "S등급 가능성 재개. 팀장과의 관계는 사실상 끝.",
        "method": "프로젝트별 before-after 증명서를 전무와 HR에 동시 제출하여 오세진 견제를 우회.",
        "investment_type": "증거 기반 직접 접근",
        "deal_type": "성과 증명서 제출",
        "leverage_used": [
            "전무와의 기존 신뢰 관계",
            "프로젝트별 원본 문서 작성자란",
            "서정민 확인서",
            "전무-HR 직통 라인"
        ],
        "opponent": {
            "name": "오세진",
            "type": "팀장 권한 기반 성과 희석",
            "weakness_exploited": "오세진의 견제는 인사위원 점심 라인에 의존했지만, 전무의 직접 개입은 인사위원보다 상위 권한이다"
        },
        "historical_event": {
            "name": None,
            "year": None,
            "how_exploited": None
        },
        "time_pressure": "인사평가 최종 확정까지 2주",
        "knowledge_used": "올해 전체 프로젝트의 before-after 수치와 문서 이력",
        "risk_level": "고위험 (팀장 완전 우회는 돌이킬 수 없다)",
        "business_sector": "인사 / 전무실",
        "section_rotation": "ARC-04 감각의 흔들림",
        "success_pattern": "감각이 아니라 문서와 타이밍으로 이겼다.",
        "special_ability": {
            "has_ability": True,
            "ability_type": "감각",
            "ability_name": "조직 역학 조감",
            "ability_source": "건강검진 이후 발현 (원인 불명)",
            "ability_used_for": "이 블록에서는 감각에 의존하지 않음. 문서와 증거만 사용."
        }
    },
    "regression_ext": {
        "is_regressor": False,
        "regression_type": None,
        "execution_doctrine": "감각이 흔들릴 때는 증거가 말하게 한다."
    },
    "block_no": 38
}

block_39 = {
    "block_id": "Block 39",
    "title": "떨어지는 줄",
    "content": {
        "context": "2025년 12월 중순. 전무가 HR팀장에게 전화를 건 사실이 하루 만에 오세진에게 전달된다. 오세진은 처음으로 불안해한다. 경영기획팀 내에서도 변화가 느껴진다. 팀원 3명 중 시혁과 가장 자주 일했던 후배 사원이 연말 프로젝트 리뷰 자료를 시혁에게 직접 보내기 시작한다. 오세진을 거치지 않고. 오세진의 인사위원 점심 라인도 흔들린다 — 전무가 직접 개입한 이상 인사위원들이 팀장 코멘트만 보고 판단하기는 어려워졌다. 시혁은 이 변화를 감지한다. 감각이 돌아왔다. 체력이 아직 한계지만, 인사 라인에서 사람이 움직이기 시작하자 감각이 다시 작동한다. 누가 오세진 편에 남아 있고, 누가 이미 마음이 움직였는지가 복도 대화 한 마디에서 읽힌다.",
        "event_villain": "오세진은 마지막으로 팀 회식을 잡는다. 표면은 연말 회식이지만 실제로는 팀원들의 충성도를 확인하려는 시도다. 하지만 회식 자리에서 오세진이 평소 하던 농담에 팀원들이 웃지 않는다. 분위기가 이미 바뀌었다.",
        "solution": "시혁은 아무것도 하지 않는다. 이 블록에서 시혁의 역할은 관찰이다. 오세진의 네트워크가 스스로 무너지고 있다. 시혁이 직접 와해시키는 것이 아니라, 전무의 개입이라는 사건 이후 자연스럽게 사람들이 재배치되고 있다. 시혁은 회식에 참석하고 조용히 먹고 돌아온다.",
        "reward": "오세진의 팀 내 통제력이 눈에 띄게 약해졌다. 후배 사원이 시혁에게 직접 자료를 보내는 것은 작은 신호지만, 조직에서 가장 분명한 충성 전환 신호다. 시혁은 아직 팀장이 아니지만, 팀의 실질 중심이 이동하고 있다."
    },
    "stakes": "오세진이 마지막 저항으로 인사위원회에서 시혁의 결격 사유를 만들 수 있다. 네트워크가 약해져도 팀장이 작정하면 평가서에 부정적 의견을 추가로 넣을 수 있다.",
    "power_shift": {
        "protagonist": "팀 내 실질 중심이 시혁으로 이동하기 시작. 감각 복귀.",
        "antagonist": "오세진의 팀 내 통제력과 인사위원 라인이 동시에 약화."
    },
    "relationship_delta": [
        {
            "target": "오세진(팀장)",
            "before": "전무의 직접 개입으로 코멘트가 무력화되기 시작한 후퇴 상태",
            "after": "팀 내 충성 전환으로 고립이 시작된 팀장"
        },
        {
            "target": "경영기획팀 후배사원",
            "before": "오세진과 시혁 사이에서 중립이던 팀원",
            "after": "시혁에게 직접 자료를 보내기 시작한 사실상의 시혁 라인"
        }
    ],
    "foreshadow": [
        "오세진의 고립은 다음 블록에서 최종 인사평가 결과로 확정된다.",
        "팀 충성 전환은 이후 시혁이 경영기획팀 실질 리더로 서는 기반이 된다."
    ],
    "callback": [
        "전무가 HR팀장에게 건 전화의 파급 효과가 팀 내부까지 전달됨.",
        "감각이 인사 서류 앞에서 흔들렸던 경험 이후, 사람이 움직이자 감각이 다시 작동 — 감각은 서류보다 사람의 감정에 더 잘 반응한다는 확인."
    ],
    "emotional_beat": {
        "type": "quiet_resolution",
        "intensity": 5
    },
    "tension_level": 5,
    "pov_character": "한시혁",
    "location": {
        "place": "한일유통 경영기획팀 사무실 / 사내 식당 (회식)",
        "type": "본사"
    },
    "time_span": {
        "duration": "1주",
        "in_story_time": "2025년 12월 중순"
    },
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv5 예산 발언권 + 전무 직접 확인 + HR팀장 인지 + S등급 가능성 재개",
        "capital_after": "Lv5 예산 발언권 + 오세진 네트워크 와해 진행 + 팀 내 실질 중심 이동 시작",
        "capital_delta": "오세진 네트워크 와해 (구조 변화) + 팀 충성 전환 시작 (소득)",
        "profit_loss": "실질 소득 없음. 구조적 변화가 자연스럽게 진행 중.",
        "method": "아무것도 하지 않음. 전무 개입 이후의 자연스러운 파급 효과를 관찰.",
        "investment_type": "관찰",
        "deal_type": "해당 없음 — 자연 와해 관찰",
        "leverage_used": [
            "전무의 HR 직접 개입이라는 기정사실"
        ],
        "opponent": {
            "name": "오세진",
            "type": "팀 내 통제력 상실",
            "weakness_exploited": "오세진의 네트워크는 실적이 아니라 점심 라인에 의존했다. 상위 권한이 개입하자 점심 라인은 의미를 잃었다."
        },
        "historical_event": {
            "name": None,
            "year": None,
            "how_exploited": None
        },
        "time_pressure": "인사평가 최종 확정까지 1주",
        "knowledge_used": "조직 내 충성 전환 신호를 읽는 감각",
        "risk_level": "저위험 (시혁이 움직이지 않아도 구도가 변하고 있음)",
        "business_sector": "경영기획팀 내부",
        "section_rotation": "ARC-04 감각의 흔들림",
        "success_pattern": "적의 네트워크가 스스로 무너지는 것을 지켜본다. 가장 좋은 반격은 가끔 아무것도 안 하는 것이다.",
        "special_ability": {
            "has_ability": True,
            "ability_type": "감각",
            "ability_name": "조직 역학 조감",
            "ability_source": "건강검진 이후 발현 (원인 불명)",
            "ability_used_for": "팀 충성 전환 감지. 누가 오세진 편에 남아 있고 누가 이미 옮겼는지를 복도 대화에서 읽음."
        }
    },
    "regression_ext": {
        "is_regressor": False,
        "regression_type": None,
        "execution_doctrine": "적이 무너지는 중에는 건드리지 않는다."
    },
    "block_no": 39
}

block_40 = {
    "block_id": "Block 40",
    "title": "연말 인사 S",
    "content": {
        "context": "2025년 12월 하순, 연말 인사평가 결과 발표. 시혁은 S등급을 받는다. 경영기획팀 소속 사원으로는 최초다. 인사팀에서 내려온 결과지에는 전무의 직접 의견이 첨부되어 있었다. '한시혁 사원은 올해 물류센터 통합안 저지, 물류 재설계 TF 실무 간사, MD사업부 감사 지원 등 팀 단위를 넘는 전사적 기여를 했음.' 오세진의 '팀 공동 프로젝트' 코멘트는 결과지 어디에도 반영되지 않았다. 같은 날, 인사팀에서 추가 공지가 내려온다. 경영기획팀장 직무대행 건. 오세진은 연초 유통사업부 파견으로 이동한다. 공식 사유는 '현장 경험 강화'이지만, 실질은 팀장직에서의 이탈이다. 시혁이 팀장이 되는 것은 아니다. 직급은 아직 사원이다. 하지만 경영기획팀의 팀장이 빠진 상태에서 전무 직보 라인과 TF 실무 간사를 쥔 사람은 시혁뿐이다.",
        "event_villain": "해당 없음. 오세진은 이 블록에서 퇴장한다. 팀장에서 밀려난 것이 아니라, 더 이상 시혁의 적대자로 기능할 수 없는 위치로 이동한 것이다.",
        "solution": "시혁은 S등급 결과를 확인하고, 오세진 파견 공지를 읽고, 경영기획팀 사무실에 혼자 앉는다. 3년간 이름 한 번 불린 적 없던 자리다. 이제 이 자리의 의미가 달라졌다. 시혁은 TF룸 책상 위에 내년도 물류 재설계 일정표를 펼쳐 놓는다.",
        "reward": "S등급 확정. 오세진 팀장 축 정리 완료. 경영기획팀 실질 리더 포지션 확보. 전무 직보 + TF 실무 간사 + 감사 지원 경험이 한 사람에게 모였다. Lv6 TF 실권 진입. 동시에 시혁은 처음으로 자기 라인을 만들 수 있는 위치에 섰다."
    },
    "stakes": "S등급은 받았지만 직급은 사원이다. 실질 리더 포지션은 공식 직함이 뒷받침되지 않으면 다음 인사에서 뒤집힐 수 있다.",
    "power_shift": {
        "protagonist": "S등급 + 경영기획팀 실질 리더 + Lv6 TF 실권. 오세진 축 정리 완료.",
        "antagonist": "오세진 퇴장. 장현태는 여전히 MD사업부에 있지만 감사 압박 아래."
    },
    "relationship_delta": [
        {
            "target": "오세진(팀장)",
            "before": "팀 내 충성 전환으로 고립이 시작된 팀장",
            "after": "유통사업부 파견. 시혁의 적대자에서 퇴장."
        },
        {
            "target": "박전무",
            "before": "시혁의 성과를 직접 확인하고 HR에 전화를 건 적극적 후원자",
            "after": "인사평가에 직접 의견을 첨부한 시혁의 공식 후원자"
        },
        {
            "target": "경영기획팀 후배사원",
            "before": "시혁에게 직접 자료를 보내기 시작한 사실상의 시혁 라인",
            "after": "팀장 부재 상태에서 시혁의 실질 지시를 따르는 팀원"
        }
    ],
    "foreshadow": [
        "오세진이 빠진 경영기획팀은 시혁이 채우지만, 공식 직함 없는 리더는 외부에서 도전받기 쉽다.",
        "장현태는 아직 살아 있다. 오세진 축이 정리되면서 장현태와의 최종전이 더 선명해진다."
    ],
    "callback": [
        "시혁의 이름이 처음 불린 것이 전무 입에서였다면, 이번에는 인사 결과지에 공식으로 각인됨.",
        "오세진이 공을 가져가던 패턴이 마침내 뒤집혔다. 인사평가 결과지에는 시혁 이름만 있다."
    ],
    "emotional_beat": {
        "type": "validation",
        "intensity": 9
    },
    "tension_level": 4,
    "pov_character": "한시혁",
    "location": {
        "place": "한일유통 인사팀 / 경영기획팀 사무실 / TF룸",
        "type": "본사"
    },
    "time_span": {
        "duration": "1일",
        "in_story_time": "2025년 12월 하순"
    },
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv5 예산 발언권 + 오세진 네트워크 와해 진행 + 팀 내 실질 중심 이동 시작",
        "capital_after": "Lv6 TF 실권 + S등급 + 경영기획팀 실질 리더 + 전무 직보 + 자기 라인 형성 가능",
        "capital_delta": "Lv5→Lv6 점프 (소득) + S등급 (소득) + 오세진 퇴장 (구조 변화)",
        "profit_loss": "전면 소득. S등급, 실질 리더, 오세진 축 정리.",
        "method": "해당 없음 — 보상 블록. 앞선 블록들의 축적이 인사 결과로 확정된 것.",
        "investment_type": "보상 확정",
        "deal_type": "인사평가 확정",
        "leverage_used": [
            "전무의 직접 의견 첨부",
            "프로젝트별 before-after 증명서",
            "서정민 확인서",
            "올해 전사적 기여 이력"
        ],
        "opponent": {
            "name": "해당 없음",
            "type": "보상 블록",
            "weakness_exploited": "해당 없음"
        },
        "historical_event": {
            "name": None,
            "year": None,
            "how_exploited": None
        },
        "time_pressure": "해당 없음",
        "knowledge_used": "해당 없음",
        "risk_level": "무위험 (보상 블록)",
        "business_sector": "인사 / 경영기획",
        "section_rotation": "ARC-04 감각의 흔들림",
        "success_pattern": "3년간의 투명인간이 S등급을 받았다. 인사평가 결과지에 이름이 남는 것이 조직에서 가장 확실한 증명이다.",
        "special_ability": {
            "has_ability": True,
            "ability_type": "감각",
            "ability_name": "조직 역학 조감",
            "ability_source": "건강검진 이후 발현 (원인 불명)",
            "ability_used_for": "이 블록에서 감각은 보조적. 결과는 문서와 증거로 만들었다."
        }
    },
    "regression_ext": {
        "is_regressor": False,
        "regression_type": None,
        "execution_doctrine": "이름이 결과지에 남는 것이 조직에서 가장 확실한 무기다."
    },
    "block_no": 40
}

# ── ARC-05 (41-50): 본사를 넘어서 ──────────

block_41 = {
    "block_id": "Block 41",
    "title": "계열사 호출",
    "content": {
        "context": "2026년 1월 초, 시혁에게 처음 보는 회의 초대가 온다. 한일그룹 경영지원실에서 보낸 계열사 합동 물류 효율화 회의. 한일유통뿐 아니라 한일식품, 한일건설의 물류 담당자가 함께 모이는 자리다. 시혁이 불린 이유는 명확하다 — 한일유통 물류 재설계 TF에서 가장 숫자를 잘 아는 사람. 시혁은 처음으로 본사가 아닌 한일그룹 본관 회의실에 들어간다. 회의실 분위기가 다르다. 유통 안에서는 시혁이 전무 직보 라인이었지만, 여기서는 계열사 3곳의 부장급 이상이 앉아 있고 시혁은 가장 직급이 낮은 참석자다. 감각이 작동한다 — 하지만 읽히는 양이 달라졌다. 유통 내부에서는 모든 사람의 이해관계가 이어져 있었지만, 계열사 간에는 끊어진 부분이 많다. 시혁은 처음으로 읽히지 않는 구간이 사람이 아니라 조직 경계에서 발생한다는 것을 체감한다.",
        "event_villain": "한일그룹 경영지원실 팀장 정태호가 회의를 주관한다. 정태호는 시혁을 호출했지만, 실제로는 유통의 물류 재설계 성과를 그룹 차원으로 가져와 자기 실적으로 보고하려는 의도가 있다. 시혁의 데이터가 필요하지 시혁이 필요한 것은 아니다.",
        "solution": "시혁은 회의에서 자기 역할을 데이터 제공자로 한정한다. 유통의 물류 재설계 성과를 발표하되, 계열사에 적용할 수 있는 부분은 '검토가 필요하다'고 선을 긋는다. 감각으로 읽은 것 — 정태호가 원하는 건 시혁의 데이터를 자기 보고서에 넣는 것이다. 시혁은 데이터는 주되 보고서의 주체는 넘기지 않는 선을 유지한다.",
        "reward": "계열사 회의 첫 참석 완료. 시혁은 한일유통 바깥의 숫자와 사람을 처음 직접 봤다. 감각이 조직 경계에서 끊어진다는 발견은 불편하지만, 동시에 '경계를 넘으면 감각이 새로 적응할 수 있는가'라는 질문이 생긴다."
    },
    "stakes": "계열사 회의에서 시혁의 데이터가 정태호 이름으로 나가면 그룹 레벨에서 시혁의 존재감은 0이 된다. 동시에 계열사 판에서 실패하면 유통 안의 지위도 흔들릴 수 있다.",
    "power_shift": {
        "protagonist": "계열사 합동 회의 첫 참석. 감각의 조직 경계 한계 발견.",
        "antagonist": "정태호(경영지원실 팀장)는 시혁의 데이터를 자기 보고서로 가져가려 한다."
    },
    "relationship_delta": [
        {
            "target": "정태호(경영지원실 팀장)",
            "before": "신규 — 시혁을 호출한 그룹 본관 인물",
            "after": "시혁의 데이터를 원하지만 시혁 자체는 원하지 않는 이용적 관계"
        }
    ],
    "foreshadow": [
        "감각이 조직 경계에서 끊어지는 경험은 이후 시혁이 경계를 넘어 감각을 확장하는 동기가 된다.",
        "정태호의 데이터 탈취 시도는 더 큰 규모로 반복된다 — 계열사 레벨에서는 데이터를 가진 사람이 아니라 보고서를 올리는 사람이 공을 갖는다."
    ],
    "callback": [
        "시혁이 유통 안에서 올라간 성과(물류 재설계, 감사 지원)가 그룹 차원에서 주목받은 결과.",
        "감각의 조직 경계 한계는 감각이 감정 있는 상대에게만 작동한다는 이전 발견의 확장판."
    ],
    "emotional_beat": {
        "type": "curiosity",
        "intensity": 6
    },
    "tension_level": 6,
    "pov_character": "한시혁",
    "location": {
        "place": "한일그룹 본관 15층 합동 회의실",
        "type": "그룹 본관"
    },
    "time_span": {
        "duration": "2일",
        "in_story_time": "2026년 1월 초"
    },
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + S등급 + 경영기획팀 실질 리더 + 전무 직보 + 자기 라인 형성 가능",
        "capital_after": "Lv6 TF 실권 + 계열사 회의 접근권 + 그룹 레벨 데이터 노출 + 감각 경계 한계 인식",
        "capital_delta": "계열사 회의 접근 (소득) + 감각 한계 새 발견 (중립)",
        "profit_loss": "접근권은 얻었지만 데이터 소유권은 위협받고 있다.",
        "method": "데이터는 제공하되 보고서 주체는 넘기지 않는 선 유지.",
        "investment_type": "접근권 확보",
        "deal_type": "계열사 협업 회의 진입",
        "leverage_used": [
            "한일유통 물류 재설계 성과 데이터",
            "전무 직보 라인에서의 신뢰"
        ],
        "opponent": {
            "name": "정태호",
            "type": "그룹 경영지원실의 데이터 탈취 시도",
            "weakness_exploited": "정태호는 데이터를 직접 만들 수 없다. 시혁이 데이터 제공을 조절하면 보고서의 질을 통제할 수 있다."
        },
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "그룹 분기 경영회의까지 4주",
        "knowledge_used": "유통 물류 재설계 전 과정의 숫자와 맥락",
        "risk_level": "중위험 (그룹 레벨은 유통 내부보다 실패 비용이 크다)",
        "business_sector": "그룹 경영지원 / 물류",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "새 판에서는 먼저 규칙을 읽고, 자기 데이터의 소유권을 지킨다.",
        "special_ability": {
            "has_ability": True,
            "ability_type": "감각",
            "ability_name": "조직 역학 조감",
            "ability_source": "건강검진 이후 발현 (원인 불명)",
            "ability_used_for": "조직 경계에서 감각이 끊어지는 현상을 처음 체감. 정태호의 의도는 부분적으로 읽힘."
        }
    },
    "regression_ext": {
        "is_regressor": False,
        "regression_type": None,
        "execution_doctrine": "새 판에서는 먼저 규칙을 배운다. 데이터를 주되 이름은 지킨다."
    },
    "block_no": 41
}

# Block 42-70은 분량이 매우 크므로 별도 파일로 이어서 작성합니다.
# 여기서는 먼저 Block 36-41을 기존 파일에 추가하고 검증합니다.

def main():
    # Read existing
    with open(TR_PATH, 'r', encoding='utf-8') as f:
        existing = json.load(f)

    assert len(existing) == 35, f"Expected 35 blocks, got {len(existing)}"
    assert existing[-1]["block_no"] == 35

    new_blocks = [block_36, block_37, block_38, block_39, block_40, block_41]

    # Verify capital continuity
    prev_cap = existing[-1]["genre_ext"]["capital_after"]
    for b in new_blocks:
        assert b["genre_ext"]["capital_before"] == prev_cap, \
            f"Block {b['block_no']}: capital_before mismatch.\n  Expected: {prev_cap}\n  Got: {b['genre_ext']['capital_before']}"
        prev_cap = b["genre_ext"]["capital_after"]

    # Verify bundle density
    for b in new_blocks:
        c = b["content"]
        bundle = len(c.get("context","")) + len(c.get("event_villain","")) + len(c.get("solution","")) + len(c.get("reward","")) + len(b.get("stakes",""))
        print(f"Block {b['block_no']} ({b['title']}): bundle_chars = {bundle}")
        assert bundle >= 300, f"Block {b['block_no']}: bundle too thin ({bundle})"

    # Append
    combined = existing + new_blocks
    with open(TR_PATH, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(combined)} blocks to {TR_PATH}")
    print(f"New blocks added: {[b['block_no'] for b in new_blocks]}")

if __name__ == "__main__":
    main()
