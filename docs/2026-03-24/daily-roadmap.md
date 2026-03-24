Date: 2026-03-23
Status: active (3-pass audited, planning memo)
Document Type: daily roadmap memo
Canonical Path: `docs/2026-03-23/daily-roadmap-2026-03-23.md`
Temp Mirror Path: none

## 금일 로드맵

병렬 8터미널 + 8축 딥다이브 전역 전수조사 준비 단계. 현재는 console-log 실행문서 진행 중이며, 완료 직후 Q1-Q8 현황 파악 wave로 전환한다.

이 문서는 `daily roadmap memo`이고, 실제 실행 오더는 별도 문서가 우선한다.
- Lane A canonical order:
  - `docs/2026-03-23/director-verdict-deep-dive-order.md`
- Lane B canonical order:
  - `docs/2026-03-23/generation-coherence-deep-dive-order.md`
- Lane D canonical order:
  - `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`

### 8축 프레임워크 — 디렉터 파이프라인 품질 모델

| # | 질문 | 축 | 핵심 지표 |
|---|---|---|---|
| Q1 | **"잘 쓰냐"** | 첫 생성 품질 | Director 피드백 없이 1회차에 PASS 되는 비율, 초안 점수 분포 |
| Q2 | **"잘 고치냐"** | fix/retry 품질 | PASS_WITH_FIX 성공률, inplace_patch 후 점수 상승폭, 재시도 횟수 대비 수렴 속도 |
| Q3 | **"잘 판단하냐"** | PASS/REJECT 정확도 | 오탐(불합격할 걸 통과), 누락(통과할 걸 불합격), gate_basis 분포, 판정 일관성 |
| Q4 | **"잘 설명하냐"** | 피드백 전달 품질 | reject reason -> retry instruction -> 다음 생성에서 해당 이슈 해결 비율, 피드백 루프 단절 지점 |
| Q5 | **"잘 기억하냐"** | 에피소드 간 일관성 | 장기 설정 모순 감지율, NPC 사망 후 재등장 차단율, WorldState/FactLedger 정합성 |
| Q6 | **"잘 찾냐"** | 선택적 검색 (SAM) | "어디에 있는지 안다 -> 필요할 때만 꺼낸다" 패턴. Store Routing 정확도, 불필요 검색 비율, VecMem/DB 히트율 |
| Q7 | **"잘 받냐"** | 컨텍스트 수신 품질 | 각 Stage 주요 LLM이 필요한 정보를 빠짐없이, 올바른 형태로 받는지. 프롬프트 주입 완전성, 토큰 예산 내 핵심 정보 우선순위, 잘림/누락/순서 뒤집힘 |
| Q8 | **"잘 로깅하냐"** | 콘솔/DB/Audit 관측성 | 왜 PASS/REJECT인지, 어떤 advisory/score mutation/fix 지시가 있었는지, 콘솔과 DB에 절삭 없이 남는지 |

논문 컬렉션: `docs/2026-03-20/sparse-attention-memory-applicability-to-tf.md` (168편)

축별 관련 논문 섹션:

| 축 | 1차 논문 카테고리 | 2차 참조 |
|---|---|---|
| Q1 잘 쓰냐 | A-1 장편 소설 생성, A-9 Controllable Generation, A-21 LLM Ensemble/Best-of-N | A-11 Narrative Pacing |
| Q2 잘 고치냐 | A-12 Self-Refinement / Iterative Revision | A-14 LLM-as-Judge |
| Q3 잘 판단하냐 | A-14 LLM-as-Judge for Creative Writing, A-8 평가/벤치마크 | A-6 할루시네이션 감지 |
| Q4 잘 설명하냐 | A-12 Self-Refinement (피드백 루프), A-4 MAS (에이전트 간 통신) | A-23 Agentic Workflow |
| Q5 잘 기억하냐 | A-2 서사 일관성/모순 감지, A-3 장기 메모리/에피소딕 메모리, A-10 Temporal Knowledge Graph | A-17 Plot Hole Detection, A-13 Persona/Character |
| Q6 잘 찾냐 (SAM) | **A-29 Memory Routing / Selective Retrieval** — "Did You Check the Right Pocket?" (2603.15658) | A-7 RAG/컨텍스트 엔지니어링, A-20 GraphRAG |
| Q7 잘 받냐 | A-15 Prompt Compression / Optimization, A-7 RAG/컨텍스트 엔지니어링 | A-5 Sparse Attention/KV Cache, A-24 API Cost Optimization |
| Q8 잘 로깅하냐 | A-8 평가/벤치마크, A-23 Agentic Workflow | 시스템 observability / audit sink / operator logging |

### Q7 "잘 받냐" 상세 — 컨텍스트 수신 품질

각 Stage의 주요 LLM 호출 시점에서 정보 수신 상태를 검증:

| Stage | 주요 LLM | 받아야 할 핵심 정보 | 검증 포인트 |
|---|---|---|---|
| Stage 2 | Analyst (`plan_single_arc`) | 이전 arc 요약, 팩트시트, 세계관, 장르 가드 | 프롬프트에 실제로 주입되는지, 토큰 예산 내 우선순위 |
| Stage 2 | Director (`audit_strategic_plan`) | arc 문서, 검증 결과, 이전 reject 피드백 | validation_context 필드가 빠짐없이 전달되는지 |
| Stage 3 | ThreePhaseBlueprint | constraint block, 이전 blueprint, 장르 가이드 | Phase 1 캐시 -> Phase 2 생성에 실제 반영되는지 |
| Stage 4 | ChiefWriter (`generate_ensemble`) | mandatory_context, blueprint, arc, prev_manuscripts | context budget 초과 시 어떤 정보가 먼저 잘리는지 |
| Stage 4 | Director (`select_and_judge_ensemble`) | 후보 원고들, 검증 결과, advisory, 이전 맥락 | director_input_pack 조립 시 누락되는 필드 |
| Stage 4 | Director (`audit_manuscript`) | 원고, arc, history, prev_full_text, HUD | expanded_prev 확장 후 토큰 한도 내 수용 여부 |

검증 관점:
- **주입 완전성**: 필요한 필드가 프롬프트에 실제로 들어가는지
- **우선순위**: 토큰 예산 초과 시 핵심 정보가 보존되고 부차 정보가 잘리는지
- **형태 정합성**: dict -> 프롬프트 문자열 변환 시 구조가 보존되는지
- **잘림 감지**: `_fit_prompt_text`, `smart_truncate` 등에서 의미 단위가 아닌 바이트 단위로 잘리는지
- **순서**: 컨텍스트 섹션 순서가 LLM의 attention 패턴에 유리한지

대상 파일:
- `stage4_context_builder.py`
- `stage4_context_packets.py`
- `chief_writer_context.py`
- `chief_writer_context_packets.py`
- `prompt_builder.py`
- `base_agent.py`

### Q8 "잘 로깅하냐" 상세 — 콘솔/DB/Audit 관측성

핵심 질문:
- 운영자가 콘솔만 보고도 `왜 PASS/REJECT인지`, `무슨 advisory가 나왔는지`, `점수가 왜 변했는지`, `어떤 fix 지시가 있었는지`를 복원할 수 있는가
- 같은 판단 근거가 DB, audit, metrics, console 사이에서 절삭 없이 일관되게 남는가
- `logging.info/debug`에만 있고 operator sink에는 안 나오는 정보가 있는가

검증 관점:
- **최대 표시**: decision-bearing 텍스트가 `[:80]`, `[:100]`, `[:200]` 등으로 잘리지 않는지
- **최대 저장**: DB `TEXT`인데 Python에서 잘라 저장하지 않는지
- **sink 정합성**: console / DB / audit / metrics가 같은 사건을 다른 이름/다른 길이로 기록하지 않는지
- **침묵 경로**: advisory, score mutation, adaptive verdict branch, failure category가 operator surface에서 빠지지 않는지

대상 파일:
- `director_ensemble.py`
- `stage4_interview_round.py`
- `stage4_director_runtime.py`
- `stage2_finalizer.py`
- `stage3_orchestrator.py`
- `db_manager.py`
- `logger.py`
- `pass_rate_monitor.py`
- `metrics_collector.py`

### Lane A. 디렉터 판정 딥다이브 (Q2 + Q3 + Q4 + Q7-Director)

Canonical order:
- `docs/2026-03-23/director-verdict-deep-dive-order.md`

포함 축:
- Q2 "잘 고치냐"
- Q3 "잘 판단하냐"
- Q4 "잘 설명하냐"
- Q7 "잘 받냐" 중 Director-side context reception

핵심 대상:
- `stage4_director_runtime.py`
- `director_ensemble.py`
- `director_auditor.py`
- `stage4_interview_round.py`
- `stage4_retry_runtime.py`
- `stage4_reject_runtime.py`
- `four_phase_arc_runtime.py`

### Lane B. 생성-정합성 딥다이브 (Q1 + Q5 + Q6 + Q7-Generator)

Canonical order:
- `docs/2026-03-23/generation-coherence-deep-dive-order.md`

포함 축:
- Q1 "잘 쓰냐"
- Q5 "잘 기억하냐"
- Q6 "잘 찾냐"
- Q7 "잘 받냐" 중 Generator-side context reception

핵심 대상:
- `chief_writer.py`
- `arc_ensemble.py`
- `blueprint_ensemble.py`
- `chief_writer_context_packets.py`
- `world_state.py`
- `fact_ledger.py`
- `continuity_arc.py`
- `continuity_validator.py`
- `state_tracker.py`
- `vec_memory.py`
- `stage4_context_builder.py`
- `stage4_context_packets.py`
- `context_advisor.py`

### Lane C. Fresh Run ("돌아가냐")

- Stage 0 -> 2 -> 3 -> 4 최소 경로 실행
- 백그라운드 2시간
- 터지면 traceback 수집, 안 터지면 콘솔/DB/메트릭스 캡처
- 주말 감사 unresolved 3건 실측 검증
  - Stage 3 REJECT 싱크
  - Stage 4 bible_delta
- `_god1_*`
- **7축 전체에 대한 라이브 데이터 수집 가능 여부 판단**

### Lane D. 전역 전수조사 sidecar (Opus 수집 -> Codex 감리)

Canonical order:
- `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md`

역할 분리:
- Opus는 전역 heatmap, hotspot, quick win, no-action zone을 수집한다
- Codex는 결과를 merge-audit하고 stale claim을 제거한다
- action-bearing finding만 execution SSOT 또는 bounded fix order로 materialize한다

포함 축:
- Navigation
- Authority
- Contract
- Observability
- Local Readability

핵심 대상:
- `main_a.py`
- `modules/core/**/*.py`
- `modules/domain/agents/**/*.py`
- `modules/validation/**/*.py`
- `modules/api/**/*.py`
- `docs/2026-03-23/llm-codebase-orientation-pack.md`

### Lane E. Post-Console Q1-Q8 Parallel Deep Survey

Canonical order:
- `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md`

핵심 운영 원칙:
- 시작 시점: `console-log-max-display-post-audit-execution-ssot` realization + closure audit 이후
- 터미널: 8개
- 각 터미널: Opus TF 1개
- 산출물: Q1~Q8 축별 deep-dive report 8개 + optional evidence manifest + Codex merge-audit 후 execution SSOT 승격
- 현재 fresh run은 이미 1회 수행했으나 `LLM-Director 정합성 불일치`로 실패했으므로, 다음 live rerun은 survey -> code fix 이후로 미룬다

## 실행 순서

1. 현재 dirty 커밋
2. C 백그라운드 시작 (사용자 조작)
3. A + B + D 병렬 조사 (Opus)
   - A/B는 **8축 프레임워크** 기반 딥다이브
   - D는 전역 LLM 친화도 / owner / contract / observability survey
4. C 결과 수집 -> **8축별** 라이브 증거 머지
5. Codex merge-audit
   - A/B/D finding stale 여부 판정
   - live evidence 우선 재분류
   - action-bearing finding만 execution SSOT로 승격
6. **8축 종합 보고서 + 전역 전수조사 후속 큐** 정리

## 산출물 계획

| 산출물 | 경로 | 내용 |
|---|---|---|
| 8축 딥다이브 보고서 | `docs/2026-03-23/director-pipeline-7axis-deep-dive.md` | 기존 Q1~Q7 기반 보고서. 다음 wave는 Q8까지 확장 |
| Lane A 오더 | `docs/2026-03-23/director-verdict-deep-dive-order.md` | Q2+Q3+Q4+Q7-Director 조사 오더 |
| Lane B 오더 | `docs/2026-03-23/generation-coherence-deep-dive-order.md` | Q1+Q5+Q6+Q7-Generator 조사 오더 |
| Lane D 오더 | `docs/2026-03-23/opus-llm-friendliness-global-survey-order.md` | 전역 전수조사 Opus 수집 오더 |
| Lane E 오더 | `docs/2026-03-23/q1-q8-current-state-parallel-deep-survey-order.md` | Q1~Q8 병렬 8터미널 전수조사 오더 |
| 전역 전수조사 보고서 | `docs/2026-03-23/opus-llm-friendliness-global-survey-report.md` | heatmap + hotspot + quick win + no-action zone |
| Fresh run 로그 | 사용자 캡처 | 콘솔/DB/메트릭스 |
| 후속 실행 큐 | `docs/YYYY-MM-DD/*execution-ssot.md` | Codex merge-audit 후 action-bearing finding만 생성 |

## 선행 조건

- post-audit 3트랜치 이미 반영됨
- 주말 감사 96% 신뢰도 확보
- LLM 친화도 서베이 88% 확보
- 180+ 밴드 = 0 (장함수 캠페인 완료)
- fresh run 1회 완료, 다만 `LLM-Director 정합성 불일치`로 rerun ROI가 높아짐
- current focus: `console-log-max-display-post-audit-execution-ssot` closure -> Q1-Q8 parallel survey -> code fixes -> fresh run retry

## 3-Pass Audit Record
- Pass 1
  - 문서 타입을 `daily roadmap memo`로 유지하고, 실행 지배 문서는 별도 lane order가 우선임을 명시했다
- Pass 2
  - `7축`과 `6축` 혼선을 제거하고, 이번 갱신에서 `Q8 잘 로깅하냐`를 추가해 `8축`으로 확장했다
- Pass 3
  - Lane E `Q1-Q8` 병렬 전수조사 계획과 `Opus 수집 -> Codex 감리/실행문서화` 책임 분리를 명시했다

## Confidence
- Confidence: 98%
- Basis:
  - 현재 live workspace와 충돌하지 않는 planning memo 범위로 제한됨
  - lane execution authority를 별도 order docs로 분리해 roadmap 과적재를 피함
