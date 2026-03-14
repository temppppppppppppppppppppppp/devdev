# 전역 거시 조사 통합 결과 - 3PASS 재감리

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty
> Scope: GMR-A ~ GMR-H

## PASS 1 수집 요약

- live composition root는 `main_a.py`의 `SovereignApp`으로 확인됐다.
- durable handoff truth는 DB 중심으로 확인됐다.
- desktop/backend는 API-native engine이 아니라 CLI protocol wrapper 구조로 확인됐다.
- 관측성은 풍부하지만 correlation key가 분산돼 있다.
- build/release는 문서상 `engine.exe` 제품보다 source-bundle fallback 현실에 가깝다.

## PASS 2 교차 검증 요약

- `docs/stage_map/*`와 현재 코드의 큰 축은 대체로 맞는다.
- 다만 safe-op runtime restore, Stage 4 artifact completeness, approval gate 운영 경로, release guide는 문서보다 구현 nuance가 더 거칠다.
- 기존 2026-03-13 상세 조사 문서군과도 방향은 맞지만, 이번 문서는 그보다 상위의 구조 판단 기준을 다시 고정했다.

## PASS 3 최종 우선순위

### P1

1. `main_a.py`가 여전히 실질 composition root다.
2. safe-op의 DB 복원과 runtime 복원이 서로 다른 실패 의미론을 가진다.
3. Stage 4 PASS artifact는 단일 atomic package가 아니라 hard sink와 soft sink로 갈라진다.
4. risk approval gate는 live approval registration/load path가 드러나지 않는다.
5. observability plane 사이에 단일 provenance key가 없다.
6. 릴리스 현실은 `engine.exe` 문서보다 source-bundle fallback에 가깝다.

### P2

1. service/orchestrator 분리는 live이지만 app-bound wrapper 의존이 강하다.
2. legacy shared cursor와 local cursor 패턴이 혼재한다.
3. stage repair seam이 ownership boundary를 흐린다.
4. advisory/post-select 병렬 검사는 의도적으로 fail-open이다.
5. shadow main file과 alternate automation surface가 유지보수 혼선을 만든다.
6. desktop package test는 curated subset이지 full regression envelope가 아니다.

### closed / non-finding

1. DB가 현재 durable handoff truth라는 점은 문서와 코드가 대체로 일치한다.
2. `UI/`는 runtime code가 아니라 reference asset archive로 보는 것이 맞다.

## 통합 결론

현재 시스템의 가장 큰 문제는 “개별 버그가 많다”가 아니다.  
가장 큰 문제는 **중앙 조립 루트 집중**, **hard/soft persistence 경계 혼재**, **CLI shell을 감싼 control plane의 현실**, **문서와 shipping reality의 일부 분리**다.

즉 다음 단계의 ROI가 높은 순서는 아래와 같다.

1. composition root / stage context / repair seam의 소유권 문서 동결
2. safe-op 및 Stage 4 artifact completeness 상태 표준화
3. approval gate live source와 provenance key 표준화
4. desktop/release guide를 현재 shipping path 기준으로 재작성
5. live vs shadow surface를 명시적으로 표기

## 참고 산출물

- `GMR-A-composition-root-live-wiring-findings.md`
- `GMR-B-persistence-safeop-boundary-findings.md`
- `GMR-C-stage-contract-handoff-findings.md`
- `GMR-D-control-plane-desktop-findings.md`
- `GMR-E-state-cache-concurrency-findings.md`
- `GMR-F-observability-provenance-findings.md`
- `GMR-G-live-vs-legacy-surface-findings.md`
- `GMR-H-test-release-envelope-findings.md`

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
