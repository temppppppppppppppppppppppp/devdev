Date: 2026-03-24
Status: final
Document Type: evidence ledger (T8 lane)
Canonical Path: `docs/2026-03-24/opus-residual/t8-stage4-contradiction-detection-evidence.md`

---

# T8 Evidence Ledger — Stage 4 Contradiction Detection

## E1. Detection Architecture Code Anchors

### Post-select continuity check
- File: `modules/core/stage4_interview_round.py:3611-3784`
- Method: `_run_post_select_checks()`
- Runs two parallel LLM checks via `ThreadPoolExecutor(max_workers=2)`:
  - `check_manuscript_continuity_with_cache`: Director agent's cached continuity check (L3656-3664)
  - `check_manuscript_history_conflicts`: Director agent's history conflict check (L3666-3677)
- Downgrade logic (L3708-3782): If conflicts found, verdict→REJECT, gate_basis→"post_select_conflict"
- Error categories set: POST_SELECT_CONTINUITY_CONFLICT, POST_SELECT_HISTORY_CONFLICT, POST_SELECT_CONTINUITY_AND_HISTORY

### Continuity replay detection
- File: `modules/core/stage4_interview_round.py:714-754`
- Method: `_is_continuity_replay_reject()`
- Checks `firewall_triggered` flag AND intersection with continuity_types set
- Continuity types: scene_overlap, event_ordering, space_continuity, timeline_arc_consistency, opening_diversity
- Text markers: "continuity conflict", "history conflict", "같은 사건", "같은 장면", etc.

### Reject guidance with IFC
- File: `modules/core/stage4_reject_runtime.py:438-494`
- On `_is_continuity_replay_reject()` → error_category="LOGIC_ERROR", fix_scope escalated to "partial"
- IFC violation classification (L458-494): classify_violation_family → should_escalate_to_rewrite
- Rewrite escalation: if hard-fact family + empty patches → escalate to partial/full

### V75-D blueprint patch path
- File: `modules/core/stage4_orchestrator.py:1662-1873`
- Method: `_run_v75d_patch_attempt()`
- Trigger: `logic_error_streak >= v75d_threshold` (1 if quality_risk, else 2)
- Sequence: V75-D inplace → V75-B regeneration if inplace fails
- File: `modules/core/stage4_outcome_runtime.py:730-789`
- V75-D threshold logic: quality_risk flag from `blueprint._stage3_meta`

## E2. 00_001 Episode Production Timeline

### Complete ep3 rejection chain
```
L3 (ep3 R1 selection):  PASS s=95, gate=post_select_conflict → downgraded
L4 (ep3 R1 summary):    ep_num=3, bkt=constraint_violation, gate=post_select_conflict, err=CONSTRAINT_VIOLATION
L5 (ep3 R2 selection):  REJECT s=44, gate=continuity_firewall, reason="Contradiction Firewall: CRITICAL 1건"
L6 (ep3 R2 summary):    ep_num=3, bkt=structure_error, fw=True, gate=continuity_firewall, err=LOGIC_ERROR
L7 (ep3 final):         PASS (recovered via V75-D)
L8 (ep3 R3 selection):  PASS s=95, gate=director_primary_pass
```

### Complete ep4 rejection chain
```
L9  (ep4 R1 selection): REJECT s=30, gate=continuity_firewall, reason="Contradiction Firewall: CRITICAL 2건"
L10 (ep4 R1 summary):   ep_num=4, bkt=structure_error, fw=True, gate=continuity_firewall, err=LOGIC_ERROR
L11 (ep4 intermediate): -
L12 (ep4 R2 selection): PASS s=96, gate=post_select_conflict
L13 (ep4 R2 summary):   ep_num=4, bkt=constraint_violation, gate=post_select_conflict, err=CONSTRAINT_VIOLATION
L14 (ep4 R3 selection): PASS s=95, gate=director_primary_pass
```

### Complete ep5-7 rejection chain
```
EP5 R1: REJECT s=80, gate=director_primary_reject, reason="EP 4와의 타임라인 모순 (이란 선언 시점)"
EP5 R2: PASS s=90
EP6 R1: PASS s=96 → post_select_conflict (constraint_violation)
EP6 R2: PASS_WITH_FIX s=93, reason="OTP 액정에 표시된 잔고가... 38억 원이 아닌 20억 원으로 잘못 표기됨"
EP6 R3: PASS s=96
EP7 R1: PASS s=95 → post_select_conflict (constraint_violation)
EP7 R2: PASS s=90
```

## E3. Blueprint Contamination Delta

### 00_001 (pre-Wave-1) — EP1 ending_state overconsumption
```json
{
  "location": "재벌가 본가 저택 침실 내부 (방문 앞)",
  "protagonist_status": "자본금 20억 확보 및 법인 설립을 완료하고 첫 투자를 목전에 둔 상태",
  "timeline": {"표현": "2006년 1월 하순, 저녁"}
}
```
EP1 consumed: 20억 확보 + 법인 설립 + 첫 투자 준비 → These are EP3-4 content.

### 00_0324 (post-Wave-1) — EP1 ending_state properly scoped
```json
{
  "location": "서울 성북동 본가 저택 한시우의 침실 문 앞",
  "protagonist_status": "감정을 완벽히 통제하고 가족 대면을 준비하는 상태",
  "timeline": {"표현": "2006년 1월 12일 저녁 식사 직전"}
}
```
EP1 stays within scope: awakening + emotional control + family preparation.

### 00_0324 (post-Wave-1) — EP4 correctly receives the 20억 content
```json
{
  "location": "서울 강남 PB센터 VIP룸 문 앞",
  "protagonist_status": "자산 현금화 완료, 다음 투자(법인 설립)를 위해 이동할 준비가 된 상태",
  "timeline": {"표현": "2006년 1월 13일 오전"}
}
```
EP4 contains: 자산 현금화 + 법인 설립 이동 → Correct temporal allocation.

## E4. IFC Violation Family Vocabulary

From `stage4_immutable_fact_contract.py:24-29`:
- `opening_anchor_drift` — start location/time changed
- `committed_state_regression` — numeric/state values contradict committed facts
- `completed_event_replay` — already-finished events replayed as unresolved
- `scene_obligation_missing` — blueprint scene not materialized
- `scene_order_drift` — scene sequence changed
- `metadata_reference_shape_violation` — dict witness in scalar sink

Hard-fact families (L31-37): opening_anchor_drift, committed_state_regression, completed_event_replay
Rewrite-biased families (L39-46): above + scene_order_drift

## E5. Detection Effectiveness Summary

| Detection Layer | EP3 R1 | EP3 R2 | EP4 R1 | EP5 R1 | EP6 R2 |
|---|---|---|---|---|---|
| Director primary | PASS (missed) | — | — | REJECT (caught) | PASS_WITH_FIX |
| Post-select check | REJECT (caught) | — | — | — | — |
| Continuity firewall | — | REJECT CRITICAL 1 | REJECT CRITICAL 2 | — | — |
| V75-D recovery | — | triggered | triggered | — | — |

- Post-select caught what Director missed on EP3 R1
- Firewall caught CRITICAL contradictions on EP3 R2 and EP4 R1
- Director caught timeline mismatch on EP5 R1
- V75-D recovered by patching blueprints after LOGIC_ERROR streaks
