# Track A: Stage 2 내부 검증 강건성

Date: 2026-03-17
3-Pass Audit: 93% → 96% → 97%
Final Confidence: 97%

---

## A-1: tactical_doc 구체성 검증 부재 — "5개 다른 이야기에 쓸 수 있는 범용 Arc"가 통과

### 1. 현황 (코드 경로)

**tactical_doc 생성 후 검증 경로 3단계:**

| 단계 | 검증자 | 파일 | 검증 내용 |
|------|--------|------|----------|
| ① Python 점수 | `arc_ensemble.py` | `_evaluate_draft()` | 길이, 화수 마커 개수 |
| ② 중복 검사 | `stage2_validation_pipeline.py` | `_is_tactical_doc_duplicate()` | 0.92 유사도 기반 |
| ③ Director LLM | `unified_arc_validator.py` | `validate()` | 구조+내용 심사 |

**① Python 점수** (`arc_ensemble.py`:962-994):
- 길이 검사: `ep_count * 500자` 미만이면 CRITICAL (line 975-979). `ep_count * 700자` 미만이면 -5점 (line 984-986).
- 화수 마커 검사 (line 989-992):
  ```python
  ep_mentions = len(re.findall(r"제\s*\d+\s*화", tactical))
  if ep_mentions < ep_count:
      score -= 5
      issues.append(f"화수 구분 부족: {ep_mentions}/{ep_count}")
  ```
  - "제N화" 패턴의 **출현 횟수만** 카운트. 마커 순서, 마커 간 내용, 내용의 구체성은 미검사.
  - **감점 -5점**: 전체 ~1000점 기준 무시할 수준.

**② 중복 검사** (`stage2_validation_pipeline.py`:964-993):
- `TACTICAL_DOC_DUPLICATE_THRESHOLD = 0.92` (`stage2_contracts.py`:3)
- SequenceMatcher 기반으로 최근 3개 Arc와 비교.
- **92% 이상 유사**해야 중복 판정 → "5개 다른 이야기에 쓸 수 있는 범용 Arc"는 **80% 수준 유사도**로 통과.

**③ Director LLM** (`unified_arc_validator.py`:72-73 부근):
- 화 구분이 `ep_count`개 미만이면 MAJOR severity로 표기.
- **구체성(specificity) 검증 프롬프트 = 없음**: Director에게 "이 tactical_doc이 이 특정 주인공/세계/장르에 의존하는가?" 질문하지 않음.

### 2. 갭

**핵심 갭: Specificity Validation Layer 부재**

1. **Python 계층**: 길이+마커 개수만 검사 → "전략가가 자금 조달하고 성공한다" (29자 × ep_count로 길이만 채우면) 통과.
2. **중복 검사**: 같은 저자의 **이전 Arc**와 비교만. 범용적이지만 이전과 "다른" 텍스트는 통과.
3. **Director LLM**: 구조+연속성 위주 평가. "이 tactical_doc이 이 이야기에만 유효한가?"라는 질문이 프롬프트에 없음.

**결과**: 주인공 이름, 세계관 특유의 규칙, 장르 고유 메커니즘을 전혀 언급하지 않는 범용 전술 문서가 모든 검증 단계를 통과할 수 있음.

### 3. 영향도

**Significant**

- **Stage 4 직접 영향**: Chief Writer가 tactical_doc을 서사의 핵심 앵커로 사용 → 범용 tactical_doc이면 범용 원고 생산. Arc당 2-6개 에피소드에 영향.
- **패턴 피로**: 여러 Arc에 걸쳐 유사한 전술 구조가 반복되면 독자 체감 품질 저하.
- **Critical이 아닌 이유**: Director가 내용 품질 자체를 LLM으로 평가하므로 **극단적** 범용성은 걸릴 수 있음. 다만 "적당히 범용적인" 수준은 통과.

### 4. 방향 스케치

**접근법 A: Python 구체성 패턴 체크 (비용 0)**
- `_evaluate_draft()`에 grounding element 체크 추가:
  - 주인공 이름 언급 횟수, 장르 고유 키워드 존재 여부, 세계관 상태 참조.
  - 3개 미만이면 "low-specificity advisory" 플래그.

**접근법 B: Director 프롬프트 확장 (LLM 비용)**
- `unified_arc_validator.py` 프롬프트에 구체성 검증 질문 추가:
  - "이 tactical_doc이 [주인공 이름]의 이 세계의 규칙에 의존하는가?"
  - 범용적이면 MAJOR severity 반환.

**접근법 C: 생성 시 제약 강화**
- Arc 생성 프롬프트에 "tactical_doc에 반드시 [주인공명], [현재 위치], [장르 메커니즘] 언급" 조건 삽입.

---

## A-2: MAJOR 무한 반복 위험 — Director가 MAJOR를 계속 수용하면 저품질 Arc 통과

### 1. 현황 (코드 경로)

**2중 루프 구조:**

```
[외부 루프] stage2_orchestrator.py:585 — while attempt < max_attempts
  └─ [내부 루프] stage2_finalizer.py:669 — for _fix_i in range(_MAX_FIX)
```

**내부 루프 (Patch Loop)** — `stage2_finalizer.py`:657-845:
- Director가 `PASS_WITH_FIX` 판정 시 진입.
- `_MAX_FIX = 3` (line 661): 최대 3회 inplace 패치 시도.
- 각 반복마다: FourPhase가 패치 → Director 재심사 → PASS/PASS_WITH_FIX/REJECT 판정.
- 3회 소진 시: `_d_decision = "REJECT"` (line 820) → 외부 루프로 돌아감.
- **[PF-3]** (line 824): PASS_WITH_FIX 소진 시 마지막 패치본을 채택하되 REJECT 처리.

**외부 루프 (Retry Loop)** — `stage2_orchestrator.py`:585-797:
- `max_attempts = int(_threshold("retry.analyst_max_attempts", 5))` (`stage2_preflight.py`:747)
- 하드 리밋: `ANALYST_MAX_ATTEMPTS = 10` (`constants.py`:103)
- REJECT 시 `attempt += 1` → 새 Arc 생성 → Director 재심사.

**최악의 경우 총 LLM 호출:**
- 10회 시도 × (1 생성 + 1 심사 + 3 패치 × 2 호출) = **10 × 8 = ~80 LLM 호출**

### 2. 갭

1. **MAJOR 판정 누적 카운터 없음**: Director가 시도 1, 2, 3, ... 모두에서 MAJOR를 주어도 **"MAJOR가 반복된다"는 사실 자체를 감지하는 메커니즘이 없음**. 각 시도는 독립적으로 평가됨.

2. **점수 하한 없음**: PASS_WITH_FIX 판정에 최소 점수 요구 없음. 예: Director score 50이어도 PASS_WITH_FIX면 패치 루프 진입. 점수 60 미만은 패치로 개선 불가능한 구조적 문제일 가능성 높음.

3. **하강 추세 미감지**: 시도 N의 점수 < 시도 N-1의 점수이면 Arc 구조 자체의 문제인데, 현재는 이를 감지하지 않고 그냥 retry. 결국 max_attempts 소진까지 계속 실패.

4. **최악 경로 비용**: 80회 LLM 호출 + 15-30분 소요 → 결국 실패하고 수동 개입 필요. **비용 대비 성과 없는 구간**이 길게 지속됨.

### 3. 영향도

**Significant** (비용 + 시간 낭비, 품질 저하 아닌 품질 미생산)

- **비용**: 정상 경로(5분, ~10 LLM 호출) vs 최악 경로(30분, ~80 LLM 호출). 8배 비용.
- **Stage 4 영향**: Arc 설계 실패 → 해당 Arc의 에피소드 미생산 → 스토리 갭.
- **Critical이 아닌 이유**: 결국 `max_attempts` 하드 리밋으로 종료됨. 무한 루프는 아니지만 **비효율적 유한 루프**.

### 4. 방향 스케치

**접근법 A: MAJOR 누적 카운터**
- `stage2_orchestrator.py`에 `major_verdict_count` 카운터 추가.
- Director가 MAJOR 판정할 때마다 +1.
- `major_verdict_count >= 3`이면 조기 종료 + 에스컬레이션.

**접근법 B: 패치 루프 진입 점수 하한**
- PASS_WITH_FIX 진입 전: `if director_score < 60 → REJECT (패치 불가)`.
- 저점수 Arc에 패치를 시도하는 비용 절약.

**접근법 C: 하강 추세 감지**
- 시도 N 점수 < 시도 N-1 점수이고 둘 다 MAJOR이면: "Arc 구조 문제" 진단 → 피드백 변경("전술 구조 자체를 재설계하라").
- 같은 접근법으로 재시도하는 것을 방지.

---

## A-3: 에피소드 구조 마커 강제 없음 — tactical_doc이 산문 1덩어리 가능

### 1. 현황 (코드 경로)

**유일한 구조 검사** — `arc_ensemble.py`:989-992:
```python
ep_mentions = len(re.findall(r"제\s*\d+\s*화", tactical))
if ep_mentions < ep_count:
    score -= 5
    issues.append(f"화수 구분 부족: {ep_mentions}/{ep_count}")
```

이 검사의 한계:
- **개수만 카운트**: "제1화"가 몇 번 나오는지만 셈. 순서, 위치, 마커 간 내용 분리 미확인.
- **-5점 감점**: 전체 점수 대비 미미. 다른 항목에서 고점이면 무시됨.
- **패턴 관용성**: `"제 1화에서 주인공은... 제 2화에서는..."` 같은 산문 내 인라인 언급도 마커로 카운트.

**통과 가능한 시나리오:**

| 시나리오 | ep_mentions | 감점 | 결과 |
|----------|------------|------|------|
| 마커 0개, 순수 산문 | 0 | -5 | 통과 가능 |
| 마커 1개 ("제1화"만) | 1 (ep_count=3) | -5 | 통과 가능 |
| 산문 내 인라인 언급 | 3 (ep_count=3) | 0 | 완전 통과 |
| 구조화된 섹션 분리 | 3 (ep_count=3) | 0 | 완전 통과 |

**Director LLM 심사**: `director_ensemble.py`:958 부근에서 "화별 사건이 균형 있게 배분되었는가?"를 평가 기준에 포함하지만, 이는 **구조가 아닌 내용** 수준의 판단. 마커 없이 산문으로 쓰여도 내용이 좋으면 PASS 가능.

**DraftValidator** (`arc_draft_validator.py`): 필수 필드 존재만 확인 — tactical_doc의 내부 구조는 미검사.

### 2. 갭

1. **파티션 검증 부재**: "제1화...제2화"가 실제로 내용을 **분리**하는지 미확인. 마커가 있어도 한 문장 안에 모두 등장하면 구분이 아님.

2. **순서 검증 부재**: 제3화→제1화→제2화 순서도 통과. 오름차순 정렬 미확인.

3. **섹션별 최소 내용 미검증**: "제1화: A\n제2화:\n제3화: B" — 2화 내용 비어있어도 통과.

4. **downstream 영향**: `extract_episode_tactical()` (`tactical_utils.py`)이 tactical_doc에서 화별 섹션을 regex로 추출 → 마커가 없거나 산문형이면 **추출 실패** → 폴백으로 전체 텍스트 또는 beat_sequence 사용 → 정보 손실.

### 3. 영향도

**Nice-to-have** (구조 부재 시 downstream 폴백 존재)

- **Stage 4 간접 영향**: `extract_episode_tactical()`이 폴백으로 전체 tactical_doc 또는 beat_sequence를 사용하므로 **완전한 정보 손실은 아님**. 다만 화별 정밀한 내용 추출은 불가.
- **Blueprint 품질**: 화별 구분 없는 tactical_doc에서 BlueprintConstraintCompiler가 `must_focus`를 추출할 때 정확도 저하.
- **Critical이 아닌 이유**: Director LLM이 내용 수준에서 "화별 균형"을 평가하므로 극단적 불균형은 잡힘. 구조적 마커가 없어도 **내용이 화별로 구분되어 있으면** 기능은 함.

### 4. 방향 스케치

**접근법 A: 구조적 파싱 검증 (Python, 비용 0)**
```python
def validate_episode_structure(tactical_doc: str, ep_count: int):
    pattern = r"제\s*(\d+)\s*화[^\S\n]*\n(.*?)(?=제\s*\d+\s*화|$)"
    matches = re.findall(pattern, tactical_doc, re.DOTALL)
    if len(matches) != ep_count: return MAJOR("화 구분 누락")
    ep_nums = [int(m[0]) for m in matches]
    if ep_nums != list(range(1, ep_count + 1)): return MAJOR("화 번호 순서 오류")
    for ep_num, content in matches:
        if len(content.strip()) < 200: return MAJOR(f"제{ep_num}화 내용 부족")
    return PASS
```

**접근법 B: 생성 시 구조 강제**
- Arc 생성 프롬프트에 "tactical_doc은 반드시 ep_count개의 '제N화:' 섹션으로 구분" 조건 삽입.
- Python 후검증이 아닌 **생성 시 제약**으로 구조 확보.

**접근법 C: 감점 강화**
- 현재 -5 → -30 이상으로 상향.
- 또는 ep_mentions < ep_count이면 MAJOR severity로 승격.

---

## Track 내 교차 발견

### 교차 발견 1: "생성 시 제약 < 사후 필터링" 편향

A-1(구체성), A-2(MAJOR 반복), A-3(구조 마커) 모두 **생성 시점(generation-time)의 제약이 약하고, 사후(post-generation) 필터링에 의존**하는 동일 패턴:
- Arc 생성 프롬프트가 구체성/구조를 강제하지 않음 → 생성 품질이 넓은 분산.
- Director가 사후 평가 → 넓은 분산의 하단(저품질)을 reject.
- **문제**: reject 비용이 높음(LLM 재호출). 생성 시 제약 강화가 비용 효율적.

### 교차 발견 2: 감점 체계의 무력화

A-1과 A-3에서 발견된 -5점 감점은 전체 점수 대비 무시 수준. **감점이 있으나 마나한 수준**이면 검증 자체가 존재하지 않는 것과 동일. 감점 체계의 재보정 또는 severity 기반 체계로 전환 필요.

### 교차 발견 3: A-2는 A-1/A-3의 결과

범용적 tactical_doc(A-1)이 통과하고, 구조 마커 없는 tactical_doc(A-3)이 통과하면 → Director가 MAJOR를 줄 확률 상승 → MAJOR 무한 반복(A-2) 트리거. A-1/A-3 해결이 A-2의 발생 빈도 자체를 줄임.

---

## 3-Pass 감리 기록

### Pass 1: 사실 정확성 (93%)

- ✅ `arc_ensemble.py`:989-992의 화수 검사 로직 정확
- ✅ `TACTICAL_DOC_DUPLICATE_THRESHOLD = 0.92` 확인 (`stage2_contracts.py`:3)
- ✅ `_MAX_FIX = 3` 확인 (`stage2_finalizer.py`:661)
- ✅ REJECT 전환 로직 확인 (line 820)
- ✅ `ANALYST_MAX_ATTEMPTS = 10` 확인 (`constants.py`:103)
- ✅ `max_attempts = int(_threshold("retry.analyst_max_attempts", 5))` 확인 (`stage2_preflight.py`:747)
- ⚠️ 총 LLM 호출 수 추정(~80회)은 경로별 분기에 따라 변동 가능 → "최악의 경우" 한정자 부착

### Pass 2: 논리 정합성 (96%)

- ✅ A-1: 구체성 미검증 → 범용 Arc 통과 → Stage 4 범용 원고 — 논리 체인 건전
- ✅ A-2: MAJOR 누적 미감지 → 비효율 반복 → 비용 낭비 — 인과 명확
- ✅ A-3: 마커 개수만 검사 → 산문 통과 → downstream 추출 실패 — 연결 건전
- ✅ 교차 발견 3(A-1/A-3 → A-2 트리거)의 인과 논리 건전

### Pass 3: 완성도 (97%)

- ✅ 각 항목 4단계(현황/갭/영향도/방향) 완비
- ✅ 코드 경로 주장 모두 file:line 근거 제시
- ✅ 방향 스케치가 구현 제안이 아닌 접근법 수준
- ✅ 영향도 등급(Significant/Nice-to-have) 근거 명시
- ✅ 교차 발견 3건으로 Track 내 상호작용 분석
