# 10pair True Benchmark — Terminal 05 / Pair 05 Report

Date: 2026-04-07
Mode: read-only true benchmark audit
Scope: canonical pair `05` only

## 1. Pair Identity

- pair id: `05`
- slug: `failed_future_ceo_intern`
- family: `blockguide`
- BI: `bible/05_bi_failed_future_ceo_intern.json`
- TR: `treatments/05_failed_future_ceo_intern_tr_block_070_draft.json` (`_total_blocks: 70`, contiguous `Block 1` ~ `Block 70`)
- WG: `work_guards/05_failed_future_ceo_intern.yaml`
- canonical resolution: `docs/2026-04-07/01_10_canonical_pair_manifest.md` row `05`

## 2. Evidence Anchor Table

| Anchor | Source | Location | Extract |
| --- | --- | --- | --- |
| `one_line_truth` | WG | `work_identity.one_line_truth` | "파산의 모든 분기점을 기억하는 0권한 인턴이 결재선·KPI·예산 코드·이사회 표결을 한 칸씩 자기 관문으로 옮겨 한라테크를 다시 장악한다" |
| `mandatory_scene_engines` | WG | `work_identity.mandatory_scene_engines` | 인턴급 접점 우회 → 공개 성과 → 권한 이동 / 전생 기억 병목 선독 / 승리 직후 체감형 권한 보상 회수 |
| `evaluation_thresholds` | WG | `work_identity.protagonist_evaluation.evaluation_thresholds` | 3~6화 내 정태준 실명 호명 1회, 첫 승리 직후 정규직 전환+전략기획실 접근권, 큰 피해 뒤 즉시 다음 카드 |
| `custom_rules` (per-block reward list) | WG | `custom_rules[0]` | 매 블록 보상은 실명 인정·배석권·CC·TF·결재선 상승·인사 이동·스톡옵션/지분 중 하나의 체감형 권한 보상 |
| `custom_rules` (반격 예약) | WG | `custom_rules[3]` | 반격 예약 없는 손해는 금지 |
| `tracking_slots` | WG | `work_identity.tracking_slots` | 저평가→고평가 전환, 결재선·예산 코드 회수, 수혁 없이 못 움직이는 병목, 시총 15조→85조 |
| `forbidden_flattenings` | WG | `work_identity.forbidden_flattenings` | 회개물 스타트 / 자기연민 주조감정 / 적대자 캐리커처 / 전생 만능 예언 / 0권한 즉시 해결 금지 |
| `cider_point` 등가 (success_device) | TR `Block 3` `reward` | line 137 | "최준호 CC 라인 정식 진입. Lv1→Lv2 CC·발표권. … '다음 주 OJT 보고회에서 직접 5분 발표하라' 지시. 첫 사이다." |
| `protagonist_only_proof` 등가 | TR `Block 2` `solution`/`reward` | line 79~80 | KPI 산정식을 OJT 감상문 포맷으로 변환해 인사팀 평행 결재선 우회 → 김미선 비공식 검토 + 분기 KPI 회의 참관권 |
| `evaluation_thresholds` 회수 | TR `Block 9` `reward` | line 483 | "정태준 실명 호명 + 재정리 지시. Lv2→Lv3 임시 상신권. 정태준 직보 라인 근접·배석 기록 공식 등재." (BI 3~6화 임계 정확 적중) |
| `간판 권한 보상 4종` | TR `Block 10` `reward` | line 541 | 정규직 트랙 + 전략기획실 OJT + 정태준 등재 3회+ + KPI 정식 안건 작성자 권한 + Lv3→Lv4 + 개인 첫 3,000만 원 |

## 3. P0 Hard Gates

Anchors restricted to `TR blocks 2~6` for gates `1~4`. Block 1 used only as opening context. Block 7+ used only for downstream linkage in gate 5.

| # | Gate | Verdict | Anchor |
| --- | --- | --- | --- |
| 1 | first-block visible cider | PASS | `Block 2` reward — 김미선 분기 KPI 회의 **참관권** + Lv0→Lv1 자료작성권. `Block 3` reward — Lv1→Lv2 **CC라인+발표권**, 본문에 "첫 사이다" 명시. |
| 2 | protagonist-only proof | PASS | `Block 2` solution — "팀장 결재선 우회 → 인사팀 평행 상신" 구조는 전생 13년 CEO의 결재선 선독+0권한 인턴 제약을 동시에 충족해야만 성립. `Block 3` 직보 발표권은 전생 KPI 도면이 있어야만 인턴이 5분 안에 정렬 가능. WG `protagonist_weapon` 직접 발화. |
| 3 | evaluation revision | PASS | `Block 2` — 김미선 과장이 비공식 검토→공식 참관 의사 전환 (인사팀 권위자 재평가). `Block 3` — 최준호 차장이 직접 5분 발표를 지시 (전략기획실 차장급 재평가). 둘 다 BI `observer_tiers` 내. |
| 4 | visible reward token | PASS | `Block 2` 참관권 + `Block 3` CC라인 + 발표권 + Lv 1→2. 모두 spec 4.1 `blockguide` token 목록(name call, seat, CC, report line, TF, approval, ownership, entry ticket) 정확 일치. |
| 5 | block1→block2 gate linkage | PASS | `Block 2`의 김미선 인사팀 라인 → `Block 7` 해고 철회·정규직 전환 트랙 + 김미선 공식 지지자 전환 (line 365). `Block 3`의 최준호 CC → `Block 9` 정태준 실명 호명·임시 상신권 (line 483). 5의 reward(파벌 지도)가 6 이후 모든 우회 설계의 공급원으로 명시(line 311). 누락·역방향 backfill 없음. |
| 6 | BI/TR early conversion alignment | PASS | BI `mandatory_scene_engines` "인턴급 접점 → 공개 성과 → 권한 이동" 사이클이 `Block 1`(56층 동선 우회 확보) → `Block 2`(KPI 인사팀 평행 상신 + 참관권) → `Block 3`(최준호 CC + 5분 발표권, 본문 "첫 사이다" 명시)에서 한 사이클이 닫힘. BI `tracking_slots` "결재선·KPI·예산 코드 회수" 중 KPI축은 `Block 2`, 결재선/CC축은 `Block 3`에서 TR 1~3 내부에서 발화. opening innocence rule(4.3) 안전: 전생 파산은 정태준 외부 조작·구형 라인 관성으로 명기, 자초/태만 아님. |

P0 verdict: **6/6 PASS**. Opening innocence: clean. No gate cited block 1 or block 7+ as primary proof for gates 1~4.

## 4. Full-Block Cider Scan

Scan policy: a block scores `has_cider: true` only if its `reward` (or equivalent power_shift token) lands at least one item from WG `custom_rules[0]` — 실명 인정 / 배석권 / CC라인 / TF 자리 / 결재선 상승(Lv) / 인사 이동 / 스톡옵션·지분 — or an explicit blockguide token (name call, seat, approval, ownership, entry ticket). Watchpoint enforced: 생존·격려·관찰자 식별·정보 수집·내적 정리 단독은 cider로 인정하지 않음.

Totals:
- total TR blocks: **70**
- no-cider blocks: **32**
- exact no-cider block numbers: **1, 4, 5, 6, 8, 12, 13, 14, 15, 17, 18, 19, 24, 28, 29, 32, 33, 35, 36, 37, 38, 42, 44, 45, 46, 50, 55, 60, 63, 64, 66, 69**
- longest no-cider drought: **4 blocks** (`12~15`, then equaled by `35~38`)

Window summaries:

- **`1~10`** (NC: 1,4,5,6,8 → 5 NC): 오프닝 setup이 무거움. 첫 cider는 `Block 2` 참관권, 본문 명시 첫 사이다는 `Block 3`. `Block 4` 첫 defeat(시총 -5천억, 신뢰 씨앗 only), `Block 5` 박동훈 자산 등록(관계 식별만), `Block 6` quiet mapping. 회복은 `Block 7` 정규직 트랙 + `Block 9` 정태준 실명 + `Block 10` 4종 동시 발동으로 강하게 닫힘.
- **`11~20`** (NC: 12,13,14,15,17,18,19 → 7 NC): 본 페어 최약 구간. `12 한예린 첫 대면`, `13 계좌번호 확보`, `14 한예린 동맹(피로스)`, `15 정태준 파견 축소(방어)`로 4-블록 드라우트. 16에서 노정숙 등재·우선순위 가중치 설계권으로 잠시 회복 후 17~19(판단 기록부·박동훈 재분류·외부 회계법인이지만 "수혁 이름은 여전히 안 나감")로 다시 3-블록 드라우트. `Block 20` 오승재 퇴진+스톡옵션 8억으로 구간 봉합.
- **`21~30`** (NC: 24,28,29 → 3 NC): 가장 강한 구간. Lv5→Lv6, TF 실권, 노정숙 해석자, JV 협상권, 특허 5건, JV 파기, 독자 배터리 라인+해외법인 설립권, IPO 상정 — 7개 cider. `Block 24` CATT 데이터 수집, `Block 28` 한예린 의심 일시 전환, `Block 29` 결백 증명(피로스)만 NC.
- **`31~40`** (NC: 32,33,35,36,37,38 → 6 NC): 두 번째 약지대. `31` 이사 취임(Lv6→Lv7)과 `34` 국민연금 비공식 연대, `39` 정태준 채널 추적 조율권, `40` 장현우 복귀 + 미공개 특허 12건 접근권으로만 cider. 35~38 4-블록 드라우트(정태준 hint·빙의 공유·백기사 섭외 진행·R&D 위기 두 번째 defeat)는 longest drought tie.
- **`41~50`** (NC: 42,44,45,46,50 → 5 NC): payoff 폭발(`43` FS-05 사라 밀러 LP 폭로, `48` FS-06 박동훈 회수, `49` AI 칩 +10조)과 hint·defeat 블록의 교차. `42` 유언장 hint, `44` 첫 defeat(-2조), `45` 데자뷔 hint, `46` 장현우 신뢰 심화, `50` 정태준 hint 3차로 cider 사이 간격이 또 벌어짐.
- **`51~60`** (NC: 55,60 → 2 NC): 페어 최강 구간. FS-03(51), 뮌헨(52), APAC HQ(53), BIS 사전 통지권(54), FS-07 한예린(56), 독일 5년 독점(57), FS-01 정태준 정체(58), Lv8→Lv9 COO(59) — 8 cider. `55` 시총 -8조 피로스, `60` 명단·시나리오 준비만 NC.
- **`61~70`** (NC: 63,64,66,69 → 4 NC): finale. Lv9→Lv10 CEO 56층 입실(61), FS-02 유언장 회수(62), FS-08 전생 파산 폭로(65), 삼면 분열 가동(67), 정태준 무력화(68), 시총 85조 finale(70) — 6 cider. NC는 `63` 첫 defeat(이탈 임원 4명 역유출), `64` 삼면 연합 분석, `66` 두 번째 defeat(-8조), `69` 내적 정돈.

## 5. Active Cap Rules

- **§6 cap "any no-cider block: YELLOW ceiling"** — TRIGGERED (32 NC blocks).
- §6 cap "no-cider drought 6+: YELLOW ceiling" — not triggered (longest drought = 4).
- §6 cap "no first-block cider: YELLOW ceiling" — not triggered (Block 2/3 cider strong).
- Opening innocence rule (§4.3) — clean (전생 파산은 정태준 조작·외부 LP 신뢰 파괴 + 구형 라인 관성, 주인공 자초 아님).

## 6. P1 Score Table

| Axis | Score | Anchor |
| --- | --- | --- |
| protagonist innocence | 2 | `Block 1` 프롤로그가 외부 조작/구형 라인 관성을 명시. WG `forbidden_flattenings` "회개물 스타트" 차단 준수. |
| protagonist-only proof clarity | 2 | `Block 2` KPI 인사팀 평행 우회, `Block 3` 최준호 직보, `Block 9` 정태준 실명 — 모두 전생 13년 CEO 기억 + 0권한 인턴 제약 동시 필요. |
| evaluation revision visibility | 2 | `Block 2` 김미선, `Block 3` 최준호, `Block 9` 정태준, `Block 16` 노정숙, `Block 41` 부사장 — 등급별 재평가가 명시 호명 동반. |
| visible reward token strength | 2 | Lv0→Lv10 사다리 + CC, TF, 배석권, 스톡옵션 8억, 개인 지분 5,200억까지 토큰이 모두 구체. |
| block1→block2 linkage | 2 | `Block 2~3`의 reward가 `Block 7·9·10` 다음 게이트를 직접 연다. backfill 없음. |
| rational opposition | 2 | 정태준·오승재·사라 밀러·빅터 웨이가 모두 "이전 시대 정답을 믿은 사람" 프레임으로 합리화. WG `forbidden_flattenings` "적대자 무능 캐리커처화" 차단 준수. |
| domain truth density | 2 | 결재선·CC·KPI·예산 코드·LP 한도·BIS 사전 통지·SPC·이사회 표결 지분 31/28/9·시총 단계가 도면처럼 깔림. |
| repeatable loop clarity | 2 | proof → reevaluation → token → next gate 루프가 `Block 2·3·7·9·10·20·21·31·41·49·59·61·70`까지 사다리 형태로 반복. |
| BI amplification power | 2 | BI `mandatory_scene_engines` 3종이 전 블록에서 살아 있고, BI `tracking_slots` 4개가 TR 진행 사다리와 1:1 대응. |
| blockwise cider continuity | 0 | 32개 no-cider 블록(spec 5.0 표 정의: "one or more no-cider blocks" = 0점). |

**Total P1: 18 / 20** (continuity axis가 0인 채로 다른 9축은 모두 만점.)

## 7. Provisional Grade

**YELLOW (capped)**.

- raw P0/P1만 보면 GREEN/GREENPLUS 후보지만, §6 cap "any no-cider block: YELLOW ceiling"이 32회 발동.
- §3 등급 정의("full-block cider scan finds zero no-cider blocks")의 GREEN 조건 불성립.
- RED 강등 트리거 없음(P0 6/6 PASS, opening innocence 안전, 두 게이트 이상 fail 없음).

## 8. Top 3 Repair Units

(YELLOW이므로 alias note 대신 repair units 제시. full-wave surgery 금지: 각 repair는 해당 윈도 블록 내부 reward 한 줄 단위로 한정.)

1. **mid-game drought 12~15 + 17~19 보강**
   - target: 본 페어 최약 구간. 4-블록 + 3-블록 드라우트가 한 윈도에 겹쳐 GREEN 도달의 1차 차단막.
   - 처방: `Block 13`(오승재 송금 추적)에 "감사실 결재선 임시 등재 1건" 토큰 1줄, `Block 14`(한예린 동맹) 기존 "Lv4 유지"를 "한예린 신사업팀 배석권 1회"로 재설계, `Block 18`(박동훈 재분류)에 "보고선 통제권 1단" 추가, `Block 19`(외부 회계법인 가동) 마지막 줄에 "수혁 이름이 부속서 1행 등재" 1구를 추가해 "수혁 이름은 여전히 안 나감"을 깬다.
   - 비용: 4 줄. 본 윈도 NC 7→3 수렴 가능.

2. **35~38 4-블록 드라우트 분쇄**
   - target: 페어 longest drought tie. 정태준 정체 빌드업 구간이 길어져 독자 체감 정체.
   - 처방: `Block 36`(빙의 진실 한예린 공유)에 "한예린 명의 내부 메모 한 행 = 수혁 분석권 공식 인정" 한 줄, `Block 37`(백기사 섭외)에 "이재민 채널을 수혁 명의 사외 자문 등재"로 인사 라인 토큰 1개. `35`와 `38`은 hint·defeat의 본래 기능을 유지하되 "반격 예약 카드 1장"을 reward 끝줄에 명시(custom_rules[3] "반격 예약 없는 손해는 금지" 직접 호환).
   - 비용: 2 줄 + 2 단서. 본 윈도 NC 6→3 수렴 가능.

3. **defeat·피로스 블록 9개의 즉시 회수 토큰 의무화**
   - target: `4, 14, 33, 38, 44, 47, 55, 63, 66`. 손해는 합리적이지만 BI `evaluation_thresholds` "큰 피해 뒤 즉시 다음 카드 확보"와 custom_rules[3] "반격 예약 없는 손해는 금지"의 텍스트 발화가 reward 라인에 명시되지 않는 경우가 다수.
   - 처방: 각 defeat 블록 reward 끝줄에 "다음 블록 진입 전 즉시 회수 카드 1장"을 명시(예: `Block 4` "최준호 메일함 내 증거 예금", `Block 33` "국민연금 라인 비공식 호출권 예약", `Block 55` "BIS 채널 사전 통지권 자기 명의 등재"). 이미 hint·동맹은 있으므로 텍스트 1줄로 토큰화만 하면 된다.
   - 비용: 9 줄. 잔여 NC를 추가로 5개 가량 절감, 두 번째 cap rule(6+ drought) 안전 마진 확보.

상기 3개 repair만으로 NC 32 → 약 14~17 수렴 추정. 0 수렴(GREEN 진입)은 추가 micro-pass 1회 필요.

## 9. Concise Rationale

`failed_future_ceo_intern`은 P0 6 게이트와 P1 9개 축이 거의 만점인 견고한 production pair다. `Block 2~3`이 BI `mandatory_scene_engines` "인턴급 접점 → 공개 성과 → 권한 이동" 사이클을 텍스트 그대로 작동시키고, `Block 9~10`이 BI `evaluation_thresholds` "3~6화 내 정태준 실명 호명"을 정확히 적중시킨다. 도메인 토큰(결재선·CC·TF·KPI·BIS·LP·이사회 지분)은 추상이 아니라 실수·코드로 깔리며 적대자 4인은 모두 합리화되어 forbidden_flattenings를 침범하지 않는다.

그러나 70블록 중 32블록이 no-cider로 잡힌다. 원인은 구조적 결함이 아니라 (a) defeat·피로스 블록이 손실 묘사 후 즉시 회수 토큰을 reward 행에 명시하지 않는 습관, (b) hint·정보 수집·관계 식별 quiet 블록이 다음 cider로 이어지는 receipt를 reward 행이 아니라 power_shift·foreshadow 행으로만 흘려보내는 패턴 — 두 가지다. 이 둘은 본 페어의 cider continuity 정의("같은 블록 안에서 독자가 셀 수 있는 토큰") 기준을 비껴간다. watchpoint("intern survival, praise, or probation extension alone does not count")를 강하게 적용한 결과이며, 보수적 관점에서는 일부 NC 판정이 1~2개 흔들릴 수 있지만 그 경우에도 NC 총수가 30 미만으로 떨어지지 않아 §6 "any no-cider block" cap이 그대로 발동한다.

따라서 raw 성능은 GREENPLUS 후보지만 spec 룰북에 따라 **YELLOW (capped)** 로 묶인다. cap을 푸는 길은 새 사건 추가가 아니라 기존 블록 reward 행 미세 보강(섹션 8의 3개 repair unit)이다.

---

read-only true benchmark audit complete; no pair files mutated
