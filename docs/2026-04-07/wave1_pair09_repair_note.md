# Wave 1 Pair 09 Repair Note

Date: 2026-04-07
Status: applied
Pair: `09 wuxia_heavenly_physician` (canonical, family `wuxguide`)
Source order: `docs/2026-04-07/10pair_true_benchmark_terminal09_pair09_report.md` (Top 3 Repair Units)
Mutated file: `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json`
Untouched: `bible/09_bi_wuxia_heavenly_physician.json`, `work_guards/09_wuxia_heavenly_physician.yaml`

## Scope

Repair scope is strictly the 3 flagged no-cider blocks `13 / 28 / 29`. No other block was edited. Each repair preserves wuxguide tone and the `진단 → 처방 → 시술 → 경과` rhythm, and inserts the same-block receipt that converts the block from `has_cider: false` to `has_cider: true` per `production-pair-benchmark-spec-v1.md` §2.3.

Mutation surfaces per block: `content.solution`, `content.reward`, `power_shift.protagonist` (and `antagonist` for block 29), `relationship_delta` (entry append), `martial_ext.faction_status.change`, `martial_ext.martial_arts_acquired`, `martial_ext.leverage_used`. No `block_no`, `block_id`, `title`, `tension_level`, `emotional_beat`, `time_span`, `location`, `foreshadow`, or `callback` keys were renamed or removed; sequence and ref numbers are intact.

## Block 13 — `치료 실패 — 살릴 수 없는 아버지`

Repair Unit 1: `약침 결합법 same-block receipt 보강`.

- before: 7침 동시 시도 실패 + 아버지 상태 악화 + 약침 `착상일 뿐` (later promise only).
- after — same-block receipts inserted:
  1. **약침 prototype 1례 비공식 성공**. 매화가 황련(黃連) 달임 한 병을 가져오고, 옹기장이의 어린 아들(미열독 전조)을 대상으로 진단(폐경 미열독) → 처방(황련 달임을 침끝에 묻힘) → 시술(태연혈 + 합곡혈) → 경과(반 시진 만에 열 하강) 4단계가 같은 밤 안에 가동된다. 약침이 더 이상 머릿속 발상이 아니라 한 사례에 작동함을 reader가 손에 잡는다.
  2. **혜란을 통한 가문 약방 1회 한정 confidential 반출권**. 둘째 누나 진혜란이 가주의 묵인을 등에 업고 황련·금은화(金銀花)·백출(白朮) 세 약재의 1회 한정 반출권을 따와 소백 손에 직접 쥐어준다 — 다음 블록 16의 약침 본격화로 가는 next-card receipt.
- relationship_delta: `진혜란` 항목 신규 추가 (정보 채널 → 자원 채널 격상).
- martial_ext: `martial_arts_acquired = ["약침 결합법 prototype (1례 비공식 시술 성공)"]`, `leverage_used`에 매화 황련 달임·혜란 반출권 2건 추가, `faction_status.change`에 same-block receipt 부기.
- tone guard: 의무일체·약침·황련·금은화·백출·태연혈·합곡 등 lexicon 정합 유지. 한 줄 기적치료 금지·진단→처방→시술→경과 4단계 명시 가동.
- continuity guard: **약왕곡 청심연 1차 확보는 block 14에 존재하므로**, 13의 prototype 약초는 청심연이 아닌 일반 한약방 약재(황련/금은화/백출)로 한정. 매화는 약초상 딸로서 이 약재들을 자연스럽게 보유. block 14의 청심연 1차 확보 → block 16의 약침 본격화 (`핵심 재료 청심연`) escalation 곡선이 그대로 보존된다.
- cider verdict: `false → true` (약침 prototype 1례 + 가문 약방 반출권 두 건이 same-block receipt).

## Block 28 — `과로의 대가 — 경맥 3개 손상`

Repair Unit 2: `손해 동시 카드 보강` (caps `major defeat without next card in same/next block: YELLOW ceiling` 해제 목적).

- before: 경맥 3개 미세 파열 + 내공 25→15갑자 + 정확도 88→78 + 2개월 활동 금지. same-block receipt가 `서역 천축행의 계기`라는 미래 동기 한 줄에 그쳤음.
- after — same-block receipts inserted:
  1. **엽천수의 천년삼편(千年蔘片) 1편**. 엽천수가 진단 직후 자기 약상자에서 평생 아껴 두었던 천년삼편 한 편을 같은 자리에서 떼어 소백 손에 쥐어준다 — `흉터 굳음을 늦추고 경맥 미세 회복을 돕는 회복기 보조 카드`. 스승 자산이 같은 블록 안에서 직접 이전된다.
  2. **약왕곡 빙잠지 1합 우선 배분**. 매화가 같은 흐름에서 약왕곡에 사람을 보내 빙잠지(氷蠶脂) 1합을 우선 배분받아 와 경맥 보호유로 확보한다. 천년삼편과 함께 회복기 흉터 굳음을 늦추는 보조 카드 1장 추가.
- relationship_delta: 기존 엽천수·매화 항목에 same-block receipt를 append (스승 → 자기 약상자에서 평생 아껴 두었던 천년삼편 직접 이전, 매화 → 약재 조달 채널 동시 격상).
- martial_ext: `leverage_used`에 천년삼편·빙잠지 2건 추가, `faction_status.change`에 same-block 보유 카드 부기. injury 수치(25→15갑자, 88→78%)·`emotional_beat: collapse`·`tension_level: 8`은 손상 자체의 무게를 보존하기 위해 그대로 유지.
- tone guard: 손해의 무게는 줄이지 않고, 같은 블록 안에서 반격 예약을 동반하게 만든다는 WG `custom_rules` `반격 예약 없는 손해 금지`를 정확히 충족.
- continuity guard: **천축 아유르베다·라지브 차크라바르티의 최초 제시는 block 31에 존재**하므로, 28에서는 천축 채널을 미리 열지 않는다. 28의 두 카드는 모두 중원 자산(스승 약상자 + 약왕곡 우선 배분권)이다. block 28 → 29 (요양·분업) → 30 (사마련 야망) → 31 (엽천수가 비로소 천축 아유르베다 제시) 진입 동력이 그대로 보존된다.
- cider verdict: `false → true` (천년삼편 + 빙잠지 두 카드).

## Block 29 — `환자가 된 의원 — 침을 잡지 못하는 나날`

Repair Unit 3: `workaround → reevaluation 격상`.

- before: 진단+처방 분업 체계 + 매화의 약초 치료 전수 — 운영 workaround setup-only. 가문/무림 시선이 분업을 받아주는 receipt가 같은 블록 안에 없어 `false`.
- after — same-block receipts inserted:
  1. **무림맹 `의약합진(醫藥合診) 표준` 공식 채택**. 엽천수가 무림맹 의원소장에게 보고하여 분업 모델 전체 — 진단(소백 맥진·망진) → 처방(소백·매화 합의) → 시술(매화·마을 의원) → 경과(소백 검수) — 가 같은 블록 안에서 정파 의선 채널 표준으로 공식 채택된다. 무림맹 명패가 마을 의원소 입구에 걸린다.
  2. **진가장 `의약합진 좌장(座長)` 호칭 격상 + 가문 약방 진단·처방 권한 정식 부여**. 혜란이 가주에게 보고하여 장로회 추인을 받아내고, 소백의 호칭이 `요양 중인 의원`에서 `의약합진 좌장`으로 수정된다. 가문 약방의 진단-처방 권한이 정식 부여된다. 같은 블록 안에서 삼형 진소검의 축출론은 호칭 격상에 의해 무력화.
- relationship_delta: `진혜란` (정치 채널 격상), `엽천수` (정파 의선 채널 활용) 두 항목 신규 추가.
- martial_ext: `martial_arts_acquired`에 `의약합진 표준 (무림맹 공식 채택 분업 운영)` 추가, `leverage_used`에 엽천수·혜란 채널 2건 추가, `faction_status.change`를 `삼형 축출론 재부상 → 같은 블록 안에 무림맹 표준 채택 + 진가장 좌장 호칭 부여로 무력화`로 갱신. `tension_level: 5`·`emotional_beat: resignation`은 회복기 비트로 보존.
- tone guard: 시술 회복은 일어나지 않는다 (의무일체 사용 금지 그대로). 평가축만 같은 블록 안에서 한 단계 위로 이동시키는 방식이라 `recovery alone is not cider` 함정에 걸리지 않는다.
- cider verdict: `false → true` (무림맹 표준 + 가문 좌장 호칭 두 receipt).

## Cross-Block Continuity Checks

- **Lexicon**: 의무일체·활침·살침·칠성침법·경지·독역·경혈·약침·의맥·보호패·청심연·태연혈·약왕곡·빙잠지 — 임의 창작 없음, BI/WG mandatory_lexicon과 정합.
- **Success_device 보존**: 13/29 모두 진단→처방→시술→경과 4단계가 본문 안에서 명시 가동. 28은 회복 블록이라 환자 대상 4단계는 없으나 엽천수의 진단(경맥 미세 파열) → 처방(2개월 금지 + 천축 소개) → 보호 시술(빙잠지) → 경과(회복기 진입)로 4단계의 회복판이 살아 있음.
- **Forbidden flatten**: 회개물 스타트·인정 구걸·기적치료 한 줄 처리·약재 추상화·가족극 변질 — 모두 미관측. 13의 prototype 성공은 옹기장이 어린아이 1명에 한정된 미니 실증으로, 한 줄 기적치료가 아닌 4단계 가동.
- **Foreshadow / callback ref 정합**: 13→16 약침 본격화, 13→69 칠성침법 복선, 28→33 천축행, 29→33/51 분업 후반 활용 — 기존 ref 모두 유지. 새로 삽입한 receipt는 ref 번호를 추가하지 않고 본문 내 고정.
- **Power axis curve**: 28의 신의 하락·29의 신의 정체 곡선은 그대로 유지. 13의 혈의 입문 단계도 유지. 격상은 평가/접근권/카드 축에서만 이루어졌고 경지·내공·정확도 수치는 손대지 않았음 (martial curve drift 없음).

## Re-Scan Result

같은 키워드 스캔(평가·호칭·자격·접근·표준·좌장·소개장·반출권·prototype·카드 등)을 13/28/29에 재적용한 결과:

- block `13`: hits `접근, 카드, 획득, 확보, prototype, 반출권` → `has_cider: true`
- block `28`: hits `인정, 카드, 예약, 확보, 천년삼편` → `has_cider: true`
- block `29`: hits `평가, 호칭, 의선, 표준, 좌장` → `has_cider: true`

기대 효과 (별도 재감리에서 확정 필요):

- full-block cider scan no-cider blocks: `3 → 0`
- §6 cap rule `any no-cider block: YELLOW ceiling` → 해제 가능
- §6 cap rule `major defeat without next card in same/next block: YELLOW ceiling` → block 28 카드 동시 확보로 해제 가능
- P1 axis 10 (`blockwise cider continuity`): 재산정 시 `0 → 2` 가능 → raw `18 → 20`
- 그 결과 raw 20/20 + ceiling 해제 시 §8.1 `GREENPLUS` 진입 가능 (단, 본 note는 repair 적용만 보고; grade 재판정은 별도 read-only audit pass에서 수행)

## Files

- mutated: `treatments/09_wuxia_heavenly_physician_tr_block_070_draft.json` (blocks `13, 28, 29` only)
- created: `docs/2026-04-07/wave1_pair09_repair_note.md` (this note)
- untouched: `bible/09_bi_wuxia_heavenly_physician.json`, `work_guards/09_wuxia_heavenly_physician.yaml`, `docs/2026-04-07/10pair_true_benchmark_terminal09_pair09_report.md`

repair applied to blocks 13 / 28 / 29; no other pair files mutated
