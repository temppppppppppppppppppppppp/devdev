# 시스템 전역 전량 전수조사·3Pass 마스터 감사 보고서

> 조사일: 2026-03-12
> 조사 방식: 읽기 전용 전수조사 + 3Pass 재감리
> 기준선: dirty worktree 고정
> 코드 수정: 없음
> 테스트 실행: 없음
> canary/full/live rerun: 없음
> 최종 확신도: 95%

## Executive Summary

이번 감사는 `HEAD=b3cfa0e` 위의 현재 dirty worktree를 기준선으로 고정하고, tracked 소스 전체를 인벤토리한 뒤 8개 조사 버킷을 3pass로 재감리한 결과다. 결론부터 말하면 Stage 0→4 계약, PASS_WITH_FIX 의미론, sink alignment 구현, provider→metrics 비용 telemetry, Electron 패키징 계약은 현재 dirty worktree 내부에서 대체로 일관된다. 즉, 이번 변경축의 중심은 "핵심 파이프라인 붕괴"가 아니라 "로그/산출물 계보 강화, PASS_WITH_FIX 재감리 보강, canary 자동화, 감사 문서 축적"이다.

확정 finding은 5건이다. 이 중 P1은 2건이며 둘 다 재현성/문서 신뢰성 문제다. `docs/stage_map`의 상태 원장이 실제 `stage1.md`와 정면 충돌하고, 현재 dirty cluster의 핵심 로깅/산출물 계보 기능은 tracked 파일이 untracked 지원 모듈에 의존한다. 나머지 P2 3건은 tracked Stage 4 샘플 로그의 schema drift, DB LLM 로그의 token telemetry 누락, MagicMock soft-failure 잔존 아티팩트다. 즉, 현재 위험의 중심은 "운영 계약과 증거물의 정합성"이지 "즉시 확인된 코드상 오동작"이 아니다.

95%는 방어 가능한 상한이다. 8개 버킷 전수 인벤토리, 38개 tracked dirty cluster 추적, 핵심 계약의 2중 근거 확보, 오탐 제거까지는 완료했다. 다만 테스트 실행과 live rerun이 금지되어 있어 런타임 폐쇄 검증은 일부러 남겨 두었다.

## 조사 범위/금지사항

범위는 사용자가 고정한 `Tracked 소스 전체`다. 포함 대상은 백엔드 파이프라인, 설정/프롬프트, `docs/`, `tests/`의 읽기 전용 계약 증거, Electron 데스크톱 소스, tracked 운영 로그/산출물이다. 현재 dirty worktree에만 존재하는 untracked 파일은 두 경우에만 조사 대상으로 포함했다.

- 현재 dirty baseline의 재현성에 직접 영향을 주는 경우
- tracked 변경 파일의 import/운영 경로를 성립시키는 경우

이번 감사에서 명시적으로 금지한 행위는 아래와 같다.

- 코드 수정
- 테스트 실행
- canary/full/live rerun
- 기존 dirty 변경의 revert

순환근거 방지를 위해 이미 존재하던 다른 감사 초안 문서는 인벤토리만 수행했고, 최종 판단 근거는 코드/문서/로그/`git` 메타데이터/읽기 전용 테스트에서만 채택했다.

## 기준선과 인벤토리

### 기준선

- `HEAD`: `b3cfa0e`
- 최근 커밋 흐름:
  - `b3cfa0e` feat: TF-IPG InPlace Patch Guard 강화 + Control-Treatment 감사 + 신규 모듈/테스트 보강
  - `3614a7c` feat: 전량 동기화 — Bible/Treatment 번호 체계 정리 + Desktop UI/API 확장 + 감사문서 + 신규 모듈(semantic_query_broker/soft_failure) + 테스트 보강
  - `ea5ae7f` Integrate quality, provider, and UI upgrades
  - `d2d935b` feat: Continuity Packet 1차+확장 구현 + DB 활용 극대화 코덱스 + Desktop UI/품질 개선
  - `3a00c12` feat: Desktop UI 개선 + 배포 빌드 파이프라인 + Treatment/Bible 데이터 동기화

### dirty worktree 스냅샷

```text
38 files changed, 3449 insertions(+), 188 deletions(-)
modified=38
untracked=60
```

dirty cluster는 단일 축으로 설명 가능했다. 변경축은 다음 여섯 묶음으로 정리된다.

| 묶음 | 대표 파일 | 해석 |
|---|---|---|
| Stage/PWF 보강 | `main_a.py`, `modules/core/stage2_finalizer.py`, `modules/core/stage3_orchestrator.py`, `modules/core/stage4_interview_round.py`, `modules/domain/agents/chief_writer.py` | Stage handoff와 PASS_WITH_FIX 재심사 강화 |
| sink/artifact lineage | `modules/core/pass_rate_monitor.py`, `modules/core/failure_analyzer.py`, `modules/core/db_manager.py` | attempt_key, artifact_path, content_hash 계보 강화 |
| telemetry | `modules/domain/agents/base_agent.py`, `modules/core/metrics_collector.py`, `modules/core/providers/gemini_provider.py`, `modules/core/providers/vertex_provider.py` | cached/thinking token 비용 추적 강화 |
| soft-failure | `modules/core/soft_failure.py`, `modules/core/stage4_post_processor.py`, `modules/validation/validation_orchestrator.py` | MagicMock 경로 오염 방지 및 구조화된 경고 기록 |
| docs/runbook | `docs/2026-03-12/*`, `docs/stage_map/*`, `config/prompts/chief_writer.yaml` | 변경축 문서화 및 운영 시나리오 반영 |
| sample artifact | `projects/test_project/logs/episode_production.jsonl` | tracked 샘플 로그 갱신 흔적 |

### tracked 파일 인벤토리

```text
TOTAL=4836
py=628
md=480
json=421
yaml_yml=27
```

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

대형 fixture 숲 처리 원칙:

- `lite_mode/`, `test_mode/`, `백업/`은 tracked 목록 전수 인벤토리만 수행했다.
- 대표 샘플 파일명은 확인했다.
  - `lite_mode/ARCHITECTURE.md`, `lite_mode/bridge/gemini_driver.py`
  - `test_mode/ARCHITECTURE.md`, `test_mode/bridge/gemini_driver.py`
  - `백업/0_합본.txt`, `백업/INVESTMENT_TECH_WHITEPAPER.md`
- 이 숲들에 대해서는 생산 경로와 직접 연결된 근거가 없는 한 동작 일반화를 하지 않았다.
- `build/`, `dist/`는 디렉터리는 존재하지만 tracked 파일은 `0`개였다.

## Pass 1 사실 수집

### 버킷별 사실 수집 요약

| 버킷 | Pass 1 사실 | 1차 근거 |
|---|---|---|
| 오케스트레이션/진입점 | `main_a.py`는 Stage 0/1 thin delegate, Stage 2/3 context 주입, Stage 4 lazy init 후 orchestrator 위임 구조다. | `main_a.py:2478-2492`, `main_a.py:2558-2581`, `main_a.py:2792-2801`, `main_a.py:3350-3454` |
| Stage 0-4 계약 | `docs/stage_map/interfaces.md`는 Stage handoff와 PASS_WITH_FIX, `state_updates` merge 우선순위를 명시한다. | `docs/stage_map/interfaces.md:11-33` |
| PASS_WITH_FIX 의미론 | Stage 3 외부 성공 집합은 `PASS`/`PASS_WITH_WARNING`이고, Stage 2/4는 PASS_WITH_FIX patch+re-audit loop와 PF-3를 구현한다. | `modules/core/stage3_orchestrator.py:760-763`, `modules/core/stage2_finalizer.py:659-724`, `modules/core/stage2_finalizer.py:800-811`, `modules/core/stage4_interview_round.py:2332-2385`, `modules/core/stage4_interview_round.py:2587-2664` |
| DB/로그/sink 정합성 | `pass_rate_monitor`는 attempt linkage 필드를 보유하고, `failure_analyzer`는 final/lifecycle sink 간 verdict/score/key/hash/path mismatch를 비교한다. | `modules/core/pass_rate_monitor.py:32-56`, `modules/core/pass_rate_monitor.py:129-192`, `modules/core/failure_analyzer.py:286-313`, `modules/core/failure_analyzer.py:356-524` |
| provider/비용 telemetry | Gemini/Vertex provider가 cached/thinking token usage를 노출하고, `BaseAgent`가 이를 누적해 `MetricsCollector.end_call()`로 전달한다. | `modules/core/providers/gemini_provider.py:32-41`, `modules/core/providers/vertex_provider.py:101-110`, `modules/domain/agents/base_agent.py:280-281`, `modules/domain/agents/base_agent.py:370-400`, `modules/core/metrics_collector.py:205-301` |
| scripts/canary 운영 경로 | Stage 4 canary helper와 runner가 존재하고 hard gate를 정의하지만 모두 untracked 상태다. | `modules/core/stage4_canary_tools.py:23-27`, `modules/core/stage4_canary_tools.py:86-120`, `modules/core/stage4_canary_tools.py:257-322`, `scripts/run_stage4_canary.py:82-110`, `git status --short` |
| 문서 동기화 | `docs/stage_map/README.md`의 규칙과 `doc_status.md`의 `stage1.md` 행이 실제 `stage1.md` 말미와 충돌한다. | `docs/stage_map/README.md:26-29`, `docs/stage_map/doc_status.md:13-21`, `docs/stage_map/stage1.md:172-176` |
| Electron/UI 표면 | 데스크톱 패키징은 `dist/backend`, `dist/engine`, `backend.exe`, `STATUS_BASE_URL=http://127.0.0.1:8300` 계약을 사용한다. | `geuldobi-desktop/package.json:39-52`, `geuldobi-desktop/src/main.js:20`, `geuldobi-desktop/src/main.js:82-89`, `geuldobi-desktop/src/main.js:312-313` |

### dirty cluster 설명 가능성

38개 tracked 변경 파일은 아래 한 줄로 요약 가능했다.

> PASS_WITH_FIX 재감리 강화 + attempt lineage/artifact linkage 추가 + 비용 telemetry 보강 + soft-failure 경로 정리 + Stage 4 canary 자동화/문서화

설명되지 않는 사이드 이펙트는 2건만 남았다.

- tracked 샘플 로그 `projects/test_project/logs/episode_production.jsonl`의 schema가 현재 sink 계약을 대표하지 못한다.
- worktree에 `MagicMock/.../logs/soft_failures.jsonl` 잔존물이 남아 있어 현재 코드 수정보다 오래된 행위를 보여 준다.

둘 다 "코드 동작 자체"보다 "증거물의 최신성" 문제로 분류했다.

## Pass 2 교차 검증

### 1. Stage handoff 계약

코드와 문서는 일치했다. `main_a.py`는 Stage 2에서 `Stage2Context.from_app(self)`를 주입하고 `stage_2_arcs_async_logic()`를 호출하며, Stage 3에서는 `Stage3Context.from_app(self)` 이후 `stage_3_batch_blueprinting()`로 위임한다. Stage 4는 `StateTracker`, `WorldState`, `FactLedger`를 lazy init한 뒤 `Stage4Context`에 주입하고 `stage_4_v2_chief_writer()`로 넘긴다. 이 구조는 `docs/stage_map/interfaces.md`의 Stage 0→4 handoff 계약과 맞다.

교차 근거:

- 코드 1차: `main_a.py:2558-2581`, `main_a.py:2792-2801`, `main_a.py:3350-3454`
- 문서 2차: `docs/stage_map/interfaces.md:11-14`

판정: `confirmed`

### 2. PASS_WITH_FIX 외부/내부 의미론

PASS_WITH_FIX 의미론은 dirty worktree 내부에서 정합적이었다.

- Stage 3는 `PASS_WITH_FIX`를 외부 성공으로 취급하지 않는다.
- Stage 2는 `PASS_WITH_FIX`에 대해 patch + Director 재심사를 최대 3회 반복하고, PF-3로 "패치본 채택 + 최종 REJECT" 경로를 남긴다.
- Stage 4는 patch trace, shrink guard, re-audited final score, `director_score`, `_director_quality_labels`를 최종 verdict 기준으로 갱신한다.
- `ChiefWriter`의 structural patch는 localizable issue에만 적용되고, `global` 분류면 구조패치 대신 fallback 이유를 남긴다.

교차 근거:

- 코드 1차: `modules/core/stage3_orchestrator.py:760-763`, `modules/core/stage2_finalizer.py:659-724`, `modules/core/stage2_finalizer.py:800-811`, `modules/core/stage4_interview_round.py:2332-2385`, `modules/core/stage4_interview_round.py:2587-2664`, `modules/domain/agents/chief_writer.py:1066-1085`, `modules/domain/agents/chief_writer.py:1314-1343`
- 테스트 2차: `tests/test_pass_with_fix.py:943-963`, `tests/test_pass_with_fix.py:1468-1510`, `tests/test_pass_with_fix.py:2010-2075`, `tests/test_stage4_interview_round.py:1387-1393`, `tests/test_stage4_interview_round.py:1536-1540`, `tests/test_stage4_interview_round.py:1597-1605`
- 문서 3차: `docs/stage_map/interfaces.md:28-33`, `docs/stage_map/stage2.md:147-151`, `docs/stage_map/stage3.md:131-137`, `docs/stage_map/stage4.md:255-275`

판정: `confirmed`

### 3. sink alignment와 artifact lineage

구현은 명시적이다. `pass_rate_monitor.AttemptRecord`는 `attempt_key`, `final_verdict`, `patch_strategy`, `candidate_key`, `content_hash`, `artifact_path`를 보유한다. `stage3_orchestrator`와 `stage2_finalizer`는 이 필드를 DB/monitor에 동시에 저장한다. `failure_analyzer.sink_alignment_summary()`는 final/lifecycle sink 간 verdict/score mismatch, candidate/content/artifact mismatch, metadata missing, artifact missing file, legacy key 시도를 전부 보고한다.

교차 근거:

- 코드 1차: `modules/core/pass_rate_monitor.py:32-56`, `modules/core/pass_rate_monitor.py:167-192`, `modules/core/stage3_orchestrator.py:1270-1316`, `modules/core/stage2_finalizer.py:1383-1387`, `modules/core/stage2_finalizer.py:1529-1533`, `modules/core/failure_analyzer.py:286-313`, `modules/core/failure_analyzer.py:356-524`
- 테스트 2차: `tests/test_stage3_orchestrator.py:524-582`, `tests/test_v55_modules.py:237`, `tests/test_failure_analyzer.py:337-527`

판정: `confirmed`

단, tracked 샘플 로그 `projects/test_project/logs/episode_production.jsonl`은 위 계약을 대표하지 못했다. 이 지점은 finding으로 승격했다.

### 4. provider→metrics 비용 telemetry

provider와 metrics collector 사이의 cached/thinking token propagation은 구현돼 있다. Gemini와 Vertex provider는 `thoughts_token_count`, `cached_content_token_count`를 usage로 반환하고, `BaseAgent`는 이를 `_build_metric_usage_payload()`에서 `cached_tokens`, `thinking_tokens`로 변환해 `MetricsCollector.end_call()`에 전달한다. `MetricsCollector.calculate_cost()`는 cache-aware discount를 적용한다.

교차 근거:

- 코드 1차: `modules/core/providers/gemini_provider.py:35-40`, `modules/core/providers/vertex_provider.py:104-109`, `modules/domain/agents/base_agent.py:370-400`, `modules/domain/agents/base_agent.py:667-677`, `modules/domain/agents/base_agent.py:747-760`, `modules/core/metrics_collector.py:205-301`
- 코드 2차: `rg -n` 결과로 `save_llm_call()`과 `end_call()` 경로를 별도 확인

판정: `confirmed`

단, DB 로그 sink는 동일한 세부 token usage를 저장하지 않는다. 이 지점은 finding으로 승격했다.

### 5. soft-failure와 MagicMock 경로 오염

현재 코드와 읽기 전용 테스트는 `MagicMock` root를 무시한다. `_coerce_path()`는 `unittest.mock` 타입을 `None`으로 변환하고, `resolve_project_log_dir()`는 유효한 root나 db_path가 있는 경우에만 `logs` 경로를 반환한다. `Stage4PostProcessor`와 `ValidationOrchestrator`는 이 헬퍼를 경유한다. 테스트도 `MagicMock` root일 때 `soft_failures.jsonl`이 생성되지 않아야 함을 명시한다.

교차 근거:

- 코드 1차: `modules/core/soft_failure.py:28-63`, `modules/core/soft_failure.py:118-170`, `modules/core/stage4_post_processor.py:26-56`, `modules/core/stage4_post_processor.py:1204-1210`, `modules/validation/validation_orchestrator.py:276-322`
- 테스트 2차: `tests/test_validation_orchestrator_soft_failure.py:28-36`, `tests/test_stage4_post_processor.py:858-890`
- worktree 3차: `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl`

판정: `confirmed`

문제는 현재 코드가 아니라 잔존 아티팩트다. 이 또한 finding으로 승격했다.

### 6. canary/runbook/체크리스트와 현재 코드의 일치 여부

현재 worktree 안의 canary 구현 자체는 내부 일관성이 높다. `stage4_canary_tools.py`는 `from_ep=1`만 허용하고, pass rate monitor 누락, final/lifecycle sink 누락, mismatch, `legacy_key_attempts`, artifact 문제를 hard gate로 잡는다. `run_stage4_canary.py`는 Stage 4 실행 후 `pass_rate_monitor.save()`와 `_flush_audit_buffer()`를 강제하고 나서만 분석한다. 읽기 전용 테스트도 이 순서를 검증한다.

교차 근거:

- 코드 1차: `modules/core/stage4_canary_tools.py:23-27`, `modules/core/stage4_canary_tools.py:86-120`, `modules/core/stage4_canary_tools.py:257-322`, `scripts/run_stage4_canary.py:82-110`
- 테스트 2차: `tests/test_stage4_canary_tools.py:95-144`, `tests/test_run_stage4_canary.py:7-30`
- `git` 3차: `git status --short`에서 canary 코드/테스트가 모두 untracked

판정: `confirmed`

문제는 구현 품질이 아니라 baseline 재현성이다. 이 지점은 finding으로 승격했다.

### 7. stage_map 문서 sync

`docs/stage_map/README.md`는 코드 변경 시 동일 세션에서 stage 파일을 갱신하고, known mismatch가 있으면 `Code Sync`를 `No`로 두라고 규정한다. 그러나 `doc_status.md`는 `stage1.md`를 `Draft | No | TBD`로 표기하는 반면, 실제 `stage1.md` 말미는 `2026-03-10`, `d2d935b`, `Code Sync Yes`, `Verified By Codex`다.

교차 근거:

- 문서 1차: `docs/stage_map/README.md:26-29`
- 문서 2차: `docs/stage_map/doc_status.md:15-16`
- 문서 3차: `docs/stage_map/stage1.md:172-176`

판정: `confirmed`

### 8. Electron packaging contract

Electron 표면은 dirty worktree 내부에서 일치한다. `package.json`은 `../dist/backend`, `../dist/engine`을 extraResources로 패키징하며, `src/main.js`는 개발 모드에서 `uvicorn modules.api.bridge_server:app --port 8300`, 배포 모드에서 `resources/backend/backend.exe`와 `resources/engine/engine.exe`를 사용한다. IPC 브리지 URL도 `http://127.0.0.1:8300`으로 고정된다.

교차 근거:

- 패키징 1차: `geuldobi-desktop/package.json:39-52`
- 런타임 2차: `geuldobi-desktop/src/main.js:20`, `geuldobi-desktop/src/main.js:82-89`, `geuldobi-desktop/src/main.js:312-313`

판정: `confirmed`

## Pass 3 오탐 제거

재감리 루프에서 제거한 주요 오탐/가설은 아래와 같다.

| ID | 가설 | 최종 판정 | 제거 근거 |
|---|---|---|---|
| R-01 | Stage 3가 `PASS_WITH_FIX`를 외부 성공으로 잘못 취급한다. | `rejected` | `modules/core/stage3_orchestrator.py:760-763`, `tests/test_pass_with_fix.py:943-963` |
| R-02 | Stage 4는 re-audit 뒤에도 초기 score를 유지한다. | `rejected` | `modules/core/stage4_interview_round.py:2587-2604`, `tests/test_stage4_interview_round.py:1387-1393` |
| R-03 | structural inplace patch가 전역 문제에도 무분별하게 실행된다. | `rejected` | `modules/domain/agents/chief_writer.py:1083-1085`, `modules/domain/agents/chief_writer.py:1337-1343` |
| R-04 | sink alignment는 이름만 있고 실제 mismatch 비교가 없다. | `rejected` | `modules/core/failure_analyzer.py:356-524`, `tests/test_failure_analyzer.py:497-527` |
| R-05 | soft-failure MagicMock 오염은 아직 현재 코드의 활성 버그다. | `rejected` | `modules/core/soft_failure.py:33-44`, `tests/test_stage4_post_processor.py:858-890` |
| R-06 | Electron 배포 계약이 문서와 분리되어 있다. | `rejected` | `geuldobi-desktop/package.json:39-52`, `geuldobi-desktop/src/main.js:82-89` |

오탐 제거 결과, 남는 위험은 전부 "증거물/재현성/문서 동기화" 중심으로 수렴했다.

## 확정 findings

### F-01. `docs/stage_map` 상태 원장과 실제 `stage1.md`가 정면 충돌한다

- 심각도: `P1`
- canary blocker: `No`
- 문서 불일치: `Yes`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - `docs/stage_map/README.md`는 known mismatch가 있으면 `Code Sync=No`, 검증 완료 문서는 `Last Verified`를 채우라고 규정한다.
  - 그런데 `doc_status.md`는 `stage1.md`를 `Draft | No | TBD`로 두고 있고, 실제 `stage1.md`는 `2026-03-10 / d2d935b / Code Sync Yes / Verified By Codex`다.
- 직접 근거:
  - `docs/stage_map/README.md:26-29`
  - `docs/stage_map/doc_status.md:15-16`
  - `docs/stage_map/stage1.md:172-176`
- 반대 근거 검토:
  - `stage1.md`를 무효화하거나 임시로 제외한다는 override는 발견되지 않았다.
- 왜 오탐이 아닌가:
  - 같은 `stage_map` 하위 문서들끼리 직접 충돌한다.
- 사용자 영향:
  - `doc_status.md`를 신뢰하는 감사/운영자가 `stage1.md`를 미검증 초안으로 오판할 수 있다.
- 테스트 미실행 사유:
  - 사용자 금지사항에 따라 문서/코드 읽기만 수행했다.

### F-02. 현재 dirty cluster의 핵심 lineage 경로가 untracked 지원 모듈에 의존한다

- 심각도: `P1`
- canary blocker: `Yes`
- 문서 불일치: `Yes`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - dirty baseline에서 `stage2_finalizer`, `stage3_orchestrator`, `stage4_interview_round`, `pass_rate_monitor`는 `modules/core/logging_keys.py`, `modules/core/artifact_logging.py`에 의존한다.
  - 그런데 이 지원 모듈들과 Stage 4 canary 코드/테스트는 모두 untracked다.
- 직접 근거:
  - import 경로: `modules/core/pass_rate_monitor.py:29`, `modules/core/stage2_finalizer.py:8-10`, `modules/core/stage3_orchestrator.py:14-19`, `modules/core/stage4_interview_round.py:9-11`
  - 지원 모듈 실제 내용: `modules/core/logging_keys.py:1-53`, `modules/core/artifact_logging.py:1-52`
  - `git status --short`:
    - `?? modules/core/logging_keys.py`
    - `?? modules/core/artifact_logging.py`
    - `?? modules/core/stage4_canary_tools.py`
    - `?? scripts/run_stage4_canary.py`
    - `?? tests/test_stage4_canary_tools.py`
    - `?? tests/test_run_stage4_canary.py`
- 반대 근거 검토:
  - 현재 로컬 dirty worktree 안에서는 파일이 존재하므로 "로컬 실행 불가"는 아니다.
- 왜 오탐이 아닌가:
  - 기준선이 `HEAD=b3cfa0e`라고 적힐 때, commit checkout만으로는 현재 lineage/canary 계약을 재현할 수 없다.
- 사용자 영향:
  - commit-pin 기준 감사, 협업자 checkout, CI 재현, canary 문서 추적성이 깨진다.
- 테스트 미실행 사유:
  - 테스트 실행 금지. import 관계와 `git` 상태만으로 판정했다.

### F-03. tracked `episode_production.jsonl` 샘플이 현재 Stage 4 lifecycle sink 계약을 대표하지 못한다

- 심각도: `P2`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - 현재 `failure_analyzer`와 Stage 4 episode production 분석은 `attempt_key`, `initial_verdict`, `final_verdict`, `final_score`, `patch_trace`, `candidate_key`, `content_hash`, `artifact_path`를 읽는 전제를 갖는다.
  - 그러나 tracked 샘플 `projects/test_project/logs/episode_production.jsonl`의 앞부분은 `TF49b_PREFLIGHT` 이벤트만 있고 위 필드가 없다.
- 직접 근거:
  - 샘플 로그: `projects/test_project/logs/episode_production.jsonl:1-20`
  - 소비 계약: `modules/core/failure_analyzer.py:296-313`, `modules/core/failure_analyzer.py:356-524`
  - 테스트 기대치: `tests/test_failure_analyzer.py:298-321`, `tests/test_failure_analyzer.py:424-484`
- 반대 근거 검토:
  - 코드/테스트 자체는 최신 schema를 기준으로 정합적이다.
- 왜 오탐이 아닌가:
  - 문제는 코드가 아니라 tracked 샘플 증거물이 현재 schema를 대표하지 못한다는 점이다.
- 사용자 영향:
  - 이 파일을 근거 샘플로 삼는 감리는 sink alignment를 잘못 해석할 수 있다.
- 테스트 미실행 사유:
  - 로그 정적 열람만 수행했다.

### F-04. provider/metrics는 token telemetry를 갖지만 DB LLM 로그는 그 세부값을 남기지 않는다

- 심각도: `P2`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - provider와 `MetricsCollector`는 cached/thinking token 기반 비용 계산을 수행한다.
  - 하지만 `BaseAgent._log_llm_call_to_db()`는 prompt/response/duration/verdict/thinking snippet만 저장하고 usage token 필드를 넘기지 않는다.
- 직접 근거:
  - provider usage: `modules/core/providers/gemini_provider.py:35-40`, `modules/core/providers/vertex_provider.py:104-109`
  - metric payload 생성/전달: `modules/domain/agents/base_agent.py:370-400`, `modules/domain/agents/base_agent.py:667-677`, `modules/domain/agents/base_agent.py:747-760`
  - DB 저장 경로: `modules/domain/agents/base_agent.py:496-512`
  - 비용 계산: `modules/core/metrics_collector.py:205-301`
- 반대 근거 검토:
  - `MetricsCollector`에는 필요한 정보가 들어가므로 live 비용 추적 자체가 막히지는 않는다.
- 왜 오탐이 아닌가:
  - DB sink에 usage 필드가 전달되지 않는 직접 누락이다.
- 사용자 영향:
  - DB-only 포렌식, 후행 집계, 비용 재산정 시 cached/thinking token granularity가 사라진다.
- 테스트 미실행 사유:
  - 실행 대신 코드 경로만 교차 검토했다.

### F-05. MagicMock soft-failure 경로를 막는 코드는 맞지만, worktree에는 오염 잔존물이 남아 있다

- 심각도: `P2`
- canary blocker: `No`
- 문서 불일치: `No`
- 런타임 검증 필요: `No`
- 깨진 계약:
  - 현재 soft-failure 경로는 `MagicMock` root를 유효한 프로젝트 경로로 취급하지 않아야 한다.
  - 그러나 worktree에는 `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl`이 실제로 존재하고, `stage4_post_processor.save_world_state_atomic` 이벤트를 담고 있다.
- 직접 근거:
  - 보호 로직: `modules/core/soft_failure.py:28-63`, `modules/core/soft_failure.py:165-170`
  - 호출부: `modules/core/stage4_post_processor.py:26-56`, `modules/core/stage4_post_processor.py:1204-1210`
  - 테스트: `tests/test_validation_orchestrator_soft_failure.py:28-36`, `tests/test_stage4_post_processor.py:858-890`
  - 잔존 파일: `MagicMock/mock.current_project.paths.root/1384832399024/logs/soft_failures.jsonl`, `MagicMock/mock.current_project.paths.root/2930521814512/logs/soft_failures.jsonl`
- 반대 근거 검토:
  - 현재 코드 기준으로 같은 오염이 재발한다고 단정할 근거는 없다.
- 왜 오탐이 아닌가:
  - finding의 대상은 "현재 코드 버그"가 아니라 "현재 worktree 증거 오염"이다.
- 사용자 영향:
  - 수동 로그 스캔이나 느슨한 수집기가 pseudo-project 로그를 실제 장애로 오해할 수 있다.
- 테스트 미실행 사유:
  - 사용자 제약상 기존 잔존 파일만 읽었다.

## 제외된 오탐

아래 항목은 끝까지 확인했지만 finding으로 유지하지 않았다.

| 항목 | 제외 사유 |
|---|---|
| Stage 3 외부 성공 집합이 PASS_WITH_FIX를 포함한다 | 실제 코드는 `PASS`, `PASS_WITH_WARNING`만 성공으로 처리한다. |
| Stage 4 re-audit 뒤에도 초기 score/state_updates가 남는다 | 실제 코드는 final score로 `director_score`와 `_director_quality_labels`를 갱신한다. |
| structural patch가 global issue에도 발동한다 | `focus == "global"`이면 structural path를 타지 않고 fallback 이유를 기록한다. |
| sink alignment는 이름만 있고 실제 mismatch 비교가 없다 | `failure_analyzer`는 verdict/score/key/hash/path/file existence를 모두 비교한다. |
| Electron 패키징 계약이 코드와 분리되어 있다 | `package.json`과 `src/main.js`가 `backend.exe`/`engine.exe`/`8300` 기준으로 맞물린다. |

## 확신도 ledger

| 항목 | 점수 |
|---|---:|
| 8개 버킷 인벤토리 완료 | +70 |
| 38개 tracked dirty cluster 추적 완료 | +10 |
| 핵심 계약 2중 근거 확보 | +10 |
| 문서/코드 모순 범위 규명 | +5 |
| Pass 3 오탐 제거 완료 | +5 |
| 테스트 실행/라이브 rerun 금지로 인한 런타임 미폐쇄 | -2 |
| 대형 fixture 숲은 인벤토리 중심, 내용 검증은 비일반화 정책 적용 | -1 |
| tracked 샘플 로그 drift로 인한 lifecycle 산출물 대표성 부족 | -1 |
| worktree-only dependency로 인한 commit-pin 재현성 부족 | -1 |
| `MagicMock` 잔존 아티팩트로 인한 증거 오염 위험 | 0 |
| 합계 | **95** |

판정 메모:

- 95%는 현재 제약 하에서 방어 가능한 상한이다.
- 95%를 넘기지 않은 이유는 live rerun과 test execution이 금지되어 있기 때문이다.
- 추가 상승 여지는 fresh canary 재생성과 tracked/untracked 정리 이후에만 가능하다.

## 잔여 불확실성

아래 항목은 읽기 전용 조사만으로는 더 못 올린다.

| 항목 | 상태 | 상한 이유 |
|---|---|---|
| Stage 4 sink가 실제 프로젝트 실행에서 항상 최신 schema를 쓰는지 | `runtime-only` | canary/full/live rerun 금지 |
| untracked canary/logging helper가 향후 commit에 편입될지 | `runtime-only` | `git` 미래 상태는 정적 조사로 폐쇄 불가 |
| `MagicMock` 잔존물이 pre-fix 생성인지 외부 수동 생성인지 | `runtime-only` | 생성 시점 재구성 불가 |

## 부록 A. Evidence Index

| ID | subsystem | claim | evidence_type | file_ref | risk | confidence_delta | status |
|---|---|---|---|---|---|---:|---|
| E-001 | baseline | `HEAD=b3cfa0e`, dirty baseline 고정 | git | `git rev-parse`, `git diff --stat HEAD`, `git status --short` | Meta | +4 | confirmed |
| E-002 | inventory | tracked 4,836개, 상위 분포 고정 | git | `git ls-files` 집계 | Meta | +4 | confirmed |
| E-003 | fixture policy | `lite_mode/test_mode/백업`은 인벤토리 전수 후 비일반화 | git | `git ls-files lite_mode`, `git ls-files test_mode`, `git ls-files 백업` | None | +1 | confirmed |
| E-004 | orchestration | `main_a.py`는 Stage handoff thin delegate/context 주입 구조 | code | `main_a.py:2478-2492`, `2558-2581`, `2792-2801`, `3350-3454` | Observation | +3 | confirmed |
| E-005 | interfaces | Stage 계약과 PASS_WITH_FIX/state_updates invariant 문서화 | doc | `docs/stage_map/interfaces.md:11-33` | Observation | +2 | confirmed |
| E-006 | Stage 3 semantics | 외부 성공 집합은 `PASS`, `PASS_WITH_WARNING`만 | code+test | `modules/core/stage3_orchestrator.py:760-763`, `tests/test_pass_with_fix.py:943-963` | Observation | +3 | confirmed |
| E-007 | Stage 2 semantics | PASS_WITH_FIX patch loop와 PF-3 채택+REJECT 경로 존재 | code | `modules/core/stage2_finalizer.py:659-724`, `792-811` | Observation | +3 | confirmed |
| E-008 | Stage 4 semantics | final score와 patch trace가 최종 verdict 기준으로 갱신 | code+test | `modules/core/stage4_interview_round.py:2578-2664`, `3976-3982`, `tests/test_stage4_interview_round.py:1387-1393`, `1597-1605` | Observation | +3 | confirmed |
| E-009 | structural patch | global issue는 structural patch 비적용, local target만 허용 | code | `modules/domain/agents/chief_writer.py:1083-1085`, `1195-1303`, `1337-1343` | Observation | +2 | confirmed |
| E-010 | sink schema | attempt linkage 필드가 monitor에 존재 | code | `modules/core/pass_rate_monitor.py:32-56`, `167-192` | Observation | +2 | confirmed |
| E-011 | sink audit | failure analyzer가 final/lifecycle sink mismatch 전부 비교 | code+test | `modules/core/failure_analyzer.py:286-313`, `356-524`, `tests/test_failure_analyzer.py:337-527` | Observation | +3 | confirmed |
| E-012 | tracked sample drift | tracked `episode_production.jsonl`은 최신 lifecycle schema 대표가 아님 | log+code | `projects/test_project/logs/episode_production.jsonl:1-20`, `modules/core/failure_analyzer.py:296-313` | P2 | -1 | confirmed |
| E-013 | telemetry | provider가 cached/thinking token usage를 노출 | code | `modules/core/providers/gemini_provider.py:35-40`, `modules/core/providers/vertex_provider.py:104-109` | Observation | +2 | confirmed |
| E-014 | telemetry gap | DB LLM 로그는 usage token 필드를 저장하지 않음 | code | `modules/domain/agents/base_agent.py:496-512`, `370-400`, `667-760`, `modules/core/metrics_collector.py:205-301` | P2 | -1 | confirmed |
| E-015 | soft-failure guard | MagicMock root는 유효 path로 간주되지 않음 | code+test | `modules/core/soft_failure.py:28-63`, `tests/test_validation_orchestrator_soft_failure.py:28-36`, `tests/test_stage4_post_processor.py:858-890` | Observation | +2 | confirmed |
| E-016 | soft-failure residue | worktree에 MagicMock soft_failure 로그가 실제 남아 있음 | artifact | `MagicMock/mock.current_project.paths.root/*/logs/soft_failures.jsonl` | P2 | -1 | confirmed |
| E-017 | canary logic | hard gate는 sink mismatch, missing artifact, legacy key를 fail 처리 | code+test | `modules/core/stage4_canary_tools.py:257-322`, `tests/test_stage4_canary_tools.py:137-144` | Observation | +2 | confirmed |
| E-018 | canary reproducibility | canary 및 logging helper는 모두 untracked | git | `git status --short` | P1 | -1 | confirmed |
| E-019 | doc rule | stage_map mismatch는 `Code Sync=No`로 표기해야 함 | doc | `docs/stage_map/README.md:26-29` | Observation | +1 | confirmed |
| E-020 | doc contradiction | `doc_status.md`와 `stage1.md`가 직접 충돌 | doc | `docs/stage_map/doc_status.md:15-16`, `docs/stage_map/stage1.md:172-176` | P1 | -1 | confirmed |
| E-021 | desktop packaging | Electron이 `dist/backend`, `dist/engine`, `backend.exe`, `8300` 계약을 사용 | code | `geuldobi-desktop/package.json:39-52`, `geuldobi-desktop/src/main.js:20`, `82-89`, `312-313` | Observation | +2 | confirmed |
| E-022 | runtime-only closure | live 실행 금지로 런타임 폐쇄 검증은 보류 | policy | 사용자 지시사항 | Meta | -2 | runtime-only |

## 부록 B. 버킷 커버리지 표

| 버킷 | 대표 검토 대상 | 커버리지 | 결론 |
|---|---|---|---|
| 오케스트레이션/진입점 | `main_a.py` | 완료 | 위임/DI 구조 확인 |
| Stage 0-4 계약 | `docs/stage_map/interfaces.md`, `docs/stage_map/stage*.md` | 완료 | core 계약 일치, `stage1` 문서 원장 불일치만 finding |
| PASS_WITH_FIX·validation 의미론 | `stage2_finalizer.py`, `stage3_orchestrator.py`, `stage4_interview_round.py`, `chief_writer.py`, 관련 테스트 | 완료 | 의미론 정합 |
| DB·로그·sink 정합성 | `pass_rate_monitor.py`, `failure_analyzer.py`, `db_manager.py`, tracked sample logs | 완료 | 구현 정합, 샘플 로그 drift finding |
| provider·비용 telemetry | provider 2종, `base_agent.py`, `metrics_collector.py` | 완료 | telemetry 흐름 정합, DB sink detail gap finding |
| scripts·canary 운영 경로 | `stage4_canary_tools.py`, `run_stage4_canary.py`, 관련 테스트, `git status` | 완료 | 로컬 구현 일관, tracked baseline 재현성 finding |
| 문서 동기화 상태 | `docs/stage_map/README.md`, `doc_status.md`, `stage1.md`, 2026-03-12 문서군 | 완료 | `stage1` 원장 불일치 finding |
| Electron/UI 표면 | `geuldobi-desktop/package.json`, `src/main.js` | 완료 | packaging/bridge 계약 확인 |

미조사 영역은 없다. 다만 런타임 재실행 없이 닫을 수 없는 항목은 `runtime-only`로 남겼다.
