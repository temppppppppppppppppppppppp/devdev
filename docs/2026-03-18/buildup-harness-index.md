# 거버넌스 하네스 인덱스 (HARNESS-INDEX)

**문서 유형**: 빌드업 (S7-OPP-08 네비게이터)
**작성일**: 2026-03-18
**상태**: INDEX — 하네스 통합이 아닌 네비게이션 문서
**감리**: 3회 전면 재조사 + 적대적 3-pass 완료 (6 TF 병렬 투입)
**교정 이력**: 초판 ~40 → 2차 51+ → 3차 55+ → **4차 재검증: 하네스 파일 ~39 + 지원 문서 ~22 = 거버넌스 총 ~61**

---

## 1. 진입점

```
사용자 요청
  │
  ├─ 시스템 트랙 (코드/인프라/테스트/DB)
  │   → AGENTS.md → system-order-init-harness.md
  │
  └─ 서사 트랙 (Treatment/BI/스토리)
      → docs/blockguide/AGENTS.md → SSOT_blockguide-integrated-order.md
```

**최상위 권한**: `AGENTS.md` > init harness > companion harness > `CLAUDE.md`

---

## 2. 시스템 트랙 — 모드별 하네스 선택 매트릭스

### 2.1 Init Harness 모드 결정 (검증 완료: init harness Step 3, L87-105)

| 모드 | 트리거 | 설명 |
|------|--------|------|
| **A** | 활성 큐/로드맵 존재 | Queue Realization — 기존 실행 계획 이행 |
| **B** | 조사/감사/실행문서 생산 | Survey/Audit/Execution-Doc Production |
| **B1** | 라이브 런 직후 + 감사 | Live-Run Merge Survey |
| **C** | 좁은 범위 직접 패치 | Direct Focused Patch |

### 2.2 모드별 동반 하네스 (13개 핵심)

| 하네스 | A | B | B1 | C | 설명 |
|--------|---|---|----|----|------|
| `system-order-preflight-harness` | O | O | O | - | 사전 검증 (고위험/광범위 작업) |
| `system-full-survey-execution-harness` | - | **O** | - | - | 전수조사 + 부작용 체크리스트 |
| `deep-global-integrity-survey-harness` | - | O | - | - | 20단계 심층 무결성 (고강도 요청 시) |
| `live-run-merge-survey-harness` | - | - | **O** | - | 라이브런 후 병합 감사 |
| `execution-synthesis-harness` | O | O | O | - | 다중 소스 증거 통합 |
| `temp-execution-queue-roadmap-harness` | **O** | O | - | - | 로드맵 생성/우선순위 |
| `document-3pass-audit-harness` | - | O | O | - | 3-pass 문서 검토 + 95% 신뢰 게이트 |
| `evidence-manifest-harness` | - | O | O | - | 증거 추적성 |
| `ops-validator-harness` | O | - | - | - | 큐 검증, 정규 무결성 |
| `execution-closure-harness` | O | - | - | - | 실현 완료 항목 정리 |
| `exception-registry-harness` | O | O | O | O | 명시적 예외 허용 목록 |
| `process-health-scorecard-harness` | O | - | - | - | 운영 상태 보고 |
| `stale-reference-sweep-harness` | - | O | - | - | 구 참조 정리 |

> 모든 13개 파일 존재 확인 완료 (`docs/implementation/` 디렉토리).

### 2.3 추가 하네스 (초판 미등재 — 적대적 감리에서 발견)

| 하네스 | 위치 | 용도 |
|--------|------|------|
| `auto-frontier-lag-n-arc-test-harness-ssot.md` | `docs/2026-03-14/` | 프론티어 래그 자동 테스트 |
| `main-a-manual-stage0-selection-harness-00_20260314.md` | `docs/2026-03-14/` | Stage 0 수동 선택 UI |
| `TF-BH1_block_harness_reinforcement.md` | `docs/blockguide/` | 블록 하네스 보강 |
| `harness_3pass_audit_and_patch.md` | `docs/blockguide/` | 3-pass 감사 + 패치 |
| `codex_comment_on_harness_3pass_audit_and_patch.md` | `docs/blockguide/` | 위 하네스 코멘터리 |
| `dynasty-heir-remediation-harness.md` | `docs/2026-03-09/` | 프로젝트별 교정 |
| `alt_history_material_json_harness.md` | `docs/2026-03-10/` | 대체역사 자료 셋업 |

> **참고**: 이 하네스들은 날짜별 디렉토리에 위치하며, 일부는 프로젝트별/일시적 용도. 핵심 13개 시스템 하네스와 성격이 다름.

### 2.4 날짜별 3-pass 감사 동반 문서 (3차 재조사 발견)

| 문서 | 위치 |
|------|------|
| `alt_history_material_json_harness_3pass_audit.md` | `docs/2026-03-10/` |
| `autorun_harness_docs_3pass_audit.md` | `docs/2026-03-10/` |
| `next_step_harness_docs_3pass_audit.md` | `docs/2026-03-10/` |
| `codex_blockguide_failed_tr_harness_reinforcement_plan.md` | `docs/2026-03-11/` |
| `codex_blockguide_failed_tr_harness_reinforcement_3pass_audit.md` | `docs/2026-03-11/` |

### 2.5 Python 스크립트 하네스 (3차 재조사 발견)

| 스크립트 | 위치 | 크기 | 용도 |
|---------|------|------|------|
| `run_auto_frontier_lag_harness.py` | `scripts/` | 36K | 프론티어 래그 자동화 테스트 |
| `tr_batch_harness.py` | `scripts/` | 59K | 배치 트리트먼트 블록 생성 |
| `validation_test_harness.py` | `tools2/` | 18K | V66.1 검증 파이프라인 |

---

## 3. 서사 트랙 — 하네스 체인

| 순서 | 하네스 | 트리거 |
|------|--------|--------|
| 허브 | `SSOT_blockguide-integrated-order.md` | 모든 서사 작업 |
| Phase 0 | `treatment-planning-harness.md` | 트리트먼트 기획 |
| Phase 1 | `treatment-production-harness-v2.md` | 트리트먼트 실현 |
| Phase 2 | `bi-production-harness-v1.md` | 바이블 생성 |
| 선택 | `alt_history_db_harness.md` | 대체역사 장르 |
| 선택 | `modern_fantasy_material_harness.md` | 현대판타지 장르 |

> 모든 6개 파일 존재 확인 완료 (`docs/blockguide/` 디렉토리).

---

## 4. 지원 계층 — 템플릿/계약/루브릭

### 4.1 템플릿 (9개)
| 템플릿 | 용도 |
|--------|------|
| `execution-ssot-template` | 실행 SSOT 문서 작성 |
| `execution-roadmap-template` | 로드맵 작성 |
| `execution-closure-template` | 실행 종료 문서 |
| `evidence-manifest-template` | 증거 매니페스트 |
| `execution-exception-template` | 예외 등록 |
| `process-health-scorecard-template` | 건강 스코어카드 |
| `deep-global-survey-template` | 심층 전수조사 |
| `cross-cut-integrity-matrix-template` | 교차 무결성 |
| `uncertainty-contradiction-ledger-template` | 불확실성 원장 |

### 4.2 계약 (6개)
| 계약 | 핵심 규칙 |
|------|----------|
| `canonical-naming-contract` | 파일명 정규화 규칙 |
| `commit-state-minimal-contract` | 커밋 시 최소 상태 보장 |
| `codebase-global-survey-coverage-contract` | 전수조사 커버리지 기준 |
| `single-ssot-roadmap-contract` | 하나의 SSOT 로드맵 원칙 |
| `evidence-triangulation-contract` | 증거 삼각 검증 |
| `integrity-confidence-scoring-contract` | 무결성 신뢰도 채점 |

### 4.3 루브릭/체크리스트 (4개)
| 문서 | 용도 |
|------|------|
| `queue-priority-rubric` | 큐 항목 우선순위 결정 |
| `side-effect-survey-checklist` | 부작용 점검 |
| `operations-governance-map` | 운영 거버넌스 전체 지도 |
| `release-gate-v1` | 릴리스 게이트 기준 |

---

## 5. 문서 수량 요약

| 트랙 | 카테고리 | 수량 |
|------|---------|------|
| 루트 거버넌스 | AGENTS.md, CLAUDE.md, blockguide/AGENTS.md | 3 |
| 시스템 | 핵심 하네스 | 13 |
| 시스템 | 날짜별/프로젝트별 하네스 | 9+ |
| 시스템 | 날짜별 3-pass 감사 동반 | 5+ |
| 시스템 | Python 스크립트 하네스 | 3 |
| 시스템 | 템플릿 | 9 |
| 시스템 | 계약/루브릭 | 10 |
| 서사 | 핵심 하네스 | 4 |
| 서사 | 선택/특화/보강 | 5+ |
| **하네스 소계** | | **~39** |
| **지원 문서 소계** | (템플릿+계약+루브릭) | **~22** |
| **거버넌스 총계** | | **~61** |

---

## 6. Document Save Rule 중복 현황

| 위치 | 내용 |
|------|------|
| `AGENTS.md` L33-42 | 3-pass 감사 + 95% 신뢰 게이트 (일반 규정) |
| `system-order-init-harness.md` L164-173 | 정규 vs temp 경로 + 3-pass (시스템 트랙 상세) |
| `system-full-survey-execution-harness.md` L148+ | "Document Save Gate" 반복 |
| `document-3pass-audit-harness.md` L16-42 | **정식 절차 정의** (3-pass 상세) |

**권고**: `document-3pass-audit-harness.md`를 SSOT로 지정, 나머지 3곳은 참조만.

---

## 7. 주의 사항 (적대적 감리 지적)

1. **빈도 순위는 근거 없는 추정**: 사용 빈도 추적 시스템이 없으며, 논리적 추론에 기반. 경험적 데이터가 쌓이면 갱신 필요.
2. **하네스 선택 모호성**: Mode B에서 "일반 조사" vs "심층 무결성 조사" 경계가 init harness에 명확히 정의되지 않음. 운영자 판단에 의존.
3. **날짜별 하네스 수명**: `docs/2026-03-09/`, `docs/2026-03-14/` 등에 위치한 하네스는 프로젝트별/일시적 성격일 수 있음. 정기적 정리 필요.
