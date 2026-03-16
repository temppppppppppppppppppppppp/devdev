# TF-A 조사: Stage 0-2 신호 x 소비자 존재 여부

- 특별 오더 메모: 기존 하네스는 사용하지 않았고, 현재 워크스페이스 런타임 코드만 기준으로 판정했다.
- 판정 기준:
  - `closed`: 신호가 분기, 재시도, 프롬프트 주입, 오퍼레이터 선택, 또는 다음 단계 진입에 실제 영향을 준다.
  - `advisory`: 소비자는 있으나 자동 분기까지는 아니고 경고/UI/다음 행동 가이드에 머문다.
  - `open`: 현재 런타임 코드에서 소비자를 찾지 못했다.

## 요약

- closed: 9
- advisory: 1
- open: 0
- 핵심 결론: Stage 0-2는 대부분 측정-소비 루프가 닫혀 있다. 다만 Stage 2 retrieval coverage 계열은 자동 분기보다 브리지 calibration/UI 가이드에 더 강하게 소비된다.

## 신호별 판정

| 신호 | 생산자 | 소비자 | 실제 영향 | 루프 상태 | 근거 |
| --- | --- | --- | --- | --- | --- |
| `BootstrapStatus.core_ok/v50_ok/partial_failures` | `main_a.py`의 `_validate_initialized_agents`, `_finalize_bootstrap_status`, `_attach_agents` | 부트 시퀀스의 `if callable(attach_agents) and not attach_agents()` | `core_ok=False`면 부트 중단, `partial_failures`는 부트 로그에 노출 | closed | `main_a.py:177-185`, `main_a.py:1321-1324`, `main_a.py:2256-2333` |
| Stage readiness status (`Stage 0/1/2`) | `StudioSystem.check_v20_readiness()` | 메인 메뉴 렌더링과 Stage 2 진입 전 확인 | Stage 1 미완료 시 Stage 2 진행 전에 skip 확인을 요구 | closed | `modules/core/system.py:80-102`, `main_a.py:2491-2522` |
| Treatment block density (`density_score`, `missing_elements`, `needs_enrichment`) | `BlockEnricher.analyze_block_density()` | `_enrich_treatment_blocks()`의 농축 대상 선정과 사용자 confirm | 농축 대상 block만 추려서 실제 재작성 여부를 결정 | closed | `modules/domain/agents/block_enricher.py:234-295`, `main_a.py:1587-1617` |
| Volume boundary validator (`status`, `reason`, `feedback`, `future_count`) | `Stage01Helpers.validate_volume_boundaries()` | Stage 1 `_vol_on_success()` | 미래 권수 누수면 즉시 실패 처리하고 재시도 루프로 되돌린다 | closed | `modules/core/stage01_helpers.py:56-103`, `modules/core/stage01_helpers.py:843-871` |
| Volume document length (`doc_len`) | Stage 1 `_vol_on_success()` | 동일 함수의 pass/fail gate | 2000자 미만이면 Stage 1 통과를 거부 | closed | `modules/core/stage01_helpers.py:852-858`, `modules/core/stage01_helpers.py:877-888` |
| Stage 2 quality trend summary | `quality_dashboard.get_score_trend_summary(stage=2)` | Stage 2 preflight context 조립 | 최근 품질 추세가 Arc 생성 프롬프트 앞머리에 주입된다 | closed | `modules/core/stage2_preflight.py:793-806`, `modules/core/quality_dashboard.py:973-1008` |
| Stage 4 to Stage 2 reverse difficulty feedback | `pass_rate_monitor.get_arc_difficulty()` | `generate_reverse_feedback_stage4_to_2` 경로 | 이전 Arc 난도를 Stage 2 enhanced context에 다시 주입 | closed | `modules/core/stage2_preflight.py:984-1004`, `modules/core/pass_rate_monitor.py:487-520` |
| Stage 2 retrieval coverage bundle (`source_counts`, `coverage_warnings`, inclusion flags, char counts) | Stage 2 preflight observation record | `QualityDashboard.get_retrieval_summary()`와 브리지 calibration `next_step` | 자동 분기는 아니지만 retrieval 경고가 운영자의 다음 액션 텍스트로 승격된다 | advisory | `modules/core/stage2_preflight.py:1204-1232`, `modules/core/quality_dashboard.py:197-224`, `modules/core/quality_dashboard.py:308-373`, `modules/api/bridge_server.py:1074-1080`, `modules/api/bridge_server.py:1422-1429` |
| Stage 2 fix routing (`fix_scope`, `score`, previous warnings/reasoning) | Stage 2 finalizer와 preflight patch feedback 조립 | PASS_WITH_FIX patch loop, patch-vs-rewrite 분기 | `fix_scope` 누락 시 score threshold로 fallback하고, `partial/full`이면 inplace를 포기한다 | closed | `modules/core/stage2_finalizer.py:669-678`, `modules/core/stage2_preflight.py:1300-1330` |
| Stage 2 verdict/score telemetry | Stage 2 finalizer의 `record_validation`, `record_attempt`, `save_stage_attempt`, `save_director_selection` | 이후 품질 추세, pass-rate, bridge stage stats | Stage 2의 PASS/REJECT와 score가 후속 trend/bias/운영 통계의 입력이 된다 | closed | `modules/core/stage2_finalizer.py:1469-1504`, `modules/core/stage2_finalizer.py:1646-1684`, `modules/core/quality_dashboard.py:124-149` |

## TF-A 판단

- Stage 0-1은 품질/경계 신호가 바로 재시도 또는 사용자 선택으로 연결된다.
- Stage 2는 patch routing과 reverse feedback 루프까지 닫혀 있다.
- TF-A 범위에서 `측정은 하지만 아무도 쓰지 않는 신호`는 현재 코드 기준으로 발견하지 못했다.

## 3pass 감리

- pass1: 생산자와 1차 소비자를 매핑했다. persistence-only write는 소비자로 인정하지 않았다.
- pass2: 테스트/문서 호출을 제외하고 현재 런타임 호출만 남겼다. retrieval coverage는 자동 분기 아님을 반영해 `advisory`로 낮췄다.
- pass3: 특별 오더 조건, 파일명 prefix, UTF-8 저장, TF 단위 저장만 수행했는지 재확인했다.

최종 confidence: 0.96
