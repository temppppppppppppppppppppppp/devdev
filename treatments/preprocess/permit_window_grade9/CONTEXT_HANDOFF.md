# permit_window_grade9 — Context Handoff

Date: 2026-04-06
Status: TR Block 35/70 완료 — Block 36부터 재개
Author: Claude (full-lane owner)

## 1. 현재 상태

| 산출물 | 경로 | 상태 |
|--------|------|------|
| Canon pitch | `material_ssot/20_pitch/canon/permit_window_grade9.md` | **locked** |
| Phase0 design | `treatments/preprocess/permit_window_grade9/02_phase0_work/phase0_fixed.json` | **완료** |
| Work Guard | `work_guards/10_permit_window_grade9.yaml` | **FROZEN** (WG-V2 PASS 10/10) |
| TR blocks 001-035 | `treatments/preprocess/permit_window_grade9/03_tr_blocks/` | **35블록 완료** |
| ARC-01 감리 | Block 1-10 자체 감리 PASS | **완료** |
| ARC-02 감리 | Block 11-20 자체 감리 PASS | **완료** |
| ARC-03 감리 | Block 21-30 자체 감리 PASS | **완료** |
| ARC-04 전반 | Block 31-35 개별 감리 PASS | **완료** |
| BI draft | `treatments/preprocess/permit_window_grade9/05_bi_work/` | **미착수 — TR 완료 후** |

## 2. 재시작 지점

**Block 036 "정산 대조" (ARC-04 후반, quiet block)**

5블록 cap에서 정지. Block 36~40 생산 후 ARC-04 자체 감리 필수.

## 3. ARC별 완료 현황

| ARC | 블록 | 상태 | 자체 감리 |
|-----|------|------|-----------|
| ARC-01 도장이 멈춘 40분 | 1-10 | **완료** | **PASS** |
| ARC-02 하청 도면의 값 | 11-20 | **완료** | **PASS** |
| ARC-03 소방 동선의 정치학 | 21-30 | **완료** | **PASS** |
| ARC-04 예산 코드의 길목 | 31-40 | 31-35 완료, 36-40 미착수 | 미실시 |
| ARC-05 건설사 연합 반격 | 41-50 | 미착수 | — |
| ARC-06 시장의 계산 | 51-60 | 미착수 | — |
| ARC-07 도시의 관문 | 61-70 | 미착수 | — |

## 4. 10블록 주기 권한 도약 패턴 (확인됨)

| Block | 권한 |
|-------|------|
| B01 | 9급 접수권 (보완요청서로 도장 정지) |
| B10 | 특별보완명령권 + TF 실무 간사 + 시장 직보 |
| B20 | 도면 검증 표준화 권한 (교차검증 길목 장악) |
| B30 | 특별점검 독자 발동권 + 민원 정량화 시스템 운영권 |
| B40 | (예정) 예산 코드 연결권 |

## 5. 활성 NPC 상태 (Block 35 after 기준)

| NPC | 현재 상태 | 다음 블록 before로 이월 |
|-----|-----------|------------------------|
| 이종혁 | 오재명과 연합 가능성. TF 결재+예산 동시 차단 구도. 코드 우회 발견 시 연합이 공모로 변질 위험 | ✓ |
| 박준호 | 하청 도면 원본 최종 제출 완료. 물류센터 마무리 단계 | ✓ |
| 강태원 | 산업단지 예산 코드 우회 12억 발견됨. 현장 확인 대상. 감사 대상 가능 | ✓ |
| 서정아 | 전략 조언 역할로 진화. '묶어서 가라' 타이밍 조언. 현장 확인 행정 처리 | ✓ |
| 최영수 | 물류센터 마무리. ARC-04와 직접 관련 적음 | ✓ |
| 한석배 | 독자 발동권으로 사전 통제 불가. TF 약체화 시 다시 움직일 유인 | ✓ |
| 조은비 | 조례에 소방서 검증 주체로 명시. 법적 기반 확보. 예산 건과 무관 | ✓ |
| 오재명 | TF 내년 예산 보류 반격. 보조금 '적법' 의견서 제출. 코드 우회 미인지 | ✓ |
| 김도형(시장) | 기훈에게 독자 발동권+민원 정량화 부여. 보조금 환수 확인 지시. 직접 신뢰 | ✓ |

## 6. 열린 복선 (Block 36 이후 회수 대상)

| 복선 | 심기 | 회수 예정 |
|------|------|-----------|
| 코드 우회 현장 확인 → 감사 경고 | B35 | B37 |
| 오재명 계산 전환 | B32,B35 | B38 |
| 보조금 건 + 예산 건 묶어서 시장에게 | B34 | B39 |
| 인허가-예산 연동 시스템 시범 가동 | B33 | B39 |
| 예산 코드 연결권 회수 | B31 | B40 |
| 시범 조례 → 본 조례 전환 전장 | B29 | B49 |
| 건설사 연합 본격 반격 | B30 | B41 |
| 한석배 실각 가능성 | B28 | B46+ |

## 7. 30블록 품질 메트릭 (감리 확인 완료)

| 메트릭 | 결과 |
|--------|------|
| P0 위반 | **0건** |
| P1 위반 | **0건** (B3-5 callback 번호 4건 수정 완료) |
| NPC before/after 리셋 | **0건** (35블록 전량) |
| solution 케이던스 | **35블록 전부 다른 문두** |
| "기훈은 ~않는다. 대신 ~" 패턴 | **0회** |
| 밀도 ARC 간 하락 | **없음** (ARC-01~03 평균 1,230~1,250자) |
| solution 단독 최저 | 280자 (quiet blocks) — 기준 150자 초과 |
| content 합산 최저 | 1,100자 (quiet blocks) — 기준 600자 초과 |
| 패배 블록 | B4, B14, B24, B34 (Phase0 일치) |
| quiet 블록 | B6, B16, B26 (Phase0 일치) |

## 8. 재시작 시 읽어야 할 파일

1. `AGENTS.md`
2. `docs/blockguide/treatment-production-harness-v2.md` (§1.1~1.4 생산 규율)
3. `material_ssot/20_pitch/canon/permit_window_grade9.md` (canon)
4. `treatments/preprocess/permit_window_grade9/02_phase0_work/phase0_fixed.json` (Phase0 ARC-04 block_slots 36-40)
5. `work_guards/10_permit_window_grade9.yaml` (work guard)
6. 이 CONTEXT_HANDOFF.md
7. `block_035.json` (직전 블록 상태 확인)

## 9. 재시작 첫 단계

Block 36 "정산 대조" 생산 → 수동 감리 → Block 37 → ... → Block 40 → ARC-04 자체 감리

Phase0 ARC-04 block_slots 참조:
- B36: 정산 대조 (quiet block) — 인허가 이력과 예산 집행 이력을 대조하는 정산 표준
- B37: 감사 경고 — 코드 우회 건이 감사원 예비 경고로 올라감
- B38: 오재명의 전환 — 감사 경고 앞에서 오재명이 연동 시스템이 자기 부서를 보호할 수 있다는 계산
- B39: 예산-인허가 연동 — 인허가 심의 결과와 예산 코드가 자동 연동되는 시스템 시범 가동
- B40: 코드 연결권 — 예산 코드 연결권 확보. 인허가 없이 예산이 풀리는 길이 막힘
