Date: 2026-03-23
Document Type: T1 Runtime / Artifact Flow evidence manifest
Parent Report: `docs/2026-03-23/opus/rol-live-merge-t1-runtime-artifact.md`

## Evidence Index

### Static Source Inspections

| File | Lines Inspected | Purpose |
|---|---|---|
| `modules/validation/blocking_validator_scene_checks.py` | 128-256 | Scene header regex, keyword fallback, completeness threshold |
| `modules/domain/agents/chief_writer_context.py` | 170-299 | Blueprint section extraction, opening anchor packet (TF-2) |
| `modules/domain/agents/chief_writer_prompts.py` | 62-148 | Prompt template: scene_breakdown, prev_ending, opening_anchor_section slots |
| `modules/core/writer_template.py` | 100-180 | ManuscriptTemplate and SceneSlot generation |
| `modules/core/stage4_interview_round.py` | 60-73, 318-420, 647-670, 1601-1682, 3575-3729, 3780-3810, 5630-5670 | Retry directives, fix-pack evaluation, post-select checks, verdict processing, failure category assignment |
| `modules/domain/agents/director_ensemble.py` | 942-1210 | CONDITIONAL_PASS handling, ensemble quality gates |

### Live Artifact Inspections

| Path | What was checked |
|---|---|
| `projects/0_0323/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__action_focused.json` | scene_count=5, start_location, time_flow metadata |
| `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_01/rejected_best__C.txt` | No scene headers found |
| `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_03/rejected_best__A.txt` | 5 scene headers present (`### 씬 1:` through `### 씬 5:`) |
| `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_05/selected_candidate__A.txt` | 5 scene headers present; opens at 유성그룹 회장 자택, 2006년 1월 18일 저녁 |
| `projects/0_0323/logs/artifacts/stage4/ep_0003/attempt_05/patched_after_fix__A.txt` | Same as selected_candidate (patched version) |
| `projects/0_0323/drafts/ep_0001.txt` | No scene headers |
| `projects/0_0323/drafts/ep_0002.txt` | No scene headers |
| `projects/0_0323/drafts/ep_0003.txt` | 5 scene headers present |

### Console Evidence

| Line Range | Signal |
|---|---|
| 496-498 | Ep1 Round 1: `0/5 씬만 완성` on candidates A and B |
| 526 | Ep1 Round 1: Director PASS score 96 |
| 566-571 | Ep2 Round 1: `0/5 씬만 완성` on all 3 candidates |
| 606 | Ep2 Round 1: Director PASS score 95 |
| 651-654 | Ep3 Round 1: `0/5 씬만 완성` on candidates 1 and 2 |
| 690 | Ep3 Round 1: Director REJECT score 44 (continuity firewall) |
| 731-732 | Ep3 Round 2: `0/5 씬만 완성` on candidate 1 |
| 753 | Ep3 Round 2: Director PASS_WITH_FIX score 90 |
| 765-771 | Ep3 Round 2: post-select continuity+history conflict -> downgrade to REJECT |
| 857-860 | Ep3 Round 3: `0/5 씬만 완성` on candidates 1 and 2 |
| 888 | Ep3 Round 3: Director PASS score 95 |
| 897-900 | Ep3 Round 3: post-select history conflict -> downgrade to REJECT |
| 901 | Ep3 Round 3: `Fix Pack patch_targets is empty` |
| 994-997 | Ep3 Round 4: `0/5 씬만 완성` on candidates 1 and 2 |
| 1025 | Ep3 Round 4: Director PASS score 95 |
| 1034-1037 | Ep3 Round 4: post-select history conflict (timeline: 어제 vs same-day) |
| 1061 | Ep3 Round 4: `Fix Pack patch_targets is empty` |
| 1135-1137 | Score plateau detected; TF-29 constraint violation 3 consecutive |
| 1144 | User stop requested |
| 1162 | System shutdown sequence |

### Independent Verification

| Test | Result |
|---|---|
| Scene header regex (`^#{1,3}\s+씬\s*(\d+)\s*[:\-]?\s*(.*)`) against `### 씬 1: 보이지 않는 감시망` | Match confirmed |
| Ep3 attempt_05 opening text vs blueprint start_location | Consistent (유성그룹 회장 자택) |
| Ep3 attempt_05 opening time vs blueprint time_flow | Consistent (2006년 1월 18일 저녁, within blueprint range) |
