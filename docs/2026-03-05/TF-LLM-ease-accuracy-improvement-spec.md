# TF-LLM: 파이프라인 LLM 작업 용이성 + 정확도 개선 명세

> 작성일: 2026-03-05
> 기준 커밋: `02b458a` (Log-Phase2)
> 테스트 기준: 3,348 passed
> 감리: 3회 예정

---

## 목차

1. [현황 진단](#1-현황-진단)
2. [TF-A: 프롬프트 중복 제거 + 계층화](#tf-a)
3. [TF-B: Director 의사결정 부하 경감](#tf-b)
4. [TF-C: 스키마-프롬프트-규칙 3중 정합](#tf-c)
5. [TF-D: Advisory 우선순위 시각화](#tf-d)
6. [TF-E: Chief Writer 규칙 톤 조절](#tf-e)
7. [TF-F: 컨텍스트 예산 제어](#tf-f)
8. [TF-G: Self-Critique 루프 구조 개선](#tf-g)
9. [TF-H: JSON 파싱 실패 복구 강화](#tf-h)
10. [TF-I: 피드백 전달 경로 명확화](#tf-i)
11. [우선순위 + 구현 순서](#우선순위)
12. [코덱스 구현 오더](#codex-orders)
13. [감리 기록](#감리-기록)

---

## 1. 현황 진단

### 1.1 LLM 역할별 부하 현황

| LLM 역할 | 동시 판단 항목 | 프롬프트 크기 | 핵심 문제 |
|----------|-------------|------------|----------|
| **Director** (심사) | ~20개 이진 판단 (selected3+verdict3+fix_scope3+체크리스트10+NC응답N건) + 연속값(score,breakdown5개) | 72-79KB | 의사결정 과부하 |
| **Chief Writer** (집필) | 24개 규칙 + 8개 컨텍스트 섹션 | 27-45KB | 규칙 공포감 |
| **Analyst** (Arc설계) | ARC_DESIGN 8 required + state_constraints 4 nested | 15-25KB | 스키마 복잡도 |

### 1.2 핵심 문제 3가지

1. **프롬프트 중복**: director.yaml에서 모순 검사 9개 항목이 2곳에 동일 반복 (~15K 토큰 낭비)
2. **스키마-지시 불일치**: consistency_checklist가 스키마에서 optional인데 프롬프트에서 "반드시 입력" 지시
3. **Python 자동 감점 vs Director 주권**: NC-1 AGREE 시 -8점 자동 감점 → 성실 응답에 대한 역인센티브

### 1.3 LLM 응답 후처리 체인 (현재)

```
score = _safe_int(result.get("score", 50), 50)
  ↓
[NC-3B] score_breakdown 합산 검증 → breakdown 우선 교정
  ↓
v60_97_swapped → score=50 강제
  ↓
[NC-1 SCM] 단일후보 score≥95 → min(score,90)
  ↓
[V75-C] Contradiction Firewall → CRITICAL/MAJOR 강제 REJECT
  ↓
[NC-1] numeric_consistency_review → AGREE마다 -8점
  ↓
[NC-3] consistency_checklist → ISSUE 3건+ → pw=3
  ↓
QualityGate → score<90+PASS → REJECT (PASS_WITH_FIX bypass)
```

**6단계 점수 보정**이 순차 적용 → LLM이 출력한 score와 최종 score가 크게 괴리될 수 있음.

---

## TF-A: 프롬프트 중복 제거 + 계층화 {#tf-a}

### 문제

`director.yaml`의 `ENSEMBLE_STABLE_CONTEXT`와 `ENSEMBLE_SELECTION_PROMPT`에서 **동일한 모순 검사 9개 항목이 정확히 2회 반복**됨.

- 1차: STABLE_CONTEXT L61-99 (~100줄)
- 2차: SELECTION_PROMPT L345-383 (~100줄)

ENSEMBLE_SELECTION_PROMPT는 `{stable_context}` 플레이스홀더로 STABLE_CONTEXT를 포함하므로, **결과적으로 Director는 동일 지시를 2번 읽음**.

또한 `[TF-27] 100점 지향 원칙`이 6곳에서 반복, `[I-10] 점진적 감점 규칙`이 6곳에서 반복.

### 제안

| 항목 | 현재 | 개선안 |
|------|------|--------|
| 모순검사 9항 | STABLE + SELECTION 양쪽 | STABLE에만 배치, SELECTION에서 "위 검사 기준을 적용하세요" 1줄 참조 |
| 100점 지향 | 6곳 반복 | STABLE에 1회만, 나머지는 삭제 |
| I-10 감점 규칙 | 6곳 반복 | STABLE에 1회만, score_breakdown 출력 형식 직전에 요약 1줄 |

### 예상 효과

- **토큰 절감**: ~5,000-8,000자 (약 1,500-2,000토큰)
- **집중도**: 동일 지시 반복에 의한 "읽기 피로" 해소
- **위험**: 낮음 — STABLE은 캐시되므로 항상 포함됨

### 변경 파일

- `config/prompts/director.yaml` — ENSEMBLE_SELECTION_PROMPT, STRATEGIC_AUDIT_PROMPT_V30, DIRECTOR_AUDIT_PROMPT_V30에서 중복 블록 제거

---

## TF-B: Director 의사결정 부하 경감 {#tf-b}

### 문제

Director `select_and_judge_ensemble()`에서 **1회 호출에 ~20개 이진 판단 + 연속값**:
- 모순 체크 5종
- 점수 가중치 4종 (continuity 40%, blueprint 35%, quality 15%, length 10%)
- verdict 3종 (PASS/PASS_WITH_FIX/REJECT)
- fix_scope 3종 (inplace/partial/full)
- consistency_checklist 10종 (OK/ISSUE)
- numeric_consistency_review N건 (AGREE/DISMISS)
- contradiction 목록 (severity + type + description 각각)

**의사결정 경우의 수**: 이진 판단만 2^20 = 1M+ (+ score 연속값, NC 가변 건수) → temperature=0.1이어도 첫 몇 토큰 오류 시 전체 JSON 붕괴

### 제안

**Phase 1: consistency_checklist를 "요약 판정"으로 전환**

현재: 10개 카테고리를 개별 OK/ISSUE로 응답
→ 개선: `"consistency_issues": ["arithmetic: 레버리지 40.6% 오류", "scene_overlap: 3화와 동일 구조"]` (이슈가 있는 항목만 배열로)

효과: 경우의 수 2^10=1024 → 가변 배열 (보통 0-3건) → 응답 부담 대폭 경감

**Phase 2: numeric_consistency_review 응답 형식 단순화**

현재: 각 항목별 `{"verdict": "AGREE", "reason": "..."}`
→ 개선: `"nc_review_agrees": [1, 3]` (AGREE한 항목 인덱스만) + `"nc_review_note": "자본금 38억 확인"`

효과: 깊은 nested JSON 제거 → 파싱 실패율 감소

### 예상 효과

- **의사결정 항목**: ~20개 이진 → 10-12개 (경우의 수 99%+ 감소)
- **JSON 파싱 실패율**: 추정 -30% (nested 깊이 감소)
- **위험**: 중간 — 기존 NC-1/NC-3 Python 파싱 로직 수정 필요

### 변경 파일

- `config/prompts/director.yaml` — NC-3 응답 형식 변경
- `modules/domain/agents/director_ensemble.py` — NC-1/NC-3 파싱 로직 대응
- `modules/core/response_schemas.py` — consistency_checklist 스키마 변경
- `tests/test_nc3_checklist.py` — 테스트 대응

---

## TF-C: 스키마-프롬프트-규칙 3중 정합 {#tf-c}

### 문제

| 필드 | 스키마 | 프롬프트 | Python 규칙 | 불일치 |
|------|--------|---------|------------|--------|
| `consistency_checklist` | optional | "반드시 입력" | 미응답→감점 없음 | 스키마=optional ↔ 프롬프트=필수 |
| `numeric_consistency_review` | optional | advisory로 주입 (필수처럼 보임) | 미응답→pw 10→5 | 스키마=optional ↔ Python=감점 |
| `fix_scope_reasoning` | required | "수정 근거 작성" | 누락→빈문자열 | Python이 required 무시 |
| `state_changes` | optional | 프롬프트에서 hint | Python fallback이 자동 채움 | 문제 없으나 혼란 소지 |

### 제안

**원칙: "스키마가 optional이면 Python도 감점 없이 처리"**

1. `consistency_checklist` — 프롬프트에서 "반드시"→"가능하면 작성하세요. 미작성 시 별도 감점 없음" 변경
2. `numeric_consistency_review` — 미응답 시 pw 감점(10→5) 제거. 대신 "Python advisory를 참고하여 contradiction 점수에 반영하세요" 지시로 변경 (Director 주권 존중)
3. `fix_scope_reasoning` — 스키마에서 optional로 변경 (Python이 이미 빈문자열 허용)

### 대원칙 정합성 (감리 2차 반영)

- **대원칙 1 (판단은 LLM이)**: NC-1 AGREE→-8점 자동감점은 해석이 갈림 — "Director 판단을 Python이 실행"으로 볼 수도 있으나, Director가 AGREE 시 기계적 -8점은 유연성 부족. → **Python은 "상한 제안"만 하고, Director가 continuity_contradiction에 직접 반영**하도록 유도
- **대원칙 3 (Director 주권)**: Python이 Director 응답 유무에 따라 차등 감점 (응답→감점, 미응답→무시) → 역인센티브 구조 → **차등 제거 또는 동일화**
- **구현 난제**: Director가 score_breakdown을 이미 직접 설정하므로, "NC-1 기반 재계산"을 추가 지시하면 과중. → NC-1 advisory를 "참고 정보"로 프롬프트에 명시하고, Director가 이를 고려하여 continuity_contradiction을 스스로 설정하도록 함

### 예상 효과

- **대원칙 준수**: 역인센티브 해소 (성실 응답 = 감점 구조 제거)
- **Director 인센티브**: "성실하게 응답해도 감점" → "Advisory를 참고하여 자율 판단" 전환
- **위험**: 중간 — NC-1 AGREE 자동감점 제거 시 일부 모순 누수 가능. 다만 Contradiction Firewall이 CRITICAL/MAJOR는 별도 처리하므로 실제 위험은 제한적. **Phase 1에서 모니터링 후 Phase 2에서 완전 제거 권장**

### 변경 파일

- `config/prompts/director.yaml` — NC-1/NC-3 지시 톤 조절
- `modules/domain/agents/director_ensemble.py` — NC-1 AGREE 자동감점 로직 제거, NC-3 미응답 감점 제거
- `modules/core/response_schemas.py` — fix_scope_reasoning optional 변경
- `tests/` — 관련 테스트 대응

---

## TF-D: Advisory 우선순위 시각화 {#tf-d}

### 문제

Director에게 전달되는 advisory 8개가 **동일한 시각적 가중치**로 나열됨:
```
[TruthGate Advisory] 사망 NPC 부활 감지...      ← CRITICAL
[NpcDriftAdvisor] 김기준 직함 변경 감지...        ← MAJOR
[NumericConsistencyChecker] 자본금 불일치 2건...  ← VARIES
```

CRITICAL(TruthGate 사망NPC)과 MAJOR(NpcDrift 직함변경)의 시급성이 같아 보임.

### 제안

**Advisory 헤더에 우선순위 태그 추가**:
```
🚨 [CRITICAL — TruthGate] 사망 NPC 부활 감지...
⚠️ [MAJOR — NpcDriftAdvisor] 김기준 직함 변경...
ℹ️ [INFO — NumericConsistencyChecker] 자본금 불일치...
```

**3-tier 분류**:
| Tier | Advisory | 조건 |
|------|----------|------|
| CRITICAL | TruthGate (사망NPC, 세계법칙) | 경고 존재 시 |
| MAJOR | NpcDrift, FlashbackVerifier, InfoParadox, RelDrift | 경고 존재 시 |
| INFO | NumericDrift, LongTermRep, NumericConsistency, SceneSimilarity, Timeline | 항상 |

**0건일 때**: "✅ [TruthGate] 이상 없음" (1줄로 축약, Director 안심)

### 예상 효과

- **Director 집중도**: CRITICAL 즉시 인지 → 핵심 모순 처리 시간 단축
- **advisory 0건 시**: "✅ 이상 없음" 1줄 vs 현재 "[TruthGate Advisory] 경고 0건" 형태
- **토큰 절감**: 경고 0건인 advisory를 1줄로 축약 → 평균 -300~500자
- **위험**: 매우 낮음 — 표시 형식만 변경, 로직 무변경

### 변경 파일

- `modules/core/stage4_interview_round.py` — advisory 헤더 포맷 변경
- 각 advisory 모듈 (`truth_gate.py`, `npc_drift_advisor.py` 등) — 반환 형식에 severity 포함

---

## TF-E: Chief Writer 규칙 톤 조절 {#tf-e}

### 문제

`chief_writer.yaml`에서 **"절대", "금지", "무조건", "필수"** 등 강압적 표현이 **과다 밀집**:

- "벽돌 문단 = 독자 이탈 1순위" (공포 유발)
- "4,999자 이하는 무조건 REJECT" (경직)
- "영문 병기 절대 금지" (과잉)
- "Markdown 절대 금지" (과잉)

LLM이 과도한 공포감을 느끼면 **자기검열 → 창작 자유도 저하 → 기계적 글쓰기** 악순환.

### 제안

**톤 다운 원칙**: "절대 금지" → "강력 권장" / "반드시" → "권장" / "무조건 REJECT" → "감점 대상"

예시:
| 현재 | 개선 |
|------|------|
| "벽돌 문단 = 독자 이탈 1순위" | "5줄 이상 연속 서술은 줄바꿈으로 끊어주세요" |
| "4,999자 이하는 무조건 REJECT" | "5,000자 이상이 기준이며, 미달 시 감점됩니다" |
| "영문 병기 절대 금지" | "영문 병기는 사용하지 마세요" |
| "Markdown 절대 금지" | "Markdown 기호(#, *, - 등)는 사용하지 마세요" |

**단, 핵심 금지사항은 유지**:
- "사망 NPC의 행동/대사 등장 금지" → 유지 (대원칙 4)
- "미습득 무공 사용 금지" → 유지 (팩트 일관성)

### 예상 효과

- **창작 자유도**: 추정 +20-30% (기계적 반복 감소)
- **규칙 준수**: 핵심 금지는 유지하므로 영향 없음
- **위험**: 낮음 — 톤만 변경, 규칙 자체는 동일

### 변경 파일

- `config/prompts/chief_writer.yaml` — COMMON_RULES_SECTION, WRITING_GUIDELINES_SECTION 톤 조절

---

## TF-F: 컨텍스트 예산 제어 {#tf-f}

### 문제

Chief Writer 1회 호출 시 프롬프트 구성:
```
기본 규칙 (chief_writer.yaml):              ~4,000자
Writer Utility Context:                     ~2,600자
Chief Writer Context (27개 파라미터 조립):    ~9,200자
SmartRetrieval Context:                     ~5,000자
Blueprint & Plans:                          ~7,000자
──────────────────────────────────────────
캐시 제외 합계:                              ~27,800자
+ prev_manuscripts_text (캐시):              ~150,000자
= 총합:                                     ~177,800자 (~45K 토큰)
```

**base_agent.py 절삭 한도가 1MB** — 사실상 절삭이 작동하지 않음 (45K 토큰 << 1MB).
하지만 프롬프트가 길수록 LLM 집중도는 선형 감소 (특히 중간 부분).

### 제안

**Phase 1: 컨텍스트 "중요도 계층" 도입**

| 계층 | 내용 | 최대 | 절삭 전략 |
|------|------|------|----------|
| L1 필수 | blueprint + 직전 1화 원문 + HUD | 10KB | 절삭 불가 |
| L2 중요 | Arc + Director 피드백 + WritingDirective | 5KB | 요약 가능 |
| L3 참고 | 이전 2-5화 원문 + NPC 관계 + style_guide | 20KB | 절삭 가능 |
| L4 보조 | anti_trope + justification + mandatory_context | 3KB | 생략 가능 |

**Phase 2: chief_writer_context.py 30개 파라미터 → 4개 데이터 객체**

```python
@dataclass
class EpisodeInput:
    ep_num: int
    blueprint: dict
    prev_manuscript: str
    hud_report: str

@dataclass
class PlanInput:
    arc_doc: str
    style_guide: str
    writing_directive: str | None
    director_feedback: str

@dataclass
class HistoryInput:
    prev_manuscripts_text: str
    world_state_summary: str
    chain_link_section: str

@dataclass
class ConstraintInput:
    genre_name: str
    purism_prompt: str
    failure_constraints: str
    dead_npcs: list
```

### 예상 효과

- **유지보수**: 파라미터 30→4, 호출자 명확도 +80%
- **LLM 집중도**: L3/L4 절삭 시 프롬프트 -30% → 중간부 집중 개선
- **위험**: Phase 2는 리팩토링 규모 큼 — 호출자 전량 수정 필요

### 변경 파일

- `modules/domain/agents/chief_writer_context.py` — dataclass 도입 + 기존 함수 래핑
- `modules/core/stage4_interview_round.py` — 호출 코드 대응
- `modules/domain/agents/chief_writer.py` — 호출 코드 대응

---

## TF-G: Self-Critique 루프 구조 개선 {#tf-g}

### 문제

`chief_writer_quality.py`의 `apply_self_critique()`:

1. **8가지 체크가 순서 의존적**: ending_hook 체크가 마지막(8번째) → rubric만 높으면 미검증 탈출 가능
2. **severity가 수량 기반만**: 1-2건 이슈 → "low" → 루프 즉시 종료 (L159) → 구조적 문제 방치
3. **mid-loop rubric 조기 종료**: round_num > 1 + rubric ≥ 3.5 → break → ending_hook 미검증 상태 탈출

```python
# 현재 문제 흐름
round 1: 이슈 2건 감지 → severity="low" → break (ending_hook 미검증!)
round 2: 도달하지 않음
```

### 제안

**ending_hook + 분량 체크를 "게이트 검사"로 분리**:

```python
# Phase 1: 게이트 검사 (self-critique 루프 전)
gate_issues = []
if not _check_ending_hook_presence(manuscript, blueprint):
    gate_issues.append("ending_hook 미포함")
if len(manuscript) < 5000:
    gate_issues.append(f"분량 부족 ({len(manuscript)}자)")

# gate_issues가 있으면 무조건 수정 라운드 진입
if gate_issues:
    # 수정 프롬프트에 gate_issues 명시
    ...

# Phase 2: 기존 self-critique 루프 (8개 체크)
for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
    ...
```

효과: ending_hook/분량 누락이 severity="low"로 무시되는 경로 차단

### 예상 효과

- **ending_hook 준수율**: 추정 +30% (현재 누락 가능 경로 차단)
- **분량 미달 방지**: 게이트에서 사전 차단
- **위험**: 낮음 — 기존 루프 전에 검사만 추가, 루프 자체 미변경

### 변경 파일

- `modules/domain/agents/chief_writer_quality.py` — 게이트 검사 추가

---

## TF-H: JSON 파싱 실패 복구 강화 {#tf-h}

### 문제

`base_agent.py`의 `_extract_json_robust()` 5단계 폴백:

1. json.loads() → 2. ast.literal_eval() → 3. Hard Repair (괄호 폐쇄) → 4. Regex 추출 → 5. 원문 반환

**단계 4-5에서 정보 손실 심각**:
- Regex가 `tactical_doc`만 추출 → 다른 필드 소실
- 원문 반환 → `{"parsing_error": True}` 래핑 → 소비자가 폴백 처리

`director_ensemble.py`에서 파싱 실패 시 **무조건 첫 번째 후보 선택** (L180-187) → Director 판단 없이 자동 결정.

### 제안

**Phase 1: 파싱 실패 시 "단순 프롬프트로 재시도" 1회**

현재는 파싱 실패 → 즉시 폴백. 대신:
```python
if not isinstance(result, dict) or result.get("parsing_error"):
    # 단순화된 프롬프트로 1회 재시도
    retry_prompt = f"""이전 응답이 유효한 JSON이 아니었습니다.
아래 형식으로만 응답하세요:
{{"selected": "A"|"B"|"C", "verdict": "PASS"|"REJECT", "score": 0-100}}"""
    retry_result = self._d.ask(retry_prompt, temperature=0.0)
    result = self._d._extract_json_robust(retry_result)
```

효과: 파싱 실패 복구율 +50% (LLM이 짧은 프롬프트에서 JSON 준수율 높음)

**Phase 2: Hard Repair에 "닫히지 않은 문자열" 감지 추가**

LLM이 JSON 내부에서 한글 큰따옴표(", ")를 사용하면 파싱 실패. 정규식으로 사전 정규화.

### 예상 효과

- **파싱 실패 복구율**: +50% (재시도) + +20% (정규화)
- **토큰 비용**: 재시도 1회 추가 → 실패 시에만 +500토큰
- **위험**: 낮음 — 기존 폴백 경로 유지, 재시도는 추가 경로

### 변경 파일

- `modules/domain/agents/director_ensemble.py` — 파싱 실패 시 재시도 로직
- `modules/domain/agents/base_agent.py` — Hard Repair 정규화 강화

---

## TF-I: 피드백 전달 경로 명확화 {#tf-i}

### 문제

`stage4_interview_round.py`에서 Director→CW 피드백 전달 경로가 복잡:

1. Director가 `feedback` 필드에 수정 지시 작성
2. `_process_verdict()`에서 `director_feedback` 문자열 추출
3. `run()` 다음 라운드에서 `director_feedback` 파라미터로 전달
4. `_build_common_writer_kwargs()`에서 **director_feedback이 사용되지 않는 경로 존재**
5. `_generate_candidates()`에서 `strategy_feedback`으로 전달 (형식 변환)
6. 최종적으로 CW 프롬프트에 주입

**경로 4에서 피드백이 누락될 수 있음**: `_build_common_writer_kwargs()`가 `director_feedback`을 받지 않는 경우, PromptWeighter `_weighted_injection`으로만 전달됨.

### 제안

**common_writer_kwargs에 director_feedback을 별도 키로 추가** (감리 2차 반영):

```python
# run() 내에서 _build_common_writer_kwargs() 호출 후 별도 키 추가
mandatory_context, _common_writer_kwargs = self._build_common_writer_kwargs(...)
_common_writer_kwargs["director_feedback"] = director_feedback  # 별도 키로 명시 전달
```

**주의**: `_build_common_writer_kwargs()` 시그니처 변경이 아닌, 호출자에서 dict에 추가.
- 호출 순서 변경 불필요 (PromptWeighter 누적 전에 실행됨)
- 기존 PromptWeighter 주입과 비충돌
- CW 메서드(generate_ensemble, inplace_patch 등)에서 `kwargs.get("director_feedback")` 접근

### 예상 효과

- **피드백 반영률**: 추정 +20% (현재 경로 혼선으로 누락 가능)
- **위험**: 낮음 — mandatory_context 앞에 prepend만

### 변경 파일

- `modules/core/stage4_interview_round.py` — `_build_common_writer_kwargs()` 수정

---

## 우선순위 + 구현 순서 {#우선순위}

### P0 (즉시, 위험 없음)

| 순서 | TF | 핵심 변경 | 예상 효과 | 변경 규모 |
|------|-----|---------|----------|----------|
| 1 | **TF-D** | Advisory 우선순위 헤더 | Director 집중도 +20% | 소 (포맷만) |
| 2 | **TF-E** | CW 규칙 톤 조절 | 창작 자유도 +20% | 소 (텍스트만) |
| 3 | **TF-A** | 프롬프트 중복 제거 | 토큰 -5K~8K | 중 (YAML 4곳) |

### P1 (1주 이내, 로직 변경)

| 순서 | TF | 핵심 변경 | 예상 효과 | 변경 규모 |
|------|-----|---------|----------|----------|
| 4 | **TF-C** | 스키마-프롬프트-규칙 정합 | 대원칙 준수 | 중 (3파일) |
| 5 | **TF-G** | Self-Critique 게이트 검사 | ending_hook +30% | 소 (1파일) |
| 6 | **TF-I** | 피드백 경로 통일 | 피드백 반영 +20% | 소 (1파일) |

### P2 (2주 이내, 구조 변경)

| 순서 | TF | 핵심 변경 | 예상 효과 | 변경 규모 |
|------|-----|---------|----------|----------|
| 7 | **TF-B** | Director 의사결정 경감 | 파싱실패 -30% | 대 (스키마+파싱) |
| 8 | **TF-H** | JSON 재시도 + 정규화 | 복구율 +50% | 중 (2파일) |

### P3 (1개월, 리팩토링)

| 순서 | TF | 핵심 변경 | 예상 효과 | 변경 규모 |
|------|-----|---------|----------|----------|
| 9 | **TF-F Phase 2** | 30파라미터→4 dataclass | 유지보수 +80% | 대 (호출자 전량) |

### P3-추가 (감리 3차 발견 — 별도 추적)

| 순서 | 항목 | 핵심 변경 | 예상 효과 | 비고 |
|------|------|---------|----------|------|
| 10 | **analyst.yaml Few-Shot 축약** | 6개 예시 → 2개 (WRONG 1 + CORRECT 1) | 토큰 -40줄 (~1,000자) | ENRICH_BLOCK_PROMPT_V30 L56-80 |
| 11 | **HUD 이상 감지 장르별 임계값** | writer_prompt_builders.py 절대값(+500) → 퍼센트 기반 + 장르별 분기 | 비무협 오탐 -50% | L118 내공 급상승 등 무협 하드코딩 |
| 12 | **MAX_CONTINUATIONS 5→3** | base_agent.py 이어쓰기 최대 횟수 감소 | 토큰 낭비 방지 (실패 시 -2회분) | 3회 = 15,000자 이상이면 충분 |

---

## 감리 기록 {#감리-기록}

### 감리 1차 — 팩트 정확성 검증 ✅

| 항목 | 결과 | 조치 |
|------|------|------|
| TF-A 중복 반복 횟수 | ✅ CORRECT | — |
| TF-B 동시 판단 수 | ❌ 27+→~20 이진 | 문서 수정 완료 |
| TF-C 스키마 optional | ✅ CORRECT | — |
| TF-G ending_hook 순서 | ✅ CORRECT | — |
| 후처리 체인 순서 | ✅ CORRECT | — |
| TF-F 파라미터 수 | ❌ 27→30 | 문서 수정 완료 |

### 감리 2차 — 대원칙 정합성 + 실현 가능성 ✅

| 항목 | 결과 | 조치 |
|------|------|------|
| TF-C NC-1 자동감점 | ⚠️ 해석 갈림 | "상한 제안" + Director 자율 판단으로 변경. 구현 난제 명시 |
| TF-A 중복 제거 | ✅ VALID | — |
| TF-B 배열 전환 | ⚠️ 하위호환 | 병행 도입 권고 추가 |
| TF-D Advisory 시각화 | ✅ VALID | 문자열 매칭 advisory 이름 기반 유지 조건 |
| TF-I 피드백 경로 | ❌ 설계 결함 | _build_common_writer_kwargs 수정 대신 common_writer_kwargs dict에 별도 키 추가로 변경 |

### 감리 3차 — P0 코덱스 실행 감리 (2026-03-05)

> Codex가 P0 3건(TF-D, TF-E, TF-A) 구현 → Opus 감리

**TF-D: Advisory 우선순위 시각화 — ✅ PASS**

| 검증 항목 | 결과 |
|-----------|------|
| 위치: L457-490, `_advisory_summary` dict 후 배치 | ✅ 정확 |
| CRITICAL: TruthGate → `[CRITICAL · TruthGate]` | ✅ |
| MAJOR: NpcDrift/RelDrift/Flashback/InfoParadox 4종 | ✅ |
| INFO: 나머지 전부 `[INFO]` 폴백 | ✅ |
| 0건 축약: `[이름] 이상 없음` 1줄 | ✅ |
| `_advisory_summary` dict (L440-456) 미변경 | ✅ |

**TF-E: Chief Writer 규칙 톤 조절 — ✅ PASS**

| 변경 | Before | After | 판정 |
|------|--------|-------|------|
| L22 줄바꿈 | 벽돌 문단 = 독자 이탈 1순위 | 5줄 이상 연속 서술은 줄바꿈으로 끊어주세요 | ✅ |
| L47 분량 | 무조건 REJECT | 감점 대상입니다 | ✅ |
| L52 영문 병기 | 절대 금지 | 사용하지 마세요 | ✅ |
| L53 Markdown | 절대 금지 | 사용하지 마세요 | ✅ |
| L51 사망NPC/미습득무공 | 절대 금지 | **유지** | ✅ 핵심 금지 |
| L66 원시인모드 현대용어 | 절대 금지 | **유지** | ✅ 핵심 금지 |

**TF-A: 프롬프트 중복 제거 — ❌ CRITICAL 오류 → 수동 복구 → NO-OP 재분류**

| 문제 | 상세 |
|------|------|
| Codex 실행 오류 | V67을 VARIABLE_PROMPT(SSOT)에서 삭제. "stable_context 참조" 블록 교체 |
| 영향 | 캐시 모드(운영 기본)에서 모순 검사 9항 **전체 소실** |
| 복구 | VARIABLE_PROMPT L61-112에 V67/I-10/TF-27 원문 전량 수동 복원 |
| **근본 원인 — 오더 설계 오류** | 오더가 "STABLE_CONTEXT L61-101이 SSOT"라고 명시했으나, **STABLE_CONTEXT에는 V67이 없음**. 실제 SSOT는 VARIABLE_PROMPT L61-112. |

**아키텍처 분석 (TF-A 재평가)**:

| 프롬프트 | 용도 | V67 필요 |
|----------|------|----------|
| STABLE_CONTEXT (L7-33) | 캐시 대상 공통 컨텍스트 | ❌ 없음 (blueprint/prev_manuscripts만) |
| VARIABLE_PROMPT (L34-291) | 캐시 모드 per-call 지시 | ✅ SSOT (L61-112) |
| SELECTION_PROMPT (L292-575) | 비캐시 fallback **단독 전송** | ✅ 필수 사본 (L345-397) |

SELECTION_PROMPT는 비캐시 경로에서 **단독 전송**됨 (`director_ensemble.py` L713-745). V67 삭제 시 비캐시 경로에서 모순 검사 규칙 소실.

**결론**: TF-A "중복 제거"는 **구조적으로 불가** (양쪽 모두 필수). 진정한 dedup은 V67을 STABLE_CONTEXT로 이동해야 하나 캐시 무효화 주기 재설계 필요 → **P2 후순위 재분류**.

**최종 상태**: 3,348 passed, YAML 파싱 OK, VARIABLE_PROMPT SSOT 복원 완료.

---

## 코덱스 구현 오더 {#codex-orders}

> **구현 순서**: P0(TF-D → TF-E → TF-A) → P1(TF-C → TF-G → TF-I) → P2(TF-B → TF-H)
> **TF-F Phase 2**와 **P3-추가 3건**은 이 오더에서 제외 (별도 스프린트).
> **테스트 기준선**: 3,348 passed (깨뜨리면 안 됨)
> **검증**: 각 TF 완료 후 `pytest tests/ -q` 전체 회귀 필수

---

### 오더 1: TF-D — Advisory 우선순위 시각화

**의존성**: 없음 (독립 실행 가능)

**변경 1: `modules/core/stage4_interview_round.py`**

`_run_advisory_chain()` (L2054) 반환값을 가공하는 블록 (L440-457)을 수정.
현재 advisory 결과물은 `_advisory_parts` 리스트에 평문 문자열로 들어옴.

advisory를 `_director_mc_parts`에 합치기 **직전** (L457 `_director_mc_parts = _advisory_parts + _director_mc_parts`) 에서:

```python
# L457 직전에 추가 — advisory 우선순위 헤더 포맷
_formatted_advisory = []
for _part in (_advisory_parts or []):
    _ps = str(_part)
    if "[TruthGate]" in _ps and "이상 없음" not in _ps:
        _formatted_advisory.append(f"🚨 [CRITICAL — TruthGate] {_ps.replace('[TruthGate Advisory]', '').replace('[TruthGate]', '').strip()}")
    elif any(tag in _ps for tag in ["[LM-B]", "[LM-D]", "[LM-E]", "[LM-F]", "NpcDrift", "RelDrift", "Flashback", "InfoParadox"]):
        _tag_name = "NpcDrift" if "[LM-B]" in _ps or "NpcDrift" in _ps else \
                    "RelDrift" if "[LM-D]" in _ps or "RelDrift" in _ps else \
                    "Flashback" if "[LM-E]" in _ps or "Flashback" in _ps else "InfoParadox"
        _formatted_advisory.append(f"⚠️ [MAJOR — {_tag_name}] {_ps.strip()}")
    elif "이상 없음" in _ps or "경고 0건" in _ps or not _ps.strip():
        # 0건 advisory → 1줄 축약
        _short_name = _ps.split("]")[0].replace("[", "").strip() if "]" in _ps else "Advisory"
        _formatted_advisory.append(f"✅ [{_short_name}] 이상 없음")
    else:
        _formatted_advisory.append(f"ℹ️ [INFO] {_ps.strip()}")
_advisory_parts = _formatted_advisory
```

**핵심 규칙**:
- TruthGate 경고 존재 시 → `🚨 [CRITICAL — TruthGate]`
- NpcDrift/RelDrift/Flashback/InfoParadox 경고 → `⚠️ [MAJOR — ...]`
- 나머지 (NumericDrift/LongTermRep/NumericConsistency 등) → `ℹ️ [INFO]`
- 경고 0건 → `✅ [...] 이상 없음` (1줄 축약)

**변경 2: 각 advisory 모듈 반환 형식은 건드리지 않음** — 포맷팅은 소비자(`stage4_interview_round.py`)에서만 처리.

**테스트**:
- `python -m py_compile modules/core/stage4_interview_round.py`
- `pytest tests/test_pipeline_wiring.py -v` (advisory 배선 테스트)
- `pytest tests/ -q` (전체 회귀)

**수용 기준**:
- [x] advisory 헤더에 CRITICAL/MAJOR/INFO 태그 포함
- [x] 0건 advisory → 1줄 축약
- [x] 기존 `_advisory_summary` 딕셔너리 로직 (L440-456) 영향 없음
- [x] 테스트 3,348+ passed

---

### 오더 2: TF-E — Chief Writer 규칙 톤 조절

**의존성**: 없음 (독립 실행 가능)

**변경: `config/prompts/chief_writer.yaml`**

COMMON_RULES_SECTION과 WRITING_GUIDELINES_SECTION에서 아래 표현 치환:

| 현재 | → 변경 |
|------|--------|
| `절대 금지` | `사용하지 마세요` |
| `무조건 REJECT` | `감점 대상입니다` |
| `벽돌 문단 = 독자 이탈 1순위` | `5줄 이상 연속 서술은 줄바꿈으로 끊어주세요` |
| `절대 사용하지 마라` | `사용하지 마세요` |

**예외 (변경 금지)**:
- "사망 NPC" 관련 금지 → 유지 (대원칙 4)
- "미습득 무공/스킬 사용 금지" → 유지
- "타인 시점 정보 노출 금지" (1인칭 제한) → 유지

**작업 방법**: `replace_all=false`로 개별 치환. 치환 전 원문 확인 필수 (맥락에 따라 미치환).

**테스트**:
- `pytest tests/test_satisfaction_step2_prompts.py -v` (프롬프트 길이 회귀)
- `pytest tests/ -q`

**수용 기준**:
- [x] "절대 금지" 0건 (대원칙 예외 제외)
- [x] "무조건 REJECT" 0건
- [x] 대원칙 4 관련 금지 표현은 그대로 유지
- [x] 프롬프트 길이 임계값 내

---

### 오더 3: TF-A — 프롬프트 중복 제거

**의존성**: 없음 (독립 실행 가능, TF-E와 병렬 OK)

**변경: `config/prompts/director.yaml`**

**3-1. 모순 검사 9항 중복 제거**

ENSEMBLE_VARIABLE_PROMPT (L345-385)에 있는 `### 🚨🚨🚨 [V67] 최우선 — 명시적 모순 검사` 블록 **전체 삭제**.
대신 아래 1줄 참조로 교체:

```yaml
    ※ 위 stable_context의 [V67] 모순 검사 9항을 이 심사에도 동일 적용하세요.
```

**이유**: ENSEMBLE_SELECTION_PROMPT는 `{stable_context}` 플레이스홀더로 STABLE_CONTEXT를 이미 포함. 2중 주입 = 토큰 낭비.

**3-2. [I-10] 점진적 감점 규칙 중복 제거**

ENSEMBLE_VARIABLE_PROMPT (L371-375)의 `[I-10] 점진적 감점 규칙` 블록 삭제.
대신:

```yaml
    ※ stable_context의 [I-10] 점진적 감점 규칙을 적용하세요.
```

**3-3. [TF-27] 100점 지향 중복 제거**

ENSEMBLE_VARIABLE_PROMPT (L377)의 `[TF-27] 100점 지향 원칙` 블록 삭제.
대신:

```yaml
    ※ stable_context의 [TF-27] 100점 지향 원칙을 적용하세요.
```

**3-4. 참조 1줄들을 한 블록으로 통합**

삭제한 3개 블록 자리에 아래 1블록만 배치:

```yaml
    ### ※ 중복 방지 — stable_context 참조
    아래 항목은 stable_context에 이미 포함되어 있으므로 동일 기준을 적용하세요:
    - [V67] 명시적 모순 검사 9항
    - [I-10] 점진적 감점 규칙 (CRITICAL/MAJOR/MINOR)
    - [TF-27] 100점 지향 원칙
```

**주의**:
- ENSEMBLE_STABLE_CONTEXT (L61-101)의 원본은 **절대 삭제하지 않음** (이것이 SSOT)
- STRATEGIC_AUDIT_PROMPT_V30, DIRECTOR_AUDIT_PROMPT_V30에도 동일 중복이 있으면 같은 패턴으로 처리

**테스트**:
- `pytest tests/test_satisfaction_step2_prompts.py -v` (프롬프트 길이 — 크게 줄어야 함, 임계값 하향 필요할 수 있음)
- `pytest tests/test_nc3_checklist.py -v`
- `pytest tests/ -q`

**수용 기준**:
- [x] ENSEMBLE_VARIABLE_PROMPT에서 V67/I-10/TF-27 원문 블록 삭제됨
- [x] ENSEMBLE_STABLE_CONTEXT의 원본 블록은 그대로 유지
- [x] 참조 블록 1개 추가됨
- [x] 프롬프트 길이 감소 확인 (테스트 임계값 조정 필요 시 같이 수정)

> **⚠️ [감리 3차 결과] TF-A NO-OP 판정**
>
> 위 오더는 **설계 오류**로 인해 NO-OP 처리됨:
> - "STABLE_CONTEXT L61-101이 SSOT" → 실제로는 STABLE_CONTEXT에 V67 없음
> - VARIABLE_PROMPT (SSOT) + SELECTION_PROMPT (standalone fallback) 양쪽 모두 V67 필수
> - Codex가 VARIABLE_PROMPT에서 삭제 → CRITICAL 결함 → 수동 복원 완료
> - 진정한 dedup은 V67→STABLE_CONTEXT 이동 필요 (캐시 재설계) → P2 후순위

---

### 오더 4: TF-C — 스키마-프롬프트-규칙 3중 정합

**의존성**: TF-A 완료 후 (프롬프트 텍스트 위치가 변경됨)

**변경 1: `config/prompts/director.yaml`**

- NC-3 `consistency_checklist` 지시에서 "반드시 입력" → "가능하면 작성하세요. 미작성 시 별도 감점 없습니다" 변경
- NC-1 `numeric_consistency_review` 지시에서 "각 항목에 반드시 AGREE/DISMISS" → "Python advisory를 참고하여 continuity_contradiction 점수에 직접 반영하세요. 별도 numeric_consistency_review 응답은 선택사항입니다" 변경

**변경 2: `modules/domain/agents/director_ensemble.py`**

NC-1 AGREE 자동감점 블록 (L887-945) 수정:

```python
# 현재 (L910-928):
if _nc_agree_count > 0:
    _cc_cap = max(0, 40 - _nc_agree_count * 8)
    if _cc_score > _cc_cap:
        _sb["continuity_contradiction"] = _cc_cap
        # 총점 재계산...

# → 변경: 자동감점 제거, 로깅만 유지
if _nc_agree_count > 0:
    logging.warning(
        "[NC-1] Director가 %d건 수치 모순 인정. "
        "Director가 continuity_contradiction에 직접 반영했는지 확인 권장.",
        _nc_agree_count,
    )
    # 자동감점 제거 — Director 주권 존중 (대원칙 3)
```

NC-1 미응답 감점 제거 (pw 10→5 로직 찾아서 삭제 또는 주석화):

```python
# 현재: numeric_consistency_review 미응답 → python_warnings 10→5
# → 변경: 미응답 시에도 감점 없음 (Director 주권 존중)
```

**변경 3: `modules/core/response_schemas.py`**

`fix_scope_reasoning` (L136-139) — `required` 리스트(L161)에서 유지하되, `description`에 "(미작성 시 빈 문자열 허용)" 추가. Python이 이미 빈문자열을 허용하므로 실질 변경 없음.

**테스트**:
- `pytest tests/test_nc1_numeric_consistency.py -v` (NC-1 테스트 — 감점 로직 변경에 따라 기대값 수정 필요)
- `pytest tests/test_nc3_checklist.py -v`
- `pytest tests/ -q`

**수용 기준**:
- [x] NC-1 AGREE 시 `_cc_cap` 강제 미적용 (자동감점 0)
- [x] NC-1 미응답 시 `python_warnings` 감점 없음
- [x] NC-3 미응답 시 감점 없음 (기존과 동일 — 이미 구현됨)
- [x] 프롬프트 톤이 "필수"→"선택사항/권장"으로 변경됨
- [x] 관련 테스트 기대값 업데이트 완료

---

### 오더 5: TF-G — Self-Critique 게이트 검사

**의존성**: 없음 (독립 실행 가능)

**변경: `modules/domain/agents/chief_writer_quality.py`**

`apply_self_critique()` (L67-174)의 self-critique 루프(L138) **직전**에 게이트 검사 추가:

```python
# L137 직후, for 루프 직전에 삽입:

# ── [TF-G] 게이트 검사: ending_hook + 분량 (severity="low" 탈출 방지) ──
_gate_issues = []
if blueprint:
    _eh_issues = self._check_ending_hook_presence(current_manuscript, blueprint)
    if _eh_issues:
        _gate_issues.extend(_eh_issues)
if len(current_manuscript) < 5000:
    _gate_issues.append(f"분량 부족 ({len(current_manuscript)}자 < 5,000자)")

if _gate_issues:
    logging.info("[TF-G] 게이트 검사 실패 %d건: %s", len(_gate_issues), _gate_issues)
    # 게이트 이슈가 있으면 무조건 1회 수정 시도
    _gate_prompt = (
        "아래 필수 요건이 미충족입니다. 반드시 수정하세요:\n"
        + "\n".join(f"- {g}" for g in _gate_issues)
    )
    try:
        current_manuscript = self._fix_issues(
            current_manuscript, [{"severity": "high", "issues": _gate_issues}],
            hud_report, genre_name,
        )
        total_issues_fixed += len(_gate_issues)
    except Exception as _ge:
        logging.warning("[TF-G] 게이트 수정 실패 (비치명): %s", _ge)

for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):
    ...  # 기존 루프
```

**주의**: `_fix_issues()` 메서드 시그니처 확인 필요. 현재 `_fix_issues(manuscript, critique_result_dict, ...)` 형태이면 호환되는 dict 구조로 전달.

**테스트**:
- `python -m py_compile modules/domain/agents/chief_writer_quality.py`
- `pytest tests/test_chief_writer_quality*.py -v` (관련 테스트)
- `pytest tests/ -q`

**수용 기준**:
- [x] ending_hook 미포함 시 게이트에서 사전 수정 시도
- [x] 분량 5,000자 미만 시 게이트에서 사전 수정 시도
- [x] 기존 self-critique 루프는 그대로 유지 (게이트 후 실행)
- [x] 게이트 수정 실패 시 비치명 (기존 루프로 진행)

---

### 오더 6: TF-I — 피드백 전달 경로 명확화

**의존성**: 없음 (독립 실행 가능)

**변경: `modules/core/stage4_interview_round.py`**

`run()` 메서드에서 `_build_common_writer_kwargs()` 호출 직후 (L269-273 이후):

```python
# L273 직후에 추가:
# [TF-I] Director 피드백을 common_writer_kwargs에 명시 전달
if director_feedback:
    _common_writer_kwargs["director_feedback"] = director_feedback
```

**소비자 측** (`chief_writer.py`의 `generate_ensemble()` 등)에서 `kwargs.get("director_feedback")` 접근 가능해짐.
다만 **기존 PromptWeighter 경로(L299-302)도 그대로 유지** — 이중 전달이지만 충돌 없음 (dict 키 접근 vs mandatory_context prepend는 독립 경로).

**테스트**:
- `python -m py_compile modules/core/stage4_interview_round.py`
- `pytest tests/test_pipeline_wiring.py -v`
- `pytest tests/ -q`

**수용 기준**:
- [x] `_common_writer_kwargs["director_feedback"]` 키 존재 확인
- [x] 기존 PromptWeighter 주입 경로 (L299-302) 미변경
- [x] `_build_common_writer_kwargs()` 시그니처 미변경

---

### 오더 7: TF-B — Director 의사결정 부하 경감

**의존성**: TF-C 완료 후 (NC-1/NC-3 규칙 변경 후 스키마 전환)

**Phase 1만 구현** (Phase 2는 별도 스프린트):

**변경 1: `config/prompts/director.yaml`**

NC-3 consistency_checklist 응답 형식 변경 — 4곳 전량:

```yaml
# 현재:
"consistency_checklist": {
    "numeric_accuracy": "OK",
    "arithmetic": "ISSUE",
    ...10개 전부 OK/ISSUE
}

# → 변경:
"consistency_issues": ["arithmetic: 레버리지 40.6% 오류", "scene_overlap: 3화와 동일 구조"]
# 이슈가 없으면 빈 배열: "consistency_issues": []
```

**변경 2: `modules/core/response_schemas.py`**

`DIRECTOR_AUDIT_SCHEMA`의 `consistency_checklist` (L145-158) → `consistency_issues`로 교체:

```python
"consistency_issues": types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(type=types.Type.STRING),
    description="일관성 이슈 배열. 이슈가 있는 항목만 '카테고리: 설명' 형식으로. 이슈 없으면 빈 배열.",
),
```

**변경 3: `modules/domain/agents/director_ensemble.py`**

NC-3 파싱 블록을 `consistency_issues` 배열 기반으로 변경:

```python
# 현재 NC-3: _checklist dict에서 ISSUE 카운트
# → 변경: _issues 배열의 len()으로 카운트
_consistency_issues = result.get("consistency_issues") or []
if isinstance(_consistency_issues, list) and len(_consistency_issues) >= 3:
    # python_warnings 상한 3점 (기존 로직 동일)
    ...
```

**하위호환**: dict 형태도 폴백으로 지원 (기존 `consistency_checklist` dict → `consistency_issues` 배열 자동 변환):

```python
# 하위호환 브릿지
_raw_checklist = result.get("consistency_checklist")
if isinstance(_raw_checklist, dict) and not _consistency_issues:
    _consistency_issues = [
        f"{k}: ISSUE" for k, v in _raw_checklist.items()
        if str(v).upper() == "ISSUE"
    ]
```

**변경 4: `tests/test_nc3_checklist.py`**

기존 dict 기반 테스트 유지 (하위호환 테스트) + 배열 기반 테스트 추가.

**테스트**:
- `pytest tests/test_nc3_checklist.py -v`
- `pytest tests/ -q`

**수용 기준**:
- [x] Director가 `consistency_issues` 배열로 응답 가능
- [x] 기존 `consistency_checklist` dict도 폴백으로 처리됨
- [x] ISSUE 3건+ → python_warnings 상한 3점 (기존 로직 유지)
- [x] 스키마-프롬프트-Python 3곳 정합

---

### 오더 8: TF-H — JSON 파싱 실패 복구 강화

**의존성**: 없음 (독립 실행 가능, TF-B와 병렬 OK)

**변경 1: `modules/domain/agents/director_ensemble.py`**

`select_and_judge_ensemble()` 내 JSON 파싱 실패 처리 블록 (L180 부근) 수정:

```python
# 파싱 실패 시 단순 프롬프트로 1회 재시도
if not isinstance(result, dict) or result.get("parsing_error"):
    logging.warning("[TF-H] Director JSON 파싱 실패 → 단순 프롬프트로 재시도")
    _retry_prompt = (
        "이전 응답의 JSON이 유효하지 않았습니다. 아래 형식으로만 응답하세요:\n"
        '{"selected": "A", "verdict": "PASS", "score": 85, '
        '"score_breakdown": {"continuity_contradiction": 35, "blueprint_coverage": 20, '
        '"quality_engagement": 15, "length": 10, "python_warnings": 5}, '
        '"reason": "판정 이유"}'
    )
    try:
        _retry_raw = self._d.ask(_retry_prompt, temperature=0.0)
        _retry_result = self._d._extract_json_robust(_retry_raw)
        if isinstance(_retry_result, dict) and not _retry_result.get("parsing_error"):
            result = _retry_result
            logging.info("[TF-H] 재시도 성공")
        else:
            logging.warning("[TF-H] 재시도도 실패 → 기존 폴백")
    except Exception as _rte:
        logging.warning("[TF-H] 재시도 예외: %s → 기존 폴백", _rte)
```

**변경 2: `modules/domain/agents/base_agent.py`**

`_extract_json_robust()` Phase 3(Hard Repair) 단계에서 한글 큰따옴표 정규화 추가:

```python
# Hard Repair 단계 시작 부분에 추가:
import re
text = re.sub(r'["\u201c\u201d]', '"', text)  # 한글 큰따옴표 → ASCII 큰따옴표
```

**테스트**:
- `python -m py_compile modules/domain/agents/director_ensemble.py`
- `python -m py_compile modules/domain/agents/base_agent.py`
- `pytest tests/test_base_agent*.py -v` (JSON 파싱 테스트)
- `pytest tests/ -q`

**수용 기준**:
- [x] 파싱 실패 시 1회 재시도 (temperature=0.0)
- [x] 재시도 실패 시 기존 폴백 경로 그대로 유지
- [x] 한글 큰따옴표 정규화 추가
- [x] 재시도는 실패 시에만 발동 (정상 경로 오버헤드 0)

---

### 오더 공통사항

**커밋 단위**: TF별 1커밋 (예: `feat(TF-D): Advisory 우선순위 시각화`)

**CLAUDE.md 업데이트**: 전체 오더 완료 후 1회. "완료된 것" 리스트에 추가, 테스트 기준선 갱신.

**감리**: 오더 구현 완료 후 Opus가 3회 감리 실시 — ①코드 팩트 검증 ②대원칙 정합성 ③테스트 커버리지

---

### 감리 3차 — 누락 항목 + 내부 일관성 검증 ✅

| 항목 | 결과 | 조치 |
|------|------|------|
| TF-A~I 누락 주제 | ❌ 3건 발견 | P3-추가 섹션에 analyst Few-Shot/HUD 장르별 임계값/MAX_CONTINUATIONS 추가 |
| 문서 내부 일관성 | ✅ 100% | TF-ID 9개 × 파일경로·예상효과·우선순위표 교차 정합 |
| 실파이프라인 정합 | ✅ CORRECT | 6단계 후처리 체인·advisory 체인 8개·DI 슬롯 24개 CLAUDE.md 기준 일치 |
| P0~P3 우선순위 배분 | ✅ VALID | 위험도 기준 정렬 확인 (P0=포맷만, P1=로직, P2=구조, P3=리팩토링) |
