# GCP IAM 5-Arc Live Run Handoff Current

Date: 2026-04-27
Snapshot Time: 2026-04-27 10:20 KST
Updated: 2026-04-27 10:35 KST
Status: stopped provisional handoff

## Purpose

This document is a compact handoff for continuing or inspecting the current GCP/Vertex 5-arc validation work from another PC.

It is not a final post-run audit. The live run was stopped by explicit operator request before terminal 5-arc completion, so every run conclusion here remains provisional until a later terminal run and post-run 3-pass merge audit are completed.

## Workspace Anchor

- Workspace: `C:\Users\PC\Desktop\글도비`
- Branch: `run/gcp-iam-5arc-clean-proof`
- HEAD at snapshot: `de4dc335`
- Main context doc: `docs/2026-04-27/gcp-iam-5arc-sleep-ops-context.md`
- This handoff: `docs/2026-04-27/gcp-iam-5arc-live-run-handoff-current.md`
- Target project: `projects/01_골든카나리아`
- Target DB: `projects/01_골든카나리아/project_data.db`
- Active log: `projects/01_골든카나리아/logs/session_20260427_070604.log`
- Manifest: `projects/01_골든카나리아/logs/auto_frontier_lag_harness_manifest.json`

## Live Run

- Run id: `20260427_070602_68e560f5d2`
- Stage attempt session id: `20260427_070604`
- Parent process PID at snapshot: `13692`
- Worker process PID at snapshot: `9616`
- Manifest status at snapshot: `frontier_running`
- Return code at snapshot: `None`
- Completed at snapshot: `None`
- Failure digest at snapshot: `None`
- Stop update: parent PID `13692` and worker PID `9616` were explicitly stopped after the snapshot before PR/main sync.
- Stop verification: no matching `run_auto_frontier_lag_harness.py` process remained after termination.
- Manifest caveat: the manifest may still say `frontier_running` because the process was force-stopped before normal harness cleanup.

Run command:

```powershell
python scripts/run_auto_frontier_lag_harness.py run `
  --arc-count 5 `
  --target-project 01_골든카나리아 `
  --reuse-existing-project `
  --reuse-reset-after-ep 16 `
  --trigger gcp_iam_vertex_global_31pro_strict_5arc_rerun_after_vehicle_intrusion_guard_patch `
  --poll-interval-seconds 60 `
  --operational-attempt-cap 10 `
  --max-runtime-seconds 21600 `
  --stage3-failure-policy strict
```

The live run has already been stopped by explicit operator instruction. Do not restart it during PR/main sync.

## Current Progress At Snapshot

Stage3:

- Current live session generated/validated Stage3 `ep16` through `ep27`.
- All 12 Stage3 episodes in this session passed on the first recorded attempt.
- Verdict distribution in current session:
  - `ep16`: `PASS`
  - `ep17`: `PASS`
  - `ep18`: `PASS`
  - `ep19`: `PASS_WITH_WARNING`
  - `ep20`: `PASS_WITH_WARNING`
  - `ep21`: `PASS_WITH_WARNING`
  - `ep22`: `PASS_WITH_WARNING`
  - `ep23`: `PASS`
  - `ep24`: `PASS_WITH_WARNING`
  - `ep25`: `PASS`
  - `ep26`: `PASS`
  - `ep27`: `PASS`

Stage4:

- Manuscripts persisted at snapshot: `ep1` through `ep8`.
- Current live Stage4 status after stop: `ep9` had two `POST_SELECT_CONFLICT` rejects and no PASS persisted.
- Current live session Stage4 attempt rows:
  - `ep4`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep5`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep6`: `REJECT:LOGIC_ERROR | REJECT:CONSTRAINT_VIOLATION | REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep7`: `REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep8`: `REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT | PASS`
  - `ep9`: `REJECT:POST_SELECT_CONFLICT | REJECT:POST_SELECT_CONFLICT`

Interpretation:

- The run is not clean-pass-only.
- The important improvement is recovery behavior: Stage4 conflicts are being caught by Director/post-select gates and recovering in 2 to 4 attempts so far.
- The recurrent current bottleneck is downstream continuity/history drift, especially repeated carryover mistakes such as institution naming and duplicated continuation beats.

## GCP / Cache / Memory Evidence

At snapshot:

- Active model in current session: `vertexai:gemini-3.1-pro-preview`
- Current-session LLM calls since 07:06: `410`
- Current-session input tokens since 07:06: `13,534,909`
- Current-session output tokens since 07:06: `1,319,089`
- Current-session cached tokens since 07:06: `8,020,575`
- Total `context_cache_attempts` rows in target DB: `207`
- Log shows repeated Vertex context cache calls:
  - `https://aiplatform.googleapis.com/v1beta1/projects/gen-lang-client-0159412471/locations/global/cachedContents`
- Log shows session/vector memory retrieval with `VecMem ... fallback=false`.

Interpretation:

- GCP/Vertex route is active.
- Context caching is materially active.
- Session/vector memory retrieval is materially active.
- This does not prove final quality success yet; it proves the memory/cache transport is operating during the live run.

## Important Mid-Run Findings

- Vehicle chase / unauthorized physical intrusion did not recur after the tactical guard patch in the current live run.
- The vehicle guard is still a firewall-style mitigation, not the deeper root fix.
- Root improvement candidate for later: genre-align Stage3 and Stage4 ensemble strategies so investment / business-power works do not interpret "action" or "tension" as physical chase, violence, or thriller intrusion.
- The active Stage4 bottleneck is now continuity carryover, not process death.
- CoVe LLM runtime failures appeared after some PASSes, but Stage4 preserved Director PASS. This should be reviewed post-run, not patched mid-run unless it becomes terminal.

## Comparison Snapshot

Representative earlier data:

- 2026-04-03 Stage4 canary:
  - Stage4 `ep2`: 9 attempts before PASS.
  - Stage4 `ep3`: 3 attempts before PASS in one run; 5 REJECTs and no PASS in another rerun.
- 2026-04-20 / 2026-04-21 midline:
  - Stage4 `ep3`: 8 attempts before PASS.
  - Stage4 `ep4`: 4 REJECTs and no PASS in that DB snapshot.
- 2026-04-27 current live run:
  - Stage4 `ep4`: 2 attempts before PASS.
  - Stage4 `ep5`: 2 attempts before PASS.
  - Stage4 `ep6`: 4 attempts before PASS.
  - Stage4 `ep7`: 2 attempts before PASS.
  - Stage4 `ep8`: 3 attempts before PASS.

Provisional conclusion:

- Current system is not yet a no-error clean run.
- Current system appears much better at bounded recovery than early April runs.
- Current cache/session-memory activation is much stronger and measurable in DB/token telemetry.
- Because this run was manually stopped, it must not be reported as a completed 5-arc proof.

## Dirty Workspace Warning

At snapshot, the workspace is not clean.

Notable dirty state includes production code, tests, docs, and live/generated project artifacts. A different PC will not automatically receive local dirty changes unless they are committed and pushed or otherwise copied.

Do not run destructive git cleanup commands. Do not reset, checkout, or delete generated project folders while preserving this stopped-run evidence.

## Safe Read-Only Status Checks

Process check:

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*run_auto_frontier_lag_harness.py*' -and $_.CommandLine -like '*01_골든카나리아*' } |
  Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine |
  Format-List
```

DB summary:

```powershell
@'
import json, sqlite3, datetime
from pathlib import Path
project = next(p for p in Path('projects').iterdir() if p.is_dir() and p.name.startswith('01_') and (p/'project_data.db').exists())
log = project/'logs'/'session_20260427_070604.log'
print('now', datetime.datetime.now().isoformat(timespec='seconds'))
if log.exists():
    print('log_mtime', datetime.datetime.fromtimestamp(log.stat().st_mtime).isoformat(timespec='seconds'), 'bytes', log.stat().st_size)
manifest = project/'logs'/'auto_frontier_lag_harness_manifest.json'
if manifest.exists():
    data=json.loads(manifest.read_text(encoding='utf-8'))
    print('manifest', {k:data.get(k) for k in ['status','returncode','completed_at','failure_digest_path','run_id']})
con=sqlite3.connect(project/'project_data.db')
cur=con.cursor()
print('blueprints', cur.execute('SELECT COUNT(*), MIN(ep_num), MAX(ep_num) FROM blueprints').fetchall())
print('manuscripts', cur.execute('SELECT COUNT(*), MIN(ep_num), MAX(ep_num) FROM manuscripts').fetchall())
print('stage4_current', cur.execute("SELECT ep_num, COUNT(*), GROUP_CONCAT(verdict || COALESCE(':'||failure_category,''), ' | ') FROM stage_attempts WHERE stage=4 AND session_id='20260427_070604' GROUP BY ep_num ORDER BY ep_num").fetchall())
print('llm_current', cur.execute("SELECT model, COUNT(*), SUM(COALESCE(input_tokens,0)), SUM(COALESCE(output_tokens,0)), SUM(COALESCE(cached_tokens,0)), SUM(COALESCE(total_cost_usd,0)) FROM llm_calls WHERE ts >= '2026-04-27T07:06:00' GROUP BY model ORDER BY COUNT(*) DESC").fetchall())
print('cache_attempts', cur.execute('SELECT COUNT(*) FROM context_cache_attempts').fetchall())
con.close()
'@ | python -
```

Log tail:

```powershell
@'
from pathlib import Path
log = next(Path('projects').glob('01_*/logs/session_20260427_070604.log'), None)
if not log:
    print('log_missing')
else:
    lines = log.read_text(encoding='utf-8').splitlines()
    pats = ('제9화','제10화','Round','PASS','REJECT','FAILED','POST_SELECT_CONFLICT','CONSTRAINT_VIOLATION','LOGIC_ERROR','생산 완료','작업 완료','Traceback','Exception','종료','cachedContents','VecMem')
    for line in [x for x in lines if any(p in x for p in pats)][-120:]:
        print(line)
'@ | python -
```

## If Continuing On Another PC

1. Treat this file and `docs/2026-04-27/gcp-iam-5arc-sleep-ops-context.md` as the first read.
2. Confirm the branch and commit state before starting any code work.
3. The live run on this PC has been stopped; if restarting later, do not start a second writer against the same `projects/01_골든카나리아` folder.
4. If the other PC is only reviewing, use DB/log read-only commands.
5. If the other PC needs exact current code and docs, first commit/push or otherwise transfer the dirty workspace intentionally. Do not assume `de4dc335` contains all local changes.

## 3-Pass Save Audit

Pass 1 - Evidence coverage:

- Captures process status, manifest status, DB state, LLM/cache metrics, and latest log-derived Stage4 progress.
- Explicitly labels the document as provisional because the live run was stopped before terminal proof.

Pass 2 - Risk and authority check:

- Does not claim final success.
- Does not weaken Director/post-select authority.
- Does not treat Python advisory as quality judge.
- Records process termination only because it was explicitly requested before PR/main sync.

Pass 3 - Handoff usability check:

- Includes paths, run id, process ids, current branch, dirty workspace warning, read-only status commands, and another-PC caveats.
- Confidence for provisional handoff accuracy at snapshot: 95%.
