# Codex & Opus 문서 현황 파악 리포트

작성일: 2026-02-21
목적: 프로젝트 루트 및 `docs` 폴더에 산재된 `codex_*.md` 및 `opus_*.md` 파일들의 성격과 역할을 분류하여 쉽게 파악하기 위함입니다.

---

## 🏛️ 1. 아키텍처 및 코어 리팩토링 기획안 (Architecture & Refactoring Plans)
시스템의 근본적인 구조 개선, 메모리 최적화, 검색 성능 향상을 위한 청사진 문서들입니다.

- **`codex_canon_os_v2_plan.md`**
  - **내용 요약**: 설정 데이터(Canon)의 전체 구조를 V2로 업그레이드하고 운영 체제(OS) 관점에서의 관리를 설계한 개발 플랜.
- **`codex_hybrid_retrieval_refactor_plan.md`**
  - **내용 요약**: 벡터 매칭(ChromaDB/sqlite-vec 등)과 관계형 DB 방식을 혼합한 하이브리드 검색 시스템 도입 및 리팩토링 설계안.
- **`codex_memory_roi_boost_plan.md`**
  - **내용 요약**: 대형 언어 모델(LLM)의 제한된 컨텍스트 윈도우(메모리)를 가장 효율적으로 쓰기 위해, 프롬프트의 토큰 비용 대비 성능(ROI)을 극한으로 끌어올리는 최적화 계획.
- **`codex_stage_canon_memory_plan.md`**
  - **내용 요약**: 파이프라인의 각 Stage마다 상태값을 어떻게 유지하고, 메모리를 넘겨줄지 정리한 플랜.

---

## 🛡️ 2. 컴플라이언스 및 복구력 향상 계획 (Resilience & Retry Plans)
에러 발생 시 파이프라인이 중단되지 않고 스스로 회복하거나 재시도하는 메커니즘을 정의한 문서들입니다.

- **`codex_patch_retry_extension_plan.md`**
  - **내용 요약**: 코드나 데이터 패치 적용 중 오류 발생 시 재시도(Retry) 로직 규칙을 개선하고 확장하는 계획.
- **`codex_postpatch_sweep_expansion_plan.md`**
  - **내용 요약**: 패치가 성공적으로 적용된 후, 다른 연관 모듈들에 문제가 생기지는 않았는지 점검하는 범위(Sweep)를 넓히려는 계획.

---

## 🧪 3. 100회 스트레스 테스트 기획 (Sweep 100 & Integrity Tests)
특정 모듈이나 로직이 가혹한 반복 실행 환경에서도 정상 작동하는지(무결성/멱등성) 검증하는 대규모 테스트 계획입니다.

- **`codex_patch_retry_determinism_sweep100_plan.md`**
  - **내용 요약**: 재시도 로직을 수없이 반복해도 실행 결과가 랜덤하게 튀지 않고 결정론적(Determinism)으로 일관되게 나오는지 100회 점검하는 플랜.
- **`codex_canon_field_integrity_sweep100_plan.md`**
  - **내용 요약**: 주요 데이터 필드(Canon Field) 정보가 연속 생성/수정 작업 중에도 손상되지 않는지(무결성) 100회 스트레스 테스트.
- **`codex_resume_replay_idempotency_sweep100_plan.md`**
  - **내용 요약**: 작업 중단 후 다시 시작(Resume)하거나, 과거 시점으로 돌아가 다시 실행(Replay)할 때 완벽하게 같은 상태로 복원되는지(멱등성/Idempotency) 100회 테스트.
- **`codex_prompt_budget_fidelity_sweep100_plan.md`**
  - **내용 요약**: LLM 프롬프트에 책정된 토큰 할당량(Budget)을 모듈들이 초과하지 않고 정교하게 지키는지(Fidelity) 100회 검증.
- **`codex_observability_rca_sweep100_plan.md`**
  - **내용 요약**: 장애가 발생했을 때 남는 로그와 추적 데이터(Observability)만으로 정확한 근본 원인 분석(RCA)이 가능한지 100회 시뮬레이션.

---

## 📋 4. 디버깅 이슈 및 런타임 인벤토리 (Issues & Runtime Inventory)
주요 에이전트의 현재 작동 상태나 발견된 버그들을 문서화한 목록입니다.

- **`codex_director_issues.md`**
  - **내용 요약**: 검수자 역할을 하는 Director 에이전트와 관련된 주요 문제 및 버그 사항 정리.
- **`codex_pydantic_abc_baseline_report_2026-02-20.md`**
  - **내용 요약**: Pydantic 데이터 모델과 추상 기반 클래스(ABC)의 구조 안정을 체크한 베이스라인 점검 리포트 (날짜: 2026-02-20).
- **`codex_major_agents_runtime_inventory_2026-02-20.md`**
  - **내용 요약**: Writer, Analyst, Director 등 전체 주요 에이전트가 런타임(메모리)에서 어떻게 구성되어 돌고 있는지 정리한 인벤토리 문서 (날짜: 2026-02-20).

---

## 🔍 5. 종합 코드 감사 및 실행 지시서 (Comprehensive Audits & Execution Orders)
AI가 코드베이스 전반을 오디트(점검)한 결과이거나, 특정 테스팅/점검 프레임워크를 구동하기 위한 순서와 지시를 담은 문서입니다.

- **`opus_tf_comprehensive_audit_2026-02-20.md`**
  - **내용 요약**: Opus 모델이 코드베이스 전반을 스캔하고 남긴 포괄적인 종합 오디트 리포트 (날짜: 2026-02-20).
- **`opus_truncation_manual_audit_order_2026-02-20.md`**
  - **내용 요약**: 특정 생성 결과물의 끝부분이 잘리는 현상(Truncation)을 해결하기 위해 수동으로 점검해야 할 순서를 남긴 지시서.
- **`opus_tf_sweep4x10_execution_order_2026-02-20.md`**
  - **내용 요약**: '4개의 테스트 패키지 x 10회 반복' 프레임워크를 어떤 순서로 돌려야 할지 나열한 실행 명령서.
