# manual_meridian_archivist 컨텍스트 핸드오프

- Date: 2026-04-06
- Status: TR production 진행 중 (Block 13 완료, Block 14 대기)
- Work ID: `manual_meridian_archivist`
- Family: `wuxguide`
- Profile: `wuxia`

## 1. 완료된 산출물

| 산출물 | 경로 | 상태 |
|--------|------|------|
| Canon pitch | `material_ssot/20_pitch/canon/manual_meridian_archivist.md` | 완료 (PASS) |
| Stage 0 source_manifest | `treatments/preprocess/manual_meridian_archivist/source_manifest.json` | 완료 |
| Stage 0 profile_lock | `treatments/preprocess/manual_meridian_archivist/profile_lock.json` | 완료 |
| Stage 0 material_bundle | `treatments/preprocess/manual_meridian_archivist/material_bundle_summary.json` | 완료 |
| Stage 0 phase0_ready | `treatments/preprocess/manual_meridian_archivist/phase0_ready_snapshot.json` | 완료 |
| Phase 0 design | `treatments/phase0/manual_meridian_archivist_phase0_design.json` | 완료 |
| work_guard | `work_guards/11_manual_meridian_archivist.yaml` | 완료 (WG-V2 PASS) |
| TR draft | `treatments/manual_meridian_archivist_tr_block_070_draft.json` | **Block 1-13 완료** |

## 2. TR 진행 상태

- **완료**: Block 1-13 (ARC-01 전체 + ARC-02 Block 11-13)
- **다음**: Block 14 (묵리 방문, quiet_block, Phase 0 설계에 부합)
- **현재 5-block window**: Block 11-15 중 Block 13까지 완료. Block 14-15 잔여.
- **Block 015 경계**에서 반드시 정지 후 새 오더.

### ARC-01 감리 결과

- **PASS (1건 경미 HOLD)**: realm 진행이 Phase 0보다 한 단계 빠름(무경지→후천중기 vs 설계상 무경지→후천초기). ARC-02에서 후천중기 안정→완성으로 소화하면 전체 곡선 정합.
- Phase 0 수정 불필요 — TR에서 소화.

### Block 13 직후 상태 (다음 블록의 realm_before/internal_energy_before)

- **realm**: 후천중기
- **internal_energy**: 소(小) 약화 (복원 실패 심리적 동요)
- **복원 감각**: 통맥 독해 (원본 대조 결함 인지 상태)
- **부상**: 본인 없음. 임호 경맥 미세 손상(3개월 회복)
- **감정**: 자신감 급락. 원본 대조 한계를 처음 인지
- **정치**: 분기 보고 족쇄 + 복원 실패가 보고에 기재됨

### Block 14 사전 선언 (작성 완료, JSON 미출력)

- **고유 사건**: 묵리(떠돌이 비급 수집가) 태허검문 방문. 복수 사본 대조 기법 교환으로 원본 대조 결함 보강.
- **Phase 0 설계**: quiet_block, defeat 직후 회복.
- **beat**: catastrophe → recovery
- **action_type**: 복원실패 → 지식교환+기법보강
- **location**: 외문수련장 → 객사(客舍)
- **duration**: 3일 → 10일

## 3. 핵심 서사 상태

### 복선 심기 현황 (Block 1-13)

| ID | 내용 | seed | payoff 예상 |
|----|------|------|-------------|
| 한설 10년 | 장로 검세 10년간 막힌 시점 = 곽유정 장서각 정리 직후 | B1 | B9(부분회수), B36 |
| 장서각 붕괴 | 단순 노후 아닌 의도적 약화 가능성 | B1 | B57 |
| 붉은 흔적 정체 | 선천적 감맥 체질 | B1 | B65 |
| 곽유정 목록 누락 | 봉인 비고 비급을 목록에서 제외 | B5 | B37 |
| 의심 목록 비보고 | 곽유정에게 보고하지 않은 4건 | B5,B11 | B33 |
| 봉인각 열쇠=곽유정 | 30년 전 마지막 출입자 | B8 | B36,B57 |
| 풍잔운 "곽씨 원로급" | 30년 전 비급 교류 사절단 수장 | B12 | B32 |
| 원본 대조 한계 | 표준 참고서만으로 부족 → 묵리 복수 사본 | B13 | B14(다음) |

### 적대자 상태

| 인물 | 현재 상태 |
|------|----------|
| 설화진 | 분기 보고 족쇄 성공 + 복원 실패를 탄약으로 축적. 다음 공격 준비 중 |
| 곽유정 | 표면 후원자/실제 감시자. 여운의 외부 접촉 제한 시도 좌절. 분기 보고로 감시 구조화. 30년 전 사절단 수장으로서의 과거가 서서히 노출 위험 |
| 풍잔운 | 적대→잠재 동맹. 청풍검파에서 30년 전 기록 탐색 중 |
| 사공묵 | 아직 미등장. Phase 0 설계상 B18 첫 등장 |

### 의심 목록 (여운이 곽유정에게 비보고로 보관)

1. 태허검문 비급 A — 의도적 변조 냄새, 필체·먹 다름 (B5)
2. 태허검문 비급 B — 동상 (B5)
3. 태허사절 — 위중혈 삼분→이분 변조, 너무 정교 (B9)
4. 남궁세가 비급 — 태허검문과 동일 유형 순서 역전 (B11)

## 4. canon truth 보존 체크

| 항목 | 보존 여부 |
|------|----------|
| 첫 전장: 계승비무 직전 죽은 검식 복원 | O (B1) |
| 첫 보상: 열쇠+보호패+진입권+열람우선권 | O (B1) |
| 살렸더니 문이 열렸다 | O (B1 이후 전 블록) |
| 검을 살리는 자 | O (B1,6,9 복원 주도) |
| 복원 5단계 생략 금지 | O (B1 부분, B6,9 완전, B13 실패로 한계 노출) |
| business-power 어휘 금지 | O |
| 성인군자형 금지 | O — 복원은 항상 접근권/보호/지위와 교환 |

## 5. 재개 시 절차

1. 이 문서를 읽는다
2. `docs/wuxguide/wuxia-production-harness.md`를 읽는다
3. `treatments/phase0/manual_meridian_archivist_phase0_design.json`에서 ARC-02 Block 14-20 설계를 확인한다
4. `treatments/manual_meridian_archivist_tr_block_070_draft.json`에서 Block 13의 martial_ext를 확인해 연속성을 잡는다
5. Block 14 사전 선언(위 §2에 초안 있음)을 확정하고 JSON을 출력한다
6. Block 14-15 생산 후 Block 015 경계 정지 → 새 오더로 Block 16-20 진행

## 6. 남은 전체 로드맵

| 구간 | 블록 | 상태 |
|------|------|------|
| ARC-01 | 1-10 | **완료 + 감리 PASS** |
| ARC-02 | 11-20 | **11-13 완료, 14-20 잔여** |
| ARC-03 | 21-30 | 미착수 |
| ARC-04 | 31-40 | 미착수 |
| ARC-05 | 41-50 | 미착수 |
| ARC-06 | 51-60 | 미착수 |
| ARC-07 | 61-70 | 미착수 |
| BI 초안 | - | TR 완료 후 |
