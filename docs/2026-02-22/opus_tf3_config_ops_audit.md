# Opus TF3: 설정 관리, 외부 의존성, 배포/운영 준비도 감사

> **감사일**: 2026-02-22
> **감사자**: Claude Opus 4.6
> **대상 브랜치**: main (`5c762b6`)
> **범위**: 설정 파일 일관성, 환경 변수, 외부 의존성, 파일 경로, 로깅, 시크릿 관리, 초기화 순서

---

## 요약

| 등급 | 건수 | 설명 |
|------|------|------|
| **CRITICAL** | 2 | 시크릿 노출 (즉시 조치 필요) |
| **HIGH** | 5 | 운영 안정성에 직접 영향 |
| **MEDIUM** | 7 | 일관성 부재, 관리 부채 |
| **LOW** | 6 | 개선 권장 사항 |

---

## 1. 시크릿 관리 [CRITICAL]

### C-1. `.env` 파일이 Git에 트래킹됨

- **파일**: `.env`, `tests/stage4_v2_test/project/.env`
- **증거**: `git ls-files --error-unmatch .env` -- 정상 출력 (트래킹 중)
- **내용**: `GOOGLE_API_KEY= REDACTED_GOOGLE_API_KEY`, `SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...`
- **이력**: 커밋 `b69763d` ("Upload .env and projects folder as requested")에서 최초 추가됨
- **위험도**: **CRITICAL** -- API 키와 Slack 웹훅이 Git 히스토리에 영구 기록됨. `.gitignore`에 `.env` 패턴이 있으나 이미 트래킹된 파일에는 효과 없음.
- **조치 권장**:
  1. 노출된 Google API 키와 Slack 웹훅을 즉시 폐기/재발급
  2. `git rm --cached .env tests/stage4_v2_test/project/.env`
  3. 리포지토리가 공개(public)인 경우 `git filter-branch` 또는 BFG Repo Cleaner로 히스토리 정리
  4. 프로젝트별 `.env` (`projects/*/.env`) 도 `test_mode/.env` 등 다수 존재하지만 `.gitignore`의 `_*.txt` 패턴으로 우연히 제외되거나 untracked 상태

### C-2. `.gitignore` 불완전

- **현재 상태**: `.env`와 `.env.local`이 `.gitignore`에 명시됨 (L12-13)
- **문제**: 이미 트래킹된 `.env`는 `.gitignore`로 제거되지 않음
- **누락 패턴**: `projects/*/.env`, `test_mode/**/.env`, `*.db` (SQLite 프로덕션 DB), `crash_dump.log`, `projects/` 디렉토리 전체

---

## 2. 설정 파일 일관성 [HIGH ~ MEDIUM]

### H-1. validation.yaml에 Dead Configuration 섹션 다수 존재

`config/settings/validation.yaml`에 정의되어 있지만, 코드에서 `_threshold()` 또는 `_LazyThreshold()`로 읽히지 않는 키:

| YAML 섹션 | 키 | 상태 | 비고 |
|-----------|-----|------|------|
| `thresholds` | `tactical_duplicate`, `pattern_min_hits`, `min_tactical_doc_length` 등 8건 전체 | **Dead** | `constants.py::Thresholds` 클래스에 하드코딩 값으로 중복. `_LazyThreshold`를 사용하지 않음 |
| `volume` | `arcs_per_volume`, `episodes_per_arc` 등 4건 전체 | **Dead** | `constants.py::VolumeSettings`에 하드코딩. `_LazyThreshold` 미사용 |
| `retry` | `director_max_attempts`, `architect_max_attempts`, `writer_max_attempts`, `blueprint_max_attempts`, `cache_ttl_seconds`, `api_timeout_seconds` | **5/6 Dead** | `retry.analyst_max_attempts`만 `stage2_preflight.py`에서 사용됨 |
| `writing` | `max_retry_per_episode`, `min_episode_loop_guard`, `max_failure_streak` 3건 전체 | **Dead** | `constants.py::WritingLimits`에 하드코딩 |
| `scoring.breakdown` | `character_consistency: 15` 등 6건 | **Dead** | 코드에서 `scoring.breakdown.*`을 _threshold로 조회하는 곳 없음 |

**위험**: 운영자가 YAML 값을 변경해도 실제 동작에 반영되지 않음. YAML이 "Single Source of Truth"라는 주석(L2-3)과 실제 동작이 불일치.

### H-2. scoring.genre_thresholds가 4개 장르만 정의

- **YAML**: `wuxia`, `hunter`, `investment`, `fantasy` (4개)
- **코드**: `ScoringValidator.GENRE_THRESHOLDS`에도 동일 4개만 정의 (L29-34)
- **실제 지원 장르**: 10개 (`wuxia`, `hunter`, `investment`, `fantasy`, `composer`, `cooking`, `alt_history`, `actor`, `sports`, `medical`)
- **결과**: composer, cooking, alt_history, actor, sports, medical 6개 장르는 `default_pass_threshold` (70)으로 폴백. 장르별 튜닝 불가능 상태.

### H-3. context.vector_max_results_s2 YAML-코드 기본값 불일치

| 키 | YAML 값 | 코드 기본값 |
|----|---------|------------|
| `context.vector_max_results_s2` | `12` | `8` (stage2_preflight.py L111, L684) |
| `context.vector_max_results_s4` | `16` | `12` (stage4_context_builder.py L130, L641) 또는 `16` (stage4_interview_round.py L461) |

**위험**: YAML이 로드 실패하면 코드 기본값이 적용되어, 정상 동작과 다른 수의 벡터 결과를 가져옴. 동일 키의 코드 기본값이 파일마다 다름 (s4: 12 vs 16).

### H-4. system.yaml에 `max_output_tokens` 누락

- **코드** (`base_agent.py` L141): `MAX_OUTPUT_TOKENS = _SYSTEM_CFG.get("api", {}).get("max_output_tokens", 8192)`
- **system.yaml**: `api` 섹션에 `delay`, `timeout`, `quota_cache_duration`만 존재. `max_output_tokens` 없음.
- **결과**: 항상 하드코딩 기본값 `8192` 사용. YAML에서 튜닝하려면 키를 추가해야 함.
- **추가**: `api.timeout`도 system.yaml에 `90`이지만, validation.yaml `retry.api_timeout_seconds`에 `300`이 있음. 어느 것이 실제 사용되는지 혼동 가능.

### M-1. models.yaml와 ConfigManager.settings 이중 설정

- `config/models.yaml`: 에이전트별 모델 매핑 (21개 에이전트)
- `modules/core/config_manager.py` L42-54: `settings["models"]`에 5개 에이전트만 하드코딩
- `base_agent.py`는 `models.yaml`을 직접 로드 (L57-68)
- `main_a.py`는 `_load_models_yaml()`과 `sys.get_v20_orchestrator_config()["models"]`를 폴백 체인으로 사용
- **위험**: 모델 설정의 SSOT가 2곳에 분산. `config_manager.py`의 하드코딩 모델은 사실상 `models.yaml` 부재 시 레거시 폴백이지만, `gemini-2.5-flash`라는 구 모델명이 남아있음 (L74).

---

## 3. 환경 변수 [HIGH ~ MEDIUM]

### H-5. API 키 누락 시 에러 메시지 품질

| 진입점 | API 키 없을 때 동작 |
|--------|---------------------|
| `main_a.py` L233 | `genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))` -- None 전달. Gemini SDK가 나중에 암호화 안 된 에러 발생 |
| `base_agent.py` L164-172 | `_init_api_keys()` -- 키가 0개면 빈 리스트. 이후 API 호출 시 비명시적 실패 |
| `vec_memory.py` L61 | `api_key or os.getenv("GOOGLE_API_KEY", "")` -- 빈 문자열로 임베딩 API 호출 시도, 에러 발생 |
| `smoke_sc.py` L62 | 유일하게 명시적 체크: `if not os.getenv("GOOGLE_API_KEY"): print(...); return` |

**문제**: 메인 진입점(`main_a.py`)에서 API 키 유효성을 체크하지 않음. 누락 시 에이전트 초기화 단계에서 암호 같은 SDK 에러 메시지가 출력됨.

### M-2. 환경 변수 목록이 문서화되지 않음

사용 중인 환경 변수 전체:

| 변수명 | 필수 | 사용처 |
|--------|------|--------|
| `GOOGLE_API_KEY` | **필수** | Gemini API 인증 (main_a.py, base_agent.py 등) |
| `GOOGLE_API_KEY_2` ~ `_9` | 선택 | API 키 순환 (base_agent.py L168-171) |
| `SLACK_WEBHOOK_URL` | 선택 | Slack 알림 (slack_bot.py) |
| `GEMINI_API_KEY` | 레거시 | `GOOGLE_API_KEY` 폴백 (stage0/*.py만 사용) |
| `DEBUG_MODE` | 선택 | analyst.py L142에서만 사용 (true 시 추가 로깅) |
| `PROMPT_DIR` | 선택 | 프롬프트 디렉토리 오버라이드 (prompt_loader.py) |
| `EDITOR` | 선택 | 외부 에디터 (blueprint_editor.py, 기본값 "nano") |
| `PYTHONIOENCODING` | 자동설정 | Windows UTF-8 (main_a.py) |

`.env.example` 파일이 존재하지 않아 신규 개발자가 어떤 환경 변수가 필요한지 알 수 없음.

### M-3. `GEMINI_API_KEY` 레거시 폴백 불일치

`stage0/reverse_expander.py`, `story_expander.py`, `style_extractor.py`에서만 `os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")` 패턴 사용. 나머지 코드는 `GOOGLE_API_KEY`만 참조. 프로덕션에서 `GEMINI_API_KEY`만 설정하면 stage0 모듈만 동작하고 나머지는 실패하는 혼란 가능.

---

## 4. 외부 의존성 [HIGH ~ MEDIUM]

### H-6. PyYAML이 requirements.txt에 없음

- **사용처**: `main_a.py` (L35: `import yaml`), `base_agent.py` (L10), `config_manager.py` (L106), `context_advisor.py` (L25), `genre_guards/base_guard.py` (L13), `genre_guards/work_guard.py` (L15)
- **requirements.txt**: PyYAML 미기재. `google-generativeai`가 간접 의존하여 우연히 설치될 수 있으나, 이는 fragile dependency.
- **위험**: `pip install -r requirements.txt`만으로는 PyYAML이 설치되지 않을 수 있음. 특히 가상 환경을 새로 구성할 때 `import yaml` 실패.

### M-4. 의존성 버전 고정 불충분

```
requirements.txt (현재):
  google-generativeai>=0.8.0
  rich>=13.0
  python-dotenv>=1.0
  numpy>=1.26
  requests>=2.31
  beautifulsoup4>=4.12
  sqlite-vec>=0.1.6
  pydantic>=2.0
  pytest>=8.0
  nest-asyncio>=1.5
```

- 모두 `>=` (최소 버전)만 지정. `==` 또는 상한(`<`) 없음.
- **위험**: `pip install -r requirements.txt`가 호환되지 않는 최신 버전을 설치할 수 있음. 특히 `google-generativeai>=0.8.0`은 현재 빠르게 변경되는 라이브러리.
- **개선**: `pip freeze > requirements.lock` 또는 `pip-tools`로 lock 파일 관리 권장.

### M-5. beautifulsoup4 미사용 가능성

- `requirements.txt`에 `beautifulsoup4>=4.12` 명시
- `modules/` 내에서 `from bs4` 또는 `import beautifulsoup` 사용처 없음
- `main_a.py`에서도 미사용
- 레거시 의존성이거나 `tools/`, `백업의백업의백업/` 에서만 사용될 가능성

### M-6. dev 의존성과 production 의존성 미분리

- `pytest>=8.0`, `nest-asyncio>=1.5`가 프로덕션 requirements.txt에 포함
- 프로덕션 배포 시 불필요한 테스트 프레임워크가 설치됨
- 권장: `requirements.txt` (prod) + `requirements-dev.txt` (test/lint) 분리

---

## 5. 파일 경로 하드코딩 [MEDIUM]

### M-7. CWD 의존 상대 경로 패턴

다음 코드들은 `Path.cwd()` 또는 상대 경로(`Path("bible")`)에 의존. 작업 디렉토리가 프로젝트 루트가 아니면 실패:

| 파일 | 경로 | 문제 |
|------|------|------|
| `config_manager.py` L20 | `self.root = Path.cwd()` | CWD 의존 |
| `system.py` L17 | `self.root = Path.cwd()` | CWD 의존 |
| `services/ui_service.py` L33 | `Path("bible")` | CWD 기준 상대 |
| `services/ui_service.py` L49 | `Path("treatments")` | CWD 기준 상대 |
| `stage0/style_extractor.py` L573, L609 | `Path("config/style_references")` | CWD 기준 상대 |
| `stage0/__init__.py` L396 | `Path("config/style_references")` | CWD 기준 상대 |
| `main_a.py` L228 | `_PROJECTS_DIR = "projects"` | CWD 기준 상대 |

- `prompt_loader.py`는 `Path(__file__).resolve()` 기반으로 올바르게 구현됨 (모범 사례).
- `context_advisor.py` L23도 `Path(__file__).resolve()` 기반 (모범 사례).
- **영향**: 프로덕션에서 `cron`이나 `systemd`로 다른 디렉토리에서 실행하면 설정 파일을 찾지 못함.

### L-1. Windows 전용 경로 하드코딩 없음 (양호)

- `modules/` 내에 `C:\Users`, `C:/Users` 등 절대 경로 하드코딩 없음
- 백슬래시 경로 리터럴도 없음 (이스케이프 문자열은 regex 관련)
- `Path` 객체를 일관되게 사용하여 크로스플랫폼 호환성 양호

---

## 6. 로깅 설정 [MEDIUM ~ LOW]

### M-8. logging.warning 과다 사용

- `modules/` 전체에서 `logging.warning()` 호출 **477건** (66개 파일)
- 정상 동작 흐름에서도 `logging.warning()`을 정보 전달용으로 사용:
  - `project_manager.py`: **36건** (정상 저장 확인 메시지에 warning 사용)
  - `stage4_interview_round.py`: **18건**
  - `stage2_finalizer.py`: **16건**
  - `stage4_post_processor.py`: **16건**
- **문제**: 프로덕션 로그에서 실제 경고와 정상 동작 메시지가 혼재. 모니터링 알림 설정 시 노이즈 과다.
- **예시** (`project_manager.py` L68):
  ```python
  logging.warning(f"[DB] SQLite S-Grade 엔진 가동: {self.db_path.name}")
  ```
  이것은 정상 기동 메시지인데 WARNING 레벨.

### L-2. StudioLogger가 실제로 사용되지 않음

- `modules/core/logger.py`에 `StudioLogger` (싱글톤 패턴, 듀얼 출력) 구현 완료
- 그러나 실제 코드에서 `from modules.core.logger import get_logger`를 사용하는 곳은 `logger.py` 자체 docstring 1건뿐
- 모든 모듈이 `logging.warning()`, `logging.info()` 등 표준 라이브러리 직접 호출
- **결과**: StudioLogger의 파일 로깅, 세션 추적, 메트릭 카운팅 기능이 전부 미사용

### L-3. 루트 로거 레벨 설정 부재

- `main_a.py`에서 `logging.basicConfig()` 호출 없음
- `StudioLogger`가 `"글도비"` 이름의 로거를 설정하지만, 코드가 `logging.warning()` (루트 로거)을 사용하므로 별개
- **결과**: 루트 로거의 기본 레벨(WARNING)이 적용됨. `logging.info()`와 `logging.debug()` 호출이 콘솔에 출력되지 않을 수 있음.

### L-4. 파일 핸들러가 DEBUG 레벨로 고정

- `logger.py` L90: `self.file_handler.setLevel(logging.DEBUG)`
- 프로덕션에서도 DEBUG 레벨 로그가 파일에 기록됨
- 장기 운영 시 로그 파일 크기 급증 가능
- 로그 로테이션(`RotatingFileHandler`) 미사용

---

## 7. 초기화 순서 의존성 [LOW ~ MEDIUM]

### L-5. SovereignApp 기동 순서 체인

`main_a.py` 기동 순서 (필수 선행 조건 위배 시 크래시):

```
1. load_dotenv()                    -- .env에서 GOOGLE_API_KEY 로드
2. genai.Client(api_key=...)        -- API 키 없으면 SDK 에러
3. StudioSystem()                   -- Path.cwd() 기준 경로 설정
4. _select_genre()                  -- 장르 선택 (사용자 입력)
5. _select_project()                -- 프로젝트 선택 (사용자 입력)
6. load_dotenv(project/.env)        -- 프로젝트별 키 오버라이드
7. sys.boot_v20_project()           -- DB 연결, ProjectContext 초기화
8. PromptLoader.invalidate_cache()  -- 프롬프트 캐시 리셋
9. Guard 초기화                     -- 장르 Guard + WorkGuard + StyleGuard
10. VecMemory()                     -- DB 커넥션 공유, sqlite-vec 초기화
11. _attach_agents()                -- 에이전트 초기화 (Guard, API client 필요)
12. _ignite_quad_cache_system()     -- 4중 캐시 시스템
```

- **취약점 1**: 단계 2에서 API 키 검증 없이 `genai.Client` 생성. 키가 유효하지 않으면 단계 11에서야 에러 발생.
- **취약점 2**: 단계 6에서 프로젝트별 `.env`로 키를 오버라이드하면 `BaseAgent._keys_initialized = False`로 리셋하고 재초기화 (L928-932). 이 사이에 다른 스레드가 에이전트를 사용하면 경합 발생 가능 (단, 현재 단일 스레드 기동이므로 실질 위험 낮음).
- **취약점 3**: `ConfigManager.__init__()`에서 `self.root = Path.cwd()`를 캡처하므로, 이후 `os.chdir()`이 일어나면 모든 경로가 깨짐.

### L-6. PromptLoader 싱글톤 캐시 문제

- `PromptLoader`가 클래스 레벨 `_cache`를 사용하는 싱글톤
- 프로젝트 전환 시 `invalidate_cache()` 호출이 필수이나, 이는 `main_a.py` L938에서만 수행
- 다른 진입점(예: 테스트, 도구 스크립트)에서는 캐시 무효화 없이 이전 프로젝트의 프롬프트가 잔류 가능

---

## 8. 추가 발견 사항

### L-7. 프롬프트 YAML 40개 vs 에이전트 수 불일치

- `config/prompts/` 에 40개 YAML 파일 존재
- 실제 에이전트: 20+개 (`modules/domain/agents/*.py`)
- `PromptLoader`는 커스텀 YAML 파서를 사용 (PyYAML 의존 회피, L76-78). 이 파서는 `KEY_NAME: |` 패턴만 인식하므로, 표준 YAML 기능(앵커, 참조 등)은 미지원.

### L-8. crash_dump.log 미관리

- `main_a.py` L10: `open("crash_dump.log", "w")` -- 항상 CWD에 생성
- `.gitignore`에 `crash_dump.log` 패턴 없음 (`.log`으로 커버)
- 그러나 프로덕션 배포 시 이 파일의 위치/로테이션이 관리되지 않음

---

## 종합 진단표

| # | 등급 | 항목 | YAML/코드 위치 | 요약 |
|---|------|------|---------------|------|
| C-1 | **CRITICAL** | .env Git 트래킹 | `.env` | API 키/Slack 웹훅이 Git 히스토리에 영구 기록 |
| C-2 | **CRITICAL** | .gitignore 불완전 | `.gitignore` | 이미 트래킹된 .env에 무력 |
| H-1 | HIGH | YAML Dead Config | `validation.yaml` thresholds/volume/writing/retry/scoring.breakdown | 5개 섹션, 20+키 미사용 |
| H-2 | HIGH | 장르 임계값 미완성 | `validation.yaml` scoring.genre_thresholds | 10장르 중 4장르만 정의 |
| H-3 | HIGH | YAML-코드 기본값 불일치 | `validation.yaml` context.* | vector_max_results 기본값 YAML/코드 상이 |
| H-4 | HIGH | system.yaml 키 누락 | `config/system.yaml` | max_output_tokens 미정의, timeout 이중 정의 |
| H-5 | HIGH | API 키 누락 에러 품질 | `main_a.py` L233 | 유효성 미검증, 늦은 에러 발생 |
| H-6 | HIGH | PyYAML requirements 누락 | `requirements.txt` | 핵심 의존성 미기재 |
| M-1 | MEDIUM | 모델 설정 SSOT 분산 | `models.yaml` vs `config_manager.py` | 2곳에서 모델 정의 |
| M-2 | MEDIUM | 환경 변수 미문서화 | -- | `.env.example` 없음 |
| M-3 | MEDIUM | GEMINI_API_KEY 레거시 | stage0/*.py | 일부 모듈만 폴백 지원 |
| M-4 | MEDIUM | 버전 고정 불충분 | `requirements.txt` | `>=`만 사용, lock 파일 없음 |
| M-5 | MEDIUM | beautifulsoup4 미사용 | `requirements.txt` | modules/ 내 사용처 없음 |
| M-6 | MEDIUM | dev/prod 의존성 미분리 | `requirements.txt` | pytest가 프로덕션에 포함 |
| M-7 | MEDIUM | CWD 의존 상대 경로 | 6개 파일 | cron/systemd 실행 시 실패 |
| M-8 | MEDIUM | logging.warning 과다 | 66파일 477건 | 정상 메시지와 경고 혼재 |
| L-1 | LOW | Windows 경로 하드코딩 없음 | -- | **양호** |
| L-2 | LOW | StudioLogger 미사용 | `logger.py` | 구현만 있고 실제 미적용 |
| L-3 | LOW | 루트 로거 설정 부재 | `main_a.py` | basicConfig 없음 |
| L-4 | LOW | 파일 로그 DEBUG 고정 | `logger.py` L90 | 프로덕션 로그 크기 관리 불가 |
| L-5 | LOW | 기동 순서 의존성 | `main_a.py` | API 키 유효성 늦은 검증 |
| L-6 | LOW | PromptLoader 캐시 잔류 | `prompt_loader.py` | 프로젝트 전환 시 수동 무효화 필요 |

---

## 권장 조치 우선순위

### 즉시 (1일 이내)
1. 노출된 API 키/웹훅 폐기 및 재발급
2. `git rm --cached .env tests/stage4_v2_test/project/.env`
3. `requirements.txt`에 `PyYAML>=6.0` 추가

### 단기 (1주 이내)
4. `.env.example` 생성 (필수/선택 환경 변수 목록)
5. `main_a.py` 기동 초기에 `GOOGLE_API_KEY` 유효성 검증 추가
6. `validation.yaml` Dead Config 섹션에 `_LazyThreshold` 적용 또는 섹션 제거
7. 나머지 6개 장르의 `scoring.genre_thresholds` 추가
8. `system.yaml`에 `max_output_tokens` 키 추가
9. `context.vector_max_results_s2/s4` 코드 기본값을 YAML 값과 통일

### 중기 (1개월 이내)
10. `requirements.txt` 버전 고정 + lock 파일 도입
11. `requirements-dev.txt` 분리 (pytest, nest-asyncio)
12. `logging.warning` -> `logging.info` 일괄 정리 (정상 동작 메시지)
13. CWD 의존 경로를 `Path(__file__).resolve()` 기반으로 전환
14. beautifulsoup4 사용 여부 확인 후 제거

---

*이 문서는 연구/감사 목적이며 코드 수정은 포함하지 않습니다.*
