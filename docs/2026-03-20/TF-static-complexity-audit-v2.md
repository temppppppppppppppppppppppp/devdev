# TF — 글도비 정적 복잡도 전수감리 v2 (Current-State Corrected)

**일자**: 2026-03-20  
**상태**: current-state corrected after adversarial re-audit  
**기준 원칙**: 한 문서 안에서 서로 다른 범위를 섞지 않는다. 범위가 다르면 섹션 단위로 명시한다.

Commit State:
- Baseline Commit: `9a4f46a8f8193c42e236cf181e0151b26a3167b4`
- Baseline Dirty Summary: `dirty: 9 tracked, 4 untracked; hotspots: config/settings/validation.yaml, modules/core/stage4_orchestrator.py, modules/validation/scoring_validator.py, tests/test_stage4_context.py, tests/test_stage4_orchestrator.py, tests/test_validation.py, docs/temp/queue-state.json, docs/2026-03-20/*.md`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

---

## 1. Scope Matrix

| Scope ID | 범위 | 포함 | 제외 | 용도 |
| --- | --- | --- | --- | --- |
| **S1** | 구조/규모용 프로덕션 코드 범위 | root `*.py` + `modules/**/*.py` + `scripts/**/*.py` | `tests/`, `docs/`, `projects/`, `geuldobi-desktop/`, `lite_mode/`, `test_mode/`, `tools/`, `tools2/`, `spikes/`, `build/`, `dist/`, `python-embed/`, `logs/`, `test_material/` | LOC, 파일 수, 클래스/함수 수, 대형 파일, 장함수, 외부 의존 |
| **S2** | 런타임 코어 범위 | `modules/**/*.py` | root `*.py`, `scripts/` | `.get()` 의존, 예외 처리, 분기/중첩, fan-in/out, 전역 가변 상태 |
| **S3** | 설정/프롬프트 범위 | `config/**/*.{json,yaml,yml}` | `laws/` 없음 | 설정 표면적, 프롬프트 파일 수 |
| **S4** | DB substrate 범위 | `modules/core/db_manager.py`, `modules/core/vec_memory.py` | 기타 SQL 문자열 산포 파일 | 테이블/DDL/DML 표면적 |

핵심 정정:
- 이전 v2는 상단 총괄은 사실상 `S1`, `.get()/예외/분기/전역상태`는 `S2`, DB는 거의 `S4`, 설정은 오래된 `config + laws` 가정이 섞여 있었다.
- 이번 판본은 섹션마다 scope를 고정했다.

---

## 2. 방법론

- AST 파싱은 `utf-8-sig`로 수행했다. BOM이 있는 파일도 같은 규칙으로 읽는다.
- 함수 길이는 `end_lineno - lineno + 1`의 inclusive LOC로 계산했다.
- `God Object`는 **direct class methods only** 기준이다. nested closure는 메서드로 세지 않는다.
- `fan-in`은 같은 scope 내부에서 해당 모듈을 import하는 **고유 파일 수**다.
- `fan-out`은 파일 최상단 `import`/`from ... import ...` 라인 수다.
- `전역 가변 상태`는 모듈 레벨의 `dict/list/set` literal 할당만 센다.
- DB 정규식 수치는 `S4`에 한정했다. 전체 코드베이스 regex는 주석/문자열 잡음이 커서 substrate-only가 더 재현 가능하다.

---

## 3. S1 구조 스코어카드

### 3.1 총괄

| 차원 | 측정값 | 비고 |
| --- | --- | --- |
| 파일 수 | **295** | root `8` + `modules 248` + `scripts 39` |
| 총 LOC | **168,905** | 현재 dirty worktree 기준 |
| 클래스 수 | **429** | `ast.ClassDef` |
| 함수/메서드 AST 노드 합계 | **4,594** | top-level 함수 `986` + direct methods `3,465` + nested-in-class `109` + nested-outside-class `34` |
| direct-method God Object (50+) | **7개** | nested closure 미포함 |
| 100줄+ 함수/메서드 | **244개** | inclusive LOC |
| 500줄+ 함수/메서드 | **8개** | 장함수 임계치 초과 |
| 최장 단일 메서드 | **1,149줄** | `Stage4InterviewRound.run` |
| 최대 중첩 깊이 | **14** | `main_a.py` 포함 S1 기준 |
| 순환 의존 | **8쌍** | 전부 구조적 쌍, 런타임 import-time 순환으로 단정하지 않음 |
| 외부 의존 | **14 패키지** | `PIL`, `anthropic`, `dotenv`, `fastapi`, `fpdf`, `google`, `nest_asyncio`, `numpy`, `openai`, `pydantic`, `requests`, `rich`, `sqlite_vec`, `yaml` |

### 3.2 대형 파일 Top 20

| 순위 | 파일 | LOC |
| --- | --- | --- |
| 1 | `modules/core/stage4_interview_round.py` | 6,205 |
| 2 | `main_a.py` | 4,891 |
| 3 | `modules/core/db_manager.py` | 3,986 |
| 4 | `modules/core/stage4_context_builder.py` | 3,109 |
| 5 | `modules/core/stage2_finalizer.py` | 2,363 |
| 6 | `modules/api/bridge_server.py` | 2,320 |
| 7 | `modules/core/stage3_orchestrator.py` | 2,257 |
| 8 | `modules/domain/agents/base_agent.py` | 2,213 |
| 9 | `modules/domain/agents/state_tracker_npc.py` | 2,204 |
| 10 | `modules/domain/agents/four_phase_arc_generator.py` | 2,197 |
| 11 | `scripts/investment_corpus_support.py` | 2,099 |
| 12 | `modules/domain/agents/chief_writer.py` | 2,015 |
| 13 | `modules/core/stage4_orchestrator.py` | 1,996 |
| 14 | `modules/core/failure_analyzer.py` | 1,962 |
| 15 | `modules/domain/agents/director_ensemble.py` | 1,952 |
| 16 | `modules/core/stage4_post_processor.py` | 1,874 |
| 17 | `modules/domain/agents/analyst.py` | 1,849 |
| 18 | `modules/core/stage2_preflight.py` | 1,801 |
| 19 | `modules/validation/validation_orchestrator.py` | 1,702 |
| 20 | `modules/domain/agents/state_tracker.py` | 1,668 |

### 3.3 direct-method God Object

| 클래스 | 메서드 수 | LOC | 메모 |
| --- | --- | --- | --- |
| `SovereignApp` | 126 | 4,533 | root 진입점 |
| `DBManager` | 122 | 3,937 | DB 영속/DDL/DML 집중 |
| `StateTracker` | 109 | 1,543 | 상태 관리 집약 |
| `Stage4InterviewRound` | 94 | 6,148 | Stage 4 실행 엔진 |
| `DBRepositoryProtocol` | 59 | 183 | Protocol |
| `ChiefWriter` | 57 | 1,960 | 원고 생성 |
| `StateServiceProtocol` | 51 | 91 | Protocol |

정정 포인트:
- `Stage4ContextBuilder`는 **direct-method 기준 47**이라 50+ God Object에 포함되지 않는다.
- 예전 v2의 `8개`는 nested closure까지 메서드로 세었을 때만 성립한다.

### 3.4 장함수 분포

| 구간 | 건수 |
| --- | --- |
| 500줄+ | 8 |
| 300-499줄 | 20 |
| 200-299줄 | 38 |
| 100-199줄 | 178 |
| 100줄+ 합계 | **244** |

### 3.5 장함수 Top 20

| 순위 | 함수 | LOC | 위치 |
| --- | --- | --- | --- |
| 1 | `Stage4InterviewRound.run` | 1,149 | `L1864-L3012` |
| 2 | `ThreePhaseBlueprintGenerator.generate` | 739 | `L111-L849` |
| 3 | `DBManager._boot_db` | 695 | `L229-L923` |
| 4 | `DirectorEnsembleSelector.select_and_judge_ensemble` | 660 | `L1224-L1883` |
| 5 | `Stage2PreflightAnalysis._preflight_enrichment` | 656 | `L1146-L1801` |
| 6 | `FailureAnalyzer.sink_alignment_summary` | 628 | `L379-L1006` |
| 7 | `FourPhaseArcGenerator.generate` | 620 | `L578-L1197` |
| 8 | `WorldStateManager.update_from_state_changes` | 596 | `L158-L753` |
| 9 | `Stage4InterviewRound._run_pre_director_validation` | 493 | `L3014-L3506` |
| 10 | `Stage4Orchestrator._handle_round_outcome` | 490 | `L968-L1457` |
| 11 | `Stage4PostProcessor._collect_manager_and_build_delta` | 434 | `L1043-L1476` |
| 12 | `SovereignApp._one_stop_pipeline_frontier_lag` | 418 | `L4208-L4625` |
| 13 | `ChiefWriterContextBuilder.build_common_context` | 413 | `L111-L523` |
| 14 | `Analyst.plan_single_arc_v20` | 409 | `L663-L1071` |
| 15 | `DirectorQualityAuditor.audit_manuscript` | 408 | `L399-L806` |
| 16 | `Stage3Orchestrator._generate_blueprint` | 398 | `L1013-L1410` |
| 17 | `FourPhaseArcGenerator._generate_prev_context` | 363 | `L1736-L2098` |
| 18 | `ValidationOrchestrator._validate_sync_body` | 359 | `L372-L730` |
| 19 | `Stage2Orchestrator.stage_2_arcs_async_logic` | 358 | `L798-L1155` |
| 20 | `convert` | 356 | `md2pdf.py:L10-L365` |

---

## 4. S2 런타임 코어 복잡도

### 4.1 총괄

| 차원 | 측정값 | 비고 |
| --- | --- | --- |
| 파일 수 | **248** | `modules/**/*.py` |
| 총 LOC | **148,058** | `modules/__init__.py` 0줄 포함 |
| 클래스 수 | **401** | 런타임 코어 한정 |
| 함수/메서드 AST 노드 합계 | **3,942** | top-level `508`, direct methods `3,321` |
| TypedDict | **11** | 아직 낮은 편 |
| `.get()` 호출 | **8,414** | dict 의존도 높음 |
| 분기 합계 | **15,768** | `if 11,601`, `for 2,564`, `while 35`, `try 1,568` |
| except 핸들러 | **1,574** | generic `1,024` = **65.1%** |
| silent pass | **133** | `8.5%` |
| 전역 가변 상태 선언 | **87** | lower-case `8`, 전부 `__all__` |
| 최대 중첩 깊이 | **11** | `main_a.py` 제외한 코어 기준 |
| 깊이 7+ 위치 | **129곳** | 인지 부하 높은 영역 |

### 4.2 분기 밀도 Top 10

| 파일 | 밀도 | 분기 수 | LOC | if | for | try |
| --- | --- | --- | --- | --- | --- | --- |
| `inventory_state.py` | 23.4% | 29 | 124 | 24 | 5 | 0 |
| `blueprint_constraint_compiler.py` | 21.0% | 127 | 605 | 108 | 18 | 1 |
| `world_state.py` | 20.6% | 275 | 1,338 | 202 | 40 | 33 |
| `stage0_handoff.py` | 20.5% | 38 | 185 | 27 | 10 | 1 |
| `stage4_context_builder.py` | **19.6%** | **609** | **3,109** | **441** | **106** | **62** |
| `info_paradox_checker.py` | 18.9% | 49 | 259 | 39 | 6 | 4 |
| `fact_ledger.py` | 18.8% | 160 | 852 | 115 | 37 | 8 |
| `writer_prompt_builders.py` | 18.3% | 43 | 235 | 28 | 8 | 7 |
| `narrative_context_formatter.py` | 18.0% | 43 | 239 | 39 | 4 | 0 |
| `writing_directive_generator.py` | 17.6% | 37 | 210 | 29 | 3 | 5 |

### 4.3 중첩 깊이 Top 10

| 파일 | 최대 깊이 | 깊이 7+ 위치 |
| --- | --- | --- |
| `scoring_validator.py` | 11 | 14 |
| `error_helper.py` | 11 | 5 |
| `martial_manager.py` | 10 | 8 |
| `genre_guards/__init__.py` | 10 | 4 |
| `genre_hud_manager.py` | 10 | 4 |
| `stage2_preflight.py` | 9 | 18 |
| `stage4_context_builder.py` | 9 | 8 |
| `stage4_interview_round.py` | 8 | 10 |
| `project_manager.py` | 8 | 9 |
| `stage4_orchestrator.py` | 8 | 9 |

### 4.4 결합도

Fan-In Top 10:

| 모듈 | Fan-In |
| --- | --- |
| `core.constants` | 80 |
| `core.prompt_loader` | 30 |
| `validation.threshold_helper` | 30 |
| `domain.agents.base_agent` | 26 |
| `core.llm_generate` | 19 |
| `core.genre_schema_builder` | 13 |
| `core.genre_guards.base_guard` | 12 |
| `core.project_support` | 11 |
| `core.tactical_utils` | 11 |
| `core.soft_failure` | 7 |

Fan-Out Top 10:

| 파일 | import 라인 수 |
| --- | --- |
| `bridge_server.py` | 31 |
| `process_runner.py` | 16 |
| `base_agent.py` | 16 |
| `stage4_context_builder.py` | 15 |
| `stage4_orchestrator.py` | 15 |
| `stage3_orchestrator.py` | 14 |
| `four_phase_arc_generator.py` | 14 |
| `validation_orchestrator.py` | 14 |
| `genre_guards/__init__.py` | 13 |
| `stage0/__init__.py` | 13 |

### 4.5 순환 의존 8쌍

| 부모 | 자식 |
| --- | --- |
| `pre_director_checklist` | `pre_director_manuscript_checker` |
| `pre_director_checklist` | `pre_director_narrative_checker` |
| `pre_director_checklist` | `pre_director_style_checker` |
| `relationship_tracker` | `relationship_tracker_factions` |
| `relationship_tracker` | `relationship_tracker_npc` |
| `blocking_validator` | `blocking_validator_consistency_checks` |
| `blocking_validator` | `blocking_validator_entity_checks` |
| `blocking_validator` | `blocking_validator_scene_checks` |

수동 확인 결과:
- 모두 `TYPE_CHECKING` 역참조 또는 lazy import 패턴이 섞인 구조적 쌍이다.
- 정적 도구 경고 가능성은 있으나, 곧바로 import-time 순환 장애로 단정할 수는 없다.

### 4.6 코드 중복

| 항목 | 값 |
| --- | --- |
| `_fit_prompt_text` 정의 수 | **17** |
| `validate` 정의 수 | 17 |
| `generate` 정의 수 | 10 |

해석:
- `_fit_prompt_text`만이 확실한 복제 후보다.
- `validate`, `generate`, 장르 가드 계열 getter는 다형성 섞임이 크므로 이름 중복만으로 중복 코드라고 단정하지 않는다.

---

## 5. S3 설정/프롬프트 표면적

| 항목 | 파일 수 | LOC | 메모 |
| --- | --- | --- | --- |
| YAML | 24 | 4,463 | `config/` 전체 |
| JSON | 20 | 1,291 | `config/` 전체 |
| 합계 | **44** | **5,754** | `laws/` 디렉터리 없음 |
| `config/prompts/` 전체 파일 | **23** | — | JSON 포함 |
| `config/prompts/` YAML | **9** | **2,692** | YAML만 별도 집계 |

프롬프트 참조 Python 파일:
- `S1` 기준: **147파일**
- `S2` 기준: **134파일**

정정 포인트:
- 이전 v2의 `65파일 / 37,729줄`, `프롬프트 YAML 23파일 / 3,661줄`은 현재 워크스페이스 기준으로 재현되지 않는다.
- 이번 판본은 `config/` 현존 파일만 집계했다.

---

## 6. S4 DB Substrate 복잡도

| 파일 | CREATE TABLE | ALTER TABLE | SELECT | INSERT | UPDATE | DELETE | SQL 합계 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `db_manager.py` | 33 | 17 | 96 | 39 | 15 | 24 | 174 |
| `vec_memory.py` | 5 | 0 | 18 | 13 | 4 | 9 | 44 |
| **합계** | **38** | **17** | **114** | **52** | **19** | **33** | **218** |

해석:
- 이전 v2의 `DB 테이블 33 / SQL 174`는 사실상 `db_manager.py` 단독 집계였다.
- DB substrate 전체를 보면 `vec_memory.py`의 DDL/DML 표면적도 별도로 존재한다.

---

## 7. Correction Ledger

| 항목 | 이전 v2 | 현재 교정값 | 비고 |
| --- | --- | --- | --- |
| 총 LOC | 168,877 | **168,905** | S1 현재 dirty worktree 기준 |
| 클래스 수 | 425 | **429** | S1 |
| 함수+메서드 수 | 4,555 | **4,594** | S1, AST node 합계 |
| God Object | 8 | **7** | direct-method rule |
| `Stage4ContextBuilder` 메서드 수 | 54 취급 | **47 direct** | nested closure 제외 |
| `Stage4Orchestrator._handle_round_outcome` | 490줄이지만 라인 범위 stale | **L968-L1457** | inclusive 유지 |
| 설정 표면적 | 65 / 37,729 | **44 / 5,754** | `laws/` 없음 |
| 프롬프트 YAML | 23 / 3,661 | **9 / 2,692** | `config/prompts/` YAML만 |
| DB 복잡도 | 33 / 174 | **38 / 218** | `db_manager + vec_memory` 기준 |

---

## 8. 3Pass 재감리 결과

### Pass 1 — Structure and Scope

- `scope matrix`를 문서 최상단에 추가했다.
- `commit-state` 메타데이터를 추가했다.
- `S1/S2/S3/S4`를 분리해 같은 표 안에 서로 다른 범위 수치를 섞지 않도록 정리했다.

판정: **PASS**

### Pass 2 — Evidence and Consistency

- 모든 핵심 수치를 현재 workspace에서 재산출했다.
- 장함수는 inclusive LOC 기준으로 통일했다.
- `God Object`는 direct-method rule로 고정했다.
- 설정/프롬프트/DB 수치를 현재 실제 파일 존재 상태와 맞췄다.

판정: **PASS**

### Pass 3 — Readability and Operational Use

- 이제 각 섹션이 어떤 범위를 대표하는지 바로 알 수 있다.
- 리팩터링 핫스팟 판단에 필요한 구조 지표와 런타임 위험 지표가 분리되어 있다.
- dirty worktree 기준 문서라는 점을 metadata에 고정했다.

판정: **PASS**

### Confidence Gate

- 현재 신뢰도: **96%**
- 단서: 이 문서는 `9a4f46a8f8193c42e236cf181e0151b26a3167b4` + 위 dirty 상태를 기준으로만 유효하다.
- `modules/`, `scripts/`, `config/`가 더 바뀌면 수치는 다시 흔들릴 수 있으므로 재감리가 필요하다.

---

## 9. 최종 판정

이 판본은 이전 v2의 핵심 문제였던 범위 혼합, stale 설정 수치, direct/nested method 규칙 혼선을 제거했다.  
현재 기준 결론은 다음과 같다.

- `S1` 구조 규모는 **크고 무거운 편**이다. `295파일 / 168,905LOC / 244개 100줄+ 함수`는 유지보수 부담이 높다.
- `S2` 런타임 코어는 **dict 의존, generic except, 장함수, 중첩 깊이** 측면에서 명확한 리팩터링 압력을 갖고 있다.
- 최우선 핫스팟은 여전히 `Stage4InterviewRound`, `DBManager`, `Stage2Preflight`, `Stage4ContextBuilder`, `Stage4Orchestrator` 축이다.
- 설정/프롬프트/DB 수치는 이제 실제 존재하는 파일 기준으로만 해석해야 한다.

즉, 이번 교정판은 더 이상 "대충 방향은 맞는 문서"가 아니라, **현재 dirty workspace 상태를 기준으로 재현 가능한 정적 복잡도 감리 문서**다.

---

## 10. Readability Refactor Tracker

목표: LLM이 읽을 때 한 번에 잡아야 하는 맥락 반경을 줄이되, 회귀 위험이 낮은 tranche부터 순차 처리한다.

| Status | Tranche | 대상 | 기록 |
| --- | --- | --- | --- |
| `v` | T1 | `Stage4InterviewRound.run` PASS/REJECT 종료 처리 추출 | 완료. `_finalize_pass_result`, `_finalize_reject_result` helper로 분리. 회귀 검증: `pytest tests/test_stage4_interview_round.py -q` → `99 passed` |
| `v` | T2 | `Stage4InterviewRound.run` Director input-pack 조립부 추출 | 완료. `_build_director_input_pack()`로 `decision_core / candidate_evidence / reference_appendix` 조립을 분리. 검증: `python -m py_compile modules/core/stage4_interview_round.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_interview_round.py docs/2026-03-20/TF-static-complexity-audit-v2.md`, `python -m pytest tests/test_stage4_interview_round.py -q` → `99 passed` |
| `v` | T3 | `Stage4InterviewRound.run` candidate generation / EMPTY 처리 추출 | 완료. `_run_generation_phase()`, `_build_empty_candidates_result()` helper로 generation/EMPTY early-return 경계를 분리 |
| `v` | T4 | `Stage4InterviewRound.run` pre-director validation handoff 정리 | 완료. `_run_validation_phase()`로 `_god1_*` 임시 필드 세팅과 `_run_pre_director_validation()` 호출을 묶고, `run()`의 미사용 context unpack도 함께 제거 |
| `v` | T5 | `Stage4ContextBuilder.build_mandatory_context` tail prompt 조립부 추출 | 완료. `_build_mandatory_prompt_injections()`로 `anti_trope / justification / writer_guidance / reflexion` 조립을 분리. 검증: `python -m py_compile modules/core/stage4_context_builder.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py`, `python -m pytest tests/test_stage4_context_builder.py tests/test_stage4_context.py -q` → `98 passed` |
| `v` | T6 | `Stage4ContextBuilder.prepare_episode_context` hybrid lookback 조립부 추출 | 완료. `_build_prev_manuscripts_text()`로 Tier1 full-text, Tier2 summary, Tier3 arc-summary lookback 조립을 분리하고 long-term anchor 주입은 caller에 유지 |
| `v` | T7 | `Stage4Orchestrator._run_interview_loop` writer prompt supplement 추출 | 완료. `_build_writer_prompt_supplements()`와 `_WriterPromptSupplements`로 `purism_prompt / npc_equipment_summary / effective_anti_trope / intro_dna` 조립을 분리. 검증: `python -m py_compile modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python -m pytest tests/test_stage4_orchestrator.py -q` → `67 passed` |
| `v` | T8 | `Stage2PreflightAnalysis._preflight_arc_analysis` retry focus-mode 추출 | 완료. `_apply_retry_focus_mode()`로 retry 시 `current_feedback / preserved constraints / minimal context` 조립을 분리. 검증: `python -m py_compile modules/core/stage2_preflight.py tests/test_stage2_preflight.py`, `python scripts/check_utf8_hygiene.py modules/core/stage2_preflight.py tests/test_stage2_preflight.py`, `python -m pytest tests/test_stage2_preflight.py -q` → `34 passed` |
| `v` | T9 | `Stage2PreflightAnalysis._preflight_enrichment` patch-feedback 조립부 추출 | 완료. `_build_patch_feedback()`로 `rejection_reason / selection_reason / score_breakdown / validation_warnings / fix_scope_reasoning` 조립을 분리. 검증: `python -m py_compile modules/core/stage2_preflight.py tests/test_stage2_preflight.py`, `python scripts/check_utf8_hygiene.py modules/core/stage2_preflight.py tests/test_stage2_preflight.py`, `python -m pytest tests/test_stage2_preflight.py -q` → `36 passed` |
| `v` | T10 | `Stage4Orchestrator._run_interview_loop` mandatory-context budget 처리 추출 | 완료. `_fit_mandatory_context_budget()`와 `_MandatoryContextBudgetResult`로 섹션 제거/폴백 절단 규칙을 분리하고 meta/UI logging은 caller에 유지. 검증: `python -m py_compile modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python -m pytest tests/test_stage4_orchestrator.py -q` → `69 passed` |
| `v` | T11 | `Stage4ContextBuilder.build_mandatory_context` ReferenceAnchor 로딩부 추출 | 완료. `_load_reference_anchor_prompt()`로 `relevant/critical anchor` 조회와 prompt 조립을 분리. 검증: `python -m py_compile modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`, `python -m pytest tests/test_stage4_context_builder.py -q` → `65 passed` |
| `v` | T12 | `Stage4Orchestrator._run_interview_loop` current-episode 준비부 추출 | 완료. `_prepare_current_episode_inputs()`와 `_EpisodeLoopInputs`로 `blueprint / arc_data / preflight_advisory` 준비를 분리하고 caller의 `break` 제어는 유지. 검증: `python -m py_compile modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python -m pytest tests/test_stage4_orchestrator.py -q` → `72 passed` |
| `v` | T13 | `Stage4ContextBuilder.build_mandatory_context` base mandatory-context 로딩부 추출 | 완료. `_load_base_mandatory_context()`로 writer mandatory context 로딩과 HUD anomaly 기록을 분리. 검증: `python -m py_compile modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`, `python -m pytest tests/test_stage4_context_builder.py -q` → `67 passed` |
| `v` | T14 | `Stage4Orchestrator._run_interview_loop` prompt-bundle 준비부 추출 | 완료. `_build_episode_prompt_bundle()`와 `_EpisodePromptBundle`로 `genre_name / ctx_prompts / writer prompt supplements` 준비를 분리. 검증: `python -m py_compile modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python -m pytest tests/test_stage4_orchestrator.py -q` → `73 passed` |
| `v` | T15 | `Stage4ContextBuilder.build_mandatory_context` retrieval-seed 준비부 추출 | 완료. `_build_mandatory_context_seed()`와 `Stage4MandatoryContextSeedPayload`로 `cp_entities / work_focus / tier0_parts / slot_summary` 준비를 분리. 검증: `python -m py_compile modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_context_builder.py tests/test_stage4_context_builder.py`, `python -m pytest tests/test_stage4_context_builder.py -q` → `68 passed` |
| `v` | T16 | `Stage4Orchestrator._run_interview_loop` round-context 패키징부 추출 | 완료. `_build_episode_round_context()`로 `_RoundContext` 조립 인자를 묶고 `prompt_bundle` 필드를 직접 전달하도록 정리. 검증: `python -m py_compile modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python scripts/check_utf8_hygiene.py modules/core/stage4_orchestrator.py tests/test_stage4_orchestrator.py`, `python -m pytest tests/test_stage4_orchestrator.py -q` → `74 passed` |
| `[ ]` | T17 | Stage4/Stage2 축 후속 핫스팟 | `stage4_context_builder.py` 잔여 orchestration, `stage4_orchestrator.py` 잔여 loop orchestration, `stage2_preflight.py` 추가 context assembly 순으로 안전 분해 예정 |

운영 메모:
- 각 tranche는 완료 후 이 표의 `Status`를 `v`로 갱신한다.
- 회귀 검증 없이 `v` 처리하지 않는다.
- 전량 처리가 목표지만, 한 번에 하나씩만 진행한다.
