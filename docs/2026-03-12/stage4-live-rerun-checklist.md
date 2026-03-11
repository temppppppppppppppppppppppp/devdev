# Stage 4 Live Rerun Checklist

작성일: 2026-03-12

상위 마스터 문서: `docs/2026-03-12/pass-with-fix-master-roadmap.md`  
문서 역할: 마스터 로드맵의 `Phase 7 limited rerun`과 `Phase 8 full live rerun` 운영 체크리스트

## 사용 전제

- 이 문서는 `계약 고정`, `structural inplace 설계/구현`, `최소 계측`, `오프라인 회귀/골든 검증`, `logging/analytics 체계 보완`이 선행된 뒤 사용한다.
- `episode_production.jsonl`, `director_selections`, `stage_attempts`, `pass_rate_monitor.json`의 의미는 마스터 문서의 sink 역할 정의를 따른다.

## 목적

이 문서는 현재 worktree에서 source-level로 닫아 둔 P0/P1 변경을 실제 live rerun에서 확인하기 위한 운영 체크리스트다.

이번 체크리스트의 핵심 목표는 아래 3가지다.

1. `stage4_complete`가 진짜 성공 완주에서만 기록되는지 확인
2. `episode_production.jsonl`, `pass_rate_monitor.json`, `director_selections`, `stage_attempts`의 의미가 서로 어긋나지 않는지 확인
3. Stage 4 hardening 이후 rerun이 기존 성공 기준선(`00_test_01`, `00_test_02`)과 같은 방향으로 닫히는지 확인

## 고정 전제

- scope는 우선 `1 arc / ep_0001~ep_0004` 기준으로 본다.
- completion 판정 source priority는 아래 순서를 따른다.
  1. `drafts/` 실파일
  2. `runtime_audit_summary.json`
  3. `stage_attempts`
  4. `pass_rate_monitor.json`
  5. `episode_production.jsonl`
- `episode_production.jsonl`은 round trace와 reasoning split 확인용이지, 단독 completion source가 아니다.
- 기존 프로젝트를 reset 후 재사용한 tree는 baseline로 쓰지 않는다. 새 live rerun은 새 project name으로 분리한다.

## 성공 기준선

현재 확인된 성공 reference는 아래 2개다.

| project | drafts | runtime_audit tag | stage_attempts total | stage4 attempts | director_selections total | director_selections stage4 |
|---|---:|---|---:|---:|---:|---:|
| `00_test_01` | 4 | `stage4_complete` | 11 | 6 | 7 | 6 |
| `00_test_02` | 4 | `stage4_complete` | 10 | 5 | 6 | 5 |

따라서 같은 scope의 healthy rerun은 아래처럼 읽는다.

- hard gate: draft `4/4`, `runtime_audit_summary.tag=stage4_complete`
- healthy band: `stage4_attempts=5~6`, `director_selections(stage4)=5~6`
- investigate: `stage4_attempts>=7` 또는 `director_selections(stage4)>=7`
- fail-closed: `draft_count<4` 또는 `runtime_audit_summary.tag!=stage4_complete`

## 1. 실행 전

### 1.1 Run Metadata 고정

- [ ] 새 project name을 정한다. 예: `00_test_04`
- [ ] profile / treatment / model tier를 문서에 적는다.
- [ ] scope를 적는다. 예: `1 arc / ep_0001~ep_0004`
- [ ] 시작 시각을 적는다.
- [ ] 현재 worktree snapshot을 남긴다.

권장 기록:

```powershell
git rev-parse HEAD
git status --short
```

### 1.2 최소 회귀 테스트 재확인

- [ ] 아래 테스트 묶음이 green인지 확인한다.

```powershell
pytest -q tests/test_stage4_orchestrator.py tests/test_stage4_interview_round.py
pytest -q tests/test_v75c_contradiction_firewall.py tests/test_chief_writer.py tests/test_cost_tracking.py tests/integration/test_patch_wiring.py
```

### 1.3 실행/보존 규칙

- [ ] rerun은 새 project에 수행한다.
- [ ] 실패/중단 시 project 폴더를 삭제하지 않는다.
- [ ] 중단해도 `runtime_audit_summary.json`, `episode_production.jsonl`, `pass_rate_monitor.json`, `project_data.db`, session log를 그대로 보존한다.
- [ ] rerun 도중 인간 개입 또는 `KeyboardInterrupt`가 있었다면 문서에 명시한다.

## 2. 실행 중

### 2.1 필수 관찰 포인트

- [ ] Stage 4가 실제로 ep1~ep4를 생산 중인지 콘솔 또는 session log로 확인한다.
- [ ] REJECT가 나오면 다음 round가 patch인지 full rerun인지 같이 본다.
- [ ] run이 조기 종료되면 종료 이유를 즉시 적는다.

### 2.2 즉시 기록할 이벤트

- [ ] 첫 Stage 4 REJECT episode / round / score
- [ ] `score=44` firewall REJECT 발생 여부
- [ ] `post-select conflict` 발생 여부
- [ ] `PASS_WITH_FIX` 발생 episode / round
- [ ] 수동 중단 여부

## 3. 실행 후 Hard Gate

### 3.1 Completion

- [ ] `drafts/ep_0001.txt` ~ `ep_0004.txt`가 모두 존재한다.
- [ ] `runtime_audit_summary.tag`가 실제 성공 완주면 `stage4_complete`다.
- [ ] 실패/중단/인간 검토 필요 run이면 `runtime_audit_summary.tag`가 `stage4_complete`여서는 안 된다.

즉, 아래 둘 중 하나만 허용한다.

- 성공 run: `draft_count=4` and `tag=stage4_complete`
- 비성공 run: `draft_count<4` and `tag!=stage4_complete`

아래 조합은 correctness fail로 본다.

- `draft_count<4`인데 `tag=stage4_complete`
- run이 중단됐는데 `tag=stage4_complete`
- `draft_count=4`인데 `tag=stage3_complete` 또는 `missing`

### 3.2 DB / 로그 정합성

- [ ] `stage_attempts(stage=4)` 수가 `episode_production.jsonl`의 stage4 round trace와 대체로 맞는다.
- [ ] `director_selections(stage=4)` 수가 `stage4_attempts`와 1:1 또는 근사 1:1로 맞는다.
- [ ] `pass_rate_monitor.records`의 stage4 entry 수가 `stage4_attempts`와 맞는다.
- [ ] session interrupt가 있었다면 `stage_attempts`와 `episode_production` 간 시차는 허용하되, 이를 문서에 명시한다.

### 3.3 Observability 필드

- [ ] `episode_production.jsonl` stage4 row에 아래 필드가 실제 저장된다.
  - `duration_ms`
  - `round_total_calls`
  - `round_total_tokens`
  - `round_total_cost_usd`
  - `flags.strategy_budget`
  - `flags.strategy_count`
  - `flags.reject_bucket`
  - `selection_reason`
  - `verdict_reason`
- [ ] `pass_rate_monitor.json` stage4 row에 `duration_ms`와 `token_cost`가 0 또는 누락이 아닌 값으로 저장된다.
- [ ] `director_selections`에 `selection_reason`, `verdict_reason`, `pre_firewall_score`, `firewall_triggered`, `firewall_reason`이 필요 시 저장된다.

## 4. 조건부 시나리오 검증

이 섹션은 해당 이벤트가 실제 rerun에서 발생했을 때만 체크한다.

### 4.1 Firewall REJECT (`score=44`)

- [ ] `director_selections.stage=4` row에서 `score=44`와 함께 `pre_firewall_score`가 보존된다.
- [ ] `firewall_triggered=1` 또는 `firewall_reason`이 비어 있지 않다.
- [ ] `selection_reason`과 `verdict_reason`이 같은 문장으로 뭉개지지 않고 분리되어 있다.
- [ ] 다음 retry routing이 `patch/inplace` 쪽으로 갔는지 확인한다.

### 4.2 Post-Select Conflict

- [ ] `episode_production.jsonl` 또는 feedback에서 `[Continuity Conflict]` 흔적을 확인한다.
- [ ] 해당 REJECT의 `reject_bucket`가 `post_select_conflict`로 남는다.
- [ ] 다음 retry가 full regenerate보다 `patch_with_feedback(single-strategy)` 우선으로 갔는지 확인한다.

### 4.3 PASS_WITH_FIX

- [ ] `verdict=PASS_WITH_FIX` row가 있어도 최종 completion 판정은 `drafts/`, `runtime_audit_summary`, `stage_attempts` 기준으로 다시 확인한다.
- [ ] `episode_production.jsonl`의 round verdict만 보고 성공으로 단정하지 않는다.

### 4.4 Interrupted Session

- [ ] `KeyboardInterrupt` 또는 수동 종료 시 `runtime_audit_summary.tag`가 `stage4_complete`가 아니다.
- [ ] partial draft / partial round trace / partial DB row가 남아도 삭제하지 않고 그대로 보존한다.
- [ ] interrupted run은 별도 문단으로 분리해 기록한다.

## 5. 즉시 확인용 명령

### 5.1 Summary / Draft Count

```powershell
Get-Content projects/<PROJECT>/logs/runtime_audit_summary.json
Get-ChildItem projects/<PROJECT>/drafts/ep_*.txt | Select-Object Name,Length
```

### 5.2 pass_rate_monitor 구조 확인

```powershell
@'
import json, pathlib
name = "<PROJECT>"
path = pathlib.Path("projects") / name / "logs" / "pass_rate_monitor.json"
data = json.loads(path.read_text(encoding="utf-8"))
records = data.get("records", [])
s4 = [r for r in records if r.get("stage") == 4]
print("records_total", len(records))
print("records_stage4", len(s4))
for row in s4:
    print({
        "episode": row.get("episode"),
        "attempt_num": row.get("attempt_num"),
        "success": row.get("success"),
        "duration_ms": row.get("duration_ms"),
        "token_cost": row.get("token_cost"),
        "reject_reason": row.get("reject_reason"),
        "prev_score": row.get("prev_score"),
    })
'@ | python -
```

### 5.3 DB counts / 핵심 row 확인

```powershell
@'
import pathlib, sqlite3
name = "<PROJECT>"
db = pathlib.Path("projects") / name / "project_data.db"
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
cur = con.cursor()
print("stage_attempts_total", cur.execute("select count(*) c from stage_attempts").fetchone()["c"])
print("stage4_attempts", cur.execute("select count(*) c from stage_attempts where stage=4").fetchone()["c"])
print("director_selections_total", cur.execute("select count(*) c from director_selections").fetchone()["c"])
print("director_selections_stage4", cur.execute("select count(*) c from director_selections where stage=4").fetchone()["c"])
print()
print("stage4_attempts_rows")
for row in cur.execute("""
    select id, ep_num, attempt_num, verdict, score, duration_ms, failure_category, reject_reason, fix_scope
    from stage_attempts
    where stage=4
    order by id
"""):
    print(dict(row))
print()
print("director_stage4_rows")
for row in cur.execute("""
    select id, ep_num, round_num, verdict, score, selected_strategy,
           selection_reason, verdict_reason, pre_firewall_score,
           firewall_triggered, firewall_reason
    from director_selections
    where stage=4
    order by id
"""):
    print(dict(row))
'@ | python -
```

### 5.4 episode_production 필드 확인

```powershell
Get-Content projects/<PROJECT>/logs/episode_production.jsonl -TotalCount 20
```

확인 포인트:

- `round_total_calls`
- `round_total_tokens`
- `round_total_cost_usd`
- `reason`
- `selection_reason`
- `verdict_reason`
- `flags.strategy_budget`
- `flags.strategy_count`
- `flags.reject_bucket`

## 6. 최종 판정 템플릿

아래 블록을 그대로 복붙해서 채우면 된다.

```text
Project:
Date:
Scope:
Profile / Treatment:
Git HEAD:

Outcome:
- success / fail-closed / interrupted

Hard Gate:
- draft_count:
- runtime_audit_summary.tag:
- completion verdict:

Counts:
- stage_attempts_total:
- stage4_attempts:
- director_selections_total:
- director_selections_stage4:
- pass_rate_monitor stage4 records:

Observability:
- episode_production per-round metrics present: yes/no
- pass_rate_monitor duration_ms/token_cost present: yes/no
- selection_reason / verdict_reason split preserved: yes/no

Conditional Paths:
- firewall REJECT seen: yes/no
- post_select_conflict seen: yes/no
- PASS_WITH_FIX seen: yes/no
- interrupted session: yes/no

Notes:
- acceptable drift:
- correctness issue:
- follow-up:
```

## 결론 규칙

- 이 체크리스트의 목적은 "좋아 보이는 콘솔 출력"이 아니라 "completion semantics + observability semantics + retry routing semantics"를 실제 run에서 재검증하는 것이다.
- rerun 결과가 성공 기준선보다 조금 느리거나 retry가 1회 더 많아도, `draft_count=4`와 `tag=stage4_complete`가 닫히고 observability 필드가 정상이면 우선 `acceptable drift`로 본다.
- 반대로 콘솔에 성공처럼 보여도 `draft_count`, `runtime_audit_summary.tag`, `stage_attempts`가 안 맞으면 fail로 기록한다.
