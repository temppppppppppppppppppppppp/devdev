# WG-V2 Verdict: wuxia_heavenly_physician

- Date: 2026-04-06
- Terminal: 5
- Target work: wuxia_heavenly_physician (천의무쌍)
- Family: wuxguide / wuxia

## Authority Set Used

1. `material_ssot/20_pitch/canon/wuxia_heavenly_physician.md` — canonical pitch
2. `treatments/preprocess/wuxia_heavenly_physician/phase0_ready_snapshot.json` — phase0 authority substitute
3. `treatments/preprocess/wuxia_heavenly_physician/material_bundle_summary.json` — Stage0 bundle
4. `material_ssot/20_pitch/pitch-philosophy.md` — house philosophy
5. `material_ssot/20_pitch/protagonist-first-constitution.md` — protagonist-first law
6. `material_ssot/20_pitch/work-guard-translation-map.md` — translation map
7. `docs/wuxguide/SSOT_wuxguide-integrated-order.md` — wuxguide family SSOT

Note: live TR/BI는 consistency reference로만 사용. phase0_design.json은 disk에 부재하며 phase0_ready_snapshot이 authority 대체.

## Hard Gate

| Key | Present |
|-----|---------|
| `work_identity.one_line_truth` | YES |
| `work_identity.tracking_slots` | YES (4개) |
| `work_identity.mandatory_scene_engines` | YES (3개) |
| `work_identity.forbidden_flattenings` | YES (14개) |
| `work_identity.protagonist_weapon` | YES (3개) |

Hard gate: **PASS**

## WG-V2 Checklist

### 1. One-Line Truth — YES

`무공 자질 없는 명문 무가 막내가 침술=무공의 의무일체를 개척해, 치료할 수 있는 손의 희소가치로 가문·무림·독역의 관문을 동시에 장악한다`

- 주인공 장악 판타지가 바로 읽힌다: "치료할 수 있는 손의 희소가치로 관문을 장악"
- generic theme 아님 — 작품 고유의 의무일체 메커니즘이 명시

### 2. Protagonist-First Purity — YES

- 소백의 결핍(무공 자질 전무)은 과실이 아님 — 판의 불리함
- 의맥이라는 감춰진 자산이 있되 그것만으로 해결되지 않음 — 실행력 필요
- 회개물/자업자득 스타트 아님

### 3. Tracking Slots — YES

4개 슬롯 모두 서열/통제/재평가 축:
- `저평가→고평가 전환` — 재평가
- `가문 내 권한 회수` — 통제
- `경지 7단계 돌파` — wuxia 특화 서열 (realm progression)
- `독역 치료 독점 병목` — 소백 없이 못 움직이는 구조

generic `성장`/`성공`으로 흐르지 않았음.

### 4. Signature Scene Engine — YES

3개 엔진 모두 `저건 쟤라서 가능했다`를 증명하는 구조:
- 치료 4단계 구동 + 활침 고유 인과
- 의술 비무의 이중 레이어 (경혈+독/해독) — 일반 전투와 분리
- 치료 성공 직후 평가 수정 장면

첫 블록 3~6화 간판 장면(형 치료 → 공인 의원 자격 → 평가 수정)이 engine 1+3에 잡힘.

### 5. Protagonist Weapon — YES

- `의맥으로 독맥·경혈·독역 경로를 동시에 읽는 진단력` — 작품 고유, 소백만 가능
- `활침=살침 동일 기술 인과` — 200년 만의 유일한 계승자
- `치료 4단계를 전투에 전용` — 시스템 기반 재현 가능

generic competence 아님.

### 6. Reward Vector — YES

- 초반 보상: 조건부 공인 의원 자격(서열 변화), 약방·서고 접근권(통제), 보호 태도 변화(영수증)
- `admiration_axes`에 5축 명시: 선독, 비굴하지 않음, 유일성, 피해 통제, 결과 강제
- `observer_tiers`에 평가 수정 계층 순서 명시 (형→누나→스승→적대자→아버지→무림)
- 태도 변화가 영수증으로 찍히는 구조

### 7. Crisis Doctrine — YES

- `admiration_axes`에 "위기에서 최소 피해를 통제하며 반격 자산 확보" 명시
- `custom_rules`에 "반격 예약 없는 손해 금지" + "위기는 우선순위 선택권 증명으로 사용"
- `evaluation_thresholds`에 "큰 피해 뒤 즉시 새 경지 돌파 또는 다음 카드 확보"
- 소백은 진단력이라는 수단을 쥐고 위기에 들어감

### 8. Forbidden Flattenings Coverage — YES

14개 항목. 표준 치명 drift 7개 전부 포함 + wuxia/wuxguide 특화 7개 추가:
- 한 줄 기적치료 금지
- 경혈 임의 창작 금지
- 의술 비무 일반 전투 환원 금지
- 독역 메커니즘 편의 변경 금지
- 약재 추상화 금지
- business-power vocabulary 이식 금지
- 가문 갈등 치정극 변질 금지

### 9. Translation Discipline — YES

- upstream 철학 원문 장문 복붙 없음
- 모든 슬롯이 작품별 doctrine으로 압축
- 교육문이 아니라 runtime rule 형태

### 10. Work Specificity — YES

- 이 guard를 다른 wuxia 작품에 그대로 붙이면 의무일체·활침/살침·독역·경지 7단계·치료 4단계 등이 전부 어색
- 소재 설명이 아니라 소백의 장악 판타지가 앞섬

## Verdict Summary

| # | Item | Result |
|---|------|--------|
| 1 | One-Line Truth | YES |
| 2 | Protagonist-First Purity | YES |
| 3 | Tracking Slots | YES |
| 4 | Signature Scene Engine | YES |
| 5 | Protagonist Weapon | YES |
| 6 | Reward Vector | YES |
| 7 | Crisis Doctrine | YES |
| 8 | Forbidden Flattenings Coverage | YES |
| 9 | Translation Discipline | YES |
| 10 | Work Specificity | YES |

- NO: 0개
- WEAK: 0개
- 4번·5번·6번 모두 YES

## WG-V2 Result: **PASS**

## Weak Points

1. **phase0_design.json 부재**: authority가 phase0_ready_snapshot으로 대체됨. 실제 Phase0 블록 설계가 나오면 work_guard 재검증이 필요할 수 있음.
2. **경지 돌파 tracking이 wuxia 특화 서열이지만 blockguide 기준과 이질적**: wuxguide family니까 정상이지만, 다른 터미널의 blockguide 작품들과 교차 비교 시 감각 차이가 있을 수 있음.
3. **forbidden_flattenings 14개로 다른 작품 대비 많음**: wuxia 특화 domain guard가 필요해서 늘어난 것이므로 정당하나, 런타임 소비 시 축약 가능성 열어 둘 필요.

## Next Action

- 이 draft는 **freeze candidate**로 둔다
- runtime install은 이번 배치 scope 밖
- Phase0가 실제 생성되면 WG-V2 재검증 권장
- TR 생성 후에는 WG-V3 drift audit 수행
