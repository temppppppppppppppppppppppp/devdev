# Opus 5-Terminal `chaebol_ent_empire` HOLD Closure Order

- Date: 2026-04-06
- Status: operator-ready after 3-pass self-audit
- Scope: `chaebol_ent_empire` `work_guard` HOLD closure only
- Family: `blockguide`
- Mode: parallel Stage 0 preprocess completion + workguard re-audit
- Code changes: forbidden

## 1. Objective

현재 `chaebol_ent_empire`는 `work_guard`가 draft까지는 만들어졌지만 `WG-V2 HOLD` 상태다.

이번 배치의 목표는 아래다.

- missing Stage 0 preprocess 4-pack을 만든다
- HOLD 원인인 `Reward Vector`, `Crisis Doctrine`을 upstream truth 안에서 보강한다
- `work_guard`를 재작성하고 `WG-V2`를 다시 돌린다
- `PASS`가 나오면 `work_guards/03_chaebol_ent_empire.yaml`까지 publish한다

핵심 해석:

- 이번 작업의 본체는 `work_guard` 자체가 아니라 `preprocess authority`를 채우는 것이다
- 상상 보강으로 PASS를 억지 부여하면 안 된다

## 2. Current HOLD Reason

현재 기준 문서:

- `material_ssot/20_pitch/canon/chaebol_ent_empire.md`
- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.work_guard.yaml`
- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.wg_v2_verdict.md`
- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.authority_note.md`

현재 HOLD 이유는 3개다.

1. `treatments/preprocess/chaebol_ent_empire/` 자체가 없다
2. `Reward Vector`가 자산 증가 쪽으로 기울고 권한 이동 세부가 얇다
3. `Crisis Doctrine`이 `선독 -> 대비 -> 최소 피해 -> 즉시 보상` 구조로 명시되지 않았다

즉 closure 조건은:

- preprocess 4-pack 생성
- reward vector를 권한/서열/접근권 언어로 명확화
- crisis doctrine을 protagonist-first 위기 철학으로 명시
- 그 결과로 WG-V2의 6번, 7번을 `YES`로 끌어올리는 것

## 3. Global Rules

### 반드시 지킬 것

- canonical authority 1순위는 `material_ssot/20_pitch/canon/chaebol_ent_empire.md`
- live `TR/BI`는 consistency reference로만 사용한다
- 없는 사실, 새 인물, 새 사업축, 새 위기축을 상상으로 추가하지 않는다
- `preprocess 4-pack -> work_guard re-audit -> PASS 시 publish` 순서를 지킨다

### 이번 배치에서 금지

- 코드 수정
- 파이프라인 수정
- canon pitch 수정
- live `TR` 수정
- live `BI` 수정
- 다른 작품 preprocess/workguard 수정
- `default_work_guard.yaml` 수정

## 4. Output Contract

### 4.1 Canonical outputs

아래 4개를 최종 canonical 산출물로 만든다.

- `treatments/preprocess/chaebol_ent_empire/source_manifest.json`
- `treatments/preprocess/chaebol_ent_empire/profile_lock.json`
- `treatments/preprocess/chaebol_ent_empire/material_bundle_summary.json`
- `treatments/preprocess/chaebol_ent_empire/phase0_ready_snapshot.json`

### 4.2 Operator-side supporting outputs

필요 시 아래 보조 산출물을 만든다.

- `docs/2026-04-06/chaebol_ent_empire_hold_closure/reward_crisis_doctrine_note.md`
- `docs/2026-04-06/chaebol_ent_empire_hold_closure/manual_audit_note.md`
- `docs/2026-04-06/chaebol_ent_empire_hold_closure/final_closure_report.md`

### 4.3 Refresh outputs

preprocess 4-pack이 잠기면 아래를 refresh한다.

- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.work_guard.yaml`
- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.wg_v2_verdict.md`

### 4.4 Publish output

`WG-V2 PASS`일 때만 아래를 만든다.

- `work_guards/03_chaebol_ent_empire.yaml`

`HOLD/REJECT`면 publish하지 않는다.

## 5. Common Read Order

모든 터미널 공통 read order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
3. `전처리_ssot/docs/stage0_source_manifest_harness.md`
4. `전처리_ssot/docs/stage0_profile_lock_harness.md`
5. `전처리_ssot/docs/stage0_material_collection_harness.md`
6. `material_ssot/20_pitch/pitch-philosophy.md`
7. `material_ssot/20_pitch/protagonist-first-constitution.md`
8. `material_ssot/20_pitch/work-guard-translation-map.md`
9. `material_ssot/20_pitch/canon/chaebol_ent_empire.md`
10. `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.wg_v2_verdict.md`
11. `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.authority_note.md`
12. live consistency refs:
   - `treatments/03_chaebol_ent_empire_tr_block_070_draft.json`
   - `bible/03_bi_chaebol_ent_empire.json`

Shape exemplars only:

- `treatments/preprocess/chaebol_allowance_zero/`
- `treatments/preprocess/pantech_cyworld_reborn/`

중요:

- exemplar는 형식 참고용이다
- `chaebol_ent_empire`의 truth authority가 아니다

## 6. Terminal Ownership

### Terminal 1

담당:

- preprocess root bootstrap
- `source_manifest.json`

write set:

- `treatments/preprocess/chaebol_ent_empire/`
- `treatments/preprocess/chaebol_ent_empire/source_manifest.json`

세부 역할:

- `_template` 또는 exemplar 구조를 참고해 preprocess root를 먼저 만든다
- canonical source / reference-only source / core_materials / npc_pool / crisis_pool / hard_constraints / do_not_fake를 잠근다
- `reward`와 `crisis`는 새로 만들지 말고 canon pitch와 live pair에 이미 있는 것만 정리한다

### Terminal 2

담당:

- `profile_lock.json`

write set:

- `treatments/preprocess/chaebol_ent_empire/profile_lock.json`

세부 역할:

- `primary_profile = entertainment_media_profile`
- `secondary_profile = business_growth_profile`
- `resource_axis`, `power_axis`, `control_axis`, `payoff_axis`, `failure_axis`를 작품 truth에 맞게 잠근다
- 특히 `Reward Vector`가 돈만이 아니라 `배석권/결정권/접근권/자율권/표준 선점`으로 읽히게 축을 세운다

### Terminal 3

담당:

- `material_bundle_summary.json`

write set:

- `treatments/preprocess/chaebol_ent_empire/material_bundle_summary.json`

세부 역할:

- events / npc_candidates / crisis_candidates / terms / scene_details / notes를 채운다
- 위기 후보는 `선독 가능한 징후`, `대비 수단`, `최소 피해 통제`, `즉시 보상`이 downstream에서 읽히도록 압축한다
- 기존 pitch의 proof scene, VIP 라운지 무대, 인재 배치, 패키지 구조를 재료 중심 언어로 정리한다

### Terminal 4

담당:

- reward/crisis doctrine 보강 메모
- 수동 감리 메모 초안

write set:

- `docs/2026-04-06/chaebol_ent_empire_hold_closure/reward_crisis_doctrine_note.md`
- `docs/2026-04-06/chaebol_ent_empire_hold_closure/manual_audit_note.md`

세부 역할:

- 현재 HOLD의 6번, 7번이 왜 약한지 작품 언어로 다시 정리한다
- `first block reward`를 자산 증가가 아니라 권한 이동과 평가 수정 언어로 어떻게 번역할지 적는다
- `early antagonist shape`와 `proof scene`에서 어떤 위기 doctrine을 추출할 수 있는지 적는다
- 새 truth를 발명하지 말고, canon pitch와 consistency refs 안에서만 번역한다

### Terminal 5

담당:

- `phase0_ready_snapshot.json`
- refreshed `work_guard`
- refreshed `WG-V2 verdict`
- publish if PASS
- final closure report

write set:

- `treatments/preprocess/chaebol_ent_empire/phase0_ready_snapshot.json`
- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.work_guard.yaml`
- `docs/2026-04-06/work_guard_greenplus_batch01/chaebol_ent_empire.wg_v2_verdict.md`
- `work_guards/03_chaebol_ent_empire.yaml` if PASS
- `docs/2026-04-06/chaebol_ent_empire_hold_closure/final_closure_report.md`

세부 역할:

- Terminal 1~4 산출물 수신 후 snapshot을 잠근다
- `manual_audit_pass`는 억지 true 금지
- preprocess 4-pack을 authority로 삼아 work_guard를 재작성한다
- `WG-V2`를 다시 돌린다
- `PASS`면 publish, 아니면 HOLD 유지 후 종료한다

## 7. Execution Order

권장 실행 순서는 아래다.

1. Terminal 1이 preprocess root를 먼저 만든다
2. Terminal 2, 3, 4가 병렬 진행
3. Terminal 5는 먼저 모든 authority를 읽고 skeleton을 준비한다
4. Terminal 1~4 결과가 모이면 Terminal 5가 최종 통합

즉:

- `T1 bootstrap`
- `T2/T3/T4 parallel`
- `T5 final integration`

## 8. Reward / Crisis Closure Rule

이번 closure에서 제일 중요한 건 아래 두 개다.

### 8.1 Reward Vector

이 작품의 첫 블록 보상은 아래 4개를 함께 보여야 한다.

- `사람은 볼 줄 아는 놈`이라는 평가 수정
- 다음 인재/행사/파트너에 접근할 수 있는 접근권
- 세령컬처웍스 내부에서의 제한적 결정권
- 향후 패키지 구조를 밀 수 있는 자율권의 첫 조각

금지:

- `120억 + 7억`만 강조하고 끝내기
- 태도 변화 없이 숫자만 남기기

### 8.2 Crisis Doctrine

이 작품의 위기는 아래 구조로 번역되어야 한다.

- 주인공은 먼저 `누가 웃고 있는지`, `어디서 무대가 비는지`, `어떤 인재가 방치됐는지`를 읽는다
- 빈손으로 들어가지 않고, 최소한 `배치 카드`와 `증명 무대`를 쥐고 들어간다
- 전부를 구하는 대신 가장 비싼 proof만 살린다
- 피해나 압박 뒤에는 반드시 다음 입장권, 태도 변화, 부킹, 계약, 권한 조각이 남아야 한다

금지:

- 위기를 그냥 당하고 버티기
- 성공 뒤 pure punishment spiral
- 설명 없이 운빨로만 넘기기

## 9. Freeze / PASS Definition

이번 배치에서 `closure complete`로 보는 최소 조건:

1. preprocess 4-pack 존재
2. `phase0_ready_snapshot.manual_audit_pass == true`
3. refreshed `work_guard` 존재
4. refreshed `WG-V2 verdict == PASS`
5. `work_guards/03_chaebol_ent_empire.yaml` publish 완료

아래면 partial close다.

- preprocess 4-pack은 생겼지만 `WG-V2 HOLD`
- 이 경우 publish 없이 종료하고, remaining weak point를 closure report에 남긴다

## 10. Delivery Rule

각 터미널은 자기 write set만 수정한다.

공유 파일 수정 금지:

- `AGENTS.md`
- canon pitch
- 다른 작품 preprocess 4-pack
- 다른 작품 work_guard
- README 전역 문서

예외:

- Terminal 5만 `work_guards/03_chaebol_ent_empire.yaml`를 건드릴 수 있다

## 11. One-Line Order Per Terminal

- Terminal 1: `chaebol_ent_empire` preprocess root를 열고 source authority를 잠근다
- Terminal 2: reward/power/control 축이 살아 있는 `profile_lock.json`을 만든다
- Terminal 3: 엔터 배치·증명·패키지 전장을 `material_bundle_summary.json`으로 압축한다
- Terminal 4: HOLD 원인인 reward/crisis doctrine을 작품 언어로 다시 번역해 note로 남긴다
- Terminal 5: preprocess 4-pack을 잠그고 work_guard를 재감리해 PASS면 publish까지 닫는다
