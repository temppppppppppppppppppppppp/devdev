# 7차 전수조사 결과

> 감사일: 2026-03-04

## 감사 범위

A. P2 유보 7파일 [SSOT-P2] 주석 처리
B. `long_term_repetition_advisor.py` 예외 범위 보강
C. `npc_drift_advisor.py` 예외 범위 + 입력 방어 보강
D. `numeric_drift_advisor.py` 예외 범위 + 입력 방어 보강

## 발견 이슈

| ID | 파일 | 내용 | 등급 | 처리 |
|----|------|------|------|------|
| A-001 | P2 유보 7파일 | 하드코딩 default 라인에 SSOT 호출부 근거 주석 부재 | P2 | 주석 추가 완료 |
| B-001 | `modules/core/long_term_repetition_advisor.py` | `_llm_check()` 예외 범위가 제한적이라 일부 예외 누락 가능 | P1 | `except Exception`으로 보강 |
| C-001 | `modules/core/npc_drift_advisor.py` | `npc_snapshots`/`manuscript` 타입 방어 부재 및 `_llm_check_batch()` 예외 범위 제한 | P1 | 입력 타입 가드 + `except Exception` 보강 |
| D-001 | `modules/core/numeric_drift_advisor.py` | `numbers` 타입 방어 부재, `_llm_check()` 예외 범위 제한, `_detect_exponential_growth()` dict 가드 부재 | P1 | 입력 타입 가드 + `except Exception` + dict 가드 보강 |

## 조치 내역

### A그룹: [SSOT-P2] 주석 추가 (로직 변경 없음)

- `modules/core/adversarial_self_play.py` (`__init__` default)
- `modules/core/chain_of_verification.py` (`__init__` default)
- `modules/core/cross_agent_verifier.py` (`__init__` default)
- `modules/core/multi_agent_deliberation.py` (`__init__` default)
- `modules/domain/agents/arc_corrector.py` (`create_arc_corrector` default)
- `modules/domain/agents/arc_critic.py` (`__init__`, `create_arc_critic` default)
- `modules/domain/agents/arc_ensemble.py` (`__init__`, `create_ensemble_generator` default)

### B그룹: `long_term_repetition_advisor.py`

- before: `_llm_check()`에서 `except (json.JSONDecodeError, ValueError, RuntimeError, OSError)`
- after: `_llm_check()`에서 `except Exception`

### C그룹: `npc_drift_advisor.py`

- `check()` 진입부 타입 방어 추가
  - `if not isinstance(manuscript, str) or not manuscript: return []`
  - `if not isinstance(npc_snapshots, dict) or not npc_snapshots: return []`
- `_find_appearing_npcs()` 진입부 타입 방어 추가
  - `if not isinstance(manuscript, str) or not isinstance(npc_snapshots, dict): return []`
- `_llm_check_batch()` 예외 범위 확장
  - before: 제한된 예외 tuple
  - after: `except Exception`

### D그룹: `numeric_drift_advisor.py`

- `check()` 진입부 타입 방어 추가
  - `if not isinstance(numbers, dict) or not numbers: return []`
- `_llm_check()` 예외 범위 확장
  - before: 제한된 예외 tuple
  - after: `except Exception`
- `_detect_exponential_growth()` dict 가드 추가
  - `if not isinstance(numbers, dict): return warnings`

## 수동 검토 + 런타임 확인

- `LongTermRepetitionAdvisor`
  - `bad_llm(ConnectionError)` 입력 시 `_llm_check()`가 `[]` 반환 확인
  - `build_pattern_summary(..., current_ep=10)`에서 `""` 조기 반환 확인
- `NpcDriftAdvisor`
  - 빈 dict/None/list 입력에서 `check()`가 `[]` 반환 확인
  - `bad_llm(RuntimeError)` 입력 시 `[]` 반환 확인
- `NumericDriftAdvisor`
  - 빈 dict/list 입력에서 `check()`가 `[]` 반환 확인
  - 짧은 이력(`len<6`)에서 `_detect_exponential_growth()`가 `[]` 반환 확인
  - `bad_llm(AttributeError)` 입력 시 `[]` 반환 확인

## 검증 결과

- py_compile: 통과
  - A그룹 7파일 일괄 `python -m py_compile` 통과
  - `modules/core/long_term_repetition_advisor.py` 통과
  - `modules/core/npc_drift_advisor.py` 통과
  - `modules/core/numeric_drift_advisor.py` 통과
- ruff: 위반 0건
  - `ruff check modules/ tests/` → `All checks passed!`
- 전체 테스트:
  - `pytest tests/ -q` → **3220 passed, 16 skipped, 0 failed** (warning 1건)

## P2 목록

| 파일 | 라인 | 주석 추가 | 호출부 |
|------|------|-----------|--------|
| `adversarial_self_play.py` | 136 | `[SSOT-P2]` | `main_a.py:L1929` |
| `chain_of_verification.py` | 122 | `[SSOT-P2]` | `main_a.py:L1906` |
| `cross_agent_verifier.py` | 118 | `[SSOT-P2]` | `main_a.py:L1895` |
| `multi_agent_deliberation.py` | 181 | `[SSOT-P2]` | `main_a.py:L1936` |
| `arc_corrector.py` | 592 | `[SSOT-P2]` | `main_a.py:L1548` |
| `arc_critic.py` | 131, 368 | `[SSOT-P2]` | `main_a.py:L1529` |
| `arc_ensemble.py` | 113, 890 | `[SSOT-P2]` | `main_a.py:L1513` |
