# GMR-C Stage Contract & Handoff Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- `docs/stage_map/interfaces.md`는 Stage 2 -> 3 -> 4 handoff를 `anchors`, `blueprints`, `manuscripts`, `episode_bibles`, `state_logs` 기준으로 정의한다.
- `stage2_finalizer.py`는 Arc 저장 전 `validate_arc_data_fields()` repair seam을 갖는다.
- `stage4_post_processor.py`는 PASS 후 manuscript, episode bible, state log, world state, fact ledger를 순차 저장한다.

## PASS 2 교차 검증

- `modules/core/stage2_finalizer.py:905-1089`는 downstream consumer seam을 고려해 arc를 저장 직전 보정한다.
- `modules/core/stage4_post_processor.py:310-340`은 manuscript를 먼저 명시적 DB 트랜잭션으로 저장한다.
- 이후 `save_episode_bible`, `save_state_log_with_summary`, `_save_world_state_atomic()`는 soft failure를 허용하는 별도 단계다.

## PASS 3 최종 findings

### [GMR-C-001] Stage handoff truth는 DB 중심으로 문서와 대체로 일치한다

- Severity: `closed / non-finding`
- Evidence:
  - `docs/stage_map/interfaces.md`
  - `modules/core/db_manager.py:1095-1108`
  - `modules/core/db_manager.py:1843-1878`
- Note:
  - 현재 코드와 문서는 모두 txt보다 DB를 우선 truth로 본다.
  - 이 항목은 open finding이 아니라 기준선 확정 항목으로 닫는다.

### [GMR-C-002] Stage 4 durable output은 하나의 원자적 계약이 아니라 hard sink와 soft sink로 분리된다

- Severity: `P1`
- Evidence:
  - `modules/core/stage4_post_processor.py:310-340`
  - `modules/core/stage4_post_processor.py:1013-1138`
  - `modules/core/stage4_post_processor.py:1140-1232`
- Why macro risk:
  - manuscript 저장은 fail-closed에 가깝지만, episode_bible/state_log/world_state/fact_ledger는 실패해도 후속 처리가 유지된다.
  - 따라서 “제N화 PASS 결과”가 항상 동일한 수준의 downstream artifact completeness를 의미하지 않는다.
- Recommended next order:
  - PASS artifact completeness를 별도 상태 코드로 표준화하는 후속 문서 필요.

### [GMR-C-003] downstream repair seam이 stage boundary를 의도적으로 반투명하게 만든다

- Severity: `P2`
- Evidence:
  - `modules/core/stage2_finalizer.py:905-906`
  - `modules/core/stage4_orchestrator.py:1099-1170`
- Why macro risk:
  - Stage 2 finalizer가 저장 직전 schema repair를 수행하고, Stage 4는 반복 실패 시 Stage 3 reverse feedback/inplace patch를 시도한다.
  - 구조적으로는 유연하지만, “어느 stage가 어느 결함을 책임지는가”를 흐리게 만든다.
- Recommended next order:
  - repair seam과 ownership seam을 분리하는 contract 문서 필요.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
