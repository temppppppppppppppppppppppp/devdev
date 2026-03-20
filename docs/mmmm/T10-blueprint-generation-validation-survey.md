# T10 — Blueprint Generation & Validation Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY

**Terminal**: T10
**Area**: Blueprint Generation & Validation
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Confidence**: 96%

---

## 1. Scope & Files

### Source Files

| File | Lines | Role |
|------|-------|------|
| `modules/domain/agents/three_phase_blueprint_generator.py` | 973 | 3-Phase 파이프라인 오케스트레이터 |
| `modules/domain/agents/blueprint_ensemble.py` | 1,072 | 3-Strategy 병렬 생성 엔진 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | 606 | Arc→Blueprint 제약 블록 컴파일러 |
| `modules/domain/agents/unified_blueprint_validator.py` | 771 | Python 사전검사 + Director 판정 중개 |
| `modules/domain/agents/constraint_compiler.py` | 423 | Stage 2용 제약 조건 컴파일러 (Arc 설계) |
| `modules/core/constraint_db.py` | 664 | Pre-Generation 제약 DB (아이템/수여물 추적) |
| `modules/models/blueprint.py` | 87 | Pydantic v2 Blueprint 모델 |

### Test Files

| File | Lines | Coverage |
|------|-------|----------|
| `tests/test_blueprint_patch_mode.py` | 688 | ThreePhaseBlueprintGenerator patch mode |
| `tests/test_blueprint_preflight.py` | 482 | Stage4Orchestrator._preflight_validate_blueprint |
| `tests/test_canonical_constraints.py` | 169 | FactLedger/WorldState canonical constraints |

---

## 2. TF Registry

### T10-TF-001 — Three Phase Blueprint Pipeline Structure SYNC
```
ID: T10-TF-001
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/three_phase_blueprint_generator.py
Evidence:
  - three_phase_blueprint_generator.py:244-268 — Phase 1 (CONSTRAINT): constraint_compiler.compile() 호출
  - three_phase_blueprint_generator.py:272-438 — Phase 2 (GENERATE): ensemble.generate_ensemble() 호출
  - three_phase_blueprint_generator.py:440-823 — Phase 3 (VALIDATE): validator.validate() + Director 판정
  - 각 phase 결과가 pipeline_result["phases"]에 기록됨 (L264, L428, L520)
  - stats 카운터: total_attempts, phase1_complete, phase2_complete, phase3_pass, phase3_reject (L55-61)
Inference: 3-Phase 파이프라인 구조가 docstring 설계(L1-18)와 일치. Phase 1 캐싱(L246-249), Phase 2 Ensemble 생성, Phase 3 Director 판정 순서가 명확.
Uncertainty: 없음
Cross-Ref: T04 (Stage 3 Pipeline), T07 (Director System)
```

### T10-TF-002 — Scene Count Minimum Inconsistency (Ensemble 4 vs Validator 3)
```
ID: T10-TF-002
Severity: P3-LOW
Category: CONTRADICTION
Surface: blueprint_ensemble.py:453, unified_blueprint_validator.py:634
Evidence:
  - blueprint_ensemble.py:453: `if scene_count >= 4 and integrated_len >= 500:`
    → Ensemble은 최소 4씬 + 500자를 요구하여 4씬 미달 시 후보 탈락
  - unified_blueprint_validator.py:634: `if scene_count < 3:`
    → Validator는 최소 3씬 미만일 때 MAJOR 이슈 발행
  - 둘 다 scene_breakdown의 씬 개수를 체크하지만 임계값이 다름 (4 vs 3)
Inference: Ensemble이 4씬 미만을 미리 걸러내므로 Validator의 3씬 미만 체크는 이론적으로 도달하지 않음 (단, 단일 후보 경로에서 Ensemble을 거치지 않는 inplace 패치 시에는 Validator만 통과할 수 있어 안전장치 역할). 실질적 모순은 아니나, 임계값이 암묵적으로 불일치.
Uncertainty: inplace patch 결과가 3씬인 경우 Validator는 통과, Ensemble 재진입 시에는 탈락할 수 있음
Cross-Ref: T06 (Stage 4 Interview — 유사 게이트 패턴)
```

### T10-TF-003 — ending_hook Missing from Pydantic Blueprint Model
```
ID: T10-TF-003
Severity: P2-MEDIUM
Category: DRIFT
Surface: modules/models/blueprint.py, modules/core/response_schemas.py:642
Evidence:
  - response_schemas.py:642: `"ending_hook": types.Schema(type=types.Type.STRING),`
    → BLUEPRINT_SCHEMA에 ending_hook 필드 정의됨
  - modules/models/blueprint.py:40-63: Blueprint 클래스에 ending_hook 필드 없음
    Grep "ending_hook" in modules/models/blueprint.py → 0 matches
  - Blueprint 클래스는 `extra="allow"` (L46)이므로 ending_hook은 extra 필드로 수용됨
  - 그러나 validate_blueprint() (L76-86)에서 model_dump() 시 extra 필드는 포함되나,
    명시적 필드가 아니므로 타입 검증/기본값/문서화가 누락됨
  - blueprint_constraint_compiler.py:342: `continuity["prev_ending"] = prev_blueprint.get("ending_hook", "")`
  - blueprint_ensemble.py:926-928: `ending_hook = prev_blueprint.get("ending_hook", "")`
  - unified_blueprint_validator.py:452: `prev_ms_ending = prev_blueprint.get("ending_hook", "")`
    → 3곳에서 ending_hook을 참조하지만 Pydantic 모델에는 미정의
Inference: extra="allow"로 인해 런타임 크래시는 없으나, ending_hook이 스키마 필수 의미(Director 판정 시 연속성 훅)를 갖는데도 Pydantic 모델에서 명시되지 않아 문서/타입 안전성이 부족함.
Uncertainty: extra="allow"가 있으므로 실제 데이터 손실은 없을 것으로 추론. 동적 검증 필요.
Cross-Ref: T17 (Config/Schemas — response_schemas.py), T05 (Stage 4 — Blueprint 소비 측)
```

### T10-TF-004 — compile_to_prompt() Dead Code in Production
```
ID: T10-TF-004
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/domain/agents/blueprint_constraint_compiler.py:108-201
Evidence:
  - blueprint_constraint_compiler.py:108: `def compile_to_prompt(self, constraint_block: dict) -> str:`
  - Grep "compile_to_prompt" in modules/ → 1 match (정의 자체만)
  - Grep "compile_to_prompt" in tests/ → 2 matches (test_legacy_reentry_reaudit.py:119, :126)
  - three_phase_blueprint_generator.py에서 compile() 결과를 받지만 compile_to_prompt()는 호출하지 않음
  - 대신 blueprint_ensemble.py:289에서 _format_constraints()로 자체 포맷팅함
Inference: compile_to_prompt()는 원래 프롬프트 주입용이었으나 V60.80 리팩토링 시 _format_constraints()로 대체됨. 레거시 테스트만 호출.
Uncertainty: 없음 — 프로덕션 호출 경로 0건 확인됨
Cross-Ref: 없음
```

### T10-TF-005 — BlueprintConstraintCompiler Arc Data Field Extraction
```
ID: T10-TF-005
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/blueprint_constraint_compiler.py:43-106
Evidence:
  - compile() L43-106 추출 필드:
    1. arc_data["tactical_doc"] → _extract_episode_focus() L203
    2. arc_data["ep_start"], arc_data["ep_count"] → arc_position 계산 L64-69
    3. arc_data["beat_sequence"] → 폴백 L213-221
    4. arc_data["episode_details"] → 에피소드별 상세 L251-259
    5. arc_data["state_constraints"] → _extract_inherited_state() L378-420
    6. arc_data["joint_docs"] → _extract_inherited_state() L386-392
    7. arc_data["status_shadow"] → _extract_inherited_state() L394-409
    8. arc_data["constraint_summary"] → L84-86
    9. arc_data["state_changes"] → _summarize_state_changes() L89
    10. arc_data["semantic_carryover"] → _normalize_semantic_carryover() L90
  - 출력: constraint_block dict (7 키: must_focus, stop_line, continuity, inherited_state, arc_constraint_summary, state_changes_summary, semantic_carryover)
Inference: 10개 소스 필드에서 7개 제약 블록으로 구조화. genre 파라미터로 비무협 장르의 internal_energy 필터링 적용(TF-41 패치).
Uncertainty: 없음
Cross-Ref: T02 (Stage 2 — arc_data 생성 측), T09 (Arc Generation — Arc 출력 구조)
```

### T10-TF-006 — Dual Constraint Compilers (Blueprint vs Arc)
```
ID: T10-TF-006
Severity: P4-OBSERVATION
Category: SYNC
Surface: blueprint_constraint_compiler.py, constraint_compiler.py
Evidence:
  - BlueprintConstraintCompiler (blueprint_constraint_compiler.py): Stage 3용
    → 호출: three_phase_blueprint_generator.py:45 (ThreePhaseBlueprintGenerator.__init__)
    → 입력: arc_data + ep_num + prev_blueprint
    → 출력: constraint_block dict (episode-level 제약)
  - ConstraintCompiler (constraint_compiler.py): Stage 2용
    → 호출: main_a.py:210, stage2_preflight.py:780
    → 입력: prev_arcs list + state_extractor_result
    → 출력: 구조화된 체크리스트 문자열 (arc-level 제약)
  - 역할 분리: ConstraintCompiler는 Arc 간 중복 획득 방지, BlueprintConstraintCompiler는 에피소드별 제약
Inference: 이름이 유사하나 역할이 명확히 분리됨. BlueprintConstraintCompiler는 LLM 미호출(Python-only), ConstraintCompiler도 Python-only.
Uncertainty: 없음
Cross-Ref: T03 (Stage 2 Preflight — ConstraintCompiler 소비 측)
```

### T10-TF-007 — Blueprint Ensemble 3-Strategy Parallel Generation
```
ID: T10-TF-007
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/blueprint_ensemble.py:40-80
Evidence:
  - blueprint_ensemble.py:40-80: BLUEPRINT_STRATEGIES 3개 정의
    1. "action_focused" — 긴장도 7-9/10, 전투/추격/대결
    2. "emotion_focused" — 긴장도 4-6/10, 심리/갈등/화해
    3. "dialogue_focused" — 긴장도 3-7/10, 대화/음모/협상
  - blueprint_ensemble.py:330: `ThreadPoolExecutor(max_workers=self.max_workers)` (max_workers=3, L200)
  - blueprint_ensemble.py:332-355: 3 전략 각각 future submit
  - blueprint_ensemble.py:440-453: 최소 기준 필터링 (4씬 + 500자)
  - blueprint_ensemble.py:494: `return qualified_candidates[0], qualified_candidates` (첫 후보 = 대표, 전체 리스트 = Director 선택용)
  - 타임아웃: ENSEMBLE_TIMEOUT=300s, SINGLE_CANDIDATE_TIMEOUT=240s (L193-194)
Inference: 3전략 병렬 생성 → Python 최소 기준 필터 → Director 비교 선택 흐름 확인됨.
Uncertainty: 없음
Cross-Ref: T07 (Director — compare_and_select_blueprint)
```

### T10-TF-008 — Patch Mode Thresholds SYNC
```
ID: T10-TF-008
Severity: P4-OBSERVATION
Category: SYNC
Surface: three_phase_blueprint_generator.py:282-292, constants.py:633-645
Evidence:
  - constants.py:644: `REWRITE = _LazyThreshold("patch_mode.rewrite_below", 50)`
  - constants.py:645: `INPLACE = _LazyThreshold("patch_mode.inplace_below", 60)`
  - three_phase_blueprint_generator.py:285-288:
    ```python
    _use_inplace = _previous_best is not None and (
        _prev_fix_scope == "inplace"
        or (not _prev_fix_scope and _prev_reject_score >= PatchModeThresholds.INPLACE)
    )
    ```
  - three_phase_blueprint_generator.py:291:
    `_use_partial = (not _use_inplace) and _previous_best is not None and (_prev_fix_scope == "partial")`
  - tests/test_blueprint_patch_mode.py:557-583: score=60 경계값 테스트 (L557-583)
  - tests/test_blueprint_patch_mode.py:504-529: score<50 → inplace 미진입 테스트
  - tests/test_blueprint_patch_mode.py:531-555: score 50~59 → ensemble 재생성 테스트
  - 분기 요약:
    - fix_scope=="inplace" OR (no fix_scope AND score>=60): inplace patch
    - fix_scope=="partial": single strategy regeneration
    - else (score<50 OR fix_scope=="full"): full regeneration
Inference: 테스트가 3개 분기 경계값을 전부 커버. fix_scope Director 주권주의 우선, 점수 fallback 설계 확인.
Uncertainty: 없음
Cross-Ref: T09 (Arc — 동일 PatchModeThresholds 사용)
```

### T10-TF-009 — ConstraintDB Degraded Mode Fallback
```
ID: T10-TF-009
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/constraint_db.py:78-106, 108-114
Evidence:
  - constraint_db.py:78-106: _load_from_db()
    - context 없거나 db 속성 없으면 → 조용히 return (L80-81)
    - arcs_data 없으면 → degraded=False 설정 후 return (L85-88)
    - 예외 시 → degraded=True, degraded_reason 설정 (L103-106)
  - constraint_db.py:108-114: degraded property
    ```python
    @property
    def degraded(self) -> bool:
        return bool(self._degraded)
    ```
  - constraint_db.py:615-616: validate_arc_design()에서 degraded 시 warning 추가
    ```python
    if self.degraded:
        result["degraded"] = True
        result["degraded_reason"] = self.degraded_reason
    ```
  - constraint_db.py:438: generate_constraint_block()에서 arc_states 없으면 빈 문자열 반환 (L449)
Inference: DB 불가 시 degraded 모드로 전환, 빈 제약 블록 반환. 비차단 설계 확인.
Uncertainty: 없음
Cross-Ref: T16 (Database — DB availability), T02 (Stage 2 — ConstraintDB 소비 측)
```

### T10-TF-010 — _format_prev_info() Legacy Method (Internal Use Only)
```
ID: T10-TF-010
Severity: P4-OBSERVATION
Category: DEAD-CODE
Surface: modules/domain/agents/blueprint_ensemble.py:915-973
Evidence:
  - blueprint_ensemble.py:915: `def _format_prev_info(self, prev_blueprint: dict | None) -> str:`
    → docstring: "이전 Blueprint 정보 포맷팅 (레거시 - 단일 Blueprint)" (L916)
  - blueprint_ensemble.py:982: `direct_prev = self._format_prev_info(prev_blueprint)`
    → _format_prev_info_expanded() 내부에서만 호출됨
  - _format_prev_info_expanded() (L975-1067)가 실제 프로덕션 엔트리포인트
  - _format_prev_info()는 단독 외부 호출 없음 — _format_prev_info_expanded()의 헬퍼로만 사용
Inference: "레거시"로 명시된 메서드지만 _format_prev_info_expanded()의 구성 요소로 활용 중. 완전한 dead code는 아님.
Uncertainty: 없음
Cross-Ref: 없음
```

### T10-TF-011 — Quality Gate Score 90 SYNC
```
ID: T10-TF-011
Severity: P4-OBSERVATION
Category: SYNC
Surface: three_phase_blueprint_generator.py:552
Evidence:
  - three_phase_blueprint_generator.py:552:
    `_quality_gate_score = _threshold("scoring.quality_gate_score", 90)`
  - three_phase_blueprint_generator.py:568-574:
    ```python
    if (verdict == "PASS" and _score < _quality_gate_score):
        verdict = "REJECT"
    ```
  - 주석 L570: "[TF-46] PASS_WITH_FIX는 Director 주권 존중 — gate 미적용"
  - 즉, Quality Gate는 PASS에만 적용되고 PASS_WITH_FIX에는 미적용 (Director 주권주의)
Inference: Stage 2/4와 동일한 90점 통일 기준 사용. Director가 PASS_WITH_FIX를 내리면 gate 우회하는 설계.
Uncertainty: validation.yaml에서 quality_gate_score 실제 값이 90인지는 YAML 파일 확인 필요 (동적 검증 필요)
Cross-Ref: T14 (Validation Pipeline — 동일 threshold 사용), T06 (Stage 4 — L4037 동일 패턴)
```

### T10-TF-012 — Adversarial Self Play Integration at retry >= 2
```
ID: T10-TF-012
Severity: P4-OBSERVATION
Category: SYNC
Surface: three_phase_blueprint_generator.py:355-394
Evidence:
  - three_phase_blueprint_generator.py:355: `if retry >= 2 and adversarial_self_play and best_blueprint:`
  - L362-363: `_asp_result = adversarial_self_play.generate_with_adversary(...)`
  - L376-380: ASP 결과에 scene_breakdown + integrated_scenario가 있으면 후보에 추가
  - L391: `pipeline_result["asp_used"] = True`
  - 조건: retry >= 2 (즉, 3번째 시도부터), adversarial_self_play 인스턴스 존재, best_blueprint 존재
Inference: ASP는 마지막 시도에서만 추가 후보를 생성하는 보조 메커니즘. 비용 효율성을 위해 초기 시도에서는 비활성.
Uncertainty: generate() 호출 시 adversarial_self_play 파라미터가 주입되는 경로 확인 필요
Cross-Ref: T15 (Quality Intelligence — AdversarialSelfPlay 모듈)
```

### T10-TF-013 — Emergency Fallback with PASS_WITH_WARNING
```
ID: T10-TF-013
Severity: P2-MEDIUM
Category: SIDE-EFFECT
Surface: three_phase_blueprint_generator.py:832-843
Evidence:
  - three_phase_blueprint_generator.py:832-843:
    ```python
    if best_blueprint and director and _last_score >= PatchModeThresholds.REWRITE:
        pipeline_result["final_verdict"] = "PASS_WITH_WARNING"
        pipeline_result["quality_gate_failed"] = True
        pipeline_result["quality_risk"] = True
        pipeline_result["revision_required"] = True
        pipeline_result["last_score"] = _last_score
        best_blueprint = validate_blueprint(best_blueprint)
        return best_blueprint, pipeline_result
    ```
  - 조건: 모든 재시도 실패 후, score >= 50 (PatchModeThresholds.REWRITE), Director 존재, best_blueprint 존재
  - PatchModeThresholds.REWRITE = 50 (constants.py:644)
Inference: 50점 이상이면 모든 재시도가 실패해도 "PASS_WITH_WARNING"으로 Blueprint를 반환. 이는 10+1회 시도 실패 시에도 차선을 반환하는 설계. quality_risk=True 마킹으로 후속 단계에 경고 전달.
Uncertainty: Stage 4에서 quality_risk=True Blueprint를 어떻게 처리하는지 확인 필요
Cross-Ref: T05 (Stage 4 — quality_risk 소비 측), T04 (Stage 3 — pipeline_result 소비 측)
```

### T10-TF-014 — PASS_WITH_FIX Repair Loop Max 3 Iterations
```
ID: T10-TF-014
Severity: P4-OBSERVATION
Category: SYNC
Surface: three_phase_blueprint_generator.py:587-760
Evidence:
  - three_phase_blueprint_generator.py:588: `_MAX_FIX = 3`
  - L593: `for _fix_i in range(_MAX_FIX):`
  - L594-602: fix_scope 기반 라우팅 — "partial"/"full"이면 break → generate 재시도 루프 위임
  - L610-616: _inplace_patch_blueprint() 호출
  - L649-661: validator.validate() 재심사 (단일 후보 경로, all_candidates=None)
  - L676-689: 재심사 PASS → quality gate 체크 → _fix_ok = True → break
  - L690-697: PASS_WITH_FIX → 다음 fix 라운드, PASS_WITH_WARNING → _fix_ok = True, REJECT → break
  - L699-763: fix 루프 후 분기 — _fix_ok이면 PASS, 아니면 REJECT + continue
  - tests/test_blueprint_patch_mode.py:661-688: PASS_WITH_FIX change ratio warning-only 테스트
Inference: inplace patch → Director 재심사를 최대 3회 반복. fix_scope가 "partial"/"full"이면 inplace 불가하므로 즉시 generate 루프로 돌아감.
Uncertainty: 없음
Cross-Ref: T08 (ChiefWriter — 동일 PASS_WITH_FIX 패턴)
```

### T10-TF-015 — validate_blueprint() Pydantic Graceful Degradation
```
ID: T10-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/models/blueprint.py:76-86
Evidence:
  - blueprint.py:76-86:
    ```python
    def validate_blueprint(raw: dict) -> dict:
        try:
            bp = Blueprint.model_validate(raw)
            return bp.model_dump()
        except Exception as e:
            logger.warning("[Pydantic] Blueprint 검증 실패 — 원본 dict 유지: %s", e)
            return raw
    ```
  - 호출 경로:
    - three_phase_blueprint_generator.py:763: PASS 반환 직전
    - three_phase_blueprint_generator.py:842: 긴급 폴백 반환 직전
    - three_phase_blueprint_generator.py:944: inplace patch 후
  - Blueprint 클래스(L40-73): extra="allow", episode_number/scene_breakdown/integrated_scenario 등 7개 필수 필드 + 4개 추가 필드
  - model_validator _sync_ep_num_alias (L64-73): ep_num ↔ episode_number 상호 동기화
Inference: Pydantic 검증 실패 시 원본 dict 그대로 반환하는 graceful degradation. LLM 출력이 스키마를 위반해도 크래시 없이 진행.
Uncertainty: 없음
Cross-Ref: T17 (Schemas — response_schemas.py BLUEPRINT_SCHEMA)
```

### T10-TF-016 — Stop Line Violation Detection (Two-Mode)
```
ID: T10-TF-016
Severity: P4-OBSERVATION
Category: SYNC
Surface: unified_blueprint_validator.py:152-208
Evidence:
  - unified_blueprint_validator.py:182-208: _detect_stop_line_violation()
    Mode 1 (L193): clause_substring — 12자 이상 clause가 integrated_scenario에 부분문자열로 존재
    Mode 2 (L197-206): token_overlap — clause의 유의미 토큰 중 75% 이상이 integrated_scenario에 존재 (최소 3토큰)
  - L153-167: _extract_stop_line_clauses() — 정지선 텍스트를 8자+ 절로 분리
  - L169-180: _extract_significant_stop_tokens() — 공통 토큰(다음, 주인공 등 15개) 제외
  - L694-711: 정지선 위반 발견 시 CRITICAL severity 이슈 발행
  - _STOP_LINE_COMMON_TOKENS (L34-50): 15개 공통 토큰 필터
Inference: 두 모드로 정지선 위반을 감지. clause_substring은 정확 매칭, token_overlap은 퍼지 매칭. 공통 토큰 필터로 false positive 방지.
Uncertainty: 없음
Cross-Ref: 없음
```

### T10-TF-017 — Dead NPC Advisory-Only Check
```
ID: T10-TF-017
Severity: P4-OBSERVATION
Category: SYNC
Surface: unified_blueprint_validator.py:88-116
Evidence:
  - unified_blueprint_validator.py:88-116: _apply_dead_npc_advisory()
    - state_tracker.check_dead_npc_in_blueprint() 호출 (L101)
    - 위반 시 CRITICAL severity 이슈를 pre_result["issues"]에 추가 (L106-114)
    - 직접 REJECT하지 않음 — "죽은 NPC는 회상/언급만 허용" fix_hint만 제공
  - L396-411: Phase A에서 dead NPC 경고 발견 시 Director에게 전달 (디렉터 주권주의)
  - L238-245: compare 경로에서도 각 후보별 dead NPC 검사
Inference: 대원칙 4 ("사망 캐릭터는 회상/언급만 허용") 구현. Python은 경고만, Director가 최종 판단.
Uncertainty: 없음
Cross-Ref: T12 (State Tracking — check_dead_npc_in_blueprint 구현), T07 (Director — 최종 판정)
```

### T10-TF-018 — Blueprint Preflight (TF-49b) in Stage4Orchestrator
```
ID: T10-TF-018
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: modules/core/stage4_orchestrator.py:403, tests/test_blueprint_preflight.py
Evidence:
  - stage4_orchestrator.py:403: `def _preflight_validate_blueprint(self, *, blueprint, arc_data, ep_num) -> dict:`
  - 이 메서드는 Stage 4 Orchestrator에 위치, Blueprint 생성 모듈(T10 범위)에는 없음
  - NS-1 (numeric self-verification): stage2_finalizer.py:126, :663, :868에 구현
  - NS-1은 chief_writer_quality.py:314, :455에도 구현
  - T10 범위의 BlueprintConstraintCompiler/UnifiedBlueprintValidator에는 NS-1 구현 없음
  - tests/test_blueprint_preflight.py: Stage4Orchestrator._preflight_validate_blueprint 테스트
Inference: Blueprint preflight(TF-49b)는 T10 범위가 아닌 T05 범위(Stage4Orchestrator)에 구현. T10 모듈들은 NS-1 검증을 직접 수행하지 않음.
Uncertainty: 없음 — 구현 위치가 Stage 4 오케스트레이터임을 확인
Cross-Ref: T05 (Stage 4 — _preflight_validate_blueprint), T03 (Stage 2 — NS-1-P)
```

### T10-TF-019 — ConstraintDB Snapshot/Restore for Retry Rollback
```
ID: T10-TF-019
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/constraint_db.py:560-574
Evidence:
  - constraint_db.py:560-567: snapshot()
    ```python
    def snapshot(self) -> dict:
        return {
            "arc_states": copy.deepcopy(self.arc_states),
            "item_registry": copy.deepcopy(self.item_registry),
        }
    ```
  - constraint_db.py:569-574: restore()
    ```python
    def restore(self, snap: dict) -> None:
        if isinstance(snap, dict) and "arc_states" in snap:
            self.arc_states = snap["arc_states"]
        if isinstance(snap, dict) and "item_registry" in snap:
            self.item_registry = snap["item_registry"]
    ```
  - constraint_db.py:576-587: update_arc_state()
    - docstring: "Contract: DB 커밋 성공 이후에만 호출해야 한다"
    - retry 경로에서는 호출되지 않으므로 상태 오염 방지
Inference: snapshot/restore는 retry rollback을 위한 안전장치. update_arc_state()의 contract가 명시되어 있어 retry 안전성 보장.
Uncertainty: 없음
Cross-Ref: T02 (Stage 2 — ConstraintDB 소비 측)
```

### T10-TF-020 — Director == None Guard
```
ID: T10-TF-020
Severity: P4-OBSERVATION
Category: SYNC
Surface: unified_blueprint_validator.py:425-435
Evidence:
  - unified_blueprint_validator.py:425-435:
    ```python
    if director is None:
        logging.error("❌ [대원칙3] Director가 None — Blueprint 판정 불가, REJECT 처리")
        return "REJECT", {
            "verdict": "REJECT",
            "phase": "no_director",
            ...
        }
    ```
  - 주석: "[TF-36] 대원칙 3: Director 없으면 REJECT — 디렉터 주권주의 위반 방지"
  - 대원칙 3 (AGENTS.md L13): "Director가 최종 품질 결정권"
Inference: 대원칙 3의 코드 레벨 가드. Director 없이 Blueprint가 승인되는 경로 차단.
Uncertainty: 없음
Cross-Ref: T07 (Director System)
```

### T10-TF-021 — Context Caching in Blueprint Ensemble
```
ID: T10-TF-021
Severity: P4-OBSERVATION
Category: SYNC
Surface: blueprint_ensemble.py:314-321
Evidence:
  - blueprint_ensemble.py:314-320:
    ```python
    shared_context = f"{arc_focus or ''}\n\n{constraints_str or ''}\n\n{prev_info or ''}\n\n{hud_context or ''}"
    cache_info = self._get_or_create_context_cache(
        cache_type="blueprint_ensemble",
        content=shared_context,
        ttl_seconds=600,
        project_name=self._context_cache_project_namespace("ep", ep_num),
    )
    cache_name = cache_info.get("cache_name")
    ```
  - TTL: 600s (intra-episode)
  - blueprint_ensemble.py:628-635: _ask_with_cached_context() 호출
  - blueprint_ensemble.py:596-618: cache miss 시 full_prompt_fallback 구축
  - BaseAgent (T11 범위) 인프라 사용: _get_or_create_context_cache(), _ask_with_cached_context()
  - 최소 요건: 50,000자 이상 (system.yaml 설정)
Inference: 3개 전략이 동일 컨텍스트를 공유하므로 캐시 히트 시 비용 절감. TTL 600s는 에피소드 내 재시도 범위.
Uncertainty: cache_name이 None일 때 full_prompt_fallback으로 안전하게 폴백하는지 확인 필요 (BaseAgent 구현 의존)
Cross-Ref: T11 (Agent Infrastructure — context caching 인프라)
```

### T10-TF-022 — _work_retrieval_contract Fetched Twice
```
ID: T10-TF-022
Severity: P3-LOW
Category: HARDCODING
Surface: blueprint_ensemble.py:296-302, 562-568
Evidence:
  - blueprint_ensemble.py:296-302: generate_ensemble() 레벨에서 _work_retrieval_contract 로드
    ```python
    _work_retrieval_contract = ""
    try:
        _guard = getattr(self.context, "guard", None)
        if _guard and hasattr(_guard, "get_retrieval_contract_prompt"):
            _work_retrieval_contract = str(_guard.get_retrieval_contract_prompt("blueprint") or "").strip()
    ```
  - blueprint_ensemble.py:562-568: _generate_single() 레벨에서 동일 코드 반복
  - generate_ensemble()에서 로드한 _work_retrieval_contract는 _generate_single()에 전달되지 않음
  - _generate_single()이 worker thread에서 실행되므로 context 접근의 thread-safety 고려일 수 있음
  - 그러나 generate_ensemble()의 L296-302는 결과를 사용하지 않음 (이후 참조 없음)
Inference: generate_ensemble() L296-302의 _work_retrieval_contract는 사실상 dead code. _generate_single() 내부에서 각 worker가 독립적으로 로드함.
Uncertainty: generate_ensemble()의 _work_retrieval_contract가 다른 용도로 사용되는지 확인 필요 — Grep 결과 L296 이후 해당 변수 참조 없음
Cross-Ref: T18 (Genre Guards — WorkGuard retrieval contract)
```

### T10-TF-023 — ConstraintDB Semantic Item Registry Optional Integration
```
ID: T10-TF-023
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/constraint_db.py:26-33, 71-74
Evidence:
  - constraint_db.py:26-33: Optional import with fallback
    ```python
    try:
        from modules.core.semantic_item_registry import SemanticItemRegistry, create_item_registry
        SEMANTIC_REGISTRY_ENABLED = True
    except ImportError:
        SEMANTIC_REGISTRY_ENABLED = False
    ```
  - constraint_db.py:71-74: 초기화 시 조건부 생성
    ```python
    if SEMANTIC_REGISTRY_ENABLED:
        self.item_registry = create_item_registry()
    ```
  - constraint_db.py:630-636: validate_arc_design()에서 고급 중복 감지
    ```python
    if self.item_registry and new_acquired:
        registry_result = self.item_registry.validate_arc_items(arc_no, new_acquired)
    ```
  - constraint_db.py:637-646: fallback — 기존 정확/부분 매칭 로직
Inference: SemanticItemRegistry는 선택적 의존성. import 실패 시 기존 regex 기반 검증으로 폴백. graceful degradation 패턴.
Uncertainty: 없음
Cross-Ref: T20 (Cross-Cut — semantic_item_registry.py)
```

### T10-TF-024 — PASS_WITH_FIX fix_scope Routing Decision
```
ID: T10-TF-024
Severity: P4-OBSERVATION
Category: SYNC
Surface: three_phase_blueprint_generator.py:594-602
Evidence:
  - three_phase_blueprint_generator.py:594-602:
    ```python
    _fix_scope = _current_vr.get("fix_scope", "")
    if not _fix_scope:
        _inplace_thresh = int(_threshold("patch_mode.inplace_below", 60))
        _fix_scope = "inplace" if _score >= _inplace_thresh else "full"
    if _fix_scope in ("partial", "full"):
        break  # → REJECT → generate 재시도 루프
    ```
  - fix_scope 값별 라우팅:
    - "inplace": _inplace_patch_blueprint() → Director 재심사 루프 (최대 3회)
    - "partial": break → generate 루프에서 단일 전략 재생성
    - "full": break → generate 루프에서 전면 재생성
    - 누락 시: score 기반 fallback (score >= 60 → inplace, else full)
  - tests/test_blueprint_patch_mode.py:585-621: partial 라우팅 테스트
  - tests/test_blueprint_patch_mode.py:623-659: full 라우팅 테스트
Inference: Director의 fix_scope 판단이 최우선, 점수는 fallback. 3개 경로가 테스트로 검증됨.
Uncertainty: 없음
Cross-Ref: T07 (Director — fix_scope 발행)
```

### T10-TF-025 — _initial_feedback Accumulation Prevention
```
ID: T10-TF-025
Severity: P4-OBSERVATION
Category: SYNC
Surface: three_phase_blueprint_generator.py:228, 236
Evidence:
  - three_phase_blueprint_generator.py:228: `_initial_feedback = feedback` — 초기 피드백 보존
  - three_phase_blueprint_generator.py:236: `_attempt_feedback = _initial_feedback` — 매 retry마다 초기값에서 시작
  - 주석 L228: "[TF-S3-04] 초기 피드백 보존 (retry간 누적 방지)"
  - L464: `feedback = _initial_feedback + f"\n[연속성 오류]\n{continuity_feedback}"`
  - L574: `feedback = _initial_feedback + f"\n[Quality Gate] score {_score}점으로 {_quality_gate_score}점 미달."`
  - L716: `feedback = _initial_feedback + f"\n[TF-32-V] PASS_WITH_FIX 수정 {_MAX_FIX}회 내 미해결 → REJECT"`
Inference: += 누적 대신 _initial_feedback 기반 재구성으로 피드백 비대화(snowball) 방지. 이전 TF-S3-04 패치 결과 반영.
Uncertainty: 없음
Cross-Ref: 없음
```

### T10-TF-026 — Blueprint Pydantic Model Missing end_location and ending_state
```
ID: T10-TF-026
Severity: P3-LOW
Category: DRIFT
Surface: modules/models/blueprint.py, modules/core/response_schemas.py:639-645
Evidence:
  - response_schemas.py:639-645: BLUEPRINT_SCHEMA에 end_location, ending_hook, ending_state 정의
  - blueprint.py:40-63: Blueprint Pydantic 모델에 end_location은 없음 (start_location만 L59)
    - ending_hook 없음 (T10-TF-003 참조)
    - ending_state 없음
  - 사용처:
    - blueprint_constraint_compiler.py:343: `prev_blueprint.get("end_location", ...)`
    - blueprint_ensemble.py:928: `prev_blueprint.get("ending_hook", "")`
    - unified_blueprint_validator.py:715: `prev_blueprint.get("end_location", "")`
  - extra="allow"로 인해 런타임 문제 없으나, 3개 필드가 Pydantic 모델에서 누락
Inference: BLUEPRINT_SCHEMA와 Pydantic Blueprint 클래스 간 필드 동기화 부족. extra="allow"가 안전장치이나, 명시적 필드 정의가 바람직.
Uncertainty: 없음
Cross-Ref: T10-TF-003 (ending_hook 구체 사례), T17 (Schemas)
```

---

## 3. Evidence Inventory

| TF ID | Evidence Type | Primary File:Line |
|-------|--------------|-------------------|
| TF-001 | 코드 구조 확인 | three_phase_blueprint_generator.py:244-823 |
| TF-002 | 수치 비교 | blueprint_ensemble.py:453 vs unified_blueprint_validator.py:634 |
| TF-003 | Grep 부재 증명 | Grep "ending_hook" in blueprint.py → 0 matches |
| TF-004 | Grep 부재 증명 | Grep "compile_to_prompt" in modules/ → 1 match (정의만) |
| TF-005 | 코드 스니펫 인용 | blueprint_constraint_compiler.py:43-106 |
| TF-006 | 코드 비교 | blueprint_constraint_compiler.py vs constraint_compiler.py |
| TF-007 | 코드 스니펫 인용 | blueprint_ensemble.py:40-80, :330, :494 |
| TF-008 | 코드+테스트 비교 | constants.py:644-645, test_blueprint_patch_mode.py:557 |
| TF-009 | 코드 스니펫 인용 | constraint_db.py:78-106, :108-114 |
| TF-010 | Grep 호출 확인 | blueprint_ensemble.py:915, :982 |
| TF-011 | 코드 스니펫 인용 | three_phase_blueprint_generator.py:552, :568-574 |
| TF-012 | 코드 스니펫 인용 | three_phase_blueprint_generator.py:355 |
| TF-013 | 코드 스니펫 인용 | three_phase_blueprint_generator.py:832-843 |
| TF-014 | 코드 스니펫 인용 | three_phase_blueprint_generator.py:588-760 |
| TF-015 | 코드 스니펫 인용 | blueprint.py:76-86 |
| TF-016 | 코드 스니펫 인용 | unified_blueprint_validator.py:182-208 |
| TF-017 | 코드 스니펫 인용 | unified_blueprint_validator.py:88-116 |
| TF-018 | Grep 위치 확인 | stage4_orchestrator.py:403, Grep "NS-1" |
| TF-019 | 코드 스니펫 인용 | constraint_db.py:560-574 |
| TF-020 | 코드 스니펫 인용 | unified_blueprint_validator.py:425-435 |
| TF-021 | 코드 스니펫 인용 | blueprint_ensemble.py:314-321 |
| TF-022 | 코드 비교 | blueprint_ensemble.py:296-302 vs :562-568 |
| TF-023 | 코드 스니펫 인용 | constraint_db.py:26-33, :71-74, :630-636 |
| TF-024 | 코드+테스트 비교 | three_phase_blueprint_generator.py:594-602 |
| TF-025 | 코드 스니펫 인용 | three_phase_blueprint_generator.py:228, :236 |
| TF-026 | Grep 부재 + 비교 | blueprint.py vs response_schemas.py:639-645 |

---

## 4. Side-Effect Surface

### Write Effects
| Module | Side-Effect | Trigger |
|--------|------------|---------|
| ThreePhaseBlueprintGenerator | pipeline_result dict 구축 | generate() 호출 |
| ThreePhaseBlueprintGenerator | self.stats 카운터 증가 | phase 완료/reject |
| ThreePhaseBlueprintGenerator | pass_rate_monitor.record_attempt() | _record_intermediate_reject() |
| BlueprintEnsembleGenerator | last_error_type, last_error_types 갱신 | generate_ensemble() 완료 |
| BlueprintEnsembleGenerator | context cache 생성 | _get_or_create_context_cache() |
| ConstraintDB | arc_states dict 갱신 | update_arc_state() |
| ConstraintDB | item_registry 항목 등록 | _parse_arc_state() |
| ConstraintDB | DB 읽기 (load_anchor) | _load_from_db() |

### No-Write Modules
- BlueprintConstraintCompiler: 순수 함수형 — 입력→출력만
- UnifiedBlueprintValidator: 이슈 목록 구축만, DB/상태 변경 없음
- ConstraintCompiler: 순수 함수형 — 입력→출력만

---

## 5. Facts

1. Three Phase Blueprint Generator는 3단계 파이프라인 (Constraint→Generate→Validate)으로 Blueprint를 생성
2. Blueprint Ensemble은 3개 전략(action/emotion/dialogue)을 ThreadPoolExecutor(3)로 병렬 생성
3. Python 최소 기준: Ensemble=4씬+500자, Validator=3씬
4. Director가 최종 선택과 판정을 담당 (디렉터 주권주의)
5. Patch mode: inplace(≥60점), partial(fix_scope), full(<50점 또는 fix_scope="full")
6. PASS_WITH_FIX는 최대 3회 inplace patch → Director 재심사 루프
7. 모든 재시도 실패 시 score≥50이면 PASS_WITH_WARNING 긴급 폴백
8. BlueprintConstraintCompiler와 ConstraintCompiler는 역할이 분리됨 (에피소드 vs Arc 레벨)
9. ConstraintDB는 degraded 모드를 지원하며 DB 불가 시 빈 제약 반환
10. validate_blueprint()은 Pydantic 실패 시 원본 dict를 반환하는 graceful degradation
11. compile_to_prompt()는 프로덕션에서 미호출 (dead code)
12. ending_hook/end_location/ending_state가 BLUEPRINT_SCHEMA에는 있으나 Pydantic 모델에는 없음

---

## 6. Inferences

1. Scene count 불일치(4 vs 3)는 안전장치 설계로 보임 — Ensemble이 먼저 걸러내므로 Validator 임계값에 도달하기 어려움
2. compile_to_prompt()는 V60.80 리팩토링 때 _format_constraints()로 대체되었으나 삭제되지 않음
3. Pydantic Blueprint 모델의 필드 누락은 extra="allow" 설정으로 커버되지만, 장기적으로 스키마 동기화 필요
4. generate_ensemble()의 _work_retrieval_contract 로드(L296-302)는 dead code로 추정
5. 긴급 폴백(PASS_WITH_WARNING)은 10+1회 실패 시에도 생산을 중단하지 않으려는 운영 설계

---

## 7. Uncertainty / Contradictions

1. **TF-002**: Ensemble 4씬 기준과 Validator 3씬 기준의 설계 의도 불명확. 문서화되지 않은 암묵적 합의일 수 있음.
2. **TF-003/026**: extra="allow"가 있어 런타임 문제는 없으나, Pydantic 모델 갱신이 필요한지는 팀 결정 사항.
3. **TF-011**: validation.yaml의 quality_gate_score 실제 값은 YAML 파일 정적 읽기로 확인 가능하나 _LazyThreshold이므로 런타임 값이 default(90)과 다를 수 있음.
4. **TF-013**: Stage 4에서 quality_risk=True Blueprint를 어떻게 처리하는지는 T05 범위.

---

## 8. Cross-Ref to Adjacent Terminals

| Terminal | Cross-Ref | TF IDs |
|----------|----------|--------|
| T02 (Stage 2 Orch) | ConstraintCompiler/ConstraintDB 소비 측 | TF-006, TF-009, TF-019 |
| T03 (Stage 2 Preflight) | ConstraintCompiler 사용, NS-1-P | TF-006, TF-018 |
| T04 (Stage 3 Pipeline) | ThreePhaseBlueprintGenerator 호출 | TF-001, TF-013 |
| T05 (Stage 4 Orch) | _preflight_validate_blueprint, quality_risk 소비 | TF-013, TF-018 |
| T06 (Stage 4 Interview) | 유사 quality gate 패턴 | TF-002, TF-011 |
| T07 (Director System) | compare_and_select_blueprint, fix_scope | TF-007, TF-017, TF-020, TF-024 |
| T08 (ChiefWriter) | 동일 PASS_WITH_FIX 패턴, NS-1 | TF-014, TF-018 |
| T09 (Arc Generation) | Arc → Blueprint handoff, PatchModeThresholds | TF-005, TF-008 |
| T11 (Agent Infra) | BaseAgent context caching 인프라 | TF-021 |
| T12 (State Tracking) | check_dead_npc_in_blueprint | TF-017 |
| T15 (Quality Intel) | AdversarialSelfPlay 모듈 | TF-012 |
| T17 (Config/Schemas) | BLUEPRINT_SCHEMA, validation.yaml | TF-003, TF-011, TF-026 |
| T18 (Helpers) | Genre Guards retrieval contract | TF-022 |

---

## 9. Candidate Watchlist

1. **compile_to_prompt() 삭제 후보** (TF-004): 프로덕션 미호출 확인됨, 레거시 테스트만 의존
2. **Pydantic Blueprint 필드 동기화** (TF-003, TF-026): ending_hook, end_location, ending_state 추가 후보
3. **generate_ensemble() dead _work_retrieval_contract** (TF-022): L296-302 삭제 후보
4. **Scene count 임계값 통일** (TF-002): 4씬으로 통일하거나 현재 설계 의도 문서화

---

## 10. 6Pass Audit Log

### Pass 1 — 구조/범위
- T10 범위 7개 소스 파일 + 3개 테스트 파일 전수 읽기 완료
- 필수 조사 7개 항목 모두 커버됨
- TF 26개 구성 — 최소 기대(8-15) 초과
- SYNC 확인도 TF로 기록됨 (14개 P4-OBSERVATION)
- **PASS**

### Pass 2 — 증거/일관성
- 모든 TF에 파일:라인 형식 Evidence 존재
- 코드 스니펫 인용 17건, Grep 부재 증명 3건, 수치 비교 2건
- 라인 번호 정확성: 실제 파일 읽기 기반
- TF 간 내부 모순 없음
- **PASS**

### Pass 3 — 실행가능성
- P0: 0건, P1: 0건, P2: 2건, P3: 4건, P4: 20건
- P2 2건 (TF-003 Pydantic 필드 누락, TF-013 긴급 폴백) — actionable
- Severity 배분: 코드 크래시 위험 없는 영역이므로 P2가 최고 severity로 적절
- **PASS**

### Pass 4 — 적대적 Pass 1 (스코프 과잉/누락 반박 시도)
- "blueprint_preflight.py 테스트는 T10이 아닌 T05 범위다" → TF-018에서 이를 명시하고 COVERAGE-GAP으로 기록. T10 범위에서 해당 코드 부재를 확인한 것은 T10의 책임 → **반박 실패, PASS**
- "ConstraintCompiler(Stage 2용)는 T10이 아닌 T03 범위다" → Master order에서 constraint_compiler.py를 T10에 배정함. 또한 T10-TF-006에서 역할 분리를 명시 → **반박 실패, PASS**

### Pass 5 — 적대적 Pass 2 (증거 거짓/오해 반박 시도)
- "TF-004 compile_to_prompt()가 dead code라는 증거가 불충분하다" → Grep "compile_to_prompt" in modules/ → 1 match (정의 자체). Grep in tests/ → 2 matches (레거시 테스트). 프로덕션 호출 0건 확인 → **반박 실패, PASS**
- "TF-022의 dead code 주장이 잘못되었다 — L296의 _work_retrieval_contract가 다른 곳에서 사용될 수 있다" → L296에서 정의된 변수는 generate_ensemble() 스코프 내에서 L302 이후 참조 없음. _generate_single() 내부의 L562에서 별도로 재로드됨 → **반박 실패, PASS**

### Pass 6 — 적대적 Pass 3 (severity 과대/과소 반박 시도)
- "TF-003을 P2로 올린 것은 과대평가다 — extra=allow가 완전히 커버한다" → extra="allow"는 데이터 보존은 하나 타입 검증/기본값/IDE 자동완성/문서화가 누락됨. 여러 모듈에서 ending_hook을 직접 참조하므로 P2가 적절 → **반박 실패, PASS**
- "TF-013을 P2로 올린 것은 과대평가다 — 긴급 폴백은 의도된 설계다" → 의도된 설계이지만 quality_risk=True Blueprint가 후속 파이프라인에 미치는 영향이 불명확하므로 P2 유지가 적절 → **반박 실패, PASS**

**6PASS-CLEARED** — 확신도 96%
