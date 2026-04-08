# line_stop_deputy — Integration Handoff Closeout

Date: 2026-04-06
Status: **CLOSED / RETIRED** (updated 2026-04-08)
Authority: this document is the historical integration decision record for `line_stop_deputy` + `shockline_salaryman`

## 1. Decision Summary

| Work | Disposition | Detail |
|---|---|---|
| `line_stop_deputy` | **RETIRE** | active candidate lane에서 제거. canon / phase0 / downstream route 종료 |
| `shockline_salaryman` | **RETIRED** | 기존 retire 유지. active candidate lane 복귀 없음 |

현재는 두 작품 모두 active promotion 대상이 아니다. 이 문서는 historical reasoning record로만 보존한다.

## 2. Historical Keep Logic

### core engine
`사고를 막는 사람`이 아니라 `멈출 권리를 가진 사람`으로 올라가는 안전 권력 엔진.
라인을 세우는 권한이 곧 돈줄과 승계 명분이 되는 구조다.

### first block reward
1. 임시 라인 중지권
2. 재가동 공동 서명권
3. 해외 고객사 실사 배석권
4. 보험사 갱신 협상 테이블 진입권
5. 첫 공개 신호 기반 합법 환전 수익 (secondary — 권한 4개가 먼저 잡힌 뒤에만 발동)

### repeatable loop
전조선 감지 → 라인 중지 또는 조건부 가동 → 증거 확보와 공개 증명 → 중지권/승인권/감사권 중 하나 회수 → 공개 신호 전환 후 합법 환전 → 다음 공장과 다음 고객사 전장 진입

### controllable growth resource (primary)
`라인 중지권`, `재가동 서명권`, `감사 로그 접근권`, `보험 갱신 협상력`

### controllable growth resource (secondary)
`공개 신호 기반 합법 외부 환전` — primary 권한이 만든 공개 정보로만 작동

## 3. Absorb — shockline_salaryman에서 가져온 것

| # | 흡수 요소 | 통합본 반영 위치 |
|---|---|---|
| 1 | "회사에 남아 있어야 먼저 읽는다" 내러티브 | protagonist_position, Phase0 handoff `already_locked` |
| 2 | 공개 신호 → 합법 외부 환전 보조 루프 | long_term_goal, repeatable_loop, controllable_growth_resource (secondary) |

이 두 요소는 historical 통합본에 반영되었고, 현재는 `01_line_stop_deputy_RETIRE.md` 경로 아래 retirement 상태로만 남아 있다. 추가 흡수 없음.

## 4. Retire — shockline_salaryman에서 버린 것

- 투자가 core engine인 구조
- `investment_market_profile` primary profile
- 리스크관리팀 소속 설정 (안전팀 대리 유지)
- `시장 포지션 시드 자본`이 주 성장자원인 구조
- `오준혁` 캐릭터 설정 (통합본 주인공은 `서정우`)

retire 기록:
- `material_ssot/20_pitch/intake/fresh_20260406_batch01/04_shockline_salaryman_RETIRE.md`

## 5. Do-Not-Cross Rules

downstream(canon / phase0 / work_guard / TR)은 아래를 재판단하지 않는다:

### 5-A. Insider-Trading Hardline
- 비공개 전조선 정보로 자기 회사 주식이나 파생 포지션을 건드리지 않는다
- 공개 전환 전 외부 포지션 진입 금지
- 이 룰은 contamination guard이자 법적 하드라인이다. 예외 없음

### 5-B. Reward Ordering Rule
- 첫 보상은 **권한**이다: 라인 중지권 / 재가동 서명권 / 감사 배석권
- 환전 수익은 권한이 **먼저 잡힌 뒤에만** 따라온다
- 어떤 블록에서도 `환전 먼저, 권한 나중` 순서는 금지

### 5-C. Engine Hierarchy
- core engine = `멈출 권리 독점` (안전 권력 엔진)
- secondary payoff = `공개 신호 환전` (보조 루프)
- 투자 루프가 서사 주도권을 잡으면 contamination이다
- TR/BI 설계 시 블록당 투자 환전 비중은 서브플롯 수준으로 제한

## 6. Downstream Status

- `line_stop_deputy` canon route: closed
- `line_stop_deputy` Stage0 / Phase0 route: closed
- `shockline_salaryman` route: already retired and still closed
- downstream는 이 두 작품을 active candidate로 다시 읽지 않는다 unless a future explicit restart order creates a new work from scratch

## 7. File References

| Role | Path |
|---|---|
| retire 기록 | `material_ssot/20_pitch/intake/fresh_20260406_batch01/01_line_stop_deputy_RETIRE.md` |
| retire 기록 | `material_ssot/20_pitch/intake/fresh_20260406_batch01/04_shockline_salaryman_RETIRE.md` |
| shockline 원본 (동결) | `material_ssot/20_pitch/intake/fresh_20260406_batch01/04_shockline_salaryman.md` |
| pitch philosophy | `material_ssot/20_pitch/pitch-philosophy.md` |
| 이 문서 | `material_ssot/20_pitch/synthesis/line_stop_deputy_integration_handoff.md` |
