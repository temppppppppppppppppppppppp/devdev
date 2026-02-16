# Codex Order: D-4 Director 선택 추적 + 전략 성과 피드백 루프

> **목표**: Director의 앙상블 선택을 DB에 기록하고, 전략별 승률을 다음 에피소드 생성에 피드백
> **범위**: 1개 파일 수정(db_manager.py) + 1개 파일 수정(stage4_interview_round.py) + 테스트 1개 신규
> **위험도**: 낮음 (기존 로직 변경 없음, 선택 후 INSERT만 추가)

---

## 배경

**현재 문제**: Director가 3개 앙상블 후보(balanced/narrative/tension) 중 하나를 선택하지만,
그 결과가 **어디에도 저장되지 않음**. 어떤 전략이 잘 작동하는지 분석 불가.

**기존 `ab_testing.py`**: Legacy vs V0128 비교 전용 프레임워크 (463줄). 현재 0곳에서 import됨.
앙상블 전략 비교 용도가 아니므로 **그대로 두고**, 별도 추적 메커니즘을 추가.

**해결**:
1. `director_selections` 테이블 → 매 선택 기록
2. 인터뷰 라운드 완료 시 자동 INSERT
3. 전략별 승률 조회 메서드 → 향후 피드백 루프 확장 가능

---

## 설계

```
기존 플로우 (변경 없음):
  Chief Writer → 3 candidates (balanced, narrative, tension)
  → Python 사전 검증
  → Director select_and_judge_ensemble()
  → PASS: 원고 확정  /  REJECT: 재시도

D-4 추가 (선택 직후):
  Director 선택 완료
  → db.save_director_selection(ep_num, round_num, selected, strategy, verdict, score)
  → 비차단 (실패 시 로깅만)
```

---

## 수정/생성 파일

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/core/db_manager.py` | 테이블 생성 + CRUD 3개 메서드 | ~55줄 |
| `modules/core/stage4_interview_round.py` | 선택 기록 호출 (~8줄) | ~8줄 |
| `tests/test_selection_tracker.py` | **신규** — 테스트 8건 | ~100줄 |

---

## 상세 구현

### 1. `modules/core/db_manager.py` — 테이블 + CRUD

#### 1a. 테이블 생성 (기존 `__init__` 내, L338 `self.conn.commit()` 직전에 추가)

**현재 (L328-340):**
```python
        # 14. [D Step 3] 에피소드 만족도 태깅
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_satisfaction_tags (
                ep_num INTEGER PRIMARY KEY,
                ...
            )
        """)

        self.conn.commit()
```

**수정 후:**
```python
        # 14. [D Step 3] 에피소드 만족도 태깅
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS episode_satisfaction_tags (
                ep_num INTEGER PRIMARY KEY,
                ...
            )
        """)

        # 15. [D-4] Director 앙상블 선택 기록
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS director_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ep_num INTEGER NOT NULL,
                round_num INTEGER NOT NULL,
                selected_label TEXT NOT NULL,
                selected_strategy TEXT,
                verdict TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                selection_reason TEXT,
                candidate_count INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_director_selections_ep "
            "ON director_selections(ep_num)"
        )

        self.conn.commit()
```

#### 1b. CRUD 메서드 (NPC history 섹션 뒤, `episode_sentence_hashes` 섹션 전에 추가)

```python
    # --- [D-4] Director 앙상블 선택 기록 ---

    def save_director_selection(
        self,
        ep_num: int,
        round_num: int,
        selected_label: str,
        selected_strategy: str,
        verdict: str,
        score: int = 0,
        selection_reason: str = "",
        candidate_count: int = 3,
    ) -> None:
        """[D-4] Director의 앙상블 선택 결과를 기록."""
        with self._lock:
            self.cursor.execute(
                "INSERT INTO director_selections "
                "(ep_num, round_num, selected_label, selected_strategy, verdict, score, "
                "selection_reason, candidate_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (ep_num, round_num, selected_label, selected_strategy, verdict, score,
                 selection_reason[:200] if selection_reason else "", candidate_count),
            )
            if not self.conn.in_transaction:
                self.conn.commit()

    def get_strategy_win_rates(self, lookback: int = 20) -> dict:
        """[D-4] 최근 N건의 PASS 선택에서 전략별 승률 조회.

        Returns:
            {"balanced": 0.45, "narrative": 0.30, "tension": 0.25, "total": 20}
        """
        with self._lock:
            cur = self.cursor.execute(
                "SELECT selected_strategy, COUNT(*) as cnt "
                "FROM director_selections "
                "WHERE verdict = 'PASS' AND selected_strategy IS NOT NULL "
                "ORDER BY id DESC LIMIT ?",
                (lookback,),
            )
            rows = cur.fetchall()

        total = sum(r["cnt"] for r in rows)
        if total == 0:
            return {"total": 0}

        result = {"total": total}
        for row in rows:
            strategy = row["selected_strategy"]
            if strategy:
                result[strategy] = round(row["cnt"] / total, 2)
        return result

    def get_recent_selections(self, ep_num: int, lookback: int = 10) -> list:
        """[D-4] 최근 선택 이력 조회 (최신순)."""
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, round_num, selected_strategy, verdict, score "
                "FROM director_selections "
                "WHERE ep_num < ? "
                "ORDER BY id DESC LIMIT ?",
                (ep_num, lookback),
            )
            return [dict(row) for row in cur.fetchall()]
```

---

### 2. `modules/core/stage4_interview_round.py` — 선택 기록 호출

Director 판정 로깅 직후, PASS/REJECT 분기 직전에 삽입.

**현재 (L500-508):**
```python
        selected = director_result.get("selected", "A")
        verdict = director_result.get("verdict", "REJECT")
        score = director_result.get("score", 0)
        reason = director_result.get("selection_reason", "")

        self.ctx.ui.log(f"   📊 Director 판정: {verdict} (점수: {score}, 선택: 후보 {selected})")
        self.ctx.ui.log(f"      └─ 사유: {reason[:80]}...")

        if verdict == "PASS":
```

**수정 후:**
```python
        selected = director_result.get("selected", "A")
        verdict = director_result.get("verdict", "REJECT")
        score = director_result.get("score", 0)
        reason = director_result.get("selection_reason", "")

        self.ctx.ui.log(f"   📊 Director 판정: {verdict} (점수: {score}, 선택: 후보 {selected})")
        self.ctx.ui.log(f"      └─ 사유: {reason[:80]}...")

        # [D-4] Director 선택 기록
        try:
            _sel_candidate = director_result.get("selected_candidate", {})
            _sel_strategy = _sel_candidate.get("strategy_name", "") or _sel_candidate.get("strategy", "")
            self.ctx.current_project.db.save_director_selection(
                ep_num=next_ep,
                round_num=round_num,
                selected_label=selected,
                selected_strategy=_sel_strategy,
                verdict=verdict,
                score=score,
                selection_reason=reason,
                candidate_count=len(candidates) if candidates else 0,
            )
        except Exception as e:
            logging.warning(f"[D-4] Director 선택 기록 실패 (비차단): {e!s:.100}")

        if verdict == "PASS":
```

> **핵심**: try/except 비차단. DB 기록 실패해도 파이프라인 중단 안 됨.
> `selected_candidate`에서 `strategy_name` 또는 `strategy` 필드 추출.

---

### 3. `modules/core/db_manager.py` — `reset_after()` 확장

`director_selections`도 롤백 시 정리.

**현재 reset_after() 내 (D-2에서 추가한 3줄 뒤):**
```python
    # [D-2] 만족도 태그 롤백 (Phase D)
    self.cursor.execute("DELETE FROM episode_satisfaction_tags WHERE ep_num >= ?", (target_ep,))
```

**그 뒤에 추가:**
```python
    # [D-4] Director 선택 기록 롤백
    self.cursor.execute("DELETE FROM director_selections WHERE ep_num >= ?", (target_ep,))
```

**`get_rollback_impact()`에도 추가:**

기존 `satisfaction_tags` 조회 뒤에:
```python
    # Director 선택 기록
    cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM director_selections WHERE ep_num >= ?", (target_ep,))
    impact["director_selections"] = cur.fetchone()["cnt"]
```

---

## 테스트

### `tests/test_selection_tracker.py` (신규, ~100줄)

```python
"""[D-4] Director 선택 추적 테스트."""
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager


@pytest.fixture
def db(tmp_path):
    return DBManager(tmp_path / "test_selection.db")


class TestDirectorSelectionsTable:
    """director_selections 테이블 기본 CRUD."""

    def test_save_and_retrieve(self, db):
        """선택 기록 저장 후 조회."""
        db.save_director_selection(
            ep_num=5, round_num=0, selected_label="B",
            selected_strategy="narrative", verdict="PASS",
            score=85, selection_reason="서사 밀도 우수",
        )
        rows = db.get_recent_selections(ep_num=10, lookback=5)
        assert len(rows) == 1
        assert rows[0]["selected_strategy"] == "narrative"
        assert rows[0]["verdict"] == "PASS"
        assert rows[0]["score"] == 85

    def test_multiple_rounds_recorded(self, db):
        """같은 에피소드 여러 라운드 기록."""
        db.save_director_selection(5, 0, "A", "balanced", "REJECT", 45, "길이 부족")
        db.save_director_selection(5, 1, "C", "tension", "PASS", 78, "재시도 후 합격")
        rows = db.get_recent_selections(ep_num=10, lookback=10)
        assert len(rows) == 2

    def test_reason_truncated(self, db):
        """selection_reason이 200자로 잘림."""
        long_reason = "A" * 300
        db.save_director_selection(5, 0, "A", "balanced", "PASS", 80, long_reason)
        rows = db.get_recent_selections(ep_num=10)
        # 정상 저장 확인 (에러 없음)
        assert len(rows) == 1


class TestStrategyWinRates:
    """전략별 승률 조회."""

    def test_single_strategy_100_percent(self, db):
        """하나의 전략만 PASS면 100%."""
        for i in range(5):
            db.save_director_selection(i + 1, 0, "A", "balanced", "PASS", 80)
        rates = db.get_strategy_win_rates(lookback=10)
        assert rates["balanced"] == 1.0
        assert rates["total"] == 5

    def test_mixed_strategies(self, db):
        """여러 전략 PASS 시 비율 계산."""
        db.save_director_selection(1, 0, "A", "balanced", "PASS", 80)
        db.save_director_selection(2, 0, "B", "narrative", "PASS", 75)
        db.save_director_selection(3, 0, "C", "tension", "PASS", 90)
        db.save_director_selection(4, 0, "A", "balanced", "PASS", 85)
        rates = db.get_strategy_win_rates(lookback=10)
        assert rates["total"] == 4
        assert rates["balanced"] == 0.5  # 2/4

    def test_reject_excluded(self, db):
        """REJECT는 승률 계산에서 제외."""
        db.save_director_selection(1, 0, "A", "balanced", "PASS", 80)
        db.save_director_selection(2, 0, "B", "narrative", "REJECT", 40)
        rates = db.get_strategy_win_rates(lookback=10)
        assert rates["total"] == 1
        assert "narrative" not in rates

    def test_empty_db_returns_zero_total(self, db):
        """빈 DB에서 total=0."""
        rates = db.get_strategy_win_rates()
        assert rates["total"] == 0


class TestRollbackIncludesSelections:
    """롤백 시 director_selections도 정리."""

    def test_reset_after_deletes_selections(self, db):
        """target_ep 이상 선택 기록 삭제."""
        db.save_director_selection(3, 0, "A", "balanced", "PASS", 80)
        db.save_director_selection(5, 0, "B", "narrative", "PASS", 75)
        db.reset_after(4)
        rows = db.get_recent_selections(ep_num=10)
        assert len(rows) == 1  # ep 3만 남음
        assert rows[0]["ep_num"] == 3

    def test_rollback_impact_includes_selections(self, db):
        """get_rollback_impact에 director_selections 포함."""
        db.save_director_selection(5, 0, "A", "balanced", "PASS", 80)
        impact = db.get_rollback_impact(4)
        assert "director_selections" in impact
        assert impact["director_selections"] == 1
```

---

## 파일별 변경 요약

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/core/db_manager.py` | 테이블 + save/get_win_rates/get_recent + reset_after/rollback_impact 확장 | ~55줄 |
| `modules/core/stage4_interview_round.py` | Director 선택 기록 호출 | ~8줄 |
| `tests/test_selection_tracker.py` | 신규 테스트 8건 | ~100줄 |

**총 프로덕션 코드**: ~63줄 추가
**총 테스트**: 8건

---

## 주의사항

1. **비차단 기록** — `save_director_selection()` 호출이 실패해도 파이프라인 중단 없음.
2. **strategy_name 추출** — `selected_candidate`의 `strategy_name` 또는 `strategy` 필드. Chief Writer가 반환하는 candidate dict에 `strategy_name` 키로 들어있음 (`chief_writer.py` L289-293).
3. **selection_reason 200자 제한** — DB 공간 절약 + 불필요한 장문 방지.
4. **reset_after() 확장** — D-2 패턴과 동일. `director_selections` 1줄 추가.
5. **get_strategy_win_rates() SQL** — `ORDER BY id DESC LIMIT ?`로 최근 N건만 집계. 전체 스캔 안 함.
6. **`ab_testing.py` 미변경** — 기존 파일은 그대로 유지 (별도 용도의 독립 도구).

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/db_manager.py
python -m py_compile modules/core/stage4_interview_round.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_selection_tracker.py -v

# Gate 4: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 5: pre-commit
pre-commit run --files modules/core/db_manager.py modules/core/stage4_interview_round.py tests/test_selection_tracker.py
```

---

## 체크리스트

- [ ] `director_selections` 테이블 + 인덱스 생성
- [ ] `save_director_selection()` 메서드
- [ ] `get_strategy_win_rates()` 메서드
- [ ] `get_recent_selections()` 메서드
- [ ] `reset_after()` 1줄 추가
- [ ] `get_rollback_impact()` 1줄 추가
- [ ] `stage4_interview_round.py` Director 선택 기록 호출 (~8줄)
- [ ] 테스트 8건 전체 통과
- [ ] Gate 1-5 전체 통과
- [ ] 커밋: `feat(tracking): add Director selection tracking with strategy win rates (D-4)`
