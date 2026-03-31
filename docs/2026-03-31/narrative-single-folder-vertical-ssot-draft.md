# Narrative Single-Folder Vertical SSOT Draft

Status: draft only
Date: 2026-03-31
Scope: `docs/실물기반 사각지대 테스트` + `전처리_ssot` + `treatments/` + `bible/`를 하나의 상위 SSOT 체계로 재정렬하는 개편안 초안

## 1. Intent

이 초안의 목표는 폴더를 단순 병합하는 것이 아니다.

- `재료 창고`
- `전처리 계약`
- `기획안`
- `TR`
- `BI`
- `감리 / 출고`

를 하나의 상위 폴더 안에서 수직 계층으로 연결해, 작품별 생산 체인을 한눈에 따라갈 수 있게 만드는 것이다.

핵심 방향은 아래 4개다.

1. shared reference와 project-specific production을 같은 상위 폴더 아래에 둔다.
2. `few-shot -> source_manifest -> phase0 -> TR -> BI`를 schema와 handoff로 잠근다.
3. 새 작품은 `project vertical stack` 안에서 시작하고 끝나게 만든다.
4. 기존 `treatments/`, `bible/` 경로는 cutover 전까지 compatibility export로 유지한다.

## 2. Recommended Top Folder

추천 상위 폴더명:

- `narrative_ssot/`

이 폴더가 새 서사 생산 SSOT의 진입점이 된다.

```text
narrative_ssot/
├── README.md
├── 00_governance/
├── 10_reference_bank/
├── 20_shared_materials/
├── 30_harness/
├── 40_contracts/
├── 50_projects/
├── 60_ops/
├── 70_archive/
├── 80_tools/
└── 90_migration/
```

역할 요약:

- `00_governance/`: 엔트리 SSOT, stage machine, path policy, naming policy
- `10_reference_bank/`: few-shot bank, cards, manifest, genre packs, reusable analysis
- `20_shared_materials/`: 장면은행, 장르노트, 용어집, golden samples
- `30_harness/`: 사람용 실행 문서와 단계별 하네스
- `40_contracts/`: JSON schema, quality gates, handoff rules, state machine
- `50_projects/`: 작품별 수직 생산기지
- `60_ops/`: intake queue, audit queue, release queue, migration status
- `70_archive/`: superseded docs, legacy mirrors, frozen evidence
- `80_tools/`: builders, validators, publishers
- `90_migration/`: legacy path mapping, cutover notes, compat rules

## 3. Top-Level Folder Tree

```text
narrative_ssot/
├── README.md
├── 00_governance/
│   ├── SSOT_narrative_factory_entry.md
│   ├── narrative_stage_machine.json
│   ├── canonical_path_policy.md
│   ├── naming_contract.md
│   └── authority_map.md
├── 10_reference_bank/
│   ├── README.md
│   ├── reference_card_manifest.json
│   ├── cards/
│   ├── genre_packs/
│   ├── pattern_packs/
│   ├── analysis/
│   └── source_registry/
├── 20_shared_materials/
│   ├── genre_notes/
│   ├── scene_bank/
│   ├── terminology/
│   ├── style_profiles/
│   └── golden_samples/
├── 30_harness/
│   ├── 00_entry_router.md
│   ├── 10_reference_intake_harness.md
│   ├── 11_reference_card_harness.md
│   ├── 12_reference_selection_harness.md
│   ├── 20_stage0_preprocess_harness.md
│   ├── 30_phase0_planning_harness.md
│   ├── 40_tr_production_harness.md
│   ├── 50_bi_build_harness.md
│   ├── 60_audit_release_harness.md
│   └── 70_compat_cutover_harness.md
├── 40_contracts/
│   ├── README.md
│   ├── stage_machine.json
│   ├── quality_gates.json
│   ├── handoff_rules.json
│   ├── artifact_contracts.json
│   ├── shared/
│   ├── reference/
│   ├── preprocess/
│   ├── planning/
│   ├── production/
│   ├── bi/
│   └── release/
├── 50_projects/
│   └── {work_id}/
├── 60_ops/
│   ├── intake_queue/
│   ├── audit_queue/
│   ├── release_queue/
│   ├── work_registry.json
│   └── queue_indexes/
├── 70_archive/
│   ├── legacy_docs/
│   ├── superseded_contracts/
│   └── frozen_project_refs/
├── 80_tools/
│   ├── build_bi_from_verified_tr.py
│   ├── validate_narrative_artifact.py
│   ├── publish_legacy_outputs.py
│   └── sync_reference_manifest.py
└── 90_migration/
    ├── legacy_path_map.json
    ├── cutover_plan.md
    └── compat_matrix.md
```

## 4. Project Vertical Stack

이 개편안의 핵심은 `50_projects/{work_id}/`다.

작품 하나는 아래처럼 수직으로 쌓는다.

```text
narrative_ssot/50_projects/{work_id}/
├── README.md
├── 00_intake/
│   ├── project_brief.md
│   ├── user_notes.md
│   └── intake_meta.json
├── 10_reference_selection/
│   ├── reference_selection.json
│   ├── contamination_guard.json
│   └── selection_audit.md
├── 20_preprocess/
│   ├── source_manifest.json
│   ├── profile_lock.json
│   ├── material_bundle_summary.json
│   ├── phase0_ready_snapshot.json
│   ├── preprocess_audit_status.json
│   └── evidence/
├── 30_planning/
│   ├── phase0_design.json
│   ├── phase0_audit_status.json
│   └── planning_notes.md
├── 40_production/
│   ├── tr_block_070_draft.json
│   ├── tr_batches/
│   ├── sequential_run_status.json
│   ├── tr_audit_status.json
│   └── repair_notes.md
├── 50_bi/
│   ├── 0_bi_{work_id}.json
│   ├── bi_audit_status.json
│   └── builder_inputs.json
├── 60_audit/
│   ├── cross_stage_audit.md
│   ├── release_gate.json
│   └── final_findings.md
├── 70_publish/
│   ├── legacy_exports/
│   │   ├── treatments/
│   │   └── bible/
│   ├── publish_status.json
│   └── export_hashes.json
└── 80_history/
    ├── superseded/
    └── snapshots/
```

의미:

- shared 자산은 상위 `reference_bank`, `shared_materials`에 남긴다.
- 작품 고유 산출물은 반드시 `50_projects/{work_id}/` 안에서만 생성한다.
- 기존 루트 `treatments/`, `bible/`는 publish 결과물로 취급한다.

## 5. Harness Layering

엔트리 읽기 순서는 아래처럼 단순화한다.

1. `00_governance/SSOT_narrative_factory_entry.md`
2. `30_harness/00_entry_router.md`
3. 현재 stage 판정
4. 해당 stage 하네스
5. 해당 stage schema + quality gates

추천 하네스 체계:

### 5.1 Entry Layer

- `SSOT_narrative_factory_entry.md`
  - 전체 read order
  - authoritative path
  - stage detection precedence
  - cutover mode

- `00_entry_router.md`
  - request가 reference intake인지
  - preprocess인지
  - phase0인지
  - TR인지
  - BI인지
  - audit / repair인지 판정

### 5.2 Reference Layer

- `10_reference_intake_harness.md`
  - raw source intake
  - source scope 확인
  - save preflight

- `11_reference_card_harness.md`
  - `Master Reference Card v1`
  - `Slim Reference Card v1`
  - `must_not_copy`
  - `contamination_risk`

- `12_reference_selection_harness.md`
  - 작품별 card shortlist
  - `reference_selection.json` 작성 규칙
  - selection audit 기준

### 5.3 Production Layer

- `20_stage0_preprocess_harness.md`
  - `reference_selection` 기반 `source_manifest`
  - `profile_lock`
  - `material_bundle_summary`
  - `phase0_ready_snapshot`

- `30_phase0_planning_harness.md`
  - `phase0_design.json`
  - opening arc / spike / payoff design

- `40_tr_production_harness.md`
  - `TR` 1-block sequential production
  - 5-block cap
  - 10-block self-audit gate
  - repair / resume rules

- `50_bi_build_harness.md`
  - `phase0 + verified TR -> BI`
  - deterministic build
  - BI schema + sync audit

- `60_audit_release_harness.md`
  - cross-stage consistency audit
  - release gate
  - publish rules

### 5.4 Compatibility Layer

- `70_compat_cutover_harness.md`
  - legacy `treatments/`, `bible/` export rules
  - old path readers와의 공존 규칙
  - cutover 단계별 우선순위

## 6. Contract and Schema Layout

`40_contracts/`는 읽는 사람보다 도구가 먼저 소비하는 층이다.

```text
40_contracts/
├── stage_machine.json
├── quality_gates.json
├── handoff_rules.json
├── artifact_contracts.json
├── shared/
│   ├── work_identity.schema.json
│   ├── path_aliases.json
│   └── naming_rules.json
├── reference/
│   ├── reference_card_manifest.schema.json
│   ├── master_reference_card.schema.json
│   ├── slim_reference_card.schema.json
│   ├── reference_selection.schema.json
│   └── contamination_guard.schema.json
├── preprocess/
│   ├── source_manifest.schema.json
│   ├── profile_lock.schema.json
│   ├── material_bundle_summary.schema.json
│   ├── phase0_ready_snapshot.schema.json
│   └── preprocess_audit_status.schema.json
├── planning/
│   ├── phase0_design.schema.json
│   └── phase0_audit_status.schema.json
├── production/
│   ├── tr_block.schema.json
│   ├── tr_block_070_draft.schema.json
│   ├── sequential_run_status.schema.json
│   └── tr_audit_status.schema.json
├── bi/
│   ├── bi_output.schema.json
│   ├── bi_builder_inputs.schema.json
│   └── bi_audit_status.schema.json
└── release/
    ├── release_gate.schema.json
    ├── publish_status.schema.json
    └── cross_stage_audit.schema.json
```

## 7. Contract Relationship

핵심 계약은 아래 순서로 이어진다.

1. `reference_card_manifest.json`
   - shared reference inventory의 SSOT
   - 카드 저장 상태와 audit 상태를 잠근다

2. `reference_selection.json`
   - 특정 작품이 어떤 카드들을 실제로 썼는지 잠근다
   - 이 단계가 빠지면 few-shot 적용 증거가 남지 않는다

3. `source_manifest.json`
   - `reference_selection`에서 통과한 slim card만 입력으로 받는다
   - raw source path 직접 참조를 최소화한다

4. `phase0_design.json`
   - `phase0_ready_snapshot.manual_audit_pass == true`를 선행조건으로 둔다

5. `tr_block_070_draft.json`
   - `phase0_design`만을 narrative design source로 사용한다
   - 진행 상태는 `sequential_run_status.json`이 authoritative하다

6. `0_bi_{work_id}.json`
   - `phase0 + verified TR`만 받아 생성한다
   - builder input hash를 기록한다

7. `release_gate.json`
   - preprocess / phase0 / TR / BI / cross-stage audit를 모두 통과했는지 잠근다

## 8. Recommended Authoritative Precedence

개편 후 권위 순서는 아래를 권장한다.

1. status JSON
2. stage gate JSON
3. canonical artifact JSON
4. audit markdown
5. legacy export path

즉, stage 판정은 단순 파일 존재보다 아래처럼 가는 편이 낫다.

- 먼저 `preprocess_audit_status`, `sequential_run_status`, `bi_audit_status`, `release_gate`
- 그다음 canonical artifact 존재
- 마지막에 legacy path existence

이건 현행 `file existence first`와 다르므로, router cutover 시 명시적 변경이 필요하다.

## 9. Reference-to-Output Traceability

이번 개편안에서 가장 중요한 보강점은 `traceability`다.

필수 링크는 아래처럼 건다.

- `reference_card_manifest.entries[*].slug`
  -> `reference_selection.selected_cards[*].card_slug`
- `reference_selection.selected_cards[*].handoff_label`
  -> `source_manifest.reference_only_sources[*].label`
- `source_manifest.work_identity`
  -> `phase0_design.work_id`
- `phase0_design.hash`
  -> `tr_block_070_draft.build_meta.phase0_hash`
- `verified TR hash`
  -> `0_bi_{work_id}.json._build_meta.tr_hash`
- `phase0 + TR + BI hashes`
  -> `release_gate.json.inputs`

이렇게 해야 "few-shot이 실제 적용됐나", "BI가 어느 TR을 실었나" 같은 질문에 증거형으로 답할 수 있다.

## 10. Quality Gates

stage별 최소 게이트 초안:

### 10.1 Reference

- card saved
- card audit PASS
- slim handoff label 존재
- contamination guard PASS

### 10.2 Preprocess

- `source_manifest` schema PASS
- `profile_lock` schema PASS
- `material_bundle_summary` schema PASS
- `phase0_ready_snapshot.manual_audit_pass == true`

### 10.3 Planning

- `phase0_design` schema PASS
- opening arc / representative spike / payoff axis 존재
- phase0 audit PASS

### 10.4 Production

- `TR` item schema PASS
- sequential status coherent
- 1-block sequential rule 준수
- 5-block cap 준수
- 10-block self-audit gate 준수

### 10.5 BI

- `BI` schema PASS
- `phase0` title / protagonist sync PASS
- `TR -> BI roadmap sync` PASS
- builder input hash recorded

### 10.6 Release

- cross-stage audit PASS
- release gate PASS
- publish status PASS

## 11. Legacy Compatibility Rule

처음부터 기존 경로를 끊지 않는 것이 안전하다.

권장 cutover:

### Phase A. Mirror Introduction

- 새 canonical path는 `narrative_ssot/50_projects/{work_id}/...`
- 기존 `treatments/`, `bible/`는 export target으로만 유지
- router와 builder는 아직 legacy read도 허용

### Phase B. Canonical Read Switch

- router는 새 canonical path를 먼저 읽음
- legacy path는 publish 결과 검증용으로만 사용
- conflict 발생 시 canonical이 승리

### Phase C. Legacy Optional

- 기존 스크립트가 모두 새 경로를 이해하면 legacy export를 optional로 낮춤

## 12. Migration Recommendation

한 번에 갈아엎지 말고 아래 순서를 권장한다.

1. `narrative_ssot/` 상위 폴더 신설
2. `10_reference_bank/`에 현재 few-shot-bank를 mirror or move
3. `40_contracts/reference/`에 reference schema 추가
4. `50_projects/_template/` 생성
5. 신규 작품부터 `project vertical stack` 사용
6. `publish_legacy_outputs.py`로 기존 `treatments/`, `bible/` export
7. 안정화 후 기존 `전처리_ssot/`와 분산 docs를 archive 처리

## 13. Non-Goals

이 초안이 지금 당장 의미하지 않는 것은 아래다.

- 기존 작품 전체를 즉시 재배치
- 기존 `treatments/`, `bible/` 제거
- few-shot 카드 포맷을 전부 JSON으로 강제 변환
- blockguide / wuxguide family 체계를 폐기

## 14. Open Decisions

아직 결정이 필요한 지점:

1. 상위 폴더명을 `narrative_ssot/`로 갈지 다른 이름을 쓸지
2. few-shot 카드는 `md only`로 유지할지 `md + normalized json` 쌍으로 갈지
3. stage 판정을 `status-first`로 바꿀지, 한동안 `status + existence dual mode`로 둘지
4. `phase0_design`, `TR`, `BI`의 canonical 경로를 새 폴더로 완전히 옮길지, 당분간 legacy path를 정본으로 남길지
5. audit 결과를 `md + json` 이중 체계로 둘지, status JSON 중심으로 내릴지

## 15. Recommendation Summary

가장 무난한 초안은 이렇다.

- 상위 폴더는 `narrative_ssot/`
- shared layer와 project vertical layer를 한 폴더 안에 공존
- 작품별 산출물은 `50_projects/{work_id}/`에 모음
- 기존 `treatments/`, `bible/`는 publish export로 유지
- few-shot 적용 증거를 위해 `reference_selection.json` 신설
- `phase0/TR/BI` 전부 stage별 schema를 추가
- cutover는 `mirror -> canonical read switch -> legacy optional` 3단계로 진행

이 안이면 "한 폴더로 모으자"는 요구와 "기존 생산체계를 한 번에 깨지 말자"는 안정성 요구를 둘 다 잡을 수 있다.
