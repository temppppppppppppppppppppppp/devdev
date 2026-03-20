# T03 — Stage 2 Preflight, Finalizer & Optimizer Survey

**6PASS-CLEARED** | COLLECTOR ONLY | NO EXECUTION AUTHORITY

**Terminal**: T03
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Confidence**: 96%
**Adjacent Terminals**: T02 (Stage 2 Orchestration & Context), T09 (Arc Generation & Validation), T14 (Validation Pipeline)

---

## 1. Scope & Files

| File | Lines | Role |
|------|-------|------|
| `modules/core/stage2_preflight.py` | 1,801 | Preflight 분석, 벡터 검색, FourPhase 실행, StateTracker enrichment |
| `modules/core/stage2_finalizer.py` | 2,165 | Director 심사, PASS/REJECT 분기, DB writes, StateTracker rollback |
| `modules/core/stage2_optimizer.py` | 1,213 | 6-component optimizer (StateSnapshot, AutoCorrector, Constraints, Feedback, FailureMemory, FewShot) |
| **Tests** | | |
| `tests/test_stage2_preflight.py` | 796 | Preflight unit tests |
| `tests/test_stage2_preflight_helpers.py` | 1,194 | Preflight helper tests |
| `tests/test_stage2_finalizer.py` | 663 | Finalizer unit tests |

**Total**: 5,179 source lines + 2,653 test lines

---

## 2. TF Registry (18 TFs)

### T03-TF-001 — max_attempts 표시 vs 실제값 불일치
```
ID: T03-TF-001
Severity: P3-LOW
Category: CONTRADICTION
Surface: modules/core/stage2_preflight.py:799, :843
Evidence:
  - stage2_preflight.py:799
    `max_attempts = int(_threshold("retry.analyst_max_attempts", 5))`
    fallback default = 5
  - stage2_preflight.py:843 (in _preflight_arc_analysis)
    `f"(시도 {attempt + 1}/{RetryLimits.ANALYST_MAX_ATTEMPTS})"`
    RetryLimits.ANALYST_MAX_ATTEMPTS = 10 (constants.py:103)
  - config/settings/validation.yaml:96
    `analyst_max_attempts: 10`
  - 정상 운영 시 YAML에서 10을 읽으므로 max_attempts=10, 표시도 10 → 일치
  - YAML 키 누락 시 fallback default=5이나 표시는 10 → DRIFT
Inference: YAML 키가 정상이면 문제없지만, fallback default(5)와 상수(10)가 다르다.
  _preflight_state_setup이 반환하는 max_attempts는 orchestrator의 attempt loop을
  제어하지만, UI 메시지는 별도 상수를 참조하므로 decoupled 상태.
Uncertainty: 실제 운영에서 YAML 키 누락은 극히 드묾. 표시 불일치 영향은 사용자 혼란에 한정.
Cross-Ref: T17 (Config 키 참조 정합성)
```

### T03-TF-002 — Stage2Optimizer 4개 메서드 미호출 (Dead Code)
```
ID: T03-TF-002
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/core/stage2_optimizer.py:1158, :1179, :1183, :1196
Evidence:
  - stage2_optimizer.py:1158 `def record_result(...)`
  - stage2_optimizer.py:1179 `def generate_focused_feedback(...)`
  - stage2_optimizer.py:1183 `def get_stats(...)`
  - stage2_optimizer.py:1196 `def print_stats(...)`
  - Grep `stage2_optimizer\.(record_result|generate_focused_feedback|print_stats|get_stats)`
    in modules/ → 0 matches
  - 반면 같은 클래스의 다른 메서드는 사용됨:
    - `generate_optimized_prompt` → stage2_preflight.py:921
    - `post_process_arc` → stage2_validation_pipeline.py:372
    - `failure_memory.record_failure` → stage2_finalizer.py:1970
    - `failure_memory.clear_arc_failures` → stage2_finalizer.py:1764
Inference: record_result, generate_focused_feedback, get_stats, print_stats는 Stage2Optimizer
  설계 시 의도되었으나 production wiring에서 누락됨. failure_memory는 직접 접근으로
  사용 중이므로 record_result 래퍼가 bypass된 상태.
Uncertainty: 없음 — grep 0 matches로 확정.
Cross-Ref: T02 (Stage 2 Orchestration)
```

### T03-TF-003 — "Preflight" Enrichment의 대규모 StateTracker 변형
```
ID: T03-TF-003
Severity: P2-MEDIUM
Category: SIDE-EFFECT
Surface: modules/core/stage2_preflight.py:1596-1727
Evidence:
  - stage2_preflight.py:1600 `extract_npc_deaths_from_arc(refined_arc)`
  - stage2_preflight.py:1601 `extract_skill_acquisitions_from_arc(refined_arc)`
  - stage2_preflight.py:1602-1604 `extract_npc_info_from_arc(...)`, `extract_resolved_plots_from_arc(...)`
  - stage2_preflight.py:1607-1613 entity_destructions, npc_personality, npc_npc_relationships, item_states, plot_mentions
  - stage2_preflight.py:1622 `_populate_genre_registries_from_arc(refined_arc)`
  - stage2_preflight.py:1630 `extract_financial_events_from_arc(refined_arc)`
  - stage2_preflight.py:1656-1702 dialogue_styles, time_markers, injuries, companions, commitments, emotion, relationships, npc_injuries, npc_movements
  - stage2_preflight.py:1706-1707 `generate_arc_summary()` → `save_v20_anchor(f"arc_summary_{global_arc_no}", ...)`
  - stage2_preflight.py:1715 `cleanup_npc_registry_with_llm(global_arc_no)` (매 5 Arc)
  - stage2_preflight.py:1631-1633 `save_v20_anchor("financial_registry", ...)` (investment 장르)
  - 총 15+ StateTracker extract 호출 + 2개 DB anchor 저장 + 1개 LLM 정리 호출
Inference: "preflight" 네이밍과 달리 _preflight_enrichment는 대규모 상태 변형 + DB 쓰기를
  수행함. FourPhase 생성 성공 시에만 실행되며, Director REJECT 시 st_snapshot으로 롤백됨.
  설계 의도는 이해되나, 메서드명이 부작용의 규모를 숨김.
Uncertainty: 의도적 설계인지 역사적 누적인지 불확실. 롤백 메커니즘이 있으므로 기능 결함은 아님.
Cross-Ref: T12 (State Tracking), T01 (SovereignApp — write-back)
```

### T03-TF-004 — Finalizer DB Write Surface 전수
```
ID: T03-TF-004
Severity: P4-OBSERVATION
Category: SIDE-EFFECT
Surface: modules/core/stage2_finalizer.py (9개 DB write 경로)
Evidence:
  1. stage2_finalizer.py:1335 `save_v20_anchor("arcs", all_refined_arcs)` — 핵심 Arc 데이터
  2. stage2_finalizer.py:1383 `upsert_arc_dependency(from_arc, to_arc, "causes", ...)` — Arc 인과 의존
  3. stage2_finalizer.py:1392 `upsert_arc_dependency(_prereq, _arc_no, "requires", "")` — 명시 prerequisite
  4. stage2_finalizer.py:1439 `save_cost_record(...)` — PASS 비용 기록
  5. stage2_finalizer.py:1704 `save_stage_attempt(stage=2, verdict="PASS", ...)` — PASS 시도 기록
  6. stage2_finalizer.py:1727 `save_director_selection(...)` — Director 선택 기록
  7. stage2_finalizer.py:1506 `save_v20_anchor(f"volume_summary_{_vol_no}", ...)` — 볼륨 요약 (매 5 Arc)
  8. stage2_finalizer.py:1527 `save_v20_anchor("series_summary", ...)` — 시리즈 요약 갱신
  9. stage2_finalizer.py:1904 `save_cost_record(...)` — REJECT 비용/메타 기록
  - REJECT 경로: stage2_finalizer.py:1853 `save_stage_attempt(stage=2, verdict="REJECT", ...)`
  - REJECT 경로: stage2_finalizer.py:1877 `save_director_selection(...)` (REJECT)
  - Preflight 경로: stage2_preflight.py:1707 `save_v20_anchor(f"arc_summary_{global_arc_no}", ...)`
  - Preflight 경로: stage2_preflight.py:1632 `save_v20_anchor("financial_registry", ...)`
Inference: PASS 시 최소 6개 DB write, REJECT 시 최소 3개 DB write 발생.
  volume_summary/series_summary는 ARCS_PER_VOLUME(5) 주기로 추가 LLM 호출 + write.
Uncertainty: 없음 — grep으로 전수 확인.
Cross-Ref: T16 (Database, Persistence & Logging)
```

### T03-TF-005 — Quality Gate Score SYNC 확인
```
ID: T03-TF-005
Severity: P4-OBSERVATION
Category: SYNC
Surface: config/settings/validation.yaml:34, modules/core/stage2_finalizer.py:762
Evidence:
  - validation.yaml:34 `quality_gate_score: 90`
  - stage2_finalizer.py:762 `_quality_gate_score = _threshold("scoring.quality_gate_score", 90)`
  - 코드 fallback default(90)와 YAML 값(90)이 일치
  - stage2_finalizer.py:1041에서 `_score < _quality_gate_score` 비교 → REJECT 전환
  - stage2_finalizer.py:968에서 PASS_WITH_FIX 재심사 시에도 동일 gate 적용
Inference: Quality gate score는 YAML과 코드 fallback이 일치하며, PASS/PASS_WITH_FIX
  양 경로에서 일관되게 적용됨.
Uncertainty: 없음.
Cross-Ref: T17 (Config), T14 (Validation Pipeline)
```

### T03-TF-006 — CRITICAL_MISSING_THRESHOLD SYNC 확인
```
ID: T03-TF-006
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/constants.py:121, modules/core/stage2_finalizer.py:1211
Evidence:
  - constants.py:121 `CRITICAL_MISSING_THRESHOLD = 3`
  - stage2_finalizer.py:1211
    `if len(critical_missing) >= RecoveryLimits.CRITICAL_MISSING_THRESHOLD:`
  - critical_missing에 추가되는 필드: hybrid_composition, joint_docs, status_shadow (3개)
  - 3개 모두 누락 시 threshold=3에 도달 → "핵심 데이터 과다 누락" 판정
Inference: 3개 필드가 검사 대상이고 threshold도 3이므로, 모두 누락 시에만 트리거.
  1-2개 누락은 기본값 주입 후 계속 진행.
Uncertainty: 없음.
Cross-Ref: None
```

### T03-TF-007 — ArcAutoCorrector 10-Step Correction Pipeline
```
ID: T03-TF-007
Severity: P4-OBSERVATION
Category: SIDE-EFFECT
Surface: modules/core/stage2_optimizer.py:237-289
Evidence:
  - stage2_optimizer.py:250 Step 0: _sanitize_tactical_meta_terms (메타 용어 치환)
  - stage2_optimizer.py:253 Step 1: _remove_duplicate_items (중복 아이템 제거)
  - stage2_optimizer.py:256 Step 2: _check_equipment_continuity (소지품 연속성, advisory-only)
  - stage2_optimizer.py:259 Step 3: _fix_start_location (시작 위치 자동 수정)
  - stage2_optimizer.py:262 Step 4: _fix_start_state (시작 상태 계승)
  - stage2_optimizer.py:265 Step 5: _fix_joint_docs (joint_docs 자동 추출)
  - stage2_optimizer.py:268 Step 5-1: _sync_final_location (위치 동기화)
  - stage2_optimizer.py:271 Step 5-2: _check_tactical_location_consistency (tactical↔end 위치, advisory)
  - stage2_optimizer.py:274-275 Step 6: _strip_wuxia_fields (비무협 장르 전용)
  - stage2_optimizer.py:278 Step 7: _ensure_required_fields (필수 필드 보장)
  - stage2_optimizer.py:281 Step 8: _filter_abstract_items_consumed (추상 개념 제거)
  - stage2_optimizer.py:284 Step 9: _normalize_internal_energy (내공 0-100% 클램프)
  - stage2_optimizer.py:287 Step 10: _check_asset_growth_rate (자산 성장률 200% 상한, advisory)
  - 호출 경로: stage2_validation_pipeline.py:372 `self.ctx.stage2_optimizer.post_process_arc(...)`
Inference: 10 단계 중 실제 수정은 Step 0,1,3,4,5,5-1,6,7,8,9. Step 2,5-2,10은 advisory-only.
  corrections_made 리스트로 모든 변경 사항 추적됨.
Uncertainty: 없음.
Cross-Ref: T09 (Arc Generation — arc data 구조)
```

### T03-TF-008 — PASS_WITH_FIX 루프 최대 3회 하드코딩
```
ID: T03-TF-008
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/stage2_finalizer.py:793
Evidence:
  - stage2_finalizer.py:793 `_MAX_FIX = 3`
  - stage2_finalizer.py:801 `for _fix_i in range(_MAX_FIX):`
  - validation.yaml에 해당 키 없음 (grep "max_fix" in config/ → 0 matches)
  - 루프 탈출 조건:
    1. fix_scope 누락 → break (L805-807)
    2. fix_scope == "partial"/"full" → break (L808-810)
    3. _inplace_patch_arc 실패 → break (L830-831)
    4. 재심사 PASS + score >= quality_gate → _fix_ok=True, break (L967-980)
    5. 재심사 REJECT → break (L988-989)
    6. 3회 소진 → 루프 종료
Inference: 하드코딩이지만 PASS_WITH_FIX는 이미 거의 통과 가능한 Arc에 대한 미세 수정이므로
  3회는 합리적. Config 이동 시 `patch_mode.max_inplace_fix` 키 권장.
Uncertainty: 없음.
Cross-Ref: T06 (Stage 4 — PASS_WITH_FIX 유사 루프 비교)
```

### T03-TF-009 — StateTracker Rollback 6개 지점 대칭성
```
ID: T03-TF-009
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage2_finalizer.py (6개 rollback 지점)
Evidence:
  - 모든 rollback 지점은 동일 패턴:
    ```python
    for _k, _v in st_snapshot.items():
        if hasattr(_st, _k):
            setattr(_st, _k, _v)
    ```
  1. L1057-1065: QualityGate REJECT + ConstraintDB restore
  2. L1104-1110: validate_arc_data_fields 실패 + ConstraintDB restore
  3. L1222-1228: critical_missing 초과 + ConstraintDB restore
  4. L1237-1243: validate_arc_integrity 실패 + ConstraintDB restore
  5. L1358-1370: DB commit 실패 + ConstraintDB restore
  6. L1567-1576: Director REJECT (ConstraintDB rollback은 상위에서 처리됨)
  - ConstraintDB snapshot: stage2_finalizer.py:531-536
    `constraint_db.snapshot()` at entry, `constraint_db.restore(snap)` at rollback
  - constraint_db.py:560 `def snapshot(self)`, :569 `def restore(self, snap)`
Inference: 6개 지점 모두 StateTracker rollback 패턴 일관. 5개 지점에서 ConstraintDB
  대칭 rollback도 수행. st_snapshot은 stage2_preflight.py:1568-1592에서 17개 필드를
  deepcopy로 생성 (npc_registry, resolved_plots, ... financial_number_registry).
Uncertainty: L1567(Director REJECT)에서는 ConstraintDB rollback이 없으나, 이 시점에서
  _cdb_snapshot은 아직 해제되지 않았으므로 상위 finally에서 처리 가능. 명시적 restore가
  없는 것은 의도적 누락 또는 미세 GAP일 수 있음.
Cross-Ref: T01 (SovereignApp — write-back), T12 (StateTracker)
```

### T03-TF-010 — Preflight 병렬 실행 3 Workers + 개별 타임아웃
```
ID: T03-TF-010
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage2_preflight.py:693-732
Evidence:
  - stage2_preflight.py:693 `ThreadPoolExecutor(max_workers=3)`
  - stage2_preflight.py:694 `_fut_drive = _parallel_exec.submit(_compute_arc_drive)` — Weaver LLM
  - stage2_preflight.py:695 `_fut_preflight = _parallel_exec.submit(_compute_preflight)` — Preflight LLM
  - stage2_preflight.py:696 `_fut_constraint = _parallel_exec.submit(_compute_constraint_block)` — ConstraintDB (Python)
  - 개별 타임아웃:
    - arc_drive: 300s (L699)
    - preflight: 300s (L705)
    - constraint: 60s (L711)
  - 각 future에 개별 try/except → 부분 실패 시 다른 결과 수거 (L697 주석)
  - executor shutdown: `wait=False, cancel_futures=True` (L719, L726)
  - PerfTimer: `s2_arc_{N}_preflight_parallel` 외곽 측정 (L683)
Inference: 3개 작업이 완전 독립적이므로 병렬 실행 적합.
  constraint_block은 Python-only이므로 타임아웃이 짧음(60s).
  arc_drive/preflight는 LLM 호출이므로 300s.
Uncertainty: 없음.
Cross-Ref: T11 (BaseAgent — LLM 호출 인프라)
```

### T03-TF-011 — Context Size Warning Threshold 하드코딩
```
ID: T03-TF-011
Severity: P3-LOW
Category: HARDCODING
Surface: modules/core/stage2_preflight.py:1070
Evidence:
  - stage2_preflight.py:1070 `_CONTEXT_WARNING_THRESHOLD = 100_000`
  - stage2_preflight.py:1071-1075
    ```python
    if _ec_size > _CONTEXT_WARNING_THRESHOLD:
        logging.warning(
            f"[S2-I8] enhanced_context {_ec_size:,}자 > {_CONTEXT_WARNING_THRESHOLD:,}자 경고: "
            "Gemini context window 초과 가능성 — 컨텍스트 축소 권장"
        )
    ```
  - Grep `_CONTEXT_WARNING_THRESHOLD` in config/ → 0 matches (validation.yaml에 미정의)
  - ContextLimits.MAX_CONTEXT_CHARS = 1,000,000 (constants.py:142, _LazyThreshold)
Inference: 100K 경고 임계값은 로컬 상수로 하드코딩. MAX_CONTEXT_CHARS(1M)와는 별도.
  advisory 로깅이므로 기능 영향 없음. config 이동 시 `context.warning_threshold` 키 권장.
Uncertainty: 없음.
Cross-Ref: T17 (Config)
```

### T03-TF-012 — ARCS_PER_VOLUME=5 SYNC 확인
```
ID: T03-TF-012
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/constants.py:327, modules/core/stage2_finalizer.py:1452
Evidence:
  - constants.py:327 `ARCS_PER_VOLUME = 5`
  - stage2_finalizer.py:1452 `_arcs_per_volume = max(1, int(VolumeSettings.ARCS_PER_VOLUME))`
  - stage2_finalizer.py:1453 `if global_arc_no > 0 and global_arc_no % _arcs_per_volume == 0:`
  - 5 Arc마다 volume_summary 생성 + series_summary 갱신
  - LLM 호출: director.ask (temperature=0.2) → 볼륨 요약 생성
  - 볼륨 요약 max 2000자, 시리즈 요약 max 5000자 (_trim_hierarchical_summary)
Inference: 상수 참조 일관. 볼륨 요약 트리거는 매 5 Arc (Arc 5, 10, 15, ...).
Uncertainty: 없음.
Cross-Ref: T16 (DB — save_v20_anchor)
```

### T03-TF-013 — Director REJECT 시 ConstraintDB Rollback 누락 가능성
```
ID: T03-TF-013
Severity: P3-LOW
Category: COVERAGE-GAP
Surface: modules/core/stage2_finalizer.py:1567-1576
Evidence:
  - L1567-1576: Director REJECT 시 StateTracker 롤백:
    ```python
    if st_snapshot and generation_method.startswith("four_phase"):
        _st = self.ctx.state_tracker
        for _k, _v in st_snapshot.items():
            if hasattr(_st, _k):
                setattr(_st, _k, _v)
    ```
  - 이 블록에는 ConstraintDB restore가 없음
  - 반면 QualityGate REJECT(L1064-1065), validate_arc(L1108-1110), critical_missing(L1226-1228),
    DB commit 실패(L1368-1370) 모두 ConstraintDB restore 포함
  - ConstraintDB snapshot은 L531-536에서 run_finalize 진입 시 생성됨
  - _cdb_snapshot은 L1374에서 PASS 경로에서만 해제 (`_cdb_snapshot = None`)
Inference: Director REJECT 경로에서는 ConstraintDB가 rollback되지 않음.
  다른 5개 REJECT/실패 경로에서는 모두 rollback이 있으므로 비대칭.
  ConstraintDB는 run_finalize 호출마다 snapshot을 새로 생성하므로,
  다음 attempt에서 새 snapshot이 이전 상태를 덮어쓰므로 실질적 영향은 제한적.
  하지만 attempt loop 내에서 constraint_block이 이전 attempt의 dirty state를
  포함할 수 있음.
Uncertainty: constraint_db.update_arc_state(L1398)가 PASS 경로에서만 호출되므로,
  REJECT 시 실제로는 CDB가 변경되지 않았을 가능성 높음. 이 경우 rollback 불필요.
  동적 검증 필요.
Cross-Ref: T03-TF-009
```

### T03-TF-014 — FewShotExampleManager 저장 3개 / 표시 2개
```
ID: T03-TF-014
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/stage2_optimizer.py:1038, :1076
Evidence:
  - stage2_optimizer.py:1038 `def __init__(self, max_examples: int = 3):`
  - stage2_optimizer.py:1063-1064
    ```python
    if len(self.examples) > self.max_examples:
        self.examples.pop(0)
    ```
  - stage2_optimizer.py:1076 `for i, ex in enumerate(self.examples[-2:], 1):  # 최근 2개만`
  - 3개 저장, 2개만 프롬프트에 표시
Inference: 의도적 설계 — 최근 2개만 표시하여 프롬프트 크기 절약. 3번째는 백업 역할.
Uncertainty: 없음.
Cross-Ref: None
```

### T03-TF-015 — Preflight Guard 확인 (Finalizer 진입 방지)
```
ID: T03-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/stage2_orchestrator.py:662-667
Evidence:
  - stage2_orchestrator.py:662-667
    ```python
    if refined_arc is None:
        self.ctx.ui.log("...")
        attempt += 1
        continue
    ```
  - stage2_orchestrator.py:687-692
    ```python
    if _val["action"] == "retry":
        current_feedback = _val["current_feedback"]
        director_feedback_for_fourphase = current_feedback
        attempt += 1
        continue
    ```
  - stage2_orchestrator.py:715 `_fin = await self.finalizer.run_finalize(...)` — 위 2개 가드 통과 후에만 진입
Inference: Preflight/Enrichment 실패 (refined_arc=None) → finalizer 미진입.
  Validation pipeline 실패 (action=retry) → finalizer 미진입.
  이중 가드로 finalizer 진입 전 반드시 유효한 arc + validation 통과 보장.
Uncertainty: 없음.
Cross-Ref: T02 (Stage 2 Orchestration)
```

### T03-TF-016 — _check_tactical_arithmetic 테스트 커버리지 확인
```
ID: T03-TF-016
Severity: P4-OBSERVATION
Category: SYNC
Surface: tests/test_numeric_selfcheck.py, modules/core/stage2_finalizer.py:124-177
Evidence:
  - stage2_finalizer.py:124-177 `def _check_tactical_arithmetic(tactical_doc: str) -> list[str]`
  - Grep `_check_tactical_arithmetic` in tests/ → tests/test_numeric_selfcheck.py
  - 함수 로직: mult_pattern (A×N=C) + pct_pattern (A×P%=C) regex 매칭
  - tolerance = 0.05 (5%)
  - 한국어 단위 지원: 조(1e12), 억(1e8), 만(1e4) via _to_num_with_korean_units
Inference: 산술 검증 함수는 전용 테스트 파일에서 커버됨. advisory-only이므로 REJECT 강제 없음.
Uncertainty: test_numeric_selfcheck.py의 테스트 범위 깊이는 미확인 (T03 범위 외).
Cross-Ref: T14 (Validation Pipeline — advisory integration)
```

### T03-TF-017 — Finalizer run_finalize async 단일 await
```
ID: T03-TF-017
Severity: P4-OBSERVATION
Category: SIDE-EFFECT
Surface: modules/core/stage2_finalizer.py:492
Evidence:
  - stage2_finalizer.py:492 `async def run_finalize(self, *, ...)`
  - 함수 내 유일한 await: stage2_finalizer.py:1338
    `_commit_ok = await self.ctx.safe_commit_async()`
  - stage2_orchestrator.py:715 `_fin = await self.finalizer.run_finalize(...)`
Inference: run_finalize가 async인 이유는 safe_commit_async 하나뿐.
  나머지 2,100+ lines는 동기 코드. async 전환 비용 대비 단일 await만 사용.
Uncertainty: safe_commit_async의 실제 구현이 blocking I/O를 포함하는지는 T16 범위.
Cross-Ref: T16 (Database)
```

### T03-TF-018 — SessionFailureMemory 타입 어노테이션 불일치
```
ID: T03-TF-018
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/core/stage2_optimizer.py:960
Evidence:
  - stage2_optimizer.py:960
    `def record_failure(self, arc_no: int, attempt: int = 0, reason: str = "",
     category: str = "unknown", details: str = "", failure_type: str = None):`
  - `failure_type: str = None` — str 타입에 None 기본값. 올바른 타입은 `str | None = None`
  - stage2_optimizer.py:973 `actual_category = failure_type if failure_type else category`
  - 런타임 동작에는 영향 없음 (Python은 타입 어노테이션을 강제하지 않음)
Inference: strict type checking (mypy) 환경에서 경고 발생 가능.
  기능 영향 없음.
Uncertainty: 없음.
Cross-Ref: None
```

---

## 3. Evidence Inventory

| TF | Primary Evidence | Evidence Type |
|----|------------------|---------------|
| TF-001 | preflight:799, constants:103, validation.yaml:96 | 코드+설정 비교 |
| TF-002 | optimizer:1158,1179,1183,1196 + grep 0 matches | 부재 증명 |
| TF-003 | preflight:1596-1727 (15+ extract calls) | 코드 인용 |
| TF-004 | finalizer:1335,1383,1439,1704,1727,1506,1527,1904 | 코드 전수 |
| TF-005 | validation.yaml:34, finalizer:762 | 양쪽 코드 비교 |
| TF-006 | constants:121, finalizer:1211 | 양쪽 코드 비교 |
| TF-007 | optimizer:237-289 (10 steps) | 코드 인용 |
| TF-008 | finalizer:793, 801 | 코드 인용 |
| TF-009 | finalizer:6개 롤백 지점 + constraint_db:560,569 | 코드 전수 |
| TF-010 | preflight:693-732 | 코드 인용 |
| TF-011 | preflight:1070 + grep config 0 matches | 코드+부재 |
| TF-012 | constants:327, finalizer:1452 | 양쪽 코드 비교 |
| TF-013 | finalizer:1567-1576 vs 1064-1065 | 비교 근거 |
| TF-014 | optimizer:1038, 1076 | 코드 인용 |
| TF-015 | orchestrator:662-667, 687-692, 715 | 호출 경로 |
| TF-016 | finalizer:124-177, tests/test_numeric_selfcheck.py | 코드+테스트 |
| TF-017 | finalizer:492, 1338 | 코드 인용 |
| TF-018 | optimizer:960 | 코드 인용 |

---

## 4. Side-Effect Surface

### Preflight Side-Effects (stage2_preflight.py)
| Line | Side-Effect | Scope |
|------|------------|-------|
| 1600-1613 | StateTracker: 9개 extract 호출 (NPC, skills, plots, entities, items, ...) | State mutation |
| 1622 | StateTracker: genre registry 업데이트 | State mutation |
| 1630-1633 | DB: financial_registry anchor 저장 (investment only) | DB write |
| 1656-1702 | StateTracker: 8개 추가 extract (dialogue, time, injury, companion, ...) | State mutation |
| 1706-1707 | DB: arc_summary anchor 저장 | DB write |
| 1715 | StateTracker: NPC registry LLM 정리 (매 5 Arc) | State mutation + LLM |
| 766-767 | ctx.sync_cache_key_to_app — app 캐시 동기화 | Cross-boundary mutation |

### Finalizer Side-Effects (stage2_finalizer.py)
| Line | Side-Effect | Scope |
|------|------------|-------|
| 1335 | DB: arcs anchor 저장 | DB write (critical) |
| 1383-1392 | DB: arc_dependency 2종 | DB write |
| 1398 | ConstraintDB: arc state 업데이트 | State mutation |
| 1375-1376 | cumulative_state_cache 무효화 | Cache invalidation |
| 1439-1447 | DB: cost_record 저장 | DB write |
| 1506-1528 | DB: volume_summary, series_summary 저장 + LLM 호출 2회 | DB write + LLM |
| 1704-1743 | DB: stage_attempt, director_selection 저장 | DB write |
| 1904-1924 | DB: cost_record (REJECT) | DB write |
| 1951-1966 | stage_rejection_history append | Memory mutation |
| 1970-1976 | optimizer failure_memory record | Memory mutation |

### Optimizer Side-Effects (stage2_optimizer.py)
| Line | Side-Effect | Scope |
|------|------------|-------|
| 237-289 | ArcAutoCorrector: Arc dict 직접 변경 (10 steps) | Input mutation |
| 979-980 | SessionFailureMemory: failures/pattern_counts 추가 | Memory mutation |
| 1060-1064 | FewShotExampleManager: examples 추가/trim | Memory mutation |

---

## 5. Facts

1. `Stage2PreflightAnalysis`는 `self.host` → `self.ctx` 프록시 패턴 사용 (L20-25)
2. `Stage2Finalizer`도 동일한 `self.host` → `self.ctx` 프록시 패턴 (L485-490)
3. 병렬 실행은 `ThreadPoolExecutor(max_workers=3)` — arc_drive + preflight + constraint 3개 작업
4. PASS_WITH_FIX 루프는 최대 3회 (`_MAX_FIX=3`), 하드코딩
5. StateTracker 스냅샷은 17개 필드 deepcopy (preflight:1569-1591)
6. Quality gate score = 90 (validation.yaml SSOT, 코드 fallback 일치)
7. DB 트랜잭션 롤백: `conn.rollback()` (finalizer:1346) — 명시적 rollback 존재
8. Volume summary는 매 5 Arc마다 생성, Director LLM으로 2000자 이내 요약
9. Series summary는 volume summary 생성 시 함께 갱신, 5000자 이내
10. ArcAutoCorrector는 production에서 `stage2_validation_pipeline.py:372`에서 호출됨

---

## 6. Inferences

1. `_preflight_enrichment`가 15+ StateTracker mutation을 수행하는 것은 FourPhase 성공 시 즉시 상태를 반영하기 위한 의도적 설계로 보임. Director REJECT 시 st_snapshot 롤백으로 보호됨.
2. Stage2Optimizer의 4개 미사용 메서드(record_result, generate_focused_feedback, get_stats, print_stats)는 초기 설계에서 orchestrator가 직접 호출하도록 의도되었으나, failure_memory를 직접 접근하는 방식으로 우회됨.
3. ConstraintDB rollback이 Director REJECT 경로(L1567)에서 누락된 것은 의도적일 가능성이 높음 — constraint_db.update_arc_state는 PASS 경로(L1398)에서만 호출되므로 REJECT 시 CDB 상태 변경이 없음.
4. run_finalize가 async인 것은 safe_commit_async 단일 호출 때문이며, 나머지 로직은 sync. async 오버헤드가 존재하나 기능 문제는 아님.

---

## 7. Uncertainty / Contradictions

1. **TF-001**: YAML 키 누락 시에만 발생하는 fallback 불일치이므로 실제 발생 가능성 낮음
2. **TF-013**: Director REJECT 시 ConstraintDB 실제 변경 여부는 동적 검증 필요
3. **TF-003**: `_preflight_enrichment` 내 15+ extract 호출 중 일부 실패 시 부분 업데이트 상태에서의 st_snapshot 롤백 완전성은 동적 검증 필요 (L1614의 단일 except가 9개 extract를 묶으나, L1616 이후 개별 extract는 각자 except 래핑)

---

## 8. Cross-Ref to Adjacent Terminals

| Terminal | Cross-Ref 내용 |
|----------|---------------|
| T02 | Stage2Context 44 slots 중 stage2_optimizer slot 사용 (stage2_context.py:268). Orchestrator가 preflight 3개 메서드를 프록시로 호출 (orchestrator:1021-1031) |
| T09 | FourPhaseArcGenerator 호출 경로: preflight:1414 `self.ctx.agents["four_phase"].generate(...)`. arc_draft_validator.validate 3회 호출 패턴과의 관계 |
| T12 | StateTracker 17개 필드 스냅샷/롤백, 15+ extract 호출, NPC registry LLM 정리 |
| T14 | validation_pipeline.run_validation이 finalizer 진입 전 가드 역할 (orchestrator:670-692) |
| T16 | Finalizer 9개 DB write surface, DB 트랜잭션 rollback (conn.rollback) |
| T17 | _threshold 참조: retry.analyst_max_attempts, scoring.quality_gate_score, context.vector_max_results_s2, smart_retrieval.*, patch_mode.* |

---

## 9. Candidate Watchlist

1. **Stage2Optimizer dead methods 정리**: record_result, generate_focused_feedback, get_stats, print_stats 제거 또는 wiring (T03-TF-002)
2. **_preflight_enrichment 리네이밍**: `_post_fourphase_state_enrichment` 등 부작용을 명시하는 이름으로 변경 고려 (T03-TF-003)
3. **_MAX_FIX config 이동**: `patch_mode.max_inplace_fix` 키로 validation.yaml 이동 고려 (T03-TF-008)
4. **Context warning threshold config 이동**: `context.warning_threshold` 키 추가 고려 (T03-TF-011)
5. **max_attempts fallback default 통일**: `_threshold("retry.analyst_max_attempts", 5)` → `_threshold("retry.analyst_max_attempts", 10)` 또는 `RetryLimits.ANALYST_MAX_ATTEMPTS` 참조 (T03-TF-001)

---

## 10. 6Pass Audit Log

| Pass | 결과 | 상세 |
|------|------|------|
| Pass 1 (구조/범위) | PASS | 3개 소스 파일 + 3개 테스트 파일 전수 조사. 6개 필수 조사 항목 모두 반영. 18 TFs 구성. |
| Pass 2 (증거/일관성) | PASS | 모든 TF에 파일:라인 증거 포함. grep 결과 기반 부재 증명. 수치/상수 교차 검증 완료. |
| Pass 3 (실행가능성) | PASS | TF severity는 blast radius 기준 적절. P2는 대규모 side-effect(TF-003), P3은 dead code/hardcoding, P4는 관측/SYNC. |
| Pass 4 (적대적 — 스코프) | PASS | "stage2_validation_pipeline.py 누락" 반박 시도 → T02 범위이므로 T03에서는 cross-ref로 언급. "test 파일 drift 미확인" → 테스트 fixture와 production 코드 대조 완료. |
| Pass 5 (적대적 — 증거) | PASS | "TF-001 fallback은 실제 사용 안됨" → 맞으나 코드상 존재하는 불일치이므로 TF 유지. "TF-013 ConstraintDB는 변경 안됨" → Uncertainty에 명시, REJECT 경로에서 update_arc_state 미호출 확인. |
| Pass 6 (적대적 — severity) | PASS | "TF-002 P3은 과대" → 4개 public method가 dead code이므로 P3 유지. "TF-003 P2는 과대" → 15+ state mutation이 misleading name 하에 수행되므로 P2 유지. |

**6PASS-CLEARED** — 확신도 96%
