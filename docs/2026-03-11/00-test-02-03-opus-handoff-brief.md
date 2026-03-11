# OPUS Handoff Brief: 00_test_02 / 00_test_03 Control-Treatment Cross-Check

아래 오더 문서를 그대로 실행해 주세요.

- 오더 문서: [00-test-02-03-control-treatment-crosscheck-order.md](C:/Users/User/Desktop/글도비/docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-order.md)

요청 범위:

1. `00_test_02`와 `00_test_03`를 오더 문서 기준으로 read-only 감리
2. Codex와 동일하게 메인 바디 표 구조 유지
3. taxonomy는 아래 4개만 사용
   - `confirmed control parity`
   - `acceptable drift`
   - `failure signal`
   - `hypothesis pending`
4. `00_test_03`는 성공 로그만으로 `채택 가능` 판정 금지
5. reconciliation 전제:
   - `편측 발견`은 가능하면 같은 턴에 source-level 추가 확인을 끝까지 수행
   - 확인 가능한 항목은 `합의 사실` 또는 `해석 차이`로 이동
   - 끝까지 닫히지 않는 항목만 `편측 발견`으로 남김

필수 산출물:

- `docs/2026-03-11/00-test-02-03-control-treatment-crosscheck-report-OPUS.md`

후속 reconciliation 산출물:

- `docs/2026-03-11/00-test-02-03-control-treatment-reconciliation-opus.md`

판정 시 유의사항:

- `00_test_02`는 control 재현/재측정 run
- `00_test_03`는 all-lite cost/perf experiment
- `00_test_03`의 `채택 가능 / 95%`는 manual reading 없이는 금지
- 반대로 반복 REJECT, Stage 4 붕괴, ep 미완료, runtime/cost 악화가 충분하면 logs만으로 `채택 불가` 판정 가능
