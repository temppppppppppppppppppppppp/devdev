# 250화 웹소설 장기 기억 시스템 추천안

작성일: 2026-02-27  
대상: 글도비 Stage2/Stage4 기반 장기 연재(최대 250화)

---

## 1. 목표

250화 연재에서 다음 4가지를 안정적으로 보장하는 메모리 시스템을 제안한다.

1. 캐릭터/관계/세계관 설정의 장기 일관성
2. 수치(나이, 금액, 전투력, 기간) 누적 표류 방지
3. 복선-회수 추적 및 회상 오염 방지
4. 오류 발생 시 근거 화수까지 역추적 가능한 운영성

---

## 2. 현재 상태 요약

현재 시스템은 이미 `VecMemory(hybrid) + FactLedger + WorldState + SC 슬롯` 구조를 갖고 있다.

- 강점: 최근화 연속성, 하이브리드 검색, 사망/아이템/스킬 계열 TruthGate
- 약점: 60화 이후 장기 설정, 범용 수치 추적, 원문 단위 증거 회수, 시간축 추적

즉, "검색 엔진"은 이미 충분히 좋고, "기억 모델(무엇을 구조화해 저장할지)"이 상대적으로 약하다.

---

## 3. 대안 비교

| 대안 | 설명 | 장기 품질(250화) | 구현 난이도 | 운영 리스크 |
|---|---|---:|---:|---:|
| A. 현행 미세 개선 | 기존 VecMemory 파라미터/프롬프트만 조정 | 중 | 낮음 | 중 |
| B. 하이브리드 메모리 계층화 | 정형 앵커 + 이벤트 로그 + 벡터/FTS + 검증 게이트 | 높음 | 중 | 낮음 |
| C. 그래프 DB 중심 재구축 | 별도 Graph/Vector 인프라로 전면 이관 | 높음 | 높음 | 중~높음 |

권장안: **B. 하이브리드 메모리 계층화**  
이유: 현재 코드 자산을 재사용하면서 250화 장기 기억의 핵심 갭을 가장 적은 리스크로 메운다.

---

## 4. 권장 아키텍처 (Hybrid Memory Stack for 250EP)

### L0. Canonical Constraints (정형 앵커, SSOT)

절대 변하면 안 되는 사실을 구조화 저장한다.

- 캐릭터 고정 속성: 나이, 신체, 출신, 학력, 최초 직업/지위
- 세계관 절대 법칙: 마법 제약, 시스템 룰, 금기
- 수치 팩트: 금액, 레벨, 기간, 재고, 나이
- 관계 스냅샷: 관계 타입, 신뢰도, 마지막 변경 화수
- 타임라인: 작중 날짜/시간 경과

역할: "모델이 잊어도 시스템이 강제로 다시 알려주는 기준점"

### L1. Episodic Event Log (화별 사건 로그)

화 단위 사건을 정규화해서 저장한다.

- 사건 주체/대상/행동/결과
- 원인-결과 링크(`cause_event_id`)
- 최초 등장 화수, 마지막 갱신 화수

역할: "줄거리 기억"과 "인과 추적"

### L2. Evidence Retrieval (원문 근거 회수)

기존 `VecMemory`를 유지하되, "요약" 중심에서 "요약 + 원문 발췌"로 확장한다.

- 검색: hybrid(dense + FTS)
- 결과: 화수, 요약, 키 엔티티, 원문 발췌(짧은 evidence window)
- 슬롯별 예산 상한 적용

역할: "왜 그렇게 판단했는지"를 화수 근거와 함께 제공

### L3. Rolling Narrative Summaries (압축 기억)

다음 3종 요약을 분리 보관한다.

- Arc 요약 (10~20화 단위)
- Volume 요약 (50화 단위)
- Series 요약 (전체)

역할: 긴 연재에서 컨텍스트 예산을 절약하면서도 큰 흐름 유지

### L4. Continuity Gate (생성 전/후 검증)

- 생성 전: Blueprint/Scene 계획이 L0 제약을 깨는지 검사
- 생성 후: 원고 결과를 다시 L0/L1과 비교해 위반 탐지
- 정책: `CRITICAL=차단`, `MAJOR=재시도`, `MINOR=경고`

역할: "기억을 조회"에서 끝내지 않고 "기억 위반을 제어"

---

## 5. 250화 기준 검색/주입 정책

### 기본 원칙

- 최근화 편향을 줄이고, 장기 제약 슬롯을 항상 강제 주입한다.
- 슬롯 우선순위는 "장기 불변 정보 > 미해결 복선 > 최근 장면" 순으로 둔다.

### 권장 슬롯 구성

1. 캐릭터 고정 속성
2. 세계관 법칙
3. 수치/자원 제약
4. 관계 변화 핵심 5건
5. 미회수 복선
6. 장기 인과 이벤트
7. 최근 3화 연결
8. 현재 Arc 전술 문맥

### 예산 가이드

- Stage4 mandatory context: 현재 상한 유지(예: 100k 문자)
- 장기 제약 슬롯(L0/L1)은 예산 선할당(고정)
- 최근 장면/분위기 슬롯은 가변 예산

핵심은 "중요 장기 기억을 잘라내지 않는 예산 정책"이다.

---

## 6. 데이터 모델 권장(최소 확장)

기존 SQLite 기반을 유지하면서 아래 엔터티를 추가/보강한다.

- `canonical_facts`
  - `fact_key`, `fact_type`, `value_json`, `first_ep`, `last_ep`, `confidence`
- `episode_events`
  - `event_id`, `ep_no`, `actors_json`, `action`, `outcome`, `cause_event_id`
- `timeline_entries`
  - `ep_no`, `story_date`, `elapsed_days`, `time_note`
- `relation_edges`
  - `a`, `b`, `relation_type`, `strength`, `updated_ep`
- `foreshadow_open`
  - `hook_id`, `opened_ep`, `due_hint`, `status`
- `memory_evidence`
  - `ep_no`, `chunk_id`, `chunk_text`, `entities_json`

---

## 7. 현재 코드베이스 적용 포인트

다음 파일을 중심으로 단계적 확장을 권장한다.

- `modules/core/world_state.py`
  - 고정 속성(`known_attrs`) 자동 유입 강화
  - `timeline` 필드 및 장기 앵커 출력 강화
- `modules/core/fact_ledger.py`
  - 범용 `numerical_facts` 수집 경로 추가
- `modules/core/context_advisor.py`
  - 세계관 법칙/수치/복선 전용 슬롯 생성
- `modules/core/stage4_context_builder.py`
  - 슬롯 우선순위 + 장기 슬롯 예산 선할당
- `modules/core/vec_memory.py`
  - 검색 결과에 원문 발췌(evidence window) 포함
- `modules/domain/agents/director_continuity.py`
  - CRITICAL/MAJOR/MINOR 기준으로 게이트 정책 연결

---

## 8. 단계별 도입 로드맵

### Phase 1 (1주): L0 정형 앵커 강화

- NPC 고정 속성, 범용 수치, world_laws 슬롯 주입
- 즉시 효과: 캐릭터/수치 표류 급감

### Phase 2 (1~2주): L2 원문 근거 회수

- VecMemory 검색 응답에 원문 발췌 추가
- 즉시 효과: 회상 오염/왜곡 감소, 디버깅 용이

### Phase 3 (1주): 타임라인 + 복선 상태기

- timeline/foreshadow 상태를 mandatory context 상단 고정
- 즉시 효과: 날짜/기간 역행, 복선 유실 감소

### Phase 4 (1주): Continuity Gate 운영 고도화

- 위반 등급별 자동 액션(차단/재시도/경고)
- 즉시 효과: 품질 편차 축소, 운영 자동화

---

## 9. 성공 기준(KPI)

250화 운영 기준으로 다음 지표를 권장한다.

1. 장기 기억 회수율(50화+ 근거 검색) `Recall@K >= 0.85`
2. CRITICAL 모순률 `<= 1%` (화당)
3. MAJOR 모순률 `<= 5%` (화당)
4. 복선 회수 누락률 `<= 10%` (Arc 종료 시)
5. 시간축 오류율 `<= 2%` (월/계절/나이 불일치)

---

## 10. 결론

250화 장기 연재에서 필요한 것은 "더 큰 모델"보다 **기억의 계층화와 제약의 강제성**이다.  
현 코드베이스에는 이미 하이브리드 검색 기반이 있으므로, 본 권장안은 재구축 없이도 장기 기억 커버리지를 실질적으로 올릴 수 있다.

