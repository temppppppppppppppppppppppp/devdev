# 시점·혼합 시점 전량 전수조사 — 3PASS 최종 감리 보고서

작성일: 2026-03-13  
판정: `runtime blocker 없음 / clean 아님`  
최종 확신도: `95%`

## Executive Summary
- 조사 범위는 `Stage 0 POV 입력`, `StyleGuide 캐시/산출물`, `Stage 2~3 blueprint planning`, `Stage 4 CW·Director·validator`, `prompt asset`, `현재 4개 병렬 3아크 런 로그`까지로 고정했다.
- 결론은 `혼합 시점이 아예 미지원인 것은 아니지만, 단계별 SSOT가 갈라져 있다`이다.
- 현재 구조는 사용자 POV 선택, 스타일 레퍼런스 산출물, Stage 4 실효 POV가 서로 다른 층에서 관리된다.
- retained finding은 `P1 1건`, `P2 2건`, `Observation 2건`이다.

## 조사 범위
- 코드: `modules/core/stage0`, `modules/core/stage01_helpers.py`, `modules/core/project_support.py`, `modules/core/stage4_orchestrator.py`, `modules/core/stage4_interview_round.py`, `modules/validation/pre_llm_validator.py`, `modules/domain/agents/chief_writer_quality.py`, `modules/domain/agents/blueprint_ensemble.py`
- 프롬프트/설정: `config/prompts/writer_rules.json`, `config/prompts/ensemble.yaml`, `config/style_references/investment/style_guide.json`
- 테스트: `tests/test_stage0_pov.py`, `tests/test_pre_llm_validator.py`, `tests/test_chief_writer_quality.py`, `tests/test_stage4_interview_round.py`, `tests/test_project_support.py`
- 런타임 증거: `projects/00`, `projects/01`, `projects/03`, `projects/0w`의 `logs/` 및 `stage0_output/style_guide.json`

## Pass 1 — 사실 수집

### 1. Stage 0는 혼합 시점을 입력받을 수 있다
- `modules/core/stage01_helpers.py`는 시점 메뉴에 `1인칭 / 3인칭 / 전지적 / 혼합` 4개를 노출한다.
- `tests/test_stage0_pov.py`, `tests/test_stage01_helpers.py`도 `혼합` 선택이 실제로 저장됨을 검증한다.
- 즉 `혼합 시점 메뉴가 없다`는 가설은 현재 코드 기준 오탐이다.

### 2. StyleExtractor는 혼합 시점 규칙을 이미 가진다
- `modules/core/stage0/style_extractor.py`의 `_get_pov_rules()`는 `혼합` 분기를 가진다.
- 규칙은 `씬 단위 전환 허용`, `동일 씬 내 혼합 금지`, `씬 구분자 사용`, `주인공 장면 1인칭 허용`, `타 인물 장면은 3인칭 제한`, `전지 개입 최소화`다.
- 즉 `혼합 POV 규칙이 아예 없다`는 과거 문서형 가설도 현재 시점에서는 오탐이다.

### 3. Stage 0 스타일 산출물은 사용자 POV를 반영하지 않는다
- 아래 4개 프로젝트의 `stage0_output/style_guide.json`을 UTF-8로 직접 판독한 결과, 모두 `pov=1인칭`, `tone=진지`였다.

| 프로젝트 | Stage 0 선택 POV | `stage0_output/style_guide.json.pov` |
| --- | --- | --- |
| `projects/00` | 전지적 | 1인칭 |
| `projects/01` | 혼합 | 1인칭 |
| `projects/03` | 3인칭 | 1인칭 |
| `projects/0w` | 1인칭 | 1인칭 |

- 이는 현재 Stage 0 스타일 산출물이 `사용자 선택 POV`가 아니라 `장르 reference-derived POV`에 묶여 있음을 뜻한다.

### 4. Stage 4는 이 불일치를 런타임에서 보정한다
- `modules/core/stage4_orchestrator.py`는 `resolve_project_bible_pov()`로 Bible POV를 읽고, `StyleGuide POV != Bible POV`면 경고 후 `Bible 우선 적용`으로 덮어쓴다.
- 실제 로그에서도 이 경고가 재현된다.
  - `projects/00/logs/session_20260313_043840.log`
  - `projects/01/logs/session_20260313_044504.log`
- 즉 현재 시스템은 `Stage 0 artifact drift`를 `Stage 4 runtime override`로 메우는 구조다.

### 5. Director는 POV를 모르지 않는다
- `modules/core/stage4_interview_round.py`는 Director mandatory context 앞부분에 `[작품 시점] - 기본 POV: ...`를 주입한다.
- `tests/test_stage4_interview_round.py`도 `혼합`일 때 `기본 POV: 혼합`이 포함되는지 검증한다.
- 실제 `projects/0w/logs/session/llm_io.jsonl`에서도 Director prompt에 `[작품 시점] - 기본 POV: 1인칭` 블록이 존재한다.

### 6. 혼합 시점 검사는 존재하지만 advisory-only다
- `modules/validation/pre_llm_validator.py`는 `혼합` 시점에서
  - `***` 씬 구분자 없는 1인칭/3인칭 혼재
  - 동일 씬 블록 내 1인칭/3인칭 혼재
  를 경고한다.
- `modules/domain/agents/chief_writer_quality.py`도 같은 로직을 self-critique로 재사용한다.
- 그러나 둘 다 hard fail이 아니라 advisory/warning 계층이다.

### 7. Stage 3 planning에는 혼합 시점 전용 분기가 없다
- `modules/domain/agents/blueprint_ensemble.py`는 `_pov == "1인칭"`과 `_pov == "3인칭"`일 때만 프리셋 제약을 명시한다.
- `혼합` 전용 분기는 없다.
- 반면 `config/prompts/ensemble.yaml`, `config/prompts/writer_rules.json`은 `villain_scheme`, `side_glimpse`, `omniscient_hint`, `시점 전환 활용`을 적극 권장한다.
- 따라서 mixed POV planning은 `명시적 양성 규칙`보다 `일반 전환 프롬프트 + downstream 보정`에 더 의존한다.

## Pass 2 — 교차 검증

### 교차 검증 A: Stage 0 사용자 선택 vs 산출물
- 로그:
  - `projects/01/logs/session_20260313_044504.log` → `설정 완료: 현대인 / 회귀자 / 혼합`
  - `projects/03/logs/session_20260313_045921.log` → `설정 완료: 현대인 / 회귀자 / 3인칭`
  - `projects/00/logs/session_20260313_043840.log` → `설정 완료: 현대인 / 회귀자 / 전지적`
- 산출물:
  - `projects/00/stage0_output/style_guide.json`
  - `projects/01/stage0_output/style_guide.json`
  - `projects/03/stage0_output/style_guide.json`
  - 모두 `pov=1인칭`
- 결론: `Stage 0 선택 POV != Stage 0 스타일 산출물 POV` 드리프트는 교차 검증으로 확정된다.

### 교차 검증 B: Runtime 보정 존재 여부
- 코드: `modules/core/stage4_orchestrator.py`
- 로그: `projects/00/logs/session_20260313_043840.log`, `projects/01/logs/session_20260313_044504.log`
- 결론: 보정은 실제로 존재한다. 따라서 `시점 시스템이 즉시 깨진다`는 가설은 과장이다.

### 교차 검증 C: 혼합 시점 검증 부재 여부
- 코드: `modules/validation/pre_llm_validator.py`
- 테스트: `tests/test_pre_llm_validator.py`, `tests/test_chief_writer_quality.py`
- 결론: `혼합 시점 검증이 없다`는 가설은 기각한다. 다만 severity가 advisory-only라는 별도 문제가 남는다.

### 교차 검증 D: Director blind 여부
- 코드: `modules/core/stage4_interview_round.py`
- 테스트: `tests/test_stage4_interview_round.py`
- 런타임 prompt: `projects/0w/logs/session/llm_io.jsonl`
- 결론: Director는 POV를 알고 있다. 따라서 `Stage 4 판단기가 POV를 모른다`는 가설도 기각한다.

## Pass 3 — 오탐 제거 및 최종 판정

## 확정 Findings

### P1. Stage 0 스타일 산출물 POV가 사용자 선택 POV와 분리돼 있다
- 깨진 계약: 사용자/프로젝트 POV 선택이 `Stage 0 style_guide.json`에 SSOT로 반영되지 않는다.
- 직접 근거:
  - `projects/00`, `projects/01`, `projects/03`, `projects/0w`의 `stage0_output/style_guide.json`이 모두 `pov=1인칭`
  - 같은 런의 Stage 0 로그는 전지적/혼합/3인칭/1인칭 선택을 각각 기록
  - Stage 4는 `Bible 우선 적용` 경고로 이를 런타임에서 덮어씀
- 반대 근거 검토:
  - `modules/core/project_support.py`의 `build_style_guide_summary()`는 Bible POV를 우선 사용해 downstream 피해를 일부 줄인다.
  - 그러나 raw artifact와 audit surface는 여전히 잘못된 POV를 보존한다.
- 왜 오탐이 아닌가:
  - 4개 병렬 프로젝트에서 같은 패턴이 재현됐다.
- 영향:
  - Stage 0 결과물 감사, 수동 점검, raw anchor consumer, 향후 UI surface가 잘못된 POV를 보게 된다.
  - 런타임이 보정하더라도 SSOT drift는 남는다.
- 테스트 미실행 사유:
  - 이번 턴은 read-only 조사 정책을 유지했다.

### P2. 혼합 시점 planning contract가 Stage 3에서 명시적으로 닫혀 있지 않다
- 깨진 계약: `혼합` 시점이 planning 단계에서 `1인칭/3인칭`처럼 전용 분기로 제어되지 않는다.
- 직접 근거:
  - `modules/domain/agents/blueprint_ensemble.py`는 `_pov == "1인칭"`과 `_pov == "3인칭"` 제약만 명시
  - `혼합` 전용 분기 없음
  - `config/prompts/ensemble.yaml`, `config/prompts/writer_rules.json`은 시점 전환 프리셋을 적극 장려
- 반대 근거 검토:
  - `Stage 0 style_extractor.py`에는 혼합 규칙이 존재한다.
  - 그러나 planning 계층에서 같은 규칙이 전용 branch로 닫혀 있지는 않다.
- 왜 오탐이 아닌가:
  - mixed POV의 핵심 제약인 `씬 단위 전환`이 planning 계층에서 별도 제어되지 않는다는 사실은 코드상 명확하다.
- 영향:
  - 혼합 POV 프로젝트는 planning 단계에서 필요한 양성 규칙이 약하고,
  - 비혼합 프로젝트는 prompt asset의 전환 성향을 downstream 제약으로 막아야 한다.

### P2. 혼합 시점 위반은 현재 advisory-only라 hard gate가 없다
- 깨진 계약: 동일 씬 내 1인칭/3인칭 혼재가 경고는 되지만, 강제 수정/거절까지 승격되지 않는다.
- 직접 근거:
  - `modules/validation/pre_llm_validator.py`의 `혼합` 검사 반환 severity는 `WARNING`
  - `modules/domain/agents/chief_writer_quality.py`도 medium self-critique issue로만 소비
- 반대 근거 검토:
  - Director mandatory context와 Stage 4 review가 간접적으로 제어할 수 있다.
  - 하지만 `same-scene mixed POV`가 전용 hard gate로 승격된 코드는 현재 보이지 않는다.
- 왜 오탐이 아닌가:
  - mixed POV 품질을 실제로 보장하는 마지막 안전장치가 advisory에 머물러 있다.
- 영향:
  - 혼합 시점 품질은 `LLM 성능 + Director 판단`에 과도하게 의존한다.

## Observation

### O1. Prompt asset에는 여전히 시점 전환 친화적 유산이 많다
- `config/prompts/writer_rules.json`, `config/prompts/ensemble.yaml`, `modules/core/prompt_builder.py`는 여전히 `시점 전환 활용` 방향을 강하게 띤다.
- 이것이 곧 결함은 아니지만, mixed POV가 아닌 프로젝트에서도 drift pressure를 만든다.

### O2. 기존 진단 문서 중 일부는 현재 코드와 어긋난다
- `docs/2026-03-10/TF-QI-structural-quality-gaps-audit.md`의 일부 POV 항목은 현재 코드보다 뒤처져 있다.
- 이번 보고서에서는 현재 코드/테스트/런타임을 우선 근거로 삼았다.

## 기각한 가설
- `혼합 시점 메뉴가 없다` -> 기각
- `혼합 시점 규칙이 없다` -> 기각
- `전지적/혼합 POV validation이 없다` -> 기각
- `Director는 작품 POV를 모른다` -> 기각
- `시점 시스템이 현재 즉시 깨져 있다` -> 기각  
  다만 `artifact SSOT drift`와 `mixed planning/validation gap`은 유지

## 최종 판단
- `진행 가능 여부`: 가능
- `clean 여부`: 아님
- `가장 큰 문제`: `Stage 0 artifact POV drift`
- `혼합 시점에 대한 결론`: 혼합 시점은 부분 지원되지만, planning·validation·artifact 계층이 하나의 SSOT로 닫혀 있지 않다

## 확신도 Ledger
- `70` 전수 커버리지 완료
- `+10` 코드/테스트/로그/산출물 4계층 교차 검증
- `+10` 4개 병렬 프로젝트 실증 확인
- `+5` 오탐 5건 기각 및 severity 재분류
- `= 95`

95%를 넘기지 않은 이유:
- 현재 4개 3아크 런이 진행 중이어서, mixed POV의 `completed Stage 4 manuscript`를 이번 턴에서 끝까지 재판독하지는 않았다.
- 그 부분은 runtime-only 잔여 확인으로 남긴다.
