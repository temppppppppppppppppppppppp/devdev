"""[D-2] 에피소드 롤백 NPC/누적 상태 되감기 테스트."""

from unittest.mock import MagicMock

import pytest

from modules.core.db_manager import DBManager


@pytest.fixture
def db(tmp_path):
    """테스트용 DB."""
    _db = DBManager(tmp_path / "test_rollback.db")
    try:
        yield _db
    finally:
        _db.close()


class TestResetAfterNpcHistory:
    def test_npc_history_deleted_after_target_ep(self, db):
        db.insert_npc_change("노사부", 3, 1, "status", "alive", "dead", "arc")
        db.insert_npc_change("흑풍", 5, 1, "personality", "냉정", "분노", "arc")
        db.insert_npc_change("이청풍", 2, 1, "skill", "", "검술", "arc")

        db.reset_after(4)

        assert len(db.get_npc_history("흑풍")) == 0
        assert len(db.get_npc_history("노사부")) == 1
        assert len(db.get_npc_history("이청풍")) == 1

    def test_npc_history_all_deleted_when_target_ep_1(self, db):
        db.insert_npc_change("노사부", 1, 1, "status", "alive", "dead", "arc")
        db.insert_npc_change("흑풍", 2, 1, "role", "적", "동맹", "arc")

        db.reset_after(1)

        assert len(db.get_npc_history("노사부")) == 0
        assert len(db.get_npc_history("흑풍")) == 0


class TestResetAfterSentenceHashes:
    def test_sentence_hashes_deleted_after_target_ep(self, db):
        db.store_sentence_hashes(3, [("hash_a", "문장A")])
        db.store_sentence_hashes(5, [("hash_b", "문장B")])

        db.reset_after(4)

        assert len(db.get_sentence_hashes(3)) == 1
        assert len(db.get_sentence_hashes(5)) == 0


class TestResetAfterSatisfactionTags:
    def test_satisfaction_tags_deleted_after_target_ep(self, db):
        db.save_satisfaction_tag(
            3,
            {
                "primary_tag": "성장",
                "satisfaction_score": 8,
                "protagonist_agency": "자력",
                "frustration_flag": False,
            },
        )
        db.save_satisfaction_tag(
            5,
            {
                "primary_tag": "고난",
                "satisfaction_score": 4,
                "protagonist_agency": "타력",
                "frustration_flag": True,
            },
        )

        db.reset_after(4)

        assert db.get_satisfaction_tag(3) is not None
        assert db.get_satisfaction_tag(5) is None


class TestGetRollbackImpact:
    def test_returns_correct_counts(self, db):
        db.insert_npc_change("노사부", 3, 1, "status", "alive", "dead", "arc")
        db.insert_npc_change("흑풍", 5, 1, "personality", "냉정", "분노", "arc")
        db.store_sentence_hashes(5, [("hash_a", "문장A")])
        db.save_manuscript(5, "제5화", "내용")

        impact = db.get_rollback_impact(4)

        assert impact["npc_history"] == 1
        assert impact["sentence_hashes"] == 1
        assert impact["manuscripts"] == 1

    def test_includes_satisfaction_tag_count(self, db):
        db.save_satisfaction_tag(
            5,
            {
                "primary_tag": "성장",
                "satisfaction_score": 7,
                "protagonist_agency": "자력",
                "frustration_flag": False,
            },
        )

        impact = db.get_rollback_impact(4)
        assert impact["satisfaction_tags"] == 1

    def test_empty_db_returns_all_zeros(self, db):
        impact = db.get_rollback_impact(1)
        assert all(v == 0 for v in impact.values())


class TestWorldStateRollback:
    def test_rollback_replays_npc_martial_state_before_target(self, db):
        """npc_martial_state_changes should replay only episodes before the rollback target."""
        from modules.core.world_state import WorldStateManager

        db.save_episode_bible(
            2,
            {
                "state_changes": {
                    "npc_martial_state_changes": [
                        {"name": "Chief Han", "episode": 2, "realm": "Peak", "techniques_learned": ["Storm Palm"]}
                    ]
                },
            },
        )
        db.save_episode_bible(
            5,
            {
                "state_changes": {
                    "npc_martial_state_changes": [
                        {
                            "name": "Chief Han",
                            "episode": 5,
                            "realm": "Transcendent",
                            "techniques_learned": ["Sky Step"],
                        }
                    ]
                },
            },
        )

        ws = WorldStateManager(db)
        ws.update_from_state_changes(
            2,
            {"npc_martial_state_changes": [{"name": "Chief Han", "episode": 2, "realm": "Peak", "techniques_learned": ["Storm Palm"]}]},
        )
        ws.update_from_state_changes(
            5,
            {"npc_martial_state_changes": [{"name": "Chief Han", "episode": 5, "realm": "Transcendent", "techniques_learned": ["Sky Step"]}]},
        )
        ws.save()

        ws.rollback_to(3)

        martial_state = ws._state["alive_npcs"]["Chief Han"]["martial_state"]
        assert martial_state["realm"] == "Peak"
        assert martial_state["realm_changed_ep"] == 2
        assert martial_state["techniques"] == ["Storm Palm"]
        assert martial_state["last_martial_ep"] == 2

    def test_rollback_replays_episodes_before_target(self, db):
        """[Sweep64] rollback_to는 target_ep 이전 에피소드를 리플레이해야 함."""
        from modules.core.world_state import WorldStateManager

        # ep 2: NPC 등장 (episode_bible에 저장)
        db.save_episode_bible(
            2,
            {
                "state_changes": {"npc_deaths": [], "relationship_changes": [{"npc": "이청풍", "to": "동맹"}]},
                "new_npcs": ["이청풍"],
            },
        )
        # ep 5: NPC 사망 (episode_bible에 저장)
        db.save_episode_bible(
            5,
            {
                "state_changes": {"npc_deaths": [{"name": "노사부", "cause": "전투"}]},
            },
        )

        ws = WorldStateManager(db)
        ws.update_from_state_changes(2, {"relationship_changes": [{"npc": "이청풍", "to": "동맹"}]})
        ws.update_from_state_changes(5, {"npc_deaths": [{"name": "노사부", "cause": "전투"}]})
        ws.save()
        assert "노사부" in ws._state["dead_npcs"]

        # rollback_to(3): ep 1~2만 리플레이 → 이청풍 관계는 살아있고, 노사부 사망은 없어야 함
        ws.rollback_to(3)

        assert ws._state["dead_npcs"] == {}
        assert ws._state["relationships"].get("이청풍") == "동맹"
        assert ws._state["last_updated_ep"] == 2

    def test_rollback_to_1_gives_empty_state(self, db):
        """rollback_to(1)이면 리플레이할 에피소드 없음 → 초기 상태."""
        from modules.core.world_state import WorldStateManager

        db.save_episode_bible(
            5,
            {
                "state_changes": {"npc_deaths": [{"name": "노사부", "cause": "전투"}]},
            },
        )
        ws = WorldStateManager(db)
        ws.update_from_state_changes(5, {"npc_deaths": [{"name": "노사부", "cause": "전투"}]})
        ws.save()

        ws.rollback_to(1)

        assert ws._state["dead_npcs"] == {}
        assert ws._state["last_updated_ep"] == 0


class TestFactLedgerRollback:
    def test_rollback_replays_episodes_before_target(self, db):
        """[Sweep64] rollback_to는 target_ep 이전 에피소드를 리플레이해야 함."""
        from modules.core.fact_ledger import FactLedger

        # ep 2: 관계 변화 (episode_bible에 저장)
        db.save_episode_bible(
            2,
            {
                "state_changes": {"relationship_changes": [{"npc": "이청풍", "to": "동맹"}]},
                "new_npcs": ["이청풍"],
            },
        )
        # ep 5: NPC 사망 (episode_bible에 저장)
        db.save_episode_bible(
            5,
            {
                "state_changes": {"npc_deaths": [{"name": "노사부", "cause": "전투"}]},
            },
        )

        fl = FactLedger(db)
        fl.update_from_state_changes(2, {"relationship_changes": [{"npc": "이청풍", "to": "동맹"}]})
        fl.update_from_state_changes(5, {"npc_deaths": [{"name": "노사부", "cause": "전투"}]})
        fl.save()
        assert "노사부" in fl._ledger.get("characters", {})

        # rollback_to(3): ep 1~2만 리플레이 → 이청풍은 존재, 노사부 사망은 없어야 함
        fl.rollback_to(3)

        assert "이청풍" in fl._ledger["characters"]
        chars = fl._ledger["characters"]
        # 노사부는 ep5에서만 등장했으므로 리플레이에 없어야 함
        assert chars.get("노사부", {}).get("status") != "dead"
        assert fl._ledger["last_updated_ep"] == 2

    def test_rollback_to_1_gives_empty_ledger(self, db):
        """rollback_to(1)이면 리플레이할 에피소드 없음 → 빈 원장."""
        from modules.core.fact_ledger import FactLedger

        db.save_episode_bible(
            5,
            {
                "state_changes": {"npc_deaths": [{"name": "노사부", "cause": "전투"}]},
            },
        )
        fl = FactLedger(db)
        fl.update_from_state_changes(5, {"npc_deaths": [{"name": "노사부", "cause": "전투"}]})
        fl.save()

        fl.rollback_to(1)

        assert fl._ledger["characters"] == {}
        assert fl._ledger["last_updated_ep"] == 0


class TestAutoBacktrackIntegration:
    def test_backtrack_calls_world_state_rollback(self, db):
        from modules.core.project_manager import ProjectContext

        pm = ProjectContext.__new__(ProjectContext)
        pm.db = db
        pm.paths = MagicMock()
        pm.paths.drafts.exists.return_value = False
        pm.paths.drafts.glob.return_value = []

        mock_ws = MagicMock()
        mock_ws.rollback_to = MagicMock()
        mock_fl = MagicMock()
        mock_fl.rollback_to = MagicMock()

        db.save_manuscript(5, "테스트", "내용" * 50)

        result = pm.auto_backtrack_v35(
            "제 3화부터 설정 오류",
            memory=None,
            world_state=mock_ws,
            fact_ledger=mock_fl,
        )

        assert result is not None
        mock_ws.rollback_to.assert_called_once()
        mock_fl.rollback_to.assert_called_once()

    def test_backtrack_without_optional_args(self, db):
        from modules.core.project_manager import ProjectContext

        pm = ProjectContext.__new__(ProjectContext)
        pm.db = db
        pm.paths = MagicMock()
        pm.paths.drafts.exists.return_value = False
        pm.paths.drafts.glob.return_value = []

        db.save_manuscript(5, "테스트", "내용" * 50)

        result = pm.auto_backtrack_v35("제 4화부터 설정 오류", memory=None)
        assert result is not None
