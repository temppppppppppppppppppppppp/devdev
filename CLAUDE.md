# 글도비 — 후임 에이전트 인수인계

> AI 웹소설 자동 생성 시스템. Python + Gemini API.
> 상세 참고: `참고자료.md` (2000줄+ 종합 자료)

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

## 현재 상태 (2026-02-23)

- **작동함**: Stage 0→2→4 정상 동작
- **완료된 것**: Phase 1~2, 5-A/5-B/5-C, 6-A/6-B/6-C, 4C(DI), 4D(sqlite-vec), 3-5B(패치), 3-5A(NPC이력), **4-R1~R3(몬스터 분할)**, R4-a(NO-GO), **3-QR(품질 회귀 감지)**, **3-5C(NPC 과잉 경고)**, **3-Obs Step 1+2(관측성 계측)**, **3-B(크로스 에피소드 반복 감지)**, **D.대리만족 전체 완료(Step1~5)**, **A-1(writer 유틸 해체)**, **A-3(test xfail)**, **C-1(PlotGuard 폴백)**, **C-2(NPC 체인)**, **C-3(Validator 체인)**, **B-1 전체 완료(stage4 -64%, chief_writer -62%, stage2 -66%)**, **E-2(Ruff 0 violations)**, **A-2(optimizer TODO)**, **R5(2차 분할 전량)**, **WorkGuard(작품별 YAML)**, **Debug Sweep 1차~12차 전량 완료**, **B-3(Protocol 전면 표준화)**, **DB-SSOT(VecMemory merge)**, **Patch Mode(Stage 2/3)**, **Passrate 전략 배선**, **Ensemble Feedback**, **Ops Quality 6대 개선**, **Opus TF 전면 재감사+T1/T2 수정**, **SC-0~6(Smart Context Retrieval) + Post-Audit**, **TF-5 전체 시스템 디버깅 감사 32건 패치**, **TF-6 롤백 원자성·상태 누적·트랜잭션 등 16건 패치**, **TF-7 전체 감사(A~N) + P0/P1/P2 24건 패치**, **TF-7R 1차/3차/6차 17건 + 7차 카오스 테스트 38개**, **PBT(hypothesis) 46개**, **E2E 통합 wiring 16개**, **아키텍처 부채 감사(silent except·DI주석·dead var)**, **Memory ROI P0-1~P0-4(검색품질 4건)**, **D1 Hybrid Retrieval(FTS5+RRF)**, **DB 효율화(chroma_db삭제·file→DB·인덱스보강)**, **D2 Memory Observability(경로별 계측)**, **문서정리(docs 445→70개)**, **E2E Smoke Tests(파이프라인 통합 33개)**, **TF-10~15 전면 감사+P0 패치**, **TF-16(P1 백로그 3건)**, **TF-17(Truth Gate 메모리 오염 방지)**, **TF-18(Hybrid 검색 활성화)**, **TF-19(Memory Benchmark 17개)**, **Opus TF 전수조사(P0 7+P1 17건 패치)**, **2차 전수조사(P0 10건 + P1 34건 전량 패치)**, **3차 전수조사(P0 19+P1 17+P2 2건 패치)**, **4차 전수조사(동시성·복구·계약·설정·크로스컷 51건 — P0 10+P1 18+dead code 1744줄 삭제)**, **메타감리(1~4차 130+패치 검증 — 오작업 0건, 테스트 복원 17개)**
- **현재 단계**: 4차 Opus TF 전수조사 + 메타감리 완료. 안정화 단계.
- **테스트 기준선**: **2,585 passed + 0 xfailed** (last verified 2026-02-24, `pytest tests/ -q`)
- **Ruff**: 0 violations, Silent Pass YELLOW 0건 (E-1+E-2 완료)
- **stage4 orchestrator**: 2,481→883줄 (**-64%**, 분할 완료, 서브모듈 3개)
- **chief_writer**: 2,255→854줄 (**-62%**, 분할 완료, 서브모듈 2개)
- **stage2 orchestrator**: 2,639→907줄 (**-66%**, B-1-8 완료, 서브모듈 3개)
- **DI 전환**: Stage2(44슬롯) + Stage3(19슬롯) + Stage4(24슬롯) 전량 완료
- **checkpoint**: `b506e48`
- **향후 계획 문서**: `docs/2026-02-23/next_steps_plan.md` (후순위 관찰 대기 항목)
- **후순위(관찰 대기)**: `docs/2026-02-23/next_steps_plan.md` — 2차(동적 장르), 4차(캐시), 5차(설정 SSOT)

---

## 핵심 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `modules/core/stage2_orchestrator.py` | Arc 오케스트레이터 | B-1-6~8 분리 후 907줄, 서브모듈 3개 위임 |
| `modules/core/stage2_validation_pipeline.py` | Stage2 검증 파이프라인 | B-1-6 분리 (683줄), V64 위임 패턴 |
| `modules/core/stage2_finalizer.py` | Stage2 Finalizer | B-1-7 분리 (535줄), V64 위임 패턴 |
| `modules/core/stage2_preflight.py` | Stage2 Preflight 분석 | B-1-8 분리 (637줄), V64 위임 패턴 |
| `modules/core/stage3_orchestrator.py` | Blueprint 오케스트레이터 | DI 전환 완료 (19슬롯, lazy init만 self.app) |
| `modules/core/stage4_orchestrator.py` | 원고 오케스트레이터 | B-1-1~3 분리 후 883줄, 서브모듈 3개 위임 |
| `modules/core/stage4_post_processor.py` | Stage4 PASS 후처리 | B-1-1 분리 (543줄), V64 위임 패턴 |
| `modules/core/stage4_context_builder.py` | Stage4 컨텍스트 빌더 | B-1-2 분리 (570줄), V64 위임 패턴 |
| `modules/core/stage4_interview_round.py` | Stage4 인터뷰 라운드 | B-1-3 분리 (554줄), V64 위임 패턴 |
| `modules/domain/agents/chief_writer_context.py` | CW 컨텍스트 빌더 | B-1-4 분리 (1,074줄), V64 위임 패턴 |
| `modules/domain/agents/chief_writer_quality.py` | CW 품질 게이트 | B-1-5 분리 (465줄), V64 위임 패턴 |
| `modules/core/truth_gate.py` | 메모리 오염 방지 advisory 검증기 | TF-17, 5개 검사 (사망NPC/아이템/장소/스킬/카르마) |
| `modules/core/context_advisor.py` | Smart Context Retrieval 플래너 | SC-1~6, RetrievalPlan/Slot/Sources |
| `modules/core/db_manager.py` | SQLite DB 매니저 | 모범 패턴 |
| `modules/core/prompt_loader.py` | YAML 프롬프트 로더 (싱글톤) | |
| `config/prompts/*.yaml` | 외부화된 프롬프트 43개 | |
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

- `writer.py` — 유틸 3개는 `writer_prompt_builders.py`로 분리 완료 (A-1). `write_v20_manuscript` API만 유지 (오케스트레이터에서 호출 제거됨, 외부 진입점용).
- `memory_engine.py` — **삭제됨** (Phase 4D 완료). VecMemory(`vec_memory.py`)가 DBManager 커넥션을 공유 (DB-MERGE). `project_data.db` 단일 파일이 SSOT.
- NPC 속성 변경 — `npc_history` 테이블로 append-only 이력 기록 (Phase 3-5A 완료). `bind_db()` 호출 시 활성화.
- `base_agent.py`의 Context Caching — 구현 완료 (`_get_or_create_context_cache` L920, `_ask_with_cached_context` L1003). `chief_writer`·`director_continuity`에서 사용 중.

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

