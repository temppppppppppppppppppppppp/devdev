# Material SSOT WorkGuard Translation Absorption Execution Plan

- Date: 2026-04-06
- Scope: documentation-only execution plan
- Status: active plan
- Target: absorb `philosophy-to-work-guard-translation-map.md` into canonical `material_ssot` stage governance
- Edit scope in this wave: docs only

## 1. Decision

네, 이 문서는 `material_ssot` 체계에 흡수하는 쪽이 맞다.

다만 흡수 위치는 `00_governance`가 아니라 `20_pitch`가 더 적절하다.

권장 canonical home:

- `material_ssot/20_pitch/work-guard-translation-map.md`

이유는 간단하다.

- source law가 이미 `material_ssot/20_pitch/protagonist-first-constitution.md`와 `material_ssot/20_pitch/pitch-philosophy.md`에 있다
- 이 문서는 system-wide governance보다 `pitch truth -> downstream runtime guard` 번역 규칙에 가깝다
- 즉 `20_pitch`의 하위 bridge 문서로 두는 편이 stage 의미가 가장 선명하다

한 줄 요약:

- `docs/2026-04-06/...`에 남아 있는 동안은 working note다
- `material_ssot/20_pitch/...`로 들어가야 stage-canonical bridge 문서가 된다

## 2. Why `20_pitch`, Not `00_governance`

### `20_pitch`에 두어야 하는 이유

- 현재 house-law source가 모두 `20_pitch`에 있다
- 이 문서는 `pitch philosophy`를 `work_guard` 문법으로 번역하는 문서다
- 즉 “무엇을 믿는가”와 “그 믿음을 어떻게 runtime용으로 압축하는가”가 같은 묶음에 있는 편이 읽기 쉽다

Evidence:

- [20_pitch README](../../material_ssot/20_pitch/README.md)
- [pitch-philosophy.md](../../material_ssot/20_pitch/pitch-philosophy.md)
- [protagonist-first-constitution.md](../../material_ssot/20_pitch/protagonist-first-constitution.md)

### `00_governance`에 두지 않는 이유

- `00_governance`는 root authority map, stage read order, legacy map 같은 전역 stage-axis 문서가 중심이다
- 번역표는 전역 권위 지도보다 `pitch-stage derivative law`에 가깝다
- 여기에 두면 문서 성격이 너무 커 보이고, 실제 읽기 진입점도 오히려 흐려진다

Evidence:

- [material_ssot README](../../material_ssot/README.md)
- [authority-map.md](../../material_ssot/00_governance/authority-map.md)
- [stage-read-order.md](../../material_ssot/00_governance/stage-read-order.md)

## 3. What This Absorption Should Mean

이번 흡수는 “파일을 옮기는 것” 이상을 뜻한다.

최소한 아래까지 완료되어야 진짜 흡수라고 본다.

1. canonical path를 `material_ssot/20_pitch/` 아래로 승격
2. `20_pitch/README.md`에서 current canon set으로 명시
3. `pitch-philosophy.md`에서 downstream translation reference로 연결
4. dated `docs/2026-04-06/...` 문서는 historical working note로 내림

즉:

- canonical authority는 `material_ssot`
- dated doc는 execution trace

## 4. Non-Goals

이번 흡수 웨이브에서 하지 않을 것:

- router 계약 수정
- preprocess readiness에 `work_guard` 강제 추가
- `work_guard.yaml` 자동 생성 코드 추가
- `TR/BI` builder CLI 수정
- live `treatments/` / `bible/` 경로 수정

이번 문서는 어디까지나 `문서 authority 정리` execution plan이다.

## 5. Proposed Target State

### Canonical

- `material_ssot/20_pitch/work-guard-translation-map.md`

### Related Canonical References

- `material_ssot/20_pitch/protagonist-first-constitution.md`
- `material_ssot/20_pitch/pitch-philosophy.md`
- `material_ssot/20_pitch/pitch-selection-checklist.md`

### Historical Trace

- `docs/2026-04-06/philosophy-to-work-guard-translation-map.md`

Historical trace는 남겨도 되지만, canonical role은 잃어야 한다.

## 6. Execution Steps

### Step 1. Re-audit the translation map against current pitch law

목적:

- `translation map`이 현재 `constitution` / `pitch philosophy`와 모순 없는지 다시 확인

완료 기준:

- 조항과 field map 사이 충돌 없음
- `work_guard` 필드가 실제 runtime consumer와 일치

### Step 2. Promote the document into `material_ssot/20_pitch`

목적:

- dated working doc를 stage-canonical bridge doc로 승격

구체 행동:

- `material_ssot/20_pitch/work-guard-translation-map.md` 생성
- 현재 dated 문서 내용을 canonical 문서로 복제 또는 이동

완료 기준:

- canonical path가 `material_ssot/20_pitch/` 아래 존재

### Step 3. Update `material_ssot/20_pitch/README.md`

목적:

- `20_pitch`가 이제 “house law + downstream translation bridge”까지 포함한다는 것을 명시

추가할 내용:

- `work-guard-translation-map.md`가 current canonical bridge doc라는 한 줄

완료 기준:

- `README`만 읽어도 새 문서의 역할이 보임

### Step 4. Update `pitch-philosophy.md`

목적:

- house law 문서와 translation bridge 문서 사이 참조선을 고정

추가할 내용:

- downstream runtime translation reference로 `work-guard-translation-map.md` 링크

완료 기준:

- operator가 `pitch philosophy -> translation map` 경로를 바로 따라갈 수 있음

### Step 5. Downgrade the dated doc to historical trace

목적:

- 중복 authority를 방지

권장 방식:

- dated doc는 유지 가능
- 단, 제목 또는 상단 note에서 `historical working draft` 또는 `superseded by material_ssot canonical path`를 명시

완료 기준:

- 같은 내용의 dual-canonical state가 남지 않음

## 7. Acceptance Criteria

아래가 다 만족되면 흡수 완료로 본다.

1. `material_ssot/20_pitch/work-guard-translation-map.md`가 존재한다
2. `material_ssot/20_pitch/README.md`가 새 문서를 canon으로 가리킨다
3. `material_ssot/20_pitch/pitch-philosophy.md`가 새 문서를 downstream bridge로 가리킨다
4. dated doc는 canonical authority로 오해되지 않는다
5. `material_ssot` read order상 `20_pitch`만 읽어도 house law와 translation bridge를 모두 찾을 수 있다

## 8. Risks

### Risk 1. Canon duplication

- dated doc와 canonical doc가 둘 다 정본처럼 남을 수 있다

대응:

- dated doc를 historical trace로 강등

### Risk 2. Wrong stage placement

- `00_governance`로 올리면 문서 성격이 과도하게 커질 수 있다

대응:

- canonical home은 `20_pitch`

### Risk 3. Future system reality drift

- 나중에 `work_guard`가 preprocess 필수 artifact가 되면 문서 위치를 다시 고민할 수 있다

대응:

- 이번 웨이브는 `20_pitch` canon으로 두고, 필요시 `30_stage0_preprocess`에서 pointer만 추가

## 9. Recommendation

이번 execution plan의 권장안은 아래다.

1. `philosophy-to-work-guard-translation-map.md`를 `material_ssot/20_pitch/work-guard-translation-map.md`로 승격
2. `20_pitch/README.md`와 `pitch-philosophy.md`에서 canonical reference로 연결
3. dated doc는 historical trace로 남김
4. 시스템 계약 승격은 나중 wave로 미룸

즉, 사용자 질문에 대한 짧은 대답은:

- `응, material_ssot에 흡수하는 게 맞다`
- `위치는 20_pitch가 맞다`
- `이번엔 문서 authority 흡수까지만 하고, runtime 계약 승격은 다음 wave가 맞다`

## 10. Practical Next Action

이 plan 기준으로 다음 실제 실행 턴에서 할 일은 딱 3개다.

1. canonical file 생성
2. `20_pitch/README.md` 업데이트
3. `pitch-philosophy.md` 업데이트

이 3개만 하면 흡수 1차는 끝난다.

## 11. 3-Pass Audit

- Pass 1: placement 후보를 `20_pitch`와 `00_governance` 사이에서 다시 비교함
- Pass 2: 이번 웨이브의 non-goal을 분리해 문서 흡수와 시스템 계약 승격을 혼동하지 않게 정리함
- Pass 3: 실제 다음 실행 턴에서 바로 쓸 수 있게 3개 작업으로 압축함
- Confidence: 0.98
