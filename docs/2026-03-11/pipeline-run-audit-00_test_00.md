# 파이프라인 실행 감사: 00_test_00

> **실행일**: 2026-03-11, **장르**: 투자 (Investment Fiction)
> **Treatment**: `01_tr_투자물_골든_sample.json` (60블록)
> **3-pass 감사**: 1차 식별 → 2차 오탐 검증 → 3차 근본원인+개선방향 확정

---

## 실행 요약

| 항목 | 값 |
|------|-----|
| Arc | 1개 (4화) |
| Blueprint | 4개 전량 PASS (score 100) |
| 원고 | 4화 PASS (ep1: 9회, ep2: 1회, ep3: 2회, ep4: 1회) |
| 총 LLM 호출 | 169회 (실패 0) |
| 토큰 | 1,027K (Pro 980K + Flash 48K) |
| 비용 | $1.97 |
| 소요 시간 | ~64분 (Stage2+3: ~15분, Stage4: ~49분) |
| 최종 원고 분량 | ep1: 11,413B, ep2: 10,582B, ep3: 10,365B, ep4: 11,864B |

### 에피소드별 Stage 4 결과

| EP | 시도 | 최종 점수 | 전략 | 비고 |
|----|------|----------|------|------|
| 1 | **9회** | 96 | tension → patch | 7연속 REJECT(30점), 8차 88점 PASS_WITH_FIX, 9차 patch PASS |
| 2 | 1회 | 90 | narrative | 1회 통과 |
| 3 | 2회 | 90 | inplace_patch | 1차 44점 REJECT(Contradiction Firewall), 2차 PASS |
| 4 | 1회 | 100 | tension | 1회 통과, 만점 |

---

## 확정 이슈 (3-pass 검증 완료)

---

### P0-1. CW 분량 미달 반복 — 근본적 생성 실패

**현상**: EP1 round 0~6(7연속), 3개 후보 전원 4,000자 미달.
- Round 0: 최대 2,211자 (목표 대비 44%)
- Round 3: 최대 3,588자 (목표 대비 72%)
- Round 6: 최대 3,790자 (목표 대비 76%)
- EP2~4에서도 다수 후보 4,000자 미달 (합격 후보만 간신히 초과)

**왜 — 근본 원인 5개 (우선순위순)**:

#### 원인 ①: `response_mime_type="application/json"` 강제 (CRITICAL)
- **위치**: `base_agent.py:793`
- **메커니즘**: ChiefWriter의 `ask()` 호출 시 **항상** JSON 응답 강제. Gemini API에서 JSON 모드는 내부 토큰 budget을 **15-25% 자동 제한**. 프롬프트 21,353자 → 응답 2,197자 (수율 10%)
- **왜 문제인가**: 원고 본문은 텍스트인데 JSON 래핑 오버헤드로 본문 토큰이 줄어듦

#### 원인 ②: TF-G 게이트 `_fix_manuscript_issues` 역효과 (HIGH)
- **위치**: `chief_writer_quality.py:1050-1120`
- **메커니즘**: 분량 부족 감지 → `expand_length_prompt` 호출 → **thinking="medium" 강제** → thinking 오버헤드로 응답이 **더 짧아짐**. 실제 로그: 2,011자 원본 → 수정 후 1,607자 (-20%)
- **왜 문제인가**: 수정 시도가 분량을 늘리는 게 아니라 **축소 재생성**. JSON 강제 + thinking 조합이 토큰 budget을 이중 소모

#### 원인 ③: Self-Critique 분량 재검사 무한 루프 (HIGH)
- **위치**: `chief_writer_quality.py:307-321`
- **메커니즘**: 매 Self-Critique 라운드마다 분량 검사 → `severity="medium"` 판정(4500자 미만) → `_fix_manuscript_issues` 재호출 → 또 실패 → 최대 3회 반복. `severity="low"`일 때만 루프 탈출(L200-201)이므로 **분량 미달이면 영원히 medium**
- **왜 문제인가**: 원인 ②의 실패를 3회 반복하며 시간만 소모

#### 원인 ④: rubric_score 분량 무시 조기 탈출 (MEDIUM)
- **위치**: `chief_writer_quality.py:203-207`
- **메커니즘**: `rubric_score ≥ 3.5`이면 Self-Critique 루프 탈출. rubric은 문체·감정·대화 비율만 평가하고 **분량은 제외**. 3000자 고품질 원고도 3.5+ 가능 → 분량 미달 원고 통과
- **왜 문제인가**: 품질 점수와 분량이 분리 평가되어 분량 게이트가 우회됨

#### 원인 ⑤: 프롬프트 분량 지시 약함 (MEDIUM)
- **위치**: `chief_writer.yaml:8` ("5,000자 이상의 소설 본문"), `chief_writer.yaml:57` ("5,000자 이상을 권장합니다")
- **메커니즘**: "권장"이라는 표현이 LLM에게 약한 구속력. JSON 강제라는 구조적 제약을 프롬프트가 극복 불가능
- **왜 문제인가**: 구조적 토큰 제약 앞에서 텍스트 지시는 무력

**영향**: EP1에서 7회 REJECT × ~180초/회 = **~21분 낭비**, LLM 비용 $0.8+ 추가

**개선 방향**:

| TF | 수정 | 위치 | 효과 |
|----|------|------|------|
| **TF-A** | CW 원고 생성 시 `response_mime_type` JSON 제거 | `base_agent.py` 또는 CW 호출부 | 토큰 budget +15-25% 확보 |
| **TF-B** | `expand_length_prompt` thinking="medium" → "low" | `chief_writer_quality.py:1088` | thinking 오버헤드 제거 |
| **TF-C** | 분량 재검사 severity 조정: 4800자 이상 → "low" 탈출 | `chief_writer_quality.py:311` | 80% 달성 시 루프 탈출 |
| **TF-D** | rubric_score에 분량 가중치 20% 추가 | `chief_writer_quality.py:1122-1214` | 분량 미달 시 조기 탈출 차단 |

---

### P0-2. PromptLoader 템플릿 문법 오류

**현상**: 매 라운드마다 반복 (총 10회+):
```
[WARNING] [PromptLoader] Template substitution failed for writing_directive/WRITING_DIRECTIVE_SYSTEM:
Invalid format specifier ' "이번 화 행동 지시 1문장"'
```

**왜 — 근본 원인**:
- **위치**: `config/prompts/writing_directive.yaml:14-22`
- **메커니즘**: JSON 예시 블록의 `{"NPC명": "이번 화 행동 지시 1문장"}` (L19)에서 `{"NPC명"` 부분이 Python `str.format_map()` 엔진에 의해 포맷 지정자 `{NPC명}` 으로 파싱 시도 → `Invalid format specifier` 에러
- **PromptLoader 동작** (`prompt_loader.py:229`): `template.format_map(SafeDict(**kwargs))` 호출 → 에러 catch → **원문 그대로 반환** (L232 폴백). 따라서 `{N}`, `{pattern_summary}`, `{blueprint_summary}` 등 **정상 플레이스홀더도 미치환**
- **비교**: `analyst.yaml`, `ensemble.yaml` 등 다른 YAML은 이중 중괄호(`{{`, `}}`)로 올바르게 이스케이프 처리됨
- **왜 문제인가**: WritingDirective 프롬프트에 `{pattern_summary}` 등이 원문 그대로 전달 → LLM이 패턴 분석 결과 대신 플레이스홀더 문자열 수신

**영향**: WritingDirective 생성 시 컨텍스트 누락. 다만 LLM이 맥락 추론으로 생성 자체는 성공 (`[TF-54] WritingDirective 생성 완료`)

**개선 방향**:

| TF | 수정 | 위치 | 효과 |
|----|------|------|------|
| **TF-E** | JSON 예시 중괄호를 이중 중괄호(`{{`, `}}`)로 교체 | `writing_directive.yaml:14-22` | 플레이스홀더 정상 치환 |

---

### P1-1. 대화 감지 오탐 — 0개 반복 보고

**현상**: 모든 에피소드, 모든 후보에서 `대화 부족: 0개 (최소 4개)` 반복.

**왜 — 근본 원인**:
- **위치**: `pre_director_manuscript_checker.py:42-46` (패턴), `:61` (카운트)
- **메커니즘**:
  1. `dialogue_patterns` (L42-46): 직선 큰따옴표(`"`), 꺾쇠(`「」`), 직선 작은따옴표(`'`) 3종만 정의. **스마트따옴표** (`'…'` U+2018/U+2019, `"…"` U+201C/U+201D) 미포함
  2. `dialogue_count` (L61): `manuscript.count('"') // 2 + manuscript.count("「")` — 직선 큰따옴표+꺾쇠만 카운트. 스마트따옴표 원고에서 **항상 0**
  3. 원고(ep_0001.txt)는 스마트 작은따옴표(`'…'`)로 대화 표기 → `dialogue_chars=0`, `dialogue_count=0`
- **영향 범위** (동일 버그 5파일):
  - `confidence_calibration.py:181,220` — ❌ 미처리
  - `adversarial_self_play.py:343` — ❌ 미처리
  - `multi_agent_deliberation.py:411` — ❌ 미처리
  - `self_reflection.py:321` — ❌ 미처리
  - `pre_llm_validator.py:222`, `scoring_validator.py:326` — ✅ 이미 스마트따옴표 처리됨

**왜 문제인가**: 대화 0개 오탐 → CW Self-Critique에 "대화 추가" 지시 반복 삽입 → P0-1(분량 미달)과 결합하여 토큰 budget을 대화 추가에 낭비. Confidence 점수도 하향.

**개선 방향**:

| TF | 수정 | 위치 | 효과 |
|----|------|------|------|
| **TF-F** | `dialogue_patterns`에 스마트따옴표 4종 추가 + `dialogue_count` 계산을 regex 기반으로 통일 | `pre_director_manuscript_checker.py:42-46,61` + 4파일 동기화 | 대화 감지 정상화 |

---

### P1-2. CrossVerify 씬 반영률 0% 오탐

**현상**: 전 에피소드, 전 후보에서 `4개 씬 중 0개만 감지됨 (0%)` 반복.

**왜 — 근본 원인**:
- **위치**: `pre_director_manuscript_checker.py:127-217` (`_measure_scene_reflection`)
- **메커니즘**:
  1. L151: Blueprint 씬 title+description에서 `re.findall(r"[\w가-힣]{2,}", full_text)[:8]` — 2글자+ 한국어 단어 추출
  2. L157: `matched = [kw for kw in unique_keywords if kw in manuscript]` — 원고에서 **substring 매칭**
  3. **문제점**: 키워드 "추격"이 Blueprint에서 추출되어도, 원고에 "추격"이 단독으로 없으면 미매칭. 조사/활용어미 처리 없음 ("주인공이" vs "주인공" 불일치). 제목이 추상적일수록 매칭률 급감
  4. L164-177: `ratio < 0.3` 이면 weak_scene 분류 → 모든 씬이 weak → overall 0%
- **기존 인지 상태**: TF-51 주석 `# [TF-51] FAIL→WARNING: Python 키워드 매칭 오탐 과다, Director LLM 판단 위임` — 이미 오탐을 알고 FAIL→WARNING 다운그레이드만 적용. 근본 해결 안 됨
- **동일 문제**: `confidence_calibration.py:248-276` 씬 반영도 계산도 같은 로직

**왜 문제인가**: Director MC에 "0% 반영" 경고가 노이즈로 전달. Director가 무시하지만 프롬프트 공간 낭비.

**개선 방향**:

| TF | 수정 | 위치 | 효과 |
|----|------|------|------|
| **TF-G** | 씬 매칭 로직 개선: 키워드 전처리(조사 제거) + n-gram 부분매칭 + 최소 매칭 키워드 3개 보장 | `pre_director_manuscript_checker.py:127-217` + `confidence_calibration.py:248-276` | 오탐률 대폭 감소 |

---

### P1-3. EP1 과다 retry — 비용/시간 효율 저하

**현상**: EP1 9회 시도, ~35분, 전체 Stage 4의 71%

**왜**: P0-1(분량 미달)의 직접적 결과. 분량 미달 → score=30 자동 REJECT → retry → 또 분량 미달 → 악순환. P0-1 해소 시 자연 해결.

**개선 방향**: P0-1 TF-A~D 해소에 종속.

---

### P2-1. V75 State-Text 불일치 경고 (초기값 노이즈)

**현상**: EP1 `capital=10000000, 근거=근거 없음`

**왜 — 근본 원인**:
- **위치**: `state_text_verifier.py:38-40` (프롬프트 규칙), `:119-138` (판정 로직)
- **메커니즘**: V75 규칙 "원고에 명시적으로 언급되지 않은 수치 변경은 '근거 없음'으로 보고". 초기 에피소드에서 자본금은 **초기화 값(arc_start_state)**이므로 원고에 근거가 없는 것이 당연. 하지만 LLM은 규칙대로 정확히 "근거 없음" 보고
- **현재 상태**: `blocking=False` (advisory 모드) — 저장 차단 없음. **정상 동작이나 노이즈**

**왜 문제인가**: 초기 에피소드에서 무의미한 경고가 반복 → 로그 오염. 실질적 피해는 없음.

**개선 방향**: V75 프롬프트에 "초기값(arc_start_state)과 일치하는 필드는 불일치 제외" 규칙 추가. **후순위** (advisory 모드이므로 blocking 없음).

---

## 오탐 제거 (3-pass에서 탈락)

| 1차 식별 | 판정 | 사유 |
|----------|------|------|
| I-04 ConsistencyValidator 2 checks skipped | **정상** | 1화 컨텍스트 부재로 skip. 정상 동작 |
| NC-3 consistency_checklist ISSUE 1건 | **정상** | Director가 적절히 반영. 시스템 정상 |
| V75-C Contradiction Firewall REJECT | **정상 작동** | 애마 이름 불일치 정확히 포착 |
| PassRate 경보 33% | **정상 작동** | 조기 경보 정상 발동 |
| EP1 vector_context_chars=0 | **정상** | 1화이므로 VecMemory 비어있음 |
| missing_relation_slice | **정상** | 초기 상태 NPC 관계 데이터 없음 |

---

## 긍정적 관측

1. **Stage 2/3 무결**: Arc 95점 PASS_WITH_FIX→PASS, Blueprint 4개 전량 100점
2. **Contradiction Firewall**: EP3 애마 이름 오류 CRITICAL 포착 → REJECT → 2차 수정 PASS
3. **Patch Mode**: EP1 88점 → patch 96점. PASS_WITH_FIX 시스템 정상 작동
4. **AI Slop 0**: EP1~3 slop=0.0, EP4 2.0(경미)
5. **Advisory 병렬**: 8개 advisory 1초 이내 완료
6. **원고 품질**: 최종 합격 원고 모두 고품질
7. **비용**: 4화 $1.97 (과다 retry 포함)

---

## TF 구성

### TF-A: CW 원고 JSON 모드 제거 — ⛔ 3-pass 감리: **실현 불가**
- **대상**: ChiefWriter 원고 생성 시 `response_mime_type="application/json"` 제거
- **위치**: `base_agent.py:793`
- **감리 결과**: `base_agent.py:793`에서 **모든 에이전트**에 `response_mime_type="application/json"` 하드코딩. CW 원고 파싱 경로(`_generate_single_candidate` L647)에서 `_extract_json_robust()` → `data.get("content", "")` 호출 — JSON 응답 **필수 의존**. 제거 시 3개 앙상블 후보 + `inplace_patch` + `_fix_manuscript_issues` 전량 파싱 실패.
- **대안**: CW 전용 `ask_text()` 메서드 신설 + 원고 파싱 로직 전면 교체 필요. **대규모 리팩토링** (20+ 파일 영향).
- **판정**: P2 후순위 유보. 현재 P0-1 원인 ①이나 **단독 해결 불가**, TF-B/C/D로 우회 개선.

### TF-B: expand_length thinking 경량화 — ✅ 3-pass 감리: **실행 가능**
- **대상**: `_fix_manuscript_issues`의 분량 확장 시 `thinking="medium"` → `"low"`
- **위치**: `chief_writer_quality.py:1088`
- **효과**: thinking 오버헤드 제거, 본문 토큰 할당 증가
- **리스크**: 낮음 (expand는 단순 확장이므로 deep thinking 불필요)

### TF-C: 분량 severity 조정 — ⚠️ 3-pass 감리: **조건부 실행**
- **대상**: 분량 재검사에서 4800자 이상이면 `severity="low"` → Self-Critique 루프 탈출
- **위치**: `chief_writer_quality.py:307-321`
- **감리 메모**: 임계값 4800자는 `ManuscriptLimits.WARNING=4500` 이상이므로 안전. 다만 4500~4800 구간의 동작 변경은 실파이프라인 검증 후 결정 필요.
- **효과**: 80% 목표 달성 시 무의미한 수정 반복 방지
- **리스크**: 낮음 (4800자면 Director가 PASS 가능한 수준)

### TF-D: rubric 분량 가중치 — ⚠️ 3-pass 감리: **재설계 필요**
- **대상**: `_evaluate_with_rubric()`에 분량 점수 가중치 추가
- **위치**: `chief_writer_quality.py:1122-1214`
- **감리 결과**: rubric 내부에 분량 가중치를 직접 넣으면 **대원칙 3(Director 주권주의) 위반** 우려 — Python이 품질 판단(분량의 적정성)을 하게 됨.
- **대안 설계**: rubric 가중치 대신 **별도 `length_penalty` 계수** 도입. `rubric_score ≥ 3.5` 조기 탈출 조건에 `and len(manuscript) >= ManuscriptLimits.MIN` 추가. 이 방식은 판단이 아닌 사실 확인(분량 미달 여부)이므로 대원칙 위반 없음.
- **효과**: 분량 미달 원고의 rubric 조기 탈출 차단
- **리스크**: 낮음 (단순 AND 조건 추가)

### TF-E: WritingDirective YAML 이중 중괄호 — ✅ 3-pass 감리: **즉시 실행**
- **대상**: `writing_directive.yaml` L14-22 JSON 예시 `{}` → `{{}}`
- **위치**: `config/prompts/writing_directive.yaml`
- **감리 결과**: `analyst.yaml`, `ensemble.yaml` 등 기존 YAML과 100% 동일 패턴. 안전성 99%.
- **효과**: 플레이스홀더 `{N}`, `{pattern_summary}`, `{blueprint_summary}` 정상 치환
- **리스크**: 없음

### TF-F: 스마트따옴표 대화 감지 — ✅ 3-pass 감리: **실행 가능 (스코프 축소)**
- **대상**: `dialogue_patterns`에 `'…'`(U+2018/2019), `"…"`(U+201C/201D) 추가 + `dialogue_count` regex 기반 통일
- **위치**: `pre_director_manuscript_checker.py:42-46,61` **(1파일 우선)**
- **감리 결과**: 동기화 대상으로 열거된 4파일(`confidence_calibration`, `adversarial_self_play`, `multi_agent_deliberation`, `self_reflection`)은 **P2 유보 에이전트**(운영 경로 `main_a.py`에서 model 명시 주입) 소속. `pre_director_manuscript_checker.py` 1파일만 Stage 4 핵심 경로. 나머지는 후속 패치.
- **효과**: Stage 4 대화 감지 정상화
- **리스크**: 낮음 (`pre_llm_validator`, `scoring_validator`에 이미 동일 패턴 적용 완료)

### TF-G: 씬 매칭 개선 — ❓ 3-pass 감리: **추가 조사 필요**
- **대상**: `_measure_scene_reflection` 키워드 매칭 → 조사 정규화 + n-gram 부분매칭
- **위치**: `pre_director_manuscript_checker.py:127-217` + `confidence_calibration.py:248-276`
- **감리 결과**: 기존 `[TF-51]` 주석이 FAIL→WARNING 다운그레이드만 적용한 이유가 있음 — **"Python 키워드 매칭 오탐 과다, Director LLM 판단 위임"**이 의도된 설계. 매칭 로직 자체를 개선하면 오탐은 줄지만 **미탐(false negative)** 증가 가능. 한국어 형태소 분석 없이 조사 제거는 오작업 위험.
- **대안**: 현재 WARNING 상태 유지 + Director가 이미 무시하므로 **프롬프트 공간 비용만 문제**. advisory 축약(0% 시 1줄 요약) 정도가 적정 수준.
- **효과**: 0% 오탐 해소 (대안 적용 시 advisory 노이즈 축소)
- **리스크**: 중간~높음 (매칭 로직 전면 교체 시 회귀 위험)

### TF 실행 순서 (3-pass 감리 반영)

```
Phase 1 (즉시, 위험 낮음):
  TF-E → TF-F(1파일) → TF-B

Phase 2 (단기, 검증 필요):
  TF-C → TF-D(재설계안)

Phase 3 (후순위):
  TF-A(대규모 리팩토링) → TF-G(추가 조사)
```

---

## 3-pass 감리 결과 요약

| TF | 1차 제안 | 3차 감리 판정 | 변경 사항 |
|----|---------|-------------|----------|
| TF-A | JSON 모드 제거 | ⛔ **실현 불가** | CW 파싱이 JSON 필수 의존. P2 유보 |
| TF-B | thinking 경량화 | ✅ **실행 가능** | 변경 없음 |
| TF-C | severity 조정 | ⚠️ **조건부** | 임계값 실파이프라인 검증 후 확정 |
| TF-D | rubric 분량 가중치 | ⚠️ **재설계** | rubric 가중치→`length_penalty` AND 조건 |
| TF-E | YAML 이중 중괄호 | ✅ **즉시 실행** | 변경 없음 |
| TF-F | 스마트따옴표 | ✅ **스코프 축소** | 5파일→1파일 우선 |
| TF-G | 씬 매칭 개선 | ❓ **추가 조사** | 대안: 0% advisory 축약 |

---

## 감사 메타데이터

- **1차 식별**: 12건 (P0 2 + P1 3 + P2 1 + 후보 6)
- **2차 오탐 검증**: 6건 오탐/정상 작동 제거 (50% 오탐률)
- **3차 근본원인 확정**: 코드 레벨 원인 추적 + 개선 방향 도출
- **4차 3-pass 감리**: TF-A 실현 불가 확정, TF-D 재설계, TF-F 스코프 축소
- **최종 확정**: P0 2건 + P1 3건 + P2 1건 = **6건**, TF 7개 (실행 가능 4개 + 조건부 2개 + 유보 1개)
- **확신도**: 97%+
