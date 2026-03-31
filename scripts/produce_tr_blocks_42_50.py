#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Block 42-50 production: ARC-05 본사를 넘어서 (continuation)"""

import json, pathlib

TR_PATH = pathlib.Path(r"C:\Users\User\Desktop\글도비\treatments\office_checkup_next_day_tr_block_070_draft.json")

block_42 = {
    "block_id": "Block 42",
    "title": "다른 회사의 숫자",
    "content": {
        "context": "2026년 1월 중순. 시혁은 계열사 합동 물류 효율화 회의를 준비하면서 한일식품과 한일건설의 물류 데이터를 처음 직접 본다. 같은 그룹인데 비용 항목 이름이 다르다. 한일유통의 '배송 단가'가 한일식품에서는 '콜드체인 운송비', 한일건설에서는 '자재 이송료'다. 숫자만 보면 비교가 안 되지만, 시혁이 항목별 구조를 다시 맞추자 같은 병목이 보인다. 세 회사 모두 물류 외주 계약의 갱신 시점에서 단가가 뛰고, 갱신 전 3개월간 실제 물동량과 계약 물량의 괴리가 커진다. 감각이 작동한다 — 하지만 유통 안에서처럼 사람의 의도까지 읽히는 것이 아니라, 숫자의 패턴이 먼저 보인다. 계열사 경계에서는 감각이 사람 모드가 아니라 숫자 모드로 작동한다.",
        "event_villain": "정태호는 시혁이 만든 비교표를 가져가려 한다. '내가 경영지원실 이름으로 올릴 테니 네 이름은 빼자'고 요청한다. 노골적이지만, 그룹 본관에서는 흔한 일이다.",
        "solution": "시혁은 정태호의 요청을 거절하지 않는다. 대신 조건을 건다. '비교표는 드리겠지만, 경영지원실 보고서에 한일유통 물류 TF의 협조로 작성했다는 각주를 넣어 주십시오.' 정태호는 각주 정도는 괜찮다고 수락한다. 시혁은 각주가 아니라 그 각주를 읽을 사람이 누구인지를 계산한다. 그룹 경영회의에서 각주를 읽을 사람은 그룹 전략실장이다.",
        "reward": "비교표가 정태호 보고서에 각주와 함께 실린다. 시혁의 이름은 보고서 본문에 없지만, 각주를 통해 그룹 전략실장의 시야에 들어갈 경로가 생겼다. 동시에 계열사 물류 데이터의 패턴을 읽는 경험은 시혁의 판을 유통 밖으로 처음 넓혔다."
    },
    "stakes": "각주가 무시되면 시혁의 계열사 노출 전략은 실패한다. 정태호가 각주를 빼면 시혁은 데이터만 빼앗긴 셈이 된다.",
    "power_shift": {
        "protagonist": "계열사 물류 데이터 비교 능력 확보. 그룹 전략실장 시야 진입 경로 개설.",
        "antagonist": "정태호는 비교표를 가져갔지만 각주라는 실을 남겨 줌."
    },
    "relationship_delta": [
        {
            "target": "정태호(경영지원실 팀장)",
            "before": "시혁의 데이터를 원하지만 시혁 자체는 원하지 않는 이용적 관계",
            "after": "비교표를 가져갔지만 각주를 허용한 거래 관계"
        }
    ],
    "foreshadow": [
        "각주를 통한 그룹 전략실장 노출은 몇 블록 뒤에서 그룹 전략실장의 직접 접촉으로 이어진다.",
        "계열사 물류 외주 계약 갱신 병목은 공동 TF 설계의 핵심 근거가 된다."
    ],
    "callback": [
        "시혁이 데이터를 주되 이름을 지키겠다던 전략이 각주라는 구체적 형태로 실행됨.",
        "감각이 조직 경계에서 숫자 모드로 전환된다는 발견의 첫 실전 적용."
    ],
    "emotional_beat": {"type": "discovery", "intensity": 7},
    "tension_level": 6,
    "pov_character": "한시혁",
    "location": {"place": "한일유통 TF룸 / 한일그룹 본관 자료실", "type": "본사 / 그룹 본관"},
    "time_span": {"duration": "3일", "in_story_time": "2026년 1월 중순"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 계열사 회의 접근권 + 그룹 레벨 데이터 노출 + 감각 경계 한계 인식",
        "capital_after": "Lv6 TF 실권 + 계열사 물류 데이터 비교 역량 + 그룹 전략실장 시야 진입 경로 (각주)",
        "capital_delta": "데이터 비교 역량 (소득) + 그룹 전략실장 노출 경로 (소득)",
        "profit_loss": "비교표는 정태호 이름으로 나갔지만 각주를 통해 시혁의 흔적이 남았다.",
        "method": "비교표 제공 조건으로 각주 삽입. 각주의 진짜 독자는 그룹 전략실장.",
        "investment_type": "조건부 데이터 거래",
        "deal_type": "데이터 교차 분석 + 각주 거래",
        "leverage_used": ["계열사 3사 물류 데이터 비교 능력", "각주라는 최소 노출 장치"],
        "opponent": {"name": "정태호", "type": "데이터 소유권 탈취", "weakness_exploited": "정태호는 비교표를 직접 만들 역량이 없다. 시혁의 조건을 수용할 수밖에 없었다."},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "그룹 분기 경영회의까지 2주",
        "knowledge_used": "유통, 식품, 건설 3사의 물류 비용 구조 패턴",
        "risk_level": "중위험 (각주가 무시되면 데이터만 빼앗김)",
        "business_sector": "그룹 경영지원 / 계열사 물류",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "데이터를 줄 때는 반드시 자기 이름이 남는 장치를 건다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "계열사 경계에서 숫자 패턴을 먼저 읽는 모드 적응. 물류 외주 갱신 병목 공통점 발견."}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "데이터를 줄 때는 이름이 남는 장치를 반드시 건다."},
    "block_no": 42
}

block_43 = {
    "block_id": "Block 43",
    "title": "본사식 브리핑",
    "content": {
        "context": "2026년 1월 하순, 그룹 분기 경영회의 사전 브리핑. 정태호가 경영지원실 이름으로 보고서를 올리고, 시혁은 보조 발표자로 참석한다. 시혁이 유통 물류 재설계 부분을 설명하는데, 그룹 전략실 이상무가 끼어든다. '유통 물류 숫자는 알겠는데, 이게 그룹 전체 물류비에 어떤 의미를 갖느냐?' 시혁은 유통 숫자 기준으로 답변을 시작하지만, 이상무는 '그룹 언어'로 말하라고 요구한다. 유통의 물동량 단위가 아니라 그룹 전체 물류비 대비 비율, 계열사 간 시너지 효과 수치, 연간 절감 추정치를 원한다. 시혁은 이 숫자를 갖고 있지 않다. 유통 안에서는 절대치로 충분했지만, 그룹 레벨에서는 상대 비율과 시너지 언어가 기본이다. 시혁은 답변을 마치지 못하고 '추가 분석 후 제출하겠습니다'로 끝낸다.",
        "event_villain": "이상무는 시혁을 공격한 것이 아니다. 그룹 전략실의 기준으로 당연한 질문을 한 것이다. 하지만 시혁에게는 첫 번째 그룹 레벨 패배다.",
        "solution": "시혁은 브리핑 직후 TF룸으로 돌아와 그룹 전략실이 사용하는 보고 양식을 구한다. 전무에게 요청해 과거 그룹 경영회의 보고 자료 3건을 받는다. 밤새 읽으며 '그룹 언어'의 구조를 익힌다. 유통 숫자를 그룹 비율로 변환하는 공식을 만들고, 계열사 시너지 추정 모델을 처음으로 설계한다.",
        "reward": "이 블록은 패배에서의 학습이다. 시혁은 그룹 보고 양식의 구조를 이해하고 변환 공식을 만들었다. 아직 완성되지 않았지만, 다음 기회에는 그룹 언어로 말할 수 있는 기반이 생겼다."
    },
    "stakes": "그룹 레벨에서 첫 인상이 '유통 사원이 그룹 숫자를 모른다'로 각인되면 이후 그룹 회의에 다시 불리기 어렵다.",
    "power_shift": {
        "protagonist": "그룹 레벨 패배. 하지만 그룹 보고 양식과 변환 공식 학습.",
        "antagonist": "이상무(그룹 전략실)는 시혁의 능력을 아직 인정하지 않지만, 존재는 인지했다."
    },
    "relationship_delta": [
        {"target": "이상무(그룹 전략실)", "before": "신규 — 브리핑에서 처음 만남", "after": "시혁의 유통 역량은 확인했지만 그룹 언어 부재를 지적한 평가자"},
        {"target": "박전무", "before": "인사평가에 직접 의견을 첨부한 시혁의 공식 후원자", "after": "그룹 보고 자료를 제공하며 시혁의 그룹 레벨 성장을 지원하는 후원자"}
    ],
    "foreshadow": [
        "시혁이 만든 그룹 비율 변환 공식은 이후 공동 TF 설계의 핵심 도구가 된다.",
        "이상무와의 관계는 적대가 아니라 시험으로 시작했다. 시혁이 그룹 언어를 익히면 협력자가 될 수 있다."
    ],
    "callback": [
        "유통 안에서는 절대치로 충분했지만 그룹에서는 상대 비율이 기본이라는 사실 — 판이 커지면 규칙도 바뀐다.",
        "감각이 조직 경계에서 숫자 모드로 전환된다는 이전 발견이 한계로 작용. 숫자 패턴은 읽히지만 그룹 언어 번역까지는 안 된다."
    ],
    "emotional_beat": {"type": "setback", "intensity": 6},
    "tension_level": 7,
    "pov_character": "한시혁",
    "location": {"place": "한일그룹 본관 경영회의실 / 한일유통 TF룸", "type": "그룹 본관 / 본사"},
    "time_span": {"duration": "2일", "in_story_time": "2026년 1월 하순"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 계열사 물류 데이터 비교 역량 + 그룹 전략실장 시야 진입 경로 (각주)",
        "capital_after": "Lv6 TF 실권 + 그룹 언어 부재 노출 + 그룹 보고 양식 학습 시작 + 비율 변환 공식 초안",
        "capital_delta": "그룹 레벨 패배 (손실) + 그룹 언어 학습 기반 (소득)",
        "profit_loss": "첫 인상 손실. 하지만 학습 속도가 빠르다.",
        "method": "패배 직후 그룹 보고 양식 분석 + 비율 변환 공식 설계.",
        "investment_type": "역량 보강",
        "deal_type": "브리핑 실패 후 학습",
        "leverage_used": ["전무를 통한 과거 그룹 보고 자료 확보"],
        "opponent": {"name": "이상무", "type": "그룹 전략실의 기준", "weakness_exploited": "해당 없음 — 이 블록에서 시혁이 졌다"},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "다음 그룹 경영회의까지 3개월",
        "knowledge_used": "유통 물류 숫자 (그룹 비율 미변환 상태)",
        "risk_level": "중위험 (그룹 레벨 첫 인상 손실)",
        "business_sector": "그룹 전략 / 물류",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "졌지만 규칙을 배웠다. 다음에는 그룹 언어로 말한다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "이상무의 질문 의도는 읽혔지만 답을 만들 역량이 부족했다. 감각만으로는 안 되는 영역."}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "판이 커지면 언어부터 배운다."},
    "block_no": 43
}

block_44 = {
    "block_id": "Block 44",
    "title": "전략기획 상무의 커피",
    "content": {
        "context": "2026년 2월 초. 이상무가 시혁에게 커피를 제안한다. 그룹 본관 1층 카페. 시혁은 긴장한다 — 브리핑에서 밀린 사람에게 상무가 커피를 사는 것은 보통이 아니다. 이상무가 말한다. '자네가 만든 물류 비교표, 정태호 보고서에 각주로 들어간 거 봤어. 유통 숫자를 저렇게 정리할 수 있는 사람이 경영기획팀 사원이라니.' 시혁은 읽는다 — 이상무는 시혁을 평가하러 온 것이 아니라 '자기 쪽에서 쓸 수 있는 사람인지'를 보러 온 것이다. 이상무는 그룹 전략실에서 계열사 간 물류 표준화 프로젝트를 구상 중이지만, 현장 데이터를 직접 다룰 사람이 없다. 시혁이 그 빈자리에 맞다고 본다.",
        "event_villain": "이상무는 적이 아니다. 하지만 시혁을 '자기 라인'으로 끌어오려는 의도가 있다. 시혁이 이상무 밑에 들어가면 유통의 전무 라인에서 벗어나게 된다. 이상무의 제안은 기회이자 족쇄다.",
        "solution": "시혁은 이상무의 제안에 즉답하지 않는다. '전무님과 상의해 보겠습니다'라고 말한다. 이것은 거절이 아니라 시간 벌기다. 시혁은 이상무의 프로젝트에 참여하면서도 전무 라인을 유지할 수 있는 구조를 찾아야 한다. 돌아가는 길에 감각이 작동한다 — 이상무가 원하는 건 시혁 개인이 아니라 '유통의 현장 데이터에 접근할 수 있는 채널'이다. 시혁이 개인으로 가면 채널이 되지만, TF를 통해 가면 채널이자 주체가 될 수 있다.",
        "reward": "이상무와의 관계가 열렸다. 그룹 전략실의 프로젝트 구상 정보를 처음으로 얻었다. 동시에 시혁은 개인이 아닌 TF 단위로 그룹 레벨에 진입하는 전략을 구상하기 시작한다."
    },
    "stakes": "이상무의 제안을 수락하면 전무 라인에서 이탈. 거절하면 그룹 레벨 진입 기회를 잃는다. 두 라인을 동시에 유지할 수 있는 구조를 찾아야 한다.",
    "power_shift": {
        "protagonist": "그룹 전략실 프로젝트 정보 입수. TF 단위 진입 전략 구상.",
        "antagonist": "이상무는 시혁을 자기 라인으로 끌어오려 하지만, 시혁이 즉답하지 않아 아직 미확정."
    },
    "relationship_delta": [
        {"target": "이상무(그룹 전략실)", "before": "시혁의 유통 역량은 확인했지만 그룹 언어 부재를 지적한 평가자", "after": "시혁을 자기 프로젝트에 끌어오려는 제안자. 회색 협력자."}
    ],
    "foreshadow": [
        "시혁이 구상하는 'TF 단위 그룹 진입'은 공동 TF 설계로 구체화된다.",
        "이상무와의 관계는 단순한 상하가 아니라 상호 필요의 구조. 이후 협력과 견제가 반복된다."
    ],
    "callback": [
        "각주를 통한 그룹 전략실장 노출 전략이 실제로 이상무의 주목을 끌어냄.",
        "감각이 이상무의 의도를 읽음 — 조직 경계에서도 감각이 점차 적응하고 있다."
    ],
    "emotional_beat": {"type": "calculation", "intensity": 6},
    "tension_level": 6,
    "pov_character": "한시혁",
    "location": {"place": "한일그룹 본관 1층 카페", "type": "그룹 본관"},
    "time_span": {"duration": "1일", "in_story_time": "2026년 2월 초"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 그룹 언어 부재 노출 + 그룹 보고 양식 학습 시작 + 비율 변환 공식 초안",
        "capital_after": "Lv6 TF 실권 + 이상무 관계 개설 + 그룹 전략실 프로젝트 정보 + TF 단위 진입 전략 구상",
        "capital_delta": "이상무 관계 (소득) + 그룹 프로젝트 정보 (소득)",
        "profit_loss": "직접적 손익 없음. 관계와 정보 확보.",
        "method": "즉답을 피하고 TF 단위 진입 경로를 구상.",
        "investment_type": "관계 개설",
        "deal_type": "라인 탐색",
        "leverage_used": ["유통 현장 데이터 접근 능력", "각주를 통해 이미 노출된 분석 역량"],
        "opponent": {"name": "이상무 (회색)", "type": "그룹 전략실의 인재 영입 시도", "weakness_exploited": "이상무는 현장 데이터를 직접 다룰 사람이 없다. 시혁의 조건에 맞출 여지가 있다."},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "이상무의 프로젝트 킥오프까지 약 6주",
        "knowledge_used": "감각을 통한 이상무의 진짜 의도 분석",
        "risk_level": "중위험 (라인 선택의 분기점)",
        "business_sector": "그룹 전략 / 물류 표준화",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "기회가 와도 즉답하지 않는다. 구조를 먼저 설계한다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "이상무의 진짜 의도(현장 데이터 채널 확보)와 제안의 이면(전무 라인 이탈) 분석"}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "기회가 와도 구조를 먼저 본다. 개인으로 가면 채널이 되지만 TF로 가면 주체가 된다."},
    "block_no": 44
}

block_45 = {
    "block_id": "Block 45",
    "title": "같은 숫자, 다른 무게",
    "content": {
        "context": "Quiet block. 2026년 2월 중순. 시혁은 그룹 전략실 과장 윤재영과 점심을 먹는다. 윤재영은 이상무의 밑에서 계열사 데이터 취합을 맡는 실무자인데, 시혁에게 호의적이다. 이유가 있다 — 윤재영도 현장 숫자를 다루는 사람이 그룹 본관에 거의 없다는 점에 답답해하고 있었다. 점심 자리에서 윤재영이 말한다. '같은 1억이라도 유통에서의 1억과 건설에서의 1억은 전략실에서 완전히 다른 무게로 읽혀요. 숫자를 그룹 프레임에 올리는 건 숫자를 만드는 것보다 어렵거든요.' 시혁은 듣는다. 이것은 감각으로 읽는 것이 아니라 경험 있는 사람에게 배우는 것이다.",
        "event_villain": "직접 적대 없음. 학습 블록.",
        "solution": "시혁은 윤재영에게 묻는다. '그룹 경영회의에서 숫자를 올릴 때 가장 먼저 보는 게 뭔가요?' 윤재영이 답한다. '절대 수치가 아니라 비교 프레임이에요. 작년 대비, 경쟁사 대비, 계열사 내 순위. 숫자 자체보다 그 숫자가 어디에 놓이느냐가 무기입니다.' 시혁은 자기 비율 변환 공식을 다시 꺼내 비교 프레임을 입힌다.",
        "reward": "그룹 언어의 핵심이 '비교 프레임'이라는 것을 체득. 윤재영이라는 그룹 본관 협력자를 확보. 시혁의 데이터 역량에 그룹 프레임이 결합되기 시작한다."
    },
    "stakes": "낮음. 조용한 학습 블록이지만, 이 학습이 없으면 시혁은 계속 유통 언어로만 말하는 사람에 머문다.",
    "power_shift": {
        "protagonist": "그룹 프레임 학습. 윤재영 확보.",
        "antagonist": "해당 없음."
    },
    "relationship_delta": [
        {"target": "윤재영(그룹 전략실 과장)", "before": "신규", "after": "그룹 언어와 프레임을 가르쳐 주는 실무 협력자"}
    ],
    "foreshadow": [
        "비교 프레임의 학습은 공동 TF 조건표 협상에서 결정적 무기가 된다.",
        "윤재영과의 관계는 이후 시혁이 그룹 레벨에서 움직일 때 정보 통로로 작동한다."
    ],
    "callback": [
        "브리핑에서 이상무에게 밀린 이유가 비교 프레임 부재였다는 것이 윤재영의 설명으로 확인됨.",
        "시혁이 만든 비율 변환 공식이 비교 프레임과 결합하면서 그룹 언어 역량이 완성 단계에 진입."
    ],
    "emotional_beat": {"type": "learning", "intensity": 4},
    "tension_level": 3,
    "pov_character": "한시혁",
    "location": {"place": "여의도 식당가 / 한일그룹 전략실 자료실", "type": "외부 / 그룹 본관"},
    "time_span": {"duration": "1주", "in_story_time": "2026년 2월 중순"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 이상무 관계 개설 + 그룹 전략실 프로젝트 정보 + TF 단위 진입 전략 구상",
        "capital_after": "Lv6 TF 실권 + 그룹 비교 프레임 학습 + 윤재영 협력 관계 + 비율 변환 공식에 프레임 결합",
        "capital_delta": "그룹 프레임 역량 (소득) + 윤재영 관계 (소득)",
        "profit_loss": "직접적 손익 없음. 역량과 관계 축적.",
        "method": "경험 있는 실무자에게 직접 묻고 배운다.",
        "investment_type": "학습",
        "deal_type": "해당 없음 — quiet block",
        "leverage_used": [],
        "opponent": {"name": "해당 없음", "type": "학습 블록", "weakness_exploited": "해당 없음"},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "해당 없음",
        "knowledge_used": "윤재영의 그룹 프레임 경험",
        "risk_level": "무위험",
        "business_sector": "그룹 전략 / 데이터 프레이밍",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "모르는 것은 감각이 아니라 사람에게서 배운다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "이 블록에서 감각은 보조적. 학습과 관계 구축이 주."}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "감각으로 못 읽는 것은 사람에게 물어서 배운다."},
    "block_no": 45
}

block_46 = {
    "block_id": "Block 46",
    "title": "공동 TF 설계",
    "content": {
        "context": "2026년 2월 하순. 시혁은 전무에게 한 장짜리 제안서를 올린다. '한일그룹 계열사 간 물류 표준화 공동 TF.' 핵심은 이것이다 — 시혁이 이상무 밑으로 가는 것이 아니라, 유통 TF와 그룹 전략실이 공동으로 운영하는 TF를 새로 만들자는 것. 시혁은 유통 측 실무 리더로 참여하되, 보고 라인은 전무와 이상무 양쪽에 두는 구조다. 전무가 묻는다. '이상무 쪽에서 이걸 받아들일 거라고 보나?' 시혁이 답한다. '이상무님은 현장 데이터를 직접 다룰 사람이 없습니다. 이 구조면 데이터와 사람을 동시에 얻습니다.' 전무는 이상무에게 직접 제안해보라고 한다.",
        "event_villain": "정태호가 이 제안을 먼저 듣고 반발한다. 경영지원실이 이미 계열사 물류 취합을 맡고 있는데, 새 TF가 생기면 자기 관할이 줄어든다. 정태호는 이상무에게 '유통 사원이 그룹 TF를 제안하는 것은 월권'이라고 귓바람을 넣는다.",
        "solution": "시혁은 이상무를 직접 만나 제안서를 설명한다. 동시에 계열사 물류 비교표를 업그레이드한 버전 — 비교 프레임을 입힌 그룹 언어 버전을 함께 제출한다. 이상무는 비교표를 30분간 읽고 말한다. '이건 정태호가 만들 수 없는 수준이다.' 이상무는 공동 TF를 수락한다. 단, 조건이 있다. '분기마다 그룹 경영회의에 직접 보고할 것.'",
        "reward": "공동 TF 설계 승인. 시혁은 유통 측 실무 리더로 참여하되 전무와 이상무 양쪽 보고 라인을 유지한다. 정태호의 반발은 이상무가 직접 제압했다. 시혁은 개인이 아닌 TF 단위로 그룹 레벨에 진입하는 데 성공했다."
    },
    "stakes": "이상무가 거절하면 시혁의 그룹 레벨 진입은 정태호의 각주에 의존하는 수준에 머문다. 동시에 전무 라인과 이상무 라인 양쪽을 잡는 구조는 하나가 무너지면 다른 쪽도 위험해진다.",
    "power_shift": {
        "protagonist": "공동 TF 승인. 전무+이상무 양쪽 보고 라인 확보. 그룹 레벨 진입.",
        "antagonist": "정태호의 관할이 줄어들었고, 이상무에 의해 반발이 제압됨."
    },
    "relationship_delta": [
        {"target": "이상무(그룹 전략실)", "before": "시혁을 자기 프로젝트에 끌어오려는 제안자. 회색 협력자.", "after": "공동 TF를 수락한 파트너. 분기 보고 조건."},
        {"target": "정태호(경영지원실 팀장)", "before": "비교표를 가져갔지만 각주를 허용한 거래 관계", "after": "공동 TF 설계로 관할이 줄어든 상태. 시혁에 대한 반감 증가."}
    ],
    "foreshadow": [
        "전무+이상무 양쪽 보고 라인은 이후 라인 선택의 딜레마로 발전한다.",
        "정태호의 반감은 장현태 잔여 세력과 합류할 가능성이 있다."
    ],
    "callback": [
        "시혁이 구상했던 'TF 단위 그룹 진입 전략'이 구체적 제안서로 실행됨.",
        "그룹 비교 프레임을 입힌 물류 비교표가 이상무를 설득하는 결정적 도구."
    ],
    "emotional_beat": {"type": "strategic_triumph", "intensity": 7},
    "tension_level": 7,
    "pov_character": "한시혁",
    "location": {"place": "한일유통 전무실 / 이상무 집무실", "type": "본사 / 그룹 본관"},
    "time_span": {"duration": "4일", "in_story_time": "2026년 2월 하순"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 그룹 비교 프레임 학습 + 윤재영 협력 관계 + 비율 변환 공식에 프레임 결합",
        "capital_after": "Lv6 TF 실권 + 공동 TF 유통 측 실무 리더 + 전무/이상무 양쪽 보고 라인 + 그룹 경영회의 직접 보고 권한",
        "capital_delta": "공동 TF 리더십 (소득) + 그룹 보고 권한 (소득) + 정태호 반감 (비용)",
        "profit_loss": "그룹 레벨 진입 확정. 정태호 관계 악화는 감수.",
        "method": "공동 TF 구조로 개인 이동이 아닌 TF 단위 그룹 진입. 비교 프레임 버전 제출로 이상무 설득.",
        "investment_type": "구조 설계",
        "deal_type": "공동 TF 설계안 승인",
        "leverage_used": ["그룹 비교 프레임 입힌 물류 비교표", "전무의 지원", "이상무의 현장 데이터 필요"],
        "opponent": {"name": "정태호", "type": "관할 축소에 대한 반발", "weakness_exploited": "정태호의 물류 분석 역량은 시혁에 비해 현저히 부족. 이상무가 직접 품질 차이를 인지함."},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "이상무의 프로젝트 킥오프 4주 전",
        "knowledge_used": "계열사 3사 물류 데이터 + 그룹 비교 프레임",
        "risk_level": "중위험 (양쪽 라인 유지 구조의 불안정성)",
        "business_sector": "그룹 전략 / 계열사 물류 표준화",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "개인으로 가면 채널이 되지만 TF로 가면 주체가 된다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "이상무의 수락 조건(분기 보고)이 진짜 의미하는 바를 읽음 — 성과를 직접 보겠다는 견제와 기회의 동시 부여"}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "개인이 아닌 구조로 진입한다. 구조는 개인보다 오래간다."},
    "block_no": 46
}

block_47 = {
    "block_id": "Block 47",
    "title": "두 회사를 잇는 한 장",
    "content": {
        "context": "2026년 3월 초. 공동 TF 킥오프. 한일유통과 한일식품의 물류 담당자, 그룹 전략실 윤재영, 경영지원실 정태호(관찰자 자격)가 모인다. 시혁이 첫 TF 안건으로 '계열사 간 물류 외주 계약 갱신 시점 통합'을 올린다. 핵심 논리 — 세 계열사가 각각 물류 외주사와 별도로 계약을 갱신하면 협상력이 분산된다. 갱신 시점을 묶으면 그룹 차원에서 협상할 수 있고, 연간 물류비 절감이 5-8% 예상된다. 시혁은 한 장짜리 조건표에 각 계열사의 현재 갱신 시점, 계약 물량, 외주 단가, 통합 시 예상 절감액을 정리했다. 이 한 장이 두 회사를 잇는다.",
        "event_villain": "한일식품 물류 담당 부장이 반발한다. '식품 콜드체인은 일반 물류와 다릅니다. 묶으면 품질 문제가 생깁니다.' 논리적으로 맞는 반론이다. 정태호도 이 반론을 지지하며 '계열사별 특수성을 무시하면 안 됩니다'라고 거든다.",
        "solution": "시혁은 반론을 정면으로 반박하지 않는다. 대신 조건표의 두 번째 열을 펼친다. '콜드체인 전용 외주사와 일반 물류 외주사를 분리해서 묶는 안입니다. 특수성은 유지하되 갱신 시점과 협상 테이블만 공유합니다.' 시혁은 반론을 예측하고 조건표에 이미 분리안을 넣어 뒀다. 한일식품 부장이 조건표를 다시 읽고 고개를 끄덕인다.",
        "reward": "공동 TF 첫 안건 합의. 시혁의 조건표가 계열사 간 첫 공동 실행 안건으로 채택됐다. 시혁은 데이터를 잘 읽는 사람에서 '판을 설계하는 사람'으로 인식이 바뀌기 시작한다."
    },
    "stakes": "첫 안건이 부결되면 공동 TF의 존재 의미가 흔들린다. 시혁의 리더십도 킥오프에서 무너진다.",
    "power_shift": {
        "protagonist": "공동 TF 첫 안건 합의. 계열사 간 판 설계자로 인식 전환.",
        "antagonist": "한일식품 부장의 반론은 합리적이었지만 분리안으로 해소됨. 정태호의 지원 사격 실패."
    },
    "relationship_delta": [
        {"target": "한일식품 물류 부장", "before": "신규 — 공동 TF에서 처음 만남", "after": "시혁의 분리안에 동의. 전문성을 인정하기 시작."},
        {"target": "정태호(경영지원실 팀장)", "before": "공동 TF 설계로 관할이 줄어든 상태. 시혁에 대한 반감 증가.", "after": "TF 회의에서 반론 지원 실패. 관찰자 위치로 밀려남."}
    ],
    "foreshadow": [
        "조건표를 통한 판 설계 능력은 이후 장현태 최종전에서도 핵심 무기가 된다.",
        "정태호가 관찰자로 밀려난 것은 장현태 잔여 세력과의 합류를 가속할 수 있다."
    ],
    "callback": [
        "계열사 물류 외주 갱신 병목이 실제 안건으로 구체화. 시혁의 데이터 분석이 실행으로 전환.",
        "반론을 예측하고 분리안을 미리 준비한 것은 감각이 아니라 경험과 설계의 결과."
    ],
    "emotional_beat": {"type": "demonstration", "intensity": 8},
    "tension_level": 7,
    "pov_character": "한시혁",
    "location": {"place": "한일그룹 합동 TF 회의실", "type": "그룹 본관"},
    "time_span": {"duration": "2일", "in_story_time": "2026년 3월 초"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 공동 TF 유통 측 실무 리더 + 전무/이상무 양쪽 보고 라인 + 그룹 경영회의 직접 보고 권한",
        "capital_after": "Lv6 TF 실권 + 공동 TF 첫 안건 합의 + 계열사 간 판 설계자 인식 + 한일식품 협력 확보",
        "capital_delta": "첫 안건 합의 (소득) + 판 설계자 인식 (소득) + 정태호 관찰자화 (구조 변화)",
        "profit_loss": "안건 합의로 공동 TF의 존재 근거가 확보됨.",
        "method": "반론을 예측한 분리안을 조건표에 미리 포함. 정면 반박 대신 대안 제시.",
        "investment_type": "구조 설계 + 협상",
        "deal_type": "조건표 기반 합의",
        "leverage_used": ["계열사 3사 물류 데이터", "콜드체인/일반 물류 분리 설계", "그룹 비교 프레임"],
        "opponent": {"name": "한일식품 물류 부장 + 정태호", "type": "계열사 특수성 반론 + 관할 방어", "weakness_exploited": "반론은 합리적이었지만 분리안이라는 구체적 대안 앞에서 유지할 명분이 없었다."},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "물류 외주 계약 갱신 시즌까지 2개월",
        "knowledge_used": "콜드체인과 일반 물류의 구조적 차이 + 계약 갱신 시점 데이터",
        "risk_level": "중위험 (첫 안건 실패 시 TF 자체가 흔들림)",
        "business_sector": "그룹 물류 / 계열사 협업",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "반론을 예측하고 대안을 미리 설계한다. 정면 반박보다 대안 제시가 강하다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "한일식품 부장의 반론이 진심인지 정치인지 읽음 — 진심이었기 때문에 대안으로 해소 가능했다."}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "반론을 예측하고 대안을 미리 넣어 둔다. 정면충돌은 최후 수단이다."},
    "block_no": 47
}

block_48 = {
    "block_id": "Block 48",
    "title": "이름 위의 이름",
    "content": {
        "context": "2026년 3월 중순. 공동 TF의 물류 외주 갱신 통합안이 그룹 경영회의 안건으로 올라간다. 이상무가 시혁에게 말한다. '발표는 내가 한다. 자네는 데이터 보조.' 시혁은 읽는다 — 이상무는 공동 TF를 수락했지만 그룹 경영회의에서의 공은 자기가 가져갈 생각이다. 시혁의 이름은 다시 보고서 밑에 깔린다. 동시에 정태호가 장현태 잔여 세력과 접촉하고 있다는 정보가 윤재영을 통해 들어온다. 정태호는 시혁이 만든 공동 TF를 무력화하기 위해 'MD사업부 측 물류 데이터가 미반영'이라는 문제를 제기할 준비를 하고 있다.",
        "event_villain": "이상무는 시혁의 적은 아니지만, 그룹 경영회의에서 자기 이름을 앞에 세우려 한다. 정태호는 장현태 잔여 세력의 정보를 활용해 공동 TF 안건의 결함을 공격할 준비를 한다. 시혁은 두 방향의 압박 사이에 놓인다.",
        "solution": "시혁은 두 가지를 동시에 움직인다. 첫째, 이상무에게 말한다. '보고서에 유통 TF의 데이터 분석 근거를 별첨으로 넣으면 보고 신뢰도가 올라갑니다. 별첨 작성자란에 제 이름을 넣겠습니다.' 이상무는 수락한다 — 별첨 정도는 양보할 수 있다. 둘째, 시혁은 MD사업부 물류 데이터를 미리 확보해서 통합안에 반영한다. 정태호가 문제를 제기하기 전에 결함을 메운다.",
        "reward": "그룹 경영회의 보고서에 별첨 작성자로 시혁의 이름이 올라간다. 각주보다 한 단계 위다. 동시에 정태호의 공격 루트를 미리 차단했다. 하지만 이상무가 발표한다는 사실은 변하지 않았다. 시혁은 아직 그룹 경영회의에서 직접 말하는 사람이 아니다."
    },
    "stakes": "이상무가 공을 독식하면 공동 TF는 이상무의 프로젝트가 되고 시혁은 실무자로 고정된다. 정태호의 공격이 성공하면 공동 TF 자체가 흔들린다.",
    "power_shift": {
        "protagonist": "별첨 작성자로 이름 상승. 정태호 공격 루트 사전 차단.",
        "antagonist": "이상무는 발표권을 유지. 정태호의 공격은 실행 전 무력화."
    },
    "relationship_delta": [
        {"target": "이상무(그룹 전략실)", "before": "공동 TF를 수락한 파트너. 분기 보고 조건.", "after": "발표는 자기가 하되 별첨 이름은 시혁에게 양보한 상급 파트너"},
        {"target": "정태호(경영지원실 팀장)", "before": "TF 회의에서 반론 지원 실패. 관찰자 위치로 밀려남.", "after": "장현태 잔여 세력과 접촉. 공동 TF 공격 준비 중이었으나 사전 차단됨."}
    ],
    "foreshadow": [
        "정태호와 장현태 잔여 세력의 결합은 장현태 최종전의 전초전.",
        "이상무가 발표권을 쥐고 있는 한, 시혁은 그룹 경영회의에서 직접 목소리를 내지 못한다. 이 구조를 바꿀 기회가 필요하다."
    ],
    "callback": [
        "각주에서 별첨 작성자로 — 시혁의 이름이 한 단계씩 올라가는 패턴.",
        "정태호의 반감이 장현태 잔여 세력과 결합하기 시작 — 유통 내부의 적이 그룹 레벨로 확장."
    ],
    "emotional_beat": {"type": "tension", "intensity": 7},
    "tension_level": 8,
    "pov_character": "한시혁",
    "location": {"place": "이상무 집무실 / 한일유통 TF룸", "type": "그룹 본관 / 본사"},
    "time_span": {"duration": "5일", "in_story_time": "2026년 3월 중순"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 공동 TF 첫 안건 합의 + 계열사 간 판 설계자 인식 + 한일식품 협력 확보",
        "capital_after": "Lv6 TF 실권 + 그룹 경영회의 별첨 작성자 + 정태호 공격 사전 차단 + MD 데이터 통합 완료",
        "capital_delta": "별첨 이름 상승 (소득) + 정태호 공격 차단 (방어) + 이상무 발표 독점 (비용)",
        "profit_loss": "이름은 올라갔지만 발표는 아직 이상무가 한다.",
        "method": "별첨 작성자란 확보 + MD 데이터 사전 반영으로 공격 루트 차단.",
        "investment_type": "위치 상승 + 방어",
        "deal_type": "별첨 이름 협상 + 데이터 결함 사전 보강",
        "leverage_used": ["별첨이 보고 신뢰도를 높인다는 논리", "윤재영의 정보 통로", "MD 물류 데이터 접근 능력"],
        "opponent": {"name": "이상무 (발표 독점) / 정태호 (공동 TF 공격)", "type": "발표권 독점 + 관할 회복 시도", "weakness_exploited": "이상무는 데이터 품질에 의존하므로 별첨을 거부할 수 없었다. 정태호는 결함이 미리 메워지면 공격 명분을 잃는다."},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "그룹 경영회의 3일 전",
        "knowledge_used": "윤재영을 통한 정태호-장현태 접촉 정보 + MD 물류 데이터",
        "risk_level": "고위험 (두 방향 압박 동시 대응)",
        "business_sector": "그룹 전략 / 경영회의",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "이름을 위에 올리는 건 한 단계씩. 오늘은 별첨, 다음에는 발표.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "이상무의 발표 독점 의도와 정태호의 공격 준비를 동시에 감지"}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "두 방향의 위협은 동시에 처리한다. 한쪽만 막으면 다른 쪽이 뚫린다."},
    "block_no": 48
}

block_49 = {
    "block_id": "Block 49",
    "title": "조건표 협상",
    "content": {
        "context": "2026년 3월 하순. 그룹 경영회의에서 물류 외주 갱신 통합안이 원칙 승인된다. 이상무가 발표했고, 시혁은 질문 대응 보조로 참석했다. 하지만 승인 조건이 달렸다 — '계열사별 실행 조건을 확정하고 다음 분기까지 재보고.' 이것은 이상무가 아니라 시혁이 해야 할 일이다. 시혁은 한일식품과 한일건설의 물류 담당자를 각각 만나 실행 조건을 협상한다. 문제는 각 계열사가 자기에게 유리한 조건을 원한다는 것이다. 한일식품은 콜드체인 외주사 선택권 유지를 원하고, 한일건설은 자재 이송 우선순위를 요구한다. 시혁은 각 회사가 얻는 것과 잃는 체면을 정리해 새 조건표를 만든다.",
        "event_villain": "한일건설 물류 임원이 자재 이송 우선순위를 강하게 밀며 유통과 식품이 양보해야 한다고 주장한다. 이것이 관철되면 유통의 물류 일정이 건설에 종속된다.",
        "solution": "시혁은 조건표에 '분기별 우선순위 로테이션'을 넣는다. 고정 우선순위가 아니라 분기마다 물동량 기준으로 우선순위가 재배분되는 구조다. 어느 회사도 영구 우선을 갖지 못하지만, 물동량이 많은 분기에는 자동으로 우선권이 올라간다. 건설 임원이 처음에 반발하지만, 자기 물동량이 많은 3분기에는 사실상 우선이라는 계산을 보여주자 수용한다.",
        "reward": "계열사 3사의 실행 조건 합의. 시혁이 만든 조건표가 각 계열사의 이해관계를 조율하는 기준 문서가 됐다. 이제 사람들은 시혁을 보고서 잘 쓰는 사람이 아니라 '조건표를 짜는 사람', 즉 판의 규칙을 설계하는 사람으로 본다."
    },
    "stakes": "실행 조건이 합의되지 않으면 원칙 승인이 무효가 된다. 공동 TF의 첫 실행 성과가 사라진다.",
    "power_shift": {
        "protagonist": "계열사 3사 실행 조건 합의. 판의 규칙 설계자로 인식 확정.",
        "antagonist": "한일건설 물류 임원의 우선순위 요구가 로테이션 구조로 해소됨."
    },
    "relationship_delta": [
        {"target": "한일건설 물류 임원", "before": "신규 — 우선순위를 강하게 요구하는 상대", "after": "로테이션 구조에 동의. 시혁의 설계 능력을 인정."},
        {"target": "한일식품 물류 부장", "before": "시혁의 분리안에 동의. 전문성을 인정하기 시작.", "after": "실행 조건에서도 시혁의 설계를 수용. 협력 관계 심화."}
    ],
    "foreshadow": [
        "조건표 설계 역량은 장현태 최종전과 라인 선택 협상에서 핵심 무기로 재사용된다.",
        "'판의 규칙을 설계하는 사람'이라는 인식은 최종 아크에서 시혁이 라인을 선택할 때의 기반."
    ],
    "callback": [
        "공동 TF 첫 안건(물류 외주 갱신 통합)이 실행 조건 합의까지 도달. 킥오프에서 합의까지 한 사이클 완성.",
        "반론을 예측하고 대안을 미리 설계하는 패턴이 로테이션 구조로 반복 적용."
    ],
    "emotional_beat": {"type": "mastery", "intensity": 8},
    "tension_level": 6,
    "pov_character": "한시혁",
    "location": {"place": "한일식품 본사 회의실 / 한일건설 사옥 미팅룸", "type": "계열사"},
    "time_span": {"duration": "1주", "in_story_time": "2026년 3월 하순"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 그룹 경영회의 별첨 작성자 + 정태호 공격 사전 차단 + MD 데이터 통합 완료",
        "capital_after": "Lv6 TF 실권 + 계열사 3사 실행 조건 합의 + 판 규칙 설계자 인식 + 그룹 레벨 실행 성과",
        "capital_delta": "실행 조건 합의 (소득) + 설계자 인식 확정 (소득)",
        "profit_loss": "공동 TF의 첫 실행 사이클 완성. 그룹 레벨 성과 1건.",
        "method": "분기별 우선순위 로테이션 구조로 고정 우선 요구를 해소.",
        "investment_type": "다자 협상",
        "deal_type": "다자 조건표 합의",
        "leverage_used": ["물동량 기반 우선순위 로테이션 설계", "각 계열사의 분기별 물동량 데이터", "이미 합의된 원칙 승인"],
        "opponent": {"name": "한일건설 물류 임원", "type": "우선순위 고정 요구", "weakness_exploited": "건설의 물동량이 3분기에 집중되므로 로테이션 구조에서도 사실상 우선을 확보할 수 있다는 점"},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "다음 분기 재보고까지 2개월",
        "knowledge_used": "계열사 3사의 분기별 물동량 패턴 + 각 임원의 우선순위",
        "risk_level": "중위험 (합의 실패 시 원칙 승인 무효)",
        "business_sector": "그룹 물류 / 계열사 협업",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "고정 요구는 로테이션으로 해소한다. 모두에게 돌아가는 구조가 고정 우선보다 강하다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "건설 임원의 반발이 진심인지 협상 포지션인지 읽음 — 진심이었지만 양보 가능한 라인이 보였다."}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "모두가 돌아가며 이기는 구조를 설계한다. 누군가 영구히 지는 판은 오래 못 간다."},
    "block_no": 49
}

block_50 = {
    "block_id": "Block 50",
    "title": "그룹의 사원",
    "content": {
        "context": "2026년 4월 초. 공동 TF의 물류 외주 갱신 통합이 실행에 들어간다. 첫 통합 계약 협상 결과 — 연간 물류비 6.2% 절감 확정. 이 숫자가 그룹 경영회의에 재보고된다. 이번에는 이상무가 시혁에게 말한다. '이번 보고는 같이 서자.' 시혁은 처음으로 그룹 경영회의에서 직접 발표한다. 물류 비교표, 조건표, 실행 결과 수치를 그룹 언어로 설명한다. 그룹 부회장이 묻는다. '이게 한일유통 경영기획 사원이 만든 건가?' 이상무가 답한다. '네, 공동 TF의 유통 측 실무 리더입니다.'",
        "event_villain": "해당 없음. 보상 블록.",
        "solution": "시혁은 그룹 경영회의에서 물류 비교표를 설명하면서 한일유통 사원이 아닌 그룹 레벨 플레이어로 처음 인정받는다. 유통의 물류 재설계에서 시작한 역량이 그룹 차원 성과로 확대됐다.",
        "reward": "그룹 경영회의 직접 발표 완료. 부회장이 시혁의 이름을 들었다. 계열사 3사 물류 담당자가 시혁을 공동 TF의 실질 리더로 인정한다. 한일유통 안의 사원에서 그룹 레벨 플레이어로 체급이 바뀌는 중간 승리. Lv6 TF 실권 확보."
    },
    "stakes": "낮음. 보상 블록. 하지만 장현태는 아직 살아 있고, 시혁의 그룹 레벨 부상은 장현태에게도 들렸다.",
    "power_shift": {
        "protagonist": "그룹 경영회의 직접 발표. 부회장 인지. 그룹 레벨 플레이어로 전환.",
        "antagonist": "해당 없음. 장현태는 다음 아크에서 본격 등장."
    },
    "relationship_delta": [
        {"target": "이상무(그룹 전략실)", "before": "발표는 자기가 하되 별첨 이름은 시혁에게 양보한 상급 파트너", "after": "시혁과 함께 발표. 시혁의 역량을 공식적으로 인정한 파트너."},
        {"target": "그룹 부회장", "before": "신규 — 시혁의 존재를 모름", "after": "그룹 경영회의에서 시혁의 이름을 처음 들은 최고위 의사결정자"}
    ],
    "foreshadow": [
        "부회장이 시혁의 이름을 들었다는 것은 최종 아크에서 라인 선택 협상의 기반이 된다.",
        "그룹 레벨 성과는 장현태에게도 전해진다. 장현태는 시혁이 유통 안에 머물 때보다 더 위험한 존재가 됐다는 것을 인지한다."
    ],
    "callback": [
        "각주→별첨 작성자→직접 발표. 시혁의 이름이 한 단계씩 올라가는 패턴이 완성.",
        "그룹 언어 학습(브리핑 실패→윤재영 학습→비교 프레임 결합)이 직접 발표로 결실."
    ],
    "emotional_beat": {"type": "achievement", "intensity": 9},
    "tension_level": 3,
    "pov_character": "한시혁",
    "location": {"place": "한일그룹 본관 경영회의실", "type": "그룹 본관"},
    "time_span": {"duration": "1일", "in_story_time": "2026년 4월 초"},
    "genre_ext": {
        "type": "investment",
        "capital_before": "Lv6 TF 실권 + 계열사 3사 실행 조건 합의 + 판 규칙 설계자 인식 + 그룹 레벨 실행 성과",
        "capital_after": "Lv6 TF 실권 확보 + 그룹 경영회의 직접 발표 경험 + 부회장 인지 + 그룹 레벨 플레이어 전환",
        "capital_delta": "그룹 경영회의 발표 (소득) + 부회장 인지 (소득) + 그룹 레벨 전환 (소득)",
        "profit_loss": "전면 소득. 체급 상승 확정.",
        "method": "해당 없음 — 보상 블록. 이전 블록들의 축적이 결실.",
        "investment_type": "보상 확정",
        "deal_type": "그룹 경영회의 보고",
        "leverage_used": ["물류 비교표 + 조건표 + 실행 결과 수치", "이상무의 공동 발표 제안"],
        "opponent": {"name": "해당 없음", "type": "보상 블록", "weakness_exploited": "해당 없음"},
        "historical_event": {"name": None, "year": None, "how_exploited": None},
        "time_pressure": "해당 없음",
        "knowledge_used": "그룹 비교 프레임 + 실행 결과 수치",
        "risk_level": "무위험 (보상 블록)",
        "business_sector": "그룹 전략 / 경영회의",
        "section_rotation": "ARC-05 본사를 넘어서",
        "success_pattern": "한일유통 사원에서 그룹 레벨 플레이어로. 판을 설계하는 사람은 어디서든 인정받는다.",
        "special_ability": {"has_ability": True, "ability_type": "감각", "ability_name": "조직 역학 조감", "ability_source": "건강검진 이후 발현 (원인 불명)", "ability_used_for": "이 블록에서 감각은 보조적. 결과는 역량과 구조로 만들었다."}
    },
    "regression_ext": {"is_regressor": False, "regression_type": None, "execution_doctrine": "판을 설계하는 사람은 판의 크기가 바뀌어도 설계한다."},
    "block_no": 50
}

def main():
    with open(TR_PATH, 'r', encoding='utf-8') as f:
        existing = json.load(f)
    assert len(existing) == 41, f"Expected 41 blocks, got {len(existing)}"

    new_blocks = [block_42, block_43, block_44, block_45, block_46, block_47, block_48, block_49, block_50]

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

    combined = existing + new_blocks
    with open(TR_PATH, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(combined)} blocks to {TR_PATH}")
    print(f"New blocks added: {[b['block_no'] for b in new_blocks]}")

if __name__ == "__main__":
    main()
