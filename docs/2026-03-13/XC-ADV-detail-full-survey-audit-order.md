# XC-ADV Track: 병렬 Advisory 체인 안전성 — Full Survey Audit Order

> 감사 일자: 2026-03-13
> 감사 범위: Advisory Chain 병렬 실행 아키텍처 전반
> 방법론: 3-Pass (수집 → 교차검증 → 위양성 제거)
> 감사 대상 파일 9개, 핵심 코드 라인 ~2,300줄

---

## 1. 감사 대상 파일

| 파일 | 줄수 | 역할 |
|------|------|------|
| `modules/core/stage4_interview_round.py` | ~4,700 | Advisory 병렬 실행 오케스트레이터 |
| `modules/core/truth_gate.py` | 439 | TruthGate — 메모리 오염 방지 (7개 검사) |
| `modules/core/npc_drift_advisor.py` | 193 | NPC 속성 표류 LLM advisory |
| `modules/core/numeric_drift_advisor.py` | 208 | FactLedger 수치 누적 표류 LLM advisory |
| `modules/core/relationship_drift_advisor.py` | 169 | NPC 관계도 표류 LLM advisory |
| `modules/core/flashback_verifier.py` | 199 | 회상/플래시백 오염 LLM advisory |
| `modules/core/info_paradox_checker.py` | 260 | 1인칭 정보 역설 LLM advisory |
| `modules/core/long_term_repetition_advisor.py` | 234 | 20화+ 장기 반복 패턴 LLM advisory |
| `modules/core/numeric_consistency_checker.py` | 1001 | Python-only 수치 정합성 (LLM 0회) |

---

## 2. 타겟 분석 항목

| 타겟 | 초점 | 핵심 코드 라인 |
|------|------|----------------|
| **XC-ADV-T1** | 병렬 실행 중 공유 상태 변이 | `stage4_interview_round.py:3807-3832`, `3841-3859`, `3874-3922` |
| **XC-ADV-T2** | Timeout 캐스케이드 & 예외 삼킴 | `stage4_interview_round.py:3817-3826` |
| **XC-ADV-T3** | Advisory 충돌 억제 양방향성 | `stage4_interview_round.py:1004-1109` |
| **XC-ADV-T4** | Advisory->Director MC 주입 충실도 | `stage4_interview_round.py:1563-1619` |

---

## 3. 아키텍처 요약

```
_run_advisory_chain()  [L3791-3832]
├── ThreadPoolExecutor(max_workers=8)
├── 8개 advisory submit:
│   ├── TruthGate          (candidates, validation_results, next_ep)
│   ├── NpcDrift            (candidates, validation_results, next_ep)
│   ├── NumericDrift        (next_ep)
│   ├── Flashback           (candidates, next_ep)
│   ├── InfoParadox         (candidates, next_ep, genre_name)
│   ├── RelDrift            (candidates, next_ep)
│   ├── LongTermRep         (candidates, next_ep)
│   └── NumericConsistency  (candidates, next_ep)
├── as_completed(timeout=300)
├── future.result(timeout=60) per advisory
└── 결과 → list[str] 반환

_suppress_conflicting_advisories()  [L1066-1109]
├── 티어 분류: TruthGate(3) > NpcDrift/RelDrift/Flashback/InfoParadox(2) > NumericDrift/LongTermRep(1)
├── 상위 티어가 같은 대상(NPC명 등)을 가리키면 하위 티어 억제
└── explicit/broad 키워드 매칭 기반

Director MC 주입  [L1563-1619]
├── _advisory_summary → dict (truth_gate, npc_drift, ... 플래그)
├── _formatted_advisory_parts → 태그 재포맷팅
├── _director_mc_parts = advisory_parts + 기존 mc_parts
└── _last_advisory_summary / _last_advisory_details 인스턴스 저장
```

---

## 4. 3-Pass 실행 계획

### PASS 1: 전수 수집 (HIGH/MED/LOW 모든 후보)
- 각 타겟별 잠재 이슈 전수 추출
- 코드 라인 + 스니펫 근거 확보

### PASS 2: 교차 검증
- 런타임 도달 가능성 확인 (dead code 아닌지)
- 기존 262+ finding과 교차 비교 (T3-004, T2-038 등 기존 advisory 관련 발견 확인)
- GIL 보호 범위 vs 실제 mutation 범위 재검토

### PASS 3: 최종 확정
- 위양성 제거
- P0-P3 최종 등급 배정
- 권장 후속 조치 및 공수 추정

---

## 5. 기존 관련 Findings 교차 참조

| 기존 ID | 내용 | 본 감사 관계 |
|----------|------|-------------|
| T3-004 | Advisory Chain 병렬 실행 직접 테스트 부재 | T2 (timeout/예외 테스트 갭 관련) |
| T2-038 | ThreadPoolExecutor 타임아웃 후 메모리 점유 | T2 (timeout 캐스케이드 관련) |
| OPUS-TF-T1 (L273) | 8 advisory 병렬 시 동일 값 중복 계산 | T1 (공유 상태 관련) |
| D-T3 | advisory timeout, 부분 실패, future 수거 순서 미검증 | T2 (예외 삼킴 관련) |

---

## 6. 산출물

| # | 파일 | 내용 |
|---|------|------|
| 1 | `XC-ADV-detail-full-survey-audit-order.md` | 본 문서 (감사 계획) |
| 2 | `XC-ADV-T1-parallel-shared-state-mutation-findings.md` | T1 상세 findings |
| 3 | `XC-ADV-T2-timeout-cascade-exception-swallow-findings.md` | T2 상세 findings |
| 4 | `XC-ADV-T3-advisory-conflict-suppression-findings.md` | T3 상세 findings |
| 5 | `XC-ADV-T4-advisory-director-mc-injection-findings.md` | T4 상세 findings |
| 6 | `XC-ADV-consolidated-findings.md` | 전체 통합 findings |
| 7 | `XC-ADV-consolidated-findings-3pass-reaudit.md` | 3-Pass 최종 감사 결과 |
