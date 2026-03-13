# main_a Control Plane Detail Consolidated Findings

> 작성일: 2026-03-13
> 상태: `executed / consolidated`
> 범위: `MCP-T1` ~ `MCP-T5` 통합본
> 기준 오더: `main_a-control-plane-detail-full-survey-audit-order.md`
> 확정 결과: `총 15건 (P0 0 / P1 6 / P2 7 / P3 2)`

이 문서는 2026-03-13 기준 T1~T5 PASS3 결과를 재구성한 통합 SSOT다. 교차 터미널 중복 제거로 삭제된 finding은 없었고, 오더의 duplicate enum을 맞추기 위해 T2 원문이 쓴 `none found`는 통합 ledger에서 `none`으로 정규화했다. finding의 실질 내용은 바꾸지 않았다.

---

## 터미널별 상태

| 터미널 | 소스 상태 | 문서 | PASS 요약 | 최종 건수 |
|--------|-----------|------|-----------|-----------|
| T1 | `PASS3 completed` | `MCP-T1-boot-project-binding-findings.md` | `PASS1 4 -> PASS2 제거 2 -> 최종 2` | 2 |
| T2 | `executed` | `MCP-T2-agent-bootstrap-di-findings.md` | `PASS1 4 -> PASS2 제거 1 -> 최종 3` | 3 |
| T3 | `executed / PASS3 finalized` | `MCP-T3-menu-stage-entry-findings.md` | `PASS1 5 -> PASS2 제거 2 -> 최종 3` | 3 |
| T4 | `3pass executed` | `MCP-T4-destructive-ops-recovery-findings.md` | `PASS1 6 -> PASS2 제거 3 -> 최종 3` | 3 |
| T5 | `PASS 3 complete / confirmed` | `MCP-T5-control-contract-regression-findings.md` | `PASS1 6 -> PASS2 제거 2 -> 최종 4` | 4 |

## Severity Summary

| Severity | T1 | T2 | T3 | T4 | T5 | 확정 |
|----------|----|----|----|----|----|------|
| P0 | 0 | 0 | 0 | 0 | 0 | 0 |
| P1 | 2 | 1 | 0 | 2 | 1 | 6 |
| P2 | 0 | 2 | 2 | 1 | 2 | 7 |
| P3 | 0 | 0 | 1 | 0 | 1 | 2 |
| 합계 | 2 | 3 | 3 | 3 | 4 | 15 |

## 상위 위험군

| 위험군 | 포함 finding | 의미 |
|--------|--------------|------|
| Boot / project binding | `MCP-T1-001`, `MCP-T1-002`, `MCP-T2-03` | 프로젝트별 credential, project root, legacy fallback path가 같은 bound root를 보지 않아 잘못된 프로젝트/키 바인딩으로 이어질 수 있다 |
| Destructive ops / recovery invariant | `MCP-T4-001`, `MCP-T4-002`, `MCP-T4-003` | destructive delete 후 false-return, rollback 후 복선 전량 삭제, shutdown close skip가 결합돼 복구 불가능한 drift를 만든다 |
| External control contract drift | `MCP-T5-001`, `MCP-T5-002` | desktop, validator, runner, `main_a.py`가 같은 interactive 계약을 공유하지 않는다 |
| Stage entry / resume / observability drift | `MCP-T3-01`, `MCP-T3-02`, `MCP-T3-03` | operator-facing 진행 배너, Stage 4 target floor, Stage 4 session logging이 서로 다른 기준으로 움직인다 |
| Bootstrap DI / regression trust gap | `MCP-T2-01`, `MCP-T2-02`, `MCP-T5-003`, `MCP-T5-004` | hidden app dependency와 source-string 회귀망 때문에 refactor safety 신호가 과대평가된다 |

## 취합 메모

- 기존 OPUS, frontier-lag, UI-connectivity 문서에서 이미 닫힌 항목은 재오픈하지 않았다.
- `MCP-T1-002`와 `MCP-T2-03`은 둘 다 root binding 문제지만, 하나는 boot control plane의 project selection surface이고 다른 하나는 `_init_v50_modules()` 내부 legacy fallback surface라 별개로 유지했다.
- `MCP-T4-001`과 `MCP-T4-002`도 같은 rollback 테마지만, 전자는 service transaction split-brain이고 후자는 app-level foreshadow cleanup 오용이라 중복으로 처리하지 않았다.
- `MCP-T2-01`, `MCP-T2-03`의 source duplicate 문구 `none found`는 오더의 enum 요구사항에 맞춰 각각 `none`으로 정규화했다.

## 통합 Ledger

| ID | 터미널 | Sev | 주제 | duplicate status |
|----|--------|-----|------|------------------|
| `MCP-T1-001` | T1 | `P1` | 프로젝트별 `.env`가 `ProjectContext` 초기화 중 root `.env`로 재오염된다 | `none` |
| `MCP-T1-002` | T1 | `P1` | `GEULDOBI_PROJECTS_ROOT` SSOT를 우회해 잘못된 프로젝트 트리를 열 수 있다 | `related-but-new-control-plane-surface` |
| `MCP-T2-01` | T2 | `P2` | partial V50 init failure가 bootstrap success로 은닉된다 | `none` |
| `MCP-T2-02` | T2 | `P2` | Stage 3 smart retrieval이 injected context를 우회하고 `app`을 직접 읽는다 | `related-but-new-control-plane-surface` |
| `MCP-T2-03` | T2 | `P1` | legacy JSON fallback이 bound project root 대신 `_PROJECTS_DIR`에 고정된다 | `none` |
| `MCP-T3-01` | T3 | `P2` | resume 배너와 Stage 2/3 manuscript head 계산이 다른 source를 본다 | `none` |
| `MCP-T3-02` | T3 | `P2` | 메뉴 `4번` Stage 4 target 입력이 현재 production head를 반영하지 않는다 | `related-but-new-control-plane-surface` |
| `MCP-T3-03` | T3 | `P3` | `main_a.py`의 manual Stage 4 context 주입이 `session_logger`를 누락한다 | `related-but-new-control-plane-surface` |
| `MCP-T4-001` | T4 | `P1` | destructive op가 `False`를 반환한 뒤에도 이미 일부 DB 삭제가 커밋된다 | `related-but-new-control-plane-surface` |
| `MCP-T4-002` | T4 | `P1` | rewind/rollback 후처리가 target 이전 복선까지 전부 지운다 | `related-but-new-control-plane-surface` |
| `MCP-T4-003` | T4 | `P2` | shutdown이 anchor save 실패를 비차단 처리하지 않아 DB close 경로가 끊긴다 | `none` |
| `MCP-T5-001` | T5 | `P1` | desktop/bridge의 Stage 0 `sub_key` 계약이 `main_a.py` 실제 번호 체계와 어긋난다 | `related-but-new-control-plane-surface` |
| `MCP-T5-002` | T5 | `P2` | boot confirm은 조건부인데 runner는 무조건 `y`를 주입한다 | `related-but-new-control-plane-surface` |
| `MCP-T5-003` | T5 | `P2` | protocol 이름과 추출된 service 구현 의미가 분리됐는데 회귀망은 이를 검증하지 않는다 | `none` |
| `MCP-T5-004` | T5 | `P3` | control-plane 회귀망이 source-string assertion에 과의존한다 | `none` |

## 결론

- 이번 트랙의 통합 baseline은 `15 confirmed findings`다.
- 우선 remediation 순서는 `boot/root binding -> destructive ops/recovery -> external control contract -> stage entry/DI observability`가 적절하다.
- 최종 SSOT 승격 여부는 `main_a-control-plane-detail-consolidated-findings-3pass-reaudit.md` 기준으로 판단한다.
