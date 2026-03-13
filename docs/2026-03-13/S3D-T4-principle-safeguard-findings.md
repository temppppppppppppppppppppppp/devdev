# S3D-T4: Stage 3 대원칙 준수 및 안전장치 감사 보고서

> **감사 유형**: 1pass read-only audit
> **감사일**: 2026-03-13
> **감사 범위**: Stage 3 Blueprint 파이프라인 전체
> **감사 대상 파일**:
> - `modules/core/stage3_orchestrator.py`
> - `modules/domain/agents/unified_blueprint_validator.py`
> - `modules/domain/agents/blueprint_ensemble.py`
> - `modules/domain/agents/three_phase_blueprint_generator.py`
> - `modules/domain/agents/continuity_blueprint.py`
> - `modules/domain/agents/director_ensemble.py` (Stage 3 부분)
> - `config/settings/validation.yaml`

---

## 체크리스트 결과 요약

| # | 항목 | 상태 | 심각도 |
|---|------|------|--------|
| 1 | 대원칙1: Python auto-REJECT 부재 | **OK** | - |
| 2 | 대원칙2: NPC 속성 직접 수정 부재 | **OK** | - |
| 3 | 대원칙3: Director bypass 경로 | **OK** | - |
| 4 | 대원칙4: 사망 캐릭터 경로 | **OK** | - |
| 5 | 정지선 30자 substring 오탐 위험 | **FINDING** | P2 |
| 6 | QualityGate 임계값 통일 | **OK** | - |
| 7 | fail_count 무한루프 방어 | **OK** | - |
| 8 | production_head >= total_planned_ep 방어 | **OK** | - |
| 9 | InPlace 30KB 보호 | **OK** | - |
| 10 | 비무협 장르 내공 오염 방지 | **OK** | - |

---

## 1. 대원칙1: Python auto-REJECT 경로 — PreValidator warning-only vs verdict determination

**상태: OK**

### 근거

`unified_blueprint_validator.py` 구조가 명확하게 2단계로 분리되어 있다:

- **Phase A (L146-181)**: `_python_pre_validate()` 호출. 반환값은 issues 리스트와 `has_critical` 플래그만 포함. Python은 REJECT 판정 없이 경고만 생성.
  - L174: `# [V60.80] Python은 경고만 - REJECT 권한 없음, Director가 최종 판정`
  - L176: `logging.warning(" [PreValidator] Python 경고: CRITICAL 이슈 발견 (Director가 최종 판정)")`

- **Phase B (L183-317)**: Director에게 항상 호출 전달. `final_verdict = director_verdict` (L292)로 Director 판정을 그대로 수용.

- `_python_pre_validate()` (L331-442): issues를 수집하지만 어떤 경로에서도 verdict를 반환하지 않음. `has_critical`, `has_major_excess` 플래그만 반환하며, 이들은 Director 주의 포인트로만 활용.

- `blueprint_ensemble.py` L377-402: Python 최소 기준 필터(씬 4개, 500자)는 "당선 불가" 후보 제거용이며 verdict 판정이 아님. L378: `# 철학: Python은 "당선 불가" 후보만 걸러냄, 선택은 Director가 함`

- `continuity_blueprint.py` L210: Python advisory를 `python_check` dict에 수집하고 L213-214에서 LLM에게 전달만 함.

**결론**: Python은 데이터 수집/포맷팅/경고 생성만 수행하며, 판정 권한은 전량 Director(LLM)에게 위임. 대원칙 1 준수.

---

## 2. 대원칙2: NPC 속성/세계관 직접 수정 코드 부재 확인

**상태: OK**

### 근거

감사 대상 6개 파일 전체를 검토한 결과:

- `stage3_orchestrator.py`: StateTracker는 읽기 전용으로만 사용 (L511: `ctx.state_tracker` 할당, L630-653: `full_extract_from_arcs`는 Arc에서 **추출**만 수행). NPC registry 수정/덮어쓰기 코드 없음.
- `unified_blueprint_validator.py`: L236-247에서 `state_tracker.npc_registry`를 **읽기**하여 encyclopedia 정보 구성만 수행. 수정 호출 없음.
- `blueprint_ensemble.py`: state_tracker를 HUD 컨텍스트 빌드용으로만 전달 (L268). NPC 속성 변경 없음.
- `three_phase_blueprint_generator.py`: state_tracker를 검증 파라미터로 전달만 (L392). 수정 없음.
- `continuity_blueprint.py`: NPC 관련 코드 없음. Blueprint 텍스트 내 아이템/수여물 regex 추출만 (순수 읽기).
- `director_ensemble.py`: Blueprint 선택/판정만 수행. 팩트시트 수정 코드 없음.

**결론**: Stage 3 전체에서 NPC 속성, 세계관, 관계도를 Python이 직접 수정하는 코드 없음. 대원칙 2 준수.

---

## 3. 대원칙3: Director bypass 경로 — QualityGate PASS→REJECT, continuity REJECT, director=None

**상태: OK**

### 근거

**3-a. Director=None 방어**:
- `unified_blueprint_validator.py` L186-196: Director가 None이면 즉시 REJECT 반환.
  ```
  logging.error("❌ [대원칙3] Director가 None — Blueprint 판정 불가, REJECT 처리")
  return "REJECT", {...}
  ```
  명시적으로 `[대원칙3]` 태그 부착. 완벽한 방어.

**3-b. QualityGate PASS→REJECT 전환**:
- `three_phase_blueprint_generator.py` L434-440: `verdict == "PASS" and _score < _quality_gate_score` 시에만 REJECT 전환.
  - L436: `# [TF-46] PASS_WITH_FIX는 Director 주권 존중 — gate 미적용`
  - PASS_WITH_FIX는 QualityGate bypass 되어 Director 주권 존중. 대원칙 3 준수.

**3-c. Continuity REJECT**:
- `three_phase_blueprint_generator.py` L362-380: `check_blueprint_continuity_with_cache`가 REJECT이면 `continue`로 재시도. Director를 우회하지 않고 연속성 오류에 대한 재생성을 유도. Director 호출 전 사전 필터로서 합리적.

**3-d. Director compare_and_select_blueprint**:
- `director_ensemble.py` L201-229: Director가 직접 후보 비교/선택. Python이 선택하지 않음.
- `unified_blueprint_validator.py` L104-143: `all_candidates > 1`이면 Director 비교 선택 모드 진입. Python 개입 없음.

**결론**: Director 주권이 일관되게 유지됨. Director=None 방어, PASS_WITH_FIX bypass, 재시도 유도 모두 정상. 대원칙 3 준수.

---

## 4. 대원칙4: 사망 캐릭터 — check_dead_npc → CRITICAL issues → Director 전달 경로

**상태: OK**

### 근거

- `unified_blueprint_validator.py` L157-172:
  - `state_tracker.check_dead_npc_in_blueprint()` 호출 (L158)
  - 위반 감지 시 `severity: "CRITICAL"`, `category: "dead_npc"` 이슈를 `pre_result["issues"]`에 추가 (L163-171)
  - `pre_result["has_critical"] = True` 설정 (L172)
  - L162: `# Director 주의 포인트로 추가 (Python은 REJECT 안 함)` — 대원칙 1과 3 동시 준수
  - L150: `# [V60.96] 죽은 NPC 등장 체크 - 경고로 Director에게 전달 (디렉터주권주의)`

- `state_tracker_npc.py` L1420-1460: `check_dead_npc_in_blueprint()`가 integrated_scenario + scene_breakdown 전체를 검사.

- 이슈는 L224-232에서 `python_warnings`로 Director 프롬프트 앞에 `[Director 주의 포인트]` 헤더와 함께 주입됨.

- Director가 최종 PASS/REJECT 판정 (L292: `final_verdict = director_verdict`).

**결론**: 사망 NPC 감지 → CRITICAL 이슈 생성 → Director 주의 포인트 주입 → Director 최종 판정. 회상/언급 판별은 LLM(Director)이 담당. 대원칙 4 준수.

---

## 5. 정지선 위반 검증 — 30자 substring matching 오탐 위험

**상태: FINDING**
**심각도: P2 (Low — advisory 경고일 뿐 REJECT 권한 없음)**

### 근거

`unified_blueprint_validator.py` L392-405:
```python
stop_content = stop_line.get("content", "")
if stop_content and len(stop_content) > 10:
    stop_keywords = stop_content[:30].strip()
    if stop_keywords in integrated:
```

**문제점**:
1. `stop_content[:30]`으로 다음 화 내용의 앞 30자를 추출하여 `in` 연산으로 substring 매칭.
2. 30자 substring이 일반적인 한국어 표현과 우연히 일치할 수 있음 (예: 흔한 장소명, 인물명 조합).
3. 한국어 30자는 약 15단어 분량으로, 일반 서술문 일부와 겹칠 가능성이 낮지 않음.

**완화 요인**:
- 이 결과는 `_python_pre_validate()`의 이슈 리스트에만 추가됨 (CRITICAL severity).
- Python은 REJECT 권한이 없으므로 (대원칙 1), 오탐이 발생해도 Director 주의 포인트로만 작동.
- Director가 실제 정지선 위반 여부를 LLM 판단으로 최종 결정.

**영향**: 오탐 시 Director에게 불필요한 CRITICAL 경고가 전달되어 잠재적으로 Director의 REJECT 판정 확률을 높일 수 있음. 그러나 Director가 최종 판정하므로 실질적 위험은 낮음.

**권장사항**: 정지선 매칭을 단순 substring 대신 핵심 키워드 추출 + 2개 이상 키워드 동시 출현 조건으로 강화하면 오탐을 줄일 수 있음.

---

## 6. QualityGate score 임계값 — Stage 2/3/4 통일 확인

**상태: OK**

### 근거

- `config/settings/validation.yaml` L34: `quality_gate_score: 90  # [TF-28b] Stage 2/3/4 전 스테이지 통일 QualityGate`

- **Stage 2**: `stage2_finalizer.py` L632: `_quality_gate_score = _threshold("scoring.quality_gate_score", 90)`
- **Stage 3**: `three_phase_blueprint_generator.py` L418: `_quality_gate_score = _threshold("scoring.quality_gate_score", 90)`
- **Stage 4**: `stage4_interview_round.py` L2909: `_quality_gate_score = _threshold("scoring.quality_gate_score", 90)`

3개 스테이지 모두 동일한 YAML 키 (`scoring.quality_gate_score`)를 참조하고, 기본값(fallback)도 90으로 통일. SSOT 준수.

**추가 확인**: Stage 3의 QualityGate 적용 조건:
- `three_phase_blueprint_generator.py` L434: `verdict == "PASS" and _score < _quality_gate_score`
- PASS_WITH_FIX는 gate 미적용 (L436 주석: Director 주권 존중)
- Stage 2/4와 동일한 패턴 (PASS일 때만 gate 적용, PASS_WITH_FIX bypass).

---

## 7. fail_count 무한루프 방어 — _handle_failure 항상 break=True

**상태: OK**

### 근거

`stage3_orchestrator.py` L1805-2002:
- `_handle_failure()` 메서드가 반환하는 dict에 항상 `"break": True` 포함 (L2001).
- L1808 docstring: `"항상 break=True를 반환하여 루프를 종료한다 (순차 의존성: 후속 에피소드는 현재 에피소드 Blueprint에 의존)"`
- L1995-1996 주석: `# [TF-S3-02] 실패 에피소드에서 중단 (순차 의존성 보존)`

호출측 (L590-597):
```python
while working_ep <= target_ep:
    result = self._process_single_episode(...)
    ...
    if result.get("break"):
        completed_normally = False
        break
```

**결론**: 실패 시 무조건 루프 탈출. 무한루프 가능성 없음.

참고: `three_phase_blueprint_generator.py`의 내부 retry 루프도 `max_retries + 1` (L176: 최대 10회)로 상한이 있으며, 소진 시 FAILED/긴급 폴백 반환.

---

## 8. production_head >= total_planned_ep 방어

**상태: OK**

### 근거

`stage3_orchestrator.py` L547-550:
```python
if production_head >= total_planned_ep:
    ctx.ui.log(f"✅ 이미 {production_head}화까지 완료되어 추가 생성할 범위가 없습니다.")
    ctx.ui.log("   💡 Stage 2에서 Arc를 추가하면 설계 범위가 늘어납니다.")
    return {"success_count": 0, "fail_count": 0}
```

추가로 L580-582에서 `target_ep < working_ep` 역전도 방어:
```python
if target_ep < working_ep:
    ctx.ui.log(f"✅ 이미 {target_ep}화까지 완료되어 추가 생성할 범위가 없습니다.")
    return {"success_count": 0, "fail_count": 0}
```

**결론**: 범위 역전 및 이미 완료된 범위에 대한 방어가 2중으로 구현됨. 정상.

---

## 9. InPlace 30KB 보호 구현 확인

**상태: OK**

### 근거

`three_phase_blueprint_generator.py` L688-691:
```python
_full_json = json.dumps(original_blueprint, ensure_ascii=False, indent=2)
if len(_full_json) > 30000:
    logging.warning("[TRUNCATION] _inplace_patch_blueprint: Blueprint JSON %d자 > 30KB 상한 → InPlace 불가", len(_full_json))
    return None  # 절단 시 깨진 JSON → full rewrite 폴백
```

- 30,000자(30KB) 초과 시 즉시 `None` 반환.
- 호출측 (L248-249): `None` 반환 시 `logging.warning("[InPlace] 실패 → 전면 재생성 폴백")`으로 full 재생성 경로 진입.
- CLAUDE.md의 "InPlace 보호: 30KB 초과 → return None (full 폴백)" 사양과 일치.

---

## 10. 비무협 장르 내공(internal_energy) 오염 방지

**상태: OK**

### 근거

`blueprint_ensemble.py` L752-754 (`_format_constraints` 메서드):
```python
# [TF-41] P1-2: 무협 전용 — 비무협 장르는 내공 표시 스킵
if genre == "wuxia" and inherited.get("internal_energy") is not None:
    lines.append(f"  내공/에너지: {inherited['internal_energy']}")
```

- `genre == "wuxia"` 조건으로 비무협 장르에서 `internal_energy` 키가 제약 프롬프트에 주입되지 않음.
- `genre` 파라미터는 L262에서 `_format_constraints(constraint_block, genre=genre)`로 전달됨.
- `genre`는 L252-259에서 DB bible의 `_genre` 필드로부터 로드 (기본값: `GenreTypes.WUXIA`).

`three_phase_blueprint_generator.py` L106-114에서도 genre를 로드하여 `constraint_compiler.compile(genre=_genre)`로 전달.

**결론**: 비무협 장르에서 내공/에너지 키가 Blueprint 제약에 노출되지 않음. 오염 방지 정상.

---

## 종합 판정

| 카테고리 | 결과 |
|----------|------|
| 대원칙 1 (Python 수집만, 판단은 LLM) | **준수** |
| 대원칙 2 (팩트시트 수정 권한 LLM만) | **준수** |
| 대원칙 3 (디렉터 주권주의) | **준수** |
| 대원칙 4 (사망 캐릭터 회상/언급만) | **준수** |
| P0 발견 | **0건** |
| P1 발견 | **0건** |
| P2 발견 | **1건** (정지선 30자 substring 오탐 위험) |
| P3 발견 | **0건** |

Stage 3 Blueprint 파이프라인은 4대 대원칙을 일관되게 준수하고 있으며, 안전장치(QualityGate 통일, 무한루프 방어, InPlace 보호, 비무협 오염 방지, Director=None 방어, production_head 범위 방어)가 정상 작동 중이다. 유일한 발견은 P2 수준의 정지선 substring 매칭 오탐 가능성이며, Director가 최종 판정하므로 실질적 운영 위험은 낮다.
