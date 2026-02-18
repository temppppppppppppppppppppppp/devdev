# Codex Order: Sweep2 Phase 2 — StateTracker Extract 헬퍼 통합 (B-1 + B-2)

## 목표

Stage 2/3/4에서 각각 다르게 호출하던 StateTracker extract 메서드(17개 vs 4개)를
`full_extract_from_arcs()` 인스턴스 메서드 하나로 통합.
어떤 Stage에서든 동일한 NPC 상태 데이터를 구축하도록 보장.

---

## 수정 파일 (4개) + 테스트 (1개)

| 파일 | 변경 |
|------|------|
| `modules/domain/agents/state_tracker.py` | `full_extract_from_arcs()` 인스턴스 메서드 추가 |
| `modules/core/stage2_orchestrator.py` | L171-239 인라인 루프 → 1줄 호출로 교체 |
| `modules/core/stage3_orchestrator.py` | L182-188 인라인 루프 → 1줄 호출로 교체 |
| `main_a.py` | L2735-2739 인라인 루프 → 1줄 호출로 교체 |
| `tests/test_state_tracker.py` | `TestFullExtractFromArcs` 클래스 3개 테스트 추가 |

---

## Step 1: `modules/domain/agents/state_tracker.py` — 메서드 추가

`StateTracker` 클래스(L96)에 인스턴스 메서드 추가.
`__init__` 메서드(L118) 아래 적절한 위치에 삽입. 다른 public 메서드들 근처에 배치.

```python
    def full_extract_from_arcs(self, arcs: list[dict], genre: str = "") -> None:
        """Arc 목록에서 17개 extract 메서드를 순회 호출하여 모든 NPC 상태를 구축.

        Stage 2/3/4 공통 초기화 경로. V66 확장 데이터 포함.
        개별 V66 확장 메서드 실패 시 로깅 후 계속 진행 (비차단).
        """
        import logging

        for arc in arcs:
            # ── 필수 4종 (기존 Stage3/4 lazy init과 동일) ──
            self.extract_npc_deaths_from_arc(arc)
            self.extract_skill_acquisitions_from_arc(arc)
            self.extract_npc_info_from_arc(arc, genre=genre)
            self.extract_resolved_plots_from_arc(arc)
            # ── V66 확장 13종 (soft-fail) ──
            try:
                self.extract_time_markers_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 시간선 추출 실패 (무시): %s", e)
            try:
                self.extract_permanent_injuries_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 신체 변화 추출 실패 (무시): %s", e)
            try:
                self.update_companions_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 동행자 추출 실패 (무시): %s", e)
            try:
                self.extract_commitments_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 약속 추출 실패 (무시): %s", e)
            try:
                self.extract_protagonist_emotion_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.1] 감정 추출 실패 (무시): %s", e)
            try:
                self.extract_item_states_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (major_items): %s", e)
            try:
                self.extract_entity_destructions_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (entity_destructions): %s", e)
            try:
                self.extract_npc_personality_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (npc_personality): %s", e)
            try:
                self.extract_npc_npc_relationships_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (npc_npc_relationships): %s", e)
            try:
                self.extract_npc_dialogue_styles_from_arc(arc)
            except (KeyError, ValueError, TypeError) as e:
                logging.warning("[V66.3] Init load 복원 실패 (dialogue_profiles): %s", e)
            try:
                self.extract_relationship_changes_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.2] 관계 변화 추출 실패 (무시): %s", e)
            try:
                self.extract_npc_injuries_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.2] NPC 부상 추출 실패 (무시): %s", e)
            try:
                self.extract_npc_movements_from_arc(arc)
            except Exception as e:
                logging.warning("[V66.2] NPC 이동 추출 실패 (무시): %s", e)
            # ── 장르 특화 ──
            if genre == "investment":
                self.extract_financial_events_from_arc(arc)
```

---

## Step 2: `modules/core/stage2_orchestrator.py` — L171-239 교체

### 현재 코드 (L171-239, 69줄):
```python
        for prev_arc in new_arcs_to_load:
            self.ctx.state_tracker.extract_npc_deaths_from_arc(prev_arc)
            ... (17개 개별 호출 + try/except 각각)
            if _genre_for_tracker == "investment":
                self.ctx.state_tracker.extract_financial_events_from_arc(prev_arc)
```

### 교체할 코드 (2줄):
```python
        self.ctx.state_tracker.full_extract_from_arcs(new_arcs_to_load, genre=_genre_for_tracker)
```

**정확한 교체 범위**:
- 삭제: L171 `for prev_arc in new_arcs_to_load:` ~ L239 `self.ctx.state_tracker.extract_financial_events_from_arc(prev_arc)` (69줄)
- 삽입: 위의 1줄
- **보존**: L170 (`_genre_for_tracker = ...`)과 L240 (`self.ctx.state_tracker_loaded_arcs = ...`) 그대로 유지

교체 후 해당 영역은 다음과 같아야 함:
```python
        new_arcs_to_load = all_refined_arcs[existing_tracker_arcs:]
        _genre_for_tracker = self.ctx.selected_genre.get("type", "") if self.ctx.selected_genre else ""
        self.ctx.state_tracker.full_extract_from_arcs(new_arcs_to_load, genre=_genre_for_tracker)
        self.ctx.state_tracker_loaded_arcs = len(all_refined_arcs)
```

---

## Step 3: `modules/core/stage3_orchestrator.py` — L182-188 교체

### 현재 코드 (L182-188):
```python
            all_arcs = app.current_project.db.load_anchor("arcs") or []
            for arc in all_arcs:
                app.state_tracker.extract_npc_deaths_from_arc(arc)
                app.state_tracker.extract_skill_acquisitions_from_arc(arc)
                _g = app.selected_genre.get("type", "") if app.selected_genre else ""
                app.state_tracker.extract_npc_info_from_arc(arc, genre=_g)
                app.state_tracker.extract_resolved_plots_from_arc(arc)
```

### 교체할 코드:
```python
            all_arcs = app.current_project.db.load_anchor("arcs") or []
            _g = app.selected_genre.get("type", "") if app.selected_genre else ""
            app.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
```

**보존**: L189~ (`if app.state_tracker.npc_registry:`) 이후 그대로 유지.

---

## Step 4: `main_a.py` — L2733-2739 교체

### 현재 코드 (L2733-2739):
```python
            all_arcs = self.current_project.db.load_anchor("arcs") or []
            _g = self.selected_genre.get("type", "") if self.selected_genre else ""
            for arc in all_arcs:
                self.state_tracker.extract_npc_deaths_from_arc(arc)
                self.state_tracker.extract_skill_acquisitions_from_arc(arc)
                self.state_tracker.extract_npc_info_from_arc(arc, genre=_g)
                self.state_tracker.extract_resolved_plots_from_arc(arc)
```

### 교체할 코드:
```python
            all_arcs = self.current_project.db.load_anchor("arcs") or []
            _g = self.selected_genre.get("type", "") if self.selected_genre else ""
            self.state_tracker.full_extract_from_arcs(all_arcs, genre=_g)
```

**보존**: L2740~ (`if self.state_tracker.npc_registry:`) 이후 그대로 유지.

---

## Step 5: `tests/test_state_tracker.py` — 테스트 추가

파일 끝에 `TestFullExtractFromArcs` 클래스 추가:

```python
class TestFullExtractFromArcs:
    """B-1/B-2: full_extract_from_arcs가 17개 메서드를 모두 호출하는지 확인."""

    def test_calls_all_17_extract_methods(self):
        """17개 extract 메서드 전부 호출 확인."""
        from unittest.mock import MagicMock

        tracker = MagicMock(spec=StateTracker)
        arcs = [{"arc_number": 1, "content": {}}]

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

    def test_financial_extract_only_for_investment_genre(self):
        """투자물 장르에서만 금융 이벤트 추출 호출."""
        from unittest.mock import MagicMock

        tracker = MagicMock(spec=StateTracker)
        arcs = [{"arc_number": 1}]

        StateTracker.full_extract_from_arcs(tracker, arcs, genre="wuxia")
        tracker.extract_financial_events_from_arc.assert_not_called()

        tracker.reset_mock()
        StateTracker.full_extract_from_arcs(tracker, arcs, genre="investment")
        tracker.extract_financial_events_from_arc.assert_called_once()

    def test_optional_extract_exception_does_not_propagate(self):
        """V66 확장 메서드 예외 시 전파되지 않고 필수 메서드는 정상 호출."""
        from unittest.mock import MagicMock

        tracker = MagicMock(spec=StateTracker)
        tracker.extract_time_markers_from_arc.side_effect = ValueError("test")
        tracker.extract_permanent_injuries_from_arc.side_effect = KeyError("test")
        tracker.extract_npc_personality_from_arc.side_effect = TypeError("test")

        # 예외 전파 없이 완료되어야 함
        StateTracker.full_extract_from_arcs(tracker, [{"arc_number": 1}])

        # 필수 4종은 정상 호출됨
        tracker.extract_npc_deaths_from_arc.assert_called_once()
        tracker.extract_skill_acquisitions_from_arc.assert_called_once()
        tracker.extract_npc_info_from_arc.assert_called_once()
        tracker.extract_resolved_plots_from_arc.assert_called_once()
```

---

## 검증 게이트

```bash
py_compile modules/domain/agents/state_tracker.py
py_compile modules/core/stage2_orchestrator.py
py_compile modules/core/stage3_orchestrator.py
py_compile main_a.py

pytest tests/test_state_tracker.py -v -k "FullExtract"
pytest tests/test_stage_transition.py -v
pytest tests/ -q
pre-commit run --files modules/domain/agents/state_tracker.py modules/core/stage2_orchestrator.py modules/core/stage3_orchestrator.py main_a.py tests/test_state_tracker.py
```

예상: 1,665+ passed, 68 xfailed

---

## 커밋

```
refactor(state-tracker): unify 17 extract calls into full_extract_from_arcs

Stage 2/3/4 each had divergent StateTracker init paths (17 vs 4 extract
methods). Unified into StateTracker.full_extract_from_arcs() to ensure
all entry points produce identical NPC state data.

- Add StateTracker.full_extract_from_arcs() with 17 extracts + soft-fail
- Replace inline loops in stage2_orchestrator (69 lines → 1 line)
- Replace inline loops in stage3_orchestrator (7 lines → 2 lines)
- Replace inline loops in main_a.py Stage4 init (7 lines → 2 lines)
- Add 3 unit tests for the unified method

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

push 포함.
