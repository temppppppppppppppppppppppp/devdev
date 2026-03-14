# 전역 디테일 전수조사 Baseline Ledger

> 작성일: 2026-03-13
> Prefix: `GDFS-BL`
> 상태: `baseline-frozen`
> 역할: `global-detail-full-survey-master-audit-order.md`의 baseline truth, active surface inventory, 재개 포인터를 한 파일에 잠그는 ledger

---

## 0. 목적

- 기존 detail/reaudit 문서를 무근거로 재오픈하지 않기 위한 baseline freeze
- 현재 live workspace의 active surface를 범위 단위로 고정
- context compaction 이후에도 `무엇을 이미 truth로 채택했는지` 빠르게 복원

---

## 1. Baseline Truth 문서

아래 문서는 이번 전역 조사에서 `선행 truth`로 채택한다.

| 문서 | 기준 상태 | Last Write | 역할 |
|------|-----------|------------|------|
| `docs/2026-03-13/OPUS-TF-5terminal-detail-master-audit-order.md` | baseline order | 2026-03-13 08:59:48 | 미열거 디테일 2차 마스터 오더 |
| `docs/2026-03-13/OPUS-TF-5terminal-deep-dive-master-audit-order.md` | baseline order | 2026-03-13 09:24:47 | 심층 미조사 3차 마스터 오더 |
| `docs/2026-03-13/stage0-full-survey-consolidated-findings-3pass-reaudit.md` | baseline truth | 2026-03-13 19:02:14 | Stage 0 3PASS 재감리 종착점 |
| `docs/2026-03-13/S3D-full-survey-3pass-audit.md` | baseline truth | 2026-03-13 19:02:14 | Stage 3 detail 딥다이브 종착점 |
| `docs/2026-03-13/runtime-observability-provenance-artifact-detail-consolidated-findings-3pass-reaudit.md` | baseline truth | 2026-03-13 19:02:14 | runtime evidence layer 종착점 |
| `docs/2026-03-13/XC-6track-merged-remediation-execution-ssot.md` | baseline merged view | 2026-03-13 19:02:14 | XC 6트랙 통합 SSOT |
| `docs/2026-03-13/ui-frontend-backend-connectivity-remediation-execution-ssot.md` | baseline operator surface | 2026-03-13 04:45:18 | frontend/backend/desktop 연결 기준 |
| `docs/2026-03-13/today-detail-sideeffect-connectivity-liverun-checklist.md` | baseline runtime checklist | 2026-03-13 10:40:12 | 당일 side-effect/canary 순서 기준 |

Reopen 허용 조건:

- `live-code-changed`
- `artifact-contradiction`
- `new-consumer-scope`
- `operator-surface-mismatch`

위 reason code 없이 baseline truth를 뒤집지 않는다.

---

## 2. Active Surface Inventory

아래 수치는 `2026-03-13` 시점 실제 파일 수 기준이다.

| 범위 | 파일 수 | 판정 |
|------|--------|------|
| `modules` | 810 | active core/backend/code |
| `tests` | 871 | active regression/runtime proof surface |
| `scripts` | 19 | active/legacy mixed |
| `lite_mode` | 1,559 | conditional live-consumer 후보 |
| `tools` | 16 | conditional live-consumer 후보 |
| `tools2` | 29 | conditional live-consumer 후보 |
| `main_tools` | 1 | conditional live-consumer 후보 |
| `config` | 55 | active contract/config surface |
| `work_guards` | 2 | active config surface |
| `전처리_ssot/contracts` | 9 | active contract surface |
| `전처리_ssot/docs` | 91 | active process/document contract surface |
| `docs/implementation` | 10 | active implementation contract surface |
| `geuldobi-desktop` | 23,248 | active desktop surface + packaged/vendor 포함 |
| `treatments` | 496 | active artifact/reference surface |
| `bible` | 32 | active artifact/reference surface |
| `projects` | 14,754 | active runtime artifact / DB / project state surface |
| `logs` | 357 | active runtime evidence surface |

해석:

- `geuldobi-desktop`, `projects`는 file count가 크므로 전수 읽기 대상이 아니라 `live consumer path 기준 표면 추출` 방식으로 조사한다.
- `lite_mode`, `tools*`, `scripts`는 기본 포함이 아니라 `actual wiring / operator usage / residue risk` 기준으로 선별한다.

---

## 3. 전역 범위 분류

### 3.1 기본 포함

- `main_a.py`
- `modules/`
- `tests/`
- `config/`
- `work_guards/`
- `전처리_ssot/contracts/`
- `전처리_ssot/docs/`
- `docs/implementation/`
- `geuldobi-desktop/`의 active entry 및 operator-facing surface
- `treatments/`, `bible/`, `projects/`, `logs/`의 live artifact surface

### 3.2 조건부 포함

- `scripts/`
- `lite_mode/`
- `tools/`
- `tools2/`
- `main_tools/`
- 루트 `temp-*`
- `MagicMock/`
- `build/`, `dist/`

판정 기준:

- live code가 참조한다
- operator가 오늘 실제 사용한다
- current finding의 증거다

### 3.3 기본 제외

- `docs/이전/`
- 백업 zip
- 스냅샷 사본
- 현재 import/실행 경로와 무관한 폐기 실험물

---

## 4. 현재 조사 순서

1. baseline freeze
2. active surface inventory
3. `T1` live code hidden branch
4. `T2` persistence / artifact / evidence
5. `T3` config / contract / SSOT drift
6. `T4` UI / API / desktop / operator surface
7. `T5` test / canary / runtime proof
8. `T6` tools / lite mode / residue
9. consolidated findings
10. consolidated 3PASS re-audit

---

## 5. Resume Packet

- `Current phase`: consolidated re-audit completed
- `Last completed pass`: global `PASS 3`
- `Last completed surface`: `global-detail-full-survey-consolidated-findings-3pass-reaudit.md`
- `Next surface`: `global-detail-full-survey-remediation-execution-ssot.md`
- `Reopen reason codes used`: `live-code-changed`, `operator-surface-mismatch`, `new-consumer-scope`
- `Stop gate or blocker`: none

---

## 6. Execution Status Snapshot

생성 완료 문서:

1. `docs/2026-03-13/GDFS-T1-live-code-hidden-branch-findings.md`
2. `docs/2026-03-13/GDFS-T2-persistence-artifact-evidence-findings.md`
3. `docs/2026-03-13/GDFS-T3-config-contract-ssot-drift-findings.md`
4. `docs/2026-03-13/GDFS-T4-ui-api-desktop-operator-surface-findings.md`
5. `docs/2026-03-13/GDFS-T5-test-canary-runtime-proof-findings.md`
6. `docs/2026-03-13/GDFS-T6-tools-lite-mode-live-consumer-residue-findings.md`
7. `docs/2026-03-13/global-detail-full-survey-consolidated-findings.md`
8. `docs/2026-03-13/global-detail-full-survey-consolidated-findings-3pass-reaudit.md`
9. `docs/2026-03-13/global-detail-full-survey-remediation-execution-ssot.md`

전역 totals:

- retained `21`
- `P1 6`
- `P2 14`
- `P3 1`
- `P0 0`
