Date: 2026-03-24
Status: final
Document Type: survey report (T9 lane — LLM I/O / Retrieval Trace)
Canonical Path: `docs/2026-03-24/opus-residual/t9-llm-io-retrieval-trace.md`
Temp Mirror Path: none (lane survey, not execution SSOT)
Source Survey Docs:
- `docs/2026-03-24/stage2-stage3-residual-leakage-resurvey-10terminal-master-order.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-expanded-survey-report.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave1-execution-ssot.md`
- `docs/2026-03-24/stage2-stage3-episode-boundary-wave2-survey-report.md`
Evidence Artifacts:
- `projects/00_001/logs/session/llm_io.jsonl` (368 entries, 12.8MB — old run)
- `projects/00_0324/logs/session/llm_io.jsonl` (114 entries, 4.3MB — fresh run)
- `projects/00_001/logs/episode_production.jsonl` (27 lines — old run)
- `projects/00_0324/logs/episode_production.jsonl` (6 lines — fresh run)
- `modules/domain/agents/blueprint_ensemble.py:842-867` (live prompt path)
- `modules/domain/agents/blueprint_constraint_compiler.py:119-174` (dead code path)
- `modules/domain/agents/blueprint_constraint_compiler.py:312-373` (stop line extraction)
- `docs/mmmm/T10-blueprint-generation-validation-survey.md:96-108` (prior dead-code finding)
Commit State:
- Baseline Commit: `529869adddb35c93c3ec557aeaed665de168daef`
- Baseline Dirty Summary: `dirty workspace; Wave 1 closed, Wave 2 survey finalized, fresh live-run evidence in docs/2026-03-24/console.txt and projects/00_0324/logs/*`

---

# T9. LLM I/O / Retrieval Trace — Residual Leakage Re-Survey

## 1. Executive Summary

Direct comparison of the LLM prompts sent to the BlueprintEnsembleGenerator in the old run (00_001) vs the fresh run (00_0324) reveals:

- **Wave 1 `state_changes` filter: WORKING.** EP1 prompts no longer contain future-episode items (법인 인감도장, OTP).
- **Wave 1 treatment block quarantine: WORKING.** Event fields (event_villain, solution) are stripped from the Arc overview section.
- **Wave 1 stop line expansion: APPLIED TO DEAD CODE.** The `compile_to_prompt()` method in `blueprint_constraint_compiler.py` correctly renders all future episodes, but this method is never called in production. The actual prompt path (`blueprint_ensemble.py:_format_constraints()`) only renders the next-episode stop line and silently drops `future_eps`.

**Residual culprit candidate:** `blueprint_ensemble.py:864-867` — the live prompt formatter that builds `[Stop Line]` for the LLM only enumerates `ep+1` content, ignoring the `future_eps` list collected by Wave 1's `_extract_stop_line()`.

**Practical impact in the fresh run:** zero rejections (0/3 episodes). The state_changes filter and treatment block quarantine were sufficient alone. But the stop line gap remains a latent defense-in-depth failure.

---

## 2. Included Coverage / Exclusions

### Covered
- Full comparison of BlueprintEnsembleGenerator prompts between 00_001 (old) and 00_0324 (fresh) runs
- Contamination marker analysis across all 62 (old) and 18 (fresh) blueprint prompt entries
- Prompt size growth patterns across episodes
- Stop line rendering path verification: constraint compiler vs blueprint ensemble
- Production outcome comparison (rejection rates)
- Verification of prior T10-TF-004 finding (compile_to_prompt dead code)

### Excluded
- Stage 4 ChiefWriter/Director prompts (different lane)
- Retrieval/vector memory context injection (no evidence of retrieval contamination in Stage 3 prompts)
- Context caching behavior (Gemini API caching is per-agent, not a contamination vector)
- Stage 2 ArcEnsembleGenerator prompts (covered by T2/T3)

---

## 3. Key Evidence

### E1. Old Run EP1 Prompt Contamination (00_001, L9, prompt=8666c)

```
[상태 변경 요약]
  🤝 관계변화: 한정호 기대 제로→의외라는 시선
  🤝 관계변화: 한태준 (큰형) 무관심→무관심 유지
  📦 아이템: SW인베스트먼트 법인 인감도장 (획득)    ← EP4 item
  📦 아이템: 20억 예치 법인 계좌 OTP (획득)        ← EP4 item

[Stop Line]
  다음 화 내용 금지: 아버지 한정호의 서재로 호출됨    ← EP2 only
```

**Verdict:** EP4 items leaked into EP1 via unfiltered `state_changes`. Stop line only blocked EP2.

### E2. Fresh Run EP1 Prompt — Wave 1 Working (00_0324, L9, prompt=7455c)

```
[상태 변경 요약]
  🤝 관계변화: 한정호 (아버지) 귀여운 막내, 기대 제로→의외라는 시선
  🤝 관계변화: 한태준 (큰형) 무관심→무관심 유지
  🤝 관계변화: 한태민 (둘째형) 무관심→무관심 유지
                                                     ← NO future items

[Stop Line]
  다음 화 내용 금지: 서울 성북동 본가 저택 다이닝룸    ← Still EP2 only
```

**Verdict:** `state_changes` filter is working — no future items. But stop line still only blocks EP2.

### E3. Stop Line Dead Code Path

- `blueprint_constraint_compiler.py:119` — `compile_to_prompt()` correctly renders all future episodes with blanket prohibition at lines 156-174
- `blueprint_constraint_compiler.py:312-373` — `_extract_stop_line()` correctly collects `future_eps` for ep+2+
- BUT per prior finding T10-TF-004 (`docs/mmmm/T10-blueprint-generation-validation-survey.md:96-108`): `compile_to_prompt()` is **dead code in production**
- Production path: `blueprint_ensemble.py:264` calls `self._format_constraints()` at line 842
- `blueprint_ensemble.py:864-867`:
  ```python
  stop_line = constraint_block.get("stop_line", {})
  if isinstance(stop_line, dict) and stop_line.get("content"):
      lines.append("\n[Stop Line]")
      lines.append(f"  다음 화 내용 금지: {_fit_compact_context(stop_line['content'], 150)}")
  ```
  This renders only `stop_line["content"]` (next-ep) and ignores `stop_line["future_eps"]`.

**Verdict:** Wave 1's stop line expansion was applied to dead code. The live prompt path still only blocks ep+1.

### E4. Fresh Run Blueprint EP1 — Overconsumption Fixed

Old run EP1 `integrated_scenario` consumed: "SW인베스트먼트 법인 인감도장과 20억 예치 법인 계좌 OTP" — EP4 content.

Fresh run EP1 `integrated_scenario` stays within EP1 scope: waking up, remembering future data, calculating funds, ending at father's summons. Equipment = ["구형 애니콜 휴대폰", "암호화된 가죽 수첩"] — no future items.

**Verdict:** The dominant leakage vector (`state_changes`) being closed was sufficient to prevent overconsumption even without the stop line expansion.

### E5. Prompt Size Growth Comparison

| Episode | Old Run (avg chars) | Fresh Run (avg chars) |
|---------|--------------------:|----------------------:|
| EP1     |              8,663  |                7,452  |
| EP2     |              6,895  |               10,379  |
| EP3     |              8,665  |               10,787  |
| EP4     |              8,911  |               11,499  |
| EP5     |              9,814  |               12,351  |
| EP6     |                 —   |               38,410  |
| EP15    |             29,889  |                  —    |
| EP19    |             42,681  |                  —    |

Fresh run EP1 is ~14% smaller (Wave 1 removed some contamination content). Later episodes grow as continuity context accumulates. EP6 (Arc 2 start) jumps to 38K due to accumulated Arc 1 history.

### E6. Production Outcome Comparison

| Metric | Old Run (00_001) | Fresh Run (00_0324) |
|--------|-----------------|---------------------|
| Total episodes | 7 (Arc 1) | 3 (Arc 1 partial) |
| Total attempts | 17 | 3 |
| Rejections | 7 (41%) | 0 (0%) |
| EP1 result | PASS R0 (s96) | PASS R0 (s95) |
| EP3 result | REJECT → PASS R2 | PASS R0 (s95) |
| EP4 result | REJECT (s30) → PASS R2 | PASS R0 (s95) |

All 7 rejections in the old run traced to Wave 1 leakage cascade. Zero rejections in the fresh run.

---

## 4. Findings Ranked

| # | Finding | Classification | Can Explain EP1 Overconsumption? | Can Explain EP3/EP4 Replay? | Fixable in Bounded Wave? |
|---|---------|---------------|----------------------------------|----------------------------|-|
| F1 | `blueprint_ensemble.py:864-867` drops `future_eps` from stop line | confirmed residual leakage | No alone (stop line is defensive, not primary) | No alone | Yes — ~5 lines |
| F2 | `compile_to_prompt()` is dead code; Wave 1 stop line fix applied there | confirmed residual leakage (dead code target) | No | No | Yes — migrate rendering or wire live path |
| F3 | `genre_ext` arc-level capital metadata in EP1 prompt | secondary amplifier | No alone | No | Maybe — requires genre_ext episode filtering |
| F4 | Prompt size grows unboundedly with episode count | follow-up only | No | No | Requires context budget design |

---

## 5. Cleared Non-Culprits

| Surface | Status | Evidence |
|---------|--------|----------|
| `state_changes` episode filter | **working** | Fresh run EP1 prompt has no future items (E2) |
| Treatment block quarantine | **working** | Fresh run EP1 has `[Arc 개요]` with event fields stripped (E2) |
| `semantic_carryover` foreshadow | **clean (by design)** | Arc-level foreshadow descriptions, not episode content |
| Retrieval / vector memory | **not a contamination vector** | No evidence of retrieval injecting future-episode content into Stage 3 prompts |
| Context caching (Gemini API) | **not applicable** | Caching is per-agent, not a content contamination mechanism |
| Continuity pins | **clean** | Only reference prior/current episode data |

---

## 6. Residual Culprit Candidate

**`blueprint_ensemble.py:_format_constraints()` stop line rendering gap**

The Wave 1 constraint compiler correctly collects all future episode stop lines into `future_eps`. The Wave 1 `compile_to_prompt()` correctly renders them with a blanket prohibition. But:

1. `compile_to_prompt()` is dead code — never called in production
2. The live path (`blueprint_ensemble.py:_format_constraints()`) only renders `stop_line["content"]` (next-ep) and ignores `stop_line["future_eps"]`
3. The LLM prompt therefore has `[Stop Line]` blocking only ep+1, not ep+2+

**Why this didn't cause failures in the fresh run:**
- The dominant leakage vector (`state_changes`) is now closed
- The secondary vector (treatment block events) is now quarantined
- Without future content in the prompt, the stop line gap is moot — there's nothing to stop because the contamination was already removed upstream

**Why this is still a residual risk:**
- The stop line is a defense-in-depth mechanism
- If a new feature or code change reintroduces future content through another channel (e.g., new advisory, genre extension, or world state update), the stop line won't catch it
- The gap is between "data computed correctly" and "data rendered in prompt" — a classic integration seam

---

## 7. Next-Scope Recommendation

**Bounded fix: wire `future_eps` into `blueprint_ensemble.py:_format_constraints()`**

Scope:
- `modules/domain/agents/blueprint_ensemble.py:864-867`
- Add rendering of `stop_line.get("future_eps", [])` after the next-ep line
- Add blanket prohibition line matching the constraint compiler's format
- Estimated: ~8 lines of code

Optional cleanup:
- Either remove `compile_to_prompt()` dead code or add a deprecation comment
- This is cosmetic — the fix should target the live path

Test:
- Verify that `[Stop Line]` in the LLM prompt includes future episode content
- Run `tests/test_stage2_stage3_episode_boundary_guardrail.py`
- Run `tests/test_blueprint_patch_mode.py`

---

## 8. Confidence and Limits

- **Confidence: 96%**
- **Basis:**
  - Direct prompt comparison between old and fresh runs confirms Wave 1 fixes are working in the live path
  - The stop line dead-code finding is confirmed by prior T10-TF-004 survey and verified by grep (0 production callers of `compile_to_prompt`)
  - The fresh run's zero-rejection outcome demonstrates that `state_changes` filter + treatment block quarantine are the dominant fixes
  - The 4% uncertainty is in whether the `genre_ext` capital metadata is a meaningful amplifier or fully benign
- **Limits:**
  - Fresh run only covered 3 episodes (Arc 1 partial) — longer runs may reveal additional patterns
  - No Stage 4 prompt analysis (different lane)
  - No context budget or truncation mechanism was found in the Stage 3 blueprint path; prompt growth is unbounded

### Mandatory Conclusions

- Can this seam alone explain ep1 overconsumption: **no** — the stop line gap is defensive, not the primary leakage source
- Can this seam explain ep3/ep4 continuity-firewall replay: **no** — the replay was caused by `state_changes` contamination, not stop line undercoverage
- Can this seam be fixed in a bounded next wave: **yes** — ~8 lines in `blueprint_ensemble.py:_format_constraints()`

---

## 9. 3-Pass Audit Record

- Pass 1
  - confirmed this is a survey report anchored to LLM I/O evidence
  - confirmed scope matches T9 lane definition (LLM I/O, retrieval trace, context budget, prompt trace)
  - confirmed the stop line dead-code finding is verified against prior survey T10-TF-004
- Pass 2
  - confirmed all prompt excerpts are sourced from actual llm_io.jsonl entries with line/position references
  - confirmed the fresh run evidence is from project 00_0324 (post-Wave-1), not 00_001 (pre-Wave-1)
  - confirmed the production outcome comparison uses episode_production.jsonl from both projects
  - confirmed no overclaiming: the stop line gap is classified as "residual" not "dominant"
- Pass 3
  - confirmed the recommendation is bounded and actionable (~8 lines)
  - confirmed the finding is grounded in code path analysis, not speculation
  - confirmed the mandatory conclusion lines are consistent with the evidence
