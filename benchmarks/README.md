# Benchmark Archive

`benchmarks/` keeps experiment records separate from live `projects/` workspaces.

Each archived run is stored under `benchmarks/<project>/<run_id>/` and includes:

- `snapshots/project_data.db`
- selected runtime logs copied from the source project
- `manifest.json`
- `stage_metrics.csv`

`benchmark_index.csv` is the quick comparison surface across runs. Snapshot folders are ignored by git by default so large DB copies do not get staged accidentally. The index therefore marks archive backing evidence as `local_ignored_snapshot` / `local_only_non_reproducible` unless a separate export or tracked evidence bundle is created.

Example:

```bash
python scripts/archive_benchmark_record.py --project "골든 카나리아" --lane stage4-supervised --target-ep 5 --status interrupted --notes "ep4 replay blocker"
```

Direct supervised launchers now auto-archive on completion:

```bash
python scripts/run_stage4_direct_supervised.py run --project "골든 카나리아" --target-ep 5
python scripts/run_stage4_direct_supervised_guarded.py run --project "골든 카나리아" --target-ep 10 --max-attempts 5 --poll-interval-seconds 300
python scripts/run_stage3_direct_supervised.py run --project "골든 카나리아" --target-ep 16 --operational-attempt-cap 5
python scripts/run_stage2_direct_supervised.py run --project "골든 카나리아" --target-total-arcs 5
```

The guarded Stage 4 wrapper delegates execution to the normal direct runner, polls `stage_attempts` every fixed interval, and archives monitor-forced stops as `operational_failure`.

Canary runners also auto-archive for `run` and `full` commands only:

```bash
python scripts/run_stage4_canary.py run --project "canary_name" --target-ep 4
python scripts/run_stage34_canary.py full --source-project "골든 카나리아" --target-project "probe_name" --from-ep 4 --target-ep 4
```

Current archive scope is intentionally compact:

- copy the DB snapshot
- copy core logs and `logs/metrics/` when present
- summarize Stage 2/3 from `logs/pass_rate_monitor.json`
- summarize Stage 4 from `logs/episode_production.jsonl`

Artifacts such as full manuscript or blueprint trees are not copied by default.
