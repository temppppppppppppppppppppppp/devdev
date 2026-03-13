# [MFS-T1] Stage2 Normalization / Flow Findings

> 작성일: 2026-03-13
> 상태: `PASS3 completed`
> 조사 모드: `static / read-only / code-and-test verification / UTF-8 only`
> 기준 오더: `main_a-facade-shim-detail-full-survey-audit-order.md`
> 실행 요약: `PASS1 후보 4건 -> PASS2 제거 2건 -> 최종 2건`

---

## 조사 범위

- `main_a.py`
  - `_normalize_tactical_text()`
  - `_is_tactical_doc_duplicate()`
  - `_normalize_flow_text()`
  - `_stage2_flow_guard()`
  - `_stage2_flow_guard_legacy()`
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_validation_pipeline.py`

## 필수 근거

- 읽은 테스트:
  - `tests/test_stage2_pipeline.py`
  - `tests/test_stage2_validation_pipeline.py`
  - `tests/test_stage2_preflight_helpers.py`
- 읽은 참조 문서:
  - `docs/stage_map/stage2.md`
  - `docs/2026-03-11/00-test-02-03-system-improvement-final-audit-codex.md`
  - `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md`
- 실행 검증:
  - `pytest -q tests/test_stage2_pipeline.py tests/test_stage2_validation_pipeline.py tests/test_stage2_preflight_helpers.py`
  - 결과: `146 passed in 3.02s`
- ad-hoc 재현:
  - `inspect.signature()`로 `main_a.py`/`Stage2Orchestrator`/`Stage2ValidationPipeline`의 duplicate threshold 기본값을 대조했다.
  - `SequenceMatcher` 유사도 `0.9508196721311475`인 near-duplicate 예제에서 `Stage2ValidationPipeline._is_tactical_doc_duplicate()`는 기본값으로 `True`, `threshold=0.98` 명시 시 `False`를 반환함을 확인했다.
  - `modules.core.narrative_structure_analyzer.NarrativeStructureAnalyzer.analyze()`를 `RuntimeError("boom")`로 monkeypatch한 뒤 `_stage2_flow_guard()`를 호출했을 때 `{'status': 'PASS', 'fallback': True}`가 반환됨을 확인했다.

## PASS 기록

- PASS 1:
  - 후보 1: duplicate helper 기본 threshold가 facade와 실제 Stage 2 consumer에서 다르다.
  - 후보 2: flow analyzer runtime exception이 legacy fallback 대신 `PASS`로 승격된다.
  - 후보 3: `_stage2_flow_guard_legacy()`의 annotation/list contract와 실제 str 수용 동작이 어긋난다.
  - 후보 4: `main_a.py` facade shim 5개가 직접 테스트되지 않아 drift가 가려진다.
- PASS 2:
  - 후보 3 제거: `modules/core/stage2_validation_pipeline.py:1142-1146`이 str/non-list를 방어하고, 현재 정상 consumer 경로도 list를 넘기므로 즉시 기능 결함으로 확정할 근거는 부족했다.
  - 후보 4 제거: direct test 부재는 명확하지만, 그것만으로 현재 동작 결함을 확정할 수는 없어 `coverage gap`으로만 유지했다.
- PASS 3:
  - facade default drift 1건, flow guard fallback semantics 1건만 `MFS-T1-*`로 채택했다.

## Finding Ledger

| ID | Severity | 상태 | 파일/함수 | 요약 |
|----|----------|------|-----------|------|
| MFS-T1-001 | P2 | confirmed | `main_a.py::_is_tactical_doc_duplicate`, `modules/core/stage2_orchestrator.py::_is_tactical_doc_duplicate`, `modules/core/stage2_validation_pipeline.py::_is_tactical_doc_duplicate` | facade 기본 threshold는 `0.98`인데 실제 Stage 2 duplicate guard 소비 경로는 `0.92`를 써 near-duplicate 판정 의미가 갈라진다 |
| MFS-T1-002 | P1 | confirmed | `main_a.py::_stage2_flow_guard`, `modules/core/stage2_validation_pipeline.py::_stage2_flow_guard` | flow analyzer runtime exception이 legacy fallback이 아니라 `status='PASS'`로 흡수되어 advisory 신호를 잃는다 |

## Final Findings

### [MFS-T1-001] P2 - facade duplicate threshold 기본값이 실제 Stage 2 duplicate guard 소비 경로와 다르다

1. ID
   - `MFS-T1-001`
2. Severity
   - `P2`
3. 현상 요약
   - `main_a.py` facade와 `Stage2Orchestrator` thin wrapper는 `_is_tactical_doc_duplicate(..., threshold=0.98)`를 public contract처럼 노출한다.
   - 그러나 실제 duplicate guard 소비 경로는 `Stage2ValidationPipeline.run_validation()` 내부에서 `_is_tactical_doc_duplicate()`를 threshold 인자 없이 호출하므로 pipeline 기본값 `0.92`를 사용한다.
   - 즉, 외부 facade를 직접 쓰는 호출자와 실제 Stage 2 pre-Director validation이 서로 다른 유사도 기준으로 중복 여부를 판단한다.
   - ad-hoc 재현에서도 유사도 `0.9508` 예제가 pipeline 기본값에서는 duplicate로, `0.98` 기준에서는 non-duplicate로 갈렸다.
4. 코드 근거
   - `main_a.py:2602-2604`는 facade default를 `0.98`로 고정한다.
   - `modules/core/stage2_orchestrator.py:935-942`도 wrapper default를 `0.98`로 유지한다.
   - `modules/core/stage2_validation_pipeline.py:963-989`는 실제 구현 default를 `0.92`로 둔다.
   - `modules/core/stage2_validation_pipeline.py:501-504`는 duplicate guard 소비 지점이 threshold를 명시하지 않음을 보여 준다.
   - `modules/core/stage2_orchestrator.py:553-557`, `919-921`는 현재 Stage 2 실제 소비가 `validation_pipeline.run_validation()`으로 직행함을 보여 준다.
5. downstream 영향 경계
   - `main_a.py`나 `Stage2Orchestrator` helper를 직접 호출하는 consumer는 기본적으로 더 보수적인 `0.98` 계약을 본다.
   - 반면 실제 Stage 2 duplicate guard advisory는 더 공격적인 `0.92`로 동작해, 직전 Arc와 완전히 동일하지 않은 near-duplicate도 `"직전 아크와 동일한 전술 설계"` 경고로 승격될 수 있다.
   - 이 drift는 hard crash를 만들지는 않지만, pre-Director advisory와 retry 유도 메시지를 과민하게 만들 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_validation_pipeline.py:101-107`은 exact match/empty case만 본다.
   - `tests/test_stage2_pipeline.py:567-585`도 exact match/clearly different/empty case만 본다.
   - `tests/test_stage2_validation_pipeline.py:186-191`, `tests/test_stage2_preflight_helpers.py:653-668`은 duplicate outcome을 `MagicMock(return_value=True)`로 고정해 threshold band를 검증하지 않는다.
   - `tests/` 전역 검색 기준 `main_a.py` facade `_is_tactical_doc_duplicate()`를 직접 검증하는 테스트는 없었다.
7. 기존 문서와의 중복 여부
   - duplicate status: `none`
   - `docs/2026-03-11/00-test-02-03-system-improvement-final-audit-codex.md`, `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md`, `docs/2026-03-13/main_a-control-plane-detail-consolidated-findings*.md`에서 이 threshold drift를 다룬 항목은 확인되지 않았다.
8. 권장 후속 조치
   - duplicate threshold를 single constant/SSOT로 올리고, facade/orchestrator/pipeline이 같은 기본값을 쓰게 맞춘다.
   - `run_validation()` duplicate guard call site에 threshold를 명시적으로 넘겨 public facade와 같은 계약으로 고정한다.
   - 회귀 테스트를 추가한다: `0.92 < similarity < 0.98` 구간 샘플이 pipeline/orchestrator/facade에서 동일한 판정을 내리는지 검증한다.

### [MFS-T1-002] P1 - flow analyzer runtime exception이 legacy fallback이 아니라 `PASS`로 흡수된다

1. ID
   - `MFS-T1-002`
2. Severity
   - `P1`
3. 현상 요약
   - `_stage2_flow_guard()`는 구조 분석기 import 실패(`ImportError`) 때만 `_stage2_flow_guard_legacy(normalized)`로 폴백한다.
   - 하지만 분석기가 import는 되었고 `analyze()` 호출 중 runtime exception이 나면 broad `except Exception`이 `{"status": "PASS", "fallback": True}`를 반환한다.
   - `run_validation()`은 `status == "REJECT"`일 때만 flow_guard advisory를 조립하므로, analyzer crash는 legacy guard 재평가도 하지 않고 advisory도 남기지 않는다.
   - facade `main_a.py::_stage2_flow_guard()`와 `Stage2Orchestrator::_stage2_flow_guard()`는 이 semantics를 그대로 노출한다.
4. 코드 근거
   - `main_a.py:2610-2612`는 facade가 `_stage2_orch._stage2_flow_guard()`를 그대로 위임한다.
   - `modules/core/stage2_orchestrator.py:948-954`는 orchestrator wrapper도 validation pipeline semantics를 그대로 노출한다.
   - `modules/core/stage2_validation_pipeline.py:1095-1134`는 `ImportError`만 legacy fallback으로 보내고, generic exception은 `{"status": "PASS", "fallback": True}`로 삼킨다.
   - `modules/core/stage2_validation_pipeline.py:431-499`는 `REJECT`일 때만 advisory를 붙이고 `PASS/fallback=True`는 추가 처리하지 않음을 보여 준다.
   - ad-hoc monkeypatch 재현에서 `NarrativeStructureAnalyzer.analyze()`가 `RuntimeError("boom")`를 던지자 `_stage2_flow_guard()`는 실제로 `{'status': 'PASS', 'fallback': True}`를 반환했다.
5. downstream 영향 경계
   - `docs/stage_map/stage2.md:8`, `18`, `144`, `217` 기준 Stage 2 semantic validators는 advisory 중심이다.
   - 따라서 flow analyzer crash를 `PASS`로 흡수하면, Director로 넘어가야 할 flow_guard 경고가 아예 사라진다.
   - `ImportError`와 달리 runtime failure는 legacy stagnation 검사도 재사용하지 않으므로, analyzer가 설치돼 있지만 내부 오류를 낸 환경이 가장 느슨한 판정을 받게 된다.
   - 영향 범위는 `main_a.py` facade, `Stage2Orchestrator._preflight_validation()`, `Stage2ValidationPipeline.run_validation()` 전체다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_stage2_validation_pipeline.py:121-139`는 legacy helper 자체의 PASS/REJECT만 검증한다.
   - `tests/test_stage2_pipeline.py:641-658`는 valid beats에서 `status` key 존재만 확인하고, analyzer runtime failure semantics는 보지 않는다.
   - `tests/test_stage2_validation_pipeline.py:174-183`, `tests/test_stage2_preflight_helpers.py:629-647`는 `_stage2_flow_guard()`를 `MagicMock(...REJECT...)`로 바꿔 advisory 조립만 확인한다.
   - analyzer `ImportError`와 runtime exception을 구분해 회귀 고정하는 테스트는 없다.
7. 기존 문서와의 중복 여부
   - duplicate status: `none`
   - 기존 감사 문서들은 Stage 2가 advisory 중심이라는 큰 의미론은 다루지만, `_stage2_flow_guard()`의 runtime-exception branch가 legacy fallback을 우회해 `PASS`를 반환하는 구체 surface는 다루지 않았다.
8. 권장 후속 조치
   - generic exception branch도 `_stage2_flow_guard_legacy(normalized)`로 보내거나, 최소한 `status='REJECT'` 또는 별도 diagnostic status로 승격해 advisory가 사라지지 않게 해야 한다.
   - `fallback=True`만으로는 downstream consumer가 의미를 보존하지 못하므로, `run_validation()`에서 fallback branch를 별도 advisory source로 기록하는 안전장치가 필요하다.
   - 회귀 테스트를 추가한다: `ImportError`와 runtime exception 각각에서 legacy fallback/advisory semantics가 동일하게 유지되는지 검증한다.

## Rejected Candidates

| 후보 | PASS2 판정 | 근거 |
|------|------------|------|
| `_stage2_flow_guard_legacy()`의 annotation이 `list`인데 구현은 `str`도 받으므로 즉시 contract bug다 | removed | `modules/core/stage2_validation_pipeline.py:1142-1146`이 str/non-list를 방어하고, 현재 정상 consumer 경로는 `_stage2_flow_guard()`가 만든 list를 전달한다. annotation rough edge는 맞지만 현시점 즉시 오동작 근거는 부족했다. |
| non-string 입력을 `""`로 정규화하는 helper 동작이 현재 data corruption이다 | removed | `modules/core/stage2_validation_pipeline.py:953-961`, `991-997`와 `tests/test_stage2_pipeline.py:550-559`, `605-614`, `tests/test_stage2_validation_pipeline.py:92-99`는 empty-string sentinel을 현재 의도된 계약으로 잠그고 있다. 현재 범위에서는 semantic drift보다 의도된 방어 동작으로 보는 편이 타당했다. |

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `main_a.py` facade shim 직접 회귀 | 테스트 공백 | 실제 `SovereignApp` bound method로 `_normalize_*`, `_is_tactical_doc_duplicate`, `_stage2_flow_guard*` 5개 shim이 orchestrator/pipeline과 동일 contract를 유지하는지 검증 |
| duplicate similarity band | 테스트 공백 | `0.92 < similarity < 0.98` 구간 샘플을 fixture로 고정해 facade/orchestrator/pipeline/duplicate guard advisory가 동일한 판정을 내리는지 확인 |
| flow analyzer failure semantics | 테스트 공백 | analyzer `ImportError`, runtime exception, 정상 PASS/WARNING/STAGNATION 각 branch에서 legacy fallback/advisory 처리 결과를 분기별로 고정 |

## 마감 체크

- 코드 근거 포함
- downstream 영향 경계 포함
- 현재 테스트 근거 또는 테스트 부재 포함
- 기존 문서와의 중복 여부 포함
- `PASS1 -> PASS2 -> PASS3` 요약 포함
