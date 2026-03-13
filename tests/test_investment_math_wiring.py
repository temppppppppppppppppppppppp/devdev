"""Wiring tests for Codex F integration in FourPhaseArcGenerator."""

from unittest.mock import MagicMock, patch

from modules.core.investment_arithmetic_checker import InvestmentArithmeticChecker
from modules.domain.agents.four_phase_arc_generator import FourPhaseArcGenerator


def _make_generator(*, genre: str = "investment", flash_ask=None) -> tuple[FourPhaseArcGenerator, dict]:
    gen = FourPhaseArcGenerator.__new__(FourPhaseArcGenerator)
    gen.context = MagicMock()
    gen.context.master_bible = {}
    gen.stats = {
        "total_attempts": 0,
        "phase1_complete": 0,
        "phase2_complete": 0,
        "phase3_pass": 0,
        "phase3_reject": 0,
    }
    gen.preflight = MagicMock()
    gen.preflight.analyze.return_value = {}
    gen.preflight.generate_analyst_injection.return_value = "preflight"
    gen.compiler = MagicMock()
    gen.compiler.compile.return_value = "constraints"
    gen.negative_injector = MagicMock()
    gen.negative_injector.generate_injection.return_value = "neg"
    gen.negative_injector.generate_self_check_prompt.return_value = "self_check"
    gen.negative_injector.record_rejection = MagicMock()
    gen._genre = genre
    gen._flash_ask = flash_ask
    gen.ensemble = MagicMock()
    candidate = {
        "_strategy": "balanced",
        "tactical_doc": "mock tactical",
        "state_constraints": {
            "arc_start_state": {},
            "arc_end_state": {},
            "investment_calc": {"transactions": []},
        },
    }
    gen.ensemble.generate_ensemble.return_value = (candidate, [candidate])
    gen.validator = MagicMock()
    gen.validator.validate.return_value = ("PASS", {"issues": [], "confidence": 90})
    gen._determine_ep_count = MagicMock(return_value=(4, "reason"))
    gen._generate_prev_context = MagicMock(return_value="prev")
    gen._check_arc_end_state = MagicMock(side_effect=lambda arc: arc)
    gen._load_execution_state = MagicMock(return_value={})
    return gen, candidate


def test_investment_advisory_reaches_director():
    gen, candidate = _make_generator(genre="investment", flash_ask=lambda _prompt: "[]")
    director = MagicMock()
    director.compare_and_select_arc.return_value = {
        "decision": "PASS",
        "selected_arc": candidate,
        "score": 95,
    }

    fake_checker = MagicMock()
    fake_checker.check.return_value = [
        {"check": "investment_arithmetic", "severity": "MAJOR", "text": "[F-1] mismatch"},
    ]

    with (
        patch("modules.core.investment_arithmetic_checker.InvestmentArithmeticChecker.from_yaml", return_value=fake_checker),
        patch(
            "modules.core.investment_math_verifier.InvestmentMathVerifier.verify",
            return_value=[{"check": "investment_math_llm", "severity": "MAJOR", "text": "[F-2] llm mismatch"}],
        ),
    ):
        _, result = gen.generate(
            arc_no=4,
            ep_start=1,
            vol_strategy="std",
            curr_block={},
            prev_arcs=[],
            director=director,
        )

    assert result["final_verdict"] == "PASS"
    advisory = director.compare_and_select_arc.call_args.kwargs["advisory"]
    quality_flags = director.compare_and_select_arc.call_args.kwargs["candidate_quality_flags"]
    assert "InvestmentMathVerifier" in advisory
    assert "[F-1] mismatch" in advisory
    assert "[F-2] llm mismatch" in advisory
    assert quality_flags[0]["force_pass_with_fix"] is True
    assert quality_flags[0]["score_cap"] == 89


def test_non_investment_genre_skips_codex_f():
    gen, candidate = _make_generator(genre="wuxia", flash_ask=lambda _prompt: "[]")
    director = MagicMock()
    director.compare_and_select_arc.return_value = {
        "decision": "PASS",
        "selected_arc": candidate,
        "score": 95,
    }

    with patch("modules.core.investment_arithmetic_checker.InvestmentArithmeticChecker.from_yaml") as mocked_from_yaml:
        _, result = gen.generate(
            arc_no=2,
            ep_start=1,
            vol_strategy="std",
            curr_block={},
            prev_arcs=[],
            director=director,
        )

    assert result["final_verdict"] == "PASS"
    assert not mocked_from_yaml.called
    assert director.compare_and_select_arc.call_args.kwargs["advisory"] == ""


def test_arc4_case_detected_as_major_gap():
    checker = InvestmentArithmeticChecker()
    arc = {
        "state_constraints": {
            "investment_calc": {
                "transactions": [
                    {
                        "ep_no": 17,
                        "asset": "금",
                        "action": "청산",
                        "entry_price": 620,
                        "exit_price": 680,
                        "leverage": 3,
                        "principal": 500_000_000,
                        "stated_profit": 500_000_000,
                    }
                ],
                "final_cash": 2_645_161_290,
                "final_total_assets": 2_645_161_290,
            }
        }
    }
    out = checker.check(arc, 4, prev_arc_end_state={"capital": 2_000_000_000})
    assert any(x.get("severity") == "MAJOR" and "수익 과대/과소" in x.get("text", "") for x in out)


def test_flash_disabled_skips_f2():
    gen, candidate = _make_generator(genre="investment", flash_ask=lambda _prompt: "[]")
    director = MagicMock()
    director.compare_and_select_arc.return_value = {
        "decision": "PASS",
        "selected_arc": candidate,
        "score": 95,
    }

    fake_checker = MagicMock()
    fake_checker.check.return_value = [
        {"check": "investment_arithmetic", "severity": "MAJOR", "text": "[F-1] mismatch"},
    ]

    def _fake_threshold(key, default):
        if key == "investment_math.flash_enabled":
            return False
        return default

    with (
        patch("modules.core.investment_arithmetic_checker.InvestmentArithmeticChecker.from_yaml", return_value=fake_checker),
        patch("modules.core.investment_math_verifier.InvestmentMathVerifier.verify") as mocked_verify,
        patch("modules.domain.agents.four_phase_arc_generator._threshold", side_effect=_fake_threshold),
    ):
        _, result = gen.generate(
            arc_no=4,
            ep_start=1,
            vol_strategy="std",
            curr_block={},
            prev_arcs=[],
            director=director,
        )

    assert result["final_verdict"] == "PASS"
    assert not mocked_verify.called


def test_investment_critical_candidate_filtered_before_director():
    gen, candidate = _make_generator(genre="investment", flash_ask=lambda _prompt: "[]")
    critical_candidate = {
        "_strategy": "aggressive",
        "tactical_doc": "critical tactical",
        "state_constraints": {
            "arc_start_state": {},
            "arc_end_state": {},
            "investment_calc": {"transactions": []},
        },
    }
    clean_candidate = {
        "_strategy": "balanced",
        "tactical_doc": "clean tactical",
        "state_constraints": {
            "arc_start_state": {},
            "arc_end_state": {},
            "investment_calc": {"transactions": []},
        },
    }
    gen.ensemble.generate_ensemble.return_value = (critical_candidate, [critical_candidate, clean_candidate])

    director = MagicMock()
    director.compare_and_select_arc.return_value = {
        "decision": "PASS",
        "selected_arc": clean_candidate,
        "score": 95,
    }

    fake_checker = MagicMock()
    fake_checker.check.side_effect = [
        [{"check": "investment_arithmetic", "severity": "CRITICAL", "text": "[F-1] critical mismatch"}],
        [],
    ]

    with patch(
        "modules.core.investment_arithmetic_checker.InvestmentArithmeticChecker.from_yaml",
        return_value=fake_checker,
    ):
        _, result = gen.generate(
            arc_no=4,
            ep_start=1,
            vol_strategy="std",
            curr_block={},
            prev_arcs=[],
            director=director,
        )

    assert result["final_verdict"] == "PASS"
    passed_candidates = director.compare_and_select_arc.call_args.kwargs["candidates"]
    quality_flags = director.compare_and_select_arc.call_args.kwargs["candidate_quality_flags"]
    assert passed_candidates == [clean_candidate]
    assert len(quality_flags) == 1
    assert quality_flags[0]["force_reject"] is False
    assert quality_flags[0]["force_pass_with_fix"] is False
