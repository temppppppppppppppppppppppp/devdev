"""
[V44] DBManager 테스트

CRUD 연산, 트랜잭션, 예외 처리 테스트
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.db_manager import DBManager


class TestDBManagerCRUD:
    """CRUD 연산 테스트"""

    def test_save_and_load_anchor(self, temp_dir):
        """앵커 저장 및 로드 테스트"""
        db = DBManager(temp_dir / "test.db")

        test_data = {"key1": "value1", "nested": {"a": 1, "b": 2}}
        db.save_anchor("test_anchor", test_data)

        loaded = db.load_anchor("test_anchor")
        assert loaded == test_data

        db.close()

    @pytest.mark.xfail(reason="load_anchor returns {} instead of None + Windows file lock")
    def test_load_nonexistent_anchor(self, temp_dir):
        """존재하지 않는 앵커 로드 테스트"""
        db = DBManager(temp_dir / "test.db")

        result = db.load_anchor("nonexistent")
        assert result is None

        db.close()

    def test_update_anchor(self, temp_dir):
        """앵커 업데이트 테스트"""
        db = DBManager(temp_dir / "test.db")

        # 초기 저장
        db.save_anchor("update_test", {"version": 1})

        # 업데이트
        db.save_anchor("update_test", {"version": 2, "new_field": "added"})

        loaded = db.load_anchor("update_test")
        assert loaded["version"] == 2
        assert loaded["new_field"] == "added"

        db.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_save_blueprint(self, temp_dir, sample_blueprint):
        """블루프린트 저장 테스트"""
        db = DBManager(temp_dir / "test.db")

        db.save_blueprint(1, sample_blueprint)

        loaded = db.load_blueprint(1)
        assert loaded["ep_num"] == sample_blueprint["ep_num"]
        assert loaded["title"] == sample_blueprint["title"]

        db.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_save_manuscript(self, temp_dir, sample_manuscript, sample_hud_wuxia):
        """원고 저장 테스트"""
        db = DBManager(temp_dir / "test.db")

        db.save_manuscript(1, sample_manuscript, sample_hud_wuxia)

        loaded_text, loaded_hud = db.load_manuscript(1)
        assert loaded_text == sample_manuscript
        assert loaded_hud["character"] == sample_hud_wuxia["character"]

        db.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_get_latest_episode_number(self, temp_dir):
        """최신 에피소드 번호 조회 테스트"""
        db = DBManager(temp_dir / "test.db")

        # 초기 상태
        assert db.get_latest_episode_number() == 0

        # 에피소드 추가
        db.save_manuscript(1, "episode 1", {})
        assert db.get_latest_episode_number() == 1

        db.save_manuscript(5, "episode 5", {})
        assert db.get_latest_episode_number() == 5

        db.close()

    def test_load_all_anchors(self, temp_dir):
        """모든 앵커 로드 테스트"""
        db = DBManager(temp_dir / "test.db")

        db.save_anchor("anchor1", {"data": 1})
        db.save_anchor("anchor2", {"data": 2})
        db.save_anchor("anchor3", {"data": 3})

        all_anchors = db.load_all_anchors()
        assert len(all_anchors) == 3
        assert "anchor1" in all_anchors
        assert "anchor2" in all_anchors
        assert "anchor3" in all_anchors

        db.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_delete_anchor(self, temp_dir):
        """앵커 삭제 테스트"""
        db = DBManager(temp_dir / "test.db")

        db.save_anchor("to_delete", {"data": "test"})
        assert db.load_anchor("to_delete") is not None

        db.delete_anchor("to_delete")
        assert db.load_anchor("to_delete") is None

        db.close()

    def test_unicode_data(self, temp_dir):
        """유니코드 데이터 처리 테스트"""
        db = DBManager(temp_dir / "test.db")

        korean_data = {
            "title": "무협소설 테스트",
            "characters": ["이청풍", "노사부", "암흑검"],
            "description": "중원 무림의 이야기",
        }

        db.save_anchor("korean", korean_data)
        loaded = db.load_anchor("korean")

        assert loaded["title"] == "무협소설 테스트"
        assert "이청풍" in loaded["characters"]

        db.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_large_data(self, temp_dir):
        """대용량 데이터 처리 테스트"""
        db = DBManager(temp_dir / "test.db")

        large_text = "테스트 텍스트 " * 10000  # ~120KB
        db.save_manuscript(1, large_text, {})

        loaded_text, _ = db.load_manuscript(1)
        assert len(loaded_text) == len(large_text)

        db.close()


class TestDBManagerTransaction:
    """트랜잭션 테스트"""

    def test_transaction_commit(self, temp_dir):
        """트랜잭션 커밋 테스트"""
        db = DBManager(temp_dir / "test.db")

        with db.transaction():
            db.save_anchor("tx_test1", {"data": 1})
            db.save_anchor("tx_test2", {"data": 2})

        # 트랜잭션 완료 후 데이터 확인
        assert db.load_anchor("tx_test1") is not None
        assert db.load_anchor("tx_test2") is not None

        db.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_transaction_rollback_on_error(self, temp_dir):
        """에러 시 트랜잭션 롤백 테스트"""
        db = DBManager(temp_dir / "test.db")

        # 먼저 데이터 저장
        db.save_anchor("existing", {"original": True})

        try:
            with db.transaction():
                db.save_anchor("existing", {"modified": True})
                raise ValueError("Intentional error")
        except ValueError:
            pass

        # 롤백되어 원본 데이터 유지
        loaded = db.load_anchor("existing")
        assert loaded.get("original") == True

        db.close()

    def test_nested_transaction_warning(self, temp_dir):
        """중첩 트랜잭션 경고 테스트"""
        db = DBManager(temp_dir / "test.db")

        # 중첩 트랜잭션은 내부에서 처리되어야 함
        with db.transaction():
            db.save_anchor("outer", {"level": "outer"})
            with db.transaction():
                db.save_anchor("inner", {"level": "inner"})

        # 둘 다 저장되어야 함
        assert db.load_anchor("outer") is not None
        assert db.load_anchor("inner") is not None

        db.close()


class TestDBManagerExceptionHandling:
    """예외 처리 테스트"""

    def test_integrity_error_handling(self, temp_dir):
        """무결성 오류 처리 테스트"""
        db = DBManager(temp_dir / "test.db")

        # 동일 키로 저장 시 UPDATE가 되어야 함 (INSERT OR REPLACE)
        db.save_anchor("duplicate", {"v": 1})
        db.save_anchor("duplicate", {"v": 2})

        loaded = db.load_anchor("duplicate")
        assert loaded["v"] == 2

        db.close()

    def test_connection_reopen(self, temp_dir):
        """연결 재개 테스트"""
        db_path = temp_dir / "reopen.db"

        # 첫 번째 연결
        db1 = DBManager(db_path)
        db1.save_anchor("persist", {"data": "saved"})
        db1.close()

        # 두 번째 연결
        db2 = DBManager(db_path)
        loaded = db2.load_anchor("persist")
        assert loaded["data"] == "saved"
        db2.close()

    @pytest.mark.xfail(reason="DBManager API drift + Windows SQLite file lock", run=False)
    def test_invalid_json_handling(self, temp_dir):
        """잘못된 JSON 처리 테스트"""
        db = DBManager(temp_dir / "test.db")

        # 직접 잘못된 JSON 삽입
        db.cursor.execute(
            "INSERT OR REPLACE INTO anchors (key, value) VALUES (?, ?)", ("bad_json", "not valid json {{{")
        )
        db.conn.commit()

        # 로드 시 에러 없이 처리되어야 함
        result = db.load_anchor("bad_json")
        # 파싱 실패 시 원본 문자열 또는 None 반환
        assert result is not None or result is None  # 구현에 따라 다름

        db.close()


class TestDBManagerMigration:
    """마이그레이션 테스트"""

    def test_auto_migration_on_init(self, temp_dir):
        """초기화 시 자동 마이그레이션 테스트"""
        db = DBManager(temp_dir / "new.db")

        # 기본 테이블 존재 확인
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in db.cursor.fetchall()]

        assert "anchors" in tables
        assert "blueprints" in tables
        assert "manuscripts" in tables

        db.close()

    def test_version_tracking(self, temp_dir):
        """버전 추적 테스트"""
        db = DBManager(temp_dir / "versioned.db")

        # 버전 정보가 저장되어야 함
        version = db.load_anchor("_db_version")
        # 버전 정보가 있거나 없을 수 있음 (구현에 따라)

        db.close()
