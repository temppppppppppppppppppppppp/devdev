# SZ0-T5 Integration Wiring & Regression Findings

> 작성일: 2026-03-13
> 상태: 3pass complete
> 범위: `modules/core/stage01_helpers.py`, `modules/core/stage0/__init__.py`, `main_a.py` (Stage 0 관련), 테스트 파일 5개

---

## Executive Summary

Stage 0 통합 배선은 전반적으로 견고하다. lazy loading, handler dispatch, 결과 저장, 프리셋 복원 경로 모두 정상 동작하며 테스트 커버리지도 핵심 경로를 잘 포괄한다. 최종 확정 finding은 3건이며, 사전 배정된 P3-9(인코딩 깨짐)은 확인 완료, P3-11(프리셋 하드코딩)은 의도된 설계로 오탐 처리했다.

- 확정 결함: 3건 (P3 x 2, P2 x 1)
- 오탐 제거: 3건
- Coverage Gap: 3건 식별

---

## PASS 1 - 후보 수집

### 후보 A — `__init__.py` L317 인코딩 깨짐 (사전 배정 P3-9)

- **위치**: `modules/core/stage0/__init__.py` L317
- **현상**: `print("\n  [????쒖젏 ?쎌엯 ?뺤콉]")` — 한글 "외부시점 삽입 정책"이 EUC-KR/CP949 바이트가 UTF-8로 잘못 저장되어 깨진 문자열
- **영향**: `show_protagonist_config_menu()` 호출 시 사용자에게 깨진 한글이 출력됨
- **확신도**: HIGH — 직접 확인 가능

### 후보 B — `__init__.py` L325 인코딩 깨짐 (후보 A 연장)

- **위치**: `modules/core/stage0/__init__.py` L325
- **현상**: `raw_choice = input(f"    ?좏깮 (湲곕낯: {default_index}): ").strip()` — "선택 (기본:" 역시 깨진 상태
- **영향**: 후보 A와 동일한 메서드, 동일 원인
- **확신도**: HIGH

### 후보 C — `GENRE_PRESETS` Python dict 하드코딩 (사전 배정 P3-11)

- **위치**: `modules/core/stage0/preset_registry.py` L44+ `GENRE_PRESETS` 클래스 변수
- **현상**: 10개 장르 프리셋(investment, wuxia, hunter 등)이 외부 설정 파일이 아닌 Python dict로 하드코딩
- **확신도**: HIGH — 소스 직접 확인

### 후보 D — `_s0_save_results()` 실패 시 treatment만 저장되고 bible 저장 안 되는 비대칭

- **위치**: `stage01_helpers.py` L654-699
- **현상**: `_s0_save_results()`에서 bible 저장이 예외 발생으로 실패해도 treatment 저장은 독립 블록이라 진행됨. bible 없이 treatment만 존재하면 Stage 2 진입 시 plot_roadmap 누락 가능
- **확신도**: MEDIUM

### 후보 E — mode=0 메뉴 리매핑에서 block_extension 접근 불가

- **위치**: `stage01_helpers.py` L403-410
- **현상**: `show_menu(is_new_project=True)`의 메뉴에는 block extension이 없고 4→5, 5→6으로 리매핑. 신규 프로젝트에서는 block extension에 접근 불가
- **확신도**: HIGH — 코드 직접 확인

### 후보 F — `_restore_preset_registry()`가 `_preset_state_raw=None`일 때 기존 preset_registry를 `None`으로 덮어씀

- **위치**: `main_a.py` L391-402
- **현상**: `self.preset_registry = None`을 먼저 수행 후 `_ps_raw`가 None이면 early return. 프로젝트 전환 시 이전 프로젝트의 preset이 남는 것은 방지하지만, DB에 preset_state가 없는 프로젝트로 전환하면 preset이 초기화됨
- **확신도**: MEDIUM

---

## PASS 2 - 교차 검증

### 후보 A, B — 인코딩 깨짐 → 확정

- `stage01_helpers.py`의 동일 메서드(`phase_0_recovery` L162-224)에서는 정상 한글로 동일 UI를 구현하고 있어, `__init__.py`의 `show_protagonist_config_menu()`만 깨진 것이 확인됨
- `test_stage0_pov.py`에서 이 메서드를 테스트하지만, 출력 문자열 내용은 검증하지 않아 테스트에서 발견되지 않음
- **판정**: 확정 (P3-9와 통합, 2곳을 1건으로 관리)

### 후보 C — 프리셋 하드코딩 → 오탐 제거

- `GENRE_PRESETS`는 장르별 HUD 필드 스키마를 정의하는 것으로, 런타임에 변경될 필요가 없는 구조적 정의다
- `CLAUDE.md`에 "~~동적 장르 확장~~ → 폐기 (템플릿 복제 방식 10개 장르 검증 완료)"로 명시적 NO-GO 결정
- 10개 장르가 `GenreTypes.all()`과 동기화되어 있고 테스트(`test_stage0_fixes.py::TestPhaseA::test_supported_genres_matches_genre_types`)가 이를 검증
- **판정**: 오탐 — 의도된 설계, 외부화 ROI 낮음

### 후보 D — bible/treatment 비대칭 저장 → 확정 (P3)

- `_s0_save_results()` L656-698 코드 분석:
  1. bible 저장 시도 (L656-681): 예외 → warning 로그만
  2. treatment 저장 시도 (L683-690): bible과 독립적으로 진행
  3. bible 재로드 (L692-694): bible 변수가 truthy이면 실행
- bible 저장이 `save_v20_anchor()` 예외로 실패해도 `bible` dict 자체는 truthy이므로 `_load_from_db()` 호출됨. 이 경우 DB에는 이전 bible이 남아 있어 불일치 발생
- 단, `generate_from_concept()` 내부에서 `_ensure_plot_roadmap()`이 bible dict를 직접 변경하므로, save 실패 시에도 메모리 상태는 일시적으로 정합됨. 디스크 영속성만 깨짐
- **판정**: 확정 P3 — 실제 발생 빈도 낮음 (DB 저장 실패는 드문 상황), 재시작 시 이전 상태로 롤백되어 데이터 손실은 없음

### 후보 E — mode=0에서 block_extension 접근 불가 → 오탐 제거

- `phase_0_recovery()` L134에서 `choice=5`일 때 `self.stage_0_extended(mode=4)`를 호출하여 block extension에 접근 가능
- `show_menu(is_new_project=True)`는 신규 프로젝트 전용이며, block extension은 기존 treatment가 필요하므로 신규 프로젝트 메뉴에 없는 것이 의도된 동작
- **판정**: 오탐 — 의도된 UX 설계

### 후보 F — preset_registry None 초기화 → MRL-T3-001과 교차 검증

- `MRL-T3-project-switch-preset-registry-findings.md`에서 이미 "장르 불일치 continue 경로가 selected_genre와 preset_registry.base_genre를 다른 truth source로 남긴다"를 MRL-T3-001(P1)로 확정
- 본 후보는 MRL-T3-001의 하위 증상에 해당하며, `_restore_preset_registry()`가 None으로 초기화하는 것 자체는 올바른 동작 (이전 프로젝트 preset 잔류 방지)
- DB에 preset_state가 없는 프로젝트의 경우, `_select_genre()`에서 `PresetRegistry(base_genre=...)` 신규 생성하므로 실사용 경로에서는 문제 없음
- **판정**: 오탐 — MRL-T3-001로 이미 커버됨

---

## PASS 3 - 최종 확정 Findings

| ID | Sev | 상태 | 파일 | 요약 |
|----|-----|------|------|------|
| SZ0-T5-001 | P3 | retained | `modules/core/stage0/__init__.py` L317, L325 | `show_protagonist_config_menu()` 내 한글 인코딩 깨짐 — "외부시점 삽입 정책", "선택 (기본:" 등이 EUC-KR 바이트로 손상 |
| SZ0-T5-002 | P3 | retained | `modules/core/stage01_helpers.py` L654-699 | `_s0_save_results()`에서 bible 저장 실패 시 treatment가 독립 저장되어 bible/treatment 불일치 가능 |
| SZ0-T5-003 | P2 | retained (cross-ref) | `modules/core/stage0/__init__.py`, `main_a.py` | `StageZeroManager.show_protagonist_config_menu()`와 `Stage01Helpers.phase_0_recovery()`가 동일 POV 설정 UI를 중복 구현 — `__init__.py` 쪽만 인코딩 깨짐이 있어 두 경로의 drift 위험 |

### SZ0-T5-001 상세

- **사전 배정**: P3-9
- **위치**: `modules/core/stage0/__init__.py` L317 `print("\n  [????쒖젏 ?쎌엯 ?뺤콉]")`, L325 `input(f"    ?좏깮 (湲곕낯: {default_index}): ")`
- **원인**: 파일이 EUC-KR로 작성된 후 UTF-8로 변환 시 일부 문자열이 누락됨
- **영향 범위**: `StageZeroManager.show_protagonist_config_menu()` — 신규 프로젝트 flow (`run_new_project_flow()`) 및 `show_menu(is_new_project=False)` → preset 관리 경로에서 호출
- **회피**: `phase_0_recovery()` 경로를 사용하면 동일 기능이 정상 한글로 제공됨
- **수정 방향**: L317을 `print("\n  [외부시점 삽입 정책]")`으로, L325를 `input(f"    선택 (기본: {default_index}): ")`으로 교체

### SZ0-T5-002 상세

- **위치**: `modules/core/stage01_helpers.py` `_s0_save_results()` L654-699
- **현상**: bible 저장 블록(L656-681)과 treatment 저장 블록(L683-690)이 독립 try/except로 구성되어, bible 저장 예외 시에도 treatment가 디스크에 쓰여짐. 이후 bible 변수가 truthy이므로 `_load_from_db()` 호출 → DB의 이전 bible과 신규 treatment가 혼재
- **발생 확률**: 낮음 (DB 쓰기 오류 조건 필요)
- **수정 방향**: bible 저장 성공 여부를 플래그로 관리하고, 실패 시 treatment 저장 및 reload를 억제하거나 사용자에게 명시적 경고

### SZ0-T5-003 상세

- **위치**: `modules/core/stage0/__init__.py` L267-334 `show_protagonist_config_menu()` vs `modules/core/stage01_helpers.py` L162-231 `phase_0_recovery()` 내부 POV 설정
- **현상**: 동일한 세계관 출신 / 캐릭터 타입 / POV / 외부시점 삽입 정책 설정 UI가 두 곳에 중복 구현됨. `__init__.py` 쪽은 인코딩 깨짐(SZ0-T5-001)이 있고, `stage01_helpers.py` 쪽은 정상. 향후 옵션 추가/변경 시 한쪽만 수정하면 drift 발생
- **교차 참조**: ROP-T4에서 "operator-facing support surface의 POV 노출 불일치"를 이미 지적한 바 있음
- **수정 방향**: `show_protagonist_config_menu()`를 단일 진실 원천(SSOT)으로 통합하고, `phase_0_recovery()`는 이를 호출하는 방식으로 리팩토링

---

## 오탐 제거 요약

| 후보 | 판정 | 사유 |
|------|------|------|
| 후보 C (P3-11 GENRE_PRESETS 하드코딩) | 오탐 | CLAUDE.md에 "동적 장르 확장 폐기" NO-GO 확정. 10개 장르 고정 운영이 의도된 설계. GenreTypes.all() 동기화 테스트 존재 |
| 후보 E (mode=0 block_extension 접근 불가) | 오탐 | 신규 프로젝트 메뉴에서 block extension 미노출은 의도된 UX. `phase_0_recovery()` 경로에서는 접근 가능 |
| 후보 F (preset_registry None 초기화) | 오탐/중복 | MRL-T3-001(P1)로 이미 커버. None 초기화 자체는 이전 프로젝트 잔류 방지로 올바른 동작 |

---

## Coverage Gap Log

### Gap 1 — `StageZeroManager.show_protagonist_config_menu()` 출력 내용 미검증

- **현황**: `test_stage0_pov.py`에서 반환값(config dict)만 검증. 실제 print 출력 문자열은 검증하지 않음
- **영향**: SZ0-T5-001(인코딩 깨짐)이 테스트에서 잡히지 않은 원인
- **제안**: capsys/capfd를 활용하여 출력 문자열에 한글이 포함되는지 검증하는 테스트 추가

### Gap 2 — `_s0_save_results()` 부분 실패 시나리오 미테스트

- **현황**: `test_stage01_helpers.py::TestStage0RoadmapInjection`에서 정상 경로만 테스트. `save_v20_anchor()` 예외 시 동작 미검증
- **영향**: SZ0-T5-002(bible/treatment 비대칭 저장) 미탐지
- **제안**: `save_v20_anchor`에 side_effect=Exception을 주입하여 treatment 저장 및 reload 동작 검증

### Gap 3 — `StageZeroManager.load_state()` / `save_state()` 통합 테스트 미존재

- **현황**: `__init__.py` L687-788의 `save_state()`/`load_state()` 메서드에 대한 직접 테스트 없음
- **영향**: 파일 I/O 기반 상태 직렬화/역직렬화 경로가 검증되지 않음. 다만 이 경로는 Stage 0 독립 실행 시에만 사용되며, 일반 파이프라인에서는 DB anchor(`save_v20_anchor`)를 사용
- **제안**: 별도 테스트 파일에서 `save_state()` → `load_state()` 라운드트립 검증 추가
