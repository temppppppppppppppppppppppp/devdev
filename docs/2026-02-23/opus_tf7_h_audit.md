# TF-7-H 감사 보고서: Genre Guard 체인 완전성

## 감사 파일 목록
- `modules/core/genre_guards/base_guard.py`
- `modules/core/genre_guards/work_guard.py`
- `modules/core/genre_guards/style_guard.py`
- `modules/core/genre_guards/alt_history_guard.py`
- `modules/core/genre_guards/composer_guard.py`
- `modules/core/genre_guards/medical_guard.py`
- `modules/core/genre_guards/sports_guard.py`
- `modules/core/genre_guards/actor_guard.py`
- `modules/core/genre_guards/cooking_guard.py`
- `modules/core/genre_guards/wuxia_guard.py`
- `modules/core/genre_guards/hunter_guard.py`
- `modules/core/genre_guards/fantasy_guard.py`
- `modules/core/genre_guards/investment_guard.py`
- `modules/core/genre_guards/__init__.py`
- `modules/validation/consistency_validator.py`
- `modules/validation/validation_orchestrator.py`
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage4_interview_round.py`
- `modules/validation/blocking_validator.py`
- `modules/validation/blocking_validator_entity_checks.py`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_auditor.py`
- `main_a.py`

## Guard 시그니처 정합성 테이블 (13개 Guard)

### 계약 결론
- `BaseGuard`의 추상 계약은 `get_genre_name()`, `get_v20_purism_prompt()` 2개이며 `check(manuscript, context)` 추상 계약은 없다.
  - 근거: `modules/core/genre_guards/base_guard.py:48`, `modules/core/genre_guards/base_guard.py:165`
- 실검증 체인의 공통 호출 계약은 `run_deep_validation(manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]`로 통일되어 있다.
  - 근거: `modules/core/genre_guards/base_guard.py:204`

| Guard | 핵심 검증 엔트리 | 시그니처/반환 | 근거 |
|---|---|---|---|
| BaseGuard | `run_deep_validation` | `(manuscript: str, current_state: dict[str, Any] = None) -> dict[str, Any]` | `modules/core/genre_guards/base_guard.py:204` |
| WuxiaGuard | override | 동일 | `modules/core/genre_guards/wuxia_guard.py:629` |
| HunterGuard | override | 동일 | `modules/core/genre_guards/hunter_guard.py:817` |
| InvestmentGuard | override | 동일 | `modules/core/genre_guards/investment_guard.py:605` |
| FantasyGuard | override | 동일 | `modules/core/genre_guards/fantasy_guard.py:287` |
| ComposerGuard | override | 동일 | `modules/core/genre_guards/composer_guard.py:507` |
| CookingGuard | override | 동일 | `modules/core/genre_guards/cooking_guard.py:500` |
| AltHistoryGuard | override | 동일 | `modules/core/genre_guards/alt_history_guard.py:481` |
| ActorGuard | override | 동일 | `modules/core/genre_guards/actor_guard.py:453` |
| SportsGuard | override | 동일 | `modules/core/genre_guards/sports_guard.py:451` |
| MedicalGuard | override | 동일 | `modules/core/genre_guards/medical_guard.py:458` |
| WorkGuard | wrapper override | 동일 | `modules/core/genre_guards/work_guard.py:155` |
| StyleGuard | wrapper override | 동일 | `modules/core/genre_guards/style_guard.py:99` |

## Guard 체인 호출 경로 검증
- 부트 시점에 장르 Guard 생성 후 `work_guard.yaml` 존재 시 `WorkGuard`를 래핑한다.
  - 근거: `main_a.py:977`, `main_a.py:988`
- StyleGuide anchor가 dict로 존재할 때만 `StyleGuard`를 추가 래핑하여 Director/Writer에 주입한다.
  - 근거: `main_a.py:1519`, `main_a.py:1522`, `main_a.py:1527`, `main_a.py:1532`, `main_a.py:1539`
- Stage4 interview 라운드의 ConsistencyValidator는 `self.ctx.sys.guard`를 직접 주입받아 실행된다.
  - 근거: `modules/core/stage4_orchestrator.py:677`, `modules/core/stage4_interview_round.py:331`
- ValidationOrchestrator 경로는 별도 인자 없이 `ConsistencyValidator(genre=genre)`를 생성하며, 내부에서 `create_genre_guard()`를 통한 동적 로딩 경로를 사용한다.
  - 근거: `modules/validation/validation_orchestrator.py:214`, `modules/validation/consistency_validator.py:15`, `modules/validation/consistency_validator.py:47`, `modules/validation/consistency_validator.py:53`

## 발견 이슈 (총 0건)
- 확정 BUG 없음.

## Risk (총 1건)

### [TF-7-H-R1] V0128 경로에서 `validation_context`가 빈 dict로 시작되면 BLOCKING dead-NPC 체크 입력(`encyclopedia.npcs`)이 누락될 수 있음 (MEDIUM, Risk)
**근거 파일/라인**
- `modules/domain/agents/director_auditor.py:541`~`modules/domain/agents/director_auditor.py:543` (`validation_context`를 빈 dict로 초기화)
- `modules/domain/agents/director_auditor.py:184` (`mode`만 추가)
- `modules/validation/blocking_validator.py:60` (dead NPC 체크 호출)
- `modules/validation/blocking_validator_entity_checks.py:60`~`modules/validation/blocking_validator_entity_checks.py:63` (`context["encyclopedia"]["npcs"]` 기준)

**판단 근거**
- dead-NPC BLOCKING 검사는 `encyclopedia.npcs` 입력 의존이다.
- V0128 호출부에서 해당 키를 강제 주입하지 않는 경로가 존재해, 호출자 컨텍스트 품질에 따라 검사가 약화될 수 있다.
- 다만 Stage4 인터뷰 경로는 별도로 `encyclopedia.npcs`를 주입하고 있어 즉시 장애로 확정하지 않고 Risk로 분류한다.
  - 보강 근거: `modules/core/stage4_interview_round.py:282`~`modules/core/stage4_interview_round.py:295`

## [FP] 오탐 목록

### [FP-1] `check(manuscript, context)` 메서드 부재는 계약 위반이다
- **판정**: 오탐
- **수동 근거**:
  - `BaseGuard` 추상 계약에 `check()`가 없다.
  - 검증 체인 엔트리는 `run_deep_validation(...)`이며 호출부가 이를 사용한다.
  - 근거: `modules/core/genre_guards/base_guard.py:48`, `modules/core/genre_guards/base_guard.py:165`, `modules/core/genre_guards/base_guard.py:204`, `modules/domain/agents/director_auditor.py:83`

### [FP-2] dead NPC 제약은 각 Genre Guard에서 직접 검사해야 하며 현재 미구현은 결함이다
- **판정**: 오탐
- **수동 근거**:
  - dead NPC는 Guard 계층이 아니라 BLOCKING Entity check에서 중앙 검사한다.
  - 회상/과거 맥락은 허용하고 행동/대사는 차단하도록 구현되어 있다.
  - 근거: `modules/validation/blocking_validator.py:60`, `modules/validation/blocking_validator_entity_checks.py:58`, `modules/validation/blocking_validator_entity_checks.py:88`, `modules/validation/blocking_validator_entity_checks.py:92`

## TF-5-H, K-3 패치 후속 확인

| 패치 항목 | 결과 | 근거 |
|---|---|---|
| TF-5-H(장르별 if/elif 대신 Guard 단일 호출 체인) | 회귀 없음 | `modules/domain/agents/director_auditor.py:83` (단일 `run_deep_validation` 호출), 각 장르 Guard override 유지: `modules/core/genre_guards/wuxia_guard.py:629`, `modules/core/genre_guards/hunter_guard.py:817`, `modules/core/genre_guards/investment_guard.py:605` |
| TF-5-K-3(ConsistencyValidator Guard 동적 로딩 통합) | 회귀 없음 | `modules/validation/consistency_validator.py:15`, `modules/validation/consistency_validator.py:47`, `modules/validation/consistency_validator.py:53`, `modules/validation/validation_orchestrator.py:214` |

## 요약 테이블
| 분류 | 건수 | 항목 |
|---|---:|---|
| 확정 BUG | 0 | - |
| Risk | 1 | `TF-7-H-R1` |
| FP | 2 | `FP-1`, `FP-2` |
