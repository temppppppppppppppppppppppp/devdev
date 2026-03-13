# MDH-T3: Stage01 / NPC / UI Helper Liveness Findings

> Terminal: `T3`
> 작성일: 2026-03-13
> 재감리: Codex (`OPUS` 초안 교차 검증 + 보강)
> 상태: `PASS3-reaudited`
> 오더: `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 실행 검증:
> - `python -X utf8 -m pytest tests/test_stage01_helpers.py tests/test_ui_service.py tests/test_prompt_builder.py tests/test_state_service.py -q` -> `137 passed`
> - `python -X utf8 -m pytest tests/test_stage4_context.py -q` -> `16 failed, 12 errors`
>   - helper liveness 자체와는 별개로 `Stage4Context.__slots__`에 `generate_writer_guidance_v60_8`, `enrich_director_result`가 빠져 callback 저장 단계에서 선행 실패
> 인코딩 검증:
> - 본 조사에 사용한 코드/테스트/문서와 현재 결과 문서에서 question-mark triplet, `U+FFFD` replacement char 미검출

---

## 0. 재감리 핵심 보정

OPUS 초안에서 바로잡은 점은 아래 3가지다.

1. `main_a.py` facade 직접 테스트와 `StateService` / `PromptBuilder` 단위 테스트를 분리했다.
   - 기존 초안은 service-level 테스트를 facade test처럼 적은 부분이 있었다.
2. `_validate_volume_boundaries()`와 `_show_volume_table()`는 **live helper**가 맞지만, direct facade regression이 있는 것은 아니다.
   - `tests/test_stage01_helpers.py`는 `_validate_volume_boundaries`를 mock으로만 주입한다.
   - `tests/test_ui_service.py`는 `UIService.show_volume_table()`만 검증한다.
3. `stage4_context.py`는 이번 helper 6종의 live consumer 근거가 아니다.
   - `from_app()`가 뽑는 callback 목록에 이번 T3 helper는 없다.
   - 관련 테스트도 현재 `__slots__` drift로 깨져 있어 positive proof로 쓰기 어렵다.

---

## 1. 조사 범위

| Helper | 정의 위치 | 현재 역할 |
|--------|-----------|-----------|
| `_validate_volume_boundaries()` | `main_a.py:2730-2762` | Stage 1 권 경계 검증 자체 구현 |
| `_extract_npc_profiles()` | `main_a.py:2809-2811` | `StateService -> PromptBuilder` thin delegate |
| `_get_character_traits()` | `main_a.py:2813-2815` | `StateService -> PromptBuilder` thin delegate |
| `_load_character_archetypes()` | `main_a.py:2817-2819` | `StateService` thin delegate |
| `_get_archetype_reference_for_npcs()` | `main_a.py:2821-2823` | `StateService` thin delegate |
| `_show_volume_table()` | `main_a.py:2908-2910` | `UIService.show_volume_table()` thin delegate |

직접 downstream 확인 범위:

- `modules/core/stage01_helpers.py`
- `modules/core/stage4_context.py`
- `modules/core/services/state_service.py`
- `modules/core/prompt_builder.py`
- `modules/core/services/ui_service.py`
- `tests/test_stage01_helpers.py`
- `tests/test_ui_service.py`
- `tests/test_prompt_builder.py`
- `tests/test_state_service.py`
- `tests/test_stage4_context.py`
- `docs/stage_map/stage1.md`

---

## 2. Findings

### MDH-T3-001 - NPC / archetype facade 4종은 현행 runtime consumer가 없는 dormant surface

| 필드 | 내용 |
|------|------|
| ID | `MDH-T3-001` |
| Severity | `P2` |
| 현상 요약 | `main_a.py`의 `_extract_npc_profiles`, `_get_character_traits`, `_load_character_archetypes`, `_get_archetype_reference_for_npcs`는 모두 thin delegate로 남아 있지만, 현행 repo 기준 direct production caller가 없다. direct facade regression test도 없다. 남아 있는 실행 근거는 `StateService` / `PromptBuilder` 단위 테스트뿐이다. |
| 코드 근거 | (1) `main_a.py:2809-2823`에 4개 facade가 연속 정의되어 있고 모두 `self._state_service`로 즉시 위임된다. (2) `modules/core/services/state_service.py:140-167`는 다시 `PromptBuilder` 위임 또는 내부 archetype 로직으로 연결된다. (3) `modules/core/prompt_builder.py:930-968`에는 `extract_npc_profiles()` / `get_character_traits()` 구현이 남아 있다. (4) repo 전역 exact-name 검색 결과, 현행 production 코드에서 이 4개 facade 이름의 호출은 발견되지 않았다. (5) `modules/core/stage4_context.py:168-199`의 `from_app()` callback 추출 목록에도 이번 4개 helper는 없다. |
| downstream 영향 경계 | 현재 runtime에서 이 4개 facade를 제거해도 직접적인 실행 경로 변화는 없을 가능성이 높다. 다만 facade 표면이 살아 있어 유지보수자가 `main_a -> StateService -> PromptBuilder` 체인이 실제로 소비된다고 오인할 수 있다. 실제 semantic 영향은 별도 문서 `MFS-T4-001`이 다룬 Stage4 bypass 축에서 이미 나타난다. |
| 현재 테스트 근거 또는 테스트 부재 | direct facade test는 `0건`이다. `tests/test_state_service.py:164-225`와 `tests/test_prompt_builder.py:453-457`은 underlying service/helper를 검증할 뿐, `main_a.py` facade 호출을 검증하지 않는다. |
| 기존 문서와의 중복 여부 | `related-but-new-live-consumer-surface` - `MFS-T4-001`은 Stage4 live validation path가 NPC sourcing을 우회한다는 semantic finding이고, 본 문서는 `main_a.py` facade 자체에 direct caller가 없다는 inventory 사실을 확정한다. |
| 권장 후속 조치 | (1) 4개 facade를 `deprecated / dormant`로 명시하거나 제거 후보로 분류한다. (2) 유지할 계획이면 facade-level regression test를 추가해 "정말 계약 표면으로 유지할 것인지"를 먼저 고정한다. (3) Stage4가 쓸 NPC sourcing SSOT가 `PromptBuilder.build_validation_context()`인지, 별도 helper 체인인지 문서로 고정한다. |

---

### MDH-T3-002 - `_show_volume_table()`는 live helper지만 contract가 duck-typed이고 facade-level 회귀가 없다

| 필드 | 내용 |
|------|------|
| ID | `MDH-T3-002` |
| Severity | `P3` |
| 현상 요약 | `_show_volume_table()`는 dormant가 아니라 Stage 1 종료 경로의 live consumer를 가진다. 다만 `Stage01Helpers`는 이를 `hasattr(app, "_show_volume_table")`로 optional surface처럼 호출하고, direct facade regression test는 없다. 즉, live consumer inventory 관점에서는 "살아 있지만 명시 계약이 약한 helper"다. |
| 코드 근거 | (1) `main_a.py:2908-2910` - `_show_volume_table()`는 `UIService.show_volume_table()` thin delegate다. (2) `modules/core/stage01_helpers.py:838-839` - Stage 1 완료 후 `hasattr(app, "_show_volume_table")`를 거쳐 `app._show_volume_table(final_volumes)`를 호출한다. (3) `docs/stage_map/stage1.md:27-28,125` - Stage 1 map은 `_show_volume_table(final_volumes)`를 operator completion check로 문서화한다. (4) `modules/core/services/ui_service.py:90-100` - 실질 UI 출력은 서비스 구현이 담당한다. |
| downstream 영향 경계 | 현재 영향은 operator-facing presentation에 한정된다. DB 저장과 메모리 동기화는 이 호출 전에 끝난다. 따라서 helper 누락이 즉시 데이터 손실로 이어지지는 않지만, Stage 1 완료 확인 surface가 optional처럼 남아 있으면 UI contract 회귀를 조기에 잡기 어렵다. |
| 현재 테스트 근거 또는 테스트 부재 | direct facade test는 `0건`이다. `tests/test_ui_service.py:122-126`은 `UIService.show_volume_table()`만 검증한다. `tests/test_stage01_helpers.py:519-544`는 성공 경로를 돌리지만 `_show_volume_table()` 호출 여부를 assert하지 않는다. |
| 기존 문서와의 중복 여부 | `related-but-new-live-consumer-surface` - `MFS-T4-002`는 `_show_volume_table()`의 제목 라벨 drift를 다룬다. 본 finding은 그보다 좁게, live helper contract가 `hasattr` duck-typing과 테스트 부재에 기대고 있다는 inventory/coverage 문제를 확정한다. 기존 title drift finding은 재오픈하지 않는다. |
| 권장 후속 조치 | (1) `Stage01Helpers`에서 `hasattr` guard를 제거하거나 protocol로 명시한다. (2) `tests/test_stage01_helpers.py`에 `_show_volume_table(final_volumes)` 호출 assertion을 추가한다. (3) presentation semantics 자체는 기존 `MFS-T4-002` 후속 조치로 계속 추적한다. |

---

## 3. Live Consumer Inventory

| Helper | 상태 | Production caller | Direct facade test | Service / mock 수준 근거 | 중복 처리 |
|--------|------|-------------------|--------------------|--------------------------|-----------|
| `_validate_volume_boundaries` | `live` | `modules/core/stage01_helpers.py:776` | `0건` | `tests/test_stage01_helpers.py:529`는 mock만 주입 | `already-covered-do-not-reopen` |
| `_extract_npc_profiles` | `dormant` | `0건` | `0건` | `tests/test_state_service.py:164-165`, `tests/test_prompt_builder.py:453-454` | `MDH-T3-001` |
| `_get_character_traits` | `dormant` | `0건` | `0건` | `tests/test_state_service.py:174-175`, `tests/test_prompt_builder.py:456-457` | `MDH-T3-001` |
| `_load_character_archetypes` | `dormant` | `0건` | `0건` | `tests/test_state_service.py:188-196` | `MDH-T3-001` |
| `_get_archetype_reference_for_npcs` | `dormant` | `0건` | `0건` | `tests/test_state_service.py:205-225` | `MDH-T3-001` |
| `_show_volume_table` | `live` | `modules/core/stage01_helpers.py:838-839` | `0건` | `tests/test_ui_service.py:122-126`는 service만 검증 | `MDH-T3-002` |

해석:

- `live`와 `tested`는 같은 뜻이 아니다.
- `_validate_volume_boundaries`와 `_show_volume_table`는 runtime consumer가 있지만, direct facade regression은 없다.
- NPC / archetype 4종은 facade, service delegate, 구현체가 모두 남아 있지만 현행 runtime consumer는 없다.

---

## 4. PASS1 -> PASS2 -> PASS3 요약

### PASS 1 - 표면 수집

| 후보 | 확신도 | 임시 태깅 |
|------|--------|-----------|
| NPC / archetype facade 4종 dormant | HIGH | dormant |
| `_show_volume_table` live but weak contract | MED | live |
| `_validate_volume_boundaries` live | HIGH | live |
| `stage4_context.py`가 helper consumer를 숨기고 있을 가능성 | LOW | unknown |

### PASS 2 - 교차 검증

- repo 전역 exact-name 검색으로 `main_a.py` facade 직접 caller를 다시 셌다.
  - NPC / archetype 4종: production caller `0`
  - `_validate_volume_boundaries`: production caller `1`
  - `_show_volume_table`: production caller `1`
- direct facade test 여부를 다시 분리했다.
  - `tests/test_stage01_helpers.py:529`는 `_validate_volume_boundaries`를 mock으로만 사용한다.
  - `tests/test_ui_service.py:122-126`는 `UIService.show_volume_table()`만 검증한다.
  - `tests/test_state_service.py`, `tests/test_prompt_builder.py`는 main facade가 아니라 underlying helper만 검증한다.
- `stage4_context.py`를 재확인한 결과, 이번 T3 helper 6종은 `from_app()` callback 목록에 없다.
- `tests/test_stage4_context.py`는 helper liveness 확인 전에 `Stage4Context.__slots__` drift로 실패하므로, positive evidence로 채택하지 않았다.

### PASS 2 제거 / 보정

- "`test-only surface`"라는 OPUS 표현은 facade 기준으로는 부정확해서 삭제했다.
  - 정확한 표현은 "`direct facade test 0건, underlying service test만 존재`"다.
- "`hasattr` guard 자체가 legacy 확정"이라는 표현은 과해서 삭제했다.
  - 대신 "optional duck-typed contract"로 완화했다.
- `_validate_volume_boundaries`는 live inventory에는 남기되 신규 finding으로 재오픈하지 않았다.
  - 이 축은 `MPN-T3-*`, `MCS-T4-*` 문서가 이미 다룬다.

### PASS 3 - 최종 확정

| Finding | PASS1 | PASS2 | PASS3 |
|---------|-------|-------|-------|
| `MDH-T3-001` NPC / archetype facade 4종 dormant | 채택 | 확정 | **확정** |
| `MDH-T3-002` `_show_volume_table` live but weak contract | 채택 | 보정 후 확정 | **확정** |
| `_validate_volume_boundaries` live note | 채택 | inventory only | **finding 비채택** |
| `stage4_context.py` hidden consumer 가능성 | 후보 | 근거 부족 | **coverage gap로 이동** |

---

## 5. Coverage Gap / Open Question

| 항목 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| main facade direct regression | 6개 helper 전부 `0건` | `main_a.py` facade를 직접 호출하는 regression test |
| `stage4_context.py` callback inventory 신뢰도 | 테스트 suite가 현재 red | `__slots__` drift 정리 후 callback extraction test 재실행 |
| dormant NPC / archetype helper의 one-shot consumer | 미발견 | canary / manual path / runtime artifact에서 exact-name 호출 증거 |

추가 해석:

- 이번 재감리에서는 `main_a.py` facade **직접 caller**를 기준으로 liveness를 잠갔다.
- 서비스 구현이 남아 있다는 사실만으로 facade를 live로 분류하지 않았다.
- 기존 OPUS 초안보다 보수적으로 확정했으며, 직접 근거가 없는 항목은 전부 coverage gap로 후퇴시켰다.

---

## 6. 조사 완료 선언

- T3 범위 helper 6개 재조사 완료
- 3PASS 재감리 완료
- direct facade 기준 live / dormant inventory 재잠금 완료
- 코드 수정 0건
