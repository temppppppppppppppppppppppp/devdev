# stage_map 5pass audit (CLAUDE.md SSOT)

> Date: 2026-03-10
> Scope: `docs/stage_map/*` vs `CLAUDE.md` + current codebase
> Rule: code edits 금지, 코드 실측 우선, 오탐 제거 후 확정 불일치만 기록

---

## 결론

- `P0`: 없음
- `P1`: 3건
- `P2`: 2건

핵심 결론은 다음이다.

1. `CLAUDE.md`와 실제 코드 기준으로 Stage 3 QualityGate는 더 이상 `80`이 아니다. 현재는 `Stage 2/3/4 공통 90`이다.
2. `docs/stage_map`의 주 문서인 `stage1.md`, `stage3.md`는 이미 상당 부분 최신화되어 있다.
3. 남은 문제는 `보조 문서`와 `문서 메타`에 예전 값이 남아 있어 운영자가 잘못된 문서를 SSOT처럼 읽을 위험이 있다는 점이다.

---

## Pass 1. SSOT 추출 (`CLAUDE.md`)

SSOT로 채택한 기준:

- Director 주권주의: `CLAUDE.md`
- PASS_WITH_FIX + `fix_scope` 3-tier 라우팅: `CLAUDE.md`
- QualityGate 규칙: `CLAUDE.md`에서 `PASS일 때만 score < 90이면 REJECT`, `PASS_WITH_FIX는 bypass`
- `PatchModeThresholds.PATCH`는 dead code 제거 완료: `CLAUDE.md`
- Stage 2/3/4는 unified `quality_gate_score=90`: `CLAUDE.md` + 현재 코드 일치

SSOT로 보되 역사 스냅샷으로 처리한 항목:

- `CLAUDE.md`의 `현재 상태 (2026-03-07)` 블록
- `CLAUDE.md`의 당시 테스트 기준선 `3,614 passed`

이 둘은 날짜가 명시된 상태 스냅샷이므로, 현재 실측값과 다르더라도 자동 결함으로 잡지 않았다.

---

## Pass 2. 코드 실측

실측 사실:

- `config/settings/validation.yaml:34`
  - `quality_gate_score: 90`
- `modules/domain/agents/three_phase_blueprint_generator.py:418`
  - Stage 3도 `_threshold("scoring.quality_gate_score", 90)` 사용
- `modules/core/stage3_orchestrator.py:768`
  - Stage 3 호출값 `max_retries=9` → 최대 10회 시도
- `modules/core/constants.py:113-114`
  - `DIRECTOR_MAX_ATTEMPTS = 10`
  - `ANALYST_MAX_ATTEMPTS = 10`
- `modules/core/stage2_preflight.py:461`
  - Stage 2 로그도 `RetryLimits.ANALYST_MAX_ATTEMPTS` 사용
- `modules/core/stage01_helpers.py:591,641`
  - Stage 1도 `RetryLimits.DIRECTOR_MAX_ATTEMPTS` 사용

테스트 실측:

- 실행 명령: `pytest -q`
- 결과: `3700 passed, 16 skipped, 1 warning`

---

## Pass 3. Active stage_map 대조

### P1-1. Active 보조 문서에 Stage 3 구형 게이트(`80`)가 남아 있음

증거:

- `docs/stage_map/agent_graph.md:39`
  - `QualityGate (blueprint_quality_gate_score=80)`
- `docs/stage_map/gotchas.md:32`
  - `Stage 3은 blueprint_quality_gate_score=80`
- `docs/stage_map/metrics_baseline.md:12`
  - `Stage 3 | 80 | 80 | scoring.blueprint_quality_gate_score`

반증 코드:

- `config/settings/validation.yaml:34`
- `modules/domain/agents/three_phase_blueprint_generator.py:418`
- `docs/stage_map/stage3.md:15`

판정:

- `P1`
- 이유: 이 문서들은 현재 `Deprecated` 표시가 없고 `stage_map` 내부에서 운영 문서처럼 보인다. 실무에서 잘못 읽을 가능성이 높다.

### P1-2. `doc_status.md`가 실제 최신 상태를 반영하지 못함

증거:

- `docs/stage_map/doc_status.md:16`
  - `stage1.md | Draft | No | TBD`
- `docs/stage_map/doc_status.md:17-24`
  - `stage2.md`~`metrics_baseline.md`가 전부 `2026-03-02 / 8476bc2 / Opus`

반증 문서:

- `docs/stage_map/stage1.md:130-134`
  - `2026-03-10 / 3a00c12 / Codex`
- `docs/stage_map/stage3.md:134-138`
  - `2026-03-10 / 3a00c12 / Codex`

판정:

- `P1`
- 이유: `doc_status.md`는 폴더의 freshness SSOT 역할인데, 이 파일이 틀리면 다른 문서를 열기 전에 잘못된 판단을 유도한다.

### P1-3. retry 기본값 설명이 Stage 2/4에서 실제 코드보다 낮게 적혀 있음

증거:

- `docs/stage_map/stage2.md:81`
  - `retry.analyst_max_attempts (기본 5)`
- `docs/stage_map/stage4.md:93`
  - `retry.director_max_attempts (기본 5)`

반증 코드:

- `modules/core/constants.py:113-114`
  - 둘 다 `10`
- `modules/core/stage2_preflight.py:461`
  - Stage 2 실제 표시도 `RetryLimits.ANALYST_MAX_ATTEMPTS`

판정:

- `P1`
- 이유: 운영자가 재시도 budget을 잘못 이해하면 failure triage와 비용 판단이 어긋난다.

---

## Pass 4. Historical 문서 오염 점검

### P2-1. 역사 오더 문서가 현재형으로 읽힐 위험

증거:

- `docs/stage_map/ENHANCE_ORDER.md:53-58,113,135`
- `docs/stage_map/FILL_ORDER.md:72,85,167-168`

문제:

- 둘 다 `blueprint_quality_gate_score=80` 체계를 전제로 쓴 과거 오더 문서다.
- 현재 `README.md`에는 이 문서들이 역사 문서라는 경고가 없다.

판정:

- `P2`
- 이유: 이 파일들은 직접 SSOT는 아니지만, stage_map 폴더 안에 있어 신규 감리자가 잘못 집어들 가능성이 있다.

### P2-2. `metrics_baseline.md`의 테스트 기준선이 현재 실측과 다름

증거:

- `docs/stage_map/metrics_baseline.md:10`
  - `3,040 passed + 0 xfailed`

실측:

- `pytest -q`
  - `3700 passed, 16 skipped, 1 warning`

판정:

- `P2`
- 이유: 런타임 동작을 오도하진 않지만, 운영 품질 판단 문서의 숫자가 낡았다.

---

## Pass 5. 오탐 제거

제외한 항목:

- `docs/stage_map/stage3.md`
  - 이미 `quality_gate_score=90`, `max_retries=9`로 수정 완료
- `docs/stage_map/stage1.md`
  - 더 이상 빈 템플릿이 아니고, 실제 코드 경로 기반으로 채워져 있음
- `docs/stage_map/stage4.md`의 PASS_WITH_FIX bypass 설명
  - 현재 코드와 일치함
- `CLAUDE.md`의 `3,614 passed`
  - 날짜가 붙은 과거 상태 스냅샷이므로 현재 불일치로 카운트하지 않음

---

## 우선순위 권고

1. `doc_status.md`를 현재 기준으로 갱신
2. `agent_graph.md`, `gotchas.md`, `metrics_baseline.md`의 Stage 3 gate를 `90`으로 통일
3. `stage2.md`, `stage4.md`의 retry 기본값을 `10`으로 교정
4. `README.md`에 active 문서와 historical 문서 구분 추가
5. `ENHANCE_ORDER.md`, `FILL_ORDER.md`, `SYNC_CHECK.md` 상단에 `historical / non-SSOT` 배너 부착

---

## 감사 메모

- 이번 감리는 `CLAUDE.md -> 코드 -> active stage_map -> historical docs -> 오탐 제거` 순서의 5pass로 수행했다.
- 코드 수정은 하지 않았다.
- 문서 수정도 이번 파일 추가 외에는 하지 않았다.
