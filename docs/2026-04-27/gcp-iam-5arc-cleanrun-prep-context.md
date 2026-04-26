# GCP IAM 5-Arc Cleanrun Prep Context

Date: 2026-04-27
Status: prep-only; live run not started
Branch: `codex/gcp-iam-cleanrun-proof`

## Operator Intent
- Do not start the 5-arc run yet.
- Prepare the workspace so the next run can be a clean GCP Vertex IAM proof.
- If a future run fails, investigate first, run adversarial 3-pass review, patch through the formal system-track route, then rerun.

## Current Findings
- `0_temp.txt` now matches Stage 0 setup for `projects/01_골든카나리아`.
- Verified Stage 0 artifacts by file/DB read-back:
  - `project_data.db` exists.
  - DB anchors include `bible`, `style_guide`, `genre_info`, `emotion_history`.
  - `MasterBible.plot_roadmap` count is 60.
  - `stage0_output/style_guide.json` has `analysis_version=v2`, `genre=investment`, 15 exemplar passages, and 10 anti-AI patterns.
  - `config/work_guard.yaml` includes `golden_canary_deepclone_probe_a_fullblock_v1` and `family: blockguide`.
- `projects/01_골든카나리아` is a clean pre-run target: `stage_attempts=0`, `context_cache_attempts=0`, `llm_calls=0`, `cost_log=0`, `blueprints=0`, `manuscripts=0`.
- A previous run attempt on `projects/0000_골든카나리아` was stopped before accepting it as proof because logs showed Vertex API-key auth could override project/location credentials. That older project is not the current clean target.

## Prep Patch
- `modules/core/providers/vertex_provider.py` now lets `GEULDOBI_VERTEX_AUTH_MODE` override provider config `auth_mode`.
- This aligns `VertexAIProvider` with `build_google_genai_client`.
- With `GEULDOBI_VERTEX_AUTH_MODE=project_credentials`, `VERTEX_API_KEY` no longer silently wins when provider config is `auth_mode: auto`.

## Validation Already Run
- `python -m pytest tests/test_llm_router.py -q`
  - Result: 51 passed.
- `python scripts/check_utf8_hygiene.py modules/core/providers/vertex_provider.py tests/test_llm_router.py 0_temp.txt docs/2026-04-27/gcp-iam-5arc-cleanrun-prep-context.md`
  - Result: pass.
- Pre-run raw baseline:
  - `docs/2026-04-27/gcp-iam-5arc-cleanrun-prerun-baseline.json`

## Future Run Candidate
Use the freshly prepared target project `01_골든카나리아`.

Suggested command:

```powershell
python scripts/run_auto_frontier_lag_harness.py run `
  --arc-count 5 `
  --target-project "01_골든카나리아" `
  --reuse-existing-project `
  --trigger gcp_iam_vertex_5arc_clean_proof `
  --operational-attempt-cap 10 `
  --max-runtime-seconds 21600 `
  --stage3-failure-policy strict
```

## 3-Pass Prep Audit
- Pass 1 authority check: GCP/IAM auth mode must be controlled by `GEULDOBI_VERTEX_AUTH_MODE`, not by implicit API-key presence.
- Pass 2 contamination check: `01_골든카나리아` has no LLM calls, stage attempts, context cache attempts, blueprints, or manuscripts at the saved baseline.
- Pass 3 execution gate: no live run is active now; next run should start only after the operator explicitly permits execution.
