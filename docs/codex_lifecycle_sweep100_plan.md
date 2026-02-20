# 데이터 객체 생애주기 100-Round Sweep Plan

## 기존 4가지 스윕과의 차별점

| 관점 | sweep100_manual | debug_sweep100 | crosscut_sweep100 | **본 플랜** |
|------|----------------|----------------|--------------------|-------------|
| 축 | 파일별 | 파일별 | 시나리오별 | **도메인 객체별** |
| 질문 | "이 함수의 계약이 맞나?" | "이 파일에 크래시 패턴이 있나?" | "이 경계 입력이 파이프를 관통하면?" | **"이 객체가 태어나서 죽을 때까지 안전한가?"** |
| 강점 | 모듈 내부 계약 | 패턴 수색 | 모듈 간 seam | **표현 불일치·변환 손실·수명 누수** |

> **핵심 아이디어**: ArcData, Blueprint, Manuscript, NPC, StateTracker, WorldState, FactLedger, Score, Feedback, Config 등 10가지 핵심 도메인 객체의 **전체 생애주기(Creation → Validation → Transformation → Persistence → Retrieval → Consumption → Retirement)**를 각각 10라운드씩 추적한다.

---

## 생애주기 체크리스트 (매 라운드 적용)

```
□ C (Creation)     — 어디서 어떻게 생성되는가? 필수 필드 보장인가?
□ V (Validation)   — 생성 직후 검증이 있는가? 실패 시 원본 유지 vs 거부?
□ T (Transform)    — 변환 과정에서 타입 변경, 키 손실, 구조 왜곡이 있는가?
□ P (Persistence)  — DB/파일 저장 시 직렬화 충실도 (JSON 라운드트립)?
□ R (Retrieval)    — 읽어올 때 역직렬화 안전성, stale 캐시 가능성?
□ U (Usage)        — 소비처에서 실제 접근 패턴과 저장 스키마가 일치하는가?
□ D (Disposal)     — 메모리 해제, 캐시 무효화, 히스토리 제한이 있는가?
```

---

## Phase 1: ArcData 생애주기 (R01–R10)

`ArcData`(Pydantic) — LLM이 생성하는 Arc 설계 데이터.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R01 | **C: Creation** — `analyst.py`에서 LLM JSON → raw dict 생성 | `_extract_json_robust` → `ArcData.model_validate` 경로 vs raw dict 직접 사용 경로 |
| R02 | **V: Validation** — `validate_arc()` graceful degradation | Pydantic 검증 실패 시 원본 dict 유지 → 다운스트림에 `arc_no`/`ep_start` 키 부재 가능성 |
| R03 | **T: Transform** — `_sync_arc_no_alias` + `constraint_compiler` 변환 | `global_arc_no ↔ arc_no` 동기화, `items_acquired`/`grants_received` 런타임 키 주입 |
| R04 | **T: Transform** — `arc_corrector` 교정 후 키 정합 | 교정 결과가 `state_constraints` 내부 구조를 변경할 때 `StateConstraints` 모델과 일관성 |
| R05 | **P: Persistence** — DB 저장 시 `model_dump()` vs raw dict | `db_manager` 저장 경로에서 Pydantic 활성화 여부, `extra="allow"` 키의 보존 |
| R06 | **R: Retrieval** — DB에서 Arc 읽기 → JSON 역직렬화 | `json.loads` 실패 시 row-level guard, 저장된 `tactical_doc`이 `str|dict` 혼재 |
| R07 | **U: Usage** — `stage2_preflight`/`stage3_orchestrator`에서 Arc 소비 | `arc_data.get("ep_count")` int 기대 vs 실제 타입, `beat_sequence` list vs str |
| R08 | **U: Usage** — `stage4_context_builder`에서 Arc 참조 | Blueprint 경로에서 `validate_blueprint_arc()` 적용 범위, `state_constraints` dict 접근 |
| R09 | **D: Disposal** — Arc 롤백/덮어쓰기 시 이전 데이터 정리 | `StateTracker` 스냅샷 복원, `_cumulative_state_cache` 무효화 |
| R10 | **전체 라운드트립** — Arc 생성 → 저장 → 읽기 → 소비 → 갱신 → 재저장 | `model_dump()` ↔ `model_validate()` 왕복 시 키 손실 여부 |

### Phase 2: Blueprint 생애주기 (R11–R20)

`Blueprint`(Pydantic) — 각 에피소드의 장면 설계도.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R11 | **C: Creation** — `three_phase_blueprint_generator` → LLM JSON | Blueprint 생성 3단계 각각의 반환 스키마, `scene_breakdown` dict 구조 |
| R12 | **V: Validation** — `validate_blueprint()` + `unified_blueprint_validator` | Pydantic 검증 vs 비즈니스 검증의 이중 검증, 실패 시 분기 차이 |
| R13 | **T: Transform** — `_sync_ep_num_alias` + `blueprint_ensemble` 합의 변환 | `ep_num ↔ episode_number` 동기화, 앙상블 투표 후 승자 Blueprint 변환 |
| R14 | **T: Transform** — `blueprint_constraint_compiler` 제약 주입 | Blueprint에 Arc 제약 병합 시 키 충돌, `relationship_changes` list 병합 |
| R15 | **P: Persistence** — Blueprint DB 저장 | `stage3_orchestrator:485` commit 후 blueprint dict 구조 보존 |
| R16 | **R: Retrieval** — 이전 에피소드 Blueprint 로드 | `prev_blueprints` 구성, JSON 역직렬화 시 `protagonist_state` dict 무결성 |
| R17 | **U: Usage** — `stage4_context_builder`에서 Blueprint 소비 | `scene_breakdown` dict 접근 패턴, 장면 수 산출, None 체크 |
| R18 | **U: Usage** — `prompt_builder`에서 Blueprint 가이드 생성 | `high_impact_zone` → 장면 수 기반 계산, 0/1 경계 |
| R19 | **D: Disposal** — 이전 Blueprint 갱신/폐기 | 재생성 시 기존 Blueprint 덮어쓰기, `prev_blueprints` 리스트 크기 제한 |
| R20 | **전체 라운드트립** — Blueprint 생성 → 검증 → 저장 → 로드 → 소비 | 키 손실 없이 `model_dump() ↔ json.loads()` 왕복 검증 |

### Phase 3: ManuscriptCandidate 생애주기 (R21–R30)

원고 후보 — ChiefWriter가 생성하고 Director가 심사.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R21 | **C: Creation** — `chief_writer.generate_ensemble()` 3-전략 생성 | 각 전략별 반환 dict 구조 차이, `error=True` 후보 처리 |
| R22 | **V: Validation** — `validate_manuscript_candidate()` + 자기비평 | Pydantic 검증 + `SelfCritiqueResult`, 비평 실패 시 원본 유지 경로 |
| R23 | **T: Transform** — 자기비평 후 `manuscript` 필드 교체 | `chief_writer:482` 비평 파싱 실패 → 원본 필드 복원, `content` dict/list 정규화 |
| R24 | **T: Transform** — Director 앙상블 선택 → 최종 후보 | `director_ensemble` 투표 → `selected_candidate` dict 구조 |
| R25 | **P: Persistence** — 원고 DB 저장 | `stage4_post_processor:38` DB-first commit, HUD 갱신 순서 |
| R26 | **R: Retrieval** — 이전 에피소드 원고 조회 | `get_recent_manuscript_excerpts` 부분 데이터 시 처리, 빈 결과 |
| R27 | **U: Usage** — `block_enricher` 원고 블록 보강 | 블록 단위 분해 → LLM 보강 → 재조립, 블록 누락 처리 |
| R28 | **U: Usage** — `manuscript_enhancer` 후처리 | 정규식 기반 텍스트 처리, 그룹 매칭 실패 경로 |
| R29 | **U: Usage** — `director_auditor` 감사 점수 산출 | 원고 기반 감사, `state_changes` dict vs string 혼재 |
| R30 | **D: Disposal** — REJECT 원고 폐기 + best-manuscript 보관 | 5라운드 전부 REJECT 시 last-best 선택, 이전 후보 메모리 해제 |

### Phase 4: NPC 데이터 생애주기 (R31–R40)

NPC 레지스트리 엔트리 — StateTracker가 관리하는 캐릭터 데이터.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R31 | **C: Creation** — `state_tracker.create_npc_entry()` | `NPCEntry` Pydantic vs bare dict 생성 경로 공존 여부 |
| R32 | **V: Validation** — `validate_npc_entry()` 검증 범위 | `extra="allow"` 동적 필드(무협/헌터/판타지별 차이), `name` 필수 필드 강제 |
| R33 | **T: Transform** — `state_tracker_npc` NPC 갱신 | 관계 변경, 무기 변경, 레벨 업 시 dict 직접 수정 vs Pydantic 재검증 |
| R34 | **T: Transform** — NPC 사망 처리 (`status="dead"`, `death_arc` 설정) | 사망 후 재등장 방지 메커니즘, `last_arc` 갱신 |
| R35 | **P: Persistence** — NPC 레지스트리 DB 저장/로드 | `npc_registry` dict → JSON 직렬화, nested dict 보존 |
| R36 | **R: Retrieval** — `state_tracker.npc_registry` 조회 | 캐시된 레지스트리 vs DB 재로드 타이밍, stale 데이터 가능성 |
| R37 | **U: Usage** — `continuity_inspector`에서 NPC 연속성 검증 | NPC 이름 매칭 (정규식 메타문자), 상태 비교 |
| R38 | **U: Usage** — `chief_writer_context`에서 NPC 프로필 조립 | NPC 데이터 순회, dict 키 접근 패턴, 대형 dict 조립 |
| R39 | **D: Disposal** — `cleanup_npc_registry_with_llm()` 정리 | LLM 기반 정리 후 레지스트리 일관성, 삭제된 NPC 참조 잔존 |
| R40 | **전체 라운드트립** — NPC 생성 → 갱신 → 사망 → 정리 → 재조회 | Arc 걸쳐 NPC 상태 일관성, `death_arc` 이후 필터링 |

### Phase 5: StateTracker 스냅샷 생애주기 (R41–R50)

StateTracker 내부 상태 — 스냅샷, 롤백, 누적 추출.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R41 | **C: Creation** — `StateTracker.__init__` + `full_extract_from_arcs` | 초기 상태 누적 추출 순서, Arc 순회 중 에러 시 부분 상태 |
| R42 | **V: Validation** — 스냅샷 무결성 | deep-copy 스냅샷 `stage2_preflight:597` 가 모든 mutable 필드 포함하는지 |
| R43 | **T: Transform** — 에피소드별 상태 추출 적용 | `state_extractor` 결과 적용, `state_changes` dict→list→string 혼재 |
| R44 | **T: Transform** — `state_delta_tracker` 변화량 계산 | 이전 스냅샷 vs 현재 상태 비교, 타입 불일치 시 delta 오류 |
| R45 | **P: Persistence** — StateTracker JSON 스냅샷 저장 | `snapshot_and_reset_scope()` → JSON string, 재로드 시 구조 복원 |
| R46 | **R: Retrieval** — 캐시된 StateTracker 재사용 | `_state_tracker_loaded_arcs` 기반 증분 로드, 캐시 무효화 조건 |
| R47 | **U: Usage** — 다운스트림 소비자 (validation, prompt_builder, context_builder) | StateTracker 요약 생성 → 프롬프트 삽입 → 검증 피드백 |
| R48 | **D: Disposal** — 롤백 시 스냅샷 복원 | `stage2_finalizer:326` 전체 필드 복원 검증, 누락 필드 |
| R49 | **Arc 전환** — 이전 Arc 상태 → 다음 Arc 초기 상태 계승 | `joint_docs` 기반 전환, `physical_inventory` str/dict 혼재 |
| R50 | **전체 라운드트립** — 초기화 → 추출 → 스냅샷 → 롤백 → 재추출 | 스냅샷-롤백 사이클 반복 시 상태 드리프트 |

### Phase 6: WorldState & FactLedger 생애주기 (R51–R60)

게임 세계 상태와 사실 원장 — 에피소드 간 持속.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R51 | **C: Creation** — WorldState 초기화 | 빈 세계 → 첫 에피소드 데이터 로드, 필수 필드 |
| R52 | **V: Validation** — 상태 업데이트 검증 | `world_state.save()` 비차단 정책(FP-1) vs 데이터 무결성 |
| R53 | **T: Transform** — 에피소드 결과 반영 | 엔티티 추가/수정/삭제, 이력 append 제한 |
| R54 | **P: Persistence** — WorldState JSON 저장 | 저장 포맷과 로드 포맷 일치 여부, entity dict 구조 |
| R55 | **R: Retrieval** — 롤백 리플레이 | 롤백 후 WorldState 재구성, entity 이력 제한 초과 |
| R56 | **C+V: FactLedger** — 사실 원장 생성 및 검증 | 사실 항목 구조, 중복 사실 처리 |
| R57 | **T: FactLedger** — 엔티티 병합 | 동명 엔티티 병합 시 충돌 해결 전략 |
| R58 | **P+R: FactLedger** — 저장 및 읽기 | JSON 라운드트립, 대형 원장 직렬화 성능 |
| R59 | **U: Usage** — `stage4_context_builder`에서 WorldState/FactLedger 요약 | 요약 생성 시 빈 엔티티/사실 처리, 프롬프트 크기 제한 |
| R60 | **D: Disposal** — 이전 에피소드 상태 아카이브/폐기 | 오래된 WorldState 버전 정리, 메모리 관리 |

### Phase 7: Score & Feedback 생애주기 (R61–R70)

점수 데이터와 피드백 메시지 — Validator → Director → 재시도 루프.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R61 | **C: Creation** — `scoring_validator` 점수 생성 | 카테고리별 점수 dict 구조, 가중치 합산 100% 검증 |
| R62 | **V: Validation** — 점수 범위 검증 | 0~100 범위 강제, 음수/초과 점수 처리 |
| R63 | **T: Transform** — `pass_threshold` 동적 조정 | 적응형 난이도 → 점수 기준 변경 → 판정 영향 |
| R64 | **T: Transform** — 다중 Validator 결과 합산 | `validation_orchestrator` 합산 로직, 가중치 충돌 |
| R65 | **P: Persistence** — 점수 이력 저장 | reject/pass 이력 DB 기록, `stage_rejection_history` |
| R66 | **R: Retrieval** — 이전 점수 이력 조회 | 적응형 임계값 계산 시 이전 점수 참조, stale 데이터 |
| R67 | **C: Feedback 생성** — REJECT 시 피드백 메시지 조립 | `stage2_finalizer:466` 피드백 구성, 다중 소스 병합 |
| R68 | **T: Feedback 변환** — 피드백 → 재시도 프롬프트 | `stage2_preflight:297` 압축, `{}` 중괄호 이스케이프 |
| R69 | **U: Feedback 소비** — 피드백 → LLM 프롬프트 삽입 | 패치 모드 vs 전체 재생성, 피드백 필드 보존 |
| R70 | **D: Feedback 폐기** — 성공 후 이전 피드백 정리 | 피드백 이력 크기 제한, 메모리 해제 |

### Phase 8: DI Context & Config 생애주기 (R71–R80)

DI 컨텍스트 객체와 설정 — 스테이지 전환 시 수명.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R71 | **C: Context 생성** — `Stage2Context.from_app(app)` 스냅샷 | `__slots__` 정합, 선택적(optional) 슬롯 바인딩 |
| R72 | **C: Context 생성** — `Stage3Context.from_app(app)` | Stage2 → Stage3 전환 시 공유 상태 vs 독립 상태 |
| R73 | **C: Context 생성** — `Stage4Context.from_app(app)` | Stage3 → Stage4 전환 시 slot 바인딩 누락 |
| R74 | **V: 바인딩 검증** — 선택적 슬롯의 None Guard | `getattr(ctx, "...", None)` 패턴 vs 직접 접근 불일치 |
| R75 | **T: 콜백 동기화** — ctx 변경 → app 동기화 콜백 | `sync_cache_key_to_app` key vs value 동기화 차이 |
| R76 | **P: Config 로드** — `ConfigManager` YAML 로드 | `validation.yaml` 키 로드 → `_threshold()` 연결, 미존재 키 fallback |
| R77 | **R: Config 참조** — 하드코딩 vs `_threshold()` 혼재 | 동일 임계값의 이중 출처 문제 |
| R78 | **U: Context 소비** — Orchestrator에서 ctx 속성 접근 | 선택적 속성 접근 시 AttributeError 가능성 |
| R79 | **D: Context 폐기** — Stage 전환 시 이전 Context 해제 | 이전 Context 참조 잔존, GC 문제 |
| R80 | **전체 라운드트립** — app init → Context 생성 → 사용 → 전환 → 폐기 | Stage 0→2→3→4 Context 수명 일관성 |

### Phase 9: Cache & Registry 생애주기 (R81–R90)

캐시, 레지스트리, 트래커 — 메모리 상 장기 객체.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R81 | **C: 캐시 생성** — `_cumulative_state_cache` 초기화 | 초기 None → 첫 계산 → 캐시 키 설정 |
| R82 | **V: 캐시 유효성** — 키 기반 hit/miss 판정 | 키 업데이트 vs 값 업데이트 불일치 |
| R83 | **T: 캐시 갱신** — Arc 추가 후 캐시 재계산 | 증분 갱신 vs 전체 재계산 정합성 |
| R84 | **D: 캐시 무효화** — 롤백/리셋 시 캐시 정리 | 무효화 누락 → stale 캐시 전파 |
| R85 | **C: Entity Registry** — `semantic_item_registry` 초기화 | 아이템 레지스트리 구축, dict 키 정규화 |
| R86 | **T: Entity Registry 갱신** — 아이템 추가/소모 | `items_acquired` 타입 혼재 (str vs dict `{"name":"검", "quantity":1}`) |
| R87 | **U: Entity Registry 소비** — set 연산 시 unhashable dict 원소 | `set.update()` → `TypeError` 가능성 |
| R88 | **C+D: `_context_caches`** — `base_agent` 캐시 생명 | 생성 시점 / 크기 제한 / 정리 시점 |
| R89 | **C+D: `_failures` 리스트** — `adaptive_retry` 누적 | 무한 성장 → 메모리 누수, pruning 부재 |
| R90 | **C+D: `_cumulative_bible_cache`** — `db_manager` 캐시 | maxsize 제한 부재 → 메모리 누수 |

### Phase 10: Prompt & Response 생애주기 (R91–R100)

프롬프트 객체와 LLM 응답 — 조립에서 파싱까지.

| Round | 생애주기 단계 | 추적 대상 |
|-------|-------------|-----------|
| R91 | **C: 프롬프트 조립** — `prompt_builder` 다단계 합성 | 필수 컨텍스트 + 선택 섹션 조립, 크기 제한 절삭 |
| R92 | **V: 프롬프트 검증** — 길이 제한, 필수 필드 존재 | `stage4_orchestrator:478` mandatory context 절삭 후 고우선순위 보존 |
| R93 | **T: 템플릿 치환** — `.replace()` / `.format()` / f-string | 사용자 텍스트 내 `{}` 충돌, placeholder 오염 |
| R94 | **P: 프롬프트 캐싱** — 동일 프롬프트 재사용 | 캐시 키 계산, 컨텍스트 변경 시 캐시 miss 보장 |
| R95 | **C: LLM 응답 수신** — raw string 수신 | 빈 응답, 타임아웃, 부분 JSON |
| R96 | **V: 응답 파싱** — `_extract_json_robust` | list vs dict, nested JSON, markdown 코드블록 래핑 |
| R97 | **T: 응답 정규화** — dict 기대 위치에 list/string 유입 | `chief_writer:460` `list`/`dict`/other 정규화 경로 |
| R98 | **U: 응답 소비** — 다운스트림 `.get()` 접근 | 키 부재 시 기본값 타입 불일치, `None`에 메서드 호출 |
| R99 | **D: 응답 폐기** — REJECT 후 응답 데이터 처리 | 재시도 루프에서 이전 응답 참조 잔존, 메모리 해제 |
| R100 | **전체 라운드트립** — 프롬프트 조립 → LLM 호출 → 파싱 → 검증 → 소비 → 폐기 | 한 사이클 전체 추적 종합 |

---

## 실행 규칙

### 라운드별 출력 형식

```markdown
## Round N — [객체명]: [생애주기 단계] — [한줄 요약]

### 객체 정의
- **객체**: [Pydantic 모델명 또는 런타임 dict 구조]
- **생애주기 단계**: C / V / T / P / R / U / D
- **추적 범위**: `파일A` → `파일B` → `파일C`

### 생애주기 추적
**[단계: 파일A:L100]**
- 코드: `실제 코드 copy-paste`
- 객체 상태: [이 시점에서 객체의 구조/타입/키]
- 변환/위험: [구체적 설명]

**[단계: 파일B:L200]**
- 코드: `실제 코드 copy-paste`
- 객체 상태: [변환 후 구조]
- 불일치: [이전 단계 대비 변화/손실]

### 발견
- **BUG / RISK / SAFE**: [판정]
- **생애주기 위반 유형**: [표현 불일치 / 변환 손실 / stale 참조 / 메모리 누수 / 키 손실]
- **기존 스윕 교차**: [기존 sweep에서 커버 여부]

---
## Round N 완료
```

### 핵심 규칙
1. **매 라운드 생애주기 체크리스트 (C-V-T-P-R-U-D) 중 최소 2단계 추적**
2. **Pydantic 모델과 런타임 dict 양쪽 경로 모두 확인** — 검증 우회 가능성
3. **`extra="allow"` 키의 보존/손실 추적** — `model_dump()` 왕복 확인
4. **FP-1~10 교차 확인** (기존 debug_sweep100 규칙 준수)
5. **코드 수정 금지**

### 체크포인트 (매 10라운드)
```markdown
## Checkpoint — Round XX

| Metric | Value |
|--------|-------|
| 표현 불일치 (Type Mismatch) | N |
| 변환 손실 (Transform Loss) | N |
| Stale 참조 (Stale Reference) | N |
| 메모리 누수 (Memory Leak) | N |
| 키 손실 (Key Loss) | N |
| 기존 스윕 중복 | N |
| 신규 발견 | N |
```

---

## 결과 파일
- 플랜: `docs/codex_lifecycle_sweep100_plan.md`
- 결과: `docs/codex_findings_lifecycle_sweep100.md`

---

## 무중단 수동검사 강제 가드 (필수)

본 섹션은 본 플랜 수행 시 최우선 강제 규칙이다. 자동 스캔 흔적이 있으면 라운드를 무효 처리한다.

### 1) 수동 검사 강제 / 검색 금지
- 금지 도구: `rg`, `grep`, `freg`, `greg`, `Select-String`, `findstr`, `git grep`, IDE 전역 검색, 기타 패턴 검색 자동화 전부.
- 허용 방식: 대상 파일을 직접 열람하는 단순 읽기만 허용 (`Get-Content`, 에디터 수동 열람).
- 근거 규칙: 모든 판정은 최소 1개 이상의 `file:line` 근거를 포함해야 하며, 근거는 수동 열람 내용이어야 한다.
- 위반 처리: 검색 기반 근거가 1회라도 확인되면 해당 라운드는 무효이며 동일 라운드를 처음부터 재수행한다.

### 2) 무중단 수행 규칙
- 기본 원칙: Round 1~100을 사용자 재질문 없이 연속 수행한다.
- 중간 정산/요약은 허용하되, 수행 중단 사유로 사용하지 않는다.
- 중단 허용(하드 블로커) 조건:
  - 대상 파일 실존 불가
  - 파일 권한/잠금으로 열람 불가
  - 문서/코드 파손으로 라인 판독 불가
- 하드 블로커 발생 시 1회만 아래 포맷으로 보고한다:
  - `Blocker`: [원인]
  - `Last Completed Round`: [N]
  - `Resume Condition`: [필요 조치]

### 3) 컨텍스트 컴팩트 내성 규칙
- 컨텍스트 컴팩트 발생 시 즉시 플랜 문서와 결과 문서의 마지막 완료 라운드를 기준으로 상태를 복구한다.
- 복구 직후 사용자 문의 없이 `Last Completed Round + 1`부터 재개한다.
- 라운드마다 다음 최소 메타를 남긴다:
  - `Last Completed Round`
  - `Last Read Files`
  - `Next Round`

### 4) 라운드 출력 스키마 (고정)
- 각 라운드는 아래 섹션을 반드시 모두 포함한다:
  - `Read Files`
  - `Manual Inspection Evidence`
  - `Confirmed Bugs`
  - `Risks`
  - `False Positives Excluded`
  - `Test Gaps`
- `Manual Inspection Evidence`는 최소 2개 bullet로 작성하고, 각 bullet에 `file:line`을 포함한다.
- `Confirmed Bugs`가 `none`이 아닌 경우:
  - `[P0]`~`[P3]` severity 태그 필수
  - `file:line` 필수
  - 기존 의도/철학과 충돌 여부(`intent check`) 필수
- 각 라운드에 `Intent Alignment Check`를 추가한다:
  - `Candidate Intent`
  - `Intent Evidence (file:line)`
  - `Conflict Evidence (file:line or none)`
  - `Decision (Aligned / Conflict / Unclear)`

### 5) 오탐 방지 / 설계 의도 보존 게이트
- `BUG` 확정 전 아래 항목을 모두 기록한다:
  - `Intent Source`: 주석/함수명/정책명/상수/가드 로직 근거 (`file:line`)
  - `Caller Contract`: 상위 호출자 기대 동작 근거 (`file:line`)
  - `Fallback Policy`: 비차단/Advisory/Fallback 경로 존재 여부 (`file:line`)
  - `Reachability`: 실제 도달 가능한 호출 경로 (`file:line`)
  - `Blast Radius`: 장애 전파 범위와 발현 조건
- 판정 규칙:
  - 의도 근거와 충돌 근거가 동시에 존재하면 `Confirmed Bugs` 금지, `Risks`로 분류
  - 정책 의도와 합치하고 가드가 존재하면 `False Positives Excluded`로 분류
  - 의도와 명확히 충돌 + 도달 가능 + 보호 부재일 때만 `Confirmed Bugs`로 확정
- 금지 규칙:
  - 단일 라인/단일 파일 근거만으로 버그 확정 금지 (최소 2파일 근거 필수)
  - 일반 베스트 프랙티스 위반만으로 버그 확정 금지
- 기록 의무:
  - 모든 BUG/RISK 항목에 `intent check: pass/fail/unclear` 표기
  - `unclear`는 BUG 금지, RISK로 유지 후 후속 검증 항목에 추가

### 6) 판정 주권 규칙 (Director Sovereignty / 내각제)
- Python/정적 규칙/검증 스크립트는 `WARNING` 또는 `ADVISORY`까지만 가능하며, 단독 `REJECT`/`BLOCK` 판정은 금지한다.
- 자동 검사의 역할은 이상 징후 플래그와 근거 수집 보조에 한정한다.
- 최종 판정 주권:
  - `REJECT`/`PASS` 최종 결정은 Director LLM(단일 또는 ensemble)만 수행한다.
- 충돌 처리:
  - Python 경고 vs Director 승인: `False Positives Excluded`로 기록
  - Python 경고 vs Director 반려: Director 근거와 함께 `Confirmed Bugs` 또는 `Risks`로 기록
- Director 판정 불가(응답 없음/보류) 시:
  - `Pending Director Decision`으로 기록하고 `REJECT` 확정 금지

### 7) 체크포인트/품질 게이트
- 매 10라운드마다 체크포인트를 작성한다.
- 체크포인트 최소 항목:
  - Cumulative Confirmed Bugs (P0~P3 분해)
  - Cumulative Risks
  - Cumulative False Positives Excluded
  - Cumulative Test Gaps
  - Phase False-Positive Ratio
  - Consecutive Empty Rounds
  - Manual Evidence Compliance Rate

### 8) 최종 유효성 판정 (완료 조건)
- 아래 검증을 모두 통과해야 완료로 인정한다.
- `python scripts/validate_manual_sweep.py docs/codex_findings_lifecycle_sweep100.md --from-round 1 --to-round 100`
- `python scripts/validate_manual_sweep.py docs/codex_findings_lifecycle_sweep100.md --from-round 1 --to-round 100 --max-fp-ratio 0.35 --max-fp-streak 2`
- 위 Python 검증은 문서 형식/근거 충족 여부 확인용이며, 최종 내용 판정(REJECT/PASS) 권한이 아니다.
- 검증 실패 시 실패 라운드를 수정하고 재검증한다.
