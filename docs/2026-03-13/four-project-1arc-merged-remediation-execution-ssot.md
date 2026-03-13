# 4개 프로젝트 1Arc 런 병합 수정 실행 SSOT

> 작성일: 2026-03-13  
> 상태: execution-ready  
> 목표: `projects/00`, `projects/01`, `projects/03`, `projects/0w` 1Arc 런 조사 결과를 병합해, 실제 실행해야 할 수정/증명 항목만 남긴다.

## 1. 소스와 위계

이 문서는 아래 두 근거 계층을 병합한 실행 기준 문서다.

1. Opus 조사 문서  
   - `docs/2026-03-13/TF-4P-four-project-1arc-canary-full-survey-3pass-audit.md`
2. Codex 직접 재검증 근거  
   - `projects/00`, `projects/01`, `projects/03`, `projects/0w`의 세션 로그, DB, `runtime_audit_summary.json`, `episode_production.jsonl`, `stage0_output/style_guide.json`

판정 원칙은 아래와 같다.

- Opus 문서의 finding은 직접 로그/DB 근거로 다시 확인해야 retained로 인정한다.
- 이미 최근 closure 문서에서 코드상 닫힌 축은 새 코드 수정 범위에서 제외하고, proof/runtime refresh 범위로 내린다.
- 과거 런에만 남은 historical debt와, 현재 코드에서도 다시 열려 있는 open debt를 분리한다.

## 2. 병합 판정 요약

### 2.1 유지되는 핵심 사실

- 네 프로젝트 모두 런타임 완주는 성공했다.
- 공통 crash, artifact missing, sink alignment drift, mojibake는 없다.
- `00/01/03`에는 `Stage 0 POV artifact drift`가 남아 있다.
- `0w`는 Stage 4가 clean pass가 아니라 `PASS_WITH_FIX / REJECT / inplace patch / PASS` 복구형 pass였다.
- `03`은 `flow_guard`, `data_missing`, `integrity_fail`가 runtime audit에 남아 있어 upstream arc integrity debt가 실제로 있었다.

### 2.2 실행 범위에서 내리는 항목

- `TF-47 Arc compare retry bug`
  - 이유: 로그상 historical debt는 맞지만, 현재 코드베이스에서는 이미 후속 수정/회귀로 닫힌 축이다.
  - 실행 범위: 새 코드 수정 아님. fresh rerun proof만 필요.
- `Stage 4 Director/CW provenance 분리 부족`
  - 이유: 별도 closure 문서에서 이미 닫혔다.
  - 실행 범위: 새 코드 수정 아님. fresh rerun proof만 필요.
- `POV taxonomy 분리 부재`
  - 이유: 별도 closure 문서에서 이미 닫혔다.
  - 실행 범위: 새 코드 수정 아님. old artifact refresh와 fresh proof만 필요.

## 3. 현재 시점 실행 대상

### E-1. POV artifact refresh / proof

- 대상: `00`, `01`, `03`
- 문제:
  - `style_guide.json`은 아직 `pov = 1인칭`으로 남아 있고
  - `selected_primary_pov`, `effective_primary_pov`, `external_pov_insert_policy`가 비어 있다.
- 현재 판단:
  - 이건 최신 코드 미적용 artifact다.
  - 시스템 코드 재수정이 아니라 Stage 0 refresh로 proof를 남겨야 한다.
- 실행 목표:
  - affected 프로젝트에서 Stage 0 POV artifact를 새 계약 기준으로 재생성
  - mismatch warning이 사라지거나, 최소한 artifact와 runtime effective POV가 일치함을 확인
- 성공 기준:
  - `style_guide.json`에 `selected_primary_pov`, `effective_primary_pov`가 채워짐
  - 세션 로그에 기존 `StyleGuide POV(1인칭) ≠ Bible POV(...)` 경고가 재현되지 않음

### E-2. `0w`형 Stage 4 continuity hardening proof

- 대상: `0w`와 동형 workload
- 문제:
  - ep2 attempt1에서 `26세` vs `23세` 충돌로 `REJECT`
  - 이후 inplace patch로 recovery
- 현재 판단:
  - 최근 Stage 4 continuity hardening은 이미 코드상 반영됐다.
  - 하지만 이 로그는 수정 전 evidence이므로 fresh runtime proof가 없다.
- 실행 목표:
  - 동일하거나 유사한 1Arc/2ep Stage 4 run에서 multi-reject chain이 줄었는지 확인
  - continuity conflict가 나더라도 rationale/provenance가 새 sink에 제대로 남는지 확인
- 성공 기준:
  - 동일 계열 conflict가 재발하지 않거나
  - 재발하더라도 `stage_attempts` rationale와 final warning split이 정상 저장됨

### E-3. `03`형 upstream arc integrity debt 보강

- 대상: Stage 2 arc finalization / integrity gate
- 문제:
  - `runtime_audit_summary.json`에 `data_missing = 1`, `integrity_fail = 1`
  - auto-correct와 수습으로 완주했지만, upstream arc artifact는 clean하지 않았다.
- 현재 판단:
  - 이 축은 fresh proof만으로 닫기 어렵다.
  - 실제 코드 보강 범위가 남아 있을 가능성이 가장 높다.
- 실행 목표:
  - `beat_sequence`, `hybrid_composition`, 기타 required field가 빠진 arc가 Stage 3로 넘어가기 전에 더 강하게 차단되거나 구조화 복구되게 한다.
- 우선순위:
  - 이번 병합 SSOT에서 유일한 명시적 code-harden target
- 성공 기준:
  - `integrity_fail`와 `data_missing`가 recovery-only가 아니라 early gate 또는 deterministic repair로 정리됨
  - 같은 유형 런에서 `runtime_audit_summary`에 해당 키가 남지 않음

### E-4. `state_tracker 없음` validation coverage 재평가

- 대상: Unified Arc validation
- 문제:
  - 네 프로젝트 모두 `state_tracker 없음 — 사망 NPC 체크 skip`
- 현재 판단:
  - 1Arc 초반 런에서 blocker는 아니다.
  - 하지만 validation coverage gap이므로 완전히 무시하면 안 된다.
- 실행 목표:
  - `prev_arcs`가 적은 early-arc에서는 benign skip인지
  - tracker wiring 누락인지 분리
- 범위:
  - 기본값은 조사/증명 우선
  - fresh evidence에서 실제 wiring 누락으로 재현될 때만 코드 수정으로 승격

## 4. 실행 제외 항목

- `artifact missing`, `sink alignment drift`, `mojibake`
  - 이번 4개 런에서는 직접 근거 없음
- `PASS_WITH_FIX provenance 유실`
  - recent Stage 4 closure에서 이미 닫힘
- `TF-47 retry bug 자체 재수정`
  - historical evidence일 뿐, 현재 실행 범위에서는 proof-only

## 5. 실행 순서

1. `E-1` POV artifact refresh / proof
2. `E-2` Stage 4 continuity hardening proof
3. `E-3` Stage 2 integrity hardening
4. `E-4` state_tracker coverage 재평가

이 순서로 두는 이유:

- `E-1`, `E-2`는 이미 닫힌 코드 축의 proof라 ROI가 높다.
- `E-3`은 실제 open code-hardening 가능성이 있어 그 다음 tranche로 둔다.
- `E-4`는 현재는 관찰성/coverage 성격이 강해 마지막으로 둔다.

## 6. 기존 closure 문서와의 관계

아래 문서들은 이미 닫힌 축으로 취급한다.

- `docs/2026-03-13/viewpoint-primary-pov-external-insert-remediation-postfix-3pass-closure.md`
- `docs/2026-03-13/stage4-director-cw-log-informed-remediation-postfix-5pass-closure.md`
- `docs/2026-03-13/logging-hardening-moderate-followup-postfix-3pass-closure.md`

즉 이번 SSOT는 위 closure들을 뒤집는 문서가 아니라,  
`과거 4개 런의 evidence를 현재 코드 상태와 reconciliation해서 남은 실행 과제만 추린 문서`다.

## 7. 검증 기준

- POV refresh 후:
  - `style_guide.json` meta 필드 확인
  - mismatch warning 부재 또는 감소 확인
- Stage 4 proof 후:
  - `stage_attempts`, `director_selections`, `episode_production` rationale/provenance 확인
  - continuity conflict 재발 여부 확인
- Stage 2 integrity hardening 후:
  - `runtime_audit_summary.json`에서 `data_missing`, `integrity_fail` 제거 확인
- state_tracker 재평가 후:
  - benign skip인지, wiring 결함인지 명시적으로 판정

## 8. 최종 판정

- 현재 병합 실행 오더는 `proof-heavy + one open hardening tranche`로 정리하는 게 맞다.
- historical issue를 다시 구현 대상으로 끌어들이면 중복 수정이 된다.
- 따라서 이번 SSOT는 `이미 닫힌 축의 재증명`과 `03형 integrity debt의 선택적 재개방`만 남기는 방식으로 확정한다.
