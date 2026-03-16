# TF-D: Stage 4 Broken Feedback

> 조사일: 2026-03-16
> 범위: ai_slop / npc_drift / open_review / compression_ratio / burstiness / complexity / ced_score / coverage_warning
> 방법: Grep 전체 .py 검색 + 코드 직접 읽기 (producer→storage→consumer 양방향 추적)

---

## Signal Inventory

| # | Signal | Producer (file:line) | Storage | Expected Consumer | Actual Consumer | Status | Impact |
|---|--------|---------------------|---------|-------------------|-----------------|--------|--------|
| D-1 | `ai_slop` | quality_signal_metrics.py:129 | episode_quality_signals DB | S4 retry CW 주입 | bridge_server (대시보드만) | **DEAD** | H |
| D-2 | `npc_drift` | npc_drift_advisor.py:20-150 | 인메모리 (transient) | S4 retry CW 주입 | Director mandatory_context (advisory) | **ADVISORY-ONLY** | M |
| D-3 | `open_review` | director_ensemble.py | episode_quality_labels DB | S4 retry CW 주입 | bridge_server + failure_analyzer (사후) | **DEAD** | M |
| D-4 | `compression_ratio` | quality_signal_metrics.py:103 | episode_quality_signals DB | S4 retry CW 주입 | bridge_server (대시보드만) | **DEAD** | L |
| D-5 | `burstiness` | quality_signal_metrics.py:110 | episode_quality_signals DB | S4 retry CW 주입 | bridge_server (대시보드만) | **DEAD** | L |
| D-6 | `complexity` | quality_signal_metrics.py:118 | episode_quality_signals DB | S4 retry CW 주입 | bridge_server (대시보드만) | **DEAD** | L |
| D-7 | `ced_score` | quality_signal_metrics.py:153 | episode_quality_signals DB | S4 retry CW 주입 | bridge_server (대시보드만) | **DEAD** | M |
| D-8 | `coverage_warning` | stage3_orchestrator.py:1233 | Blueprint metadata (transient) | S4 retry 명시적 표면화 | Blueprint 구조에 암묵 포함 | **WEAK** | M |

---

## Detailed Findings

### [TF-D-1] ai_slop — DEAD (가장 심각)

- **Producer**: `compute_ai_slop()` → `quality_signal_metrics.py:129-150`
  - 11개 AI 슬랍 패턴 탐지 (그야말로, 말 그대로, 순식간에, 숨을 삼켰다 등)
  - density_per_10k 계산, 패턴별 hit count 집계
- **Storage**: `db_manager.py:2918` → `episode_quality_signals` 테이블
  - `ai_slop_score` (REAL), `ai_slop_hits` (TEXT/JSON)
  - `stage4_post_processor.py:356-367`에서 최종 원고 기준 저장
- **Expected Consumer**: Chief Writer retry CW에 주입 → "이 패턴 줄여라" 지시
- **Actual Consumer**: `bridge_server.py:1026,1092` (UI 대시보드 전용)
- **Status**: DEAD — 측정→DB 저장→대시보드 표시. **retry 루프에 주입 경로 없음**
- **Evidence Gap**:
  - `stage4_interview_round.py:1600-1920`에서 mandatory_context 구성 시 quality_signals DB 조회 없음
  - `stage4_context_builder.py`에 ai_slop 참조 없음
  - Chief Writer는 ai_slop 데이터를 절대 볼 수 없음
- **Impact**: H — AI 슬랍 패턴이 반복 생성되어도 Writer가 모르므로 같은 실수 반복
- **Remediation**: WIRE — retry 시 이전 라운드 ai_slop_hits를 mandatory_context에 주입

### [TF-D-2] npc_drift — ADVISORY-ONLY

- **Producer**: `NpcDriftAdvisor` → `npc_drift_advisor.py:20-150`
  - LLM 기반 NPC 이탈 감지
  - `stage4_interview_round.py:4282-4327`에서 호출
- **Storage**: 인메모리 `validation_results[_ci]["npc_drift_warnings"]` (L4305). DB 미저장
- **Expected Consumer**: Chief Writer retry CW에 구체적 NPC 이탈 정보 주입
- **Actual Consumer**:
  1. `_advisory_parts`에 병합 (L4301-4324)
  2. `_director_mc_parts`에 병합 (L1765)
  3. Director의 `mandatory_context`에 전달 (L1921)
  4. Director가 판단 → REJECT 시 retry 트리거
- **Status**: ADVISORY-ONLY — Director에게 전달되어 간접적으로 영향. **Chief Writer에게는 "왜 NPC가 이탈했는지" 구체적 피드백 없음**
- **Evidence Gap**: Director가 REJECT 사유를 생성하지만, npc_drift 구체 데이터(어떤 NPC, 어떤 이탈)가 retry feedback에 명시적으로 포함되지 않음
- **Impact**: M — 간접 경로(Director reject)로 부분 작동. 직접 피드백 부재
- **Remediation**: WIRE — npc_drift_warnings를 Director feedback에 구조화하여 Chief Writer에 전달

### [TF-D-3] open_review — DEAD

- **Producer**: Director 평가 시 생성 (selection_reason, verdict_reason)
- **Storage**: `db_manager.py:2882-2889` → `episode_quality_labels` 테이블 `open_review` 컬럼
- **Expected Consumer**: 다음 에피소드 생성 시 이전 open_review 참조
- **Actual Consumer**: `bridge_server.py:858-936` (UI API), `failure_analyzer.py:834-897` (사후 분석)
- **Status**: DEAD — Director의 최종 출력물. 다음 라운드/에피소드 생성에 재주입 없음
- **Evidence**: `get_episode_quality_label()` 호출이 retry/generation 경로에 없음
- **Impact**: M — Director의 정성적 평가가 축적만 되고 학습에 활용 안 됨
- **Remediation**: WIRE (optional) — 이전 에피소드 open_review를 다음 에피소드 CW에 요약 주입

### [TF-D-4] compression_ratio — DEAD

- **Producer**: `compute_compression_ratio()` → `quality_signal_metrics.py:103-107`
  - gzip 압축률 계산 (텍스트 반복성/다양성 지표)
- **Storage**: `episode_quality_signals.compression_ratio`
- **Expected Consumer**: 높은 압축률(= 반복적 텍스트) 감지 → retry 시 "반복 줄여라" 지시
- **Actual Consumer**: bridge_server (대시보드만)
- **Status**: DEAD
- **Impact**: L — 트렌드 모니터링용으로 충분할 수 있음
- **Remediation**: KEEP-AUDIT (optional WIRE — 임계값 초과 시 경고)

### [TF-D-5] burstiness — DEAD

- **Producer**: `compute_burstiness()` → `quality_signal_metrics.py:110-115`
  - 문장 길이 표준편차 (리듬 다양성 지표)
- **Storage**: `episode_quality_signals.burstiness`
- **Expected Consumer**: 낮은 burstiness(= 단조로운 리듬) 감지 → retry 지시
- **Actual Consumer**: bridge_server (대시보드만)
- **Status**: DEAD
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-D-6] complexity — DEAD

- **Producer**: `compute_complexity()` → `quality_signal_metrics.py:118-126`
  - 평균 문장 길이 × (1 + 장문 비율)
- **Storage**: `episode_quality_signals.complexity`
- **Expected Consumer**: 복잡도 편차 감지 → 스타일 가이드 대비 경고
- **Actual Consumer**: bridge_server (대시보드만)
- **Status**: DEAD
- **Impact**: L
- **Remediation**: KEEP-AUDIT

### [TF-D-7] ced_score — DEAD

- **Producer**: `compute_ced()` → `quality_signal_metrics.py:153-168`
  - Consistency Error Density = (checklist 이슈 + warnings) / 10K 텍스트 단위
- **Storage**: `episode_quality_signals.ced_score`
- **Expected Consumer**: 높은 CED → retry 시 "일관성 오류 수정" 강조
- **Actual Consumer**: bridge_server (대시보드만)
- **Status**: DEAD
- **Impact**: M — CED가 높으면 모순이 많다는 의미이나 retry에 반영 안 됨
- **Remediation**: WIRE — CED > threshold 시 retry mandatory_context에 경고 주입 권장

### [TF-D-8] coverage_warning — WEAK (암묵적)

- **Producer**: `stage3_orchestrator.py:1233-1243` + `stage4_interview_round.py:2736-2759`
  - missing_work_slot_summary, work_focus_without_slots, missing_relation_slice
- **Storage**: Blueprint metadata (transient dict)
- **Expected Consumer**: retry 시 "이 영역 커버리지 부족" 명시적 표면화
- **Actual Consumer**:
  - `stage4_context_builder.py:2560-2586` → Blueprint observability로 로드
  - Chief Writer가 Blueprint 전체를 받으므로 metadata에 **암묵적으로** 포함
  - **BUT**: 명시적으로 mandatory_context에 표면화되지 않음
- **Status**: WEAK — Blueprint 구조에 매몰. Writer가 주목하지 않을 가능성
- **Impact**: M
- **Remediation**: WIRE — coverage_warnings를 mandatory_context에 별도 섹션으로 표면화

---

## Summary

| Status | Count | Signals |
|--------|-------|---------|
| **DEAD** | 6 | ai_slop, open_review, compression_ratio, burstiness, complexity, ced_score |
| **ADVISORY-ONLY** | 1 | npc_drift |
| **WEAK** | 1 | coverage_warning |

### 핵심 구조적 문제

**"Post-Generation Metrics → Dashboard Only" 패턴**:

```
생성 → 측정 → DB 저장 → 대시보드 표시
                         ↑ 여기서 끊김
                         ↓ 이 경로 없음
retry → mandatory_context ← DB 조회 ← 이전 라운드 metrics
```

quality_signal_metrics.py의 6개 신호(ai_slop, compression_ratio, burstiness, complexity, ced_score + open_review)가 모두 같은 패턴: **측정→저장→표시만. retry CW 주입 경로 전무.**

### Missing Code (핵심 갭)

`stage4_interview_round.py:1600-1920` mandatory_context 구성 시:
```python
# 이 코드가 없음:
# recent_signals = db.get_recent_episode_quality_signals(ep_num, lookback=3)
# if recent_signals:
#     signal_injection = format_signal_feedback(recent_signals)
#     mandatory_context += signal_injection
```

### Remediation 우선순위

| 우선순위 | Signal | 조치 | 근거 |
|---------|--------|------|------|
| **P1** | ai_slop | WIRE — retry CW에 hit 패턴 주입 | AI 슬랍 반복 방지 핵심 |
| **P2** | ced_score | WIRE — CED 임계값 초과 시 경고 주입 | 일관성 오류 축적 방지 |
| **P3** | npc_drift | WIRE — Director feedback에 구체 데이터 포함 | 간접 경로 강화 |
| **P4** | coverage_warning | WIRE — mandatory_context에 명시적 표면화 | 커버리지 갭 가시화 |
| KEEP | compression/burstiness/complexity | KEEP-AUDIT — 트렌드 모니터링 충분 | ROI 낮음 |
| KEEP | open_review | KEEP-AUDIT (optional 다음 에피소드 요약 주입) | 장기적 가치 |
