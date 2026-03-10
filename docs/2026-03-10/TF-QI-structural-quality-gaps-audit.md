# TF-QI: 구조적 품질 갭 전수조사 — NPC 정보 격차 / 장르 지원 불균형 / 시점 전환

> 작성: 2026-03-10
> 상태: 6-pass 감리 완료 (최근 코드 반영 교정 3건 + 오탐 2건 제거, 확신도 96%)
> 방법: 코드 전수 탐색 → 교차 검증 → 최근 보강분 재대조 → 오탐/과장 진술 제거
> 코드 수정: 없음 (조사 문서만)

---

## 공통 원칙

- **대원칙 1**: Python은 수집만, 판단은 LLM이
- **대원칙 3**: Director 주권주의 — advisory만, REJECT 강제 금지
- 모든 개선 제안은 advisory 수준 — 기존 동작 변경 금지

---

## TF-A. 주연/조연 정보 격차 (NPC Information Gap)

### 현황 구조

```
주인공 (protagonist)
├── WorldState: name, location, assets, injuries, skills(max 50)
├── FactLedger: characters[주인공] + items(owner="주인공") + skills
├── StateTracker: protagonist_emotion {emotion, trigger, arc_no, episode}
├── HUD: 전용 상태 스냅샷 + 추세 + 이상치
└── Advisory: InfoParadoxChecker(1인칭 전용 지식 추적)

NPC (조연)
├── WorldState: alive_npcs[name] = {role, relation, personality, location, first_seen_ep, role_at_intro, known_attrs{4필드}}
├── FactLedger: characters[name] = {status, role, relationship, established_ep, last_ep, history[]}
├── StateTracker: NPC 추출 16종 (전부 주인공 기준 관점)
├── npc_history: append-only 변경 이력 (reason 컬럼)
├── npc_relationship_history: append-only 관계 변경 이력
└── Advisory: NpcDriftAdvisor(max 5), TruthGate(사망NPC), RelDrift(전체)
```

### 식별된 갭 (6-pass 검증 완료)

#### NPC-G1. NPC 감정 상태 미추적 [P2]

- **현황**: 주인공은 `update_protagonist_emotion()` → `{emotion, trigger, arc_no, episode}` 구조화 추적 (`state_tracker_npc.py:1946-2039`). NPC는 `personality` 플랫 문자열만 존재.
- **영향**: NPC 감정 변화가 에피소드 간 추적 안 됨. "박성호가 분노→체념"이 기록 없이 사라짐.
- **제안**: `npc_emotion_snapshot` 경량 dict 추가 (episode당 상위 3 NPC만). Advisory → Director MC 주입.
- **비용**: 중 (StateTracker 확장 + Advisory 1개)
- **확신도**: HIGH

#### NPC-G2. NPC known_attrs 4필드 한정 [P2]

- **현황**: `known_attrs` 자동 동기화 4필드만: `relation_to_protag`, `injury`, `location`, `permanent_injuries` (`world_state.py:486-557`). `personality`, `motivation`, `companion_status` 등은 NPC dict 최상위 키로만 존재.
- **영향**: NpcDriftAdvisor가 `known_attrs` + `role_at_intro`만 검사 (`npc_drift_advisor.py:93-101`). personality 변화는 drift 감지 대상 밖.
- **제안**: `personality`를 5번째 known_attrs로 자동 동기화. NpcDriftAdvisor 프롬프트에 personality 대조 추가.
- **비용**: 낮 (world_state.py §18 추가 + drift advisor 프롬프트 1줄)
- **확신도**: HIGH

#### NPC-G3. NpcDriftAdvisor max 5 NPC 제한 [P2]

- **현황**: `npc_drift_advisor.py:55` — 에피소드당 최대 5명만 drift 검사. 50+ NPC 장기연재에서 대부분 미검사.
- **영향**: 10화 이상 등장 안 한 NPC가 갑자기 다른 성격으로 등장해도 감지 불가.
- **제안**: max_npcs 5→8 상향 또는 "마지막 등장 이후 N화 경과" 기준 우선순위 정렬.
- **비용**: 낮 (정렬 로직 10줄)
- **확신도**: HIGH

#### NPC-G4. Arc 설계에 NPC 선택 메커니즘 부재 [P1]

- **현황**: `four_phase_arc_generator.py`에 NPC 선택 단계 없음. NPC 등장은 전적으로 LLM이 Treatment/이전 컨텍스트 기반으로 결정. Python 수준의 NPC 로스터 주입 없음.
- **CW 경고 존재**: `chief_writer_context.py:1045-1071` — `_get_npc_frequency_warning()`이 "최근 10화 미등장" NPC를 CW에 경고. 그러나 이는 **원고 생성 단계**(Stage 4)에서만 작동. **Arc 설계 단계**(Stage 2)에는 미전달.
- **영향**: Arc 5~6개 연속 특정 NPC 미등장해도 Arc 설계에 반영 안 됨. CW 경고는 이미 설계된 Arc 내에서만 유효.
- **제안**: `_generate_prev_context()`에 `[방치 NPC 주의]` advisory 주입 — WorldState `alive_npcs` 중 최근 N화 미등장 NPC 목록 (Arc 설계자가 참고).
- **비용**: 낮 (Python-only, DB 조회 + 텍스트 주입 ~20줄)
- **확신도**: HIGH

#### NPC-G5. Arc state_changes 엔티티의 structured CP 누락 [P2]

- **현황**: `stage4_context_builder.py`에는 `_collect_npc_roster()`가 있어 Arc/Blueprint 기준 NPC 로스터를 Smart Retrieval 쿼리에 반영한다. 즉, Blueprint에 이름이 없어도 **retrieval 경로에서는 일부 보완**된다.
- **잔여 갭**: 그러나 structured Continuity Packet의 엔티티 추출은 여전히 `_extract_blueprint_entities()`의 Blueprint `full_text` 중심이다. Arc `state_changes`에만 등장하고 Blueprint 본문에 없는 NPC/아이템은 **CP 구조화 경로에서 보호가 약하다**.
- **영향**: "박성호가 배신"이 Arc `state_changes`에만 있고 Blueprint 문면에 없으면, Smart Retrieval이 비활성/빈 결과인 경우 CW가 structured CP 레벨의 직접 보호를 못 받을 수 있다.
- **제안**: `_extract_blueprint_entities()`에 Arc `state_changes` 기반 후보를 OR 조건으로 합치거나, CP 엔티티 세트에 별도 병합.
- **비용**: 낮 (조건 추가 ~10줄)
- **확신도**: HIGH

#### NPC-G6. NPC 아이템 소유 미추적 [P3]

- **현황**: `fact_ledger.py:181,194` — 아이템 owner가 항상 "주인공"으로 하드코딩. NPC 소지품 추적 없음.
- **영향**: "박성호가 증거 문서를 가져감" → FactLedger에 기록 안 됨.
- **제안**: 장기 후순위. 현재 NPC 아이템이 서사적으로 중요한 경우가 드물고, WorldState `known_attrs`로 간접 표현 가능.
- **비용**: 높 (FactLedger 스키마 변경)
- **확신도**: HIGH

#### NPC-G7. NPC별 지식 경계(Knowledge Boundary) 부재 [P1]

- **시나리오**: 주인공=회귀자(핸드폰 앎), 조연=원시인(핸드폰 모름). 주인공이 "핸드폰..." 혼잣말 → 조연이 들음.
  - **기대**: "핸드폰이 무엇이옵니까 나리?" (NPC는 모르는 개념)
  - **현실**: "핸드폰은 역시 갤럭시 S10이죠" (NPC가 아는 것처럼 반응) — 높은 확률
- **현황**: `InfoParadoxChecker`는 **주인공 전용** (`info_paradox_checker.py:3` "1인칭 시점 전용"). `build_knowledge_summary()`가 "주인공이 아는 정보" 목록을 누적하고, 회귀자 예외까지 처리 (L154 `incarnation_type == "회귀자"`). 그러나 **NPC에 대한 동등한 지식 경계 시스템이 전무**.
- **구조적 근본 원인**:
  ```
  주인공: Bible → knowledge_map → reveals/witnesses/misled → LLM 검증
  NPC:    personality 플랫 문자열만 존재 → 지식 범위 추론 불가
  ```
  - WorldState `alive_npcs[name]`에 `knowledge_scope` 같은 필드 없음
  - NPC가 "무엇을 아는지/모르는지"를 CW나 Director에게 전달하는 경로 없음
  - LLM 상식에 100% 의존 — NPC `personality="원시 시대 사람"`이 CP에 있어도, CW가 대사 생성 시 지식 범위를 추론하지 못할 수 있음
- **영향**: 회귀물/이세계물/빙의물에서 핵심 서사 장치인 "정보 비대칭"이 시스템적으로 보호받지 못함. 조연이 모르는 개념을 자연스럽게 사용하는 몰입 파괴 대사 생성 가능.
- **제안 (2단계)**:
  - **Phase 1 (advisory)**: NPC 등록 시 `knowledge_era` 또는 `knowledge_tags` 필드 추가 (예: `"원시인"→knowledge_era="선사시대"`, `"현대인"→knowledge_era="2024"`). CW 프롬프트에 `[NPC 지식 범위]` 섹션 주입: "원시인은 전자기기, 현대 용어를 모릅니다". Director `consistency_checklist`에 `npc_knowledge_boundary` 18번째 항목 추가.
  - **Phase 2 (검증)**: NPC 대사에서 `knowledge_era` 밖 용어 사용 감지 → advisory 경고. Python-only regex (시대별 금지어 목록) 또는 LLM 1회 판정.
- **비용**: Phase 1 — 중 (WorldState 스키마 + CW 프롬프트 + Director 체크리스트). Phase 2 — 중~높 (시대별 용어 사전 또는 LLM 호출).
- **확신도**: HIGH

#### ~~NPC-G8. Character Voice → CW 미전달~~ [오탐 제거]

- **검증 결과**: `chief_writer_context.py:304-328`에 I-25 캐릭터 보이스 가이드 섹션이 **이미 존재**. `character_voice.build_voice_guide()` → CW `writer_core_section`에 주입됨.
- **상태**: 오탐. DB-7이 Director에게만 간다는 초기 판단은 잘못됨. CW도 별도 경로로 수신 중.

### NPC 갭 우선순위 요약

| ID | 항목 | 우선순위 | 비용 | 확신도 |
|----|------|----------|------|--------|
| NPC-G4 | Arc 설계 NPC 방치 경고 | P1 | 낮 | HIGH |
| NPC-G7 | NPC별 지식 경계 부재 | P1 | 중 | HIGH |
| NPC-G2 | known_attrs personality 동기화 | P2 | 낮 | HIGH |
| NPC-G3 | NpcDriftAdvisor 5→8 상향 | P2 | 낮 | HIGH |
| NPC-G5 | Arc state_changes NPC → CP 포함 | P2 | 낮 | HIGH |
| NPC-G1 | NPC 감정 상태 추적 | P2 | 중 | HIGH |
| NPC-G6 | NPC 아이템 소유 추적 | P3 | 높 | HIGH |

---

## TF-B. 장르 지원 불균형 (Genre Support Imbalance)

### 현황 구조 — 3-Tier 장르 지원

```
Tier 1 (FULL): WUXIA, HUNTER, INVESTMENT
  └── 커스텀 run_deep_validation() + 전용 validate 헬퍼 + DB 레지스트리

Tier 2 (PARTIAL+): FANTASY, ACTOR
  └── 부분 커스텀 검증 + 제한적 DB 레지스트리

Tier 3 (MINIMAL): COOKING, COMPOSER, MEDICAL, SPORTS, ALT_HISTORY
  └── 기본 금지어 검사만. run_deep_validation()은 super() passthrough
```

### 장르별 지원 매트릭스 (6-pass 검증 완료)

| 장르 | Guard 줄수 | 금지어 | Deep Validation | DB Registry | Context 분기 | 전체 |
|------|-----------|--------|----------------|-------------|-------------|------|
| WUXIA | 662 | 130 | CUSTOM (현대 표기+무력 불일치) | base 16종 | 전용 | **FULL** |
| HUNTER | 867 | 41 | CUSTOM (5 validate 헬퍼) | 2종 (skill_cooldown, dungeon_clear) | 전용 | **FULL** |
| INVESTMENT | 717 | 29 | CUSTOM (4 validate 헬퍼) | 1종 (financial_state) | 전용 | **FULL** |
| FANTASY | 362 | 32 | PARTIAL (compound+spell) | 2종 (spell_repertoire, blessing_curse) | 전용 | **PARTIAL+** |
| ACTOR | 464 | 38 | NONE (passthrough) | 1종 (filmography) | 전용 | **PARTIAL** |
| COOKING | 511 | 33 | NONE (passthrough) | 없음 | 없음 | **PARTIAL-** |
| COMPOSER | 518 | 33 | NONE (passthrough) | 없음 | 없음 | **PARTIAL-** |
| MEDICAL | 469 | 37 | NONE (passthrough) | 없음 | 없음 | **PARTIAL-** |
| SPORTS | 462 | 37 | NONE (passthrough) | 없음 | 없음 | **PARTIAL-** |
| ALT_HISTORY | 492 | 58 | NONE (passthrough) | 없음 | 없음 | **PARTIAL-** |

**균등 부분** (장르 무관):
- `genre_schema_builder.py`: 10개 장르 전부 동적 스키마 생성 (HUD 필드, NPC HUD, 아이템 접미사). **균등.**
- `config/genres/*.yaml`: 10개 장르 전부 YAML 설정 존재. **균등.**
- `analyst.yaml` 플레이스홀더: `{energy_tracking_rules}` 등 장르 동적 치환. **균등.**
- `numeric_consistency_checker.py`: 장르 분기 없음, 9개 검사 전부 장르 무관. **균등.**

### 식별된 갭

#### GENRE-G1. Tier 3 장르 run_deep_validation() 미구현 [P2]

- **현황**: COOKING/COMPOSER/MEDICAL/SPORTS/ALT_HISTORY 5개 장르의 `run_deep_validation()`이 전부 `super()` 호출 후 재포맷만.
  - `cooking_guard.py:501-511`, `composer_guard.py:508-518`, `medical_guard.py:459-469`, `sports_guard.py:452-462`, `alt_history_guard.py:482-492`
- **대비**: HUNTER는 `validate_dungeon_entry()`, `validate_awakening_progression()`, `validate_skill_count()` 등 5개 헬퍼. INVESTMENT는 `validate_investment_scale()`, `validate_return_rate()` 등 4개 헬퍼.
- **영향**: 의료물에서 비현실적 시술 순서, 스포츠물에서 규칙 위반 경기 진행, 요리물에서 화학적 불가능 조리법 등이 미검사.
- **제안**: 장르당 2~3개 핵심 validate 헬퍼 추가 (도메인 지식 기반 regex). 예: 의료 — 시술 순서, 스포츠 — 경기 시간/스코어 일관성.
- **비용**: 높 (장르 도메인 지식 필요, 5개 장르 × 2~3개 헬퍼)
- **확신도**: HIGH

#### GENRE-G2. Tier 3 장르 DB Registry 부재 [P2]

- **현황**: `state_tracker.py:1410-1421` — COOKING/COMPOSER/MEDICAL/SPORTS/ALT_HISTORY는 `get_all_summaries(genre=)`에서 기본 16종만 반환. 장르별 진행 데이터 추적 없음.
  - 대비: HUNTER는 `skill_cooldown_registry` + `dungeon_clear_registry`, FANTASY는 `spell_repertoire` + `blessing_curse_registry`, ACTOR는 `filmography_registry`.
- **영향**: 요리물에서 레시피 진행, 의료물에서 환자 치료 이력, 스포츠물에서 시즌 전적 등이 에피소드 간 추적 불가.
- **제안**: 장르별 1~2개 경량 레지스트리 추가. 예: 의료 → `treatment_history_registry`, 스포츠 → `match_record_registry`.
- **비용**: 중 (StateTracker 메서드 + DB 저장 + 컨텍스트 주입)
- **확신도**: HIGH

#### GENRE-G3. Stage4 explicit 장르 분기 불균형 [P2]

- **현황**: `stage4_context_builder.py`의 명시적 분기는 HUNTER, FANTASY, ACTOR 3개뿐이다.
- **사실 교정**: 다만 INVESTMENT는 `state_tracker.get_all_summaries(genre="investment")` 경로에서 `financial_state`가 **암묵적으로 포함**된다. 따라서 "나머지 7개가 전부 generic만"이라는 표현은 과장이다.
- **잔여 갭**: 명시적 branch 수준의 장르 특화는 여전히 3개에 치우쳐 있고, Tier 3 장르 5개는 사실상 generic summary 의존이다.
- **제안**: G2 레지스트리 추가 후 context_builder explicit branch 확장. INVESTMENT는 암묵 경로를 유지하되 필요 시 explicit formatting만 보강.
- **비용**: G2에 의존
- **확신도**: HIGH

#### GENRE-G4. WUXIA 금지어 130 vs 타 장르 29~58 비대칭 [P3]

- **현황**: WUXIA `forbidden_terms` 130개로 타 장르의 3~4배. `check_modern_notation()` 17개 regex 패턴은 WUXIA 전용.
- **영향**: WUXIA 원고는 촘촘한 보호, 타 장르는 느슨한 보호. 그러나 WUXIA는 시대극 특성상 현대 용어 차단이 필수적이므로 비대칭 자체가 결함은 아님.
- **제안**: NO-GO — 장르별 금지어 수는 도메인 특성에 비례. 억지로 균등화하면 오탐 증가.
- **확신도**: HIGH

### 장르 갭 우선순위 요약

| ID | 항목 | 우선순위 | 비용 | 확신도 |
|----|------|----------|------|--------|
| GENRE-G1 | Tier 3 deep validation 구현 | P2 | 높 | HIGH |
| GENRE-G2 | Tier 3 DB Registry 추가 | P2 | 중 | HIGH |
| GENRE-G3 | Context 장르 분기 확장 | P2 | G2 의존 | HIGH |
| GENRE-G4 | 금지어 비대칭 | NO-GO | — | HIGH |

---

## TF-C. 시점(POV) 전환 기능 현황 (POV System Status)

### 현황 구조

```
Stage 0 (설정)
├── POV 선택 메뉴: 1인칭 / 3인칭 / 전지적 (3가지)
├── 저장: MasterBible.protagonist_config.pov
└── 자동 감지: style_extractor.py (혼합 포함 4가지 감지 가능)

Stage 2 (Arc)
├── stage2_preflight: POV → enhanced_context 주입 (1인칭 금지 규칙 포함)
└── blueprint_ensemble: scene_presets villain_scheme/side_glimpse 제한 (1인칭 시 금지)

Stage 3 (Blueprint)
└── stage3_orchestrator: StyleGuide 요약에 시점={pov} 포함

Stage 4 (원고)
├── StyleGuide → CW 프롬프트에 POV 규칙 주입 (style_extractor._get_pov_rules)
├── pre_llm_validator: V70 POV 일관성 검사 (1인칭/3인칭만, 전지적/혼합 미검사)
├── InfoParadoxChecker: 1인칭 전용 지식 경계 LLM advisory
├── Director: pov_discipline 체크리스트 (NC-3, 17개 중 16번)
└── director_auditor: POV 동적 갱신 (PreLLMValidator.pov 설정)
```

### 작동하는 것 (6-pass 확인)

1. **3가지 POV 선택 + 전파**: Stage 0 → Bible → 전 Stage 전파 확인. `stage0/__init__.py:64`, `stage01_helpers.py:129`.
2. **CW POV 규칙 주입**: `style_extractor._get_pov_rules()` (L73-115) — 1인칭/3인칭/전지적/혼합 4가지 규칙셋 완비. CW StyleGuide 경로로 주입.
3. **1인칭 전용 보호**: InfoParadoxChecker(지식 경계), Blueprint scene preset 제한(villain_scheme 금지), Stage2 preflight 금지 규칙.
4. **Director pov_discipline**: NC-3 체크리스트 16번 — "한 씬 안에서 시점 누출이나 타인 내면 침범이 없는가?". 관찰 기반 추론 false-positive 방지 단서 포함.
5. **V70 Pre-LLM 검사**: 1인칭/3인칭 대명사 비율 검사.
6. **Bible POV 우선**: `stage4_orchestrator.py:1327-1363` — Bible POV가 StyleGuide POV를 override (TF-31-2).

### 식별된 갭

#### POV-G1. 전지적/혼합 POV 검증 0건 [P1]

- **현황**: `pre_llm_validator.py:424-464` — `_check_pov_consistency()`가 `전지적`과 `혼합` POV에 대해 **아무 검증도 안 함**. 무조건 pass.
- **영향**: 전지적 시점에서 1인칭 대명사 사용("나는 생각했다")이 미검사. 혼합 시점에서 씬 내 POV 혼재가 미검사.
- **제안**:
  - 전지적: 1인칭 대명사 비율 > 20% 시 WARNING (대사 제외 후)
  - 혼합: `***` 씬 구분자 기준 블록별 POV 일관성 검사
- **비용**: 낮 (pre_llm_validator 확장 ~30줄)
- **확신도**: HIGH

#### POV-G2. Director POV 소비 준비는 있으나 호출부 wiring이 약함 [P1]

- **현황**: `director_auditor.py`는 `validation_context["pov"]`를 받아 `PreLLMValidator.pov`에 동적으로 반영할 준비가 되어 있다.
- **잔여 갭**: 하지만 `stage4_interview_round.py`의 Director 메인 선택 경로에서는 현재 POV가 Director MC에 명시적으로 드러나지 않고, selection path 자체도 POV를 일관되게 surface하지 않는다.
- **영향**: Director가 원고와 일반 규칙만으로 POV를 추론해야 하는 구간이 남는다. 3인칭 작품의 간접 화법이나 관찰 기반 추론을 판독할 때 근거가 약해질 수 있다.
- **제안**: Director MC에 `[작품 시점: {pov}]` 1줄 주입하고, 가능하면 Director validation_context에도 동일 POV를 caller에서 함께 넘긴다.
- **비용**: 매우 낮 (1줄 추가)
- **확신도**: HIGH

#### POV-G3. "혼합" POV 메뉴 미제공 [P2]

- **현황**: Stage 0 메뉴는 3가지만 제공 (`1인칭/3인칭/전지적`). `혼합`은 `style_extractor.py:361` 자동 감지로만 설정 가능.
- **영향**: 사용자가 의도적으로 혼합 시점을 선택할 수 없음. 자동 감지는 기존 원고 분석 기반이므로, 새 프로젝트에서는 설정 불가.
- **제안**: POV_OPTIONS에 `"혼합"` 추가 (`stage0/__init__.py:64`, `stage01_helpers.py:129`).
- **비용**: 매우 낮 (리스트 1항목 추가)
- **확신도**: HIGH

#### POV-G4. 에피소드/Arc 단위 POV 전환 미지원 [P3]

- **현황**: POV는 `protagonist_config.pov` 단일 전역 값. 에피소드별 또는 Arc별 POV 변경 메커니즘 없음.
- **영향**: "짝수 화는 적대자 시점" 같은 교대 POV 구조 불가. Blueprint `scene_presets`로 씬 단위 전환은 가능하나, 에피소드 전체 시점 교대는 불가.
- **제안**: 장기 후순위. 현재 장르(투자물/무협 등)에서 교대 POV 수요 낮음. 향후 미스터리/군상극 장르 추가 시 재검토.
- **비용**: 높 (파이프라인 전체 POV 동적 전파 필요)
- **확신도**: HIGH

#### POV-G5. Advisory 체인 POV 무인지 [P2]

- **현황**: InfoParadoxChecker만 POV 인지 (1인칭 전용 게이트). 나머지 advisory 5종(NpcDrift, FlashbackVerifier, RelDrift, NumericDrift, LongTermRep)은 POV 무관하게 작동.
- **영향**:
  - FlashbackVerifier: 1인칭 회상은 주인공 기억만 가능한데, NPC 시점 회상도 동일하게 검사.
  - NpcDriftAdvisor: 1인칭에서 NPC 속성 묘사는 주인공 인식 필터를 거침. Drift 감지 시 "주인공이 모르는 NPC 변화"를 잘못 경고할 수 있음.
- **제안**: FlashbackVerifier에 POV 게이트 추가 (1인칭 시 주인공 기억 범위 제한). NpcDriftAdvisor는 현행 유지 (Director가 판단).
- **비용**: 낮 (FlashbackVerifier 조건 추가 ~10줄)
- **확신도**: MEDIUM (실제 오탐 빈도 미측정)

#### POV-G6. CW Self-Critique에 POV 검사 부재 [P2]

- **현황**: `chief_writer_quality.py` self-critique 15개 체크 중 POV 전용 검사 없음. POV 강제는 전적으로 StyleGuide 프롬프트 주입에 의존.
- **영향**: CW가 self-critique 루프에서 POV 위반을 스스로 수정할 기회 없음. Pre-LLM 검사 후 Director 심사까지 POV 교정 경로 부재.
- **제안**: Self-critique 16번째 체크 `_check_pov_consistency_critique`: 원고에서 대사 제거 후 POV 위반 대명사 패턴 검사. 기존 pre_llm_validator 로직 재사용.
- **비용**: 낮 (pre_llm regex 재사용 ~20줄)
- **확신도**: HIGH

### POV 갭 우선순위 요약

| ID | 항목 | 우선순위 | 비용 | 확신도 |
|----|------|----------|------|--------|
| POV-G1 | 전지적/혼합 POV 검증 추가 | P1 | 낮 | HIGH |
| POV-G2 | Director POV 값 전달 | P1 | 매우 낮 | HIGH |
| POV-G3 | 혼합 POV 메뉴 추가 | P2 | 매우 낮 | HIGH |
| POV-G5 | FlashbackVerifier POV 게이트 | P2 | 낮 | MEDIUM |
| POV-G6 | CW Self-Critique POV 검사 | P2 | 낮 | HIGH |
| POV-G4 | 에피소드/Arc 단위 POV 전환 | P3 | 높 | HIGH |

---

## TF-D. 실전 시나리오 10건 검증 (6-pass)

> 시스템 구조 기반 실패 시나리오를 코드 레벨에서 교차 검증.
> CONFIRMED GAP = 방어 0%, PARTIALLY HANDLED = 부분 방어 (LLM 의존 또는 제한적 범위)

### SC-1. 비밀 정보 전파 [CONFIRMED GAP] → NPC-S1

**시나리오**: 주인공이 A에게만 비밀을 말함 → 5화 후 B가 그 비밀을 아는 것처럼 행동

- **현황**: `InfoParadoxChecker`(`info_paradox_checker.py:29`)는 **주인공 지식만** 추적 (`build_knowledge_summary()` → "주인공이 아는 정보"). NPC 간 정보 전파 추적 없음.
- **근거**: `fact_ledger.py` — "who told whom" 필드 없음. `world_state.py:34-54` — NPC `known_attrs`에 knowledge 필드 없음. `episode_bibles`의 `reveals`/`witnesses`도 주인공 기준.
- **영향**: 미스터리/스릴러 장르에서 핵심 서사 장치인 "비밀 공유 범위"가 시스템적으로 보호 안 됨.
- **제안**: NPC `known_attrs`에 `secrets_known` 리스트 추가 (episode_bibles에서 자동 수집). CW 프롬프트에 `[NPC별 비밀 인지 범위]` 주입. Director 체크리스트에 `secret_consistency` 항목 추가.
- **비용**: 중 (WorldState 확장 + episode_bibles 파싱 + CW/Director 주입)
- **우선순위**: P1
- **확신도**: HIGH

### SC-2. 죽은 NPC 소지품 증발 [CONFIRMED GAP] → NPC-S2

**시나리오**: 핵심 증거 USB를 든 NPC가 사망 → USB가 어디 갔는지 시스템이 모름

- **현황**: `fact_ledger.py:181,194` — 아이템 owner 항상 "주인공" 하드코딩. `world_state.py:130-135` — NPC 사망 시 `alive_npcs.pop()` → `dead_npcs[name] = {ep, cause}`. **소지품 이전 로직 0줄.**
- **근거**: `active_items`(`world_state.py:47`)도 주인공 전용. NPC 인벤토리 개념 자체가 없음.
- **영향**: NPC가 들고 있던 서사적 중요 아이템(증거, 열쇠, 무기)이 사망과 함께 데이터에서 소멸.
- **제안**: NPC 사망 시 `state_changes.items_transferred` 필드로 "NPC 소지품 → 주인공/다른NPC/유실" 명시. FactLedger에 `transfer_on_death` 이벤트 기록.
- **비용**: 중 (state_changes 스키마 + FactLedger 이벤트 + Analyst 프롬프트)
- **우선순위**: P2
- **확신도**: HIGH

### SC-3. 전문 지식 역전 [PARTIALLY HANDLED] → NPC-S3

**시나리오**: 투자물에서 라면집 사장 조연이 "CDS 스프레드 확대되면 숏 포지션을..."

- **현황**: NPC `role`/`personality`는 WorldState에 있고, CW 컨텍스트에 `get_npc_personality_summary()` + `get_npc_dialogue_style_summary()`로 주입됨 (`stage4_context_builder.py:1660-1669`).
- **방어 수준**: LLM이 NPC 직업 정보를 읽고 대사를 맞출 **가능성** 있음. 그러나 **"이 NPC는 금융 용어를 모른다"는 명시적 제약이 없음**. `character_voice`는 말투(경어/반말)만 추적, 어휘 범위 미추적.
- **제안**: NPC-G7(knowledge_era)의 확장으로 통합. NPC 등록 시 `expertise_domain` 태그 추가 → CW 프롬프트에 "라면집 사장은 금융 전문 용어를 사용하지 않습니다" 주입.
- **비용**: NPC-G7에 포함
- **우선순위**: P1 (NPC-G7 하위)
- **확신도**: HIGH

### SC-4. NPC 감정 리셋 [PARTIALLY HANDLED] → NPC-S4

**시나리오**: 10화에서 어머니 사망으로 절규한 조연 → 11화에서 웃으며 "오늘 날씨 좋네요~"

- **현황**: `protagonist_emotion`은 `{emotion, trigger, arc_no, episode}` 구조화 추적 (`state_tracker_npc.py:1946`). NPC는 `emotion_baseline`(정적 기준선, `state_tracker_npc.py:1724`) + `_extract_npc_reaction_patterns()`(반응 빈도 추적, `pattern_tracker.py:330`) 존재.
- **방어 수준**: `emotion_baseline`은 "차분한" 같은 **정적** 값. 트라우마 이벤트가 동적으로 반영 안 됨. `npc_personality_changes`가 state_changes에서 수집되지만, "슬픔 → 지속 N화" 같은 감정 지속 메커니즘 없음. TF-DB-E2 `감정 고착 경고`는 **전체 서사 톤** 기준, NPC별 아님.
- **제안**: NPC `known_attrs`에 `emotional_state` 동적 필드 추가 — 중대 이벤트(사망/배신/승진) 발생 시 자동 설정 + N화 후 자연 감쇠. CW 프롬프트에 `[NPC 감정 상태]` 주입.
- **비용**: 중 (WorldState 확장 + 감쇠 로직 + CW 주입)
- **우선순위**: P2
- **확신도**: HIGH

### SC-5. NPC 맹세 망각 [PARTIALLY HANDLED] → NPC-S5

**시나리오**: "이 검으로 반드시 원수를 갚겠다" 선언한 NPC → 15화 동안 아무 행동 없음

- **현황**: `promises` 시스템(`world_state.py:451-474`)에 `promiser`/`promisee` 필드 있음 — NPC 맹세 구조적 지원 **존재**. B-4(`chief_writer_quality.py:634-677`)가 promise 관련 당사자 등장 시 방치 여부 체크.
- **방어 수준**: NPC 맹세가 `commitments`로 등록될 **경우** 추적 가능. 그러나: ①Analyst LLM이 NPC 맹세를 `commitments`에 기록하는지 보장 없음 ②B-4는 **NPC가 해당 에피소드에 등장할 때만** 발동 — 15화 연속 미등장이면 경고 0회 ③`format_motivations` 방치 플래그(`≥3 Arc 방치`)는 `active_plots` 대상, NPC 개인 맹세는 plot 등록 필요.
- **제안**: NPC-G4(방치 NPC advisory)와 연계. Arc 설계 시 `promises` 중 `promiser`가 최근 N화 미등장인 건 → `[방치 맹세 경고]` advisory.
- **비용**: 낮 (NPC-G4 확장, 추가 쿼리 ~10줄)
- **우선순위**: P2
- **확신도**: HIGH

### SC-6. NPC 위치 텔레포트 [PARTIALLY HANDLED] → NPC-S6

**시나리오**: 서울에 있던 조연이 다음 화에서 설명 없이 부산에서 등장

- **현황**: NPC `known_attrs.location`에 위치 추적됨 (`world_state.py:525`). `get_summary()`에 `위치={location}` 노출. `director.yaml` `space_continuity` 체크리스트가 "캐릭터"(NPC 포함) 이동 자연스러움 검사. `NpcDriftAdvisor`(`npc_drift_advisor.py:112`)도 위치 drift 검사.
- **방어 수준**: **LLM 다중 계층** 방어(Director 체크리스트 + NpcDriftAdvisor). 그러나 **Python 수준의 NPC 위치 교차 검증은 없음** — 원고 내 NPC 출현 위치 vs `known_attrs.location` 자동 비교 없음. 에피소드 내 씬 간 NPC 텔레포트는 LLM 주의력에 의존.
- **제안**: Python 수준 보강 불필요 — 현재 LLM 2중 방어(Director + NpcDrift)로 충분. 만약 실파이프라인에서 반복 발생 시 NC-1에 NPC 위치 교차 검사 추가 고려.
- **비용**: 현행 유지
- **우선순위**: P3 (모니터링)
- **확신도**: HIGH

### SC-7. 이중 스파이 자기모순 [CONFIRMED GAP] → NPC-S7

**시나리오**: NPC가 주인공 앞에서는 아군, 악당 앞에서는 배신자 — 같은 씬에서 두 페르소나 섞임

- **현황**: WorldState NPC 스키마에 `secret_role`/`public_facade`/`known_by_characters` 필드 없음 (`world_state.py:44`). `character_voice`는 말투 일관성만 추적, 상황별 행동 분기 없음. `NpcDriftAdvisor`는 **단일 스냅샷** 대조(`npc_drift_advisor.py:33`) — 이중 정체 비교 불가.
- **근거**: "persona", "facade", "이중", "위장" 전수 검색 결과 프로덕션 코드 0건.
- **영향**: 스릴러/미스터리에서 이중 스파이·내통자가 핵심 서사인데, 페르소나 전환 규칙이 시스템적으로 강제 안 됨.
- **제안**: NPC 등록 시 `dual_identity` 옵션: `{public_role, secret_role, known_by: [NPC 이름 리스트]}`. CW 프롬프트에 "해당 NPC는 [known_by] 앞에서만 secret_role 행동" 주입. Director 체크리스트에 `identity_consistency` 항목 추가.
- **비용**: 중 (WorldState 스키마 + CW/Director 주입 + Bible 등록 UI)
- **우선순위**: P2
- **확신도**: HIGH

### SC-8. 회귀자 메타 지식 노출 [PARTIALLY HANDLED] → NPC-S8

**시나리오**: 회귀자 주인공이 아직 안 만난 NPC 이름을 자연스럽게 부름: "김대리, 거기 있었어?"

- **현황**: `InfoParadoxChecker`가 회귀자 예외 처리(`info_paradox_checker.py:154` — 전생 기억 기반 지식은 역설 아님). `build_knowledge_summary()`는 `episode_bibles`의 `reveals`/`witnesses`를 누적.
- **방어 수준**: LLM이 knowledge_summary vs 원고를 비교하여 역설 감지. 그러나: ①`first_seen_ep`이 WorldState에 있지만 `InfoParadoxChecker`가 **소비하지 않음** — "주인공이 NPC를 만난 시점" Python 교차 검증 없음 ②`episode_bibles`에 NPC 첫 만남이 `reveal`로 기록되는지는 **LLM 품질에 의존**.
- **제안**: `build_knowledge_summary()`에 `WorldState.alive_npcs[name].first_seen_ep` 교차 참조 추가 — "주인공이 ep N에서 처음 만난 NPC" 목록을 knowledge_summary에 추가. 회귀자는 전생 기억 예외 유지.
- **비용**: 낮 (info_paradox_checker.py에 WorldState 조회 ~15줄)
- **우선순위**: P2
- **확신도**: HIGH

### SC-9. 시간 역행 NPC [PARTIALLY HANDLED] → NPC-S9

**시나리오**: Arc 3에서 "5년 경력 의사"였던 NPC가 Arc 7에서 "3년차 레지던트"로 후퇴

- **현황**: `_check_title_consistency()`(`numeric_consistency_checker.py:559-617`)가 직함 변경 감지. `_TITLE_RANK`(L119-141)에 기업 직급(사원~회장) 순서 있음. `NpcDriftAdvisor`(`npc_drift_advisor.py:111`)가 "역할 변화" LLM 검사.
- **방어 수준**: 기업 직급 역행(부장→과장)은 Python 감지. 그러나 **의료**(인턴→레지던트→전문의→교수), **군사**(이등병→상등병→하사), **스포츠**(2군→1군→국대), **학술**(석사→박사→교수) 등 **비기업 직급 순서가 `_TITLE_RANK`에 없음**. NpcDriftAdvisor LLM이 잡을 수 있지만 보장 없음.
- **제안**: `_TITLE_RANK`에 의료/군사/학술/스포츠 직급 계층 추가 (각 5~10항목). 장르별 분기로 해당 장르 직급만 활성화.
- **비용**: 낮 (딕셔너리 확장 ~30줄 + 장르 분기 ~10줄)
- **우선순위**: P2
- **확신도**: HIGH

### SC-10. 장르 혼선 NPC 대사 [CONFIRMED GAP] → NPC-S10

**시나리오**: 의료물 간호사가 "크리티컬 히트!" / 스포츠물 코치가 "마나가 부족해"

- **현황**: Tier 3 장르(MEDICAL/SPORTS/COOKING/COMPOSER/ALT_HISTORY)의 `run_deep_validation()`이 전부 `super()` passthrough. `forbidden_terms`는 **타 장르 용어 침입** 방지(예: 의료물에서 "내공"/"마나" 금지)이지, **장르 내 NPC 부적합 대사** 미검사.
- **근거**: `base_guard.py:228-237` — `if term in manuscript` 전체 원고 단일 검색. NPC별 대사 분리 없음. "크리티컬 히트"는 어떤 장르 guard에도 금지어로 등록 안 됨.
- **영향**: NPC 직업과 무관한 타 분야 용어(게임/군사/금융)가 대사에 등장해도 미감지.
- **제안**: GENRE-G1(Tier 3 deep validation)과 통합. 장르별 "NPC 직업 부적합 용어" 사전 추가 → `run_deep_validation()`에서 대사 블록 분리 후 NPC role 기반 어휘 검사. 또는 NPC-G7(knowledge_era) 확장으로 해결.
- **비용**: GENRE-G1에 포함
- **우선순위**: P2
- **확신도**: HIGH

### 시나리오 검증 결과 요약

| # | 시나리오 | 판정 | 근본 원인 |
|---|----------|------|-----------|
| SC-1 | 비밀 정보 전파 | **CONFIRMED GAP** | NPC 간 지식 추적 0 |
| SC-2 | 죽은 NPC 소지품 | **CONFIRMED GAP** | NPC 아이템 추적 0, 사망 시 이전 로직 0 |
| SC-7 | 이중 스파이 모순 | **CONFIRMED GAP** | 이중 정체 데이터 모델 0 |
| SC-10 | 장르 혼선 NPC 대사 | **CONFIRMED GAP** | Tier 3 deep validation passthrough |
| SC-3 | 전문 지식 역전 | **PARTIALLY** | NPC role 컨텍스트 있으나 대사-전문성 제약 없음 |
| SC-4 | NPC 감정 리셋 | **PARTIALLY** | emotion_baseline 정적, 트라우마 지속 없음 |
| SC-5 | NPC 맹세 망각 | **PARTIALLY** | promises 구조 있으나 NPC 미등장 시 미발동 |
| SC-6 | NPC 위치 텔레포트 | **PARTIALLY** | LLM 2중 방어 존재, Python 교차 검증 없음 |
| SC-8 | 회귀자 메타 지식 | **PARTIALLY** | InfoParadox 존재, first_seen_ep 미소비 |
| SC-9 | 시간 역행 NPC | **PARTIALLY** | 기업 직급만 순서화, 비기업 직급 미지원 |

---

## 오탐/사실 교정 기록

| 초기 판단 | 검증 결과 | 처리 |
|-----------|-----------|------|
| "Character Voice → CW 미전달" | `chief_writer_context.py:304-328` I-25 보이스 가이드 이미 존재 | **오탐 제거** |
| "Forgotten NPC 감지 완전 부재" | `chief_writer_context.py:1045-1071` NPC 빈도 경고 존재 (CW 단계). 단, Arc 설계 단계에는 미전달 | **보정: NPC-G4로 범위 축소** |
| "Arc state_changes NPC는 Stage4에서 완전 탈락" | Smart Retrieval는 `_collect_npc_roster()`로 일부 보완. 다만 structured CP는 여전히 Blueprint 본문 중심 | **보정: NPC-G5를 'structured CP 누락'으로 축소** |
| "나머지 7개 장르는 전부 generic only" | INVESTMENT는 `get_all_summaries(genre=\"investment\")` 경로에서 `financial_state`가 암묵 주입 | **보정: GENRE-G3 문구 축소** |
| "Director는 POV 값을 전혀 못 받음" | `director_auditor.py`는 `validation_context[\"pov\"]` 소비 준비 완료. 다만 caller wiring 약함 | **보정: POV-G2를 wiring gap으로 재정의** |

---

## 전체 우선순위 요약

### P1 (즉시 효과)

| ID | 항목 | 비용 | 시나리오 |
|----|------|------|----------|
| NPC-G4 | Arc 설계 방치 NPC advisory | 낮 | SC-5 연계 |
| NPC-G7 | NPC별 지식 경계 (knowledge_era/tags/expertise) | 중 | SC-1, SC-3 |
| SC-1 | NPC 비밀 인지 범위 추적 | 중 | 비밀 정보 전파 |
| POV-G1 | 전지적/혼합 POV 검증 | 낮 | — |
| POV-G2 | Director POV 값 전달 | 매우 낮 | — |

### P2 (중기)

| ID | 항목 | 비용 | 시나리오 |
|----|------|------|----------|
| NPC-G2 | known_attrs personality 동기화 | 낮 | — |
| NPC-G3 | NpcDriftAdvisor 5→8 상향 | 낮 | — |
| NPC-G5 | Arc state_changes 엔티티 → structured CP 포함 | 낮 | — |
| NPC-G1/SC-4 | NPC 감정 상태 동적 추적 | 중 | NPC 감정 리셋 |
| SC-2 | 사망 NPC 소지품 이전 | 중 | 소지품 증발 |
| SC-5 | NPC 맹세 방치 경고 | 낮 | 맹세 망각 |
| SC-7 | 이중 정체 데이터 모델 | 중 | 이중 스파이 |
| SC-8 | InfoParadox first_seen_ep 교차 | 낮 | 회귀자 메타 지식 |
| SC-9 | 비기업 직급 순서 확장 | 낮 | 시간 역행 NPC |
| SC-10/GENRE-G1 | Tier 3 deep validation | 높 | 장르 혼선 대사 |
| GENRE-G2 | Tier 3 DB Registry | 중 | — |
| GENRE-G3 | Context 장르 분기 확장 | G2 의존 | — |
| POV-G3 | 혼합 POV 메뉴 | 매우 낮 | — |
| POV-G5 | FlashbackVerifier POV 게이트 | 낮 | — |
| POV-G6 | CW Self-Critique POV 검사 | 낮 | — |

### P3/NO-GO

| ID | 항목 | 사유 |
|----|------|------|
| SC-6 | NPC 위치 텔레포트 Python 검증 | LLM 2중 방어로 충분, 모니터링만 |
| NPC-G6 | NPC 아이템 소유 | FactLedger 스키마 변경, ROI 낮음 |
| GENRE-G4 | 금지어 비대칭 | 도메인 특성 비례 |
| POV-G4 | 에피소드/Arc POV 전환 | 파이프라인 전면 재설계 |

---

## 파일 변경 예상 (구현 시)

| 파일 | 변경 | ID |
|------|------|-----|
| `four_phase_arc_generator.py` | 방치 NPC advisory + 방치 맹세 경고 주입 | NPC-G4, SC-5 |
| `world_state.py` | known_attrs 확장 (personality/knowledge_era/emotional_state/secrets_known) + dual_identity 옵션 | NPC-G2, NPC-G7, SC-1, SC-4, SC-7 |
| `stage4_context_builder.py` | NPC 지식 범위 + 비밀 인지 + 이중 정체 CW 프롬프트 주입 + Arc state_changes 엔티티를 structured CP 후보에 병합 | NPC-G7, SC-1, SC-7, NPC-G5 |
| `info_paradox_checker.py` | build_knowledge_summary에 first_seen_ep 교차 참조 | SC-8 |
| `numeric_consistency_checker.py` | _TITLE_RANK에 의료/군사/학술/스포츠 직급 추가 | SC-9 |
| `director.yaml` | npc_knowledge_boundary + secret_consistency + identity_consistency 체크리스트 | NPC-G7, SC-1, SC-7 |
| `director_ensemble.py` | _nc3_keys 확장 (18~20번째) | NPC-G7, SC-1, SC-7 |
| `response_schemas.py` | consistency_checklist 키 확장 | NPC-G7, SC-1, SC-7 |
| `npc_drift_advisor.py` | max_npcs 상향 + 우선순위 정렬 | NPC-G3 |
| `pre_llm_validator.py` | 전지적/혼합 POV 검사 | POV-G1 |
| `stage4_interview_round.py` | Director MC POV 값 주입 | POV-G2 |
| `stage0/__init__.py` + `stage01_helpers.py` | 혼합 POV 메뉴 항목 | POV-G3 |
| `flashback_verifier.py` | POV 게이트 | POV-G5 |
| `chief_writer_quality.py` | Self-critique 16번째 POV 검사 | POV-G6 |
| `genre_guards/{cooking,composer,medical,sports,alt_history}_guard.py` | Deep validation + NPC 직업 어휘 검사 | GENRE-G1, SC-10 |
| `state_tracker.py` | 장르별 레지스트리 | GENRE-G2 |

---

## 절대 하지 말 것

- Director score_breakdown 가중치(40/20/20/10/10) 변경 금지
- 기존 advisory 체인 순서 변경 금지
- Genre Guard 기존 금지어 목록 변경 금지
- POV 전역 설정 구조 변경 금지 (protagonist_config.pov 단일 값 유지)
- InfoParadoxChecker의 1인칭 전용 게이트 제거 금지
- Self-critique 기존 15개 체크 로직 수정 금지
- NPC 지식 경계를 Python REJECT로 강제하지 말 것 (advisory만, 대원칙 3 준수)
