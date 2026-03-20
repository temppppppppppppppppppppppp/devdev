# Narrative Router Integrated Order

Date: 2026-03-20
Status: active
Scope: narrative-pipeline routing only

## 1. Purpose

- Keep existing family harnesses intact.
- Route each narrative order to the correct family before any family-specific harness is opened.
- Separate shared process rules from genre-family semantic contracts.

This router does not replace family harnesses. It only decides which family becomes SSOT for the current work.

## 2. Family Registry

### 2.1 `blockguide`

- Primary scope: 현대판타지 business-power family
- Typical genres: 현판, 헌터, 투자/기업 성장, 직장 권력전, 테크 스타트업, 엔터/미디어, 의료, 스포츠, 대체역사
- Canonical docs:
  - `docs/blockguide/SSOT_blockguide-integrated-order.md`
  - `docs/blockguide/treatment-planning-harness.md`
  - `docs/blockguide/treatment-production-harness-v2.md`
  - `docs/blockguide/bi-production-harness-v1.md`

### 2.2 `wuxguide`

- Primary scope: 무협/선협 family
- Typical genres: 무협, 선협, 강호 성장물, 문파/세가 권력전, 경지 상승물
- Canonical docs:
  - `docs/wuxguide/SSOT_wuxguide-integrated-order.md`
  - `docs/wuxguide/wuxia-planning-harness.md`
  - `docs/wuxguide/wuxia-production-harness.md`
  - `docs/wuxguide/wuxia-bi-production-harness.md`

## 3. Routing Order

When a request is narrative-pipeline work, use this sequence.

1. Read this file first.
2. Resolve family.
3. Open the resolved family integrated order.
4. Open the resolved family planning / production / BI harnesses.
5. Continue only inside that family unless the user explicitly re-routes.

## 4. Family Resolution Rules

### 4.1 Precedence

1. Explicit family hint from the user
2. Explicit genre label
3. Existing work registry or already-generated artifacts
4. Safe default

### 4.2 Safe Defaults

- Default to `blockguide` when the work is clearly modern-fantasy business-power family.
- Default to `wuxguide` when the work is clearly martial-arts / sect / realm / jianghu family.
- If still ambiguous, stop at family classification and clarify before family-specific generation.

### 4.3 Practical Genre Signals

Route to `blockguide` when the core conflict is dominated by one or more of:

- company / market / guild / operator control
- cashflow / leverage / KPI / contracts / distribution
- hunter urban-fantasy power structures

Route to `wuxguide` when the core conflict is dominated by one or more of:

- 경지 / 내공 / 무공 / 비급 / 영약
- 문파 / 세가 / 마교 / 무림맹 / 강호 위계
- 사부-제자 / 원한 / 복수 / 강호 평판 / 비무

## 5. Shared Stage Detection

The router keeps the existing cross-family stage file rules unless a family doc explicitly narrows them.

- `phase0_design` 없음: planning
- `phase0_design` 있음, `tr_block_070_draft` 없음: production
- `tr_block_070_draft` 있음, `0_bi_{work_id}.json` 없음: BI
- `BI`가 있어도 감리 FAIL이면 완료가 아니다

## 6. Shared Output Paths

These output paths remain shared across families.

- `treatments/{work_id}_phase0_design.json`
- `treatments/{work_id}_tr_block_070_draft.json`
- `bible/0_bi_{work_id}.json`

Stage 0 preprocess artifacts also remain shared unless a future family contract explicitly forks them.

- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`

## 7. Guardrails

- Do not modify `blockguide` semantics to force-fit `wuxguide` works.
- Do not route 무협/선협 works through `FinanceHUD`-first logic.
- Do not fork family docs without also updating the router family registry.
- Keep family docs narrow. Shared invariants belong here or in root `AGENTS.md`, not inside family docs.

## 8. Non-Goals

- This router does not define TR or BI field semantics.
- This router does not validate generated JSON.
- This router does not replace family-specific stage rules.

## 9. Router CLI

Use the routed CLI before opening any family harness.

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id> --json
```

Expected operator reads from the JSON:

- `family`: resolved family key
- `stage`: `planning`, `production`, `bi`, or `audit_or_repair`
- `artifact_state.preprocess_ready`: whether shared Stage 0 preprocess is ready
- `artifact_state.manual_audit_pass`: whether `phase0_ready_snapshot.manual_audit_pass == true`
- `planning_path`, `production_path`, `bi_path`: next harness docs

If `stage == planning` and `artifact_state.preprocess_ready == false`, return to `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md` before opening a family planning harness.
