# XC-ADV-T3: Advisory 충돌 억제 양방향성 — Findings

> 감사 일자: 2026-03-13
> 초점: `_suppress_conflicting_advisories()` 억제 로직의 단방향/양방향성, 엣지 케이스

---

## 분석 요약

억제 로직은 상위 티어(TruthGate=3, NpcDrift/RelDrift/Flashback/InfoParadox=2, NumericDrift/LongTermRep=1)가 동일 대상을 가리키는 하위 티어를 제거하는 단방향 구조이다. 아래에서 양방향 충돌 가능성과 엣지 케이스를 분석한다.

---

## PASS 1: 후보 수집

### [XC-ADV-011] P2 | 동일 티어 간 충돌 억제 부재

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-011 |
| Severity | P2 |
| 현상 요약 | 티어 2 advisory (NpcDrift, RelDrift, Flashback, InfoParadox) 간 동일 대상 중복 경고 시 억제 불가 |
| 코드 근거 | `stage4_interview_round.py:1091` — `low["tier"] >= high["tier"]` 조건으로 동일 티어 스킵 |
| 영향 경계 | Stage 4 — Director MC 파트에 중복 경고 주입 |
| 테스트 근거 | 커버리지 0% (억제 로직 직접 테스트 없음) |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 동일 티어 내에서 `kind`가 다르고 동일 NPC를 가리키는 경우 합산/축약 로직 추가 가능. 다만, Director 주권주의(대원칙 3)에 의해 중복 경고가 오히려 바람직할 수 있음. 설계 판단 필요. 공수 1h |

**코드 스니펫:**
```python
# L1087-1101
for high in sorted(meta, key=lambda item: (-item["tier"], item["idx"])):
    if high["idx"] in suppressed:
        continue
    for low in meta:
        if low["idx"] == high["idx"] or low["idx"] in suppressed or low["tier"] >= high["tier"]:
            continue  # ← 동일 티어면 스킵 → 억제 불가
        # ... overlap 검사 ...
        if overlap:
            suppressed.add(low["idx"])
```

**분석:**
- 예시 시나리오: NpcDrift(티어2)가 "김철수" NPC 역할 변경을 감지, RelDrift(티어2)가 "김철수 ↔ 주인공" 관계 역전을 감지.
- 두 advisory는 동일 NPC를 가리키지만, 둘 다 티어 2이므로 어느 쪽도 억제되지 않는다.
- Director에게 같은 NPC에 대해 2개의 MAJOR 경고가 전달된다.
- **이것이 실제 문제인가?** Director 주권주의 관점에서, 서로 다른 관점(속성 표류 vs 관계 표류)의 경고를 모두 제공하는 것이 바람직할 수 있다.

---

### [XC-ADV-012] P3 | explicit/broad 키워드 매칭의 오탐 가능성

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-012 |
| Severity | P3 |
| 현상 요약 | `_extract_advisory_subjects()`의 broad 매칭이 공통 한국어 토큰으로 인해 비관련 advisory를 잘못 억제할 수 있음 |
| 코드 근거 | `stage4_interview_round.py:1023-1064` |
| 영향 경계 | Stage 4 — advisory 억제 정확도 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 현재 stopwords 18개는 합리적이나, "원고", "검사", "변경" 같은 빈출 용어가 누락되면 오탐 가능. 모니터링 후 stopwords 확장 권장. 공수 0.3h |

**코드 스니펫:**
```python
# L1023-1064 — 키워드 추출
explicit = {match.group(1).strip() for match in _re.finditer(r"'([^']{2,40})'", text) ...}
# explicit: 작은따옴표로 감싼 NPC명 등
broad = set(explicit)
for token in _re.findall(r"[가-힣A-Za-z][가-힣A-Za-z0-9_]{1,}", text):
    if token.lower() in stopwords:
        continue
    broad.add(token)
# broad: 2글자 이상 모든 한글/영문 토큰
```

**분석:**
- `explicit` 집합: 작은따옴표로 감싼 NPC명, 아이템명 등 — 정밀도 높음.
- `broad` 집합: 모든 2글자+ 토큰 — "투자금", "수련", "전투" 같은 일반 용어도 포함.
- 억제 로직에서 `high["explicit"] & low["broad"]` 교차를 검사하므로, 상위 advisory의 explicit(NPC명)이 하위 advisory의 broad(일반 텍스트)에 포함되면 억제 발동.
- NPC명이 "수련"이나 "발견" 같은 일반 명사이면 오탐 가능성이 있으나, 실제 NPC명은 보통 2-6자 고유명사이므로 위험은 낮다.

---

### [XC-ADV-013] P3 | NumericConsistency 미분류 — 기본 티어 1 할당

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-013 |
| Severity | P3 |
| 현상 요약 | NumericConsistency advisory가 `_classify_advisory_tier()`에서 매칭되지 않아 기본값 `(1, "Advisory")`로 분류됨 |
| 코드 근거 | `stage4_interview_round.py:1004-1021` |
| 영향 경계 | Stage 4 — NumericConsistency 억제 판정 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `_classify_advisory_tier()`에 NumericConsistency 매칭 조건 추가. 현재 출력 텍스트에 "[NumericConsistency"가 포함되므로 매칭 가능. 공수 0.1h |

**코드 스니펫:**
```python
# L1004-1021
@staticmethod
def _classify_advisory_tier(advisory_text: str) -> tuple[int, str]:
    text = str(advisory_text or "")
    if "[TruthGate" in text:       return 3, "TruthGate"
    if "[LM-B]" or "NpcDrift":     return 2, "NpcDrift"
    if "[LM-D]" or "RelDrift":     return 2, "RelDrift"
    if "[LM-E]" or "Flashback":    return 2, "Flashback"
    if "[LM-F]" or "InfoParadox":  return 2, "InfoParadox"
    if "[LM-C]" or "NumericDrift": return 1, "NumericDrift"
    if "[LM-P1]" or "LongTerm":   return 1, "LongTermRepetition"
    return 1, "Advisory"  # ← NumericConsistency는 여기로 fall-through
```

**분석:**
- NumericConsistency 출력은 `"[NumericConsistency — Python 수치 검증 결과...]"`로 시작한다.
- 이 텍스트는 위 if 체인에서 어느 조건에도 매칭되지 않아 기본 `(1, "Advisory")`로 분류된다.
- kind가 "Advisory"이므로 로깅의 suppression 메시지에서 정체가 불명확해진다.
- 실질 위험은 낮다 (티어 1이므로 상위 티어에 의해 적절히 억제됨).

---

### [XC-ADV-014] P2 | 억제 로직이 advisory 내용 손실 여부를 추적하지 않음

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-014 |
| Severity | P2 |
| 현상 요약 | 억제된 advisory 건수/내용이 Director에게 전달되지 않아, Director가 억제 사실을 인지할 수 없음 |
| 코드 근거 | `stage4_interview_round.py:1109` — 억제된 파트 단순 제거 후 반환 |
| 영향 경계 | Stage 4 — Director 판정의 정보 완전성 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 억제된 건수를 요약 라인으로 Director MC에 포함 (예: "[참고] 하위 중복 경고 2건 억제됨"). 공수 0.3h |

---

### [XC-ADV-015] P3 | 단방향 억제는 설계 의도와 부합

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-015 |
| Severity | P3 |
| 현상 요약 | 억제 방향이 상위→하위 단방향이며, 양방향 억제는 의도적으로 배제됨 |
| 코드 근거 | `stage4_interview_round.py:1066-1067` — docstring "상위 티어와 같은 대상을 가리키는 하위 advisory는 Director MC에서 제거" |
| 영향 경계 | 해당 없음 (설계 확인) |
| 테스트 근거 | 해당 없음 |
| 기존 중복 여부 | 해당 없음 |
| 권장 후속 조치 | 현재 설계 유지. TruthGate(CRITICAL)가 NPC 사망을 감지하면, 같은 NPC에 대한 NpcDrift(MAJOR) 경고는 중복이므로 억제하는 것이 올바름. |

---

## PASS 2: 교차 검증

| ID | PASS 1 신뢰도 | PASS 2 판정 | 근거 |
|----|-------------|------------|------|
| XC-ADV-011 | HIGH | **유효** | 동일 티어 미억제는 코드에서 명확히 확인됨. 다만 설계 의도 가능 |
| XC-ADV-012 | MED | **유효 (낮은 위험)** | NPC 고유명사 ↔ 일반명사 오탐 시나리오 가능하나 실현 확률 낮음 |
| XC-ADV-013 | HIGH | **유효** | NumericConsistency 미분류 코드에서 확인 |
| XC-ADV-014 | MED | **유효** | Director 주권주의 관점에서 정보 손실 우려 |
| XC-ADV-015 | HIGH | **유효 (정보성)** | 설계 확인 완료 |

---

## PASS 3: 최종 확정

| ID | 최종 Severity | 비고 |
|----|-------------|------|
| XC-ADV-011 | **P2** | 동일 티어 중복 경고 — Director 부담 증가 가능. 설계 판단 필요 |
| XC-ADV-012 | **P3** | broad 매칭 오탐 — 실현 확률 낮음 |
| XC-ADV-013 | **P3** | NumericConsistency 미분류 — 기능 영향 없으나 로깅 불명확 |
| XC-ADV-014 | **P2** | 억제 사실 미전달 — Director 정보 완전성 저해 |
| XC-ADV-015 | **P3** | 정보성 — 단방향 억제는 올바른 설계 |

---

## 총평

억제 로직은 **티어 기반 단방향 설계**로 구현되어 있으며, 이는 "TruthGate CRITICAL이 하위 MAJOR/INFO와 같은 대상을 가리킬 때 중복 제거"라는 명확한 목적에 부합한다.

주요 개선 영역:
1. **동일 티어 간**(XC-ADV-011) 중복은 현재 억제되지 않아 Director에게 같은 NPC에 대해 2-3개 경고가 동시 전달될 수 있음. 설계 판단 필요.
2. **NumericConsistency 미분류**(XC-ADV-013)는 간단한 조건 추가로 해결 가능.
3. **억제 사실 미전달**(XC-ADV-014)은 Director의 정보 완전성을 위해 요약 라인 추가 권장.
