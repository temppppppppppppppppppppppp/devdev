# T08: Config / Data / Contract 계층

Surveyor: Claude Code (Terminal 8)
Date: 2026-04-19
Scope: `config/`, `contracts/`, `datasets/`, `libraries/` 하 YAML/JSON 전량 + 로더·스키마·환경분리·env 관리 감사

## 1. Executive Summary

- 성숙도 판정: **Pre-production** — 핵심 튜너블(`validation.yaml`), 에이전트-모델 라우팅(`models.yaml`), 장르 가드(`config/genres/*.yaml`), 11개 계약 스키마(`contracts/*.schema.json`)까지 외부화되어 있고 `ConfigManager`는 키마다 `authoritative_source / fallback_source / effective_source / used_fallback`을 반환하는 provenance-우선 로더라, 설정 토대는 단단하다. 다만 (a) 과거 커밋(`b69763dc`)에 실 API 키가 포함된 `.env`가 히스토리에 박혀 있고, (b) 환경(dev/prod/test) 분리가 없고, (c) `jsonschema` 라이브러리가 전혀 import되지 않아 스키마 11종 중 Stage0 4종만 수작업 검증되며, (d) `DEFAULT_AGENT_MODELS`·`analyst_libraries.json` 등 인라인 기본값이 YAML SSOT와 병존해 드리프트 위험이 있다.
- 한줄 요약: "provenance 계약은 훌륭한데 환경 분리·시크릿 운영·스키마 런타임 강제 3축이 비어 있다."

## 2. 강점 (Strengths)

**(S1) 계약 인지형 로더 (Contract-Aware Config Loader)**
- `modules/core/config_manager.py:177` `get_guard_threshold_contract(key, default)` — 단일 read가 `{authoritative_source, compatibility_source, fallback_source, effective_source, effective_value, used_fallback, used_compatibility}` 전체 계약을 반환. type coercion 실패 시 `type_mismatch_source`까지 기록(199).
- `modules/core/models_config.py:77` `load_model_contract(section, key, fallback)` — 모델 라우팅에도 같은 패턴 적용.
- `modules/core/config_manager.py:247` `build_config_authority_summary()` — 런타임 진단용 집합 뷰.
- 결과: 어떤 임계값이든 "누가 승리했는가(`effective_source`)"를 호출자가 추적 가능 → 관측·재현성 관점에서 드문 수준.

**(S2) YAML-first + 하드코드 fallback 이중 레이어**
- `config/system.yaml:3` 헤더 주석이 계약을 명문화: "이 파일이 없거나 파싱 실패 시 base_agent.py 하드코딩 폴백 사용".
- `config/settings/validation.yaml:1~9` — "이 파일의 값은 constants.py 하드코드와 동일한 기본값… 키 누락 시 Python 기본값으로 안전 fallback".
- `modules/core/constants.py:18~39` `_LazyThreshold` descriptor가 YAML I/O를 모듈 임포트 시점이 아닌 최초 속성 접근 시점으로 지연 + 클래스-레벨 캐시. `constants.py:130~142, 644~645, 827~828`에서 12개 파생 상수에 적용.
- `modules/core/genre_guards/base_guard.py:34~46` `_load_genre_yaml(genre_key)` — 장르별 YAML 실패 시 `{}`.

**(S3) 스키마 자산 존재**
- `contracts/` 11개 `*.schema.json` (총 ~12K LOC): `phase0_design` (345 lines), `bi_wuxguide` (195), `bi_blockguide` (151), `densification_harness`, `material_bundle_summary`, `profile_lock`, `sequential_run_status`, `source_manifest`, `phase0_ready_snapshot`, `audit_status`, + `artifact_contracts.json` (cutover 규칙).
- 모두 `"$schema": "https://json-schema.org/draft/2020-12/schema"` (`contracts/phase0_design.schema.json:2`) — draft 버전 일관.
- `libraries/_core/block_schema.json` — 장르-공통 블록 데이터 모델 정의.
- `docs/implementation/regression-validation-tier-contract-v1.json` — 회귀 검증 계약까지 데이터 파일화.

**(S4) 프롬프트 외부화 + 버전 태깅**
- `config/prompts/` 12개 YAML(총 3,258 lines) + 11개 JSON(총 857 lines).
- `modules/core/prompt_loader.py:120~159` `_load_yaml_metadata` — `_version` 메타데이터 지원(`config/prompts/analyst.yaml:4` `_version: "2026-03-10-opt1"`).
- `prompt_loader.py:242~255` `get_prompt_version` — 미버저닝 YAML은 정렬된 key-value의 MD5 hash(앞 10자)로 자동 버전 생성 → 프롬프트 변동이 추적 가능.
- `prompt_loader.py:214~230` `get_prompt_contract` — 프롬프트도 provenance 계약 반환.
- `prompt_loader.py:42~55` PROMPT_DIR env 오버라이드 + PyInstaller `sys._MEIPASS` 대응.

**(S5) Provider 모드 명시 스위치**
- `.env.example:2~6` — `GEULDOBI_PROVIDER_MODE` 3종(`ambient`/`gemini_direct`/`vertex_ai`) 계약 주석 포함.
- `modules/core/provider_mode.py:36` — env 정규화 헬퍼.
- `modules/core/models_yaml.py` 경로의 `apply_provider_mode_to_models_payload` (`models_config.py:8,70`)로 payload 가공.

**(S6) 패키징 대응 경로 해석**
- `modules/core/models_config.py:47~57` `resolve_models_yaml_path()` — 패키징 모드(`GEULDOBI_ENGINE_ROOT`) / 개발 모드(`__file__` 기반) 이중 해석. PyInstaller 번들 대비.

**(S7) Stage0 핸드오프 수작업 검증기**
- `scripts/stage0_handoff_validator.py:40~45` — 4종 Stage0 아티팩트를 schema와 1:1 매핑, `VALID_PRIMARY_PROFILES` enum(28~37), `OPENING_CONTRACT_BLOCK_START/END` 정수 상한(46~47), `_check_required_fields`(88~105) + `_check_type`(108~124) + 도메인 특화 검사(`_validate_opening_bundle_contract` 등, 175~244)로 스키마 → 런타임 위반을 exit 1 로 변환.
- `contracts/artifact_contracts.json:13~19` `quality_gates` 블록이 각 단계 통과 요건을 텍스트로 명문화.

**(S8) 비밀 관리 표면**
- `.gitignore:11~15` `.env`, `.env.local`, `secrets/*.env` 명시 제외.
- `.env.example:16~22` — ClickUp 토큰은 `secrets/clickup.env` 별도 경로 권고 + `CLICKUP_ENV_FILE` 오버라이드.
- `main_a.py:1236~1253` `_reload_project_environment` — 프로젝트별 `.env`를 동적 주입, 라우터/프로바이더 재초기화.

## 3. 개선 필수 (Critical Issues) — P0

**(C1) 실 API 키가 git 히스토리에 박혀 있음 — 즉시 로테이션 필요**
- `git log --all --diff-filter=A -- .env` → `b69763dc "Upload .env and projects folder as requested"` 커밋이 `.env`를 최초 추가.
- 현재 working tree의 `.env:1~5`에는 실 키 노출(`GOOGLE_API_KEY=AIzaSyC…`, `VERTEX_API_KEY=AQ.Ab8RN6…`, `CLAUDE_API=sk-ant-api03-…`). 파일은 현재 `.gitignore:12`로 보호되지만 **과거 커밋에 그대로 남아 있음**.
- 영향도: 배포 리포 접근자·포크·미러·AI 인덱서에 노출된 것으로 간주해야 함. 프로덕션 등급 평가 블로커.
- 권장 조치: (a) 해당 3개 키 즉시 폐기/로테이션, (b) `git filter-repo`/BFG로 히스토리 정리 검토(공개 저장소면 필수), (c) pre-commit에 `detect-secrets`/`gitleaks` 훅 추가, (d) `.env` 대신 `secrets/*.env` 분할 정책을 코드 상 기본값으로 전환.

**(C2) `jsonschema` 런타임 검증기 부재 — 스키마 11종 중 4종만 수작업 enforce**
- `Grep("import jsonschema|from jsonschema") → No files found` (전 코드베이스).
- `scripts/stage0_handoff_validator.py:108~140`가 `_check_type`으로 top-level type만 수작업 검사 → required·enum·nested object만 지원, oneOf/allOf/pattern/format/additionalProperties/array item type 등은 검증 불가.
- `contracts/bi_blockguide.schema.json`, `bi_wuxguide.schema.json`, `densification_harness.schema.json`, `sequential_run_status.schema.json`, `phase0_design.schema.json`, `profile_lock.schema.json` 은 **런타임 강제 주체가 없음** — "스키마 파일은 있지만 검사는 없다".
- 영향도: 계약 위반이 Stage3/4 런타임까지 누수 → 증거-잔차(evidence residue)로 사후 감지되는 구조.
- 권장 조치: `jsonschema>=4` 도입 + `modules/validation/schema_registry.py` 단일 진입점에서 모든 contracts/를 Draft 2020-12 로 로드하고 Stage 경계에서 enforce.

**(C3) 환경(dev/prod/test) 분리 부재**
- `config/` 하위에 `config/dev/`, `config/prod/`, `config/test/` 없음(`ls config/`: `cash, genres, prompts, settings, smart_retrieval, style_references, terms, treatments` + `settings.json`, `models.yaml`, `system.yaml`).
- 단일 `.env` + `GEULDOBI_PROVIDER_MODE` 하나로 환경을 가름 → 테스트에서 실 API를 때릴 수 있음. `tests/` 내에서 실제 LLM을 호출하는 패턴과 결합하면 위험.
- `config/style_references/investment/style_guide_test.json`(99 lines) — "test" 접미사로 섞여 있어 환경 분리 대신 파일 suffix 네이밍만 존재.
- 권장 조치: `config/profiles/{dev,prod,test}.yaml` 오버레이 도입, `ConfigManager`가 `GEULDOBI_PROFILE` env로 merge. 테스트 시 LLM provider를 강제 fake 로 고정.

**(C4) Provenance YAML과 인라인 기본값 이중 소스 — 드리프트 위험**
- `modules/core/models_config.py:17~38` `DEFAULT_AGENT_MODELS` (20개 에이전트 → 모델) 하드코드.
- `config/models.yaml:36~56` 동일 20개 키를 YAML에 정의.
- `config_manager.py:33~37` `self.settings["models"] = dict(self._yaml_models) if self._yaml_models else dict(self._default_models)` — YAML 있으면 우선, 없으면 인라인.
- 인라인을 직접 import하는 호출자(`modules/core/constants.py:8` `from modules.core.models_config import DEFAULT_FLASH_MODEL, DEFAULT_PRO_MODEL, load_model_name`)는 YAML 업데이트를 놓칠 수 있음.
- 권장 조치: 인라인을 "초기 설치 시 template으로만 사용, 런타임 import 금지" 로 강등하고 `constants.py`에서는 `load_model_name()` 계약 형태만 노출.

**(C5) 장르 라이브러리 이름 비대칭 — wuxia default-fallback trap**
- `modules/domain/agents/analyst.py:1886~1898` genre→filename 맵:
  - `"wuxia": "analyst_libraries.json"` (접미사 없음)
  - 나머지 8개 장르: `"analyst_libraries_{genre}.json"`
  - `lib_filename = genre_library_map.get(genre, "analyst_libraries.json")` (1898) — **등록되지 않은 장르는 전부 wuxia 라이브러리로 fallback**.
- `ls config/prompts/analyst_libraries*` — 10번째 예상 장르 `analyst_libraries_wuxia.json` 이 **없음**(wuxia가 default이므로).
- 영향도: 새 장르 추가 시 map 등록을 누락하면 "오염 방지가 목적인 장르 시스템"이 조용히 wuxia로 되돌아감 — 장르 순혈주의 가드의 핵심 가정 붕괴.
- 권장 조치: (a) `analyst_libraries.json` → `analyst_libraries_wuxia.json` 으로 리네임, (b) map에 wuxia도 명시 등록, (c) fallback을 `None` → `raise` 로 강제.

## 4. 개선 권장 (Major Issues) — P1

**(M1) `validation.yaml` 중복 키 — 마지막 승리(undefined behavior per YAML spec)**
- `config/settings/validation.yaml:47` `sanitize_max_chars: 3000` + `validation.yaml:59` `sanitize_max_chars: 5000` — 둘 다 `scoring:` 블록 아래.
- PyYAML `safe_load`는 마지막 값을 채택하지만, YAML 1.1 스펙상 동작은 unspecified. 주석 `# [TF7-P2-08] runtime-aligned override` 이 override 의도를 드러냄 → 명시적 override 메커니즘 없이 "주석 + 재정의"로 처리 중.
- 권장 조치: `sanitize_max_chars_base` / `sanitize_max_chars_runtime` 두 키로 분리하거나 코드에서 계산.

**(M2) 파싱 실패 시 silent-empty — 시동 게이트 없음**
- `config_manager.py:110~132` `load_settings` — `yaml.safe_load` 예외 시 `logging.warning` 후 `{}` 반환, 시동 중단 없음.
- `config_manager.py:65~75` `_load_agents_from_yaml` — `except Exception: warn + None`.
- `genre_guards/base_guard.py:40~46` — `except Exception: return {}`.
- 영향도: `validation.yaml` 말뭉치가 손상되어도 서비스는 "하드코딩된 constants 로 살아남지만" 운영자는 한참 뒤에야 알아챔.
- 권장 조치: `main_a.py` 부팅 시 `build_config_authority_summary()`로 핵심 임계값 12개의 `used_fallback=True` 비율을 측정, 임계 초과 시 `raise ConfigBootstrapError`.

**(M3) 계약 스키마 일부가 시한 만료 — 하드코드 만료일**
- `contracts/artifact_contracts.json:4~5` `"grace_period_days": 30, "grace_expiry": "2026-04-11"` — 오늘(2026-04-19) 기준 이미 8일 경과.
- 계약은 "md fallback → (유예 만료) status_missing 처리"로 자동 전환을 예고하지만, 이 날짜는 JSON에 박힌 상수일 뿐 런타임에 감시되는지는 불확실.
- 권장 조치: 날짜 비교 로직을 `modules/core/stage0_handoff.py`에 명시 하거나, 만료된 grace 블록을 스키마에서 제거.

**(M4) Dataset 디렉토리 껍데기만 존재**
- `datasets/p/approved/`, `datasets/p/rejected/`, `datasets/p/training_pairs/` — 모두 `total 0` (빈 디렉토리, 2026-02-19 생성 후 미사용).
- `datasets/test_project/approved/`에 3개 샘플 JSON만 있고 `rejected/`, `training_pairs/`는 없음.
- `ls datasets/`: `p, test_project` 두 개뿐.
- 권장 조치: 사용되지 않으면 `.gitkeep`만 남기고 README로 용도 명시 또는 제거.

**(M5) Deprecated 디렉토리가 정리되지 않음**
- `config/prompts/deprecated/architect_rules.json` (deprecated/writer.json 포함) — 참조하는 모듈 없음.
- `config/prompts/__pycache__/writer_rules.cpython-312.pyc` — `config/prompts/` 에는 `writer_rules.json`만 있는데 pyc가 있다는 건 과거에 `.py`가 있었고 import되었음을 시사. (잔여 바이너리)
- 권장 조치: `deprecated/` 폴더 제거 + `.pyc` 캐시 gitignore 엔트리 추가(`config/**/__pycache__/`).

**(M6) PromptLoader는 custom YAML 파서 사용 — yaml.safe_load 우회**
- `modules/core/prompt_loader.py:71~117` `_load_yaml_file` — `re.compile(r"^([A-Z][A-Z0-9_]+):\s*\|")` 정규식으로 top-level block-literal 키만 파싱.
- 장점: 탭/들여쓰기 예외를 손으로 다룰 수 있음. 단점: YAML alias/anchor, flow style, nested block 등 표준 YAML 기능은 무시됨. 프롬프트가 점차 구조화되면 깨질 여지.
- `prompt_loader.py:120~159` 메타데이터 파서도 별도 regex.
- 권장 조치: 단순 `yaml.safe_load`로 이전하거나, custom 파서에 "지원되지 않는 구문 감지 시 fail-fast" 체크 추가.

**(M7) 대규모 파생 데이터를 소스 트리에 커밋**
- `libraries/_opportunity_db/opportunity_db.json` (4,495 lines), `opportunity_db_backup.json` (4,296 lines), `dependency_graph.json` (413 lines), `build_stats.json` — 모두 "derived" 성격.
- `libraries/재벌물/raw_treatments/*.json` 10개 — 책 1권 분량의 raw treatment들이 소스 트리에 존재.
- 영향도: `git clone` 시 체크아웃 부담, diff noise, LFS 미사용.
- 권장 조치: Git LFS 또는 `datasets/` 이관 + CI에서 빌드하도록 전환.

**(M8) 스타일 레퍼런스 디렉토리 불균형**
- `config/style_references/wuxia/`, `actor/`, `alt_history/`, `fantasy/`, `hunter/` — `.gitkeep`만 존재.
- `config/style_references/investment/` — 실제 레퍼런스 원고 + `style_guide.json` (178 lines) + `style_guide_test.json` (99 lines) 존재.
- 영향도: 장르별 스타일 클로닝 시스템(메모리 "Style Cloning System V61.8" 항목 참조)의 6/9 장르는 실질적으로 비어 있음 → 기능 커버리지 갭.
- 권장 조치: 누락된 장르에 최소 reference 1건씩 채우거나, "stub 장르" 목록 문서화.

**(M9) `config/settings.json` vs `config/settings/` 디렉토리 — 이름 충돌**
- `ls config/`: `settings.json` (파일, 12 lines) + `settings/` (디렉토리, `item_suffixes.yaml`, `validation.yaml`, `stage4_policy_digest.json`).
- `ConfigManager._SETTINGS_DIR = "config/settings"` 와 `_SETTINGS_JSON = "settings.json"` 두 리졸버가 서로 다른 경로를 가리킴(`config_manager.py:62~63`).
- 영향도: 신규 기여자의 혼동 + 편집기 탭 완성 시 오지정 위험.
- 권장 조치: `config/settings.json` → `config/runtime_flags.json` 등으로 리네임.

**(M10) Bible quarantine 디렉토리 + duplicate naming**
- `bible/_quarantine/` — 17개의 격리된 BI JSON. 라이브 `bible/*.json` 13개와 이름 중복(`02_bi_chaebol_allowance_zero.json`이 양쪽에 존재).
- 격리 수명 주기·승격 규칙에 대한 문서 없음(참고: T06/T07에서 교차 감사 필요).
- 권장 조치: `bible/_quarantine/README.md`에 정책 명시.

## 5. 개선 검토 (Minor Issues) — P2

**(m1) `.env` 포맷 불규칙**
- `.env:1` `GOOGLE_API_KEY= AIzaSyC...` (등호 뒤 공백), `.env:2` `VERTEX_API_KEY =AQ.Ab8R...` (등호 앞 공백). `python-dotenv`는 허용하지만 관습 위반.
- 권장 조치: pre-commit에 `.env` 린터(`dotenv-linter`) 추가.

**(m2) YAML 주석에 날짜·티켓 ID가 많아 SSOT 증거로도 쓰이고 있음**
- `validation.yaml` 전반의 `# [TF-26]`, `# [1M-CTX-P0]`, `# [TF7-P2-08]` 주석 — 설계 히스토리를 YAML에 기록 중.
- 장점: 변경 사유 추적. 단점: YAML이 "설정"이 아닌 "changelog 유사물"로 비대해짐.
- 권장 조치: 큰 변경은 `docs/implementation/validation-yaml-changelog.md`로 이관.

**(m3) 한글 경로**
- `libraries/재벌물/`, `bible/기록/` — 한글 디렉토리명이 다수. Windows UTF-8 autorun 설정이 전제되어야 동작(MEMORY.md 언급).
- 권장 조치: 영문 키(`chaebol/`) + 한글 표시명 메타데이터 분리 검토.

**(m4) `config/treatments/wuxia/test.txt`**
- 1개 파일만 존재(`content: ?`). 장르 treatment 시드 vs 테스트 아티팩트 경계 불분명.

**(m5) `tone_presets.json` (9 lines), `protagonist_background_2006_2018.json` (20 lines)**
- 매우 작고 단발성. 사용처 grep 결과 없음 → dead config 의심.

**(m6) `contracts/audit_status.schema.json` (44 lines)**
- 가장 작은 스키마. `required` 최소 필드만 있고 enum/pattern 없음 → 느슨한 계약.

**(m7) `_opportunity_db/opportunity_db_backup.json` 이 backup이 아님**
- `opportunity_db.json`과 199 line 차이(4495 vs 4296) — 단순 백업이 아니라 분기된 파일. 어느 쪽이 권위인지 불명.

## 6. 수치 지표 (Metrics)

| 항목 | 수치 | 근거 |
|------|------|------|
| `config/` 하 YAML | 23개 | `find config -name "*.yaml"` |
| `config/` 하 JSON | 27개 | `find config -name "*.json"` |
| `contracts/` 스키마 JSON | 11개 | `ls contracts/*.json`, `*.schema.json` 10 + `artifact_contracts.json` |
| YAML 총 LOC (config/) | 4,533 | `wc -l` 합산 |
| JSON 총 LOC (config/settings·prompts·terms 등) | ~12,148 | `wc -l` 합산 |
| `jsonschema` import | **0** | `Grep("import jsonschema")` |
| 환경 분리 디렉토리(dev/prod/test) | **0** | `ls config/` |
| YAML-fallback을 가진 로더 | 3 | `ConfigManager`, `PromptLoader`, `BaseGuard._load_genre_yaml` |
| provenance-aware 로드 지점 | 2 종 | `get_guard_threshold_contract`, `load_model_contract` |
| 에이전트→모델 매핑 중복 | 2곳 | `models_config.DEFAULT_AGENT_MODELS` + `config/models.yaml` |
| `.env` 노출 히스토리 | 1건 | `git log --all --diff-filter=A -- .env` → `b69763dc` |
| Stage0 검증기가 커버하는 스키마 | 4/11 | `STAGE0_ARTIFACTS` (stage0_handoff_validator.py:40~45) |
| 중복 키 보유 YAML | 1 | `validation.yaml:47 vs :59` `sanitize_max_chars` |
| Deprecated 프롬프트 JSON | 2 | `config/prompts/deprecated/{architect_rules,writer}.json` |
| 빈 dataset 버킷 | 3 | `datasets/p/{approved,rejected,training_pairs}` |
| 장르 YAML LOC 범위 | 82(fantasy) ~ 237(wuxia) | `wc -l config/genres/*.yaml` |

## 7. 성숙도 근거 (Maturity Evidence)

**Production-ready를 가로막는 것 (config 관점):**
- **C1** 실 API 키가 git 히스토리에 커밋된 이력. 회전 + 히스토리 정리 없이는 프로덕션 불가.
- **C3** 환경 분리 부재. 테스트/스테이징/프로덕션 동일 설정 → blast radius 제어 불가.
- **C2** 스키마는 있는데 enforcer 없음 → 계약 위반이 데이터 레이어에서 누수.

**Pre-production은 충족하는 것:**
- 핵심 튜너블이 전부 YAML로 나와 있음 (`validation.yaml` 244 lines + `system.yaml` 47 + `models.yaml` 80 + genre guards 9종).
- 단일 진입점(`ConfigManager`, `PromptLoader`, `BaseGuard._load_genre_yaml`)로 경로 해석 일원화.
- Provenance 계약 반환으로 "어떤 값이 왜 선택됐는지" 추적 가능.
- 11개 `.schema.json` 자산 — 스키마-우선 설계 의도 뚜렷.

**MVP 수준이 아닌 이유:**
- 장르 추가 시 YAML SSOT가 실제로 하드코드를 대체해 온 이력(MEMORY.md 16-step checklist + `base_guard.py:34` 메커니즘)이 있음.
- Stage0 핸드오프가 JSON-only cutover 를 이미 단행(`artifact_contracts.json:4` `cutover_date: 2026-03-12`).
- 패키징(PyInstaller) 대응 경로 리졸버(`models_config.py:47` `GEULDOBI_ENGINE_ROOT`)와 프로젝트별 `.env` 재주입(`main_a.py:1236~1253`)이 이미 구현됨.

## 8. 권장 로드맵 (Recommendations)

**P0 — 1주 내**
1. **시크릿 비상조치**: 현 `.env`의 3개 키(`GOOGLE_API_KEY`, `VERTEX_API_KEY`, `CLAUDE_API`) 즉시 폐기·재발급. 공개 저장소라면 `git filter-repo`로 히스토리 rewrite. pre-commit에 `gitleaks` 도입. (C1)
2. **`jsonschema` 도입 + Stage0 검증기 통합**: `requirements.txt`에 `jsonschema>=4.21` 추가, `modules/validation/schema_registry.py` 신설, `contracts/*.schema.json` 11개를 Draft 2020-12 로 로드, Stage0/2/3/4 경계에서 `validate()` 호출. (C2)
3. **환경 프로파일 도입**: `config/profiles/{dev,prod,test}.yaml` + `GEULDOBI_PROFILE` env 읽어 merge하는 layer를 `ConfigManager`에 추가. 테스트는 fake provider 강제. (C3)
4. **`analyst_libraries.json` → `analyst_libraries_wuxia.json` 리네임**: fallback 제거, `raise ValueError(f"no library for genre {genre}")` 로 변경. (C5)

**P1 — 1개월 내**
5. 인라인 `DEFAULT_AGENT_MODELS` 를 "installer seed"로 강등하고 런타임 import 차단 (lint 규칙) — C4.
6. 시동 시 `build_config_authority_summary()` 검사 → 핵심 임계값 중 `used_fallback=True` 비율이 10% 초과면 `ConfigBootstrapError` 발생 (M2).
7. `validation.yaml` 중복 키(`sanitize_max_chars`) 해소 + YAML changelog 외부화 (M1, m2).
8. `artifact_contracts.json` 의 grace 블록 제거, `stage0_handoff.py` 에 날짜 비교 로직 추가 (M3).
9. `libraries/_opportunity_db/*.json` 대형 파생 데이터 Git LFS 이관 또는 CI 재생성으로 전환 (M7).
10. `PromptLoader` 의 custom YAML 파서를 `yaml.safe_load` 기반으로 재작성 (M6).

**P2 — 분기 내**
11. 스타일 레퍼런스 누락 장르(wuxia/actor/alt_history/fantasy/hunter) 채우기 또는 stub 문서화 (M8).
12. `config/settings.json` 리네임 (M9).
13. `config/prompts/deprecated/` 폴더 제거 + `.pyc` gitignore (M5).
14. `bible/_quarantine/` 라이프사이클 문서화 (M10).
15. `tone_presets.json`, `protagonist_background_2006_2018.json` 사용처 재감사 후 제거 또는 문서화 (m5).
16. 한글 경로를 영문 ID + 한글 메타데이터로 분리 (m3).
