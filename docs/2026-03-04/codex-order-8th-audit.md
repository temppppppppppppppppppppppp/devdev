# Codex Order: 8차 전수조사

> **목적**: LM-post-1 변경 후속 검증 + LM-E/F/D (flashback/info_paradox/relationship) 예외 범위 보강.
>   7차에서 B/C/D 3파일 패치 완료 — 동일 패턴의 잔여 3파일 마무리.
> **금지**: 모델 값 변경. 기존 테스트 시그니처 변경. 명세에 없는 신기능 추가.
> **출력 보고서**: `docs/2026-03-04/8th-audit-result.md`

---

## 0) 강제 제약

- 각 패치 후 즉시 `python -m py_compile <수정파일>` 통과 필수.
- `pytest tests/ -q` 기준선: **LM-post-1 완료 후 전체 passed 수, 0 failed**.
- `ruff check modules/ tests/` 위반 0건 유지.

---

## 1) 감사 대상 파일 (우선순위 순)

### A 그룹 — LM-post-1 후속 검증 (코드 수정 없음, 확인만)

LM-post-1에서 변경한 두 경로가 올바르게 배선되었는지 수동 확인.

| 파일 | 확인 포인트 |
|------|-----------|
| `modules/validation/validation_orchestrator.py` | `lookback_episodes=5` 하드코딩이 YAML 읽기로 교체되었는지 |
| `modules/core/stage4_post_processor.py` | `get_recent_causal_links()` 호출 + `_director_mc_parts` 주입 블록 존재 여부 |
| `modules/core/db_manager.py` | `get_recent_causal_links()` 메서드 시그니처 + 비치명 except 확인 |

**런타임 확인**:

```bash
python -c "
import yaml
with open('config/settings/validation.yaml') as f:
    cfg = yaml.safe_load(f)
lookback = cfg.get('retrospective', {}).get('lookback_episodes', -1)
print('[A] retrospective.lookback_episodes:', lookback)
assert lookback >= 10, f'FAIL: expected >=10, got {lookback}'
print('[A] PASS')
"
```

```bash
python -c "
import tempfile, os
from modules.core.db_manager import DBManager
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    tmpdb = f.name
try:
    db = DBManager(tmpdb)
    db.initialize_db()
    result = db.get_recent_causal_links(current_ep=5, lookback=10)
    print('[A] get_recent_causal_links(empty):', result)
    assert result == [], f'expected [], got {result}'
    print('[A] PASS')
finally:
    os.unlink(tmpdb)
"
```

A그룹은 코드 변경 없음. 검증 실패 시 LM-post-1 패치 재확인.

---

### B 그룹 — `flashback_verifier.py` 예외 범위 보강

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/flashback_verifier.py
읽을 범위:
  - check()             전체 (L45~68 근방)
  - _llm_check()        전체 (L127~155 근방)
  - _parse_llm_response() 전체 (L156~198 근방)
```

체크포인트:
- `check()` — `if not manuscript: return []` 조기 리턴 확인 (안전 경로)
- `_llm_check()` `except` 구문이 `(json.JSONDecodeError, ValueError, RuntimeError, OSError)`로 좁은지 확인 → **`Exception`으로 확장 필요 (P1)**
- `_parse_llm_response()` 내 `except (json.JSONDecodeError, ValueError)` — parse용 좁은 except는 허용 (P2)

**P1 기준**: `_llm_ask()` 호출 시 `ConnectionError`, `AttributeError` 등 미처리 예외 → 비치명 보장 안 됨.

**② 런타임 검증**:

```bash
python -c "
from modules.core.flashback_verifier import FlashbackVerifier

def bad_llm(prompt):
    raise ConnectionError('네트워크 오류')

fv = FlashbackVerifier(llm_ask=bad_llm)
ms = '그는 문득 어린 시절 기억이 떠올랐다. 예전에 아버지가 말씀하셨다. 기억 속의 그 날, 동생이 웃고 있었다.'
result = fv.check(ms, ep_num=10, reference_context='어린 시절 아버지의 기억')
print('bad_llm 비치명 결과:', result)  # 빈 리스트여야 함
"
```

**③ 패치 대상**:

```python
# Before (flashback_verifier.py _llm_check):
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[LM-E] FlashbackVerifier LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After:
except Exception as e:
    logger.warning("[LM-E] FlashbackVerifier LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

---

### C 그룹 — `info_paradox_checker.py` 예외 범위 보강

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/info_paradox_checker.py
읽을 범위:
  - build_knowledge_summary()  전체 (L29~117 근방)
  - check()                    전체 (L119~147 근방)
  - _llm_check()               전체 (L148~188 근방)
  - _parse_llm_response()      전체 (L190~233 근방)
```

체크포인트:
- `build_knowledge_summary()` L47 근방 `except (AttributeError, TypeError, RuntimeError)` — DB 접근 실패용이므로 `Exception`으로 확장 여부 판단
- `check()` — `if not manuscript or not pov_character or not knowledge_summary: return []` 조기 리턴 확인
- `_llm_check()` L185 근방 `except (json.JSONDecodeError, ValueError, RuntimeError, OSError)` → **`Exception`으로 확장 필요 (P1)**
- `_parse_llm_response()` L206 근방 `except (json.JSONDecodeError, ValueError)` — parse용, P2 허용

**② 런타임 검증**:

```bash
python -c "
from modules.core.info_paradox_checker import InfoParadoxChecker

def bad_llm(prompt):
    raise AttributeError('LLM API 속성 오류')

checker = InfoParadoxChecker(llm_ask=bad_llm)
result = checker.check(
    '그는 그 사실을 이미 알고 있었다.',
    ep_num=5,
    pov_character='이준혁',
    knowledge_summary='[LM-F] ep1~4 지식 요약...',
)
print('bad_llm 비치명 결과:', result)  # 빈 리스트여야 함

# build_knowledge_summary DB 없음 처리
summary = InfoParadoxChecker.build_knowledge_summary(None, up_to_ep=5, protagonist_name='이준혁')
print('db=None 결과:', repr(summary))  # 빈 문자열이어야 함
"
```

**③ 패치 대상**:

```python
# Before (_llm_check L185 근방):
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[LM-F] InfoParadoxChecker LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After:
except Exception as e:
    logger.warning("[LM-F] InfoParadoxChecker LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

`build_knowledge_summary()` L47도 동일하게 `Exception`으로 확장:

```python
# Before:
except (AttributeError, TypeError, RuntimeError) as e:
    logger.warning("[LM-F] episode_bibles 조회 실패: %s", str(e)[:80])
    return ""

# After:
except Exception as e:
    logger.warning("[LM-F] episode_bibles 조회 실패: %s", str(e)[:80])
    return ""
```

---

### D 그룹 — `relationship_drift_advisor.py` 예외 범위 보강

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/relationship_drift_advisor.py
읽을 범위:
  - build_relationship_timeline()  전체 (L29~75 근방)
  - check()                        전체 (L76~98 근방)
  - _llm_check()                   전체 (L99~120 근방)
  - _parse_llm_response()          전체 (L121~166 근방)
```

체크포인트:
- `build_relationship_timeline()` — `if not db or not hasattr(...)` 방어 확인
- `check()` — `if not manuscript or not relationship_timeline: return []` 조기 리턴 확인
- `_llm_check()` L117 근방 `except (json.JSONDecodeError, ValueError, RuntimeError, OSError)` → **`Exception`으로 확장 필요 (P1)**
- `_parse_llm_response()` L138 근방 `except (json.JSONDecodeError, ValueError)` — parse용, P2 허용

**② 런타임 검증**:

```bash
python -c "
from modules.core.relationship_drift_advisor import RelationshipDriftAdvisor

def bad_llm(prompt):
    raise OSError('파일 시스템 오류')

adv = RelationshipDriftAdvisor(llm_ask=bad_llm)
result = adv.check(
    '김철수와 박영희는 함께 걸었다.',
    ep_num=30,
    relationship_timeline='ep1: 원수 → ep15: 협력',
)
print('bad_llm 비치명 결과:', result)  # 빈 리스트여야 함

# build_relationship_timeline db=None 처리
timeline = RelationshipDriftAdvisor.build_relationship_timeline(None)
print('db=None 결과:', repr(timeline))  # 빈 문자열이어야 함
"
```

**③ 패치 대상**:

```python
# Before (_llm_check L117 근방):
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[LM-D] RelationshipDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After:
except Exception as e:
    logger.warning("[LM-D] RelationshipDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

---

## 2) 패치 원칙

- **LLM 호출 except**: 반드시 `Exception`으로 확장 — advisory-only 모듈은 어떤 예외도 파이프라인 중단 불가.
- **parse except**: `(json.JSONDecodeError, ValueError)` 유지 허용 — 입력이 명확히 str이므로 좁은 범위가 안전.
- **DB 접근 except**: `Exception`으로 통일 — DB 드라이버 예외 종류가 다양함.
- **A그룹 검증 실패 시**: LM-post-1 패치 누락 의미 → 해당 파일 재패치, 이 파일들은 수정 금지.

---

## 3) 실행 순서

```bash
# A그룹 확인 (코드 변경 없음)
python -c "<A그룹 런타임 검증 스크립트 1>"
python -c "<A그룹 런타임 검증 스크립트 2>"

# B그룹 패치 후
python -m py_compile modules/core/flashback_verifier.py
python -c "<B그룹 런타임 검증 스크립트>"

# C그룹 패치 후
python -m py_compile modules/core/info_paradox_checker.py
python -c "<C그룹 런타임 검증 스크립트>"

# D그룹 패치 후
python -m py_compile modules/core/relationship_drift_advisor.py
python -c "<D그룹 런타임 검증 스크립트>"

# ruff
ruff check modules/core/flashback_verifier.py \
  modules/core/info_paradox_checker.py \
  modules/core/relationship_drift_advisor.py

# 전체 회귀
pytest tests/ -q
```

---

## 4) 보고서 형식

출력: `docs/2026-03-04/8th-audit-result.md`

```markdown
# 8차 전수조사 결과

> 감사일: 2026-03-04

## 감사 범위

A. LM-post-1 변경 후속 검증 (validation_orchestrator + causal_graph read)
B. flashback_verifier.py 예외 범위 보강
C. info_paradox_checker.py 예외 범위 보강
D. relationship_drift_advisor.py 예외 범위 보강

## 발견 이슈

| ID | 파일 | 내용 | 등급 | 처리 |
|----|------|------|------|------|
| A-001 | LM-post-1 후속 | lookback/causal 배선 | 확인 | PASS/FAIL |
| B-001 | flashback_verifier.py | _llm_check except 범위 | P1 | 패치 |
| C-001 | info_paradox_checker.py | _llm_check + build_knowledge except 범위 | P1 | 패치 |
| D-001 | relationship_drift_advisor.py | _llm_check except 범위 | P1 | 패치 |

## 조치 내역

(패치 before/after)

## 검증 결과

- py_compile: 통과
- ruff: 위반 0건
- 전체 테스트: N passed, 0 failed (N skipped)
```

---

## 5) 합격 기준

- A그룹 런타임 검증 **전량 PASS** (lookback ≥ 10, get_recent_causal_links 존재)
- B/C/D 예외 범위 **전량 `except Exception`으로 확장**
- 전체 테스트 **LM-post-1 기준선 이상 passed, 0 failed**
- ruff 위반 **0건**
