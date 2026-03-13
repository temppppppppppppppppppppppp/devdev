from unittest.mock import MagicMock

from modules.core.information_diffusion import InformationDiffusion


class _StubContext:
    def __init__(self):
        self.db = MagicMock()
        self.master_bible = {"MasterBible": {"ProjectData": {"protagonist_faction": "하북팽가"}}}


def test_propagate_event_uses_same_faction_delay_for_dict_payloads():
    diffusion = InformationDiffusion(_StubContext())
    diffusion.register_event("arc1_ep1_event", "소문", arc=1, episode=1, location="개봉")

    newly_informed = diffusion.propagate_event(
        "arc1_ep1_event",
        current_arc=1,
        current_episode=2,
        npc_locations={"철혈단": {"current_location": "산동", "faction": "하북팽가"}},
    )

    assert newly_informed == ["철혈단"]
    assert diffusion.npc_knows("철혈단", "arc1_ep1_event") is True


def test_propagate_event_respects_isolated_npc_flag():
    diffusion = InformationDiffusion(_StubContext())
    diffusion.register_event("arc1_ep1_secret", "비밀 사건", arc=1, episode=1, location="개봉")

    newly_informed = diffusion.propagate_event(
        "arc1_ep1_secret",
        current_arc=2,
        current_episode=20,
        npc_locations={"은둔고수": {"current_location": "심원곡", "isolated": True}},
    )

    assert newly_informed == []
    assert diffusion.npc_knows("은둔고수", "arc1_ep1_secret") is False
