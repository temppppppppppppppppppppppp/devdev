# Wuxia Treatment 블록 생산 하네스 (통합 실전판)

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-24
> 근거: `treatment-production-harness-v2.md` (blockguide 골든 스탠다드) + wuxia 기획안 전수 분석
> 목적: **모든 지능 수준의 모델이 무협/선협/세가물/문파물 Treatment JSON을 생산**할 수 있는 완전한 하네스
> 출력: `treatments/{work_id}_tr_block_070_draft.json`
> 선행 문서: `SSOT_wuxguide-integrated-order.md`
>
> 위임/외부 모델 시작 규칙:
>
> - 먼저 `docs/wuxguide/delegation-bootstrap.md`를 읽는다.
> - work-level current-truth doc가 있으면 handoff note보다 우선한다.
> - `tr_block_070_draft`라는 이름은 저장 컨테이너 이름이지 saved boundary 보장이 아니다.
>
> **즉시 정지 표지판**
>
> - `treatments/{work_id}_tr_block_070_draft.json`는 **최종 누적 저장 컨테이너 이름**이다.
> - 이 파일명은 `70블록을 한 번에 생성하라`는 뜻이 아니다.
> - 실제 생산 단위는 항상 **Block 1개**다.
> - 같은 운영 오더에서 자동 연속 가능한 최대치는 **5블록**이다.
> - 블록 완료 시마다 즉시 merge/save 하고, `Block 5`에서 반드시 정지한다.
> - `Block / ARC / Phase / Stage` 번호 메타는 자연어 필드에서 전면 금지한다.
> - `foreshadow` / `callback`도 자연어 의미만 적고, 구조 타깃은 `foreshadow_targets` / `callback_sources`에만 둔다.
> - `section_rotation`, `arc_section`, `phase` 같은 라벨은 번호 없는 자연어 제목만 허용한다.

---

## 0A. SSOT 장르 선언 — Wuxia All-Genre General Mode

이 문서는 `wuxguide` 패밀리 전체를 아우르는 **무협 all-genre general mode** 하네스다.

현재 메인 시스템 일부 런타임과 코드 경로는 `blockguide`의 `FinanceHUD`와 `capital_*` 필드명을 사용한다.
그러나 이 문서의 SSOT 의미는 `MartialHUD` 기반의 **무협 세계관 성장물 전체**다.

이 문서가 포괄하는 서브장르:

| 서브장르 프로파일 | 핵심 성장 축 | 대표 작품 유형 |
| ---- | ---- | ---- |
| `orthodox_wuxia_profile` (정통무협) | 경지 상승, 비급 획득, 강호 명성 | 무당검협, 화산질풍검, 정통 강호물 |
| `xianxia_profile` (선협) | 경지 돌파, 영약/영물 획득, 천겁 | 선천경 돌파물, 수선물, 영단물 |
| `sega_profile` (세가물) | 가문 지위, 가주 승계, 가문 무공 | 진가장, 하가장, 명문세가 성장기 |
| `munpa_profile` (문파물) | 문파 등급, 제자 육성, 문파 재건 | 삼류문파 장문인, 소림 입문기, 문파 중흥기 |
| `rebirth_wuxia_profile` (환생/회귀물) | 전생 기억 활용, 경지 재돌파, 인과 회수 | 무림 회귀, 전생 검성, 환생 의선 |
| `merchant_wuxia_profile` (상업무협) | 상단 규모, 거래 영향력, 무림 경제 장악 | 상단 막내딸, 무림 재벌, 표국 운영기 |
| `medical_wuxia_profile` (의술무협) | 의술 경지, 치료 범위, 의명(醫名) | 침의무쌍, 독의, 의선 성장기 | <!-- utf8-hygiene: allow-line rationale: intentional Hangul+CJK term for wuxia naming. -->
| `training_wuxia_profile` (육성무협) | 교육 경지, 제자 경지, 문파 위상 | 스승 시점물, 제자 군단, 교육 먼치킨 |

핵심 해석:

- `realm` = 주인공의 무공/능력 경지 단계 (삼류 → 무신, 침의 → 천의, 산원 → 천하상주 등)
- `internal_energy` = 내공량 또는 핵심 역량 수치 (갑자, 냥, 교육 경지 수치 등)
- `martial_arts` = 획득/수련한 무공/기술 목록
- `faction` = 소속 문파/세가/상단/세력
- `jianghu_reputation` = 강호/무림 내 명성과 위상

서브장르마다 `realm`과 `internal_energy`의 구체 단위가 다르지만, MartialHUD 필드명은 동일하게 유지한다.

---

## 0B. 공통 코어와 프로파일 분리 — MartialHUD 호환 필드 재해석

### MartialHUD 기본 필드

| blockguide 필드 | MartialHUD 필드 | 무협 SSOT 의미 |
| ---- | ---- | ---- |
| `capital_before` | `realm_before` | 블록 시작 시점의 경지/역량 수준 |
| `capital_after` | `realm_after` | 블록 종료 시점의 경지/역량 수준 |
| `capital_delta` | `power_delta` | 경지/내공/역량의 변동량 |
| `deal_type` | `action_type` | 결정적 진행 액션 (비무, 비급 습득, 문파 교섭, 전투, 치료 등) |
| `business_sector` | `martial_domain` | 활동 무림 영역 (정파, 사파, 마교, 관부, 강호 등) |
| `company_state` | `faction_state` | 소속 세력의 현재 상태 |
| `business_lines` | `active_domains` | 현재 활성 활동 영역 (수련, 전투, 상업, 의술, 교육 등) |
| `leverage_used` | `leverage_used` | 이번 블록에서 동원한 자원/인맥/무공 |
| `opponent` | `opponent` | 적대자 정보 (이름, 소속, 약점) |
| `success_pattern` | `success_pattern` | 결과 패턴 (승리/패배/피로스/부분성공) |
| `method` | `strategy` | 전략/전술 서술 |

### 서브장르별 `realm` 예시

| 서브장르 | realm 체계 |
| ---- | ---- |
| 정통무협 | 삼류 → 이류 → 일류 → 절정 → 초절정 → 화경 → 현경 → 무신 |
| 선협 | 연기 → 축기 → 금단 → 원영 → 화신 → 대승 → 도조 → 천선 |
| 의술무협 | 침의 → 혈의 → 맥의 → 신의 → 의성 → 의신 → 천의 |
| 상업무협 | 산원 → 장방 → 대관 → 재신 → 상성 → 상도 → 천하상주 |
| 육성무협 | 사범 → 명사 → 현사 → 대종사 → 사성 → 사신 → 만류귀종 |

각 작품의 Phase 0에서 구체적 realm 체계를 확정하고, 이후 TR 블록은 해당 체계를 일관되게 따른다.

---

## 0C. 자기이익 우선 원칙 (무협 적용)

### 원칙 선언

> **주인공은 매 블록에서 자기 이익(경지 상승, 비급 획득, 세력 확장, 원수 제거, 인맥 확보, 생존)을 위해 행동해야 한다.**
> **대의명분만으로 움직이면 REJECT.**

무협물에서 자기이익이란 돈이 아니다. 무공 성장, 문파 강화, 복수, 명성, 생존 — 이것이 무협 주인공의 자기이익이다.

### 좋은 예시

```
Block 15: 사파 독문의 약초 독점을 깨기 위해 위험을 무릅쓰고 독초 산지에 잠입한다.
→ 자기이익: 약재 확보로 내공 수련 가속 + 독문과의 거래에서 우위 확보 + 정파 내 명성 상승
→ 부수 효과로 주변 문파도 약재를 구할 수 있게 됨
```

```
Block 28: 마교 성녀의 치료 요청을 수락한다.
→ 자기이익: 마교의 비전 약재 3종을 대가로 확보 + 마교 내부 정보 획득 + 의술 경지 돌파의 계기
→ "불쌍해서 치료해줌"이 아니라 "치료 대가가 내 성장에 필수적"
```

```
Block 42: 천류문 장문인 풍천류와 비무에 응한다.
→ 자기이익: 승리 시 무림맹 일류 승격 심사에서 우위 + 패배해도 자신의 약점 파악 기회
→ 의리나 명예만으로 싸우는 것이 아니라 승격이라는 구체적 이익이 걸려 있음
```

### 나쁜 예시

```
Block 15: "무림의 평화를 위해" 독문에 맞선다.
→ REJECT: 주인공에게 돌아오는 구체적 이익이 없다. 평화는 결과이지 동기가 아니다.
```

```
Block 28: "아픈 사람을 그냥 지나칠 수 없어서" 마교 성녀를 치료한다.
→ REJECT: 무조건적 선행. 대가 없는 치료는 주인공의 성장에 기여하지 않는다.
```

```
Block 42: "스승의 가르침을 세상에 알리기 위해" 비무에 나선다.
→ REJECT: 추상적 대의명분. 비무의 구체적 보상(승격, 명성, 자원)이 명시되지 않았다.
```

### 자기이익 유효 범주 (무협)

| 범주 | 예시 |
| ---- | ---- |
| 경지 상승 | 돌파, 깨달음, 내공 증가, 경지 안정 |
| 비급/보물 획득 | 무공 비급, 영약, 신병이기, 비전 의서 |
| 세력 확장 | 문파 등급 상승, 영역 확대, 제자 확보, 동맹 맺기 |
| 원수 제거 | 복수 진전, 적대 세력 약화, 위협 제거 |
| 인맥 확보 | 고수와의 교분, 정보원 확보, 후원자 획득 |
| 생존 확보 | 부상 회복, 독 해독, 추적 회피, 은신처 확보 |
| 명성/위상 | 강호 명성 상승, 무림맹 인정, 구파 인정 |

---

## 0C-1. 블록별 사이다 계약 (생산 단계 필수)

무협도 예외가 아니다. 이 문서는 이제 **각 블록이 같은 블록 안에서 체감 가능한 사이다 영수증을 지급해야 한다**는 전제로 읽는다.

- 모든 블록은 `martial_ext.block_cider`를 포함해야 한다.
- 현재 운용 JSON이 `genre_ext`를 쓰면 `genre_ext.block_cider`로 같은 계약을 기록해도 된다.
- `has_cider=true`가 아니면 그 블록은 생산 실패다.
- `receipt_type`과 `receipt_line`에는 "이번 블록 안에서 이미 지급된 영수증"을 적어야 한다.
- 무협 영수증은 `재평가`, `입문/승급`, `비급/영약/토큰 확보`, `문파 내 발언권`,
  `보호 세력 확보`, `복수 카드 개봉`, `다음 비무/심사/입장권`처럼
  독자가 셀 수 있는 same-block 결과여야 한다.
- `수련 block`, `회복 block`, `정치 block`, `잠복 block`도 예외가 아니다.
  조용할 수는 있지만 반드시 `quiet but paid`여야 한다.
- `실패/굴욕/부상/대기만 남기고 닫힘`은 `pain_only_exit=true`로 보고 즉시 재생성한다.

---

## 0D. 절대 금지 규칙

```
## 절대 금지 — 이 규칙을 어기면 전량 재생성

=== 무협 핵심 금지 (MartialHUD 정합성) ===
1. 경지 역행 금지: realm_after < realm_before는 부상/봉인/독 중독/경맥 손상 외에 금지.
   역행 시 반드시 서사적 근거(부상, 사공 폭주, 경맥 파열 등)를 content에 명시해야 한다.
2. 내공 인과 없는 돌파 금지: 경지 상승에는 반드시 선행 조건(수련, 비급 습득, 실전 깨달음,
   영약 복용 등)이 content.solution 또는 content.context에 서술되어야 한다.
3. 죽은 NPC 행동 금지: 사망 처리된 NPC가 이후 블록에서 행동하면 REJECT.
   부활/환생/가사(假死)는 반드시 foreshadow에서 사전 심기가 있어야 한다. <!-- utf8-hygiene: allow-line rationale: intentional Hangul+CJK term for wuxia naming. -->
4. 3블록 연속 동일 경지 금지: realm_before = realm_after가 3블록 연속이면 REJECT.
   경지 변화가 없더라도 내공량 변동, 무공 습득, 깨달음 중 최소 1개가 있어야 한다.
5. 무공 무근거 사용 금지: martial_arts_acquired에 없고 이전 블록에서도 습득하지 않은
   무공을 갑자기 사용하면 REJECT.
6. 내공량 연속성 위반 금지: internal_energy_before ≠ 직전 블록의 internal_energy_after면 REJECT.
   부상/회복/돌파에 의한 변동은 반드시 content에 근거가 있어야 한다.

=== 서사 반복 금지 (Pattern 차단) ===
7. emotional_beat.type 2블록 연속 동일 금지
8. emotional_beat.intensity 3블록 연속 동일 값 금지
9. action_type 동일 값 3블록 이내 재등장 금지
10. location 동일 장소 3블록 이내 재등장 금지
11. success_pattern 동일 표현 3회 이상 반복 금지
12. opponent.weakness_exploited 동일 표현 3회 이상 금지
13. 성장률(내공 변동폭) 3블록 이상 동일 값 금지 (±5% 이상 변동 필수)
14. duration 전량 동일 값 금지 (블록별 서사 규모에 맞게 1일~6개월)

=== 언어/형식 금지 ===
15. 영어 문장 금지: relationship_delta, foreshadow, callback, reward, stakes는
    반드시 한국어로 작성. 영어 1문장이라도 있으면 재작성.
16. 코드 식별자 금지: strategy, success_pattern, weakness_exploited에
    "type_1", "plan_01" 같은 코드/번호 접미사 금지. 서사적 한국어 문장으로 서술.
    - 금지: "realm_breakthrough_type_1"
    - 허용: "독맥 경색을 침술로 뚫어 화경 돌파의 실마리를 잡다"
17. 문장 템플릿 재사용 금지: solution/context/event_villain/stakes에서
    "적대자명만 교체"한 동일 구조 문장을 2회 이상 사용하면 재작성.

=== NPC/관계 금지 ===
18. relationship_delta.before가 직전 블록의 after와 다르면 금지
19. callback이 "직전 블록의 X 성과가..." 패턴 2회 이상 금지
20. 페이즈 내 NPC 변화 의무: 동일 NPC가 5블록 이상 등장하면,
    before≠after인 블록이 최소 3개 있어야 한다.
21. relationship_delta.after 복제 금지: 동일 문장이 다른 블록/다른 NPC에 3회 이상 반복이면 재작성.

=== 복선/밀도 금지 ===
22. 메타 번호 본문 노출 금지: TR 블록의 **모든 자연어 텍스트 필드**에 `B숫자`, `Block 숫자`, `블록 숫자`, `ARC-숫자`, `Phase 숫자`, `Stage 숫자` 패턴 금지.
    대상: content.*, stakes, power_shift.*, relationship_delta[].before/after, foreshadow, callback, martial_ext.strategy/success_pattern.
    복선/회수 구조 타깃은 `foreshadow_targets` / `callback_sources`에만 기입한다.
    `section_rotation`/`arc_section`/`phase`는 번호 없는 자연어 라벨만 허용한다.
    이유: TR의 모든 텍스트가 downstream 원고 생성에 흐르므로 메타 번호의 작중 오염을 방지.

    ### 22A. Plan-level 참조 허용 예외 (ratified 2026-04-09, superseded by material-side §4.3.1 on same date)

    **Authority note**: 본 Rule 22A는 `material_ssot/00_governance/production-pair-schema-standard-v1.md §4.3.1 Structured Ref Convention Alias`의 **family-specific 구현 노트**다. 최종 권한은 material-side §4.3.1이며, wuxguide 하네스의 본 항목은 wuxia family TR 생성 시 그 규칙을 어떻게 적용하는지 적는 참조용이다. 충돌 시 material-side §4.3.1이 승리한다.

    TR이 `foreshadow_targets` / `callback_sources` 구조 필드를 사용하지 않고 `foreshadow: [{ref: int, event: str}, ...]` / `callback: [{ref: int, event: str}, ...]` convention을 채택한 작품에 한해, 아래 조건을 모두 충족하면 자연어 필드의 `B숫자` / `ARC-숫자` inline 참조를 **TR-내부 plan-level 참조**로 허용한다.

    **허용 조건**:
    - `foreshadow[].ref` / `callback[].ref`가 정수 구조 필드로 분리돼 있을 것 (번호 구조는 ref에 고정)
    - inline 참조는 plan-level 서사 연결 신호이며, downstream 원고 생성기(episode writer / scene builder)가 scene 레벨에서 해석·제거하는 책임을 진다
    - 특정 작품 TR 내부에서 이 convention이 일관되게 사용되고 있을 것 (work_id별 all-or-nothing)
    - `.` 같은 작중 대사/서술 filed가 아니라 plan 텍스트 필드(`content.context/event_villain/solution/reward`, `stakes`, `power_shift.*`, `strategy`, `success_pattern`, `relationship_delta[].before/after`, `foreshadow.event`, `callback.event`)에 한함

    **여전히 금지**:
    - 최종 원고(`manuscript` / `episode` 산출물)의 작중 대사·서술
    - `foreshadow_targets` / `callback_sources` 구조 필드가 이미 사용된 TR — 그 경우에는 Rule 22 원문을 그대로 적용
    - 하이브리드(일부 블록만 ref convention, 일부는 inline)도 금지 — 작품 단위로 일관되어야 함

    **Precedent**:
    - `manual_meridian_archivist` (wuxguide): ARC-03/04 §5.3 감리가 이 pattern을 암묵 승인, 2026-04-09 B46·B47 3-pass 감리(`docs/2026-04-09/manual_meridian_archivist_b46_b47_3pass_audit.md`)에서 systemic finding으로 정면 적발 → 본 예외로 공식 수용

    **운영 규칙**:
    - 신규 작품 TR 생성 시 기본값은 Rule 22 원문 (구조 필드 사용)
    - 기존 작품이 이미 inline convention을 채택한 경우에만 22A 예외 적용
    - 22A 예외 적용 작품은 `live_status.md §Delegation Rule` 또는 해당 work의 canonical SSOT에 "Rule 22A 예외 적용"을 명시해야 함
    - 감리 보고서의 `meta_number_leak_blocks` 수치는 계속 기록하되, 22A 예외 작품에서는 P1 FAIL이 아닌 **INFO-level 관찰 항목**으로 분류
23. 복선 실제 회수 의무: foreshadow에서 ref로 지목한 블록의 callback에 명시적으로 회수 문장 포함 필수.
24. reward 재진술 금지: context를 시제만 바꿔 반복하면 무효.
    reward에는 반드시 "새로 생긴 결과/손실/경지 변화"가 1개 이상 포함.
24A. 블록별 same-block 사이다 의무:
    - 모든 블록은 `martial_ext.block_cider`를 포함해야 한다.
      현재 JSON 운용이 `genre_ext`를 쓰면 `genre_ext.block_cider`로 같은 정보를 적는다.
    - `has_cider=true`가 아니면 무효.
    - `receipt_type`과 `receipt_line`에는 "이번 블록 안에서 이미 지급된 영수증"을 적어야 한다.
    - `수련/회복/정치/잠복` 블록도 예외가 아니다. 반드시 `quiet but paid`여야 한다.
    - `pain_only_exit=true` 또는 패배/부상/지연만 남기고 닫히는 블록은 즉시 재생성.
25. 대단원 슬롯 반복 금지: 10블록 패턴을 다음 대단원에서 같은 순서로 재사용하면 무효.
26. skeleton draft 금지: Phase 0의 block slot 문장을 context/reward에 얕게 풀어쓴 수준이면 무효.
    블록마다 최소 1개의 "구체 장면", 1개의 "구체 경지/세력/관계 변화"가 새로 생겨야 한다.
27. 핵심 서술 번들 저밀도 금지:
    - context + event_villain + solution + reward + stakes 평균(avg_bundle_chars)이 350자 미만이면
      해당 draft를 skeleton draft로 분류한다.
    - 300자 미만 블록이 1개라도 있으면 P0 재생성.
28. leverage_used 고정 금지: 동일 4항목 세트 3회 이상 반복 금지.
    블록별 최소 2항목은 고유해야 한다.
29. 장소 순환 주기 최소 10블록: 동일 장소가 10블록 이내에 재등장하면 위반.
    (무협은 이동이 잦으므로 blockguide의 15블록보다 완화하되 10블록은 유지)
30. opponent 다양성 부족 금지:
    - 70블록 전체 opponent_unique 6명 미만이면 FAIL.
    - 단일 opponent 점유율 30% 초과면 FAIL.
    - 연속된 2개 이상의 10블록 구간이 동일 2인 opponent 로테이션이면 FAIL.
31. 복선 회수율 저하 금지:
    - callback_ratio = callback_total / foreshadow_total이 0.65 미만이면 FAIL.
32. 후반 상대 공백 금지:
    - 마지막 10블록에서 opponent가 비어 있거나 "없음"이면 1블록까지 허용, 그 이상이면 FAIL.
33. 무협 고유 — 무공 체계 일관성: 작품 내에서 경지 체계 명칭이 블록 간에 불일치하면 REJECT.
    (예: 초반 블록에서 "화경"이라 쓰고 이후 같은 경지를 "통현경"으로 부르면 위반)
34. 무협 고유 — 부상 연속성: injury_status에 기록된 부상이 치료/회복 서사 없이 사라지면 REJECT.
```

---

## 0E. MartialHUD 계약 — 블록마다 추적 필드

### 필수 추적 필드 (`martial_ext`)

모든 wuxia TR 블록은 `genre_ext` 대신 (또는 추가로) `martial_ext` 객체를 포함해야 한다.

```json
{
  "martial_ext": {
    "realm_before": "일류 중기",
    "realm_after": "일류 후기",
    "internal_energy_before": "18갑자",
    "internal_energy_after": "22갑자",
    "martial_arts_acquired": ["청풍검법 제4초식 '풍월무한'"],
    "martial_arts_used": ["청풍검법 제1~3초식", "기본 경공"],
    "injury_status": {
      "current": "좌측 경맥 미세 손상 (Block 12 전투 후유증)",
      "change": "자연 회복 중, 전투 가능하나 내공 운용 80% 수준"
    },
    "faction_status": {
      "affiliation": "청풍문",
      "rank": "장문인",
      "change": "무림맹 이류 문파 심사 통과 → 이류 승격"
    },
    "kill_count": 0,
    "spare_count": 1,
    "jianghu_reputation": {
      "before": "지역 소문파 장문인",
      "after": "이류 문파 장문인, 정파 내 호평 시작"
    },
    "action_type": "문파 비무 + 무림맹 심사",
    "opponent": {
      "name": "천류문 장문인 풍천류",
      "sect_or_faction": "천류문 (이류 문파)",
      "weakness_exploited": "풍천류의 검법이 상단공격에 치우쳐 하단 방어에 빈틈이 있음을 간파"
    },
    "strategy": "비무 전반부에 수세로 상대 패턴을 읽고, 후반부에 청풍검법 신초식으로 허를 찌름",
    "success_pattern": "비무 승리, 그러나 좌측 경맥 손상 악화",
    "block_cider": {
      "has_cider": true,
      "receipt_type": "문파 승급 + 재평가",
      "receipt_line": "이류 문파 승격과 함께 정파 내 호평이 시작되어, 한서진은 같은 블록 안에서 장문인 위상 상승 영수증을 받는다.",
      "pain_only_exit": false
    },
    "leverage_used": ["청풍검법 신초식", "감재안으로 상대 약점 간파", "제자 진무혁의 사전 정보"],
    "martial_domain": "정파 무림",
    "active_domains": ["비무", "문파 운영", "제자 교육"]
  }
}
```

### 필드 정의

| 필드 | 타입 | 의무 | 설명 |
| ---- | ---- | ---- | ---- |
| `realm_before` | string | 필수 | 블록 시작 시 주인공의 경지. 직전 블록의 `realm_after`와 동일해야 함 |
| `realm_after` | string | 필수 | 블록 종료 시 주인공의 경지. 역행 시 반드시 서사 근거 필요 |
| `internal_energy_before` | string | 필수 | 블록 시작 시 내공량/역량 수치. 직전 블록의 `internal_energy_after`와 동일해야 함 |
| `internal_energy_after` | string | 필수 | 블록 종료 시 내공량/역량 수치 |
| `martial_arts_acquired` | list[string] | 필수 | 이번 블록에서 새로 획득/습득한 무공. 없으면 빈 배열 |
| `martial_arts_used` | list[string] | 권장 | 이번 블록에서 사용한 무공 목록 |
| `injury_status` | object | 필수 | 현재 부상 상태와 변동. 부상 없으면 `{"current": "정상", "change": "변동 없음"}` |
| `faction_status` | object | 필수 | 소속 세력 정보와 변동 |
| `kill_count` | int | 필수 | 이번 블록에서 처치한 적 수 |
| `spare_count` | int | 필수 | 이번 블록에서 살려준 적 수 |
| `jianghu_reputation` | object | 필수 | 강호 명성 변동 |
| `action_type` | string | 필수 | 결정적 진행 액션 (blockguide의 deal_type에 해당) |
| `opponent` | object | 필수 | 적대자 정보. 적대자 없는 수련 블록이면 `{"name": "없음(수련 블록)"}` |
| `strategy` | string | 필수 | 이번 블록의 전략/전술 (blockguide의 method에 해당) |
| `success_pattern` | string | 필수 | 결과 패턴 |
| `block_cider` | object | 필수 | 이번 블록의 same-block 사이다 영수증. `has_cider=true`, `receipt_type`, `receipt_line`, `pain_only_exit=false`를 기본으로 기록 |
| `leverage_used` | list[string] | 필수 | 동원한 자원/인맥/무공 |
| `martial_domain` | string | 필수 | 활동 영역 (정파/사파/마교/관부/강호/상단) |
| `active_domains` | list[string] | 권장 | 현재 활성 활동 영역 |

### MartialHUD 연속성 제약

1. `realm_before(N)` = `realm_after(N-1)` — 위반 시 P0
2. `internal_energy_before(N)` = `internal_energy_after(N-1)` — 위반 시 P0
3. `injury_status`의 부상이 치료/회복 없이 사라지면 P0
4. `martial_arts_used`에 있는 무공이 이전 블록들의 `martial_arts_acquired` 누적에 없으면 P1
5. `faction_status.affiliation`이 변경될 때는 content에 서사 근거 필수

---

## 1. 블록 생산 단위

### 1.1 기본 원칙

이 하네스의 생산 단위는 항상 **블록 1개**다.

- `auto-run`은 블록을 순서대로 이어서 쌓는다는 뜻이다.
- 같은 운영 오더에서 자동 연속 가능한 최대치는 **5블록**이다.
- `Block 005`, `010`, `015` ... 경계에 도달하면 새 오더 전까지 반드시 멈춘다.
- 10블록은 대단원 구조/감리 창(window)일 뿐, 출력 단위가 아니다.
- 70블록 일괄 생성이나 10블록 일괄 생성은 금지한다.

### 1.2 생산 전 확인

1. `SSOT_wuxguide-integrated-order.md`를 **UTF-8로 먼저 읽는다.**
2. `wuxia-planning-harness.md`를 다시 확인해 지금이 기획 단계인지 생산 단계인지 판단한다.
3. 이 문서를 **UTF-8로 다시 읽는다.**
4. `treatments/phase0/{work_id}_phase0_design.json`과 직전 `candidate/fixed/draft`를 재오픈한다.
5. `Phase 0`가 없으면 이 문서를 실행하지 말고 planning 단계로 되돌린다.

### 1.3 블록 1개 생산 사이클

```
1. 사전 선언 (§1.5)
2. 블록 1개 JSON 생성
3. 절대 금지 규칙 자가 점검 (§0D)
4. Python 교정/검증 (§3)
5. 수동 감리 메모 작성
6. 위반 시 같은 블록만 재생성
7. 통과 시 다음 블록으로 이동
```

### 1.4 대화형 순차 진행 프로토콜

실전에서는 사용자가 `다음 스텝`만 반복하는 경우가 많다.
이 하네스는 그 상황을 **정상 경로**로 간주한다.

| 사용자 입력 | 기본 행동 | 산출물 |
| ----------- | --------- | ------ |
| `다음 스텝` (기획 직후) | Phase 0 JSON 작성 | Phase 0 설계 시트 |
| `다음 스텝` (생산 시작) | Block 1 생성 | 블록 candidate |
| `다음 스텝` (블록 완료 후) | 다음 블록 1개 생성 | 다음 candidate |
| `다음 스텝` (70 완료 후) | 전량 merge/최종 draft 정리 | `tr_block_070_draft.json` |
| `다음 스텝` (draft 확정 후) | BI 하네스로 handoff | `0_bi_{work_id}.json` |

- `알아서 계속`도 이 표를 무제한 확장하는 뜻이 아니다. 같은 운영 오더에서는 최대 5블록까지만 연속 진행한다.

### 1.4A TR auto-run window (5-block cap)

이 절은 **TR production 오더에만** 적용한다.
Planning, BI handoff, 감리 단계에는 그대로 확장하지 않는다.

규칙:

1. 내부 실행 단위는 항상 `Block 1개`다.
2. 사용자가 `알아서 계속`, `정지 게이트 전까지 계속`처럼 연속 진행을 허용해도, 같은 운영 오더에서 자동 연속 가능한 최대치는 **5블록**이다.
3. `Block 005`, `010`, `015` ... 처럼 5의 배수 경계에 도달하면 품질 이상이 없어도 반드시 멈추고 새 오더/재정렬을 기다린다.
4. P0, UTF-8, 수동 감리, continuity, compaction 경고가 먼저 오면 5블록 이전에도 즉시 멈춘다.
5. BI handoff는 별도 단계다. TR의 5블록 cap을 BI 감리 생략 허가로 해석하지 않는다.

### 1.5 사전 선언 프로토콜 (블록마다 JSON 앞에 필수)

```
각 블록마다 JSON 출력 직전에 아래 8개 항목을 자연어로 서술하라.
사전 선언 없이 JSON을 출력하면 무효 처리된다.

1. **이전 블록 잔향**: 직전 블록에서 무슨 일이 일어났는가?
   주인공의 감정 상태, 경지, 내공, 부상 상태는?
2. **이번 블록의 고유 사건**: 이전/이후 블록에서 절대 반복되지 않는
   고유 이벤트를 1문장으로 서술하라.
3. **차별화 증명**: 직전 블록과 아래 5필드가 어떻게 다른지 명시:
   - emotional_beat.type: [직전] → [이번]
   - action_type: [직전] → [이번]
   - opponent 또는 weakness: [직전] → [이번]
   - location: [직전] → [이번]
   - duration: [직전] → [이번]
   5개 중 3개 이상이 직전과 동일하면 해당 블록을 다시 구상하라.
4. **경지/내공 계산 과정**: realm_before = [직전 realm_after].
   internal_energy_before = [직전 internal_energy_after].
   변동 근거 = [서사적 근거].
5. **NPC 관계 이월**: 각 NPC의 before를 직전 블록 after에서 복사.
   새 NPC면 "신규" 명시.
6. **약점 차별화 증명**: 이번 블록의 weakness_exploited가 직전 3블록의 약점과
   어떤 차원에서 다른지 1문장으로 서술하라.
7. **부상/무공 연속성 확인**: 직전 블록에서 부상이 있었으면 이번 블록에서의 상태를
   명시. 새로 사용하는 무공이 이전에 습득한 것인지 확인.
8. **패턴 피드백 재확인**: 이번 블록이 금지 패턴 목록과 겹치지 않는다고 1문장으로 명시.
```

### 1.6 차이 행렬 (블록 완료 후 필수 출력)

```
| Block | beat_type | intensity | tension | action_type | opponent | location | duration | realm_delta | 내공변동 | success |
|-------|-----------|-----------|---------|-------------|----------|----------|----------|-------------|---------|---------|

### 자가 검증 (행렬 출력 후 수행)
1. beat_type 열에 2연속 동일 값? → 수정
2. intensity 열에 3연속 동일 값? → 수정
3. action_type 열에 3블록 이내 동일 값? → 수정
4. opponent 열이 전부 동일? → 최소 2개 분화
5. location 열에 3블록 이내 동일 값? → 수정
6. duration 열이 전부 동일? → 최소 3종 분화
7. realm_delta가 3블록 연속 변동 없음? → 내공량이라도 변동 필수
8. success 열이 전부 동일? → 최소 2개 "패배"/"부분성공"
9. 내공 전부 상승? → 최소 1개 하락/정체 필수
10. relationship_delta/foreshadow/callback에 영어 문장? → 한국어로 교체
11. strategy/success_pattern에 코드 접미사? → 서사 문장으로 교체
12. solution/event_villain에서 "적대자명만 다르고 나머지 동일"? → 재작성
13. leverage_used가 3블록 이상 동일 세트? → 최소 2항목 교체
14. callback이 전부 "carry-over" 패턴? → 구체적 사건 참조로 교체
15. reward가 context 반복 요약? → 실제 결과, 경지 변화, 세력 변동으로 교체
16. martial_arts_used에 미습득 무공이 있는가? → 수정
17. injury_status에 이전 부상이 근거 없이 사라졌는가? → 회복 서사 추가
18. faction_status 변동이 있는데 content에 근거가 없는가? → 근거 추가
```

---

## 2. 블록 구조 계약

### 2.1 블록 JSON 스키마

```json
{
  "block_id": "Block 1",
  "title": "산골 문파의 불꽃 — 첫 번째 제자",
  "content": {
    "context": "청풍문 3대 장문인 한서진은 문도 다섯, 실력 삼류의 허름한 산골 문파를 이끌고 있다. 선대 장문인의 유언 '청풍문을 세상에 알려다오'가 어깨를 짓누른다. 문파 운영비조차 빠듯한 상황에서 산 아래 마을로 약초를 팔러 내려간다.",
    "event_villain": "마을에서 쫓겨난 거지 소년 진무혁을 발견한다. 마을 건달 3명이 소년을 때리고 있고, 주변 문파 제자들은 구경만 한다. 한서진이 삼류 무공으로 건달들을 겨우 쫓아낸다. 이 과정에서 소년의 근골에서 금색 빛(감재안 발동)을 목격 — 검(劍)의 천재 그릇임을 직감한다.", <!-- utf8-hygiene: allow-line rationale: intentional Hangul+CJK term inside literal JSON example. -->
    "solution": "소년에게 기초 검결 하나를 가르친다. 소년이 세 번 만에 숙달하는 것을 보고 확신한다. '이 아이, 검성의 그릇이다.' 소년을 청풍문 1호 제자로 영입하겠다고 선언하지만, 소년은 어른에 대한 불신이 깊어 쉽게 따르지 않는다. 한서진은 강요 대신 매일 밥을 갖다 주며 신뢰를 쌓기 시작한다.",
    "reward": "진무혁을 1호 제자로 영입하는 데 성공한다. 청풍문 문도가 6명으로 늘어난다. 그러나 소년은 아직 기초 검결 1개뿐이고, 문파 경제 사정은 제자 한 명 더 먹여 살리기 어려운 수준. 한서진의 교육 경지는 사범 입문 단계(5/100)에서 시작."
  },
  "stakes": "1호 제자 영입에 실패하면 청풍문의 미래가 없다. 문파 운영비가 3개월분밖에 남지 않은 상황에서 입 하나 더 늘리는 것은 경제적 위험. 주변 문파가 재능 있는 소년을 빼앗으려 할 가능성",
  "power_shift": {
    "protagonist": "교육 경지 사범 입문(5/100). 삼류 무공이지만 감재안으로 재능을 알아보는 유일한 능력 보유. 1호 제자 확보로 문파 재건의 첫 발을 뗌.",
    "antagonist": "아직 명시적 적대자 없음. 주변 군소 문파들이 청풍문을 업신여기는 상태."
  },
  "relationship_delta": [
    {
      "target": "진무혁 (1호 제자)",
      "before": "신규 — 어른에 대한 깊은 불신. 거지 출신으로 누구도 믿지 않음",
      "after": "매일 밥을 가져다주는 한서진에게 조금씩 마음을 열기 시작. 아직 '사부'라 부르지 않음"
    },
    {
      "target": "백운노인 (장로)",
      "before": "선대 장문인의 벗. 한서진을 걱정하지만 노환으로 실질적 도움은 어려움",
      "after": "진무혁의 재능을 보고 '오랜만에 좋은 소식'이라며 감격. 한서진의 판단을 처음으로 인정"
    }
  ],
  "foreshadow": [
    {"ref": 27, "event": "진무혁이 쓰레기장에서 주운 녹슨 검을 고집스럽게 갖고 다님 — 이 검의 정체가 공개될 것"},
    {"ref": 37, "event": "한서진의 감재안이 발동할 때 눈에 푸른 빛이 스침 — 감재안의 진짜 기원이 드러날 것"}
  ],
  "callback": [],
  "emotional_beat": { "type": "revelation", "intensity": 6 },
  "tension_level": 5,
  "location": {
    "place": "청풍산 기슭 마을",
    "detail": "마을 변두리 빈터 + 청풍문 연무장"
  },
  "time_span": {
    "duration": "2주",
    "in_story_time": "1년차 1월"
  },
  "martial_ext": {
    "realm_before": "삼류 (교육 경지: 사범 입문 5/100)",
    "realm_after": "삼류 (교육 경지: 사범 입문 7/100)",
    "internal_energy_before": "삼류 하급",
    "internal_energy_after": "삼류 하급",
    "martial_arts_acquired": [],
    "martial_arts_used": ["청풍문 기본 권법 (건달 격퇴)", "감재안 (재능 감별)"],
    "injury_status": {
      "current": "정상",
      "change": "변동 없음"
    },
    "faction_status": {
      "affiliation": "청풍문",
      "rank": "장문인",
      "change": "문도 5명 → 6명 (진무혁 영입)"
    },
    "kill_count": 0,
    "spare_count": 0,
    "jianghu_reputation": {
      "before": "무명의 삼류 산골 문파 장문인",
      "after": "무명의 삼류 산골 문파 장문인 (변동 없음)"
    },
    "action_type": "제자 발굴 및 영입",
    "opponent": {
      "name": "없음 (제자 영입 블록)",
      "sect_or_faction": "N/A",
      "weakness_exploited": "N/A"
    },
    "strategy": "감재안으로 재능 감별 후 강요 대신 신뢰 구축 방식으로 접근",
    "success_pattern": "영입 성공, 그러나 경제적 부담 증가",
    "leverage_used": ["감재안", "선대 장문인의 교육 철학", "기본 검결 시연"],
    "martial_domain": "정파 무림",
    "active_domains": ["제자 교육", "문파 운영"]
  }
}
```

### 2.2 블록 필드 정의

| 필드 | 의무 | 설명 |
| ---- | ---- | ---- |
| `block_id` | 필수 | "Block N" 형식 |
| `title` | 필수 | 블록 제목. 한국어. 구체적 사건을 반영 |
| `content.context` | 필수 | 블록 시작 상황. 직전 블록의 결과를 이어받음 |
| `content.event_villain` | 필수 | 적대 행동 또는 갈등 촉발 사건 |
| `content.solution` | 필수 | 주인공의 대응과 해결 |
| `content.reward` | 필수 | 결과와 변화. 경지/세력/관계의 구체적 변동 포함 |
| `stakes` | 필수 | 실패 시 잃는 것. 구체적이고 심각해야 함 |
| `power_shift` | 필수 | 주인공과 적대자의 힘 균형 변화 |
| `relationship_delta` | 필수 | NPC 관계 변화. 최소 2명 |
| `foreshadow` | 필수 | 자연어 복선 심기 배열. 번호 메타는 금지하고, 대상 블록은 `foreshadow_targets`에 둔다 |
| `callback` | 조건부 | 자연어 회수 배열. 번호 메타는 금지하고, 원복선 블록은 `callback_sources`에 둔다 |
| `emotional_beat` | 필수 | 감정 비트와 강도 |
| `tension_level` | 필수 | 긴장도 1~10 |
| `location` | 필수 | 장소. place + detail |
| `time_span` | 필수 | 기간과 작중 시간 |
| `martial_ext` | 필수 | MartialHUD 필드 전체 (§0E) |
| `regression_ext` | 조건부 | 회귀/환생물일 때만. is_regressor, regression_type 등 |

---

## 3. 연속성 체크리스트

### 3.1 경지/내공 연속성 (P0 — 자동 교정 대상)

- [ ] `realm_before(N)` = `realm_after(N-1)`
- [ ] `internal_energy_before(N)` = `internal_energy_after(N-1)`
- [ ] 경지 역행 시 content에 서사 근거(부상/봉인/독/경맥 손상)가 있는가
- [ ] 내공 하락 시 content에 서사 근거가 있는가

### 3.2 부상 연속성 (P0 — 수동 확인)

- [ ] 직전 블록의 `injury_status.current`가 "정상"이 아닌 경우, 이번 블록에서 상태가 추적되는가
- [ ] 부상이 치료/회복 서사 없이 사라지지 않았는가
- [ ] 새 부상이 content에 서사적 원인이 있는가

### 3.3 무공 연속성 (P1 — 수동 확인)

- [ ] `martial_arts_used`의 모든 무공이 이전 블록 누적 `martial_arts_acquired`에 존재하는가
- [ ] 새로 사용하는 무공의 습득 경위가 추적 가능한가

### 3.4 세력/소속 연속성 (P1 — 수동 확인)

- [ ] `faction_status.affiliation`이 변경될 때 content에 근거가 있는가
- [ ] 문파 등급/조직 상태 변화가 content에 반영되어 있는가

### 3.5 NPC 관계 연속성 (P0 — 자동 교정 대상)

- [ ] `relationship_delta.before(N, NPC_X)` = `relationship_delta.after(N-1, NPC_X)`
- [ ] 사망 처리된 NPC가 행동하지 않는가
- [ ] 새 NPC 등장 시 "신규"로 표기되어 있는가

### 3.6 시간 연속성 (P0)

- [ ] `time_span.in_story_time`이 순방향 진행하는가 (역행 0건)
- [ ] duration이 서사 규모에 적합한가

### 3.7 Python 자동 교정 대상

```python
def auto_correct_martial(blocks: list[dict], npc_tracker: dict) -> list[dict]:
    """MartialHUD 연속성 자동 교정"""
    for i, block in enumerate(blocks):
        me = block.setdefault("martial_ext", {})

        # --- 경지/내공 연속성 ---
        if i > 0:
            prev_me = blocks[i-1].get("martial_ext", {})
            me["realm_before"] = prev_me.get("realm_after", me.get("realm_before", ""))
            me["internal_energy_before"] = prev_me.get(
                "internal_energy_after", me.get("internal_energy_before", ""))

        # --- NPC before 이월 ---
        for rd in block.get("relationship_delta", []):
            target = rd.get("target", "")
            if target in npc_tracker:
                rd["before"] = npc_tracker[target]
            npc_tracker[target] = rd.get("after", rd.get("before", ""))

        # --- pov_character 일관성 ---
        if i > 0 and block.get("pov_character") != blocks[0].get("pov_character"):
            block["pov_character"] = blocks[0]["pov_character"]

    return blocks
```

### 3.8 자동 교정 허용/금지 경계

#### 자동 보정 허용

| 필드 | 교정 방식 |
|------|-----------|
| `block_id` | 배치 순서에 맞게 재정렬 |
| `martial_ext.realm_before` | 직전 블록의 `realm_after`로 강제 |
| `martial_ext.internal_energy_before` | 직전 블록의 `internal_energy_after`로 강제 |
| `relationship_delta.before` | 동일 NPC의 직전 `after` 값으로 이월 |
| `regression_ext.is_regressor` | `regression_type in {환생, 회귀}`이면 `true`로 강제 |

#### 자동 보정 금지

| 필드 | 금지 이유 |
|------|-----------|
| `content.*` | 서사 재작성 대상 |
| `martial_ext.realm_after` | 경지 변동은 서사 맥락에 의존 |
| `martial_ext.internal_energy_after` | 내공 변동은 서사 맥락에 의존 |
| `martial_ext.injury_status` | 부상 상태는 서사 판단 필요 |
| `martial_ext.martial_arts_acquired` | 무공 습득은 서사 설계 영역 |
| `stakes` | 손실 규모와 긴장도는 문맥 의존적 |
| `foreshadow` | 자연어 배열. 의미만 적고 번호 메타 금지. 구조 타깃은 `foreshadow_targets`로 분리 |
| `callback` | 자연어 배열. 의미만 적고 번호 메타 금지. 구조 원본은 `callback_sources`로 분리 |

---

## 4. 예시 블록 3개

### 4.1 Block 1 — 시작 (제자 발굴)

```json
{
  "block_id": "Block 1",
  "title": "산골의 불꽃 — 검성의 그릇을 발견하다",
  "content": {
    "context": "청풍문 3대 장문인 한서진(22세)은 선대 장문인의 유언 '청풍문을 세상에 알려다오'를 안고 허름한 산골 문파를 이끌고 있다. 문도 5명, 실력 삼류. 문파 운영비도 빠듯하여 직접 약초를 캐어 마을에 팔러 내려간다.",
    "event_villain": "마을 변두리에서 건달 3명에게 맞고 있는 거지 소년 진무혁을 발견한다. 주변의 이류 문파 '청운문' 제자들은 구경만 하며 비웃는다. 한서진이 삼류 권법으로 간신히 건달을 물리치지만, 청운문 제자들이 '삼류 장문인이 건달이나 잡는군'이라며 조롱. 이 과정에서 감재안이 발동하여 소년의 근골에서 금색 빛이 보임 — 검(劍)의 천재, 검성급 그릇이다.", <!-- utf8-hygiene: allow-line rationale: intentional Hangul+CJK term inside literal JSON example. -->
    "solution": "소년에게 청풍검법 기초 검결을 가르치자 세 번 만에 숙달한다. 천재임을 확신하고 '내 제자가 되어라'고 제안하지만 소년은 거부한다. 어른에 대한 불신이 너무 깊다. 한서진은 강요 대신 매일 밥을 갖다 주며, 검결을 혼자 시연하다 돌아가기를 7일간 반복한다. 7일째 소년이 '그 검법... 좀 더 알려주시오'라 말한다.",
    "reward": "진무혁을 1호 제자로 영입. 청풍문 문도 6명. 교육 경지 사범 입문(5→7). 그러나 문파 살림은 더 어려워짐 — 입 하나 더 늘었고 약초 밭은 그대로. 백운노인 장로가 '오래간만에 좋은 소식'이라며 한서진을 처음으로 칭찬."
  },
  "stakes": "재능 있는 소년을 놓치면 청풍문 재건의 실마리가 사라진다. 삼류 문파 장문인이 건달에게 맞는 모습이 소문나면 문파 위신이 더 추락. 이미 빠듯한 살림에 식구가 늘면 운영비 고갈 3개월 앞당겨짐",
  "power_shift": {
    "protagonist": "무공 삼류, 감재안만이 유일한 강점. 1호 제자 확보로 문파 재건의 씨앗을 심음.",
    "antagonist": "명시적 적대자 없음. 주변 이류 문파 '청운문'이 청풍문을 업신여기는 상태."
  },
  "relationship_delta": [
    {
      "target": "진무혁 (1호 제자)",
      "before": "신규 — 거지 출신. 어른에 대한 깊은 불신",
      "after": "7일간 밥을 가져다주는 한서진에게 조금씩 마음을 열기 시작. '사부님'이 아닌 '어르신'으로 부름"
    },
    {
      "target": "백운노인 (장로)",
      "before": "한서진이 문파를 이끌 수 있을지 걱정하는 늙은 장로",
      "after": "진무혁의 재능을 보고 감격. 한서진의 판단력을 처음으로 인정"
    }
  ],
  "foreshadow": [
    {"ref": 25, "event": "진무혁이 쓰레기장에서 주운 녹슨 검을 절대 놓지 않음 — 이 검의 정체가 공개될 것"},
    {"ref": 35, "event": "감재안 발동 시 한서진의 눈에 푸른 빛이 스침 — 감재안의 기원이 드러날 것"}
  ],
  "callback": [],
  "emotional_beat": { "type": "revelation", "intensity": 6 },
  "tension_level": 4,
  "location": {
    "place": "청풍산 기슭 마을 변두리",
    "detail": "마을 빈터(건달 격퇴) → 청풍문 연무장(검결 전수)"
  },
  "time_span": {
    "duration": "10일",
    "in_story_time": "1년차 1월 상순~중순"
  },
  "martial_ext": {
    "realm_before": "삼류 (교육 경지: 사범 입문 5/100)",
    "realm_after": "삼류 (교육 경지: 사범 입문 7/100)",
    "internal_energy_before": "삼류 하급",
    "internal_energy_after": "삼류 하급",
    "martial_arts_acquired": [],
    "martial_arts_used": ["청풍문 기본 권법", "감재안"],
    "injury_status": { "current": "정상", "change": "변동 없음" },
    "faction_status": {
      "affiliation": "청풍문",
      "rank": "장문인",
      "change": "문도 5명 → 6명 (진무혁 영입)"
    },
    "kill_count": 0,
    "spare_count": 0,
    "jianghu_reputation": {
      "before": "무명의 삼류 산골 문파 장문인",
      "after": "삼류 장문인이 건달을 쫓아냈다는 소문이 마을에 퍼짐 (미미한 인지도)"
    },
    "action_type": "제자 발굴 및 영입",
    "opponent": { "name": "없음 (제자 영입 블록)", "sect_or_faction": "N/A", "weakness_exploited": "N/A" },
    "strategy": "감재안으로 재능 감별 → 강요 대신 7일간 신뢰 구축",
    "success_pattern": "영입 성공, 경제적 부담 증가",
    "leverage_used": ["감재안 (재능 감별)", "청풍검법 기초 검결 시연", "꾸준한 선의(매일 밥 배달)"],
    "martial_domain": "정파 무림",
    "active_domains": ["제자 교육", "문파 운영"]
  }
}
```

### 4.2 Block 5 — 패배 (비무 참패)

```json
{
  "block_id": "Block 5",
  "title": "비무의 치욕 — 청풍문이 무너지던 날",
  "content": {
    "context": "청풍문이 이류 문파 천류문과의 지역 비무대회에 출전한다. 장문인 풍천류가 '삼류 문파가 제자 자랑이나 한다'며 공개 도전장을 보냈고, 거절하면 영역 양보를 요구받는 상황. 진무혁과 소연화 두 제자가 참전하고, 한서진은 지휘석에서 전략을 짠다.",
    "event_villain": "천류문 제자 3명이 각각 진무혁, 소연화와 대결. 진무혁이 첫 판은 이기지만, 천류문 2번 제자의 비열한 암기 공격에 오른팔을 다친다. 소연화는 천류문 수제자에게 완패. 풍천류가 '삼류는 삼류답게 굴지'라며 공개 모욕. 관중석에서 '청풍문 해체하라'는 야유가 터진다.",
    "solution": "한서진이 비무대에 직접 올라 풍천류에게 장문인 대결을 제안하지만, 삼류 무공으로는 풍천류의 일류 검법을 10합도 버티지 못한다. 결국 한서진이 쓰러지고, 진무혁이 부상을 무릅쓰고 뛰어올라 스승을 구한다. 한서진은 의식을 잃기 직전 '져도 괜찮다... 하지만 배울 건 배웠다'고 중얼거림 — 감재안으로 풍천류 검법의 구조적 약점(상단 편중, 하단 빈틈)을 읽어냈다.",
    "reward": "비무 3:1 완패. 청풍문 영역의 남쪽 약초 산지를 천류문에 양보해야 함. 한서진 갈비 2대 골절 + 내상, 진무혁 오른팔 근육 파열. 교육 경지 28→24 하락. 그러나 감재안으로 읽은 천류문 검법의 약점이 다음 교육의 핵심 자산이 될 것."
  },
  "stakes": "비무 패배 시 약초 산지 상실로 문파 운영비 40% 감소. 청풍문 해체 압력 가속. 진무혁의 팔 부상이 영구화되면 검사로서의 미래가 끝남",
  "power_shift": {
    "protagonist": "완패. 경지 하락, 영토 상실, 제자 부상. 그러나 감재안으로 적의 약점을 파악한 것이 유일한 수확.",
    "antagonist": "천류문 풍천류가 압도적 승리. 지역 패권을 굳히고 청풍문 해체론에 힘을 실음."
  },
  "relationship_delta": [
    {
      "target": "진무혁 (1호 제자)",
      "before": "한서진을 '어르신'에서 '사부님'으로 부르기 시작한 상태. 검술 성장에 자신감",
      "after": "패배와 부상에 분노하면서도, 쓰러진 사부를 구하며 '사부님은 제가 지킵니다'라고 선언. 충성심 심화"
    },
    {
      "target": "소연화 (2호 제자)",
      "before": "냉소적이지만 한서진의 교육에 서서히 마음을 열고 있던 상태",
      "after": "자신의 완패에 좌절. '저 때문에 문파가 망했어요'라며 자책. 한서진에 대한 미안함과 분함이 뒤섞임"
    },
    {
      "target": "풍천류 (천류문 장문인)",
      "before": "청풍문을 무시하는 이류 문파 장문인",
      "after": "완승에 만족하지만, 한서진이 10합 안에 자신의 검법 약점을 읽었다는 것을 눈치채고 불쾌함"
    }
  ],
  "foreshadow": [
    {"ref": 18, "event": "한서진이 감재안으로 읽은 풍천류 검법의 '상단 편중, 하단 빈틈' — 이 약점을 제자에게 전수하여 복수 비무 승리의 열쇠로 활용될 것"},
    {"ref": 12, "event": "진무혁의 팔 부상 치료 과정에서 한서진이 '무공과 의술은 같은 뿌리'라는 힌트를 얻음 — 교육법 혁신으로 연결될 것"}
  ],
  "callback": [
    {"ref": 2, "event": "진무혁에게 '검은 이기는 것만이 아니라 지는 법도 배워야 한다'고 가르친 것이 현실화 — 패배 속에서도 배울 것을 배움"},
    {"ref": 3, "event": "소연화가 '저는 혼자서도 싸울 수 있어요'라고 선언한 것이 이번 패배로 시험받음"}
  ],
  "emotional_beat": { "type": "defeat", "intensity": 8 },
  "tension_level": 9,
  "location": {
    "place": "영풍현 비무장",
    "detail": "천류문이 주관하는 지역 비무대회장. 관중석에 주변 5개 문파 장문인들이 참석"
  },
  "time_span": {
    "duration": "3일 (비무 당일 + 치료 2일)",
    "in_story_time": "1년차 8월"
  },
  "martial_ext": {
    "realm_before": "삼류 (교육 경지: 명사 28/100)",
    "realm_after": "삼류 (교육 경지: 명사 24/100 — 하락)",
    "internal_energy_before": "삼류 중급",
    "internal_energy_after": "삼류 하급 (내상으로 인한 일시 하락)",
    "martial_arts_acquired": [],
    "martial_arts_used": ["청풍검법 기본", "감재안 (상대 약점 분석)"],
    "injury_status": {
      "current": "갈비 2대 골절 + 내상. 2개월 안정 필요",
      "change": "정상 → 중상. 내공 운용 50% 수준으로 저하"
    },
    "faction_status": {
      "affiliation": "청풍문",
      "rank": "장문인",
      "change": "남쪽 약초 산지 상실. 문파 운영비 40% 감소 예상"
    },
    "kill_count": 0,
    "spare_count": 0,
    "jianghu_reputation": {
      "before": "제자들이 급성장 중이라는 소문이 지역에 퍼지던 상태",
      "after": "비무 참패로 '삼류는 역시 삼류'라는 평가 고착. 해체론 대두"
    },
    "action_type": "문파 비무 (장문인 대결 포함)",
    "opponent": {
      "name": "풍천류 (천류문 장문인)",
      "sect_or_faction": "천류문 (이류 문파)",
      "weakness_exploited": "이번 블록에서는 약점을 '활용'하지 못하고 '발견'만 함. 풍천류의 검법은 상단 공격에 치우쳐 하단 방어에 구조적 빈틈이 있음"
    },
    "strategy": "장문인 대결로 시간을 끌며 감재안으로 상대 검법 구조 분석. 승리가 아닌 정보 수집이 실질 목표(결과론적)",
    "success_pattern": "완패. 영토 상실. 제자 부상. 그러나 적의 약점 파악이라는 장기 자산 확보",
    "leverage_used": ["감재안 (패배 중에도 분석 가능)", "진무혁의 충성심 (위기 시 스승 보호)"],
    "martial_domain": "정파 무림",
    "active_domains": ["비무", "문파 방어"]
  }
}
```

### 4.3 Block 10 — 전환점 (교육법 혁신)

```json
{
  "block_id": "Block 10",
  "title": "깨달음의 밤 — 모든 무공은 사람에게서 시작된다",
  "content": {
    "context": "비무 참패 이후 청풍문은 영토 축소와 운영비 감소로 위기에 처해 있다. 한서진의 갈비 골절은 치료되었으나 내상이 완전히 회복되지 않은 상태. 진무혁의 팔 부상은 회복되었으나 검법에 미세한 떨림이 남아 있다. 3호 제자 곽대산과 4호 제자 하소룡이 합류했지만, 제자마다 재능의 방향이 달라 하나의 교육법으로는 한계에 부딪힌다.",
    "event_villain": "무림맹 심사관 단목령이 청풍문에 방문하여 '연례 문파 존속 심사'를 통보한다. 삼류 이하 판정이 나오면 문파 해산 명령. 심사 기준은 '제자 3명 이상의 이류 이상 실력 증명'. 현재 진무혁만 이류에 근접하고, 소연화는 삼류 상급, 곽대산은 삼류 중급. 심사까지 6개월. 동시에 인근 산적단이 약해진 청풍문을 노리고 약초 창고 습격을 시도한다.",
    "solution": "한서진은 밤새 제자들의 수련을 관찰하다 깨달음을 얻는다: '나는 지금까지 모든 제자에게 같은 검결을 가르쳤다. 하지만 금색(검)의 진무혁과 적색(도)의 곽대산은 다른 길로 가야 한다.' 감재안으로 각 제자의 재능 색깔과 근골 구조를 재분석하고, 제자별 완전 맞춤형 교육 커리큘럼을 설계한다. 진무혁에게는 경공을 섞은 유연한 검법을, 곽대산에게는 힘을 극대화하는 권각 중심 체계를, 소연화에게는 암기 재능을 살린 원거리 전투를, 하소룡에게는 타고난 속도를 살린 경공 특화를 배정. 산적 습격은 제자들의 첫 실전 테스트로 활용하여 격퇴한다.",
    "reward": "맞춤형 교육 체계 확립. 교육 경지 명사 → 현사 입문(24→35)으로 도약. 제자 4명의 성장 속도가 눈에 띄게 빨라지기 시작. 산적 격퇴로 청풍문의 최소한의 전투력 증명. 단목령 심사관이 '6개월 후 다시 오겠다'며 돌아가면서 '흥미로운 문파'라는 코멘트를 남김. 약초 창고 방어에 성공하여 운영비 위기는 일단 넘김."
  },
  "stakes": "문파 존속 심사에서 삼류 이하 판정이 나오면 청풍문 강제 해산. 산적 습격에 제자가 다치면 심사 전 전력 약화. 맞춤형 교육이 실패하면 남은 6개월 안에 이류 3명 달성 불가능",
  "power_shift": {
    "protagonist": "교육법 혁신으로 성장 속도가 질적으로 변화. 교육 경지 현사 입문. 제자 4명 체제 안정화.",
    "antagonist": "무림맹 심사 제도가 구조적 적대 세력으로 등장. 산적단은 격퇴되었지만 배후에 천류문의 사주 가능성 암시."
  },
  "relationship_delta": [
    {
      "target": "진무혁 (1호 제자)",
      "before": "팔 부상 후유증으로 검에 대한 자신감이 흔들린 상태",
      "after": "맞춤형 경공 검법을 배우며 '사부님이 저만을 위해 검법을 만들어 주셨다'고 감동. 충성심 최고조"
    },
    {
      "target": "곽대산 (3호 제자)",
      "before": "신규 — 광부 아들. 힘은 세지만 머리가 느려 검법을 제대로 따라하지 못해 좌절 중",
      "after": "권각 중심 체계를 받고 '이건 제가 할 수 있는 무공입니다!'라며 처음으로 자신감. 한서진을 진심으로 사부로 인정"
    },
    {
      "target": "단목령 (무림맹 심사관)",
      "before": "신규 — 관료적이고 냉정한 심사관. 삼류 문파에 큰 기대 없음",
      "after": "산적 격퇴를 목격하고 약간의 관심. '6개월 후'라는 유예 자체가 관례보다 관대한 조치"
    }
  ],
  "foreshadow": [
    {"ref": 20, "event": "단목령이 청풍문에 관심을 보인 것 — 문파 등급 심사의 우호적 변수로 작용할 것"},
    {"ref": 14, "event": "산적 습격의 배후에 천류문 사주 가능성 — 증거가 발견될 것"},
    {"ref": 35, "event": "한서진의 감재안이 '색깔'뿐 아니라 '근골 구조'까지 읽을 수 있게 된 변화 — 감재안의 정체가 '심안결'임이 밝혀지는 단서"}
  ],
  "callback": [
    {"ref": 5, "event": "감재안으로 읽은 '풍천류 검법의 상단 편중' 분석이 이번 맞춤형 교육의 핵심 원리로 발전 — 상대 약점을 아는 것이 곧 제자별 강점을 설계하는 열쇠"},
    {"ref": 7, "event": "곽대산이 '저는 검이 안 맞습니다'라고 울먹이던 것이 이번 권각 배정으로 해결"}
  ],
  "emotional_beat": { "type": "realization", "intensity": 7 },
  "tension_level": 7,
  "location": {
    "place": "청풍문 내원 수련동",
    "detail": "야간 수련장(깨달음) → 문파 앞마당(산적 격퇴) → 연무장(맞춤 교육 시작)"
  },
  "time_span": {
    "duration": "1개월",
    "in_story_time": "2년차 2월"
  },
  "martial_ext": {
    "realm_before": "삼류 (교육 경지: 명사 24/100)",
    "realm_after": "삼류 (교육 경지: 현사 입문 35/100)",
    "internal_energy_before": "삼류 중급 (내상 회복 후)",
    "internal_energy_after": "삼류 상급 (교육 깨달음에 의한 미세 상승)",
    "martial_arts_acquired": ["맞춤형 교육 설계법 (교육 무공)", "청풍검법 경공 변형 (진무혁용 설계)"],
    "martial_arts_used": ["감재안 (제자 재능 재분석)", "청풍문 기본 권법 (산적 격퇴)"],
    "injury_status": {
      "current": "갈비 골절 완치, 내상 90% 회복. 과도한 감재안 사용으로 두통",
      "change": "Block 5 중상에서 대부분 회복. 새로운 경미 증상(두통) 추가"
    },
    "faction_status": {
      "affiliation": "청풍문",
      "rank": "장문인",
      "change": "문파 존속 심사 통보. 6개월 유예. 산적 격퇴로 최소한의 전투력 증명"
    },
    "kill_count": 0,
    "spare_count": 3,
    "jianghu_reputation": {
      "before": "비무 참패 이후 '삼류는 삼류' 평가가 고착된 상태",
      "after": "산적 격퇴 소식이 지역에 퍼지며 '그래도 산적은 막는 문파'라는 최소 인정"
    },
    "action_type": "교육법 혁신 + 산적 격퇴 (실전 교육)",
    "opponent": {
      "name": "영풍산 산적단 두목 철곤",
      "sect_or_faction": "비소속 산적단 (배후 불명)",
      "weakness_exploited": "산적단은 개인 무력은 있으나 진형과 협동이 전무. 제자들의 연계 공격으로 각개격파"
    },
    "strategy": "산적 습격을 제자 실전 교육의 기회로 전환. 감재안으로 산적 두목의 공격 패턴을 읽고 제자별 역할 배정",
    "success_pattern": "산적 격퇴 + 교육법 혁신 = 이중 성과. 문파 존속 위기는 아직 진행 중",
    "leverage_used": ["감재안 (제자 재능 재분석 + 적 패턴 분석)", "맞춤형 교육 커리큘럼", "제자 4명의 연계 전투", "약초 창고 지형 이용"],
    "martial_domain": "정파 무림",
    "active_domains": ["제자 교육", "문파 방어", "비무 준비"]
  }
}
```

---

## 5. 밀도 게이트

### 5.1 생산 밀도 게이트 (실전용 필수)

정합성이 맞아도 아래 기준을 못 넘기면 `production_ready = false`로 본다.
이 경우 결과물은 draft가 아니라 **skeleton draft**로 분류하며, 출고 전 재생성이 원칙이다.

핵심 서술 밀도:

- `context + event_villain + solution + reward + stakes` 평균(`avg_bundle_chars`) 350자 이상
- 300자 미만 블록(`critical_thin_blocks`) = 0
- 300~349자 블록(`thin_blocks`) 전체 비율 10% 이하, 마지막 10블록 0개
- `block_cider_missing_blocks = 0`
- `no_cider_blocks = 0`
- `pain_only_exit_blocks = 0`
- `cider_receipt_line_missing_blocks = 0`

반복 검출 — 같은 적대자:

- `opponent_unique` 6명 이상
- 단일 opponent 점유율 30% 이하
- 연속된 2개 이상의 10블록 구간이 동일 2인 opponent 로테이션 = 0건
- 마지막 10블록에서 opponent 공백 1블록까지 허용

반복 검출 — 같은 무공/약점:

- 동일 `weakness_exploited` 3회 이상 = 0건
- 동일 `opponent + weakness_exploited` 조합 4회 이상 = 0건
- 동일 `martial_arts_used` 세트가 5블록 이상 반복 = 경고 (같은 무공만 쓰면 성장이 없는 것)

반복 검출 — 서사 패턴:

- `action_type` 최대 반복 4회 이하
- `strategy` 최대 반복 4회 이하
- `success_pattern` 동일 표현 3회 이상 = FAIL

복선/회수:

- `foreshadow` 평균 0.8개 이상
- `callback` 평균 0.8개 이상
- `callback_ratio >= 0.65`
- `unresolved_foreshadow_count <= foreshadow_total * 0.35`

관계:

- `relationship_delta` 평균 대상 수 2.0 이상
- 관계 동결(5블록 이상 before=after) = 0건

MartialHUD 고유 밀도:

- `realm` 정체(3블록 연속 realm_before=realm_after이고 내공/무공/깨달음 변동도 없음) = 0건
- `injury_status` 미추적(부상 후 3블록 이상 언급 없음) = 0건
- `martial_arts_acquired` 전체 합계 10종 이상 (70블록 기준)
- `kill_count + spare_count` 전체 합계 0이면 전투가 없는 것 = 전투 블록 최소 15개
- `quiet block`도 면책이 아니다. 휴식/회복 블록이어도 same-block 영수증이 있어야 통과

### 5.2 반복 검출 상세

| 검출 항목 | 기준 | 심각도 |
| ---- | ---- | ---- |
| 같은 적대자 3블록 연속 | opponent.name이 3블록 연속 동일 | P1 |
| 같은 적대 세력 10블록 연속 | opponent.sect_or_faction이 10블록 연속 동일 | P1 |
| 같은 무공 과다 사용 | martial_arts_used 세트 5블록 이상 동일 | P1 경고 |
| 같은 action_type 3블록 이내 | action_type 3블록 이내 재등장 | P1 |
| 같은 location 3블록 이내 | location.place 3블록 이내 재등장 | P1 |
| 경지 정체 3블록 | realm_before=realm_after 3블록 연속 + 내공/무공 변동도 없음 | P0 |
| 내공 연속 상승 10블록 | internal_energy 10블록 연속 증가 | P1 — 최소 1개 정체/하락 필수 |
| 부상 미추적 | injury_status 부상 후 3블록 이상 언급 없이 정상 복귀 | P0 |

### 5.3 의무 수치 출력 (감리 보고서)

3-Pass 감리 보고서에는 아래 수치를 반드시 남긴다.

```text
- opponent_unique: 8
- top_opponent_repetition: 12
- top_opponent_weakness_pair_repetition: 3
- action_type_top_repetition: 4
- strategy_top_repetition: 3
- window_10_opponent_unique_counts: [3, 3, 4, 3, 2, 3, 4]
- avg_context: 120.5
- avg_event_villain: 95.3
- avg_solution: 130.2
- avg_reward: 85.1
- avg_stakes: 65.8
- avg_bundle_chars: 496.9
- foreshadow_total: 85
- callback_total: 62
- callback_ratio: 0.73
- unresolved_foreshadow_count: 12
- critical_thin_blocks: []
- thin_blocks: []
- block_cider_missing_blocks: []
- no_cider_blocks: []
- pain_only_exit_blocks: []
- cider_receipt_line_missing_blocks: []
- realm_stagnation_blocks: []
- injury_untracked_blocks: []
- total_martial_arts_acquired: 18
- total_combat_blocks: 28
- recognition_signal_blocks: 8 (환생/회귀물일 때만)
- production_density_gate: PASS
```

---

## 6. 감정 비트 확장 목록 (무협 20종+)

기존 4종(`resolve/pressure/breakthrough/victory`) 순환을 탈피:

| 유형 | 설명 | intensity | 무협 장면 예시 |
|------|------|-----------|--------------|
| `triumph` | 완전한 승리 | 8~10 | 비무 완승, 경지 대돌파 |
| `pyrrhic_victory` | 대가를 치른 승리 | 5~7 | 적 격퇴했으나 경맥 손상 |
| `defeat` | 실질적 패배 | 2~4 | 비무 참패, 영역 상실 |
| `betrayal` | 배신당함 | 7~9 | 동문 배신, 제자 이탈 |
| `revelation` | 중대한 사실 발견 | 6~9 | 비급 발견, 적의 정체 밝혀짐 |
| `sacrifice` | 희생적 선택 | 5~8 | 내공 소모해 제자 구함, 비급 포기 |
| `isolation` | 고립/고독 | 3~5 | 강호에서 축출, 독행 수련 |
| `reconciliation` | 화해/관계 회복 | 5~7 | 라이벌 화해, 가문 내분 봉합 |
| `escalation` | 위기 고조 | 7~9 | 적대 세력 연합, 전면전 임박 |
| `respite` | 숨고르기/평화 | 2~4 | 은거 수련, 상처 회복기 |
| `moral_dilemma` | 윤리적 갈등 | 6~8 | 살생 vs 방생, 의리 vs 이익 |
| `confrontation` | 정면 대결 | 8~10 | 최종 결전, 장문인 대결 |
| `realization` | 깨달음/자기성찰 | 4~6 | 무공의 이치 깨달음, 교육 철학 정립 |
| `humiliation` | 굴욕 | 3~6 | 공개 비무 참패, 적에게 무릎 꿇음 |
| `alliance` | 새로운 동맹 | 5~7 | 문파 연합, 사제 결연, 의형제 맺음 |
| `deception` | 속임수 성공/발각 | 6~8 | 간자 발각, 위장 잠입 성공 |
| `transformation` | 캐릭터 변화 | 5~8 | 사공→정공 전환, 살수→협객 전환 |
| `countdown` | 시간 제한 긴장 | 8~10 | 독 해독 시한, 비무 기한, 구출 제한 |
| `aftermath` | 사건 후유증 | 3~5 | 전투 후 부상 치료, 패배 후 재정비 |
| `breakthrough` | 경지 돌파 | 7~9 | 화경 진입, 신공 개안 |
| `inheritance` | 전승/계승 | 5~8 | 비급 전수, 장문인 계승, 유언 전달 |

---

## 7. 무협 결정적 액션 유형 확장 (`action_type` 24종+)

| 유형 | 대표 프로파일 |
|------|--------------|
| 비무 대결 | `orthodox_wuxia_profile`, `munpa_profile` |
| 생사결 (실전) | `orthodox_wuxia_profile` |
| 비급/무공 습득 | 전체 |
| 영약/영물 획득 | `xianxia_profile`, `medical_wuxia_profile` |
| 경지 돌파 수련 | 전체 |
| 문파/세가 비무대회 | `munpa_profile`, `sega_profile` |
| 문파 등급 심사 | `munpa_profile` |
| 제자 영입/교육 | `training_wuxia_profile`, `munpa_profile` |
| 세력 동맹/교섭 | 전체 |
| 첩보/잠입 | `orthodox_wuxia_profile` |
| 의술 치료 | `medical_wuxia_profile` |
| 독 해독/경맥 치료 | `medical_wuxia_profile` |
| 상단 거래/교역 | `merchant_wuxia_profile` |
| 유통망 장악 | `merchant_wuxia_profile` |
| 약재/무기 조달 | `merchant_wuxia_profile`, `munpa_profile` |
| 문파 재건/영역 확장 | `munpa_profile` |
| 가주 승계 | `sega_profile` |
| 가문 무공 전수 | `sega_profile` |
| 보물/비경 탐사 | 전체 |
| 원수 추적/복수전 | 전체 |
| 의형제/사제 결연 | 전체 |
| 무림맹/관부 교섭 | 전체 |
| 마교/사파 침투 | `orthodox_wuxia_profile` |
| 구출/호위 임무 | 전체 |

금지 해석:

- `action_type`을 "전투", "수련", "이동" 같은 추상어로만 채우지 않는다.
- 의술무협인데 억지로 비무 대결만 넣지 않는다.
- 상업무협인데 모든 해결을 칼싸움으로 처리하지 않는다.
- 반대로 정통무협인데 모든 갈등을 '대화로 해결'하지 않는다.

---

## 8. 대단원 종료 시 필수 보조 출력 (4종)

### A. NPC 추적표

```
| NPC 이름 | 등장 블록 | 마지막 활동 | 현재 관계 (= 다음 블록 before) | 다음 예정 |
|----------|-----------|-------------|-------------------------------|-----------|

검증:
- 활성 NPC ≤ 2명 → 다음 대단원에서 최소 2명 추가
- 10블록 동안 NPC 변동 0건 → 재설계
- "현재 관계" 열에 동일 문장 2명+ → 차별화
```

### B. 복선 원장

```
| # | 복선 내용 | 심기 블록 | 목표 회수 블록 | 실제 회수 블록 | 상태 |
|---|-----------|-----------|---------------|---------------|------|

검증:
- OPEN 복선 20개+ 누적 → 5개 이상 이번 대단원에서 회수
- 심기 후 20블록+ 미회수 → 즉시 회수 또는 "폐기"
- 장기 복선(간격 10블록+) 5개 미만 → 추가
```

### C. 경지/내공 곡선 ASCII

```
Block N+1:  ████████ 삼류 중급 (내공 8갑자)
Block N+2:  █████████ 삼류 상급 (내공 10갑자)
Block N+3:  ██████ 삼류 중급 (부상으로 내공 역류, 6갑자)
...

검증:
- 10블록 연속 상승 → 최소 1블록 하락/정체
- 경지 변동 5블록+ 없음 → 내공이라도 변동 필수
- 최종 경지가 Phase 0 목표 ±1단계 이탈 → 조정
```

### D. 적대자 상태 (20블록마다)

```
현재 적대자: [이름]
- 소속: [문파/세력]
- 활동 기간: Block X~Y (Z블록)
- 실질적 교전 횟수: N회
- 약점 노출 종류: N종 (3종 이하 → 추가 필요)

### 20블록 초과 시 필수 조치 (택 1)
□ 적대자 분열    □ 적대자 교체
□ 적대자 진화    □ 적대자 동맹
```

---

## 9. Routed CLI Commands

### Prompt

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia prompt \
  --draft treatments/<work_id>_tr_block_070_draft.json \
  --roadmap bible/0_bi_<work_id>.json \
  --start <start_block> \
  --batch-size 1 \
  --output treatments/<work_id>_batch_prompt.md
```

### Check

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia check \
  --candidate treatments/<candidate>.json \
  --draft treatments/<work_id>_tr_block_070_draft.json \
  --start <start_block> \
  --batch-size 1 \
  --report treatments/<work_id>_batch_check.md
```

### Merge

```bash
python -X utf8 scripts/narrative_tr_batch.py --genre wuxia merge \
  --draft treatments/<work_id>_tr_block_070_draft.json \
  --candidate treatments/<candidate>.json \
  --start <start_block> \
  --batch-size 1 \
  --report treatments/<work_id>_batch_merge.md
```

---

## 10. Production Guardrails

### 10.1 blockguide 필드 금지

- `capital_before/after`를 wuxia 유효성 검사에 요구하지 않는다.
- `deal_type`, `business_sector`, `company_state`, `business_lines`를 무협 블록의 필수 필드로 요구하지 않는다.
- 모든 성장을 재화 메타포로 번역하지 않는다.

### 10.2 하이브리드 작품 규칙

상업무협처럼 무협 + 상업 축이 모두 필요한 작품은:

- `martial_ext`가 주축이다. `genre_ext`(blockguide 호환)를 보조로 추가할 수 있다.
- 무협 연속성(경지, 내공, 부상)이 상업 연속성(거래 규모, 영향력)보다 우선한다.
- 충돌 시 `martial_ext` 기준이 SSOT다.

### 10.3 인코딩

- 모든 산출물은 **UTF-8 only**로 저장한다.
- `???`, `�`, 인코딩 오염은 P0다. <!-- utf8-hygiene: allow-line rationale: literal mojibake tokens are documented here as stop-gate examples. -->

---

## 11. 출고 게이트 (합격 조건)

### P0 게이트 (자동화 필수 — 1건이라도 있으면 출고 불가)

- realm 연속성 위반 0건
- internal_energy 연속성 위반 0건
- NPC before 리셋 위반 0건
- 시간 역행 0건
- pov_character 불일치 0건
- 죽은 NPC 행동 0건
- 부상 미추적 0건
- 경지 무근거 역행 0건

### P1 게이트 (감리 확인 — 각 0건)

- 영문 템플릿 0건
- 복선 미회수율 35% 이하
- 관계 동결(연속 5블록+) 0건
- 적대자 3세력 이상
- NPC 8명 이상
- 패배 블록 7개 이상
- emotional_beat 6종 이상
- callback 구체적 사건 참조 (기계 패턴 0건)
- action_type 10종 이상
- leverage_used 동일 세트 3회 미만
- reward 재진술 0건
- relationship_delta 복제 문장 0건
- 대단원 슬롯 반복 0건
- martial_arts_used 미습득 무공 사용 0건

### P2 게이트 (권장)

- 코드형 토큰 0건
- reward 한국어
- duration 3종 이상
- location 8곳 이상, 10블록 이내 재등장 0건
- 핵심 서술 평균 길이 400자 이상
- foreshadow 평균 1.0 이상
- callback 평균 1.0 이상
- martial_arts_acquired 전체 10종 이상
- 전투 블록 15개 이상

---

## 12. 실행 순서 요약

```
0. docs/wuxguide/SSOT_wuxguide-integrated-order.md를 UTF-8로 읽고 현재 단계 판정
   ↓
1. Bible/기획안/Phase 0 존재 여부 확인
   → planning 단계면 wuxia-planning-harness.md로 복귀
   ↓
2. Phase 0: 대단원 아크 설계
   → 적대자 변천, NPC 타임라인, 경지 곡선, 복선 맵, 패배 계획
   ↓
3. 생산 시작 전 직전 SSOT 재오픈
   → phase0_design + 직전 candidate/fixed/draft
   ↓
4. Phase 1: 블록 1개씩 순차 생성
   → 사전 선언 8항목 + 절대 금지 33개 + MartialHUD 연속성 체크
   ↓
5. 생성 직후 자가 점검
   → 절대 금지 33개를 먼저 눈으로 점검
   ↓
6. Phase 2: Python 자동 교정
   → realm/internal_energy/NPC/pov 강제 교정
   ↓
7. Phase 3: Python 자동 검증 + 위반 블록 재생성
   → MartialHUD 연속성 + 서사 반복 탐지
   → 위반 블록만 LLM 재생성
   ↓
8. 통과한 블록만 merge
   → 실패 블록은 같은 범위만 재생성
   ↓
9. Phase 4: 3-Pass 감리
   → 1차 전수 → 2차 오탐 제거 → 3차 최종 확정
   ↓
10. 출고 게이트 통과 (§11)
    → P0 0건, P1 0건, P2 권장 충족
    ↓
11. production_ready = true 확인
    → 밀도 게이트 실패 시 skeleton draft로 분류하고 재생성
    ↓
12. treatments/{work_id}_tr_block_070_draft.json 저장
    ↓
13. 사용자가 다음 스텝 입력 시 wuxia-bi-production-harness.md로 인계
```

---

---

## 컨텍스트 윈도우 대응 — 자동 체크포인트

### 자동 저장 규칙
1. 블록 생산 완료 시마다 즉시 tr_block_070_draft.json에 머지하고 저장한다. "나중에 한꺼번에" 금지.
2. 블록 저장 후 sequential_run_status.json을 업데이트한다:
   - last_sequential_block_pass = 완료된 블록 번호
   - next_unit_type = 다음 단위 (`block` | `merge` | `bi_handoff`)
   - next_block_id = 다음 단위가 block이면 다음 블록 번호, 아니면 null
   - run_class = sequential_production
3. 같은 운영 오더 안에서는 최대 5블록까지만 자동 연속 진행한다.
   - Block 1~4 종료: continuity check 통과 시 다음 블록으로 진행 가능
   - Block 5 종료: continuity check 후 반드시 정지하고 새 오더를 기다린다
4. 5블록마다 중간 정합성 체크를 수행한다:
   - python scripts/block_continuity_checker.py --work-id {work_id} --family {family}
   - 불일치 발견 시 즉시 수정 후 다음 블록 진행

### 세션 종료 시
5. context window 한계가 가까워지면 (압축 경고 발생 시):
   - 현재 진행 중인 블록을 완료하고 저장
   - sequential_run_status.json 업데이트
   - "세션 종료. python scripts/generate_resume_prompt.py --work-id {work_id} 실행하여 다음 세션 프롬프트를 생성하세요." 출력
6. 비정상 종료 대비: 블록 단위 즉시 저장이 이미 되어 있으므로, 다음 세션에서 generate_resume_prompt.py가 정확한 재개 지점을 알려준다.

### 자동 진행 규칙
7. 이 절의 auto-run은 **TR production 범위에만** 적용한다. Stage 0/Planning 전이는 각 전용 하네스가 따로 판정한다.
8. Production auto-run은 `1블록씩 + 최대 5블록`까지만 허용한다.
9. `Block 70` 완료 후 source TR gate가 정상이면 BI 하네스로 handoff할 수 있다.
10. 5블록 창 소진, 강제 정지 게이트, compaction 경고 중 하나라도 오면 새 오더 전까지 재개하지 않는다.

---

*이 문서는 `treatment-production-harness-v2.md` (blockguide 골든 스탠다드 2055줄) 구조를 무협/선협/세가물/문파물에 적용한 wuxguide 패밀리 전용 생산 하네스입니다. MartialHUD를 canonical로 삼고, 경지/내공/부상/무공/세력 연속성을 blockguide의 자본/NPC 연속성에 대응시킵니다.*
