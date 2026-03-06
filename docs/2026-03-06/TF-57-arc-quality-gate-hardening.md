# TF-57: Arc 품질 게이트 강화 — Director 허용 근본 원인 분석 + 패치 계획

> 작성: 2026-03-06
> 트리거: `projects/00_260306` 실파이프라인 결과물 재감리 3건 오류 확정
> 대상: Stage 2 Arc 생성 파이프라인

---

## 1. 확정 오류 3건 요약

| # | 위치 | 오류 내용 |
|---|------|----------|
| A | Arc 4 14화 | 등장인물 대화에 `"Block 2"` 집필 시스템 용어 노출 (4th wall break) |
| B | Arc 5 19~23화 | [시작 상태] 헤더 "대치동" ↔ 본문 "테헤란로의 야경" 위치 자가모순 |
| C | Arc 3 11화 | WTI 절반 청산 실현 수익 5.3억 — 직전 Arc 9화 28.5억 기준 예상값(6.75억+)과 불일치 |

---

## 2. 왜 Director가 허용했는가

### 오류 A — "Block 2" 허용 이유

**근본 원인: 검사 항목 부재**

Director 감사 체크리스트(NC-3) 11개 항목:
```
numeric_accuracy / arithmetic_consistency / title_changes /
scene_overlap / percentage_composition / event_ordering /
space_continuity / npc_identity / time_progression /
opening_diversity / timeline_arc_consistency
```

→ "픽션 외부 집필 시스템 용어가 등장인물 대화에 노출됐는지" 항목이 **존재하지 않음**.

Director thinking log(Arc 4 100점)에서도 확인:
> "No contradictions. No violations." — Block 2 언급을 단순 "이전 시점 언급" 대화로 처리

**추가 원인: Analyst 프롬프트에 금지 규정 없음**
Analyst는 "Block", "Arc", "전술서", "치료 문서" 등 내부 용어를 알고 있고, 등장인물 대화를 쓸 때 자연스럽게 노출시킴. 현재 어디에도 "픽션 내 등장인물이 집필 시스템 용어를 사용하면 안 된다"는 규칙이 없음.

---

### 오류 B — 대치동/테헤란로 허용 이유

**근본 원인: auto-correct가 메타데이터만 수정, 텍스트 미반영**

로그 증거:
```
[V60.25] Auto-correct: 2 fixes applied
- 시작 위치 수정: '서울 강남구 대치동...' → '서울 강남구 역삼동...'
```

코드 추적 결과 (`stage2_optimizer.py:270`):
```python
def _fix_start_location(self, arc, prev_arcs):
    ...
    start_state["location"] = prev_location  # ← JSON 필드만 수정
    # tactical_doc 내 "[시작 상태: 대치동...]" 텍스트는 그대로
```

즉 파이프라인이 **오류를 감지하고 수정을 시도했으나**, 수정 대상이 JSON 구조체의 `start_state.location` 필드뿐이었고, tactical_doc 텍스트 안에 하드코딩된 `"[시작 상태: 서울 강남구 대치동, ...]"` 문자열은 변경하지 않았음.

arc_005.txt 저장 시 tactical_doc 원본이 그대로 기록됨 → **수정이 phantom(유령 수정)**이 됨.

**추가 원인: Director 검사 범위 제한**
Director의 `(e) 위치/지리` 항목은 "직전 아크 종료 위치 → 현재 아크 시작 위치 연결성"을 보지만, **동일 에피소드 내에서 `[시작 상태:]` 헤더 위치와 본문 첫 문단 위치 묘사가 충돌하는지**는 체크하지 않음.

---

### 오류 C — 수치 불일치 허용 이유

**근본 원인: Stage 2 크로스-Arc 자산 연속성 검사 부재**

- `_check_tactical_arithmetic()` (`stage2_finalizer.py:76`): 곱셈·퍼센트 패턴 검사. 투자 수익 누적(이전 arc 자산 → 현재 arc 계산)은 패턴에 없음.
- NC-1 `NumericConsistencyChecker`: Stage 4 FactLedger 기반. Stage 2 Arc 생성 시점에는 FactLedger 미생성 → **Stage 2에서 NC-1 미작동**.
- Arc 4 PASS_WITH_FIX로 "15화 수치 오류" 잡았으나 Arc 3 11화(별개 Arc)의 수익 수치는 크로스-Arc 검사 대상이 아님.
- Analyst self-critic에 "직전 Arc 최종 자산 대비 현재 Arc 계산 검증" 항목 없음.

---

## 3. 왜 Fix도 못 했는가

| 오류 | Fix 시도 여부 | 실패 이유 |
|------|-------------|---------|
| A (Block 2) | ❌ 시도 안 함 | Director가 오류로 인식 못 함 |
| B (대치동) | ✅ 시도했으나 실패 | auto-correct가 JSON 필드만 수정, tactical_doc 텍스트 미반영 — **phantom fix** |
| C (5.3억) | ❌ 시도 안 함 | 크로스-Arc 수치 검사 없음 |

---

## 4. 패치 계획

### TF-57-A: Analyst 픽션 용어 오염 차단

**파일**: `config/prompts/analyst.yaml`
**위치**: COMMON_RULES 또는 WRITING_GUIDELINES 상단
**내용 추가**:

```yaml
# [TF-57-A] 픽션 내부 용어 사용 금지
- 등장인물의 대화·지문·내레이션에 집필 시스템 용어를 절대 사용하지 마세요.
  금지 용어: "Block N", "Arc N", "Blueprint", "전술서", "치료 문서", "Tactical Doc"
  예시 (잘못): "Block 2에서 내가 금도 간다고 중얼거린 것, 기억합니까?"
  예시 (올바름): "처음 원유에 투자할 때 금도 보라고 했던 것, 기억합니까?"
```

**Director 체크리스트 추가**: `director.yaml` NC-3 12번째 항목

```yaml
12. **fiction_term_leak** — 등장인물 대화·지문에 집필 시스템 용어
    (Block N / Arc N / Blueprint / 전술서)가 노출됐는가?
    OK = 없음. ISSUE = 1건 이상.
```

**`director_ensemble.py`**: `_nc3_keys` 리스트에 `"fiction_term_leak"` 추가
**테스트**: `test_fiction_term_leak.py` — "Block 2", "Arc 3" 포함 tactical_doc → ISSUE 감지 확인

---

### TF-57-B: tactical_doc 텍스트 레벨 위치 동기화

**파일**: `modules/core/stage2_optimizer.py`
**함수**: `ArcAutoCorrector._fix_start_location()` (L270)
**현재 동작**:
```python
start_state["location"] = prev_location  # JSON 필드만
```

**추가 동작** — tactical_doc 내 `[시작 상태:...]` 텍스트도 동기화:
```python
# tactical_doc 텍스트 내 위치도 교체
tactical_doc = arc.get("tactical_doc", "")
if tactical_doc and current_location and prev_location:
    import re
    # [시작 상태: <위치>, ...] 패턴에서 위치 부분만 교체
    old_escaped = re.escape(current_location)
    arc["tactical_doc"] = re.sub(
        rf'(\[시작 상태:.*?){old_escaped}',
        lambda m: m.group(0).replace(current_location, prev_location),
        tactical_doc,
        flags=re.DOTALL
    )
    corrections.append(f"tactical_doc 위치 텍스트 동기화: '{current_location}' → '{prev_location}'")
```

**Director NC-3 추가**: 기존 `(e) 위치/지리` 보강

```yaml
(e-2) **헤더-본문 위치 일관성**: 각 에피소드의 [시작 상태:] 헤더에 명시된
      위치와 본문 첫 문단의 위치 묘사가 일치하는가?
      예: 헤더 "대치동" ↔ 본문 "테헤란로의 야경을 내려다보고" = ISSUE
```

**테스트**: `test_tactical_doc_location_sync.py`
- auto-correct 후 tactical_doc 내 위치 텍스트도 변경됐는지 확인
- arc_txt 파일 저장 후 재검증

---

### TF-57-C: Stage 2 크로스-Arc 자산 연속성 검사

**파일**: `modules/core/stage2_finalizer.py`
**새 함수**: `_check_cross_arc_asset_continuity(tactical_doc, prev_arcs)` 추가

검사 로직:
1. 직전 Arc의 `arc_end_state` 또는 tactical_doc 마지막 종료 상태에서 자산 수치 추출 (정규식: `총자산 약? (\d+)억`)
2. 현재 tactical_doc 첫 에피소드 또는 본문 수치와 비교
3. ±20% 이상 차이 시 advisory 생성 → Director story_context 주입

**Analyst self-critic 항목 추가** (`analyst.yaml`):

```yaml
# [TF-57-C] 자산 수치 자기검증
- 직전 Arc 최종 자산을 [이전 Arc 종료 상태]에서 확인하고,
  현재 Arc의 첫 화 자산 언급이 이와 정합하는지 검증하세요.
  직전 Arc 없으면 해당 없음.
  수익 = 원금 × (가격 상승률) × 레버리지 공식을 직접 계산하세요.
```

---

## 5. 우선순위 및 작업 순서

```
1. TF-57-A (analyst.yaml + director.yaml NC-3 추가)   — 코드 변경 없음, yaml만
2. TF-57-B (tactical_doc 텍스트 동기화)               — stage2_optimizer.py 수정
3. TF-57-C (크로스-Arc 자산 검사)                     — stage2_finalizer.py 신규 함수
```

**감리 기준**:
- 테스트 기준선 유지: 3,390 passed ± 0 xfailed
- TF-57-A: `test_fiction_term_leak.py` 신규 3개 이상
- TF-57-B: `test_tactical_doc_location_sync.py` 신규 3개 이상
- TF-57-C: `test_cross_arc_asset_continuity.py` 신규 3개 이상

---

## 6. 현재 00_260306 프로젝트 처리

확정 오류 3건에 대해 arc_004.txt / arc_005.txt 직접 수동 수정 여부를 결정해야 함.

| 오류 | arc 파일 수동 수정 | 우선도 |
|------|------------------|--------|
| A (Block 2 — arc_004.txt 14화) | ✅ 즉시 수정 필요 | Stage 4 생성 전 必 |
| B (대치동 — arc_005.txt 전체) | ✅ 즉시 수정 필요 | Stage 4 생성 전 必 |
| C (5.3억 — arc_003.txt 11화) | 선택적 | 서술적 묘사이므로 Stage 4에서도 추가 불일치 유발 가능 |

수동 수정은 별도 작업으로 진행 (파이프라인 패치와 분리).

---

## 7. 병행 전수조사 오더 (오더 A·E~H 완료 / B~D 타 터미널)

> 상태: 오더 A·E~H 조사 완료, 감리 3회 오탐 제거 완료. 오더 B~D는 타 터미널 진행 중.

### 오더 A — Director NC-1 묵살 패턴 감사 ✅ 완료

**조사 결과 (감리 완료)**

| 질문 | 결과 |
|------|------|
| NC-1 AGREE/DISMISS 강제 파싱/감점 로직 | **없음** — `numeric_consistency_review` 필드는 선택사항 (director.yaml L458/728/965 "선택사항" 명시) |
| DISMISS 시 score 패널티 | **없음** — `director_ensemble.py` L905-910 로깅만, score 조정 코드 없음 |
| 미응답 시 감점 10→5 로직 | **없음** — L927 "[TF-C] 대원칙 3 준수: 감점 없음" 명시 |
| python_warnings 10→5 로직 | **없음** — NC-3 ISSUE 3건+ → python_warnings 3점 감점만 존재 (NC-1과 무관) |

**결론**: NC-1은 완전 optional, advisory-only. Director 주권주의(대원칙 3) 의도적 설계. 오탐 없음.

---

### 오더 B — NS-4 구현 전수 감사

**조사 파일**
- NS-4 태그 코드 전체 (grep 추적)
- `modules/core/stage2_orchestrator.py` (NS-4-S2 부분)
- `modules/core/stage4_interview_round.py` (NS-4-S4 부분)

**조사 목표**
1. NS-4-S2: Stage 2 Analyst self-critic에서 수치 목표 강제 주입 실제 동작 확인
2. NS-4-S4: Stage 4에서 NS-4 수치 검증 체인 실제 wiring 확인
3. 최근 커밋(`b8c06d8`)에서 변경된 NS-4 관련 코드에 버그/갭 있는가?
4. 기존 테스트에서 NS-4 경로를 커버하는 테스트가 있는가?

---

### 오더 C — PASS_WITH_FIX 루프 엣지케이스 감사

**조사 파일**
- `modules/core/stage4_interview_round.py` (`_execute_pass_with_fix_loop`)
- `modules/core/stage4_orchestrator.py`
- `modules/core/stage2_finalizer.py` (PWF-S2)

**조사 목표**
1. inplace 패치 3회 실패 시 full fallback 경로가 실제로 작동하는가?
2. PASS_WITH_FIX 루프 중 예외 발생 시 상태 롤백이 보장되는가?
3. `patch_state_updates` merge 로직에서 기존 `state_updates` 덮어쓰기 버그 있는가?
4. Director 재심사 최대 3회 카운터가 정확히 추적되는가?

---

### 오더 D — WritingDirective 체인 wiring 전수

**조사 파일**
- `modules/core/pattern_tracker.py`
- `modules/core/writing_directive_generator.py`
- `modules/core/stage4_interview_round.py` (`_setup_writing_directive`)
- `modules/domain/agents/chief_writer_quality.py` (check 6/7번)

**조사 목표**
1. `PatternTracker.build_report()` → `WritingDirectiveGenerator` → CW `setattr` 주입 체인이 실제로 끊기지 않고 연결되는가?
2. `writing_directive`가 None일 때 각 단계의 방어 코드가 있는가?
3. Director MC prepend에서 `[WritingDirective]` 블록이 실제로 포함되는가?
4. self-critique 6번(directive 준수)/7번(표현 신선도) 체크에서 `_tf54_writing_directive`가 None이면 어떻게 처리되는가?

---

### 오더 E — Analyst 픽션 용어 차단 + self-critic 항목 전수 ✅ 완료

**조사 파일**
- `config/prompts/analyst.yaml` (SELF_CRITIC_PROMPT, COMMON_RULES)
- `config/prompts/chief_writer.yaml` (COMMON_RULES_SECTION)
- `modules/domain/agents/chief_writer_quality.py` (_check_system_term_exposure)

**조사 결과 (감리 완료)**

| 항목 | 결과 |
|------|------|
| analyst.yaml 픽션 용어 금지 규칙 | **없음** — analyst.yaml에 "Block N", "Arc N" 등 금지 규정 부재 |
| chief_writer.yaml 픽션 용어 금지 규칙 | **있음** — L44-47 COMMON_RULES_SECTION 항목 14 ("Block 1", "Arc 4" 등 4th Wall 파괴 금지) |
| chief_writer_quality.py 코드 감지 | **있음** — L281-300 `_check_system_term_exposure()`: "Block \d+", "Arc \d+" 정규식 감지 (self-critique 10번째 체크) |
| Analyst self-critic 항목 수 | **7개** (ep_count, archetype, continuity, costume, state_constraints, quality_fields, **NS-1 수치검증**) |
| 직전 Arc 자산 → 현재 Arc 강제 주입 | **없음** — 개념적 지시만 있음, Python 레벨 강제 데이터 주입 메커니즘 부재 |

**핵심 갭**: analyst.yaml에 픽션 용어 금지 규정 없음 → Arc tactical_doc에 시스템 용어 노출 방지 불가.
chief_writer.yaml 규칙은 Stage 4 원고 전용이므로 Stage 2 Arc 생성 시점에는 무효.

**결론**: 오탐 0건. TF-57-A 패치 근거 실증 완료.

---

### 오더 F — V60.25 auto-correct tactical_doc 미반영 실증 ✅ 완료

**조사 파일**
- `modules/core/stage2_optimizer.py` (`ArcAutoCorrector._fix_start_location()`, `_sync_final_location()`)
- `modules/core/project_manager.py` (`_save_arcs_to_txt()`)
- `modules/core/stage2_validation_pipeline.py` (auto-correct 호출 지점)

**조사 결과 (감리 완료)**

`_fix_start_location()` L270-298 수정 범위:
```
arc["state_constraints"]["arc_start_state"]["location"]  ← 수정됨
tactical_doc 문자열 내 "[시작 상태: 위치]" 텍스트  ← 수정 안 됨
```

`_sync_final_location()`, `_fix_joint_docs()` 동일: tactical_doc 미수정 확인.

`_save_arcs_to_txt()` (project_manager.py L317):
```python
f"{arc.get('tactical_doc', '내용 없음')}"  ← 원본 그대로 저장
```

**Phantom Fix 흐름:**
```
auto-correct() → state_constraints.location 갱신 → tactical_doc 원본 유지
                                                           ↓
_save_arcs_to_txt() → tactical_doc 원본 txt 파일에 기록 ← 갱신 전 텍스트
```

**결론**: 오탐 0건. phantom fix 코드 레벨 실증 완료. TF-57-B 패치 근거 확정.

---

### 오더 G — _check_tactical_arithmetic 커버리지 갭 ✅ 완료

**조사 파일**
- `modules/core/stage2_finalizer.py` (`_check_tactical_arithmetic()` L76-129)
- `modules/core/numeric_consistency_checker.py`
- `modules/core/stage4_interview_round.py` (NumericConsistencyChecker 호출 경로)

**조사 결과 (감리 완료)**

`_check_tactical_arithmetic()` 지원 패턴:
| 패턴 | 정규식 | 지원 여부 |
|------|--------|----------|
| 배수 계산 `A × N배 = C` | L92-96 mult_pattern | ✅ |
| 퍼센트 수익 `A × P% = C` | L97-101 pct_pattern | ✅ |
| 합산식 `A + A×P% = Total` | 없음 | ❌ |
| 자연어 연산 ("절반 청산", "50% 청산") | 없음 | ❌ |

Stage 호출 경로:
- `_check_tactical_arithmetic`: Stage 2 PASS_WITH_FIX inplace patch **후에만** 호출 (전체 원고 검사 아님)
- `NumericConsistencyChecker`: **Stage 4 전용** (`stage4_interview_round.py`에서만 호출)
- Stage 2에서 FactLedger 교차검증 없음

**핵심 갭**: 투자 원금 + 수익률 기반 총액 검증 불가. 크로스-Arc 자산 연속성 검사 없음.

**결론**: 오탐 0건. TF-57-C 패치 근거 실증 완료.

---

### 오더 H — NC-3 optional 구조 + 위치(e) 검사 완전성 ✅ 완료

**조사 파일**
- `config/prompts/director.yaml` (NC-3 체크리스트 4곳)
- `modules/domain/agents/director_ensemble.py` (`_nc3_keys` L931-943)
- `modules/api/response_schemas.py` (consistency_checklist required 여부)

**조사 결과 (감리 완료)**

NC-3 11개 항목 `_nc3_keys` 매핑:

| # | 프롬프트 항목 | _nc3_keys | 매핑 |
|---|------------|-----------|------|
| 1 | numeric_accuracy | numeric_accuracy | ✅ |
| 2 | arithmetic | arithmetic | ✅ |
| 3 | title_consistency | title_consistency | ✅ |
| 4 | scene_overlap | scene_overlap | ✅ |
| 5 | percent_calculation | percent_calculation | ✅ |
| 6 | event_ordering | event_ordering | ✅ |
| 7 | space_continuity | space_continuity | ✅ |
| 8 | npc_identity | npc_identity | ✅ |
| 9 | time_progression | time_progression | ✅ |
| 10 | opening_diversity | opening_diversity | ✅ |
| 11 | timeline_arc_consistency | timeline_arc_consistency | ✅ |

`space_continuity` 항목 범위:
- **검사됨**: 직전 Arc 종료 → 현재 Arc 시작 장소 이동 + 전환 묘사 유무
- **미명시**: 동일 에피소드 내 `[시작 상태:]` 헤더 위치 ↔ 본문 첫 문단 위치 정합성

NC-3 optional 구조: 프롬프트("권장")/스키마(optional)/코드(L969 로깅만) 완전 일치.

**결론**: 구조 갭 0건. space_continuity 동일 에피소드 내 헤더-본문 범위 미명시 확인 → TF-57-B `(e-2)` 항목 추가 근거.

---

## 8. 전수조사 종합 결론 (감리 3회 완료)

> 완료: 2026-03-06
> 감리 3회 오탐 제거 완료. 오더 A·E~H 전량 확인.

### TF-57-A (Analyst 픽션 용어 차단) 근거 확정

- **analyst.yaml**: 픽션 용어 금지 규정 없음 ✅ 확인
- **chief_writer.yaml**: 규칙 있으나 Stage 4 원고 전용 → Stage 2 Arc에서는 무효 ✅ 확인
- **Director NC-3**: `fiction_term_leak` 항목 없음 ✅ 확인
- **패치 필요성**: analyst.yaml COMMON_RULES 추가 + director.yaml NC-3 12번째 항목 + `_nc3_keys` 추가

### TF-57-B (tactical_doc 텍스트 동기화) 근거 확정

- **phantom fix 실증**: `_fix_start_location()` JSON 필드만 수정, tactical_doc 미수정 ✅ 코드 레벨 확인
- **저장 흐름 확인**: `_save_arcs_to_txt()` tactical_doc 원본 그대로 기록 ✅ 확인
- **Director NC-3 space_continuity**: 동일 에피소드 헤더-본문 위치 정합 미명시 ✅ 확인
- **패치 필요성**: `_fix_start_location()` tactical_doc 텍스트 동기화 추가 + NC-3 `(e-2)` 항목

### TF-57-C (크로스-Arc 자산 연속성 검사) 근거 확정

- **_check_tactical_arithmetic**: 배수/퍼센트만, 합산식 미지원 ✅ 확인
- **NC-1 Stage 2 미작동**: NumericConsistencyChecker Stage 4 전용 ✅ 확인
- **NC-1 Optional**: AGREE/DISMISS 강제 없음, 패널티 없음 ✅ 확인
- **패치 필요성**: `stage2_finalizer._check_cross_arc_asset_continuity()` 신규 + Analyst self-critic 항목 추가

### 오탐 현황

| 오더 | 주요 발견 | 오탐 |
|------|---------|------|
| A (NC-1 묵살) | 강제성·패널티 없음 — 의도적 설계 (TF-C 대원칙 3) | 0건 |
| E (Analyst 용어) | analyst.yaml 규정 없음, chief_writer에만 존재 | 0건 |
| F (phantom fix) | tactical_doc 미수정 코드 레벨 실증 완료 | 0건 |
| G (_check_arithmetic) | 합산식 미지원, Stage 2 NC-1 미호출 | 0건 |
| H (NC-3 optional) | 구조 갭 없음, space_continuity 범위 모호성만 | 0건 |

**총 오탐: 0건. TF-57-A/B/C 패치 계획 모두 실증 완료.**

---

## 9. 터미널 3 오더 — Stage 2/3 전수 (감리 3회 완료)

> 완료: 2026-03-06. 오탐 1건 제거.

| 항목 | 파일:줄번호 | 상태 | 설명 |
|------|-----------|------|------|
| 1. NS-4-S2 wiring | stage2_preflight.py:480-514 | **OK** | NarrativeContextFormatter.format_all() → enhanced_context 병합 → FourPhase.generate() 내부 주입. wiring 정상. |
| 2. PASS_WITH_FIX 카운터 | stage2_finalizer.py:433,440 | **OK** | `_MAX_FIX=3` 상수화, `for _fix_i in range(_MAX_FIX)` 루프. 3회 초과 시 break → PF-3 패치본 채택 또는 REJECT fallback 완비. |
| 3. fix_scope 전파 (TF-34) | stage2_validation_pipeline.py:135-143 | **OK** *(오탐 제거)* | `run_validation()`은 pre-Director 단계 (V60 auto-correct + draft validator). fix_scope는 `stage2_finalizer.run_finalize()` 내부에서 Director 응답에서 직접 취득. TF-34는 Stage 4 Validator 패치였음 — Stage 2에 fix_scope 반환 불필요. |
| 4. NarrativeContextFormatter 전달 | stage2_preflight.py:501-511 | **GAP** *(설계, 기능 정상)* | `_narrative_ctx`가 enhanced_context에 병합 후 FourPhase.generate() 내부에서 사용됨. 기능은 정상 작동. 단, `_preflight_arc_analysis()` 반환값에 enhanced_context 포함 안 됨 → orchestrator에서 enrichment 여부 외부 추적 불가. |
| 5. quality_risk S3→S4 | stage3_orchestrator.py:757-760 | **OK** | `blueprint["_stage3_meta"]["quality_risk"]=True` 설정 후 stage4_interview_round.py:454-462에서 수신, Director advisory 주입. 전달 경로 완비. |

**결론: BUG 0건, GAP 1건(설계 이슈, 기능 영향 없음). Stage 2/3 파이프라인 핵심 경로 정상.**
