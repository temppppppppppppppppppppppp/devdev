# NPC 추적표 마스터 인덱스

> 최종 업데이트: 2026-03-25
> 목적: 전 작품 NPC 추적 자산 통합 현황

---

## 작품별 현황

| 작품 | 블록 진행 | 추적표 | 이월 매핑 (handoff) | 비고 |
|------|-----------|--------|---------------------|------|
| failed_future_ceo_intern | **70/70** | `failed_future_ceo_intern_npc_tracker.md` | `failed_future_ceo_intern_npc_handoff_b57_b70.md` | **Block 70 최종** — NPC 10명 + 신규 4명 + 진영 결과 |
| wuxia_nakyang_merchant_daughter | 40/70 | `wuxia_nakyang_merchant_daughter_npc_tracker.md` | `wuxia_nakyang_merchant_daughter_npc_handoff_b41_b70.md` | NPC 11명 + 6섹션 + 복선 5건 + 체크리스트 30항 |
| wuxia_third_rate_sect_master | 44/70 | `wuxia_third_rate_sect_master_npc_tracker.md` | `wuxia_third_rate_sect_master_npc_handoff_b45_b70.md` | NPC 10명 + 복선 13건 + 체크리스트 37항 |
| empire_youngest_allsector | 70/70 | `empire_youngest_allsector_npc_tracker_final.md` | — (완결작) | **밀도 완료** — NPC 24명 전량 궤적, before/after 전문 |
| wuxia_heavenly_physician | 70/70 | `wuxia_heavenly_physician_npc_tracker_final.md` | — (완결작) | **밀도 완료** — NPC 23명 전량 궤적, before/after 전문 |

---

## 문서 유형 설명

### 추적표 (tracker)
- 마지막 생산 블록 시점의 NPC 상태 스냅샷
- 다음 블록 생산 시 `relationship_delta.before` 직접 복사 가능
- 미완성작: Block N after + 다음 핵심 이벤트
- 완성작: 전량 궤적 아카이브 (블록별 before/after 전문)

### 이월 매핑 (handoff)
- 추적표 + phase0_design 교차 참조
- 미생산 블록의 이벤트별 NPC 변화 예측
- 미회수 복선 체인 + 진영 배치 + 검증 체크리스트 포함
- 완성작에는 불필요 (모든 블록이 이미 생산됨)

### 교차 검증 리포트
- `npc_tracker_validation_report.md`: 추적표 ↔ draft 정합성 자동 검증 결과
- 검증 스크립트: `scripts/npc_tracker_validator.py`

---

## 데이터 파일 (내부용)

| 파일 | 용도 |
|------|------|
| `_empire_npc_data.json` | empire NPC 전량 궤적 정규화 데이터 |
| `_physician_npc_data.json` | physician NPC 전량 궤적 정규화 데이터 |

---

## 이름 변형 이슈

다수의 작품에서 동일 NPC가 블록별로 다른 호칭으로 등장:
- 예: `홍매(시녀)` → `홍매(紅梅/시녀)` → `홍매(紅梅/정보원)` (nakyang)
- 예: `조학연(무림맹 사천 분타주)` → `조학연(무림맹주)` (third_rate)
- 예: `이준혁(장남 형)` → `이준혁(장남)` → `이준혁` (empire)

정규화 매핑은 각 작품의 추적표 내 "이름 변형 매핑" 섹션 또는 `_*_npc_data.json` 참조.

---

## 사용법

### 미완성작 블록 생산 시
1. 해당 작품의 **추적표**에서 NPC `Block N after` 값을 `Block N+1` before로 복사
2. **handoff 문서**의 이벤트 예측을 참조하여 해당 블록의 NPC 변화 방향 확인
3. 생산 완료 후 **검증 체크리스트**에서 해당 블록 항목 체크

### 완성작 참조 시
1. **최종 추적표**에서 NPC 최종 상태 확인
2. 스핀오프/시리즈 작업 시 진영 배치와 서사 궤적 요약 참조
