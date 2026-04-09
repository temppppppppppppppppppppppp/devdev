# hoegui_surgeon — ARC-07 Entry Handoff (Block 61 ~ 65 생산 설계)

Date: 2026-04-09
Work ID: `hoegui_surgeon`
Scope: ARC-07 "왕좌" 진입 — Block 61 `과장 선임` 생산 전 정렬 handoff
Basis:
- `treatments/hoegui_surgeon_tr_block_020_draft.json` (boundary=60)
- `treatments/phase0/hoegui_surgeon_phase0_design.json` ARC-07 block_slots 61-70
- `docs/2026-04-09/hoegui_surgeon_block_51_60_self_audit.md` (3-Pass audit §P3.4 Next 10 Focus)
- `docs/2026-04-09/hoegui_surgeon_live_status.md` (Block 60 boundary)
- `work_guards/12_hoegui_surgeon.yaml`
- `docs/blockguide/treatment-production-harness-v2.md` §0D 의사물 profile, §0G 사이다 계약, §1.5 Gemini-safe, §1.1C 10-block 감리

---

## 1. ARC-07 Entry 조건 확인

- [x] ARC-06 exit_function 3축 달성 (Block 59-60)
- [x] 10-block self-audit (51-60) 3-Pass 완료 (차단 0건)
- [x] TR boundary=60, `_arcs_covered` ARC-06 포함, `_next_continuation_boundary`=61
- [x] Phase0 ARC-07 block_slots 61-70 확인 완료
- [x] live_status 2026-04-09 동기화 (Block 60 기준)
- [x] work_guard custom_rules + forbidden_flattenings 재확인

**ARC-07 entry 조건 통과**. Block 61 생산 가능.

---

## 2. Phase0 ARC-07 원본 (SSOT)

**ARC-07 "왕좌"** (Block 61-70, 2029년 7월 ~ 2032년)
- **capital_target**: 과 운영 실권자 → 진료과장 + 외과학회 영향력 + 수술 결정권 체계 확립
- **front_sectors**: 진료과장 선임 + 외과학회 체계
- **support_sectors**: 해외 학회 + 후진 양성
- **main_opponents**: 이상훈(최종 라이벌) + 기존 교수진 저항
- **new_npcs**: [] (없음)
- **emotion_curve**: 진료과장 도전 → 이상훈 최종 대결 → 학회 체계 제안 → 과장 확정 → 왕좌
- **quiet_blocks**: [66]
- **defeat_blocks**: [64]
- **entry_function**: 진료과장 선임에 도전하고 최종 라이벌과 결착한다
- **exit_function**: 진료과장 확정. "서동혁 소견 없이 고난도 수술을 열지 않는다"는 관행 확립

**block_slots**:
| Block | Title | Phase0 function |
|---|---|---|
| 61 | 과장 선임 | 외과 진료과장 선임 시즌. 서동혁이 후보에 오른다. 수술 실적, M&M 기록, 교육 재편 실적이 근거 |
| 62 | 이상훈의 도전 | 이상훈이 타 대학에서 서동혁과 동일 포지션을 노리며 학계에서 경쟁 구도를 만든다 |
| 63 | 최종 케이스 | 국내 최고 난이도 수술 케이스가 서동혁의 병원에 의뢰된다. 성공 여부가 과장 선임의 결정타 |
| 64 | 변수 (defeat) | 수술 중 예상치 못한 합병증. 3만 건의 경험에도 없던 패턴. 서동혁이 처음으로 경험의 한계에 부딪힌다 |
| 65 | 현재의 판독 | 서동혁은 과거 경험이 아닌 현재의 판단으로 합병증을 통제한다. **회귀자의 기억이 아니라 이번 생에서 쌓은 실력이 증명되는 순간** |
| 66 | 수술 성공 (quiet) | 수술 성공. 학회와 병원 내부에서 서동혁의 위치가 확정적 |
| 67 | 학회 제안 | 외과학회에 수술 전 판독 기반 표준 프로토콜 제안. **개인의 관행이 학회 표준으로 올라가는 시작** |
| 68 | 강태준의 퇴장 | 강태준이 정년을 앞두고 서동혁에게 한마디. 적대도 인정도 아닌, "네 방식이 맞았다"는 한 줄 |
| 69 | 진료과장 | 서동혁이 외과 진료과장으로 확정. **전생에서 과장으로 퇴직한 자리를 이번에는 출발점으로** |
| 70 | 왕좌 | "서동혁 소견 없이 고난도 수술을 열지 않는다"는 관행 확립. **서열이 아니라 판독력이 결정권의 기준** |

---

## 3. 이월 이슈 annotation (I-51-60-A / I-51-60-D 본 handoff에서 처리)

### 3.1 I-51-60-A — Phase0 ARC-06 exit_function "과 운영 실권" 해석 매핑

**문제**: Phase0 ARC-06 exit_function 문구 "과 운영 실권"이 literal reading 시 "과장급 또는 상위 결정권"으로 읽힐 수 있으나, work_guard `custom_rules: 서열은 그대로인데 실질적 결정권이 뒤집히는 구조`를 준수하기 위해 본문 Block 59는 "은폐 수습 TF 실무 책임자 임시 직책 + 3축 통합 실무 + 과장 영역 불변 + 자동 해제 조항"으로 한정 해석했다.

**해석 매핑 (본 handoff 확정)**:

| Phase0 문구 | work_guard 준수 해석 |
|---|---|
| "과 운영 실권" | **"특정 국면(은폐 수습)의 실무 권한 이양 + 과장 자리는 불변"** |
| "병원장 라인으로부터 독립" | "FS-27 모니터링 경로 3회 차단 + 나경태 직접 전화 차단 + 조건부 승인 권고 서면의 역작동(차단 근거)" |
| "수술 교육 체계 재편 시작" | "외과 수술 교육 위원회 4축 필수 모듈 편제 가결 + 2029-09 신학기 적용" |

**ARC-07 적용 규칙**:
- Block 61 과장 "후보" 등재 시점에서도 동일 원칙 유지: "후보 등재"는 공식 절차 기록 수준, "최연소" 표현 금지
- Block 69 진료과장 "확정"에 이르기까지 "실권"을 규모 표현이 아닌 "실질 결정권 축"으로만 서술
- "과장 자리 탈취" 서사 금지, "제도 경로로 서열 축과 결정권 축이 같이 움직이는 구조" 유지

**I-51-60-A 처리**: **본 handoff에서 주석 완료**. `phase0_addendum` 별도 envelope 불필요.

### 3.2 I-51-60-D — FS-07/FS-10 단독 집도 유예 structural_resolution 주석

**문제**: FS-07(단독 집도 유예 정식 심사) + FS-10(유예 시한)이 ARC-03 Block 23에서 seed → ARC-06 내내 정식 심사 미개최. Phase0 또는 본문에 명시적 해소 기록 부재.

**해소 근거 (본 handoff 확정)**:
- **Block 51 callback**: "R2 펠로우 종료 + 조교수 직급 부여" 명시
- **해석**: 단독 집도 유예는 R2 펠로우 신분의 부수 제약 조건. Block 51 정식 임용으로 R2 신분 자체가 종료되면 유예 대상 존재가 소멸 → **structural resolution by status transition**
- **Pattern N (복선-회수 단절) 미해당**: 정식 심사 이벤트가 실종된 것이 아니라, 심사 대상 신분 자체가 승격으로 소멸한 것 — 단절 아닌 전제 소멸

**ARC-07 적용 규칙**:
- Block 61 handoff 시점에서 FS-07/FS-10은 **structural_resolution by Block 51** 상태로 고정
- ARC-07 어느 블록에서도 "단독 집도 유예"를 재소환할 수 없음 (유예 조건 자체가 소멸)
- orphan seed 아님 (본 handoff로 추적 종료)

**I-51-60-D 처리**: **본 handoff에서 주석 완료**. Block 51 callback 추가 편집 불필요.

### 3.3 잔여 I-51-60 이슈 (본 handoff 범위 외)

- **I-51-60-B** (박정민 NPC back-reference) — `phase0_addendum` 별도 envelope 권장, ARC-07 생산에 직접 영향 없음 (박정민은 ARC-07 미등장)
- **I-51-60-C** (윤지영 NPC 등록) — ARC-07 동결 유지 권장(R8'"), Phase0 등록 여부는 ARC-08 이후 결정
- **I-51-60-E** (FS-30/FS-34 ARC-07 처리) — **동결 유지** 본 handoff에서 확정 (R8'" + ARC-07 capital_target이 진료과장 + 학회 체계이지 병원장 라인 청산 아님)
- **I-51-60-F** (§0G block_cider 형식/실질 ambiguity) — 하네스 상위 방침 결정 대기, 본 audit는 실질 PASS 기준 운영

---

## 4. Block 61 `과장 선임` 생산 설계

### 4.1 Phase0 정렬

- **slot 61 title**: 과장 선임
- **slot 61 function**: 외과 진료과장 선임 시즌. 서동혁이 후보에 오른다. 수술 실적, M&M 기록, 교육 재편 실적이 근거.
- **tension**: 6 (안정 진입, ARC-07 권장 곡선 6-7-8-8-7-5-7-6-8-8)
- **beat**: candidate_registration (권장, ARC-06 formal_ascension과 결이 다른 ARC-07 고유 beat)
- **authority delta**: +2 (추정, 후보 등재 수준)
- **time_span**: 약 3-4주, 2029년 7월 ~ 8월 초 (TF 자동 해제 2029-07 직후)

### 4.2 필수 설계 요소

#### 4.2.1 진입 조건 처리 (R9'")

- **TF 실무 책임자 자동 해제 2029-07** 실제 작동 서술
- **조영채 과장의 4단 운영 단서 (자동 해제 조항)** 공식 해제 회신
- **조교수 4축 단일 직책 복귀** 후 진료과장 후보 등재 — 연장 요청 금지 원칙 유지
- 자동 해제를 **연장하려 시도했다는 서술 없음** (해제 수용이 자연)

#### 4.2.2 후보 등재 근거 3축 (Phase0 slot 61 명시)

1. **수술 실적**: ARC-05 ~ ARC-06 간담도·췌장·상복부 고난도 수술 누적 수치 + 합병증률 (단 "국내 최저" 등 규모 과시 금지, 병원 내부 통계 층에서만)
2. **M&M 기록**: Morbidity & Mortality Conference 기록 — 서동혁 케이스 기록 밀도 + 판독 기반 사전 설계 적용 케이스 추적
3. **교육 재편 실적**: Block 60 FS-20 full_payoff 4축 필수 모듈 편제안 가결 + 2029-09 신학기 적용 — **교육 축이 후보 근거로 직접 작동하는 첫 장면**

#### 4.2.3 opponent 설계 (패턴 피드백 원칙 준수)

**ARC-06 직전 batch opponent 빈도 경고**:
- 박정민 5/10 — **ARC-07 재등장 금지** (자진 보직 조정 퇴조 완결)
- 나경태 ARC-06 3회 — **ARC-07 직접 등장 자제, 간접 언급만**
- 권혁수 ARC-06 5회 — 형식 한정 유지

**Block 61 신규 opponent 축**:
- **임상 과장진 경쟁 후보 1-2인** (서동혁 외 진료과장 후보) — "기존 교수진 저항" Phase0 main_opponent의 구체화. 단 Block 61 단계에서는 "후보 3인 경쟁" 구도만, 공격 각도는 "연차·서열 역전 우려" 수준
- **이상훈은 Block 62 예정** — Block 61에서 언급 금지, 후보 등재 시점과 이상훈 타 대학 포지션 경쟁 시점 분리

#### 4.2.4 weakness 신규 축 (Pattern S 반복 금지)

ARC-06 누적 weakness 재사용 금지. Block 61 권장 신규 축:
- **"진료과장 선임 기준 '수술 실적 vs 학술 영향력' 가중치 경쟁 구조의 기존 관행 편향"**
- **"연차 역전 후보의 내부 공식 절차 대응 미숙"** (경쟁 후보 측 weakness)

#### 4.2.5 callback / foreshadow

**필수 callback**:
- Block 60 교육 재편 4축 필수 모듈 제도화 → 후보 근거 3축 중 "교육 재편 실적"
- Block 59 TF 실무 책임자 임시 직책 → 자동 해제 2029-07
- Block 51 조교수 4축 공식 운영권 → 단일 직책 복귀
- Block 23-24 단독 집도 유예 → structural_resolution (R10'", I-51-60-D 처리)
- Block 50 조교수 후보 등재 6:3 → **Block 61 진료과장 후보 등재가 Block 50의 ARC-07 확장 구조임을 내부 서술**

**필수 foreshadow 신규 seed**:
- Block 62 이상훈 재등장 예고 (타 대학 포지션 경쟁 구도 암시 — 단 이상훈 직접 언급 금지, "학계 내 동일 포지션 경쟁자 축"의 일반 언급 수준)
- Block 63 최종 케이스 의뢰 예고 (병원 내부 고난도 수술 의뢰 파이프라인 언급)

#### 4.2.6 한미정 (R7'" 후진 배치)

- Block 61에서 한미정 직접 등장 금지 (FS-36 2차 기사 5월 발행 시점이 Block 61-62와 겹치나, "언론 축 활용 후보" 프레임 리스크)
- 간접 언급만 허용: "2차 기사가 예정대로 익명화 원칙 유지됐다" 수준 1문장

#### 4.2.7 회귀 자산 운용 (R3'" 선제 설계)

- Block 61 시점에서 회귀 자산은 "배경 자원"으로만 서술, 본 블록의 결정타 아님
- Block 64-65 회귀 자산 무력화 장면을 위한 **"현재의 판단"과 "전생 기억"의 구분선 인식**이 Block 61 내부 독백에 1-2문장 수준으로 잠복
- 규모 과시 금지: "3만 건의 손"은 ARC-03 Block 22에서 이미 소진, Block 61에서 재사용 금지

### 4.3 금지 항목 (work_guard + 3-pass audit 피드백)

- ❌ "국내 최연소 진료과장" / "최연소 후보" 등 규모 과시 표현
- ❌ "전생에서 과장으로 퇴직한 자리" 차트 노트 기재 (**내부 독백 1회 한정, 공식 기록 0**)
- ❌ 박정민 재등장, 이상훈 직접 언급
- ❌ 나경태 직접 등장 (간접 언급 허용: "병원장 라인은 후보 추천 절차에 직접 개입하지 않는다")
- ❌ 권혁수 방문·서신 재소환 (Block 61 범위 밖, ARC-07 학회 축은 Block 67 이후)
- ❌ 단독 집도 유예 FS-07/FS-10 재소환 (structural_resolution 완료)
- ❌ 감동 의사물 / 내부 고발 미담 / 환자 사연 감정 축
- ❌ "실권" 규모 표현 (실질 결정권 축으로만 서술)
- ❌ 10블록 일괄 생성 사고 (Block 61 단독, 다음은 Block 62 새 오더)

### 4.4 block_cider 계약 (§0G 실질 기준)

Block 61 same-block receipt 요구사항:
- **receipt_type 후보**: `권한/접근권 이동` (후보 등재 공식 서류) 또는 `명시적 다음 관문 입장권` (선임 심사 일정)
- **receipt_line 필수**: "본 블록 안에서 이미 지급된 영수증" 1문장 이상
- **pain_only_exit = false** (후보 등재 자체가 가시 성과)
- 단, schema 층 `genre_ext.block_cider` 필드 탑재는 I-02 schema debt scope (별도 backfill) — 본 블록도 기존 관행 유지 (Blocks 1-60 byte-equal invariant 연속)

---

## 5. Block 61 사전 선언 프로토콜 (harness §3.3 + 3-pass audit P3.4.4)

Block 61 생성 **전** 8항목 선언:

1. **이전 배치와 capital 연속성**: Block 60 ARC-06 exit_function 3축 달성 → Block 61 조교수 4축 단일 직책 복귀 + 진료과장 후보 등재 (서열 축 전진 1회 예정)
2. **이번 배치 NPC 변동**: 
   - 박정민: 퇴장 확정 (미등장)
   - 이상훈: Block 62 예정 (미등장)
   - 한미정: 간접 언급만 (FS-36 2차 기사 익명화 확인 1문장)
   - 권혁수: 미등장
   - 강태준: 미등장 (Block 68 완전 payoff 예정)
   - 조영채: 자동 해제 회신 서면 + 후보 추천 라인 (등장)
   - **임상 과장진 경쟁 후보 1-2인**: 신규 등장
3. **이번 배치 deal_type**: 진료과장 후보 등재 공식 절차 기록 (후보 추천 서면 + 외과 교수회 내규 경유)
4. **이번 배치 복선/회수**: 
   - FS-07/FS-10 structural_resolution 주석 (I-51-60-D 처리)
   - FS-36 2차 기사 간접 언급 (후진 배치 유지)
   - 신규 seed: Block 62 이상훈 재등장 + Block 63 최종 케이스 의뢰 예고
5. **이번 배치 emotional_beat**: candidate_registration (tension 6)
6. **약점 차별화 증명**: ARC-07 신규 weakness "진료과장 선임 기준 가중치 경쟁 구조 기존 관행 편향" — ARC-06 10+종 재사용 금지
7. **opponent 교체 증명**: "직전 배치는 박정민 5회 + 나경태 3회 간접. 이번 배치는 임상 과장진 경쟁 후보 1-2인 신규, 나경태 간접 언급만, 박정민 0회, 이상훈 0회(Block 62 예정)"
8. **회귀물 함정 자가 점검**: Block 64-65 회귀 자산 무력화 구조 설계 의식 유지, Block 61 내부 독백에 "현재의 판단 vs 전생 기억" 구분선 1-2문장 잠복

---

## 6. Block 61 수용 조건 (PASS 기준)

생산 직후 다음 7항목 전수 통과 시 Block 61 수용:

- [ ] Phase0 ARC-07 slot 61 title/function 정확 구현
- [ ] 후보 근거 3축(수술 실적/M&M/교육 재편) 전부 본문 편입
- [ ] work_guard forbidden_flattenings 10항목 0건
- [ ] 규모 과시 표현 0 ("최연소", "최고", "독보적" 등)
- [ ] 박정민/이상훈/권혁수/한미정 직접 등장 0
- [ ] same-block receipt 실질 지급 (권한 이동 또는 관문 입장권)
- [ ] tension 6, authority delta +2 (±0.5 허용)

**FAIL 조건**: 1항목이라도 위반 시 즉시 Block 61만 재생성 (harness §1.4 step 12)

---

## 7. Block 61 이후 진행 순서

1. **Block 61 단독 생산 + 수용 점검** (이 handoff 기준)
2. **Block 61 수동 감리 메모** 작성 (harness §1.4 step 13)
3. **새 오더 대기** — 자동 연속 생산 disabled, Block 62 `이상훈의 도전`은 별도 오더
4. **ARC-07 3블록 안전 배치** (61-62-63): 3-pass audit P3.4.6 권장 — 각 블록 단독 감리 후 다음
5. **Block 64-65 특별 관리**: 회귀물 함정 핵심 지점, 각각 단독 감리 필수 (R3'")
6. **Block 66 quiet 이후** Block 67-70 auto-run 5블록 허용 (stable 구간)
7. **Block 70 완료 시** 10-block self-audit (Blocks 61-70, ARC-07 exit)

---

## 8. 본 handoff의 SSOT 우선순위

1. `docs/2026-04-09/hoegui_surgeon_block_51_60_self_audit.md` §P3.4 Next 10 Focus (최상위)
2. `treatments/phase0/hoegui_surgeon_phase0_design.json` ARC-07 block_slots (Phase0 원본)
3. `work_guards/12_hoegui_surgeon.yaml` custom_rules + forbidden_flattenings
4. `docs/blockguide/treatment-production-harness-v2.md` §0D + §0G + §1.1C + §1.5
5. 본 handoff doc (실행 설계 층)

충돌 시 상위 SSOT 우선. 본 handoff와 Phase0가 충돌하면 Phase0 원본이 우선.
