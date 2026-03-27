# OPUS Fallen Prince Pair Consumability Order

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `fallen_prince_buys_joseon`

## 1. Order Intent

This order fixes the target to `fallen_prince_buys_joseon` and asks OPUS to advance exactly one revival-ladder unit.

Current lane truth:
- family: `blockguide`
- entry type: existing `TR + BI` pair revival
- current pair location: `_quarantine`
- smallest remaining unproven step: `pair consumability` (ladder Step 1)

This is the first revival-ladder entry for this work. No prior revival artifacts exist.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not regenerate TR
- do not redesign BI from scratch
- do not promote to active path in the same run
- do not run Stage 2/3/4 in the same run
- if consumability fails, patch only the smallest contract blockers — do not start narrative repair

## 3. Canonical Target

- work_id: `fallen_prince_buys_joseon`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`

Treat these quarantine files as the authoritative pair for this order.

## 4. Proven Prior Steps

None. This is the first revival-ladder entry for this work.

Preprocess gate (Stage 0) is already evidenced:
- `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`
- `treatments/preprocess/fallen_prince_buys_joseon/profile_lock.json`
- `treatments/preprocess/fallen_prince_buys_joseon/material_bundle_summary.json`
- `treatments/preprocess/fallen_prince_buys_joseon/phase0_ready_snapshot.json`
- `manual_audit_pass == true`

Known risks from preprocess snapshot:
- skeleton risk — quarantine BI/TR의 블록 단위 서사가 기계적 반복 패턴일 가능성 높음
- 비어 있는 재료 — 블록별 이벤트 정밀 배치, NPC 등장/전환 스케줄, 유럽 도시별 금융 진입 구체 루트, 가명법인 설립 실무
- DB 재료 소비 필요 — 병목 5축 실물 메커니즘은 material_bank.db의 AH-* 소스 6개에서 블록별로 바인딩해야 함

These risks inform the consumability survey but do not block it.

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `treatments/preprocess/fallen_prince_buys_joseon/phase0_ready_snapshot.json`
5. `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`

## 6. Immediate Goal

Execute exactly one bounded `pair consumability survey` (ladder Step 1) for `fallen_prince_buys_joseon`.

The survey must answer:
- does the quarantine pair admit into the current harness?
- is the BI standalone roadmap ready?
- are there embedded roadmap warnings?
- are runtime protagonist keys present?
- are required contract fields populated?

## 7. Survey Method

### 7.1 Pair Admission

Verify, at minimum:
- both TR and BI parse as valid UTF-8 JSON
- TR contains block entries (expected: 70)
- BI contains MasterBible / top-level keys
- pair identity is unambiguous (both files point to the same `work_id`)

### 7.2 BI Standalone Roadmap Readiness

Check:
- `plot_roadmap` or equivalent block-level roadmap exists
- block count matches TR
- title sync between BI roadmap and TR blocks (spot-check first 10 blocks)

### 7.3 Runtime Protagonist Keys

Check protagonist-facing runtime keys:
- `protagonist_config.name`
- `protagonist_config.world_origin`
- `protagonist_config.incarnation_type`
- `protagonist_config.pov`
- any regression mechanic fields if applicable

Report missing keys explicitly — these are promotion blockers.

### 7.4 Embedded Roadmap Warnings

Check for:
- empty or placeholder blocks
- blocks with missing required fields (context, conflict, solution, result)
- suspicious repetition patterns (skeleton risk from preprocess snapshot)
- blocks where context/solution are near-identical copies of adjacent blocks

### 7.5 Contract Field Coverage

For a sample window (Block 1-10), check:
- all required block fields are present and non-empty
- content sub-fields (context, conflict, solution, result) exist
- genre-specific fields if any (genre_ext, regression_ext, etc.)

### 7.6 Schema Drift Check

Verify no unexpected schema divergence:
- BI top-level key set is within expected range
- no corrupted or malformed nested structures
- JSON values are all valid types (no raw strings where objects expected)

## 8. Consumability Repair Decision

After survey:
- if pair consumability passes cleanly: report pass, recommend next step (TR static audit)
- if pair consumability fails on trivial contract issues: list the specific blockers, recommend `consumability repair` as next unit
- if pair consumability fails because BI is a thin echo or placeholder: report this explicitly, note it as a structural issue for BI repair (Step 3)
- if TR is unparseable or fundamentally broken: report fail, recommend `TR regeneration` before restarting ladder

Do NOT perform repair in this run. This is survey only.

## 9. Skeleton Risk Assessment

The preprocess snapshot flags skeleton risk. During the consumability survey, explicitly evaluate:
- do block-level descriptions show variation in vocabulary, location, conflict type?
- or do they read as template-filled repetitions of the same pattern?
- give a preliminary skeleton risk rating: `low`, `medium`, `high`

This informs the TR static audit (Step 2) but does not block consumability.

## 10. Deliverable

Save exactly one main report:

- `docs/2026-03-27/fallen-prince-pair-consumability-survey.md`

The report should include:
- target pair paths
- pair admission result
- BI roadmap readiness result
- protagonist key check result
- embedded roadmap warnings
- contract field coverage (Block 1-10 sample)
- schema drift check
- skeleton risk preliminary assessment
- overall consumability verdict: `pass`, `pass with warnings`, or `fail`
- specific blocker list (if any)
- next unit recommendation

## 11. Stop Conditions

Stop immediately and report if any of the following occurs:

- pair files are missing or corrupted
- pair identity is ambiguous (TR and BI point to different works)
- JSON parsing fails on either file
- confidence falls below 95% and no smaller bounded next step exists

## 12. Expected Next Unit After This Order

- if consumability passes cleanly: `TR static audit` (ladder Step 2)
- if consumability fails on trivial contract issues: `consumability repair`
- if TR is broken: `TR regeneration`, then restart ladder

## 13. Handoff Format

End with this exact flat report:

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: pair consumability survey
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- no same-work parallel editing is authorized
- this is survey-only, no repair in the same run

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `pair consumability survey`
- preprocess gate truth and known risks are enumerated
- deliverable and stop conditions are explicit
- skeleton risk assessment is included given preprocess warning

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded revival step

Confidence:
- 97% that `pair consumability survey` is the correct first OPUS unit for this pair
