# Codex Order: LM-후순위-1 — Retrospective Lookback 개선 + causal_graph Read 연결

> **목적**: LM-A~I 완료 후 유보된 후순위 2건.
>   1. `RetrospectiveValidator` lookback 하드코딩 5화 → YAML 외부화 + 기본값 10화로 확장.
>   2. `causal_graph` 테이블 Read 메서드 추가 → Stage4 Director MC에 인과 컨텍스트 보조 주입.
> **금지**: 기존 테스트 시그니처 변경. 모델 값 변경. 명세에 없는 기능 추가.
> **출력 보고서**: `docs/2026-03-04/LM-post-1-result.md`

---

## 0) 강제 제약

- 수정 파일: **4개 이하** (`validation_orchestrator.py`, `validation.yaml`, `db_manager.py`, `stage4_post_processor.py`).
- 각 Phase 완료 후 `python -m py_compile <수정파일>` 통과 필수.
- `pytest tests/ -q` 기준선: **3220 passed, 16 skipped, 0 failed**.
- `ruff check modules/ tests/` 위반 0건.

---

## 1) 현재 코드 구조 파악 (수동 검사 필수)

구현 전 아래를 직접 읽어라:

```
파일: modules/validation/validation_orchestrator.py
읽을 범위:
  - RetrospectiveValidator 초기화 블록 (L570~580 근방)
  - _threshold() 또는 _section() 헬퍼 사용 방식 (파일 상단 import 블록)

파일: config/settings/validation.yaml
읽을 범위:
  - retrospective 섹션 전체 (L130~155 근방)

파일: modules/core/db_manager.py
읽을 범위:
  - save_causal_links() (L1739~1755 근방)
  - causal_graph 테이블 DDL (L246~250 근방)
  - get_causal_summary_chain() 바로 아래 (L1706~1715 근방) — Read 메서드 삽입 위치

파일: modules/core/stage4_post_processor.py
읽을 범위:
  - _director_mc_parts 구성 블록 (Director MC advisory 주입 영역)
  - causal_graph dual-write 블록 (L883~888 근방) — Read 호출 위치 파악
```

확인 사항:
- `validation_orchestrator.py:574` 에서 `lookback_episodes=5` 가 **하드코딩**인지 확인
- `validation.yaml` `retrospective.lookback_episodes` 값이 `5` 인지 확인
- `db_manager.py` 에 `get_causal_links_range()` 또는 유사 Read 메서드가 **없는지** 확인
- `stage4_post_processor.py` Director MC 구성 부분에서 causal 데이터를 읽는 코드가 **없는지** 확인

---

## 2) Phase 1 — Retrospective Lookback YAML 외부화 + 10화 확장

### 변경 대상 A: `config/settings/validation.yaml`

```yaml
# Before (L134 근방):
  lookback_episodes: 5          # 최근 N화 대비 비교

# After:
  lookback_episodes: 10         # 최근 N화 대비 비교 (LM-후순위-1: 5→10 확장)
```

### 변경 대상 B: `modules/validation/validation_orchestrator.py`

```python
# Before (L574 근방):
self.retrospective = RetrospectiveValidator(context_obj, lookback_episodes=5)

# After:
_retro_lookback = _settings.get("retrospective", {}).get("lookback_episodes", 10)
self.retrospective = RetrospectiveValidator(context_obj, lookback_episodes=_retro_lookback)
```

**주의**: `_settings` 변수가 이 메서드 스코프에서 이미 사용 가능한지 확인. 없으면 `validation.yaml`을 읽는 기존 헬퍼(`_threshold()` 또는 클래스 속성)를 활용. 새 파일 접근 코드 추가 금지 — 기존 패턴만 따를 것.

---

## 3) Phase 2 — causal_graph Read 메서드 추가

### 변경 대상: `modules/core/db_manager.py`

`save_causal_links()` 바로 아래에 삽입:

```python
def get_recent_causal_links(self, current_ep: int, lookback: int = 10) -> list[dict]:
    """[LM-후순위-1] 최근 N화의 인과 링크 목록 반환.

    Args:
        current_ep: 현재 에피소드 번호 (미포함)
        lookback: 몇 화 뒤돌아볼지

    Returns:
        list[dict]: 인과 링크 dict 목록. 없거나 실패 시 [].
    """
    start_ep = max(1, current_ep - lookback)
    try:
        with self._lock:
            cur = self.cursor.execute(
                "SELECT ep_num, data FROM causal_graph WHERE ep_num >= ? AND ep_num < ? ORDER BY ep_num",
                (start_ep, current_ep),
            )
            results = []
            for row in cur.fetchall():
                try:
                    link = json.loads(row["data"]) if isinstance(row["data"], str) else {}
                    if link:
                        link.setdefault("ep", row["ep_num"])
                        results.append(link)
                except (json.JSONDecodeError, ValueError):
                    continue
            return results
    except Exception as _e:
        logging.debug("[causal_graph] get_recent_causal_links 실패 (비치명): %s", _e)
        return []
```

---

## 4) Phase 3 — Stage4 Director MC 인과 컨텍스트 보조 주입

### 변경 대상: `modules/core/stage4_post_processor.py`

**causal dual-write 블록(L883~888 근방) 이후**에 Read + 주입 블록 추가:

```python
# [LM-후순위-1] causal_graph Read → Director MC 보조 주입
try:
    _causal_links = self.ctx.current_project.db.get_recent_causal_links(next_ep, lookback=10)
    if _causal_links:
        _causal_lines = ["[인과 관계 요약]"]
        for _lk in _causal_links[:8]:  # 최대 8개
            _cause = _lk.get("cause", "") or _lk.get("trigger", "")
            _effect = _lk.get("effect", "") or _lk.get("consequence", "")
            _ep = _lk.get("ep", "?")
            if _cause and _effect:
                _causal_lines.append(f"- ep{_ep}: {_cause} → {_effect}")
        if len(_causal_lines) > 1:
            _director_mc_parts.append("\n".join(_causal_lines))
            logging.debug("[causal_graph] Director MC 인과 컨텍스트 주입: %d건", len(_causal_lines) - 1)
except Exception as _cg_read_err:
    logging.debug("[causal_graph] Director MC 주입 실패 (비치명): %s", _cg_read_err)
```

**주의**:
- `_director_mc_parts` 가 이 스코프에서 사용 가능한지 확인. 없으면 주입 위치를 조정.
- causal_links가 0건이면 아무것도 추가하지 않음 (데이터 없는 프로젝트에서 MC 팽창 방지).
- 기존 `_cg_err` 변수와 이름 충돌 없게 `_cg_read_err` 사용.

---

## 5) Phase 4 — 테스트 추가

파일: `tests/test_lm_post1.py` (신규)

```python
"""[LM-후순위-1] Retrospective lookback YAML 외부화 + causal_graph Read 연결 테스트."""
import json


# ── Phase 1: Retrospective lookback YAML 외부화 ──────────────────────────────

def test_retrospective_lookback_reads_yaml():
    """ValidationOrchestrator가 validation.yaml에서 lookback_episodes를 읽는지 확인."""
    import yaml, pathlib
    val_yaml = pathlib.Path("config/settings/validation.yaml")
    with open(val_yaml, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    lookback = cfg.get("retrospective", {}).get("lookback_episodes", 5)
    assert lookback >= 10, f"lookback_episodes should be >=10, got {lookback}"


def test_retrospective_validator_accepts_lookback():
    """RetrospectiveValidator가 lookback_episodes 인자를 받아 self.lookback에 저장하는지."""
    from unittest.mock import MagicMock
    from modules.validation.retrospective_validator import RetrospectiveValidator

    rv = RetrospectiveValidator(MagicMock(), lookback_episodes=10)
    assert rv.lookback == 10


# ── Phase 2: causal_graph Read 메서드 ────────────────────────────────────────

def test_get_recent_causal_links_empty_db():
    """DB에 데이터 없을 때 빈 리스트 반환."""
    import tempfile, os
    from modules.core.db_manager import DBManager

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    try:
        db = DBManager(tmpdb)
        db.initialize_db()
        result = db.get_recent_causal_links(current_ep=5, lookback=10)
        assert result == [], f"expected [], got {result}"
    finally:
        os.unlink(tmpdb)


def test_get_recent_causal_links_returns_data():
    """저장된 causal_links를 정상 반환하는지 확인."""
    import tempfile, os
    from modules.core.db_manager import DBManager

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    try:
        db = DBManager(tmpdb)
        db.initialize_db()
        links = [
            {"cause": "사업 실패", "effect": "자본 소진", "ep": 3},
            {"cause": "신규 투자", "effect": "자본 회복", "ep": 4},
        ]
        db.save_causal_links(links, current_ep=5)
        result = db.get_recent_causal_links(current_ep=6, lookback=5)
        assert len(result) == 2, f"expected 2, got {len(result)}"
        causes = [r.get("cause") for r in result]
        assert "사업 실패" in causes
    finally:
        os.unlink(tmpdb)


def test_get_recent_causal_links_range_filter():
    """lookback 범위 밖의 링크는 반환하지 않는지 확인."""
    import tempfile, os
    from modules.core.db_manager import DBManager

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    try:
        db = DBManager(tmpdb)
        db.initialize_db()
        old_links = [{"cause": "오래된 사건", "effect": "결과", "ep": 1}]
        new_links = [{"cause": "최근 사건", "effect": "결과", "ep": 10}]
        db.save_causal_links(old_links, current_ep=1)
        db.save_causal_links(new_links, current_ep=10)
        # current_ep=15, lookback=5 → ep 10~14만 포함
        result = db.get_recent_causal_links(current_ep=15, lookback=5)
        causes = [r.get("cause") for r in result]
        assert "최근 사건" in causes
        assert "오래된 사건" not in causes, f"오래된 사건이 포함됨: {result}"
    finally:
        os.unlink(tmpdb)


def test_get_recent_causal_links_malformed_json():
    """malformed JSON row는 skip하고 정상 row만 반환."""
    import tempfile, os, sqlite3
    from modules.core.db_manager import DBManager

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmpdb = f.name
    try:
        db = DBManager(tmpdb)
        db.initialize_db()
        # 정상 link 저장
        db.save_causal_links([{"cause": "정상", "effect": "결과", "ep": 3}], current_ep=3)
        # malformed JSON 직접 삽입
        with db._lock:
            db.cursor.execute("INSERT INTO causal_graph (ep_num, data) VALUES (?, ?)", (4, "NOT_JSON{{{"))
            db.conn.commit()
        result = db.get_recent_causal_links(current_ep=10, lookback=10)
        # malformed는 skip, 정상 1건만 반환
        assert len(result) == 1
        assert result[0].get("cause") == "정상"
    finally:
        os.unlink(tmpdb)
```

---

## 6) 실행 순서

```bash
# Phase 1 완료 후
python -m py_compile modules/validation/validation_orchestrator.py
python -c "
import yaml
with open('config/settings/validation.yaml') as f:
    cfg = yaml.safe_load(f)
print('lookback_episodes:', cfg.get('retrospective', {}).get('lookback_episodes'))
"

# Phase 2 완료 후
python -m py_compile modules/core/db_manager.py

# Phase 3 완료 후
python -m py_compile modules/core/stage4_post_processor.py

# Phase 4 완료 후
pytest tests/test_lm_post1.py -v

# ruff
ruff check modules/validation/validation_orchestrator.py \
  modules/core/db_manager.py \
  modules/core/stage4_post_processor.py \
  tests/test_lm_post1.py

# 전체 회귀
pytest tests/ -q
```

---

## 7) 보고서 형식

출력: `docs/2026-03-04/LM-post-1-result.md`

```markdown
# LM-후순위-1 구현 결과

> 구현일: 2026-03-04

## 수정 내역

| Phase | 파일 | 작업 | 완료 여부 |
|-------|------|------|---------|
| 1 | validation.yaml + validation_orchestrator.py | lookback 5→10 + YAML 외부화 | ✅/❌ |
| 2 | db_manager.py | get_recent_causal_links() 추가 | ✅/❌ |
| 3 | stage4_post_processor.py | Director MC 인과 컨텍스트 보조 주입 | ✅/❌ |
| 4 | test_lm_post1.py | 7개 테스트 추가 | ✅/❌ |

## 검증 결과

- py_compile: 통과/실패
- 신규 테스트: N passed, N failed
- ruff: 위반 N건
- 전체 테스트: N passed, N failed (N skipped)
```

---

## 8) 합격 기준

- 신규 테스트 **7개 전부 PASS**
- 전체 테스트 **3220+ passed, 0 failed**
- ruff 위반 **0건**
- `validation.yaml` `retrospective.lookback_episodes` **≥ 10**
- `validation_orchestrator.py` lookback 하드코딩 **제거 확인**
- `db_manager.py` `get_recent_causal_links()` **존재 확인**
