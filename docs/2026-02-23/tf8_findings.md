# TF-8 Findings (발견 사항 기록)

> **감사 플랜**: `docs/2026-02-23/tf8_system_audit_plan.md`
> **생성일**: 2026-02-23
> **실행자**: Codex

---

## 현재 위치 (컴팩트 복구용)

```
Last Completed Round: L
Next Action: TF-8 완료 (후속 백로그만 추적)
Status: 완료
Unresolved CRITICAL: 0건
```

---

## 감사 통계

| 등급 | 발견 수 | 패치 완료 | 미해결 |
|------|---------|-----------|--------|
| CRITICAL | 1 | 1 | 0 |
| HIGH | 9 | 9 | 0 |
| MEDIUM | 5 | 0 | 5 |
| LOW | 0 | 0 | 0 |
| INFO | 2 | 0 | 2 |
| **합계** | **17** | **10** | **7** |

---

## Round A: vec_memory.py — Hybrid Retrieval 핵심 구현

> 상태: 완료
> 읽은 파일: `modules/core/vec_memory.py`

### 수동 근거
- `modules/core/vec_memory.py:387`~`modules/core/vec_memory.py:407`
  `vec_episodes`/`episode_meta`/`episode_fts`가 동일 `cur`에서 수행되고 `modules/core/vec_memory.py:422`에서 단일 `commit()`.
- `modules/core/vec_memory.py:1023`~`modules/core/vec_memory.py:1039`
  FTS 쿼리가 키워드를 `"..."`로 감싸 OR 결합되는 경로 확인.
- `modules/core/vec_memory.py:85`~`modules/core/vec_memory.py:90`
  shared 모드 성공 경로에서 기존에는 메타데이터 검사만 수행했고 FTS 보장 로직이 없었음.

### 발견 이슈
#### [TF8-A-1] FTS 키워드 따옴표 미정규화로 MATCH 구문 실패 가능 (HIGH)
**파일**: `modules/core/vec_memory.py`
**줄**: L1023-L1039
**현재 코드**:
```python
keywords = [w for w in re.split(r"[\s,.\-|/]+", query) if len(w) >= 2]
fts_query = " OR ".join(f'"{kw}"' for kw in keywords[:5])
```
**문제**: `"` 포함 키워드가 그대로 MATCH 구문에 들어가면 구문 오류로 except 경로(`[]`)로 떨어짐.
**영향**: hybrid/sparse 검색이 silent 실패(품질 저하).
**권장 수정 방향**: 키워드 정규화 후 MATCH 문자열 생성.
**수정 상태**: [수정완료] 2026-02-23

#### [TF8-A-2] shared 모드에서 episode_fts 누락 DB 백필 부재 (HIGH)
**파일**: `modules/core/vec_memory.py`
**줄**: L85-L90, L170-L193
**현재 코드**:
```python
self._ensure_metadata_and_migrate()
# (기존) FTS 보장/백필 없음
```
**문제**: vec_episodes는 존재하지만 episode_fts가 비어 있거나 없는 DB에서 sparse/hybrid recall이 비정상.
**영향**: 기존 프로젝트에서 hybrid/sparse 사실상 무력화 가능.
**권장 수정 방향**: shared 모드 초기화 시 FTS 테이블 보장 + episode_meta 기반 백필.
**수정 상태**: [수정완료] 2026-02-23

---

## Round B: db_manager.py — FTS5 + 신규 스키마

> 상태: 완료
> 읽은 파일: `modules/core/db_manager.py`, `modules/core/vec_memory.py`, `modules/core/character_voice.py`, `modules/core/foreshadow_tracker.py`

### 수동 근거
- `modules/core/db_manager.py:483`~`modules/core/db_manager.py:490`와 `modules/core/vec_memory.py:176`~`modules/core/vec_memory.py:182` tokenizer 동일성 확인 (`unicode61 remove_diacritics 2`).
- `modules/core/db_manager.py:575`~`modules/core/db_manager.py:599`
  마이그레이션에서 episode_fts 이관/백필 보강 코드 적용 전후 비교.

### 발견 이슈
#### [TF8-B-1] vec_memory DB 마이그레이션에서 episode_fts 이관 누락 (HIGH)
**파일**: `modules/core/db_manager.py`
**줄**: L568-L599
**현재 코드**:
```python
# 기존: episode_meta, vec_episodes, sync_status, anchors만 이관
# episode_fts 이관 로직 부재
```
**문제**: 마이그레이션 후 FTS 데이터 공백 발생 가능.
**영향**: sparse/hybrid 검색 recall 급감.
**권장 수정 방향**: old episode_fts 직접 이관, 없으면 episode_meta 기반 백필.
**수정 상태**: [수정완료] 2026-02-23

---

## Round C: character_voice + foreshadow_tracker — DB 라운드트립

> 상태: 완료
> 읽은 파일: `modules/core/character_voice.py`, `modules/core/foreshadow_tracker.py`, `main_a.py`

### 수동 근거
- `modules/core/character_voice.py:427`~`modules/core/character_voice.py:458`
  `save_to_db()`에 rollback 경로 추가됨.
- `modules/core/foreshadow_tracker.py:427`~`modules/core/foreshadow_tracker.py:464`
  `DELETE` 후 INSERT 중 예외 시 rollback 처리 추가됨.
- `main_a.py:1748`~`main_a.py:1772`
  DB 로드 0건 시 JSON→DB 마이그레이션 fallback 경로 존재.

### 발견 이슈
#### [TF8-C-1] CharacterVoice save_to_db 예외 시 롤백 부재 (HIGH)
**파일**: `modules/core/character_voice.py`
**줄**: L427-L458
**문제**: 중간 예외에서 후속 commit으로 부분 반영될 수 있음.
**영향**: 프로필 일부만 저장되는 불일치 가능.
**권장 수정 방향**: try/except + rollback.
**수정 상태**: [수정완료] 2026-02-23

#### [TF8-C-2] Foreshadow DELETE→INSERT 중단 시 데이터 유실 위험 (CRITICAL)
**파일**: `modules/core/foreshadow_tracker.py`
**줄**: L427-L464
**문제**: DELETE 이후 INSERT 실패 시 전량 손실 가능.
**영향**: 복선 SSOT 손상.
**권장 수정 방향**: 동일 트랜잭션 롤백 보장.
**수정 상태**: [수정완료] 2026-02-23

---

## Round D: stage4_post_processor + main_a — DB 전환 완전성

> 상태: 완료
> 읽은 파일: `modules/core/stage4_post_processor.py`, `main_a.py`

### 수동 근거
- `modules/core/stage4_post_processor.py:272`~`modules/core/stage4_post_processor.py:287`
  character_voice/foreshadow 모두 `save_to_db(...)` 경로 사용.
- `main_a.py:2273`~`main_a.py:2318`
  failure_learner 세션 종료 저장이 `reflexion_memory` DB UPSERT 경로임.

### 발견 이슈
- [D] 이슈 없음 (JSON 저장 잔존 미발견, DB 전환 경로 확인).

---

## Round E: vec_memory.py — D2 Observability 로깅

> 상태: 완료
> 읽은 파일: `modules/core/vec_memory.py`, `docs/2026-02-23/memory_observability_d2_plan.md`

### 수동 근거
- `modules/core/vec_memory.py:447`~`modules/core/vec_memory.py:463`
  dense/fallback 경로 debug 로그 존재 확인.
- `modules/core/vec_memory.py:685`~`modules/core/vec_memory.py:881`
  `retrieve_npc_context()`에 기존 D2 로그 부재 확인 후 path=npc 로그 추가 반영.

### 발견 이슈
#### [TF8-E-1] NPC retrieval 경로 observability 누락 (HIGH)
**파일**: `modules/core/vec_memory.py`
**줄**: L685-L832 (기존)
**문제**: 주요 retrieval 경로인데 D2 로그가 없어 운영 관측 사각지대.
**영향**: 장애 분석/튜닝 근거 부족.
**권장 수정 방향**: fallback/normal 모두 debug 계측 추가.
**수정 상태**: [수정완료] 2026-02-23

#### [TF8-E-2] dense 로그 포맷 필드(hits/selected) 불완전 (MEDIUM)
**파일**: `modules/core/vec_memory.py`
**줄**: L458-L463
**문제**: D2 표준 필드 일부 누락.
**영향**: 후처리 파서 일관성 저하.
**권장 수정 방향**: 표준 포맷으로 필드 통일.
**수정 상태**: 미수정

---

## Round F: retrieval_mode 라우팅

> 상태: 완료
> 읽은 파일: `config/settings/validation.yaml`, `modules/core/stage2_preflight.py`, `modules/core/stage4_context_builder.py`

### 수동 근거
- `config/settings/validation.yaml:185`~`config/settings/validation.yaml:188`
  기본값 `retrieval_mode: dense`, `dense_k/sparse_k/rrf_k` 확인.
- `modules/core/stage2_preflight.py:137`~`modules/core/stage2_preflight.py:165`
  hybrid/multi 경로에 `current_arc_no` 전달.
- `modules/core/stage4_context_builder.py:170`~`modules/core/stage4_context_builder.py:193`
  (기존) arc_no 전달 누락 확인, 이후 전달 보강.

### 발견 이슈
#### [TF8-F-1] Stage4 retrieval 경로에서 current_arc_no 미전달 (HIGH)
**파일**: `modules/core/stage4_context_builder.py`
**줄**: L170-L193
**문제**: stage2와 달리 arc bonus 문맥이 stage4에서 끊김.
**영향**: hybrid/multi 검색 일관성 저하.
**권장 수정 방향**: `plan.arc_no`를 hybrid/multi 호출로 전달.
**수정 상태**: [수정완료] 2026-02-23

#### [TF8-F-2] invalid retrieval_mode 시 silent dense fallback (MEDIUM)
**파일**: `modules/core/stage2_preflight.py`, `modules/core/stage4_context_builder.py`
**줄**: `stage2_preflight.py:152-165`, `stage4_context_builder.py:186-193`
**문제**: 잘못된 설정값 감지/경고 없음.
**영향**: 운영자가 오설정을 인지하기 어려움.
**권장 수정 방향**: 경고 로그 추가 또는 명시적 검증.
**수정 상태**: 미수정

---

## Round G: Memory ROI P0 패치 통합

> 상태: 완료
> 읽은 파일: `modules/core/vec_memory.py`, `modules/core/stage4_context_builder.py`

### 수동 근거
- `modules/core/vec_memory.py:913`~`modules/core/vec_memory.py:943`
  `_knn_search_raw()`가 arc bonus 후 distance 재정렬 + dense_rank 재산정으로 보강됨.
- `modules/core/vec_memory.py:651`~`modules/core/vec_memory.py:653`
  hybrid 결과 0건 시 빈 문자열 반환(키워드 폴백 미연결) 확인.

### 발견 이슈
#### [TF8-G-1] arc bonus가 dense_rank에 반영되지 않음 (HIGH)
**파일**: `modules/core/vec_memory.py`
**줄**: L913-L943
**문제**: 기존 구현은 bonus를 `distance`에만 반영하고 `dense_rank`는 원본 순서 유지.
**영향**: RRF 점수에서 arc bonus 효과 상실.
**권장 수정 방향**: bonus 적용 거리로 재정렬 후 dense_rank 재부여.
**수정 상태**: [수정완료] 2026-02-23

#### [TF8-G-2] hybrid 0-hit 시 keyword fallback 미호출 (MEDIUM)
**파일**: `modules/core/vec_memory.py`
**줄**: L651-L653
**문제**: dense/sparse 모두 0일 때 즉시 빈 문자열 반환.
**영향**: fallback 회복력 부족.
**권장 수정 방향**: 옵션 기반 keyword fallback 연계 검토.
**수정 상태**: 미수정

---

## Round H: 크로스파일 패치 상호작용

> 상태: 완료
> 읽은 파일: `modules/core/vec_memory.py`, `modules/core/db_manager.py`, `modules/core/stage4_post_processor.py`, `main_a.py`

### 수동 근거
- `main_a.py:1027`~`main_a.py:1032`
  `VecMemory(conn=self.current_project.db.conn, lock=self.current_project.db._lock)`로 동일 lock 객체 주입 확인.
- `modules/core/vec_memory.py:304`~`modules/core/vec_memory.py:308`
  vec 마이그레이션 중 sync_status 컬럼이 두 스키마(`synced`/`vector_synced`)를 모두 처리하도록 보강.

### 발견 이슈
#### [TF8-H-1] sync_status 컬럼명 차이로 shared 마이그레이션 예외 가능 (HIGH)
**파일**: `modules/core/vec_memory.py`
**줄**: L304-L308
**문제**: 기존 코드가 `synced`만 갱신하여 shared 스키마(`vector_synced`)에서 실패 가능.
**영향**: 차원 마이그레이션 경로 비정상 종료 위험.
**권장 수정 방향**: 두 컬럼 스키마 모두 처리.
**수정 상태**: [수정완료] 2026-02-23

---

## Round I: 테스트 커버리지 갭

> 상태: 완료
> 읽은 파일: `tests/test_vec_memory.py`, `tests/test_db_manager.py`, `tests/integration/test_pipeline_smoke.py`

### 수동 근거
- `tests/test_vec_memory.py:759`~`tests/test_vec_memory.py:802`
  따옴표 쿼리 FTS, arc bonus dense_rank 회귀 테스트 추가.
- `tests/test_db_efficiency_transactions.py:40`~`tests/test_db_efficiency_transactions.py:65`
  character_voice/foreshadow 저장 실패 rollback 회귀 테스트 추가.
- `tests/integration/test_pipeline_smoke.py:130`~`tests/integration/test_pipeline_smoke.py:153`
  shared 모드 FTS 백필 검증 테스트 추가.

### 발견 이슈
#### [TF8-I-1] DB 저장 실패 rollback 회귀 테스트 부재 (HIGH)
**파일**: `tests/` (신규)
**문제**: save_to_db 예외 시 rollback 동작을 고정하는 테스트가 없었음.
**영향**: 추후 회귀 시 데이터 유실 재발 가능.
**권장 수정 방향**: 실패 주입 테스트 추가.
**수정 상태**: [수정완료] 2026-02-23

#### [TF8-I-2] retrieval_mode 라우팅 전용 테스트 부재 (MEDIUM)
**파일**: `tests/` 전반
**문제**: `dense/hybrid/sparse/invalid` 분기 호출 자체를 직접 고정하는 테스트 없음.
**영향**: 분기 회귀 탐지 지연.
**권장 수정 방향**: stage2/stage4 단위 테스트 추가.
**수정 상태**: 미수정

#### [TF8-I-3] D2 로그 포맷 caplog 검증 부재 (MEDIUM)
**파일**: `tests/` 전반
**문제**: 로그 문자열 필드 계약 검증이 없음.
**영향**: 관측 파이프라인 파싱 회귀 위험.
**권장 수정 방향**: caplog 기반 포맷 테스트 추가.
**수정 상태**: 미수정

---

## Round J: 전체 실행 검증

> 상태: 완료

### pytest 결과

```text
(사전 검증) 2537 passed, 1 warning
(최종 검증) 2542 passed, 1 warning
```

### ruff 결과

```text
ruff check modules/ main_a.py tests/ -> All checks passed!
ruff check(핵심 변경 파일 집합) -> All checks passed!
```

---

## Round K: 발견 건 수정

> 상태: 완료

### 수정 목록

| 이슈 ID | 등급 | 파일 | 수정 상태 |
|---------|------|------|-----------|
| TF8-A-1 | HIGH | `modules/core/vec_memory.py` | 완료 |
| TF8-A-2 | HIGH | `modules/core/vec_memory.py` | 완료 |
| TF8-B-1 | HIGH | `modules/core/db_manager.py` | 완료 |
| TF8-C-1 | HIGH | `modules/core/character_voice.py` | 완료 |
| TF8-C-2 | CRITICAL | `modules/core/foreshadow_tracker.py` | 완료 |
| TF8-E-1 | HIGH | `modules/core/vec_memory.py` | 완료 |
| TF8-F-1 | HIGH | `modules/core/stage4_context_builder.py` | 완료 |
| TF8-G-1 | HIGH | `modules/core/vec_memory.py` | 완료 |
| TF8-H-1 | HIGH | `modules/core/vec_memory.py` | 완료 |
| TF8-I-1 | HIGH | `tests/test_db_efficiency_transactions.py`, `tests/test_vec_memory.py`, `tests/integration/test_pipeline_smoke.py` | 완료 |

---

## Round L: 종합 자체검증

> 상태: 완료

### 최종 통계

- 총 이슈 발견: 17건
- CRITICAL 패치: 1건
- HIGH 패치: 9건
- 미해결 MEDIUM/INFO: 7건
- 최종 pytest: `2542 passed, 1 warning`
- 최종 ruff: `All checks passed!`
- 최종 커밋: (아직 미커밋)

### 미해결 백로그

1. `TF8-E-2` dense 로그 포맷 표준 필드 보강 (MEDIUM)
2. `TF8-F-2` invalid retrieval_mode 경고 로그 추가 (MEDIUM)
3. `TF8-G-2` hybrid 0-hit fallback 정책 결정 및 구현 (MEDIUM)
4. `TF8-I-2` retrieval_mode 라우팅 분기 단위 테스트 추가 (MEDIUM)
5. `TF8-I-3` D2 로그 caplog 포맷 테스트 추가 (MEDIUM)
6. retrieval tokenizer/한국어 토크나이징 정밀도 튜닝 검토 (INFO)
7. DBManager 벡터 차원 하드코딩(3072) 상수 동기화 리팩터링 검토 (INFO)

---

## 이슈 등록 양식 (복사해서 사용)

```markdown
#### [TF8-X-n] {이슈 제목} ({등급})
**파일**: `경로/파일명.py`
**줄**: L{시작}–L{끝}
**현재 코드**:
{코드 스니펫}
**문제**: {설명}
**영향**: {실제 결과}
**권장 수정 방향**: {방향}
**수정 상태**: 미수정 / [수정완료] {날짜}
```
