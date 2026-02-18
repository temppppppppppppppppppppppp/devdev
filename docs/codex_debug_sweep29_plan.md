# Debug Sweep 29 — 검증 우회 (silent PASS) + 점수 엣지케이스 + 스레드 안전성

## Context

Sweep 28(11건) 완료 후, 5-에이전트 병렬 탐색으로 새로운 패턴 탐색:
스레드 안전성, YAML key drift, 점수 계산 엣지, except 에러 삼킴, DI 콜백 배선.
수동 코드 검증으로 **확인된 실제 버그 8건** 정리.
- YAML drift: 0건 크래시 위험 (45+ dead YAML키, 전량 폴백 정상)
- DI 콜백: 0건 프로덕션 위험 (from_app 배선 전량 정상, 테스트 환경에서만 리스크)

---

## A-1 (HIGH): `continuity_manuscript.py:309` — LLM 실패 시 연속성 검증 무조건 PASS → 사망NPC 등장 미탐지

**파일**: `modules/domain/agents/continuity_manuscript.py:309-331`

**문제**:
```python
except Exception as e:
    logging.warning(f"🚨 [ContinuityInspector] 원고 LLM 검증 실패: {e}")
    return {
        "decision": "PASS",       # ← LLM 실패 = 무조건 PASS
        "severity": "NONE",
        "violations": [],
        ...
    }
```
- `inspect_manuscript()` 전체를 감싸는 except → LLM 타임아웃, API 429, JSON 파싱 실패 등 모든 예외에서 PASS
- 사망 NPC 등장, 아이템 모순, 블루프린트 이탈 등 연속성 위반이 탐지 불가
- 호출자 (Director audit) 입장에서 정상 PASS와 구분 불가 — `degraded` 플래그 없음

**수정** — `degraded` 플래그 추가 + 호출자 인지:
```python
except Exception as e:
    logging.warning(f"🚨 [ContinuityInspector] 원고 LLM 검증 실패: {e}")
    _base = {
        "decision": "PASS",
        "severity": "MINOR",
        "degraded": True,           # ← 추가: 호출자가 탐지 가능
        "degraded_reason": str(e),  # ← 추가: 사유
        ...
    }
```
`warnings` 리스트에 "LLM 검증 실패" 경고는 이미 포함 — `degraded` 플래그만 추가하면 호출자에서 감지 가능.

**테스트**: LLM 호출 예외 시 반환값에 `degraded=True` 포함 검증

---

## A-2 (HIGH): `director_auditor.py:91-93` — 장르 가드 크래시 → 위반 0건 반환

**파일**: `modules/domain/agents/director_auditor.py:91-93`

**문제**:
```python
except (ValueError, KeyError, IndexError) as e:
    logging.warning(f"⚠️ [V66] 장르 검증 오류: {str(e)[:50]}")
    return {"has_critical": False, "violations": [], "summary": "", "feedback": ""}
```
- `run_deep_validation()` 내부에서 `ValueError/KeyError/IndexError` 발생 시 → 위반 0건 반환
- 이 3가지는 guard 데이터 구조 불일치 시 가장 흔한 예외 → 실제 guard 실패를 "문제 없음"으로 보고
- Director가 장르 위반 없다고 판단 → 금기어/필수 개념 위반 원고 통과

**수정** — `degraded` 플래그 추가:
```python
except (ValueError, KeyError, IndexError) as e:
    logging.warning(f"⚠️ [V66] 장르 검증 오류: {str(e)[:50]}")
    return {
        "has_critical": False,
        "violations": [],
        "summary": f"장르 검증 실패: {str(e)[:100]}",
        "feedback": "장르 검증 중 오류 발생 — 수동 확인 권장",
        "degraded": True,
    }
```

**테스트**: `run_deep_validation` ValueError 시 반환값에 `degraded=True` + 비어있지 않은 summary 검증

---

## A-3 (MEDIUM): `scoring_validator.py:260` — 음수 LLM 점수 미클램핑 → total_score 왜곡

**파일**: `modules/validation/scoring_validator.py:260`

**문제**:
```python
_val["score"] = min(int(_val["score"]), int(_val["max"]))
# ↑ 상한만 클램핑. LLM이 score=-3 반환 시 → min(-3, 15) = -3 통과
```
- L127: `total_score = sum(...)` — 음수 점수가 합산에 포함 → total_score 하락
- L136: `percentage = (total_score / max_score) * 100` — 음의 percentage 가능
- LLM 적대적 응답이나 파싱 오류 시 현실적으로 발생

**수정**:
```python
_val["score"] = max(0, min(int(_val["score"]), int(_val["max"])))
```

**테스트**: `score=-5, max=15` 입력 시 `_val["score"] == 0` 검증

---

## A-4 (MEDIUM): `scoring_validator.py:615,638` — float 0.5 페널티 → integer 파이프라인 오염

**파일**: `modules/validation/scoring_validator.py:615,638`

**문제**:
```python
sensory_penalty = 0.5                         # L615: float
final_score = max(1, base_score - sensory_penalty)  # L638: 4 - 0.5 = 3.5 (float!)
```
- `base_score`는 int(1-5), `sensory_penalty`가 0.5일 때 `final_score`가 float(3.5)
- L127: `total_score = sum(...)` → float (68.5)
- L139: 메시지 `"68.5/100점"` — integer 기대 형식 위반
- 기능적 영향은 경미하지만, 일관성 위반

**수정** — 정수 페널티로 변경:
```python
sensory_penalty = 1  # 시각 편중 시 1점 감점 (기존 0.5 → 1로 통일)
```
또는 float 유지하되 최종값 int 변환:
```python
final_score = int(max(1, base_score - sensory_penalty))
```

**테스트**: 시각 편중(visual > 70%) 원고에서 `final_score`가 int 타입인지 검증

---

## B-1 (MEDIUM): `stage4_context_builder.py:254-259` — mandatory_context 실패 시 빈 문자열 → Writer 맹점 실행

**파일**: `modules/core/stage4_context_builder.py:254-259`

**문제**:
```python
mandatory_context = ""
try:
    mandatory_context = _build_writer_mandatory_context(_db, _bible, next_ep)
except Exception as e:
    self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
    # mandatory_context stays ""
```
- Chief Writer가 HUD/인벤토리/NPC 정보 없이 원고 생성
- 존재하지 않는 아이템 사용, 부상 무시, NPC 관계 모순 발생 가능
- downstream 연속성 검증에서 잡히지만, 불필요한 재작성 라운드 발생

**수정** — 경고를 mandatory_context에 직접 포함:
```python
except Exception as e:
    self.ctx.ui.log(f"   ⚠️ Mandatory Context 실패 (비치명): {e}")
    mandatory_context = "[⚠️ 필수 컨텍스트 로딩 실패 — 이전 에피소드 상태를 반드시 참고하여 연속성 유지]"
```

**테스트**: `_build_writer_mandatory_context` 예외 시 `mandatory_context`에 경고 문자열 포함 검증

---

## B-2 (MEDIUM): `base_agent.py:351` — `_rotation_count = 0` 락 없이 쓰기 → 키 회전 오작동

**파일**: `modules/domain/agents/base_agent.py:351`

**문제**:
```python
# L351 — ask() 내부, 락 없음
if current_model == self.primary_model:
    BaseAgent._rotation_count = 0  # ← 베어 쓰기

# L190 — _try_rotate_key() 내부, _rotation_lock 보유
cls._rotation_count += 1
```
- 앙상블 생성기(3 스레드 병렬)에서 Thread A가 `_rotation_count = 0` 리셋하는 동안
- Thread B가 `_try_rotate_key`에서 `_rotation_count += 1` 수행
- 결과: 회전 카운트 불일치 → 불필요한 키 회전 또는 회전 누락

**수정** — 락 내에서 리셋:
```python
if current_model == self.primary_model:
    with BaseAgent._rotation_lock:
        BaseAgent._rotation_count = 0
```

**테스트**: `_rotation_count` 리셋이 `_rotation_lock` 내에서 수행되는지 코드 검사

---

## B-3 (LOW): `blocking_validator.py:152-164` — 일관성 체크 크래시 → `passed:True` (degraded 무시)

**파일**: `modules/validation/blocking_validator.py:152-164`

**문제**:
```python
except Exception as e:
    return {"check": "relationship_consistency", "passed": True, "degraded": True, ...}
```
- `degraded: True` 플래그 포함이지만, 호출자 `validate()` L88-94에서 `passed` 필드만 확인
- `degraded` 무시 → 관계/정보 일관성 위반이 Director에 전달되지 않음
- [C-3] 의도적 degradation이지만 호출자 미인지

**수정** — `validate()` 내에서 degraded 검사 + 경고 전파:
```python
# validate() 내 check 순회 루프에서:
if check.get("degraded"):
    logging.warning(f"[BlockingValidator] {check['check']} 검증 degraded: {check.get('error', '')}")
    # failures에는 추가하지 않지만 warnings에 추가
    result.setdefault("warnings", []).append(f"degraded: {check['check']}")
```

**테스트**: degraded 체크 결과가 warnings에 포함되는지 검증

---

## B-4 (LOW): `continuity_manuscript.py:184-192` — `incarnation_type` 추출 실패 시 로깅 없는 `pass`

**파일**: `modules/domain/agents/continuity_manuscript.py:184-192`

**문제**:
```python
except Exception:
    pass  # ← 로깅 없음
return ""
```
- 회귀자/전생자 주인공의 `incarnation_type` 추출 실패 → 빈 문자열 반환
- 연속성 검증에서 미래 지식 참조를 위반으로 판정 → 불필요한 REJECT
- 예외 원인 추적 불가 (로깅 없음)

**수정**:
```python
except Exception as e:
    logging.warning(f"[ContinuityManuscript] incarnation_type 추출 실패: {e}")
return ""
```

**테스트**: 예외 발생 시 로그에 "incarnation_type 추출 실패" 포함 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `modules/domain/agents/continuity_manuscript.py` | except 블록에 `degraded=True` 2줄 추가 × 2경로 |
| A-2 | `modules/domain/agents/director_auditor.py` | except 반환값에 `degraded=True` + summary 수정 |
| A-3 | `modules/validation/scoring_validator.py` | 1줄 수정 (`max(0, min(...))`) |
| A-4 | `modules/validation/scoring_validator.py` | 1줄 수정 (`int()` 래핑 또는 penalty 정수화) |
| B-1 | `modules/core/stage4_context_builder.py` | except 내 fallback 문자열 1줄 |
| B-2 | `modules/domain/agents/base_agent.py` | 리셋 라인에 `with _rotation_lock:` 2줄 |
| B-3 | `modules/validation/blocking_validator.py` | degraded 검사 + warnings 추가 3줄 |
| B-4 | `modules/domain/agents/continuity_manuscript.py` | `pass` → `logging.warning(...)` 1줄 |

**총 ~20줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| YAML 45+ dead keys | ✗ 정보 | 전량 폴백 정상 작동. 크래시 위험 0 |
| DI 콜백 14건 None 가드 미비 | ✗ 테스트 전용 | `from_app()` 프로덕션 배선 전량 정상 |
| `scoring_validator.py:783` percentage vs point 임계 | ✗ 설계 | weighted_percentage는 0-100% 정규화. 70% 임계는 의도된 동작 |
| `pacing_analyzer.py:164` dead else | ✗ 스타일 | `total_breaks >= 0` 항상 True — 기능 무관 (Sweep24에서 이미 확인) |
| `quality_dashboard.py:463` population vs sample variance | ✗ 경미 | window=5에서 차이 무시 가능. 임계값 조정으로 보상 |
| `_quota_exhausted_models` mixed-lock mutation | ✗ 경미 | CPython GIL이 dict 개별 연산 보호. 논리적 레이스지만 실질 영향: 캐시 미스 수준 |
| `batch_validator.stats` 락 없이 쓰기 | ✗ 경미 | executor.map() 완료 후 메인 스레드에서 쓰기 → 워커와 동시 아님 |
| `v0128_orchestrator` lazy-init TOCTOU | ✗ 경미 | Self-Consistency에서만 발생. 실질적 영향: 동일 config로 재생성 |
| `_key_rotation_pending` read-check-act | ✗ 오탐 | _try_rotate_key 내부에서 이중 진입 방지 정상 처리 |
| `stage2_validation_pipeline.py:658` NarrativeAnalyzer PASS 폴백 | ✗ 설계 | 비차단 원칙 적용. analyzer 예외 시 arc 생성 중단 방지 의도 |
| `emotion_tracker.yaml` 중복 키 | ✗ 비활성 | 해당 모듈이 PromptLoader 미사용 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_director_modules.py tests/test_scoring_validator.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Update (2026-02-18)

Status: completed for Sweep 29 scope.

Applied items:
- A-1 `modules/domain/agents/continuity_manuscript.py`: LLM failure path now returns degraded metadata and warning propagation.
- A-2 `modules/domain/agents/director_auditor.py`: genre-specific validation exception path now returns degraded payload with summary/feedback.
- A-3 `modules/validation/scoring_validator.py`: score clamp now enforces non-negative lower bound.
- A-4 `modules/validation/scoring_validator.py`: show-dont-tell penalty path now keeps integer score.
- B-1 `modules/core/stage4_context_builder.py`: mandatory context failure now injects fallback warning text.
- B-2 `modules/domain/agents/base_agent.py`: rotation counter reset now protected by `_rotation_lock`.
- B-3 `modules/validation/blocking_validator.py`: degraded checks are surfaced as validator warnings.
- B-4 `modules/domain/agents/continuity_manuscript.py`: incarnation extraction exception now logs warning.

Additional repair during execution:
- `modules/domain/agents/director_auditor.py` was recovered to a compilable state after prior encoding corruption.
- Compatibility strings restored so existing director tests expecting Korean keywords pass (e.g. `"오류"`, `"분량 미달"`).

Verification run:
- `python -m pytest tests/test_sweep29.py -q -x` -> `8 passed`
- `python -m pytest tests/test_director_modules.py tests/test_continuity_modules.py tests/test_stage4_context_builder.py tests/test_stage2_validation_pipeline.py -q -x` -> `168 passed`
- `python -m pytest tests/ -q -p no:capture` -> `2028 passed, 68 xfailed, 1 warning`

Notes:
- test runner output includes interactive/log prints and a post-run traceback print from mocked ImportError path; it did not fail pytest (exit code 0).
