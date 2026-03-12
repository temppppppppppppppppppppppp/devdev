# Stage 4 Canary Log Audit

작성일: 2026-03-12  
인코딩: UTF-8

대상 canary:
- project: `projects/00_test_07`
- prep source: `projects/00_test_02`
- canary summary: `projects/00_test_07/logs/canary_summary.json`
- lifecycle sink: `projects/00_test_07/logs/episode_production.jsonl`
- final sink: `projects/00_test_07/logs/pass_rate_monitor.json`
- runtime summary: `projects/00_test_07/logs/runtime_audit_summary.json`
- raw session log: `projects/00_test_07/logs/session_20260312_123849.log`
- LLM I/O: `projects/00_test_07/logs/session/llm_io.jsonl`
- drafts/artifacts: `projects/00_test_07/drafts`, `projects/00_test_07/logs/artifacts`
- DB: `projects/00_test_07/project_data.db`

추가 비교 근거:
- `modules/core/stage4_canary_tools.py`
- `scripts/run_stage4_canary.py`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
- `docs/2026-03-12/stage4-canary-automation-3pass-audit.md`
- `tests/test_stage4_canary_tools.py`
- `tests/test_run_stage4_canary.py`
- `tests/test_chief_writer.py`
- `tests/test_stage4_interview_round.py`
- `tests/test_failure_analyzer.py`

## 감사 원칙

- 코드 수정 없이 기존 canary 산출물, DB, 문서, 테스트 코드만 읽는다.
- `확신이 낮다`는 이유만으로 문제를 배제하지 않는다.
- 직접 반증된 경우에만 `기각`한다.
- 반증되지 않은 항목은 아래 중 하나로 남긴다.
  - `확정 문제`
  - `원인 후보가 매우 강한 문제`
  - `운영 계약 문제`
  - `보조 신호`

즉 이번 문서는 `오탐 최소화`보다 `전량 처리`를 우선한다.  
단, 억지 확정은 피하고 `문제 자체`와 `원인 확정 수준`을 분리해 기록한다.

## 3-Pass 요약

### Pass 1. 산출물/DB/로그 파싱

실제 canary 결과는 이미 `clean pass`가 아니다.

- `canary_summary.json`:
  - `hard_gates.status = fail`
  - errors = `candidate_key_mismatches`, `artifact_path_mismatches`, `sink_alignment_status:warn`
- `runtime_audit_summary.json`:
  - `tag = stage4_complete`
  - `total_events = 0`
  - `counts = {}`
- `pass_rate_monitor.json`:
  - Stage 4 attempt 5건 기록
  - ep2 attempt2, ep4 attempt1에서 `patch_strategy=inplace_patch`
  - 동시에 `is_patch=false`
- `episode_production.jsonl`:
  - ep2 round1, ep4 round0에서 `flags.patch_mode=false`
  - 동시에 `patch_trace.patch_strategy=inplace_patch`
- `drafts/ep_0004.txt`, `patched_after_fix__A_InPlace.txt`, DB `manuscripts.ep_num=4`:
  - 모두 `{ "revised_manuscript": ... }` wrapper가 원고 본문처럼 저장됨

### Pass 2. 코드·문서·테스트 계약 대조

이번 canary에서 드러난 문제는 로그만의 해석 차이가 아니었다.

- `stage4_canary_tools.py`와 runbook은 post-run canary에서
  - `candidate_key_mismatches == []`
  - `artifact_path_mismatches == []`
  - `sink_alignment_summary.status == "ok"`
  를 hard gate로 요구한다.
- 현재 canary는 바로 그 필드들 때문에 fail이다.
- `tests/test_run_stage4_canary.py`는 `save()/flush()/analyze()` 호출만 검증한다.
- `tests/test_stage4_canary_tools.py`는 prep 직후 fail-closed를 검증하지만, post-run mismatch 허용 규칙은 다루지 않는다.
- `tests/test_chief_writer.py`는 JSON unwrap 케이스를 검증하지만, `revised_manuscript` key는 커버하지 않는다.

### Pass 3. retained 판정

이번 문서에서는 낮은 확신 항목도 버리지 않고 아래처럼 남긴다.

- 확정 문제: 6건
- 원인 후보가 매우 강한 문제: 2건
- 보조 신호: 3건

결론은 단순하다.

1. 현재 canary는 `runbook/auto-gate 기준 fail`이다.
2. ep4 wrapper 저장은 실제 산출물 오염이다.
3. 투자물 canary에 무협 state schema 잔재가 실제 prompt/response에 존재한다.
4. sink mismatch는 일부가 semantics 차이일 수 있어도, 현재 계약상 허용되지 않으므로 문제로 유지한다.

## Findings

### F-01. 확정 문제 — `revised_manuscript` wrapper가 최종 manuscript로 저장된다

증상:
- `drafts/ep_0004.txt`가 plain manuscript가 아니라 `{ "revised_manuscript": ... }` 전체 JSON이다.
- 같은 wrapper가 artifact와 DB manuscript까지 전파된다.
- downstream `StateExtractor`도 wrapper째 입력받는다.

직접 근거:
- `projects/00_test_07/drafts/ep_0004.txt`
- `projects/00_test_07/logs/artifacts/stage4/ep_0004/attempt_01/patched_after_fix__A_InPlace.txt`
- `projects/00_test_07/project_data.db`
  - `manuscripts.ep_num=4.content` 시작부가 `{ "revised_manuscript": ... }`
- `projects/00_test_07/logs/session/llm_io.jsonl` line 117
  - `agent = "StateExtractor"`
  - prompt 본문이 `{"revised_manuscript": ...}` wrapper째 들어간다

코드 근거:
- `modules/domain/agents/chief_writer.py:1426-1440`
  - JSON unwrap 1단계가 `corrected_manuscript`, `patched_text`, `content`, `text`, `manuscript`, `patched_manuscript`만 본다
- `modules/domain/agents/chief_writer.py:1501-1523`
  - `_unwrap_manuscript_text()`도 동일하게 `revised_manuscript`를 모른다

테스트 대조:
- `tests/test_chief_writer.py:151-206`
  - `content`, `patch_state_updates`, short-manuscript guard는 검증한다
  - 그러나 `revised_manuscript` key 케이스는 없다

판정:
- 이건 `로그 해석`이 아니라 `실제 저장 오염`이다.
- 원인도 거의 닫혔다.
  - unwrap code가 `revised_manuscript` 키를 인식하지 못하는 설계 공백이다.

### F-02. 원인 후보가 매우 강한 문제 — 투자물 canary에서 장르명 매핑 drift로 무협 state schema가 주입될 가능성이 높다

증상:
- 투자물 canary prompt/response 안에 `internal_energy`, `realm`, `causal_injuries`, `martial_arts`가 등장한다.

직접 근거:
- `projects/00_test_07/logs/session/llm_io.jsonl` line 33
  - `agent = "ChiefWriter"`
  - `state_updates`가 무협형 키를 포함한다
- `projects/00_test_07/project_data.db`
  - `anchors.genre_info.data.name = "투자 (Investment Fiction)"`
  - `anchors.genre_info.data.type = "investment"`

코드 근거:
- `scripts/run_stage4_canary.py:127-135`
  - runner는 `genre_info` anchor의 `name/type`를 그대로 읽어 boot에 넣는다
- `modules/core/stage4_orchestrator.py:673`
- `modules/core/stage4_context_builder.py:2041`
  - Stage 4는 `current_project.genre.name`을 `genre_name`으로 사용한다
- `modules/domain/agents/chief_writer_context.py:157-169`
  - 장르 매핑은 `"투자물": "investment"`만 인식한다
  - 매핑 miss 시 `bible_root.get("_genre", "wuxia")`로 fallback한다

강한 해석:
- 실제 genre name은 `"투자 (Investment Fiction)"`인데, context builder 매핑은 `"투자물"`만 인식한다.
- 따라서 investment canary가 context 단계에서 `wuxia` fallback을 타는 경로가 열려 있다.
- line 33의 무협형 `state_updates`와 코드 fallback 규칙이 정확히 맞물린다.

보수적 단서:
- 이 항목은 아직 `단일 원인 100% 확정`은 아니다.
- 그러나 현재 확보한 로그·DB·코드 근거만으로도 `매우 강한 원인 후보`이며, 문제 자체는 확정이다.

### F-03. 확정 문제 — 현재 canary는 자기 계약 기준으로 명백한 FAIL이다

증상:
- `canary_summary.json`가 `candidate_key_mismatches`, `artifact_path_mismatches`, `sink_alignment_status:warn` 때문에 fail이다.

직접 근거:
- `projects/00_test_07/logs/canary_summary.json`
  - `hard_gates.status = fail`
  - `sink_alignment_summary.status = warn`
  - `candidate_key_mismatches = 3`
  - `artifact_path_mismatches = 3`

문서/코드 계약 근거:
- `docs/2026-03-12/stage4-canary-execution-runbook.md:109-112`
  - `candidate_key_mismatches == []`
  - `selection_candidate_key_mismatches == []`
  - `artifact_path_mismatches == []`
- `docs/2026-03-12/stage4-canary-execution-runbook.md`
  - `sink_alignment_summary.status != "ok"`면 fail
- `modules/core/stage4_canary_tools.py:287-302`
  - 위 mismatch와 `sink_alignment_status != ok`를 hard error로 추가한다

판정:
- 일부 mismatch가 `initial/lifecycle vs final` 의미 차이에서 왔을 가능성은 있다.
- 그래도 현재 runbook과 auto gate는 그 차이를 허용하지 않는다.
- 따라서 이 canary는 현재 계약상 `실패`이며, 낮은 확신을 이유로 fail을 취소하면 안 된다.

### F-04. 확정 문제 — candidate/artifact linkage가 실제로 흔들린다

증상:
- 같은 attempt인데 sink마다 `candidate_key`와 `artifact_path`가 다르다.
- 일부는 단순 label 차이가 아니라 같은 내용이 서로 다른 파일명으로 중복 저장된다.

직접 근거:
- `projects/00_test_07/logs/episode_production.jsonl`
  - ep2 attempt2: `candidate_key = A|inplace_patch`
  - ep4 attempt1: `candidate_key = A|긴장감 + 반전 강조`
- `projects/00_test_07/logs/pass_rate_monitor.json`
  - ep2 attempt2, ep4 attempt1: `candidate_key = A|InPlace 수정`
- `projects/00_test_07/project_data.db`
  - `director_selections.stage=4`
  - ep2 round1: `candidate_key = A|inplace_patch`
  - ep4 round0: `candidate_key = A|긴장감 + 반전 강조`
- artifact 중복:
  - `projects/00_test_07/logs/artifacts/stage4/ep_0002/attempt_02/patched_after_fix__A_InPlace.txt`
  - `projects/00_test_07/logs/artifacts/stage4/ep_0002/attempt_02/patched_after_fix__A_inplace_patch.txt`
  - 두 파일의 SHA-256이 동일
  - `889C6D21F56383A0BEFE38E93F20A19829C6B5A12D2B8D6B7941442D3AA82ACD`
  - `projects/00_test_07/logs/artifacts/stage4/ep_0004/attempt_01/patched_after_fix__A.txt`
  - `projects/00_test_07/logs/artifacts/stage4/ep_0004/attempt_01/patched_after_fix__A_InPlace.txt`
  - 두 파일의 SHA-256이 동일
  - `CD22D96E4453276DF5CD227586576D6EA65982645F7290D9A11AC6B971CE182B`

테스트/문서 대조:
- `tests/test_failure_analyzer.py:424-527`
  - analyzer는 이런 mismatch를 실제 경고 대상으로 본다
- `docs/2026-03-12/logging-reinforcement-master-roadmap.md:27-30, 40-43, 127-129`
  - Stage 4 linkage는 cross-sink로 설명 가능해야 한다고 적는다

판정:
- 이 항목은 `단순 표시 차이`로 치부하기 어렵다.
- 실제 runtime에서 같은 원고가 여러 이름으로 남고, sink마다 서로 다른 label/path를 참조한다.

### F-05. 확정 문제 — ep4의 local issue가 structural inplace로 라우팅되지 않았다

증상:
- ep4 Director feedback은 1인칭 POV 관련 국소 수정이다.
- 그런데 실제 patch trace는 `inplace_patch`, `fallback_reason=unclassified_feedback`, `structural_attempted=false`다.

직접 근거:
- `projects/00_test_07/logs/episode_production.jsonl`
  - ep4 round0:
    - `verdict_reason = 1인칭 시점에서 타인의 내면 심리를 단정적으로 서술하는 미세한 오류 발생`
    - `action_items = 복도 장면 특정 문장을 추측형으로 수정`
    - `patch_trace.patch_strategy = inplace_patch`
    - `patch_trace.fallback_reason = unclassified_feedback`
    - `patch_trace.structural_attempted = false`
- `projects/00_test_07/logs/pass_rate_monitor.json`
  - ep4 record도 `patch_strategy=inplace_patch`, `structural_attempted=false`

코드/테스트 근거:
- `modules/domain/agents/chief_writer.py:1324-1372`
  - structural patch는 `focus` 분류가 되면 시도되고, 아니면 `unclassified_feedback`로 whole-text fallback한다
- `tests/test_chief_writer.py:263-353`
  - structural path와 global fallback path가 분리되어 있다
- `tests/test_stage4_interview_round.py:1550-1741`
  - Stage 4는 structural patch trace를 실제로 보존하도록 기대한다

판정:
- 구조적 국소 수정이 필요한 실제 canary 케이스에서 classifier가 patch focus를 잡지 못했다.
- 이건 단순 미관 문제가 아니라 `scene-aware patch`의 실전 미작동이다.

### F-06. 확정 문제 — patch lineage 플래그가 sink마다 서로 다른 의미를 남긴다

증상:
- patch attempt인데 final sink는 `is_patch=false`
- lifecycle sink도 patch인데 `flags.patch_mode=false`
- 반면 `patch_strategy=inplace_patch`는 존재한다

직접 근거:
- `projects/00_test_07/logs/pass_rate_monitor.json`
  - ep2 attempt2, ep4 attempt1:
    - `patch_strategy=inplace_patch`
    - `is_patch=false`
- `projects/00_test_07/logs/episode_production.jsonl`
  - ep2 round1, ep4 round0:
    - `patch_trace.patch_strategy=inplace_patch`
    - `flags.patch_mode=false`

판정:
- 운영자가 `patch attempt였는지`를 sink별로 일관되게 읽을 수 없다.
- correctness bug까지는 아니어도 observability 계약은 깨져 있다.

### F-07. 확정 문제 — `runtime_audit_summary.json`는 completion tag만 있고 event count는 비어 있다

직접 근거:
- `projects/00_test_07/logs/runtime_audit_summary.json`
  - `tag = stage4_complete`
  - `total_events = 0`
  - `counts = {}`

테스트 대조:
- `tests/test_stage4_canary_tools.py:103-136`
  - prep/analyze fail-closed는 보지만, post-run runtime summary richness는 검증하지 않는다

판정:
- 현재 파일은 completion marker로만 기능한다.
- runbook의 운영 추적 문서가 기대하는 이벤트 요약물로는 빈약하다.

### F-08. 확정 문제 — ep4 종료 경로에서 `causal_graph` dual-write runtime bug가 발생한다

직접 근거:
- `projects/00_test_07/logs/session_20260312_123849.log:3073`
  - `[Stage4] causal_graph dual-write 실패 (비치명): 'str' object has no attribute 'get'`

판정:
- Stage4 완료를 막지는 않았지만 runtime bug는 남아 있다.
- `비치명` 라벨 때문에 삭제하면 안 된다. 실제 예외가 발생했다.

### F-09. 보조 신호 — downstream verifier가 wrapper/본문 차이를 사후 보정한다

직접 근거:
- `projects/00_test_07/logs/session_20260312_123849.log:3067-3071`
  - `connections`, `equipment` 불일치를 감지하고 `actual_truth`를 수정한다
- `projects/00_test_07/project_data.db`
  - `state_logs.ep_num=4.data.actual_truth`
  - `internal_energy`, `realm`, `martial_arts`, `causal_injuries`는 없고
  - `capital`, `connections`, `equipment`는 투자물 기준으로 정산됨

판정:
- state 정산 자체는 투자물 형태로 수습됐다.
- 하지만 이건 upstream 오염이 없었다는 뜻이 아니라, downstream recovery가 작동했다는 뜻이다.

### F-10. 보조 신호 — `TF-H` 길이 부족 경고가 전 구간에 반복된다

직접 근거:
- `projects/00_test_07/logs/session_20260312_123849.log`
  - 분량 부족/대화 비율 부족 경고가 ep1~ep4 전반에 다수 존재

판정:
- 즉시 blocker는 아니지만 품질/비용 비효율 신호다.
- 특히 candidate 여러 개가 구조적으로 길이 하한을 자주 놓친다.

### F-11. 보조 신호 — canary 테스트는 실행 경로를 고정하지만, 실제 발견된 후행 결함은 대부분 커버하지 못한다

직접 근거:
- `tests/test_run_stage4_canary.py`
  - `save()`, `_flush_audit_buffer()`, `analyze()` 호출 여부만 본다
- `tests/test_stage4_canary_tools.py`
  - prep/reset과 pre-run fail-closed를 본다
- `tests/test_chief_writer.py:151-206`
  - unwrap 기본 케이스는 보지만 `revised_manuscript`는 안 본다

판정:
- 이번 canary에서 잡힌 핵심 문제는 “테스트가 있으니 이미 안전하다”로 닫을 수 없다.
- 테스트는 helper/runner의 골격 계약만 보장하고, 실제 runtime artifact drift는 대부분 놓친다.

## 우선순위 정리

### P1

- `revised_manuscript` wrapper가 final manuscript로 저장되는 문제
- 투자물 canary에서 무협 state schema가 주입되는 문제
- candidate/artifact linkage drift로 canary가 자기 계약 기준 fail이 되는 문제

### P2

- local issue가 structural inplace로 라우팅되지 않는 문제
- patch lineage flag 의미 불일치
- runtime_audit_summary 정보량 부족
- `causal_graph` dual-write runtime bug

### Observation

- downstream verifier의 사후 수습
- 반복적인 TF-H 길이 부족 경고
- canary helper/test의 커버리지 공백

## 최종 판정

현재 `00_test_07` canary는 `형식상 완료`가 아니라 `계약상 FAIL`이다.

핵심 이유는 3개다.

1. ep4 patch 결과가 JSON wrapper째 draft/artifact/DB/downstream prompt로 전파됐다.
2. investment canary에 wuxia state schema가 실제로 섞였다.
3. candidate/artifact linkage mismatch가 runbook과 auto gate 둘 다에서 hard fail로 취급된다.

여기서 `candidate_key/artifact_path mismatch가 semantics 차이일 수도 있다`는 해석은 보조 설명으로만 남긴다.  
현재 계약이 그것을 허용하지 않고, 실제로 동일 content가 다른 artifact 이름으로 중복 저장되는 사례까지 확인됐기 때문이다.

즉 이번 문서의 결론은 다음과 같다.

- 낮은 확신을 이유로 이 canary를 clean pass로 돌리면 안 된다.
- 원인 100% 확정이 안 된 항목도 `문제 자체`는 유지해야 한다.
- 현재 canary는 `문제 있음` 쪽으로 판정하는 것이 맞다.

코드 수정과 테스트 실행은 수행하지 않았다.
