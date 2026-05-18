# Firefly-Side Research Dry Run Plan Audit v1

Date: 2026-05-17
Status: adversarial audit complete
Target: `125_firefly_side_research_dryrun_plan_v1.md`
Work ID: `chaebol3_sector_rotation_successor`
Issue: #157

## 0. Verdict

`PASS_WITH_WATCH_FOR_FILE_ONLY_EP007_DRYRUN`

The plan is correctly bounded.

It does not authorize:

- B11-B20;
- TR70;
- BI;
- Firefly DB/project mutation;
- `manuscript save`;
- production manuscript save;
- production S4 prompt change.

It does authorize:

- one file-only EP007 buyer-desk dry run;
- a post-write micro-audit;
- patch/re-audit if thesis-clean or checklist-like residue appears.

## 1. Hard Checks

| Check | Verdict | Reason |
|---|---|---|
| honors Firefly harness distinction | PASS | It labels output `draft_not_db_saved` and avoids completion/save claims. |
| avoids DB mutation | PASS | Explicitly forbids `manuscript save` and Firefly project mutation. |
| uses current material evidence | PASS | Anchors on `116`, `118/121`, `122/124`. |
| avoids long research prompt leakage | PASS | Blocks `114/115`, full audit prose, mechanism labels. |
| picks reasonable next surface | PASS | EP007 buyer desk tests commercial outside actor after product-hand and finance/file surfaces. |
| preserves S2-S3-S4 objective | PASS | This is S4 context compatibility, not a replacement pipeline. |

## 2. Adversarial Concerns

### Concern 1 - Is this still too synthetic?

Verdict: `WATCH`

The plan is artificial by design. That is acceptable because it is a file-only dry run.

The actual EP007 dry run must not sound like it is answering audit questions. The buyer should protect shelf space, return calls, and delivery penalty as office/work behavior.

### Concern 2 - Does this bypass Firefly?

Verdict: `NO`

It avoids DB and production S4 prompts on purpose. This is the correct step before touching Firefly runtime surfaces.

### Concern 3 - Should we instead generate B11-B20?

Verdict: `NO`

Two smoke tests prove `116` is promising. They do not prove range multiplication. The next bottleneck is integration discipline.

## 3. Decision

Next unit:

`Run file-only EP007 buyer-desk dry run from 116, draft_not_db_saved, then post-write micro-audit.`

Required audit focus:

- buyer has a practical reason to resist;
- Doyun reduces exposure;
- sample box remains beside phone/return ledger;
- no front-display victory;
- no thesis-clean explanation lines;
- no DB/project mutation.

Stoplines remain:

- no B11-B20;
- no TR70;
- no BI;
- no Firefly DB/project mutation;
- no production manuscript save.
