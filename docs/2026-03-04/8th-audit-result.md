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
| A-001 | LM-post-1 후속 | lookback/causal 배선 | 확인 | PASS |
| B-001 | modules/core/flashback_verifier.py | `_llm_check` except 범위 | P1 | 패치 |
| C-001 | modules/core/info_paradox_checker.py | `_llm_check` + `build_knowledge_summary` except 범위 | P1 | 패치 |
| D-001 | modules/core/relationship_drift_advisor.py | `_llm_check` except 범위 | P1 | 패치 |

## 조치 내역

### B-001

```python
# Before
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[LM-E] FlashbackVerifier LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After
except Exception as e:
    logger.warning("[LM-E] FlashbackVerifier LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

### C-001

```python
# Before
except (AttributeError, TypeError, RuntimeError) as e:
    logger.warning("[LM-F] episode_bibles 조회 실패: %s", str(e)[:80])
    return ""

# After
except Exception as e:
    logger.warning("[LM-F] episode_bibles 조회 실패: %s", str(e)[:80])
    return ""
```

```python
# Before
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[LM-F] InfoParadoxChecker LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After
except Exception as e:
    logger.warning("[LM-F] InfoParadoxChecker LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

### D-001

```python
# Before
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[LM-D] RelationshipDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After
except Exception as e:
    logger.warning("[LM-D] RelationshipDriftAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

## 검증 결과

- A-런타임-1: `retrospective.lookback_episodes = 10` (PASS)
- A-런타임-2: `get_recent_causal_links(current_ep=5, lookback=10) == []` (PASS)
- A-정적 확인:
  - `modules/validation/validation_orchestrator.py` 에서 `retrospective.lookback_episodes` YAML 조회 확인
  - `modules/core/stage4_post_processor.py` 에서 `get_recent_causal_links(..., lookback=10)` + `_director_mc_parts` 주입 로그 블록 확인
  - `modules/core/db_manager.py` 에서 `get_recent_causal_links(self, current_ep: int, lookback: int = 10)` 시그니처 확인
- py_compile: 3/3 통과
  - `modules/core/flashback_verifier.py`
  - `modules/core/info_paradox_checker.py`
  - `modules/core/relationship_drift_advisor.py`
- B/C/D 런타임 비치명 검증: 3/3 PASS (bad_llm 입력에서 모두 `[]` 반환)
- ruff(대상 3파일): 위반 0건
- ruff(전체 `modules/ tests/`): 위반 0건
- 전체 테스트(`pytest tests/ -q`): **3227 passed, 16 skipped, 0 failed, 1 warning**

## 참고 사항

- 오더 문서 A-런타임-2 예시 스크립트의 `DBManager.initialize_db()` 호출은 현 코드베이스에 해당 메서드가 없어, 동일 검증 목적(빈 DB에서 `get_recent_causal_links`가 비치명으로 `[]` 반환)을 만족하는 등가 스크립트로 실행함.
