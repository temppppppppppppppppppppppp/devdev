# XC-MEM-T4: 사망 NPC Regex 엣지 케이스 — 상세 분석

> 날짜: 2026-03-13
> Track: XC-MEM / Target: T4
> 대상: `modules/core/truth_gate.py:79-152`

---

## 1. 분석 범위

`_check_deceased_resurrection()` 메서드의 사망 NPC 감지 로직에서 한글 이름 매칭의 엣지 케이스를 분석한다.

---

## 2. 코드 증거

### 2.1 핵심 감지 로직

```python
# truth_gate.py:116-152
for name in deceased_names:
    if not name or len(name) < 2:        # (1) 단음절 필터
        continue

    for line in manuscript.split("\n"):
        if name not in line:              # (2) 부분 문자열 포함 검사
            continue

        _esc = re.escape(name)
        _lb = r"(?<![가-힣])"            # (3) 한글 lookbehind
        action_patterns = [
            rf"{_lb}{_esc}[이가은는]\s",  # (4) 주어 패턴
            rf'{_lb}"{_esc}',            # (5) 대사 패턴
            rf"{_lb}{_esc}.*말했다",
            rf"{_lb}{_esc}.*외쳤다",
            rf"{_lb}{_esc}.*달려",
            rf"{_lb}{_esc}.*공격",
        ]
        is_recall = any(kw in line for kw in recall_patterns)  # (6) 회상 판별
```

### 2.2 엣지 케이스 분석

#### Case A: 단음절 NPC 이름 무시 (`len(name) < 2`)

- **영향**: "검", "란", "홍" 등 단음절 이름의 NPC가 사망 후 부활해도 감지 안 됨
- **현실적 확률**: 웹소설 NPC가 단음절 이름인 경우는 극히 드뭄. 보통 2-3자 (예: "검황", "홍련")
- **단음절이 필터되는 이유**: `name in line` 검사에서 1글자 한글은 false positive가 극심 (예: "검"이 "검은", "검사", "검토" 등에 매칭)
- **판정**: 합리적 설계 결정

#### Case B: 부분 문자열 매칭 (`name in line` at L122)

- **시나리오**: 사망 NPC "김"이 있을 때 "김철수가 말했다"에서 매칭
- **방어**: `len(name) < 2` 필터로 단음절 제외. 2글자 이상에서:
  - NPC "철수"가 사망: "철수가 말했다" → 정상 매칭
  - NPC "철수"가 사망: "김철수가 말했다" → `(?<![가-힣])철수` lookbehind로 "김" 다음의 "철수"는 **매칭되지 않음** → false negative!

```python
# 구체적 예시
name = "철수"
line = "김철수가 걸어갔다"
# name in line → True (L122 통과)
# action_pattern: r"(?<![가-힣])철수[이가은는]\s"
# "김철수가" 에서 "철수" 앞에 "김" (가-힣)이 있으므로 lookbehind 불통과
# → FALSE NEGATIVE: 사망한 "철수"가 "김철수"의 부분으로 나타나면 미감지
```

- **역방향**: NPC "김철수"가 사망 시 "김철수가 말했다" → `(?<![가-힣])김철수[이가은는]` → "김" 앞이 줄 시작이므로 정상 매칭
- **판정**: lookbehind가 정확히 의도대로 동작. "철수"라는 독립 NPC와 "김철수"라는 NPC가 별개로 존재하는 경우만 문제이나, 이는 네이밍 충돌이지 regex 버그는 아님

#### Case C: 유사 이름 NPC 간 간섭

- **시나리오**: "무영"(사망)과 "무영검"(생존) 두 NPC 존재
  - "무영검이 공격했다" → `(?<![가-힣])무영` → "무영검"에서 "무영" 부분이 매칭 → **FALSE POSITIVE**
  - lookbehind는 "무영" 앞만 검사하지, "무영" 뒤의 추가 글자는 검사하지 않음

```python
name = "무영"  # 사망
line = "무영검이 공격했다"
# name in line → True
# pattern: r"(?<![가-힣])무영.*공격"
# "무영검이 공격했다" → "무영" 앞이 줄 시작(lookbehind 통과) + ".*공격" 매칭
# → FALSE POSITIVE: 생존한 "무영검"의 행동이 사망한 "무영"의 부활로 오감지
```

- **판정**: **실제 위험이 있는 엣지 케이스**. lookahead (`(?![가-힣])`)가 없어 이름 뒤의 한글 추가 문자를 구분하지 못함

#### Case D: 회상 키워드 근접도 부재

```python
# truth_gate.py:114,136
recall_patterns = ["회상", "과거", "기억", "떠올", "추억", "생전", "살아있을 때", "그때"]
is_recall = any(kw in line for kw in recall_patterns)
```

- **시나리오**: 200자짜리 줄에서 앞부분에 "회상"이 있고 뒷부분에 "김철수가 공격했다"가 있는 경우
  - `is_recall = True` → 경고 억제
  - 그러나 실제로는 "회상"과 "김철수" 행동이 무관한 내용일 수 있음
- **반대**: 줄 단위 검사이므로, 한 줄에 "회상"과 행동이 함께 있으면 대부분 관련 문맥
- **판정**: 줄 단위 근접도가 합리적 수준의 휴리스틱. 완벽하지는 않으나 실용적

#### Case E: 대사 패턴의 따옴표 의존

```python
rf'{_lb}"{_esc}',  # 대사 시작
```

- **시나리오**: 한국 소설에서 대사 마커로 큰따옴표 `"` 대신 겹낫표 `『』`, 작은따옴표 `'`, 하이픈 `-` 사용 시 미감지
- **판정**: 대부분의 웹소설 플랫폼(카카오/네이버)은 큰따옴표 사용이 표준. 다만 역설계 원고에서 다른 마커를 쓸 가능성 있음

---

## 3. Finding

### [XC-MEM-T4-001] P2 | 유사 이름 NPC의 false positive (lookahead 부재)

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T4-001 |
| Severity | P2 |
| 현상 요약 | 사망 NPC 이름이 생존 NPC 이름의 접두사인 경우(예: "무영" vs "무영검"), lookbehind만 있고 lookahead가 없어 생존 NPC의 행동이 사망 NPC 부활로 오감지됨 |
| 코드 근거 | `truth_gate.py:128-135` — `rf"{_lb}{_esc}[이가은는]\s"` 등 패턴에 이름 뒤 한글 문자 검사(lookahead) 없음. `_lb = r"(?<![가-힣])"` lookbehind만 적용 |
| 영향 경계 | TruthGate advisory → Director 판정. CRITICAL severity 경고가 Director에게 전달되어 REJECT 유도 가능 |
| 테스트 근거 | `tests/test_truth_gate.py` — 유사 이름 NPC 간 간섭 테스트 없음 |
| 기존 중복 여부 | 기존 262+ finding에 사망 NPC regex false positive 지적 없음 |
| 권장 후속 조치 | action_patterns에 `(?![가-힣])` lookahead 추가: `rf"{_lb}{_esc}(?![가-힣])[이가은는]\s"` (1h) |

### [XC-MEM-T4-002] P3 | 단음절 NPC 이름 완전 무시

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T4-002 |
| Severity | P3 |
| 현상 요약 | `len(name) < 2` 필터로 단음절 NPC 이름(예: "검", "란")이 사망 후 부활해도 감지 불가 |
| 코드 근거 | `truth_gate.py:117-118` `if not name or len(name) < 2: continue` |
| 영향 경계 | 단음절 NPC 이름을 사용하는 프로젝트에서만 영향. 웹소설에서 단음절 NPC는 극히 드뭄 |
| 테스트 근거 | 단음절 이름 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | 조치 불필요. 단음절 이름의 false positive 비용이 false negative 비용보다 높음 |

### [XC-MEM-T4-003] P3 | 대사 마커 다양성 미지원

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T4-003 |
| Severity | P3 |
| 현상 요약 | 대사 패턴이 큰따옴표(`"`)만 검사하여, `『』`, `「」`, `'`, `-` 등 대체 마커 사용 시 대사 감지 불가 |
| 코드 근거 | `truth_gate.py:130` `rf'{_lb}"{_esc}'` — 큰따옴표만 매칭 |
| 영향 경계 | 비표준 대사 마커를 사용하는 원고에서 false negative |
| 테스트 근거 | 대체 대사 마커 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | 대사 패턴을 `rf'{_lb}["\'\u300e\u300f\u300c\u300d]{_esc}'`로 확장 (0.5h) |

### [XC-MEM-T4-004] P3 | 행동 패턴 목록의 한정성

| 필드 | 내용 |
|------|------|
| ID | XC-MEM-T4-004 |
| Severity | P3 |
| 현상 요약 | 행동 패턴이 6개(주어, 대사, 말했다, 외쳤다, 달려, 공격)로 한정되어, "걸어갔다", "웃었다", "검을 뽑았다" 등 다양한 행동 동사를 미감지 |
| 코드 근거 | `truth_gate.py:128-135` — 6개 패턴만 정의 |
| 영향 경계 | false negative 증가. 그러나 advisory 모드이므로 blocking하지 않음 |
| 테스트 근거 | 추가 행동 동사 테스트 없음 |
| 기존 중복 여부 | 기존 finding에 동일 지적 없음 |
| 권장 후속 조치 | 주어 패턴(`{name}[이가은는]\s`)만으로 대부분 감지 가능. 추가 동사 패턴은 false positive 증가 위험. 현재 수준 유지 권장 |

---

## 4. 종합 판정

T4 영역에서 **실질적 위험이 있는 finding은 XC-MEM-T4-001**(유사 이름 false positive)이다. 나머지는 합리적 설계 결정이거나 영향 범위가 극히 제한적이다. XC-MEM-T4-001은 lookahead 1줄 추가로 수정 가능하며, 공수 1h 이내이다.
