# Audit — projects/00000 Post-TF-J 전수조사

> **일시**: 2026-03-07
> **프로젝트**: `projects/00000` (투자물 장르, Arc 1~5, Ep.1~19)
> **범위**: TF-H + TF-J 패치 적용 후 Stage 2 실행 결과 전수 검증
> **기준**: 3,647 passed

---

## 1. 실행 요약

| 항목 | 값 |
|------|-----|
| Stage 0 | PASS (style_guide + Bible + KeyNPC 10명) |
| Stage 2 Arc 1~5 | **5/5 PASS** (100, 100, 95, 95, 95) |
| Stage 3 Blueprint | **미실행** (blueprints 테이블 빈 상태) |
| Stage 4 원고 | **미실행** |
| LLM 호출 | 72회, 실패 0건, 비용 $1.26 |
| auto-correct | 5건 (Arc 1~5 각 1건, 전량 정상) |

---

## 2. 이슈 분류

### BUG-1 (P2 하향): TF-J 다양성 규칙 — Block treatment가 단일 공간이므로 정상 동작

**증상**: Arc 4(12~15화) 4화 연속 SW오피스.

**재조사 결과**: Block 4 "금의 귀환" treatment context가 **명시적으로 "SW인베스트먼트 5평짜리 원룸 오피스"를 무대로 설정**. event_villain/solution/reward 전부 오피스에서 모니터 보며 트레이딩하는 장면. 외부 이동 이벤트 없음. **Arc가 Block의 서사 의도를 충실히 따른 것이며, TF-J 규칙 위반이 아님.**

**근본 원인 재판정**: TF-J 규칙("3화 이상 연속 금지")이 Block 서사와 충돌할 수 있는 **설계 갭**. 검증 계층 부재 자체는 사실이나, Block이 단일 공간이면 감지해봤자 오탐.

> **[P1→P2 하향 근거]**: Block 4 treatment 실물 확인. context/event_villain/solution/reward 전량 SW오피스 내 트레이딩 서사. LLM이 규칙을 무시한 것이 아니라 Block 지시를 우선한 것.

| 검증 계층 | 장소 다양성 체크 | 비고 |
|-----------|----------------|------|
| `_evaluate_candidate()` (arc_ensemble.py L694) | **없음** | 필수 필드/금지 아이템/연속성/분량만 검사 |
| Stage 2 Director Audit (`STRATEGIC_AUDIT_PROMPT_V30`) | **없음** | 내부 모순/상태 연속성/미래 오염/분절성/페이싱/인과율 6단계만 |
| NC-3 `scene_variety` | Stage 4에만 존재 | Arc 설계 단계에서 무력 |

**패치 방안**:

**(A안) Python advisory 추가 (감점 없음, issues 리스트만)** — `_evaluate_candidate()`에 tactical_doc 내 에피소드별 장소를 regex 파싱하여 3화+ 동일 장소 연속 시 **issues에 추가하되 score는 변경하지 않음**. Director에 advisory로 전달.

> **[감리 수정]**: 초안에서 `score -= 5` 감점을 제안했으나, 감리 3번에서 대원칙 1("Python은 수집만") + 대원칙 3("Director 주권주의") 위반 지적. TF-C 선례(NC-1/NC-3 자동감점 제거)에 따라 **advisory-only**로 변경. Python은 사실 감지만, 판단은 Director가 수행.
>
> **[감리 수정 2]**: 초안의 `td_episodes` dict 순회 의사코드는 실제 데이터 구조와 불일치. `_evaluate_candidate()` 시점의 tactical_doc은 **str**(flat string)이다. `_extract_episode_sections()` + regex 방식으로 화 분할 후 장소 키워드 추출 필요.

```python
# arc_ensemble.py _evaluate_candidate() 내부 — advisory only, score 미변경
import re
_ep_sections = re.split(r"(?:제?\s*\d+화|에피소드\s*\d+|EP\.?\s*\d+)", tactical_doc)
locations = []
for sec in _ep_sections[1:]:  # 첫 분할은 헤더
    # 장소 키워드 추출 (앞 200자 내 "사무실|오피스|카페|..." 매칭)
    _loc_match = re.search(r"(사무실|오피스|카페|거래소|은행|법원|호텔|본가|저택|학교)", sec[:200])
    locations.append(_loc_match.group(1) if _loc_match else "")

consecutive = 1
for i in range(1, len(locations)):
    if locations[i] and locations[i] == locations[i-1]:
        consecutive += 1
        if consecutive >= 3:
            issues.append("[TF-J] 3화+ 연속 동일 장소 — Director 확인 필요")
            break
    else:
        consecutive = 1
```

**(B안) Director Audit 프롬프트 추가** — `STRATEGIC_AUDIT_PROMPT_V30`에 Step 6 "공간/인물 다양성" 추가. Director가 직접 판단하므로 대원칙 3 완전 부합.

**권장**: B안 단독. A안은 Block context 미참조 시 오탐 위험.

**TF-J 프롬프트 규칙 보강**: "3화 이상 연속 금지"에 **"단, Block/Treatment의 서사가 단일 공간을 요구하는 경우 예외"** 단서 추가 필요.

---

### BUG-2 (P1): C-1 regex 한글 word boundary 결함 — "Arc 2에서" → "시기 2에서"

**증상**: Arc 3 10화 tactical_doc에 "시기 2에서" 표현 잔존.

**근본 원인**: `stage2_optimizer.py` L719 regex `\bArc\s+\d+\b`가 한글 뒤에서 `\b` 미발동.

- Python `re` 모듈은 유니코드 인식 → 한글 '에'가 `\w`로 분류
- "2에" 사이에 word boundary 없음 → `\bArc\s+\d+\b` 매칭 실패
- fallback 규칙 L720 `\bArc\b` → `"시기"` 적용 → "Arc 2에서" → "시기 2에서"

**경로**:
```
LLM 원본: "Arc 2에서" (llm_io.jsonl 확인)
  → C-1 L719: \bArc\s+\d+\b 매칭 실패 (한글 \b 문제)
  → C-1 L720: \bArc\b → "시기" 치환
  → 결과: "시기 2에서"
```

**독자 노출 가능성**: 있음 — tactical_doc → Blueprint arc_focus → CW common_context 경로 존재. 4th wall 방어 3단계(`_check_system_term_exposure`) 모두 "시기 N" 미감지.

**패치 방안**: L719 regex 후행 `\b` 제거 또는 lookahead로 교체

```python
# Before (L719):
(r"\bArc\s+\d+\b", "해당 시기"),

# After — 후행 \b 대신 non-digit lookahead:
(r"\bArc\s+\d+(?=\D|$)", "해당 시기"),
```

이렇게 하면 "Arc 2에서"에서 "2" 뒤 "에"(non-digit)가 매칭되어 "해당 시기에서"로 정상 치환됨.

---

### BUG-3 (P2): llm_calls stage/ep_num 미배선 — 전 파이프라인 NULL

**증상**: `llm_calls` 테이블 72건 전부 `stage=NULL, ep_num=NULL`.

**근본 원인**: `base_agent.py` L313-337의 `_resolve_stage_number()`/`_resolve_episode_number()`가 값을 탐색하지만, **코드베이스 어디에서도 `_current_stage`/`_current_ep_num`을 에이전트 인스턴스에 설정하지 않음**. `ProjectContext`에도 `current_stage`/`episode_num` 속성 없음.

Log-Phase2에서 resolve 메서드를 만들었으나 **값 주입 배선이 누락**된 미완성 상태.

**영향**: `FailureAnalyzer`의 stage별/ep별 LLM 호출 통계, 비용 추적 불가. 기능적 영향 없음(파이프라인 동작에 무관).

**패치 방안**: 각 Stage 오케스트레이터에서 에이전트 호출 전 setattr 주입

```python
# stage2_orchestrator.py (Arc 생성 전)
for agent in [self.analyst, self.arc_ensemble, ...]:
    agent._current_stage = 2
    agent._current_ep_num = ep_num

# stage4_orchestrator.py (원고 생성 전)
for agent in [self.chief_writer, self.director, ...]:
    agent._current_stage = 4
    agent._current_ep_num = ep_num
```

---

## 3. 비이슈 확인 (정상)

| 항목 | 결과 |
|------|------|
| ep_start/ep_end 연속성 | PASS — 겹침/빈 화수 없음 |
| Arc 간 상태 계승 | PASS — end_state → start_state 전량 일치 |
| tactical_doc 분량 | PASS — 19화 전량 500자+ |
| 무협 오염 | PASS — 0건 |
| 메타 용어 노출 | PASS — "Arc/Block/Stage/Blueprint" 0건 (BUG-2 "시기" 제외) |
| 자본금 산술 정합 | PASS — 20→30→45→50억 일관 |
| items_acquired/consumed | PASS |
| PATCH-B auto-correct | NEEDS_INVESTIGATION — 감지 기능 정상이나 4건 연속 소멸 반복은 LLM 컨텍스트 주입 구조 문제 시사 |
| LLM 실패율 | PASS — 0/72 (100% 성공) |

---

## 4. 이슈 분류 종합

| 등급 | ID | 내용 | 위치 |
|------|-----|------|------|
| **P2** | **BUG-1** | TF-J 다양성 규칙 — Block 4 treatment가 단일 공간이므로 정상 동작. 검증 계층 부재는 사실이나 오탐 위험 | `arc_ensemble.py` + `director.yaml` AUDIT (B안 후순위) |
| **P1** | **BUG-2** | C-1 regex 한글 `\b` 결함 — "Arc 2에서" → "시기 2에서" 오치환 | `stage2_optimizer.py` L719 |
| **P2** | **BUG-3** | llm_calls stage/ep_num 미배선 — resolve 메서드 존재, 값 주입 없음 | `base_agent.py` L313-337 |
| **P2** | **BUG-4** | npc_history reason 전부 빈 값 — TF-D 설계 의도 대비 Stage 2 경로에서 reason 미주입 | `npc_history` 테이블 10건 전량 `reason=[]` |
| **P2** | **FINDING-1** | PATCH-B 소지품 소멸 4건 연속 반복 — Arc 2~5 매번 이전 Arc 소지품 소실 감지. 감지 기능 정상이나 LLM이 반복적으로 소지품 누락하는 구조적 패턴 | `runtime_audit.jsonl` Arc 2~5 전량 |

---

## 5. 확신도 평가

| 조사 항목 | 결과 | 방법 |
|-----------|------|------|
| TF-J 프롬프트 전달 경로 | **확인** — ensemble.yaml L31-33 → arc_ensemble._generate_single() → LLM | 코드 경로 추적 (5단계) |
| TF-J 규칙 LLM 도달 여부 | **도달함** — 고정 텍스트, 변수 치환 대상 아님 | ensemble.yaml 직접 확인 |
| 검증 계층 부재 | **확인** — _evaluate_candidate + AUDIT + NC-3 전량 확인, 장소 다양성 0건 | 코드 3곳 전수 확인 |
| C-1 regex 결함 | **확인** — llm_io.jsonl 원본 "Arc 2" vs arc_003.txt "시기 2" 대조 | LLM 원본 ↔ 저장 파일 교차 검증 |
| `\b` 한글 미발동 | **확인** — Python re 유니코드 모드에서 한글은 `\w` | Python 문서 + 실동작 확인 |
| 4th wall "시기 N" 미감지 | **확인** — `_check_system_term_exposure` regex에 "시기" 없음 | 코드 직접 확인 |
| llm_calls 미배선 | **확인** — `_current_stage` setattr 0건 (코드베이스 전수 검색) | grep 전수 검색 |
| Stage 4에서도 NULL | **확인** — resolve 경로 동일, 배선 코드 없음 | 코드 추적 |

**종합 확신도: 99%** — LLM 원본(llm_io.jsonl) ↔ 저장 파일(arc_003.txt) 교차 검증, 코드 경로 5단계 추적, regex 동작 확인, 검증 계층 3곳 전수 확인 완료.

---

## 6. 감리 이력 (3회)

| 회차 | 역할 | 판정 | 주요 발견 |
|------|------|------|-----------|
| 1 | 인과 분석 | BUG-1~3 전량 **CORRECT** | 프롬프트 전달 확인, 검증 계층 부재 확인, regex 동작 재현, setattr 0건 확인 |
| 2 | 패치 안전성 | BUG-1 A안 **RISK**, BUG-2/3 **SAFE** | A안 `td_episodes` dict 순회는 실제 str 구조와 불일치. `(?=\D\|$)` lookahead 안전. setattr 순차 아키텍처에서 안전 |
| 3 | 대원칙+누락 | **ISSUE 2건** + **NEEDS_INVESTIGATION 1건** | A안 `score -= 5` 대원칙 1·3 위반(advisory-only로 변경), PATCH-B 4건 연속 반복 구조 문제, npc_history reason 미배선(BUG-4 신규) |

**감리 결과 반영 완료**: A안 감점→advisory 변경, 의사코드 데이터 구조 수정, PATCH-B 격상, BUG-4 추가.
