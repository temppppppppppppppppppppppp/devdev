# 글도비 코드 품질 평가 방법론 및 Rubric

> 작성일: 2026-03-13
> 대상: Python 파이프라인 본체, Stage 0~4 오케스트레이션, Electron 데스크톱 브리지, 계약/설정/테스트 자산

---

## 1. 목적

이 문서는 글도비 저장소의 코드 품질을 일관된 기준으로 평가하기 위한 실무용 방법론이다.  
평가의 목적은 "코드가 예쁜가"가 아니라 아래 4가지를 빠르게 판정하는 데 있다.

1. 실제 결함 위험이 높은가
2. 변경 시 파급 범위가 통제 가능한가
3. 실패 시 원인 추적과 복구가 가능한가
4. Stage/계약/SSOT가 안정적으로 유지되는가

---

## 2. 평가 원칙

- 점수보다 결함 위험을 우선한다.
- 추측보다 실행 결과와 파일 증거를 우선한다.
- touched area와 실행 경로를 우선 본다.
- Stage 경계 파손, 계약 위반, UTF-8 오염은 단일 건으로도 강한 감점 사유다.
- `PASS_WITH_FIX`, 재시도, 감사 로그는 "존재"보다 "실제로 수렴하는가"를 본다.

---

## 3. 글도비 전용 핵심 관찰 포인트

이 저장소는 일반 CRUD 앱이 아니라 아래 특성을 가진다.

- Python 메인 제어면과 다수의 Stage 오케스트레이터가 중심이다.
- `main_a.py`가 큰 제어 허브 역할을 수행한다.
- 품질 게이트, 감사 로그, soft failure, Director 판단 루프가 중요한 안정성 축이다.
- Electron 데스크톱이 Python 백엔드와 계약 기반으로 연결된다.
- JSON/YAML/Markdown/SQLite/프로젝트 아티팩트가 함께 움직인다.

따라서 품질 평가는 일반적인 "함수 길이"보다 아래 항목을 더 중하게 본다.

- Stage 입력/출력 계약 일치
- 재시도 및 복구 루프 수렴성
- 감사 로그와 원인 추적 가능성
- `main_a.py`와 서비스 계층의 책임 분리 수준
- 테스트가 실제 파이프라인 위험 구간을 커버하는지 여부

---

## 4. 평가 절차

### 4-1. Baseline 수집

먼저 아래를 고정한다.

- 현재 브랜치와 `git status`
- 변경 범위와 touched file
- `pyproject.toml`, `.pre-commit-config.yaml`, `geuldobi-desktop/package.json`
- 관련 테스트 파일과 최근 감사 문서

### 4-2. 자동 증거 수집

전체 일괄 실행보다 위험 구간 중심으로 분할 실행한다.

추천 순서:

```powershell
python -m ruff check .
python -m pytest -q tests/test_main_a_stage_entry_contracts.py tests/test_project_service.py tests/test_protocols_services.py
python -m pytest -q tests/test_stage2_pipeline.py tests/test_stage3_orchestrator.py tests/test_stage4_orchestrator.py
python -m pytest -q tests/e2e/test_l3_golden_route.py tests/e2e/test_l3_stage2_realproject.py
cd geuldobi-desktop; npm test
```

주의:

- 전체 테스트가 크면 touched area 기준으로 먼저 자른다.
- Stage 2/3/4는 개별 오케스트레이터 테스트와 E2E 스모크를 모두 본다.
- 실패 시 첫 실패를 고치는 것이 아니라, 실패 유형이 계약 파손인지 테스트 드리프트인지 먼저 분류한다.

### 4-3. 수동 리뷰

수동 리뷰는 아래 순서로 한다.

1. `main_a.py` 제어면 책임 과적 여부 확인
2. `modules/core` 오케스트레이터와 서비스 경계 확인
3. `modules/validation`의 게이트 우회 경로 확인
4. Electron bridge와 backend endpoint 계약 확인
5. JSON/YAML/SQLite/문서 산출물의 SSOT 일치 확인

### 4-4. 결과 정리

결과는 반드시 아래 형식으로 정리한다.

- `Critical findings`: 즉시 수정 필요
- `Major findings`: 배포 전 정리 권고
- `Rubric score`: 축별 점수와 근거
- `Residual risk`: 아직 확인 못 한 부분
- `Next actions`: 우선순위 1~3

---

## 5. Rubric

각 축은 0.0~5.0점으로 평가한다.  
가중 점수는 `축 점수 / 5 x 가중치`로 계산한다.

| 축 | 가중치 | 무엇을 보나 | 주요 감점 요인 |
|----|--------|-------------|----------------|
| Correctness / Contract Safety | 25 | Stage 입력/출력, 서비스 계약, 회귀 여부 | Stage 경계 파손, 계약 위반, 저장 포맷 불일치 |
| Test Reliability | 20 | 핵심 흐름 테스트, 실패 재현성, E2E/단위 균형 | 핵심 경로 무테스트, flaky, 오래된 실패 방치 |
| Architecture / Modularity | 15 | 책임 분리, 서비스 경계, god object 축소 | 제어면 과집중, 순환 의존, 숨은 사이드이펙트 |
| Observability / Recovery | 10 | 감사 로그, soft failure, 복구 경로, 재시도 수렴 | 실패 원인 추적 불가, 무한 재시도, 조용한 실패 |
| Static Hygiene | 10 | lint, import 정리, dead code, 일관성 | 과도한 ignore, 중복, 임시 코드 상시화 |
| Data / Schema / UTF-8 Discipline | 10 | JSON/YAML/schema/SSOT/UTF-8 일관성 | 깨진 인코딩, schema drift, 문서와 코드 불일치 |
| Security / Operational Safety | 5 | `.env`, 경로 처리, 파괴적 동작 안전장치 | 비밀값 노출, 파괴 명령 가드 부재 |
| Desktop Bridge / Packaging | 5 | Electron-Python 계약, 패키징, UI-백엔드 연결 | endpoint drift, build script 불일치, 브리지 누락 |

### 5-1. 점수 해석

| 점수 | 해석 |
|------|------|
| 4.5~5.0 | 운영 가능. 개선은 최적화 성격 |
| 3.5~4.0 | 양호. 국소 리스크 관리 필요 |
| 2.5~3.0 | 주의. 변경 시 회귀 위험 높음 |
| 1.0~2.0 | 취약. 구조 또는 테스트 보강 선행 필요 |
| 0.0~0.5 | 사실상 실패. 즉시 차단 수준 |

### 5-2. Auto-Fail Red Flags

아래는 총점과 무관하게 전체 평가를 `FAIL` 또는 `REVIEW BLOCKED`로 본다.

- Stage 0~4 중 하나라도 입력/출력 계약이 깨짐
- `PASS_WITH_FIX` 또는 재시도 루프가 수렴하지 않음
- 감사 로그가 핵심 실패 원인을 남기지 못함
- UTF-8 깨짐 또는 SSOT 문서/코드 간 불일치가 확인됨
- touched area에 대응하는 테스트가 없거나 실패한 상태로 방치됨
- 데스크톱 브리지 계약이 깨져 UI에서 실제 기능 호출이 불가함

---

## 6. 글도비용 검사 체크리스트

### 6-1. 공통

- `ruff`와 `pytest`가 재현 가능하게 실행되는가
- `.pre-commit-config.yaml`과 실제 운영 규칙이 일치하는가
- README, pyproject, docs가 UTF-8로 깨지지 않는가
- 임시 파일과 스파이크 코드가 본 경로에 침투하지 않았는가

### 6-2. Python 제어면

- `main_a.py`가 실제 오케스트레이션만 하고 세부 구현은 서비스/모듈에 위임하는가
- audit, cache, stage entry, DB, UI 호출이 한 메서드에 과집중되지 않았는가
- thin delegate가 실제로 얇은가, 아니면 숨은 로직이 남아 있는가

### 6-3. Stage 파이프라인

- Stage 2/3/4 각각이 이전 Stage 산출물 계약을 강하게 검증하는가
- Director/Validator 결과가 후속 단계에서 임의 해석되지 않는가
- fallback과 retry가 "복구"인지 "문제 은폐"인지 구분되는가

### 6-4. 품질/감사 계층

- `modules/validation`의 blocking/consistency/scoring 결과가 실제 차단으로 연결되는가
- advisory 결과가 로그에 남고 최종 판단에 반영되는가
- quality dashboard, audit service, runtime proof가 단순 장식이 아닌가

### 6-5. 데스크톱 브리지

- `main.js`와 `geuldobi-desktop/src` 간 IPC 계약이 실제 backend endpoint와 맞는가
- 데스크톱 테스트가 Stage 0, quality endpoint, work guard 경로를 덮는가
- 패키징 시 backend/engine/python embed 포함 규칙이 깨지지 않는가

---

## 7. 산출물 템플릿

```md
# 코드 품질 평가 결과

## 범위
- 대상:
- 변경 파일:
- 실행한 검사:

## Findings
1. [Severity] 파일:라인 - 이슈 요약
2. [Severity] 파일:라인 - 이슈 요약

## Rubric
| 축 | 점수 | 가중치 반영 | 근거 |
|----|------|-------------|------|

## Red Flags
- 없음 / 있음

## 결론
- PASS / CONDITIONAL PASS / FAIL

## Next Actions
1. ...
2. ...
3. ...
```

---

## 8. 빠른 1차 Rubric 검사 (2026-03-13)

범위:

- 실행 없는 저장소 구조 점검
- `pyproject.toml`, `.pre-commit-config.yaml`, `geuldobi-desktop/package.json`
- `test_results.xml`
- 파일 수/라인 수/테스트 자산 수 확인

확인 사실:

- `main_a.py`: 3666 lines
- `main_a.py` 내 `class`/`def` 매치 수: 111
- `tests` 내 `test_*.py`: 282 files
- `test_results.xml`: 1419 tests, 4 failures, 1 error, 55 skipped
- `ruff` + `ruff-format` pre-commit 존재
- Electron 패키지에서 Python 테스트를 직접 호출하는 구조 존재

### 8-1. 1차 점수

| 축 | 점수 | 가중치 반영 | 근거 |
|----|------|-------------|------|
| Correctness / Contract Safety | 2.5 / 5 | 12.5 | 과거 테스트 리포트에 계약/회귀성 실패 흔적 존재 |
| Test Reliability | 3.5 / 5 | 14.0 | 테스트 자산은 풍부하나 실패와 skip 흔적이 남아 있음 |
| Architecture / Modularity | 2.0 / 5 | 6.0 | `main_a.py` 제어면 집중도가 높음 |
| Observability / Recovery | 4.0 / 5 | 8.0 | audit/quality/dashboard 문서와 모듈이 비교적 강함 |
| Static Hygiene | 3.0 / 5 | 6.0 | lint 체계는 있으나 per-file ignore가 적지 않음 |
| Data / Schema / UTF-8 Discipline | 3.5 / 5 | 7.0 | SSOT/contract 자산은 강하나 인코딩 관리 재확인 필요 |
| Security / Operational Safety | 3.0 / 5 | 3.0 | 즉시 치명상 증거는 없으나 별도 보안 점검 필요 |
| Desktop Bridge / Packaging | 3.5 / 5 | 3.5 | build/test 경로는 존재하나 계약 일치성은 실검증 필요 |

**총점: 60 / 100**

### 8-2. 1차 해석

- 상태는 `주의`다.
- 가장 큰 구조 리스크는 `main_a.py` 제어면 집중과 그에 따른 변경 파급성이다.
- 가장 큰 운영 리스크는 "테스트가 많음"과 "현재도 신뢰 가능한가" 사이의 간극이다.
- 가장 큰 강점은 감사/관측성 축이 이미 구축되어 있다는 점이다.

### 8-3. 즉시 추천 액션

1. `main_a.py` 변경이 들어가는 작업에는 항상 대응 테스트를 묶는다.
2. `test_results.xml`에 남아 있는 실패 유형을 현재 HEAD 기준으로 재확인한다.
3. `ruff` ignore가 붙은 파일을 위험도 순으로 줄인다.
4. Stage 2/3/4 계약 테스트를 touched area 기준 기본 게이트로 고정한다.

---

## 9. 운영 규칙

앞으로 코드 품질 평가는 아래 규칙으로 운영한다.

- 총점만 보고 승인하지 않는다.
- Findings가 없으면 "없음"을 명시하고 잔여 리스크를 따로 적는다.
- touched area에 대한 테스트 증거가 없으면 높은 점수를 주지 않는다.
- `main_a.py`, Stage 오케스트레이터, Electron bridge 변경은 항상 별도 항목으로 본다.

