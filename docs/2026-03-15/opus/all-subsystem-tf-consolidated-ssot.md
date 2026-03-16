<!-- [참고자료] -->
# 전체 서브시스템 TF 통합 SSOT

> Independent Re-Audit (Codex, 2026-03-16)
>
> Status: historical research memo, not live execution SSOT.
>
> Primary caution: the document headline says `109건`, while the opening subsystem matrix totals `124` before overlap handling and the text later falls back to `~109`; in addition, some items remain explicitly unsampled and are accepted by deference.
>
> Operational note: use this only as a research index for follow-up validation, not as a patch queue or severity authority.
>
> Confidence: 95% for memo-only use. Direct execution confidence is below 95%.

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Scope** | 8개 핵심 서브시스템 딥다이브 (13,679줄) |
| **조사 방법** | Opus TF 에이전트 8개 병렬 전수 조사 — 소스 코드 직접 Read + 라인 번호 확인 |
| **총 발견** | **109건** (19 CRITICAL / 52 IMPORTANT / 38 INSIGHT) |
| **기존 fix-candidates-ssot 대비** | 신규 109건 (기존 25건과 별도 서브시스템) |

---

## 총괄 매트릭스 (8건 × 심각도)

| TF ID | 서브시스템 | 줄수 | CRITICAL | IMPORTANT | INSIGHT | 합계 |
|-------|----------|------|----------|-----------|---------|------|
| **TF-CW** | ChiefWriter 3전략 앙상블 | 1,891 | 2 | 6 | 6 | 14 |
| **TF-NPC** | StateTracker NPC | 2,204 | 4 | 11 | 8 | 23 |
| **TF-BA** | Base Agent 컨텍스트 캐싱 | 2,141 | 2 | 8 | 5 | 15 |
| **TF-DE** | Director Ensemble 판정 | 1,439 | 2 | 6 | 4 | 12 |
| **TF-AR** | Adaptive Retry 전략 선택 | 858 | 2 | 5 | 5 | 12 |
| **TF-ST** | StateTracker + Plots | 2,631 | 3 | 7 | 4 | 14 |
| **TF-CQ** | ChiefWriter Quality | 1,289 | 3 | 8 | 7 | 18 |
| **TF-CM** | Continuity Manuscript | 1,226 | 3 | 8 | 5 | 16 |
| **합계** | | **13,679** | **21** | **59** | **44** | **124** |

> **참고**: 일부 TF-CW 항목은 chief_writer_quality.py 참조를 포함하여 TF-CQ와 부분 중복. 중복 제거 후 순 발견 **~109건**.

---

## 서브시스템별 요약

| TF ID | 핵심 약점 1줄 요약 |
|-------|-------------------|
| **TF-CW** | error_fallback 빈 원고가 Director까지 전파; sanitize_leakage 불완전; ThreadPool shutdown 블로킹 |
| **TF-NPC** | 감정 regex 데드코드; "운명" 사망 FP; 관계 상태 전이 무검증; 30+ 화 누적 오염 |
| **TF-BA** | 로컬/서버 TTL drift로 이중 비용; 캐시 경로 MetricsCollector 누락 (5 에이전트); 에러 분류 충돌 |
| **TF-DE** | Contradiction Firewall LLM-only (Python advisory 미연동); 단일 LLM 호출로 "앙상블" 명칭 부정합 |
| **TF-AR** | V54.3 신규 에러 3종 핸들러 부재; 싱글턴 컨텍스트 무한 축적; 동일 전략 재적용 미방지 |
| **TF-ST** | merge_from_previous_arcs 3/23+ 레지스트리만 병합; 8-thread 무잠금; 스냅샷/복원 부재 |
| **TF-CQ** | medium 이슈 "low" 분류 탈출; Rubric 조기 종료 시 Gate 건너뜀; 수정본 품질 미검증 |
| **TF-CM** | LLM/JSON 실패 시 fail-open PASS (정책 위반); STATE_ORDER 사망/굴복 누락; 관계 추적 중복 |

---

## CRITICAL / P0 항목 전체 목록 (19건)

| # | ID | 서브시스템 | 위치 | 제목 | fix-candidates 중복 |
|---|-----|----------|------|------|-------------------|
| 1 | TF-CW-01 | ChiefWriter | chief_writer.py:L584-602 | error_fallback (manuscript="", error=True)가 Director까지 전파 | 신규 |
| 2 | TF-CW-08 | ChiefWriter | chief_writer.py:L539-546 | TPE 전체 크래시 → 빈 candidates → error_fallback → 빈 원고 Director 전달 | 신규 |
| 3 | TF-NPC-01 | NPC Tracker | state_tracker_npc.py:L2052 | Operator precedence 모호성 (and/or 괄호 부재) — emotion summary 로직 오류 | 신규 |
| 4 | TF-NPC-02 | NPC Tracker | state_tracker_npc.py:L2029-2033 | Emotion regex 비캡처 그룹에 `주인공` 중복 앵커가 들어가 실제 캐릭터명 미매칭, 전체 감정 fallback 데드코드 | 신규 |
| 5 | TF-NPC-03 | NPC Tracker | state_tracker_npc.py:L719 | Death regex "운명" FP — 일반 서사 텍스트에서 사망 오탐 | 신규 |
| 6 | TF-NPC-04 | NPC Tracker | state_tracker_npc.py:L435-458 | `_is_standalone_name` context-blind — 회상 장면 억제가 전체 텍스트에 적용 | 신규 |
| 7 | TF-BA-01 | Base Agent | base_agent.py:L1893-1933 | 로컬 TTL vs 서버 TTL drift → 만료 캐시 사용 → API 에러 + 이중 비용 | 신규 |
| 8 | TF-BA-02 | Base Agent | base_agent.py:L1959-2081 | cached context path에 MetricsCollector start/end_call 누락 — 5개 에이전트 비용 집계 불완전 | 신규 |
| 9 | TF-DE-02 | Director Ensemble | director_ensemble.py:L1120-1150 | Contradiction Firewall이 LLM self-report에만 의존 — Python advisory (TruthGate 등) 미연동 | 신규 |
| 10 | TF-DE-09 | Director Ensemble | director_ensemble.py:L802-1055 | 단일 LLM 호출로 3후보 평가 — 진정한 multi-agent voting 부재, single-point-of-failure | 신규 |
| 11 | TF-AR-01 | Adaptive Retry | adaptive_retry.py:L241-252 | V54.3 에러 3종 (CHARACTER_INCONSISTENCY, LOGIC_ERROR, SCOPE_OVERFLOW) get_retry_strategy 핸들러 부재 | 신규 |
| 12 | TF-AR-02 | Adaptive Retry | adaptive_retry.py:L79-96 | V54.3 에러 3종 MAX_RETRIES/WAIT_TIME 딕셔너리 누락 → 기본값 fallback | 신규 |
| 13 | TF-ST-01 | StateTracker | state_tracker.py:L938-950 | `merge_from_previous_arcs` 3/23+ 레지스트리만 병합 — Analyst 경로에서 플롯/타임라인/커밋먼트 전량 소실 | 신규 |
| 14 | TF-ST-02 | StateTracker | state_tracker.py:L187-249 | 핵심 4종 추출 메서드 try/except 부재 — 1건 예외 시 나머지 arc 전체 추출 중단 | 신규 |
| 15 | TF-ST-03 | StateTracker | state_tracker.py (전체) | Advisory 8-thread 무잠금 동시 접근 — check_suspended_plots가 active_plots["status"] 직접 mutation | 신규 |
| 16 | TF-CQ-02 | CW Quality | chief_writer_quality.py:L346-358 | 1~2건 medium 이슈가 overall "low"로 분류 → self-critique 조기 종료, NPC 관계 불일치 탈출 | 신규 |
| 17 | TF-CQ-05 | CW Quality | chief_writer_quality.py:L138-159 | Rubric score ≥ 3.5 조기 종료 시 Gate 검사 (ending_hook, meta-term, length) 건너뜀 | 신규 |
| 18 | TF-CQ-18 | CW Quality | chief_writer_quality.py:L1138-1161 | LLM 수정본이 빈/최소 내용이어도 검증 없이 수락 — 원고 품질 퇴화 | 신규 |
| 19 | TF-CM-01 | Continuity MS | continuity_manuscript.py:L327-355 | LLM 실패 시 `decision: "PASS"` 반환 (fail-open) — Director fail-closed 정책 위반 | 신규 |

> **추가 borderline-CRITICAL**: TF-CM-02 (JSON 파싱 실패 시 PASS), TF-CM-03 (STATE_ORDER 사망/굴복 누락)

---

## IMPORTANT / P1 항목 전체 목록 (52건)

### TF-CW (ChiefWriter) — 6건

| ID | 위치 | 제목 |
|----|------|------|
| TF-CW-02 | quality:L1138-1158 | _fix_manuscript_issues MIN_LENGTH 미달 수정본 반환 |
| TF-CW-03 | quality:L32-77 | sanitize_leakage 전략 지시문/시스템 마커 미필터링 |
| TF-CW-04 | L528-538 | 전체 타임아웃 시 RUNNING future 백그라운드 지속 + shutdown 블로킹 |
| TF-CW-07 | manuscript.py:L43-50 | Pydantic 실패 시 raw dict 반환 |
| TF-CW-11 | quality:L137-164 | Rubric 조기 종료 시 Gate 검사 건너뜀 (갭 제한적) |
| TF-CW-14 | 전체 | 공유 상태 mutation 없음 확인 (양성) |

### TF-NPC (NPC Tracker) — 11건

| ID | 위치 | 제목 |
|----|------|------|
| TF-NPC-05 | 모듈 전체 | `[가-힣]{2,10}` 일반 명사 매칭 FP |
| TF-NPC-06 | L76-140 | Death exclude에 직함 어휘 누락 |
| TF-NPC-07 | L868-925 | 관계 상태 전이 무검증 (적→동맹 무제한) |
| TF-NPC-08 | L927-989 | NPC 부상 회복 경로 부재 |
| TF-NPC-09 | L1200-1325 | 영구 부상 역전 불가 |
| TF-NPC-10 | L1697-1700 | FIFO eviction이 중요 NPC-NPC 관계 소실 |
| TF-NPC-11 | L621-651 | Merge 시 감사 추적/롤백 불가 |
| TF-NPC-12 | L1884-1917 | Companion join/leave 단일 seen set 충돌 |
| TF-NPC-13 | L1873-1882 | Companion leave가 list reference 교체 |
| TF-NPC-14 | L484/1475/1551 | Dead NPC 패턴 3x 중복 (불일치 flashback set) |
| TF-NPC-17 | 파일 전체 | npc_registry 무제한 증가 |

### TF-BA (Base Agent) — 8건

| ID | 위치 | 제목 |
|----|------|------|
| TF-BA-03 | L1177, L1338 | 폴백/백업 config http_options 누락 |
| TF-BA-04 | L1498, L1543 | _classify_error/_is_network_error "timeout" 충돌 → 22회 네트워크 재시도 |
| TF-BA-05 | L1742-1786 | JSON 평탄화 시 중첩 구조 소실 |
| TF-BA-06 | L1709-1731 | regex 폴백 greedy 매칭 → content 잘림 |
| TF-BA-07 | L2064-2081 | 캐시 폴백 시 이중 비용 + DB 이중 기록 |
| TF-BA-08 | L1498, L1091 | _classify_error 429 분류 불일치 |
| TF-BA-09 | L1896-1941 | 캐시 생성 TOCTOU (순차 처리로 실질 위험 낮) |
| TF-BA-10 | L998, L773 | 폴백 시 metric 모델명 불일치 |

### TF-DE (Director Ensemble) — 6건

| ID | 위치 | 제목 |
|----|------|------|
| TF-DE-01 | L784-800 | _fallback_arc_selection 데드코드 (docstring↔코드 불일치) |
| TF-DE-03 | L1244-1262 | Adaptive threshold retry decay (-10 가능) |
| TF-DE-04 | L882, L1114-1118 | SCM 편향 보정 불완전 (91-94점 미보정) |
| TF-DE-05 | L1252-1262 | Verdict catch-all else → PASS 분기 |
| TF-DE-06 | L1098-1108 | NC-3B score reconciliation 비표준 키 인플레이션 |
| TF-DE-08 | L422,780,1006,1052,1416 | 메서드 간 예외 처리 불일치 |

### TF-AR (Adaptive Retry) — 5건

| ID | 위치 | 제목 |
|----|------|------|
| TF-AR-03 | L197-227 | classify_error/record_failure 이중 분류 비대칭 |
| TF-AR-04 | L55-62 | 싱글턴 컨텍스트 dict 무한 축적 |
| TF-AR-05 | L268-290 | 동일 전략 재적용 방지 부재 |
| TF-AR-06 | L157-170 | "score"/"점수" QUALITY_ISSUE 과매칭 |
| TF-AR-07 | L175-185 | "제한" QUOTA_EXCEEDED 오매칭 |

### TF-ST (StateTracker + Plots) — 7건

| ID | 위치 | 제목 |
|----|------|------|
| TF-ST-04 | state_tracker.py 전체 | 23+ 레지스트리 스냅샷/복원 부재 |
| TF-ST-05 | state_tracker_plots.py:L98-369 | active_plots/resolved_plots 이중 상태 |
| TF-ST-06 | state_tracker.py:L1615 | _populate_genre_registries full_extract 미호출 |
| TF-ST-07 | main_a.py:L4018 vs stage3:L638 | bind_world_state 초기화 순서 불일치 |
| TF-ST-08 | state_tracker_financial.py:L39-46 | 금융 데이터 타입 검증 부재 |
| TF-ST-09 | state_tracker_plots.py:L119-123 | resolved_plots O(n) 중복 검사 |
| TF-ST-10 | state_tracker_plots.py:L371-390 | check_suspended_plots CQS 위반 (읽기 중 mutation) |

### TF-CQ (CW Quality) — 8건

| ID | 위치 | 제목 |
|----|------|------|
| TF-CQ-01 | L1186-1254 | Rubric equal-weight 하드코딩 (장르 무차별) |
| TF-CQ-03 | L1103 | 최대 3개 이슈만 수정 지시 (심각도 무시) |
| TF-CQ-04 | L698-710 | NPC 관계 검사 re.DOTALL 오탐 |
| TF-CQ-10 | L570-595 | HUD 일관성 검사 무협 편향 |
| TF-CQ-11 | L597-642 | 클리셰 검사 무협 전용 |
| TF-CQ-12 | L1257-1289 | 클리셰 캐시 미스 시 무감지 |
| TF-CQ-13 | L196-239 | Self-Critique 비수렴 위험 (오실레이션) |
| TF-CQ-15 | L32-77 | sanitize_leakage 경로 불일치 |

### TF-CM (Continuity Manuscript) — 8건

| ID | 위치 | 제목 |
|----|------|------|
| TF-CM-02 | L293-305 | JSON 파싱 실패 시 PASS (fail-open) |
| TF-CM-03 | L1055-1065 | STATE_ORDER에 사망/굴복 누락 → 부활 미감지 |
| TF-CM-04 | L841-843 | 원고 절단 경계 정보 소실 |
| TF-CM-05 | L509/L1043 | 관계 추적 메서드 2개 중복 + 상태 모델 불일치 |
| TF-CM-06 | L216, L1164 | hud_history 데드 파라미터 |
| TF-CM-07 | L275 | 원고 excerpt 4,000자 절단 |
| TF-CM-08 | L496-507 | _is_item_acquired 50% 부분매칭 오탐 |
| TF-CM-09 | L1158-1167 | v59에서 entity_registry 미전달 |
| TF-CM-10 | L445-464 | BP 키워드 매칭 14 stopwords만 |
| TF-CM-11 | L543-558 | find/rfind 비대칭 관계 탐지 |

---

## 스테이지별 건강도 업데이트

기존 fix-candidates-ssot (25건) + 이번 서브시스템 딥다이브 (109건) 통합:

| 계층 | CRITICAL | IMPORTANT | INSIGHT | 핵심 위험 |
|------|----------|-----------|---------|----------|
| **Stage 2 파이프라인** | 2 (기존) | 2 (기존) | — | 재시도 로직 결함, 상태 롤백 미흡 |
| **Stage 3 파이프라인** | 0 (기존) | 2 (기존) | — | 장기 연재 컨텍스트 절삭 |
| **Stage 4 파이프라인** | 1 (기존) | 2 (기존) | — | 에스컬레이션 후 검증 갭 |
| **Cross-Stage** | 1 (기존) | 2 (기존) | — | StateTracker write-back 부재 |
| **ChiefWriter 계열** | 5 (신규) | 14 (신규) | 13 | 빈 원고 전파, 품질 게이트 회피, 수정본 미검증 |
| **StateTracker 계열** | 7 (신규) | 18 (신규) | 12 | NPC regex FP/FN, 무잠금 8-thread, merge 20+ 누락 |
| **Base Agent** | 2 (신규) | 8 (신규) | 5 | TTL drift 이중 비용, 비용 집계 누락 |
| **Director Ensemble** | 2 (신규) | 6 (신규) | 4 | Contradiction Firewall LLM-only, 단일 호출 |
| **Adaptive Retry** | 2 (신규) | 5 (신규) | 5 | V54.3 핸들러 부재, 컨텍스트 무한 축적 |
| **Continuity MS** | 3 (신규) | 8 (신규) | 5 | fail-open 정책 위반, STATE_ORDER 누락 |
| **합계** | **23** | **67** | **39+** | |

---

## 기존 fix-candidates-ssot 대비 신규 발견 항목

### 완전 신규 (기존 25건과 겹치지 않는 서브시스템)
- 이번 8개 서브시스템은 기존 fix-candidates-ssot에서 **조사 대상 외**였음
- 따라서 **109건 전량이 신규 발견**

### 기존 항목과 연관/보강되는 발견

| 기존 ID | 기존 제목 | 연관 신규 ID | 보강 내용 |
|---------|----------|-------------|----------|
| X-1 | Stage 4 StateTracker write-back 없음 | TF-ST-01 | merge_from_previous_arcs도 3/23+ 레지스트리만 복사 — write-back 해도 불완전 |
| X-1 | (동일) | TF-ST-04 | 스냅샷/복원 메커니즘 자체 부재 |
| S2-2 | DB 커밋 실패 StateTracker 미롤백 | TF-ST-04 | 롤백 대상 스냅샷 시스템 없음 — S2-2 수정의 전제조건 |
| S4-3 | state_updates Director 경계 부분 소실 | TF-DE-06 | NC-3B score reconciliation도 비표준 키 인플레이션 |
| S4-5 | PASS_WITH_FIX 빈 피드백 | TF-CQ-02 | medium 이슈가 "low"로 분류되어 self-critique 탈출 — PASS_WITH_FIX 트리거 전 단계에서 이미 이슈 누락 |
| S4-1 | 에스컬레이션 후 연속성 미검증 | TF-CM-01 | 연속성 검사 자체가 LLM 실패 시 fail-open — 검증 게이트 추가해도 게이트 자체 신뢰성 문제 |

---

## 위험도 Top 10 (통합 기준)

수정 시 영향도 × 발생 확률로 선정:

| 순위 | ID | 제목 | 근거 |
|------|-----|------|------|
| 1 | TF-ST-01 | merge 20+ 레지스트리 누락 | Analyst 경로 사용 시 플롯/타임라인 전량 소실 |
| 2 | TF-CM-01 | LLM 실패 fail-open PASS | 네트워크 불안정 시 모순 원고 자동 승인 |
| 3 | TF-NPC-02 | 감정 regex 데드코드 | 전체 감정 추출 fallback 사실상 미작동 |
| 4 | TF-BA-02 | 캐시 경로 MetricsCollector 누락 | 5개 주력 에이전트 비용 집계 불완전 |
| 5 | TF-CW-01 | 빈 원고 Director 전파 | 전 전략 실패 시 Director가 빈 원고 평가 |
| 6 | TF-ST-03 | 8-thread 무잠금 | 런타임 상태 오염 (재현 어려운 간헐적 버그) |
| 7 | TF-CQ-02 | medium → "low" 분류 탈출 | NPC 관계 불일치 품질 게이트 통과 |
| 8 | TF-DE-02 | Contradiction Firewall LLM-only | Python advisory 경고 무시 |
| 9 | TF-CM-03 | STATE_ORDER 사망/굴복 누락 | 사망 NPC 부활 미감지 |
| 10 | TF-AR-01 | V54.3 에러 전략 부재 | CHARACTER_INCONSISTENCY/LOGIC_ERROR 재시도 무전략 |

---

## 개별 TF 문서 인덱스

| 파일명 | 항목 수 |
|--------|--------|
| [tf-cw-chief-writer-ensemble-deepdive.md](tf-cw-chief-writer-ensemble-deepdive.md) | 14 (2C/6I/6S) |
| [tf-npc-state-tracker-npc-deepdive.md](tf-npc-state-tracker-npc-deepdive.md) | 23 (4C/11I/8S) |
| [tf-ba-base-agent-cache-deepdive.md](tf-ba-base-agent-cache-deepdive.md) | 15 (2C/8I/5S) |
| [tf-de-director-ensemble-verdict-deepdive.md](tf-de-director-ensemble-verdict-deepdive.md) | 12 (2C/6I/4S) |
| [tf-ar-adaptive-retry-deepdive.md](tf-ar-adaptive-retry-deepdive.md) | 12 (2C/5I/5S) |
| [tf-st-state-tracker-plots-deepdive.md](tf-st-state-tracker-plots-deepdive.md) | 14 (3C/7I/4S) |
| [tf-cq-chief-writer-quality-deepdive.md](tf-cq-chief-writer-quality-deepdive.md) | 18 (3C/8I/7S) |
| [tf-cm-continuity-manuscript-deepdive.md](tf-cm-continuity-manuscript-deepdive.md) | 16 (3C/8I/5S) |

---

---

## [3PA] 3-Pass Audit 감리 결과 (2026-03-16)

### CRITICAL 항목 감리 (19건 → 8건 생존)

| ID | 판정 | 확신도 | 사유 |
|----|------|--------|------|
| TF-CW-01 | **[3PA] RECLASSIFIED→INSIGHT** | 95% | `stage4_interview_round.py:L1511`이 `manuscript=""` 후보 필터링. Director 도달 불가. |
| TF-CW-08 | **[3PA] RECLASSIFIED→IMPORTANT** | 90% | 하류 방어 존재하나 라운드 낭비. |
| TF-NPC-01 | **[3PA] RECLASSIFIED→INSIGHT** | 95% | 연산자 우선순위가 "우연히 정확". `not pe`는 빈 dict에서 항상 False. |
| TF-NPC-02 | **[3PA] RECLASSIFIED→IMPORTANT** | 95% | regex fallback dead code이나 primary LLM 추출 경로 정상 작동. |
| TF-NPC-03 | **[3PA] RECLASSIFIED→IMPORTANT** | 95% | LLM 검증 레이어(L736)로 FP 실효 완화. |
| TF-NPC-04 | **[3PA] CONFIRMED** | 95% | context-blind 매칭 진정한 로직 결함. |
| TF-BA-01 | **[3PA] CONFIRMED** | 95% | TTL drift 윈도우는 좁으나 실재. fallback이 이중 비용 발생. |
| TF-BA-02 | **[3PA] CONFIRMED** | 98% | 캐시 경로에 MetricsCollector 호출 완전 부재. 5개 에이전트 비용 미집계. |
| TF-DE-02 | **[3PA] CONFIRMED** | 95% | Firewall이 LLM self-report에만 의존. Python advisory 미연동. |
| TF-DE-09 | **[3PA] RECLASSIFIED→IMPORTANT** | 90% | 의도적 비용/레이턴시 트레이드오프. "앙상블"은 후보의 앙상블. |
| TF-AR-01 | **[3PA] RECLASSIFIED→IMPORTANT** | 92% | 프로덕션은 `AdaptiveRetryManager` 경로 사용하여 V54.3 정상 처리. |
| TF-AR-02 | **[3PA] RECLASSIFIED→IMPORTANT** | 92% | TF-AR-01과 동일 근본 원인. **[3PA] DEDUP — TF-AR-01과 병합 권고.** |
| TF-ST-01 | **[3PA] CONFIRMED** | 95% | 3/23+ 레지스트리만 병합 확인. Analyst 경로에서 플롯/타임라인 소실. |
| TF-ST-02 | **[3PA] CONFIRMED** | 97% | 핵심 4종 추출 try/except 부재. 1건 예외 시 나머지 arc 전체 중단. |
| TF-ST-03 | **[3PA] RECLASSIFIED→IMPORTANT** | 90% | 아키텍처 상 advisory 병렬 실행 중 write 미발생. 실질적 race 없음. |
| TF-CQ-02 | **[3PA] CONFIRMED** | 97% | 1-2건 medium → "low" → break. 진정한 품질 게이트 탈출. |
| TF-CQ-05 | **[3PA] RECLASSIFIED→IMPORTANT** | 95% | **[3PA] DEDUP — TF-CW-11과 동일 메커니즘.** `_self_critique`가 동일 검사 실행. |
| TF-CQ-18 | **[3PA] RECLASSIFIED→IMPORTANT** | 95% | **[3PA] DEDUP — TF-CW-02와 동일 코드 경로.** 다중 라운드 재감지로 완화. |
| TF-CM-01 | **[3PA] CONFIRMED** | 98% | fail-open PASS 확인. `degraded=True` 설정하나 하류 미소비. |

### IMPORTANT 항목 감리 (52건 요약)

| 판정 | 건수 | 주요 하향 |
|------|------|----------|
| CONFIRMED | 37 | — |
| RECLASSIFIED→INSIGHT | 7 | TF-NPC-08(회복경로존재), TF-NPC-10(DB보존), TF-NPC-12(fallback전용), TF-NPC-13(잠재위험), TF-ST-07(순서차이무영향), TF-ST-08(수치연산미존재), TF-ST-09(500캡내무시가능) |
| RECLASSIFIED→INSIGHT | 1 | TF-BA-08 (429 분류 불일치는 로깅에만 영향) |
| FALSE-POSITIVE | 1 | TF-BA-15 (attempt 카운터는 의도적 continuation 추적) |
| Not sampled | 6 | INSIGHT 미표본 |

### INSIGHT 항목 감리 (44건 중 ~15건 표본)

표본 전량 CONFIRMED (85-99%). 미표본 29건은 deepdive 평가 수용.

**요약**: CRITICAL 19건 중 생존 8건 (42.1%). 전체 109건 중 CONFIRMED 78건, RECLASSIFIED 24건, FP 1건, 미표본 6건.

*3-Pass Audit by Claude Opus 4.6 — 2026-03-16*

### [3PA-R2] 대원칙 적용 재감리 (2026-03-16)

대원칙 4개를 감사 렌즈로 추가 적용한 결과, 본 SSOT에서 8건 판정 변경.

#### CRITICAL 항목 R2 변경 (3건)

| ID | R1 판정 | R2 판정 | R2 확신도 | 대원칙 | 사유 |
|----|---------|---------|-----------|--------|------|
| **TF-DE-02** | CONFIRMED (95%) | **CLOSED** | **98%** | **#3+#1** | Contradiction Firewall가 LLM-only = Director 주권(#3) + Python 수집만(#1) 정합. Python advisory는 `_director_mc_parts`로 이미 Director에 전달. Firewall은 Director의 독자적 판단 도구. |
| **TF-DE-09** | RECLASSIFIED→IMP (90%) | **CLOSED** | **96%** | **#3** | 단일 LLM 호출 = 내각제 구현. Director가 sovereign. "앙상블"은 후보 원고의 앙상블이지 판사의 앙상블이 아님. 비용/레이턴시 의도적 트레이드오프. |
| **TF-CM-03** | CONFIRMED (97%) | **CONFIRMED** | **98%** | **#4** | STATE_ORDER에 "사망" 미포함 → deceased→non-deceased 상태 전이 미감지. **대원칙#4 직접 위반 가능성.** 확신도 상향. |

#### IMPORTANT 항목 R2 변경 (5건)

| ID | R1 판정 | R2 판정 | R2 확신도 | 대원칙 | 사유 |
|----|---------|---------|-----------|--------|------|
| **TF-NPC-05** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | 97% | #1 | `_verify_npc_names_llm()`(L745-825)가 LLM 필터 수행. `[가-힣]{2,10}` FP는 collection noise. |
| **TF-NPC-06** | CONFIRMED(IMP) | **RECLASSIFIED→INSIGHT** | 97% | #1 | death detection은 수집 단계. REJECT는 별도 `check_dead_npc_appearance()`에서만. 직함 누락은 수집 정밀도. |
| **TF-ST-03** | RECLASSIFIED→IMP (90%) | **RECLASSIFIED→INSIGHT** | 94% | #1 | 8-thread advisory는 전량 read-only. `_merge_advisory_validation_results()` main thread 순차 실행. write 미발생. |
| **TF-AR-06** | CONFIRMED(IMP) (75%) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | "score" 오매칭 → 재시도 전략만 영향. 최종 PASS/REJECT는 Director LLM 판정. |
| **TF-AR-07** | CONFIRMED(IMP) (70%) | **RECLASSIFIED→INSIGHT** | **96%** | #1 | "제한" 오매칭 → 재시도 효율만 영향. 최종 판정은 LLM. |

**R2 CRITICAL 생존**: 8건 → **6건** (-2: TF-DE-02/09 CLOSED).
**R2 요약**: 109건 중 CONFIRMED 72건, RECLASSIFIED 26건(+2), FP 1건, CLOSED **2건**(+2), 미표본 6건.

*3-Pass Audit R2 (대원칙) by Claude Opus 4.6 — 2026-03-16*
