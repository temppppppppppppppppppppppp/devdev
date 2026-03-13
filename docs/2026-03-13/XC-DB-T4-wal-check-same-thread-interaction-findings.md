# XC-DB-T4: WAL + check_same_thread=False 상호작용

> Track: XC-DB | 타깃: T4 | 생성일: 2026-03-13

---

## 1. 배경

`db_manager.py`는 다음 설정으로 SQLite 커넥션을 생성:
```python
# L125
conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)

# L158-159
self.cursor.execute("PRAGMA journal_mode=WAL")
self.cursor.execute("PRAGMA synchronous=NORMAL")
```

Advisory 체인은 `ThreadPoolExecutor(max_workers=8)` (L3807)로 8개 쓰레드 병렬 실행.

---

## 2. Findings

### [XC-DB-015] P3 | WAL + check_same_thread=False + RLock 조합 — 현재 안전하나 WAL 체크포인트 정책 미설정

| 필드 | 내용 |
|------|------|
| ID | XC-DB-015 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | WAL 모드에서 자동 체크포인트(기본 1000페이지) 시점이 명시적으로 제어되지 않으며, 장기 세션에서 WAL 파일이 커질 수 있다 |
| 코드 근거 | `db_manager.py:158-159` — `PRAGMA journal_mode=WAL` + `PRAGMA synchronous=NORMAL`. WAL 자동 체크포인트 임계값은 SQLite 기본값(1000페이지 = ~4MB)에 의존. `PRAGMA wal_autocheckpoint` 미설정. |
| 영향 경계 | 250화 이상 장기 세션에서 WAL 파일이 수십 MB까지 커질 수 있으나, SQLite가 자동 체크포인트를 수행하므로 실제 문제 발생 가능성 낮음. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `PRAGMA wal_autocheckpoint=500` 명시적 설정 고려. 또는 에피소드 완료 시 `PRAGMA wal_checkpoint(TRUNCATE)` 실행. 최저 우선순위. |

**WAL 동작 분석**:
- WAL 모드에서 reader는 writer를 차단하지 않음 → Advisory 8쓰레드 읽기와 메인 쓰레드 쓰기 동시 가능
- SQLite는 자동으로 WAL 체크포인트를 1000페이지마다 실행
- `synchronous=NORMAL`은 WAL 모드에서 안전 (WAL 체크포인트 시에만 fsync)
- `timeout=30.0`은 busy timeout으로 DB locked 시 30초 대기

---

### [XC-DB-016] P3 | VACUUM이 lock 외부에서 실행 — WAL 모드 간섭 가능성

| 필드 | 내용 |
|------|------|
| ID | XC-DB-016 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `reset_after()` L2342-2346에서 VACUUM이 `with self._lock:` 블록 **외부**에서 실행되며, 다른 쓰레드의 DB 접근과 경합 가능 |
| 코드 근거 | `db_manager.py:2341-2346` |
| 영향 경계 | WAL 모드에서 VACUUM은 배타적 잠금을 필요로 함. Advisory 쓰레드가 동시에 DB를 읽고 있으면 `VACUUM`이 `database is locked` 에러 발생 가능. 현재 코드에서 `except Exception` → `logging.debug`로 처리. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | VACUUM 실패 시 동작이 이미 비차단(debug 로깅)이므로 **현행 유지 합리적**. VACUUM을 lock 내부로 이동하면 Advisory 쓰레드와의 순차화가 보장되나 lock 점유 시간 증가. |

```python
# L2341-2346
# [TF-24] VACUUM은 커밋 경로에서만 lock 밖에서 실행 (장시간 lock 점유 방지)
if commit:
    try:
        self.conn.execute("VACUUM")
    except Exception as _vac_err:
        logging.debug("[DBManager] VACUUM 실패 (비치명): %s", _vac_err)
```

**분석**: VACUUM을 lock 밖에서 실행한 것은 의도적 설계 결정 (TF-24 주석). VACUUM이 수초 걸릴 수 있으므로 lock 점유를 피한 것. 실패 시 비차단 처리이므로 **안전**.

---

### [XC-DB-017] P3 | vec_memory.py 별도 커넥션 — WAL reader 독립성

| 필드 | 내용 |
|------|------|
| ID | XC-DB-017 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `vec_memory.py` L118에서 `sqlite3.connect(self._db_path, check_same_thread=False)` 별도 커넥션을 생성하며, DBManager의 RLock 보호 범위 밖에서 동작 |
| 코드 근거 | `modules/core/vec_memory.py:118` |
| 영향 경계 | DB-MERGE 이후 `vec_memory.py`는 DBManager의 커넥션을 공유하도록 전환되었을 수 있음. 별도 커넥션이 남아있다면 WAL 모드에서는 안전 (reader 독립성) 이나, RLock 외부에서 쓰기 시 충돌 가능. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `vec_memory.py`가 현재 실제로 별도 커넥션을 사용하는지 확인 필요. 사용한다면 읽기 전용으로 제한 권장. 공수: 30분 조사 |

---

### [XC-DB-018] P2 | Advisory 8쓰레드 동시 DB 읽기 — WAL reader 경합 vs RLock 직렬화

| 필드 | 내용 |
|------|------|
| ID | XC-DB-018 |
| Severity | P2 (품질 저하) |
| 현상 요약 | Advisory 8쓰레드가 동시에 DB를 읽을 때, WAL 모드의 동시 읽기 이점이 RLock 직렬화에 의해 무효화됨 |
| 코드 근거 | `stage4_interview_round.py:3807-3831` — 8쓰레드 병렬 실행. 각 advisory가 DB 읽기 호출 시 `with self._lock:` 진입 → 순차 실행됨. |
| 영향 경계 | 성능 — WAL 모드는 다수 reader가 동시에 읽을 수 있으나, RLock이 reader도 직렬화하여 병렬 이점 소실. Advisory 8개가 각각 DB read를 하면, 8번 순차 lock 획득/해제. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 읽기 전용 메서드에 `threading.Lock` 대신 `threading.RWLock` 패턴 도입 또는 읽기 전용 별도 커넥션 풀. 공수: 4시간 (대규모 리팩토링). **ROI 낮음** — 현재 Advisory 총 실행 시간 대비 DB read 비율이 미미 (LLM 호출이 지배적). |

**성능 영향 추정**:
- Advisory 1개당 DB 읽기: ~1-5ms (SQLite 로컬 파일)
- Advisory 1개당 LLM 호출: ~10,000-60,000ms
- DB 직렬화 오버헤드: 8 * 5ms = 40ms / LLM 총 시간 300,000ms = 0.01%
- **결론**: 성능 영향 무시 가능. 리팩토링 ROI 극히 낮음.

---

### [XC-DB-019] P3 | synchronous=NORMAL 설정 — WAL 크래시 시 마지막 트랜잭션 유실 가능

| 필드 | 내용 |
|------|------|
| ID | XC-DB-019 |
| Severity | P3 (코드 스멜) |
| 현상 요약 | `PRAGMA synchronous=NORMAL`은 WAL 모드에서 체크포인트 시에만 fsync하므로, 시스템 크래시 시 마지막 커밋된 트랜잭션이 유실될 수 있다 |
| 코드 근거 | `db_manager.py:159` — `PRAGMA synchronous=NORMAL` |
| 영향 경계 | 정전/커널 패닉 시 최근 1-2개 트랜잭션 유실 가능. 일반 애플리케이션 크래시(Python 예외)에서는 WAL이 정상 복구. |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 현행 유지 합리적. `FULL`로 변경 시 매 커밋마다 fsync로 성능 2-3배 저하. LLM 기반 시스템에서 디스크 I/O 성능은 비핵심. 데이터 안전성이 우선이면 `synchronous=FULL` 전환 가능. |

**SQLite 공식 문서 참조**:
> In WAL mode when synchronous is NORMAL, the WAL file is synchronized before each checkpoint and the database file is synchronized after each completed checkpoint and the WAL file header is synchronized when a WAL file begins to be reused after a checkpoint, but no sync operations occur during most transactions.

**결론**: 정상 종료 + 일반 예외에서는 안전. 정전/하드웨어 장애에서만 위험이 있으나, 이 시스템의 데이터(AI 생성 원고)는 재생성 가능하므로 **현행 유지 합리적**.

---

## 3. 요약

| ID | Severity | 현상 | 실제 위험 |
|----|----------|------|-----------|
| XC-DB-015 | P3 | WAL 체크포인트 미설정 | 극히 낮음 |
| XC-DB-016 | P3 | VACUUM lock 외부 | 의도적 설계, 안전 |
| XC-DB-017 | P3 | vec_memory 별도 커넥션 | WAL reader 안전 |
| XC-DB-018 | P2 | RLock이 WAL 읽기 병렬성 무효화 | ROI 낮은 성능 이슈 |
| XC-DB-019 | P3 | synchronous=NORMAL 크래시 위험 | 재생성 가능 데이터 |
