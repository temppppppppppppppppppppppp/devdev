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

## 현재 상태 (2026-02-16)

- **작동함**: Stage 0→2→4 정상 동작
- **완료된 것**: Phase 1~2, 5-A/5-B/5-C, 6-A/6-B/6-C, 4C(DI), 4D(sqlite-vec), 3-5B(패치), 3-5A(NPC이력), **4-R1~R3(몬스터 분할)**, R4-a(NO-GO), **3-QR(품질 회귀 감지)**, **3-5C(NPC 과잉 경고)**, **3-Obs Step 1+2(관측성 계측)**, **3-B(크로스 에피소드 반복 감지)**, **D.대리만족 전체 완료(Step1~5)**, **A-1(writer 유틸 해체)**, **A-3(test xfail)**, **C-1(PlotGuard 폴백)**, **C-2(NPC 체인)**, **C-3(Validator 체인)**, **B-1-1(stage4 post-processor 추출)**
- **약점**: ~~플롯 중복 감지 불안정 (Chain 1)~~ → C-1에서 키워드 폴백 도입으로 개선
- **현재 단계**: **B-1 모놀리스 분할 진행 중** (B-1-1 stage4 post-processor 완료)
- **다음 우선순위**: B-1-2(stage4 context builders) → B-1-3(interview loop) → chief_writer 분할
- **테스트 기준선**: **419 passed** (기존 406 + post_processor 13)
- **stage4 orchestrator**: 2,481→1,972줄 (-21%, B-1-1 분할 후)
- **checkpoint**: `ed48489`
- **실행 기준 문서(SSOT)**: `내일작업.md` (남은 작업만 관리)

---

## 핵심 파일

| 파일 | 역할 | 비고 |
|------|------|------|
| `modules/core/stage2_orchestrator.py` | Arc 오케스트레이터 | DI 전환 완료 (`self.app` 0, `self.ctx` 사용) |
| `modules/core/stage3_orchestrator.py` | Blueprint 오케스트레이터 | DI 전환 완료 (`self.app` 0, `self.ctx` 사용) |
| `modules/core/stage4_orchestrator.py` | 원고 오케스트레이터 | DI 전환 완료, B-1-1 post-processor 분리 (1,972줄) |
| `modules/core/stage4_post_processor.py` | Stage4 PASS 후처리 | B-1-1 분리 (543줄), V64 위임 패턴 |
| `modules/core/db_manager.py` | SQLite DB 매니저 | 모범 패턴 |
| `modules/core/prompt_loader.py` | YAML 프롬프트 로더 (싱글톤) | |
| `config/prompts/*.yaml` | 외부화된 프롬프트 43개 | |
| `modules/domain/agents/*.py` | AI 에이전트 20+개 | |
| `modules/core/genre_guards/*.py` | 장르 가드 3개 | |
| `modules/validation/*.py` | 검증 파이프라인 | |
| `config/settings/validation.yaml` | 검증 임계값 설정 | Phase 5-B |
| `modules/validation/threshold_helper.py` | 공유 `_threshold()` 헬퍼 | Phase 5-B-2c |
| `modules/core/writer_prompt_builders.py` | Writer 유틸 독립 모듈 | A-1 분리 |
| `modules/core/semantic_plot_guard.py` | 플롯 중복 감지 (임베딩+키워드 폴백) | C-1 개선 |

---

## ⚠️ 주의

- `writer.py` — 유틸 3개는 `writer_prompt_builders.py`로 분리 완료 (A-1). 냉동인간 폴백(`write_v20_manuscript`)만 유지.
- `memory_engine.py` — **삭제됨** (Phase 4D 완료). VecMemory(`vec_memory.py`)가 단일 벡터 경로.
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

---

## 기존에 있지만 제대로 안 쓰이는 것들

| 기능 | 파일 | 상태 |
|------|------|------|
| 시점 전환 프리셋 | `blueprint_ensemble.py` L81~84 | ✅ 존재, YAML 연동만 필요 |
| 시점(POV) 일관성 체크 | `pre_llm_validator.py` V70 | ✅ 구현됨 |
| A/B 테스트 | `ab_testing.py` | ⚠️ `quick_ab_test()` 존재, 확장 필요 |
| 에피소드 롤백 | `project_manager.py` | ⚠️ `auto_backtrack_v35()`, NPC 되감기 추가 필요 |
| 문체 분석 | `stage0/style_extractor.py` | ⚠️ 있음, 가드 자동생성 연동 필요 |
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

