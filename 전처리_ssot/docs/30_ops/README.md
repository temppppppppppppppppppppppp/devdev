# 30_ops

운영 허브다.

- `intake_queue/`: 새 작업 유입 메모
- `source_manifests/`: source manifest 보관
- `profile_locks/`: profile lock 보관
- `phase0_ready_reviews/`: Stage 0 완료 판정 기록
- `migration_notes/`: 구조 개혁과 `md + json` 전환 준비 문서
- `path_rules/`: 경로 규칙
- `handoffs/`: handoff 메모

핵심:

- 지금은 결과물보다 운영 기준을 먼저 잠그는 단계다.
- `migration_notes/`는 구현 지시서가 아니라 cutover 기준 문서 묶음이다.
- 실제 JSON 계약층은 `95% confidence audit`를 넘긴 뒤에만 구현한다.
