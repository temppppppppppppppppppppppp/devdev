# permit_window_grade9 — Context Handoff

Date: 2026-04-06
Status: TR 전량 재시작 대기
Author: Claude (full-lane owner)

## 1. 현재 상태

| 산출물 | 경로 | 상태 |
|--------|------|------|
| Canon pitch | `material_ssot/20_pitch/canon/permit_window_grade9.md` | **locked** |
| Phase0 design | `treatments/preprocess/permit_window_grade9/02_phase0_work/phase0_fixed.json` | **완료** |
| Work Guard | `work_guards/10_permit_window_grade9.yaml` | **FROZEN** (WG-V2 PASS 10/10) |
| TR blocks | `treatments/preprocess/permit_window_grade9/03_tr_blocks/` | **삭제됨 — 재시작 필요** |
| BI draft | `treatments/preprocess/permit_window_grade9/05_bi_work/` | **삭제됨 — TR 완료 후 재작성** |

## 2. 작품 핵심 (canon에서 보존)

- **엔진**: 도장을 찍는 말단이 아니라 도장을 멈추는 말단
- **프레임**: 막은 사람이 아니라 다시 열 조건을 가진 사람
- **첫 전장**: 물류센터 사용승인 40분 전 도장 정지
- **첫 증명**: 밤비 적중 + 현장 침수/대피 동선 문제
- **첫 보상**: 특별보완명령권 + 시장 직보 + TF 실무 간사
- **보상 원칙**: 생존이 아니라 권한 회수
- **오염 방지**: 공익 미담 ✕ / 민원 감동 ✕ / 추상 정치 ✕ / 정의감 해결 ✕

## 3. Phase0 구조 요약

7 Arc × 10 blocks = 70 blocks

| Arc | 제목 | 블록 | 전장 | 최종 보상 |
|-----|------|------|------|-----------|
| ARC-01 | 도장이 멈춘 40분 | 1-10 | 물류센터 사용승인 | 특별보완명령권 + TF 간사 |
| ARC-02 | 하청 도면의 값 | 11-20 | 데이터센터 건축허가 | 도면 검증 표준화 권한 |
| ARC-03 | 소방 동선의 정치학 | 21-30 | 재개발 소방 동선 | 특별점검 독자 발동권 |
| ARC-04 | 예산 코드의 길목 | 31-40 | 생활SOC 예산 코드 | 예산 코드 연결권 |
| ARC-05 | 건설사 연합 반격 | 41-50 | 건설사 로비 방어 | 인허가 표준 조례 참여권 |
| ARC-06 | 시장의 계산 | 51-60 | 시장 선거 전 대형 3건 | 도시안전관 직제 |
| ARC-07 | 도시의 관문 | 61-70 | 인허가 체계 재편 | 도시 관문 체제 완성 |

10블록마다 권한 도약: TF 간사(10) → 검증권(20) → 발동권(30) → 코드 연결권(40) → 조례 참여권(50) → 도시안전관(60) → 관문(70)

## 4. 주요 NPC 10명

| 이름 | 역할 | 첫 등장 | 축 |
|------|------|---------|-----|
| 이종혁 | 도시개발국 국장 (3급) | Block 2 | 관료 적대 → 퇴임 시 인정 |
| 박준호 | 건설사 상무 | Block 2 | 건설사 적대 → 최후 항복 |
| 서정아 | 도시개발국 계장 (6급) | Block 5 | 계산 전환 조력자 (핵심) |
| 최영수 | 물류센터 현장소장 | Block 3 | 간접 협조 |
| 강태원 | 다른 건설사 상무 | Block 14 | 연합 → 이탈 |
| 한석배 | 시장 정무비서관 | Block 23 | 정치 적대 → 실각 |
| 조은비 | 소방서 조사관 | Block 25 | 외부 검증 조력자 |
| 오재명 | 재무과장 | Block 32 | 적대 → 계산 전환 |
| 정민우 | 시의원 | Block 46 | 정치 조력자 |
| 김도형 | 시장 | Block 28 | 최종 권한자 → 의존 |

## 5. 1차 생산 실패 분석 (재시작 이유)

### 하네스 위반
- §1.1 "1블록 생산 → 수동 감리 → 다음 블록" 미준수 — 10블록씩 일괄 생산
- §1.1B "5블록 cap" 무시 — 연속 10블록 진행

### 발견된 결함 (A~U 기준)
- **P0**: Block 30 solution 필드 누락
- **P1 Pattern O**: NPC before/after 리셋 42건 — 이전 등장 after와 다음 등장 before 불일치
- **P1 Pattern Q**: 밀도 하락 — ARC-01 평균 719자 → ARC-04 평균 541자
- **P1 Pattern T**: solution 길이 하락 — ARC-01 평균 189자 → ARC-04 평균 142자, 최단 95자
- **P1 Pattern K**: solution 문두 "기훈은 ~하지 않는다. 대신 ~" 케이던스 25% 반복

### PASS였던 항목 (유지할 것)
- opponent 다양성 (17종)
- emotional_beat 다양성 (27종)
- deal_type 다양성 (38/40 unique)
- leverage_used 다양성 (109/115 unique)
- foreshadow/callback 연결 양호
- success_pattern 다양성 (38/40 unique)

## 6. 재시작 시 지켜야 할 규율

### 하네스 준수
1. 1블록 생산 → 수동 감리 메모 → 다음 블록
2. 5블록 cap에서 반드시 정지, 새 오더 대기
3. Block 10/20/30/40/50/60/70 완료 후 직전 10블록 자체 감리 필수
4. 감리 PASS 전 다음 블록 진행 금지

### 밀도 유지
5. content 5필드(context + event_villain + solution + reward + stakes) 합산 최소 600자
6. solution 단독 최소 150자
7. ARC 후반으로 갈수록 밀도를 의식적으로 유지 — 하락 금지

### 케이던스 다변화
8. solution 문두를 매 블록 다르게 — "기훈은 ~하지 않는다. 대신 ~" 패턴은 10블록에 최대 2회
9. 시작 주어를 다변화: 기훈 / 서정아 / 조은비 / 상대방 / 상황 묘사 / 대화 시작

### NPC 정합성
10. NPC relationship_delta 작성 시 반드시 해당 NPC의 직전 등장 after를 확인하고 before에 반영
11. NPC state tracking 표를 별도 유지 권장

### 품질 체크
12. 매 블록 감리 최소 항목: solution 길이, NPC before/after 정합, capital continuity, 케이던스 점검

## 7. 읽어야 할 하네스 (재시작 시)

1. `AGENTS.md` → Track Split → 서사 파이프라인
2. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
3. `docs/blockguide/treatment-planning-harness.md` (단계 확인)
4. `docs/blockguide/treatment-production-harness-v2.md` (생산 규율)
5. `material_ssot/20_pitch/canon/permit_window_grade9.md` (canon truth)
6. `treatments/preprocess/permit_window_grade9/02_phase0_work/phase0_fixed.json` (Phase0)
7. `work_guards/10_permit_window_grade9.yaml` (work guard)

## 8. 재시작 첫 단계

Block 1 생산 → 수동 감리 메모 → Block 2 생산 → ...

Phase0의 ARC-01 block_slots를 참조하되, 1차 생산에서 좋았던 점(Block 1-5의 밀도, 서정아 계산 전환 설계, 밤비 적중 구조)은 계승하고 밀도와 정합성을 끝까지 유지할 것.
