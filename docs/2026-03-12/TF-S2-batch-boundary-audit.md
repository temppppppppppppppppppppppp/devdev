# TF-S2-BATCH: Stage 2 배치 경계 전수조사 보고서

> 상태: **CONFIRMED** (3-Pass 감리 완료 2026-03-12)
> 감리 결과: P1 1건 수정(시나리오 불일치), P2 2건 수정(상수 미연결, 표현 혼동)
> 작성일: 2026-03-12
> 질문: "5아크 생성과 6아크 생성은 다른가?"
> 범위: stage2_orchestrator.py 배치 처리 로직 전수조사
> 제약: 코드 수정 절대 금지

---

## 1. 현재 구조 요약

### 1.1 배치 루프 구조

```python
# stage2_orchestrator.py L268-269
for batch_start in range(done_count, target_limit, 5):
    batch_end = min(batch_start + 5, target_limit)
```

**배치 크기 5 하드코딩.** 루프에서 리터럴 `5`를 직접 사용. `constants.py`에 `BatchSizes.ARC_BATCH_SIZE = 5`가 정의되어 있으나, orchestrator에서 참조하지 않음 (미연결 상수).

### 1.2 아크 생산 3단계

```
A단계: 병렬 농축 (배치 단위)
  → 배치 내 모든 아크를 asyncio.gather로 동시 농축
  → 각 아크에 prev_block, next_block, transfused_history 주입

B단계: 인과율 용접 (배치 단위)
  → 배치 내 인접 아크 쌍(1-2, 2-3, 3-4, 4-5)을 순차 용접
  → stitch_joints()로 joint_docs 정합성 검사/수리

C단계: 순차 설계 (아크 단위)
  → 배치 내 아크를 1개씩 순차 처리
  → 앙상블 3후보 → Director 선택 → 검증 → 확정
  → 확정된 아크의 상태가 다음 아크에 전달
```

### 1.3 배치 간 상태 전달

```python
# L278: 배치 시작 시 이전 아크 전체 상태를 컨텍스트로 생성
last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, batch_start + 1)

# L626: 아크 완성 후 상태 갱신
last_refined_context = _fin.get("last_refined_context", last_refined_context)
current_ep_start = _fin.get("current_ep_start", current_ep_start)
```

---

## 2. 핵심 질문: 5아크 vs 6아크 — 무엇이 달라지는가?

### 2.1 5아크 생성 시 (정확히 1배치)

```
Batch 1: [Arc 1, 2, 3, 4, 5]
  A. 병렬 농축: 5개 동시
  B. 인과율 용접: 1-2, 2-3, 3-4, 4-5 (4쌍)
  C. 순차 설계: 1→2→3→4→5
끝.
```

- 용접: 배치 내 4쌍 전부 처리됨
- 농축: 5개 모두 동일한 `last_refined_context`로 농축됨
- 순차 설계: Arc 1의 결과가 Arc 2에, Arc 2의 결과가 Arc 3에... 연쇄 전달

### 2.2 6아크 생성 시 (1배치 + 잔여 1)

```
Batch 1: [Arc 1, 2, 3, 4, 5]
  A. 병렬 농축: 5개 동시 (last_refined_context = 빈 문자열)
  B. 인과율 용접: 1-2, 2-3, 3-4, 4-5 (4쌍)
  C. 순차 설계: 1→2→3→4→5

Batch 2: [Arc 6]
  A. 병렬 농축: 1개 (last_refined_context = Arc 1~5 전체 상태)
  B. 인과율 용접: 없음 (1개라 쌍 없음)
  C. 순차 설계: 6
끝.
```

### 2.3 차이점 분석

| 항목 | 5아크 (1배치) | 6아크 (1+1배치) | 영향도 |
|------|-------------|----------------|--------|
| **Arc 5→6 용접** | 해당 없음 (Arc 6 미생성) | 없음 (배치 경계) | **⚠️ 6아크 시 누락** |
| **Arc 6 농축 컨텍스트** | — | Arc 1~5 전체 상태 포함 | ✅ 더 풍부 |
| **Arc 6 prev_block** | — | arcs_source[5] 참조 | ✅ 정상 |
| **인과율 용접 범위** | 1-2,2-3,3-4,4-5 | 1-2,2-3,3-4,4-5 (Batch1) + 없음 (Batch2) | **⚠️ 5→6 미용접** |

---

## 3. 발견된 문제점

### 3.1 P1: 배치 경계 인과율 용접 누락

**위치:** `stage2_orchestrator.py` L392-423

```python
# B. 사후 용접 — 배치 내부만 순회
for i in range(len(enriched_batch) - 1):
    arc_a_idx, arc_a = enriched_batch[i]
    arc_b_idx, arc_b = enriched_batch[i + 1]
    stitch_res = self.ctx.agents["analyst"].stitch_joints(...)
```

**문제:** `stitch_joints()`는 **배치 내부의 인접 쌍**만 용접한다.

예시 (10아크, 2배치):
- Batch 1 [1~5]: Arc 1-2, 2-3, 3-4, 4-5 ✅
- **Batch 1→2 경계: Arc 5→6 용접 없음** ❌
- Batch 2 [6~10]: Arc 6-7, 7-8, 8-9, 9-10 ✅

**영향:**
- 5아크 생성: 영향 없음 (배치 경계 없음)
- 6아크 생성: Arc 5→6 인과율 용접 누락
- 10아크 생성: Arc 5→6 인과율 용접 누락
- 15아크 생성: Arc 5→6, 10→11 인과율 용접 누락

**심각도:** **IMPORTANT**
- 용접은 `joint_docs` 정합성 검사 + 수리. 누락 시 아크 경계에서 설정 불일치 가능.
- 다만 C단계(순차 설계)에서 `last_refined_context`가 이전 아크 전체 상태를 전달하므로, **LLM이 암묵적으로 연결을 유지할 수 있음**. 용접 누락이 반드시 품질 저하로 이어지지는 않음.
- 그러나 **Python 수준의 기계적 정합성 검사가 빠지는 것**은 사실.

### 3.2 P2: 배치 내 농축의 동일 컨텍스트 문제

**위치:** `stage2_orchestrator.py` L278, L303-304

```python
# 배치 시작 시 1회만 생성
last_refined_context = self.ctx.generate_arc_context_v60(all_refined_arcs, batch_start + 1)

# 농축 시 모든 아크가 동일한 last_refined_context 사용
_result = await self.ctx.agents["analyst"].enrich_raw_block_async(
    curr_b, prev_b, next_b_safe, [], transfused_history=last_refined_context
)
```

**문제:** 배치 내 5개 아크가 **모두 같은 시점의 컨텍스트**로 농축됨.
- Arc 1이 농축될 때의 컨텍스트 = Arc 5가 농축될 때의 컨텍스트
- Arc 1의 농축 결과가 Arc 2~5의 농축에 반영되지 않음

**영향:**
- 농축은 `prev_block`과 `next_block`으로 인접 블록 참조를 하므로, 원본 TR 블록 수준의 연결은 유지됨
- 그러나 **농축 과정에서 생성된 새로운 정보**(예: 부가 설정, 확장된 맥락)는 동일 배치 내 다른 아크에 전파되지 않음
- C단계(순차 설계)에서 이 정보가 `last_refined_context`를 통해 순차 전달되므로, **최종 아크 설계 시에는 반영됨**

**심각도:** **LOW**
- 농축은 원본 TR 블록을 풍부하게 만드는 단계이지 아크 설계 자체가 아님
- 순차 설계(C단계)에서 실제 아크 간 연결이 이뤄짐

### 3.3 INFO: 배치 크기와 무관한 요소들

다음 요소들은 배치 크기에 영향받지 않음:

| 요소 | 이유 |
|------|------|
| 앙상블 3후보 | 아크 단위 (배치 무관) |
| Director 선택 | 아크 단위 (배치 무관) |
| 검증 파이프라인 | 아크 단위 (배치 무관) |
| ep_start/ep_end 계산 | `all_refined_arcs[-1].get("ep_end")` — 순차 누적 |
| ConstraintDB | 아크 완성 시 갱신 — 순차 누적 |
| `cumulative_state_cache` | 배치 시작 시 리셋, 무효화 후 재생성 |

---

## 4. 시나리오별 영향 매트릭스

| 생성 수 | 배치 구성 | 용접 누락 | 컨텍스트 단절 | 실제 품질 영향 |
|---------|----------|----------|-------------|--------------|
| 1~5 | [1~5] | 없음 | 없음 | 없음 |
| 6 | [1~5]+[6] | Arc 5→6 | 없음 (L278 재생성) | **미미** |
| 7 | [1~5]+[6~7] | Arc 5→6 | 없음 | **미미** |
| 10 | [1~5]+[6~10] | Arc 5→6 | 없음 | **미미** |
| 11 | [1~5]+[6~10]+[11] | Arc 5→6, 10→11 | 없음 | **미미~낮음** |
| 15 | 3배치 | Arc 5→6, 10→11 | 없음 | **낮음** |
| 50 | 10배치 | 9곳 누락 | 없음 | **낮음~중간** |

**"미미"인 이유:** C단계 순차 설계에서 `last_refined_context`가 이전 아크 전체를 LLM에 전달. LLM이 인과율을 암묵적으로 유지. 용접은 **Python 수준의 보조 검증**이므로, 누락이 치명적이지는 않음.

---

## 5. 결론

### 5아크 vs 6아크는 다른가?

**답: 구조적으로 다르다. 그러나 실제 품질 영향은 미미하다.**

- **구조적 차이:** 6아크 생성 시 Arc 5→6 인과율 용접이 누락됨 (P1)
- **품질 영향이 미미한 이유:** C단계 순차 설계에서 LLM이 전체 컨텍스트를 받아 연결을 유지하므로, Python 용접 누락이 LLM 설계 품질에 직접 영향을 주지 않음
- **잠재 위험:** 50아크 이상 대규모 생산 시 용접 누락 9곳이 누적되면 `joint_docs` 정합성 검사의 누적 이점을 잃음

### 권고 사항 (코드 수정 없이)

1. **현행 유지 가능:** 5아크 단위 배치가 기본값이고, UI에서 "10개(2배치) 이내 권장"으로 안내. 현재 워크플로우에서 문제 발생 가능성 낮음.
2. **인지만 해두기:** 배치 경계(5, 10, 15, ...)에서 `stitch_joints()` 누락이 있다는 사실을 알고 있으면 됨. 해당 아크 경계에서 수동 검수 시 주의.
3. **미래 개선 후보:** 배치 루프 시작 시 "직전 배치 마지막 아크 + 현재 배치 첫 아크" 용접을 추가하면 P1 해소. 단, 현재 ROI는 낮음.

---

## 부록: 관련 코드 위치

| 파일 | 라인 | 내용 |
|------|------|------|
| `modules/core/constants.py` | L304 | `ARC_BATCH_SIZE = 5` |
| `modules/core/stage2_orchestrator.py` | L268-269 | 배치 루프 (`range(done_count, target_limit, 5)`) |
| 동상 | L278 | 배치 시작 시 `last_refined_context` 생성 |
| 동상 | L282-318 | A단계: 병렬 농축 (`asyncio.gather`) |
| 동상 | L392-423 | B단계: 인과율 용접 (`stitch_joints`, 배치 내부만) |
| 동상 | L425-627 | C단계: 순차 설계 (`while idx < len(enriched_batch)`) |
| 동상 | L626 | `last_refined_context` 갱신 (아크 완성 후) |
| `modules/domain/agents/arc_ensemble.py` | L159-178 | 앙상블 3전략 정의 |
| 동상 | L414-446 | 앙상블 병렬 생성 (`ThreadPoolExecutor(3)`) |
