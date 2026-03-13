# XC-DB: DB 트랜잭션 일관성 & 커서 안전 — 통합 Findings

> Track: XC-DB | 생성일: 2026-03-13 | 총 19건

---

## 심각도 분포

| 심각도 | 건수 | 설명 |
|--------|------|------|
| P0 | 0 | 데이터 손실 — 해당 없음 |
| P1 | 0 | 무성 실패 — 해당 없음 (XC-DB-009 P1→P2 하향) |
| P2 | 8 | 품질 저하 |
| P3 | 11 | 코드 스멜 |

---

## 전체 Finding 목록

### T1: Legacy cursor vs Local cursor 패턴 충돌

| ID | Sev | 제목 | 기존 중복 |
|----|-----|------|-----------|
| XC-DB-001 | P2 | db_manager.py 공유/로컬 커서 혼용 재진입 | T1-07 확장 |
| XC-DB-002 | P2 | ProjectService 15곳 RLock 바이패스 | T1-09 동일 |
| XC-DB-003 | P3 | cursor alias 혼동 패턴 | T1-07 하위 |
| XC-DB-004 | P3 | Advisory 쓰레드 공유 커서 접근 | 신규 |

### T2: JSON 컬럼 corruption 복원력

| ID | Sev | 제목 | 기존 중복 |
|----|-----|------|-----------|
| XC-DB-005 | P2 | JSON 읽기 방어 비일관 (11곳) | 신규 |
| XC-DB-006 | P3 | JSON 쓰기 미방어 (비현실적) | 신규 |
| XC-DB-007 | P3 | _safe_json_loads fallback 이중 파싱 | 신규 |
| XC-DB-008 | P3 | safe_get() 중첩 정의 (P2→P3) | 신규 |

### T3: 트랜잭션 경계 & 부분 롤백 캐스케이드

| ID | Sev | 제목 | 기존 중복 |
|----|-----|------|-----------|
| XC-DB-009 | P2 | reset_stage_2 lock 외부 DELETE (P1→P2) | T1-09 관련 |
| XC-DB-010 | P2 | rollback 후 외부 저장소 불일치 | 신규 |
| XC-DB-011 | P2 | FTS 삭제 실패 무시 | 신규 |
| XC-DB-012 | P2 | commit_episode_factory 공유 커서 | T1-07 하위 |
| XC-DB-013 | P3 | execute_update commit 누락 | T1-06 동일 |
| XC-DB-014 | P3 | 이중 트랜잭션 패턴 | 신규 |

### T4: WAL + check_same_thread=False 상호작용

| ID | Sev | 제목 | 기존 중복 |
|----|-----|------|-----------|
| XC-DB-015 | P3 | WAL 체크포인트 미설정 | 신규 |
| XC-DB-016 | P3 | VACUUM lock 외부 | 신규 |
| XC-DB-017 | P3 | vec_memory 별도 커넥션 | 신규 |
| XC-DB-018 | P2 | RLock이 WAL 읽기 병렬성 무효화 | 신규 |
| XC-DB-019 | P3 | synchronous=NORMAL 크래시 위험 | 신규 |

---

## 기존 Finding 교차 참조

| XC-DB ID | 기존 ID | 관계 |
|----------|---------|------|
| XC-DB-001 | OPUS-TF-T1-07 | 확장 (재진입 시나리오 추가) |
| XC-DB-002 | OPUS-TF-T1-09 | 동일 현상 |
| XC-DB-003 | OPUS-TF-T1-07 | 하위 사례 |
| XC-DB-009 | OPUS-TF-T1-09 | 트랜잭션 경계 분석 추가 |
| XC-DB-012 | OPUS-TF-T1-07 | 하위 사례 |
| XC-DB-013 | OPUS-TF-T1-06 | 동일 현상 |

**순수 신규 finding**: 11건 (XC-DB-004~008, 010~011, 014~019)

---

## 핵심 아키텍처 진단

### 긍정적 측면
1. **RLock 보호**: DBManager의 모든 메서드가 `with self._lock:`으로 보호 (~96곳)
2. **WAL 모드**: 읽기/쓰기 동시성 + 크래시 복구 안전성
3. **중첩 트랜잭션 인지**: `nested = self.conn.in_transaction` 패턴으로 중첩 시 이중 커밋/롤백 방지
4. **integrity_check 복구**: 부트 시 DB 무결성 검사 + 손상 시 자동 격리/재생성
5. **commit_episode_factory 원자성**: 8단계 에피소드 저장이 하나의 트랜잭션으로 보호

### 개선 필요 측면
1. **공유 커서 잔존**: 독스트링에서 deprecated 선언했으나 ~185곳 사용 중
2. **ProjectService 캡슐화 위반**: DBManager API 우회하여 raw cursor 직접 접근
3. **JSON 방어 비일관**: `_safe_json_loads` 적용 범위 불균등 (적용/미적용 혼재)
4. **외부 저장소 정합성**: DB 커밋 후 VectorDB/파일 삭제 실패 시 보상 메커니즘 없음

---

## 공수 추정 (우선순위별)

| 우선순위 | 작업 | 공수 |
|----------|------|------|
| HIGH | ProjectService raw cursor → Protocol 메서드 전환 | 1시간 |
| HIGH | JSON 읽기 방어 `_safe_json_loads()` 통일 | 1시간 |
| MEDIUM | 공유 커서 → 로컬 커서 점진적 전환 | 2-3시간 |
| LOW | FTS 삭제 실패 로깅, safe_get 통합 | 30분 |
| SKIP | RWLock 도입, synchronous=FULL | ROI 낮음 |
