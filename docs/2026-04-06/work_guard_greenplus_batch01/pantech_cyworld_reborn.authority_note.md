# Authority Note — pantech_cyworld_reborn

- Date: 2026-04-06
- Terminal: 4

## 1. Authority Chain 현실

이 작품의 authority chain에는 다른 GREENPLUS 작품과 구별되는 특이점이 있다.

### 1.1 강한 authority (draft의 1차 근거)

- `material_ssot/20_pitch/canon/pantech_cyworld_reborn.md` — canonical pitch, 이 작품의 최상위 authority
- `treatments/preprocess/pantech_cyworld_reborn/profile_lock.json` — 프로필 잠금
- `treatments/preprocess/pantech_cyworld_reborn/phase0_ready_snapshot.json` — Phase0 진입 준비 확인
- `treatments/preprocess/pantech_cyworld_reborn/phase0_planning_wip.md` — Phase0 계획 WIP (순번 12/18 완료)

### 1.2 존재하나 authority 제한

- `treatments/pantech_cyworld_reborn_phase0_design.json` — live root phase0 design, 디스크에 존재
- `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json` — live root TR 70블록 draft, 디스크에 존재
- `bible/08_bi_pantech_cyworld_reborn.json` — live BI, 디스크에 존재

**그런데** canonical pitch 문서 §1 Authority에서 이 세 파일은 명시적으로 다르게 분류된다:

- phase0_design과 TR은 "live root"로 존재하지만, canonical pitch 문서의 authority chain에는 quarantine TR/BI만 "optional consistency references (not authorities)"로 기재
- BI의 `_authority_chain`은 이 세 파일을 모두 포함하지만, BI 자체가 "plot_roadmap은 live TR 전량 복사이며 BI 레벨에서 재창작하지 않았다"고 명시

### 1.3 quarantine 상태

- `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json`
- `bible/_quarantine/07_pantech_cyworld_reborn_bi.json`

Canon pitch에서 이 quarantine 파일들이 "supporting consistency references only, not authorities"로 지정되어 있다.

## 2. 충돌 지점

### 2.1 Canon pitch vs live root 파일의 authority 위상

Canon pitch 문서는 "Canonical pitch truth for pantech_cyworld_reborn is fixed in this file and replaces any prior bootstrap note"라고 선언한다. 그러면서 live root phase0/TR/BI를 authority chain에서 quarantine 참조로만 언급한다.

그런데 **디스크에는** `treatments/pantech_cyworld_reborn_phase0_design.json`과 `treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json`이 quarantine이 아닌 live root에 존재한다. BI도 `bible/08_bi_pantech_cyworld_reborn.json`에 live로 존재하며, 이 BI의 `_authority_chain`은 live phase0/TR을 포함한다.

**해석**: canon pitch가 최상위 authority이므로, live root 파일들은 consistency reference로 본다. 이 work_guard draft는 canon pitch + preprocess 4종을 1차 authority로, live phase0/TR/BI를 consistency cross-check용으로만 사용했다.

### 2.2 phase0_planning_wip 미완료

순번 12/18까지만 완료. 순번 13~18(블록별 상세, 인물 arc, NPC 디테일 등 추정)이 빠져 있어 후반 arc 세부 슬롯의 정밀도가 제한적이다.

**해석**: 이 work_guard는 순번 10~12(7대단원 골격, 입구/출구 상세, 자본 곡선)까지의 authority로 작성했다. 순번 13~18 완료 시 `tracking_slots`와 `mandatory_scene_engines`의 후반 arc 커버리지를 재검증해야 한다. 현 draft에서 이 부분은 canon pitch의 handoff note와 contamination guard를 보수적으로 반영했다.

### 2.3 Historical wording

Canon pitch의 일부 문구와 live phase0 design의 arc 구조 사이에 표현 밀도 차이가 있다. 예를 들어:
- Canon pitch: ARC-01~02를 "입장권 선점 + 쌍축 결합"으로 설명
- Live phase0: ARC-02를 "인증 병목의 반격 — 312종 충돌 로그와 베타폰 재구성"으로 확장

Canon pitch 기준 ARC-02는 아직 인증 반격이 아니라 쌍축 결합 단계이나, live phase0에서는 이미 인증 반격까지 포함한다. 이는 phase0 확장 과정에서 arc 배치가 재조정된 것으로 보인다.

**해석**: work_guard draft에서는 canonical pitch의 `mandatory_scene_engines`와 `tracking_slots`를 arc 독립적으로 작성해 이 재조정에 영향받지 않도록 했다. 구체적 arc-block 매핑은 TR 생성 시 live phase0를 따르면 된다.

## 3. 결론

| 항목 | 충돌 심각도 | 처리 |
|------|-----------|------|
| live root vs quarantine authority 위상 | LOW | canon pitch가 최상위. live root는 consistency reference. |
| phase0_planning_wip 미완료 | MEDIUM | 순번 13~18 완료 후 후반 arc 슬롯 재검증 필요. |
| historical wording 차이 | LOW | work_guard를 arc 독립적으로 작성해 회피. TR 시점 정합 필요. |

이상의 ambiguity에도 불구하고, canonical pitch + preprocess 4종의 authority가 work_guard 생성에 충분하므로 WG-V2 verdict는 PASS를 유지한다. 다만 freeze 확정은 phase0_planning_wip 순번 18 완료 + operator 확인 후가 권장된다.
