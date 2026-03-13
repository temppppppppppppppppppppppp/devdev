# OPUS TF 5-Terminal 전역 전량 마스터 조사 오더

> **작성일**: 2026-03-13
> **목적**: 거시 건강성 증명 완료 상태에서, 세부 디테일 레벨의 코드 결함·누락·불일치를 전량 적출
> **범위**: 프로덕션 코드 134K lines (239 .py) + 테스트 68K lines (274 .py) + Config/Contract 전량
> **3PASS 감리 완료**

---

## 1. 조사 원칙

### 1.1 탐지 대상 (Severity 등급)

| 등급 | 정의 | 예시 |
|------|------|------|
| **P0-CRITICAL** | 런타임 크래시 또는 데이터 손실 | unhandled None, DB write 누락, 무한루프 |
| **P1-IMPORTANT** | 기능 오동작 (silent wrong result) | 잘못된 조건 분기, 누락된 필드 매핑, 오염된 캐시 |
| **P2-MODERATE** | 성능·관측성·유지보수 결함 | 불필요한 LLM 호출, 로깅 누락, dead code |
| **P3-MINOR** | 코드 위생 (동작에 영향 없음) | 오타, 불일치 docstring, 미사용 import |

### 1.2 조사 방법론

각 터미널은 다음 **6-Point Inspection** 을 전 파일에 적용:

1. **Null/None 안전성**: 모든 외부 데이터(DB, LLM 응답, config, 사용자 입력)에 None guard 존재하는가
2. **분기 정합성**: if/elif/else 체인에 빠진 경로 없는가, 조건 중복/역전 없는가
3. **데이터 흐름 추적**: 입력→가공→출력 경로에서 필드명 불일치·누락·타입 불일치 없는가
4. **에러 처리**: except 블록이 적절한가 (bare except 0건 원칙), 로깅 레벨 정확한가
5. **계약 준수**: CLAUDE.md 4대 원칙, SSOT contract, API contract 위반 없는가
6. **테스트 커버리지 갭**: 프로덕션 코드의 핵심 분기를 테스트가 실제로 검증하는가

### 1.3 보고 형식

각 터미널은 발견사항을 다음 형식으로 보고:

```
### [T{N}-{SEQ}] {제목}
- **Severity**: P0/P1/P2/P3
- **파일**: `path/to/file.py` L{line}
- **현상**: {무엇이 잘못되었는가}
- **근거**: {왜 문제인가, 코드 증거}
- **수정안**: {구체적 수정 방향}
```

### 1.4 금지 사항

- **대원칙 위반 수정 제안 금지**: Python이 LLM 판단을 대체하는 코드를 제안하지 말 것
- **구조 리팩터링 제안 금지**: 이번 조사는 결함 적출만. 아키텍처 변경은 별도 TF
- **오탐 최소화**: 의도적 설계(CLAUDE.md 문서화된 패턴)를 결함으로 보고하지 말 것
- **테스트 수정 직접 실행 금지**: 발견만 보고, 수정은 마스터 취합 후 일괄

---

## 2. 터미널 영역 분할

### 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    글도비 시스템 전역 지도                         │
├───────────┬───────────┬───────────┬───────────┬─────────────────┤
│ Terminal 1│ Terminal 2│ Terminal 3│ Terminal 4│   Terminal 5    │
│  기반 인프라 │ Stage 0→2 │ Stage 3→4 │ 품질·감사  │ 도메인·보조    │
│  & 데이터   │ 파이프라인  │ 파이프라인  │ & Advisory│ & 프런트엔드   │
│ ~16K lines│ ~22K lines│ ~22K lines│ ~20K lines│ ~22K lines     │
│  + 테스트   │  + 테스트   │  + 테스트   │  + 테스트   │  + 테스트       │
└───────────┴───────────┴───────────┴───────────┴─────────────────┘
```

---

## 3. Terminal 1 — 기반 인프라 & 데이터 레이어

### 담당 범위

**진입점 & 앱 프레임워크** (~5K lines)
| 파일 | 줄수 |
|------|------|
| `main_a.py` | 4,051 |
| `RESET.py` | 170 |
| `modules/core/constants.py` | 904 |

**DB & 메모리** (~5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/db_manager.py` | 3,490 |
| `modules/core/vec_memory.py` | 1,331 |
| `modules/core/constraint_db.py` | 611 |

**LLM 추상화 레이어** (~1.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/llm_provider.py` | 36 |
| `modules/core/llm_router.py` | 138 |
| `modules/core/llm_generate.py` | 21 |
| `modules/core/llm_schema.py` | 95 |
| `modules/core/response_schemas.py` | 781 |
| `modules/core/providers/gemini_provider.py` | 49 |
| `modules/core/providers/anthropic_provider.py` | 88 |
| `modules/core/providers/openai_provider.py` | 106 |
| `modules/core/providers/vertex_provider.py` | 118 |

**프롬프트 인프라** (~1.3K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/prompt_builder.py` | 999 |
| `modules/core/prompt_loader.py` | 287 |

**DI Context & 타입** (~650 lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/stage2_context.py` | 259 |
| `modules/core/stage3_context.py` | 120 |
| `modules/core/stage4_context.py` | 179 |
| `modules/core/stage4_types.py` | 91 |

**로깅 & 유틸리티** (~1.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/logger.py` | 322 |
| `modules/core/session_logger.py` | 292 |
| `modules/core/error_helper.py` | 351 |
| `modules/core/project_manager.py` | 922 |
| `modules/core/project_support.py` | 278 |
| `modules/core/runtime_paths.py` | (신규) |
| `modules/core/spinners.py` | 270 |
| `modules/core/hud_utils.py` | 265 |

**Protocol 정의** (~680 lines)
| 파일 | 줄수 |
|------|------|
| `modules/protocols/app_services.py` | 230 |
| `modules/protocols/agents.py` | 159 |
| `modules/protocols/db_repository.py` | 198 |
| `modules/protocols/validators.py` | 37 |

**서비스 레이어** (~1K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/services/project_service.py` | 388 |
| `modules/core/services/state_service.py` | 369 |
| `modules/core/services/ui_service.py` | 138 |
| `modules/core/services/audit_service.py` | 104 |

**Config & Contract 파일**
- `config/models.yaml`, `config/system.yaml`, `config/settings.json`
- `config/settings/validation.yaml`, `config/settings/item_suffixes.yaml`
- `config/tone_presets.json`
- `전처리_ssot/contracts/*.json` (9개)
- `docs/implementation/api-contract-v1.yaml`
- `docs/implementation/prompt-map-v1.json`

**관련 테스트** (전량)
- `tests/test_db_manager.py`, `tests/test_db_integrity_recovery.py`, `tests/test_db_merge.py`
- `tests/test_prompt_builder.py`, `tests/test_prompt_loader.py`
- `tests/test_base_agent.py` (LLM 추상화 부분)
- `tests/test_stage2_context.py`
- `tests/test_protocols.py`, `tests/test_protocols_services.py`, `tests/test_protocol_conformance.py`, `tests/test_protocol_validators.py`
- `tests/test_state_service.py`, `tests/test_ui_service.py`, `tests/test_audit_service.py`
- `tests/test_vec_memory.py`
- `tests/test_integrity.py`
- `tests/test_runtime_paths.py`, `tests/test_project_support.py`
- `tests/test_api_contract.py`
- `tests/test_desktop_contract_refresh.py`
- `tests/test_lmi_known_attrs_sync.py`
- `tests/test_investment_math_wiring.py`

### 핵심 검사 포인트

1. **DB 트랜잭션 안전성**: `db_manager.py`의 모든 write path에서 commit/rollback 쌍 검증
2. **LLM Router fallback**: gemini→flash 폴백 체인이 모든 에러 타입에서 동작하는가
3. **DI Context slots**: `from_app()` → `__slots__` 매핑에 누락 없는가, 타입 불일치 없는가
4. **Config SSOT 정합성**: `models.yaml` ↔ `constants.py` ↔ 실제 사용처 3자 일치
5. **Contract 스키마**: `api-contract-v1.yaml` ↔ `bridge_server.py` 엔드포인트 1:1 대응
6. **Protocol 이행**: `app_services.py` Protocol의 모든 메서드가 `main_a.py`에서 실제 구현되었는가
7. **VecMemory↔DB**: vec_memory가 db_manager 커넥션을 올바르게 공유하는가, 동시성 문제 없는가

---

## 4. Terminal 2 — Stage 0→2 파이프라인

### 담당 범위

**Stage 0 전처리** (~5.1K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/stage0/__init__.py` | 774 |
| `modules/core/stage0/reverse_expander.py` | 1,178 |
| `modules/core/stage0/style_extractor.py` | 1,143 |
| `modules/core/stage0/preset_registry.py` | 739 |
| `modules/core/stage0/spinner.py` | 666 |
| `modules/core/stage0/story_expander.py` | 600 |

**Stage 0→1 헬퍼** (~740 lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/stage01_helpers.py` | 740 |

**Stage 2 오케스트레이션** (~6.7K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/stage2_orchestrator.py` | 954 |
| `modules/core/stage2_validation_pipeline.py` | 1,167 |
| `modules/core/stage2_finalizer.py` | 1,745 |
| `modules/core/stage2_preflight.py` | 1,600 |
| `modules/core/stage2_optimizer.py` | 1,213 |

**Arc 에이전트 체인** (~7K lines)
| 파일 | 줄수 |
|------|------|
| `modules/domain/agents/analyst.py` | 1,838 |
| `modules/domain/agents/analyst_prompts.py` | 747 |
| `modules/domain/agents/analyst_prompt_api.py` | 101 |
| `modules/domain/agents/four_phase_arc_generator.py` | 2,130 |
| `modules/domain/agents/state_locked_arc_generator.py` | 583 |
| `modules/domain/agents/arc_ensemble.py` | 1,167 |
| `modules/domain/agents/arc_draft_validator.py` | 905 |
| `modules/domain/agents/arc_critic.py` | 379 |
| `modules/domain/agents/arc_corrector.py` | 596 |
| `modules/domain/agents/unified_arc_validator.py` | 704 |

**Config — 프롬프트 & 장르 정의**
- `config/prompts/analyst.yaml`
- `config/prompts/arc_generator.yaml`
- `config/prompts/ensemble.yaml`
- `config/prompts/analyst_libraries*.json` (11개)
- `config/genres/*.yaml` (10개 — 장르 정의 자체의 정합성)

**관련 테스트** (전량)
- `tests/test_stage0_fixes.py`, `tests/test_stage0_pov.py`
- `tests/test_stage0_work_guard_style_cache.py`
- `tests/test_reverse_expander_g2.py`
- `tests/test_stage01_helpers.py`
- `tests/test_stage2_preflight.py`, `tests/test_stage2_preflight_helpers.py`
- `tests/test_stage2_pipeline.py`, `tests/test_stage2_finalizer.py`
- `tests/test_stage2_optimizer.py`, `tests/test_stage2_patch_integration.py`
- `tests/test_stage2_context.py`, `tests/test_stage2_validation_pipeline.py`
- `tests/test_four_phase_arc_generator.py`
- `tests/test_arc_difficulty.py`, `tests/test_arc_noise_fixes.py`
- `tests/test_genre_yaml_loading.py`, `tests/test_genre_schema_builder.py`
- `tests/test_process_runner_stage0_inputs.py`
- `tests/test_frontend_stage0_connectivity.py`

### 핵심 검사 포인트

1. **Stage 0 데이터 무결성**: reverse_expander/style_extractor 출력이 Stage 2 입력 스키마와 정확히 일치하는가
2. **Arc 생성 4-Phase 정합성**: four_phase_arc_generator의 Phase 1→2→3→4 데이터 전달에 필드 누락 없는가
3. **앙상블 전략 선택**: arc_ensemble의 후보 비교 로직에 편향·누락 없는가
4. **Stage 2 Preflight→Validation→Finalizer 체인**: 3단계 파이프라인의 데이터 핸드오프 빈틈 없는가
5. **Analyst 장르 분기**: 10개 장르별 `_build_genre_placeholders()` + `analyst_libraries_*.json` 매핑 정확성
6. **Director Selection (TF-S2)**: `compare_and_select_arc()`에서 Python 자동선택 잔류 코드 없는가
7. **Config↔코드 동기**: 장르 YAML 10개 + prompt YAML의 키가 코드에서 참조하는 키와 1:1 대응하는가
8. **STRUCTURAL_MIN_SCORE = 50**: 소프트필터 적용이 "최소 1개 보장" 로직과 정합하는가

---

## 5. Terminal 3 — Stage 3→4 파이프라인

### 담당 범위

**Stage 3 Blueprint** (~5.7K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/stage3_orchestrator.py` | 2,001 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | 789 |
| `modules/domain/agents/blueprint_ensemble.py` | 940 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 460 |
| `modules/domain/agents/unified_blueprint_validator.py` | 465 |
| `modules/domain/agents/block_enricher.py` | 930 |

**Stage 4 원고 생산** (~10.1K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/stage4_orchestrator.py` | 1,549 |
| `modules/core/stage4_interview_round.py` | 4,542 |
| `modules/core/stage4_post_processor.py` | 1,428 |
| `modules/core/stage4_context_builder.py` | 2,592 |

**Chief Writer 체인** (~5.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/domain/agents/chief_writer.py` | 1,875 |
| `modules/domain/agents/chief_writer_context.py` | 1,348 |
| `modules/domain/agents/chief_writer_quality.py` | 1,265 |
| `modules/domain/agents/chief_writer_prompts.py` | 272 |
| `modules/domain/agents/writer.py` | 376 |
| `modules/core/writer_template.py` | 418 |

**수정 전략** (~860 lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/adaptive_retry.py` | 858 |

**프롬프트 Config**
- `config/prompts/blueprint_generator.yaml`
- `config/prompts/chief_writer.yaml`
- `config/prompts/writing_directive.yaml`
- `config/prompts/writer_rules.json`

**관련 테스트** (전량)
- `tests/test_stage3_orchestrator.py`
- `tests/test_blueprint_preflight.py`
- `tests/test_stage4_orchestrator.py`, `tests/test_stage4_interview_round.py`
- `tests/test_stage4_post_processor.py`, `tests/test_stage4_context_builder.py`
- `tests/test_stage4_cv_context.py`
- `tests/test_chief_writer.py`, `tests/test_chief_writer_quality.py`
- `tests/test_pass_with_fix.py`
- `tests/test_adaptive_retry.py`
- `tests/test_stage4_canary.py`
- `tests/stage3_isolated_test/test_stage3_production.py`
- `tests/stage3_isolated_test/test_stage3_arc3*.py`
- `tests/stage4_v2_test/test_batch_1_to_10.py`, `tests/stage4_v2_test/test_episode_1.py`
- `tests/test_desktop_work_guard_template_contract.py`
- `tests/test_director_logging_reinforcement.py`

### 핵심 검사 포인트

1. **Blueprint→Manuscript 핸드오프**: Stage 3 출력 스키마 → Stage 4 입력 스키마 필드 100% 매핑
2. **Interview Round 12개 메서드**: 4,542줄의 거대 모듈 — 메서드 간 상태 전달 누수 점검
3. **PASS_WITH_FIX 3-tier 라우팅**: inplace/partial/full 분기 조건이 정확하고, 30KB 보호가 동작하는가
4. **Self-Critique 15개 체크**: chief_writer_quality.py의 15개 체크가 모두 실행되는가, 스킵 조건 정확한가
5. **Chief Writer Context 빌딩**: 1,348줄의 컨텍스트 조립에서 누락되는 정보 없는가
6. **Stage 4 Post Processor**: PASS 판정 후처리 (WorldState/FactLedger/ChainLink 갱신)가 전량 실행되는가
7. **Blueprint Ensemble**: 후보 비교·선택 로직의 정합성, 앙상블 전략 편향 없는가
8. **Context Caching**: ChiefWriter/BlueprintEnsemble의 50K 임계값 체크 로직 정확성

---

## 6. Terminal 4 — 품질 시스템 & Advisory 체인

### 담당 범위

**Director 체계** (~4.9K lines)
| 파일 | 줄수 |
|------|------|
| `modules/domain/agents/director.py` | 379 |
| `modules/domain/agents/director_ensemble.py` | 1,429 |
| `modules/domain/agents/director_auditor.py` | 1,236 |
| `modules/domain/agents/director_continuity.py` | 868 |
| `modules/domain/agents/director_grading.py` | 688 |
| `modules/domain/agents/director_prompts.py` | 455 |
| `modules/domain/agents/director_caching.py` | 176 |

**Continuity 체계** (~3.7K lines)
| 파일 | 줄수 |
|------|------|
| `modules/domain/agents/continuity_inspector.py` | 548 |
| `modules/domain/agents/continuity_arc.py` | 1,012 |
| `modules/domain/agents/continuity_blueprint.py` | 479 |
| `modules/domain/agents/continuity_manuscript.py` | 1,226 |
| `modules/domain/agents/continuity_tracker.py` | 424 |

**Advisory Chain (10개)** (~2.7K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/truth_gate.py` | 438 |
| `modules/core/npc_drift_advisor.py` | 192 |
| `modules/core/numeric_drift_advisor.py` | 207 |
| `modules/core/relationship_drift_advisor.py` | 168 |
| `modules/core/flashback_verifier.py` | 198 |
| `modules/core/info_paradox_checker.py` | 259 |
| `modules/core/long_term_repetition_advisor.py` | 233 |
| `modules/core/numeric_consistency_checker.py` | 1,000 |

**Pre-Director 검사** (~1.4K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/pre_director_checklist.py` | 595 |
| `modules/core/pre_director_manuscript_checker.py` | 476 |
| `modules/core/pre_director_narrative_checker.py` | 359 |

**Validation 프레임워크** (~8.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/validation/validation_orchestrator.py` | 1,648 |
| `modules/validation/scoring_validator.py` | 1,274 |
| `modules/validation/continuity_validator.py` | 1,042 |
| `modules/validation/consistency_validator.py` | 616 |
| `modules/validation/pre_llm_validator.py` | 515 |
| `modules/validation/blocking_validator.py` | 208 |
| `modules/validation/blocking_validator_entity_checks.py` | 511 |
| `modules/validation/blocking_validator_scene_checks.py` | 442 |
| `modules/validation/blocking_validator_consistency_checks.py` | 383 |
| `modules/validation/action_scene_evaluator.py` | 455 |
| `modules/validation/catharsis_timer.py` | 395 |
| `modules/validation/retrospective_validator.py` | 365 |
| `modules/validation/batch_validator.py` | 299 |
| `modules/validation/advisory_validator.py` | 225 |
| `modules/validation/dialogue_utils.py` | 33 |
| `modules/validation/threshold_helper.py` | 24 |

**품질 메타시스템** (~2.4K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/quality_dashboard.py` | 1,222 |
| `modules/core/quality_amplifier.py` | 410 |
| `modules/core/quality_constitution.py` | 290 |
| `modules/core/confidence_calibration.py` | 458 |

**프롬프트 Config**
- `config/prompts/director.yaml`
- `config/prompts/emotion_tracker.yaml`
- `config/prompts/investment_math_verifier.yaml`
- `config/settings/validation.yaml`

**관련 테스트** (전량)
- `tests/test_director_modules.py`, `tests/test_director_bias.py`
- `tests/test_director_continuity_sc5.py`
- `tests/test_continuity_modules.py`, `tests/test_continuity_packet.py`, `tests/test_continuity_validator.py`
- `tests/test_consistency_validator.py`
- `tests/test_validation.py`
- `tests/test_blocking_validator_submodules.py`
- `tests/test_action_scene_evaluator.py`, `tests/test_catharsis_timer.py`
- `tests/test_info_paradox_checker.py`
- `tests/test_numeric_consistency_checker.py`
- `tests/test_quality_trend.py`
- `tests/test_manuscript_validator.py`
- `tests/test_pre_director_checklist_submodules.py`
- `tests/test_run_validator.py`
- `tests/test_v75b_escalation.py`, `tests/test_v75c_contradiction_firewall.py`
- `tests/test_sc6_observability.py`
- `tests/test_relationship_drift_advisor.py`
- `tests/test_sweep3.py` ~ `tests/test_sweep39.py` (관련 항목)

### 핵심 검사 포인트

1. **Director 주권 (대원칙 3)**: Director를 우회하는 자동 REJECT/PASS 코드가 남아있지 않은가
2. **Advisory → Director MC Parts 주입**: 10개 advisory 결과가 빠짐없이 `_director_mc_parts`에 합류하는가
3. **ThreadPoolExecutor(8) 안전성**: future.result(timeout=60) 후 예외 처리, cancel() 누락 없는가
4. **TruthGate 7개 검사**: 모든 검사가 실행되고, CRITICAL 우선순위가 정확히 전파되는가
5. **NC-1/NC-3 규칙 준수**: NC-1은 선택사항 + NC-3B 자동교정이 정확한가
6. **Validation Orchestrator 분기**: 1,648줄에서 validator 간 의존성·순서가 올바른가
7. **Scoring Validator**: 점수 계산 공식의 산술 정확성, 경계값 처리
8. **사망 캐릭터 (대원칙 4)**: deceased=True NPC 필터가 continuity/truth_gate/blocking 모든 경로에서 동작하는가
9. **Pre-Director 3단 검사**: checklist→manuscript→narrative 순서와 결과 병합 정합성

---

## 7. Terminal 5 — 도메인 로직 & 보조 시스템

### 담당 범위

**Genre Guards** (~7.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/genre_guards/base_guard.py` | 861 |
| `modules/core/genre_guards/wuxia_guard.py` | 662 |
| `modules/core/genre_guards/hunter_guard.py` | 867 |
| `modules/core/genre_guards/investment_guard.py` | 717 |
| `modules/core/genre_guards/fantasy_guard.py` | 362 |
| `modules/core/genre_guards/alt_history_guard.py` | 492 |
| `modules/core/genre_guards/composer_guard.py` | 518 |
| `modules/core/genre_guards/cooking_guard.py` | 511 |
| `modules/core/genre_guards/medical_guard.py` | 469 |
| `modules/core/genre_guards/actor_guard.py` | 464 |
| `modules/core/genre_guards/sports_guard.py` | 462 |
| `modules/core/genre_guards/work_guard.py` | 854 |
| `modules/core/genre_guards/style_guard.py` | 167 |

**세계 상태 & 팩트** (~3.6K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/world_state.py` | 1,209 |
| `modules/core/fact_ledger.py` | 717 |
| `modules/core/state_delta_tracker.py` | 434 |
| `modules/core/chain_of_verification.py` | 372 |
| `modules/core/genre_schema_builder.py` | 445 |
| `modules/core/genre_hud_manager.py` | 751 |

**NPC & 캐릭터** (~4.8K lines)
| 파일 | 줄수 |
|------|------|
| `modules/domain/agents/state_tracker.py` | 1,668 |
| `modules/domain/agents/state_tracker_npc.py` | 2,204 |
| `modules/domain/agents/state_tracker_plots.py` | 963 |
| `modules/domain/agents/state_tracker_financial.py` | 124 |
| `modules/domain/agents/state_extractor.py` | 858 |
| `modules/domain/agents/manuscript_validator.py` | 989 |
| `modules/core/relationship_tracker_npc.py` | 409 |
| `modules/core/relationship_tracker_factions.py` | 848 |
| `modules/core/character_voice.py` | 577 |
| `modules/core/character_voice_profiler.py` | 451 |
| `modules/core/emotion_tracker.py` | 409 |

**서사 분석 & 패턴** (~5.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/narrative_diversity.py` | 592 |
| `modules/core/narrative_structure_analyzer.py` | 308 |
| `modules/core/narrative_context_formatter.py` | (크기 확인 필요) |
| `modules/core/foreshadow_tracker.py` | 686 |
| `modules/core/information_diffusion.py` | 441 |
| `modules/core/semantic_plot_guard.py` | 303 |
| `modules/core/pattern_tracker.py` | 1,209 |
| `modules/core/semantic_item_registry.py` | 801 |
| `modules/core/pacing_analyzer.py` | 439 |

**지능 & 전략** (~4.5K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/context_advisor.py` | 889 |
| `modules/core/agent_intelligence.py` | 606 |
| `modules/core/diversity_sampler.py` | 510 |
| `modules/core/tree_of_thoughts.py` | 744 |
| `modules/core/context_compression.py` | 379 |
| `modules/core/expert_mixture.py` | 388 |
| `modules/core/multi_agent_deliberation.py` | 427 |
| `modules/core/dynamic_prompt_weighting.py` | 302 |

**실패 분석 & 피드백** (~3.3K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/failure_analyzer.py` | 1,483 |
| `modules/core/failure_learning.py` | 367 |
| `modules/core/feedback_system.py` | 853 |
| `modules/core/pass_rate_monitor.py` | 561 |

**기타 핵심 모듈** (~3K lines)
| 파일 | 줄수 |
|------|------|
| `modules/core/writing_directive_generator.py` | (크기 확인 필요) |
| `modules/core/adversarial_self_play.py` | 397 |
| `modules/core/self_reflection.py` | 334 |
| `modules/core/cross_agent_verifier.py` | 498 |
| `modules/core/investment_arithmetic_checker.py` | 473 |
| `modules/core/semantic_query_broker.py` | 465 |
| `modules/core/data_collector.py` | 458 |
| `modules/core/metrics_collector.py` | 535 |
| `modules/core/reference_anchor.py` | 353 |
| `modules/core/justification_patterns.py` | 318 |
| `modules/core/primitive_guard.py` | 285 |
| `modules/core/power_scaling.py` | 521 |
| `modules/core/martial_manager.py` | 564 |
| `modules/core/lore_manager.py` | 445 |
| `modules/core/quality_sidecar_bootstrap.py` | (크기 확인 필요) |
| `modules/core/artifact_logging.py` | (크기 확인 필요) |

**API 레이어** (~2.9K lines)
| 파일 | 줄수 |
|------|------|
| `modules/api/bridge_server.py` | 1,549 |
| `modules/api/process_runner.py` | 676 |
| `modules/api/risk_approval.py` | 215 |
| `modules/api/prompt_broker.py` | 184 |
| `modules/api/prompt_classifier.py` | 144 |
| `modules/api/run_validator.py` | 89 |

**Desktop (Electron)** (~1.7K lines)
| 파일 | 줄수 |
|------|------|
| `geuldobi-desktop/main.js` | 758 |
| `geuldobi-desktop/src/main.js` | 843 |
| `geuldobi-desktop/src/preload.js` | 54 |
| `geuldobi-desktop/src/index.html` | (크기 확인 필요) |

**관련 테스트** (전량)
- `tests/test_genre_guard.py`, `tests/test_genre_guards_extended.py`
- `tests/test_work_guard.py`, `tests/test_style_guard.py`
- `tests/test_state_tracker.py`, `tests/test_npc_info_chain.py`, `tests/test_npc_history.py`
- `tests/test_relationship_tracker.py`, `tests/test_relationship_tracker_submodules.py`
- `tests/test_con2_npc_position_tracking.py`
- `tests/test_feedback_system.py`, `tests/test_failure_analyzer.py`
- `tests/test_semantic_plot_guard.py`, `tests/test_repetition_guard.py`
- `tests/test_negative_example_injector.py`
- `tests/test_martial_manager.py`
- `tests/test_hud_utils.py`
- `tests/test_narrative_context_formatter.py`
- `tests/test_context_advisor.py`
- `tests/test_pydantic_models.py`
- `tests/test_edge_cases.py`
- `tests/test_satisfaction_framework.py`, `tests/test_satisfaction_step3_tagging.py`, `tests/test_satisfaction_step4_frustration.py`
- `tests/test_reader_feedback.py`
- `tests/test_cross_episode_repetition.py`
- `tests/test_rollback_npc.py`
- `tests/test_bridge_quality_summary.py`
- `tests/test_run_validator.py`
- `tests/test_artifact_logging.py`
- `tests/test_ui_renderer_sanitization.py`
- `tests/test_frontend_frontier_lag_wiring.py`, `tests/test_one_stop_frontier_lag.py`
- `tests/test_viewpoint_primary_external_policy.py`
- `tests/test_stage4_canary.py` (장르 가드 부분)
- `tests/chaos/*.py` (5개 전량)
- `tests/property/*.py` (4개 전량)
- `tests/e2e/*.py` (관련 항목)

### 핵심 검사 포인트

1. **Genre Guard 10종 일관성**: base_guard의 인터페이스를 10개 장르가 모두 동일하게 구현하는가
2. **WorkGuard → GenreGuard 체인**: work_guard.yaml 오버라이드가 base 금기어와 충돌하지 않는가
3. **WorldState 9개 필드**: 갱신 경로마다 모든 필드가 빠짐없이 처리되는가
4. **FactLedger append-only**: MAX_HISTORY_PER_ENTITY=10 초과 시 올바르게 evict하는가
5. **StateTracker NPC 2,204줄**: NPC 등록·수정·삭제 경로의 DB write-back 정합성
6. **protagonist_items vs items_acquired**: 14파일 21곳 폴백 패턴이 실제로 전량 적용되었는가
7. **비무협 장르 오염**: genre_schema_builder → analyst placeholders → truth_gate 3단 방어 빈틈 없는가
8. **Bridge Server 엔드포인트**: 1,549줄의 모든 라우트에서 입력 검증·에러 응답이 일관된가
9. **Electron IPC**: preload.js ↔ main.js ↔ bridge_server.py 3자 메시지 프로토콜 정합성
10. **Chaos/Property 테스트**: 경계조건 테스트가 실제 프로덕션 경로를 커버하는가

---

## 8. 각 터미널에 내릴 오더

### Terminal 1 오더

```
OPUS TF — Terminal 1: 기반 인프라 & 데이터 레이어 전량 조사

너는 글도비 시스템의 기반 인프라 담당 OPUS TF다.

■ 범위: main_a.py, DB(db_manager/vec_memory/constraint_db), LLM 추상화(llm_*/providers/*),
  프롬프트(prompt_builder/loader), DI Context(stage2/3/4_context), Protocol 정의,
  서비스 레이어, 로깅/유틸, Config/Contract 파일 전량.

■ 임무:
1. 위 범위의 모든 파일을 1줄 단위로 읽고, 6-Point Inspection 적용
2. DB 트랜잭션 안전성: 모든 write path의 commit/rollback 쌍 검증
3. LLM Router: fallback chain이 모든 에러 타입(timeout/rate-limit/malformed)에서 동작하는가
4. DI Context: from_app() 매핑 누락, __slots__ 불일치, 타입 오류
5. Config SSOT: models.yaml ↔ constants.py ↔ 실사용처 3자 교차 검증
6. Protocol 이행: app_services.py의 모든 메서드가 main_a.py에서 구현되었는가
7. Contract 정합: api-contract-v1.yaml ↔ bridge_server.py 엔드포인트 1:1 대응
8. 관련 테스트가 핵심 분기를 실제로 검증하는지 확인

■ 보고: 마스터 문서의 [T1-{SEQ}] 형식. Severity P0~P3.
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md, docs/implementation/api-contract-v1.yaml
```

### Terminal 2 오더

```
OPUS TF — Terminal 2: Stage 0→2 파이프라인 전량 조사

너는 글도비 시스템의 Stage 0→2 파이프라인 담당 OPUS TF다.

■ 범위: Stage 0(stage0/*), stage01_helpers, Stage 2(stage2_*), Arc 에이전트 체인
  (analyst/four_phase_arc/state_locked_arc/arc_ensemble/arc_critic/arc_corrector/
  arc_draft_validator/unified_arc_validator), 관련 config/prompt, 관련 테스트 전량.

■ 임무:
1. 위 범위의 모든 파일을 1줄 단위로 읽고, 6-Point Inspection 적용
2. Stage 0→2 데이터 핸드오프: reverse_expander/style_extractor 출력 스키마 → Stage 2 입력 스키마 필드 매핑 검증
3. Arc 4-Phase: Phase 1→2→3→4 데이터 전달 누락 필드 적출
4. 앙상블: arc_ensemble 후보 비교 로직의 편향/누락 점검
5. Preflight→Validation→Finalizer: 3단 파이프라인 핸드오프 빈틈
6. Analyst 장르 분기: 10개 장르별 placeholders + libraries 매핑 정확성
7. Director Selection (TF-S2): Python 자동선택 잔류 코드 점검
8. Config↔코드: 장르 YAML 10개 + prompt YAML 키 vs 코드 참조 키 대응
9. 관련 테스트가 핵심 분기를 실제로 검증하는지 확인

■ 보고: 마스터 문서의 [T2-{SEQ}] 형식. Severity P0~P3.
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md (Stage2 Director Selection, 비무협 장르 오염 방지 섹션)
```

### Terminal 3 오더

```
OPUS TF — Terminal 3: Stage 3→4 파이프라인 전량 조사

너는 글도비 시스템의 Stage 3→4 파이프라인 담당 OPUS TF다.

■ 범위: Stage 3(stage3_orchestrator, blueprint 에이전트 5개, block_enricher),
  Stage 4(stage4_orchestrator/interview_round/post_processor/context_builder),
  Chief Writer 체인(chief_writer*/writer*/writer_template),
  adaptive_retry, 관련 config/prompt, 관련 테스트 전량.

■ 임무:
1. 위 범위의 모든 파일을 1줄 단위로 읽고, 6-Point Inspection 적용
2. Blueprint→Manuscript 핸드오프: Stage 3 출력 → Stage 4 입력 필드 100% 매핑 검증
3. Interview Round: 4,542줄 12개 메서드 간 상태 전달 누수 점검
4. PASS_WITH_FIX 3-tier: inplace(30KB보호)/partial/full 분기 조건 정확성
5. Self-Critique 15개: chief_writer_quality.py의 15개 체크 전량 실행 확인, 스킵 조건
6. Context Building: chief_writer_context.py 1,348줄에서 누락 정보 점검
7. Post Processor: PASS 후 WorldState/FactLedger/ChainLink 갱신 전량 실행 확인
8. Context Caching: ChiefWriter/BlueprintEnsemble 50K 임계값 체크 정확성
9. 관련 테스트가 핵심 분기를 실제로 검증하는지 확인

■ 보고: 마스터 문서의 [T3-{SEQ}] 형식. Severity P0~P3.
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md (PASS_WITH_FIX, Self-Critique, Context Caching 섹션)
```

### Terminal 4 오더

```
OPUS TF — Terminal 4: 품질 시스템 & Advisory 체인 전량 조사

너는 글도비 시스템의 품질 시스템 & Advisory 체인 담당 OPUS TF다.

■ 범위: Director 체계(director.py + 6 서브모듈), Continuity 체계(5개),
  Advisory Chain(truth_gate/npc_drift/numeric_drift/relationship_drift/
  flashback_verifier/info_paradox/long_term_repetition/numeric_consistency),
  Pre-Director 검사(3개), Validation 프레임워크(16개 모듈),
  품질 메타시스템(quality_dashboard/amplifier/constitution/confidence_calibration),
  관련 config/prompt, 관련 테스트 전량.

■ 임무:
1. 위 범위의 모든 파일을 1줄 단위로 읽고, 6-Point Inspection 적용
2. Director 주권 (대원칙 3): Director 우회 자동 REJECT/PASS 잔류 코드 적출
3. Advisory → MC Parts: 10개 advisory 결과가 빠짐없이 합류하는지 검증
4. ThreadPoolExecutor(8): timeout/cancel/exception 전 경로 안전성
5. TruthGate: 7개 검사 전량 실행, CRITICAL 우선순위 전파 정확성
6. NC-1/NC-3: 선택사항 규칙 + NC-3B 자동교정 정확성
7. Validation Orchestrator: validator 간 의존성·순서 정합성
8. Scoring: 점수 공식 산술 정확성, 경계값 처리
9. 사망 캐릭터 (대원칙 4): deceased=True 필터 전 경로 동작 확인
10. Pre-Director 3단: checklist→manuscript→narrative 결과 병합 정합성
11. 관련 테스트가 핵심 분기를 실제로 검증하는지 확인

■ 보고: 마스터 문서의 [T4-{SEQ}] 형식. Severity P0~P3.
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md (Advisory 체인, NC-1/NC-3, 대원칙 3·4 섹션)
```

### Terminal 5 오더

```
OPUS TF — Terminal 5: 도메인 로직 & 보조 시스템 전량 조사

너는 글도비 시스템의 도메인 로직 & 보조 시스템 담당 OPUS TF다.

■ 범위: Genre Guards(base + 10종 + work/style), 세계 상태(world_state/fact_ledger/
  state_delta_tracker/chain_of_verification/genre_schema_builder/genre_hud_manager),
  NPC/캐릭터(state_tracker*/state_extractor/manuscript_validator/relationship_tracker*/
  character_voice*/emotion_tracker), 서사 분석(narrative_*/foreshadow_tracker/
  information_diffusion/semantic_plot_guard/pattern_tracker/pacing_analyzer),
  지능(context_advisor/agent_intelligence/diversity_sampler/tree_of_thoughts/
  context_compression/expert_mixture/multi_agent_deliberation),
  실패/피드백(failure_analyzer/failure_learning/feedback_system/pass_rate_monitor),
  기타(investment_arithmetic/martial_manager/power_scaling/lore_manager 등),
  API(bridge_server/process_runner/risk_approval/prompt_broker/prompt_classifier),
  Desktop(geuldobi-desktop/*), 관련 테스트 전량 + chaos/property 테스트.

■ 임무:
1. 위 범위의 모든 파일을 1줄 단위로 읽고, 6-Point Inspection 적용
2. Genre Guard 10종: base_guard 인터페이스 일관성, 오버라이드 누락/충돌
3. WorkGuard 체인: GenreGuard → WorkGuard → StyleGuard 합성 정합성
4. WorldState: 9개 필드 갱신 경로 전량 추적, 누락 필드 적출
5. FactLedger: append-only + MAX_HISTORY eviction 정확성
6. StateTracker NPC 2,204줄: 등록/수정/삭제 → DB write-back 전경로 정합성
7. protagonist_items vs items_acquired: 14파일 21곳 폴백 실제 적용 전수 확인
8. 비무협 오염 3단 방어: genre_schema_builder → analyst → truth_gate 빈틈
9. Bridge Server: 전 엔드포인트 입력검증·에러응답 일관성
10. Electron IPC: preload ↔ main ↔ bridge 3자 메시지 프로토콜 정합성
11. Chaos/Property 테스트: 실제 프로덕션 경계조건 커버리지 확인
12. 관련 테스트가 핵심 분기를 실제로 검증하는지 확인

■ 보고: 마스터 문서의 [T5-{SEQ}] 형식. Severity P0~P3.
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md (비무협 장르 오염 방지, protagonist_items, WorldState 섹션)
```

---

## 9. 취합 프로세스

### 9.1 개별 터미널 완료 후

각 터미널이 보고서를 제출하면:

1. **P0 즉시 에스컬레이션**: P0 발견 시 즉시 보고, 다른 터미널 완료 대기 없이 검토
2. **교차 검증**: 터미널 경계에 걸치는 이슈(예: T2 Stage2 출력 ↔ T3 Stage3 입력)는 양쪽 보고서 대조
3. **중복 제거**: 동일 이슈가 여러 터미널에서 보고된 경우 가장 상세한 것을 채택

### 9.2 최종 마스터 보고서

- **파일명**: `docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings.md`
- **구성**: P0→P1→P2→P3 순 정렬, 터미널별 섹션
- **액션 플랜**: P0/P1 항목에 대해 수정 우선순위 배정

---

## 10. 3PASS 감리 기록

### PASS 1 — 구조 검증 (완료)
- [x] 5개 터미널 범위가 전체 코드베이스를 빠짐없이 커버하는가
- [x] 터미널 간 중복 영역 최소화 (경계 파일 명확히 한쪽에 배정)
- [x] 각 터미널 작업량 대략 균등 (16K~22K lines)
- [x] 검사 포인트가 CLAUDE.md 대원칙/주의사항을 전량 반영하는가
- **수정**: base_agent.py를 T1에서 제외 (T3 Chief Writer 체인과 밀접), API 레이어를 T5로 이동 (bridge_server가 T5 도메인과 직결)

### PASS 2 — 오더 정합성 (완료)
- [x] 각 터미널 오더에 범위·임무·보고형식·금지사항·참조 5요소 완비
- [x] 핵심 검사 포인트가 해당 터미널의 실제 파일과 1:1 대응
- [x] CLAUDE.md에 명시된 특수 규칙(NC-1/NC-3, PASS_WITH_FIX, Director 주권 등)이 해당 터미널에 반영
- [x] 보고 형식 통일 ([TN-SEQ], Severity, 파일/라인, 현상/근거/수정안)
- **수정**: T4에 NC-3B 자동교정 검사 명시 추가, T2에 STRUCTURAL_MIN_SCORE 검사 추가

### PASS 3 — 누락 항목 최종 점검 (완료)
- [x] `modules/models/` (arc.py, blueprint.py, manuscript.py, npc.py) — T1 Protocol 섹션에 포함 확인
- [x] `modules/core/artifact_logging.py`, `quality_sidecar_bootstrap.py` — T5 기타 모듈에 포함 확인
- [x] `writing_directive_generator.py` — T5 기타 모듈에 포함 확인
- [x] `stage4_canary_tools.py` — T3에서 커버 (Stage 4 파이프라인)
- [x] `negative_example_injector.py`, `consensus_validator.py`, `preflight_checker.py` — T5에 포함 확인
- [x] chaos/property 테스트 4+5개 — T5에 배정 확인
- [x] e2e 테스트 — 관련 stage 터미널에 분산 배정 확인
- [x] `전처리_ssot/contracts/` — T1에 배정 확인
- [x] Desktop 파일 — T5에 배정 확인
- **최종 확인**: 239 .py 모듈 전량 + 274 테스트 파일 전량 + Config/Contract 전량 커버 완료
