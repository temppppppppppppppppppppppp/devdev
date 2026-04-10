"""
[W1] Stage 2 -> Stage 3 Episode Boundary Guardrail Tests

Regression tests for Wave 1 of the episode-boundary fix:
- state_changes filtering by ep_num
- stop line expansion beyond ep+1
- treatment block event-field quarantine
"""

from unittest.mock import MagicMock

import pytest

from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def compiler():
    return BlueprintConstraintCompiler()


@pytest.fixture
def arc_data_4ep():
    """4-episode arc with state_changes containing per-episode events."""
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_count": 4,
        "ep_end": 4,
        "tactical_doc": "제1화: 도입\n제2화: 전개\n제3화: 절정\n제4화: 결말",
        "beat_sequence": ["beat1", "beat2", "beat3", "beat4"],
        "episode_details": [
            {"ep_num": 1, "details": ["주인공 등장", "배경 설명"]},
            {"ep_num": 2, "details": ["첫 대결", "동맹 결성"]},
            {"ep_num": 3, "details": ["반전 발생", "위기 고조"]},
            {"ep_num": 4, "details": ["최종 대결", "결말"]},
        ],
        "state_changes": {
            "npc_deaths": [
                {"name": "장로A", "episode": 1, "cause": "독살"},
                {"name": "장로B", "episode": 3, "cause": "전투"},
                {"name": "보스", "episode": 4, "cause": "결투"},
            ],
            "skill_acquisitions": [
                {"name": "기본검법", "episode": 1},
                {"name": "비급무공", "episode": 4},
            ],
            "relationship_changes": [
                {"npc": "소림승", "from": "적", "to": "동맹", "episode": 2},
                {"npc": "사형", "from": "동맹", "to": "적", "episode": 4},
            ],
            "major_items": [
                {"name": "검", "action": "획득", "episode": 1},
                {"name": "비급서", "action": "획득", "episode": 3},
            ],
            "npc_injuries": [
                {"name": "주인공", "injury": "팔 부상", "episode": 2},
            ],
            "npc_movements": [
                {"name": "사형", "to": "마교", "episode": 4},
            ],
            "resolved_plots": [
                {"plot": "문파 내분", "arc_no": 1, "episode": 3},
            ],
        },
        "joint_docs": {},
        "state_constraints": {},
        "constraint_summary": "",
        "semantic_carryover": {},
    }


# ── Seam 1: state_changes Episode Filtering ──────────────────


class TestStateChangesEpisodeFiltering:
    """_summarize_state_changes must exclude entries where episode > ep_num."""

    def test_ep1_excludes_future_deaths(self, compiler, arc_data_4ep):
        """EP1: 장로A(ep1) visible, 장로B(ep3) and 보스(ep4) excluded."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "장로A" in result
        assert "장로B" not in result
        assert "보스" not in result

    def test_ep3_includes_up_to_ep3(self, compiler, arc_data_4ep):
        """EP3: 장로A(ep1), 장로B(ep3) visible; 보스(ep4) excluded."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=3)
        assert "장로A" in result
        assert "장로B" in result
        assert "보스" not in result

    def test_ep4_includes_all(self, compiler, arc_data_4ep):
        """EP4 (last): all entries visible."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=4)
        assert "장로A" in result
        assert "장로B" in result
        assert "보스" in result

    def test_ep1_excludes_future_skills(self, compiler, arc_data_4ep):
        """EP1: 기본검법(ep1) visible, 비급무공(ep4) excluded."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "기본검법" in result
        assert "비급무공" not in result

    def test_ep1_excludes_future_relationships(self, compiler, arc_data_4ep):
        """EP1: no relationship changes visible (all are ep2+)."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "소림승" not in result
        assert "사형" not in result

    def test_ep2_includes_ep2_relationships(self, compiler, arc_data_4ep):
        """EP2: 소림승(ep2) visible, 사형(ep4) excluded."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=2)
        assert "소림승" in result
        assert "사형" not in result

    def test_ep1_excludes_future_items(self, compiler, arc_data_4ep):
        """EP1: 검(ep1) visible, 비급서(ep3) excluded."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "검" in result
        assert "비급서" not in result

    def test_ep1_excludes_future_movements(self, compiler, arc_data_4ep):
        """EP1: no movements visible (사형 이동 is ep4)."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "마교" not in result

    def test_ep1_excludes_future_resolved_plots(self, compiler, arc_data_4ep):
        """EP1: no resolved plots visible (문파 내분 is ep3)."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "문파 내분" not in result

    def test_no_episode_field_included(self, compiler):
        """Entries without 'episode' field are always included."""
        state_changes = {
            "npc_deaths": [{"name": "무명NPC"}],
        }
        result = compiler._summarize_state_changes(state_changes, ep_num=1)
        assert "무명NPC" in result

    def test_string_entries_always_included(self, compiler):
        """String entries (no dict) are always included."""
        state_changes = {
            "npc_deaths": ["장로X 사망"],
        }
        result = compiler._summarize_state_changes(state_changes, ep_num=1)
        assert "장로X 사망" in result

    def test_ep_num_zero_shows_all(self, compiler, arc_data_4ep):
        """ep_num=0 (default) shows all entries without filtering."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=0)
        assert "장로A" in result
        assert "보스" in result
        assert "비급무공" in result

    def test_compile_passes_ep_num(self, compiler, arc_data_4ep):
        """compile() passes ep_num to _summarize_state_changes — future entries excluded."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        summary = block["state_changes_summary"]
        assert "장로A" in summary
        assert "보스" not in summary
        assert "비급무공" not in summary


class TestStage3FidelityEpisodeBoundary:
    """Stage3 fidelity hints must not pressure EPs with future-only relationship changes."""

    def test_future_only_relationship_changes_do_not_trigger_ep1_warning(self):
        from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator

        validator = UnifiedBlueprintValidator(MagicMock(), MagicMock())
        issues = validator._collect_fidelity_prevalidation_issues(
            integrated="한시우가 첫 투자 발표를 준비한다.",
            arc_data={
                "state_constraints": {
                    "relationship_changes": [
                        {"npc": "큰형", "episode": 2},
                        {"npc": "아버지", "episode": 3},
                    ]
                }
            },
            ep_num=1,
        )

        assert issues == []

    def test_current_episode_relationship_change_still_triggers_warning_when_missing(self):
        from modules.domain.agents.unified_blueprint_validator import UnifiedBlueprintValidator

        validator = UnifiedBlueprintValidator(MagicMock(), MagicMock())
        issues = validator._collect_fidelity_prevalidation_issues(
            integrated="한시우가 첫 투자 발표를 준비한다.",
            arc_data={
                "state_constraints": {
                    "relationship_changes": [
                        {"npc": "아버지", "episode": 1},
                        {"npc": "큰형", "episode": 3},
                    ]
                }
            },
            ep_num=1,
        )

        assert len(issues) == 1
        assert issues[0]["category"] == "fidelity"
        assert "1명" in issues[0]["issue"]


# ── Seam 2: Treatment Block Event Quarantine ──────────────────


class TestTreatmentBlockQuarantine:
    """Treatment block must not inject per-episode event fields."""

    def test_treatment_block_excludes_event_fields(self):
        """event_villain, solution, reward, power_shift should not appear."""
        from modules.core.stage3_orchestrator import Stage3Orchestrator

        app = MagicMock()
        app.current_project = MagicMock()
        app.current_project.master_bible = {
            "MasterBible": {
                "plot_roadmap": [
                    {
                        "title": "테스트 아크",
                        "emotional_beat": "상승",
                        "foreshadow": "복선 설정",
                        "event_villain": "EP3에서 마왕 등장",
                        "solution": "EP4에서 무공으로 해결",
                        "reward": "비급서 획득",
                        "power_shift": "세력 전환",
                        "content": {
                            "context": "아크 배경 설명",
                            "event_villain": "마왕이 EP3에서 나타남",
                            "solution": "EP4 최종 대결로 해결",
                        },
                    }
                ],
            },
        }
        orch = Stage3Orchestrator.__new__(Stage3Orchestrator)
        orch.ctx = MagicMock()
        orch.ctx.current_project = app.current_project

        arc_data = {"ep_start": 1, "ep_end": 4}
        result = orch._inject_stage3_treatment_block_context(
            semantic_ctx="", working_ep=1, arc_data=arc_data, arc_idx=0
        )

        # Safe arc-framing fields should be present
        assert "테스트 아크" in result
        assert "상승" in result
        assert "복선 설정" in result
        assert "아크 배경 설명" in result

        # Per-episode event fields should NOT be present
        assert "마왕 등장" not in result
        assert "무공으로 해결" not in result
        assert "비급서 획득" not in result
        assert "세력 전환" not in result
        assert "마왕이 EP3" not in result
        assert "최종 대결" not in result

    def test_treatment_block_header_structural_guard(self):
        """Treatment block header should indicate arc-overview-only."""
        from modules.core.stage3_orchestrator import Stage3Orchestrator

        app = MagicMock()
        app.current_project = MagicMock()
        app.current_project.master_bible = {
            "MasterBible": {
                "plot_roadmap": [{"title": "Test Arc", "emotional_beat": "rising"}]
            },
        }
        orch = Stage3Orchestrator.__new__(Stage3Orchestrator)
        orch.ctx = MagicMock()
        orch.ctx.current_project = app.current_project

        result = orch._inject_stage3_treatment_block_context(
            semantic_ctx="", working_ep=1, arc_data={"ep_start": 1, "ep_end": 4}, arc_idx=0
        )

        assert "Arc 개요" in result
        assert "방향성" in result
        assert "제거되었습니다" in result


# ── Seam 3: Stop Line Expansion ──────────────────────────────


class TestStopLineExpansion:
    """Stop line must cover ALL future episodes, not only ep+1."""

    def test_ep1_stop_line_covers_all_future(self, compiler, arc_data_4ep):
        """EP1: stop line should reference ep2, ep3, and ep4."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        stop_line = block["stop_line"]
        assert not stop_line.get("is_arc_finale")
        assert stop_line.get("next_ep") == 2
        future_ep_nums = [fe["ep"] for fe in stop_line.get("future_eps", [])]
        assert 3 in future_ep_nums
        assert 4 in future_ep_nums

    def test_ep2_stop_line_has_ep3_and_ep4(self, compiler, arc_data_4ep):
        """EP2: stop line next=3, future_eps contains ep4."""
        block = compiler.compile(arc_data_4ep, ep_num=2)
        stop_line = block["stop_line"]
        assert stop_line.get("next_ep") == 3
        future_ep_nums = [fe["ep"] for fe in stop_line.get("future_eps", [])]
        assert 4 in future_ep_nums

    def test_ep3_stop_line_no_future_beyond_next(self, compiler, arc_data_4ep):
        """EP3: stop line next=4, no future eps beyond ep4."""
        block = compiler.compile(arc_data_4ep, ep_num=3)
        stop_line = block["stop_line"]
        assert stop_line.get("next_ep") == 4
        assert len(stop_line.get("future_eps", [])) == 0

    def test_ep4_stop_line_is_finale(self, compiler, arc_data_4ep):
        """EP4 (last): is_arc_finale should be True."""
        block = compiler.compile(arc_data_4ep, ep_num=4)
        stop_line = block["stop_line"]
        assert stop_line.get("is_arc_finale") is True

    def test_prompt_contains_blanket_prohibition(self, compiler, arc_data_4ep):
        """compile_to_prompt for ep1 should contain blanket prohibition."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "모든 에피소드 사건" in prompt
        assert "REJECT" in prompt

    def test_prompt_lists_future_episodes(self, compiler, arc_data_4ep):
        """compile_to_prompt for ep1 should list ep3 and ep4."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "[제3화]" in prompt
        assert "[제4화]" in prompt

    def test_prompt_arc_finale_no_prohibition(self, compiler, arc_data_4ep):
        """compile_to_prompt for the last ep should say 정지선 없음."""
        block = compiler.compile(arc_data_4ep, ep_num=4)
        prompt = compiler.compile_to_prompt(block)
        assert "정지선 없음" in prompt


# ── Integration: compile → compile_to_prompt ──────────────────


class TestCompileIntegration:
    """End-to-end: ep1 prompt must exclude future events and preserve positive authority."""

    def test_ep1_prompt_excludes_ep4_events(self, compiler, arc_data_4ep):
        """EP1 prompt must not contain EP4 state_changes content."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "보스" not in prompt
        assert "비급무공" not in prompt
        assert "장로A" in prompt

    def test_ep1_preserves_positive_authority(self, compiler, arc_data_4ep):
        """EP1 prompt must preserve episode_details and must_focus."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "MUST_FOCUS" in prompt
        assert "STOP_LINE" in prompt
        assert "CONTINUITY" in prompt
        assert "INHERITED_STATE" in prompt

    def test_ep1_state_changes_header_updated(self, compiler, arc_data_4ep):
        """state_changes section header should say '현재 화까지 확정된 이벤트'."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "현재 화까지 확정된 이벤트" in prompt
