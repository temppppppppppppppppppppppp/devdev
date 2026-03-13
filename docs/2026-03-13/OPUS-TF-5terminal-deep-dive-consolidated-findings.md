# OPUS TF 5-Terminal 심층 감사 통합본

> 작성일: 2026-03-13
> 기준 문서:
> - `S-T1-stage0-ui-flow-deep-dive-findings.md`
> - `S-T2-cross-stage-root-cause-deep-dive-findings.md`
> - `S-T3-lite-mode-tools-deep-dive-findings.md`
> - `S-T4-api-desktop-deep-dive-findings.md`
> - `S-T5-security-performance-scale-deep-dive-findings.md`
> 조사 모드: static / read-only / deep-dive / no code modification

---

## Executive Summary

3차 심층 감사는 1차·2차 문서의 빈 구간을 메우는 목적에 맞게 수행됐다. 이번 통합본의 결론은 두 층으로 나뉜다.

첫째, **기존 미해결 상위위험 7건은 현재 트리 기준으로 대부분 정리됐다.** 실제로 루트코즈가 남은 것은 `plot_roadmap` handoff 1건이며, 4건은 현행 코드에서 해소됐다.

둘째, 그와 별도로 **새로운 심층 ledger 11건**이 확정됐다. 분포는 `P1 2건 / P2 8건 / P3 1건`이다. 이번 심층본의 최상위 이슈는 아래 두 가지다.

- `S-T1-001`: Stage 0 복구 경로에서 외부 시점 정책 선택이 기본값으로 덮이는 silent wrong result
- `S-T4-001`: Desktop 경로에서 위험 키 dual-control 승인이 사실상 우회됨

---

## 최종 집계

| Severity | 건수 |
|----------|------|
| P0 | 0 |
| P1 | 2 |
| P2 | 8 |
| P3 | 1 |
| **합계** | **11** |

터미널별 분포:

| Terminal | 건수 | 비고 |
|----------|------|------|
| T1 | 3 | Stage 0 메뉴 드리프트 / handoff 루트코즈 |
| T2 | 1 | historical root-cause 재확정 |
| T3 | 4 | Lite Mode raw Gemini / host-bound tools |
| T4 | 2 | Desktop 승인 경계 / 테스트 경로 drift |
| T5 | 1 | 글로벌 cache namespace / scale debt |

---

## Section A — 기존 미해결 P0/P1 추적 결과

| 기존 ID | 현재 상태 | 메모 |
|--------|----------|------|
| `T2-001` | **root-cause remains** | `plot_roadmap`가 생성기 산출물이 아니라 save patch에 의존 |
| `T3-003` | open | handoff 통합 테스트 갭 |
| `T3-004` | open | advisory 병렬 테스트 갭 |
| `T3-029` | resolved | continuity unresolved는 현재 audit/log 경로로만 남음 |
| `T4-P1-03` | resolved | 단일 후보 auto-PASS 금지 |
| `T4-P1-04` | resolved | PASS 계열은 `CONDITIONAL_PASS`로 완화 |
| `T5-WS-016` | resolved | FactLedger dead NPC guard 존재 |

핵심 해석:

- 과거 문서의 "미해결 상위위험 다수" 상태는 현재 트리 기준 그대로 유지되지 않는다.
- 실제 open root-cause는 `T2-001`이 중심이다.
- `T3-003`, `T3-004`는 코드 결함보다 테스트 갭으로 남는다.

---

## Section B — 신규 심층 발견사항

### P1

| ID | 요약 | 파일 |
|----|------|------|
| `S-T1-001` | `phase_0_recovery()` 외부 시점 정책 선택이 깨진 리터럴 때문에 기본값으로 덮임 | `stage01_helpers.py`, `project_support.py` |
| `S-T4-001` | Desktop 실경로에서 위험 키 dual-control 승인이 사실상 우회됨 | `preload.js`, `src/main.js`, `bridge_server.py` |

### P2

| ID | 요약 | 파일 |
|----|------|------|
| `S-T1-002` | `plot_roadmap` 계약이 생성기 밖 save patch에 의존 | `stage0/__init__.py`, `stage01_helpers.py` |
| `S-T2-001` | `T2-001` 루트코즈가 현재도 save boundary dependency로 잔존 | `stage0/__init__.py`, `stage01_helpers.py`, `stage2_orchestrator.py` |
| `S-T3-001` | Lite Mode `ui_discovery.py` raw Gemini HTTP + query-key 경로 | `lite_mode/bridge/ui_discovery.py` |
| `S-T3-002` | `lite_mode/test_ui_discovery.py` live API 수동 진단 스크립트 | `lite_mode/test_ui_discovery.py` |
| `S-T3-003` | host-bound 절대경로 + 직접 DB mutation 도구군 잔존 | `tools/*`, `tools2/*` 일부 |
| `S-T3-004` | `blueprint_editor.py`가 DBManager 없이 SQLite 직접 수정 | `main_tools/blueprint_editor.py` |
| `S-T4-002` | API 계약 테스트가 real server가 아니라 RouterStub에 묶여 drift를 숨김 | `tests/test_api_contract.py`, `tests/test_run_validator.py` |
| `S-T5-001` | `BaseAgent` 글로벌 context cache namespace/eviction이 프로젝트 단위로 일관되지 않음 | `base_agent.py` 및 다수 호출부 |

### P3

| ID | 요약 | 파일 |
|----|------|------|
| `S-T1-003` | Stage 0 주인공 설정 플로우가 2곳에 복제돼 이미 drift 발생 | `stage0/__init__.py`, `stage01_helpers.py` |

---

## Section C — 보안 취약점 요약

### 신규 심층본 기준 상위 위험

1. `S-T4-001`
   Desktop runtime이 위험 키 승인을 실질적으로 비운다.

2. `S-T1-001`
   보안 이슈는 아니지만 사용자 선택이 조용히 변질되는 silent wrong result다.

### 기존 ledger에서 이어지는 중대 carry-over

이번 심층본에서는 중복 금지 때문에 재-ID를 부여하지 않았지만, 아래 기존 위험은 여전히 운영상 중요하다.

- `D-T5-002`: renderer 직접 Gemini fetch
- `D-T5-003`: CSP `unsafe-inline`

즉, Desktop 경계는 심층 감사 후에도 여전히 최우선 위험 영역이다.

---

## Section D — 성능 병목 및 규모 경계

| 항목 | 유형 | 해석 |
|------|------|------|
| `S-T5-001` 글로벌 context cache | scale/perf | 에이전트·프로젝트 간 상호 축출로 cache 효율 하락 가능 |
| `S-T3-003` host-bound tools | ops/perf | 특정 환경에서만 성립하는 직접 DB mutation 도구군 |
| `T3-004` advisory 병렬 테스트 갭 | perf assurance | 실제 timeout/부분실패 성능 경계 검증 부족 |

핵심 해석:

- production core의 즉시 P0/P1 성능 폭탄보다는, **멀티프로젝트·장시간 배치에서 생기는 격리/효율 저하**가 더 큰 축이다.

---

## Section E — 삭제 / 격리 / legacy 판정

### 격리 권고

- `lite_mode/test_ui_discovery.py`
- `tools/normalize_arcs_db.py`
- `tools/db_porter.py`
- `tools/fix_future_items.py`
- `tools/make_BP.py`
- `tools/concat_txt.py`
- `tools2/expand_ep15.py`

### legacy-only 성격으로 재분류 권고

- Lite Mode Selenium/Gemini 자동화 경로
- `main_tools/blueprint_editor.py`

판정 기준:

- production abstraction 우회
- 특정 사용자/특정 작품 절대경로 전제
- 직접 DB mutation
- 수동 운영 절차 의존

---

## Section F — 프로토콜 / handoff 대조표

### Stage handoff

| 경계 | 현재 결론 |
|------|----------|
| Stage 0 → Stage 2 | `plot_roadmap` 생성기 직접 보장 실패, save patch 의존 |
| Stage 2 → Stage 3 | 현행 코드상 구조적 break 근거는 약화 |
| Stage 3 → Stage 4 | 테스트 갭은 남지만 historical P1 일부 해소 |
| Stage 4 → DB | 핵심 write path 유지 |
| Stage 4 → 다음 에피소드 | prior high-risk 4건 중 다수가 해소 |

### API / Desktop protocol

| 경계 | 현재 결론 |
|------|----------|
| OpenAPI → Desktop preload | `approval_id` 표면 누락 |
| Desktop main → bridge_server | 위험 키 auto-approval 경로 존재 |
| Contract tests → real runtime | RouterStub drift로 실서버 검증 불충분 |

---

## 결론

3차 심층 감사의 최종 결론은 명확하다.

- 과거 상위위험 중 상당수는 현재 코드에서 이미 닫혔다.
- 남은 루트코즈는 `plot_roadmap` handoff 구조다.
- 새로 확인된 최상위 위험은 **Desktop 승인 경계 우회**다.

따라서 후속 실행 우선순위는 다음과 같다.

1. `S-T4-001` 수정: Desktop 위험 키 승인 경계 복구
2. `S-T1-001` 수정: Stage 0 복구 경로 메뉴 단일화
3. `S-T1-002` / `S-T2-001` 수정: `plot_roadmap`를 생성기 산출물 계약으로 승격
4. `S-T3-*` 정리: Lite/Tools를 manual-only/legacy로 명시 격리
