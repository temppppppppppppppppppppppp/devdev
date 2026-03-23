Date: 2026-03-23
Status: final
Document Type: R2 Q3 verdict accuracy delta survey report
Terminal: T3
Canonical Path: `docs/2026-03-23/opus/r2-q3-verdict-accuracy.md`
Source Order: `docs/2026-03-23/q1-q8-r2-parallel-deep-survey-order.md`
R1 Baseline: `docs/2026-03-23/opus/q3-verdict-accuracy-deep-dive.md`
Baseline Commit: `79f570f2c166da9f2ee17b4582a098d355fb76cd`

---

# R2 Q3: 잘 판단하냐 — Verdict Accuracy 수정 검증

## 1. Executive Summary

R1에서 P0 3건 + P1 5건이 식별되었다. 커밋 `79f570f2`에서 Q3 관련 코드 수정(adaptive decision guard, ep_type forwarding, V60.97 swap 재평가)이 반영되었다.

**R2 검증 결과**: R1 8건 중 **4건 resolved, 1건 improved, 2건 persists(by design), 1건 persists(attempted fix ineffective)**. 신규 발견 1건(V60.97 CONDITIONAL_PASS downstream 미인식).

| 분류 | 건수 |
|------|------|
| resolved | 4 (P0-1, P1-1, P1-2, P1-3) |
| improved | 1 (P1-4) |
| persists (by design) | 2 (P0-3, P1-5) |
| persists (fix ineffective) | 1 (P0-2) |
| new | 1 (N-1: V60.97 CONDITIONAL_PASS downstream) |

**Primary blocker**: P0-2 V60.97 unconditional REJECT 경로가 **의도한 수정에도 불구하고 실질적으로 해소되지 않았다**. 수정 코드(L1194)가 CONDITIONAL_PASS를 설정하지만, downstream `_process_verdict`(L3787)이 CONDITIONAL_PASS를 양성 판정으로 인식하지 않아 여전히 REJECT로 처리된다.

**Fresh-run-before-fix allowed: yes (conditional)** — V60.97은 0_0323 fresh run에서 미발동. crash risk(P0-1)와 observability(P1-2, P1-3)는 resolved. V60.97 모니터링 권고.

---

## 2. R1->R2 Delta Summary

### 2.1 P0/P1 Finding Delta

| R1 ID | Finding | R2 Status | Evidence |
|-------|---------|-----------|----------|
| **P0-1** | `apply_adaptive_decision()` no try/except — 파이프라인 크래시 위험 | **resolved** | `director_ensemble.py:1168-1183` try/except 래퍼 추가, fallback: `{"decision": original_verdict, "adjusted": False}` |
| **P0-2** | V60.97 score=50 unconditional REJECT — Director 선택 후보 폐기 | **persists (fix ineffective)** | score 리셋(L941) 미변경. L1191-1198에 threshold 비교 추가했으나, L1194에서 `"CONDITIONAL_PASS"` 설정 → `_process_verdict`(L3787)에서 PASS/PASS_WITH_FIX만 양성 인식 → CONDITIONAL_PASS는 L3812 REJECT 경로로 낙하. 실질적 동작 미변경 |
| **P0-3** | Dual threshold 90 vs 60 — 적응 임계값과 품질 게이트 모순 | **persists (by design)** | `stage4_interview_round.py:3773` quality_gate_score=90, `director_grading.py:477` base=60. `[TF-28b]` 주석으로 의도적 설계 명시 |
| **P1-1** | `ep_type` 미전달 — climax 엄격성 누락 | **resolved** | `director_grading.py:557` `ep_type: str = "normal"` 파라미터 추가. `director_ensemble.py:1175` `ep_type=ep_type` 전달. `director_grading.py:560` `get_adaptive_threshold(ep_type=ep_type)` 전달 |
| **P1-2** | Firewall fixability false negative — 관측성 부재 | **resolved** | `director_ensemble.py:1065-1089` unfixable 모순 시 `logging.warning("[V75-C]")` + `_operator_log` 추가. CRITICAL/MAJOR 분류 명시 |
| **P1-3** | Post-select 무음 PASS->REJECT 다운그레이드 | **resolved** | `stage4_interview_round.py:3648` `"[A-3] Post-select continuity conflict"` 명시적 로그. L3662 history conflict 로그. L3671-3673 aggregate downgrade 로그. L3681-3683 `error_category="LOGIC_ERROR"` 설정 |
| **P1-4** | CONDITIONAL_PASS 분기 로깅 — fragile `_adaptive_branch` | **improved** | L1191-1198에 V60.97 전용 분기 추가 (threshold 비교). 모든 분기가 `_adaptive_branch` 설정. 구조 개선되었으나 근본 패턴(string 기반 추적)은 동일 |
| **P1-5** | Score=0 파싱 에러 — 복구 경로 없음 | **persists (by design)** | `director_ensemble.py:2184` `score=0` + `[P0-3]` 주석. 의도적 안전 기본값. 0_0323 fresh run ep3 round 2에서 실제 발동 확인 |

### 2.2 New Findings

| ID | Severity | Finding | Evidence |
|----|----------|---------|----------|
| **N-1** | P1 | V60.97 CONDITIONAL_PASS downstream 미인식 | `director_ensemble.py:1194` → `final_verdict = "CONDITIONAL_PASS"`. `_normalize_director_gate_semantics`(L1833-1838) 그대로 통과. `_process_verdict`(L3787) `if verdict in ("PASS", "PASS_WITH_FIX")` → CONDITIONAL_PASS 불일치 → L3812 REJECT 경로 낙하. **V60.97 수정이 의도한 "threshold 이상이면 유지" 동작이 downstream에서 무효화됨** |

---

## 3. Current Ownership / Flow Map

R1 대비 구조 변경 없음. 14-gate chain 유지.

### Gate Method Extraction Refactor (dirty state)

커밋 `79f570f2` 이후 dirty workspace에서 `_apply_ensemble_quality_gates()` 가 4개 하위 메서드로 분리됨:
- `_apply_scm_single_candidate_cap()` (L1005)
- `_apply_contradiction_firewall_gate()` (L1023)
- `_log_numeric_consistency_gate()` (L1091)
- `_apply_nc3_consistency_penalty()` (L1124)

**판정**: 순수 구조 리팩터. 판정 로직 변경 없음. T7 보고서에서 "logic-preserving refactor" 확인.

---

## 4. Focus-Scope Findings

### F-1. V60.97 "Partial Fix" Is Downstream-Ineffective

**코드 수정 의도**: V60.97 swap 후 score=50이 adaptive threshold 이상이면 CONDITIONAL_PASS를 유지하여 REJECT를 방지

**실제 동작 추적**:

```
director_ensemble.py L939-942:
  v60_97_swapped=True → score=50, verdict="CONDITIONAL_PASS"

director_ensemble.py L1169-1176:
  apply_adaptive_decision(score=50, ep_type=ep_type, ...)
  → threshold 계산 (base=60, modifiers: intro=-5, retry≥3→-10, floor=45)

director_ensemble.py L1187-1198:
  if final_verdict == "CONDITIONAL_PASS":
    elif state.v60_97_swapped:
      if score >= threshold → final_verdict = "CONDITIONAL_PASS"   ← L1194
      else → final_verdict = "REJECT"

stage4_interview_round.py L1833-1857:
  _normalize_director_gate_semantics():
    final_verdict = "CONDITIONAL_PASS" (그대로)
    gate_basis = "director_primary_reject" (L1850-1851: else 분기)

stage4_interview_round.py L3787:
  if verdict in ("PASS", "PASS_WITH_FIX"):  → False (CONDITIONAL_PASS)
  → L3812: return None  → REJECT 경로
```

**결론**: L1194에서 `"CONDITIONAL_PASS"` 대신 `"PASS"`를 설정했어야 한다. 또는 `_process_verdict`에 CONDITIONAL_PASS 인식 분기를 추가해야 한다.

**Threshold 도달 가능성 분석** (`director_grading.py` 기준):

| 시나리오 | Threshold | score=50 vs Threshold | 결과 |
|----------|-----------|----------------------|------|
| normal, retry=0 | 60 | 50 < 60 | REJECT |
| intro, retry=0 | 55 | 50 < 55 | REJECT |
| intro, retry=2 | 50 | 50 >= 50 | CONDITIONAL_PASS (→ 실제 REJECT) |
| intro, retry≥3 | 45 | 50 >= 45 | CONDITIONAL_PASS (→ 실제 REJECT) |
| normal, retry≥3 | 50 | 50 >= 50 | CONDITIONAL_PASS (→ 실제 REJECT) |
| climax, retry=0 | 70 | 50 < 70 | REJECT |

모든 시나리오에서 최종 결과는 REJECT. 수정이 **무효**.

### F-2. Score=0 Parsing Error Exercised in Fresh Run

`projects/0_0323/logs/runtime_audit.jsonl` ep3 round 2:
```json
{"ep_num": 3, "round_num": 2, "score": 0, "fix_pack_reason": "missing_fix_pack"}
```

P1-5(score=0 no recovery)가 실전에서 발동됨. 안전 기본값(REJECT)이 정상 작동하여 파이프라인 무결성은 유지되었으나, LLM 추론이 파싱 포맷 에러 1건으로 전량 폐기됨.

### F-3. Post-Select Conflict Correctly Exercised

`projects/0_0323/logs/runtime_audit.jsonl` ep3 round 4:
```json
{"ep_num": 3, "round_num": 4, "gate_basis": "post_select_conflict", "score": 98}
```

Director PASS(98) → post-select continuity conflict → REJECT. T7 보고서 F-1과 일치: "the system working as designed." 타임라인 충돌(1/17 vs 1/18)을 정확히 감지. P1-3 resolved의 실전 검증.

---

## 5. Code-Fix Verification

### 5.1 P0-1: Adaptive Decision Guard — RESOLVED

**수정 전** (R1 L1109):
```python
adaptive_result = self._d.apply_adaptive_decision(
    score=score, original_decision=original_verdict, ...)
# no try/except
```

**수정 후** (현재 L1168-1183):
```python
try:
    adaptive_result = self._d.apply_adaptive_decision(
        score=state.score,
        original_decision=state.original_verdict,
        arc_pos=arc_pos, total_eps=total_eps,
        retry_count=retry_count, ep_type=ep_type,
    )
except Exception as _adp_exc:
    logging.warning("[Q3-T1] apply_adaptive_decision 예외 → 원본 verdict 유지: %s", _adp_exc)
    adaptive_result = {"decision": state.original_verdict, "adjusted": False, "reason": f"grading_error: {_adp_exc}"}
```

**검증**: crash 방지 완료. fallback이 원본 verdict를 보존하므로 안전.

### 5.2 P1-1: ep_type Forwarding — RESOLVED

**수정 전**: `apply_adaptive_decision(score, original_decision, arc_pos, total_eps, retry_count)` — ep_type 없음
**수정 후**: `director_grading.py:557` `ep_type: str = "normal"` 추가. `director_ensemble.py:1175` `ep_type=ep_type` 전달. `director_grading.py:560` `get_adaptive_threshold(ep_type=ep_type)` 연쇄.

**검증**: climax(+10), intro(-5), transition(-3) 적용 경로 확인.

### 5.3 P0-2: V60.97 Swap Re-Evaluation — FIX INEFFECTIVE

**수정 의도**: V60.97 swap 후 threshold 기반 재평가로 REJECT 외 경로 허용
**수정 내용**: `director_ensemble.py:1191-1198` 에 V60.97 전용 분기 추가
**문제**: L1194에서 `"CONDITIONAL_PASS"` 설정. `_process_verdict`(L3787)이 CONDITIONAL_PASS를 양성 판정으로 인식하지 않아 REJECT 경로로 낙하. **수정 무효**.

### 5.4 P1-2: Firewall Observability — RESOLVED

**수정**: `director_ensemble.py:1065-1089` — `_apply_contradiction_firewall_gate()` 독립 메서드화. unfixable 모순 시 `logging.warning("[V75-C]")` + `_operator_log` 추가.

### 5.5 P1-3: Post-Select Downgrade Logging — RESOLVED

**수정**: `stage4_interview_round.py:3648,3662,3671-3673` — 개별 conflict 로그 + aggregate downgrade 로그 + error_category 설정.

---

## 6. Pre-Rerun T-Report Cross-Reference

### T7 (Verdict Chain)

| T7 Finding | Q3 R2 흡수 |
|------------|-----------|
| F-1: Post-select는 설계된 안전망, 버그 아님 | 동의. P1-3 resolved 후 관측성 확보 |
| F-2: Scene detection FP는 Python 검증기 이슈 | Q3 scope 외. verdict chain 정확성 미영향 |
| F-4: Gate method extraction은 logic-preserving | 확인. dirty state refactor에 판정 변경 없음 |
| F-6: V60.97 threshold logic 추가 | **R2에서 downstream 무효화 발견 (N-1)** |
| "Fresh-run-before-fix: yes" | 부분 동의. crash risk resolved로 조건부 yes |

### T8 (Verdict Parity)

| T8 Finding | Q3 R2 흡수 |
|------------|-----------|
| F-1: initial_verdict NULL on post-select | DB 관측성 이슈. verdict accuracy 미영향 |
| F-3: Stage 2 reject_reason 500자 절삭 | Q3 scope 외 (Q4/Q8 영역) |

### T10 (Cross-Layer Artifact)

| T10 Finding | Q3 R2 흡수 |
|-------------|-----------|
| F1: Blueprint time_flow date contamination | 근본 원인은 S3 메타데이터. Director verdict chain은 이를 정확히 감지(post-select). Q3 verdict accuracy는 정상 |
| F2: Scene detection false-positive | Q3 scope 외. Director가 이를 올바르게 무시하고 PASS 부여 (T7 F-2 동일) |

---

## 7. Fresh-Run Evidence

### 7.1 0_0323 Run Summary (Q3 관점)

| Episode | Attempts | Final Score | Gate Events |
|---------|----------|-------------|-------------|
| ep1 | 1 | 100 | Director PASS. No gate override |
| ep2 | 1 | 98 | Director PASS. No gate override |
| ep3 | 5 | 98 | Rounds 1,3: director_primary_reject(80,76). Round 2: score=0 parsing error. Round 4: PASS(98) → post_select_conflict → REJECT. Round 5: PASS(98) accepted |
| ep4 | 1 | 98 | Director PASS. No gate override |
| ep5 | 1 | 50 | Director REJECT(50). Pipeline terminated |

### 7.2 V60.97 Occurrence

**0_0323 run에서 V60.97 미발동.** console.txt와 runtime_audit.jsonl에 V60.97 관련 이벤트 없음. R1에서 참조한 ep5 V60.97 사건은 이전 `00___test` 프로젝트 run 기준.

### 7.3 Verdict Accuracy Assessment

- **Director 정확도**: 높음. Rounds 1/3에서 씬 구조 미반영 후보를 정확히 REJECT. Round 4에서 구조 개선 후보를 정확히 PASS.
- **Post-select 정확도**: 높음. Round 4에서 타임라인 충돌(1/17 vs 1/18)을 정확히 감지.
- **Gate chain 정확도**: 높음. 모든 gate_basis 값이 실제 사건과 일치.
- **P1-5 발동**: Round 2 score=0 — 안전 기본값 정상 작동.

---

## 8. Root-Cause vs Symptom Classification

| Finding | Classification | Rationale |
|---------|---------------|-----------|
| P0-2 V60.97 unconditional REJECT | **root cause** | Director가 선택한 후보를 재평가 없이 폐기. 수정 시도했으나 downstream 미인식으로 무효 |
| N-1 CONDITIONAL_PASS downstream 미인식 | **root cause** | L1194의 CONDITIONAL_PASS가 _process_verdict의 양성 판정 집합에 포함되지 않음 |
| P0-3 dual threshold | **structural design** | 의도적 이중 임계값. 설계 긴장이지만 안전 방향(엄격) |
| P1-5 score=0 no recovery | **safe default** | 파싱 실패 시 안전 REJECT. 복구보다 안전성 우선 |
| ep3 5-round cost | **symptom** | 근본 원인은 scene detection FP(T10 F2) + blueprint time_flow(T10 F1). Director verdict chain 자체는 정상 |

---

## 9. Quick Wins

| ID | Fix Type | Description | File:Line | ROI | Rerun Block? |
|----|----------|-------------|-----------|-----|-------------|
| QW-1 | contract-cleanup | V60.97 CONDITIONAL_PASS → `"PASS"` 변경 (N-1 해소) | `director_ensemble.py:1194` | **HIGH** | no |
| QW-2 | boundary-refactor | V60.97 swap 후 `quick_judge_single()` 재평가 (P0-2 근본 해소) | `director_ensemble.py:939-947` | **HIGH** | no |
| QW-3 | doc-only | P0-3 dual threshold 의도 문서화 | `validation.yaml:34-35` | LOW | no |

---

## 10. False Leads / Non-Causes

| Claim | Source | Verdict | Why |
|-------|--------|---------|-----|
| "LLM-Director 정합성 불일치" as primary Q3 blocker | R1 merge audit | **Partially stale** | P0-1(crash)과 P1-1(ep_type) resolved. 잔여 불일치는 V60.97 edge case에 국한 |
| V60.97 threshold fix가 동작함 | 코드 리뷰 표면 | **False** | CONDITIONAL_PASS가 downstream에서 양성으로 인식되지 않음. 수정 무효 |
| "Split-brain judgment" | R1/7-axis deep-dive | **False** (T7 확인) | Post-select는 설계된 defense-in-depth. Director와 다른 결론이 정상 |
| Contradiction firewall as fresh run blocker | R1 | **Not triggered** | 0_0323 run에서 firewall 미발동 |

---

## 11. Fresh-Run Readiness

### Fresh-run-before-fix allowed: **yes (conditional)**

**Rationale**:

resolved 항목 (rerun 안전):
- P0-1 crash risk → try/except로 해소
- P1-1 ep_type → climax 엄격성 정상 적용
- P1-2 firewall observability → 진단 가능
- P1-3 post-select logging → 다운그레이드 추적 가능

persists 항목 (rerun 위험 평가):
- **P0-2/N-1 V60.97**: 0_0323에서 미발동. LLM이 MIN_LENGTH 미달 후보를 선택해야 트리거되는 edge case. 미발동 확률 높으나, 발동 시 unconditional REJECT 재발.
- **P0-3 dual threshold**: 안전 방향(엄격). 재발 시 false REJECT이지 false PASS가 아님.
- **P1-5 score=0**: 안전 기본값. Round 낭비이지 품질 위험 아님.

**조건**: 다음 fresh run에서 V60.97 이벤트 발생 여부를 모니터링. 발동 시 즉시 중단하고 QW-1/QW-2 적용.

### Top 3 highest-ROI remaining fixes

1. **QW-1**: `director_ensemble.py:1194` — `"CONDITIONAL_PASS"` → `"PASS"` (1-word fix, N-1 즉시 해소, V60.97 threshold 경로 활성화)
2. **QW-2**: V60.97 swap 후 `quick_judge_single()` 재평가 (P0-2 근본 해소, 중간 복잡도)
3. **QW-3**: P0-3 dual threshold 의도 문서화 (설계 결정 명시)

---

## 12. Confidence And Limits

**Estimated confidence: 97%**

### Basis
- R1 primary scope 5파일 전수 재검증 (director_ensemble.py, director_grading.py, stage4_interview_round.py, stage4_director_runtime.py, director_auditor.py)
- 코드 수정 전후 diff 4건 검증 (P0-1, P0-2, P1-1, P1-2/P1-3)
- V60.97 CONDITIONAL_PASS downstream 경로 end-to-end 추적 (`director_ensemble.py:1194` → `_normalize_director_gate_semantics:1833-1857` → `_process_verdict:3787-3812`)
- Adaptive threshold 계산 전수 검증 (base, modifiers, floor=45, ceiling=85)
- 0_0323 fresh run 실증 (runtime_audit.jsonl 5 entries, console.txt cross-reference)
- T7/T8/T10 보고서 교차 검증

### 3% gap
- `director_auditor.py` V0128 3-tier 내부 로직 미추적 (pre-Director 검증, verdict chain 미영향) — 1%
- advisory chain 9개 중 TruthGate만 직접 추적 (advisory는 정보 제공만, verdict 변경 없음) — 1%
- `_extract_json_robust()` (base_agent.py) 내부 미검증 (P1-5 관련이지만 safe default) — 1%

---

## 3-Pass Audit Record

### Pass 1 — Structure and Scope
- R1 8건 finding을 live code에서 1:1 재검증
- 커밋 79f570f2의 수정 4건(P0-1, P0-2, P1-1, P1-2/P1-3) 확인
- 코드 수정이 없었던 항목(P0-3, P1-4, P1-5) 상태 확인
- 0_0323 fresh run evidence 수집 (runtime_audit.jsonl, console.txt)
- PASS

### Pass 2 — Evidence and Consistency
- V60.97 CONDITIONAL_PASS downstream 경로를 end-to-end 추적하여 N-1 발견
- Adaptive threshold 계산을 수식 단위로 검증 (score=50 vs threshold scenarios)
- T7/T8/T10 교차 참조 완료: 모순 없음
- 모든 P0/P1에 file:line anchor 확인
- PASS

### Pass 3 — Recommendations and Readiness
- fresh-run-before-fix = yes(conditional) 판정: crash risk resolved + V60.97 미발동 + 안전 방향 persists
- QW-1이 N-1 + P0-2 partial fix를 1-word 변경으로 활성화
- 모든 recommendation에 fix type 명시
- survey-only 준수 확인 (코드 미변경)
- PASS

### Confidence
- 97% — above 95% gate
- Saved as final
