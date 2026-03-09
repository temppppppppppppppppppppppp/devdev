# Treatment Batch Harness Prompt

이 프롬프트는 저지능 모델 기준으로 작성되었다. 절대로 한 번에 70블록을 만들지 마라.

## 작품 컨텍스트
- 제목: (미지정)
- 장르: (미지정)
- 주인공: (미지정)
- 로그라인: (미지정)

## 이번 배치
- 시작 블록: 4
- 종료 블록: 6
- 모드: flash

## 이번 배치 목표
- Block 4: Block 4
- Block 5: Block 5
- Block 6: Block 6

## 직전 3블록 요약
- Block 1: 벽돌 더미 속 미래 지도 | 자본 0억 -> 350억 | beat rebirth/9 | deal 전환사채(CB) 발행 | 장소 서울 중구 세림그룹 본관 28층 전략회의실
  reward: 세림그룹은 공식 투자 대신 윤도현 개인 책임 조건의 전환사채 인수를 승인하고, 프론티어 원 설립 안건이 통과된다. 시장에서는 재벌가 막내의 변덕으로 보지만, 윤도현은 이 자금이 곧 팬택 채권과 싸…
- Block 2: 팬택의 마지막 실험실 | 자본 350억 -> 290억 | beat pyrrhic_victory/6 | deal 부실 자산 인수 | 장소 김포 팬택 연구개발센터와 주거래은행 채권단 회의실
  reward: 프론티어 원은 팬택 관련 전환권과 채권 묶음을 선점하는 데 성공하지만, 연구소 유지를 위한 현금 투입 때문에 장부상 자본은 350억에서 290억으로 줄어든다. 대신 오세라는 윤도현이 회사를 뜯어먹…
- Block 3: 미니홈피의 심장을 사다 | 자본 290억 -> 430억 | beat alliance/7 | deal 우호적 M&A | 장소 서울 서초동 프론티어 원 임시 사무실과 싸이월드 협상 테이블
  reward: 싸이월드 측은 경영권 매각까지는 아니어도 모바일 전환권과 핵심 개발 조직을 묶은 우호적 인수 조건에 합의한다. 프론티어 원의 자본은 290억에서 430억으로 뛰는데, 이는 싸이월드의 사용자 데이터…

## NPC 추적표
| NPC | 마지막 블록 | 현재 관계 |
|---|---:|---|
| 한유리 싸이월드 서비스 총괄 | 3 | 주소록과 일촌 데이터를 모바일 운영 경험으로 확장하겠다는 비전에 설득돼 핵심 동맹으로 합류 |
| 차우진 CFO | 3 | 외부 투자자 재평가가 붙자 공개 반대에서 물러서고 실패 시 책임만 기다리는 냉정한 감시자로 변함 |
| 오세라 팬택 전략기획 임원 | 3 | 팬택 하드웨어와 싸이월드 플랫폼을 함께 설계하는 공동 전선의 핵심 파트너가 됨 |
| 정민석 구조조정실장 | 2 | 통신사 압박 문건까지 넘기며 실무 정보선으로 완전히 올라탐 |
| 윤재문 회장 | 1 | 처음으로 숫자와 일정표를 들고 온 후계 후보, 시험해볼 가치는 있는 카드 |

## OPEN 복선 원장
| # | 내용 | 심기 | 회수 예정 | 상태 |
|---|---|---:|---:|---|
| 1 | 팬택 연구소의 터치 UI 프로토타입이 Block 5에서 국산 앱마켓 시연용… | 2 | 5 | OPEN |
| 2 | 팬택과 싸이월드를 묶은 첫 홈 화면 시안이 Block 6에서 베타폰 공개의… | 3 | 6 | OPEN |
| 3 | 차우진이 실패 책임만 기다리겠다고 마음먹은 태도가 Block 7에서 내부 … | 3 | 7 | OPEN |

## 출력 순서
1. 사전 선언
2. JSON
3. 차이 행렬
4. 복선 원장 업데이트

## 사전 선언 항목
1. 직전 상태 인용: 직전 블록의 capital_after, emotional_beat, 관계 after를 인용하라.
2. 자본 계산: capital_before = 직전 capital_after. 이번 변화 근거와 계산식을 적어라.
3. 차별화 1줄: 직전 블록과 가장 크게 달라진 지점을 1문장으로 써라.

## 절대 금지
- 70블록 단일 출력 금지
- 한국어 대신 영문 템플릿 사용 금지
- `plan_01`, `type_1`, `_B01` 같은 코드형 값 금지
- callback을 `직전 블록의 성과가 발판` 한 문장으로 때우는 것 금지
- deal_type 3블록 이내 재등장 금지
- emotional_beat.type 2연속 동일 금지
- location 15블록 이내 재등장 금지
- `capital_before != 직전 capital_after` 금지
- `relationship_delta.before != 직전 after` 금지
- leverage_used 동일 세트 3회 반복 금지

## 배치 운영 규칙
배치는 3블록이며, JSON 뒤에 3블록 차이 행렬과 OPEN 복선 원장만 출력하라.

## JSON 스켈레톤
```json
[
  {
    "block_id": "Block 4",
    "title": "제목",
    "content": {
      "context": "상황과 배경",
      "event_villain": "적대 행동",
      "solution": "주인공 해결",
      "reward": "결과와 보상"
    },
    "stakes": "이번 블록 실패 시 손실",
    "power_shift": {
      "protagonist": "주인공 위상 변화",
      "antagonist": "적대자 위상 변화"
    },
    "relationship_delta": [
      {
        "target": "NPC 이름",
        "before": "직전 after 복사",
        "after": "이번 변화"
      }
    ],
    "foreshadow": [
      "향후 회수할 복선"
    ],
    "callback": [
      "이번 블록에서 회수한 복선"
    ],
    "emotional_beat": {
      "type": "resolve",
      "intensity": 7
    },
    "tension_level": 8,
    "pov_character": "주인공",
    "location": {
      "place": "장소",
      "type": "사업 거점"
    },
    "time_span": {
      "duration": "2주",
      "in_story_time": "2006년 1월"
    },
    "genre_ext": {
      "capital_before": "120억",
      "capital_after": "135억",
      "capital_delta": "+15억",
      "profit_loss": "15억 증가",
      "method": "한국어 서사 문장",
      "investment_type": "거래 유형 설명",
      "deal_type": "직전 2블록과 다른 딜 형태",
      "leverage_used": [
        "신규 레버리지 1",
        "신규 레버리지 2"
      ],
      "opponent": {
        "name": "적대자",
        "type": "경쟁 세력",
        "weakness_exploited": "한국어 약점 설명"
      },
      "historical_event": "이번 블록 사건명",
      "time_pressure": "시간 압박",
      "knowledge_used": "판단 근거",
      "risk_level": "중상",
      "business_sector": "섹터명",
      "section_rotation": "대단원 내 역할",
      "global_partner": {
        "name": "파트너",
        "cadence": "비정형",
        "objective": "목적"
      },
      "success_pattern": "한국어 결과 패턴"
    },
    "regression_ext": {
      "is_regressor": true,
      "regression_type": "빙의",
      "timeline_knowledge": {
        "info_used": "사용 정보",
        "accuracy": "상",
        "source": "출처"
      },
      "butterfly_effect": {
        "original_event": "원래 사건",
        "changed_event": "바뀐 사건",
        "ripple_effect": "파급"
      },
      "death_flag": {
        "avoided": "회피한 위기",
        "method": "회피 방법"
      },
      "regression_hint": {
        "slip_up": "의심을 부른 실수",
        "suspicion_from": "의심한 세력"
      },
      "future_prep": {
        "action": "다음 준비",
        "target_event": "다음 목표"
      },
      "single_heir_policy": "승계 정책",
      "incarnation_type": "빙의자",
      "execution_doctrine": "이번 블록 시점 전략 문장"
    }
  },
  {
    "block_id": "Block 5",
    "title": "제목",
    "content": {
      "context": "상황과 배경",
      "event_villain": "적대 행동",
      "solution": "주인공 해결",
      "reward": "결과와 보상"
    },
    "stakes": "이번 블록 실패 시 손실",
    "power_shift": {
      "protagonist": "주인공 위상 변화",
      "antagonist": "적대자 위상 변화"
    },
    "relationship_delta": [
      {
        "target": "NPC 이름",
        "before": "직전 after 복사",
        "after": "이번 변화"
      }
    ],
    "foreshadow": [
      "향후 회수할 복선"
    ],
    "callback": [
      "이번 블록에서 회수한 복선"
    ],
    "emotional_beat": {
      "type": "resolve",
      "intensity": 7
    },
    "tension_level": 8,
    "pov_character": "주인공",
    "location": {
      "place": "장소",
      "type": "사업 거점"
    },
    "time_span": {
      "duration": "2주",
      "in_story_time": "2006년 1월"
    },
    "genre_ext": {
      "capital_before": "120억",
      "capital_after": "135억",
      "capital_delta": "+15억",
      "profit_loss": "15억 증가",
      "method": "한국어 서사 문장",
      "investment_type": "거래 유형 설명",
      "deal_type": "직전 2블록과 다른 딜 형태",
      "leverage_used": [
        "신규 레버리지 1",
        "신규 레버리지 2"
      ],
      "opponent": {
        "name": "적대자",
        "type": "경쟁 세력",
        "weakness_exploited": "한국어 약점 설명"
      },
      "historical_event": "이번 블록 사건명",
      "time_pressure": "시간 압박",
      "knowledge_used": "판단 근거",
      "risk_level": "중상",
      "business_sector": "섹터명",
      "section_rotation": "대단원 내 역할",
      "global_partner": {
        "name": "파트너",
        "cadence": "비정형",
        "objective": "목적"
      },
      "success_pattern": "한국어 결과 패턴"
    },
    "regression_ext": {
      "is_regressor": true,
      "regression_type": "빙의",
      "timeline_knowledge": {
        "info_used": "사용 정보",
        "accuracy": "상",
        "source": "출처"
      },
      "butterfly_effect": {
        "original_event": "원래 사건",
        "changed_event": "바뀐 사건",
        "ripple_effect": "파급"
      },
      "death_flag": {
        "avoided": "회피한 위기",
        "method": "회피 방법"
      },
      "regression_hint": {
        "slip_up": "의심을 부른 실수",
        "suspicion_from": "의심한 세력"
      },
      "future_prep": {
        "action": "다음 준비",
        "target_event": "다음 목표"
      },
      "single_heir_policy": "승계 정책",
      "incarnation_type": "빙의자",
      "execution_doctrine": "이번 블록 시점 전략 문장"
    }
  },
  {
    "block_id": "Block 6",
    "title": "제목",
    "content": {
      "context": "상황과 배경",
      "event_villain": "적대 행동",
      "solution": "주인공 해결",
      "reward": "결과와 보상"
    },
    "stakes": "이번 블록 실패 시 손실",
    "power_shift": {
      "protagonist": "주인공 위상 변화",
      "antagonist": "적대자 위상 변화"
    },
    "relationship_delta": [
      {
        "target": "NPC 이름",
        "before": "직전 after 복사",
        "after": "이번 변화"
      }
    ],
    "foreshadow": [
      "향후 회수할 복선"
    ],
    "callback": [
      "이번 블록에서 회수한 복선"
    ],
    "emotional_beat": {
      "type": "resolve",
      "intensity": 7
    },
    "tension_level": 8,
    "pov_character": "주인공",
    "location": {
      "place": "장소",
      "type": "사업 거점"
    },
    "time_span": {
      "duration": "2주",
      "in_story_time": "2006년 1월"
    },
    "genre_ext": {
      "capital_before": "120억",
      "capital_after": "135억",
      "capital_delta": "+15억",
      "profit_loss": "15억 증가",
      "method": "한국어 서사 문장",
      "investment_type": "거래 유형 설명",
      "deal_type": "직전 2블록과 다른 딜 형태",
      "leverage_used": [
        "신규 레버리지 1",
        "신규 레버리지 2"
      ],
      "opponent": {
        "name": "적대자",
        "type": "경쟁 세력",
        "weakness_exploited": "한국어 약점 설명"
      },
      "historical_event": "이번 블록 사건명",
      "time_pressure": "시간 압박",
      "knowledge_used": "판단 근거",
      "risk_level": "중상",
      "business_sector": "섹터명",
      "section_rotation": "대단원 내 역할",
      "global_partner": {
        "name": "파트너",
        "cadence": "비정형",
        "objective": "목적"
      },
      "success_pattern": "한국어 결과 패턴"
    },
    "regression_ext": {
      "is_regressor": true,
      "regression_type": "빙의",
      "timeline_knowledge": {
        "info_used": "사용 정보",
        "accuracy": "상",
        "source": "출처"
      },
      "butterfly_effect": {
        "original_event": "원래 사건",
        "changed_event": "바뀐 사건",
        "ripple_effect": "파급"
      },
      "death_flag": {
        "avoided": "회피한 위기",
        "method": "회피 방법"
      },
      "regression_hint": {
        "slip_up": "의심을 부른 실수",
        "suspicion_from": "의심한 세력"
      },
      "future_prep": {
        "action": "다음 준비",
        "target_event": "다음 목표"
      },
      "single_heir_policy": "승계 정책",
      "incarnation_type": "빙의자",
      "execution_doctrine": "이번 블록 시점 전략 문장"
    }
  }
]
```

## 추가 지시
- title은 위 배치 목표의 title을 그대로 사용하라.
- roadmap 내용이 이미 존재하더라도 그대로 베끼지 말고, title만 고정점으로 사용하라.
- 모델이 확신이 없으면 빈칸 대신 보수적인 한국어 서사 문장을 작성하라.