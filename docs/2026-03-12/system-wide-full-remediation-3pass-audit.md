# 시스템 전역 retained finding 실현 계획 3-Pass 감리

작성일: 2026-03-12  
인코딩: UTF-8  
감리 대상: `docs/2026-03-12/system-wide-full-remediation-execution-plan.md`

## 1. 감리 결론

현재 실행 계획은 두 감사 문서의 retained finding을 빠짐없이 흡수했고, 구현 순서도 canary blocker 우선으로 정렬돼 있다.

판정:
- blocker: 없음
- 범위 누락: 없음
- 과잉 범위: 없음
- 구현 진행 권고: 가능
- 현재 확신도: `95%`

95% 근거:
- system-wide 감사 retained finding 전량이 `WP-1`~`WP-5`에 매핑됐다.
- stage4 canary 확정 문제와 보조 신호 중 구현 연결이 필요한 항목이 전부 배정됐다.
- `rejected/runtime-only` 항목 재유입을 명시적으로 차단했다.
- work package 순서가 재현성 → 데이터 계약 → lineage → runtime defect → observability로 고정돼 있다.

남은 5%:
- 실제 코드 수정 후 회귀 실행 전까지는 acceptance 충족을 이 문서만으로 100% 증명할 수 없다.
- canary rerun은 아직 실행 전이므로 umbrella finding 닫힘은 후속 구현 검증이 필요하다.

## 2. Pass 1. findings 대비 범위 적합성

확인 결과:
- system-wide `F-01 ~ F-07`은 각각 실행 묶음 또는 post-fix refresh로 직접 연결됐다.
- system-wide `F-08`은 코드 버그가 아니라 hygiene 문제이므로 `WP-5` + `Phase G`로 배정됐다.
- canary `F-01 ~ F-08`은 전부 구현 또는 acceptance gate로 연결됐다.
- canary `F-09 ~ F-11`은 standalone bug로 과대승격하지 않고, root-cause 확인용 근거와 테스트 보강 대상으로 처리됐다.

판정:
- `canary F-03`를 별도 코드 항목으로 중복 생성하지 않고 umbrella gate로 둔 판단이 맞다.
- `projects/test_project/logs/episode_production.jsonl` refresh를 코드 fix 이전이 아니라 `Phase G`로 미룬 판단도 맞다.
- 누락된 retained finding은 없다.

## 3. Pass 2. 선후관계 / 구현 리스크 감리

### WP-1
- 난이도: 중간
- 이유:
  - untracked canary stack, provider routing drift, 문서 충돌을 같이 묶어야 한다.
  - 하지만 이 묶음을 먼저 닫아야 이후 canary 결과 해석이 흔들리지 않는다.

### WP-2
- 난이도: 중간
- 이유:
  - `chief_writer`와 `stage4_interview_round` 계약을 동시에 건드린다.
  - wrapper 저장, 장르 정규화, state merge는 서로 연결돼 있으므로 분리 구현이 오히려 위험하다.

### WP-3
- 난이도: 중간
- 이유:
  - sink 의미론과 canary hard gate가 연결돼 있다.
  - naming drift만 닫아서는 안 되고, patch lineage 의미까지 맞춰야 한다.

### WP-4
- 난이도: 중간
- 이유:
  - structural patch 분류와 `causal_graph` runtime bug는 서로 다른 층이지만 Stage 4 patch/post-process 경계에서 만난다.
  - TruthGate는 Stage 4 전용은 아니나 retained P2로서 이번 phase에 같이 닫는 편이 맞다.

### WP-5
- 난이도: 중간
- 이유:
  - runtime summary, DB telemetry, soft-failure residue는 관측 계층과 산출물 위생이 동시에 걸려 있다.
  - 다만 기능 로직을 크게 흔들지 않고 계측과 hygiene 중심으로 닫을 수 있다.

판정:
- work package 분해 수준은 충분하다.
- 현재 순서가 가장 보수적이다.

## 4. Pass 3. acceptance / 비대상 / 누락 재점검

acceptance 점검:
- 각 `WP`마다 목적, 대상 파일, 구현 요구, acceptance, 예정 검증이 존재한다.
- `Phase G`가 없으면 tracked sample refresh와 문서 sync가 다시 빠질 수 있었는데, 현재 계획은 이를 별도 단계로 고정했다.
- `TF-H` 반복 경고는 관찰로 남기되, contract fix 후 지속 시 follow-up으로 승격하도록 적어 scope creep를 막았다.

비대상 점검:
- Electron/UI non-finding 유지가 명시됐다.
- full/live rerun 선실행 금지가 명시됐다.
- `rejected/runtime-only` 재유입 금지가 명시됐다.

최종 판정:
- 이 계획은 바로 구현에 들어가도 된다.
- 추가 planning round 없이 `WP-1 -> WP-2 -> WP-3 -> WP-4 -> WP-5` 순서로 착수 가능하다.
