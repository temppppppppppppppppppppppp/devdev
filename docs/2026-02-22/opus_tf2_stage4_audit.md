# Stage 4 2차 전수 감사 리포트 (2026-02-22)

> 감사 범위: Stage 4 원고 생성 파이프라인 전체 (1차 수정 검증 + 신규 발굴)
> 감사자: Claude Opus 4.6
> 대상 파일: 12개 (stage4_orchestrator, stage4_context_builder, stage4_interview_round, stage4_post_processor, stage4_types, stage4_context, chain_of_verification, chief_writer, chief_writer_context, chief_writer_quality, director)
> 1차 감사: P0 2건, P1 7건, P2 6건, 개선 아이디어 8건 -- 전량 수정 완료 주장

---

## 1. 1차 수정 검증 결과

### S4-P0-1: 30화 원고 재사용 (DB 이중 로드 방지)

**상태: 수정 확인**

`stage4_interview_round.py` L559-583에서 `_prev_manuscripts_text`를 정규식으로 파싱하여 `_ms_history_for_check`를 구성하고 있다. `"\n\n---\n\n"` 구분자로 split 후 `^\[제(\d+)화\]\n` 패턴으로 에피소드 번호와 본문을 추출한다. 파싱 실패 시 L571-583에서 DB 폴백 경로가 정상 동작한다.

**실측**: `stage4_context_builder.py` L345에서 `"\n\n---\n\n".join(...)` 형식으로 구성하고, L342에서 `f"[제{_prev_ep}화]\n{_prev_content}"` 형식으로 각 블록을 구성한다. interview_round의 파싱 정규식 `^\[제(\d+)화\]\n`이 이 형식에 정확히 매칭되므로, 정상 재사용이 이루어진다. DB 이중 로드 해소 확인.

**잔여 리스크**: 파싱 정규식과 구성 형식 간의 암묵적 계약이 존재한다. context_builder에서 형식을 변경하면 interview_round의 파싱이 깨진다. 상수화하거나 공유 유틸로 추출하면 이 결합을 명시적으로 만들 수 있다. (P3급, 비차단)

---

### S4-P0-2: blueprint 전달

**상태: 수정 확인**

`stage4_orchestrator.py` L371-384의 `build_mandatory_context()` 호출부에 `blueprint=blueprint`가 정상 전달되고 있다:

```python
_ctx_prompts = self.context_builder.build_mandatory_context(
    ...,
    blueprint=blueprint,
    pacing_analyzer=self.ctx.pacing_analyzer,
)
```

`stage4_context_builder.py` L427의 시그니처에서 `blueprint: dict | None = None`으로 수신하고, L584에서 `_collect_npc_roster(arc_data=arc_data, blueprint=blueprint)`에 정상 전달된다. SC NPC roster 수집 정상 동작 확인.

---

### S4-P1-1: CoVe REJECT 시 final_title 리셋

**상태: 수정 확인**

`stage4_orchestrator.py` L585에 `final_title = None` 리셋이 추가되어 있다:

```python
final_manuscript = None
final_title = None  # [S4-P1-1] CoVe REJECT 시 title도 리셋
continue
```

---

### S4-P1-2: state_tracker 일괄 호출

**상태: 수정 확인 (S4-I2로 구현)**

`stage4_context_builder.py` L521-555에서 `get_all_summaries()` 일괄 호출 + 개별 폴백 패턴으로 구현되었다:

```python
try:
    _all_summaries = _st.get_all_summaries(
        arc_no=_arc_no_for_st,
        genre=s4_genre_type,
    )
    for _summary in _all_summaries.values():
        if _summary:
            _mc_parts.append(_summary)
except Exception as _st_err:
    logging.warning("[S4-I2] get_all_summaries 실패, 개별 폴백: %s", _st_err)
    # 폴백: 개별 호출 (하위 호환성 보장)
    for _summary in (
        _st.get_entity_destruction_summary(),
        ...
    ):
```

`state_tracker.py` L1230-1280에서 `get_all_summaries()` 메서드가 16종 기본 + `plot_suspension` + 조건부 `financial` 요약을 dict로 통합 반환한다. 개별 메서드 호출 시 각각 try-except로 감싸여 있어 부분 실패에 강건하다. 수정 확인.

---

### S4-P1-5: bible_delta 사전 초기화 + save_episode_bible 격리

**상태: 수정 확인**

`stage4_post_processor.py` L242에서 `bible_delta = None`으로 사전 초기화하고, L391에서 실제 할당된다. L405-411에서 `save_episode_bible`이 별도 try-except로 격리되어 있어, DB 저장 실패해도 bible_delta 자체는 유효하게 유지된다. L502에서 `if bible_delta:`로 FactLedger에 정상 전달된다.

**주석**: `[S4-P1-5] save_episode_bible 실패가 후속 처리(state_log, FactLedger)를 차단하지 않도록 격리` 주석 확인.

---

### S4-P1-6: O(n^2) -> O(n) 최적화

**상태: 수정 확인**

`stage4_context_builder.py` L198-219에서 `compression_targets`를 루프 전 1회 캐시하고, tracker 재생성 대신 `sum(len(s) for s in sections)`으로 빠르게 총량을 체크한다:

```python
# [S4-P1-6] 압축 대상 목록을 루프 전 1회 캐시하여 O(n^2) -> O(n) 개선
compression_targets = tracker.get_compression_targets()
compressor = ContextCompressor()
for target in compression_targets:
    ...
    # 총 사용량만 빠르게 체크 (tracker 재생성 대신 합산)
    _used = sum(len(s) for s in sections)
    if _used <= total_budget_chars:
        break
```

최종 보고용 tracker는 1회만 재생성 (L221-226). O(n) 확인.

---

### S4-I2: get_all_summaries

**상태: 수정 확인 (위 S4-P1-2와 동일)**

`state_tracker.py`에 `get_all_summaries()` 메서드 구현 완료. 16종 기본 + `plot_suspension` (arc_no 필요) + 조건부 `financial_portfolio` 요약을 dict 반환. `stage4_context_builder.py`에서 일괄 호출 + 개별 폴백 패턴 정상.

---

### S4-I5: CoVe 컨텍스트 최적화

**상태: 수정 확인**

`stage4_orchestrator.py` L564-593에서 CoVe 최적화가 구현되어 있다:

1. `quick_verify()` (Python-only) 먼저 실행
2. 통과 시 LLM 호출 스킵 (기존 동작 유지)
3. 실패 시 `quick_verify_warnings`를 `_cove_context`에 주입하여 LLM `verify()`에 집중 검증 지시
4. `chain_of_verification.py` L188-193에서 `quick_verify_warnings` 키를 `_build_context_string()`에서 처리

```python
if "quick_verify_warnings" in context:
    qv = context["quick_verify_warnings"]
    if qv:
        parts.append(f"[Python 사전검증 경고 -- 이 항목을 중점 검증할 것]\n{qv}")
```

이중 호출 최적화 확인. quick_verify 통과 시 LLM 비용 절약, 실패 시에만 LLM 호출.

---

### S4-I6: Bible 비동기 실행

**상태: 수정 확인**

`stage4_post_processor.py` L248-317에서 `ThreadPoolExecutor(max_workers=1)`로 Manager LLM 호출을 비동기 실행한다:

1. L280: `_bible_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="bible_settle")`
2. L281-289: `_bible_executor.submit(manager.update_state_and_lore_v20, ...)`
3. L290: `_bible_executor.shutdown(wait=False)` -- 제출 후 즉시 반환
4. L296-309: `_bible_future.result(timeout=120)` -- 최대 2분 대기 후 결과 회수
5. L292-294: 비동기 제출 실패 시 동기 폴백 경로

**문제점 발견 (신규 P2-N1, 아래 기술)**: `shutdown(wait=False)` 후 `_bible_future.result(timeout=120)`으로 결과를 기다리는 패턴은 정상 동작하지만, submit과 result 사이에 다른 작업이 없으므로 실질적으로 동기 실행과 차이가 없다. 아래 신규 이슈에서 상세 기술.

---

## 2. 신규 발견 이슈

### N-P1-1. Bible 비동기 실행의 실질적 무효성 (P1)

**파일**: `modules/core/stage4_post_processor.py` L248-317

**현상**: S4-I6에서 Manager LLM 호출을 `ThreadPoolExecutor`로 비동기화했지만, submit 직후 L290에서 `_bible_executor.shutdown(wait=False)`를 호출한 다음, L298에서 즉시 `_bible_future.result(timeout=120)`으로 결과를 대기한다. submit과 result 사이에 병렬로 실행되는 코드가 없다.

코드의 구조를 보면:

```python
# submit (L281-289)
_bible_future = _bible_executor.submit(...)
_bible_executor.shutdown(wait=False)
# ... except 블록만 존재 ...

# 즉시 대기 (L296-309)
if _bible_future is not None:
    raw_audit = _bible_future.result(timeout=120)
```

원래 의도는 "벡터 메모리 저장, 로그 등과 병렬로 진행"이었으나, 벡터 메모리 저장(L162-205)과 로그 저장(L214-239)은 submit 이전에 이미 완료된다. 따라서 비동기화의 실질적 이득이 0이다.

**영향**: 기능적 오류는 아니지만, ThreadPoolExecutor 생성/해제 오버헤드가 매 에피소드마다 발생하며, 코드 복잡도만 증가한다.

**수정 제안**: 두 가지 선택지:
1. 비동기를 제거하고 동기 호출로 단순화
2. submit을 벡터 메모리/로그 저장 이전으로 이동하여 실제 병렬화 달성

---

### N-P1-2. `_detect_cross_episode_repetition` 기본 인자에서 모듈 로드 시점 _threshold 호출 (P1)

**파일**: `modules/core/stage4_orchestrator.py` L86-87

**현상**: 함수 시그니처에서 기본 인자로 `_threshold()`가 호출된다:

```python
def _detect_cross_episode_repetition(
    fingerprints,
    repeated,
    *,
    warning_threshold: int = _threshold("cross_episode_repetition.overlap_warning", 3),
    regression_threshold: int = _threshold("cross_episode_repetition.overlap_regression", 6),
):
```

Python에서 기본 인자는 함수 정의 시점(=모듈 import 시점)에 1회만 평가된다. `_threshold()`가 YAML 설정 파일을 읽으므로:
- 모듈 import 시점에 YAML이 아직 로드되지 않았으면 fallback 값(3, 6)이 고정된다
- 이후 YAML 설정을 변경해도 반영되지 않는다

1차 감사 P1-3에서 `_detect_npc_overexposure`의 동일 패턴을 지적했으나, `_detect_cross_episode_repetition`은 여전히 수정되지 않았다. `_detect_npc_overexposure`는 L40-41에서 `if max_mentions is None: max_mentions = _threshold(...)` 패턴으로 이미 수정되어 있다.

**영향**: 현재는 fallback 값이 적절하므로 실질적 문제는 낮지만, 설정 변경이 무시되는 것은 설계 의도와 불일치.

**수정 제안**: `None` 기본값 + 함수 내부에서 `_threshold()` 호출.

```python
def _detect_cross_episode_repetition(
    fingerprints,
    repeated,
    *,
    warning_threshold: int | None = None,
    regression_threshold: int | None = None,
):
    if warning_threshold is None:
        warning_threshold = _threshold("cross_episode_repetition.overlap_warning", 3)
    if regression_threshold is None:
        regression_threshold = _threshold("cross_episode_repetition.overlap_regression", 6)
```

---

### N-P0-1. `_common_writer_kwargs`에 `episode_digest` 포함 -> ChiefWriter TypeError 크래시 (P0)

**파일**: `modules/core/stage4_interview_round.py` L71-97, L128, L142-148, L154-159, L161-166

**현상**: 1차 감사 P2-4에서 지적된 `episode_digest` 미포함 이슈에 대한 수정이 시도되었다. L96에 `"episode_digest": _episode_digest,  # [S4-P2-4]`가 추가되었다.

**그러나 이 수정이 오히려 P0 버그를 도입했다.**

`_common_writer_kwargs` dict에 `episode_digest` 키가 포함된 상태에서, 4곳의 호출부에서 `**_common_writer_kwargs`로 dict unpacking 전달이 이루어진다:

1. L128: `chief_writer.generate_ensemble(**_common_writer_kwargs)`
2. L142: `chief_writer.patch_with_feedback(**_common_writer_kwargs, ...)`
3. L154: `chief_writer.regenerate_with_feedback(**_common_writer_kwargs, ...)`
4. L161: `chief_writer.regenerate_with_feedback(**_common_writer_kwargs, ...)`

**그러나 이 세 메서드 모두 `episode_digest` 파라미터를 시그니처에 가지고 있지 않다**:

- `generate_ensemble()` (chief_writer.py L115-154): `ep_num` ~ `chain_link_section`까지 24개 명시적 파라미터. `episode_digest` 없음. `**kwargs` 없음.
- `regenerate_with_feedback()` (chief_writer.py L550-587): 동일하게 `episode_digest` 없음.
- `patch_with_feedback()` (chief_writer.py L686-717): 동일하게 `episode_digest` 없음.

따라서 `**_common_writer_kwargs`로 호출하면 **즉시 `TypeError: generate_ensemble() got an unexpected keyword argument 'episode_digest'`가 발생**한다.

**검증**: `generate_ensemble()`이 `**kwargs`를 수용하는지 3중 확인:
1. L115-154의 시그니처: 명시적 파라미터만 존재, `**kwargs` 없음
2. `BaseAgent` 클래스: `generate_ensemble` 오버라이드가 아니므로 부모의 `**kwargs` 없음
3. `episode_digest`로 grep: chief_writer.py에서 `_generate_episode_digest` 메서드만 존재 (L535-536), `generate_ensemble` 시그니처에는 없음

**영향**: **Stage 4 전체가 실행 불가**. 이 코드 경로가 실행되면 즉시 크래시한다. 현재 프로덕션에서 발생하지 않고 있다면 다음 가능성 중 하나:
- Stage 4가 최근 실행되지 않았다
- 다른 진입점을 사용하고 있다
- 테스트에서 이 경로가 mock되어 있다

**긴급도**: P0 -- 차단급. Stage 4 원고 생성이 불가능.

**수정 제안**: 두 가지 선택지:
1. **[권장]** `_common_writer_kwargs`에서 `episode_digest` 제거 -- ChiefWriter 내부에서 `self.context_builder._generate_episode_digest(prev_manuscript, ep_num - 1)`로 자체 생성하므로 외부 전달 불필요
2. `chief_writer.generate_ensemble()`, `regenerate_with_feedback()`, `patch_with_feedback()` 3개 시그니처 + `build_common_context()` 시그니처에 `episode_digest: str = ""` 추가

```python
# 선택지 1: _common_writer_kwargs에서 제거 (최소 변경)
_common_writer_kwargs = {
    "ep_num": next_ep,
    ...
    "chain_link_section": _chain_link_section,
    # "episode_digest": _episode_digest,  # 제거: CW 내부에서 자체 생성
}
```

---

### N-P2-1. `stage4_post_processor.py` 파일 길이 (720줄) -- 후속 분할 필요 (P2)

**파일**: `modules/core/stage4_post_processor.py`

**현상**: `process_pass_result()` 메서드 단독으로 ~693줄이다. 내부 로직이 명확한 블록으로 구분되어 있어 가독성은 양호하지만, 단일 메서드로서는 과도하게 길다:
- DB 저장 (L117-134)
- HUD 업데이트 (L136-152)
- 파일 저장 (L154-160)
- 벡터 메모리 저장 (L162-205)
- 내러티브 요약 (L207-212)
- 로그 저장 (L214-239)
- Bible 정산 (L241-448)
- ChainLink 추출/저장 (L453-467)
- WorldState + FactLedger 원자적 갱신 (L469-513)
- 만족도 태깅 (L515-528)
- 호흡 분석 (L530-553)
- 품질 회귀 감지 (L555-573)
- NPC 과잉 등장 (L575-614)
- 크로스 에피소드 반복 (L616-653)
- 비용 기록 (L655-680)

각 블록은 독립적이므로, 향후 `_save_to_db()`, `_run_bible_settlement()`, `_run_post_analytics()` 등으로 분할 가능.

---

### N-P2-2. `stage4_interview_round.py`에서 `import re as _re_hist` 인라인 (P2)

**파일**: `modules/core/stage4_interview_round.py` L561

**현상**: while 루프 내부 (interview round 실행 중)에서 `import re as _re_hist`가 호출된다. 파일 상단에서 `re`가 import되지 않았으므로 인라인 import가 필요하지만, `_re_hist`라는 별칭은 불필요하다. Python import 캐싱으로 성능 영향은 없으나, 1차 감사 P2-1과 동일 패턴의 반복.

**수정 제안**: 파일 상단에 `import re` 추가, 인라인 import 제거.

---

### N-P2-3. `_SessionConfig`에서 `target_ep`과 `output_dir`의 타입 힌트가 `object` (P2)

**파일**: `modules/core/stage4_orchestrator.py` L151-152

**현상**:
```python
target_ep: object  # int | None
output_dir: object  # Path
```

주석으로 실제 타입을 명시하고 있지만, 타입 힌트 자체는 `object`이다. Python 3.10+에서 `int | None`과 `Path`를 직접 사용할 수 있다.

---

### N-P2-4. `_RoundOutcome`에서도 동일한 `object` 타입 힌트 (P2)

**파일**: `modules/core/stage4_orchestrator.py` L159-160

```python
final_manuscript: object  # str | None
final_title: object  # str | None
```

`str | None` 또는 `Optional[str]`로 변경 가능.

---

## 3. 연결성 심층 검증

### 3-1. Stage 4 출력 -> DB 저장 완전성

**검증 결과: 정상**

`process_pass_result()` 내 DB 저장 순서와 실패 처리를 추적:

1. **원고 저장** (L119): `save_manuscript(ep_num, title, content)` -- `INSERT OR REPLACE INTO manuscripts`. 실패 시 rollback + `return False`로 루프 중단. 가장 핵심 산출물이 최우선 저장됨.

2. **martial_tracker 저장** (L122): `update_martial_tracker(next_ep, final_state_updates)` -- 15대 지표. 원고와 동일 트랜잭션 내에서 실행 (L125의 `commit()`으로 원자적 커밋).

3. **HUD 업데이트** (L137-152): DB 커밋 성공 후에만 실행. `director.on_approve_workflow()` -> `hud.bulk_update()`. 실패 시 경고만.

4. **파일 저장** (L155-160): `ep_NNNN.txt`. DB 백업 역할. 실패 시 경고만.

5. **벡터 메모리** (L162-205): `memorize_v20_episode()`. 실패 시 경고만.

6. **Bible 정산** (L241-448): Manager LLM 호출 -> `save_episode_bible()` + `save_state_log_with_summary()`. 실패 시 경고만 (비차단).

7. **ChainLink** (L453-467): `save_anchor()`. 실패 시 경고만.

8. **WorldState + FactLedger** (L469-513): `transaction()` 컨텍스트 매니저로 원자적 갱신. 실패 시 전체 롤백.

**결론**: 핵심 산출물(원고+지표)은 원자적으로 저장되고 실패 시 루프가 중단된다. 메타데이터(Bible, WorldState, FactLedger)는 각각 비차단으로 처리되어 부분 실패에 강건하다. WorldState/FactLedger만 트랜잭션으로 묶여 있어, Bible 저장 실패 + WorldState 성공 같은 반쪽 상태가 가능하지만, Bible과 WorldState/FactLedger는 독립적인 데이터 소스이므로 문제없다.

### 3-2. Bible/WorldState/FactLedger 동기화

**검증 결과: 정상 (조건부)**

- **WorldState**: L477-494에서 `update_from_state_changes()` + `update_protagonist_state()` + `save()` 순서로 갱신. `final_state_updates`를 입력으로 사용.

- **FactLedger**: L498-511에서 `update_from_state_changes()` (final_state_updates) + `update_from_bible_delta()` (bible_delta) + `save()` 순서로 갱신.

- **동기화 보장**: WorldState와 FactLedger가 동일 트랜잭션 (`_meta_db.transaction()`) 내에서 갱신되므로, 부분 커밋이 방지된다. `_nullcontext()` 폴백으로 transaction 미지원 DB에서도 크래시 없이 동작.

**조건부 이슈**: `bible_delta`가 `None`인 경우 (Bible 정산 전체 실패 시), FactLedger의 `update_from_bible_delta()`가 호출되지 않는다. 이는 L502의 `if bible_delta:` 가드로 의도된 동작이지만, Bible 정산 실패 시 FactLedger에 NPC 사망/아이템 변화 등이 기록되지 않아 장기적으로 불일치가 누적될 수 있다. state_changes 기반 업데이트(L499-501)는 정상 실행되므로, bible_delta 전용 정보(lore, knowledge_map 등)만 누락된다.

### 3-3. `get_latest_episode_number()` 반환값 의미

**검증 결과: 정상**

`project_manager.py` L631-657에서 `get_latest_episode_number()`는 **다음에 생성할 에피소드 번호**를 반환한다. DB의 `MAX(ep_num) + 1`과 물리 파일의 최대 에피소드 번호 + 1 중 큰 값을 반환.

`stage4_orchestrator.py` L319에서 `next_ep = self.ctx.current_project.get_latest_episode_number()`로 사용하므로, next_ep이 정확히 "다음에 생성할 에피소드"를 가리킨다. L304의 `max_loops` 계산에서도 `target_ep - next_ep + 5`로 올바르게 사용.

---

## 4. Race Condition 분석

### 4-1. Bible 비동기 정산의 Race Condition

**분석 결과: Race Condition 없음 (현재 구조에서)**

`stage4_post_processor.py`의 Bible 비동기 실행 패턴을 분석:

1. **submit** (L281-289): `_manager_agent.update_state_and_lore_v20(...)` 제출
2. **shutdown(wait=False)** (L290): Executor 종료 (스레드는 계속 실행)
3. **result(timeout=120)** (L299): 결과 대기 (blocking)

submit과 result 사이에 다른 코드가 없으므로, 실질적으로 동기 실행이다. Manager 에이전트가 `self.client.models.generate_content()`를 호출하는데, API 클라이언트가 thread-safe한지 확인:
- `base_agent.py`에서 API 호출 시 `threading.Lock`을 사용하는 API key rotation이 구현되어 있다 (CLAUDE.md의 "API key rotation needs threading.Lock" 참조, V61.7.1에서 수정 완료)
- Manager는 독립 에이전트 인스턴스이므로 다른 에이전트와 공유 상태가 없다

**결론**: 현재 구조에서 race condition은 없다. 단, 향후 submit-result 사이에 병렬 작업을 추가하면 `self.ctx.current_project.master_bible` 등 공유 상태 읽기가 발생할 수 있으므로 주의.

### 4-2. ChiefWriter 앙상블의 Thread Safety

**분석 결과: 안전**

`chief_writer.py` L252에서 `ThreadPoolExecutor(max_workers=3)`으로 3개 후보를 병렬 생성한다. 각 `_generate_single_candidate()` 호출은:
- `common_context` (str, immutable) 공유 -- 안전
- `master_bible` (dict, 읽기 전용) 공유 -- 안전 (수정하지 않음)
- `self.client` (API 클라이언트) 공유 -- `base_agent.py`의 Lock으로 보호됨
- 각 후보의 `self.quality_gate.sanitize_leakage()`, `self.quality_gate.apply_self_critique()` -- 입력/출력이 로컬이므로 안전

### 4-3. Interview Round 내 Validation 순서

**분석 결과: 안전**

`stage4_interview_round.py`에서 6종 validator가 순차 실행되며, 각각 `validation_results[ci]`를 수정한다. 모든 validator는 동일 스레드에서 실행되므로 경쟁 조건이 없다. `validation_results`는 `manuscript_validator.validate_all_candidates()`에서 생성되고, 이후 각 validator가 순차적으로 `warnings`/`warning_count`/`focus_points`를 추가한다.

---

## 5. Lazy Import 영향 분석

### 5-1. `stage4_orchestrator.py`의 Lazy Import

- L309: `from modules.core.reference_anchor import ReferenceAnchor` -- 루프 밖에서 1회 실행. 정상.
- L528: `from modules.core.spinners import StageSpinner` -- `_handle_round_outcome()` 진입 시마다 실행. Python import 캐싱으로 성능 영향 없음.

### 5-2. `stage4_interview_round.py`의 Lazy Import

- L27: `from modules.core.stage4_types import _PATCH_REWRITE_THRESHOLD, _InterviewRoundResult` -- `run()` 호출 시마다 실행. Python import 캐싱으로 성능 영향 없음. 순환 참조 방지 목적.
- L655: `from modules.core.cross_agent_verifier import ComplianceLevel` -- 조건부 실행. 정상.

### 5-3. `_prepare_stage4_session`의 Lazy Import

- L644-652: 6개 모듈 lazy import. 순환 참조 방지 목적. `_prepare_stage4_session()`은 세션 시작 시 1회만 호출되므로 성능 영향 없음.

**결론**: 모든 lazy import는 순환 참조 방지 또는 조건부 실행을 위한 것이며, Python import 캐싱에 의해 2회차 이후 비용이 0이다. 성능 영향 없음.

---

## 6. 개선 아이디어 (신규)

### NI-1. `_common_writer_kwargs` 불필요 kwarg 전달 방지

**현재**: `_common_writer_kwargs` (L71-97)에 25개 항목이 있고, `chief_writer.generate_ensemble(**_common_writer_kwargs)`로 dict unpacking 전달된다. `episode_digest` 같이 시그니처에 없는 키가 포함되면 `TypeError`가 발생한다 (N-P0-1 참조).

**제안**: kwarg 전달 시 수신측 시그니처와 대조하는 필터 또는, 양쪽에서 공유하는 `WRITER_KWARGS` 상수를 정의하여 동기화.

### NI-2. `process_pass_result()` 메서드 길이 감축

**현재**: 693줄 단일 메서드. 15개 독립 블록.

**제안**: 각 블록을 private 메서드로 추출:
```python
def process_pass_result(self, ...):
    if not self._save_manuscript_to_db(...):
        return False
    self._update_hud(...)
    self._save_to_file(...)
    self._save_to_vector_memory(...)
    self._settle_bible(...)
    self._save_chain_link(...)
    self._update_world_state_and_ledger(...)
    self._run_post_analytics(...)
    return True
```

### NI-3. `prev_manuscripts_text` 형식 계약 명시화

**현재**: `stage4_context_builder.py`에서 `f"[제{ep}화]\n{content}"` + `"\n\n---\n\n"` 조인으로 구성하고, `stage4_interview_round.py`에서 `"^\[제(\d+)화\]\n"` 정규식으로 파싱한다. 이 형식이 암묵적 계약.

**제안**: 상수 또는 유틸 함수로 명시화:
```python
# stage4_types.py
PREV_MS_SEPARATOR = "\n\n---\n\n"
PREV_MS_HEADER_RE = re.compile(r"^\[제(\d+)화\]\n")

def format_prev_manuscript(ep_num: int, content: str) -> str:
    return f"[제{ep_num}화]\n{content}"

def parse_prev_manuscripts(text: str) -> list[dict]:
    ...
```

### NI-4. Bible 정산 비동기의 실질적 병렬화

**현재**: submit 직후 result()로 대기하므로 실질적 병렬화가 0.

**제안**: 코드 순서를 재구성하여 Manager LLM 호출과 벡터 메모리/로그/ChainLink 저장을 병렬 실행:

```python
# 1) submit (비동기 시작)
_bible_future = executor.submit(manager.update_state_and_lore_v20, ...)

# 2) 벡터 메모리 저장 (병렬 실행)
self._save_to_vector_memory(...)

# 3) 로그 저장 (병렬 실행)
self._save_logs(...)

# 4) ChainLink 추출/저장 (병렬 실행)
self._save_chain_link(...)

# 5) result 회수 (여기서 대기)
raw_audit = _bible_future.result(timeout=120)
```

이렇게 하면 Manager LLM 호출(~30-60초)과 I/O 작업(~1-5초)이 병렬로 실행되어 에피소드당 ~1-5초 절약.

---

## 7. 종합 판정

### 1차 수정 검증: 7/7건 정상 수정 확인

| 이슈 | 수정 상태 | 비고 |
|------|-----------|------|
| S4-P0-1 (30화 캐시 재사용) | 수정 확인 | 정규식 파싱 + DB 폴백 |
| S4-P0-2 (blueprint 전달) | 수정 확인 | `blueprint=blueprint` 추가 |
| S4-P1-1 (CoVe title 리셋) | 수정 확인 | `final_title = None` 추가 |
| S4-P1-2/I2 (state_tracker 일괄) | 수정 확인 | `get_all_summaries()` + 개별 폴백 |
| S4-P1-5 (bible_delta 격리) | 수정 확인 | save_episode_bible 별도 try-except |
| S4-P1-6 (O(n) 최적화) | 수정 확인 | compression_targets 1회 캐시 |
| S4-I5 (CoVe 최적화) | 수정 확인 | quick_verify 경고 -> LLM 컨텍스트 주입 |
| S4-I6 (Bible 비동기) | 수정 확인 | ThreadPoolExecutor (실질적 병렬화는 미달) |

### 2차 신규 발견: P0 1건, P1 2건, P2 4건, 개선 아이디어 4건

| 등급 | ID | 요약 |
|------|-----|------|
| **P0** | **N-P0-1** | **`_common_writer_kwargs`에 `episode_digest` 포함 -> ChiefWriter 시그니처 불일치 -> TypeError 즉시 크래시 (Stage 4 실행 불가)** |
| P1 | N-P1-1 | Bible 비동기 실행의 실질적 무효성 |
| P1 | N-P1-2 | `_detect_cross_episode_repetition` 기본 인자에서 모듈 로드 시점 _threshold 호출 |
| P2 | N-P2-1 | `stage4_post_processor.py` 단일 메서드 693줄 |
| P2 | N-P2-2 | `import re as _re_hist` 인라인 (파일 상단에 re 미import) |
| P2 | N-P2-3 | `_SessionConfig`의 object 타입 힌트 |
| P2 | N-P2-4 | `_RoundOutcome`의 object 타입 힌트 |
| 개선 | NI-1 | kwarg 동기화 메커니즘 |
| 개선 | NI-2 | process_pass_result() 분할 |
| 개선 | NI-3 | prev_manuscripts_text 형식 계약 명시화 |
| 개선 | NI-4 | Bible 정산 비동기의 실질적 병렬화 |

### 전체 건강도 평가

Stage 4 파이프라인은 1차 감사 이후 수정이 충실히 적용되어 있으며, 핵심 데이터 흐름(Blueprint -> ChiefWriter -> Director -> DB)이 정상 동작한다. 예외 처리와 폴백 패턴이 일관적이고, race condition이 없으며, 트랜잭션 경계가 적절하게 설정되어 있다.

**가장 우선적으로 수정해야 할 것은 N-P0-1** (`episode_digest` kwarg 불일치로 인한 Stage 4 TypeError 크래시)이다. `_common_writer_kwargs`에서 `episode_digest` 키를 제거하거나, ChiefWriter의 3개 메서드 시그니처에 해당 파라미터를 추가해야 한다. 이 이슈가 프로덕션에서 아직 발견되지 않았다면, Stage 4가 최근에 실행되지 않았거나 다른 진입점을 사용 중일 가능성이 있다. 1차 감사 P2-4 수정 과정에서 도입된 회귀 버그이다.
