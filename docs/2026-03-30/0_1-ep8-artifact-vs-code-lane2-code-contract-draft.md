# EP8 Code Contract / Retry Lane Survey — Lane 2

Date: 2026-03-30
Status: draft-bounded-partial-evidence
Document Type: lane survey report (read-only)
Track: system
Terminal: 2
Master Order: `docs/2026-03-30/0_1-ep8-artifact-vs-code-parallel-master-order.md`
Baseline Commit: `92ba1cf7`

## 1. Coverage

Core investigation files read:

| File | Lines Read | Purpose |
| --- | --- | --- |
| `modules/core/stage4_interview_round.py` | L545-556, L825-866, L1770-1940, L1970-2070, L2810-2878, L2987-3080, L3905-4044, L4104-4186, L4187-4265, L4267-4333, L5473-5522 | verdict flow, Lane3 Gate, advisory escalation, post-select checks, reject_bucket classification |
| `modules/core/stage4_retry_runtime.py` | L84-328, L830-1055 | retry lane routing, PASS_WITH_FIX loop, patch/rewrite lane selection |
| `modules/core/stage4_reject_runtime.py` | L49-465 | reject guidance, retry snapshot, scope resolution |
| `modules/core/stage4_outcome_runtime.py` | L17-200 | CoVe pass verification (not directly implicated) |
| `modules/core/stage4_immutable_fact_contract.py` | L1-100 | IFC violation families, rewrite escalation |
| `0_temp.txt` | L301-814 | EP8 round-by-round terminal evidence |
| `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_*` | directory listing | 5 attempts persisted on disk |

## 2. Findings

### FINDING-C1: Lane2-G1 → Lane3 Gate Seam Gap (Attempts 1-4)

**Severity**: Contract defect (wastes budget, not a crash)

**Exact seam**:
- `stage4_interview_round.py:2009-2028` — Lane2-G1 strong advisory binding
- `stage4_interview_round.py:1889-1939` — `_enforce_pass_with_fix_contract`

**Mechanism**:

1. Director returns `PASS` (score 95-96) for all 4 attempts.
2. `_STRONG_ADVISORY_KEYS` check at L2012-2014 finds NpcDrift triggered → escalates `PASS` → `PASS_WITH_FIX` (L2016-2024).
3. `_enforce_pass_with_fix_contract` at L1889 runs `_evaluate_pass_with_fix_contract` at L1830.
4. `_evaluate_fix_pack_contract` at L1811 checks `patch_targets` (L1815-1816) — empty because the Director never populated a fix_pack (it said `PASS`, not `PASS_WITH_FIX`).
5. Contract fails with `reason="missing_patch_targets"` → verdict downgraded to `REJECT` at L1933-1938.
6. Gate basis: `pass_with_fix_contract_missing_patch_targets`.

**Evidence from `0_temp.txt`**:
```
L353: 📊 Director 판정: REJECT (초기: PASS, 점수: 95, 선택: 후보 A)
L354: └─ 사유: [Lane3 Gate] PASS_WITH_FIX downgraded: Fix Pack patch_targets is empty
L358: gate: pass_with_fix_contract_missing_patch_targets
```

Same pattern repeats identically at L414 (attempt 2), L505 (attempt 3), L629 (attempt 4).

**Root cause**: Lane2-G1 escalates PASS → PASS_WITH_FIX **without synthesizing a fix_pack from the advisory findings**. Lane3 Gate then always rejects because it requires a valid fix_pack. The advisory escalation is structurally incompatible with the PASS_WITH_FIX contract.

**Impact**: Attempts 1-4 all loop through the same hopeless cycle: Director says PASS → advisory escalates → Lane3 Gate rejects → rewrite. The retry feedback carries PASS_WITH_FIX contract failure messages instead of actionable advisory-specific fix guidance. The NpcDrift finding (박성호 role) is real, but the code path cannot convert it into a usable fix instruction.

**Design intent assessment**: This appears to be **intended fail-closed** behavior (better to reject than pass with a known advisory issue). However, the fail-closed design has a budget leak: it burns 4 rounds before the first fundamentally different attempt, and TF-4 `_consecutive_empty_patch` only fires from attempt 3 onward (L449, L580, L678 in `0_temp.txt`).

---

### FINDING-C2: Post-Select Conflict Scope Leak (Attempt 5 → Attempt 6)

**Severity**: Contract defect (scope information lost, wrong retry lane entered)

**Exact seam**:
- `stage4_interview_round.py:3981-4044` — `_run_post_select_checks` builds `previous_attempt` with `fix_scope="full"`, `reject_bucket="post_select_conflict"` (L4023, L4030, L4042)
- `stage4_interview_round.py:2073-2093` — `_apply_director_gate_update` sets `repair_scope="full"` but does NOT set `fix_scope="full"` (L2089-2090 vs absent `fix_scope` parameter)
- `stage4_reject_runtime.py:497` — `_build_reject_guidance_payload` reads `resolved_fix_scope = director_result.get("fix_scope")` — gets Director's original "inplace", not the post-select "full"
- `stage4_reject_runtime.py:558-560` — `if reject_bucket == "post_select_conflict"` guard that SHOULD force `resolved_fix_scope = "full"` but doesn't fire because `reject_bucket` is "constraint_violation"

**Mechanism**:

1. Director returns `PASS_WITH_FIX` (initial=PASS_WITH_FIX, score 93, 후보 C) for attempt 5. The fix is for '18년 전 과거의 기억' (시점 모순). Director provides `fix_scope="inplace"` with fix_pack targeting local phrase correction.
2. Post-select checks at L3920-3979 find a continuity conflict: 계좌 잔고 4.71억 원 → 5억 원 불일치.
3. `_apply_director_gate_update` at L3996-4001 downgrades to REJECT, sets `repair_scope="full"`, `gate_basis="post_select_conflict"`. But `director_result["fix_scope"]` remains "inplace" (only `repair_scope` is updated, not `fix_scope`).
4. `_run_post_select_checks` builds `previous_attempt` with `fix_scope="full"` and `reject_bucket="post_select_conflict"` (L4023-4044).
5. Control flows to `_finalize_round_reject_path` → `handle_reject` → `_build_reject_guidance_payload`.
6. At L497: `resolved_fix_scope = str(director_result.get("fix_scope", ""))` → `"inplace"` (from Director's pre-downgrade PASS_WITH_FIX).
7. At L492: `reject_bucket = owner._classify_reject_bucket(...)` → `"constraint_violation"` (see FINDING-C3).
8. At L500-505: `_is_continuity_replay_reject` returns `False` because `director_result["firewall_triggered"]` is not set (post-select checks don't set it; only Director's internal firewall does).
9. At L558: `if reject_bucket == "post_select_conflict":` → `False`. The `resolved_fix_scope = "full"` override doesn't fire.
10. At L570: `if resolved_fix_scope == "inplace":` checks fix_pack. If Director provided a valid fix_pack for the '18년 전' fix, resolved_fix_scope stays "inplace".
11. `_build_reject_retry_snapshot` at L404: `"fix_scope": resolved_fix_scope` → "inplace".
12. Next round (attempt 6) enters InPlace mode for the wrong issue.

**Evidence from `0_temp.txt`**:
```
L729: 📊 Director 판정: PASS_WITH_FIX  (초기: PASS_WITH_FIX, 점수: 93, 선택: 후보 C)
L743: [TF-3] Provisional PASS → REJECT downgrade: 1 post-select conflicts (continuity)
L785: 🔧 [TF-23] InPlace: fix_scope='inplace', score=93
```

**Impact**: Attempt 6 enters InPlace mode trying to fix the '18년 전' phrase, while the more fundamental issue (계좌 잔고 continuity conflict) requires a full rewrite. The post-select conflict's scope override (`fix_scope="full"`) is constructed but then overwritten by the reject guidance pipeline, which re-derives scope from the Director's pre-downgrade response.

---

### FINDING-C3: `_classify_reject_bucket` Vocabulary Gap

**Severity**: Design gap (contributes to FINDING-C2)

**Exact seam**: `stage4_interview_round.py:545-556`

```python
def _classify_reject_bucket(*, director_feedback, feedback, action_items):
    ...
    if any(key in reject_lower for key in ("constraint", "consistency", "conflict", ...)):
        return "constraint_violation"
    if any(key in reject_lower for key in ("structure", "structural", ...)):
        return "structure_error"
    return "quality_issue"
```

This function returns one of three values: `"constraint_violation"`, `"structure_error"`, `"quality_issue"`. It **never** returns `"post_select_conflict"`.

The `"post_select_conflict"` bucket is only assigned via:
1. `_is_continuity_replay_reject` at L500-505 — requires `director_result["firewall_triggered"] == True`
2. Explicit assignment in `_run_post_select_checks` at L4042 — goes into `previous_attempt["reject_bucket"]`, NOT into the reject guidance pipeline's `reject_bucket`

For post-select conflicts (which are NOT Director firewall triggers), the reject_bucket falls to `_classify_reject_bucket`, which returns `"constraint_violation"` due to the word "conflict" in the feedback. The scope override at L558-560 (`if reject_bucket == "post_select_conflict": resolved_fix_scope = "full"`) then never fires.

---

### FINDING-C4: `_consecutive_empty_patches` Reset on Positive Verdict Entry

**Severity**: Minor (observable in attempts 1-4 behavior)

**Exact seam**: `stage4_interview_round.py:4155`

```python
if verdict in ("PASS", "PASS_WITH_FIX"):
    self._consecutive_empty_patches = 0  # [IFC] reset on positive verdict
```

When Director gives PASS (then escalated to PASS_WITH_FIX by advisory), this line resets the consecutive empty patch counter. Even though the PASS_WITH_FIX contract will fail and produce REJECT, the counter was already reset at entry.

This means the TF-4 consecutive empty patch detection (`_resolve_retry_lane_routing` L856-869) sees a broken count: the counter was reset before the contract failure re-incremented it. This is why TF-4 first fires at attempt 3 (round 3), not attempt 2 (round 2) — the counter needs 2 consecutive failures, but each time it's reset at entry before the failure occurs.

However, since attempts 1-4 all end up in full rewrite anyway (TF-PATCH-GATE or TF-4), this has no visible impact on the routing outcome. It's a correctness issue for the counter, not a behavioral bug.

## 3. Non-Issues

1. **Attempt 5 provisional PASS_WITH_FIX → REJECT is correct behavior**: The post-select continuity check correctly detected a genuine 계좌 잔고 conflict. The downgrade itself is working as designed. The problem is only in the propagation of scope information to the retry pipeline.

2. **CoVe pass verification**: Not implicated. Post-select checks run before CoVe, and the issue is upstream.

3. **Advisory chain parallelism**: Working correctly. 8-9 advisories run in parallel, returning within 60s. NpcDrift and FlashbackVerifier correctly detect real issues.

4. **Stage4OutcomeRuntime**: Not implicated in EP8's failure path. The outcome runtime only handles accepted PASS results.

5. **ASP (Adversarial Self-Play)**: Firing correctly from round 3+ (L450, L581, L679). Not contributing to the failure cycle.

## 4. Verdict

**code-first**

Attempts 1-4 fail due to a structural seam gap between Lane2-G1 (strong advisory escalation) and Lane3 Gate (PASS_WITH_FIX contract). The advisory escalation produces a verdict state (PASS_WITH_FIX without fix_pack) that the contract gate can never accept, resulting in 4 rounds of wasted budget.

Attempt 5 reaches a genuinely different state (Director explicitly gives PASS_WITH_FIX for a real artifact issue), but the post-select conflict scope override is lost through a contract propagation defect. The next attempt (6) enters the wrong retry lane.

The artifact-level issues (박성호 role drift, '18년 전' 시점 모순, 계좌 잔고 불일치) are real but secondary: even if the artifacts were perfect, the Lane2-G1 → Lane3 Gate seam gap would still produce the same 4-round failure cycle for any episode where a tier-2+ advisory triggers on a Director PASS.

**Primary blockers** (code):
1. FINDING-C1: Lane2-G1 advisory escalation without fix_pack synthesis → hopeless retry cycle
2. FINDING-C2: Post-select conflict scope leak → wrong retry lane in subsequent round

**Secondary blockers** (artifact, observed but not root cause):
1. 박성호 NPC role drift (SW인베스트먼트 전담 PB vs 한미증권 파생상품 데스크)
2. '18년 전 과거의 기억' 시점 모순 (2006년 현재 vs 2024년 기준)
3. 계좌 잔고 수치 불일치 (4.71억 vs 5억 원)

## 5. Stop

read-only lane complete; no files mutated
