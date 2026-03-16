# TF-C: Stage 3 Observational Signals

> 조사일: 2026-03-16
> 범위: coverage_warnings / scene_count validation / blueprint quality scores
> 방법: Grep 전체 .py 검색 + 코드 직접 읽기

---

## Signal Inventory

| # | Signal | Producer (file:line) | Expected Consumer | Actual Consumer | Status | Impact |
|---|--------|---------------------|-------------------|-----------------|--------|--------|
| C-1 | `coverage_warnings` | stage3_orchestrator.py:1233-1243 | S3 retry 루프 | quality_dashboard (관측만) | **ADVISORY-ONLY** | M |
| C-2 | `scene_count validation` | UnifiedBlueprintValidator:380-388 | S3 retry 루프 | S4 Director hard gate (L455-460) | **DEFERRED** | M |
| C-3 | `blueprint quality scores` | (S3에서 미산출) | S3 retry 루프 | S4 quality_gate_score (L3265-3270) | **DEFERRED** | M |

---

## Detailed Findings

### [TF-C-1] coverage_warnings — ADVISORY-ONLY

- **Producer**: `Stage3Orchestrator._stage_3_batch_blueprinting()` → `stage3_orchestrator.py:1233-1243`
  - 리스트 형태: `["missing_work_slot_summary", "work_focus_without_slots", "missing_relation_slice"]`
  - `quality_dashboard.record_retrieval_observation()` (L1244)에 전달
- **Storage**: `pipeline_result["_stage3_observability"]["coverage_warnings"]`
- **Expected Consumer**: Stage 3 retry 루프 — coverage_warning 임계값 초과 시 Blueprint 재생성
- **Actual Consumer**:
  - `quality_dashboard.get_retrieval_observation_summary()` (L321-350) — coverage_warning_rate 계산
  - **관측/트렌드 모니터링 전용**. retry 트리거 없음
- **Status**: ADVISORY-ONLY — 경고 계산 → 기록 → 끝. 아무 조치 안 함
- **Evidence**: stage3_orchestrator.py에서 coverage_warnings 기반 retry/재생성 로직 없음
- **Impact**: M — 불완전한 Blueprint가 Stage 4로 전달될 수 있음
- **Remediation**: WIRE — coverage_warning_rate > threshold 시 S3 retrieval 재실행 트리거 권장

### [TF-C-2] scene_count validation — DEFERRED (S3→S4)

- **Producer**: `UnifiedBlueprintValidator.validate()` → `unified_blueprint_validator.py:380-388`
  - scene_count < 3 → severity: MAJOR 이슈 생성
- **Stage 3 소비**: **없음**
  - Stage 3 orchestrator에 scene_count 기반 retry 루프 없음
  - Blueprint 생성 → Validator 체크 → 이슈 기록 → Stage 4로 전달
- **Stage 4 소비**: `DirectorEnsemble._preliminary_quick_check()` → `director_ensemble.py:455-460`
  - scene_count < 4 → **즉시 REJECT** (hard gate)
  - Stage 4 retry 루프에서 재생성 시도
- **Status**: DEFERRED — S3에서 감지 가능하나 조치 안 함. S4에서 비로소 reject
- **Evidence**: stage3_orchestrator.py에 scene_count 기반 BlueprintRetry 메커니즘 없음
- **Impact**: M — S3에서 씬 부족 Blueprint 생성 → S4에서 reject → S4 retry 비용 낭비
- **Remediation**: WIRE — S3 Validator에서 scene_count < 4 시 Architect 재호출 루프 추가

### [TF-C-3] blueprint quality scores — DEFERRED (S3→S4)

- **Stage 3 산출**: **없음**
  - S3의 `ThreePhaseBlueprinter`는 Blueprint 생성만 수행
  - `UnifiedBlueprintValidator`는 구조 검증만 (점수 없음)
  - 품질 점수는 S3에서 산출되지 않음
- **Stage 4 산출**: `DirectorEnsemble.evaluate()` → `director_ensemble.py`
  - score_breakdown (setting_consistency, scene_composition, narrative_flow, length) 산출
  - score < quality_gate_score(기본 90) → REJECT → S4 retry
- **Status**: DEFERRED — S3에서 품질 측정 없이 S4로 넘김. S4에서 비로소 평가
- **Evidence**: stage3_orchestrator.py에 Blueprint 품질 점수 계산 로직 없음
- **Impact**: M — 저품질 Blueprint가 S4까지 도달 후 reject → 비용 낭비
- **Remediation**: WIRE (optional) — S3에 경량 Blueprint 품질 사전평가 추가. 단, 과도 engineering 주의

---

## Summary

| Status | Count | Signals |
|--------|-------|---------|
| **ADVISORY-ONLY** | 1 | coverage_warnings |
| **DEFERRED** | 2 | scene_count, blueprint quality |

### 구조적 패턴

**Stage 3 = "생성만, 검증은 Stage 4 위임" 패턴**: S3는 Blueprint를 생성하고 기본 구조만 체크. 품질 검증/씬 수 강제/커버리지 경고 대응 모두 S4 Director에 위임. **S3 자체 retry 루프가 사실상 부재**.

이는 의도적 설계일 수 있으나(S3 LLM 호출 최소화), S4에서 반복 reject 시 비용이 S3 retry보다 큼.

### Remediation 우선순위

| 우선순위 | Signal | 조치 |
|---------|--------|------|
| P1 | coverage_warnings | threshold 초과 시 S3 retrieval 재실행 |
| P2 | scene_count | S3 Validator에서 < 4 시 Architect 재호출 |
| P3 | blueprint quality | S3 경량 사전평가 (optional — ROI 확인 필요) |
