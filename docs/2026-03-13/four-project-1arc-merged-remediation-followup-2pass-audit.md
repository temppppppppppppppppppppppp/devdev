# 4프로젝트 1Arc 병합 수정 Follow-Up 2PASS Audit

> 작성일: 2026-03-13
> 상태: closed
> 기준 SSOT: `docs/2026-03-13/four-project-1arc-merged-remediation-execution-ssot.md`
> 선행 문서: `docs/2026-03-13/four-project-1arc-merged-remediation-postfix-3pass-closure.md`

---

## 0. 최종 결론

follow-up 2PASS 결과, 이번 tranche의 retained `P0 / P1 / P2`는 없다.

- `E-3` integrity hardening은 `field_repair`와 `integrity_fail` 분리로 의미론이 정리됐다.
- `E-4` state tracker skip semantics는 benign early-arc와 실제 tracker gap을 구분하도록 정리됐다.
- 3PASS에서 발견된 test/fixture realism 문제는 대응 후 재검증되었다.

최종 확신도는 `95%`다.

---

## 1. Follow-Up 2PASS

### Pass 1. 대응 적합성 재검증

재확인 항목:

- `validate_arc_data_fields` helper 경로가 helper 부재 컨텍스트에서 잘못 발동하지 않는가
- deterministic repair가 더 이상 `data_missing`로 뭉뚱그려지지 않는가
- `prev_arcs`가 없는 early-arc에서 dead NPC skip이 benign하게 처리되는가
- `prev_arcs`가 있는데 `state_tracker`가 없을 때만 warning이 유지되는가

판정:

- 적합
- 3PASS에서 발견된 이슈는 모두 대응 경로와 직접 맞닿아 있고, 대응 이후 의미론 drift가 남지 않는다.

### Pass 2. 잔존 위험 재분류

검토 항목:

- 이 tranche에 아직 `P1/P2`로 남길 코드 결함이 있는가
- 남은 리스크가 runtime-only인지, 정적/회귀 단계에서도 남는지

판정:

- 새 retained `P0/P1/P2` 없음
- 남은 것은 runtime-only observation뿐이다.
  - `E-1` POV artifact refresh proof
  - `E-2` 0w형 Stage 4 continuity proof
  - `03`형 integrity debt가 fresh rerun에서 실제로 줄었는지 확인

이들은 이번 code-hardening tranche의 미해결 코드 결함이 아니라, 다음 실행 단계의 검증 과제다.

---

## 2. 근거

### 코드 변경 범위

- `modules/core/stage2_finalizer.py`
- `modules/domain/agents/unified_arc_validator.py`
- `tests/test_stage2_finalizer.py`
- `tests/test_arc_retry.py`
- `tests/test_unified_arc_validator.py`

### 검증 결과

```text
python -m py_compile modules/domain/agents/unified_arc_validator.py modules/core/stage2_finalizer.py tests/test_stage2_finalizer.py tests/test_unified_arc_validator.py tests/test_arc_retry.py
```

- 결과: 통과

```text
pytest -q tests/test_stage2_finalizer.py tests/test_state_service.py tests/test_unified_arc_validator.py tests/test_arc_retry.py
```

- 결과: `67 passed in 2.40s`

---

## 3. 최종 Findings

### Closed

- `03`형 Stage 2 deterministic repair와 integrity debt가 `data_missing`로 혼재되던 문제
- helper 부재 컨텍스트에서도 `validate_arc_data_fields` 경로가 가짜로 발동할 수 있던 test realism 문제
- `state_tracker 없음` warning이 benign early-arc skip과 실제 tracker gap을 구분하지 못하던 문제

### Observation

- fresh rerun 전까지는 이번 수정이 실제 `projects/03`형 로그에서 어떤 분포로 남는지까지는 증명되지 않았다.
- 그러나 이건 다음 실행 tranche의 runtime proof 문제이며, 현재 수정분의 retained defect는 아니다.

---

## 4. 확신도 Ledger

- `70`: SSOT 범위 구현 완료
- `+10`: focused regression `67 passed`
- `+5`: 3PASS 발견 이슈 대응 완료
- `+5`: 2PASS에서 retained `P0/P1/P2` 부재 확인
- `+5`: integrity / repair / skip semantics 분리 근거 확보

최종 확신도: `95%`

---

## 5. 닫힘 판단

이번 tranche는 `closed`다.

정리하면:

- 코드 수정은 SSOT 범위 안에서만 수행됐다.
- 3PASS 중 실제 문제가 발견되었고 바로 대응했다.
- 대응 후 2PASS에서 잔존 `P0/P1/P2`는 확인되지 않았다.
- 더 높은 확신도는 정적 감리나 추가 코드 수정이 아니라, fresh rerun 증거가 있어야만 올릴 수 있다.
