# TF-7-J 감사 보고서 — Emotion / Foreshadow / Karma / Catharsis

## 감사 파일 목록
- `modules/core/karma_service.py`
- `modules/core/emotion_tracker.py`
- `modules/core/foreshadow_tracker.py`
- `modules/validation/catharsis_timer.py`
- `modules/core/system.py`
- `modules/core/stage4_context.py`
- `modules/core/stage4_types.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage4_interview_round.py`
- `modules/validation/validation_orchestrator.py`
- `modules/validation/continuity_validator.py`
- `modules/core/services/project_service.py`
- `modules/core/db_manager.py`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_ensemble.py`
- `modules/domain/agents/manuscript_validator.py`
- `main_a.py`

## 발견 이슈 (총 3건)

### [TF-7-J-1] Rollback 경로가 `director_selections`를 정리하지 않아 폐기된 회차 선택 이력이 편향 분석에 재유입됨 (HIGH)
**근거 파일/줄**
- `modules/core/stage4_interview_round.py:664`~`modules/core/stage4_interview_round.py:673` (회차별 Director 선택 기록 저장)
- `modules/core/db_manager.py:1793`~`modules/core/db_manager.py:1797` (`director_selections`에 INSERT)
- `modules/core/services/project_service.py:159`~`modules/core/services/project_service.py:163` (rollback 삭제 대상 테이블 목록)
- `modules/core/services/project_service.py:168`~`modules/core/services/project_service.py:174` (실제 삭제 실행; `director_selections` 미포함)
- `main_a.py:2093`~`main_a.py:2103` (종료 시 `get_selection_analysis()` 기반 편향 진단)
- `modules/core/db_manager.py:1842`~`modules/core/db_manager.py:1845` (`director_selections` 최신 N건을 ep 필터 없이 조회)
- `modules/core/db_manager.py:1517` (기준 구현 `reset_after()`는 `director_selections` 삭제 수행)

**문제**
- 실사용 rollback(`ProjectService.rollback_episode`)는 핵심 테이블만 삭제하고 `director_selections`를 남긴다.
- 이후 편향 진단은 ep 범위 필터 없이 최신 선택 로그를 읽기 때문에, rollback으로 폐기된 회차의 선택 이력이 재사용된다.

**영향**
- rollback 후 종료 진단에서 Director bias 경고/요약이 실제 재생성 히스토리와 어긋날 수 있다.
- 선택 이력 기반 advisory 신뢰도가 하락한다.

**Caller→Callee 계약 추적**
- Stage4 면담 라운드: `stage4_interview_round` → `db_manager.save_director_selection`
- 종료 분석: `main_a` → `db_manager.get_selection_analysis`
- rollback 경로: `main_a._rollback_episode` → `project_service.rollback_episode` (삭제 누락)

**Bug-vs-intent 근거**
- rollback 주석/문서가 “HUD, DB, Vector DB, 파일 모두 rollback”을 의도(`modules/core/services/project_service.py:92`, `main_a.py:2781`)하는데, 실제 삭제 범위가 분석 테이블과 불일치한다.
- 동일 저장소의 기준 경로(`db_manager.reset_after`)에서는 해당 테이블을 삭제하므로 설계 의도 대비 누락으로 판단.

**권장 수정 방향**
- `ProjectService.rollback_episode()` 삭제 목록에 `director_selections`를 포함.
- 가능하면 rollback 삭제 테이블 집합을 `DBManager.reset_after()`와 단일 소스로 통합.

### [TF-7-J-2] Rollback 이후 ForeshadowTracker 상태가 되감기되지 않아 삭제된 미래 복선이 다음 회차 프롬프트에 주입될 수 있음 (HIGH)
**근거 파일/줄**
- `main_a.py:1631`~`main_a.py:1637` (시작 시 `foreshadow.json` 로드)
- `modules/core/stage4_context_builder.py:759`~`modules/core/stage4_context_builder.py:763` (Writer mandatory context에 Foreshadow 프롬프트 주입)
- `modules/core/stage4_post_processor.py:285`~`modules/core/stage4_post_processor.py:286` (원고 후처리 시 auto-detect + `foreshadow.json` 저장)
- `modules/core/services/project_service.py:199`~`modules/core/services/project_service.py:206` (rollback 파일 정리는 drafts만 수행)
- `main_a.py:2782`~`main_a.py:2806` (rollback 성공 후 캐시만 무효화, foreshadow 재동기화 없음)
- `modules/core/foreshadow_tracker.py:540`~`modules/core/foreshadow_tracker.py:544` (`clear()` API 존재)
- `modules/core/foreshadow_tracker.py:259`~`modules/core/foreshadow_tracker.py:265` (active hook 계산 시 planted_ep 기준 필터 없음)

**문제**
- rollback은 DB/원고를 되감지만, 복선 추적기(메모리 + 로그 파일) 상태는 되감기되지 않는다.
- 복선 프롬프트 주입은 매 라운드 활성 hook 기반으로 동작하므로, rollback으로 폐기된 회차에서 생성된 hook이 다음 회차 지시에 남을 수 있다.

**영향**
- rollback 직후 재생성 경로에서 “존재하면 안 되는 미래 복선”이 prompt에 섞여 연속성 오염 위험이 발생한다.

**Caller→Callee 계약 추적**
- 로드/주입/저장 경로: `main_a`(load) → `stage4_context_builder`(inject) → `stage4_post_processor`(save)
- rollback 경로: `main_a._rollback_episode` → `project_service.rollback_episode` (foreshadow 상태 복구 누락)

**Bug-vs-intent 근거**
- rollback 기능 설명은 “전체 상태 되감기”인데, 복선 상태는 별도 생애주기(로그 파일)로 남겨 일관성을 깨뜨린다.
- `ForeshadowTracker.clear()`가 이미 제공되어 있어 복구 훅 부재는 의도된 제한보다는 배선 누락으로 해석된다.

**권장 수정 방향**
- rollback 성공 시 `foreshadow_tracker.clear()` 후 target ep 기준 재구성(또는 로그 재생성) 수행.
- `logs/foreshadow.json`도 target ep 기준으로 trim하거나 즉시 재저장.

### [TF-7-J-3] EmotionArcTracker가 초기화/로드만 되고 Stage4 실경로에 연결되지 않음 (MEDIUM)
**근거 파일/줄**
- `main_a.py:1660`~`main_a.py:1664` (EmotionArcTracker 생성 및 DB load)
- `modules/core/stage4_context.py:30`~`modules/core/stage4_context.py:62` (`Stage4Context.__slots__`에 `emotion_tracker` 부재)
- `main_a.py:3066`~`main_a.py:3095` (Stage4Context 구성 시 `emotion_tracker` 전달 없음)
- `modules/core/emotion_tracker.py:328`~`modules/core/emotion_tracker.py:337` (`add_episode_emotion`)
- `modules/core/emotion_tracker.py:370`~`modules/core/emotion_tracker.py:382` (`save_to_db`)
- `main_a.py:2136`~`main_a.py:2168` (종료 시 failure/voice/foreshadow 저장은 있으나 emotion 저장 경로 없음)

**문제**
- 감정선 추적기는 생성되지만 Stage4 컨텍스트/후처리/종료 저장 루프와 연결되지 않는다.
- 결과적으로 런타임에서 감정 이력 갱신 및 피드백 주입 루프가 형성되지 않는다.

**영향**
- 감정선 단조화 방지 목적의 기능이 사실상 비활성화되어, 장기 연재 품질 제어 신호를 제공하지 못한다.

**Bug-vs-intent 근거**
- 모듈 자체는 분석/권고/저장 API까지 제공(`emotion_tracker.py`)되어 운영 의도가 명확하다.
- 반면 실운영 배선(Stage4Context + post/exit pipeline)이 누락되어 의도 대비 미완결 상태로 판단.

**권장 수정 방향**
- Stage4Context에 `emotion_tracker`를 주입하고, PASS 후처리에서 `analyze_manuscript_emotion` + `add_episode_emotion` + `save_to_db` 연결.
- rollback 성공 시 target ep 기준 감정 이력 재로딩/trim 절차 추가.

## Risk (총 2건)

### [TF-7-J-R1] CatharsisTimer는 ValidationOrchestrator 경로에만 연결되고 Stage4 면담 메인 루프에서는 우회됨 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/validation/validation_orchestrator.py:230`~`modules/validation/validation_orchestrator.py:231` (CatharsisTimer 초기화)
- `modules/validation/validation_orchestrator.py:468`~`modules/validation/validation_orchestrator.py:470` (카타르시스 점검 수행)
- `modules/core/stage4_interview_round.py:245`~`modules/core/stage4_interview_round.py:251` (Stage4는 ManuscriptValidator 경로 사용)
- `modules/core/stage4_interview_round.py:621`~`modules/core/stage4_interview_round.py:634` (Director ensemble 판단 경로)
- `modules/domain/agents/manuscript_validator.py:18`~`modules/domain/agents/manuscript_validator.py:29` (warning-only Python validator)

**Risk 판단 근거**
- Stage4 실경로는 경량 validator + Director 판단으로 구성되어 있고, V0128 오케스트레이터의 CatharsisTimer 점검이 직접 적용되지 않는다.
- 다만 성능/운영 모드 분리를 위한 의도일 가능성을 배제할 수 없어 Risk로 분류.

### [TF-7-J-R2] KarmaService는 구현되어 있으나 현재 핵심 생성/검증 파이프라인에서 소비 지점이 확인되지 않음 (MEDIUM, Risk)
**근거 파일/줄**
- `modules/core/karma_service.py:9`~`modules/core/karma_service.py:24` (`get_relationship_report` 구현 존재)
- `modules/core/system.py:44`~`modules/core/system.py:57` (System boot/config에 karma service 등록)
- `modules/core/stage4_post_processor.py:387`~`modules/core/stage4_post_processor.py:417` (Stage4는 `karma_matrix` 데이터를 직접 처리)

**Risk 판단 근거**
- 서비스 자체는 동작 구현이 있으나, Stage4 주경로에서는 `karma_matrix` 직처리로 흐르고 `KarmaService` 호출 배선이 확인되지 않았다.
- 즉시 장애는 없으나 모듈 중복/사문화 위험이 있어 Risk로 분류.

## [FP] 오탐 목록

### [FP-1] `karma_service.py`는 스텁(`pass`/`NotImplemented`)이다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/karma_service.py:9`~`modules/core/karma_service.py:24` 실제 report dict 생성 로직 존재.

### [FP-2] CatharsisTimer에 `ep_count=0` 분모 0 오류가 있다
- **판정**: 오탐
- **수동 근거**:
  - `modules/validation/catharsis_timer.py:315`~`modules/validation/catharsis_timer.py:318` 분모는 상수(12)이며, 데이터 없을 때 `score=0.5`로 처리.
  - `modules/validation/catharsis_timer.py:331`~`modules/validation/catharsis_timer.py:333` history 비어있으면 즉시 0 반환.

### [FP-3] Foreshadow 스키마가 `ep_resolved` 필드를 반드시 가져야 한다
- **판정**: 오탐
- **수동 근거**:
  - `modules/core/foreshadow_tracker.py:63` (`payoff_ep` 설계)
  - `modules/core/foreshadow_tracker.py:220`~`modules/core/foreshadow_tracker.py:223` payoff 시점 기록
  - `modules/core/foreshadow_tracker.py:405`~`modules/core/foreshadow_tracker.py:410` 저장 스키마도 `payoff_ep` 기준
- **의도 확인**: 이 구현의 해소 시점 필드 명은 `ep_resolved`가 아니라 `payoff_ep`.

## 파이프라인 배선 현황 (Emotion / Foreshadow / Karma / Catharsis)

| 모듈 | 생성/로드 | Stage4 주입 | Stage4 후처리/저장 | Rollback 동기화 | 판정 |
|---|---|---|---|---|---|
| EmotionArcTracker | `main_a.py:1660`~`1664` | 없음 (`stage4_context.py:30`~`62`) | 없음 (`main_a.py:2136`~`2168`) | 없음 | Dead Feature (Confirmed) |
| ForeshadowTracker | `main_a.py:1631`~`1637` | `stage4_context_builder.py:759`~`763` | `stage4_post_processor.py:285`~`286` | 없음 (`main_a.py:2782`~`2806`) | Rollback 불일치 (Confirmed) |
| KarmaService | `system.py:44` | 핵심 루프 소비 미확인 | Stage4는 `karma_matrix` 직처리 (`stage4_post_processor.py:387`) | N/A | 연결 약함 (Risk) |
| CatharsisTimer | `validation_orchestrator.py:230`~`231` | Stage4 면담 루프 직접 주입 없음 | ValidationOrchestrator 경로에서만 사용 (`validation_orchestrator.py:468`) | N/A | 경로 분리 리스크 (Risk) |

## 요약 테이블

| 심각도 | 건수 | 항목 |
|---|---:|---|
| HIGH | 2 | `TF-7-J-1`, `TF-7-J-2` |
| MEDIUM | 1 | `TF-7-J-3` |
| Risk | 2 | `TF-7-J-R1`, `TF-7-J-R2` |
| FP | 3 | `FP-1~3` |
