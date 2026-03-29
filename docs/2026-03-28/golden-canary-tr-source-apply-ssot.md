# Golden Canary TR Source-Apply SSOT

Date: 2026-03-28
Status: complete
Scope: actual TR JSON source-apply for the repaired Golden Canary pair

## 1. Purpose

- This document is the single SSOT for applying already-approved repair decisions into the actual TR JSON.
- It is not a redesign memo.
- It is not a new audit pass.
- It exists to prevent drift between:
  - approved repair decisions
  - actual TR source truth

## 2. Targets

- TR: `C:\Users\User\Desktop\글도비\treatments\01_tr_투자물_골든_카나리아 테스트.json`
- BI: `C:\Users\User\Desktop\글도비\bible\01_bi_투자물_골든_카나리아 테스트.json`
- Repair relay reference: `C:\Users\User\Desktop\글도비\docs\2026-03-28\golden-canary-pair-repair-relay.md`
- Result sink: `C:\Users\User\Desktop\글도비\docs\2026-03-28\golden-canary-tr-source-apply-runlog.md`

## 3. Locked Interpretation

- Strategic verdict: `생산 가능 (GO)`
- Operational verdict: `GO after TR real-apply`
- No new repair-wave design is needed here
- This work is source-apply only

## 4. Hard Rules

- No new design decisions
- No new ranking pass
- No bulk regeneration
- No Python rewrite
- No jq rewrite
- No regex mass rewrite
- Patch actual TR JSON only
- Use only already-approved repair decisions from the relay SSOT
- Preserve untouched TR structure outside the active batch
- Work one batch at a time
- Stop after each batch
- Write the batch result into the result sink document before replying in chat
- Chat reply should be brief and point back to the updated runlog

## 5. Active POV Contract

- `혼합`
- `제한적 허용`
- first scene and last scene stay anchored on Han Siwoo
- no same-scene POV mixing

## 6. Apply Order

### Batch 1. Highest Continuity Risk

- `B41`
- `B42`
- `B46`
- `B47`
- `B48`

Why:

- this is the most continuity-fragile chain
- `B48` still has known old-source contradiction risk
- if this batch drifts, ARC-05 loses authority first

### Batch 2. Carry And Endgame Support

- `B49`
- `B37`
- `B54`
- `B57`

Why:

- this closes Michael / family / endgame carry lines
- these blocks must become source truth before production

### Batch 3. Early And Mid-Body Anchors

- `B16`
- `B18`
- `B22`
- `B26`

Why:

- these anchor flavor, theme carry, and early/mid retention
- they are important but less continuity-fragile than Batch 1

## 7. Current Task

All batches complete. No remaining task.

## 8. Batch 1 Minimum Expectations

### B41

- keep GameStop observation -> crypto-wave insight spine
- add Kim Doyun pressure
- add off-rail routing cost
- preserve hook continuity into B42/B43

### B42

- keep ETH hold competence line
- add institutionalization pressure through counterparties / KYC / Minjae report
- add visible slippage cost from B41 routing choice
- keep Kim Doyun at profile-narrowing level only
- preserve strong hook into B43

### B46

- keep pre-Luna waiting spine
- add Jason wavering fuse
- add mother-call cost
- start family control dilemma

### B47

- receive B46 fuse properly
- keep betrayal -> forced sale -> irony structure
- do not restore old one-block setup shortcut
- keep irony tone restrained, not immediate laughter

### B48

- preserve Luna/UST crash spine
- remove direct old-form Jason continuity conflict
- use Michael-relayed Jason residue logic
- keep Jason as outside fear source, not restored ally

## 9. Output Contract

After Batch 1:

1. update the result sink document first
2. then report only:

   - Which of the five blocks were applied
   - Any source-apply issue found while patching
   - Immediate continuity notes for adjacent blocks only
   - Stop

Result sink format:

- append one dated section per batch
- include:
  - applied blocks
  - source-apply issues
  - adjacent continuity notes
  - next suggested batch
- do not leave the only durable result in chat text

## 10. Stop Gate

After `Batch 1`:

- stop
- ask for confirmation
- do not continue to Batch 2 automatically

## 11. Operator Shortcut

Use this exact instruction when handing off to the next model:

`C:\Users\User\Desktop\글도비\docs\2026-03-28\golden-canary-tr-source-apply-ssot.md`만 SSOT로 읽고 따른다. Current Task만 수행한다. 이건 source-apply work다. 새 설계 금지, 승인된 repair decision만 실제 TR JSON에 반영해라. 결과는 반드시 runlog 문서에 먼저 기록하고, 채팅에는 요약만 남겨라. 끝나면 멈춰라.
