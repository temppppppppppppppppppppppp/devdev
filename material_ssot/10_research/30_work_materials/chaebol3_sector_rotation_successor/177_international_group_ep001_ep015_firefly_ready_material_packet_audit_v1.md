# International Group EP001-EP015 Firefly-Ready Material Packet Audit v1

Date: 2026-05-17
Status: adversarial audit, research-only
Target:

- `176_international_group_ep001_ep015_firefly_ready_material_packet_v1.md`

## Verdict

`PASS_WITH_WATCH_FOR_FIREFLY_SIDE_CONTEXT_FILL_OR_M16`

The integrated EP001-EP015 packet is a real improvement over scattered canary fragments.

It gives Firefly a coherent first-15-episode material spine without abandoning the mainline `S2 -> S3 -> S4` pipeline.

## Pass Checks

1. Fifteen units are present: PASS
   - EP001 through EP015 each has a surface, moving object, resisting actor, narrow action, paid ending, and next gate.

2. M09-to-M15 continuity is repaired: PASS
   - M10 no longer repeats the file-room card; it enters cost sheet, shipment ledger, swatch index, and use-right note.

3. Payments rotate: PASS
   - stamp line, watched chair, clipped fax, task sheet, pay notice, spec sheet, sample box, school memo, finance card, supplier question, outgoing inquiry, sample strips, test sheet, retest terms, catalog contents page.

4. Resistance stays practical: PASS
   - audit trail, department name, payroll face, quality credibility, shelf/parent risk, original custody, sample inventory, factory schedule, budget creep.

5. S2-S3-S4 relevance is explicit without replacing the system: PASS
   - the packet says what S2 carries, what S3 stages, and what S4 receives.

## Adversarial Watch

1. This is not full prose.
   - It is high-density material. Full manuscript still needs line-level prose, body texture, voice, and scene length.

2. EP008-EP010 may need careful splitting in production.
   - Public trial, complaint, and finance request can blur if the writer compresses too aggressively.
   - Keep EP008 as entry/use, EP009 as complaint/messy proof, EP010 as finance/file access.

3. EP015 catalog door must stay small.
   - Do not jump from catalog contents to Olympics or famous global actors.
   - Next should be catalog terms, sample procurement, school procurement, or tiny licensing condition.

4. Repeated document surfaces remain a genre strength and a risk.
   - Future full prose should add human mess: late reply, tired clerk, worker impatience, teacher schedule, buyer hand stopping on ledger, finance officer changing wording.

## 3-Pass Audit

### Pass 1 - Commercial Satisfaction

The packet has a paid-episode cadence. Every episode gives something visible before it ends:

- a line stays alive;
- a chair opens;
- outside facts attach;
- a task becomes executable;
- pay notice posts;
- sample survives;
- box is not returned;
- complaint is handled;
- file opens;
- question leaves;
- inquiry goes out;
- sample strips move;
- test sheet exists;
- retest survives;
- catalog page opens.

This is enough to support paid serial pacing at material level.

### Pass 2 - Human-Like Writing Risk

The packet helps because it replaces abstract "competence/reward/authority" with objects and rooms. The risk is that a weak writer turns those objects into repetitive procedural dialogue.

Patch rule:

`one exact procedure term per beat, then let human behavior carry the pressure.`

Examples:

- do not repeat "review" three times if the finance officer's red pen and changed wording can carry it;
- do not repeat "custody" if the clerk's hand stays on the binder;
- do not repeat "return condition" if the buyer's ledger stays open.

### Pass 3 - Mainline Integration

This should not become a new stage.

Best integration shape:

- S2: causal ladder and promise of each episode;
- S3: room/object/resistor/payment/next-gate blueprint;
- S4: compact writer-facing payload plus continuity state.

If Firefly context shows `s4_writer_context_seed.status == partial`, fill it from this packet before prose. Do not paste the audit sections into S4.

## Decision

Accepted as the current first-15-episode material spine.

Current next authorized units:

1. Firefly-side compact S4 context fill test from EP001-EP015.
2. M16 / sportswear licensing or public procurement surface.
3. Patch pass only if an episode surface sounds too document-heavy.

Not authorized:

- production BI;
- production TR70;
- full B16-B20 generation;
- Firefly DB mutation;
- production manuscript save;
- production prompt/schema/validator change;
- NAS mutation.

Safe issue wording:

`176/177 integrate the scattered proof into a Firefly-ready EP001-EP015 material packet. Verdict PASS_WITH_WATCH_FOR_FIREFLY_SIDE_CONTEXT_FILL_OR_M16. This is now a first-15-episode material spine, not production manuscript/TR70/BI authorization.`
