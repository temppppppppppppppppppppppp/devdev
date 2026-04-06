# ROL Global Terminal 5 — Observability / Bridge / App Shell P0-P1 Survey

Date: 2026-04-06
Terminal: 5
Scope: persistence, observability, operator surface, bridge/app shell, validation summary
Mode: read-only severity sweep
Baseline Commit: `0d7c077a9e6f14575aba7fc509b836d218db610d`

## Verdict

**No live P0-P1 found in this lane.**

## 1. Operator가 현재 state를 거짓으로 읽게 만드는 summary/sink mismatch가 live P0-P1인가

**아니다.**

모든 operator-facing surface에 explicit authority classification이 적용되어 있다.

| Surface | Authority Role | Source |
| --- | --- | --- |
| `/status` | `companion_snapshot` | `control_plane_contract.py:59` |
| `/quality/dashboard` | `companion_snapshot` | `control_plane_contract.py:60` |
| `/quality/summary` | `companion_snapshot` | `control_plane_contract.py:61` |
| `control_plane_provenance` | `authoritative_sink` | `control_plane_contract.py:52` |
| `project_data.db` | `authoritative_sink` | `control_plane_contract.py:53` |
| `episode_production.jsonl` | `authoritative_sink` | `control_plane_contract.py:54` |

`AuditService.write_audit_summary()` 가 생성하는 `runtime_audit_summary.json`은 내부 contract에 `attempt_truth_authoritative: false`를 명시하고, authoritative 싱크 목록을 별도로 나열한다 (`audit_service.py:277-286`).

`SessionLogger` docstring은 session JSONL을 "OPTIONAL best-effort telemetry", "NOT authoritative truth for verdict adjudication"으로 선언한다 (`session_logger.py:12-17`). JSONL loss 시 durable pipeline truth는 보존된다.

bridge_server의 모든 dashboard response는 `authority_role` 필드를 payload에 포함시켜 companion/authoritative를 구분한다. `budget_status`는 `operator_guidance_only: True`를 명시한다.

**결론: sink mismatch가 operator를 오도할 live P0-P1 경로가 없다.**

## 2. Bridge/dashboard/app shell이 stale authority를 더 권위 있어 보이게 만드는가

**아니다.**

- **bridge_server**: `/quality/dashboard` 및 `/quality/summary`는 매 호출마다 DB를 fresh read하여 payload를 구성한다. 캐시 계층이 없다. Response에 `authority_role: companion_snapshot`이 포함된다.
- **desktop app shell** (`main.js`): Electron 렌더러는 bridge_server HTTP/WS를 통해 데이터를 받는다. 자체 truth를 persist하지 않는다. `contextIsolation: true`, `nodeIntegration: false`로 격리된다. Authority chain은 `desktop_renderer -> IPC -> bridge_server -> ProcessRunner -> main_a.py`로 명확하다.
- **control_plane_contract.py**: Authority path와 sink 분류가 코드 수준에서 고정되어 있으며, `build_control_plane_authority_summary()`가 모든 status response에 포함된다.

Stale authority를 mask하는 live 경로가 없다.

## 3. Canary/summary 계열이 false clean을 낼 수 있는가

**현재 코드에서 P0-P1급 false clean 경로는 없다.**

- **stage4_canary_tools.py**: Canary 준비 함수들은 project *복사본*에서만 DB 수정(DELETE, VACUUM)을 실행한다. Source project는 변경되지 않는다. 테스트(`test_stage4_canary_tools.py:66-100`)가 source 보존을 검증한다.
- **Gate 평가**: `_evaluate_stage3_canary_gates`와 `_evaluate_stage4_canary_gates`는 sink alignment 문제를 `warnings`로, blueprint/attempt 부족을 `errors`로 분리한다. `errors`가 있으면 status는 `fail`이다. Sink alignment warn은 status를 `warn`으로 내리며 `pass`로 보고하지 않는다.
- **AuditService proof digest**: `_build_proof_digest`가 stage별 sink alignment을 조회할 때, any non-ok status는 전체 digest status를 `warn`으로 내린다 (`audit_service.py:266-273`).
- **QualityDashboard**: `record_validation`에서 `PASS_WITH_WARNING`은 `pass` 카운트에 포함되지만, `PASS_WITH_FIX`는 별도 분류된다 (`quality_dashboard.py:79-80`). 이 분류는 Stage4 test에서도 검증된다 (`test_failure_analyzer.py:84-101`: `pass_with_fix_transient`).

**Watchlist only**: `QualityDashboard._process_record`는 `PASS_WITH_WARNING`을 `pass`에 카운트한다 (`quality_dashboard.py:79`). 이것은 설계 의도이며 P0-P1이 아니지만, operator가 `pass_rate`를 볼 때 `PASS_WITH_WARNING` 포함 여부를 인지해야 한다. `get_summary()`에서 이 구분이 노출되지 않는 점은 long-term observability debt이다.

## 4. Pipeline bug와 observability bug를 분리하면 가장 좁은 owner file 1~3개는 무엇인가

이 lane에서 조사한 모든 파일은 observability/presentation layer이다. Pipeline authority는 이 lane에 속하지 않는다.

Observability owner set:

| Owner | 역할 | 위험도 |
| --- | --- | --- |
| `modules/core/services/audit_service.py` | Runtime heartbeat + proof digest 생산 | 가장 넓은 observability owner; sink alignment summary를 통해 pipeline truth를 읽어 operator에게 보여주는 bridge |
| `modules/api/bridge_server.py` | 모든 operator-facing HTTP/WS endpoint | Presentation layer; authority role tagging의 single source |
| `modules/core/quality_dashboard.py` | Quality metrics 집계 + persistence | In-memory + JSONL 기반; pipeline verdict에 직접 영향 없음 |

`audit_service.py`가 가장 좁은 single owner이다 — proof digest 구성 로직이 operator가 보는 sink alignment status의 유일한 생산자이기 때문이다.

## Watchlist Only (P2 이하)

1. **`QualityDashboard.get_summary()`의 `PASS_WITH_WARNING` 미분리**: `pass_rate`에 `PASS_WITH_WARNING`이 포함되나 operator에게 이 구분이 surface되지 않는다. Long-term observability clarity debt.
2. **`SessionLogger` soft failure 카운트 race**: `_soft_failure_count`는 atomic 타입이 아니지만 `_write_lock` 바깥에서 increment된다 (`session_logger.py:369`). 실질적 영향은 best-effort telemetry 카운터 정확도뿐이므로 P2 이하.
3. **Desktop settings recovery chain complexity**: `loadDesktopSettingsFromDisk` (`main.js:335-384`)는 primary -> backup -> factory_reset 3단 recovery chain을 가진다. 복잡하지만 pipeline truth에 영향 없음.

## Fresh Run Required?

**아니다.** 이 lane의 결론은 static evidence만으로 충분하다. Authority contract와 sink classification은 코드 수준에서 고정되어 있으며, runtime behavior에 따라 달라지지 않는다. Canary gate 로직도 코드 분석과 테스트로 확인 가능하다.

## 3-Pass Audit Record

- Pass 1: 문서 유형을 `terminal survey output`으로 고정. Scope는 Terminal 5 assigned files로 한정. 4개 질문 모두 응답.
- Pass 2: 모든 file path reference가 실제 워크스페이스에 존재하는지 확인. Line number 참조가 코드와 일치하는지 확인. Authority contract 내용이 코드와 일치.
- Pass 3: Watchlist 항목이 P0-P1 판정 기준에 해당하지 않음을 재확인. Speculative issue가 watchlist로 분리됨.
- Confidence: 0.96

read-only terminal survey complete; no files mutated outside assigned docs/2026-04-06 output
