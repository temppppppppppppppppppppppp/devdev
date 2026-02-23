# TF-9 Findings

> 베이스라인: 2,542 passed, 0 violations (commit `2fcffff`)

---

## 현재 위치

```
Last Completed Step: 없음 (미시작)
Next Step: Step 1
Status: 대기 중
```

---

## 진행 테이블

| Step | 내용 | 상태 | 비고 |
|------|------|------|------|
| Step 1 | arc_no 전달 수정 (TF8R-1) | ⬜ 미완료 | |
| Step 2 | invalid mode 경고 로그 (TF8-F-2) | ⬜ 미완료 | |
| Step 3 | retrieval_mode 라우팅 테스트 (TF8-I-2) | ⬜ 미완료 | |
| Step 4 | D2 로그 caplog 테스트 (TF8-I-3) | ⬜ 미완료 | |
| Step 5 | 최종 검증 + 커밋 | ⬜ 미완료 | |

---

## Step별 수정 기록

### Step 1: arc_no 전달 수정
- 대상: `modules/core/stage4_context_builder.py`
- 수정 전: (Codex가 실제 Read 후 기록)
- 수정 후: (Codex가 실제 Read 후 기록)

### Step 2: invalid mode 경고 로그
- 대상: `modules/core/stage2_preflight.py`, `modules/core/stage4_context_builder.py`
- 수정 전: (Codex가 실제 Read 후 기록)
- 수정 후: (Codex가 실제 Read 후 기록)

### Step 3: retrieval_mode 라우팅 테스트
- 신규 파일: `tests/test_retrieval_mode_routing.py`
- 테스트 수: 5개 예정

### Step 4: D2 로그 caplog 테스트
- 대상: `tests/test_vec_memory.py`
- 추가 테스트: 2개 예정

### Step 5: 최종 검증
- pytest: (Codex가 기록)
- ruff: (Codex가 기록)
- 커밋: (Codex가 기록)

---

## 이슈 목록 (TF-8 감리 → TF-9 패치 대상)

| ID | 등급 | 내용 | 상태 |
|----|------|------|------|
| TF8R-1 | HIGH | stage4_context_builder arc_no 항상 None (죽은 코드) | ⬜ |
| TF8-F-2 | MEDIUM | invalid retrieval_mode silent 폴백 (경고 없음) | ⬜ |
| TF8-I-2 | MEDIUM | retrieval_mode 라우팅 단위 테스트 부재 | ⬜ |
| TF8-I-3 | MEDIUM | D2 로그 caplog 포맷 검증 테스트 부재 | ⬜ |

---

## 보류 이슈 (이번 TF 범위 외)

| ID | 등급 | 내용 | 사유 |
|----|------|------|------|
| TF8-E-2 | MEDIUM | dense 로그 hits/selected 보강 | `_knn_search` 내부 리팩터 필요 — 별도 TF |
| TF8-G-2 | MEDIUM | hybrid 0-hit 폴백 전략 | 설계 결정 필요 — 별도 TF |
| TF8-INFO-1 | INFO | tokenizer 없음 | 설계 결정 필요 |
| TF8-INFO-2 | INFO | EMBED_DIM 하드코딩 | 현재 영향 없음 |
