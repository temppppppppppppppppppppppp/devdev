# Stage2 Contract Normalization Arc 5 Inventory-Semantic Rerun Proof

Date: 2026-04-19
Status: final (bounded fresh proof complete; confidence `97/100`)
Canonical Path: `docs/2026-04-19/stage2-contract-normalization-arc5-inventory-semantic-rerun-proof.md`
Commit State:
- Baseline Commit: `029df1a7`
- Baseline Dirty Summary: `dirty worktree with active canary, runtime, docs, and test deltas already present; this proof note records the first fresh arc_005 rerun after the Stage2 stale-receipt / inventory-semantic filtering tranche`
Source Survey Docs:
- `docs/2026-04-19/stage2-contract-normalization-arc5-state-shell-rerun-proof.md`
- `docs/2026-04-02/0_0-stage2-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-19/stage2-contract-normalization-reactivation-refresh.md`
- `docs/2026-04-19/active-temp-execution-roadmap.md`
Source Anchors:
- [Pre-filter arc 5 decision rows](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_stateshell_r1/logs/session/decisions.jsonl:1)
- [Pre-filter arc 5 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_stateshell_r1/logs/artifacts/stage2/arc_005/attempt_01/final_arc__balanced.json:1)
- [Post-filter arc 5 decision rows](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_inventorysem_r1/logs/session/decisions.jsonl:1)
- [Post-filter arc 5 artifact](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_inventorysem_r1/logs/artifacts/stage2/arc_005/attempt_01/final_arc__balanced.json:1)
- [Post-filter UI trace](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_inventorysem_r1/logs/session/ui_events.jsonl:1)
- [Post-filter Stage2 summary](/c:/Users/PC/Desktop/글도비/projects/_canary/probe_a_stage2_arc5_inventorysem_r1/logs/stage2_canary_summary.json:1)

## Result

The first fresh `arc_005` rerun after the stale-receipt / inventory-semantic filter tranche removed the last visible first-pass repair noise on this family.

- rerun target: `projects/_canary/probe_a_stage2_arc5_inventorysem_r1`
- initial Director verdict on attempt 1: `PASS (95)`
- final verdict on the same attempt: `PASS`
- final score: `95`
- final strategy: `balanced`

This is materially stronger than the immediately previous fresh rerun:

- previous `stateshell_r1`: `PASS_WITH_FIX (92) -> PASS (100)`
- current `inventorysem_r1`: `PASS (95)` from the first Director pass, no `PASS_WITH_FIX` hop needed

## What Changed

The current accepted end inventory is now a narrower seven-item set:

- `18년 치 매크로 이벤트가 암호화되어 적힌 양장 수첩`
- `SW인베스트먼트 법인 설립 신청서 가안`
- `박성호 PB의 직통 핫라인 번호가 적힌 명함`
- `SW인베스트먼트 법인 등록증`
- `리스크관리팀 예외 계좌 승인 서류 사본`
- `해외 대체 투자 데스크 사전 브리핑 메모`
- `2006년 연말 결산 50억 원 잔고 증명서`

Compared with the previous fresh rerun, the first-pass stale inventory complaint is gone:

- the old `WTI 6월물 3배 레버리지 매수 체결 내역서` no longer survives into the accepted end inventory
- the stale `17.5억 원의 현금 유동성이 찍힌 법인 계좌 잔고 증명서` no longer survives into the accepted end inventory
- the accepted artifact now keeps the current-state proof object instead: `2006년 연말 결산 50억 원 잔고 증명서`

The fresh artifact and summary also show the current consumed side more honestly:

- `금 선물 롱 포지션 계약서 (잔여 절반)`
- `잔고 45억 원이 찍힌 법인 계좌 원장`

That is exactly the family this tranche aimed to narrow: transient or stale receipt objects that should not keep masquerading as durable carryover inventory.

## Interpretation

This proof is enough to bank the stale-receipt filter as a real Stage2 improvement.

What changed relative to the prior state-shell proof:

- the lane is no longer failing first on header completeness
- the lane is no longer failing first on stale receipt carryover
- the fresh rerun now clears the entire `arc_005` family on the first Director pass

What remains true:

- this note does **not** claim every broader Stage2 normalization question is closed
- this note does **not** claim the lane should skip closure review
- this note does justify moving the lane from `front-active localfix` toward `closure-review ready`

## Operational Consequence

The next honest move for this Stage2 lane is no longer another same-family patch.

The next honest move is:

1. bank the end-state header sync tranche
2. bank the stale-receipt / inventory-semantic filter tranche
3. move the lane into closure review unless a different later-family proof reopens it

## Pass 1

- the proof is bounded to the first fresh `arc_005` rerun after the inventory-semantic filter tranche
- the document distinguishes this result from the earlier state-shell proof so the improvement chain is legible

## Pass 2

- the claims are tied to checked decision rows, artifact content, UI trace, and Stage2 summary
- the document does not overclaim full Stage2 closure from one rerun

## Pass 3

- the operating consequence is explicit: no more same-family localfix by default, closure review next
- the result is strong enough to use as queue-governing backing for the Stage2 sibling lane

Confidence: 97/100
