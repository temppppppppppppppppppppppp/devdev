# TF-4P: 4개 프로젝트 1Arc 런 로그 전수조사 3PASS 감리 보고서

> 감사일: 2026-03-13  
> 대상: `projects/00`, `projects/01`, `projects/03`, `projects/0w`  
> 범위: Stage 2~4 세션 로그, `runtime_audit_summary.json`, `episode_production.jsonl`, `pass_rate_monitor.json`, `project_data.db`, `stage0_output/style_guide.json`  
> 제한: 코드 수정 금지, 테스트 실행 금지, 읽기 전용 조사만 수행

## 1. 최종 결론

- 네 프로젝트 모두 `1Arc 런` 자체는 완료됐다.
- 공통 런타임 크래시, artifact missing, sink alignment drift, mojibake는 확인되지 않았다.
- 다만 `clean pass`는 아니다. retained finding은 `P1 2건`, `P2 2건`, `Observation 3건`이다.
- 가장 큰 공통 문제는 `과거 TF-47 Arc compare retry bug`의 런타임 흔적과, `Stage 0 POV artifact drift`다.
- 가장 큰 개별 문제는 `projects/0w`의 Stage 4 연속성 충돌 후 복구와 `projects/03`의 upstream arc integrity debt다.

## 2. 조사 대상 요약

| 프로젝트 | 세션 로그 | Stage 3 산출물 | Stage 4 산출물 | manuscripts | stage_attempts | director_selections |
|---|---|---:|---:|---:|---:|---:|
| `00` | `session_20260313_043840.log` | 3 | 2 | 2 | 6 | 6 |
| `01` | `session_20260313_044504.log` | 3 | 2 | 2 | 6 | 6 |
| `03` | `session_20260313_045921.log` | 3 | 2 | 2 | 6 | 6 |
| `0w` | `session_20260313_044636.log` | 3 | 2 | 2 | 7 | 7 |

공통적으로 `runtime_audit_summary.json`의 `latest_event_type`은 모두 `stage4_complete`이고, `counts.blueprint_success = 3`, `counts.stage4_complete = 1`이다.

## 3. Pass 1: 사실 수집

### 3.1 공통 구조

- 네 프로젝트 모두 `Stage 2 1Arc -> Stage 3 3화 -> Stage 4 2화` 흐름으로 끝났다.
- Frontier-lag 설계와 일치하게 `blueprint 3개`, `manuscript 2개`가 생성됐다.
- `episode_quality_labels`, `episode_quality_signals`, `director_selections`, `stage_attempts`는 네 프로젝트 모두 존재한다.
- `pass_rate_monitor.json`은 존재하지만, 이번 런 기준으로 핵심 비교는 DB와 `episode_production.jsonl` 쪽이 더 신뢰도 높다.

### 3.2 공통 로그 패턴

네 프로젝트 모두 Stage 2 초반에 아래 패턴이 남아 있다.

- `[TF-47] Arc 비교 오류: name 'ep_num' is not defined → Python 폴백`
- 직후 `❌ [TF-47] Director REJECT — Arc 1, retry`

대표 근거:

- `projects/00/logs/session_20260313_043840.log:323`
- `projects/01/logs/session_20260313_044504.log:279`
- `projects/03/logs/session_20260313_045921.log:280`, `:599`
- `projects/0w/logs/session_20260313_044636.log:280`

이 패턴은 네 프로젝트 모두 최종 완료를 막지는 않았지만, Arc 1 재시도를 강제한 공통 historical runtime debt다.

### 3.3 공통 POV artifact 상태

네 프로젝트의 `stage0_output/style_guide.json`은 모두 아래 상태다.

- `pov = 1인칭`
- `extracted_pov = null`
- `selected_primary_pov = null`
- `effective_primary_pov = null`
- `external_pov_insert_policy = null`
- `tone = 진지`

그런데 실제 런타임 로그는 아래와 같이 Bible POV를 따로 우선 적용했다.

- `00`: `StyleGuide POV(1인칭) ≠ Bible POV(전지적)`  
  근거: `projects/00/logs/session_20260313_043840.log:1359`
- `01`: `StyleGuide POV(1인칭) ≠ Bible POV(혼합)`  
  근거: `projects/01/logs/session_20260313_044504.log:1014`
- `03`: `StyleGuide POV(1인칭) ≠ Bible POV(3인칭)`  
  근거: `projects/03/logs/session_20260313_045921.log:1386`
- `0w`: 불일치 경고 없음. `style_guide`가 `1인칭`이라 런타임 경고가 발생하지 않았다.

즉, 런타임은 Bible 쪽 fallback으로 버텼지만 persisted artifact는 3개 프로젝트에서 잘못 남아 있다.

### 3.4 프로젝트별 핵심 사실

#### `00`

- Stage 2 결과는 `PASS_WITH_FIX` 후 수습됐다.
- `runtime_audit_summary.json`에 `flow_guard = 1`이 남아 있다.
- Stage 3/4는 최종적으로 깨끗하게 닫혔다.
- Stage 4 품질:
  - ep1 `PASS / 98`
  - ep2 `PASS / 100`
- `episode_quality_signals` 기준 ep2 `ai_slop_score = 2.0`

#### `01`

- Stage 2 historical retry bug 외에는 구조상 가장 매끈하다.
- POV drift는 있지만, Stage 4 결과는 무난하다.
- Stage 4 품질:
  - ep1 `PASS / 90`
  - ep2 `PASS / 98`
- ep1 `open_review`는 `대화 비율 부족 경고는 1화 특성상 수용 가능`으로 정리돼 있다.

#### `03`

- 네 프로젝트 중 upstream debt가 가장 크다.
- `runtime_audit_summary.json`에 아래가 동시에 찍혔다.
  - `flow_guard = 1`
  - `data_missing = 1`
  - `integrity_fail = 1`
  - `v60_25_auto_correct = 2`
- 의미:
  - Arc 산출물이 처음부터 깔끔하지 않았고
  - auto-correct와 후속 보정이 개입해서 완주했다
- Stage 4 품질:
  - ep1 `PASS / 96`
  - ep2 `PASS / 98`
- `episode_quality_signals` 기준 ep2 `ai_slop_score = 4.0`으로 4개 중 가장 높다.

#### `0w`

- 네 프로젝트 중 Stage 4 런타임 변동성이 가장 컸다.
- ep1:
  - initial verdict `PASS_WITH_FIX / 96`
  - 금지 표현 `주마등처럼`, `꿈이 아니다` 검출
  - inplace patch 후 final `PASS / 90`
- ep2:
  - attempt 1에서 `Continuity Conflict`
  - `26세` vs `23세` 충돌로 `REJECT`
  - attempt 2 inplace patch 후 final `PASS / 90`
- 중요한 점:
  - 이 흐름은 `director_selections`, `stage_attempts`, `episode_production.jsonl`에서 traceable하게 보존된다.
  - 즉 sink drift는 아니고, 실제 runtime instability 후 복구다.

근거:

- `projects/0w/logs/session_20260313_044636.log:1413`
- `projects/0w/logs/session_20260313_044636.log:1427`
- `projects/0w/logs/session_20260313_044636.log:2275`
- `projects/0w/logs/session_20260313_044636.log:2324`

## 4. Pass 2: 교차 검증

### 4.1 DB vs 로그 vs 산출물

교차 검증 결과 다음 항목은 정합적이다.

- `manuscripts = 2`와 실제 `drafts/ep*.txt` 2개가 일치
- `director_selections(stage=4)`와 `episode_quality_labels`의 최종 verdict/score가 일치
- `artifact_path`는 네 프로젝트 모두 실파일 존재
- `episode_production.jsonl`의 final row는 DB의 최종 Stage 4 결과와 충돌하지 않음

따라서 이번 런에 대해 아래 항목은 기각한다.

- `artifact missing`
- `sink alignment drift`
- `final verdict lost`
- `PASS_WITH_FIX provenance 유실`

### 4.2 공통 TF-47 버그의 성격

교차 검증 결과 TF-47은 아래처럼 정리된다.

- 실제 로그에는 runtime warning과 retry가 남아 있음
- DB 최종 결과는 모두 recovery 후 상태를 반영
- 현재 코드베이스에서는 이 버그가 이미 별도 수정된 상태

따라서 이번 문서에서는 이를 `현재 코드베이스의 open blocker`로 올리지 않고, `historical runtime debt evidence`로 분류한다.

### 4.3 POV drift의 성격

POV drift는 단순 표시 문제가 아니다.

- persisted `style_guide.json`은 잘못된 `1인칭`
- 런타임은 Bible POV 우선 적용으로 회복
- 즉 `artifact 잘못됨 + runtime fallback으로 완주` 구조다

이건 clean으로 볼 수 없으므로 retained finding으로 남긴다.

## 5. Pass 3: 오탐 제거

다음 항목은 검토 후 오탐 또는 하향 처리했다.

- `0w`의 ep1 `selection_candidate_key != final candidate_key`
  - 기각: PASS_WITH_FIX + inplace patch 구조에서 의도된 보존값이다.
- `episode_production.jsonl`의 중간 event row
  - 기각: null row나 손상 row가 아니라 `TF49b_PREFLIGHT` 이벤트 row다.
- `pass_rate_monitor`가 빈 구조라서 런 자체가 불완전하다는 주장
  - 기각: 이번 비교에서 DB, session log, `episode_production.jsonl`가 충분한 근거 계층을 제공했다.

## 6. Retained Findings

### P1-1. Stage 0 POV artifact drift가 3개 프로젝트에서 persisted 상태로 남아 있다

- 영향 프로젝트: `00`, `01`, `03`
- 깨진 계약:
  - `style_guide.json`이 실제 선택 POV를 보존하지 못함
  - 런타임은 Bible POV fallback으로 버티지만, artifact는 잘못 남음
- 직접 근거:
  - `projects/00/stage0_output/style_guide.json`
  - `projects/01/stage0_output/style_guide.json`
  - `projects/03/stage0_output/style_guide.json`
  - mismatch 로그 3건
- 사용자 영향:
  - 이후 수동 검토나 후속 Stage 해석 시 style artifact를 신뢰하기 어렵다
- 왜 오탐이 아닌가:
  - 실제 persisted file과 runtime warning이 동시에 존재한다

### P1-2. `0w`는 Stage 4가 clean pass가 아니라 복구형 pass였다

- 깨진 계약:
  - ep1은 `PASS_WITH_FIX -> PASS`
  - ep2는 `REJECT -> inplace patch -> PASS`
- 직접 근거:
  - `projects/0w/logs/session_20260313_044636.log`
  - `projects/0w/project_data.db`의 `stage_attempts`, `director_selections`
- 사용자 영향:
  - 결과물은 나왔지만, Stage 4 runtime stability는 네 프로젝트 중 가장 낮다
- 왜 오탐이 아닌가:
  - DB와 로그에 reject/patch/pass lifecycle이 모두 남아 있다

### P2-1. TF-47 Arc compare retry bug의 historical 흔적이 네 프로젝트 모두에 남아 있다

- 깨진 계약:
  - Arc compare가 warning 없이 한 번에 닫혀야 했는데, `ep_num` 참조 오류로 retry가 강제됨
- 직접 근거:
  - 네 개 세션 로그의 TF-47 경고 라인
- 사용자 영향:
  - 당시 런의 Stage 2 효율과 신뢰도를 떨어뜨림
- 비고:
  - 현 코드베이스에서는 이미 수정된 것으로 보이므로, historical debt로 제한적으로 유지

### P2-2. `03`은 upstream arc integrity debt를 auto-correct로 덮고 통과했다

- 깨진 계약:
  - `data_missing`, `integrity_fail`이 남은 상태에서 recovery 후 완주
- 직접 근거:
  - `projects/03/logs/runtime_audit_summary.json`
- 사용자 영향:
  - 최종 산출물은 통과했지만, upstream planning artifact가 clean하지 않았다
- 왜 오탐이 아닌가:
  - runtime audit summary count가 직접 남아 있다

## 7. Observations

- `00`, `03`에는 `flow_guard`가 1회씩 남아 있다.  
  의미: 비트 대비 화수 밀도가 초반부터 빠듯했다.
- `00`, `01`, `03`, `0w` 모두 `state_tracker 없음 — 사망 NPC 체크 skip`가 남아 있다.  
  의미: validation coverage gap이지 즉시 결함은 아니다.
- `03` ep2의 `ai_slop_score = 4.0`은 네 프로젝트 중 가장 높다.  
  즉시 결함은 아니지만 추후 품질 관찰 포인트다.

## 8. 프로젝트별 최종 판정

| 프로젝트 | 판정 | 비고 |
|---|---|---|
| `00` | 성공, clean 아님 | TF-47 흔적 + POV drift + flow_guard |
| `01` | 성공, 상대적으로 가장 안정 | TF-47 흔적 + POV drift |
| `03` | 성공, debt 동반 | TF-47 흔적 + POV drift + integrity/data_missing |
| `0w` | 성공, 복구형 pass | TF-47 흔적 + Stage 4 연속성 충돌 후 회복 |

## 9. 확신도 Ledger

- `70`: 4개 프로젝트 로그/DB/산출물 인벤토리 완료
- `+10`: Stage 2/3/4 counts와 DB row 정합성 확인
- `+5`: TF-47 공통 패턴 교차 검증
- `+5`: POV drift artifact와 runtime fallback 동시 확인
- `+5`: `0w`의 PASS_WITH_FIX / REJECT / patch / PASS lifecycle trace 확인
- `+5`: `03` integrity/data_missing가 runtime audit에 직접 남아 있음을 재확인
- `-5`: 실제 원고 품질의 문학적 우열은 이번 문서 범위 밖

최종 확신도: `95%`

## 10. 최종 권고

- 현재 네 프로젝트는 `Stage 4까지 나왔다`는 의미에서는 usable하다.
- 다만 `00/01/03`은 Stage 0 POV artifact를 신뢰하면 안 된다.
- `0w`는 Stage 4 output이 나왔다고 해서 clean pass로 해석하면 안 된다.
- 추가 수정이 필요하다면 우선순위는 아래다.
  1. POV artifact persistence 정합화
  2. `0w` 유형 continuity conflict 재발 방지
  3. `03` 유형 upstream integrity debt의 early gate 강화

## 11. 증거 인덱스

- `projects/00/logs/session_20260313_043840.log`
- `projects/01/logs/session_20260313_044504.log`
- `projects/03/logs/session_20260313_045921.log`
- `projects/0w/logs/session_20260313_044636.log`
- `projects/00/logs/runtime_audit_summary.json`
- `projects/01/logs/runtime_audit_summary.json`
- `projects/03/logs/runtime_audit_summary.json`
- `projects/0w/logs/runtime_audit_summary.json`
- `projects/00/logs/episode_production.jsonl`
- `projects/01/logs/episode_production.jsonl`
- `projects/03/logs/episode_production.jsonl`
- `projects/0w/logs/episode_production.jsonl`
- `projects/00/project_data.db`
- `projects/01/project_data.db`
- `projects/03/project_data.db`
- `projects/0w/project_data.db`
- `projects/00/stage0_output/style_guide.json`
- `projects/01/stage0_output/style_guide.json`
- `projects/03/stage0_output/style_guide.json`
- `projects/0w/stage0_output/style_guide.json`
