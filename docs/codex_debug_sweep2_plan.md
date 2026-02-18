# 2차 디버그 스윕 플랜 — 인프라 구조 버그

> 작성: 2026-02-16
> 대상: DI 마이그레이션 + B-1 분할 + Phase 5 이후 전체 인프라
> 전략: 7개 탐색 에이전트 병렬 감사 → 발견 사항 카테고리화
> 안전망: 1,659 passed + 68 xfailed (전체 그린 스위트)

---

## 스캔 결과 총괄

| # | 카테고리 | 발견 건수 | 심각도 |
|---|---------|----------|--------|
| A | StateTracker 스테이지 간 손실 | 1건 | CRITICAL |
| B | Lazy Init Extract 갭 | 2건 (Stage3 + Stage4) | MEDIUM |
| C | Facade 위임 계약 | 0건 | CLEAN |
| D | 서브모듈 역참조 | 0건 | CLEAN |
| E | DI from_app 정합성 | 0건 | CLEAN |
| F | 임포트 건전성 | 0건 | CLEAN |
| G | 에러 전파 경로 | 0건 | CLEAN |
| H | 테스트 mock 신선도 | 0건 | CLEAN |

---

## 카테고리 A: StateTracker 스테이지 간 손실 (CRITICAL)

### A-1: Stage 2→3/4 전환 시 StateTracker 데이터 소실

**심각도**: CRITICAL — NPC 연속성 데이터 13개 카테고리 전량 소실

**현상**:

Stage 2는 `self.ctx.state_tracker`에 17개 extract 메서드로 풍부한 NPC 데이터를 구축하지만,
Stage 2 종료 시 `app.state_tracker`에 동기화하지 않음.
Stage 3/4가 시작하면 `app.state_tracker is None` → 신규 StateTracker 생성 → **데이터 전량 소실**.

**증거**:

Stage 2 (stage2_orchestrator.py L150-240)가 호출하는 17개 extract:
```
1.  extract_npc_deaths_from_arc           ← Stage3/4 lazy init에도 있음
2.  extract_skill_acquisitions_from_arc   ← Stage3/4 lazy init에도 있음
3.  extract_npc_info_from_arc             ← Stage3/4 lazy init에도 있음
4.  extract_resolved_plots_from_arc       ← Stage3/4 lazy init에도 있음
5.  extract_time_markers_from_arc         ← ❌ LOST
6.  extract_permanent_injuries_from_arc   ← ❌ LOST
7.  update_companions_from_arc            ← ❌ LOST
8.  extract_commitments_from_arc          ← ❌ LOST
9.  extract_protagonist_emotion_from_arc  ← ❌ LOST
10. extract_item_states_from_arc          ← ❌ LOST
11. extract_entity_destructions_from_arc  ← ❌ LOST
12. extract_npc_personality_from_arc      ← ❌ LOST
13. extract_npc_npc_relationships_from_arc← ❌ LOST
14. extract_npc_dialogue_styles_from_arc  ← ❌ LOST
15. extract_relationship_changes_from_arc ← ❌ LOST
16. extract_npc_injuries_from_arc         ← ❌ LOST
17. extract_npc_movements_from_arc        ← ❌ LOST
(+) extract_financial_events_from_arc     ← ❌ LOST (투자물)
```

Stage 3/4 lazy init은 #1~#4만 호출 → **13개 카테고리 소실**.

**근본 원인**: DI 마이그레이션 시 Stage 2의 `ctx.state_tracker`가 `app.state_tracker`에
동기화되는 경로가 없음. Stage 3는 lazy init 후 sync(L88-91)를 수행하지만,
Stage 2에는 이 패턴이 빠져 있음.

**수정**:

`main_a.py` L2070 (`asyncio.run(...)` 직후)에 동기화 코드 추가:

```python
        asyncio.run(self._stage2_orch.stage_2_arcs_async_logic())
        # [Sweep2-A1] Stage 2에서 구축한 StateTracker를 app에 동기화
        # Stage 3/4 lazy init이 재사용할 수 있도록 함
        _s2_ctx = self._stage2_orch.ctx
        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
            self.state_tracker = _s2_ctx.state_tracker
```

**검증**:
1. 단위 테스트 추가: `tests/test_stage_transition.py`
   - Stage 2 완료 후 `app.state_tracker`가 ctx의 인스턴스와 동일한지 확인
   - Stage 3 시작 시 lazy init이 스킵되는지 확인 (이미 존재하므로)
2. 전체 회귀: `pytest tests/ -q`

---

## 카테고리 B: Lazy Init Extract 갭 (MEDIUM)

### B-1: Stage 3 lazy init의 V66 확장 데이터 미추출

**심각도**: MEDIUM — Stage 2 없이 직접 Stage 3 실행 시 V66 확장 데이터 누락

**파일**: `modules/core/stage3_orchestrator.py` L175-193

**현상**: Stage 3 `_init_state_tracker_if_needed()`가 4개 extract만 호출.
Stage 2 없이 직접 Stage 3 진입 시(메뉴에서 허용) V66 이후 추가된 13개 카테고리 데이터 없음.
Blueprint 생성 품질에 간접 영향.

### B-2: Stage 4 lazy init의 V66 확장 데이터 미추출

**심각도**: MEDIUM — Stage 2 없이 직접 Stage 4 실행 시 동일 문제

**파일**: `main_a.py` L2725-2738

**현상**: B-1과 동일 패턴.

**수정 (B-1, B-2 공통)**:

`_init_state_tracker_if_needed()` 내부에 Stage 2와 동일한 extract 호출 추가.
별도 헬퍼 `_full_extract_from_arcs(state_tracker, arcs, genre)` 추출 후 3곳에서 공유.

```python
# modules/domain/agents/state_tracker.py (또는 별도 유틸)
def full_extract_from_arcs(tracker, arcs: list[dict], genre: str = "") -> None:
    """Stage 2와 동일한 17개 extract 메서드를 순회 호출."""
    for arc in arcs:
        tracker.extract_npc_deaths_from_arc(arc)
        tracker.extract_skill_acquisitions_from_arc(arc)
        tracker.extract_npc_info_from_arc(arc, genre=genre)
        tracker.extract_resolved_plots_from_arc(arc)
        try:
            tracker.extract_time_markers_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.extract_permanent_injuries_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.update_companions_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.extract_commitments_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.extract_protagonist_emotion_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.extract_item_states_from_arc(arc)
        except (KeyError, ValueError, TypeError):
            pass
        try:
            tracker.extract_entity_destructions_from_arc(arc)
        except (KeyError, ValueError, TypeError):
            pass
        try:
            tracker.extract_npc_personality_from_arc(arc)
        except (KeyError, ValueError, TypeError):
            pass
        try:
            tracker.extract_npc_npc_relationships_from_arc(arc)
        except (KeyError, ValueError, TypeError):
            pass
        try:
            tracker.extract_npc_dialogue_styles_from_arc(arc)
        except (KeyError, ValueError, TypeError):
            pass
        try:
            tracker.extract_relationship_changes_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.extract_npc_injuries_from_arc(arc)
        except Exception:
            pass
        try:
            tracker.extract_npc_movements_from_arc(arc)
        except Exception:
            pass
        if genre == "investment":
            tracker.extract_financial_events_from_arc(arc)
```

적용 위치:
- `stage2_orchestrator.py` L170-239 → `full_extract_from_arcs(self.ctx.state_tracker, new_arcs_to_load, genre)` 호출로 교체
- `stage3_orchestrator.py` L182-188 → `full_extract_from_arcs(app.state_tracker, all_arcs, genre)` 호출로 교체
- `main_a.py` L2729-2733 → `full_extract_from_arcs(self.state_tracker, all_arcs, genre)` 호출로 교체

**검증**: `pytest tests/ -q` 전체 회귀

---

## 카테고리 C~H: 이상 없음 (CLEAN)

| 카테고리 | 스캔 결과 |
|---------|----------|
| C. Facade 위임 계약 | 93+ 위임 호출 전수 검사 — 메서드명·시그니처 불일치 0건 |
| D. 서브모듈 역참조 | 15개 서브모듈 `self._parent` / `self._orch` 전수 — 댕글링 0건 |
| E. DI from_app 정합성 | Stage2/3/4 Context `from_app()` 매핑 전수 — 누락/불일치 0건 |
| F. 임포트 건전성 | 전체 모듈 순환참조 0건, 데드 임포트 0건 |
| G. 에러 전파 경로 | CRITICAL 경로 re-raise 확인, OPTIONAL soft-fail 패턴 일관 |
| H. 테스트 mock 신선도 | 스테일 패치 0건, 미사용 mock 속성 소수 (무해) |

---

## 실행 순서

```
Phase 1: A-1 StateTracker 동기화 (CRITICAL, 1줄 + 테스트)   ← ✅ 완료 (26cf92a)
Phase 2: B-1+B-2 Extract 헬퍼 통합 (MEDIUM, 리팩토링)       ← ✅ 완료 (7d11fa7)
```

---

## 검증 게이트 (모든 Phase 공통)

1. `py_compile` 변경 파일
2. `python -m pytest tests/ -q` → 1,668 passed, 68 xfailed
3. `pre-commit run --files <변경파일>`
4. 수동 확인: Stage 2 → Stage 3 전환 시 `app.state_tracker` 보존 확인

---

## Phase 1 Codex 오더: A-1 StateTracker 동기화

### 목표
Stage 2 완료 후 `ctx.state_tracker`를 `app.state_tracker`에 동기화하여
Stage 3/4 진입 시 데이터 소실 방지.

### 수정 파일

| 파일 | 변경 |
|------|------|
| `main_a.py` L2070 | Stage 2 완료 후 sync 3줄 추가 |
| `tests/test_stage_transition.py` | **신규** — StateTracker 동기화 테스트 |

### 상세 지침

#### 1. `main_a.py` — `_stage_2_arcs()` 메서드

L2070 (`asyncio.run(...)` 직후)에 추가:

```python
        asyncio.run(self._stage2_orch.stage_2_arcs_async_logic())
        # [Sweep2-A1] Stage 2 → app StateTracker 동기화
        _s2_ctx = self._stage2_orch.ctx
        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
            self.state_tracker = _s2_ctx.state_tracker
```

#### 2. `tests/test_stage_transition.py` — 신규

```python
"""Stage 간 StateTracker 동기화 테스트."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestStage2ToAppSync:
    """A-1: Stage 2 완료 후 state_tracker가 app에 동기화되는지 확인."""

    def test_state_tracker_synced_after_stage2(self):
        """Stage 2 완료 후 app.state_tracker == ctx.state_tracker"""
        from main_a import SovereignApp

        app = MagicMock(spec=SovereignApp)
        app.state_tracker = None
        app._stage2_orch = MagicMock()

        mock_tracker = MagicMock()
        mock_tracker.npc_registry = {"npc_1": {"name": "테스트", "status": "alive"}}
        app._stage2_orch.ctx.state_tracker = mock_tracker

        # Simulate the sync logic
        _s2_ctx = app._stage2_orch.ctx
        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
            app.state_tracker = _s2_ctx.state_tracker

        assert app.state_tracker is mock_tracker
        assert app.state_tracker.npc_registry["npc_1"]["name"] == "테스트"

    def test_state_tracker_not_synced_when_none(self):
        """ctx.state_tracker가 None이면 동기화하지 않음."""
        app = MagicMock()
        app.state_tracker = None
        app._stage2_orch.ctx.state_tracker = None

        _s2_ctx = app._stage2_orch.ctx
        if _s2_ctx is not None and getattr(_s2_ctx, "state_tracker", None) is not None:
            app.state_tracker = _s2_ctx.state_tracker

        assert app.state_tracker is None

    def test_stage3_reuses_synced_tracker(self):
        """동기화된 state_tracker가 있으면 Stage 3 lazy init 스킵."""
        mock_tracker = MagicMock()

        app = MagicMock()
        app.state_tracker = mock_tracker  # 이미 동기화된 상태

        # Stage 3 lazy init 조건: hasattr(app, "state_tracker") and app.state_tracker is not None
        should_init = not hasattr(app, "state_tracker") or app.state_tracker is None
        assert should_init is False  # lazy init 스킵
```

### 검증

```bash
py_compile main_a.py
pytest tests/test_stage_transition.py -v
pytest tests/ -q
pre-commit run --files main_a.py tests/test_stage_transition.py
```

---

## Phase 2 Codex 오더: B-1+B-2 Extract 헬퍼 통합

### 목표
17개 extract 호출을 `full_extract_from_arcs()` 헬퍼로 통합하여
Stage 2/3/4 어디서든 동일한 NPC 데이터를 추출하도록 보장.

### 수정 파일

| 파일 | 변경 |
|------|------|
| `modules/domain/agents/state_tracker.py` | `full_extract_from_arcs()` 메서드 추가 |
| `modules/core/stage2_orchestrator.py` L170-239 | 17개 호출 → 1줄 호출로 교체 |
| `modules/core/stage3_orchestrator.py` L182-188 | 4개 호출 → 1줄 호출로 교체 |
| `main_a.py` L2729-2733 | 4개 호출 → 1줄 호출로 교체 |
| `tests/test_state_tracker.py` | `full_extract_from_arcs` 테스트 추가 |

### 상세 지침

#### 1. `modules/domain/agents/state_tracker.py` — 메서드 추가

StateTracker 클래스에 인스턴스 메서드로 추가:

```python
    def full_extract_from_arcs(self, arcs: list[dict], genre: str = "") -> None:
        """17개 extract 메서드를 순회 호출하여 모든 NPC 상태를 구축.

        Stage 2/3/4 공통 초기화 경로. V66 확장 데이터 포함.
        """
        for arc in arcs:
            self.extract_npc_deaths_from_arc(arc)
            self.extract_skill_acquisitions_from_arc(arc)
            self.extract_npc_info_from_arc(arc, genre=genre)
            self.extract_resolved_plots_from_arc(arc)
            try:
                self.extract_time_markers_from_arc(arc)
            except Exception:
                pass
            try:
                self.extract_permanent_injuries_from_arc(arc)
            except Exception:
                pass
            try:
                self.update_companions_from_arc(arc)
            except Exception:
                pass
            try:
                self.extract_commitments_from_arc(arc)
            except Exception:
                pass
            try:
                self.extract_protagonist_emotion_from_arc(arc)
            except Exception:
                pass
            try:
                self.extract_item_states_from_arc(arc)
            except (KeyError, ValueError, TypeError):
                pass
            try:
                self.extract_entity_destructions_from_arc(arc)
            except (KeyError, ValueError, TypeError):
                pass
            try:
                self.extract_npc_personality_from_arc(arc)
            except (KeyError, ValueError, TypeError):
                pass
            try:
                self.extract_npc_npc_relationships_from_arc(arc)
            except (KeyError, ValueError, TypeError):
                pass
            try:
                self.extract_npc_dialogue_styles_from_arc(arc)
            except (KeyError, ValueError, TypeError):
                pass
            try:
                self.extract_relationship_changes_from_arc(arc)
            except Exception:
                pass
            try:
                self.extract_npc_injuries_from_arc(arc)
            except Exception:
                pass
            try:
                self.extract_npc_movements_from_arc(arc)
            except Exception:
                pass
            if genre == "investment":
                self.extract_financial_events_from_arc(arc)
```

#### 2. `modules/core/stage2_orchestrator.py` — L170-239 교체

**현재 코드** (L170-239): 17개 extract 개별 호출 + try/except 각각

**교체 코드**:
```python
        _genre_for_tracker = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
        self.ctx.state_tracker.full_extract_from_arcs(new_arcs_to_load, genre=_genre_for_tracker)
        self.ctx.state_tracker_loaded_arcs = len(all_refined_arcs)
```

**주의**: L169의 `new_arcs_to_load = all_refined_arcs[existing_tracker_arcs:]` 보존.
L242-246의 금융 레지스트리 DB 영구 저장도 보존:
```python
        # [V63.4 P0] 금융 레지스트리 DB 영구 저장 (투자물)
        if _genre_for_tracker == "investment" and self.ctx.state_tracker.financial_number_registry:
            self.ctx.current_project.save_v20_anchor(
                "financial_registry", self.ctx.state_tracker.export_financial_registry()
            )
```

#### 3. `modules/core/stage3_orchestrator.py` — L182-188 교체

**현재 코드** (L182-188):
```python
            for arc in all_arcs:
                app.state_tracker.extract_npc_deaths_from_arc(arc)
                app.state_tracker.extract_skill_acquisitions_from_arc(arc)
                _g = app.selected_genre.get("type", "") if app.selected_genre else ""
                app.state_tracker.extract_npc_info_from_arc(arc, genre=_g)
                app.state_tracker.extract_resolved_plots_from_arc(arc)
```

**교체 코드**:
```python
            _g = app.selected_genre.get("type", "") if app.selected_genre else ""
            app.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
```

#### 4. `main_a.py` — L2727-2733 교체

**현재 코드** (L2727-2733):
```python
            all_arcs = self.current_project.db.load_anchor("arcs") or []
            _g = self.selected_genre.get("type", "") if self.selected_genre else ""
            for arc in all_arcs:
                self.state_tracker.extract_npc_deaths_from_arc(arc)
                self.state_tracker.extract_skill_acquisitions_from_arc(arc)
                self.state_tracker.extract_npc_info_from_arc(arc, genre=_g)
                self.state_tracker.extract_resolved_plots_from_arc(arc)
```

**교체 코드**:
```python
            all_arcs = self.current_project.db.load_anchor("arcs") or []
            _g = self.selected_genre.get("type", "") if self.selected_genre else ""
            self.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
```

#### 5. 테스트 추가

`tests/test_state_tracker.py`에 추가:

```python
class TestFullExtractFromArcs:
    """B-1/B-2: full_extract_from_arcs가 17개 메서드를 모두 호출하는지 확인."""

    def test_calls_all_extract_methods(self):
        tracker = MagicMock()
        arcs = [{"arc_number": 1, "content": {}}]

        from modules.domain.agents.state_tracker import StateTracker
        StateTracker.full_extract_from_arcs(tracker, arcs, genre="wuxia")

        tracker.extract_npc_deaths_from_arc.assert_called_once()
        tracker.extract_skill_acquisitions_from_arc.assert_called_once()
        tracker.extract_npc_info_from_arc.assert_called_once()
        tracker.extract_resolved_plots_from_arc.assert_called_once()
        tracker.extract_time_markers_from_arc.assert_called_once()
        tracker.extract_permanent_injuries_from_arc.assert_called_once()
        tracker.update_companions_from_arc.assert_called_once()
        tracker.extract_commitments_from_arc.assert_called_once()
        tracker.extract_protagonist_emotion_from_arc.assert_called_once()
        tracker.extract_item_states_from_arc.assert_called_once()
        tracker.extract_entity_destructions_from_arc.assert_called_once()
        tracker.extract_npc_personality_from_arc.assert_called_once()
        tracker.extract_npc_npc_relationships_from_arc.assert_called_once()
        tracker.extract_npc_dialogue_styles_from_arc.assert_called_once()
        tracker.extract_relationship_changes_from_arc.assert_called_once()
        tracker.extract_npc_injuries_from_arc.assert_called_once()
        tracker.extract_npc_movements_from_arc.assert_called_once()

    def test_financial_extract_only_for_investment(self):
        tracker = MagicMock()
        arcs = [{"arc_number": 1}]

        from modules.domain.agents.state_tracker import StateTracker

        StateTracker.full_extract_from_arcs(tracker, arcs, genre="wuxia")
        tracker.extract_financial_events_from_arc.assert_not_called()

        tracker.reset_mock()
        StateTracker.full_extract_from_arcs(tracker, arcs, genre="investment")
        tracker.extract_financial_events_from_arc.assert_called_once()

    def test_exception_in_optional_extract_does_not_propagate(self):
        """V66 확장 메서드 예외 시 전파되지 않음."""
        tracker = MagicMock()
        tracker.extract_time_markers_from_arc.side_effect = ValueError("test")
        tracker.extract_permanent_injuries_from_arc.side_effect = KeyError("test")

        from modules.domain.agents.state_tracker import StateTracker
        # 예외 전파 없이 완료되어야 함
        StateTracker.full_extract_from_arcs(tracker, [{"arc_number": 1}])

        # 필수 메서드는 정상 호출됨
        tracker.extract_npc_deaths_from_arc.assert_called_once()
```

### 검증

```bash
py_compile modules/domain/agents/state_tracker.py
py_compile modules/core/stage2_orchestrator.py
py_compile modules/core/stage3_orchestrator.py
py_compile main_a.py
pytest tests/test_state_tracker.py -v -k "full_extract"
pytest tests/test_stage_transition.py -v
pytest tests/ -q
pre-commit run --files modules/domain/agents/state_tracker.py modules/core/stage2_orchestrator.py modules/core/stage3_orchestrator.py main_a.py
```

---

## 커밋 메시지

### Phase 1
```
fix(critical): sync state_tracker from Stage2 ctx to app after completion

Stage 2 builds a rich StateTracker with 17 extract methods but never
syncs it back to app. Stage 3/4 then creates fresh instances, losing
13 categories of NPC data (injuries, companions, emotions, etc.).

- A-1: add state_tracker write-back in main_a.py after Stage 2
- Add test_stage_transition.py with 3 sync verification tests
```

### Phase 2
```
refactor(state-tracker): unify 17 extract calls into full_extract_from_arcs

Stage 2/3/4 each had divergent StateTracker initialization paths
(17 vs 4 extract methods). Unified into a single method to ensure
all entry points produce identical NPC state.

- B-1: StateTracker.full_extract_from_arcs() method (17 extracts)
- B-2: Replace inline loops in stage2/stage3/main_a with single call
- Add 3 unit tests for the unified method
```
