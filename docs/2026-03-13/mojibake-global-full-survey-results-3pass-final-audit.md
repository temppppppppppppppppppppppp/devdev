# Mojibake Global Full Survey Results - 3Pass Final Audit

- 작성일: 2026-03-13
- 기준 오더: `docs/2026-03-13/mojibake-global-full-survey-order-3pass-audit.md`
- evidence: `docs/2026-03-13/mojibake-global-full-survey-evidence.json`
- 조사 모드: `static` / `read-only`
- 최종 상태: `closed`
- 최종 확신도: `93%`

## Executive Summary

`python -X utf8 scripts/mojibake_global_survey.py --output docs/2026-03-13/mojibake-global-full-survey-evidence.json`를 실제 실행했다. scan 결과는 "저장소 전체가 멀쩡하다"가 아니라, `archived log`, `historical material asset`, `IMF chain`, `live source string`, `non-UTF8 root log` 다섯 축에서 실제 저장 손상이 남아 있다는 쪽으로 닫힌다.

반대로 `docs/blockguide/*`, `AGENTS.md`, 일부 build/helper script, `lite_mode/test_mode` fixture, `geuldobi-desktop/src/index.html`의 `??`는 literal detection example, placeholder, language operator라서 retained finding에서 제거했다.

## Pass 1 - Raw Scan

- text files scanned: `20,776`
- suspicious files before re-audit: `105`
- UTF-8 strict decode fail: `1`
- `U+FFFD` 포함 파일: `36`
- `???` 포함 파일: `91`
- `??` 후보 파일: `43`

주요 bucket 분포:

| bucket | files | signal summary |
| --- | ---: | --- |
| `projects` | 14,735 | archived log 5건에 `U+FFFD` 대량 잔존 |
| `docs` | 964 | literal example 다수 + 실제 손상된 historical JSON 묶음 존재 |
| `전처리_ssot` | 103 | 대부분 literal example |
| `modules` | 263 | live source string corruption 5파일 |
| `test_material` | 196 | historical JSON pack 3파일 대량 `???` |
| `<root>` | 32 | `p1_rerun_1arc.err.log` 1건 non-UTF8 |

## Pass 2 - Confirmed Findings

### F1. P1 - Archived project logs already contain durable mojibake

- 대상: `projects/기록용/02_20250305/logs/monitor_output.txt`, `projects/기록용/01_20260305/logs/session/llm_io.jsonl`, `projects/기록용/02_20250305/logs/session/llm_io.jsonl`, `projects/기록용/02_20250305/logs/session_20260305_144837.log`, `projects/기록용/01_20260305/logs/session_20260305_131308.log`
- 집계: `5 files`, `U+FFFD 1,698`, `Q3 78`, `Q2 253`
- 직접 근거:
  - `monitor_output.txt`에 `?�� [TF-32-V]`, `Director ?�심??`, `Arc ?�정 ?�료` 같은 저장 손상 로그가 남아 있다.
  - `session/llm_io.jsonl` 내부에 `작품 설정 — 판정 맥락` 구간이 `?�르`, `주인�?`, `ȸ�� ����`처럼 깨진 채 저장돼 있다.
- 판정:
  - console-only 오탐이 아니라 저장된 artifact 본문 손상이다.
  - 다만 정확한 producer 한 점은 read-only 조사만으로 단정하지 않았다. 현재 `main_a.py`, `modules/api/process_runner.py`, `scripts/run_stage4_smoke.py`의 replace/ignore surface는 관련 위험면으로만 기록한다.

### F2. P1 - Historical material asset 6파일이 대량 `???/??` 상태다

- 대상:
  - `docs/2026-03-08/g5-middle-east-africa-commodities.json`
  - `docs/2026-03-08/g4-europe-russia.json`
  - `docs/2026-03-08/s12-telecom-platforms.json`
  - `test_material/json_outputs/i-tr-dynasty-heir-possession-pack-2006-2031.json`
  - `test_material/json_outputs/i-tr-entertainment-ceo-possession-pack-2006-2031.json`
  - `test_material/json_outputs/i-tr-franchise-tycoon-possession-pack-2006-2031.json`
- 집계: `6 files`, `Q3 42,969`, `Q2 24,392`
- 직접 근거:
  - `g5-middle-east-africa-commodities.json`의 `theme`, `event_name`, `detail`, `strategy`가 대량 `??`로 저장돼 있다.
  - `i-tr-dynasty-heir-possession-pack-2006-2031.json`는 title부터 `???? ?? TR ?`이고, `detail` 필드 전체에 `????`, `???`, `??`가 광범위하게 잔존한다.
- 판정:
  - placeholder 한두 개가 아니라 payload 전체가 의미를 잃은 historical data corruption이다.

### F3. P1 - IMF artifact chain에서 손상이 downstream까지 전파됐다

- 대상:
  - `docs/2026-03-09/imf_kukje_heir_tf_master_001_070.json`
  - `docs/2026-03-09/imf_kukje_heir_tf_continuity_bible_v1.json`
  - `treatments/06_imf_kukje_heir_tr_block_070_draft.json`
  - `bible/06_imf_kukje_heir_bi.json`
- 집계: `4 files`, `Q3 80`, `Q2 46`
- 직접 근거:
  - master와 treatment의 `_schema_description`이 `IMF? ??? ???? ...`로 일부 파손돼 있다.
  - continuity bible과 최종 BI는 `canonical`, `role`, `npc_end_state`, `future_extension_guardrails`까지 `???`가 퍼져 있다.
- 판정:
  - source-side partial corruption이 downstream continuity/BI까지 전달된 케이스로 본다.

### F4. P1 - Live source string corruption이 runtime surface까지 닿는다

- 핵심 대상: `modules/core/relationship_tracker_npc.py`
- 보조 대상:
  - `modules/core/relationship_tracker.py`
  - `modules/validation/blocking_validator_consistency_checks.py`
  - `modules/core/stage4_interview_round.py`
  - `modules/core/pre_director_checklist.py`
  - `tests/test_pass_with_fix.py`
- 직접 근거:
  - `relationship_tracker_npc.py`의 `generate_transition_prompt()` docstring과 반환 문자열이 `??? ??? ???? ??? ??`, `[?? ?? ????]`처럼 깨져 있다.
  - wrapper `modules/core/relationship_tracker.py:89-90`가 그대로 전달한다.
  - `tests/test_relationship_tracker.py:446-454`가 이 API를 실제 surface로 잡고 있다.
  - `blocking_validator_consistency_checks.py`는 import failure warning 자체가 `?? [BlockingValidator] ...`로 깨져 있다.
  - `stage4_interview_round.py`, `pre_director_checklist.py`, `tests/test_pass_with_fix.py`는 저영향 docstring/log 문자열 손상이 남아 있다.
- 판정:
  - `relationship_tracker_npc.py`는 live prompt surface라서 retained finding이다.
  - 나머지 4파일은 collateral low-impact source corruption으로 같이 보존한다.

### F5. P2 - root stderr log 1건이 UTF-8이 아니라 cp949 계열로 저장됐다

- 대상: `p1_rerun_1arc.err.log`
- 직접 근거:
  - UTF-8 strict decode fail
  - alternate decode preview:
    - `cp949`: `[V61.3] Faulthandler 활성화 → crash_dump.log`
    - `latin-1`: `È°¼ºÈ­ ¡æ`로 깨짐
- 판정:
  - mojibake payload라기보다 UTF-8-only 정책 위반 artifact다.
  - 재생성/보관 규칙 관점에서 retained finding으로 남긴다.

## Pass 3 - False Positive Removal

### R1. literal detection example 문서/스크립트는 retained finding이 아니다

- 예:
  - `docs/blockguide/bi-production-harness-v1.md`
  - `docs/2026-03-10/us_ai_exile_monopoly_onboarding_prompt.md`
  - `AGENTS.md`
  - `scripts/build_bi_from_phase0_and_tr.py`
- 이유:
  - `???`, `??`, `�`가 "손상 예시를 탐지하라"는 규칙으로 문자 그대로 적혀 있다.

### R2. placeholder fixture는 retained finding이 아니다

- 예:
  - `lite_mode/projects/무협 test/stage3/ep_0091_context.txt`
  - `test_mode/projects/무협 test/stage3/ep_0091_context.txt`
- 직접 근거:
  - sample line이 `[보상: ???]` 형태다.
- 이유:
  - 서사 placeholder이지 인코딩 파손으로 볼 증거가 없다.

### R3. 언어 문법/연산자/regex의 `??`는 retained finding이 아니다

- 예:
  - `geuldobi-desktop/src/index.html`의 nullish coalescing `value ?? ""`
  - `lite_mode/bridge/gemini_driver.py` regex `\??`
- 이유:
  - syntax-level token이며 문자 손실과 무관하다.

### R4. viewer/console display artifact는 retained finding이 아니다

- 이번 세션에서 PowerShell `Get-Content`로 읽은 기존 UTF-8 문서가 깨져 보였지만, 동일 파일을 `python -X utf8`로 읽으면 정상 본문이 나왔다.
- 따라서 "화면에서 깨져 보임"은 별도 파일 strict-read 반증 없이는 finding으로 올리지 않았다.

## Runtime-only Observations

- `main_a.py:23-29`는 stdio를 UTF-8로 재설정하지만 `errors="replace"`를 사용한다.
- `modules/api/process_runner.py:479,499,582,623`는 decode path에 `errors="replace"`가 남아 있다.
- `modules/core/stage0/reverse_expander.py:205-218`는 UTF-8 실패 시 `cp949` 복구를 허용한다.
- `scripts/run_stage4_smoke.py:80`은 `cp949` + `errors="ignore"` console fallback을 쓴다.

위 4건은 현재 저장 파일 손상과 1:1 인과를 확정한 것은 아니다. 다만 향후 mojibake를 숨기거나 유입시킬 수 있는 producer risk로 기록한다.

## Confidence Ledger

- 기본 점수: `70`
- full worktree strict-read + evidence JSON 생성: `+10`
- 상위 후보 manual sample 재감리: `+8`
- source consumer/test 교차 검증: `+5`
- false-positive bucket 정리: `+5`
- dynamic rerun 미실행, archived log producer 미확정: `-5`

최종 확신도: `93%`

## Final Verdict

- retained findings: `5`
- rejected clusters: `4`
- runtime-only observation clusters: `1`

전역 조사 결론은 "현재 저장소가 깨끗하다"가 아니라 "실제 저장 손상은 historical artifact와 archived log에 이미 남아 있고, 일부 live source string도 깨져 있다"이다.
