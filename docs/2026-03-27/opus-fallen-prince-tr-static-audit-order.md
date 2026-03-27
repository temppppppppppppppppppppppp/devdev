# OPUS Fallen Prince TR Static Audit Order

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
- smallest remaining unproven step: `TR static audit` (ladder Step 2)

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- do not modify TR — this is audit only
- do not modify BI — this is audit only
- do not skip to BI repair before TR verdict is rendered
- do not promote to active path in the same run

## 3. Canonical Target

- work_id: `fallen_prince_buys_joseon`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json` (reference only)

Both files are read-only in this run.

## 4. Proven Prior Steps

1. Pair consumability survey:
   - `docs/2026-03-27/fallen-prince-pair-consumability-survey.md`
   - verdict: `pass with warnings` — 8 promotion blockers, HIGH skeleton risk
2. Consumability repair:
   - `docs/2026-03-27/fallen-prince-consumability-repair-report.md`
   - verdict: `pass` — 8/8 blockers resolved, pair is contract-level consumable

Known context from survey:
- **skeleton risk HIGH** — event_villain/solution/stakes 70/70 동일 템플릿
- **살릴 수 있는 뼈대** — title 70종, deal_type 70종, location 69종, 역사이벤트 매핑, source_binding, foreshadow 교차참조, 자본궤적 4억→1조6,400억

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/fallen-prince-pair-consumability-survey.md` (skeleton evidence 상세)
5. `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md` (format + 9축 평가 reference)

## 6. Immediate Goal

Execute exactly one bounded `TR static audit` (ladder Step 2) for `fallen_prince_buys_joseon`.

The audit must answer one question: **이 TR은 usable production spine인가, regeneration이 필요한가?**

Allowed verdicts (ladder harness §5 Step 2):
- `strong spine` → continue to BI repair
- `usable spine but mixed` → continue to BI repair
- `consumable but skeleton-likely` → may continue to BI repair, but with caveats
- `regenerate TR first` → regenerate TR, then restart ladder

## 7. Audit Method — 9-Axis Evaluation

Use the same 9-axis framework as `pantech-cyworld-tr-static-quality-audit.md`.

### Axis 1. Premise / Commercial Hook Persistence

- Is the premise (몰락 황족이 1907년으로 회귀하여 대한제국 자산을 지키고 근대 금융 제국을 건설) persistent across 70 blocks?
- Does the hook shift or dilute? Where?
- Score /10

### Axis 2. Protagonist Engine Strength

- Is 이강윤's engine (미래지식 기반 자산 선점 + 정체 노출 리스크) well-defined?
- Does the regression mechanic create sustained tension?
- POV rotation: any, or 100% single POV?
- Score /10

### Axis 3. Growth-Resource / Leverage Logic Clarity

- Capital trajectory (4억 → 1조6,400억) — is it internally coherent?
- deal_type diversity (survey reports 70 unique) — is this genuine or surface variation?
- Setback blocks count and quality
- Score /10

### Axis 4. Block Progression Density

- Content length statistics: context, solution avg/stdev by half
- Do blocks degenerate to 1-2 line summaries in back half?
- 1-block-per-X pacing or multi-block sustained conflict?
- Score /10

### Axis 5. Sceneability

- **CRITICAL AXIS for this TR**: given skeleton risk HIGH, are there scene-grade blocks at all?
- Sample 5 blocks across different arcs: does any block have a specific location, dialogue marker, sensory detail, or spatial cue?
- Or is every block a template-filled deal summary?
- Score /10

### Axis 6. Foreshadow / Callback Density

- Survey reports foreshadow cross-references exist — are these genuine inter-block causal links or formulaic X→Y templates?
- Resolution rate
- Score /10

### Axis 7. Antagonist Roster Diversity

- Survey reports 11 unique opponents / 70 blocks — is this adequate for the work's scale?
- Do opponents escalate or are they flat?
- Score /10

### Axis 8. Genre-Specific Texture

- **1907~1938 대한제국/일제강점기 질감**: 역사 이벤트가 서사에 유기적으로 녹아드는가, 배경 장식인가?
- 해운·보험·철도·은행·광산 5대 병목이 구체적 비즈니스 로직으로 전개되는가?
- 식민지 경제, 유럽 금융, 일본 재벌과의 경쟁이 장르적 질감을 유지하는가?
- Score /10

### Axis 9. Overall Structural Integrity

- Front-half vs back-half quality gradient
- Template contamination rate (event_villain/solution/stakes)
- Skeleton 안의 salvageable spine vs disposable template
- Score /10

## 8. Skeleton-Specific Deep Dive

Because survey already flagged HIGH skeleton risk, the audit must explicitly:

1. **Quantify template contamination**: event_villain, solution, stakes 외에도 context, reward, regression_ext 등에서 반복 패턴을 측정
2. **Identify salvageable spine elements**:
   - title (70종 unique)
   - deal_type (70종 unique)
   - location (69종 unique)
   - historical_event mapping
   - source_binding (material_bank.db AH-* 소스)
   - foreshadow cross-references
   - capital trajectory breakpoints
   - relationship_delta patterns
3. **Judge regeneration scope**: 만약 regenerate 판정이면, 전면 재생성인가 / 뼈대 유지 densification인가?

## 9. Comparison Anchor

For calibration, use `pantech_cyworld_reborn` TR as the "usable spine but mixed" reference point:

| Metric | pantech (mixed) | fallen_prince (expected?) |
|--------|-----------------|--------------------------|
| Context stdev | 42 | 13 (survey) |
| Template repetition | 0/70 | 70/70 (survey) |
| Opponent unique | 68/70 | 11/70 (survey) |
| deal_type unique | 28/70 | 70/70 (survey) |
| Foreshadow resolution | 60% | Unknown |

This comparison should anchor the verdict calibration.

## 10. Deliverable

Save exactly one main report:

- `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md`

The report should include:
- target TR path
- 9-axis evaluation with score per axis
- skeleton-specific deep dive
- salvageable spine inventory
- front-half vs back-half comparison
- comparison with pantech reference
- overall score
- **verdict**: one of the four allowed verdicts
- next unit recommendation
- if verdict is "regenerate TR first": specify recommended regeneration scope (full vs spine-preserving densification)

## 11. Stop Conditions

Stop immediately and report if any of the following occurs:

- TR file is missing or corrupted
- TR identity mismatches BI
- confidence falls below 95% and no smaller bounded next step exists

## 12. Expected Next Unit After This Order

- if verdict is `strong spine` or `usable spine but mixed`: `BI repair` (ladder Step 3)
- if verdict is `consumable but skeleton-likely`: `BI repair` with caveats, or decision point
- if verdict is `regenerate TR first`: `TR regeneration` — specify scope, then restart ladder

## 13. Handoff Format

End with this exact flat report:

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR static audit
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- this is audit only — no file modification
- verdict must be one of four allowed values

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `TR static audit`
- skeleton risk HIGH is explicitly carried forward from survey
- 9-axis framework + skeleton deep dive provides structured evaluation
- pantech comparison anchor provides calibration reference
- regeneration scope guidance is included for the most likely verdict

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- no multi-unit overreach beyond one bounded audit step

Confidence:
- 97% that `TR static audit` is the correct next OPUS unit for this pair
