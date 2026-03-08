from types import SimpleNamespace

from modules.core.stage2_orchestrator import Stage2Orchestrator
from modules.core.stage3_orchestrator import Stage3Orchestrator


class _Dummy:
    pass


def test_stage2_telemetry_includes_four_phase_sub_agents():
    main_agent = _Dummy()
    preflight = _Dummy()
    ensemble = _Dummy()
    validator = _Dummy()
    four_phase = SimpleNamespace(preflight=preflight, ensemble=ensemble, validator=validator)
    ctx = SimpleNamespace(agents={"analyst": main_agent, "four_phase": four_phase})

    orch = Stage2Orchestrator(app=SimpleNamespace(), context=ctx)
    orch._set_agent_telemetry_context(ep_num=12)

    assert getattr(main_agent, "_current_stage", None) == 2
    assert getattr(main_agent, "_current_ep_num", None) == 12
    assert getattr(preflight, "_current_stage", None) == 2
    assert getattr(preflight, "_current_ep_num", None) == 12
    assert getattr(ensemble, "_current_stage", None) == 2
    assert getattr(ensemble, "_current_ep_num", None) == 12
    assert getattr(validator, "_current_stage", None) == 2
    assert getattr(validator, "_current_ep_num", None) == 12


def test_stage3_telemetry_includes_three_phase_ensemble():
    main_agent = _Dummy()
    sub_ensemble = _Dummy()
    three_phase_bp = SimpleNamespace(ensemble=sub_ensemble)
    ctx = SimpleNamespace(agents={"director": main_agent, "three_phase_bp": three_phase_bp})

    orch = Stage3Orchestrator(app=SimpleNamespace(), context=ctx)
    orch._set_agent_telemetry_context(ep_num=7)

    assert getattr(main_agent, "_current_stage", None) == 3
    assert getattr(main_agent, "_current_ep_num", None) == 7
    assert getattr(sub_ensemble, "_current_stage", None) == 3
    assert getattr(sub_ensemble, "_current_ep_num", None) == 7
