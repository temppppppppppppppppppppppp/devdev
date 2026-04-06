# WG-V2 Verdict — pantech_cyworld_reborn

- Date: 2026-04-06
- Terminal: 4
- Target work: pantech_cyworld_reborn
- Draft file: `pantech_cyworld_reborn.work_guard.yaml`

## Authority Set Used

1. `material_ssot/20_pitch/pitch-philosophy.md`
2. `material_ssot/20_pitch/protagonist-first-constitution.md`
3. `material_ssot/20_pitch/work-guard-translation-map.md`
4. `docs/2026-04-06/work-guard-global-contract-promotion-decision.md`
5. `docs/2026-04-06/work-guard-validator-checklist-spec.md`
6. `docs/2026-04-06/wg-v2-freeze-checklist.md`
7. `material_ssot/20_pitch/canon/pantech_cyworld_reborn.md` (canonical pitch)
8. `treatments/preprocess/pantech_cyworld_reborn/profile_lock.json`
9. `treatments/preprocess/pantech_cyworld_reborn/phase0_ready_snapshot.json`
10. `treatments/preprocess/pantech_cyworld_reborn/phase0_planning_wip.md` (순번 10~12)
11. `treatments/pantech_cyworld_reborn_phase0_design.json` (live phase0 — consistency reference)
12. `bible/08_bi_pantech_cyworld_reborn.json` (live BI — consistency reference)

## WG-V2 Checklist

### 1. One-Line Truth — YES

`one_line_truth`가 protagonist-first 장악 판타지를 직접 말한다: "유통 계열사에 밀려난 오너 3세가 … 모두가 자기 관문을 거치게 만든다." Generic theme 소개가 아니라 주인공이 뭘 장악하는지가 바로 읽힌다.

### 2. Protagonist-First Purity — YES

전생 실패는 판의 불리함(전통 계열 결재선)이지 주인공 과실이 아니다. 회개물 스타트, 자기연민 소비가 `forbidden_flattenings`에 명시적으로 잡혀 있다.

### 3. Tracking Slots — YES

4개 slot 전부 서열 상승/통제권 회수/방어선 확장/병목 형성 축이다. "성장", "성공" 같은 generic slot 없음.

### 4. Signature Scene Engine — YES

3개 엔진 모두 주인공 고유 인과를 증명하는 구조:
- 금융 레버리지 장면: 회귀 타임라인 → 숫자 환전 → 회의실 판 뒤집기
- 인증 반격 장면: 312종 충돌 로그 → 품질검증 → 공개 돌파
- 승계전 역전 장면: 실적·문서·지분으로 감사/형제 프레임 되받아치기

Block 1 간판 장면(CB 350억 승인 + 차우진 태도 영수증)이 첫 번째 엔진에 정확히 잡힌다.

### 5. Protagonist Weapon — YES

3개 무기 모두 작품 특유의 인과:
- 거시 타임라인 → 숫자 환전 (팬택/싸이월드 특유)
- 4축 결합 실행력 (이 작품만의 금융+제품+인증+선점 구조)
- 거시 선독 vs 미시 불가의 이중 구조

Generic competence ("리더십", "분석력")로 흐르지 않았다.

### 6. Reward Vector — YES

`evaluation_thresholds`가 태도 변화 영수증 중심:
- Block 1: CB 승인 + 차우진 "숫자만큼은 틀리지 않았다"
- Block 3: 3종 입장권 (이사회 배석권, 협상권, 직보 라인)
- 큰 피해 직후 반격 자산/입장권 확보

`observer_tiers` 8계층이 태도 변화 순서를 잡고 있다. 초반 보상이 현금이 아니라 권한 입장권임이 명확.

### 7. Crisis Doctrine — YES

- 선독: 거시 타임라인으로 병목/위기 조기 감지
- 대비: 금융 액션으로 입장권 사전 매입
- 최소 피해 통제: `custom_rules`에 "위기는 피해 연출보다 우선순위 선택권 증명"
- 보상: "반격 예약 없는 손해 금지"가 명시적 — 구체 예시까지 잡혀 있음 (돈→증거, 시연→충돌 로그, 동결→ABS)

### 8. Forbidden Flattenings Coverage — YES

10개 항목. 기본 7대 치명 drift 전부 포함 + 이 작품 특유 3개 추가:
- 회귀 지식 만능 예언화
- 팬택/싸이월드 분리 전개
- 단일 자본 투하 즉시 해결

### 9. Translation Discipline — YES

upstream 철학 원문 복붙 없음. 교육용 설명문 없음. 전부 runtime doctrine으로 압축.

### 10. Work Specificity — YES

이 `work_guard`를 다른 작품에 그대로 붙이면 즉시 어색하다:
- 팬택·싸이월드·프론티어 원·CB·ABS·312종 충돌 로그·통신사 인증·일촌 그래프·도토리 결제 등 작품 특유 어휘가 전면 관통
- `slip_up`/`suspicion_pressure` 회귀 제약이 고유하게 잡혀 있음
- `mandatory_lexicon` 20개 전부 이 작품 고유 도메인

## WG-V2 Result: PASS

- `NO` 항목: 0개
- `WEAK` 항목: 0개
- 4번(Signature Scene Engine), 5번(Protagonist Weapon), 6번(Reward Vector) 모두 `YES`

## Weak Points

1. **live TR/BI는 아직 quarantine 상태**: canon pitch + preprocess + phase0_planning_wip까지는 강하지만, live root TR(`treatments/08_pantech_cyworld_reborn_tr_block_070_draft.json`)과 BI(`bible/08_bi_pantech_cyworld_reborn.json`)의 authority chain 위치가 canon pitch 문서에서 "optional consistency references (not authorities)"로 명시되어 있다. 이 work_guard draft는 canonical pitch + preprocess authority만으로 만들었으며, live TR/BI와의 세부 정합은 WG-V3 drift audit 시점에서 재확인해야 한다.

2. **phase0_planning_wip 순번 13~18 미완료**: phase0_planning_wip가 순번 12/18까지만 완료되어 있다. 순번 13~18 완료 후 work_guard 내 세부 슬롯(특히 후반 ARC-05~07의 인프라 병목·계열 분리·생활계정 확장 관련)을 재검증할 필요가 있다.

3. **slip_up/suspicion_pressure 에스컬레이션 스케줄**: work_guard에 "아크별 스케줄대로 지킨다"는 custom_rule만 있고, 구체 빈도는 phase0_design의 `slip_up_schedule`에 위임되어 있다. 이 위임 자체는 적절하나, freeze 후 TR 생성 시 스케줄 반영 여부를 WG-V3에서 확인해야 한다.

## Next Action

- 이 draft는 **freeze candidate**로 올린다.
- freeze 확정은 phase0_planning_wip 순번 18 완료 후 operator 최종 확인 시.
- freeze 후 TR 생성 → WG-V3 drift audit 순서를 따른다.
- live TR/BI quarantine 해제 시 work_guard와의 정합을 재확인한다.
