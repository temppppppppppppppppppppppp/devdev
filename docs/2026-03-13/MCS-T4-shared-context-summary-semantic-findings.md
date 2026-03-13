# [MCS-T4] Shared Context / Summary Semantic Findings

> 작성일: 2026-03-13
> 상태: `PASS3 finalized`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-cross-stage-semantic-preservation-detail-full-survey-audit-order.md`

코드 직접 수정은 수행하지 않았다. 본 문서는 `Terminal 4 - Summary / Context / Arc Semantic Preservation` 범위의 PASS3 결과만 기록한다.

---

## 조사 범위

- `main_a.py`
  - `_generate_narrative_summary()`
  - `_load_narrative_summaries()`
  - `_build_focused_context()`
  - `_build_minimal_arc_context()`
  - `_generate_arc_context_v60()`
  - `_get_arc_context_for_episode()`
  - `_validate_volume_boundaries()`
- 직접 downstream
  - `modules/core/stage4_context.py`
  - `modules/core/stage4_context_builder.py`
  - `modules/core/stage01_helpers.py`
- runtime 교차 확인
  - `modules/core/stage4_interview_round.py`
  - `modules/core/stage4_post_processor.py`
  - `modules/core/context_compression.py`

## 필수 근거

- `tests/test_stage4_context.py`
- `tests/test_stage4_context_builder.py`
- `tests/test_stage01_helpers.py`
- `tests/test_sweep23.py`
- 기존 문서 교차 검증
  - `docs/2026-03-13/MPN-T4-stage4-summary-cache-findings.md`
  - `docs/2026-03-13/MPN-T3-stage01-stage3-shared-helper-findings.md`
  - `docs/2026-03-13/MRF-T3-prompt-guidance-context-findings.md`
  - `docs/2026-03-13/MFS-T3-stage3-stage4-audit-callback-findings.md`

## 실행 검증

- `pytest tests/test_stage4_context.py tests/test_stage4_context_builder.py tests/test_stage01_helpers.py tests/test_sweep23.py -q`
  - 결과: `119 passed`
- synthetic verification 1
  - `Stage4ContextBuilder.build_mandatory_context()`를 작은 `context.mandatory_context_max`로 호출했을 때, middle에 둔 `SUMMARYBLOCK`는 사라지고 tail의 `FUTUREBLOCK`는 남는 재현을 확인했다.
  - 의미: past summary와 future arc context가 같은 보존 우선순위를 갖지 않는다.

## PASS 기록

### PASS 1 - 표면 수집

- 후보 5건을 수집했다.
  - 후보 A: narrative summary와 future arc context가 같은 `mandatory_context` 안에 섞인 뒤 trim에서 비대칭적으로 보존된다
  - 후보 B: Stage4가 past-story 의미를 `prev_manuscripts_text`와 `_load_narrative_summaries()` 두 채널로 동시에 받지만 범위 규약이 다르다
  - 후보 C: Stage1 volume boundary와 Stage4 future arc injection 사이에 공통 boundary contract가 없다
  - 후보 D: `_get_arc_context_for_episode()` real facade 의미는 여전히 test blind spot이다
  - 후보 E: `Stage4Context.from_app()` callback wiring 자체에 신규 semantic drift가 있다

### PASS 2 - 교차 검증

- 후보 D는 PASS3 finding에서 제거했다.
  - malformed arc 처리 coverage gap은 이미 `MFS-T3` 문서 말미에 정리되어 있고, 이번 T4 범위에서 신규 semantic-preservation finding으로 재오픈할 근거는 부족했다.
- 후보 E도 제거했다.
  - `tests/test_stage4_context.py`와 runtime path를 대조한 결과, `Stage4Context`의 callback 포획 자체는 현재 조사 범위에서 drift가 아니라 안정된 wiring으로 보였다.
- 후보 A/B/C는 retained finding으로 유지했다.
  - 후보 A는 static code + synthetic verification으로 재현이 가능했다.
  - 후보 B는 `prepare_episode_context()`와 `_load_narrative_summaries()`의 source/range/unit 차이가 `Stage4InterviewRound`까지 동시에 전달되는 runtime chain으로 확인됐다.
  - 후보 C는 `Stage1`의 boundary REJECT와 `Stage4`의 future context injection이 같은 “미래 경계”를 서로 다른 의미로 사용하지만 이를 연결하는 정책/validator가 없음을 확인했다.

### PASS 3 - 최종 확정

- PASS1 후보 `5건`
- PASS2 제거 `2건`
- 최종 확정 `3건`

## Finding Ledger

| ID | Sev | Type | 상태 | 파일/함수 | 요약 | 중복 여부 |
|----|-----|------|------|-----------|------|-----------|
| `MCS-T4-001` | `P1` | `semantic-loss` | confirmed | `main_a.py::_load_narrative_summaries`, `stage4_context_builder.py::build_mandatory_context`, `context_compression.py::_smart_trim` | `mandatory_context` trim이 past summary와 future arc context를 비대칭적으로 보존해 이전 서사 의미가 future hint보다 먼저 탈락할 수 있다 | `related-but-new-cross-stage-semantic-surface` |
| `MCS-T4-002` | `P2` | `semantic-rewrite` | confirmed | `stage4_context_builder.py::prepare_episode_context`, `main_a.py::_load_narrative_summaries`, `stage4_interview_round.py` | Stage4가 past-story 의미를 서로 다른 range/unit을 쓰는 두 summary 채널로 동시에 전달해 동일 사건의 경계 의미가 한 곳에 잠기지 않는다 | `related-but-new-cross-stage-semantic-surface` |
| `MCS-T4-003` | `P2` | `semantic-bypass` | confirmed | `main_a.py::_validate_volume_boundaries`, `stage01_helpers.py::stage_1_volumes`, `stage4_context_builder.py::_build_future_arc_context` | Stage1의 future-volume boundary는 REJECT인데 Stage4는 next-arc future plan을 mandatory context로 주입하며, 둘 사이를 잇는 공통 boundary contract가 없다 | `related-but-new-cross-stage-semantic-surface` |

---

## [MCS-T4-001] P1

1. ID
   - `MCS-T4-001`
2. Severity
   - `P1`
3. 현상 요약
   - `Stage4ContextBuilder.build_mandatory_context()`는 past-story narrative summary를 `_mc_parts` 후반에 붙인 뒤, 바로 다음에 future arc context를 append한다.
   - 이후 `_compose_mandatory_context_with_headroom()`와 `ContextCompressor._smart_trim()`은 `mandatory_context`를 “앞 60% + 뒤 40%” 방식으로 잘라 middle을 버린다.
   - 그 결과 prior-episode meaning을 담는 narrative summary는 빠지고, tail에 가까운 future arc context만 살아남는 비대칭이 발생한다.
   - synthetic verification에서도 작은 max cap에서 `SUMMARYBLOCK`는 사라지고 `FUTUREBLOCK`는 남았다.
4. 코드 근거
   - `main_a.py:3385-3426`은 `_load_narrative_summaries()`가 5화 단위 summary와 series/volume summary를 조합해 하나의 장문 문자열로 반환함을 보여 준다.
   - `modules/core/stage4_context_builder.py:2447-2456`은 `_narrative_summaries`를 append한 뒤 `_future_ctx`를 바로 append한다.
   - `modules/core/stage4_context_builder.py:1447-1503`은 `context.mandatory_context_max` 기준으로 `mc_body`와 최종 `mandatory_context`를 다시 trim한다.
   - `modules/core/context_compression.py:187-197`의 `_smart_trim()`은 시작 60%, 끝 40%만 남기고 middle을 생략한다.
   - `modules/core/stage4_interview_round.py:1219,1736`은 trim된 `mandatory_context`를 그대로 Writer/Director에 전달한다.
5. downstream 영향 경계
   - Stage4 Writer/Director는 같은 prompt 안에서 미래 arc 힌트는 보지만, 바로 이전 장기 서사 요약은 잃을 수 있다.
   - partial resume, 장기 누적 작품, dense retrieval 환경일수록 “과거 의미가 줄고 미래 힌트가 남는” 왜곡이 커진다.
   - 이는 stage handoff 의미 보존 관점에서 `past continuity > future hint` 우선순위를 뒤집는 효과를 낸다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage4_context_builder.py:764-810`은 길이 제한과 headroom만 확인하고, narrative summary나 future context가 실제로 살아남는지는 검증하지 않는다.
   - `tests/test_stage4_context_builder.py:32`는 `ctx.load_narrative_summaries = MagicMock(return_value="")`로 고정해 실제 narrative summary 경로를 비운다.
   - `tests/test_stage4_context.py:166-177`은 callback wiring만 본다.
   - `tests/test_sweep23.py:19-26`은 summary 생성기 crash 방지만 확인한다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - `MPN-T4-003`은 series/volume summary 중복 적재와 상한 drift를 지적했지만, 본 finding은 “trim 이후 past summary가 future context보다 먼저 탈락하는 보존 우선순위 역전”을 신규로 확정한다.
8. 권장 후속 조치
   - narrative summary와 future arc context를 동일한 장문 블록으로 두지 말고 보호 우선순위를 명시한 별도 section으로 관리한다.
   - 최소 회귀 테스트로 `SUMMARYBLOCK`와 `FUTUREBLOCK`를 동시에 넣은 뒤, 작은 budget에서도 어느 쪽이 살아남아야 하는지 계약을 잠근다.
   - `_smart_trim()`을 계속 쓸 경우에는 Stage4 mandatory context에 대해 head/tail이 아니라 section-aware trim을 적용해야 한다.

## [MCS-T4-002] P2

1. ID
   - `MCS-T4-002`
2. Severity
   - `P2`
3. 현상 요약
   - Stage4는 past-story 의미를 두 채널로 동시에 전달한다.
   - `prepare_episode_context()`는 `prev_manuscripts_text`에 최근 30화 full text, 21~60화 전 episode_meta summary, 그보다 오래된 arc summary를 누적한다.
   - 반면 `_load_narrative_summaries()`는 별도 anchor 저장소에서 5화 단위 narrative summary와 series/volume summary를 읽어 `mandatory_context`에 붙인다.
   - 두 채널은 source, range, granularity가 다르지만 Writer/Director에는 함께 전달되고, 둘 사이에 dedupe나 coherence check가 없다.
4. 코드 근거
   - `modules/core/stage4_context_builder.py:1676-1788`은 `prev_manuscripts_text`를 Tier1 full text + Tier2 `episode_meta.summary` + Tier3 `arc_summary_*`로 만든다.
   - `main_a.py:3356-3359`는 `_generate_narrative_summary()`가 `ep_range` 기반 5화 summary anchor를 저장함을 보여 준다.
   - `main_a.py:3385-3420`은 `_load_narrative_summaries()`가 저장된 5화 summary와 series/volume summary를 다시 하나의 문자열로 로드한다.
   - `modules/core/stage4_context_builder.py:2447-2449`은 이 문자열을 `mandatory_context`에 붙인다.
   - `modules/core/stage4_interview_round.py:1205-1228`은 Writer kwargs에 `mandatory_context`와 `prev_manuscripts_text`를 둘 다 넣는다.
   - `modules/core/stage4_interview_round.py:1736-1737`은 Director에도 `mandatory_context`와 `prev_manuscripts_text`를 함께 넘긴다.
5. downstream 영향 경계
   - 동일 사건이 episode summary, 5화 narrative summary, arc summary, volume summary 등 서로 다른 범위/라벨로 동시에 주입될 수 있다.
   - sparse resume나 manual cleanup 뒤에는 “이 summary가 어느 범위를 대표하는가”가 stage 내부에서 일관되게 해석되지 않을 수 있다.
   - Writer/Director가 동일 과거를 서로 다른 granularity로 받으므로, same narrative boundary가 single SSOT에 잠기지 않는다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage4_context_builder.py:311-417`은 `prev_manuscripts_text`의 tier2/tier3 조립만 본다.
   - `tests/test_stage4_context_builder.py:32`는 `_load_narrative_summaries()` 경로를 빈 문자열 mock으로 비워 두기 때문에 dual-channel coherence를 검증하지 못한다.
   - `tests/test_stage4_context.py:166-177`은 callback 주입만 본다.
   - 두 채널이 동시에 non-empty일 때 Writer/Director prompt에 어떤 중복/충돌이 생기는지 보는 test는 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - `MPN-T4-001/003`은 stale summary와 series/volume duplicate를 다뤘고, 본 finding은 `prev_manuscripts_text`와 `mandatory_context`가 서로 다른 summary source를 동시 handoff하는 runtime contract 자체를 신규로 확정한다.
8. 권장 후속 조치
   - Stage4 past-history SSOT를 하나로 정하고, 다른 채널은 그 SSOT에서 파생되게 바꾼다.
   - 최소한 `_load_narrative_summaries(current_ep=...)` 같은 episode-aware loader로 바꿔 `prev_manuscripts_text`와 같은 boundary plan 아래 놓아야 한다.
   - integration test에서 `episode_meta.summary`와 `narrative_summary_ep_*`를 동시에 채운 뒤 Writer/Director 입력이 중복/충돌 없이 조립되는지 확인해야 한다.

## [MCS-T4-003] P2

1. ID
   - `MCS-T4-003`
2. Severity
   - `P2`
3. 현상 요약
   - Stage1에서는 volume strategy 문서에 future volume 정보가 들어가면 `_validate_volume_boundaries()`가 REJECT한다.
   - 그런데 Stage4에서는 `_build_future_arc_context()`가 현재 Arc 남은 blueprint와 다음 Arc 계획을 `mandatory_context`에 적극적으로 주입한다.
   - 즉 같은 “미래 경계”가 Planning/Volume 설계에서는 금지 신호이고, Stage4 원고 단계에서는 필수 guidance처럼 취급된다.
   - 이를 이어 주는 명시적 policy, validator, metadata flag가 보이지 않는다.
4. 코드 근거
   - `main_a.py:2685-2709`에서 `_validate_volume_boundaries()`는 미래 권 번호와 미래 지향 키워드를 검사해 `REJECT`/`WARNING`을 반환한다.
   - `modules/core/stage01_helpers.py:776-783`은 Stage1 success gate에서 이 validator를 직접 호출한다.
   - `modules/core/stage4_context_builder.py:1597-1645`는 `_build_future_arc_context()`가 현재 Arc 남은 화 blueprint와 다음 Arc 제목/비트/방향을 생성함을 보여 준다.
   - `modules/core/stage4_context_builder.py:2454-2456`은 이를 `mandatory_context`에 append한다.
   - `tests/test_stage01_helpers.py:529-544`는 validator를 `PASS` stub으로만 사용하고, `tests/test_stage4_context_builder.py`에는 `_build_future_arc_context()`의 semantic contract를 직접 검증하는 테스트가 없다.
5. downstream 영향 경계
   - “future boundary”의 의미가 stage마다 바뀌므로, 감리나 handoff 문서가 동일 용어를 서로 다른 뜻으로 읽을 위험이 있다.
   - volume 경계 직전/직후, partial resume, foreshadow-safe 범위 판단에서 특히 semantic bypass가 생긴다.
   - Stage1은 lexical/textual REJECT, Stage4는 structural future-plan injection이라는 서로 다른 메커니즘을 사용하므로 single SSOT가 없다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage01_helpers.py:529-544`는 `_validate_volume_boundaries()`의 실제 의미를 실행하지 않는다.
   - `tests/test_stage4_context_builder.py:794-810`은 `_build_future_arc_context()`를 patch한 채 길이 제한만 본다.
   - Stage1 boundary rule과 Stage4 future injection을 함께 검증하는 cross-stage test는 없다.
7. 기존 문서와의 중복 여부
   - `related-but-new-cross-stage-semantic-surface`
   - `MPN-T3-001/002/003`은 `_validate_volume_boundaries()`의 fail-open, hidden coupling, test blind spot을 다뤘다. 본 finding은 그 validator와 Stage4 future-context injection 사이의 “의미 polarity flip”을 cross-stage contract 문제로 신규 확정한다.
8. 권장 후속 조치
   - `future_boundary_policy` 같은 명시적 계약을 두고, Stage1에서 금지되는 미래 정보와 Stage4에서 허용되는 foreshadow-safe future info를 구분해야 한다.
   - `_build_future_arc_context()`가 next-volume/next-arc 정보를 넣기 전에 policy flag나 arc metadata를 확인하도록 경계를 잠근다.
   - cross-stage 회귀 테스트로 “같은 작품, 같은 arc 경계”에서 Stage1 REJECT 조건과 Stage4 허용 범위를 동시에 검증해야 한다.

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_get_arc_context_for_episode()` real facade semantics | `already-covered-do-not-reopen` | `MFS-T3`에서 malformed arcs coverage gap으로 이미 기록. 재오픈 대신 real facade test를 별도 트랙에서 처리 |
| `_build_future_arc_context()` direct semantic test | 미검증 | 현재 Arc 끝/volume 경계/다음 Arc 존재 여부에 따라 어떤 future scope가 허용되는지 직접 검증하는 단위 테스트 |
| summary section-aware trim 규약 | 미검증 | `mandatory_context`에서 narrative summary, future arc context, work-slot summary의 보존 우선순위를 고정하는 regression test |

## PASS1 후보 -> PASS2 제거 -> PASS3 확정

- PASS1 후보 5건
  - narrative summary / future context trim 비대칭
  - dual summary channel boundary drift
  - Stage1 boundary vs Stage4 future injection polarity flip
  - `_get_arc_context_for_episode()` real facade coverage gap
  - `Stage4Context` callback wiring drift 가설
- PASS2 제거 2건
  - `_get_arc_context_for_episode()`는 이번 문서의 신규 finding이 아니라 `MFS-T3` coverage gap으로 유지
  - `Stage4Context` callback wiring은 현재 범위에서 semantic drift가 아니라 정상 wiring으로 확인
- PASS3 확정 3건
  - `MCS-T4-001`
  - `MCS-T4-002`
  - `MCS-T4-003`

## 마감 체크

- 코드 근거 포함: 완료
- downstream 영향 경계 포함: 완료
- 현재 테스트 근거 또는 테스트 부재 포함: 완료
- 기존 문서와의 중복 여부 포함: 완료
- PASS1 -> PASS2 -> PASS3 요약 포함: 완료
