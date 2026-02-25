# Metrics Baseline

Purpose:
- Track measurable baselines and targets by stage.

## Baseline Table

| Metric | Stage | Baseline | Target | Source | Notes |
|---|---|---|---|---|---|
| Test Baseline | Global | 2,583 passed + 0 xfailed (2026-02-24) | TBD | `CLAUDE.md` | 문서 기준선. `FILL_ORDER.md`의 2,618 값과 불일치하여 최신 재검증 필요 |
| QualityGate Score | Stage 2 | 90 | 90 | `config/settings/validation.yaml` (`scoring.quality_gate_score`) | Arc 검증 |
| QualityGate Score | Stage 3 | 80 | 80 | `config/settings/validation.yaml` (`scoring.blueprint_quality_gate_score`) | Blueprint 검증 |
| QualityGate Score | Stage 4 | 90 | 90 | `config/settings/validation.yaml` (`scoring.quality_gate_score`) | 원고 검증 |
| Patch Threshold | Global | `rewrite_below=50` | 유지 | `config/settings/validation.yaml`, `modules/core/constants.py` (`PatchModeThresholds.REWRITE`) | 50 미만 전면 재작성 |
| Patch Threshold | Stage 4 | `patch_below=80` | 유지 | `config/settings/validation.yaml`, `modules/core/constants.py` (`PatchModeThresholds.PATCH`) | 80 미만 패치 모드 분기 |
| Patch Threshold | Stage 3 | `inplace_below=60` | 유지 | `config/settings/validation.yaml`, `modules/core/constants.py` (`PatchModeThresholds.INPLACE`) | 60 이상 in-place 단일 수정 |
| Manuscript Length | Stage 4 | `min=4000`, `target=5000`, `max=15000` | 유지 | `config/settings/validation.yaml` (`manuscript.*`) | 분량 가드 |
| Throughput | Stage 0 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Throughput | Stage 1 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Throughput | Stage 2 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Throughput | Stage 3 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Throughput | Stage 4 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Error Rate | Stage 0 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Error Rate | Stage 1 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Error Rate | Stage 2 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Error Rate | Stage 3 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |
| Error Rate | Stage 4 | TBD | TBD | TBD | 코드/문서에 고정 수치 없음 |

## Measurement Rules
- Use the same sampling window across comparisons.
- Record exact command and environment.
- Do not compare mixed datasets.

## Last Verified
- Date: 2026-02-25
- Commit: `f99119d`
- Code Sync (Yes/No): Yes
- Verified By: Codex

