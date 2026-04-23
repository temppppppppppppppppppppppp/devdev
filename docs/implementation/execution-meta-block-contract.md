# Execution Meta Block Contract

Date: 2026-04-23
Status: active
Applies To: canonical execution SSOT documents that want machine-readable queue and tranche metadata

## 1. Purpose

- provide a narrow machine-readable metadata surface inside execution SSOT docs
- avoid brittle prose parsing for queue dependencies and tranche identity
- keep canonical human and machine facts in one file

## 2. Placement

Place the block:

- after the header metadata and `Side-Effect Coverage`
- before `## 1. Intent`

Use the exact section heading:

- `## 0. Execution Metadata Block`

The machine-readable payload should be the first fenced block under that heading.

## 3. Block Format

Use fenced YAML.

Example:

```yaml
execution_meta:
  schema_version: execution-meta-block-v1
  topic: authority-alignment-benchmark-operating-model-hardening
  github_issue: 5
  status: pending
  queue_role: parked_future_wave
  roadmap_rank: 1
  depends_on: []
  tranches:
    - id: authority-benchmark-proof-contract-freeze
      title: Authority and benchmark proof contract freeze
    - id: benchmark-record-comparison
      title: Benchmark-record comparison surface
  verification_commands:
    - pytest tests/test_archive_benchmark_record.py -q
    - pytest tests/test_diff_canary_summaries.py -q
```

## 4. Required Fields

- `schema_version`
  - string
  - currently must be `execution-meta-block-v1`
- `topic`
  - string
  - must match the execution SSOT topic slug
- `status`
  - string
  - allowed initial values:
    - `pending`
    - `in_progress`
    - `completed`
    - `blocked`
- `queue_role`
  - string
  - allowed values:
    - `front_active`
    - `blocked_holding`
    - `parked_future_wave`
    - `historical_backing`
- `roadmap_rank`
  - positive integer
- `depends_on`
  - list of topic slugs
  - may be empty
- `tranches`
  - non-empty list of objects

## 5. Optional Fields

- `github_issue`
  - integer
- `verification_commands`
  - list of strings

If an optional field is omitted, parser code should not fail unless the calling tool explicitly requires it.

## 6. Tranche Entry Contract

Each `tranches` item must contain:

- `id`
  - stable kebab-case identifier
- `title`
  - short human-readable title

Recommended guardrails:

- keep `id` stable once queued tooling depends on it
- keep `title` short enough for operator surfaces

## 7. Parser Rules

- parse only the fenced YAML block under `## 0. Execution Metadata Block`
- do not scrape tranche identity from `## 8. Execution Tranches`
- do not infer `depends_on` from prose once the block is present
- if the block is absent, current tooling may fall back to legacy prose-based inference during migration

## 8. Migration Strategy

Preferred rollout:

1. add this contract
2. add the example block to the execution SSOT template
3. pilot the block in a small set of live queue docs
4. update `sync_temp_queue_state.py` to prefer the block when present
5. update `ops_validator.py` to validate the block-backed fields
6. later, decide whether block presence should become mandatory

## 9. Guardrails

- do not let the block become a second narrative document
- do not duplicate long rationale inside the block
- do not add fields just because they might be useful someday
- do not parse arbitrary markdown when a block lookup is enough
- do not let sidecar files outrank the canonical execution SSOT
