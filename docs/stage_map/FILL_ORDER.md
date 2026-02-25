# stage_map 채우기 오더 — Codex/Agent 실행용

> 생성: 2026-02-25
> 목적: docs/stage_map/ 스켈레톤 파일들을 실제 코드 기반으로 채워 박제

---

## 전제

- 수정 금지 파일: 실제 Python 코드 (.py), YAML 설정
- 작업 대상: `docs/stage_map/*.md` 파일들만
- 작성 원칙: 추측 금지, 코드 실제 읽고 확인된 것만 기재
- 포맷: 각 스켈레톤 섹션 그대로 유지, 내용만 채움

---

## 파일별 오더

### 1. `stage0.md`

읽어야 할 파일:
- `modules/core/stage0/__init__.py` — StageZeroManager export
- `modules/core/stage0/story_expander.py` — 컨셉 → Bible + Treatment
- `modules/core/stage0/reverse_expander.py` — 역설계
- `modules/core/stage0/style_extractor.py` — 문체 추출
- `main_a.py` (Stage 0 관련 메뉴 부분만) — 진입점 확인

채워야 할 내용:
- **Scope**: Stage 0 책임 범위 (Bible/NPC/Treatment/Style 추출)
- **Entry Points**: `main_a.py` 메뉴 번호, StageZeroManager 진입 메서드
- **Inputs**: 사용자 입력(컨셉 텍스트 or 원고 파일), 장르 선택
- **Outputs/Files**: `project_data.db` 어느 테이블에 무엇이 저장되는가
- **Outputs/DB updates**: bible, npc, style_guide 테이블 확인
- **Dependencies**: LLM 호출 여부, 어떤 에이전트 사용
- **Failure and Recovery**: LLM 실패 시 fallback 있는가
- **Tests**: `tests/` 에서 stage0 관련 테스트 파일명

---

### 2. `stage2.md`

읽어야 할 파일:
- `modules/core/stage2_orchestrator.py` — 메인 오케스트레이터 (907줄)
- `modules/core/stage2_validation_pipeline.py` — 검증 파이프라인 (683줄)
- `modules/core/stage2_finalizer.py` — Finalizer (535줄)
- `modules/core/stage2_preflight.py` — Preflight (637줄)
- `modules/domain/agents/four_phase_arc_generator.py` — 4Phase Arc 생성
- `modules/domain/agents/arc_ensemble.py` — 앙상블
- `modules/domain/agents/director_auditor.py` — Director audit_strategic_plan()

채워야 할 내용:
- **Scope**: Arc 설계 + 검증 파이프라인. Analyst → Arc → Director 심사 흐름
- **Entry Points**: `stage2_orchestrator.py`의 메인 함수명
- **Inputs**: bible, NPC, treatment (DB), 사용자가 지정한 화 범위
- **Outputs**: `data_anchors` 테이블 `stage="arcs"` JSON. Arc 몇 개, 구조
- **Key Agents**: FourPhaseArcGenerator, ArcEnsemble, DirectorAuditor
- **Retry logic**: Arc REJECT 시 재시도 횟수, 패치 모드 조건
- **State and Cache**: Entity Registry 캐시
- **QualityGate**: `quality_gate_score: 90` 적용 위치 (`stage2_finalizer.py` L182)
- **Tests**: `tests/` stage2 관련 파일 목록

---

### 3. `stage3.md`

읽어야 할 파일:
- `modules/core/stage3_orchestrator.py` — 오케스트레이터
- `modules/domain/agents/three_phase_blueprint_generator.py` — 핵심 생성기
- `modules/domain/agents/blueprint_ensemble.py` — 앙상블 (3개 병렬)
- `modules/domain/agents/unified_blueprint_validator.py` — Director 비교 선택
- `modules/domain/agents/director_ensemble.py` — compare_and_select_blueprint()
- `config/settings/validation.yaml` — blueprint_quality_gate_score: 80

채워야 할 내용:
- **Scope**: Blueprint 생성 (화별 설계도). Stage 2 Arc → 화별 세부 플롯
- **Entry Points**: `stage3_orchestrator.py` 진입 함수
- **Inputs**: Arc (DB `data_anchors`), Entity Registry, 이전 Blueprint (연속성용)
- **Outputs/Files**: `projects/{name}/plans/blueprints/blueprint_XXXX.txt` (사람 읽기용 백업만)
- **Outputs/DB**: `db_manager.get_blueprint() / save_blueprint()` 어느 테이블?
- **Key flow**:
  ```
  retry 루프(max 3회):
    1. Ensemble 3개 병렬 생성
    2. Director compare_and_select (80점 미만 → REJECT)
    3. QualityGate (blueprint_quality_gate_score: 80)
    4. REJECT 시:
       score >= 60 → _inplace_patch_blueprint() (단일 LLM 1회)
       score 50~59 → 전면 재생성
       score < 50  → 전면 재생성 + _previous_best 폐기
    5. 3회 모두 REJECT + score >= 50 → PASS_WITH_WARNING
  ```
- **Known issues / Open Risks**:
  - LLM 고점수 편향 (항상 95-100 → REJECT 드묾, in-place 잘 발동 안 됨)
  - PASS_WITH_WARNING 임계값 50점이 낮을 수 있음
- **Tests**: `tests/test_blueprint_patch_mode.py` 등 관련 파일

---

### 4. `stage4.md`

읽어야 할 파일:
- `modules/core/stage4_orchestrator.py` — 메인 오케스트레이터 (883줄)
- `modules/core/stage4_context_builder.py` — 컨텍스트 빌더 (570줄)
- `modules/core/stage4_interview_round.py` — 인터뷰 라운드 (554줄)
- `modules/core/stage4_post_processor.py` — PASS 후처리 (543줄)
- `modules/domain/agents/chief_writer.py` — Chief Writer
- `modules/domain/agents/director_continuity.py` — Director 연속성 심사

채워야 할 내용:
- **Scope**: 원고 집필. Blueprint → 실제 원고 텍스트
- **Entry Points**: `stage4_orchestrator.py` 진입 함수
- **Inputs**: Blueprint (DB `get_blueprint(ep_num)`), VecMemory, WorldState, FactLedger
  - ⚠️ txt 파일 미사용, DB 전용 확인됨
- **Key flow**: Chief Writer 집필 → Director 심사 → PASS/REJECT 루프
- **QualityGate**: `quality_gate_score: 90` (`stage4_interview_round.py` L873)
- **Patch mode**: Stage 4 패치 모드 조건 (score >= patch_below: 80)
- **Outputs**: `projects/{name}/drafts/` txt, DB 원고 저장
- **Post-processing**: NPC 이력 업데이트, WorldState 업데이트, VecMemory 저장

---

### 5. `interfaces.md`

읽어야 할 파일 (실제 데이터 흐름 추적):
- `modules/core/db_manager.py` — 전체 테이블 목록과 주요 메서드
- `modules/core/project_manager.py` — get_blueprint(), save_blueprint()
- `modules/models/arc.py` — ArcData Pydantic 모델

채워야 할 내용:
- **Stage 간 계약 (DB 경유)**:
  ```
  Stage 0 → Stage 2: bible, npc_registry (DB)
  Stage 2 → Stage 3: data_anchors[stage="arcs"] (ArcData JSON)
  Stage 3 → Stage 4: blueprints 테이블 (get_blueprint(ep_num) → dict)
  Stage 4 → Stage 4+1: vec_memory, npc_history, world_state, fact_ledger (DB)
  ```
- **Pydantic 모델 목록**: ArcData 필드, BlueprintData 필드 (있다면)
- **DB 테이블 전체 목록**: `db_manager.py` 초기화 코드에서 추출

---

### 6. `runbook.md`

읽어야 할 파일:
- `modules/core/project_manager.py` — rollback 메서드
- `main_a.py` — 메뉴 44(롤백), 77(Stage4 초기화), 88(Stage2 초기화), 99(정밀 되감기)

채워야 할 내용:
- **Stage 4 회차 롤백**: 메뉴 44 → 어떤 테이블을 되돌리는가
- **Stage 4 전체 초기화**: 메뉴 77 → 삭제되는 것
- **Stage 2 초기화**: 메뉴 88 → 삭제되는 것
- **Stage 2 정밀 되감기**: 메뉴 99 → selective rewind 로직
- **NPC 이력 롤백**: `npc_history` append-only → rollback 시 어떻게?

---

### 7. `metrics_baseline.md`

정보 출처:
- `config/settings/validation.yaml` — 임계값 전체
- `modules/core/constants.py` — PatchModeThresholds
- `CLAUDE.md` — 테스트 기준선 (2,618 passed 기준)

채워야 할 내용:
- **테스트 기준선**: 2,618 passed, 2026-02-25 기준
- **QualityGate 임계값**:
  - Stage 3 Blueprint: `blueprint_quality_gate_score: 80`
  - Stage 2 Arc / Stage 4 원고: `quality_gate_score: 90`
- **Patch Mode 임계값**:
  - `rewrite_below: 50` (전면 재작성)
  - `patch_below: 80` (Stage 4 부분 수정)
  - `inplace_below: 60` (Stage 3 in-place 수정)
- **원고 분량 기준**:
  - `min_length: 4000`, `target_length: 5000`, `max_length: 15000`

---

### 8. `doc_status.md`

마지막에 채울 것 (다른 파일 채우고 나서):
- 각 파일별 `Last Verified` 날짜, 커밋 해시, Code Sync Yes/No

---

## 실행 순서 권장

1. `metrics_baseline.md` (가장 쉬움, YAML만 읽으면 됨)
2. `interfaces.md` (DB 테이블 목록)
3. `stage3.md` (이미 이번 세션에서 가장 많이 파악됨)
4. `stage4.md`
5. `stage2.md`
6. `stage0.md`
7. `runbook.md`
8. `doc_status.md`

---

## 실행 제약 (필수)

- **rg/grep/find/bash 자동화 금지** — Read 툴로 파일 직접 읽기만 허용
- **파일 하나 완료 즉시 저장** — Write/Edit으로 저장 후 `doc_status.md` 업데이트
- **컨텍스트 소진 시 재개 방법**:
  1. 이 파일(FILL_ORDER.md) 읽기
  2. `doc_status.md` 읽어서 완료된 파일 확인
  3. 미완료 파일부터 이어서 진행
- 내용 없는 섹션은 `TBD` 로 표시하고 넘어갈 것 (추측 금지)
- 코드 확인 없이 "아마 이럴 것" 작성 금지
