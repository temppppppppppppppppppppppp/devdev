"""[LM-Tier TF-E] HUD Anomaly 파이프라인 — manuscripts hud_snapshot 테스트."""

import pytest

from modules.core.db_manager import DBManager


@pytest.fixture
def db(tmp_path):
    """임시 DB 인스턴스."""
    mgr = DBManager(str(tmp_path / "test.db"))
    yield mgr
    mgr.close()


class TestHUDSnapshotPipeline:
    """manuscripts 테이블 hud_snapshot round-trip 테스트."""

    def test_save_load_roundtrip(self, db):
        """hud_snapshot dict 저장 후 조회 시 동일 dict 반환."""
        hud = {"internal_energy": 500, "realm": "후천초급", "weapon": "목검"}
        db.save_manuscript(ep_num=1, title="1화", content="본문", hud_snapshot=hud)
        result = db.get_manuscript(1)
        assert result is not None
        assert result["hud_snapshot"] == hud

    def test_save_without_hud(self, db):
        """hud_snapshot 미전달 시 빈 dict 반환."""
        db.save_manuscript(ep_num=2, title="2화", content="본문")
        result = db.get_manuscript(2)
        assert result is not None
        assert result["hud_snapshot"] == {}

    def test_hud_json_deserialization(self, db):
        """JSON 역직렬화: 한국어 포함 dict 정상 복원."""
        hud = {"경지": "화경", "내공": 3000, "무기": ["의천검", "도룡도"]}
        db.save_manuscript(ep_num=3, title="3화", content="본문", hud_snapshot=hud)
        result = db.get_manuscript(3)
        assert result["hud_snapshot"]["경지"] == "화경"
        assert result["hud_snapshot"]["내공"] == 3000
        assert len(result["hud_snapshot"]["무기"]) == 2

    def test_hud_none_snapshot(self, db):
        """hud_snapshot=None → 빈 dict 반환."""
        db.save_manuscript(ep_num=4, title="4화", content="본문", hud_snapshot=None)
        result = db.get_manuscript(4)
        assert result["hud_snapshot"] == {}

    def test_hud_empty_dict(self, db):
        """hud_snapshot={} → 빈 dict 반환."""
        db.save_manuscript(ep_num=5, title="5화", content="본문", hud_snapshot={})
        result = db.get_manuscript(5)
        assert result["hud_snapshot"] == {}

    def test_migration_idempotent(self, db):
        """ALTER TABLE 마이그레이션 중복 실행 안전."""
        db2 = DBManager(db.db_path)
        hud = {"test": 1}
        db2.save_manuscript(ep_num=10, title="10화", content="본문", hud_snapshot=hud)
        result = db2.get_manuscript(10)
        assert result["hud_snapshot"] == hud
        db2.close()
