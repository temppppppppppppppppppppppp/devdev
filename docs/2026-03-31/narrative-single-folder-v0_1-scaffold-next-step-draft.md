# Narrative Single-Folder V0.1 Scaffold Next Step Draft

Status: draft only
Date: 2026-03-31
Purpose: `narrative_ssot/` 개편안을 실제 착수 가능한 최소 단위로 내리는 `next step` 초안

## 1. Recommended Immediate Step

바로 할 다음 스텝은 `전면 이관`이 아니라 아래 3개다.

1. `narrative_ssot/` 빈 골격을 만든다.
2. 최소 schema 6종과 엔트리 하네스 2종만 먼저 잠근다.
3. 기존 경로는 유지한 채, 신규 작품부터만 `vertical stack`을 시험 적용한다.

즉, `move`보다 `scaffold + contract pin + pilot`가 먼저다.

## 2. V0.1 Scope

V0.1에서 하는 것:

- 상위 폴더 `narrative_ssot/` 신설
- shared reference layer와 project layer의 자리만 먼저 만든다
- `reference_selection` 계약을 새로 도입한다
- `source_manifest -> phase0 -> TR -> BI`의 최소 schema 뼈대를 만든다
- 신규 작품 1개에만 pilot 적용한다
- 기존 `treatments/`, `bible/`는 계속 유지한다

V0.1에서 하지 않는 것:

- 기존 few-shot-bank 즉시 이동
- 기존 `전처리_ssot/` 즉시 삭제
- 기존 작품 전체 재배치
- router 전면 교체
- BI builder 전면 개조

## 3. Recommended Folder Creation Set

V0.1에서 실제로 먼저 만들어도 되는 폴더는 이 정도다.

```text
narrative_ssot/
├── README.md
├── 00_governance/
│   ├── SSOT_narrative_factory_entry.md
│   └── authority_map.md
├── 10_reference_bank/
│   ├── README.md
│   ├── reference_card_manifest.mirror.md
│   └── selection/
├── 30_harness/
│   ├── 00_entry_router.md
│   ├── 12_reference_selection_harness.md
│   ├── 20_stage0_preprocess_harness.md
│   ├── 30_phase0_planning_harness.md
│   ├── 40_tr_production_harness.md
│   ├── 50_bi_build_harness.md
│   └── 70_compat_cutover_harness.md
├── 40_contracts/
│   ├── README.md
│   ├── artifact_contracts.json
│   ├── handoff_rules.json
│   ├── quality_gates.json
│   ├── reference/
│   ├── preprocess/
│   ├── planning/
│   ├── production/
│   ├── bi/
│   └── release/
├── 50_projects/
│   ├── _template/
│   └── _pilot/
└── 90_migration/
    ├── cutover_plan.md
    └── legacy_path_map.json
```

포인트:

- `20_shared_materials/`, `60_ops/`, `70_archive/`, `80_tools/`는 V0.1에 꼭 없어도 된다
- 처음부터 다 만들지 말고, 필요한 축만 연다

## 4. Minimal Canonical Files To Author First

가장 먼저 써야 하는 파일은 아래 8개다.

1. `narrative_ssot/README.md`
2. `narrative_ssot/00_governance/SSOT_narrative_factory_entry.md`
3. `narrative_ssot/30_harness/00_entry_router.md`
4. `narrative_ssot/30_harness/12_reference_selection_harness.md`
5. `narrative_ssot/40_contracts/reference/reference_selection.schema.json`
6. `narrative_ssot/40_contracts/preprocess/source_manifest.schema.json`
7. `narrative_ssot/40_contracts/planning/phase0_design.schema.json`
8. `narrative_ssot/40_contracts/production/tr_block_070_draft.schema.json`

그다음 2차로:

1. `narrative_ssot/40_contracts/bi/bi_output.schema.json`
2. `narrative_ssot/40_contracts/release/release_gate.schema.json`
3. `narrative_ssot/40_contracts/production/sequential_run_status.schema.json`
4. `narrative_ssot/50_projects/_template/...`

## 5. Minimum Schema Pack

V0.1 최소 schema pack은 아래 6개를 권장한다.

### 5.1 `reference_selection.schema.json`

잠글 것:

- `work_id`
- `selection_date`
- `selected_cards[]`
- `card_slug`
- `track`
- `handoff_label`
- `selection_reason`
- `must_not_copy_applied`
- `contamination_risk_reviewed`

### 5.2 `source_manifest.schema.json`

잠글 것:

- `work_identity`
- `canonical_sources`
- `reference_only_sources`
- `core_materials`
- `npc_pool`
- `crisis_pool`
- `hard_constraints`
- `do_not_fake`
- `manual_audit_note`

### 5.3 `phase0_design.schema.json`

잠글 것:

- `work_id`
- `title`
- `protagonist`
- `core_fantasy`
- `opening_arc`
- `representative_spike`
- `growth_axis`
- `opponent_transition_plan`
- `payoff_axis`

### 5.4 `tr_block_070_draft.schema.json`

잠글 것:

- top-level array
- `block_id`
- `title`
- `content`
- `stakes`
- `opponent`
- `payoff`
- `hook_strength`

### 5.5 `bi_output.schema.json`

잠글 것:

- `_schema_version`
- `MasterBible.ProjectData`
- `MasterBible.CoreIdentity`
- `MasterBible.plot_roadmap`
- `MasterBible.FinanceHUD`
- `_build_meta.phase0_hash`
- `_build_meta.tr_hash`

### 5.6 `release_gate.schema.json`

잠글 것:

- `work_id`
- `phase0_pass`
- `tr_pass`
- `bi_pass`
- `cross_stage_sync_pass`
- `publish_allowed`
- `blocking_reasons`

## 6. Harness Read Order For V0.1

V0.1 read order는 과하게 길면 안 된다.

```text
1. narrative_ssot/00_governance/SSOT_narrative_factory_entry.md
2. narrative_ssot/30_harness/00_entry_router.md
3. stage별 하네스 1개
4. 해당 stage schema
5. quality_gates.json
```

V0.1에서 꼭 필요한 stage 하네스는 아래만 유지해도 된다.

- reference selection
- preprocess
- phase0
- TR
- BI
- compat cutover

## 7. Recommended Project Template

`50_projects/_template/`는 처음부터 크게 만들 필요 없다.

```text
50_projects/_template/
├── 00_intake/
│   └── intake_meta.json
├── 10_reference_selection/
│   ├── reference_selection.json
│   └── contamination_guard.json
├── 20_preprocess/
│   ├── source_manifest.json
│   ├── profile_lock.json
│   ├── material_bundle_summary.json
│   └── phase0_ready_snapshot.json
├── 30_planning/
│   └── phase0_design.json
├── 40_production/
│   ├── tr_block_070_draft.json
│   └── sequential_run_status.json
├── 50_bi/
│   └── 0_bi_template.json
└── 60_audit/
    └── release_gate.json
```

## 8. Compatibility Rule For V0.1

V0.1에서는 `legacy path`를 끊지 않는다.

원칙:

- canonical write는 아직 보류
- pilot에서는 `narrative_ssot/50_projects/{work_id}/...`에 먼저 쓴다
- publish 시에만 `treatments/`, `bible/`로 export한다
- 기존 reader가 legacy path만 읽어도 깨지지 않게 한다

즉, V0.1은 `dual-path safe mode`다.

## 9. Pilot Recommendation

pilot는 기존 진행 중 작품보다 `신규 작품`이 낫다.

권장:

- `office_checkup_next_day` 같은 진행 중 작품에 바로 적용하지 않는다
- 새 `work_id` 1개를 골라 V0.1 vertical stack으로 시작한다
- `few-shot selection -> preprocess -> phase0`까지만 먼저 돌린다
- TR과 BI는 pilot 2차로 넘긴다

이유:

- 진행 중 작품은 status 불일치, legacy drift, repair history가 많아 cutover 변수까지 섞인다
- 신규 작품은 폴더 구조 검증에 더 적합하다

## 10. First Acceptance Criteria

V0.1이 성공으로 볼 수 있는 기준:

1. 신규 작품 1개가 `reference_selection.json`을 가진다
2. 그 작품의 `source_manifest`가 selected slim card를 traceable하게 참조한다
3. `phase0_design`이 schema PASS 한다
4. legacy export 없이도 내부 경로만으로 stage 추적이 가능하다
5. cutover 문서가 `무엇이 아직 legacy인지`를 명확히 적는다

## 11. Suggested Execution Order

실행 순서 초안:

1. `narrative_ssot/` scaffold 생성
2. `SSOT_narrative_factory_entry.md` 작성
3. `00_entry_router.md` 작성
4. `reference_selection.schema.json` 작성
5. `source_manifest.schema.json` 작성
6. `_template/` 생성
7. 신규 작품 1개에 pilot 적용
8. pilot 결과 보고 후 `phase0/TR/BI` schema 확장

## 12. Recommended Next Real Work Item

가장 무난한 다음 실작업은 이거다.

- `narrative_ssot/` 폴더 생성
- `README.md`
- `SSOT_narrative_factory_entry.md`
- `00_entry_router.md`
- `reference_selection.schema.json`

여기까지가 `V0.1 Day 1` 범위다.

이후 `Day 2`에:

- `source_manifest.schema.json`
- `_template/`
- 신규 `work_id` pilot

## 13. Recommendation Summary

다음 스텝은 `이관`이 아니라 `골격 생성`이다.

- 먼저 상위 폴더만 세운다
- `reference_selection`을 새 계약으로 넣는다
- schema 6종 중 4종만 먼저 시작한다
- 신규 작품에서만 pilot 한다
- 기존 작품과 legacy 경로는 당분간 건드리지 않는다

이 순서가 제일 리스크가 낮고, 개편안이 실제 체계로 내려오는 첫 발판이 된다.
