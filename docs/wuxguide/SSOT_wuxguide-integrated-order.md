# Wuxguide Integrated Order

Date: 2026-03-20
Status: active
Scope: wuxia / xianxia narrative family
Entry Point: `docs/narrative-router/SSOT_narrative-router-integrated-order.md`

## 1. Purpose

- Provide a family SSOT for wuxia / xianxia planning, TR, BI, and audit.
- Preserve existing `blockguide` semantics for modern-fantasy business-power works.
- Make `MartialHUD` canonical for martial-family BI output.

## 2. Read Order

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. this file
3. `docs/wuxguide/wuxia-planning-harness.md`
4. `docs/wuxguide/wuxia-production-harness.md`
5. `docs/wuxguide/wuxia-bi-production-harness.md`
6. `docs/wuxguide/treatment-densification-harness-v1.md` — TR 밀도 부족 판정 시에만 진입 (§0C 진입 게이트 참조)

## 3. Family Identity

Choose `wuxguide` when the dominant story engine is martial-family first:

- realm progression
- internal-energy / cultivation gain
- martial-art acquisition or refinement
- sect / clan / jianghu politics
- revenge, grievance, inheritance, or manual / treasure pursuit

Do not choose `wuxguide` just because the story contains action scenes.

## 4. Shared Stage Policy

- `phase0_design` missing: planning
- `phase0_design` exists and `tr_block_070_draft` missing: production
- `tr_block_070_draft` exists and `0_bi_{work_id}.json` missing: BI
- existing BI still requires audit PASS before completion

Intermediate artifact quarantine:

- `phase0_design` is an intermediate artifact. Once TR and BI both exist and pass 5-Pass audit,
  move `phase0_design` to `treatments/_quarantine/`.
- Rationale: after TR+BI are complete, the canonical truth is TR+BI, not `phase0_design`.
  Keeping `phase0_design` active creates ambiguity when it drifts from TR/BI.
- Do not delete — preserve in `_quarantine/` for debug/audit trail.
- Stage detection: if `phase0_design` is in `_quarantine/` and TR+BI exist, stage = audit/review.

## 5. Shared Artifact Paths

- `treatments/preprocess/{work_id}/source_manifest.json`
- `treatments/preprocess/{work_id}/profile_lock.json`
- `treatments/preprocess/{work_id}/material_bundle_summary.json`
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`
- `treatments/{work_id}_phase0_design.json`
- `treatments/{work_id}_tr_block_070_draft.json`
- `bible/0_bi_{work_id}.json`

## 6. Canonical Semantic Shift

Inside `wuxguide`, the canonical BI root is `MartialHUD`.

- `FinanceHUD` is not canonical for this family.
- runtime aliasing is allowed only when a bridge explicitly requires it.
- the core progression axes are `realm`, `internal_energy`, `martial_arts`, `faction`, and `jianghu_reputation`.

## 7. Operator Runbook

Always start from the router:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id> --json
```

Resume rules:

1. If `stage == planning`, open `docs/wuxguide/wuxia-planning-harness.md`.
2. If `stage == production`, open `docs/wuxguide/wuxia-production-harness.md`.
3. If `stage == bi`, open `docs/wuxguide/wuxia-bi-production-harness.md`.
4. If `stage == audit_or_repair`, audit the BI first and repair the smallest failing layer.
5. Production 재개 시에는 `treatments/preprocess/{work_id}/sequential_run_status.json`을 먼저 읽고, `.md`는 deprecated fallback으로만 취급한다.
6. Production auto-run은 내부 단위가 항상 1블록이며, 같은 운영 오더에서 최대 5블록까지만 허용한다.

If `artifact_state.preprocess_ready == false`, return to `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md` before family planning.

## 8. Routed CLI Examples

Planning gate check:

```bash
python -X utf8 scripts/narrative_router.py --genre wuxia --work-id <work_id>
```

TR prompt / check / merge:

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia prompt --draft treatments/<work_id>_tr_block_070_draft.json --roadmap bible/0_bi_<work_id>.json --start 1 --batch-size 1
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia check --candidate treatments/<candidate>.json --draft treatments/<work_id>_tr_block_070_draft.json --start 1 --batch-size 1 --report treatments/<work_id>_batch_check.md
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia merge --draft treatments/<work_id>_tr_block_070_draft.json --candidate treatments/<candidate>.json --start 1 --batch-size 1 --report treatments/<work_id>_batch_merge.md
```

BI build and audit:

```bash
python -X utf8 scripts/build_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --output bible/0_bi_<work_id>.json
python -X utf8 scripts/audit_narrative_bi.py --genre wuxia --phase0 treatments/<work_id>_phase0_design.json --draft treatments/<work_id>_tr_block_070_draft.json --bi bible/0_bi_<work_id>.json --report bible/audit_reports/<work_id>_wuxia_bi_5pass.md
```

## 9. Guardrails

- Do not force `capital_before/after` into wuxia validation.
- Do not reuse `deal_type`, `business_lines`, `company_state`, or `starter_company` as primary martial-family anchors.
- Do not pass BI while `MartialHUD` is incomplete or out of sync with the final TR block.

## 10. Failure Triage (실패 분류)

TR/BI 감리 중 발견되는 무협 특화 실패 유형과 대응 절차.

| 실패 유형 | 증상 | 대응 |
|-----------|------|------|
| `realm_continuity_failure` | 경지가 이전 블록과 불일치 (예: Block 15에서 선천인데 Block 16에서 후천으로 회귀) | 해당 블록 재생산 |
| `martial_art_logic_failure` | 미습득 무공 사용, 봉인된 무공 사용 (예: 아직 배우지 않은 검법으로 전투) | 해당 블록 재생산 |
| `injury_tracking_failure` | 부상 상태 무시하고 전투 (예: 직전 블록에서 단전에 중상인데 다음 블록에서 전력 전투) | 해당 블록 + 직전 블록 재검토 |
| `npc_deceased_violation` | 사망 NPC가 행동/대사 (예: Block 20에서 사망한 NPC가 Block 25에서 대화) | 해당 블록 재생산 |
| `faction_drift` | 문파 소속이 설명 없이 변경 (예: 화산파 제자가 갑자기 무당파 소속으로 표기) | Phase 0 재검토 후 블록 재생산 |
| `foreshadow_orphan` | 심은 복선이 회수 없이 종료 (예: Block 5에서 심은 비급 단서가 Block 70까지 언급 없음) | BI 감리에서 포착, TR 보충 블록 필요 |
| `density_failure` | 같은 적대자/무공 3블록 연속 (예: Block 11~13 모두 동일 적대자와 동일 무공으로 전투) | 밀도 게이트 재적용 후 재생산 |
| `handoff_false_pass` | Stage 0 산출물 부실인데 통과됨 (예: profile_lock에 경지축이 없는데 Planning을 통과) | Stage 0 재진입 |

### 10.1 실패 분류 절차

1. 감리 중 위 유형에 해당하는 결함을 발견하면 `failure_type` 태그를 붙인다.
2. 대응 열의 지시에 따라 재작업 범위를 결정한다.
3. 재생산 시 해당 블록의 `MartialHUD` 상태를 직전 블록과 대조하여 연속성을 확인한다.
4. Phase 0 재검토가 필요한 유형(`faction_drift`, `foreshadow_orphan`)은 Phase 0 수정 후 영향받는 모든 블록을 재검토한다.
5. `handoff_false_pass`는 Stage 0부터 재진입하므로 가장 비용이 크다. `stage0_handoff_validator.py`를 반드시 재실행한다.

### 10.2 실패 우선순위

재작업 비용이 낮은 순서대로 처리한다:

1. `npc_deceased_violation` — 단일 블록 수정
2. `realm_continuity_failure` — 단일 블록 수정
3. `martial_art_logic_failure` — 단일 블록 수정
4. `injury_tracking_failure` — 2블록 재검토
5. `density_failure` — 밀도 재조정 후 재생산
6. `foreshadow_orphan` — BI 단계 보충
7. `faction_drift` — Phase 0 + 블록 재생산
8. `handoff_false_pass` — Stage 0 재진입

---

## 11. 자동 진행 정책

단계 전환은 정지 게이트가 아니다. Go 조건이 충족되면 멈추지 않고 다음 단계로 넘어간다.

project-only handoff mode:

- 사용자가 `work_id`나 특정 pair만 주면 먼저 live 파일과 최신 감리 산출물을 읽고 현재 단계를 판정한다.
- 다음 필수 단위가 명확하면 그 단위를 바로 진행한다.
- 단계나 대상이 모호할 때만 짧은 clarifying question 1회로 정리한다.
- 사용자가 단계를 직접 말하지 않았다는 이유만으로 멈추지 않는다.

Production 단위 규칙:

- Production auto-run의 내부 단위는 항상 `Block 1개`다.
- 같은 운영 오더에서 자동 연속 가능한 최대치는 **5블록**이다.
- `Block 005/010/015...` 경계에 도달하면 새 오더 전까지 반드시 멈춘다.
- BI auto-run은 `handoff 1사이클`까지만 허용한다. sync/audit PASS 또는 FAIL 보고가 끝나면 반드시 정지한다.

금지:
- "Stage 0 끝났습니다. Planning으로 갈까요?"
- "Phase 0 설계 완료했습니다. Production 시작할까요?"
- "TR 70블록 완료했습니다. BI 만들까요?"

허용:
- "Stage 0 완료. Planning 진입." (1줄 상태 보고 후 즉시 진행)
- "Block 4 완료. Block 5 시작." (같은 운영 오더 내 허용)
- "TR 70 완료. BI handoff 1사이클 진행." (상태 보고 후 바로 감리/동기화)

유일한 정지 조건:
- manual_audit_pass 필요 시 (Stage 0 → Planning 전환)
- context window 한계 도달
- 같은 운영 오더에서 5블록 창 소진
- BI handoff 1사이클 완료
- 사용자의 명시적 정지 지시
