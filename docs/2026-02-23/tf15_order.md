# TF-15 패치 오더 (TF-10~14 집계 반영)

> 기준: `docs/2026-02-23/tf10_14_master_plan.md`  
> 목표: TF-10~14에서 집계된 HIGH/MEDIUM 중 즉시 운영 리스크가 큰 항목 우선 패치

---

## 1) 범위

### P0 (즉시 차단)
1. `save_v20_anchor` 실패 시 트랜잭션 부분 커밋 방지
2. Stage2 병렬 enrich 실패 후 arc index 드리프트 방지
3. `VecMemory.retrieve_hybrid_context` 무검색 시 키워드 폴백 추가
4. API 키 로테이션 client 생성 예외 fail-safe
5. Stage4 CoVe 예외 경로 fail-open 제거 (fail-closed)
6. `ContinuityValidator`의 `prev_hud` 누락 fail-open 제거
7. 병렬 검증에서 consistency 예외 시 fail-closed
8. Stage4Context `emotion_tracker` DI 누락 배선 복구

### P1 (후속 라운드)
1. Prompt fail-open (`MANUSCRIPT_HISTORY_CONFLICT_PROMPT`) 정책 재정의
2. PromptLoader 캐시 키(`PROMPT_DIR` 전환) 보강
3. stage3/stage2 실패 경로의 audit/callback callable guard 정리

---

## 2) 완료 기준

1. 대상 파일 패치 반영
2. `python -m ruff check` 통과
3. 변경 영향 테스트 셋 통과

---

## 3) 산출물

1. 코드 패치 (P0)
2. `docs/2026-02-23/tf15_patch_plan.md`
