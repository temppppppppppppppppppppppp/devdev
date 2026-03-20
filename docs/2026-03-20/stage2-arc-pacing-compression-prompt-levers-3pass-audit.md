Date: 2026-03-20
Status: final
Document Type: focused 3-pass audit
Topic: Stage 2 arc pacing compression prompt-first intervention
Scope:
- Stage 2 Arc `ep_count` ownership
- Stage 2 Arc prompt/control surfaces that can influence pacing without hardcoding `-1화`
- prompt-first recommendation order for "아이템이 적을수록 늘어지는 느낌" 문제
Non-Goals:
- live code patch
- Stage 3/4 pacing policy
- treatment block redesign
- execution SSOT or roadmap production

Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: large active workspace; hotspots include Stage2/3/4 agent files, geuldobi-desktop, tests, docs/2026-03-19, docs/2026-03-20`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Temp Queue:
- `docs/temp/` active execution mirrors: none
- `docs/temp/README.md` only

Evidence Basis:
- [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py)
- [arc_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/arc_ensemble.py)
- [constraint_compiler.py](C:/Users/User/Desktop/글도비/modules/domain/agents/constraint_compiler.py)
- [ensemble.yaml](C:/Users/User/Desktop/글도비/config/prompts/ensemble.yaml)

Confidence:
- Estimated confidence after 3-pass audit: 96%

## 1. Question

사용자 질문은 다음이다.

- Stage 2에서 Arc가 화수를 잡을 때 조금 더 급하게 갈 수 있는가
- 아이템/보상/실물 사건이 적은 블록에서 밀도가 낮아져 늘어지는 느낌이 있다
- 단순 `ep_count - 1` 하드코딩보다 먼저 시도할 수 있는 prompt적 해결이 있는가

이 문서는 그 질문에 대해 live 코드 기준으로 `ownership`, `prompt levers`, `추천 개입 순서`만 정리한다.

## 2. Pass 1 - Live Ownership Inventory

### 2.1 `ep_count`는 현재 Python이 먼저 결정한다

현재 Stage 2 Arc의 화수는 LLM이 자율 결정하는 구조가 아니다.

- [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py) `_determine_ep_count()`는 `curr_block`의 텍스트 길이와 문장 수를 보고 `3~6화`를 고른다.
- 같은 함수에서 `tension_level >= 8`이면 `+1화`, `tension_level <= 3`이면 `-1화` 보정이 들어간다.
- [four_phase_arc_generator.py](C:/Users/User/Desktop/글도비/modules/domain/agents/four_phase_arc_generator.py) `generate()`는 이 결과를 받아 `ArcEnsemble.generate_ensemble(... ep_count=...)`로 넘긴다.
- [arc_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/arc_ensemble.py) `generate_ensemble()`는 전달받은 `ep_count`를 그대로 `ep_end` 계산과 tactical length validation에 사용한다.

즉 현재 문제는 "LLM이 화수를 너무 느슨하게 잡는다"보다, 더 정확히는 아래에 가깝다.

- Python이 먼저 화수를 고른다
- 그 뒤 prompt는 같은 화수 안에서 얼마만큼 급하게 압축할지에 대한 명시가 약하다

### 2.2 현재 prompt는 `밀도 압축`보다 `구조 충족`에 더 가깝다

현재 Arc prompt는 이미 많은 블록 정보를 받고 있다.

- [arc_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/arc_ensemble.py) 는 `curr_block`, `block_event_guard`, `genre_ext_guide`, `extended_block_guide`, `vol_strategy`, `assets`, `constraint_block`, `prev_arc_context`를 모두 `ENSEMBLE_ARC_PROMPT`에 주입한다.
- [ensemble.yaml](C:/Users/User/Desktop/글도비/config/prompts/ensemble.yaml) 에는 다음과 같은 강한 규칙이 이미 있다.
  - 각 화 최소 변화 요구
  - 준비만 하는 화 금지
  - 다른 블록 사건을 당겨 쓰지 말 것
  - 현재 블록 사건을 더 세밀하게 심화하라
  - tactical_doc 최소 분량 강제

하지만 지금 prompt에는 사용자가 원하는 종류의 지시가 약하다.

- "아이템/보상/사건 자원이 적을수록 화수를 느슨하게 쓰지 말고 각 화의 사건 밀도를 높이라"
- "idle beat, 반복 정리, 상황 설명 비중을 줄이고 사건 진행/회수 비중을 높이라"
- "같은 화수라도 episode당 최소 1개 이상의 불가역적 변화나 회수 진전이 있어야 한다"

즉 현재 prompt는 `형식적 사건 분할`은 강하지만, `저자원 블록에서의 압축 페이싱`은 직접적으로 말해 주지 않는다.

## 3. Pass 2 - Semantic Classification

### 3.1 이 문제를 바로 `-1화`로 푸는 것은 의미가 섞인다

단순 `ep_count - 1`은 아래 두 문제를 하나로 섞는다.

1. 화수 자체가 과하게 많다
2. 같은 화수 안에서도 tactical_doc가 느슨하게 전개된다

사용자 불만은 2번에 더 가깝다.

- 아이템이 적다
- 보상/획득 포인트가 적다
- 그래서 episode가 길게 늘어진다

이건 반드시 "화수를 줄여야만" 생기는 문제가 아니다.

- 같은 4화라도 더 급하게 쓸 수 있다
- 같은 3화라도 느슨하게 쓰면 여전히 늘어진다

따라서 첫 개입은 `ep_count` 자체보다 `같은 ep_count 안에서 tactical density를 높이는 prompt`가 더 정확하다.

### 3.2 prompt-first 개입에 가장 적합한 삽입 위치

live 코드상 prompt-first 개입 위치는 세 군데가 보인다.

#### A. 1순위: `arc_ensemble.py`의 `extended_block_guide`

가장 추천하는 위치다.

이유:

- `curr_block`의 확장 필드를 그대로 묶어 LLM에 설명하는 구간이다
- 이미 `foreshadow`, `callback`, `emotional_beat`, `tension_level` 같은 block-level 설계 의도를 tactical_doc로 내리라는 문구가 있다
- 여기서 `low item / low reward / low prop density`일 때만 추가 pacing instruction을 넣기 쉽다

추천되는 추가 의미:

- 사건 수가 적은 블록일수록 장면 전환/설명으로 늘리지 말 것
- 각 화마다 적어도 하나의 실질 진전, 회수, 관계 변화, 위험 증폭, 손익 변화 중 하나를 만들 것
- 동일 정보 재서술과 정서 반복을 줄일 것
- "준비", "관찰", "결심"만으로 한 화를 쓰지 말 것

#### B. 2순위: `arc_ensemble.py`의 `block_event_guard`

이 위치도 유효하다.

이유:

- 현재 블록의 `context / event_villain / solution / reward`만 추출해 사건 경계를 명시하는 구간이기 때문이다
- 여기에 "reward가 빈약하거나 solution/event 자원이 적을수록 남은 사건 자원을 더 조밀하게 배치하라"는 식의 짧은 운영 지시를 덧붙이기 좋다

단, 이 위치는 "무슨 사건을 써야 하는가"에는 강하지만 "얼마나 급하게 써야 하는가"를 길게 설명하기엔 공간이 작다.

#### C. 3순위: `config/prompts/ensemble.yaml`의 `서사 흥미 설계` 섹션

이 위치는 프롬프트 원문 차원에서 일반 규칙을 넣기 좋다.

하지만 이 위치만 단독으로 쓰면 `low item density` 같은 조건부 정보를 계산하지 못한다. 따라서 실제 patch 시에는 아래 조합이 더 낫다.

- Python에서 density signal 계산
- `extended_block_guide` 또는 별도 `{pacing_density_guide}` 변수로 주입
- prompt 원문은 그 변수를 소비

### 3.3 `constraint_compiler.py`는 1차 개입 위치로는 덜 적합하다

[constraint_compiler.py](C:/Users/User/Desktop/글도비/modules/domain/agents/constraint_compiler.py)는 현재 의미상 아래 역할이 강하다.

- 중복 획득 금지
- inherited state 고정
- must-not-do checklist

이 파일에 pacing compression까지 얹을 수는 있지만, 현재 책임과 조금 어긋난다. 첫 개입 위치로는 `ArcEnsemble prompt assembly`가 더 자연스럽다.

## 4. Pass 3 - Recommended Execution Shape

### 4.1 추천 결론

추천은 다음 순서다.

1. `ep_count - 1` 하드코딩은 지금 하지 않는다
2. 먼저 `ArcEnsemble` prompt에 `low-density pacing compression` 지시를 조건부로 추가한다
3. 그 효과를 본 뒤에도 여전히 느리면, 그다음에만 `_determine_ep_count()` 휴리스틱에 `item/reward density`를 보조 신호로 넣는다

### 4.2 추천 patch shape

가장 좋은 1차 patch shape는 아래와 같다.

- 파일:
  - [arc_ensemble.py](C:/Users/User/Desktop/글도비/modules/domain/agents/arc_ensemble.py)
  - [ensemble.yaml](C:/Users/User/Desktop/글도비/config/prompts/ensemble.yaml)
- 방법:
  - `curr_block.content.reward`, `genre_ext`, `reward`, `solution`, `items`, `capital_after` 등에서 `low-density` 신호를 좁게 계산
  - 별도 guide 문자열을 만든다
  - prompt에 다음 의미를 넣는다

예시 의미:

- 이번 블록은 보상/아이템 자원이 적으므로 화수를 느슨하게 채우지 말라
- 각 화는 설명보다 사건 진행 비중이 커야 한다
- 각 화마다 최소 하나의 실질 변화가 있어야 한다
- idle beat와 중복 감정 서술을 줄이고, callback/foreshadow 회수 밀도를 올려라

### 4.3 왜 이 순서가 ROI가 높은가

- current ownership을 뒤집지 않는다
- Stage 2 전체 ep_count policy를 흔들지 않는다
- user complaint와 직접 맞닿은 지점을 먼저 친다
- 효과가 좋으면 `ep_count` 휴리스틱은 건드리지 않아도 된다

## 5. Recommended Next Step

다음 작업은 bounded patch로 아래 1건이 적합하다.

- `ArcEnsemble low-density pacing compression guide` 추가

권장 범위:

- Python 하드코딩 `-1화` 금지
- `_determine_ep_count()`는 일단 유지
- prompt assembly에만 조건부 density guide를 추가
- 회귀는 Stage 2 prompt contract 수준으로 시작

## 6. 3-Pass Audit Summary

### Pass 1. Structure and Scope

- 질문 범위를 `Stage 2 arc pacing`으로 한정했다
- 코드 수정/실행 SSOT/roadmap은 제외했다
- ownership과 prompt lever를 분리해 문서 구조를 잡았다

### Pass 2. Evidence and Consistency

- `ep_count` 결정권이 Python에 있다는 점을 live 코드로 확인했다
- prompt 입력면과 actual template key를 live 코드로 대조했다
- `constraint_compiler`가 pacing보다는 prohibition/inherited-state 계층이라는 점을 확인했다

### Pass 3. Execution and Readability

- 바로 적용 가능한 권장 순서를 `prompt-first -> observe -> heuristic later`로 압축했다
- 사용자가 요청한 "`-1화` 하드코딩보다 prompt적 해결" 질문에 바로 답할 수 있게 했다
- 다음 bounded patch 후보를 한 줄로 닫았다

## 7. Final Conclusion

현 구조에서 Stage 2 Arc의 느린 페이싱은 우선 `ep_count`보다 `prompt density guidance` 문제로 보는 게 맞다.

따라서 추천은 다음 한 문장으로 요약된다.

- `화수를 먼저 줄이지 말고, 저아이템/저보상 블록은 같은 화수 안에서도 더 급하고 촘촘하게 쓰라고 Arc prompt를 먼저 강화하라`
