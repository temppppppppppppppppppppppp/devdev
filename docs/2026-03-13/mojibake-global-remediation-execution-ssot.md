# Mojibake Global Remediation Execution SSOT

> 작성일: 2026-03-13
> 상태: `execution-ready`
> 확신도 목표: `95%`
> 기준 조사:
> - `docs/2026-03-13/mojibake-global-full-survey-order-3pass-audit.md`
> - `docs/2026-03-13/mojibake-global-full-survey-results-3pass-final-audit.md`
> - `docs/2026-03-13/mojibake-global-full-survey-evidence.json`
> 역할: 3pass 재감리로 남은 `mojibake` retained set을 실행 단위, 순서, acceptance, 증거 산출물로 다시 잠그는 단일 SSOT

## Executive Summary

- 현재 retained set은 `P1 4건`, `P2 1건`이다.
- 실제 실행은 raw file-by-file patch가 아니라 `5개 execution unit`으로 재배열하는 것이 맞다.
- 핵심 방향은 `archive evidence quarantine`, `historical asset recovery`, `IMF chain repair`, `live source string cleanup`, `output boundary hardening`이다.
- 권장 실행 순서는 `MJB-E1 -> MJB-E2 -> MJB-E3 -> MJB-E4 -> MJB-E5`다.
- 이번 문서는 실행 기준만 고정한다. 실제 코드/데이터 수정은 후속 execution 턴에서만 수행한다.

## Scope

포함:

- `projects/기록용/**/*`
- `docs/2026-03-08/*.json`
- `docs/2026-03-09/imf_kukje_heir_tf_*.json`
- `test_material/json_outputs/i-tr-*.json`
- `treatments/06_imf_kukje_heir_tr_block_070_draft.json`
- `bible/06_imf_kukje_heir_bi.json`
- `modules/core/relationship_tracker_npc.py`
- `modules/core/relationship_tracker.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/pre_director_checklist.py`
- `tests/test_relationship_tracker.py`
- `tests/test_pass_with_fix.py`
- `main_a.py`
- `modules/api/process_runner.py`
- `modules/core/stage0/reverse_expander.py`
- `scripts/run_stage4_smoke.py`
- `scripts/mojibake_global_survey.py`
- 후속 remediation evidence 문서

제외:

- `dist`, `python-embed`, packaged bundle inventory
- literal example 문서(`docs/blockguide/*`, onboarding prompt류)의 예시 문자열 제거 작업
- placeholder fixture (`[보상: ???]`) 정리
- unrelated feature work
- live/full canary rerun

## Non-Negotiables

### 1. UTF-8 only, blind replacement 금지

- `???`, `??`, `�`를 기계적으로 일괄 치환하지 않는다.
- 의미 복원은 `authoritative upstream`가 있을 때만 허용한다.
- upstream이 없으면 `repair`가 아니라 `quarantine` 또는 `legacy-corrupt` 분류로 닫는다.

### 2. Archive evidence는 원본 바이트를 보존한다

- archived log와 historical corrupted artifact는 원본 증거를 덮어쓰지 않는다.
- 필요하면 `recovered/` 또는 `clean/` 파생본을 만들고 provenance를 문서로 남긴다.
- 원본 삭제/이동이 필요할 때도 checksum 또는 manifest를 남긴다.

### 3. 각 execution unit은 3PASS를 강제한다

1. Pass 1: source truth 확인 또는 quarantine 전략 확정
2. Pass 2: focused verification
3. Pass 3: scanner rerun + 문서/evidence 동기화

### 4. 한 번에 1유닛만 진행한다

- 데이터 복원과 source code patch를 같은 턴에 섞지 않는다.
- 각 유닛은 acceptance와 evidence가 닫힌 뒤 다음 유닛으로 넘어간다.

## Retained Set -> Execution Unit Map

| Finding | Severity | Execution Unit | 실행 의미 |
| --- | --- | --- | --- |
| `F1 archived logs` | `P1` | `MJB-E1` | 손상 log evidence quarantine + active baseline 분리 |
| `F2 historical material assets` | `P1` | `MJB-E2` | 대량 `???` asset family 복원 또는 격리 |
| `F3 IMF chain` | `P1` | `MJB-E3` | master -> treatment -> bible 체인 복원 |
| `F4 live source strings` | `P1` | `MJB-E4` | runtime-visible literal/docstring/log string 정리 |
| `F5 non-UTF8 root log` + runtime-only observations | `P2` | `MJB-E5` | future writer/decode boundary hardening |

## Public Contracts To Preserve

- `relationship_tracker.generate_transition_prompt()`의 함수 시그니처와 반환 구조는 유지한다.
- `BlockingValidator`의 validation semantics는 바꾸지 않는다. 문자열 가독성만 바로잡는다.
- archived log는 historical evidence로서 append-only 성격을 유지한다.
- Stage 0 입력 정책은 최소한 현재의 `utf-8 -> cp949 -> fail-closed` 의미를 잃지 않는다.
- `scripts/mojibake_global_survey.py`의 JSON summary shape는 후속 rerun 비교가 가능해야 한다.

## Execution Units

### MJB-E1. Archived Log Evidence Quarantine

목표:

- 이미 손상된 archived log 5파일을 `active mojibake baseline`과 분리하고, 원본 evidence를 보존한다.

대상:

- `projects/기록용/02_20250305/logs/monitor_output.txt`
- `projects/기록용/01_20260305/logs/session/llm_io.jsonl`
- `projects/기록용/02_20250305/logs/session/llm_io.jsonl`
- `projects/기록용/02_20250305/logs/session_20260305_144837.log`
- `projects/기록용/01_20260305/logs/session_20260305_131308.log`

작업:

- file manifest를 만들고 `historical-corrupt-archive` 상태를 부여한다.
- active health gate에서 이 5파일을 `known-corrupt evidence`로 분리할지, 별도 ledger로 유지할지 결정한다.
- 원본을 덮어쓰지 않고 필요시 sanitized copy 또는 metadata sidecar를 만든다.

비포함:

- 손상 로그 본문을 추정 복원하는 수동 번역
- runtime code patch

acceptance:

- 5파일 모두 provenance와 상태가 문서화된다.
- 후속 scanner/quality gate가 이 파일들을 "현재 live writer가 새로 만든 손상"과 구분한다.
- 원본 바이트는 보존된다.

필수 산출물:

- `mojibake-archive-manifest` 계열 문서 또는 JSON

### MJB-E2. Historical Material Asset Recovery / Quarantine

목표:

- 대량 `???/??` 상태인 material asset family 6파일을 upstream 기준으로 복원하거나, upstream 부재 시 확실히 격리한다.

대상:

- `docs/2026-03-08/g5-middle-east-africa-commodities.json`
- `docs/2026-03-08/g4-europe-russia.json`
- `docs/2026-03-08/s12-telecom-platforms.json`
- `test_material/json_outputs/i-tr-dynasty-heir-possession-pack-2006-2031.json`
- `test_material/json_outputs/i-tr-entertainment-ceo-possession-pack-2006-2031.json`
- `test_material/json_outputs/i-tr-franchise-tycoon-possession-pack-2006-2031.json`

작업:

- 각 파일의 authoritative upstream을 찾는다.
- upstream이 있으면 clean regeneration 경로를 사용한다.
- upstream이 없으면 `legacy-corrupt material pack`으로 분류하고 active ingestion에서 분리한다.
- asset family 단위로 `repairable`과 `non-repairable`을 나눈다.

비포함:

- 모델 추측으로 내용을 채워 넣는 복원
- unrelated material schema redesign

acceptance:

- 6파일 모두 `recovered` 또는 `quarantined` 중 하나로 닫힌다.
- recovered 파일은 strict UTF-8 read + semantic field spot-check를 통과한다.
- quarantined 파일은 active material path에서 참조되지 않는다.

필수 산출물:

- `material-recovery-source-map`
- `material-quarantine-ledger`

### MJB-E3. IMF Chain Authoritative Repair

목표:

- `master -> continuity bible -> treatment -> BI` 체인에서 깨진 IMF 계열 산출물을 lineage를 유지한 채 복원한다.

대상:

- `docs/2026-03-09/imf_kukje_heir_tf_master_001_070.json`
- `docs/2026-03-09/imf_kukje_heir_tf_continuity_bible_v1.json`
- `treatments/06_imf_kukje_heir_tr_block_070_draft.json`
- `bible/06_imf_kukje_heir_bi.json`

작업:

- upstream source와 field ownership을 먼저 정한다.
- partial corruption인 `master/treatment`와 heavy corruption인 `continuity bible/BI`를 분리 처리한다.
- 최종 repair는 같은 체인에서 title, canonical name, role, continuity field가 서로 모순되지 않도록 끝낸다.

비포함:

- IMF 작품의 서사 재기획
- unrelated BI schema change

acceptance:

- 위 4파일에 `???`, `??`, `U+FFFD`가 semantically significant field에 남지 않는다.
- `master`, `treatment`, `bible`의 title/canonical mapping/continuity field가 서로 일치한다.
- repair provenance가 문서화된다.

필수 산출물:

- `imf-chain-repair-ledger`

### MJB-E4. Live Source String Cleanup + Regression Guard

목표:

- 실제 wrapper/test를 통해 닿는 source string corruption을 정리하되, 동작 의미는 바꾸지 않는다.

대상:

- `modules/core/relationship_tracker_npc.py`
- `modules/core/relationship_tracker.py`
- `modules/validation/blocking_validator_consistency_checks.py`
- `modules/core/stage4_interview_round.py`
- `modules/core/pre_director_checklist.py`
- `tests/test_relationship_tracker.py`
- `tests/test_pass_with_fix.py`

작업:

- runtime-visible string, docstring, warning message의 손상을 바로잡는다.
- `relationship_tracker_npc.generate_transition_prompt()`와 wrapper 경로를 focused regression으로 고정한다.
- touched file에 대해 `???/??/�` literal이 intentional example이 아닌 이상 남지 않게 한다.

비포함:

- relationship FSM redesign
- Stage 4 logic flow 변경

acceptance:

- touched live source 파일에서 unintentional garbled token이 `0`이다.
- `tests/test_relationship_tracker.py`와 관련 focused regression이 유지된다.
- 수정이 string cleanup임을 문서와 diff에서 방어할 수 있다.

필수 산출물:

- `source-string-cleanup-proof`

### MJB-E5. Output Boundary Hardening

목표:

- 미래에 새 mojibake가 다시 저장되지 않도록 writer/decode boundary의 의미를 표준화한다.

대상:

- `p1_rerun_1arc.err.log`
- `main_a.py`
- `modules/api/process_runner.py`
- `modules/core/stage0/reverse_expander.py`
- `scripts/run_stage4_smoke.py`
- 필요 시 logging/runbook 문서

작업:

- root `.err.log` 같은 non-UTF8 artifact가 어떤 경로에서 생기는지 추적하고 writer contract를 문서화한다.
- `errors="replace"` / `errors="ignore"` decode path를 `durable sink 금지`와 `console-only 허용`으로 분리해 기록한다.
- Stage 0 인입 정책을 `utf-8 -> cp949 -> fail-closed`로 명시 고정하고 future drift를 막는다.
- smoke/runtime helper가 console masking을 파일 저장으로 오해하게 만들지 않도록 runbook을 보강한다.

비포함:

- packaged live rerun
- process runner 전면 재설계

acceptance:

- future writer policy가 문서와 코드에서 한 의미를 가진다.
- non-UTF8 root log 재발 방지 규칙이 존재한다.
- scanner rerun 시 새 artifact가 same-class finding으로 추가되지 않는다.

필수 산출물:

- `encoding-boundary-contract`

## Recommended Execution Order

1. `MJB-E1`
- 손상 archive를 먼저 분리해야 이후 rerun scanner 숫자가 의미를 가진다.

2. `MJB-E2`
- 대량 corrupted asset family를 먼저 정리해야 active material surface를 깨끗하게 만들 수 있다.

3. `MJB-E3`
- IMF chain은 downstream treatment/BI까지 연결돼 있어 별도 묶음으로 복원하는 편이 안전하다.

4. `MJB-E4`
- live source string은 수정 blast radius가 작고 focused regression으로 닫기 쉽다.

5. `MJB-E5`
- 마지막에 output boundary contract를 잠가야 앞선 repair/quarantine 이후 재오염을 막는다.

## Verification Plan

각 유닛 종료 시 공통:

1. `python -X utf8 scripts/mojibake_global_survey.py --output docs/2026-03-13/mojibake-global-full-survey-evidence.json`
2. touched file strict-read sample 확인
3. evidence diff와 문서 ledger 갱신

유닛별 focused verification:

- `MJB-E1`: archive manifest와 scanner 분리 규칙 확인
- `MJB-E2`: recovered/quarantined asset list + field spot-check
- `MJB-E3`: IMF chain 4파일 line-level semantic field 검증
- `MJB-E4`: `pytest tests/test_relationship_tracker.py tests/test_pass_with_fix.py -q`
- `MJB-E5`: writer/decode contract 정적 점검 + root log 재발 방지 증거

## Stop Conditions

- authoritative upstream 없이 blind repair만 가능한 경우
- archived evidence를 덮어써야만 진행 가능한 경우
- 한 execution unit 안에서 unrelated semantic change가 섞이기 시작한 경우
- rerun scanner가 새 `P1` 이상을 추가로 드러내는 경우

## Final Direction

- follow-up execution은 반드시 이 SSOT 기준으로 한 유닛씩 진행한다.
- 다음 턴의 권장 시작점은 `MJB-E1 archived log quarantine`이다.
