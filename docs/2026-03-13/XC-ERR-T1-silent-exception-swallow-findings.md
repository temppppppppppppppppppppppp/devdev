# XC-ERR-T1: Silent Exception 삼킴 전수 조사

> 생성일: 2026-03-13
> 스코프: 전체 modules/ 디렉터리
> 방법론: 3-Pass (수집 → 교차검증 → 위양성 제거)

---

## 1. 전체 통계

| 카테고리 | 건수 | 비고 |
|----------|------|------|
| `except Exception` 총계 | 957 | 137개 파일 |
| bare `except:` | 0 | 전량 제거 완료 (양호) |
| `except Exception` + `pass` only | ~15 | 대부분 telemetry setattr |
| `except Exception` + `continue` only | ~10 | 루프 내 개별 항목 스킵 |
| `except Exception` + `logging.debug` + return 기본값 | ~96 | 의도적 비차단 패턴 |
| `except Exception` + `report_soft_failure` | ~50+ | 구조화된 리포팅 (양호) |

### 상위 10 파일 (except Exception 카운트 기준)
| 파일 | 카운트 | 위험도 |
|------|--------|--------|
| `stage4_interview_round.py` | 71 | 높음 — 원고 생성 핫패스 |
| `stage2_preflight.py` | 57 | 중간 — 전처리 경로 |
| `stage4_context_builder.py` | 54 | 높음 — 컨텍스트 조립 |
| `stage4_post_processor.py` | 47 | 높음 — 후처리 핫패스 |
| `db_manager.py` | 42 | 높음 — DB 접근 계층 |
| `stage3_orchestrator.py` | 40 | 중간 |
| `vec_memory.py` | 33 | 중간 — 벡터 DB |
| `stage4_orchestrator.py` | 31 | 높음 — 오케스트레이터 |
| `failure_analyzer.py` | 28 | 낮음 — 분석 유틸리티 |
| `base_agent.py` | 27 | 높음 — 에이전트 베이스 |

---

## 2. Findings

### [XC-ERR-001] P2 | Stage3Orchestrator 에이전트 telemetry setattr silent pass

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-001 |
| Severity | P2 |
| 현상 요약 | `_set_agent_telemetry_context()`에서 agent attribute 설정 실패 시 `except Exception: pass`로 완전 삼킴 |
| 코드 근거 | `stage3_orchestrator.py:467-468`, `stage3_orchestrator.py:472-473` |
| 영향 경계 | Stage 3 전체 — telemetry 누락으로 실패 분석 불가 |
| 테스트 근거 | 해당 경로 직접 테스트 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `logging.debug` 최소 1줄 추가 (0.5h) |

```python
# stage3_orchestrator.py:465-473
try:
    setattr(agent, "_current_stage", 3)
except Exception:
    pass  # ← 완전 삼킴
if _ep_value is not None:
    try:
        setattr(agent, "_current_ep_num", _ep_value)
    except Exception:
        pass  # ← 완전 삼킴
```

**분석**: `setattr` 실패는 frozen dataclass나 `__slots__` 제한 시 발생 가능. 현재 에이전트는 일반 클래스이므로 실제 발생 확률은 낮으나, 발생 시 디버깅 단서가 전무.

---

### [XC-ERR-002] P2 | Stage4Orchestrator 동일 telemetry silent pass 패턴

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-002 |
| Severity | P2 |
| 현상 요약 | `stage4_orchestrator.py:262-268`에서 동일한 `setattr` + `except Exception: pass` 패턴 |
| 코드 근거 | `stage4_orchestrator.py:262-268` |
| 영향 경계 | Stage 4 전체 — telemetry 누락 |
| 테스트 근거 | 해당 경로 직접 테스트 없음 |
| 기존 중복 여부 | XC-ERR-001과 동일 패턴, 별도 파일 |
| 권장 후속 조치 | XC-ERR-001과 동일 수정 (0.5h) |

---

### [XC-ERR-003] P3 | Stage4ContextBuilder `_build_condensed_world_state_summary` silent return ""

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-003 |
| Severity | P3 |
| 현상 요약 | `world_state.get_summary()` 실패 시 `except Exception: return ""` — 에러 로그 없이 빈 문자열 반환 |
| 코드 근거 | `stage4_context_builder.py:976-977` |
| 영향 경계 | Stage 4 원고 품질 — world state 컨텍스트 누락으로 연속성 약화 가능 |
| 테스트 근거 | 해당 경로 직접 테스트 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `logging.debug` 추가 (0.3h) |

```python
# stage4_context_builder.py:974-977
try:
    return world_state.get_summary(max_chars=max_chars)
except Exception:
    return ""  # ← 로그 없는 삼킴
```

---

### [XC-ERR-004] P3 | Stage4ContextBuilder 두 번째 `get_summary` 폴백도 silent

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-004 |
| Severity | P3 |
| 현상 요약 | 동일 메서드 내 두 번째 `world_state.get_summary()` 호출도 `except Exception: return ""` |
| 코드 근거 | `stage4_context_builder.py:985-988` |
| 영향 경계 | XC-ERR-003과 동일 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | XC-ERR-003 sister |
| 권장 후속 조치 | XC-ERR-003과 함께 수정 (0.3h) |

---

### [XC-ERR-005] P2 | db_manager.py 마이그레이션 rollback 내 pass 삼킴

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-005 |
| Severity | P2 |
| 현상 요약 | `state_logs` ALTER TABLE 실패 후 `conn.rollback()` 재실패 시 `except Exception: pass` — 이중 실패 무시 |
| 코드 근거 | `db_manager.py:231-234` |
| 영향 경계 | DB 초기화 — 마이그레이션 실패가 완전히 은폐될 수 있음 |
| 테스트 근거 | 마이그레이션 실패 경로 테스트 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `logging.warning` 추가 + 마이그레이션 상태 플래그 (1h) |

```python
# db_manager.py:230-234
except sqlite3.OperationalError as e:
    if "no such table" not in str(e).lower():
        logging.warning(f"[WARNING] state_logs 마이그레이션 실패: {e}")
        try:
            self.conn.rollback()
        except Exception as e:
            logging.debug(f"[SILENT] state_logs rollback: {e}")
            pass  # ← rollback 실패도 삼킴
```

---

### [XC-ERR-006] P2 | db_manager.py merge 마이그레이션 rollback + DETACH 실패 삼킴

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-006 |
| Severity | P2 |
| 현상 요약 | DB 마이그레이션 중 `conn.rollback()` 실패 시 `except Exception: pass`, 이후 DETACH도 실패 가능 |
| 코드 근거 | `db_manager.py:938-941` |
| 영향 경계 | DB 마이그레이션 — attached DB가 유령 상태로 남을 수 있음 |
| 테스트 근거 | 마이그레이션 실패 경로 테스트 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | rollback+DETACH 실패 시 `logging.error` + 재시도 (1h) |

---

### [XC-ERR-007] P3 | db_manager.py `save_episode_data` rollback 후 pass

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-007 |
| Severity | P3 |
| 현상 요약 | `save_episode_data` 내 여러 except 블록에서 `self.rollback()` 재실패 시 `except Exception: pass` |
| 코드 근거 | `db_manager.py:2153-2155`, `db_manager.py:2170-2172`, `db_manager.py:2194-2196`, `db_manager.py:2206-2208` |
| 영향 경계 | 에피소드 저장 — 이미 실패 상태이므로 이차 실패는 저위험 |
| 테스트 근거 | `[R7-P1-2]` 주석으로 의도적임을 명시 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `logging.debug` 유지, 현행 유지 가능 (0h) — 의도적 방어 패턴 |

**분석**: `[R7-P1-2]` 주석이 "closed DB 시 이차 예외 방지"를 명시. 이미 실패 경로에서의 방어적 pass이므로 P3.

---

### [XC-ERR-008] P3 | Stage3Orchestrator `_build_stage3_prompt_version` silent return None

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-008 |
| Severity | P3 |
| 현상 요약 | 프롬프트 버전 태그 생성 실패 시 `logging.debug` + `return None` — 비차단이나 디버깅 추적성 약함 |
| 코드 근거 | `stage3_orchestrator.py:102-103` |
| 영향 경계 | 감사 로그 품질 — 프롬프트 버전 추적 불가 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | 현행 유지 가능 — logging.debug 존재 (0h) |

---

### [XC-ERR-009] P3 | Stage3Orchestrator 다수의 advisory 빌더 silent return ""

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-009 |
| Severity | P3 |
| 현상 요약 | `_build_stale_seed_advisory`, `_build_fact_ledger_advisory`, `_build_world_state_advisory` 등 5개+ 함수에서 실패 시 빈 문자열 반환 |
| 코드 근거 | `stage3_orchestrator.py:134-136`, `stage3_orchestrator.py:151-153`, `stage3_orchestrator.py:163-165`, `stage3_orchestrator.py:251-253`, `stage3_orchestrator.py:339-340` |
| 영향 경계 | Stage 3 Blueprint 품질 — advisory 컨텍스트 누락이나 각각 독립적이므로 전체 실패는 아님 |
| 테스트 근거 | 개별 advisory 실패 테스트 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | 현행 유지 — 모두 `logging.debug` 포함, 비차단 의도 (0h) |

**분석**: 이 패턴은 코드베이스의 설계 철학("Python은 수집만, 판단은 LLM")과 일치. advisory 실패가 Blueprint 생성 자체를 막으면 안 되므로 의도적 비차단.

---

### [XC-ERR-010] P3 | Stage4ContextBuilder `_resolve_protagonist_name` 3단계 폴백 체인

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-010 |
| Severity | P3 |
| 현상 요약 | 주인공 이름 해결에 3단계 try-except 체인 사용 — 각 단계 실패가 `logging.debug` + 다음 폴백 |
| 코드 근거 | `stage4_context_builder.py:79-106` |
| 영향 경계 | Stage 4 — 3단계 전부 실패 시 빈 문자열 반환, NPC 경계 블록 등에서 주인공 식별 불가 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | 현행 유지 — 3단계 폴백은 견고한 설계 (0h) |

---

### [XC-ERR-011] P3 | Stage3Orchestrator notifier import silent swallow

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-011 |
| Severity | P3 |
| 현상 요약 | `from modules.utils.notifier import notifier`가 모듈 레벨 `except Exception`으로 감싸져 있어 import 실패가 은폐됨 |
| 코드 근거 | `stage3_orchestrator.py:25-28` |
| 영향 경계 | Slack 알림 비활성화 — 비차단 기능이므로 저위험 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | `except ImportError`로 좁히기 (0.3h) |

```python
# stage3_orchestrator.py:25-28
try:
    from modules.utils.notifier import notifier
except Exception:  # ← ImportError로 좁혀야 함
    notifier = None
```

---

## 3. 비차단 패턴 분류 (위양성으로 제외된 항목)

다음 패턴들은 의도적 비차단(non-blocking)으로 판정하여 finding에서 제외:

1. **`report_soft_failure()` 호출 후 return**: 구조화된 리포팅이 있으므로 "삼킴"이 아님
2. **`logging.debug` + return 기본값 (advisory 경로)**: CLAUDE.md 대원칙 1 준수 (Python 수집만)
3. **루프 내 개별 항목 `except Exception: continue`**: 단일 항목 실패가 전체를 막지 않는 설계
4. **`failure_analyzer.py` 내 28건**: 분석 유틸리티는 원본 데이터가 부실할 수 있으므로 방어적 처리 적합

---

## 4. Pass 3 최종 판정

| Finding | Pass 1 | Pass 2 | Pass 3 최종 |
|---------|--------|--------|------------|
| XC-ERR-001 | P2 HIGH | P2 확인 | **P2** — telemetry 무조건 필요 |
| XC-ERR-002 | P2 HIGH | P2 확인 | **P2** — XC-ERR-001 sister |
| XC-ERR-003 | P3 MED | P3 확인 | **P3** — 비차단 경로 |
| XC-ERR-004 | P3 MED | P3 확인 | **P3** — XC-ERR-003 sister |
| XC-ERR-005 | P1 HIGH | P2 하향 | **P2** — 마이그레이션은 초기 1회성 |
| XC-ERR-006 | P1 HIGH | P2 하향 | **P2** — 마이그레이션은 초기 1회성 |
| XC-ERR-007 | P3 MED | P3 확인 | **P3** — 의도적 방어 패턴 |
| XC-ERR-008 | P3 LOW | P3 확인 | **P3** — logging.debug 존재 |
| XC-ERR-009 | P3 LOW | P3 확인 | **P3** — 의도적 비차단 |
| XC-ERR-010 | P3 LOW | P3 확인 | **P3** — 견고한 3단계 폴백 |
| XC-ERR-011 | P3 LOW | P3 확인 | **P3** — except 범위만 좁히면 됨 |
