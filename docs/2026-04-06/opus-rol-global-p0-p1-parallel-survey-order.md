# ROL 전역 P0-P1 병렬 조사 오더 (Opus용)

Date: 2026-04-06
Status: final
Mode: system-track, read-only global pipeline severity sweep
Scope: live codebase pipeline surfaces only
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`
Baseline Dirty Summary: active Stage4/queue/material edits already present; this survey must not mutate existing dirty files or `docs/temp/`

## 목적

이 문서는 Opus 병렬 조사 오더다.

목표는 하나다.

- 현재 워크스페이스 전역에서 `P0-P1급 문제`가 각 파이프라인에 **이미 살아 있는지** 확인한다.

이 오더는 아래를 하지 않는다.

- 새 lane 제안
- queue 재우선순위화
- 실행 SSOT 작성
- 코드 수정
- fresh run 실행
- closure 선언

즉, 이건 `global read-only severity sweep`이다.
전역 전체를 보되, `P0-P1 후보가 있는가 / 없다면 없다`만 말하면 된다.

## 고정 전제

- 이 오더는 시스템 오더다.
- `AGENTS.md`와 `docs/implementation/system-order-init-harness.md`를 먼저 따른다.
- live code가 1차 authority다. 과거 문서는 baseline 또는 contradiction check로만 쓴다.
- 현재 `docs/temp/`에는 active execution queue가 이미 있다. 이번 조사 wave는 그 queue를 바꾸거나 닫지 않는다.
- 이번 wave는 `pipeline별 고위험도 확인`만 한다. lower-severity backlog 정리는 목적이 아니다.
- `docs/temp/` 수정 금지.
- 코드/설정/DB/아티팩트 수정 금지.
- 기존 dirty worktree 파일 수정 금지.
- 조사 산출물은 `docs/2026-04-06/` 아래 assigned output 문서만 허용한다.

## P0-P1 판정 계약

### `P0`

아래 중 하나에 해당하면 `P0` 후보다.

- 현재 live code path가 canonical artifact나 DB truth를 잘못 덮어쓸 수 있다
- destructive overwrite, wrong-project write, wrong-stage write, authority inversion이 현재 경로에 열려 있다
- false PASS/false closure가 authoritative sink에 persisted 될 수 있다
- 복구 가능한 경고가 아니라, 한 번 실행하면 손상이나 대형 오판을 남길 수 있다

### `P1`

아래 중 하나에 해당하면 `P1` 후보다.

- 현재 live code path가 높은 확률로 잘못된 canonical output을 만든다
- authoritative readback/snapshot/summary가 current truth를 거짓으로 보여 준다
- stage handoff나 repair/gate contract가 깨져서 front execution을 잘못 이끈다
- operator가 runtime state를 안전하지 않게 오판할 정도의 sink mismatch가 있다
- 지금 즉시 코드수정이 없더라도, fresh run 전 bounded fix를 진지하게 검토해야 하는 급이다

### `P2 이하로 내리는 규칙`

아래면 `P0-P1`로 올리지 마라.

- concrete consumer path가 없다
- sink/owner/consequence 연결고리가 약하다
- purely speculative hotspot이다
- cosmetic/readability/cleanup 수준이다
- long-term debt는 맞지만 지금 실행 안전성에는 직접 안 닿는다

## 공통 질문

모든 terminal은 아래 4문장에 답해야 한다.

1. 이 lane에 `live P0-P1`이 있나, 없나
2. 있다면 정확히 어떤 `entry -> owner -> sink -> consequence` 경로인가
3. 가장 좁은 owner file 1~3개는 무엇인가
4. 지금 결론이 static evidence만으로 충분한가, 아니면 `fresh run required`인가

`없다`면 반드시 명시적으로 `no live P0-P1 found in this lane`라고 적는다.

## 공통 읽기 목록

모든 terminal은 먼저 아래만 읽는다.

- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/codebase-global-survey-coverage-contract.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/temp/execution-roadmap.md`

주의:

- `docs/temp/execution-roadmap.md`는 context only다
- queue를 바꾸거나 successor lane을 새로 파지 마라
- canonical execution SSOT를 수정하지 마라

## Terminal Ownership

### Terminal 1

Owner:
- bootstrap, project binding, router, upstream handoff

Focus files:

- `main_a.py`
- `modules/core/project_manager.py`
- `modules/core/project_support.py`
- `scripts/narrative_router.py`
- `modules/narrative_router/router.py`
- `modules/narrative_router/families/blockguide.py`
- `modules/narrative_router/families/wuxguide.py`
- `scripts/stage0_handoff_validator.py`
- `contracts/source_manifest.schema.json`
- `contracts/profile_lock.schema.json`
- `contracts/material_bundle_summary.schema.json`
- `contracts/phase0_ready_snapshot.schema.json`

Required questions:

1. 잘못된 project binding, fallback project, wrong-stage routing이 live P0-P1인가
2. upstream handoff contract가 조용히 비거나 엇갈려도 run이 계속되는 경로가 있나
3. router/handoff 쪽 authority owner는 어디까지가 가장 좁은 owner set인가
4. 이 lane의 위험이 static code만으로 확정 가능한가

Output:

- `docs/2026-04-06/rol-global-terminal1-bootstrap-router-handoff-p0p1.md`

### Terminal 2

Owner:
- Stage2 generation, normalization, validation, finalization

Focus files:

- `modules/domain/agents/arc_ensemble.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_validation_pipeline.py`
- `modules/core/stage2_entity_contract.py`
- `modules/core/stage2_optimizer.py`
- `modules/core/stage2_finalizer.py`

Required questions:

1. Stage2에서 false PASS, wrong canonicalization, entity/numeric drift persistence가 P0-P1로 열려 있나
2. Stage2 validation과 finalizer 사이에 authoritative truth가 바뀌거나 빠지는 seam이 있나
3. 이 lane에서 지금 가장 위험한 owner file 1~3개는 무엇인가
4. 지금 보이는 위험이 front blocker인가, 아니면 fresh run 전 watchlist인가

Output:

- `docs/2026-04-06/rol-global-terminal2-stage2-pipeline-p0p1.md`

### Terminal 3

Owner:
- Stage3 blueprint pipeline, carryover, continuity, prevalidation

Focus files:

- `modules/domain/agents/three_phase_blueprint_generator.py`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/chief_writer.py`
- `modules/domain/agents/chief_writer_context.py`
- `modules/domain/agents/chief_writer_context_packets.py`
- `modules/core/stage3_orchestrator.py`

Required questions:

1. Stage3에서 blueprint truth loss, carryover misread, continuity false clean이 P0-P1로 열려 있나
2. validator PASS와 final blueprint artifact truth가 갈라질 live seam이 있나
3. Pin/inventory/carryover family가 지금도 front P1인지, 아니면 bounded residue인지
4. owner file는 `generator / validator / context / orchestrator` 중 어디가 제일 좁은가

Output:

- `docs/2026-04-06/rol-global-terminal3-stage3-pipeline-p0p1.md`

### Terminal 4

Owner:
- Stage4 consumer, gate, repair-contract, numeric carryover, authority readback

Focus files:

- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_director_runtime.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/db_manager.py`
- `modules/core/failure_analyzer.py`

Required questions:

1. Stage4에서 false PASS_WITH_FIX, wrong fix_scope/repair_scope authority, numeric carryover misauthority가 live P0-P1인가
2. gate -> repair -> persistence -> summary readback 중 어디가 가장 먼저 틀어지나
3. current front queue와 직접 연결되는 P1이 실제로 남아 있나
4. 가장 좁은 owner set은 무엇인가

Output:

- `docs/2026-04-06/rol-global-terminal4-stage4-pipeline-p0p1.md`

### Terminal 5

Owner:
- persistence, observability, operator surface, bridge/app shell, validation summary

Focus files:

- `modules/core/session_logger.py`
- `modules/core/quality_dashboard.py`
- `modules/core/services/audit_service.py`
- `modules/core/stage4_canary_tools.py`
- `modules/api/bridge_server.py`
- `geuldobi-desktop/src/main.js`
- `tests/test_stage4_canary_tools.py`
- `tests/test_failure_analyzer.py`

Required questions:

1. operator가 현재 state를 거짓으로 읽게 만드는 summary/sink mismatch가 live P0-P1인가
2. bridge/dashboard/app shell이 stale authority를 더 권위 있어 보이게 만드는가
3. canary/summary 계열이 false clean을 낼 수 있는가
4. 이 lane의 위험이 pipeline bug인지 observability bug인지 분리 가능한가

Output:

- `docs/2026-04-06/rol-global-terminal5-observability-bridge-p0p1.md`

## Output Contract

각 terminal은 아래를 지켜야 한다.

- read-only only
- assigned output 문서 1개만 작성
- findings first
- `P0`, `P1`, `no live P0-P1 found` 중 하나를 문서 첫 섹션에서 명시
- exact file path를 적는다
- speculative issue는 `watchlist only`로 분리한다
- queue 변경 제안 금지
- 코드 패치 제안은 해도 되지만 `future implementation`으로만 적는다
- 문서 마지막 줄은 정확히 아래 문장으로 끝낸다

`read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output`

## Synthesis Rules

다섯 terminal 결과를 합칠 때는 아래 순서를 따른다.

1. `live P0가 있는가`
2. `live P1이 어느 pipeline에 남아 있는가`
3. `pipeline별 no live P0-P1 found` 여부
4. `가장 좁은 owner set`
5. `fresh run 전에 고쳐야 하는가 / fresh run으로 먼저 확인해도 되는가`

합성자는 아래를 하면 안 된다.

- lower-severity debt를 P1로 승격
- queue를 새로 짠다
- implementation SSOT를 대신 작성한다
- closure나 해결 선언을 한다

## Paste-Ready Orders

### Opus Terminal 1

```text
시스템 오더다. 전역 read-only 조사다. 목표는 `bootstrap / project binding / router / upstream handoff`에서 live P0-P1이 있는지 확인하는 것이다.

먼저 읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/codebase-global-survey-coverage-contract.md
- docs/implementation/document-3pass-audit-harness.md
- docs/temp/execution-roadmap.md

집중 파일:
- main_a.py
- modules/core/project_manager.py
- modules/core/project_support.py
- scripts/narrative_router.py
- modules/narrative_router/router.py
- modules/narrative_router/families/blockguide.py
- modules/narrative_router/families/wuxguide.py
- scripts/stage0_handoff_validator.py
- contracts/source_manifest.schema.json
- contracts/profile_lock.schema.json
- contracts/material_bundle_summary.schema.json
- contracts/phase0_ready_snapshot.schema.json

질문:
1. wrong project binding, fallback project, wrong-stage routing이 live P0-P1인가
2. handoff contract가 조용히 비거나 엇갈려도 run이 계속되는 경로가 있나
3. entry -> owner -> sink -> consequence를 가장 짧게 적으면 어떻게 되나
4. 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-06/rol-global-terminal1-bootstrap-router-handoff-p0p1.md

규칙:
- read-only only
- 코드/설정/DB/docs-temp 수정 금지
- findings first
- 첫 섹션에서 `P0`, `P1`, `no live P0-P1 found` 중 하나를 명시
- speculative 건은 `watchlist only`로 따로 빼라
- 마지막 줄은 정확히 아래 문장으로 끝내라

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

### Opus Terminal 2

```text
시스템 오더다. 전역 read-only 조사다. 목표는 `Stage2 pipeline`에서 live P0-P1이 있는지 확인하는 것이다.

먼저 읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/codebase-global-survey-coverage-contract.md
- docs/implementation/document-3pass-audit-harness.md
- docs/temp/execution-roadmap.md

집중 파일:
- modules/domain/agents/arc_ensemble.py
- modules/core/stage2_preflight.py
- modules/core/stage2_validation_pipeline.py
- modules/core/stage2_entity_contract.py
- modules/core/stage2_optimizer.py
- modules/core/stage2_finalizer.py

질문:
1. false PASS, wrong canonicalization, entity/numeric drift persistence가 live P0-P1인가
2. validation과 finalizer 사이에 authoritative truth가 바뀌거나 빠지는 seam이 있나
3. entry -> owner -> sink -> consequence를 가장 짧게 적으면 어떻게 되나
4. 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-06/rol-global-terminal2-stage2-pipeline-p0p1.md

규칙:
- read-only only
- 코드/설정/DB/docs-temp 수정 금지
- findings first
- 첫 섹션에서 `P0`, `P1`, `no live P0-P1 found` 중 하나를 명시
- speculative 건은 `watchlist only`로 따로 빼라
- 마지막 줄은 정확히 아래 문장으로 끝내라

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

### Opus Terminal 3

```text
시스템 오더다. 전역 read-only 조사다. 목표는 `Stage3 pipeline`에서 live P0-P1이 있는지 확인하는 것이다.

먼저 읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/codebase-global-survey-coverage-contract.md
- docs/implementation/document-3pass-audit-harness.md
- docs/temp/execution-roadmap.md

집중 파일:
- modules/domain/agents/three_phase_blueprint_generator.py
- modules/domain/agents/unified_blueprint_validator.py
- modules/domain/agents/chief_writer.py
- modules/domain/agents/chief_writer_context.py
- modules/domain/agents/chief_writer_context_packets.py
- modules/core/stage3_orchestrator.py

질문:
1. blueprint truth loss, carryover misread, continuity false clean이 live P0-P1인가
2. validator PASS와 final blueprint artifact truth가 갈라질 live seam이 있나
3. Pin/inventory/carryover family는 지금 front P1인가, 아니면 bounded residue인가
4. 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-06/rol-global-terminal3-stage3-pipeline-p0p1.md

규칙:
- read-only only
- 코드/설정/DB/docs-temp 수정 금지
- findings first
- 첫 섹션에서 `P0`, `P1`, `no live P0-P1 found` 중 하나를 명시
- speculative 건은 `watchlist only`로 따로 빼라
- 마지막 줄은 정확히 아래 문장으로 끝내라

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

### Opus Terminal 4

```text
시스템 오더다. 전역 read-only 조사다. 목표는 `Stage4 pipeline`에서 live P0-P1이 있는지 확인하는 것이다.

먼저 읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/codebase-global-survey-coverage-contract.md
- docs/implementation/document-3pass-audit-harness.md
- docs/temp/execution-roadmap.md

집중 파일:
- modules/core/stage4_orchestrator.py
- modules/core/stage4_context_builder.py
- modules/core/stage4_director_runtime.py
- modules/core/stage4_interview_round.py
- modules/core/db_manager.py
- modules/core/failure_analyzer.py

질문:
1. false PASS_WITH_FIX, wrong fix_scope/repair_scope authority, numeric carryover misauthority가 live P0-P1인가
2. gate -> repair -> persistence -> summary readback 중 어디가 가장 먼저 틀어지나
3. current front queue와 직접 연결되는 P1이 실제로 남아 있나
4. 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-06/rol-global-terminal4-stage4-pipeline-p0p1.md

규칙:
- read-only only
- 코드/설정/DB/docs-temp 수정 금지
- findings first
- 첫 섹션에서 `P0`, `P1`, `no live P0-P1 found` 중 하나를 명시
- speculative 건은 `watchlist only`로 따로 빼라
- 마지막 줄은 정확히 아래 문장으로 끝내라

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

### Opus Terminal 5

```text
시스템 오더다. 전역 read-only 조사다. 목표는 `persistence / observability / bridge / app shell`에서 live P0-P1이 있는지 확인하는 것이다.

먼저 읽을 것:
- AGENTS.md
- docs/implementation/system-order-init-harness.md
- docs/implementation/codebase-global-survey-coverage-contract.md
- docs/implementation/document-3pass-audit-harness.md
- docs/temp/execution-roadmap.md

집중 파일:
- modules/core/session_logger.py
- modules/core/quality_dashboard.py
- modules/core/services/audit_service.py
- modules/core/stage4_canary_tools.py
- modules/api/bridge_server.py
- geuldobi-desktop/src/main.js
- tests/test_stage4_canary_tools.py
- tests/test_failure_analyzer.py

질문:
1. operator가 현재 state를 거짓으로 읽게 만드는 summary/sink mismatch가 live P0-P1인가
2. bridge/dashboard/app shell이 stale authority를 더 권위 있게 보이게 만드는가
3. canary/summary 계열이 false clean을 낼 수 있는가
4. pipeline bug와 observability bug를 분리하면 가장 좁은 owner file 1~3개는 무엇인가

산출물:
- docs/2026-04-06/rol-global-terminal5-observability-bridge-p0p1.md

규칙:
- read-only only
- 코드/설정/DB/docs-temp 수정 금지
- findings first
- 첫 섹션에서 `P0`, `P1`, `no live P0-P1 found` 중 하나를 명시
- speculative 건은 `watchlist only`로 따로 빼라
- 마지막 줄은 정확히 아래 문장으로 끝내라

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
```

## 3-Pass Audit

- Pass 1: 문서 유형을 `survey-only parallel order`로 고정했고, execution SSOT/queue 문서와 역할이 섞이지 않게 분리했다.
- Pass 2: terminal별 파일 경로가 실제 워크스페이스에 존재하는지 확인했고, 공통 금지사항이 active temp queue와 충돌하지 않게 맞췄다.
- Pass 3: 각 terminal이 `P0-P1 존재 여부`, `owner`, `sink`, `fresh-run 필요성`만 답하도록 좁혀서 과잉 조사나 lane 증설로 번지지 않게 다듬었다.
- Confidence: 0.97
