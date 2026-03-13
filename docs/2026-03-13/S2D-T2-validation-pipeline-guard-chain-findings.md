# [S2D-T2] Validation Pipeline & Guard Chain — Deep Dive Audit

> 작성일: 2026-03-13
> 상태: `3pass completed`
> 조사 모드: `static / read-only / code-and-test verification`
> Track: Stage 2 Deep Dive — T2 (Validation Pipeline & Guard Chain)

---

## 조사 범위

| 파일 | 역할 |
|------|------|
| `modules/core/stage2_validation_pipeline.py` | Pre-Director 검증 체인 (1,196줄) |
| `modules/core/stage2_optimizer.py` | ArcAutoCorrector + StateSnapshotInjector 등 6개 컴포넌트 |
| `modules/core/stage2_contracts.py` | 공유 상수 (TACTICAL_DOC_DUPLICATE_THRESHOLD) |
| `modules/domain/agents/arc_corrector.py` | ArcCorrector (LLM 기반 부분 수정, BaseAgent 상속) |
| `modules/domain/agents/arc_draft_validator.py` | ArcDraftValidator (Python-only advisory) |

## 참조 테스트

- `tests/test_stage2_validation_pipeline.py` (17 tests)
- `tests/test_stage2_pipeline.py` (41 tests)
- `tests/test_stage2_optimizer.py` (17 tests)
- `tests/test_arc_draft_validator.py` (2 tests)

## 기존 문서 확인

- `docs/2026-03-13/MFS-T1-stage2-normalization-flow-findings.md` — MFS-T1-001 (threshold drift), MFS-T1-002 (flow guard fallback) 이미 보고됨
- 본 감사에서 MFS-T1과 중복되는 건은 참조만 하고 재보고하지 않음

---

## Summary Table

| ID | Severity | 상태 | 위치 | 요약 |
|----|----------|------|------|------|
| S2D-T2-001 | P2 | 확정 | `stage2_optimizer.py` ArcAutoCorrector | Python이 아이템 중복·위치·내공·소지품 등을 자율 수정 — 대원칙1 경계 사례 |
| S2D-T2-002 | P3 | 확정 | `arc_corrector.py:342-371` | `_correct_location_issue`가 LLM 없이 Python-only로 위치 직접 수정 |
| S2D-T2-003 | P2 | 확정 | `stage2_validation_pipeline.py:746-747` | ContinuityInspector 호출 전 `joint_docs`/`status_shadow`를 enriched_block 값으로 덮어씀 |
| S2D-T2-004 | P3 | 확정 | `stage2_optimizer.py:227-289` | ArcAutoCorrector.auto_correct()가 corrections를 문자열 리스트로 반환, advisory 변환 시 구조 정보 손실 |
| S2D-T2-005 | P3 | 확정 | `arc_corrector.py:93-94` | ArcCorrector.max_corrections=2 하드코드, validation.yaml 미참조 |
| S2D-T2-006 | P3 | 보류 | `stage2_validation_pipeline.py:1019-1162` | Flow Guard가 NarrativeStructureAnalyzer 내부에서 LLM 호출 수행 — 대원칙 위반 가능성 |
| S2D-T2-007 | P2 | 확정 | `stage2_validation_pipeline.py:556-573` | DraftValidator 크래시 시 fail-closed 결과가 ArcCorrector 경로로 유입되나, critical_issues가 crash 메시지뿐 |
| S2D-T2-008 | P3 | 확정 | `stage2_validation_pipeline.py:229-246` | 1차 DraftValidator 호출의 advisory_issues가 로컬 `python_advisory`에만 저장되어 Consensus에만 전달, Director advisory에 미포함 |

---

## Final Findings

### [S2D-T2-001] ArcAutoCorrector가 아이템 중복 제거·위치·내공·소지품을 Python-only로 자율 수정
- Severity: P2
- 위치: `modules/core/stage2_optimizer.py:227-289` (`auto_correct` 메서드)
- 근거:
```python
# L253-259
# 1. 중복 아이템 제거
arc = self._remove_duplicate_items(arc, prev_arcs)
# 2. 소지품 연속성 점검 (advisory-only)
arc = self._check_equipment_continuity(arc, prev_arcs)
# 3. 시작 위치 자동 수정
arc = self._fix_start_location(arc, prev_arcs)
# 4. 시작 상태 계승
arc = self._fix_start_state(arc, prev_arcs)
```
  - `_remove_duplicate_items` (L291-341): 이전 Arc에 존재하는 아이템을 Python 부분 문자열 매칭(`_is_duplicate`)으로 판단하여 삭제. LLM 판단 없음.
  - `_fix_start_location` (L360-402): 이전 Arc 종료 위치와 다르면 Python이 직접 `arc_start_state.location`을 덮어쓰고, tactical_doc 내 텍스트까지 `str.replace()`로 치환.
  - `_fix_start_state` (L404-454): 내공/부상/소지품을 이전 Arc 종료값으로 Python이 직접 교체.
  - `_filter_abstract_items_consumed` (L586-611): 15자 초과이거나 정규식 매칭되면 Python이 자동 삭제.
- 판정: **확정** (경계 사례)
  - 대원칙1("Python은 수집만, 판단은 LLM이")에 대한 가장 광범위한 예외. corrections 목록에 기록하여 Director advisory로 전달되지만, 수정 자체는 LLM 판단 없이 실행됨.
  - `_is_duplicate` (L343-358)의 부분 문자열 + 길이 비율 2.0 기준은 "천풍검" vs "천풍검법" 같은 서로 다른 아이템도 중복으로 오탐할 수 있음.
  - 단, corrections가 Director advisory로 전달되므로 Director가 최종 판정에서 이를 참조할 수 있어 대원칙3은 형식적으로 준수.
- 권장 조치:
  - 자동 수정 대신 advisory-only로 전환 검토 (현재 PATCH-B/C/D처럼)
  - `_is_duplicate`의 부분 문자열 매칭 오탐 가능성 문서화

### [S2D-T2-002] ArcCorrector._correct_location_issue가 LLM 없이 위치 직접 수정
- Severity: P3
- 위치: `modules/domain/agents/arc_corrector.py:342-371`
- 근거:
```python
# L358-367
if prev_location:
    # arc_start_state.location 수정
    arc_start = state.get("arc_start_state", {})
    arc_start["location"] = prev_location
    state["arc_start_state"] = arc_start
    arc["state_constraints"] = state

    result["success"] = True
    result["field"] = "state_constraints.arc_start_state.location"
    result["summary"] = f"시작 위치를 '{prev_location}'으로 수정"
```
  - ArcCorrector는 BaseAgent를 상속하여 LLM 호출 능력이 있으나 (`_correct_length_issue`, `_correct_checkpoint_issue` 등은 `self.ask()` 사용), `_correct_location_issue`만 Python-only로 직접 수정.
  - `_correct_field_issue` (L431-454)의 `_generate_joint_docs_from_tactical`과 `_generate_default_state_constraints`도 Python-only.
- 판정: **확정** (P3)
  - 위치 수정은 기계적 계승이므로 대원칙1 위반으로 보기 어렵지만, 같은 클래스 내 다른 메서드는 LLM을 사용하는 비대칭 설계.
- 권장 조치: 의도적 설계라면 주석으로 "기계적 계승이므로 LLM 불필요" 명시

### [S2D-T2-003] ContinuityInspector 호출 전 joint_docs/status_shadow를 enriched_block 값으로 덮어씀
- Severity: P2
- 위치: `modules/core/stage2_validation_pipeline.py:746-747`
- 근거:
```python
# L743-751 (_run_continuity_inspection 내부)
if not four_phase_passed and "continuity_inspector" in self.ctx.agents:
    self.ctx.ui.log(f"      🔍 [V49] Arc {global_arc_no} 연속성 검증 중...")

    refined_arc["joint_docs"] = enriched_block.get("joint_docs", {})
    refined_arc["status_shadow"] = enriched_block.get("status_shadow", {})

    try:  # [S2-001] ContinuityInspector 예외 전파 차단 → retry 변환
        with rich_console.status(...):
            continuity_result = self.ctx.agents["continuity_inspector"].inspect_arc(
                current_arc=refined_arc, ...
```
  - B1 단계의 ArcAutoCorrector가 `_fix_joint_docs`로 정교하게 수정한 `joint_docs`를, B4 단계에서 `enriched_block.get("joint_docs", {})` (원본 블록 데이터)로 무조건 덮어씀.
  - 이로 인해 ArcAutoCorrector가 추출한 `final_location`이나 `_sync_final_location`의 결과가 무효화됨.
  - `status_shadow`도 동일하게 원본으로 리셋됨.
- 판정: **확정**
  - ArcAutoCorrector 수정 결과가 ContinuityInspector 검증 시점에 반영되지 않아, 연속성 검증이 수정 전 데이터를 기준으로 수행됨.
- 권장 조치: 덮어쓰기 대신 `refined_arc`에 이미 있으면 유지, 없을 때만 `enriched_block`에서 채우는 merge 방식으로 전환

### [S2D-T2-004] ArcAutoCorrector corrections가 문자열 리스트로 반환되어 advisory 변환 시 구조 정보 손실
- Severity: P3
- 위치: `modules/core/stage2_optimizer.py:227-289` (auto_correct 반환), `stage2_validation_pipeline.py:158-197` (advisory 변환)
- 근거:
```python
# stage2_optimizer.py L237, L244
self.corrections_made = []
# ...
self.corrections_made.append(f"중복 아이템 제거: {', '.join(removed)}")  # L337 — 순수 문자열

# stage2_validation_pipeline.py L170-186 (_append_auto_correction_pressure_advisory)
for item in corrections[:5]:
    if isinstance(item, dict):
        label = (
            item.get("category")
            or item.get("rule") ...
        )
    else:
        label = str(item)  # ← 실제로 항상 이 경로
```
  - `ArcAutoCorrector.corrections_made`는 `list[str]`이지만, `_append_auto_correction_pressure_advisory`는 dict를 먼저 체크하고 str은 `str(item)`으로 처리.
  - category/rule/type 같은 구조화된 메타데이터가 없어 Director가 advisory를 받아도 어떤 종류의 수정인지 파악이 어려움.
  - 반면 `ArcCorrector.correct()`의 `corrections_made`는 `list[dict]` (field, change_summary 포함) — 두 corrector의 반환 형식 불일치.
- 판정: **확정**
  - 기능 결함은 아니지만, Director가 받는 advisory의 정보 밀도가 낮음.
- 권장 조치: `ArcAutoCorrector.corrections_made`를 `list[dict]` (category, message, field 키)로 구조화

### [S2D-T2-005] ArcCorrector 하드코드 상수가 validation.yaml 미참조
- Severity: P3
- 위치: `modules/domain/agents/arc_corrector.py:93-94`
- 근거:
```python
# L90-94
def __init__(self, context, client, model_tier: str = None):
    super().__init__(context, client, model_tier)
    self.max_corrections = 2  # 최대 수정 횟수
    self.max_change_ratio = 0.20  # 최대 변경 비율 (20%)
```
  - `max_corrections=2`, `max_change_ratio=0.20`이 하드코드. 프로젝트 SSOT인 `config/settings/validation.yaml`에 해당 키 없음.
  - 반면 같은 파이프라인의 다른 컴포넌트들은 `_threshold()` 헬퍼를 통해 YAML에서 값을 로드함 (예: `_JACCARD_SIMILARITY_THRESHOLD`, `_min_beats_floor` 등).
- 판정: **확정**
  - 운영 문제는 아니지만, SSOT 원칙에 대한 일관성 부재.
- 권장 조치: `validation.yaml`에 `arc_corrector.max_corrections`, `arc_corrector.max_change_ratio` 키 추가

### [S2D-T2-006] Flow Guard 내부 NarrativeStructureAnalyzer LLM 호출 — 대원칙1 경계
- Severity: P3
- 위치: `modules/core/stage2_validation_pipeline.py:1115-1136`
- 근거:
```python
# L1115-1136
try:
    from modules.core.narrative_structure_analyzer import NarrativeStructureAnalyzer

    analyzer = NarrativeStructureAnalyzer(client=self.ctx.sys.api_client, model=_SUMMARY_MODEL)

    # [Sweep45] dict 혼합 beats 방지 — normalized (문자열만) 전달
    result = analyzer.analyze(normalized[:5])

    if result.get("status") == "STAGNATION":
        # ...
        return {
            "status": "REJECT",
            "reason": f"서사 정체 감지: {stagnation_type} 반복 ({pattern})",
            "feedback": recommendation,
        }
```
  - `NarrativeStructureAnalyzer`가 `api_client`와 `SUMMARY_MODEL`(Flash)을 받아 LLM 호출 수행.
  - Flow Guard의 REJECT 판정이 LLM 분석 결과에 기반하므로, 이것이 대원칙1("Python은 수집만")과 대원칙3("디렉터 주권주의")의 경계에 위치.
  - 단, Flow Guard REJECT는 [TF-25-08]에 의해 Director advisory로 전환되어 Director가 최종 판정하므로, Director 주권은 형식적으로 보존됨.
- 판정: **보류**
  - Flow Guard 내부의 LLM 호출이 "수집/분석"인지 "판단"인지 해석에 따라 다름. REJECT가 advisory로 전환되므로 실질적 위반은 아님.
- 권장 조치: 현행 유지 가능. 다만 `NarrativeStructureAnalyzer`가 api_client를 사용한다는 점을 Flow Guard 문서에 명시

### [S2D-T2-007] DraftValidator 크래시 시 fail-closed 결과가 ArcCorrector로 유입되지만 critical_issues가 crash 메시지뿐
- Severity: P2
- 위치: `modules/core/stage2_validation_pipeline.py:556-573`, `597-601`
- 근거:
```python
# L565-573 (DraftValidator crash → fail-closed)
except (RuntimeError, ValueError, OSError) as _dv_err:
    logging.warning(f"[G6] DraftValidator 호출 실패 — fail-closed: {_dv_err!s:.100}")
    draft_result = {
        "valid": False,
        "score": 0,
        "advisory_issues": [],
        "critical_issues": [f"DraftValidator crash: {_dv_err!s:.100}"],
        "warnings": [],
    }

# L597-601 (ArcCorrector 분기 조건)
critical_only = draft_result.get("critical_issues", [])
major_only = [{"message": w, "severity": "WARNING"} for w in draft_result.get("warnings", [])]

if not critical_only and major_only and self.ctx.arc_corrector and self.ctx.use_arc_corrector:
```
  - Crash 시 `critical_issues = ["DraftValidator crash: ..."]`이므로 `critical_only`가 비어있지 않아 ArcCorrector 경로에는 진입하지 않음 — 이 자체는 정상.
  - 그러나 crash 메시지가 그대로 `_python_advisories`에 "V60.11 DraftValidator 사전 검증 실패" advisory로 전달됨 (L697-708). Director는 내부 에러 메시지("DraftValidator crash: RuntimeError...")를 받게 됨.
- 판정: **확정**
  - Director가 Python 내부 에러 스택을 advisory로 받는 것은 정보 품질 문제. Director가 이를 기반으로 유의미한 판단을 내리기 어려움.
- 권장 조치: crash 시 advisory 메시지를 "사전 검증 시스템 일시 오류. Director 직접 검증 필요." 등 서사 검증 관점의 문구로 변환

### [S2D-T2-008] 1차 DraftValidator advisory가 Director advisory에 미포함
- Severity: P3
- 위치: `modules/core/stage2_validation_pipeline.py:229-246`
- 근거:
```python
# L229-246 (_run_pre_validation_checks, B1 단계)
python_advisory = []  # ← 로컬 변수
if not four_phase_passed and refined_arc and self.ctx.arc_draft_validator:
    try:
        draft_result = self.ctx.arc_draft_validator.validate(...)
        advisory_issues = draft_result.get("advisory_issues", [])
        if advisory_issues:
            python_advisory.extend(advisory_issues)  # ← 로컬에만 저장
        # ...
    except ...

# L296-307 (Consensus 호출)
consensus_verdict, consensus_result = self.ctx.agents["consensus"].validate_with_consensus(
    arc=refined_arc,
    prev_arcs=all_refined_arcs,
    constraints=constraint_block or "",
    python_advisory=python_advisory,  # ← Consensus에만 전달
)
```
  - 1차 DraftValidator의 advisory_issues는 `python_advisory` (로컬 변수)에 저장되어 Consensus 검증에만 전달됨.
  - 최종 반환의 `_python_advisories` (Director에 전달되는 리스트)에는 포함되지 않음.
  - 2차 DraftValidator (B3 단계, L556-718)는 별도로 실행되어 결과가 `_python_advisories`에 추가됨.
  - 1차 호출의 주석 `# [S2-P1-4] 1차 호출은 Consensus용 advisory 수집 전용` (L248)에 의하면 의도적 설계.
- 판정: **확정** (의도적이나 정보 손실 가능성 존재)
  - Consensus가 REJECT하면 그 advisory가 `_python_advisories`에 추가되므로 간접적으로 Director에 도달.
  - 그러나 Consensus가 PASS하면 1차 DraftValidator가 발견한 advisory_issues가 Director에 전혀 전달되지 않는 경로 존재.
- 권장 조치: 의도적 설계라면 현행 유지. 다만, Consensus PASS + 1차 DraftValidator advisory 존재 시 정보 누락 가능성을 주석에 명시

---

## Guard Chain 실행 순서 분석

### 현재 순서 (run_validation 기준):

```
B1: _run_pre_validation_checks
    ├── DraftValidator 1차 (advisory 수집용)
    ├── SelfReflector (Analyst 자기 비판)
    ├── Consensus 3-LLM 검증
    ├── Data Validation (refined_arc null check)
    ├── Mapping Validation
    ├── Stage2Optimizer.post_process_arc (ArcAutoCorrector)
    └── Pre-Validation (constraint_db.validate_arc_design)

B2: _run_flow_and_duplicate_guards
    ├── Flow Guard (_stage2_flow_guard)
    ├── Duplicate Guard (_is_tactical_doc_duplicate)
    └── Data Validation (refined_arc + enriched_block null check)

B3: _run_draft_validator_full
    ├── DraftValidator 2차 (full validation)
    └── ArcCorrector (MAJOR-only 부분 수정)

B4: _run_continuity_inspection
    ├── joint_docs/status_shadow 덮어쓰기 ← [S2D-T2-003]
    ├── ContinuityInspector
    └── FailureLearner / PassRateMonitor / Stage2Optimizer 기록
```

### 순서 관련 소견:
1. ArcAutoCorrector (B1)가 joint_docs를 수정하지만 B4에서 enriched_block으로 덮어씀 [S2D-T2-003]
2. Flow Guard (B2)가 ArcAutoCorrector (B1) 이후에 실행되므로 메타 용어 치환(`_sanitize_tactical_meta_terms`) 후의 beat_sequence를 검증함 — 정상
3. DraftValidator가 1차(B1)와 2차(B3)로 나뉘어 실행됨 — 의도적 설계 (1차=Consensus 지원, 2차=full validation)

---

## 대원칙 준수 평가

| 대원칙 | 준수 여부 | 비고 |
|--------|-----------|------|
| 1. Python은 수집만, 판단은 LLM이 | **부분 준수** | ArcAutoCorrector가 광범위한 자율 수정 수행 [S2D-T2-001]. 단, corrections가 advisory로 Director에 전달됨 |
| 2. 팩트시트 수정 권한은 LLM만 | **준수** | Arc 데이터 수정이므로 팩트시트 직접 수정은 아님 |
| 3. 디렉터 주권주의 | **준수** | 모든 Guard REJECT가 advisory로 전환되어 Director가 최종 판정 [TF-25-08] |
| 4. 사망 캐릭터 제한 | **해당 없음** | Stage 2 검증 범위 외 |

---

## 테스트 커버리지 소견

- `Stage2ValidationPipeline`: 17개 테스트로 주요 경로 커버 (happy path, Flow Guard REJECT, Duplicate Guard REJECT, Consensus REJECT, ContinuityInspector REJECT, auto_correct_pressure advisory)
- `ArcAutoCorrector`: 17개 테스트로 개별 수정 규칙 검증 (duplicate items, location fix, wuxia strip, abstract filter, PATCH-A/B/C/D)
- `ArcCorrector`: 직접 단위 테스트 없음 (sweep 테스트에서 간접 커버)
- `ArcDraftValidator`: 2개 테스트만 존재 (grant timeline, genre suffixes) — 커버리지 부족

---

## 종합 판정

- P0: 0건
- P1: 0건
- P2: 3건 (S2D-T2-001, S2D-T2-003, S2D-T2-007)
- P3: 4건 확정 + 1건 보류
- 전반적으로 대원칙3(디렉터 주권주의)은 TF-25-08 advisory 전환 패턴 덕에 잘 준수됨
- 가장 주의가 필요한 영역은 ArcAutoCorrector의 자율 수정 범위(S2D-T2-001)와 B4 단계의 joint_docs 덮어쓰기(S2D-T2-003)
