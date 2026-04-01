# Lane 3: Artifact-Truth Vertical-Slice Draft

Date: 2026-03-31
Status: draft-bounded-partial-evidence
Lane: Opus Terminal 3 — artifact-truth vertical-slice
Master Order: `docs/2026-03-31/0_0-stage2-stage3-stage4-readiness-parallel-master-order.md`
Baseline Commit: `fd1707372bd7eb8ad23a5d4506ef556e3f72cc51`

## 1. Coverage

Artifacts directly inspected:

| Layer | Artifact | Inspected |
|---|---|---|
| Arc source | `plans/arcs/arc_001.txt` | Yes |
| Arc source | `plans/arcs/arc_002.txt` | Yes |
| Stage 2 JSON | `stage2/arc_001/attempt_01/final_arc__creative.json` | Yes |
| Stage 2 JSON | `stage2/arc_002/attempt_01/final_arc__balanced.json` | Yes |
| Stage 3 saved | `plans/blueprints/blueprint_0001.txt` | Yes |
| Stage 3 saved | `plans/blueprints/blueprint_0002.txt` | Yes |
| Stage 3 saved | `plans/blueprints/blueprint_0005.txt` | Yes |
| Stage 3 saved | `plans/blueprints/blueprint_0006.txt` | Yes |
| Stage 3 saved | `plans/blueprints/blueprint_0008.txt` | Yes |
| Stage 3 JSON | `stage3/ep_0001/attempt_01/final_blueprint__action_focused.json` | Yes |
| Stage 3 JSON | `stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` | Yes |
| Stage 3 JSON | `stage3/ep_0005/attempt_06/final_blueprint__action_focused.json` | Yes |
| Stage 3 JSON | `stage3/ep_0006/attempt_09/final_blueprint__dialogue_focused.json` | Yes |
| Stage 3 JSON | `stage3/ep_0008/attempt_01/final_blueprint__dialogue_focused.json` | Yes |
| Stage 4 manuscript | `stage4/ep_0001/attempt_01/final_manuscript__C.txt` | Yes |
| Stage 4 manuscript | `stage4/ep_0002/attempt_01/selected_candidate__A.txt` | Yes (REJECT) |
| DB | `project_data.db` (blueprints, stage_attempts, manuscripts, director_selections) | Yes |
| Log | `episode_production.jsonl` | Yes |

## 2. Findings

### F-1. Arc Source → Stage 2: CLEAN preservation, minor schema drift

**Artifact truth**: Stage 2 JSON artifacts preserve the arc source tactical document verbatim in the `tactical_doc` field. Beat sequences, episode details, and state constraints are structurally extracted and enriched.

**Schema drift** (minor): Arc 1 JSON uses `antagonists_in_play: [list]` for active villainy, while Arc 2 JSON uses `antagonist_name: string`. This is a Stage 2 generation-side schema inconsistency, not a source-authority problem. It does not contaminate downstream, but it means Stage 3/4 code consuming `arc_drive.narrative_drive.active_villainy` must handle two shapes.

**NPC duplication** (minor): Arc 2 lists 박성호 as `npc_introductions` at ep 5, but 박성호 was already introduced in Arc 1 ep 2. This is a cross-arc bookkeeping gap, not a narrative error.

**Severity**: LOW. Stage 2 is structurally sound as a source-of-truth emitter.

---

### F-2. Stage 2 → Stage 3 (Arc 1, ep 1-4): ADEQUATE alignment

**Artifact truth**: Blueprint .txt and .json artifacts match in content. Saved blueprint text in `plans/blueprints/` is identical to the `integrated_scenario` and `scene_breakdown` in the artifact JSON.

**Narrative fidelity**: Arc 1 blueprints faithfully follow the arc tactical doc:
- EP 1: 회귀 자각 → 형들 대면 → 서재에서 독립 선언 → 신탁 해지 연락 시작
- EP 2: 박성호 PB에게 전화 → 여의도 VIP 라운지 → 페널티 경고 → 20억 확보

**Scene structure**: 5 scenes per episode. Opening hooks, tension builds, dialogue duels, cliffhangers present. `content` field is empty in all scenes (ep 1, ep 2) — this is a generation-side omission but does not impair Stage 4 consumption since `integrated_scenario` carries the full prose.

**Attempt efficiency**: ep 1(1 attempt), ep 2(1 attempt), ep 3(4 attempts), ep 4(1 attempt). Acceptable convergence.

**Severity**: LOW.

---

### F-3. Stage 2 → Stage 3 (Arc 2, ep 5-9): PRIMARY DRIFT POINT — THREE CRITICAL CONTAMINATIONS

#### F-3a. Narrative fabrication (CRITICAL)

The arc tactical doc for ep 5 is purely a financial scene: 한시우 calls 박성호 PB from the opicel, orders 15억 WTI 3x leverage, 박성호 reluctantly complies.

The Stage 3 blueprint for ep 5 introduces:
- **Physical violence**: 불량배 breaks into the opicel, 한시우 fights with 쇠파이프, hand-to-hand combat
- **Organized crime subplot**: 태산개발 용역반장 최기태 as the mastermind behind the thugs (ep 6)
- **New character**: 제임스 강 (전 모건스탠리 애널리스트) as an intelligence asset (ep 6, 8)

**None of these exist in the arc source.** The Stage 3 generator fabricated entirely new plot elements, characters, and action sequences that the arc did not authorize. This is not a "weakness" or "drift" — it is a **structural contract violation** where Stage 3 output contradicts Stage 2 authority.

**Evidence**:
- Arc 2 tactical doc ep 5: "박성호 PB의 오만한 조언을 끊어내고 15억 원 규모의 WTI 3배 레버리지 매수를 지시하는 한시우"
- Blueprint ep 5 scene 1: "오피스텔에 무단 침입한 불량배를 한시우가 압도적인 물리력으로 제압"

#### F-3b. Institution name lock violation (CRITICAL)

- Arc source: "한미증권 VIP 전담 박성호 PB" (ep 5 tactical doc)
- All Arc 2 blueprints (ep 5-8): consistently use "신성증권" instead of "한미증권"
- Python prevalidation explicitly caught this: `기관 사실잠금 위반: 확정 '신성증권' → blueprint '한미증권' 사용` (CRITICAL severity)
- **The validator detected the violation but did not block the artifact.** The blueprint passed with score 91.

#### F-3c. Timeline misalignment (MAJOR)

- Arc 2 timeline: start = 2006-02-01, end = 2006-02-28
- EP 5 is the FIRST episode of Arc 2 → should be at the timeline START (2월 초)
- EP 5 blueprint `ending_state.timeline` says "2006년 2월 28일 심야" — this is the arc END date
- Python prevalidation caught this: `MAJOR: ending_state.timeline 불일치`
- EP 8 blueprint `ending_state.timeline` says "2006년 2월 초 새벽" — but EP 8 is arc ep 4 of 5, should be at ~2월 말
- The timeline is inverted: early episodes claim late dates and late episodes claim early dates

#### F-3 severity summary

| Issue | Severity | Validator detected? | Validator blocked? |
|---|---|---|---|
| Narrative fabrication | CRITICAL | No | No |
| Institution name lock | CRITICAL | Yes (CRITICAL) | No |
| Timeline inversion | MAJOR | Yes (MAJOR) | No |

**Attempt churn evidence**: EP 5 needed 6 attempts, EP 6 needed 9 attempts. The pipeline is struggling to converge but the validator cannot steer it back to arc fidelity.

---

### F-4. Stage 3 → Stage 4 (Arc 1): SECONDARY DRIFT with conflict detection working

**EP 1 (PASS, score 96)**:
- Manuscript follows blueprint structure and scene breakdown
- **New drift introduced**: Manuscript uses "SW그룹" where arc source says "한성그룹" — the protagonist's family conglomerate name changed. This is a Stage 4 generation-side error, not inherited from Stage 3.
- Manuscript saved to DB (manuscripts table, ep=1)

**EP 2 (REJECTED, score 96 → post_select_conflict)**:
- Director initially PASSED at score 96
- Downstream gate detected post-selection conflicts:
  - **CONTINUITY**: EP 1 manuscript ends inside 서재; EP 2 starts in 서재 앞 복도 — spatial disconnect
  - **HISTORY**: "SW그룹" (ep 1 manuscript) vs "한성그룹" (arc source) group name clash
  - **DETAIL**: 이면지 stored in "바지 주머니" (ep 1) vs "재킷 안주머니" (ep 2) — micro-continuity break
- Artifact saved as `rejected_best__A_narrative.txt` and `selected_candidate__A.txt` (same content hash) — NOT saved to manuscripts DB
- `STAGE4_RETRY_PATHOLOGY` event logged: `post_select_conflict|fix_pack:missing_fix_pack`
- **Stage 4 is paused here.**

**Severity**: MEDIUM. The conflict detection system works at Stage 4, but:
1. It catches problems AFTER generation, not before
2. The fix_pack mechanism failed (`missing_fix_pack`)
3. The root cause (group name drift) originates from the blueprint's insufficient grounding

---

### F-5. Metadata truth vs artifact truth alignment

| Episode | Stage | Metadata says | Artifact truth says | Aligned? |
|---|---|---|---|---|
| 1 | S3 | score 95, PASS, 1 attempt | Blueprint faithful to arc | Yes |
| 2 | S3 | score 90, PASS, 1 attempt | Blueprint faithful to arc | Yes |
| 5 | S3 | score 91, PASS, 6 attempts, quality_risk=true, CRITICAL+MAJOR warnings | Blueprint fabricates fight scenes, wrong institution, wrong timeline | **NO** — metadata flags issues but still says PASS |
| 6 | S3 | score 90, PASS, 9 attempts, quality_risk=true | Blueprint continues fabricated violence, adds unauthorized character | **NO** — 9 attempts is a failure signal, but metadata says PASS |
| 8 | S3 | score 85, PASS, 1 attempt, quality_risk=false, 0 warnings | Blueprint has wrong institution (신성증권), unauthorized character (정보원) | **NO** — metadata shows clean pass, artifact has fact lock violations |
| 1 | S4 | score 96, PASS | Manuscript generally aligned but introduces SW그룹 drift | Mostly yes |
| 2 | S4 | score 96 → REJECT (post_select_conflict) | Manuscript has continuity and history conflicts | **Yes** — metadata correctly caught the problem |

**Key observation**: Stage 3 metadata systematically under-reports artifact problems. Stage 4 metadata is more honest about catching conflicts, but by then the damage is upstream.

---

### F-6. Per-episode attempt distribution (Stage 3)

| Episode | Arc | Attempts | Score | Observation |
|---|---|---|---|---|
| 1 | 1 | 1 | 95 | Clean first pass |
| 2 | 1 | 1 | 90 | Clean first pass |
| 3 | 1 | 4 | 95 | Moderate churn |
| 4 | 1 | 1 | 93 | Clean first pass |
| 5 | 2 | 6 | 91 | Heavy churn, CRITICAL+MAJOR warnings unblocked |
| 6 | 2 | 9 | 90 | Severe churn, fabrication persists through 9 attempts |
| 7 | 2 | 2 | 90 | Light churn |
| 8 | 2 | 1 | 85 | Passed first try at lowest score, silent fact violations |
| 9 | 2 | 1 | 95 | Clean first pass |

**Arc boundary effect**: Arc 1 total = 7 attempts (avg 1.75). Arc 2 total = 19 attempts (avg 3.8). The arc boundary is where blueprint generation struggles.

---

### F-7. DB truth

- `blueprints` table: 9 rows (ep 1-9), all with data. Consistent with on-disk artifacts.
- `manuscripts` table: 1 row (ep 1 only). EP 2 was rejected and never committed. EP 3-9 were never reached at Stage 4.
- `stage_attempts` table: Correctly records all Stage 3 attempts (including retries) and Stage 4 attempts (ep 1-2 only).
- DB state is consistent with artifact-on-disk state.

## 3. Non-Issues

- **Stage 2 tactical doc preservation**: Verbatim. No content loss or mutation.
- **Stage 2 enrichment quality**: arc_drive, state_changes, state_constraints, joint_docs are all structurally populated and internally consistent.
- **Arc 1 vertical slice (ep 1-4)**: Source → Stage 2 → Stage 3 → Stage 4 pipeline is functionally intact. The drift that occurs (SW그룹 name) is a Stage 4 generation error, not a pipeline structural failure.
- **Stage 4 post-selection conflict detection**: Working correctly. The system caught real continuity and history conflicts in EP 2.
- **DB consistency**: On-disk artifacts match DB records. No phantom records or missing artifacts.
- **Blueprint structure completeness**: All blueprints have integrated_scenario, scene_breakdown (5 scenes), core_tension, expected_ending, protagonist_state, relationship_changes, ending_hook. The structure is Stage4-consumable.

## 4. Verdict

### artifact-fragile

**Justification**:

The vertical slice reveals a **clean pipeline for Arc 1** and a **structurally contaminated pipeline for Arc 2**. The contamination occurs at the **Stage 2 → Stage 3 boundary** where:

1. The blueprint generator fabricates narrative content (fight scenes, new characters) not authorized by the arc tactical document
2. The blueprint generator mutates locked facts (institution names) that the arc source established
3. The validator detects some of these issues (CRITICAL, MAJOR severity) but does **not block** the artifacts
4. High retry counts (6, 9 attempts) indicate the generation loop cannot converge to arc-faithful output

This is not yet **artifact-blocking** because:
- Arc 1 artifacts are structurally ready for Stage 4
- The Stage 3 blueprint structural format (scenario, scenes, tension, ending) is correct even when content is fabricated
- Stage 4's post-selection conflict detector catches some downstream contamination

But it is more than **artifact-ready** because:
- Arc 2 blueprints cannot be trusted as Stage 4 input without human review
- The validator's inability to block CRITICAL violations means the quality gate is structurally insufficient
- Stage 4 is already paused at EP 2 with unresolvable conflicts, and the Arc 2 blueprints waiting downstream have worse problems than the ones that already caused the pause

### Primary blocker: Stage 3 generation fidelity to arc source, compounded by Stage 3 validator blind spots

### Arc-level readiness

| Arc | Verdict | Rationale |
|---|---|---|
| Arc 1 (ep 1-4) | artifact-ready (with minor caveats) | Blueprints faithful to arc, Stage 4 ep 1 PASSED, ep 2 has resolvable conflicts |
| Arc 2 (ep 5-9) | artifact-blocking | Fabricated narratives, violated fact locks, inverted timelines, 9-attempt churn — not Stage4-consumable without rework |

## 5. Required Artifacts

### Vertical-Slice Truth Table

| Layer | Arc 1 (ep 1-4) | Arc 2 (ep 5-9) |
|---|---|---|
| Arc source | CLEAN | CLEAN |
| Stage 2 JSON | CLEAN (minor schema drift) | CLEAN (minor schema drift, NPC dupe) |
| Stage 3 blueprint content | FAITHFUL to arc | FABRICATED (fight scenes, new chars, wrong institution, wrong timeline) |
| Stage 3 validator | ADEQUATE | INSUFFICIENT (detects but does not block CRITICAL issues) |
| Stage 3 metadata accuracy | ALIGNED | MISALIGNED (metadata says PASS despite CRITICAL violations) |
| Stage 4 manuscript | EP1 PASS (SW그룹 drift), EP2 REJECT (continuity) | NOT REACHED |
| DB consistency | CONSISTENT | CONSISTENT (blueprints saved despite quality issues) |

### Per-Episode Readiness Table

| Episode | Arc | S3 attempts | S3 score | S3 artifact quality | S4 status | S4-ready? |
|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 95 | Faithful to arc | PASS (score 96, manuscript saved) | YES |
| 2 | 1 | 1 | 90 | Faithful to arc | REJECT (post_select_conflict, paused) | YES with fix |
| 3 | 1 | 4 | 95 | Likely faithful (not inspected in detail) | Not started | Probably |
| 4 | 1 | 1 | 93 | Likely faithful (not inspected in detail) | Not started | Probably |
| 5 | 2 | 6 | 91 | FABRICATED: fight scenes, wrong institution, wrong timeline | Not started | NO |
| 6 | 2 | 9 | 90 | FABRICATED: violence, new chars, wrong institution | Not started | NO |
| 7 | 2 | 2 | 90 | Not inspected in detail | Not started | UNKNOWN |
| 8 | 2 | 1 | 85 | Wrong institution, unauthorized character, timeline issues | Not started | NO |
| 9 | 2 | 1 | 95 | Not inspected in detail | Not started | UNKNOWN |

## Stop

read-only lane complete; no files mutated
