# T1. Run Chronology + Sink Reconciliation

Date: 2026-03-24
Status: final (3-pass audited)
Document Type: lane survey report
Master Order: `docs/2026-03-24/ep5-ep7-midarc-residual-6terminal-master-order.md`
Lane: T1 — Run Chronology + Sink Reconciliation
Report Path: `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t1-run-chronology-and-sinks.md`
Evidence Path: `docs/2026-03-24/opus-ep5-ep7-midarc-residual/t1-run-chronology-and-sinks-evidence.md`

Primary Evidence Sources:
- `docs/2026-03-24/console.txt` (1849 lines)
- `projects/0324_00_/logs/episode_production.jsonl` (42 lines)
- `projects/0324_00_/logs/quality_metrics.jsonl` (lines 44-65)
- `projects/0324_00_/logs/runtime_audit.jsonl` (contains same EP5-7 pathology events as episode_production.jsonl)

## 1. Run Chronology — EP5-EP7 Reconstruction

### 1.1 EP5 (Arc 2, Position 1/5, "여의도 입성")

| Round | Wall Clock | Console Verdict | Console Score | Gate |
|---|---|---|---|---|
| R1 | 18:37:08 | PASS_WITH_FIX → post_select_conflict → retry | 92 | post_select_conflict |
| R2 | 18:41:00 | REJECT | 78 | director_primary_reject |
| R3 | 18:48:28 | PASS | 95 | director_primary_pass |

- Total rounds: **3**
- Final output: 7172자, blueprint coverage 100% (5/5)
- Console R1 rejection cause: 박성호 PB 소속 변경 (3화 시중은행 → 5화 한미증권)
- Console R2 rejection cause: score drop after retry (Director REJECT)
- R3: ASP red team correction triggered at round 3

### 1.2 EP6 (Arc 2, Position 2/5, "15억의 베팅")

| Round | Wall Clock | Console Verdict | Console Score | Gate |
|---|---|---|---|---|
| R1 | 18:54:40 | REJECT | 75 | director_primary_reject |
| R2 | ~19:03 | PASS (Director) → CoVe runtime failure → PASS preserved | 90 | director_primary_pass |

- Console claims **2 rounds** total
- Final output: 5896자, blueprint coverage 60% (3/5, invalid)
- Console R1 rejection: location continuity (시중은행 → 한미증권), balance error (5억 vs 4.7억)
- Console R2: Director PASS, CoVe LLM verification JSONDecodeError → PASS preserved
- However, quality_metrics shows **3 validation events** (see Sink Mismatch section)

### 1.3 EP7 (Arc 2, Position 3/5, "조롱과 확신")

| Round | Wall Clock | Console Verdict | Console Score | Gate |
|---|---|---|---|---|
| R1 | ~19:10 | REJECT | 86 | director_primary_reject |
| R2 | ~19:14 | REJECT | 75 | director_primary_reject |
| R3 | ~19:16 | PASS | 96 | director_primary_pass |

- Total rounds: **3** per console
- Final output: 5109자, blueprint coverage 60% (3/5, invalid)
- Console R1 rejection: location continuity error — blueprint says 한미증권, should be 시중은행 본점
- Console R2 rejection: POV violation — entire manuscript written in 1인칭 instead of 3인칭
- R3: ASP red team + corrected → Director PASS

## 2. Sink-by-Sink Comparison

### 2.1 Cross-Sink Score Matrix

| EP | Round | Console Score | quality_metrics Score | episode_production Score |
|---|---|---|---|---|
| 5 | R1 | 92 | 93 | 93 |
| 5 | R2 | 78 | 93 | 93 |
| 5 | R3 | 95 | 95 | (not recorded) |
| 6 | R1 | 75 | 78 | 83 |
| 6 | R2 | 90 (PASS) | 44 (REJECT!) | 69 (firewall) |
| 6 | R3 | (not visible) | 98 (PASS) | (not recorded) |
| 7 | R1 | 86 | **MISSING** | **MISSING** |
| 7 | R2 | 75 | **MISSING** | **MISSING** |
| 7 | R3 | 96 | 90 | (not recorded) |

### 2.2 Cross-Sink Round Count Matrix

| EP | Console Rounds | quality_metrics Validation Events | episode_production Pathology Events |
|---|---|---|---|
| 5 | 3 (R1 PASS_WITH_FIX→retry, R2 REJECT, R3 PASS) | 3 (REJECT 93, REJECT 93, PASS 95) | 2 (R1, R2 pathology only) |
| 6 | 2 (R1 REJECT, R2 PASS) | 3 (REJECT 78, REJECT 44, PASS 98) | 2 (R1, R2 pathology) + 1 CoVe advisory |
| 7 | 3 (R1 REJECT, R2 REJECT, R3 PASS) | 1 (PASS 90 only) | 0 |

## 3. Confirmed Sink Mismatches

### 3.1 [CRITICAL] EP7 — Complete JSONL Blackout for R1/R2

**Classification: `sink mismatch`**

Console clearly shows 3 rounds for EP7 with two distinct, meaningful REJECT reasons:
- R1: 한미증권 location error (blueprint-originated)
- R2: POV violation (1인칭 vs 3인칭)

Neither REJECT round appears in any JSONL sink:
- `episode_production.jsonl`: 0 pathology entries for EP7
- `quality_metrics.jsonl`: 0 validation REJECT entries for EP7
- Only 1 Director retrieval observation recorded (vs 3 for EP5, 3 for EP6)

This is not an observer selectivity issue — the complete absence of all event types (retrieval, validation, pathology) for R1 and R2 indicates a systemic recording gap during EP7 processing.

Evidence anchors:
- `console.txt` L1611-1842: full 3-round EP7 production
- `quality_metrics.jsonl` L61-64: only final PASS and 1 retrieval observation
- `episode_production.jsonl`: no EP7 Stage 4 entries at all

### 3.2 [CRITICAL] EP6 R2 — Three-Way Verdict Disagreement

**Classification: `sink mismatch`**

The three sinks record fundamentally different events for EP6 R2:

| Sink | Verdict | Score | Gate/Reason |
|---|---|---|---|
| Console | **PASS** | 90 | director_primary_pass, CoVe failure → PASS preserved |
| quality_metrics | **REJECT** | 44 | director_reject |
| episode_production | **firewall** | 69 | continuity_firewall, 자본금정합 |

The console says EP6 was completed in 2 rounds (R2 = PASS), but quality_metrics records a third validation event (PASS at score 98, timestamp 19:05:07) that the console does not display. Either:
- (a) The console display is misleading: the continuity firewall actually rejected R2 and a hidden R3 ran
- (b) The metrics recorded an intermediate firewall evaluation as a separate REJECT

Given that quality_metrics also has a third Director retrieval observation (19:02:09) between the R2 REJECT (18:58:25) and the final PASS (19:05:07), interpretation (a) is more likely: **a real R3 occurred but was invisible in console output**.

Evidence anchors:
- `console.txt` L1576-1588: R2 Director PASS → CoVe failure → PASS preserved
- `quality_metrics.jsonl` L55-60: REJECT(78), REJECT(44), PASS(98) — three events
- `episode_production.jsonl` L37-39: R1 pathology, R2 firewall, CoVe advisory

### 3.3 [IMPORTANT] EP5 R2 Score Mismatch

**Classification: `sink mismatch`**

Console R2 Director score: **78** (REJECT)
quality_metrics R2 score: **93** (REJECT)
episode_production R2 score: **93** (post_select_conflict pathology)

A 15-point gap between the Director's reported score (78) and the JSONL recorded score (93) for the same round. The JSONL appears to record the candidate's pre-Director evaluation score rather than the Director's verdict score.

This means the JSONL score field is not the Director's score — it is a different metric. Operators relying on JSONL scores to understand retry severity will see misleadingly high scores.

Evidence anchors:
- `console.txt` L1324: Director REJECT score 78
- `quality_metrics.jsonl` L49: validation REJECT score 93
- `episode_production.jsonl` L36: pathology score 93

### 3.4 [IMPORTANT] EP5 arc_no Metadata Error

**Classification: `artifact-truth mismatch`**

`episode_production.jsonl` records EP5 blueprint as `arc_no: 1`.
Console clearly shows: `📐 제5화 Blueprint 생성 중... (Arc 2, 주인공: 한시우)`.
EP6/EP7 blueprints correctly record `arc_no: 2`.

This is a Stage 3 blueprint metadata recording error for EP5 only.

Evidence anchors:
- `episode_production.jsonl` L26: `"ep_num": 5, "arc_no": 1`
- `console.txt` L880: `제5화 Blueprint 생성 중... (Arc 2, 주인공: 한시우)`

### 3.5 [IMPORTANT] EP5 R1 Contradiction Type Mismatch

**Classification: `sink mismatch`**

Console post-select conflict: "제3화에서 시중은행 소속이었던 박성호 PB가 제5화에서는 한미증권 소속으로 등장" (NPC affiliation mismatch).

episode_production pathology: `contradiction_type: "레버리지계산"` with reasoning about "레버리지 배수와 진입 계약 수 사이의 산술적 불일치" (leverage arithmetic error).

These are **two different contradictions** reported for the same round. The console displays the post-select continuity check's finding (PB affiliation), while the JSONL records the pathology observer's finding (leverage calculation). Both are real issues, but the sinks disagree on which is the primary.

Evidence anchors:
- `console.txt` L1234-1240: PB affiliation conflict
- `episode_production.jsonl` L35: contradiction_type=레버리지계산

### 3.6 [IMPORTANT] EP6 R1 Three-Way Score Disagreement

**Classification: `sink mismatch`**

| Sink | EP6 R1 Score |
|---|---|
| Console | 75 |
| quality_metrics | 78 |
| episode_production | 83 |

Three different scores for the same round across three sinks. Likely each sink records a different scoring perspective:
- Console: Director verdict score
- quality_metrics: validation pipeline score
- episode_production: pathology observer score

Evidence anchors:
- `console.txt` L1508: score 75
- `quality_metrics.jsonl` L55: score 78
- `episode_production.jsonl` L37: score 83

### 3.7 [SECONDARY] EP7 Final Score Mismatch

**Classification: `sink mismatch`**

Console R3 PASS score: **96**
quality_metrics PASS score: **90**

A 6-point gap for the final accepted episode.

Evidence anchors:
- `console.txt` L1812: score 96
- `quality_metrics.jsonl` L64: score 90

### 3.8 [SECONDARY] EP6/EP7 Blueprint Coverage 60%

**Classification: `validator-only signal`**

Both EP6 and EP7 accepted manuscripts have only 60% blueprint coverage (3/5 scenes reflected), flagged as `valid: false`. EP5 achieved 100%. This means the Director accepted manuscripts that substantially deviated from the blueprint design.

This is not a sink mismatch but a separate quality signal: the retry loop converged on a PASS that doesn't fully implement the blueprint. Whether this is a problem depends on whether the blueprint was itself faulty (see T3 lane).

Evidence anchors:
- `quality_metrics.jsonl` L59: EP6 coverage 60%
- `quality_metrics.jsonl` L63: EP7 coverage 60%

## 4. EP5-EP7 Rescue Round Causal Summary

### EP5: Primary cause = blueprint location/NPC error → Stage 4 conflict detection
- Blueprint contained 한미증권 reference → manuscripts reproduced it → post_select_conflict caught PB affiliation mismatch
- Secondary: leverage arithmetic errors in manuscript (not in blueprint)
- Rescue cost: 2 extra rounds

### EP6: Primary cause = blueprint location error + capital state drift
- R1: Blueprint's 한미증권 location → Director REJECT for location and timing errors
- R2: Director PASS, but post-select firewall caught capital consistency issue (score 69/44) → likely triggered hidden R3
- Rescue cost: 1-2 extra rounds (depends on whether hidden R3 is real)

### EP7: Primary cause = blueprint location error + LLM POV failure
- R1: Blueprint's 한미증권 location error reproduced again → Director REJECT
- R2: Patch mode produced 1인칭 manuscript (POV violation) → Director REJECT
- R3: ASP red team corrected → PASS
- Rescue cost: 2 extra rounds
- **Both R1 and R2 are completely invisible in JSONL sinks**

### Common Root: Stage 3 Blueprint Location Error (한미증권)

All three episodes share the same upstream cause: the Stage 3 blueprint for EP6 contained `여의도 한미증권 VIP룸` as the starting location, contradicting the established story fact that the protagonist operates from `시중은행 본점 VIP 라운지`. This error propagated into EP6 and EP7 blueprints and was faithfully reproduced by the Chief Writer ensemble, requiring the Director to repeatedly REJECT and correct.

## 5. Lane Classification

| Claim | Classification |
|---|---|
| EP7 has 2 REJECT rounds invisible to all JSONL sinks | `confirmed primary cause` (of observability gap) |
| EP6 R2 has three-way verdict disagreement across sinks | `confirmed primary cause` (of sink truth divergence) |
| EP5 R2 score mismatch (78 vs 93) indicates JSONL records non-Director score | `confirmed secondary amplifier` |
| EP5 arc_no=1 is a metadata recording error | `artifact-truth mismatch` |
| EP5 R1 contradiction type differs between console and JSONL | `sink mismatch` |
| EP6 R1 has three different scores across sinks | `sink mismatch` |
| EP7 final score gap (96 vs 90) | `sink mismatch` |
| EP6/EP7 60% blueprint coverage accepted | `validator-only signal` |
| All EP5-7 rescue rounds trace to 한미증권 blueprint error | `confirmed primary cause` (of rescue rounds) |
| EP7 R2 POV violation is a pure Stage 4 LLM generation error | `confirmed secondary amplifier` |

## 6. Lane Answers

### Can this lane explain a real EP5-EP7 rescue round by itself: **yes**

The sink reconciliation reveals that the **rescue round count** itself is uncertain across sinks. Console shows 8 total rounds (3+2+3), JSONL validation events show 7 (3+3+1), and episode_production pathology shows 4 (2+2+0). The primary content cause of rescue rounds (한미증권 location error) is visible in console, but the observability infrastructure cannot accurately replay the retry history from JSONL alone.

### Does this lane justify a bounded next execution wave: **yes**

Two bounded waves are justified:
1. **Sink recording fix**: EP7 complete JSONL blackout + EP6 R2 three-way verdict disagreement + EP5 score recording semantics — these are recording infrastructure bugs that degrade post-run audit capability
2. **Score semantics normalization**: The three sinks record three different scores for the same round — operators cannot trust any single JSONL field to represent the Director's verdict score

### Dominant seam in this lane: **sink**

The primary findings are sink-layer mismatches and recording gaps, not Stage 3 or Stage 4 content errors. The content-level root cause (한미증권 blueprint) is visible in console but would need T3/T6 lanes to fully diagnose.

### Is the likely owner Stage 3 / Stage 4 / sink-reconciliation / validator / mixed: **sink-reconciliation**

The EP7 blackout and EP6 three-way disagreement are pure sink-reconciliation issues. The content-level rescue cause (blueprint location error) is Stage 3 → Stage 4 propagation, but that belongs to T3/T4 lanes. This lane's unique contribution is proving the sink infrastructure cannot reliably replay the production history.
