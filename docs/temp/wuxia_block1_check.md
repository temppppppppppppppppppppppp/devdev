# Wuxia TR Batch Check 1-1

## Summary
- unresolved P0: 2
- unresolved P1: 8
- unresolved P2: 1
- autofixed: 0

## P0
- Block 1 `ENERGY-002`: internal_energy_before is not numeric.
- Block 1 `ENERGY-003`: internal_energy_after is not numeric.

## P1
- Block 1 `MARTIAL-001`: genre_ext.realm_before is blank.
- Block 1 `MARTIAL-001`: genre_ext.realm_after is blank.
- Block 1 `MARTIAL-001`: genre_ext.internal_energy_before is blank.
- Block 1 `MARTIAL-001`: genre_ext.internal_energy_after is blank.
- Block 1 `MARTIAL-001`: genre_ext.faction_position is blank.
- Block 1 `MARTIAL-001`: genre_ext.jianghu_reputation is blank.
- Block 1 `MARTIAL-001`: genre_ext.enemy_pressure is blank.
- Block 1 `OPP-001`: genre_ext.opponent.name is blank.

## P2
- 1-1 `MARTIAL-010`: No clear martial progress exists in the entire batch.
## Draft Projection
- production_density_gate: False
- avg_bundle_chars: 1012.0
- avg_solution_chars: 240.0
- callback_ratio: 0.0
- unresolved_foreshadow_count: 3
- opponent_unique: 1
- top_opponent_share: 100.0
- martial_progress_blocks: 1/1
- hard_gate_failures: ['callback_ratio_ok', 'unresolved_foreshadow_count_ok']
