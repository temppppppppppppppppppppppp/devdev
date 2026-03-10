# TF-DB 전수조사: DB/State 활용 극대화 — 퀄리티 부스트

> 작성: 2026-03-10
> 상태: 3-pass 감리 3차 완료 (2026-03-10, 실행 전 보강 반영 — B1 사실관계 수정 / E2 경로 수정 / 검증 계획 현실화)
> 전제: `db-utilization-boost-codex-order.md`(§1~§10)과 독립. 중복 항목은 §번호로 참조.
> 목표: "저장되어 있지만 LLM이 못 보는" 데이터를 **전량** 식별하여 퀄리티 상승 경로 확보

---

## 공통 원칙

- **LLM 호출 0회** — 순수 Python 데이터 조립
- **읽기 전용** — DB/WorldState/FactLedger에 쓰기 금지
- **비치명** — 실패 시 `logging.debug` + skip, 기존 동작 불변
- **Director 주권** — advisory만 제공, REJECT 강제 금지 (대원칙 3)
- **오탐 고지** — Python 자동 감지이므로 각 advisory에 `(Python 자동 감지 — 오탐 가능, 참고용)` 포함

> `Codex 메모`
> 이 문서는 본문을 `Opus` 주장으로 보고, 쟁점이 남은 항목에만 `Codex`가 반론/동의를 적는 방식으로 재감리한다.
> 현재 기준으로 핵심 토론 포인트는 `A1`, `B1`, `D1`, `E2`, `검증 계획`이다. 나머지 항목은 이번 버전에서 대체로 정리됐다.
>
> `Codex 3-pass 결론`
> - `A1`: 동의 유지. `motivations`/`promises`의 CW 생성 프롬프트 우회 주입 경로는 재확인되지 않았다.
> - `B1`: 수정 필요. Stage 2 Arc 생성기가 FactLedger를 읽으려 하지만 `_load_execution_state()`가 현재 스키마(`numbers`/`items`/`characters`...)가 아닌 `fact_ledger["facts"]`를 참조해 실효성이 낮다.
> - `D1`: 반론 유지. `item_state_registry`는 실제로 populate되고 Stage 4에 노출된다.
> - `E2`: 반론 유지. 단, raw `protagonist_emotions` 리스트가 직접 노출되는 것은 아니고, 저다양성 경고 형태의 간접 사용이다.
> - `검증`: `tests/test_db_quality_boost.py`는 현재 저장소에 없으므로, 기존 분산 테스트군 기준으로 검증 계획을 다시 쓰는 편이 정확하다.

---

## 카테고리 A: WorldState 미노출 필드

### TF-DB-A1. `motivations`/`promises` — `get_summary()` 미포함

**현황**:
- `world_state.py` §13(protagonist_motivations), §14(commitments/promises)에서 쓰기
- 최대 20개 motivation, 30개 promise 저장
- `get_summary()`에 **미포함** — Stage 2/3 LLM이 전혀 못 봄
- Stage 4 Director MC: `stage4_interview_round.py`에서 `_ws._state.get("motivations")` 직접 접근
- Stage 4 CW 사후 검증: `chief_writer_quality._check_motivation_consistency()` (L622-665, self-critique 5번째 체크)에서 `_common_writer_kwargs` 경유 참조 — **단, CW LLM 프롬프트에는 미주입** (사후 검증용만)

**갭**: CW LLM 프롬프트에 주인공 동기/약속 미포함 — 생성 시점에 모름 (사후 검증으로만 잡음). Stage 2 Arc 생성 시에도 미참조.

**해법**:
- `get_summary()`에 `[주인공 핵심 동기]`, `[서약/약속]` 섹션 추가
- active 상태만 표시, 최대 10건씩, since_ep 포함
- Stage 2 `_generate_prev_context()`에도 주입

**영향**: Arc가 기존 동기/약속을 무시하고 새 동기를 만드는 문제 방지. CW가 "이미 약속한 것"을 인지.

**우선순위**: P1
**파일**: `modules/core/world_state.py` (`get_summary()`)

> `Opus`
> CW는 동기/약속을 사후 검증에서만 보고, 생성 프롬프트에서는 못 본다.
>
> `Codex`
> 동의. 이번 버전의 A1은 맞다.
> `stage4_interview_round.py`에서 `motivations`/`promises`를 `_common_writer_kwargs`로 넘기긴 하지만, `chief_writer.py`의 `_generate_single_candidate()`는 `full_prompt`를 `common_context`만으로 조립한다.
> `chief_writer_context.py`도 `motivations`/`promises`를 인자로 받지 않고, `world_state_summary`/`mandatory_context` 경로에서도 이 값이 별도 합성되지 않는다.
> 실제 사용 지점은 `chief_writer_quality.py`의 self-critique 체크이므로, "CW LLM 프롬프트에는 미주입"이라는 판단은 현재 코드 기준으로 타당하다.

---

### TF-DB-A2. `cumulative_elapsed` — `get_summary()` 미포함

**현황**:
- `world_state.py` §12에서 `{"total_days": int, "history": [{ep, days, desc}]}` 저장
- `get_summary()`에 **미포함**
- Stage 4: `NarrativeContextFormatter.format_cumulative_time()` → Director MC 주입
- Stage 2: `stage2_preflight.py` L493-509에서 읽어서 `NarrativeContextFormatter`로 전달 → enhanced_context 주입

**갭**: CW가 "총 며칠 경과했는지" 모름. Stage 3만 미참조.

**해법**:
- `get_summary()`에 `[누적 경과] 총 {total_days}일` 1줄 추가

**우선순위**: P2 (Director MC + Stage 2 preflight에 이미 주입 중, Stage 3만 잔여)
**파일**: `modules/core/world_state.py` (`get_summary()`)

---

### TF-DB-A3. `get_summary()` Truncation 무경고

**현황**:
- 생존 NPC: sorted[:30], 사망 NPC: [:20], 관계: [:20], 아이템: [:20], 파괴: [-10:], 플롯: [-10:], 타임라인: [-5:]
- 절삭 시 **LLM에 절삭 사실을 알려주지 않음**

**갭**: 250명 생존 NPC 중 30명만 보이지만, LLM은 "30명이 전부"로 인식. 절삭된 220명의 존재 자체를 모름.

**해법**:
- 각 섹션 끝에 절삭 카운터 추가: `(총 250명 중 30명 표시)` 형태
- 절삭 0이면 카운터 미표시

**예시**:
```python
# 변경 전
lines.append(f"생존 NPC ({len(alive_sorted)}명)")
# 변경 후
_total = len(all_alive)
_shown = len(alive_sorted)
_trunc = f" (총 {_total}명 중 {_shown}명 표시)" if _total > _shown else ""
lines.append(f"생존 NPC ({_shown}명){_trunc}")
```

**우선순위**: P1
**파일**: `modules/core/world_state.py` (`get_summary()` 7개 섹션)

---

### TF-DB-A4. `world_notes` 필드 — Dead Field

**현황**:
- `_INIT_STATE`에 `"world_notes": []` 정의
- 10-item buffer 제한 로직 존재 (L549-554)
- **쓰기 0회, 읽기 0회** — 완전한 dead field

**해법**: 스키마에서 제거하거나, 용도 결정 후 구현. 현 시점에서는 dead code.

**우선순위**: P2 (dead code 정리)
**파일**: `modules/core/world_state.py`

---

## 카테고리 B: FactLedger 미노출 데이터

### TF-DB-B1. FactLedger — Stage 2/3 직접 주입 부재 (기존 Arc 핸드오프도 실효성 낮음)

**현황**:
- `fact_ledger.to_summary(max_chars=25000)` → Stage 4 `build_mandatory_context()`에 주입
- Stage 2 Arc 생성: `_load_execution_state()` (four_phase_arc_generator.py L1363-1375)에서 Arc N+1 생성 시 FactLedger 로드 **시도**
- 단, 현재 구현은 `fact_ledger["facts"]`를 읽으며 실제 FactLedger 스키마는 `numbers`/`items`/`characters`/`locations`/`organizations`라 **스키마 불일치**
- **Stage 2 preflight / Stage 3 Blueprint에는 직접 미주입**

**갭**: Stage 2 Arc 생성기조차 수치 팩트 핸드오프가 불안정하고, Stage 2 preflight/Stage 3 Blueprint에는 직접 주입 경로가 없다.

**해법**:
- `four_phase_arc_generator._load_execution_state()`에서 `numbers` 기준 핵심 수치 추출로 스키마 정합 복구
- Stage 2 preflight `enhanced_context`에 핵심 수치 주입
- Stage 3 `_bp_semantic_ctx`에 핵심 수치 팩트 요약 주입

**우선순위**: P1 (기존 "부분 해소" 경로도 현재 스키마 불일치로 실효성이 낮아 사실상 미해결에 가깝다)
**파일**: `modules/domain/agents/four_phase_arc_generator.py`, `modules/core/stage2_preflight.py`, `modules/core/stage3_orchestrator.py`

---

### TF-DB-B2. `established_value` — `to_summary()` 미포함

**현황**:
- `fact_ledger.py:265`에서 `setdefault("established_value", value)` 저장 — 최초 등록 시점 값
- `to_summary()`에서 현재값만 표시, **초기값 미표시**

**갭**: LLM이 "자본금 10억"만 보고 "원래 1억이었다"를 모름. 성장/하락 추세 파악 불가.

**해법**: CP 확장(continuity-packet-ext-codex-order.md §3-B)에서 이미 해결됨.
추가로 `to_summary()`에도 `초기값→현재값` 포맷 추가 검토.

**우선순위**: P2 (CP 확장에서 부분 해소)
**파일**: `modules/core/fact_ledger.py` (`to_summary()`)

---

### TF-DB-B3. `to_summary()` 섹션별 Truncation 무경고

**현황**:
- 캐릭터(생존): [:30], 아이템(활성): [:20], 아이템(소실): [:10], 장소: [:10], 조직: [:10], 수치: [:15]
- **섹션별 절삭 카운터 없음** — "캐릭터 100명 중 30명 표시" 같은 알림 미생성
- 참고: `max_chars` 초과 시에는 전체 절삭 메시지 `"... (팩트 원장 절삭)"` 존재 (L548-549). 이것은 전체 문자열 레벨 절삭이며, 섹션별 항목 수 절삭과는 다른 레벨.

**갭**: TF-DB-A3과 동일 패턴. 섹션별 항목 수 절삭 사실을 LLM에 미고지.

**해법**: A3과 동일 — 각 섹션 절삭 카운터 추가.

**우선순위**: P1
**파일**: `modules/core/fact_ledger.py` (`to_summary()`)

---

## 카테고리 C: DB 테이블 Dead Code / Dead Read

### TF-DB-C1. `surgery_logs` 테이블 — 완전 Dead

**현황**:
- 6컬럼 (id, ep_num, error_category, failed_logic, surgery_result, created_at)
- `save_surgery_log()` 메서드 존재하나 **호출 0회**
- 읽기 메서드 **없음**

**해법**: 테이블 + 메서드 삭제.

**우선순위**: P2
**파일**: `modules/core/db_manager.py`

---

### TF-DB-C2. `cost_log` 테이블 — Write-Only

**현황**:
- 9컬럼 (session_id, scope_type, total_calls, total_tokens, total_cost_usd, model_breakdown 등)
- `save_cost_record()` — Stage 2/3/4에서 **6회 호출** (stage2_finalizer×2, stage3_orchestrator×1, stage4_interview_round×1, stage4_post_processor×2)
- `get_cost_summary()` — **프로덕션 호출 0회**

**갭**: 비용 데이터를 매화 저장하지만 아무도 읽지 않음.

**해법 (퀄리티 관점)**: 비용 자체는 퀄리티와 무관하므로 P2. 단, "고비용 전략 대비 합격률" 분석은 FailureAnalyzer에서 가능.

**우선순위**: P2
**파일**: `modules/core/db_manager.py`

---

### TF-DB-C3. Dead Read 메서드 일괄 (6건)

**현황** — 프로덕션 호출 0회인 read 메서드:

| 메서드 | 테이블 | 대체 경로 |
|--------|--------|-----------|
| `get_lore_item()` | encyclopedia | `get_lore_list_by_category()` 사용 중 |
| `get_satisfaction_tag()` | episode_satisfaction_tags | `get_recent_satisfaction_tags()` 사용 중 |
| `get_selection_analysis()` | director_selections | `get_fix_scope_stats()` 사용 중 |
| `get_recent_selections()` | director_selections | `get_strategy_win_rates()` 사용 중 |
| `get_all_manuscripts()` | manuscripts | `get_context_manuscripts()` 등 사용 중 |
| `get_all_blueprints()` | blueprints | `get_recent_blueprints()` 사용 중 |

> ~~`get_latest_episode_number()`~~ — **오탐 (감리에서 기각)**: stage4_orchestrator.py(2), project_manager.py(4), information_diffusion.py(1), narrative_diversity.py(1), project_service.py(1) 등 **10건 프로덕션 호출** 확인. Dead 아님.

**해법**: deprecated 마킹 또는 삭제. 퀄리티 영향 없음.

**우선순위**: P2
**파일**: `modules/core/db_manager.py`

---

### TF-DB-C4. `director_selections` 미사용 컬럼 (3건)

**현황**:
- `director_selections` **테이블 컬럼 기준** `selected_label`, `selection_reason`, `candidate_count`는 저장되지만 프로덕션 read 경로 없음
- 주의: `selection_reason` 문자열 자체는 런타임 dict/feedback 경로에서 사용 중이므로, 여기서의 "미사용"은 **DB persisted column 기준**
- 12컬럼 중 25%가 write-only

**해법**: 퀄리티 관점에서 `selection_reason`을 Director advisory에 재활용 가능 — "지난 5화 동안 어떤 이유로 후보를 선택했는지" Director가 참조.

**우선순위**: P2 (단독으로는 low impact)
**파일**: `modules/core/db_manager.py`, `modules/core/stage4_interview_round.py`

---

## 카테고리 D: StateTracker 미노출 데이터

### TF-DB-D1. 장르별 Registry 6종 검토 — 실제 미노출 갭은 5종

**현황** (`state_tracker.py` L142-150):

| Registry | 장르 | 저장 내용 | LLM 노출 |
|----------|------|-----------|----------|
| `skill_cooldown_registry` | 헌터 | 스킬 쿨다운 상태 | ✗ |
| `dungeon_clear_registry` | 헌터 | 던전 클리어 기록·랭크 | ✗ |
| `spell_repertoire` | 판타지 | 마법 티어·진행도 | ✗ |
| `blessing_curse_registry` | 판타지 | 활성 축복/저주 | ✗ |
| `filmography_registry` | 배우물 | 출연작·역할·연도 | ✗ |
| `item_state_registry` | 전장르 | 아이템 출처·상태·획득Arc | **✓** |

**갭**: StateTracker가 16종 카테고리를 추적하지만, 이 중 **5종** registry는 summary 추출 메서드가 **없음**. Director/CW가 스킬 쿨다운, 마법 티어, 축복/저주를 전혀 모름.

> `item_state_registry`는 갭 아님 — `get_item_state_summary()` (state_tracker_plots.py L302-314) 존재, `state_tracker_plots.py` L256-300에서 Arc의 `state_changes.major_items` + regex 폴백으로 실제 populate, `stage4_context_builder.py` L1375-1409에서 `get_all_summaries()` + 폴백 경로 양쪽에서 LLM에 주입. **수집 + 요약 + 주입 전량 구현됨.**

**해법**:
- 5종 registry에 `get_{name}_summary()` 메서드 추가
- `stage4_context_builder.py`의 StateTracker 16종 요약 블록에서 해당 장르일 때만 추가 주입

**우선순위**: P1 (장르별 핵심 메커니즘 정보 누락)
**파일**: `modules/domain/agents/state_tracker.py`, `modules/core/stage4_context_builder.py`

> `Opus`
> ~~장르별 registry 6종이~~ → **5종이** 수집만 되고 LLM에는 안 들어간다.
> `item_state_registry`는 Codex 지적대로 이미 완전 구현됨. 표 ✓로 수정, 파일 경로 `modules/domain/agents/state_tracker.py`로 수정. 갭 범위 6→5종 축소.
>
> `Codex`
> 여기엔 이견이 있다. 범위가 6종은 아니다.
> `item_state_registry`는 이미 `get_item_state_summary()`가 있고, `stage4_context_builder.py`가 `get_all_summaries()`와 폴백 경로 둘 다에서 이 값을 실제 주입한다.
> 게다가 `state_tracker_plots.py`는 Arc의 `state_changes.major_items`와 regex 폴백에서 `item_state_registry`를 실제 populate하고, `stage4_interview_round.py`의 validator 컨텍스트도 이 registry를 읽는다.
> 따라서 진짜 갭은 `skill_cooldown_registry`, `dungeon_clear_registry`, `spell_repertoire`, `blessing_curse_registry`, `filmography_registry`의 5종이다.
> 표의 `item_state_registry | ✗` 표시는 수정 필요하고, 작업 파일 경로도 `modules/core/state_tracker.py`가 아니라 `modules/domain/agents/state_tracker.py`가 맞다.
>
> `Opus 3-pass 결론`
> **Codex 전면 동의.** 코드 검증 결과:
> - `state_tracker_plots.py:256-300` populate 확인 (major_items + regex 이중 경로)
> - `state_tracker.py:1270` `get_all_summaries()`에 `("item_state", "get_item_state_summary")` 포함 확인
> - `stage4_context_builder.py:1375-1409` primary + fallback 양쪽 주입 확인
> - 파일 위치 `modules/domain/agents/state_tracker.py` 확인 (core 아님)
> 표, 파일 경로, 갭 범위 전부 Codex 의견대로 수정 완료.

---

### TF-DB-D2. `known_attrs` (NPC 속성 변경) — 분산 노출

**현황**:
- `world_state.update_from_state_changes()` §9/15/16/17에서 NPC별 `known_attrs` dict에 injury/location/permanent_injuries 저장
- **NpcDriftAdvisor**에서 참조
- **`get_canonical_constraints()`** (world_state.py L597-605)에 `known_attrs` 포함 → `stage4_context_builder.py` L1322에서 호출 → mandatory_context에 주입
- `get_summary()`의 NPC 블록에는 미포함

**갭**: `canonical_constraints` 경유로 Stage 4 CW/Director에는 전달되나, `get_summary()` NPC 블록에서는 빠져있어 요약 계층에서 보이지 않음. 보완 가치는 있으나 "완전 블라인드"는 아님.

**해법**:
- `get_summary()` NPC 블록에 `known_attrs` 주요 필드(injury, location, permanent_injuries) 포함
- NPC당 최대 1줄 추가 (`부상: 안대, 위치: 서울시청`)

**우선순위**: P1
**파일**: `modules/core/world_state.py` (`get_summary()`)

---

## 카테고리 E: PatternTracker / WritingDirective 미노출

### TF-DB-E1. NPC 반응 패턴 — PatternTracker 미수집

**현황**:
- `PatternReport` dataclass에 `npc_reaction_patterns` 필드 존재
- `to_summary_text()` (pattern_tracker.py L103-105)에서 포맷 코드 존재
- `writing_directive_generator.py` L67에서 `to_summary_text()` 호출 → WritingDirective 생성에 반영
- **문제**: `build_report()` (L231-252)에서 `npc_reaction_patterns`를 **실제로 수집하지 않음** — 항상 빈 dict

**갭**: 포맷/소비 경로는 전부 존재하나 **데이터 수집 단계**가 미구현. `build_report()`에 NPC별 반응 패턴 추출 로직 추가 필요.

**해법**:
- `build_report()`에 NPC 반응 패턴 수집 로직 추가 (직전 N화 원고에서 regex/키워드 추출)
- 나머지 경로(to_summary_text → WDG → WritingDirective)는 이미 배선됨

**우선순위**: P1
**파일**: `modules/core/pattern_tracker.py` (`build_report()` 메서드)

---

### TF-DB-E2. `protagonist_emotions` — 조건부 간접 주입만 존재

**현황**:
- PatternReport에 `protagonist_emotions` list[str] (감정 키워드 목록) 수집 (`build_report()` L247, `_extract_emotions()` L302-320: 10개 한국어 감정 키워드 regex)
- `emotion_diversity` 계산 (`unique/total`, L250)
- `to_summary_text()` L99-101: `emotion_diversity < 0.4` 조건 충족 시 `【감정 빈곤】` 경고 생성
- `writing_directive_generator.py` L67: `to_summary_text()` 출력을 WDG 프롬프트에 주입 → LLM이 `emotion_required` 필드 생성 가능
- `chief_writer_context.py` L289-291: `emotion_required` 필드 CW 프롬프트에 주입

**간접 경로 요약**:
```
protagonist_emotions → emotion_diversity < 0.4 → to_summary_text() 【감정 빈곤】
→ WDG prompt → LLM → WritingDirective.emotion_required → CW prompt
```

**잔여 갭**:
1. `emotion_diversity ≥ 0.4`이면 경고 미생성 — 다양성이 적당한 수준이어도 **동일 감정 3화+ 연속** 같은 패턴은 미감지
2. `emotion_required` 준수 여부 self-critique에서 미검증 (`_check_writing_directive`는 `expression_ban`/`ending_style`만 체크)
3. raw 감정 분포(감정별 빈도)가 직접 전달되지 않음 — LLM 해석에 의존

**해법**:
- `to_summary_text()`에 diversity ≥ 0.4여도 지배적 감정 3화+ 연속 시 경고 추가
- self-critique에 `emotion_required` 준수 검증 추가

**우선순위**: P2
**파일**: `modules/core/pattern_tracker.py` (`to_summary_text()`), `modules/domain/agents/chief_writer_quality.py`

> `Opus`
> ~~수집 후 탈락~~ → **조건부 간접 주입만 존재**로 제목 변경. Codex 지적 수용.
> 코드 검증 결과:
> - `to_summary_text()` L99-101에서 `protagonist_emotions` 사용하여 `【감정 빈곤】` 경고 생성 확인 (조건: `emotion_diversity < 0.4`)
> - WDG L67 → LLM → `emotion_required` → CW L289-291 주입 경로 전량 확인
> - 따라서 "완전 미사용"/"수집 후 탈락"은 과장. **간접 경로 존재**.
> - 다만 "오탐"까지는 아님 — 잔여 갭 3건(조건부 트리거, self-critique 미검증, raw 분포 미전달)은 실질적.
> - 결론: **Codex 부분 동의**. 제목 변경 + 잔여 갭 명시로 해결.
>
> `Codex`
> 이건 아직 오탐으로 본다.
> `pattern_tracker.py`의 `PatternReport.to_summary_text()`는 이미 `protagonist_emotions`를 이용해 "감정 빈곤" 경고를 만들고, `writing_directive_generator.py`는 그 요약을 프롬프트에 넣는다.
> 다만 이 값이 항상 노출되는 것은 아니다. 현재는 `emotion_diversity < 0.4`일 때만 경고가 생성되므로, raw 리스트가 그대로 WritingDirective에 전달되는 구조는 아니다.
> 즉 현재 상태는 "완전 미사용"이 아니라 "저다양성일 때만 간접 요약으로 들어가고, 더 구조화된 감정 분포 주입은 없다"에 가깝다.
> 이 항목을 유지하려면 제목도 `수집 후 탈락`이 아니라 `간접 요약 주입만 존재` 정도로 낮추는 편이 정확하다.

---

## 카테고리 F: ReflexionManager 미활용

### ~~TF-DB-F1. `solution` 필드~~ — **오탐 (감리에서 기각)**

**감리 결과**: `get_prompt_injection()` L197-198에서 `solution` 필드 **이미 포함 중**.
```python
if pattern.get("solution"):
    prompt_parts.append(f"  해결책: {pattern['solution']}")
```
**조치 불필요.**

---

### TF-DB-F2. 빈도 추세 미활용

**현황**:
- 각 패턴에 `first_ep`, `last_ep`, `frequency` 저장
- "이 오류가 Arc 3 이후 50% 증가"같은 추세 분석 없음

**해법**: P2 후순위. db-utilization-boost §8에서 Director MC 주입으로 부분 해소.

**우선순위**: P2
**파일**: `modules/core/reflexion_manager.py`

---

## 카테고리 G: 텔레메트리 미소비

### TF-DB-G1. `llm_calls` 테이블 — FailureAnalyzer 내부만

**현황**:
- 18컬럼, 매 LLM 호출마다 저장
- FailureAnalyzer 내부 쿼리만 소비 (외부 공개 API 없음)
- **Director/CW에 미주입**

**해법 (퀄리티 관점)**: FailureAnalyzer 요약을 Director advisory로 주입 — "이번 Arc에서 REJECT 3회, 주 실패 원인: 수치 모순". db-utilization-boost §8에서 ReflexionManager 경로로 부분 해소.

**우선순위**: P2
**파일**: `modules/core/failure_analyzer.py`

---

### TF-DB-G2. `stage_attempts` 테이블 — FailureAnalyzer 내부만

**현황**: G1과 동일 패턴. 17컬럼 write, 내부 소비만.

**해법**: G1과 통합. FailureAnalyzer 요약 advisory.

**우선순위**: P2
**파일**: `modules/core/failure_analyzer.py`

---

## 카테고리 H: 교차 Stage 데이터 미전달

### TF-DB-H1. `karma_status` — Arc 생성 미참조

**현황**:
- `karma_status` 테이블에 NPC별 karma 이력 저장
- `get_all_karma()` — `project_manager.py`에서만 조회 (상태 표시용)
- **Stage 2 Arc Generator / Director에 미주입**

**갭**: NPC의 도덕적 궤적을 LLM이 못 봄. "악행 8회 누적 빌런"인데 갑자기 선행하는 Arc 생성 가능.

**해법**:
- Stage 2 `_generate_prev_context()`에 주요 NPC karma 요약 주입
- Director advisory로 karma 급변 경고

**우선순위**: P2
**파일**: `modules/domain/agents/four_phase_arc_generator.py`, `modules/core/stage4_interview_round.py`

---

### TF-DB-H2. `causal_graph` — Stage 2/3 미참조

**현황**:
- `get_recent_causal_links()` — Stage 4 post-processor (사후 기록)와 LM-post-1(Director MC 보조 주입)에서만 사용
- **Stage 2 Arc Generator / Stage 3 Blueprint에 미주입**

**갭**: Arc 설계 시 "이전 Arc의 인과관계 귀결"을 모름. Blueprint 생성 시 인과 체인 미참조.

**해법**:
- Stage 2 `_generate_prev_context()`에 최근 10화 causal_links 요약 주입
- 이미 LM-post-1에서 Director MC에는 주입 중 — Stage 2로 확장

**우선순위**: P2
**파일**: `modules/domain/agents/four_phase_arc_generator.py`

---

## 우선순위 요약

### P1 (퀄리티 직결 — 즉시 효과)

| ID | 항목 | 영향 |
|----|------|------|
| A1 | motivations/promises `get_summary()` 추가 | CW 프롬프트에 미주입 (사후 검증만) |
| A3 | Truncation 카운터 (WorldState) | LLM이 절삭 인지 |
| B1 | FactLedger Stage 3 주입 (S2 Arc 핸드오프 부분 해소) | Blueprint 수치 정합 |
| B3 | Truncation 카운터 (FactLedger) | LLM이 절삭 인지 |
| D1 | 장르별 Registry **5종** 노출 (item_state_registry 이미 구현) | 장르 메커니즘 정보 전달 |
| D2 | known_attrs `get_summary()` 보강 | canonical_constraints 경유 전달 중이나 summary 계층 미포함 |
| E1 | NPC 반응 패턴 build_report() 수집 로직 추가 | WDG 배선 완비, 데이터 수집만 누락 |

### P2 (보강 — 중기 효과)

| ID | 항목 | 영향 |
|----|------|------|
| A2 | cumulative_elapsed `get_summary()` | 시간 감각 보강 (Director MC + S2 preflight 주입 중, S3만 잔여) |
| A4 | world_notes dead field 정리 | Dead code 제거 |
| B2 | established_value 노출 | CP 확장에서 부분 해소 |
| C1 | surgery_logs 삭제 | Dead code 제거 |
| C2 | cost_log read 활성화 | 텔레메트리 |
| C3 | Dead read 6건 정리 (get_latest_episode_number 10건 호출 확인, 오탐 제거) | Dead code 제거 |
| C4 | selection_reason 재활용 | Director 이력 참조 |
| E2 | protagonist_emotions 조건부 간접 주입 보강 | 감정 다양성 (간접 경로 존재, 잔여 갭 3건) |
| ~~F1~~ | ~~solution 필드 주입~~ | **오탐 — 이미 구현됨** |
| F2 | 빈도 추세 분석 | §8에서 부분 해소 |
| G1/G2 | 텔레메트리 advisory | §8에서 부분 해소 |
| H1 | karma Stage 2 주입 | NPC 도덕 궤적 |
| H2 | causal_graph Stage 2 확장 | 인과 연속성 |

---

## db-utilization-boost-codex-order.md(§1~§10)와 중복/관계

| 본 TF | §번호 | 관계 |
|--------|--------|------|
| A1 | — | **신규** (§1~10에 없음) |
| A2 | — | **신규** |
| A3 | — | **신규** |
| B1 | — | **신규** |
| D1 | — | **신규** |
| D2 | — | **신규** |
| E1 | — | **신규** |
| C1 | — | **신규** (dead code) |
| C2 | — | **신규** (dead code) |
| H1 | — | **신규** |
| H2 | — | **신규** (§3과 부분 겹침 — §3은 arc_dependencies, H2는 causal_graph) |
| F1 | §8 | **보완** — §8은 Director MC 주입, F1은 CW 주입 내 solution 필드 |
| G1/G2 | §8 | **보완** — §8은 ReflexionManager 경로, G1/G2는 FailureAnalyzer 경로 |

---

## 파일 변경 목록 (예상)

| 파일 | 변경 | TF ID |
|------|------|-------|
| `modules/core/world_state.py` | `get_summary()` 4개 섹션 추가 + 7개 절삭 카운터 | A1, A2, A3, D2 |
| `modules/core/fact_ledger.py` | `to_summary()` 6개 절삭 카운터 | B3 |
| `modules/domain/agents/four_phase_arc_generator.py` | `_load_execution_state()` FactLedger 스키마 정합 수정 | B1 |
| `modules/core/stage2_preflight.py` | `enhanced_context` FactLedger 핵심 수치 주입 | B1 |
| `modules/core/stage3_orchestrator.py` | `_bp_semantic_ctx` FactLedger 핵심 수치 주입 | B1 |
| `modules/domain/agents/state_tracker.py` | 장르별 registry summary 메서드 5종 | D1 |
| `modules/core/stage4_context_builder.py` | StateTracker 장르 registry 주입 | D1 |
| `modules/core/pattern_tracker.py` | `build_report()` NPC 반응 패턴 수집 로직 추가 | E1 |
| `modules/core/pattern_tracker.py` | `to_summary_text()` 감정 경고 조건 확대 | E2 |
| `modules/domain/agents/chief_writer_quality.py` | `emotion_required` 준수 self-critique 검증 | E2 |
| ~~`modules/core/reflexion_manager.py`~~ | ~~`get_prompt_injection()` solution 추가~~ | ~~F1 오탐~~ |
| `modules/core/db_manager.py` | surgery_logs 삭제 + dead read 6건 정리 | C1, C3 |
| `tests/test_world_state_caps.py` 외 기존 관련 테스트 | 회귀/주입 테스트 보강 | 전량 |

> `Codex 메모`
> 실행 문서로 바로 쓸 때는 D1 경로를 먼저 고쳐야 한다.
> `state_tracker.py`의 실제 위치는 `modules/domain/agents/state_tracker.py`다.
> 또 E2를 유지한다면 `writing_directive_generator.py` 단독 수정보다 `pattern_tracker.py`의 요약 표현 강화와 세트로 보는 쪽이 더 정확하다.
>
> `Opus 3-pass 결론`
> D1 경로 수정 완료 (`modules/domain/agents/state_tracker.py`), E2 파일 대상도 `pattern_tracker.py` + `chief_writer_quality.py` 세트로 수정 완료. Codex 메모 전면 반영.

---

## 절대 하지 말 것

- WorldState.get_summary()의 **기존 cap 값**(30/20/20 등)을 변경하지 말 것 — 카운터만 추가
- FactLedger.to_summary()의 **기존 cap 값**을 변경하지 말 것 — 카운터만 추가
- LLM 호출을 추가하지 말 것
- DB 테이블 스키마를 변경하지 말 것 (C1 삭제 제외)
- 기존 advisory 체인(TruthGate, NpcDrift 등)을 수정하지 말 것
- Director MC 40K cap을 초과하지 말 것

---

## 검증 기준

- `tests/test_db_quality_boost.py` 단일 신규 파일을 전제하지 말 것 — 기존 분산 테스트군 우선
- `pytest tests/test_world_state_caps.py tests/test_narrative_context_formatter.py tests/test_cumulative_elapsed.py tests/test_canonical_constraints.py tests/test_lmi_known_attrs_sync.py tests/test_fact_ledger.py tests/test_pattern_tracker.py tests/test_chief_writer_quality.py tests/test_stage2_preflight.py tests/test_stage3_orchestrator.py tests/test_stage4_context_builder.py tests/test_db_manager.py -q` PASS
- `pytest --collect-only -q tests` 기준 전체 테스트 **3,756개 수집 유지** (2026-03-10 확인)
- `pytest tests/ -q` 전체 회귀 PASS
- `ruff check` 변경 파일 전량 0 violations
- `get_summary()` / `to_summary()` 기존 테스트 전량 PASS (회귀 0)
