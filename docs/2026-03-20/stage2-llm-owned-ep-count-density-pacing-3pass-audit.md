Date: 2026-03-20
Status: final
Document Type: focused 3-pass audit
Topic: Stage 2 LLM-owned ep_count and high-density pacing
Scope:
- Stage 2 Arc `ep_count` ownership
- current mixed authority between Python and prompt
- prompt-first and ownership-first redesign feasibility
- side-effect surfaces affected by moving `ep_count` judgment to LLM
Non-Goals:
- live code patch
- Stage 3/4 pacing redesign
- treatment block production redesign
- desktop or UI work

Commit State:
- Baseline Commit: `d0fa70f11f9c389182d3a4799e1fd4a4b3db7fc2`
- Baseline Dirty Summary: `dirty: large active workspace; hotspots include Stage2/3/4 agent files, geuldobi-desktop, tests, docs/2026-03-19, docs/2026-03-20`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

Evidence Basis:
- `modules/domain/agents/four_phase_arc_generator.py`
- `modules/domain/agents/arc_ensemble.py`
- `modules/domain/agents/constraint_compiler.py`
- `modules/core/response_schemas.py`
- `modules/core/stage2_validation_pipeline.py`
- `config/prompts/ensemble.yaml`
- `config/prompts/analyst.yaml`
- `tests/test_four_phase_arc_generator.py`
- `tests/test_stage2_pipeline.py`

Source Survey Docs:
- `docs/2026-03-20/stage2-arc-pacing-compression-prompt-levers-3pass-audit.md`

Confidence:
- Estimated confidence after 3-pass audit: 96%

## 1. Intent

이 문서는 다음 질문에 답한다.

- Stage 2 Arc의 `ep_count` 판단을 Python이 아니라 LLM이 맡는 구조가 맞는가
- 단순 `-1화` 보정 대신, 더 높은 밀도 지향을 구조적으로 넣을 수 있는가
- 그렇게 바꿀 경우 어떤 코드/스키마/검증면이 같이 흔들리는가

결론부터 말하면, 추천은 아래와 같다.

- `ep_count` 판단은 장기적으로 LLM이 맡는 구조가 맞다
- Python은 판단자가 아니라 `signal collector + guard + normalizer`로 내려가는 것이 맞다
- 단, 현재 구조는 이미 `Python 추천 + Prompt 자유 결정 문구`가 섞여 있는 혼합 상태라서, 바로 ownership을 분리하지 않으면 오히려 더 헷갈린다

## 2. Pass 1 - Live Ownership Inventory

### 2.1 현재 Stage 2는 이미 "혼합 ownership" 상태다

한 줄로 말하면, 현재는 Python이 사실상 먼저 정하지만 prompt는 여전히 LLM에게 고르는 척을 시킨다.

#### Python이 먼저 하는 일

- `modules/domain/agents/four_phase_arc_generator.py`
- `_determine_ep_count()`가 `curr_block`의 텍스트 길이, 문장 수, `tension_level`을 보고 `2~6화` 추천을 만든다
  - `generate()`는 그 결과를 `ep_count, pacing_reason`으로 받아 로그를 남긴다
  - 이후 `ArcEnsemble.generate_ensemble(..., ep_count=ep_count)`로 넘긴다

즉 Stage 2의 실제 출발점은 이미 Python heuristic이다.

#### prompt가 여전히 하는 일

- `config/prompts/ensemble.yaml`
- output schema 설명에는 아직 `"ep_count": "3~6 중 결정"`이 들어 있다
  - tactical density와 ep_count 적합성도 LLM이 고려하라고 적혀 있다
- `modules/domain/agents/arc_ensemble.py`
  - prompt에 `ep_start`, `ep_end`를 이미 계산된 값으로 넣는다
  - 그런데 output schema 설명은 여전히 LLM이 `ep_count`를 결정하는 것처럼 적혀 있다

즉 현재 구조는 아래처럼 섞여 있다.

- Python: ep_count를 사실상 먼저 결정
- Prompt: ep_count를 여전히 LLM이 결정하는 듯이 설명
- Runtime: 둘 사이의 mixed authority를 명시적으로 정리하지 않음

이 상태는 "누가 pacing을 소유하는가"가 흐릿해서 장기적으로 좋지 않다.

### 2.2 이미 analyst 계열에는 LLM-owned pacing 흔적이 있다

- `config/prompts/analyst.yaml`
- `modules/domain/agents/analyst_prompts.py`
- `modules/domain/agents/analyst.py`

여기에는 이미 아래 개념이 존재한다.

- `pacing_decision`
- `chosen_pacing`
- `ep_count_suggestion`
- `LLM이 사건 밀도에 맞게 ep_count를 직접 결정`

즉 `LLM이 pace mode를 고르고 ep_count를 정한다`는 발상 자체는 workspace에 없는 개념이 아니다. 현재 Stage 2 Arc mainline에 그 ownership이 끝까지 관철되지 않았을 뿐이다.

## 3. Pass 2 - Semantic Classification

### 3.1 이 문제는 숫자 문제가 아니라 판단 문제다

사용자 문제의식은 정확하다.

- 아이템이 적다
- reward가 약하다
- 실제 사건 자원이 적다
- 그래서 화가 늘어진다

이건 단순 길이 계산보다 `서사 밀도 판단`에 가깝다.

즉 아래와 같은 질문은 Python보다 LLM이 더 잘한다.

- 이 블록은 4화를 유지하되 더 급하게 써야 하는가
- 5화로 가도 되는 블록인가
- 아이템은 적지만 감정/위험/관계 전개가 충분해서 4화가 맞는가
- reward는 약하지만 callback/foreshadow 회수 밀도로 버틸 수 있는가

따라서 `ep_count` 자체를 포함한 pacing 판단은 원칙적으로 LLM 쪽이 더 적합하다.

### 3.2 다만 "완전 자유 LLM"으로 바로 가면 안 된다

LLM이 판단을 맡는 것이 맞다고 해서, guard 없이 전부 맡기는 건 위험하다.

이유:

- ep_count가 validation/beat count/min tactical length와 연결된다
- `ep_end = ep_start + ep_count - 1`은 downstream에서 기준축으로 많이 쓰인다
- `stage2_validation_pipeline`은 beat 수가 `ep_count`보다 적으면 REJECT한다
- state service와 later context builder도 `ep_count`를 신뢰한다

즉 적합한 목표 구조는 아래다.

- LLM: pacing mode와 ep_count를 판단
- Python: 입력 신호를 수집하고, 출력 범위를 검증하고, `ep_end`를 정규화하고, invalid output 시 fallback만 수행

이 문서에서 말하는 "LLM-owned ep_count"는 완전 무가드 자유 결정이 아니라, 위 구조를 뜻한다.

### 3.3 높은 밀도 지향은 `ep_count 축소`와 동일하지 않다

이건 중요하다.

사용자 목표는 "무조건 화수를 줄이자"가 아니라 `더 급하게`, `더 촘촘하게`다.

그래서 최종 구조는 두 축을 같이 가져가야 한다.

1. `ep_count ownership`
  - 누가 3화/4화/5화를 고르는가
2. `density direction`
  - 같은 화수 안에서 tactical_doc를 얼마나 압축적으로 쓰게 할 것인가

추천은 둘 다 LLM 쪽으로 넘기되, 형태는 아래처럼 나누는 것이다.

- `pace_mode`: `compressed(2~3) | standard(4~5) | expanded(6)`
- `ep_count`: `2~6`
- `pacing_reasoning`: 왜 그렇게 판단했는지 짧은 설명

이렇게 해야 "4화지만 compressed"도 표현할 수 있다.

## 4. Side-Effect Coverage

### file writes / artifacts

- 직접 파일 산출은 없다
- Arc JSON payload shape가 바뀌면 subsequent persistence schema가 간접 영향을 받는다

### DB / schema / transaction boundaries

- 직접 DB write는 Stage 2 이후 sink에서 일어난다
- 다만 `ep_count`, `ep_end`, verdict/advisory 메타 shape가 바뀌면 downstream summary rows와 diagnostics 의미가 변한다

### JSONL / log / audit sinks

- 현재 `four_phase_arc_generator`는 `pacing_reason`를 로그에만 남긴다
- ownership 변경 시 `pace_mode`, `pacing_reasoning`, `density_signal_summary` 같은 audit field를 추가할지 결정해야 한다

### console / UI / operator output

- 현재 operator는 왜 2화/3화/4화/5화/6화가 나왔는지 충분히 보기 어렵다
- 이 변경은 오히려 operator transparency를 높이는 방향으로 설계할 수 있다

### rollback / recovery / retry

- invalid LLM pacing output에 대해 Python fallback이 필요하다
- 예:
  - ep_count missing
  - ep_count out of range
  - `pace_mode`와 `ep_count` 자기모순
  - `ep_end` 불일치

### cache / global state

- 특별한 global cache 변화는 없지만, prompt cache key가 `pacing signal`에 영향을 받을 수 있다

### bootstrap fallback / config-env mutation

- not applicable

## 5. Pass 3 - Recommended Direction

### 5.1 목표 구조

최종 목표는 아래다.

- Python:
  - item/reward/solution/content/tension 관련 신호 수집
  - density summary 구성
  - LLM 출력 guard
  - `ep_end` 계산과 normalization
- LLM:
  - `pace_mode`
  - `ep_count`
  - `pacing_reasoning`
  - high-density tactical direction

### 5.2 추천되는 output contract

현재 Arc schema에 다음 계층을 추가하는 방향이 가장 자연스럽다.

- `pacing_decision`
- `pace_mode`: `compressed(2~3) | standard(4~5) | expanded(6)`
  - `ep_count_reasoning`: short string
  - `density_focus`: short string

핵심은 `ep_count` 자체만 남기지 않는 것이다.

그 이유:

- 지금 문제의 본질은 숫자보다 판단 근거다
- 왜 4화가 나왔는지 남겨야 이후 품질 회귀를 잡을 수 있다
- "늘어짐" complaint는 나중에 reasoning과 density focus를 봐야 진단 가능하다

### 5.3 추천되는 Python guard

Python은 아래만 해야 한다.

- `ep_count`는 2~6 범위로 clamp
- `pace_mode`와 `ep_count`가 강하게 모순되면 warning/advisory
- `ep_end = ep_start + ep_count - 1` 재계산
- `beat_sequence >= ep_count` 최소 규칙 유지
- tactical minimum length guard 유지

즉 Python은 더 이상 "몇 화가 맞는지" 판단하지 않고, "출력이 계약을 지키는지"만 확인한다.

## 6. Adversarial 3-Pass Findings

### Pass 1. Structure

- 기존 focused audit보다 한 단계 넓혀서 ownership, schema, validation 면까지 포함했다
- execution SSOT로 승격할 수 있는 수준으로 범위를 정리했다

### Pass 2. Evidence

- live mainline는 여전히 Python-first ep_count였다
- prompt는 여전히 LLM-owned처럼 적혀 있어 mixed authority가 확인됐다
- analyst 계열에는 이미 LLM-owned pacing precedent가 존재했다
- validation pipeline은 ep_count를 믿고 있으므로 guard design이 필수라는 점이 확인됐다

### Pass 3. Execution Meaning

- 단순 `-1화`는 symptom patch에 가깝고 ownership 문제를 해결하지 못한다
- prompt-only 보강은 좋은 첫 patch지만, 사용자가 요청한 "근본 수정" 기준으로는 ownership split까지 가야 한다
- 따라서 execution SSOT는 `LLM ownership + Python guard`를 목표로 하는 것이 맞다

## 7. Final Recommendation

최종 추천은 아래 한 문장으로 요약된다.

- `Stage 2 ep_count는 LLM이 판단하고, Python은 density signal 수집과 출력 guard만 맡는 구조로 바꾸되, 같은 화수 안에서도 더 촘촘하게 쓰게 하는 high-density direction을 함께 넣어라`
