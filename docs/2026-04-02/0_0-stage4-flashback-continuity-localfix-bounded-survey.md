Date: 2026-04-02
Status: final-bounded-survey
Canonical Path: `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-bounded-survey.md`
Baseline Commit: `5ef5f7ab2f2bbd36c2e8168cfd6d9b096caadc0f`
Baseline Dirty Summary: `dirty: 0_temp.txt modified, 0_tempdd.tz untracked`
Source Runtime Watch:
- `0_temp.txt`
Source SSOT / Prior Audits:
- `docs/2026-04-02/0_0-stage4-consumer-contract-normalization-remediation-execution-ssot.md`
- `docs/2026-04-01/0_0-stage4-ep2-advisory-escalation-loop-remediation-execution-ssot.md`
- `docs/2026-04-02/0_0-stage4-npcdrift-relation-tag-semantic-localfix-remediation-execution-ssot.md`
Evidence Artifacts:
- `docs/2026-04-02/0_0-stage4-flashback-continuity-localfix-evidence.json`
Mode: survey only, read-only only

---

## Answer First

The current fresh-run ep2 blocker is no longer the old device-type `FlashbackVerifier` false positive and no longer the contaminated `Stage4-only` canary interpretation.

It is a narrower `Stage4` seam:

1. the fresh run is surfacing real flashback continuity contradictions against prior manuscript truth, and
2. Stage4 cannot convert those advisory-only flashback findings into a bounded local `fix_pack`.

In short:

`real flashback contradiction -> freeform advisory payload -> strong advisory escalation -> non-ready fix_pack -> forced REJECT`

This is a bounded `Stage4 flashback continuity local-fix-contract` problem.

---

## Hard Conclusions

### 1. The live fresh-run evidence is dominated by Flashback continuity contradiction, not by the old phone/button false positive

`0_temp.txt` shows that round 7 advisory output is a series of concrete continuity contradictions:

- prior truth says the protagonist left the study and used the phone in the corridor
- candidates instead describe stopping, turning back, facing the father directly, or walking toward the study

The relevant watch region is `0_temp.txt` lines 865-876 and again 904-925.

This is not the earlier "screen button implies smartphone" over-inference class. It is a substantive prior-truth contradiction class.

### 2. The prior manuscript and current blueprint support that this is a real continuity comparison, not arbitrary detector noise

`projects/0_0/drafts/ep_0001.txt` lines 91-99 place the authoritative prior scene in the corridor after leaving the study and starting the phone call there.

`projects/0_0/plans/blueprints/blueprint_0002.txt` line 7 preserves that immediate carryover: phone call in the corridor after leaving the study.

So the Flashback advisory is comparing candidate flashback scenes against a real authoritative baseline.

### 3. The direct runtime failure still occurs at the Stage4 fix-contract gate

`0_temp.txt` lines 886-893 show:

- Director PASS
- `gate_basis = strong_advisory_escalation_non_local_fix`
- forced downgrade to REJECT

`0_temp.txt` line 931 then shows:

- `[TF-PATCH-GATE] non-ready fix_pack -> patch 차단, rewrite 경로 사용`

So Stage4 is not failing because it cannot detect the problem. It is failing because it cannot operationalize the problem into a local repair contract.

### 4. FlashbackVerifier currently emits only flat advisory payloads

`modules/core/flashback_verifier.py` returns flat structures:

- `marker`
- `issue`
- `referenced_context`
- `severity`
- `check`
- `text`

There is no structured metadata for:

- contradiction subtype
- local-fix eligibility
- patch anchor
- bounded target kind

That makes later Stage4 local-fix synthesis guesswork.

### 5. `_advisory_flashback()` discards structured repairability and keeps only freeform text

`modules/core/stage4_interview_round.py` `_advisory_flashback()` currently:

- runs `FlashbackVerifier`
- appends `_cand_idx`
- flattens each item into display lines for Director

Unlike the newer `NpcDrift` path, it does not persist structured flashback metadata into `_last_advisory_metadata`.

So even if the detector had enough semantic detail, Stage4 would not currently retain it for fix-pack synthesis.

### 6. Existing strong-advisory backfill does not cover flashback from zero

`_backfill_strong_advisory_fix_pack()` in `modules/core/stage4_interview_round.py` already has:

- generic triggered-by templates
- a concrete `NpcDrift relation-tag` zero-to-local synthesis path

But there is no Flashback-specific zero-to-local synthesis path.

That is why the live chain remains:

`Flashback advisory -> strong advisory escalation -> missing/non-ready local fix contract -> REJECT`

---

## Medium-Confidence Conclusions

### 1. This seam is narrower than a full FlashbackVerifier redesign

The current failure does not require weakening Flashback globally.

The bounded missing piece is:

- structured flashback contradiction metadata
- plus a Flashback-specific local-fix synthesis bridge for clearly local continuity contradictions

### 2. The safe bounded target is subtype-aware local repair, not broad rewrite suppression

The current contradictions mostly live in local continuity language:

- facing / relative position
- movement / stop-vs-continue
- location / destination
- dialogue content

These are usually representable as `local_phrase` or `local_sentence` repair targets, even if the final round may still choose rewrite later.

### 3. The prior `NpcDrift` child lane remains valid substrate, but it is no longer the best explanation of the current fresh run

`NpcDrift relation_to_protag` was isolated by a contaminated `Stage4-only` canary and remains a real Stage4 debt family.

But the current fresh full run is higher-authority evidence, and it points first to `Flashback continuity local-fix synthesis`.

---

## Open Questions

1. Should FlashbackVerifier explicitly classify contradiction subtype values such as `movement`, `location`, `facing`, `dialogue`, and `timeline`?
2. Should Flashback local-fix synthesis require an explicit `local_fixable=true` detector flag, or can Stage4 derive local repairability from subtype alone?
3. Should some flashback contradictions still hard-fail as rewrite-only, for example if a whole flashback scene premise is inverted rather than one sentence drifting?

---

## Scope Judgment

This is not a Stage2 issue.

This is not primarily a Stage3 issue.

This is not primarily the already-fixed device-type Flashback false positive seam.

This is a bounded `Stage4 flashback continuity local-fix contract` seam.

---

## Next Action

The next bounded wave should be:

`0_0-stage4-flashback-continuity-localfix-remediation`

with scope limited to:

1. structured FlashbackVerifier contradiction metadata
2. `_advisory_flashback()` metadata persistence
3. Flashback-specific zero-to-local fix-pack synthesis for clearly local continuity contradiction cases

---

## Stop

survey-only complete; code realization deferred to the paired execution SSOT in the same turn

---

## 3-Pass Audit Record

Pass 1. Structure and scope
- stayed bounded to the fresh-run ep2 blocker
- separated this seam from the older Flashback false-positive lane
- kept Stage2/3 reopen and broad Flashback redesign out of scope

Pass 2. Evidence and consistency
- live watch evidence from `0_temp.txt` matches the Stage4 gate/fix-pack failure chain
- artifact truth from `ep_0001.txt` and `blueprint_0002.txt` supports that the contradiction is real, not arbitrary detector noise
- code findings align with `flashback_verifier.py` and `stage4_interview_round.py`

Pass 3. Execution and readability
- next action is explicit and bounded
- operator consequence is clear: add structured flashback metadata plus local-fix synthesis
- no premature runtime-closure claim is made

Confidence: 96%
