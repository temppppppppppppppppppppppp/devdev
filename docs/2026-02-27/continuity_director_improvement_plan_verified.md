# 연속성·모순 방지 및 Director 권한 강화 계획 (검증본)

> 작성일: 2026-02-27
> 검증: OPUS TF 5개 병렬 코드 감사
> 원본 문서 대비 수정 사항: 오류 3건 정정, 의도된 설계 재분류 4건, 새 발견 2건

---

## 검증 총평

원본 문서(초안)의 주장 15개 중:

| 판정 | 건수 | 내용 |
|------|------|------|
| ✅ 사실 | 4건 | C2, C3, C5, D3 — 단, 3건은 **의도된 설계** |
| ⚠️ 부분적 사실 | 5건 | H1, C1, D1, D2, D4 |
| ❌ 오류 | 4건 | H2, H3, #1(Arc DB), #2(NPC 로스터) |
| 🔁 전제 오류 | 2건 | E1(state_changes 필드 소재), #3 일부 |

**실제 개선이 필요한 문제는 초안보다 적다.** 의도된 설계로 판명된 항목은 개선 대상에서 제거.

---

## 1. Stage 0 → Stage 2 오염 지점 (검증 결과)

### 1-1. H1: Bible.KeyNPCs ↔ StateTracker 미동기 — ⚠️ 부분적 사실

**코드 증거:**
- `modules/domain/agents/arc_ensemble.py:470` — Arc 생성 LLM 호출에 `assets=AssetLibrary JSON` 직접 주입
- `modules/domain/agents/state_tracker_npc.py:209` — 사망 NPC는 `{"status": "dead"}`로 npc_registry에 기록
- Bible.KeyNPCs 상태를 StateTracker와 동기화하는 코드: **존재하지 않음**

**실제 작동 방식:**
- Arc 생성(Phase 2)에는 **AssetLibrary만** 전달, StateTracker는 Validator(Phase 3)에만 전달
- 모순 신호가 동시에 전달되는 것이 아니라, **사망 정보가 빠진 채 Arc 생성**이 이뤄지는 것이 문제
- `prev_arc_context`(이전 Arc tactical_doc 전문)가 간접 보완하지만 명시적 사망 선언이 아님

**추가 발견 (신규):** TruthGate는 `info.get("deceased")` 키를 체크하지만, StateTracker는 `{"status": "dead"}`를 사용 → **키 불일치로 TruthGate의 사망 NPC 감지가 무력화될 수 있음** (`truth_gate.py:70`)

**결론:** H1의 핵심 — "동기화 없음"은 사실. 그러나 원인이 "모순 신호 동시 전달"이 아니라 "사망 정보 누락 전달"임. 더불어 TruthGate 키 불일치 버그도 발견.

---

### 1-2. H2: HUD 얕은 복사 오염 — ❌ 오류 (전제 잘못됨)

**원본 주장:** `list()` 얕은 복사로 중첩 객체가 공유된다.

**실제 코드:**
- `modules/core/genre_hud_manager.py:34-57` — `pro_root` property가 Bible dict 내부 **원본 참조를 그대로 반환**. 복사 자체 없음.
- `modules/domain/agents/state_tracker.py:57-68` — `EpisodeState.to_dict()`에서 `weapons`, `items`는 얕은 복사(`list.copy()`)이지만 **해당 필드들은 문자열 리스트**라 실제 공유 문제 없음. `extra_fields`는 `copy.deepcopy()` 올바르게 사용.
- StateTracker 롤백 스냅샷은 `copy.deepcopy()` 올바르게 사용 (`stage2_preflight.py:888-914`)

**수정:** "얕은 복사" 문제가 아니라 "복사 없는 원본 참조 반환"이 `pro_root`의 실제 특성. 단, 이것이 실제로 오염을 일으키는지는 `pro_root`를 수정하는 코드 존재 여부에 달림. **H2는 개선 대상에서 제거.**

---

### 1-3. H3: AssetLibrary + StateTracker 동시 전달 모순 신호 — ❌ 오류

**원본 주장:** 두 소스를 동시에 LLM에 전달해 모순 신호가 발생한다.

**실제 코드:**
- `modules/domain/agents/arc_ensemble.py:114-131` — `generate_ensemble()` 시그니처에 `state_tracker` 파라미터 없음
- `modules/domain/agents/four_phase_arc_generator.py:349-365` — Phase 2 (생성)에 AssetLibrary만 전달
- `modules/domain/agents/four_phase_arc_generator.py:433-441` — `state_tracker`는 Phase 3 (검증)에만 전달

**수정:** 두 소스가 "동시에 LLM에 전달"되지 않음. 진짜 문제는 H1과 동일 — **사망 정보가 빠진 AssetLibrary만 생성에 전달**. **H3은 개선 대상에서 제거, H1로 통합.**

---

## 2. Stage 2 → Stage 4 오염 지점 (검증 결과)

### 2-1. #1: Arc DB 미저장 — ❌ 오류

**원본 주장:** Arc가 메모리에만 존재, DB에 저장 안 됨.

**실제 코드:**
- `modules/core/stage2_finalizer.py:408` — `ctx.current_project.save_v20_anchor("arcs", all_refined_arcs)` 호출
- `modules/core/project_manager.py:264-272` — `anchors` 테이블에 JSON 저장 + `self.arcs` 메모리 동기화
- `modules/core/project_manager.py:156` — 기동 시 `load_all_anchors()`로 DB에서 복원

**수정:** Arc는 DB(`anchors` 테이블, key="arcs")에 정상 저장됨. 메모리는 DB 로드 캐시. **#1은 개선 대상에서 제거.**

---

### 2-2. #2: NPC 로스터 3필드만 스캔 — ❌ 오류

**원본 주장:** `_collect_npc_roster()`가 3개 필드만 스캔.

**실제 코드 (`stage4_context_builder.py:83-139`):**

실제로 4개 계층 스캔:
1. Arc `state_changes` → `npc_deaths`, `relationship_changes`, `npc_injuries` (3필드)
2. Blueprint 씬별 → `npcs`, `characters`, `participants` (3가지 키)
3. Blueprint 최상위 → `npc_roster`, `key_npcs`, `characters` (3가지 키)
4. `side_character` 필드: 코드베이스에 **존재하지 않는 필드명** (오탐)

**수정:** NPC 로스터 수집은 충분히 구현됨. **#2는 개선 대상에서 제거.**

---

### 2-3. #3: Blueprint 메타정보 Chief Writer 프롬프트 누락 — ⚠️ 부분적 사실

**필드별 검증 결과:**

| 필드 | 실제 상태 | 판정 |
|------|---------|------|
| `chain_link` | DB에서 별도 로드 → 명시적 섹션으로 주입 (`chief_writer_prompts.py:93`) | ❌ 원본 주장 오류 |
| `key_npcs` | Blueprint에 해당 필드 없음. 씬별 `characters`는 scene_breakdown JSON에 포함 | ⚠️ 대체로 무관 |
| `emotional_beat` | Chief Writer 코드·YAML 어디에도 없음. Treatment→Arc→Blueprint 간접 영향만 | ✅ 원본 주장 맞음 |
| `state_changes` | **이 필드는 Blueprint가 아닌 Arc의 필드**. Arc tactical_doc, dead_npcs, NPC 로스터로 간접 반영 | 🔁 전제 오류 |

**추가 발견 (신규):** Blueprint의 `protagonist_state`, `ending_state`, `time_flow`, `core_tension`, `ending_hook` 등이 Chief Writer에 전달되지 않음 (`chief_writer_context.py` 검증). 이 중 `ending_hook`(독자를 다음 화로 유인하는 설계)이 누락되는 것이 연속성 관점에서 실제 문제가 될 수 있음.

**결론:** `emotional_beat` 누락만 실제 문제. `state_changes`는 필드 소재 자체가 잘못된 전제. `chain_link`는 정상 전달됨.

---

## 3. Stage 4 내부 동계층 오염 지점 (검증 결과)

### 3-1. C1: director_feedback 덮어쓰기 — ⚠️ 부분적 사실

**코드 증거 (`stage4_interview_round.py:996-1016`):**
```python
# REJECT 시 director_feedback 처리
_prev_system_lines = [line for line in director_feedback.split("\n")
    if any(line.strip().startswith(p) for p in
           ("[연속성 충돌]", "[V67]", "[CoVe]", "[ToT", "[MAD"))]
director_feedback = "\n".join(action_items)  # ← assign (덮어쓰기)
if _prev_system_lines:
    director_feedback = "\n".join(_prev_system_lines) + "\n" + director_feedback
```

**실제 동작:**
- 시스템 접두사 라인(`[연속성 충돌]`, `[V67]`, `[CoVe]`, `[ToT`, `[MAD`)은 **추출-복원 메커니즘**으로 라운드 간 보존됨
- 일반 Director 피드백(예: "긴장감을 높여라", "대화 비율 줄여라")은 **소실됨**
- ToT/MAD 결과는 `+=` append로 누적됨 (L1038, L1052)

**결론:** 시스템 메시지는 보존, 일반 지시사항은 소실. 부분적 문제.

---

### 3-2. C2: HUD 재시도 중 미갱신 — ✅ 사실이지만 의도된 설계

**코드 증거:** `stage4_post_processor.py:214-230` — HUD 갱신은 `process_pass_result()`에서만, PASS 후 실행.

**의도:** 미확정 원고의 state_updates로 HUD를 변경하면 REJECT 후 상태가 오염됨. PASS 후 갱신이 정확한 설계. **개선 대상 아님.**

---

### 3-3. C3: BlockingValidator advisory 모드 — ✅ 사실이지만 의도된 설계

**코드 증거 (`stage4_interview_round.py:499-521`):**
```python
# [V70.1] 대원칙 준수: Python은 수집만, 판단은 Director(LLM)가.
```

CLAUDE.md 대원칙 1번의 명시적 이행. **개선 대상 아님 — 대원칙 위반 없음.**

---

### 3-4. C5: TruthGate 저장 후 실행 — ✅ 사실이지만 의도된 설계

**코드 증거 (`stage4_post_processor.py`):**
- L196-212: DB 저장
- L309-330: TruthGate 실행

**TruthGate 목적 (`truth_gate.py` docstring):** "memorize_v20_episode() 직전에 state_updates + manuscript를 교차 검증... **Advisory 모드이므로 저장을 차단하지 않는다.**"

TruthGate는 원고 차단이 아닌 **벡터 메모리 오염 방지**가 목적. DB 저장 후가 맞는 위치. **개선 대상 아님.**

---

## 4. Director 권한 분석 (검증 결과)

### 4-1. D1: 재시도 완화 — ⚠️ 부분적 사실

**코드 증거:**
- `director_grading.py:524-529` — `retry >= 3` 시 `base -= 10` (최저 45점)
- `director_ensemble.py:487-514` — **V75-C Contradiction Firewall**: CRITICAL/MAJOR 모순 감지 시 `score <= 44` 강제 → 재시도 완화 **무력화**

**결론:** 완화는 존재하지만 Firewall이 심각한 모순을 방어. "어떤 위반이든 통과"는 과장.

---

### 4-2. D2: 30화 제한 — ⚠️ 부분적 사실

**코드 증거:**
- `director.py:57` — `history_check_max_episodes = 30`
- `director_continuity.py:387` — 최근 30화 슬라이싱

**보완 경로:** 벡터 메모리 검색(`memory_context`)이 시맨틱 유사도 기반으로 초반 에피소드도 검색 가능. 직접 원고 텍스트 비교는 30화 제한이지만, 의미론적 보완이 존재.

---

### 4-3. D3: TruthGate blocking=False — ✅ 사실, 의도된 설계

`truth_gate.py:49` — `"blocking": False` 하드코딩. 설계 의도. **개선 대상 아님.**

---

### 4-4. D4: entity consistency 경고 시 저장 계속 — ⚠️ 부분적 사실

**실제 동작 (`director_auditor.py:514-534`):**
- `REJECT` (CRITICAL 1건+, MAJOR 3건+): 즉시 차단
- `WARNING` (MAJOR 1-2건): 경고 기록 후 계속
- `PASS`: 통과

"경고가 반환되어도 저장 계속"은 WARNING 수준에서만 사실. REJECT는 차단됨.

---

## 5. 실제 개선이 필요한 문제 (재정리)

원본 문서에서 제거된 오류 항목들을 제외하고, 실제 코드 기반으로 확인된 문제만 정리.

### 문제 A: AssetLibrary.KeyNPCs에 사망 상태 미반영 (H1 검증)

**증거:** Arc 생성 LLM에 전달되는 `assets`(AssetLibrary)에 NPC 사망 정보가 없음. StateTracker의 `npc_deaths`와 동기화 없음.

**추가 발견 — TruthGate 키 불일치:**
- TruthGate: `npc_info.get("deceased")` 체크
- StateTracker: `{"status": "dead"}` 사용
- 결과: TruthGate가 StateTracker 데이터를 받아도 사망 NPC를 감지하지 못할 수 있음

**방향:**
- A안: Arc 생성 프롬프트에 StateTracker의 `npc_deaths` 목록을 명시적 "사망 NPC 목록" 섹션으로 주입
- B안: TruthGate의 키를 `status == "dead"` 체크로 통일 (단순 버그 수정)
- B안이 즉시 실행 가능하고 리스크 낮음

---

### 문제 B: emotional_beat Chief Writer 프롬프트 누락 (E2 검증)

**증거:** `chief_writer_context.py`, `chief_writer_prompts.py`, `chief_writer.yaml` 어디에도 `emotional_beat` 없음.

**실제 흐름:** Treatment → `arc_ensemble.yaml` 프롬프트에 주입 → Arc에 반영 → Blueprint 생성에 영향. Chief Writer에는 **전달 안 됨**.

**영향:** Chief Writer가 "이 화의 감정적 정점"을 모른 채 집필. Director가 감정 비트 미흡을 감지해도 Writer에게 원인 설명 불가.

**방향:** Arc의 `emotional_beat` 또는 Blueprint 생성 시 파생된 감정 설계를 Chief Writer context에 별도 섹션으로 추가.

---

### 문제 C: 일반 Director 피드백 라운드 간 소실 (C1 검증)

**증거:** `stage4_interview_round.py:1012-1014` — `director_feedback = "\n".join(action_items)` assign으로 덮어쓰기.

**보존되는 것:** `[연속성 충돌]`, `[V67]`, `[CoVe]`, `[ToT`, `[MAD` 접두사 라인만.

**소실되는 것:** Director의 일반 개선 지시 ("긴장감", "대화 비율", "장면 속도" 등).

**방향:** 일반 피드백도 누적하되 최대 길이 제한. 예: `director_feedback = prev_feedback + "\n[R{n}] " + new_feedback`. 단, 프롬프트 토큰 예산 고려 필요.

---

### 문제 D: Blueprint 일부 필드 Chief Writer 미전달 (신규 발견)

**증거 (`chief_writer_context.py` 검증):**

Chief Writer에 전달되지 않는 Blueprint 필드:
- `ending_hook` — 독자를 다음 화로 유인하는 설계 (연속성 핵심)
- `protagonist_state` — 에피소드 시작/종료 시 주인공 상태
- `ending_state` — 에피소드 종료 시 세계 상태
- `time_flow` — 시간 흐름 설계
- `core_tension` — 핵심 긴장 요소

**영향:** Chief Writer가 "이 화를 어떻게 마무리해야 하는가"(ending_hook)를 모른 채 집필. 다음 화 연결이 Blueprint 설계와 어긋날 수 있음.

**방향:** `ending_hook`과 `protagonist_state`를 Chief Writer context에 추가. 이 두 필드가 연속성에 가장 직접적.

---

### 문제 E: 적응형 임계값 완화 (D1 검증)

**증거:** 재시도 3회 이상 시 합격 기준 -10점. Contradiction Firewall이 방어하지만 MAJOR 미만 위반은 통과 가능.

**방향 (Director 권한 강화):**
- 연속성 오류(CONTINUITY 카테고리)에 한해 완화 제외 옵션
- "CRITICAL_HOLD" 반환값 — 특정 유형 위반 시 재시도 기준 완화 비활성화

---

## 6. 개선 우선순위 (재정리)

원본 문서의 7개 아이디어에서 검증 결과를 반영한 실제 실행 목록:

| 순위 | 문제 | 방향 | 난이도 | 근거 |
|------|------|------|--------|------|
| 1 | TruthGate 키 불일치 (A 부분) | `status == "dead"` 체크 통일 | **L** | 단순 버그, 즉시 가능 |
| 2 | director_feedback 누적 (C) | assign → append + 길이 제한 | **L** | 라운드 간 맥락 보존 |
| 3 | emotional_beat 주입 (B) | Chief Writer context 섹션 추가 | **L** | 감정 비트 설계 반영 |
| 4 | ending_hook 주입 (D) | Blueprint.ending_hook → 프롬프트 | **L** | 화 마무리·연결 설계 반영 |
| 5 | Arc 생성 사망 NPC 목록 주입 (A) | StateTracker.npc_deaths → 프롬프트 명시 | **M** | 사망 NPC Arc 재등장 방지 |
| 6 | CRITICAL_HOLD 반환값 | 연속성 위반 시 기준 완화 비활성화 | **M** | Director 권한 강화 |

---

## 7. 원본 문서 대비 주요 수정 사항

| 원본 주장 | 실제 | 처리 |
|---------|------|------|
| H2: 얕은 복사 오염 | 복사 없는 원본 참조 반환 (다른 문제) | ❌ 개선 항목 제거 |
| H3: 동시 전달 모순 신호 | AssetLibrary만 전달, 문제는 H1과 동일 | ❌ 개선 항목 제거 (H1로 통합) |
| #1: Arc DB 미저장 | DB 정상 저장 확인 | ❌ 개선 항목 제거 |
| #2: NPC 3필드만 스캔 | 4개 계층 스캔 확인 | ❌ 개선 항목 제거 |
| C2: HUD 미갱신 개선 필요 | 의도된 설계 | ❌ 개선 항목 제거 |
| C3: BlockingValidator 차단 활성화 | 대원칙 준수 의도 설계 | ❌ 개선 항목 제거 |
| C5: Blocking TruthGate | 메모리 오염 방지용, 의도된 advisory | ❌ 개선 항목 제거 |
| E1: Blueprint.state_changes 누락 | state_changes는 Arc 필드 (전제 오류) | 🔁 A 문제로 재기술 |
| TruthGate 키 불일치 | 신규 발견 | 🆕 추가 |
| Blueprint.ending_hook 미전달 | 신규 발견 | 🆕 추가 |
