# main_a Persistence Narrative Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MPN-T1` ~ `MPN-T5` 통합본
> 기준 오더: `main_a-persistence-narrative-detail-full-survey-audit-order.md`
> 확정 결과: `총 16건 (P0 0 / P1 5 / P2 10 / P3 1)`

이 문서는 2026-03-13 기준 shared persistence / narrative helper 트랙의 T1~T5 PASS3 결과를 재구성한 통합 SSOT다. 교차 터미널 중복 제거로 삭제된 finding은 없었다. 일부 source 문서가 heading에서 bracket form ID를 쓰지만 통합 ledger에서는 plain code token으로만 표기했다.

---

## 터미널별 상태

| 터미널 | 소스 상태 | 문서 | PASS 요약 | 최종 건수 |
|--------|-----------|------|-----------|-----------|
| T1 | `3pass executed` | `MPN-T1-commit-preset-recovery-findings.md` | `PASS1 5 -> PASS2 제거 3 -> 최종 2` | 2 |
| T2 | `executed / PASS3 complete` | `MPN-T2-protagonist-episode-mapping-findings.md` | `PASS1 6 -> PASS2 제거 2 -> 최종 4` | 4 |
| T3 | `completed` | `MPN-T3-stage01-stage3-shared-helper-findings.md` | `PASS1 4 -> PASS2 제거 1 -> 최종 3` | 3 |
| T4 | `PASS3 finalized` | `MPN-T4-stage4-summary-cache-findings.md` | `PASS1 4 -> PASS2 제거 1 -> 최종 3` | 3 |
| T5 | `completed` | `MPN-T5-consumer-tests-legacy-contract-findings.md` | `PASS1 6 -> PASS2 제거 2 -> 최종 4` | 4 |

## Severity Summary

| Severity | T1 | T2 | T3 | T4 | T5 | 확정 |
|----------|----|----|----|----|----|------|
| P0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P1 | 0 | 2 | 1 | 1 | 1 | 5 |
| P2 | 2 | 2 | 2 | 2 | 2 | 10 |
| P3 | 0 | 0 | 0 | 0 | 1 | 1 |
| 합계 | 2 | 4 | 3 | 3 | 4 | 16 |

## 상위 위험군

| 위험군 | 포함 finding | 의미 |
|--------|--------------|------|
| Protagonist / episode / arc SSOT split | `MPN-T2-01`, `MPN-T2-02`, `MPN-T2-03`, `MPN-T2-04`, `MPN-T5-001` | protagonist source와 episode→arc 계산 계약이 DB anchor, live bible, nullable callback, 5화 고정 helper 사이에서 갈라져 Stage1/2/3/4 shared semantics가 흔들린다 |
| Shared persistence / commit success semantics drift | `MPN-T1-001`, `MPN-T1-002`, `MPN-T5-002`, `MPN-T5-003` | stale preset 유지, cache persistence false-success, Stage4의 `_safe_commit` 반환값 무시, smoke fixture의 잘못된 bool contract가 합쳐져 persistence helper 의미가 stage/test마다 달라진다 |
| Stage01 hidden coupling / validation blind spot | `MPN-T3-001`, `MPN-T3-002`, `MPN-T3-003`, `MPN-T5-004` | `_validate_volume_boundaries()`가 fail-open과 hidden coupling을 동시에 남기고, 테스트는 핵심 callback 체인을 실제로 실행하지 않아 facade 분리 회귀를 놓칠 수 있다 |
| Narrative summary lifecycle drift | `MPN-T4-001`, `MPN-T4-002`, `MPN-T4-003` | rollback 이후 stale narrative summary 누수, sparse `ep_range` 오표기, series/volume summary 중복 주입이 Stage4 prompt contract를 오염시킨다 |

## 취합 메모

- cross-terminal dedupe로 삭제한 항목은 없었다.
- `MPN-T2-04`와 `MPN-T5-001`은 둘 다 5화 고정 helper를 다루지만, 전자는 shared helper contract 자체의 drift이고 후자는 그 drift를 테스트/consumer가 stale SSOT로 같이 고정하고 있다는 regression surface라 분리 유지했다.
- `MPN-T1-002`와 `MPN-T5-002`도 둘 다 commit helper의 bool semantics를 다루지만, 하나는 cache metadata save path의 false-success 문제이고 다른 하나는 Stage4 cleanup contract 분기 문제라 별개다.
- `MPN-T3-003`과 `MPN-T5-004`는 모두 테스트 blind spot이지만, 전자는 Stage1 boundary gate 실행 공백이고 후자는 Stage3 DI slot coverage의 MagicMock auto-attr 공백이라 분리했다.

## 통합 Ledger

| ID | 터미널 | Sev | 주제 | duplicate status |
|----|--------|-----|------|------------------|
| `MPN-T1-001` | T1 | `P2` | `_restore_preset_registry()` no-data/failure 경로가 stale preset을 유지한다 | `related-but-new-shared-helper-surface` |
| `MPN-T1-002` | T1 | `P2` | cache persistence 경로가 `save_anchor()`와 `_safe_commit()`의 bool 실패 신호를 무시하고 성공처럼 진행한다 | `none` |
| `MPN-T2-01` | T2 | `P1` | `_get_protagonist_name()`가 live `master_bible` 대신 DB anchor만 읽어 stale/default 주인공명을 주입한다 | `related-but-new-shared-helper-surface` |
| `MPN-T2-02` | T2 | `P1` | `_fix_entity_registry_protagonist()`가 `role="extracted"` protagonist를 발견하지 못해 중복 protagonist row를 삽입한다 | `none` |
| `MPN-T2-03` | T2 | `P2` | Stage2 smart skip는 nullable callback contract를 반쯤만 지켜 manuscript가 있으면 `calculate_arc_from_episode`에서 즉시 크래시한다 | `related-but-new-shared-helper-surface` |
| `MPN-T2-04` | T2 | `P2` | `_calculate_arc_from_episode()`의 5화 고정 버킷이 Stage2 가변 `ep_count` 계약과 충돌한다 | `related-but-new-shared-helper-surface` |
| `MPN-T3-001` | T3 | `P1` | 비문자열 `strategy_doc` fail-open으로 권 경계 검증이 우회된다 | `none` |
| `MPN-T3-002` | T3 | `P2` | Stage 1 helper가 `main_a.py` private validator에 숨은 결합을 유지한다 | `related-but-new-shared-helper-surface` |
| `MPN-T3-003` | T3 | `P2` | Stage 1 성공 경로 테스트가 실제 boundary callback을 실행하지 않는다 | `related-but-new-shared-helper-surface` |
| `MPN-T4-001` | T4 | `P1` | rollback/reset/wipe 뒤 삭제된 미래 회차 narrative summary anchor가 Stage4 재시작 프롬프트에 다시 주입될 수 있다 | `none` |
| `MPN-T4-002` | T4 | `P2` | summary 생성기가 실제 회차 집합이 아닌 산술 창을 `ep_range`로 저장해 sparse resume 구간에서 보존 범위를 잘못 표기한다 | `none` |
| `MPN-T4-003` | T4 | `P2` | Stage4가 series/volume summary를 두 경로에서 중복 적재하며 하드코딩 상한도 그대로 남아 있다 | `related-but-new-shared-helper-surface` |
| `MPN-T5-001` | T5 | `P1` | Stage2 smart skip이 4화 시스템 위에서 여전히 5화 버킷 helper를 소비하고, 테스트도 그 stale 계약을 고정한다 | `related-but-new-shared-helper-surface` |
| `MPN-T5-002` | T5 | `P2` | Stage4만 `_safe_commit` 반환값을 무시해 shared persistence 계약이 분기된다 | `related-but-new-shared-helper-surface` |
| `MPN-T5-003` | T5 | `P2` | Stage2 smoke fixture가 `safe_commit_async -> bool` 계약을 잘못 모사하고 현재 workspace에서는 둘 다 skip된다 | `none` |
| `MPN-T5-004` | T5 | `P3` | Stage3 DI slot coverage test가 MagicMock auto-attribute 때문에 실제 app surface drift를 놓칠 수 있다 | `none` |

## 결론

- 이번 트랙의 통합 baseline은 `16 confirmed findings`다.
- 우선 remediation 순서는 `protagonist/arc mapping SSOT 통일 -> preset/commit success semantics 정렬 -> Stage01 hidden coupling 제거 -> narrative summary lifecycle 정리`가 적절하다.
- 최종 SSOT 승격 여부는 `main_a-persistence-narrative-detail-consolidated-findings-3pass-reaudit.md` 기준으로 판단한다.
