# NPC Martial State Substrate Wave1 UTF-8 Hygiene Exception

Date: 2026-03-27
Status: active
Exception ID: `EXC-20260327-npc-martial-wave1-utf8-hygiene`
Owner: `system-track / codex`
Scope: `modules/domain/agents/state_tracker.py`, `modules/domain/agents/state_tracker_npc.py`

## 1. Exception Statement
- what rule is being temporarily bypassed:
  full touched-file `python scripts/check_utf8_hygiene.py ...` closure gating for this execution item
- why it is needed:
  the current `suspicious_question_token` heuristic flags pre-existing legacy regex literals in the tracker files, even after the wave-local scope leak edits were removed; no new invalid UTF-8, replacement characters, or wave-local mojibake regression was identified

## 2. Boundaries
- allowed surface:
  closure of `npc-martial-state-substrate-wave1` with the tracker regex false positives explicitly disclosed
- forbidden surface:
  this exception does not allow invalid UTF-8, replacement-character saves, blind decode fallbacks, or unrelated tracker refactors under the same waiver
- risk if it leaks:
  a real encoding regression inside the same tracker files could be hidden behind the inherited false-positive noise

## 3. Removal Condition
- review trigger:
  the next tracker regex cleanup wave or the next `check_utf8_hygiene.py` heuristic update that touches `suspicious_question_token`
- expiration date:
  2026-04-30
- concrete removal action:
  rerun `python scripts/check_utf8_hygiene.py modules/domain/agents/state_tracker.py modules/domain/agents/state_tracker_npc.py`; remove this exception only after the command passes without special handling

## 4. Linked Docs
- execution SSOT:
  `docs/2026-03-27/npc-martial-state-substrate-wave1-execution-ssot.md`
- roadmap:
  `none`
- scorecard:
  `none`
