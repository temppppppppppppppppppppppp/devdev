Date: 2026-03-23
Status: final
Document Type: evidence manifest
Terminal: T5
Focus: Stage 4 write/fix/retry code chain
Canonical Path: `docs/2026-03-23/opus/pre-rerun-root-cause-t5-stage4-write-fix-evidence.md`

---

# T5 Evidence Manifest

## 1. Source Code Anchors

### stage4_interview_round.py (5,917 lines)

| Finding | Line(s) | Evidence |
|---|---|---|
| F-1 EMPTY 처리 | L2060-2099 | `"모든 후보 생성 실패"` → `previous_attempt = {strategy: "none", score: 0}` |
| F-2 retry_feedback_provenance | L572-670 | 5-section merged_feedback 조립: system_feedback + evidence_summary + director_feedback_text + retry_directives + runtime_advisory |
| F-3 _compact_text 절삭 | L459 | `def _compact_text(value, limit=500)` — 기본 500자 |
| F-3 verdict_reason 절삭 | L5367-5368 | `(verdict_reason or selection_reason)[:500]` |
| F-3 reason 절삭 | L399-403 | `reason=self._compact_text(reason, limit=500)` + 5개 필드 동일 |
| F-3 feedback_provenance 절삭 | L5460-5462 | DB 저장용 director_feedback/runtime_advisory/retry_directives 각 500자 |
| F-4 A-3 downgrade 스냅샷 | L3693-3720 | `provisional_pass_downgrade=True`, `fix_scope` escalation, `error_category="LOGIC_ERROR"` |
| F-5 retry_directives 평탄화 | L649 | `retry_directives = " / ".join(prev_general_lines)` |
| F-6 EMPTY 스냅샷 | L2071-2079 | `score=0, action_items=[], strategy="none"` |
| F-8 prior_attempts 제한 | L1169-1202 | 중복 제거 후 `[-3:]` 절삭 |

### stage4_retry_runtime.py (1,076 lines)

| Finding | Line(s) | Evidence |
|---|---|---|
| F-1 관련 generate_candidates | L238-328 | Retry lane routing → patch/rewrite/inplace |
| F-1 관련 PASS_WITH_FIX loop | L90-236 | max_fix=3, 6단계 gate pipeline |
| Patch guard limits | L478, L500 | min_patched_length=2000, inplace_min_preserve_ratio=0.70 |
| Fallback recovery | L920-949 | _run_inplace_retry_lane fallback to patch_or_rewrite |

### stage4_reject_runtime.py (820 lines)

| Finding | Line(s) | Evidence |
|---|---|---|
| F-7 contradiction_details | L366 | `[:5]` — 현재 상태 |
| H-1 rejection_reason (stale) | L342 | `director_result.get("verdict_reason") or director_feedback` — 이미 수정됨 |
| Reject bucket classification | L417-421 | `_classify_reject_bucket()` → 3-category |
| Continuity replay escalation | L425-443 | fix_scope "" or "inplace" → "partial" |
| Fix pack contract gate | L445-460 | inplace → partial if contract fails |
| Reject snapshot 35 fields | L309-389 | Full snapshot construction |

### chief_writer.py (2,266 lines)

| Finding | Line(s) | Evidence |
|---|---|---|
| generate_ensemble 3전략 | L66-104 | balanced(0.7) / narrative(0.8) / tension(0.9) |
| Parallel execution | L396-499 | ThreadPoolExecutor(max_workers=3), 540s/worker, 600s total |
| Strategy bias | L119-145 | 20ep lookback win rate → temperature adjustment |
| Self-critique | L759 → chief_writer_quality.py | MAX_CRITIQUE_ROUNDS=3, rubric≥3.5 skip |
| Manuscript truncation | L1668 | `smart_truncate(manuscript, max_chars=150000)` |
| Patch target normalization | L1192-1195 | 6 items max, 80/180 char limits |
| Retry history | L2063-2133 | `_build_retry_history_feedback()` — last 3 attempts, 2 contradictions max |
| Regeneration feedback | L1069-1102 | score_breakdown + validation_warnings[:10] + fix_scope_reasoning + open_review |

## 2. Artifact Path Inventory

### Stage 4 Artifacts (`projects/0_0323/logs/artifacts/stage4/`)

| Path | Status | Evidence |
|---|---|---|
| `ep_0001/attempt_01/` | 존재 | 1차 PASS |
| `ep_0002/attempt_01/` | 존재 | 1차 PASS |
| `ep_0003/attempt_01/` | 존재 | `rejected_best__C.txt` (13,486 bytes), `rejected_best__C_balanced.txt` (13,486 bytes) |
| `ep_0003/attempt_02/` | **부재** | F-1 확인: 후보 전량 실패, 아티팩트 미생성 |
| `ep_0003/attempt_03/` | 존재 | REJECT |
| `ep_0003/attempt_04/` | 존재 | `selected_candidate__A_asp_correction.txt` (12,560 bytes) = `rejected_best__A_asp_correction.txt` (12,560 bytes) → A-3 다운그레이드 확인 |
| `ep_0003/attempt_05/` | 존재 | 최종 PASS |

### Draft Outputs (`projects/0_0323/drafts/`)

| File | Status |
|---|---|
| `ep_0001.txt` | 존재 — 최종 원고 |
| `ep_0002.txt` | 존재 — 최종 원고 |
| `ep_0003.txt` | 존재 — 최종 원고 (5,344자) |

## 3. Console Log Anchors

| Event | Console Evidence |
|---|---|
| Ep1 PASS(98) | "후보 C는 주인공의 절망적인 과거와 회귀 후 냉철한 결의를 가장 입체적으로 묘사" |
| Ep2 PASS(98) | "후보 C는 직전 화와의 서사적 연속성을 가장 매끄럽게 유지" |
| Ep3 R1 REJECT(80) | "Blueprint에 명시된 5개의 씬 구분이 원고에 전혀 반영되지 않았음" |
| Ep3 R2 EMPTY | "🚨 [V66.3] 모든 후보 생성 실패 — 다음 면담으로 진행" |
| Ep3 R3 REJECT(76) | "원고가 블루프린트의 'scene_breakdown'에 명시된 5개의 씬으로 명확하게 구분되지 않았습니다" |
| Ep3 R4 PASS→REJECT | "[A-3] Post-select continuity conflict: Timeline mismatch — 1월 17일 vs 1월 18일" |
| Ep3 R4 ASP | "[ASP] 레드팀 교정 발동 (재시도 4회차)", "[ASP] 교정 완료 (delta: +24)" |
| Ep3 R5 PASS(98) | "후보 A는 이전 2화의 타임라인(1월 18일 저녁 독대)을 정확히 계승" |
| FrontierLag stop | "🏁 목표 회차(3화) 도달. 종료합니다." |

## 4. DB / Audit Notes

- DB 레코드 직접 조사는 T5 범위 외 (T6/T8 범위)
- `_compact_text` 절삭이 DB 저장 경로에 적용되는 것은 소스에서 확인
- `_record_s4_attempt()` (L5826-5917)에서 verdict, score, reject_reason 등 기록

## 5. Cross-Reference Map

| T5 Finding | Prior Report | Status |
|---|---|---|
| F-1 | Fresh run 3pass P1-3 | 관련 (TF-H 패치 실패 언급) |
| F-2 | Q4 feedback-loop deep-dive | 직접 관련 (피드백 수렴 실패) |
| F-3 | Q8 logging-retention deep-dive | 직접 관련 (DB 절삭) |
| F-4 | Director 7-axis H-1~H-3 | 부분 관련 (A-3 게이트 이후 스냅샷) |
| F-5 | Director 7-axis H-4 | 동일 발견 |
| F-7 | Director 7-axis H-2 | Stale: 3→5로 이미 수정 |
| H-1 (rejection_reason) | Director 7-axis H-1 | Stale: verdict_reason 우선 사용으로 수정 |
| H-2 (contradiction 5→3) | Director 7-axis H-2 | Stale: [:5]로 이미 확장 |
| H-3 (verdict_reason 500) | Director 7-axis H-3 | Confirmed: 그대로 |
