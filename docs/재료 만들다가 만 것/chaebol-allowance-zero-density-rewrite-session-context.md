# chaebol_allowance_zero Density Rewrite — 세션 컨텍스트 메모

Date: 2026-03-27
work_id: `chaebol_allowance_zero`
family: `blockguide`
session_role: order-OPUS (감리/조율)

---

## 1. 세션 전체 흐름

```
density-recovery rewrite plan (완료)
  → Wave 1 order 작성 (완료)
    → Wave 1 executor 실행 → 8/8 PASS (완료)
      → Wave 2 order 작성 (완료)
        → Wave 2 executor 실행 (미착수)
          → Wave 3 order (미작성)
```

## 2. 완료된 산출물

### 2.1 Density-Recovery Rewrite Plan

| File | Status |
|------|--------|
| `docs/2026-03-27/chaebol-allowance-zero-density-rewrite-plan.md` | **완료** |

핵심 판정:
- verdict: **mixed** (구조 PASS, 밀도 FAIL)
- path truth: `_quarantine` pair가 유일한 live authority
- Block 1-6: benchmark band (보존)
- Block 7-70: template-heavy (rewrite 대상)
- 3 wave로 분할: Wave 1(B7-15), Wave 2(B16-35), Wave 3(B36-70)

### 2.2 Wave 1 (Block 7-15) — 완료

오더 3건:
| File | Role |
|------|------|
| `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave1-order.md` | 메인 오더 |
| `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-opus-context-memo.md` | 컨텍스트 메모 |
| `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave1-order-opus-brief.md` | executor brief |

실행 결과:
- **8/8 Quality Gate PASS**
- kill rules 7개 금지 패턴 전량 삭제
- 9블록 각각 독립 operational 전술 확인 (분실률 역대조 / 유령인력 증빙 / 법률 리프레이밍 / 법인 분리 / 원가 입찰 / 미끼 정보 유출 / 폐기율 실증 / CCTV-POS 대조 / 유휴공간 재패키징)
- villain intelligence evolution 확인: 노현주(B1→B9), 서도윤(B3→B10→B12), 윤석진(B11→B15)
- Block 13 opponent fix: 김태석↔나영수 스왑
- "재이의 정보 출처를 의심한다" → 블록별 구체적 행동 escalation으로 교체
- historical event 2건: B8 최저임금, B10 법인설립 원스톱

### 2.3 Wave 2 (Block 16-35) — 오더 작성 완료, 실행 미착수

오더 3건:
| File | Role |
|------|------|
| `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave2-order.md` | 메인 오더 |
| `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-opus-context-memo.md` | 컨텍스트 메모 |
| `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-order-opus-brief.md` | executor brief |

Wave 2 핵심 차이점 (vs Wave 1):
- 20블록 (Wave 1의 2.2배)
- kill rules 18개 (전 필드 템플릿 — context/villain/solution/reward/stakes/power_shift/foreshadow/callback 전부)
- quality gates 9개 (opponent 다양성 게이트 추가)
- opponent 재편: 윤석진 ≤5블록 상한, 신규 적대자 ≥6명, 공장 도메인 신규 ≥3명
- historical event ≥5건
- 도메인 전환 2회 (호텔→공장 ~B21, 공장→병원 ~B31)
- 병렬 구조: `A(B16-25) || B(B26-35)` → `C(quality gate)`

executor 프롬프트:
```text
너는 이번 런의 executor-OPUS다. `docs/2026-03-27/opus-chaebol-allowance-zero-rewrite-wave2-order.md`와 `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-opus-context-memo.md`, `docs/2026-03-27/chaebol-allowance-zero-rewrite-wave2-order-opus-brief.md`를 UTF-8로 읽고, `chaebol_allowance_zero` TR의 Block 16-35를 density rewrite하라. `A(B16-25) || B(B26-35)` 병렬 후 `C(quality gate)` 순차. 최종 TR JSON merge는 너만 수행. 수정 대상은 TR JSON 1건뿐이다.
```

## 3. 미착수 작업

### 3.1 Wave 2 실행

위 프롬프트로 새 세션에서 executor-OPUS 실행.

### 3.2 Wave 3 (Block 36-70) — 오더 미작성

Wave 2 완료 후 작성해야 할 사항:
- 35블록 (가장 큰 wave)
- 도메인: 병원→정산→전국→가문
- Block 36-70의 실제 template 패턴을 새로 샘플링해서 kill rules 추출 필요
- 자본 규모 91억→1,318억 — exponential growth 구간에서 전술 혁신 요구
- 이 구간의 villain archetype이 가장 단조로움 (이름만 바뀐 동일 유형)
- Wave 3는 scope가 크므로 2-tranche 분할 검토 필요할 수 있음

### 3.3 전체 완료 후

- 70블록 전체 density rewrite 완료 확인
- FinanceHUD / seed-state 정리 (density rewrite plan §7에서 deferred 처리)
- stale root path 정리 (source_manifest.json → _quarantine path 정정)
- promotion 검토 가능 여부 판정

## 4. Canonical Pair 현황

| Role | Path | Status |
|------|------|--------|
| TR | `treatments/_quarantine/chaebol_allowance_zero_tr_block_070_draft.json` | Block 7-15 rewritten, B16-70 원본 |
| BI | `bible/_quarantine/0_bi_chaebol_allowance_zero.json` | 미수정 (read-only) |

Duplicate BI (reference-only, 수정 대상 아님):
- `02_bi_chaebol_allowance_zero.json` (435KB)
- `02_chaebol_allowance_zero_bi.json` (399KB)
- `chaebol_allowance_zero_bi.json` (599KB)

Stale root paths (존재하지 않음, 정리 필요):
- `treatments/02_chaebol_allowance_zero_tr_block_070_draft.json`
- `treatments/chaebol_allowance_zero_phase0_design.json`
- `bible/02_bi_chaebol_allowance_zero.json`
- `bible/chaebol_allowance_zero_bi.json`

## 5. 역할 체계

```
order-OPUS (이 세션, 감리/조율)
  └─ executor-OPUS (별도 세션, 실행)
       ├─ Sub-OPUS-A (병렬 읽기/쓰기)
       ├─ Sub-OPUS-B (병렬 읽기/쓰기)
       └─ Sub-OPUS-C (quality gate 검증)
```

- order-OPUS: 오더 작성, kill rules 추출, quality gate 설계, 감리
- executor-OPUS: 오더를 받아 sub 디스패치 + merge + handoff
- 같은 work_id 안에서 동시 편집자 1명 제한

## 6. Fixed Creative Anchors (전 wave 공통)

절대 훼손 불가:
1. support-system cashflow warfare (장례→호텔→공장→병원→정산→전국→가문)
2. moneyline > inheritance
3. no family bailout
4. B2B 일상경비 조임점이 전쟁터
5. business_growth_profile + office_power_profile
6. concrete operational detail (skeleton plot 불가)

drift 금지:
- 주식/M&A spectacle
- 모든 사업을 "운영사업" 하나로 뭉뚱그리기
- cashflow warfare → 추상적 권력 게임

## 7. 이어가기 체크리스트

새 세션에서 이 작업을 이어갈 때:

- [ ] 이 문서를 먼저 읽는다
- [ ] Wave 2 실행 여부 확인 (TR JSON의 Block 16 content.solution이 "기억를 떠올리며"로 시작하면 미실행)
- [ ] Wave 2 미실행이면 §2.3의 executor 프롬프트로 실행
- [ ] Wave 2 완료 시 handoff 확인 (9/9 quality gate)
- [ ] Wave 3 오더 작성: Block 36-70 샘플링 → kill rules 추출 → 오더 3건
- [ ] Wave 3 실행
- [ ] 전체 완료 후: HUD/seed-state 정리, stale path 정리, promotion 판정

## 8. 감리 시 주의점

- Wave 1 결과가 이미 TR에 반영됨 — Block 7-15는 rewritten 상태
- Wave 2 오더의 kill rules 18개는 Block 16, 20, 30에서 직접 추출한 실제 문장
- Wave 2는 Wave 1보다 template 오염이 심각 (전 필드)
- Wave 3는 아직 샘플링하지 않음 — 오더 작성 전 반드시 Block 36-70 실제 상태 확인 필요
- 자본 수치(capital_before/after)는 어떤 wave에서도 변경 금지
