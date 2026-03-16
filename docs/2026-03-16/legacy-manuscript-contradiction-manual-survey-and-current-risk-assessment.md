<!-- [추적필요] -->
<\!-- [추적필요] -->
Date: 2026-03-16
Status: final
Canonical Path: `docs/2026-03-16/legacy-manuscript-contradiction-manual-survey-and-current-risk-assessment.md`
Baseline Commit: `d6c81c1976d9812d447c2a78e2aeb36f7aed666a`
Baseline Dirty Summary: `dirty: desktop icon/version files, stage4/continuity runtime modules and tests, project runtime artifacts/db, opus memo edits, and untracked 2026-03-16 follow-up docs`
Scope: `legacy project manuscript contradiction manual-survey plan`, `LLM-limit vs engineering-fix split`, `current codebase similar-risk assessment`
Evidence Artifact: `docs/2026-03-16/legacy-manuscript-contradiction-manual-survey-and-current-risk-assessment-evidence.txt`
Confidence: `96%`

# Legacy Manuscript Contradiction Manual Survey And Current Risk Assessment

## 1. Purpose

이 문서는 두 가지를 동시에 정리한다.

1. 이전 프로젝트에 남아 있는 실물 원고를 사람이 직접 읽으며 모순을 찾기 위한 수동 전수조사 계획
2. 그 모순이 어디까지는 `LLM 자체 한계`이고, 어디부터는 `현 코드에서 더 줄일 수 있는 문제`인지에 대한 분리 판단

핵심 전제는 단순하다. `DB 행`이나 `로그 요약`만으로는 충분하지 않다. 실물 Stage 4 원고 txt와 DB `manuscripts`, Stage 4 `selected/rejected/patched` artifact, Stage 3 blueprint, `episode_bibles`, `director_selections`를 함께 봐야 한다.

## 2. Confirmed Legacy Artifact Surface

실제 조사 가능한 실프로젝트 표면은 아래 네 개다.

| Project | DB manuscripts | Stage4 final/patched artifacts | Stage4 selections | Stage4 attempts | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| `0` | 2 | 2 | 2 | 2 | 소규모 초기 실험이지만 실물 원고 존재 |
| `000` | 6 | 6 | 11 | 11 | rejected / patched history가 남아 있어 비교 가치 큼 |
| `00_20260314` | 2 | 2 | 3 | 3 | short bounded set |
| `00_260315` | 11 | 11 | 14 | 14 | 가장 큰 legacy set |

실물 확인도 이미 샘플 수준이 아니라 본문 decode까지 직접 확인됐다.

- `projects/000/logs/artifacts/stage4/ep_0004/attempt_03/patched_after_fix__A.txt`
- `projects/000/logs/artifacts/stage4/ep_0005/attempt_04/final_manuscript__C.txt`
- `projects/00_260315/logs/artifacts/stage4/ep_0001/attempt_01/final_manuscript__C.txt`
- `projects/00_260315/logs/artifacts/stage4/ep_0004/attempt_01/patched_after_fix__A_InPlace.txt`

즉, 이 조사는 `남아 있으면 좋겠다` 수준이 아니라 `실제 원고 본문이 이미 확인된 상태`에서 시작할 수 있다.

## 3. Manual Survey Method

이번 조사는 자동 요약이 아니라 `사람이 실제로 읽고 판정하는 방식`이어야 한다. 따라서 조사 절차를 아래처럼 고정한다.

### 3.1 Scope Freeze

- 포함: `projects/0`, `projects/000`, `projects/00_20260314`, `projects/00_260315`
- 제외: `test`, `demo`, `bounded_*`, `기록용`, `MagicMock`
- 조사 단위: `final_manuscript`와 `patched_after_fix` 원고 전편

### 3.2 Episode Packet

에피소드 하나를 완료로 치기 위한 최소 패킷은 다음 네 묶음이다.

1. `artifact truth`
   - 파일 존재
   - UTF-8 decode 성공
   - chars / lines
   - final / patched / rejected lineage
2. `metadata truth`
   - DB `manuscripts` 본문과 artifact 일치 여부
   - `director_selections`, `stage_attempts`, `artifact_path`, `selection_reason` 연결
3. `narrative truth`
   - 인물 상태
   - 시간선
   - 장소 이동
   - 관계 변화
   - 부상 / 회복
   - 소지품 / 자산 / 수치
   - 목표 / 지식 / 복선 회수
4. `persistent facts sheet`
   - 다음 화 판정 때 다시 사용할 누적 사실 목록

### 3.3 Contradiction Decision Template

모순 후보는 반드시 아래 템플릿으로만 적는다.

- `Statement A`: 어디 문서/원고/DB에서 나온 사실인지
- `Statement B`: 무엇이 어디와 충돌하는지
- `Can coexist?`: 시점 차이, 오인, 의도적 거짓말, 패치 정정으로 설명 가능한지
- `Why not`: 그 설명이 왜 안 먹히는지
- `Final class`: `hard contradiction` / `soft inconsistency` / `ambiguity` / `resolved-by-patch`

### 3.4 Anti-Lazy Rules

- 샘플 몇 줄만 읽고 판정 금지
- 각 에피소드는 final 또는 patched 본문 전체 독해 후에만 완료 처리
- 모순 1건당 최소 `두 개 이상의 실물 근거` 필요
- “문제 없음” 판정도 continuity check 세 개 이상을 거쳐야 함
- 애매한 것은 모순으로 부풀리지 말고 `ambiguity`로 분리
- 프로젝트 1차 독해 종료 후 `red-team pass` 1회 필수

## 4. LLM Limits Vs Engineering-Fixable Problems

이번 legacy 원고 모순 조사에서 나올 문제는 모두 같은 종류가 아니다. 아래처럼 갈라서 봐야 한다.

### 4.1 Mostly LLM-Limit Problems

아래는 시스템을 더 보강해도 완전히 없애기 어려운 부류다.

1. 장기 서사 기억 압축 한계
   - 현재 Stage 4는 최근 30화 full text와 그 이전 tiered summary를 쓰고, 이후에는 trimming도 발생한다.
   - 코드 근거: `modules/core/stage4_context_builder.py:1772-1895`, `modules/core/stage4_context_builder.py:1448-1515`
   - 의미: 수십 화 전의 미묘한 감정선, 암시, 관계 온도 차이는 압축 과정에서 흐려질 수 있다.

2. 비결정적 품질 판정
   - self-consistency는 3표 다수결이고, 애매한 구간에서 soft-margin + random 경계 확장이 들어간다.
   - 코드 근거: `modules/validation/validation_orchestrator.py:229-242`, `modules/validation/validation_orchestrator.py:745-796`
   - 의미: 미세한 narrative contradiction은 반복 평가마다 판정이 흔들릴 수 있다.

3. 서브텍스트/동기/정서 연속성
   - 어떤 변화가 “설명된 성장”인지 “갑작스러운 캐붕”인지는 구조적 상태만으로 판정하기 어렵다.
   - 현재 validator들이 이 부분을 일부 보지만, 최종 판단은 여전히 모델 해석에 의존한다.

### 4.2 Engineering-Fixable Or Reducible Problems

아래는 지금 코드 구조를 더 고치면 유의미하게 줄일 수 있는 부류다.

1. continuity failure가 hard stop이 아닌 advisory로 흘러가는 문제
   - 코드 근거: `modules/validation/validation_orchestrator.py:395-409`, `modules/validation/validation_orchestrator.py:678-705`
   - 현재는 `continuity failed -> advisory -> bounded score penalty -> PASS/CONDITIONAL_PASS 가능` 구조다.

2. `prev_hud` 주입 의존
   - `prev_hud`가 없으면 continuity validator는 degraded fail을 내지만, DB에서 직접 복구하지는 못한다.
   - 코드 근거: `modules/validation/continuity_validator.py:117-145`, `modules/validation/continuity_validator.py:227-239`, `modules/core/stage4_interview_round.py:3942-3955`

3. lookback window와 truncation의 구조적 제한
   - Director history check는 최대 30화, post-select continuity는 bounded recent context, cache merge도 화당 문자 수 제한이 있다.
   - 코드 근거: `modules/domain/agents/director.py:57-58`, `modules/domain/agents/director_continuity.py:446-461`, `modules/domain/agents/director_continuity.py:750-859`, `modules/domain/agents/base_agent.py:2135-2137`

4. candidate prevalidation이 실제 filtering이 아니라 warning accumulation인 문제
   - 코드 근거: `modules/core/stage4_interview_round.py:2449-2552`
   - 현재는 후보에 continuity/blocking 문제가 있어도 Director 판단으로 넘긴다.

5. prompt size gate에 의한 중간 맥락 탈락
   - 코드 근거: `modules/domain/agents/base_agent.py:305-315`, `modules/core/constants.py:145-165`
   - 길어진 context는 중간이 잘려 head/tail 위주만 남을 수 있다.

즉 결론은, legacy 원고 모순은 `LLM이라 원래 그런 것`으로만 돌리면 안 된다. 현재 구조상 더 줄일 수 있는 시스템성 문제도 분명히 있다.

## 5. Current Codebase: Similar-Risk Surfaces

현재 코드에서도 유사 문제가 다시 날 수 있는 표면은 아래가 핵심이다.

### 5.1 Advisory-Only Continuity Gate

가장 중요한 위험이다. continuity 위반이 감지돼도 즉시 hard reject가 아니라 advisory와 감점으로 누그러진다.

- `modules/validation/validation_orchestrator.py:395-409`
- `modules/validation/validation_orchestrator.py:678-705`

따라서 `continuity violation exists`와 `runtime actually blocks bad manuscript`는 같은 말이 아니다.

### 5.2 Runtime HUD Dependency Instead Of Durable Truth Reconstruction

continuity validator는 `prev_hud`가 없으면 degraded fail을 반환하지만, 그 truth를 DB manuscript / artifact 본문에서 복원하지는 않는다.

- `modules/validation/continuity_validator.py:117-145`
- `modules/validation/continuity_validator.py:227-239`
- `modules/core/stage4_interview_round.py:3942-3955`

이 말은 곧, runtime HUD가 약하거나 누락된 상태에서는 연속성 검증이 구조적으로 흔들릴 수 있다는 뜻이다.

### 5.3 Long-Range Narrative Compression

최근 화 중심 lookback, summary tier, cache merge budget, smart truncate가 모두 겹친다.

- `modules/core/stage4_context_builder.py:1772-1895`
- `modules/core/stage4_context_builder.py:1448-1515`
- `modules/domain/agents/base_agent.py:2135-2137`
- `modules/core/constants.py:145-165`

이 구조는 `수십 화 전의 뉘앙스 모순`, `서서히 변한 관계 온도`, `중간 화에서만 드러난 제약` 같은 것을 놓치기 쉽다.

### 5.4 Candidate Stage Is Still Warning-Oriented

후보 생성 직후 consistency / blocking / continuity 검사를 해도, 그 결과는 mostly warning과 focus point로 붙는다.

- `modules/core/stage4_interview_round.py:2449-2552`

이건 early filter라기보다 `Director에게 넘기는 메모`에 가깝다.

### 5.5 Current Hardening Already Proves Improvement Is Possible

반대로, 아래 구조들은 “이건 순수 LLM 운빨 문제가 아니라 엔지니어링으로 줄일 수 있다”는 근거다.

1. continuity pins
   - `modules/core/stage4_orchestrator.py:387-446`
   - 이전 published text를 반영해 blueprint를 보정한다.
2. stage2 failure context injection
   - `modules/core/stage4_context_builder.py:1669-1736`
   - `modules/core/stage4_context_builder.py:2193-2197`
   - 이전 실패 사유와 retry directive를 Stage 4 앞단에 재주입한다.
3. post-select fail-closed checks
   - `modules/core/stage4_interview_round.py:2863-2965`
   - post-select continuity/history conflict는 PASS를 REJECT로 강등할 수 있다.
4. repeated contradiction -> blueprint regeneration
   - `modules/core/stage4_orchestrator.py:1178-1335`
   - 반복되는 logic error와 contradiction type streak를 구조 문제로 승격시킨다.
5. stage attempt persistence
   - `modules/core/db_manager.py:3161-3185`
   - `modules/core/db_manager.py:3274-3360`
   - `modules/core/stage4_interview_round.py:4937-5039`
   - artifact path, rationale, retry directives가 남기 때문에 사후 audit 품질을 더 끌어올릴 수 있다.

## 6. Operational Conclusion

이번 legacy manuscript contradiction 조사는 반드시 `수동 실물 독해` 기반으로 가야 한다. 이유는 두 가지다.

1. legacy 원고의 진짜 모순은 실물 txt를 읽지 않으면 식별할 수 없는 narrative truth 층에 많이 걸려 있을 가능성이 높다.
2. 현재 코드도 일부는 개선됐지만, 아직 `bounded context`, `advisory-first continuity`, `runtime HUD dependency`, `LLM judgement variability` 때문에 유사 문제가 재발할 수 있다.

따라서 후속 조사 문서는 아래 원칙으로 가는 것이 맞다.

- legacy contradiction finding은 `실물 txt + DB manuscripts + Stage4 selected/rejected/patched + blueprint + episode_bibles` 묶음으로 판정
- 모순 분류는 `hard contradiction / soft inconsistency / ambiguity / resolved-by-patch`
- 각 finding은 `LLM-limit`인지 `engineering-fixable`인지 별도로 태깅
- current runtime recurrence risk는 code anchor로 따로 기록

## 7. Recommended Next Outputs

다음 산출물 순서는 아래가 맞다.

1. `project-level manuscript truth survey`
   - project `0`
   - project `000`
   - project `00_20260314`
   - project `00_260315`
2. `global contradiction ledger`
   - finding별 severity
   - evidence pair
   - LLM-limit vs engineering-fix tag
3. `current-code recurrence memo`
   - 이번 문서의 risk surfaces를 action candidate로 정리
4. action-bearing finding이 충분히 모이면 그때만 execution SSOT / roadmap으로 승격

지금 단계의 결론은 명확하다. `실물 원고 전수조사`는 가능하고, `현재 코드에도 유사 문제는 여전히 발생 가능`하다. 다만 그 원인을 전부 LLM 탓으로 묶으면 안 되고, 현재 구조에서 더 줄일 수 있는 부분도 분명히 존재한다.
