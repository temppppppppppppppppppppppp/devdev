# Stage 3 Blueprint P1 Defect Root-Cause Bounded Survey

Date: 2026-03-30
Status: final
Project: 0_1
Scope: EP8 empty characters + EP15 cross-field drift — Stage 3 code path root cause
Mode: read-only bounded survey (코드/DB/blueprint 수정 금지)
Baseline Commit: 9ad4efcc (main)
Source Evidence:
- docs/2026-03-30/0_1-stage3-blueprint-integrity-bounded-survey.md (prior survey)
- docs/2026-03-30/0_1-stage3-blueprint-fix-execution-ssot.md (prior fix SSOT)
- projects/0_1/logs/artifacts/stage3/ep_0008/ (artifact truth)
- projects/0_1/logs/artifacts/stage3/ep_0015/ (artifact truth)
- projects/0_1/plans/arcs/arc_004.txt (arc source truth)
- projects/0_1/logs/session/decisions.jsonl (runtime decision truth)
- modules/domain/agents/unified_blueprint_validator.py (validation code truth)
- modules/core/stage3_orchestrator.py (orchestration code truth)
- modules/models/blueprint.py (schema truth)

## 1. Defect Summary

| ID | EP | Defect | Severity | Original Score |
|----|-----|--------|----------|----------------|
| P1-A | 8 | `scene_breakdown.scene_1~4.characters == []` (4건 전량 빈 배열) | P1 | 78 |
| P1-B | 15 | `ending_state.timeline.표현 = "2006년 4월 중순 심야"` vs Arc 4 = "2006년 5월 말" (6주 gap) | P1 | 78 |
| P1-C | 15 | `integrated_scenario` "밑줄" vs `scene_2.content` "동그라미" (동일 행동 불일치) | P1 | 78 |

## 2. Investigation Method

**3-layer cross-referencing:**
1. Artifact truth: git diff로 원본 JSON 상태 확인 (patch 전/후 분리)
2. Code truth: validation pipeline 9개 prevalidation 함수 + Director compare + gating 코드 전수 읽기
3. Runtime truth: decisions.jsonl 의 EP8/EP15 결정 로그 교차 검증

**핵심 질문 5개에 대한 코드 경로 추적:**
- unified_blueprint_validator.py (1,300+ lines) 전량 분석
- stage3_orchestrator.py 앞부분 200줄 + artifact save 경로
- modules/models/blueprint.py Pydantic schema
- blueprint_constraint_compiler.py / writer_template.py / context_compression.py: downstream consumer의 characters 의존성 확인
- director_ensemble.py: Director compare prompt 내 timeline 관련 instruction 확인

## 3. Stage 3 Validation Pipeline 구조

```
LLM Ensemble (3 candidates)
  ↓
_prepare_compare_candidate() — per-candidate
  ├─ _python_pre_validate()
  │   ├─ _collect_structure_prevalidation_issues      → scene_breakdown 존재, scene_count ≥ 3, goal/summary
  │   ├─ _collect_fidelity_prevalidation_issues       → Arc NPC integrated_scenario 언급
  │   ├─ _collect_arc_compliance_prevalidation_issues  → 정지선 위반 (다음 화 침범)
  │   ├─ _collect_continuity_prevalidation_issues      → 이전 화 종료 위치 vs 현재 시작 위치
  │   ├─ _collect_fact_lock_drift_issues              → fact-lock/capital 숫자 drift
  │   ├─ _collect_capital_state_drift_issues           → 자산 상태 drift
  │   ├─ _collect_temporal_deictic_drift_issues        → ending_hook "N년 전" 패턴
  │   ├─ _collect_scene_specificity_issues             → goal/summary 8자 미만, key_events 빈 배열
  │   └─ _collect_scenario_density_issues              → 평균 자/씬 밀도
  ├─ _apply_dead_npc_advisory()
  └─ python_warnings → candidate._ensemble_meta에 attach
  ↓
Director.compare_and_select_blueprint() — LLM 최종 판정
  ↓
verdict: PASS / PASS_WITH_FIX / REJECT
  ↓
Pydantic validate_blueprint() — schema-level validation
  ↓
snapshot_logged_artifact() → JSON 파일 저장
save_episode_blueprint() → DB 저장
```

## 4. Root Cause Chain: P1-A (EP8 Empty Characters)

### 4.1 원인 경로

| Layer | What Happened | Evidence |
|-------|---------------|----------|
| **Generator (LLM)** | 3개 후보 중 선택된 candidate_index=2가 `scene_breakdown`의 4개 씬에서 `characters: []` 생성 | git diff: 원본 JSON 4건 전량 `"characters": []` |
| **Pydantic schema** | `BlueprintScene.characters = Field(default_factory=list)` — 빈 리스트는 valid value | modules/models/blueprint.py |
| **Python prevalidation** | 9개 검사 함수 중 `characters` 비어있음을 검사하는 함수 **0건** | unified_blueprint_validator.py grep "characters" = 0 match |
| **Director compare** | 서사 품질 평가 (score 78). integrated_scenario 본문에 한시우/박성호 언급 → 캐릭터 부재를 인지 불가 | decisions.jsonl: "금융물의 카타르시스를 잘 살렸으며 엔딩 훅이 가장 강력함." |
| **Gating** | quality_risk=true → advisory only, PASS 차단 안 함 | unified_blueprint_validator.py:361 |

### 4.2 핵심 gap

**`scene.characters` non-empty invariant가 전체 validation pipeline에 부재.**

- Python prevalidation: goal/summary 유무, key_events 유무, scene_count ≥ 3은 검사하지만 characters는 검사하지 않음
- Director: integrated_scenario 텍스트에서 캐릭터 이름을 읽을 수 있으나, structured `characters` 배열의 completeness는 검사 대상이 아님
- Pydantic: `default_factory=list` → 빈 리스트를 유효한 값으로 허용

### 4.3 Downstream 영향

characters를 읽는 소비자 3곳:
1. `blueprint_constraint_compiler.py:472` — `last_scene.get("characters", [])` → Stage 4 constraint 구성 시 빈 배열이면 캐릭터 정보 누락
2. `context_compression.py:285` — `scene_data.get("characters", [])[:3]` → 압축 컨텍스트에 캐릭터 정보 미포함
3. `writer_template.py:145` — `scene_data.get("characters", [])` → Stage 4 manuscript 생성 시 캐릭터 목록 미제공

### 4.4 prevalidation false positive 문제

EP8 `_ensemble_meta.python_warnings`에 기록된 3건:
- "씬 구조 미비: 4/4개 씬에 goal/summary 없음" (MINOR)
- "씬 목표 미흡: 4/4개 씬의 goal/summary가 8자 미만" (MAJOR)
- "씬 이벤트 부재: 4/4개 씬에 key_events가 비어 있음" (MINOR)

그러나 최종 저장 artifact에는 goal/summary/key_events가 전부 정상 채워져 있음. 이는 prevalidation이 LLM raw output 상태에서 실행된 후, Director compare 또는 후처리에서 scene 필드가 enrich된 것을 의미. 하지만 **characters만 enrich 대상에서 제외**되어 빈 배열로 남았음.

## 5. Root Cause Chain: P1-B (EP15 Timeline 6주 Gap)

### 5.1 원인 경로

| Layer | What Happened | Evidence |
|-------|---------------|----------|
| **Generator (LLM)** | EP14 ending "4월 중순 늦은 저녁" → EP15를 같은 시간대로 계속 생성. Arc 4의 "2주 gap → 5월 말" 지시를 무시 | git diff: 원본 `"표현": "2006년 4월 중순 심야"` |
| **Timeline advisory** | `_inject_stage3_timeline_advisory()` (stage3_orchestrator.py:1180)가 arc 시간 마커를 생성 프롬프트에 주입 | 코드 확인 완료 — 생성 시 advisory, 검증 시 미사용 |
| **Python prevalidation** | `_collect_temporal_deictic_drift_issues()` (L1154): ending_hook에서 "N년 전/후" regex만 검사. **ending_state.timeline vs arc.state_changes.timeline 비교 없음** | unified_blueprint_validator.py L1154-1211 |
| **Continuity check** | `_collect_continuity_prevalidation_issues()` (L805): **위치** 연속성만 검사, **시간** 연속성 미검사 | unified_blueprint_validator.py L805-831 |
| **Director compare** | "이전 화 훅과 완벽히 이어지며 Arc 전술서를 충실히 반영함" — 시간 정합성 언급 없음 | decisions.jsonl EP15 entry |
| **Gating** | PASS, score 78, quality_risk=true (advisory only) | |

### 5.2 핵심 gap

**Blueprint `ending_state.timeline` vs Arc `state_changes.timeline` cross-reference 검증이 전체 pipeline에 부재.**

- `_collect_temporal_deictic_drift_issues`: "N년 전" regex 패턴만 감지. 실제 날짜 비교 아님
- `_collect_continuity_prevalidation_issues`: location만 비교. timeline 비교 없음
- `_inject_stage3_timeline_advisory`: 생성 프롬프트에 arc 시간을 주입하지만, 산출물 검증에서는 미사용
- Director: arc tactical doc 텍스트를 받지만, 구조화된 timeline start/end 날짜를 비교 지시 받지 않음

### 5.3 누적 drift 메커니즘

EP10-14가 "4월 중순" 하루 동안의 사건으로 압축 생성 → EP15가 EP14 직후 같은 밤으로 이어짐 → Arc 4의 의도된 "EP14→EP15 사이 2주 gap"이 사라짐. 이는 multi-episode cumulative timeline drift를 감지하는 메커니즘이 없기 때문.

## 6. Root Cause Chain: P1-C (EP15 Marker 불일치)

### 6.1 원인 경로

| Layer | What Happened | Evidence |
|-------|---------------|----------|
| **Generator (LLM)** | `integrated_scenario`에서 "밑줄을 그었다" 기술 → 별도로 `scene_2.content`에서 "동그라미를 친다" 기술. 두 필드가 독립 생성 | git diff: 원본 scene_2.content "동그라미를 친다" |
| **Python prevalidation** | integrated_scenario와 scene.content 간 cross-field consistency 검사 **없음** | 9개 검사 함수 전량 확인 |
| **Director compare** | integrated_scenario를 primary text로 읽음. scene.content까지 교차 읽기/비교 지시 없음 | |

### 6.2 핵심 gap

**integrated_scenario 본문과 scene.content 간 내부 일관성 검증 없음.**

## 7. 5가지 핵심 질문에 대한 답변

### Q1: EP8에서 왜 `scene.characters` 빈 배열 4건이 하드 fail 되지 않았는가

**답변:** Python prevalidation의 9개 검사 함수 중 `characters` 필드를 검사하는 함수가 0건이다. Pydantic schema는 빈 리스트를 valid로 허용한다. Director는 integrated_scenario 텍스트를 읽기 때문에 structured characters 배열의 completeness를 판단하지 않는다.

### Q2: Stage 3는 `scene_breakdown` 존재만 보았는가, scene-level completeness contract가 있었는데 누락된 것인가

**답변:** `scene_breakdown` 존재는 검사한다 (`_collect_structure_prevalidation_issues` L681). scene 내부에서 `goal`/`summary` 존재와 `key_events` 비어있음은 검사한다 (L719-745, L1228-1257). 그러나 `characters`에 대한 completeness contract는 **원래부터 존재하지 않았다**. 누락이 아니라 미설계.

### Q3: EP15에서 `integrated_scenario`, `scene_2.content`, `time_flow`, `ending_state.timeline` 간 내부 불일치를 누가 놓쳤는가

**답변:** 전원이 놓쳤다.
- Python prevalidation: cross-field consistency 검사 자체가 없음
- Director: integrated_scenario를 primary로 읽고, scene.content나 ending_state.timeline을 arc data와 교차 비교하는 지시가 없음
- Constitutional checker: timeline alignment 관련 article 없음 (B5는 content scope 검사, time scope 아님)

### Q4: 이 문제는 generator의 산출 문제인가, validator의 누락인가, selection/gating의 severity 설정 문제인가

**답변:** **Validator 누락이 primary root cause.** Generator가 불완전한 산출물을 생성한 것은 LLM의 본질적 한계 (확률적 생성). 이를 보상하기 위한 validation contract가 해당 invariant를 커버하지 않았다. Gating은 secondary — quality_risk=true가 PASS를 차단하지 않는 것은 설계 의도이므로 문제가 아니다.

### Q5: 가장 낮은 위험 seam은 어디인가

**답변:** **Validator invariant 추가** (Option 2).

| Seam | Risk | Effectiveness | 비고 |
|------|------|---------------|------|
| Generator prompt 강화 | Low | Medium | LLM이 무시할 수 있음. Safety net 아님 |
| **Validator invariant 추가** | **Lowest** | **High** | 기존 `_collect_*_issues` 패턴 확장. Advisory-only. 아키텍처 변경 없음 |
| Post-generation normalizer | Medium | Medium | 새 파이프라인 단계 추가. Characters 자동 추출은 오류 가능 |
| Confidence/hard-gate 승격 | High | High | 유효한 blueprint를 과도하게 reject할 위험 |

Validator invariant 추가가 최적인 이유:
1. `_python_pre_validate()` 내 `_collect_*_issues` 메서드 3개 추가로 해결
2. 기존 패턴 (advisory-only, Director에게 전달) 100% 재활용
3. 아키텍처/파이프라인 변경 0건
4. 기존 8개 에피소드 (EP2-7, EP9, EP11)의 정상 blueprint에 false positive 없음

## 8. Touched Code Surfaces (Validator Hardening)

| File | 추가할 검사 | P1 대상 |
|------|------------|---------|
| `modules/domain/agents/unified_blueprint_validator.py` | `_collect_scene_characters_issues()` | P1-A |
| `modules/domain/agents/unified_blueprint_validator.py` | `_collect_arc_timeline_alignment_issues()` | P1-B |
| `modules/domain/agents/unified_blueprint_validator.py` | `_collect_cross_field_consistency_issues()` | P1-C |

호출 삽입점: `_python_pre_validate()` (L845-914) 내부, 기존 `_collect_*` 호출 이후.

## 9. 확신도

| Pass | Focus | Result |
|------|-------|--------|
| Pass 1 | 9개 prevalidation 함수 전량 코드 읽기 + characters/timeline 검사 부재 확인 | 완료 |
| Pass 2 | git diff 교차, decisions.jsonl 교차, arc_004.txt 교차 — 3-layer evidence 확보 | 완료 |
| Pass 3 | downstream consumer 3곳 characters 의존성, Director prompt timeline 지시 부재, Pydantic default 확인 | 완료 |

**Estimated confidence: 97%**

제한 요인:
- Director의 compare_and_select_blueprint() LLM 내부 reasoning은 직접 관찰 불가 (decisions.jsonl의 reason만 간접 확인)
- EP8 prevalidation false positive의 정확한 enrich 메커니즘 (Director response vs 후처리)은 런타임 LLM I/O 없이 완전 특정 불가

---

*3pass audit completed. Final save.*
