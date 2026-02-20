# Codex Sweep 300 — 탐색 전용 오더

> 목표: Stage 2/3/4 통과율·런타임 안정성 확보 + 인코딩 하드닝.
> 원칙: 코드를 먼저 읽고, 읽은 코드 기반으로만 판단한다. 추측 금지.

---

## 0. 사전 규칙 (전 Phase 공통)

### 0-0. 역할 한정: 탐색만, 수정 금지

**너의 역할은 버그·리스크를 찾아서 보고하는 것이다. 코드를 수정하지 마라.**

- 소스 파일(`.py`, `.yaml`, `.json`, `.md`)을 절대 편집하지 마라.
- 테스트 파일도 수정하지 마라.
- `git add`, `git commit` 하지 마라.
- 수정 제안은 리포트 텍스트 안에 "제안:" 항목으로만 기술하라.
- 실제 수정은 별도 감리 단계에서 수행한다.

**허용되는 행동:**
1. 파일 읽기 (Read).
2. `ruff check --no-fix` (읽기 전용 린트).
3. `pytest --collect-only` 또는 `pytest -q --tb=short` (테스트 실행, 수정 없이).
4. 리포트 파일(`docs/codex_findings_sweep300.md`) 작성·추가.

### 0-1. 코드 읽기 의무

**각 Phase의 대상 파일을 반드시 먼저 읽은 후에만 버그를 보고하라.**
- 파일을 읽지 않고 추측으로 작성한 항목은 전부 오탐(false positive)이다.
- 모든 보고에 `파일:라인` 근거를 포함하라.
- 근거 없는 항목은 리포트에 넣지 마라.


### 0-1A. 수동 코드 검토 강제 (추가)

아래 규칙은 **필수**다. 위반 시 해당 라운드 결과는 무효 처리한다.

1. 각 라운드는 대상 파일 1~3개를 **직접 열어서** 함수 본문/분기/예외 경로를 눈으로 확인한 뒤 기록한다.
2. `rg`, `ruff`, `pytest` 결과는 **보조 증거**일 뿐이며, 이것만으로 BUG를 확정하지 않는다.
3. 로그/grep 출력만 모아 작성하는 방식은 금지한다. (자동 요약 기반 보고 금지)
4. Confirmed Bug는 아래 3개 중 **최소 2개 충족** 시에만 허용한다.
   - 수동 재현 근거
   - 계약 위반 근거 (호출자↔피호출자 타입/필드/분기)
   - 테스트 근거 (실패 재현 또는 테스트 공백의 명시적 증거)
5. 2개 미만 충족 항목은 BUG로 쓰지 말고 **Risks**로 분류한다.

### 0-2. 1라운드 정의

1라운드 = **대상 파일 1~3개를 읽고, 해당 파일 범위에서 버그/리스크를 탐색하는 단위**.
- 라운드당 출력: 아래 템플릿 1건.
- 발견이 없으면 `없음`으로 기록 (빈 라운드도 기록).

### 0-3. 라운드별 작업 절차

매 라운드마다 아래 순서를 따르라:

1. **파일 읽기**: 대상 파일 1~3개를 전문 읽기.
2. **흐름 추적**: 함수 호출 체인, 분기 조건, 예외 처리 경로를 따라가며 검토.
3. **의심 지점 확인**: 의심 가는 곳이 있으면, 호출하는 쪽과 호출받는 쪽을 모두 읽어서 실제 문제인지 교차 검증.
4. **리포트 작성**: 아래 템플릿에 맞춰 `docs/codex_findings_sweep300.md`에 추가.
5. **다음 라운드**: 같은 Phase 내 다음 파일로 이동.

### 0-4. 라운드 출력 템플릿

모든 라운드 결과를 `docs/codex_findings_sweep300.md`에 누적 기록하라.

```markdown
### Round N

**읽은 파일**: `파일1.py`, `파일2.py`
**수동 검토 근거**:
- 직접 확인한 함수/메서드: `함수A`, `함수B`
- 확인한 핵심 분기/예외 경로: `if ...`, `except ...`
- BUG 확정 근거 충족 수: (재현/계약/테스트 중 2개 이상)


**Confirmed Bugs** (런타임 크래시 또는 잘못된 결과를 유발하는 확실한 버그):
- `파일:라인` — 설명. 재현 조건. 영향 범위.
- (제안: 어떻게 고쳐야 하는지 한 줄 서술)

**Risks** (설계 확인 필요 — 버그일 수도 의도일 수도 있는 것):
- `파일:라인` — 설명. 왜 리스크인지. 어떤 조건에서 문제가 되는지.

**False Positives Excluded** (처음에 의심했으나 오탐으로 판정한 것):
- `파일:라인` — 왜 오탐인지 근거.

**Test Gaps** (테스트가 없거나 부족한 경로):
- `파일:라인` — 어떤 경로가 테스트되지 않는지.

**없으면**: 각 항목에 `없음` 기재.
```

### 0-5. 심각도 분류

모든 Confirmed Bug에 심각도를 부여하라:

| 등급 | 기준 | 예시 |
|------|------|------|
| P0-CRITICAL | 데이터 소실, 무한루프, 파이프라인 중단 | DB write 누락, Stage 루프 미종료 |
| P1-HIGH | 잘못된 결과, 상태 오염 | 점수 계산 오류, 캐시 미갱신 |
| P2-MEDIUM | 엣지케이스 크래시, 성능 저하 | None 입력 시 TypeError, 불필요 재연산 |
| P3-LOW | 로깅 부재, 코드 위생 | 경고 누락, 미사용 변수 |

### 0-6. 오탐 판정 기준 — 아래는 버그가 아니다

1. `# [V64.P4] OPTIONAL:` 주석이 달린 pass/빈 except → 의도적 설계.
2. `getattr(obj, attr, None)` 폴백 → DI 호환 패턴.
3. `logging.info` 레벨 → 이미 Sweep 3에서 정리 완료.
4. validation.yaml에서 로드하는 임계값 → 하드코딩 아님.
5. `_threshold()` 호출 → 외부 설정 참조, 하드코딩 아님.
6. `MagicMock` 관련 테스트 패턴 → 의도적.
7. Thread safety에서 `RLock` 또는 `threading.Lock` 사용 중인 곳 → 이미 보호됨.
8. `bare except` 0건 정책 완료 상태 → 재보고 불필요.
9. Advisory 시스템(3-QR, 3-5C, 3-B) → 관측 전용, LLM 동작 불변. 로직 버그 아님.
10. `side_effect` 없는 MagicMock 반환값 → 테스트 설계상 의도적.

### 0-7. 이전 Sweep에서 수정 완료된 영역 (재보고 금지)

| Sweep | 수정 항목 수 | 주요 영역 |
|-------|------------|----------|
| 1차 | 11건 | quality_dashboard 배선, 캐시 무효화, silent swallow 로깅, DB 중복정의, DI 잔류, Stage3Context 확장 |
| 2차 | 2건 | Stage2→app StateTracker 동기화, full_extract_from_arcs 통합 |
| 3차 | 27건 | 크래시 방지 4, 로깅 레벨 7, Null Guard 4, 캐시 동기화 2, 하드코딩 임계값 3, JSON 안전성 2, 스레드 안전성 2, 코드 위생 3 |
| Codex 1~2 | 15건 | set+dict 크래시, re.escape, ep_count 타입, safe_commit_async, 스레드 안전성, 롤백 리플레이, 적응 임계값 |

위 영역과 동일한 패턴을 다시 보고하면 오탐으로 처리한다.

### 0-8. 중단 규칙

- 같은 P1 이슈가 3번 반복 발견되면 해당 Phase 즉시 종료, 리포트 제출.
- 데이터 무결성 관련 P0가 1건이라도 나오면 즉시 종료, 리포트 제출.
- Phase 종료 전 발견 건수 0이 10라운드 연속이면 해당 Phase 조기 종료 가능.

### 0-9. Phase 종료 시 검증

각 Phase 종료 후, 기존 테스트가 깨지지 않았는지 확인 (수정 없이 실행만):

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short
```

테스트 실패가 발견되면 리포트에 `Test Failure` 항목으로 기록하라. 수정하지 마라.

---

## Phase A (라운드 1-40): Stage 전환 + 재시도 회귀

### 목적
Stage 오케스트레이터·DI Context·DB 계층의 계약 위반과 회귀 탐색.

### 필수 읽기 파일 (Phase A 시작 전 전부 읽을 것)

**Stage 오케스트레이터 (6,552 LOC)**:
```
modules/core/stage2_orchestrator.py          (818줄)
modules/core/stage2_validation_pipeline.py   (713줄)
modules/core/stage2_finalizer.py             (685줄)
modules/core/stage2_preflight.py             (799줄)
modules/core/stage3_orchestrator.py          (565줄)
modules/core/stage4_orchestrator.py          (879줄)
modules/core/stage4_post_processor.py        (626줄)
modules/core/stage4_context_builder.py       (589줄)
modules/core/stage4_interview_round.py       (878줄)
```

**DI Context (511 LOC)**:
```
modules/core/stage2_context.py               (233줄)
modules/core/stage3_context.py               (111줄)
modules/core/stage4_context.py               (167줄)
```

**DB + 벡터 (2,375 LOC)**:
```
modules/core/db_manager.py                   (1,797줄)
modules/core/vec_memory.py                   (578줄)
```

### 탐색 초점

1. **Stage 전환 계약**: Stage 2 결과 → Stage 3 입력 → Stage 4 입력 경로에서 데이터 누락/변형.
2. **재시도 종료 조건**: max_attempts=5 (Stage 2/4), max_retries=4 (Stage 3)이 실제로 종료되는지.
3. **점수/판정 계약**: Director 점수가 quality gate, patch mode 분기에 정확히 전달되는지.
4. **DB 읽기/쓰기 무결성**: 트랜잭션 commit 누락, Lock 보호 범위 확인.
5. **DI Context 동기화**: Stage 종료 후 app에 write-back 되는지 (Sweep 2 교훈).

### 라운드 배분 가이드

| 라운드 | 대상 파일 | 초점 |
|--------|----------|------|
| 1-5 | stage2_orchestrator + stage2_context | Stage 2 진입/종료 흐름 |
| 6-10 | stage2_preflight | Arc 재시도 루프, 패치 분기 |
| 11-14 | stage2_validation_pipeline | 검증 체인 계약 |
| 15-18 | stage2_finalizer | quality gate, quota fallback |
| 19-23 | stage3_orchestrator + stage3_context | Blueprint 재시도, PASS_WITH_WARNING |
| 24-28 | stage4_orchestrator + stage4_context | 원고 생성 진입/종료 |
| 29-32 | stage4_interview_round | 인터뷰 루프, ASP 배선 |
| 33-35 | stage4_context_builder + stage4_post_processor | 컨텍스트 조립, 후처리 |
| 36-38 | db_manager | DB 트랜잭션, Lock, 테이블 계약 |
| 39-40 | vec_memory | 벡터 검색, 동기화 |

### 종료 조건
- 40라운드 완료 또는 10라운드 연속 발견 0건.

---

## Phase B (라운드 41-120): 경계값 + 폴백 경로

### 목적
비정상 입력과 엣지케이스에서의 크래시·무한루프·상태 불일치 탐색.

### 필수 읽기 파일 (Phase B 시작 전 전부 읽을 것)

**에이전트 — 재시도 루프 참여자 (7,918 LOC)**:
```
modules/domain/agents/chief_writer.py             (934줄)
modules/domain/agents/chief_writer_context.py      (1,083줄)
modules/domain/agents/chief_writer_quality.py      (483줄)
modules/domain/agents/director.py                  (331줄)
modules/domain/agents/director_continuity.py       (763줄)
modules/domain/agents/director_auditor.py          (1,065줄)
modules/domain/agents/director_ensemble.py         (528줄)
modules/domain/agents/director_grading.py          (680줄)
modules/domain/agents/blueprint_ensemble.py        (707줄)
modules/domain/agents/three_phase_blueprint_generator.py  (572줄)
modules/domain/agents/four_phase_arc_generator.py  (772줄)
```

**검증 파이프라인 (7,596 LOC)**:
```
modules/validation/validation_orchestrator.py      (1,418줄)
modules/validation/continuity_validator.py         (974줄)
modules/validation/scoring_validator.py            (1,027줄)
modules/validation/blocking_validator.py           (193줄)
modules/validation/blocking_validator_entity_checks.py     (476줄)
modules/validation/blocking_validator_consistency_checks.py (377줄)
modules/validation/blocking_validator_scene_checks.py      (455줄)
modules/validation/consistency_validator.py        (597줄)
modules/validation/batch_validator.py              (299줄)
modules/validation/retrospective_validator.py      (365줄)
modules/validation/advisory_validator.py           (181줄)
modules/validation/pre_llm_validator.py            (492줄)
modules/validation/action_scene_evaluator.py       (455줄)
modules/validation/catharsis_timer.py              (223줄)
modules/validation/threshold_helper.py             (22줄)
```

### 탐색 초점

1. **None/빈값 입력**: blueprint=None, manuscript="", score=None, feedback="" 등에서 크래시.
2. **dict 키 누락**: `result.get("key")` 없이 `result["key"]` 직접 접근하는 곳.
3. **타입 불일치**: score가 str/float/int 혼용, list vs dict 혼용.
4. **폴백 경로 정합성**: except 블록에서 상태가 일관되게 유지되는지.
5. **ThreadPoolExecutor**: future.result() 타임아웃, 예외 전파.

### 라운드 배분 가이드

| 라운드 | 대상 파일 | 초점 |
|--------|----------|------|
| 41-48 | chief_writer + context + quality | 앙상블 생성, 피드백 소비, self-critique |
| 49-56 | director + auditor + grading | 채점 계약, 점수 파싱, verdict 판정 |
| 57-62 | director_continuity + director_ensemble | 연속성 검사, 앙상블 선택 |
| 63-68 | blueprint_ensemble + three_phase | Blueprint 생성, 피드백 주입 |
| 69-74 | four_phase_arc_generator | Arc 생성, 재시도 루프 |
| 75-82 | validation_orchestrator + scoring_validator | 검증 오케스트레이션, 채점 |
| 83-90 | continuity_validator + consistency_validator | 연속성/일관성 검증 |
| 91-98 | blocking_validator + 3 sub-checks | 차단 검증 체인 |
| 99-106 | batch_validator + retrospective + advisory | 배치/회고/권고 검증 |
| 107-114 | pre_llm_validator + action_scene_evaluator | 사전검증, 액션 평가 |
| 115-120 | catharsis_timer + threshold_helper | 카타르시스 타이밍, 임계값 |

### 종료 조건
- 80라운드 완료 또는 10라운드 연속 발견 0건.

---

## Phase C (라운드 121-240): 상태 추적 + 장기 안정성

### 목적
반복 실행에서의 상태 누적 오류, 캐시 오염, 메모리 성장 탐색.

### 필수 읽기 파일 (Phase C 시작 전 전부 읽을 것)

**상태 추적 (4,405 LOC)**:
```
modules/domain/agents/state_tracker.py             (1,455줄)
modules/domain/agents/state_tracker_npc.py         (2,006줄)
modules/domain/agents/state_tracker_plots.py       (944줄)
```

**세계 상태 + 팩트 (966 LOC)**:
```
modules/core/world_state.py                        (426줄)
modules/core/fact_ledger.py                        (540줄)
```

**핵심 인프라 (4,107 LOC)**:
```
modules/core/prompt_builder.py                     (959줄)
modules/core/adaptive_retry.py                     (860줄)
modules/core/tree_of_thoughts.py                   (730줄)
modules/core/agent_intelligence.py                 (606줄)
modules/core/constraint_db.py                      (585줄)
modules/core/constants.py                          (785줄)
```

**추가 추적기 (2,455 LOC)**:
```
modules/core/manuscript_enhancer.py                (788줄)
modules/core/foreshadow_tracker.py                 (478줄)
modules/core/diversity_sampler.py                  (510줄)
modules/core/relationship_tracker_npc.py           (410줄)
modules/core/reference_anchor.py                   (351줄)
modules/core/self_reflection.py                    (328줄)
```

**장르 가드 (6,652 LOC)**:
```
modules/core/genre_guards/base_guard.py            (807줄)
modules/core/genre_guards/wuxia_guard.py           (661줄)
modules/core/genre_guards/hunter_guard.py          (865줄)
modules/core/genre_guards/investment_guard.py      (636줄)
modules/core/genre_guards/fantasy_guard.py         (333줄)
modules/core/genre_guards/alt_history_guard.py     (491줄)
modules/core/genre_guards/composer_guard.py        (517줄)
modules/core/genre_guards/cooking_guard.py         (510줄)
modules/core/genre_guards/actor_guard.py           (463줄)
modules/core/genre_guards/medical_guard.py         (468줄)
modules/core/genre_guards/sports_guard.py          (461줄)
modules/core/genre_guards/style_guard.py           (167줄)
modules/core/genre_guards/work_guard.py            (203줄)
```

**기초 에이전트 (2,540 LOC)**:
```
modules/domain/agents/base_agent.py                (1,231줄)
modules/domain/agents/state_extractor.py           (854줄)
modules/domain/agents/consensus_validator.py       (455줄)
```

**엔트리 포인트 (2,987 LOC)**:
```
main_a.py                                          (2,987줄)
```

### 탐색 초점

1. **캐시 무효화**: 소스 데이터 변경 후 캐시가 None으로 리셋되는지 (`_state_cache`, `_cumulative_state_cache`, `_item_timeline_cache`, `_cumulative_bible_cache`).
2. **NPC 이력 누적**: `state_tracker_npc.py`에서 deceased=True NPC가 행동으로 재등장하는 경로.
3. **WorldState/FactLedger 갱신 실패**: 비차단 원칙이 지켜지는지 (갱신 실패 시 파이프라인 중단 금지).
4. **LRU/Anchor 크기 제한**: `LRU 500`, `Anchor 1000`, `MAX_HISTORY_PER_ENTITY=10`, `MAX_SUMMARY_CHARS=20000` 경계에서의 동작.
5. **Guard 다형성**: base_guard → 장르별 guard → WorkGuard → StyleGuard 체인에서 누락/중복 호출.
6. **prompt_builder 캐시**: 에피소드 전환 시 이전 에피소드 프롬프트 잔류.

### 라운드 배분 가이드

| 라운드 | 대상 파일 | 초점 |
|--------|----------|------|
| 121-130 | state_tracker + npc + plots | 상태 추출, NPC 사망 처리, 플롯 추적 |
| 131-138 | world_state + fact_ledger | 세계 상태 문서, 팩트 원장 누적 |
| 139-146 | prompt_builder + constants | 프롬프트 조립, 상수 정합성 |
| 147-154 | adaptive_retry + tree_of_thoughts | 재시도 전략, ToT/ASP/MAD 계약 |
| 155-162 | agent_intelligence + constraint_db | 에이전트 지능, 제약 DB |
| 163-172 | manuscript_enhancer + foreshadow + diversity | 원고 강화, 복선, 다양성 |
| 173-180 | relationship_tracker_npc + reference_anchor + self_reflection | NPC 관계, 앵커, 자기 반성 |
| 181-200 | genre_guards (base + 11종) | Guard 체인 다형성, 오버라이드 정합성 |
| 201-208 | style_guard + work_guard | 커스텀 Guard, YAML 래퍼 |
| 209-220 | base_agent + state_extractor + consensus_validator | 기초 에이전트, 상태 추출 |
| 221-240 | main_a.py | 부트스트랩, 초기화 순서, 종료 경로 |

### 종료 조건
- 120라운드 완료 또는 10라운드 연속 발견 0건.

---

## Phase D (라운드 241-300, 선택적): 인코딩 하드닝

> Phase C까지의 발견 건수가 안정적일 때만 실행.

### 목적
한글 텍스트 파손, 인코딩 불일치, diff 노이즈 탐색. 수정하지 않고 보고만.

### 정책

| 항목 | 기준 |
|------|------|
| 소스/문서 인코딩 | UTF-8 (BOM 없음) |
| 줄바꿈 | 리포지토리 전체 일관 (LF 또는 CRLF, `.gitattributes`에 명시) |
| 혼합 인코딩 | `docs/`, `config/`, `prompts/`, `tests/`에서 금지 |

### 하드 체크 항목

1. `.py/.md/.yaml/.json` 파일에 BOM 존재 여부.
2. `U+FFFD` (replacement character) 존재 여부.
3. 깨진 한글 패턴 (mojibake).
4. 단일 파일 내 혼합 줄바꿈 (LF + CRLF).

### 런타임 안전성 체크

- 파일 I/O에 `encoding="utf-8"` 명시 여부 확인.
- `open()` 호출에서 encoding 파라미터 누락된 곳 보고.

### 대상 파일

```
docs/*.md                          (한글 문서)
config/**/*.yaml
config/**/*.json
projects/**/config/**/*.txt
modules/core/prompt_loader.py      (프롬프트 I/O)
modules/core/db_manager.py         (DB I/O)
modules/core/vec_memory.py         (벡터 I/O)
main_a.py                          (파일 읽기/쓰기)
```

### 종료 조건
- 60라운드 완료 또는 10라운드 연속 발견 0건.

---

## 메트릭 추적 (10라운드마다)

각 Phase 내 10라운드마다 아래를 `docs/codex_findings_sweep300.md` 하단에 기록:

```markdown
## Checkpoint — Round XX

| 메트릭 | 값 |
|--------|-----|
| 누적 Confirmed Bugs | N건 (P0: ?, P1: ?, P2: ?, P3: ?) |
| 누적 Risks | N건 |
| 누적 False Positives Excluded | N건 |
| 누적 Test Gaps | N건 |
| 현 Phase 오탐 비율 | X% |
| 연속 빈 라운드 수 | N |
```

---

## 산출물

| 항목 | 경로 | 비고 |
|------|------|------|
| 발견 문서 (유일한 산출물) | `docs/codex_findings_sweep300.md` | 라운드별 누적 기록 |

리포트 파일 외에는 어떤 파일도 생성·수정하지 마라.

---

## 실행 순서 요약

| Step | Phase | 라운드 | 초점 | 대상 LOC |
|------|-------|--------|------|----------|
| 1 | A | 1-40 | Stage 전환 + 재시도 + DB | 9,438 |
| 2 | B | 41-120 | 경계값 + 폴백 + 검증 | 15,514 |
| 3 | C | 121-240 | 상태 추적 + 캐시 + 장기 안정성 | 27,112 |
| 4 | D | 241-300 | 인코딩 하드닝 (선택적) | 대상별 |

---

## 판단 기준

- 각 Phase 종료 시 오탐 비율 50% 이상이면 → 탐색 전략 재검토 후 재시작.
- P0 발견 시 → 해당 Phase 즉시 종료, 리포트 제출.
- 10라운드 연속 빈 라운드 → 해당 Phase 조기 종료 가능.
