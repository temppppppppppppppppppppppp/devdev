# 패밀리 재라우팅 런북

## 언제 재라우팅하는가
- Phase 0 작업 중 "이 작품은 blockguide가 아니라 wuxguide다" (또는 반대)를 깨달았을 때
- Stage 0 완료 전이면 비용 최소, Phase 0 이후면 비용 증가

## 재라우팅 비용표
| 시점 | 비용 | 절차 |
|------|------|------|
| Stage 0 진행 중 | 최소 | profile_lock.json의 primary_profile만 변경. source_manifest는 유지 가능 |
| Stage 0 완료, Phase 0 미착수 | 소 | profile_lock 재작성 + phase0_ready_snapshot 재감리 |
| Phase 0 완료, TR 미착수 | 중 | phase0_design 재작성. Stage 0 산출물은 profile_lock만 재작성 |
| TR 진행 중 (Block N까지 완료) | 대 | Block 1부터 재생산 권장. 기존 TR은 reference_only로 강등 |
| BI 완료 | 금지 | 재라우팅 대신 신규 work_id로 시작 |

## 절차
1. narrative_router.py --work-id {work_id} --genre {new_genre} 실행하여 새 패밀리 확인
2. profile_lock.json에서 primary_profile 변경
3. 해당 시점의 비용표에 따라 재작업
4. phase0_ready_snapshot.manual_audit_pass를 false로 되돌림
5. 수동 감리 후 true로 재전환
