# 글도비 Next Steps — 검증 고도화 플랜

> **작성일**: 2026-02-23
> **현황**: TF-5/6/7/7R 완료, 테스트 2,415 passed, ruff 0 violations (commit `ddef308`)

---

## 우선순위 요약

| 순위 | 옵션 | 방식 | 기대 효과 |
|---|---|---|---|
| **1** | **A. Property-Based Testing** ✅ | `hypothesis` 자동 반례 탐색 | 결정론적 테스트가 못 잡는 엣지케이스 자동 발굴 |
| **2** | B. E2E 통합 연기 검증 ✅ | 미니 파이프라인 DI 흐름 검증 | TF-7R 패치 실제 배선 정합성 확인 |
| **3** | C. 아키텍처 부채 감사 ✅ | 코드 고고학 | 다음 감사 정확도 향상 |
| 후순위 | 2차/4차/5차 Risk 패치 | 관찰 기반 결정 | 실제 버그 신호 생기면 진행 |

---

## A. Property-Based Testing (hypothesis)

### 목적
`hypothesis` 라이브러리로 핵심 불변식(invariant)을 자동 반례 탐색으로 검증.
38개 결정론적 chaos 테스트가 못 잡는 케이스(ep=0, 빈 history rollback, max_chars=0 등)를 수천 개 자동 생성.

### 검증 대상 불변식

#### 1. Rollback 불변식
```
∀ ep_list, target:
  tracker.rollback_to(target) → 모든 남은 항목의 ep ≤ target
  tracker.reset() → history 길이 == 0
  rollback_to(0) → history 완전 비움
  rollback_to(MAX_INT) → history 변화 없음
```
대상: `EmotionArcTracker`, `StateDeltaTracker`

#### 2. Validation 불변식
```
∀ context:
  prev_hud=None → ContinuityValidator 반환 degraded=True, passed=True
  blueprint=None → BlockingValidator 크래시 없음, 반환값 dict
  prev_hud 있음 → degraded 필드 False 또는 없음
```

#### 3. Slot Budget 불변식
```
∀ slots, total_budget:
  _assign_slot_budgets() → 모든 slot.max_chars ≥ slot_max_chars_default
  sum(slot.max_chars) ≤ total_budget * 1.1  (10% 허용 오차)
```

#### 4. DB 롤백 불변식
```
∀ ep_records, target:
  rollback_to(target) → DB에 ep > target인 레코드 없음
  rollback 후 _assert_rollback_invariants() → WARNING 없음
```

### 산출물
- `tests/property/` 디렉토리 신규
- `tests/property/test_rollback_props.py`
- `tests/property/test_validation_props.py`
- `tests/property/test_budget_props.py`
- `tests/property/test_db_rollback_props.py`

### 설치 요건
```
pip install hypothesis
```
또는 `requirements.txt` / `pyproject.toml`에 추가.

### 실행 진행 상태
| 파일 | 상태 | 테스트 수 | 반례 |
|---|---|---|---|
| `tests/property/test_rollback_props.py` | ✅ 완료 | 19 | 없음 |
| `tests/property/test_validation_props.py` | ✅ 완료 | 9 | 없음 |
| `tests/property/test_budget_props.py` | ✅ 완료 | 7 | 없음 |
| `tests/property/test_db_rollback_props.py` | ✅ 완료 | 11 | 없음 |
| **합계** | | **46** | **0** |

**결과**: 각 테스트 200~300 example × 46개 → 반례 미발견. TF-7R 불변식 전량 유지 확인.

---

## B. E2E 통합 연기 검증

### 목적
TF-7R 패치(EmotionTracker, StateDeltaTracker, Stage3 QualityDashboard, FailureLearner Stage4)가
실제 DI 컨텍스트를 통해 Stage2→Stage3→Stage4 흐름에서 올바르게 신호를 수신하는지 검증.

현재 chaos 테스트는 컴포넌트를 단독으로 테스트함 — DI 체인 연결 정합성은 미검증.

### 검증 포인트
1. Stage4PostProcessor가 emotion_tracker.add_episode_emotion() 호출
2. Stage3 완료 시 quality_dashboard.record_validation(stage=3) 호출
3. Stage4 REJECT 시 failure_learner.record_failure(stage=4) 호출
4. rollback 성공 시 emotion_tracker.rollback_to() + state_delta_tracker.rollback_to() 동시 호출

### 산출물
- `tests/integration/test_patch_wiring.py` — 미니 파이프라인 모킹 기반 DI 배선 검증

---

## C. 아키텍처 부채 감사

### 목적
7라운드 패치 누적 후 코드 부채 정리.

### 감사 항목
1. `getattr(self, "xxx", None)` 패턴 → DI 슬롯 공식화 후보 목록
2. `try/except Exception: pass` 블록 — 실제 발화 조건 불명확한 것
3. 사용 안 되는 콜백 파라미터 / None guard 중복
4. 다음 TF 감사 정확도를 높이는 코드 정리

---

## 후순위 (관찰 기반 결정)

### 2차: 동적 장르/프리셋 전파 완결
- TF-7-K-R1, TF-7-N-R1, TF-7-B-R2
- preset/genre 변경 시 validator/guard/context 즉시 재구성 이벤트 체인
- **트리거**: 장르 전환이 실제 프로덕션에서 버그로 재현될 때

### 4차: 캐시/타임아웃 라이프사이클 정리
- TF-7-C-R2, TF-7-C-1, TF-7-M-R2
- **트리거**: 타임아웃/캐시 관련 프로덕션 이슈 발생 시

### 5차: Arc JSON 출력 토큰 한도 초과 (데이터 절단 구조적 해결)
- **현황**: Arc 생성 시 매번 `ast.literal_eval 실패 → 정규식 fallback` 발생. tactical_doc(4,000자+) + episode_details + state_constraints 등 합산 시 10,000~13,000자 → Gemini 출력 토큰 한도 초과.
- **현재 대응**: 절단 감지 → 정규식으로 28개 키 복구. 실질 데이터 손실은 없음.
- **근본 해결 방향**: 출력 토큰 한도 상향 설정이 현실적. 2-pass 생성(tactical_doc 별도 호출)은 앙상블 병렬성을 깨므로 부적합 — 후보별로 2차 호출 컨텍스트가 달라져 순차 처리가 필요해짐.
- **트리거**: 정규식 복구 실패율이 올라가거나 키 누락이 발생할 때

### 6차: 설정 SSOT 완결
- TF-7-M-R1 계열 (validation.yaml/system.yaml 100% 키 명시)
- **트리거**: startup 경고나 fallback 발화 빈도가 높아질 때

### 6차: Blueprint↔원고 인터리브 자동 모드
- **현황**: Blueprint 전체 먼저 뽑고 → 원고 전체 생성. 교차 방식(화별로 블루→원고 반복)은 수동으로 메뉴 왔다갔다 해야 함.
- **개선 방향**: Stage 4 진입 시 "다음 화 Blueprint가 없으면 자동으로 Stage 3 실행 후 원고 생성" 조건 추가.
- **구현 포인트**: `stage4_orchestrator.py` 루프 내에서 `next_ep` Blueprint 존재 여부 확인 → 없으면 `stage3_orchestrator.run_single(next_ep)` 호출 후 진행.
- **효과**: 메뉴 전환 없이 블루+원고 한 번에 n화까지 자동 생성. 화별 WorldState 갱신이 다음 Blueprint에 반영됨.
- **트리거**: 원할 때 언제든 (공사 규모 작음)

### 6차: 앙상블 차순위 재활용 (REJECT 시 재생성 최적화)
- **현황**: 앙상블 N개 생성 → 최고점 1개 선택 → UnifiedValidator REJECT → N개 재생성. 차순위 후보들이 버려짐.
- **개선 방향**: REJECT 시 동일 배치의 차순위 후보를 순서대로 재검증 → 전부 소진 시에만 앙상블 재생성.
- **구현 포인트**: `generate_ensemble()`이 이미 `(best, candidates)` 반환. 오케스트레이터에서 `candidates` 리스트를 소진하는 루프 추가.
- **효과**: REJECT 1회당 앙상블 재생성(~2분) 절약. 차순위 통과 시 즉시 진행.
- **적용 대상**: Stage 2 (`arc_ensemble.py`) + Stage 3 (`blueprint_ensemble.py`) 둘 다 해당.
- **Stage 4는 이미 해결됨**: Chief Writer도 `generate_ensemble()`로 후보 N개 생성하지만, BLOCKING 필터로 전체 후보를 거른 뒤 Director가 그 중에서 선택하는 구조. REJECT 시에도 ToT(구조 오류) / MAD(제약 위반) 버킷별 전문 fallback 존재. 후보를 버리지 않음.
- **트리거**: REJECT 빈도가 높아져 총 소요 시간이 유의미하게 늘어날 때
