# Workspace Instructions

## SSOT

- 현재 워크스페이스 운영 SSOT는 `AGENTS.md`
- `CLAUDE.md`는 호환용 shim이며 독립 운영 기준으로 쓰지 않는다

## Track Split

이 워크스페이스의 오더는 아래 두 트랙으로 분리한다.

- `글도비 시스템 오더`
  - 코드베이스 조사/수정, `main_a.py`, `modules/`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, 런타임, DB, 회귀, 리팩터, 성능, 로깅, control plane, persistence, process runner, desktop/app 연결, `docs/20xx-xx-xx/` 아래 시스템 감사 오더
  - 이 경우 **블록가이드 문서를 먼저 읽지 않는다.**
  - `phase0_design`, `tr_block_070_draft`, `BI` 파일 존재로 단계를 판정하지 않는다.
- `서사 파이프라인 오더`
  - 작품 기획, `work_id` 기반 `Treatment/BI`, `Phase 0`, `TR draft`, `BI`, 감리, 정합성, 밀도 점검, 전처리 handoff, 작품 기준 `다음 스텝/계속/승인`
  - 이 경우에만 아래 `Blockguide First` 규칙을 적용한다.

판정 원칙:

- 대상이 코드/시스템/앱/테스트면 시스템 오더다.
- 대상이 작품/`work_id`/`treatments/`/`bible/` 산출물이면 서사 파이프라인 오더다.
- `다음 스텝`, `계속`, `승인`만으로는 블록가이드 트리거가 아니다. 현재 대상이 작품 파이프라인일 때만 트리거다.

## Document Save Rule

사람이 읽는 문서는 기본적으로 `3pass 감리 후 저장`을 원칙으로 한다.

- 대상: survey, audit, execution SSOT, harness, README, 운영 노트, 보고 문서
- 순서: draft -> pass1 -> pass2 -> pass3 -> final save
- 3pass가 끝나도 추정 확신도 95% 미만이면 추가 감리를 반복하고 final save 하지 않는다
- `execution SSOT`의 `docs/temp/` 카피본도 3pass 감리 완료 및 확신도 95% 달성 후에만 생성/갱신
- raw evidence txt/json 생성 자체는 조사 중간에 가능하지만, 그것을 해석하거나 결론화한 문서는 3pass 감리 전 저장 완료로 취급하지 않는다
- `execution SSOT` 또는 `aggregate roadmap`을 근거로 실제 코드 수정에 착수할 때는, 착수 시점의 최신 workspace 상태를 기준으로 해당 문서를 다시 3pass 감리하고 확신도 95% 이상을 재확인한 뒤에만 수정 작업을 시작한다

## System Init Harness (System Track Only)

시스템 오더는 먼저 `docs/implementation/system-order-init-harness.md`를 읽는다.

- 이 하네스가 temp queue 점검, 현재 모드 판정, 다음으로 읽을 하네스 선택을 담당
- 필요 시 `system-full-survey-execution-harness`, `temp-execution-queue-roadmap-harness`, `document-3pass-audit-harness`로 내려간다
- 템플릿이 필요하면 `execution-ssot-template`, `execution-roadmap-template`을 사용
- `AGENTS.md`는 라우팅/불변식 위주로 유지하고, 상세 시작 절차는 init harness에 둔다

## Operations Governance (System Track Only)

- this system-track operating pattern may be referred to as `Recursive Ops Loop`
- accepted aliases: `Recursive Ops Loop`, `ROL`, `rol`
- `Recursive Ops Loop` means: init -> optional preflight -> survey/evidence synthesis -> execution queue control -> validation -> closure
- the loop is bounded by task intent; it does not imply patching or full realization on every request
- system-track governance or process-doc conflicts use `docs/implementation/operations-governance-map.md`
- workspace precedence is `AGENTS.md` -> init harness -> specialized harness -> contracts/templates -> local notes -> `CLAUDE.md` shim
- canonical dated docs beat `docs/temp/` mirrors, and live workspace evidence beats stale survey text
- high-rigor system-track starts may use `docs/implementation/system-order-preflight-harness.md`
- multi-source execution docs may use `docs/implementation/execution-synthesis-harness.md`
- evidence-heavy work may use `docs/implementation/evidence-manifest-harness.md`
- canonical names should follow `docs/implementation/canonical-naming-contract.md`
- codebase-global survey bundles remain documentation-only, but may still create tranche survey docs, area execution SSOT docs, and an aggregate roadmap before any realization work
- `ROL 전역 전체 전수조사` should default to `docs/implementation/codebase-global-survey-coverage-contract.md`
- `ROL 전역 전체 전수조사` should use deep integrity survey mode by default via `docs/implementation/deep-global-integrity-survey-harness.md`
- deep global surveys should use `docs/implementation/single-ssot-roadmap-contract.md`
- deep global survey claims should use `docs/implementation/evidence-triangulation-contract.md`
- deep global survey confidence claims should use `docs/implementation/integrity-confidence-scoring-contract.md`
- multi-item temp execution ordering should use `docs/implementation/queue-priority-rubric.md`
- temp queue state may be materialized with `python scripts/sync_temp_queue_state.py`
- aggregate roadmap auto-build is available via `python scripts/build_execution_roadmap.py`
- evidence manifest generation is available via `python scripts/generate_evidence_manifest.py`
- deep survey bundle validation is available via `python scripts/validate_deep_global_survey_bundle.py --survey-doc <canonical-master-survey-doc>`
- temp queue closure and cleanup should use `docs/implementation/execution-closure-harness.md`
- temp queue integrity checks should use `docs/implementation/ops-validator-harness.md`
- stale-reference sweep automation is available via `python scripts/run_stale_reference_sweep.py`
- process health scorecard auto-population is available via `python scripts/populate_process_health_scorecard.py`
- temporary allowlists or bounded bypasses should use `docs/implementation/exception-registry-harness.md`
- broader operational confidence summaries may use `docs/implementation/process-health-scorecard-harness.md`
- stale authority or stale path cleanup should use `docs/implementation/stale-reference-sweep-harness.md`
- optional `docs/temp/queue-state.json` should follow `docs/implementation/temp-queue-state-contract-v1.json`
- survey-only requests should stop at documentation outputs; for codebase-global survey bundles, that may still include area execution SSOT docs and an aggregate roadmap without entering realization
- a deep codebase-global survey bundle may contain many execution SSOT docs but only one SSOT roadmap
- direct focused patches may use compact mode and should not inflate into full-governance artifacts unless scope or risk justifies it
- shorthand examples: `ROL 전수조사만`, `ROL 실행문서까지`, `ROL 구현까지`, `rol compact bugfix`
- global shorthand examples: `ROL 전역 전체 전수조사만`, `ROL 전역 전체 조사만`

## System Survey Harness (System Track Only)

시스템 오더에서 아래 유형이 들어오면 init harness 다음으로 `docs/implementation/system-full-survey-execution-harness.md`를 읽는다.

- full survey
- master audit
- audit order
- 3-pass audit
- execution SSOT
- remediation execution plan
- 잔여분 inventory 후 실행문서 작성

기본 조사 원칙:

- 전수조사/실행문서 류는 사이드이펙트 조사까지 기본 포함
- 최소 조사 대상: file write, DB write, JSONL/log/audit sink, console/UI 출력, rollback/recovery/retry, cache/global state, bootstrap fallback, config/env mutation
- 해당 항목이 비적용이면 생략하지 말고 문서에 비적용이라고 명시

경로 규칙:

- 전수조사/감리/evidence/side-effect 산출물 기본 경로는 `docs/YYYY-MM-DD/`
- `execution SSOT` 정본은 `docs/YYYY-MM-DD/`
- 같은 `execution SSOT` 카피본을 `docs/temp/`에도 함께 저장
- `docs/temp/` 카피본은 취합/후처리/검토 후 비워도 되지만, 정본 없는 temp 단독 저장은 금지
- `execution SSOT` 수정은 항상 정본(`docs/YYYY-MM-DD/`) 먼저 반영 후 temp 카피본 덮어쓰기
- temp 카피본만 단독 수정하는 운영은 금지
- `execution SSOT`는 가능하면 source survey docs / evidence artifacts / side-effect coverage를 본문 앞부분에 명시
- `docs/temp/` 정리는 정본 존재와 temp 동기화가 확인된 뒤에만 수행
- `docs/temp/`의 실행문서 카피본은 active execution queue로 간주
- 실행문서 실현 완료 후 해당 temp 카피본은 삭제
- temp 안에 실행문서가 2개 이상이면 먼저 전체 실행문서 기준 aggregate roadmap 작성 후 roadmap 순서대로 진행
- roadmap 소진 후에는 temp 내 active execution artifact를 비운다
- 사용자가 다른 경로를 직접 지정하면 그 경로를 우선

## Blockguide First (Narrative Pipeline Only)

이 워크스페이스에서 아래 작업이 들어오면 먼저 `docs/blockguide/SSOT_blockguide-integrated-order.md`를 UTF-8로 읽는다.

- 작품 기획안 작성 또는 수정
- `work_id` 기준 Treatment/BI 생성
- `Phase 0`, `TR draft`, `BI`, 감리, 정합성, 밀도 점검
- 특정 작품/`work_id`가 이미 정해진 상태에서 `다음 스텝`, `계속`, `승인` 기반 자동 진행

그다음 아래 문서를 UTF-8로 읽는다.

1. `docs/blockguide/treatment-planning-harness.md`
2. `docs/blockguide/treatment-production-harness-v2.md`
3. `docs/blockguide/bi-production-harness-v1.md`

대상 작품이 `alt_history`이거나 역사 재료 DB 조회가 필요하면 추가로 아래 문서를 읽는다.

4. `docs/blockguide/alt_history_db_harness.md`

## Narrative Stage Detection

현재 단계는 메모리가 아니라 파일 존재로 판정한다.

- `phase0_design` 없음: planning 단계
- `phase0_design` 있음, `tr_block_070_draft` 없음: production 단계
- `tr_block_070_draft` 있음, `0_bi_{work_id}.json` 없음: BI 단계
- `BI`가 있어도 감리 FAIL이면 완료가 아니다

## Narrative Execution Rules

- 한 번에 1단위만 진행한다.
- 애매하면 더 작은 단위로 쪼갠다.
- `Phase 0` 없이 TR 생성 금지
- `TR draft` 없이 BI 생성 금지
- 감리 PASS 전 완료 선언 금지
- UTF-8 only. `???`, `�` 탐지 시 즉시 중단 후 원인 보고
