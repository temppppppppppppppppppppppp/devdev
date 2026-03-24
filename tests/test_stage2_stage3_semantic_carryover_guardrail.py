"""
[W2] Stage 2 -> Stage 3 Semantic Carryover Boundary Guardrail Tests

Regression tests for Wave 2:
- Tranche A: semantic_carryover quarantine (continuity_checkpoints, growth_justification suppressed)
- Tranche B: IFC episode filtering for ep2+
- Tranche C: future_eps rendering in blueprint_ensemble._format_constraints()
"""

import pytest

from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def compiler():
    return BlueprintConstraintCompiler()


@pytest.fixture
def arc_data_with_semantic_carryover():
    """4-episode arc with semantic_carryover containing arc-end state."""
    return {
        "arc_no": 1,
        "ep_start": 1,
        "ep_count": 4,
        "ep_end": 4,
        "tactical_doc": "제1화: 도입\n제2화: 전개\n제3화: 절정\n제4화: 결말",
        "beat_sequence": ["beat1", "beat2", "beat3", "beat4"],
        "episode_details": [
            {"ep_num": 1, "details": ["주인공 등장"]},
            {"ep_num": 2, "details": ["첫 대결"]},
            {"ep_num": 3, "details": ["반전 발생"]},
            {"ep_num": 4, "details": ["최종 대결"]},
        ],
        "state_changes": {
            "npc_deaths": [
                {"name": "장로A", "episode": 1, "cause": "독살"},
                {"name": "보스", "episode": 4, "cause": "결투"},
            ],
            "relationship_changes": [
                {"npc": "동맹A", "from": "적", "to": "동맹", "episode": 2},
                {"npc": "사형", "from": "동맹", "to": "적", "episode": 4},
                {"npc": "원로", "from": "중립", "to": "우호"},  # episode=null
            ],
            "major_items": [
                {"name": "검", "action": "획득", "episode": 1},
                {"name": "법인인감도장", "action": "획득", "episode": 4},
                {"name": "OTP카드", "action": "획득", "episode": 4},
            ],
            "skill_acquisitions": [
                {"name": "기본검법", "episode": 1},
                {"name": "비급무공", "episode": 4},
            ],
        },
        "semantic_carryover": {
            "continuity_checkpoints": [
                "20억 자본금 확보 완료",
                "가족 감시망 완전 이탈",
                "법인 설립 완료",
            ],
            "growth_justification": "미래 경제 지식 각성 및 20억 원 확보",
            "foreshadow_anchors": [
                "유가 상승 뉴스 보도",
                "아버지 발언: 형들이 알아서",
            ],
            "relationship_rationale": [
                {"npc": "아버지", "trigger": "투자사 설립 선언"},
                {"npc": "큰형", "trigger": "막내 사업 선언"},
            ],
        },
        "joint_docs": {},
        "state_constraints": {},
        "constraint_summary": "",
    }


# ── Tranche A: Semantic Carryover Quarantine ─────────────────


class TestSemanticCarryoverQuarantine:
    """continuity_checkpoints and growth_justification must be suppressed."""

    def test_normalize_suppresses_continuity_checkpoints(self, compiler):
        """_normalize_semantic_carryover must not include continuity_checkpoints."""
        payload = {
            "continuity_checkpoints": ["20억 확보", "법인 설립 완료"],
            "relationship_rationale": [{"npc": "A", "trigger": "test"}],
        }
        result = compiler._normalize_semantic_carryover(payload)
        assert "continuity_checkpoints" not in result

    def test_normalize_suppresses_growth_justification(self, compiler):
        """_normalize_semantic_carryover must not include growth_justification."""
        payload = {
            "growth_justification": "경제 지식 각성 및 자본 확보",
            "relationship_rationale": [{"npc": "A", "trigger": "test"}],
        }
        result = compiler._normalize_semantic_carryover(payload)
        assert "growth_justification" not in result

    def test_normalize_preserves_relationship_rationale(self, compiler):
        """relationship_rationale must remain as relational context."""
        payload = {
            "relationship_rationale": [{"npc": "아버지", "trigger": "투자사 설립"}],
        }
        result = compiler._normalize_semantic_carryover(payload)
        assert "relationship_rationale" in result
        assert result["relationship_rationale"][0]["npc"] == "아버지"

    def test_normalize_preserves_foreshadow_anchors(self, compiler):
        """foreshadow_anchors must remain (with advisory label at render time)."""
        payload = {
            "foreshadow_anchors": ["유가 뉴스", "발언"],
        }
        result = compiler._normalize_semantic_carryover(payload)
        assert "foreshadow_anchors" in result
        assert len(result["foreshadow_anchors"]) == 2

    def test_format_lines_no_continuity_checkpoints(self, compiler):
        """_format_semantic_carryover_lines must not render continuity checkpoints."""
        payload = {
            "continuity_checkpoints": ["20억 확보", "법인 설립 완료"],
            "relationship_rationale": [{"npc": "A", "trigger": "test"}],
        }
        lines = compiler._format_semantic_carryover_lines(payload)
        joined = "\n".join(lines)
        assert "20억 확보" not in joined
        assert "법인 설립" not in joined
        assert "continuity:" not in joined

    def test_format_lines_no_growth_justification(self, compiler):
        """_format_semantic_carryover_lines must not render growth_justification."""
        payload = {
            "growth_justification": "경제 지식 각성 및 자본 확보",
        }
        lines = compiler._format_semantic_carryover_lines(payload)
        joined = "\n".join(lines)
        assert "growth_justification" not in joined
        assert "경제 지식" not in joined

    def test_format_lines_foreshadow_has_advisory_label(self, compiler):
        """foreshadow lines must have future-only advisory label."""
        payload = {
            "foreshadow_anchors": ["유가 상승 뉴스"],
        }
        lines = compiler._format_semantic_carryover_lines(payload)
        assert any("미래 복선 참고용" in line for line in lines)
        assert any("유가 상승 뉴스" in line for line in lines)

    def test_compile_to_prompt_ep1_no_arc_end_obligations(
        self, compiler, arc_data_with_semantic_carryover
    ):
        """EP1 prompt must not expose arc-end completion items as current-ep obligations."""
        block = compiler.compile(arc_data_with_semantic_carryover, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "20억 자본금 확보" not in prompt
        assert "법인 설립 완료" not in prompt
        assert "경제 지식 각성" not in prompt

    def test_compile_to_prompt_ep1_preserves_positive_authority(
        self, compiler, arc_data_with_semantic_carryover
    ):
        """EP1 prompt must still include must_focus, continuity, inherited_state."""
        block = compiler.compile(arc_data_with_semantic_carryover, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "MUST_FOCUS" in prompt
        assert "STOP_LINE" in prompt
        assert "CONTINUITY" in prompt
        assert "INHERITED_STATE" in prompt

    def test_compile_to_prompt_ep1_preserves_foreshadow_as_advisory(
        self, compiler, arc_data_with_semantic_carryover
    ):
        """EP1 prompt may include foreshadow with future-only advisory label."""
        block = compiler.compile(arc_data_with_semantic_carryover, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "유가 상승 뉴스" in prompt
        assert "미래 복선 참고용" in prompt

    def test_compile_to_prompt_ep1_preserves_relationship_rationale(
        self, compiler, arc_data_with_semantic_carryover
    ):
        """EP1 prompt must still include relationship rationale as context."""
        block = compiler.compile(arc_data_with_semantic_carryover, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "아버지" in prompt
        assert "relationship" in prompt


# ── Tranche B: IFC Episode Filtering ─────────────────────────


class TestIFCEpisodeFiltering:
    """_extract_immutable_fact_carryover must filter by episode for ep2+."""

    def test_ep1_ifc_returns_empty(self, compiler, arc_data_with_semantic_carryover):
        """EP1 (arc_position=1): IFC returns empty string."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=1, ep_num=1
        )
        assert result == ""

    def test_ep2_ifc_excludes_ep4_items(self, compiler, arc_data_with_semantic_carryover):
        """EP2 (arc_position=2): must not include ep4 items."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=2
        )
        assert "법인인감도장" not in result
        assert "OTP카드" not in result
        assert "비급무공" not in result

    def test_ep2_ifc_includes_ep1_death(self, compiler, arc_data_with_semantic_carryover):
        """EP2: ep1 death (장로A) should be present."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=2
        )
        assert "장로A" in result

    def test_ep2_ifc_excludes_ep4_death(self, compiler, arc_data_with_semantic_carryover):
        """EP2: ep4 death (보스) must not appear."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=2
        )
        assert "보스" not in result

    def test_ep2_ifc_excludes_ep4_relationships(self, compiler, arc_data_with_semantic_carryover):
        """EP2: ep4 relationship change (사형) must not appear."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=2
        )
        assert "사형" not in result

    def test_ep2_ifc_includes_ep2_relationships(self, compiler, arc_data_with_semantic_carryover):
        """EP2: ep2 relationship change (동맹A) should be present."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=2
        )
        assert "동맹A" in result

    def test_ep2_ifc_includes_null_episode_entries(self, compiler, arc_data_with_semantic_carryover):
        """EP2: null-episode entries (원로) pass through as arc-global."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=2
        )
        assert "원로" in result

    def test_ep4_ifc_includes_all(self, compiler, arc_data_with_semantic_carryover):
        """EP4 (last): all entries visible."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=4, ep_num=4
        )
        assert "장로A" in result
        assert "보스" in result
        assert "법인인감도장" in result
        assert "비급무공" in result

    def test_compile_passes_ep_num_to_ifc(self, compiler, arc_data_with_semantic_carryover):
        """compile() for ep2 must produce IFC output excluding ep4 items."""
        block = compiler.compile(arc_data_with_semantic_carryover, ep_num=2)
        ifc = block["immutable_fact_carryover"]
        assert "법인인감도장" not in ifc
        assert "OTP카드" not in ifc
        assert "장로A" in ifc

    def test_ep0_ifc_shows_all(self, compiler, arc_data_with_semantic_carryover):
        """ep_num=0 (default) shows all entries without filtering."""
        result = compiler._extract_immutable_fact_carryover(
            arc_data_with_semantic_carryover, arc_position=2, ep_num=0
        )
        assert "법인인감도장" in result
        assert "보스" in result


# ── Tranche C: Stop-Line Live Prompt Parity ──────────────────


class TestStopLineLivePromptParity:
    """blueprint_ensemble._format_constraints must render all-future stop lines."""

    @pytest.fixture
    def ensemble(self):
        """Minimal BlueprintEnsembleGenerator for _format_constraints testing."""
        from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator

        gen = BlueprintEnsembleGenerator.__new__(BlueprintEnsembleGenerator)
        return gen

    def test_format_constraints_renders_future_eps(self, ensemble):
        """_format_constraints must render future_eps entries beyond next_ep."""
        constraint_block = {
            "ep_num": 1,
            "must_focus": {"content": "주인공 등장", "key_events": [], "arc_title": ""},
            "stop_line": {
                "content": "다음 화 내용",
                "is_arc_finale": False,
                "next_ep": 2,
                "future_eps": [
                    {"ep": 3, "content": "반전 발생"},
                    {"ep": 4, "content": "최종 대결"},
                ],
            },
            "continuity": {},
            "inherited_state": {},
            "arc_constraint_summary": "",
            "state_changes_summary": "",
            "semantic_carryover": {},
        }
        result = ensemble._format_constraints(constraint_block)
        assert "[제3화]" in result
        assert "반전 발생" in result
        assert "[제4화]" in result
        assert "최종 대결" in result

    def test_format_constraints_blanket_prohibition(self, ensemble):
        """_format_constraints must include blanket all-future prohibition."""
        constraint_block = {
            "ep_num": 1,
            "must_focus": {"content": "주인공 등장", "key_events": [], "arc_title": ""},
            "stop_line": {
                "content": "다음 화 내용",
                "is_arc_finale": False,
                "next_ep": 2,
                "future_eps": [],
            },
            "continuity": {},
            "inherited_state": {},
            "arc_constraint_summary": "",
            "state_changes_summary": "",
            "semantic_carryover": {},
        }
        result = ensemble._format_constraints(constraint_block)
        assert "REJECT" in result
        assert "모든 에피소드" in result

    def test_format_constraints_arc_finale_no_stop_line(self, ensemble):
        """Arc finale: no stop line section rendered."""
        constraint_block = {
            "ep_num": 4,
            "must_focus": {"content": "최종 대결", "key_events": [], "arc_title": ""},
            "stop_line": {
                "content": None,
                "is_arc_finale": True,
            },
            "continuity": {},
            "inherited_state": {},
            "arc_constraint_summary": "",
            "state_changes_summary": "",
            "semantic_carryover": {},
        }
        result = ensemble._format_constraints(constraint_block)
        assert "Stop Line" not in result
        assert "REJECT" not in result

    def test_format_constraints_no_growth_no_checkpoints(self, ensemble):
        """[W2] _format_constraints must not render growth or checkpoints."""
        constraint_block = {
            "ep_num": 1,
            "must_focus": {"content": "주인공 등장", "key_events": [], "arc_title": ""},
            "stop_line": {"content": None, "is_arc_finale": True},
            "continuity": {},
            "inherited_state": {},
            "arc_constraint_summary": "",
            "state_changes_summary": "",
            "semantic_carryover": {
                "growth_justification": "경제 지식 각성",
                "continuity_checkpoints": ["20억 확보", "법인 설립"],
                "relationship_rationale": [{"npc": "A", "trigger": "test"}],
            },
        }
        result = ensemble._format_constraints(constraint_block)
        assert "경제 지식 각성" not in result
        assert "20억 확보" not in result
        assert "법인 설립" not in result
        # relationship should remain
        assert "relationship A" in result

    def test_format_constraints_foreshadow_advisory_label(self, ensemble):
        """[W2] foreshadow in _format_constraints must have advisory label."""
        constraint_block = {
            "ep_num": 1,
            "must_focus": {"content": "주인공 등장", "key_events": [], "arc_title": ""},
            "stop_line": {"content": None, "is_arc_finale": True},
            "continuity": {},
            "inherited_state": {},
            "arc_constraint_summary": "",
            "state_changes_summary": "",
            "semantic_carryover": {
                "foreshadow_anchors": ["유가 뉴스"],
            },
        }
        result = ensemble._format_constraints(constraint_block)
        assert "미래 복선 참고용" in result
        assert "유가 뉴스" in result


# ── Wave 1 Regression Guard ──────────────────────────────────


class TestWave1RegressionGuard:
    """Wave 2 changes must not break Wave 1 guarantees."""

    @pytest.fixture
    def arc_data_4ep(self):
        return {
            "arc_no": 1,
            "ep_start": 1,
            "ep_count": 4,
            "ep_end": 4,
            "tactical_doc": "제1화: 도입\n제2화: 전개\n제3화: 절정\n제4화: 결말",
            "beat_sequence": ["beat1", "beat2", "beat3", "beat4"],
            "episode_details": [
                {"ep_num": 1, "details": ["주인공 등장"]},
                {"ep_num": 2, "details": ["첫 대결"]},
                {"ep_num": 3, "details": ["반전 발생"]},
                {"ep_num": 4, "details": ["최종 대결"]},
            ],
            "state_changes": {
                "npc_deaths": [
                    {"name": "장로A", "episode": 1},
                    {"name": "보스", "episode": 4},
                ],
                "skill_acquisitions": [
                    {"name": "기본검법", "episode": 1},
                    {"name": "비급무공", "episode": 4},
                ],
            },
            "joint_docs": {},
            "state_constraints": {},
            "constraint_summary": "",
            "semantic_carryover": {},
        }

    def test_w1_state_changes_filter_still_works(self, compiler, arc_data_4ep):
        """Wave 1 _within_ep filter must still exclude future entries."""
        result = compiler._summarize_state_changes(arc_data_4ep["state_changes"], ep_num=1)
        assert "장로A" in result
        assert "보스" not in result
        assert "비급무공" not in result

    def test_w1_stop_line_future_eps_still_collected(self, compiler, arc_data_4ep):
        """Wave 1 stop line expansion must still collect future_eps."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        stop_line = block["stop_line"]
        future_ep_nums = [fe["ep"] for fe in stop_line.get("future_eps", [])]
        assert 3 in future_ep_nums
        assert 4 in future_ep_nums

    def test_w1_compile_to_prompt_blanket_prohibition(self, compiler, arc_data_4ep):
        """Wave 1 blanket prohibition in compile_to_prompt must still work."""
        block = compiler.compile(arc_data_4ep, ep_num=1)
        prompt = compiler.compile_to_prompt(block)
        assert "모든 에피소드 사건" in prompt
        assert "REJECT" in prompt
