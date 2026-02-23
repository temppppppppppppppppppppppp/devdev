# TF-6: 전체 시스템 디버깅 감사 — 롤백·상태·견고성

> **작성**: Opus TF (2026-02-23)
> **목적**: TF-5(32건 패치) 이후 미진 영역 정밀 감사
> **대상**: 롤백 원자성, 상태 누적, 트랜잭션 안전성, LLM 응답 견고성, 엣지 케이스
> **실행**: Codex
> **감리**: Opus TF
> **베이스라인**: 2,377 passed, ruff 0 violations, commit `5e7f7c0`

---

## 사전 조사 결과 요약 (Opus 스캔)

| 영역 | 결과 | 발견 |
|------|------|------|
| 인코딩 (UTF-8/cp949) | **CLEAN** | open() 전량 encoding= 보유, yaml.safe_load 전용, ensure_ascii=False 적용 |
| None-Safety | **CLEAN** | .get() 체인 전량 디폴트 보유, Optional 반환 전량 체크됨 |
| 롤백 원자성 | **HIGH 1건 + MEDIUM 3건** | HUD 미복원, VecMemory 미롤백, resolved_plots 무한 누적, StateTracker 미초기화 |
| 트랜잭션 안전성 | **MEDIUM 1건** | 중첩 트랜잭션 진입점 1회 체크, 예외 경로 변이 시 위험 |
| 상태 누적 | **LOW 2건** | all_reveals/cumulative_bible 무한 성장, 500화+ 시나리오 |

---

## Codex 실행 규칙 (필독 — 반드시 준수)

### 핵심 원칙
- **수동 중단 절대 금지** — TF-A부터 TF-H까지 **전량 완료 후** 종합 보고서 작성까지 한 번에 끝낸다
- **중간 보고 금지** — 사용자에게 "여기까지 했습니다" 식의 중간 보고 없이 끝까지 진행
- **자동 탐색 금지** — 아래 TF별 지정 파일만 분석, 범위 밖 파일 탐색하지 않음

### 인코딩 규칙
- **모든 파일 I/O는 UTF-8** — 보고서, 코드, 테스트 파일 작성 시 반드시 UTF-8
- **한글 깨짐 절대 금지** — 파일명, 파일 내용, 커밋 메시지 모두 한글이 정상 출력되어야 함
- **ensure_ascii=False** — JSON 출력 시 반드시 적용
- Windows 환경임을 인지하고, 경로 구분자나 인코딩 문제 주의

### 진행 관리
1. **각 TF 완료 시** → 이 문서의 진행 테이블 업데이트 (상태: ✅ 완료 + 발견 건수)
2. **각 TF별 독립 보고서** → `docs/2026-02-23/opus_tf6_{tf_letter}_audit.md`에 작성
3. **전체 완료 후** → `docs/2026-02-23/opus_tf6_consolidated_report.md` 종합 보고서 작성

### 컨텍스트 컴팩트 복구 절차
> 컨텍스트가 압축되어 이전 작업 내용이 사라졌을 때:
1. 이 문서(`docs/2026-02-23/opus_tf6_system_audit_order.md`)를 **처음부터** 다시 읽는다
2. 진행 테이블에서 **마지막 ✅ 완료된 TF**를 확인한다
3. 그 다음 미완료 TF부터 이어서 진행한다
4. 이미 작성된 보고서 파일이 있으면 읽어서 중복 작업 방지
5. **절대 처음부터 다시 시작하지 않는다** — 완료된 TF는 건드리지 않음

### 발견 사항 형식
- **ID**: `[TF-X-N]` (예: TF-A-1, TF-A-2)
- **심각도**: CRITICAL / HIGH / MEDIUM — 코드 경로, 영향 범위, 재현 조건 명시
- **패치 제안**: 각 발견에 수정 전/후 코드 스니펫 포함
- **테스트**: 각 패치에 대응 테스트 케이스 명시

### 금지 사항
- `git commit`, `git push` 등 Git 조작 금지 (감사만 수행)
- 소스 코드 직접 수정 금지 (보고서에 수정안만 기록)
- 기존 테스트 파일 수정 금지
- 진행 테이블 외의 이 문서 내용 수정 금지

---

## 진행 테이블

| TF | 대상 | 상태 | 발견 |
|----|------|------|------|
| TF-A | 롤백 원자성 | ✅ 완료 | HIGH 1, MEDIUM 2 |
| TF-B | 상태 누적 / 메모리 성장 | ✅ 완료 | MEDIUM 3 |
| TF-C | 트랜잭션 안전성 | ✅ 완료 | MEDIUM 2 |
| TF-D | LLM 응답 견고성 | ✅ 완료 | MEDIUM 1 |
| TF-E | 엣지 케이스 경계값 | ✅ 완료 | HIGH 1 |
| TF-F | 크로스-모듈 계약 검증 | ✅ 완료 | MEDIUM 1 |
| TF-G | 임계값/매직넘버 외부화 | ✅ 완료 | MEDIUM 4 |
| TF-H | 데드코드 / 위생 정리 | ✅ 완료 | MEDIUM 3 |

---

## TF-A: 롤백 원자성 (Rollback Atomicity)

### 배경
TF-5에서 F-1/F-2(`_safe_commit()` 반환값 무시)를 패치했으나, 롤백 실패 시 **인메모리 상태 복원** 문제는 미해결.

### 감사 파일 (4개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/core/services/project_service.py` | ~230 | rollback_episode() 전체 흐름 |
| `modules/core/vec_memory.py` | ~950 | delete_episodes_from() |
| `main_a.py` | L2770~2810 | _rollback_episode() 호출부 |
| `modules/core/db_manager.py` | L1290~1380 | save_episode_stack() 트랜잭션 |

### 알려진 이슈 (Opus 스캔 선발견)

**[A-HINT-1] HUD 상태 미복원 (HIGH)**
- `project_service.py` L122-152: HUD(master_bible) 인메모리 갱신 → L188 커밋 실패 시 인메모리는 이미 변경됨
- 기대: 커밋 실패 시 HUD 원복 또는 커밋 성공 후에만 인메모리 반영

**[A-HINT-2] VecMemory 삭제 실패 시 미롤백 (MEDIUM)**
- `vec_memory.py` L877-901: except 블록에서 `return 0`만 하고 `self._conn.rollback()` 미호출
- SQLite ACID가 커밋 안 된 변경을 자동 롤백하긴 하나 명시적 rollback() 누락

**[A-HINT-3] StateTracker 미초기화 (MEDIUM)**
- `project_service.py` L214 `project._load_from_db()` 호출하지만 StateTracker가 메모리에 별도 보유 중
- 롤백 후 StateTracker.npc_registry에 삭제된 에피소드의 NPC 참조 잔존 가능

### 추가 조사 지시

1. `project_service.py`에서 `_safe_commit()` 실패 시 **모든 인메모리 변경이 원복되는지** 확인
2. `rollback_episode()`의 5단계(HUD→SQL→커밋→파일→벡터) 중 **3단계 실패 시 1-2단계 원복 경로** 존재 여부
3. `main_a.py` `_rollback_episode()` 에서 rollback 후 **state_tracker 재초기화** 여부 확인
4. `vec_memory.py` `delete_episodes_from()` — 공유 모드 vs 독립 모드에서 **sync_status 롤백 일관성**

---

## TF-B: 상태 누적 / 메모리 성장 (State Accumulation)

### 배경
LRU 캐시가 있는 곳(entity_registry=500, embed_cache=128, bible_cache=5)은 안전하나, **무한 성장** 구조가 존재.

### 감사 파일 (5개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/domain/agents/state_tracker.py` | ~1,527 | resolved_plots, tracking_fields |
| `modules/domain/agents/state_tracker_plots.py` | ~300 | extract_resolved_plots_from_arc() |
| `modules/core/db_manager.py` | L820~911 | get_cumulative_bible(), all_reveals |
| `modules/domain/agents/state_tracker_npc.py` | ~2,008 | NPC 상태 누적 구조 |
| `modules/core/data_collector.py` | ~400 | 수집 데이터 캐시 |

### 알려진 이슈 (Opus 스캔 선발견)

**[B-HINT-1] resolved_plots 무한 누적 (MEDIUM)**
- `state_tracker.py` L132: `resolved_plots: list[dict] = []` — 크기 제한 없음
- 500화 시 ~2,500 항목(250KB) 예상, 메모리 압박 가능

**[B-HINT-2] all_reveals 무한 성장 (LOW)**
- `db_manager.py` L842-901: cumulative_bible의 `all_reveals` 리스트에 에피소드마다 append
- 1,000화 시 ~3,000 항목(150KB)

### 추가 조사 지시

1. `state_tracker.py`에서 **무한 성장하는 리스트/딕셔너리** 전수 조사 (resolved_plots 외)
2. `state_tracker_npc.py`에서 **NPC별 이벤트 이력**이 누적만 되고 정리 안 되는 구조 확인
3. `db_manager.py` `get_cumulative_bible()` — items, npcs, dead_npcs, relationships 각각 **에비싱/정리 로직** 존재 여부
4. `data_collector.py` — 수집 결과 캐시에 **크기 제한** 있는지 확인
5. **500화 시뮬레이션**: 각 누적 구조의 예상 크기 계산 (항목 수 × 평균 바이트)

---

## TF-C: 트랜잭션 안전성 (Transaction Safety)

### 배경
DBManager는 RLock + `in_transaction` 체크로 중첩 트랜잭션을 관리하나, 예외 경로에서 트랜잭션 상태 불일치 가능성 존재.

### 감사 파일 (3개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/core/db_manager.py` | L1040~1080, L1290~1520 | begin/commit/rollback, save_episode_stack, transaction() |
| `modules/core/vec_memory.py` | L400~500, L870~900 | 공유 모드 트랜잭션 |
| `modules/core/services/project_service.py` | L40~230 | _safe_commit() 호출 패턴 |

### 알려진 이슈 (Opus 스캔 선발견)

**[C-HINT-1] 중첩 트랜잭션 진입 체크 1회 (MEDIUM)**
- `db_manager.py` L1300: `nested_transaction = self.conn.in_transaction` — 진입 시 1회만 체크
- 하위 호출에서 rollback() 발생 시 상위는 여전히 `nested=False`로 commit() 시도 → 빈 트랜잭션 커밋

### 추가 조사 지시

1. `db_manager.py`에서 `begin()`/`commit()`/`rollback()` 호출 **전체 콜 그래프** 추적
2. `transaction()` 컨텍스트매니저가 **예외 시 rollback 보장**하는지 확인
3. `save_episode_stack()` 내부에서 호출하는 **모든 DB 메서드**가 자체 트랜잭션을 열지 않는지 확인
4. `_safe_commit()` 가 **트랜잭션 외부에서 호출**되는 경우 존재 여부 (no-op commit)
5. ThreadPoolExecutor 콜백에서 **DB 접근 시 락 획득** 여부

---

## TF-D: LLM 응답 견고성 (LLM Response Robustness)

### 배경
모든 에이전트가 LLM JSON 응답을 파싱하나, 필수 키 누락/타입 불일치/빈 응답 등 엣지 케이스 처리 수준이 불균일.

### 감사 파일 (8개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/domain/agents/base_agent.py` | ~1,362 | _extract_json_robust(), _ask() 에러 핸들링 |
| `modules/domain/agents/analyst.py` | ~1,475 | arc_data 파싱, _load_genre_libraries |
| `modules/domain/agents/arc_critic.py` | ~350 | result["scores"] 직접 접근 |
| `modules/domain/agents/arc_corrector.py` | ~450 | response["corrected_content"] 파싱 |
| `modules/domain/agents/chief_writer.py` | ~854 | 원고 생성 응답 처리 |
| `modules/domain/agents/director.py` | ~700 | PASS/REJECT 판정 파싱 |
| `modules/domain/agents/continuity_arc.py` | ~750 | 연속성 검증 결과 파싱 |
| `modules/domain/agents/four_phase_arc_generator.py` | ~600 | 4-Phase 아크 파싱 |

### 조사 지시

1. `base_agent.py` `_extract_json_robust()` — **어떤 실패 모드**에서 None/빈 dict 반환하는지 전수 확인
2. 각 에이전트의 LLM 응답 파싱에서 **필수 키 누락 시 동작** 확인:
   - `analyst.py`: arc_data에 `tactical_doc`, `beat_sequence` 누락 시
   - `arc_critic.py`: `result["scores"]` 키 없을 때 KeyError 가능성 (L189)
   - `arc_corrector.py`: `response["corrected_content"]` 키 없을 때
   - `director.py`: PASS/REJECT 판정문 없을 때
   - `chief_writer.py`: 원고 텍스트 없을 때
3. **빈 문자열 응답** ("") 또는 **빈 JSON** ({}) 반환 시 각 에이전트의 행동
4. **부분 JSON** (중간에 잘린 응답) 처리 — `_extract_json_robust()`의 복구 능력 검증
5. LLM이 **예상 외 타입** 반환 시 (str 대신 list, dict 대신 str 등) 처리 여부

---

## TF-E: 엣지 케이스 경계값 (Boundary Edge Cases)

### 배경
TF-5에서 ep1(콜드스타트)과 ep30+(핫패스)를 점검했으나, 극단적 경계값(단일 에피소드 아크, 200화+, 장르 전환)은 미검증.

### 감사 파일 (7개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/core/stage2_orchestrator.py` | ~907 | 단일 에피소드 아크(ep_count=1) |
| `modules/core/stage2_preflight.py` | ~637 | arc_no=0 또는 음수 |
| `modules/core/stage4_orchestrator.py` | ~883 | ep=1에서 prev_ending 없음 |
| `modules/core/stage4_context_builder.py` | ~570 | 빈 NPC 목록, 빈 blueprint |
| `modules/domain/agents/state_tracker.py` | ~1,527 | ep=200+ 스냅샷 크기 |
| `modules/core/stage3_orchestrator.py` | ~500 | 빈 arc, beat_sequence=[] |
| `modules/core/stage0/__init__.py` | ~400 | 장르 전환 시 기존 데이터 충돌 |

### 조사 지시

1. **단일 에피소드 아크** (ep_count=1):
   - `stage2_orchestrator.py`: beat_sequence가 1개일 때 flow_guard 통과 여부
   - `stage2_validation_pipeline.py`: ep_count=1에서 비트 수 검증 (비트 수 < ep_count이면 REJECT?)
2. **Arc 번호 경계**:
   - arc_no=0: 첫 아크 생성 시 이전 아크 참조 코드가 인덱스 에러 발생하는지
   - arc_no가 매우 클 때(100+): 성능 저하 여부
3. **에피소드 1 콜드스타트**:
   - `stage4_context_builder.py`: prev_ending=""일 때 컨텍스트 빌드 정상 동작
   - `stage4_orchestrator.py`: 이전 에피소드 참조 코드가 ep=1에서 빈 결과 처리
4. **빈 데이터 입력**:
   - NPC 목록이 []일 때 Stage4 interview round 동작
   - blueprint.scene_breakdown이 []일 때 Stage4 컨텍스트 빌더
   - master_bible이 {}일 때 Stage2 preflight
5. **200화+ 대량 데이터**:
   - get_manuscripts_range() 200개 에피소드 조회 시 메모리/시간
   - cumulative_bible 계산 비용

---

## TF-F: 크로스-모듈 계약 검증 (Cross-Module Contracts)

### 배경
TF-5에서 scene_breakdown dict/list 불일치(B-3)와 items_acquired str(dict) 문제(J-1/J-2)를 패치했으나, 유사 패턴이 다른 모듈 간 경계에 잔존할 수 있음.

### 감사 파일 (6개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/core/stage2_finalizer.py` | ~535 | 아크 출력 → Stage3 입력 계약 |
| `modules/core/stage3_orchestrator.py` | ~500 | 블루프린트 출력 → Stage4 입력 계약 |
| `modules/core/stage4_context.py` | ~300 | Stage4Context 슬롯 타입 계약 |
| `modules/core/stage2_context.py` | ~350 | Stage2Context 슬롯 타입 계약 |
| `modules/domain/agents/block_enricher.py` | ~400 | enriched_block 출력 형식 |
| `modules/validation/blocking_validator.py` | ~400 | 입력 타입 가정 |

### 조사 지시

1. **Stage2 → Stage3 계약**:
   - `stage2_finalizer.py` 출력의 `refined_arc` 딕셔너리 키 → `stage3_orchestrator.py`가 기대하는 키 일치 여부
   - 특히 `state_changes`, `hybrid_composition`, `joint_docs` 타입 계약
2. **Stage3 → Stage4 계약**:
   - blueprint 딕셔너리의 필수 키 → Stage4Context 슬롯 매핑 일치 여부
   - `scene_breakdown` 외에 타입 불일치 가능한 필드 탐색
3. **block_enricher 출력 계약**:
   - enriched_block의 키/타입 → stage2_preflight, stage2_orchestrator가 기대하는 형식 일치 여부
4. **Stage4Context 슬롯 None 허용 여부**:
   - 24개 슬롯 중 None이 들어올 수 있는 슬롯 식별
   - None 슬롯을 참조하는 하위 모듈이 None 체크하는지 확인
5. **검증기 입력 타입 가정**:
   - `blocking_validator.py`가 manuscript를 str로 가정하는데 None/빈 문자열 처리

---

## TF-G: 임계값 / 매직넘버 외부화 (Threshold Externalization)

### 배경
Phase 5-B에서 validation.yaml 임계값 외부화를 완료했으나, 코드에 하드코딩된 매직넘버가 57개 파일에 잔존.

### 감사 파일 (5개)

| 파일 | 줄 수 | 감사 범위 |
|------|-------|----------|
| `modules/domain/agents/base_agent.py` | ~1,362 | MAX_OUTPUT_TOKENS, MAX_CONTEXT_CHARS, 타임아웃 |
| `modules/core/stage4_interview_round.py` | ~554 | 하드코딩 절단 길이, 재시도 횟수 |
| `modules/core/stage2_validation_pipeline.py` | ~683 | 비트 길이/개수 임계값 |
| `modules/domain/agents/scoring_validator.py` | ~1,258 | 점수 임계값 |
| `config/settings/validation.yaml` | | 현재 외부화된 임계값 목록 (비교 기준) |

### 조사 지시

1. **validation.yaml에 이미 있는 임계값**과 **코드에 하드코딩된 같은 값** 비교 → 불일치 탐색
2. `base_agent.py`의 `MAX_OUTPUT_TOKENS=8192`, `MAX_CONTEXT_CHARS=900000` — yaml 외부화 후보
3. `stage4_interview_round.py`의 절단 길이 `[:1500]`, `[:2000]` 등 — `_threshold()` 사용 여부
4. `scoring_validator.py`의 점수 임계값 (합격 기준, 가산점 등) — 외부화 여부
5. **재시도 횟수**: `range(3)`, `range(5)`, `max_retries=3` 등 하드코딩 → `_threshold()` 전환 후보

---

## TF-H: 데드코드 / 위생 정리 (Dead Code & Hygiene)

### 배경
TF-5에서 strategies/ 디렉토리와 5개 미사용 모듈을 삭제했으나, 루트의 임시 파일과 tools2/ 잔존.

### 감사 파일

| 파일/디렉토리 | 감사 범위 |
|---------------|----------|
| `_ag_deep.py`, `_ag_scan.py`, `_scan_modules.py` | 루트 임시 분석 도구 |
| `_tmp_r1f.py` ~ `_tmp_r3e.py` (6개) | 리팩토링 임시 파일 |
| `check_blocks.py` (6줄) | 블록 검증 스크립트 |
| `tools2/` 디렉토리 | 대시보드, 자동화 도구 |
| `test_mode/` 디렉토리 | 테스트 모드 런너 |
| `new_blocks_*.json` (5개) | 블록 데이터 파일 |
| `recent_diff*.txt`, `temp_inspect.txt` | 임시 diff 파일 |

### 조사 지시

1. **루트 임시 파일 (9개)**: `_ag_*.py`, `_tmp_*.py`, `_scan_modules.py` — 어디서도 import되는지 확인 → 미사용 시 삭제 후보
2. **check_blocks.py**: 6줄짜리 스크립트 — 용도와 호출처 확인
3. **tools2/**: 각 파일이 프로덕션 코드에서 참조되는지 확인
   - `apply_v3.py`, `apply_v3_pt2.py`: 적용 스크립트
   - `automate_snack.py`: 자동화 도구
   - `studio_dashboard.py`: Streamlit 대시보드
4. **test_mode/**: 프로덕션에서 사용되는지 vs 개발 전용인지
5. **루트 JSON/TXT**: `new_blocks_*.json`, `recent_diff*.txt`, `temp_inspect.txt` — git tracked 여부, 삭제 후보
6. **treatments/ 디렉토리**: 데이터 파일 정리 대상 확인
7. **미사용 import**: 각 모듈에서 import했지만 실제 사용하지 않는 심볼 탐색 (ruff가 잡지 못한 것)

---

## 실행 순서

```
Phase 1: TF-A (롤백) + TF-B (상태) — 병렬
Phase 2: TF-C (트랜잭션) + TF-D (LLM 견고성) — 병렬
Phase 3: TF-E (엣지 케이스) + TF-F (계약 검증) — 병렬
Phase 4: TF-G (매직넘버) + TF-H (데드코드) — 병렬
```

각 Phase 완료 시 진행 테이블 업데이트.

---

## 결과 보고 형식

각 TF별 독립 보고서를 `docs/2026-02-23/opus_tf6_{tf_letter}_audit.md`에 작성.

### 보고서 템플릿

```markdown
# TF-6-{X}: {제목}

## 감사 범위
- 파일: (목록)
- 코드 줄 수: N줄

## 발견 사항

### [{X}-1] {제목} ({심각도})
- **파일**: path L{line}
- **현재 코드**:
  ```python
  (문제 코드)
  ```
- **문제**: (설명)
- **영향**: (재현 조건, 영향 범위)
- **수정안**:
  ```python
  (수정 코드)
  ```
- **테스트**: (검증 방법)

## 요약
| 심각도 | 건수 |
|--------|------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
```

---

## 최종 종합 보고서

모든 TF 완료 후 `docs/2026-02-23/opus_tf6_consolidated_report.md` 작성:
- 전체 발견 건수 (CRITICAL/HIGH/MEDIUM)
- 파일별 발견 분포
- 패치 우선순위 (P0/P1/P2)
- 예상 패치 작업량

---

## 검증

```bash
# 감사 후 기존 테스트 회귀 확인
pytest tests/ -q
# 2,377 passed 유지 확인

# Ruff
python -m ruff check modules/ tests/ main_a.py
python -m ruff format --check modules/ tests/ main_a.py
```
