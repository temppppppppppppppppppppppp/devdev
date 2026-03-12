# 대체역사물 JSON 생산 하네스 v1

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-10
> 장르 코드: `alt_history`
> 근거: `treatment-production-harness-v2.md` + `bi-production-harness-v1.md` + `alt_history_guard.py` 장르 규칙
> 목적: **대체역사물(조선 배경 회귀/빙의물) 전용 JSON 스키마와 생산 규칙을 고정**
> 선행 문서: `SSOT_blockguide-integrated-order.md`

---

## 0. 이 문서가 존재하는 이유

투자물·방산물·AI물은 "자본(capital)"이 핵심 수치다.
대체역사물은 **관직(court_rank)·당파 영향력(faction_influence)·왕의 신임(royal_trust)**이 그 역할을 대체한다.

`treatment-production-harness-v2.md`의 범용 스키마를 그대로 쓰면:

- `capital_before/after`가 의미 없는 숫자가 됨
- `genre_ext` 투자 필드가 조선 배경에 오염
- `leverage_used`가 금융 용어로 채워져 시대고증 위반

이 문서는 대체역사물에서만 쓰는 **JSON 필드 재정의·추가·금지 목록**을 확정한다.

---

## 1. 장르 핵심 전제

### 1.1 권력 곡선 = 관직 승진 곡선

투자물의 자본 곡선은 대체역사물에서 **권력 곡선**으로 치환된다.

| 투자물 개념 | 대체역사물 대응 개념 | 비고 |
|------------|-------------------|----|
| `capital_before` | `rank_before` (직전 관직/품계) | 예: "종6품 사헌부 감찰" |
| `capital_after` | `rank_after` (이번 Arc 말 관직/품계) | 예: "정4품 사간원 사간" |
| `capital_target` | `power_target` (Arc 목표 권한) | 예: "병조 참의 임명권 확보" |
| `deal_type` | `political_action` (정치 행동 유형) | 상소/탄핵/경연/혼인동맹 등 |
| `leverage_used` | `faction_leverage` (당파/인맥 지렛대) | 노론/소론/남인/서인 등 |
| `items_acquired` | `powers_acquired` (획득한 권한/지위) | 과거급제/관직/밀지 등 |

### 1.2 서사 동력

대체역사물 주인공의 자기중심성은 **권력 독점**으로 구현된다:

- 미래 역사 지식(회귀) 또는 현대 지식(빙의)을 활용
- 당파 대립의 균열을 먼저 읽고 명분과 실리를 동시에 취함
- 관직·학문·기술 도입으로 왕의 신임과 조정 내 실권을 확장
- 호구 금지: 의리·체면·충성심으로 손해를 보면 반드시 보상 설계가 있어야 함

---

## 2. Phase 0 JSON 스키마 (대체역사물 전용)

```json
{
  "project": {
    "work_id": "alt_history_{작품식별자}",
    "title_ko": "한국어 작품명",
    "title_en": "English title",
    "format": "조선 대체역사 회귀물",
    "logline": "한 줄 요약 (회귀/빙의 설정 + 핵심 목표 명시)",
    "core_premise": "주인공이 무엇을 무기로 어떻게 조정 실권을 장악하는가",
    "target_audience": "삶에 찌든 30405060 남성 독자",
    "era_setting": "조선 {왕대} 연간 ({시작연도}~{종료연도})",
    "alt_history_type": "회귀 | 빙의 | 환생 | 타임슬립",
    "divergence_point": "역사 분기점 — 실제 역사와 어떤 사건부터 달라지는가"
  },
  "setting": {
    "political_background": "당시 조정 당파 구도와 왕의 성향 요약",
    "group_background": "주인공이 속하거나 장악할 가문/관청/당파 배경",
    "execution_doctrine": "주인공이 권력을 확장하는 핵심 전략 한 문장",
    "starter_position": {
      "name": "초기 관직 또는 신분",
      "social_class": "양반 | 중인 | 상민 | 천민",
      "court_rank": "초기 품계 (예: 종9품, 무품)",
      "faction": "소속 당파 (예: 소론, 남인, 무당파)",
      "assets": ["보유 자산 목록 — 관계, 정보, 학문, 기술 등"],
      "liabilities": ["초기 약점 목록 — 누명, 부채, 당파 배척 등"]
    }
  },
  "protagonist": {
    "name": "주인공 이름",
    "age_at_start": 0,
    "previous_life": "전생 직위 또는 최후 (회귀물일 때)",
    "public_image": "표면상 평판",
    "true_strength": "미래/현대 지식 + 장악하는 핵심 능력",
    "true_weakness": ["약점 목록"],
    "initial_goal": "Arc 1 목표 (관직 또는 명분 확보)",
    "mid_goal": "Arc 4~5 수준 권력 목표",
    "final_goal": "Arc 7 수준 최종 실권 목표"
  },
  "phase0_design": {
    "arcs": [
      {
        "arc_id": "ARC-01",
        "title": "Arc 제목",
        "block_range": "1-10",
        "time_window": "{왕 재위 N년} {월}~{월}",
        "power_target": {
          "start": "종9품 예문관 검열",
          "end": "정6품 사헌부 지평",
          "summary": "권력 목표 한 줄 서술 (rank_before -> rank_after)"
        },
        "front_sectors": ["주력 정치 행동 유형: 상소, 경연, 탄핵 등"],
        "support_sectors": ["보조 전략: 혼인동맹, 학파 결집 등"],
        "main_opponents": ["주요 적대 NPC 이름"],
        "new_npcs": ["이 Arc에서 처음 등장하는 NPC 이름"],
        "historical_event": "이 Arc에서 활용하는 실제 또는 대체 역사 사건",
        "emotion_curve": ["굴욕", "포착", "거래", "역전"],
        "foreshadow": "이 Arc에서 심는 장기 복선",
        "callback": "이전 Arc에서 회수하는 복선 (Arc 1이면 null)",
        "faction_shifts": "당파 세력 변화 요약"
      }
    ],
    "npc_timeline": [
      {
        "name": "NPC 이름",
        "role": "역할",
        "faction": "당파",
        "court_rank": "초기 품계 (예: 정2품 좌의정)",
        "arc_range": "등장 Arc 범위",
        "rank_change": "Arc 종료 후 관직 변화 (없으면 null)",
        "fate": "Arc 종료 후 운명 (생존/실각/사망/동맹 전환)"
      }
    ],
    "power_curve": [
      {
        "arc_id": "ARC-01",
        "rank_start": "종9품",
        "rank_end": "정6품",
        "faction_influence": "소론 내 입지 상승",
        "royal_trust": "왕의 신임도 (낮음/보통/높음/절대적)"
      }
    ],
    "long_term_foreshadow": [
      {
        "block_planted": 0,
        "block_resolved": 0,
        "content": "복선 내용"
      }
    ],
    "alt_history_divergence_map": [
      {
        "arc_id": "ARC-01",
        "real_history": "실제 역사 사건",
        "alt_outcome": "대체역사에서 달라진 결과",
        "butterfly_effect": "이후 파급 효과"
      }
    ]
  }
}
```

---

## 3. TR 블록 스키마 (대체역사물 전용)

### 3.1 블록 기본 구조

투자물 블록과 **다른 필드만** 명시한다. 나머지는 `treatment-production-harness-v2.md` §4 기준을 따른다.

```json
{
  "block_id": 1,
  "title": "블록 제목",
  "arc": "ARC-01",
  "content": {
    "context": "이전 화 종료 상태 한 줄 요약",
    "conflict": "이번 화 핵심 갈등 (정치적 대립/탄핵/역모 등)",
    "solution": "주인공의 해결 전략 (명분 + 실리 구조)",
    "result": "이번 화 종료 상태"
  },
  "state": {
    "rank_before": "이번 블록 시작 관직/품계",
    "rank_after": "이번 블록 종료 관직/품계",
    "faction_before": "이번 블록 시작 당파 입지",
    "faction_after": "이번 블록 종료 당파 입지",
    "royal_trust_before": "왕의 신임도 시작",
    "royal_trust_after": "왕의 신임도 종료",
    "key_stat_change": "핵심 수치 변화 (관직품계 N단계 승진 등)"
  },
  "genre_ext": {
    "political_action": "상소 | 탄핵 | 경연 | 혼인동맹 | 기술도입 | 군사행동 | 외교 | 정보조작",
    "faction_leverage": ["사용한 당파/인맥 지렛대"],
    "historical_hook": "연계된 역사 사건 또는 인물",
    "powers_acquired": ["이번 블록에서 획득한 권한/지위/정보"],
    "powers_lost": ["이번 블록에서 잃은 권한/지위/정보"],
    "modern_knowledge_used": "사용한 미래/현대 지식 (없으면 null)",
    "tech_introduced": "도입한 기술 또는 문물 (없으면 null)"
  },
  "npcs": {
    "before": [
      {
        "name": "NPC 이름",
        "role": "역할",
        "faction": "당파",
        "court_rank": "품계",
        "relationship": "관계 (동맹/중립/적대)",
        "attitude": "태도"
      }
    ],
    "after": [
      {
        "name": "NPC 이름",
        "role": "역할",
        "faction": "당파",
        "court_rank": "품계",
        "relationship": "관계 (변화 명시)",
        "attitude": "태도 (변화 명시)"
      }
    ],
    "delta": "이번 블록에서 바뀐 관계 한 줄 요약"
  },
  "foreshadow": "이번 블록에서 심는 복선 (없으면 null)",
  "callback": "이번 블록에서 회수하는 복선 (없으면 null)",
  "emotional_beat": "이번 블록 감정 기조",
  "duration": "이번 화 시간 경과 (예: 3일)",
  "location": "주요 장소 (예: 사헌부, 경복궁 편전, 한양 남촌 주막)"
}
```

### 3.2 `political_action` 허용값 목록

| 값 | 설명 | 조선 관청/제도 |
|----|------|-------------|
| `상소` | 왕에게 글로 호소 | 사헌부·사간원·홍문관 언관 |
| `탄핵` | 관원 비위 고발 | 사헌부 대사헌·지평·감찰 |
| `경연` | 왕과 학문 토론 | 경연청·홍문관 |
| `혼인동맹` | 혼인으로 당파 결합 | 가문간 정략 |
| `기술도입` | 새 기술·문물 채택 | 공조·호조·군기시 |
| `군사행동` | 반란 진압·전쟁 | 병조·비변사 |
| `외교` | 청·일본·서양과 교섭 | 예조·승문원·역관 |
| `정보조작` | 첩보·유언비어·무고 조작 | 의금부·금부도사 |
| `과거_급제` | 문과·무과 응시 합격 | 예조·성균관 |
| `암행` | 어사·밀정 활동 | 암행어사·내금위 |

### 3.3 `faction_leverage` 허용값 예시

- `노론_핵심`: 노론 당파 주류 지지
- `소론_잔존`: 소론 잔류세력 연대
- `남인_학맥`: 남인 학문 계보 활용
- `서얼_연대`: 서얼 출신 동맹
- `무당파_실무`: 당파 초월 실무 관료층
- `왕실_외척`: 왕비 가문 인맥
- `내수사_재원`: 왕실 재원 접근

---

## 4. BI 스키마 추가 필드 (대체역사물 전용)

`bi-production-harness-v1.md`의 기본 BI 스키마에 아래 섹션을 추가한다.

```json
{
  "AltHistoryWorld": {
    "era": "조선 {왕대} 연간",
    "alt_divergence_point": "역사 분기점 설명",
    "court_factions": {
      "노론": {"strength": "강성|중간|약세", "key_figures": ["인물명"]},
      "소론": {"strength": "강성|중간|약세", "key_figures": ["인물명"]},
      "남인": {"strength": "강성|중간|약세", "key_figures": ["인물명"]}
    },
    "technology_level": "시대 기술 수준 설명",
    "modern_knowledge_catalogue": [
      {
        "category": "농업|군사|의학|건축|상업|재정",
        "knowledge": "도입할 지식 내용",
        "implementation_arc": "ARC-0N",
        "obstacles": "도입 장벽"
      }
    ]
  },
  "PowerHUD": {
    "Protagonist": {
      "actual_truth": {
        "name": "주인공 이름",
        "current_rank": "현재 관직/품계",
        "faction": "현재 소속 당파",
        "royal_trust": "왕의 신임도"
      }
    },
    "power_history": [
      {
        "arc_id": "ARC-01",
        "rank_start": "종9품",
        "rank_end": "정6품",
        "key_power_gained": "획득한 핵심 권한",
        "key_power_lost": "잃은 권한 (없으면 null)"
      }
    ]
  }
}
```

---

## 5. 절대 금지 규칙 (대체역사물 고유)

### 5.1 시대 오염 금지

아래 개념은 TR 블록·BI 어디에도 등장해서는 안 된다.

- 현대 기술 용어: 스마트폰, 인터넷, AI, 자동차, 엘리베이터 등
- 헌터물 용어: 마나, 스킬, 던전, 레벨업, 각성, 내공, 검기
- 투자물 용어: 주식, 펀드, 채권, 레버리지, ROI, IRR
- 현대식 조직명: 팀장, 본부장, CEO, CFO, 스타트업

### 5.2 신분 제약 위반 금지

| 신분 | 절대 불가 행동 |
|------|--------------|
| 천민 | 과거 응시, 관직 임명, 조정 참석 |
| 상민 | 조정 발언, 왕 알현, 양반 행세 |
| 중인 | 문과 급제, 정승 임명, 종묘 제사 |
| 유배 중 | 한양 귀환, 관직 복귀, 조정 참석 |

위반 시 **왕명·특사·서얼허통 등 개연성 있는 근거를 반드시 명시**해야 한다.

### 5.3 관직 위계 비약 금지

> 당상관 기준: **정3품 이상** (정3품 당상관~정1품). 정3품 당하관·종3품 이하는 당하관.
> `alt_history_guard.py` `_court_rank_hierarchy` 기준 18단계: 종9품 → 정9품 → … → 정1품

- 종9품 → 정3품(당상관) 1화 만에 승진 금지
- 무품(유생/서얼) → 당상관 직행 금지 (최소 5블록 이상 단계적 승진)
- 왕이 기분으로 정1품 바로 임명 금지 (공적·명분·인사 절차 필요)
- `_activity_requirements` 기준 준수: 왕 독대는 정3품 이상, 군사 동원은 종2품 이상

---

## 6. 패턴 감지 규칙 (1세대 + 2세대 대체역사 특화)

### 6.1 1세대 패턴 (자동 탐지 대상)

| ID | 패턴 | 심각도 |
|----|------|--------|
| A | rank_before ≠ prev rank_after | P0 |
| B | NPC before 매 블록 리셋 (당파 정보 날아감) | P0 |
| C | 적대 NPC 단일 고정 70블록 동일 | P1 |
| D | emotional_beat 4종 수학적 순환 | P1 |
| E | political_action 5종 균등 분배 14회씩 | P1 |
| F | duration 전량 "3일" 고정 | P2 |
| G | solution 패턴 "상소로 해결" 반복 | P1 |
| H | death_flag/위기 유형 70블록 전량 동일 (예: "탄핵_누명"만 반복) | P1 |

### 6.2 2세대 패턴 (심층 감지 대상)

| ID | 패턴 | 심각도 |
|----|------|--------|
| I | 영문 혼용 (faction_leverage에 "political_ally_A") | P1 |
| J | 코드형 값 (political_action="action_type_01") | P2 |
| K | 10문장 로테이션 (당파명만 교체하며 순환) | P1 |
| L | faction_leverage 70블록 전량 동일 4항목 | P1 |
| M | alt_history_type="빙의"인데 modern_knowledge_used=null 70블록 전량 | P0 |
| N | foreshadow 지목 블록에서 callback 회수 없음 | P1 |
| O | NPC 당파 2명×10블록 before=after 동결 | P1 |
| P | location 10곳 10블록 주기 정확 순환 | P2 |

---

## 7. Python 교정 규칙 (Phase 2 자동화 대상)

범용 교정 (`treatment-production-harness-v2.md` §5) 외 대체역사물 전용 교정:

```python
# 주의: rank_before/after는 "정6품 사헌부 지평"처럼 품계+관청+직위 조합 문자열.
# 단순 != 비교 시 "정6품 지평" vs "정6품 사헌부 지평" 같은 부분 일치 미탐지 가능.
# 교정 전 공백 정규화(strip) 적용 권장.

# 1. rank 연속성 교정
if block["state"]["rank_before"].strip() != prev_block["state"]["rank_after"].strip():
    block["state"]["rank_before"] = prev_block["state"]["rank_after"]

# 2. NPC before 이월
if block["npcs"]["before"] != prev_block["npcs"]["after"]:
    block["npcs"]["before"] = prev_block["npcs"]["after"]

# 3. power_target 동기화 (phase0_design arc와 비교)
# arc의 power_target.end가 해당 arc 마지막 블록의 rank_after와 일치해야 함

# 4. modern_knowledge_used null 과다 탐지
# 회귀/빙의물인데 modern_knowledge_used=null이 10블록 연속이면 경고
```

---

## 8. 검증 체크리스트 (3-Pass 감리)

### PASS 1: 시대 정합성

- [ ] FORBIDDEN_TERMS 0건 (`alt_history_guard.py` 기준)
- [ ] 신분 제약 위반 0건
- [ ] 관직 위계 비약 0건
- [ ] 아라비아 숫자 과다 사용 없음 (한자 수 표기 권장)
- [ ] 대화체 ~하오/~하시오/~이옵니다 일관성

### PASS 2: 서사 정합성

- [ ] rank_before/after 70블록 연속성
- [ ] NPC before/after 이월
- [ ] foreshadow→callback 연결 최소 3쌍
- [ ] alt_history_divergence_map 활용 흔적 (최소 1 Arc 1건)
- [ ] modern_knowledge_used 활용 패턴 자연스러운 간격
- [ ] `PowerHUD.Protagonist.actual_truth.name == CoreIdentity.protagonist` (BI 정합성)

### PASS 3: 품질 감리

- [ ] 1세대 패턴 A~H 0건
- [ ] 2세대 패턴 I~P 경고 3건 이하
- [ ] political_action 다양성: **Arc당 3종 이상, 전체 70블록 5종 이상**
- [ ] faction_leverage 다양성 (전체 3종 이상)
- [ ] location 다양성 (조정/지방/외국 균형)

---

## 9. 대체역사물 phase0_design 생성 빠른 시작

사용자가 `alt_history` work_id와 짧은 기획안을 주면 아래 순서를 따른다.

1. `era_setting`·`alt_history_type`·`divergence_point` 먼저 확정
2. `protagonist` 회귀/빙의 전생 + 현생 목표 확정
3. Arc 7개 권력 곡선 (rank 단계별 상승) 설계
4. `npc_timeline` 당파별 등장/퇴장 설계
5. `alt_history_divergence_map` 분기점→파급 효과 맵핑
6. `long_term_foreshadow` 복선 3쌍 이상 심기
7. Phase 0 JSON 저장 (UTF-8) 후 파싱 검증
8. 통과 후 `treatment-production-harness-v2.md`로 인계

---

## 10. 실전 규칙 한 줄 요약

**대체역사물 JSON은 "자본" 대신 "관직품계"를 추적한다.**
`rank_before/after`를 연속성 SSOT로 삼고, `political_action`과 `faction_leverage`를 당파 다양성 있게 교체한다.
시대 오염(`FORBIDDEN_TERMS`)과 신분 위계 위반은 즉시 재생성 사유다.
