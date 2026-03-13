# TF-10: Arc Episode Detail Map -- 설계 및 영향 분석

> 작성일: 2026-02-24
> 근거: 코드 실독 기반 (추정 없음)

---

## 1. 현재 Arc 스키마 전체 필드 목록

### 1-A. Gemini API 강제 스키마 (response_schemas.py ARC_DESIGN_SCHEMA, L260-298)

| 필드 | 타입 | required | 비고 |
|------|------|----------|------|
| `arc_no` | INTEGER | **YES** | |
| `ep_count` | INTEGER (2-6) | **YES** | |
| `ep_start` | INTEGER | **YES** | |
| `ep_end` | INTEGER | **YES** | |
| `title` | STRING | **YES** | |
| `beat_sequence` | ARRAY[STRING] | **YES** | |
| `tactical_doc` | STRING | **YES** | **현재 유일한 화별 서사 전달 경로** |
| `hybrid_composition` | OBJECT | no | primary, secondary, mixing_logic |
| `state_constraints` | OBJECT | no | ARC_STATE_CONSTRAINTS_SCHEMA (L193-258) |
| `joint_docs` | OBJECT | no | final_location, physical_inventory, world_joint |
| `status_shadow` | OBJECT | no | internal_energy_loss, expected_injuries, item_consumption |

### 1-B. Pydantic 모델 (modules/models/arc.py ArcData, L163-193)

위 스키마를 수용하되 `extra="allow"` 설정으로 추가 키를 안전 흡수. 주요 추가 필드:

| 필드 | 기본값 | 비고 |
|------|--------|------|
| `volume_no` | 0 | 오케스트레이터 주입 |
| `global_arc_no` | 0 | arc_no alias |
| `constraint_summary` | "" | Stage 2 finalizer L353에서 주입 |
| `state_changes` | {} | V61 구조화 (npc_deaths, skill_acquisitions 등 20+ 서브키) |
| `seed_injection` / `seeds` | None | 복선 데이터 |
| `arc_drive` | - | Weaver 욕망 드라이브 (finalizer L228) |

### 1-C. LLM 프롬프트 JSON 스키마 (config/prompts/ensemble.yaml ENSEMBLE_ARC_PROMPT, L86-217)

LLM에게 요구하는 출력 스키마. `tactical_doc` 필드 지시:

```
"tactical_doc": "[V60.40] 각 화마다 시작/종료 상태 체크포인트 필수.
                  화당 500자 이상. '제 N화:' 형식으로 화별 명확 구분"
```

**핵심 문제**: `tactical_doc`은 자유 텍스트 STRING 하나에 모든 화의 서사를 담는 구조. LLM이 "제 N화:" 패턴으로 구분하도록 지시하지만, 실제 출력은 일관되지 않음.

---

## 2. arc_data 참조 코드 지도

### 2-A. Stage 2 (Arc 생성/검증)

| 파일 | 위치 | 사용 방식 |
|------|------|-----------|
| `modules/core/response_schemas.py` | L260-298 | `ARC_DESIGN_SCHEMA` 정의 (Gemini API 강제) |
| `modules/models/arc.py` | L163-229 | `ArcData` Pydantic 모델, `validate_arc()` |
| `modules/core/stage2_finalizer.py` | L189-190 | `refined_arc.get("tactical_doc", "")` 길이 검사 |
| `modules/core/stage2_finalizer.py` | L86-96 | Director 컨텍스트에서 `_pa.get("tactical_doc", "")` 전문 전달 |
| `modules/core/stage2_validation_pipeline.py` | L239-240 | Duplicate Guard: `all_refined_arcs[-1].get("tactical_doc", "")` |
| `modules/core/stage2_validation_pipeline.py` | L640-734 | Flow Guard: `refined_arc.get("beat_sequence", [])` |
| `modules/core/stage2_preflight.py` | L1026-1028 | `refined_arc.get("tactical_doc", "")` 동적 장르 감지 |
| `modules/core/constraint_db.py` | L93-100 | `_parse_arc_state()` - state_constraints 추출 |
| `modules/core/semantic_plot_guard.py` | - | `tactical_doc` 텍스트로 플롯 중복 감지 |
| `modules/domain/agents/arc_ensemble.py` | - | `tactical_doc` 생성 (LLM) |
| `modules/domain/agents/four_phase_arc_generator.py` | - | `tactical_doc` 생성 (3단계 파이프라인) |
| `modules/domain/agents/unified_arc_validator.py` | - | `tactical_doc` 검증 |
| `modules/domain/agents/arc_draft_validator.py` | - | `tactical_doc` 사전 검증 |
| `modules/domain/agents/arc_corrector.py` | - | `tactical_doc` 부분 수정 |
| `modules/domain/agents/continuity_inspector.py` | - | `tactical_doc` 연속성 검증 |
| `modules/domain/agents/consensus_validator.py` | - | `tactical_doc` 합의 검증 |
| `modules/domain/agents/state_tracker.py` | - | `tactical_doc` 상태 추출 |
| `modules/domain/agents/constraint_compiler.py` | - | `tactical_doc` 제약 컴파일 |
| `modules/core/stage2_optimizer.py` | - | 실패 메모리에 `tactical_doc` 참조 |

### 2-B. Stage 3 (Blueprint 생성) -- **가장 큰 영향**

| 파일 | 위치 | 사용 방식 |
|------|------|-----------|
| `modules/domain/agents/blueprint_ensemble.py` | L148-154 | **`arc_focus` 추출**: `tactical = arc_data.get("tactical_doc", "")` -> `arc_focus = tactical[:4000]` |
| `modules/domain/agents/blueprint_constraint_compiler.py` | L188-234 | **`_extract_episode_focus()`**: regex로 `tactical_doc`에서 "제N화" 섹션 추출 |
| `modules/domain/agents/blueprint_constraint_compiler.py` | L236-266 | **`_extract_stop_line()`**: regex로 다음 화 내용 추출 |
| `modules/domain/agents/three_phase_blueprint_generator.py` | L57-100 | `arc_data` 전체를 `generate()`에 전달 |
| `modules/core/stage3_orchestrator.py` | L512-549 | **TF9 Treatment Block 직접 주입** -- `arc_data` 압축 정보 손실 보완 시도 |
| `modules/core/stage3_orchestrator.py` | L571-587 | `three_phase_bp.generate(arc_data=arc_data, ...)` |

### 2-C. Stage 4 (원고 집필)

| 파일 | 위치 | 사용 방식 |
|------|------|-----------|
| `modules/core/stage4_context_builder.py` | L363-370 | `arc_tactical = arc_data.get("tactical_doc", "")` -> 에피소드 컨텍스트 |
| `modules/core/stage4_post_processor.py` | - | `arc_data` 참조 (제한적) |
| `modules/domain/agents/director_auditor.py` | L743, L761, L785, L804 | `arc_plan.get("tactical_doc", "")` -> Director 심사 |

### 2-D. DB 저장 경로

| 파일 | 위치 | 사용 방식 |
|------|------|-----------|
| `modules/core/project_manager.py` | L195-201 | `save_v20_anchor("arcs", all_refined_arcs)` -- JSON 직렬화 후 `data_anchors` 테이블 저장 |
| `modules/core/project_manager.py` | L200 | `arcs` 키일 때 dict→list 정규화만 수행, 스키마 검증 없음 |

---

## 3. Stage 2 수정 범위 (파일/함수/난이도)

### 3-1. Gemini API 스키마 추가

**파일**: `modules/core/response_schemas.py`
**위치**: L260-298 (`ARC_DESIGN_SCHEMA`)
**수정**: `properties`에 `episode_detail_map` 추가

```python
# 현재 (L279)
"tactical_doc": types.Schema(type=types.Type.STRING),

# 추가 (L279 이후)
"episode_detail_map": types.Schema(
    type=types.Type.OBJECT,
    description="화별 세부 사건 매핑. key=에피소드번호(str), value=해당 화의 핵심 사건 리스트",
    # Gemini은 동적 키 OBJECT를 additionalProperties로 처리
    # 단, OBJECT의 값을 ARRAY[STRING]으로 강제하려면 별도 처리 필요
),
```

**난이도**: 2줄 추가. 단, `required` 배열에 추가하지 않아야 함 (선택 필드).
**주의**: Gemini `types.Schema`는 `additionalProperties` 미지원이라 동적 키 제약이 있음. `type=types.Type.OBJECT`로만 선언하고 내부 구조는 프롬프트로 유도해야 할 수 있음.

### 3-2. Pydantic 모델 추가

**파일**: `modules/models/arc.py`
**위치**: L183 (`tactical_doc` 뒤)
**수정**: 1줄 추가

```python
# 현재 (L183)
tactical_doc: str | dict = ""

# 추가
episode_detail_map: dict[str, list[str]] = Field(default_factory=dict)
```

**난이도**: 1줄 추가. `extra="allow"`이므로 기존 데이터에 필드가 없어도 문제 없음.

### 3-3. LLM 프롬프트 수정

**파일**: `config/prompts/ensemble.yaml`
**위치**: L86-92 (`ENSEMBLE_ARC_PROMPT` Output JSON Schema 섹션)
**수정**: JSON 스키마 예시에 `episode_detail_map` 추가

```yaml
# 현재 (L92)
"tactical_doc": "...",

# 추가 (L92 이후)
"episode_detail_map": {{
    "{ep_start}": ["첫 화의 핵심 사건 1", "첫 화의 핵심 사건 2"],
    "{ep_start+1}": ["둘째 화의 핵심 사건 1"],
    ...
}},
```

별도 지시문 추가 (~15줄):

```yaml
### [NEW] episode_detail_map 필수 작성 규칙
- tactical_doc의 각 화별 핵심 사건을 구조화된 매핑으로 작성
- key: 에피소드 번호 (문자열, 예: "4", "5")
- value: 해당 화의 핵심 사건/씬 리스트 (최소 2개, 최대 5개)
- 각 항목은 "장소 + 사건" 형태로 구체적으로 작성
- 예: ["승마장에서 아버지와 조우 -- 내면갈등 촉발", "야간 수련 -- 신체 기억 첫 각성"]
- tactical_doc과 episode_detail_map의 내용이 불일치하면 REJECT
```

**난이도**: 15줄 추가. `arc_generator.yaml`의 `ARC_PATCH_MODE_PROMPT`도 보존 지시에 `episode_detail_map` 언급 1줄 추가 필요.

### 3-4. 검증 체인 수정

| 파일 | 함수 | 수정 내용 | 줄 수 |
|------|------|-----------|-------|
| `modules/domain/agents/unified_arc_validator.py` | validate() | `episode_detail_map` 키 존재 + ep_start~ep_end 범위 검증 (선택적 advisory) | ~10줄 |
| `modules/domain/agents/arc_draft_validator.py` | validate() | `episode_detail_map`과 `tactical_doc` 정합성 체크 (advisory) | ~8줄 |
| `modules/domain/agents/continuity_inspector.py` | inspect_arc() | 이전 Arc episode_detail_map 마지막 화와 현재 첫 화 연속성 참조 (선택적) | ~5줄 |

**난이도**: 총 ~23줄 추가. 모두 advisory/선택적 검증이므로 기존 PASS/REJECT 로직에 영향 없음.

### 3-5. 기존 `tactical_doc` 공존 전략

**원칙**: `episode_detail_map`은 보충 필드, `tactical_doc`은 그대로 유지.

- `tactical_doc`: 여전히 화별 전체 서사 텍스트 (LLM이 자유 형식으로 작성)
- `episode_detail_map`: 화별 핵심 사건의 구조화된 인덱스 (정보 검색용)
- 둘 다 LLM이 동시에 생성. `episode_detail_map`이 없어도 기존 로직 동작 (폴백)

---

## 4. Stage 3 수정 범위

### 4-1. BlueprintConstraintCompiler._extract_episode_focus() 개선 -- **최대 수혜자**

**파일**: `modules/domain/agents/blueprint_constraint_compiler.py`
**위치**: L188-234
**현재 로직**: `tactical_doc`에서 정규식으로 "제N화" 섹션 추출 -> 폴백으로 `beat_sequence[position]`
**수정**: `episode_detail_map`을 우선 참조, 없으면 기존 regex 폴백

```python
# 수정 후 의사 코드
def _extract_episode_focus(self, arc_data, ep_num, arc_position):
    # 1차: episode_detail_map 직접 참조 (구조화된 데이터)
    detail_map = arc_data.get("episode_detail_map", {})
    if detail_map:
        ep_key = str(ep_num)
        details = detail_map.get(ep_key, [])
        if details:
            content = "\n".join(f"- {d}" for d in details)
            key_events = details[:5]
            return {"content": content, "key_events": key_events, "arc_position": arc_position}

    # 2차: 기존 regex 로직 (폴백)
    tactical_doc = arc_data.get("tactical_doc", "")
    ...  # 기존 코드 유지
```

**난이도**: ~10줄 추가 (기존 로직 수정 없음, 앞에 분기만 추가).
**효과**: regex 파싱 실패율 0%로 낮아짐. 정보 정확도 대폭 향상.

### 4-2. BlueprintConstraintCompiler._extract_stop_line() 개선

**파일**: `modules/domain/agents/blueprint_constraint_compiler.py`
**위치**: L236-266
**수정**: 동일 패턴 (episode_detail_map 우선 참조)

```python
# 수정 후 의사 코드
def _extract_stop_line(self, arc_data, ep_num, arc_position, ep_count):
    if arc_position >= ep_count:
        return {"content": None, "is_arc_finale": True}

    next_ep = ep_num + 1
    detail_map = arc_data.get("episode_detail_map", {})
    if detail_map:
        next_details = detail_map.get(str(next_ep), [])
        if next_details:
            content = "; ".join(next_details)[:300]
            return {"content": content, "is_arc_finale": False, "next_ep": next_ep}

    # 기존 regex 폴백...
```

**난이도**: ~8줄 추가.

### 4-3. BlueprintEnsembleGenerator.generate_ensemble() arc_focus 보강

**파일**: `modules/domain/agents/blueprint_ensemble.py`
**위치**: L148-154
**현재**: `arc_focus = tactical[:4000]` (전체 tactical_doc 앞 4000자 절삭)
**수정**: episode_detail_map이 있으면 현재 화 세부 사건을 arc_focus 앞에 주입

```python
# 수정 후 의사 코드
arc_focus = constraint_block.get("must_focus", {}).get("content", "")
if not arc_focus:
    # episode_detail_map 우선
    detail_map = arc_data.get("episode_detail_map", {})
    ep_details = detail_map.get(str(ep_num), []) if detail_map else []
    if ep_details:
        arc_focus = f"[이번 화 핵심 사건]\n" + "\n".join(f"- {d}" for d in ep_details)
        arc_focus += f"\n\n[전체 전술서]\n{tactical[:3000]}"
    else:
        arc_focus = tactical[:4000]
```

**난이도**: ~8줄 수정. 기존 분기에 삽입.
**효과**: Blueprint LLM이 "어느 화에 무엇을" 정확히 인지.

### 4-4. Stage 3 Orchestrator TF9 Treatment Block 주입 단순화

**파일**: `modules/core/stage3_orchestrator.py`
**위치**: L512-549 (TF9 Treatment Block 직접 주입)
**현재**: `plot_roadmap[arc_idx]`에서 원본 Treatment Block 필드를 직접 추출하여 보완
**수정**: `episode_detail_map` 존재 시 TF9 보완 경로 스킵 가능 (정보 손실이 이미 해결되므로)

**난이도**: ~5줄 조건 추가. 기존 TF9 코드는 폴백으로 유지.

### 4-5. Smart Context Retrieval (context_advisor.py)

**수정 불필요**. `context_advisor.py`의 `plan_stage2_retrieval` / `plan_stage3_retrieval`은 `arc_data` dict를 통째로 받아 내부적으로 키를 참조하므로, 신규 필드가 추가되어도 무시됨. 향후 `episode_detail_map`을 활용하는 검색 쿼리 개선은 별도 Phase로 분리 권장.

---

## 5. Stage 4 영향 분석

### 5-1. stage4_context_builder.py L363-370

```python
arc_tactical = arc_data.get("tactical_doc", "")
```

`episode_detail_map` 활용 가능 지점이지만, Stage 4는 Blueprint 기반으로 동작하므로 **직접 영향 없음**. Stage 3에서 이미 `episode_detail_map`을 소비하여 Blueprint에 반영된 상태.

### 5-2. director_auditor.py

Director 심사는 `arc_plan.get("tactical_doc", "")`를 전문 전달. `episode_detail_map`이 추가되면 자동으로 JSON에 포함되지만, Director LLM이 이를 참조하는지는 프롬프트에 의존. **수정 불필요** (Director는 전체 JSON을 받으므로 자동 인식).

### 5-3. 결론

**Stage 4는 무영향**. 모든 개선 효과는 Stage 2→3 경로에서 발생하며, Stage 4는 Blueprint를 통해 간접 수혜.

---

## 6. 검증/테스트 범위

### 6-1. 신규 필드 추가 시 깨질 수 있는 테스트

`episode_detail_map`은 **선택 필드**이므로, 기존 테스트의 Arc fixture에 필드가 없어도 깨지지 않음. Pydantic `extra="allow"` + `Field(default_factory=dict)`.

그러나 **엄격한 스키마 검증**을 하는 다음 테스트는 확인 필요:

| 파일 | 리스크 |
|------|--------|
| `tests/test_pydantic_models.py` | `ArcData` 필드 카운트 검증 시 실패 가능 (LOW) |
| `tests/test_integrity.py` | Arc 무결성 검증 (LOW -- `validate_arc` graceful degradation) |
| `tests/e2e/conftest.py` | Arc fixture에 필드 미포함 (LOW -- default_factory) |

### 6-2. 신규 테스트 필요 항목

| 카테고리 | 테스트 | 설명 |
|----------|--------|------|
| Unit | `test_episode_detail_map_pydantic` | ArcData에 episode_detail_map 포함/미포함 검증 |
| Unit | `test_extract_episode_focus_with_map` | BlueprintConstraintCompiler가 map 우선 참조 확인 |
| Unit | `test_extract_stop_line_with_map` | 정지선이 map에서 정확히 추출되는지 확인 |
| Unit | `test_episode_detail_map_fallback` | map이 비어있을 때 기존 regex 로직으로 폴백 확인 |
| Unit | `test_arc_validate_with_map` | validate_arc()가 map 포함 dict를 정상 처리 확인 |
| Integration | `test_stage3_uses_detail_map` | Stage 3가 map을 실제 Blueprint 제약에 반영하는지 |

총 **6개 테스트 추가** 예상.

### 6-3. 기존 테스트 중 tactical_doc 사용 파일 (34개)

`tests/` 하위 34개 파일에서 `tactical_doc` 픽스처 사용 중. 이 중 **수정 필요 없음** -- 기존 fixture에 `episode_detail_map` 키가 없어도 `default_factory=dict`로 빈 dict 반환.

---

## 7. DB 마이그레이션 전략

### 7-1. 현재 DB 구조

Arc 데이터는 `data_anchors` 테이블에 `stage="arcs"` 키로 JSON TEXT 저장:

```sql
-- project_data.db
CREATE TABLE data_anchors (
    stage TEXT PRIMARY KEY,
    data TEXT,         -- JSON 직렬화된 list[dict]
    updated_at TEXT
);
```

`project_manager.py` L195-201의 `save_v20_anchor("arcs", data)`가 JSON 직렬화 후 저장. **스키마 강제 없음** -- 어떤 키든 추가 가능.

### 7-2. 하위 호환성

| 시나리오 | 동작 |
|----------|------|
| 기존 프로젝트 (map 없음) | `arc_data.get("episode_detail_map", {})` -> 빈 dict -> 기존 regex 폴백 |
| 신규 프로젝트 (map 있음) | `episode_detail_map` 우선 참조 -> 정확한 사건 매핑 |
| 구버전 코드 + 신규 데이터 | `extra="allow"`이므로 무시됨. JSON에 남아있지만 코드가 읽지 않음 |

### 7-3. 마이그레이션 필요 여부

**불필요**. 이유:

1. DB에 스키마 강제 없음 (JSON TEXT 컬럼)
2. Pydantic `extra="allow"` + `default_factory=dict`
3. 모든 소비 코드에 `.get("episode_detail_map", {})` 폴백
4. 기존 데이터 무수정으로 동작

### 7-4. (선택적) 기존 데이터 후처리

기존 프로젝트의 Arc에 `episode_detail_map`을 역생성하려면:

```python
# 1회성 스크립트 (선택적)
for arc in all_arcs:
    if "episode_detail_map" not in arc:
        arc["episode_detail_map"] = _regenerate_from_tactical_doc(arc)
```

이는 **선택적**이며 Phase 3 이후에 검토 가능.

---

## 8. 스키마 설계 최종 제안

### 8-1. 필드 구조

```python
# Python 타입
episode_detail_map: dict[str, list[str]]

# JSON 예시
{
    "episode_detail_map": {
        "4": [
            "승마장에서 아버지와 조우 -- 내면갈등 촉발",
            "야간 수련 시작 -- 신체 기억의 첫 징후"
        ],
        "5": [
            "시장 탐색 -- 무기 구매 및 정보 수집",
            "NPC 장대한과 첫 만남 -- 동맹 가능성 암시"
        ],
        "6": [
            "승마 훈련 복선 실현 -- 신체 기억 각성",
            "아크 클라이맥스 -- 첫 실전 적용"
        ]
    }
}
```

### 8-2. 키 타입: str vs int

**str 권장**. 이유:
- JSON 객체 키는 항상 문자열
- Gemini API `types.Schema(type=types.Type.OBJECT)`는 동적 키를 문자열로 처리
- Python에서 `dict[str, ...]`로 통일하면 타입 혼동 없음
- 소비 시 `detail_map.get(str(ep_num), [])` 패턴으로 안전 접근

### 8-3. 값 타입: list[str] vs 구조체

**list[str] 권장**. 이유:
- LLM이 복잡한 중첩 구조보다 문자열 리스트를 더 정확히 생성
- 각 항목에 "장소/인물 -- 사건" 패턴을 프롬프트로 유도하면 충분
- 구조체(`{"scene": "승마장", "event": "조우", "npc": "아버지"}`)는 LLM 출력 실패율 증가

향후 구조체가 필요하면 Phase 2에서 `list[dict]`로 확장 가능 (하위 호환).

### 8-4. 필수 vs 선택

**선택 필드**. 이유:
- Gemini API `required` 배열에 추가하면 기존 프로젝트의 Arc 생성 시 필수 출력을 강제하여 토큰 비용 증가
- Stage 3 소비 코드에서 `.get()` 폴백으로 처리
- 점진적 도입 가능 (프롬프트에서 "권장"으로 시작, 안정화 후 "필수"로 전환)

### 8-5. 빈 값/누락 시 폴백

```python
detail_map = arc_data.get("episode_detail_map") or {}
if not detail_map:
    # 기존 regex 파싱 로직 (tactical_doc에서 추출)
    return self._extract_from_tactical_doc_regex(...)
```

### 8-6. tactical_doc과 중복 최소화

| 역할 | tactical_doc | episode_detail_map |
|------|-------------|-------------------|
| 용도 | 서사 전문 (LLM→LLM 전달) | 구조화된 인덱스 (코드→코드 전달) |
| 형식 | 자유 텍스트 | dict[str, list[str]] |
| 소비자 | Director, Chief Writer (LLM) | BlueprintConstraintCompiler (Python) |
| 길이 | 2000~5000자 | ~500자 |
| 중복 | 필연적 일부 중복 | tactical_doc의 핵심만 구조화 |

**전략**: `tactical_doc`은 LLM 간 서사 전달용으로 유지. `episode_detail_map`은 Python 코드가 정확한 화별 사건을 참조하기 위한 보조 인덱스. 둘 다 LLM이 한 번에 생성하므로 추가 비용은 토큰 ~200개 증가 수준.

---

## 9. 구현 Phase 계획

### Phase 1: 스키마 + 프롬프트 (선행 필수)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| 1-1 | Pydantic 모델에 필드 추가 | `modules/models/arc.py` L183 | 1줄 |
| 1-2 | Gemini API 스키마 추가 (선택 필드) | `modules/core/response_schemas.py` L279 | 2줄 |
| 1-3 | LLM 프롬프트에 생성 지시 추가 | `config/prompts/ensemble.yaml` L86-217 | 20줄 |
| 1-4 | Patch Mode 프롬프트에 보존 지시 | `config/prompts/arc_generator.yaml` L12 | 1줄 |

**선후관계**: 1-1 -> 1-2 -> 1-3 (1-4는 독립)
**예상 수정량**: 4개 파일, ~24줄

### Phase 2: Stage 3 소비 코드 (Phase 1 완료 후)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| 2-1 | _extract_episode_focus() 개선 | `blueprint_constraint_compiler.py` L188 | 10줄 |
| 2-2 | _extract_stop_line() 개선 | `blueprint_constraint_compiler.py` L236 | 8줄 |
| 2-3 | arc_focus 보강 | `blueprint_ensemble.py` L148 | 8줄 |
| 2-4 | TF9 조건 추가 (선택적) | `stage3_orchestrator.py` L512 | 5줄 |

**선후관계**: 2-1, 2-2는 독립. 2-3은 2-1과 함께.
**예상 수정량**: 3개 파일, ~31줄

### Phase 3: 검증 체인 보강 (Phase 1 완료 후, Phase 2와 병렬 가능)

| # | 작업 | 파일 | 난이도 |
|---|------|------|--------|
| 3-1 | Arc 검증에 map 정합성 체크 | `unified_arc_validator.py` | 10줄 |
| 3-2 | DraftValidator에 map 체크 | `arc_draft_validator.py` | 8줄 |
| 3-3 | ContinuityInspector map 참조 | `continuity_inspector.py` | 5줄 |

**예상 수정량**: 3개 파일, ~23줄

### Phase 4: 테스트 (Phase 1-3 완료 후)

| # | 작업 | 설명 |
|---|------|------|
| 4-1 | 단위 테스트 6개 추가 | Pydantic + ConstraintCompiler + 폴백 |
| 4-2 | 기존 테스트 그린 확인 | `pytest tests/ -q` 2,537개 통과 확인 |
| 4-3 | E2E smoke 테스트 | Stage 2→3 파이프라인에서 map 전달 확인 |

**예상 수정량**: 1-2개 파일, ~100줄 (테스트 코드)

### 전체 타임라인

```
Phase 1 (스키마+프롬프트)     ████  (1시간)
Phase 2 (Stage 3 소비 코드)   ████████  (2시간)
Phase 3 (검증 체인 보강)       ██████  (1.5시간)  ← Phase 2와 병렬 가능
Phase 4 (테스트)              ████████████  (3시간)
                              ─────────────────────
                              총 ~5.5시간 (Phase 2+3 병렬 시)
```

---

## 10. 리스크 목록

| # | 리스크 | 등급 | 설명 | 완화 방안 |
|---|--------|------|------|-----------|
| R1 | LLM이 `episode_detail_map` 생성 실패 | **MED** | Gemini가 JSON 동적 키 OBJECT를 잘못 생성할 수 있음 | 선택 필드 + regex 폴백 유지. Gemini `response_schema` 대신 프롬프트 유도 |
| R2 | `episode_detail_map`과 `tactical_doc` 불일치 | **MED** | LLM이 둘을 독립적으로 생성하면 내용이 다를 수 있음 | 프롬프트에 "tactical_doc 작성 후 episode_detail_map을 tactical_doc에서 추출" 지시 |
| R3 | 토큰 비용 증가 | **LOW** | 추가 필드로 출력 토큰 ~200개 증가 | Arc당 ~$0.001 수준. 연간 수천 Arc 기준 무시 가능 |
| R4 | 기존 프로젝트 데이터 비호환 | **LOW** | 기존 Arc에 필드 없음 | `default_factory=dict` + `.get()` 폴백으로 완전 호환 |
| R5 | SelfReflector/ASP 경로에서 map 소실 | **LOW** | SelfReflector가 Arc JSON을 재구성할 때 episode_detail_map 누락 가능 | `extra="allow"` Pydantic이 미지원 키도 보존. JSON 직렬화/역직렬화 시 유지 |
| R6 | Gemini Schema 동적 키 미지원 | **MED** | `types.Schema`에 `additionalProperties` 없음. 동적 에피소드 번호를 키로 사용 불가 | Gemini `response_schema`에서 `episode_detail_map` 제외 (프롬프트 유도만 사용), 또는 `ARRAY[OBJECT]` 형태로 변경 (`[{"ep": 4, "details": [...]}]`) |

### R6 대안 (Gemini Schema 제약 우회)

Gemini API의 `response_schema`는 동적 키 OBJECT를 지원하지 않을 수 있음. 두 가지 대안:

**대안 A**: `response_schema`에서 `episode_detail_map` 제외, 프롬프트로만 유도
- 장점: 스키마 수정 최소
- 단점: LLM이 필드를 빠뜨릴 수 있음 (폴백으로 해결)

**대안 B**: ARRAY 형태로 변환
```json
"episode_details": [
    {"ep_num": 4, "details": ["사건1", "사건2"]},
    {"ep_num": 5, "details": ["사건1"]}
]
```
- 장점: Gemini Schema에 정확히 표현 가능
- 단점: dict 키 접근(`detail_map[str(ep)]`) 대신 리스트 검색 필요

**권장**: 대안 A (Phase 1에서 프롬프트 유도, 안정화 후 대안 B 검토)

---

## 부록: 핵심 코드 스니펫 참조

### A-1. 현재 _extract_episode_focus (문제 코드)

```python
# modules/domain/agents/blueprint_constraint_compiler.py L188-234
def _extract_episode_focus(self, arc_data: dict, ep_num: int, arc_position: int) -> dict:
    tactical_doc = arc_data.get("tactical_doc", "")
    if isinstance(tactical_doc, dict):
        tactical_doc = json.dumps(tactical_doc, ensure_ascii=False, indent=2)
    content = ""
    for pattern_template in self._EPISODE_HEADER_PATTERNS:
        pattern = pattern_template.format(ep=ep_num)
        match = re.search(pattern, tactical_doc, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if content:
                break
    if not content:
        beats = arc_data.get("beat_sequence", [])
        if arc_position - 1 < len(beats):
            content = beats[arc_position - 1]
    ...
```

### A-2. 현재 arc_focus 추출 (blueprint_ensemble.py L148-154)

```python
arc_focus = constraint_block.get("must_focus", {}).get("content", "")
if not arc_focus:
    tactical = arc_data.get("tactical_doc", "")
    if isinstance(tactical, dict):
        tactical = json.dumps(tactical, ensure_ascii=False)
    arc_focus = tactical[:4000]  # 4000자 절삭
```

### A-3. 현재 TF9 Treatment Block 주입 (stage3_orchestrator.py L512-549)

```python
# Arc 압축 정보 손실 보완을 위해 Treatment Block을 직접 주입
_plot_roadmap = _bible_root.get("plot_roadmap", [])
if isinstance(_plot_roadmap, list) and 0 <= arc_idx < len(_plot_roadmap):
    _block = _plot_roadmap[arc_idx]
    # ... Treatment Block 필드 추출 ...
    _bp_semantic_ctx = _tb_text + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")
```

---

**문서 끝**

---

## 11. 3-시각 재검토 결과 (2026-02-24)

> 회의론(A) / 아키텍처(B) / 구현 리스크(C) 3개 OPUS 에이전트 독립 검토

### 11-1. 3개 시각이 수렴한 결론

| 항목 | 내용 |
|------|------|
| 스키마 타입 변경 | `dict[str, list[str]]` → `list[dict]` 필수. 필드명 `episode_details` 권장 |
| TF9 독립 유지 | `episode_details`는 TF9(Treatment Block 직접 주입)를 대체 불가. 정보 원천이 다름 |
| 측정 선행 | `_extract_episode_focus()` regex 실패율 계측 없이 설계된 점 — 실패율 데이터 선확보 권장 |

### 11-2. TF-10이 과소평가하거나 미언급한 HIGH 위험

#### EC-1. ArcCorrector 수정 후 episode_details 불일치 [HIGH — TF-10 미언급]
`arc_corrector.py`가 `tactical_doc`의 특정 화를 수정하면 `episode_details`는 수정 전 내용 그대로 잔존.
`_extract_episode_focus()`가 `episode_details` 우선 참조하면 잘못된 정보가 Blueprint로 전달됨.
**완화**: ArcCorrector 수정 성공 시 해당 화 항목 삭제 → regex 폴백 강제 (전략 A, ~3줄)

#### EC-2. ASP 경로 전체 Arc 교체로 map 소실 [HIGH — TF-10은 LOW로 과소평가]
`four_phase_arc_generator.py` ASP 경로가 `best_arc = _asp_arc`로 Arc 통째 교체.
ASP LLM 출력에 `episode_details` 없으면 소실 확정.
**완화**: ASP 교체 전 원본 map 백업, ASP 결과에 없으면 복원 (~5줄)

### 11-3. 구현 전 선결 조건

| # | 조건 | 규모 |
|---|------|------|
| P1 | Gemini `response_schema` 실제 사용 경로 확인 (arc_ensemble / four_phase) | 코드 확인만 |
| P2 | ASP 경로 map 복원 로직 추가 (`four_phase_arc_generator.py` L376 부근) | ~5줄 |
| P3 | ArcCorrector 동기화 전략 결정 및 구현 (전략 A: 해당 화 항목 삭제) | ~3줄 |

### 11-4. 테스트 계획 확대

TF-10 원안 6개 → 14개로 확대

추가 8개:
- `test_arc_corrector_preserves_map` — ArcCorrector 수정 후 map dict 잔존 확인
- `test_arc_corrector_map_sync_warning` — tactical_doc 수정 후 불일치 감지
- `test_asp_preserves_map` — ASP 경로 map 복원 확인
- `test_patch_mode_regenerates_map` — Patch Mode 후 map 포함 여부
- `test_detail_map_type_normalization` — 값이 str일 때 list[str]로 정규화
- `test_detail_map_int_key_fallback` — int 키 접근 시 str 폴백
- `test_evaluate_candidate_map_bonus` — map 있는 후보 채점 보너스
- `test_tactical_doc_map_consistency_reject` — 불일치 시 REJECT 트리거

### 11-5. 수정된 Phase 계획

Phase 1-4 구조는 유지하되:
- **Phase 0 (선결, 신규)**: P1~P3 선결 조건 해소
- **Phase 1.5 (검증 게이트, 신규)**: 실제 Gemini 출력 1~2개 수집 후 episode_details 생성률 확인. 70% 미만이면 프롬프트 재조정 후 진행
- **Phase 2+3 병렬 → 순차 변경**: 키 해석 규칙 확정 후 검증 체인 작성

### 11-6. 최종 판정

| 시각 | 판정 |
|------|------|
| A (회의론) | 수정 후 진행 |
| B (아키텍처) | 조건부 승인 |
| C (구현 리스크) | 선결 조건 해소 후 진행 |

**종합**: 방향성 유효. 선결 3건(P1~P3) + 스키마 타입 변경(`list[dict]`) 반영 후 Phase 0부터 진입.
