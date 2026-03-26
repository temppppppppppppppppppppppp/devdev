# stage4-ifc-structural-extraction-wave2 Execution SSOT

Date: 2026-03-25
Status: closed (closure-audited)
Canonical Path: `docs/2026-03-25/stage4-ifc-structural-extraction-wave2-execution-ssot.md`
Temp Mirror Path: `docs/temp/stage4-ifc-structural-extraction-wave2-execution-ssot.md`
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: Wave 1 code changes (stage4_immutable_fact_contract, chief_writer_context, tests), canary project, dated docs`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Source Survey Docs:
- `docs/2026-03-25/stage4-compliance-gap-compact-survey.md`
- `docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-canary-report.md`
Evidence Artifacts:
- `projects/canary_0325_stage4_fix/logs/canary_summary.json`
- `projects/canary_0325_stage4_fix/logs/episode_production.jsonl`
- `projects/canary_0325_stage4_fix/logs/artifacts/stage4/ep_0005/attempt_01-03/`
Side-Effect Coverage: covered

## 1. Intent
- Broaden IFC committed_state_facts and completed_event_facts extraction to capture entity-ownership and procedural-completion structural facts beyond monetary keywords.
- Move structural facts (account ownership, item possession, organization status, procedural completion) from lower-authority context (chain_link prose, prev_manuscripts) into the ⛔-marked IFC section where CW demonstrably complies.
- This is Wave 2 of the IFC repair. Wave 1 restored the fact-ledger wiring and added bilingual/genre keywords. Wave 2 broadens the extraction categories within the same proven IFC path.

## 2. Baseline Facts
- Wave 1 reduced EP4 retry from 6→3 rounds by restoring fact-ledger → IFC monetary data.
- Canary EP5 R1 still confused personal vs corporate account ownership ("SW인베스트먼트 법인 계좌" instead of "개인 명의 파생 계좌") — this structural fact is NOT in IFC committed_state_facts.
- Fact_ledger `to_summary()` renders entity-ownership lines that the current extraction misses:
  - Items: `- OTP (일회용 비밀번호 생성기) (보유, 소유: 주인공, ep3)` — contains "소유", "보유"
  - Items: `- SW인베스트먼트 법인 인감 (황동 재질) (획득, 소유: 주인공, ep4)` — contains "법인", "소유"
  - Numbers: `- capital: 2000000005.0 won (ep5 기준)` — already captured by Wave 1
- Chain_link/prev_digest contain procedural-completion facts ("세팅 완료", "OTP 수령") that the current completed_event extraction misses.
- CW complies with ⛔ IFC monetary facts (proven: EP4 R3 capital compliance). Putting structural facts in the same ⛔ section should yield the same compliance improvement.

## 3. Scope
Included:
- `modules/core/stage4_immutable_fact_contract.py`
- `tests/test_stage4_immutable_fact_contract.py`

Excluded:
- `modules/domain/agents/chief_writer_context.py` (no changes needed — IFC build path already works from Wave 1)
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_prompts.py`
- `modules/domain/agents/director_prompts.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/failure_analyzer.py`
- Stage 3 code/prompts
- `world_state` population logic
- post-select / retry routing logic
- DB schema, JSONL path/naming, dashboard/UI

## 4. Pass 1. Inventory Summary
- Primary extraction gap: 2 categories
  - entity-ownership lines in fact_ledger summary (items with `소유:`, organizations with `법인`/`활동중`)
  - procedural-completion lines in chain_link/prev_digest (`세팅`, `수령`, `설립`, `발급`)
- Touched functions: 2
  - `_extract_committed_state_facts()` L161-189
  - `_extract_completed_event_facts()` L192-226
- Evidence quality: high (fact_ledger to_summary() output directly inspected; canary artifacts confirm the gap)

## 5. Pass 2. Semantic Classification
- Class A. Entity-ownership extraction gap
  - fact_ledger summary contains `소유:`, `법인`, `보유`, `활동중` lines that carry structural entity state
  - current keyword set matches only monetary terms
  - fix: add bounded structural keywords to fact_ledger extraction
- Class B. Procedural-completion extraction gap
  - chain_link/prev_digest contain `세팅`, `수령`, `발급`, `설립`, `입주`, `확인` lines
  - current completed_event keyword set matches only wuxia/action/investment verbs (Wave 1)
  - fix: add bounded procedural keywords to completed_event extraction
- Deferred, not in this wave:
  - Director audit rubric coarseness (separate investigation)
  - Account ownership attribution in fact_ledger data model (world_state redesign territory)
  - Post-select → retry feedback classification granularity

## 6. Side-Effect Map
- file writes / artifacts: none beyond tests
- DB / schema / transaction boundaries: not applicable
- JSONL / log / audit sinks: no new sinks
- console / UI / operator output: not applicable
- rollback / recovery / retry: no policy change
- cache / global state: none
- bootstrap fallback / config-env mutation: not applicable

## 7. Realization Architecture
- Keep changes inside existing `_extract_committed_state_facts()` and `_extract_completed_event_facts()` keyword tuples.
- No new extraction functions, no new data structures, no new parameters to `build_packet()`.
- The rendering path (`render_packet_for_cw()`) already handles committed_state_facts and completed_event_facts with ⛔ markers — no changes needed.
- Backward compatibility: if fact_ledger has no structural lines, the extraction yields nothing — same as before.

## 8. Execution Tranches
1. Tranche A: Entity-ownership committed_state_facts keywords
   - Add to fact_ledger extraction keyword tuple in `_extract_committed_state_facts()`:
     - `소유` — matches "소유: 주인공" in fact_ledger item/location lines
     - `법인` — matches "법인 인감", "법인 계좌" in fact_ledger item/org lines
     - `개인` — matches "개인 명의" attribution
     - `명의` — matches "명의" ownership attribution
     - `보유` — matches item possession status "보유"
     - `활동중` — matches organization active status
   - Additive only. Do not remove existing monetary keywords.

2. Tranche B: Procedural-completion completed_event_facts keywords
   - Add to completed_event extraction keyword tuple in `_extract_completed_event_facts()`:
     - `세팅` — matches "계좌 세팅 완료"
     - `수령` — matches "OTP 수령"
     - `발급` — matches "인감 발급", "카드 발급"
     - `설립` — matches "법인 설립"
     - `입주` — matches "사무실 입주"
     - `확인` — matches "접속 확인", "잔고 확인"
   - Additive only. Do not remove existing wuxia/action/investment keywords.

3. Tranche C: Targeted regression tests
   - Add tests proving:
     - Fact_ledger item-ownership line with "소유:" yields committed_state_fact
     - Fact_ledger line with "법인" yields committed_state_fact
     - Chain_link line with "세팅" or "수령" yields completed_event_fact
     - Chain_link line with "설립" or "확인" yields completed_event_fact
     - Existing monetary extraction (capital/won) is not regressed
     - Existing wuxia/action extraction (처단/돌파) is not regressed
     - Existing investment extraction (개설/이체/계약) is not regressed

## 9. Acceptance Criteria
- Fact_ledger summary containing `소유: 주인공` lines yields non-empty committed_state_facts for those lines.
- Fact_ledger summary containing `법인` yields committed_state_facts for those lines.
- Chain_link section containing `세팅 완료` or `OTP 수령` yields completed_event_facts.
- Existing monetary/wuxia/investment extraction is not regressed.
- No change to `build_packet()` signature, `render_packet_for_cw()`, or any other file.
- `render_packet_for_cw()` ⛔ markers continue to render correctly for the expanded facts.

## 10. Verification Plan
- `python -m py_compile modules/core/stage4_immutable_fact_contract.py`
- `set PYTHONIOENCODING=utf-8 && pytest tests/test_stage4_immutable_fact_contract.py -q`
- `python scripts/check_utf8_hygiene.py modules/core/stage4_immutable_fact_contract.py tests/test_stage4_immutable_fact_contract.py docs/2026-03-25/stage4-ifc-structural-extraction-wave2-execution-ssot.md docs/temp/stage4-ifc-structural-extraction-wave2-execution-ssot.md`
- `python scripts/sync_temp_queue_state.py`
- `python scripts/ops_validator.py`

## 11. Guardrails
- Do not modify `build_packet()` signature or add new parameters.
- Do not modify `render_packet_for_cw()` rendering logic.
- Do not touch Director prompts, CW prompts, retry runtime, or post-select logic.
- Do not open Stage 3, world_state population, or fact_ledger data model.
- Do not broaden into Director rubric patch — that is a separate investigation.
- Keyword additions are additive only; do not remove any existing keyword.
- If a keyword causes unacceptable false-positive noise in non-investment genres, shrink scope rather than expand it.

## 12. Temp Queue Notes
- temp status: pending
- cleanup condition:
  - remove the temp mirror only after implementation is realized, closure-audited, and queue state returns to empty
- roadmap dependency:
  - none; single-item queue expected (Wave 1 is already closed)

## 13. Validation and Closure Hooks
- validator command: `python scripts/ops_validator.py`
- closure harness: `docs/implementation/execution-closure-harness.md`
- optional queue state entry: `docs/temp/queue-state.json`
- execution-start rule: re-run the document 3-pass audit and confirm at least 95% confidence against the current workspace state before patching code from this document

## 14. 3-Pass Audit Notes
- Pass 1: scope narrowed to IFC extraction keyword expansion only; two functions in one file + one test file
- Pass 2: evidence matches live code — fact_ledger to_summary() output directly inspected; canary artifacts confirm EP5 R1 ownership confusion not captured by current extraction; keyword additions are bounded and additive
- Pass 3: realization is actionable and bounded; same pattern as Wave 1; no policy or schema blast-radius
- Confidence: 97%

## 15. Closure Audit
- Closure result: accepted with no blocking findings.
- Realized scope matched the active SSOT:
  - `modules/core/stage4_immutable_fact_contract.py`
  - `tests/test_stage4_immutable_fact_contract.py`
- Confirmed realized tranches:
  - Tranche A: committed-state extraction now recognizes bounded structural ownership cues
  - Tranche B: completed-event extraction now recognizes bounded procedural-completion verbs
  - Tranche C: targeted regression coverage expanded without reopening other Stage 4 surfaces
- Re-run verification during closure audit:
  - `python -m py_compile modules/core/stage4_immutable_fact_contract.py`
  - `pytest tests/test_stage4_immutable_fact_contract.py -q` -> `55 passed`
  - `python scripts/check_utf8_hygiene.py ...` -> pass
  - `python scripts/ops_validator.py` -> `0 errors, 0 warnings`
- Closure notes:
  - The implementation summary's "7 new tests" wording overcounted by one relative to the net file total (`49 -> 55`, net `+6`). This is reporting drift only, not a code or verification issue.
  - Live proof remains a subsequent Stage 4 canary question; this closure only certifies the bounded extraction expansion and regression coverage.
