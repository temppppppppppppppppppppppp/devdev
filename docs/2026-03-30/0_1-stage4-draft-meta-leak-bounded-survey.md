# 0_1 Stage4 Draft Meta Leak Bounded Survey

Date: 2026-03-30
Status: active
Scope: `0_1` Stage 4 reader-facing draft/meta leak only
Temp Mirror Path: deferred

Commit State:
- Baseline Commit: `229b85c655c32366818c2278462b51f3ad490913`
- Baseline Dirty Summary: `dirty: tracked stage4 runtime files/tests plus live-run logs/db artifacts and EP8 docs; active python main_a.py`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Question

`projects/0_1/drafts/ep_0001.txt` 같은 최종 draft에 아래 형식이 그대로 남는 문제를 bounded 조사한다.

- `### 씬 1: 2024년의 끝, 2006년의 시작`
- `[2024년 12월, 서울 외곽의 좁은 원룸]`

핵심 판정 질문은 두 가지였다.

1. 이 포맷이 모델의 일회성 출력 실수인가
2. 아니면 시스템 contract가 reader-facing 산출물에 내부 scaffold를 누수시키는가

## 2. Conclusion

결론은 `시스템 contract leak`이다.

- Chief Writer prompt가 scene header를 강제한다.
- Pre-director checker가 scene header 존재를 품질 계약처럼 취급한다.
- Reader-facing final artifact 직전에서 이를 벗겨내는 sink boundary가 없었다.
- Manuscript validator는 `EP 6`, `다음 화` 같은 메타 참조는 막지만, `### 씬 N` / standalone bracket cue line은 실질적으로 막지 못했다.

즉 현재 draft는 `내부 구조화 원고` 계약으로 생성되고 있었고, 그것이 그대로 DB manuscript와 `drafts/*.txt`에 저장되고 있었다.

## 3. Evidence

### 3.1 Writer contract가 scene header를 강제함

`modules/domain/agents/chief_writer_prompts.py:139-142`

- `각 씬의 시작 부분에 반드시 '### 씬 N: 제목' 형식의 마크다운 헤더를 삽입하라`
- `씬 헤더 없이 하나의 산문 블록으로 쓰면 불합격이다`

이건 선택이 아니라 명시적 hard instruction이다.

### 3.2 Pre-director checker가 header contract를 검증함

`modules/core/pre_director_manuscript_checker.py:266-283`

- `_SCENE_HEADER_RE`가 `^#{1,3}\s+씬\s*(\d+)\s*[:\-]`를 찾는다.
- `_check_scene_header_contract()`는 blueprint 씬이 3개 이상일 때 원고 내 header 존재율을 점검한다.

즉 pipeline 중간 품질 게이트도 이 포맷을 정상 구조로 본다.

### 3.3 Scene은 "정확히 4개"가 아니라 "최소 4개" contract다

`modules/domain/agents/director_ensemble.py:1594-1604`

- blueprint `scene_breakdown`이 4개 미만이면 Director가 REJECT한다.

`modules/core/confidence_calibration.py:327-333`

- `4 <= scene_count <= 7`을 가장 선호한다.
- `3` 또는 `8`도 차선으로 허용된다.

따라서 이번 문제는 `씬을 꼭 4분할해서 써야 한다`가 아니라, `scene structure를 내부 scaffold로 유지하되 reader-facing artifact에 그대로 노출한 것`이다.

### 3.4 Final leak blocker가 부재함

`modules/domain/agents/manuscript_validator.py:748-755`

- `META_PATTERNS`는 `EP 6`, `에피소드 12`, `다음 회`, `작가가` 등을 막는다.
- 그러나 `### 씬 N:` 또는 `[시간/장소 cue]`를 막는 reader-facing blocker는 없다.

### 3.5 실제 산출물 오염 범위

Read-only evidence 기준으로 `0_1` 산출물 전 화수에 누수가 확인됐다.

- `rg -n "^### 씬|^\\[[0-9]{4}년|^\\[[^\\]]+\\]$" projects/0_1/drafts`
- `ep_0001.txt` ~ `ep_0008.txt` 모두 `### 씬 ...` header 존재
- 여러 화수에서 standalone bracket cue line 존재

또한 DB manuscript read-back에서도 `ep_0001` ~ `ep_0008` 모두 normalization 적용 시 변경이 발생했다. 즉 누수는 txt mirror만이 아니라 authoritative manuscript content에도 들어가 있다.

## 4. Safe Patch Boundary

최소 blast radius 경계는 `Stage4PostProcessor.process_pass_result()`다.

- 이 시점에는 Writer/Director/validator가 내부 scene scaffold를 이미 활용한 뒤다.
- 이후에는 DB manuscript save와 `drafts/ep_XXXX.txt` export가 연쇄로 일어난다.

따라서 가장 안전한 bounded fix는:

1. 내부 prompt/validator contract는 당장 뒤엎지 않는다.
2. final reader-facing manuscript를 Stage 4 artifact boundary에서 정규화한다.
3. 이후 DB save / txt export / sidecar가 모두 정규화된 텍스트를 사용하게 만든다.

## 5. Patch Decision

이번 bounded patch 방향은 아래로 확정했다.

- `### 씬 N: ...`
  - 첫 씬 header는 제거
  - 이후 씬 header는 `***` 장면 전환 기호로 치환
- standalone bracket cue line
  - `[2024년 12월, 서울 외곽의 좁은 원룸]`
  - `[시간: 정오 / 장소: 본가 응접실]`
  - 같은 라인은 bracket을 벗기고 plain cue line으로 정규화
- 과도한 blank line은 축소

이 방식은 내부 씬 분할 사고는 유지하면서 reader-facing AI 메타 느낌만 제거한다.

## 6. Current Run Constraint

조사 시점에 `python main_a.py` live process가 살아 있었다.

- 따라서 이번 턴에서는 `project_data.db`나 현재 `projects/0_1/drafts/*.txt`를 즉시 backfill하지 않는다.
- 이번 턴의 realization 범위는 `코드 patch + regression + canonical docs`까지로 제한한다.
- existing manuscript/draft backfill은 live run 종료 후 safe edit window에서 수행해야 한다.

## 7. Survey Verdict

판정: `system-contract leak`

- primary cause: writer/checker contract + missing final-stripper
- secondary cause: meta validator blind spot
- non-cause: scene count being "exactly 4"

## 8. Recommended Execution

1. Stage 4 post-processor에 reader-facing normalization 삽입
2. regression tests로 DB save / draft export carry 확인
3. live run 종료 후 `0_1` manuscripts authoritative backfill + draft export sync
4. next fresh Stage 4 pass에서 header leak 재발 여부 확인

## 9. 3-Pass Audit Note

- Pass 1: source contract and artifact leakage evidence 확인
- Pass 2: patch boundary를 prompt/validator가 아닌 Stage 4 sink로 제한
- Pass 3: active run guardrail 반영 여부 재확인

Confidence: 0.98
