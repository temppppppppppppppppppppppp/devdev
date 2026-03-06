# T6 발령문 - 위험키 승인 정책 구현

## 미션
- 위험키(`44/77/88/99`) 승인 게이트를 코드 경로에 고정.

## 시작 조건
- 모드: `CODE_OPEN`
- 선행 의존: `T1`, `T2` 동결 완료
- 공통: 작업 착수 전 `docs/2026-03-06/handoff/T0-broadcast.md` 최신 `seq` 확인 후 handoff에 `last_seen_broadcast_seq` 기록

## 작업
1. `approval_id` 미제공 시 차단
2. 승인 만료 시 차단
3. 동일 승인자(2인 미충족) 차단
4. 승인 검증 성공 시에만 실행 허용
5. 감사 로그(`approval_id` 기준) 저장

## 기대 오류
- `RISK_APPROVAL_REQUIRED`
- `RISK_APPROVAL_EXPIRED`
- `RISK_APPROVAL_DUAL_CONTROL_REQUIRED`

## 산출물
- 위험키 검증 코드
- 감사로그 기록 로직

## 완료 기준
1. 승인 4케이스(없음/만료/2인미충족/정상) 분기 통과
2. 감사로그 추적 가능
3. 계약 오류코드와 일치

## handoff
- `docs/2026-03-06/handoff/T6-handoff.md`


