Date: 2026-04-17
Status: final (3-pass adversarial audit complete, confidence 97%)
Scope: `Arc 2 ep8/ep9 boundary recut + Stage3 next-episode reservation guard` pre-rerun audit
Project Target: `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1`
Baseline Commit: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
Baseline Dirty Summary: tracked local edits remain in `0_temp.txt`, `modules/domain/agents/{blueprint_constraint_compiler.py, blueprint_ensemble.py, stage3_retry_coordinator.py, three_phase_blueprint_runtime.py}`, and the touched Stage3 guardrail tests; untracked local docs from 2026-04-17 and canary artifacts also remain
Resume Commit: `ce0f3b47b465fcd67796f75e0497a5f7c7b2424f`
Resume Drift Summary: added canary copy `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1`, rewrote Arc 2 authority there, and cleared Stage3 outputs from `ep8+` before rerun
Evidence:
- `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/project_data.db`
- `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1/plans/arcs/arc_002.txt`
- `projects/0_20260417-카나리아/project_data.db` (adversarial prior `ep7`/`ep8` blueprint source)
- `modules/domain/agents/blueprint_constraint_compiler.py`
- `modules/domain/agents/blueprint_ensemble.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`

**Pass 1**
This audit covers only the bounded `Arc 2 ep8 -> ep9` rerun lane. It does not reopen broad `Stage234`, `ep7` proof lineage, or wider runtime closure claims. The concrete question is whether the new authority split and the new reservation guard remove the prior `ep8 front-load -> ep9 contract squeeze` blocker enough to justify a clean Stage3 rerun from `ep8`.

**Pass 2**
Finding 1: no structural boundary leak remains in the recut authority text. In the new canary copy, `ep8` MUST_FOCUS now ends at `고위험 WTI 15억 구상 공개 -> 공급 충격 논리 제시 -> 박성호가 즉시 실행을 망설임 -> 지점장 라인 압박` and no longer includes `수수료 두 배`, `지점장 전결/컴플라이언스 간소화`, or `실제 주문 체결 완료`. Those beats are now explicitly reserved in `ep8.stop_line` for `ep9`.

Finding 2: `ep9` now owns the previously squeezed execution lane. The new `ep9` MUST_FOCUS is explicitly `수수료 두 배 제안 -> 지점장 전결/컴플라이언스 간소화 -> 15억 증거금 동결 -> 실제 주문 체결 완료`. The next-stop for `ep10` is now explicitly `한미증권 이탈 -> 카페 이동 -> 초기 모니터링 -> 에콰도르/후속 공급 충격 대기`, so `ep9` no longer needs to carry both execution and aftermath in the same surface.

Finding 3: the engine-side guard is now stronger than the previous replay-only reroute. `BlueprintConstraintCompiler` now emits `future_beat_reservations` from `stop_line`, `blueprint_ensemble` surfaces them in the producer prompt, and `three_phase_blueprint_runtime` re-injects them on `candidate_disqualified` retries. This means the model now sees not only `직전 화 replay 금지` but also an explicit instruction that the next episode's reserved result beats must not be completed early.

Finding 4: adversarially, even when `ep9` is compiled against the old failing `ep8` blueprint from the source canary, the packet still blocks the stale VIP-room confrontation family. The compiled `ep9` packet identifies `dialogue_duel`, `action_peak`, and `cliffhanger` families in `서울 여의도 한미증권 VIP룸` with the `한시우 + 박성호 PB` axis, and the surface guidance reroutes the episode toward `승인/전달/집행/후속 처리` rather than repeated two-person confrontation.

**Pass 3**
Operational readiness is acceptable for a bounded rerun from `ep8`. The new canary copy has `blueprints WHERE ep_num >= 8 = 0` and `stage_attempts(stage=3) WHERE ep_num >= 8 = 0`, so no stale `ep8` or `ep9` Stage3 outputs remain in the rerun target. The authoritative Arc 2 payload and the human-facing `plans/arcs/arc_002.txt` were aligned to the same recut text, so the operator-visible artifact and the runtime anchor no longer diverge.

Residual risk remains, but it is no longer the same structural blocker. The rerun can still fail on ordinary generation quality reasons such as density, opening transition roughness, or new local replay signatures inside the newly generated `ep8`. What this audit does clear is the prior `ep8 overconsumed ep9 -> ep9 had no legal surface left` contract squeeze. That specific blocker is no longer supported by the current authority and guard state.

**Conclusion**
Proceed with a bounded Stage3 rerun from `ep8` on `projects/_canary/0_20260417-카나리아-ep8ep9-recut-r1`. Do not rerun `ep9` alone against the old `blueprint_0008`, because the whole point of this wave is to replace that stale frontier. The right execution path is `ep8 -> ep9` regeneration under the recut authority and the strengthened reservation guard.
