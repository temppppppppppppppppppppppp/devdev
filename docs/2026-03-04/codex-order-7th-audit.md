# Codex Order: 7차 전수조사

> **목적**: P2 유보 7파일 SSOT 문서화 완결 + LM-Tier 신규 Advisory 모듈 3종 예외 처리 보강.
> **금지**: 모델 값 변경. 기존 테스트 시그니처 변경. 명세에 없는 신기능 추가.
> **출력 보고서**: `docs/2026-03-04/7th-audit-result.md`

---

## 0) 강제 제약

- 각 패치 후 즉시 `python -m py_compile <수정파일>` 통과 필수.
- `pytest tests/ -q` 기준선: **3220 passed, 16 skipped, 0 failed**.
- `ruff check modules/ tests/` 위반 0건 유지.

---

## 1) 감사 대상 파일 (우선순위 순)

### A 그룹 — P2 유보 7파일 [SSOT-P2] 주석 처리

6차 전수조사에서 P2로 유보한 파일들. `main_a.py`가 model을 명시 주입하므로 default 값이 실제로 쓰이지 않음.
**작업**: 각 하드코딩 라인 끝에 `# [SSOT-P2] 호출자(main_a.py:LXXX)가 model 인자를 명시 전달` 주석 추가. 로직 변경 없음.

| 파일 | 라인 | 호출자(main_a.py) |
|------|------|-------------------|
| `modules/core/adversarial_self_play.py` | L136 근방 default 인자 | L1929 `model=_V50_MODULE_MODEL` |
| `modules/core/chain_of_verification.py` | L122 근방 default 인자 | L1906 `model=_V50_MODULE_MODEL` |
| `modules/core/cross_agent_verifier.py` | L118 근방 default 인자 | L1895 `model=_V50_MODULE_MODEL` |
| `modules/core/multi_agent_deliberation.py` | L181 근방 default 인자 | L1936 `model=_V50_MODULE_MODEL` |
| `modules/domain/agents/arc_corrector.py` | L592 근방 default 인자 | L1548 `model_tier=_FLASH_ANALYSIS_MODEL` |
| `modules/domain/agents/arc_critic.py` | L131, L368 근방 default 인자 | L1529 `model_tier=AIModels.STAGE2_MAIN_MODEL` |
| `modules/domain/agents/arc_ensemble.py` | L113, L890 근방 default 인자 | L1513 `model_tier=AIModels.STAGE2_MAIN_MODEL` |

**주석 형식**:
```python
# Before:
def __init__(self, ..., model: str = "gemini-2.5-flash", ...):

# After:
def __init__(self, ..., model: str = "gemini-2.5-flash", ...):  # [SSOT-P2] 호출자(main_a.py:L1929)가 model 인자를 명시 전달
```

---

### B 그룹 — `long_term_repetition_advisor.py` 예외 범위 보강

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/long_term_repetition_advisor.py
읽을 범위:
  - check()              전체 (L44~70 근방)
  - _llm_check()         전체 (L165~195 근방)
  - _parse_llm_response() 전체 (L197~230 근방)
```

체크포인트:
- `_llm_check()` `except` 구문이 `json.JSONDecodeError, ValueError, RuntimeError, OSError`로 너무 좁은지 확인 → **`Exception`으로 확장 필요 (P1)**
- `_parse_llm_response()` 내 `isinstance(parsed, list)` 체크 후 빈 리스트 반환 경로 확인 (안전 경로)
- `build_pattern_summary()` 내 `current_ep < MIN_LOOKBACK` 조기 리턴 확인 (안전 경로)
- `check()` 내 `if not manuscript or not pattern_summary: return []` 조기 리턴 확인

**P0 기준**: LLM 호출 실패 시 except 누락 → advisory 크래시 → 원고 생성 중단.
**P1 기준**: except 범위 좁아 일부 예외 미포착 → silent crash 가능.

**② 런타임 검증**:

```bash
python -c "
from modules.core.long_term_repetition_advisor import LongTermRepetitionAdvisor

# llm_ask가 예외 발생 시 비치명 처리 여부 확인
def bad_llm(prompt):
    raise ConnectionError('네트워크 오류')

advisor = LongTermRepetitionAdvisor(llm_ask=bad_llm)
result = advisor._llm_check('원고 내용', '전투→수련', '[P1-5] 테스트', 25)
print('비치명 처리 결과:', result)  # 빈 리스트여야 함

# ep < 20 조기 리턴 확인
summary = LongTermRepetitionAdvisor.build_pattern_summary(None, current_ep=10)
print('ep<20 조기 리턴:', repr(summary))  # 빈 문자열이어야 함
"
```

**③ 패치 대상** (P1 확인 시):

```python
# Before:
except (json.JSONDecodeError, ValueError, RuntimeError, OSError) as e:
    logger.warning("[P1-5] LongTermRepetitionAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []

# After:
except Exception as e:
    logger.warning("[P1-5] LongTermRepetitionAdvisor LLM 호출 실패 (비치명): %s", str(e)[:80])
    return []
```

---

### C 그룹 — `npc_drift_advisor.py` 예외 범위 보강

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/npc_drift_advisor.py
읽을 범위:
  - check()                  전체 (L28~63 근방)
  - _llm_check_batch()       전체 (L100~126 근방)
  - _parse_llm_response()    전체 (L127~170 근방)
  - _find_appearing_npcs()   전체 (L64~77 근방)
```

체크포인트:
- `check()` — `npc_snapshots` 빈 dict/None 입력 시 안전 경로 있는지
- `_find_appearing_npcs()` — `npc_snapshots` 값이 dict가 아닌 경우(str, None 등) 방어 있는지
- `_llm_check_batch()` `except` 범위가 `Exception`인지 좁은 타입인지 확인
- `_parse_llm_response()` — LLM이 dict가 아닌 list 안에 비dict 항목 넣을 때 처리

**P0 기준**: `_find_appearing_npcs()`에서 AttributeError/TypeError → advisory 크래시.
**P1 기준**: `_llm_check_batch()` except 범위 좁음 → silent crash.

**② 런타임 검증**:

```bash
python -c "
from modules.core.npc_drift_advisor import NpcDriftAdvisor

# 빈 입력 비치명 처리 확인
advisor = NpcDriftAdvisor(llm_ask=None)
result = advisor.check('원고 내용', {}, ep_num=5)
print('빈 npc_snapshots 결과:', result)  # 빈 리스트여야 함

# None 입력 확인
result2 = advisor.check('', None, ep_num=5)
print('None 입력 결과:', result2)

# llm_ask 예외 발생 시 비치명 처리 확인
def bad_llm(prompt):
    raise RuntimeError('API 오류')

advisor2 = NpcDriftAdvisor(llm_ask=bad_llm)
result3 = advisor2.check('이준혁은 차갑게 말했다.', {'이준혁': {'name': '이준혁'}}, ep_num=3)
print('LLM 실패 비치명:', result3)  # 빈 리스트여야 함
"
```

---

### D 그룹 — `numeric_drift_advisor.py` 예외 범위 + 지수 성장 감지 보강

**① 코드 수동 검사** — 아래 메서드를 직접 읽어라:

```
파일: modules/core/numeric_drift_advisor.py
읽을 범위:
  - check()                     전체 (L31~62 근방)
  - _format_history()           전체 (L63~96 근방)
  - _llm_check()                전체 (L97~120 근방)
  - _parse_llm_response()       전체 (L121~167 근방)
  - _detect_exponential_growth() 전체 (L178~205 근방)
```

체크포인트:
- `check()` — `numbers` 빈 dict/None 입력 시 조기 리턴 여부
- `check()` — `len(history) < min_history` 체크 위치 (크래시 방어)
- `_detect_exponential_growth()` — `numbers` 이력 길이가 `< 5` 일 때 안전한지 (ZeroDivisionError 방지)
- `_llm_check()` `except` 범위 — `Exception`인지 좁은 타입인지 확인
- `_format_history()` — `MAX_ITEMS=30` 초과 시 슬라이싱 여부 확인

**P0 기준**: `_detect_exponential_growth()`에서 list index / ZeroDivisionError → advisory 크래시.
**P1 기준**: `_llm_check()` except 범위 좁음 → silent crash.

**② 런타임 검증**:

```bash
python -c "
from modules.core.numeric_drift_advisor import NumericDriftAdvisor

# 빈 입력 비치명 처리 확인
advisor = NumericDriftAdvisor(llm_ask=None)
result = advisor.check({}, ep_num=5)
print('빈 numbers 결과:', result)  # 빈 리스트여야 함

# 이력 부족 시 처리 확인
result2 = advisor.check({'capital': [{'ep': 1, 'value': 100}]}, ep_num=2)
print('이력 부족 결과:', result2)  # 빈 리스트여야 함

# 지수 성장 감지 확인
advisor2 = NumericDriftAdvisor(llm_ask=None)
short_history = [10, 20]  # 2개 → 지수 성장 감지 크래시 없어야 함
warnings = advisor2._detect_exponential_growth({'capital': [{'ep': i+1, 'value': v} for i, v in enumerate(short_history)]})
print('짧은 이력 지수 감지:', warnings)

# llm_ask 예외 발생 시 비치명 처리 확인
def bad_llm(prompt):
    raise AttributeError('속성 오류')

advisor3 = NumericDriftAdvisor(llm_ask=bad_llm)
result3 = advisor3.check({'capital': [{'ep': i, 'value': i*100} for i in range(1, 6)]}, ep_num=5)
print('LLM 실패 비치명:', result3)  # 빈 리스트여야 함
"
```

---

## 2) 패치 원칙

### P0 패치 즉시 처리
- ZeroDivisionError / AttributeError / TypeError / 예외 전파로 advisory가 파이프라인을 중단시키는 경우.
- 수정 후 py_compile + 런타임 검증 즉시.

### P1 패치 처리
- except 범위 좁음: `Exception`으로 확장.
- None/빈값 입력 방어 누락.
- 수정 후 전체 테스트 회귀 확인.

### P2 현상 유지
- `# [SSOT-P2] 호출자 명시 전달` 주석만 추가, 로직 변경 없음.
- 모든 P2 파일은 `main_a.py`가 model을 명시 전달하므로 default 실사용 없음.

### 보존 항목 (절대 변경 금지)
- `MIN_LOOKBACK = 20` — 최소 분석 윈도우 정책.
- `REPEAT_THRESHOLD = 3` — 반복 패턴 경고 임계값.
- `MAX_ITEMS = 30`, `MAX_HISTORY_POINTS = 20` — NumericDrift 한도 (이미 보강됨).
- P2 유보 7파일의 default 모델명 값 자체 — 주석 추가만, 값 변경 금지.

---

## 3) 실행 순서

```bash
# A그룹: 7개 파일 주석 추가 후
python -m py_compile modules/core/adversarial_self_play.py \
  modules/core/chain_of_verification.py \
  modules/core/cross_agent_verifier.py \
  modules/core/multi_agent_deliberation.py \
  modules/domain/agents/arc_corrector.py \
  modules/domain/agents/arc_critic.py \
  modules/domain/agents/arc_ensemble.py

# B그룹 패치 후
python -m py_compile modules/core/long_term_repetition_advisor.py
python -c "<B그룹 런타임 검증 스크립트>"

# C그룹 패치 후
python -m py_compile modules/core/npc_drift_advisor.py
python -c "<C그룹 런타임 검증 스크립트>"

# D그룹 패치 후
python -m py_compile modules/core/numeric_drift_advisor.py
python -c "<D그룹 런타임 검증 스크립트>"

# ruff
ruff check modules/core/long_term_repetition_advisor.py \
  modules/core/npc_drift_advisor.py \
  modules/core/numeric_drift_advisor.py \
  modules/core/adversarial_self_play.py \
  modules/core/chain_of_verification.py \
  modules/core/cross_agent_verifier.py \
  modules/core/multi_agent_deliberation.py \
  modules/domain/agents/arc_corrector.py \
  modules/domain/agents/arc_critic.py \
  modules/domain/agents/arc_ensemble.py

# 전체 회귀
pytest tests/ -q
```

---

## 4) 보고서 형식

출력: `docs/2026-03-04/7th-audit-result.md`

```markdown
# 7차 전수조사 결과

> 감사일: 2026-03-04

## 감사 범위

A. P2 유보 7파일 [SSOT-P2] 주석 처리
B. long_term_repetition_advisor.py 예외 범위 보강
C. npc_drift_advisor.py 예외 범위 + 입력 방어
D. numeric_drift_advisor.py 예외 범위 + 지수 성장 감지 안전성

## 발견 이슈

| ID | 파일 | 내용 | 등급 | 처리 |
|----|------|------|------|------|
| A-001 | P2 유보 7파일 | [SSOT-P2] 주석 없음 | P2 | 주석 추가 |
| B-001 | long_term_repetition_advisor.py | _llm_check except 범위 | P1/P0/없음 | 패치/현상유지 |
| C-001 | npc_drift_advisor.py | _llm_check_batch except 범위 | P1/P0/없음 | 패치/현상유지 |
| D-001 | numeric_drift_advisor.py | _llm_check except 범위 | P1/P0/없음 | 패치/현상유지 |

## 조치 내역

(패치한 항목별 before/after 핵심 라인)

## 검증 결과

- py_compile: 통과
- ruff: 위반 0건
- 전체 테스트: N passed, 0 failed (16 skipped)

## P2 목록

| 파일 | 라인 | 주석 추가 | 호출자 |
|------|------|-----------|--------|
| adversarial_self_play.py | L136 | [SSOT-P2] | main_a.py:L1929 |
| chain_of_verification.py | L122 | [SSOT-P2] | main_a.py:L1906 |
| cross_agent_verifier.py | L118 | [SSOT-P2] | main_a.py:L1895 |
| multi_agent_deliberation.py | L181 | [SSOT-P2] | main_a.py:L1936 |
| arc_corrector.py | L592 | [SSOT-P2] | main_a.py:L1548 |
| arc_critic.py | L131, L368 | [SSOT-P2] | main_a.py:L1529 |
| arc_ensemble.py | L113, L890 | [SSOT-P2] | main_a.py:L1513 |
```

---

## 5) 합격 기준

- P0 이슈 **전량 패치**
- P1 이슈 **전량 패치 또는 명시적 현상유지 판정**
- P2 유보 7파일 **[SSOT-P2] 주석 전량 추가 완료**
- 전체 테스트 **3220+ passed, 0 failed**
- ruff 위반 **0건**
