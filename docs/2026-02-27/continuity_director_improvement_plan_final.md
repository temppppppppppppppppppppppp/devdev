# 연속성·모순 방지 및 Director 권한 강화 계획 — 최종본

> 작성일: 2026-02-27
> 감리: OPUS TF 3라운드 + 2차 수정 후 재감리 (R1: 4에이전트 / R2: 2에이전트 / R3: 1에이전트 / 재감리: 2에이전트)
> 기준 코드: 현재 워킹트리 (HEAD 대비 미커밋 변경 포함)

---

## 감리 총평

| 구분 | 건수 | 내용 |
|------|------|------|
| 1차 수정으로 해결됨 | 7건 | 투자물 레버리지 검증(부분), D-2 롤백, next 루프, state_updates, deadcode, re.DOTALL, TruthGate 접근자 |
| 2차 수정으로 해결됨 | 5건 | 투자물 파이프라인 완결, stage2_finalizer 조건 단순화, ContinuityValidator 로깅, HUD dead branch, 타입 힌트 |
| 의도된 설계 (개선 불필요) | 4건 | HUD 재시도 중 미갱신, BlockingValidator advisory, TruthGate advisory, Contradiction Firewall 완화 |
| 원본 초안 오류 (실제 문제 아님) | 4건 | Arc DB 미저장, NPC 로스터 3필드, HUD 얕은복사, 동시 전달 모순신호 |
| **여전히 미해결** | **4건** | TruthGate 키불일치, emotional_beat, director_feedback, ending_hook |
| 신규 발견 (이번 감리) | 2건 | director_prompts.py dead code, npc_registry 테스트 커버리지 갭 |

---

## 1. 이번 커밋으로 해결된 항목

### ✅ 투자물 레버리지 검증 시스템 (1차 수정)

**구성:**
- `chief_writer.yaml`: `WRITING_GUIDELINES_INVESTMENT_ONLY` — 레버리지 공식 집필 규칙 주입
- `director.yaml`: 수학적 정확성 항목에 레버리지 공식 + 자본금 정합 추가
- `investment_guard.py`: `validate_leverage_return()` — 진입가·매도가·레버리지·수익률 정합 검증
- `chief_writer_context.py`: `genre_code == "investment"` 조건 분기 및 `_investment_guidelines` 변수 선언

**상태 (1차):** YAML 키·Director 검증·InvestmentGuard까지 구성됨. Python accessor 함수 미존재로 Chief Writer 주입 파이프라인 미완성.

**일관성 확인:** 4개 위치에서 동일 공식(`계좌 수익률 = 기초자산 변동폭 × 레버리지 배수`). YAML이 SSOT, Python 상수(director_prompts.py)는 dead code.

**호출 경로:** `run_deep_validation()` → `DirectorQualityAuditor._run_genre_specific_validation()` (Director 심사 단계에서만 실행, Chief Writer 집필 단계에서는 미실행).

---

### ✅ D-2 롤백 누락 수정 (`db_manager.py`)

`reset_after()` 내 `vec_episodes`, `foreshadow` DELETE가 BEGIN~commit 트랜잭션 내부에 추가됨. `_vec_available` 가드 + try/except 방어 코드 포함.

**이전 문제:** 롤백 후 재생성 시 이전 벡터/복선이 남아 메모리 오염 및 복선 상태 불일치 발생 가능.

**경미한 미반영:** `get_rollback_impact()` 미리보기에 vec_episodes·foreshadow 건수 미포함. UX 이슈, 기능 무관.

---

### ✅ stage2 "next" action 무한루프 수정 (`stage2_orchestrator.py`)

`_fin["action"] == "next"` 시 `break` 추가. 이전에는 Director 최종 REJECT 후에도 while 루프가 `attempt += 1`로 계속 돌았음.

---

### ✅ director_ensemble state_updates 버그 수정

분량 미달 REJECT 시 `"state_updates": {}` → `candidates[best_idx].get("state_updates", {})`. Chief Writer가 생성한 NPC 사망·무공 습득 등 상태 변경이 분량 미달 경로에서 유실되던 문제 수정.

---

### ✅ consistency_validator 데드코드 제거

`len(unjustifiable) > 0` (결과를 사용하지 않는 단독 표현식) 제거. 순수 no-op. `unjustifiable`는 L258, L254, L265에서 여전히 정상 사용.

---

### ✅ chief_writer_quality re.DOTALL 수정

NPC 관계 불일치 감지 패턴에 `re.DOTALL` 추가. 이전에는 `.`이 개행을 매칭하지 못해 단락 경계를 넘는 NPC-키워드 공출현을 감지하지 못했음.

---

### ✅ TruthGate 접근자 연결 (`world_state.py`)

4개 접근자(`get_deceased_npcs`, `get_owned_items`, `get_destroyed_locations`, `get_known_skills`) 추가. TruthGate 내부에서 `hasattr` 가드로 모두 호출됨. `stage4_post_processor.py`가 `world_state`를 TruthGate에 주입하는 경로도 확인.

`world_state=None` 시 각 검사 메서드가 안전하게 스킵하는 구조.

---

---

## 1-B. 2차 수정으로 해결된 항목

### ✅ 투자물 Chief Writer 파이프라인 완결 (`chief_writer_prompts.py` + `chief_writer_context.py`)

**추가 내용:**
- `chief_writer_prompts.py`: `get_writing_guidelines_investment_only()` 함수 추가 — `_load_prompt("WRITING_GUIDELINES_INVESTMENT_ONLY", _FALLBACK_EMPTY)` 로 YAML 로드
- `chief_writer_context.py`: import 섹션에 `get_writing_guidelines_investment_only` 추가 + 주입 코드 완성

**end-to-end 검증 결과 (OPUS 감리):** YAML → `get_writing_guidelines_investment_only()` → import → `genre_code == "investment"` 조건 분기 → `writing_guidelines=get_writing_guidelines_section() + _investment_guidelines` → `build_chief_writer_main_prompt()` f-string 삽입까지 단절 없이 연결 확인. 5개 항목 전부 CORRECT.

**이전 1차 수정의 불완전성:** 1차에서 context.py에 주입 로직은 추가했으나 prompts.py에 accessor 함수가 없어 `ImportError` 상태였음. 2차에서 함수 정의로 완결.

---

### ✅ `stage2_finalizer.py` 조건 단순화

`if not curr_inventory or curr_inventory == [] or curr_inventory == "[]":` → `if not curr_inventory:`

**안전성 (OPUS 감리):** 이 조건 도달 전에 라인 277~278의 정규화 로직이 `"[]"` 문자열을 빈 리스트 `[]`로 명시 변환함. 라인 281 도달 시점에 `str` 타입 잔존 불가. `or curr_inventory == []`(not []는 True라 이미 포함)와 `or curr_inventory == "[]"`(정규화 후 불가) 모두 dead condition. 동치 변환 확인. **판정: SAFE.**

참고: 라인 296의 `prev_inventory != [] and prev_inventory != "[]"` 도 동일 패턴이나 이번 변경 범위 밖.

---

### ✅ `continuity_validator.py` silent except → 로깅

```python
# 이전
except Exception:
    return []

# 이후
except Exception:
    logging.warning("[CV] 좌절-보상 태그 조회 실패", exc_info=True)
    return []
```

`import logging` L18 존재 확인. advisory 기능(`check_frustration_streak`) 실패 시 스택 트레이스 포함 경고 로그. 기능 동작은 동일(빈 리스트 반환). **참고:** advisory 실패에 `WARNING + exc_info=True`는 약간 과하나 매 에피소드 1회 호출이므로 로그 폭증 위험 없음. **판정: CORRECT.**

---

### ✅ `chief_writer_context.py` HUD dead branch 제거

`latest = hud_history[-1]["hud"] if hud_history else {}` → `latest = hud_history[-1]["hud"]`

**근거:** 라인 779~780에 `if not hud_history: return {"has_anomalies": False, ...}` guard clause 존재. 라인 782 도달 시점에 `hud_history` 반드시 비어있지 않음. `else {}` 분기는 실행 불가능한 dead code. **판정: CORRECT.**

---

### ✅ `stage0/__init__.py` 타입 힌트 수정

`run_reverse_engineering_flow()` 반환 타입: `tuple[dict, list, StyleGuide]` → `tuple[dict, list, StyleGuide | None]`

style 추출 실패 시 `None`을 반환하는 실제 동작과 타입 힌트 일치. 기능 변화 없음.

---

## 2. 의도된 설계 (개선 불필요)

| 항목 | 이유 |
|------|------|
| HUD 재시도 중 미갱신 | 미확정 원고 state_updates로 HUD 변경하면 REJECT 후 상태 오염 발생. PASS 후 갱신이 정확한 설계. |
| BlockingValidator advisory | CLAUDE.md 대원칙 1번("Python은 수집만, 판단은 LLM이") 명시적 이행. L499 주석 `[V70.1]`. |
| TruthGate advisory-only | 목적이 벡터 메모리 오염 방지이며 원고 차단이 아님. docstring에 "Advisory 모드이므로 저장을 차단하지 않는다" 명시. |
| Contradiction Firewall 완화 | `base -= 10`(재시도 3회+)이 있으나, V75-C Firewall이 CRITICAL/MAJOR 모순 시 score≤44 강제로 방어. 실제 무력화되지 않음. |

---

## 3. 미해결 문제 (우선순위 순)

### 🔴 문제 A: TruthGate npc_registry 키 불일치 (P1)

**현상:** `truth_gate.py:70` — `info.get("deceased")` 체크. StateTracker는 `{"status": "dead"}` 사용. `"deceased"` 키를 쓰는 코드가 코드베이스 전체에 없음.

**실제 영향:**
- world_state 정상 초기화 시: `get_deceased_npcs()` 경로가 보완하여 사망 NPC 감지 동작
- world_state=None 시 (초기화 실패 비차단 경로): npc_registry만으로 동작 → 사망 NPC 감지 **완전 실패**
- world_state 초기화 실패 조건: `main_a.py:3239-3241` except 블록, 비차단 설계로 `self.world_state = None`

**테스트 갭:** `test_truth_gate.py`의 npc_registry 테스트 3건 모두 `{"deceased": True}` 구조 사용. 실제 StateTracker 구조 `{"status": "dead"}`로 테스트하는 케이스 0건.

**방향:**
- `truth_gate.py:70` — `info.get("deceased")` → `info.get("status") == "dead" or info.get("deceased")` 로 수정 (하위 호환)
- `test_truth_gate.py` — `{"status": "dead", "death_arc": 3}` 구조 테스트 케이스 추가

---

### 🟡 문제 B: emotional_beat Chief Writer 미전달

**현상:** Treatment 블록의 `emotional_beat` 필드가 `chief_writer_context.py`, `chief_writer_prompts.py`, `chief_writer.yaml` 어디에도 없음. Treatment → Arc 생성 → Blueprint 생성에는 영향을 주지만, Chief Writer 프롬프트에는 미전달.

**영향:** Chief Writer가 "이 화의 감정적 정점"을 모른 채 집필. Director가 감정 비트 미흡을 REJECT해도 Writer가 설계 의도를 명시적으로 참조하지 못함.

**방향:** Arc 또는 Blueprint에서 파생된 `emotional_beat`를 `prepare_episode_context()` → `build_common_context()` 경로로 추가 주입.

---

### 🟡 문제 C: director_feedback 라운드 간 일반 지시사항 소실

**현상:** `stage4_interview_round.py:1012` — `director_feedback = "\n".join(action_items)` (assign). 매 REJECT 시 Director 일반 피드백이 교체됨.

**보존되는 것:** `[연속성 충돌]`, `[V67]`, `[CoVe]`, `[ToT`, `[MAD` 접두사 라인만 추출-복원.

**소실되는 것:** Director의 일반 개선 지시("긴장감을 높여라", "대화 비율 줄여라" 등).

**라운드 내 누적:** ToT, MAD, Quality Gate, adaptive_manager 결과는 `+=`로 같은 라운드 내에서 누적됨. 라운드 간 누적은 없음.

**방향:** `director_feedback = prev_system_lines + f"\n[R{n}] " + new_feedback` 형태로 라운드 번호와 함께 누적. 최대 길이 제한 (토큰 예산) 필요.

---

### 🟡 문제 D: ending_hook Blueprint→Chief Writer 미전달

**현상:** `ensemble.yaml:L293-294` — Blueprint 스키마에 `ending_hook` ("다음 화 연결 훅") 필드 존재. `stage4_post_processor.py:L343`에서 `blueprint.get("ending_hook", "")` 사용 (chain_link 저장용).

**그러나** `chief_writer_context.py`가 Blueprint에서 추출하는 필드는 `scene_breakdown`과 `integrated_scenario`뿐. `ending_hook`을 Chief Writer 프롬프트에 전달하는 코드 없음.

**결과:** 이전 화의 chain_link(= 이전 화 ending_hook 파생)는 Chief Writer에게 전달되지만, **현재 화 Blueprint의 ending_hook** — "이 화를 어떻게 마무리해야 하는가" — 는 전달되지 않음.

**방향:** `prepare_episode_context()` → `build_common_context()`에 `blueprint.get("ending_hook")` 주입 섹션 추가.

---

## 4. 신규 발견 (이번 감리)

### 🔵 director_prompts.py 완전한 dead code

**확인:** `PromptLoader.load()`에 fallback 파라미터 없음. 모든 Director 프롬프트 사용처가 YAML에서 직접 로드. `director_prompts.py`의 상수는 import + 재할당만 되고 실제 프롬프트 생성에 사용되지 않음.

| 상수 | import 여부 | 실제 사용 |
|------|-----------|---------|
| ENSEMBLE_SELECTION_PROMPT | director.py (재할당만) | YAML 로드 |
| MANUSCRIPT_HISTORY_CONFLICT_PROMPT | director.py (재할당만) | YAML 로드 |
| STRATEGIC_AUDIT_PROMPT_V30 | import 없음 | YAML 로드 |
| DIRECTOR_AUDIT_PROMPT_V30 | import 없음 | YAML 로드 |

**향후 정리 대상:** `director_prompts.py` 파일 삭제 + `director.py` L10-11 import문 + L14, L16, L248 재할당 제거.

---

### 🔵 소도구/의상 물리 상태 추적 추가 (신규 긍정 변화)

`chief_writer_context.py`의 `_generate_episode_digest()` — 이전 원고의 의상 배치(수트 등받이에 걸침)·트레이딩 단말기 상태를 정규식으로 추출하여 digest에 포함. 소도구 연속성을 간접 보조. 이전 화 digest 경로이므로 현재 화 집필 지시가 아닌 context 보강.

---

## 5. 최종 우선순위 매트릭스

| 순위 | 항목 | 난이도 | 효과 | 비고 |
|------|------|--------|------|------|
| 1 | TruthGate `status: "dead"` 키 수정 | **L** | npc_registry 경로 사망 감지 복구 | 1줄 수정 + 테스트 추가 |
| 2 | director_feedback 라운드 누적 | **L** | 재시도 맥락 보존 | assign → append + 길이 제한 |
| 3 | ending_hook Chief Writer 주입 | **L** | 화 마무리 설계 반영 | blueprint 필드 추출 1개 추가 |
| 4 | emotional_beat Chief Writer 주입 | **L** | 감정 비트 설계 반영 | context 섹션 1개 추가 |
| 5 | director_prompts.py 정리 | **L** | dead code 제거, 코드 위생 | 파일 삭제 + import 4줄 제거 |
| 6 | get_rollback_impact() 미리보기 | **L** | UX 정확성 | vec_episodes·foreshadow 건수 추가 |

---

## 6. 이전 문서 수정 이력

| 원본/이전 버전 주장 | 최종 판정 | 근거 |
|------------------|---------|------|
| H2: 얕은복사 오염 | ❌ 오류 제거 | EpisodeState 얕은복사는 단순 타입 필드라 무해. `pro_root`는 복사 없는 원본 참조이나 실제 오염 경로 미확인. |
| H3: 동시 전달 모순신호 | ❌ 오류 제거 | AssetLibrary만 Arc 생성에 전달. StateTracker는 Validator(Phase 3)에만. |
| #1: Arc DB 미저장 | ❌ 오류 제거 | `save_v20_anchor("arcs")` → anchors 테이블 정상 저장. |
| #2: NPC 3필드만 스캔 | ❌ 오류 제거 | 4계층 스캔 확인 (arc state_changes + 씬별 npcs + Blueprint 최상위 key_npcs 등). |
| C2/C3/C5: 의도된 설계 제안 | ❌ 개선 불필요 | 대원칙 준수, PASS 후 HUD 갱신 의도, TruthGate advisory 의도. |
| TruthGate 키 불일치 | ⚠️ 상태 업데이트 | world_state 접근자 연결 완료. npc_registry 경로 키 불일치는 여전히 존재 (미수정). |
| ending_hook 미전달 | ⚠️ 상태 업데이트 | Blueprint 스키마에 필드 존재 확인. post_processor는 사용. Chief Writer 미전달은 여전히 사실. |
| E1: Blueprint.state_changes | 🔁 전제 오류 제거 | state_changes는 Arc 필드, Blueprint 필드가 아님. |
| 신규: director_prompts.py dead code | 🆕 추가 | PromptLoader fallback 없음. 파일 전체 dead code 확인. |
| 신규: npc_registry 테스트 갭 | 🆕 추가 | `{"status": "dead"}` 구조 테스트 0건 확인. |
| 투자물 CW 파이프라인 (1차 부분 완료) | ✅ 2차에서 완결 | chief_writer_prompts.py accessor 추가로 ImportError 해소, end-to-end 연결 확인. |
| stage2_finalizer.py 조건 "[]" | ✅ 2차에서 단순화 | 정규화 후 str 잔존 불가 확인. 동치 변환. SAFE. |
| continuity_validator.py silent except | ✅ 2차에서 로깅 추가 | Debt Audit 패턴 해소. WARNING+exc_info=True 약간 과하나 기능 무해. |
| chief_writer_context.py HUD dead branch | ✅ 2차에서 제거 | guard clause(L779) 확인. dead code 제거 적절. |
| stage0/__init__.py StyleGuide | ✅ 2차에서 타입 수정 | StyleGuide\|None으로 실제 반환 타입 일치. |
