# Stage 0 전수 감사 리포트 (2026-02-22)

> 감사 대상: Stage 0 (초기 설정 -- 세계관 바이블 추출, NPC 등록, 문체 분석)
> 감사 범위: `modules/core/stage0/` 전체, `main_a.py` Stage 0 관련, `stage01_helpers.py`, `project_manager.py`, `genre_guards/__init__.py`, `genre_hud_manager.py`
> 감사자: Claude Opus 4.6

---

## 요약

- **P0 (차단급 버그)**: 2건
- **P1 (품질 이슈)**: 7건
- **P2 (스타일/경미)**: 5건
- **개선 아이디어**: 6건

---

## P0 -- 차단급 버그

### P0-1: StageZeroManager에 LLM 클라이언트가 전달되지 않음

- **파일**: `modules/core/stage01_helpers.py:291`
- **증상**: Stage 0 확장 기능 (컨셉 생성, 역설계, 스타일 분석)에서 LLM 호출이 모두 실패하여 빈 결과만 반환됨
- **원인**: `stage_0_extended()` 메서드에서 `StageZeroManager`를 생성할 때 `llm_client`를 전달하지 않음:
  ```python
  stage0_manager = StageZeroManager(project_path=project_path)
  # llm_client=??? 누락
  ```
  `StageZeroManager.__init__`에서 `self.client = llm_client`로 저장되므로 `self.client = None`이 됨.
  이후 `run_new_project_flow()` -> `generate_from_concept()` -> `StoryExpander(llm_client=self.client)` 체인에서 `llm_client=None`이 전파됨.
  `StoryExpander._call_llm()`은 `self._init_llm()`을 호출하여 환경변수에서 API 키를 찾아 자체적으로 클라이언트를 생성하므로 **환경변수가 설정되어 있으면 동작하지만**, `main_a.py`의 `SovereignApp`에는 이미 초기화된 `self.sys.api_client`가 있으므로 재사용하는 것이 정석임.
- **영향**: 환경변수 `GOOGLE_API_KEY`가 설정되어 있으면 실질적으로 문제 없지만, API 키 로테이션이나 커스텀 클라이언트 설정이 무시됨. 환경변수 미설정 환경에서는 Stage 0 전체가 무음 실패.
- **수정안**:
  ```python
  # stage01_helpers.py:291
  stage0_manager = StageZeroManager(
      project_path=project_path,
      llm_client=app.sys.api_client,  # SovereignApp의 클라이언트 재사용
  )
  ```

### P0-2: StoryExpander.run()에서 generate_bible() None 반환 시 후속 크래시

- **파일**: `modules/core/stage0/story_expander.py:493, 519`
- **증상**: LLM이 주인공 생성에 실패하면 `generate_bible()`이 `None`을 반환하는데, `run()` 메서드가 이를 검사하지 않고 `generate_treatment()`과 `save_all()`을 계속 실행하여 `json.dump(self.bible, ...)` 시 `TypeError: Object of type NoneType is not JSON serializable` 발생
- **원인**: `generate_bible()` L152에서 `return None` 경로가 존재하지만, `run()` L492-493, L518-519에서 반환값을 확인하지 않고 `self.bible`이 None인 채 진행
- **영향**: `run()` 호출 시 LLM 실패하면 크래시. `generate_from_concept()` (L234-239)에서는 올바르게 검사하므로 `StageZeroManager` 경유 시에는 안전하지만, `StoryExpander.run()`을 직접 호출하면 크래시
- **수정안**:
  ```python
  # story_expander.py run() 내부, generate_bible 호출 후
  result = self.generate_bible(protagonist_config)
  if result is None:
      logging.error("[StoryExpander] Bible 생성 실패 - 파이프라인 중단")
      return {}, []
  ```

---

## P1 -- 품질 이슈

### P1-1: ReverseExpander.run() 반환 타입 불일치 -- style_guide가 None일 수 있음

- **파일**: `modules/core/stage0/reverse_expander.py:506`
- **증상**: `run()` 메서드 시그니처가 `-> tuple[dict, list, StyleGuide]`를 명시하지만, `extract_style_guide()`가 실패하면 `self.style_guide = None` 상태에서 반환됨. 호출부에서 `.tone`, `.pov` 등에 접근 시 `AttributeError` 발생 가능
- **원인**: `extract_style_guide()` 내부에서 `StyleExtractor.extract_from_drafts()`가 빈 drafts를 받으면 기본 StyleGuide를 반환하므로 실제로는 드문 상황이지만, LLM 호출 전체 실패 시에는 불완전한 StyleGuide가 반환될 수 있음
- **수정안**: 반환 타입을 `tuple[dict, list, StyleGuide | None]`으로 명시하거나, None 방어 코드 추가

### P1-2: PresetRegistry GENRE_PRESETS에 "fantasy"가 있지만 StageZeroManager.SUPPORTED_GENRES에 없음 (동기화 불일치)

- **파일**: `modules/core/stage0/__init__.py:48-59` vs `modules/core/stage0/preset_registry.py:100-108`
- **증상**: `StageZeroManager.SUPPORTED_GENRES`에 `"fantasy": "판타지"`가 포함되어 있고, `PresetRegistry.GENRE_PRESETS`에도 `"fantasy"` 키가 존재하므로 **현재는 동기화 정상**
- **그러나**: `SUPPORTED_GENRES`의 순서가 `GenreTypes.all()`의 순서와 다름 (fantasy가 4번째 위치). `show_genre_menu()`에서 번호 매핑이 SUPPORTED_GENRES dict 순서에 의존하므로, 사용자가 `_select_genre()`에서 선택한 번호와 `show_genre_menu()`에서 선택한 번호가 다른 장르를 가리킬 수 있음
- **원인**: `main_a.py`의 `_select_genre()`는 하드코딩된 1-10 매핑, `StageZeroManager.show_genre_menu()`는 dict 순서 기반 동적 매핑
- **수정안**: `SUPPORTED_GENRES`를 `OrderedDict`로 명시하거나, `GenreTypes.all()` + `GenreTypes.get_name()`을 활용하여 SSOT 유지

### P1-3: cp949 폴백 실패 시 2차 UnicodeDecodeError가 미처리

- **파일**: `modules/core/stage0/reverse_expander.py:113-115, 170-172`
- **증상**: UTF-8 실패 시 cp949로 재시도하지만, 파일이 EUC-KR도 아닌 인코딩(예: UTF-16, Shift_JIS)이면 cp949 읽기도 실패하여 미처리 예외 발생
- **원인**: cp949 폴백에 `try-except` 래핑이 없음
- **수정안**: cp949 읽기도 `try-except`로 감싸고 `chardet`이나 `errors='replace'` 폴백 추가

### P1-4: StoryExpander._generate_skeleton()에서 LLM 실패 시 빈 블록이 생성됨

- **파일**: `modules/core/stage0/story_expander.py:379-413`
- **증상**: `_generate_skeleton()`의 `_parse_json(self._call_llm(prompt))` 결과가 None이면 빈 리스트가 반환되지만, `all_blocks`에 빈 결과가 누적되면서 Treatment의 총 블록 수가 기대보다 적어짐. 에러 로그 없이 조용히 진행됨
- **원인**: LLM 호출 실패 시 `or []` 폴백은 있지만, 실패 로깅과 재시도가 없음
- **수정안**: 배치별 실패 시 경고 로그 추가, 최소 1회 재시도

### P1-5: PresetRegistry.detect_new_genre()의 키워드 세트가 불완전

- **파일**: `modules/core/stage0/preset_registry.py:552-567`
- **증상**: `detect_new_genre()`가 `fantasy`, `romance`, `politics`, `military`만 감지하고, 실제 프로덕션에서 사용하는 `wuxia`, `hunter`, `investment`, `composer`, `cooking`, `alt_history`, `actor`, `sports`, `medical` 장르의 키워드를 포함하지 않음
- **원인**: 초기 구현에서 보조 장르만 감지하도록 설계된 듯하나, 현재 10개 장르 체제에서는 모든 장르를 커버해야 함
- **영향**: 런타임 장르 감지가 주요 장르를 놓침 (다만 이 함수가 실제로 호출되는 곳이 없어 실질적 영향은 낮음)
- **수정안**: 10개 장르 전체의 키워드를 추가하거나, 미사용 함수임을 명시적으로 표시

### P1-6: StageZeroManager.show_menu()에서 logging.info를 UI 출력에 사용

- **파일**: `modules/core/stage0/__init__.py:85-101`
- **증상**: `logging.info()`는 기본적으로 콘솔에 출력되지 않음 (logging 레벨이 WARNING 이상인 경우). Stage 0 메뉴가 사용자에게 보이지 않을 수 있음
- **원인**: `StageZeroManager`가 독립 모듈로 설계되어 `SovereignApp.ui.log()` 대신 `logging.info()`를 사용
- **영향**: 프로덕션에서 logging 레벨 설정에 따라 메뉴가 안 보일 수 있음. `show_genre_menu()`, `show_protagonist_config_menu()`, `manage_presets()` 등 모든 메뉴 함수에 동일 문제
- **수정안**: `print()` 또는 콜백 패턴으로 변경하거나, 최소한 `logging.warning()`으로 상향

### P1-7: StyleExtractor._llm_call()에서 last_err가 None일 때 RuntimeError 발생

- **파일**: `modules/core/stage0/style_extractor.py:683`
- **증상**: 모든 모델이 실패하면 `raise last_err if last_err else RuntimeError("All models failed")`인데, `last_err`는 항상 Exception이므로 이론적으로 RuntimeError 경로는 도달 불가. 하지만 `models` 리스트가 빈 경우(상수 변경 시) `last_err = None`이 되어 불친절한 에러 메시지 발생
- **원인**: 방어 코드이지만 `models` 리스트 길이 0 체크가 없음
- **수정안**: `if not models: return {}` 조기 반환 추가

---

## P2 -- 스타일/경미

### P2-1: PresetRegistry.FIELD_ALIASES가 일부 장르 필드를 커버하지 못함

- **파일**: `modules/core/stage0/preset_registry.py:412-420`
- **증상**: `FIELD_ALIASES`에 `chef_rank`, `doctor_rank`, `athlete_tier`, `fame` 등 신규 장르 필드의 별칭이 없음
- **영향**: LLM이 한글 필드명(예: "셰프등급")으로 HUD를 반환하면 `normalize_field_name()`이 정규화하지 못하고 원본 그대로 저장됨
- **수정안**: 각 장르 프리셋의 주요 필드에 대해 한글 별칭 추가

### P2-2: StageZeroManager.save_state()에서 preset_registry 직렬화 오류 가능

- **파일**: `modules/core/stage0/__init__.py:481-483`
- **증상**: `preset_registry.to_json()`은 `discovered_fields`를 직렬화하지 않음 (`base_genre`와 `active_presets`만 저장). 런타임 중 발견된 필드가 유실됨
- **영향**: 프로젝트 재로드 시 동적 발견 필드가 사라짐
- **수정안**: `to_json()`에 `discovered_fields` 포함하거나, 필드를 별도 파일로 저장

### P2-3: Spinner 스레드가 데몬 스레드지만 join(timeout=0.5)로 제한

- **파일**: `modules/core/stage0/spinner.py:250-257`
- **증상**: `stop()` 호출 시 `thread.join(timeout=0.5)`로 0.5초만 대기. `_animate_rich()`의 `Live` 컨텍스트가 아직 활성 상태일 때 main 스레드가 먼저 진행하면 출력 충돌 가능
- **영향**: 간헐적으로 Rich Live 출력이 깨질 수 있음 (콘솔 깜빡임)
- **수정안**: `self.running = False` 후 충분한 대기 시간 확보, 또는 `Live` 인스턴스를 명시적으로 종료

### P2-4: import re가 _parse_korean_number 내부에서 반복 수행

- **파일**: `modules/core/stage0/preset_registry.py:516`
- **증상**: `_parse_korean_number()` 함수 내부에서 `import re`가 호출됨. 매 호출마다 모듈 룩업 비용 발생
- **영향**: 성능상 무시할 수 있는 수준이지만 코드 스타일 비정상
- **수정안**: 파일 상단에서 `import re`

### P2-5: story_expander.py에서 Spinner 컨텍스트 매니저의 `as sp` 변수 미사용

- **파일**: `modules/core/stage0/story_expander.py:485, 492, 499, 506`
- **증상**: `with Spinner(...) as sp:` 에서 `sp` 변수가 사용되지 않음 (Ruff F841 경고 후보)
- **영향**: 기능 이상 없음, 코드 청결도 이슈
- **수정안**: `as sp` 제거하거나 `as _` 변경

---

## 개선 아이디어

### IDEA-1: StageZeroManager에 DI 패턴 적용

- **현황**: `StageZeroManager`는 `__init__`에서 `llm_client`를 직접 받지만, 하위 모듈(`StoryExpander`, `StyleExtractor`)이 각각 독립적으로 LLM 클라이언트를 초기화함
- **제안**: `SovereignApp`처럼 DI 컨텍스트를 정의하여 LLM 클라이언트, 프로젝트 경로, 장르 설정 등을 통합 주입. 이렇게 하면 P0-1 같은 누락 문제를 구조적으로 방지

### IDEA-2: 역설계 원고 로딩 시 자동 인코딩 감지

- **현황**: UTF-8 -> cp949 2단계 폴백만 존재
- **제안**: `chardet` 또는 `charset-normalizer` 라이브러리를 사용하여 자동 인코딩 감지. Windows 환경에서 다양한 인코딩의 원고를 처리해야 하는 상황에 유용

### IDEA-3: StoryExpander의 LLM 호출에 재시도 로직 추가

- **현황**: `_call_llm()`에 2-모델 폴백은 있지만, 같은 모델에 대한 재시도(backoff)가 없음. Rate limit, 일시적 네트워크 오류 시 즉시 실패
- **제안**: `adaptive_retry` 모듈의 `retry_with_feedback` 래퍼를 적용하여 지수 백오프 + 재시도 구현

### IDEA-4: 역설계 회차별 상태 추출의 병렬화

- **현황**: `extract_episode_bibles()`가 모든 에피소드를 순차적으로 LLM에 호출. 100화 원고 역설계 시 100회 순차 LLM 호출로 매우 느림
- **제안**: `concurrent.futures.ThreadPoolExecutor`로 3-5개 동시 처리 (단, 이전 상태가 필요한 연쇄 구조이므로, 5화 단위 배치 병렬화 + 배치 간 순차 실행)

### IDEA-5: 문체 DNA 캐싱 강화

- **현황**: `StyleExtractor.extract_from_references()`가 호출될 때마다 전체 레퍼런스를 다시 분석 (LLM 3-4회 호출)
- **제안**: 분석 결과를 `style_guide.json`으로 저장 후, 레퍼런스 파일의 mtime 체크를 통해 변경이 없으면 캐시 사용. 불필요한 LLM 비용 절감

### IDEA-6: Stage 0 메뉴 시스템의 UI 계층 통일

- **현황**: `StageZeroManager`의 메뉴는 `logging.info()` + `input()` 직접 호출, `main_a.py`의 메뉴는 `SovereignApp.ui.log()` + `_get_int_input()` 사용. 두 시스템의 UI 인터페이스가 분리됨
- **제안**: `StageZeroManager`에 UI 콜백(logger, input_handler)을 주입하여 `SovereignApp`의 UI 시스템과 통합. 또는 `StageZeroManager`를 순수 로직 클래스로 만들고 UI는 `stage01_helpers.py`에서 전담

---

## 검증 완료 항목 (문제 없음)

1. **장르-Guard-HUD 3자 동기화**: `GenreTypes.all()` 10종, `create_genre_guard()` 10종 + 폴백, `create_hud_manager()` 10종 + 폴백 -- 전부 일치
2. **PresetRegistry 장르 프리셋**: `GENRE_PRESETS` 13종 (10 프로덕션 + 3 보조), `NPC_GENRE_PRESETS` 13종 -- 동기화 정상
3. **import 순환 참조**: `stage0/` 패키지 내부에서 외부 모듈(`constants.py`) import는 정방향만 존재, 순환 없음
4. **ProjectContext.force_sync_v25_dna()**: Bible/Treatment JSON 로드 + 검증 + DB 저장 체인이 안전하게 동작
5. **StageZeroManager.load_state()**: JSON 파일 로드 실패 시 모든 경로에 try-except + 폴백 처리 완료
6. **StyleGuide.from_dict()**: 불필요한 키를 필터링하여 TypeError 방지 완료
7. **ReverseExpander.persist_to_db()**: 5개 하위 저장 메서드 모두 개별 try-except + commit 패턴 적용
8. **preset_registry.py 깊은 복사**: `build_initial_hud()`, `build_npc_template()` 모두 `copy.deepcopy(field_def.default)` 사용하여 뮤터블 기본값 공유 오염 방지됨

---

## 파일별 감사 결과 요약

| 파일 | 줄 수 | 발견 | 상태 |
|------|-------|------|------|
| `modules/core/stage0/__init__.py` | 580 | P0-1, P1-6, P2-2 | 수정 필요 |
| `modules/core/stage0/story_expander.py` | 530 | P0-2, P1-4, P2-5 | 수정 필요 |
| `modules/core/stage0/reverse_expander.py` | 1062 | P1-1, P1-3 | 수정 권장 |
| `modules/core/stage0/style_extractor.py` | 726 | P1-7 | 경미 |
| `modules/core/stage0/preset_registry.py` | 672 | P1-2, P1-5, P2-1, P2-4 | 수정 권장 |
| `modules/core/stage0/spinner.py` | 665 | P2-3 | 경미 |
| `modules/core/stage01_helpers.py` | 691 | P0-1 (근본 원인) | 수정 필요 |
| `modules/core/project_manager.py` | 941 | 이상 없음 | 양호 |
| `modules/core/genre_guards/__init__.py` | 74 | 이상 없음 | 양호 |
| `modules/core/genre_hud_manager.py` | 752 | 이상 없음 | 양호 |
| `main_a.py` (Stage 0 부분) | ~200 | 이상 없음 | 양호 |
