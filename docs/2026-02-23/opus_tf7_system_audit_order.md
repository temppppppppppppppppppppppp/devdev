# OPUS TF-7 — 전체 시스템 감사 오더 (Codex Sweep Plan)

> **작성일**: 2026-02-23
> **작성자**: Claude Sonnet 4.6 (설계) / 실행: Opus TF × 14
> **베이스라인**: 2,377 passed, ruff 0 violations, commit `9f0de73` (TF-6 완료)
> **전제**: TF-1~6 전량 완료. 본 TF-7은 그 이후 미탐지 영역 + 크로스컷 심화 감사.

---

## ★ Codex 실행 수칙 (절대 준수)

### 핵심 규칙
1. **수동 코드 조사만 허용** — `rg`, `freg`, `gfreg`, `grep`, `find` 등 셸 자동 탐색 도구 절대 금지. 반드시 `Read` 도구로 파일을 직접 읽어 검사한다.
2. **수정 금지** — 감사 단계에서는 코드 변경 없음. 발견 사항을 문서화만 한다.
3. **근거 필수** — 모든 이슈는 `파일명:줄번호 + 해당 코드 스니펫`을 첨부한다. "보임", "가능성 있음" 수준의 주관적 판단만 있는 경우 이슈로 등록하지 않는다.
4. **인코딩 주의** — 모든 파일 읽기 시 UTF-8 기준으로 판단. 한글 리터럴·주석이 포함된 파일에서 `ensure_ascii=False` 누락 여부를 명시적으로 확인한다.
5. **수정 금지 품목** — FALSE POSITIVE 판정 이슈는 문서에 `[FP]` 표기 후 종결. 수정 오더에 포함하지 않는다.

### 컨텍스트 컴팩트 복구 절차
1. 이 문서(`docs/2026-02-23/opus_tf7_system_audit_order.md`)를 처음부터 재독한다.
2. 진행 테이블에서 마지막 ✅ TF를 확인한다.
3. 그 다음 미완료 TF부터 이어서 진행한다.
4. **절대 처음부터 다시 시작하지 않는다.**

### 이슈 분류 기준
| 등급 | 기준 |
|------|------|
| CRITICAL | 데이터 유실·무한루프·시스템 크래시 가능 |
| HIGH | silent 품질 저하, 검증 무력화, 잘못된 PASS/REJECT |
| MEDIUM | 운영 관측 사각, 매직넘버, 계약 불일치(비크리티컬) |
| LOW | 스타일·주석·위생 문제 |
| FP | False Positive — 감사 결과 실제 문제 없음 |

### 출력 형식 (각 TF 보고서)
```markdown
## [TF-7-X] — {주제}

### 감사 파일
- `경로/파일명.py` (N줄)

### 발견 이슈

#### [TF-7-X-n] {이슈 제목} ({등급})
**파일**: `경로/파일명.py`
**줄**: L{시작}–L{끝}
**현재 코드**:
```python
{코드 스니펫}
```
**문제**: {설명}
**영향**: {실제 결과}
**권장 수정 방향**: {방향 (코드 아님)}
```

---

## 진행 테이블

| TF | 주제 | 담당 파일 수 | 상태 |
|----|------|-------------|------|
| TF-7-A | Stage0 모듈 교차 버그 | 5 | ⬜ |
| TF-7-B | Context Advisor / Smart Retrieval | 6 | ⬜ |
| TF-7-C | Director 체인 완전성 | 5 | ⬜ |
| TF-7-D | Validation Orchestrator 완전성 | 6 | ⬜ |
| TF-7-E | World State / Fact Ledger / State Delta 삼중 일관성 | 6 | ⬜ |
| TF-7-F | 인코딩·직렬화 안전성 (파일 I/O 전체) | 전체 횡단 | ⬜ |
| TF-7-G | Narrative Diversity / Repetition / Pattern | 4 | ⬜ |
| TF-7-H | Genre Guard 체인 완전성 | 13 | ⬜ |
| TF-7-I | Adaptive Retry / Feedback / Failure Learning | 5 | ⬜ |
| TF-7-J | Emotion / Foreshadow / Karma / Catharsis | 4 | ⬜ |
| TF-7-K | Stage0 Preset ↔ Stage2 StateTracker 연동 | 4 | ⬜ |
| TF-7-L | Quality Dashboard / Metrics / Pass Rate 피드백 루프 | 3 | ⬜ |
| TF-7-M | YAML / Prompt Config 완전성 | config 전체 | ⬜ |
| TF-7-N | 크로스컷 시나리오 스윕 (종단간) | 파이프라인 전체 | ⬜ |

---

## TF-7-A: Stage0 모듈 교차 버그

### 감사 목적
`StageZeroManager` 내 4개 서브모듈(`preset_registry`, `style_extractor`, `reverse_expander`, `story_expander`)과 통합 `__init__.py` 간 계약·상태 공유 일관성. TF-1~6에서 Stage0는 단편적으로만 감사됨. 이 영역의 버그는 모든 신규 프로젝트 초기화에 영향.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/stage0/__init__.py` (581줄) — StageZeroManager
2. `modules/core/stage0/preset_registry.py` (714줄) — 프리셋 스키마 체계
3. `modules/core/stage0/style_extractor.py` (772줄) — 문체 추출
4. `modules/core/stage0/reverse_expander.py` (1131줄) — 역설계 (진정한 역설계)
5. `modules/core/stage0/story_expander.py` (556줄) — 컨셉 → Bible 생성

### 검사 포인트
- [ ] **A-1**: `StageZeroManager.__init__`에서 서브모듈 초기화 순서. `preset_registry` 없이 `style_extractor` 호출 가능한가?
- [ ] **A-2**: `preset_registry.get_preset()` 반환값이 None일 때 호출부에서 None 검사 누락 여부.
- [ ] **A-3**: `reverse_expander.py`에서 원고 파일 읽기 시 `encoding="utf-8"` 명시 여부. 한글 소설 파일이므로 인코딩 오류 발생 가능.
- [ ] **A-4**: `style_extractor.py`에서 LLM 응답 파싱 실패 시 폴백값. `json.loads` 예외 처리 및 스키마 검증.
- [ ] **A-5**: `story_expander.py`에서 NPC 등록 시 `deceased` 필드 기본값. 미설정 시 `deceased=None`이 truthy/falsy 판정 오류 가능.
- [ ] **A-6**: `reverse_expander.py` 역설계 결과가 `StageZeroManager`를 통해 DB에 저장될 때 트랜잭션 보호 여부.
- [ ] **A-7**: 프리셋 `[common] + [genre]` 조합 시 키 충돌(동일 키 중복 정의) 처리 로직.
- [ ] **A-8**: `style_extractor.py` → `StyleGuard` 자동 래핑 경로에서 예외 시 Guard가 None 상태로 등록되는지.
- [ ] **A-9**: `story_expander.py`에서 Bible 구조체 생성 후 필수 키(`MasterBible`, `Characters`, `WorldSettings`) 존재 검증 여부.
- [ ] **A-10**: `reverse_expander.py`의 Arc/Blueprint 역추출 스킵 로직 — 스킵 여부를 결정하는 조건이 명확히 문서화되어 있는가, 아니면 암묵적인가.

### 출력
→ `docs/2026-02-23/opus_tf7_a_audit.md`

---

## TF-7-B: Context Advisor / Smart Retrieval 계약

### 감사 목적
SC-0~6에서 구현된 Smart Context Retrieval 시스템(`context_advisor.py`)과 이를 소비하는 `stage4_context_builder.py`, `stage4_interview_round.py`, 3개 DI 컨텍스트(`stage2_context.py`, `stage3_context.py`, `stage4_context.py`) 간 계약 정합성. TF-5/6에서 부분 감사됐으나 슬롯 오버라이드·캐시 무효화 경로는 미검증.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/context_advisor.py` (675줄) — RetrievalPlan / Slot / Sources
2. `modules/core/stage4_context_builder.py` (570줄) — SC 소비자 메인
3. `modules/core/stage4_interview_round.py` (554줄) — SC 소비자 인터뷰 라운드
4. `modules/core/stage2_context.py` (44슬롯 DI) — SC 배선 확인
5. `modules/core/stage3_context.py` (19슬롯 DI) — SC 배선 확인
6. `modules/core/stage4_context.py` (24슬롯 DI) — SC 배선 확인

### 검사 포인트
- [ ] **B-1**: `RetrievalPlan` 객체가 None일 때 `stage4_context_builder`의 처리. 폴백 경로 존재 여부.
- [ ] **B-2**: `Slot.max_chars` 필드가 0 또는 음수일 때 `stage4_interview_round`의 동작. (TF-6 TF-G-1 패치 후 상태 확인)
- [ ] **B-3**: `Sources` 리스트가 비어 있을 때 SC가 빈 컨텍스트를 반환하는가, 아니면 예외를 던지는가.
- [ ] **B-4**: `context_advisor.py`에서 `plan()` 메서드의 반환 타입이 항상 `RetrievalPlan`을 보장하는지, 아니면 `None`을 반환할 수 있는지.
- [ ] **B-5**: Stage2/3/4 DI 컨텍스트에서 SC 슬롯을 `lazy_init`으로 초기화 시, 두 번 호출될 때 중복 초기화 방어 여부.
- [ ] **B-6**: `stage2_context.py` 44슬롯 중 SC 관련 슬롯과 비SC 슬롯의 초기화 순서 의존성 — 순서가 바뀌면 `AttributeError` 발생 가능성.
- [ ] **B-7**: `context_advisor.py`의 캐시(`_cache` 또는 유사)가 프로젝트 전환 시 무효화되는지.
- [ ] **B-8**: SC 슬롯이 `stage4_context_builder`에서 직접 사용될 때와 `stage4_interview_round`에서 사용될 때 동일한 데이터를 받는지, 또는 독립적으로 계산되는지 (중복 호출 여부).

### 출력
→ `docs/2026-02-23/opus_tf7_b_audit.md`

---

## TF-7-C: Director 체인 완전성

### 감사 목적
Director 관련 5개 모듈(`director_grading.py`, `director_auditor.py`, `director_caching.py`, `director_ensemble.py`, `director_continuity.py`) 간 판정 경계·캐시 정합성·앙상블 결과 처리. TF-5-E에서 Director 판정 경계 결함 1건 HIGH 발견. 잔여 결함 탐색.

### 감사 파일 (순서대로 읽을 것)
1. `modules/domain/agents/director_grading.py` (680줄)
2. `modules/domain/agents/director_auditor.py` (1063줄)
3. `modules/domain/agents/director_caching.py` (175줄)
4. `modules/domain/agents/director_ensemble.py` (534줄)
5. `modules/domain/agents/director_continuity.py` (파일 존재 확인 후 읽기)

### 검사 포인트
- [ ] **C-1**: `director_grading.py`에서 점수 계산 시 NaN/inf 방어 — `float('nan')` 입력 시 비교 연산 결과 불안정.
- [ ] **C-2**: `director_auditor.py`에서 병렬 감사 스레드 결과 수집 시 예외 발생한 Future 처리. `future.exception()` 확인 여부.
- [ ] **C-3**: `director_caching.py`에서 캐시 키 생성 로직 — 에피소드 번호·Arc 번호·전략 조합이 충분히 유일한가. 키 충돌 시 오래된 캐시 히트 가능성.
- [ ] **C-4**: `director_ensemble.py`에서 앙상블 후보가 전부 REJECT될 때 폴백 로직. `None` 반환 또는 예외 중 무엇인가.
- [ ] **C-5**: `director_ensemble.py`에서 `selected_candidate=None` 케이스가 `stage4_interview_round`로 전달될 때 `None` 검사 누락 여부 (크로스컷 TF-5-B-1 연관).
- [ ] **C-6**: `director_continuity.py`에서 Context Caching 활성화 후 캐시 항목 만료 시 재생성 로직 — 만료 감지 실패 시 stale 캐시 사용 위험.
- [ ] **C-7**: `director_grading.py`에서 `scores` dict의 키가 예상 외 문자열일 때 KeyError 방어.
- [ ] **C-8**: `director_auditor.py` ThreadPoolExecutor 내부에서 발생한 예외가 외부로 전파되지 않고 조용히 무시되는 경로.

### 출력
→ `docs/2026-02-23/opus_tf7_c_audit.md`

---

## TF-7-D: Validation Orchestrator 완전성

### 감사 목적
`validation_orchestrator.py`(1522줄)를 중심으로 6개 검증 모듈 간 호출 계약·우회 경로·타입 불일치 전수 검사. TF-5-K에서 required_scenes 최소치 오류, ConsistencyValidator guard 3종 제한 HIGH 발견 — 패치 여부 및 잔여 결함 탐색.

### 감사 파일 (순서대로 읽을 것)
1. `modules/validation/validation_orchestrator.py` (1522줄)
2. `modules/validation/advisory_validator.py` (211줄)
3. `modules/validation/blocking_validator.py` (211줄) + 서브모듈 3개
4. `modules/validation/pre_llm_validator.py` (494줄)
5. `modules/validation/scoring_validator.py` (1271줄)
6. `modules/validation/continuity_validator.py` (993줄)

### 검사 포인트
- [ ] **D-1**: `validation_orchestrator.py`에서 Advisory 검증 결과가 Blocking 검증 입력에 영향을 주는지, 아니면 독립적인지. 결합 시 순서 역전 위험.
- [ ] **D-2**: `advisory_validator.py`의 반환 스키마(`warnings: list[str]` 여부 확인) — 소비자가 `dict["warnings"]` 키 접근 시 KeyError 가능성.
- [ ] **D-3**: `blocking_validator.py`에서 서브모듈 3개(`consistency_checks`, `entity_checks`, `scene_checks`) 중 하나가 예외를 던질 때 나머지 체크가 스킵되는지.
- [ ] **D-4**: `pre_llm_validator.py` V70(POV 일관성) 체크 — D-1(POV 시스템 활성화) 이후 실제로 호출되는지 `validation_orchestrator`에서 확인.
- [ ] **D-5**: `scoring_validator.py`에서 score 합산 시 분모가 0인 경우 ZeroDivisionError 방어.
- [ ] **D-6**: `continuity_validator.py`에서 이전 에피소드 데이터가 없을 때(Episode 1) 빈 참조 처리 — `None` vs 빈 dict 혼용 여부.
- [ ] **D-7**: `validation_orchestrator.py`에서 각 검증기의 반환값을 집계할 때 `None` 반환 vs 빈 dict 혼용 케이스.
- [ ] **D-8**: `blocking_validator_scene_checks.py`에서 `blueprint`가 None/빈 dict일 때 scene 검사가 조용히 PASS되는지 (TF-5 K-2 Cross-TF X-1 연관).
- [ ] **D-9**: `consistency_validator.py` 내부 genre guard 로딩 — `create_genre_guard()` 기반으로 통합됐는지 (TF-5 K-3 패치 확인).

### 출력
→ `docs/2026-02-23/opus_tf7_d_audit.md`

---

## TF-7-E: World State / Fact Ledger / State Delta 삼중 일관성

### 감사 목적
3개 상태 저장소(`world_state.py`, `fact_ledger.py`, `state_delta_tracker.py`)와 `state_tracker.py`, `constraint_db.py`, `reference_anchor.py` 간 동기화 실패·롤백 부분 복구 문제. 에피소드 롤백(D-2 완료) 이후 3개 저장소가 동시에 올바르게 롤백되는지.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/world_state.py` (474줄)
2. `modules/core/fact_ledger.py` (601줄)
3. `modules/core/state_delta_tracker.py` (419줄)
4. `modules/domain/agents/state_tracker.py` (조사 깊이: 롤백/스냅샷 경로 집중)
5. `modules/core/constraint_db.py` (585줄)
6. `modules/core/reference_anchor.py` (351줄)

### 검사 포인트
- [ ] **E-1**: `world_state.py`에서 `rollback_to(ep_num)` 또는 유사 메서드 존재 여부. 없으면 에피소드 롤백 시 WorldState가 복구되지 않는 구조적 문제.
- [ ] **E-2**: `fact_ledger.py`에서 append-only 이력이 실제 롤백 시 "삭제"되는지, 아니면 단순히 "무시"되는지 — 무시라면 이후 읽기에서 stale 팩트 반환 가능.
- [ ] **E-3**: `state_delta_tracker.py`에서 delta가 누적될 때 최대 크기 제한 여부 (TF-6 TF-B 계열 유사 문제).
- [ ] **E-4**: `constraint_db.py`에서 제약 조건 추가 시 에피소드 번호가 기록되는지 — 롤백 시 필터링 가능하려면 필수.
- [ ] **E-5**: `reference_anchor.py`에서 앵커 항목의 에피소드 태깅 여부 — 롤백 후 미래 앵커 참조 차단 로직.
- [ ] **E-6**: `world_state.py`, `fact_ledger.py`, `state_delta_tracker.py` 3개가 동일한 DB 트랜잭션 내에서 커밋되는지, 아니면 개별 커밋인지 — 개별 커밋이면 부분 성공/실패 불일치 가능.
- [ ] **E-7**: `state_delta_tracker.py`의 delta가 `state_tracker.py`의 메인 상태와 분기(diverge)될 수 있는 경로.
- [ ] **E-8**: `fact_ledger.py`에서 NPC `deceased=True` 팩트가 기록된 후 이를 읽는 경로에서 `deceased` 필드가 항상 bool로 역직렬화되는지 (JSON에서 `true` → `True` 변환).

### 출력
→ `docs/2026-02-23/opus_tf7_e_audit.md`

---

## TF-7-F: 인코딩·직렬화 안전성 (횡단 감사)

### 감사 목적
한국어 텍스트가 전체 파이프라인에서 안전하게 처리되는지 횡단 감사. `open()`, `json.dumps()`, `json.loads()`, DB 저장, 파일 출력 경로 전반에서 UTF-8 누락 및 `ensure_ascii` 설정 불일치 탐지. TF-6 실행 수칙에도 명시된 주제이나 전용 TF가 없었음.

### 감사 파일 (우선순위 순)
1. `modules/core/db_manager.py` — DB I/O 핵심 경로
2. `modules/core/project_manager.py` — 파일 저장/로드
3. `modules/core/stage4_post_processor.py` — 카카오/네이버 포맷 출력
4. `modules/core/stage0/reverse_expander.py` — 원고 파일 읽기 (한글 소설)
5. `modules/core/stage0/style_extractor.py` — 원고 스타일 분석 출력
6. `modules/domain/agents/base_agent.py` — JSON 파싱/직렬화 핵심
7. `modules/core/prompt_loader.py` — YAML 로드 (한글 프롬프트)
8. `main_a.py` — UI 출력·파일 입출력

### 검사 포인트
- [ ] **F-1**: `open()` 호출 시 `encoding="utf-8"` 또는 `encoding="utf-8-sig"` 명시 누락 경로. Windows 기본값은 cp949이므로 한글 깨짐 발생 가능.
- [ ] **F-2**: `json.dumps()` 호출 시 `ensure_ascii=False` 누락 — 한글이 `\uXXXX` 이스케이프로 저장되어 가독성 저하 및 외부 비교 오류.
- [ ] **F-3**: `json.loads()` 에서 bytes 타입 입력 처리 — DB에서 읽은 값이 str이 아닌 bytes일 경우 `json.loads(bytes)` Python 3.6+에서는 허용되나 일관성 점검.
- [ ] **F-4**: YAML 로드 시 `yaml.safe_load()` 사용 여부 — `yaml.load()` 단독 사용 시 arbitrary code execution 위험.
- [ ] **F-5**: `stage4_post_processor.py`에서 카카오/네이버 포맷 파일 출력 시 BOM(`\ufeff`) 처리 여부 — 일부 플랫폼은 BOM 없는 UTF-8 요구.
- [ ] **F-6**: `reverse_expander.py`에서 외부 원고 파일 경로 처리 — Windows `\`, Unix `/` 혼용 시 경로 오류.
- [ ] **F-7**: `base_agent.py`에서 LLM 응답을 `json.loads()` 전에 `.encode()/.decode()` 변환 없이 직접 파싱 — 서로게이트 문자(U+D800~U+DFFF) 포함 시 파싱 오류.
- [ ] **F-8**: DB `TEXT` 컬럼에서 읽은 값을 `json.loads()` 시 이중 직렬화 여부 — 이미 dict인데 `json.loads(json.dumps(dict))` 형태로 이중 처리 경로.

### 출력
→ `docs/2026-02-23/opus_tf7_f_audit.md`

---

## TF-7-G: Narrative Diversity / Repetition / Pattern Tracker

### 감사 목적
반복 탐지 3종(`narrative_diversity.py`, `information_diffusion.py`, `pattern_tracker.py`)과 `repetition_guard.py` 간 기능 중복·경합·오탐(False Positive)/미탐(False Negative) 경계 점검. 크로스 에피소드 반복 감지(3-B 완료) 이후 잔여 결함.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/narrative_diversity.py` (592줄)
2. `modules/core/information_diffusion.py` (441줄)
3. `modules/core/pattern_tracker.py` (936줄)
4. `modules/core/repetition_guard.py`

### 검사 포인트
- [ ] **G-1**: `pattern_tracker.py`와 `repetition_guard.py`가 동일한 패턴을 이중으로 탐지하는 경로 — 오케스트레이터에서 두 모듈을 모두 호출한다면 중복 경고 발생 가능.
- [ ] **G-2**: `narrative_diversity.py`에서 다양성 점수 계산 시 에피소드 0~1 구간(초기) 샘플 부족으로 점수 신뢰도 저하 → 잘못된 REJECT 가능성.
- [ ] **G-3**: `information_diffusion.py`에서 "정보 확산" 계산에 사용하는 NPC 목록이 `state_tracker` vs 직접 DB 조회 중 어느 쪽인지 — 불일치 시 stale 데이터 사용.
- [ ] **G-4**: `pattern_tracker.py`에서 패턴 DB 항목의 최대 크기 제한 여부 (TF-6 TF-B 계열 유사).
- [ ] **G-5**: `repetition_guard.py`에서 임베딩 폴백(키워드 방식) 실패 시 최종 폴백이 무엇인지 — PASS인지 REJECT인지 (C-1에서 키워드 폴백 추가됐으나 2차 폴백 미확인).
- [ ] **G-6**: `narrative_diversity.py`에서 장르별 다양성 기준이 동일한지, 아니면 장르별로 다르게 설정 가능한지 — 무협/헌터처럼 전투 반복이 허용되는 장르에서 오탐 위험.
- [ ] **G-7**: 3개 반복탐지 모듈이 `validation_orchestrator.py`에서 순서 보장되어 호출되는지, 아니면 병렬인지 — 병렬 시 한 모듈의 결과가 다른 모듈 입력에 영향을 줄 수 없음 확인.

### 출력
→ `docs/2026-02-23/opus_tf7_g_audit.md`

---

## TF-7-H: Genre Guard 체인 완전성

### 감사 목적
10종 장르 Guard + WorkGuard + StyleGuard, 총 13개 Guard 체인 순서·예외 처리·폴백 정합성 전수 검사. TF-5 H에서 구현/적용 일관성 HIGH 1건 발견 — 패치 여부 확인 및 잔여 결함 탐색.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/genre_guards/base_guard.py`
2. `modules/core/genre_guards/work_guard.py`
3. `modules/core/genre_guards/style_guard.py`
4. `modules/core/genre_guards/alt_history_guard.py`
5. `modules/core/genre_guards/composer_guard.py`
6. `modules/core/genre_guards/medical_guard.py`
7. `modules/core/genre_guards/sports_guard.py`
8. `modules/core/genre_guards/actor_guard.py`
9. `modules/core/genre_guards/cooking_guard.py`
10. `modules/core/genre_guards/wuxia_guard.py`
11. `modules/core/genre_guards/hunter_guard.py`
12. `modules/core/genre_guards/fantasy_guard.py`
13. `modules/core/genre_guards/investment_guard.py`

### 검사 포인트
- [ ] **H-1**: `base_guard.py`의 `check()` 메서드 서명 — 모든 하위 Guard가 동일한 서명으로 오버라이드하는지. 서명 불일치 시 `super().check()` 호출 체인 파괴.
- [ ] **H-2**: `work_guard.py`에서 YAML 로드 실패 시 Guard가 None이 되는지, 아니면 통과 Guard(no-op)로 폴백하는지.
- [ ] **H-3**: `style_guard.py`에서 StyleGuard 래핑 실패(D-3 자동 생성) 시 예외 처리. 스타일 분석 LLM 응답이 빈 dict일 때.
- [ ] **H-4**: Guard 체인 순서 — Genre → Work → Style 순서가 모든 호출 경로에서 일관되게 유지되는지.
- [ ] **H-5**: 사망한 NPC(`deceased=True`)가 장르 가드 체크 대상 NPC 목록에 포함되는지 — 사망 NPC가 행동으로 등장하면 REJECT 규칙(대원칙 4)과의 정합성.
- [ ] **H-6**: `investment_guard.py`, `wuxia_guard.py`처럼 도메인 전문 지식이 필요한 Guard에서 하드코딩된 용어 목록의 완전성 — 누락 용어로 인한 미탐.
- [ ] **H-7**: 장르가 복합적(예: 무협+투자)일 때 두 Guard가 모두 활성화되는지 로직 확인.
- [ ] **H-8**: Guard 결과를 `validation_orchestrator`로 전달할 때 `warnings`와 `errors`의 분류가 일관되는지.
- [ ] **H-9**: `ConsistencyValidator` 내부 guard 로딩이 `create_genre_guard()` 기반으로 통합됐는지 (TF-5 K-3 패치 확인).

### 출력
→ `docs/2026-02-23/opus_tf7_h_audit.md`

---

## TF-7-I: Adaptive Retry / Feedback / Failure Learning 피드백 루프

### 감사 목적
`adaptive_retry.py`, `feedback_system.py`, `failure_learning.py`, `reflexion_manager.py`, `pass_rate_monitor.py` 간 피드백 루프 완결성. 실패 학습이 실제로 다음 시도에 반영되는지, 또는 데이터만 쌓이고 미활용되는지.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/adaptive_retry.py` (858줄)
2. `modules/core/feedback_system.py` (853줄)
3. `modules/core/failure_learning.py` (367줄)
4. `modules/core/reflexion_manager.py` (225줄)
5. `modules/core/pass_rate_monitor.py` (550줄)

### 검사 포인트
- [ ] **I-1**: `adaptive_retry.py`에서 `_failures` 리스트 무한 성장 (TF-5 R30 미패치 확인).
- [ ] **I-2**: `adaptive_retry.py`의 재시도 지연(backoff) 계산에서 overflow 방어 — `2**n` 계산 시 n이 크면 메모리 이슈.
- [ ] **I-3**: `failure_learning.py`에서 학습된 패턴이 실제로 `adaptive_retry.py` 또는 `base_agent.py`에 피드백되는지, 아니면 기록만 되는지.
- [ ] **I-4**: `reflexion_manager.py`에서 Reflexion 루프 종료 조건 — 개선 없이 무한 반복 방어.
- [ ] **I-5**: `feedback_system.py`에서 피드백 항목이 특정 에이전트에만 전달되는지 확인 — 전역 피드백이 무관한 에이전트에 영향을 줄 가능성.
- [ ] **I-6**: `pass_rate_monitor.py`에서 전략별 통과율 계산 시 샘플 수 부족 구간(초기 에피소드) 처리 — 1~2개 샘플으로 100%/0% 극단값 발생 가능.
- [ ] **I-7**: `pass_rate_monitor.py`의 전략 통과율이 실제 Director 전략 선택에 연결되는지 (D-4 완료 이후 배선 확인).
- [ ] **I-8**: `feedback_system.py`에서 피드백 로그 `deque` 상한 설정 여부 (TF-6 TF-B-3 `data_collector.py` 패치와 유사 패턴).

### 출력
→ `docs/2026-02-23/opus_tf7_i_audit.md`

---

## TF-7-J: Emotion / Foreshadow / Karma / Catharsis 시스템

### 감사 목적
독자 대리만족 프레임워크(D 완료) 관련 4개 모듈의 배선·DB 저장·수명주기 관리. 감사 TF가 없었던 영역.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/emotion_tracker.py` (397줄)
2. `modules/core/foreshadow_tracker.py` (544줄)
3. `modules/core/karma_service.py` (24줄) — 매우 짧음, 스텁 여부 확인
4. `modules/validation/catharsis_timer.py`

### 검사 포인트
- [ ] **J-1**: `emotion_tracker.py`에서 감정 상태가 에피소드별로 스냅샷 저장되는지, 아니면 인메모리 누적만인지 — 롤백 시 감정 상태 복구 가능 여부.
- [ ] **J-2**: `foreshadow_tracker.py`에서 복선 항목이 "회수됨"으로 표시될 때 에피소드 번호 기록 — 롤백 후 미회수 복선으로 되돌아가야 함.
- [ ] **J-3**: `karma_service.py` 24줄 — 실제 구현인지 스텁인지 확인. 스텁이라면 카르마 시스템이 미작동 중.
- [ ] **J-4**: `catharsis_timer.py`에서 카타르시스 타이밍 계산에 `ep_count`가 0일 때 ZeroDivisionError 방어.
- [ ] **J-5**: 4개 모듈이 `stage4_post_processor.py` 또는 `director.py`에서 실제로 호출되는지 — 구현됐으나 파이프라인에 배선되지 않은 "dead feature" 여부.
- [ ] **J-6**: `emotion_tracker.py`와 `foreshadow_tracker.py` 간 데이터 공유 — 감정 고조와 복선 회수가 동기화되어야 한다면 결합 여부 확인.

### 출력
→ `docs/2026-02-23/opus_tf7_j_audit.md`

---

## TF-7-K: Stage0 Preset ↔ Stage2 StateTracker 연동

### 감사 목적
Stage0에서 동적으로 활성화된 장르 프리셋이 Stage2 `StateTracker`와 `stage2_preflight.py`에 올바르게 전달되는지. MEMORY.md에 "Stage 0 ↔ Stage 2 연동"이 완료로 표기되어 있으나 세부 계약 검증.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/stage0/preset_registry.py` (714줄) — `get_active_presets()` 인터페이스
2. `modules/core/stage0/__init__.py` (581줄) — StageZeroManager에서 Stage2로 전달 경로
3. `modules/domain/agents/state_tracker.py` (PresetRegistry 참조 부분 집중)
4. `modules/core/stage2_preflight.py` (637줄) — preflight 분석에서 프리셋 활용

### 검사 포인트
- [ ] **K-1**: `preset_registry.get_active_presets()` 반환 타입 — `list[str]`, `list[dict]`, `dict` 중 어느 것인가? 소비자가 기대하는 타입과 일치하는가?
- [ ] **K-2**: `state_tracker.py`에서 PresetRegistry를 참조할 때 — 직접 객체 참조인지, 문자열 목록을 받는지. 직접 참조라면 순환 의존 위험.
- [ ] **K-3**: Block 30에서 새 장르가 감지되어 프리셋이 추가될 때 이미 생성된 Arc/Blueprint를 소급 적용하는 메커니즘이 있는지, 없는지.
- [ ] **K-4**: `stage2_preflight.py`에서 프리셋 기반 NPC 추적 필드(13개 → 17~19개)가 실제로 검증 조건에 반영되는지, 아니면 프리셋과 독립적으로 고정 스키마를 사용하는지.
- [ ] **K-5**: 프리셋이 DB에 저장되는지, 아니면 세션 인메모리 전용인지 — 세션 재시작 후 프리셋 복원 가능 여부.

### 출력
→ `docs/2026-02-23/opus_tf7_k_audit.md`

---

## TF-7-L: Quality Dashboard / Metrics / Pass Rate 피드백 루프

### 감사 목적
TF-5 L-1에서 발견된 "Stage4 결과가 `quality_dashboard`에 기록되지 않아 경보 체인 공회전" 패치 여부 확인 + 3개 모듈 간 데이터 흐름 완결성 재감사.

### 감사 파일 (순서대로 읽을 것)
1. `modules/core/quality_dashboard.py` (1100줄)
2. `modules/core/metrics_collector.py` (478줄)
3. `modules/core/pass_rate_monitor.py` (550줄)

### 추가 확인
- `modules/core/stage4_post_processor.py` — `quality_dashboard.record_validation()` 호출 여부 (TF-5 L-1 패치 확인)
- `modules/core/stage2_finalizer.py` — `quality_dashboard` 배선 여부

### 검사 포인트
- [ ] **L-1**: `stage4_post_processor.py`에서 PASS/REJECT 확정 지점에 `quality_dashboard.record_validation(stage=4)` 배선이 추가됐는지 (TF-5 L-1 패치 확인).
- [ ] **L-2**: `quality_dashboard.py`에서 stage별 집계 시 `stage=4` 케이스가 누락되어 있는지.
- [ ] **L-3**: `metrics_collector.py`와 `quality_dashboard.py`의 데이터가 중복 기록되는지 — 동일 이벤트를 두 모듈이 각각 기록하면 집계 오류.
- [ ] **L-4**: `quality_dashboard.py`에서 경보(alert) 발동 임계값이 외부화되어 있는지, 하드코딩인지 (TF-6 TF-G 계열 연관).
- [ ] **L-5**: `pass_rate_monitor.py`에서 저장된 전략별 통과율이 `quality_dashboard` 경보와 연동되는지, 독립적으로 운영되는지.
- [ ] **L-6**: `metrics_collector.py`에서 수집하는 지표 항목 목록과 실제 사용 경로 확인 — 기록만 되고 읽히지 않는 "dead metric" 여부.

### 출력
→ `docs/2026-02-23/opus_tf7_l_audit.md`

---

## TF-7-M: YAML / Prompt Config 완전성

### 감사 목적
43개 외부화된 프롬프트 YAML + `system.yaml` + `validation.yaml` + `settings.json`/`models.yaml` 전반의 키 정합성·미사용 키·하드코딩 잔존 감사.

### 감사 파일 (순서대로 읽을 것)
1. `config/system.yaml` — 시스템 설정
2. `config/settings/validation.yaml` — 임계값 외부화
3. `config/settings.json` — 레거시 설정 여부
4. `modules/core/prompt_loader.py` — YAML 로더 싱글톤
5. `config/prompts/` 디렉터리 내 주요 YAML 파일 샘플 (전량 읽기 어려우면 대표 10개)

### 검사 포인트
- [ ] **M-1**: `validation.yaml`에 TF-6 TF-G에서 외부화한 새 키(`smart_retrieval.slot_max_chars_default`, `scope.min_beats_floor` 등)가 실제로 추가됐는지.
- [ ] **M-2**: `prompt_loader.py` 싱글톤이 YAML 파일 변경 후 캐시 무효화 없이 stale 프롬프트를 반환하는지 — 운영 중 YAML 수정 시 리스타트 필요 여부 문서화.
- [ ] **M-3**: `config/settings.json`이 `system.yaml`과 중복 설정을 가지고 있다면 어느 쪽이 우선인지 명확하지 않은 경우.
- [ ] **M-4**: YAML 프롬프트에서 `{변수명}` 형식 플레이스홀더가 코드에서 실제로 치환되지 않고 그대로 LLM에 전달되는 경로.
- [ ] **M-5**: `system.yaml`에 `retry.director_max_attempts`가 있고 Stage4 루프가 이 값을 실제로 읽는지 (TF-5 L-3 패치 확인).
- [ ] **M-6**: `models.yaml`에 정의된 모델 ID가 `base_agent.py`의 실제 호출 모델 ID와 일치하는지.
- [ ] **M-7**: YAML 파일 내 한글 주석/값이 UTF-8로 저장됐는지 (BOM 없는 UTF-8 요구).

### 출력
→ `docs/2026-02-23/opus_tf7_m_audit.md`

---

## TF-7-N: 크로스컷 시나리오 스윕 (종단간)

### 감사 목적
특정 경계 시나리오를 파이프라인 전체(Stage 0 → 2 → 3 → 4 → PostProcessor)에 투과시켜 각 스테이지별 처리를 추적. 이전 TF들이 모듈 단위였다면, 본 TF는 **데이터 흐름 축**으로 접근. 기존 `codex_crosscut_sweep100_plan.md`의 고밀도 버전.

### 검사 시나리오 (10개)

| # | 시나리오 | 시작점 | 추적 경로 |
|---|---------|--------|----------|
| N-01 | Episode 1 초기 진입 — 이전 원고/Arc 전무 | `stage4_context_builder` | `lookback_digest` → `chief_writer_context` → `director` |
| N-02 | 에피소드 롤백(D-2) 후 NPC 상태 재진입 | `project_service.rollback_episode()` | `state_tracker` → `fact_ledger` → `world_state` → `stage4_context_builder` |
| N-03 | 사망 NPC(`deceased=True`)가 Arc에 등장 시도 | `analyst.py` → `stage2_validation_pipeline` | `fact_ledger` → `blocking_validator` → REJECT 경로 |
| N-04 | 장르 전환 감지 — Block 30에서 [fantasy] 추가 | `preset_registry` | `state_tracker` → `stage2_preflight` → Guard 체인 |
| N-05 | LLM Arc 응답 빈 dict `{}` | `four_phase_arc_generator` | `stage2_validation_pipeline:_validate_flow_guard` → REJECT → 재시도 |
| N-06 | 모든 Director 전략 REJECT (5라운드) | `stage4_interview_round` | `adaptive_retry` → `failure_learning` → 폴백 원고 |
| N-07 | Blueprint `scenes=None` 관통 | `blueprint_ensemble` | `stage4_context_builder:_build_scene_context` → `blocking_validator_scene_checks` |
| N-08 | 상태 누적 1000에피소드 — 장기 실행 | `state_tracker.resolved_plots` | TF-6 B 패치 후 상한 동작, `all_reveals`, `feedback_log` 상한 확인 |
| N-09 | `ep_count=1` 단일 에피소드 아크 | `stage2_validation_pipeline` | TF-6 E 패치 후 PASS 확인, beat_sequence 길이 검증 |
| N-10 | 멀티스레드 Arc 생성 중 1개 타임아웃 | `arc_ensemble` | Future cancel → `stage2_orchestrator` 복원 맵 → 부분 성공 처리 |

### 검사 방법
- 각 시나리오에 대해 **시작 파일을 Read 도구로 직접 읽고** 해당 함수를 추적
- 코드 분기를 따라 다음 호출 파일로 이동하여 동일하게 Read
- 각 스테이지에서 경계 데이터 처리 누락·타입 불일치·예외 미처리 경로 기록
- **이미 TF-6에서 패치된 항목**(N-08, N-09)은 패치 코드 적용 여부만 확인

### 출력
→ `docs/2026-02-23/opus_tf7_n_audit.md`

---

## 종합 보고서 형식

각 TF-7-A~N 완료 후 종합 보고서 작성:

→ `docs/2026-02-23/opus_tf7_consolidated_report.md`

포함 내용:
1. 전체 이슈 집계 표 (등급별 건수)
2. TF별 분포 표
3. P0/P1/P2 우선순위 제안
4. Cross-TF 이슈 (복수 TF에서 관련된 이슈)
5. TF-5/6 패치 회귀 확인 결과

---

## 패치 오더 연계

종합 보고서 검토 후, 별도 문서 작성:

→ `docs/2026-02-23/opus_tf7_patch_order.md`

형식: TF-6 패치 오더(`opus_tf6_patch_order.md`)와 동일한 구조.
패치 오더는 **본 감사 완료 후 별도 Codex 실행**으로 처리.

---

## 베이스라인 검증

감사 시작 전·후 확인:
```bash
pytest tests/ -q           # 2,377+ passed 유지 확인
python -m ruff check modules/ tests/ main_a.py   # 0 violations
python -m ruff format --check modules/ tests/ main_a.py
```

감사 단계에서는 코드 변경이 없으므로 테스트는 **감사 오더 시작 전 1회**만 실행.
