# TF-8 전체 시스템 감사 플랜 (Codex 실행용)

> **작성일**: 2026-02-23
> **실행자**: Codex (자율 에이전트)
> **베이스라인**: 2,537 passed, 0 xfailed, ruff 0 violations
> **기준 커밋**: `9f0de73` (TF-6 완료)
> **현재 HEAD**: `11cf0ee`
> **감사 대상**: TF-6 이후 추가된 신규 코드 (Hybrid Retrieval, DB 효율화, D2 Observability)

---

## ★★★ CODEX 최우선 오더 (이 섹션부터 읽어라)

이 문서를 받은 Codex는 다음 순서로 즉시 실행을 시작한다:

1. **이 문서 전체를 읽는다** (`docs/2026-02-23/tf8_system_audit_plan.md`)
2. **findings 파일을 확인한다** (`docs/2026-02-23/tf8_findings.md`) — 이미 완료된 라운드는 건너뛴다
3. **findings 파일의 "현재 위치" 섹션을 확인한다** — 거기서 이어서 시작한다
4. **각 라운드는 반드시 실제 소스 코드를 Read 도구로 직접 읽은 후 분석한다**
5. **pytest 통과 = 완료가 아니다** — Read 없이 진행한 라운드는 무효다

### 컨텍스트 컴팩트 복구 절차

컨텍스트 리셋이 발생했다면:

1. `docs/2026-02-23/tf8_system_audit_plan.md` (이 파일) 재독
2. `docs/2026-02-23/tf8_findings.md` 재독
3. findings의 **"현재 위치"** 섹션 확인 → 마지막 완료 라운드 확인
4. 그 다음 미완료 라운드부터 즉시 재개
5. **절대 Round A부터 다시 시작하지 않는다**

---

## 배경 및 목적

### 감사 대상 커밋 (TF-6 이후)

| 커밋 해시 | 설명 |
|-----------|------|
| `2671927` | feat(hybrid): D1 Hybrid Retrieval (FTS5+RRF) 구현 |
| `3abea28` | fix(hybrid): 감리 후 소결함 3건 수정 |
| `6422dc4` | refactor(db): DB 효율화 — chroma_db 삭제·file→DB 전환·인덱스 보강 |
| `da7439e` | fix(db): stage4_post_processor JSON->DB 저장 전환 |
| `1b8fe9a` | fix(db): failure_learner 매화 JSON 저장 제거 |
| `266640d` | feat(obs): memory retrieval 경로별 observability 계측 [D2] |
| `11cf0ee` | test(smoke): Stage2/4 파이프라인 E2E smoke 테스트 추가 |

### 주요 변경 파일

- `modules/core/vec_memory.py` — Hybrid Retrieval(_fts_search, _knn_search_raw, _rrf_score, retrieve_hybrid_context) + D2 logging
- `modules/core/db_manager.py` — FTS5 virtual table(episode_fts), character_voice table, foreshadow table, 인덱스
- `modules/core/character_voice.py` — save_to_db(), load_from_db() 신규
- `modules/core/foreshadow_tracker.py` — save_to_db(), load_from_db() 신규
- `modules/core/stage4_post_processor.py` — JSON→DB 전환
- `modules/core/stage2_preflight.py` — retrieval_mode 라우팅 분기
- `modules/core/stage4_context_builder.py` — retrieval_mode 라우팅 분기
- `main_a.py` — DB-first 로드, failure_learner JSON 저장 제거
- `config/settings/validation.yaml` — retrieval_mode 설정 추가

---

## 이슈 분류 기준

| 등급 | 기준 | 처리 |
|------|------|------|
| CRITICAL | 데이터 유실·무한루프·시스템 크래시 가능 | Round K에서 즉시 패치 |
| HIGH | silent 품질 저하·검증 무력화·잘못된 PASS/REJECT | Round K에서 즉시 패치 |
| MEDIUM | 운영 관측 사각·매직넘버·계약 불일치(비크리티컬) | 기록 후 로드맵 반영 |
| LOW | 스타일·주석·위생 문제 | 기록만 |
| INFO | 참고 사항·정상 동작 확인 | 기록만 |

### 발견 사항 등록 양식

```
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

---

## 진행 테이블

| 라운드 | 주제 | 감사 파일 | 상태 |
|--------|------|-----------|------|
| Round A | vec_memory — Hybrid Retrieval 핵심 구현 | `vec_memory.py` | ⬜ |
| Round B | db_manager — FTS5 + 신규 스키마 | `db_manager.py` | ⬜ |
| Round C | character_voice + foreshadow_tracker — DB 라운드트립 | 2파일 | ⬜ |
| Round D | stage4_post_processor + main_a — DB 전환 완전성 | 2파일 | ⬜ |
| Round E | vec_memory — D2 Observability 로깅 | `vec_memory.py` | ⬜ |
| Round F | stage2_preflight + stage4_context_builder + validation.yaml — retrieval_mode 라우팅 | 3파일 | ⬜ |
| Round G | vec_memory — Memory ROI P0 패치 통합 | `vec_memory.py` | ⬜ |
| Round H | 크로스파일 패치 상호작용 | 전체 횡단 | ⬜ |
| Round I | 테스트 커버리지 갭 | tests/ | ⬜ |
| Round J | 전체 실행 검증 | pytest + ruff | ⬜ |
| Round K | 발견 건 수정 | CRITICAL/HIGH | ⬜ |
| Round L | 종합 자체검증 + 최종 커밋 | 전체 | ⬜ |

---

## Round A: vec_memory.py — Hybrid Retrieval 핵심 구현 감사

### 목적

FTS5+RRF 하이브리드 검색의 핵심 구현체가 설계대로 동작하는지 확인.
기존 dense 경로와의 공존, 빈 결과 처리, FTS 동기화 원자성을 검증한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/vec_memory.py` | L167–L221 | `_ensure_tables()` — FTS5 테이블 생성 확인 |
| `modules/core/vec_memory.py` | L362–L435 | `memorize_v20_episode()` — FTS INSERT 원자성 |
| `modules/core/vec_memory.py` | L583–L683 | `retrieve_hybrid_context()` 전체 |
| `modules/core/vec_memory.py` | L834–L879 | `_knn_search_raw()` — dense_rank 부여 방식 |
| `modules/core/vec_memory.py` | L972–L1010 | `_fts_search()` — FTS5 쿼리 구성 |
| `modules/core/vec_memory.py` | L1012–L1024 | `_rrf_score()` — RRF 공식 |
| `modules/core/vec_memory.py` | L1147–L1180 | `delete_episodes_from()` — FTS cascade DELETE |

### 확인 포인트

**A-1. FTS5 테이블 tokenizer 적합성**
- `episode_fts` tokenizer가 한국어 텍스트를 처리하는지 확인
- `_fts_search()`에서 쿼리를 `" OR ".join(f'"{kw}"' for kw in keywords[:5])` 형태로 구성 시 tokenizer와 정합성
- space-delimited tokenization으로 한국어 단어가 올바르게 검색되는지

**A-2. `memorize_v20_episode()`의 FTS INSERT 원자성**
- vec_episodes, episode_meta, episode_fts 세 테이블에 각각 INSERT
- 이 세 INSERT가 같은 트랜잭션 안에 있는지 확인
- DELETE → INSERT 쌍이 같은 cur 객체로 실행되는지

**A-3. `_knn_search_raw()`의 LEFT JOIN 안전성**
- `LEFT JOIN episode_meta m ON m.ep_num = vec_episodes.rowid`
- episode_meta에 행이 없으면 m.* 컬럼이 NULL → dict에 `summary or ""` 처리 확인

**A-4. `_fts_search()`의 빈 결과 및 특수문자 처리**
- keywords 빈 리스트일 때 `[]` 반환 경로 확인
- 특수문자(쌍따옴표, 괄호) 포함 키워드 이스케이핑 여부
- 빈 FTS 결과 시 except 블록에서 `[]` 반환인지 확인

**A-5. `retrieve_hybrid_context()`의 빈 결과 처리**
- dense 0개 + sparse 0개 시 `scored = []` → `if not top: return ""` 경로 확인
- dense 없고 sparse만 있을 때 RRF 점수 계산 정확성 (`dense_rank=None` 경우)

**A-6. `delete_episodes_from()`의 FTS cascade**
- `DELETE FROM episode_fts WHERE rowid >= ?`
- episode_fts의 rowid가 episode_meta.ep_num과 1:1 매핑인지 확인
- `memorize_v20_episode()` INSERT 시 `INSERT INTO episode_fts(rowid, ...)` 형태인지 확인

**A-7. RRF 공식 정확성**
- `score = 1/(k + dense_rank) + 1/(k + sparse_rank)`
- rank가 0-based인지 1-based인지 확인 (`enumerate(rows)` 시작값)
- 두 rank 모두 None인 경우 score=0.0 반환 확인

**A-8. shared 모드 FTS 테이블 가용성**
- shared 모드에서 `_ensure_tables()` 호출 경로 확인
- shared 모드의 `_ensure_metadata_and_migrate()`가 episode_fts 테이블을 생성하는지 확인
- DBManager가 먼저 생성하고 VecMemory shared 모드가 연결되는 순서 보장 여부

### 완료 조건

모든 확인 포인트에서 실제 코드 스니펫과 줄번호를 첨부한 근거를 findings에 기록.
이슈 없으면 `[A] 이슈 없음` 기록. 이슈 있으면 해당 등급으로 등록.

---

## Round B: db_manager.py — FTS5 virtual table + 신규 스키마 감사

### 목적

DBManager가 생성하는 FTS5 테이블, character_voice, foreshadow 테이블의 스키마 정확성과
마이그레이션 안전성을 검증한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/db_manager.py` | L148–L215 | `_boot_db()` 앞부분 — WAL 모드, sync_status 등 |
| `modules/core/db_manager.py` | L465–L535 | FTS5 테이블, vec_episodes, episode_meta, character_voice, foreshadow 생성 |
| `modules/core/db_manager.py` | L540–L640 | `_migrate_vec_memory_db()` — 기존 DB 마이그레이션 |
| `modules/core/vec_memory.py` | L167–L221 | VecMemory의 `_ensure_tables()` — 비교 기준 |

### 확인 포인트

**B-1. FTS5 tokenizer 일치성**
- `db_manager.py`의 `episode_fts` tokenizer vs `vec_memory.py`의 `episode_fts` tokenizer
- 두 곳이 동일한 tokenizer 설정인지 확인
- 불일치 시 shared/standalone 모드에서 다른 동작 가능

**B-2. character_voice 테이블 스키마 vs save_to_db() 컬럼 일치**
- DBManager의 `CREATE TABLE character_voice` 컬럼명
- `character_voice.py`의 `INSERT OR REPLACE` 컬럼명
- 컬럼명·순서·타입 일치 여부

**B-3. foreshadow 테이블 스키마 vs save_to_db() 컬럼 일치**
- DBManager의 `CREATE TABLE foreshadow` 컬럼명
- `foreshadow_tracker.py`의 `INSERT OR REPLACE` 컬럼명
- `load_from_db()`의 SELECT 컬럼 순서가 테이블 정의와 일치하는지

**B-4. vec_episodes 테이블 하드코딩 차원값**
- DBManager: `USING vec0(embedding float[3072])` 하드코딩 여부
- `vec_memory.py`: `EMBED_DIM = 3072` 상수
- DBManager에 EMBED_DIM 참조 없이 하드코딩이면 모델 변경 시 불일치 위험

**B-5. sync_status 컬럼명 불일치 확인**
- DBManager `CREATE TABLE sync_status`의 컬럼명
- `vec_memory.py` shared 모드에서 INSERT 시 컬럼명
- `vec_memory.py` standalone 모드에서 INSERT 시 컬럼명
- 모드 간 컬럼명 불일치 여부 (`synced` vs `vector_synced`)

**B-6. 마이그레이션 중 FTS 테이블 포함 여부**
- `_migrate_vec_memory_db()`에서 episode_fts 테이블도 재구성하는지 확인
- 이전 DB에 episode_fts가 없으면 마이그레이션 후 FTS 검색 결과가 비어있을 수 있음

**B-7. `_boot_db()`에서 episode_fts 생성 조건**
- `if self._vec_available:` 블록과 episode_fts 생성 위치 관계
- sqlite-vec 미설치 환경에서도 FTS 테이블이 생성되는지 확인

### 완료 조건

스키마 정의 코드와 실제 사용 코드를 대조하여 불일치 항목을 모두 기록.

---

## Round C: character_voice.py + foreshadow_tracker.py — DB 라운드트립 감사

### 목적

save_to_db()/load_from_db()가 데이터를 완전히 왕복하는지 확인.
첫 실행(empty DB), JSON 레거시 마이그레이션 fallback 동작을 검증한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/character_voice.py` | L420–L457 | `save_to_db()` 전체 |
| `modules/core/character_voice.py` | L496–L564 | `load_from_db()` 전체 |
| `modules/core/foreshadow_tracker.py` | L419–L463 | `save_to_db()` 전체 |
| `modules/core/foreshadow_tracker.py` | L520–L675 | `load_from_db()` 전체 |

### 확인 포인트

**C-1. character_voice save_to_db()의 트랜잭션 완결성**
- profiles 순회하며 `INSERT OR REPLACE` 후 `commit()` 경로
- commit 전 예외 발생 시 rollback 처리 확인
- profiles가 0개일 때 commit 없이 조용히 종료하는지 확인

**C-2. character_voice load_from_db()의 row_factory 호환성**
- `isinstance(row, tuple)` 분기 vs `sqlite3.Row` 객체 처리
- DBManager가 `conn.row_factory = sqlite3.Row` 사용 시 분기 동작 확인

**C-3. foreshadow save_to_db()의 DELETE→INSERT 원자성**
- `DELETE FROM foreshadow` 전체 삭제 후 INSERT
- 중간 예외 발생 시 데이터 전부 사라지는 위험 (DELETE 성공, INSERT 실패)
- 트랜잭션 wrapping 여부 확인

**C-4. foreshadow load_from_db()의 data 컬럼 중복 활용**
- `data` 컬럼(payload JSON 전체) vs 개별 컬럼(content, status 등) 중 어느 것을 신뢰하는지
- 두 소스 간 데이터 불일치 시 처리

**C-5. 첫 실행 empty DB 동작**
- load_from_db() 호출 시 row가 없을 때 0 반환 후 정상 동작 확인

**C-6. JSON 마이그레이션 fallback 존재 여부**
- `main_a.py`에서 DB 로드 실패 시 JSON 파일 fallback 경로 존재 여부
- fallback 경로가 없다면 첫 DB 업그레이드 시 기존 JSON 데이터 유실 가능

### 완료 조건

save → load → save → load 왕복에서 데이터가 보존되는 코드 경로를 추적.
트랜잭션 취약점은 CRITICAL 또는 HIGH로 분류.

---

## Round D: stage4_post_processor.py + main_a.py — DB 전환 완전성 감사

### 목적

JSON 저장 경로가 완전히 제거되고 DB 전환이 완전한지 확인.
failure_learner의 JSON→DB 전환 경로를 추적한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/stage4_post_processor.py` | L260–L302 | character_voice/foreshadow save_to_db() 호출부 |
| `modules/core/stage4_post_processor.py` | L1–L50 | 파일 상단 — JSON 관련 import 잔존 여부 |
| `main_a.py` | L1640–L1740 | failure_learner DB 로드/마이그레이션 경로 |
| `main_a.py` | L290–L330 | 세션 종료 시 failure_learner 저장 경로 |

### 확인 포인트

**D-1. stage4_post_processor에 JSON 저장 잔존 여부**
- `save_to_json()` 호출이 모두 제거됐는지 확인
- `character_voice.json`, `foreshadow.json` 경로 문자열 잔존 여부

**D-2. ctx.current_project.db 가용성 보장**
- `self.ctx.current_project.db`가 None일 수 있는지 확인
- `self.ctx.character_voice`가 None일 때 가드 존재 여부

**D-3. failure_learner 매화 JSON 저장 제거 확인**
- stage4_post_processor에 `failure_learning.json` 쓰는 코드 없는지 확인
- 주석으로 제거 근거가 기록되어 있는지 확인

**D-4. main_a.py failure_learner DB 로드 vs JSON 마이그레이션 경계**
- DB 로드 실패 시 JSON 파일 fallback 경로
- JSON 마이그레이션 성공 후 중복 마이그레이션 방지 플래그 존재 여부

**D-5. foreshadow_tracker.save_to_db() 호출 시 db 객체 타입 확인**
- 전달되는 `db`가 DBManager 인스턴스인지
- `db.conn`이 닫혀있는 경우 처리 여부

### 완료 조건

JSON 파일 쓰기 경로가 실제로 모두 제거됐는지 코드에서 직접 확인.
잔존하는 JSON 쓰기는 HIGH로 분류.

---

## Round E: vec_memory.py — D2 Observability 로깅 감사

### 목적

retrieval 경로별 D2 로그가 모든 경로를 빠짐없이 커버하는지 확인.
포맷 일관성, 누락 경로, 파싱 가능 여부를 검증한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/vec_memory.py` | L437–L464 | `retrieve_high_res_context()` — dense + fallback |
| `modules/core/vec_memory.py` | L466–L581 | `retrieve_multi_query_context()` — multi_dense + fallback |
| `modules/core/vec_memory.py` | L583–L683 | `retrieve_hybrid_context()` — hybrid |
| `modules/core/vec_memory.py` | L922–L970 | `_keyword_fallback_search()` — fallback_entry |
| `docs/2026-02-23/memory_observability_d2_plan.md` | 전체 | 설계된 로그 포맷 기준 |

### 확인 포인트

**E-1. D2 로그 포맷 기준**

설계 문서의 표준 포맷:
```
[VecMem] path=<경로> ep<N> q=<쿼리 앞 30자> hits=<N> fallback=<true|false> selected=[<ep목록>] chars=<N>
```

**E-2. retrieve_high_res_context() dense/fallback 경로 로그**
- `path=dense` 로그: `hits` 필드, `selected` 필드 포함 여부 확인
- `path=fallback` 로그: 설계 포맷과 일치 여부

**E-3. retrieve_multi_query_context() multi_dense 경로 로그**
- `path=multi_dense` 로그: `hits`, `selected` 필드 포함 여부
- multi_dense fallback 경로 로그 포맷 확인

**E-4. retrieve_hybrid_context() hybrid 경로 로그**
- 첫 번째 debug 로그 (`chars=pending`) — selected 필드 포함 여부
- 두 번째 debug 로그 (`chars=%d`) — selected 필드 누락이 의도적인지

**E-5. _keyword_fallback_search() fallback_entry 경로**
- `path=fallback_entry` 진입 계측 로그 확인
- 결과 반환 시 결과 길이 로그 없음 → 누락인지 의도적 생략인지

**E-6. retrieve_npc_context() — NPC 경로 로그 누락**
- `retrieve_npc_context()` 전체에 D2 로그 여부
- NPC 경로도 주요 retrieval 경로인데 계측이 빠져있다면 D2 사각지대

**E-7. 로그 레벨 적합성**
- 모든 D2 로그가 `logging.debug`인지 확인
- 잘못된 레벨(`info`, `warning`) 로그 존재 여부

### 완료 조건

설계 문서 포맷과 실제 코드 로그 대조하여 필드 누락을 모두 기록.
포맷 불일치는 MEDIUM, 경로 전체 누락은 HIGH로 분류.

---

## Round F: stage2_preflight.py + stage4_context_builder.py + validation.yaml — retrieval_mode 라우팅 감사

### 목적

retrieval_mode 설정이 실제 함수 호출로 올바르게 연결되는지 확인.
default 동작, invalid 값 처리, 세 파일 간 일관성을 검증한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `config/settings/validation.yaml` | 전체 | retrieval_mode 설정값 확인 |
| `modules/core/stage2_preflight.py` | L130–L160 | retrieval_mode 라우팅 분기 |
| `modules/core/stage4_context_builder.py` | L160–L205 | retrieval_mode 라우팅 분기 |
| `modules/core/vec_memory.py` | L583–L610 | `retrieve_hybrid_context()` 시그니처 |

### 확인 포인트

**F-1. validation.yaml 기본값**
- `smart_retrieval.retrieval_mode` 값이 `dense`인지 확인
- `dense_k`, `sparse_k`, `rrf_k` 값이 vec_memory.py 함수 기본값과 일치 여부

**F-2. stage2_preflight.py 라우팅 완전성**
- `hybrid` 분기 시 `hasattr(memory, "retrieve_hybrid_context")` 조건
- `sparse` 분기 경로
- `else` (default dense) 경로
- retrieval_mode=hybrid 이지만 hasattr=False 일 때 silent 폴백 확인

**F-3. stage4_context_builder.py 라우팅 완전성**
- stage2_preflight와 동일한 패턴인지
- 한쪽에만 있는 분기 여부

**F-4. sparse 경로의 출력 포맷 불일치**
- sparse 경로에서 `_fts_search()` 결과를 직접 조합한 문자열 포맷
- `retrieve_hybrid_context()` 반환 포맷과의 차이
- downstream에서 포맷 차이가 문제가 되는지

**F-5. invalid retrieval_mode 처리**
- `retrieval_mode = "invalid_value"` 일 때 else 분기(dense) 폴백 확인
- 경고 로그 없는 silent 폴백인지 확인

**F-6. sparse 경로에서 dense_k, rrf_k 파라미터 미사용 확인**
- sparse 경로에서 읽히지 않고 버려지는 파라미터 존재 여부

### 완료 조건

세 파일 간 retrieval_mode 설정 연결을 완전히 추적.
silent 폴백이 의도적 설계인지 미완성인지 판단하여 기록.

---

## Round G: vec_memory.py — Memory ROI P0 패치 통합 감사

### 목적

Memory ROI P0 패치(P0-1 거리 기반 랭킹, P0-2 키워드 폴백, P0-3 4-slot, P0-4 count 상향)가
hybrid 경로에서도 일관되게 동작하는지 확인한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/vec_memory.py` | L531–L582 | `retrieve_multi_query_context()` P0 패치 적용 구간 |
| `modules/core/vec_memory.py` | L583–L683 | `retrieve_hybrid_context()` — P0 패치 미적용 여부 확인 |
| `modules/core/vec_memory.py` | L834–L879 | `_knn_search_raw()` — arc bonus 적용 |

### 확인 포인트

**G-1. P0-1 거리 기반 랭킹 — hybrid 경로 미적용 여부**
- `retrieve_multi_query_context()` P0-1 랭킹 vs `retrieve_hybrid_context()` RRF 점수 기반 정렬
- `연속 에피소드 중복 제거`가 hybrid 경로에는 없는지 확인

**G-2. P0-2 키워드 폴백 — hybrid 경로에서의 처리**
- `retrieve_hybrid_context()` dense 임베딩 실패 시 `dense_results = []`로 진행
- sparse FTS 결과만 있으면 RRF 후 반환 — P0-2 폴백을 대체하는지
- hybrid 경로에서 dense=0, sparse=0 인 경우 `_keyword_fallback_search()` 미호출 확인 — 설계 의도 여부

**G-3. P0-3 4-slot count — hybrid 경로 count 전파**
- `retrieve_high_res_context(n_results=3)` 기본값 vs `retrieve_hybrid_context(max_results=5)` 기본값
- stage4_context_builder에서 hybrid 경로에 전달하는 `max_results` 파라미터

**G-4. arc bonus — hybrid 경로 적용 여부**
- `_knn_search_raw()` arc bonus (`adj_distance = distance * 0.9`)
- `retrieve_hybrid_context()` 호출 시 `current_arc_no` 파라미터 전달 여부
- `retrieve_hybrid_context()` 시그니처에 `current_arc_no` 파라미터 존재 여부

**G-5. RRF fusion에서 adj_distance vs dense_rank 혼용**
- arc bonus는 `adj_distance`를 변경하지만 RRF는 `dense_rank`(순서 기반)를 사용
- arc bonus가 RRF 점수에 반영되지 않는 구조인지 확인

### 완료 조건

P0 패치의 hybrid 미통합이 설계상 의도인지 미구현인지를 판단하여 기록.
의도적 미구현이면 INFO, 예상치 못한 동작이면 MEDIUM 이상으로 분류.

---

## Round H: 크로스파일 패치 상호작용 감사

### 목적

여러 파일에 걸친 패치들이 서로 충돌하거나 누락된 연결이 없는지 확인한다.
특히 FTS 원자성, 롤백 cascade, DB 커넥션 공유 일관성을 검증한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `modules/core/vec_memory.py` | L362–L435 | memorize_v20_episode — FTS INSERT 원자성 |
| `modules/core/vec_memory.py` | L1147–L1180 | delete_episodes_from — FTS cascade |
| `modules/core/db_manager.py` | L58–L67 | `__init__` — lock 객체 |
| `modules/core/vec_memory.py` | L60–L103 | VecMemory `__init__` — shared 모드 lock 수신 |
| `modules/core/stage4_post_processor.py` | L260–L302 | save_to_db 호출 시 db 경로 |

### 확인 포인트

**H-1. memorize_v20_episode FTS INSERT 원자성**
- vec_episodes, episode_meta, episode_fts 세 테이블 INSERT가 동일 트랜잭션인지
- `with self._db_lock():` 블록 안에 세 테이블 조작이 모두 있는지
- 중간 예외 발생 시 롤백 범위가 세 테이블 모두인지

**H-2. delete_episodes_from FTS cascade 원자성**
- `with self._db_lock():` 블록 안에 vec_episodes, episode_meta, episode_fts, sync_status DELETE가 모두 있는지
- episode_fts DELETE가 누락되거나 순서가 잘못됐는지

**H-3. shared 모드에서 DBManager lock과 VecMemory lock 동일성**
- VecMemory shared 모드 초기화: `self._lock = lock` (외부 주입)
- 이 lock이 DBManager의 `self._lock`과 동일 객체인지
- 다른 객체라면 DB 커넥션 공유 시 데드락 또는 레이스 컨디션 가능

**H-4. character_voice/foreshadow save_to_db가 DBManager lock 우회**
- `character_voice.py` `db.conn.execute(...)` 직접 호출
- DBManager의 `_lock`을 통하지 않고 `db.conn`을 직접 사용하는 경우 concurrent 쓰기 시 race condition

**H-5. VecMemory standalone 모드에서 episode_fts 테이블 생성 경로**
- standalone vs shared 모드 각각의 FTS 테이블 생성 경로 추적
- shared 모드에서 DBManager가 먼저 초기화되고 VecMemory가 연결되는 순서 보장 여부

**H-6. _boot_db 이후 VecMemory shared 모드 부트스트랩**
- shared 모드에서 vec_episodes 테이블 없을 때 `_ensure_tables()` 재시도 경로
- 이 경우 episode_fts도 같이 생성되는지 확인

### 완료 조건

각 확인 포인트에서 lock 소유자와 트랜잭션 범위를 명시.
데이터 유실 가능한 트랜잭션 갭은 CRITICAL로 분류.

---

## Round I: 테스트 커버리지 갭 감사

### 목적

TF-6 이후 추가된 신규 코드에 대응하는 테스트가 존재하는지 확인한다.

### 읽어야 할 파일

| 파일 | 구간 | 이유 |
|------|------|------|
| `tests/test_vec_memory.py` | L700–L780 | hybrid/FTS 테스트 클래스 확인 |
| `tests/test_db_manager.py` | 전체 | character_voice/foreshadow 테이블 테스트 여부 |
| `tests/integration/test_pipeline_smoke.py` | 전체 | Stage2/4 E2E smoke 커버리지 |

### 확인 포인트

**I-1. test_vec_memory.py — hybrid/FTS 테스트 존재 여부**
- `TestHybridRetrieval` 또는 유사 클래스 존재 여부
- `retrieve_hybrid_context()` 직접 호출 테스트
- `_fts_search()` 직접 호출 + 결과 검증 테스트
- `_rrf_score()` 단위 테스트
- FTS 테이블 memorize 후 존재 확인 테스트

**I-2. test_vec_memory.py — hybrid path 통합 테스트**
- memorize 후 `retrieve_hybrid_context()` 조회 통합 테스트

**I-3. test_db_manager.py — character_voice/foreshadow 테이블 테스트**
- character_voice 테이블 생성 확인 테스트
- foreshadow 테이블 생성 확인 테스트

**I-4. character_voice/foreshadow save_to_db/load_from_db 왕복 테스트**
- `CharacterVoiceTracker.save_to_db()` → `load_from_db()` 왕복 테스트
- `ForeshadowTracker.save_to_db()` → `load_from_db()` 왕복 테스트
- 빈 DB에서 load_from_db() 호출 시 0 반환 테스트

**I-5. retrieval_mode 라우팅 테스트**
- `retrieval_mode = "hybrid"` 시 `retrieve_hybrid_context()` 호출 테스트
- `retrieval_mode = "sparse"` 시 FTS 경로 테스트
- `retrieval_mode = "invalid"` 시 dense 폴백 테스트

**I-6. D2 observability 로그 테스트**
- `logging.debug` 호출 검증 테스트 (caplog fixture)
- 로그 포맷 검증 테스트

**I-7. E2E smoke test — hybrid 경로 포함 여부**
- `test_pipeline_smoke.py`가 retrieval_mode를 주입하는지
- hybrid 모드 E2E 경로 존재 여부

### 완료 조건

각 항목에 대해 "존재함 / 없음 / 부분적" 판정하고 파일명:줄번호 기록.
테스트 미존재 신규 기능은 HIGH 또는 MEDIUM으로 분류.

---

## Round J: 전체 실행 검증

### 목적

기준선 테스트를 통과하는지, ruff violations이 없는지 확인한다.

### 실행할 명령

**J-1. pytest 실행**
```bash
cd /c/Users/wjjo/Desktop/글도비
pytest tests/ -q 2>&1 | tail -5
```
- 기대: `2537 passed, 0 xfailed`

**J-2. ruff 전체 실행**
```bash
ruff check modules/ main_a.py 2>&1 | tail -10
```
- 기대: 0 violations

**J-3. 신규 파일 대상 ruff 집중 검사**
```bash
ruff check modules/core/vec_memory.py modules/core/db_manager.py modules/core/character_voice.py modules/core/foreshadow_tracker.py modules/core/stage4_post_processor.py modules/core/stage2_preflight.py modules/core/stage4_context_builder.py
```

### 완료 조건

pytest 2,537 이상 + xfailed 0 + ruff 0 violations 이어야 합격.
미달 시 findings에 상세 기록 후 Round K 진입.

---

## Round K: 발견 건 수정

### 목적

Round A~J에서 발견된 CRITICAL 및 HIGH 등급 이슈를 모두 패치한다.

### 수정 원칙

1. **각 수정 전 반드시 해당 파일을 Read 도구로 다시 읽는다**
2. 수정 후 `pytest tests/ -q` 재실행하여 기준선 유지 확인
3. `ruff check <수정파일>` 실행하여 violations 없음 확인
4. 수정한 내용을 findings에 `[수정완료]` 태그로 기록

### 수정 우선순위

| 우선순위 | 등급 | 예시 이슈 유형 |
|---------|------|---------------|
| 1 | CRITICAL | 트랜잭션 원자성 파괴, 데이터 유실 경로 |
| 2 | HIGH | FTS 테이블 생성 누락, 로직 silent 실패 |
| 3 | HIGH | 테스트 미커버 신규 기능 (테스트 추가) |

### 수정 후 검증 체크리스트

```
[ ] pytest tests/ -q → 2537 passed, 0 xfailed
[ ] ruff check modules/ main_a.py → 0 violations
[ ] 수정된 파일별 Read 재확인 완료
[ ] findings에 [수정완료] 태그 기록 완료
```

---

## Round L: 종합 자체검증 + 최종 커밋

### 목적

TF-8 감사 전체를 결산하고 최종 커밋을 생성한다.

### 체크리스트

**L-1. 감사 통계 집계**
- findings 파일에서 등급별 이슈 수 집계
- CRITICAL 패치 수, HIGH 패치 수, 미해결 MEDIUM/LOW/INFO 수

**L-2. 미해결 항목 정리**
- MEDIUM 이하 미해결 이슈를 findings의 "미해결 백로그" 섹션에 정리

**L-3. 최종 pytest + ruff 확인**
```bash
pytest tests/ -q 2>&1 | tail -5
ruff check modules/ main_a.py
```

**L-4. git 커밋**

수정된 파일 목록 확인 후 스테이징. 커밋 메시지 형식:
```
audit(tf8): TF-8 전면 재감사 — Hybrid Retrieval·DB효율화·D2 Obs 신규코드 감사 완료

- Round A~L 완료: CRITICAL N건, HIGH N건 패치
- 미해결 MEDIUM/LOW N건 백로그 기록
- 테스트 기준선: 2,XXX passed, 0 xfailed
```

**L-5. findings 파일 최종 업데이트**
- "현재 위치" 섹션을 "TF-8 완료"로 갱신
- 감사 완료 날짜 및 최종 커밋 해시 기록

---

## 부록: 핵심 코드 위치 빠른 참조

| 기능 | 파일 | 줄 범위 |
|------|------|---------|
| FTS5 테이블 생성 (VecMemory) | `vec_memory.py` | L193–L202 |
| FTS5 테이블 생성 (DBManager) | `db_manager.py` | L482–L491 |
| memorize + FTS INSERT | `vec_memory.py` | L362–L435 |
| retrieve_hybrid_context | `vec_memory.py` | L583–L683 |
| _knn_search_raw | `vec_memory.py` | L834–L879 |
| _fts_search | `vec_memory.py` | L972–L1010 |
| _rrf_score | `vec_memory.py` | L1012–L1024 |
| delete_episodes_from FTS | `vec_memory.py` | L1147–L1180 |
| D2 logging dense | `vec_memory.py` | L457–L463 |
| D2 logging multi_dense | `vec_memory.py` | L570–L578 |
| D2 logging hybrid | `vec_memory.py` | L640–L681 |
| character_voice save_to_db | `character_voice.py` | L420–L457 |
| character_voice load_from_db | `character_voice.py` | L496–L564 |
| foreshadow save_to_db | `foreshadow_tracker.py` | L419–L463 |
| foreshadow load_from_db | `foreshadow_tracker.py` | L520–L675 |
| stage2_preflight retrieval_mode | `stage2_preflight.py` | L134–L157 |
| stage4_context_builder retrieval_mode | `stage4_context_builder.py` | L167–L193 |
| validation.yaml retrieval_mode | `config/settings/validation.yaml` | L185–L188 |
| DBManager character_voice table | `db_manager.py` | L510–L517 |
| DBManager foreshadow table | `db_manager.py` | L519–L534 |
| stage4_post_processor save_to_db | `stage4_post_processor.py` | L274–L302 |
| failure_learner DB 로드 | `main_a.py` | L1640–L1695 |
