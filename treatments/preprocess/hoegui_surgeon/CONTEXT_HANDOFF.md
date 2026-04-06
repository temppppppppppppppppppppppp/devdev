# hoegui_surgeon — Context Handoff

Date: 2026-04-06
Status: ARC-01~02 TR 완료 (Block 1-20), ARC-03~07 TR 미착수
Author: Claude (full-lane owner)

## 1. 현재 상태

| 산출물 | 경로 | 상태 |
|--------|------|------|
| Canon pitch | `material_ssot/20_pitch/canon/hoegui_surgeon.md` | **locked** |
| Synthesis | `material_ssot/20_pitch/synthesis/medical_hoegui_surgeon_working_synthesis.md` | **완료** |
| Audit | `material_ssot/20_pitch/synthesis/medical_hoegui_surgeon_checklist_audit.md` | **PASS** |
| Phase0 design | `treatments/preprocess/hoegui_surgeon/02_phase0_work/phase0_fixed.json` | **완료** |
| Work Guard | `work_guards/12_hoegui_surgeon.yaml` | **FROZEN** |
| TR ARC-01 | `treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_001_010.json` | **완료 + 감리 PASS** |
| TR ARC-02 | `treatments/preprocess/hoegui_surgeon/03_tr_blocks/tr_block_011_015.json` + `tr_block_016_020.json` | **완료 + 감리 PASS** |
| TR ARC-03~07 | 미착수 | **대기** |
| BI draft | 미착수 | **TR 완료 후** |

## 2. 작품 핵심 (canon에서 보존)

- **엔진**: 갈고리만 잡는 R1이 차트 한 줄로 교수의 오판을 먼저 읽고, 적중이 반복되면서 서열은 그대로인데 실질적 결정권이 뒤집힌다
- **첫 승리**: 환자 구조 자체가 아니라 차트 기록 적중에 따른 평가 수정
- **첫 보상**: 과장 직보선 + 고난도 케이스 사전 배정 + 컨퍼런스 발표권
- **도구**: 차트 노트 (R1이 유일하게 공식으로 남길 수 있는 문서)
- **sacrifice policy**: 희생 허용, 단 의학적 명분 + 기록 근거 + 책임 선점 필수, 직후 권한 영수증 필수
- **오염 방지**: 무보상 희생 미담 펌프 ✕ / 감동 의사물 ✕ / 과로 미담 ✕ / 규모 과시 ✕

## 3. Phase0 구조 요약

7 Arc × 10 blocks = 70 blocks

| Arc | 제목 | 블록 | 전장 | 최종 보상 |
|-----|------|------|------|-----------|
| ARC-01 | 차트가 먼저 맞는 R1 | 1-10 | 간담도 수술 판독 | 직보선 + 배정권 + 발표권 + 1st assist |
| ARC-02 | M&M 회의록에 이름을 올리다 | 11-20 | M&M 컨퍼런스 | M&M 기재 + 사전 설계권 + 협진 호출권 |
| ARC-03 | R1이 메스를 잡다 | 21-30 | 단독 집도 + 응급 | 단독 집도 + 학회 증례 + 특수 수술 추천 |
| ARC-04 | 교수의 정치학 | 31-40 | 간이식 + 인사 정치 | 펠로우 추천 + 교육위 참여 |
| ARC-05 | 메스 하나로 올라간다 | 41-50 | 술식 개량 + 라이벌 | 조교수 후보 + 독립팀 |
| ARC-06 | 병원의 칼 | 51-60 | 은폐 사건 + 제도 | 과 운영 실권 + 교육 재편 |
| ARC-07 | 왕좌 | 61-70 | 과장 선임 + 최종 | 진료과장 + 판독 체계 확립 |

## 4. 주요 NPC

| 이름 | 역할 | 첫 등장 | 축 |
|------|------|---------|-----|
| 강태준 | 지도교수 / 핵심 적대 | Block 1 | 묵살 → 위계 → 공작 → 의존 → 인정 |
| 조영채 | 외과 과장 / 핵심 조력 | Block 5 | 계산 전환 → 직보선 → 추천 |
| 한정우 | 치프 R | Block 1 | 위계 수호 → 태도 전환 |
| 박세진 | 동기 R1 | Block 1 | 관찰자 |
| 박정민 | M&M 당사자 교수 | Block 13 | 반박 불가 → 판독 체계 수용 |
| 김수현 | 내과 펠로우 | Block 20 | 타과 첫 협진 호출 |
| 이상훈 | 타 대학 라이벌 | Block 28 | 데이터 검증 → 경쟁 → 양립 |
| 나경태 | 병원장 | Block 37 | 이용 시도 → 압박 → 퇴장 |
| 정소연 | 간이식팀 교수 | Block 32 | 계산 전환 → 펠로우 추천 |
| 권혁수 | 학회 중진 | Block 49 | 학회 표준 지지 |

## 5. ARC-02 완료 요약

Block 11-20 완료. 핵심 달성:
- Block 12: 강태준 합리적 반격 — 차트 기록 사전 승인 규칙 도입
- Block 15: **M&M 회의록 공식 기재** — ARC-02 핵심 도약
- Block 17: 강태준 정식 안건 → 수련교육위 검토로 에스컬레이션
- Block 18: 조영채 '착각하지 마, 내가 지키는 건 내 판단이야' — 계산 방어 본질
- Block 19: **수술 계획 사전 설계권** 부여
- Block 20: **소화기내과 김수현 첫 타과 협진 호출** — ARC-02 종료

열린 복선:
- FS-07: 강태준이 수련교육위 동원 → ARC-03 Block 23에서 심사위 통한 단독 집도 제한
- FS-08: 김수현 협진 관계 → ARC-04 간이식 케이스로 발전

강태준 반격 에스컬레이션 추적:
- B4 위계 문제 → B12 사전 승인 규칙 → B14 발표 순서 조정 → B17 정식 안건 + 수련교육위 → B23(예정) 심사위 단독 집도 제한

## 6. 다음 단계: ARC-03 (Block 21-30)

Phase0 설계:
- ARC-03 제목: "R1이 메스를 잡다"
- 시간: 2026년 10월~2027년 2월

핵심 블록:
- Block 21: 조영채 과장이 R1 최초 단독 집도 기회 부여 (중등도 간절제)
- Block 22: 28세 체력 + 65세 판단력의 조합이 완전히 드러나는 수술
- Block 23: **강태준이 심사위를 통해 R1 단독 집도 제한** (FS-07 payoff)
- Block 24: 집도 제한 → 권한 후퇴
- Block 25: 야간 응급. 집도 가능 의사 전원 부재 + 대량 출혈 환자 → 서동혁 응급 집도
- Block 26: 응급 수술 성공 → 심사위 논거 무력화
- Block 27: **헤드헌팅 거절 (stay method 테스트)** — 대학병원 밖에서는 고난도 케이스 없음
- Block 28: 학회 증례 보고 추천 → 이상훈(타 대학 에이스) 첫 인식
- Block 29: 특수 수술(간이식 보조) 추천 리스트 등재
- Block 30: R2 진급. 직급 한 칸 올랐지만 권한은 이미 R2 이상.

ARC-03 핵심 NPC:
- 강태준: 심사위 반격 (제도적 최고점)
- 이상훈: 첫 등장 (타 대학 라이벌)
- 윤지영: 첫 등장 (병원장 비서 — ARC-04 병원장 라인 예고)

ARC-03 위험축:
- Block 23-24가 강태준 반격의 절정. 집도 제한이 걸리면 권한 후퇴가 크다.
- Block 25 응급이 이 후퇴를 역전하는 핵심. 법적 근거(응급의료법)가 뒷받침.

## 7. 하네스 규율 (재시작 시 확인)

1. 1블록 생산 → 수동 감리 메모 → 다음 블록
2. 5블록 cap에서 반드시 정지, 새 오더 대기
3. Block 30 완료 후 직전 10블록 자체 감리 필수
4. 감리 PASS 전 다음 블록 진행 금지

읽어야 할 하네스:
1. `AGENTS.md`
2. `docs/blockguide/treatment-production-harness-v2.md` (생산 규율)
3. `material_ssot/20_pitch/canon/hoegui_surgeon.md` (canon truth)
4. `treatments/preprocess/hoegui_surgeon/02_phase0_work/phase0_fixed.json` (Phase0)
5. `work_guards/12_hoegui_surgeon.yaml` (work guard)
6. 직전 블록 파일: `tr_block_016_020.json` (Block 20이 직전 상태)
