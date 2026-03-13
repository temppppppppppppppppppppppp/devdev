# OPUS TF 5-Terminal Consolidated Findings 3-Pass Re-Audit

- 작성일: 2026-03-13
- 대상 문서: [OPUS-TF-5terminal-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings.md)
- 조사 모드: static / read-only / source-report cross-check / targeted code verification
- 최종 상태: `pass-with-ledger-correction`
- 최종 확신도: `95%`

## Executive Summary

원문 [OPUS-TF-5terminal-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-5terminal-consolidated-findings.md)은 고위험 실행 우선순위를 잡는 용도로는 충분히 쓸 수 있다. 특히 `T2-001`, `T3-029`, `T4-P1-01~04`, `T1-01`, `T5-WS-016`로 이어지는 상위 위험군은 소스 보고서와 실코드 대조에서 모두 재확인됐다.

다만 무조건 PASS로 둘 수는 없다. 이번 재감리에서 아래 3개는 원문 그대로 승격하지 않았다.

- 범위 헤더의 테스트 파일 수가 현재 워크스페이스와 불일치한다. 원문은 `274 .py`라고 적었지만 실제 카운트는 `276 .py`다.
- `중복제거 -3` / `총 262건`은 문서 서술만으로는 재구성되지 않는다.
- `T3-040`과 `T4-P2-CF01`은 같은 표면의 중복이 아니라 `CLAUDE.md`와 `director.yaml`에 걸친 별도 문서 드리프트다.

따라서 이번 재감리의 결론은 다음이다.

- **실행 우선순위용 고위험군은 신뢰 가능**
- **정확한 grand total 262는 현행 문서만으로는 SSOT 승격 불가**
- 이후 실행 SSOT는 원문 단독이 아니라 **이 재감리 문서와 함께** 참조해야 한다

## 1. Pass 1 - 소스 리포트 교차 대조

### P1-1. 터미널별 최종 수치는 소스 리포트와 일치한다

직접 근거:

- [OPUS-TF-T1-infrastructure-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T1-infrastructure-findings.md): 최종 `31건`
- [OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md): 최종 `47건`
- [T3-stage3-4-pipeline-audit-report.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md): 최종 `40건`
- [T4-quality-advisory-audit-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T4-quality-advisory-audit-findings.md): 최종 `56건`
- [OPUS-TF-T5-domain-auxiliary-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/OPUS-TF-T5-domain-auxiliary-findings.md): 최종 `91건`

판정:

- `confirmed`

해석:

- 터미널별 최종 수치 `31 + 47 + 40 + 56 + 91 = 265`는 재구성 가능하다.
- 즉 원문의 per-terminal 테이블은 소스 리포트 최종본을 잘 끌어왔다.

### P1-2. P0/P1 상위 위험군 구성은 원문과 소스가 일치한다

직접 근거:

- P0: `T2-001`
- P1: `T1-01`, `T2-002`, `T5-WS-016`, `T3-003`, `T3-004`, `T3-029`, `T4-P1-01~07`

판정:

- `confirmed`

해석:

- 원문 P0/P1 섹션은 소스 리포트의 상위 위험군을 누락 없이 담고 있다.
- 실행 오더의 입력층으로 삼기 적합하다.

### P1-3. 원문의 범위 문구는 현재 워크스페이스 기준으로는 부분 수정이 필요하다

직접 근거:

- 실제 모듈 수: `239`
- 실제 테스트 파일 수: `276`
- 실제 라인 수: 프로덕션 `134,121`, 테스트 `68,200`

판정:

- `confirmed`

해석:

- 원문의 `프로덕션 134K lines (239 .py)`는 현재와 실질적으로 맞다.
- 하지만 `테스트 68K lines (274 .py)`는 현재 기준 `276 .py`와 불일치한다.
- 같은 날짜 문서라도 “전량 조사” 문맥에서는 범위 수치가 그대로 SSOT가 되므로, 이 부분은 보정이 필요하다.

## 2. Pass 2 - 실코드 표적 검증

### P2-1. `T2-001` Stage 2 진입 차단은 실코드에서 직접 확인된다

직접 근거:

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py) `_s0_save_results()`는 Bible 저장과 Treatment 파일 저장만 수행하고 `plot_roadmap` 주입을 하지 않는다.
- [story_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py) `generate_bible()` 생성 결과에는 `plot_roadmap` 키가 없다.

판정:

- `confirmed`

해석:

- 원문의 `T2-001`은 보고서 수준 추정이 아니라 실코드로 재현 가능한 진탐이다.

### P2-2. `T3-029` Director PASS 사후 무효화는 실코드에서 직접 확인된다

직접 근거:

- [stage3_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage3_orchestrator.py) `_handle_success()`는 `apply_continuity_pins` 결과가 `unresolved`면 즉시 `fail_count + 1`로 반환한다.
- 이 반환은 같은 함수의 Blueprint 저장 경로보다 앞에서 발생한다.

판정:

- `confirmed`

해석:

- 원문이 지적한 “Director PASS를 Python continuity pin이 뒤집는다”는 클러스터의 핵심 축은 실제 코드에 남아 있다.

### P2-3. `T4-P1-01` / `T4-P1-02` / `T4-P1-03` / `T4-P1-04`는 모두 실코드에서 직접 확인된다

직접 근거:

- [validation_orchestrator.py](C:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py) L468-482 상당: `unjustifiable_violations` 즉시 `REJECT`
- [validation_orchestrator.py](C:/Users/User/Desktop/글도비/modules/validation/validation_orchestrator.py) L656-667 상당: retrospective `CRITICAL` 즉시 `REJECT`
- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py) L471-478 상당: Python-only `PASS`
- [director_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/director_ensemble.py) L1246-1256 상당: adaptive 조정으로 `PASS/PASS_WITH_FIX -> REJECT`

판정:

- `confirmed`

해석:

- 원문이 가장 크게 잡은 “Director 주권 클러스터”는 신뢰할 수 있다.
- 이 축은 실행 SSOT의 최상위 묶음으로 유지해야 한다.

### P2-4. `T1-01`과 `T5-WS-016`도 실코드에서 직접 확인된다

직접 근거:

- [RESET.py](C:/Users/User/Desktop/글도비/RESET.py) L86 상당: `MartialHUD` 하드코딩 접근
- [fact_ledger.py](C:/Users/User/Desktop/글도비/modules/core/fact_ledger.py) L206-255 상당: `npc_injuries`, `npc_movements`, `npc_personality_changes`, `npc_npc_relationships` 처리에 dead-NPC guard 부재

판정:

- `confirmed`

해석:

- 원문 P1의 비-Director 축도 진탐이다.
- 따라서 실행 오더는 Director 주권 축만이 아니라 HUD/FactLedger 데이터 무결성 축을 함께 잡아야 한다.

## 3. Pass 3 - ledger 정리와 오탐 제거

### R1. `총 262건 확정`은 현행 문서만으로는 재현되지 않는다

직접 근거:

- 소스 리포트 합계는 `265`
- 원문이 명시적으로 hard duplicate로 입증한 것은 `T1-04 ↔ T5-API-04` 1건이다
- 나머지 `-2`에 해당하는 삭제 ID는 문서만으로는 재구성되지 않는다

상태:

- `rejected-as-ssot-count`

해석:

- `262`가 틀렸다고 단정할 근거는 아직 부족하다.
- 하지만 **입증되지도 않았다**. 현재 문서만 기준으로는 `262`를 SSOT total로 쓰면 안 된다.

### R2. `T3-040`과 `T4-P2-CF01`은 같은 이슈라서 하나로 합쳐도 된다

직접 근거:

- [T3-stage3-4-pipeline-audit-report.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T3-stage3-4-pipeline-audit-report.md)의 `T3-040`: `CLAUDE.md` Self-Critique 개수 드리프트
- [T4-quality-advisory-audit-findings.md](C:/Users/User/Desktop/글도비/docs/2026-03-13/T4-quality-advisory-audit-findings.md)의 `T4-P2-CF01`: `director.yaml` NC-3 항목 수 드리프트

상태:

- `rejected`

해석:

- 둘 다 “문서/프롬프트 개수 표기 불일치”라는 theme은 같지만, 수정 표면과 런타임 영향 지점이 다르다.
- 따라서 dedupe 대상으로 묶는 것은 과도하다.

### R3. 범위 헤더의 `274 .py`는 그대로 유지해도 된다

직접 근거:

- 현재 워크스페이스 직접 카운트 결과 테스트 파일 수 `276`

상태:

- `rejected`

해석:

- 전량 조사 신뢰도 문서에서는 범위 수치 드리프트도 추후 혼선을 만든다.
- 최소한 재감리 문서에서는 `276 .py`로 보정해 두어야 한다.

## 4. 재감리 후 확정 baseline

이번 재감리 이후 실행 SSOT가 신뢰할 수 있는 baseline은 아래다.

### 확정 가능

- `P0 = 1` (`T2-001`)
- `P1 = 13` (원문 P1 전량)
- hard duplicate로 문서상 입증된 항목 `1건`: `T1-04 ↔ T5-API-04`
- 실코드까지 재확인한 상위 위험군:
  - `T2-001`
  - `T1-01`
  - `T2-002`
  - `T5-WS-016`
  - `T3-029`
  - `T4-P1-01`
  - `T4-P1-02`
  - `T4-P1-03`
  - `T4-P1-04`

### 보류

- `총 262건`이라는 grand total
- `중복제거 -3`의 정확한 삭제 ledger

### 실행용 해석

실행 오더는 disputed grand total이 아니라 아래 **고신뢰 클러스터**를 기준으로 잡는 것이 맞다.

1. Stage 0→2 `plot_roadmap` handoff 차단
2. Director 주권 침식 클러스터
3. HUD / FactLedger 데이터 무결성
4. API contract / 문서 드리프트
5. 교차 단계 회귀 테스트 갭

## 5. retained observation

### O1. 원문은 “우선순위 문서”로는 유효하지만 “정량 ledger 문서”로는 보강이 필요하다

- 우선순위 자체는 맞다.
- 하지만 `265 -> 262`로 내려가는 정량 ledger는 이번 재감리 없이는 그대로 승격하기 어렵다.

### O2. 실행 SSOT는 `정확한 총건수`보다 `확정된 고위험군` 중심으로 짜는 것이 맞다

- 이번 사용자 요청의 목적은 통계 과시가 아니라 **신뢰 가능한 수정 순서 확보**다.
- 따라서 숫자가 흔들리는 구간은 오더의 gate로 쓰지 않는다.

## 6. 확신도 ledger

- 기본 점수: `75`
- 5개 터미널 최종 리포트 상호 대조: `+10`
- P0/P1 상위 위험군 원문-소스 정합 확인: `+5`
- 실코드 표적 검증 4축 완료: `+10`
- 실제 파일 수/라인 수 직접 계수: `+5`
- grand total `262` 미입증: `-5`
- 265건 전체를 line-by-line 재검증하지는 않음: `-5`

최종 확신도: `95%`

## 7. 결론

- 상태: `execution-ready-with-corrected-ledger`
- blocker:
  - 고위험 실행 순서에는 없음
  - 다만 `262건 확정`은 보조 설명으로만 취급
- 다음 단계:
  - 이 재감리 문서를 기준으로 실행 SSOT를 작성한다
  - 실행 SSOT는 `확정된 P0/P1 + 선별 P2`만을 게이트로 사용한다

이번 재감리에서 원문 전체를 폐기할 필요는 없다고 판단했다. 다만 지금부터는 원문 단독이 아니라 **원문 + 이 재감리 문서**를 한 세트로 봐야 한다.
