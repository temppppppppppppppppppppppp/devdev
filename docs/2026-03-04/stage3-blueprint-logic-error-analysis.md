# Stage 3 Blueprint 로직 에러 현황 분석

> 작성일: 2026-03-04
> 목적: Stage 3에서 발생하는 Blueprint 로직 에러의 현황과 기존 대비책 문서화

---

## 1. 문제 정의

Stage 3(Blueprint 생성)에서 간헐적으로 로직 에러가 포함된 Blueprint가 PASS 판정을 받아 Stage 4로 전달됨. Stage 4에서 해당 Blueprint 기반 원고를 생성하면 Director가 반복 REJECT → retry 횟수 증가 → 시간 소요 증대.

**핵심 메커니즘**: Blueprint의 로직 에러는 Stage 4에서 "원고 품질 문제"로 표출되므로, 원인(Blueprint)과 증상(원고 REJECT) 사이에 한 단계 지연이 존재.

---

## 2. Stage 3 Blueprint 검증 체계 (현재)

### 2.1 검증 2단계 구조

| 단계 | 담당 | 역할 | 파일 |
|------|------|------|------|
| **Python 사전검사** | Validator | 필수 필드·분량·씬 수·정지선 위반 체크 (경고만, REJECT 불가) | `unified_blueprint_validator.py:L330-412` |
| **Director 최종 판정** | Director LLM | 모순·연속성·품질 종합 판정 (PASS/PASS_WITH_FIX/REJECT) | `unified_blueprint_validator.py:L255-316` |

### 2.2 Python 사전검사 항목

| 항목 | 조건 | 결과 |
|------|------|------|
| 필수 필드 | `scene_breakdown`, `integrated_scenario` 없음 | 경고 |
| 분량 | `integrated_scenario` < 800자 | 경고 |
| 씬 수 | `scene_breakdown` < 3개 | 경고 |
| 정지선 위반 | 다음 화 내용 침범 | 경고 |

**한계**: Python 사전검사는 **구조적 결함**만 감지. "타임라인 역행", "수치 불일치", "사망 NPC 행동" 같은 **논리적 모순**은 감지 불가 → Director LLM에 전적 의존.

### 2.3 Director 비교 선택 모드

- 앙상블 3개 후보 생성 (Action/Emotion/Dialogue 전략)
- Director가 3후보를 비교하여 최적 선택 (`director_ensemble.py:L44-318`)
- 평가 기준: 일관성·모순 없음(40%) + Arc 준수(35%) + 연속성(15%) + 다음 화 연결(10%)

### 2.4 PASS_WITH_FIX 수정 루프

```
Director → PASS_WITH_FIX 판정
  └─ for i in [0..2]: (최대 3회)
      ├─ fix_scope 판정 (PF-1: 누락 시 점수 기반 폴백)
      ├─ inplace/partial/full 분기
      ├─ InPlace 패치 (LLM 1회) → Director 재심사
      └─ PASS → 성공 / REJECT → break
  └─ 3회 소진 → REJECT 전환 (PF-3: PASS_WITH_FIX 소진 시 패치본 채택)
```
- 파일: `three_phase_blueprint_generator.py:L448-577`

### 2.5 Retry 루프

- `max_retries=9` (총 10회 시도 × 3전략 = 최대 30개 후보)
- REJECT 시 Director 피드백을 다음 생성에 주입
- 이전 REJECT 점수 ≥ REWRITE 임계값이면 `_previous_best` 보존
- 파일: `three_phase_blueprint_generator.py:L174-627`

---

## 3. Stage 4에서의 Blueprint 소비 경로

### 3.1 Blueprint 의존 체인

```
Blueprint (Stage 3 출력)
  ├─ WritingDirective 생성 (TF-54) ─── stage4_interview_round.py:L59-111
  ├─ Chief Writer 프롬프트 주입 ────── chief_writer_context.py:L108-117
  │   └─ scene_breakdown + ending_hook + integrated_scenario
  ├─ Director 심사 기준 ────────────── director_ensemble.py:L624-660
  │   └─ Stable Context (캐싱)에 Blueprint 포함
  ├─ Pre-Director 검증 ────────────── stage4_interview_round.py:L641-969
  │   └─ ConsistencyValidator·CrossAgentVerifier에 Blueprint 전달
  ├─ Self-Critique (8단계) ─────────── chief_writer_quality.py:L67-236
  │   └─ 6번째(directive 준수)·8번째(ending_hook 포함) 체크
  └─ Post-Processing ──────────────── stage4_post_processor.py:L583-665
      └─ VecMemory 저장 시 장소·결말 메타 추출
```

### 3.2 Blueprint 로직 에러가 Stage 4에서 유발하는 증상

| 증상 | 원인 | 감지 위치 |
|------|------|---------|
| **반복 REJECT** | Blueprint 모순 → CW가 모순 포함 원고 생성 → Director REJECT | `stage4_orchestrator.py:L902-906` |
| **동일 모순 유형 2연속** | Blueprint 특정 영역 결함 → 같은 종류의 모순 반복 | `stage4_orchestrator.py:L936-947` |
| **REJECT Bucket 3연속** | 품질/제약위반/구조 중 같은 REJECT 분류 반복 | `stage4_orchestrator.py:L908-934` |
| **Ending Hook 불일치** | Blueprint ending_hook이 원고와 불일치 | `chief_writer_quality.py:L477-490` |
| **시간 소요 증대** | retry 횟수 증가 (1라운드당 LLM 5~8회) | Stage 4 전체 |

---

## 4. Stage 4의 기존 대비책

### 4.1 LOGIC_ERROR 연속 감지 + 자동 수정

```
_logic_error_streak 추적 (stage4_orchestrator.py:L906)
  │
  ├─ 2연속 + 동일 모순 유형 2연속
  │   └─ [A-4] Arc 구조 진단 advisory 생성 → Director feedback 주입
  │       (stage4_orchestrator.py:L949-965)
  │
  ├─ 2연속 + InPlace 미시도
  │   └─ [V75-D] Blueprint InPlace 패치 (LLM 1회)
  │       (stage4_orchestrator.py:L967-1004)
  │
  └─ InPlace 실패 후에도 2연속
      └─ [V75-B] Blueprint 전면 재생성
          (stage4_orchestrator.py:L1006-1029)
```

### 4.2 대비책 효과 분석

| 대비책 | 트리거 조건 | 비용 | 효과 |
|--------|-----------|------|------|
| A-4 Advisory | LOGIC_ERROR 2연속 + 동일 모순 유형 | 0 (Python) | Director에 구조 결함 힌트 |
| V75-D InPlace | LOGIC_ERROR 2연속 | LLM 1회 | 국소 수정 (성공률 미측정) |
| V75-B 재생성 | InPlace 실패 후 계속 실패 | LLM 3회+ | Blueprint 전면 교체 |

### 4.3 트리거 지연 문제

**핵심 비효율**: 대비책이 "2연속 실패 후"에만 발동.

```
Round 1: Blueprint 로직 에러 → CW 원고 생성 (LLM 3회) → Director REJECT (LLM 1회)
Round 2: 동일 에러 → CW 재생성 (LLM 3회) → Director REJECT (LLM 1회)
         ↑ 여기서 V75-D 트리거 (이미 LLM 8회 소진)
Round 3: InPlace 패치 (LLM 1회) → 성공 시 CW 재생성 (LLM 3회) → Director 판정 (LLM 1회)
```

**최소 LLM 호출**: 성공 시 13회, 실패 시 V75-B로 에스컬레이션 → 20회+

---

## 5. Stage 3 메타데이터 전달

Stage 3 성공 시 Blueprint에 `_stage3_meta` 주입 (`stage3_orchestrator.py:L710-716`):

```python
blueprint["_stage3_meta"] = {
    "final_verdict": "PASS" | "PASS_WITH_FIX" | "PASS_WITH_WARNING",
    "quality_gate_failed": bool,
    "quality_risk": bool,
    "last_score": int,
}
```

**현재 미활용**: Stage 4에서 `_stage3_meta`의 `quality_risk`나 `final_verdict`에 따른 사전 조치 없음. PASS_WITH_WARNING으로 통과한 Blueprint도 일반 PASS와 동일하게 처리됨.

---

## 6. 현황 요약

### 잘 되어 있는 것
- Director 주권주의 준수 (Python은 경고만, 최종 판정은 Director)
- PASS_WITH_FIX 3-tier 수정 라우팅 (inplace/partial/full)
- Stage 4에서 연속 실패 감지 + 자동 Blueprint 수정/재생성 메커니즘
- 모순 유형별 추적 (타임라인/수치/사망/고유명사/아이템/상태)

### 비효율 지점
- **트리거 지연**: V75-D/B가 2연속 실패 후 발동 → 최소 LLM 8회 낭비
- **메타데이터 미활용**: `_stage3_meta.quality_risk`가 Stage 4 초기 전략에 반영 안 됨
- **Stage 3 Python 검증 한계**: 논리적 모순(수치·타임라인·인과) 감지 불가, Director 1회 판정에 의존

---

## 7. 파일 참조표

| 기능 | 파일 | 핵심 라인 |
|------|------|---------|
| S3 Blueprint 생성 루프 | `three_phase_blueprint_generator.py` | L174-627 |
| S3 PASS_WITH_FIX 수정 | `three_phase_blueprint_generator.py` | L448-577 |
| S3 InPlace 패치 | `three_phase_blueprint_generator.py` | L653-737 |
| S3 Python 사전검사 | `unified_blueprint_validator.py` | L330-412 |
| S3 Director 최종 판정 | `unified_blueprint_validator.py` | L255-316 |
| S3 Director 비교 선택 | `director_ensemble.py` | L44-318 |
| S3 메타데이터 주입 | `stage3_orchestrator.py` | L710-716 |
| S4 Blueprint 소비 | `stage4_interview_round.py` | L59-111, L124-208, L641-969 |
| S4 LOGIC_ERROR 추적 | `stage4_orchestrator.py` | L902-947 |
| S4 A-4 구조 진단 | `stage4_orchestrator.py` | L949-965 |
| S4 V75-D InPlace | `stage4_orchestrator.py` | L967-1004 |
| S4 V75-B 재생성 | `stage4_orchestrator.py` | L1006-1029 |
| CW Self-Critique | `chief_writer_quality.py` | L67-236, L477-490 |
| CW Blueprint 프롬프트 | `chief_writer_context.py` | L108-117 |
| Director Stable Context | `director_ensemble.py` | L624-660 |
| Post-Processing 메타 | `stage4_post_processor.py` | L583-665 |
