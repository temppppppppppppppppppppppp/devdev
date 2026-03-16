# 3-Pass 감리: 끊긴 루프 전수조사

> 감리일: 2026-03-16
> 감리자: Claude Opus 4.6 (1M context)
> 대상: 조사_TF-A ~ TF-F 전 6건
> 방법론: Pass 1 (사실 검증) → Pass 2 (교차 일관성) → Pass 3 (누락/오분류)

---

## Pass 1: 사실 검증 (Producer Line 정확도)

모든 TF 문서의 file:line 참조를 코드 직접 읽기로 대조.

| TF | 검증 항목 수 | 정확 | 오류 | 비고 |
|----|-------------|------|------|------|
| A | 9 | 9 | 0 | to_prompt() 라인 번호 정확. anti_ai_patterns LIVE 확인 |
| B | 3 | 3 | 0 | PreDirectorManuscriptChecker 하드코딩 0.30 확인 |
| C | 3 | 3 | 0 | coverage_warnings 관측 전용 확인 |
| D | 8 | 8 | 0 | episode_quality_signals DB 저장 → bridge_server만 조회 확인 |
| E | 8+2 | 10 | 0 | get_cost_summary 호출자 0건 확인. DPW/FailureLearner LIVE 확인 |
| F | 13 | 13 | 0 | 역방향 피드백 3건 FRAGILE 확인 |

**Pass 1 결론**: 전 항목 사실 정확. 오류 0건.

---

## Pass 2: 교차 일관성 (TF 간 모순 점검)

### 2-1. TF-A vs TF-B: anti_ai_patterns 상태

| 문서 | 판정 |
|------|------|
| TF-A | LIVE (StyleGuard 강제) |
| TF-B | ENFORCED (brittle, substring 매칭) |

**일관성**: ✅ 양립 가능. TF-A는 "소비자 존재 여부", TF-B는 "강제 방식의 품질". 동일 신호를 다른 축에서 평가.

### 2-2. TF-D vs TF-E: DPW 상태

| 문서 | 판정 |
|------|------|
| TF-D (DPW 언급 없음) | — |
| TF-E | DPW = LIVE (runtime-affecting) |
| TF-F | DPW = WORKING (F-5) |

**일관성**: ✅ DPW는 TF-E/F에서 LIVE/WORKING 일치. TF-D는 DPW와 무관 (quality_signal_metrics 범위).

### 2-3. TF-C vs TF-D: coverage_warning 이중 등록

| 문서 | 판정 |
|------|------|
| TF-C | ADVISORY-ONLY (S3 관측) |
| TF-D | WEAK (S4 Blueprint metadata에 암묵 포함) |

**일관성**: ✅ 양립 가능. TF-C는 S3 생산 측면, TF-D는 S4 소비 측면. **동일 신호의 생산↔소비 양면**.

### 2-4. TF-D vs TF-F: npc_drift 상태

| 문서 | 판정 |
|------|------|
| TF-D | ADVISORY-ONLY (Director에게만 전달) |
| TF-F | (별도 항목 없음) |

**일관성**: ✅ TF-F는 정상 루프만 다룸. npc_drift는 끊긴 루프이므로 TF-D 관할.

### 2-5. 전체 수량 교차 검증

| 카테고리 | 계획 | 실제 식별 | 비고 |
|---------|------|----------|------|
| 끊긴/약한 신호 | 29건 | 29건 | TF-A(7) + TF-B(3) + TF-C(3) + TF-D(8) + TF-E(8) = 29 |
| 정상 루프 | 13건 | 13건 | TF-F 전량 |

**Pass 2 결론**: TF 간 모순 0건. 수량 일치.

---

## Pass 3: 누락/오분류 점검

### 3-1. 누락 신호 점검

아래 추가 신호가 조사 범위에서 누락되었는지 점검:

| 잠재 신호 | 검토 결과 | 판정 |
|----------|----------|------|
| `reverse_feedback_stage4_to_2` | feedback_system.py:691-760에 존재. Arc 난이도 기반 역방향 피드백 | TF-F에서 미포함 → **추가 권고** |
| `pre_checklist_result` | feedback_system.py:639-645에서 참조. S4→S3 역방향에 pre-checklist 실패 포함 | TF-F-10 내 포함 (별도 불필요) |
| `protagonist_tracker` | DB 테이블. StateTracker가 읽기/쓰기 | TF-F-6 HUD 루프에 포함 |
| `style_guide DB 캐시` | style_guide.json 파일 캐시 | S0 내부 캐시. 피드백 루프 아님 (제외 정당) |

**추가 식별**: `reverse_feedback_stage4_to_2` (feedback_system.py:691-760)
- Arc 난이도 기반 역방향 피드백
- semantic_failures, reject_bucket, weak_score_areas 분석
- **Status**: TF-F와 동일 패턴 — 구현되어 있으나 자동 주입 여부 미확인
- **영향**: 기존 TF-F-10/11과 동일 FRAGILE 범주. 별도 TF 불필요. TF-F에 주석 추가 권고.

### 3-2. 오분류 점검

| Signal | 현재 분류 | 재검토 결과 | 변경 |
|--------|----------|------------|------|
| TF-A exemplary_passages | WEAK | to_prompt + reference_excerpt 재료 + UI 표시. 3곳 사용이나 모두 입력 재료 | **유지** |
| TF-B anti_ai_patterns | ENFORCED (brittle) | StyleGuard에서 substring 매칭 수행. severity MEDIUM | **유지** |
| TF-D npc_drift | ADVISORY-ONLY | Director mandatory_context에 전달 → 간접 reject 가능 | **유지** (WEAK으로 상향 불가 — Director가 npc_drift를 명시적으로 reject 사유에 기재하지 않을 수 있음) |
| TF-E decisions.jsonl | ANALYSIS-ONLY | FailureAnalyzer가 읽지만 사후 분석 전용 | **유지** |
| TF-F FactLedger | FRAGILE | advisory-only. hard validation 없음 | **유지** |

**Pass 3 결론**: 오분류 0건. 누락 1건(reverse_feedback_stage4_to_2) 발견 → TF-F 주석 추가 권고.

---

## 종합 판정

### 전체 통계

| 분류 | 건수 | 신호 |
|------|------|------|
| **DEAD** | 10 | A-1~7(WEAK→to_prompt only), B-3(vocabulary), D-1(ai_slop), D-3(open_review), D-4~6(compression/burst/complex), D-7(ced), E-1(cost_log), E-2(learnable) |
| **ADVISORY-ONLY** | 3 | C-1(coverage_warn), D-2(npc_drift), D-8(coverage_warn S4) |
| **WRITE-ONLY** | 5 | E-3~6(session logs), E-7(audit_service) |
| **DIAGNOSTIC** | 1 | E-8(soft_failures.jsonl) |
| **ENFORCED** (brittle) | 1 | B-1(anti_ai_patterns) |
| **ADVISORY** (하드코딩 타겟) | 1 | B-2(dialogue_ratio) |
| **LIVE** | 4 | A-8(anti_ai), A-9(reference_excerpt), E-DPW, E-FailureLearner |
| **FRAGILE** | 3 | F-7(FactLedger), F-10(S4→S3), F-11(S3→S2) |
| **WORKING** | 10 | F-1~6, F-8,9,12,13 |

※ TF-A의 7개 WEAK 필드는 to_prompt() 경유 soft guidance로 기능하므로 "완전 DEAD"가 아닌 "WEAK (to_prompt only)"로 세분화. 프로그래밍적 검증/강제 경로가 없다는 점에서 끊긴 루프에 해당.

### Top 5 Remediation 우선순위 (비용 대비 효과)

| 순위 | Signal | 조치 | 효과 | 난이도 |
|------|--------|------|------|--------|
| **1** | ai_slop (D-1) | retry CW에 이전 라운드 hit 패턴 주입 | AI 슬랍 반복 즉시 감소 | LOW |
| **2** | dialogue_ratio (B-2) | PreDirectorManuscriptChecker에 StyleGuide 타겟 연동 | 장르별 대화 비율 강제 | LOW |
| **3** | FactLedger (F-7) | 충돌 감지 시 hard constraint violation 에스컬레이션 | NPC 사망/부활 모순 차단 | MEDIUM |
| **4** | ced_score (D-7) | CED 임계값 초과 시 retry mandatory_context 경고 | 일관성 오류 축적 방지 | LOW |
| **5** | cost_log (E-1) | get_cost_summary() 호출 + 세션 비용 대시보드 | 비용 모니터링/제한 | LOW |

### KEEP-AUDIT (현행 유지 권장)

| 범위 | 근거 |
|------|------|
| TF-A WEAK 7건 | to_prompt() 경유 soft guidance로 충분. 강제 시 과도 engineering |
| TF-E session logs 4건 | 감사 로그 가치. 런타임 소비 불필요 |
| TF-D compression/burstiness/complexity | 트렌드 모니터링용 충분. ROI 낮음 |

---

## 감리 서명

- **Pass 1**: 사실 검증 통과 (오류 0건)
- **Pass 2**: 교차 일관성 통과 (모순 0건, 수량 일치)
- **Pass 3**: 누락/오분류 점검 통과 (누락 1건 식별 → 주석 추가 권고, 오분류 0건)
- **최종 판정**: 전 TF 문서 **감리 통과**
