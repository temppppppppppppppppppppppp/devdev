# 끊긴 루프 전수조사 — 마스터 오더

> 작성: 2026-03-16
> 근거: freshrun 0_260316 TF에서 정합성만 검증, 효용성(신호 소비 여부) 미검증 → 구조적 문제 누락
> 범위: 전 스테이지 신호 × 소비자 전수조사
> 제약: **코드 수정 금지** — 조사 + 문서화만

---

## 1. 목적

시스템이 측정·생산하는 **모든 신호**에 대해:
- 소비자가 존재하는가?
- 소비자가 실제로 런타임에 영향을 미치는가?
- 정상 루프의 경계 조건은 안전한가?

---

## 2. TF 구성

| TF | 주제 | 신호 수 | 핵심 질문 |
|---|---|---|---|
| **A** | Stage 0 Dead Extraction | 7 | V2 필드가 왜 아무도 안 읽나? |
| **B** | Stage 0→Downstream Weak | 3 | anti_ai_patterns/dialogue_ratio/vocab이 왜 미강제? |
| **C** | Stage 3 Observational | 3 | coverage_warnings가 왜 retry에 안 들어가나? |
| **D** | Stage 4 Broken Feedback | 8 | ai_slop/npc_drift가 왜 CW에 안 돌아가나? |
| **E** | Cross-Cutting Sinks | 8 | cost_log/learnable/session이 왜 런타임에 안 쓰이나? |
| **F** | Working Loop Verify | 13+ | 정상 루프 경계 조건 점검 |

---

## 3. 산출물

| # | 파일명 | 상태 |
|---|---|---|
| 0 | `조사_broken_feedback_loop_audit_order.md` | ✅ |
| 1 | `조사_TF-A_stage0_dead_extraction_signals.md` | ✅ |
| 2 | `조사_TF-B_stage0_downstream_weak_links.md` | ✅ |
| 3 | `조사_TF-C_stage3_observational_signals.md` | ✅ |
| 4 | `조사_TF-D_stage4_broken_feedback.md` | ✅ |
| 5 | `조사_TF-E_cross_cutting_write_only_sinks.md` | ✅ |
| 6 | `조사_TF-F_working_loop_verification.md` | ✅ |
| 7 | `OPUS_broken_feedback_loop_3pass_audit.md` | ✅ |

---

## 4. 검증 방법론

- **Producer 라인**: 코드 직접 읽기로 확인
- **"소비자 없음" 주장**: Grep 전체 검색으로 확인 (전 .py 파일)
- **정상 루프**: producer→consumer 양방향 추적
- **3-pass 감리**: 전 TF 문서 교차 검증 후 final save

---

## 5. 핵심 파일 매핑

| 역할 | 파일 |
|---|---|
| S0 신호 생산 | `modules/core/stage0/style_extractor.py` |
| S4 컨텍스트 주입 | `modules/core/stage4_context_builder.py` |
| S4 품질 측정 | `modules/core/quality_signal_metrics.py` |
| S4 retry 루프 | `modules/core/stage4_interview_round.py` |
| S4 오케스트레이터 | `modules/core/stage4_orchestrator.py` |
| Director | `modules/domain/agents/director_ensemble.py` |
| 피드백 시스템 | `modules/core/feedback_system.py` |
| DPW | `modules/core/dynamic_prompt_weighting.py` |
| soft failure | `modules/core/soft_failure.py` |
| session logger | `modules/core/session_logger.py` |
| failure analyzer | `modules/core/failure_analyzer.py` |
| S3 오케스트레이터 | `modules/core/stage3_orchestrator.py` |
| style guard | `modules/core/genre_guards/style_guard.py` |

---

## 6. 실행 순서

1. ✅ 마스터 오더 작성 (#0)
2. ✅ TF-A — style_extractor.py V2 필드 7개 추적 (WEAK 7, LIVE 2)
3. ✅ TF-B — anti_ai_patterns/dialogue_ratio/vocabulary_level (ENFORCED 1, ADVISORY 1, DEAD 1)
4. ✅ TF-C — S3 observational 3건 (ADVISORY-ONLY 1, DEFERRED 2)
5. ✅ TF-D — ai_slop→CW 단절 등 (DEAD 6, ADVISORY 1, WEAK 1)
6. ✅ TF-E — cost_log/learnable/session logs (DEAD 2, WRITE-ONLY 4, LIVE 2)
7. ✅ TF-F — 정상 13건 (WORKING 10, FRAGILE 3)
8. ✅ 3-Pass 감리 통과 (사실 오류 0, 모순 0, 오분류 0)
