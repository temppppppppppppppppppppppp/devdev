# Stage 2 디테일 딥다이브 — 통합 보고서

> 작성일: 2026-03-13
> 3Pass 감리 완료, 코드 수정 금지

---

## Executive Summary

| 지표 | 값 |
|------|-----|
| 트랙 수 | 5 |
| 후보 총 건수 | 39 |
| **확정 Finding** | **25** |
| 오탐 | 2 |
| 보류 | 3 |
| 기존 문서 중복 제거 | 5 |
| INFO | 1 |
| Clean 확인 | 6 |

### Severity 분포 (확정 건만)

| Severity | 건수 | 비율 |
|----------|------|------|
| **P0** | 0 | 0% |
| **P1** | 0 | 0% |
| **P2** | 12 | 48% |
| **P3** | 12 | 48% |
| **INFO** | 1 | 4% |

**P0/P1 없음** — Stage 2 파이프라인에 데이터 손실이나 오동작 위험은 없으나, P2급 설계 결함 12건은 장기적 품질 저하 요인.

---

## 트랙별 요약

### Track S2D-T1: DI Contract & Callback Wiring
| ID | Sev | 판정 | 제목 |
|----|-----|------|------|
| S2D-T1-001 | **P2** | 확정 | `world_state` 슬롯 Stage2Context 누락 → StateTracker WorldState 바인딩 항상 None |
| S2D-T1-002 | P3 | 확정 | `retry_feedback_contract` required tier 미집행 (raise 없음) |
| S2D-T1-003 | P3 | 확정 | `prompt_builder.py` DI 우회 직접 캐시 접근 (dual-ownership) |

### Track S2D-T2: Validation Pipeline & Guard Chain
| ID | Sev | 판정 | 제목 |
|----|-----|------|------|
| S2D-T2-001 | **P2** | 확정 | ArcAutoCorrector 자율 교정 (item dedup/location/energy/equipment) — 대원칙1 경계 |
| S2D-T2-002 | P3 | 확정 | `_correct_location_issue` Python-only 위치 수정 (형제 메서드는 LLM 사용) |
| S2D-T2-003 | **P2** | 확정 | `_run_continuity_inspection`이 joint_docs/status_shadow 덮어쓰기 → ArcAutoCorrector 수정 무효화 |
| S2D-T2-004 | P3 | 확정 | ArcAutoCorrector `list[str]` vs ArcCorrector `list[dict]` — advisory 변환 시 구조 정보 손실 |
| S2D-T2-005 | P3 | 확정 | `max_corrections=2`, `max_change_ratio=0.20` 하드코딩 (validation.yaml SSOT 외부) |
| S2D-T2-006 | P3 | 보류 | NarrativeStructureAnalyzer LLM 호출이 Guard 내부 — advisory 변환으로 Director 주권 유지 |
| S2D-T2-007 | **P2** | 확정 | DraftValidator 크래시 시 내부 에러 메시지가 Director advisory로 노출 |
| S2D-T2-008 | P3 | 확정 | 1차 DraftValidator advisory가 Consensus에만 전달, Director 미전달 |

### Track S2D-T3: Preflight & State Management
| ID | Sev | 판정 | 제목 |
|----|-----|------|------|
| S2D-T3-001 | **P2** | 확정 | `response_schemas.py` npc_deaths STRING 배열 — 계약은 OBJECT(name/episode/cause) 요구 |
| S2D-T3-002 | **P2** | 확정 | `skill_acquisitions` response_schemas.py에서 완전 누락 → 항상 regex 폴백(~70%) |
| S2D-T3-003 | P3 | 확정 | `major_items` 전용 extract 메서드 + regex 폴백 없음 |
| S2D-T3-004 | — | 보류 | cumulative_state_cache 롤백 경로 mid-batch 실패 시나리오 미검증 |
| S2D-T3-005 | — | 오탐 | PreflightChecker guidance는 LLM 생성 (대원칙1 미침해) |
| S2D-T3-006 | — | 오탐 | 10개 장르 `_build_genre_placeholders` 정상 커버 |
| S2D-T3-007 | — | 보류 | enrichment_metadata 소비처 불분명 |
| S2D-T3-008 | **P2** | 확정 | `timeline.start/end` STRING 스키마 vs 소비자 dict 기대 → 검증 노이즈 + 데이터 손실 |

### Track S2D-T4: Finalizer & Director Integration
| ID | Sev | 판정 | 제목 |
|----|-----|------|------|
| S2D-T4-001 | **P2** | 확정 | Equipment 강제 동기화 — Python이 arc_start_state.equipment 직접 덮어쓰기 (대원칙2 경계) |
| S2D-T4-003 | **P2** | 확정 | physical_inventory 자동 상속 — LLM 공백 시 Python 폴백 (대원칙2 경계) |
| S2D-T4-013 | **P2** | 확정 | Equipment Sync 로직 테스트 커버리지 0% |
| S2D-T4-P3a | P3 | 확정 | (기타 P3급 4건 — 상세는 트랙 문서 참조) |

**Clean 확인 6건**: Director 자동선택 완전 제거, compare_and_select_arc LLM-only, STRUCTURAL_MIN_SCORE=50 min-1 보장 정상, DB atomic commit+rollback 견고, QualityGate PASS_WITH_FIX bypass 정상, DB-3/DB-7 advisory-only.

### Track S2D-T5: Dead Code & Test Coverage
| ID | Sev | 판정 | 제목 |
|----|-----|------|------|
| S2D-T5-001 | **P2** | 확정 | `state_locked_arc_generator.py` (583줄) 테스트 커버리지 0% |
| S2D-T5-002 | **P2** | 확정 | `stage2_optimizer.py` 6개 클래스 15개 공개 메서드 미테스트 |
| S2D-T5-003 | **P2** | 확정 | MagicMock spec 미지정 161건 / spec 지정 1건 — __slots__ 인터페이스 드리프트 은닉 |
| S2D-T5-004 | P3 | 확정 | `stage2_contracts.py` 전용 테스트 없음 (3줄 상수 파일, 저위험) |
| S2D-T5-005 | P3 | 확정 | e2e 테스트가 Stage2Context.from_app() 팩토리 경로 미사용 |
| S2D-T5-006 | INFO | 확정 | 데드코드 의심 3파일 전부 라이브 확인 (state_locked, continuity_arc, continuity_inspector) |
| S2D-T5-007 | P3 | 확정 | backward-compat wrapper 12개 — main_a(5) + tests(7) 호출 중, 리팩토링 후보 |

---

## Cross-Track 패턴 분석

### 패턴 1: 대원칙 경계선 (4건)
| Finding | 대원칙 | 판정 |
|---------|--------|------|
| S2D-T2-001 | 1 (Python은 수집만) | ArcAutoCorrector 자율 교정 — 구조 정규화 vs 판단 경계 모호 |
| S2D-T2-002 | 1 | location 수정 Python-only |
| S2D-T4-001 | 2 (팩트시트 LLM만) | Equipment 강제 동기화 — Arc 구조 필드 한정, Director PASS 이후 |
| S2D-T4-003 | 2 | inventory 자동 상속 — LLM 공백 시 폴백 |

**종합 판단**: 4건 모두 "구조 정규화" 범주로 대원칙 위반이라기보다 경계선 사례. 단, 범위가 확장되면 위반으로 전환될 수 있으므로 모니터링 필요.

### 패턴 2: 스키마 계약 불일치 (3건)
| Finding | 불일치 |
|---------|--------|
| S2D-T3-001 | npc_deaths STRING vs OBJECT |
| S2D-T3-002 | skill_acquisitions 스키마 누락 |
| S2D-T3-008 | timeline STRING vs dict |

**영향**: StateTracker 정확도가 구조화 경로(~98%) 대신 regex 폴백(~70%)으로 저하. 3건 모두 response_schemas.py 한 파일에 집중.

### 패턴 3: 테스트 사각지대 (4건)
| Finding | 대상 |
|---------|------|
| S2D-T5-001 | state_locked_arc_generator 0% |
| S2D-T5-002 | stage2_optimizer 15 메서드 0% |
| S2D-T5-003 | MagicMock spec 미지정 161건 |
| S2D-T4-013 | Equipment Sync 테스트 0% |

**영향**: 인터페이스 드리프트가 테스트에서 감지되지 않음. __slots__ 기반 Stage2Context와 spec 없는 MagicMock 조합이 특히 위험.

### 패턴 4: 수정 무효화 체인 (1건, 고유)
| Finding | 설명 |
|---------|------|
| S2D-T2-003 | continuity_inspection이 ArcAutoCorrector 결과를 덮어씀 |

**영향**: ArcAutoCorrector가 수행한 교정이 후속 단계에서 원본으로 롤백됨. 교정 자체가 대원칙1 경계선이므로 "무효화가 오히려 안전장치"일 수 있으나, 의도치 않은 동작.

---

## 권장 조치 우선순위

### 즉시 문서화 (코드 수정 금지, 향후 작업 큐)

| 우선순위 | Finding | 조치 |
|----------|---------|------|
| 1 | T3-001, T3-002, T3-008 | response_schemas.py state_changes 스키마 → 계약 일치 작업 큐 등록 |
| 2 | T1-001 | Stage2Context에 world_state 슬롯 추가 작업 큐 등록 |
| 3 | T5-003 | MagicMock spec= 일괄 적용 작업 큐 등록 |
| 4 | T2-003 | joint_docs 덮어쓰기 체인 정리 작업 큐 등록 |
| 5 | T4-001, T4-003 | Equipment/Inventory 자동동기화 범위 문서화 (대원칙2 경계 명시) |
| 6 | T5-001, T5-002, T4-013 | 테스트 커버리지 확대 작업 큐 등록 |

---

## 기존 문서 교차 참조

| 본 TF Finding | 기존 문서 | 관계 |
|---------------|----------|------|
| S2D-T1-003 | MLW-T1-002 | T1-003이 MLW-T1-002의 compound 사례 |
| S2D-T1 후보 5건 | MLW-T1-001~004, MRL-T1 | 중복 → 제거됨 |
| S2D-T2-001 | 신규 | ArcAutoCorrector 대원칙1 경계 최초 식별 |
| S2D-T3-001~002 | 신규 | state_changes 스키마 불일치 최초 식별 |
| S2D-T5-003 | 신규 | MagicMock spec 체계적 감사 최초 수행 |
