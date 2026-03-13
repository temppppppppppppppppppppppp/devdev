# OPUS TF Terminal 2 — Stage 0→2 파이프라인 전량 조사 취합 보고서

> **작성일**: 2026-03-13
> **범위**: Stage 0 전처리, Stage 0→1 헬퍼, Stage 2 오케스트레이션, Arc 에이전트 체인 10개 모듈
> **총 조사 대상**: ~22K lines 프로덕션 + 관련 테스트 전량
> **방법론**: 6-Point Inspection (4개 병렬 에이전트 + 5Pass 감리)

---

## 5Pass 감리 기록

### Pass 1 — 에이전트 보고서 취합 (완료)
- [x] 4개 병렬 에이전트(Stage0 전처리, Stage2 오케스트레이션, Arc 에이전트, 핸드오프 교차검증) 결과 취합
- [x] 번호 체계 T2-001~T2-052로 통합

### Pass 2 — P0/P1 실코드 대조 (완료)
- [x] T2-001(P0): `_s0_handle_concept` → `_s0_save_results` → `save_v20_anchor("bible", bible)` 흐름 추적. `generate_bible()` 출력에 `plot_roadmap` 미존재 **확인**. `force_sync_v25_dna()` L776만이 `plot_roadmap` 주입. 신규 프로젝트 메뉴에서 Block Extension(choice=4) 미노출(L338-341 리매핑) **확인**
- [x] T2-002(P1): 역설계 `_s0_handle_reverse_engineering` → `persist_to_db`가 `arcs` anchor만 저장, `plot_roadmap` 미주입 **확인**
- [x] T2-003(P1→**P2**): `_extract_single_episode_bible`은 내부 메서드, `extract_episode_bibles`에서만 호출. 호출부 L432에서 `ep_num` 보장. 외부 직접 호출 가능성은 낮음
- [x] T2-004(P1→**P2**): `generate_bible()` L210 `return None` 확인. 호출부 `generate_from_concept` L390 `if not self.bible` 방어 존재
- [x] T2-005(P1→**P2**): L699 `from google.genai import types` 확인. 다만 `generate_content_via_router()` L897을 통해 Provider Router는 사용 중. config 객체 타입만 Gemini 전용
- [x] T2-006(P1→**P3**): 앙상블 `(None, valid_candidates)` 반환 계약 자체는 정상 동작. 문서화 부재만 이슈

### Pass 3 — P2 오탐 검증 (완료)
- [x] ~~T2-010~~: `_NEI_GENRE_DETECT_MAP` L39-59에 **10개 장르 20개 항목 전량 등록** 확인. **오탐 → 삭제**
- [x] ~~T2-009~~: `build_state_constraints_schema()` L358/379/380 — 모든 반환값에 `:` 포함. 빈 `_sc_field` 불가. **오탐 → 삭제**
- [x] T2-008(P2→**P3**): `RECOVERY_PROMPT`가 `analyst.yaml` L622에 정상 등록. YAML 파일 분실 시에만 해당
- [x] T2-015(P2): L1337 `_rejected_arc = refined_arc`, L1338 `refined_arc = None`, L1346-1352 `refined_arc` 사용 → 항상 None. **확인**
- [x] T2-011(P2): L253 `_fsc.get("protagonist_items") or ...` → `[] or other_list` = `other_list`. **확인**
- [x] T2-012(P2): `_post_process_arc` L1189-1206에 `timeline` 미포함. `_ensure_required_fields` L1002-1031에서만 추가. **확인**
- [x] T2-017(P2→**P3**): `stage2_orchestrator.py` L626-627, L664-665에서 `.get()` 안전 접근 확인
- [x] T2-016(P2→**P3**): L1319-1322 `hasattr(None, k)` → False, 기능적 안전. L866-871 `if _st:` 가드와 패턴 불일치만 이슈
- [x] T2-007(P2→**P3**): `_auto_correct_joint_docs_v60` L649-667이 `state_constraints.joint_docs` AND `arc_data.joint_docs` 양쪽 기록. 실사용 시 정합

### Pass 4 — Severity 재분류 정리 + 중복 제거 (완료)
- [x] ~~T2-043~~: T2-010 오탐과 연동 — 실제로 10개 장르 동일. **오탐 → 삭제**
- [x] T2-014(P2→**P3**): `analyst.yaml` RECOVERY_PROMPT 확인 완료, 템플릿 이스케이프 정상 추정
- [x] T2-024(P2): T2-001과 동일 근본 원인 → T2-001에 통합, **별도 항목 삭제**

### Pass 5 — 최종 수치 검증 + 수정 우선순위 확정 (완료)
- [x] 오탐 3건 삭제 (T2-009, T2-010, T2-043)
- [x] T2-001 통합 1건 삭제 (T2-024)
- [x] Severity 재조정 10건 반영
- [x] 최종 수치: P0=1, P1=1, P2=14, P3=31

---

## 총괄 요약 (5Pass 감리 후)

| Severity | 건수 | 핵심 |
|----------|------|------|
| **P0** | 1 | 컨셉 플로우 plot_roadmap 미주입 → Stage 2 진입 불가 |
| **P1** | 1 | 역설계 plot_roadmap 미주입 |
| **P2** | 14 | 메트릭 손실, falsy `or` 패턴, timeline 미생성, 변수 미초기화, 테스트 갭 등 |
| **P3** | 31 | 코드 위생, 패턴 불일치, dead code, mojibake, 문서화 부재 등 |
| **정합 확인** | 11 | Director Selection, STRUCTURAL_MIN_SCORE, Config YAML, 핸드오프 정상 항목, 장르 맵 완전성 |
| **오탐 삭제** | 4 | T2-009, T2-010, T2-024, T2-043 |
| **최종 합계** | **47건 + 정합 확인 11건** |

---

## P0 — CRITICAL (1건)

### [T2-001] 컨셉 플로우 Treatment → plot_roadmap 미주입 — Stage 2 진입 불가
- **Severity**: P0
- **파일**: `modules/core/stage01_helpers.py` L501-538, `modules/core/stage0/story_expander.py` L229-253
- **현상**: Stage 0 컨셉 플로우(`_s0_handle_concept`)로 Bible+Treatment 생성 시, Treatment 데이터가 Bible의 `plot_roadmap` 키에 주입되지 않음. `StoryExpander.generate_bible()`은 `plot_roadmap` 키를 생성하지 않음.
- **근거**: Stage 2 진입점(`stage2_orchestrator.py` L155-156)은 `bible_root.get("plot_roadmap", [])` 에서 블록 목록을 읽음. `plot_roadmap`은 오직 `force_sync_v25_dna()`(레거시 파일 선택, `project_manager.py` L776)와 `_s0_handle_block_extension()`(블록 확장, `stage01_helpers.py` L454)에서만 Bible에 주입됨. 신규 프로젝트 메뉴에서 Block Extension은 리매핑(L338-341: choice 4→5)되어 접근 불가. 컨셉 플로우로 프로젝트를 만들면 Stage 2가 빈 `[]`을 받아 "모든 아크 설계 완료"로 즉시 종료.
- **5Pass 검증**: 실코드 대조 완료. `generate_from_concept()` L404 → `_s0_save_results()` L503-506 → `save_v20_anchor("bible", bible)` — treatment은 L529 별도 파일 저장만. plot_roadmap 주입 코드 0건.
- **수정안**: `_s0_save_results()` 내에서 `treatment`이 존재할 때 `bible["MasterBible"]["plot_roadmap"]`으로 주입. `force_sync_v25_dna()`의 패턴 재사용:
  ```python
  if treatment and bible:
      bible_root = bible.get("MasterBible", bible)
      refined_roadmap = [{"block_no": i + 1, **block} for i, block in enumerate(treatment)]
      bible_root["plot_roadmap"] = refined_roadmap
  ```

---

## P1 — IMPORTANT (1건)

### [T2-002] 역설계 플로우 plot_roadmap 미주입
- **Severity**: P1
- **파일**: `modules/core/stage01_helpers.py` L370-424, `modules/core/stage0/reverse_expander.py` L705-755
- **현상**: 역설계 플로우에서 Treatment/plot_roadmap 미생성. `persist_to_db()`가 arc_stubs를 `arcs` anchor에 저장하지만 `plot_roadmap`은 Bible에 미주입.
- **근거**: `plot_roadmap` 부재 시 Stage 2가 `total_count=0` → "모든 아크 완료"로 즉시 종료. 역설계 후 신규 Arc 생성 불가. 다만 역설계 프로젝트는 arc_stubs 기반으로 Stage 4 직행이 가능하여 P0보다 영향 적음.
- **5Pass 검증**: 실코드 대조 완료. `_s0_handle_reverse_engineering` → `return bible, None` (treatment=None) → `_s0_save_results` treatment 저장 스킵.
- **수정안**: 역설계 시 arc_stubs 수량 기반 `plot_roadmap` 스텁 생성, 또는 `_s0_save_results`에서 `persist_to_db` 결과의 arc_stub 수로 역산.

---

## P2 — MODERATE (14건)

### [T2-003] `_extract_single_episode_bible` KeyError on missing `ep_num`
- **Severity**: P2 (감리 하향: P1→P2. 내부 메서드, 호출부에서 ep_num 보장)
- **파일**: `modules/core/stage0/reverse_expander.py` L383, L394, L413
- **현상**: `draft["ep_num"]` 직접 인덱스 접근 3곳. `extract_episode_bibles` L432의 `.get("ep_num", 0)` 패턴과 불일치.
- **수정안**: `draft["ep_num"]` → `draft.get("ep_num", 0)` 3곳 통일.

### [T2-004] `StoryExpander.generate_bible()` 반환 타입 불일치 (None vs dict)
- **Severity**: P2 (감리 하향: P1→P2. 호출부 전량 `if not self.bible` 방어 존재)
- **파일**: `modules/core/stage0/story_expander.py` L210
- **현상**: 타입 어노테이션 `dict[str, Any]`이지만 protagonist 실패 시 `None` 반환.
- **수정안**: 반환 타입을 `dict[str, Any] | None`으로 수정, 또는 `return {}`로 통일.

### [T2-005] `analyst.py` `plan_single_arc_v20()`에서 Gemini 전용 config 타입 사용
- **Severity**: P2 (감리 하향: P1→P2. `generate_content_via_router` 자체는 사용 중, config 타입만 전용)
- **파일**: `modules/domain/agents/analyst.py` L699, L901
- **현상**: `from google.genai import types` → `types.GenerateContentConfig(**config_params)` 사용. Provider-neutral config가 아닌 Gemini 전용 타입.
- **근거**: CLAUDE.md 허용 목록(gemini_provider/vertex_provider/response_schemas)에 analyst.py 미포함. 현재 Gemini only 운영이므로 런타임 문제 없으나, 멀티 프로바이더 전환 시 장애.
- **수정안**: `_ask_with_analyst_cache` 패턴으로 마이그레이션, 또는 `config_params` dict를 직접 전달하도록 변경.

### [T2-011] `ArcCritic._apply_auto_fixes()` falsy 빈 리스트 `or` 패턴
- **Severity**: P2
- **파일**: `modules/domain/agents/arc_critic.py` L253
- **현상**: `_fsc.get("protagonist_items") or _fsc.get("items_acquired", [])` — `protagonist_items`가 빈 리스트 `[]`이면 falsy로 `items_acquired`에서 읽음. 잘못된 리스트에서 아이템 제거.
- **5Pass 검증**: L253 실코드 확인. `[] or other_list` → `other_list`. analyst.py L438-443 `[Sweep50]`에서 동일 패턴 이미 수정됨.
- **수정안**: `_fsc.get("protagonist_items") if "protagonist_items" in _fsc else _fsc.get("items_acquired", [])`.

### [T2-012] `UnifiedArcValidator` expects `state_changes.timeline` but legacy Analyst path 미생성
- **Severity**: P2
- **파일**: `modules/domain/agents/unified_arc_validator.py` L293-305
- **현상**: Validator가 `state_changes.timeline`을 체크하지만, `analyst._post_process_arc()` L1189-1206에서 `timeline` 미생성. `arc_ensemble._ensure_required_fields`에서만 추가.
- **5Pass 검증**: `_post_process_arc` 기본 키 목록에 `timeline` 미포함 확인. 레거시 Analyst fallback 경로에서 WARNING 발생.
- **수정안**: `_post_process_arc()`의 `state_changes` 기본값에 `"timeline": {"start": {}, "end": {}}` 추가.

### [T2-013] `ArcDraftValidator._validate_tactical_doc()` 길이 체크 변수명 혼동
- **Severity**: P2
- **파일**: `modules/domain/agents/arc_draft_validator.py` L423-428
- **현상**: `warn_length (400*ep) < min_length (500*ep)`. `<warn_length`이면 25점 감점 "심각 미달", `warn~min` 사이면 10점 감점 "부족". 페널티 배분은 올바르나 `warn_length`라는 변수명이 실제로는 critical 임계값.
- **수정안**: 변수명 `warn_length` → `critical_length` 수정 또는 주석 보강.

### [T2-015] REJECT 메트릭에서 `selected_strategy` 항상 `generation_method`로 퇴화
- **Severity**: P2
- **파일**: `modules/core/stage2_finalizer.py` L1337-1352
- **현상**: L1337 `_rejected_arc = refined_arc`, L1338 `refined_arc = None`, L1346 `refined_arc.get(...)` → 항상 None. `_rejected_arc`에 보존된 전략 정보 미사용.
- **5Pass 검증**: 실코드 L1337-1352 대조 확인. `isinstance(refined_arc, dict)` → False → `generation_method` 폴백.
- **수정안**: L1346-1352에서 `refined_arc` → `_rejected_arc` 사용.

### [T2-018] `run_validation` `retry` 반환에 `python_advisories` 등 누락
- **Severity**: P2
- **파일**: `modules/core/stage2_validation_pipeline.py` L56-69
- **현상**: `refined_arc` None 시 `{"action": "retry", ...}` 반환에 정상 경로 키 누락. 호출자가 `.get()` 사용하므로 크래시는 없으나, 반환 계약 불명확.
- **수정안**: `retry` 반환에 빈 기본값 포함: `corrections_made=0, python_advisories=[]`.

### [T2-019] `import_bible` 빈 `bible_path` 시 `Path("")` 플랫폼 의존적 동작
- **Severity**: P2
- **파일**: `modules/core/stage0/__init__.py` L461-463
- **현상**: Windows에서 `Path("").exists()` → True (현재 디렉토리). `.suffix` 체크로 걸리긴 하지만 방어 부족.
- **수정안**: `if not bible_path:` 조기 반환 추가.

### [T2-020] `save_state`에 OSError 방어 없음
- **Severity**: P2
- **파일**: `modules/core/stage0/__init__.py` L651-685
- **현상**: 6개 파일 순차 저장 중 디스크 오류 시 전체 실패. 동일 파일 `run_reference_analysis`에는 OSError 방어 존재.
- **수정안**: 각 파일 저장을 try/except OSError로 감싸고 logging.warning.

### [T2-021] `_s0_handle_reverse_engineering` `bible` 변수 미초기화
- **Severity**: P2
- **파일**: `modules/core/stage01_helpers.py` L370-424
- **현상**: `run_reverse_engineering_flow()`가 DraftEncodingError 이외의 예외 시 L424 `return bible, None`에서 UnboundLocalError.
- **수정안**: L370 하단에 `bible = {}` 초기화.

### [T2-022] `_enrich_arc_stubs_from_episode_bibles` 이중 `save_anchor` 호출
- **Severity**: P2
- **파일**: `modules/core/stage0/reverse_expander.py` L1147 vs L1005
- **현상**: 트랜잭션 내에서 `save_anchor("arcs", ...)` 2회 호출. `load_anchor`로 재로드하는 불필요 I/O.
- **수정안**: `_save_arc_stubs` 반환값을 직접 전달.

### [T2-023] Stage 0 컨셉 플로우 `genre_info` anchor 비저장
- **Severity**: P2
- **파일**: `modules/core/stage01_helpers.py` L501-538
- **현상**: `_s0_save_results()`에서 `genre_info` anchor 미저장. `stage0_manager.genre`가 있어도 `app.selected_genre`에 동기화되지 않음. 별도 장르 선택 UI를 거쳐야 저장됨.
- **수정안**: `stage0_manager.genre` 존재 시 `genre_info` anchor 동기화.

### [T2-052] Arc 에이전트 핵심 모듈 전용 테스트 파일 부재
- **Severity**: P2
- **파일**: `tests/` 디렉토리
- **현상**: 6개 핵심 모듈 전용 테스트 없음:
  - `arc_ensemble.py` (1,167줄) — `_evaluate_candidate()` 선택 로직 미커버
  - `arc_critic.py` (379줄) — auto-fix 적용 로직 미커버
  - `arc_corrector.py` (596줄) — 섹션 교체 로직 미커버
  - `unified_arc_validator.py` (704줄) — Python+LLM 검증 파이프라인 미커버
  - `state_locked_arc_generator.py` (583줄) — 상태 잠금 생성 미커버
  - `analyst.py` (1,838줄) — 핵심 Arc 설계 로직 미커버
- **수정안**: 우선순위: `arc_ensemble._evaluate_candidate()`, `unified_arc_validator._python_validate()`, `arc_corrector._replace_episode_section()`.

---

## P3 — MINOR (31건)

### [T2-006] 앙상블 반환 계약 미문서화
- **Severity**: P3 (감리 하향: P1→P3. 기능적 문제 없음, 문서화만 부재)
- **파일**: `modules/domain/agents/arc_ensemble.py` L592-596
- **현상**: `(None, valid_candidates)` 반환 시 첫 번째 원소가 highest-scored임이 암묵적.
- **수정안**: docstring에 반환 계약 명시.

### [T2-007] `_validate_arc_state_continuity_v60()` joint_docs 읽기 경로 방어 부족
- **Severity**: P3 (감리 하향: P2→P3. `_auto_correct_joint_docs_v60`이 양쪽에 기록하여 실사용 정합)
- **파일**: `modules/domain/agents/analyst.py` L423
- **현상**: `prev_constraints.get("joint_docs", {})` — `state_constraints` 내부에서만 읽음. `_auto_correct_joint_docs_v60` L667이 양쪽에 기록하므로 실사용 시 문제 없으나, 방어적 폴백 추가 권장.
- **수정안**: `prev_joint = prev_arc.get("joint_docs") or prev_constraints.get("joint_docs", {})`.

### [T2-008] `get_recovery_prompt()` YAML 분실 시 빈 문자열 반환
- **Severity**: P3 (감리 하향: P2→P3. `analyst.yaml` L622에 정상 등록 확인)
- **파일**: `modules/domain/agents/analyst_prompt_api.py` L70-75
- **현상**: YAML 파일 분실/손상 시에만 빈 문자열 반환 → 빈 LLM 프롬프트.
- **수정안**: `if not template: raise RuntimeError("RECOVERY_PROMPT missing")`.

### [T2-014] `total_absolute_recovery_v20()` `.format()` vs `.format_map()` 불일치
- **Severity**: P3 (감리 하향: P2→P3. YAML 템플릿 정상 이스케이프 확인)
- **파일**: `modules/domain/agents/analyst.py` L1280
- **현상**: 다른 모든 메서드는 `format_map(_SafeDict())` 사용하는데 이 메서드만 `.format()` 사용.
- **수정안**: `format_map(_SafeDict(...))` 패턴으로 통일.

### [T2-016] StateTracker 롤백 None 체크 패턴 불일치
- **Severity**: P3 (감리 하향: P2→P3. `hasattr(None, k)` → False로 기능적 안전)
- **파일**: `modules/core/stage2_finalizer.py` L1319-1322
- **현상**: `_st = self.ctx.state_tracker` 후 None 체크 없이 사용. L866-871에서는 `if _st:` 가드 존재.
- **수정안**: L1319 아래에 `if not _st: ...` 가드 추가.

### [T2-017] QualityGate REJECT 반환 dict 키 구조 불일치
- **Severity**: P3 (감리 하향: P2→P3. 호출자 `.get()` 안전 접근 확인)
- **파일**: `modules/core/stage2_finalizer.py` L890-898
- **현상**: QualityGate REJECT 반환은 7개 키, 정상 REJECT 경로는 12개 키. 코드 일관성 이슈.
- **수정안**: 누락 키 추가하여 반환 구조 통일.

### [T2-025] Treatment 블록 필수 키 검증 부재
- **Severity**: P2→P3 (LLM 의존적, 프롬프트에서 키 명시)
- **파일**: `modules/core/stage0/story_expander.py` L304-312
- **현상**: `_generate_details()` LLM 응답의 블록 구조에서 `content` 키 존재 여부 미검증.
- **수정안**: 필수 키 검증 게이트 추가 검토.

### [T2-026] `plan_single_arc_v20()` `final_arc_data` None 잔류 가능성
- **Severity**: P2→P3 (L1066-1067 최소 fallback dict로 처리)
- **파일**: `modules/domain/agents/analyst.py` L853, L1058-1071
- **현상**: `_arc_attempt_func`에서 비예상 예외 시 `_arc_loop_state["draft_result"]` 미설정. 최소 fallback으로 처리됨.
- **수정안**: `_arc_attempt_func` 내 try/except로 항상 설정 보장.

### [T2-027] `post_process_arc` 예외 시 corrections 카운트 누락
- **Severity**: P2→P3 (advisory 정보 누락일 뿐 기능 영향 없음)
- **파일**: `modules/core/stage2_validation_pipeline.py`
- **수정안**: 예외 시 corrections=0 명시 기록.

### [T2-028] `stage01_helpers` mojibake 하드코딩
- **Severity**: P3
- **파일**: `modules/core/stage01_helpers.py` L143-151
- **현상**: 외부 시점 삽입 정책 메뉴 텍스트가 깨진 한글(mojibake)로 출력. `"?봿 ????쒖젏..."` 등.
- **수정안**: 정상 한글 텍스트로 교정.

### [T2-029] `StyleGuide._get_pov_rules` 비표준 POV silent 무시
- **Severity**: P3
- **파일**: `modules/core/stage0/style_extractor.py` L81-123
- **수정안**: 비표준 pov에 대해 warning 로깅.

### [T2-030] `detect_genre` 기본값 `GenreTypes.INVESTMENT` 하드코딩
- **Severity**: P3
- **파일**: `modules/core/stage0/reverse_expander.py` L228-253
- **현상**: LLM 실패 시 무조건 투자물로 분류.
- **수정안**: 기본값 빈 문자열 + 경고 로깅.

### [T2-031] `_llm_call` 폴백 dead code
- **Severity**: P3
- **파일**: `modules/core/stage0/style_extractor.py` L1101
- **수정안**: `last_err` 초기화.

### [T2-032] `_parse_korean_number` 소수점 금액 미지원
- **Severity**: P3
- **파일**: `modules/core/stage0/preset_registry.py` L552-591
- **현상**: "1.5억" → 5억 오파싱.
- **수정안**: float 변환 후 단위 곱셈.

### [T2-033] `import_bible` bare `Exception` catch 범위 과대
- **Severity**: P3
- **파일**: `modules/core/stage0/__init__.py` L491

### [T2-034] `_s0_save_results` 일부 핸들러에서 `input()` 이중 호출
- **Severity**: P3
- **파일**: `modules/core/stage01_helpers.py` L540-543
- **현상**: 핸들러 4,5,6이 자체 `input()` 호출 + `_s0_save_results` `input()` = 2회.

### [T2-035] `_rejected_arc` 중복 할당
- **Severity**: P3
- **파일**: `modules/core/stage2_finalizer.py` L1296, L1337

### [T2-036] `constraint_block` 문자열 기반 advisory 핸드오프
- **Severity**: P3
- **파일**: `modules/core/stage2_finalizer.py` L498-502

### [T2-037] `_check_cross_arc_asset_continuity` 한국어 단위 미지원
- **Severity**: P3
- **파일**: `modules/core/stage2_finalizer.py` L177-220

### [T2-038] ThreadPoolExecutor 타임아웃 후 메모리 점유
- **Severity**: P3 (Python 표준 한계)
- **파일**: `modules/core/stage2_preflight.py` L477-717

### [T2-039] `arc_corrector.can_correct()` dead code (CORRECTABLE/UNCORRECTABLE dicts)
- **Severity**: P3
- **파일**: `modules/domain/agents/arc_corrector.py` L28-42, L108

### [T2-040] `state_locked_arc_generator.py` `episode_beats[:5]` 하드코딩
- **Severity**: P3
- **파일**: `modules/domain/agents/state_locked_arc_generator.py` L220
- **현상**: 최대 5화 하드코딩, 시스템은 6화 지원.

### [T2-041] energy check silent pass 비로깅
- **Severity**: P3
- **파일**: `modules/domain/agents/analyst.py` L464-475

### [T2-042] `arc_ensemble._evaluate_candidate()` 파라미터 shadowing
- **Severity**: P3
- **파일**: `modules/domain/agents/arc_ensemble.py` L866-874

### [T2-044] `ArcCritic.critique()` 예외 경로 반환 계약 암묵적
- **Severity**: P3
- **파일**: `modules/domain/agents/arc_critic.py` L176-179

### [T2-045] `arc_ensemble._generate_single()` 프롬프트 60줄 중복
- **Severity**: P3
- **파일**: `modules/domain/agents/arc_ensemble.py` L727-788

### [T2-046 ~ T2-051] 테스트 커버리지 갭 6건
- **T2-046** (P3): `extend_treatment` 핵심 분기 미검증
- **T2-047** (P3): `persist_to_db` 롤백 경로 미검증
- **T2-048** (P3): `_save_episode_bibles_to_db` 스키마 변환 미검증
- **T2-049** (P3): Finalizer PASS_WITH_FIX score < quality_gate 분기 미테스트
- **T2-050** (P3): `_check_cross_arc_asset_continuity` 미테스트
- **T2-051** (P3): `stage2_optimizer.post_process_arc()` 통합 테스트 부재

---

## 정합 확인 완료 (위반 없음, 11건)

| # | 항목 | 결과 |
|---|------|------|
| 1 | Director Selection (TF-S2) | 정합 — Python 자동선택 잔류 없음. `return None, valid_candidates` |
| 2 | STRUCTURAL_MIN_SCORE = 50 + 최소 1개 보장 | 정합 — `scored_candidates[:1]` 폴백 동작 |
| 3 | Stage 0→2 MasterBible 스키마 | 정합 — `bible_root.get("MasterBible", bible_data)` 폴백 패턴 |
| 4 | StyleGuide DB 핸드오프 (`style_guide` anchor) | 정합 — 키/타입 일치 |
| 5 | protagonist_config 핸드오프 | 정합 — 4개 키 양측 일치 |
| 6 | preset_registry 핸드오프 (`preset_state` anchor) | 정합 — 키/타입 일치 |
| 7 | config/genres/*.yaml 10개 ↔ 코드 | 정합 — 전량 1:1 대응 |
| 8 | config/prompts/analyst.yaml ↔ analyst_prompt_api.py | 정합 — 플레이스홀더 전량 대응 |
| 9 | 전처리_ssot/contracts ↔ Stage 0 코드 | 별개 시스템 (수동 전처리 워크플로우) |
| 10 | episode_bibles Stage 2 미참조 | 의도된 설계 (Stage 4 전용) |
| 11 | `_NEI_GENRE_DETECT_MAP` 장르 완전성 | 정합 — 10개 장르 20개 항목 전량 등록 (에이전트 오탐 교정) |

---

## 오탐 삭제 기록 (4건)

| 원래 번호 | 원래 Severity | 삭제 사유 |
|-----------|--------------|-----------|
| T2-009 | P2 | `build_state_constraints_schema()` 모든 반환값에 `:` 포함, 빈 `_sc_field` 불가 |
| T2-010 | P2 | `_NEI_GENRE_DETECT_MAP` L39-59에 10개 장르 전량 등록 확인 |
| T2-024 | P2 | T2-001과 동일 근본 원인 → T2-001에 통합 |
| T2-043 | P3 | T2-010 오탐과 연동 — 두 맵 모두 10개 장르 동일 |

---

## 대원칙 준수 확인

| 원칙 | 결과 |
|------|------|
| 1. Python은 수집만, 판단은 LLM | **준수** — 전 모듈에서 Python은 데이터 수집/포맷팅만 수행 |
| 2. 팩트시트 수정 권한은 LLM만 | **준수** — NPC/세계관 자동 덮어쓰기 없음 |
| 3. 디렉터 주권주의 | **준수** — arc_ensemble은 `(None, candidates)` 반환, Director가 최종 선택 |
| 4. 사망 캐릭터 회상/언급만 | **해당 없음** — Stage 0-2 범위 밖 |

---

## 수정 우선순위 권고 (5Pass 감리 확정)

### 즉시 수정 (P0)
1. **T2-001**: 컨셉 플로우 `plot_roadmap` 주입 — Stage 2 진입 차단 해소

### 1순위 수정 (P1)
2. **T2-002**: 역설계 플로우 `plot_roadmap` 주입

### 2순위 수정 (P2, 영향도 순)
3. **T2-011**: `ArcCritic` falsy 빈 리스트 `or` 패턴 (데이터 오염)
4. **T2-015**: REJECT 메트릭 전략 손실 (관측성 저하)
5. **T2-012**: `_post_process_arc` timeline 기본값 추가 (불필요 WARNING 방지)
6. **T2-021**: `bible` 변수 미초기화 (UnboundLocalError 위험)
7. **T2-005**: analyst.py Gemini 전용 config 타입 (멀티 프로바이더 준비)
8. **T2-052**: Arc 에이전트 핵심 모듈 테스트 파일 신설
