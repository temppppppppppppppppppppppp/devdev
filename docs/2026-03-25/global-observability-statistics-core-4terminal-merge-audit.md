# Global Observability + Statistics Core 4-Terminal Merge Audit

Date: 2026-03-25
Status: final (3-pass audited)
Document Type: system-track merge audit
Canonical Path: `docs/2026-03-25/global-observability-statistics-core-4terminal-merge-audit.md`
Source Master Order: `docs/2026-03-25/global-observability-statistics-core-4terminal-master-order.md`
Commit State:
- Baseline Commit: `e3f2771699cb5d596aefaf994a8a177bbbad0a3e`
- Baseline Dirty Summary: `dirty: docs/2026-03-24/console.txt modified, docs/2026-03-25/stage3-latency-efficiency-static-survey.md untracked, no active temp execution queue`
Source Survey Docs:
- `docs/2026-03-25/opus-observability-core/t1-runtime-timing-cost.md`
- `docs/2026-03-25/opus-observability-core/t2-quality-verdict-passrate.md`
- `docs/2026-03-25/opus-observability-core/t3-retry-rescue-asp.md`
- `docs/2026-03-25/opus-observability-core/t4-sink-alignment-instrumentation-ledger.md`
- `docs/2026-03-25/stage3-latency-efficiency-static-survey.md`
Mode: survey merge only
Temp Mirror Path: none

## 1. Findings First

### 1.1 The sink architecture is not the problem

The live system already has a coherent authority contract:
- authoritative sinks are explicitly defined in `modules/api/control_plane_contract.py:41-66`
- sink alignment checking already exists in `modules/core/failure_analyzer.py:1260-1356`
- T4 found no evidence that the system needs sink-topology redesign or dashboard-first redesign

Merge judgment:
- **do not open a sink-architecture redesign wave**
- **do not open a dashboard/UI wave**

The next observability wave, if opened, should be instrumentation-focused, not topology-focused.

### 1.2 Quality / verdict / pass-rate observability is already mature

T2 found that this lane is the most complete of the four:
- authoritative verdict/score sinks already exist across DB and JSONL
- pass-rate computation already exists
- quality signals already have both DB and companion-sink coverage
- the remaining gaps are mostly joins and convenience surfaces, not missing operator truth

Merge judgment:
- **quality/verdict/pass-rate is not the next observability wave**
- defer:
  - cross-stage quality-chain view
  - REJECT-only quality signal enrichment
  - `quality_metrics.jsonl` rotation

### 1.3 The dominant gap is actual token/cost truth plus retry attribution

Three lanes converge here:

- T1: runtime/cost data exists structurally, but token counts are heuristic-estimated rather than API-returned truth
- T3: retry/rescue timing and token cost are not wired through to operator-facing statistics, even though data model fields already exist
- T4: the most meaningful remaining operator blind spot is instrumentation completeness, especially around token/cost truth and retry/rescue evidence

This aligns with the earlier Stage 3 latency survey:
- the dominant runtime source is LLM generation calls, amplified by retries
- optimization decisions need trustworthy token/cost and retry-overhead data first

Merge judgment:
- the next bounded observability candidate is **not** "more sinks"
- it is **actual token/cost propagation + retry/rescue attribution**

### 1.4 A compact observability-core wave is now justified

The lane verdicts were all `no` in isolation, but the merge picture is stronger than any single lane:
- T1 and T4 independently point to the same token/cost truth problem
- T3 independently points to the same retry-attribution problem
- T2 explicitly says its lane is mature and should not be the focus

This is enough to justify one compact merge-level candidate:
- **Observability Core Wave 1**

Scope should remain bounded:
- actual token/cost truth
- per-attempt retry cost/time attribution
- one read-only rescue effectiveness surface

It should not include:
- dashboard redesign
- sink architecture changes
- broad schema redesign
- quality-policy changes

## 2. Lane Rollup

| Lane | Merge Reading | Best Candidate | Merge Status |
|---|---|---|---|
| T1 runtime/timing/cost | strong evidence of instrumentation gap, not sink gap | actual API `usage_metadata` propagation | promote |
| T2 quality/verdict/pass-rate | already mature, no urgent wave | cross-stage quality chain view | defer |
| T3 retry/rescue/ASP | strong evidence of retry attribution gap | wire `duration_ms` / `token_cost` into pass-rate records | promote |
| T4 sink alignment / operator SSOT | architecture coherent, instrumentation gap remains | token/cost completeness verification and fix | promote |

## 3. Recommended Single Next Wave

### Wave Label

`observability-core-wave1-token-cost-retry-attribution`

### Recommended bounded contents

#### Tranche A. Actual token/cost truth propagation

Goal:
- stop relying on heuristic token estimation where the Gemini API already returns usage metadata

Bounded target:
- extract Gemini `usage_metadata` in the LLM client path
- propagate actual token counts into the existing metrics path
- keep existing sinks, pricing logic, and authority contract intact

Expected effect:
- DB `llm_calls`, `cost_log`, canary summaries, and related cost surfaces become materially more trustworthy

#### Tranche B. PassRateMonitor retry attribution wiring

Goal:
- make retry-added time and token/cost visible at attempt level

Bounded target:
- populate the already-existing `duration_ms` and `token_cost` fields at the `PassRateMonitor.record_attempt()` call sites
- do not redesign the pass-rate schema or dashboard

Expected effect:
- operator can answer how much retries cost in wall time and token/cost terms without reconstructing everything manually

#### Tranche C. Read-only rescue effectiveness helper

Goal:
- answer "how much do rescue paths actually save?" without opening a rescue-policy redesign wave

Bounded target:
- add one read-only analyzer surface for rescue effectiveness:
  - rescue attempted
  - rescue succeeded
  - rescue score delta where available

Expected effect:
- ASP / PASS_WITH_FIX / rescue investment decisions become evidence-led rather than intuition-led

## 4. Explicit Defers

Keep these out of Wave 1:
- dashboard redesign
- UI/bridge payload redesign
- per-attempt quality signal DB table
- session lineage cleanup
- patch_strategy normalization
- cross-stage quality-chain view
- REJECT-only quality signal enrichment
- any policy change to retry budgets or ASP behavior

## 5. Why This Wave, Not Another

This merge audit does **not** support these alternatives as the next wave:

- `quality-verdict observability wave`
  - rejected because T2 shows this lane is already mature
- `sink alignment redesign`
  - rejected because T4 shows the authority contract is already coherent
- `dashboard-first wave`
  - rejected because the missing value is in instrumentation truth, not presentation
- `latency optimization wave right now`
  - rejected because optimization still depends on trustworthy token/cost/retry attribution

## 6. Confidence and Limits

Estimated confidence: 96%

Why this clears the 95% merge gate:
- three lanes converge on the same bounded instrumentation gap
- the non-candidate lane (T2) converges in the opposite direction and helps narrow scope cleanly
- the recommended wave changes instrumentation, not policy or authority topology
- the existing authority contract and sink alignment mechanism were directly inspected

Limits:
- this merge did not run a fresh instrumented canary in the same turn
- token-zero evidence was inherited from recent canary/static survey evidence rather than re-collected here
- exact write points for `PassRateMonitor.record_attempt()` were not re-opened in this merge doc; the candidate remains bounded but still needs implementation-level re-audit

## 7. Merge Verdict

- dominant observability gap: **actual token/cost truth plus retry/rescue attribution**
- best bounded next wave: **Observability Core Wave 1**
- quality/verdict/pass-rate lane: **defer**
- sink architecture redesign: **no**
- dashboard redesign: **no**

## 8. Next Action

Codex should open **one** bounded execution SSOT, and only for:
- actual token/cost propagation
- retry attempt duration/token-cost wiring
- read-only rescue effectiveness summary

No temp queue action is taken by this merge audit itself.

---

Dominant observability gap: token-cost truth + retry attribution
Best bounded next wave: observability-core-wave1-token-cost-retry-attribution
Should Codex open an execution SSOT now: yes
