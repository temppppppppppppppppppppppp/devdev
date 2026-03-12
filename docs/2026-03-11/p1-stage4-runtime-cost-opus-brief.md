# P1 Stage 4 Runtime/Cost Hardening OPUS Brief

## Scope
- P1 목표: `retry/fanout 경감 + per-round 계측 강화`
- 실전 재실행은 제외
- 이번 배치의 변경은 `P0 correctness hardening` 위에 `runtime/cost hardening`만 추가

## Touched Paths
- `modules/core/stage4_interview_round.py`
- `modules/domain/agents/chief_writer.py`
- `modules/core/metrics_collector.py`

## Implemented Changes
- `quality_issue` / `constraint_violation` retry regenerate는 `strategy_budget="reduced"`로 2-strategy fanout만 사용
- `post_select_conflict` forced patch는 `round_num <= 1`까지만 허용
- round별 metrics delta를 episode-end reset과 분리
- `episode_production.jsonl`에 round cost/tokens/calls 및 `strategy_budget`, `strategy_count`, `reject_bucket` 기록
- `PassRateMonitor.record_attempt()`에 실제 `duration_ms`, `token_cost` 전달

## Regression Command
```powershell
pytest tests/test_stage4_interview_round.py tests/test_chief_writer.py tests/test_cost_tracking.py tests/test_v75c_contradiction_firewall.py tests/integration/test_patch_wiring.py -q
```

## Result
- `154 passed in 3.74s`

## Review Questions
1. `quality_issue/constraint_violation` retry를 2-strategy fanout으로 줄여도 quality regression 위험이 과도하지 않은가
2. `post_select_conflict` forced patch를 `round 1`까지만 허용하는 제한이 충분한가
3. scope peek 기반 per-round cost 계측이 episode-end cost reset과 충돌하지 않는가

## Context
- reconciliation baseline: `docs/2026-03-11/ops-runtime-cost-reconciliation-codex.md`
