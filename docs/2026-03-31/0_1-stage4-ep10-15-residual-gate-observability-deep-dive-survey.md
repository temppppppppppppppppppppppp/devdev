# 0_1 Stage4 EP10-15 Residual Gate Observability Deep Dive Survey

- Date: 2026-03-31
- Scope: work `0_1`, Stage 4, EP10-15 residual gate and observability seams after the EP9 remediation wave
- Baselines:
  - `docs/2026-03-31/0_1-stage4-ep1-15-db-log-bounded-audit.md`
  - `docs/2026-03-30/0_1-stage4-ep9-remediation-postpatch-bounded-survey.md`
  - `docs/2026-03-31/0_1-stage4-cw-first-pass-false-miss-remediation-postpatch-bounded-survey.md`
- Method: live code + DB + JSONL + artifact truth, then 3-pass audit
- Confidence: 96%

## Answer First

이번 deep dive에서 닫힌 핵심은 네 가지다.

1. persisted sink에 `verdict_layers`가 안 보이는 이유는 DB serializer stripping이 아니라 `stale long-running runtime session`일 가능성이 가장 높다.
2. EP13-14의 `npc_drift(position/role)`는 실제 서사 위반보다 `authority precision` 문제에 가깝다.
3. EP15의 `npc_drift(relation_to_protag)`는 EP13-14와 달리 실제 서사 압력을 제대로 짚은 경고일 가능성이 높다.
4. `flashback` family는 현재 operator-facing sink에서 너무 거칠게 평평해져서, literal flashback contamination인지 일반 continuity/time-pressure인지 분간이 안 된다.

## Truth Layers

### Artifact Truth

- 최종 PASS 원고는 살아 있다.
- `projects/0_1/drafts/ep_0013.txt:11`은 박성호를 `한미증권 파생상품 데스크 소속으로 SW인베스트먼트 전담 PB`로 동시에 적는다.
- `projects/0_1/drafts/ep_0014.txt:7`도 `한미증권 소속 SW인베스트먼트 전담 PB`로 적는다.
- `projects/0_1/drafts/ep_0015.txt:43`, `:91`, `:107`은 박성호의 `경외감/집착/맹목적 복종심`을 명시한다.

### Metadata Truth

- `modules/core/stage4_interview_round.py:2162-2215`는 on-disk code상 `gate_semantics.verdict_layers`를 생성한다.
- 같은 파일 `:6002-6008`, `:6110-6143`, `:6180-6222`는 그 payload를 persistence/reporting sink로 다시 올리도록 되어 있다.
- 그런데 DB의 `stage_attempts`와 `director_selections`에는 EP1-15 범위에서 `verdict_layers`가 `0`건이다.
- `projects/0_1/logs/session/decisions.jsonl`와 `projects/0_1/logs/episode_production.jsonl`에도 `verdict_layers` 문자열 hit가 없다.

### Narrative Truth

- EP13-14의 문제는 `박성호가 정말 다른 사람처럼 변했는가`보다 `박성호의 복합 역할을 단일 라벨로만 읽었는가` 쪽이다.
- EP15의 문제는 반대로, rejected candidate가 실제로 박성호를 너무 평범한 subordinate/witness처럼 눌러쓴 흔적이 있다.

## Hard Conclusions

### 1. `verdict_layers` persisted gap은 stale runtime session 설명이 가장 강하다

- On-disk code는 이미 `verdict_layers`를 만든다.
  - `modules/core/stage4_interview_round.py:2168`
  - `modules/core/stage4_interview_round.py:2185-2186`
  - `modules/core/stage4_interview_round.py:6002-6008`
  - `modules/core/stage4_interview_round.py:6110-6143`
  - `modules/core/stage4_interview_round.py:6180-6222`
- DB read/report path는 해당 field를 strip하지 않는다.
  - `modules/core/db_manager.py:2858-2887`
- EP10-15 Stage 4 rows는 전부 같은 live session `20260330_231345`에서 생성됐다.
- `modules/core/stage4_interview_round.py` 파일 mtime은 `2026-03-31 01:05:56`이다.
- 그런데 그 이후 같은 session에서 생성된 Stage 4 rows가 `14`건 더 있고, 그 `14/14`가 모두 `verdict_layers` 없이 저장됐다.
- 즉, 코드 파일은 바뀌었지만 실행 프로세스는 그 이전 메모리 이미지를 계속 사용한 것으로 보는 게 가장 일관적이다.

판정:

- `broken serializer`보다는 `stale in-memory runtime` 설명이 우세하다.
- 이 결론을 runtime truth로 확정하려면 process restart 후 fresh rerun이 필요하다.

### 2. EP13-14 `npc_drift(position/role)`는 authority-precision false positive가 주류다

- advisory raw payload는 박성호의 expected를 `SW인베스트먼트 전담 PB`로 고정한다.
- rejected candidate에서 걸린 문구는
  - `여의도 한미증권 본사 파생상품 데스크 소속`
  - `여의도 한미증권의 베테랑 PB`
  - `파생상품 데스크에서 근무`
  같은 composite role/desk affiliation 표현이다.
- 그런데 blueprint와 최종 PASS artifact를 같이 보면 이건 거짓이 아니라 부분 truth다.
  - `projects/0_1/plans/blueprints/blueprint_0013.txt:7`
  - `projects/0_1/drafts/ep_0013.txt:11`
  - `projects/0_1/drafts/ep_0014.txt:7`
- current code도 authoritative ladder를 이미 `known_attrs.position -> role -> role_at_intro` 순으로 읽는다.
  - `modules/core/world_state.py:49-65`
  - `modules/core/world_state.py:1378-1386`
  - `modules/core/npc_drift_advisor.py:104-114`

판정:

- EP13-14 role/position 경고는 `real drift`보다 `composite role phrasing over-penalty`로 보는 게 맞다.

### 3. EP15 `npc_drift(relation_to_protag)`는 true-positive narrative pressure 쪽이다

- raw advisory는 박성호의 expected를 `집착100/오해100`으로 잡고, rejected candidate를 `평범한 부하직원/목격자`처럼 묘사했다고 지적한다.
- 이건 EP13-14의 직책 표현 문제와 다르다. role label mismatch가 아니라 emotional relation pressure를 본다.
- 최종 PASS 원고는 실제로 그 압력을 복구한다.
  - `projects/0_1/drafts/ep_0015.txt:43`
  - `projects/0_1/drafts/ep_0015.txt:91`
  - `projects/0_1/drafts/ep_0015.txt:107`

판정:

- EP15 relation-to-protagonist 경고는 묶어서 false positive 처리하면 안 된다.
- EP13-14 position/role lane과 EP15 relation lane은 분리해서 다뤄야 한다.

### 4. `flashback` family는 taxonomy/observability loss가 남아 있다

- `FlashbackVerifier`는 원래 `flashback_contamination` 수준의 issue text를 만든다.
  - `modules/core/flashback_verifier.py:187-197`
- 하지만 Director runtime sink는 실제 payload detail 대신 family bit만 남긴다.
  - `modules/core/stage4_director_runtime.py:1283-1305`
- 그래서 persisted metadata에는 `triggered_by=["flashback"]`만 남고, operator는 무슨 flashback issue였는지 못 본다.
- 대표적으로 EP14 `s4:ep14:arc3:a1:20260330_231345`는 strong advisory가 `flashback`으로 비화했는데, `attempt_raw_rationale` raw payload를 보면 구조 위반과 generic continuity warning만 보이고 flashback-specific explanation은 안 남아 있다.

판정:

- 현재 `flashback`은 clean narrative category라기보다 `collapsed family label`에 가깝다.
- literal flashback contamination과 generic carryover/time continuity pressure가 sink에서 분해되지 않는다.

### 5. retry-lane observability는 `stage/ep_num`은 회복됐지만 `attempt_key`는 아직 비어 있다

- current JSONL에서는 retry-lane rows가 `stage="stage4"`와 `ep_num`을 가진다.
  - `projects/0_1/logs/session/ui_events.jsonl:3918`
  - `projects/0_1/logs/session/ui_events.jsonl:4765`
  - `projects/0_1/logs/session/ui_events.jsonl:5330`
- 하지만 EP1-15 범위 Stage 4 retry-lane rows는 `9/9`가 `attempt_key=null`이다.

판정:

- operator는 `TF-PATCH-GATE`와 `QR-7`를 개별 attempt와 안정적으로 join할 수 없다.
- stage/ep attribution patch는 half-close고, attempt identity seam은 남아 있다.

## Medium-Confidence Conclusions

- EP10과 EP14의 `flashback` 계열 일부는 literal flashback scene보다 carryover/time-sequencing pressure였을 가능성이 높다. 다만 persisted sink가 detail을 잃어서 attempt-by-attempt 확정은 못 한다.
- `projects/0_1/logs/session/decisions.jsonl`와 `projects/0_1/logs/episode_production.jsonl`의 `verdict_layers` 부재는 stale session 설명과 일치한다. 다만 fresh process restart rerun 없이는 `확정 closure`로 올릴 수 없다.
- `modules/core/truth_gate.py:358-366`의 `role_at_intro` 비교 path는 이번 EP10-15 실증에서 주원인으로 드러나진 않았지만, stale baseline seam으로는 여전히 남아 있다.

## Open Questions

1. process restart 후 known downstream override episode를 다시 돌리면 `verdict_layers`, `downstream_override_applied`, `primary_failure_layer`가 세 sink에서 모두 보이나?
2. `flashback` family의 몇 %가 실제 `flashback_contamination`이고, 몇 %가 generic continuity/carryover pressure인가?
3. `NpcDrift`가 composite role truth를 직접 normalize해야 하나, 아니면 authoritative snapshot prompt에서 multi-part role을 더 명시해야 하나?
4. retry-lane JSONL에 `attempt_key`를 넣었을 때 기존 operator diagnosis query가 얼마나 단순화되나?

## Improvement Priorities

1. process restart 후 bounded rerun으로 `verdict_layers` persistence를 runtime truth로 검증
2. `flashback` raw issue payload를 별도 sink로 보존
3. EP13-14 style composite role phrasing을 `npc_drift`에서 과벌하지 않도록 authority normalization 보강
4. EP15 `relation_to_protag` lane은 별도 gate pressure로 유지
5. retry-lane JSONL에 `attempt_key` 부여

## Query Examples

```sql
-- 1) on-disk patch 이후에도 같은 session에서 verdict_layers가 비었는지 확인
select ts, ep_num, attempt_key
from stage_attempts
where stage = 4
  and ts >= '2026-03-31T01:05:56'
order by ts;
```

```sql
-- 2) director_selections / stage_attempts에서 gate_semantics는 있는데 verdict_layers는 없는지 확인
select ep_num, attempt_key, advisory_flags
from stage_attempts
where stage = 4
  and ep_num between 10 and 15;
```

```sql
-- 3) flashback family가 실제 raw payload로 남는지 확인
select attempt_key, payload_kind, payload
from attempt_raw_rationale
where ep_num in (10, 13, 14, 15)
order by ep_num, attempt_key, payload_kind;
```

```python
# 4) retry-lane JSONL에 attempt_key가 비는지 확인
import json, pathlib
rows = []
for line in pathlib.Path("projects/0_1/logs/session/ui_events.jsonl").read_text(encoding="utf-8").splitlines():
    obj = json.loads(line)
    if obj.get("component") == "retry_lane" and obj.get("stage") == "stage4":
        rows.append(obj)
print(len(rows), sum(1 for r in rows if not r.get("attempt_key")))
```

## Final Assessment

- 이번 seam은 `새 코드가 안 써졌다`보다 `새 코드가 live process에 반영되기 전 세션이 계속 돌았다` 쪽이 더 설득력 있다.
- residual advisory도 한 덩어리가 아니다.
  - EP13-14 `npc_drift(position/role)`는 precision issue
  - EP15 `npc_drift(relation_to_protag)`는 real pressure
  - `flashback`은 observability/taxonomy loss
- 따라서 다음 patch wave가 필요하다면 `verdict_layers 재검증`, `flashback detail persistence`, `retry_lane attempt identity`, `NpcDrift composite-role normalization` 순으로 가는 게 맞다.

## Audit Record

- Pass 1: DB/log/code/artifact triangulation
- Pass 2: stale-session vs serializer-stripping 반증 시도
- Pass 3: file:line anchor, query examples, UTF-8 byte-level read-back 확인
- Final save threshold: confidence 96%, save allowed
