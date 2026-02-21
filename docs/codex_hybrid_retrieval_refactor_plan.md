# Hybrid Retrieval 보강 수정 플랜 (Refactor-level)

- 작성일: 2026-02-21
- 대상: `VecMemory` 기반 검색 경로(Stage2/Stage4)
- 목적: 의미(벡터) 편중 검색을 하이브리드(의미 + 키워드)로 강화

## 1) 리팩토링급 여부 판정

결론: **리팩토링급 + 기능 확장**.

판정 근거:
- 검색 코어 변경: `modules/core/vec_memory.py`
- DB 스키마 확장(FTS): `modules/core/db_manager.py`
- 핵심 호출 경로 교체: `modules/core/stage2_preflight.py`, `modules/core/stage4_context_builder.py`
- 회귀/품질 테스트 추가 필요: `tests/test_vec_memory.py`, `tests/test_stage2_preflight.py`, `tests/test_stage4_context_builder.py`

영향도:
- 코드 리스크: 중간
- 데이터 리스크(DB): 중간
- 운영 리스크: 중간(플래그 기반 점진 전환으로 완화 가능)

## 2) 현재 상태 요약

- 메인 검색은 벡터 KNN 중심.
- 키워드 기반은 `SemanticPlotGuard` fallback 중심이며 메인 컨텍스트 검색 경로에는 직접 결합되지 않음.
- Stage2/Stage4의 컨텍스트 주입은 벡터 결과 위주.

## 3) 목표 상태

- 메인 retrieval을 `dense + sparse + fusion` 구조로 전환.
- 임베딩 실패/비활성 시에도 sparse 검색으로 품질 저하를 완화.
- Stage2/Stage4에서 동일한 하이브리드 API를 사용.
- 동작 모드를 설정 플래그로 제어(`dense | hybrid | sparse`).

## 4) 단계별 수정 플랜

### P0. 베이스라인 고정 (반나절)

작업:
- 현재 retrieval 출력 스냅샷 테스트 추가.
- Stage2/Stage4에서 기존 동작을 고정하는 회귀 테스트 추가.

산출물:
- 기존 동작 회귀 기준선 확보.

완료 기준:
- 기존 테스트 + 신규 스냅샷 테스트 통과.

### P1. 인터페이스 확장 (1일)

작업:
- `VecMemory`에 `retrieve_hybrid_context()` 추가.
- 기존 `retrieve_high_res_context()`, `retrieve_multi_query_context()`는 유지(호환성 보장).
- 내부 공통 결과 포맷/정렬 유틸 추가.

대상 파일:
- `modules/core/vec_memory.py`

완료 기준:
- 기존 API 호출 경로 무변경 상태에서 신규 API 단위 테스트 통과.

### P2. Sparse 축 도입 (1~2일)

작업:
- `episode_meta` 기반 FTS 테이블 도입(예: `episode_fts`).
- 저장 시 벡터/메타와 함께 FTS 문서 upsert.
- DB 초기화/마이그레이션 경로에 FTS 생성 포함.

대상 파일:
- `modules/core/db_manager.py`
- `modules/core/vec_memory.py`

완료 기준:
- 신규/기존 DB 모두 FTS 정상 생성.
- 저장/업데이트/삭제 시 FTS 동기화 유지.

### P3. Fusion 랭킹 적용 (1~2일)

작업:
- dense 결과와 sparse 결과를 RRF(Reciprocal Rank Fusion)로 결합.
- dedup 및 편중 방지 규칙 추가(동일 arc 과집중 완화).
- 최종 컨텍스트 생성 시 근거 필드(에피소드/매칭소스) 포함.

대상 파일:
- `modules/core/vec_memory.py`

완료 기준:
- dense-only 대비 recall 저하 없음.
- 중복/편중률 개선 확인.

### P4. 호출부 전환 + 설정 플래그 (1일)

작업:
- Stage2/Stage4 호출을 하이브리드 API로 전환.
- 설정값 추가:
- `retrieval_mode`
- `dense_k`
- `sparse_k`
- `rrf_k`
- `max_results`
- 초기 기본값은 `dense` 유지 후 점진 전환.

대상 파일:
- `modules/core/stage2_preflight.py`
- `modules/core/stage4_context_builder.py`
- `config/settings/validation.yaml`

완료 기준:
- 플래그별 경로(`dense|hybrid|sparse`) 테스트 통과.
- 운영 기본값 유지 상태에서 회귀 없음.

### P5. 관측성/품질 게이트 (1일)

작업:
- 로깅: query, dense hit 수, sparse hit 수, fusion 상위 결과.
- 지표: Recall@K, MRR, 중복률, 지연시간.
- 통합 테스트 보강.

대상 파일:
- `tests/test_vec_memory.py`
- `tests/test_stage2_preflight.py`
- `tests/test_stage4_context_builder.py`

완료 기준:
- 회귀 테스트 + 성능 기준 통과.

## 5) 리스크와 완화

- 리스크: DB 스키마 변경으로 마이그레이션 불안정 가능.
- 완화: idempotent DDL, startup self-check, 실패 시 rollback + 기존 경로 유지.

- 리스크: retrieval 품질 변동.
- 완화: 초기 기본값 `dense`, 실험 플래그로 점진 전환.

- 리스크: 임베딩 API 장애 시 품질 급락.
- 완화: sparse-only 자동 폴백, 비차단 정책 유지.

## 6) 롤아웃 전략

1. 배포 1차: 코드 포함, 기본 모드 `dense`.
2. 배포 2차: 제한 환경에서 `hybrid` 활성.
3. 배포 3차: 지표 확인 후 기본 모드를 `hybrid`로 상향.
4. 이상 징후 시 즉시 `dense` 복귀.

## 7) 완료(Definition of Done)

- `retrieve_hybrid_context()`가 Stage2/Stage4 메인 경로에서 사용됨.
- dense/sparse/fusion 모드가 설정값으로 전환 가능함.
- 저장/삭제/재동기화 시 FTS 일관성이 유지됨.
- 회귀 테스트, 통합 테스트, 성능 지표 기준을 모두 만족함.
- 장애 시 sparse-only 또는 dense-only로 자동 복귀 가능함.
