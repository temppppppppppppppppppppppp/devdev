# Firefly Research Handoff: M01-M02 S4 Context Audit v1

Date: 2026-05-17
Status: adversarial audit, research-only
Target: `147_firefly_research_handoff_m01_m02_s4_context_v1.md`
Work ID: `chaebol3_sector_rotation_successor`
Issue: #157
Firefly issues: #31, #13

## 0. Boundary

This audit does not authorize Firefly DB mutation, `manuscript save`, production manuscript save, production S4 prompt/schema/validator change, production BI, production TR70, B3-B10 rewrite, B11-B20, or NAS mutation.

It only judges whether `147` is a safe and useful Firefly-side research handoff.

## 1. Verdict

`PASS_WITH_WATCH_FOR_ONE_FIREFLY_SIDE_RESEARCH_DRYRUN`

`147` is a good handoff because it does not ask Firefly to ingest the whole material stack. It strips the research into:

- one S4 Writer Context payload;
- one writer-visible dispatch;
- one audit checklist;
- explicit stoplines.

This is the correct direction.

## 2. Does It Preserve S2-S3-S4?

Yes.

The handoff explicitly says:

- S2 still owns long-range gate/block order;
- S3 still owns episode/scene skeleton;
- S4 owns body/object/room/prose rendering.

It does not create a new production stage.

The key handoff lesson is specific:

`S2/S3 should pass scene-native payment tokens to S4.`

This is compatible with the existing pipeline.

## 3. Does It Avoid Checklist Slop?

Mostly yes.

Good:

- writer-visible dispatch removes JSON labels;
- it forbids `authority opens`, `competence proved`, `reward paid`;
- it forces object payment before explanation;
- it keeps adults resistant.

Watch:

- The S4 Writer Context payload is still label-heavy, as expected for Director use.
- If someone passes both the full JSON and the entire research context to prose, S4 may over-explain.

Mitigation:

- For prose, pass only section 5 and the stoplines.
- Use section 4 only for Director/pre-draft context fill.

## 4. Does It Serve The Material-Production Goal?

Yes.

The material-production purpose was not to abandon S2-S3-S4. It was to stop S4 from receiving abstract, mushy material.

`147` translates the material into concrete tokens:

- small hand / folder edge / date stamp;
- stamp pad closes;
- approval line stays blank;
- folder pushed away;
- watched telex chair pulled out;
- condition written beside the machine.

These are S4-fuel.

## 5. Remaining Risk

The risk has moved from "material is too abstract" to "Firefly dryrun may still over-explain."

The first Firefly-side dryrun must be judged on:

- chair arriving in scene, not summary;
- Doyun speaking less like a consultant;
- condition sheet carrying meaning;
- no production labels leaking.

If those fail, patch prose line-level. Do not add a new doctrine.

## 6. Decision

Authorized next:

- one Firefly-side research dryrun or issue handoff using `147`;
- or stop and consolidate.

Blocked:

- Firefly DB mutation;
- manuscript save;
- production prompt/schema/validator change;
- production BI/TR70/B11-B20;
- additional material philosophy layer.

Recommended issue note:

`147/148 package the M01-M02 handoff for Firefly research. The next test is one file-only dryrun using the stripped writer-visible dispatch, audited for stamp/chair payment before explanation.`
