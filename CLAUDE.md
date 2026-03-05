# 글도비 — 후임 에이전트 인수인계

> AI 웹소설 자동 생성 시스템. Python + Gemini API.
> 상세 참고: `참고자료.md` (2000줄+ 종합 자료)
> 검토 문서: `docs/2026-03-04/명세-행동 정합성 감사.md`, `docs/2026-03-04/stage3-blueprint-logic-error-analysis.md`

---

## ⚖️ 대원칙 (절대 위반 금지)

1. **Python은 수집만, 판단은 LLM이** — Python은 데이터 수집·포맷팅·전달만. "오류인가?", "수정할까?" 같은 판단은 LLM 에이전트가 담당.
2. **팩트시트 수정 권한은 LLM만** — NPC 속성, 세계관 설정, 관계도를 수정하는 건 LLM뿐. Python이 자동으로 팩트를 덮어쓰면 안 됨.
3. **디렉터 주권주의 (내각제)** — Director가 최종 품질 결정권. Chief Writer·Analyst 등은 초안 제출만, 합격/불합격/수정 지시는 Director가 내림. Director를 우회하면 안 됨.
4. **사망 캐릭터는 회상/언급만 허용** — `deceased=True` NPC가 행동/대사로 등장하면 REJECT. 회상·과거 장면·타인 언급은 허용.

---

## 파이프라인

```
Stage 0 (초기 설정)  →  Stage 2 (Arc/Blueprint)  →  Stage 4 (원고)
세계관 바이블 추출       Analyst → Arc → Blueprint     Chief Writer → Director 심사
NPC 등록                앙상블 + 검증 체인              합격/불합 → 재작성 루프
문체 분석                연속성 검사                    카카오/네이버 포맷 출력
```

---

## 현재 상태 (2026-03-05)

- **작동함**: Stage 0→2→4 정상 동작 (투자물 장르 실파이프라인 검증 완료)
- **완료된 것**: Phase 1~2, 5-A/5-B/5-C, 6-A/6-B/6-C, 4C(DI), 4D(sqlite-vec), 3-5B(패치), 3-5A(NPC이력), **4-R1~R3(몬스터 분할)**, R4-a(NO-GO), **3-QR(품질 회귀 감지)**, **3-5C(NPC 과잉 경고)**, **3-Obs Step 1+2(관측성 계측)**, **3-B(크로스 에피소드 반복 감지)**, **D.대리만족 전체 완료(Step1~5)**, **A-1(writer 유틸 해체)**, **A-3(test xfail)**, **C-1(PlotGuard 폴백)**, **C-2(NPC 체인)**, **C-3(Validator 체인)**, **B-1 전체 완료(stage4 -64%, chief_writer -62%, stage2 -66%)**, **E-2(Ruff 0 violations)**, **A-2(optimizer TODO)**, **R5(2차 분할 전량)**, **WorkGuard(작품별 YAML)**, **Debug Sweep 1차~12차 전량 완료**, **B-3(Protocol 전면 표준화)**, **DB-SSOT(VecMemory merge)**, **Patch Mode(Stage 2/3)**, **Passrate 전략 배선**, **Ensemble Feedback**, **Ops Quality 6대 개선**, **Opus TF 전면 재감사+T1/T2 수정**, **SC-0~6(Smart Context Retrieval) + Post-Audit**, **TF-5 전체 시스템 디버깅 감사 32건 패치**, **TF-6 롤백 원자성·상태 누적·트랜잭션 등 16건 패치**, **TF-7 전체 감사(A~N) + P0/P1/P2 24건 패치**, **TF-7R 1차/3차/6차 17건 + 7차 카오스 테스트 38개**, **PBT(hypothesis) 46개**, **E2E 통합 wiring 16개**, **아키텍처 부채 감사(silent except·DI주석·dead var)**, **Memory ROI P0-1~P0-4(검색품질 4건)**, **D1 Hybrid Retrieval(FTS5+RRF)**, **DB 효율화(chroma_db삭제·file→DB·인덱스보강)**, **D2 Memory Observability(경로별 계측)**, **문서정리(docs 445→70개)**, **E2E Smoke Tests(파이프라인 통합 33개)**, **TF-10~15 전면 감사+P0 패치**, **TF-16(P1 백로그 3건)**, **TF-17(Truth Gate 메모리 오염 방지)**, **TF-18(Hybrid 검색 활성화)**, **TF-19(Memory Benchmark 17개)**, **Opus TF 전수조사(P0 7+P1 17건 패치)**, **2차 전수조사(P0 10건 + P1 34건 전량 패치)**, **3차 전수조사(P0 19+P1 17+P2 2건 패치)**, **4차 전수조사(동시성·복구·계약·설정·크로스컷 51건 — P0 10+P1 18+dead code 1744줄 삭제)**, **메타감리(1~4차 130+패치 검증 — 오작업 0건, 테스트 복원 17개)**, **5차 전수조사(에러전파·입력검증·리소스·LLM파싱·상태일관성 — P0 7+P1 12건 패치)**, **1~3차 재감사(7TF 병렬 — P0 1+P1 11건 패치, 감리 12/12 CORRECT)**, **extended_block_guide(treatment 확장 필드 → Arc LLM generic serialization)**, **Treatment 반응 다양화(골든루트 60블록 — Intensity·캐릭터아크·power_shift 전량)**, **Bible 동기화(골든루트 — 이름 충돌 3건 통일·NPC 2건 추가)**, **TF-20(정확도 우선 5건 — ContinuityInspector 예외→retry·memorize 반환값 체크·NPC LLM fail-closed·Manager audit_event·save_episode_bible→False)**, **LM-A(world_laws 자동등록+TruthGate 7번째 검사+CRITICAL 핀 보호)**, **LM-B(NpcDriftAdvisor — NPC 속성 텍스트 레벨 표류 LLM advisory)**, **LM-C(NumericDriftAdvisor — FactLedger 수치 누적 표류 LLM advisory)**, **LM-D(RelationshipDriftAdvisor — NPC 관계도 장기 표류 LLM advisory)**, **LM-E(FlashbackVerifier — 회상/플래시백 오염 감지 LLM advisory)**, **LM-F(InfoParadoxChecker — 1인칭 시점 정보 역설 LLM advisory)**, **LM-G(NarrativeContextFormatter — 서사 구조 컨텍스트 enrichment)**, **TF-27~32(PASS_WITH_FIX verdict 도입 + S2/S3 소비자 코드 패치)**, **TF-32-VERIFY(PASS_WITH_FIX → patch + Director 재심사 반복 최대3회)**, **TF-33(fix_scope 기반 3-tier 수정 라우팅 — inplace/partial/full)**, **TF-34(Validator PASS_WITH_FIX 피드백 보존 + compare 경로 fix_scope 전파)**, **TF-45(비무협 무협 오염 근절 7건 — 동적 에너지 블록+스키마+플레이스홀더+후처리)**, **TF-46(합격률 개선 — QualityGate 적응형 + 컨텍스트 보강 + InPlace state_updates)**, **TF-47(InPlace 원고 전체 삭제 버그 수정 — JSON 파싱 1단계 + rfind 보호)**, **TF-48(Arc 간 실행 상태 연속성 — DB 실행 결과 우선 주입)**, **B-1-3b(stage4_interview_round.run() 2차 분할 — 1,647→686줄, -58%)**, **LM-I(npc_history known_attrs 4필드 동기화)**, **E-1(PatchModeThresholds.PATCH dead code 제거)**, **LM-H(FlashbackVerifier 원고 원문 대조 강화)**, **A-4(공통 실패 패턴 감지 — contradiction_types 수렴 + Arc 구조 진단 advisory)**, **NumericDrift 한도 보강(MAX_ITEMS 30, MAX_HISTORY_POINTS 20)**, **A-2(open_review Director→CW 전달)**, **A-3(fix_scope DB 추적 — director_selections)**, **B-4(동기/약속 방치 감지 — CW self-critique 5번째 체크)**, **TF-25-01(director_ensemble IndexError 방어)**, **TF-25 전수 확인(01~09 — SSOT 통합 + 7건 기존 완료 확인)**, **TF-26(종합 감사 — Director SSOT + dead code 2파일 삭제 + 로깅 강화 9건 + 타임아웃 YAML 외부화)**, **B-1-9(거대 함수 2차 분할 — process_pass_result -71%, run_validation -83%, ask -57%)**, **LM-Tier(장기 기억+품질 강화 6건 — TF-A~F)**, **TF-54(WritingDirective — PatternTracker+지시생성+CW주입+Director정합+self-critique 6·7·8번째 체크)**, **TF-55b(VecMemory hits=0 슬롯 → STATIC/DB_NPC_RELATIONSHIP 직접 주입)**, **Model SSOT(models.yaml 단일 참조 — constants.py _load_model_from_yaml + config_manager 동적 로드)**, **합격률 개선(ending_hook 의무화 규칙12·13 + self-critique 8번째 체크 + blueprint 주입)**, **실파이프라인 검증(TF-54/55b/합격률 wiring 통합 테스트 8개)**, **6차 전수조사(신규 코드 전수 감사 P1 3건 — config_manager/reference_anchor/confidence_calibration SSOT)**, **V73(자본금 역동기화 2중 방어 — Director state_updates 우선 + 대사 제거 regex)**, **7차 전수조사(P2 SSOT 주석 7파일 + LM-B/C/P1-5 except Exception 보강)**, **LM-post-1(Retrospective lookback 5→10 YAML 외부화 + causal_graph Read 연결 + Director MC 보조 주입)**, **8차 전수조사(LM-E/F/D except Exception 보강 — advisory 비치명 완결)**, **God Object 해체 1~3차(run() 782→404줄 + _attach_agents() 570→137줄 + _process_verdict() 320→114줄, 신규 메서드 +7개)**, **로깅 강화(llm_calls+stage_attempts DB 테이블 + BaseAgent 계측 + FailureAnalyzer — 실패 학습 기반 진단 시스템)**, **Log-Phase2(실패 스니펫 저장 prompt_snippet/response_snippet + Stage2 duration_ms/failure_category/advisory_flags 보강 + Stage3 attempt_num 동적화/arc_num 복원/reject_reason 상세화)**, **S3-META(quality_risk Blueprint → Director advisory 주입 + V75-D 1연속 조기 트리거)**, **감사문서 패치(F-1 YAML주석 교정·F-2 diff ratio S2/S3/S4 3곳·F-3 fix_scope required 스키마)**, **NC-1(수치 정합성 Python 검증 5개 검사 + 단일 후보 독점 방지 SCM)**, **NC-2(실파이프라인 11대 이슈 잔여 갭 6건 해소 — 퍼센트구성+동명이인+도입부유사도+씬유사도+공간연속성+시간경과)**, **NC-3(Director 일관성 체크리스트 10개 카테고리 — consistency_checklist 스키마+프롬프트+파싱+점수보정)**, **NC-3B(Few-Shot Golden Example + score_breakdown 합산 Self-Consistency Check)**, **TF-LLM P0(TF-D Advisory 시각화 + TF-E CW 톤 조절 — TF-A 중복제거 NO-OP 재분류)**, **NS-3(treatment block 수치 목표 self-critic 주입 — NS-3-A fallback critic_input 주입 + NS-3-B FourPhase Phase 2.55 Python 교차검증)**, **TF-G(Self-Critique 게이트 검사 — ending_hook+분량 루프 전 사전 수정)**, **TF-I(피드백 전달 경로 명확화 — common_writer_kwargs에 director_feedback 추가)**, **TF-C(스키마-프롬프트-규칙 3중 정합 — NC-1/NC-3 자동감점 제거, Director 주권 존중)**
- **현재 단계**: 코드 개선 전량 완료. 실파이프라인 실행 + 실전 데이터 수집 단계.
- **테스트 기준선**: **3,390 passed + 0 xfailed** (last verified 2026-03-05, `pytest tests/ -q`)
- **Ruff**: 0 violations, Silent Pass YELLOW 0건 (E-1+E-2 완료)
- **stage4 orchestrator**: 2,481→883줄 (**-64%**, 분할 완료, 서브모듈 3개)
- **chief_writer**: 2,255→854줄 (**-62%**, 분할 완료, 서브모듈 2개)
- **stage2 orchestrator**: 2,639→907줄 (**-66%**, B-1-8 완료, 서브모듈 3개)
- **stage4_interview_round**: run() 782→404줄, _process_verdict() 320→114줄, _attach_agents() 570→137줄 (God-1~3, 신규 메서드 +7개)
- **DI 전환**: Stage2(44슬롯) + Stage3(19슬롯) + Stage4(24슬롯) 전량 완료
- **checkpoint**: `02b458a`
- **향후 계획 문서**: `docs/2026-02-27/LM-enhancement-implementation-spec.md` — L1~L7 **전량 구현 완료** (LM-A~I). 잔여 항목 없음.
- **폐기/NO-GO 확정 (2026-03-04 재검사)**:
  - ~~causal_graph Read 연결~~ → **LM-post-1에서 완료됨** (get_recent_causal_links + Director MC 주입, 테스트 8개)
  - ~~FTS5 한국어 형태소 분리~~ → **후순위 유지, ROI 낮음** (Python re.split이 97% 처리, 조사 분리만 약점이나 OR 5키워드로 recall 충분)
  - ~~동적 장르 확장~~ → **폐기** (16~20개 하드코딩 위치 + Guard/HUDManager 클래스 신규 필요, 템플릿 복제 방식이 10개 장르로 검증 완료)
  - ~~캐시 최적화~~ → **NO-GO 재확인** (6사이트 ~11 HIT/에피소드 전량 커버, P1 ROI 부족, P2 프롬프트 7-13KB < 50K 임계값 미달, Gemini API 임계값 하향 전까지 추가 불가)

---

## 핵심 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `modules/core/stage2_orchestrator.py` | Arc 오케스트레이터 | B-1-6~8 분리 후 907줄, 서브모듈 3개 위임 |
| `modules/core/stage2_validation_pipeline.py` | Stage2 검증 파이프라인 | B-1-6 분리, B-1-9b 2차 분할 (run_validation 693→120줄 -83%, 4개 private 메서드) |
| `modules/core/stage2_finalizer.py` | Stage2 Finalizer | B-1-7 분리 (535줄), V64 위임 패턴 |
| `modules/core/stage2_preflight.py` | Stage2 Preflight 분석 | B-1-8 분리 (637줄), V64 위임 패턴 |
| `modules/core/stage3_orchestrator.py` | Blueprint 오케스트레이터 | DI 전환 완료 (19슬롯, lazy init만 self.app) |
| `modules/core/stage4_orchestrator.py` | 원고 오케스트레이터 | B-1-1~3 분리 후 883줄, 서브모듈 3개 위임 |
| `modules/core/stage4_post_processor.py` | Stage4 PASS 후처리 | B-1-1 분리, B-1-9a 2차 분할 (process_pass_result 813→238줄 -71%, 5개 private 메서드) |
| `modules/core/stage4_context_builder.py` | Stage4 컨텍스트 빌더 | B-1-2 분리 (570줄), V64 위임 패턴 |
| `modules/core/stage4_interview_round.py` | Stage4 인터뷰 라운드 | B-1-3b 2차 분할 (run 686줄, 메서드 12개), 5개 private 메서드 추출 |
| `modules/domain/agents/chief_writer_context.py` | CW 컨텍스트 빌더 | B-1-4 분리 (1,074줄), V64 위임 패턴 |
| `modules/domain/agents/chief_writer_quality.py` | CW 품질 게이트 | B-1-5 분리 (465줄), V64 위임 패턴 |
| `modules/core/failure_analyzer.py` | 실패 패턴 사후 분석 유틸리티 | 로깅 강화, FailureAnalyzer(db).summary() / advisory_reject_correlation() / model_performance() 등 11개 메서드 |
| `modules/core/numeric_consistency_checker.py` | Python-only 수치 정합성 검사 | NC-1, 5개 검사 (FactLedger 교차/산술/직함/이벤트순서), LLM 0회 advisory |
| `modules/core/truth_gate.py` | 메모리 오염 방지 advisory 검증기 | TF-17+LM-A, 7개 검사 (사망NPC/아이템/장소/스킬/카르마/NPC역할/세계법칙) |
| `modules/core/npc_drift_advisor.py` | NPC 속성 텍스트 레벨 표류 LLM advisory | LM-B, 원고 vs 스냅샷 대조 |
| `modules/core/numeric_drift_advisor.py` | FactLedger 수치 누적 표류 LLM advisory | LM-C, 5화 단위 이력 검사 |
| `modules/core/relationship_drift_advisor.py` | NPC 관계도 장기 표류 LLM advisory | LM-D, npc_relationship_history 이력 |
| `modules/core/flashback_verifier.py` | 회상/플래시백 오염 감지 LLM advisory | LM-E, 14개 마커 + VecMemory 참조 |
| `modules/core/info_paradox_checker.py` | 1인칭 시점 정보 역설 LLM advisory | LM-F, episode_bibles 지식 누적 |
| `modules/core/narrative_context_formatter.py` | 서사 구조 컨텍스트 포맷터 | LM-G, Stage2 enrichment (LLM/DB 없음) |
| `modules/core/long_term_repetition_advisor.py` | 장기 반복 패턴 감지 LLM advisory | P1-5, 20화+ 윈도우 씬 패턴 분석 |
| `modules/core/genre_schema_builder.py` | 장르별 프롬프트 스키마 자동 생성 | TF-45, 비무협 동적 스키마 (순수 Python, LLM/DB 없음) |
| `modules/core/pattern_tracker.py` | 직전 N화 표현·은유·결말 패턴 추적 | TF-54a, LLM 0회, `build_report()` → PatternReport |
| `modules/core/writing_directive_generator.py` | PatternReport → WritingDirective 생성 | TF-54b, Flash 1회, JSON 파싱 폴백 완비 |
| `modules/core/context_advisor.py` | Smart Context Retrieval 플래너 | SC-1~6, RetrievalPlan/Slot/Sources, STATIC·DB_NPC_RELATIONSHIP(TF-55b) |
| `modules/core/db_manager.py` | SQLite DB 매니저 | 모범 패턴 |
| `modules/core/prompt_loader.py` | YAML 프롬프트 로더 (싱글톤) | |
| `config/prompts/*.yaml` | 외부화된 프롬프트 43개 | |
| `modules/domain/agents/base_agent.py` | AI 에이전트 베이스 클래스 | B-1-9c ask() 분할 (4개 private 메서드), Context Caching |
| `modules/domain/agents/*.py` | AI 에이전트 20+개 | |
| `modules/core/genre_guards/*.py` | 장르 가드 10종 + WorkGuard + StyleGuard | Guard 체인: Genre→Work→Style |
| `modules/core/genre_guards/alt_history_guard.py` | 대체역사 Guard | 실제 역사 오류·미래기술 금지 |
| `modules/core/genre_guards/composer_guard.py` | 음악/작곡 Guard | 음악 용어·악기 일관성 |
| `modules/core/genre_guards/medical_guard.py` | 의료 Guard | 의학 용어·시술 정합성 |
| `modules/core/genre_guards/sports_guard.py` | 스포츠 Guard | 종목별 규칙·경기 진행 |
| `modules/core/genre_guards/actor_guard.py` | 연예/배우 Guard | 업계 용어·오디션 절차 |
| `modules/core/genre_guards/cooking_guard.py` | 요리 Guard | 조리법·식재료 일관성 |
| `modules/validation/*.py` | 검증 파이프라인 | |
| `config/settings/validation.yaml` | 검증 임계값 설정 | Phase 5-B |
| `modules/validation/threshold_helper.py` | 공유 `_threshold()` 헬퍼 | Phase 5-B-2c |
| `modules/core/writer_prompt_builders.py` | Writer 유틸 독립 모듈 | A-1 분리 |
| `modules/core/semantic_plot_guard.py` | 플롯 중복 감지 (임베딩+키워드 폴백) | C-1 개선 |
| `modules/core/stage2_context.py` | Stage2 DI 컨텍스트 (43슬롯) | Phase 4C-3 |
| `modules/core/stage3_context.py` | Stage3 DI 컨텍스트 (19슬롯) | Phase E-1a |
| `modules/core/stage4_context.py` | Stage4 DI 컨텍스트 (24슬롯) | Phase 4C-2 |

---

## ⚠️ 주의

- **LLM 모델 설정 SSOT 완료** — `models.yaml` 단일 참조 달성. `constants.py`의 `_load_model_from_yaml()` import-time 로드 + `AIModels` 16개 attr 전량 yaml 참조. `config_manager.py` `_load_agents_from_yaml()` 동적 로드. `state_locked_arc_generator`/`narrative_structure_analyzer`/`self_reflection`/`tree_of_thoughts` default 인자 `AIModels.*` 교체 완료. **P2 유보(호출자 명시 주입)**: `adversarial_self_play`/`chain_of_verification`/`cross_agent_verifier`/`multi_agent_deliberation`/`arc_corrector`/`arc_critic`/`arc_ensemble` 7개 파일 — 운영 경로(`main_a.py`)에서 model 명시 주입하므로 현상 유지. `base_agent.py:47` fallback_chain 키·`metrics_collector.py` 가격표는 변경 불필요.
- `writer.py` — 유틸 3개는 `writer_prompt_builders.py`로 분리 완료 (A-1). `write_v20_manuscript` API만 유지 (오케스트레이터에서 호출 제거됨, 외부 진입점용).
- `memory_engine.py` — **삭제됨** (Phase 4D 완료). VecMemory(`vec_memory.py`)가 DBManager 커넥션을 공유 (DB-MERGE). `project_data.db` 단일 파일이 SSOT.
- NPC 속성 변경 — `npc_history` 테이블로 append-only 이력 기록 (Phase 3-5A 완료). `bind_db()` 호출 시 활성화.
- `base_agent.py`의 Context Caching — 구현 완료 (`_get_or_create_context_cache` L920, `_ask_with_cached_context` L1003). `chief_writer`·`director_continuity`에서 사용 중.
- NPC 관계 변경 이력 — `npc_relationship_history` 테이블 (append-only, sorted key). `upsert_npc_relationship_edge()` 호출 시 변경분 자동 기록. `reset_after()` 롤백 포함 (LM-D).
- NPC 변경 이력 reason — `npc_history` 테이블에 `reason` 컬럼 추가 (TF-D). `insert_npc_change(reason="...")` 전달.
- HUD Anomaly 파이프라인 — `manuscripts` 테이블에 `hud_snapshot` 컬럼 활성화 (TF-E). `save_manuscript(hud_snapshot=dict)` → `get_manuscript()["hud_snapshot"]` dict 반환. `_check_hud_anomalies()` 실제 데이터 수신.
- NumericDrift 지수 성장 — Python 사전 감지 (TF-B): `_detect_exponential_growth()` (100배+ 급등, 5연속 50%+ 성장). LLM 경로 유지, pre_warnings를 history_text에 prepend.
- fix_scope Director 주입 — `get_fix_scope_stats()` 결과를 Director mc_parts에 주입 (TF-C). 기존 win_rates 블록 직후.
- 누적 경과 시간 — WorldState `cumulative_elapsed` 필드 (TF-F). `_parse_elapsed_days()` 한국어 시간 파서. `NarrativeContextFormatter.format_cumulative_time()` → Stage2 advisory 주입.
- Stage4 advisory 체인 — TruthGate(LM-A) → NpcDriftAdvisor(LM-B, 4필드 확장) → NumericDriftAdvisor(LM-C, MAX_ITEMS=30/MAX_HISTORY_POINTS=20) → FlashbackVerifier(LM-E, 원문 대조 LM-H) → InfoParadoxChecker(LM-F, 1인칭 전용) → RelationshipDriftAdvisor(LM-D) → LongTermRepetitionAdvisor(P1-5, 20화+ 전용) → **NumericConsistencyChecker(NC-1/NC-2, Python-only, LLM 0회, 8개 검사)** → **SceneSimilarity(NC-2, Python-only)** → **Timeline(NC-2, cumulative_elapsed)**. 전부 `_director_mc_parts`에 주입, Director 최종 판정.
- NC-1/NC-2 NumericConsistencyChecker — 매화 Python-only advisory, **8개 검사**: ①FactLedger 교차(5% 허용 오차) ②산술 일관성(A+B=C, 레버리지) ③직함 변경 감지(승진 허용, 무단 변경 경고) ④"처음" 이벤트 모순 ⑤숫자 추출(대사 제거) ⑥퍼센트 구성 검증(유지율/담보비율 역산, 2%p 허용) ⑦NPC 동명이인 감지(WorldState 교차) ⑧도입부 유사도(3-gram 자카드 40% 임계값). LLM 0회.
- NC-2 씬 유사도 advisory — `stage4_context_builder._collect_recent_scene_keywords()`로 직전 3화 씬 키워드 수집 → `compute_scene_similarity_advisory()`로 50% 자카드 임계값 초과 씬 2쌍+ → `[SceneSimilarity]` advisory Director MC 주입. Python-only, LLM 0회.
- NC-2 공간 연속성/시간 경과 — `director.yaml` ENSEMBLE_STABLE_CONTEXT + AUDIT 프롬프트에 공간 이동 묘사·전환 표지 체크 + `[Timeline]` 시간 경과 정보 심사 기준 추가. `stage4_interview_round`에서 `cumulative_elapsed` → `NarrativeContextFormatter.format_cumulative_time()` → Director MC 주입.
- NC-1 응답 **선택사항** (TF-C) — `numeric_consistency_review` 필드는 **선택사항**으로 변경. AGREE/DISMISS 판정 가능하나 자동감점 없음. Director가 직접 continuity_contradiction 점수에 반영 여부 결정. 미응답 시에도 감점 없음. **대원칙 3(Director 주권주의) 준수**.
- TF-G Self-Critique 게이트 검사 — `apply_self_critique()` 루프 진입 전 ending_hook 누락 + 분량 부족(< 5,000자) 사전 검사. 해당 시 `_fix_manuscript_issues(severity="high")` 호출. severity="low" 탈출 방지.
- TF-I 피드백 전달 경로 — `_weighted_injection` 적용 후 `_common_writer_kwargs["director_feedback"]` 설정. `_generate_candidates` 내부 `**_common_writer_kwargs` 전개 시 명시적 `director_feedback=` 중복 제거.
- NC-3 일관성 체크리스트 (TF-C: **권장**으로 변경) — Director JSON 응답에 `consistency_checklist` 필드 추가. 11개 카테고리를 OK/ISSUE로 체크. ISSUE 3건+ → python_warnings 상한 3점. **체크리스트 미작성 시 감점 없음** (TF-C). `DIRECTOR_AUDIT_SCHEMA` optional, 반환 dict에 전파.
- NC-3B Few-Shot + Self-Consistency — director.yaml 4곳에 `[NC-3B]` few-shot golden example 삽입 (올바른 체크리스트 응답 예시 + "합산=score 필수" 메시지). `director_ensemble.py`에서 score_breakdown 합산 ≠ score 시 breakdown 우선 자동 교정 (0~100 클램프, _sb_sum > 0 조건). 배치 순서: `_safe_int(score)` 직후, SCM/Firewall/NC-1/NC-3 전.
- SCM 단일 후보 독점 방지 — `director_ensemble.py`에서 `qualified_indices==1`일 때 ①경고 주입("절대 기준으로 독립 평가") ②score≥95→min(score,90) 보정. 90점이면 QualityGate PASS 유지, Director 주권 존중.
- TF-D Advisory 우선순위 시각화 — `stage4_interview_round.py` L457-490에서 advisory 문자열에 우선순위 헤더 태그 삽입. TruthGate→`[CRITICAL · TruthGate]`, NpcDrift/RelDrift/Flashback/InfoParadox→`[MAJOR · ...]`, 나머지→`[INFO]`, 0건 advisory→`[이름] 이상 없음` 1줄 축약. `_advisory_summary` dict 로직(L440-456) 미변경.
- TF-E Chief Writer 톤 조절 — `chief_writer.yaml` COMMON_RULES/WRITING_GUIDELINES에서 "절대 금지"→"사용하지 마세요", "무조건 REJECT"→"감점 대상입니다", "벽돌 문단=독자 이탈 1순위"→"5줄 이상 연속 서술은 줄바꿈으로 끊어주세요". 핵심 금지 3곳 유지: L51 사망NPC/미습득무공, L66 원시인모드 현대용어.
- TF-A 프롬프트 중복 제거 NO-OP — director.yaml VARIABLE_PROMPT(L61-112)와 SELECTION_PROMPT(L345-397)의 V67 중복은 **구조적 필수** (SELECTION_PROMPT는 비캐시 fallback 단독 전송). 진정한 dedup은 V67→STABLE_CONTEXT 이동 필요 (캐시 재설계) → P2 후순위.
- A-4 공통 실패 패턴 감지 — `stage4_orchestrator._handle_round_outcome()`에서 `contradiction_types` 수렴 추적. LOGIC_ERROR 2연속 + 동일 모순 유형 2연속 → Arc 구조 진단 advisory. Director `select_and_judge_ensemble` 반환에 `contradiction_types` 포함, `previous_attempt`에 보존.
- A-3 fix_scope DB 추적 — `director_selections` 테이블에 `fix_scope` 컬럼 추가. Director 판정 시 fix_scope 값(inplace/partial/full/null) 저장, 전략별 수정 패턴 분석 가능.
- B-4 동기/약속 방치 감지 — Chief Writer `self_critique` 5번째 체크: "방치된 동기·약속·떡밥이 없는지". `NarrativeContextFormatter`가 enrichment한 동기/약속 목록과 대조.
- Stage2 advisory — NarrativeContextFormatter(LM-G)가 `stage2_preflight.py`에서 동기/약속/Arc스케일을 `enhanced_context`에 prepend. 순수 Python, LLM/DB 없음.
- TF-45 비무협 무협 오염 근절 — `genre_schema_builder.py`의 `build_state_constraints_schema()`/`build_status_shadow_schema()`로 장르별 동적 스키마 생성. `analyst.yaml`/`analyst_prompts.py`의 "내공" 하드코딩 → `{energy_tracking_rules}`/`{state_constraints_genre_field}`/`{episode_state_label}` 등 플레이스홀더 교체. `analyst.py _build_genre_placeholders(genre, critical_keys)` → 무협이면 원본, 비무협이면 장르별 대체. `response_schemas.py` `status_shadow`의 `internal_energy_loss` → `key_stat_change` 장르 중립화 + 하위호환 브릿지. `stage2_preflight.py`에서 enriched_block → state_changes 매핑 + items_acquired diff 자동 채움.
- TF-47 InPlace 원고 보호 — `chief_writer.inplace_patch()`에서 `response_mime_type="application/json"` 강제 시 LLM이 `{"content":"원고..."}` JSON 반환 → JSON 전체 파싱 1단계 추가 (content/text/manuscript 키). rfind 폴백에서 `_outer_start > 0` 조건 추가 (position 0 → 원고 전체 삭제 방지). `_generate_candidates`에서 빈 manuscript 후보도 실패로 간주.
- TF-48 Arc 실행 상태 연속성 — `four_phase_arc_generator.py`에 `_load_execution_state()`/`_generate_prev_context()` 추가. Arc N+1 생성 시 Arc N의 계획 상태(arc_end_state)뿐 아니라 WorldState/FactLedger/episode_bibles에서 **실제 에피소드 실행 결과**를 로드하여 LLM 컨텍스트에 주입. "실행 결과가 계획과 다를 경우 실행 결과를 따르라" 지시.
- TF-54 WritingDirective — `pattern_tracker.py`의 `build_report()`가 직전 N화 패턴 분석(LLM 0회). `writing_directive_generator.py`가 Flash 1회로 `WritingDirective` 생성. `stage4_interview_round.py`가 `setattr(cw, "_tf54_writing_directive", wd)` + `setattr(cw, "_current_blueprint", blueprint)` 주입. Director `_director_mc_parts[0]`에 `[WritingDirective]` prepend. `chief_writer_quality.py` self-critique 6번째(directive 준수)·7번째(표현 신선도)·8번째(ending_hook) 체크.
- TF-55b STATIC/DB_NPC_RELATIONSHIP — `context_advisor.py` `RetrievalSources.STATIC`(query 문자열 직접 반환, VecMemory 미호출)·`DB_NPC_RELATIONSHIP`(npc_relationship_history 직접 조회). `stage4_context_builder._execute_retrieval_plan()`에서 source 분기 처리. VecMemory hits=0 슬롯이 이 경로로 리다이렉트됨.
- 합격률 개선 — `chief_writer.yaml` 규칙 12(ending_hook 의무화)·13(씬별 대화 의무) 추가. `chief_writer_quality._check_ending_hook_presence()`: 원고 마지막 500자에서 ending_hook 앞 20자 부분 일치 확인. `apply_self_critique()`에서 `getattr(self.host, "_current_blueprint", None)`으로 blueprint 취득.
- Log-Phase2 실패 스니펫 — `llm_calls` 테이블에 `prompt_snippet`(실패 시 앞 3000자)/`response_snippet`(실패 시 전체) 컬럼 추가. 성공 호출은 NULL(DB 폭발 방지). `FailureAnalyzer.failed_call_snippets(agent_name=)` + `failure_prompt_patterns()` 조회. Stage2 `duration_ms`/`failure_category`/`advisory_flags` 보강, Stage3 `attempt_num` `retries+1` 동적화 + `arc_num` 복원 + `reject_reason` 상세화.
- S3-META quality_risk 활용 — `stage4_interview_round.py`에서 `_stage3_meta.quality_risk=True` 시 `[S3-META 경고]` Director advisory 주입 (advisory만, REJECT 강제 없음). `stage4_orchestrator.py`에서 V75-D 임계값을 `quality_risk=True`이면 1연속, 아니면 기존 2연속으로 동적 설정. 테스트 3개 (`test_pass_with_fix.py`).
- 감사 문서 항목 패치 현황 — `docs/2026-03-04/명세-행동 정합성 감사.md` 기준: F-1(YAML주석 교정) ✅, F-2(diff ratio S2/S3/S4) ✅, F-3(fix_scope required) ✅, F-4(트렁케이션 경고) ✅. **F-5(PF-3 소진 상태 전파)**: 미완이나 ROI 낮음 — PF-3 소진 자체가 드물고 다음 라운드 full rewrite로 자연 복구. `stage3-blueprint-logic-error-analysis.md` 기준: §5 _stage3_meta 미활용 → S3-META로 해결 ✅, §6 트리거 지연 → V75-D 조기 트리거로 해결 ✅, §6 Stage3 Python 검증 한계 → 대원칙 부합 NO-GO.
- PASS_WITH_FIX verdict — 전 Stage에서 **Director fix_scope 기반 수정 전략 라우팅 + 재심사 반복** (최대 3회).
  - **3-tier 수정 전략 (분기 조건)**:
    ```
    _use_inplace = _previous_best is not None and (
        fix_scope == "inplace"
        or (not fix_scope and score >= PatchModeThresholds.INPLACE)
    )
    _use_partial = (not _use_inplace) and _previous_best is not None and (
        fix_scope == "partial"
    )
    # else → full rewrite
    ```
    - **inplace**: LLM 1회 국소 수정, `_inplace_patch_*()` 호출. 실패 시 full 폴백.
    - **partial** (TF-36): 가장 좋은 후보 **1개만** `single_strategy=rejected_strategy`로 재생성. Director 피드백 기반 집중 수정.
    - **full**: `_previous_best` 없거나 fix_scope="full" → Ensemble 3후보 전면 재생성.
  - **PASS_WITH_FIX 루프**: fix_scope="inplace" → Stage별 InPlace 패치 + Director 재심사(동일 audit 메서드). fix_scope="partial"/"full" → fix loop 즉시 REJECT → 기존 retry 경로 위임.
  - **재심사 메서드**: S2 `audit_strategic_plan()`, S3 `validator.validate(all_candidates=None)`, S4 `audit_manuscript()`
  - **Validator 2경로**: compare(multi-candidate, director_ensemble) vs audit(single-candidate, audit_manuscript). 양쪽 모두 fix_scope/feedback 전파 완비.
  - **QualityGate 적용 규칙 (TF-46)**: PASS일 때만 score < 90이면 REJECT 선전환. **PASS_WITH_FIX는 QualityGate bypass** — Director 주권 존중, patch 기회 부여.
  - **InPlace patch state_updates (TF-46)**: InPlace 패치 시 LLM이 `patch_state_updates` JSON 블록 반환 → 소비측에서 기존 state_updates에 merge (stale 방지).

---

## SAFE 작업

| Phase | 작업 | 상태 |
|-------|------|------|
| 6-C | pre-commit + ruff 설정 | ✅ 완료 |
| 6-A | pytest 테스트 (GenreGuard, RepetitionGuard, PromptLoader — 63개) | ✅ 완료 |
| 5-A' | PromptLoader import 전환 (7파일 완료) | ✅ 완료 (2026-02-13) |
| 5-B | Settings YAML + 임계값 외부화 | ✅ 완료 (2026-02-14) |

## RISKY 작업 (순서 지킬 것)

| 순서 | Phase | 작업 | 전제 |
|------|-------|------|------|
| ~~1~~ | ~~4D~~ | ~~sqlite-vec (ChromaDB 교체)~~ | ✅ 완료 |
| ~~2~~ | ~~3-5B~~ | ~~수정 모드 — Stage 4 패치 모드~~ | ✅ 완료 |
| ~~3~~ | ~~3-5A~~ | ~~NPC 이력 DB + 검증 강화~~ | ✅ 완료 |
| ~~4~~ | ~~5-B~~ | ~~Settings/임계값 외부화~~ | ✅ 완료 |
| ~~5~~ | ~~6-B~~ | ~~E2E 테스트~~ | ✅ 완료 |
| ~~6~~ | ~~4(잔여)~~ | ~~대형 함수 분할 (R1~R3)~~ | ✅ 완료, R4 async 통일은 NO-GO |
| ~~7~~ | ~~3-QR~~ | ~~품질 회귀 감지 (Step 1+2)~~ | ✅ 완료 (`4b6ad8e`) |
| ~~8~~ | ~~3-5C~~ | ~~NPC 과잉 등장 경고 (extra-only)~~ | ✅ 완료 (`409093c`) |
| ~~9~~ | ~~3-Obs~~ | ~~관측성 — preflight 병렬 구간 계측~~ | ✅ 완료 (`b4eaa58`) |
| ~~10~~ | ~~3-B~~ | ~~크로스 에피소드 반복 감지 (advisory)~~ | ✅ 완료 (`db07efd`) |
| ~~11~~ | ~~3-Obs Step 2~~ | ~~관측성 — 에이전트 레벨 ThreadPoolExecutor 계측~~ | ✅ 완료 (`597fcae`) |
| ~~12~~ | ~~D. 대리만족~~ | ~~대리만족 프레임워크 구현 (5-Step)~~ | ✅ **전체 완료** — Step 1(`0d676c8`), 2(`ffc2bb8`), 3(`470dfee`), 4(`7684a78`), 5(문서) |
| ~~13~~ | ~~A-1~~ | ~~writer.py 유틸 해체~~ | ✅ 완료 (`4aeb9f3`) |
| ~~14~~ | ~~A-3~~ | ~~test_validation 13건 xfail~~ | ✅ 완료 (`8b2081e`) |
| ~~15~~ | ~~C-1~~ | ~~SemanticPlotGuard 키워드 폴백~~ | ✅ 완료 (`eb81782`) |
| ~~16~~ | ~~C-2~~ | ~~NPC 정보 소실 체인 수정~~ | ✅ 완료 (`d145db1`) |
| ~~17~~ | ~~C-3~~ | ~~Validator 우회 체인 수정~~ | ✅ 완료 (`d107eee`) |
| ~~18~~ | ~~B-1-1~~ | ~~stage4 post-processor 추출~~ | ✅ 완료 (`ed48489`) |
| ~~19~~ | ~~B-1-2~~ | ~~stage4 context builder 추출~~ | ✅ 완료 (`667291e`) |
| ~~20~~ | ~~B-1-3~~ | ~~stage4 interview round 추출~~ | ✅ 완료 (`7242d4a`) |
| ~~21~~ | ~~B-1-4~~ | ~~chief_writer context builder 추출~~ | ✅ 완료 (`1e8db62`) |
| ~~22~~ | ~~B-1-5~~ | ~~chief_writer quality gate 추출~~ | ✅ 완료 (`d8c0663`) |
| ~~23~~ | ~~B-1-6~~ | ~~stage2 validation pipeline 추출~~ | ✅ 완료 (`c1008e7`) |
| ~~24~~ | ~~B-1-7~~ | ~~stage2 finalizer 추출~~ | ✅ 완료 (`a6613b1`) |
| ~~25~~ | ~~B-1-8~~ | ~~stage2 preflight analysis 추출~~ | ✅ 완료 (`8d68e85`) |
| ~~26~~ | ~~Green Suite~~ | ~~테스트 정리 (B-1 regression + xfail)~~ | ✅ 완료 (`ae97ffa`) |
| ~~27~~ | ~~E-2~~ | ~~Ruff 전면 정리 (2,234건→0 violations)~~ | ✅ 완료 (`6472c42`, `610d8e4`) |
| ~~28~~ | ~~A-2~~ | ~~stage2_optimizer TODO 2건~~ | ✅ 완료 (`167b305`) |
| ~~29~~ | ~~E-1~~ | ~~Silent Pass 로깅 보강 (16건)~~ | ✅ 완료 (`380c911`) |
| ~~30~~ | ~~D-1~~ | ~~POV 시스템 활성화~~ | ✅ 완료 (`f0390e8`) |
| ~~31~~ | ~~D-2~~ | ~~에피소드 롤백 NPC 되감기~~ | ✅ 완료 (`9ba06cd`) |
| ~~32~~ | ~~D-3~~ | ~~문체 분석 → StyleGuard 자동생성~~ | ✅ 완료 (`79afbfd`) |
| ~~33~~ | ~~D-4~~ | ~~Director 선택 추적~~ | ✅ 완료 (`a2c1fb2`) |
| ~~34~~ | ~~B-2~~ | ~~Protocol 미적합 어댑터 3종~~ | ✅ 완료 (`d45d53c`) |
| ~~35~~ | ~~R5~~ | ~~2차 분할 (R5-1a/2a/2b/2c)~~ | ✅ 완료 (`2b0161c`) |
| ~~36~~ | ~~WorkGuard~~ | ~~작품별 Guard YAML 시스템~~ | ✅ 완료 (`d3bd2db`) |
| ~~37~~ | ~~Debug Sweep~~ | ~~전면 디버깅 스윕 (Phase 1~5b)~~ | ✅ 완료 (`883f438`) |
| ~~38~~ | ~~B-3~~ | ~~ABC/Protocol 전면 표준화~~ | ✅ 완료 |
| ~~39~~ | ~~Sweep 3차~12차~~ | ~~전면 디버깅 스윕 (sweep3~64 + codex)~~ | ✅ 완료 — 128파일+, 200건+ 수정 |
| ~~40~~ | ~~Patch Mode~~ | ~~Stage 2/3 패치 모드 + Legacy 제거~~ | ✅ 완료 (`396280b`, `dd825a8`) |
| ~~41~~ | ~~Ops Quality~~ | ~~운영 품질 6대 개선~~ | ✅ 완료 (`af32192`) |
| ~~42~~ | ~~DB-SSOT~~ | ~~VecMemory → project_data.db 통합~~ | ✅ 완료 (`d7ff7f0`) |
| ~~43~~ | ~~Passrate~~ | ~~전략별 재시도 + 조건부 지능 배선~~ | ✅ 완료 (`0141553`) |
| ~~44~~ | ~~Ensemble FB~~ | ~~Stage 2 arc 앙상블 전략 피드백~~ | ✅ 완료 (`b037cf7`) |
| ~~45~~ | ~~크로스컷+계약~~ | ~~R1-R100 시나리오 스윕 + 계약 위생~~ | ✅ 완료 (`16dc053`, `24b6372`) |
| ~~46~~ | ~~Multi-Sweep~~ | ~~sweep 4~12 + codex 종합 버그 수정~~ | ✅ 완료 (`a4f984f`, `5d073a7`) |
| ~~47~~ | ~~Opus TF 재감사~~ | ~~전면 재감사 + T1/T2 9건 수정~~ | ✅ 완료 (`7ba32c0`, `77b0164`) |
| ~~48~~ | ~~SC-0~6~~ | ~~Smart Context Retrieval 전량 + Post-Audit~~ | ✅ 완료 (`5c762b6`, `6454f5a`) |
| ~~49~~ | ~~TF-5~~ | ~~전체 시스템 디버깅 감사 12TF + 32건 패치~~ | ✅ 완료 (`5e7f7c0`) |
| ~~50~~ | ~~TF-6~~ | ~~롤백 원자성·상태 누적·트랜잭션 등 16건 패치~~ | ✅ 완료 (`9f0de73`) |
| ~~51~~ | ~~TF-7~~ | ~~전체 감사(A~N 14TF) + TF-C-1 + P0/P1/P2 24건 패치~~ | ✅ 완료 (`ddef308`) |
| ~~52~~ | ~~TF-7R~~ | ~~1차(롤백SSOT) + 3차(fail-close) + 6차(피드백루프) + 7차(카오스테스트38개)~~ | ✅ 완료 (`ddef308`) |
| ~~53~~ | ~~PBT~~ | ~~hypothesis property-based tests 46개 — rollback/validation/budget/invariant~~ | ✅ 완료 (`cff4ae5`) |
| ~~54~~ | ~~E2E 통합~~ | ~~DI 배선 wiring 검증 16개 — TF-7R 8개 신호 경로 전량 확인~~ | ✅ 완료 (`67a0262`) |
| ~~55~~ | ~~Debt Audit~~ | ~~아키텍처 부채 감사 — silent except 22건 debug화, DI 후보 주석, dead var 제거~~ | ✅ 완료 (`77f5d62`) |
| ~~56~~ | ~~Memory ROI~~ | ~~vec_memory 검색 품질 4건 개선 (P0-1~P0-4)~~ | ✅ 완료 (`d5888f7`) |
| ~~57~~ | ~~D1 Hybrid~~ | ~~FTS5 + RRF 하이브리드 검색 + 감리 소결함 수정~~ | ✅ 완료 (`2671927`, `3abea28`) |
| ~~58~~ | ~~DB 효율화~~ | ~~chroma_db 삭제·character_voice/foreshadow DB 전환·인덱스 보강~~ | ✅ 완료 (`6422dc4`, `da7439e`, `1b8fe9a`) |
| ~~59~~ | ~~D2 Observability~~ | ~~memory retrieval 경로별 계측 (dense/fallback/hybrid/multi_dense)~~ | ✅ 완료 (`266640d`) |
| ~~60~~ | ~~문서정리~~ | ~~docs/ 완료 히스토리 삭제 (445→70개, -84%)~~ | ✅ 완료 (`48d66d4`) |
| ~~61~~ | ~~E2E Smoke~~ | ~~파이프라인 통합 smoke 테스트 33개 추가~~ | ✅ 완료 (`11cf0ee`) |
| ~~62~~ | ~~TF-10~15~~ | ~~전면 감사 6TF + P0 패치 8건~~ | ✅ 완료 (`e3b407d`) |
| ~~63~~ | ~~TF-16~~ | ~~P1 백로그 3건 — fail-closed + 캐시키 + callable guard 38건~~ | ✅ 완료 (`abe66de`) |
| ~~64~~ | ~~TF-17~~ | ~~Truth Gate 메모리 오염 방지 advisory 검증기 (5개 검사, 20개 테스트)~~ | ✅ 완료 (`5446a3b`) |
| ~~65~~ | ~~TF-18~~ | ~~Hybrid 검색 모드 활성화 (smart_retrieval enabled + hybrid 모드)~~ | ✅ 완료 (`5446a3b`) |
| ~~66~~ | ~~TF-19~~ | ~~Memory Benchmark 골든 에피소드 검색 정확도 테스트 17개~~ | ✅ 완료 (`e4dff1c`) |
| ~~67~~ | ~~Opus TF 전수조사~~ | ~~Stage 0~4 전면 감사 78건 — P0 7건 + P1 17건 패치~~ | ✅ 완료 (`abe64c3`) |
| ~~68~~ | ~~2차 전수조사~~ | ~~동시성·트랜잭션·리소스 71건 — P0 10건 + P1 34건 전량 패치~~ | ✅ 완료 (`eb604a5`) |
| ~~69~~ | ~~3차 전수조사~~ | ~~데이터 무결성·엣지케이스·정합성 73건 — P0 19건 + P1 17건 + P2 2건 패치~~ | ✅ 완료 (`a116ac7`) |
| ~~70~~ | ~~4차 전수조사~~ | ~~동시성·복구경로·계약·설정·크로스컷 51건 — P0 10건 + P1 18건 + dead code 1744줄 삭제~~ | ✅ 완료 (`eb653cf`) |
| ~~71~~ | ~~TF-20~~ | ~~정확도 우선 5건 — [S2-001] ContinuityInspector→retry / [CO-002] memorize 반환값 / [XC-002] NPC fail-closed + Manager audit_event / [S4-001] save_episode_bible→False~~ | ✅ 완료 (`8efe39c`) |
| ~~72~~ | ~~LM-A~~ | ~~세계관 절대 법칙 강제 — Bible→world_laws 자동등록 + TruthGate 7번째 검사(_check_world_law_violation) + CRITICAL 핀 보호~~ | ✅ 완료 |
| ~~73~~ | ~~LM-B~~ | ~~NPC 속성 텍스트 레벨 표류 감지 — NpcDriftAdvisor(원고 vs 스냅샷 LLM advisory) + Stage4 배선~~ | ✅ 완료 |
| ~~74~~ | ~~LM-C~~ | ~~수치 누적 표류 감지 — NumericDriftAdvisor(FactLedger 이력 LLM advisory, 5화 단위) + Stage4 배선~~ | ✅ 완료 |
| ~~75~~ | ~~LM-D~~ | ~~관계도 장기 표류 감지 — RelationshipDriftAdvisor(npc_relationship_history append-only + LLM advisory) + Stage4 배선~~ | ✅ 완료 (`71f1a1f`) |
| ~~76~~ | ~~LM-E~~ | ~~회상/플래시백 오염 감지 — FlashbackVerifier(14개 마커 + VecMemory 참조 + LLM advisory) + Stage4 배선~~ | ✅ 완료 (`71f1a1f`) |
| ~~77~~ | ~~LM-F~~ | ~~1인칭 정보 역설 감지 — InfoParadoxChecker(episode_bibles 지식 누적 + LLM advisory, 1인칭 전용) + Stage4 배선~~ | ✅ 완료 (`71f1a1f`) |
| ~~78~~ | ~~LM-G~~ | ~~서사 구조 컨텍스트 enrichment — NarrativeContextFormatter(동기/약속/Arc스케일 포맷터) + WorldState motivations/promises + Stage2 배선~~ | ✅ 완료 (`71f1a1f`) |
| ~~79~~ | ~~TF-27~32~~ | ~~PASS_WITH_FIX verdict 도입 — 스키마+프롬프트+Stage4 inplace patch + S2/S3 소비자 코드 패치 + 테스트 17개~~ | ✅ 완료 (`75efa5f`) |
| ~~80~~ | ~~TF-32-VERIFY~~ | ~~PASS_WITH_FIX → patch + Director 재심사 반복 (최대3회) — S2/S3/S4 전량~~ | ✅ 완료 |
| ~~81~~ | ~~TF-33~~ | ~~fix_scope 기반 3-tier 수정 라우팅 — inplace만 fix loop, partial/full → REJECT → retry 경로~~ | ✅ 완료 |
| ~~82~~ | ~~TF-34~~ | ~~Validator PASS_WITH_FIX 피드백 보존(L303) + compare 경로 fix_scope 전파(L133)~~ | ✅ 완료 |
| ~~83~~ | ~~TF-45~~ | ~~Central Schema Builder — 비무협 장르 프롬프트 오염 근절~~ | ✅ 완료 (`3c19e6d`) |
| ~~84~~ | ~~TF-46~~ | ~~합격률 개선 — QualityGate PASS_WITH_FIX bypass + 컨텍스트 한도 증가 + InPlace state_updates 반환/merge~~ | ✅ 완료 (`8476bc2`) |
| ~~85~~ | ~~B-1-3b~~ | ~~stage4_interview_round.run() 2차 분할 — 1,647→686줄(-58%), 5개 private 메서드 추출~~ | ✅ 완료 (`ce9b9c4`) |
| ~~86~~ | ~~LM-I~~ | ~~npc_history known_attrs 4필드 동기화 — WorldState §15~17 (injury/location/permanent_injuries) + §3 (relation_to_protag) + NpcDriftAdvisor 프롬프트 보강~~ | ✅ 완료 |
| ~~87~~ | ~~E-1~~ | ~~PatchModeThresholds.PATCH dead code 제거 — fix_scope 기반 라우팅으로 대체됨. 테스트·YAML·docstring 정리~~ | ✅ 완료 |
| ~~88~~ | ~~LM-H~~ | ~~FlashbackVerifier 원고 원문 대조 강화 — VecMemory.fetch_manuscript_snippet 공개화 + 원문 스니펫 LLM 프롬프트 주입 + 원문 우선 참조 지시~~ | ✅ 완료 |
| ~~89~~ | ~~A-4~~ | ~~공통 실패 패턴 감지 — contradiction_types 반환·보존 + 동일 모순 유형 2연속 Arc 구조 진단 advisory~~ | ✅ 완료 (`f0a091b`) |
| ~~90~~ | ~~NumericDrift~~ | ~~장기연재 한도 보강 — MAX_ITEMS 20→30, MAX_HISTORY_POINTS 15→20~~ | ✅ 완료 (`f0a091b`) |
| ~~91~~ | ~~A-2+A-3+B-4+TF-25-01~~ | ~~open_review CW 전달 + fix_scope DB 추적 + 동기/약속 방치 감지 + IndexError 방어~~ | ✅ 완료 (`9417b6d`) |
| ~~92~~ | ~~TF-25~~ | ~~전수 확인(01~09) + SSOT 통합 — base_agent/director_ensemble → validation.yaml 단일 참조~~ | ✅ 완료 |
| ~~93~~ | ~~TF-26~~ | ~~종합 감사 — Director SSOT + dead config 2파일 삭제 + 로깅 강화 9건 + 타임아웃 YAML 외부화~~ | ✅ 완료 |
| ~~94~~ | ~~B-1-9~~ | ~~거대 함수 2차 분할 — process_pass_result(-71%) + run_validation(-83%) + ask(-57%) = 13개 메서드 추출~~ | ✅ 완료 |
| ~~95~~ | ~~LM-Tier~~ | ~~장기 기억+품질 강화 6건 — TF-A(bare except) + TF-B(지수 성장) + TF-C(fix_scope 주입) + TF-D(npc reason) + TF-E(HUD Anomaly) + TF-F(누적 시간)~~ | ✅ 완료 |
| ~~96~~ | ~~P1-5~~ | ~~장기 반복 감지 advisory — LongTermRepetitionAdvisor(20화+ 씬 패턴 2-gram 분석 + LLM 판정) + Stage4 배선~~ | ✅ 완료 |
| ~~97~~ | ~~TF-45~~ | ~~비무협 무협 오염 근절 7건 — 동적 에너지 블록+ARC_DESIGN_SCHEMA state_changes+status_shadow 중립화+analyst 플레이스홀더+후처리 매핑~~ | ✅ 완료 (`63661c1`) |
| ~~98~~ | ~~TF-47~~ | ~~InPlace/PASS_WITH_FIX 패치 원고 전체 삭제 버그 — JSON 파싱 1단계+rfind position 0 보호+빈 manuscript 실패 처리~~ | ✅ 완료 (`99bd199`) |
| ~~99~~ | ~~TF-48~~ | ~~Arc 간 실행 상태 연속성 — DB에서 실제 에피소드 실행 결과 로드+LLM 컨텍스트 주입 (계획-실행 괴리 근절)~~ | ✅ 완료 (`00bcef5`) |
| ~~100~~ | ~~TF-54~~ | ~~WritingDirective — PatternTracker(LLM 0회)+지시생성(Flash 1회)+CW setattr 주입+Director MC prepend+self-critique 6·7·8번째 체크~~ | ✅ 완료 (`3f18370`) |
| ~~101~~ | ~~TF-55b~~ | ~~VecMemory hits=0 슬롯 → STATIC(query 직접 반환)/DB_NPC_RELATIONSHIP(관계이력 직접 조회) — context_advisor + stage4_context_builder~~ | ✅ 완료 (`d55081d`) |
| ~~102~~ | ~~Model SSOT~~ | ~~모델명 models.yaml 단일 참조 — constants.py _load_model_from_yaml + config_manager 동적 로드 + 6개 파일 AIModels.* 교체~~ | ✅ 완료 (`5336be8`) |
| ~~103~~ | ~~합격률 개선~~ | ~~ending_hook 의무화(chief_writer.yaml 규칙12·13) + _check_ending_hook_presence(앞20자 부분일치) + stage4_interview_round blueprint setattr~~ | ✅ 완료 (`5a27a8d`) |
| ~~104~~ | ~~실파이프라인 검증~~ | ~~TF-54/55b/합격률 wiring 통합 테스트 8개 — setattr 배선·ending_hook 체인·STATIC/DB_NPC dispatch·Director MC prepend(test_pipeline_wiring.py)~~ | ✅ 완료 (`8dcb785`) |
| ~~105~~ | ~~6차 전수조사~~ | ~~신규 코드 전수 감사 P0 0건 + P1 3건 — config_manager fallback 정렬·reference_anchor AIModels·confidence_calibration model 인자화~~ | ✅ 완료 (`ce1658f`) |
| ~~106~~ | ~~V73~~ | ~~자본금 역동기화 2중 방어 — Director state_updates 우선 + 대사 제거 regex~~ | ✅ 완료 |
| ~~107~~ | ~~7차 전수조사~~ | ~~P2 SSOT 주석 7파일 + LM-B/C/P1-5 except Exception 보강~~ | ✅ 완료 |
| ~~108~~ | ~~LM-post-1~~ | ~~Retrospective lookback 5→10 YAML 외부화 + causal_graph Read + Director MC 보조 주입~~ | ✅ 완료 |
| ~~109~~ | ~~8차 전수조사~~ | ~~LM-E/F/D except Exception 보강 — advisory 비치명 완결~~ | ✅ 완료 |
| ~~110~~ | ~~God Object 1~~ | ~~stage4_interview_round.run() 782→404줄, _setup_writing_directive/_build_common_writer_kwargs/_run_pre_director_validation 추출~~ | ✅ 완료 (`9405b6f`) |
| ~~111~~ | ~~God Object 2~~ | ~~main_a._attach_agents() 570→137줄, _init_core_agents/_init_v50_modules 추출~~ | ✅ 완료 (`d3b9d79`) |
| ~~112~~ | ~~God Object 3~~ | ~~stage4_interview_round._process_verdict() 320→114줄, _run_post_select_checks/_execute_pass_with_fix_loop 추출~~ | ✅ 완료 (`d715975`) |
| ~~113~~ | ~~로깅 강화~~ | ~~llm_calls+stage_attempts DB 테이블 + BaseAgent 계측 + FailureAnalyzer + advisory_warnings 컬럼 + episode_production.jsonl 필드 강화~~ | ✅ 완료 (`b48a1c6`) |
| ~~114~~ | ~~Log-Phase2~~ | ~~실패 스니펫 저장(prompt_snippet/response_snippet 실패 한정 3000자) + Stage2 duration_ms/failure_category/advisory_flags 보강 + Stage3 attempt_num 동적화/arc_num 복원/reject_reason 상세화~~ | ✅ 완료 (감리 PASS, 3,245 passed) |
| ~~115~~ | ~~NC-1~~ | ~~수치 정합성 Python 검증(5개 검사: FactLedger교차/산술/직함/이벤트순서, LLM 0회) + 단일 후보 독점 방지 SCM(경고 주입+score 95→90 보정)~~ | ✅ 완료 (3,299 passed) |
| ~~116~~ | ~~NC-2~~ | ~~실파이프라인 11대 이슈 잔여 갭 6건 해소 — 퍼센트구성검증+NPC동명이인+도입부유사도+씬유사도advisory+공간연속성프롬프트+시간경과Stage4주입~~ | ✅ 완료 (3,331 passed) |
| ~~117~~ | ~~NC-3~~ | ~~Director 일관성 체크리스트 10개 카테고리 — consistency_checklist 스키마+프롬프트(4곳)+파싱+ISSUE 3건+ python_warnings 상한 3+반환 전파+테스트 11개~~ | ✅ 완료 (3,342 passed) |
| ~~118~~ | ~~NC-3B~~ | ~~Few-Shot Golden Example(director.yaml 4곳) + score_breakdown 합산 Self-Consistency Check(director_ensemble.py) + 테스트 6개~~ | ✅ 완료 (3,348 passed) |
| ~~119~~ | ~~TF-LLM P0~~ | ~~TF-D Advisory 시각화(CRITICAL/MAJOR/INFO 헤더+0건 축약) + TF-E CW 톤 조절(강압→완화, 핵심 금지 유지) + TF-A 중복 제거(NO-OP — SELECTION_PROMPT standalone 필수, P2 재분류)~~ | ✅ 완료 (3,348 passed, 감리 PASS) |
| ~~120~~ | ~~PWF-S2~~ | ~~Stage 2 PASS_WITH_FIX 무력화 수정 — inplace patch 이력을 Director 재심사 story_context에 주입(stage2_finalizer.py) + 테스트 3개~~ | ✅ 완료 (3,351 passed, 감리 PASS) |
| ~~121~~ | ~~NS-1/NS-1-P/NS-2~~ | ~~전장르 수치 자기검증 — S2 ANALYST_SELF_CRITIC 항목7 강화(LLM재계산) + S3 BLUEPRINT_PREFLIGHT 항목6 추가 + S4 CW self_critique check9(_check_arithmetic_consistency, mult/pct/add_sub 3패턴) + NS-1-P(inplace 패치 후 Python 산술 검증→Director story_context 주입) + NS-2(Arc PASS 후 genre_ext vs arc_end_state 30% 괴리 advisory 로깅) + 테스트 13개~~ | ✅ 완료 (3,364 passed, 감리 PASS) |
| ~~122~~ | ~~NS-3~~ | ~~Treatment block 수치 목표 self-critic 주입 — NS-3-A(_format_block_numeric_targets: genre_ext 수치 → fallback critic_input prepend) + NS-3-B(_check_arc_vs_block_targets: FourPhase Phase 2.55 Python 교차검증, 30% 괴리 경고 → feedback prepend) + 테스트 6개~~ | ✅ 완료 (3,370 passed, 감리 PASS) |
| ~~123~~ | ~~NS-4~~ | ~~Arc 간 시간 연속성 체크 — stage3_orchestrator._extract_arc_time_markers(regex, LLM 0회) + NS-4 advisory 주입(TF9 except 직후) + Director NC-3 체크리스트 11번째 항목(timeline_arc_consistency) + director_ensemble._nc3_keys 추가 + 테스트 5개~~ | ✅ 완료 (3,382 passed, 감리 PASS) |
| ~~124~~ | ~~NS-4-S2/S4~~ | ~~Arc 간 날짜 감각 Stage 2/4 확장 — four_phase_arc_generator._ns4_extract_time_markers(모듈 상단)+_generate_prev_context() return 직전 ⏱️[NS-4] 주입 + stage4_interview_round._ns4_extract_time_markers(모듈 상단)+run() [Timeline] 직후 [Arc 시간 연속성 참고] Director mc_parts 주입 + 테스트 5개~~ | ✅ 완료 (3,387 passed, 감리 PASS) |
| ~~125~~ | ~~TF-G/TF-I/TF-C~~ | ~~P1 코덱스 3건 — TF-G(Self-Critique 게이트 ending_hook+분량) + TF-I(director_feedback common_writer_kwargs 주입) + TF-C(NC-1/NC-3 자동감점 제거 — 대원칙 3 Director 주권 존중)~~ | ✅ 완료 (3,390 passed, 감리 PASS) |

---

## 기존에 있지만 제대로 안 쓰이는 것들

| 기능 | 파일 | 상태 |
|------|------|------|
| 시점 전환 프리셋 | `blueprint_ensemble.py` L76~90, `stage0/__init__.py` | ✅ **D-1 활성화 완료** — POV 선택 메뉴 추가, 전체 체인 작동 |
| 시점(POV) 일관성 체크 | `pre_llm_validator.py` V70 | ✅ 구현됨 |
| A/B 테스트 / 선택 추적 | `db_manager.py` director_selections | ✅ D-4 완료 — 전략 승률 DB 저장 |
| 에피소드 롤백 | `project_manager.py` | ✅ D-2 완료 — NPC이력+WorldState+FactLedger 롤백 |
| 문체 분석 → Guard | `genre_guards/style_guard.py` | ✅ D-3 완료 — StyleGuard 래퍼 (자동 래핑) |
| Context Caching | `base_agent.py` | ✅ 구현 완료 (`chief_writer`·`director_continuity`에서 사용 중) |

---

## 상세 정보

**`참고자료.md`를 반드시 읽을 것.** 포함 내용:
- 시스템 아키텍처 전체 구조도
- 버그 패턴 분석 (Tier 1~8)
- NPC 연속성 실패 시나리오 24개 (3-C)
- 수정 모드 전략 (3-D)
- 개선 아이디어 27개 + 대조표 (3-E)
- 독자 대리만족 프레임워크 (3-F)
- 리팩토링 Phase 1~6 로드맵

