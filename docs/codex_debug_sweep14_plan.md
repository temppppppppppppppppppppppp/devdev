# Debug Sweep 14 — 로깅 레벨 + 데드 코드 정리

## Execution Status (2026-02-17)

- A-1 completed:
  - `modules/core/stage2_preflight.py`: success logs changed `warning -> info` for parallel completion and FourPhase PASS.
  - `modules/core/stage2_finalizer.py`: volume summary save completion log changed `warning -> info`.
- A-2 completed:
  - `modules/core/stage2_preflight.py`: patch fallback log changed `info -> warning`.
  - `modules/core/stage4_interview_round.py`: patch fallback log changed `info -> warning`.
- B-1 completed:
  - `modules/core/stage2_preflight.py`: removed dead return fields from `_preflight_arc_analysis`:
    - `enhanced_context`
    - `recent_patterns`
    - `preflight_injection`
- B-2 completed:
  - `tests/test_stage4_orchestrator.py`: removed duplicated assertion block in reject-path test.
- Contract-aligned test updates:
  - `tests/test_stage2_preflight.py`
  - `tests/test_stage2_preflight_helpers.py`
  - updated to validate new `_preflight_arc_analysis` return contract (4 keys only).
- Verification:
  - `pytest -q tests/test_stage4_orchestrator.py tests/test_stage2_preflight_helpers.py tests/test_stage2_finalizer.py tests/test_stage4_interview_round.py -x` -> `122 passed`
  - Expanded regression set (18 modules) -> `305 passed`

## Context

Sweep 11~13(총 12건) 완료 후, 5-에이전트 병렬 탐색으로 patch-mode(`396280b`) + legacy-removal(`dd825a8`) 커밋 교차 분석.
수동 코드 검증으로 **로깅 레벨 오류 5건 + 데드 코드 2건** 정리. (Guard 관련 3건은 오탐 확인)

---

## A-1 (MEDIUM): 성공 메시지가 WARNING 레벨 — 3건

성공/완료 이벤트에 `logging.warning()` 사용. 모니터링 도구에서 경고 노이즈 생성.

### A-1a: `stage2_preflight.py:110`

```python
# 현재
logging.warning("✅ [V66.1] arc_drive + preflight 병렬 완료")
# 수정
logging.info("✅ [V66.1] arc_drive + preflight 병렬 완료")
```

### A-1b: `stage2_preflight.py:532`

```python
# 현재
logging.warning(f"✅ [V60.77] FourPhase 성공! (내부 재시도: {pipeline_result.get('retries', 0)}회)")
# 수정
logging.info(f"✅ [V60.77] FourPhase 성공! (내부 재시도: {pipeline_result.get('retries', 0)}회)")
```

### A-1c: `stage2_finalizer.py:381`

```python
# 현재
logging.warning(f"📖 [V68] 볼륨 {_vol_no} 요약 저장 완료 ({len(_vol_result)}자)")
# 수정
logging.info(f"📖 [V68] 볼륨 {_vol_no} 요약 저장 완료 ({len(_vol_result)}자)")
```

---

## A-2 (MEDIUM): 실패 메시지가 INFO 레벨 — 2건

패치 실패 + 폴백 이벤트에 `logging.info()` 사용. 운영 중 실패 추적 누락 가능.

### A-2a: `stage2_preflight.py:499`

```python
# 현재
logging.info("[Patch Mode] Arc 패치 실패 → 전면 재생성 폴백")
# 수정
logging.warning("[Patch Mode] Arc 패치 실패 → 전면 재생성 폴백")
```

### A-2b: `stage4_interview_round.py:144`

```python
# 현재
logging.info("[Phase 3-5B] 패치 실패, full rewrite 폴백")
# 수정
logging.warning("[Phase 3-5B] 패치 실패, full rewrite 폴백")
```

---

## B-1 (LOW): `_preflight_arc_analysis()` 데드 리턴 키 3개

**파일**: `modules/core/stage2_preflight.py:398-406`

**문제**: 반환 dict에 7개 키 중 3개가 소비처 없음.
- `enhanced_context` — 오케스트레이터(L442-445)에서 미추출
- `recent_patterns` — 동상
- `preflight_injection` — 동상 (`cached_preflight_injection`으로 별도 관리됨)

**수정**: 데드 키 3개 제거:
```python
return {
    "refined_arc": refined_arc,
    "generation_method": generation_method,
    "constraint_block": constraint_block,
    "entity_registry_for_director": entity_registry_for_director,
}
```

---

## B-2 (LOW): 테스트 중복 단언문

**파일**: `tests/test_stage4_orchestrator.py:410-413`

**문제**: L404-407의 단언문과 L410-413이 완전 동일한 복사-붙여넣기.
```python
# L404-407 (원본)
assert result.should_return is True
assert result.final_manuscript is None
assert result.final_title is None
assert result.final_state_updates == {}
# L410-413 (중복 — 삭제 대상)
assert result.should_return is True
assert result.final_manuscript is None
assert result.final_title is None
assert result.final_state_updates == {}
```

**수정**: L410-413 삭제.

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1a | `modules/core/stage2_preflight.py` | 1줄 (warning→info) |
| A-1b | `modules/core/stage2_preflight.py` | 1줄 (warning→info) |
| A-1c | `modules/core/stage2_finalizer.py` | 1줄 (warning→info) |
| A-2a | `modules/core/stage2_preflight.py` | 1줄 (info→warning) |
| A-2b | `modules/core/stage4_interview_round.py` | 1줄 (info→warning) |
| B-1 | `modules/core/stage2_preflight.py` | 3줄 삭제 |
| B-2 | `tests/test_stage4_orchestrator.py` | 4줄 삭제 |

**총 ~12줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| Writer에 StyleGuard 누락 (HIGH) | ✗ 오탐 | ChiefWriter(실제 Stage 4 파이프라인)는 guard 미사용. 구 Writer는 외부 진입점용으로만 유지. 또한 StyleGuard가 `get_dungeon_rules_prompt()` 등 장르 전용 메서드 위임 안 함 → Writer에 주면 오히려 장르 프롬프트 손실 |
| WorkGuard 장르 메서드 위임 누락 | ✗ 설계 | WorkGuard는 `run_deep_validation()` 확장 전용. Writer의 `hasattr` 체크가 graceful fallback 처리 |
| pre_llm_validator 하드코딩 임계값 | ✗ 설계 | Phase 5-B에서 의도적으로 유지 결정 — `_threshold()` 대상은 validation.yaml 등재분만 |
| arc_draft_validator regex 주입 | ✗ 극저확률 | NPC/아이템 이름에 regex 특수문자 포함 가능성 거의 없음. LLM 생성 한글 명사만 사용 |
| `stage2_finalizer.py:433` WARNING 롤백 | ✗ 의도 | Director REJECT 롤백은 운영 경고 레벨 적절 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_stage4_orchestrator.py tests/test_stage2_preflight_helpers.py tests/test_stage2_finalizer.py tests/test_stage4_interview_round.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```
