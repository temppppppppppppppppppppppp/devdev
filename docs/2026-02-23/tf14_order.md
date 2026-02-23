# TF-14 Codex 실행 오더 — 상태 일관성 감사

---

## ★ CODEX 환경 규칙 (최우선)

1. **인코딩**: findings 파일 작성 시 UTF-8만 사용. 한글 깨짐 방지를 위해 Write 도구로 파일을 쓸 때 BOM 없는 UTF-8로 작성한다.
2. **자동 검색 도구 금지**: `grep`, `rg`, `find`, `ag`, `ripgrep` 등 셸 자동 검색 도구를 절대 사용하지 않는다. 파일 내용 확인은 **오직 Read 도구**로만 수행한다.
3. **컨텍스트 컴팩트 시 중단 금지**: 컨텍스트 컴팩트가 발생해도 **감사를 중단하지 않는다**. findings.md의 "현재 위치"를 읽고, 미완료 Round부터 이어서 끝까지 완료한다. Round A부터 재시작하면 안 된다.
4. **토큰 절약**: 파일 내용을 findings에 통째로 복사하지 않는다. `파일:줄번호 + 핵심 스니펫(1~3줄) + 등급 + 한 줄 설명`만 기록한다.

---

## 너의 임무

글도비 프로젝트의 **상태 일관성**을 감사한다.
DB 트랜잭션, 롤백, NPC 이력, world_state/fact_ledger의 원자성이 보장되는지 판정한다.

**코드 수정 없음. Read-only 감사.**

---

## 시작 전 필수

1. **이 문서 전체를 읽어라**
2. **`docs/2026-02-23/tf14_findings.md`를 읽어라** → "현재 위치" 확인

---

## 절대 수칙

1. **모든 판정은 Read 도구로 파일을 직접 읽은 후 수행한다**
2. **발견 즉시 tf14_findings.md에 기록한다**
3. **각 Round 완료 즉시 "현재 위치" 업데이트**
4. **코드를 수정하지 않는다**

---

## 컨텍스트 컴팩트 복구

1. `docs/2026-02-23/tf14_order.md` 재독
2. `docs/2026-02-23/tf14_findings.md` 재독 → "현재 위치" 확인
3. 다음 미완료 Round부터 즉시 재개

---

## Round 순서

```
Round A → B → C → D → E → 완료
```

---

## Round A: DB 트랜잭션 원자성

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/db_manager.py` | BEGIN/COMMIT/ROLLBACK 패턴 |
| `modules/core/project_manager.py` | safe_commit / safe_commit_async |

### 체크리스트

- [ ] BEGIN/COMMIT/ROLLBACK 패턴의 일관성
- [ ] safe_commit / safe_commit_async의 동작 차이
- [ ] 동시 접근 시 DB 잠금 처리 (WAL 모드 등)
- [ ] 대량 INSERT (memorize_v20_episode 등) 시 트랜잭션 범위

---

## Round B: 롤백 원자성 (auto_backtrack)

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/project_manager.py` | auto_backtrack_v35 구현 |
| `modules/core/db_manager.py` | rollback_episode 관련 메서드 |
| `modules/core/vec_memory.py` | 벡터 DB 롤백 |

### 체크리스트

- [ ] 롤백 시 manuscripts + world_state + fact_ledger + npc_history + vec_memory 원자성
- [ ] 부분 롤백 실패 시 시스템 상태 일관성 (TF-6 패치 재검증)
- [ ] 롤백 후 재시작 시 상태 무결성

---

## Round C: NPC 이력 일관성

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/db_manager.py` | npc_history 테이블 DDL + CRUD |
| `modules/domain/agents/state_tracker_npc.py` | NPC 상태 변경 로직 |
| `modules/domain/agents/state_tracker.py` | bind_db() 호출 |

### 체크리스트

- [ ] npc_history append-only 패턴이 모든 NPC 변경 경로에서 준수
- [ ] bind_db() 호출 없이 NPC 변경이 이루어지는 경로
- [ ] deceased NPC 상태 변경 시도 차단 여부

---

## Round D: world_state / fact_ledger 일관성

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/fact_ledger.py` | FactLedger 구현 |
| `modules/core/stage3_orchestrator.py` | 초기화 (L220, L237) |
| `modules/validation/continuity_validator.py` | fact_ledger 참조 |

### 체크리스트

- [ ] world_state 에피소드별 스냅샷 누적 정확성
- [ ] fact_ledger 사망/기술/아이템이 검증기에서 올바르게 참조되는지
- [ ] Stage3 미실행 → Stage4 직행 시 world_state=None 처리

---

## Round E: 크로스 에피소드 상태 정합

### 읽어야 할 파일

| 파일 | 목적 |
|------|------|
| `modules/core/stage4_post_processor.py` | PASS 후 상태 업데이트 |
| `modules/core/character_voice.py` | 캐릭터 보이스 일관성 |
| `modules/core/foreshadow_tracker.py` | 복선 추적 |

### 체크리스트

- [ ] 에피소드 N PASS 후 상태 업데이트가 N+1 시작 전 완료되는지
- [ ] character_voice 누적이 에피소드 순서를 보장하는지
- [ ] foreshadow_tracker 복선 해소가 롤백 시 정합성을 유지하는지

---

## 완료 기준

- tf14_findings.md "현재 위치" = Round E 완료
- 모든 체크리스트 항목에 PASS/FAIL/WARN 판정
- 발견 건수 집계

---

지금 바로 `docs/2026-02-23/tf14_findings.md`를 읽는 것부터 시작하라.
