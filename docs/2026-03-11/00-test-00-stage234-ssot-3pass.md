# 00_test_00 Stage 2/3/4 SSOT 3-Pass 감리

> 작성일: 2026-03-11
> 상태: SSOT 갱신 완료
> 감리: 시스템 3-pass + 문서 3-pass 완료
> 확신도: 97%
> 기준선: `00_test_00`는 `technical validation baseline`이며 `real production baseline`이 아니다.

---

## 0. 최종 판정

`00000` 기준은 폐기한다.

- 2026-03-11 기준 기술 검증 baseline은 `projects/00_test_00`로 교체한다.
- 이번 실행은 `Stage 2 -> 3 -> 4` 1 arc end-to-end가 실제로 통과했음을 증명한다.
- 이번 실행은 `quality_summary / result_summary / retrieval_summary`가 실제 데이터로 채워짐을 증명한다.
- 이번 실행은 `manual review`와 `work_guard / role-fit` 실데이터 보정이 아직 시작 전임도 같이 증명한다.

오탐 제거 후 현재 핵심 문제는 아래 네 축으로 정리된다.

1. 대시보드 read 경로가 DB를 수정한다.
2. Stage 4 observability와 판정 표기가 서로 어긋난다.
3. Stage 4 retry/cost가 ep1 기준 과도하다.
4. calibration은 retrieval telemetry와 manual review 저장소가 분리돼 있어 UX 해석이 쉽게 꼬인다.

---

## 1. Baseline 교체 선언

- `projects/00000`는 더 이상 현재 기준 샘플이 아니다.
- `projects/00000`는 과거 calibration 우선순위 판단에 쓰였던 historical snapshot으로만 남긴다.
- 현재 SSOT는 `projects/00_test_00`의 실제 `Stage 2 -> 3 -> 4` 실행 로그, DB, draft, metrics에 둔다.
- 단 `00_test_00`도 운영 대표 프로젝트는 아니다. 따라서 이 문서는 `기술 검증 baseline` 문서이지 `실운영 품질 인증서`가 아니다.

---

## 2. Pass 1: 실행 사실 고정

이 pass에서는 해석을 배제하고 사실만 적는다. 대시보드 payload는 호출하지 않았고, helper/DB/log 직접 조회만 사용했다.

| 항목 | 값 | 출처 |
|---|---|---|
| 대상 프로젝트 | `projects/00_test_00` | `session_20260311_112831.log`, `project_data.db` |
| 실행 범위 | Arc 1, ep 1~4 | 세션 로그 |
| Stage 2 | PASS, `stage_attempts(stage=2)=1` | `project_data.db` |
| Stage 3 | PASS, ep 1~4 전부 PASS, `stage_attempts(stage=3)=4` | `project_data.db`, `runtime_audit.jsonl` |
| Stage 4 | PASS, ep 1~4 완료, `stage_attempts(stage=4)=13` | `project_data.db`, 세션 로그 |
| 산출물 | `drafts/ep_0001.txt` ~ `drafts/ep_0004.txt` 생성 | 파일시스템 |
| `stage_attempts` 총합 | `18` | `project_data.db` |
| `director_selections` 총합 | `14` | `project_data.db` |
| `episode_quality_labels` | `4` | `project_data.db` |
| `episode_quality_signals` | `4` | `project_data.db` |
| `episode_quality_observations` | `0` | `project_data.db` |
| `quality_metrics.jsonl` retrieval | `22` | `quality_metrics.jsonl` |
| `quality_metrics.jsonl` validation | `18` | `quality_metrics.jsonl` |
| retrieval stage 분포 | `director=13`, `stage2=1`, `stage3=4`, `stage4=4` | `quality_metrics.jsonl` |
| pass_rate monitor | ep1 `9`회 시도 후 PASS, ep2 `1`회 PASS, ep3 `2`회 PASS, ep4 `1`회 PASS | `pass_rate_monitor.json` |
| 세션 호출 수 | `169` | `metrics_20260311_112834.json` |
| 총 토큰 | `1,027,179` | `metrics_20260311_112834.json` |
| 총 비용 | `$1.9671` | `metrics_20260311_112834.json` |
| ep1 비용 | `$1.1133`, `530,162 tokens` | `session_20260311_112831.log` |
| ep2 비용 | `$0.2480`, `143,023 tokens` | `session_20260311_112831.log` |
| ep3 비용 | `$0.3093`, `177,209 tokens` | `session_20260311_112831.log` |
| ep4 비용 | `$0.2965`, `176,785 tokens` | `session_20260311_112831.log` |
| quality summary | `available=True`, `latest_ep=4` | `db.get_quality_signal_summary()` |
| result summary | `available=True`, `headline='ep 4 · PASS · 100점'` | `_build_result_summary()` |
| retrieval summary | `available=True`, `total_observations=22` | `QualityDashboard.get_retrieval_summary()` |
| calibration | `available=False`, `next_step='수동 review 라벨이 아직 없습니다...'` | `_build_calibration_payload()` |
| work guard 상태 | `work_guard_exists=False`, `tracking_slots=0`, `registry_profiles=0`, `role_fit_constraints=0` | `inspect_quality_sidecar_health()` |

---

## 3. Pass 2: 증거 정합성 교차검증

### 3.1 런타임/DB/로그 정합성

| 토픽 | 교차 증거 | 판정 |
|---|---|---|
| end-to-end 실행 성공 | 세션 로그, draft 4개, `stage_attempts` 18건, `director_selections` 14건이 서로 맞물린다 | 정상 기록 |
| `REJECT 44` | 세션 로그, `director_selections`, `episode_production.jsonl`, `tests/test_v75c_contradiction_firewall.py`가 모두 `firewall cap to 44`를 지지한다 | `designed but confusing` |
| `episode_quality_observations=0` + retrieval 22건 | DB manual review table은 0이지만 `quality_metrics.jsonl` retrieval은 22건이다 | `designed but confusing` |
| `runtime_audit_summary` | summary는 `stage3_complete`에서 종료되고 Stage 4는 `flush_audit_buffer()`만 탄다 | `confirmed defect` |
| dashboard read path | `_build_quality_dashboard_payload()`가 `bootstrap_quality_sidecars()`를 호출한다 | `confirmed defect` |
| `prev_score=100` after `REJECT 44` | `stage4_interview_round.py`가 `pre_firewall_score`를 `previous_attempt["score"]`로 보존하고 `pass_rate_monitor`가 이를 기록한다 | `designed but confusing` |
| role-fit/work guard 공백 | helper 기준 `work_guard_exists=False`, `work_focus_rate=0.0` | 정상 기록, calibration pending |

### 3.2 기존 TF 리소스 재분류

| 문서 | 기존 요지 | 이번 감리 반영 |
|---|---|---|
| `docs/2026-03-05/audit-score-logging-gaps.md` | Stage 4 score/logging 불일치 갭 존재 | 심각도 유지. 단 `REJECT 44` 자체를 버그로 승격하지 않고 `표기/설명 정합성 갭`으로 한정 |
| `docs/2026-03-07/TF-stage4-ep1-failure-audit.md` | ep1 연속 REJECT와 분량/심사 경로 문제 추적 | 이번 실행에서도 ep1 9회 시도, `$1.1133` 발생. 현상 미해결로 갱신 |
| `docs/2026-03-10/TF-QI-structural-quality-gaps-audit.md` | InfoParadox/NPC/구조 경고의 오탐 여지 감리 | ep3 open_review와 합치됨. `InfoParadox`, scene coverage, ending hook 일부 경고는 직접 defect가 아니라 warning noise로 강등 |
| `docs/2026-03-10/TF-work-guard-identity-ssot-plan.md` | `calibration pending`, `role-fit pending` | 심각도 유지. `00_test_00`는 retrieval wiring 확인용일 뿐 role-fit 보정 완료 근거가 아님 |
| `docs/2026-03-11/TF-quality-sidecar-bootstrap.md` | sidecar bootstrap 자체는 유효 | bootstrap 성공 자체는 유지. 단 dashboard read-on-write 경로는 이 SSOT에서 `confirmed defect`로 재분류 |

---

## 4. Pass 3: 현재 문제 taxonomy

### 4.1 `confirmed defect`

### CF-1. 대시보드 quality payload가 read-on-write다

- 증거: `modules/api/bridge_server.py`의 `_build_quality_dashboard_payload()`가 `bootstrap_quality_sidecars(project_dir, db)`를 호출한다.
- 현재 해석: 대시보드 조회가 inspection이 아니라 sidecar backfill write를 동반한다.
- 운영 영향: before/after 비교, 감리, rollback 검증에서 조회만으로 상태가 바뀔 수 있어 운영 신뢰도가 떨어진다.
- 다음 수정 포인트: `inspect_*`와 `bootstrap_*`를 완전히 분리하고, 대시보드 경로는 read-only helper만 사용한다. 수동 backfill은 script 또는 명시적 operator action으로 제한한다.
- confidence: High

### CF-2. Stage 4 runtime audit summary가 남지 않는다

- 증거: `projects/00_test_00/logs/runtime_audit_summary.json`의 마지막 tag는 `stage3_complete`다. `modules/core/stage4_orchestrator.py`는 종료/예외 경로에서 `flush_audit_buffer()`만 호출하고 `write_audit_summary()`는 호출하지 않는다.
- 현재 해석: Stage 4는 실제로 실행됐지만 runtime audit summary에는 닫히지 않는다.
- 운영 영향: Stage 4 성공/실패/종료 상태를 runtime summary 한 장으로 확인할 수 없고, 관측 체계가 Stage 3에서 끊긴다.
- 다음 수정 포인트: Stage 4 정상 종료, 예외 종료, 사용자 중단 종료 모두에서 `stage4_complete` 또는 동등한 summary write를 남기고 `modules/protocols/app_services.py` 설명도 맞춘다.
- confidence: High

### CF-3. Stage 4 firewall 이후 최종 판정과 설명 필드가 섞여 저장된다

- 증거: ep3 1차 `director_selections`는 `REJECT`, `score=44`인데 reason은 강하게 긍정적이다. `episode_production.jsonl` 같은 회차도 `score_breakdown`은 `40+20+20+10+10` 형태로 사실상 고득점 구조를 보존하고 `open_review` 역시 긍정적이다.
- 현재 해석: `44 cap` 자체는 의도된 방화벽 동작이다. 문제는 최종 verdict/score는 post-firewall인데, selection/open_review/score_breakdown은 pre-firewall 톤이 남아 있어 operator 표기가 붕괴한다는 점이다.
- 운영 영향: 사람도 로그를 잘못 읽고, 후속 요약/추천 로직도 혼합된 의미를 소비할 위험이 있다.
- 다음 수정 포인트: firewall trigger 시 `final_reason`, `final_score_breakdown`, `firewall_triggered`, `pre_firewall_score`를 분리 저장하고 UI/요약은 최종 판정용 필드만 읽게 한다.
- confidence: High

### CF-4. Stage 4 retry/cost가 ep1 기준 과도하다

- 증거: `pass_rate_monitor.json`에서 ep1은 9회 시도 후 PASS다. 세션 로그에는 ep1 비용 `$1.1133`, `530,162 tokens`, 총 소요 `_total=2097.86s`가 남아 있다.
- 현재 해석: 현재 파이프라인은 성공은 만들지만 intro episode에서 비용과 시간이 과도하게 소모된다.
- 운영 영향: 운영비, 대기 시간, retry 피로, failure learning noise가 동시에 커진다.
- 다음 수정 포인트: ep1 failure audit와 연결해 precheck, self-critique, patch 진입 기준, retry budget, failure bucket별 fast-fail 정책을 함께 조정한다.
- confidence: High

### 4.2 `designed but confusing`

### DC-1. `REJECT 44` cap 자체는 버그가 아니다

- 증거: `modules/domain/agents/director_ensemble.py`는 contradiction firewall 시 `score = min(score, 44)`를 적용한다. `tests/test_v75c_contradiction_firewall.py`는 CRITICAL 1건 또는 MAJOR 2건에서 REJECT와 44 cap을 직접 검증한다.
- 현재 해석: adaptive floor 45 미만으로 내리는 의도된 방화벽이며, scoring bug가 아니다.
- 운영 영향: 이 규칙을 모르면 `44점` 현상을 자체 버그로 오판한다.
- 다음 수정 포인트: UI/문서에서 `firewall_triggered`와 `pre_firewall_score`를 분리 표기해 `규칙`과 `표기 결함`을 분리한다.
- confidence: High

### DC-2. manual review table과 retrieval telemetry는 저장소가 다르다

- 증거: `episode_quality_observations=0`, `manual_review_rows=0`인데 `retrieval_observation_rows=22`다. `quality_metrics.jsonl`에는 `retrieval_observation`이 22건 남고, calibration helper는 별도로 manual review 부족을 next step으로 반환한다.
- 현재 해석: `episode_quality_observations`는 operator/manual review 저장소이고 retrieval telemetry 저장소가 아니다.
- 운영 영향: manual review 0건을 "retrieval도 안 쌓임"으로 잘못 읽으면 calibration 상태를 오판한다.
- 다음 수정 포인트: calibration UI에서 `manual review`와 `retrieval telemetry`를 분리 표기하고, 둘을 하나의 "observation" 단어로 뭉뚱그리지 않는다.
- confidence: High

### DC-3. `pass_rate_monitor.prev_score`는 최종 점수가 아니라 routing용 원점수다

- 증거: `modules/core/stage4_interview_round.py`는 REJECT 시 `previous_attempt["score"] = director_result.get("pre_firewall_score", score)`로 저장한다. 그래서 ep3는 1차 `REJECT 44` 뒤 2차 기록의 `prev_score=100`이 나온다.
- 현재 해석: patch routing을 위한 설계이며, prior final verdict history가 아니다.
- 운영 영향: raw monitor를 그대로 읽으면 "44점 다음에 왜 prev_score가 100이냐"는 혼선이 생긴다.
- 다음 수정 포인트: `prev_score`를 `routing_score`로 이름 바꾸거나 `final_score`와 `pre_firewall_score`를 동시에 저장한다.
- confidence: High

### DC-4. AuditServiceProtocol 문서 설명이 Stage 4 실제 코드와 어긋난다

- 증거: `modules/protocols/app_services.py`는 Stage 4가 `flush_audit_buffer()`와 `write_audit_summary()`를 모두 쓰는 것처럼 설명하지만, 실제 `stage4_orchestrator.py`에서는 `flush_audit_buffer()`만 확인된다.
- 현재 해석: 런타임 크래시 원인은 아니지만 protocol/doc drift다.
- 운영 영향: 이후 리팩터링이나 테스트 설계에서 Stage 4 audit 완료 조건을 잘못 가정할 수 있다.
- 다음 수정 포인트: Stage 4 observability 수정을 반영한 뒤 protocol 주석과 smoke/integration assertion을 같이 맞춘다.
- confidence: High

### 4.3 `warning noise / false positive`

### WN-1. `scene coverage 0%` / `ending hook 누락` 경고는 ep3 기준 오탐 근거가 강하다

- 증거: ep3 2차 PASS의 `open_review`는 `'씬 반영률 0%'`와 `'엔딩 훅 누락'`을 명백한 false positive로 적고 있다.
- 현재 해석: 현 경고는 일부 구조를 text heuristics로 과도하게 누락 판정한다.
- 운영 영향: Advisory count가 부풀고 실제 문제와 경고 노이즈가 섞인다.
- 다음 수정 포인트: ep3 1~2차 원고와 Blueprint를 calibration corpus로 삼아 scene/hook detector를 재조정한다.
- confidence: High

### WN-2. dialogue ratio 경고는 intro/setup 회차에서 과민하다

- 증거: ep1 PASS와 ep2 PASS의 `open_review`는 낮은 대화 비율을 "회차 특성상 허용 가능한 선택"으로 직접 면책한다.
- 현재 해석: 모든 회차에 같은 dialogue threshold를 적용하면 intro/setup episode를 과하게 치는 경향이 있다.
- 운영 영향: 작가와 운영자가 실제 품질보다 경고 숫자에 먼저 피로해진다.
- 다음 수정 포인트: intro/setup/climax 타입별 threshold 또는 advisory tier 분리를 도입한다.
- confidence: Medium

### WN-3. `InfoParadox('유진우의 의구심')`은 ep3 기준 직접 defect로 보기 어렵다

- 증거: ep3 1차 REJECT row와 후속 `open_review`는 이를 "상대의 표정과 시선에서 추론한 자연스러운 1인칭 서술"로 해석한다.
- 현재 해석: 현 checker가 `mind-reading`과 `inference`를 충분히 분리하지 못한다.
- 운영 영향: POV/knowledge boundary bucket의 신뢰도가 떨어진다.
- 다음 수정 포인트: inference 표현과 실제 전지적 서술을 분리하는 rule/example set을 추가한다.
- confidence: High

### 4.4 `hypothesis pending`

### HP-1. `missing_relation_slice` 반복 경고는 실제 retrieval gap인지 calibration state인지 아직 닫히지 않았다

- 증거: `QualityDashboard.get_retrieval_summary()` 기준 stage4 `coverage_warning_rate=0.75`, `top_warnings=[missing_relation_slice x3]`다. 동시에 `work_guard_exists=False`, `work_focus_rate=0.0`다.
- 현재 해석: 현재 증거만으로는 "relation slice 포장 버그"인지 "work guard 미설정 baseline의 예상 경고"인지 확정할 수 없다.
- 운영 영향: retrieval health를 지금 단계에서 과대 또는 과소평가할 위험이 있다.
- 다음 수정 포인트: `work_guard.yaml`이 실제로 있는 프로젝트에서 같은 지표를 한 번 더 뽑아 비교한다.
- confidence: Medium

---

## 5. 오탐/강등 항목

이번 감리에서 직접 defect 후보에서 내린 항목은 아래와 같다.

- `REJECT 44` 자체는 bug가 아니다. contradiction firewall의 의도된 cap이다.
- `episode_quality_observations = 0`은 missing retrieval bug가 아니다. manual review table이 비어 있는 것이다.
- `work_focus_rate = 0.0`은 retrieval wiring 실패 증거가 아니다. 이번 baseline에는 `work_guard.yaml`이 없다.
- ep3 `scene coverage 0%`, `ending hook 누락`, `InfoParadox('유진우의 의구심')`은 그대로 defect로 적지 않는다.
- ep1/ep2 `dialogue ratio` 경고는 intro/setup episode 특성을 고려해 warning noise로 강등한다.

---

## 6. 현재 우선순위

1. `dashboard read-only화`
2. `Stage 4 observability / 판정 표기 정합성`
3. `calibration / manual-review UX 분리 명시`
4. `retrieval / role-fit 실데이터 캘리브레이션`

부연:

- 2번에는 `firewall 이후 설명 필드 정합성`과 `ep1 retry/cost 폭증 완화`를 함께 묶는다.
- 4번은 `work_guard.yaml`이 실제로 있는 프로젝트에서 다시 검증해야 의미가 있다.

---

## 7. 문서 3-Pass 재감리 결과

### 7.1 Fact pass

- 모든 숫자는 `project_data.db`, `quality_metrics.jsonl`, `pass_rate_monitor.json`, `metrics_20260311_112834.json`, `session_20260311_112831.log` 기준으로 다시 맞췄다.
- `00_test_00`는 문서 전 구간에서 `technical validation baseline`으로만 표기했다.
- `00000`는 과거 historical snapshot으로만 남겼다.

### 7.2 Taxonomy pass

- `REJECT 44`를 bug에서 제외했다.
- `episode_quality_observations=0`을 bug에서 제외했다.
- warning noise와 designed behavior를 confirmed defect와 분리했다.

### 7.3 Actionability pass

- 모든 `confirmed defect`에 코드 후보 영역을 붙였다.
- TF 기존 문서와 충돌하는 표현을 정리했다.
- 다음 엔지니어가 바로 수정 작업을 시작할 수 있도록 `다음 수정 포인트`를 각 블록에 고정했다.

### 7.4 수동 원고 감리 반영

- `docs/2026-03-11/00-test-00-manual-reading-audit.md`를 manual reading layer로 추가했다.
- 수동 판독 기준 최종 원고 `ep_0001.txt` ~ `ep_0004.txt`에는 이번 1-arc 범위에서 확인되는 `hard contradiction`이 없다.
- 다만 Director 전체 등급은 `잘 막음`이 아니라 `부분적`이다.
  - 결과물 기준: ep1~ep4 최종본은 설계 연속성을 대체로 유지했다.
  - 과정 기준: ep1은 `9회` 시도 후 PASS였고, ep3은 `REJECT 44`/`InfoParadox` 오탐이 섞였으며, ep4는 최종 원고에 대사가 많은데도 `대화 0%` telemetry가 남았다.
- 수동 감리로 새로 드러난 text-level 문제는 두 가지다.
  - `Stage 3 blueprint proper noun drift`: arc의 `아퀼라`가 `blueprint_0003/0004`에서 `이클립스`로 흔들렸다.
  - `elapsed time soft drift`: arc의 `약 2주 후`가 blueprint의 `다음 날 오후`, final draft의 `일주일 후`로 완전 복구되지 않았다.
- 이 수동 감리 결과는 현재 우선순위를 뒤집지 않고, 기존 `CF-4`, `WN-2`, `WN-3`를 실제 텍스트 근거로 보강한다.

---

## 8. 참고 근거

- `projects/00_test_00/project_data.db`
- `projects/00_test_00/logs/quality_metrics.jsonl`
- `projects/00_test_00/logs/pass_rate_monitor.json`
- `projects/00_test_00/logs/episode_production.jsonl`
- `projects/00_test_00/logs/runtime_audit.jsonl`
- `projects/00_test_00/logs/runtime_audit_summary.json`
- `projects/00_test_00/logs/metrics/metrics_20260311_112834.json`
- `projects/00_test_00/logs/session_20260311_112831.log`
- `docs/2026-03-05/audit-score-logging-gaps.md`
- `docs/2026-03-07/TF-stage4-ep1-failure-audit.md`
- `docs/2026-03-10/TF-QI-structural-quality-gaps-audit.md`
- `docs/2026-03-10/TF-work-guard-identity-ssot-plan.md`
- `docs/2026-03-11/TF-quality-sidecar-bootstrap.md`
- `docs/2026-03-11/00-test-00-manual-reading-audit.md`
- `docs/2026-03-11/director-quality-audit-00_test_00.md`
- `docs/2026-03-11/pipeline-run-audit-00_test_00.md`

---

## Appendix A. OPUS 감리 reconciliation

`docs/2026-03-11/pipeline-run-audit-00_test_00.md`는 `부분 유효`로 판정한다. 아래 표는 OPUS 주장과 현행 코드/테스트/런타임 로그의 합치 여부를 정리한 것이다.

| OPUS 주장 | 현행 판정 | 근거 | SSOT 반영 방식 |
|---|---|---|---|
| `writing_directive.yaml` JSON 예시 중괄호 때문에 `PromptLoader` 치환이 깨진다 | `merge-confirmed` | `config/prompts/writing_directive.yaml`, `modules/core/prompt_loader.py`, `session_20260311_112831.log`의 반복 경고 | 별도 confirmed defect로 승격하지 않고, Stage 4 품질 저하 보조 근거로 appendix에 반영 |
| `pre_director_manuscript_checker.py`가 스마트따옴표 대화를 놓친다 | `merge-confirmed` | `modules/core/pre_director_manuscript_checker.py`는 ASCII/꺾쇠/직선 작은따옴표만 사용, `modules/validation/pre_llm_validator.py`는 유니코드 따옴표 지원 | warning noise 축의 보강 근거로 반영 |
| 씬 반영률 0% 경고는 warning-only 오탐 축이다 | `merge-confirmed` | `modules/core/pre_director_manuscript_checker.py`의 `[TF-51] FAIL→WARNING`, ep3 PASS open_review의 false positive 판정 | 기존 `WN-1` 보강 근거로 반영 |
| ep1은 `9회 retry / $1.1133 / 약 35분`으로 과도하다 | `merge-confirmed` | `pass_rate_monitor.json`, `session_20260311_112831.log`, `_total=2097.86s` | 기존 `CF-4` 현상 근거로 반영 |
| ChiefWriter는 JSON 응답 경로에 강하게 묶여 있다 | `merge-supporting` | `modules/domain/agents/base_agent.py`의 `response_mime_type=\"application/json\"`, `modules/domain/agents/chief_writer.py`의 `_extract_json_robust()` + `data.get(\"content\", \"\")` | `CF-4`의 구조적 제약 보조 근거로만 반영 |
| `expand_length_prompt`는 `thinking=\"medium\"`을 사용한다 | `merge-supporting` | `modules/domain/agents/chief_writer_quality.py` | `CF-4`의 후보 보조 근거로만 반영 |
| `rubric_score`는 자체적으로 분량 점수를 포함하지 않는다 | `merge-supporting` | `modules/domain/agents/chief_writer_quality.py`의 rubric 항목, 분량 체크는 별도 gate/self-critique 경로 | `CF-4`의 후보 보조 근거로만 반영 |
| JSON mode가 실제로 원고 길이를 15~25% 깎는다 | `merge-hypothesis` | 현행 코드에는 budget 인과를 직접 증명하는 계측이 없음 | `추가 조사 필요`로만 유지, SSOT 본문 미병합 |
| `rubric >= 3.5`가 실파이프라인에서 분량 미달 탈출의 주원인이다 | `merge-hypothesis` | 현재 코드는 gate + 구조 이슈 재검사 + mid-loop rubric 탈출이 혼합돼 있어 단일 원인으로 닫히지 않음 | `추가 조사 필요`로만 유지 |
| V75 초기값 노이즈는 지금 우선 대응 가치가 높다 | `merge-hypothesis` | 현재 SSOT 우선순위와 직접 연결된 blocking 증거 부족 | appendix에만 남기고 우선순위 변경 없음 |
| `chief_writer_quality`에 분량 재검사가 없다 | `exclude-stale` | `modules/domain/agents/chief_writer_quality.py`, `tests/test_chief_writer_quality.py` | SSOT 반영 제외 |
| `_fix_manuscript_issues`에 수정 후 분량 검증이 없다 | `exclude-stale` | `modules/domain/agents/chief_writer_quality.py`, `tests/test_chief_writer_quality.py` | SSOT 반영 제외 |
| self-critique가 분량 때문에 `영원히 medium`이라 무한 루프다 | `exclude-stale` | `MAX_CRITIQUE_ROUNDS`, gate 구조, 분량 재검사, 수정 후 경고 경로, 테스트 | SSOT 반영 제외 |

결론:

- OPUS 문서는 `CF-4 retry/cost 폭증`의 현상 설명과 일부 보조 근거에는 유효하지만, 현재 SSOT의 taxonomy나 우선순위를 뒤집지는 못한다.
- `CF-4`의 원인 설명은 `confirmed cause`와 `candidate cause`를 분리한다.
  - confirmed cause: `writing_directive` 템플릿 포맷 오류, `pre_director_manuscript_checker`의 스마트따옴표 미감지, ep1 retry/cost 현상 그 자체
  - candidate cause: JSON mode budget 영향, `expand_length_prompt`의 thinking 비용, mid-loop rubric 탈출 경로
- 이미 코드와 테스트가 반박하는 OPUS 주장은 `exclude-stale`로 고정한다. 이 appendix는 외부 감리를 SSOT에 흡수한 것이지, 외부 문서에 SSOT를 넘긴 것이 아니다.

---

## Appendix B. Director-quality audit reconciliation

`docs/2026-03-11/director-quality-audit-00_test_00.md`는 `부분 유효`로 판정한다. 이 문서는 `최종 산출물 품질`과 `Director의 서사 판독력`에 대해서는 강한 보강 근거를 제공하지만, `시스템/과정 안정성`은 상대적으로 낙관적으로 본다. 따라서 SSOT 본문 verdict를 뒤집지 않고 아래처럼 보강 근거로만 흡수한다.

| 외부 감리 주장 | 현행 판정 | 근거 | SSOT 반영 방식 |
|---|---|---|---|
| ep1에서 `88점` 고품질 후보도 ending hook drift 때문에 REJECT한 것은 Director 주권주의의 모범 사례다 | `merge-confirmed` | `director_selections(stage=4, ep=1, round=7~8)`, `session_20260311_112831.log`, `00-test-00-manual-reading-audit.md` | `설계 충실도 우선`의 강한 정성 근거로 반영 |
| ep3에서 blueprint의 `이클립스` 오류보다 기발행 원고의 `아퀼라`를 정본으로 취급했다 | `merge-confirmed` | `director_selections(stage=4, ep=3, round=0~1)`, `arc_001.txt`, `blueprint_0003.txt`, `ep_0003.txt` | `published text > flawed blueprint` continuity SSOT 원칙 보강 |
| ep4의 `호텔`, `시장 옷`, `본가 이탈` 디테일은 설계를 해치지 않는 enrich다 | `merge-confirmed` | `ep_0004.txt`, `00-test-00-manual-reading-audit.md`의 `allowed enrichment` 판정 | 최종본 품질 보강 근거로 반영 |
| ep1 `score=30` 자동 REJECT 구간은 상세 breakdown 없이 길이 gate가 우선했다 | `merge-confirmed` | `director_ensemble.py` 분량 미달 조기 반환 분기, `director_selections(ep1 round 0~6)`, `stage_attempts(stage=4, ep=1)` | 기존 `CF-4`와 `Stage 4 observability/표기 정합성` defect 보강 |
| ep3 `후보 C 최우수 + REJECT 44`는 Firewall 개입을 판정문에 더 분명히 써야 한다 | `merge-confirmed` | `director_ensemble.py` firewall cap, `stage4_interview_round.py`의 `pre_firewall_score` 보존, `director_selections(ep3 round 0)` | 기존 `표기/설명 정합성` defect 보강 |
| Python 오탐을 Director가 여러 차례 기각한 것은 실제 판독력이 있다는 증거다 | `merge-supporting` | ep2/ep3/ep4 `open_review`, `00-test-00-manual-reading-audit.md`의 `warning false positive` 재분류 | `Director quality`의 긍정 근거로만 반영. 시스템 신호 품질이 높다는 뜻으로 승격하지 않음 |
| 최종 원고 4편은 `A-` 또는 `상업적 수준`으로 볼 수 있다 | `merge-hypothesis` | 최종본 품질이 높은 것은 맞지만, 등급/상업성은 주관적 해석 비중이 큼 | SSOT 본문 verdict에는 미반영. 외부 감리자의 결과물 중심 총평으로만 보관 |
| ep3의 페이스 불균형은 Director가 놓친 실제 약점이다 | `merge-hypothesis` | 수동 판독상 가능한 지적이지만 단일 샘플의 정성 판단이고 blocking defect 증거는 약함 | `추가 수동 감리 후보`로만 유지 |
| `스스로` 항목은 Director가 놓친 맞춤법 이슈다 | `exclude-stale` | 실제 draft 검색 결과 `스스로`는 정상 표현이고, 외부 문서 자체도 이 항목을 자가 정정하지 못함 | SSOT 반영 제외 |

결론:

- 이 외부 감리는 `Director가 텍스트를 읽고 의미 있는 판정을 내렸다`는 점을 더 강하게 지지한다.
- 반면 SSOT의 본판정인 `Director 전체 성능 = 부분적`은 유지한다. 이유는 SSOT가 결과물만이 아니라 `중간 산출물 drift`, `retry/cost`, `firewall 이후 표기 혼선`, `telemetry noise`까지 함께 보기 때문이다.
- 따라서 이번 반영 후 SSOT 확신도는 `97% 유지`가 적절하다. 외부 감리가 `결과물 품질` 쪽 확신은 올려주지만, 남은 confirmed defect를 추가로 닫아주지는 못했다.
