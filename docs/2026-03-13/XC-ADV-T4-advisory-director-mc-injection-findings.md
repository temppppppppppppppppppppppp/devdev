# XC-ADV-T4: Advisory->Director MC 주입 충실도 — Findings

> 감사 일자: 2026-03-13
> 초점: Advisory 결과가 Director MC 파트에 충실하게 주입되는가, 라운드 간 누수는 없는가

---

## 분석 요약

Advisory 결과는 `_run_advisory_chain()` → `_suppress_conflicting_advisories()` → 포맷팅 → `_director_mc_parts` prepend 경로를 거쳐 Director에 주입된다. 이 경로의 충실도와 라운드 간 격리를 분석한다.

---

## PASS 1: 후보 수집

### [XC-ADV-016] P2 | _last_advisory_summary 인스턴스 변수 라운드 간 잔류

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-016 |
| Severity | P2 |
| 현상 요약 | `_last_advisory_summary`와 `_last_advisory_details`가 인스턴스 변수로, 동일 InterviewRound 인스턴스가 다중 라운드에 재사용되면 이전 라운드 결과가 잔류 |
| 코드 근거 | `stage4_interview_round.py:58-59` (초기화), `1290-1291` (라운드 시작 시 리셋), `1583` (저장), `1618` (저장) |
| 영향 경계 | Stage 4 — 다중 라운드 시 이전 advisory 결과 누수 가능 |
| 테스트 근거 | 기존 테스트에서 다중 라운드 advisory 격리 미검증 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 현재 **L1290-1291에서 라운드 시작 시 리셋**하고 있으므로, 정상 흐름에서는 누수 없음. 다만, 리셋 전에 `_last_advisory_summary`를 참조하는 코드(L3015, L3247, L4602)가 있어, 라운드 간 경계에서 race가 발생하면 이전 값 참조 가능. 공수 0.2h (방어적 리셋 위치 확인) |

**코드 스니펫:**
```python
# L58-59 — 인스턴스 초기화
self._last_advisory_summary = {}
self._last_advisory_details: list[str] = []

# L1290-1291 — 라운드 시작 시 리셋
self._last_advisory_summary = {}
self._last_advisory_details = []

# L1583 — advisory 완료 후 저장
self._last_advisory_summary = dict(_advisory_summary)

# L1618 — 포맷팅 완료 후 저장
self._last_advisory_details = list(_advisory_parts)
```

**분석:**
- `run()` 메서드 진입 후 L1290-1291에서 리셋 → L1583/1618에서 새 값 저장.
- 리셋과 저장 사이의 코드 경로에서 `_last_advisory_summary`를 참조하는 곳은 없으므로, 이전 라운드 값이 현재 라운드에 영향을 미치지 않는다.
- 다만, `_last_advisory_summary`는 라운드 완료 후 후속 처리(L3015, L3247)에서 참조되므로, 라운드 완료 시점의 값은 정확하다.
- **결론: 현재 코드에서 라운드 간 누수는 발생하지 않음.**

---

### [XC-ADV-017] P2 | "이상 없음" 필터링으로 인한 정보 손실

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-017 |
| Severity | P2 |
| 현상 요약 | advisory 결과에 "이상 없음" 또는 "경고 0건"이 포함되면 축약형으로 변환되어, 실제 검사 수행 여부만 표시되고 상세 결과가 삭제됨 |
| 코드 근거 | `stage4_interview_round.py:1589-1592` |
| 영향 경계 | Stage 4 — Director가 "이상 없음" advisory의 검사 범위를 파악 불가 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 현재 설계는 합리적 (Director에게 불필요한 정보 줄임). 다만, 검사 대상 NPC 수나 수치 항목 수 등의 메타 정보를 축약에 포함하면 Director의 신뢰도 판단에 도움. 공수 0.5h |

**코드 스니펫:**
```python
# L1589-1592
if "이상 없음" in _part_s or "경고 0건" in _part_s:
    _short_name = _part_s.split("]")[0].replace("[", "").strip() if "]" in _part_s else "Advisory"
    _formatted_advisory_parts.append(f"[{_short_name}] 이상 없음")
    continue
```

---

### [XC-ADV-018] P2 | TruthGate 경고 10건 상한 truncation

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-018 |
| Severity | P2 |
| 현상 요약 | TruthGate 경고가 10건을 초과하면 `_tg_warnings_all[:10]`으로 잘림, Director에게 잘린 사실이 전달되지 않음 |
| 코드 근거 | `stage4_interview_round.py:3866` — `for _w in _tg_warnings_all[:10]:` |
| 영향 경계 | Stage 4 — CRITICAL 경고 누락 가능 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 10건 상한 후 잔여 건수를 요약 라인으로 추가 (예: "... 외 N건 추가 경고"). 공수 0.2h |

**분석:**
- 후보 3개 x 각 7개 검사 = 최대 21건 경고 가능.
- 10건 잘림 시 Director가 일부 CRITICAL 경고를 보지 못할 수 있다.
- 다른 advisory도 유사한 상한 존재: NpcDrift 8건(L3905), Flashback 6건(L4002), InfoParadox 6건(L4060), RelDrift 6건(L4108), LongTermRep 6건(L4150), NumericConsistency 10건(L4208).

---

### [XC-ADV-019] P3 | _advisory_summary dict의 단순 플래그 방식

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-019 |
| Severity | P3 |
| 현상 요약 | `_advisory_summary`가 `{"truth_gate": 1, "npc_drift": 1, ...}` 단순 존재 플래그만 저장하여, 경고 건수/심각도 정보가 누락됨 |
| 코드 근거 | `stage4_interview_round.py:1566-1583` |
| 영향 경계 | Stage 4 — 후속 처리(L3015, L3247, L4602)에서 advisory 강도 판단 불가 |
| 테스트 근거 | 해당 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 건수 저장으로 변경 (예: `_advisory_summary["truth_gate"] += 1` 방식). 공수 0.3h |

**코드 스니펫:**
```python
# L1566-1583
_advisory_summary = {}
for _part in _advisory_parts or []:
    _part_s = str(_part)
    if "[TruthGate" in _part_s:
        _advisory_summary["truth_gate"] = 1       # ← 건수 아닌 플래그
    if "[LM-B]" in _part_s or "NpcDrift" in _part_s:
        _advisory_summary["npc_drift"] = 1
    # ...
```

---

### [XC-ADV-020] P3 | 포맷팅 단계에서 원본 텍스트 유지 미확인

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-020 |
| Severity | P3 |
| 현상 요약 | TruthGate 포맷팅에서 원본 태그를 제거한 후 `[CRITICAL · TruthGate]`로 재포맷하면서, 원본 경고 텍스트의 줄바꿈 구조가 변형될 수 있음 |
| 코드 근거 | `stage4_interview_round.py:1593-1603` |
| 영향 경계 | Stage 4 — Director 프롬프트 가독성 |
| 테스트 근거 | 커버리지 0% |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 현재 코드는 `.replace().strip()`으로 안전하게 처리. 줄바꿈 보존됨. 실질 위험 없음 |

**코드 스니펫:**
```python
# L1593-1603
if "[TruthGate" in _part_s:
    _body = (
        _part_s.replace("[TruthGate Advisory — CRITICAL 경고 시 반드시 REJECT]", "")
        .replace("[TruthGate Advisory]", "")
        .replace("[TruthGate]", "")
        .strip()
    )
    _formatted_advisory_parts.append(
        f"[CRITICAL · TruthGate] {_body}" if _body else "[CRITICAL · TruthGate]"
    )
```

---

### [XC-ADV-021] P2 | _director_mc_parts 조립 순서 — advisory가 최상단

| 필드 | 내용 |
|------|------|
| ID | XC-ADV-021 |
| Severity | P2 |
| 현상 요약 | `_director_mc_parts = _advisory_parts + _director_mc_parts` (L1619)로 advisory가 MC 최상단에 배치되어, Director 프롬프트에서 가장 먼저 읽힘 |
| 코드 근거 | `stage4_interview_round.py:1619` |
| 영향 경계 | Stage 4 — Director 판정 bias |
| 테스트 근거 | 해당 없음 (설계 판단) |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 현재 설계는 **의도적**. Advisory(특히 CRITICAL TruthGate)가 Director의 첫 번째 맥락으로 제공되어 REJECT 판정을 유도하는 것이 목적. 대원칙 4(사망 캐릭터)와 부합. 유지 권장 |

---

## PASS 2: 교차 검증

| ID | PASS 1 신뢰도 | PASS 2 판정 | 근거 |
|----|-------------|------------|------|
| XC-ADV-016 | HIGH | **유효 (낮은 위험)** | L1290-1291 리셋 확인, 현재 누수 경로 없음 |
| XC-ADV-017 | MED | **유효** | 설계 의도적이나 메타 정보 부재 |
| XC-ADV-018 | HIGH | **유효** | 10건 상한 확인, CRITICAL 누락 가능 |
| XC-ADV-019 | MED | **유효** | 플래그 방식 확인 |
| XC-ADV-020 | LOW | **위양성 제거** | 실질 위험 없음 확인 |
| XC-ADV-021 | HIGH | **유효 (설계 의도)** | 의도적 배치 확인 |

---

## PASS 3: 최종 확정

| ID | 최종 Severity | 비고 |
|----|-------------|------|
| XC-ADV-016 | **P3** | 하향 조정 — 현재 코드에서 누수 없음 확인 |
| XC-ADV-017 | **P3** | 하향 조정 — 설계 의도적 축약 |
| XC-ADV-018 | **P2** | 유지 — CRITICAL 경고 truncation은 품질 위험 |
| XC-ADV-019 | **P3** | 유지 — 개선 여지 존재하나 기능 영향 없음 |
| XC-ADV-020 | 제거 | 위양성 — 실질 위험 없음 |
| XC-ADV-021 | **P3** | 하향 조정 — 의도적 설계 |

---

## 총평

Advisory→Director MC 주입 경로는 전반적으로 **충실하게 구현**되어 있다.

핵심 발견:
1. **라운드 간 누수 없음**: L1290-1291 리셋이 올바르게 작동.
2. **TruthGate 10건 상한**(XC-ADV-018)이 유일한 실질적 품질 위험. 후보 3개 x 7검사 = 21건 가능한데 10건만 전달.
3. 포맷팅은 태그 정리 + 우선순위 헤더 재부착으로 Director 가독성을 높이는 합리적 설계.
4. advisory 최상단 배치(XC-ADV-021)는 대원칙 4 준수를 위한 의도적 설계.
