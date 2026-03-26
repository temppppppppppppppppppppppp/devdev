# Genre Expansion Consumer-Contract Survey Master Order

Date: 2026-03-26
Status: ready
Track: system-track, bounded survey
Workspace: `C:\Users\wjjo\Desktop\글도비`

## Purpose

- 조사 목표는 `장르 확장 관점에서 글도비 시스템이 BI/TR를 실제로 어떻게 소비하는지`를 맵핑하는 것이다.
- narrative 제작 의미론보다 `runtime consumer contract`를 우선 조사한다.
- 특히 `stable investment sample`과 `wuxia candidate sample`을 비교해, 무엇이 hard blocker인지, 무엇이 fallback인지, 무엇이 quality-only degradation인지 분리한다.

## Survey Samples

- Stable BI: `bible\01_bi_투자물_골든_카나리아 테스트.json`
- Stable TR: `treatments\01_tr_투자물_골든_카나리아 테스트.json`
- Candidate BI: `bible\0_bi_wuxia_heavenly_physician.json`
- Candidate TR: `treatments\wuxia_heavenly_physician_tr_block_070_draft.json`
- Candidate Phase0 if needed only: `treatments\_quarantine\wuxia_heavenly_physician_phase0_design.json`

## Common Rules

- 코드 수정 금지
- 문서 저장 금지
- 실제 코드 경로 기준으로 판단. 문서는 보조 참고만 사용
- `rg` 우선 사용
- 모든 결론에 `file:line` 근거를 붙일 것
- severity 분류:
  - `P0`: runtime hard blocker / 즉시 중단
  - `P1`: silent wrong behavior / quality 크게 저하 / 장르 오염
  - `P2`: soft degradation / 미래 리스크

## Required Output Format

각 터미널은 반드시 아래 형식으로 응답한다.

1. `Scope covered`
2. `Consumer map`
3. `Findings ordered by severity`
4. `Normalize-at-ingress opportunities`
5. `Open questions`

## Non-Goals

- narrative router / TR/BI 제작 하네스 자체 품질 감리
- 작품 서사 평가
- 코드 패치 제안 상세 구현

## Terminal 1

```text
넌 1번 터미널이다.

You are doing a bounded system-track survey in `C:\Users\wjjo\Desktop\글도비`.

Scope:
- `modules/core/project_manager.py`
- `modules/core/stage01_helpers.py`
- `modules/core/stage0_handoff.py`
- `modules/core/response_schemas.py`
- `main_a.py` around Phase 0 / DNA sync entry

Focus:
- How BI/TR are imported into runtime or DB anchors
- Accepted TR JSON shapes: list vs dict-with-blocks vs other
- How `plot_roadmap` is created, normalized, or validated at ingress
- Whether `wuxia_heavenly_physician` can enter through the same import path as `golden canaria`
- Exact hard blockers for raw candidate BI/TR

Ignore:
- downstream Stage 3/4 writing logic
- narrative generation docs

Return:
- ingress contract map
- exact shape assumptions
- P0/P1/P2 findings with file:line
- best normalization seam at ingress
```

## Terminal 2

```text
넌 2번 터미널이다.

You are doing a bounded system-track survey in `C:\Users\wjjo\Desktop\글도비`.

Scope:
- `main_a.py` around Stage 2 entry / one-stop / frontier flow
- `modules/core/stage2_orchestrator.py`
- `modules/core/stage2_preflight.py`
- any nearby Stage 2 helpers directly used by those paths

Focus:
- What Stage 2 actually reads from `plot_roadmap`
- Which fields are hard required vs optional vs fallback
- Whether summary-only roadmap entries are enough
- Whether `block_no`, `content.context`, `event_villain`, `solution`, `reward`, `title`, HUD name, `protagonist_config` are required
- Compare stable sample vs wuxia candidate against Stage 2 consumer contract

Return:
- Stage 2 consumer map
- hard blockers for candidate
- soft degradation risks
- normalize-at-ingress opportunities
```

## Terminal 3

```text
넌 3번 터미널이다.

You are doing a bounded system-track survey in `C:\Users\wjjo\Desktop\글도비`.

Scope:
- `modules/core/stage3_*`
- `modules/core/stage4_context*`
- `modules/core/stage4_orchestrator.py`
- `modules/domain/agents/analyst.py`
- `modules/domain/agents/chief_writer_context.py`
- closely related consumer files only if directly referenced

Focus:
- What BI/TR-derived fields are consumed after Stage 2
- Which fields silently fall back to defaults
- Whether missing `protagonist_config` fields can cause genre bias or wrong prompt assumptions
- How HUD, AssetLibrary, WorldState, Seeds, plot_roadmap, protagonist name are used in blueprint/manuscript context building
- Distinguish hard blocker vs silent quality corruption

Return:
- downstream context consumer map
- P0/P1/P2 findings with file:line
- exact default/fallback behaviors
- normalization opportunities before Stage 3/4
```

## Terminal 4

```text
넌 4번 터미널이다.

You are doing a bounded system-track survey in `C:\Users\wjjo\Desktop\글도비`.

Scope:
- `modules/core/constants.py`
- `modules/core/project_service.py`
- `modules/core/world_state.py`
- `modules/core/fact_ledger.py`
- `modules/core/db_manager.py` only where directly relevant

Focus:
- How protagonist/HUD/state are persisted and restored
- FinanceHUD vs MartialHUD handling in persistence and rollback
- Whether BI-derived data is lost, downgraded, or misread after anchor save/load
- Whether genre-specific assumptions remain in rollback, world state sync, fact ledger, or state replay

Return:
- persistence/recovery consumer map
- P0/P1/P2 findings with file:line
- where genre-specific drift still exists
- normalize-at-ingress vs persistence-layer normalization recommendation
```

## Terminal 5

```text
넌 5번 터미널이다.

You are doing a bounded system-track survey in `C:\Users\wjjo\Desktop\글도비`.

Scope:
- `modules/api/bridge_server.py`
- `modules/api/process_runner.py`
- `scripts/process_and_audit_tr_bi_loop.py`
- other API/operator surface files only if directly referenced

Focus:
- What operator/API surfaces expose or require BI/TR-derived fields
- Whether there are blockguide-only assumptions in bridge/UI/API surfaces
- Whether support scripts are falsely acting as runtime truth or gating
- How `plot_roadmap`, HUD root, protagonist_config, and Bible anchors are surfaced to operators

Return:
- API/operator consumer map
- P0/P1/P2 findings with file:line
- any blockguide bias that affects genre expansion
- notes on whether these are runtime-critical or operator-only
```

## Reduced Parallel Mode

터미널이 3개뿐이면 아래처럼 합친다.

- `1번`: Terminal 1 그대로
- `2번`: Terminal 2 + Terminal 3 범위 결합
- `3번`: Terminal 4 + Terminal 5 범위 결합

## Final Synthesis Order

```text
모든 터미널 결과를 합쳐 하나의 bounded `genre expansion consumer-contract map`으로 종합하라.

Required output:
1. Executive verdict
2. Hard blockers preventing `wuxia_heavenly_physician` from being consumed like `golden canaria`
3. Soft degradations / default-driven genre corruption
4. Canonical consumer contract
   - ingress
   - Stage 2
   - Stage 3/4
   - persistence/rollback
   - API/operator surfaces
5. Best normalization seam
   - ingress adapter
   - runtime consumer widening
   - persistence normalization
6. Recommended next action in cost order
   - smallest patch set
   - medium patch set
   - strategic refactor
```

## Notes For The Coordinator

- 조사 중 `하네스 문제`와 `runtime consumer problem`을 섞지 말고 분리해서 적는다.
- `골든_카나리아`는 stable sample일 뿐, 그것이 곧 canonical truth라는 전제는 두지 않는다.
- 핵심 질문은 `현재 글도비 시스템이 실제로 무엇을 소비하느냐`다.
- 결과 종합 시 `raw file contract`, `ingress normalization contract`, `runtime consumer contract`를 구분하면 이후 패치 방향이 선명해진다.
