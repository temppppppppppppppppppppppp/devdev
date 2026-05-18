# User Agreements: chaebol3_sector_rotation_successor

Date: 2026-05-17
Status: active for issue #157 canary

## Goal

Make one new material that can help Firefly/Geuldobi produce human-like commercial webnovel prose by learning inductively from real successful manuscripts.

## Target Direction

- regressed chaebol 3rd-generation protagonist
- group successor body
- sector-by-sector growth
- money-making as a repeated pleasure engine
- authority acquisition, not only asset increase
- vicarious satisfaction from adults adopting the protagonist's frame

## User Preference

- Do not invent the whole premise from thin air.
- Start from NAS success works.
- Treat `독식하는 재벌 3세` as the closest commercial skeleton.
- Change local names, surfaces, sectors, incidents, and expression.
- Do not treat functional closeness as a problem.
- Do treat raw prose/dialogue/proper noun/object-chain copying as a problem.

## Current Material Verdict

This is a normalized research material pack, not TR/BI and not canon.

- `selection-ready`: no until the synthesis markdown passes `scripts/material_readiness_validator.py`.
- `Phase0-ready`: not yet.
- `TR/BI-ready`: no.
- next unit after this pack: validator-shaped synthesis under `20_pitch/synthesis/`, then pitch checklist.

## Operator Hard Stop

Future operator, read this before expanding:

- Do not generate 70 blocks in one pass.
- Do not call opening beats `TR blocks`.
- Do not use block 1 as opening cider proof.
- Do not use block 7+ to rescue missing opening proof/reward.
- The only valid opening readiness window is exact rows `block_no: 2, 3, 4, 5, 6`.
- If `material_readiness_validator.py` fails, the candidate is `HOLD`, no matter how good the idea feels.

Current validator command:

```bash
python -X utf8 scripts/material_readiness_validator.py --path material_ssot/20_pitch/synthesis/chaebol3_sector_rotation_successor_working_synthesis.md
```
