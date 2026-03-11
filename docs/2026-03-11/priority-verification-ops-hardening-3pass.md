# 현재 우선순위 검증 및 운영 고도화 3-Pass 감리

> 작성일: 2026-03-11
> 상태: 검증 완료
> 감리: 3-pass 완료
> 확신도: 97%
> 목적: "지금은 새 기능 필수보다 운영 고도화 단계인가?"와 "제시한 우선순위 순서가 현재 코드베이스 상태에 맞는가?"를 문서/코드/실데이터 기준으로 판정

> 보완 메모 (2026-03-11):
> 이 문서의 `projects/00000` 예시는 calibration 우선순위를 판정할 때 사용한 historical snapshot으로만 본다.
> 현재 `technical validation baseline`은 `projects/00_test_00`이며, 상세 근거와 오탐 제거 결과는 [00-test-00-stage234-ssot-3pass.md](./00-test-00-stage234-ssot-3pass.md)로 이관했다.
> 본문에 남아 있는 `_build_quality_dashboard_payload("00000", 5)` 언급도 historical check 기록이며, 현재 read-on-write 이슈 때문에 재실행 기준으로 보지 않는다.

---

## 0. 최종 판정

큰 방향은 맞다.

- 현재 글도비의 주된 병목은 `핵심 새 기능 부재`보다 `운영 정합성 + 실데이터 캘리브레이션 + UX 제품화` 쪽이다.
- 최근 문서, 코드, UI, 테스트 축도 모두 같은 방향으로 움직이고 있다.

다만 현재 상태를 더 정확히 반영하면 순서는 아래가 맞다.

1. `retrieval / quality / role-fit` 실데이터 캘리브레이션
2. `Safe Ops backup/undo` 검토
3. `writer journey` 잔여 UX
4. `BI -> TR` 연결 정리
5. `다음 행동 추천` 고도화

즉 `운영 고도화 단계`라는 판단은 맞지만, `1번과 2번`은 바꿔 두는 편이 더 실무적이다.

이유:

- Safe Ops는 `DB 정합성`과 `UI preview`가 이미 상당 부분 닫혔다.
- 반면 retrieval/quality/role-fit은 문서상으로도 `calibration pending`, `role-fit pending`이고, 실제 프로젝트 데이터도 아직 충분히 쌓여 있지 않다.

---

## 1. Pass 1: 문서/로드맵 기준 판정

### 1.1 Safe Ops

현 상태는 `기본 정합성 완료 + undo/backup 미완`이다.

- `TF-safe-ops-db-consistency-3pass-audit.md`는 Safe Ops 경로를 `PASS`로 판정한다.
- `TF-safe-ops-ux-productization-plan.md`는 백엔드 정합성은 복구됐고 남은 핵심 갭은 `UX`라고 명시한다.
- 같은 문서의 Out of Scope에 `undo stack`, `snapshot backup/restore`가 남아 있다.

판정:

- `Safe Ops 자체`는 새 기능보다 운영 고도화 항목이 맞다.
- 다만 지금 남은 것은 `정합성 복구`보다 `undo/backup 설계 검토`다.

### 1.2 Retrieval / Quality / Role-Fit

이 축은 문서상으로도 아직 `실데이터 캘리브레이션 단계`다.

- `TF-db-retrieval-consumption-intelligence-plan.md`는 현재 병목을 `저장 부족`이 아니라 `retrieval/consumption`으로 규정한다.
- 같은 문서는 `새 장르 추가보다 우선순위 높음`이라고 명시한다.
- `TF-work-guard-identity-ssot-plan.md`는 문서 헤더부터 `calibration pending` 상태다.
- 같은 문서는 `role-fit pending`을 별도로 남긴다.

판정:

- 현재 최상위 운영 고도화 항목으로 보는 것이 타당하다.
- 특히 문서상 "구현 1~2차 완료" 이후 단계가 바로 calibration이라, 지금은 신규 기능보다 보정이 더 중요하다.

### 1.3 Writer Journey

이 축도 문서상으로 분명한 `운영/제품화 잔여 UX`다.

- `TF-writer-journey-friction-audit.md`는 글도비를 `엔진은 강한데, 작가 체감은 아직 운영툴 쪽에 더 가깝다`고 정리한다.
- 같은 문서는 주요 불편으로
  - 입력 구조화 부족
  - 기억/판단 근거 비가시성
  - `BI -> TR -> Arc -> Blueprint -> Manuscript` 사슬 비가시성
  - 다음 행동 추천의 약함
  를 적는다.

판정:

- 새 기능보다 `작가가 덜 머리 아프게 쓰는 제품`으로 가는 UX 정리가 맞다.

### 1.4 BI -> TR 연결

이 축은 이미 별도 수습 문서가 있고, 신규 발명보다 `정본/후보 정리` 문제다.

- `TR-BI-hybrid-salvage-plan.md`는 `03/04/08`을 현재 실행 정본으로, `09/10/11`을 `promotion candidate bible`로 분리한다.
- 같은 문서는 `TR -> BI` 순서를 유지하되 입력 SSOT를 바꾸라고 권고한다.

판정:

- 이 문제도 새 기능이라기보다 `실행 정본 유지 + 승격 후보 관리 + 재생성 순서 통제`의 운영 항목이다.

### 1.5 다음 행동 추천

이 축은 이미 1차 제품화됐지만 아직 얕다.

- `TF-writer-journey-friction-audit.md`는 `결과는 보이지만, 다음 행동 추천은 아직 약하다`고 적는다.
- `TF-UX-dashboard-feedback-productization-plan.md` 역시 행동 피드백이 약하고 CTA가 후속 단계라고 본다.

판정:

- 이것도 맞는 우선순위다.
- 다만 retrieval/quality 데이터가 비어 있으면 추천 고도화도 같이 막히므로, 선행은 calibration 쪽이다.

---

## 2. Pass 2: 코드/배선 기준 판정

### 2.1 이미 닫힌 것

운영 고도화 표면은 실제 코드에 들어와 있다.

- `modules/api/bridge_server.py`
  - `safe_ops`
  - `artifact_ladder`
  - `retrieval_summary`
  - `result_summary`
  payload를 한 번에 조립한다.
- `geuldobi-desktop/src/index.html`
  - `Safe Ops Preview`
  - `Artifact Ladder`
  - `Retrieval Inspector`
  - `Run Result Summary`
  패널이 실제 UI에 존재한다.
- `modules/core/quality_dashboard.py`
  - retrieval observation 집계와 summary API가 존재한다.
- `modules/core/genre_guards/work_guard.py`
  - `tracking_slots`
  - `registry_profiles`
  - `role_fit_constraints`
  를 로드하고 warning-only 검증까지 수행한다.
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `modules/core/stage4_interview_round.py`
  는 retrieval observation을 stage별로 기록한다.

즉 지금 코드베이스는 "새 큰 기능이 하나도 없다"가 아니라, 이미 만든 운영 표면을 더 믿을 수 있게 만드는 단계다.

### 2.2 아직 얕은 것

반대로 남은 갭도 코드에서 명확하다.

- `modules/api/bridge_server.py`의 `next_action`은 verdict/issue/signal 조합 기반의 얕은 휴리스틱이다.
- Safe Ops에는 preview와 stage-aware 설명이 있지만, 실제 `undo stack`이나 `snapshot restore` 경로는 없다.
- `Artifact Ladder`는 현재 산출물 상태를 잘 보여주지만, `03/04/08 vs 09/10/11` 같은 정체성 승격 로직을 자동으로 해결하진 않는다.
- role-fit은 warning payload와 예외 구조는 생겼지만, 실데이터 보정 전제의 1차 구현에 머문다.

판정:

- 사용자가 적은 5개 항목은 전부 `운영 고도화의 남은 잔업`으로 읽히며,
- 그중 가장 "코드가 이미 들어왔는데 아직 보정이 덜 된 것"은 retrieval/quality/role-fit이다.

---

## 3. Pass 3: 테스트/실데이터 기준 판정

### 3.1 회귀 테스트

우선순위 5개와 직접 연결된 회귀 묶음을 실행했다.

실행:

```bash
python -m pytest tests/test_bridge_quality_summary.py tests/test_safe_ops_db_consistency.py tests/test_work_guard.py tests/test_quality_regression.py tests/test_stage2_preflight.py tests/test_stage3_orchestrator.py tests/test_stage4_context_builder.py tests/test_stage4_interview_round.py -q
```

결과:

- `211 passed in 5.62s`

판정:

- Safe Ops preview/정합성
- retrieval summary
- work guard / role-fit
- Stage 2/3/4 retrieval wiring
  는 회귀 기준선이 있다.

### 3.2 실제 프로젝트 데이터 스냅샷

로컬 `projects/**/project_data.db`를 전수 확인한 결과:

- 총 `18`개 DB 중
  - `episode_quality_labels` 존재: `3`
  - `episode_quality_signals` 존재: `3`
  - `episode_quality_observations` 존재: `3`
  - `director_selections.stage` 컬럼 존재: `2`

즉 코드와 문서는 최신 상태여도, 실제 프로젝트 데이터는 아직 신구 스키마가 혼재한다.

### 3.3 대표 실데이터 예시: `projects/00000`

`projects/00000/project_data.db` 기준:

- `episode_quality_labels = 0`
- `episode_quality_signals = 0`
- `episode_quality_observations = 0`
- `director_selections = 24`

동시에 로그는 존재한다.

- `projects/00000/logs/quality_metrics.jsonl` 행 수: `44`
- `projects/00000/logs/episode_production.jsonl` 행 수: `20`

또한 `_build_quality_dashboard_payload("00000", 5)` 결과:

- `safe_ops.available = True`
- `quality_summary.available = False`
- `retrieval_summary.available = False`
- `result_summary.available = False`

해석:

- 운영 패널은 켜졌지만,
- 품질/관측/다음 행동 추천에 필요한 최신 구조화 데이터는 아직 충분히 채워지지 않았다.

이건 `retrieval / quality / role-fit 실데이터 캘리브레이션`을 최상위로 올려야 하는 직접 근거다.

---

## 4. 권장 우선순위

### 4.1 지금 기준 권장 순서

1. `retrieval / quality / role-fit` 실데이터 캘리브레이션
   - 이유: 코드와 UI는 이미 깔렸는데, 실제 데이터 누적/마이그레이션/보정이 비어 있다.
2. `Safe Ops backup/undo` 검토
   - 이유: Safe Ops 정합성/preview는 닫혔지만, 진짜 되돌리기 계층은 아직 out-of-scope다.
3. `writer journey` 잔여 UX
   - 이유: 엔진 대비 작가 체감이 뒤처지는 핵심 병목이다.
4. `BI -> TR` 연결 정리
   - 이유: 현재 정본과 승격 후보가 분리돼 있어 운영 기준선 고정이 필요하다.
5. `다음 행동 추천` 고도화
   - 이유: 지금 로직은 얕은 휴리스틱이라, 앞단 데이터 품질이 정리된 뒤 고도화하는 것이 맞다.

### 4.2 사용자 제안 순서와의 차이

사용자 제안:

1. Safe Ops backup/undo 검토
2. retrieval / quality / role-fit 실데이터 캘리브레이션
3. writer journey 잔여 UX
4. BI→TR 연결
5. 다음 행동 추천 고도화

판정:

- `운영 고도화 단계`라는 큰 방향은 맞다.
- 다만 `1`과 `2`는 교체하는 편이 더 정확하다.

---

## 5. 결론

지금 글도비는 분명히 `새 기능 필수 단계`보다 `운영 고도화 단계`에 있다.

근거는 세 가지다.

1. 최근 문서 대부분이 `audit / plan / productization / calibration`이다.
2. 코드에는 Safe Ops, Artifact Ladder, Retrieval Inspector, Result Summary 같은 운영 표면이 이미 구현돼 있다.
3. 실제 프로젝트 데이터는 아직 새 관측 스키마와 충분히 정렬되지 않아, 지금 가장 큰 병목이 `실데이터 보정`으로 드러난다.

따라서 다음 행동은 `새 기능 추가`보다 아래 순서가 맞다.

1. 실데이터 캘리브레이션
2. Safe Ops undo/backup 검토
3. writer journey UX
4. BI->TR 운영 정본 정리
5. next-action 추천 고도화

추가 메모:

- 만약 목표가 `멀티장르 외부 릴리스`로 바뀌면 `멀티장르 실파이프라인 검증`과 `Treatment 편집 UX`가 다시 상위로 올라온다.
- 그러나 현재 메인라인 기준으로는 사용자가 적은 문장, 즉 `지금은 새 기능 필수보다 운영 고도화 단계다`가 맞다.
