"""[TF-45] genre_schema_builder 단위 테스트."""

import pytest

from modules.core.genre_schema_builder import (
    build_actual_truth_schema,
    build_manager_genre_instructions,
    build_npc_hud_schema,
    build_state_constraints_schema,
    build_state_updates_schema,
    build_status_shadow_schema,
    get_genre_label,
    get_genre_role_title,
    is_wuxia,
)

# ── is_wuxia ────────────────────────────────────────────────────────────────


class TestIsWuxia:
    def test_wuxia_string(self):
        assert is_wuxia("wuxia") is True

    def test_wuxia_korean(self):
        assert is_wuxia("무협") is True

    def test_empty_string_defaults_to_wuxia(self):
        assert is_wuxia("") is True

    @pytest.mark.parametrize(
        "genre",
        ["hunter", "investment", "composer", "cooking", "alt_history", "actor", "sports", "medical", "fantasy"],
    )
    def test_non_wuxia(self, genre):
        assert is_wuxia(genre) is False


# ── get_genre_label ─────────────────────────────────────────────────────────


class TestGetGenreLabel:
    def test_wuxia_label(self):
        assert get_genre_label("wuxia") == "무협"

    def test_investment_label(self):
        assert get_genre_label("investment") == "투자"

    def test_actor_label(self):
        assert get_genre_label("actor") == "배우"

    def test_unknown_genre_returns_raw(self):
        assert get_genre_label("romance") == "romance"


# ── build_actual_truth_schema ───────────────────────────────────────────────


class TestBuildActualTruthSchema:
    def test_wuxia_returns_empty(self):
        assert build_actual_truth_schema("wuxia", ["realm"]) == ""

    def test_investment_has_capital(self):
        schema = build_actual_truth_schema("investment", ["capital", "total_assets"])
        assert '"capital"' in schema
        assert '"total_assets"' in schema
        assert "내공" not in schema
        assert "martial" not in schema

    def test_hunter_has_mana(self):
        schema = build_actual_truth_schema("hunter", ["awakening_rank", "mana"])
        assert '"mana"' in schema
        assert '"awakening_rank"' in schema

    def test_always_includes_common_fields(self):
        schema = build_actual_truth_schema("actor", ["acting_skill"])
        assert '"equipment"' in schema
        assert '"wealth"' in schema

    def test_empty_keys_still_has_common(self):
        schema = build_actual_truth_schema("sports", [])
        assert '"equipment"' in schema


# ── build_state_updates_schema ──────────────────────────────────────────────


class TestBuildStateUpdatesSchema:
    def test_wuxia_has_internal_energy(self):
        schema = build_state_updates_schema("wuxia", [])
        assert "internal_energy" in schema
        assert "martial_arts" in schema

    def test_investment_no_internal_energy(self):
        schema = build_state_updates_schema("investment", ["capital", "total_assets"])
        assert "internal_energy" not in schema
        assert "martial_arts" not in schema
        assert '"capital"' in schema

    def test_medical_has_surgery_count(self):
        schema = build_state_updates_schema("medical", ["doctor_rank", "surgery_count"])
        assert '"surgery_count"' in schema
        assert "내공" not in schema


# ── build_state_constraints_schema ──────────────────────────────────────────


class TestBuildStateConstraintsSchema:
    def test_wuxia_returns_internal_energy(self):
        result = build_state_constraints_schema("wuxia", [])
        assert "internal_energy" in result
        assert "내공" in result

    def test_investment_returns_capital(self):
        result = build_state_constraints_schema("investment", ["capital", "total_assets"])
        assert '"capital"' in result
        assert "내공" not in result

    def test_no_numeric_keys_returns_status(self):
        result = build_state_constraints_schema("cooking", ["chef_rank", "signature_dish"])
        assert '"status"' in result


# ── build_status_shadow_schema ──────────────────────────────────────────────


class TestBuildStatusShadowSchema:
    def test_wuxia_has_internal_energy_loss(self):
        schema = build_status_shadow_schema("wuxia", [])
        assert "internal_energy_loss" in schema

    def test_investment_no_internal_energy_loss(self):
        schema = build_status_shadow_schema("investment", ["capital"])
        assert "internal_energy_loss" not in schema
        assert "key_stat_change" in schema

    def test_actor_genre_label_in_schema(self):
        schema = build_status_shadow_schema("actor", ["acting_skill"])
        assert "배우" in schema


# ── build_npc_hud_schema ────────────────────────────────────────────────────


class TestBuildNpcHudSchema:
    def test_wuxia_returns_empty(self):
        assert build_npc_hud_schema("wuxia") == ""

    def test_hunter_has_npc_hud(self):
        schema = build_npc_hud_schema("hunter")
        assert "NPC_헌터_HUD" in schema
        assert '"rank"' in schema

    def test_investment_has_npc_hud(self):
        schema = build_npc_hud_schema("investment")
        assert "NPC_투자_HUD" in schema

    def test_unknown_genre_has_fallback(self):
        schema = build_npc_hud_schema("romance")
        assert "NPC_romance_HUD" in schema


# ── build_manager_genre_instructions ────────────────────────────────────────


class TestBuildManagerGenreInstructions:
    def test_wuxia_returns_empty(self):
        assert build_manager_genre_instructions("wuxia", []) == ""

    def test_investment_instructions(self):
        instructions = build_manager_genre_instructions("investment", ["capital", "total_assets"])
        assert "투자 핵심 지표" in instructions
        assert "capital" in instructions
        assert "internal_energy" in instructions  # 금지 명시
        assert "절대 생성하지 마라" in instructions

    def test_sports_instructions(self):
        instructions = build_manager_genre_instructions("sports", ["athlete_tier", "ranking"])
        assert "스포츠 핵심 지표" in instructions
        assert "athlete_tier" in instructions


# ── get_genre_role_title ────────────────────────────────────────────────────


class TestGetGenreRoleTitle:
    def test_wuxia_role_title(self):
        assert get_genre_role_title("wuxia") == "무협 대서사 전략가"

    def test_investment_role_title(self):
        assert get_genre_role_title("investment") == "투자 대서사 전략가"

    def test_actor_role_title(self):
        assert get_genre_role_title("actor") == "배우 대서사 전략가"


# ── Manager genre branch ────────────────────────────────────────────────────


class TestManagerGenreBranch:
    """Manager.update_state_and_lore_v20 — 장르 분기 테스트 (LLM 미호출)."""

    def test_wuxia_uses_original_prompt(self):
        """무협 경로 — UPDATE_STATE_PROMPT_V25 상수 사용 확인."""
        from modules.domain.agents.manager import UPDATE_STATE_PROMPT_V25, is_wuxia

        assert is_wuxia("wuxia")
        assert "무림 15대 지표" in UPDATE_STATE_PROMPT_V25
        assert "internal_energy" in UPDATE_STATE_PROMPT_V25

    def test_non_wuxia_prompt_generation(self):
        """비무협 경로 — _build_genre_manager_prompt 호출 확인."""
        from modules.domain.agents.manager import _build_genre_manager_prompt

        prompt = _build_genre_manager_prompt(
            genre="investment",
            critical_keys=["capital", "total_assets"],
            ep_num=1,
            manuscript="테스트 원고",
            current_state_json="{}",
            lore_list_json="[]",
            active_seeds_json="[]",
            causal_history="없음",
        )
        assert "투자 핵심 지표" in prompt
        assert "capital" in prompt
        assert "무림 15대 지표" not in prompt


# ── StateTextVerifier genre-aware ───────────────────────────────────────────


class TestStateTextVerifierGenre:
    def test_default_genre_is_wuxia(self):
        from modules.core.state_text_verifier import StateTextVerifier

        v = StateTextVerifier()
        assert v._genre == "wuxia"

    def test_genre_filter_includes_critical_keys(self):
        from modules.core.state_text_verifier import StateTextVerifier

        v = StateTextVerifier(genre="investment", critical_keys=["capital", "total_assets"])
        result = v._filter_verifiable_fields_genre({"capital": "100억", "internal_energy": 50, "foo": "bar"})
        assert "capital" in result
        assert "internal_energy" in result  # still numeric (int)
        assert "foo" not in result  # non-numeric string without digits

    def test_static_method_still_works(self):
        from modules.core.state_text_verifier import StateTextVerifier

        result = StateTextVerifier._filter_verifiable_fields({"capital": "100억", "unknown": "abc"})
        assert "capital" in result


# ── ConstraintDB genre-aware ────────────────────────────────────────────────


class TestConstraintDBGenre:
    def test_default_genre_is_wuxia(self):
        from modules.core.constraint_db import ConstraintDB

        db = ConstraintDB()
        assert db._genre == "wuxia"

    def test_investment_genre_skips_internal_energy(self):
        from modules.core.constraint_db import ConstraintDB

        db = ConstraintDB(genre="investment")
        # Parse arc with internal_energy — should set 0 for non-wuxia
        db._parse_arc_state(
            {
                "arc_no": 1,
                "state_constraints": {
                    "arc_end_state": {"internal_energy": 80, "location": "서울"},
                },
            }
        )
        assert db.arc_states[1].internal_energy == 0

    def test_wuxia_parses_internal_energy(self):
        from modules.core.constraint_db import ConstraintDB

        db = ConstraintDB(genre="wuxia")
        db._parse_arc_state(
            {
                "arc_no": 1,
                "state_constraints": {
                    "arc_end_state": {"internal_energy": 80, "location": "화산"},
                },
            }
        )
        assert db.arc_states[1].internal_energy == 80

    def test_constraint_block_no_internal_energy_for_investment(self):
        from modules.core.constraint_db import ConstraintDB

        db = ConstraintDB(genre="investment")
        db._parse_arc_state(
            {
                "arc_no": 1,
                "state_constraints": {"arc_end_state": {"location": "서울"}},
            }
        )
        block = db.generate_constraint_block(for_arc=2)
        assert "내공" not in block


# ── StateTracker genre-aware ────────────────────────────────────────────────


class TestStateTrackerGenre:
    def test_wuxia_fallback_has_internal_energy(self):
        from modules.domain.agents.state_tracker import StateTracker

        tracker = StateTracker(genre="wuxia")
        assert "internal_energy" in tracker.tracking_fields

    def test_investment_fallback_no_internal_energy(self):
        from modules.domain.agents.state_tracker import StateTracker

        tracker = StateTracker(genre="investment")
        assert "internal_energy" not in tracker.tracking_fields

    def test_default_genre_is_wuxia(self):
        from modules.domain.agents.state_tracker import StateTracker

        tracker = StateTracker()
        assert tracker._genre == "wuxia"
        assert "internal_energy" in tracker.tracking_fields
