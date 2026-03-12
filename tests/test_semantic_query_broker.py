from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.core.semantic_query_broker import SemanticQueryBroker


def test_get_key_relationship_candidates_collects_source_backed_evidence():
    world_state = SimpleNamespace(
        get_state_dict=lambda: {
            "protagonist": {"name": "주인공"},
            "relationships": {"연홍": "죽마고우"},
            "alive_npcs": {
                "연홍": {
                    "relation": "신뢰",
                    "known_attrs": {"relation_to_protag": {"value": "어릴 때부터 함께 자란 동네 친구"}},
                }
            },
        }
    )
    fact_ledger = SimpleNamespace(
        _ledger={
            "characters": {
                "연홍": {
                    "relationship": "소꿉친구",
                    "established_ep": 3,
                    "history": ["ep3: 어릴 때부터 함께 자람", "ep11: 주인공을 위해 거짓말을 감수함"],
                }
            }
        }
    )
    db = MagicMock()
    db.get_npc_relationship_edges.return_value = [
        {"npc1": "주인공", "npc2": "연홍", "relation": "신뢰", "updated_ep": 12}
    ]
    db.get_relationship_history.return_value = [
        {"old_relation": "중립", "new_relation": "죽마고우", "change_ep": 5}
    ]

    broker = SemanticQueryBroker(
        db=db,
        world_state=world_state,
        fact_ledger=fact_ledger,
        protagonist_name="주인공",
    )

    candidates = broker.get_key_relationship_candidates(limit=2)

    assert candidates
    top = candidates[0]
    assert top["name"] == "연홍"
    assert any(evidence["source"].startswith("world_state") for evidence in top["evidences"])
    assert any("어릴 때부터" in evidence["text"] for evidence in top["evidences"])


def test_answer_relation_intent_childhood_friend_uses_taxonomy_and_evidence():
    world_state = SimpleNamespace(
        get_state_dict=lambda: {
            "protagonist": {"name": "주인공"},
            "relationships": {"연홍": "죽마고우"},
            "alive_npcs": {},
        }
    )
    fact_ledger = SimpleNamespace(
        _ledger={
            "characters": {
                "연홍": {
                    "relationship": "",
                    "established_ep": 2,
                    "history": ["ep2: 어린 시절부터 한 동네에서 자란 친구"],
                },
                "철무": {
                    "relationship": "라이벌",
                    "established_ep": 4,
                    "history": ["ep4: 맞수로 각인됨"],
                },
            }
        }
    )

    broker = SemanticQueryBroker(
        world_state=world_state,
        fact_ledger=fact_ledger,
        protagonist_name="주인공",
    )

    answer = broker.answer_relation_intent("childhood_friend", limit=2)

    assert answer["label"] == "소꿉친구"
    assert answer["candidates"]
    assert answer["candidates"][0]["name"] == "연홍"
    assert all(candidate["name"] != "철무" for candidate in answer["candidates"])
