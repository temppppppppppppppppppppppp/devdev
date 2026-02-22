# NPC 생애주기(Lifecycle) 데이터 흐름 전면 감사 보고서

**작성일**: 2026-02-22
**감사자**: Claude Opus 4.6 (TF-4차)
**범위**: NPC 생성 ~ 사망 ~ 롤백 전 경로 추적, 데이터 유실 지점 식별

---

## 목차

1. [NPC 생성 경로 (Stage 0)](#1-npc-생성-경로-stage-0)
2. [NPC 등장 추적 (Stage 2/3/4)](#2-npc-등장-추적-stage-234)
3. [NPC 속성 변경 기록](#3-npc-속성-변경-기록)
4. [NPC 사망 처리](#4-npc-사망-처리)
5. [NPC 과잉 등장 경고 (3-5C)](#5-npc-과잉-등장-경고-3-5c)
6. [데이터 유실 지점 분석](#6-데이터-유실-지점-분석)
7. [에피소드 롤백 시 NPC 되감기 (D-2)](#7-에피소드-롤백-시-npc-되감기-d-2)
8. [deceased 검증 커버리지](#8-deceased-검증-커버리지)
9. [발견 사항 총괄표](#9-발견-사항-총괄표)

---

## 1. NPC 생성 경로 (Stage 0)

### 1.1 Bible 내 NPC 정의

NPC는 Stage 0에서 Bible의 `MasterBible.AssetLibrary.KeyNPCs` 배열로 정의된다.

**경로**: `modules/core/stage0/story_expander.py:211-213`

```python
"AssetLibrary": {
    "KeyNPCs": npcs,
},
```

StoryExpander가 LLM에게 NPC 목록 생성을 요청하고, 결과를 Bible JSON에 삽입한다. 각 NPC는 장르별 NPC HUD 키(`NPCHUDKeys`)에 따른 속성 블록을 포함한다.

**장르별 NPC HUD 키** (`modules/core/constants.py:468-496`):
- 무협: `NPC_Martial_HUD`
- 헌터: `NPC_Hunter_Status`
- 투자: `NPC_Business_Profile`
- 판타지: `NPC_Fantasy_Status`
- 작곡가: `NPC_Music_Profile`
- 요리: `NPC_Cooking_Profile`
- 대체역사: `NPC_Joseon_Status`
- 배우: `NPC_Actor_Profile`
- 스포츠: `NPC_Sports_Profile`
- 의학: `NPC_Medical_Profile`

### 1.2 PresetRegistry NPC 스키마

**경로**: `modules/core/stage0/preset_registry.py:275-410`

- `NPC_COMMON_PRESET` (L275-289): 공통 필드 — name, status(`alive/dead/injured/missing/unknown`), role, relationship, first_appearance, last_seen_arc, description
- `NPC_GENRE_PRESETS` (L291-410): 장르별 확장 필드 — 무협(faction, rank, martial_arts, weapon, karma, title), 헌터(guild, awakening_rank, class, skills, level) 등 12개 장르

**NPC 템플릿 생성**: `PresetRegistry.build_npc_template()` (L635-646) — 프리셋 기반 기본값으로 NPC dict 생성

### 1.3 Pydantic 모델

**경로**: `modules/models/npc.py:20-34`

```python
class NPCEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    status: str = "alive"
    weapon: str = ""
    level: str = ""
    death_arc: int | None = None
    last_arc: int = 0
```

`validate_npc_entry()` (L36-43): graceful degradation — 검증 실패 시 원본 dict 유지. NPC 모델은 `extra="allow"`로 PresetRegistry 기반 동적 필드를 수용한다.

### 1.4 역설계 경로

**경로**: `modules/core/stage0/reverse_expander.py`

역설계 시에도 동일하게 Bible JSON 내 `AssetLibrary.KeyNPCs` 배열로 NPC가 추출된다. `ReverseExpander`가 기존 원고에서 NPC 정보를 역추출한다.

---

## 2. NPC 등장 추적 (Stage 2/3/4)

### 2.1 StateTracker 초기화

NPC 등장 추적의 핵심은 `StateTracker` 클래스이다.

**정의**: `modules/domain/agents/state_tracker.py:96-175`

```python
class StateTracker:
    def __init__(self, preset_registry=None, llm_client=None):
        self.npc_registry: dict[str, dict] = {}  # name -> {프리셋 기반 필드들}
        self.protagonist_skills: set[str] = set()
        self.skill_acquisitions: dict[str, int] = {}
        ...
```

**초기화 경로 3곳**:

| 위치 | 파일:라인 | 설명 |
|------|-----------|------|
| Stage 2 | `stage2_orchestrator.py:148-163` | `full_extract_from_arcs()` 호출하여 기존 Arc에서 NPC 상태 복원 |
| Stage 3 | `stage3_orchestrator.py:182-203` | lazy init — `app.state_tracker` 미설정 시 생성 |
| Stage 4 (직행) | `main_a.py:3004-3021` | Stage 3 없이 Stage 4 직행 시 별도 초기화 |

### 2.2 full_extract_from_arcs — 17개 추출 메서드

**경로**: `modules/domain/agents/state_tracker.py:184-249`

Arc 목록 순회하며 다음 17개 메서드를 호출:
1. `extract_npc_deaths_from_arc()` — 사망 추출 (state_changes > regex 폴백)
2. `extract_skill_acquisitions_from_arc()` — 무공/스킬 습득
3. `extract_npc_info_from_arc()` — NPC 무장/수준 (무협 only)
4. `extract_resolved_plots_from_arc()` — 완결 플롯
5. `extract_time_markers_from_arc()` — 시간선 마커
6. `extract_permanent_injuries_from_arc()` — 영구 부상
7. `update_companions_from_arc()` — 동행자 추적
8. `extract_commitments_from_arc()` — 약속/맹세
9. `extract_protagonist_emotion_from_arc()` — 감정 상태
10. `extract_item_states_from_arc()` — 아이템 상태
11. `extract_entity_destructions_from_arc()` — 엔티티 파괴
12. `extract_npc_personality_from_arc()` — NPC 성격
13. `extract_npc_npc_relationships_from_arc()` — NPC 간 관계
14. `extract_npc_dialogue_styles_from_arc()` — NPC 대화 스타일
15. `extract_relationship_changes_from_arc()` — 관계 변화
16. `extract_npc_injuries_from_arc()` — NPC 부상
17. `extract_npc_movements_from_arc()` — NPC 이동

### 2.3 StateTrackerNPC 서브모듈

**경로**: `modules/domain/agents/state_tracker_npc.py` (1,200+줄)

`StateTracker._npc` 속성으로 접근. 핵심 기능:
- `register_npc_death()` (L124-145): 사망 등록 + DB 이력 기록
- `register_npc_info()` (L147-199): NPC 정보 갱신 + DB 이력 기록
- `check_dead_npc_appearance()` (L369-430): 죽은 NPC 행동/대사 감지
- `check_npc_changes()` (L201-277): NPC 무장/수준 변경 경고
- `get_entity_registry()` (L488-528): Director/Validator용 NPC 정보 반환
- `merge_npc_registry()` (L530-560): 다른 StateTracker NPC 레지스트리 병합
- `revive_npc()` (L1185-1226): 사망 오탐 수정 (F-10)
- `check_dead_npc_in_blueprint()` (L1232+): Blueprint 내 죽은 NPC 감지

### 2.4 entity_registry 흐름

`get_entity_registry()` (L488-528) 반환값:
```python
{
    "dead_npcs": [{"name": ..., "death_arc": ...}],
    "npc_info": [{"name": ..., "weapon": ..., "level": ..., "status": ..., "last_arc": ...}],
    "protagonist_skills": [...],
    "protagonist_items": [...]
}
```

이 데이터는 `director_continuity.py`, `continuity_arc.py`, `director_ensemble.py` 등에서 entity 일관성 검증에 사용된다.

---

## 3. NPC 속성 변경 기록

### 3.1 npc_history 테이블

**정의**: `modules/core/db_manager.py:384-398`

```sql
CREATE TABLE IF NOT EXISTS npc_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    npc_name TEXT NOT NULL,
    episode_no INTEGER,
    arc_no INTEGER,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

인덱스: `idx_npc_history_name` (npc_name), `idx_npc_history_arc` (arc_no)

### 3.2 이력 기록 API

| 메서드 | 위치 | 설명 |
|--------|------|------|
| `insert_npc_change()` | `db_manager.py:1709-1727` | append-only 삽입 |
| `get_npc_history()` | `db_manager.py:1729-1737` | NPC별 변경 이력 조회 (최신순) |
| `get_npc_latest_fields()` | `db_manager.py:1739-1749` | 필드별 최신 값 |

### 3.3 StateTracker -> DB 연결

**경로**: `modules/domain/agents/state_tracker.py:1028-1042`

```python
def bind_db(self, db_manager) -> None:
    """[Phase 3-5A] DB 매니저 바인딩. 호출측(main_a 등)에서 설정."""
    self._db = db_manager
```

### 3.4 [CRITICAL] bind_db 미호출 문제

> **위험도: HIGH**

`bind_db()`는 `StateTracker._db`를 설정하여 NPC 변경 이력이 DB에 기록되도록 한다. 그러나 **프로덕션 코드에서 `bind_db()`가 한 번도 호출되지 않는다.**

**검증 결과**:
- `main_a.py`: `bind_db` 호출 없음
- `modules/core/stage2_orchestrator.py`: `bind_db` 호출 없음
- `modules/core/stage3_orchestrator.py`: `bind_db` 호출 없음
- `modules/core/stage4_orchestrator.py`: `bind_db` 호출 없음
- **테스트에서만 호출**: `tests/e2e/conftest.py:157`, `tests/test_npc_history.py`

**영향**: `_record_change()` (L94-118)가 `self.tracker._db`를 확인하여 None이면 아무것도 하지 않으므로, **프로덕션 환경에서 NPC 변경 이력이 DB에 전혀 기록되지 않는다.** `npc_history` 테이블은 항상 비어있다.

**권고**: `stage2_orchestrator.py` 또는 `stage3_orchestrator.py`의 StateTracker 초기화 직후에 `state_tracker.bind_db(current_project.db)` 호출 추가. 3곳 모두에 적용 필요.

---

## 4. NPC 사망 처리

### 4.1 사망 등록 경로

| 경로 | 위치 | 메커니즘 |
|------|------|----------|
| state_changes 기반 | `state_tracker_npc.py:581-603` | `state_changes.npc_deaths` 배열 직접 읽기 (정확도 ~98%) |
| Regex + LLM 폴백 | `state_tracker_npc.py:605-636` | tactical_doc에서 regex 추출 후 LLM 검증 |
| `register_npc_death()` | `state_tracker_npc.py:124-145` | 최종 등록: `status="dead"`, `death_arc`, `death_context` 설정 |

### 4.2 사망 정보 보호

`merge_npc_registry()` (L530-554)에서 **사망 상태 보존 로직** 구현:

```python
if existing.get("status") == "dead" and info.get("status") != "dead":
    continue  # 사망 상태 보존
```

### 4.3 사망 등록 취소 (F-10)

`revive_npc()` (L1185-1226): 명시적 호출로만 동작. 오탐 수정용.
- 사망 정보 백업 후 `status="alive"` 복원
- `revive_history` 배열에 부활 이력 기록

### 4.4 dead_npcs의 두 가지 소스

Stage 4에서 dead_npcs 정보는 **두 가지 독립적 소스**에서 온다:

| 소스 | 위치 | 데이터 |
|------|------|--------|
| cumulative_bible | `stage4_context_builder.py:374-378` | `db.get_cumulative_bible(next_ep-1).dead_npcs` — episode_bibles 테이블 기반 |
| npc_registry | `stage4_interview_round.py:281-292` | `state_tracker.npc_registry` — Arc 추출 기반 |

> **위험**: 두 소스의 dead_npcs 목록이 불일치할 수 있다. cumulative_bible은 episode_bibles 테이블의 `npc_deaths` JSON 필드에서 오고, npc_registry는 Arc의 state_changes에서 추출된다. LLM이 episode_bible에는 사망을 기록하지 않았지만 Arc tactical_doc에는 사망이 언급된 경우 불일치 발생.

---

## 5. NPC 과잉 등장 경고 (3-5C)

### 5.1 핵심 함수

**경로**: `modules/core/stage4_orchestrator.py:26-76`

```python
def _detect_npc_overexposure(
    manuscript, npc_names, protagonist_name="",
    *, max_mentions=None, core_npc_names=frozenset(), min_name_length=2
):
```

- **advisory-only**: 경고만 출력, 파이프라인 동작에 영향 없음
- **Longest-match-first 마스킹**: 이중 카운트 방지 (`"흑풍대사" 카운트 → "흑풍" 마스킹)
- **제외 대상**: 주인공, 핵심 NPC(`core_npc_names`), 짧은 이름(min_name_length 미만)

### 5.2 임계값 설정

**경로**: `config/settings/validation.yaml:147-150`

```yaml
npc_exposure:
  max_mentions_per_episode: 15
  min_name_length: 2
```

### 5.3 호출 경로

`stage4_post_processor.py:575-614` — PASS 후 후처리에서 호출:

```python
if detect_npc_overexposure_fn:
    _overexposure = detect_npc_overexposure_fn(
        manuscript_text, _npc_names,
        protagonist_name=..., max_mentions=_max_m,
        core_npc_names=frozenset(_core_npc_names), min_name_length=_min_len
    )
```

### 5.4 테스트 커버리지

`tests/test_stage4_orchestrator.py:545-668` — 10개 테스트 케이스:
- 기본 미초과, 초과, 주인공 제외, 기본 임계값, 핵심 NPC 제외, 짧은 이름 제외, longest-match 마스킹

---

## 6. 데이터 유실 지점 분석

### 6.1 [HIGH] Stage 2 -> 3: state_constraints에 NPC 정보 미포함

**위치**: `modules/core/stage2_orchestrator.py:600-641`

`state_constraints`는 Arc 구조의 일부로, `items_acquired` 필드만 활용된다. **NPC 정보(등장, 관계 변화, 사망)는 `state_constraints`에 포함되지 않는다.** NPC 정보는 별도로 Arc의 `state_changes` 블록과 `tactical_doc` 내 서술로 전달된다.

그러나 Stage 3 Blueprint 생성 시 **StateTracker가 Arc의 state_changes에서 NPC 정보를 재추출**하므로, `state_constraints` 미포함이 직접적 유실은 아니다. NPC 정보는 `tactical_doc`과 `state_changes` 경로로 전달된다.

**위험도: LOW** — 구조적으로는 정상이나, LLM이 `state_changes.npc_deaths`를 누락하면 regex 폴백에 의존하게 되어 정확도 저하 가능.

### 6.2 [HIGH] Stage 3 -> 4: dead_npcs 이중 소스 불일치

**위치**:
- `stage4_context_builder.py:374-378` (cumulative_bible 기반)
- `stage4_interview_round.py:281-292` (npc_registry 기반)

**시나리오**:
1. Arc에서 NPC 사망이 `tactical_doc`에만 언급되고 `state_changes.npc_deaths`에는 없음
2. StateTracker regex가 사망 감지 -> `npc_registry`에 등록
3. 그러나 `episode_bibles.npc_deaths`에는 기록 안 됨
4. `cumulative_bible.dead_npcs`에는 누락
5. ChiefWriter에게 전달되는 `dead_npcs`(cumulative_bible 기반)에는 해당 NPC 미포함
6. ChiefWriter가 사망 NPC를 등장시킬 수 있음
7. 하지만 BlockingValidator는 `npc_registry` 기반으로 검증하므로 REJECT

**결과**: ChiefWriter 초안에서 사망 NPC가 등장 -> BlockingValidator REJECT -> 재작성 루프 발생. 직접적 부활은 방지되지만 불필요한 재시도 비용 발생.

**위험도: MEDIUM** — 안전성은 확보되나 효율성 저하.

### 6.3 [MEDIUM] Stage 4 내부: Director 피드백과 NPC 이름 불일치

**위치**: `stage4_orchestrator.py:390-411`

`npc_equipment_summary`는 `MasterBible.AssetLibrary.KeyNPCs`에서 추출된다. NPC 이름은 Bible에 기록된 원본 이름을 사용한다. 반면, `state_tracker.npc_registry`의 NPC 이름은 Arc의 `tactical_doc`에서 regex로 추출된 것이다.

**시나리오**: Bible에서 "흑풍대도"로 등록된 NPC가 tactical_doc에서 "흑풍"으로만 언급되면, npc_registry에는 "흑풍"으로 등록되고 Bible에는 "흑풍대도"로 남아 불일치 발생.

**영향**:
- npc_equipment_summary에는 "흑풍대도"로 표시
- npc_registry에는 "흑풍"으로 표시
- 동일 NPC의 별명/약칭으로 이중 추적될 수 있음

**위험도: MEDIUM** — `_is_standalone_name()` 경계 검증이 부분적으로 완화하지만, 근본적 해결 아님.

### 6.4 [CRITICAL] bind_db 미호출 — NPC 이력 DB 미기록

위 3.4절 참조. 프로덕션에서 NPC 변경 이력이 DB에 전혀 기록되지 않음.

**위험도: HIGH** — Phase 3-5A의 핵심 기능이 프로덕션에서 비활성 상태.

### 6.5 [LOW] extract_npc_info_from_arc 장르 제한

**위치**: `state_tracker_npc.py:279-338`

```python
if genre and genre != "wuxia":
    return []
```

무협 외 장르에서는 NPC 무장/수준 regex 추출이 완전히 비활성화된다. 이는 오탐 방지를 위한 의도적 설계이나, 비무협 장르에서 NPC 정보 추적이 `state_changes` 블록에만 의존하게 된다.

**위험도: LOW** — 의도적 설계. 비무협 장르의 NPC 추적은 LLM의 `state_changes` 출력 품질에 전적으로 의존.

---

## 7. 에피소드 롤백 시 NPC 되감기 (D-2)

### 7.1 DB 레벨 롤백

**경로**: `modules/core/db_manager.py:1490-1514` (`reset_project` 메서드)

```python
self.cursor.execute("DELETE FROM npc_history WHERE episode_no >= ?", (target_ep,))
```

`npc_history` 테이블은 롤백 시 정상 삭제된다. 그러나 위 6.4에서 확인한 바와 같이, 프로덕션에서 이 테이블에 데이터가 기록되지 않으므로 실질적 효과 없음.

### 7.2 WorldState 롤백

**경로**: `modules/core/world_state.py:433-462`

WorldState는 `episode_bibles` 리플레이로 롤백한다. 이 과정에서 `state_changes`의 NPC 관련 변경사항도 재적용된다.

### 7.3 FactLedger 롤백

**경로**: `modules/core/fact_ledger.py:558-584`

FactLedger도 `episode_bibles` 리플레이 방식. NPC 관련 사실(이름, 관계 등)이 팩트 원장에서 롤백된다.

### 7.4 [CRITICAL] StateTracker npc_registry 미롤백

**위치**: `modules/core/services/project_service.py:86-219`

`rollback_episode()` 메서드에서 수행하는 작업:
1. HUD 롤백 (state_logs 기반)
2. SQL 테이블 삭제 (manuscripts, blueprints, state_logs 등)
3. Lore/Seeds 초기화
4. Episode Bibles 삭제
5. 파일 삭제
6. 벡터 DB 소거
7. DB 리로드

**누락된 작업**: `state_tracker.npc_registry` 초기화/재구축

**시나리오**:
1. 5화까지 집필 완료, NPC "흑풍"이 3화에서 사망 등록됨
2. 사용자가 2화로 롤백
3. DB 데이터는 정상 삭제됨
4. **`state_tracker.npc_registry`에는 "흑풍" 사망 상태가 그대로 남아있음**
5. 3화 재집필 시 "흑풍"이 사망 NPC로 취급되어 등장 불가
6. 실질적으로 2화 이전에 사망하지 않은 NPC가 차단됨

**완화 요인**: Stage 2 진입 시 `stage2_orchestrator.py:148-164`에서 StateTracker를 재생성한다:

```python
if (
    self.ctx.state_tracker is None
    or existing_tracker_arcs == 0
    or existing_tracker_arcs > len(all_refined_arcs)  # [V62.5] Arc 삭제 감지 → 리셋
):
    self.ctx.state_tracker = StateTracker(...)
```

`existing_tracker_arcs > len(all_refined_arcs)` 조건에 의해 Arc가 삭제되면(롤백) StateTracker가 리셋된다. **하지만 이는 Stage 2를 다시 실행할 때만 적용되며, Stage 4로 직접 진입하면 적용되지 않는다.**

Stage 4 직행 시(`main_a.py:3004-3021`)에도 StateTracker를 재생성하지만, 이는 `state_tracker is None` 조건에서만 트리거된다. 롤백 후 `state_tracker`가 이미 존재하면 재생성하지 않는다.

**위험도: HIGH** — 롤백 후 Stage 4 직행 시 stale NPC 상태로 인한 잘못된 REJECT 발생 가능.

**권고**: `rollback_episode()` 실행 후 `self.state_tracker = None`으로 리셋하여 다음 Stage 진입 시 재생성 강제.

### 7.5 auto_backtrack_v35의 추가 롤백

**경로**: `modules/core/project_manager.py:875-922`

자동 되감기에서는 추가로:
- `world_state.rollback_to(target_ep)` 호출
- `fact_ledger.rollback_to(target_ep)` 호출

그러나 여기서도 **`state_tracker` 리셋은 수행하지 않는다.** `reset_project()` 내에서 `npc_history` DB 삭제는 수행하지만, 인메모리 `npc_registry`는 그대로.

---

## 8. deceased 검증 커버리지

### 8.1 사망 NPC 부활 방지가 적용되는 위치

| 검증 지점 | 위치 | Stage | 메커니즘 |
|-----------|------|-------|----------|
| Arc tactical_doc | `state_tracker_npc.py:369-430` (`check_dead_npc_appearance`) | Stage 2 | npc_registry 기반, 회상/과거 언급 허용 |
| Arc Validator | `unified_arc_validator.py:195` | Stage 2 | `state_tracker.check_dead_npc_appearance()` 위임 |
| Arc Draft Validator | `arc_draft_validator.py:846` | Stage 2 | 동일 |
| Blueprint | `state_tracker_npc.py:1232+` (`check_dead_npc_in_blueprint`) | Stage 3 | integrated_scenario + scene_breakdown 검사 |
| Blueprint Validator | `unified_blueprint_validator.py:149` | Stage 3 | `state_tracker.check_dead_npc_in_blueprint()` 위임 |
| Director Ensemble | `director_ensemble.py:202` | Stage 3 | Blueprint 선택 시 사망 NPC 등장 검사 |
| Manuscript (Blocking) | `blocking_validator_entity_checks.py:58-101` | Stage 4 | encyclopedia.npcs에서 dead 상태 NPC 검사, 회상 패턴 허용 |
| Chief Writer 프롬프트 | `chief_writer_context.py:55-93` | Stage 4 | dead_npcs 목록을 프롬프트에 주입하여 사전 방지 |
| Fallback Constitution | `validation_orchestrator.py:918` | Stage 4 | "사망한 NPC는 등장할 수 없다" 규칙 |

### 8.2 검증 누락 위치

| 누락 지점 | 설명 | 위험도 |
|-----------|------|--------|
| Director 피드백 | Director가 피드백으로 "흑풍을 등장시켜라"고 지시할 수 있음. Director는 npc_registry를 직접 참조하지 않고 프롬프트 텍스트만 확인 | LOW — ChiefWriter 재작성 후 BlockingValidator가 차단 |
| Patch Mode (수정 모드) | Stage 2/3 패치 모드에서 기존 Arc 수정 시, StateTracker가 패치 전 상태로 초기화되는지 불확실 | LOW — 패치 모드는 Arc 단위 재생성이므로 StateTracker 재추출 |
| Stage 2 Arc Ensemble | 앙상블 후보 3개 중 사망 NPC 등장 검사는 최종 선택 후에만 실행 | LOW — 선택 전 검사면 불필요한 LLM 비용 절감 |

### 8.3 회상/언급 판별 패턴

**BlockingValidator** (`blocking_validator_entity_checks.py:18-36`):
```python
_RECALL_PATTERNS = ("회상", "과거", "기억", "떠올리", "그때", "예전에", "했었다", "했던",
                    "였던", "이었다", "말했었", "죽은", "생전에", "살아있을 때", "고인", "영전에", "추모")

_ACTION_PATTERNS = ("말했다", "말한다", "외쳤다", "소리쳤다", "웃었다", "웃으며", "걸어", "달려",
                    "싸우", "공격", "막았다", "들었다", "일어나", "나타나", "등장", "다가와", "다가오")
```

**StateTrackerNPC** (`state_tracker_npc.py:393-406`):
```python
flashback_patterns = [
    f"{npc_name}의 죽음", f"{npc_name}을 떠올", f"{npc_name}를 떠올",
    f"고인이 된 {npc_name}", f"죽은 {npc_name}",
    f"{npc_name}의 유언", f"{npc_name}의 무덤",
    f"{npc_name}의 원혼", f"{npc_name}의 유품",
]
```

> **문제**: 두 검증 지점의 회상 판별 패턴이 상이하다. BlockingValidator는 문맥 윈도우(전후 100자) 내 패턴 매칭 방식이고, StateTrackerNPC는 전체 텍스트 내 특정 조합 패턴 검사 방식이다. 동일 원고에 대해 서로 다른 판정을 내릴 수 있다.

**위험도: LOW** — 두 검증이 독립적으로 동작하고, BlockingValidator가 최종 게이트키퍼이므로 안전성은 확보됨.

---

## 9. 발견 사항 총괄표

| # | ID | 위치 | 위험도 | 시나리오 | 권고 조치 |
|---|-----|------|--------|----------|-----------|
| 1 | NPC-L1 | `stage2_orchestrator.py:152`, `stage3_orchestrator.py:189`, `main_a.py:3008` | **HIGH** | `bind_db()` 프로덕션 미호출 → NPC 변경 이력 DB 미기록. Phase 3-5A 핵심 기능 비활성 | StateTracker 생성 직후 `state_tracker.bind_db(current_project.db)` 호출 추가 (3곳) |
| 2 | NPC-L2 | `services/project_service.py:86-219` | **HIGH** | 롤백 후 `state_tracker.npc_registry` 미리셋 → stale 사망 정보로 잘못된 REJECT | `rollback_episode()` 내에서 `self.state_tracker = None` 또는 `self.state_tracker.npc_registry.clear()` 추가 |
| 3 | NPC-L3 | `stage4_context_builder.py:374-378` vs `stage4_interview_round.py:281-292` | **MEDIUM** | dead_npcs 이중 소스(cumulative_bible vs npc_registry) 불일치 → 불필요한 재작성 루프 | cumulative_bible.dead_npcs를 npc_registry로 통합하거나, ChiefWriter에 npc_registry 기반 dead_npcs 전달 |
| 4 | NPC-L4 | `state_tracker_npc.py:279-293` | **LOW** | 비무협 장르에서 NPC 무장/수준 regex 비활성 → state_changes 의존도 100% | 의도적 설계. 장르별 regex 패턴 확장 또는 LLM 의존 유지 |
| 5 | NPC-L5 | `stage4_orchestrator.py:390-411` vs `state_tracker.npc_registry` | **MEDIUM** | Bible NPC 이름과 npc_registry NPC 이름 불일치(약칭/별명) → 이중 추적 | NPC 이름 정규화 또는 alias 레지스트리 구축 |
| 6 | NPC-L6 | `blocking_validator_entity_checks.py:18-36` vs `state_tracker_npc.py:393-406` | **LOW** | 회상/언급 판별 패턴 상이 → 같은 텍스트에 다른 판정 가능 | 패턴을 공유 상수로 통합 |
| 7 | NPC-L7 | `project_manager.py:875-922` | **MEDIUM** | `auto_backtrack_v35()`에서 `state_tracker` 미리셋 → 자동 되감기 후 stale NPC 상태 | NPC-L2와 동일 해결책 적용 |
| 8 | NPC-L8 | `main_a.py:3004-3021` | **MEDIUM** | Stage 4 직행 시 StateTracker 재생성 조건이 `is None`만 검사 → 롤백 후에도 기존 tracker 유지 | `state_tracker_loaded_arcs` 비교 또는 Arc 개수 변화 감지 로직 추가 |

---

## 부록: NPC 데이터 흐름 요약도

```
Stage 0 (Bible 생성)
  └─ StoryExpander._generate_npcs()
      └─ Bible.MasterBible.AssetLibrary.KeyNPCs[]
          ├─ name, role, description
          └─ NPC_{Genre}_HUD (장르별 속성)

Stage 2 (Arc 설계)
  ├─ StateTracker.full_extract_from_arcs()
  │   ├─ extract_npc_deaths_from_arc() → npc_registry[name].status = "dead"
  │   ├─ extract_npc_info_from_arc() → npc_registry[name].weapon/level (무협 only)
  │   ├─ extract_relationship_changes_from_arc() → npc_registry[name].relation_to_protag
  │   ├─ extract_npc_injuries_from_arc() → npc_registry[name].injury
  │   ├─ extract_npc_movements_from_arc() → npc_registry[name].location
  │   ├─ extract_npc_personality_from_arc() → npc_registry[name].personality_traits
  │   └─ extract_npc_dialogue_styles_from_arc() → npc_dialogue_profiles[name]
  ├─ UnifiedArcValidator.check_dead_npc_appearance() → REJECT if 사망NPC 행동
  └─ _record_change() → npc_history 테이블 (※ bind_db 미호출로 비활성)

Stage 3 (Blueprint 설계)
  ├─ UnifiedBlueprintValidator.check_dead_npc_in_blueprint() → REJECT
  └─ DirectorEnsemble.check_dead_npc_in_blueprint() → REJECT

Stage 4 (원고 집필)
  ├─ ChiefWriter 프롬프트 주입
  │   ├─ dead_npcs (cumulative_bible 소스)
  │   └─ _build_past_guard_section() → "사망 NPC: ..." 경고
  ├─ BlockingValidator._check_dead_npc_resurrection()
  │   └─ encyclopedia.npcs (npc_registry 소스) → CRITICAL REJECT
  ├─ _detect_npc_overexposure() → advisory WARNING (3-5C)
  └─ Stage4InterviewRound → 재작성 루프

롤백 (D-2)
  ├─ DB: npc_history DELETE WHERE episode_no >= target_ep ✅
  ├─ DB: cumulative_bible_cache 무효화 ✅
  ├─ WorldState: rollback_to() → episode_bibles 리플레이 ✅
  ├─ FactLedger: rollback_to() → episode_bibles 리플레이 ✅
  └─ StateTracker.npc_registry: 미리셋 ❌ (NPC-L2)
```

---

**감사 완료.** 총 8건의 발견 사항 중 HIGH 2건, MEDIUM 3건, LOW 3건.
핵심 이슈는 **NPC-L1 (bind_db 미호출)**과 **NPC-L2 (롤백 시 npc_registry 미리셋)**으로, 두 건 모두 코드 1~2줄 추가로 해결 가능하다.
