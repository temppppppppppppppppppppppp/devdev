# Stage3 Blueprint First-Pass Structural Survey

Date: 2026-04-10
Status: final
Canonical Path: `docs/2026-04-10/stage3-blueprint-first-pass-structural-survey.md`
Baseline Commit: `e597a7bf4836dab71547e350b015f6658a1cfb03`
Baseline Dirty Summary: `dirty: 46 tracked_modified, 29 untracked; hotspots: docs/, modules/, tests/, material_ssot/, scripts/, secrets/`
Scope: `Stage3 ep1 blueprint가 "처음부터 잘 안 써지는" 구조적 이유 survey`
Confidence: `96%`

## 1. Intent

이번 survey의 목표는 `모델이 못 쓴다` 수준의 인상비평이 아니라, 현재 Stage3 BP 파이프라인이 첫 시도부터 높은 품질의 blueprint를 안정적으로 만들기 어렵게 만드는 구조적 요인을 코드/프롬프트/런타임 증거 기준으로 분해하는 것이다.

이 문서는 survey-only 산출물이다. 이번 턴에서는 실행 SSOT, roadmap, temp mirror, queue-state, ClickUp 상태를 변경하지 않는다.

## 2. Evidence Basis

- `projects/00_000/logs/session_20260410_143423.log`
- `projects/00_000/logs/session_20260410_160214.log`
- `projects/00_000/logs/session/llm_io.jsonl`
- `modules/domain/agents/unified_blueprint_validator.py`
- `modules/domain/agents/three_phase_blueprint_runtime.py`
- `modules/domain/agents/director_ensemble.py`
- `config/settings/validation.yaml`

## 3. Finding Summary

결론부터 말하면, 현재 Stage3 BP가 처음부터 잘 안 나오는 1순위 원인은 단순 모델 품질이 아니다. 더 큰 원인은 아래 네 축의 구조 충돌이다.

1. `episode-local hard constraint`와 `future-carryover/fidelity hint`가 서로 충돌한다.
2. 길이/점수 기준이 validator, Director compare, runtime quality gate 사이에서 일치하지 않는다.
3. Python prevalidation이 advisory처럼 보이지만 실제로는 first-pass repair를 강제하는 쪽으로 작동한다.
4. prompt pack이 ep1 생성 태스크에 비해 과적재되어 있고, repair feedback도 canonical anchor가 약하다.

추가로, 이 구조 위에서 `PASS_WITH_FIX -> patch -> re-audit` 루프가 first-pass 성과를 훼손하면서 "처음부터 못 썼다"처럼 보이게 만드는 2차 문제가 있다.

## 4. Structural Findings

### Finding 1. Ep1 hard-stop과 future relationship requirement가 충돌한다

Stage3 첫 후보 prompt는 ep1에 대해 `제1화 이후 모든 에피소드 사건/NPC/전개를 이번 화에서 소비하거나 언급하면 즉시 REJECT`라고 강하게 묶는다. 동시에 같은 prompt 안에 `Arc Semantic Carryover`, 미래 복선, 관계변화 요약, tracking_slots, scene engines가 함께 들어간다. 실제 ep1 후보 prompt에는 아버지/형들 관련 future carryover와 복선이 같이 실려 있다. [llm_io.jsonl](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session/llm_io.jsonl#L24)

그런데 validator는 `arc_data.state_constraints.relationship_changes`에 들어 있는 NPC가 integrated scenario에 한 명도 안 나오면 바로 `intent 불일치: Arc 관계 변화 NPC 3명 blueprint 미언급`을 낸다. 이 체크는 episode-local gating 없이 전체 relationship_changes를 그대로 읽는다. [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L970)

즉 시스템은 ep1에게 동시에 이렇게 말하고 있다.

- 미래 화 내용을 미리 소비하지 마라
- 그런데 future relationship change NPC는 blueprint에 등장시켜라

이 충돌 때문에 모델은 ep1 순도를 지키면 fidelity warning을 맞고, fidelity warning을 피하려고 future NPC를 앞당기면 hard constraint에 가까운 오염 위험을 진다.

### Finding 2. 길이/점수 기준이 세 군데에서 다르다

현재 Stage3 구조 기준은 세 겹으로 갈라져 있다.

- blueprint validator 최소 분량: `800자` [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L39)
- Director compare 즉시 탈락 기준: `1000자 미만` [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py#L2021)
- runtime quality gate: `PASS score < 90`이면 강제 REJECT [three_phase_blueprint_runtime.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/three_phase_blueprint_runtime.py#L1179) [validation.yaml](/c:/Users/wjjo/Desktop/글도비/config/settings/validation.yaml#L34)

Director compare rubric 자체는 `80~89`를 pass band로 둔다. [director_ensemble.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/director_ensemble.py#L2028)

실제 런에서도 이 불일치가 그대로 보인다.

- 후보는 `1000자 미만` 때문에 즉시 탈락 취급된다. [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L262)
- 다른 구간에서는 `760자 < 800자`가 major structure issue로 잡힌다. [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L556)
- `83 PASS`를 받아도 Stage3 runtime이 `90` 미만이라 강제 REJECT 한다. [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L553)

즉 "꽤 잘 쓴" first-pass도 구조상 final PASS가 아니라 repair loop 진입 후보가 된다.

### Finding 3. Python prevalidation은 advisory처럼 보이지만 실제로는 binding repair pressure다

validator는 binding prevalidation issue가 있으면 plain `PASS`를 `PASS_WITH_FIX`로 승격한다. [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L304)

또 compare path에서 candidate별 Python warnings와 `quality_risk`를 ensemble meta에 붙이고, Director compare 이후에도 selected candidate advisory의 `quality_risk`를 다시 verdict에 섞는다. [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L430) [unified_blueprint_validator.py](/c:/Users/wjjo/Desktop/글도비/modules/domain/agents/unified_blueprint_validator.py#L503)

로그에서도 Stage3 audit 때마다 `Python findings forwarded: 2`가 뜬다. [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L471)

즉 이름은 advisory지만, 현재 구조에서는 first-pass candidate가 structural/fidelity/density 휴리스틱을 조금만 어겨도 plain PASS로 종료되기 어렵다.

### Finding 4. Prompt pack이 ep1 생성 작업에 비해 과적재되어 있다

ep1 후보 prompt에는 단순한 `이번 화 목표`만 있는 게 아니다. 실제 prompt 안에 아래가 같이 들어간다.

- hard stop line
- expected continuity
- advisory 상태 변경 요약
- Arc Semantic Carryover
- future foreshadow
- tracking_slots
- mandatory scene engines
- observer hierarchy
- anti-AI/style guide
- Arc 1~6 개요와 genre_ext

실제 evidence는 `llm_io.jsonl`의 ep1 candidate prompt에서 보인다. [llm_io.jsonl](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session/llm_io.jsonl#L24)

retry로 갈수록 prompt 부담은 더 커진다.

- patch round prompt_len `5594` [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L272)
- 다음 retry prompt_len `7757` [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L454)
- 이전 aborted run에서는 `14860`까지 불어난 병렬 재생성도 있었다. [session_20260410_143423.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_143423.log#L649)

이 구조는 모델이 ep1 scene authority를 쓰기보다, 미래 pipeline pressure와 style/rule bookkeeping을 동시에 감당하게 만든다. 그 결과 가장 먼저 잘리는 것이 분량, 구체 앵커, 관계 NPC 언급이다.

### Finding 5. Repair feedback가 canonical anchor 없이 내려와 invented-name drift를 유발한다

patch prompt는 `형들이나 전 아내 등 핵심 인물들의 이름을 직접 언급`하라고 지시한다. [llm_io.jsonl](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session/llm_io.jsonl#L70)

그런데 같은 라인에서 실제 patch 결과는 `한시혁`, `한시준`, `서유라` 같은 이름을 새로 만들어 넣는다. [llm_io.jsonl](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session/llm_io.jsonl#L70)

반면 current arc constraint 쪽 관계변화 표면은 `한정호`, `한태준`, `한태민`을 쓰고 있다. [llm_io.jsonl](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session/llm_io.jsonl#L24)

즉 시스템은 `관계 변화 NPC를 넣어라`는 요구를 canonical entity anchor 없이 내리고 있고, patch layer는 그 빈칸을 invented names로 메운다. 이건 fidelity repair가 아니라 새 drift를 생산하는 구조다.

### Finding 6. "처음부터 못 쓴다"는 인상은 repair loop가 first-pass 성과를 무너뜨리면서 더 심해진다

두 fresh run 모두 ep1 first-pass candidate는 꽤 강하게 나온다.

- `후보 3 선택 (PASS_WITH_FIX, 점수: 95)` [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L260)
- `후보 3 선택 (PASS_WITH_FIX, 점수: 95)` [session_20260410_143423.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_143423.log#L259)

문제는 그 다음이다.

- patch re-audit `85 PASS`도 `score < 90`라서 다시 reject loop [session_20260410_143423.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_143423.log#L454)
- later run에서는 `84 -> 83`으로 깎이고 `분량 부족 760자`, `관계 변화 NPC 미언급`으로 재거절 [session_20260410_160214.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_160214.log#L552)
- 한 번은 patch output이 `scene_breakdown` 자체를 날려버렸다. [session_20260410_143423.log](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session_20260410_143423.log#L644)

즉 관찰되는 실패는 `first-pass 생성 실패`라기보다, `좋은 first-pass도 현재 repair/gate 구조 아래서는 안정적으로 살아남지 못한다`가 더 정확하다.

## 5. Secondary Watchlist

`Entity Registry` 품질도 좋지 않다. later audit prompt에는 일반 명사 수준의 토큰이 대량 등록된 polluted registry가 보인다. [llm_io.jsonl](/c:/Users/wjjo/Desktop/글도비/projects/00_000/logs/session/llm_io.jsonl#L71)

다만 이번 survey 기준으로 이것은 Stage3 first-pass 실패의 1차 원인이라기보다, 후속 audit noise와 drift pressure를 키우는 2차 문제로 분류한다.

## 6. Operating Consequence

현재 구조에서 `BP가 처음부터 잘 써지지 않는다`는 판단은 부분적으로 맞지만, 더 정확한 표현은 아래다.

- 모델이 형편없어서가 아니다.
- ep1 local generation contract가 internally clean하지 않다.
- "괜찮은 first-pass"를 final pass로 인정하는 구조가 아니다.
- repair feedback가 canonical anchor가 약해서 local fix가 drift를 낳는다.

즉 first-pass 품질을 올리려면 model retune보다 먼저 contract alignment가 필요하다.

## 7. Recommended Next Patch Order

survey 결과 기준, ROI가 높은 순서는 아래다.

1. `ep-local gating`
   - `relationship_changes`와 future carryover를 현재 화에서 실제로 강제해야 하는 subset으로 줄이기
2. `threshold alignment`
   - `800 vs 1000 vs 90`의 삼중 기준을 한 묶음으로 정렬하기
3. `canonical patch anchors`
   - patch feedback가 canonical NPC 이름/field path를 직접 넘기게 만들기
4. `prompt pack slimming`
   - ep1 first-pass 생성 prompt에서 future investment-track substrate와 repeated policy pack을 줄이기

## 8. Save Gate

- Pass 1: scope/type/path 확인 완료
- Pass 2: evidence/code/log consistency 재확인 완료
- Pass 3: operating consequence와 next patch order 명시 완료
- Confidence gate: `96%`로 final save
