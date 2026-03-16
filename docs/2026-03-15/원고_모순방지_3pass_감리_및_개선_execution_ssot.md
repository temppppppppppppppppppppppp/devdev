<!-- [추적필요] -->
# 원고 모순 방지 — 3PASS 감리 및 개선 Execution SSOT

Date: 2026-03-15
Status: blocked
Canonical Path: `docs/2026-03-15/원고_모순방지_3pass_감리_및_개선_execution_ssot.md`
Temp Mirror Path: `none`
Source Survey Docs: `docs/2026-03-15/원고_모순점검_00_260315.md`
Queue Disposition: `excluded from active queue on 2026-03-15`
Authority Scope: `projects/00_260315` only
Authority Class: `project-scoped memo only; invalid for projects/000 or global manuscript authority`

| Field | Value |
|-------|-------|
| **Date** | 2026-03-15 |
| **Baseline** | `bbb00a77` |
| **Status** | blocked |
| **Source** | `docs/2026-03-15/원고_모순점검_00_260315.md` (7건) |
| **Canonical Path** | `docs/2026-03-15/원고_모순방지_3pass_감리_및_개선_execution_ssot.md` |
| **Temp Mirror Path** | `none` |
| **Queue Disposition** | excluded from active queue on 2026-03-15 |
| **Authority Scope** | `projects/00_260315` only |
| **Authority Class** | project-scoped memo only; not valid for `projects/000` or global manuscript remediation |
| **Predecessor** | originally queued under `codebase-global-post-remediation-execution-roadmap.md`; excluded after project-scope mismatch review |

---

## Demotion Notice
- This document is retained only as a bounded memo for `projects/00_260315`.
- It must not govern the active execution queue, `projects/000`, or any global manuscript-remediation decision.
- Re-entry requires a fresh scope check plus a new 3-pass audit against the intended target project.

---

## PASS 1 — 개별 항목 근인 분류

각 모순을 (A) LLM 고유 한계, (B) 시스템 갭, (C) 프롬프트 갭 으로 분류하고, 기존 어떤 시스템이 잡았어야 하는지 판정한다.

### M-01: 박성호 호칭 불일치 (팀장 vs 부장)

| 분류 | 판정 |
|------|------|
| **근인** | **(B) 시스템 갭 + (A) LLM 장거리 컨텍스트 드리프트** |
| **잡았어야 할 시스템** | Director 체크리스트 #1 "고유명사 일관성" — 그러나 이름만 검사, 직함/호칭은 범위 밖 |
| **현재 FactLedger** | `characters` 섹션에 `role` 필드 존재하나, "팀장"/"부장" 같은 **세분 직함**은 미추적 |
| **현재 NpcDrift** | 성격(personality) 드리프트만 감지, 호칭 드리프트는 범위 밖 |
| **LLM 요인** | "팀장"과 "부장"은 의미적으로 유사한 한국어 직급명 → LLM이 6화 시점에서 혼동. 전형적 soft-token confusion |
| **개선 가능성** | **높음** — Python 레벨에서 잡을 수 있음 |

**개선안**: FactLedger `characters` 에 `title` (직함) 필드 추가 → TruthGate에서 원고 내 NPC 호칭과 등록 직함 교차 검증 (regex 매칭)

---

### M-02: IFC 2006년 존재 (역사적 사실 오류)

| 분류 | 판정 |
|------|------|
| **근인** | **(A) LLM 고유 한계 (사실 환각) + (C) 프롬프트 갭** |
| **잡았어야 할 시스템** | 없음 — 현재 시스템에 **실세계 사실 검증 레이어 자체가 부재** |
| **Blueprint Preflight** | "Allow minor historical tech anachronisms (±1-5 years)" 명시 — 허용 범위이나 IFC는 6년 오차 |
| **LLM 요인** | "여의도 + 금융 + 고급 빌딩" → IFC 연상이 학습 데이터에서 압도적. 시대 교차 검증 미수행 |
| **개선 가능성** | **중간** — 완벽한 사실 검증은 불가능하나 완화책 존재 |

**개선안**:
- **(1차)** 투자물 장르 프롬프트에 "실존 건물/기업명 사용 시 해당 시대 존재 여부 자체 검증" 지시 추가
- **(2차)** Stage 3 Blueprint에 `timeline_year` 필드 명시 → ChiefWriter에 "현재 작중 연도: {year}" 강제 주입
- **(3차, 선택)** 고비용이므로 당장은 NO-GO: 외부 사실 검증 API/임베딩 연동

---

### M-03: 사무실 문 설정 급격 격상

| 분류 | 판정 |
|------|------|
| **근인** | **(B) 시스템 갭 — 환경 오브젝트 속성 지속성 미추적** |
| **잡았어야 할 시스템** | WorldState — 그러나 `active_items`는 주인공 소유물만 추적, **환경 설정(세팅)의 물리 속성**은 범위 밖 |
| **현재 ChainLink** | `location` 필드는 "현재 위치"만 기록, 장소의 물리적 특성(문 재질 등)은 미기록 |
| **LLM 요인** | 긴장감 고조를 위해 장면마다 설정을 즉흥 강화(escalation bias). 이전 화에서 자기가 쓴 "강화유리 문"을 기억 못함 |
| **개선 가능성** | **높음** — ChainLink 확장으로 해결 가능 |

**개선안**: ChainLink에 `setting_details` dict 추가 → 주요 장소의 물리적 속성(문 종류, 층수, 창문 유형 등)을 에피소드 종료 시 LLM 추출 → 다음 화 mandatory_context로 주입

---

### M-04: 전투 능력 근거 부재

| 분류 | 판정 |
|------|------|
| **근인** | **(A) LLM 장르 클리셰 편향 + (B) 시스템 갭 — 캐릭터 능력 프로파일 미추적** |
| **잡았어야 할 시스템** | ContinuityInspector — `learned_before_used` 검증은 있으나, **"학습 없이 발현된 능력"은 범위 밖** |
| **현재 FactLedger** | `skills[]` 리스트로 습득 기술만 추적. 캐릭터의 **기본 능력치 프로파일**(체력, 격투, 지략 등)은 없음 |
| **LLM 요인** | 회귀물/투자물에서도 "주인공은 강해야 한다"는 웹소설 학습 데이터의 장르 관성이 프롬프트보다 우선. 자신이 1화에서 쓴 "무술 경멸" 설정을 7화에서 무시 |
| **개선 가능성** | **높음** — 능력 프로파일 도입 + 프롬프트 강화 |

**개선안**:
- **(1차)** WorldState `protagonist`에 `capability_profile` 추가: `{combat: "없음|초급|중급|고급", intellect: ..., physical: ...}`
- **(2차)** Stage 3 Blueprint preflight에 "주인공 능력 프로파일 범위 내 행동만 허용" 검증 추가
- **(3차)** Director 체크리스트에 #10 "캐릭터 능력 개연성" 항목 신설

---

### M-05: 고층 빌딩 통유리창 탈출

| 분류 | 판정 |
|------|------|
| **근인** | **(A) LLM 물리 추론 한계 + (B) 시스템 갭** |
| **잡았어야 할 시스템** | 없음 — **물리적 개연성 검증 레이어 자체가 부재** |
| **LLM 요인** | LLM은 "극적 탈출 장면"을 생성할 때 물리 법칙(고층 창문 개폐 불가, 중력)을 추론하지 않음. 이것은 현재 LLM 아키텍처의 근본적 한계에 가까움 |
| **개선 가능성** | **중간** — 완전 자동화 불가, 프롬프트 완화책 가능 |

**개선안**:
- **(1차)** ChainLink `setting_details`에 층수/건물 유형 기록 → "고층 빌딩" 태그 시 ChiefWriter 프롬프트에 "고층 건물에서 창문 탈출 불가" 제약 자동 주입
- **(2차)** Director 체크리스트에 "물리적 개연성" 항목 추가 — "탈출/이동/전투 장면의 물리적 가능성 검증"
- **(3차, 한계 인정)** 모든 물리 시나리오를 열거할 수 없으므로, "의심스러운 물리 장면 발견 시 WARNING" 수준의 advisory가 현실적 상한

---

### M-06: 습격자 정체 혼란

| 분류 | 판정 |
|------|------|
| **근인** | **(A) LLM 컨텍스트 드리프트 + (C) 프롬프트 갭** |
| **잡았어야 할 시스템** | InfoParadox — 주인공의 **추론/판단**도 사실과 동일한 수준으로 추적해야 하나, 현재는 "주인공이 아는 사실"만 추적 |
| **LLM 요인** | 4~5화에서 "한태준 소속"이라 판단한 것을 6~7화에서 "한정호 소속"으로 바꿈. 화 단위 생성에서 이전 추론을 망각 |
| **개선 가능성** | **중간** — 의도적 미스터리와 실수를 구분하기 어려움 |

**개선안**:
- **(1차)** WorldState에 `protagonist_beliefs[]` 필드 추가: `{belief: "습격자는 한태준 소속", established_ep: 5, status: "unconfirmed"}`
- **(2차)** Director에 "주인공의 이전 추론과 현재 행동이 모순될 경우 명시적 재평가 장면 필요" 지시 추가

---

### M-07: 비상 스위치 설치 시점 미설명

| 분류 | 판정 |
|------|------|
| **근인** | **(A) LLM 편의적 플로팅 + (B) 시스템 갭** |
| **잡았어야 할 시스템** | ContinuityInspector `item_timeline` — 아이템 "획득→사용" 순서는 검증하나, **환경 설비의 설치 타임라인**은 범위 밖 |
| **LLM 요인** | 극적 장면(8화 탈출)을 위해 소품을 즉흥 생성(deus ex machina). 그 소품이 이전 타임라인에 맞는지 검증하지 않음 |
| **개선 가능성** | **높음** — 새 오브젝트 도입 시 설치/획득 근거 요구 |

**개선안**:
- **(1차)** Director 체크리스트에 "신규 오브젝트/설비의 도입 근거" 항목 추가
- **(2차)** ChiefWriter 프롬프트에 "이전 화에서 언급/복선 없는 새 장치를 갑자기 사용하지 말 것" 명시

---

## PASS 1.5 — BP 로그 역추적 결과 (근인 수정)

### 발견: 모순의 근본 원인은 ChiefWriter가 아니라 Stage 3 Blueprint Ensemble이다

`projects/00_260315/logs/artifacts/stage3/` 역추적 결과, M-03~M-05, M-07의 모순 요소가 **블루프린트 단계에서 이미 설계**되어 있었다.

#### BP 전략별 모순 분포

| 전략 | 적용 화 | 모순 건수 |
|------|---------|----------|
| `dialogue_focused` | 2, 3, 5, 9, 10, 11화 | **0건** |
| `action_focused` | 1, 4, 6, 7, 8화 | **5건** (M-03~M-05, M-07 + M-06 일부) |

#### BP에 심어진 모순 증거

| 모순 | BP 원문 (artifacts) | 판정 |
|------|-------------------|------|
| **M-03** 문 격상 | 7화 BP scene_1: "**강화 문을 잠금**", "**기계식 잠금장치가 여러 번 맞물리는 소리**" — 4화에서 "강화유리 문"이었는데 BP가 이미 격상 | BP 오류 |
| **M-04** 전투 능력 | 7화 BP scene_1 key_events: "**과거 수련으로 다져진 움직임으로 상대의 공격을 회피하고 주동자의 팔을 탈골시킴**" — 1화에서 "무술 경멸, 형식적 수련"인데 BP가 전투 능력 부여 | BP 오류 |
| **M-05** 창문 탈출 | 8화 BP scene_1 key_events: "**창문 하나가 열려 있음**" — 고층 IFC 빌딩인데 BP가 창문 탈출 직접 설계 | BP 오류 |
| **M-07** 비상 스위치 | 8화 BP scene_1: "한시우가 **책상 밑 비상 전력 차단기**로 사무실 전체의 전원을 내려 암흑을 만듦" — 설치 경위 없이 BP가 직접 도입 | BP 오류 |

#### 근인 수정

| 항목 | 기존 근인 | 수정 근인 |
|------|----------|----------|
| M-03 | (B) 시스템 갭 (환경 추적 부재) | **(B) Stage 3 BP Ensemble의 action_focused 전략이 이전 화 설정 무시 + 환경 추적 부재** |
| M-04 | (A) LLM 장르 클리셰 + (B) 능력 미추적 | **(B) BP Ensemble이 capability_profile 없이 전투 장면 설계 + (A) LLM 장르 편향** |
| M-05 | (A) LLM 물리 추론 한계 + (B) 시스템 갭 | **(B) BP Ensemble이 고층 건물 물리 제약 무시하고 탈출 설계 + (A) LLM 물리 추론 한계** |
| M-07 | (A) LLM 편의적 플로팅 + (B) 시스템 갭 | **(B) BP Ensemble이 미도입 설비를 deus ex machina로 설계** |

**핵심 결론**: ChiefWriter는 BP 지시를 충실히 이행했을 뿐이다. 모순을 방지하려면 **Stage 3 Blueprint Ensemble 단계**에서 막아야 한다. Stage 4 Director도 이를 통과시켰으므로 Director 검증도 보강 필요.

---

## PASS 2 — 교차 분석: 시스템적 약점 패턴

### 패턴 E: "Blueprint action_focused 전략의 에스컬레이션 편향" (M-03, M-04, M-05, M-07) — **최우선**

| 현재 상태 | 문제 |
|-----------|------|
| Stage 3 BP Ensemble | `action_focused` 전략 선택 시 긴장감 극대화를 위해 **이전 화 설정 제약을 무시**하고 장면 에스컬레이션 |
| BP Preflight | 수치 정합성, NPC 정합성, 타임라인 정합성은 검증하나 **환경 물리 정합성, 캐릭터 능력 범위**는 범위 밖 |
| BP integrated_scenario | 1,000~1,700자의 상세 시나리오를 작성하면서 **이전 화의 장소/설비/능력 설정과의 교차 검증 없음** |

**진단**: `action_focused` 전략은 `dialogue_focused` 대비 극적 긴장감을 높이도록 설계되어 있으나, 그 과정에서 "더 강한 문", "더 극적인 탈출", "더 압도적인 전투"를 생성하며 **이전 설정을 덮어쓴다.** 모순 7건 중 5건이 이 전략에 집중된 것은 우연이 아니라 구조적 결함이다.

**통합 처방**: → TF-MS-07 (Blueprint Action Strategy Constraint Gate) — **신규, 최우선**

---

### 패턴 A: "환경/세팅 디테일 지속성 부재" (M-03, M-05, M-07)

| 현재 상태 | 문제 |
|-----------|------|
| WorldState | 주인공 소유물만 추적 |
| ChainLink | 위치명만 기록, 물리적 속성 없음 |
| FactLedger | 캐릭터/숫자/아이템만, 환경 오브젝트 없음 |

**진단**: 시스템이 "누가 무엇을 가지고 있는가"는 추적하지만, **"장소가 어떻게 생겼는가"는 전혀 추적하지 않는다.** 문, 창문, 설비, 건물 특성 등 환경 디테일이 화 단위로 리셋되어 LLM이 매 화마다 즉흥적으로 재설정한다.

**통합 처방**: → TF-MS-01 (Setting Persistence Layer)

---

### 패턴 B: "캐릭터 행동 개연성 검증 부재" (M-04, M-07)

| 현재 상태 | 문제 |
|-----------|------|
| FactLedger skills[] | 습득 기술 리스트만 존재 |
| ContinuityInspector | "배운 뒤 사용" 순서만 검증 |
| TruthGate | 사망/파괴/미보유 등 이진 검증만 |

**진단**: "이 캐릭터가 이 행동을 할 수 있는가?"에 대한 **능력 개연성(plausibility) 검증이 없다.** 시스템은 "A 기술을 배웠는가?"만 보고, "A를 배운 적 없는데 A급 행동을 하는가?"는 잡지 못한다.

**통합 처방**: → TF-MS-02 (Character Capability Gate)

---

### 패턴 C: "LLM 장르 클리셰 오버라이드" (M-02, M-04)

| 현재 상태 | 문제 |
|-----------|------|
| ChiefWriter 프롬프트 | 장르별 금기어/필수 개념은 있으나, **"장르 관성 억제"** 지시 없음 |
| Director 체크리스트 | 9항목 중 "캐릭터 능력 범위" 항목 없음 |
| Blueprint Preflight | "minor anachronism 허용" 명시 → 사실 검증 약화 |

**진단**: LLM의 학습 데이터에 포함된 웹소설 클리셰(회귀자는 강하다, 금융가는 IFC에 있다)가 프롬프트 지시보다 우선하는 현상. 현재 프롬프트에 이를 억제하는 **명시적 브레이크가 없다.**

**통합 처방**: → TF-MS-03 (Anti-Cliché Prompt Reinforcement)

---

### 패턴 D: "NPC 메타데이터 추적 공백" (M-01, M-06)

| 현재 상태 | 문제 |
|-----------|------|
| FactLedger characters | role, relationship, personality — **title(직함) 없음** |
| WorldState alive_npcs | role, relation, personality, location — **title 없음** |
| NpcDrift | personality drift만 감지 |

**진단**: NPC의 이름과 성격은 추적하지만, **직함(팀장/부장), 외모, 말투 패턴** 등 변별적 메타데이터가 미추적. LLM이 유사 직급명을 혼동해도 잡을 수 없다.

**통합 처방**: → TF-MS-04 (NPC Extended Metadata)

---

## PASS 3 — 개선 TF 구성 및 실행 계획

### TF 요약

| TF | 이름 | 심각도 | 우선순위 | 대상 모순 | 비용 |
|----|------|--------|---------|----------|------|
| **TF-MS-07** | **Blueprint Action Strategy Constraint Gate** | **CRITICAL** | **P0** | **M-03, M-04, M-05, M-07** | **중 (코드 + 프롬프트)** |
| TF-MS-01 | Setting Persistence Layer | IMPORTANT | P1 | M-03, M-05, M-07 | 중 (코드 + 프롬프트) |
| TF-MS-02 | Character Capability Gate | IMPORTANT | P1 | M-04 | 중 (코드 + 프롬프트) |
| TF-MS-03 | Anti-Cliché Prompt Reinforcement | IMPORTANT | P1 | M-02, M-04 | 저 (프롬프트만) |
| TF-MS-04 | NPC Extended Metadata | IMPORTANT | P2 | M-01, M-06 | 중 (코드) |
| TF-MS-05 | Director Checklist Expansion | IMPORTANT | P1 | M-04, M-05, M-07 | 저 (프롬프트만) |
| TF-MS-06 | Protagonist Belief Tracker | INSIGHT | P3 | M-06 | 중 (코드 + 프롬프트) |

---

### TF-MS-07: Blueprint Action Strategy Constraint Gate — **P0, 최우선**

**목표**: Stage 3 Blueprint Ensemble의 `action_focused` 전략이 이전 화 설정 제약을 무시하고 에스컬레이션하는 패턴을 차단한다.

**근거**: 7건 모순 중 5건(M-03, M-04, M-05, M-07 + M-06 일부)이 `action_focused` BP에서 이미 설계됨. `dialogue_focused` BP는 모순 0건. BP가 오염되면 이후 Stage 4 ChiefWriter/Director가 아무리 잘해도 모순이 전파된다.

**구현 범위**:

1. **BP Preflight에 물리 정합성 게이트 추가** (`blueprint_generator.yaml`)
   - 기존 5항목 (수치, NPC, 타임라인, 장소, 아이템) + 3항목 추가:
     ```
     6. 환경 물리 정합성: 이전 화에서 확립된 장소의 물리 속성(문 종류, 창문 유형,
        층수, 보안 등급)과 현재 BP의 장면 묘사가 일치하는가?
        "강화유리 문"이 갑자기 "방탄 기계식 잠금"으로 변경되면 REJECT.
     7. 캐릭터 능력 범위: protagonist_state.capabilities 또는 이전 화에서 확립된
        주인공 능력 범위 내에서 행동이 설계되었는가?
        무술 미수련 캐릭터가 전문 격투로 다수를 제압하는 BP는 REJECT.
     8. 신규 오브젝트 도입: BP에 이전 화에서 언급되지 않은 장치/설비/도구가
        갑자기 등장하는가? 있다면 해당 화 내에서 설치/획득 장면이 포함되어야 한다.
   ```

2. **BP Ensemble에 이전 화 setting_details 주입** (Stage 3 context)
   - ChainLink의 `setting_details` (TF-MS-01에서 추가)를 Stage 3 BP 생성 컨텍스트에도 주입
   - 주입 포맷: `[장소 물리 제약] 사무실: 문=강화유리, 창=고정(개폐불가), 보안=일반`
   - BP Ensemble이 이 제약을 벗어나는 장면을 설계하면 Preflight에서 REJECT

3. **BP Ensemble에 capability_profile 주입** (Stage 3 context)
   - WorldState의 `capability_profile` (TF-MS-02에서 추가)을 BP 생성 컨텍스트에 주입
   - 주입 포맷: `[주인공 능력 범위] combat=없음, martial_arts=형식적(실전 무경험)`
   - `action_focused` 전략 선택 시에도 이 범위를 벗어나는 전투 장면 설계 금지

4. **action_focused 전략 전용 제약 프롬프트** (`blueprint_generator.yaml`)
   ```
   [action_focused 전략 제약]
   - 긴장감은 물리적 전투가 아닌 심리전, 시간 압박, 정보 우위로 구현할 것.
   - 주인공이 직접 전투로 위기를 돌파하는 장면은 capability_profile.combat이
     "중급" 이상인 경우에만 허용.
   - 탈출 장면: 물리적으로 불가능한 경로(고층 창문, 환기구 등) 대신
     비상 계단, 엘리베이터, 조력자 지원, 사전 준비된 탈출로를 사용할 것.
   - 장소 설비의 격상(문, 벽, 보안 장치)은 이전 화 setting_details 범위 내에서만 허용.
   ```

**수용 기준**:
- `action_focused` BP가 생성한 전투/탈출 장면이 이전 화 설정 및 캐릭터 능력 범위 내에 있음
- BP Preflight에서 환경 물리 + 능력 범위 검증 통과율 확인

**영향 범위**: `blueprint_generator.yaml` (프롬프트 + preflight), Stage 3 context builder (주입), BP Ensemble (전략별 제약)

**의존성**: TF-MS-01 (setting_details 데이터), TF-MS-02 (capability_profile 데이터) — 단, TF-MS-07의 프롬프트 부분은 이 둘 없이도 독립 실행 가능

---

### TF-MS-01: Setting Persistence Layer

**목표**: 주요 장소의 물리적 속성을 에피소드 간 지속시켜 환경 설정 리셋을 방지한다.

**구현 범위**:

1. **ChainLink 확장** (`stage4_orchestrator.py`)
   - 기존 6필드 + `setting_details` dict 추가
   - 구조:
     ```json
     "setting_details": {
       "사무실": {
         "building": "여의도 XX빌딩",
         "floor": "고층",
         "door_type": "강화유리",
         "window_type": "고정 커튼월(개폐 불가)",
         "security": "일반 전자 잠금"
       }
     }
     ```
   - LLM 추출: 원고 확정 시 장소별 물리 속성 자동 추출 (기존 ChainLink 추출 프롬프트 확장)

2. **mandatory_context 주입** (`stage4_context_builder.py`)
   - 다음 화 생성 시 `setting_details`를 ChiefWriter/Director에 주입
   - 포맷: `[장소 설정 제약] 사무실: 문=강화유리, 창=고정(개폐불가), 층수=고층`

3. **Director 검증**
   - 후보 원고가 setting_details와 충돌 시 MAJOR 감점

**수용 기준**: 동일 장소의 문/창문/보안 설비 묘사가 에피소드 간 일관되게 유지됨

**영향 범위**: `stage4_orchestrator.py` (ChainLink 추출), `stage4_context_builder.py` (주입), `director.yaml` (검증 지시)

---

### TF-MS-02: Character Capability Gate

**목표**: 주인공의 능력 프로파일을 정의하고, 프로파일 범위를 벗어나는 행동을 검출한다.

**구현 범위**:

1. **WorldState `protagonist` 확장** (`world_state.py`)
   - `capability_profile` 추가:
     ```json
     "capability_profile": {
       "combat": "없음",
       "martial_arts": "형식적 수련(실전 무경험)",
       "intellect": "상위(18년 미래 지식)",
       "physical": "건강(승마 선수 출신)",
       "special": "미래 기억(2006-2024)"
     }
     ```
   - 초기값: Stage 0 프로젝트 설정 시 사용자 입력 또는 Treatment에서 추출
   - 갱신: `state_changes`에 `capability_update` 키 추가 → 에피소드 내 능력 변화 반영

2. **TruthGate 확장** (`truth_gate.py`)
   - `_check_capability_plausibility()` 신규:
     - 원고에서 전투/격투/탈출 장면 감지 (기존 `injury_patterns` + 신규 `combat_action_patterns`)
     - `capability_profile.combat`이 "없음"/"초급"인데 고급 전투 행동 → MAJOR 경고

3. **ChiefWriter 프롬프트 주입**
   - `[주인공 능력 범위] combat=없음, martial_arts=형식적 → 전문적 격투 장면 금지. 지략/도구/외부 도움으로 위기 해결`

**수용 기준**: combat="없음" 설정 시 전문적 관절기/격투 장면이 생성되지 않음

**영향 범위**: `world_state.py`, `truth_gate.py`, `chief_writer.yaml`, `stage4_context_builder.py`

---

### TF-MS-03: Anti-Cliché Prompt Reinforcement

**목표**: LLM의 장르 클리셰 편향을 프롬프트 수준에서 억제한다.

**구현 범위**:

1. **ChiefWriter `chief_writer.yaml`**
   - 투자물 장르 섹션에 추가:
     ```
     [장르 클리셰 억제]
     - 회귀자라고 해서 자동으로 격투/무술 능력이 생기지 않는다.
       전투 능력은 capability_profile에 명시된 범위만 허용.
     - 실존 건물/기업/기관명 사용 시 작중 연도({timeline_year})에
       해당 건물이 실제로 존재했는지 반드시 확인.
       확신 없으면 가상 명칭 사용.
     - "고층 빌딩 창문으로 탈출", "맨손으로 다수 제압" 등
       물리적으로 불가능한 장면은 지략/도구/조력자 활용으로 대체.
     ```

2. **Blueprint Preflight `blueprint_generator.yaml`**
   - 기존 "Allow minor historical tech anachronisms (±1-5 years)" 조건 강화:
     ```
     실존 건물/기관: 작중 연도 기준 ±2년 이내만 허용.
     ±2년 초과 시 가상 명칭으로 교체 필수.
     ```

3. **`timeline_year` 변수 자동 주입**
   - Stage 2 Arc 생성 시 `treatment.timeline_start_year` → 이후 모든 Stage에 `{timeline_year}` 변수로 전파
   - 프롬프트 내 `{timeline_year}` 치환 → LLM이 항상 현재 작중 연도를 인지

**수용 기준**: 작중 연도에 존재하지 않는 실존 건물명이 생성되지 않음, 능력 범위 밖 전투 장면 미생성

**영향 범위**: `chief_writer.yaml`, `blueprint_generator.yaml`, `stage2_orchestrator.py` (변수 전파)

**비용**: 프롬프트 수정만, 코드 변경 최소

---

### TF-MS-04: NPC Extended Metadata

**목표**: NPC의 직함(title), 말투 패턴, 외모 특징을 추적하여 호칭/묘사 불일치를 방지한다.

**구현 범위**:

1. **FactLedger `characters` 확장** (`fact_ledger.py`)
   - 기존 필드: `status, role, relationship, known_attrs, history`
   - 추가 필드: `title` (직함), `speech_pattern` (말투 요약), `appearance_note` (외모 키워드)
   - 초기 입력: `state_changes`에서 NPC 첫 등장 시 자동 추출

2. **TruthGate 확장** (`truth_gate.py`)
   - `_check_npc_title_consistency()` 신규:
     - 원고 내 NPC 호칭 패턴 추출: `{NPC이름}\s*(팀장|부장|과장|대리|사장|회장|비서|관장|변호사|PB)` 등
     - FactLedger 등록 `title`과 불일치 시 MAJOR 경고
     - 승진/강등 등 의도적 변경은 `state_changes.title_change`로 허용

3. **WorldState `alive_npcs` 확장** (`world_state.py`)
   - `known_attrs`에 `title` 키 자동 포함

**수용 기준**: 등록 직함과 다른 호칭이 원고에 등장 시 TruthGate MAJOR 경고 발생

**영향 범위**: `fact_ledger.py`, `truth_gate.py`, `world_state.py`

---

### TF-MS-05: Director Checklist Expansion

**목표**: Director 9항목 체크리스트를 12항목으로 확장하여 원고 모순 커버리지를 넓힌다.

**구현 범위**:

기존 9항목 유지 + 3항목 추가:

| 번호 | 신규 항목 | 대상 모순 |
|------|----------|----------|
| #10 | **캐릭터 능력 개연성**: 주인공/NPC가 설정된 capability_profile 범위 내에서 행동하는가? 근거 없는 초인적 능력 발현은 MAJOR. | M-04 |
| #11 | **환경 설정 지속성**: 이전 화에서 묘사된 장소의 물리적 속성(문, 창문, 보안, 층수)이 현재 화에서 유지되는가? 갑작스러운 격상/변경은 MAJOR. | M-03, M-05 |
| #12 | **신규 오브젝트 도입 근거**: 이전 화에서 언급/복선 없이 갑자기 등장하는 장치/설비/도구가 있는가? 있다면 설치/획득 경위가 서술되어야 한다. MINOR. | M-07 |

**감점 규칙** (기존 I-10 확장):
- #10 CRITICAL 위반: continuity 15점 캡
- #11 MAJOR 위반: -10점
- #12 MINOR 위반: -3점

**수용 기준**: Director JSON output의 `consistency_checklist`에 `capability_plausibility`, `setting_persistence`, `new_object_provenance` 키 추가

**영향 범위**: `director.yaml` (프롬프트), Director JSON 파서

**비용**: 프롬프트 수정만

---

### TF-MS-06: Protagonist Belief Tracker (P3/INSIGHT)

**목표**: 주인공의 추론/판단/믿음을 별도 추적하여 화간 인식 모순을 방지한다.

**구현 범위**:

1. **WorldState 확장** (`world_state.py`)
   - `protagonist_beliefs[]` 추가:
     ```json
     [
       {"belief": "습격자는 한태준 소속", "established_ep": 5, "status": "unconfirmed"},
       {"belief": "아버지는 직접 개입 안 할 것", "established_ep": 3, "status": "overturned_ep_9"}
     ]
     ```
   - `state_changes.belief_update`로 갱신

2. **Director 주입**: 다음 화 생성 시 `protagonist_beliefs` 목록을 mandatory_context에 포함 → "이전 추론과 모순되는 행동 시 명시적 재평가 장면 필요" 지시

**수용 기준**: 주인공이 이전 판단을 번복할 때 내면 독백 또는 서술로 재평가 근거가 제시됨

**영향 범위**: `world_state.py`, `stage4_context_builder.py`, `director.yaml`

**비용**: 중간, P3 배정

---

## 실행 순서 및 의존성

```
Phase 0 (근본 원인 차단, P0):
  TF-MS-07 프롬프트 부분 (BP action_focused 제약) ──┐
  TF-MS-03 (Anti-Cliché Prompt)                     ├── 프롬프트만, 즉시 실행 가능
  TF-MS-05 (Director Checklist 12항목)               ┘
      ↓
Phase 1 (데이터 인프라):
  TF-MS-01 (Setting Persistence) ──┐
  TF-MS-02 (Capability Gate) ──────┤── 코드 + 프롬프트
  TF-MS-04 (NPC Metadata) ─────────┘
      ↓
Phase 1.5 (인프라 연동):
  TF-MS-07 코드 부분 (BP에 setting_details + capability_profile 주입)
      ↓
Phase 2 (후순위):
  TF-MS-06 (Belief Tracker, P3)
```

**Phase 0** (프롬프트만, 코드 변경 없음, 즉시 실행):
- TF-MS-07 프롬프트 부분: `blueprint_generator.yaml`에 action_focused 전략 제약 + preflight 3항목 추가
- TF-MS-03: Anti-Cliché Prompt (ChiefWriter + Blueprint)
- TF-MS-05: Director Checklist 9→12항목

**Phase 1** (코드 + 프롬프트):
- TF-MS-01: Setting Persistence (ChainLink 확장)
- TF-MS-02: Capability Gate (WorldState + TruthGate)
- TF-MS-04: NPC Extended Metadata (FactLedger + TruthGate)

**Phase 1.5** (Phase 0 + Phase 1 연동):
- TF-MS-07 코드 부분: BP Ensemble에 setting_details + capability_profile 데이터 주입

**Phase 2** (후순위):
- TF-MS-06: Belief Tracker

---

## LLM 고유 한계 vs 시스템 개선 가능 판정 요약

| 모순 | LLM 한계 비중 | 시스템 개선으로 해소 가능 비중 | 잔여 리스크 |
|------|-------------|--------------------------|-----------|
| M-01 호칭 오타 | 30% (soft-token confusion) | **70%** (Python 직함 교차검증) | 매우 낮음 |
| M-02 IFC 역사 | 60% (사실 환각) | **40%** (timeline_year 주입 + 프롬프트) | 중간 — 완전 제거 불가 |
| M-03 문 격상 | 40% (escalation bias) | **60%** (ChainLink setting_details) | 낮음 |
| M-04 전투 능력 | 50% (장르 클리셰) | **50%** (capability_profile + 프롬프트) | 중간 — 미묘한 능력 초과는 잔존 |
| M-05 창문 탈출 | 70% (물리 추론 한계) | **30%** (설정 제약 주입 + Director) | 중간 — 모든 물리 시나리오 열거 불가 |
| M-06 정체 혼란 | 50% (컨텍스트 드리프트) | **50%** (belief tracker) | 낮음 |
| M-07 스위치 시점 | 40% (편의적 플로팅) | **60%** (Director #12 + 프롬프트) | 낮음 |

**종합**: 7건 중 **5건은 시스템 개선으로 대부분 해소 가능**. M-02(역사 사실)와 M-05(물리 추론)는 LLM 고유 한계 비중이 높아 완전 제거는 불가하나, 프롬프트 강화로 **발생 빈도를 유의미하게 낮출 수 있다.**

---

## 에스컬레이션 로깅 체계 감사 (TF-MS-08)

### 현행 에스컬레이션 경로

```
REJECT 발생
  ↓
error_category 판정:
  - Director 직접 REJECT → _classify_reject_bucket()
      → quality_issue / constraint_violation / structure_error
  - A-3 post-select conflict → LOGIC_ERROR (강제 설정)
  - _is_continuity_replay_reject() → LOGIC_ERROR (강제 설정)
  ↓
_logic_error_streak 카운터 (LOGIC_ERROR일 때만 증가)
  ↓
V75-D (streak >= 2, quality_risk면 1):
  BP inplace 패치
  로그: (1) ui.log (2) log_patch_diff (3) _log_escalation_event → JSONL
  ↓ (실패 후 계속 LOGIC_ERROR)
V75-B (streak >= 2 + inplace 시도 완료):
  BP 전면 재생성 (_regenerate_blueprint)
  로그: (1) ui.log (2) _log_escalation_event → JSONL
```

### 로깅 갭 5건

| # | 갭 | 심각도 | 영향 |
|---|-----|--------|------|
| **G-1** | V75-B 전면 재생성 시 **diff 로깅 없음** — V75-D는 `log_patch_diff()` 호출하지만 V75-B(L1278~1307)에는 diff 코드 없음 | IMPORTANT | 재생성 전/후 BP 차이 추적 불가 |
| **G-2** | 변경 전 BP **artifact 백업 미저장** — V75-D/V75-B 모두 `round_ctx` 교체만 하고 원본 BP를 파일로 보존하지 않음 | IMPORTANT | 사후 감사 시 원본 BP 복원 불가 |
| **G-3** | `_log_escalation_event` **실패 시 silent** — L1372 `logging.warning`으로만 남기고 계속 진행. JSONL 쓰기 실패하면 이벤트 유실 | MINOR | 드문 경우지만 에스컬레이션 기록 소실 |
| **G-4** | **error_category 분류 사각지대** — Director가 연속성 모순으로 REJECT해도 `_classify_reject_bucket()`이 `quality_issue`로 분류하면 LOGIC_ERROR streak에 불참 → V75-D/V75-B 트리거 불발 | **CRITICAL** | 이 세션에서 물리적 모순이 에스컬레이션을 타지 못한 근본 원인 |
| **G-5** | **Director PASS 시 에스컬레이션 경로 자체가 없음** — Director가 물리적 모순을 인지 못하고 PASS하면, REJECT가 발생하지 않으므로 에스컬레이션 체인 진입 자체가 불가 | **CRITICAL** | 이 세션의 M-03~M-05, M-07이 모두 Director PASS로 통과된 이유 |

### 이 세션(00_260315)에서의 실제 동작

| 화 | Director 판정 | error_category | streak | 에스컬레이션? |
|----|-------------|----------------|--------|------------|
| 7화 | **PASS/90** (모순 미감지) | — | 0 | 진입 불가 |
| 8화 a1 | REJECT/30 (분량 미달) | — (`quality_issue`) | 0 | LOGIC_ERROR 아님 |
| 8화 a2 | PASS/93 | — | 0 | — |
| 10화 a1 | REJECT→PASS/98 (post-select conflict) | LOGIC_ERROR | 1 | streak < 2, 미트리거 |
| 10화 a2 | PASS/90 | — | 0 (리셋) | — |

**결론**: V75-B 전면 재생성은 이 세션에서 **한 번도 트리거되지 않았다.** 이유:
1. 물리적 모순(M-03~M-05)을 Director가 PASS로 통과시킴 (G-5)
2. 유일한 LOGIC_ERROR(10화 a1)가 1회 뿐이라 streak < 2
3. 분량 미달 REJECT(8화, 11화)는 `quality_issue`로 분류되어 streak 불참 (G-4)

### TF-MS-08: Escalation Logging & Trigger Gap Remediation

**목표**: 에스컬레이션 로깅의 5개 갭을 해소하고, Director PASS 시에도 물리적 모순이 감지되면 에스컬레이션 경로에 진입할 수 있도록 한다.

**심각도**: CRITICAL / **우선순위**: P1

**구현 범위**:

1. **G-1 해소**: V75-B `_regenerate_blueprint()` 호출 전후에 `log_patch_diff("S4-V75B-Blueprint", ...)` 추가
   - 위치: `stage4_orchestrator.py` L1284 앞에 diff 로깅 삽입
   - V75-D와 동일한 패턴 (`_json_mod.dumps` + `log_patch_diff` + `calc_patch_change_ratio`)

2. **G-2 해소**: V75-D/V75-B 진입 시 원본 BP를 artifact로 저장
   - `logs/artifacts/stage4/ep_{N}/attempt_{M}/original_blueprint_before_escalation.json`
   - 위치: V75-D L1229 앞, V75-B L1278 앞

3. **G-3 해소**: `_log_escalation_event` 실패 시 세션 로그에도 이벤트 기록
   - L1372 `logging.warning` → `logging.error` + `self.ctx.ui.log("⚠️ [V76] escalation log 쓰기 실패")`
   - 최소한 세션 로그에는 남도록 보장

4. **G-4 해소**: `_classify_reject_bucket`에 연속성/물리 모순 분류 추가
   - Director feedback에 "모순", "연속성", "설정 불일치", "물리적", "contradiction" 등의 키워드가 있으면 `constraint_violation` 대신 **`logic_error` 버킷으로 분류** → `error_category = "LOGIC_ERROR"` 설정
   - 이렇게 하면 Director가 연속성 문제로 REJECT할 때 streak에 정상 참여

5. **G-5 해소**: TruthGate CRITICAL 경고 시 Director PASS 오버라이드 검토
   - 현재: TruthGate CRITICAL → Director에 "반드시 REJECT" 지시 (프롬프트) → 그러나 Director가 무시 가능
   - 개선: TruthGate CRITICAL 경고가 있는데 Director가 PASS한 경우, **post-select에서 강제 REJECT** (A-3 패턴 확장)
   - 위치: `stage4_interview_round.py` post-select validation 확장
   - **단, TF-MS-02(capability_profile) + TF-MS-01(setting_details)이 먼저 구현되어야 TruthGate가 물리적 모순을 감지할 수 있음**

**수용 기준**:
- V75-B 발생 시 diff 로그 + 원본 BP artifact가 남음
- Director가 연속성 모순으로 REJECT 시 LOGIC_ERROR streak에 정상 참여
- TruthGate CRITICAL + Director PASS 조합이 post-select에서 강제 REJECT

**영향 범위**: `stage4_orchestrator.py` (G-1~G-3), `stage4_interview_round.py` (G-4~G-5)

---

## Status Ledger

| TF | Status | Phase | Blocker |
|----|--------|-------|---------|
| TF-MS-07 (프롬프트) | pending | 0 | none — 즉시 실행 가능 |
| TF-MS-03 | pending | 0 | none — 즉시 실행 가능 |
| TF-MS-05 | pending | 0 | none — 즉시 실행 가능 |
| TF-MS-08 (G-1~G-3) | pending | 0.5 | none — 로깅 코드만, 즉시 실행 가능 |
| TF-MS-01 | pending | 1 | none |
| TF-MS-02 | pending | 1 | none |
| TF-MS-04 | pending | 1 | none |
| TF-MS-08 (G-4~G-5) | pending | 1.5 | TF-MS-01 + TF-MS-02 필요 (TruthGate 확장 의존) |
| TF-MS-07 (코드) | pending | 1.5 | TF-MS-01 + TF-MS-02 완료 필요 |
| TF-MS-06 | pending | 2 | TF-MS-01~08 완료 후 |

---

## Cleanup Rule
- Phase 1 완료 시: 원고 재생성 후 M-02/M-04/M-05 재현 여부 검증
- Phase 2 완료 시: 11화 전체 재생성 후 전 항목 재점검 → `원고_모순점검_00_260315.md` 갱신
- 전 Phase 완료 시: 이 문서를 completed로 변경, 결과를 execution-roadmap에 반영
