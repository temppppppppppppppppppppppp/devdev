# 시스템 전역 전수조사 비교·병합 3Pass 최종 감사 보고서
> 조사일: 2026-03-12
> 비교 원본:
> - `docs/2026-03-12/system-wide-full-audit-3pass.md` (Opus 조사 자료)
> - `docs/2026-03-12/system-wide-full-survey-3pass-master-audit.md` (Codex 마스터 조사 자료)
> 기준선: `HEAD=b3cfa0e`, dirty worktree 고정
> 코드 수정: 없음
> 테스트 실행: 없음
> canary/full/live rerun: 없음
> 최종 확신도: 95% (정적 조사 기준 방어 가능한 상한)

## Executive Summary

이번 병합 감사는 Opus 문서의 넓은 탐색 폭과 Codex 마스터 문서의 높은 근거 밀도를 하나로 합친 뒤, 충돌 주장만 다시 소스에 대입하는 방식으로 3Pass 재감리를 수행했다. 결론적으로 Opus 쪽 코드성 주장 5건, 마스터 쪽 증거물/재현성 주장 5건을 유지했고, 나머지 Opus 주요 주장들은 `기각`, `관찰`, `runtime-only`로 하향했다.

최종 retained finding은 `P1 4건`, `P2 3건`, `Observation 1건`이다. 가장 강한 문제는 `Stage 4 PASS_WITH_FIX patch loop의 state_updates merge 계약 드리프트`, `docs/stage_map 상태 원장 충돌`, `dirty lineage/canary 경로의 untracked 의존성`, `멀티-provider SSOT 드리프트(main_a direct call + models.yaml deprecated fallback 잔존)`다.

반대로 두 문서가 충돌하던 주장 중 `Stage 4 re-audit QualityGate 미적용`, `Stage 3 external success 집합 오판`, `Vertex AI 비용 미정의`, `spinners_mod lazy flag 동기화 문제`, `Stage 3 entity_registry 실패 캐시`는 현재 코드/문서/읽기 전용 테스트 기준으로 유지할 수 없었다. 따라서 이번 최종본은 단순 합집합이 아니라 `유지 가능한 주장만 남긴 병합 판정본`이다.

## 조사 범위/금지사항

범위는 사용자가 고정한 `Tracked 소스 전체`로 두고, 아래 항목을 포함했다.

- 백엔드 파이프라인, 설정, 프롬프트, `docs/`, `tests/`, Electron 데스크톱 소스
- tracked 운영 로그와 샘플 산출물
- dirty cluster가 직접 import하거나 운영 재현성에 관여하는 untracked 지원 모듈
- `MagicMock/.../soft_failures.jsonl` 같은 worktree 오염 산출물

명시적 금지사항은 끝까지 유지했다.

- 코드 수정 금지
- 테스트 실행 금지
- canary/full/live rerun 금지
- 기존 dirty 변경 revert 금지

## 기준선과 인벤토리

### 기준선

- `HEAD`: `b3cfa0e`
- `git diff --stat`: `38 files changed / 3449 insertions / 188 deletions`
- `git status --short`: `modified=38`, `untracked=24`
- tracked 파일 수: `4836`
  - `py=628`, `md=480`, `json=421`, `yaml/yml=27`

상위 디렉터리 분포:

| 경로 | tracked 수 |
|---|---:|
| `lite_mode/` | 1554 |
| `test_mode/` | 1554 |
| `docs/` | 411 |
| `tests/` | 290 |
| `modules/` | 253 |
| `logs/` | 189 |
| `백업/` | 137 |
| `projects/` | 125 |
| `treatments/` | 87 |
| `config/` | 55 |
| `geuldobi-desktop/` | 44 |

조사 버킷은 아래 8개로 고정했다.

1. 오케스트레이션/진입점
2. Stage 0-4 계약
3. PASS_WITH_FIX·validation 의미론
4. DB·로그·sink 정합성
5. provider·비용 telemetry
6. scripts·canary 운영 경로
7. 문서 동기화 상태
8. Electron/UI 표면

### 비교 대상 문서의 성격

| 문서 | 성격 | 강점 | 약점 | 병합 시 처리 원칙 |
|---|---|---|---|---|
| `system-wide-full-audit-3pass.md` | Opus broad survey | 넓은 영역을 빠르게 훑어 잠재 결함을 많이 수집 | 설계 갭, 관찰, 실제 버그가 같은 심각도로 섞임 | 주장 단위로 재판정 |
| `system-wide-full-survey-3pass-master-audit.md` | evidence-first master survey | dirty baseline, 문서, 테스트 코드, 로그를 강하게 교차 검증 | 탐색 폭이 Opus보다 좁음 | retained finding의 기본 골격으로 사용 |

## Pass 1 사실 수집

### 버킷별 1차 사실 수집 요약

| 버킷 | 1차 수집 사실 | 1차 근거 |
|---|---|---|
| 오케스트레이션/진입점 | `main_a.py`는 Stage 2/3/4를 thin delegate로 연결하고, lazy init과 context 주입을 맡는다 | `main_a.py:2558-2581`, `main_a.py:2792-2801`, `main_a.py:3350-3454` |
| Stage 계약 | `docs/stage_map/interfaces.md`가 handoff 계약, PASS_WITH_FIX, state_updates merge 규칙을 명시한다 | `docs/stage_map/interfaces.md:28-33` |
| PASS_WITH_FIX 의미론 | Stage 3 external success는 `PASS`, `PASS_WITH_WARNING`만 허용하고, Stage 2/4는 patch + re-audit loop를 갖는다 | `modules/core/stage3_orchestrator.py:763`, `modules/core/stage4_interview_round.py:2458-2467` |
| sink 정합성 | `pass_rate_monitor`와 `failure_analyzer`는 attempt-level lineage key를 사용한다 | `modules/core/pass_rate_monitor.py:29-52`, `modules/core/failure_analyzer.py:299-312`, `modules/core/failure_analyzer.py:356-424` |
| provider telemetry | provider usage는 metrics로 전파되지만 DB `llm_calls`에는 동일한 세부 토큰이 없다 | `modules/domain/agents/base_agent.py:370-400`, `modules/domain/agents/base_agent.py:496-511`, `modules/core/db_manager.py:2982-3015` |
| scripts/canary | canary helper와 runner는 존재하지만 현재 모두 untracked다 | `git status --short`, `modules/core/stage4_canary_tools.py`, `scripts/run_stage4_canary.py` |
| 문서 sync | `doc_status.md`와 `stage1.md`의 상태가 서로 충돌한다 | `docs/stage_map/doc_status.md:16`, `docs/stage_map/stage1.md:176-180` |
| Electron/UI | Electron 패키징은 `dist/backend`, `dist/engine`, `backend.exe`, `engine.exe`, `8300` 포트를 계약으로 쓴다 | `geuldobi-desktop/package.json:41-48`, `geuldobi-desktop/src/main.js:20`, `geuldobi-desktop/src/main.js:82-88`, `geuldobi-desktop/src/main.js:313` |

### 두 문서의 1차 차이

- Opus 문서는 코드 내부 `잠재적 위험`과 `구현 개선 여지`를 폭넓게 끌어왔다.
- 마스터 문서는 dirty cluster, tracked 산출물, 문서 sync, 재현성 문제를 더 강하게 잡았다.
- 병합 시 원칙은 `문제처럼 보이는 코드`가 아니라 `현재 기준선에서 깨진 계약`만 남기는 것으로 고정했다.

## Pass 2 교차 검증

### 1. Stage handoff 계약

`main_a.py`의 Stage 2/3/4 진입 경로는 현재 문서 계약과 일치한다. `main_a.py`는 context를 주입하고 실제 실행은 각 stage orchestrator로 위임한다. 이 항목은 Opus와 마스터가 모두 문제 제기하지 않았고, 재검증에서도 이상이 없었다.

- 코드 근거: `main_a.py:2558-2581`, `main_a.py:2792-2801`, `main_a.py:3350-3454`
- 문서 근거: `docs/stage_map/interfaces.md:11-14`
- 판정: `confirmed`

### 2. PASS_WITH_FIX 의미론

큰 틀의 의미론은 맞다. Stage 3 external success 집합은 여전히 `PASS`, `PASS_WITH_WARNING`만 허용하고, Stage 4는 PASS_WITH_FIX loop를 가진다. 다만 Stage 4 loop 내부에서 `PASS` 재심사 경로는 `state_updates`를 merge하는데, `PASS_WITH_FIX` 반복 경로는 `_re_su`로 덮어쓴다. 문서와 인터페이스는 merge 계약을 명시하고 있으므로 이 부분만 retained finding으로 승격했다.

또한 Opus가 제기한 `재심사 PASS(score < 90)인데 REJECT 전환이 빠진다`는 주장은 유지하지 않았다. 현재 코드는 최종 점수를 `director_score`와 `_director_quality_labels`로 갱신하고, 읽기 전용 테스트 `test_s4_reaudit_qualitygate_rejects_low_score`가 이 경로를 명시적으로 고정한다.

- 코드 근거(유지): `modules/core/stage4_interview_round.py:2458`, `modules/core/stage4_interview_round.py:2467`
- 문서 근거(유지): `docs/stage_map/interfaces.md:31-33`, `docs/stage_map/stage4.md:262-265`
- 코드/테스트 근거(기각): `modules/core/stage4_interview_round.py:2592-2602`, `tests/test_pass_with_fix.py:1493-1518`
- 판정: `partially confirmed`

### 3. sink alignment와 artifact lineage

구현은 실제로 존재한다. `failure_analyzer`는 final/lifecycle sink 사이의 verdict, score, candidate_key, content_hash, artifact_path mismatch를 비교한다. 따라서 `sink alignment는 이름뿐`이라는 류의 주장은 기각한다. 다만 tracked 샘플 `projects/test_project/logs/episode_production.jsonl`은 현재 schema를 대표하지 못하므로, `구현 문제`가 아니라 `샘플 증거물 drift`로 retained했다.

- 코드 근거: `modules/core/failure_analyzer.py:299-312`, `modules/core/failure_analyzer.py:356-424`
- 테스트 근거: `tests/test_failure_analyzer.py:424-527`
- 샘플 근거: `projects/test_project/logs/episode_production.jsonl:1-12`
- 판정: `confirmed with artifact drift`

### 4. provider·비용 telemetry

provider usage에서 `cached_content_token_count`, `thoughts_token_count`가 metrics로 전달되는 것은 확인됐다. 반대로 DB `llm_calls` 저장 경로는 prompt/response/thinking snippet만 저장하고, token 세부값은 넘기지 않는다. 따라서 `metrics는 맞지만 DB sink는 세밀하지 않다`는 retained finding이 성립한다.

Opus의 `Vertex AI 비용이 MODEL_COSTS에 없어 default 폴백을 타서 부정확하다`는 주장은 유지하지 않았다. `_normalize_billable_model()`이 `vertexai:` prefix를 제거하고, `tests/test_cost_tracking.py`가 vertex-prefixed Gemini 모델이 Gemini 가격표를 그대로 쓰는 것을 고정한다.

- provider/metrics 근거: `modules/domain/agents/base_agent.py:370-400`, `modules/core/metrics_collector.py:71-88`, `modules/core/metrics_collector.py:309`
- DB sink 근거: `modules/domain/agents/base_agent.py:496-511`, `modules/core/db_manager.py:2982-3015`
- 기각 근거: `tests/test_cost_tracking.py:101-107`
- 판정: `partially confirmed`

### 5. soft-failure와 MagicMock 경로

현재 코드와 읽기 전용 테스트는 `MagicMock` root를 유효한 프로젝트 경로로 쓰지 않는다. 따라서 `MagicMock 오염이 현재 활성 버그다`라는 주장은 유지하지 않는다. 다만 worktree에는 실제 `MagicMock/.../logs/soft_failures.jsonl` 잔존물이 남아 있으므로, 현재 문제는 `코드 버그`가 아니라 `증거 오염`이다.

- 보호 로직: `modules/core/soft_failure.py:28-54`, `modules/core/soft_failure.py:169`
- 테스트 근거: `tests/test_stage4_post_processor.py:890`, `tests/test_validation_orchestrator_soft_failure.py:25`
- 산출물 근거: `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl`
- 판정: `confirmed as artifact residue`

### 6. scripts/canary 운영 경로

Stage 4 canary helper와 runner는 현재 dirty cluster 핵심 파일이 기대하는 lineage 보강과 함께 들어와 있지만, 전부 untracked다. 따라서 로컬 worktree에서만 재현 가능하고, commit-pin 기준 재현성은 깨진다. 이 항목은 그대로 retained했다.

- import 근거: `modules/core/pass_rate_monitor.py:29`, `modules/core/stage2_finalizer.py:8-10`, `modules/core/stage3_orchestrator.py:14-19`, `modules/core/stage4_interview_round.py:9-11`
- `git` 근거: `git status --short`
- 판정: `confirmed`

### 7. 문서 동기화 상태

`docs/stage_map/README.md`는 mismatch가 있으면 `Code Sync=No`를 두고, 검증된 문서는 `Last Verified`를 채우라고 한다. 그런데 `doc_status.md`는 `stage1.md`를 `Draft | No | TBD`로 남겨 두고, 실제 `stage1.md`는 `2026-03-10 / d2d935b / Code Sync Yes / Verified By Codex`다. 이는 문서 내부 직접 충돌이므로 retained finding이다.

- 문서 근거: `docs/stage_map/README.md:28-29`, `docs/stage_map/doc_status.md:16`, `docs/stage_map/stage1.md:176-180`
- 판정: `confirmed`

### 8. Electron packaging contract

Electron 패키징 계약은 현재 코드와 일치한다. `package.json`의 `dist/backend`, `dist/engine` extraResources와 `src/main.js`의 `backend.exe`, `engine.exe`, `http://127.0.0.1:8300`가 서로 맞물린다. 이 항목은 finding이 아니라 shared non-finding으로 닫는다.

- 패키징 근거: `geuldobi-desktop/package.json:41-48`
- 코드 근거: `geuldobi-desktop/src/main.js:20`, `geuldobi-desktop/src/main.js:82-88`, `geuldobi-desktop/src/main.js:313`
- 판정: `confirmed`

## Pass 3 오탐 제거

### 공유 비finding으로 닫힌 항목

| 항목 | 최종 판정 | 근거 |
|---|---|---|
| Stage handoff 계약 붕괴 | 기각 | `main_a.py`와 `docs/stage_map/interfaces.md`가 일치 |
| Stage 3 external success가 PASS_WITH_FIX를 포함 | 기각 | `modules/core/stage3_orchestrator.py:763`, `tests/test_pass_with_fix.py:943-963` |
| Stage 4 re-audit QualityGate 미적용 | 기각 | `modules/core/stage4_interview_round.py:2592-2602`, `tests/test_pass_with_fix.py:1493-1518` |
| sink alignment가 이름뿐 | 기각 | `modules/core/failure_analyzer.py:356-424`, `tests/test_failure_analyzer.py:424-527` |
| Vertex AI 비용 MODEL_COSTS 미정의 | 기각 | `modules/core/metrics_collector.py:84-88`, `tests/test_cost_tracking.py:101-107` |
| Electron packaging contract 붕괴 | 기각 | `geuldobi-desktop/package.json:41-48`, `geuldobi-desktop/src/main.js:82-88` |

### Opus 주요 주장 판정표

| 항목 | 최종 판정 | 이유 |
|---|---|---|
| TF-IPR-1 PASS_WITH_FIX state_updates 비대칭 | `retained` | PASS merge vs PASS_WITH_FIX overwrite가 실제 코드와 문서에서 충돌 |
| TF-IPR-2 `main_a.py` direct API call | `retained` | `_flash_ask_cb`가 router를 우회하며 문서의 “잔류 2곳만” 주장과 충돌 |
| TF-IPR-3 TruthGate 회상 예외 줄 단위 갭 | `retained` | line-level recall skip이 deceased 행동 라인도 함께 건너뛸 수 있음 |
| TF-IPR-4 `base_agent.py` metrics silent pass | `retained` | metrics end/start 예외가 debug-only로 소거됨 |
| TF-IPR-5 DB 마이그레이션 부분 실패 진행 | `runtime-only` | continue-on-warning 경로는 실제지만, 실사용 스키마 파손 영향은 정적으로 확정 불가 |
| TF-IPR-6 deprecated fallback_chain entry | `retained` | 문서상 제거 완료인데 YAML에 gemini-3.1 entry 잔존 |
| TF-IPR-7 entity_registry 실패 캐시 | `rejected` | 테스트가 동일 arc 무한 재시도 방지 의도를 명시 |
| P2-01 KRW 레버리지 regex 미지원 | `observation` | 기능 갭은 맞지만 현재 계약 위반으로 올리기 어렵다 |
| P2-02 장르 weight YAML 미외부화 | `observation` | 하드코딩은 맞지만 버그 근거는 부족 |
| P2-03 `pass_rate_monitor` 정렬 미보장 | `rejected` | append order 기반 recent slice 외에 실제 오동작 근거가 없다 |
| P2-04 Stage4 QualityGate fix loop 미적용 | `rejected` | 코드/테스트가 반증 |
| P2-05 Stage4 advisory timeout 전략 미문서화 | `runtime-only` | timeout 값은 존재하지만 문서화 부재를 bug severity로 올릴 근거가 약함 |
| P2-06 Stage4 context_builder 50+ silent except | `observation` | debug-heavy except가 많지만 비치명성 설계가 함께 명시됨 |
| P2-07 `constants.py` YAML load silent exception | `observation` | fallback은 사실이나 영향은 bounded fallback 수준 |
| P2-08 `LLMProviderRouter` singleton race | `runtime-only` | 잠재 경합은 추론 가능하나 정적 증거만으로는 불충분 |
| P2-09 `spinners_mod` lazy flag 동기화 타이밍 | `rejected` | `main_a.py:1908-1909`가 lazy import 후 재동기화 |
| P2-10 SemanticPlotGuard 임계값 차이 | `rejected` | fallback 비율 차이는 보이지만 깨진 계약이나 회귀 근거는 확보 못함 |
| P2-11 Stage3 logging 누락 except 2건 | `observation` | 일부 debug-only except는 맞지만 핵심 계약 위반으로 승격할 정도는 아님 |
| P2-12 Vertex AI 비용 MODEL_COSTS 미정의 | `rejected` | `_normalize_billable_model()` + 비용 테스트가 반증 |

## 확정 findings

### F-01. Stage 4 PASS_WITH_FIX loop가 문서화된 `state_updates` merge 계약을 깨뜨린다

- 심각도: `P1`
- canary blocker: `No`
- 문서 불일치: `Yes`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - `docs/stage_map/interfaces.md`와 `docs/stage_map/stage4.md`는 in-place patch 후 `state_updates`를 기존 `final_state_updates`와 merge한다고 적는다.
  - 그러나 `modules/core/stage4_interview_round.py`는 재심사 `PASS` 경로에서만 merge하고, 재심사 `PASS_WITH_FIX` 반복 경로에서는 `_re_su`로 덮어쓴다.
- 직접 근거:
  - 코드: `modules/core/stage4_interview_round.py:2458`, `modules/core/stage4_interview_round.py:2467`
  - 문서: `docs/stage_map/interfaces.md:31-33`, `docs/stage_map/stage4.md:262-265`
- 반대 근거 검토:
  - 최종 `director_score`와 `_director_quality_labels` 갱신은 별도로 존재한다. 즉, 이 finding은 `최종 score 미갱신`이 아니라 `반복 patch state 누적 계약` 문제다.
- 왜 오탐이 아닌가:
  - 같은 loop 안에서 PASS와 PASS_WITH_FIX가 서로 다른 대입 규칙을 사용한다.
- 사용자 영향:
  - 연속 PASS_WITH_FIX 반복 시 이전 iteration의 patch-derived state_updates가 유실될 수 있다.
- 테스트 미실행 사유:
  - 사용자 금지사항에 따라 코드 읽기와 읽기 전용 테스트 열람만 수행했다.

### F-02. `docs/stage_map` 상태 원장과 실제 `stage1.md`가 정면 충돌한다

- 심각도: `P1`
- canary blocker: `No`
- 문서 불일치: `Yes`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - `README.md`는 mismatch가 있으면 `Code Sync=No`, 검증 완료 문서는 `Last Verified`를 채우라고 규정한다.
  - 그런데 `doc_status.md`는 `stage1.md`를 `Draft | No | TBD`로 두고, 실제 `stage1.md`는 `Date: 2026-03-10 / Commit: d2d935b / Code Sync: Yes / Verified By: Codex`다.
- 직접 근거:
  - `docs/stage_map/README.md:28-29`
  - `docs/stage_map/doc_status.md:16`
  - `docs/stage_map/stage1.md:176-180`
- 반대 근거 검토:
  - `stage1.md`를 임시 제외하거나 override한다는 문서는 발견되지 않았다.
- 왜 오탐이 아닌가:
  - 동일 문서 집합 내부에서 직접 모순이 난다.
- 사용자 영향:
  - 감사자와 운영자가 `doc_status.md`를 신뢰하면 `stage1.md`를 미검증 초안으로 오판할 수 있다.
- 테스트 미실행 사유:
  - 문서 조사만 수행했다.

### F-03. 현재 dirty lineage/canary 경로는 untracked 지원 모듈에 의존한다

- 심각도: `P1`
- canary blocker: `Yes`
- 문서 불일치: `Yes`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - dirty baseline의 lineage 보강은 `logging_keys.py`, `artifact_logging.py`, `stage4_canary_tools.py`, `run_stage4_canary.py`에 기대고 있다.
  - 그런데 이 지원 모듈과 관련 테스트는 모두 untracked다.
- 직접 근거:
  - import 경로: `modules/core/pass_rate_monitor.py:29`, `modules/core/stage2_finalizer.py:8-10`, `modules/core/stage3_orchestrator.py:14-19`, `modules/core/stage4_interview_round.py:9-11`
  - `git status --short`의 `?? modules/core/logging_keys.py`, `?? modules/core/artifact_logging.py`, `?? modules/core/stage4_canary_tools.py`, `?? scripts/run_stage4_canary.py`, `?? tests/test_stage4_canary_tools.py`, `?? tests/test_run_stage4_canary.py`
- 반대 근거 검토:
  - 로컬 worktree 안에서는 파일이 존재하므로 당장 import 자체가 깨지지는 않는다.
- 왜 오탐이 아닌가:
  - commit checkout만으로는 현재 lineage/canary 계약을 재현할 수 없다는 점이 핵심이다.
- 사용자 영향:
  - 협업자 checkout, commit-pin 감사, CI 재현, canary 문서 추적성이 모두 흔들린다.
- 테스트 미실행 사유:
  - `git` 상태와 import 관계만으로 판정했다.

### F-04. 멀티-provider SSOT가 완전히 잠기지 않았다

- 심각도: `P1`
- canary blocker: `No`
- 문서 불일치: `Yes`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - `CLAUDE.md`는 production direct `generate_content()` 잔류가 `gemini_provider.py`와 `response_schemas.py` 독스트링 예제의 2곳뿐이라고 적는다.
  - 그러나 `main_a.py`의 `_flash_ask_cb`는 `_c.models.generate_content()`를 직접 호출한다.
  - 동시에 `config/models.yaml`의 `fallback_chain`에는 제거 완료로 적힌 `gemini-3.1-flash-lite-preview` entry가 남아 있다.
- 직접 근거:
  - direct call: `main_a.py:1465-1470`
  - 문서 주장: `CLAUDE.md:115`
  - config 잔존: `config/models.yaml:47-48`, `CLAUDE.md:114`
- 반대 근거 검토:
  - 대부분의 direct caller는 이미 `generate_content_via_router()`로 정리되어 있다. 즉 시스템 전체 전환이 무효라는 뜻은 아니다.
- 왜 오탐이 아닌가:
  - direct call 우회와 deprecated fallback 잔존이 모두 실제 파일에 남아 있다.
- 사용자 영향:
  - provider 전환 문서와 실제 호출 표면이 어긋나고, 특정 경로가 Gemini 고정 동작을 남길 수 있다.
- 테스트 미실행 사유:
  - 호출 경로와 문서만 정적으로 비교했다.

### F-05. TruthGate의 회상 예외가 줄 단위로 적용되어 deceased 행동 검출을 놓칠 수 있다

- 심각도: `P2`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - `TruthGate`는 deceased NPC의 현재 행동/대사를 잡아야 하지만, 회상 키워드가 같은 줄에 있으면 라인 전체를 건너뛴다.
- 직접 근거:
  - `modules/core/truth_gate.py:114-126`
- 반대 근거 검토:
  - 이 로직은 advisory 레벨 경고이며 최종 REJECT 권한은 Director에 있다.
- 왜 오탐이 아닌가:
  - `is_recall = any(kw in line for kw in recall_patterns)`가 이름이 들어간 동일 줄 전체에 적용된다.
- 사용자 영향:
  - 사망 NPC 행동 탐지 false negative가 advisory 단계에서 누락될 수 있다.
- 테스트 미실행 사유:
  - 예시 입력을 실제 실행하지 않고 정적 로직만 검토했다.

### F-06. telemetry 체인은 metrics와 DB 사이에서 같은 수준으로 관측되지 않는다

- 심각도: `P2`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - `BaseAgent._build_metric_usage_payload()`는 `cached_tokens`, `thinking_tokens`를 조립해 metrics로 넘긴다.
  - 하지만 metrics end/start 예외는 debug-only로 소거되는 경로가 남아 있고, DB `save_llm_call()`에는 token 세부 필드가 전달되지 않는다.
- 직접 근거:
  - token payload: `modules/domain/agents/base_agent.py:370-400`
  - debug-only metrics 예외: `modules/domain/agents/base_agent.py:671-679`, `modules/domain/agents/base_agent.py:751-764`, `modules/domain/agents/base_agent.py:1231-1271`
  - DB 저장 호출: `modules/domain/agents/base_agent.py:496-511`
  - DB 시그니처: `modules/core/db_manager.py:2982-3015`
- 반대 근거 검토:
  - `MetricsCollector` 경로 자체는 cached token 할인과 thinking token 집계를 정상적으로 갖고 있다.
- 왜 오탐이 아닌가:
  - 한 sink는 세부 토큰을 갖고, 다른 sink는 잃어버리며, metrics failure는 debug-only라는 비대칭이 코드상 직접 드러난다.
- 사용자 영향:
  - DB-only 포렌식으로는 token granularity 복원이 불가능하고, metrics 계측 오류는 운영에서 놓치기 쉽다.
- 테스트 미실행 사유:
  - 코드 경로와 저장 스키마만 읽었다.

### F-07. tracked `episode_production.jsonl` 샘플이 현재 Stage 4 lifecycle sink schema를 대표하지 못한다

- 심각도: `P2`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - 현재 `failure_analyzer`는 `attempt_key`, `initial_verdict`, `final_verdict`, `final_score`, `patch_trace`, `candidate_key`, `content_hash`, `artifact_path`를 읽는 전제를 갖는다.
  - tracked 샘플의 앞부분은 `TF49b_PREFLIGHT` 이벤트만 담고 있고 위 필드가 없다.
- 직접 근거:
  - 샘플: `projects/test_project/logs/episode_production.jsonl:1-12`
  - 소비 계약: `modules/core/failure_analyzer.py:299-312`, `modules/core/failure_analyzer.py:356-424`
  - 테스트 기대치: `tests/test_failure_analyzer.py:424-527`
- 반대 근거 검토:
  - 코드와 테스트는 최신 schema를 기준으로 서로 일치한다.
- 왜 오탐이 아닌가:
  - 문제의 대상이 코드가 아니라 tracked 샘플의 대표성 부족이기 때문이다.
- 사용자 영향:
  - 이 파일을 기준 샘플로 삼는 감사는 lifecycle sink 계약을 잘못 이해할 수 있다.
- 테스트 미실행 사유:
  - 정적 로그 열람만 수행했다.

### F-08. soft-failure 코드는 방어되었지만 worktree 증거는 아직 오염돼 있다

- 심각도: `Observation`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - 현재 코드는 `MagicMock` root를 유효 프로젝트 경로로 쓰지 않아야 한다.
  - 그러나 worktree에는 `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl` 잔존물이 실제 남아 있다.
- 직접 근거:
  - 보호 로직: `modules/core/soft_failure.py:28-54`, `modules/core/soft_failure.py:169`
  - 테스트: `tests/test_stage4_post_processor.py:890`, `tests/test_validation_orchestrator_soft_failure.py:25`
  - 잔존 산출물: `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl`
- 반대 근거 검토:
  - 현재 코드 기준으로 같은 오염이 재발한다고 단정할 근거는 없다.
- 왜 오탐이 아닌가:
  - 대상이 `현재 코드 버그`가 아니라 `현재 worktree 증거 오염`이기 때문이다.
- 사용자 영향:
  - 느슨한 수동 로그 스캔이나 산출물 수집기가 pseudo-project 로그를 실제 장애로 오해할 수 있다.
- 테스트 미실행 사유:
  - 잔존 파일 열람만 수행했다.

## 제외된 오탐 및 하향 조정

| 항목 | 최종 상태 | 이유 |
|---|---|---|
| Stage 3 Python이 `final_verdict`를 읽는 것은 대원칙 위반 | `rejected` | 판정이 아니라 routing이다 |
| Stage 4 re-audit PASS + low score가 PASS로 남는다 | `rejected` | 코드/테스트가 REJECT 전환을 고정 |
| Stage 3 entity_registry 실패 캐시는 영구 오염 버그다 | `rejected` | 동일 arc 무한 재시도 방지 의도가 테스트 주석으로 명시 |
| `pass_rate_monitor` records 정렬 미보장 | `rejected` | 실제 오동작 근거 확보 실패 |
| Vertex AI 비용 계산은 default 폴백이라 틀리다 | `rejected` | prefix 정규화와 비용 테스트가 반증 |
| `spinners_mod` lazy flag는 한 번만 동기화된다 | `rejected` | lazy import 후 재동기화 코드 존재 |
| `LLMProviderRouter` singleton race | `runtime-only` | 경합 가능성은 추론되나 증거 부족 |
| advisory timeout 전략 미문서화 | `runtime-only` | timeout 값은 있으나 문서 gap만으로 severity 상승 불가 |
| Stage4 context_builder silent except 다수 | `observation` | debug-heavy except는 사실이나 비치명성 설계가 함께 보임 |
| `constants.py` YAML load silent exception | `observation` | fallback은 bounded startup fallback |
| KRW 레버리지 regex 미지원 | `observation` | 기능 갭은 맞지만 현재 계약 위반으로 못 올림 |
| validation weight YAML 미외부화 | `observation` | 하드코딩 사실만으로 bug 판정 불가 |
| SemanticPlotGuard fallback threshold 차이 | `rejected` | 계약 위반이나 회귀 근거 불충분 |
| DB migration 부분 실패 진행 | `runtime-only` | continue-on-warning은 보였으나 실제 파손 영향은 실행 없이 확정 못함 |

## 확신도 ledger

| 항목 | 점수 |
|---|---:|
| 8개 버킷 인벤토리 완료 | +70 |
| dirty cluster 38개 tracked 변경 추적 완료 | +10 |
| 핵심 계약 2중 근거 확보 | +10 |
| 문서-코드-테스트 충돌 주장 재판정 완료 | +5 |
| Pass 3 오탐 제거 및 병합 정리 완료 | +5 |
| 테스트 실행/라이브 rerun 금지 | -2 |
| 대형 fixture는 인벤토리 + 대표 샘플 정책만 적용 | -1 |
| runtime-only 항목(마이그레이션/timeout/router race) 잔존 | -1 |
| tracked 샘플 로그 drift와 MagicMock residue | -1 |
| 합계 | **95** |

판정 메모:

- 95%는 현재 제약 하에서 방어 가능한 상한이다.
- 95%를 넘기지 않은 이유는 `실행 금지` 때문에 runtime-only 항목을 닫을 수 없기 때문이다.
- 따라서 이번 문서는 “정적 근거로 닫을 수 있는 것까지 닫은 최종판”으로 본다.

## 잔여 불확실성

| 항목 | 상태 | 상한 이유 |
|---|---|---|
| DB migration 부분 실패의 실제 후행 파손 범위 | `runtime-only` | 실패 유도 마이그레이션 없이 영향도를 확정할 수 없다 |
| advisory timeout이 실운영에서 체감 지연을 얼마나 만드는지 | `runtime-only` | hung advisor 상황을 실제로 재현하지 않았다 |
| shared router singleton의 경합 가능성 | `runtime-only` | 동시성 실행 없이 정적으로만 검토했다 |
| 대형 fixture 숲 전체 내용 일반화 | `bounded` | 인벤토리 전수는 했지만 내용 검증은 대표 샘플만 사용했다 |

## 부록 A. Evidence Index

| id | subsystem | claim | evidence_type | file_ref | risk | confidence_delta | status |
|---|---|---|---|---|---|---:|---|
| E-001 | orchestrator | Stage handoff 계약은 현재 문서와 일치한다 | code+doc | `main_a.py:2558-2581`, `docs/stage_map/interfaces.md:11-14` | baseline | +2 | confirmed |
| E-002 | stage3 semantics | Stage 3 external success는 `PASS`, `PASS_WITH_WARNING`만 허용한다 | code+test | `modules/core/stage3_orchestrator.py:763`, `tests/test_pass_with_fix.py:943-963` | P0 오탐 제거 | +2 | confirmed |
| E-003 | stage4 semantics | re-audit PASS low-score는 REJECT 전환된다 | code+test | `modules/core/stage4_interview_round.py:2592-2602`, `tests/test_pass_with_fix.py:1493-1518` | P2 오탐 제거 | +2 | rejected |
| E-004 | stage4 PWF | PASS_WITH_FIX 반복 경로는 `state_updates`를 overwrite한다 | code | `modules/core/stage4_interview_round.py:2458`, `modules/core/stage4_interview_round.py:2467` | P1 | +3 | confirmed |
| E-005 | stage4 docs | Stage 4 문서는 patch `state_updates` merge를 명시한다 | doc | `docs/stage_map/interfaces.md:31-33`, `docs/stage_map/stage4.md:262-265` | P1 | +2 | confirmed |
| E-006 | routing/SSOT | `_flash_ask_cb`는 router를 우회한다 | code | `main_a.py:1465-1470` | P1 | +2 | confirmed |
| E-007 | routing/docs | 문서는 production direct call 잔류가 2곳뿐이라 적는다 | doc | `CLAUDE.md:115` | P1 | +1 | confirmed |
| E-008 | config SSOT | deprecated fallback_chain entry가 여전히 남아 있다 | config+doc | `config/models.yaml:47-48`, `CLAUDE.md:114` | P2/Obs | +1 | confirmed |
| E-009 | truth gate | recall keyword가 같은 줄의 deceased 행동 라인도 건너뛴다 | code | `modules/core/truth_gate.py:114-126` | P2 | +2 | confirmed |
| E-010 | telemetry | metrics는 cached/thinking token을 받는다 | code | `modules/domain/agents/base_agent.py:370-400`, `modules/core/metrics_collector.py:309` | baseline | +1 | confirmed |
| E-011 | telemetry | DB `llm_calls`는 token granularity를 저장하지 않는다 | code | `modules/domain/agents/base_agent.py:496-511`, `modules/core/db_manager.py:2982-3015` | P2 | +2 | confirmed |
| E-012 | observability | metrics 예외가 debug-only로 소거된다 | code | `modules/domain/agents/base_agent.py:671-679`, `modules/domain/agents/base_agent.py:751-764`, `modules/domain/agents/base_agent.py:1231-1271` | P2 | +2 | confirmed |
| E-013 | sink lineage | `failure_analyzer`는 verdict/score/key/hash/path mismatch를 실제로 비교한다 | code+test | `modules/core/failure_analyzer.py:356-424`, `tests/test_failure_analyzer.py:424-527` | 오탐 제거 | +2 | confirmed |
| E-014 | sample artifact | tracked `episode_production.jsonl`은 현재 schema를 대표하지 못한다 | artifact | `projects/test_project/logs/episode_production.jsonl:1-12` | P2 | +1 | confirmed |
| E-015 | docs sync | `doc_status.md`와 `stage1.md`가 직접 충돌한다 | doc | `docs/stage_map/doc_status.md:16`, `docs/stage_map/stage1.md:176-180` | P1 | +2 | confirmed |
| E-016 | canary reproducibility | dirty lineage/canary 지원 모듈이 untracked다 | git+code | `git status --short`, `modules/core/pass_rate_monitor.py:29`, `modules/core/stage4_interview_round.py:9-11` | P1 | +2 | confirmed |
| E-017 | soft failure | 현재 코드는 `MagicMock` root를 무시한다 | code+test | `modules/core/soft_failure.py:28-54`, `tests/test_stage4_post_processor.py:890` | 오탐 제거 | +1 | confirmed |
| E-018 | soft failure residue | worktree에 `MagicMock/.../soft_failures.jsonl`가 남아 있다 | artifact | `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl` | Observation | 0 | confirmed |
| E-019 | cost model | vertex-prefixed Gemini 모델은 Gemini 가격표를 그대로 사용한다 | code+test | `modules/core/metrics_collector.py:84-88`, `tests/test_cost_tracking.py:101-107` | P2 오탐 제거 | +2 | rejected |
| E-020 | stage3 cache | entity_registry failure cache는 무한 재시도 방지 의도가 테스트에 명시된다 | code+test | `modules/core/stage3_orchestrator.py:799-807`, `tests/test_stage3_orchestrator.py:199-203` | P1 오탐 제거 | +2 | rejected |
| E-021 | advisory timeout | advisory chain timeout 값은 존재하지만 severity는 정적으로 확정 못함 | code | `modules/core/stage4_interview_round.py:3384-3408` | runtime-only | -1 | runtime-only |
| E-022 | router singleton | shared router race는 추론 가능하나 정적 증거만으로 부족하다 | code | `modules/core/llm_router.py:131-138` | runtime-only | -1 | runtime-only |

## 부록 B. 버킷 커버리지 표

| 버킷 | 커버리지 | 비고 |
|---|---|---|
| 오케스트레이션/진입점 | 완료 | `main_a.py` 주요 stage 진입 경로 확인 |
| Stage 0-4 계약 | 완료 | `interfaces.md`, 개별 stage 문서, orchestrator 대조 |
| PASS_WITH_FIX·validation 의미론 | 완료 | Stage 2/3/4 코드 + 읽기 전용 테스트 대조 |
| DB·로그·sink 정합성 | 완료 | `db_manager`, `pass_rate_monitor`, `failure_analyzer`, sample artifact 대조 |
| provider·비용 telemetry | 완료 | provider usage, metrics, DB `llm_calls`, cost tests 대조 |
| scripts·canary 운영 경로 | 완료 | import 관계, untracked 상태, runner/helper 확인 |
| 문서 동기화 상태 | 완료 | `docs/stage_map` 내부 원장 및 stage 문서 대조 |
| Electron/UI 표면 | 완료 | `package.json`, `src/main.js` 계약 확인 |
