# Codex Order: D-2 에피소드 롤백 NPC 되감기 + 안전장치

> **목표**: `auto_backtrack_v35()` 호출 시 NPC 이력·만족도·문장해시·WorldState·FactLedger도 함께 롤백
> **범위**: 3개 파일 수정 + 테스트 1개 신규
> **위험도**: 중 (DB 삭제 로직 변경 — 기존 `reset_after()` 확장)

---

## 배경

현재 `auto_backtrack_v35()` → `reset_project()` → `db.reset_after(target_ep)` 체인은:

**정리되는 것 (9개 테이블):**
- blueprints, state_logs, causal_graph, manuscripts, martial_tracker
- episode_bibles, sync_status, karma_status, seeds

**정리 안 되는 것 (5개):**
- `npc_history` — NPC 변경 이력 (Phase 3-5A)
- `episode_sentence_hashes` — 문장 핑거프린트 (Phase 3-B)
- `episode_satisfaction_tags` — 만족도 태그 (Phase D Step 3)
- `anchors` 중 `world_state` — 세계 상태 문서 (V68)
- `anchors` 중 `fact_ledger` — 팩트 원장 (V68)

→ 롤백 후 NPC가 "아직 안 죽은" 화로 돌아갔는데 `npc_history`에 사망 기록 남아 있으면
  연속성 검증이 오동작. WorldState에 dead_npcs 잔존하면 프롬프트에 잘못된 정보 주입.

---

## 수정 내용

### 1. `modules/core/db_manager.py` — `reset_after()` 확장

**현재 (L1115-1131):**
```python
def reset_after(self, target_ep) -> None:
    """전체 테이블 리셋 및 롤백"""
    tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]
    for tbl in tables:
        self.cursor.execute(f"DELETE FROM {tbl} WHERE ep_num >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM episode_bibles WHERE ep_num >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM seeds WHERE planted_ep >= ?", (target_ep,))
    # [V70] 누적 Bible 캐시 무효화
    invalidate_eps = [k for k in self._cumulative_bible_cache if k >= target_ep]
    for k in invalidate_eps:
        del self._cumulative_bible_cache[k]
    # 로어는 시간 개념이 모호하므로 유지하거나 별도 정책 필요 (여기선 유지)
    self.conn.commit()
    self.cursor.execute("VACUUM")
```

**수정 후:**
```python
def reset_after(self, target_ep) -> None:
    """전체 테이블 리셋 및 롤백"""
    tables = ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]
    for tbl in tables:
        self.cursor.execute(f"DELETE FROM {tbl} WHERE ep_num >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM episode_bibles WHERE ep_num >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM sync_status WHERE ep_num >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM karma_status WHERE last_updated_ep >= ?", (target_ep,))
    self.cursor.execute("DELETE FROM seeds WHERE planted_ep >= ?", (target_ep,))

    # [D-2] NPC 이력 롤백 (Phase 3-5A)
    self.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))

    # [D-2] 문장 핑거프린트 롤백 (Phase 3-B)
    self.cursor.execute("DELETE FROM episode_sentence_hashes WHERE ep_num >= ?", (target_ep,))

    # [D-2] 만족도 태그 롤백 (Phase D)
    self.cursor.execute("DELETE FROM episode_satisfaction_tags WHERE ep_num >= ?", (target_ep,))

    # [V70] 누적 Bible 캐시 무효화
    invalidate_eps = [k for k in self._cumulative_bible_cache if k >= target_ep]
    for k in invalidate_eps:
        del self._cumulative_bible_cache[k]
    # 로어는 시간 개념이 모호하므로 유지하거나 별도 정책 필요 (여기선 유지)
    self.conn.commit()
    self.cursor.execute("VACUUM")
```

> 추가된 3줄만. 기존 동작 100% 보존.

---

### 2. `modules/core/db_manager.py` — `get_rollback_impact()` 신규 메서드

`reset_after()` 바로 아래에 추가 (L1132 부근):

```python
def get_rollback_impact(self, target_ep: int) -> dict:
    """[D-2] 롤백 영향 범위 조회 — 삭제될 데이터 건수 미리보기.

    Args:
        target_ep: 롤백 기준 에피소드 번호 (이 번호 이상이 삭제됨)

    Returns:
        dict: {table_name: count} 형태의 영향 범위
    """
    impact = {}
    # 기존 테이블
    for tbl in ["blueprints", "state_logs", "causal_graph", "manuscripts", "martial_tracker"]:
        cur = self.cursor.execute(f"SELECT COUNT(*) as cnt FROM {tbl} WHERE ep_num >= ?", (target_ep,))  # noqa: S608
        impact[tbl] = cur.fetchone()["cnt"]
    # episode_bibles
    cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM episode_bibles WHERE ep_num >= ?", (target_ep,))
    impact["episode_bibles"] = cur.fetchone()["cnt"]
    # NPC 이력
    cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM npc_history WHERE episode_no >= ?", (target_ep,))
    impact["npc_history"] = cur.fetchone()["cnt"]
    # 문장 해시
    cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM episode_sentence_hashes WHERE ep_num >= ?", (target_ep,))
    impact["sentence_hashes"] = cur.fetchone()["cnt"]
    # 만족도 태그
    cur = self.cursor.execute("SELECT COUNT(*) as cnt FROM episode_satisfaction_tags WHERE ep_num >= ?", (target_ep,))
    impact["satisfaction_tags"] = cur.fetchone()["cnt"]

    return impact
```

---

### 3. `modules/core/world_state.py` — `rollback_to()` 신규 메서드

클래스 맨 아래에 추가:

```python
def rollback_to(self, target_ep: int) -> None:
    """[D-2] 특정 에피소드 이전 상태로 초기화 후 저장.

    WorldState는 누적 스냅샷이므로 부분 되감기 불가능.
    초기 상태로 리셋하고, target_ep 미만의 state_changes를 재적용하는 것이 정석이나
    state_changes 원본이 DB에 없으므로 초기화가 유일한 안전 방법.

    Args:
        target_ep: 롤백 기준 에피소드 번호
    """
    import json as _json

    _logger.warning(
        "[D-2] WorldState 롤백: ep %d 이후 데이터 초기화 (이전 last_updated_ep=%d)",
        target_ep,
        self._state.get("last_updated_ep", 0),
    )
    self._state = _json.loads(_json.dumps(self._INIT_STATE))
    self.save()
```

---

### 4. `modules/core/fact_ledger.py` — `rollback_to()` 신규 메서드

클래스 맨 아래에 추가:

```python
def rollback_to(self, target_ep: int) -> None:
    """[D-2] 특정 에피소드 이전 상태로 초기화 후 저장.

    FactLedger는 누적 원장이므로 부분 되감기 불가능.
    초기화 후 저장하여 다음 화 생성 시 재구축.

    Args:
        target_ep: 롤백 기준 에피소드 번호
    """
    _logger.warning(
        "[D-2] FactLedger 롤백: ep %d 이후 데이터 초기화 (이전 last_updated_ep=%d)",
        target_ep,
        self._ledger.get("last_updated_ep", 0),
    )
    self._ledger = self._empty_ledger()
    self.save()
```

---

### 5. `modules/core/project_manager.py` — `auto_backtrack_v35()` 확장

**현재 (L843-873):**
```python
def auto_backtrack_v35(self, error_report, memory):
    ...
    try:
        match = re.search(r"(\d+)\s*화", error_report)
        origin_ep = int(match.group(1)) if match else self.get_latest_episode_number()
        current_ep = self.get_latest_episode_number()
        target_ep = max(origin_ep, current_ep - 3)

        logging.info(f"🚑 [V35 Backtrack] 제 {target_ep}화로 인과율을 강제 되감기합니다.")

        self.reset_project(target_ep)

        if memory and hasattr(memory, "delete_episodes_from"):
            deleted = memory.delete_episodes_from(target_ep)
            logging.info(f"🌌 [Memory] 제 {target_ep}화 이후 벡터 기억 {deleted}건 소거")

        return target_ep
    except Exception as e:
        logging.warning(f"🚨 [Backtrack Error] 자동 되감기 실패: {e}")
        return None
```

**수정 후:**
```python
def auto_backtrack_v35(self, error_report, memory, *, world_state=None, fact_ledger=None):
    """
    [V35.5] 논리 모순이 발생한 '인과의 기점'을 찾아 자동 되감기(Rewind) 수행
    - Analyst의 진단 보고서를 바탕으로 물리적 DB와 파일 소거 실행

    Args:
        error_report: Analyst 진단 보고서
        memory: VecMemory 인스턴스 (벡터 기억 소거용)
        world_state: WorldStateManager 인스턴스 (선택, 있으면 롤백)
        fact_ledger: FactLedger 인스턴스 (선택, 있으면 롤백)
    """
    try:
        # 에러 메시지 내의 화수 패턴 검색 (예: "제 12화부터 설정 오류")
        match = re.search(r"(\d+)\s*화", error_report)
        origin_ep = int(match.group(1)) if match else self.get_latest_episode_number()

        # 너무 과거로 가는 것 방지 가드 (최대 3화 전까지만 자동 허용)
        current_ep = self.get_latest_episode_number()
        target_ep = max(origin_ep, current_ep - 3)

        # [D-2] 영향 범위 로깅
        impact = self.db.get_rollback_impact(target_ep)
        total = sum(impact.values())
        logging.info(f"🚑 [V35 Backtrack] 제 {target_ep}화로 되감기 (삭제 대상: {total}건)")
        for tbl, cnt in impact.items():
            if cnt > 0:
                logging.info(f"  - {tbl}: {cnt}건")

        # 기존: DB + 물리 파일 삭제
        self.reset_project(target_ep)

        # 벡터 DB 기억 소거
        if memory and hasattr(memory, "delete_episodes_from"):
            deleted = memory.delete_episodes_from(target_ep)
            logging.info(f"🌌 [Memory] 제 {target_ep}화 이후 벡터 기억 {deleted}건 소거")

        # [D-2] WorldState 롤백
        if world_state and hasattr(world_state, "rollback_to"):
            world_state.rollback_to(target_ep)
            logging.info(f"🌍 [WorldState] 세계 상태 초기화 완료")

        # [D-2] FactLedger 롤백
        if fact_ledger and hasattr(fact_ledger, "rollback_to"):
            fact_ledger.rollback_to(target_ep)
            logging.info(f"📒 [FactLedger] 팩트 원장 초기화 완료")

        return target_ep
    except Exception as e:
        logging.warning(f"🚨 [Backtrack Error] 자동 되감기 실패: {e}")
        return None
```

> **주요 변경**:
> 1. `world_state`, `fact_ledger` 키워드 인자 추가 (기존 호출 100% 호환)
> 2. `get_rollback_impact()` 호출하여 영향 범위 로깅
> 3. WorldState/FactLedger `rollback_to()` 호출 (있으면)

---

## 테스트

### `tests/test_rollback_npc.py` (신규, ~120줄)

```python
"""[D-2] 에피소드 롤백 NPC 되감기 테스트."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from modules.core.db_manager import DBManager


@pytest.fixture
def db(tmp_path):
    """In-memory DB for rollback tests."""
    _db = DBManager(tmp_path / "test_rollback.db")
    return _db


class TestResetAfterNpcHistory:
    """reset_after()가 npc_history도 정리하는지 확인."""

    def test_npc_history_deleted_after_target_ep(self, db):
        """target_ep 이상의 NPC 이력이 삭제됨."""
        db.insert_npc_change("노사부", 3, 1, "status", "alive", "dead", "arc")
        db.insert_npc_change("흑풍", 5, 1, "personality", "냉정", "분노", "arc")
        db.insert_npc_change("이청풍", 2, 1, "skill", "", "검술", "arc")

        db.reset_after(4)

        # ep 5 기록은 삭제, ep 2/3은 유지
        assert len(db.get_npc_history("흑풍")) == 0
        assert len(db.get_npc_history("노사부")) == 1  # ep 3 유지
        assert len(db.get_npc_history("이청풍")) == 1  # ep 2 유지

    def test_npc_history_all_deleted_when_target_ep_1(self, db):
        """target_ep=1이면 전체 NPC 이력 삭제."""
        db.insert_npc_change("노사부", 1, 1, "status", "alive", "dead", "arc")
        db.insert_npc_change("흑풍", 2, 1, "role", "적", "동맹", "arc")

        db.reset_after(1)

        assert len(db.get_npc_history("노사부")) == 0
        assert len(db.get_npc_history("흑풍")) == 0


class TestResetAfterSentenceHashes:
    """reset_after()가 문장 해시도 정리하는지 확인."""

    def test_sentence_hashes_deleted_after_target_ep(self, db):
        """target_ep 이상의 문장 해시가 삭제됨."""
        db.store_sentence_hashes(3, [("hash_a", "문장A")])
        db.store_sentence_hashes(5, [("hash_b", "문장B")])

        db.reset_after(4)

        assert len(db.get_sentence_hashes(3)) == 1  # 유지
        assert len(db.get_sentence_hashes(5)) == 0  # 삭제


class TestResetAfterSatisfactionTags:
    """reset_after()가 만족도 태그도 정리하는지 확인."""

    def test_satisfaction_tags_deleted_after_target_ep(self, db):
        """target_ep 이상의 만족도 태그가 삭제됨."""
        db.save_satisfaction_tags(3, {"frustration": 0.2, "reward": 0.8})
        db.save_satisfaction_tags(5, {"frustration": 0.5, "reward": 0.5})

        db.reset_after(4)

        assert db.get_satisfaction_tags(3) is not None  # 유지
        assert db.get_satisfaction_tags(5) is None  # 삭제


class TestGetRollbackImpact:
    """get_rollback_impact() 영향 범위 조회."""

    def test_returns_correct_counts(self, db):
        """각 테이블별 삭제 대상 건수가 정확."""
        # 데이터 삽입
        db.insert_npc_change("노사부", 3, 1, "status", "alive", "dead", "arc")
        db.insert_npc_change("흑풍", 5, 1, "personality", "냉정", "분노", "arc")
        db.store_sentence_hashes(5, [("hash_a", "문장A")])

        impact = db.get_rollback_impact(4)

        assert impact["npc_history"] == 1  # ep 5만
        assert impact["sentence_hashes"] == 1
        assert impact["manuscripts"] == 0  # 없음

    def test_empty_db_returns_all_zeros(self, db):
        """빈 DB에서 모든 건수가 0."""
        impact = db.get_rollback_impact(1)
        assert all(v == 0 for v in impact.values())


class TestWorldStateRollback:
    """WorldStateManager.rollback_to() 테스트."""

    def test_rollback_resets_to_init_state(self, db):
        from modules.core.world_state import WorldStateManager

        ws = WorldStateManager(db)
        ws.update_from_state_changes(5, {
            "npc_deaths": [{"name": "노사부", "cause": "전투"}],
        })
        ws.save()
        assert "노사부" in ws._state["dead_npcs"]

        ws.rollback_to(3)

        assert ws._state["dead_npcs"] == {}
        assert ws._state["last_updated_ep"] == 0


class TestFactLedgerRollback:
    """FactLedger.rollback_to() 테스트."""

    def test_rollback_resets_to_empty_ledger(self, db):
        from modules.core.fact_ledger import FactLedger

        fl = FactLedger(db)
        fl.update_from_state_changes(5, {
            "npc_deaths": [{"name": "노사부", "cause": "전투"}],
        })
        fl.save()
        assert "노사부" in fl._ledger.get("characters", {})

        fl.rollback_to(3)

        assert fl._ledger["characters"] == {}
        assert fl._ledger["last_updated_ep"] == 0


class TestAutoBacktrackIntegration:
    """auto_backtrack_v35() 통합 테스트."""

    def test_backtrack_calls_world_state_rollback(self, db):
        """world_state 인자 전달 시 rollback_to 호출."""
        from modules.core.project_manager import ProjectManager

        pm = ProjectManager.__new__(ProjectManager)
        pm.db = db
        pm.paths = MagicMock()
        pm.paths.drafts.exists.return_value = False

        mock_ws = MagicMock()
        mock_ws.rollback_to = MagicMock()
        mock_fl = MagicMock()
        mock_fl.rollback_to = MagicMock()

        # 최근 에피소드 5화 설정
        db.save_manuscript(5, "테스트", "내용" * 500)

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
        """world_state/fact_ledger 미전달 시에도 정상 동작 (기존 호환)."""
        from modules.core.project_manager import ProjectManager

        pm = ProjectManager.__new__(ProjectManager)
        pm.db = db
        pm.paths = MagicMock()
        pm.paths.drafts.exists.return_value = False

        db.save_manuscript(5, "테스트", "내용" * 500)

        result = pm.auto_backtrack_v35("제 4화부터 설정 오류", memory=None)

        assert result is not None  # 기존처럼 정상 동작
```

---

## 파일별 변경 요약

| 파일 | 변경 | 규모 |
|------|------|------|
| `modules/core/db_manager.py` | `reset_after()` +3줄, `get_rollback_impact()` 신규 ~25줄 | ~28줄 |
| `modules/core/world_state.py` | `rollback_to()` 신규 ~15줄 | ~15줄 |
| `modules/core/fact_ledger.py` | `rollback_to()` 신규 ~12줄 | ~12줄 |
| `modules/core/project_manager.py` | `auto_backtrack_v35()` 확장 ~15줄 | ~15줄 |
| `tests/test_rollback_npc.py` | 신규 테스트 11건 | ~120줄 |

**총 프로덕션 코드**: ~70줄 추가
**총 테스트**: 11건

---

## 주의사항

1. **WorldState/FactLedger 롤백은 초기화** — 부분 되감기가 아닌 전체 초기화. 이유: state_changes 원본이 별도 저장되지 않으므로 재구축 불가. 다음 화 생성 시 자연스럽게 재구축됨.
2. **`auto_backtrack_v35()` 시그니처 변경** — 키워드 인자 추가이므로 기존 호출(`error_report, memory` 2개만)은 100% 호환.
3. **`get_rollback_impact()` SQL 인젝션 방어** — 테이블 이름이 하드코딩 리스트이므로 안전. `# noqa: S608` 주석 추가.
4. **`reset_after()` 추가 3줄 순서** — 기존 DELETE 블록 바로 아래, `_cumulative_bible_cache` 무효화 전에 배치.

---

## 검증 게이트

```bash
# Gate 1: py_compile (변경 파일)
python -m py_compile modules/core/db_manager.py
python -m py_compile modules/core/world_state.py
python -m py_compile modules/core/fact_ledger.py
python -m py_compile modules/core/project_manager.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_rollback_npc.py -v

# Gate 4: 기존 테스트 회귀 없음
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 5: pre-commit
pre-commit run --files modules/core/db_manager.py modules/core/world_state.py modules/core/fact_ledger.py modules/core/project_manager.py tests/test_rollback_npc.py
```

---

## 체크리스트

- [ ] `reset_after()` 3줄 추가 (npc_history, sentence_hashes, satisfaction_tags)
- [ ] `get_rollback_impact()` 신규 메서드 추가
- [ ] `WorldStateManager.rollback_to()` 신규 메서드 추가
- [ ] `FactLedger.rollback_to()` 신규 메서드 추가
- [ ] `auto_backtrack_v35()` 확장 (world_state, fact_ledger 파라미터 + impact 로깅)
- [ ] 테스트 11건 전체 통과
- [ ] Gate 1-5 전체 통과
- [ ] 커밋: `feat(rollback): add NPC history rewind + WorldState/FactLedger reset on backtrack (D-2)`
