from unittest.mock import MagicMock

from modules.core.project_manager import ProjectContext


def _make_ctx() -> ProjectContext:
    ctx = ProjectContext.__new__(ProjectContext)
    ctx.db = MagicMock()
    ctx.master_bible = {}
    ctx.save_v20_anchor = MagicMock()
    ctx.sync_and_cleanup_seeds = MagicMock()
    ctx._normalize_seed_id = MagicMock(side_effect=lambda raw: f"NORM-{raw}")
    ctx._get_npc_hud_key = MagicMock(return_value="NPC_Business_Profile")
    return ctx


def test_normalize_recovered_seeds_filters_non_dict_and_fills_unknown():
    ctx = _make_ctx()

    normalized = ctx._normalize_recovered_seeds(
        [
            {"seed_id": "A-1", "text": "one"},
            {"id": "B-2", "text": "two"},
            {"text": "three"},
            "skip",
        ]
    )

    assert normalized == [
        {"seed_id": "NORM-A-1", "text": "one"},
        {"id": "B-2", "text": "two", "seed_id": "NORM-B-2"},
        {"text": "three", "seed_id": "UNKNOWN"},
    ]


def test_merge_lore_npc_hud_updates_merges_matching_hud_only():
    ctx = _make_ctx()
    ctx.master_bible = {
        "MasterBible": {
            "AssetLibrary": {
                "KeyNPCs": [
                    {
                        "name": "Seo",
                        "NPC_Business_Profile": {
                            "achievement_rate": 10,
                            "equipment": ["pen"],
                        },
                    }
                ]
            }
        }
    }

    ctx._merge_lore_npc_hud_updates(
        {
            "Key_NPCs": [
                {
                    "name": "Seo",
                    "NPC_Business_Profile": {
                        "achievement_rate": 25,
                        "equipment": ["pen", "tablet"],
                    },
                },
                {"name": "Skip", "NPC_Business_Profile": "bad"},
            ]
        }
    )

    npc = ctx.master_bible["MasterBible"]["AssetLibrary"]["KeyNPCs"][0]
    assert npc["NPC_Business_Profile"]["achievement_rate"] == 25
    assert npc["NPC_Business_Profile"]["equipment"] == ["pen", "tablet"]


def test_sync_episode_vector_memory_marks_partial_sync_on_exception():
    ctx = _make_ctx()
    memory = MagicMock()
    memory.memorize_v20_episode.side_effect = RuntimeError("vector down")

    ctx._sync_episode_vector_memory(
        ep_num=7,
        manuscript_data={"content": "manuscript"},
        state_data={"context_audit": {"summary": "summary"}},
        causal_links=[{"a": 1}],
        memory=memory,
    )

    ctx.db.update_sync_status.assert_called_once_with(7, 2)


def test_commit_full_episode_data_restores_bible_and_sync_status_on_failure():
    ctx = _make_ctx()
    ctx.master_bible = {"MasterBible": {"AssetLibrary": {"KeyNPCs": []}}}
    ctx._persist_episode_bible_and_factory = MagicMock(side_effect=RuntimeError("db fail"))
    ctx._merge_lore_npc_hud_updates = MagicMock()
    ctx._normalize_recovered_seeds = MagicMock(return_value=[])
    ctx._sync_episode_vector_memory = MagicMock()

    ok = ctx.commit_full_episode_data(
        ep_num=3,
        manuscript_data={},
        martial_data={},
        state_data={},
        causal_links=[],
        karma_data={},
        lore_data={},
        recovered_seeds=[],
        memory=MagicMock(),
    )

    assert ok is False
    assert ctx.master_bible == {"MasterBible": {"AssetLibrary": {"KeyNPCs": []}}}
    assert ctx.db.update_sync_status.call_args_list[-1].args == (3, 0)
