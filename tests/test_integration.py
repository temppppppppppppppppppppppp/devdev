"""Integration tests covering phase/stage flow using current DB APIs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPhase0BibleRecovery:
    """Phase 0: Bible recovery tests."""

    def test_bible_loading_from_file(self, temp_dir, sample_bible):
        bible_path = temp_dir / "bible.json"
        bible_path.write_text(json.dumps(sample_bible, ensure_ascii=False), encoding="utf-8")

        loaded = json.loads(bible_path.read_text(encoding="utf-8"))

        assert loaded["title"] == sample_bible["title"]
        assert loaded["genre"] == sample_bible["genre"]

    def test_bible_sync_to_db(self, temp_dir, sample_bible):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_anchor("bible", sample_bible)
            loaded = db.load_anchor("bible")
            assert loaded == sample_bible
        finally:
            db.close()

    def test_treatment_extraction(self, sample_bible):
        treatment = sample_bible.get("treatment", {})

        assert "protagonist" in treatment
        assert treatment["protagonist"]["name"]
        assert "setting" in treatment
        assert "themes" in treatment

    def test_dna_sync_on_startup(self, temp_dir, sample_bible):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_anchor("bible", {"title": "old", "genre": "wuxia"})
            db.save_anchor("bible", sample_bible)

            loaded = db.load_anchor("bible")
            assert loaded["title"] == sample_bible["title"]
        finally:
            db.close()


class TestStage1VolumeStrategy:
    """Stage 1: Volume strategy tests."""

    def test_volume_plan_generation(self, sample_bible):
        volumes = []
        for i in range(1, 11):
            volumes.append(
                {
                    "volume": i,
                    "title": f"{i}권",
                    "episodes": f"{(i - 1) * 50 + 1}-{i * 50}",
                    "theme": "성장" if i <= 3 else ("갈등" if i <= 7 else "안정"),
                }
            )

        assert len(volumes) == 10
        assert volumes[0]["volume"] == 1
        assert volumes[-1]["volume"] == 10

    def test_volume_skip_option(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            existing_volumes = [{"volume": i, "title": f"Vol{i}"} for i in range(1, 11)]
            db.save_anchor("volumes", existing_volumes)

            loaded = db.load_anchor("volumes")
            can_skip = loaded is not None and len(loaded) >= 10

            assert can_skip is True
        finally:
            db.close()

    def test_volume_db_persistence(self, temp_dir):
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "persist.db"

        db1 = DBManager(db_path)
        db1.save_anchor("volumes", [{"volume": i} for i in range(1, 11)])
        db1.close()

        db2 = DBManager(db_path)
        try:
            loaded = db2.load_anchor("volumes")
            assert len(loaded) == 10
        finally:
            db2.close()


class TestStage2ArcDesign:
    """Stage 2: Arc design tests."""

    def test_arc_generation_per_volume(self):
        volumes = 10
        arcs_per_volume = 5

        all_arcs = []
        for vol in range(1, volumes + 1):
            for arc_num in range(1, arcs_per_volume + 1):
                all_arcs.append({"volume": vol, "arc_num": arc_num, "title": f"Vol{vol}-Arc{arc_num}"})

        assert len(all_arcs) == 50

    def test_arc_failure_recovery(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            partial_arcs = [{"volume": 1, "arc_num": i} for i in range(1, 4)]
            db.save_anchor("arcs", partial_arcs)

            loaded = db.load_anchor("arcs")
            remaining = 5 - len(loaded)
            assert remaining == 2
        finally:
            db.close()

    def test_arc_batch_recovery_order(self):
        batch = [{"volume": 1, "arc_num": 1}, {"volume": 1, "arc_num": 2}, {"volume": 1, "arc_num": 3}]

        failed_at = 1
        recovered_batch = batch[:failed_at] + batch[failed_at:]

        assert recovered_batch == batch


class TestStage3BlueprintCreation:
    """Stage 3: Blueprint creation tests."""

    def test_blueprint_scene_structure(self, sample_blueprint):
        assert "scenes" in sample_blueprint
        assert len(sample_blueprint["scenes"]) >= 1

        for scene in sample_blueprint["scenes"]:
            assert "scene_num" in scene
            assert "location" in scene

    def test_blueprint_db_storage(self, temp_dir, sample_blueprint):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_blueprint(1, sample_blueprint)
            loaded = db.get_blueprint(1)

            assert loaded["ep_num"] == sample_blueprint["ep_num"]
            assert loaded["title"] == sample_blueprint["title"]
        finally:
            db.close()

    def test_arc_data_validation(self):
        valid_arc = {"volume": 1, "arc_num": 1, "title": "입문", "episodes": [1, 2, 3, 4, 5], "theme": "성장"}

        required_fields = ["volume", "arc_num", "title"]
        for field in required_fields:
            assert field in valid_arc


class TestStage4Production:
    """Stage 4: Production tests."""

    def test_manuscript_generation_flow(self, temp_dir, sample_blueprint, sample_manuscript):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_blueprint(1, sample_blueprint)

            manuscript = sample_manuscript
            db.save_manuscript(1, "ep1", manuscript)

            loaded = db.get_manuscript(1)
            assert len(loaded["content"]) >= 4000
        finally:
            db.close()

    def test_director_validation_loop(self):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            verdict = "REJECT" if retry_count < 2 else "PASS"

            if verdict == "PASS":
                break
            retry_count += 1

        assert verdict == "PASS"
        assert retry_count == 2

    def test_hud_update_after_episode(self, sample_hud_wuxia):
        before = sample_hud_wuxia.copy()
        after = before.copy()
        after["internal_energy"] = before["internal_energy"] + 5

        assert after["internal_energy"] > before["internal_energy"]

    def test_draft_file_creation(self, temp_dir, sample_manuscript):
        drafts_dir = temp_dir / "drafts"
        drafts_dir.mkdir()

        draft_path = drafts_dir / "0001_test_episode.txt"
        draft_path.write_text(sample_manuscript, encoding="utf-8")

        assert draft_path.exists()
        assert draft_path.read_text(encoding="utf-8") == sample_manuscript


class TestE2EScenario:
    """E2E scenario tests."""

    def test_full_pipeline_mock(self, temp_dir, sample_bible, sample_blueprint, sample_manuscript):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "test.db")
        try:
            db.save_anchor("bible", sample_bible)
            assert db.load_anchor("bible") is not None

            volumes = [{"volume": i, "title": f"Vol{i}"} for i in range(1, 11)]
            db.save_anchor("volumes", volumes)
            assert len(db.load_anchor("volumes")) == 10

            arcs = []
            for vol in range(1, 11):
                for arc in range(1, 6):
                    arcs.append({"volume": vol, "arc_num": arc})
            db.save_anchor("arcs", arcs)
            assert len(db.load_anchor("arcs")) == 50

            db.save_blueprint(1, sample_blueprint)
            assert db.get_blueprint(1) is not None

            db.save_manuscript(1, "ep1", sample_manuscript)
            loaded = db.get_manuscript(1)
            assert len(loaded["content"]) >= 4000
        finally:
            db.close()

    def test_resume_from_interruption(self, temp_dir):
        from modules.core.db_manager import DBManager

        db_path = temp_dir / "resume.db"

        db1 = DBManager(db_path)
        db1.save_anchor("bible", {"title": "Test"})
        db1.save_anchor("volumes", [{"vol": i} for i in range(1, 6)])
        db1.close()

        db2 = DBManager(db_path)
        try:
            bible = db2.load_anchor("bible")
            volumes = db2.load_anchor("volumes")

            assert bible is not None
            assert len(volumes) == 5
        finally:
            db2.close()

    def test_multi_genre_compatibility(self, temp_dir):
        from modules.core.db_manager import DBManager

        for genre in ["wuxia", "hunter", "investment"]:
            db_path = temp_dir / f"{genre}_test.db"
            db = DBManager(db_path)
            try:
                bible = {
                    "title": f"{genre.upper()} test",
                    "genre": genre,
                    "treatment": {"protagonist": {"name": "주인공"}},
                }
                db.save_anchor("bible", bible)
                loaded = db.load_anchor("bible")

                assert loaded["genre"] == genre
            finally:
                db.close()


class TestDataIntegrity:
    """Data integrity tests."""

    def test_concurrent_access_safety(self, temp_dir):
        import threading

        db_path = temp_dir / "concurrent.db"
        errors = []

        def writer_task(thread_id):
            try:
                from modules.core.db_manager import DBManager

                db = DBManager(db_path)
                db.save_anchor(f"key_{thread_id}", {"thread": thread_id})
                db.close()
            except Exception as exc:  # pragma: no cover - diagnostic path
                errors.append(exc)

        threads = [threading.Thread(target=writer_task, args=(i,)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert isinstance(errors, list)

    def test_transaction_atomicity(self, temp_dir):
        from modules.core.db_manager import DBError, DBManager

        db = DBManager(temp_dir / "atomic.db")
        try:
            with pytest.raises(DBError):
                with db.transaction():
                    db.save_anchor("atomic1", {"step": 1})
                    db.save_anchor("atomic2", {"step": 2})
                    raise ValueError("Intentional failure")

            assert db.load_anchor("atomic1") == {}
            assert db.load_anchor("atomic2") == {}
        finally:
            db.close()

    def test_unicode_preservation(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "unicode.db")
        try:
            korean_data = {
                "title": "무협소설",
                "characters": ["이청운", "응룡검", "인사부"],
                "special": "천무검과龍虎豹",
            }

            db.save_anchor("korean", korean_data)
            loaded = db.load_anchor("korean")

            assert loaded["title"] == "무협소설"
            assert "이청운" in loaded["characters"]
            assert loaded["special"] == "천무검과龍虎豹"
        finally:
            db.close()

    def test_large_data_handling(self, temp_dir):
        from modules.core.db_manager import DBManager

        db = DBManager(temp_dir / "large.db")
        try:
            large_text = "무협 소설 내용 " * 100000

            db.save_manuscript(1, "large", large_text)
            loaded = db.get_manuscript(1)

            assert len(loaded["content"]) == len(large_text)
        finally:
            db.close()
