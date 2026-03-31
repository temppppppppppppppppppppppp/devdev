# 0_1 Stage4 EP10-15 Residual Gate Observability Opus Insurance Order

아래 프롬프트는 insurance-only `Opus` bounded survey용이다. primary truth source는 먼저 생성된 내부 deep dive survey다.

- Primary baseline:
  - `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-survey.md`
  - `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-evidence.json`
- Role of Opus:
  - 위 결론을 맹신하지 말고 corroborate 또는 falsify
  - 새 코드 패치 금지
  - execution SSOT 생성 금지
  - `docs/temp/` mirror 금지

## Ready-to-Paste Prompt

```text
시스템 오더. survey-only로 진행.

먼저 `docs/implementation/system-order-init-harness.md`를 읽고, 이어서 `docs/implementation/system-full-survey-execution-harness.md`를 읽어라. 구현이나 패치는 하지 말고 bounded insurance survey만 수행하라.

이번 오더의 primary baseline은 아래 내부 조사본이다. 이것을 참고하되, 추종하지 말고 corroborate 또는 falsify 하라.

- `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-survey.md`
- `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-deep-dive-evidence.json`

목표:
work `0_1` Stage 4 EP10-15의 residual gate / observability seam 두 개를 보험용으로 재조사하라.

조사 seam:
1. persisted sink에 `verdict_layers`가 보이지 않는 이유
2. EP10 / EP13 / EP14 / EP15의 residual `npc_drift` / `flashback` strong-advisory가 실제 narrative violation인지, authority-precision false positive인지, local-fix contract 문제인지, sink taxonomy/observability loss인지

필수 질문:
1. `verdict_layers` 부재는 stale runtime session 설명이 최우선인가? 아니라면 무엇이 더 강한가?
2. code omission / serializer stripping / stale process / mixed-session artifact 중 어느 설명이 가장 맞는가?
3. EP13-14 `npc_drift(position/role)`는 artifact truth와 충돌하는가, 아니면 composite role phrasing을 과벌하는가?
4. EP15 `npc_drift(relation_to_protag)`는 실제 narrative pressure로 남는가?
5. `flashback` family는 persisted sink에서 실제 issue detail을 보존하는가?
6. `TruthGate`의 `role_at_intro` path가 EP10-15 evidence에 직접 개입했는가, 아니면 latent risk에 그치는가?
7. retry-lane UI logs는 `attempt_key` 없이 operator diagnosis에 충분한가?

필수 분류 프레임:
- artifact truth
- metadata truth
- narrative truth

특히 아래는 반드시 분리해서 적어라:
- true narrative violation
- authority-precision false positive
- missing local fix contract
- taxonomy / sink observability loss

필수 조사 대상:
- code
  - `modules/core/stage4_interview_round.py`
  - `modules/core/db_manager.py`
  - `modules/core/world_state.py`
  - `modules/core/npc_drift_advisor.py`
  - `modules/core/stage4_director_runtime.py`
  - `modules/core/flashback_verifier.py`
  - `modules/core/truth_gate.py`
- DB / logs
  - `projects/0_1/project_data.db`
  - `projects/0_1/logs/session/decisions.jsonl`
  - `projects/0_1/logs/session/ui_events.jsonl`
  - `projects/0_1/logs/episode_production.jsonl`
  - `projects/0_1/logs/runtime_audit.jsonl`
  - `attempt_raw_rationale` table
- artifact truth
  - `projects/0_1/plans/blueprints/blueprint_0013.txt`
  - `projects/0_1/plans/blueprints/blueprint_0014.txt`
  - `projects/0_1/plans/blueprints/blueprint_0015.txt`
  - `projects/0_1/drafts/ep_0010.txt`
  - `projects/0_1/drafts/ep_0013.txt`
  - `projects/0_1/drafts/ep_0014.txt`
  - `projects/0_1/drafts/ep_0015.txt`

산출물:
- canonical survey doc
  - `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-opus-survey.md`
- raw evidence json
  - `docs/2026-03-31/0_1-stage4-ep10-15-residual-gate-observability-opus-evidence.json`

문서 요구사항:
- answer-first
- hard conclusions / medium-confidence conclusions / open questions 분리
- episode-by-attempt classification matrix 포함
- `verdict_layers` 부재 설명에 대해 반증 시도 섹션 포함
- file:line 근거와 DB/log query 예시 포함
- `artifact truth / metadata truth / narrative truth` 3층 분리
- 내부 baseline과 일치한 점 / 불일치한 점을 별도 섹션으로 분리
- 3-pass audit 후 confidence 95% 이상일 때만 final save
- confidence 95% 미만이면 uncertainty를 명시하고 final save 금지

이번 오더에서 하지 말 것:
- 코드 패치
- execution SSOT 생성
- `docs/temp/` mirror 생성
- active temp roadmap 수정
- resolved 선언
- stale session 가설을 fresh rerun 없이 확정 사실로 격상

판정 원칙:
- old docs보다 live code / DB / logs / artifacts가 우선
- 콘솔 렌더링은 navigational only
- 인코딩 판단은 UTF-8 byte-level read-back 기준
- primary baseline 문서는 참고 자료일 뿐 authority가 아니다
```
