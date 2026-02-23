# TF-9 Critical Hunt Plan (Data Safety First)

> 작성일: 2026-02-23  
> 목적: CRITICAL(데이터 유실/복구 불가/크래시) 0건을 안정적으로 달성할 때까지 집중 스윕

---

## 0. 운영 원칙

1. 기능 확장 금지. 안정성 결함만 처리한다.
2. CRITICAL/HIGH는 즉시 수정, MEDIUM 이하는 백로그로 분리한다.
3. 각 Phase 종료 시 테스트 + 증거 로그를 남긴다.
4. 한 번 통과로 종료하지 않는다. **동일 스윕 2회 연속 CRITICAL 0건**이 종료 조건이다.

---

## 1. 종료 기준 (DoD)

아래 3개를 모두 만족해야 TF-9 종료:

1. Phase 1~5 전체를 **2회 반복**했을 때 CRITICAL 0건
2. 장애 주입 반복 100회에서 데이터 유실 0건
3. `pytest tests/ -q` + `ruff check modules/ main_a.py tests/` green

---

## 2. Sweep 범위

- `modules/core/vec_memory.py`
- `modules/core/db_manager.py`
- `modules/core/character_voice.py`
- `modules/core/foreshadow_tracker.py`
- `modules/core/stage4_post_processor.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage4_context_builder.py`
- `main_a.py`
- `tests/` (신규/보강 테스트)

---

## 3. Phase별 실행

### Phase 1: 데이터 유실 카오스 스윕 (최우선)

목표:
- `DELETE -> INSERT` / 다중 테이블 write 경로에서 중간 실패 시 유실 0

주요 대상:
- `foreshadow_tracker.save_to_db()`
- `character_voice.save_to_db()`
- `vec_memory.memorize_v20_episode()`
- `vec_memory.delete_episodes_from()`

작업:
1. execute/commit 지점 실패 주입 테스트 추가
2. rollback 후 row count/핵심 레코드 불변성 검증
3. 부분 저장 여부 검증 (atomicity)

검증:
```bash
pytest tests/test_db_efficiency_transactions.py -q
pytest tests/test_vec_memory.py -q -k "rollback or delete_episodes_from or memorize"
```

합격 기준:
- 실패 주입 케이스 전부 pass
- 데이터 유실 재현 0건

---

### Phase 2: 부팅/마이그레이션 복구 스윕

목표:
- 비정상 DB 상태에서 재기동 시 자동 복구/안전 폴백 보장

케이스:
1. `episode_fts` 누락 상태
2. `vec_memory.db.partial_migrated` 존재 상태
3. sqlite-vec 미설치 -> 설치 후 재기동
4. JSON -> DB fallback 경계

검증:
```bash
pytest tests/integration/test_pipeline_smoke.py -q -k "fts or shared_mode or migrate"
pytest tests/test_db_manager.py -q
```

합격 기준:
- 복구 경로 모두 pass
- 재기동 후 retrieval/sync 경로 정상

---

### Phase 3: 동시성/락 스윕

목표:
- shared connection + RLock 환경에서 race/deadlock/부분커밋 제거

작업:
1. multi-thread read/write 혼합 테스트 추가
2. tracker save + vec write 동시 실행
3. lock 우회 경로 점검 및 재현 테스트

검증:
```bash
pytest tests/ -q -k "concurrency or lock or shared_mode"
```

합격 기준:
- deadlock 0
- race성 실패 0

---

### Phase 4: 중단 복구 스윕 (kill/restart)

목표:
- 처리 중 비정상 종료 후 재기동해도 SSOT 무결성 유지

작업:
1. write 중단 시뮬레이션(예외 주입 기반)
2. 재기동 시 백필/복구 동작 검증
3. `episode_meta` ↔ `episode_fts` 정합성 검증

검증:
```bash
pytest tests/ -q -k "restart or recovery or backfill"
```

합격 기준:
- 재기동 후 핵심 테이블 정합성 손상 0

---

### Phase 5: 불변식(Invariant) 스윕

목표:
- “절대 깨지면 안 되는 규칙”을 테스트로 고정

필수 invariant:
1. `episode_meta.ep_num == episode_fts.rowid` (존재 시)
2. vec 저장 성공 시 sync_status 반영
3. rollback 후 pre-state와 post-state 동일
4. fallback 경로에서도 crash 없이 빈 문자열/빈 리스트 반환

검증:
```bash
pytest tests/ -q
ruff check modules/ main_a.py tests/
```

합격 기준:
- invariant test 전부 pass

---

## 4. 실행 템포

권장 루프:
1. Phase 1~5 실행
2. CRITICAL/HIGH 패치
3. 전체 테스트
4. 같은 루프 재실행
5. 2회 연속 CRITICAL 0건이면 종료

---

## 5. 우선 백로그 (현재 기준)

1. invalid `retrieval_mode` 경고 로그 추가 (MEDIUM)
2. D2 로그 포맷 caplog 계약 테스트 (MEDIUM)
3. hybrid 0-hit 시 fallback 정책 결정/테스트 (MEDIUM)
4. retrieval_mode 분기 단위 테스트(dense/hybrid/sparse/invalid) (MEDIUM)
5. tokenizer 한국어 적합성 심화 검증 (INFO)

---

## 6. 보고 템플릿 (반복 사용)

```markdown
### TF-9 Sweep Report (Run N)
- Phase 결과: P1[pass/fail], P2[...], P3[...], P4[...], P5[...]
- 신규 CRITICAL: N건
- 신규 HIGH: N건
- 패치 완료: [이슈ID...]
- 잔여 리스크: [이슈ID...]
- 검증:
  - pytest: xxx passed, y warning
  - ruff: clean / violations N
- 결론: 다음 루프 진행 / TF-9 종료
```
