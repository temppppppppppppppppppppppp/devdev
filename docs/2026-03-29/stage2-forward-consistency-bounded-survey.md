# Stage 2 Forward-Consistency Bounded Survey

Date: 2026-03-29
Status: final (3-pass audited, confidence 96%)
Baseline Commit: `dae2dd2f`
Evidence Project: `projects/0_1` (arcs 6-10, investment genre)

## 1. Symptom

Director가 Arc 7-10에서 반복적으로 아이템 부활(resurrection)과 시작 상태 불일치를 감지:
- Arc 7 PWF: "제24화에서 이미 파쇄한 '2007년 코스피 주도주 분석 리포트 초안'이 제29화 소지품에 존재"
- Arc 8 PWF: "MUST HAVE 소지품 '20억 원 예치 시중은행 법인 통장' 누락"
- Arc 9 REJECT: "시작 소지품 목록에 이전 Arc에서 이월되어야 할 필수 소지품들이 다수 누락, 45화에서 누락된 소지품을 갑자기 파쇄"
- Arc 10 REJECT: Entity 명칭 불일치 + 내공 수치 State Lock 위반

## 2. Resurrection Evidence (Arc 6-9)

| Item | Destroyed | Where | Reappears | Evidence |
|------|-----------|-------|-----------|----------|
| 2007년 코스피 주도주 분석 리포트 초안 | Arc 6 Ep24 (파쇄기) | arc_006.txt status_shadow.item_consumption | Arc 9 Ep40 시작 상태 | arc_009.txt tactical_doc |
| 20억 원 예치 시중은행 법인 통장 | Arc 6 Ep24 (전액 이체) | arc_006.txt status_shadow | Arc 8 Ep34 시작 상태 | arc_008.txt tactical_doc |
| 미국 서브프라임 블룸버그 출력물 | Arc 7 Ep32 (소모) | arc_007.txt item_consumption | Arc 9 Ep40 시작 상태 | arc_009.txt tactical_doc |

패턴: 파쇄/소모된 아이템이 2-3 arc 후 시작 상태에 부활하고, 부활한 아이템을 다시 파쇄하는 이중 파괴가 발생.

## 3. State Authority 분석

Stage 2에는 아이템/상태를 담는 **5개 병렬 source**가 있으며, 단일 authority가 없음:

| Source | Location | 역할 | 문제 |
|--------|----------|------|------|
| `state_constraints.arc_end_state.equipment` | JSON metadata | Equipment Sync의 primary source | LLM이 생성 — 소모된 아이템 포함 가능 |
| `joint_docs.physical_inventory` | JSON metadata | Equipment Sync fallback + PromptBuilder primary | LLM이 생성 — 동일 문제 |
| `status_shadow.item_consumption` | JSON metadata | 소모 아이템 기록 | 현재 arc 단위만 — 누적 안 됨 |
| `tactical_doc [시작 상태]/[종료 상태]` | 텍스트 | 서사적 상태 기술 | 구조화 필드와 비동기 |
| `state_constraints.arc_start_state.equipment` | JSON metadata | Validator 입력 | LLM이 생성 — Equipment Sync로 덮어쓰지만 base가 잘못됨 |

**핵심 문제**: Equipment Sync(stage2_finalizer.py L1261-1284)가 `prev_arc.state_constraints.arc_end_state.equipment`을 authority로 사용하지만, 이 필드 자체가 LLM이 생성한 것이므로 소모된 아이템이 포함될 수 있음.

## 4. Root Cause Chain

```
1. Arc N LLM 생성 시, status_shadow.item_consumption에 "아이템 A 파쇄" 기록
2. 하지만 state_constraints.arc_end_state.equipment에는 아이템 A가 여전히 포함
   (LLM이 구조화 필드를 서사와 불일치하게 생성)
3. joint_docs.physical_inventory도 같은 불일치 (LLM 생성)
4. Equipment Sync는 arc_end_state.equipment을 "정답"으로 취급하여 다음 arc에 전달
5. 아이템 A가 다음 arc의 arc_start_state.equipment에 주입됨 (resurrection)
6. Validator는 arc_start_state 누락을 WARNING으로만 처리 (fail-close 없음)
7. 이후 arc에서 LLM이 부활한 아이템 A를 다시 파쇄 → 이중 파괴
```

보조 원인:
- `StateExtractor.extract_cumulative_state()`에 **누적 소모 ledger가 없음** — `consumed_or_lost`는 현재 arc 단위만
- `cannot_acquire_again` forbidden list는 **소모된 아이템이 아닌 현재 소지품**만 포함
- `stage2_finalizer.py L1125`: inventory 계승 로직이 `curr_inventory`가 이미 채워져 있으면 **skip** — LLM이 잘못 채운 inventory를 교정 못 함

## 5. Validation Gap 분석

| 검증 | 파일:라인 | 동작 | 위험 |
|------|----------|------|------|
| 필수 필드 누락 | arc_draft_validator.py:209-211 | WARNING (penalty +10) | **No fail-close**: arc_start_state 없어도 valid=True |
| 위치 연속성 | arc_draft_validator.py:286-311 | WARNING (penalty +10) | 이동 장면 있으면 pass |
| 부상 연속성 | arc_draft_validator.py:313-342 | WARNING (penalty +5) | 회복 장면 있으면 pass |
| 중복 획득 | arc_draft_validator.py:223-284 | CRITICAL | state_constraints.items_acquired 비어있으면 check 안 됨 |
| 소지품 연속성 | **없음** | **없음** | **Equipment 연속성 검증 자체가 없음** |
| 소모 아이템 부활 | **없음** | **없음** | **Destructive transition check 없음** |

유일한 REJECT 조건: 사망 NPC 등장 (arc_draft_validator.py:185).

## 6. PWF/PATCH 증폭 경로

PASS_WITH_FIX가 잘못된 truth를 증폭하는 메커니즘:

1. Director가 부활 아이템을 발견하여 PWF 판정
2. `_inplace_patch_arc()` (four_phase_arc_generator.py:619-684)가 원본 arc를 수정
3. 패치는 **prev_arcs의 end state에 접근하지만 강제 주입하지 않음** (L915-925: 위치만 강제)
4. 패치가 서사 텍스트는 수정하지만 구조화 필드(arc_end_state.equipment)를 교정하지 않을 수 있음
5. Equipment Sync가 패치 후 실행되더라도, base가 잘못된 arc_end_state면 다시 오염

## 7. Files Investigated

| File | Purpose | Key Lines |
|------|---------|-----------|
| `modules/core/stage2_finalizer.py` | Equipment Sync + inventory 계승 | L1125-1169 (conditional inheritance), L1261-1284 (Equipment Sync) |
| `modules/domain/agents/arc_draft_validator.py` | Arc 검증 | L185 (reject=NPC만), L209-211 (필수필드 WARNING), L286-342 (연속성 WARNING) |
| `modules/domain/agents/state_extractor.py` | 상태 추출 | L281-399 (cumulative — no consumed ledger), L614-618 (consumed_or_lost current arc only) |
| `modules/core/prompt_builder.py` | 프롬프트 주입 | L634-641 (fallback: joint_docs), L673-695 (필수 계승) |
| `modules/domain/agents/four_phase_arc_generator.py` | PWF patch | L619-684 (inplace), L915-925 (location only) |
| `modules/domain/agents/analyst.py` | Arc 생성 | (LLM이 state_constraints 생성) |
