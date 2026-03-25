# T5: Validator / Retry / PASS_WITH_FIX Semantics — Evidence Appendix

Date: 2026-03-24
Lane: T5

## E1. Console Gate Trace (File/Line Anchors)

### EP5

```
L1221: 📊 Director 판정: PASS_WITH_FIX (초기: PASS_WITH_FIX, 점수: 92, 선택: 후보 A)
L1225: 판정: PASS_WITH_FIX | 초기: PASS_WITH_FIX | gate: director_primary_pass_with_fix | 점수: 92
L1234: [A-3] Post-select continuity conflict: 제3화에서 시중은행 소속이었던 박성호 PB가 제5화에서는 한미증권 소속
L1236: [A-3] Post-select history conflict: 이전 회차에서 시중은행 본점 소속이었던 박성호 PB가 현재 회차에서 여의도 한미증권 본사
L1238: [TF-3] Provisional PASS → REJECT downgrade: 2 post-select conflicts (continuity, history)
L1293: ❌ [Round 1/10] REJECT → 다음 라운드

L1324: Round 2 — Director REJECT
L1328: 판정: REJECT | 초기: REJECT | gate: director_primary_reject | 점수: 78 | 선택: 후보 A
L1385: ❌ [Round 2/10] REJECT → 다음 라운드

L1427: Round 3 — Director PASS
L1431: 판정: PASS | 초기: PASS | gate: director_primary_pass | 점수: 95 | 선택: 후보 A
L1435: Round 3 PASS!
```

### EP6

```
L1508: Round 1 — Director REJECT
L1512: 판정: REJECT | 초기: REJECT | gate: director_primary_reject | 점수: 75 | 선택: 후보 C
L1545: ❌ [Round 1/10] REJECT → 다음 라운드

[Hidden Round — not visible in console. See E2.]

L1576: Round 2 — Director PASS
L1581: 판정: PASS | 초기: PASS | gate: director_primary_pass | 점수: 90 | 선택: 후보 A
L1585: Round 2 PASS!
L1588: ⚠️ [CoVe] LLM 검증 런타임 실패 → Director PASS 유지
```

### EP7

```
L1661: Round 1 — Director REJECT
L1665: 판정: REJECT | 초기: REJECT | gate: director_primary_reject | 점수: 86 | 선택: 후보 C
L1687: ❌ [Round 1/10] REJECT → 다음 라운드

L1721: Round 2 — Director REJECT
L1725: 판정: REJECT | 초기: REJECT | gate: director_primary_reject | 점수: 75 | 선택: 후보 A
L1768: ❌ [Round 2/10] REJECT → 다음 라운드

L1812: Round 3 — Director PASS
L1817: 판정: PASS | 초기: PASS | gate: director_primary_pass | 점수: 96 | 선택: 후보 A
L1822: Round 3 PASS!
```

## E2. decisions.jsonl Gate Trace

Source: `projects/0324_00_/logs/session/decisions.jsonl`

```
L23 ep=5 R0 stage4 manuscript: REJECT s=93 gate=post_select_conflict fix=inplace fw=False
L24 ep=5 R1 stage4 manuscript: REJECT s=93 gate=post_select_conflict fix=inplace fw=False
L25 ep=5 R2 stage4 manuscript: PASS  s=95 gate=director_primary_pass  fix=inplace fw=False
L26 ep=6 R0 stage4 manuscript: REJECT s=78 gate=director_primary_reject fix=partial fw=False
L27 ep=6 R1 stage4 manuscript: REJECT s=44 gate=continuity_firewall    fix=partial fw=True
L28 ep=6 R2 stage4 manuscript: PASS  s=98 gate=director_primary_pass  fix=inplace fw=False
L29 ep=7 R0 stage4 manuscript: PASS  s=90 gate=patch_reaudit_pass     fix=inplace fw=False
```

### Mismatch Detail: EP5 R1

Console L1328: `gate: director_primary_reject | 점수: 78`
decisions.jsonl L24: `gate=post_select_conflict, s=93`

The decisions.jsonl R1 entry carries R0's gate_basis and score. This suggests the `meta` dict for the decisions.jsonl entry is populated from `previous_attempt` rather than the current round's Director result.

### Mismatch Detail: EP6 Hidden Round

decisions.jsonl L27 records: `R1 REJECT s=44 gate=continuity_firewall fw=True`
This round is completely absent from console output. The V75-C contradiction firewall forced REJECT with score capped at 44 (code: `director_ensemble.py` L1077: `state.score = min(state.score, 44)`).

### Mismatch Detail: EP7 Recording Gap

Console shows 3 rounds (2 REJECT + 1 PASS).
decisions.jsonl has only 1 entry (L29): `R0 PASS s=90 gate=patch_reaudit_pass`.
Missing: R0 REJECT (s=86), R1 REJECT (s=75).
The sole entry has gate `patch_reaudit_pass` which is a PASS_WITH_FIX re-audit gate — but no EP7 round used PASS_WITH_FIX per console.

## E3. episode_production.jsonl Pathology Trace

Source: `projects/0324_00_/logs/episode_production.jsonl`

```
L16: ep=5 R1 STAGE4_RETRY_PATHOLOGY
  pathology_fingerprint: constraint_violation|contradiction:레버리지계산|fix_pack_ready
  reject_bucket: constraint_violation
  gate_basis: post_select_conflict
  score: 93
  provisional_pass_downgrade: False

L18: ep=5 R2 STAGE4_RETRY_PATHOLOGY
  pathology_fingerprint: constraint_violation|contradiction:수치|fix_pack_ready
  reject_bucket: constraint_violation
  gate_basis: post_select_conflict
  score: 93
  plateau_detected: True

L21: ep=6 R1 STAGE4_RETRY_PATHOLOGY
  pathology_fingerprint: constraint_violation|contradiction:타임라인|fix_pack_ready
  reject_bucket: constraint_violation
  gate_basis: director_primary_reject
  score: 83

L23: ep=6 R2 STAGE4_RETRY_PATHOLOGY
  pathology_fingerprint: post_select_conflict|contradiction:자본금정합|continuity_firewall|fix_pack:missing_fix_pack
  reject_bucket: post_select_conflict
  gate_basis: continuity_firewall
  firewall_triggered: True
  score: 69

L25: ep=6 STAGE4_COVE_RUNTIME_ADVISORY
  source: llm_verify
  error_type: ChainOfVerificationParseError
  error_message: JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  director_pass_preserved: True
  quick_warning: 직전 화 아이템(패)이 현재 화에서 언급되지 않음
```

### Note on ep_production pathology score vs decisions score for EP6 R2

episode_production says score=69, decisions.jsonl says score=44. The difference: episode_production records `pre_firewall_score` (69) while decisions records the post-cap score (`min(score, 44)` → 44). Both are consistent with the V75-C firewall behavior.

## E4. Code Gate Flow Anchors

### post_select_conflict Flow

```
stage4_interview_round.py:
  L4000  _run_positive_verdict_transition()
  L4018    calls _run_post_select_checks() FIRST
  L4035    then _execute_pass_with_fix_loop() IF still PASS_WITH_FIX

  L3635  _run_post_select_checks()
  L3663    _run_continuity = next_ep > 1 and final_manuscript
  L3675    ThreadPoolExecutor(max_workers=2)
  L3680      Future: check_manuscript_continuity_with_cache
  L3693      Future: check_manuscript_history_conflicts
  L3707    if decision == "CONFLICT" → append to _post_select_conflicts
  L3732    if conflicts exist → verdict = "REJECT", gate_basis = "post_select_conflict"
  L3773    previous_attempt["fix_scope"] = "full"
  L3791    previous_attempt["provisional_pass_downgrade"] = True
```

### continuity_firewall Flow

```
director_ensemble.py:
  L1041  if critical_count >= 1 or major_count >= 2:
  L1042    classify firewall_mode (pass_with_fix vs reject)
  L1053    if firewall_mode == "pass_with_fix" → fixable path (score capped 97)
  L1065    else → firewall_triggered = True
  L1074    if firewall_triggered:
  L1075      state.original_verdict = "REJECT"
  L1077      state.score = min(state.score, 44)
  L1293    gate_basis = _derive_gate_basis(firewall_triggered=True) → "continuity_firewall"
```

### PASS_WITH_FIX Contract Enforcement

```
stage4_interview_round.py:
  L1776  _enforce_pass_with_fix_contract()
  L1781    if final_verdict != "PASS_WITH_FIX" → skip
  L1784    contract = _evaluate_pass_with_fix_contract(normalized)
  L1785    if eligible → fix_scope = "inplace"
  L1797    if not eligible → downgrade to REJECT, gate = "pass_with_fix_contract_{reason}"
```

## E5. Patch Mode Engagement Evidence

```
Console anchors:
EP5 R2  L1298: 🔧 [TF-23] InPlace: fix_scope='inplace', score=92 → REJECT 78
EP5 R3  L1390: 🔧 [Phase 3-5B] 패치 모드: score=83
        L1391: 🔥 [ASP] 레드팀 교정 발동 (재시도 3회차) → PASS 95
EP6 R2  L1550: 🔧 [Phase 3-5B] 패치 모드: score=80 → PASS 90
EP7 R2  L1692: 🔧 [Phase 3-5B] 패치 모드: score=86 → REJECT 75
EP7 R3  L1773: 🔧 [Phase 3-5B] 패치 모드: score=78
        L1774: 🔥 [ASP] 레드팀 교정 발동 (재시도 3회차) → PASS 96
```

Pattern: Patch fails on structural issues (R2) → ASP red-team succeeds (R3).
ASP triggers at Round 3 unconditionally (`재시도 3회차`).

## E6. CoVe Runtime Failure (EP6)

```
Console L1587: ⚠️ [CoVe] 사후검증 경고: 직전 화 아이템(패)이 현재 화에서 언급되지 않음
Console L1588: ⚠️ [CoVe] LLM 검증 런타임 실패 → Director PASS 유지

episode_production L25:
  event: STAGE4_COVE_RUNTIME_ADVISORY
  error_type: ChainOfVerificationParseError
  error_message: JSONDecodeError: Expecting value: line 1 column 1 (char 0)
  director_pass_preserved: True
```

CoVe (Chain of Verification) attempted post-PASS validation but LLM returned unparseable response. System preserves Director PASS rather than failing closed. The quick_warning ("직전 화 아이템(패)이 현재 화에서 언급되지 않음") indicates a potential real issue was detected by the Python pre-check but the LLM verification step failed at parse time.

**Risk**: CoVe runtime failures are fail-open (PASS preserved), which means a broken verifier cannot block a flawed manuscript. However, this is by design — CoVe is advisory-only and the Director PASS is the authoritative verdict.
