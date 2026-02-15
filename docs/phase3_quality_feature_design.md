# Phase 3 잔여 품질 기능 — ROI 선정 + 구현 설계

> 작성: 2026-02-15, checkpoint `71e1eb6`
> 상태: **Step 1 완료** (Step 2 대기)

---

## 1) 현재 기준선

| 항목 | 값 |
|------|-----|
| checkpoint | `71e1eb6` (Step 1 완료) |
| 테스트 합계 | 238 (unit 34 + quality 15 + pipeline 89 + E2E 22 + regression 78) |
| ctx refs | stage2 348/43, stage4 321/22 (불변) |
| R4-a | NO-GO (async 통일 보류, `docs/r4a_go_no_go_memo.md`) |
| 구조 개선 | Phase 4-R1~R3 완료 — 몬스터 함수 2개 제거 (3,456줄 → 133줄) |

---

## 2) 후보 기능 비교표

### 후보 정의

| ID | 기능 | 출처 | 기존 인프라 |
|----|------|------|------------|
| **A** | 품질 회귀 감지 (Quality Regression Detection) | 3-E | `pass_rate_monitor` (439줄), `quality_dashboard` (793줄) |
| **B** | 크로스 에피소드 반복 감지 | 3-E | `repetition_guard` (185줄, 1화 내 n-gram만) |
| **C** | NPC 과잉 등장 경고 | 3-E | `state_tracker_npc` (1,975줄, 카운터 없음) |
| **D** | 대리만족 프레임워크 (Reader Satisfaction) | 3-F | `scoring_validator` (975줄), `director_auditor` (1,015줄) |

### ROI 평가 (1=낮음, 10=높음)

| 기준 (가중치) | A. 회귀 감지 | B. 크로스 반복 | C. NPC 과잉 | D. 대리만족 |
|-------------|-------------|--------------|------------|------------|
| 사용자 임팩트 (30%) | 7 — 품질 하락 조기 경보 | 6 — 장편 반복 방지 | 5 — 인지부하 경감 | 9 — 핵심 재미 보장 |
| 구현 복잡도 (25%, 높을수록 쉬움) | 8 — 기존 dashboard 확장 | 5 — DB 인덱싱 신규 | 9 — 카운터 1개 | 3 — Director 심사축 변경 |
| 리스크 (20%, 높을수록 안전) | 9 — 관측 전용, LLM 불변 | 7 — advisory 수준 | 9 — advisory 수준 | 4 — LLM 점수 체계 변경 |
| 테스트 용이성 (15%) | 9 — 점수 mock으로 완전 검증 | 6 — 멀티에피소드 fixture 필요 | 9 — 결정적 카운트 | 5 — LLM 의존 |
| 예상 소요 (10%, 높을수록 빠름) | 8 — 2 step, ~150줄 | 5 — 3 step, ~300줄 | 9 — 1 step, ~50줄 | 3 — 4+ step, ~500줄 |
| **가중 합계** | **8.05** | **5.85** | **7.80** | **5.30** |
| **ROI 순위** | **1위** | 3위 | 2위 | 4위 |

---

## 3) 최종 선정: A. 품질 회귀 감지 (Quality Regression Detection)

### 선정 이유 (3줄)

1. `quality_dashboard`에 이미 에피소드별 점수 기록 + 트렌드 분석 인프라가 있어 **확장 비용이 최소** (~150줄).
2. 관측 전용(advisory)이라 LLM 동작을 전혀 변경하지 않으므로 **프로덕션 리스크 제로** — 대원칙 "Python은 수집만" 완전 준수.
3. Stage 2 컨텍스트에 점수 추세를 주입하면 Analyst가 **자율적으로 Arc 품질 보정**을 시도하므로 즉각적 가치 발생.

### 보류 항목

| ID | 보류 근거 |
|----|----------|
| **B. 크로스 반복** | DB 인덱싱 신규 개발 + 멀티에피소드 fixture 비용 대비 임팩트가 A보다 낮음 |
| **C. NPC 과잉** | 구현은 간단하나 사용자 체감 임팩트가 가장 낮아 단독 Phase로 부적합 (A 완료 후 번들 가능) |
| **D. 대리만족** | ROI 최고 임팩트이나 Director 점수 체계 변경은 **LLM 동작 변경 + 전 에이전트 재검증** 필요 — A/C 완료 후 착수 |

---

## 4) 구현 전 설계

### 4-1. Scope In / Out

**In (이번 범위)**:
- `quality_dashboard.py`에 `detect_score_regression()` + `get_score_trend_summary()` 메서드 추가
- `validation.yaml`에 `regression` 섹션 추가 (threshold, enabled 플래그)
- Stage 4 `_process_pass_result()`에서 regression check 호출 → WARNING 로그
- Stage 2 arc context에 score_trend_summary 1줄 주입 (advisory)

**Out (이번 범위 제외)**:
- regression 시 자동 REJECT / 자동 재생성 (대원칙 위반)
- Streamlit UI 대시보드 변경
- pass_rate_monitor 변경 (dashboard만 확장)
- Director 프롬프트 / 점수 체계 변경

### 4-2. 데이터 흐름

```
Stage 4: Director 심사 → score 확정
  │
  ├─ quality_dashboard.record_validation(ep, score)   [기존]
  │
  ├─ quality_dashboard.detect_score_regression(ep)     [신규]
  │     └─ prev_score = last_recorded_score(ep - 1)
  │     └─ delta = prev_score - score
  │     └─ if delta >= threshold → {detected: True, delta, prev_ep, prev_score}
  │     └─ else → {detected: False}
  │
  └─ WARNING 로그 출력 (detected=True인 경우)

Stage 2: Arc 설계 시
  │
  ├─ quality_dashboard.get_score_trend_summary(recent_n=5)   [신규]
  │     └─ "최근 5화 평균 78점, 추세: 하락 (직전 대비 -22)"
  │
  └─ arc_context에 trend_summary 포함 → Analyst가 참조
```

### 4-3. 실패 모드 3개

| # | 실패 모드 | 완화 |
|---|----------|------|
| 1 | **첫 에피소드 (이전 점수 없음)** | `detect_score_regression()`에서 prev_score=None이면 `{detected: False}` 반환, 크래시 없음 |
| 2 | **quality_dashboard 비어있거나 파일 손상** | try/except로 graceful skip + `logging.warning()` — Stage 4 흐름 비차단 |
| 3 | **threshold 과민 (너무 낮은 값)** | validation.yaml 기본값 20, 최소값 가드 10 — 10 미만 설정 시 WARNING 로그 + 10으로 클램프 |

### 4-4. 관측 지표 3개

| # | 지표 | 측정 방법 | 기대값 |
|---|------|----------|--------|
| 1 | `regression_event_count` | dashboard 내부 카운터 (JSONL 기록) | 정상 프로젝트: 전체 에피소드의 10% 미만 |
| 2 | `average_score_delta` | 연속 에피소드 간 점수 차이 평균 | ±5 이내 (안정), ±15 이상 (불안정) |
| 3 | `recovery_rate` | regression 발생 후 다음 에피소드에서 개선된 비율 | 70%+ (Analyst가 trend 참조 시) |

### 4-5. 롤백 전략

| 방법 | 조치 |
|------|------|
| **코드 롤백** | `git revert <commit>` — 관측 로직만 제거, 파이프라인 동작 불변 |
| **런타임 비활성화** | `validation.yaml`에 `regression.enabled: false` → check 호출 스킵 |
| **영향 범위** | 관측 전용이므로 비활성화 시 기존 동작과 100% 동일 |

---

## 5) 수용 기준(AC) + 테스트 전략

### AC (6개)

| # | 수용 기준 | 검증 방법 |
|---|----------|----------|
| AC-1 | Episode N 점수가 N-1 대비 threshold(기본 20) 이상 하락 시 WARNING 로그 출력 | Unit: mock 점수 → 로그 캡처 |
| AC-2 | `quality_dashboard.detect_score_regression()` 반환값에 `detected`, `delta`, `prev_score` 포함 | Unit: 반환 dict 키/타입 검증 |
| AC-3 | `validation.yaml`에 `regression.threshold` 설정 추가, `_threshold()` 헬퍼로 조회 | Unit: YAML 없을 때 기본값 20 |
| AC-4 | `get_score_trend_summary(recent_n)` 반환값이 1줄 문자열 (한국어) | Unit: 포맷 검증 |
| AC-5 | 첫 에피소드(이전 점수 없음) 또는 빈 DB 시 크래시 없이 `{detected: False}` 반환 | Unit: 빈 상태 테스트 |
| AC-6 | 기존 테스트 223개 전량 통과 (회귀 없음) | Gate: pytest 4 스위트 |

### 테스트 레벨별 계획

| 레벨 | 파일 | 테스트 수 | 내용 |
|------|------|----------|------|
| **Unit** | `tests/test_quality_regression.py` (✅ 완료) | **15** | regression 8건 (감지/미감지/부족/빈/경계/경고/키/YAML) + trend 7건 (상승/하락/안정/부족/포맷/키/min-max) |
| **Integration** | 기존 E2E에 추가 또는 별도 | 1~2 | Stage 4 mock → dashboard.record → regression check → 로그 출력 확인 |
| **회귀** | 기존 4스위트 | 223 | 전량 불변 |

### 더미/스텁 전략

- `quality_dashboard` 자체를 테스트하므로 **실제 인스턴스 + tmp_path** 사용 (in-memory JSONL)
- Director 점수는 **직접 `record_validation()` 호출**로 주입 (LLM 불필요)
- `_threshold()` 헬퍼는 **YAML fixture**로 설정 주입 (기존 패턴)
- 외부 API 호출 0건

---

## 6) 실행 계획 (3 step)

### Step 1: Core — regression detection 메서드 + Unit 테스트 ✅ 완료

**커밋**: `71e1eb6`

**수정 파일**:
- `modules/core/quality_dashboard.py` — `detect_score_regression()`, `get_score_trend_summary()` 추가 (~160줄)
- `config/settings/validation.yaml` — `quality_regression` 섹션 추가 (window, min_samples, drop_threshold, warning_threshold)
- `tests/test_quality_regression.py` — 신규 (156줄, 15 테스트)

**결과**:
- `detect_score_regression()`: drop≥20→regression, ≥10→warning, `{is_regression, severity, delta, baseline_avg, recent_avg, reason}`
- `get_score_trend_summary()`: 최근 N화 추세 (up/down/flat/insufficient_data) + 한국어 1줄 요약
- 테스트 15/15 passed (regression 8 + trend 7)
- 기존 223 회귀 없음 → 총 238 passed

### Step 2: Integration — Stage 4 hook + Stage 2 context injection

**수정 파일**:
- `modules/core/stage4_orchestrator.py` — `_process_pass_result()` 내 regression check 호출 추가 (~10줄)
- `modules/core/stage2_orchestrator.py` — `_preflight_enrichment()` 또는 arc context 구성에 trend summary 주입 (~10줄)

**종료 조건**:
- Stage 4에서 Director PASS 후 regression check 실행 → WARNING 로그
- Stage 2 arc context에 `score_trend_summary` 키 존재
- ctx refs 변동 허용 범위: stage2 +2 이내, stage4 +2 이내

**게이트**:
```bash
python -m py_compile modules/core/stage4_orchestrator.py modules/core/stage2_orchestrator.py
python -c "from main_a import SovereignApp; print('OK')"
set PYTHONIOENCODING=utf-8
pytest tests/ -v --ignore=tests/stage4_v2_test --ignore=tests/test_validation.py
pre-commit run --files modules/core/stage4_orchestrator.py modules/core/stage2_orchestrator.py
```

### Step 3: 문서 동기화 + 전체 검증

**수정 파일**:
- `내일작업.md` — 테스트 기준선 갱신, 다음 우선순위 조정
- `docs/프로젝트_현황_로드맵_2026-02-14.md` — 완료 항목 추가
- `CLAUDE.md` — checkpoint, 테스트 수치 갱신

**종료 조건**:
- 전체 테스트 통과 (223 + 신규 6~8 = 229~231)
- 문서 간 checkpoint/합계/용어 불일치 0건
- pre-commit 전량 통과

**게이트**:
```bash
git diff -- 내일작업.md docs/프로젝트_현황_로드맵_2026-02-14.md CLAUDE.md
git status -sb
```

---

## 7) 참고: 향후 확장 경로

| 순서 | 기능 | 전제 |
|------|------|------|
| 다음 | C. NPC 과잉 등장 경고 | A 완료 후 번들 (1 step, ~50줄) |
| 그 다음 | B. 크로스 에피소드 반복 | A+C 완료 후 (DB 인덱싱 필요) |
| 장기 | D. 대리만족 프레임워크 | A~C 안정 후 (Director 심사축 변경) |
