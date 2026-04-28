from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock

import pytest

from modules.core.constants import GenreTypes
from modules.core.prompt_loader import PromptLoader
from modules.core.response_schemas import BLUEPRINT_SCHEMA
from modules.core.tactical_intrusion_contract import detect_tactical_intrusion_signature
from modules.domain.agents.base_agent import AgentErrorType
from modules.domain.agents.blueprint_ensemble import BlueprintEnsembleGenerator, build_genre_strategy_contract


def _make_agent(root: Path | None = None):
    ctx = SimpleNamespace()
    ctx.author_directives = ""
    ctx.db = MagicMock()
    ctx.db.load_anchor.return_value = {}
    current_project = SimpleNamespace(name="Lane Project")
    if root is not None:
        current_project.paths = SimpleNamespace(root=root)
    ctx.current_project = current_project
    ctx.project_name = "Lane Project"
    return BlueprintEnsembleGenerator(ctx, MagicMock())


def test_generate_ensemble_owner_shell_coordinates_helper_chain():
    agent = _make_agent()
    prepared = {
        "arc_focus": "focus",
        "genre": GenreTypes.INVESTMENT,
        "constraints_str": "constraints",
        "tactical_excerpt": "tactical",
        "prev_info": "prev",
        "hud_context": "hud",
        "cache_name": "cache/bp",
        "constraint_block": {},
        "archive_appendix_meta": {"enabled": False, "raw_chars": 0, "consumed_chars": 0, "dropped_chars": 0},
    }
    active_strategies = [{"name": "action_focused"}]
    raw_candidates = [{"scene_breakdown": [1, 2, 3, 4], "integrated_scenario": "x" * 600}]
    qualified_candidates = [
        {
            "_strategy": "action_focused",
            "_scene_count": 4,
            "_length": 600,
            "scene_breakdown": [1, 2, 3, 4],
            "integrated_scenario": "x" * 600,
        }
    ]
    finalized = ({"best": True}, [{"best": True}])

    agent._prepare_blueprint_ensemble_context = MagicMock(return_value=prepared)
    agent._select_blueprint_ensemble_strategies = MagicMock(return_value=active_strategies)
    agent._run_blueprint_ensemble_workers = MagicMock(return_value=(raw_candidates, [AgentErrorType.TIMEOUT]))
    agent._qualify_blueprint_candidates = MagicMock(return_value=(qualified_candidates, []))
    agent._finalize_blueprint_candidates = MagicMock(return_value=finalized)

    result = agent.generate_ensemble(
        ep_num=9,
        arc_data={},
        constraint_block={},
        prev_blueprint={"end_location": "VIP 룸"},
        single_strategy="action_focused",
        fix_pack={"must_fix": ["keep continuity"]},
        repair_contract={"repair_scope": "full"},
        attempt_num=3,
    )

    assert result == finalized
    assert agent.last_error_types == [AgentErrorType.TIMEOUT]
    assert agent.last_error_type == AgentErrorType.TIMEOUT
    agent._prepare_blueprint_ensemble_context.assert_called_once()
    agent._select_blueprint_ensemble_strategies.assert_called_once_with("action_focused")
    agent._run_blueprint_ensemble_workers.assert_called_once()
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["cache_name"] == "cache/bp"
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["prev_blueprint"] == {"end_location": "VIP 룸"}
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["fix_pack"] == {"must_fix": ["keep continuity"]}
    assert agent._run_blueprint_ensemble_workers.call_args.kwargs["repair_contract"] == {"repair_scope": "full"}
    agent._qualify_blueprint_candidates.assert_called_once_with(raw_candidates)
    agent._finalize_blueprint_candidates.assert_called_once_with(
        qualified_candidates,
        [],
        ep_num=9,
        arc_data={},
        attempt_num=3,
        prompt_envelope_meta=ANY,
    )
    envelope_meta = agent._finalize_blueprint_candidates.call_args.kwargs["prompt_envelope_meta"]
    assert envelope_meta["genre_strategy_contracts"][0]["contract_id"] == "investment_business_power.action_focused.v1"
    assert envelope_meta["genre_strategy_contracts"][0]["authority_level"] == "route"
    assert envelope_meta["genre_strategy_contracts"][0]["contract_hash"]


def test_compress_retry_feedback_rewrites_meta_recap_markers_before_prompt_injection():
    feedback = "이전 화 훅을 이어받고 이번 화 시작부에 직전 화 설명을 반복하지 말 것."

    compressed = BlueprintEnsembleGenerator._compress_retry_feedback(feedback)

    assert "이전 화" not in compressed
    assert "이번 화" not in compressed
    assert "직전 화" not in compressed
    assert "이전 사건 훅" in compressed
    assert "현재 장면 시작부" in compressed
    assert "직전 장면 설명" in compressed


def test_qualify_blueprint_candidates_tracks_pass_and_fail_metadata():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "action_focused",
                "scene_breakdown": [
                    {"summary": "주인공이 회의실 문을 열고 들어간다.", "key_events": ["회의실 문을 열고 들어간다."]},
                    {"summary": "PB가 투자 리스크를 경고한다.", "key_events": ["PB가 투자 리스크를 경고한다."]},
                    {"summary": "주인공이 매수 결정을 밀어붙인다.", "key_events": ["매수 결정을 밀어붙인다."]},
                    {"summary": "시세가 요동치며 끝난다.", "key_events": ["시세가 요동친다."]},
                ],
                "integrated_scenario": "x" * 900,
                "opening_transition": {"type": "direct_continuation"},
                "protagonist_state": {"mood": "긴장"},
            },
            {
                "_strategy": "dialogue_focused",
                "scene_breakdown": [
                    {"summary": "주인공이 PB를 만난다.", "key_events": ["PB를 만난다."]},
                    {"summary": "PB가 경고를 건넨다.", "key_events": ["경고를 건넨다."]},
                    {"summary": "주인공이 고민한다.", "key_events": ["매수 여부를 고민한다."]},
                ],
                "integrated_scenario": "x" * 320,
                "opening_transition": {"type": "direct_continuation"},
                "protagonist_state": {"mood": "긴장"},
            },
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 4
    assert qualified[0]["_length"] == 900
    assert disqualified == [("dialogue_focused", 3, 320)]
    assert agent.last_disqualified_candidates == [
        {
            "strategy": "dialogue_focused",
            "scene_count": 3,
            "integrated_len": 320,
            "contract_reason": "",
        }
    ]


def test_run_blueprint_ensemble_workers_tracks_screening_disqualified_strategies():
    agent = _make_agent()
    agent._generate_single = MagicMock(
        side_effect=[
            (None, AgentErrorType.CANDIDATE_DISQUALIFIED),
            (None, AgentErrorType.CANDIDATE_DISQUALIFIED),
        ]
    )

    candidates, worker_error_types = agent._run_blueprint_ensemble_workers(
        ep_num=2,
        active_strategies=[
            {"name": "action_focused"},
            {"name": "dialogue_focused"},
        ],
        arc_focus="focus",
        constraints_str="constraints",
        tactical_excerpt="tactical",
        prev_info="prev",
        feedback="",
        strategy_specific_feedback="",
        rejected_strategy="",
        protagonist_name="한시우",
        protagonist_config={"pov": "혼합"},
        hud_context="hud",
        genre=GenreTypes.WUXIA,
        cache_name="cache/bp",
        prev_blueprint=None,
        constraint_block={},
        fix_pack=None,
        repair_contract=None,
    )

    assert candidates == []
    assert worker_error_types == [
        AgentErrorType.CANDIDATE_DISQUALIFIED,
        AgentErrorType.CANDIDATE_DISQUALIFIED,
    ]
    assert agent.last_disqualified_candidates == [
        {
            "strategy": "action_focused",
            "scene_count": 0,
            "integrated_len": 0,
            "contract_reason": "screening_disqualified",
            "ordinal": 0,
        },
        {
            "strategy": "dialogue_focused",
            "scene_count": 0,
            "integrated_len": 0,
            "contract_reason": "screening_disqualified",
            "ordinal": 1,
        },
    ]


def test_qualify_blueprint_candidates_accepts_dense_three_scene_blueprint():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "dense_three_scene",
                "scene_breakdown": {
                    "scene_1": {
                        "goal": "The protagonist forces the first buy order through the VIP room desk.",
                        "key_events": ["The protagonist forces the buy order through despite the PB objection."],
                    },
                    "scene_2": {
                        "summary": "Leverage warnings and collateral pressure hit the desk at the same time.",
                        "key_events": [
                            "The desk flashes a leverage warning.",
                            "Collateral pressure arrives from the broker.",
                        ],
                    },
                    "scene_3": {
                        "goal": "The trade settles at the closing bell and leaves the next crisis hanging.",
                        "key_events": ["The trade settles at the closing bell."],
                    },
                },
                "integrated_scenario": ("The trade desk keeps escalating as pressure piles on. " * 30),
                "opening_transition": {"type": "explicit_transition"},
                "protagonist_state": {"mood": "focused"},
            }
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 3
    assert qualified[0]["_length"] == len("The trade desk keeps escalating as pressure piles on. " * 30)
    assert disqualified == []


def test_qualify_blueprint_candidates_accepts_dense_two_scene_blueprint():
    agent = _make_agent()

    qualified, disqualified = agent._qualify_blueprint_candidates(
        [
            {
                "_strategy": "dense_two_scene",
                "scene_breakdown": {
                    "scene_1": {
                        "goal": "The protagonist hits the first buy button inside the PB center.",
                        "key_events": ["The protagonist hits the first buy button."],
                    },
                    "scene_2": {
                        "summary": "Leverage warnings and collateral pressure crash in together.",
                        "key_events": [
                            "A leverage warning crashes onto the desk.",
                            "Collateral pressure starts immediately.",
                        ],
                    },
                },
                "integrated_scenario": ("The protagonist keeps pushing through the market pressure. " * 30),
                "opening_transition": {"type": "explicit_transition"},
                "protagonist_state": {"mood": "focused"},
            }
        ]
    )

    assert len(qualified) == 1
    assert qualified[0]["_qualified"] is True
    assert qualified[0]["_scene_count"] == 2
    assert qualified[0]["_length"] == len("The protagonist keeps pushing through the market pressure. " * 30)
    assert disqualified == []


def test_finalize_blueprint_candidates_attaches_meta_and_cleans_temp_fields():
    agent = _make_agent()
    qualified_candidates = [
        {
            "_strategy": "emotion_focused",
            "_qualified": True,
            "_scene_count": 4,
            "_length": 700,
            "scene_breakdown": [{"scene": 1}],
            "integrated_scenario": "x" * 700,
        }
    ]
    disqualified = [("action_focused", 2, 120)]

    best, all_candidates = agent._finalize_blueprint_candidates(
        qualified_candidates,
        disqualified,
        ep_num=1,
        arc_data={},
    )

    assert best is all_candidates[0]
    meta = all_candidates[0]["_ensemble_meta"]
    assert meta["candidate_index"] == 0
    assert meta["strategy"] == "emotion_focused"
    assert meta["scene_count"] == 4
    assert meta["length"] == 700
    assert meta["disqualified"] == disqualified
    assert "_strategy" not in all_candidates[0]
    assert "_qualified" not in all_candidates[0]
    assert "_scene_count" not in all_candidates[0]
    assert "_length" not in all_candidates[0]


def test_finalize_blueprint_candidates_carries_prompt_envelope_meta():
    agent = _make_agent()
    qualified_candidates = [
        {
            "_strategy": "emotion_focused",
            "_qualified": True,
            "_scene_count": 4,
            "_length": 700,
            "scene_breakdown": [{"scene": 1}],
            "integrated_scenario": "x" * 700,
        }
    ]

    best, all_candidates = agent._finalize_blueprint_candidates(
        qualified_candidates,
        [],
        ep_num=1,
        arc_data={},
        prompt_envelope_meta={
            "total_chars": 4321,
            "budget_ledger": {"budget_bucket": "stage3.prompt_envelope_total_chars"},
        },
    )

    assert best is all_candidates[0]
    assert all_candidates[0]["_ensemble_meta"]["prompt_envelope"]["total_chars"] == 4321


def test_finalize_blueprint_candidates_snapshots_fanout_candidates_when_attempt_num_present(tmp_path):
    agent = _make_agent(tmp_path)
    qualified_candidates = [
        {
            "_strategy": "emotion_focused",
            "_qualified": True,
            "_scene_count": 4,
            "_length": 700,
            "scene_breakdown": {"scene_1": {"summary": "opening"}},
            "integrated_scenario": "x" * 700,
        }
    ]

    _, all_candidates = agent._finalize_blueprint_candidates(
        qualified_candidates,
        [],
        ep_num=9,
        arc_data={"arc_no": 2},
        attempt_num=4,
    )

    artifact_path = all_candidates[0]["_candidate_artifact_meta"]["artifact_path"]
    assert artifact_path.endswith("candidate_blueprint__emotion_focused.json")
    assert (tmp_path / artifact_path).exists()


def test_finalize_blueprint_candidates_preserves_genre_strategy_contract_meta():
    agent = _make_agent()
    contract = build_genre_strategy_contract(GenreTypes.INVESTMENT, "action_focused")

    _, all_candidates = agent._finalize_blueprint_candidates(
        [
            {
                "_strategy": "action_focused",
                "_qualified": True,
                "_scene_count": 4,
                "_length": 700,
                "_genre_strategy_contract": contract,
                "scene_breakdown": {"scene_1": {"summary": "opening"}},
                "integrated_scenario": "x" * 700,
            }
        ],
        [],
        ep_num=9,
        arc_data={"arc_no": 2},
        attempt_num=None,
    )

    meta = all_candidates[0]["_ensemble_meta"]
    assert meta["genre_strategy_contract"]["contract_id"] == "investment_business_power.action_focused.v1"
    assert meta["genre_strategy_contract"]["authority_level"] == "route"
    assert "_genre_strategy_contract" not in all_candidates[0]
    assert "_strategy" not in all_candidates[0]


def test_build_blueprint_prompt_bundle_uses_cache_stub_and_full_fallback():
    agent = _make_agent()

    def _load_side_effect(_file, _key, **kwargs):
        return (
            f"arc={kwargs['arc_focus']}|constraints={kwargs['constraints']}|"
            f"prev={kwargs['prev_info']}|hud={kwargs['hud_context']}"
        )

    agent._prompt_loader = MagicMock()
    agent._prompt_loader.load.side_effect = _load_side_effect

    prompt, fallback, contract = agent._build_blueprint_prompt_bundle(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={"display": "action", "directive": "directive"},
        protagonist_name="hero",
        protagonist_instructions="do the thing",
        extra_directive="",
        hud_context="HUD_PAYLOAD",
        pov_constraint="POV_CONSTRAINT",
        reader_feedback="",
        cache_name="cache/bp",
    )

    assert contract == {}
    assert "[context cached: refer to cached_content]" in prompt
    assert "ARC_FOCUS_PAYLOAD" not in prompt
    assert "CONSTRAINTS_PAYLOAD" not in prompt
    assert "PREV_INFO_PAYLOAD" not in prompt
    assert "HUD_PAYLOAD" not in prompt
    assert "ARC_FOCUS_PAYLOAD" in fallback
    assert "CONSTRAINTS_PAYLOAD" in fallback
    assert "PREV_INFO_PAYLOAD" in fallback
    assert "HUD_PAYLOAD" in fallback


def test_investment_action_focused_prompt_uses_business_power_semantics():
    agent = _make_agent()

    prompt, fallback, contract = agent._build_blueprint_prompt_bundle(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={
            "name": "action_focused",
            "display": "액션 중심",
            "directive": "전투, 추격, 대결 씬\n물리적 위기/액션 클리프행어",
        },
        protagonist_name="hero",
        protagonist_instructions="do the thing",
        extra_directive="",
        hud_context="HUD_PAYLOAD",
        pov_constraint="POV_CONSTRAINT",
        reader_feedback="",
        cache_name="",
        genre=GenreTypes.INVESTMENT,
    )

    assert contract["contract_id"] == "investment_business_power.action_focused.v1"
    assert contract["authority_level"] == "route"
    assert contract["contract_hash"] in prompt
    assert contract["factsheet_mutation"] is False
    assert contract["material_mutation"] is False
    for expected in ("business execution pressure", "capital exposure", "governance/legal gate"):
        assert expected in prompt
    for forbidden in ("전투", "추격", "물리적 위기", "액션 클리프행어"):
        assert forbidden not in prompt
    assert fallback == prompt


def test_cached_investment_action_focused_prompt_and_fallback_keep_contract():
    agent = _make_agent()

    prompt, fallback, contract = agent._build_blueprint_prompt_bundle(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={
            "name": "action_focused",
            "display": "액션 중심",
            "directive": "전투, 추격, 대결 씬\n물리적 위기/액션 클리프행어",
        },
        protagonist_name="hero",
        protagonist_instructions="do the thing",
        extra_directive="",
        hud_context="HUD_PAYLOAD",
        pov_constraint="POV_CONSTRAINT",
        reader_feedback="",
        cache_name="cache/bp",
        genre=GenreTypes.INVESTMENT,
    )

    for rendered in (prompt, fallback):
        assert "investment_business_power.action_focused.v1" in rendered
        assert contract["contract_hash"] in rendered
        assert "business execution pressure" in rendered
        assert "전투, 추격, 대결 씬" not in rendered
        assert "물리적 위기/액션 클리프행어" not in rendered
    assert "[context cached: refer to cached_content]" in prompt
    assert "ARC_FOCUS_PAYLOAD" in fallback


def test_build_genre_strategy_contract_keeps_verdict_authority_out_of_python():
    contract = build_genre_strategy_contract(GenreTypes.INVESTMENT, "action_focused")

    assert contract["authority_level"] == "route"
    assert contract["authority_source"] == "stage3_genre_strategy_contract"
    assert contract["director_visible"] is True
    assert contract["contract_hash"]
    assert contract["authority_level"] != "verdict"


def test_request_blueprint_generation_preserves_genre_strategy_contract_hash():
    agent = _make_agent()
    contract = build_genre_strategy_contract(GenreTypes.INVESTMENT, "action_focused")
    agent._ask_with_cached_context = MagicMock(
        return_value='{"scene_breakdown": {"scene_1": {"summary": "투자 위원회 압박"}}, "integrated_scenario": "scenario"}'
    )
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": {"scene_1": {"summary": "투자 위원회 압박"}},
            "integrated_scenario": "scenario",
        }
    )
    agent._sanitize_blueprint_candidate = MagicMock(
        return_value={
            "scene_breakdown": {"scene_1": {"summary": "투자 위원회 압박"}},
            "integrated_scenario": "scenario",
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.INVESTMENT,
        genre_strategy_contract=contract,
    )

    assert result["_genre_strategy_contract"]["contract_hash"] == contract["contract_hash"]


def test_prepare_blueprint_ensemble_context_caches_constraints_before_arc_focus():
    agent = _make_agent()
    captured = {}

    def _capture_cache(**kwargs):
        captured["content"] = kwargs["content"]
        return {"cache_name": "cache/bp"}

    agent._resolve_blueprint_arc_focus = MagicMock(return_value="ARC_FOCUS_PAYLOAD")
    agent._resolve_blueprint_ensemble_genre = MagicMock(return_value=GenreTypes.WUXIA)
    agent._format_constraints = MagicMock(return_value="CONSTRAINTS_PAYLOAD")
    agent._format_prev_info_expanded = MagicMock(return_value="PREV_INFO_PAYLOAD")
    agent._build_hud_context = MagicMock(return_value="HUD_PAYLOAD")
    agent._get_or_create_context_cache = MagicMock(side_effect=_capture_cache)

    result = agent._prepare_blueprint_ensemble_context(
        ep_num=11,
        arc_data={},
        constraint_block={},
        prev_blueprint=None,
        prev_blueprints=None,
        prev_manuscripts_text="",
        state_tracker=None,
    )

    shared_context = captured["content"]
    assert shared_context.index("CONSTRAINTS_PAYLOAD") < shared_context.index("ARC_FOCUS_PAYLOAD")
    assert result["cache_name"] == "cache/bp"


def test_build_blueprint_prompt_bundle_places_constraints_before_arc_mission():
    agent = _make_agent()

    prompt, fallback, contract = agent._build_blueprint_prompt_bundle(
        ep_num=11,
        arc_focus="ARC_FOCUS_PAYLOAD",
        constraints_str="CONSTRAINTS_PAYLOAD",
        prev_info="PREV_INFO_PAYLOAD",
        strategy={"display": "action", "directive": "directive"},
        protagonist_name="hero",
        protagonist_instructions="do the thing",
        extra_directive="",
        hud_context="HUD_PAYLOAD",
        pov_constraint="POV_CONSTRAINT",
        reader_feedback="",
        cache_name="",
    )

    assert contract == {}
    assert prompt.index("### [Constraint Stack / 제약 조건]") < prompt.index("### [Arc Mission / 이번 화 핵심]")
    assert prompt.index("### [Previous Truth And Archive]") < prompt.index("### [HUD Convenience State]")
    assert fallback == prompt


def test_request_blueprint_generation_rejects_missing_required_fields():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value='{"scene_breakdown": []}')
    agent._extract_json_robust = MagicMock(return_value={"scene_breakdown": []})

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert result == (None, AgentErrorType.SCHEMA_INCOMPATIBLE)


def test_request_blueprint_generation_retries_without_schema_on_numeric_overflow():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(
        side_effect=[
            RuntimeError("Exceeds the limit (4300 digits) for integer string conversion: value has 4853 digits"),
            "{}",
        ]
    )
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 회의실 문을 연다.", "key_events": ["회의실 문을 연다."]},
                "scene_2": {"summary": "PB가 압박 전화를 건다.", "key_events": ["PB가 압박 전화를 건다."]},
            },
            "integrated_scenario": "주인공이 회의실 문을 열고 PB의 압박 전화를 받는다. " * 40,
            "opening_transition": {"type": "direct_continuation"},
            "protagonist_state": {"mood": "냉정"},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert agent._ask_with_cached_context.call_count == 2
    assert agent._ask_with_cached_context.call_args_list[0].kwargs["response_schema"] == BLUEPRINT_SCHEMA
    assert agent._ask_with_cached_context.call_args_list[1].kwargs["response_schema"] is None


def test_request_blueprint_generation_reraises_non_numeric_schema_error():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(side_effect=RuntimeError("cached boom"))

    with pytest.raises(RuntimeError, match="cached boom"):
        agent._request_blueprint_generation(
            cache_name="cache/bp",
            prompt="PROMPT",
            full_prompt_fallback="FALLBACK",
            strategy_name="action_focused",
            genre=GenreTypes.WUXIA,
        )


def test_sanitize_blueprint_candidate_normalizes_declared_opening_transition_alias():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 문을 열고 PB의 표정을 읽는다.", "key_events": ["PB의 눈빛이 굳는다."]},
                "scene_2": {"summary": "주인공이 매수 타이밍을 확정한다.", "key_events": ["매수 버튼을 누른다."]},
            },
            "integrated_scenario": "주인공이 문을 열고 들어가 PB의 경고를 읽은 뒤 바로 매수 결정을 밀어붙인다. " * 40,
            "opening_transition": {"type": "transition", "summary": "scene cut into the trading floor"},
            "protagonist_state": {"mood": "집중"},
        },
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert result["opening_transition"]["type"] == "explicit_transition"
    assert result["opening_transition"]["summary"] == "scene cut into the trading floor"


def test_request_blueprint_generation_uses_prev_blueprint_to_infer_direct_opening_transition():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "start_location": "VIP 룸",
            "time_flow": "직후",
            "scene_breakdown": {
                "scene_1": {
                    "location": "VIP 룸",
                    "summary": "주인공이 VIP 룸 문을 열고 PB와 마주한다.",
                    "key_events": ["VIP 룸에 도착한다."],
                },
                "scene_2": {
                    "summary": "PB가 경고를 던지고 주인공은 매수 버튼을 누를 타이밍을 잰다.",
                    "key_events": ["PB의 경고를 무시한다."],
                },
            },
            "integrated_scenario": "주인공이 VIP 룸 직후 장면을 이어받아 PB의 경고를 넘기고 매수 타이밍을 재본다. "
            * 40,
            "protagonist_state": {"mood": "긴장"},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        prev_blueprint={"end_location": "VIP 룸", "time_flow": "같은 날 밤"},
    )

    assert isinstance(result, dict)
    assert result["opening_transition"]["type"] == "direct_continuation"


def test_request_blueprint_generation_infers_jump_opening_without_prev_blueprint():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 신경전을 벌인다.", "key_events": ["PB와 대치한다."]},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "protagonist_state": {"mood": "긴장"},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert result["opening_transition"]["type"] == "jump_opening"


def test_request_blueprint_generation_rejects_empty_protagonist_state_contract():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 신경전을 벌인다.", "key_events": ["PB와 대치한다."]},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {},
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_blueprint_contract_admission_reason_rejects_generic_scene_shells():
    agent = _make_agent()

    reason = agent._blueprint_contract_admission_reason(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "setup", "key_events": ["progress"]},
                "scene_2": {"summary": "climax", "key_events": ["ending"]},
            },
            "integrated_scenario": "Trader moves through the episode." * 40,
            "opening_transition": {"type": "direct_continuation"},
            "protagonist_state": {"mood": "focused"},
        }
    )

    assert reason == "scene_completeness:2"


def test_blueprint_contract_admission_reason_rejects_placeholder_protagonist_state():
    agent = _make_agent()

    reason = agent._blueprint_contract_admission_reason(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 대치한다.", "key_events": ["PB와 대치한다."]},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {"mood": "상태 유지", "objective": "변화"},
        }
    )

    assert reason == "missing_protagonist_state"


def test_blueprint_contract_admission_reason_rejects_scene_completeness_gap():
    agent = _make_agent()

    reason = agent._blueprint_contract_admission_reason(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 택시 문을 열고 내린다.", "key_events": ["택시에서 내린다."]},
                "scene_2": {"summary": "VIP룸 앞에서 PB와 대치한다.", "key_events": []},
            },
            "integrated_scenario": "주인공은 택시에서 내려 VIP룸으로 향한다. " * 40,
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {"mood": "긴장"},
        }
    )

    assert reason == "scene_completeness:1"


def test_sanitize_blueprint_candidate_rejects_unauthorized_tactical_intrusion():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {"summary": "주인공이 VIP룸 문을 열자 괴한이 난입한다.", "key_events": ["괴한이 난입한다."]},
                "scene_2": {"summary": "괴한이 멱살을 잡고 협박한다.", "key_events": ["멱살을 잡고 협박한다."]},
            },
            "integrated_scenario": "주인공이 VIP룸 문을 여는 순간 괴한이 난입하고 멱살을 잡아 협박한다. " * 40,
            "opening_transition": {"type": "jump_opening"},
            "protagonist_state": {"mood": "경계"},
        },
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="주인공은 PB와 대치하며 매수 여부를 결정한다.",
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_tactical_intrusion_contract_detects_unauthorized_vehicle_chase_signature():
    signature = detect_tactical_intrusion_signature(
        "백미러에 끈질기게 따라붙는 검은 세단이 보이고, 헤드라이트를 켠 차량이 정면으로 돌진한다."
    )

    assert "검은 세단" in signature["entry_hits"]
    assert any(marker in signature["conflict_hits"] for marker in ("돌진", "정면으로", "헤드라이트"))


def test_sanitize_blueprint_candidate_rejects_unauthorized_vehicle_chase_intrusion():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {
                    "summary": "백미러에 검은 세단이 따라붙고 한시우가 도주를 시작한다.",
                    "key_events": ["검은 세단이 미행하고 헤드라이트를 켠 차량이 정면으로 돌진한다."],
                    "goal": "미행 차량을 따돌린다.",
                },
                "scene_2": {
                    "summary": "급브레이크를 밟아 정면 충돌을 피한다.",
                    "key_events": ["타이어가 비명을 지르고 스티어링을 꺾는다."],
                    "goal": "충돌 위기에서 벗어난다.",
                },
            },
            "integrated_scenario": (
                "한시우는 도로 위에서 검은 세단의 미행을 확인하고, 헤드라이트를 켠 차량이 정면으로 "
                "돌진하자 급브레이크를 밟는다. " * 30
            ),
            "opening_transition": {"type": "explicit_transition"},
            "protagonist_state": {"mood": "경계"},
        },
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="한시우가 VIP룸에서 박성호에게 해외 데스크 브리핑 메모를 받는다.",
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_sanitize_blueprint_candidate_allows_vehicle_threat_when_tactical_authorizes_it():
    agent = _make_agent()
    candidate = {
        "scene_breakdown": {
            "scene_1": {
                "summary": "백미러에 검은 세단이 따라붙고 한시우가 도주를 시작한다.",
                "key_events": ["검은 세단이 미행하고 헤드라이트를 켠 차량이 정면으로 돌진한다."],
                "goal": "미행 차량을 따돌린다.",
            },
            "scene_2": {
                "summary": "급브레이크를 밟아 정면 충돌을 피한다.",
                "key_events": ["타이어가 비명을 지르고 스티어링을 꺾는다."],
                "goal": "충돌 위기에서 벗어난다.",
            },
        },
        "integrated_scenario": (
            "한시우는 도로 위에서 검은 세단의 미행을 확인하고, 헤드라이트를 켠 차량이 정면으로 "
            "돌진하자 급브레이크를 밟는다. " * 30
        ),
        "opening_transition": {"type": "explicit_transition"},
        "protagonist_state": {"mood": "경계"},
    }

    result = agent._sanitize_blueprint_candidate(
        candidate,
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="검은 세단의 미행과 도로 추격전, 헤드라이트 차량 돌진 위기를 처리한다.",
    )

    assert result is candidate


def test_sanitize_blueprint_candidate_rejects_korean_synonym_tactical_intrusion():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {
                    "summary": "VIP룸 문이 열리자 리스크 관리팀이 들이닥쳐 한시우의 팔목을 비틀려 든다.",
                    "key_events": ["리스크 관리팀이 들이닥쳐 팔목을 비틀려 한다."],
                },
                "scene_2": {
                    "summary": "팀장이 주먹을 들이밀며 입막음을 강요한다.",
                    "key_events": ["주먹을 들이밀며 입막음을 강요한다."],
                },
            },
            "integrated_scenario": (
                "리스크 관리팀이 VIP룸에 들이닥쳐 한시우의 팔목을 비틀고 주먹을 들이밀며 입막음을 강요한다. " * 30
            ),
            "opening_transition": {"type": "direct_continuation"},
            "protagonist_state": {"mood": "냉정"},
        },
        strategy_name="dialogue_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="한시우가 박성호 PB와 수수료 조건을 조정하며 WTI 주문 여부를 확정한다.",
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_sanitize_blueprint_candidate_rejects_character_only_tactical_intrusion():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {
                    "summary": "주인공이 VIP룸 문을 연다.",
                    "key_events": ["VIP룸 입장"],
                    "characters": ["주인공", "괴한"],
                },
                "scene_2": {
                    "summary": "상대가 팔목을 비틀며 협박한다.",
                    "key_events": ["팔목을 비틀며 협박한다."],
                    "characters": ["주인공"],
                },
            },
            "integrated_scenario": "주인공이 VIP룸으로 들어간다. 상대가 팔목을 비틀며 협박한다. " * 40,
            "opening_transition": {"type": "jump_opening"},
            "protagonist_state": {"mood": "경계"},
        },
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="주인공은 PB와 대치하며 매수 여부를 결정한다.",
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_sanitize_blueprint_candidate_allows_pb_negotiation_with_staff_words_only():
    agent = _make_agent()

    result = agent._sanitize_blueprint_candidate(
        {
            "scene_breakdown": {
                "scene_1": {
                    "summary": "박성호가 직원에게 대응표와 주문 확인서를 가져오게 한다.",
                    "key_events": ["직원이 대응표를 펼치고 주문 확인서를 건넨다."],
                },
                "scene_2": {
                    "summary": "한시우와 박성호가 수수료 조건과 체결 순서를 조율한다.",
                    "key_events": ["수수료 조건을 조율한다.", "체결 순서를 확인한다."],
                },
            },
            "integrated_scenario": (
                "박성호가 직원을 불러 대응표와 주문 확인서를 준비시키고, 한시우와 체결 순서를 차분히 맞춰 나간다. " * 30
            ),
            "opening_transition": {"type": "direct_continuation"},
            "protagonist_state": {"mood": "냉정"},
        },
        strategy_name="dialogue_focused",
        genre=GenreTypes.WUXIA,
        tactical_excerpt="한시우가 박성호 PB와 수수료 조건을 조정하며 WTI 주문 여부를 확정한다.",
    )

    assert isinstance(result, dict)


def test_request_blueprint_generation_rejects_contaminated_integrated_scenario():
    agent = _make_agent()
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(
        return_value={
            "scene_breakdown": [],
            "integrated_scenario": "직전 화의 HUD 상태창을 확인했다.",
        }
    )

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_request_blueprint_generation_sanitizes_contaminated_key_events():
    agent = _make_agent()
    candidate = {
        "scene_breakdown": {
            "scene_1": {
                "summary": "주인공이 문을 열고 적과 마주친다.",
                "key_events": [
                    "문을 열고 적과 마주친다.",
                    "HUD 상태창 점검",
                ],
            },
            "scene_2": {
                "summary": "주인공이 적의 칼끝을 피하고 뒤로 물러선다.",
                "key_events": ["칼끝을 피한다."],
            },
        },
        "integrated_scenario": "주인공은 문을 열고 적과 마주친다. " * 40,
        "opening_transition": {"type": "direct_continuation"},
        "protagonist_state": {"mood": "경계"},
    }
    agent._ask_with_cached_context = MagicMock(return_value="{}")
    agent._extract_json_robust = MagicMock(return_value=candidate)

    result = agent._request_blueprint_generation(
        cache_name="cache/bp",
        prompt="PROMPT",
        full_prompt_fallback="FALLBACK",
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
    )

    assert isinstance(result, dict)
    assert result["scene_breakdown"]["scene_1"]["key_events"] == ["문을 열고 적과 마주친다."]


def test_generate_single_compacts_retry_feedback_before_prompt_injection():
    agent = _make_agent()
    captured = {}

    def _capture_prompt_bundle(**kwargs):
        captured["extra_directive"] = kwargs["extra_directive"]
        return "PROMPT", "FALLBACK"

    agent._build_blueprint_prompt_bundle = MagicMock(side_effect=_capture_prompt_bundle)
    agent._request_blueprint_generation = MagicMock(return_value={"ok": True})

    result = agent._generate_single(
        ep_num=9,
        arc_focus="focus",
        constraints_str="constraints",
        tactical_excerpt="tactical",
        prev_info="prev",
        strategy={"name": "action_focused"},
        feedback=(
            "[작품 추적 슬롯 요약]\nnoise to drop\n"
            "[Binding prevalidation]\n"
            "- [CRITICAL/episode_progression] replayed scene family\n"
            "- [MAJOR/temporal_deictic] relative date drift\n"
            "[StyleGuide 문체/anti-AI 참고]\nignore me\n"
        ),
        strategy_feedback="Keep the episode on the fresh forward motion axis.",
        protagonist_name="주인공",
        protagonist_config={},
        hud_context="",
        genre=GenreTypes.WUXIA,
        cache_name="cache/bp",
    )

    assert result == {"ok": True}
    extra_directive = captured["extra_directive"]
    assert "episode_progression" in extra_directive
    assert "temporal_deictic" in extra_directive
    assert "Keep the episode on the fresh forward motion axis." in extra_directive
    assert "[작품 추적 슬롯 요약]" not in extra_directive
    assert "StyleGuide 문체/anti-AI 참고" not in extra_directive


def test_sanitize_blueprint_candidate_rejects_episode_progression_replay_before_validator_spend():
    agent = _make_agent()
    candidate = {
        "opening_transition": {"type": "direct_continuation"},
        "protagonist_state": {"mood": "집중"},
        "integrated_scenario": "A" * 900,
        "scene_breakdown": {
            "scene_1": {
                "title": "다시 서재",
                "goal": "아버지와 또 맞선다.",
                "summary": "서재에서 아버지와 다시 대치한다.",
                "characters": ["한시우", "한정호"],
                "key_events": ["서재에서 아버지와 다시 대치한다."],
                "location": "성북동 본가, 서재",
            },
            "scene_2": {
                "title": "다시 방",
                "goal": "전화를 다시 돌린다.",
                "summary": "자기 방에서 다시 전화를 돌린다.",
                "characters": ["한시우"],
                "key_events": ["방에서 휴대폰으로 다시 전화를 건다."],
                "location": "성북동 본가, 한시우의 방",
            },
        },
    }

    result = agent._sanitize_blueprint_candidate(
        candidate,
        strategy_name="action_focused",
        genre=GenreTypes.WUXIA,
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {"location": "한정호 회장의 서재", "characters": ["한시우", "한정호"]},
                "scene_4": {"location": "한시우의 방", "characters": ["한시우"]},
            }
        },
        constraint_block={
            "must_focus": {"content": "광화문 로펌에서 법인 설립을 의뢰하고, PB센터에서 자산 현금화를 요청한다."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_2",
                        "label": "독립 선언",
                        "location": "한정호 회장의 서재",
                        "location_variants": ["한정호 회장의 서재", "서재"],
                        "characters": ["한시우", "한정호"],
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "전장의 서막",
                        "location": "한시우의 방",
                        "location_variants": ["한시우의 방", "성북동 본가", "방"],
                        "characters": ["한시우"],
                    },
                ]
            },
        },
    )

    assert result == (None, AgentErrorType.CANDIDATE_DISQUALIFIED)


def test_sanitize_blueprint_candidate_allows_forward_must_focus_in_same_household_low_overlap():
    agent = _make_agent()
    candidate = {
        "opening_transition": {"type": "jump_opening"},
        "protagonist_state": {"mood": "결연"},
        "integrated_scenario": "거실에서 서재로 이동해 독립 투자 사업을 선언한다. " * 40,
        "scene_breakdown": {
            "scene_1": {
                "title": "서재 요청",
                "goal": "한시우가 아버지 한정호에게 서재 대화를 요청한다.",
                "summary": "거실에서 TV를 끈 한시우가 한정호에게 서재에서 따로 이야기하자고 말한다.",
                "characters": ["한시우", "한정호"],
                "key_events": ["한시우가 한정호에게 서재 면담을 요청한다."],
                "location": "성북동 본가, 거실",
            },
            "scene_2": {
                "title": "독립 선언",
                "goal": "아버지 앞에서 독립 투자 법인 설립을 선언한다.",
                "summary": "한정호의 서재에서 한시우가 그룹 승계 포기와 독립 투자 사업을 선언한다.",
                "characters": ["한시우", "한정호", "한태준", "한태민"],
                "key_events": ["독립 투자 사업 선언이 서재에서 이뤄진다."],
                "location": "성북동 본가, 한정호의 서재",
            },
        },
    }

    result = agent._sanitize_blueprint_candidate(
        candidate,
        strategy_name="dialogue_focused",
        genre=GenreTypes.INVESTMENT,
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {"location": "성북동 본가, 한시우의 방", "characters": ["한시우"]},
                "scene_3": {
                    "location": "성북동 본가, 다이닝 룸",
                    "characters": ["한시우", "한정호", "한태준", "한태민"],
                },
                "scene_4": {"location": "성북동 본가, 거실", "characters": ["한시우"]},
            }
        },
        constraint_block={
            "must_focus": {
                "content": (
                    "아버지 한정호의 서재에서 독립을 선언; "
                    "가족의 반대와 무시 속에서 투자 사업 계획을 발표; "
                    "형들과의 후계 구도에서 완전히 벗어남"
                )
            },
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_2",
                        "label": "한시우의 방",
                        "location": "성북동 본가, 한시우의 방",
                        "location_variants": ["성북동 본가, 한시우의 방", "한시우의 방", "성북동 본가"],
                        "characters": ["한시우"],
                    },
                    {
                        "scene_key": "scene_3",
                        "label": "가족 식사",
                        "location": "성북동 본가, 다이닝 룸",
                        "location_variants": ["성북동 본가, 다이닝 룸", "다이닝 룸", "성북동 본가"],
                        "characters": ["한시우", "한정호", "한태준", "한태민"],
                    },
                    {
                        "scene_key": "scene_4",
                        "label": "거실 뉴스",
                        "location": "성북동 본가, 거실",
                        "location_variants": ["성북동 본가, 거실", "거실", "성북동 본가"],
                        "characters": ["한시우"],
                    },
                ]
            },
        },
    )

    assert result == candidate


def test_sanitize_blueprint_candidate_allows_progressive_opening_bridge():
    agent = _make_agent()
    candidate = {
        "opening_transition": {"type": "direct_continuation", "signals": ["same_location_anchor"]},
        "protagonist_state": {"mood": "집중"},
        "integrated_scenario": "A" * 900,
        "scene_breakdown": {
            "scene_1": {
                "title": "서재로 향하는 걸음",
                "goal": "아버지 한정호의 서재로 향하며 독립 투자 회사 선언을 준비한다.",
                "summary": "가사도우미의 안내를 받은 한시우가 거실에서 일어나 복도를 지나 서재로 향한다.",
                "characters": ["한시우"],
                "key_events": [
                    "한시우가 거실 소파에서 일어나 서재가 있는 복도를 향해 걷기 시작한다.",
                    "한시우는 투자 회사를 차리겠다는 말을 머릿속에서 정리한다.",
                ],
                "location": "2006년 성북동 본가, 거실에서 서재로 가는 복도",
            },
            "scene_2": {
                "title": "독립 선언",
                "goal": "아버지 한정호에게 그룹이 아닌 독립 투자 회사 설립 의사를 밝힌다.",
                "summary": "한시우가 서재에서 한정호와 마주해 투자 회사를 차리겠다고 선언한다.",
                "characters": ["한시우", "한정호"],
                "key_events": ["한시우가 독립 투자 회사 설립 의사를 밝힌다."],
                "location": "성북동 본가, 한정호의 서재",
            },
        },
    }

    result = agent._sanitize_blueprint_candidate(
        candidate,
        strategy_name="action_focused",
        genre=GenreTypes.INVESTMENT,
        prev_blueprint={
            "scene_breakdown": {
                "scene_2": {"location": "2006년 성북동 본가, 한시우의 방", "characters": ["한시우"]},
                "scene_3": {"location": "2006년 성북동 본가, 거실", "characters": ["한시우"]},
                "scene_4": {"location": "2006년 성북동 본가, 거실", "characters": ["한시우", "가사도우미"]},
            }
        },
        constraint_block={
            "must_focus": {"content": "아버지 한정호의 서재에 불려가 독립 투자 회사 설립 의사를 밝힌다."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_4",
                        "label": "아버지의 부름",
                        "location": "2006년 성북동 본가, 거실",
                        "location_variants": ["2006년 성북동 본가, 거실", "거실"],
                        "characters": ["한시우", "가사도우미"],
                    }
                ],
                "completed_prior_events": [
                    {
                        "location": "2006년 성북동 본가, 거실",
                        "events": ["TV를 보던 한시우에게 가사도우미가 다가와 회장님께서 찾는다고 말한다."],
                    }
                ],
            },
        },
    )

    assert result == candidate


def test_sanitize_blueprint_candidate_allows_explicit_progressive_opening_shift():
    agent = _make_agent()
    candidate = {
        "opening_transition": {"type": "explicit_transition", "signals": ["location_shift"]},
        "protagonist_state": {"mood": "집중"},
        "integrated_scenario": "A" * 900,
        "start_location": "서울 성북동 본가 저택, 아버지의 서재 앞 복도",
        "scene_breakdown": {
            "scene_1": {
                "title": "서재 앞",
                "goal": "아버지 한정호의 서재로 이동해 독립 투자 법인 선언을 준비한다.",
                "summary": "한시우가 집사의 안내로 자신의 방 앞 복도를 벗어나 아버지의 서재 앞에 도착한다.",
                "characters": ["한시우"],
                "key_events": [
                    "한시우가 집사의 안내를 받으며 아버지의 서재 앞 복도에 선다.",
                    "한시우는 투자 법인 설립 선언을 차분히 정리한다.",
                ],
                "location": "서울 성북동 본가 저택, 아버지의 서재 앞 복도",
            },
            "scene_2": {
                "title": "선언",
                "goal": "아버지 한정호에게 그룹 경영 불참과 독립 투자 법인 설립 의사를 밝힌다.",
                "summary": "한시우가 서재 안에서 독립 투자 법인을 세우겠다고 선언한다.",
                "characters": ["한시우", "한정호"],
                "key_events": ["한시우가 독립 투자 법인 설립 의사를 밝힌다."],
                "location": "서울 성북동 본가 저택, 한정호의 서재",
            },
        },
    }

    result = agent._sanitize_blueprint_candidate(
        candidate,
        strategy_name="action_focused",
        genre=GenreTypes.INVESTMENT,
        prev_blueprint={
            "scene_breakdown": {
                "scene_4": {"location": "서울 성북동 본가 저택, 자신의 방 앞 복도", "characters": ["한시우"]},
            }
        },
        constraint_block={
            "must_focus": {"content": "아버지 한정호의 서재에 불려가 독립 투자 법인 설립 의사를 밝힌다."},
            "episode_progression_packet": {
                "blocked_scene_families": [
                    {
                        "scene_key": "scene_4",
                        "label": "아버지 호출",
                        "location": "서울 성북동 본가 저택, 자신의 방 앞 복도",
                        "location_variants": ["서울 성북동 본가 저택, 자신의 방 앞 복도", "복도"],
                        "characters": ["한시우"],
                    }
                ],
                "completed_prior_events": [
                    {
                        "location": "서울 성북동 본가 저택, 자신의 방 앞 복도",
                        "events": ["한시우가 집사에게 회장님이 찾는다는 말을 듣는다."],
                    }
                ],
            },
        },
    )

    assert result == candidate


def test_format_constraints_surfaces_episode_progression_guardrails_for_producer_prompt():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "ep_num": 9,
            "must_focus": {
                "arc_title": "포지션 진입",
                "key_events": ["수수료 두 배 제안으로 박성호 설득 성공", "WTI 원유 6월물 15억 포지션 진입 완료"],
            },
            "episode_progression_packet": {
                "time_truths": ["현재 Arc 시간축은 2006년 2월(겨울 축)이다."],
                "blocked_scene_families": [
                    {
                        "label": "PB의 맹렬한 반대",
                        "location": "한미증권 청담동 지점 15층 VIP룸",
                        "characters": ["한시우", "박성호"],
                        "type": "tension_build",
                    }
                ],
                "completed_prior_events": [
                    {
                        "location": "한미증권 청담동 지점 15층 VIP룸",
                        "events": ["박성호가 WTI 포지션 진입 승인을 이미 내렸다."],
                    }
                ],
                "next_gate_strength_mode": {
                    "mode": "foreshadow_only",
                    "introduced_target_families": ["gold"],
                    "reserved_target_families": ["oil"],
                    "reason": "금 handoff는 foreshadow 수준으로만 남기고 유가 압박을 먼저 마감한다.",
                },
                "lawful_repetition_window": {
                    "mode": "allow_escalated_repeat",
                    "allow_same_location_if_goal_changes": True,
                    "allow_same_counterparty_if_goal_changes": True,
                    "allow_same_channel_if_decision_escalates": True,
                },
                "surface_guidance": [
                    "시작 anchor 계승은 짧게 처리하고 이번 화의 주 장면은 직전 대치의 결과 이후 단계로 이동하라.",
                    "직전 화와 같은 2인 대치를 주 장면으로 반복하지 말고 보조 인물이나 기관 결정 라인을 열어라.",
                ],
                "future_beat_reservations": [
                    "제10화 reserved beat anchor: 포지션 진입 직후 카페로 이동해 차트를 모니터링한다.",
                    "장소 이동, 시장 모니터링, 후속 뉴스 반응 같은 후속 surface는 다음 화 reserved beat이므로 이번 화 엔딩에서는 예고 수준만 남겨라.",
                ],
            },
        },
        genre=GenreTypes.HUNTER,
    )

    assert "[Episode Progression - 직전 화 replay 금지]" in formatted
    assert "PB의 맹렬한 반대" in formatted
    assert "한미증권 청담동 지점 15층 VIP룸" in formatted
    assert "MUST_FOCUS의 새 사건 축으로 전진" in formatted
    assert "같은 축 반복 방지용 진행 surface 가이드" in formatted
    assert "기관 결정 라인" in formatted
    assert "새 타깃 handoff는 foreshadow 수준으로만 남기고" in formatted
    assert "lawful repetition으로 전진 가능" in formatted
    assert "다음 화 reserved beat 선소비 금지" in formatted
    assert "카페로 이동해 차트를 모니터링" in formatted
    assert "이미 완료된 사건을 scene_1/live objective로 다시 재연하지 말 것" in formatted
    assert "WTI 포지션 진입 승인을 이미 내렸다" in formatted


def test_format_constraints_surfaces_episode_state_packet_authority_and_dropped_conflicts():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "episode_state_packet": {
                "opening_truth": {
                    "location": "한미증권 청담동 지점 15층 VIP룸",
                    "location_source": "prev_blueprint.scene_breakdown.last.location",
                    "time_context": "[manuscript ending]\n그는 VIP룸 문을 나서며 다음 협상 수를 계산했다.",
                    "time_source": "prev_manuscript_ending",
                },
                "protagonist_truth": {
                    "equipment": ["가죽 서류가방", "CME 계좌 증빙"],
                    "injuries": "없음",
                    "sources": {
                        "equipment": "prev_blueprint.protagonist_state.equipment",
                        "injuries": "prev_blueprint.protagonist_state.injuries",
                    },
                },
                "dropped_conflicts": [
                    {
                        "field": "opening.location",
                        "reason": "mid_arc_arc_start_location_override_blocked",
                        "dropped_value": "본가 개인 서재",
                    }
                ],
                "rewrite_required_reasons": ["mid_arc_arc_start_location_override_blocked"],
            },
            "continuity": {"location": "한미증권 청담동 지점 15층 VIP룸"},
            "inherited_state": {"equipment": ["가죽 서류가방"], "injuries": "없음"},
        },
        genre=GenreTypes.HUNTER,
    )

    assert "[EpisodeStatePacket - authoritative pre-generation carryover]" in formatted
    assert "단일 carryover truth surface" in formatted
    assert "opening.location: 한미증권 청담동 지점 15층 VIP룸" in formatted
    assert "JSON start_location and scene_breakdown.scene_1.location must equal opening.location exactly" in formatted
    assert "prev_blueprint.scene_breakdown.last.location" in formatted
    assert "mid_arc_arc_start_location_override_blocked" in formatted


def test_format_constraints_does_not_hard_bind_placeholder_opening_location():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "episode_state_packet": {
                "opening_truth": {
                    "location": "서사 시작점",
                    "location_source": "arc_opening_sentinel",
                },
            },
        },
        genre=GenreTypes.INVESTMENT,
    )

    assert "opening.location: 서사 시작점" in formatted
    assert "must equal opening.location exactly" not in formatted


def test_format_constraints_does_not_hard_bind_arc_start_opening_location():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "episode_state_packet": {
                "opening_truth": {
                    "location": "2006년 서울 성북동 본가",
                    "location_source": "arc_data.state_constraints.arc_start_state.location",
                },
            },
        },
        genre=GenreTypes.INVESTMENT,
    )

    assert "opening.location: 2006년 서울 성북동 본가" in formatted
    assert "must equal opening.location exactly" not in formatted


def test_hard_bound_opening_location_normalizes_terminal_room_variant():
    candidate = {
        "start_location": "서울 성북동 본가, 한시우의 방",
        "scene_breakdown": {
            "scene_1": {
                "location": "서울 성북동 본가, 한시우의 방",
            }
        },
    }

    normalized = BlueprintEnsembleGenerator._normalize_hard_bound_opening_location(
        candidate,
        constraint_block={
            "episode_state_packet": {
                "opening_truth": {
                    "location": "서울 성북동 본가, 2층 복도 및 한시우의 방",
                    "location_source": "prev_blueprint.scene_breakdown.last.location",
                }
            }
        },
    )

    assert normalized == "start_location, scene_1.location"
    assert candidate["start_location"] == "서울 성북동 본가, 2층 복도 및 한시우의 방"
    assert candidate["scene_breakdown"]["scene_1"]["location"] == "서울 성북동 본가, 2층 복도 및 한시우의 방"


def test_hard_bound_opening_location_does_not_mask_unrelated_location():
    candidate = {
        "start_location": "서울 강남구 S&Y 그룹 본사",
        "scene_breakdown": {
            "scene_1": {
                "location": "서울 강남구 S&Y 그룹 본사",
            }
        },
    }

    normalized = BlueprintEnsembleGenerator._normalize_hard_bound_opening_location(
        candidate,
        constraint_block={
            "episode_state_packet": {
                "opening_truth": {
                    "location": "서울 성북동 본가, 2층 복도 및 한시우의 방",
                    "location_source": "prev_blueprint.scene_breakdown.last.location",
                }
            }
        },
    )

    assert normalized == ""
    assert candidate["start_location"] == "서울 강남구 S&Y 그룹 본사"
    assert candidate["scene_breakdown"]["scene_1"]["location"] == "서울 강남구 S&Y 그룹 본사"


def test_hard_bound_opening_location_does_not_mask_parent_only_location():
    candidate = {
        "start_location": "서울 성북동 본가",
        "scene_breakdown": {
            "scene_1": {
                "location": "서울 성북동 본가",
            }
        },
    }

    normalized = BlueprintEnsembleGenerator._normalize_hard_bound_opening_location(
        candidate,
        constraint_block={
            "episode_state_packet": {
                "opening_truth": {
                    "location": "서울 성북동 본가, 2층 복도 및 한시우의 방",
                    "location_source": "prev_blueprint.scene_breakdown.last.location",
                }
            }
        },
    )

    assert normalized == ""
    assert candidate["start_location"] == "서울 성북동 본가"
    assert candidate["scene_breakdown"]["scene_1"]["location"] == "서울 성북동 본가"


def test_format_constraints_surfaces_opening_transition_expectation():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "episode_state_packet": {
                "opening_truth": {
                    "location": "Packet Hall",
                    "location_source": "state_constraints.arc_end_state.location",
                    "opening_transition_expectation": (
                        "Use explicit_transition; never declare direct_continuation when the opening anchor moved."
                    ),
                }
            }
        },
        genre=GenreTypes.HUNTER,
    )

    assert "opening.transition_expectation" in formatted
    assert "direct_continuation" in formatted
    assert "explicit_transition" in formatted


def test_format_constraints_surfaces_opening_active_characters_for_direct_carryover():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "episode_state_packet": {
                "opening_truth": {
                    "location": "Packet Hall",
                    "active_characters": ["Lead", "PB"],
                    "opening_transition_expectation": (
                        "same-room carryover; direct_continuation is allowed if the active cast remains on stage."
                    ),
                }
            }
        },
        genre=GenreTypes.HUNTER,
    )

    assert "opening.active_characters" in formatted
    assert "Lead, PB" in formatted
    assert "재입장 동선" in formatted


def test_format_constraints_surfaces_terminal_timeline_lock_for_producer_prompt():
    agent = _make_agent()

    formatted = agent._format_constraints(
        {
            "terminal_timeline_lock": {
                "mode": "exact_terminal_match",
                "expression": "2006년 1월 15일 - 법인 설립 및 20억 자금 확보 완료",
                "timeline": {
                    "year": 2006,
                    "month": 1,
                    "day": 15,
                    "description": "법인 설립 및 20억 자금 확보 완료",
                },
            }
        },
        genre=GenreTypes.HUNTER,
    )

    assert "TERMINAL TIMELINE LOCK" in formatted
    assert "HARD CONSTRAINT" in formatted
    assert "2006년 1월 15일 - 법인 설립 및 20억 자금 확보 완료" in formatted
    assert "ending_state.timeline" in formatted


def test_select_generate_error_type_prefers_candidate_disqualified_over_schema_bundle():
    assert (
        BlueprintEnsembleGenerator._select_generate_error_type(
            [
                AgentErrorType.TIMEOUT,
                AgentErrorType.SCHEMA_INCOMPATIBLE,
                AgentErrorType.CANDIDATE_DISQUALIFIED,
            ]
        )
        == AgentErrorType.CANDIDATE_DISQUALIFIED
    )


class TestBlueprintTemporalCarryover:
    """[pre-rerun] Blueprint 시간 진실 소스가 원고 기준으로 전달되는지 검증."""

    def test_format_prev_info_expanded_includes_manuscript_ending_truth(self):
        """prev_manuscripts_text가 있으면 '원고 기준 종료 상황' 섹션이 포함."""
        agent = _make_agent()
        prev_bp = {
            "ending_hook": "적의 습격",
            "end_location": "객잔",
            "time_flow": "2006-01-17 저녁",
            "ending_state": {"timeline": {"expression": "2006-01-17 Evening"}},
        }
        manuscript_text = "주인공은 저녁 8시에 아버지를 만났다. [2006년 1월 18일, 저녁]"

        result = agent._format_prev_info_expanded(prev_bp, None, manuscript_text)

        assert "원고 기준" in result
        assert "2006년 1월 18일" in result

    def test_format_prev_info_expanded_promotes_recent_carryover_orders_from_archive(self):
        agent = _make_agent()
        prev_bp = {"ending_hook": "late call", "end_location": "office"}
        manuscript_text = (
            "━━━ 제9화 원고 ━━━\n"
            "한시우는 박성호를 내려다보며 말했다. 금. 골드. 관련된 선물 상품과 국제 금 시장 변동성까지 모두 정리해라. "
            "내일 아침 장이 열리기 전까지 보고서로 만들어.\n\n"
            "━━━ 제10화 원고 ━━━\n"
            "강남 오피스에 도착한 한시우는 창밖을 보며 다음 수를 계산했다.\n"
        )

        result = agent._format_prev_info_expanded(prev_bp, None, manuscript_text)

        assert "[Context Tier 3A - Recent Carryover Orders / Pending Actions]" in result
        assert "제9화 carryover order (금)" in result
        assert "새 지시처럼 반복하지 말 것" in result

    def test_format_prev_info_expanded_without_manuscript_omits_truth_section(self):
        """prev_manuscripts_text가 없으면 원고 기준 섹션 없음."""
        agent = _make_agent()
        prev_bp = {"time_flow": "2006-01-17 저녁"}

        result = agent._format_prev_info_expanded(prev_bp, None, "")

        assert "원고 기준" not in result

    def test_format_prev_info_expanded_demotes_stale_prev_time_when_opening_truth_conflicts(self):
        agent = _make_agent()
        prev_bp = {
            "time_flow": "2006년 4월 중순 자정 무렵",
            "ending_state": {
                "timeline": {"표현": "2006년 4월 중순 새벽"},
                "protagonist_status": "5억 원의 현금 수익을 확정하고 다음 움직임을 주시함",
            },
        }

        result = agent._format_prev_info_expanded(
            prev_bp,
            None,
            "",
            authoritative_time_context="2006년 5월",
        )

        assert "현재 화 opening time truth: 2006년 5월" in result
        assert "direct-prev 권위에서 제외" in result
        assert "시간 흐름: 2006년 4월 중순 자정 무렵" not in result
        assert "종료 시점: 표현:2006년 4월 중순 새벽" not in result
        assert "주인공 상태: 5억 원의 현금 수익을 확정하고 다음 움직임을 주시함" in result

    def test_format_prev_info_expanded_replaces_raw_scenario_with_structured_carryover(self):
        agent = _make_agent()
        prev_bp = {"time_flow": "2006-01-17 저녁"}
        previous_blueprints = [
            {
                "ep_num": 3,
                "title": "도약",
                "integrated_scenario": "상태창이 떠오르고 직전 화를 요약하는 장문 시나리오",
                "start_location": "객잔",
                "end_location": "산문 앞",
                "time_flow": "저녁 → 심야",
                "core_tension": "추적자 접근",
                "ending_hook": "문이 열렸다",
                "scene_breakdown": {
                    "scene_1": {
                        "title": "추적",
                        "location": "골목",
                        "summary": "주인공이 골목을 가로지른다.",
                        "characters": ["주인공", "추적자"],
                        "key_events": ["추적자를 따돌린다."],
                    }
                },
            }
        ]

        result = agent._format_prev_info_expanded(prev_bp, previous_blueprints, "")

        assert "상태창이 떠오르고 직전 화를 요약하는 장문 시나리오" not in result
        assert "[시작위치] 객잔" in result
        assert "[종료위치] 산문 앞" in result
        assert "[scene_1] 추적" in result
        assert "추적자를 따돌린다." in result

    def test_constraint_compiler_prefers_manuscript_ending(self):
        """원고 말미가 있으면 time_context에 원고 기준 정보가 포함."""
        from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler

        compiler = BlueprintConstraintCompiler()
        prev_bp = {"time_flow": "2006-01-17 저녁", "ending_hook": "습격"}
        continuity = compiler._extract_continuity(prev_bp, prev_manuscript_ending="저녁 8시, 1월 18일의 밤하늘")

        assert "원고 기준" in continuity["time_context"]
        assert "1월 18일" in continuity["time_context"]

    def test_constraint_compiler_falls_back_to_blueprint_without_manuscript(self):
        """원고 말미 없으면 blueprint time_flow 사용."""
        from modules.domain.agents.blueprint_constraint_compiler import BlueprintConstraintCompiler

        compiler = BlueprintConstraintCompiler()
        prev_bp = {"time_flow": "2006-01-17 저녁", "ending_hook": "습격"}
        continuity = compiler._extract_continuity(prev_bp)

        assert continuity["time_context"] == "2006-01-17 저녁"

    def test_format_prev_info_expanded_marks_truth_tiers(self):
        agent = _make_agent()
        prev_bp = {"ending_hook": "late call", "end_location": "office"}
        previous_blueprints = [{"ep_num": 1, "title": "pilot", "scene_breakdown": {}}]

        result = agent._format_prev_info_expanded(prev_bp, previous_blueprints, "manuscript ending")

        assert "[Context Tier 1 - Direct Previous Episode Truth]" in result
        assert "[Context Tier 2 - Structured Previous Blueprint Carryover]" in result
        assert "[Context Tier 3 - Manuscript Ending Truth]" in result
        assert "[Context Tier 4 - Archive Appendix / lower priority than Tier 1-3]" in result

    def test_prepare_blueprint_ensemble_context_demotes_archive_appendix_by_default(self):
        agent = _make_agent()
        agent._get_or_create_context_cache = MagicMock(return_value={"cache_name": "cache/bp"})
        agent._build_hud_context = MagicMock(return_value="")
        prev_manuscripts_text = ("원고 " * 60000) + "MS-TAIL"

        context_bundle = agent._prepare_blueprint_ensemble_context(
            ep_num=7,
            arc_data={},
            constraint_block={},
            prev_blueprint={"ep_num": 6, "title": "prev"},
            prev_blueprints=[{"ep_num": 6, "title": "prev", "scene_breakdown": {}}],
            prev_manuscripts_text=prev_manuscripts_text,
            state_tracker=None,
        )

        archive_meta = context_bundle["archive_appendix_meta"]
        assert archive_meta["enabled"] is True
        assert archive_meta["demoted"] is True
        assert archive_meta["raw_chars"] > archive_meta["consumed_chars"]
        assert "MS-TAIL" in context_bundle["prev_info"]


def test_blueprint_generation_prompt_contains_stage3_anti_contamination_contract():
    prompt = PromptLoader().load("ensemble", "BLUEPRINT_GENERATION_PROMPT")

    assert prompt is not None
    assert "Stage3 장면 권위 계약" in prompt
    assert "안티 HUD / 안티 시스템 UI" in prompt
    assert "안티 크로스 장르 오염" in prompt
    assert "scene_breakdown.key_events" in prompt
    assert '"opening_transition"' in prompt
    assert '"episode_number"' in prompt
    assert "장면 완성도 계약" in prompt
    assert "전술 권위 계약" in prompt


# ===========================================================================
# Tranche 1 (2026-04-14): Opening-Transition Vocabulary Coherence
# ===========================================================================


def test_tranche1_blueprint_generation_prompt_carries_opening_transition_decision_table():
    """Tranche 1 sub-edit 1.2: ensemble.yaml에 opening_transition decision table이 들어가
    LLM이 enum 이름만 보지 않고 실제 결정 규칙을 학습할 수 있어야 한다."""
    prompt = PromptLoader().load("ensemble", "BLUEPRINT_GENERATION_PROMPT")
    assert prompt is not None
    assert "opening_transition.type 결정 규칙" in prompt
    assert "direct_continuation" in prompt
    assert "explicit_transition" in prompt
    assert "jump_opening" in prompt
    assert "stage_cross_stage_contract.apply_opening_transition_contract" in prompt


def test_tranche1_extract_episode_tactical_default_behavior_unchanged():
    """Tranche 1 sub-edit 1.3: prefer_full_doc default False이면 13개 다른 호출자에
    영향이 없어야 한다 (episode_details 우선, 없으면 regex slice, 없으면 fallback)."""
    from modules.core.tactical_utils import extract_episode_tactical

    # episode_details 있으면 그것을 반환 (default mode)
    result = extract_episode_tactical(
        "[제1화 prologue]\nfirst content\n[제2화 next]",
        1,
        episode_details=[{"ep_num": 1, "details": ["bullet a", "bullet b"]}],
    )
    assert result == "- bullet a\n- bullet b"

    # episode_details 없으면 regex slice 반환
    result2 = extract_episode_tactical(
        "[제1화 prologue]\nfirst content\n[제2화 next]",
        1,
    )
    assert result2 == "first content"

    # 둘 다 없으면 fallback_full=True이면 전체 문자열
    result3 = extract_episode_tactical("raw doc", 99)
    assert result3 == "raw doc"

    # fallback_full=False이면 빈 문자열
    result4 = extract_episode_tactical("raw doc", 99, fallback_full=False)
    assert result4 == ""


def test_tranche1_extract_episode_tactical_prefer_full_doc_concatenates_under_budget():
    """Tranche 1 sub-edit 1.3: prefer_full_doc=True (Stage3 producer 전용) 모드는
    bullet TL;DR과 per-ep prose를 함께 결합하고 budget으로 잘라야 한다."""
    from modules.core.tactical_utils import extract_episode_tactical

    tactical_doc = "[제1화 prologue]\nA detailed prose body about ep1 events.\n[제2화 next]\nlater\n"
    episode_details = [
        {"ep_num": 1, "details": ["concrete entity X", "arithmetic anchor Y"]},
    ]

    result = extract_episode_tactical(
        tactical_doc,
        1,
        episode_details=episode_details,
        prefer_full_doc=True,
    )
    # TL;DR과 prose가 모두 포함되어야 한다
    assert "[TL;DR — episode_details]" in result
    assert "concrete entity X" in result
    assert "arithmetic anchor Y" in result
    assert "[Tactical doc — 제1화]" in result
    assert "A detailed prose body about ep1 events." in result

    # budget 내에서 잘려야 한다
    long_tactical = "[제1화 X]\n" + ("a" * 5000) + "\n[제2화 Y]\n"
    result_truncated = extract_episode_tactical(
        long_tactical,
        1,
        episode_details=episode_details,
        prefer_full_doc=True,
        full_doc_budget_chars=500,
    )
    assert len(result_truncated) <= 600  # budget + truncation marker overhead
    assert "[truncated]" in result_truncated


def test_tranche1_normalize_opening_transition_returns_missing_on_pure_omission():
    """Tranche 1 sub-edit 1.4: LLM이 opening_transition을 선언하지 않았고
    prev_blueprint/scene 단서도 없으면 'missing'을 반환해 cheap admission이 fail-closed."""
    candidate = {
        # opening_transition 누락
        "scene_breakdown": {},
        # start_location/time_flow/scene_text 모두 부재
    }
    route = BlueprintEnsembleGenerator._normalize_opening_transition_contract(
        candidate,
        prev_blueprint=None,
    )
    assert route == "missing"


def test_tranche1_normalize_opening_transition_returns_inferred_when_continuity_anchor_exists():
    """Tranche 1 sub-edit 1.4: LLM이 선언하지 않았지만 prev_blueprint/scene 단서가
    있으면 'inferred'를 반환하고 candidate를 mutate해야 한다."""
    candidate = {
        "start_location": "한미증권 본사",
        "time_flow": "오전",
        "scene_breakdown": {
            "scene_1": {"location": "한미증권 본사", "summary": "회의 시작"},
        },
    }
    route = BlueprintEnsembleGenerator._normalize_opening_transition_contract(
        candidate,
        prev_blueprint={"end_location": "한미증권 본사", "time_flow": "오전"},
    )
    assert route == "inferred"
    assert isinstance(candidate.get("opening_transition"), dict)
    assert candidate["opening_transition"].get("type") in {
        "direct_continuation",
        "explicit_transition",
        "jump_opening",
    }


def test_tranche1_normalize_opening_transition_reconciles_declared_canonical_mismatch():
    candidate = {
        "start_location": "한미증권 본사",
        "time_flow": "오전",
        "opening_transition": {"type": "explicit_transition"},
        "scene_breakdown": {
            "scene_1": {
                "location": "한미증권 본사",
                "summary": "회의가 곧장 이어진다",
            }
        },
    }

    route = BlueprintEnsembleGenerator._normalize_opening_transition_contract(
        candidate,
        prev_blueprint={"end_location": "한미증권 본사", "time_flow": "오전"},
    )

    assert route == "inferred"
    assert candidate["opening_transition"]["type"] == "direct_continuation"


def test_tranche1_normalize_direct_continuation_time_flow_inherits_prev_ending_timeline():
    candidate = {
        "start_location": "SW인베스트먼트 신규 원룸 오피스",
        "scene_breakdown": {
            "scene_1": {
                "location": "SW인베스트먼트 신규 원룸 오피스",
                "summary": "오피스에서 장세를 주시한다.",
                "key_events": ["호가창을 본다."],
            }
        },
        "opening_transition": {"type": "direct_continuation"},
    }

    inherited = BlueprintEnsembleGenerator._normalize_direct_continuation_time_flow(
        candidate,
        prev_blueprint={
            "time_flow": "2006년 4월 중순 늦은 밤 -> 자정 무렵",
            "ending_state": {"timeline": {"표현": "2006년 4월 중순 자정 무렵"}},
        },
    )

    assert inherited == "2006년 4월 중순 자정 무렵"
    assert candidate["time_flow"] == "2006년 4월 중순 자정 무렵"


def test_tranche1_normalize_direct_continuation_time_flow_skips_non_direct_transition():
    candidate = {
        "start_location": "SW인베스트먼트 신규 원룸 오피스",
        "opening_transition": {"type": "jump_opening"},
    }

    inherited = BlueprintEnsembleGenerator._normalize_direct_continuation_time_flow(
        candidate,
        prev_blueprint={
            "time_flow": "2006년 4월 중순 늦은 밤 -> 자정 무렵",
            "ending_state": {"timeline": {"표현": "2006년 4월 중순 자정 무렵"}},
        },
    )

    assert inherited == ""
    assert "time_flow" not in candidate


def test_tranche1_normalize_direct_continuation_time_flow_prefers_constraint_time_truth():
    candidate = {
        "start_location": "SW인베스트먼트 신규 원룸 오피스",
        "opening_transition": {"type": "direct_continuation"},
    }

    inherited = BlueprintEnsembleGenerator._normalize_direct_continuation_time_flow(
        candidate,
        prev_blueprint={
            "time_flow": "2006년 4월 중순 늦은 밤 -> 자정 무렵",
            "ending_state": {"timeline": {"표현": "2006년 4월 중순 자정 무렵"}},
        },
        constraint_block={
            "episode_progression_packet": {
                "time_truths": ["현재 Arc 시간축은 2006년 5월(봄 축)이다."],
            }
        },
    )

    assert inherited == "2006년 5월"
    assert candidate["time_flow"] == "2006년 5월"


def test_tranche1_normalize_direct_continuation_time_flow_accepts_month_only_constraint_truth():
    candidate = {
        "start_location": "SW인베스트먼트 신규 원룸 오피스",
        "opening_transition": {"type": "direct_continuation"},
    }

    inherited = BlueprintEnsembleGenerator._normalize_direct_continuation_time_flow(
        candidate,
        prev_blueprint={
            "time_flow": "2006년 4월 중순 늦은 밤 -> 자정 무렵",
            "ending_state": {"timeline": {"표현": "2006년 4월 중순 자정 무렵"}},
        },
        constraint_block={
            "episode_progression_packet": {
                "time_truths": ["현재 Arc 시간축은 5월(봄 축)이다."],
            }
        },
    )

    assert inherited == "5월"
    assert candidate["time_flow"] == "5월"


def test_tranche1_normalize_terminal_arc_ending_timeline_promotes_exact_arc_end_for_terminal_episode():
    candidate = {
        "ending_state": {
            "timeline": {
                "표현": "2006년 1월 늦은 오후",
            }
        }
    }

    normalized = BlueprintEnsembleGenerator._normalize_terminal_arc_ending_timeline(
        candidate,
        constraint_block={
            "terminal_timeline_lock": {
                "mode": "exact_terminal_match",
                "expression": "2006년 1월 15일 - 법인 설립 및 20억 자금 확보 완료",
                "timeline": {
                    "year": 2006,
                    "month": 1,
                    "day": 15,
                    "description": "법인 설립 및 20억 자금 확보 완료",
                },
            }
        },
    )

    assert normalized == "2006년 1월 15일 - 법인 설립 및 20억 자금 확보 완료"
    assert candidate["ending_state"]["timeline"]["day"] == 15


def test_tranche1_normalize_terminal_arc_ending_timeline_skips_cross_month_drift():
    candidate = {
        "ending_state": {
            "timeline": {
                "표현": "2006년 2월 초",
            }
        }
    }

    normalized = BlueprintEnsembleGenerator._normalize_terminal_arc_ending_timeline(
        candidate,
        constraint_block={
            "terminal_timeline_lock": {
                "mode": "exact_terminal_match",
                "expression": "2006년 1월 15일 - 법인 설립 및 20억 자금 확보 완료",
                "timeline": {
                    "year": 2006,
                    "month": 1,
                    "day": 15,
                    "description": "법인 설립 및 20억 자금 확보 완료",
                },
            }
        },
    )

    assert normalized == ""
    assert candidate["ending_state"]["timeline"]["표현"] == "2006년 2월 초"
