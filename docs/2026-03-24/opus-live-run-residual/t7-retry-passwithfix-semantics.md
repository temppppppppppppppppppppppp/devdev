# T7 Lane Report: Retry And PASS_WITH_FIX Semantics

Date: 2026-03-24
Status: final (3-pass audited)
Lane: T7 — Retry And PASS_WITH_FIX Semantics
Governing Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`
Primary Evidence Run: `projects/0324_00_`

---

## 1. Executive Summary

PASS_WITH_FIX와 post-select conflict의 coexistence는 **아키텍처적으로 올바른 separation of concerns**이다. Runtime은 두 검출 축을 정확한 순서로 실행하며, patch-bias는 존재하지 않는다.

핵심 발견:

1. Post-select 검사가 patch loop **이전**에 실행된다 — patch cycle 낭비 없음
2. Post-select downgrade는 `repair_scope="full"`을 강제한다 — patch 모드 진입 차단
3. EP5에서 PASS_WITH_FIX + post-select conflict coexistence가 2회 발생했으나, 두 경우 모두 patch loop는 진입하지 않았음
4. EP7에서 PASS_WITH_FIX가 post-select clean 상태에서 정상 작동하여 1라운드 내 해결

이 lane은 잔류 rescue round의 원인이 아니다.

---

## 2. Included Coverage / Exclusions

### Included

- `modules/core/stage4_interview_round.py` — PASS_WITH_FIX eligibility, post-select conflict detection, verdict ordering
- `modules/core/stage4_retry_runtime.py` — patch loop orchestration, retry lane routing, budget axes
- `modules/core/stage4_reject_runtime.py` — reject handling, error_category routing
- `projects/0324_00_/logs/episode_production.jsonl` — EP5/EP7 round-by-round verdict chain

### Excluded

- Blueprint authority issues (T4 lane)
- Carryover packet content (T6 lane)
- Validator signal quality (T8 lane)
- Artifact body diffs (T9 lane)

---

## 3. Key Evidence

### Finding 1: Post-select runs BEFORE patch loop (no wasted cycles)

`stage4_interview_round.py:4000-4049` `_run_positive_verdict_transition`:

```
L4018  verdict, ... = self._run_post_select_checks(...)   ← FIRST
L4035  if verdict == "PASS_WITH_FIX" and final_manuscript:  ← SECOND (conditional)
L4037      self._execute_pass_with_fix_loop(...)
```

Post-select이 verdict를 REJECT로 바꾸면 L4035 조건이 `False`가 되어 patch loop를 건너뛴다.

**결론**: PASS_WITH_FIX + post-select conflict 동시 발생 시 patch loop는 실행되지 않는다. Cycle 낭비 없음.

### Finding 2: Post-select downgrade는 full retry를 강제한다

`stage4_interview_round.py:3745-3750`:

```python
verdict = "REJECT"
director_result = self._apply_director_gate_update(
    director_result,
    final_verdict="REJECT",
    gate_basis="post_select_conflict",
    repair_scope="full",              # ← 항상 "full"
)
```

`stage4_interview_round.py:3773`:

```python
_post_select_fix_scope = "full"       # ← previous_attempt에도 "full" 저장
```

Post-select downgrade는 **항상** `repair_scope="full"`을 강제한다. 다음 라운드에서 inplace patch로 우회할 수 없다.

### Finding 3: Retry routing에서 force_patch가 post-select conflict에 대해 차단됨

`stage4_retry_runtime.py:866-873`:

```python
force_patch = (
    patch_enabled
    and prev_manuscript
    and reject_bucket == "post_select_conflict"
    and fix_scope != "full"            # ← "full"이면 False
    and round_num <= 1
    and not _consecutive_empty_patch
)
```

Post-select downgrade가 `fix_scope="full"`을 설정하므로 `fix_scope != "full"` 조건이 `False` → **force_patch = False**. 즉 post-select conflict 이후 retry는 patch 모드가 아닌 full generation으로 진행된다.

### Finding 4: PASS_WITH_FIX eligibility contract은 엄격하다

`stage4_interview_round.py:1717-1740` `_evaluate_pass_with_fix_contract`:

| 조건 | 미충족 시 |
|------|----------|
| `fix_scope == "inplace"` | eligible=False, reason=`non_local_fix_scope` |
| `fix_pack.patch_targets` 비어있음 | eligible=False, reason=`missing_patch_targets` |
| `fix_pack.must_fix` 비어있음 | eligible=False, reason=`missing_must_fix` |
| `fix_pack.do_not_regress` 비어있음 | eligible=False, reason=`missing_do_not_regress` |
| `fix_pack.success_condition` 비어있음 | eligible=False, reason=`missing_success_condition` |
| `target_kind == "scene_model"` | eligible=False, reason=`scene_model_target` |

미충족 시 `_enforce_pass_with_fix_contract` (L1776-1826)가 REJECT로 downgrade하고 `fix_scope`를 `"partial"` fallback으로 설정한다.

### Finding 5: Patch escalation 메커니즘이 존재한다

`stage4_interview_round.py:181,1792-1796`:

```python
self._consecutive_empty_patches: int = 0
# missing_patch_targets 시 +1, 그 외 reset
```

`stage4_retry_runtime.py:850-864`:

```python
# [TF-4] missing_patch_targets 연속 시 patch 강제 해제 → full rewrite escalation
_consecutive_empty_patch = (
    not fix_pack_contract.get("ready")
    and fix_pack_contract.get("reason") == "missing_patch_targets"
    and any(pa.get("fix_pack_reason") == "missing_patch_targets" for pa in _prior_attempts[-2:])
)
```

연속 2회 이상 `missing_patch_targets`이면 patch 모드를 해제하고 full rewrite로 전환한다. Patch-bias 방지 메커니즘.

### Finding 6: Patch loop 자체의 제한

`stage4_retry_runtime.py:107`:

```python
max_fix = 3
```

Patch loop는 최대 3회 iteration. 각 iteration마다 `_prepare_pass_with_fix_iteration_gate` → `_run_pass_with_fix_patch_attempt` → `_run_pass_with_fix_patch_guards` → `_capture_pass_with_fix_patch_delta` → `_run_pass_with_fix_reaudit` 순서로 실행한다.

### Finding 7: Live run EP5/EP7 verdict chain이 위 메커니즘을 확인한다

**EP5** (episode_production.jsonl):

| Round | initial_verdict | final_verdict | gate_basis | error_category |
|-------|----------------|---------------|------------|----------------|
| rd=0 | PASS_WITH_FIX | REJECT | post_select_conflict | (→ CONSTRAINT_VIOLATION) |
| rd=1 | PASS_WITH_FIX | REJECT | post_select_conflict | (→ CONSTRAINT_VIOLATION) |
| rd=2 | PASS | PASS | director_primary_pass | — |

EP5 rd=0,1: Director가 PASS_WITH_FIX를 부여했으나 post-select이 capital accounting conflict를 감지 → REJECT override. Patch loop 미진입. 두 번 연속 동일 패턴. rd=2에서 writer가 full generation으로 수치 정합 달성 → PASS.

**EP7** (episode_production.jsonl):

| Round | initial_verdict | final_verdict | gate_basis |
|-------|----------------|---------------|------------|
| rd=0 | PASS_WITH_FIX | PASS | director_primary_pass_with_fix |

EP7 rd=0: Director가 PASS_WITH_FIX ("18년 전" → "전생에" 수정 지시). Post-select clean (conflict 미감지). Patch loop 진입 → 패치 성공 → re-review PASS. 1라운드 내 해결.

---

## 4. Findings Ranked

### R1. Post-select → patch loop 순서는 정확하다 (confirmed)

`stage4_interview_round.py:4018→4035`. Post-select이 먼저 실행되어 hard conflict를 잡고, conflict가 없을 때만 patch loop가 진입한다. 설계 의도대로 작동.

### R2. PASS_WITH_FIX + post-select coexistence는 정상적인 separation of concerns (confirmed)

- Director axis: 원고 내부 표현/산술 오류 감지 (leverage arithmetic, temporal metaphor)
- Post-select axis: cross-episode 상태 모순 감지 (provenance, capital accounting, timeline)
- 두 축은 겹치지 않으며, 동시 발화는 같은 원고에 두 종류의 결함이 공존한다는 뜻이지 아키텍처 결함이 아니다.

### R3. Patch-bias 없음 (confirmed)

세 가지 anti-bias 메커니즘:
1. Post-select downgrade → `repair_scope="full"` 강제 (`stage4_interview_round.py:3750`)
2. Retry routing에서 `force_patch` 차단 (`stage4_retry_runtime.py:870`: `fix_scope != "full"` 조건)
3. TF-4 escalation: 연속 empty patch → full rewrite 전환 (`stage4_retry_runtime.py:850-864`)

### R4. EP5의 2회 연속 PASS_WITH_FIX→REJECT는 retry 결함이 아니라 writer 반복 실패 (confirmed)

EP5 rd=0과 rd=1 모두 Director가 leverage 문제로 PASS_WITH_FIX를 부여했으나, post-select는 별도의 capital accounting 문제를 감지. 이는 writer가 두 라운드 연속으로 동일한 수치 정합 실패를 범한 것이지, retry runtime의 문제가 아니다.

### R5. 잠재적 micro-inefficiency: Director→post-select 정보 단절 (not proven)

Director가 PASS_WITH_FIX를 부여한 시점에서 이미 원고를 "거의 통과"로 평가한 것인데, post-select이 잡은 conflict는 Director가 보지 못한 영역이다. 이론적으로 Director에게 post-select 감지 범위를 알려주면 불필요한 PASS_WITH_FIX 부여를 줄일 수 있으나, 현재 구조에서 실제 피해(wasted cycles)가 0이므로 **not proven as a real problem**.

---

## 5. Cleared Non-Culprits

| 의심 사항 | 판정 | 근거 |
|----------|------|------|
| Patch loop가 post-select conflict 존재 시 낭비 cycle 실행 | **cleared** | L4018→4035 순서로 preemption 확인 |
| Retry가 patch-biased (inplace 선호, hard conflict 무시) | **cleared** | repair_scope="full" 강제 + force_patch 차단 + TF-4 escalation |
| PASS_WITH_FIX + post-select coexistence가 아키텍처 결함 | **cleared** | Separation of concerns 정상 작동, EP5/EP7 live evidence 확인 |
| Retry budget 축이 post-select conflict를 잘못 분류 | **cleared** | error_category 분기 (L3756-3763) POST_SELECT_* 4종 정확 |

---

## 6. Residual Culprit Candidate

이 lane에서 식별된 primary residual culprit는 **없다**.

Retry와 PASS_WITH_FIX semantics는 설계 의도대로 작동하고 있다. Rescue round가 발생하는 근본 원인은 이 lane이 아니라:

- Writer LLM이 반복적으로 동일한 수치/상태 정합 실패를 범하는 것 (T6 lane 범위)
- Blueprint가 잘못된 authority를 제공하는 것 (T4 lane 범위)
- Post-select validator가 과도하게 엄격한지 여부 (T8 lane 범위)

---

## 7. Next-Scope Recommendation

이 lane 단독으로 bounded execution wave를 정당화하지 않는다.

선택적 micro-optimization 후보 (낮은 우선순위, 기록만):

- **[OPT]** EP5 패턴에서 Director가 PASS_WITH_FIX를 부여하기 전에 post-select 결과를 preview하여, hard conflict가 예측되면 PASS_WITH_FIX 대신 바로 REJECT + full feedback을 부여 → Director LLM call 1회 절감. 그러나 현재 구조에서도 wasted patch cycle은 0이므로 순 절감은 Director 판정 비용만큼.

---

## 8. Confidence And Limits

### Confidence: 96%

**높은 확신 영역**:
- Ordering 확인: `stage4_interview_round.py:4018→4035` 직접 읽기 (code-level proof)
- Post-select downgrade 메커니즘: L3745-3750, L3773 직접 확인
- force_patch 차단: `stage4_retry_runtime.py:866-873` 직접 확인
- Live evidence: episode_production.jsonl EP5/EP7 round chain 대조

**제한 영역**:
- `_run_pass_with_fix_patch_guards` 내부 로직은 미정밀 읽기 (patch quality gate 세부)
- retry budget "tot"/"mad" 축이 post-select conflict 이후 어떻게 escalate하는지 전체 흐름은 미추적 (이 lane의 core question에 영향 없음)

---

## Mandatory Final Lines

- Can this lane explain a real residual failure by itself: **no**
- Does this lane explain repeated rescue rounds after the closed waves: **no**
- Would this lane justify a bounded next execution wave: **no**
