# TF-29: 에이전트·디렉터 지능 강화 아이디어 조사

> 날짜: 2026-02-28
> 범위: 에이전트/디렉터 의사결정 품질 개선 아이디어 발굴 + 재검토
> 상태: **감리 5회 완료, 확정** (4-5차에서 대폭 하향 조정)

---

## 조사 방법

1. 3개 병렬 탐색: (1) 에이전트 아키텍처 (2) 프롬프트·피드백 패턴 (3) advisory 체인·메모리
2. 4개 검증 탐색: A-1~A-4, B-1~B-4 각각의 실제 코드 경로 정밀 추적
3. 초기 평가 대비 재검토 → 판정 수정 3건
4. 감리 3회: (1차) director.yaml·chief_writer.yaml·interview_round 원문 대조 (2차) director_ensemble 반환 구조·V75-B·adaptive threshold 원문 대조 (3차) satisfaction_tags 사용처·contradiction_check grep·open_review 경로 최종 확인 → 오류 1건 수정(B-3)

---

## A. 채택 권장 (ROI 높음)

### A-1. CW에게 디렉터 채점 가중치 공개

| 항목 | 내용 |
|------|------|
| **현재** | CW는 디렉터 채점 기준을 **전혀 모름** |
| **근거** | `director.yaml` L115-122에 `연속성 40% / 블루프린트 20% / 품질 20% / 길이 10% / 경고 10%` 명시. `chief_writer.yaml`에는 가중치 언급 0건. `chief_writer_context.py`에 `scoring_weights` 파라미터 없음 |
| **영향** | CW가 품질(문체)에만 집중하고 연속성(40%)을 경시 → REJECT 주원인이 연속성인데 재작성 시 문체만 수정 |
| **제안** | CW 프롬프트에 디렉터 채점 가중치 + 아크 위치별 엄격도 주입 |
| **복잡도** | **Low** — 프롬프트 텍스트 추가만 (코드 변경 최소) |

**재검토 결과**: `director_grading.py` L476-540 확인 — 아크 위치별 adaptive threshold가 있음:
- 아크 0-20% (도입): base -5점, 관대
- 아크 40-60% (전환): base +3점
- 아크 80%+ (클라이맥스): base +10점, 엄격
- 재시도 3+: base -10점

이 정보도 CW에게 전달하면 "지금 클라이맥스라 엄격 모드 → 연속성 최우선" 같은 맥락 인식 가능.

**판정: 채택 권장 (변경 없음)**

---

### A-2. 디렉터 구조화 데이터 CW 전달 (기존 데이터 활용)

| 항목 | 내용 |
|------|------|
| **현재** | 디렉터가 **이미** 구조화된 `contradiction_check` 반환 중이지만 **CW에게 전달 안 됨** |
| **근거** | `director.yaml` L360-371: `found_contradictions[{type, prev_fact, current_violation, severity, prev_episode}]` 구조 반환. 그러나 `stage4_interview_round.py` L1328-1334에서 `action_items`만 추출하고 `contradiction_check`와 `open_review`는 **폐기** |
| **영향** | CW가 "모순 2건" 텍스트만 받고, 어떤 유형(고유명사/수치/사망)인지·어느 화와 충돌하는지 구체 정보 유실 |
| **제안** | `contradiction_check.found_contradictions[]`를 CW director_feedback에 포함. `open_review`도 전달 |
| **복잡도** | **Low** — 이미 존재하는 데이터를 전달 경로에 추가만 |

**재검토 결과**: 초기 평가에서 "디렉터 응답 스키마 확장" 필요라고 했으나, 재검토 결과 **스키마 확장 불필요**. 데이터가 이미 존재하고 있으며 전달 경로만 연결하면 됨. 복잡도 Low-Medium → **Low**로 하향.

추가 발견:
- `contradiction_check`: `stage4_interview_round.py`에서 grep 결과 **참조 0건** — 디렉터 반환 후 완전 폐기 확인
- `open_review` (체크리스트 외 어색함/비약/톤급변/동기부재): `director_ensemble.py` L670-671에서 콘솔 출력(200자 절삭) + `stage4_interview_round.py` L1567에서 `previous_attempt` dict에 저장(300자 절삭)되지만 **CW에게 미전달**
- `score_breakdown` (항목별 점수): `director_ensemble.py` L687에서 반환하지만 CW에게 미전달

**판정: 채택 권장 (복잡도 하향 수정)**

---

### A-3. fix_scope 성공률 기반 지능화

| 항목 | 내용 |
|------|------|
| **현재** | 디렉터가 inplace/partial/full 판단 시 과거 성공률 참조 없음 |
| **근거** | `session_logger.py` L97-124: `log_decision()`에 `fix_scope` 필드 **없음**. 읽기 API 없음 (write-only). `stage4_interview_round.py` L1403: fix_scope는 `previous_attempt` dict에만 저장 |
| **영향** | 톤 문제에 inplace 반복 시도 → 실패 → 라운드 낭비 |
| **제안** | (1) fix_scope를 decisions.jsonl에 기록 (2) 읽기 API 구현 (3) 집계 → 디렉터 프롬프트 주입 |
| **복잡도** | **Medium-High** — 로깅 인프라 확장 필요 |

**재검토 결과**: 초기 평가 Medium에서 **Medium-High로 상향**. 이유:
1. SessionLogger에 읽기 API 자체가 없음 (현재 순수 append-only)
2. fix_scope가 log_decision() 스키마에 포함되지 않아 스키마 확장 필요
3. 프로젝트 간 데이터 축적 필요 (신규 프로젝트에서는 히스토리 0)

**판정: 채택 권장은 유지하나, A-1/A-2보다 후순위. 인프라 확장 선행 필요.**

---

### A-4. 3후보 동일 실패 감지 → 블루프린트 재생성 권고

| 항목 | 내용 |
|------|------|
| **현재** | V75-B에서 `logic_error_streak >= 2`일 때 블루프린트 재생성 **이미 존재** |
| **근거** | `stage4_orchestrator.py` L740-773: `_logic_error_streak >= 2 and _inplace_attempted` → `_regenerate_blueprint()` 호출. 그러나 **아크(전술서) 재생성은 없음**. 블루프린트만 재생성 |
| **영향** | 블루프린트가 아닌 아크 자체가 문제인 경우 → 블루프린트 재생성해도 반복 실패 |
| **제안** | "3후보 모두 동일 이슈 유형으로 REJECT" 패턴 감지 → "아크 문제 가능성" advisory 생성 |
| **복잡도** | **Medium** |

**재검토 결과**: 초기 평가에서 놓친 점 2가지:
1. **V75-B 메커니즘 이미 존재**: `_logic_error_streak` 카운팅 + 블루프린트 재생성. 단, 아크 레벨 피드백은 없음
2. **Stage4 → Stage2 피드백 경로 없음**: `three_phase_blueprint_generator.generate()`에 `external_feedback` 파라미터 존재(L66)하지만 Stage4에서 호출하는 경로 없음
3. **무한 루프 위험**: Stage4↔Stage2 왕복 시 termination 조건 필요

**판정: 채택 권장은 유지하나, 구현 시 "advisory 메시지 생성"까지만 (자동 Stage2 리슬라이스는 위험)**

---

## B. 검토 가치 있음 (ROI 중간)

### B-1. NPC 상태 타임라인 CW 주입

| 항목 | 내용 |
|------|------|
| **현재** | `npc_history` 테이블에 per-episode 상태 변화 기록. CW는 **현재 스냅샷만** 수신 |
| **근거** | `db_manager.py` L390-404: `npc_history(npc_name, episode_no, arc_no, field_name, old_value, new_value, change_source)`. `chief_writer_context.py`에 NPC 이력 조회 0건 |
| **컨텍스트 예산** | Stage4 Writer 예산 400K자 중 현재 ~35-40% 사용. NPC 타임라인 ~10K자 = 예산의 2.5% |
| **제안** | 등장 NPC의 최근 5화 상태 변화 타임라인을 CW 컨텍스트에 주입 |
| **복잡도** | **Low-Medium** |

**판정: 검토 가치 있음 (변경 없음)**

---

### B-2. 복선 회수 감사 (Seed Actualization)

| 항목 | 내용 |
|------|------|
| **현재** | `foreshadow` 테이블에 `resolved_ep` 컬럼 존재하지만 **자동 기록 안 됨** |
| **근거** | `db_manager.py` L519-531: `foreshadow(seed_id, status, planted_ep, resolved_ep)`. `resolved_ep`는 대부분 NULL. 복선 시스템이 **인메모리 중심**으로 DB와 동기화 불완전 |
| **제안** | 아크 경계에서 미회수 복선 목록 advisory 생성 → Analyst 주입 |
| **복잡도** | **Medium-High** (복선 시스템 DB 중심 전환 선행 필요) |

**재검토 결과**: 초기 평가 Medium에서 **Medium-High로 상향**. 복선 시스템이 인메모리 중심이라 DB 정합성부터 확보해야 함.

**판정: 검토 가치 있으나 선행 작업 필요 (후순위)**

---

### B-3. 감정 곡선 기반 페이싱 advisory

| 항목 | 내용 |
|------|------|
| **현재** | `episode_satisfaction_tags` 테이블 존재. `continuity_validator.py` 좌절 연속 체크 + `blueprint_ensemble.py` 만족도 추이 주입 |
| **근거** | `db_manager.py` L420-430: `(ep_num, primary_tag, satisfaction_score, protagonist_agency, frustration_flag)`. `get_recent_satisfaction_tags(before_ep, lookback=5)` API 존재. 현재 2곳에서 사용: (1) `continuity_validator.py` L1006 좌절 연속 체크 (2) `blueprint_ensemble.py` L519 블루프린트 생성 시 만족도 추이 컨텍스트 주입 |
| **제안** | Stage4 CW/디렉터에도 최근 N화 감정 패턴 주입 → "연속 비극 후 보상 권장" / "액션 과다 후 감정 에피소드 권장" advisory |
| **복잡도** | **Low** (데이터+API 모두 존재, 규칙 추가만) |

**재검토 결과**: 초기 평가 Medium에서 **Low로 하향**. 데이터와 쿼리 API가 이미 완비. 3차 감리에서 `blueprint_ensemble.py` L519 사용처 추가 확인 — Stage3에서는 이미 만족도 추이를 참조하나, **Stage4(CW/디렉터)에는 미주입**. 따라서 제안의 핵심은 "Stage4 레벨 주입"으로 범위 한정.

**판정: 검토 가치 있음 (복잡도 하향 수정)**

---

### B-4. CW 자기비평 논리 검증 항목 추가

| 항목 | 내용 |
|------|------|
| **현재** | 루브릭 4개 항목이 **문체만** 측정 (직접감정 밀도, 문장 시작 다양성, 대화 비율, 감각어) |
| **근거** | `chief_writer_quality.py` L367-459: 4개 subscores → 평균 1.0-4.0. `rubric >= 3.5`면 자기비평 스킵. 그러나 `_self_critique()`(별도 메서드)에서 **이미** HUD 일관성, 클리셰, 정당화 갭, NPC 관계 불일치를 검사 중 |
| **제안** | 루브릭에 "캐릭터 주요 결정의 동기 명시 여부" 항목 추가 |
| **복잡도** | **Medium** (LLM 기반 판단 필요, Python regex로 불가) |

**재검토 결과**: `_self_critique()`가 이미 논리적 이슈(HUD 불일치, 정당화 갭)를 체크하고 있음. 루브릭 자체는 문체 전용이지만, 루브릭 ≥ 3.5여도 구조적 이슈가 있으면 자기비평 진행됨 (L112-117). **기존 메커니즘이 부분적으로 커버 중**.

추가할 가치가 있는 것은 "캐릭터 동기 명시" 판단인데, 이것은 LLM 호출이 필요하므로 자기비평 라운드 내에서 처리하는 게 자연스러움.

**판정: 검토 가치 있으나 기존 _self_critique 확장으로 접근 (루브릭 자체 수정보다)**

---

## C. NO-GO (재검토 확정)

### C-1. StateTracker LLM 기반 추출 → NO-GO
- 정규식 → LLM 전환 시 NPC당 LLM 호출 필요. TruthGate(LM-A)가 이미 사후 검증 담당.
- 비용 대비 효과 없음.

### C-2. 앙상블 전략 적응형 선택 → NO-GO
- 3전략 fan-out이 컨텍스트 캐싱 효율의 핵심 (1캐시 + 3 cached_ask 패턴).
- 전략 수 줄이면 다양성 손실 + 캐시 구조 붕괴.

### C-3. VecMemory 전체 에피소드 리캡 API → NO-GO
- `prev_manuscripts_text`(30화)가 이미 디렉터에게 전달 중. 중복 투자.

### C-4. 관계 궤적 아키타입 마이닝 → 후순위
- 프로젝트당 NPC 쌍 수십 개 → 학습 데이터 부족. 패턴 인식 ROI 낮음.

### C-5. VoiceDriftAdvisor → 후순위
- LM-B(NpcDriftAdvisor)가 텍스트 레벨 표류 전반 감지. 음성만 분리하면 중복.

---

## 우선순위 종합 (5차 감리 후 확정)

| 순위 | ID | 아이디어 | ROI | 복잡도 | 판정 | 4-5차 감리 변경 |
|------|-----|---------|-----|--------|------|----------------|
| 1 | **A-2(부분)** | `open_review`(어색함/비약/톤급변/동기부재) CW 전달 | ★★☆ | Low | **채택** | contradiction_check는 REDUNDANT → open_review만 유효 |
| 2 | **A-4** | 동일 실패 패턴 → 블루프린트 문제 advisory | ★★☆ | Medium | **채택 가능** | 변경 없음 (유일하게 기존에 없는 기능) |
| 3 | **B-4** | CW 자기비평 동기 검증 | ★☆☆ | Medium | 검토 | 변경 없음 |
| — | **A-1** | CW에게 채점 가중치 공개 | ★☆☆ | Low | **MARGINAL** | DynamicPromptWeighter가 이미 동적 강조 수행 |
| — | **A-2(나머지)** | contradiction_check JSON CW 전달 | ★☆☆ | Low | **REDUNDANT** | _evidence_block이 이미 동일 정보 전달 |
| — | **B-1** | NPC 타임라인 CW 주입 | ★☆☆ | Low-Med | **REDUNDANT** | advisory 체인(LM-B/C/D)이 이미 디스틸 |
| — | **B-3** | 감정 곡선 페이싱 advisory | ★☆☆ | Low | **REDUNDANT** | emotional_beat + blueprint_ensemble이 이미 커버 |
| — | **A-3** | fix_scope 성공률 기반 지능화 | ★☆☆ | Med-High | 검토 (인프라 선행) | 변경 없음 |
| — | **B-2** | 복선 회수 감사 | ★☆☆ | Med-High | 검토 (DB 전환 선행) | 변경 없음 |
| — | C-1~5 | StateTracker LLM화 등 5건 | — | — | NO-GO/후순위 | 변경 없음 |

### 5차 감리 핵심 발견

**기존 시스템이 예상보다 훨씬 잘 설계되어 있음:**

1. **DynamicPromptWeighter** (`dynamic_prompt_weighting.py`): 최근 50건 REJECT 사유에서 카테고리(연속성/아이템/관계/페이싱 등 10종)별 실패 빈도를 분석하고, 상위 3개 카테고리의 강조 지시어를 CW 프롬프트에 동적 주입. **A-1(정적 가중치)보다 우수한 메커니즘.**

2. **_evidence_block** (L1314-1326): TruthGate 경고와 structured_violations를 `[CRITICAL/MAJOR/MINOR]` 태그 + 텍스트로 이미 CW에게 전달. **A-2(contradiction_check JSON)는 동일 정보의 이중 인코딩.**

3. **Advisory 체인 → mandatory_context**: LM-B(NPC표류)·LM-C(수치표류)·LM-D(관계표류) 결과가 `_director_mc_parts`를 통해 디렉터에게 전달되고, 디렉터 판정이 `action_items`로 CW에게 도달. **B-1(NPC 타임라인 직접 주입)은 이미 간접 전달되는 정보.**

4. **emotional_beat_section + blueprint_ensemble satisfaction**: 에피소드별 감정 정점(유형+강도)이 CW에게 직접 전달되고, 블루프린트 앙상블 단계에서 연속 좌절 감지 advisory가 작동. **B-3(만족도 이력 주입)은 이미 처방 수준으로 전달.**

**→ 유일하게 기존 시스템에 없는 기능: A-2(open_review 전달)과 A-4(공통 실패 패턴 감지)**

---

## 재검토에서 변경된 판정 (3건) + 감리 수정 (1건)

| ID | 초기 → 최종 | 변경 사유 |
|----|------------|-----------|
| **A-2** | 복잡도 Low-Med → **Low** | 디렉터가 이미 구조화 데이터 반환 중. 스키마 확장 불필요, 전달 경로 연결만. 감리 확인: `contradiction_check` grep 0건(완전 폐기), `open_review` L670+L1567(콘솔+dict 저장만, CW 미전달) |
| **A-3** | 복잡도 Medium → **Med-High** | SessionLogger 읽기 API 없음, fix_scope 로깅 안 됨. 인프라 확장 선행 필요 |
| **B-3** | 복잡도 Medium → **Low** + 근거 수정 | 데이터+쿼리 API 완비. **감리 3차 수정**: `continuity_validator`만 사용 → `blueprint_ensemble.py` L519에서도 사용 중. Stage3은 이미 커버, 제안 범위를 Stage4 주입으로 한정 |

---

## 핵심 발견: 디렉터→CW 정보 유실 맵

```
디렉터 반환 데이터           CW 수신 여부    상태
─────────────────────────────────────────────────
action_items (텍스트)         ✅ 전달됨       정상
issues (텍스트 리스트)        ✅ 전달됨       action_items 없을 때 폴백
contradiction_check (구조화)  ❌ 폐기됨       ← A-2로 해결 가능
open_review (자유 텍스트)     ❌ 콘솔만       ← A-2로 해결 가능
score_breakdown (항목별 점수) ❌ 미전달       ← A-1로 해결 가능
adaptive_threshold (엄격도)   ❌ 미전달       ← A-1로 해결 가능
채점 가중치 (40/20/20/10/10) ❌ 미전달       ← A-1로 해결 가능
fix_scope_reasoning (근거)    ⚠️ 부분 전달    패치 모드 분기에만 사용
```

**→ A-1 + A-2만 구현해도 CW 정보 유실의 대부분 해소.**

---

## 향후 참고 (5차 감리 후 수정)

- **A-2(open_review)만 채택 권장**: 디렉터 자유 리뷰(어색함/비약/톤급변/동기부재)가 콘솔 출력만 되고 CW에 미전달. 유일한 정보 유실 경로.
- **A-4 채택 가능**: V75-B에 "공통 실패 패턴 감지" 레이어 추가. 기존에 없는 기능.
- **A-1, A-2(contradiction_check), B-1, B-3은 REDUNDANT**: DynamicPromptWeighter·_evidence_block·advisory 체인·emotional_beat이 이미 커버.
- **A-3, B-2는 인프라 선행 필요**: 현 시점 ROI 낮음.
- 추가 품질 개선이 필요하면 **advisory 정밀도 향상**(LM-B/C/D 오탐 감소)이나 **CW action_items 이행률 계측**이 더 효과적.

---

## 감리 이력

| 차수 | 검증 대상 | 결과 |
|------|----------|------|
| **1차** | `director.yaml` L92-148 (채점 가중치·100점 원칙·PASS 기준), `chief_writer.yaml` 전문 (가중치 언급 여부), `stage4_interview_round.py` L94-159+L1320-1380 (CW kwargs·피드백 조립) | 문서 주장 전량 일치 |
| **2차** | `director_ensemble.py` L670-699 (반환 구조·open_review 콘솔), `stage4_orchestrator.py` L730-795 (V75-B 블루프린트 재생성·Arc 제안), `director_grading.py` L455-547 (adaptive threshold 로직) | 문서 주장 전량 일치 |
| **3차** | `stage4_interview_round.py` grep `contradiction_check`=0건, grep `open_review`=L1567, `blueprint_ensemble.py` L519 satisfaction 사용, `chief_writer_quality.py` L367-459 (루브릭 4항목) | **오류 1건 수정**: B-3 satisfaction 사용처 누락(`blueprint_ensemble.py`) → 제안 범위 Stage4 한정으로 수정 |
| **4차** | A-1 효과 의심 감리: `DynamicPromptWeighter`(`dynamic_prompt_weighting.py`) 발견 — 실패 카테고리별 동적 프롬프트 강조가 **이미 존재**. `chief_writer.yaml` "죽은 NPC 부활 = 즉시 REJECT" 지침도 이미 연속성 우선 시그널. 정적 가중치(40/20/20/10/10) 주입은 DPW보다 열등 | **A-1 판정 하향**: ★★★ → ★☆☆ (MARGINAL). DPW가 이미 동적으로 같은 역할 수행 |
| **5차** | A-2/B-1/B-3 효과 의심 감리: (A-2) `_evidence_block` L1314-1326이 이미 `[CRITICAL/MAJOR/MINOR]` 태그+텍스트 전달, `action_items`가 구체적 수정 지시 → `contradiction_check` JSON은 동일 정보의 이중 인코딩. (B-1) advisory 체인(LM-B/C/D)이 이미 NPC 변화 핵심을 디스틸해서 `mandatory_context`로 전달. (B-3) `blueprint_ensemble` L519+`emotional_beat_section` L88-92가 이미 페이싱 처방 전달 | **A-2 판정 하향**: ★★★ → ★★☆ (open_review만 유효). **B-1 판정 하향**: ★★☆ → ★☆☆. **B-3 판정 하향**: ★★☆ → ★☆☆ |
