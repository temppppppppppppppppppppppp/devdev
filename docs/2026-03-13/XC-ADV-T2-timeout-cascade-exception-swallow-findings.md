# XC-ADV-T2: Timeout 캐스케이드 & 예외 삼킴 — Findings

> 감사 일자: 2026-03-13
> 초점: 글로벌 300s + 개별 60s timeout 상호작용, 예외 처리 적절성

---

## 분석 요약

Advisory 체인은 이중 timeout 구조를 사용한다:
1. `as_completed(futures, timeout=300)` — 전체 advisory 체인 글로벌 타임아웃
2. `future.result(timeout=60)` — 개별 advisory 결과 수거 타임아웃

이 두 타임아웃의 상호작용과 예외 처리 경로를 분석한다.

---

## PASS 1: 후보 수집

### [XC-ADV-006] P1 | 글로벌 300s timeout 후 미수거 future 처리 부재

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-006 |
| Severity | P1 |
| 현상 요약 | `as_completed(timeout=300)` 만료 시 아직 완료되지 않은 future들이 cancel 되지 않고 방치됨 |
| 코드 근거 | `stage4_interview_round.py:3817-3832` |
| 영향 경계 | Stage 4 — advisory 체인 전체. 메모리/스레드 누수 가능성 |
| 테스트 근거 | D-T3: "advisory timeout, 부분 실패, future 수거 순서 미검증" 확인. 기존 테스트 커버리지 0% |
| 기존 중복 여부 | T2-038 (ThreadPoolExecutor 타임아웃 후 메모리 점유), T3-004 (advisory 병렬 테스트 부재) |
| 권장 후속 조치 | `as_completed` 루프 후 미완료 future에 대해 `future.cancel()` 호출 추가. `with` 블록 종료 시 executor.shutdown(wait=True)가 암시적으로 대기하므로, 300s timeout 이후에도 미완료 작업이 끝날 때까지 blocking될 수 있음. `cancel_futures=True` 옵션 (Python 3.9+) 사용 권장. 공수 0.5h |

**코드 스니펫:**
```python
# L3807-3832
with ThreadPoolExecutor(max_workers=8, thread_name_prefix="advisory") as executor:
    futures[executor.submit(self._advisory_truth_gate, ...)] = "TruthGate"
    # ... 7개 더 submit ...

    _advisory_parts: list[str] = []
    for future in as_completed(futures, timeout=300):   # 300s 글로벌
        _name = futures[future]
        try:
            result = future.result(timeout=60)           # 60s 개별
            if result:
                _advisory_parts.extend(result)
        except Exception as e:
            logging.debug("[Advisory] %s 실패 (비치명): %s", _name, e)
# with 블록 종료 → executor.shutdown(wait=True) 암시적 호출
```

**분석:**
- `as_completed(timeout=300)`이 `TimeoutError`를 raise하면, for 루프가 즉시 종료된다.
- 이 TimeoutError는 **with 블록 내부**에서 발생하므로, except 절 없이 with 블록을 탈출한다.
- `ThreadPoolExecutor.__exit__`가 `shutdown(wait=True)`를 호출하여, 아직 실행 중인 advisory들이 끝날 때까지 **무기한 대기**한다.
- LLM API 호출이 걸린 advisory가 응답을 기다리는 동안 전체 파이프라인이 blocking된다.
- **worst case**: 6개 LLM advisory가 모두 API 응답 대기 중이면, Gemini API 자체 timeout까지 대기.

---

### [XC-ADV-007] P2 | as_completed TimeoutError가 bare except 없이 전파

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-007 |
| Severity | P2 |
| 현상 요약 | `as_completed(timeout=300)` raise TimeoutError가 `_run_advisory_chain` 밖으로 전파될 수 있음 |
| 코드 근거 | `stage4_interview_round.py:3818` — for 루프 내 try/except는 `future.result()` 예외만 잡음, `as_completed` iterator 자체의 TimeoutError는 미포착 |
| 영향 경계 | Stage 4 — `_run_advisory_chain` 호출자 (`run` 메서드) |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | T3-004 관련 |
| 권장 후속 조치 | for 루프를 try/except TimeoutError로 감싸기. 공수 0.3h |

**분석:**
```python
for future in as_completed(futures, timeout=300):  # TimeoutError 가능
    # ...
    try:
        result = future.result(timeout=60)  # 이 except만 존재
    except Exception as e:
        logging.debug(...)
```
- `as_completed`의 `__next__()` 호출 시 300s가 경과하면 `TimeoutError`가 발생한다.
- 이 예외는 for 루프 바깥으로 전파되며, 현재 코드에 이를 잡는 로직이 없다.
- 호출자 `run()` 메서드의 상위 try/except가 잡을 수 있으나, advisory 부분 결과가 유실된다.
- 실제 발생 확률: 매우 낮음 (8개 advisory가 모두 60s 이상 소요해야 300s 초과).

---

### [XC-ADV-008] P2 | 이중 timeout의 의미론적 모호성

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-008 |
| Severity | P2 |
| 현상 요약 | `as_completed(timeout=300)` + `future.result(timeout=60)` 조합에서 실효 타임아웃이 360s까지 늘어날 수 있음 |
| 코드 근거 | `stage4_interview_round.py:3818-3821` |
| 영향 경계 | Stage 4 — 최악 경우 6분 대기 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 기존 체크리스트에서 "max_workers=8, per-task timeout=60s, as_completed timeout=300s" 기록만 존재, 상호작용 미분석 |
| 권장 후속 조치 | 타임아웃 전략 단순화 권장. `as_completed(timeout=300)` 하나로 충분하며, `future.result(timeout=60)`는 불필요한 이중 대기. 또는 `future.result(timeout=0)`으로 변경 (as_completed가 이미 완료된 future만 yield하므로). 공수 0.2h |

**분석:**
- `as_completed`는 **완료된** future를 yield한다. 따라서 `future.result(timeout=60)`에서 60초를 추가로 기다릴 일은 일반적으로 없다.
- 그러나 `as_completed`의 timeout은 **다음 future가 완료될 때까지**의 대기시간이 아니라, **iterator 전체** 생명주기이다.
- 실제로 `as_completed`가 future를 yield한 시점에서 `future.result()`는 즉시 반환된다.
- 따라서 `timeout=60`은 방어적이지만 실질적으로 도달하지 않는 dead timeout이다.

---

### [XC-ADV-009] P2 | 예외 삼킴 — logging.debug 레벨

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-009 |
| Severity | P2 |
| 현상 요약 | Advisory 실패가 `logging.debug` 레벨로만 기록되어, 기본 로그 설정(INFO)에서 보이지 않음 |
| 코드 근거 | `stage4_interview_round.py:3826` — `logging.debug("[Advisory] %s 실패 (비치명): %s", _name, e)` |
| 영향 경계 | Stage 4 — 운영 모니터링 |
| 테스트 근거 | 해당 없음 (로깅 레벨 이슈) |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `logging.warning`으로 상향. advisory 실패는 "비치명"이지만, 반복 실패 시 품질 저하 원인 파악이 어려워짐. 공수 0.1h |

**분석:**
- 각 개별 advisory 래퍼 메서드(`_advisory_truth_gate` 등)는 내부에서 `logging.warning`으로 기록한다.
- 그러나 `future.result()` 단계에서 발생하는 예외(TimeoutError 포함)는 `logging.debug`만 사용한다.
- 즉, advisory 내부 예외는 WARNING으로, 외부 수거 실패는 DEBUG로 — 비일관적이다.

---

### [XC-ADV-010] P3 | 개별 advisory 래퍼의 광범위 except 절

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-010 |
| Severity | P3 |
| 현상 요약 | 각 advisory 래퍼가 `(AttributeError, TypeError, ValueError, RuntimeError, OSError)` 5종을 일괄 포착 |
| 코드 근거 | `stage4_interview_round.py:3870` (TruthGate), `3920` (NpcDrift), `3948` (NumericDrift), `4015` (Flashback), `4074` (InfoParadox), `4122` (RelDrift), `4164` (LongTermRep) |
| 영향 경계 | Stage 4 — 디버깅 난이도 |
| 테스트 근거 | 해당 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 설계 의도상 advisory는 비치명이므로 광범위 포착이 의도적. 다만, 각 except에서 traceback 포함 로깅 추가 권장 (`logging.warning(..., exc_info=True)`). 공수 0.3h |

---

## PASS 2: 교차 검증

| ID | PASS 1 신뢰도 | PASS 2 판정 | 근거 |
|----|-------------|------------|------|
| XC-ADV-006 | HIGH | **유효** | ThreadPoolExecutor `__exit__` 동작 Python 문서 확인. shutdown(wait=True) 기본 동작. T2-038과 동일 메커니즘 |
| XC-ADV-007 | HIGH | **유효** | `concurrent.futures` 소스 확인: as_completed TimeoutError는 StopIteration이 아니라 별도 예외 |
| XC-ADV-008 | MED | **유효 (낮은 위험)** | as_completed가 완료된 future만 yield하므로 result() timeout은 실질적 dead path |
| XC-ADV-009 | HIGH | **유효** | 로깅 레벨 비일관성 확인 |
| XC-ADV-010 | MED | **유효 (의도적)** | advisory 비치명 원칙상 의도적 설계 |

---

## PASS 3: 최종 확정

| ID | 최종 Severity | 비고 |
|----|-------------|------|
| XC-ADV-006 | **P1** | 글로벌 timeout 후 executor blocking 위험. 유일한 P1 |
| XC-ADV-007 | **P2** | TimeoutError 미포착 — 부분 결과 유실 가능 |
| XC-ADV-008 | **P3** | 이중 timeout 의미론적 혼란이나 실질 위험 낮음 |
| XC-ADV-009 | **P2** | 운영 가시성 저해 |
| XC-ADV-010 | **P3** | 의도적 설계이나 개선 여지 존재 |

---

## 총평

가장 위험한 시나리오는 **XC-ADV-006**: `as_completed(timeout=300)`이 만료된 후, `with` 블록 종료 시 `executor.shutdown(wait=True)`가 아직 실행 중인 LLM API 호출을 무기한 대기하는 것이다.

Python 3.9+ `executor.shutdown(wait=True, cancel_futures=True)` 또는 명시적 `future.cancel()` 호출로 해결 가능하다.

`as_completed` TimeoutError 미포착(XC-ADV-007)은 상위 호출자가 잡을 가능성이 있으나, advisory 부분 결과가 유실되는 점에서 데이터 손실 이슈이다.
