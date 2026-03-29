## Stage4 Scope Sink Semantics Full Survey

Date: 2026-03-29
Status: final (3-pass audited)
Track: system
Topic Slug: stage4-scope-sink-semantics

Commit State:
- Baseline Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Baseline Dirty Summary: `dirty tracked drift in stage4/runtime/tests, provider/runtime code, temp queue artifacts, canary outputs, and unrelated narrative assets`
- Resume Commit: `95d77ec9ac315c31397d3254adc4d60345685fcc`
- Resume Drift Summary: `same commit; retry-loop-compression live validation completed and now provides the newest control evidence for sink semantics`

---

### 1. Scope and Intent

This survey answers one concrete question:

> Across Stage 4 runtime sinks, what does each field actually mean today for authoritative fix scope, derived retry scope, repair scope, conflict carryover, and rationale preservation, and where do operators currently risk reading different truths as if they were the same field?

The purpose is not to redesign Stage 4 broadly.
The purpose is to freeze the current semantics before another wave adds more additive fields and makes post-mortem reading harder.

Included surfaces:

- `modules/domain/agents/director_ensemble.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/stage4_reject_runtime.py`
- `modules/core/stage4_outcome_runtime.py`
- `modules/core/stage4_retry_runtime.py`
- `modules/domain/agents/chief_writer.py`
- `modules/core/session_logger.py`
- `modules/core/db_manager.py`
- live sinks and canary evidence:
  - `projects/canary_0328_gemini_direct_fixscope_check/logs/`
  - `projects/canary_0328_sink_verify_micro/logs/`
  - `projects/canary_0329_feedback_windowing_check/logs/`
  - `projects/canary_0329_retry_loop_compression_check/logs/`

Excluded:

- provider-default redesign
- fallback observability redesign
- broad Stage 4 policy changes
- patch-lane redesign
- DB schema migration
- code changes in this survey

---

### 2. Evidence Sources

| Source | Type | Use |
| --- | --- | --- |
| [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py) | Code | authoritative scope extraction, normalization, repair scope derivation |
| [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py) | Code | gate semantics normalization, decisions sink, episode sink, carryover assembly |
| [stage4_reject_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_reject_runtime.py) | Code | runtime widening, reject snapshot carryover, rationale blanking rules |
| [stage4_outcome_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_outcome_runtime.py) | Code | retry pathology payload sink |
| [stage4_retry_runtime.py](C:/Users/User/Desktop/글도비/modules/core/stage4_retry_runtime.py) | Code | lane routing meaning of repair scope |
| [chief_writer.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py) | Code | consumer of `selection_reason`, `open_review`, `conflict_contract`, `reuse_contract` |
| [session_logger.py](C:/Users/User/Desktop/글도비/modules/core/session_logger.py) | Code | `decisions.jsonl` write path |
| [db_manager.py](C:/Users/User/Desktop/글도비/modules/core/db_manager.py) | Code | `director_selections`, `stage_attempts` persistence shape |
| [canary_0328_gemini_direct_fixscope_check/logs](C:/Users/User/Desktop/글도비/projects/canary_0328_gemini_direct_fixscope_check/logs) | Live evidence | older seam state; no authoritative scope field |
| [canary_0328_sink_verify_micro/logs](C:/Users/User/Desktop/글도비/projects/canary_0328_sink_verify_micro/logs) | Live evidence | first clean proof that `authoritative_fix_scope` reached JSONL sinks |
| [canary_0329_feedback_windowing_check/logs](C:/Users/User/Desktop/글도비/projects/canary_0329_feedback_windowing_check/logs) | Live evidence | richest pre-compression example of sink divergence |
| [canary_0329_retry_loop_compression_check/logs](C:/Users/User/Desktop/글도비/projects/canary_0329_retry_loop_compression_check/logs) | Live evidence | latest control run; proves loop compression worked and high-score rationale preservation now lands |

---

### 3. Field Origin and Ownership Map

#### 3.1 `authoritative_fix_scope`

- Origin: Director-authored scope, normalized from Director output in [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py).
- Meaning: what the Director actually intended before runtime widening, replay handling, or reject-family overrides.
- Owner: Director output only. Runtime may validate it, but should not widen it.
- Current sinks:
  - `decisions.jsonl`
  - `episode_production.jsonl`
  - retry pathology payload
  - JSON blobs inside DB-linked advisory/gate semantics payloads

#### 3.2 `authoritative_fix_scope_violation`

- Origin: runtime validation layer in [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py) and [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py).
- Meaning: Director-supplied authoritative scope was blank or invalid for a verdict that required it.
- Owner: runtime contract checker.
- Current sinks:
  - `decisions.jsonl`
  - some `episode_production.jsonl` entries
  - retry pathology payload
- Note: presence is additive, but not perfectly uniform across all older canaries.

#### 3.3 `fix_scope`

- Origin: initially Director output, but then widened and rewritten by runtime.
- Meaning today: overloaded.
- The same name currently refers to three different layers depending on sink:
  1. Director-origin scope in `director_selections`
  2. runtime-widened scope in `stage_attempts`
  3. carried previous-attempt widened scope in pathology-style snapshots

#### 3.4 `repair_scope`

- Origin: runtime normalization of the effective retry lane.
- Meaning: lane-facing effective scope for retry routing.
- It is not a separate human judgment from the Director. It is the runtime's lane view.
- Problem: its practical meaning is close to widened `fix_scope`, but the name does not say that clearly.

#### 3.5 `selection_reason`

- Origin: Director rationale for why a candidate was selected.
- Meaning: positive or comparative choice rationale.
- Consumer: Chief Writer retry path uses it as preserved guidance.
- Important current fact: after retry-loop-compression landed, high-score downgraded PASS paths now preserve it in live evidence instead of blanking it unconditionally.

#### 3.6 `open_review`

- Origin: Director free-form commentary.
- Meaning: non-binding but useful editorial context.
- Consumer: Chief Writer retry path also reads it.
- Important current fact: same as `selection_reason`; high-score downgraded PASS carryover now preserves it in the latest canary.

#### 3.7 `conflict_contract`

- Origin: runtime-generated structure from `post_select_conflict` evidence in [stage4_interview_round.py](C:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py).
- Meaning: typed statement of the conflict that blocked a near-pass result.
- Consumer: Chief Writer retry prompt formats it into a structured block.
- Persistence today: retry pathology payload only.

#### 3.8 `reuse_contract`

- Origin: runtime-generated carryover contract assembled on the downgraded PASS path.
- Meaning: tells the rewrite path to use stored `best_manuscript` as a baseline and to read the conflict payload.
- Consumer: Chief Writer retry prompt.
- Persistence today: in-memory carryover only; no persistent operator sink.

#### 3.9 `fix_pack`

- Origin: Director-authored structured fix instructions.
- Meaning: patch-ready or rewrite-guiding instruction pack when available.
- Important nuance: `post_select_conflict` still blanks it when the system escalates to full-scope conflict handling, so empty `fix_pack` can mean runtime escalation rather than Director silence.

---

### 4. Sink-by-Sink Semantics Matrix

| Field | `decisions.jsonl` | `episode_production` main entry | `episode_production` pathology | `director_selections` | `stage_attempts` | In-memory carryover |
| --- | --- | --- | --- | --- | --- | --- |
| `authoritative_fix_scope` | Director intent | Director intent | Director intent | indirect only | indirect only | preserved |
| `authoritative_fix_scope_violation` | validation result | partial presence | validation result | indirect only | indirect only | preserved |
| `fix_scope` | mixed; often pre-widened Director-facing copy | not top-level | carried widened scope | Director-origin column | widened scope column | widened or carried |
| `repair_scope` | runtime lane view | runtime lane view | runtime lane view | not direct | indirect JSON | preserved |
| `selection_reason` | Director rationale | Director rationale | not a stable pathology field | direct column | direct column | preserved or blanked by rule |
| `open_review` | Director commentary | Director commentary | preserved when present | not direct | direct column | preserved or blanked by rule |
| `conflict_contract` | absent | absent | present | absent | absent | preserved |
| `reuse_contract` | absent | absent | absent | absent | absent | preserved only |
| `fix_pack` | full dict | full dict | only readiness/reason view | indirect JSON | indirect JSON | preserved or blanked by rule |

Key semantic split:

- `authoritative_fix_scope` = Director-origin truth
- widened `fix_scope` / `repair_scope` = runtime lane truth
- `conflict_contract` / `reuse_contract` = carryover truth

Today those truths are not consistently labeled as distinct layers in operator-facing sinks.

---

### 5. Live Canary Divergence Evidence

#### 5.1 Pre-compression divergence control: feedback-windowing canary

From [canary_0329_feedback_windowing_check/logs](C:/Users/User/Desktop/글도비/projects/canary_0329_feedback_windowing_check/logs), EP3 showed a rich divergence example:

- Director-origin scope remained `inplace`
- runtime lane moved to `full`
- pathology carried prior widened values separately

This produced the exact operator hazard the survey is about:
- same round, three scope-like values
- all correct in isolation
- easy to misread as one inconsistent system

#### 5.2 Latest control canary: retry-loop-compression

From [canary_0329_retry_loop_compression_check/logs/episode_production.jsonl](C:/Users/User/Desktop/글도비/projects/canary_0329_retry_loop_compression_check/logs/episode_production.jsonl):

- EP2 R0: `post_select_conflict`, `authoritative_fix_scope=inplace`, `repair_scope=full`, final verdict downgraded to `REJECT`
- EP2 R0 also preserved `selection_reason` and `open_review` in live evidence
- EP3 compressed from the previous 8-round family into `44 -> 98`, showing that the runtime behavior improved while semantics drift still remains

This matters because the active behavioral bug is mostly improved, so the remaining operator pain is now interpretation, not convergence.

#### 5.3 `reuse_contract` visibility gap

Code and latest canary agree:

- `reuse_contract` affects the retry prompt through [chief_writer.py](C:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py)
- but no persistent sink exposes it

So a later PASS may be caused by reuse, but the operator cannot prove that from logs alone.

#### 5.4 `conflict_contract` one-sided persistence

The latest retry-loop-compression canary is the first one where `conflict_contract` becomes visible in pathology evidence.

But the subsequent resolved PASS entry still does not carry an explicit resolution link.
Operators can see conflict raised, but not cleanly see conflict consumed and resolved.

#### 5.5 Silent blanking remains conditional, not universal

Older evidence justified the claim that `post_select_conflict` blanked rationale silently.
Current evidence is narrower:

- high-score downgraded PASS paths now preserve `selection_reason` and `open_review`
- silent blanking risk still exists for other full-scope reject paths or older rows where the runtime stripped rationale without an explicit marker

So the current defect is not "rationale always disappears."
It is "when rationale is stripped, the sink does not explain why."

---

### 6. Root-Cause Assessment

#### RC-1: `fix_scope` is reused for multiple semantic layers (CRITICAL)

Direct proof from code and canaries shows the same name means:

- Director-origin scope in one sink
- widened runtime scope in another
- carried prior-scope snapshot in pathology payloads

This is the highest-risk misread because the field name suggests one truth while the system emits three.

#### RC-2: `repair_scope` is effectively the runtime lane view, but the contract is undocumented (HIGH)

`repair_scope` is the effective retry lane indicator.
In practice it is the value operators should use to understand what the runtime actually did.
But the system does not explicitly label it as "runtime lane truth," so readers often compare it to `fix_scope` as if both were the same semantic layer.

#### RC-3: `authoritative_fix_scope` solved part of the old problem but now coexists with untagged legacy fields (MODERATE)

This was the correct additive move.
But without explicit sink-level origin labels, the system now has more fields and still expects the operator to infer which layer each field belongs to.

#### RC-4: `reuse_contract` remains invisible in persistent sinks (MODERATE)

This is now a pure observability defect.
The latest canary suggests reuse is materially helping convergence, but operators cannot see it directly in persistent evidence.

#### RC-5: `conflict_contract` is persisted only on the problem side, not the resolution side (MODERATE)

The sink shows conflict creation but not clean resolution lineage.
That limits traceability for near-pass recovery.

#### RC-6: rationale elision is unlabeled when it occurs (LOW-MODERATE)

This is no longer the older broad defect.
It is now a narrower residual issue:
- some paths still intentionally blank rationale
- no additive marker explains that the blank was runtime elision rather than Director omission

---

### 7. Highest-Risk Operator Misreads

1. **Reading widened `fix_scope` as if the Director said it**
   - highest severity
   - confirmed by cross-sink divergence

2. **Treating `repair_scope` and `fix_scope` as synonyms**
   - common and high-impact
   - especially bad in episode-level post-mortems

3. **Assuming empty `fix_pack` means the Director stopped giving instructions**
   - can actually mean runtime escalation blanked it

4. **Assuming missing `reuse_contract` means no manuscript reuse occurred**
   - currently impossible to verify from persistent sinks

5. **Assuming a resolved PASS was unrelated to the earlier `conflict_contract`**
   - because the resolution side is not explicitly linked

6. **Assuming blank rationale means the Director never supplied rationale**
   - now conditional, but still a live interpretability risk without an elision marker

---

### 8. Bounded Remediation Options Ranked

| Rank | Option | Scope | Risk | Notes |
| --- | --- | --- | --- | --- |
| 1 | Add additive `scope_origin` metadata to emitted scope fields | low code | low | strongest direct fix for RC-1 and RC-2 |
| 2 | Freeze the semantics matrix in canonical docs and reference it in future canary/post-mortem work | docs only | zero | prevents repeated human misreads |
| 3 | Persist `reuse_contract` to at least one operator-facing sink | additive | low | closes RC-4 |
| 4 | Persist conflict-resolution linkage on the resolved PASS side | additive | low-moderate | closes RC-5 |
| 5 | Add `rationale_blanked_by` or equivalent marker where runtime strips rationale | additive | low | narrows RC-6 |
| 6 | Rename DB fields or perform schema migration | broad | moderate-high | not justified yet |
| 7 | No code change; rely on reader education only | zero | low immediate, low long-term value | insufficient now that carryover fields are multiplying |

---

### 9. Recommended Bounded Next Step

The safest next move is:

> freeze one explicit semantics matrix in canonical docs and add minimal additive sink metadata so operators can distinguish Director-origin scope, runtime lane scope, and carryover state without renaming schemas or changing runtime behavior

Concretely, that means one bounded wave with these priorities:

1. add `scope_origin` / `scope_layer` style metadata beside emitted scope fields
2. persist `reuse_contract` in at least one operator-facing sink
3. add conflict-resolution linkage on the resolved side
4. add a rationale-elision marker only where stripping still occurs

What this wave should not do:

- rename DB columns
- change retry routing
- reopen provider/fallback work
- change Director sovereignty or lane semantics

---

### 10. Confidence

| Finding | Confidence | Basis |
| --- | --- | --- |
| `fix_scope` semantic overload | direct proof | code path tracing plus canary divergence |
| `repair_scope` as runtime lane truth | direct proof | normalization code and sink outputs |
| `authoritative_fix_scope` additive coexistence problem | direct proof | sink outputs and current code |
| `reuse_contract` persistence gap | direct proof | consumer exists, persistent sink absent |
| `conflict_contract` one-sided persistence | direct proof | pathology sink present, resolved PASS linkage absent |
| rationale-elision risk is now conditional, not universal | direct proof | current canary preserved high-score rationale, code still contains blanking paths |

Estimated confidence: `97%`

---

### 11. 3-Pass Audit Record

#### Pass 1. Structure and Scope

- narrowed the survey to sink semantics, not runtime redesign
- kept included and excluded surfaces explicit
- aligned the document with the current roadmap and canary state
- PASS

#### Pass 2. Evidence and Consistency

- re-audited the draft against the latest retry-loop-compression canary
- corrected the older overstatement about rationale blanking
- confirmed the main live defect has moved from convergence failure to evidence interpretation
- PASS

#### Pass 3. Execution and Readability

- reduced remediation to additive semantics metadata and persistence improvements
- kept schema renames and runtime policy changes out of the recommended move
- made the next execution wave directly derivable from the findings
- PASS
