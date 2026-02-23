# TF-7 종합 감사 보고서

- 대상 문서: `docs/2026-02-23/opus_tf7_system_audit_order.md`
- 감사 범위: TF-7 A~N 전 구간 + N 크로스컷 시나리오
- 산출물: `docs/2026-02-23/opus_tf7_{a~n}_audit.md`

## 1) 전체 발견 건수
| 심각도 | 건수 |
|---|---:|
| CRITICAL | 0 |
| HIGH | 15 |
| MEDIUM | 9 |
| LOW | 2 |
| 합계 | 26 |

## 2) TF별 분포
| TF | 파일 | CRITICAL | HIGH | MEDIUM | LOW | 핵심 이슈 |
|---|---|---:|---:|---:|---:|---|
| TF-7-A | `opus_tf7_a_audit.md` | 0 | 2 | 1 | 0 | Stage0 Guard 체인 연결 누락 |
| TF-7-B | `opus_tf7_b_audit.md` | 0 | 1 | 1 | 0 | SC 슬롯 예산/소비 경로 불일치 |
| TF-7-C | `opus_tf7_c_audit.md` | 0 | 1 | 0 | 0 | Director 체인에서 강제성 약화 구간 |
| TF-7-D | `opus_tf7_d_audit.md` | 0 | 1 | 0 | 0 | blueprint 비정상 입력에서 검증 우회 가능 |
| TF-7-E | `opus_tf7_e_audit.md` | 0 | 1 | 0 | 0 | 롤백 후 world/fact 메모리 동기화 누락 |
| TF-7-F | `opus_tf7_f_audit.md` | 0 | 0 | 0 | 0 | 확정 결함 없음 (Risk 1) |
| TF-7-G | `opus_tf7_g_audit.md` | 0 | 1 | 1 | 0 | 패턴 저장소 상태 오염 + 반복 감지 체인 |
| TF-7-H | `opus_tf7_h_audit.md` | 0 | 0 | 0 | 0 | 확정 결함 없음 (Risk 1) |
| TF-7-I | `opus_tf7_i_audit.md` | 0 | 2 | 1 | 0 | Stage4 실패 피드백 루프 누락 |
| TF-7-J | `opus_tf7_j_audit.md` | 0 | 2 | 1 | 0 | Emotion/Foreshadow/Karma 배선 불일치 |
| TF-7-K | `opus_tf7_k_audit.md` | 0 | 1 | 0 | 0 | preset_state 저장-복원 계약 단절 |
| TF-7-L | `opus_tf7_l_audit.md` | 0 | 1 | 1 | 0 | Stage4 REJECT 대시보드 미계측 |
| TF-7-M | `opus_tf7_m_audit.md` | 0 | 0 | 2 | 1 | YAML SSOT 대비 런타임 fallback 잔존 |
| TF-7-N | `opus_tf7_n_audit.md` | 0 | 2 | 1 | 1 | dead NPC BLOCKING 비강제 + 롤백 seam |

## 3) Cross-TF 이슈 (복수 TF 연관)
1. 롤백 정합성 seam  
TF-7-E, TF-7-N 공통으로 `ProjectService.rollback_episode` 경로에서 world/fact 메모리 객체 동기화 누락이 확인됨.
2. dead NPC 차단 강제성 약화  
TF-7-H, TF-7-N 공통으로 BLOCKING 실패가 최종 하드 차단이 아닌 경고 텍스트로 약화되는 경로가 확인됨.
3. preset 상태 영속 계약 단절  
TF-7-A/TF-7-K 축에서 Stage0 저장 경로와 Stage2 재로드 경로가 분리되어, 세션 경계에서 preset 연속성이 깨짐.
4. 설정 SSOT 드리프트  
TF-7-M/TF-7-N(09)에서 `validation.yaml` 미정의 키를 코드 fallback으로 보완하는 패턴이 다수 확인됨.

## 4) TF-5/6 패치 회귀 확인 결과
| 패치 ID | 확인 여부 | 증거 |
|---|---|---|
| TF-6-B-1 (`resolved_plots` 상한) | 유지 | `modules/domain/agents/state_tracker.py:133`, `modules/domain/agents/state_tracker_plots.py:119` |
| TF-6-B-2 (`all_reveals` 상한) | 유지 | `modules/core/db_manager.py:903`~`modules/core/db_manager.py:905` |
| TF-6-B-3 (`feedback_log` deque) | 유지 | `modules/core/data_collector.py:351` |
| TF-6-E-1 (`ep_count=1` Flow Guard) | 유지 | `modules/core/stage2_validation_pipeline.py:632` |
| TF-6-A (롤백 원자성) | 부분 | DB/episode_bible 정리는 유지되나 world/fact 메모리 동기화 누락 (`modules/core/services/project_service.py:220`, `main_a.py:3028`, `main_a.py:3043`) |
| TF-5-L-1 (Stage4 quality_dashboard 계측) | 부분 | PASS 경로 계측은 유지되나 REJECT 계측 누락 지속 (`modules/core/stage4_post_processor.py:578`, `modules/core/stage4_interview_round.py:950`) |

## 5) 우선순위 제안 (P0/P1/P2)

### P0 (즉시)
1. `TF-7-E-1`: 롤백 시 `world_state`/`fact_ledger` 동기 롤백 또는 강제 무효화
2. `TF-7-N-03-1`: dead NPC BLOCKING 실패를 Stage4 후보 탈락 조건으로 승격

### P1 (단기)
1. `TF-7-K-1`: `preset_state` DB 복원 경로를 Project load/rollback 경로에 통합
2. `TF-7-L-1`: Stage4 REJECT도 `quality_dashboard.record_validation(stage=4, ...)` 계측
3. `TF-7-N-07-1`: blueprint 비정상 입력 시 silent PASS 대신 explicit REJECT/DEGRADED 처리

### P2 (중기)
1. `TF-7-M-*`: `validation.yaml` 키 외부화 완결 + 누락 키 경고 체계
2. `TF-7-N-06-1`: 동적 max-rounds와 운영 로그 문구 정합화
3. Risk 묶음(`TF-7-E-R1`, `TF-7-K-R1`, `TF-7-N-R1/R2`)에 대한 설계 결정 문서화

## 6) 패치 오더 연계 → `opus_tf7_patch_order.md`
- 다음 단계는 본 종합 보고서의 P0/P1 항목을 기반으로 `docs/2026-02-23/opus_tf7_patch_order.md`를 작성해 패치 순서/테스트 전략을 고정하는 것이다.

