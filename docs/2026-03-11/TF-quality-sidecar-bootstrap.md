# TF Quality Sidecar Bootstrap

> 작성일: 2026-03-11
> 상태: 구현 완료
> 목적: 레거시 `quality_metrics.jsonl`와 원고 산출물만 남아 있는 프로젝트에서도 `quality_summary` / `result_summary`가 비지 않도록 derived sidecar를 복구

## 문제

실프로젝트 중 일부는 아래 상태였다.

- `quality_metrics.jsonl`에는 Stage 4 validation 기록이 있음
- `drafts/ep_*.txt` 또는 `manuscripts`는 있음
- 하지만 `episode_quality_labels` / `episode_quality_signals` sidecar는 비어 있음

결과:

- `Quality Radar` 비어 있음
- `Run Result Summary` 비어 있음
- calibration은 실제 품질 누적보다 "데이터 없음"으로 보임

## 구현

추가:

- `modules/core/quality_sidecar_bootstrap.py`
  - legacy `quality_metrics.jsonl` 파싱
  - ep별 최신 Stage 4 validation 추출
  - `director_selections`에서 실제 verdict / score / selection_reason 보강
  - `manuscripts` 또는 `drafts/ep_*.txt`에서 원고 본문 복원
  - `episode_quality_labels` / `episode_quality_signals` sidecar backfill
  - `work_guard.yaml` 기준 `tracking_slots / registry_profiles / role_fit_constraints` health 진단
- `modules/api/bridge_server.py`
  - 대시보드 조립 시 sidecar bootstrap 수행
  - calibration payload에 `data_health` 추가
  - 수동 review / retrieval 관측 부족 시 next_step 안내 강화
- `scripts/backfill_quality_sidecars.py`
  - 단일 프로젝트 또는 전체 프로젝트 수동 backfill 스크립트

## 검증

테스트:

```bash
python -m pytest tests/test_quality_sidecar_bootstrap.py tests/test_bridge_quality_summary.py tests/test_safe_ops_db_consistency.py tests/test_work_guard.py tests/test_quality_regression.py tests/test_stage2_preflight.py tests/test_stage3_orchestrator.py tests/test_stage4_context_builder.py tests/test_stage4_interview_round.py -q
```

결과:

- `213 passed`

실데이터 적용:

```bash
python scripts/backfill_quality_sidecars.py --project 00000
```

결과:

- `labels=15`
- `signals=15`
- `missing_manuscripts=0`

적용 후 `_build_quality_dashboard_payload("00000", 5)` 확인:

- `quality_summary.available = True`
- `result_summary.available = True`
- `latest_ep = 15`
- `retrieval_summary.available = False`

## 현재 남은 것

- `00000` 기준 retrieval observation 로그는 아직 `0`
- 수동 review label도 아직 `0`
- `work_guard.yaml`도 없어 role-fit calibration은 아직 시작 전

즉 이번 배치는 `quality/result bootstrap`까지는 닫았고, 다음 타깃은 그대로

1. retrieval observation 누적
2. manual review label 누적
3. work_guard / role-fit 실데이터 보정

이다.
