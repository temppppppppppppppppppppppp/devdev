# XC-DB: DB 트랜잭션 일관성 & 커서 안전 — 3-Pass 오탐 제거 최종본

> Track: XC-DB | 생성일: 2026-03-13 | 3-Pass 완료

---

## PASS 3 심사 요약

- **PASS 1**: 19건 후보 수집
- **PASS 2**: 코드 근거 교차 검증, 런타임 도달 가능성 확인, 기존 262+ finding 중복 6건 확인
- **PASS 3**: 오탐/중복/하향 처리 → **최종 확정 13건** (중복 제거 6건)

---

## 오탐 제거 / 심각도 변경 내역

| ID | 원래 Sev | 최종 | 사유 |
|----|----------|------|------|
| XC-DB-001 | P2 | P2 유지 | T1-07 확장이나 재진입 시나리오 분석이 **신규 가치**. DML-only 경로에서는 실제 버그 아님 확인됨. |
| XC-DB-002 | P2 | **제거** | T1-09와 **완전 중복**. 추가 분석 없음. |
| XC-DB-003 | P3 | P3 유지 | T1-07 하위이나 구체적 alias 패턴 목록이 **참고 가치** |
| XC-DB-004 | P3 | P3 유지 | RLock 보호로 실제 안전 확인. 성능 기회로 유지. |
| XC-DB-005 | P2 | P2 유지 | 신규. 11곳 비일관 방어 확인. 개별 try/except 존재하나 패턴 통일 필요. |
| XC-DB-006 | P3 | **제거** | `json.dumps()`에 dict/list/str/int/float만 전달됨 (LLM JSON 파싱 후). 발생 불가. |
| XC-DB-007 | P3 | **제거** | 최적화 기회이나 finding 가치 없음. |
| XC-DB-008 | P2→P3 | **제거** | PASS 2에서 Python 클로저 정상 동작 확인. 버그 아님. |
| XC-DB-009 | P1→P2 | P2 유지 | 트랜잭션 원자성 유지 확인 (SQLite BEGIN~COMMIT). Lock 외부 커서는 설계 위반이나 input() 게이트. |
| XC-DB-010 | P2 | P2 유지 | 신규. 의도된 비차단 설계이나 문서화 가치. |
| XC-DB-011 | P2 | P2 유지 | 신규. FTS 삭제 실패 무시 패턴. |
| XC-DB-012 | P2 | **제거** | T1-07 하위 사례. commit_episode_factory는 최상위 lock으로 완전 보호. |
| XC-DB-013 | P3 | **제거** | T1-06과 **완전 중복**. |
| XC-DB-014 | P3 | P3 유지 | 신규. 코드 구조 이슈로 참고 가치. |
| XC-DB-015 | P3 | P3 유지 | 신규. WAL 운영 참고. |
| XC-DB-016 | P3 | P3 유지 | 신규. TF-24 의도적 설계 확인. |
| XC-DB-017 | P3 | P3 유지 | 신규. vec_memory 별도 커넥션 위험도 LOW. |
| XC-DB-018 | P2 | **P3 하향** | ROI 분석 결과 DB read 시간이 LLM 시간의 0.01%. 성능 영향 무시 가능. |
| XC-DB-019 | P3 | P3 유지 | 신규. 재생성 가능 데이터이므로 현행 유지 합리적. |

---

## 최종 확정 Finding (13건)

### P2 — MAJOR (4건)

#### [XC-DB-001] P2 | db_manager.py 공유/로컬 커서 혼용 — 재진입 시나리오 분석

| 필드 | 내용 |
|------|------|
| ID | XC-DB-001 |
| Severity | P2 |
| 현상 요약 | `self.cursor` (공유)와 `cur = self.conn.cursor()` (로컬)가 ~185곳 vs ~20곳으로 혼재. 중첩 호출 시 이론적 커서 상태 간섭 가능 |
| 코드 근거 | `db_manager.py:1537` (공유), `db_manager.py:1053` (로컬). `commit_episode_factory()` L2050-2217 내부에서 공유/로컬 혼용. |
| 영향 경계 | DML(INSERT/UPDATE/DELETE) 전용이므로 결과 세트 간섭은 발생하지 않음. SELECT 혼용 시에만 문제이나 현재 해당 경로 없음. |
| 테스트 근거 | 중첩 호출 테스트 없음 |
| 기존 중복 여부 | T1-07 확장 (재진입 시나리오 분석 추가) |
| 권장 후속 조치 | 점진적 로컬 커서 전환. 공수: 2-3시간 |

#### [XC-DB-005] P2 | JSON 읽기 방어 비일관 — _safe_json_loads 미적용 11곳

| 필드 | 내용 |
|------|------|
| ID | XC-DB-005 |
| Severity | P2 |
| 현상 요약 | `_safe_json_loads()`는 episode_bibles 계열에만 적용. anchors/blueprints/state_logs 등은 개별 try/except로 비일관 방어 |
| 코드 근거 | `db_manager.py:1572` (load_anchor), `db_manager.py:1105` (get_blueprint), `db_manager.py:1887` (get_latest_state) 등 11곳 |
| 영향 경계 | 개별 방어 존재하여 크래시는 방지되나, 에러 처리 방식(None/빈dict/skip)이 불일관 |
| 테스트 근거 | JSON 손상 시나리오 테스트 없음 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `_safe_json_loads()` 통일 적용. 공수: 1시간 |

#### [XC-DB-009] P2 | ProjectService reset_stage_2: lock 외부 DELETE 체인

| 필드 | 내용 |
|------|------|
| ID | XC-DB-009 |
| Severity | P2 |
| 현상 요약 | `reset_stage_2()`가 `reset_after(commit=False)` 후 lock 외부에서 추가 DELETE 9회 실행. 트랜잭션 원자성은 유지되나 lock 외부 커서 접근은 설계 위반 |
| 코드 근거 | `project_service.py:184-192` → `_clear_stage2_metadata()` L130-154, `_clear_stage2_summary_anchors()` L100-114 |
| 영향 경계 | input() 게이트로 Advisory 동시 실행 불가. 단일 쓰레드 경로. |
| 테스트 근거 | mock DB happy path만 검증 |
| 기존 중복 여부 | T1-09 관련 (트랜잭션 경계 분석 **신규**) |
| 권장 후속 조치 | DELETE를 `reset_after()` 내부로 이동 또는 `db.transaction()` 감싸기. 공수: 1시간 |

#### [XC-DB-010] P2 | rollback 후 외부 저장소(VectorDB/파일) 정합성 보장 없음

| 필드 | 내용 |
|------|------|
| ID | XC-DB-010 |
| Severity | P2 |
| 현상 요약 | DB 커밋 성공 후 VectorDB 삭제, 파일 삭제가 실패해도 DB와 외부 저장소가 불일치. 비차단 에러 처리(의도된 설계). |
| 코드 근거 | `project_service.py:352-362` |
| 영향 경계 | VectorDB 잔류 임베딩이 검색 결과에 영향 가능하나 DB가 SSOT |
| 테스트 근거 | VectorDB 실패 시나리오 미검증 |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | 불일치 감지 플래그 또는 재시도 메커니즘. 공수: 30분 |

---

### P2 — 경계선 (1건, 분석 후 하향 보류)

#### [XC-DB-011] P2 | reset_after() FTS 삭제 실패 무시

| 필드 | 내용 |
|------|------|
| ID | XC-DB-011 |
| Severity | P2 |
| 현상 요약 | `episode_fts` DELETE 실패를 `pass`로 무시. FTS 인덱스와 데이터 불일치 가능. |
| 코드 근거 | `db_manager.py:2314-2317` |
| 영향 경계 | FTS 전문 검색에 삭제된 에피소드 포함 가능 |
| 테스트 근거 | N/A |
| 기존 중복 여부 | 신규 |
| 권장 후속 조치 | `pass` → `logging.debug()` 변경. 공수: 5분 |

---

### P3 — MINOR (8건)

| ID | 제목 | 코드 근거 | 핵심 |
|----|------|-----------|------|
| XC-DB-003 | cursor alias 혼동 패턴 | `db_manager.py:1537` 등 | `cur = self.cursor.execute()` → `self.cursor` alias |
| XC-DB-004 | Advisory 쓰레드 공유 커서 | `stage4_interview_round.py:3807` | RLock 보호로 안전, 성능 기회 |
| XC-DB-014 | 이중 트랜잭션 패턴 | `db_manager.py:2219` vs `2030` | `transaction()` vs `commit_episode_factory()` 중복 |
| XC-DB-015 | WAL 체크포인트 미설정 | `db_manager.py:158` | 기본값 1000페이지 의존 |
| XC-DB-016 | VACUUM lock 외부 실행 | `db_manager.py:2342` | TF-24 의도적 설계 |
| XC-DB-017 | vec_memory 별도 커넥션 | `vec_memory.py:118` | WAL reader 안전 |
| XC-DB-018 | RLock WAL 읽기 병렬성 무효화 | `db_manager.py:65` + `stage4_interview_round.py:3807` | LLM 대비 0.01%, ROI 낮음 |
| XC-DB-019 | synchronous=NORMAL 크래시 위험 | `db_manager.py:159` | 재생성 가능 데이터 |

---

## 최종 판정

### P0 해당 없음 (데이터 손실 경로 없음)
- SQLite 트랜잭션 원자성이 모든 쓰기 경로에서 보장됨
- `commit_episode_factory()`의 8단계 원자적 커밋이 핵심 데이터 보호
- `reset_after()`의 멀티 테이블 DELETE도 단일 트랜잭션 내 실행

### P1 해당 없음 (무성 실패 경로 없음)
- 모든 쓰기 실패가 except 블록에서 catch → rollback → logging/return False
- JSON 파싱 실패도 개별 방어 존재 (비일관적이나 크래시 방지)

### 시스템 안전성 평가: **양호**
- RLock + WAL + nested transaction 인지 = 3중 안전장치
- `check_same_thread=False`의 위험을 RLock이 완전 커버
- Advisory 8쓰레드 DB 접근이 lock으로 직렬화되어 데이터 무결성 보장
- 주요 개선점은 **코드 일관성** (공유→로컬 커서, JSON 방어 통일) 수준

---

## 권장 작업 우선순위

| # | 작업 | 공수 | 영향 |
|---|------|------|------|
| 1 | ProjectService raw cursor → Protocol 메서드 전환 | 1h | XC-DB-009 해소 |
| 2 | JSON 읽기 `_safe_json_loads()` 통일 | 1h | XC-DB-005 해소 |
| 3 | FTS 삭제 `pass` → `logging.debug()` | 5m | XC-DB-011 해소 |
| 4 | 공유 커서 → 로컬 커서 점진적 전환 | 2-3h | XC-DB-001,003,004 해소 |
| 5 | VectorDB 불일치 감지 플래그 | 30m | XC-DB-010 해소 |

**총 예상 공수**: 5-6시간 (전체 P2 해소 기준)
