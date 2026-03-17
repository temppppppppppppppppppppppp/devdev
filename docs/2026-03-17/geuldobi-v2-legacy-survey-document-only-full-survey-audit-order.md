# Geuldobi V2 Legacy Survey Document-Only Full Survey Audit Order

Date: 2026-03-17
Status: active
Canonical Path: `docs/2026-03-17/geuldobi-v2-legacy-survey-document-only-full-survey-audit-order.md`
Applies To: document-only revalidation of three legacy survey drafts
Confidence After 3-Pass Audit: `96%`

## 1. Purpose
- provide a document-only system-track order for revalidating three legacy survey drafts
- produce fresh canonical audit and execution-doc artifacts only if the live code still supports them
- prevent direct trust in previously generated derived docs, temp mirrors, or stale survey conclusions

## 2. Direct Targets
- `docs/2026-03-17/별도 조사2/ssot_stage23-improvement-survey.md`
- `docs/2026-03-17/별도 조사/ssot_integrated-survey.md`
- `docs/2026-03-17/별도 조사2/ssot_stage0-stage2-architecture-survey.md`

## 3. Working Assumption
- the operator currently does not trust prior derived outputs from these source surveys
- this order therefore treats the three source surveys as inputs to be independently re-audited against live code
- any existing derived docs may be read as `reference only`, but must not be treated as governing truth

## 4. Hard Rules
- this is `document-only`
- code modification is forbidden
- commit is forbidden
- unrelated dirty or untracked files must not be touched
- relative repo paths are authoritative; if the workspace root differs on another PC, adjust only the root prefix
- `docs/roadmap-v2.md` is seed material only, not execution authority
- human-facing docs must satisfy the 3-pass save rule and the 95% confidence gate before final save
- if the confidence gate is not met, save as draft/hold only or stop before final save

## 5. Required Governance Reads
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/execution-synthesis-harness.md`

## 6. Output Contract

### Mandatory
- one canonical revalidation audit doc covering:
  - validity
  - accuracy
  - ROI
  - landed vs stale vs still-actionable classification

### Conditional
- if execution-worthy work remains, create:
  - 1 to 3 canonical execution SSOT docs
  - 1 canonical aggregate roadmap if there are 2 or more SSOT items
  - 1 canonical 3-pass audit doc for the execution-doc bundle

### Temp Queue Rule
- do not open or modify `docs/temp/` unless all of the following are true:
  - canonical docs are completed first
  - 3-pass audit is complete
  - confidence is at least 95%
  - there is no conflicting unrelated active temp queue
- if temp opening is deferred, write the defer reason explicitly in the final report

## 7. Audit Method

### Step 1. Extract Claims
- read the three source surveys
- extract:
  - explicit issue IDs
  - claimed root causes
  - proposed execution items
  - cited code paths

### Step 2. Revalidate Against Live Code
- re-check the claims against the current codebase
- do not trust old line numbers without re-reading the live files
- separate:
  - `landed`
  - `partially landed`
  - `stale detail / valid diagnosis`
  - `still live`
  - `low ROI / not execution-worthy`

### Step 3. ROI Pruning
- keep only items that are:
  - live in current code
  - bounded enough for an execution SSOT
  - not already landed elsewhere
- exclude or downgrade:
  - broad strategy themes
  - live-run-dependent hypotheses
  - benchmark / human-calibration ideas requiring new evidence
  - duplicate lanes already addressed in prior work

### Step 4. Fresh Synthesis
- write a fresh canonical audit doc
- if warranted, synthesize fresh execution SSOT docs from the still-live subset only
- do not let the integrated survey directly control execution

## 8. Minimum Revalidation Axes
- Stage 0 / Stage 2 / Stage 3 / Stage 4 semantic transport
- provenance / budget / observability landed status
- PASS_WITH_FIX / gate / repair semantics landed status
- prompt/config/runtime authority hygiene landed status
- Stage 0 substrate quality and Stage 0 -> Stage 2 handoff contract
- schema / validator form-bias vs semantic validation gap
- broad strategy vs direct execution-worthiness

## 9. Recommended Canonical Outputs

### Revalidation Audit
- `docs/2026-03-17/geuldobi-v2-legacy-survey-independent-revalidation-audit.md`

### Example Execution SSOTs
- `docs/2026-03-17/geuldobi-v2-stage23-semantic-transport-restoration-execution-ssot.md`
- `docs/2026-03-17/geuldobi-v2-stage0-stage2-substrate-hardening-execution-ssot.md`
- `docs/2026-03-17/geuldobi-v2-stage23-semantic-validation-hardening-execution-ssot.md`

### Example Roadmap
- `docs/2026-03-17/geuldobi-v2-legacy-survey-reentry-execution-roadmap.md`

### Example Bundle Audit
- `docs/2026-03-17/geuldobi-v2-legacy-survey-reentry-execution-3pass-audit.md`

## 10. Required Content In The Revalidation Audit
- final verdict for each of the three source surveys
- what remains valid
- what is stale
- what is already landed
- what is low ROI and should not enter an execution queue
- live code references supporting those conclusions
- extraction rationale for any fresh execution SSOT

## 11. Required Content In Any Execution SSOT
- intent
- baseline facts
- included scope
- excluded scope
- realization slices
- acceptance criteria
- primary risks
- verification plan
- 3-pass audit notes
- explicit note that this cycle remains `document-only` until a future execution order says otherwise

## 12. Validation
- after saving canonical docs, run:
  - `python scripts/check_utf8_hygiene.py ...`
- if a temp queue is opened, also run:
  - `python scripts/sync_temp_queue_state.py`
  - `python scripts/ops_validator.py --strict`

## 13. Final Report Contract
- summary verdict for each source survey
- list of new canonical docs created
- whether temp queue artifacts were opened
- exact validation commands run
- remaining uncertainties
- next-step recommendation:
  - `review`
  - `execution-start readiness`
  - `defer`

## 14. Copy-Paste Launch Prompt

```text
시스템 오더다. 작업 루트는 현재 이 저장소의 루트다.
다른 PC면 루트 절대경로만 현지 환경에 맞게 바꾸고, 나머지 상대 경로는 그대로 유지하라.

이 오더는 `문서 작업 전용`이다.
코드 수정 금지.
커밋 금지.
unrelated dirty/untracked 파일 절대 건드리지 마라.

최우선 SSOT:
- `AGENTS.md`

반드시 먼저 읽을 문서:
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/system-full-survey-execution-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/implementation/execution-synthesis-harness.md`

이번 작업의 직접 대상 원문:
- `docs/2026-03-17/별도 조사2/ssot_stage23-improvement-survey.md`
- `docs/2026-03-17/별도 조사/ssot_integrated-survey.md`
- `docs/2026-03-17/별도 조사2/ssot_stage0-stage2-architecture-survey.md`

governing order doc:
- `docs/2026-03-17/geuldobi-v2-legacy-survey-document-only-full-survey-audit-order.md`

중요 전제:
- 이 3개 원문 survey의 `유효성 / 정확성 / ROI`를 현 코드베이스 기준으로 독립 재감리하는 것이 목적이다.
- 기존에 누가 만들어 둔 파생 문서, reentry docs, execution SSOT, roadmap, temp queue가 있더라도 authority로 신뢰하지 마라.
- 파생 문서가 있으면 `reference only`로 읽을 수는 있으나, 결론은 반드시 live code를 다시 대조해서 독립적으로 내려라.
- `docs/roadmap-v2.md`는 seed일 뿐 authority가 아니다.

작업 목표:
1. 세 survey 문서를 현재 코드베이스 기준으로 다시 감리
2. 각 문서를 아래 중 하나로 판정
   - usable
   - partially usable after correction
   - strategic reference only
   - not execution-worthy
3. 이미 landed 된 내용, stale claim, low-ROI broad idea를 제거
4. execution-worthy 항목만 fresh canonical execution SSOT로 추출
5. 필요하면 aggregate roadmap까지 만들되, 어디까지나 `문서까지`다
6. 코드 구현은 절대 하지 마라

하드 규칙:
- Python은 수집/비교/포맷만. 최종 품질 판단은 문서에서 사람이 이해할 수 있게 명시하라.
- line reference는 live code 기준으로 다시 잡아라. 원문 survey의 숫자/라인을 그대로 믿지 마라.
- 사람 읽는 문서는 반드시 3-pass 감리 후 저장.
- 3-pass 후 confidence 95% 미만이면 final save 하지 말고 draft/hold로 남겨라.
- execution SSOT 또는 roadmap을 새로 만들더라도, 이번 오더는 `survey/document-only`다. 코드 patch 금지.
- 기존 temp queue가 unrelated active 상태면 건드리지 마라.
- 새 temp mirror는 canonical 문서가 먼저 완성되고 3-pass + 95%를 넘긴 뒤, queue 충돌이 없을 때만 허용한다.

최종 보고 형식:
- 세 원문 문서의 판정 요약
- 새로 만든 canonical 문서 경로
- temp mirror/queue를 열었는지 여부
- 실행한 검증 명령
- 남은 불확실성 1~3개
- 다음 단계 제안
```

## 15. 3-Pass Notes

### Pass 1. Scope
- narrowed this doc to a document-only system-track order
- removed implementation ambiguity

### Pass 2. Governance
- aligned the order with the current init-harness and naming-contract rules
- made canonical-first and temp-queue constraints explicit

### Pass 3. Operator Use
- added a copy-paste launch block for another PC
- kept relative paths authoritative so only the workspace root needs adjustment
