# Debug Sweep 17 — 검증 폴백 + 이중 DB 호출 + Guard 누락

## Execution Status (2026-02-17)

- A-1 completed:
  - `modules/validation/validation_orchestrator.py`
    - `validate_parallel_v59()` advisory 폴백 키를 `{"warnings": []}`에서 `{"suggestions": []}`로 수정.
- A-2 completed:
  - `modules/domain/agents/director_auditor.py`
    - V0128 경로에서만 `_expand_prev_full_text()`를 호출하도록 이동.
    - legacy 경로(use_v0128=False)에서 중복 호출 제거(1회만 호출).
- A-3 completed:
  - `modules/core/fact_ledger.py`
    - `get_dead_characters()`, `get_alive_characters()`에 `isinstance(info, dict)` 가드 추가.
- A-4 completed:
  - `modules/validation/validation_orchestrator.py`
    - 진행/성공 메시지 6곳 `logging.warning -> logging.info` 조정.
- B-1 completed:
  - `modules/domain/agents/blueprint_ensemble.py`
    - 개별/전체 타임아웃 로그 `info -> warning`.
    - PerfTimer 로그 `warning -> info`.
- B-2 completed:
  - `modules/domain/agents/director_continuity.py`
    - timeline 조건부 `pass` 데드 코드 3줄 삭제.
  - `modules/domain/agents/director_auditor.py`
    - `[V60.55 DEBUG]` 로그 `warning -> info`.
    - Director 컨텍스트 확대 성공 로그 `warning -> info`.
- B-3 completed:
  - `modules/domain/agents/continuity_manuscript.py`
    - `stupid_villain`의 완화 케이스 severity를 `"WARNING"`에서 `"MINOR"`로 정정.
  - `modules/core/reflexion_manager.py`
    - 과거 실패 패턴 로드 성공 로그 `warning -> info`.

- Added/updated tests:
  - `tests/test_sweep7.py`
    - advisory 계약을 `suggestions`로 정렬.
    - advisory 태스크 실패 시 `{"suggestions": []}` 폴백 검증 추가.
  - `tests/test_fact_ledger.py`
    - 손상 데이터(non-dict)에서 `get_dead_characters()` / `get_alive_characters()` 안전 동작 검증 추가.
  - `tests/test_director_modules.py`
    - legacy 경로 `_expand_prev_full_text()` 호출 횟수 1회 검증 추가.
  - `tests/test_continuity_modules.py`
    - 악역 학습 반응 존재 시 `stupid_villain` severity `MINOR` 검증 추가.
  - `tests/test_sweep17.py` (신규)
    - Sweep17 로그 레벨/키명/데드코드 제거 관련 소스 회귀 검증 추가.

- Verification:
  - `python -m pytest tests/test_sweep7.py tests/test_fact_ledger.py tests/test_director_modules.py tests/test_continuity_modules.py tests/test_sweep17.py tests/test_agent_perf_timer.py -q -x` -> `142 passed`
  - `python -m pytest tests/ -q -p no:capture` -> `1948 passed, 68 xfailed, 1 warning`

## Context

Sweep 16(7건) 완료 후, 3-에이전트 병렬 탐색으로 미탐색 대형 모듈 전면 스윕:
validation_orchestrator, scoring_validator, blocking_validator, advisory_validator, director 서브모듈 5종,
continuity_inspector 서브모듈 4종, blueprint_ensemble, feedback_system, fact_ledger, reflexion_manager.
수동 코드 검증으로 **확인된 실제 버그 7건** 정리.

---

## A-1 (HIGH): `validate_parallel_v59()` advisory 폴백 — 잘못된 dict 키

**파일**: `modules/validation/validation_orchestrator.py:1046`

**문제**:
```python
# L1046 — advisory 병렬 태스크 실패 시 폴백
if not isinstance(advisory_result, dict):
    advisory_result = {"warnings": []}  # ❌ "warnings" 키 사용
```
- `AdvisoryValidator.validate()` 계약: `{"suggestions": [...], "tier": "ADVISORY", ...}` 반환
- 순차 경로 L409: `len(advisory_result.get('suggestions', []))` — "suggestions" 키 사용
- `_generate_detailed_feedback()` L739: 동일하게 "suggestions" 키 참조
- 폴백이 "warnings" 키를 제공 → `.get("suggestions", [])` 기본값 반환 → 기능적으로 빈 리스트이지만 **의도와 불일치**
- 병렬 advisory 실패 시 데이터 키가 누락된 채 무시됨

**수정**:
```python
if not isinstance(advisory_result, dict):
    advisory_result = {"suggestions": []}
```

**테스트**: `validate_parallel_v59` 에서 advisory 태스크 실패 시 폴백 dict에 "suggestions" 키 존재 검증

---

## A-2 (MEDIUM): `audit_manuscript()` — `_expand_prev_full_text()` 이중 호출

**파일**: `modules/domain/agents/director_auditor.py:527,553`

**문제**:
```python
# L527 — V0128/legacy 분기 이전에 호출
expanded_prev_for_v0128 = self._expand_prev_full_text(ep_num, prev_full_text)
# ... L530: validation_context["expanded_prev_full_text"] = expanded_prev_for_v0128

# L534: if self._d.use_v0128: return _audit_with_v0128(...)  ← V0128 경로: 여기서 early return

# L553 — legacy 경로에서 다시 호출
expanded_prev = self._expand_prev_full_text(ep_num, prev_full_text)
```
- `_expand_prev_full_text()`: DB에서 최대 30화 원고 조회 (ep_num-30 ~ ep_num-1)
- `use_v0128=False` 시 L527과 L553 **둘 다** 실행 → 동일 인자로 **2회 호출** (최대 60회 DB 조회)
- L527의 결과(`expanded_prev_for_v0128`)는 legacy 경로에서 사용되지 않음

**수정** — L527-531을 `use_v0128` 분기 내부로 이동:
```python
# [V43] V0128 검증 시스템 조건부 사용
if self._d.use_v0128 and validation_context:
    # [V66.1] V0128 경로에만 prev_full_text 확대
    expanded_prev_for_v0128 = self._expand_prev_full_text(ep_num, prev_full_text)
    if validation_context is None:
        validation_context = {}
    if expanded_prev_for_v0128:
        validation_context["expanded_prev_full_text"] = expanded_prev_for_v0128
    return self._audit_with_v0128(
        ep_num=ep_num, manuscript=manuscript, validation_context=validation_context, target_len=target_len
    )
```
기존 L527-531 제거, L553의 호출은 그대로 유지.

**테스트**: `_expand_prev_full_text` mock으로 호출 횟수 검증 (legacy 경로에서 1회만)

---

## A-3 (MEDIUM): `fact_ledger.py` — `get_dead_characters()`, `get_alive_characters()` isinstance 가드 누락

**파일**: `modules/core/fact_ledger.py:489-495`

**문제**:
```python
# L489-490 — 가드 없음
def get_dead_characters(self) -> list[str]:
    chars = self._ledger.get("characters", {})
    return [name for name, info in chars.items() if info.get("status") == "dead"]

# L492-495 — 가드 없음
def get_alive_characters(self) -> list[str]:
    chars = self._ledger.get("characters", {})
    return [name for name, info in chars.items() if info.get("status") == "alive"]

# L503 — 가드 있음 (Sweep 15 B-4 수정)
"alive": sum(1 for v in chars.values() if isinstance(v, dict) and v.get("status") == "alive"),
```
- `get_stats()` (L503)에는 `isinstance(v, dict)` 가드가 Sweep 15에서 추가됨
- 동일 데이터를 순회하는 `get_dead_characters()`와 `get_alive_characters()`에는 미적용
- 데이터 손상 시 `info`가 dict가 아니면 `info.get("status")` → AttributeError

**수정**:
```python
def get_dead_characters(self) -> list[str]:
    chars = self._ledger.get("characters", {})
    return [name for name, info in chars.items() if isinstance(info, dict) and info.get("status") == "dead"]

def get_alive_characters(self) -> list[str]:
    chars = self._ledger.get("characters", {})
    return [name for name, info in chars.items() if isinstance(info, dict) and info.get("status") == "alive"]
```

**테스트**: 손상된 ledger 데이터(비-dict 값)가 있을 때 두 메서드가 AttributeError 없이 빈 리스트 반환하는지 검증

---

## A-4 (MEDIUM): `validation_orchestrator.py` — 성공/진행 메시지 6곳 WARNING → INFO

**파일**: `modules/validation/validation_orchestrator.py`

**문제**:
```python
# L240 — 진행 메시지 (다른 Tier는 모두 logging.info 사용)
logging.warning("[V56] TIER 0.25: PRE-LLM 검증 중...")  # ← 유일하게 WARNING

# L268 — 성공 메시지
logging.warning("✅ PRE-LLM 통과")

# L297 — 성공 메시지
logging.warning("✅ CONTINUITY 통과")

# L321 — 성공 메시지
logging.warning(f"✅ BLOCKING 통과 (0/{blocking_result.get('failure_count', 0)} 실패)")

# L353 — 성공 메시지
logging.warning("✅ CONSISTENCY 통과")

# L425 — 성공 메시지
logging.warning("✅ CATHARSIS: 적절한 타이밍")
```
- L273(CONTINUITY), L302(BLOCKING), L326(CONSISTENCY), L358(SCORING), L405(ADVISORY) 진행 메시지는 모두 `logging.info` 사용
- L240만 `logging.warning` → 불일치
- 5개 성공("✅ ... 통과") 메시지가 모두 WARNING → 모니터링 노이즈

**수정**: 6곳 모두 `logging.warning` → `logging.info`

---

## B-1 (LOW): `blueprint_ensemble.py` — 타임아웃/성능 로그 레벨 3곳 수정

**파일**: `modules/domain/agents/blueprint_ensemble.py`

**문제**:
```python
# L210 — 개별 후보 타임아웃 (성능 저하 이벤트) → INFO
logging.info(f"⏰ [V61.3] {strategy_name} 타임아웃 ({self.SINGLE_CANDIDATE_TIMEOUT}초)")

# L215-217 — 전체 앙상블 타임아웃 (성능 저하 이벤트) → INFO
logging.info(
    f"⏰ [V61.3] 블루프린트 앙상블 타임아웃 ({self.ENSEMBLE_TIMEOUT}초) - 완료된 {len(candidates)}개 후보 사용"
)

# L231 — 루틴 성능 계측 → WARNING
logging.warning(f"[PerfTimer:BlueprintEnsemble] bp_ep{ep_num}_ensemble={time.monotonic() - _tp_t0:.2f}s")
```
- L210, L215: 타임아웃 → WARNING 적절 (Sweep 16 A-4 chief_writer 타임아웃과 동일 패턴)
- L231: 루틴 성능 기록 → INFO 적절 (매 호출마다 출력)

**수정**:
- L210: `logging.info` → `logging.warning`
- L215: `logging.info` → `logging.warning`
- L231: `logging.warning` → `logging.info`

---

## B-2 (LOW): 데드 코드 + 디버그 로그 레벨 — 3건

### B-2a: `director_continuity.py:636-638` — 데드 코드

```python
# 시점 체크 (있으면)
if prev_ending_state.get("timeline") and new_blueprint.get("ending_state", {}).get("timeline"):
    pass
```
- 조건 충족 시 아무 동작 없음 (`pass`) → 미구현 TODO
- L640부터 실제 결정 로직 시작 → 이 블록은 완전히 무의미

**수정**: 3줄 삭제.

### B-2b: `director_auditor.py:717` — DEBUG 진단이 WARNING

```python
logging.warning(f"🔍 [V60.55 DEBUG] 주인공 이름 검증: '{protagonist_name}'")
```
- `[V60.55 DEBUG]` 접두사가 명시적으로 디버그 용도 표시
- L718-720 후속 상세 정보는 `logging.info` 사용 → 불일치

**수정**: `logging.warning` → `logging.info`

### B-2c: `director_auditor.py:305` — 성공 메시지가 WARNING

```python
logging.warning(f"📖 [V67] Director 컨텍스트 확대: {len(loaded_parts)}화 이전 원고 로드 (ep {ep_num})")
```
- 컨텍스트 확대 **성공** 이벤트 → INFO 적절
- A-2 이중 호출 문제와 결합 시 WARNING이 2회 출력되는 부작용도 있음

**수정**: `logging.warning` → `logging.info`

---

## B-3 (LOW): `continuity_manuscript.py` severity 비표준 + `reflexion_manager.py` 로그 레벨

### B-3a: `continuity_manuscript.py:622` — severity `"WARNING"` → `"MINOR"`

```python
issues.append(
    {
        "type": "stupid_villain",
        "severity": "WARNING",  # ← 비표준 (CRITICAL/MAJOR/MINOR/NONE만 유효)
        "description": f"악역이 주인공을 {underestimate_count + 1}회 과소평가 ...",
    }
)
```
- severity 어휘: `CRITICAL` → REJECT, `MAJOR` → REJECT, `MINOR` → WARNING으로 PASS
- `"WARNING"`은 결과(조치)이지 severity 레벨이 아님
- L455-456 caller: `severity == "CRITICAL"`만 분기 → 나머지는 warnings 리스트로 이동 → 현재 동작은 정상
- 미래 코드가 `severity in ["CRITICAL", "MAJOR"]` 분기 추가 시 무시됨

**수정**: `"severity": "WARNING"` → `"severity": "MINOR"`

### B-3b: `reflexion_manager.py:56` — 성공 로드 메시지가 WARNING

```python
logging.warning(f"📚 [Reflexion] 과거 실패 패턴 {len(self.memory)}개 로드됨")
```
- 메모리 로드 **성공** 이벤트 → INFO 적절

**수정**: `logging.warning` → `logging.info`

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/validation/validation_orchestrator.py` | 1줄 수정 (키명) |
| A-2 | `modules/domain/agents/director_auditor.py` | ~5줄 이동 (분기 내부로) |
| A-3 | `modules/core/fact_ledger.py` | 2줄 수정 (isinstance 추가) |
| A-4 | `modules/validation/validation_orchestrator.py` | 6줄 (warning→info) |
| B-1 | `modules/domain/agents/blueprint_ensemble.py` | 3줄 (레벨 수정) |
| B-2a | `modules/domain/agents/director_continuity.py` | 3줄 삭제 (데드 코드) |
| B-2b | `modules/domain/agents/director_auditor.py` | 1줄 (warning→info) |
| B-2c | `modules/domain/agents/director_auditor.py` | 1줄 (warning→info) |
| B-3a | `modules/domain/agents/continuity_manuscript.py` | 1줄 (severity 수정) |
| B-3b | `modules/core/reflexion_manager.py` | 1줄 (warning→info) |

**총 ~24줄 변경 + 3줄 삭제**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `inspect_manuscript_v59()` entity_registry 누락 | ✗ 미사용 | 프로덕션 코드에서 `inspect_manuscript_v59` 호출처 없음 (facade + 내부 모듈 정의만 존재) |
| `reflexion_manager.py:99,115` conn.commit() 스레드 안전성 | ✗ 설계 | SQLite 단일 연결 직렬화 + 협력적 스레딩 컨텍스트. execute_update 내부 RLock은 커서 조작 보호용 |
| `scoring_validator.py:615` float sensory_penalty | ✗ 설계 | total_score가 `round(weighted_total, 1)`로 이미 float. 0.5 페널티는 세밀한 점수 차등화 의도 |
| `scoring_validator.py:799` "%" 레이블 | ✗ 정상 | v59 경로는 weighted_percentage 기반. `pass_threshold`가 퍼센트 임계값으로 사용됨 |
| `director_grading.py:378-386` satisfaction 분기 취약 | ✗ 설계 | satisfaction은 `examples` dict에 의도적으로 미포함. 별도 early-return으로 처리. 구조는 의도대로 |
| `director_grading.py:640-648` current_hud isinstance | ✗ 오탐 | 호출자가 항상 HUD 시스템에서 dict 또는 None 전달. `if current_hud:` 가드가 None 차단 |
| `director_auditor.py:114-116` _profiles_empty 미사용 | ✗ 오탐 | 변수가 L116 logging guard에 사용됨 |
| `catharsis_timer.py:222` timestamp=None 영구 | ✗ 설계 | dead 데이터 필드이나 기능 영향 없음. `_count_frustration_streak()`는 ep_num으로 정렬 |
| `continuity_arc.py:748-754` prev_status isinstance | ✗ 오탐 | `arc.get("status_shadow", {})` 기본값이 빈 dict. LLM 파싱 결과가 항상 dict |
| `continuity_manuscript.py:1090-1094` 데드 코드 삼항 | ✗ 무해 | `len(history) < 2: continue` 가드 뒤 중복 체크. 무해한 방어 코드 |
| `blocking_validator.py:120` 깨진 문자열 | ✗ 오탐 | Read 도구의 인코딩 표시 문제. 원본 파일은 정상 한글 ("REJECT - 필수 검증 실패") |
| `validation_orchestrator.py:658,881` dead vtype | ✗ 설계 | 디버깅용 추출 패턴. 향후 피드백 포맷 변경 시 활용 예정 |
| `state_tracker.py:90` any vs Any | ✗ 무해 | 런타임 어노테이션 미강제. 타입 체커 미사용 프로젝트 |
| `director_auditor.py:880` integer division 50% REJECT | ✗ 설계 | Sweep 14 오탐 기록: 동점 시 REJECT이 안전한 기본값 (Director 주권주의) |
| `world_state.py:99` bare logging vs _logger | ✗ 설계 | 단일 logging 호출, 모듈 필터링 미사용 환경 |
| `director_auditor.py:527,553` 이중 호출 성능만 | ✓ 수정 | A-2로 수정 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_validation_orchestrator.py tests/test_fact_ledger.py tests/test_director_audit.py tests/test_blueprint_ensemble.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
