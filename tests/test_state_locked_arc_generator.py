from unittest.mock import MagicMock

from modules.domain.agents.state_locked_arc_generator import (
    ARC_SYNTHESIS_PROMPT,
    EPISODE_TEMPLATE,
    STATE_EXTRACTION_PROMPT,
    StateLockedArcGenerator,
)


def _make_agent() -> StateLockedArcGenerator:
    return StateLockedArcGenerator(MagicMock(), MagicMock())


def test_state_locked_prompts_use_canonical_inventory_contract():
    assert '"end_equipment": ["종료 시 전체 소지품"]' in STATE_EXTRACTION_PROMPT
    assert '"protagonist_items": ["이 화에서 새로 획득해 종료 시점까지 남는 아이템"]' in STATE_EXTRACTION_PROMPT
    assert '"protagonist_items": ["Arc 전체에서 새로 획득해 종료 시점까지 남는 아이템"]' in ARC_SYNTHESIS_PROMPT
    assert "- 소지품: [종료 시 전체 소지품]" in EPISODE_TEMPLATE


def test_extract_state_prefers_explicit_protagonist_items_and_end_equipment(monkeypatch):
    agent = _make_agent()
    monkeypatch.setattr(
        agent,
        "ask",
        lambda *args, **kwargs: {
            "end_location": "시장",
            "end_energy": 90,
            "end_injuries": "없음",
            "end_equipment": ["장부"],
            "protagonist_items": [],
            "items_acquired": ["stale-only"],
            "items_consumed": [],
            "key_events": ["확인 완료"],
        },
    )

    end_state = agent._extract_state(
        "본문",
        {"location": "창고", "energy": 100, "injuries": "없음", "equipment": ["인장"]},
    )

    assert end_state["equipment"] == ["장부"]
    assert end_state["protagonist_items"] == []
    assert end_state["items_acquired"] == []


def test_extract_state_derives_end_equipment_from_deltas_when_missing(monkeypatch):
    agent = _make_agent()
    monkeypatch.setattr(
        agent,
        "ask",
        lambda *args, **kwargs: {
            "end_location": "시장",
            "end_energy": 88,
            "end_injuries": "경상",
            "protagonist_items": ["장부"],
            "items_consumed": ["인장"],
            "key_events": ["교환 완료"],
        },
    )

    end_state = agent._extract_state(
        "본문",
        {"location": "창고", "energy": 100, "injuries": "없음", "equipment": ["인장"]},
    )

    assert end_state["equipment"] == ["장부"]
    assert end_state["protagonist_items"] == ["장부"]
    assert end_state["items_acquired"] == ["장부"]


def test_synthesize_arc_emits_canonical_protagonist_items_and_inventory():
    agent = _make_agent()

    arc = agent._synthesize_arc(
        arc_no=4,
        ep_start=10,
        ep_end=11,
        episodes=[
            {
                "ep_num": 10,
                "text": "제 10화 본문",
                "beat": "장부를 확보한다",
                "end_state": {
                    "protagonist_items": ["장부"],
                    "items_consumed": ["인장"],
                },
            }
        ],
        start_state={"location": "창고", "energy": 100, "injuries": "없음", "equipment": ["인장"]},
        end_state={"location": "시장", "energy": 92, "injuries": "없음", "equipment": ["장부"]},
    )

    assert arc["state_constraints"]["protagonist_items"] == ["장부"]
    assert arc["state_constraints"]["items_acquired"] == ["장부"]
    assert arc["joint_docs"]["physical_inventory"] == ["장부"]
