# CODEX ORDER — 전 스테이지 크로스컷 결함 전수조사

작성일: 2026-02-27
기준 커밋: `394bc9a`
테스트 기준선: **2753 passed**
조사 방식: **읽기 전용. 코드 수정 금지. 결함 문서화만.**

---

## 임무 정의

글도비 AI 웹소설 생성 파이프라인(Stage 0→2→3→4)의 전 모듈을 수동 코드 검사한다.
목표는 **크로스컷(cross-cutting) 결함** — 단일 기능 버그가 아닌, 여러 스테이지·모듈에 걸쳐
동일한 패턴으로 반복되는 구조적 취약점 — 을 발굴해 보고서로 문서화하는 것이다.

**출력물**: 이 문서 아래에 결함 목록을 작성한다.
**코드 변경 없음**: `Read` 도구로 파일을 직접 읽는다. `Edit` / `Write` / `Bash` 금지.
**자동 검색 도구 사용 금지**: `Grep` / `Glob` / `rg` / `freg` 등 패턴 수집 도구 사용 금지.
코드를 눈으로 읽어가며 판단한다. 도구가 찾아준 결과가 아니라 사람이 읽은 결과만 기록한다.

---

## 조사 대상 파일 목록

### Stage 0 (초기 설정 / Bible 추출)
```
modules/core/stage0/__init__.py
modules/core/stage0/story_expander.py
modules/core/stage0/reverse_expander.py
modules/core/stage0/style_extractor.py
modules/core/stage0/preset_registry.py
modules/core/stage01_helpers.py
```

### Stage 2 (Arc / Blueprint 오케스트레이션)
```
modules/core/stage2_orchestrator.py
modules/core/stage2_preflight.py
modules/core/stage2_finalizer.py
modules/core/stage2_validation_pipeline.py
modules/core/stage2_optimizer.py
modules/core/stage2_context.py
```

### Stage 3 (Blueprint 오케스트레이션)
```
modules/core/stage3_orchestrator.py
modules/core/stage3_context.py
```

### Stage 4 (원고 생성)
```
modules/core/stage4_orchestrator.py
modules/core/stage4_context_builder.py
modules/core/stage4_interview_round.py
modules/core/stage4_post_processor.py
modules/core/stage4_context.py
modules/core/stage4_types.py
```

### Domain Agents (에이전트 레이어)
```
modules/domain/agents/base_agent.py
modules/domain/agents/chief_writer.py
modules/domain/agents/chief_writer_context.py
modules/domain/agents/chief_writer_prompts.py
modules/domain/agents/chief_writer_quality.py
modules/domain/agents/director.py
modules/domain/agents/director_ensemble.py
modules/domain/agents/director_prompts.py
modules/domain/agents/director_continuity.py
modules/domain/agents/director_grading.py
modules/domain/agents/director_caching.py
modules/domain/agents/director_auditor.py
modules/domain/agents/manager.py
modules/domain/agents/analyst.py
modules/domain/agents/analyst_prompt_api.py
modules/domain/agents/four_phase_arc_generator.py
modules/domain/agents/arc_ensemble.py
modules/domain/agents/arc_critic.py
modules/domain/agents/arc_corrector.py
modules/domain/agents/arc_draft_validator.py
modules/domain/agents/unified_arc_validator.py
modules/domain/agents/three_phase_blueprint_generator.py
modules/domain/agents/blueprint_ensemble.py
modules/domain/agents/blueprint_constraint_compiler.py
modules/domain/agents/continuity_arc.py
modules/domain/agents/continuity_blueprint.py
modules/domain/agents/continuity_manuscript.py
modules/domain/agents/continuity_inspector.py
modules/domain/agents/continuity_tracker.py
modules/domain/agents/critic.py
modules/domain/agents/weaver.py
modules/domain/agents/writer.py
modules/domain/agents/manuscript_validator.py
modules/domain/agents/state_tracker.py
modules/domain/agents/state_tracker_npc.py
modules/domain/agents/state_tracker_plots.py
modules/domain/agents/state_tracker_financial.py
modules/domain/agents/state_extractor.py
modules/domain/agents/preflight_checker.py
modules/domain/agents/consensus_validator.py
modules/domain/agents/state_locked_arc_generator.py
modules/domain/agents/block_enricher.py
modules/domain/agents/negative_example_injector.py
modules/domain/agents/constraint_compiler.py
```

### Core 공통 모듈
```
modules/core/db_manager.py
modules/core/vec_memory.py
modules/core/context_advisor.py
modules/core/truth_gate.py
modules/core/fact_ledger.py
modules/core/foreshadow_tracker.py
modules/core/world_state.py
modules/core/character_voice.py
modules/core/cross_agent_verifier.py
modules/core/constants.py
modules/core/semantic_plot_guard.py
modules/core/repetition_guard.py
modules/core/writer_prompt_builders.py
modules/core/writer_template.py
modules/core/karma_service.py
modules/core/lore_manager.py
modules/core/error_helper.py
```

### Validation 레이어
```
modules/validation/blocking_validator.py
modules/validation/blocking_validator_consistency_checks.py
modules/validation/blocking_validator_entity_checks.py
modules/validation/blocking_validator_scene_checks.py
modules/validation/advisory_validator.py
modules/validation/consistency_validator.py
modules/validation/continuity_validator.py
modules/validation/pre_llm_validator.py
modules/validation/validation_orchestrator.py
modules/validation/scoring_validator.py
modules/validation/batch_validator.py
modules/validation/threshold_helper.py
```

### Genre Guards
```
modules/core/genre_guards/base_guard.py
modules/core/genre_guards/work_guard.py
modules/core/genre_guards/style_guard.py
modules/core/genre_guards/__init__.py
```

### Config / Models
```
config/system.yaml
config/models.yaml
config/settings/validation.yaml
modules/models/arc.py
modules/models/blueprint.py
modules/models/npc.py
modules/models/manuscript.py
modules/protocols/agents.py
modules/protocols/app_services.py
modules/protocols/db_repository.py
modules/protocols/validators.py
```

---

## 크로스컷 결함 카테고리 (분류 기준)

각 결함은 아래 카테고리 중 하나로 분류한다. **복수 카테고리 허용**.

| 코드 | 카테고리 | 설명 |
|------|----------|------|
| `ERR` | Error Propagation | `except Exception` 무음 삼킴 → 상위로 전파 차단 |
| `SLT` | Silent Fail | 로그 없이 빈 값/None/`[]`/`{}` 반환 |
| `RSC` | Resource Leak | DB 커넥션/파일핸들/쓰레드 미해제 |
| `CTR` | Contract Violation | Protocol/ABC 구현 누락 또는 시그니처 불일치 |
| `STA` | State Inconsistency | 롤백 미완료, 부분 업데이트, 더티 상태 |
| `LLM` | LLM Parse | LLM 응답 파싱 실패 시 fallback 없거나 오염 데이터 흘림 |
| `TXN` | Transaction Safety | 원자성 미보장, commit 누락, partial write |
| `INP` | Input Validation | None/빈문자열/잘못된 타입 미검증 |
| `CON` | Concurrency | 락 미보유 공유 상태, RLock 미적용 |
| `CFG` | Config Hardcode | YAML 외부화해야 할 상수가 코드에 박힘 |
| `DED` | Dead Code | 호출 경로 없는 함수/분기 |
| `LEK` | Cross-Agent Leak | 에이전트 간 상태/메모리 오염 전파 |
| `ORD` | Ordering / Race | 초기화 순서 의존, 타이밍 경합 |

---

## 심각도 기준

| 등급 | 기준 |
|------|------|
| **P0** | 데이터 손실, 런타임 크래시, 원고 오염, 롤백 실패 |
| **P1** | 잘못된 결과가 조용히 통과, 논리 오류, 누적 상태 오염 |
| **P2** | 코드 냄새, 유지보수 리스크, 경미한 비효율 |

---

## 조사 방법론

### 원칙 — 순수 파일 정독

`Read` 도구로 파일을 열어 처음부터 끝까지 라인 단위로 읽는다.
자동화 도구(Grep/rg/freg)로 패턴을 수집하지 않는다.
눈으로 읽은 코드에서 직접 판단한다.

### 파일 정독 시 체크 항목

각 파일을 읽으면서 아래 질문에 답한다:

1. **try/except 범위** — 범위가 너무 넓어서 실제 오류를 삼키고 있는가?
   예: 100줄 짜리 try 블록 → `except Exception: pass`
2. **LLM 응답 접근** — `response.text`, `json.loads()`, `result.get()` 이후에
   None/KeyError 가능성을 체크하는가? fallback이 있는가?
3. **DI 슬롯 사용** — `self.ctx`, `self.app`, `self.tracker`, `self._db` 등
   None인 채로 `.method()` 체인을 타는 경우가 있는가?
4. **DB 쓰기** — `cursor.execute()` / `conn.execute()`가 트랜잭션 블록 밖에서
   단독 호출되는가? commit 누락은 없는가?
5. **공유 상태 갱신** — `self._cache[key] = value` 형태의 dict 갱신이
   Lock 없이 일어나는가?
6. **함수 시그니처** — Protocol에 선언된 메서드와 구현체의 시그니처가 맞는가?
   반환 타입이 일치하는가?
7. **ThreadPoolExecutor** — `future.result()` 호출 시 예외 처리가 있는가?
   타임아웃이 설정돼 있는가?
8. **반환값 전파** — 함수가 None을 반환했을 때 호출측이 None을 그대로
   다음 단계로 넘기는가?

### 크로스컷 판정 기준

동일한 결함 패턴이 **3개 이상** 파일에서 반복되면 크로스컷 이슈로 묶는다.
2개 이하면 각 파일의 단일 이슈로 기록한다.

---

## 출력 형식 (결함 항목)

```
### [XC-NNN] 제목 (카테고리 코드, 심각도)

**패턴**: 반복되는 코드 패턴 1줄
**발생 파일**:
- `path/to/file.py:LINE` — 설명
- `path/to/file2.py:LINE` — 설명

**근본 원인**: 한 줄로
**영향**: 어떤 상황에서 무슨 일이 생기는지
**수정 방향**: 한 줄로 (구현 명세 아님, 방향만)
```

단일 파일 결함도 같은 형식. `발생 파일`이 1개면 단일 이슈.

---

## 금지 사항

- **코드 수정 금지** — `Read` 도구로 읽기만. `Edit` / `Write` / `Bash` 절대 금지.
- **자동 수집 도구 금지** — `Grep` / `Glob` / `rg` / `freg` 사용 금지.
  도구가 "이 패턴이 N개 파일에 있다"고 찾아준 결과를 그대로 결함으로 기록하지 말 것.
  반드시 해당 라인을 `Read`로 직접 읽고 문맥을 확인한 뒤 판단한다.
- **추측 결함 금지** — `Read`로 직접 읽어 확인한 것만 보고.
- **오탐 금지** — "가능성 있음" 수준이면 P2로 기술하거나 제외.
- **기존 패치 재보고 금지** — CLAUDE.md의 완료 목록(TF-1~TF-19, SC-0~6 등) 항목은 확인 후 생략.
- **테스트 파일 조사 금지** — `tests/` 디렉터리는 대상 아님.

---

## 특별 주목 영역 (이전 조사에서 반복된 패턴)

아래 영역은 과거 전수조사(4차, 5차)에서 P0/P1이 집중 발생했다.
이번에도 동일 패턴이 잔존하는지 반드시 확인할 것.

### A. LLM 파싱 오류 전파
- `base_agent.py` `_ask()` 반환값이 str/None 혼용 — 호출측 None 체크 일관성
- `json.loads()` 호출 후 `except json.JSONDecodeError` 없이 KeyError 발생 가능
- Arc/Blueprint LLM 응답에서 필수 키 누락 시 fallback 없이 `None["key"]` 크래시

### B. 롤백 원자성
- `stage4_post_processor.py` PASS 후처리 중 일부만 성공하고 실패 시 롤백 미완료
- `StateTracker.rollback_to_episode()` — NPC이력/WorldState/FactLedger 3개 동기화 누락 여부
- `db_manager.py` `commit_episode_factory()` 예외 시 partial write 잔류 여부

### C. DI 슬롯 None 크래시
- Stage4Context / Stage2Context 슬롯이 런타임에 None인 채로 메서드 호출
- `self.ctx.current_project` 가 None일 때 `.db.` 체인 크래시
- `getattr(self, "_db", None)` 패턴이 일부 파일에만 적용돼 있음

### D. 락 없는 캐시 공유
- `base_agent.py` `_context_cache` — 멀티스레드 시 RLock 미보유 갱신
- `world_state.py` `_canonical_cache` — 무효화 타이밍 경합
- `vec_memory.py` in-memory fallback dict — 쓰레드 안전성

### E. 장르 가드 체인 단락
- `base_guard.py` → `work_guard.py` → `style_guard.py` 체인에서 중간 실패 시 후속 가드 스킵 여부
- Guard 반환 타입 불일치 — `GuardResult` vs `dict` vs `bool` 혼용

### F. FactLedger / TruthGate 우회
- Director가 PASS를 내리기 전에 TruthGate 검사를 항상 거치는지
- `fact_ledger.py` append 실패 시 무음 통과

### G. Stage2 앙상블 피드백 루프
- `arc_ensemble.py` 앙상블 결과가 None/빈 dict일 때 finalizer가 처리하는지
- `stage2_validation_pipeline.py` 검증 실패 시 재시도 루프 탈출 조건

### H. VecMemory / DB 이중 기록
- `vec_memory.py` FTS5+RRF 하이브리드 경로에서 중복 삽입 가능성
- `save_episode_bible()` 재호출 시 upsert vs insert 혼용

---

## 출력 문서 구조

조사 완료 후 아래 구조로 결과를 기술한다.

```
# 전 스테이지 크로스컷 결함 전수조사 결과

작성일: YYYY-MM-DD
조사 파일 수: N개
발견 결함 수: P0 X건 / P1 Y건 / P2 Z건

---

## 크로스컷 이슈 (복수 파일 반복 패턴)
[XC-001] ...
[XC-002] ...

## Stage 0 단일 이슈
[S0-001] ...

## Stage 2 단일 이슈
[S2-001] ...

## Stage 3 단일 이슈
[S3-001] ...

## Stage 4 단일 이슈
[S4-001] ...

## Domain Agents 단일 이슈
[AG-001] ...

## Core 공통 단일 이슈
[CO-001] ...

## Validation 레이어 단일 이슈
[VA-001] ...

## 확인했으나 결함 없음 (조사 완료 확인용)
- file.py — 이상 없음
```

---

## 우선순위 조사 순서

1. `modules/domain/agents/base_agent.py` — 모든 에이전트의 기반, 크로스컷 최다 발생
2. `modules/core/db_manager.py` — 트랜잭션 / 락 / 인덱스
3. `modules/core/stage4_post_processor.py` — 롤백 원자성
4. `modules/domain/agents/state_tracker.py` + `state_tracker_npc.py` — 상태 일관성
5. `modules/core/stage2_orchestrator.py` + `stage2_validation_pipeline.py` — 앙상블 실패 처리
6. `modules/core/truth_gate.py` + `modules/core/fact_ledger.py` — TruthGate 우회
7. `modules/core/vec_memory.py` — 하이브리드 검색 / 중복 삽입
8. `modules/core/world_state.py` — 캐시 무효화 경합
9. 나머지 파일 순차 조사

---

## 참고 컨텍스트

- **대원칙**: Python은 수집만, 판단은 LLM. Python이 팩트를 자동 수정하면 안 됨.
- **Director 주권**: Chief Writer·Analyst는 초안만, 합격/불합 판정은 Director만.
- **DB SSOT**: `project_data.db` 단일 파일. VecMemory도 이 DB 공유.
- **DI 패턴**: Stage2(44슬롯), Stage3(19슬롯), Stage4(24슬롯) — 슬롯 None 시 크래시.
- **완료된 수정**: CLAUDE.md의 완료 목록 참조. 중복 보고 금지.
- **TruthGate**: 5개 검사 (사망NPC/아이템/장소/스킬/카르마) — advisory 모드.
- **HybridSearch**: FTS5 + RRF (TF-18 활성화) — dense/fallback/hybrid 경로.
- **Guard 체인**: GenreGuard → WorkGuard → StyleGuard 순서.

---

# 전 스테이지 크로스컷 결함 전수조사 결과

작성일: 2026-02-27  
조사 파일 수: 11개 (우선순위 1~8 경로 기준)  
발견 결함 수: P0 2건 / P1 5건 / P2 0건

범위 주의: 본 결과는 전체 목록 완주본이 아니라, 우선순위 파일(1~8 세트) 1차 정독 결과임.

---

## 크로스컷 이슈 (복수 파일 반복 패턴)

### [XC-001] 영속화 실패 비차단 처리 반복 (ERR, SLT, STA, P1)

**패턴**: DB/상태 저장 실패를 경고 로그만 남기고 계속 진행하여 상위 단계에서 실패를 감지하지 못함  
**발생 파일**:
- `modules/core/db_manager.py:1283` — `save_anchor()`가 예외를 삼키고 `False`만 반환
- `modules/core/db_manager.py:1422` — `upsert_npc_relationship_edge()` 실패를 비치명 로그로만 처리
- `modules/core/db_manager.py:1469` — `upsert_arc_dependency()` 실패를 비치명 로그로만 처리
- `modules/core/stage4_post_processor.py:595` — `save_episode_bible()` 실패를 경고 후 계속 진행
- `modules/core/stage4_post_processor.py:617` — `save_state_log_with_summary()` 실패를 경고 후 계속 진행
- `modules/core/fact_ledger.py:64` — `save()` 실패를 경고 후 무시
- `modules/core/world_state.py:69` — `save()` 실패를 에러 로그만 남기고 상위 전파하지 않음
- `modules/domain/agents/state_tracker_npc.py:1606` — 관계 엣지 DB 동기화 실패를 debug 로그로만 처리

**근본 원인**: 저장 실패를 “가용성 우선”으로 취급하면서 실패 전파 기준이 모듈별로 불일치함  
**영향**: 원고/상태/그래프/원장이 서로 다른 스냅샷으로 고정되어 장기 연속성 오류가 누적됨  
**수정 방향**: 저장 API를 중요도별(critical/advisory)로 분리하고 critical 경로는 예외 전파 + 트랜잭션 단위 보장

### [XC-002] LLM/파싱 실패 fail-open 전파 (LLM, ERR, SLT, P1)

**패턴**: 파싱/검증 실패 시 재시도·차단 대신 원본/기본값으로 진행  
**발생 파일**:
- `modules/domain/agents/base_agent.py:1123` — `_extract_json_robust()` 최외곽 `except`에서 오류를 구조화 실패 결과로만 반환
- `modules/domain/agents/state_tracker_npc.py:760` — LLM 응답 비어있으면 검증 없이 원 후보 반환
- `modules/domain/agents/state_tracker_npc.py:769` — LLM 검증 예외 시 regex 후보를 그대로 신뢰
- `modules/core/stage4_post_processor.py:446` — Manager 파싱 실패 시 기본 추출로 계속 진행
- `modules/core/stage4_post_processor.py:470` — Manager 동기 재시도까지 실패해도 후속 파이프라인 지속

**근본 원인**: 품질 보증 경계(검증 실패 시 중단/재시도 기준) 없이 fail-open을 기본 정책으로 사용  
**영향**: 미검증 상태 업데이트가 누적되어 FactLedger/WorldState/메모리 검색 정합성이 저하됨  
**수정 방향**: 핵심 필드(사망, 관계, 상태변화)에는 신뢰도 게이트를 두고 실패 시 재시도 또는 fail-closed 적용

---

## Stage 2 단일 이슈

### [S2-001] ContinuityInspector 예외 전파로 Stage2 루프 중단 가능 (ERR, P0)

**패턴**: 외부 에이전트 호출 예외가 retry 피드백으로 변환되지 않고 상위 루프로 전파됨  
**발생 파일**:
- `modules/core/stage2_validation_pipeline.py:480` — `inspect_arc()` 호출이 `try/except` 없이 실행
- `modules/core/stage2_orchestrator.py:489` — `run_validation()` 호출 자체도 보호되지 않아 예외 시 Arc 설계 루프 탈락

**근본 원인**: validation chain 내부에서 “실패를 데이터(피드백)로 환원”하는 정책이 일부 구간에만 적용됨  
**영향**: 단일 에이전트 실패로 Stage2 전체가 런타임 중단될 수 있음  
**수정 방향**: 연속성 검증 호출을 보호하고 예외를 `{"action":"retry"}` 피드백으로 표준화

---

## Stage 0 단일 이슈

- 이번 범위에서는 미조사 (우선순위 1~8 세트에 Stage 0 파일 미포함)

---

## Stage 3 단일 이슈

- 이번 범위에서는 미조사 (우선순위 1~8 세트에 Stage 3 파일 미포함)

---

## Stage 4 단일 이슈

### [S4-001] 에피소드 저장 원자성 분절 (TXN, STA, P0)

**패턴**: 동일 에피소드의 핵심/메타 데이터가 서로 다른 트랜잭션 경계에서 저장됨  
**발생 파일**:
- `modules/core/stage4_post_processor.py:199` — 원고/martial은 선행 트랜잭션으로 즉시 커밋
- `modules/core/stage4_post_processor.py:595` — Episode Bible 저장 실패를 비차단 처리
- `modules/core/stage4_post_processor.py:603` — causal_graph 저장 실패를 비차단 처리
- `modules/core/stage4_post_processor.py:617` — state_logs 저장 실패를 비차단 처리
- `modules/core/stage4_post_processor.py:669` — WorldState/FactLedger는 별도 메타 트랜잭션으로 처리

**근본 원인**: 후처리 책임이 단계별로 분리되어 에피소드 단위 단일 UoW(Unit of Work)가 깨짐  
**영향**: 원고는 저장됐지만 bible/state/world/fact가 누락된 반쪽 커밋 상태가 발생 가능  
**수정 방향**: 에피소드 확정 저장을 단일 트랜잭션/보상 트랜잭션으로 재구성

---

## Domain Agents 단일 이슈

### [AG-001] 초기 상태 복원 시 부분 추출 허용으로 레지스트리 편향 가능 (ERR, SLT, P1)

**패턴**: 다수 추출기 실패를 누적 허용하고 완료로 간주  
**발생 파일**:
- `modules/domain/agents/state_tracker.py:195` — `full_extract_from_arcs()`에서 확장 추출 실패를 경고 후 계속 진행
- `modules/domain/agents/state_tracker.py:236` — 관계/부상/이동 추출 실패도 동일하게 비차단 처리

**근본 원인**: 초기화 정확도보다 가용성을 우선하는 정책인데, 최소 성공 기준이 없음  
**영향**: 재기동/롤포워드 시 NPC/플롯 레지스트리가 부분 복원되어 이후 검증 품질이 흔들림  
**수정 방향**: 초기 로드 단계에 필수 추출 성공 임계치와 실패 누적 카운터를 도입

---

## Core 공통 단일 이슈

### [CO-001] TruthGate 경고가 메모리 저장 차단으로 연결되지 않음 (LEK, STA, P1)

**패턴**: 검증 결과가 CRITICAL이어도 저장 경로는 그대로 진행  
**발생 파일**:
- `modules/core/truth_gate.py:34` — `blocking=False` 고정(advisory only)
- `modules/core/stage4_post_processor.py:325` — 경고 출력 후 즉시 다음 단계 진행
- `modules/core/stage4_post_processor.py:361` — 검증 결과와 무관하게 VecMemory 저장 시도

**근본 원인**: 검증 모듈과 저장 모듈 간 정책 계약(차단 기준)이 정의되지 않음  
**영향**: 이미 모순으로 판정된 상태 업데이트가 장기 기억에 적재될 수 있음  
**수정 방향**: TruthGate severity(`CRITICAL`) 기반 저장 차단 또는 재검증 루프 연결

### [CO-002] VecMemory 저장 반환값 계약 미사용 (CTR, SLT, P1)

**패턴**: 저장 API가 실패를 bool로 반환해도 호출측이 검사하지 않음  
**발생 파일**:
- `modules/core/vec_memory.py:418` — `memorize_v20_episode()` 실패 시 `False` 반환
- `modules/core/vec_memory.py:470` — 저장 예외 시 rollback 후 `False` 반환
- `modules/core/stage4_post_processor.py:362` — 반환값 확인 없이 저장 성공 로그 출력

**근본 원인**: 호출측이 예외 기반 실패만 가정하고 반환값 기반 실패 경로를 누락함  
**영향**: 메모리 저장 실패가 운영 로그상 성공으로 오인되어 장애 탐지 지연  
**수정 방향**: 반환값 검사 + 실패 시 경고/재시도/상태 플래그 반영

---

## Validation 레이어 단일 이슈

- 이번 범위에서는 미조사 (우선순위 1~8 세트에 Validation 파일 미포함)

---

## 확인했으나 결함 없음 (조사 완료 확인용)

- 없음 (이번 우선순위 11개 파일에서는 모두 구조적 결함 또는 고위험 리스크 식별)
