# Stage 2 디테일 딥다이브 전량 전수조사 — 3Pass 감리 TF 오더

> 작성일: 2026-03-13
> 상태: 실행중

## 목적

Stage 2(Arc 설계 파이프라인) ~18,000줄 규모 전수조사.
1pass 탐색에서 식별된 P0~P3급 Finding 12건 + 데드코드 2건 후보를 3pass 감리로 오탐 제거 후 확정.
**코드 수정 금지 — 문서화만 수행**.

## 대상 범위

| 영역 | 줄수 |
|------|------|
| Core (stage2_*.py, stage3_orchestrator.py) | ~6,257 |
| Agents (analyst, arc_ensemble, director_ensemble 등) | ~10,909 |
| **합계** | **~17,166** |

## TF 구성: 5트랙 병렬

| Track | 코드명 | 핵심 체크 대상 |
|-------|--------|---------------|
| S2D-T1 | DI Contract & Callback Wiring | stage2_context 51슬롯, producer-consumer 계약, write-back 비대칭 |
| S2D-T2 | Validation Pipeline & Guard Chain | ArcAutoCorrector 대원칙1, Guard Python 판단 경계, threshold 불일치 |
| S2D-T3 | Preflight & State Management | StateTracker, state_changes 계약, enriched_block 전달 체인 |
| S2D-T4 | Finalizer & Director Integration | Equipment 강제동기화 대원칙2, DB 원자적 커밋, Director 자동선택 잔류 |
| S2D-T5 | Dead Code & Test Coverage | 미사용 에이전트, backward-compat wrapper, MagicMock spec, real-app 부재 |

## 3Pass 프로토콜

| Pass | 목적 | 산출물 |
|------|------|--------|
| 1pass | 전수조사 — 모든 메서드/연동 지점에서 후보 finding 수집 | 후보 테이블 (확신도 HIGH/MED/LOW) |
| 2pass | 근거 검증 — 코드 인용(전후 5줄), 테스트 근거, 기존 문서 대조 | 오탐 분류 |
| 3pass | 최종 확정 — Finding ID 부여, severity 확정, 권장 조치 | 확정 Finding 상세 |

## 산출물

```
docs/2026-03-13/
├── stage2-detail-deep-dive-3pass-audit-order.md              # 본 문서
├── S2D-T1-di-contract-callback-wiring-findings.md
├── S2D-T2-validation-pipeline-guard-chain-findings.md
├── S2D-T3-preflight-state-management-findings.md
├── S2D-T4-finalizer-director-integration-findings.md
├── S2D-T5-dead-code-test-coverage-findings.md
└── stage2-detail-deep-dive-consolidated-findings.md          # 통합 보고서
```

## Finding 형식

```
### [S2D-TN-SEQ] 제목
- Severity: P0/P1/P2/P3
- 위치: file.py:L###
- 근거: 코드 인용
- 판정: 확정/오탐/보류
- 권장 조치: (코드 수정 금지, 문서화만)
```

## 검증 기준

- 각 Finding에 파일:라인 근거 필수
- 기존 문서(MLW/MRF/MFS/MDH/ROP 시리즈)와 교차 확인하여 중복 제거
- 대원칙 침해 판정은 코드 인용 + 실행 경로 추적으로 확정
