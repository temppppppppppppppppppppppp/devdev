# GMR-A Composition Root & Live Wiring Findings

> Date: 2026-03-13
> Commit: `d9825a69`
> Workspace State: dirty

## PASS 1 관찰

- `main_a.py:262-390`에서 `SovereignApp`이 UI, `StudioSystem`, Service, Orchestrator, logger, session logger, runtime audit를 직접 조립한다.
- `main_a.py:2250-2333`에서 메인 메뉴, Stage 진입, one-stop, destructive safe-op를 모두 직접 디스패치한다.
- `main_a.py:2754-2992`, `3557-3630`에서 Stage 2/3/4 진입은 thin wrapper처럼 보이지만, 실제로는 매번 `StageXContext.from_app()`로 live app surface를 다시 조립한다.

## PASS 2 교차 검증

- `modules/core/stage2_context.py`, `stage3_context.py`, `stage4_context.py`는 모두 `from_app()`로 `main_a.py`의 속성과 private callback을 직접 읽는다.
- `modules/core/stage4_orchestrator.py:198-205`도 컨텍스트가 없으면 다시 `Stage4Context.from_app(self.app)`로 app-bound fallback을 수행한다.
- 따라서 분리된 orchestrator가 존재해도, composition truth는 여전히 `SovereignApp`이다.

## PASS 3 최종 findings

### [GMR-A-001] `main_a.py`가 여전히 실질 composition root다

- Severity: `P1`
- Evidence:
  - `main_a.py:262-390`
  - `main_a.py:1053-1168`
  - `main_a.py:2250-2333`
- Why macro risk:
  - Stage runtime, menu shell, service registry, safe-op, one-stop가 한 클래스에 집중돼 있어 구조 변경 시 drift가 `main_a.py`에 다시 축적된다.
  - `modules/*` 분리가 진행돼도 live wiring 판단은 계속 `main_a.py`를 읽어야 닫힌다.
- Recommended next order:
  - 후속 구조 문서에서 `main_a.py`를 façade가 아니라 composition root로 명시 고정.

### [GMR-A-002] Service/Orchestrator 분리는 live이지만 여전히 app-bound wrapper 구조다

- Severity: `P2`
- Evidence:
  - `main_a.py:2758-2761`
  - `main_a.py:2987-2992`
  - `main_a.py:3623-3630`
  - `modules/core/stage2_context.py:315-370`
  - `modules/core/stage3_context.py:101-127`
  - `modules/core/stage4_context.py:194-237`
- Why macro risk:
  - Stage 모듈이 독립 protocol보다 `from_app()`에 크게 의존한다.
  - callback seam이 넓어 테스트상 분리와 실운영 wiring의 간극이 계속 생길 수 있다.
- Recommended next order:
  - 각 Stage context의 필수 slot과 callback을 “runtime contract” 문서로 별도 동결.

## Closed assumptions

- Orchestrator 추출이 dead refactor라는 가설은 기각한다.
- 현재 구조는 “분리 실패”가 아니라 “분리됐지만 중앙 조립이 여전히 강한 상태”로 보는 것이 맞다.

## Last Verified
- Date: 2026-03-13
- Commit: `d9825a69`
- Workspace State: dirty
- Code Sync (Yes/No): Yes
- Verified By: Codex
