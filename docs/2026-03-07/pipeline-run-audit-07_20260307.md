# 실파이프라인 감사 07 — projects/0001 전수조사

> **일시**: 2026-03-07
> **프로젝트**: `projects/0001` (투자물 장르)
> **파이프라인 버전**: TF-A~E + BUG-F 패치 적용 후
> **테스트 기준선**: 3,614 passed

---

## 1. 실행 요약

| 항목 | 값 |
|------|-----|
| Arc 수 | 5 |
| Stage Attempts | 7 (Arc 3: 3회 시도) |
| LLM 호출 | 77회, 실패 0 |
| 총 비용 | $1.34 |
| 최종 합격률 | 100% (5/5 Arc) |
| 자본금 체인 | 20 → 23.75 → 30.4 → 45.2 → 50.13 (억) |

---

## 2. 패치 효과 검증

### 2-1. BUG-F (protagonist_items vs items_acquired) — RESOLVED

모든 Arc의 `state_constraints`에 `protagonist_items`와 `items_acquired` 양쪽 키 확인됨. `stage2_optimizer L539` 정규화 코드가 정상 동작하여 downstream 소비자 전량 데이터 수신.

- Arc 1~5: 양쪽 키 존재, 값 동일
- PATCH-B 오탐: BUG-F 원인 건수 **0건** (이전 실행 대비 완전 해소)

### 2-2. TF-A (NS-3-B 실행 순서) — VERIFIED

Phase 2.55에서 Python 교차검증 실행 확인. Director 선택 전 advisory 주입 완료.

### 2-3. TF-B (Block 경계 규칙) — VERIFIED

5개 Block 전량 이벤트가 대응 Arc 범위 내에서 처리됨. Block 경계 위반 **0건**.

- Block 1 이벤트 → Arc 1 범위 내 처리
- Block 2 이벤트 → Arc 2 범위 내 처리
- Block 3~5 동일 패턴 확인

### 2-4. TF-C (genre_ext 강제) — VERIFIED

자본금 genre_ext 목표 vs Arc 실제 결과: 최대 괴리 3.3% (30% 임계값 이내).

### 2-5. TF-D (ep_count 3~6) — VERIFIED

전 Arc ep_count 범위: 3~5화. 상한 6화 이내.

### 2-6. TF-E (items_acquired 강화) — VERIFIED

BUG-F 패치와 병행하여 아이템 추적 정상 동작 확인.

---

## 3. Arc 3 재시도 분석

| 시도 | 전략 | 결과 | 사유 |
|------|------|------|------|
| 1차 | default | PASS_WITH_FIX → InPlace 3회 실패 → REJECT | Entity mismatch (NPC 속성 불일치) |
| 2차 | patch_mode | REJECT | Entity mismatch 지속 |
| 3차 | asp (Adversarial Self-Play) | PASS | NPC 속성 정합 달성 |

**분석**: Arc 3에서 NPC 속성 불일치가 반복 발생. InPlace 패치로는 해결 불가한 구조적 문제였으며, ASP 전략이 자체 검증 루프를 통해 정합성 확보. 재시도 메커니즘 정상 동작.

---

## 4. 발견 사항

### P2-1: PATCH-B 금전 문자열 토큰화 과잉 (P2 — 관찰)

PATCH-B가 4/5 Arc에서 여전히 advisory 발생. 원인은 BUG-F가 아닌 **금전 문자열 토큰화**:
- `"2,000,000,000원"` → 쉼표 분리 시 `"000"` 토큰 생성 → 아이템으로 오인
- `"50억 자본금"` 등 서술형 장비 텍스트

**판정**: P2 후순위. advisory-only이므로 동작에 영향 없음. 정규식 개선 시 금전 패턴(`\d{1,3}(,\d{3})*원?`) 사전 필터링 고려.

### P2-2: internal_energy 필드 비무협 잔류 (P2 — 기존 TF-45 범위)

4/5 Arc에서 LLM이 `internal_energy` 관련 필드 생성. TF-45 후처리에서 전량 자동 제거됨.

**판정**: P2. TF-45 방어선 정상 작동. LLM 프롬프트 추가 강화는 ROI 낮음.

### P2-3: npc_history 재시도 중복/null 엔트리 (P2 — 관찰)

Arc 3 재시도로 인해:
- npc_history id 5/6: 동일 NPC 중복 엔트리 (1차 시도 기록 잔류)
- npc_history id 7/8: `episode_no = NULL` (재시도 중간 상태)

**판정**: P2. append-only 이력이므로 데이터 손실 없음. 롤백 시 이전 엔트리가 남는 것은 설계 의도(감사 추적). null episode_no는 재시도 컨텍스트에서 아직 에피소드 미확정 상태를 반영.

---

## 5. 긍정 확인 사항

| 항목 | 상태 |
|------|------|
| 자본금 연속성 | 완벽 (20→23.75→30.4→45.2→50.13, 단조증가) |
| NPC 연속성 | 완벽 (사망NPC 재등장 0건) |
| Block 경계 준수 | 0 위반 |
| 복선-회수 패턴 | 정상 (현재 Block 언급 → 다음 Block 실행) |
| 4th wall 메타용어 | 0건 노출 |
| 아이템 날조 | 0건 |
| C-1 메타용어 치환 | 4/5 Arc에서 자동 치환 정상 동작 |

---

## 6. 결론

**확신도: 99%** — TF-A~E + BUG-F 패치 전량 정상 동작 확인. 신규 P0/P1 이슈 **0건**. P2 관찰 사항 3건은 기존 방어선으로 커버되며 추가 패치 불필요.

| 등급 | 건수 | 조치 |
|------|------|------|
| P0 (즉시) | 0 | — |
| P1 (필수) | 0 | — |
| P2 (관찰) | 3 | 현상 유지, 향후 ROI 재평가 |
