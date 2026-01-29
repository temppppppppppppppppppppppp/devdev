# 글도비 V0128 매니페스토 실현 가능성 및 효율성 평가 보고서

**보고일**: 2026-01-28
**평가 버전**: V0128 (기준: V41 코드베이스)
**평가자**: Claude Sonnet 4.5

---

## 📋 Executive Summary

### 종합 판정

| 항목 | 평가 | 세부 점수 |
|------|------|----------|
| **실현 가능성** | ★★★★☆ (4.2/5) | 기술적 장벽 낮음, 구조적 설계 우수 |
| **효율성** | ★★★☆☆ (3.5/5) | API 비용 증가 우려, 통과율 개선 기대 |
| **투자 대비 효과** | ★★★★☆ (4.0/5) | 품질 향상 명확, 개발 공수 중간 |
| **긴급도** | ★★★★★ (5/5) | 현재 50-60% 통과율은 치명적 병목 |

### 핵심 결론

✅ **즉시 구현 권장** - V0128 설계는 현실적이며 효과적입니다.

**근거**:
1. 현재 통과율 50-60%는 프로덕션 병목 → 80-85% 목표는 합리적
2. 3-Tier 시스템은 기술적으로 구현 난이도 낮음 (LLM 기반 평가)
3. 현재 Director 코드를 확장하는 방식으로 점진적 도입 가능
4. API 비용 증가는 있으나, 재시도 감소로 상쇄 가능

---

## 1. 현재 구현 상태 분석

### 1.1 V0128 요구사항 vs 현재 코드베이스

| V0128 핵심 요소 | 현재 구현 상태 | Gap |
|----------------|---------------|-----|
| **3-Tier Validation** | ❌ 미구현 | **HIGH** |
| - TIER 1: BLOCKING | 🟡 부분 구현 (director.py의 강제 체크) | MEDIUM |
| - TIER 2: SCORING | ❌ 미구현 | HIGH |
| - TIER 3: ADVISORY | ❌ 미구현 | HIGH |
| **7대 품질 차원** | ❌ 미구현 | HIGH |
| - EmotionArcEvaluator | ❌ 없음 | HIGH |
| - ProseQualityEvaluator | ❌ 없음 | HIGH |
| - DialogueQualityEvaluator | ❌ 없음 | HIGH |
| - CommercialAppealEvaluator | ❌ 없음 | HIGH |
| - OriginalityEvaluator | ❌ 없음 | MEDIUM |
| - ActionSceneEvaluator | ❌ 없음 | MEDIUM |
| **ValidationOrchestrator** | ❌ 없음 | HIGH |
| **CatharsisTimer** | ❌ 없음 | MEDIUM |

### 1.2 현재 검증 시스템 (Director.py)

**구조**:
```python
Director.audit_manuscript() → 단일 PASS/REJECT 판정
├─ 분량 체크 (4000자 최소) ✅
├─ 반복 구문 체크 (RepetitionGuard) ✅
├─ QUALITY_ISSUE / LOGIC_ERROR 분류 ✅
└─ 씬 무결성 체크 (최소 4개 장면) ✅
```

**문제점**:
1. 모든 체크가 **BLOCKING** 성격 → 통과율 저하
2. 품질 평가가 LLM의 주관적 판단에 의존
3. 세부 피드백 부족 (70점 vs 85점 구분 불가)
4. 개선 여지 있는 원고도 무조건 REJECT

---

## 2. V0128 실현 가능성 평가

### 2.1 기술적 실현 가능성: ★★★★☆ (4.2/5)

#### ✅ 긍정 요소

1. **LLM 기반 평가의 성숙도**
   - Gemini 3.0/2.5 Pro는 문학적 품질 평가 가능
   - 감정선, 문장 리듬, 대화 품질 등은 프롬프트로 유도 가능
   - 예: `"문장 길이의 표준편차를 계산하여 리듬감을 평가하라"` → LLM이 충분히 처리 가능

2. **모듈화 설계 우수**
   - V0128의 Validator 클래스들은 독립적으로 동작
   - 점진적 도입 가능 (BLOCKING → SCORING → ADVISORY 순)
   - 기존 Director와 병렬로 테스트 가능

3. **Python 기반 계산 가능**
   - Type-Token Ratio, Coefficient of Variation 등은 Python으로 직접 계산 가능
   - LLM 호출 없이도 일부 SCORING 항목 처리 가능 → **비용 절감**

4. **기존 인프라 활용**
   - `RepetitionGuard`는 이미 구현됨 → `ProseQualityEvaluator`로 확장 용이
   - `MartialManager` HUD → `BlockingValidator`의 설정 일관성 체크에 직접 사용 가능
   - ChromaDB → 과거 패턴 다양성 체크에 활용 가능

#### ⚠️ 우려 요소

1. **LLM 평가의 불안정성**
   - 같은 원고를 2번 평가하면 점수 변동 가능 (temperature 영향)
   - 완화 방법: `temperature=0.1` + 다수결 투표 (3회 평가 후 중앙값)

2. **API 호출 증가**
   - 현재: Director 1회 호출
   - V0128: BLOCKING(LLM 불필요) + SCORING(LLM 1회) + ADVISORY(LLM 1회) = **최대 2회**
   - 비용 영향: 에피소드당 +$0.01~0.02 (캐시 사용 시)

3. **구현 공수**
   - 6개 Evaluator 클래스 신규 구현 필요
   - ValidationOrchestrator 통합 로직
   - 예상 개발 시간: **3-4일** (full-time 기준)

### 2.2 아키텍처 적합성: ★★★★★ (5/5)

V0128 설계는 현재 시스템과 **완벽하게 호환**됨:

```python
# 현재 구조
Writer.write_v20_manuscript()
    ↓
Director.audit_manuscript() → PASS/REJECT
    ↓
save to DB or retry

# V0128 구조 (기존과 병렬 가능)
Writer.write_v20_manuscript()
    ↓
ValidationOrchestrator.validate()
    ├─ BlockingValidator → REJECT → 즉시 종료
    ├─ ScoringValidator → 70점 미만 → REJECT
    └─ AdvisoryValidator → 로그만 기록
    ↓
save to DB or retry
```

**통합 전략**:
1. **Phase 1**: `ValidationOrchestrator`를 Director와 병렬로 실행 (비교 테스트)
2. **Phase 2**: 통과율 검증 후 Director 대체
3. **Phase 3**: ADVISORY 데이터 축적 후 Writer 프롬프트 개선

---

## 3. 효율성 평가

### 3.1 통과율 개선 효과: ★★★★★ (5/5)

**현재 문제**:
- 통과율 50-60% → 평균 재시도 2회
- 에피소드당 실제 API 호출: Writer(1회) + Director(1회) × 2회 평균 = **3-4회**

**V0128 예상 효과**:
```
통과율: 50-60% → 80-85%
평균 재시도: 2.0회 → 1.2회
에피소드당 API 호출: 3-4회 → 2.5회 (-30%)
```

**비용 영향**:
```
현재 (50% 통과율):
Writer(3회) × $0.01 = $0.03
Director(3회) × $0.005 = $0.015
에피소드당 총: $0.045

V0128 (80% 통과율):
Writer(1.2회) × $0.01 = $0.012
ValidationOrchestrator(1.2회 × 2 LLM calls) × $0.005 = $0.012
에피소드당 총: $0.024 (-47% 절감!)
```

✅ **결론**: 재시도 감소로 인한 비용 절감이 검증 비용 증가를 상쇄하고도 남음.

### 3.2 품질 향상 효과: ★★★★☆ (4/5)

| 차원 | 현재 (V41) | V0128 예상 | 개선폭 |
|------|-----------|-----------|-------|
| **설정 일관성** | ★★★☆☆ | ★★★★★ | +40% |
| **문장 품질** | ★★☆☆☆ | ★★★★☆ | +80% |
| **감정선 관리** | ★☆☆☆☆ | ★★★★☆ | +150% |
| **상업성** | ★★★☆☆ | ★★★★★ | +50% |
| **패턴 다양성** | ★☆☆☆☆ | ★★★★☆ | +120% |

**정량 지표**:
- 문장 리듬 (CV): 측정 불가 → 0.3-0.6 범위 강제
- 어휘 다양성 (TTR): 측정 불가 → 0.3 이상 보장
- 카타르시스 간격: 제어 없음 → 3화 이내 보장
- 클리셰 반복: 체크 없음 → 10화 내 중복 방지

### 3.3 개발 투자 대비 효과: ★★★★☆ (4/5)

**투자 비용**:
- 개발 시간: 3-4일 (full-time)
- 테스트: 1-2일 (50-100 에피소드 검증)
- 총 공수: **약 5일**

**회수 기간**:
```
250화 프로젝트 1개 기준:
절감 비용: $0.045 - $0.024 = $0.021 per episode
250화 × $0.021 = $5.25 절감

프로젝트 20개 제작 시: $105 절감
```

단순 비용만으로는 회수 기간이 길지만, **품질 향상**으로 인한 부가가치가 핵심:
- 독자 이탈률 감소
- 연재 지속성 증가
- 브랜드 신뢰도 상승

---

## 4. 리스크 분석

### 4.1 기술적 리스크

| 리스크 | 심각도 | 발생 확률 | 완화 방안 |
|--------|--------|----------|----------|
| LLM 평가 불안정성 | MEDIUM | 60% | temperature=0.1 + 다수결 |
| API 타임아웃 | LOW | 10% | 개별 Evaluator 타임아웃 설정 |
| 품질 기준 과도함 | HIGH | 40% | 임계값 조정 가능하게 설계 |
| 통합 버그 | MEDIUM | 30% | 병렬 테스트 기간 2주 |

### 4.2 운영 리스크

| 리스크 | 심각도 | 완화 방안 |
|--------|--------|----------|
| 통과율이 예상보다 낮음 (70%) | HIGH | 임계값 동적 조정 (70→65→60) |
| 피드백이 너무 장황함 | MEDIUM | ADVISORY 출력 제한 (상위 3개만) |
| 특정 장르 편향 | MEDIUM | 장르별 가중치 분리 설정 |

---

## 5. 구현 우선순위 제안

### Phase 1 (Day 1-2): Core Infrastructure ⭐⭐⭐⭐⭐

```python
# 1. BlockingValidator (Python 기반, LLM 불필요)
class BlockingValidator:
    def validate(self, manuscript, context):
        # 사망 NPC 체크 (encyclopedia.status == 'dead')
        # 미획득 아이템 체크 (AssetLibrary 비교)
        # 분량 체크 (len(manuscript) >= 4000)
        # 필수 씬 체크 (Scene 1~6 키워드 매칭)
        pass
```

**기대 효과**: 즉시 적용 가능, LLM 호출 제거로 비용 0

### Phase 2 (Day 2-3): Scoring System ⭐⭐⭐⭐☆

```python
# 2. 핵심 Evaluator 3종
class EmotionArcEvaluator:
    # 감정선 평가 (20점)

class ProseQualityEvaluator:
    # 문장 품질 (20점)
    # Python으로 TTR, CV 직접 계산 → LLM은 해석만

class CommercialAppealEvaluator:
    # 후킹/클리프행어 (20점)
```

**기대 효과**: 통과율 70-75% 예상

### Phase 3 (Day 3-4): Advanced Features ⭐⭐⭐☆☆

```python
# 3. 추가 Evaluator
class DialogueQualityEvaluator:
    # 대화 품질 (15점)

class ActionSceneEvaluator:
    # 전투 씬 평가 (장르별 가중치)
```

**기대 효과**: 통과율 80-85% 달성

### Phase 4 (Day 4-5): Advisory & Polish ⭐⭐☆☆☆

```python
# 4. TIER 3 & Orchestrator
class AdvisoryValidator:
    # 클리셰 감지, 개선 제안

class ValidationOrchestrator:
    # 3-Tier 통합 실행
```

**기대 효과**: 품질 피드백 개선, 학습 데이터 축적

---

## 6. 대안 및 절충안

### 6.1 Light Version (2일 구현)

**범위**:
- BLOCKING만 구현 (Python 기반, LLM 불필요)
- SCORING은 기존 Director LLM에 점수 요청 (프롬프트만 수정)
- ADVISORY 생략

**효과**:
- 통과율 65-70% (중간 개선)
- 비용 절감 -20%
- 구현 공수 40% 감소

### 6.2 Hybrid Version (현재 + V0128)

**구조**:
```
BLOCKING (Python) → 즉시 탈락
    ↓ PASS
기존 Director (LLM) → 주관적 평가
    ↓ PASS
SCORING (Python 위주) → 객관적 점수
    ↓ 70점 이상
최종 PASS
```

**효과**:
- 통과율 75-80% (대부분 달성)
- 기존 시스템 유지 + 점진적 개선

---

## 7. 최종 권고사항

### ✅ 즉시 실행 권장 사항

1. **BlockingValidator 우선 구현** (1일 공수)
   - LLM 불필요, 즉시 효과
   - 사망 NPC/미획득 아이템 체크로 치명적 오류 차단

2. **ProseQualityEvaluator (Python 기반)** (1일 공수)
   - TTR, CV 계산은 Python으로 직접 처리
   - LLM은 해석만 담당 → 비용 최소화

3. **EmotionArcEvaluator (LLM 기반)** (1일 공수)
   - 감정선 추적으로 품질 대폭 개선
   - 카타르시스 타이머로 답답함 방지

### 🔄 2단계 권고 (1주 후)

4. CommercialAppealEvaluator
5. DialogueQualityEvaluator
6. ValidationOrchestrator 통합

### 📊 성공 지표

| 지표 | 현재 | 1주 후 목표 | 1개월 후 목표 |
|------|------|------------|--------------|
| 통과율 | 50-60% | 70-75% | 80-85% |
| 평균 재시도 | 2.0회 | 1.5회 | 1.2회 |
| 에피소드당 비용 | $0.045 | $0.035 | $0.024 |
| 품질 점수 | 측정 불가 | 70-75점 | 75-80점 |

---

## 8. 결론

### 핵심 메시지

> **V0128 매니페스토는 실현 가능하며 효율적입니다.**
>
> 현재 50-60% 통과율은 프로덕션의 치명적 병목이며, V0128의 3-Tier 시스템은 이를 80-85%로 개선할 수 있는 현실적 솔루션입니다.

### 투자 가치

```
투자: 5일 개발 공수
회수:
  - 비용 절감: -47% (250화 기준 $5.25)
  - 시간 절감: 재시도 감소로 제작 기간 -30%
  - 품질 향상: 측정 불가 → 70-80점대 일관성
  - 상업적 가치: 독자 이탈률 감소 (정량화 어려움)

ROI: 품질 향상 효과를 고려하면 **매우 높음**
```

### Action Items (우선순위 순)

1. ✅ **BlockingValidator 구현** (1일, 즉시 효과)
2. ✅ **ProseQualityEvaluator 구현** (1일, Python 기반)
3. ✅ **EmotionArcEvaluator 구현** (1일, LLM 기반)
4. 🔄 통과율 70% 검증 후 추가 Evaluator 개발
5. 🔄 2주 병렬 테스트 후 기존 Director 대체

---

**보고서 끝**

*V0128은 이론적 설계가 아닌 실행 가능한 로드맵입니다. 즉시 착수를 권장합니다.*
