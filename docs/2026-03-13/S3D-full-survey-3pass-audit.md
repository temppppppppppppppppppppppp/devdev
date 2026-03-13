# S3D: Stage 3 디테일 딥다이브 — 3pass 교차 검증 및 최종 판정

**감사일**: 2026-03-13
**범위**: Stage 3 Blueprint 파이프라인 전체 (~6,900줄)
**방법**: 5트랙 병렬 1pass → 교차 검증 2pass → 최종 판정 3pass

---

## 1pass 원시 결과 요약

| 트랙 | P0 | P1 | P2 | P3 | 총 |
|------|----|----|----|----|-----|
| T1 오케스트레이션 + DI | 0 | 0 | 1 | 1 | 2 |
| T2 LLM 에이전트 계약 | 0 | 0 | 1 | 1 | 2 |
| T3 데이터 계약 + 스키마 | 0 | 0 | 1 | 1 | 2 |
| T4 대원칙 + 안전장치 | 0 | 0 | 1 | 0 | 1 |
| T5 테스트 커버리지 | 0 | 0 | 3 | 5 | 8 |
| **합계 (중복 포함)** | **0** | **0** | **7** | **8** | **15** |

---

## 2pass 교차 검증

### 중복 제거

| 원시 | 트랙 | 병합 판정 |
|------|------|-----------|
| T2-P3 ASP 임계값 문서화 | T2 | T5-P3 ASP 배선 미커버와 **병합** → 단일 항목 |
| T5-P3 ASP 배선 미커버 | T5 | ↑ 병합됨 |

→ 중복 1건 제거, 순수 14건

### 트랙 간 교차 평가

| 발견 | 교차 검증 결과 |
|------|---------------|
| **T1-P2 fail_count=0 리셋** | T5에서 해당 경로 테스트 확인: `test_handle_success`(3건)에서 반환값 검증하나 **누적 fail_count 소실은 미검증**. `_handle_failure`가 항상 `break=True`이므로 현재 코드에서 실질 영향 없음. **유지 P2 → 조건부 P2** |
| **T2-P2 PASS_WITH_FIX 패치 누적** | Stage 3에서 PASS_WITH_FIX는 `_handle_failure`로 라우팅 (T5 확인). 따라서 **Stage 3 오케스트레이터 레벨에서는 패치 누적 불가**. 패치 누적은 `ThreePhaseBlueprintGenerator` 내부 retry 루프 한정. InPlace 30KB 가드 + Pydantic 검증 + Director 재심사로 3중 방어. **유지 P2** |
| **T3-P2 Entity Registry 중복 추출** | T5에서 `_get_entity_registry` 테스트(4건) 확인. Stage 4 재추출은 설계 의도(Stage 간 독립성)일 수 있으나 LLM 비용 중복은 사실. **유지 P2** |
| **T4-P2 정지선 30자 substring 오탐** | Python은 REJECT 권한 없음(대원칙 1). 오탐 시 Director에게 불필요한 CRITICAL 경고 전달만. Director가 최종 판정. **유지 P2 → 조건부 P2** (실질 영향은 P3에 가까우나, CRITICAL 태그로 Director 판정 편향 가능성 있어 P2 유지) |
| **T5-P2 Treatment Block 미커버** | `stage3_orchestrator.py:1044-1101` 전체 미테스트. 프로덕션 semantic_context 핵심 블록. **확정 P2** |
| **T5-P2 gen_err 크래시 미커버** | `stage3_orchestrator.py:1270-1278` LLM generate() 폭발 시 안전망. **확정 P2** |
| **T5-P2 E2E 시나리오 길이** | ~131자 vs BLUEPRINT_MIN_CHARS=800. 테스트 현실성 갭이나 E2E가 오케스트레이터 파이프라인 검증 목적이므로 기능상 무해. **유지 P2 → 조건부 P2** |

---

## 3pass 최종 판정

### 확정 P0: 0건
### 확정 P1: 0건

### 확정 P2: 7건

| ID | 트랙 | 발견 | 파일:줄 | 판정 |
|----|------|------|---------|------|
| **S3D-F01** | T1 | `_handle_success` fail_count=0 리셋 — 성공 시 실패 누적 카운트 소실 | `stage3_orchestrator.py:1565` | **조건부 P2** — `_handle_failure`가 항상 break하므로 현재 무영향. fail-break 완화 시 버그화 |
| **S3D-F02** | T2 | PASS_WITH_FIX 패치 누적 — InPlace 패치가 이전 패치 위에 중첩 가능 | `three_phase_blueprint_generator.py:551-598` | **확정 P2** — 3중 가드(30KB, Pydantic, Director 재심사) 존재하나 구조적 누적 리스크 |
| **S3D-F03** | T3 | Entity Registry Stage 3/4 독립 추출 — 중복 LLM 호출 + 잠재적 불일치 | `stage3_orchestrator.py:811-848`, `stage4_orchestrator.py:1352-1358` | **확정 P2** — LLM 비용 중복. 입력 형식 차이(Arc 리스트 vs 에피소드 번호)로 결과 미세 차이 가능 |
| **S3D-F04** | T4 | 정지선 30자 substring 매칭 오탐 가능성 | `unified_blueprint_validator.py:392-405` | **조건부 P2** — Director advisory로만 작동(REJECT 권한 없음). CRITICAL 태그로 Director 편향 가능 |
| **S3D-F05** | T5 | Treatment Block([TF9]) 주입 경로 테스트 미커버 | `stage3_orchestrator.py:1044-1101` | **확정 P2** — 프로덕션 semantic_context 핵심 블록. 포맷/내용 검증 부재 |
| **S3D-F06** | T5 | gen_err 크래시 경로 테스트 미커버 | `stage3_orchestrator.py:1270-1278` | **확정 P2** — LLM generate() 예외 시 안전망 미검증 |
| **S3D-F07** | T5 | E2E integrated_scenario ~131자 vs BLUEPRINT_MIN_CHARS=800 | `test_l3_stage3_smoke.py:76` | **조건부 P2** — 오케스트레이터 파이프라인 검증 목적으로는 유효하나 데이터 현실성 부족 |

### 확정 P3: 7건

| ID | 트랙 | 발견 | 파일:줄 | 판정 |
|----|------|------|---------|------|
| **S3D-F08** | T1 | `self.app` 직접 접근(ctx 우회) — quality_dashboard, constraint_db 4곳 | `stage3_orchestrator.py:1545,1751,1980,1194` | 의도적 DI 스코프 경계. getattr+None 가드 |
| **S3D-F09** | T2+T5 | ASP 활성화 임계값(retry≥2) 문서화 부족 + 배선 미테스트 | `three_phase_blueprint_generator.py:297` | 기능적으로 정확. Director가 최종 선택 |
| **S3D-F10** | T3 | ContinuityPinGuard 첫 화 비활성화 | `continuity_pin_guard.py:108` | 설계 의도. 첫 화에 직전 원고 없으므로 자연스러운 비활성화 |
| **S3D-F11** | T5 | SC(Smart Context) 실패 경로 미테스트 | `stage3_orchestrator.py:1041` | Non-blocking 경로. 실패 시 semantic_context 빈 채로 진행 |
| **S3D-F12** | T5 | NS-4 타임라인 주입 통합 경로 미테스트 | `stage3_orchestrator.py:1103-1146` | 헬퍼 메서드는 테스트됨. 통합 주입만 미커버 |
| **S3D-F13** | T5 | state_extractor mock 형상 불일치 (list[str] vs list[dict]) | `test_stage3_orchestrator.py:177` | `_fix_entity_registry_protagonist`가 facade 위임이므로 영향 제한적 |
| **S3D-F14** | T5 | tactical_doc "x"*600 비현실적 — 타임마커 regex 미매칭 | `test_stage3_orchestrator.py:28` | 단위 테스트 픽스처로서 허용. 타임마커 헬퍼는 별도 테스트 |

### 오탐 제거: 0건

1pass에서 보고된 모든 항목이 근거와 함께 확인됨. 오탐 없음.

---

## 4대 대원칙 준수 현황

| 대원칙 | 판정 | 근거 |
|--------|------|------|
| 1. Python은 수집만, 판단은 LLM | **준수** | PreValidator 경고만, verdict는 Director |
| 2. 팩트시트 수정 권한은 LLM만 | **준수** | Stage 3 전체에서 NPC/세계관 직접 수정 코드 없음 |
| 3. 디렉터 주권주의 | **준수** | Director=None→REJECT, PASS_WITH_FIX bypass, QualityGate PASS에만 적용 |
| 4. 사망 캐릭터 회상/언급만 | **준수** | check_dead_npc→CRITICAL→Director 주의 포인트 전달 |

---

## 안전장치 확인 결과

| 안전장치 | 상태 |
|----------|------|
| QualityGate 90점 3스테이지 통일 | OK |
| fail_count 무한루프 방어 (_handle_failure break=True) | OK |
| production_head >= total_planned_ep 2중 방어 | OK |
| target_ep 역전 방어 | OK |
| InPlace 30KB 보호 | OK |
| 비무협 internal_energy 오염 방지 | OK |
| Director=None fail-closed | OK |
| JSON 파싱 실패 fail-closed | OK |
| Context Caching ep_num 스코프 격리 | OK |
| Director 비교 가중치 합계 100% | OK |

---

## 종합 평가

Stage 3 Blueprint 파이프라인은 **P0/P1 없이 안정적으로 운영** 중이다.

- **4대 대원칙** 전부 준수
- **10개 안전장치** 전부 정상 작동
- **P2 7건** 중 3건은 조건부(현재 코드에서 실질 영향 없음), 4건은 확정(테스트 커버리지 2건 + 설계 리스크 2건)
- **P3 7건** 전부 문서화/테스트 현실성 수준

개선 우선순위:
1. **S3D-F05/F06** (테스트): Treatment Block + gen_err 크래시 테스트 추가 → 안전망 검증
2. **S3D-F03** (설계): Entity Registry 캐시/재사용 검토 → LLM 비용 절감
3. **S3D-F02** (설계): PASS_WITH_FIX 패치 깊이 상한 명시적 바운딩 검토
