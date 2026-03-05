# PASS_WITH_FIX 전면 감사 코덱스 오더

> 작성일: 2026-03-04
> 트리거: "pass with fix 이거 잘 안 되는 거 같음. 전면조사."
> 범위: Stage 2 / Stage 3 / Stage 4 전 경로

---

## 0. 현재 구조 요약

### Verdict 3단계

| Verdict | 조건 | 후속 |
|---------|------|------|
| PASS | 모순 0건 + 90점+ | 저장 |
| PASS_WITH_FIX | 모순 MINOR + 90점+ | fix_scope 기반 수정 → 재심사 |
| REJECT | 70점 미만 or CRITICAL/MAJOR | 재생성 |

### fix_scope 3-tier

| fix_scope | 의미 | 실행 경로 |
|-----------|------|----------|
| inplace | 국소 수정 (LLM 1회) | InPlace 패치 → 재심사 (최대 3회) |
| partial | 1후보 집중 재생성 | 즉시 break → REJECT → retry |
| full | 전면 재설계 | 즉시 break → REJECT → retry |

### fix_scope 결정 주체
**LLM(Director)이 100% 결정**. Python은 값을 읽어 라우팅만.
기본값 폴백: `_current_audit_result.get("fix_scope", "inplace")` — Director가 미반환 시 inplace로 간주.

---

## 1. Stage 2 (Arc) — PASS_WITH_FIX 흐름

### 진입 경로

```
stage2_orchestrator.stage_2_arcs_async_logic()
  └─ for attempt in range(max_attempts):
       ├─ FourPhase.generate() → Arc 생성
       ├─ ValidationPipeline.run_validation() → 검증
       └─ Finalizer.run_finalize()
            └─ director.audit_strategic_plan() → verdict
                 └─ PASS_WITH_FIX 시:
                      └─ for _fix_i in range(3):   ← InPlace 루프
                           ├─ _inplace_patch_arc()  (LLM 1회)
                           └─ director.audit_strategic_plan() (재심사)
```

### 핵심 코드 위치

| 단계 | 파일 | 라인 | 메서드 |
|------|------|------|--------|
| Director 심사 | stage2_finalizer.py | L178-190 | director.audit_strategic_plan() |
| PASS_WITH_FIX 분기 | stage2_finalizer.py | L260-370 | _d_decision == "PASS_WITH_FIX" |
| fix_scope 분기 | stage2_finalizer.py | L268-271 | partial/full → break |
| InPlace 패치 | four_phase_arc_generator.py | L613-668 | _inplace_patch_arc() |
| 재심사 | stage2_finalizer.py | L293-315 | director.audit_strategic_plan() |
| 성공 확정 | stage2_finalizer.py | L346-355 | _fix_ok → PASS 전환 |
| 실패 전환 | stage2_finalizer.py | L356-370 | REJECT + fix_scope 보존 |

### 재심사 결과 분기

| 재심사 verdict | 처리 |
|---------------|------|
| PASS (점수≥90) | _fix_ok=True, break, Arc 확정 |
| PASS (점수<90) | break, patch 종료 → REJECT |
| PASS_WITH_FIX | _current_arc 갱신, 다음 반복 |
| REJECT | break → REJECT |

### QualityGate 관계
- PASS_WITH_FIX는 QualityGate **bypass** (stage2_finalizer.py L363-380)
- 재심사 PASS에서만 점수 < 90 체크

---

## 2. Stage 3 (Blueprint) — PASS_WITH_FIX 흐름

### 진입 경로

```
stage3_orchestrator._run_blueprint_pipeline()
  └─ three_phase_blueprint_generator.generate_optimized_blueprint()
       └─ for retry in range(max_retries+1):    ← 생성 루프 (최대 10회)
            ├─ [InPlace 진입 조건 체크]
            │   ├─ _use_inplace = True → _inplace_patch_blueprint()
            │   └─ _use_inplace = False → ensemble.generate_ensemble()
            ├─ validator.validate() → verdict
            └─ PASS_WITH_FIX 시:
                 └─ for _fix_i in range(3):      ← InPlace 루프
                      ├─ _inplace_patch_blueprint() (LLM 1회)
                      └─ validator.validate(all_candidates=None) (재심사)
```

### 핵심 코드 위치

| 단계 | 파일 | 라인 | 메서드 |
|------|------|------|--------|
| InPlace 진입 조건 | three_phase_blueprint_generator.py | L226-229 | _use_inplace 판단 |
| InPlace 패치 | three_phase_blueprint_generator.py | L638-722 | _inplace_patch_blueprint() |
| PASS_WITH_FIX 루프 | three_phase_blueprint_generator.py | L447-562 | verdict == "PASS_WITH_FIX" |
| fix_scope 분기 | three_phase_blueprint_generator.py | L457-459 | partial/full → break |
| 재심사 | three_phase_blueprint_generator.py | L478-520 | validator.validate(all_candidates=None) |
| 실패 → REJECT | three_phase_blueprint_generator.py | L527-562 | continue (retry 진입) |
| 오케스트레이터 성공 | stage3_orchestrator.py | L363-367 | PASS_WITH_FIX → _handle_success |

### 재심사 경로 차이 (Stage3 특수)

`validator.validate(all_candidates=None)` 호출 시:
- all_candidates=None → **단일 후보 경로** → `director.audit_manuscript()` 호출
- all_candidates=[...] → **비교 경로** → `director.compare_and_select_blueprint()` 호출

### Stage3 오케스트레이터의 PASS_WITH_FIX 처리

```python
# stage3_orchestrator.py L363-367
if blueprint and pipeline_result.get("final_verdict") in (
    "PASS", "PASS_WITH_FIX", "PASS_WITH_WARNING",
):
    return self._handle_success(...)
```

**중요**: Stage3 오케스트레이터는 `final_verdict`가 PASS_WITH_FIX이면 **성공으로 저장**.
즉, three_phase_blueprint_generator 내부의 InPlace 루프가 실패하더라도
`final_verdict`가 아직 PASS_WITH_FIX로 남아 있으면 **수정 안 된 채 저장될 수 있음**.

→ **잠재적 문제점 #1**: InPlace 루프 실패 시 verdict가 REJECT로 바뀌는지 확인 필요.

---

## 3. Stage 4 (원고) — PASS_WITH_FIX 흐름

### 진입 경로

```
stage4_interview_round.run()
  └─ _process_verdict()
       ├─ QualityGate: PASS + 점수<90 → REJECT (PASS_WITH_FIX bypass)
       └─ PASS_WITH_FIX 시:
            └─ _execute_pass_with_fix_loop()   ← InPlace 루프
                 └─ for _fix_i in range(3):
                      ├─ chief_writer.inplace_patch() (LLM 1회)
                      └─ director.select_and_judge_ensemble([패치본]) (재심사)
```

### 핵심 코드 위치

| 단계 | 파일 | 라인 | 메서드 |
|------|------|------|--------|
| Director 심사 | director_ensemble.py | L548-954 | select_and_judge_ensemble() |
| verdict 반환 | stage4_interview_round.py | L1240-1285 | _process_verdict() |
| PASS_WITH_FIX 루프 | stage4_interview_round.py | L1063-1209 | _execute_pass_with_fix_loop() |
| fix_scope 분기 | stage4_interview_round.py | L1098-1105 | partial/full → break |
| InPlace 패치 | chief_writer.py | L777-877 | inplace_patch() |
| JSON 파싱 보호 | chief_writer.py | L826-869 | TF-47: _outer_start > 0 |
| 재심사 | stage4_interview_round.py | L1143-1156 | select_and_judge_ensemble([1후보]) |
| state_updates merge | stage4_interview_round.py | L1125-1127 | {**기존, **patch} |
| 성공 확정 | stage4_interview_round.py | L1196-1199 | verdict="PASS" |
| 실패 전환 | stage4_interview_round.py | L1200-1209 | verdict="REJECT" + fix_scope 보존 |

### InPlace 패치 상세 (chief_writer.py L777-877)

1. 프롬프트: `PATCH_MODE_PROMPT` (chief_writer.yaml L76-108)
2. LLM 호출: temperature=0.3, thinking_level="medium"
3. 최소 응답 길이: 2000자
4. JSON 파싱 2단계:
   - 1단계: 전체 JSON 파싱 (content/text/manuscript/patched_text 키)
   - 2단계: rfind("patch_state_updates") 마커 방식 폴백
   - TF-47: `_outer_start > 0` 조건으로 원고 전체 삭제 방지
5. 반환: `[{"manuscript": str, "strategy": "inplace_patch", "state_updates": dict}]`

### Stage4 재심사 특수사항

Stage4 재심사는 `select_and_judge_ensemble([단일후보])`를 호출:
- 원래 3후보 비교 선택용 메서드에 1후보만 전달
- Director가 "최선 선택" 대신 "단일 심사"를 수행해야 함

→ **잠재적 문제점 #2**: 비교 선택 프롬프트에 1후보만 들어가면 Director 판정 패턴이 달라질 수 있음.

---

## 4. 잠재적 문제점 종합

### P1. Stage3 InPlace 루프 실패 시 verdict 미전환

**위치**: three_phase_blueprint_generator.py L527-562
**증상**: InPlace 3회 실패 후 verdict="REJECT"로 전환 + `continue`로 retry 진입.
하지만 retry도 전부 소진(max_retries=9)하면 `pipeline_result["final_verdict"]`는?

**확인 필요**: generate_optimized_blueprint()의 반환값에서 final_verdict가 REJECT로 정확히 설정되는지.
만약 PASS_WITH_FIX가 그대로 남으면, stage3_orchestrator가 수정 안 된 Blueprint를 성공으로 저장.

### P2. Stage4 재심사에서 select_and_judge_ensemble([1후보]) 사용

**위치**: stage4_interview_round.py L1143-1156
**증상**: 3후보 비교용 메서드에 1후보만 전달. Director 프롬프트가 "후보 A/B/C 중 최선을 선택하라"인데
1개만 있으면 비교 없이 자동 PASS할 수 있음. 또는 프롬프트 오류로 파싱 실패 가능.

**확인 필요**: select_and_judge_ensemble()가 candidates=1일 때 정상 작동하는지.
Stage2는 audit_strategic_plan() (단일 심사용), Stage3는 validator.validate(all_candidates=None) (단일 경로)를 쓰는데,
Stage4만 비교 메서드를 쓰고 있음 — 설계 의도인지 실수인지 확인.

### P3. fix_scope 기본값 "inplace" 강제

**위치**: 전 Stage 공통
**증상**: Director가 fix_scope를 반환하지 않으면 기본값 "inplace"로 처리.
모순이 심각한데 fix_scope 누락 시 inplace로 시도 → 실패 → REJECT → 불필요한 LLM 호출 낭비.

**확인 필요**: 실전 로그에서 fix_scope=""(빈 문자열) 또는 누락 빈도.

### P4. InPlace 패치 후 원고 길이 < 2000자 강제 실패

**위치**: stage4_interview_round.py L1117-1119
**증상**: 패치 결과가 2000자 미만이면 무조건 실패. 하지만 장르에 따라 짧은 원고(1500자)가
정상일 수 있음. 현재 하드코딩.

### P5. partial/full → 즉시 REJECT 전환의 의미

**위치**: 전 Stage 공통
**증상**: Director가 PASS_WITH_FIX + fix_scope="partial"을 반환하면:
1. InPlace 루프 즉시 break
2. verdict = REJECT로 전환
3. retry 경로로 위임

이때 retry 경로에서 fix_scope="partial"을 **실제로 소비하는 코드가 있는지?**
Stage4에서 retry 시 `_use_partial` 분기가 존재하는지 확인 필요.

### P6. 재심사에서 PASS_WITH_FIX → 다시 PASS_WITH_FIX → 반복

**위치**: 전 Stage 공통
**증상**: InPlace 패치 후 재심사에서 또 PASS_WITH_FIX가 나오면 다음 반복 진입.
3회 전부 PASS_WITH_FIX면 _fix_ok=False → REJECT. 하지만 마지막 패치본이
원본보다 나을 수 있는데 폐기됨.

**확인 필요**: Stage2 finalizer는 _current_arc = _patched로 갱신하지만,
Stage4에서 _current_ms = _patched_ms로 갱신 후 최종 폐기 시 원본으로 돌아가는지 패치본으로 가는지.

### P7. Stage2 _inplace_patch_arc() 반환값 검증 부족

**위치**: four_phase_arc_generator.py L613-668
**확인 필요**: 패치된 Arc에서 필수 필드(arc_end_state 등) 누락 시 처리.
원본 필드 병합 로직이 있는지.

---

## 5. 스테이지별 흐름 비교표

| 항목 | Stage 2 | Stage 3 | Stage 4 |
|------|---------|---------|---------|
| **패치 대상** | Arc (JSON) | Blueprint (JSON) | 원고 (텍스트) |
| **패치 메서드** | _inplace_patch_arc() | _inplace_patch_blueprint() | chief_writer.inplace_patch() |
| **재심사 메서드** | audit_strategic_plan() | validator.validate(all_candidates=None) | select_and_judge_ensemble([1후보]) |
| **재심사 일관성** | 단일 심사 ✅ | 단일 경로 ✅ | 비교 메서드에 1후보 ⚠️ |
| **최대 패치 횟수** | 3회 | 3회 | 3회 |
| **QualityGate bypass** | ✅ | ✅ | ✅ |
| **실패 → REJECT** | ✅ fix_scope 보존 | ✅ continue (retry) | ✅ fix_scope 보존 |
| **partial/full 처리** | break → REJECT | break → REJECT + continue | break → REJECT |
| **state_updates merge** | N/A (Arc) | N/A (Blueprint) | ✅ TF-46 |
| **JSON 파싱 보호** | 부분 (원본 병합) | 부분 (원본 병합 + pydantic) | TF-47 (rfind 보호) |

---

## 6. 진단 계획

### Phase 1: 코드 정적 감사 (P1~P7)

각 문제점에 대해 실제 코드 경로 추적 + 테스트 시나리오 도출.

| ID | 문제 | 심각도 | 확인 방법 |
|----|------|--------|----------|
| P1 | Stage3 final_verdict 미전환 | **HIGH** | three_phase_blueprint_generator 반환값 추적 |
| P2 | Stage4 재심사 비교 메서드 오용 | **HIGH** | select_and_judge_ensemble 1후보 처리 확인 |
| P3 | fix_scope 기본값 inplace 강제 | MEDIUM | 실전 로그/Director 스키마 확인 |
| P4 | 원고 2000자 하드코딩 | LOW | 장르별 최소 원고 길이 확인 |
| P5 | partial → retry 시 소비 코드 부재 | **HIGH** | Stage4 retry 경로 _use_partial 확인 |
| P6 | 3회 PASS_WITH_FIX 후 패치본 폐기 | MEDIUM | 최종 반환 원고가 원본인지 패치본인지 |
| P7 | Stage2 패치 Arc 필수 필드 검증 | LOW | _inplace_patch_arc 반환값 구조 |

### Phase 2: 수정 패치

P1 → P2 → P5 순서로 HIGH 이슈부터 패치.
각 패치 후 기존 테스트 3,245 passed 유지 확인.

---

## 7. 참고 파일 목록

| 파일 | 역할 |
|------|------|
| modules/core/stage2_finalizer.py | Stage2 PASS_WITH_FIX 루프 |
| modules/domain/agents/four_phase_arc_generator.py | _inplace_patch_arc() |
| modules/core/stage3_orchestrator.py | Stage3 verdict 분기 |
| modules/core/three_phase_blueprint_generator.py (*) | Stage3 PASS_WITH_FIX 루프 + _inplace_patch_blueprint() |
| modules/core/stage4_interview_round.py | Stage4 _execute_pass_with_fix_loop() |
| modules/domain/agents/chief_writer.py | Stage4 inplace_patch() |
| modules/domain/agents/director_ensemble.py | select_and_judge_ensemble() |
| modules/domain/agents/director_auditor.py | audit_strategic_plan(), audit_manuscript() |
| modules/validation/unified_blueprint_validator.py | validate() 2경로 분기 |
| modules/core/response_schemas.py | PASS_WITH_FIX 스키마 |
| config/prompts/director.yaml | Director 프롬프트 (PASS_WITH_FIX 지시) |
| config/prompts/chief_writer.yaml | PATCH_MODE_PROMPT |
| config/settings/validation.yaml | patch_mode 임계값, quality_gate_score |

(*) 파일명 확인 필요 — `three_phase_blueprint_generator.py` 또는 `blueprint_generator.py`
