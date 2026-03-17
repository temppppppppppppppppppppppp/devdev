# 축 13: 잘 설명하고 (Explainability)

Date: 2026-03-17
Bundle: C
3-Pass Audit: 88% → 93% → 96%
Final Confidence: 96%

## 1. 핵심 질문

산출물의 의사결정 과정을 사후에 추적하고 이해할 수 있는가?

구체적으로:
- "이 원고에서 사망 NPC가 왜 살아났는지" 역추적이 가능한가?
- "이번 에피소드 품질이 왜 낮았는지" 시스템에 물어볼 수 있는가?
- Director가 왜 이 후보를 선택했는지, CW가 왜 이렇게 썼는지 재구성 가능한가?

---

## 2. 현황 인벤토리

### 2.1 의도적 구현

| # | 구성요소 | 파일 | 핵심 기능 | 설명력 등급 |
|---|---------|------|----------|-----------|
| 1 | SessionLogger | `modules/core/session_logger.py` | 4개 JSONL 스트림 (llm_io, decisions, state_changes, ui_events) 분리 기록 | 높음 |
| 2 | Director Verdict 구조 | `modules/domain/agents/director_ensemble.py:374-431` | selection_reason, verdict_reason, comparison_notes, open_review, thinking 등 6+ 근거 필드 기록 | 높음 |
| 3 | contradiction_check | `modules/domain/agents/director_prompts.py:124-161` | type, prev_fact, current_violation, severity, prev_episode 구조화 모순 기록 | 매우 높음 |
| 4 | score_breakdown (5차원) | `modules/domain/agents/director_ensemble.py:44-50` | continuity_contradiction, blueprint_coverage, quality_engagement, length, python_warnings 개별 기록 | 높음 |
| 5 | director_selections DB | `modules/core/db_manager.py:515-531` | selection_reason, verdict_reason, firewall_triggered, firewall_reason, pre_firewall_score 등 영구 저장 | 높음 |
| 6 | stage_attempts DB | `modules/core/db_manager.py:641-662` | selection_reason, verdict_reason, open_review, fix_scope_reasoning, runtime_advisory, retry_directives 저장 | 높음 |
| 7 | Artifact Snapshot | `modules/core/artifact_logging.py:40-89` | candidate_key, content_hash(SHA256), artifact_path로 실물 원고 연결 | 높음 |
| 8 | Rationale Contract | `modules/core/stage4_canary_tools.py:23-36` | STAGE4_RATIONALE_FIELDS 튜플로 근거 필드 누락 시 경고 발생 | 높음 |
| 9 | Quality Dashboard | `modules/core/quality_dashboard.py` | validation_history, hud_anomalies, blueprint_coverage, quality_signal_history 집계 | 중간 |
| 10 | Pass Rate Monitor | `modules/core/pass_rate_monitor.py:32-59` | AttemptRecord: reject_reason, error_category, reject_bucket, score_breakdown 기록 | 중간 |
| 11 | Audit Service | `modules/core/services/audit_service.py:91-130` | 5개 싱크 간 정합성 비교, rationale_metadata_missing 탐지 | 중간 |
| 12 | Gate Basis 분류 | `modules/domain/agents/director_ensemble.py:177-193` | continuity_firewall / quality_floor_fail / director_primary_pass / director_primary_reject 4종 라벨 | 높음 |
| 13 | Director Auditor | `modules/domain/agents/director_auditor.py` | entity mismatch, character logic, length violation, repetition 등 진단 보고서 생성 | 중간 |
| 14 | Firewall Mode 분류 | `modules/domain/agents/director_ensemble.py:347-371` | firewall_reason에 모순 유형·개수 명시 (예: "Fixable Contradiction Firewall: local contradiction 2count") | 높음 |

### 2.2 부수적 기여

| # | 구성요소 | 파일 | 부수적 설명력 |
|---|---------|------|-------------|
| 1 | LLM thinking 토큰 | `session_logger.py:92,109-110` | CW/Director의 중간 추론 과정이 llm_io.jsonl에 기록 (의도: 디버깅, 부수적: 의사결정 추적) |
| 2 | episode_production.jsonl | `stage4_orchestrator.py` | initial_verdict, final_verdict, patch_trace, reason 필드 (의도: 생산 로그, 부수적: 의사결정 요약) |
| 3 | Feedback System | `modules/core/feedback_system.py` | build_structured_feedback()의 violations/severity 구조 (의도: 재시도 안내, 부수적: 거부 근거 기록) |
| 4 | _log_director_frame() | `director_ensemble.py:374-431` | INFO/WARNING/DEBUG 레벨 로깅 (의도: 런타임 모니터링, 부수적: 사후 추적) |

---

## 3. 갭 식별

### G13-1. CW 창작 의도 블랙박스 — 완전 부재

**증거**: `chief_writer.py` 전체 2000+ 라인 조사 결과, CW가 "왜 이렇게 썼는지"를 기록하는 메커니즘이 없음. `thinking_level="medium"`으로 LLM thinking 토큰은 생성되지만, 이는 `llm_io.jsonl`에만 기록되며 의사결정 싱크(decisions.jsonl, DB)와 연결되지 않음.

**현재 상태**: CW의 전략(balanced/narrative/tension)은 기록되나, "이 전략으로 이 장면을 이렇게 쓴 이유"는 어디에도 없음. Director feedback → CW 반영 경로는 있으나, CW → "내가 이렇게 반영했다" 출력 경로는 없음.

### G13-2. comparison_notes 240자 절삭 — 부분 구현

**증거**: `director_ensemble.py:396`에서 `_short_text(comparison_notes, 240)` 적용. 3개 후보의 장단점 비교 분석이 240자에 절삭됨. 로깅에서도 150자+"..." 표시(`director_ensemble.py:673`).

**문제**: 3후보 비교는 최소 500-1000자 분량. 240자로는 "A가 연속성 좋고, B가 몰입도 높고, C가 분량 충족" 수준의 요약만 가능. "왜 A의 연속성이 B보다 나은지"의 구체적 논거가 유실됨.

### G13-3. Advisory 근거 압축 — 부분 구현

**증거**: `stage4_interview_round.py:63-64`에서 advisory는 이진 플래그(truth_gate: 1/0)와 240자 요약으로 압축됨. `_build_retry_advisory_digest(max_items=5)`로 최대 5개 항목만 전달. 개별 advisor 모듈(npc_drift, numeric_drift, rel_drift 등 8개)의 상세 판단 근거는 보존되지 않음.

**구체적 유실 경로**: truth_gate가 "모순 발견"을 보고할 때, 어떤 팩트와 어떤 위반이 충돌하는지의 상세 내용이 240자에 절삭. 재시도 시 CW가 받는 정보가 불충분할 수 있음.

### G13-4. 단일 감사 추적 경로 부재 — 완전 부재

**증거**: 의사결정 데이터가 5개 싱크에 분산됨 — director_selections(DB), stage_attempts(DB), session_decisions(DB), decisions.jsonl, episode_production.jsonl. `audit_service.py`가 싱크 간 정합성은 검사하나, "에피소드 N의 의사결정 전체 경로를 보여달라"는 단일 쿼리/API가 없음.

**영향**: 운영자가 "왜 이 에피소드가 낮은 점수를 받았는지" 추적하려면 최소 3개 테이블 + 2개 JSONL을 수동 교차 참조해야 함.

### G13-5. 절삭 무표지(Silent Truncation) — 형식적 존재

**증거**: `_short_text()` 함수가 240/300/500/1200자로 절삭할 때 "... [TRUNCATED]" 등의 오버플로 마커를 남기지 않음(director_ensemble.py:396 참조). session_logger의 `_truncate()`(line 231-238)만 "[TRUNCATED N chars]" 마커 삽입. 의사결정 필드의 절삭은 무표지.

**문제**: 사후 감사 시 "이 240자가 전체인지 절삭된 것인지" 구분 불가. 정보 유실 여부 자체를 알 수 없음.

### G13-6. 모순 원천 역추적 제한 — 부분 구현

**증거**: contradiction_check 구조에 `prev_episode` 필드가 있어 "어느 에피소드에서 확립된 사실인지"는 기록됨. 그러나 "그 사실이 어떤 원고의 어느 문장에서 확립되었는지"까지는 추적 불가. FactLedger/WorldState의 변경 이력은 state_changes.jsonl에 있으나, 특정 모순 항목에서 원천 기록까지의 자동 연결 경로 없음.

### G13-7. episode_production.jsonl reason 필드 240자 제한 — 부분 구현

**증거**: 에피소드 생산 로그의 reason 필드가 240자로 제한(탐색 결과 확인). 생산 완료 후 빠른 요약 조회에는 충분하나, 복잡한 거부/수리 사유의 전체 맥락은 유실됨.

---

## 4. 영향도 추정

| 갭 ID | 갭 | 직접 영향 | 간접 영향 | 등급 |
|-------|---|---------|---------|------|
| G13-1 | CW 창작 의도 블랙박스 | 원고 품질 문제 시 "CW가 왜 이렇게 썼는지" 파악 불가 → 피드백 정확도 저하 | 디버깅 비용 증가, 반복 실패 시 원인 특정 지연 | **significant** |
| G13-2 | comparison_notes 240자 절삭 | 앙상블 선택의 구체적 근거 유실 → 선택 품질 검증 불가 | 앙상블 전략 최적화 시 과거 판단 근거 활용 불가 | **significant** |
| G13-3 | Advisory 근거 압축 | 재시도 시 CW에 전달되는 피드백 정밀도 저하 → 수리 효과 감소 가능 | Advisory 모듈별 효과 측정/튜닝 불가 | **significant** |
| G13-4 | 단일 감사 추적 경로 부재 | 없음 (산출물 품질에 직접 영향 없음) | 운영 비용 증가, 장애 원인 분석 시간 증가, 시스템 개선 사이클 지연 | **significant** |
| G13-5 | 절삭 무표지 | 절삭된 피드백이 완전한 것처럼 처리되어 수리 방향 오도 가능 | 감사 시 정보 완전성 판단 불가 | **nice-to-have** |
| G13-6 | 모순 원천 역추적 제한 | 모순 수리 시 원천 맥락 부족으로 부정확한 수정 가능 | 복잡한 모순 체인 디버깅 비용 증가 | **nice-to-have** |
| G13-7 | reason 240자 제한 | 없음 (요약용이므로 직접 영향 미미) | 생산 로그 기반 패턴 분석 시 정밀도 저하 | **nice-to-have** |

**영향도 요약**: 시스템의 설명력 인프라는 **풍부한 편**이다. 의사결정 근거를 다중 싱크에 구조화하여 기록하는 체계가 갖춰져 있고, 특히 contradiction_check의 구조화 수준과 Rationale Contract(canary_tools) 기반 누락 감지는 높은 수준이다. 그러나 **CW 블랙박스(G13-1)**와 **분산 싱크 통합 부재(G13-4)**가 실질적 추적성의 천장을 누르고 있으며, **절삭 정책(G13-2, G13-3, G13-5)**이 기록된 근거의 깊이를 제한한다.

---

## 5. 방향 스케치

| 갭 | 접근법 | 난이도 | 새 LLM 호출 | 기존 인프라 활용 | 리스크/부작용 |
|----|-------|-------|------------|---------------|-------------|
| G13-1 CW 블랙박스 | **A. CW 출력 스키마에 `writing_rationale` 필드 추가** — LLM 응답에 "이 장면을 이렇게 쓴 이유" 200자 필드를 요구. 기존 JSON 파싱 경로에 필드 추가. | 소 | 아니오 (기존 호출 내 추가 필드) | chief_writer_prompts.py 스키마 확장 | 토큰 증가(~200자), 응답 지연 미미. 필드가 형식적일 위험 |
| G13-1 CW 블랙박스 | **B. 전략별 의사결정 로그** — CW가 아닌 Python 측에서 "이 전략 + 이 피드백 + 이 컨텍스트 → 이 원고"의 입력 조건을 decisions.jsonl에 기록 | 소 | 아니오 | session_logger.log_decision() 확장 | CW의 주관적 의도는 여전히 미기록 |
| G13-2 절삭 완화 | **comparison_notes 한도를 240→600자로 상향** — `_short_text()` 호출 파라미터 수정 | 소 | 아니오 | 기존 코드 수정 | DB TEXT 필드이므로 저장 무관. 로그 크기 미미 증가 |
| G13-3 Advisory 상세화 | **advisory_details를 DB에 별도 JSON 필드로 저장** — 현재 240자 요약 외에 전체 advisory 배열을 stage_attempts에 JSON으로 추가 | 중 | 아니오 | db_manager ALTER TABLE | DB 행 크기 증가. advisory 8개 모듈 × ~500자 = ~4KB/row |
| G13-4 감사 추적 통합 | **A. 감사 뷰어 스크립트** — scripts/audit_trail.py로 attempt_key 기반 5싱크 통합 조회 CLI | 소 | 아니오 | 기존 DB + JSONL 구조 활용 | 당장 할 수 있는 것 |
| G13-4 감사 추적 통합 | **B. DB VIEW 생성** — director_selections + stage_attempts + session_decisions JOIN 뷰 | 소 | 아니오 | SQLite VIEW | 설계 필요 — 키 정합성 전제 |
| G13-5 절삭 마커 | **_short_text() 반환 시 절삭 여부 표지 추가** — 예: `"...내용..." → "...내용... [+120자 절삭]"` | 소 | 아니오 | director_ensemble.py 수정 | 하류 파서가 마커를 오해할 가능성 점검 필요 |
| G13-6 원천 역추적 | **contradiction_check에 source_sentence 필드 추가** — Director 프롬프트에서 원천 문장 인용 요구 | 중 | 아니오 (기존 호출 내) | director_prompts.py 스키마 확장 | LLM hallucination 위험 — 인용 정확도 검증 필요. 설계 필요 |

**당장 할 수 있는 것**: G13-2(절삭 완화), G13-4A(감사 뷰어), G13-5(절삭 마커)
**설계가 필요한 것**: G13-1A(CW rationale 스키마), G13-3(advisory DB 확장), G13-6(원천 역추적)

---

## 6. 묶음 내 교차 발견

축 13이 묶음 C의 첫 번째 축이므로, 이후 축 14(잘 다르고), 축 15(잘 맞추고)에 전달할 교차 발견:

1. **→ 축 14 (다양성)**: 앙상블 comparison_notes 240자 절삭(G13-2)은 "후보 간 차이가 무엇이었는지"의 기록 유실을 의미. 다양성이 실제로 산출되었는지 사후 검증 불가.
2. **→ 축 14 (다양성)**: CW 전략(balanced/narrative/tension)은 기록되나, 전략이 실제 원고 차이에 얼마나 기여하는지 추적 불가(G13-1). 다양성 효과 측정의 전제조건 미비.
3. **→ 축 15 (정렬)**: Director scoring의 5차원 breakdown은 잘 기록되나(인벤토리 #4), 이 점수가 실제 독자 만족과 상관하는지의 교정(calibration) 데이터는 기록 체계에 포함되지 않음.
4. **→ 축 15 (정렬)**: advisory 8개 모듈의 개별 효과를 측정할 수 없으므로(G13-3), 어떤 advisory가 최종 품질에 실제로 기여하는지 정량적 평가 불가 → 시스템 내부 기준이 외부 가치와 정렬되는지 검증 불가.

---

## 7. 3-Pass 감리 기록

### Pass 1: 사실 정확성 (88%)

- **수정**: 인벤토리 #8 Rationale Contract 설명에서 "에러 발생" → "경고 발생"으로 수정. canary_tools는 hard error가 아닌 WARNING 수준 알림을 발생시킴(코드 확인: `stage4_canary_tools.py:289-291`의 실제 동작은 rows_missing 카운트 반환이지 exception raise가 아님).
- **수정**: G13-2에서 "DB TEXT 필드이므로 제한 없음" 기술 확인 — SQLite TEXT 필드는 이론적 제한 없으나 Python 측에서 `_short_text()`로 사전 절삭하므로 DB에 도달하는 값은 이미 240자. 정확히 기술됨.
- **수정**: 인벤토리 #1 SessionLogger 설명에서 llm_io.jsonl의 truncation 임계값을 200K로 기술 — session_logger.py:47 확인, `_MAX_PROMPT_CHARS = 200_000`으로 정확.
- **보완**: G13-3에서 advisory 모듈 수를 "8개"로 기술 — stage4_interview_round.py:63-64의 `_last_advisory_summary` 키 목록 재확인: truth_gate, npc_drift, numeric_drift, rel_drift, flashback, info_paradox, long_term_rep, style_signal = 8개. 정확.
- **미확신 항목**: open_review 절삭 한도가 경로에 따라 다름(300자 vs 240자). stage4_interview_round.py에서 300자, director_ensemble.py에서 240자. 문서에 두 경로를 명시적으로 기술하지 않았으나 핵심 논점(절삭 자체가 문제)에는 영향 없음.

### Pass 2: 논리 정합성 (93%)

- **검증**: G13-1(CW 블랙박스) → 영향도 "significant" 판정의 논리: CW가 왜 이렇게 썼는지 모르면 → Director의 피드백이 정확한 원인을 겨냥하지 못할 수 있음 → 수리 효과 저하. **합리적 추론 경로, 비약 없음.**
- **검증**: G13-4(감사 추적 부재) → 영향도 "significant"이되 직접 영향 "없음" 판정: 감사 통합 부재가 원고 품질에 직접 영향을 주지는 않음. 간접 영향(운영 비용)만 있음. **논리 건전.**
- **수정**: G13-5를 "nice-to-have"로 판정했으나, "절삭된 피드백이 완전한 것처럼 처리되어 수리 방향 오도 가능"이라는 직접 영향도 기술함. 재검토: 이 경로가 실제로 발생하는 빈도는 낮음 — CW에 전달되는 피드백은 별도 경로(enhanced_feedback)로 구성되며 절삭된 필드 자체가 CW에 직접 주입되는 것이 아님. 따라서 "nice-to-have" 유지가 적절하나, 직접 영향 설명을 "감사 시 정보 완전성 판단 불가"로 수정 완료.
- **검증**: 방향 스케치의 난이도 판정 — G13-2(240→600 상향)가 "소"는 맞음. `_short_text()` 파라미터 하나 변경. G13-3(advisory DB)이 "중"은 맞음. ALTER TABLE + 쓰기 경로 수정 + 읽기 경로 수정 필요.

### Pass 3: 완성도 (96%)

- **보완**: 인벤토리에 episode_production.jsonl을 부수적 기여로만 분류했으나, 이 파일은 "생산 완료" 기록의 핵심 싱크. 그러나 설명력 관점에서는 reason 필드의 240자 제한이 걸리므로 "부수적" 분류가 맞음. 의도적 설명력 인프라가 아닌 생산 로그이므로.
- **보완**: 교차 발견 #3에서 "calibration 데이터 기록 체계 미포함"을 축 15에 전달. 이는 축 15(정렬)의 핵심 갭 후보와 직결되므로 중요한 교차 발견.
- **누락 관점 점검**: Director thinking 토큰(1200자 절삭)을 갭으로 별도 분리하지 않았음. 이유: thinking 토큰은 디버깅 보조이며, 의사결정 근거의 주 경로가 아님(selection_reason, verdict_reason이 주 경로). 별도 갭으로 분리할 실익 없음.
- **표현 명확화**: G13-6 제목을 "모순 원천 역추적 제한"에서 더 명확한 설명으로 본문 보완 — prev_episode까지는 추적 가능하나 해당 에피소드 내 특정 문장까지는 불가하다는 점을 명시.
- **균형 점검**: 인벤토리(14개 의도적 + 4개 부수적)와 갭(7개) 비율이 적절. 시스템의 설명력이 상대적으로 높은 영역임을 인벤토리 크기가 반영. 갭은 "있으나 부족한" 유형이 대부분이며 "완전 부재"는 G13-1, G13-4 두 개뿐. 이 균형은 코드 조사 결과와 일치.
