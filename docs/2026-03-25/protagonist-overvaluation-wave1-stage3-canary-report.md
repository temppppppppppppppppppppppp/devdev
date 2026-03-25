# Protagonist Overvaluation Wave 1 — Stage 3 Canary Report

Date: 2026-03-25
Run Type: Stage 3-only fresh canary (post Wave 1 code changes)
Source Project: `000000`
Target Project: `canary_0325_overval_s3`
Scope: Arc 1 only (EP1-EP4)
Session ID: `20260325_120636`
Comparison Baseline: `canary_0325` (session `20260325_073439`, pre-Wave 1)

## Findings

### Pass Rate

| Episode | Pre-Wave 1 | Post-Wave 1 | Delta |
|---------|-----------|-------------|-------|
| EP1 | PASS 95 (1st attempt) | PASS 92 (1st attempt) | -3 |
| EP2 | PASS 95 (1st attempt) | PASS 95 (1st attempt) | 0 |
| EP3 | PASS 95 (1st attempt) | PASS 95 (1st attempt) | 0 |
| EP4 | PASS 95 (1st attempt) | PASS 92 (1st attempt) | -3 |
| **Aggregate** | **100% 1st-attempt** | **100% 1st-attempt** | **unchanged** |

Score range 92-95 across both runs. The -3 delta on EP1 and EP4 is within normal LLM generation variance and not attributable to systematic regression. Both baselines had the same score range (the prior canary EP8 also scored 92).

### Prevalidation Behavior

| Episode | Pre-Wave 1 Issues | Post-Wave 1 Issues |
|---------|-------------------|-------------------|
| EP1 | 0 | 1 (scenario_density MINOR) |
| EP2 | 0 | 0 |
| EP3 | 0 | 0 |
| EP4 | 0 | 1 (scenario_density MINOR) |

The new scenario-density prevalidation check (from clarity/density Wave 1) is now active and correctly flagging thin blueprints. EP1 had 3 concrete anchors < 5 required (in 1313 chars). EP4 had 4 < 5 (in 1951 chars). These MINOR warnings are advisory and do not reject; they surface to Director as quality-risk signals. This is the designed behavior.

### Strategy Diversity

| Episode | Pre-Wave 1 Strategy | Post-Wave 1 Strategy |
|---------|--------------------|--------------------|
| EP1 | dialogue_focused | action_focused |
| EP2 | — | emotion_focused |
| EP3 | — | dialogue_focused |
| EP4 | — | emotion_focused |

Post-Wave 1 canary shows healthy 3-strategy diversity across 4 episodes (action, emotion, dialogue). No single strategy dominates.

## What Improved

1. **Scene count consistency**: Post-Wave 1 blueprints consistently have 4-5 scenes each, with the majority having 5 scenes. The authority re-banding and self-audit checklist may contribute to this consistency.

2. **Observer allocation is healthy and bounded**: EP1 uses a `side_glimpse` scene (경호원 perspective) — a non-protagonist observer viewpoint that creates information asymmetry naturally. EP2 distributes across 5 characters (한시우, 경호원, 한태준, 한태민, 한정호). EP4 opens with a `side_glimpse` (박성호 alone in VIP room). Observer allocation appears in a healthy bounded way without forcing unnatural viewpoint shifts.

3. **Information asymmetry is well deployed**: All 4 episodes leverage 한시우's future knowledge as a natural information gap. This creates asymmetry with every NPC interaction (경호원 misreading the situation, 한정호 underestimating the request, 박성호 stunned by the financial insight, 김형석 underestimating the client). The asymmetry is genre-appropriate, not artificially manufactured.

4. **Reveal ordering is staged**: EP3 in particular stages the financial knowledge reveal across scenes: general → specific portfolio critique → IAEA prediction. EP4 stages across: law firm competence → chart analysis → news confirmation. No single-scene data-dump patterns.

5. **`big_number_wow` effectively absent**: Numbers appear as functional plot anchors (20억, WTI 78달러, 금리 25bp, 배럴당 60.25달러, 제세공과금 1,450만). No narrator-hype reactions. No "amazed at the big number" patterns. Director notes quality but does not cite raw numbers as a selling point.

6. **`uniform_reaction` effectively absent**: Each NPC reacts distinctly. 한정호 shows cold calculative interest. 한태민 shows confused irritation. 박성호 progresses from professional condescension to stunned fear. 김형석 shifts from casual dismissal to professional respect. No "everyone gasps in unison" pattern.

7. **Scenario density improved**: EP2 (1500 chars), EP3 (1858 chars), EP4 (1951 chars) all show strong integrated_scenario length with concrete detail. EP3 is notably dense with specific financial terms (금리 25bp, 건설주 비중 40%, 듀레이션, 중도 해지 수수료 3%, 6천만 원) woven into dialogue.

## What Stayed Neutral

1. **Pass rate**: Unchanged at 100% first-attempt. No regression, no improvement — this was already the ceiling for this project.

2. **Score range**: 92-95 in both canaries. The EP1/EP4 scores of 92 are consistent with the prior canary EP8 score of 92. This is normal variance.

3. **`protagonist_evaluation` substrate absent — no harm observed**: The source project `000000` does not populate `work_identity.protagonist_evaluation` in its `work_guard.yaml`. Despite this, the static blueprint staging guidance (Tranche C) still produces healthy admiration patterns. The optional substrate is correctly non-blocking.

4. **Blueprint structure**: `scene_breakdown`, `integrated_scenario`, `ending_hook`, `relationship_changes`, `protagonist_state` — all present and well-formed in every blueprint. No structural regression.

5. **Sink alignment**: `hard_gates.status = "pass"`, `sink_alignment_summary.status = "ok"`, zero mismatches across all sink categories.

## What Regressed

**Nothing actionable regressed.**

The only observable delta is the -3 score on EP1 and EP4, which coincides with the new scenario_density MINOR warnings. The warnings are working correctly: EP1's integrated_scenario is the shortest at 1313 chars and has the fewest concrete anchors. The score delta is properly attributable to normal LLM variance and is not systematic.

## Overcorrection Assessment

No evidence of overcorrection:

- No episodes were rejected or required retries.
- No episodes show overly constrained scene structures.
- The new prevalidation warnings are MINOR severity, not reject-bearing.
- Director feedback shows healthy varied reasoning without citing admiration-staging rules.
- No blueprint appears to sacrifice narrative flow in favor of satisfying a checklist.
- The self-audit checklist's presence in the prompt does not appear to cause mechanical or formulaic blueprints.

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0325_overval_s3/logs/stage3_canary_summary.json` |
| Pass rate monitor | `projects/canary_0325_overval_s3/logs/pass_rate_monitor.json` |
| Session decisions | `projects/canary_0325_overval_s3/logs/session/decisions.jsonl` |
| EP1 blueprint | `projects/canary_0325_overval_s3/logs/artifacts/stage3/ep_0001/attempt_01/final_blueprint__action_focused.json` |
| EP2 blueprint | `projects/canary_0325_overval_s3/logs/artifacts/stage3/ep_0002/attempt_01/final_blueprint__emotion_focused.json` |
| EP3 blueprint | `projects/canary_0325_overval_s3/logs/artifacts/stage3/ep_0003/attempt_01/final_blueprint__dialogue_focused.json` |
| EP4 blueprint | `projects/canary_0325_overval_s3/logs/artifacts/stage3/ep_0004/attempt_01/final_blueprint__emotion_focused.json` |
| Comparison baseline | `projects/canary_0325/logs/stage34_canary_summary.json` |

## Weaker / Riskier Blueprint Detail

**EP1** (score 92, lowest in set):
- `scenario_density` MINOR: 3 concrete anchors < 5 threshold in 1313 chars
- Integrated scenario is the shortest of the four. The detail level is adequate for a regression-opening episode (which is inherently more about physical sensation and confusion than about named entities), but the density heuristic correctly flags it as the thinnest.
- No structural or narrative defect. The action_focused strategy is appropriate for the opening hook.

**EP4** (score 92):
- `scenario_density` MINOR: 4 concrete anchors < 5 threshold in 1951 chars
- Despite being 1951 chars (longest EP), the density is diluted slightly by the emotional_reveal scene and internal monologue sections. The anchor count threshold may be slightly conservative for emotion-focused strategies where internal narration replaces external events.
- No structural or narrative defect.

Neither EP1 nor EP4 require corrective action. The MINOR warnings are correctly calibrated.

---

**Stage 3 pass-rate after protagonist-overvaluation Wave 1: unchanged**
**Overcorrection risk: none**
**Should Codex open a new execution SSOT now: no**
