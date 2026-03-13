# MDH-T3: Stage01 / NPC / UI Helper Liveness Findings

> Terminal: T3
> 작성일: 2026-03-13
> 작성자: Claude Opus
> 상태: `PASS3-confirmed`
> 오더: `main_a-dormant-helper-live-consumer-detail-full-survey-audit-order.md`

---

## 0. 조사 범위

| Helper | 정의 위치 | 위임 대상 |
|--------|-----------|-----------|
| `_validate_volume_boundaries()` | `main_a.py:2685-2716` | 자체 구현 (32줄) |
| `_extract_npc_profiles()` | `main_a.py:2764-2766` | `StateService` → `PromptBuilder` |
| `_get_character_traits()` | `main_a.py:2768-2770` | `StateService` → `PromptBuilder` |
| `_load_character_archetypes()` | `main_a.py:2772-2774` | `StateService` (직접 구현) |
| `_get_archetype_reference_for_npcs()` | `main_a.py:2776-2778` | `StateService` (직접 구현) |
| `_show_volume_table()` | `main_a.py:2863-2865` | `UIService` |

---

## 1. Findings

### MDH-T3-001 — NPC/Archetype Facade Chain 4종 전량 Dormant

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T3-001 |
| **Severity** | P2 |
| **현상 요약** | `_extract_npc_profiles`, `_get_character_traits`, `_load_character_archetypes`, `_get_archetype_reference_for_npcs` — 4개 facade helper가 main_a.py에 정의되어 있으나 production caller가 **0건**이다. test-only surface. |
| **코드 근거** | (1) `main_a.py:2764-2778` — 4개 thin delegate 정의. (2) 전역 grep 결과: `stage01_helpers.py`, `stage2_orchestrator.py`, `stage3_orchestrator.py`, `stage4_orchestrator.py`, `stage4_interview_round.py`, `stage4_context.py`, `stage4_context_builder.py` 등 **어떤 production 모듈에서도 호출하지 않음**. (3) DI Context(`stage2_context.py`, `stage3_context.py`, `stage4_context.py`) 콜백에도 미등록. (4) `state_service.py:162-234`의 `get_archetype_reference_for_npcs()`가 내부에서 `load_character_archetypes()`를 호출하지만, `get_archetype_reference_for_npcs()` 자체가 production에서 호출되지 않으므로 **전이적 dormant**. |
| **downstream 영향 경계** | production 무영향. 이 helper들이 제거되어도 runtime 동작 변화 없음. 단, `PromptBuilder.extract_npc_profiles()`와 `PromptBuilder.get_character_traits()`는 PromptBuilder 내부에서 독립 호출 가능성이 있으므로 **PromptBuilder 내부 경로는 별도 확인 필요**. |
| **테스트 근거** | `test_state_service.py:159-230` (delegate 검증 + archetype 로직), `test_prompt_builder.py:453-457` (app=None guard). 모두 unit test isolation. production flow 테스트 없음. |
| **기존 문서 중복 여부** | `related-but-new-live-consumer-surface` — MFS-T4-001 (P1)이 "Stage4가 NPC facade를 bypass한다"고 보고했으나, 그 문서는 bypass 자체의 semantic 손실을 다룬 것이고, 본 finding은 **facade 자체가 어디에서도 호출되지 않는 dormant export**라는 inventory 사실을 확정한다. |
| **권장 후속 조치** | (1) 4개 main_a facade를 dead export로 태깅. (2) StateService 내 archetype 구현(`L150-234`)이 향후 사용 계획이 없으면 함께 정리 대상. (3) PromptBuilder 내부 `extract_npc_profiles` / `get_character_traits`는 PromptBuilder 자신이 내부에서 쓰는지 별도 확인 (본 조사 범위 외). |

---

### MDH-T3-002 — _show_volume_table hasattr 방어 호출

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T3-002 |
| **Severity** | P3 |
| **현상 요약** | `_show_volume_table()`은 `stage01_helpers.py:838`에서 `hasattr(app, "_show_volume_table")` 가드를 거쳐 호출된다. production caller 1건 존재하므로 **live**이나, hasattr 가드는 이 helper가 optional/legacy surface임을 암시한다. |
| **코드 근거** | (1) `main_a.py:2863-2865` — thin delegate → `UIService.show_volume_table()`. (2) `stage01_helpers.py:838-839`: `if hasattr(app, "_show_volume_table"): app._show_volume_table(final_volumes)`. (3) `SovereignApp`은 항상 이 메서드를 가지므로 hasattr 검사는 사실상 항상 True. |
| **downstream 영향 경계** | Stage 1 volume 완료 후 UI 표시 전용. 기능 누락 시 사용자에게 volume 결과 테이블이 안 보일 뿐, 데이터 무결성 무영향. |
| **테스트 근거** | `test_ui_service.py:116-127` (table 렌더링 + empty list), `test_stage01_helpers.py:529` (mock으로 호출 확인). |
| **기존 문서 중복 여부** | `related-but-new-live-consumer-surface` — MFS-T4-002 (P3)가 volume table의 "10권 하드코딩" UI 문제를 다루었으나, 본 finding은 **hasattr 방어 패턴이 facade liveness를 불명확하게 만드는 naming drift** 관점이다. |
| **권장 후속 조치** | (1) hasattr 가드를 제거하고 직접 호출로 전환 (SovereignApp이 항상 해당 메서드를 보유). (2) 또는 Protocol/ABC로 계약 명시. |

---

### MDH-T3-003 — _validate_volume_boundaries: LIVE 확정

| 필드 | 내용 |
|------|------|
| **ID** | MDH-T3-003 |
| **Severity** | — (finding 아님, inventory 확정) |
| **현상 요약** | `_validate_volume_boundaries()`는 production caller 1건(`stage01_helpers.py:776`), test caller 1건(`test_stage01_helpers.py:529`). **LIVE**. |
| **코드 근거** | `stage01_helpers.py:776`: `boundary_check = app._validate_volume_boundaries(vol_data, _vi)` — Stage 1 volume 설계 루프 내에서 매 volume마다 호출. REJECT 시 해당 volume 재생성. |
| **downstream 영향 경계** | Stage 1 volume 설계 품질 게이트. 미래 권 정보 누수 방지. |
| **테스트 근거** | `test_stage01_helpers.py:529` — mock으로 `{"status": "PASS"}` 반환. 경계 검증 로직 자체의 unit test는 미확인 (별도 test 파일 없음). |
| **기존 문서 중복 여부** | `none` |
| **권장 후속 조치** | 경계 검증 로직(`re.findall` + 미래 키워드 카운트) 자체의 unit test 추가 권장 (현재는 통합 테스트에서 mock으로만 검증). |

---

## 2. Live Consumer Inventory

| Helper | 상태 | Production Caller | Test Caller | DI 콜백 |
|--------|------|-------------------|-------------|---------|
| `_validate_volume_boundaries` | **live** | `stage01_helpers.py:776` (1건) | `test_stage01_helpers.py:529` | 미등록 |
| `_extract_npc_profiles` | **dormant** | 0건 | `test_prompt_builder.py:454`, `test_state_service.py:164` | 미등록 |
| `_get_character_traits` | **dormant** | 0건 | `test_prompt_builder.py:457`, `test_state_service.py:174` | 미등록 |
| `_load_character_archetypes` | **dormant** | 전이적 dormant (caller가 dormant) | `test_state_service.py:188,196` | 미등록 |
| `_get_archetype_reference_for_npcs` | **dormant** | 0건 | `test_state_service.py:205,209,225` | 미등록 |
| `_show_volume_table` | **live** | `stage01_helpers.py:838` (1건, hasattr guard) | `test_ui_service.py:122,126` | 미등록 |

---

## 3. PASS1 → PASS2 → PASS3 요약

### PASS 1 — 표면 수집

| 후보 | 확신도 | 임시 태깅 |
|------|--------|-----------|
| NPC 4종 facade dormant | HIGH | dormant |
| _show_volume_table hasattr guard | MED | live (defensive) |
| _validate_volume_boundaries live | HIGH | live |
| PromptBuilder 내부 경로 가능성 | LOW | unknown |

### PASS 2 — 교차 검증

- NPC 4종: 전역 grep 재확인. `modules/core/` 전역, `tests/` 전역, DI Context 3종 모두 검색. production caller **0건** 확정. `state_service.py` 내부의 `load_character_archetypes` 호출은 `get_archetype_reference_for_npcs` 내부이나, 이 함수 자체가 호출되지 않으므로 전이적 dormant 확정.
- _show_volume_table: `stage01_helpers.py:838` live caller 확인. hasattr 가드는 SovereignApp이 항상 해당 메서드를 보유하므로 사실상 dead guard.
- _validate_volume_boundaries: `stage01_helpers.py:776` live caller 확인. 정상 작동.
- MFS-T4-001 / MFS-T4-002와의 중복 확인: facade bypass(MFS-T4-001)와 dormant export(본 MDH-T3-001)는 관점이 다르므로 신규 finding으로 채택 가능.

### PASS 2 제거

- PromptBuilder 내부 경로: 본 조사 범위(main_a facade) 밖. `unknown` → `coverage gap`으로 분리.

### PASS 3 — 최종 확정

| Finding | PASS1 | PASS2 | PASS3 |
|---------|-------|-------|-------|
| MDH-T3-001 (P2) NPC 4종 dormant | 채택 | 확정 | **확정** |
| MDH-T3-002 (P3) hasattr guard | 채택 | 확정 | **확정** |
| MDH-T3-003 (—) volume boundaries live | 채택 | 확정 | **확정 (finding 아님, inventory)** |

### Coverage Gap

- `PromptBuilder.extract_npc_profiles()` / `PromptBuilder.get_character_traits()`가 PromptBuilder 내부 다른 메서드에서 호출되는지 여부 → 본 조사 범위 외, 별도 확인 필요.

### Open Question

- NPC 4종 facade가 의도적으로 예비 보존된 것인지, 단순 carry-over인지는 프로젝트 오너 확인 필요.

---

## 4. 조사 완료 선언

- T3 범위 6개 helper 전량 조사 완료.
- 3PASS 프로토콜 준수.
- 코드 수정 0건.
