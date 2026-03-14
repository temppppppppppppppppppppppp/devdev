# Global Detail Full Survey Remediation Execution SSOT

작성일: 2026-03-13
상태: `execution-ready`
기준 조사:
- `global-detail-full-survey-consolidated-findings.md`
- `global-detail-full-survey-consolidated-findings-3pass-reaudit.md`
문서 역할: 전역 디테일 전수조사 `retained open set 21건`을 실제 후속 실행 단위, 순서, acceptance, gate로 다시 잠그는 단일 SSOT 오더
금지사항: 본 문서는 코드 수정 기록, 테스트 실행 로그, rerun 결과 보고서가 아니다. 범위 고정, 우선순위 잠금, acceptance 정의까지만 담당한다.

## 1. 기준 문서

- `docs/2026-03-13/global-detail-full-survey-master-audit-order.md`
- `docs/2026-03-13/global-detail-full-survey-baseline-ledger.md`
- `docs/2026-03-13/global-detail-full-survey-consolidated-findings.md`
- `docs/2026-03-13/global-detail-full-survey-consolidated-findings-3pass-reaudit.md`
- `docs/2026-03-13/GDFS-T1-live-code-hidden-branch-findings.md`
- `docs/2026-03-13/GDFS-T2-persistence-artifact-evidence-findings.md`
- `docs/2026-03-13/GDFS-T3-config-contract-ssot-drift-findings.md`
- `docs/2026-03-13/GDFS-T4-ui-api-desktop-operator-surface-findings.md`
- `docs/2026-03-13/GDFS-T5-test-canary-runtime-proof-findings.md`
- `docs/2026-03-13/GDFS-T6-tools-lite-mode-live-consumer-residue-findings.md`

## 2. Executive Summary

- 이번 실행 범위는 전역 retained set `21건 (P1 6 / P2 14 / P3 1)`을 중복 없는 실행 단위 `5개`로 재배열하는 것이다.
- 목표는 다시 총건수를 세는 것이 아니라, `live producer-consumer contract`, `persistence/recovery boundary`, `config/API/operator SSOT`, `runtime proof`, `manual-only legacy surface`를 한 번에 같은 순서로 닫는 것이다.
- `P0`는 없다. 따라서 이번 SSOT는 emergency patch 문서가 아니라 `execution order + acceptance contract` 문서다.
- 권장 실행 순서는 `GDFS-E1 -> GDFS-E2 -> GDFS-E3 -> GDFS-E4 -> GDFS-E5`다.
- 이번 턴의 산출물은 문서뿐이며, 실제 코드 수정은 이 SSOT를 기준으로 한 후속 execution 턴에서만 수행한다.

## 3. Scope

포함:
- `main_a.py`
- `modules/core/stage0/*`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_*`
- `modules/core/stage3_*`
- `modules/core/services/project_service.py`
- `modules/core/reflexion_manager.py`
- `modules/core/db_manager.py`
- `modules/core/project_support.py`
- `modules/core/quality_sidecar_bootstrap.py`
- `modules/core/services/audit_service.py`
- `modules/api/bridge_server.py`
- `modules/core/runtime_paths.py`
- `scripts/build_bi_from_phase0_and_tr.py`
- `scripts/run_stage4_canary.py`
- `modules/core/stage4_canary_tools.py`
- `config/`
- `docs/implementation/`
- `전처리_ssot/contracts/`
- `전처리_ssot/docs/`
- `lite_mode/`
- `tools/`, `tools2/`, `main_tools/`
- root `main.js`, root `temp-*`, `MagicMock/`
- 관련 focused regression tests와 runtime-proof docs

제외:
- 전면 UI redesign
- 제품 배포/installer/version bump
- unrelated repo-wide refactor
- historical artifact 전체 backfill
- 이번 턴에서의 실제 canary/rerun 실행

## 4. 실행 원칙

### 원칙 A. fresh proof 전에 live contract split을 먼저 닫는다

- producer-consumer shape가 갈라진 상태에서 fresh canary를 찍어도 새 stale evidence만 생긴다.
- 따라서 `GDFS-E1~E3`가 `GDFS-E4`보다 먼저다.

### 원칙 B. save-hook, wrapper, manual note는 producer truth의 대체재가 아니다

- save 시점 보정, post-hoc summary, operator memo로 contract 공백을 덮지 않는다.
- producer가 내야 할 필드와 consumer가 받는 필드는 같은 SSOT를 따라야 한다.

### 원칙 C. operator-facing 문서와 contract는 code green의 부속물이 아니라 독립 gate다

- spec, README, archive locator note, bridge detail이 runtime과 다른 신호를 내면 close로 보지 않는다.

### 원칙 D. runtime proof는 hard gate pass만으로 충분하지 않다

- canary `pass`는 lineage/basic sink alignment proof일 뿐이다.
- current rationale/provenance sink proof는 별도 companion audit까지 있어야 닫힌다.

### 원칙 E. manual-only / legacy surface는 live path가 명확해진 뒤 격리한다

- shadow main, Lite Mode, host-bound tools를 먼저 삭제/이동하지 않는다.
- active live surface를 고정한 뒤 수동 표면을 `manual-only` 또는 `stale`로 격리한다.

## 5. Baseline Retained Set -> Execution Unit Mapping

| Finding | Severity | Execution Unit | 실행 의미 |
|---|---|---|---|
| `GDFS-T1-001` | `P1` | `GDFS-E1` | reverse feedback producer-consumer closure |
| `GDFS-T1-002` | `P2` | `GDFS-E1` | `plot_roadmap` producer contract uplift |
| `GDFS-T2-001` | `P1` | `GDFS-E1` | Stage3 structured sink join key closure |
| `GDFS-T2-002` | `P1` | `GDFS-E1` | Stage3 rationale persistence closure |
| `GDFS-T3-002` | `P1` | `GDFS-E1` | `phase0_design` producer-consumer shape unification |
| `GDFS-T1-003` | `P2` | `GDFS-E2` | transaction boundary normalization |
| `GDFS-T2-003` | `P2` | `GDFS-E2` | runtime digest sink uplift |
| `GDFS-T2-004` | `P2` | `GDFS-E2` | restore compensation hardening |
| `GDFS-T3-001` | `P1` | `GDFS-E3` | threshold single-truth alignment |
| `GDFS-T3-003` | `P2` | `GDFS-E3` | fallback/test threshold alignment |
| `GDFS-T3-004` | `P2` | `GDFS-E3` | preprocess resume SSOT normalization |
| `GDFS-T4-001` | `P1` | `GDFS-E3` | required project contract normalization |
| `GDFS-T4-002` | `P2` | `GDFS-E3` | websocket formal contract uplift |
| `GDFS-T4-003` | `P2` | `GDFS-E3` | operator POV surface normalization |
| `GDFS-T5-001` | `P2` | `GDFS-E3` | contract regression gate expansion |
| `GDFS-T5-002` | `P2` | `GDFS-E4` | fresh runtime proof companion audit |
| `GDFS-T5-003` | `P2` | `GDFS-E4` | archive proof index/note refresh |
| `GDFS-T6-001` | `P2` | `GDFS-E5` | Lite Mode manual-only containment |
| `GDFS-T6-002` | `P2` | `GDFS-E5` | shadow main containment |
| `GDFS-T6-003` | `P2` | `GDFS-E5` | host-bound DB tool isolation |
| `GDFS-T6-004` | `P3` | `GDFS-E5` | residue/live-inventory hygiene split |

## 6. Execution Units

### GDFS-E1. Cross-Stage Producer / Consumer Contract Closure

대상 finding:

- `GDFS-T1-001`
- `GDFS-T1-002`
- `GDFS-T2-001`
- `GDFS-T2-002`
- `GDFS-T3-002`

대상 파일:

- `main_a.py`
- `modules/core/stage0/__init__.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage2_finalizer.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- `scripts/build_bi_from_phase0_and_tr.py`
- `전처리_ssot/contracts/artifact_contracts.json`

구현 원칙:

- producer가 내야 할 `plot_roadmap`, attempt/artifact join key, rationale field를 save-hook이나 side sink에 맡기지 않는다.
- Stage3 -> Stage2 reverse feedback는 actual producer가 남긴 structured source를 읽어야 하며 dead consumer branch만 남겨 두지 않는다.
- `phase0_design`는 contract와 consumer가 같은 shape를 보게 만든다.

acceptance:

- reverse feedback는 producer가 실제로 기록하거나, consumer branch가 live path가 아닌 것으로 명시 제거된다.
- `plot_roadmap`는 생성 결과 contract에서 직접 보장된다.
- Stage3 final sink set이 `attempt_key`, `candidate_key`, `artifact_path`, rationale fields를 같은 lineage로 복원 가능하게 남긴다.
- BI consumer와 `phase0_design` contract가 wrapper/flat shape를 두고 충돌하지 않는다.

필수 테스트:

- `tests/test_stage01_helpers.py`
- `tests/test_stage3_orchestrator.py`
- `tests/test_db_manager.py`
- BI consumer shape regression
- Stage3 -> Stage2 producer-consumer integration regression

### GDFS-E2. Persistence / Transaction / Recovery Boundary Hardening

대상 finding:

- `GDFS-T1-003`
- `GDFS-T2-003`
- `GDFS-T2-004`

대상 파일:

- `modules/core/reflexion_manager.py`
- `modules/core/db_manager.py`
- `modules/core/services/audit_service.py`
- `modules/core/services/project_service.py`
- 관련 audit/restore tests

구현 원칙:

- direct `conn.commit()` bypass는 persistence contract 밖으로 새지 않게 한다.
- `runtime_audit_summary.json`는 단순 heartbeat면 명시적으로 격하하고, operator summary면 structured digest까지 올린다.
- restore path는 partial failure를 silent success로 숨기지 않는다.

acceptance:

- transaction boundary가 `DBManager` 또는 명시 wrapper 하나로 수렴한다.
- `runtime_audit_summary.json`의 역할과 필드가 문서/테스트/코드에서 단일 의미를 가진다.
- tracker rollback 예외가 전체 restore를 비보호 중단시키지 않고 partial restore 상태를 명시 surface한다.

필수 테스트:

- `tests/test_db_manager.py`
- `tests/integration/test_patch_wiring.py`
- audit summary structured digest regression
- tracker rollback exception continuity regression

### GDFS-E3. Config / API / Operator Surface Single-Truth Normalization

대상 finding:

- `GDFS-T3-001`
- `GDFS-T3-003`
- `GDFS-T3-004`
- `GDFS-T4-001`
- `GDFS-T4-002`
- `GDFS-T4-003`
- `GDFS-T5-001`

대상 파일:

- `config/settings/validation.yaml`
- `config/settings.json`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_auditor.py`
- `modules/validation/validation_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `docs/implementation/api-contract-v1.yaml`
- `modules/api/bridge_server.py`
- `modules/core/project_support.py`
- `modules/core/quality_sidecar_bootstrap.py`
- `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
- `전처리_ssot/README.md`
- related contract tests

구현 원칙:

- threshold, required query, websocket surface, resume pointer는 각각 single truth를 하나만 둔다.
- operator-facing detail은 runtime effective truth를 기본값으로 써야 한다.
- contract regression은 path existence만 보지 않고 semantic surface까지 잠근다.

acceptance:

- validation threshold single truth가 코드/설정/테스트에서 일치한다.
- vector fallback default와 tests가 `validation.yaml` 최신 수치와 맞는다.
- `/quality/*`, `/safe-ops/preview` `project` requiredness가 spec/runtime/tests에서 일치한다.
- `/events` websocket surface가 formal contract 또는 동등한 dedicated spec으로 들어온다.
- support/quality operator surface는 `effective_pov` 또는 명시적 raw label을 사용한다.
- preprocess resume guide가 `JSON first, md fallback`로 단일화된다.
- contract regression은 requiredness와 websocket omission을 false green으로 놓치지 않는다.

필수 테스트:

- `tests/test_api_contract.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_project_support.py`
- `tests/test_quality_sidecar_bootstrap.py`
- `tests/test_tf3_threshold_alignment.py`
- preprocess resume contract sync regression

### GDFS-E4. Runtime Proof / Archived Evidence Refresh

대상 finding:

- `GDFS-T5-002`
- `GDFS-T5-003`

대상 파일:

- `scripts/run_stage4_canary.py`
- `modules/core/stage4_canary_tools.py`
- `docs/2026-03-13/stage4-canary-archive-locator-note.md`
- runtime-proof / canary closure docs
- fresh canary project artifacts

구현 원칙:

- canary `pass`는 companion DB/provenance audit 없이는 closure로 승격하지 않는다.
- archived proof note는 현재 workspace 사실과 충돌하면 안 된다.
- old historical proof와 fresh proof를 같은 층으로 섞지 않는다.

acceptance:

- fresh canary 또는 equivalent rerun 1회가 새 project 기준으로 남는다.
- same run에 대해 `stage_attempts` rationale/provenance 컬럼 populated 여부를 companion audit로 캡처한다.
- archive locator note와 closure docs가 actual archived path와 `project_locator`를 함께 보존한다.
- historical archived proof는 `historical`, fresh proof는 `current`로 분리돼 operator가 오판하지 않는다.

필수 테스트 / proof:

- `tests/test_run_stage4_canary.py`
- `tests/test_stage4_canary_tools.py`
- fresh runtime proof checklist
- archived proof index refresh verification

### GDFS-E5. Manual-Only / Legacy / Residue Surface Containment

대상 finding:

- `GDFS-T6-001`
- `GDFS-T6-002`
- `GDFS-T6-003`
- `GDFS-T6-004`

대상 파일:

- `lite_mode/bridge/ui_discovery.py`
- `lite_mode/bridge/gemini_driver.py`
- `lite_mode/manual_ui_discovery_probe.py`
- `geuldobi-desktop/package.json`
- `geuldobi-desktop/src/main.js`
- `geuldobi-desktop/main.js`
- root `main.js`
- `tools/normalize_arcs_db.py`
- `tools/fix_future_items.py`
- `tools2/expand_ep15.py`
- `tools2/style_transfer.py`
- `main_tools/blueprint_editor.py`
- `MagicMock/`
- root `temp-*`

구현 원칙:

- live surface, manual-only surface, stale/shadow surface, residue surface를 이름과 문서 기준으로 분리한다.
- manual-only tool은 범용/공식 실행 경로처럼 보이지 않게 한다.
- residue cleanup은 live classification 이후 별도 hygiene step으로 다룬다.

acceptance:

- Lite Mode raw provider path가 `manual-only`임이 코드/문서/폴더 명명에서 분명하다.
- `geuldobi-desktop/src/main.js`가 active entry이고 shadow mains는 `stale` 또는 `manual debug only`로 분류된다.
- host-bound DB mutation tools는 `legacy/manual-only` 경고 또는 격리 위치를 가진다.
- `MagicMock/`와 root `temp-*`는 live inventory와 분리된 hygiene 대상으로 기록된다.

필수 테스트 / verification:

- `tests/test_desktop_work_guard_template_contract.py`
- live-vs-shadow main classification check
- manual-only tool header / inventory verification

## 7. Recommended Execution Order

1. `GDFS-E1`
- producer-consumer split을 먼저 닫아야 새 artifact와 sink가 다시 오염되지 않는다.

2. `GDFS-E2`
- persistence/restore 경계를 바로 잠가야 E1 이후 생성되는 새 truth가 partial commit/restore gap에 흔들리지 않는다.

3. `GDFS-E3`
- config/API/operator contract와 regression gate를 정렬해야 implementation green과 operator-facing green이 같은 의미가 된다.

4. `GDFS-E4`
- fresh runtime proof는 코드/계약이 닫힌 뒤에만 의미가 있다.

5. `GDFS-E5`
- legacy/manual surface containment은 active path가 확정된 뒤에 수행하는 편이 안전하다.

## 8. Verification Plan

- focused pytest
  - `tests/test_stage01_helpers.py`
  - `tests/test_stage3_orchestrator.py`
  - `tests/test_db_manager.py`
  - `tests/integration/test_patch_wiring.py`
  - `tests/test_api_contract.py`
  - `tests/test_bridge_quality_summary.py`
  - `tests/test_project_support.py`
  - `tests/test_quality_sidecar_bootstrap.py`
  - `tests/test_tf3_threshold_alignment.py`
  - `tests/test_run_stage4_canary.py`
  - `tests/test_stage4_canary_tools.py`
  - `tests/test_desktop_work_guard_template_contract.py`
- runtime proof
  - fresh canary or equivalent rerun 1회
  - companion DB/rationale audit
- static inventory
  - `rg`로 active/shadow/manual-only/residue surface 재분류 검증

## 9. Exit Criteria

1. `GDFS-E1~E5`가 모두 implementation과 verification까지 닫힌다.
2. producer-consumer contract split이 save-hook, stale note, manual interpretation에 기대지 않는다.
3. operator-facing contract와 runtime truth가 같은 의미를 가진다.
4. canary/runtime proof가 current rationale/provenance sink까지 포함해 닫힌다.
5. manual-only / shadow / residue surface가 live path와 혼동되지 않는다.
6. postfix 3PASS에서 unresolved `P1` 0건을 목표로 재분류 가능하다.

## 10. Compaction / Resume Packet

- `Current phase`: `execution SSOT authored`
- `Last completed pass`: `survey 3PASS complete -> SSOT projection complete`
- `Last completed surface`: `retained set -> execution unit mapping`
- `Next surface`: `implementation not started`
- `Reopen reason codes used`: `none`
- `Stop gate or blocker`: `implementation not started`
