# Opus TF-5: NPC/State Debug Audit (TF-C)

> 감사일: 2026-02-22  
> 범위: `modules/domain/agents/state_tracker.py`, `modules/domain/agents/state_tracker_npc.py`, `modules/domain/agents/state_tracker_plots.py`  
> 호출/계약 추적: `modules/core/stage2_orchestrator.py`, `modules/core/stage3_orchestrator.py`, `main_a.py`, `modules/core/services/project_service.py`, `modules/core/stage4_interview_round.py`, `modules/validation/continuity_validator.py`, `modules/core/db_manager.py`  
> 방법: 수동 라인 단위 검토 (Read/cat), 호출자→피호출자 추적

## Executive Summary

| 위험도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 1 |
| LOW | 0 |

### [C-1] Episode rollback 경로에서 `npc_history`가 정리되지 않아 stale 이력 주입 발생 — HIGH
- **위치**: `modules/core/services/project_service.py:153`, `modules/core/services/project_service.py:158`, `modules/core/db_manager.py:1507`, `modules/core/stage4_interview_round.py:321`, `modules/validation/continuity_validator.py:845`
- **코드 인용**:
```python
# project_service.rollback_episode()
ep_tables = ["manuscripts", "blueprints", "state_logs", "martial_tracker", "sync_status", "causal_graph"]
for t in ep_tables:
    project.db.cursor.execute(f"DELETE FROM {t} WHERE ep_num >= ?", (target_ep,))

# db_manager.reset_after()
self.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))
```
- **현상**: 실제 rollback 실행 경로(`main_a.py:2781 -> project_service.rollback_episode`)는 `npc_history`를 지우지 않는다. 반면 DB의 표준 reset 유틸(`db_manager.reset_after`)은 같은 조건으로 `npc_history`를 명시적으로 삭제한다.
- **재현 시나리오**: 50화까지 진행 후 40화로 rollback하면 `manuscripts/blueprints/state_logs`는 삭제되지만 `npc_history`의 `episode_no >= 40` 레코드는 남는다. 이후 Stage 4에서 `stage4_interview_round.py:321`이 해당 이력을 다시 읽어 `continuity_validator.py:845`에 주입한다.
- **영향**: rollback 직후에도 미래 화수 이력이 continuity 경고 판단에 섞여, 잘못된 성격 급변/연속성 경고가 발생할 수 있다.
- **버그 vs 의도 근거**: 같은 코드베이스 내 rollback 유틸(`db_manager.reset_after`)은 `npc_history` 삭제를 포함하고 있어, episode rollback에서도 정리되어야 한다는 의도가 이미 존재한다.
- **수정 제안**:
```python
# project_service.rollback_episode() 내부
project.db.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))
```
또는 `project.db.reset_after(target_ep)` 경로로 통합해 rollback 정리 정책을 단일화.

### [C-2] `npc_history` 정렬 방향과 personality 비교 인덱스가 불일치해 최신 변화가 아닌 과거 변화를 비교 — MEDIUM
- **위치**: `modules/core/db_manager.py:1753`, `modules/core/stage4_interview_round.py:321`, `modules/validation/continuity_validator.py:855`, `modules/validation/continuity_validator.py:860`
- **코드 인용**:
```python
# db_manager.get_npc_history()
"... FROM npc_history WHERE npc_name = ? ORDER BY id DESC LIMIT ?"

# continuity_validator._check_personality_continuity()
# [G21] personality_traits 변경 이력 필터 후 최신 2개 비교
prev = personality_changes[-2]
curr = personality_changes[-1]
```
- **현상**: DB 반환 순서는 최신→과거(`DESC`)인데, validator는 리스트의 마지막 두 항목(`[-2], [-1]`)을 사용한다. 결과적으로 "최신 2개"가 아니라 조회 범위 내 가장 오래된 2개를 비교하게 된다.
- **재현 시나리오**: personality 이력이 3건 이상인 NPC에서 최근 변화가 급격해도, validator는 과거 2건만 비교해 급변을 놓치거나 반대로 오래된 급변을 현재 문제로 재경고한다.
- **영향**: 성격 연속성 경고의 시점 정확도가 떨어져 Director 판단 신뢰도가 낮아진다.
- **버그 vs 의도 근거**: 주석이 "최신 2개 비교"를 명시하지만 실제 인덱싱은 정렬 계약(`DESC`)과 모순된다.
- **수정 제안**:
```python
personality_changes = sorted(personality_changes, key=lambda h: h.get("id", 0))
prev = personality_changes[-2]
curr = personality_changes[-1]
```
또는 `get_npc_history()`를 `ASC`로 반환하고 호출부 계약을 통일.

## 비고
- `[NPC-L1] bind_db` 배선은 3개 프로덕션 생성 경로에서 모두 확인:
  - `modules/core/stage2_orchestrator.py:155`
  - `modules/core/stage3_orchestrator.py:190`
  - `main_a.py:3010`
- `[NPC-L2] rollback 후 stale registry 방지`는 적용 확인:
  - `main_a.py:2782`에서 `self.state_tracker = None`
  - `main_a.py:3005` 이후 Stage 4 진입 시 lazy 재생성 + `bind_db`.
- `[Tier4-13] resolved_plots 상한`은 구현 및 호출 경로 모두 정상:
  - `modules/domain/agents/state_tracker_plots.py:120` (`max_items=30`)
  - `modules/domain/agents/state_tracker.py:1067` (wrapper 전달)
  - `modules/core/stage2_preflight.py:238`, `modules/core/stage4_context_builder.py:634` (기본값 사용)
