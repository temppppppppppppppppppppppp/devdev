# Manual Audit Note (Draft): chaebol_ent_empire

- Date: 2026-04-06
- Terminal: 4
- Scope: preprocess 4-pack 수동 감리 초안 — Terminal 5의 phase0_ready_snapshot.manual_audit_pass 판정을 위한 사전 점검
- Authority: canon pitch + live TR/BI (consistency ref) + WG-V2 verdict + reward_crisis_doctrine_note.md

## 1. 감리 대상

Terminal 1~3이 생성할 preprocess 4-pack:

| 파일 | 담당 | 감리 초점 |
|------|------|----------|
| source_manifest.json | T1 | canonical source 등록, reference-only 구분, do_not_fake 포함 여부 |
| profile_lock.json | T2 | 5축(resource/power/control/payoff/failure)이 작품 truth를 반영하는지, 특히 reward가 권한 언어인지 |
| material_bundle_summary.json | T3 | 위기 후보가 선독/대비/최소 피해/즉시 보상 구조로 읽히는지 |
| phase0_ready_snapshot.json | T5 | 위 3개 종합 + manual_audit_pass 판정 |

## 2. 감리 체크리스트 초안

### 2.1 Source Authority 검증 (source_manifest.json)

- [ ] canonical_sources에 canon pitch가 1순위로 등록되어 있는가
- [ ] live TR/BI가 reference_only로 분류되어 있는가 (consistency ref, not truth)
- [ ] do_not_fake 항목이 canon pitch §4의 6개 항목을 포함하는가
- [ ] crisis_pool이 존재하며 canon pitch early_antagonist_shape에서 추출되었는가
- [ ] reward 관련 항목이 자산 언어(120억, 7억)만이 아니라 권한 언어(평가 수정, 접근권, 결정권, 자율권)를 포함하는가
- [ ] npc_pool에 최소 핵심 5인(권태하, 강이현, 윤서아, 서민재, 한도윤, 권도현)이 등록되어 있는가

### 2.2 Profile Lock 검증 (profile_lock.json)

- [ ] primary_profile = entertainment_media_profile인가
- [ ] secondary_profile = business_growth_profile인가
- [ ] resource_axis가 인재 포트폴리오/현금흐름/IP 자산/사업 라인을 포함하는가
- [ ] power_axis가 스타 감지 + 배치 능력을 핵심으로 잡는가
- [ ] control_axis가 캐스팅 결정권/배치권/패키지 설계권/자율권/표준 선점을 포함하는가
- [ ] payoff_axis가 **돈이 아니라** 평가 수정/접근권/결정권/자율권 언어를 우선하는가
- [ ] failure_axis가 "감각이 허풍으로 확정됨 + 청산 + 낙하산 고정"을 포함하는가
- [ ] reward vector가 120억+7억 자산 증가에 갇히지 않고 4가지 권한 조각으로 번역되어 있는가

### 2.3 Material Bundle 검증 (material_bundle_summary.json)

- [ ] events가 canon pitch의 opening spike, proof scene, Block 1~2 주요 이벤트를 포함하는가
- [ ] npc_candidates가 canon pitch + live TR에서 추출되었으며 상상 인물이 없는가
- [ ] crisis_candidates가 선독/대비/최소 피해/즉시 보상 4단계로 읽히는 구조를 갖추는가
- [ ] terms가 mandatory_lexicon(배치/부킹/계약/캐스팅/패키지/접점/라이선싱/기업가치/표준)을 반영하는가
- [ ] 위기 후보가 "위기를 그냥 당하고 버티기" 패턴이 아니라 "빈 무대를 읽고 배치 카드로 증명하는" 패턴인가
- [ ] 비대칭 무대(VIP 행사, 비공개 쇼케이스, 비방송 플랫폼)가 증명 전장으로 등록되어 있는가

### 2.4 Cross-File 정합성

- [ ] source_manifest의 canonical source 목록과 profile_lock의 authority가 일치하는가
- [ ] profile_lock의 5축이 material_bundle_summary의 재료와 모순 없이 매핑되는가
- [ ] 세 파일 모두에서 "권태하는 회귀자가 아니다"가 위배되지 않는가
- [ ] 세 파일 모두에서 "강점은 발굴이 아니라 배치"가 위배되지 않는가
- [ ] 새로운 인물/사업축/위기축이 상상으로 추가되지 않았는가

## 3. 약점 예측 (사전 경고)

Terminal 5가 manual_audit_pass를 판정할 때 주의할 잠재 약점:

### 3.1 Reward Vector 잔존 약점 가능성

- profile_lock의 payoff_axis가 여전히 자산 언어(매출, 기업가치)에 비중을 두면 WG-V2 6번이 다시 WEAK으로 갈 수 있다
- 확인 기준: payoff_axis의 첫 번째 항목이 "돈"이 아니라 "평가 수정" 또는 "접근권"인지

### 3.2 Crisis Doctrine 번역 깊이

- material_bundle_summary의 crisis_candidates가 적대자 이름만 나열하고 4단계(선독/대비/최소 피해/즉시 보상) 구조가 안 보이면 WG-V2 7번이 다시 WEAK
- 확인 기준: crisis_candidates 각 항목에 태하가 "무엇을 먼저 읽었는지"와 "무엇을 쥐고 들어갔는지"가 명시되어 있는지

### 3.3 상상 보강 오염

- preprocess 생성 중 canon pitch에 없는 인물(새 PD, 새 경쟁자 등)이나 새 사업축이 슬며시 추가될 수 있다
- 확인 기준: 모든 인물/사업축/위기축이 canon pitch 또는 live TR/BI에 이미 존재하는지 역추적 가능한지

## 4. Manual Audit Pass 조건 (Terminal 5 참고용)

Terminal 5가 `manual_audit_pass = true`를 찍으려면 아래가 모두 충족되어야 한다:

1. §2.1~2.4 체크리스트 전항 통과
2. §3.1~3.3 약점 예측 항목에서 실제 약점이 발견되지 않음
3. reward vector가 4가지 권한 조각(평가 수정/접근권/결정권/자율권 씨앗)을 포함
4. crisis doctrine이 선독/대비/최소 피해/즉시 보상 4단계로 읽힘
5. 상상 보강 없음 확인 (모든 truth가 canon pitch 또는 live consistency ref로 역추적 가능)

위 중 하나라도 미달이면 `manual_audit_pass = false`이고, Terminal 5는 HOLD 유지로 종료한다.

## 5. Evidence Source Map

| 감리 근거 | 출처 |
|----------|------|
| 6번/7번 WEAK 원인 | WG-V2 verdict + authority note |
| reward 권한 언어 번역 | reward_crisis_doctrine_note.md §2 |
| crisis doctrine 4단계 | reward_crisis_doctrine_note.md §3 |
| do_not_fake 6항목 | canon pitch §4 Phase0 Handoff Note |
| 핵심 NPC 목록 | canon pitch §3 + live TR Block 1~2 |
| mandatory_lexicon | work_guard.yaml > mandatory_lexicon |
| 회귀자 아님 불변식 | canon pitch §2 contamination_guard + work_guard custom_rules |
