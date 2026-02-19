# Codex 오더: Gemini 컨텍스트 최대 활용 조사

> 이 문서는 Codex에게 **Gemini 컨텍스트 과소공급 문제**를 조사시키기 위한 지시서입니다.
> 목표: 각 Stage에서 Gemini에 주입되는 컨텍스트가 어디서 얼마나 손실/절삭되는지 전수 조사.

---

## 배경

이 시스템은 Gemini API(200K 컨텍스트)로 웹소설을 자동 생성합니다.
현재 문제: **200K를 충분히 쓰지 못하고 있음.**
벡터 메모리는 제목만 저장하고, 원고 연속성 검사는 10화×2000자만 사용하고,
200K 절삭은 앞에서부터라 최신 화가 잘리는 등 — 컨텍스트가 얇게 들어가는 지점이 다수 존재.

---

## 조사 범위

### 1단계: 컨텍스트 주입 경로 전수 매핑

**모든 LLM 호출 지점**을 찾아서, 각 호출에 들어가는 컨텍스트를 분석하세요.

조사 대상 파일 (우선순위순):
```
# Stage 4 — 원고 생성 (가장 많은 컨텍스트 필요)
modules/core/stage4_context_builder.py    ← 컨텍스트 조립 핵심
modules/core/stage4_orchestrator.py       ← mandatory_context 절삭
modules/core/stage4_interview_round.py    ← 모순검사 컨텍스트
modules/core/stage4_post_processor.py     ← 벡터 메모리 저장
modules/domain/agents/chief_writer.py     ← Writer LLM 호출
modules/domain/agents/chief_writer_context.py  ← Writer 프롬프트 컨텍스트

# Director 심사 — 모순 판정 컨텍스트
modules/domain/agents/director.py
modules/domain/agents/director_continuity.py  ← 연속성 심사
modules/domain/agents/director_ensemble.py    ← 앙상블 심사
modules/domain/agents/director_prompts.py     ← 프롬프트 템플릿

# Stage 2 — Arc 설계
modules/core/stage2_orchestrator.py
modules/core/stage2_preflight.py
modules/domain/agents/analyst.py          ← Arc 설계 LLM 호출

# Stage 3 — Blueprint
modules/core/stage3_orchestrator.py
modules/domain/agents/blueprint_ensemble.py

# 벡터 메모리
modules/core/vec_memory.py                ← 저장/검색 로직

# 상태 시스템
modules/core/world_state.py
modules/core/fact_ledger.py
modules/domain/agents/state_tracker.py
modules/domain/agents/state_extractor.py

# 기반
modules/domain/agents/base_agent.py       ← ask(), context caching
```

### 각 LLM 호출마다 기록할 항목

| 항목 | 설명 |
|------|------|
| **파일:라인** | 정확한 위치 |
| **호출 메서드** | `self.ask()`, `self._ask_with_cached_context()` 등 |
| **호출 목적** | "원고 생성", "모순 검사", "Arc 설계" 등 |
| **주입 컨텍스트 목록** | 어떤 데이터가 프롬프트에 들어가는지 (이전 원고, 세계 상태, NPC 정보 등) |
| **각 컨텍스트의 크기 제한** | 절삭 기준 (글자수, 화수, 토큰 등) |
| **절삭 방향** | 앞에서 자름 / 뒤에서 자름 / 요약 대체 |
| **실제 활용률 추정** | 200K 중 실제 몇 % 정도 채워지는지 |

---

### 2단계: 손실 지점 분류

조사 결과를 아래 카테고리로 분류하세요:

#### A. 저장 시점 손실 (데이터가 처음부터 빈약하게 저장됨)
- 벡터 메모리 summary가 제목 수준인 문제
- Arc 요약이 너무 짧은 문제
- 에피소드 요약이 핵심 정보를 빠뜨리는 문제

#### B. 조회 시점 손실 (저장은 됐는데 조회 시 잘림)
- lookback 화수 제한 (10화, 30화 등)
- 화당 글자수 제한 (200자, 2000자 등)
- 벡터 검색 결과 개수 제한

#### C. 조립 시점 손실 (조회는 됐는데 프롬프트에 넣을 때 잘림)
- 200K 절삭 (앞/뒤 방향)
- mandatory_context 50K 제한
- 개별 섹션 글자수 하드코딩

#### D. 비활성 경로 (구현됐지만 사용 안 됨)
- ChainOfVerification 미호출
- use_summary 파라미터 미활용
- context caching 미적용 에이전트

#### E. 불균형 (일부 컨텍스트만 과다, 나머지 부족)
- 이전 원고 전문이 대부분의 토큰을 차지
- NPC 정보가 상대적으로 부족
- 세계 상태/팩트 원장 비율이 낮음

---

### 3단계: Stage별 컨텍스트 예산 분석

각 Stage에서 Gemini에 전달되는 컨텍스트를 **토큰 예산표**로 정리하세요:

```
예시 형식:

## Stage 4 — Chief Writer 원고 생성 호출
총 예산: ~200K tokens (≈ 500K chars 한국어)

| 컨텍스트 항목 | 현재 크기 | 제한 방식 | 실제 사용 예상 |
|---------------|-----------|-----------|----------------|
| 시스템 프롬프트 | ~2K | 고정 | 2K |
| 이전 원고 전문 | ~200K | 앞에서 절삭 | 150K~200K |
| 세계 상태 | ~5K | 전체 주입 | 5K |
| NPC 팩트시트 | ~10K | 전체 주입 | 10K |
| 벡터 검색 결과 | ~1K | 5건×200자 | 0.5K~1K |
| Arc/Blueprint | ~5K | 전체 주입 | 5K |
| 남는 공간 | | | ~30K (낭비) |
```

이런 표를 **모든 주요 LLM 호출**마다 작성하세요:
- Stage 2: Analyst Arc 설계
- Stage 2: Arc 검증 (DraftValidator, UnifiedValidator)
- Stage 3: Blueprint 앙상블
- Stage 4: Chief Writer 원고 생성
- Stage 4: Director 앙상블 심사
- Stage 4: Director 연속성 심사
- Stage 4: 모순 사전 검사 (Interview Round)

---

### 4단계: 개선 기회 도출

각 손실 지점마다 **수정안**을 제안하세요. 형식:

```
### [HIGH] 벡터 메모리 summary 빈약
- 현재: stage4_post_processor.py:118 — final_title[:100] 저장
- 문제: 검색 결과가 제목만 반환, 내용 없음
- 수정안: 원고 요약(500자) + 핵심 사건 + NPC 변화를 summary에 포함
- 수정 파일: stage4_post_processor.py (저장), vec_memory.py (검색 결과 포맷)
- 영향 범위: Stage 4 컨텍스트 빌더의 벡터 검색 결과 품질
- 위험도: LOW (기존 벡터 재인덱싱 필요 없음, 신규 에피소드부터 적용)
```

우선순위 기준:
1. **HIGH**: 컨텍스트 품질에 직접 영향 → 모순/반복 발생 가능성 높음
2. **MEDIUM**: 컨텍스트 효율성 → 낭비되는 토큰 공간 활용 가능
3. **LOW**: 구조 개선 → 장기적 품질 향상

---

### 5단계: 추가 조사 — 하드코딩된 숫자 전수 조사

아래 패턴을 **모든 파일**에서 검색하세요:

```python
# 검색할 패턴들
[:200]          # 글자수 절삭
[:500]
[:1000]
[:2000]
[:3000]
[:4000]
[:6000]
[:50000]
200000          # 200K 절삭
50000           # mandatory_context 제한
"lookback"      # lookback 화수
range(1, 11)    # 최근 10화 등 매직넘버
range(1, 31)    # 최근 30화
max_tokens      # 토큰 제한
"excerpt"       # 발췌본 사용
"summary"       # 요약 사용 (전문 대신)
```

각 발견마다:
- 파일:라인
- 현재 값
- 이 값이 컨텍스트 품질에 미치는 영향
- 외부화(validation.yaml 등) 가능 여부

---

## 출력 형식

파일명: `docs/컨텍스트_활용_조사_결과.md`

구조:
```markdown
# Gemini 컨텍스트 활용 현황 조사

## 1. 컨텍스트 주입 경로 전수 맵
(2단계 결과)

## 2. 손실 지점 분류 (A~E)
(3단계 결과)

## 3. Stage별 토큰 예산표
(4단계 결과)

## 4. 개선 기회 목록 (우선순위순)
(5단계 결과)

## 5. 하드코딩 숫자 전수 목록
(6단계 결과)

## 6. 비활성 경로 목록
(ChainOfVerification 등)
```

---

## Codex 실행 설정

```
모드: 읽기 전용 (코드 수정 없음)
모델: o3 또는 o4-mini
라운드: 제한 없음
컨텍스트: 이 파일 + 코드베이스 전체
```

## 주의사항

- **코드를 수정하지 마세요.** 조사만 하세요.
- `base_agent.py`의 `ask()` 메서드를 반드시 읽으세요 — 모든 LLM 호출의 진입점입니다.
- `chief_writer_context.py`와 `stage4_context_builder.py`가 컨텍스트 조립의 핵심입니다.
- `참고자료.md`의 "V67: 하이엔드 컨텍스트 확장" 섹션을 참고하세요.
- 토큰 추정: 한국어 기준 1토큰 ≈ 2~3자, Gemini 200K tokens ≈ 400K~600K 한국어 글자
- `config/settings/validation.yaml`에 이미 외부화된 임계값이 있으니 참고하세요.
