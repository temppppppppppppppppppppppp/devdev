Date: 2026-03-24
Status: final
Document Type: raw evidence ledger (T3 companion)
Canonical Path: `docs/2026-03-24/opus-residual/t3-stage2-validation-guardrails-evidence.md`

---

# T3 Evidence Ledger: Stage 2 Validation / Guardrails

## E1. Grep confirmation — episode_details not validated

### stage2_validation_pipeline.py (1,407 lines)

```
$ grep -n episode_details modules/core/stage2_validation_pipeline.py
(no matches)
```

### arc_draft_validator.py (1,003 lines)

```
$ grep -n episode_details modules/domain/agents/arc_draft_validator.py
(no matches)
```

### four_phase_arc_generator.py (1,713 lines)

```
$ grep -n episode_details modules/domain/agents/four_phase_arc_generator.py
1000:                    original_details = best_arc.get("episode_details")
1002:                    if original_details and not best_arc.get("episode_details"):
1003:                        best_arc["episode_details"] = original_details
```

Context: These three lines are in the post-generation preservation path. They restore `episode_details` if the field was accidentally dropped during arc processing. This is NOT a validation check.

---

## E2. Required fields list — episode_details absent

`arc_draft_validator.py:204-207`:

```python
required_fields = ["arc_no", "tactical_doc", "joint_docs", "state_constraints", "ep_start", "ep_end"]
required_important = ["ep_count", "items_acquired", "protagonist_items", "grants_received"]
```

`episode_details` is not in either list.

---

## E3. _stage2_flow_guard checks — episode_details not touched

`stage2_validation_pipeline.py:1231-1374`:

Flow guard checks:
1. `beat_sequence` count >= ep_count (L1250-1262)
2. Beat text content normalization (L1264-1285)
3. Per-beat word count (L1287-1325)
4. NarrativeStructureAnalyzer stagnation (L1327-1359)

None of these reads or validates `episode_details`.

---

## E4. _validate_tactical_doc checks — episode_details not touched

`arc_draft_validator.py:580-621`:

Tactical doc validation chain:
1. `_coerce_tactical_doc_value()` — type coercion (L383-404)
2. `_resolve_tactical_doc_expectations()` — ep_count/lengths (L406-416)
3. `_validate_tactical_length()` — total length check (L418-430)
4. `_validate_tactical_episode_layout()` — per-episode sections (L432-465)
5. `_validate_tactical_episode_density()` — dialogue/action/beat count (L467-500)
6. `_validate_tactical_episode_metadata()` — ep_count mismatch + state checkpoints (L502-526)
7. `_validate_tactical_relationship_mentions()` — NPC names in tactical (L547-561)
8. `_validate_tactical_action_density()` — action verb count (L564-578)

Every sub-check reads `tactical_doc` or `state_constraints`. None reads `episode_details`.

---

## E5. Fresh run episode_details content — 00_0324 Arc 1

Source: `projects/00_0324/logs/artifacts/stage2/arc_001/attempt_01/final_arc__creative.json:105-141`

| ep_num | detail_count | details (summary) |
|--------|-------------|-------------------|
| 1 | 2 | 성북동 침실 회귀 자각 / 경제 흐름 수첩 기록 |
| 2 | 2 | 다이닝룸 가족 식사 / 묵묵히 변화 관찰 |
| 3 | 2 | 서재 독대 / 독립 투자사 선언 |
| 4 | 2 | PB센터 VIP룸 / 20억 시드머니 확보 |
| 5 | 2 | 여의도 법인 설립 / WTI 투자 준비 |

Pattern: uniform 2 items/episode, each with location + primary action. Identical density to 00_001.

---

## E6. Fresh run production results

Source: `projects/00_0324/logs/episode_production.jsonl`

| Episode | Attempts | Result | Score | Strategy |
|---------|----------|--------|-------|----------|
| EP 1 | 1 | PASS | 95 | balanced |
| EP 2 | 1 | PASS (via PASS_WITH_FIX → inplace patch) | 92→90 | tension |
| EP 3 | 1 | PASS | 95 | tension |

- Zero rejections in Stage 4 production
- Zero continuity-firewall failures
- EP 2 had a minor item-continuity fix (アイテム acquisition scene added via inplace patch), not a boundary leakage issue

---

## E7. Comparison: 00_001 (pre-Wave-1) vs 00_0324 (post-Wave-1)

| Metric | 00_001 (pre-Wave-1) | 00_0324 (post-Wave-1) |
|--------|---------------------|----------------------|
| episode_details items/ep | 2 | 2 |
| Stage 2 validation guards on episode_details | 0 | 0 |
| Stage 3 blueprint PASS rate | EP1-2 first pass, EP3-7 cascading failures | EP1-4 all first pass |
| Stage 4 total attempts / episodes | 17/7 (7 rejections) | 3/3 (0 rejections) |
| Continuity-firewall triggers | ep3 (20억 replay), ep4 (timeline regression) | none |

**The only variable that changed between runs: Wave 1 leakage seam closure.** Stage 2 validation guardrails were identical in both runs. This proves the validation gap is not the cause.

---

## E8. Stage 2 Director assessment — fresh run

Source: `docs/2026-03-24/console.txt:344-398`

Arc 1, attempt 1: Director PASS, score=100

Director confirmed:
- "논리적 모순이 없으며"
- "5화 분량에 맞게 적절한 페이싱으로 분배"
- "목표 자본금 20억 원 확보 과정도 원작 블록과 완벽히 일치"
- "인과율 밀도와 공간/인물 다양성 기준을 모두 충족"

Director did not flag episode_details sparseness as an issue.

---

## E9. ep_count determination trace — fresh run

Source: `four_phase_arc_generator.py:453-524`

For 00_0324 Arc 1 (treatment block ~800 chars):
- `content_len` ≈ 800 → falls in 500-1500 range
- sentence_count ≈ 8-10 → maps to 3-4화
- Final ep_count: 5 (after tension_level adjustment)
- LLM agreed with 5

This is the same mechanism as 00_001. The heuristic is content-proportional and reasonable.

---

## E10. Guardrail coverage gap matrix

| Validated Surface | `beat_sequence` | `tactical_doc` | `episode_details` | `state_changes` | `joint_docs` |
|-------------------|:-:|:-:|:-:|:-:|:-:|
| Existence check | yes (flow guard) | yes (required field) | **NO** | no (not required) | yes (required field) |
| Length/density | yes (word count) | yes (min chars, balance) | **NO** | no | no |
| Per-episode scoping | no (arc-level) | yes (section extraction) | **NO** | no | no |
| Content quality | yes (stagnation, diversity) | yes (dialogue, action, beat) | **NO** | no | no |
| Cross-field consistency | no | no | **NO** | no | no |

`episode_details` is the only arc payload field with zero validation coverage. All others have at least existence checks.
