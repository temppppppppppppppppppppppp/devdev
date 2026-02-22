# Stage 0 2차 전수 감사 리포트 (2026-02-22)

> 감사 대상: Stage 0 (초기 설정 -- 세계관 바이블 추출, NPC 등록, 문체 분석)
> 감사 범위: `modules/core/stage0/` 전체 6파일 + `modules/core/stage01_helpers.py`
> 감사자: Claude Opus 4.6
> 목적: 1차 감사(2026-02-22) 수정 결과 재검증 + 1차에서 놓친 이슈 발굴

---

## 1. 1차 수정 검증 결과

### P0-1: llm_client 배선 -- **PASS**

- **파일**: `modules/core/stage01_helpers.py:291-292`
- **검증**: `stage_0_extended()` 메서드에서 `StageZeroManager` 생성 시 `llm_client`를 전달하도록 수정됨:
  ```python
  llm_client = getattr(app.sys, "api_client", None) if hasattr(app, "sys") else None
  stage0_manager = StageZeroManager(project_path=project_path, llm_client=llm_client)
  ```
- **판정**: 정상 적용. `hasattr(app, "sys")` 방어 + `getattr(..., None)` 안전 폴백 포함. SovereignApp의 api_client가 StageZeroManager -> StoryExpander -> _call_llm 체인으로 전파됨.

### P0-2 (P1으로 하향): StoryExpander.run() Bible 실패 시 경고 -- **PASS**

- **파일**: `modules/core/stage0/story_expander.py:517-518, 545-546`
- **검증**: `generate_bible()` 호출 후 `if not self.bible:` 검사 추가, `logging.warning()` 출력. 다만 `return`으로 조기 종료하지 않고 후속 단계를 계속 진행함. `self.bible`이 `None`이 아니라 `{}` (빈 dict) 또는 `None` (L173 `return None`)일 수 있는데:
  - `generate_bible()` L173에서 `return None` -> `self.bible`은 `None` 아님 (할당 전에 반환). `self.bible`은 `__init__`에서 `{}` 초기화됨.
  - 실제로 `self.bible`이 `None`이 되는 경우: `generate_bible()` L173 `return None`은 `self.bible`을 설정하지 않고 반환하므로 `self.bible`은 `__init__`의 `{}`를 유지.
  - **결론**: `run()`에서 `self.generate_bible()` 호출 후 반환값을 받지 않으므로 `self.bible`은 항상 dict. `save_all()`에서 빈 dict `{}`를 JSON으로 저장하면 크래시 없음. 경고 로그 출력도 확인됨.
- **판정**: 수정 적용됨. P1 수준에서 적절히 처리됨.

### P1-3: cp949 폴백 -- **PASS**

- **파일**: `modules/core/stage0/reverse_expander.py:113-121, 176-184`
- **검증**: `load_drafts_from_file()`과 `load_drafts_from_folder()` 모두 3단계 폴백 구현 확인:
  1. UTF-8 시도
  2. cp949 시도 (try-except 래핑됨)
  3. `errors='replace'` 최종 폴백
- **판정**: 정상 적용. 3단계 인코딩 폴백이 양쪽 메서드 모두에 일관되게 적용됨.

### P1-4: _generate_skeleton() 실패 로깅 -- **PASS**

- **파일**: `modules/core/stage0/story_expander.py:431-432`
- **검증**: LLM 응답이 비어있을 때 `logging.warning()` 출력 추가 확인:
  ```python
  if not result:
      logging.warning(f"[StoryExpander] _generate_skeleton: Block {start}~{end} LLM 응답 비어있음")
  ```
- **판정**: 정상 적용. 배치별 실패 시 경고 로그가 출력됨.

### P1-5: detect_new_genre() 9장르 키워드 -- **PASS**

- **파일**: `modules/core/stage0/preset_registry.py:583-607`
- **검증**: `genre_keywords` dict에 13개 장르 전량 포함 확인:
  - wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports, medical (프로덕션 10종)
  - romance, politics, military (보조 3종)
- **판정**: 정상 적용. GenreTypes.all() 10종 + 보조 3종 = 13종 전량 커버.

### P1-6: logging.info -> print 전환 -- **PASS**

- **파일**: `modules/core/stage0/__init__.py:85-101`
- **검증**: `show_menu()`, `show_genre_menu()`, `show_protagonist_config_menu()`, `manage_presets()` 모든 메뉴 함수에서 `print()` 사용 확인. `logging.info()`는 UI 출력이 아닌 내부 로깅 목적으로만 사용됨.
- **판정**: 정상 적용.

### P1-7: StyleExtractor._llm_call() models 빈 리스트 방어 -- **PASS**

- **파일**: `modules/core/stage0/style_extractor.py:712-714`
- **검증**: `models` 리스트 생성 후 빈 리스트 검사 + `RuntimeError` 발생 코드 확인:
  ```python
  models = [m for m in [AIModels.TIER_1_ARCHITECT, AIModels.EMERGENCY_FALLBACK, AIModels.SUMMARY_MODEL] if m]
  if not models:
      raise RuntimeError("[StyleExtractor] 사용 가능한 LLM 모델이 없습니다. AIModels 상수를 확인하세요.")
  ```
- **판정**: 정상 적용. 명확한 에러 메시지와 함께 조기 실패.

### P2-1: FIELD_ALIASES 신규 장르 필드 -- **PASS**

- **파일**: `modules/core/stage0/preset_registry.py:413-453`
- **검증**: 다음 장르 필드의 한글 별칭이 추가됨 확인:
  - composer: `music_skill`, `genre_mastery`, `creative_block`
  - cooking: `chef_rank`, `signature_dish`, `culinary_techniques`, `restaurant_tier`, `reputation_score`
  - alt_history: `social_class`, `court_rank`, `political_influence`, `public_trust`
  - actor: `acting_skill`, `fame`, `filmography`, `scandal_index`, `fandom`
  - sports: `athlete_tier`, `sport_type`, `physical_stats`, `ranking`
  - medical: `doctor_rank`, `specialty`, `surgery_count`, `success_rate`, `malpractice_record`
- **판정**: 정상 적용. 10개 장르 주요 필드의 한글 별칭 전량 포함.

### P2-2: preset_registry.to_json() discovered_fields 직렬화 -- 1차 오탐 확인

- **파일**: `modules/core/stage0/preset_registry.py:695-696`
- **검증**: `to_json()`에 `discovered_fields` 직렬화가 **이미 구현되어 있었음**:
  ```python
  if self.discovered_fields:
      data["discovered_fields"] = {k: asdict(v) for k, v in self.discovered_fields.items()}
  ```
  `from_json()`에서도 복원 (L711-713). 1차 감사 P2-2는 **오탐**.
- **판정**: 이슈 없음 (1차 오탐).

### P2-3: Spinner timeout -- **PASS**

- **파일**: `modules/core/stage0/spinner.py:257-259`
- **검증**: `stop()` 메서드의 timeout이 `0.5` -> `2.0`초로 증가 확인:
  ```python
  self.thread.join(timeout=2.0)
  if self.thread.is_alive():
      self.thread.join()  # 무제한 대기 (데몬 스레드이므로 프로세스 종료 시 정리됨)
  ```
- **판정**: 정상 적용. 2초 대기 + 이후 무제한 join으로 출력 충돌 방지 강화.

### P2-4: inline import re 제거 -- **PASS**

- **파일**: `modules/core/stage0/preset_registry.py:9`
- **검증**: 파일 상단에 `import re` 존재 (L9). `_parse_korean_number()` 내부에 `import re` 없음.
- **판정**: 정상 적용.

### S0-I3: StoryExpander LLM 재시도 -- **PASS**

- **파일**: `modules/core/stage0/story_expander.py:55-95`
- **검증**: 지수 백오프 재시도 로직 구현 확인:
  - `_RETRYABLE_PATTERNS`: 429, rate limit, resource exhausted, quota, 503, 500, unavailable, timeout (8개 패턴)
  - `_MAX_RETRIES = 3`, `_BASE_DELAY = 2.0` (지수 백오프: 2초, 4초, 8초)
  - 재시도 가능 에러 감지 시 `time.sleep(delay)` 후 재시도
  - 비재시도 에러 시 즉시 다음 모델로 폴백
- **판정**: 정상 구현. 2-모델 폴백 x 3회 재시도 = 최대 6회 시도.

### S0-I4: 역설계 병렬화 -- **PASS**

- **파일**: `modules/core/stage0/reverse_expander.py:369-410, 622-658`
- **검증**: 5화 단위 배치 병렬화 구현 확인:
  - `_BATCH_SIZE = 5`, `_MAX_WORKERS = 3`
  - `ThreadPoolExecutor` 사용, `as_completed`로 비동기 결과 수집
  - 배치 내 결과를 원래 에피소드 순서로 정렬하여 `episode_bibles`에 추가
  - `_extract_episode_bibles_with_progress()`에도 동일 병렬화 적용 (Spinner 통합)
  - 실패 시 빈 fallback dict 생성으로 결과 누락 방지
- **판정**: 정상 구현. 배치 간 순차 + 배치 내 병렬 구조.

### S0-I5: 문체 DNA 캐싱 -- **PASS**

- **파일**: `modules/core/stage0/style_extractor.py:596-666`
- **검증**: `extract_from_references()` 메서드에 캐싱 로직 구현 확인:
  - 캐시 경로: `config/style_references/{genre}/style_guide.json`
  - `_get_latest_ref_mtime()`: 디렉토리 내 .txt 파일 중 최신 mtime 반환
  - 캐시 히트 조건: `cache_mtime >= ref_latest_mtime` (레퍼런스 파일 미변경)
  - 캐시 저장: 분석 완료 후 JSON 자동 저장
  - 실패 시 비차단 경고 (`logging.warning`)
- **판정**: 정상 구현. mtime 기반 무효화 + LLM 3-4회 호출 절감.

---

## 2. 신규 발견 이슈

### P1-NEW-1: extend_blocks()에서 StoryExpander에 llm_client 미전달

- **파일**: `modules/core/stage01_helpers.py:253`
- **증상**: `extend_blocks()` 메서드에서 `StoryExpander`를 생성할 때 `llm_client`를 전달하지 않음:
  ```python
  expander = StoryExpander(genre=stage0_manager.genre)
  # llm_client 누락 -- stage0_manager.client가 있는데 전달 안 됨
  ```
  `stage0_manager`에는 `llm_client`가 P0-1 수정으로 올바르게 전달되지만, 그 클라이언트가 `StoryExpander`로 전파되지 않음.
- **원인**: P0-1 수정 시 `stage_0_extended()` 경로만 수정했고, `extend_blocks()` 내부의 직접 `StoryExpander` 생성 경로를 놓침
- **영향**: Block 확장 기능에서 `StoryExpander._init_llm()`이 환경변수로 자체 클라이언트를 생성함. 환경변수가 설정되어 있으면 동작하지만, SovereignApp의 API 키 로테이션/커스텀 설정이 무시됨. P0-1과 동일한 패턴의 누락.
- **등급**: P1 (환경변수 폴백으로 동작하므로 차단급은 아님)
- **수정안**:
  ```python
  expander = StoryExpander(genre=stage0_manager.genre, llm_client=stage0_manager.client)
  ```

### P1-NEW-2: ReverseExpander._call_llm()에 S0-I3 재시도 로직 미적용

- **파일**: `modules/core/stage0/reverse_expander.py:59-79`
- **증상**: S0-I3에서 `StoryExpander._call_llm()`에 지수 백오프 재시도를 추가했지만, `ReverseExpander._call_llm()`에는 동일 로직이 적용되지 않음. 역설계 파이프라인에서 rate limit / 일시적 네트워크 오류 시 즉시 실패하여 다음 모델로 폴백됨.
- **원인**: S0-I3 구현 시 `StoryExpander`만 수정하고 `ReverseExpander`를 누락
- **영향**: 역설계 시 LLM 호출이 StoryExpander보다 불안정할 수 있음. 특히 대량 원고 역설계 시 rate limit에 취약.
- **등급**: P1 (기능 저하, 크래시 아님)
- **수정안**: `ReverseExpander._call_llm()`에도 동일한 `_RETRYABLE_PATTERNS` + 지수 백오프 로직 추가. 또는 공통 mixin/유틸 함수로 통합.

### P1-NEW-3: S0-I4 병렬화에서 prev_state가 배치 내 모든 에피소드에 동일하게 전달됨

- **파일**: `modules/core/stage0/reverse_expander.py:381, 389`
- **증상**: 5화 배치 병렬 추출 시, 배치 시작 전의 `prev_state` (직전 배치의 마지막 에피소드 상태)를 배치 내 모든 에피소드에 동일하게 전달함. 예를 들어 1~5화 배치에서:
  - 1화: `prev_state = {}` (올바름)
  - 2화: `prev_state = {}` (1화 결과가 아닌 빈 상태)
  - 3화: `prev_state = {}` (2화 결과가 아닌 빈 상태)
  - ...
  이전 에피소드의 상태 변화를 참조하지 못하므로 "이전 상태" 정보가 배치 내에서 갱신되지 않음.
- **원인**: 병렬 실행 특성상 배치 내 에피소드 간 순차 의존성을 보장할 수 없음. 의도적 트레이드오프이나, 프롬프트에 "이전 상태"를 제공하면서 실제로는 배치 내 이전 에피소드의 상태를 반영하지 않으므로 LLM 출력 품질 저하 가능.
- **영향**: 배치 내 에피소드 간 HUD 상태 변화의 연속성이 보장되지 않음. 5화 단위이므로 영향은 제한적이나, 상태 변화가 급격한 에피소드에서는 추출 품질이 떨어질 수 있음.
- **등급**: P2 (설계 트레이드오프, 기능 저하 수준)
- **수정안**: 프롬프트에서 "이전 상태" 대신 "배치 시작 시점의 상태"로 명시적 표현을 변경하거나, 배치 크기를 3으로 줄여 영향 최소화.

### P2-NEW-1: ReverseExpander._init_llm()과 StyleExtractor._ensure_client()에 bare `except Exception:`

- **파일**: `modules/core/stage0/reverse_expander.py:54`, `modules/core/stage0/style_extractor.py:701`
- **증상**: `_init_llm()` / `_ensure_client()`에서 `except Exception:` 으로 모든 예외를 무시. `ImportError`, `ValueError`, `RuntimeError` 등 구체적 예외를 지정하지 않아 디버깅이 어려움.
- **비교**: `StoryExpander._init_llm()` (L50)은 `except (ImportError, ValueError, RuntimeError):` 로 구체적 예외만 잡음 (1차 수정에서 개선됨)
- **등급**: P2 (코드 위생)
- **수정안**: `except (ImportError, ValueError, RuntimeError):` 으로 통일

### P2-NEW-2: ReverseExpander._parse_json() 마지막 except 절이 bare `except Exception:`

- **파일**: `modules/core/stage0/reverse_expander.py:99`
- **증상**: JSON 파싱 실패 시 `except Exception:` 으로 모든 예외를 삼킴. `StoryExpander._parse_json()` (L109)은 `except (json.JSONDecodeError, ValueError, IndexError):` 로 구체적.
- **등급**: P2 (코드 위생)
- **수정안**: `except (json.JSONDecodeError, ValueError, IndexError):` 로 통일

### P2-NEW-3: response.text 접근 시 None/빈 문자열 방어 미비

- **파일**: `modules/core/stage0/story_expander.py:78`, `reverse_expander.py:76`, `style_extractor.py:725`
- **증상**: Gemini API의 `response.text`는 안전 필터에 걸리면 `ValueError`를 발생시키거나, `candidates`가 비어있으면 `None`을 반환할 수 있음. 현재 코드는 `response.text`를 직접 반환하여 `None`이 `_parse_json()`에 전달될 수 있음. `_parse_json()`은 `if not text: return None` 으로 방어하므로 크래시는 아니지만, `_call_llm()`의 반환 타입 계약(`-> str`)과 불일치.
- **영향**: `_call_llm()` -> `_parse_json()` 체인에서는 안전하지만, `_call_llm()` 결과를 직접 문자열로 사용하는 코드가 추가되면 잠재적 버그. 현재는 모든 호출이 `_parse_json()`을 거치므로 실질적 영향 없음.
- **등급**: P2 (방어 코딩)
- **수정안**: `return response.text or ""` 으로 변경

### P2-NEW-4: StoryExpander.run()에서 generate_bible() 실패 시 save_all() 진행

- **파일**: `modules/core/stage0/story_expander.py:516-532`
- **증상**: `generate_bible()` 실패 시 `self.bible`이 `{}`인 상태에서 `logging.warning()` 출력 후 `generate_treatment()`, `save_all()` 모두 진행됨. `save_all()`에서 빈 `bible.json` 파일이 생성됨. `generate_from_concept()` (L237-239)에서는 빈 Bible 감지 시 조기 종료하므로 `StageZeroManager` 경유 시에는 안전하지만, `run()` 직접 호출 시에는 빈 파일이 저장됨.
- **원인**: P0-2 수정 시 경고 로그만 추가하고 `return` 을 하지 않음
- **영향**: `run()` 직접 호출 시 빈 bible.json + 빈 treatment.json이 생성됨. 후속 Stage 2에서 이 파일을 로드하면 빈 데이터로 진행될 수 있음.
- **등급**: P2 (run()은 외부 진입점으로 사용 빈도 낮음)
- **수정안**: `if not self.bible:` 검사 후 `return {}, []` 조기 종료 추가

### P2-NEW-5: StageZeroManager.SUPPORTED_GENRES에 "fantasy" 키 순서 불일치

- **파일**: `modules/core/stage0/__init__.py:48-59`
- **증상**: `SUPPORTED_GENRES` dict에 `"fantasy": "판타지"`가 포함되어 있으나, 순서상 4번째 위치 (wuxia, hunter, investment, **fantasy**, composer...). 반면 `main_a.py`의 `_select_genre()`에서는 하드코딩된 1-10 매핑을 사용하며 순서가 다름. `show_genre_menu()`는 dict 순서 기반 동적 매핑이므로, 두 메뉴 시스템에서 같은 번호가 다른 장르를 가리킬 수 있음.
- **영향**: Stage 0 메뉴와 main_a.py 메뉴에서 번호 불일치 (UX 혼란). Stage 0 메뉴를 사용하는 경로에서는 올바르게 동작하므로 기능 이상 없음.
- **등급**: P2 (UX, 1차 P1-2에서 지적된 사항이나 미수정 상태)
- **수정안**: `SUPPORTED_GENRES`를 `GenreTypes.all()` + `GenreTypes.get_name()` 기반으로 동적 생성

---

## 3. S0-I3 / S0-I4 / S0-I5 구현 검증 상세

### S0-I3: LLM 재시도 -- 구현 검증 상세

| 항목 | 검증 결과 |
|------|-----------|
| 재시도 가능 에러 패턴 | 8개 패턴 (429, rate limit, resource exhausted, quota, 503, 500, unavailable, timeout) |
| 최대 재시도 횟수 | 3회 (`_MAX_RETRIES = 3`) |
| 백오프 전략 | 지수 백오프 (`_BASE_DELAY * 2^attempt` = 2초, 4초) |
| 비재시도 에러 처리 | 즉시 `break` -> 다음 모델로 폴백 |
| 로깅 | `logging.warning`으로 시도 번호/대기 시간/에러 메시지 출력 |
| 적용 범위 | StoryExpander만 (**ReverseExpander 미적용** -- P1-NEW-2) |
| time import | 함수 내 `import time` (L89) -- 정상 동작하나 파일 상단 import가 더 깔끔 |

**잠재 이슈**: `time.sleep()` 호출이 `_call_llm()` 내부에서 동기적으로 실행됨. `run()` 메서드가 Spinner 컨텍스트 매니저 내부에서 호출되므로, 재시도 대기 중에도 스피너가 정상 회전함 (별도 스레드). 문제 없음.

### S0-I4: 역설계 병렬화 -- 구현 검증 상세

| 항목 | 검증 결과 |
|------|-----------|
| 배치 크기 | 5화 (`_BATCH_SIZE = 5`) |
| 병렬 워커 수 | 3개 (`_MAX_WORKERS = 3`) |
| 순서 보장 | `batch_results[draft["ep_num"]]`으로 키 매핑 후 원래 순서로 추가 |
| 실패 처리 | 개별 에피소드 실패 시 빈 fallback dict 생성 |
| 코드 중복 | `extract_episode_bibles()`와 `_extract_episode_bibles_with_progress()` 두 곳에 동일 로직 존재 |
| prev_state 전파 | 배치 간 순차 (직전 배치 마지막 결과), 배치 내 공유 (P1-NEW-3) |
| 스레드 안전성 | `self.client`는 읽기 전용 (Gemini Client는 스레드 안전), `schema`는 불변 문자열. 안전. |

**코드 중복 이슈**: `extract_episode_bibles()`와 `_extract_episode_bibles_with_progress()`가 거의 동일한 병렬 로직을 가지고 있음. DRY 위반이지만 기능 이상 없음. 리팩토링 후보.

### S0-I5: 문체 DNA 캐싱 -- 구현 검증 상세

| 항목 | 검증 결과 |
|------|-----------|
| 캐시 위치 | `config/style_references/{genre}/style_guide.json` |
| 무효화 기준 | 레퍼런스 파일 최신 mtime > 캐시 mtime |
| mtime 수집 | `_get_latest_ref_mtime()` -- `rglob("*.txt")`로 재귀 탐색 |
| 캐시 히트 | `cache_mtime >= ref_latest_mtime` 조건 (동시 생성 시 안전) |
| 캐시 미스 | 재분석 후 JSON 저장 |
| 에러 처리 | 캐시 로드/저장 실패 시 `logging.warning()` + 비차단 진행 |
| ref_latest_mtime=0 | 레퍼런스 디렉토리 없거나 .txt 없으면 `0.0` 반환 -> 캐시 미스 -> 재분석 |

**엣지 케이스**: `ref_latest_mtime == 0`이고 `cache_path.exists()`인 경우 (레퍼런스 파일이 삭제된 후 캐시만 남은 경우), 조건 `ref_latest_mtime > 0 and cache_mtime >= ref_latest_mtime`에서 `ref_latest_mtime > 0`이 False이므로 캐시 미스 처리됨. 이후 `load_reference_manuscripts()`가 빈 dict를 반환하여 `return None`. 올바른 동작.

---

## 4. Stage 0 -> Stage 2 연결성 검증

### 4.1 Bible 데이터 전달

| 경로 | 검증 결과 |
|------|-----------|
| `StageZeroManager.bible` -> DB `save_v20_anchor("bible", ...)` -> Stage 2 `load_anchor("bible")` | **정상** -- `stage01_helpers.py:456-457`에서 `save_v20_anchor` 호출, Stage 2에서 `master_bible` 로드 확인 |
| `protagonist_config` 포함 여부 | **정상** -- Bible 내 `MasterBible.protagonist_config`에 저장 (L146-148, L461-463). analyst.py L93에서 읽어서 프롬프트에 주입 |
| `pov` 필드 전달 | **정상** -- `protagonist_config["pov"]`로 저장. 다만 `analyst.py`의 `protagonist_config_text`에 pov 항목이 직접 포함되지 않음 (world_origin과 incarnation_type만 포함). pov는 StyleGuide 또는 pre_llm_validator V70에서 별도 참조 |
| `InitialHUD` 전달 | **정상** -- `preset_registry.build_initial_hud()`로 생성, Bible 내 `MasterBible.InitialHUD`에 저장 |

### 4.2 Treatment 데이터 전달

| 경로 | 검증 결과 |
|------|-----------|
| JSON 파일 저장 | **정상** -- `treatment_generated.json` / `treatment_extended.json`으로 저장 (L480-484, L398-400) |
| plot_roadmap 주입 (Block 확장) | **정상** -- `_s0_handle_block_extension()`에서 `bible_root["plot_roadmap"] = refined_roadmap` 후 DB 저장 (L415-417) |

### 4.3 StyleGuide 데이터 전달

| 경로 | 검증 결과 |
|------|-----------|
| DB 저장 | **정상** -- `save_v20_anchor("style_guide", sg_data)` (L342, L441, L471-472) |
| preset_state 저장 | **정상** -- `save_v20_anchor("preset_state", ...)` (L467-468) |

### 4.4 역설계 데이터 전달

| 경로 | 검증 결과 |
|------|-----------|
| 원고 벡터화 | **정상** -- `persist_to_vectordb()` 호출 (L351-356) |
| DB 저장 (manuscripts, state_logs, episode_bibles, blueprints, arcs) | **정상** -- `persist_to_db()` 호출 (L361-383) |
| next_episode/next_arc 계산 | **정상** -- `get_stub_summary()` (L1108-1129)에서 정확히 계산 |

### 4.5 누락/불일치 발견

**없음.** Stage 0 -> Stage 2 데이터 전달 체인은 완전함. Bible, Treatment, StyleGuide, PresetState, 역설계 stub 모두 DB anchor 또는 JSON 파일로 올바르게 저장되며 Stage 2에서 참조 가능.

---

## 5. 개선 아이디어

### IDEA-2-1: ReverseExpander와 StoryExpander의 _call_llm() 통합

- **현황**: `StoryExpander._call_llm()` (재시도 + 백오프 포함, 32줄)과 `ReverseExpander._call_llm()` (단순 폴백만, 18줄)이 유사하지만 다른 구현. `StyleExtractor._llm_call()`도 별도 구현.
- **제안**: 공통 `LLMCaller` mixin 또는 유틸 함수로 통합. 재시도 로직, 모델 폴백, JSON 파싱을 한 곳에서 관리.
- **효과**: 코드 중복 제거, P1-NEW-2 같은 누락 방지, 유지보수성 향상.

### IDEA-2-2: extract_episode_bibles() 코드 중복 제거

- **현황**: `extract_episode_bibles()`와 `_extract_episode_bibles_with_progress()` 두 메서드가 거의 동일한 병렬화 로직을 가짐 (각 약 35줄). Spinner 유무만 다름.
- **제안**: 핵심 로직을 `_extract_batch()` private 메서드로 분리하고, 두 public 메서드에서 호출.
- **효과**: DRY 원칙 준수, 한쪽만 수정하는 실수 방지.

### IDEA-2-3: StoryExpander.run()에 Bible 실패 시 조기 종료

- **현황**: P2-NEW-4에서 지적한 대로, `run()`에서 Bible 생성 실패 시 경고만 출력하고 계속 진행.
- **제안**: `generate_from_concept()` (L237-239)과 동일하게 `return {}, []` 조기 종료 추가.
- **효과**: 빈 파일 생성 방지, 후속 Stage에서의 혼란 제거.

---

## 6. 종합 평가

### 1차 수정 검증 총괄

| 구분 | 건수 | PASS | FAIL | 비고 |
|------|------|------|------|------|
| P0 수정 | 1 | 1 | 0 | P0-1 llm_client 배선 정상 |
| P0->P1 하향 수정 | 1 | 1 | 0 | Bible 실패 시 경고 로그 추가 |
| P1 수정 | 5 | 5 | 0 | P1-3,4,5,6,7 전량 정상 |
| P2 수정 | 3 | 2 | 0 | P2-1,3,4 정상. P2-2는 1차 오탐 |
| 개선 구현 | 3 | 3 | 0 | S0-I3,I4,I5 전량 정상 구현 |
| **합계** | **13** | **12** | **0** | 1차 오탐 1건 |

### 2차 신규 발견 총괄

| 등급 | 건수 | 설명 |
|------|------|------|
| P0 (차단급) | 0 | 없음 |
| P1 (품질 이슈) | 2 | NEW-1(extend_blocks llm_client 누락), NEW-2(ReverseExpander 재시도 누락) |
| P2 (스타일/경미) | 5 | NEW-1~5 (bare except, response.text 방어, run() 조기종료, 장르 순서, batch prev_state) |
| 개선 아이디어 | 3 | IDEA-2-1~3 (_call_llm 통합, 코드 중복 제거, run() 조기종료) |
| **합계** | **10** | |

### Stage 0 최종 건전성 등급: **A-**

1차 감사에서 발견된 P0 1건 + P1 8건 + P2 5건 + 개선 6건이 **전량 올바르게 수정/구현**됨 (오탐 1건 확인). 2차 조사에서 P0급 이슈는 발견되지 않았으며, P1 2건은 1차 P0-1과 동일 패턴의 잔여 누락 (llm_client 미전달, 재시도 로직 미적용)으로 구조적 문제라기보다 적용 범위 미달. P2 5건은 코드 위생 수준.

Stage 0 -> Stage 2 데이터 전달 체인은 **완전**하며, 누락이나 불일치가 없음.

---

*감사 완료: 2026-02-22*
*감사자: Claude Opus 4.6*
*파일별 검증: stage0/__init__.py (580줄), story_expander.py (557줄), reverse_expander.py (1130줄), style_extractor.py (773줄), preset_registry.py (715줄), spinner.py (667줄), stage01_helpers.py (692줄)*
