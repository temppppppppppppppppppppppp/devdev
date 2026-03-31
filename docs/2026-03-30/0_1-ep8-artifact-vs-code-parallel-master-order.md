# 0_1 EP8 Artifact-vs-Code Parallel Master Order

Date: 2026-03-30
Status: final (3-pass audited)
Document Type: survey master order
Canonical Path: `docs/2026-03-30/0_1-ep8-artifact-vs-code-parallel-master-order.md`
Temp Mirror Path: `(none - operator order only; no docs/temp mirror)`
Baseline Commit: `92ba1cf7`
Baseline Dirty Summary: `dirty: 0_temp.txt modified; 0_1 episode/log DB sinks advanced; ep_0008 Stage 4 artifact dir untracked`
Track: system
Mode: bounded partial live-merge evidence after operator stop
Source Harnesses:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/live-run-merge-survey-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/canonical-naming-contract.md`
Context Docs:
- `docs/2026-03-30/rol-live-merge-current-context-note.md`
- `docs/2026-03-30/rol-live-merge-global-survey-bounded-execution-ssot.md`

## 1. Purpose

This is the operator master order for one bounded question only:

- is the current EP8 failure primarily an artifact-stage problem, a code-stage problem, or a mixed problem?

This order is for:

- read-only parallel survey
- evidence capture
- lane report drafting
- later execution-SSOT preparation after lane reports return

This order is not for:

- code edits
- DB writes
- manuscript or blueprint edits
- `docs/temp/` mutation
- queue cleanup
- closure claims

## 2. Current Mode

The previous run is no longer treated as actively live.

Current operating assumption:

- the operator stopped the terminal
- bounded partial evidence exists on disk and in DB sinks
- the survey may use that evidence
- no final remediation claim should be made from memory alone

Minimum authoritative evidence set for this order:

- `0_temp.txt`
- `projects/0_1/logs/session_20260330_161043.log`
- `projects/0_1/logs/episode_production.jsonl`
- `projects/0_1/project_data.db`
- `projects/0_1/logs/artifacts/stage4/ep_0008/attempt_*`

## 3. Common Rules For All Terminals

All terminals must follow these rules:

1. Survey only.
2. Read-only only.
3. No code edits, no DB edits, no artifact edits, no `docs/temp/` edits.
4. Use UTF-8 byte-level read-back for Korean text evidence.
5. Do not use console mojibake or preview rendering as encoding evidence.
6. Prefer live workspace evidence over stale survey text and memory.
7. Keep scope to the assigned lane only.
8. Use absolute paths and line anchors where practical.
9. If a lane saves a report, save only under `docs/2026-03-30/`.
10. Saved lane reports must be marked `Status: draft-bounded-partial-evidence`.
11. Do not create execution SSOTs, roadmaps, or closure docs in the lane terminals.
12. Terminal 4 is synthesis-only and should wait for lanes 1-3.

## 4. Output Contract Per Lane

Each lane terminal must return this shape in terminal output:

1. `Coverage`
2. `Findings`
3. `Non-Issues`
4. `Verdict`
5. `Stop`

Required stop line:

- `read-only lane complete; no files mutated`

If a lane finds anything action-bearing or synthesis-relevant, it should also save one draft report under `docs/2026-03-30/`.

Recommended draft paths:

- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane1-artifact-truth-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane2-code-contract-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane3-persistence-timeline-draft.md`
- `docs/2026-03-30/0_1-ep8-artifact-vs-code-lane4-master-synthesis-draft.md`

## 5. Working Hypothesis To Test, Not To Assume

The survey must test this hypothesis rather than trust it:

- attempts 1-4 look code-heavy because strong advisory escalation turned `PASS` into `PASS_WITH_FIX` without usable local `patch_targets`
- attempt 5 looks artifact-heavy because a concrete local phrase contradiction appears: `18년 전 과거의 기억`
- therefore the likely answer is `mixed`, but the terminals must prove or disprove that from evidence

## 6. Lane Map

Use this four-terminal layout:

1. Terminal 1: artifact truth and narrative defects
2. Terminal 2: Stage 4 code contract and retry-lane defects
3. Terminal 3: persistence, DB, JSONL, and attempt timeline reconstruction
4. Terminal 4: master synthesis after receiving 1-3

## 7. Terminal 1 Order

Use this as-is:

```text
넌 1번 터미널이다.

역할:
- EP8의 실물 단계 문제를 조사하는 Artifact Truth / Narrative lane

공통 가드레일:
- 이번 오더는 survey only. 코드 수정, DB write, docs/temp 수정, queue cleanup, closure claim 금지.
- UTF-8 byte-level read-back만 증거로 사용. 콘솔 mojibake/preview를 근거로 판단하지 말 것.
- live workspace evidence > stale 문서 > 기억 순서로 판단.
- 최종 산출물은 터미널 보고문 + draft 보고서 1개뿐. execution SSOT 저장 금지.

먼저 읽을 것:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\live-run-merge-survey-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-parallel-master-order.md

필수 조사 대상:
- C:\Users\User\Desktop\글도비\0_temp.txt
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session_20260330_161043.log
- C:\Users\User\Desktop\글도비\projects\0_1\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\artifacts\stage4\ep_0008\attempt_*
- C:\Users\User\Desktop\글도비\projects\0_1\plans\blueprints\blueprint_0008.txt
- C:\Users\User\Desktop\글도비\projects\0_1\drafts\ep_0007.txt
- 필요 시 C:\Users\User\Desktop\글도비\projects\0_1\plans\arcs\arc_002.txt
- C:\Users\User\Desktop\글도비\projects\0_1\project_data.db 의 stage_attempts / director_selections 관련 row

목표:
- Director가 실제로 문제 삼은 실물 하자를 재판정
- 박성호 role drift, opening continuity, 이동 경위, 대화 비율, '18년 전 과거의 기억' 시점 모순을 실물 기준으로 분리
- 코드가 완벽했어도 EP8이 반려될지 판단

최종 보고 형식:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: artifact-first / mixed / not-artifact-first
5. Stop

문서 저장:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-lane1-artifact-truth-draft.md
- 상태 표기: Status: draft-bounded-partial-evidence
```

## 8. Terminal 2 Order

Use this as-is:

```text
넌 2번 터미널이다.

역할:
- EP8의 코드 단계 문제를 조사하는 Code Contract / Retry lane

공통 가드레일:
- survey only. 코드 수정, DB write, docs/temp 수정, queue cleanup, closure claim 금지.
- 이번 lane의 일은 root cause 판정이다. 구현 제안은 허용되지만 구현 금지.
- 근거 없는 '버그 같다' 금지. exact seam과 exact function으로 말할 것.

먼저 읽을 것:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\live-run-merge-survey-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-parallel-master-order.md

핵심 조사 파일:
- C:\Users\User\Desktop\글도비\modules\core\stage4_interview_round.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_retry_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_reject_runtime.py
- C:\Users\User\Desktop\글도비\modules\core\stage4_outcome_runtime.py
- 필요 시 C:\Users\User\Desktop\글도비\modules\core\stage4_immutable_fact_contract.py
- 필요 시 C:\Users\User\Desktop\글도비\0_temp.txt
- 필요 시 C:\Users\User\Desktop\글도비\projects\0_1\logs\session_20260330_161043.log

반드시 판정할 것:
- strong advisory escalation 뒤 missing patch_targets loop는 intended fail-closed인지, 수정해야 할 계약 결함인지
- post_select_conflict / IFC 계열이 애초에 rewrite lane으로 가야 하는지
- attempt 1~4는 code routing 문제가 우세한지
- attempt 5의 provisional PASS_WITH_FIX -> final REJECT는 정상 동작인지

최종 보고 형식:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: code-first / mixed / not-code-first
5. Stop

문서 저장:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-lane2-code-contract-draft.md
- 상태 표기: Status: draft-bounded-partial-evidence
```

## 9. Terminal 3 Order

Use this as-is:

```text
넌 3번 터미널이다.

역할:
- EP8의 authoritative evidence reconstruction lane

공통 가드레일:
- survey only. 코드 수정, DB write, docs/temp 수정, queue cleanup, closure claim 금지.
- terminal capture보다 DB / JSONL / session log / artifact path를 우선한다.
- attempt-by-attempt timeline을 반드시 표로 만든다.

먼저 읽을 것:
- C:\Users\User\Desktop\글도비\AGENTS.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-order-init-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\system-full-survey-execution-harness.md
- C:\Users\User\Desktop\글도비\docs\implementation\live-run-merge-survey-harness.md
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-parallel-master-order.md

필수 조사 대상:
- C:\Users\User\Desktop\글도비\0_temp.txt
- C:\Users\User\Desktop\글도비\projects\0_1\project_data.db
- C:\Users\User\Desktop\글도비\projects\0_1\logs\episode_production.jsonl
- C:\Users\User\Desktop\글도비\projects\0_1\logs\session_20260330_161043.log
- C:\Users\User\Desktop\글도비\projects\0_1\logs\artifacts\stage4\ep_0008\attempt_*

반드시 답할 것:
- attempt 1부터 latest persisted attempt까지 matrix
- selected / director_verdict / final_verdict / gate_basis / fix_scope / top reason
- empty patch loop가 지속된 구간
- 최초로 유효한 patch target이 등장한 attempt
- 현재 latest persisted state의 primary blocker

최종 보고 형식:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: timeline says artifact-first / code-first / mixed
5. Stop

문서 저장:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-lane3-persistence-timeline-draft.md
- 상태 표기: Status: draft-bounded-partial-evidence
```

## 10. Terminal 4 Order

Use this as-is:

```text
넌 4번 터미널이다.

역할:
- 1번, 2번, 3번 터미널 보고를 받아 최종 분류하는 Master synthesis lane

중요:
- 새 broad discovery를 먼저 하지 말 것
- 1번, 2번, 3번의 최종 보고가 입력되기 전까지는 대기
- 입력 보고끼리 충돌하면 missing evidence를 먼저 지적하고, 억지 결론을 내리지 말 것

입력으로 받을 것:
- 터미널 1 최종 보고
- 터미널 2 최종 보고
- 터미널 3 최종 보고

최종 목표:
- EP8 문제를 artifact-first / code-first / mixed 중 하나로 확정
- primary blocker와 secondary blocker를 분리
- immediate next action을 '원고 수정 먼저 / 코드 수정 먼저 / 둘 다 보류' 중 하나로 제시
- execution SSOT는 만들지 말고 synthesis draft까지만 정리

최종 보고 형식:
1. Coverage
2. Findings
3. Non-Issues
4. Verdict: artifact-first / code-first / mixed
5. Stop

문서 저장:
- C:\Users\User\Desktop\글도비\docs\2026-03-30\0_1-ep8-artifact-vs-code-lane4-master-synthesis-draft.md
- 상태 표기: Status: draft-bounded-partial-evidence
```

## 11. Post-Survey Handoff Rule

After terminals 1-4 finish:

1. collect the four draft reports
2. run a document-side 3-pass audit on those reports
3. synthesize one canonical merge audit if needed
4. only then derive an execution SSOT

Execution-SSOT generation is explicitly out of scope for the lane terminals.
It belongs to the main operator pass after the lane reports return.

## 12. 3-Pass Audit Record

Pass 1, structure and scope:

- document type is survey master order, not execution SSOT
- scope is one bounded EP8 question
- canonical path is dated docs only
- `docs/temp/` exclusion is explicit

Pass 2, evidence and consistency:

- current commit and dirty summary were refreshed from the live workspace
- mode reflects operator-stopped bounded evidence, not active live run
- terminal prompts align with system-track read-only governance

Pass 3, execution and readability:

- lane scopes are non-overlapping enough for parallel use
- output contract is explicit
- post-survey handoff to later execution-SSOT creation is explicit

Confidence: 97%
