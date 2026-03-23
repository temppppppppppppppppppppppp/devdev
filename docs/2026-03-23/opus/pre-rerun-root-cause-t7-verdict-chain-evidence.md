Date: 2026-03-23
Document Type: evidence manifest (T7)
Terminal: T7
Focus: Director verdict and post-select static chain
Parent Report: `docs/2026-03-23/opus/pre-rerun-root-cause-t7-verdict-chain.md`

---

## Source Files Inspected

| File | Method | Lines Inspected | Evidence Type |
|------|--------|-----------------|---------------|
| `modules/domain/agents/director_ensemble.py` | Sub-agent deep exploration | Full file (~1400 lines) | source |
| `modules/domain/agents/director_auditor.py` | Direct read | L1-100 | source |
| `modules/core/stage4_director_runtime.py` | Sub-agent deep exploration | Full file (~1517 lines) | source |
| `modules/core/stage4_post_pass_runtime.py` | Sub-agent deep exploration | Full file (~1342 lines) | source |
| `modules/core/stage4_outcome_runtime.py` | Sub-agent deep exploration | Full file (~942 lines) | source |
| `modules/core/stage4_interview_round.py` | Direct read + grep | L3572-3721, L3751-3940 | source |

## Console Evidence (Arc 1 Episode 3)

| Round | Console Lines | Director Verdict | Score | Candidate | Gate Basis | Post-Select | Final Outcome |
|-------|--------------|------------------|-------|-----------|------------|-------------|---------------|
| 1 | 727-746 | REJECT | 80 | C | director_primary_reject | N/A | REJECT |
| 2 | 751-753 | (all candidates failed) | N/A | N/A | N/A | N/A | REJECT |
| 3 | 810-831 | REJECT | 76 | A | director_primary_reject | N/A | REJECT |
| 4 | 893-913 | PASS | 98 | A | director_primary_pass | 2 conflicts (timeline 1/17 vs 1/18) | REJECT (downgrade) |
| 5 | 961-989 | PASS | 98 | A | director_primary_pass | 0 conflicts | PASS (accepted) |

## Key Console Anchors

### Round 1 Director Verdict (L727-737)
```
📊 Director 판정: REJECT (초기: REJECT, 점수: 80, 선택: 후보 C)
사유: Blueprint에 명시된 5개의 씬 구분이 원고에 전혀 반영되지 않았음
```

### Round 4 Post-Select Downgrade (L902-913)
```
[A-3] Post-select continuity conflict: 아버지와의 독대는 1월 18일 저녁에 이루어졌어야 하나,
제3화에서는 1월 17일 저녁으로 잘못 기재
[A-3] Post-select history conflict: 1월 18일 저녁으로 확정된 '아버지와의 독대' 사건이,
제3화 씬 1에서는 1월 17일 저녁에 일어난 것으로 잘못 표기
[A-3] 2 post-select conflicts detected -> downgrade to REJECT
```

### Round 5 Final PASS (L961-989)
```
📊 Director 판정: PASS (초기: PASS, 점수: 98, 선택: 후보 A)
사유: 후보 A는 이전 2화의 타임라인(1월 18일 저녁 독대)을 정확히 계승
✅ [Round 5] PASS
```

### Persistent Scene Detection False Positive (all rounds)
```
[HIGH] 씬 완성도 부족: 0/5 씬만 완성 (최소 50% 필요)
```
Present on ALL candidates, ALL rounds, including final PASS candidate.

### Persistent NPC Drift Advisory (all rounds)
```
[MAJOR] NPC '한정호' relation_to_protag: 기대='목격자' → 원고='적대자/감시자'
```
Present on ALL candidates, ALL rounds. Advisory-only, correctly non-blocking.

## Cross-Reference Documents

| Document | Key Finding Used | Agreement with T7 |
|----------|-----------------|-------------------|
| `director-pipeline-7axis-deep-dive.md` | H-1 rejection_reason field loss, H-2 contradiction 5→3 compression, H-3 verdict_reason 500char truncation | Confirmed still live in source |
| `q1-q8-current-state-merge-audit.md` | Q3 "LLM-Director 정합성 불일치" as pre-rerun priority | T7 reframes as "designed divergence, not consistency failure" |
| `fresh-run-3pass-audit-report.md` | P1-1 V60.97 swap, P1-3 length issue | Confirmed V60.97 not triggered in 0_0323 Ep3 run |

## Gate Chain Source Anchors

| Gate | File | Lines | Status |
|------|------|-------|--------|
| LLM Primary | director_ensemble.py | L2106-2220 | Verified |
| V60.97 Swap | director_ensemble.py | L907-947 | Verified, not triggered in Ep3 |
| SCM Cap | director_ensemble.py | L1005-1021 | Verified |
| Contradiction Firewall | director_ensemble.py | L1023-1090 | Verified, not triggered in Ep3 |
| NC-3 Penalty | director_ensemble.py | L1124-1157 | Verified |
| Adaptive Threshold | director_ensemble.py | L1159-1212 | Verified |
| Quality Floor | stage4_interview_round.py | L3772-3784 | Verified, not triggered (score 98 >= 90) |
| Post-Select Checks | stage4_interview_round.py | L3572-3721 | Verified, triggered Round 4 |
| CoVe Verification | stage4_outcome_runtime.py | L71-118 | Verified, not triggered |
| Post-Pass Atomic Save | stage4_post_pass_runtime.py | L1070-1118 | Verified, succeeded Round 5 |

## Dirty Workspace Diff Summary

`director_ensemble.py` modifications:
- `_NC3_CHECKLIST_KEYS` constant extracted to module level (L53-74)
- `_apply_ensemble_quality_gates()` refactored to call 4 sub-methods (L989-1003)
- 4 new methods extracted: `_apply_scm_single_candidate_cap`, `_apply_contradiction_firewall_gate`, `_log_numeric_consistency_gate`, `_apply_nc3_consistency_penalty`
- Logic unchanged, pure structural refactor
