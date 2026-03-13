# S2D-T4: Finalizer & Director Integration Findings

**Audit date**: 2026-03-13
**Auditor**: Claude Opus 4.6 (3-pass protocol)
**Scope**: `stage2_finalizer.py`, `director_ensemble.py`, `unified_arc_validator.py`, `arc_ensemble.py`

---

## Summary Table

| ID | Title | Severity | File | Line | Verdict |
|----|-------|----------|------|------|---------|
| S2D-T4-001 | Equipment 강제 동기화 — Python이 arc_start_state.equipment 직접 덮어쓰기 | P2 | stage2_finalizer.py | L1047-1072 | 확정 |
| S2D-T4-002 | constraint_summary Python 자동 생성 → 하위 Stage 소비 | P3 | stage2_finalizer.py | L1041-1045 | 확정 |
| S2D-T4-003 | physical_inventory Python 자동 계승 — LLM 미참여 | P2 | stage2_finalizer.py | L940-997 | 확정 |
| S2D-T4-004 | hybrid_composition / joint_docs / status_shadow 기본값 Python 자동 주입 | P3 | stage2_finalizer.py | L917-1008 | 확정 |
| S2D-T4-005 | DB 원자적 커밋 — 롤백 경로 정상, 다만 save_v20_anchor + safe_commit_async 2단계 비원자적 윈도우 존재 | P3 | stage2_finalizer.py | L1087-1122 | 확정 |
| S2D-T4-006 | Director auto-selection 잔류 없음 — 정합 확인 | - | arc_ensemble.py | L551-554 | 오탐 |
| S2D-T4-007 | STRUCTURAL_MIN_SCORE = 50 소프트필터 + 최소 1개 보장 — 정합 확인 | - | arc_ensemble.py | L551-554 | 오탐 |
| S2D-T4-008 | compare_and_select_arc() LLM 전용 — Python 자동선택 없음 확인 | - | director_ensemble.py | L497-775 | 오탐 |
| S2D-T4-009 | _fallback_arc_selection dead code (L782-793) | P3 | director_ensemble.py | L778-793 | 확정 (기존 문서화됨) |
| S2D-T4-010 | UnifiedArcValidator — Python CRITICAL도 LLM에 전달, 최종 판단 LLM (대원칙 준수) | - | unified_arc_validator.py | L148-192 | 오탐 |
| S2D-T4-011 | QualityGate PASS만 적용, PASS_WITH_FIX bypass — 대원칙3 준수 | - | stage2_finalizer.py | L849-850 | 오탐 |
| S2D-T4-012 | DB-3 / DB-7 advisory — advisory-only, Director 주권 준수 | - | stage2_finalizer.py | L277-352 | 오탐 |
| S2D-T4-013 | Equipment Sync 테스트 커버리지 부재 | P2 | tests/ | - | 확정 |

### Severity Distribution

| Severity | Count |
|----------|-------|
| P0 | 0 |
| P1 | 0 |
| P2 | 3 |
| P3 | 4 |
| 정합 확인 (오탐) | 6 |

---

## Findings

### [S2D-T4-001] Equipment 강제 동기화 — Python이 arc_start_state.equipment 직접 덮어쓰기
- **Severity**: P2
- **Location**: `modules/core/stage2_finalizer.py` L1047-1072
- **Root**: 대원칙2 ("팩트시트 수정 권한은 LLM만") 경계 사례
- **Code**:
```python
# [Equipment Sync] arc_start_state.equipment ← 이전 Arc 종료 소지품 강제 동기화
if all_refined_arcs:
    _prev = all_refined_arcs[-1]
    _prev_end = _prev.get("state_constraints", {}).get("arc_end_state", {})
    _correct_equip = _prev_end.get("equipment")
    ...
    if _old_equip != _correct_equip:
        _curr_start["equipment"] = _correct_equip
        _curr_sc["arc_start_state"] = _curr_start
        refined_arc["state_constraints"] = _curr_sc
```
- **Analysis**: Python이 LLM이 생성한 `arc_start_state.equipment`을 직접 덮어쓴다. 이는 "이전 Arc 종료 소지품 → 현재 Arc 시작 소지품" 연속성 보장 목적이지만, 대원칙2의 "팩트시트 수정 권한은 LLM만"과 긴장 관계에 있다.
- **Mitigation**: equipment은 NPC 속성이 아닌 Arc 구조 필드(state_constraints)이며, "연속성 보장을 위한 데이터 정규화"로 해석 가능. Director PASS 이후에 실행되므로 Director가 이미 품질 판정을 내린 뒤의 후처리다. 다만, LLM이 의도적으로 equipment을 변경한 경우(예: "이전 Arc에서 잃어버린 아이템" 시나리오)를 Python이 되돌릴 수 있다.
- **Verdict**: 확정 (P2 — 현재 동작에 실해가 없으나 원칙적 위반 가능성 존재)
- **Recommendation**: advisory 방식으로 전환 — equipment 불일치 감지 시 Director에게 경고로 전달하고 Director가 최종 결정하도록 변경 검토.

---

### [S2D-T4-002] constraint_summary Python 자동 생성 → 하위 Stage 소비
- **Severity**: P3
- **Location**: `modules/core/stage2_finalizer.py` L1041-1045
- **Code**:
```python
# [V63] constraint_summary 저장
if constraint_block:
    _constraint_lines = constraint_block.strip().split("\n")
    _must_not = [ln.strip() for ln in _constraint_lines if "금지" in ln or "MUST NOT" in ln or "절대" in ln]
    refined_arc["constraint_summary"] = "\n".join(_must_not[:10]) if _must_not else ""
```
- **Analysis**: Python이 `constraint_block` 텍스트에서 "금지", "MUST NOT", "절대" 키워드를 포함하는 라인을 추출하여 `constraint_summary`를 자동 생성한다. 이 값은 Stage 3 (`blueprint_constraint_compiler.py` L75-92, `blueprint_ensemble.py` L759), Stage 4 (`stage4_context_builder.py` L869-871, L2112-2114)에서 소비된다.
- **Impact**: 이것은 "판단"이 아닌 "텍스트 필터링/수집" 범주에 해당한다. Python은 특정 키워드를 포함하는 라인을 추출할 뿐 새로운 제약을 생성하지 않는다. 대원칙1 ("Python은 수집만")에 부합한다고 볼 수 있다.
- **Risk**: 키워드 기반 필터링이므로 "금지"라는 단어가 문맥상 다른 의미로 사용된 라인도 추출될 수 있다 (false positive). 또한 "금지" 키워드 없이 표현된 제약은 누락된다 (false negative). 다만 Director가 이미 이 constraint_block을 보고 판정을 내린 뒤이므로, 하위 Stage에서의 참고 정보로서의 역할만 한다.
- **Verdict**: 확정 (P3 — 원칙 위반이 아닌 정밀도 우려)
- **Recommendation**: 없음. 현재 구현이 합리적. 필요 시 LLM에게 constraint_summary 생성을 위임하는 방안 검토 가능하나 ROI 낮음.

---

### [S2D-T4-003] physical_inventory Python 자동 계승 — LLM 미참여
- **Severity**: P2
- **Location**: `modules/core/stage2_finalizer.py` L940-997
- **Code** (핵심):
```python
# [V49.6 NEW] physical_inventory 계승
curr_joint = refined_arc.get("joint_docs", {})
curr_inventory = curr_joint.get("physical_inventory", [])
...
if not curr_inventory:
    if all_refined_arcs:
        prev_joint = all_refined_arcs[-1].get("joint_docs", {})
        prev_inventory = prev_joint.get("physical_inventory", [])
        ...
        inherited = [item for item in prev_inventory if _item_name(item) not in consumed_names]
        inherited.extend(acquired)
        refined_arc["joint_docs"]["physical_inventory"] = inherited
```
- **Analysis**: LLM이 `physical_inventory`를 비워 둔 경우, Python이 이전 Arc의 인벤토리에서 소비된 아이템을 제외하고 자동 계승한다. 이는 대원칙2 경계 사례로, Python이 팩트(소지품 목록)를 직접 수정한다.
- **Mitigation**: `curr_inventory`가 비어 있을 때만 동작하는 폴백이며, LLM이 인벤토리를 명시한 경우 무시된다. "누락 보정" 성격으로 "팩트 수정"보다는 "기본값 주입"에 가깝다.
- **Verdict**: 확정 (P2 — S2D-T4-001과 동일 패턴의 경계 사례)
- **Recommendation**: S2D-T4-001과 함께 검토. 인벤토리 계승 로직을 LLM 프롬프트에 명시적으로 요구하여 Python 폴백 의존도를 낮추는 방안.

---

### [S2D-T4-004] hybrid_composition / joint_docs / status_shadow 기본값 Python 자동 주입
- **Severity**: P3
- **Location**: `modules/core/stage2_finalizer.py` L917-1008
- **Code** (hybrid_composition 예시):
```python
if not refined_arc.get("hybrid_composition"):
    self.ctx.ui.log(f"Warning [Arc {global_arc_no}] hybrid_composition 누락 - 기본값 주입")
    refined_arc["hybrid_composition"] = {
        "primary": "standard_progression",
        "secondary": [],
        "mixing_logic": "기본 전개",
    }
    critical_missing.append("hybrid_composition")
```
- **Analysis**: LLM이 필수 필드를 누락한 경우 Python이 기본값을 주입한다. `critical_missing` 카운터가 `CRITICAL_MISSING_THRESHOLD`를 초과하면 REJECT 반환 (L1010-1025).
- **Impact**: 이것은 "구조 복구"(schema repair)이지 "판단"이 아니다. 대원칙2 위반이 아닌 방어적 코딩. `audit_event("field_repair", ...)` 로깅도 적절하다.
- **Verdict**: 확정 (P3 — 정상 동작, 위험 없음)
- **Recommendation**: 없음.

---

### [S2D-T4-005] DB 원자적 커밋 — save_v20_anchor + safe_commit_async 2단계
- **Severity**: P3
- **Location**: `modules/core/stage2_finalizer.py` L1087-1122
- **Code**:
```python
### [0124 핵심 4] DB 원자적 커밋
try:
    self.ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)
    if callable(getattr(self.ctx, "safe_commit_async", None)):
        _commit_ok = await self.ctx.safe_commit_async()
        if not _commit_ok:
            raise RuntimeError("safe_commit_async returned False")
except (OSError, RuntimeError) as commit_err:
    try:
        _conn = self.ctx.current_project.db.conn
        if _conn.in_transaction:
            _conn.rollback()
    except Exception as _rb:
        logging.warning("DB rollback failed: %s", _rb)
    ...
    all_refined_arcs.pop()
```
- **Analysis**:
  1. `save_v20_anchor`가 데이터를 기록하고 `safe_commit_async`가 커밋한다.
  2. 실패 시 DB rollback + `all_refined_arcs.pop()` + StateTracker 롤백으로 일관성 복구.
  3. 테스트 `test_safe_commit_async_false_returns_retry_and_audit`에서 검증됨.
  4. 이론적 윈도우: `save_v20_anchor` 성공 후 `safe_commit_async` 호출 전에 프로세스가 종료되면, SQLite autocommit 설정에 따라 반쪽 기록 가능. 다만 SQLite의 기본 트랜잭션 모드에서는 명시적 commit 없이는 데이터가 영속화되지 않으므로 실질적 위험은 낮다.
- **Verdict**: 확정 (P3 — 이론적 윈도우 존재하나 실질적 위험 낮음)
- **Recommendation**: 없음. 현재 롤백 경로가 충분히 견고하다.

---

### [S2D-T4-006] Director auto-selection 잔류 없음 — 정합 확인
- **Severity**: -
- **Location**: `modules/domain/agents/arc_ensemble.py` L550-556
- **Code**:
```python
# [TF-S2] 구조 결함만 필터링하고 최종 선택은 Director에게 위임
STRUCTURAL_MIN_SCORE = 50
valid_candidates = [c for c in scored_candidates if c.get("_score", 0) >= STRUCTURAL_MIN_SCORE]
if not valid_candidates:
    valid_candidates = scored_candidates[:1]  # 최소 1개 폴백
```
- **Analysis**: `arc_ensemble.py`는 `return None, valid_candidates`로 반환하며, Python 자동선택 잔류 없음. Director가 `compare_and_select_arc()`에서 최종 선택한다. CLAUDE.md 명시 사항과 정합.
- **Verdict**: 오탐

---

### [S2D-T4-007] STRUCTURAL_MIN_SCORE = 50 소프트필터 + 최소 1개 보장 — 정합 확인
- **Severity**: -
- **Location**: `modules/domain/agents/arc_ensemble.py` L551-554
- **Analysis**: `STRUCTURAL_MIN_SCORE = 50`이 적용되며, 전부 미달 시 `scored_candidates[:1]`로 최소 1개 보장. CLAUDE.md 명시 사항과 정합.
- **Verdict**: 오탐

---

### [S2D-T4-008] compare_and_select_arc() LLM 전용 — Python 자동선택 없음
- **Severity**: -
- **Location**: `modules/domain/agents/director_ensemble.py` L497-775
- **Analysis**: `compare_and_select_arc()`는 LLM 프롬프트로 후보를 비교하고 LLM이 `selected_index`, `decision`, `score`를 반환한다. Python은 LLM 결과의 파싱/정규화만 수행. LLM 실패 시 `_arc_compare_fallback_result()`는 `decision: "REJECT"`를 반환하여 PASS를 자동 부여하지 않는다.
- **Verdict**: 오탐

---

### [S2D-T4-009] _fallback_arc_selection dead code (L782-793)
- **Severity**: P3
- **Location**: `modules/domain/agents/director_ensemble.py` L778-793
- **Code**:
```python
@staticmethod
def _fallback_arc_selection(candidates: list[dict]) -> dict:
    """[TF-47] LLM 실패 시 Python 폴백 — 첫 번째 후보 PASS 반환."""
    logging.warning(" [TF-47] 폴백 — 첫 번째 후보 선택 (Python)")
    return _arc_compare_fallback_result(candidates)
    best = candidates[0] if candidates else None   # <-- unreachable
    return {
        "decision": "PASS",
        ...
    }
```
- **Analysis**: L780에서 `_arc_compare_fallback_result(candidates)`를 즉시 반환하므로, L782-793은 도달 불가 dead code. 이 dead code는 `decision: "PASS"`를 반환하는 이전 구현의 잔해로, 현재는 `_arc_compare_fallback_result`가 `decision: "REJECT"`를 반환하여 안전하다.
- **Verdict**: 확정 (P3 — dead code, 기존 `T4-quality-advisory-audit-findings.md`에 이미 문서화됨)
- **Recommendation**: dead code 삭제.

---

### [S2D-T4-010] UnifiedArcValidator — CRITICAL만 REJECT, MAJOR는 Director 위임
- **Severity**: -
- **Location**: `modules/domain/agents/unified_arc_validator.py` L148-192
- **Analysis**: Python CRITICAL 발견 시에도 LLM에 전달 (V63.4). 최종 verdict는 LLM issues를 포함한 all_issues 기반. CRITICAL만 REJECT, MAJOR는 PASS 후 Director 위임. 대원칙3 (Director 주권주의) 준수.
- **Verdict**: 오탐

---

### [S2D-T4-011] QualityGate — PASS만 적용, PASS_WITH_FIX bypass
- **Severity**: -
- **Location**: `modules/core/stage2_finalizer.py` L849-850
- **Code**:
```python
if _d_decision == "PASS" and _td_len >= 1500 and _score < _quality_gate_score:  # [TF-46] PASS만 gate 적용
```
- **Analysis**: CLAUDE.md 명시: "PASS_WITH_FIX는 bypass (Director 주권 존중)". 코드가 `_d_decision == "PASS"` 조건으로 정확히 이를 구현. 정합.
- **Verdict**: 오탐

---

### [S2D-T4-012] DB-3 / DB-7 advisory — advisory-only, Director 주권 준수
- **Severity**: -
- **Location**: `modules/core/stage2_finalizer.py` L277-352, L546-552
- **Analysis**: `_build_arc_dependency_advisory` (DB-3)와 `_build_character_voice_advisory` (DB-7)는 모두 문자열을 반환하여 `_story_context`에 추가한다. Director의 `audit_strategic_plan()` 호출 시 `story_context` 파라미터로 전달되어 LLM Director가 참고한다. Python은 정보 수집/포맷팅만 수행하며 판정에 개입하지 않는다. CLAUDE.md 명시: "Stage2 Finalizer: DB-3(arc_dependencies), DB-7(character_voice)". 정합.
- **Verdict**: 오탐

---

### [S2D-T4-013] Equipment Sync 테스트 커버리지 부재
- **Severity**: P2
- **Location**: `tests/test_stage2_finalizer.py` (전체)
- **Analysis**: `test_stage2_finalizer.py`에 Equipment Sync 관련 테스트가 없다. `equipment`, `강제 동기화` 키워드 검색 결과 0건. Equipment Sync는 S2D-T4-001에서 확인된 대원칙2 경계 사례로, 테스트 없이 리팩터링 시 의도치 않은 동작 변경 위험이 있다.
- **Verdict**: 확정 (P2 — 중요 로직의 테스트 부재)
- **Recommendation**: Equipment Sync 동작을 검증하는 단위 테스트 추가 (이전 Arc에 equipment 있을 때 현재 Arc에 반영되는지, 현재 Arc에 이미 equipment가 있으면 덮어쓰는지 등).

---

## 3pass Final Summary

### 대원칙 검증 결과

| 원칙 | 결과 | 비고 |
|------|------|------|
| 1. Python은 수집만, 판단은 LLM | **준수** | 모든 advisory가 Director story_context에 참고 정보로만 전달됨 |
| 2. 팩트시트 수정 권한은 LLM만 | **경계 사례 2건** | Equipment Sync (S2D-T4-001), physical_inventory 계승 (S2D-T4-003) — Python이 Arc 구조 필드를 직접 수정. NPC 속성/세계관 설정/관계도 수정은 없음 |
| 3. 디렉터 주권주의 | **준수** | Director가 compare_and_select_arc()에서 최종 선택, QualityGate는 PASS만 적용, PASS_WITH_FIX bypass |
| 4. 사망 캐릭터 회상/언급만 | **해당 없음** | Stage 2 범위 밖 (UnifiedArcValidator에서 dead NPC 체크는 LLM에게 정보 전달만) |

### 핵심 결론

1. **P0/P1 이슈 없음** — Finalizer와 Director 통합 경로에 치명적 결함 없음.
2. **Equipment Sync (S2D-T4-001) + physical_inventory 계승 (S2D-T4-003)** 이 대원칙2의 경계 사례이나, 둘 다 "Arc 구조 필드 정규화" 성격이며 NPC 속성/세계관 설정 수정이 아니므로 즉시 조치 불필요.
3. **Director auto-selection 잔류 없음** — CLAUDE.md 명시 사항과 코드가 정합.
4. **DB 원자적 커밋** — save + commit + 실패 시 rollback + all_refined_arcs.pop() + StateTracker 롤백으로 견고한 복구 경로.
5. **테스트 갭**: Equipment Sync 테스트 부재 (S2D-T4-013).
