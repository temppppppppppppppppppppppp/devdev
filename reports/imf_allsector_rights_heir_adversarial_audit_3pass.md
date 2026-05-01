# imf_allsector_rights_heir 적대적 감리 3회

Date: 2026-05-01

## Scope

- TR: `treatments/imf_allsector_rights_heir_tr_block_070_draft.json`
- BI: `bible/0_bi_imf_allsector_rights_heir.json`
- 기준: 빠른 웹소설 페이싱, 1 block = 2~6화 밀도, 매 block 주 사건 + 별도 부 사건, 자기중심적 주인공, 대리만족 보상 구조

## 1차 감리: 페이싱 / 부 사건

Verdict: PASS after minor prose cleanup

- 70개 block 모두 `side_event.primary_event`, `side_event.secondary_event`, `side_event.secondary_event_next_gate` 존재.
- 70개 block 모두 `block_cider.receipt_line` 존재.
- `pain_only_exit` block 없음.
- 패배 block도 같은 block 안에서 회수권/option/자료/조건을 지급함.
- 수정: handoff 보정 중 생긴 `N번째 권리 파일` 표현 26건을 `해당 권리 파일`로 정리.

## 2차 감리: 자기중심성 / 이득과 효율

Verdict: PASS after wording cleanup

- 모든 block의 해결/보상 문장에 권리, 조건, option, 운영권, 자료, 정산, 승인 등 실익 단위가 존재.
- 대가 없는 선의, 감정형 보복, 체면형 손실 감수로 닫히는 block 없음.
- 현장 인물 보호는 숙련자산, 인증, 계약권, 회수율 보존으로 환전됨.
- 수정: Block 69의 `착해서 지키는 게 아니라고`를 `호의를 베풀려고 지키는 게 아니라고`로 변경해 금지 뉘앙스 토큰 제거.

## 3차 감리: 대리만족 보상 구조

Verdict: PASS

- 모든 block이 보상 영수증을 명시함.
- capital ladder는 `0 -> 70`까지 연속.
- 보상 단위는 현금 칭찬이 아니라 `보류권`, `실사권`, `우선권`, `자료 열람권`, `운영권`, `재매입 option`, `TF owner`, `매각 판단권`으로 지급됨.
- 패배 block의 보상 구조:
  - 8: 해지 통지 패배 후 면책 조항과 회선 보류 proof
  - 17: 위약금 패배 후 경쟁사 회선권 약점 자료
  - 26: 보증금 납입 실패 후 대리점망 운영권
  - 35: NPL 전체 매입 포기 후 핵심 담보권
  - 46: 납품 취소 후 인증 유지 기간과 대체 수요 접근권
  - 56: 소방 점검 패배 후 합법 전환 체크리스트와 축소 테스트권
  - 66: 일부 cashout 패배 후 매각 조건표와 재매입 option

## Final Harness

- Block continuity: CLEAN
- Source TR density gate: PASS
- hard gate failures: none
- meta leak: 0
- unresolved foreshadow: 0
- NPC continuity mismatch: 0
- BI 5-pass audit: PASS
- BI/TR consumability: PASS

