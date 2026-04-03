# Workspace Instructions

Pipeline Order: `리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성 -> 글도비 파이프라인`

## SSOT

- 현재 워크스페이스 운영 SSOT는 `AGENTS.md`
- `CLAUDE.md`는 호환용 shim이며 독립 운영 기준으로 쓰지 않는다

## 대원칙 (절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python은 데이터 수집·포맷팅·전달만. "오류인가?", "수정할까?" 같은 판단은 LLM 에이전트가 담당.
2. **팩트시트 수정 권한은 LLM만** — NPC 속성, 세계관 설정, 관계도를 수정하는 건 LLM뿐. Python이 자동으로 팩트를 덮어쓰면 안 됨.
3. **디렉터 주권주의 (내각제)** — Director가 최종 품질 결정권. Chief Writer·Analyst 등은 초안 제출만, 합격/불합격/수정 지시는 Director가 내림. Director를 우회하면 안 됨.
4. **사망 캐릭터는 회상/언급만 허용** — `deceased=True` NPC가 행동/대사로 등장하면 REJECT. 회상·과거 장면·타인 언급은 허용.

## Track Split

이 워크스페이스의 오더는 아래 두 트랙으로 분리한다.

- `글도비 시스템 오더`
  - 코드베이스 조사/수정, `main_a.py`, `modules/`, `scripts/`, `tests/`, `UI/`, `geuldobi-desktop/`, 런타임, DB, 회귀, 리팩터, 성능, 로깅, control plane, persistence, process runner, desktop/app 연결, `docs/20xx-xx-xx/` 아래 시스템 감사 오더
  - 이 경우 **블록가이드 문서를 먼저 읽지 않는다.**
  - `phase0_design`, `tr_block_070_draft`, `BI` 파일 존재로 단계를 판정하지 않는다. (이 규칙은 시스템 오더 트랙에만 적용. 서사 파이프라인 오더에서는 SSOT_stage0_preprocess_integrated_order.md §3의 파일 존재 기반 단계 판정을 따른다.)
- `서사 파이프라인 오더`
  - 작품 기획, `work_id` 기반 `Treatment/BI`, `Phase 0`, `TR draft`, `BI`, 감리, 정합성, 밀도 점검, 전처리 handoff, 작품 기준 `다음 스텝/계속/승인`
  - 이 경우에만 아래 `Narrative Router First` 규칙과 `AGENTS.narrative-router.md`를 적용한다.

판정 원칙:

- 대상이 코드/시스템/앱/테스트면 시스템 오더다.
- 대상이 작품/`work_id`/`treatments/`/`bible/` 산출물이면 서사 파이프라인 오더다.
- `다음 스텝`, `계속`, `승인`만으로는 narrative-router 트리거가 아니다. 현재 대상이 작품 파이프라인일 때만 트리거다.

## Document Save Rule

사람이 읽는 문서는 기본적으로 `3pass 감리 후 저장`을 원칙으로 한다.

- 대상: survey, audit, execution SSOT, harness, README, 운영 노트, 보고 문서
- 순서: draft -> pass1 -> pass2 -> pass3 -> final save
- 3pass가 끝나도 추정 확신도 95% 미만이면 추가 감리를 반복하고 final save 하지 않는다
- `execution SSOT`의 `docs/temp/` 카피본도 3pass 감리 완료 및 확신도 95% 달성 후에만 생성/갱신
- raw evidence txt/json 생성 자체는 조사 중간에 가능하지만, 그것을 해석하거나 결론화한 문서는 3pass 감리 전 저장 완료로 취급하지 않는다
- `execution SSOT` 또는 `aggregate roadmap`을 근거로 실제 코드 수정에 착수할 때는, 착수 시점의 최신 workspace 상태를 기준으로 해당 문서를 다시 3pass 감리하고 확신도 95% 이상을 재확인한 뒤에만 수정 작업을 시작한다

## 정책 결정 사항

1. **DB 최대 보존 정책** — DB의 `TEXT` 컬럼에 저장하는 진단·판정·사유 필드는 Python에서 절삭(`[:N]`)하지 않는다. SQLite `TEXT`는 길이 제한이 없으며, 런타임 증거는 최대한 보존한다. 축소·정리·아카이빙은 별도 정리 웨이브에서만 수행한다.
2. **콘솔 로그 최대 표시 정책** — Director thinking, advisory 경고, 판정 사유 등 운영자가 실행 중 판단 근거를 확인해야 하는 로그는 콘솔에서 축약·생략하지 않고 최대한 표시한다.

## Encoding Guardrails

- UTF-8은 시스템 오더와 서사 파이프라인 오더를 모두 포함하는 워크스페이스 전역 불변식이다.
- touched text/code/doc/config 파일은 `cp949`, `euc-kr`, `latin-1`, replacement fallback 기반 저장 또는 blind decode를 금지한다.
- touched 파일에는 `three-question placeholder`, `U+FFFD`, non-ASCII 인접 `?`, Hangul/CJK mixed-script mojibake token을 남기지 않는다. archival evidence나 literal example이 꼭 필요하면 명시적 `utf8-hygiene: allow-line` 또는 `utf8-hygiene: allow-file` marker와 rationale을 함께 둔다.
- 터미널 출력만 깨졌을 가능성이 있으면 출력 렌더링을 근거로 패치하지 말고, explicit UTF-8 reader로 source bytes를 재확인한 뒤 수정한다.
- 콘솔 렌더링, `Get-Content`, PowerShell stdout, IDE preview text는 **인코딩 판정 근거가 아니다**. 탐색용으로만 쓰고, mojibake/손상/문장 파손 판정이나 패치 근거로 승격하지 않는다.
- 인코딩 관련 수정이나 "파일이 깨졌다"는 주장 전에는 반드시 `read_bytes() -> UTF-8 decode` 또는 동급의 byte-level read-back을 수행한다. DB/anchor/payload가 authoritative source면 파일 preview보다 DB read-back을 우선한다.
- 콘솔/preview와 byte-level read-back이 충돌하면 **byte-level read-back이 승리**한다. 이 경우 콘솔 출력 기준 패치, 콘솔 출력 인용 판단, 콘솔 출력 기반 회귀 판정을 금지한다.
- 인코딩 이슈 조사에서 `Get-Content`류 출력은 최종 evidence 섹션에 단독 anchor로 적지 않는다. evidence에는 bytes/hash/UTF-8 decode 결과 또는 authoritative DB payload만 남긴다.
- 기본 가드레일은 `.editorconfig`의 UTF-8 pin과 `scripts/check_utf8_hygiene.py` + pre-commit hook이다.

## Complexity Guardrails

- 이 워크스페이스의 시스템 오더는 `사후 대형 장함수 청소`보다 `사전 복잡도 회귀 방지`를 우선한다.
- touched production 함수는 정당한 예외 없이 새로 `180+ LOC` 구간에 진입하면 안 된다.
- touched production 함수가 `120+ LOC`에 들어가면, 구현 중 최소 한 번은 `bounded shell / semantic core / sink boundary` 중 어디에 속하는지 명시적으로 판정한다.
- 같은 owner class 안에서 helper를 계속 추가해 direct-method pressure만 올리는 패턴을 금지한다. owner가 `50+ direct methods`이거나, 한 family 정리 때문에 새 helper가 3개 이상 늘어날 조짐이 보이면 same-file extraction 전에 `module/runtime split` 가능성을 먼저 검토한다.
- `180+ = 0` 또는 `200+ = 0` 같은 고위험 band가 이미 제거된 상태에서는, 추가 same-file 분해보다 `module boundary`, `contract normalization`, `fresh run validation`을 우선순위로 둔다.
- 시간 압박이 있는 구간에서 고위험 band가 이미 제거됐다면, 대규모 리팩토링보다 `snapshot commit -> fresh run -> fail-only bugfix` 순서를 우선한다.
- substantial system-track code 변경 후에는 최소 touched area 기준 complexity recount를 수행하고, hotspot lane / roadmap / execution SSOT 작업이면 SSOT에도 현재 band 또는 hotspot delta를 반영한다.

## External Advisory

- optional third-party advisory systems may be vendored under `.agents/skills/`
- the current external advisory entrypoint is `.agents/skills/gary-advisory/SKILL.md`
- the vendored upstream source for that wrapper is `.agents/skills/gstack`
- external advisory is advisory-only and never outranks `AGENTS.md`, Director authority, canonical docs, queue order, or fact ownership
- external advisory runs stay read-only unless the user separately asks for internal implementation after the advisory
- direct canonical doc edits, `docs/temp/` mutation, DB writes, deploy or ship flows, QA automation, browser automation, and git-history mutation are disallowed under external advisory mode
- if upstream advice conflicts with workspace governance, label it `EXTERNAL_ADVISORY_CONFLICT` and let the internal Director or system-track flow decide
- detailed operating rules live in `docs/implementation/gary-external-advisory-harness.md`

## System Init Harness (System Track Only)

시스템 오더는 먼저 `docs/implementation/system-order-init-harness.md`를 읽는다.

- 이 하네스가 temp queue 점검, 현재 모드 판정, 다음으로 읽을 하네스 선택을 담당
- 필요 시 `system-full-survey-execution-harness`, `live-run-merge-survey-harness`, `temp-execution-queue-roadmap-harness`, `document-3pass-audit-harness`로 내려간다
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
- `ROL 전수조사-실전테스트 병행` and `ROL live-merge` should use `docs/implementation/live-run-merge-survey-harness.md`
- live-merge mode means `static survey + fresh live run + post-run merge audit`; completed live-run evidence beats static inference, and stale survey text remains lower authority
- during active live-merge mode, raw evidence and explicit draft watchlists may be saved, but canonical final survey conclusions, execution SSOT mirrors, roadmap closure, and "resolved/regressed" claims wait until the live run completes and the merged 3-pass audit finishes
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
- live-merge shorthand examples: `ROL 전수조사-실전테스트 병행`, `ROL live-merge`, `fresh live run + global survey`
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
- fresh live run 병행 조사
- 실전테스트 중 전수조사

기본 조사 원칙:

- 전수조사/실행문서 류는 사이드이펙트 조사까지 기본 포함
- 최소 조사 대상: file write, DB write, JSONL/log/audit sink, console/UI 출력, rollback/recovery/retry, cache/global state, bootstrap fallback, config/env mutation
- 조사 범위에 실제 산출물(blueprint, manuscript, episode artifact)이 포함되면 로그/DB/hash만 보지 말고 실물 파일 본문도 직접 조사한다.
- 실제 산출물 조사는 최소 `artifact truth`(존재/bytes/hash), `metadata truth`(DB/JSONL/summary/rationale linkage), `narrative truth`(본문 내용 모순, blueprint/selection/verdict와의 불일치) 3층을 함께 다룬다.
- 해당 항목이 비적용이면 생략하지 말고 문서에 비적용이라고 명시
- fresh live run을 병행하는 경우에는 `docs/implementation/live-run-merge-survey-harness.md`를 함께 읽고, run 중에는 raw evidence와 draft watchlist만 확정하며 final SSOT/closure는 post-run merge audit 이후에만 저장

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

## Narrative Router First (Narrative Pipeline Only)

이 워크스페이스에서 아래 작업이 들어오면 먼저 `docs/narrative-router/SSOT_narrative-router-integrated-order.md`를 UTF-8로 읽는다.

- 작품 기획안 작성 또는 수정
- `work_id` 기준 Treatment/BI 생성
- `Phase 0`, `TR draft`, `BI`, 감리, 정합성, 밀도 점검
- 특정 작품/`work_id`가 이미 정해진 상태에서 `다음 스텝`, `계속`, `승인` 기반 자동 진행

그다음 router가 family를 판정하고 해당 family 문서를 UTF-8로 읽는다.

세부 family read order, operator runbook, routed CLI 예시는 충돌 완화를 위해 루트 `AGENTS.md`에 길게 적지 않고 `AGENTS.narrative-router.md`에서 관리한다.

핵심만 요약:

- 현판/헌터/현대판타지 business-power 계열은 `blockguide`
- 무협/선협/강호/문파/경지 중심 작품은 `wuxguide`
- 사용자가 family를 직접 지정하면 그 지시를 우선
- 애매하면 `docs/narrative-router/SSOT_narrative-router-integrated-order.md`와 `AGENTS.narrative-router.md`의 판정 절차를 따른다

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
- UTF-8 only. triple-question placeholder, `U+FFFD`, 또는 mixed-script mojibake 탐지 시 즉시 중단 후 원인 보고

## Pytest Memory Rule

- `pytest`는 기본적으로 메모리 보수 모드로 실행한다.
- 병렬 실행(`-n`, `xdist`, auto worker)은 사용자가 명시적으로 요구하고 메모리 여유가 확인된 경우에만 허용한다.
- 기본 검증은 전체 스위트 일괄 실행보다 대상 파일/영역 기준 순차 shard 실행을 우선한다.
- 메모리 압박이나 OOM 징후가 있으면 즉시 더 작은 shard로 쪼개서 순차 재실행한다.
- `pytest` 또는 `scripts/run_pytest_lowmem.py`가 중단, 타임아웃, 사용자 abort로 끝났다면 바로 live `python` 프로세스를 커맨드라인 기준으로 확인하고, 테스트 runner/child만 종료한다.
- 이 정리 단계에서는 IDE 언어 서버나 unrelated `python` 프로세스를 종료하지 않는다.
- `logs/pytest_lowmem/`는 임시 검증 산출물로 취급한다. 필요한 pass/fail 근거를 확인한 뒤 stale 로그는 정리한다.
- 검증 보고에는 어떤 테스트 파일 또는 shard를 어떤 순서로 돌렸는지 짧게 남긴다.
