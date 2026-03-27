# chaebol_ent_empire Promotion Patch Note

Date: 2026-03-27
Type: minimal promotion-blocker patch (artifact-only, no code changes)
Target pair:
- BI: `bible/_quarantine/03_chaebol_ent_empire_bi.json`
- TR: `treatments/_quarantine/03_chaebol_ent_empire_tr_block_070_draft.json`
Prior canary: `docs/2026-03-27/chaebol-ent-empire-revival-canary-report.md`

---

## 1. Patches Applied

### 1.1 `block_no` (TR + BI plot_roadmap)

Added `block_no` integer field to all 70 blocks in both files.

- Source: derived from existing `block_id: "Block N"` — `block_no = N`
- TR: 70/70 blocks patched
- BI plot_roadmap: 70/70 blocks patched
- Verification: `block_no` first=1, last=70, all present, sequence continuous

### 1.2 `pov` (BI protagonist_config)

Added `"pov": "3인칭"` to `protagonist_config`.

- Rationale: TR `pov_character` distribution is 권태하 60/70, 윤서아 6/70, 최라희 4/70. This is a 3rd-person protagonist-centered POV with occasional external POV inserts.

### 1.3 `external_pov_insert_policy` (BI protagonist_config)

Added `"external_pov_insert_policy": "제한적 허용"` to `protagonist_config`.

- Rationale: 10/70 blocks use non-protagonist POV (윤서아, 최라희). This matches the `"제한적 허용"` policy defined in `modules/core/project_support.py` for 3인칭 POV.

## 2. What Was NOT Changed

- Block titles: untouched
- Capital progression: untouched (120억 → 6800억)
- Opponent structure: untouched
- BI structural sections (npc_timeline, foreshadow_map, opponent_transition_plan, portfolio_history, Seeds): all preserved
- File locations: both files remain in `_quarantine`
- Narrative content: zero changes to any context/solution/reward/stakes/foreshadow/callback fields

## 3. Post-Patch Consumability

| Check | Before patch | After patch |
|-------|-------------|-------------|
| `tr_consumability` | pass | **pass** |
| `bi_standalone_roadmap_readiness` | mixed | **pass** |
| `pair_consumability` | pass | **pass** |
| `embedded_roadmap_warnings` | 70 (`block_no missing`) | **0** |
| `runtime_protagonist_keys_missing` | 2 (`pov`, `external_pov_insert_policy`) | **0** |
| `notes` | "runtime protagonist subset is partial" | **[]** |

All consumability verdicts are now **pass** with zero warnings.

---

**Promotion blockers patched: yes**

**Pair promotion-ready now: yes**

**Should Codex run the next revival-stage probe now: yes**
