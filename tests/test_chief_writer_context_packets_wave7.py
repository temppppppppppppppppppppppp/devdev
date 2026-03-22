import inspect
from unittest.mock import MagicMock

from modules.domain.agents.chief_writer_context_packets import ChiefWriterContextPackets


class _OwnerStub:
    def __init__(self) -> None:
        self.host = MagicMock()
        self.context = MagicMock()

    def _fit_compact_text(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."


def _make_packets() -> ChiefWriterContextPackets:
    return ChiefWriterContextPackets(_OwnerStub())


def test_generate_episode_digest_delegates_phase_families(monkeypatch):
    packets = _make_packets()
    calls = []

    def fake_event(self, manuscript):
        calls.append(("event", manuscript))
        return ["사망 NPC: 철수"], {"철수"}

    def fake_state(self, manuscript):
        calls.append(("state", manuscript))
        return ["마지막 위치: 흑림동굴"]

    def fake_continuity(self, manuscript, dead_npcs):
        calls.append(("continuity", manuscript, dead_npcs))
        return ['클리프행어: "끝"']

    def fake_format(self, digest_parts, ep_num):
        calls.append(("format", list(digest_parts), ep_num))
        return "DIGEST"

    monkeypatch.setattr(ChiefWriterContextPackets, "_build_episode_event_digest_parts", fake_event)
    monkeypatch.setattr(ChiefWriterContextPackets, "_build_episode_state_digest_parts", fake_state)
    monkeypatch.setattr(ChiefWriterContextPackets, "_build_episode_continuity_digest_parts", fake_continuity)
    monkeypatch.setattr(ChiefWriterContextPackets, "_format_episode_digest", fake_format)

    result = packets._generate_episode_digest("가" * 220, ep_num=8)

    assert result == "DIGEST"
    assert calls == [
        ("event", "가" * 220),
        ("state", "가" * 220),
        ("continuity", "가" * 220, {"철수"}),
        ("format", ["사망 NPC: 철수", "마지막 위치: 흑림동굴", '클리프행어: "끝"'], 8),
    ]


def test_build_episode_state_digest_parts_keeps_injury_location_skill_order():
    packets = _make_packets()
    manuscript = "가" * 220 + "왼팔이 부러졌다. 청운산에 도착했다. 태극검법을 터득했다. 흑림동굴에 들어갔다."

    parts = packets._build_episode_state_digest_parts(manuscript)

    assert parts[0].startswith("부상 상태: ")
    assert "왼팔이 부러졌" in parts[0]
    assert parts[1] == "마지막 위치: 흑림동굴"
    assert parts[2] == "습득 무공: 태극검법"


def test_build_episode_continuity_digest_parts_excludes_dead_from_downed():
    packets = _make_packets()
    manuscript = "철수는 쓰러졌다. 영희는 기절했다."

    parts = packets._build_episode_continuity_digest_parts(manuscript, {"철수"})

    assert parts == ["부상/기절 NPC: 영희"]


def test_generate_episode_digest_loc_stays_below_80():
    assert len(inspect.getsource(ChiefWriterContextPackets._generate_episode_digest).splitlines()) < 80
