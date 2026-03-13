# main_a Facade Shim Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MFS-T1` ~ `MFS-T5` 통합본
> 기준 오더: `main_a-facade-shim-detail-full-survey-audit-order.md`
> 확정 결과: `총 12건 (P0 0 / P1 4 / P2 5 / P3 3)`

이 문서는 2026-03-13 기준 facade shim / audit callback 트랙의 T1~T5 PASS3 결과를 재구성한 통합 SSOT다. cross-terminal dedupe로 삭제한 finding은 없었다. source 문서 사이의 severity/duplicate enum은 이미 오더 형식과 호환되어 추가 정규화는 하지 않았다.

---

## 터미널별 상태

| 터미널 | 소스 상태 | 문서 | PASS 요약 | 최종 건수 |
|--------|-----------|------|-----------|-----------|
| T1 | `PASS3 completed` | `MFS-T1-stage2-normalization-flow-findings.md` | `PASS1 4 -> PASS2 제거 2 -> 최종 2` | 2 |
| T2 | `PASS3 complete` | `MFS-T2-state-service-validation-findings.md` | `PASS1 5 -> PASS2 제거 2 -> 최종 3` | 3 |
| T3 | `executed / PASS3 completed` | `MFS-T3-stage3-stage4-audit-callback-findings.md` | `PASS1 6 -> PASS2 제거 3 -> 최종 3` | 3 |
| T4 | `executed / PASS3 complete` | `MFS-T4-ui-stage01-presentation-findings.md` | `PASS1 4 -> PASS2 제거 2 -> 최종 2` | 2 |
| T5 | `PASS 3 complete / confirmed` | `MFS-T5-protocol-tests-regression-findings.md` | `PASS1 5 -> PASS2 제거 3 -> 최종 2` | 2 |

## Severity Summary

| Severity | T1 | T2 | T3 | T4 | T5 | 확정 |
|----------|----|----|----|----|----|------|
| P0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P1 | 1 | 1 | 1 | 1 | 0 | 4 |
| P2 | 1 | 1 | 1 | 0 | 2 | 5 |
| P3 | 0 | 1 | 1 | 1 | 0 | 3 |
| 합계 | 2 | 3 | 3 | 2 | 2 | 12 |

## 상위 위험군

| 위험군 | 포함 finding | 의미 |
|--------|--------------|------|
| Validation / audit facade miswiring | `MFS-T2-001`, `MFS-T2-002`, `MFS-T3-02`, `MFS-T5-001` | `main_a.py` facade가 export하는 validation/audit callback이 실제 Stage2/3/4 context와 protocol/test 표면에 완전히 잠기지 않아 bound-method drift가 green test 뒤에 숨는다 |
| False-pass / degraded semantics drift | `MFS-T1-002`, `MFS-T3-01`, `MFS-T5-002` | flow analyzer runtime exception, Stage3 completion summary, validation soft-failure relay가 모두 “실패를 성공 또는 관측성 약화로 흡수”하는 방향으로 기울어 있다 |
| Dormant or bypassed facade surface | `MFS-T2-003`, `MFS-T4-001` | facade로 남은 helper 일부는 runtime consumer가 없거나, live consumer graph가 facade를 우회해 실제 운영 의미와 API 표면이 분리된다 |
| Operator-facing observability drift | `MFS-T3-03`, `MFS-T4-002` | unresolved pin 로그 mojibake와 Stage01 `10권` 고정 UI 라벨이 operator-facing 관측성과 completion semantics를 오염시킨다 |

## 취합 메모

- cross-terminal dedupe로 삭제한 항목은 없었다.
- `MFS-T2-002`와 `MFS-T5-001`은 둘 다 facade regression blind spot을 다루지만, 전자는 validation shim 전체의 bound-method 경계이고 후자는 tagged audit summary contract라는 별도 callback family라 분리 유지했다.
- `MFS-T2-003`과 `MFS-T4-001`도 모두 dormant/bypass theme이지만, 전자는 state-service 쪽 dormant shim set이고 후자는 Stage4 live validation이 NPC facade를 비워서 PASS 처리하는 active bypass surface라 별도 유지했다.
- `MFS-T1-002`와 `MFS-T3-01`은 모두 false-success 테마지만, 하나는 Stage2 flow validator의 runtime exception absorb이고 다른 하나는 Stage3 completion summary tagging 문제다.

## 통합 Ledger

| ID | 터미널 | Sev | 주제 | duplicate status |
|----|--------|-----|------|------------------|
| `MFS-T1-001` | T1 | `P2` | facade duplicate threshold 기본값이 실제 Stage 2 duplicate guard 소비 경로와 다르다 | `none` |
| `MFS-T1-002` | T1 | `P1` | flow analyzer runtime exception이 legacy fallback이 아니라 `PASS`로 흡수된다 | `none` |
| `MFS-T2-001` | T2 | `P1` | `_validate_arc_data_fields()` repair hook가 실제 Stage2 context에 바인딩되지 않아 production repair path가 죽어 있다 | `related-but-new-facade-surface` |
| `MFS-T2-002` | T2 | `P2` | live validation shim 바인딩이 MagicMock 분할 테스트에만 잠겨 있어 facade bound-method drift를 놓칠 수 있다 | `related-but-new-facade-surface` |
| `MFS-T2-003` | T2 | `P3` | 여러 state-service facade shim이 현재 consumer graph가 없는 dormant surface로 남아 있다 | `none` |
| `MFS-T3-01` | T3 | `P1` | `stage3_complete` summary가 Stage3 실패/중단 경로도 성공처럼 덮는다 | `related-but-new-facade-surface` |
| `MFS-T3-02` | T3 | `P2` | Stage4 completion callback source가 `ctx`와 `app`로 갈라져 facade contract가 분열돼 있다 | `related-but-new-facade-surface` |
| `MFS-T3-03` | T3 | `P3` | unresolved continuity pin 로그 문자열이 이미 mojibake 상태다 | `none` |
| `MFS-T4-001` | T4 | `P1` | Stage4 live validation path가 `main_a.py` NPC facade를 우회하고 `npc_profiles={}`로 NPC attitude 검사를 사실상 비활성화한다 | `related-but-new-facade-surface` |
| `MFS-T4-002` | T4 | `P3` | `_show_volume_table()` 경유 UI가 실제 권 수와 무관하게 `10권` 고정 타이틀을 출력한다 | `none` |
| `MFS-T5-001` | T5 | `P2` | tagged audit summary facade contract를 protocol/context 테스트가 잠그지 못한다 | `related-but-new-facade-surface` |
| `MFS-T5-002` | T5 | `P2` | `ValidationOrchestrator` soft-failure regression net이 helper 직접 호출에서 멈추고 실제 sync/parallel exception path는 미검증이다 | `none` |

## 결론

- 이번 트랙의 통합 baseline은 `12 confirmed findings`다.
- 우선 remediation 순서는 `validation/audit facade wiring 정렬 -> false-pass semantics 차단 -> dormant/bypassed facade 정리 -> operator-facing observability 정리`가 적절하다.
- 최종 SSOT 승격 여부는 `main_a-facade-shim-detail-consolidated-findings-3pass-reaudit.md` 기준으로 판단한다.
