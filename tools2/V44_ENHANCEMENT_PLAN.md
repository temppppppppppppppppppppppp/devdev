# V44 고도화 및 안정화 계획서

**작성일**: 2026-01-29
**대상 버전**: V43 → V44
**목표**: 시스템 신뢰성 95%+, 운영 효율성 30% 향상

---

## 개요

현재 V43 시스템의 코드베이스 분석을 기반으로 4단계 점진적 개선 계획을 수립합니다.

### 현재 상태
- **안정성**: 90% (Critical 버그 2건 잔존)
- **테스트 커버리지**: 20% (수동 테스트 위주)
- **로깅 체계**: 비표준 (print/ui.log 혼재)
- **성능**: 최적화 여지 있음 (N+1 쿼리, 중복 처리)

### 목표 상태
- **안정성**: 98%
- **테스트 커버리지**: 70%
- **로깅 체계**: 표준화 (레벨별 분류)
- **성능**: 20% 개선 (API 비용 절감)

---

## Phase 1: Critical 안정화 (우선순위 P0-P1)

### 1.1 BaseAgent 백업 모델 실패 복구 강화
**파일**: `modules/domain/agents/base_agent.py`
**심각도**: Critical
**예상 시간**: 4시간

**현재 문제**:
```python
except Exception as e_inner:
    print(f"🚨 [Critical] 백업 실패: {str(e_inner)[:50]}")
    return "{}"  # 위험: 빈 JSON → 후속 파싱 오류
```

**개선 내용**:
- [ ] 백업 모델 실패 시 마지막 부분 응답 분석 재시도
- [ ] 응답 검증 로직 추가 (최소 기본 구조 확인)
- [ ] 최대 재시도 초과 시 `requires_human_intervention` 플래그
- [ ] 실패 원인별 분기 처리 (timeout/quota/malformed)

**검증 방법**:
- 의도적 API 실패 시 시스템 복구 테스트
- 빈 응답/부분 응답 처리 테스트

---

### 1.2 DBManager 예외 처리 세분화
**파일**: `modules/core/db_manager.py`
**심각도**: Critical
**예상 시간**: 6시간

**현재 문제**:
- 모든 예외를 `except Exception`으로 동일 처리
- SQL 에러 vs 파일 시스템 에러 구분 불가
- 트랜잭션 중첩 상황 특수 처리 부재

**개선 내용**:
- [ ] 예외 타입별 분리: `sqlite3.IntegrityError`, `sqlite3.OperationalError`, `IOError`
- [ ] 트랜잭션 상태별 복구 전략 (nested_transaction)
- [ ] Exception 체인 보존 (`raise ... from e`)
- [ ] 에러 심각도 분류 (CRITICAL/HIGH/WARN)

**검증 방법**:
- DB 파일 권한 오류 시뮬레이션
- 동시 접근 충돌 테스트

---

### 1.3 Memory Engine ChromaDB 초기화 실패 처리
**파일**: `modules/core/memory_engine.py`
**심각도**: High
**예상 시간**: 3시간

**개선 내용**:
- [ ] `collection` None 체크를 모든 접근 시점에 추가
- [ ] 초기화 실패 플래그 (`has_valid_memory`) 유지
- [ ] 메모리 없을 때 fallback 전략 명시 (빈 컨텍스트 반환)

---

## Phase 2: 데이터 검증 및 로깅 (P2-P3)

### 2.1 MartialManager 타입 안전성 강화
**파일**: `modules/core/martial_manager.py`
**심각도**: High
**예상 시간**: 3시간

**개선 내용**:
- [ ] 프로퍼티 접근마다 단계별 None 체크
- [ ] 특수값 검사 (NaN, inf) 일관화
- [ ] guard 모듈 주입 검증 (초기화 시점)

---

### 2.2 ProjectContext 데이터 로드 검증
**파일**: `modules/core/project_manager.py`
**심각도**: High
**예상 시간**: 3시간

**개선 내용**:
- [ ] `load_all_anchors()` 실패 처리 (empty dict 반환 보장)
- [ ] anchors 타입 검증 (`isinstance(anchors, dict)`)
- [ ] 중첩 `.get()` 헬퍼 함수 도입

---

### 2.3 로깅 시스템 표준화
**파일**: `main_a.py`, 전체 modules/
**심각도**: High
**예상 시간**: 8시간

**현재 문제**:
- `print()` 311개소 혼재
- 로그 레벨 구분 없음
- 세션 로그 파일 없음

**개선 내용**:
- [ ] Python `logging` 모듈 또는 Rich logging 확장 도입
- [ ] 로그 레벨 정의: DEBUG/INFO/WARNING/ERROR/CRITICAL
- [ ] 파일 + 콘솔 dual output
- [ ] 세션 로그 저장 (`projects/{project}/logs/session_{timestamp}.log`)
- [ ] `print()` → `logger.info()` 마이그레이션

**로그 포맷**:
```
[2026-01-29 14:30:15] [INFO] [Stage4] 제 5화 집필 시작 (model=gemini-3-pro-preview)
[2026-01-29 14:31:22] [WARN] [Writer] 패턴 반영 부족, 재시도 1/3
[2026-01-29 14:32:45] [ERROR] [Director] 검수 실패: 서사 정체 감지
```

---

### 2.4 성능 메트릭 수집
**파일**: 신규 `modules/core/metrics_collector.py`
**심각도**: Medium
**예상 시간**: 4시간

**수집 항목**:
- [ ] 에이전트별 호출 횟수/재시도 횟수
- [ ] 응답 시간 (P50, P90, P99)
- [ ] 토큰 사용량 (input/output)
- [ ] API 비용 추정치

---

## Phase 3: 테스트 인프라 구축 (P5) ✅ COMPLETE

### 3.1 테스트 스위트 생성 ✅
**파일**: 신규 `tests/` 디렉토리
**상태**: 완료

**테스트 파일 구조**:
```
tests/
├── __init__.py              ✅
├── conftest.py              ✅ pytest fixtures (25+ fixtures)
├── test_db_manager.py       ✅ CRUD, 트랜잭션 (15 tests)
├── test_martial_manager.py  ✅ 타입 안전성 (20 tests)
├── test_validation.py       ✅ TIER 1/2/3 (25 tests)
├── test_agents.py           ✅ mock API 기반 (20 tests)
├── test_integration.py      ✅ E2E 시나리오 (15 tests)
└── test_edge_cases.py       ✅ 엣지 케이스 (30 tests)
```

**테스트 케이스**:
- [x] DBManager: CRUD 연산 15케이스
- [x] MartialManager: 타입 안전성 20케이스
- [x] Validation: 각 TIER별 25케이스
- [x] Agents: mock 응답 기반 20케이스
- [x] Integration: Phase 0 → Stage 4 흐름 15케이스
- [x] EdgeCases: 극단값, 동시성, 복구 30케이스

---

### 3.2 엣지 케이스 테스트 ✅
**상태**: 완료

**테스트 시나리오**:
- [x] 극단값: 0자 원고, 999999자, Unicode 특수문자
- [x] DB 손상 복구: SQLite 파일 손상 후 복구
- [x] ChromaDB lock: 동시 접근 시뮬레이션
- [x] Stage 1 스킵 후 Stage 2 호환성
- [x] 네트워크 타임아웃 (API 지연)

---

### 3.3 CI/CD 설정 ✅
**파일**: `.github/workflows/test.yml`
**상태**: 완료

**추가 파일**:
- `requirements.txt` - 의존성 목록
- `pytest.ini` - pytest 설정

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt pytest pytest-cov
      - name: Run tests
        run: pytest tests/ --cov=modules --cov-report=xml
```

---

## Phase 4: 성능 및 UX 최적화 (P4, P7-P8) ✅ COMPLETE

### 4.1 Writer/Architect 중복 에스케이프 제거 ✅
**파일**: `modules/core/escape_utils.py` (신규), `modules/domain/agents/base_agent.py`
**상태**: 완료

**개선 내용**:
- [x] 중앙화된 에스케이프 유틸리티 모듈 (`escape_utils.py`)
- [x] 중복 에스케이프 자동 방지 (`is_already_escaped` 체크)
- [x] 에스케이프 필요 여부 사전 확인 (`needs_escape`)
- [x] 배치 에스케이프 지원 (`escape_batch`)
- [x] JSON 직렬화 + 에스케이프 통합 (`escape_json_dump`)

---

### 4.2 LoreManager N+1 쿼리 해결 ✅
**파일**: `modules/core/lore_manager.py`
**상태**: 완료

**개선 내용**:
- [x] LRU 캐시 기반 로어 인덱스 (`_lore_index`)
- [x] TTL 기반 캐시 무효화 (5분)
- [x] DB LIKE 쿼리 직접 검색 (`get_lore_by_db_search`)
- [x] 컨텍스트 길이 제한 (2000자)
- [x] 최대 결과 수 제한 (10개)
- [x] 키워드 추출 최적화 (`_extract_keywords_from_context`)

---

### 4.3 에러 메시지 친절화 ✅
**파일**: `modules/core/error_helper.py` (신규)
**상태**: 완료

**개선 내용**:
- [x] 30+ 에러 코드 정의 (DB, API, File, Validation, Memory, Config, Agent)
- [x] 각 에러별 해결책 및 문서 링크 제공
- [x] 예외 자동 분류 (`classify_exception`)
- [x] 심각도 레벨 지원 (DEBUG ~ CRITICAL)
- [x] UI 통합 지원 (`print_error(code, info, ui)`)

**예시**:
```python
from modules.core.error_helper import handle_exception
handle_exception(e, "DB 저장 중 오류", ui)
# 출력: [DB001] 데이터베이스 연결에 실패했습니다
#       상세: DB 저장 중 오류: sqlite3.OperationalError...
#       해결책: 프로젝트 폴더 권한을 확인하고...
#       문서: docs/troubleshooting.md#db-connection
```

---

### 4.4 진행상황 표시 개선 ✅
**파일**: `modules/core/progress_manager.py` (신규)
**상태**: 완료

**개선 내용**:
- [x] Rich 통합 진행률 표시 (fallback: 텍스트 기반)
- [x] 스테이지별 진행 추적 (Phase 0 ~ Stage 4)
- [x] 예상 소요 시간 계산 (`get_estimated_time`)
- [x] 에피소드별 이력 관리
- [x] 성공률/재시도 통계
- [x] 테이블 형식 요약 출력 (`print_summary`)

**사용법**:
```python
from modules.core.progress_manager import start_stage, update_stage, complete_stage

start_stage("stage4", total_items=50)
for ep in range(1, 51):
    # 작업 수행
    update_stage("stage4")
complete_stage("stage4", success=True)
```

---

## 일정 계획

| Phase | 작업 | 예상 시간 | 담당 | 완료 기준 |
|-------|------|----------|------|----------|
| **Phase 1** | Critical 안정화 | 16시간 | - | 무한루프 0건, 데이터 손실 0건 |
| **Phase 2** | 데이터검증/로깅 | 18시간 | - | 타입에러 0건, 로그 표준화 100% |
| **Phase 3** | 테스트 인프라 | 20시간 | - | 커버리지 70%, CI/CD 가동 |
| **Phase 4** | 성능/UX | 14시간 | - | API 비용 20% 절감, UX 개선 |

**총 예상 시간**: 68시간 (약 8-9 작업일)

---

## 성공 지표 (KPI)

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|----------|
| 시스템 안정성 | 90% | 98% | 오류 발생률 (에피소드당) |
| 테스트 커버리지 | 20% | 70% | pytest-cov 리포트 |
| 평균 재시도 횟수 | 2.3회 | 1.5회 | 메트릭 수집기 |
| API 비용 | 기준치 | -20% | 토큰 사용량 추적 |
| 에러 해결 시간 | 30분 | 10분 | 로그 기반 진단 시간 |

---

## 위험 요소 및 완화 전략

| 위험 | 영향 | 확률 | 완화 전략 |
|------|------|------|----------|
| 로깅 마이그레이션 중 버그 | Medium | 30% | 점진적 마이그레이션, 병행 운영 |
| 테스트 작성 시간 초과 | Low | 40% | 우선순위 테스트만 먼저 작성 |
| 성능 최적화 부작용 | Medium | 20% | A/B 테스트 후 적용 |
| 기존 프로젝트 호환성 | High | 10% | 마이그레이션 스크립트 제공 |

---

## 체크리스트

### Phase 1 시작 전
- [ ] 현재 코드 백업 (git tag v43-stable)
- [ ] 테스트 프로젝트 준비 (소규모 bible)
- [ ] 롤백 계획 수립

### 각 Phase 완료 후
- [ ] 수동 테스트 실행 (Stage 0 → Stage 4)
- [ ] 기존 프로젝트 호환성 확인
- [ ] 변경 사항 문서화

---

## 참고 문서

- `CLAUDE.md` - 코드베이스 가이드
- `AI_STRATEGY_COMPLETE.md` - AI 전략 현황
- `CODE_REVIEW_COMPLETE.md` - 이전 코드 리뷰 결과
- `DEEP_INSPECTION_COMPLETE.md` - 심층 검사 결과

---

*이 계획서는 우선순위와 리소스 상황에 따라 조정될 수 있습니다.*
