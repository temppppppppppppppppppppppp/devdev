"""
[Phase 4A] DB Adapter — conn/cursor 직접 접근 차단 래퍼

DBManager를 감싸서 conn/cursor 속성 노출을 차단하고,
Phase 4B/4C에서 기존 코드의 DB 추상화 위반(34건)을 해소하는 어댑터.

사용법:
    adapter = DBAdapter(db_manager)
    adapter.save_anchor("key", data)   # 정상 위임
    adapter.conn                        # AttributeError (차단)
    adapter.raw_execute("DELETE ...")    # 화이트리스트 기반 직접 쿼리
"""

from __future__ import annotations

from typing import Any


class DBAdapter:
    """DBManager 래핑 어댑터 — conn/cursor 직접 노출 차단"""

    # conn/cursor 접근 차단 목록
    _BLOCKED_ATTRS = frozenset({"conn", "cursor", "db_path"})

    # raw_execute 허용 SQL 접두사 (Phase 4B에서 _rollback_episode 등이 사용)
    _RAW_SQL_PREFIXES = (
        "DELETE FROM",
        "UPDATE ",
        "SELECT ",
    )

    def __init__(self, db_manager: Any) -> None:
        # object.__setattr__로 __getattr__ 재귀 회피
        object.__setattr__(self, "_db", db_manager)

    def __getattr__(self, name: str) -> Any:
        if name in self._BLOCKED_ATTRS:
            raise AttributeError(f"DBAdapter: '{name}' 직접 접근 차단됨. DBManager API 메서드를 사용하세요.")
        return getattr(self._db, name)

    # --- Phase 4A 추가 메서드 ---

    def close(self) -> None:
        """DB 연결 안전 종료"""
        self._db.close()

    @property
    def in_transaction(self) -> bool:
        """현재 트랜잭션 진행 여부"""
        return self._db.in_transaction

    def raw_execute(self, sql: str, params: tuple = ()) -> list:
        """화이트리스트 기반 직접 SQL 실행

        _rollback_episode, _wipe_production_data 등에서 사용하는
        직접 DELETE/UPDATE 쿼리를 안전하게 실행.

        Args:
            sql: SQL 문 (DELETE FROM, UPDATE, SELECT만 허용)
            params: 바인드 파라미터

        Returns:
            SELECT의 경우 결과 리스트, 그 외 빈 리스트
        """
        sql_upper = sql.strip().upper()
        if not any(sql_upper.startswith(prefix) for prefix in self._RAW_SQL_PREFIXES):
            raise ValueError(
                f"DBAdapter.raw_execute: 허용되지 않은 SQL — {sql[:50]!r}. 허용 접두사: {self._RAW_SQL_PREFIXES}"
            )
        db = self._db
        with db._lock:
            db.cursor.execute(sql, params)
            if sql_upper.startswith("SELECT"):
                return db.cursor.fetchall()
            return []

    def raw_commit(self) -> None:
        """raw_execute 후 명시적 커밋"""
        self._db.commit()

    def __repr__(self) -> str:
        return f"DBAdapter(db={self._db.db_path!r})"
