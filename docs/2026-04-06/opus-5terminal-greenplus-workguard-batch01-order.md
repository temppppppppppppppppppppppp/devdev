# Opus 5-Terminal GREENPLUS WorkGuard Batch 01 Order

- Date: 2026-04-06
- Status: operator-ready after 3-pass self-audit
- Scope: GREENPLUS pair batch only
- Mode: parallel material-side workguard drafting
- Code changes: forbidden

## 1. Objective

현재 `GREENPLUS`로 잠긴 pair들에 대해 `work_guard` 초안을 일괄 생성한다.

이번 배치의 목표는 아래다.

- `GREENPLUS` 작품만 대상으로 한다
- 각 작품별 `work_guard draft`를 만든다
- 각 draft마다 `WG-V2` 기준 self-verdict를 남긴다
- `TR/BI`나 코드, 파이프라인은 건드리지 않는다

이번 배치는 `runtime install`이 아니라 `material-side draft/freeze prep` 배치다.

## 2. Global Rules

### 반드시 지킬 것

- `AGENTS.md`의 root pipeline order는 건드리지 않는다
- `work_guard`는 `global material-side standard companion artifact`로 다룬다
- standard material-side flow는 `Phase 0 design -> work_guard draft/freeze -> TR -> BI`로 본다
- 없는 authority를 상상해서 채우지 않는다
- 불확실하면 억지 PASS 대신 `HOLD`로 남긴다

### 이번 배치에서 금지

- 코드 수정
- 파이프라인 수정
- `TR` 수정
- `BI` 수정
- canon pitch 수정
- `work_guards/**/default_work_guard.yaml` 템플릿 수정
- `{project}/config/work_guard.yaml` 직접 배포

즉 이번 배치는 `draft generation + freeze-prep only`다.

## 3. Output Contract

이번 배치 산출물은 모두 아래 폴더 기준으로 만든다.

- batch root:
  - `docs/2026-04-06/work_guard_greenplus_batch01/`

각 작품마다 아래 2개를 만든다.

1. `{work_id}.work_guard.yaml`
2. `{work_id}.wg_v2_verdict.md`

선택 산출물:

- authority conflict가 있을 때만 `{work_id}.authority_note.md`

이번 배치에서 만든 yaml은 `freeze candidate`이며, 아직 runtime install본으로 보지 않는다.

배치 시작 시:

- Terminal 1이 batch root를 먼저 생성한다
- 이후에는 각 터미널이 자기 작품 파일만 쓴다

## 4. Primary References

모든 터미널 공통 read order:

1. `material_ssot/20_pitch/pitch-philosophy.md`
2. `material_ssot/20_pitch/protagonist-first-constitution.md`
3. `material_ssot/20_pitch/work-guard-translation-map.md`
4. `docs/2026-04-06/work-guard-global-contract-promotion-decision.md`
5. `docs/2026-04-06/work-guard-validator-checklist-spec.md`
6. `docs/2026-04-06/wg-v2-freeze-checklist.md`
7. 대상 work의 canonical pitch
8. 대상 work의 preprocess / phase0 / TR / BI authority chain

Family note:

- `blockguide` works는 `docs/blockguide/SSOT_blockguide-integrated-order.md`를 참고해도 되지만, 이번 배치의 1차 authority는 `canon pitch + preprocess/phase0 + live TR/BI`
- `wuxguide` work는 `docs/wuxguide/SSOT_wuxguide-integrated-order.md`를 같이 본다

## 5. Target Set

이번 배치 대상은 아래 8작품이다.

- `chaebol_allowance_zero`
- `chaebol_ent_empire`
- `defense_defect_engineer`
- `failed_future_ceo_intern`
- `gatekeeper_heir`
- `office_checkup_next_day`
- `pantech_cyworld_reborn`
- `wuxia_heavenly_physician`

비대상:

- `GREEN` only pair
- `YELLOW` pair
- runtime project install

## 6. Terminal Ownership

### Terminal 1

담당:

- `office_checkup_next_day`
- `gatekeeper_heir`

이유:

- 현재 protagonist-first exemplar로 가장 깨끗한 blockguide 축
- batch 기준선으로 쓰기 좋음

### Terminal 2

담당:

- `defense_defect_engineer`
- `chaebol_allowance_zero`

이유:

- 둘 다 `protagonist-only proof scene`과 `권한 회수`가 선명함
- 산업 언어가 강해서 `mandatory_lexicon / control_axes` 품질이 중요함

### Terminal 3

담당:

- `failed_future_ceo_intern`
- `chaebol_ent_empire`

이유:

- 둘 다 pair locked / promotion-approved 계열
- 단, `chaebol_ent_empire`는 preprocess/phase0 부재라 authority 보수적으로 다뤄야 함

### Terminal 4

담당:

- `pantech_cyworld_reborn`

이유:

- 구조는 강하지만 authority note와 live-material alignment를 한번 더 조심해서 봐야 함
- 단독 처리로 충돌 메모까지 같이 남기는 편이 안전함

### Terminal 5

담당:

- `wuxia_heavenly_physician`

이유:

- 유일한 `wuxguide` family
- blockguide batch와 분리해 semantic drift를 막는 편이 좋음

## 7. Work-Level Authority Notes

### `office_checkup_next_day`

- canon pitch 있음
- preprocess 있음
- live phase0 있음
- live TR/BI 있음
- straight draft candidate

### `gatekeeper_heir`

- canon pitch 있음
- preprocess 있음
- live phase0 있음
- live TR/BI 있음
- straight draft candidate

### `defense_defect_engineer`

- canon pitch 있음
- preprocess 있음
- live phase0 있음
- live TR/BI 있음
- straight draft candidate

### `chaebol_allowance_zero`

- canon pitch 있음
- preprocess 있음
- live phase0 있음
- live TR/BI 있음
- straight draft candidate

### `failed_future_ceo_intern`

- canon pitch 있음
- preprocess 있음
- live phase0 있음
- live TR/BI 있음
- straight draft candidate

### `chaebol_ent_empire`

- canon pitch 있음
- live TR/BI 있음
- preprocess/phase0 부재
- 이 작품은 `canon pitch + live TR/BI` 기준으로만 draft를 만든다
- 부족한 truth를 상상 보강하지 말고, 애매하면 `HOLD`

### `pantech_cyworld_reborn`

- canon pitch 있음
- preprocess 있음
- live phase0/TR/BI 존재 여부와 canon note의 historical wording이 어긋날 수 있음
- 현재 disk reality와 canon pitch를 함께 읽고, 충돌 시 `authority_note`를 남긴다

### `wuxia_heavenly_physician`

- canon pitch 있음
- preprocess 있음
- live phase0 authority는 `phase0_ready_snapshot` 대체 규칙을 따른다
- live TR/BI는 consistency reference로만 본다

## 8. Draft Rule

각 yaml은 아래 원칙으로 만든다.

- 짧고 압축된 runtime doctrine만 넣는다
- 교육용 설명문 금지
- 장문 철학 복붙 금지
- 작품 특유의 `one_line_truth`, `tracking_slots`, `mandatory_scene_engines`, `forbidden_flattenings`, `protagonist_weapon`은 반드시 들어간다
- 가능하면 `mandatory_lexicon`, `control_axes`, `business_axes`, `protagonist_evaluation`도 넣는다

## 9. WG-V2 Verdict Rule

각 터미널은 자기 작품마다 `wg_v2_verdict.md`에 아래 중 하나를 남긴다.

- `PASS`
- `HOLD`
- `REJECT`

원칙:

- 억지 PASS 금지
- `chaebol_ent_empire`처럼 upstream authority가 얇은 경우, generic draft보다 `HOLD + reason`가 낫다

각 verdict note 최소 포함 항목:

1. target work
2. authority set used
3. WG-V2 result
4. weak points
5. next action

## 10. Freeze Readiness Definition

이번 배치에서 `freeze-ready`로 보는 최소 조건:

- hard gate key 전부 존재
- `one_line_truth`가 protagonist-first promise를 직접 말함
- 첫 블록 간판 장면이 `mandatory_scene_engines`에 잡힘
- `protagonist_weapon`이 generic competence가 아님
- `forbidden_flattenings`가 치명 drift를 충분히 막음
- `WG-V2` 결과가 `PASS`

`PASS`가 아니면 이번 배치에선 `draft complete, not freeze-ready`로 둔다.

## 11. Delivery Rule

각 터미널은 자기 담당 작품 결과만 쓴다.

공유 파일 수정 금지:

- batch index
- README
- alias files
- canon docs
- `AGENTS.md`

즉 write set은 자기 작품 파일만 허용한다.

## 12. Batch Close Condition

배치 완료 조건:

- 8작품 모두 `work_guard draft` 존재
- 8작품 모두 `WG-V2 verdict` 존재
- authority conflict가 있는 작품은 note 존재
- `TR/BI/code` 수정 0건

## 13. Recommended Execution Order

속도보다 기준선 확보가 중요하므로 아래 순서를 권장한다.

1. Terminal 1이 `office_checkup_next_day`를 먼저 완료
2. 그 표현 밀도를 참고해 Terminal 2와 Terminal 3이 동시 진행
3. Terminal 4와 Terminal 5는 단독 특수 케이스 처리
4. 두 번째 작품은 각 터미널이 첫 작품 verdict 감각을 잡은 뒤 진행

## 14. One-Line Order For Each Terminal

- Terminal 1: exemplar blockguide 2작품의 `freeze-ready work_guard draft`를 만든다
- Terminal 2: proof scene/권한 회수형 blockguide 2작품의 `freeze-ready work_guard draft`를 만든다
- Terminal 3: pair-locked blockguide 2작품의 `work_guard draft`를 만들되, authority 부족 시 `HOLD`를 우선한다
- Terminal 4: `pantech_cyworld_reborn`의 authority ambiguity를 관리하며 `work_guard draft + verdict + note`를 만든다
- Terminal 5: `wuxia_heavenly_physician`를 `wuxguide` semantics로 `work_guard draft + verdict`까지 닫는다
