# 📋 Codex Stage 4 이슈 리포트

> **생성일**: 2026-02-20  
> **대상 범위**: `modules/core/stage4_*.py` (6개) + `modules/domain/agents/chief_writer*.py` (4개)  
> **총 코드량**: ~4,000 LOC (10개 파일)

---

## 이슈 요약

| # | 심각도 | 파일 | 이슈 | 라인 |
|---|--------|------|------|------|
| 1 | 🔴 Critical | `stage4_interview_round.py` | `run()` 840줄 메서드 — 파이프라인 최대 | L15-L854 |
| 2 | 🔴 Critical | `stage4_interview_round.py` | 20+ kwargs 블록 4회 복사-붙여넣기 | L96-229 |
| 3 | 🟠 Medium | `stage4_post_processor.py` | `process_pass_result()` 600줄, 다중 try-except 체인 | L21-L623 |
| 4 | 🟠 Medium | `stage4_post_processor.py` | 세션 종료 시 blocking `input()` | L631 |
| 5 | 🟠 Medium | `stage4_interview_round.py` | 다수 검증/체크 블록 순차 try-except 스택 (290줄) | L319-L609 |
| 6 | 🟠 Medium | `stage4_post_processor.py` | `state_changes`/연관 상태 반복 순회 로직 중복 | L84-160, L295-300 |
| 7 | 🟡 Minor | `chief_writer.py` | 3개 생성 메서드의 시그니처·kwargs 거의 동일 | L115, L550, L686 |
| 8 | 🟡 Minor | `stage4_interview_round.py` | REJECT 시 `save_cost_record()` 0값 호출 | L817-L838 |

---

## 상세 분석

---

### 🔴 이슈 #1: `run()` 840줄 미토콘드리아 메서드

**파일**: [stage4_interview_round.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L15)  
**라인**: 15-854 (840줄)

**문제**: `run()` 메서드는 Stage 2의 685줄 `stage_2_arcs_async_logic`보다 더 긴 **파이프라인 전체에서 가장 큰 단일 메서드**입니다. 내부에서 수행하는 작업:

1. **L15-62**: `round_ctx` 언패킹 (30+ 로컬 변수 생성)
2. **L71-229**: Phase 2 — 원고 앙상블 생성 (3가지 분기 × 동일 kwargs)
3. **L231-255**: ASP(Adversarial Self-Play) 교정
4. **L294-311**: Phase 3 — Python 사전 검증
5. **L319-609**: 다수 검증/체크 블록 순차 실행 (약 290줄)
6. **L611-703**: Phase 4 — Director 면담 + Quality Gate
7. **L705-854**: PASS/REJECT 처리

**영향**: 이 하나의 메서드를 수정하면 전체 Stage 4 파이프라인이 영향받으며, 개별 Phase 테스트가 불가능합니다.

**제안**: Phase별로 분리:
```
run()
├── _unpack_round_context(round_ctx) → locals dict
├── _generate_candidates(round_num, ...) → candidates
├── _run_validation_pipeline(candidates, ...) → validation_results  
├── _run_director_interview(candidates, validation_results, ...) → director_result
└── _process_verdict(director_result, ...) → _InterviewRoundResult
```

---

### 🔴 이슈 #2: 20+ kwargs 블록 4회 복사-붙여넣기

**파일**: [stage4_interview_round.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L96)  
**라인**: L96-122 vs L136-165 vs L171-199 vs L201-229

```python
# 이 블록이 4번 반복됨:
candidates = chief_writer.generate_ensemble(  # / .patch_with_feedback / .regenerate_with_feedback
    ep_num=next_ep,
    blueprint=blueprint,
    prev_manuscript=prev_text,
    hud_report=hud_report,
    arc_doc=arc_tactical,
    master_bible=self.ctx.current_project.master_bible,
    style_guide=style_guide,
    current_inventory=current_inventory,
    current_martial_arts=current_martial_arts,
    dead_npcs=dead_npcs,
    item_acquisition_timeline=item_acquisition_timeline,
    reference_anchor_prompt=reference_anchor_prompt,
    mandatory_context=mandatory_context,
    anti_trope_prompt=_effective_anti_trope,
    justification_prompt=justification_prompt,
    reflexion_prompt=reflexion_prompt,
    genre_name=genre_name,
    npc_equipment_summary=npc_equipment_summary,
    intro_dna=intro_dna,
    purism_prompt=purism_prompt,
    state_tracker=self.ctx.state_tracker,
    prev_manuscripts_text=_prev_manuscripts_text,
    world_state_summary=_world_state_summary,
    chain_link_section=_chain_link_section,
)
```

**문제**: 23개 키워드 인자 블록이 `generate_ensemble`, `patch_with_feedback`, `regenerate_with_feedback` + 패치 실패 시 재시도 총 **4번** 거의 동일하게 복사되어 있습니다. 하나의 파라미터가 추가/변경되면 4곳을 모두 수정해야 합니다.

**제안**: 공통 kwargs를 dict로 추출:
```python
_common_kwargs = {
    "ep_num": next_ep, "blueprint": blueprint, "prev_manuscript": prev_text,
    "hud_report": hud_report, "arc_doc": arc_tactical, ...
}
candidates = chief_writer.generate_ensemble(**_common_kwargs)
# 또는
candidates = chief_writer.regenerate_with_feedback(
    **_common_kwargs, director_feedback=..., previous_attempt=...,
)
```

---

### 🟠 이슈 #3: `process_pass_result()` 600줄, 다중 try-except 체인

**파일**: [stage4_post_processor.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L21)  
**라인**: 21-623

**문제**: 이 메서드는 에피소드 PASS 후처리를 담당하며 다수의 독립 후처리 단계를 순차적으로 실행합니다:

| 단계 | 라인 | 설명 |
|------|------|------|
| DB 저장 | L40-56 | 원고+변동사항 커밋 |
| HUD 업데이트 | L59-74 | Director 승인 후 HUD 반영 |
| 파일 저장 | L77-82 | 텍스트 파일 출력 |
| 벡터 메모리 | L85-173 | 에피소드 메모리 저장 |
| 내러티브 요약 | L176-180 | 5화 단위 요약 생성 |
| 로그/모듈 저장 | L183-207 | failure_learner, character_voice 등 |
| Episode Bible | L210-381 | 정산·상태 업데이트 (170줄!) |
| 연결고리 | L387-400 | chain_link 추출/저장 |
| WorldState/FactLedger | L403-446 | 메타데이터 원자적 갱신 |
| 만족도 태깅 | L448-461 | 에피소드 만족도 태그 추출/저장 |
| 호흡 분석 | L464-483 | 호흡 분석 DB 저장 |
| 품질 회귀 감지 | L485-503 | 직전 Arc 대비 점수 하락 감지 |
| NPC 과잉 등장 | L505-544 | 엑스트라 NPC 과잉 등장 경고 |
| 반복 감지 | L547-583 | 크로스 에피소드 반복 |
| 비용 기록 | L586-610 | 토큰/비용 스냅샷 |

각 단계가 `try-except`로 감싸져 있어 개별 실패는 비차단이지만, 600줄 단일 메서드로 운영되는 구조는 유지보수 비용이 큽니다.

**제안**: 각 단계를 별도 메서드로 추출하고, 메인 메서드는 오케스트레이션만:
```python
def process_pass_result(self, **kwargs):
    if not self._save_to_db(**kwargs): return False
    self._update_hud(**kwargs)
    self._save_file(**kwargs)
    self._save_vector_memory(**kwargs)
    self._save_episode_bible(**kwargs)
    ...
```

---

### 🟠 이슈 #4: 세션 종료 시 blocking `input()`

**파일**: [stage4_post_processor.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L631)  
**라인**: 631

```python
def run_post_episode_tasks(self) -> None:
    ...
    try:
        input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")  # L631
    except EOFError:
        pass
```

**문제**: Stage 2의 이슈 #4와 동일한 패턴. 야간 무인 운영(attended=False) 모드에서 이 `input()`이 프로세스를 무한 대기시킬 수 있습니다.

**제안**: Stage 2 이슈와 동일 — `attended` 모드 플래그 확인 후 스킵.

---

### 🟠 이슈 #5: 다수 검증/체크 블록 순차 try-except 스택 (290줄)

**파일**: [stage4_interview_round.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L319)  
**라인**: 319-609

**문제**: 대표 검증/체크 블록들이 각각 독립적인 `try-except`로 순차 실행됩니다:

| # | 대표 검증/체크 | 라인 |
|---|--------|------|
| 1 | ConsistencyValidator | L319-407 |
| 2 | BlockingValidator | L409-424 |
| 3 | ContinuityValidator | L426-447 |
| 4 | 좌절-보상 타이머 | L449-460 |
| 5 | 파괴 엔티티 감지 | L462-475 |
| 6 | 캐시 기반 연속성 검사 | L477-502 |
| 7 | PreDirectorChecklist + ConfidenceCalibrator | L548-584 |
| 8 | CrossAgentVerifier | L586-609 |

위 표 외에도 연속성 충돌/이력 충돌 처리 블록이 동일 구간에 추가로 존재해, 전체 흐름이 더욱 길어집니다.

대부분이 동일한 패턴을 따릅니다:

```python
try:
    for ci, cand in enumerate(candidates):
        _ms = cand.get("manuscript", "")
        if _ms and ci < len(validation_results):
            result = validator.validate(_ms, context)
            violations = result.get("violations", [])
            if violations:
                for v in violations:
                    validation_results[ci]["warnings"].append(...)
                validation_results[ci]["warning_count"] = len(...)
except Exception as err:
    self.ctx.ui.log(f"... 실패: {err}")
```

이 패턴이 8번 반복되어 290줄을 차지합니다.

**제안**: 검증기 파이프라인 추상화:
```python
_validators = [
    ("ConsistencyValidator", consistency_validator, "validate"),
    ("BlockingValidator", blocking_validator, "validate"),
    ("ContinuityValidator", continuity_validator, "validate"),
    ...
]
for name, validator, method in _validators:
    self._run_validator(name, validator, method, candidates, validation_results, context)
```

---

### 🟠 이슈 #6: `state_changes` 반복 파싱 — 3중 구현

**파일**: [stage4_post_processor.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_post_processor.py#L84)  
**라인**: L84-113, L115-160, L295-300

**문제**: `state_changes` 딕셔너리의 하위 키(`npc_deaths`, `skill_acquisitions`, `relationship_changes`, `major_items` 등)를 **동일 파일 안에서 3번** 수동 순회합니다:

**1) L84-113** — 벡터 메모리용 event_type/entity_name 추출:
```python
if _sc.get("npc_deaths"):
    _mem_event_types.add("death")
    for d in _sc["npc_deaths"]:
        _mem_entity_names.add(d.get("name", "") if isinstance(d, dict) else str(d))
# skill_acquisitions, relationship_changes, major_items도 각각 동일 패턴 반복
```

**2) L115-160** — 벡터 메모리 `_rich_summary` 구성 시 동일 키를 다시 순회:
```python
_npc_deaths = _state_changes.get("npc_deaths", [])
if isinstance(_npc_deaths, list) and _npc_deaths:
    for d in _npc_deaths: ...
_rel_changes = _state_changes.get("relationship_changes", [])
# ... (major_items, resolved_plots 등 동일 반복)
```

**3) L295-300** — Episode Bible 정산 시 NPC 사망 판정:
```python
for npc in key_npcs:
    if isinstance(npc, dict):
        status = npc.get("NPC_Martial_HUD", {}).get("current_status", "")
        if "사망" in str(status) or "죽" in str(status) or "절명" in str(status):
```

반면 L403-444의 WorldState/FactLedger 갱신은 `.update_from_state_changes()`에 위임하므로 중복이 아닙니다.

**제안**: L84-160의 벡터 메모리용 요약 추출을 `_extract_state_change_summary(state_changes) → (event_types, entity_names, rich_summary)` 헬퍼로 통합.

---

### 🟡 이슈 #7: `ChiefWriter` 3개 생성 메서드의 시그니처 거의 동일

**파일**: [chief_writer.py](file:///c:/Users/User/Desktop/글도비/modules/domain/agents/chief_writer.py#L115)  
**라인**: L115 (`generate_ensemble`), L550 (`regenerate_with_feedback`), L686 (`patch_with_feedback`)

**문제**: 세 메서드 모두 20+ 파라미터를 거의 동일하게 받으며, 내부 로직도 "공통 컨텍스트 빌드 → 후보 병렬 생성 → 품질 게이트 적용"이라는 동일한 흐름을 따릅니다.

이슈 #2의 caller 측 중복과 대응되는 callee 측 중복입니다.

**제안**: 공통 파라미터를 `WriterRequest` dataclass로 묶어 전달:
```python
@dataclasses.dataclass
class WriterRequest:
    ep_num: int
    blueprint: dict
    prev_manuscript: str
    hud_report: str
    style_guide: str
    ...
```

---

### 🟡 이슈 #8: REJECT 시 `save_cost_record()` 0값 호출 (비용 로그/이벤트 로그 혼합)

**파일**: [stage4_interview_round.py](file:///c:/Users/User/Desktop/글도비/modules/core/stage4_interview_round.py#L817)  
**라인**: 817-838

```python
self.ctx.current_project.db.save_cost_record(
    session_id=f"ep_{next_ep}",
    scope_type="episode",
    scope_id=int(next_ep),
    total_calls=0,        # ← 항상 0
    total_tokens=0,        # ← 항상 0
    total_cost_usd=0.0,    # ← 항상 0
    model_breakdown={      # ← 이벤트 메타데이터를 model_breakdown에 저장
        "event": "stage4_reject",
        "bucket": _reject_bucket,
        ...
    },
)
```

**문제**: `save_cost_record`에 비용 0 레코드를 남기면서 `model_breakdown`에 REJECT 이벤트 메타를 함께 저장합니다. API 계약 위반까지는 아니지만, 비용 로그와 운영 이벤트 로그가 혼합되어 집계/대시보드에 노이즈를 만들 수 있습니다.

**제안**: 별도의 `save_rejection_event()` API를 사용하거나, 기존 `save_director_selection()` (L683)에 이미 기록하고 있으므로 이 호출을 제거.

---

## 긍정적 관찰

Stage 4는 Stage 2-3에 비해 **아키텍처적으로 가장 성숙**합니다:

- **`Stage4Context`**: `__slots__` + `from_app()` 패턴, 필수/확장/조건부/콜백 4계층 분리 — 프로젝트 최고 수준의 DI
- **`stage4_types.py`**: 순환 import 방지를 위한 별도 타입 모듈 — 올바른 설계 패턴
- **`_SessionConfig`/`_RoundContext`/`_InterviewRoundResult`**: `dataclass(slots=True)` — 메모리 효율적 구조화
- **`Stage4Orchestrator`**: lazy property로 서브모듈 초기화 — 깔끔한 구성
- **Post-Processor의 트랜잭션 처리** (L405-446): `_nullcontext` 폴백 포함 원자적 WorldState/FactLedger 갱신
