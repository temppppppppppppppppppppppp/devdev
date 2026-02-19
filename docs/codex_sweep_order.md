# 글도비 Debug Sweep — 완전 자립형 오더

> 이 문서 하나만 읽으면 된다. 다른 문서 참조 불필요.
> 결과는 `docs/codex_findings.md`에 기록한다.
> **코드를 수정(edit)하지 마라. 탐지·보고만 한다.**

---

## 1. 미션

`modules/` + `main_a.py`의 Python 프로덕션 코드(~90,000줄)에서 **런타임 크래시 또는 잘못된 결과를 유발하는 실제 버그**를 찾아라.

**보고 금지 항목**: 코드 스타일, 네이밍, 리팩토링 제안, 성능 최적화, 타입 힌트 부재, 테스트 코드(`tests/`) 버그.

---

## 2. 시스템 개요

AI 웹소설 자동 생성 파이프라인. Python 3.12 + Google Gemini API.

```
Stage 0 (초기 설정) → Stage 2 (Arc 생성) → Stage 3 (Blueprint) → Stage 4 (원고 집필)
```

핵심 설계:
- **Entry point**: `main_a.py` → `SovereignApp` 클래스 (2,900줄)
- **DI 패턴**: `StageNContext.from_app(app)` → Orchestrator는 `self.ctx`로 접근
- **LLM 호출**: 에이전트 `self.ask()` → JSON → `self._extract_json_robust()` 파싱
- **DB**: SQLite (`db_manager.py`), `check_same_thread=False` + RLock
- **Guard 체인**: GenreGuard → WorkGuard → StyleGuard
- **에러 정책**: CRITICAL=re-raise, IMPORTANT=log+safe default, OPTIONAL=pass

---

## 3. 찾아야 할 버그 패턴

### Tier 1 — 크래시 유발 (CRITICAL)
- `dict.get()` 반환 None에 `.속성` / `[키]` / `.split()` 호출
- `json.loads()` 결과가 list인데 `.get()` 호출
- `int()` / `float()`에 None/빈 문자열 전달
- `str.split()` 후 인덱스 접근 시 원소 부족
- `max()` / `min()`에 빈 시퀀스 전달
- 0으로 나누기 (분모가 `len()`, `count` 등 동적 값)

### Tier 2 — 잘못된 결과 (HIGH)
- dead store: 값 대입 후 미사용 → 이후 로직이 stale 값 사용
- `.get("key", default)` default 타입이 사용처 기대 타입과 불일치
- dict 기대 위치에 string/list 유입
- 조건문 and/or 혼동, not 누락, 비교 방향 반전
- 캐시 변경 후 관련 캐시 무효화(= None) 누락
- f-string/.format() 중괄호 이스케이프 누락

### Tier 3 — 엣지 케이스 (MEDIUM)
- Episode 1에서 `episode - 1 = 0`이 빈 결과를 만드는 경우
- 단일 Arc 루프/인덱싱 실패
- LLM 응답이 빈 문자열 / None / 예상 밖 구조
- `re.compile()` 패턴에 사용자 입력이 이스케이프 없이 전달

---

## 4. ⛔ 오탐 방지 — 아래는 버그가 아니다

아래 8가지를 버그로 보고하면 **오탐**이다. 발견 시 반드시 이 목록과 교차 확인하라.

### FP-1. 비차단 갱신 (Non-blocking updates)
```python
try:
    world_state.save()
except Exception as e:
    logger.warning("저장 실패: %s", e)  # ← 의도된 설계
```
`WorldState`, `FactLedger`, `ChainLink`, `VolumeSummary`, `NPC이력` 저장은 **모두 비차단**. except에서 pass/warning만 하는 것은 정상.

### FP-2. Advisory 시스템 (관측 전용)
`quality_regression`, `npc_overexposure`, `cross_episode_repetition`, `pacing_analyzer`, `diversity_tracker`, `satisfaction_framework` — 로그/경고만 출력, 파이프라인 동작 불변. "결과 미사용"으로 보고 금지.

### FP-3. DI Context 스냅샷
```python
ctx = Stage2Context.from_app(app)
# ctx 수정이 app에 반영 안 되는 것 = 의도된 설계. 콜백만 app 직접 호출.
```

### FP-4. getattr 방어 패턴
```python
tracker = getattr(self.ctx, "state_tracker", None)
if tracker and hasattr(tracker, "npc_registry"): ...
```
lazy init 전 안전 접근. "항상 None" 보고 금지 — init 이후 값 있음.

### FP-5. LLM 응답의 관대한 파싱
```python
result = self._extract_json_robust(response)
if not result or not isinstance(result, dict):
    return fallback
```
LLM 응답 불확실 → 타입 체크 + 폴백은 정상.

### FP-6. JSON string DB 저장
`snapshot_and_reset_scope()` → JSON string 반환 → `save_cost_record()` → SQLite TEXT 저장. 의도된 설계.

### FP-7. `_patch_fallback` 플래그
patch 실패 후 regen 성공 시 `_patch_fallback=True` 유지 = 정상.

### FP-8. pass_threshold 동적 조정
`ScoringValidator.pass_threshold` 런타임 변경 = 적응형 난이도 시스템.

---

## 5. ★★★ 라운드별 필수 출력 형식 ★★★

### 모든 라운드에서 파일마다 반드시 아래 3개 섹션을 작성하라.

```markdown
## Round N — [파일명]

### 5-A. 파일 구조 요약 (필수)
이 파일의 클래스/주요 함수를 나열하라. 최소 5개.
예시:
- `class Stage4Orchestrator` — 원고 생성 오케스트레이션
- `def run_interview_loop(self, ...)` (L45) — 메인 루프
- `def _prepare_context(self, ...)` (L120) — 컨텍스트 준비
- `def _handle_rejection(self, ...)` (L200) — REJECT 처리
- `def _finalize_pass(self, ...)` (L300) — PASS 후처리

### 5-B. 위험 지점 분석 (필수, 최소 3개)
Tier 1~3 패턴에 해당할 *가능성*이 있는 코드 위치를 최소 3개 찾아서,
각각 **안전한 이유** 또는 **버그인 이유**를 코드를 인용하며 설명하라.

예시 (안전한 경우):
> **위험 지점**: L156 `scores.get("quality")` 반환 None에 비교 연산
> **판정**: 안전 — L155에서 `if not scores: return default` 가드 존재

예시 (버그인 경우):
> **위험 지점**: L230 `int(arc_data.get("ep_count"))` — None 전달 시 TypeError
> **판정**: BUG — ep_count 키가 없으면 None, int(None) 크래시

### 5-C. 발견된 버그 (있을 때만)
아래 형식으로 기록:

### [CRITICAL/HIGH/MEDIUM] 파일:라인 — 한줄 요약

**문제**: 어떤 입력/상태에서 어떤 에러가 발생하는지 구체적으로
**문제 코드**:
```python
# 해당 코드 복사
```
**수정 제안**:
```python
# 수정된 코드
```
**확신도**: HIGH/MEDIUM/LOW
**FP 체크**: FP-1~8 해당 여부 확인 결과

---
## Round N 완료
```

### ❗ "없음" 금지 규칙
- 5-A(파일 구조)와 5-B(위험 지점 분석)는 **발견 0건이어도 반드시 작성**한다.
- 5-B에서 위험 지점을 분석한 결과 모두 안전하면, 각각 왜 안전한지 코드를 인용하여 설명한다.
- 5-C(버그)만 0건일 수 있다. 5-A, 5-B가 비어있으면 **파일을 안 읽은 것으로 간주**한다.

### ❗ 5-B 품질 기준
5-B의 위험 지점 분석은 다음을 **반드시** 포함해야 한다:
1. **구체적 라인 번호** — `L156`이 아니라 `L156: scores = arc_data.get("quality_scores")` 처럼 해당 줄의 실제 코드를 함께 인용
2. **상류/하류 컨텍스트** — "L155에 가드가 있어서 안전" 같이, 판정 근거가 되는 **다른 라인**도 인용
3. **구체적 실패 시나리오** — "ep_count가 None이면" 같이, 어떤 입력/상태에서 문제가 되는지 명시

아래는 **불합격 예시** (기계적 패턴 매칭으로 생성된 것):
```
> **위험 지점 1**: `state_service.py:45` `json.loads(data)`
> **판정**: 잠재 위험 — LLM/외부 입력 파싱 결과 shape가 dict/list 혼재 가능
```
↑ 이런 식의 일반론은 **위조로 간주**한다. 실제 코드를 읽었다면 `data`가 어디서 오는지, 후속 코드가 list를 처리하는지 등을 구체적으로 쓸 수 있다.

아래는 **합격 예시**:
```
> **위험 지점 1**: L251 `"ep_end": arc_data.get("ep_start", 1) + arc_data.get("ep_count", VolumeSettings.EPISODES_PER_ARC) - 1`
> Analyst(L430)가 LLM 응답에서 ep_start를 파싱할 때 string "5"가 들어올 수 있음.
> arc_data.get("ep_start", 1)은 키가 존재하면 string을 그대로 반환 → "5" + int = TypeError.
> L255~258의 repair 루프는 이 산술 이후에 실행되므로 보호 불가.
> **판정**: BUG — int() 캐스트 필요
```

---

## 6. 라운드 배정 (25 라운드)

### Phase 1 — Stage 4 원고 파이프라인 (Round 1~6)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 1 | `modules/core/stage4_orchestrator.py` | 818 | □ 루프 종료 조건 □ 재시도 카운터 리셋 □ ctx 속성 None 체크 |
| 2 | `modules/core/stage4_interview_round.py` | 655 | □ arc_data 키 접근 □ record_attempt 파라미터 □ 폴백 반환 타입 |
| 3 | `modules/core/stage4_context_builder.py` (585) + `modules/core/stage4_post_processor.py` (575) | 1160 | □ dict 조립 시 None 체인 □ DB 저장 후 캐시 무효화 □ 타입 불일치 |
| 4 | `modules/domain/agents/chief_writer.py` (873) + `modules/domain/agents/chief_writer_quality.py` (474) | 1347 | □ ask() 실패 처리 □ 점수 비교 타입 □ manuscript 길이 검증 |
| 5 | `modules/domain/agents/chief_writer_context.py` | 1080 | □ 대형 dict 조립 □ 키 누락 시 폴백 □ list vs string 불일치 |
| 6 | `modules/core/stage4_context.py` (134) + `modules/core/pass_rate_monitor.py` (550) | 684 | □ DI 슬롯 vs 실제 사용 □ 0 나누기 □ 빈 리스트 통계 |

### Phase 2 — Stage 2 Arc 파이프라인 (Round 7~12)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 7 | `modules/core/stage2_orchestrator.py` | 807 | □ 상태 전이 □ 에러 복구 경로 □ 루프 탈출 조건 |
| 8 | `modules/core/stage2_preflight.py` (745) + `modules/core/stage2_validation_pipeline.py` (702) | 1447 | □ parallel 결과 병합 □ 검증 점수 합산 □ None 분기 |
| 9 | `modules/core/stage2_finalizer.py` | 618 | □ joint_docs 타입 □ state_changes 구조 □ DB 커밋 에러 처리 |
| 10 | `modules/domain/agents/analyst.py` | 1490 | □ LLM JSON 파싱 □ 대형 dict 반환 키 정합 □ ep_count/ep_start 타입 |
| 11 | `modules/domain/agents/arc_corrector.py` (578) + `modules/domain/agents/arc_critic.py` (363) + `modules/domain/agents/arc_ensemble.py` (690) | 1631 | □ 교정 비율 계산 □ 앙상블 투표 집계 □ 빈 결과 처리 |
| 12 | `modules/domain/agents/arc_draft_validator.py` (854) + `modules/core/stage2_context.py` (229) + `modules/core/stage2_optimizer.py` (926) | 2009 | □ 검증 다단계 □ DI 슬롯 정합성 □ 캐시 키 충돌 |

### Phase 3 — Director + Validation (Round 13~17)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 13 | `modules/domain/agents/director.py` (329) + `modules/domain/agents/director_ensemble.py` (519) + `modules/domain/agents/director_auditor.py` (1056) | 1904 | □ facade 위임 누락 □ 앙상블 투표 □ 점수 산출 0 나누기 |
| 14 | `modules/domain/agents/director_grading.py` (654) + `modules/domain/agents/director_continuity.py` (763) | 1417 | □ 채점 가중치 합산 □ 연속성 비교 □ 에피소드 경계 |
| 15 | `modules/validation/validation_orchestrator.py` | 1411 | □ pass/fail 판정 로직 □ 점수 합산 타입 □ 조건부 skip |
| 16 | `modules/validation/scoring_validator.py` (1011) + `modules/validation/pre_llm_validator.py` (492) | 1503 | □ 임계값 비교 □ 카운터 오버플로 □ 적응형 조정 |
| 17 | `modules/validation/blocking_validator.py` (193) + `blocking_validator_entity_checks.py` (470) + `blocking_validator_scene_checks.py` (455) + `blocking_validator_consistency_checks.py` (377) + `continuity_validator.py` (976) + `consistency_validator.py` (597) | 3068 | □ blocking 조건 정합 □ 엔티티 체크 □ 에피소드 간 비교 |

### Phase 4 — 상태 추적 + 연속성 (Round 18~21)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 18 | `modules/domain/agents/state_tracker.py` (1453) + `modules/domain/agents/state_tracker_npc.py` (2005) | 3458 | □ NPC registry dict 순회 □ extract 루프 □ 이력 append 타입 |
| 19 | `modules/domain/agents/state_tracker_plots.py` (942) + `modules/domain/agents/state_extractor.py` (850) | 1792 | □ 플롯 추적 누적 □ 캐시 정합 □ LLM 파싱 |
| 20 | `modules/domain/agents/continuity_inspector.py` (546) + `continuity_manuscript.py` (1216) + `continuity_arc.py` (1002) + `continuity_blueprint.py` (472) + `continuity_tracker.py` (385) | 3621 | □ 연속성 facade □ 에피소드 간 비교 □ 빈 이력 처리 |
| 21 | `modules/core/world_state.py` (426) + `modules/core/fact_ledger.py` (540) | 966 | □ 롤백 리플레이 □ 상태 병합 □ entity 이력 제한 |

### Phase 5 — 핵심 인프라 (Round 22~23)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 22 | `modules/core/db_manager.py` (1664) + `modules/domain/agents/base_agent.py` (1229) | 2893 | □ SQL 파라미터 타입 □ RLock 범위 □ ask() 재시도 □ JSON 파싱 타입 |
| 23 | `modules/core/prompt_builder.py` (957) + `modules/core/project_manager.py` (940) + `modules/core/services/state_service.py` (353) + `modules/core/services/project_service.py` (273) | 2523 | □ f-string 이스케이프 □ 롤백 로직 □ 필드 검증 □ 타입 캐스트 |

### Phase 6 — 장르 가드 (Round 24~25)

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 24 | `modules/core/genre_guards/base_guard.py` (807) + `modules/core/genre_guards/wuxia_guard.py` (661) + `modules/core/genre_guards/hunter_guard.py` (863) | 2331 | □ Guard 다형성 오버라이드 □ 정규식 이스케이프 □ deep validation 반환 타입 |
| 25 | `modules/core/genre_guards/investment_guard.py` (636) + `modules/core/genre_guards/fantasy_guard.py` (333) + `modules/core/genre_guards/work_guard.py` (197) + `modules/core/genre_guards/style_guard.py` (167) + 확장 가드 4종 (~2000) | ~3333 | □ YAML 키 불일치 □ Guard 체인 순서 □ 금기어 정규식 |

### Phase 7 — main_a.py (Round 26~28)

`main_a.py`는 2,900줄 진입점이다. 3개 라운드로 나눠 읽어라.

| Round | 범위 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 26 | `main_a.py` L1~1000 | 1000 | □ `__init__` 초기화 순서 □ Stage 0 진입 □ DI 바인딩 (`from_app`) |
| 27 | `main_a.py` L1001~2000 | 1000 | □ Stage 2/3 진입 (`_run_stage2`, `_run_stage3`) □ 콜백 등록 시그니처 □ 에러 복구 |
| 28 | `main_a.py` L2001~끝 | ~900 | □ Stage 4 진입 (`_run_stage4`) □ 출력 포맷팅 □ 유틸 메서드 |

### Phase 8 — 대형 나머지 모듈 (Round 29~33)

이전 라운드에서 안 다룬 1,000줄 이상 또는 핵심 경로 파일.

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 29 | `modules/domain/agents/manuscript_validator.py` (1032) + `modules/domain/agents/block_enricher.py` (871) | 1903 | □ 원고 검증 점수 □ 블록 보강 타입 □ LLM 파싱 |
| 30 | `modules/domain/agents/blueprint_ensemble.py` (684) + `modules/domain/agents/four_phase_arc_generator.py` (743) + `modules/domain/agents/state_locked_arc_generator.py` (571) | 1998 | □ 앙상블 투표 □ arc 생성 폴백 □ 상태 잠금 |
| 31 | `modules/core/stage0/reverse_expander.py` (1061) + `modules/core/stage0/style_extractor.py` (723) + `modules/core/stage01_helpers.py` (650) | 2434 | □ Stage 0 초기화 □ 스타일 분석 □ 확장 로직 |
| 32 | `modules/core/quality_dashboard.py` (1100) + `modules/core/pattern_tracker.py` (936) + `modules/core/manuscript_enhancer.py` (777) | 2813 | □ 대시보드 집계 □ 패턴 추적 카운터 □ 텍스트 후처리 |
| 33 | `modules/core/adaptive_retry.py` (860) + `modules/core/feedback_system.py` (853) + `modules/core/relationship_tracker_factions.py` (852) | 2565 | □ 재시도 상태 리셋 □ 피드백 루프 □ 관계 dict 갱신 |

### Phase 9 — 중형 나머지 모듈 (Round 34~37)

500~800줄 파일.

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 34 | `modules/core/semantic_item_registry.py` (778) + `modules/core/genre_hud_manager.py` (751) + `modules/core/tree_of_thoughts.py` (724) | 2253 | □ 레지스트리 키 충돌 □ HUD 갱신 □ ToT 분기 |
| 35 | `modules/domain/agents/critic.py` (714) + `modules/domain/agents/unified_arc_validator.py` (627) + `modules/core/agent_intelligence.py` (600) | 1941 | □ 비평 로직 □ 통합 검증 □ 에이전트 지능 |
| 36 | `modules/core/stage3_orchestrator.py` (526) + `modules/core/pre_director_checklist.py` (592) + `modules/core/constitutional_checker.py` (578) + `modules/core/constraint_db.py` (581) | 2277 | □ Stage 3 lazy init □ 체크리스트 누락 □ 제약 DB 쿼리 |
| 37 | `modules/core/martial_manager.py` (564) + `modules/core/power_scaling.py` (502) + `modules/core/vec_memory.py` (506) + `modules/core/narrative_diversity.py` (529) + `modules/core/diversity_sampler.py` (510) | 2611 | □ 전투 시스템 □ 파워 스케일링 □ 벡터 메모리 □ 다양성 샘플링 |

### Phase 10 — 소형 나머지 모듈 (Round 38~40)

500줄 미만 파일. 파일당 5-A는 클래스+한줄, 5-B는 위험 지점 1~2개로 축약 가능.

| Round | 파일 | 줄수 | 집중 체크리스트 |
|-------|------|------|----------------|
| 38 | `modules/domain/agents/three_phase_blueprint_generator.py` (430) + `modules/domain/agents/unified_blueprint_validator.py` (440) + `modules/domain/agents/blueprint_constraint_compiler.py` (434) + `modules/domain/agents/constraint_compiler.py` (394) + `modules/domain/agents/preflight_checker.py` (492) + `modules/domain/agents/consensus_validator.py` (453) | 2643 | □ blueprint 생성/검증 □ 제약 컴파일 □ 합의 검증 |
| 39 | `modules/core/character_voice.py` (459) + `modules/core/character_voice_profiler.py` (448) + `modules/core/emotion_tracker.py` (370) + `modules/core/pacing_analyzer.py` (439) + `modules/core/foreshadow_tracker.py` (476) + `modules/core/information_diffusion.py` (441) | 2633 | □ 캐릭터 음성 □ 감정/페이싱 추적 □ 복선 관리 □ 정보 확산 |
| 40 | `modules/core/lore_manager.py` (444) + `modules/core/semantic_cache.py` (420) + `modules/core/ab_testing.py` (464) + `modules/core/cross_agent_verifier.py` (492) + `modules/core/confidence_calibration.py` (455) + `modules/core/data_collector.py` (457) + `modules/domain/agents/negative_example_injector.py` (274) + `modules/domain/agents/writer.py` (370) + `modules/validation/retrospective_validator.py` (362) + `modules/validation/batch_validator.py` (298) + `modules/validation/action_scene_evaluator.py` (455) + `modules/validation/advisory_validator.py` (181) + `modules/validation/catharsis_timer.py` (223) | ~4895 | □ 캐시 정합 □ A/B 테스트 □ 검증 소모듈 전수 □ 나머지 잔여 파일 |

---

## 7. `codex_findings.md` 전체 구조

```markdown
# Codex Debug Sweep Findings

## 통계
- 총 발견: N건 (CRITICAL: X, HIGH: Y, MEDIUM: Z)
- 라운드 진행: M/40

---

## Round 1 — stage4_orchestrator.py

### 5-A. 파일 구조 요약
- `class Stage4Orchestrator` — ...
- `def run_interview_loop(...)` (L45) — ...
- `def _prepare_context(...)` (L120) — ...
- ...

### 5-B. 위험 지점 분석
> **위험 지점 1**: L156 `scores.get("quality")` → None 비교
> **판정**: 안전 — L155에 `if not scores: return` 가드

> **위험 지점 2**: L230 `len(results) / total_count` → 0 나누기
> **판정**: BUG — total_count=0 가드 없음

> **위험 지점 3**: L340 `arc_data["tactical_doc"].split(...)` → KeyError
> **판정**: 안전 — L335에 `.get()` + None 체크

### 5-C. 발견된 버그

### [HIGH] modules/core/stage4_orchestrator.py:230 — 0 나누기
**문제**: total_count=0일 때 ZeroDivisionError
**문제 코드**:
```python
ratio = len(results) / total_count  # L230
```
**수정 제안**:
```python
ratio = len(results) / max(total_count, 1)
```
**확신도**: HIGH
**FP 체크**: FP-1~8 해당 없음

---
## Round 1 완료

(반복...)

---

## 미확인 (LOW confidence)
(확신도 LOW 항목 모음)
```

---

## 8. 품질 검증 규칙

완료 후 자체 검증:

1. **5-A 빈 라운드 = 0개여야 한다.** 모든 라운드에 파일 구조 요약이 있어야 한다.
2. **5-B 빈 라운드 = 0개여야 한다.** 모든 라운드에 위험 지점 분석이 있어야 한다.
3. **FP 체크 누락 = 0개여야 한다.** 모든 버그 보고에 FP-1~8 교차 확인이 있어야 한다.
4. **라인 번호 없는 보고 = 0개여야 한다.** 모든 코드 인용에 라인 번호가 있어야 한다.
5. **총 위험 지점 수 ≥ 120개.** (40 라운드 × 최소 3개)

마지막에 이 5개 항목의 충족 여부를 `## 자체 검증 결과` 섹션에 기록하라.
```markdown
## 자체 검증 결과
- [x] 5-A 빈 라운드: 0개
- [x] 5-B 빈 라운드: 0개
- [x] FP 체크 누락: 0개
- [x] 라인 번호 누락: 0개
- [x] 총 위험 지점: 132개 (≥ 120)
```

---

## 9. ⛔⛔⛔ 절대 금지 사항 ⛔⛔⛔

### 스크립트/자동화 금지
- **Python 스크립트, 셸 스크립트, grep/regex 자동화로 findings를 생성하지 마라.**
- `re.match(r'class|def')` 같은 패턴으로 5-A를 채우는 것은 **위조**다.
- `risk_patterns = [re.compile(...)]` 같은 자동 패턴 매칭으로 5-B를 채우는 것도 **위조**다.
- 이전 실행 결과를 `confirmed = { 9: [...] }` 같이 하드코딩해서 5-C에 넣는 것도 **위조**다.
- **발각 시 전체 결과가 폐기된다.** 처음부터 다시 해야 한다.

### 올바른 작업 방법
1. **각 파일을 직접 열어서 읽어라** (에디터/뷰어로, 스크립트 생성이 아님).
2. 코드를 읽으며 **함수의 목적, 입력, 출력, 에러 경로**를 이해하라.
3. 이해한 내용을 바탕으로 5-A, 5-B를 **자연어로 직접 작성**하라.
4. 5-B의 라인 번호와 코드 스니펫은 **실제 파일에서 복사**한 것이어야 한다.

### 위조 탐지 방법 (검토자가 확인할 항목)
검토자는 아래를 확인하여 위조 여부를 판단한다:
- 5-A의 함수 설명이 실제 코드의 docstring/로직과 일치하는가?
- 5-B의 라인 번호에 해당 코드가 실제로 존재하는가?
- 5-B의 "안전한 이유"에서 인용한 가드 코드가 실제로 존재하는가?
- 모든 라운드의 문체가 기계적으로 동일하지 않은가? (자동 생성 탐지)

### 기타
1. **수정(edit)은 절대 하지 마라.** `codex_findings.md` 기록만 한다.
2. **오탐 방지 8개(FP-1~8)를 매 라운드 참조하라.**
3. **Round 38~40은 파일이 많다.** 1,000줄 이상 파일 우선, 500줄 미만은 5-A 축약 가능.
4. **1번부터 40번까지 순서대로 진행한다.** 라운드를 건너뛰지 마라.
