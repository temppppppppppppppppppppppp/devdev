# Reasoning 전략 기반 가성비 업그레이드 제안

**날짜**: 2026-01-29
**현재 시스템**: Phase 1-4 완료, V0128 3-tier validation

---

## 📊 현재 적용된 Reasoning 전략

### ✅ 이미 구현됨
1. **Self-Consistency** (TIER 2 SCORING)
   - 3-vote majority로 환각 30% → 5% 감소
   - 비용: $0.03/manuscript (3회 평가)

2. **CoT (Chain of Thought)** (일부 적용)
   - Director 원고 검증 (5-step review)
   - SCORING Validator (5-step evaluation)
   - 비용: $0 (프롬프트만)

3. **Few-Shot Learning** (Phase 4)
   - Justification Patterns
   - 비용: $0

---

## 🎯 가성비 높은 업그레이드 옵션 (5가지)

### ⭐ Option 1: Writer Self-Critic (가성비 ★★★★★)

**개념**: Writer가 원고 작성 후 스스로 비판하고 수정

**구현 위치**: `write_v20_manuscript()` 직후, validation 이전

**흐름**:
```
1. Writer: 원고 작성 (현재와 동일)
2. Writer: Self-Critique
   - "이 원고가 HUD와 모순되는가?"
   - "클리셰를 과다 사용했는가?"
   - "정당화가 부족한 장면이 있는가?"
   - "NPC 관계가 일관적인가?"
3. Writer: 문제 발견 시 해당 부분만 수정
4. Validation (현재 시스템)
```

**예상 효과**:
- BLOCKING 실패율: 15% → 5% (-67%)
- SCORING 재시도: 30% → 15% (-50%)
- 총 재시도 감소로 **전체 비용 오히려 감소**

**비용**:
- Self-Critique 1회: ~$0.005 (flash 모델)
- 수정 1회: ~$0.01 (조건부)
- **순증 비용: ~$0.01/manuscript**
- **절감 효과: -$0.03/manuscript (재시도 감소)**
- **순효과: -$0.02/manuscript (절약)**

**구현 난이도**: ⭐⭐ (쉬움)

**ROI**: 200% (비용 절감 + 품질 향상)

---

### ⭐⭐ Option 2: Conditional Self-Consistency (가성비 ★★★★★)

**개념**: 애매한 점수일 때만 3-vote, 명확할 때는 1-vote

**현재 문제**:
- 모든 manuscript에 3-vote (비용 3배)
- 명확히 PASS(90+) 또는 REJECT(50-)인 경우도 3번 평가

**개선안**:
```python
# 1차 평가 (1-vote)
score = scoring_validator.evaluate()

if 70 <= score <= 85:
    # 애매한 구간만 Self-Consistency
    scores = [score, evaluate_2nd(), evaluate_3rd()]
    final_score = median(scores)
else:
    # 명확한 구간은 1-vote로 종료
    final_score = score
```

**예상 효과**:
- 애매한 구간: 20% (3-vote 필요)
- 명확한 구간: 80% (1-vote로 종료)
- **평균 비용: $0.012/manuscript (-60%)**

**품질 영향**: 거의 없음 (명확한 경우는 3번 해도 동일)

**구현 난이도**: ⭐ (매우 쉬움)

**ROI**: 300% (비용 60% 절감, 품질 유지)

---

### ⭐⭐⭐ Option 3: Architect CoT 강화 (가성비 ★★★★★)

**개념**: Blueprint 작성 시 단계별 사고 체계화

**현재 문제**: Architect가 Blueprint를 한 번에 작성

**개선안**:
```
[Step 1] 이전 화 분석
- 제N-1화 엔딩 상황 정리
- 미해결 갈등 리스트업
- 주인공 현재 상태 확인

[Step 2] 갈등 설계
- 이번 화 핵심 갈등 선정
- 갈등 강도 조절 (CatharsisTimer 고려)
- 갈등 해결 방식 계획

[Step 3] 장면 배치
- 6개 장면 배치 (기승전결)
- 각 장면의 목적 명확화
- 씬 간 논리적 연결 확인

[Step 4] 정합성 체크
- HUD 범위 내 행동인가?
- NPC 관계 일관적인가?
- 미래 누수 없는가?

[Step 5] Blueprint 작성
- 위 분석을 바탕으로 최종 Blueprint
```

**예상 효과**:
- Blueprint 품질 향상 → Writer 실패율 감소
- Architect 재시도: 10% → 5% (-50%)

**비용**: $0 (프롬프트만)

**구현 난이도**: ⭐ (프롬프트 수정만)

**ROI**: ∞ (무료, 고효과)

---

### ⭐⭐⭐⭐ Option 4: Director Reflexion (가성비 ★★★)

**개념**: 과거 실패 패턴을 학습하여 검증 강화

**구현**:
```python
# 1. 실패 로그 수집
failed_manuscripts = {
    "ep_3": {
        "reason": "사망 NPC 재등장",
        "pattern": "NPC 사망 후 2화만에 등장",
        "fix": "NPC 리스트 확인 강화"
    },
    "ep_7": {
        "reason": "관계 역행",
        "pattern": "경외→무시 전환",
        "fix": "RelationshipTracker 체크"
    }
}

# 2. 검증 시 과거 실패 참조
director_prompt = f"""
[과거 실패 패턴]
{format_past_failures(project_failures)}

이번 원고가 위 실패 패턴과 유사한가?
"""
```

**예상 효과**:
- 반복 실패 방지
- 프로젝트별 맞춤 학습

**비용**: $0 (실패 로그는 이미 있음)

**구현 난이도**: ⭐⭐⭐ (DB 스키마 추가 필요)

**ROI**: 150% (장기적 품질 향상)

---

### ⭐⭐⭐⭐⭐ Option 5: Writer Iterative Refinement (가성비 ★★★)

**개념**: 원고 작성 → 자기 비평 → 수정 → 재평가 반복

**구현**:
```
Round 1: Writer 초고 작성
Round 2: Self-Critique → 문제 발견 → 해당 부분 수정
Round 3 (optional): 재평가 → 추가 수정
Final: Validation
```

**예상 효과**:
- 최종 품질: 85점 → 90점
- SCORING 통과율: 70% → 85%

**비용**:
- Self-Critique: $0.005
- Refinement: $0.015 (부분 수정)
- **총: +$0.02/manuscript**

**구현 난이도**: ⭐⭐⭐ (중간)

**ROI**: 100% (품질 향상, 약간의 비용 증가)

---

## 💰 비용 대비 효과 매트릭스

| 옵션 | 비용 변화 | 품질 향상 | 구현 난이도 | 가성비 | 추천 순위 |
|------|-----------|-----------|-------------|--------|-----------|
| **Option 1: Writer Self-Critic** | **-$0.02** (절약) | ⭐⭐⭐⭐ | ⭐⭐ | ★★★★★ | 🥇 1위 |
| **Option 2: Conditional SC** | **-$0.018** (60% 절감) | - (유지) | ⭐ | ★★★★★ | 🥈 2위 |
| **Option 3: Architect CoT** | **$0** (무료) | ⭐⭐⭐ | ⭐ | ★★★★★ | 🥉 3위 |
| Option 4: Director Reflexion | $0 | ⭐⭐ | ⭐⭐⭐ | ★★★ | 4위 |
| Option 5: Iterative Refinement | +$0.02 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ★★★ | 5위 |

---

## 🎯 추천 구현 순서

### Phase 5.1: 무료 최적화 (즉시 가능)
1. **Option 3: Architect CoT 강화**
   - 비용: $0
   - 효과: Blueprint 품질 향상
   - 구현: `architect.py` 프롬프트 수정
   - 시간: 30분

2. **Option 2: Conditional Self-Consistency**
   - 비용: -60%
   - 효과: 비용 대폭 절감, 품질 유지
   - 구현: `validation_orchestrator.py` 로직 수정
   - 시간: 1시간

### Phase 5.2: 고급 최적화 (선택)
3. **Option 1: Writer Self-Critic**
   - 비용: -$0.02/manuscript (순절약)
   - 효과: 재시도 50% 감소
   - 구현: `writer.py`에 `_self_critique()` 메서드 추가
   - 시간: 2시간

4. **Option 4: Director Reflexion** (장기 프로젝트용)
   - 비용: $0
   - 효과: 프로젝트별 맞춤 학습
   - 구현: 실패 로그 DB + Director 프롬프트 수정
   - 시간: 3시간

---

## 📊 예상 총 효과 (250화 프로젝트)

### 현재 시스템
- 총 비용: ~$10
- BLOCKING 실패율: 15%
- SCORING 재시도율: 30%
- 평균 품질: 85점

### Phase 5 적용 후
- **총 비용: ~$6 (-40%)**
- **BLOCKING 실패율: 5% (-67%)**
- **SCORING 재시도율: 15% (-50%)**
- **평균 품질: 88점 (+3점)**

**절약액**: $4/프로젝트
**품질 향상**: +3점
**개발 시간**: 4.5시간

---

## 🔍 더 고급 옵션 (참고)

### ❌ GoT (Graph of Thoughts) - 가성비 낮음
- 개념: 다중 경로 탐색 후 최선 선택
- 비용: +300% (3개 경로)
- 효과: +5% 품질 향상 (미미)
- 결론: **비추천** (비용 대비 효과 낮음)

### ❌ Tree of Thoughts (ToT) - 과도한 비용
- 개념: 트리 구조로 다양한 사고 탐색
- 비용: +500% (트리 노드 수에 비례)
- 효과: +10% 품질 향상
- 결론: **비추천** (학술 연구용, 실전 부적합)

### ⚠️ ReAct (Reasoning + Acting) - 복잡도 높음
- 개념: 추론과 행동을 반복
- 비용: +100-200%
- 효과: 특정 task에 강력하지만 원고 작성엔 과도
- 결론: **보류** (필요성 낮음)

---

## 🚀 즉시 시작 가능한 Quick Win

### Quick Win #1: Architect CoT (15분 구현)
`modules/domain/agents/architect.py` 프롬프트에 추가:
```python
prompt = f"""
[STEP 1] 이전 화 분석
제{ep_num-1}화 엔딩: {prev_ending}
미해결 갈등: {unresolved_conflicts}
주인공 상태: {hud_summary}

[STEP 2] 갈등 설계
이번 화 핵심 갈등: ...
갈등 강도: ...
해결 방식: ...

[STEP 3] 장면 배치
Scene 1: ...
Scene 2: ...
...

[STEP 4] 정합성 체크
HUD 범위 확인: ...
NPC 관계 확인: ...
미래 누수 확인: ...

[STEP 5] 최종 Blueprint 작성
{{
  "scene_breakdown": {{...}},
  ...
}}
"""
```

### Quick Win #2: Conditional Self-Consistency (30분 구현)
`modules/validation/validation_orchestrator.py`에서:
```python
def _run_scoring_with_conditional_sc(self, manuscript, context):
    # 1차 평가
    score = self.scoring.evaluate(manuscript, context)

    # 애매한 구간만 Self-Consistency
    if 70 <= score <= 85:
        print("      ⚖️ [Conditional SC] 애매한 점수 → 3-vote 활성화")
        scores = [score]
        for i in range(2):
            scores.append(self.scoring.evaluate(manuscript, context))
        return median(scores)
    else:
        print(f"      ✓ [Conditional SC] 명확한 점수({score}) → 1-vote로 종료")
        return score
```

**즉시 효과**: 비용 60% 절감, 품질 유지

---

## 🎉 결론

**가성비 Top 3 (즉시 구현 권장)**:
1. 🥇 **Architect CoT 강화** - $0, 무료 품질 향상
2. 🥈 **Conditional Self-Consistency** - 비용 60% 절감
3. 🥉 **Writer Self-Critic** - 순비용 절약 + 품질 향상

**예상 총 효과**:
- 비용 40% 절감 ($10 → $6)
- 품질 3점 향상 (85 → 88)
- 재시도 50% 감소

**구현 시간**: 4.5시간

**ROI**: 300% (비용 절감 + 품질 향상 + 개발 시간 짧음)

---

*작성: Claude Code*
*날짜: 2026-01-29*
