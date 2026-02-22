# Stage 4 전수 감사 리포트 (2026-02-22)

> 감사 범위: Stage 4 원고 생성 파이프라인 전체 (Orchestrator, ContextBuilder, InterviewRound, PostProcessor, ChiefWriter, Director Ensemble, DI Context, Types)
> 감사자: Claude Opus 4.6
> 대상 파일: 12개 (총 ~5,800줄)

---

## 요약

- **P0 (차단급 버그)**: 2건
- **P1 (품질 이슈)**: 7건
- **P2 (스타일/경미)**: 6건
- **개선 아이디어**: 8건

---

## P0 -- 차단급 버그

### P0-1. `_run_interview_loop`에서 30화 원고 로드 중복 (성능 + 잠재적 OOM)

**파일**: `modules/core/stage4_context_builder.py` L327-340 + `modules/core/stage4_interview_round.py` L555-568

**현상**: `prepare_episode_context()` (L327-340)에서 직전 30화 원고 전문을 전부 로드하여 `_prev_manuscripts_text`를 구성한다. 그런데 `stage4_interview_round.py` L555-568에서 **동일한 30화 원고를 다시 DB에서 개별 조회**한다 (`_ms_history_for_check` 구성). 매 에피소드마다 총 60회의 DB 조회가 발생하며, 장기 연재 시 수백 MB의 메모리를 이중으로 점유한다.

**위험도**: 60화 이후부터 메모리 압박이 급증하며, 저사양 환경에서 OOM 크래시 가능.

**수정 제안**: `_prev_manuscripts_text`를 구성할 때 이미 로드한 데이터를 `round_ctx`에 구조화된 형태(`list[dict]`)로 전달하여, interview_round에서 재조회 없이 재사용하도록 변경.

```python
# round_ctx에 추가 필드:
prev_manuscripts_history: list[dict]  # [{"ep_num": N, "text": "..."}]
```

### P0-2. `build_mandatory_context`에서 `blueprint` 파라미터 누락으로 SC 검색 실패

**파일**: `modules/core/stage4_context_builder.py` L407-422 (시그니처) vs `modules/core/stage4_orchestrator.py` L364-376 (호출부)

**현상**: `build_mandatory_context()` 시그니처에는 `blueprint: dict | None = None` 파라미터가 있고, 내부에서 `blueprint` 변수를 SC(Smart Context) retrieval plan 구성 시 사용한다 (L628-630의 `_collect_npc_roster(arc_data=arc_data, blueprint=blueprint)`). 그러나 `stage4_orchestrator.py` L364-376의 실제 호출부에서는 **`blueprint` 인자를 전달하지 않는다**. 따라서 `blueprint`는 항상 `None`이 되어, `_collect_npc_roster`에서 blueprint 기반 NPC 후보를 추출하지 못한다.

**영향**: SC retrieval에서 blueprint에 명시된 NPC 이름을 수집하지 못하므로, NPC 관련 벡터 검색 품질이 저하된다. SC가 비활성화된 환경에서는 영향 없으나, SC 활성화 시 검색 정확도 하락.

**수정 제안**:
```python
# stage4_orchestrator.py L364 호출부에 blueprint 추가
_ctx_prompts = self.context_builder.build_mandatory_context(
    ...,
    blueprint=blueprint,  # 추가
    pacing_analyzer=self.ctx.pacing_analyzer,
)
```

---

## P1 -- 품질 이슈

### P1-1. `_handle_round_outcome`에서 CoVe REJECT 시 `final_title` 소실

**파일**: `modules/core/stage4_orchestrator.py` L568-575

**현상**: CoVe 사후검증 실패 시 `final_manuscript = None`으로 리셋되고 `continue`로 다음 라운드로 진행하지만, `final_title`은 리셋되지 않는다. 이후 5회 모두 실패 시 폴백 경로에서 `final_title = final_title or f"제{next_ep}화"` (L598)로 CoVe REJECT 직전의 title이 사용될 수 있다.

**영향**: 폴백 시 원고와 제목이 불일치할 수 있음 (경미하지만 데이터 무결성 문제).

**수정 제안**: CoVe REJECT 시 `final_title = None`도 함께 리셋.

### P1-2. `state_tracker` 반복적 None 검사 (15회 연속)

**파일**: `modules/core/stage4_context_builder.py` L515-596

**현상**: `if self.ctx.state_tracker:` 검사가 15줄 연속으로 반복된다. 각 블록에서 state_tracker의 다른 메서드를 호출하지만, 동일한 None 검사를 매번 반복하여 가독성이 극히 저하되고, 향후 유지보수 시 실수 가능성이 높다.

**수정 제안**: 단일 `if self.ctx.state_tracker:` 블록으로 통합.

```python
if self.ctx.state_tracker:
    st = self.ctx.state_tracker
    for getter, *args in [
        (st.get_entity_destruction_summary,),
        (st.get_resolved_plots_summary,),
        (st.get_npc_personality_summary,),
        ...
    ]:
        result = getter(*args) if args else getter()
        if result:
            _mc_parts.append(result)
```

### P1-3. `_detect_npc_overexposure`의 default argument로 mutable `frozenset()`

**파일**: `modules/core/stage4_orchestrator.py` L31

**현상**: `core_npc_names: frozenset = frozenset()`는 immutable이므로 mutable default argument 문제는 발생하지 않으나, `max_mentions`와 `min_name_length`의 기본값이 **모듈 로드 시** `_threshold()`를 호출하여 계산된다. `_threshold()`가 YAML 설정을 읽으므로, 설정 파일이 아직 로드되지 않은 시점에 import되면 기본값이 하드코딩된 fallback으로 고정될 수 있다.

**영향**: 설정 변경이 반영되지 않을 수 있음. 현재는 `_threshold`의 fallback이 적절하므로 실질적 문제는 낮지만, 설계 의도와 불일치.

**수정 제안**: default argument를 `None`으로 두고 함수 내부에서 `_threshold()` 호출.

### P1-4. Interview Round에서 `_story_context` 미정의 시 NameError

**파일**: `modules/core/stage4_interview_round.py` L541, L583

**현상**: `_story_context` 변수는 `round_ctx.story_context`에서 L58에서 언패킹된다. 그러나 변수명이 `_story_context`이고 round_ctx 필드명은 `story_context`이다. L58의 `_story_context = round_ctx.story_context`가 정상 동작하므로 현재는 문제없으나, 만약 `_RoundContext`에서 `story_context` 필드가 제거되면 즉시 `AttributeError`가 발생한다.

**영향**: 현재는 동작하지만, 필드 이름과 로컬 변수 이름의 불일치(`story_context` vs `_story_context`)는 혼란을 유발.

### P1-5. `process_pass_result`에서 `bible_delta` 사전 초기화 위치

**파일**: `modules/core/stage4_post_processor.py` L242

**현상**: `bible_delta = None`이 L242에서 초기화되어 있고, L362에서 실제 할당된다. L467에서 `if bible_delta:`로 참조되는데, L412의 except 절에서 bible 저장 실패 시 `bible_delta`가 `None`으로 남아 FactLedger에 `update_from_bible_delta`가 호출되지 않는다. 이것 자체는 의도된 동작이지만, bible 저장이 **부분 성공** (bible_delta는 구성되었으나 save_episode_bible만 실패)한 경우에도 FactLedger가 갱신되지 않아 데이터 불일치가 발생할 수 있다.

**수정 제안**: bible_delta 구성과 DB 저장을 분리하여, bible_delta 구성 성공 시 FactLedger에는 항상 전달되도록 변경.

### P1-6. `_apply_context_budget`에서 `_build_tracker` 반복 생성

**파일**: `modules/core/stage4_context_builder.py` L183-221

**현상**: `_apply_context_budget()` 내부에서 sections를 trim할 때마다 `_build_tracker(sections)`를 재생성한다 (L214). 각 재생성마다 전체 sections를 다시 순회하므로 O(n^2) 복잡도. sections가 많을 때 (15-20개) 성능 저하 발생 가능.

**영향**: 현재 sections 수가 적으므로 실질적 영향은 미미하나, mandatory_context 확장 시 문제 가능.

### P1-7. `_check_cliche_overuse`에서 현재 원고 미포함 의도와 실제 동작 불일치

**파일**: `modules/domain/agents/chief_writer_quality.py` L460-492

**현상**: L491-492 주석에 `[TF-R2-S4-I08] 현재 원고 제외 -- 이전 에피소드만 기준선`이라고 명시되어 있다. 그러나 `_check_cliche_overuse` (L211-255)에서 `self._count_recent_cliches(ep_num, content, window=self.CLICHE_WINDOW)`를 호출할 때, `content` 파라미터가 전달되지만 `_count_recent_cliches` 내부에서는 `content`를 사용하지 않는다. 즉 현재 원고의 클리셰는 개수에 포함되지 않으므로, 주석과 동작은 일치하지만, `content` 파라미터가 사용되지 않는 dead parameter이다.

**수정 제안**: `_count_recent_cliches`의 `content` 파라미터를 제거하거나, 현재 원고와 이전 에피소드 합산 검사를 수행하도록 명확히 결정.

---

## P2 -- 스타일/경미

### P2-1. `import re as _re_trunc` 인라인 import

**파일**: `modules/core/stage4_orchestrator.py` L429

**현상**: `import re as _re_trunc`가 while 루프 내부에서 매 에피소드마다 실행된다. Python의 import 캐싱으로 성능 영향은 없으나, 파일 상단에서 `import re`가 이미 되어 있지 않은 것은 스타일 불일치. 특히 `_re_trunc`라는 별칭은 네이밍 혼란을 유발한다.

**수정 제안**: 파일 상단에 `import re` 추가, 인라인 import 제거.

### P2-2. `_detect_cross_episode_repetition`의 `fingerprints` 미사용 경로

**파일**: `modules/core/stage4_orchestrator.py` L97-128

**현상**: L104에서 `overlap_ratio = overlap_count / len(fingerprints) if fingerprints else 0`으로 계산되지만, L98에서 이미 `if not fingerprints or not repeated: return None`으로 빈 배열이 걸러진다. 따라서 L104의 `if fingerprints else 0` 분기는 항상 truthy여서 dead code.

### P2-3. `Stage4PostProcessor.run_post_episode_tasks`에서 `input()` 블로킹

**파일**: `modules/core/stage4_post_processor.py` L666

**현상**: `input("   \u23ce Enter를 누르면 메뉴로 돌아갑니다...")`가 Stage 4 종료 시 호출된다. 무인 운영(야간 배치) 시 이 호출이 프로세스를 영구 블로킹한다. `EOFError` 처리는 있으나, stdin이 TTY인 경우 여전히 블로킹.

**수정 제안**: 자동 모드 플래그 확인 후 `input()` 스킵, 또는 타임아웃 적용.

### P2-4. `_common_writer_kwargs`에 `episode_digest` 미포함

**파일**: `modules/core/stage4_interview_round.py` L71-96

**현상**: `_common_writer_kwargs` dict에 `episode_digest`가 포함되지 않는다. `_episode_digest`는 round_ctx에서 언패킹되지만 (L45) chief_writer의 generate_ensemble/regenerate_with_feedback에 전달되지 않는다. ChiefWriter 내부에서 자체적으로 digest를 생성하므로 기능상 문제는 없으나, 외부에서 생성한 digest가 무시되는 것은 비효율.

### P2-5. `_SessionConfig`와 `_RoundContext`의 중복 필드

**파일**: `modules/core/stage4_orchestrator.py` L131-146 vs `modules/core/stage4_types.py` L16-51

**현상**: `_SessionConfig`와 `_RoundContext`에 `chief_writer`, `manuscript_validator`, `consistency_validator`, `blocking_validator`, `continuity_validator`, `story_context`, `style_guide` 등 7개 필드가 중복 정의되어 있다. `_run_interview_loop`에서 session의 값을 round_ctx로 복사하는 과정이 장황하다.

### P2-6. `cumulative_bible` 변수 미사용

**파일**: `modules/core/stage4_context_builder.py` L369-370 + `modules/core/stage4_orchestrator.py` L348

**현상**: `cumulative_bible = self.ctx.current_project.db.get_cumulative_bible(next_ep - 1)`이 L369에서 조회되고 L370에서 `dead_npcs`만 추출된 후 return dict에 포함된다 (`ep_ctx["cumulative_bible"]`). 그러나 orchestrator에서 `_ep_ctx["cumulative_bible"]`는 한 번도 사용되지 않는다 (L348에서 언패킹 후 dead code). cumulative_bible 자체가 상당히 무거운 DB 조회이므로 성능 낭비.

**수정 제안**: `dead_npcs`만 필요하다면 `cumulative_bible` 전체 조회 대신 `get_cumulative_bible`에서 dead_npcs만 추출하는 경량 메서드 추가.

---

## 개선 아이디어

### I-1. 이전 원고 30화 전문 로드의 메모리 최적화

**현재**: `prepare_episode_context()`에서 직전 30화 원고 전문을 매 에피소드마다 로드 (L328-340). 60화 기준으로 약 60MB 이상의 텍스트가 메모리에 상주.

**제안**:
- 최근 5화만 전문 로드, 6-30화는 요약(1-2문장)만 포함
- 또는 DB에서 SUBSTR 기반 발췌 조회 (이미 `get_recent_manuscript_excerpts`가 존재)
- Director에게 전달 시에도 `smart_truncate` 적용 (현재 적용 중이나 200K자 상한이 너무 높음)

### I-2. State Tracker 15종 호출의 일괄 처리

**현재**: `build_mandatory_context()` L515-596에서 state_tracker의 15가지 summary 메서드를 순차 호출. 각각 None 검사 + append 패턴 반복.

**제안**: `state_tracker.get_all_summaries() -> dict[str, str]` 일괄 메서드 추가.

```python
if self.ctx.state_tracker:
    summaries = self.ctx.state_tracker.get_all_summaries(
        arc_no=arc_data.get("arc_no", 0),
        genre=s4_genre_type,
    )
    _mc_parts.extend(v for v in summaries.values() if v)
```

### I-3. Interview Round의 검증 파이프라인 모듈화

**현재**: `stage4_interview_round.py`의 `run()` 메서드가 947줄. ConsistencyValidator, BlockingValidator, ContinuityValidator, PreDirectorChecklist, ConfidenceCalibrator, CrossVerifier 6종의 검증이 순차적으로 인라인 실행되며, 각각 유사한 패턴 반복:

```python
try:
    for ci, cand in enumerate(candidates):
        _ms = cand.get("manuscript", "")
        if _ms and ci < len(validation_results):
            result = validator.validate(_ms, context)
            if result.get("violations"):
                for v in result["violations"]:
                    validation_results[ci]["warnings"].append(...)
except Exception:
    ...
```

**제안**: 검증기 체인을 추상화하여 `ValidationPipeline` 클래스로 분리.

```python
pipeline = ValidationPipeline([
    consistency_validator,
    blocking_validator,
    continuity_validator,
])
validation_results = pipeline.run_all(candidates, _cv_context)
```

### I-4. Director 벡터 메모리 조회의 코드 중복 해소

**현재**: `stage4_context_builder.py`의 `_execute_retrieval_plan()`과 `stage4_interview_round.py` L416-524의 Director 벡터 메모리 조회 로직이 거의 동일한 패턴으로 중복되어 있다. 둘 다 `RetrievalSources` 분기, NPC history 조회, max_chars truncation을 수행.

**제안**: `_execute_retrieval_plan()`을 공통 유틸로 추출하여 Director 경로에서도 재사용.

### I-5. CoVe 사후검증의 `quick_verify` + `verify` 이중 호출 최적화

**파일**: `modules/core/stage4_orchestrator.py` L546-579

**현재**: PASS 판정 후 CoVe의 `quick_verify()`를 먼저 실행하고, 실패 시 `verify()`를 추가 실행한다. `quick_verify`가 실패하면 거의 항상 `verify`도 실행되므로 LLM 호출이 2회 발생.

**제안**: `quick_verify` 실패 시 바로 REJECT 처리하거나, `verify` 단독 실행으로 통합. 또는 `quick_verify`를 Python-only 검사로 변경.

### I-6. Episode Bible 정산의 LLM 호출 분리

**파일**: `modules/core/stage4_post_processor.py` L241-416

**현재**: `process_pass_result()` 내에서 `manager.update_state_and_lore_v20()` LLM 호출이 동기적으로 실행된다. 원고 저장(DB commit)은 이미 완료된 상태이므로, Bible 정산은 비동기 또는 별도 스레드에서 실행해도 안전하다.

**제안**: Bible 정산을 `ThreadPoolExecutor`로 비동기 실행하여 다음 에피소드 집필 시작 시간 단축.

### I-7. Patch Mode 단일 전략 실행 시 불필요한 3후보 생성

**파일**: `modules/domain/agents/chief_writer.py` L773-807

**현재**: `patch_with_feedback()`에서 `single_strategy=_rejected_strategy`로 단일 전략만 지정하지만, `generate_ensemble()` 내부에서 빈 candidates 방어 코드와 Pydantic 검증 등이 3후보 기준으로 실행된다.

**제안**: Patch mode에서는 `single_strategy`가 지정되면 `ThreadPoolExecutor` 대신 직렬 실행으로 전환하여 스레드 오버헤드 제거.

### I-8. `_RoundContext` 필드 40개 이상 -- Dataclass 분할 권장

**파일**: `modules/core/stage4_types.py` L16-51

**현재**: `_RoundContext`에 32개 필드가 있고, `stage4_interview_round.py`에서 모든 필드를 로컬 변수로 언패킹 (L31-63). 이는 가독성과 유지보수성을 저하시킨다.

**제안**: 관련 필드를 그룹으로 분할:
- `_EpisodeContext`: arc_pos, total_ep_in_arc, arc_tactical, prev_text, prev_ending, ...
- `_PromptContext`: purism_prompt, genre_name, style_guide, mandatory_context, ...
- `_ValidationContext`: manuscript_validator, consistency_validator, ...

---

## 연결성 검증 (Connectivity)

### 정상 동작 확인

1. **main_a.py -> Stage4Orchestrator**: `_stage_4_v2_chief_writer()` 진입 시 StateTracker/WorldState/FactLedger lazy init 후 `Stage4Context`를 정확히 구성하여 주입. DI 24슬롯 + 조건부 8종 + 콜백 7종 모두 정상 배선 확인.

2. **Blueprint -> ChiefWriter**: `prepare_episode_context()`에서 blueprint를 로드하고, `build_round_context()`를 거쳐 `_RoundContext`에 포함. ChiefWriter의 `generate_ensemble()`에 `blueprint` kwarg으로 정상 전달.

3. **Director <-> ChiefWriter 피드백 루프**: `_handle_round_outcome()`에서 5라운드 루프를 실행하며, REJECT 시 `director_feedback`와 `previous_attempt`가 다음 라운드의 `regenerate_with_feedback()`에 정확히 전달됨.

4. **PostProcessor DB 저장**: `process_pass_result()`에서 원고 -> HUD -> 파일 -> 벡터메모리 -> Bible -> ChainLink -> WorldState -> FactLedger 순서로 저장. DB 실패 시 롤백 + `return False`로 무한 재시도 방지 정상.

5. **SC (Smart Context Retrieval) 통합**: `build_mandatory_context()`에서 `context_advisor.plan_stage4_retrieval()` 호출 후 `_execute_retrieval_plan()`으로 실행. budget tracker에 의한 자동 압축도 정상 배선.

### 발견된 배선 이슈

- **P0-2에서 기술**: `build_mandatory_context()` 호출 시 `blueprint` 미전달로 SC NPC roster 수집 불완전.
- `cumulative_bible`이 준비되지만 사용되지 않음 (P2-6).

---

## 보안/안정성 검증

1. **예외 처리**: 모든 외부 호출(LLM, DB, 벡터 메모리)이 try-except로 감싸여 있으며, 비차단(advisory) 처리 원칙이 일관되게 적용됨. `[SilentPass]` 로깅 패턴 확인.

2. **무한 루프 방지**: `_run_interview_loop()`의 `max_loops` 상한 (L295-297) + interview 5라운드 제한 확인. `max(1, ...)` 방어로 음수 방지 정상.

3. **DB 트랜잭션**: `process_pass_result()`에서 원고 저장 실패 시 `conn.rollback()` 호출. WorldState/FactLedger는 별도 `transaction()` 컨텍스트 매니저로 원자적 갱신. 반쪽 커밋 방지 패턴 정상.

4. **스레드 안전성**: ChiefWriter 앙상블의 `ThreadPoolExecutor`에서 `future.cancel()` + timeout 처리 확인. Director 관련 메서드는 싱글스레드에서 실행.

---

## 결론

Stage 4 파이프라인은 전체적으로 **안정적이고 well-defended** 구조를 갖추고 있다. 12차 디버깅 스윕 + Opus TF 재감사 이후 대부분의 엣지 케이스가 처리되어 있으며, 예외 처리와 폴백 패턴이 일관적이다.

주요 개선 영역:
1. **P0-2 (blueprint 미전달)**: SC 검색 품질에 영향을 미치므로 우선 수정 권장.
2. **P0-1 (30화 중복 로드)**: 장기 연재 시 메모리 문제를 유발할 수 있으므로 중기 개선 과제.
3. **I-3 (검증 파이프라인 모듈화)**: interview_round.py의 947줄을 분할하면 유지보수성이 크게 향상됨.
