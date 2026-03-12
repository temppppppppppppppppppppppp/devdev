# Workspace Instructions

## Blockguide First

이 워크스페이스에서 아래 작업이 들어오면 먼저 `docs/blockguide/SSOT_blockguide-integrated-order.md`를 UTF-8로 읽는다.

- 작품 기획안 작성 또는 수정
- `work_id` 기준 Treatment/BI 생성
- `Phase 0`, `TR draft`, `BI`, 감리, 정합성, 밀도 점검
- `다음 스텝`, `계속`, `승인` 기반 자동 진행

그다음 아래 문서를 UTF-8로 읽는다.

1. `docs/blockguide/treatment-planning-harness.md`
2. `docs/blockguide/treatment-production-harness-v2.md`
3. `docs/blockguide/bi-production-harness-v1.md`

대상 작품이 `alt_history`이거나 역사 재료 DB 조회가 필요하면 추가로 아래 문서를 읽는다.

4. `docs/blockguide/alt_history_db_harness.md`

## Stage Detection

현재 단계는 메모리가 아니라 파일 존재로 판정한다.

- `phase0_design` 없음: planning 단계
- `phase0_design` 있음, `tr_block_070_draft` 없음: production 단계
- `tr_block_070_draft` 있음, `0_bi_{work_id}.json` 없음: BI 단계
- `BI`가 있어도 감리 FAIL이면 완료가 아니다

## Execution Rules

- 한 번에 1단위만 진행한다.
- 애매하면 더 작은 단위로 쪼갠다.
- `Phase 0` 없이 TR 생성 금지
- `TR draft` 없이 BI 생성 금지
- 감리 PASS 전 완료 선언 금지
- UTF-8 only. `???`, `�` 탐지 시 즉시 중단 후 원인 보고
