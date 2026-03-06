"""스파이크 1: PyInstaller + sqlite-vec 번들 검증.

판정 기준: 이 스크립트가 exe로 번들된 상태에서도
    1. sqlite_vec 로드 성공
    2. vec_version() 쿼리 성공
    3. 벡터 검색 1건 성공
    → "SPIKE-1 PASS" 출력

실패 시 "SPIKE-1 FAIL: <원인>" 출력 후 exit(1).
"""

import sqlite3
import sys


def main() -> None:
    print("=== Spike 1: PyInstaller + sqlite-vec ===", flush=True)

    # ── 1. sqlite_vec import ──────────────────────────────────────────────────
    try:
        import sqlite_vec
    except ImportError as e:
        print(f"SPIKE-1 FAIL: sqlite_vec import error — {e}", flush=True)
        sys.exit(1)

    # ── 2. 확장 로드 ─────────────────────────────────────────────────────────
    try:
        conn = sqlite3.connect(":memory:")
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
    except Exception as e:
        print(f"SPIKE-1 FAIL: load_extension error — {e}", flush=True)
        sys.exit(1)

    # ── 3. vec_version() 확인 ────────────────────────────────────────────────
    try:
        (vec_version,) = conn.execute("SELECT vec_version()").fetchone()
        print(f"sqlite-vec version: {vec_version}", flush=True)
    except Exception as e:
        print(f"SPIKE-1 FAIL: vec_version query error — {e}", flush=True)
        sys.exit(1)

    # ── 4. 가상 테이블 생성 + 벡터 삽입 ─────────────────────────────────────
    try:
        conn.execute("CREATE VIRTUAL TABLE v USING vec0(a float[3])")
        conn.execute(
            "INSERT INTO v(rowid, a) VALUES (1, ?)",
            (sqlite_vec.serialize_float32([1.0, 2.0, 3.0]),),
        )
        conn.execute(
            "INSERT INTO v(rowid, a) VALUES (2, ?)",
            (sqlite_vec.serialize_float32([4.0, 5.0, 6.0]),),
        )
    except Exception as e:
        print(f"SPIKE-1 FAIL: virtual table error — {e}", flush=True)
        sys.exit(1)

    # ── 5. 벡터 검색 1건 ─────────────────────────────────────────────────────
    try:
        row = conn.execute(
            "SELECT rowid, distance FROM v WHERE a MATCH ? AND k = 1",
            (sqlite_vec.serialize_float32([1.0, 2.0, 3.0]),),
        ).fetchone()
        assert row is not None, "No result"
        assert row[0] == 1, f"Expected rowid=1, got {row[0]}"
        print(f"Vector search: rowid={row[0]}, distance={row[1]}", flush=True)
    except Exception as e:
        print(f"SPIKE-1 FAIL: vector search error — {e}", flush=True)
        sys.exit(1)

    print("SPIKE-1 PASS", flush=True)


if __name__ == "__main__":
    main()
