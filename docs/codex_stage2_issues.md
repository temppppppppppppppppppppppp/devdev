# 📋 Codex Stage 2 이슈 리포트 (수동 재검증 보강본)

> **보강일**: 2026-02-20  
> **대상 범위**: `modules/core/stage2_*.py` + `modules/domain/agents/arc_*.py`, `four_phase_arc_generator.py`, `continuity_arc.py`  
> **검증 방식**: 코드 수동 판독(라인 근거 기반), 과장 문구 보정

---

## 재검증 결론

- 문서의 핵심 방향은 유효함.
- 다만 `#1`, `#3`, `#5`는 표현 강도를 보정해야 정확함.
- 즉시 운영 영향이 큰 항목은 `#2`(async 블로킹 I/O), `#8`(ep_count 폴백 매직넘버), 장르 결정 경로(`#3`)임.

---

## 이슈 요약 (보강판)

| # | 심각도 | 판정 | 파일 | 이슈 | 라인 |
|---|--------|------|------|------|------|
| 1 | 🟡 Minor | 의도된 현행 구현(확장 부채) | `four_phase_arc_generator.py` | `NegativeExampleInjector("wuxia")` 고정 주입 | 48 |
| 2 | 🔴 Critical | 실이슈 | `stage2_orchestrator.py` | `async` 메서드 내부 `input()` 호출 | 686, 712, 766 |
| 3 | 🟠 Medium | 조건부 실이슈 | `arc_ensemble.py` | genre 폴백 `"wuxia"` 하드코딩 | 122, 127, 312 |
| 4 | 🟠 Medium | 구조 리스크 | `stage2_orchestrator.py` | 685줄 단일 메서드 (`stage_2_arcs_async_logic`) | 82-766 |
| 5 | 🟠 Medium | 실이슈 | 3개 파일 | 아이템 중복 검증 로직 3중 분산 | 아래 참조 |
| 6 | 🟠 Medium | 구조 리스크 | `continuity_arc.py` | 180줄+ 프롬프트 문자열 인라인 | 17-200, 161-200 |
| 7 | 🟡 Minor | 실이슈(경미) | `stage2_orchestrator.py` | `print()`/`logging` 혼용 | 685, 710 |
| 8 | 🟡 Minor | 실이슈(상수화 필요) | `stage2_orchestrator.py` | `ep_count` 폴백 `5` 매직넘버 | 691, 693, 698, 719, 721, 726 |

---

## 상세 분석

### 1) `NegativeExampleInjector("wuxia")` 고정 주입

- 근거: `modules/domain/agents/four_phase_arc_generator.py:48`
- 보정 포인트:
  - 고정 주입 자체는 사실.
  - 현재 구현에서 장르별 라이브러리 분기는 사실상 미구현:
    - `modules/domain/agents/negative_example_injector.py:126`
    - `modules/domain/agents/negative_example_injector.py:128`
    - `modules/domain/agents/negative_example_injector.py:131`
  - 현재는 장르가 달라도 동일 예시(`WUXIA_NEGATIVE_EXAMPLES`) 반환.
  - `self.genre`는 저장되지만, 현재 파일 수동 판독 기준으로 후속 분기에서 실사용되지 않음.
- 판정: **의도된 현행 구현(확장 부채)**  
  지금 시점에서 동적 장르 주입을 해도 동작 결과는 사실상 동일함.
- 권고:
  1. 생성자에서 장르를 context 기반으로 받되,
  2. 장르별 negative library를 실제 분리
  3. 분리 완료 시점에만 severity를 상향 재평가

---

### 2) `async` 메서드 내부 블로킹 `input()`

- 근거:
  - `modules/core/stage2_orchestrator.py:686`
  - `modules/core/stage2_orchestrator.py:712`
  - `modules/core/stage2_orchestrator.py:766`
- 문제:
  - `stage_2_arcs_async_logic`가 `async def`인데 동기 입력으로 이벤트 루프를 정지시킴.
- 판정: **실이슈(Critical)**  
  CLI 단독 실행에서는 체감이 낮아도, 병행 async 태스크/향후 UI 확장 시 즉시 병목.
- 권고:
  - `await asyncio.to_thread(input, ...)` 또는 `self.ctx.ui` 추상 입력 인터페이스 사용

---

### 3) `arc_ensemble.py` genre 폴백값 `"wuxia"` 하드코딩

- 근거:
  - `modules/domain/agents/arc_ensemble.py:122`
  - `modules/domain/agents/arc_ensemble.py:127`
  - `modules/domain/agents/arc_ensemble.py:312`
- 보정 포인트:
  - 하드코딩은 사실.
  - 실제 영향은 DB 로드 실패/컨텍스트 장르 전달 누락 시에 증폭되는 **조건부 리스크**.
- 판정: **조건부 실이슈**
- 권고:
  1. 1순위: `context.selected_genre` 또는 SSOT 장르
  2. 2순위: DB 앵커
  3. 최종 폴백만 상수화된 기본 장르

---

### 4) `stage_2_arcs_async_logic` 메서드 비대화

- 근거:
  - 시작: `modules/core/stage2_orchestrator.py:82`
  - 종료: `modules/core/stage2_orchestrator.py:766`
- 문제:
  - 생성 루프/실패 처리/사용자 개입/배치 종료/후처리가 한 메서드에 결합.
- 판정: **구조 리스크**
- 권고:
  - `_run_batch`, `_handle_failure_choice`, `_skip_arc_with_ep_count`, `_finalize_batch` 등으로 분해

---

### 5) 아이템 중복 검증 로직 3중 분산

- 근거 파일:
  - `modules/domain/agents/arc_draft_validator.py:201` (`_validate_duplicate_acquisition`)
  - `modules/domain/agents/unified_arc_validator.py:342` (`_check_duplicate_items`)
  - `modules/core/stage2_optimizer.py:200` (`_remove_duplicate_items`)
- 보정 포인트:
  - 분산/중복 구현 자체는 사실.
  - 기존 문구의 "`SequenceMatcher 0.8` 사용"은 현재 코드와 불일치.
    - 현재 `stage2_optimizer`는 포함관계+길이비율 기반:
      - `modules/core/stage2_optimizer.py:248`
      - `modules/core/stage2_optimizer.py:260`
      - `modules/core/stage2_optimizer.py:263`
- 판정: **실이슈**
- 권고:
  - 공통 비교 유틸(`normalize_item`, `is_same_item`)을 단일 모듈로 통합하고 3곳 공용화

---

### 6) `continuity_arc.py` 프롬프트 인라인 대형 상수

- 근거:
  - `modules/domain/agents/continuity_arc.py:17` (`ARC_CONTINUITY_INSPECTION_PROMPT`)
  - `modules/domain/agents/continuity_arc.py:161` (`JOINT_DOCS_EXTRACTION_PROMPT`)
  - 클래스 시작: `modules/domain/agents/continuity_arc.py:203`
- 문제:
  - 모듈 상단 대형 텍스트가 코드 변경 이력에 과도한 노이즈를 유발.
- 판정: **구조 리스크**
- 권고:
  - `prompts/` 외부 파일로 이동 + `PromptLoader`로 로드

---

### 7) `print()` 사용 (logging 불일치)

- 근거:
  - `modules/core/stage2_orchestrator.py:685`
  - `modules/core/stage2_orchestrator.py:710`
- 문제:
  - 같은 메뉴 블록 내 출력 경로 혼재.
- 판정: **경미 실이슈**
- 권고:
  - 메뉴 출력 통일(`logging.info` 또는 `self.ctx.ui.log`)

---

### 8) `ep_count` 폴백 `5` 매직넘버

- 근거:
  - `modules/core/stage2_orchestrator.py:691`
  - `modules/core/stage2_orchestrator.py:693`
  - `modules/core/stage2_orchestrator.py:698`
  - `modules/core/stage2_orchestrator.py:719`
  - `modules/core/stage2_orchestrator.py:721`
  - `modules/core/stage2_orchestrator.py:726`
- 관련 상수:
  - `modules/core/constants.py:230` (`VolumeSettings.EPISODES_PER_ARC`)
- 문제:
  - 가변 페이싱(3~7) 체계와 결합 시 폴백 `5`가 의미 왜곡을 일으킬 수 있음.
- 판정: **실이슈(상수화 필요)**
- 권고:
  - `DEFAULT_EP_COUNT = VolumeSettings.EPISODES_PER_ARC`
  - skip 로직 2개 구간 공통 함수화

---

## 우선 처리 순서 (실행 관점)

1. `#2` async 블로킹 입력 제거  
2. `#8` ep_count 폴백 상수화 + skip 공통화  
3. `#3` 장르 SSOT 경로 정리  
4. `#5` 중복 검증 공통 유틸 통합  
5. `#4 + #6 + #7` 구조/가독성 리팩토링

---

## 정확성 보정 로그

1. `#1`: 실버그 단정 해제, **의도된 현행 구현(확장 부채)** 로 재분류  
2. `#3`: 무조건 오동작 표현을 **조건부 리스크**로 보정  
3. `#5`: `SequenceMatcher 0.8` 언급 제거, 현재 코드 알고리즘으로 근거 갱신  
4. `#2`: 블로킹 `input()` 근거 라인에 `:766` 추가
