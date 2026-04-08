# jangyeongshil_industrial_revolution — TR 순차 생산 현황

Date: 2026-04-06
Status: ARC-03 Block 25 완료. Block 26부터 재개.

## 완료된 산출물

| # | 산출물 | 경로 | 상태 |
|---|--------|------|------|
| 1 | Canon | `material_ssot/20_pitch/canon/jangyeongshil_industrial_revolution.md` | locked |
| 2 | Synthesis | `material_ssot/20_pitch/synthesis/althistory_jangyeongshil_working_synthesis.md` | PASS (tightening 1) |
| 3 | Audit | `material_ssot/20_pitch/synthesis/althistory_jangyeongshil_checklist_audit.md` | PASS |
| 4 | Phase0 Design | `treatments/phase0/jangyeongshil_industrial_revolution_phase0_design.json` | 완료 (7 Arc × 10 Block) |
| 5 | Work Guard | `docs/2026-04-06/work_guard_greenplus_batch01/jangyeongshil_industrial_revolution.work_guard.yaml` | 완료 |
| 6 | TR Block 01-10 | `treatments/jangyeongshil_industrial_revolution_tr_block_010_draft.json` | ARC-01 완료 |
| 7 | TR Block 11-15 | `treatments/jangyeongshil_industrial_revolution_tr_block_011_015_draft.json` | ARC-02 전반 완료 |
| 8 | TR Block 16-20 | `treatments/jangyeongshil_industrial_revolution_tr_block_016_020_draft.json` | ARC-02 완결 + 10-block audit PASS |
| 9 | TR Block 21-25 | `treatments/jangyeongshil_industrial_revolution_tr_block_021_025_draft.json` | ARC-03 전반 완료 |

## 다음 작업: Block 26-30

하네스 규칙: `narrative_ssot/30_harness/40_tr_production_harness.md`
- 1-block 순차 생산
- same order max 5 blocks
- Block 30 완료 시 10-block self-audit gate (Block 21-30)

### Block 26-30 Phase0 슬롯 요약

| Block | 제목 | function |
|-------|------|----------|
| 26 | 도면 유출 | 명나라 사신 수행원이 자격루 도면 사본 빼돌림. 도면 열람 기록에서 비정상 접근 감지. **패배**: 일부 유출. 하지만 공차 표기법 없이는 복제 불가. |
| 27 | 표준의 벽 | 유출 사건을 계기로 도면 보안 체계 건의. 영실의 공차 표기법을 궁중 기술 문서 공식 표준으로 채택 + 핵심 도면 열람/복제 승인권. |
| 28 | 측우기의 아침 | **조용한 블록**. 측우기에 빗물이 고이는 첫 아침. 데이터 없이 호조가 보고서를 못 올린다는 사실이 중요. |
| 29 | 기술 문서 표준 | 정인지와 훈민정음으로 기술 교범 작성. 집현전이 인쇄 일정을 영실과 조율. 집현전도 영실 없이 안 움직임. |
| 30 | 증기의 씨앗 | 가마솥 뚜껑 → 증기의 힘 실험 시작. 열역학 제2법칙. ARC-04 입장권. |

## Block 25 완료 시점 상태

### 주인공 권한

- 종3품 대호군
- 자격루 설계 책임자
- 기술 프로젝트 제안권
- 자재 사양 지정 (공조 경유)
- 해외 기술 접촉 권한
- 기술학교 수장

### 부서 의존도 (5개 경유처)

| 부서 | 의존 내용 | 확정 블록 |
|------|-----------|-----------|
| 관상감 | 자발적 설계 자문 요청 | Block 17 |
| 호조 | 농정 보고서에 "기술소 데이터에 의거" | Block 23 |
| 공조 | 자재 사양 경유 | Block 13 |
| 이천/갑인자 | 의존 공식 기록 ("영실 표기법 적용") | Block 22 |
| 집현전 | 정인지 협력 (첫 접점, 아직 제도적 의존 아님) | Block 25 |

### 4축 독립 엔진 진척

| 축 | 상태 | 확정 예정 |
|----|------|-----------|
| 도면 표준 | 기술소 내부 독점 (Block 11) | Block 27에서 공식 채택 |
| 검수 결재선 | 미착수 | Block 49 (가마 사건 후) |
| 제자 라인 | 4명 확보 (Block 24) | Block 58에서 교범 완성 |
| 자재 배분 | 공조 경유 시작 (Block 13) | Block 40에서 기술소 관청화 시 공식화 |

### NPC 상태

| NPC | 현재 태도 | 마지막 변화 |
|-----|-----------|-------------|
| 세종 | 검증자 → 공식 지정자 | Block 18 종3품 제수 |
| 이천 | 손익 기반 파트너. 의존 공식화. | Block 22 갑인자 보고서에 영실 이름 |
| 김순 | 제자 라인 수석. 교육자. | Block 24 |
| 정인지 | 첫 동맹. "이 사람 없으면 그림일 뿐" | Block 25 |
| 최만리 | 미등장 | Block 36 예정 |
| 수양대군 | 미등장 | Block 61 예정 |

### 복선 상태

| ID | 복선 | seed | 현재 상태 |
|----|------|------|-----------|
| FS-01 | 가마 파손은 정치 음모 | Block 10 | 심기 완료. hint Block 25, 38 예정 |
| FS-02 | 세종은 영실의 이상함을 묵인 | Block 5 | 심기 완료. hint Block 18, 35 예정 |
| FS-03 | 명나라 기술 스파이 | Block 15 | 심기 예정 → Block 26 도면 유출에서 발현 |
| FS-04 | 이천의 손익 전환 | Block 7 | **완성** (Block 7→12→22 3단) |
| FS-05 | 김순의 기술 문서 | Block 10 | hint Block 24 완료. Block 58 예정 |
| FS-06 | 자격루 안의 공차 표기 | Block 6 | 심기 완료. payoff Block 70 |

### Canon 보존 체크리스트

재개 시 반드시 확인:

- [ ] 첫 승리 = 세종 은총이 아니라 이천의 평가 수정 (Block 7 ✓)
- [ ] 첫 보상 = 이름+자리+자재 자기명의 (Block 9 ✓)
- [ ] 매 발명 = 발명→태도→자리→문 (Block 11-25 전부 ✓)
- [ ] 왕 미담 금지 (Block 18에서 세종이 공 돌리기를 직접 차단 ✓)
- [ ] 카탈로그 금지 (Block 16에서 감동 소비 금지 내면 잠금 ✓)
- [ ] 장광설 금지 (전 블록에서 "도면이 말하고 입 닫음" 유지 ✓)
- [ ] 4축 독립 엔진 진행 중 (표준 내부독점, 제자 4명, 공조 경유)

## 재개 명령어

```
작업 대상: jangyeongshil_industrial_revolution TR 순차 생산
재개 지점: Block 26 (ARC-03 후반)
읽을 것:
1. docs/2026-04-06/jangyeongshil_industrial_revolution_production_status.md
2. treatments/phase0/jangyeongshil_industrial_revolution_phase0_design.json (ARC-03 Block 26-30)
3. treatments/jangyeongshil_industrial_revolution_tr_block_021_025_draft.json (직전 블록)
하네스: narrative_ssot/30_harness/40_tr_production_harness.md
규칙: 5 blocks → Block 30 완료 시 10-block self-audit gate
```
