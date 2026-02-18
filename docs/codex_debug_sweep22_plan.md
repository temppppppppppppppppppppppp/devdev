# Debug Sweep 22 — 타입 가드 누락 + 로거 불일치

## Context

Sweep 21(5건) 완료 후(1,972 passed), 5-에이전트 병렬 탐색으로 미탐색 핵심 모듈 전면 스윕:
chief_writer 서브모듈 2종, state_tracker + extractor, world_state + fact_ledger, DI 컨텍스트 3종 + vec_memory, continuity_inspector + base_agent.
수동 코드 검증으로 **확인된 실제 버그 4건** 정리.

---

## A-1 (MEDIUM): `state_extractor.py:324` tactical 비문자열 타입 가드 누락 → re.findall 크래시

**파일**: `modules/domain/agents/state_extractor.py:321-324`

**문제**:
```python
tactical = arc.get("tactical_doc", "")
if isinstance(tactical, dict):  # [V70] dict → str 변환
    tactical = "\n".join(str(v) for v in tactical.values() if v)
# ↑ list, int, None 등 비-dict/비-str 타입은 변환 없이 통과

grants = self._extract_grants_from_text(tactical)  # ← re.findall(pattern, list) → TypeError
```
- `tactical_doc`는 LLM JSON 파싱 결과 — dict/str 외에 list 반환 가능
- L322: dict 체크만 있고, list/int/None 등 다른 타입 미처리
- `_extract_grants_from_text()`는 L641에서 `re.findall(pattern, text)` 호출 — text가 str이 아니면 TypeError
- 동일 함수 내 L656 `_fallback_entity_extraction`은 `isinstance(text, str)` 가드 있음 — 패턴 불일치

**수정** — L323 뒤에 else 추가:
```python
if isinstance(tactical, dict):
    tactical = "\n".join(str(v) for v in tactical.values() if v)
elif not isinstance(tactical, str):
    tactical = str(tactical) if tactical else ""
```

**테스트**: `arc = {"tactical_doc": ["text1", "text2"]}` 입력 시 크래시 없이 정상 처리 검증

---

## A-2 (MEDIUM): `chief_writer_context.py:847` isinstance(dict) 가드 누락 — 동일 파일 L106, L814와 불일치

**파일**: `modules/domain/agents/chief_writer_context.py:847`

**문제**:
```python
# L106 — 올바른 패턴
bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}

# L814 — 올바른 패턴
bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}

# L847 — 가드 누락
bible_root = master_bible.get("MasterBible", master_bible)  # ← isinstance 없음
```
- L844의 `if not master_bible: return {}` 는 None/빈 dict만 방어
- master_bible이 truthy 비-dict (e.g., 문자열)이면 `.get()` → AttributeError
- try/except(L842)가 있어 앱 크래시는 방지되지만, 무음 실패 + 빈 dict 반환
- 동일 파일 내 2곳은 가드 있고 1곳만 누락 — 명확한 copy-paste 누락

**수정**:
```python
bible_root = master_bible.get("MasterBible", master_bible) if isinstance(master_bible, dict) else {}
```

**테스트**: master_bible이 비-dict truthy 값일 때 크래시 없이 `{}` 반환 검증

---

## B-1 (LOW): `world_state.py:99` `logging.warning()` → `_logger.warning()` 불일치

**파일**: `modules/core/world_state.py:99`

**문제**:
```python
# L14 — 모듈 로거 정의
_logger = logging.getLogger(__name__)

# L99 — root logger 사용 (불일치)
logging.warning(f"[WorldState] NPC entry missing name: {death}")
```
- 파일 전체에서 `_logger`를 사용하는데 L99만 `logging.warning()` 직접 호출
- root logger로 메시지 전송 → 모듈별 로그 필터링 우회
- 운영 모니터링에서 WorldStateManager 로그 누락 가능

**수정**:
```python
_logger.warning(f"[WorldState] NPC entry missing name: {death}")
```

**테스트**: 소스 코드에서 `logging.warning` 직접 호출이 없는지 검증 (grep)

---

## B-2 (LOW): `fact_ledger.py:47` `logging.warning()` → `_logger.warning()` 불일치

**파일**: `modules/core/fact_ledger.py:47`

**문제**:
```python
# L14 — 모듈 로거 정의
_logger = logging.getLogger(__name__)

# L47 — root logger 사용 (불일치)
logging.warning(f"⚠️ [V70] FactLedger DB 로드 실패, 초기화: {e}")

# L67 — 모듈 로거 사용 (올바른 패턴)
_logger.warning(f"[V68] 팩트 원장 저장 실패: {e}")
```
- 동일 파일 내 L67은 `_logger.warning()` 사용, L47은 `logging.warning()` 사용
- B-1과 동일한 root logger 불일치 문제

**수정**:
```python
_logger.warning(f"⚠️ [V70] FactLedger DB 로드 실패, 초기화: {e}")
```

**테스트**: B-1과 동일 (grep 검증)

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/state_extractor.py` | 2줄 추가 (elif str 변환) |
| A-2 | `modules/domain/agents/chief_writer_context.py` | 1줄 수정 (isinstance 가드) |
| B-1 | `modules/core/world_state.py` | 1줄 수정 (logging→_logger) |
| B-2 | `modules/core/fact_ledger.py` | 1줄 수정 (logging→_logger) |

**총 ~5줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `fact_ledger.py:245` old_val 타입 불일치 | ✗ 오탐 | `entry["value"]`는 이전 호출에서 저장한 값 — 동일 타입. default `""` 는 key 누락 시에만 (불가) |
| `world_state.py:204` active_plots 비-dict 원소 | ✗ 오탐 | `active_plots`는 내부 관리 리스트, update()에서 dict만 추가. 외부 역직렬화 경로 없음 |
| `fact_ledger.py:384` history 비-문자열 | ✗ 오탐 | history는 f-string으로만 append — 항상 str |
| `world_state.py:62` json deep copy 비효율 | ✗ 스타일 | 동작 정확, _INIT_STATE에 중첩 dict/list → json roundtrip이 가장 안전한 deep copy |
| DI 콜백 None 가드 (8건) | ✗ 오탐 | `from_app()`에서 모든 콜백 바인딩. SovereignApp에 해당 메서드 전부 존재. 프로덕션에서 None 불가 |
| `base_agent.py:953` isinstance union type | ✗ 오탐 | Python 3.10+ PEP 604 유효 문법 |
| `base_agent.py:1138` cached_content 파라미터명 | ✗ 불확실 | Gemini SDK 파라미터. V61.5부터 사용 중이며 캐싱 동작 확인됨 |
| `base_agent.py:1069-1080` 캐시 race condition | ✗ 이론적 | CPython GIL + sorted_keys 스냅샷으로 실제 경합 극저확률. 캐시 작업은 주로 메인 스레드 |
| `continuity_inspector.py:186` aliases join 타입 | ✗ 오탐 | entity_registry의 aliases는 LLM JSON 파싱 후 항상 list |
| `chief_writer_context.py:974` dead code | ✗ 설계 | 미사용 메서드 — dead code이지 버그가 아님 |
| Stage2Context 콜백 카운트 21→22 | ✗ 문서 | sync_cache_key_to_app은 Sweep3-D2 후속 추가. 기능 무관 |
| Stage4Context 확장 11→13 카운트 | ✗ 문서 | 주석 카운트 불일치. 기능 무관 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_state_tracker.py tests/test_chief_writer.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-18)

- 완료: A-1 `modules/domain/agents/state_extractor.py`
  - `tactical_doc`가 `dict`가 아닌 비문자열 타입일 때 `str`/빈문자열로 정규화하는 가드(`elif not isinstance(tactical, str)`) 추가
- 완료: A-2 `modules/domain/agents/chief_writer_context.py`
  - `_get_npc_frequency()` 내부 `master_bible` 접근에 `isinstance(master_bible, dict)` 가드 추가
- 완료: B-1 `modules/core/world_state.py`
  - root logger 호출 `logging.warning(...)` -> 모듈 로거 `_logger.warning(...)`로 통일
- 완료: B-2 `modules/core/fact_ledger.py`
  - root logger 호출 `logging.warning(...)` -> 모듈 로거 `_logger.warning(...)`로 통일

### Tests Added/Updated

- 추가: `tests/test_sweep22_regressions.py`
  - `StateExtractor.extract_cumulative_state()`가 list 타입 `tactical_doc`를 크래시 없이 처리하는지 검증
  - `ChiefWriterContextBuilder._get_npc_frequency()`가 non-dict `master_bible`에서 `.get()`을 호출하지 않고 `{}` 반환하는지 검증
  - `WorldStateManager`가 NPC name 누락 경로에서 root `logging.warning`을 호출하지 않는지 검증
  - `FactLedger` 로드 실패 경로에서 root `logging.warning`을 호출하지 않는지 검증

### Pytest Results

1. 계획 기준 1차 검증
   - `python -m pytest tests/test_state_tracker.py tests/test_chief_writer.py -q -x`
   - 결과: `103 passed`
2. sweep22 회귀 테스트 포함 추가 검증
   - `python -m pytest tests/test_chief_writer_context.py tests/test_fact_ledger.py tests/test_sweep22_regressions.py -q -x`
   - 결과: `34 passed`
3. 전체 테스트
   - `python -m pytest tests/ -q -p no:capture`
   - 결과: `2 failed, 1976 passed, 68 xfailed, 1 warning`
   - 실패 테스트(기존 동일):
     - `tests/test_stage2_pipeline.py::TestAnalystProtagonistConfig::test_world_origin_primitive`
     - `tests/test_stage2_pipeline.py::TestAnalystProtagonistConfig::test_incarnation_type_regression`
