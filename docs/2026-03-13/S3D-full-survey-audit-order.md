# S3D: Stage 3 디테일 딥다이브 — 실행 순서 SSOT

**감사일**: 2026-03-13
**감사 대상**: Stage 3 Blueprint 파이프라인 전체 (~6,900줄)

---

## 실행 이력

| 단계 | 시각 | 내용 |
|------|------|------|
| **1pass** | 2026-03-13 | 5트랙 병렬 실행 완료 |
| **2pass** | 2026-03-13 | 교차 검증 — 중복 1건 병합, 오탐 0건 |
| **3pass** | 2026-03-13 | 최종 판정 — P0:0 P1:0 P2:7 P3:7 확정 |

---

## 조사 대상 파일 목록

| 파일 | 줄 | 트랙 |
|------|-----|------|
| `modules/core/stage3_orchestrator.py` | 2,002 | T1, T3, T4 |
| `modules/core/stage3_context.py` | 129 | T1 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 789 | T2, T3 |
| `modules/domain/agents/blueprint_ensemble.py` | 940 | T2, T3 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 460 | T3 |
| `modules/domain/agents/unified_blueprint_validator.py` | 465 | T2, T4 |
| `modules/domain/agents/continuity_blueprint.py` | 479 | T2, T4 |
| `modules/domain/agents/director_ensemble.py` | ~200(S3) | T2, T4 |
| `modules/models/blueprint.py` | 76 | T3 |
| `modules/core/continuity_pin_guard.py` | 150 | T3 |
| `modules/core/services/state_service.py` | L241-287 | T3 |
| `modules/core/stage4_context_builder.py` | ~600 | T3 |
| `tests/test_stage3_orchestrator.py` | 1,128 | T5 |
| `tests/e2e/test_l3_stage3_smoke.py` | 233 | T5 |
| `config/prompts/blueprint_generator.yaml` | - | T2 |
| `config/prompts/ensemble.yaml` | - | T2 |
| `config/prompts/director.yaml` | - | T2 |
| `config/models.yaml` | - | T2 |
| `config/settings/validation.yaml` | - | T4 |
| `config/system.yaml` | - | T2 |
| `main_a.py` (Stage 3 진입점) | - | T1 |

---

## 트랙별 체크리스트 결과

### T1: 오케스트레이션 + DI 배선 (10항목)

| # | 항목 | 판정 |
|---|------|------|
| 1 | `__slots__` vs `from_app()` 1:1 대응 | OK |
| 2 | `ctx.XXX` 참조 선언 누락 | OK |
| 3 | 콜백 `callable()` 가드 전수 | OK |
| 4 | lazy init → app → ctx sync 순서 | OK |
| 5 | ctx sync None 전파 | OK |
| 6 | `_process_single_episode` 반환/루프 대응 | OK |
| 7 | production_head 양쪽 0 → 1화 시작 | OK |
| 8 | target_ep 역전 방어 | OK |
| 9 | fail_count=0 리셋 | **P2** (S3D-F01) |
| 10 | `self.app` ctx 우회 | **P3** (S3D-F08) |

### T2: LLM 호출 경로 + 에이전트 계약 (10항목)

| # | 항목 | 판정 |
|---|------|------|
| 1 | LLM 호출 인벤토리 | OK |
| 2 | 모델 선택 경로 | OK |
| 3 | Context Caching | OK |
| 4 | ThreadPoolExecutor(3) timeout | OK |
| 5 | JSON 파싱 견고성 | OK |
| 6 | InPlace 30KB / rfind | OK / N/A |
| 7 | ASP 통합 | **P3** (S3D-F09, T5와 병합) |
| 8 | Director 비교 가중치 100% | OK |
| 9 | director=None REJECT | OK |
| 10 | PASS_WITH_FIX 루프 | **P2** (S3D-F02) |

### T3: 데이터 계약 + 스키마 (10항목)

| # | 항목 | 판정 |
|---|------|------|
| 1 | Arc 필수 필드 소비 | OK |
| 2 | ep_start None 방어 | OK |
| 3 | protagonist_items 폴백 | OK |
| 4 | Blueprint `extra="allow"` | OK |
| 5 | Blueprint 필수 필드 충돌 | OK |
| 6 | stop_line 3단 폴백 | OK |
| 7 | ContinuityPinGuard 소스 | **P3** (S3D-F10) |
| 8 | prev_blueprints 관리 | OK |
| 9 | Entity Registry → Stage4 | **P2** (S3D-F03) |
| 10 | state_changes_summary 반영 | OK |

### T4: 대원칙 + 안전장치 (10항목)

| # | 항목 | 판정 |
|---|------|------|
| 1 | 대원칙1 Python auto-REJECT 부재 | OK |
| 2 | 대원칙2 NPC 직접 수정 부재 | OK |
| 3 | 대원칙3 Director bypass 방어 | OK |
| 4 | 대원칙4 사망 캐릭터 경로 | OK |
| 5 | 정지선 30자 substring 오탐 | **P2** (S3D-F04) |
| 6 | QualityGate 임계값 통일 | OK |
| 7 | fail_count 무한루프 방어 | OK |
| 8 | production_head 범위 방어 | OK |
| 9 | InPlace 30KB 보호 | OK |
| 10 | 비무협 internal_energy 방지 | OK |

### T5: 테스트 커버리지 + mock (5항목)

| # | 항목 | 판정 |
|---|------|------|
| 1 | 커버리지 갭 | **P2** x2 (S3D-F05, F06) + **P3** x3 (S3D-F11, F12, F09) |
| 2 | mock 계약 | **P3** (S3D-F13) |
| 3 | 에러 경로 | P2 gen_err (F06과 중복), P3 DB commit |
| 4 | E2E 시나리오 길이 | **P2** (S3D-F07) |
| 5 | 테스트 데이터 | **P3** (S3D-F14) |

---

## 최종 판정 요약

| 심각도 | 건수 | 내역 |
|--------|------|------|
| P0 Critical | 0 | — |
| P1 Major | 0 | — |
| P2 Minor | 7 | F01~F07 |
| P3 Info | 7 | F08~F14 |
| **합계** | **14** | — |

---

## 산출물 목록

| 파일 | 내용 |
|------|------|
| `S3D-T1-orchestration-di-wiring-findings.md` | T1 1pass 보고서 |
| `S3D-T2-llm-agent-contract-findings.md` | T2 1pass 보고서 |
| `S3D-T3-data-contract-schema-findings.md` | T3 1pass 보고서 |
| `S3D-T4-principle-safeguard-findings.md` | T4 1pass 보고서 |
| `S3D-T5-test-coverage-accuracy-findings.md` | T5 1pass 보고서 |
| `S3D-full-survey-3pass-audit.md` | 3pass 교차 검증 + 최종 판정 |
| `S3D-full-survey-audit-order.md` | 실행 순서 SSOT (이 문서) |
