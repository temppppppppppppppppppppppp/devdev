# MD / JSON 계약 인벤토리

> purpose: 어떤 규칙을 `md`에 남기고 어떤 규칙을 `json`으로 내릴지 고정

## 0. 기본 원칙

- 이유, 예시, 금지 패턴, 운영 철학은 `md`
- 상태, 필수 슬롯, 판정 규칙, stop/go 게이트는 `json`
- 같은 규칙은 한 군데만 canonical로 둔다

## 1. MD에 남기는 것

| 문서 | 유지 형식 | 이유 |
| --- | --- | --- |
| `전처리_ssot/README.md` | `md` | 사용자용 단일 진입점 |
| `docs/SSOT_stage0_preprocess_integrated_order.md` | `md` | 읽기 순서, 운영 철학, stage 해석 설명 |
| `docs/stage0_source_manifest_harness.md` | `md` | 좋은/나쁜 예시, anti-pattern, 작성 지침 |
| `docs/stage0_profile_lock_harness.md` | `md` | 프로파일 선택 설명, 실패 사례 |
| `docs/stage0_material_collection_harness.md` | `md` | 자료 수집 우선순위, source quality 설명 |
| `docs/blockguide/*.md` | `md` | Planning / Production / BI 설명층 |
| `migration_notes/*.md` | `md` | 개편 이유, cutover, rollback, 감리 |
| 작품별 `README.md`, `progress_log.md`, `decisions.md` | `md` | 사람용 경과 기록 |

## 2. 이미 JSON인 것

| 파일 | 유지/승격 | 이유 |
| --- | --- | --- |
| `source_manifest.json` | 유지 | Stage 0 핵심 계약 |
| `profile_lock.json` | 유지 | 프로파일 잠금은 상태형 계약 |
| `material_bundle_summary.json` | 유지 | 재료 묶음은 구조화된 상태가 유리 |
| `phase0_ready_snapshot.json` | 유지 | Planning 진입 게이트 |
| `phase0_design.json` | 유지 | Planning 산출물 |
| `tr_block_070_draft.json` | 유지 | Production 산출물 |
| `0_bi_{work_id}.json` | 유지 | BI 산출물 |

## 3. JSON으로 내려야 하는 것

| target file | 현재 상태 | 전환 이유 |
| --- | --- | --- |
| `stage_machine.json` | prose | 단계 판정은 기계 계약이어야 함 |
| `artifact_contracts.json` | prose | 필수 산출물 경로와 필수 슬롯을 기계 검증 가능하게 해야 함 |
| `quality_gates.json` | prose | stop/go 규칙을 diff/validation 가능하게 해야 함 |
| `profile_catalog.json` | prose + scattered | 장르 프로파일과 해석축을 한 파일에서 잠가야 함 |
| `handoff_rules.json` | prose | Stage 0 -> Planning -> Production -> BI handoff를 기계적으로 읽어야 함 |
| `sequential_run_status.json` | currently md | 진행률과 재개 포인터는 prose보다 상태 파일이 적합함 |
| `audit_status.json` | 없음 | pass/fail, blockers, confidence를 구조화해야 함 |

## 4. 당장 유지하는 MD 상태 파일

이번 단계에서는 아래 파일을 바로 삭제하지 않는다.

| 현재 파일 | 이유 | 향후 처리 |
| --- | --- | --- |
| `docs/sequential_run_status.md` | 이미 운영 중이고 사람이 읽기 쉬움 | JSON 계약층이 생기면 `sequential_run_status.json`과 병행 후 축소 |
| `phase0_check.md` | 설명형 점검 메모 | `audit_status.json` 생긴 뒤 보조 설명 문서로 격하 |
| `tr_gate_report.md` | 설명형 감리 | 기계 판정은 JSON, 설명은 MD로 이원화 |
| `bi_5pass.md` | 설명형 감리 | pass flags는 JSON, reasoning은 MD |

## 5. ownership 규칙

| 규칙 유형 | canonical layer |
| --- | --- |
| 이유 / 맥락 / 예시 / anti-pattern | `md` |
| 단계 판정 | `json` |
| 필수 파일 존재 여부 | `json` |
| 필수 슬롯 검증 | `json` |
| 수동 감리 해설 | `md` |
| 수동 감리 pass flag | `json` |
| 재개 포인터 | `json` |
| 비교/교훈/배경 | `md` |

## 6. 이 인벤토리가 필요한 이유

이 표가 없으면 바로 아래 문제가 다시 생긴다.

- prose와 상태 파일이 서로 다른 말을 한다
- README와 harness, 상태 파일이 중복 진실이 된다
- 낮은 성능 모델이 `무엇이 설명이고 무엇이 계약인지` 구분 못 한다
- 이후 cutover 때 어떤 문서를 고쳐야 하는지 범위가 폭발한다

따라서 이 인벤토리는 선택 문서가 아니라 cutover의 기준 문서다.
