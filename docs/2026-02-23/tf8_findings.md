# TF-8 Findings (발견 사항 기록)

> **감사 플랜**: `docs/2026-02-23/tf8_system_audit_plan.md`
> **생성일**: 2026-02-23
> **실행자**: Codex

---

## 현재 위치 (컴팩트 복구용)

```
Last Completed Round: 없음 (아직 시작 전)
Next Action: Round A 시작
Status: 미착수
Unresolved CRITICAL: 0건
```

> Codex는 각 라운드 완료 시 이 섹션을 업데이트한다.
> 형식: `Last Completed Round: X / Next Action: Round Y 시작 / Status: 진행중`

---

## 감사 통계 (최종 집계 전 공란)

| 등급 | 발견 수 | 패치 완료 | 미해결 |
|------|---------|-----------|--------|
| CRITICAL | — | — | — |
| HIGH | — | — | — |
| MEDIUM | — | — | — |
| LOW | — | — | — |
| INFO | — | — | — |
| **합계** | — | — | — |

---

## Round A: vec_memory.py — Hybrid Retrieval 핵심 구현

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round B: db_manager.py — FTS5 + 신규 스키마

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round C: character_voice + foreshadow_tracker — DB 라운드트립

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round D: stage4_post_processor + main_a — DB 전환 완전성

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round E: vec_memory.py — D2 Observability 로깅

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round F: retrieval_mode 라우팅

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round G: Memory ROI P0 패치 통합

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round H: 크로스파일 패치 상호작용

> 상태: 미착수
> 읽은 파일: (없음)

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round I: 테스트 커버리지 갭

> 상태: 미착수
> 읽은 파일: (없음)

### 테스트 갭 목록 (초기 추정)

| 기능 | 테스트 파일 | 상태 |
|------|------------|------|
| `retrieve_hybrid_context()` 직접 호출 | `tests/test_vec_memory.py` | 미확인 |
| `_fts_search()` 직접 호출 + 결과 검증 | `tests/test_vec_memory.py` | 미확인 |
| `_rrf_score()` 단위 테스트 | `tests/test_vec_memory.py` | 미확인 |
| memorize → hybrid 조회 왕복 | `tests/test_vec_memory.py` | 미확인 |
| character_voice save_to_db/load_from_db | 미존재 (추정) | 미확인 |
| foreshadow save_to_db/load_from_db | 미존재 (추정) | 미확인 |
| retrieval_mode 라우팅 분기 | 미존재 (추정) | 미확인 |
| D2 로그 포맷 검증 | 미존재 (추정) | 미확인 |

### 발견 이슈

(없음 — 라운드 실행 후 기록)

---

## Round J: 전체 실행 검증

> 상태: 미착수

### pytest 결과

```
(미실행)
```

### ruff 결과

```
(미실행)
```

---

## Round K: 발견 건 수정

> 상태: 미착수

### 수정 목록

| 이슈 ID | 등급 | 파일 | 수정 상태 |
|---------|------|------|-----------|
| (Round A~J 완료 후 채워짐) | | | |

---

## Round L: 종합 자체검증

> 상태: 미착수

### 최종 통계

- 총 이슈 발견: —
- CRITICAL 패치: —
- HIGH 패치: —
- 미해결 MEDIUM/LOW/INFO: —
- 최종 pytest: —
- 최종 ruff: —
- 최종 커밋: —

### 미해결 백로그

(Round K 완료 후 채워짐)

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
