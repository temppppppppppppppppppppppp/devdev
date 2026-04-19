# Stage2 Contract Normalization Arc 5 State-Shell Rerun Proof

Date: 2026-04-19
Status: final (bounded fresh proof complete; confidence `96/100`)
Canonical Path: `docs/2026-04-19/stage2-contract-normalization-arc5-state-shell-rerun-proof.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this proof note records the first fresh arc_005 rerun after the Stage2 end-state header sync tranche`
Source Survey Docs:
- `docs/2026-04-19/stage2-contract-normalization-reactivation-refresh.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-19/stage2-pacing-arc5-rerun-proof.md`
- `docs/2026-04-19/active-temp-execution-roadmap.md`
Source Anchors:
- [Pre-header-sync arc 5 decision rows](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_pacing_r1/logs/session/decisions.jsonl:1)
- [Pre-header-sync arc 5 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_pacing_r1/logs/artifacts/stage2/arc_005/attempt_01/final_arc__conservative.json:1)
- [Post-header-sync arc 5 decision rows](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_stateshell_r1/logs/session/decisions.jsonl:1)
- [Post-header-sync arc 5 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_stateshell_r1/logs/artifacts/stage2/arc_005/attempt_01/final_arc__balanced.json:1)
- [Post-header-sync UI trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_stateshell_r1/logs/session/ui_events.jsonl:1)

## Result

The first fresh `arc_005` rerun after the Stage2 end-state header sync tranche stayed healthy and materially changed the kind of repair noise that appears on the first Director pass.

- rerun target: `projects/_canary/probe_a_stage2_arc5_stateshell_r1`
- initial Director verdict on attempt 1: `PASS_WITH_FIX (92)`
- final verdict on the same attempt: `PASS`
- final score: `100`
- final strategy: `balanced`

The key comparison is not pacing. `arc_005` remained a `3-episode` arc in both reruns. The key comparison is the **reason** the first pass still asked for repair.

Before the header-sync tranche, the first-pass complaint was:

- missing opening carryover instruction realization
- missing carried equipment in the episode state headers

After the header-sync tranche, the first-pass complaint shifted to:

- stale `WTI 6월물 3배 레버리지 매수 체결 내역서`
- stale `17.5억 원의 현금 유동성이 찍힌 법인 계좌 잔고 증명서`
- unclear keep-or-drop handling for the gold-liquidation receipt family

That shift matters. It means the bounded shell/header tranche no longer presents as a missing-carryover or empty-state-header problem on this family.

## Interpretation

This rerun is strong evidence that the latest Stage2 tranche moved the governing residue.

What improved:

- the old first-pass complaint about missing opening carryover realization disappeared
- the old first-pass complaint about empty carried-equipment state headers disappeared
- the fresh UI trace explicitly shows `🔧 [End State Header Sync] Arc 5 마지막 화 종료 상태 헤더 동기화`

What remains:

- the next active Stage2 residue is narrower stale-receipt and inventory-semantic filtering
- the problem is now about whether transient receipts and already-consumed proofs should still survive in state-shell inventory lists

The accepted artifact also supports that narrowing. Compared with the older post-pacing artifact, the accepted `joint_docs.physical_inventory` in the new rerun is leaner and cleaner:

- older accepted artifact preview still contained `잔고 증명서`
- new accepted artifact preview keeps the durable substrate (`양장 수첩`, `법인 등록증`, `OTP 카드`, `보안 매체`, `박성호 명함`, `예외 계좌 승인 서류 사본`, `브리핑 메모`, `50억 원 원장`)

So the shell tranche did not merely hide the issue. It appears to have removed the earlier header-completeness failure mode and exposed the next narrower keep-or-drop family underneath it.

## Remaining Scope

What this proof does **not** claim:

- that the whole Stage2 lane is now closed
- that transient receipt semantics are already normalized
- that no further `arc_005` repair noise is possible

What it does justify:

1. keep the Stage2 contract-normalization lane open, but narrow its front residue from `state header completeness` to `stale receipt / inventory semantics`
2. treat opening carryover instruction realization plus carried-equipment state-header completeness as freshly improved, not as the current top complaint
3. make the next bounded Stage2 tranche a keep-or-drop and semantic filtering pass for transient receipts rather than another generic shell/header sync patch

## Pass 1

- the proof is explicitly bounded to the first fresh `arc_005` rerun after the Stage2 header-sync tranche
- the document separates pacing stability from state-shell cleanliness so the claim does not overreach

## Pass 2

- the comparison uses checked decision rows, accepted artifacts, and the UI trace rather than inference alone
- the conclusions only claim a shift in the dominant residue, not full closure

## Pass 3

- the operating consequence is explicit: bank header-sync improvement and move the lane to stale receipt / inventory semantics
- the next tranche is narrow enough to act on without reopening the broader historical proof-sink family

Confidence: 96/100
