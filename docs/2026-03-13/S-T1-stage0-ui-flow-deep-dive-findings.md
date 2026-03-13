# [S-T1] Stage 0 메뉴 & UI 플로우 심층 감사 보고서

> 작성일: 2026-03-13
> 터미널: Terminal 1
> 범위: `modules/core/stage0/__init__.py`, `modules/core/stage01_helpers.py`, `modules/core/project_support.py`, 관련 Stage 0 테스트
> 방법: static / read-only / source cross-check / targeted test coverage inspection

---

## 요약

이번 심층 감사의 핵심은 1차/2차에서 파일 단위로만 훑고 지나간 Stage 0 메뉴 흐름을 실제 입력-정규화-저장 체인으로 다시 연결하는 것이었다. 결론은 다음과 같다.

- `StageZeroManager` 본체의 mojibake는 여전히 남아 있지만, 본체 쪽은 후단 정규화 덕분에 주로 표시 깨짐 수준에 머문다.
- 반면 `stage01_helpers.py` 안의 중복 주인공 설정 플로우는 깨진 한글 리터럴을 실제 정책값으로 사용한다.
- `plot_roadmap`는 여전히 생성기 레이어가 아니라 저장 직전 보정 레이어에서만 채워진다.

즉, Stage 0의 가장 큰 문제는 "문자 깨짐" 자체보다도, **중복 구현이 이미 의미적 드리프트로 번졌다는 점**이다.

---

## 확정 발견사항

### [S-T1-001] P1 | `phase_0_recovery()` 외부 시점 정책 메뉴가 사용자 선택을 기본값으로 덮어쓴다

- 파일:
  - `modules/core/stage01_helpers.py:143-157`
  - `modules/core/project_support.py:16-17`
  - `modules/core/project_support.py:34-51`
- 현상:
  - `phase_0_recovery()`는 외부 시점 삽입 정책 메뉴를 별도 구현하면서 깨진 문자열 리터럴을 `policy_types` 값으로 사용한다.
  - 이후 이 값은 `normalize_external_pov_insert_policy()`로 전달되는데, 정상 허용값은 `("금지", "제한적 허용", "적극 허용")`뿐이다.
  - 따라서 사용자가 `[1]` 또는 `[3]`을 골라도 깨진 문자열이 alias 표에 매칭되지 않아, 최종 저장값이 사용자의 선택이 아니라 POV/장르 기반 기본정책으로 되돌아간다.
- 증거:
  - `stage01_helpers.py`의 `policy_types = {"1": "湲덉?", "2": "?쒗븳???덉슜", "3": "?곴레 ?덉슜"}`
  - `project_support.py`는 위 깨진 문자열을 alias로 인정하지 않고, 미인식 입력이면 `default_external_pov_insert_policy()`로 폴백한다.
- 영향:
  - Stage 0 복구 경로에서 외부 시점 정책 선택이 **조용히 잘못 저장**된다.
  - UI 표시 오류가 아니라 설정 의미 자체가 변질되는 문제다.
- 기존 보고서와의 관계:
  - `D-T1-002`는 `stage0/__init__.py` 메뉴의 mojibake를 잡았지만, 본 건은 `stage01_helpers.py` 중복 경로에서 **실제 저장값이 오염되는 새 결함**이다.

### [S-T1-002] P2 | `plot_roadmap` 계약이 여전히 생성기 레이어 밖에서만 보정된다

- 파일:
  - `modules/core/stage0/__init__.py:369-404`
  - `modules/core/stage01_helpers.py:566-592`
  - `modules/core/stage2_orchestrator.py:156`
- 현상:
  - `StageZeroManager.generate_from_concept()`는 Bible/Treatment를 반환하지만, 반환 직전 `plot_roadmap`를 주입하지 않는다.
  - `Stage01Helpers._s0_save_results()`가 저장 직전 `_ensure_plot_roadmap()`를 호출해 누락을 보정하는 구조다.
  - 즉, Stage 2가 기대하는 핵심 handoff 필드는 생성기 산출물이 아니라 save-time patch에 의해 만들어진다.
- 증거:
  - `stage0/__init__.py`의 `generate_from_concept()`는 `self.bible = expander.generate_bible(...)` 후 바로 반환한다.
  - `stage01_helpers.py`는 `Stage01Helpers._ensure_plot_roadmap(app, bible, treatment)`를 저장 직전에 호출한다.
  - `stage2_orchestrator.py`는 Bible에서 `plot_roadmap`를 직접 읽는다.
- 영향:
  - 현재 Stage01Helpers 경유 정식 흐름에서는 문제를 완화하지만, 생성 직후 in-memory consumer나 save 이전 예외 경로는 여전히 불완전 Bible을 보게 된다.
  - 1차 `T2-001`의 루트코즈가 "완전 수정"된 것이 아니라 **외곽 보정으로 봉합된 상태**다.
- 기존 보고서와의 관계:
  - 1차/2차에서 `plot_roadmap` 누락은 이미 다뤘다. 본 건은 심층 감사에서 그 **잔존 위치가 생성기 레이어**임을 좁혀 확정한 것이다.

### [S-T1-003] P3 | 주인공 설정 플로우가 두 군데로 복제돼 이미 드리프트가 발생했다

- 파일:
  - `modules/core/stage0/__init__.py:297-329`
  - `modules/core/stage01_helpers.py:127-157`
  - `tests/test_stage0_pov.py:8-75`
  - `tests/test_stage3_orchestrator.py:745-786`
- 현상:
  - Stage 0 주인공 설정은 `StageZeroManager.show_protagonist_config_menu()`와 `Stage01Helpers.phase_0_recovery()` 양쪽에 중복 구현돼 있다.
  - 본체는 옵션 상수와 정규화를 사용하지만, helper 쪽은 별도 하드코딩 사전/로그 문자열을 가진다.
  - 테스트는 대부분 `StageZeroManager` 본체 경로와 저장 후 downstream 소비를 검증할 뿐, helper 중복 메뉴의 문자열/정규화 일치를 직접 보장하지 않는다.
- 영향:
  - 이번 `S-T1-001`처럼 한쪽만 깨져도 다른 쪽 테스트로는 잡히지 않는다.
  - Stage 0 UI 계약이 "상수 1곳"이 아니라 "중복 메뉴 2곳"에 분산돼 유지보수성이 낮다.
- 기존 보고서와의 관계:
  - 기존 T1/T2 문서에는 메뉴 중복 자체가 ledger로 올라오지 않았다. 이번 심층 감사에서 새로 구조적 원인으로 확인했다.

---

## 정상 확인 항목

- `manage_work_guard()`의 import/init/preview/delete 4개 분기는 현재 코드상 경로 검증과 안전한 fallback을 유지한다.
- `PresetRegistry` 장르 기본값은 현재 트리에서 `medical` 포함 상태로 확인됐다.
- `tests/test_stage01_helpers.py:364-397`는 save-time `plot_roadmap` 보정 자체는 이미 회귀 테스트로 고정하고 있다.

---

## 3PASS 감리 로그

### PASS 1 — 후보 6건

- Stage 0 mojibake 잔존
- helper 경로 정책값 오염
- `plot_roadmap` 생성기 레이어 누락
- Work Guard 경로 안전성
- PresetRegistry 장르 누락 여부
- 주인공 설정 플로우 중복

### PASS 2 — 제거 3건

- Work Guard 경로 안전성: 현행 코드에서 경로 검증 정상
- PresetRegistry 장르 누락: 현행 코드에서 재현 안 됨
- `stage0/__init__.py` mojibake 단독 건: 기존 `D-T1-002`와 중복

### PASS 3 — 최종 3건 확정

- `PASS1 6건 → PASS2 3건 제거 → 최종 3건 확정`

---

## 결론

Stage 0 심층 감사의 결론은 "메뉴 UI가 조금 지저분하다" 수준이 아니다. 핵심 문제는 **중복된 Stage 0 설정 플로우가 이미 실제 저장값 오염을 만들고 있고**, `plot_roadmap` 계약도 여전히 생성기 바깥의 저장 패치에 기대고 있다는 점이다.

따라서 후속 조치 우선순위는 아래와 같다.

1. `phase_0_recovery()`의 외부 시점 정책 메뉴를 본체 상수/정규화 경로와 단일화
2. `plot_roadmap`를 `generate_from_concept()` 산출물 자체에서 보장
3. Stage 0 주인공 설정 메뉴를 1개 구현으로 축소하고 helper 경로 테스트 추가
