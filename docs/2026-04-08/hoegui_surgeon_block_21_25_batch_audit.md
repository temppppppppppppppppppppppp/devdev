# hoegui_surgeon — Block 21-25 Batch Audit Memo

Date: 2026-04-08
Scope: ARC-03 opening batch (Block 21-25) 생산 직후 자체 감리
Work ID: `hoegui_surgeon`
Batch: 5-block cap 소진 (Block 21-25)
Basis:
- `treatments/hoegui_surgeon_tr_block_020_draft.json` (Blocks 21-25)
- `docs/2026-04-08/hoegui_surgeon_live_status.md`
- `treatments/phase0/hoegui_surgeon_phase0_design.json` (ARC-03 slots + constraints)
- `work_guards/12_hoegui_surgeon.yaml`
- `docs/blockguide/treatment-production-harness-v2.md` §1.1B 5-block cap, §1.1C 10-block audit

## 1. Audit Scope

- primary: Block 21, 22, 23, 24, 25
- continuity anchor: Block 20 말미 (ARC-02 종료 상태) → Block 21 시작 상태
- forward anchor: Block 25 말미 (응급 집도 OR door) → Block 26 착수 전제
- out-of-scope: Block 1-20 본문(보존 검증은 배치 쓰기 시 byte-equal로 확인 완료), Block 26+ 생산, Phase0 본문, work_guard 본문, BI 일체

## 2. Continuity Check

- Block 20 `authority_after`: `타과 협진 호출권을 가진 R1 (이 호 종결)`
- Block 21 `authority_before`: `타과 협진 호출권을 가진 R1`
- 의미 동치. Block 20의 `(이 호 종결)` 접미는 ARC-02 closure 주석이고 authority 상태는 동일. 연결부 통과.
- Block 21 context 문단이 "사전 설계권으로 조영채 과장이 집도한 고난도 간절제 수술이 성공하고, 소화기내과 김수현의 첫 타과 협진 호출까지 회수되며 ARC-02가 종결된 직후"로 명시 카르리 오버.
- Block 21 callback `ARC-02-exit` (carry_over) 기록됨.
- authority chain through-line:
  - 21: `타과 협진 호출권` → `R1 최초 단독 집도 1회 문서 기록 획득` (+3)
  - 22: `R1 최초 단독 집도 1회 문서 기록 획득` → `단독 집도 성공 데이터를 서류 3장에 남긴 R1` (+3)
  - 23: `단독 집도 성공 데이터를 서류 3장에 남긴 R1` → `단독 집도권 잠정 유예, 집도 기록 영구 보존, 나머지 권한 체인 분리 유지` (−2)
  - 24: `단독 집도권 잠정 유예, 나머지 권한 체인 분리 유지` → `집도의 칸 한 칸 후퇴, 권한 체인 5개 토큰 문서 고정` (−1)
  - 25: `집도의 칸 한 칸 후퇴, 권한 체인 5개 토큰 문서 고정` → `응급 집도 엔트리 제도적 근거 문서 6종 선행 확보 (메스 진입 직전)` (+0.5)
- 각 블록의 `authority_before`가 직전 블록의 `authority_after`와 문장 동치 또는 자연 축약으로 이어짐. 체인 끊김 없음.
- tension curve: 7-7-9-7-10. 긴장의 2차 피크(23)와 3차 피크(25) 사이 24가 한 박 낮춰 주는 휴식/후퇴 리듬 정상.
- Block 25 말미 hard stop 라인: "서동혁이 스크럽을 마치고 OR 앞에 선다. 이 블록은 메스를 잡는 바로 그 지점에서 정지한다 — 성공 여부, 출혈 통제, 심사위 논거 무력화는 이 블록의 것이 아니다." → OR door stop 명문 확인.
- stakes 문장도 "수술 결과는 이 블록의 평가 대상이 아니다. 다음 블록(Block 26)에서의 결과가…"로 다음 게이트 이양 명시.

Continuity check: **OK**

## 3. Harness Compliance

- 5-block cap(harness §1.1B): 5블록 정확히 생산, cap 소진. 현 턴 신규 블록 작성 금지 상태 진입. 준수.
- 10-block self-audit(harness §1.1C): 트리거는 Block 30 완료 시점. 현재 Block 25이므로 미도래. 본 감리는 5-block batch audit이며 10-block self-audit과는 별도.
- UTF-8: 파일 파싱 정상. 인코딩 오염 없음.
- 필드 구조(블록별): block_id / block_no / title / content{context,event_villain,solution,reward} / stakes / power_shift / relationship_delta / foreshadow / callback / emotional_beat / tension_level / pov_character / location / time_span / genre_ext / regression_ext — 5블록 모두 일관.
- 금지 규칙:
  - "블록 21+ 작성 금지" 이전 턴 명령은 이번 배치 생산 자체의 명령이 아니라 이전 root_admit 턴의 hard stop이었음. 본 tr_continue 턴에서는 21-25가 허용 스코프였고 준수됨.
  - 자동 연속 생산 금지 규칙(다음 턴부터): 본 턴은 감리 전용이므로 해당 없음.
- 주의(Tier B migration debt, 본 감리 스코프 밖 지적):
  - canonical `genre_ext.block_cider.*` 필드가 5블록 전부 미탑재.
  - canonical `capital_before/after/delta` 대신 work-local `authority_before/after/delta` 사용.
  - 이는 Blocks 1-20이 동일 관행을 가진 채 root_admit된 상태에서의 연속성 유지 선택이며, 본 턴의 쓰기 스코프(Block 21-25 생산)와 "Blocks 1-20 재작성 금지" 지시에 따라 의도적으로 유지됨.
  - production-pair-schema-standard-v1.md §7.1 Tier B family-standard enrichment에 해당하는 `block_cider.*` 서브셋이 영구 누락될 경우, 향후 BI 게이트 또는 promotion-target 평가 시점에 debt로 잡힐 수 있음. 일괄 백필은 "Blocks 1-70 스코프 전체 수정" 단일 오더로 별도 처리 권장.

Harness compliance: **OK (Tier B debt 지적 1건, 차기 스코프 이관)**

## 4. Phase0 Alignment

- Block 21 title `단독 집도` = Phase0 ARC-03 slot 21 `단독 집도` ✓
- Block 22 title `30,000건의 손` = Phase0 slot 22 ✓
- Block 23 title `심사위` = Phase0 slot 23 ✓
- Block 24 title `집도 제한` = Phase0 slot 24 ✓
- Block 25 title `응급` = Phase0 slot 25 ✓
- Phase0 `defeat_blocks: [24]` → Block 24 `emotional_beat.type: strategic_retreat`, power_shift.protagonist가 후퇴 한정, authority_delta −1. defeat 기능 충실. 과장 없음(5개 권한 토큰 분리 유지로 구조적 후퇴 한정).
- Phase0 `quiet_blocks: [26]` → Block 26은 본 감리 스코프 밖. Phase0 slot 26 `증명` 내용(응급 수술 성공 + 사후 보고 + 심사위 논거 무력화)은 다음 턴 생산 시점 판단.
- Phase0 ARC-03 `emotion_curve`: "단독 집도 기회 → 성공 → 강태준 심사위 공격 → 응급 적중으로 역전 → 학회 데뷔 → stay method 유혹 테스트" — Block 21-25 segment가 "기회 → 성공 → 공격 → (후퇴) → 응급 진입"까지 커버. Phase0 곡선 준수.
- Phase0 `time_window`: "2026년 10월~2027년 2월" — Block 21~25는 2026년 9월 말~11월 초. Phase0 창보다 약 2주 빨리 시작했지만 수용 가능 범위(ARC-02 종료 직후의 자연 연결). Phase0 타임창 엄수 요건은 harness에 없음.
- Phase0 `front_sectors: [고난도 간절제, 응급 수술]` — 커버 ✓.
- Phase0 `main_opponents: [강태준, 이상훈]` — 이번 배치는 강태준 한 축. 이상훈은 Block 28부터 Phase0가 지정했으므로 정상.
- Phase0 `new_npcs: [이상훈, 윤지영]` — 본 배치 구간(21-25)에 Phase0 신규 NPC 등장 안 함. 정상.

Phase0 alignment: **OK**

## 5. Work Guard Check

- `role_fit_constraints: 강태준 캐리커처 금지`
  - Block 21: 회의실 부재(다른 컨퍼런스) — 회피가 아니라 물리적 부재로 합리화.
  - Block 23: 논거가 "결과 부정 아님, 절차 적정성 문제, 법적 책임 소재, 각 과 수련 기준 붕괴 위험, 선례 일반화" — 경험 500건 기준의 합리 판단자 선 유지. 소위 내 다른 교수 2명이 "근거 있음"으로 호응 — 이 논거가 객관적으로 유효함을 보여주는 장치. 캐리커처 없음.
  - Block 24: 지연 운용 = "정식 심사를 급하게 올리지 않는다" — 합법적 제도 운용 방식. 악의적 서사 없음.
  - Block 25: 전원 호출 문자에 응답 불가로 로그에 이름이 남음 — 물리적 부재가 근거, 의도적 방해 아님.
- `role_fit_constraints: 조력자 감화 금지 (조영채/정소연)`
  - Block 21: 조영채가 R1 단독 집도를 밀어붙이는 근거는 "계산 기반" 연속(ARC-02 Block 18의 "내가 지키는 건 내 판단이야" 연장). 감화 근거 없음. Block 22에서 "이거 처음 집도 맞아?"는 확인 질문, 감탄 아님.
- `mandatory_lexicon`: 차트 기록, 판독, 합병증 패턴, 변이 혈관, 접근법, 집도권, 1st assist, M&M 회의록, 회의록, 직보선, 사전 설계권, 협진 호출, 케이스 배정, 수련 체계 — 5블록 전체에 밀도 있게 등장. 준수.
- `forbidden_flattenings`:
  - 무보상 희생 미담 X ✓
  - 감동 의사물 X ✓ (환자 사연/가족 눈물 없음, 응급도 제도 근거 중심)
  - 환자 구조 자체가 첫 승리 X ✓ (Block 22 성공의 영수증은 "서류 3장의 객관 데이터", 환자 생명 구출 드라마 아님)
  - 의료 윤리 딜레마(살릴까 말까) X ✓
  - 자기연민/참회 X ✓
  - 능력 장광설 X ✓ (서동혁 발화는 "첫 단독 집도 맞습니다" 한 줄, "좌측으로 돌리면 박리 가능합니다" 급의 통제 한 줄 패턴 유지)
  - 규모 과시 X ✓ ("세계 최초/교과서 등재" 없음. "교수 평균보다 30% 빠르다"는 내부 비교 수치, 규모 과시 아님.)
  - 적대자 멍청한 악당 X ✓
  - 보상이 생존/칭찬/감사 수준 X ✓ (모든 reward가 문서/기록/제도 근거)
- `sacrifice_policy`:
  - Block 25 응급 집도 진입이 sacrifice에 해당. "책임을 선점하는 형태여야 한다" 요건 충족 — 6종 문서(직보선 통화, 가용 의사 호출 로그, 응급의료법 조문 기재, 당직 부원장 사전 고지, 보호자 응급 동의 프로토콜, OR 긴급 오픈 로그)를 메스 잡기 전에 선행 확보.
  - "희생 직후 권한 영수증 필수" 요건: 이번 블록 자체가 entry gate이므로 영수증은 "제도적 정당성 문서화" 형태로 블록 내 지급. 완전 권한 토큰 회수(집도권 복권 등)는 Block 26+의 응급 수술 성공 결과에 연동 예정.
- `custom_rules`:
  - "차트 기록이 먼저 맞았다는 사실이 권력의 원천" — Block 23에서 정확히 방어 자산으로 작동.
  - "서열은 그대로인데 실질적 결정권이 뒤집히는 구조" — Block 24에서 집도의 칸 후퇴 + 5개 권한 토큰 유지로 정확히 작동.
  - "반격 예약 없는 손해는 금지" — Block 23-24의 후퇴는 Block 25의 응급 진입(제도적 반격 무대)로 같은 배치 내에서 예약됨.
  - "회귀 기억은 예언이 아니라 3만 건 수술 경험의 패턴 데이터베이스" — Block 22 변이 혈관 우회, Block 25 간문부 손상 응급 — 모두 경험 기반, 미래 예지 없음.
  - "Arc 3 이전까지 규모 확대 금지" — 본 배치는 ARC-03 opening이므로 엄밀히는 적용 경계선. 실제 내용은 규모 과시가 아니라 제도적 공방. 준수.

Work guard check: **OK**

## 6. Foreshadow Status

- **FS-07** (Block 17 seed → Block 23 payoff)
  - callback type: `payoff`
  - chain: 위계 문제 → 사전 승인 규칙 → 발표 순서 조정 → 의국 안건 → 수련교육위 소위 → R1 단독 집도 잠정 유예
  - payoff 지점: Block 23 정확. 이번 배치의 FS-07 timing 요건 충족.
- **FS-02** (강태준 부교수 딜레마, Phase0 payoff 예정 Block 40)
  - Block 21: `escalation` 표시 (지도 실적이 서동혁에 의존하는 구조 한 칸 기움)
  - Block 23: `counter_turn` (일시적으로 딜레마 무게가 강태준 쪽으로 역류)
  - Phase0 Block 40 payoff까지의 곡선에 일관 기여. 모순 없음.
- **FS-09** (Block 21 seed → Block 22 partial_payoff)
  - seed: 조영채 과장의 커리어 얹음 구조
  - partial_payoff: Block 22 수술 성공 데이터로 과장 판단의 부분 정당화
  - 완전 payoff 미지: 과장의 커리어 리스크가 완전히 회수되는 장면은 아직 없음. Block 26+의 응급 성공 + 심사위 논거 무력화와 맞물리는 위치가 자연스러운 완결점.
- **FS-10** (Block 23 seed)
  - seed: 정식 심사까지 유예의 시한이 강태준 쪽 운용에 달려 있음
  - 대기 상태. Block 26+ 이후 정식 수련교육위 심사 장면에서 payoff 가능. 모순 없이 후속 배치로 이월.
- **FS-11** (Block 24 seed → Block 25 activation)
  - seed: 유예 사정 범위 바깥 권한 5개 문서 고정
  - activation: Block 25에서 응급의료법 상위 법령 근거로 "유예와 분리된 작동 영역" 개념이 실제 발동
  - 완전 payoff: Block 26+의 응급 수술 결과로 이 활성화가 반례 앵커가 되는 순간. 활성화와 완결 payoff 구분 명확.
- **FS-12** (Block 25 seed)
  - seed: 6종 문서가 반례 앵커로 작동할지 사고 조사 기록으로 작동할지는 수술 결과에 따라 갈림
  - Block 26의 수술 결과가 분기를 결정하는 구조. 모순 없이 후속 배치로 이월.
- **FS-08** (Block 20 seed, 김수현 협진 관계 → ARC-04 간이식)
  - 본 배치 범위 내 진행 없음. ARC-04 시점 대기. 정상.
- **FS-04** (Phase0 seed_block 27, 경험의 한계)
  - 아직 seed 전. 본 배치 범위 밖. 정상.

Foreshadow status: **정상, 이월 가능**

## 7. NPC Scope Check

- 신규 등장 NPC (본 배치에서 처음 이름 기재):
  - **정재훈** (마취과 펠로우, Block 22 도입 / Block 25 재등장) — 객관 데이터 기록자 + 응급 공동 증인. 서사 축 변경 아니고 기록 증거원 기능. Phase0 NPC 타임라인 오염 없음.
  - **김혜원** (수술 간호사, Block 22 도입 / Block 25 재등장) — 수술 간호 기록지 증거원. 기능 인물. 오염 없음.
  - **장훈석** (외과 당직 교수, Block 25 단발 등장) — "응답 불가 호출 로그" 역할. 물리적 부재 증거 제공 기능 인물. 오염 없음.
- Phase0 `new_npcs` ARC-03 지정: 이상훈, 윤지영 — 각각 Block 28, 37 등장 예정. 본 배치는 Phase0 지정 NPC보다 일찍 등장시키지 않았음. 정상.
- Phase0 `npc_timeline` 주요 9인의 `key_turning_points`와 본 배치 상호작용:
  - 강태준 Block 23: Phase0 정의 `block 23, 심사위를 통한 단독 집도 제한` — 본 배치 Block 23이 정확히 이 turning point에 부합.
  - 조영채: Phase0 정의된 turning points 외로 Block 21, 24, 25 등장. 하지만 Phase0 turning points는 "핵심 전환점"이지 "전체 등장"이 아님. 일상적 조력자 역할 범위. 오염 없음.
  - 한정우 Block 24: Phase0 정의 `block 20, 타과 협진 호출을 보며 태도 전환 시작` 이후 자연 연장. 오염 없음.
- Block 21에서 "한정우가 과장 앞에서 수련 규정을 꺼내려다 차단"된 장면은 한정우의 태도 전환 곡선을 역행시키지 않는다(그는 여전히 규정 수호자 본능이지만 과장이 차단). Phase0의 한정우 trajectory와 일관.

NPC scope check: **오염 없음, Phase0 보호**

## 8. Audit Result

**CONDITIONAL PASS**

- 본문 품질·연속성·Phase0 정합·work_guard 제약 전부 통과.
- "CONDITIONAL"의 근거는 아래 2건의 경미한 이슈가 발견되었고, 이는 본 턴에서 TR 본문 수정 금지 지시에 따라 메모 이관 처리하기 때문:
  1. `live_status.md` 문서가 여전히 Block 20 기준으로 기술됨(§2, §3, §4, §7). 실제 저장 경계는 Block 25. 문서-파일 불일치는 지적 사항이며 별도 스코프에서 동기화 필요.
  2. Tier B migration debt(block_cider / capital_*) 미탑재가 Block 21-25에서도 Blocks 1-20 관행을 따라 유지됨. 향후 BI 게이트 또는 promotion 평가 시점에 debt로 잡힐 수 있음. 일괄 백필은 별도 스코프.
- 중대한 하자(FS-07 mistiming, Block 24 과장, Block 25 OR door 위반, 강태준 캐리커처, 금지 플래트닝) 없음.

## 9. Issues Found

- **I-01** (minor, doc drift): `docs/2026-04-08/hoegui_surgeon_live_status.md`가 Block 20 경계 기준으로 기술되어 있으나 실제 TR 저장 경계는 Block 25. 섹션 1(operational state), 2(현재 artifacts의 saved boundary), 3(boundary rule), 4(next allowed tasks), 7(admission log)이 Block 25 현실과 어긋남. 모순 범위: 수치·서술 불일치만, 스키마 오류 아님.
- **I-02** (minor, schema debt): 본 배치 5블록이 canonical `genre_ext.block_cider.{has_cider,receipt_type,receipt_line,pain_only_exit}` 및 `capital_before/capital_after/capital_delta`를 탑재하지 않음. Blocks 1-20 관행 유지(authority_before/after/delta 사용). 본 배치 단독 수정 시 Block 20과 Block 21 사이의 스키마 분기가 생기므로 배치 단위 수정이 부적절. 일괄 백필 권장.
- **I-03** (micro, optional polish): Block 25 `regression_hint.slip_up`이 "R1이 6종 문서를 순차로 남기는 속도"를 지적. 이는 의도된 회귀 hint지만, "펠로우 레벨도 당황할 상황에서" 표현이 다소 해설 톤에 가까움. 본문 리듬에 영향 주지는 않음. 수정 선택 사항.
- **I-04** (micro, continuity string): Block 20 `authority_after` 끝의 `(이 호 종결)` 접미가 Block 21 `authority_before`에 전달되지 않음. 의미 동치이므로 문제 아님. 향후 자동 체인 검사 스크립트가 strict match를 요구할 경우 Block 21 쪽 문자열 한 줄 조정 가능. 현재 validation은 통과.

## 10. Fixes Deferred

| id | 수정 대상 | 권장 스코프 | 우선순위 |
|---|---|---|---|
| I-01 | `docs/2026-04-08/hoegui_surgeon_live_status.md` — §1,2,3,4,7 Block 25 경계 반영 | `status_sync` 별도 오더 (docs 단독 1파일) | 높음 (다음 오더 전 권장) |
| I-02 | Blocks 1-25 전체 `genre_ext.block_cider.*` + `capital_*` 백필 | `schema_backfill` 별도 오더 (TR 1파일, 전블록 구조 보강) | 낮음 (BI/promotion 시점 전) |
| I-03 | Block 25 `regression_hint.slip_up` 문구 다듬기 | `tr_polish` 별도 오더 (TR 단일 블록 micro patch) | 매우 낮음 (선택) |
| I-04 | Block 21 `authority_before` 접미 정렬 | 위 I-03과 함께 단일 패치 가능 | 매우 낮음 (선택) |

본 턴에서는 어떤 수정도 적용하지 않음. 본 감리의 쓰기 범위는 본 메모 파일 한 개로 한정.

## 11. Ready For Block 26

**Yes.**

- Block 21-25 생산 배치가 ARC-03 opening으로서 인과·긴장 곡선·FS payoff timing·defeat 블록 기능·OR door stop·work_guard 제약을 모두 통과.
- I-01~I-04 이슈는 Block 26 생산 개시를 직접 가로막지 않음.
  - I-01(doc drift)은 오퍼레이터/델리게이트 재시작 시의 혼동 위험이라 Block 26 오더 발행 전에 별도로 해결하는 것이 권장되지만, 오더 문면에 Block 25 경계가 명시되면 생산은 가능.
  - I-02(schema debt)는 Blocks 1-25 전체 연속 상태이므로 Block 26 하나만 canonical로 바꾸면 오히려 분기 악화. Block 26도 관행 유지 권장.
  - I-03, I-04는 선택 polish.
- Block 26은 Phase0 quiet_blocks[26] = `증명` — 응급 수술 성공 + 사후 보고 + 심사위 논거 무력화. Block 25의 OR door stop에서 자연 연결. FS-11 activation → 완전 payoff, FS-12 분기 결정, FS-09 완전 payoff 후보 지점.

## 12. Exact Next Order (권장)

1. **선행 권장**: `status_sync` 오더 (쓰기 스코프: `docs/2026-04-08/hoegui_surgeon_live_status.md` 1파일) — Block 25 경계로 §1,2,3,4,7 동기화.
2. **다음 생산 오더**: `tr_continue` 1-block envelope, 대상 Block 26 `증명`.
   - 쓰기 스코프: `treatments/hoegui_surgeon_tr_block_020_draft.json` 1파일
   - 읽기 스코프: 본 감리 메모 + live_status + Phase0 ARC-03 slot 26 + work_guard + Blocks 1-25 현재 저장본
   - hard stop:
     - Block 27 금지
     - BI 금지
     - 파일명 변경 금지
     - Blocks 1-25 재작성 금지
   - 필수 guardrail:
     - Phase0 quiet_blocks:[26] 지정 존중. 외적 충돌 피크보다 사후 보고/논거 무력화 중심으로.
     - Block 25 응급 집도 엔트리 6종 문서를 Block 26의 근거로 연결.
     - FS-11 완전 payoff (응급의료법 근거가 유예 반례 앵커로 확정).
     - FS-12 분기 결정 (수술 성공 = 반례 앵커, 수술 실패 = 사고 조사 기록). Phase0는 성공을 지정.
     - FS-09 완전 payoff 가능 지점.
     - 심사위 논거 "사실상 무력화" 수준이지 "공식 철회"가 아니어야 함 — Phase0 slot 26 표현 준수.
     - 강태준 캐리커처 금지 유지 (합리적 위계 수호자).
     - 감정 서술 아닌 문서·기록·제도 근거 receipt 유지.
     - 블록 1개만 작성 후 정지 → `_saved_block_boundary=26`, `_next_continuation_boundary=27`, next gate 보고.
3. **감리 재트리거**: Block 30 완료 시점에 harness §1.1C에 따른 10-block self-audit (Blocks 21-30 구간) 필수.

---

_이 문서의 쓰기 범위는 본 메모 파일 하나로 한정된다. TR 본문·Phase0·work_guard·live_status·harness 일체 미수정._
