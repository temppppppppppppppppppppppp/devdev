# Codex Order: E-2 Ruff 전면 정리 + A-2 Optimizer TODO

> **목표**: Ruff 잔여 에러 전량 해소 + stage2_optimizer 스텁 2건 구현
> **주의**: E-2는 148 파일, 2,234건 변경 — **2단계로 분리 실행**

---

## Part 1: E-2 Ruff 전면 정리

### 1-A. Safe auto-fix (2,195건)

`pre-commit run ruff --all-files` 실행 시 자동 수정되는 2,195건.
148 파일에 걸쳐 import 정리, 타입 어노테이션 현대화 등.

**실행:**
```bash
pre-commit run ruff --all-files
```

자동 수정 후 `git diff --stat`로 변경 범위 확인.

**검증:**
```bash
# 자동 수정 후 전체 테스트 통과 확인
set PYTHONIOENCODING=utf-8
pytest tests/ --ignore=tests/test_agents.py --ignore=tests/test_db_manager.py -q
```

> **중요**: auto-fix 후 반드시 테스트를 돌려 regression 없음을 확인.
> Import 정리로 인해 런타임 에러가 발생할 수 있음.

**커밋:**
```
style(ruff): auto-fix 2,195 lint violations across 148 files
```

---

### 1-B. Unsafe-fix (39건, 수동 확인 필요)

`--unsafe-fixes` 옵션이 필요한 39건. 주로:
- **UP038** (28건): `isinstance(x, (A, B))` → `isinstance(x, A | B)` (Python 3.10+ union syntax)
- **UP035** (3건): deprecated import 교체
- 기타 (8건): 확인 필요

**실행:**
```bash
pre-commit run ruff --all-files -- --unsafe-fixes
```

또는 수동으로:
```bash
ruff check --select UP038,UP035 --fix --unsafe-fixes .
```

**검증:** 동일하게 전체 테스트 실행.

> **주의**: unsafe-fix는 의미 변경 가능성 있음. isinstance union 변환은 Python 3.10+ 필요.
> 현재 프로젝트는 Python 3.12이므로 안전.

**커밋:**
```
style(ruff): apply 39 unsafe-fixes (UP038 isinstance union + UP035 deprecated imports)
```

---

## Part 2: A-2 stage2_optimizer TODO 2건

### 2-A. `_build_grant_history()` (L490-504)

**현재:**
```python
for grant in grants:
    history.append({
        "grant": grant,
        "arc": arc_no,
        "from": "알 수 없음"  # TODO: tactical_doc에서 추출
    })
```

**수정:**
```python
for grant in grants:
    # tactical_doc에서 부여자(from) 추출 시도
    _from = "알 수 없음"
    _tactical = arc.get("tactical_doc", "")
    if isinstance(grant, str) and grant in _tactical:
        # grant 키워드 주변에서 "~에게", "~로부터" 패턴 탐색
        _idx = _tactical.find(grant)
        _context = _tactical[max(0, _idx - 50):_idx]
        # 간단한 패턴 매칭: "X가", "X에게서", "X로부터"
        import re
        _match = re.search(r'([가-힣]{2,6})(?:가|에게서|로부터|이|께서)', _context)
        if _match:
            _from = _match.group(1)
    history.append({
        "grant": grant,
        "arc": arc_no,
        "from": _from,
    })
```

### 2-B. `_build_relationship_history()` (L506-509)

**현재:**
```python
def _build_relationship_history(self, prev_arcs: List[Dict]) -> List[Dict]:
    """관계 변화 히스토리 구축"""
    # TODO: 구현
    return []
```

**수정:**
```python
def _build_relationship_history(self, prev_arcs: List[Dict]) -> List[Dict]:
    """관계 변화 히스토리 구축 — state_changes에서 추출."""
    history = []
    for arc in prev_arcs:
        arc_no = arc.get("arc_no", "?")
        state = arc.get("state_changes", {})
        rel_changes = state.get("relationship_changes", [])
        for change in rel_changes:
            if isinstance(change, dict):
                history.append({
                    "arc": arc_no,
                    "npc": change.get("npc", "?"),
                    "change": change.get("change", "?"),
                    "reason": change.get("reason", ""),
                })
            elif isinstance(change, str):
                history.append({
                    "arc": arc_no,
                    "npc": "?",
                    "change": change,
                    "reason": "",
                })
    return history
```

---

## 검증 게이트

```bash
# Gate 1: py_compile
python -m py_compile modules/core/stage2_optimizer.py

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 전체 테스트
set PYTHONIOENCODING=utf-8
pytest tests/ -q

# Gate 4: pre-commit
pre-commit run --all-files
```

---

## 체크리스트

- [ ] E-2 Part 1-A: `pre-commit run ruff --all-files` auto-fix + 테스트 확인
- [ ] E-2 Part 1-A 커밋
- [ ] E-2 Part 1-B: unsafe-fix 39건 + 테스트 확인
- [ ] E-2 Part 1-B 커밋
- [ ] A-2: `_build_grant_history()` TODO 해소
- [ ] A-2: `_build_relationship_history()` TODO 해소
- [ ] A-2 커밋
- [ ] Gate 1-4 전체 통과

> **커밋 순서**: E-2 auto-fix → E-2 unsafe-fix → A-2 optimizer
> 3개 별도 커밋으로 분리 (각각 독립적, rollback 용이)
