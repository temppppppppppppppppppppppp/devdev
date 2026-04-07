# 10-Pair Meta Cleanup Terminal 03 — Pair 03 Cider Absence Survey

- Date: 2026-04-07
- Status: final (read-only survey)
- Document Type: bounded read-only narrative density survey (one terminal, one pair)
- Canonical Path: `docs/2026-04-07/10pair_meta_cleanup_terminal03_pair03_cider_absence_survey.md`
- Owning Order: user-issued investigation order ("사이다가 없는 block 조사해서 문서화해")
- Terminal: `03`
- Pair: `03_chaebol_ent_empire`
- Family: `blockguide`
- Baseline Commit: `5c71b81a36ab2cbae824c630bb63219354b913a8` (post-finalize state of pair 03)

## 1. Scope

Read-only survey of all 70 blocks in pair `03` to identify blocks lacking
cathartic / cider beats. **No artifact mutations.** No fixes proposed in
this document — pure investigation.

This survey is **separate** from the consistency audit and finalize work
already completed for pair `03`. It does not propose new edits unless the
user explicitly issues a follow-up order.

## 2. Why "사이다 부재" Is Hard To Define In This Codebase

Pair `03`'s declared cider pattern lives in `BI.MasterBible.ProjectData.CommercialCode.cider_point`:

> "누구도 가치를 못 보던 사람을 맞는 자리에 놓는 순간 폭발하는 반전.
> 업계가 비웃던 변칙이 시장에서 먼저 통하는 쾌감."

This is a free-text declaration, not a measurable contract. The harness
does **not** directly measure cider density. The closest functional
metric is `has_recognition_signal()` in `scripts/tr_batch_harness.py`, which
applies a regex against a pool of fields and counts blocks where the regex
matches:

```python
RECOGNITION_RE = re.compile(
    r"(대단|인정|재평가|경탄|감탄|존중|신뢰|의지|믿게|"
    r"다시\s*봤|경외|감복|수긍|고개를 숙|격이 다르)"
)
```

Pool: `content.reward`, `callback[*]`, `relationship_delta[*].after`,
`power_shift.protagonist`, `power_shift.antagonist`,
`regression_hint.recognition_from`.

Note: this metric is only **enforced** as a hard gate for regressor
treatments (`is_regressor_treatment`). Pair `03` is not a regressor pair,
so the gate doesn't apply, but the count is still computed
(`recognition_signal_blocks: 0` on pair `03` baseline).

For this survey, I use a stricter weighted score that combines the harness
regex with additional cider markers (cathartic emotional_beat, win-language
in `power_shift.protagonist`, financial gain in `reward`, opponent
weakness exploited, "industry-was-wrong" motif).

## 3. Operational Scoring (strict)

For each block:

| Marker | Weight | What it captures |
|---|---:|---|
| `emotional_beat.type` ∈ cathartic set | +2 | `triumph / breakthrough / vindication / recovery / launch / relief / momentum / synthesis / validation / hard_won_victory / redefinition / clarity / creation / legacy / euphoria / elevation / assertion / defiance / realization / resolve` |
| `RECOGNITION_RE` matches anywhere in pool | +2 | Direct 인정/재평가/존중 wording |
| `WIN_PROT_RE` matches `power_shift.protagonist` | +1 | Protagonist explicit win wording (`승리/입증/꺾/회수/뒤집/반격/장악/관철/먹힌/굳혔/굳어진` 등) |
| `REWARD_GAIN_RE` matches `content.reward` | +1 | Concrete win in reward field (자본 +N억, 회복, 확정, 첫 인정 등) |
| `INDUSTRY_WRONG_RE` matches pool | +2 | "업계가 비웃던 / 관행을 깨 / 상식을 뒤집" 모티프 (페어 03 cider_point 핵심) |

Bucketing:

| Bucket | Definition | Read |
|---|---|---|
| **A — strong cider** | score `>= 3` | 명확한 사이다 |
| **B — mild cider** | score `1-2` | 부분적 사이다 마커 |
| **C — intentional collapse** | score `0` AND `beat ∈ {collapse, defeat, betrayal, setback, crash, despair, ambush, shock, crisis}` | 의도된 패배/하락 (사이다 부재가 정상) |
| **D — setup / buildup** | score `0` AND `beat ∈ {setup-family beats}` | 의도된 빌드업 (긴장 축적, 사이다 부재가 정상) |
| **E — pyrrhic victory** | `beat == pyrrhic_victory` | 사이다와 비용이 같이 오는 의도된 mixed |
| **F — suspicious empty** | score `0`, neither setup nor collapse, tension `>= 5` | 사이다가 있어야 할 것 같은데 마커가 없음 — 조사 대상 |

## 4. Bucket Distribution (strict scoring, 70 blocks)

| Bucket | Count | % |
|---|---:|---:|
| A — strong cider | 14 | 20% |
| B — mild cider | 29 | 41% |
| E — pyrrhic victory | 2 | 3% |
| C — intentional collapse | 4 | 6% |
| D — setup / buildup | 15 | 21% |
| F — suspicious empty | 6 | 9% |
| **Total** | **70** | 100% |

Zero-cider score: 27 blocks total (E + C + D + F).

## 5. A Bucket — Strong Cider (14 blocks)

| # | Title | Beat | Score |
|---|---|---|---:|
| 1 | 쓰레기통 상속과 첫 직감 | breakthrough | 3 |
| 3 | 감으로만 버는 건 아니다 | triumph | 5 |
| 8 | 맞는 자리 | breakthrough | 5 |
| 10 | 계속할 이유 | triumph | 4 |
| 19 | 이름이 돌기 시작한다 | momentum | 4 |
| 20 | 청산 보류 | hard_won_victory | 4 |
| 30 | 첫 업계전쟁의 승자 | assertion | 4 |
| 40 | 방송이 아니라 시장을 흔들다 | breakthrough | 4 |
| 50 | 엔터가 아니라 생활권력 | redefinition | 4 |
| 57 | 팬덤은 국경보다 오래 남는다 | recovery | 3 |
| 60 | 세계 무대의 증명 | triumph | 4 |
| 61 | 축하가 끝난 자리 | forewarning | 3 |
| 67 | 조용한 선택 | clarity | 4 |
| 70 | 인정이 아니라 표준 | legacy | 4 |

Distribution: 14 strong cider blocks across the 70-block arc, roughly one
every 5 blocks. Late-arc concentration (61-70) holds 4 strong-cider
blocks. Healthy density.

## 6. C Bucket — Intentional Collapse (4 blocks, **사이다 부재 정상**)

These are designed setbacks where the absence of cider IS the narrative
function — they exist to set up future payoff.

| # | Title | Beat | Tension | Function |
|---|---|---|---:|---|
| 16 | 감사실 칼날 | betrayal | 9 | 한도윤이 감사실을 끌어들여 태하 일정을 끊는 첫 정치적 패배. 17번 우회로 사이다의 setup. |
| 34 | 플랫폼이 문을 닫다 | setback | 8 | 단일 플랫폼 의존의 위험 노출. 35번 분산 접점 사이다의 setup. |
| 47 | 위생 논란 | crisis | 9 | 빠르게 키운 팝업·상품 구조의 첫 역풍. 49번 "우리 것만 남긴다" reconstruction의 setup. |
| 58 | 강이현의 폭발성 | shock | 8 | 글로벌 성공 직후 팀 내부 균열 폭발. 59번 reflection → 60번 triumph로 회수. |

**판정**: 4건 모두 의도된 narrative beat. 사이다 부재가 결함이 아닌 설계.

## 7. E Bucket — Pyrrhic Victory (2 blocks, **mixed cider 정상**)

| # | Title | Tension | Description |
|---|---|---:|---|
| 9 | 가능성은 떴는데 돈은 샌다 | 7 | 화제성은 얻었지만 현금 흐름은 빠지는 mixed 상태. 10번 계속할 이유에서 회수. |
| 55 | 세계를 잡았지만 팀이 갈린다 | 9 | 글로벌 성공의 고점이지만 팀 균열의 시작. 60번 triumph + 후반 반격으로 회수. |

**판정**: pyrrhic_victory는 페어 03의 의도된 narrative pattern (cider_point의
"먼저 통하는 쾌감" 뒤에 비용을 같이 보여주는 구조). 정상.

## 8. D Bucket — Setup / Buildup (15 blocks, **사이다 부재 정상**)

긴장 축적 / 위협 노출 / 의심 심기 / 자기 성찰 등 페어 03의 buildup 모드. 사이다는
이후 블록에서 회수.

| # | Title | Beat | Tension | 회수 블록 (추정) |
|---|---|---|---:|---|
| 12 | 조용한 훈련 | discipline | 4 | 13 첫 반응, 19 이름이 돌기 시작한다 |
| 14 | 호텔 주방의 남자 | curiosity | 5 | 33 주방도 무대가 된다, 41-46 문선우 라인 |
| 21 | 연습실에 규칙을 깔다 | determination | 6 | 25 팀을 만드는 일, 27 배우가 회사 간판이 되다 |
| 22 | 윤서아의 그림자 | unease | 7 | 37 누가 윤서아를 망가뜨렸나, 44 윤서아의 과거를 되돌려주다 |
| 23 | 화제는 터졌는데 방송은 막혔다 | frustration | 8 | 24 방송 없이 팬을 모으다, 30 첫 업계전쟁의 승자 |
| 26 | 천재는 팀을 찢는다 | anxiety | 7 | 60 세계 무대의 증명, 후반 반격 |
| 28 | 새벽의 숨고르기 | introspection | 4 | 59 잠깐 멈춘 방, 67 조용한 선택 |
| 29 | 놓친 이름 | humbling | 6 | 30 첫 업계전쟁의 승자, 54 돌아온 놓친 카드 |
| 31 | 카메라 한 대로도 스타는 뜬다 | experimentation | 5 | 32 포맷을 먼저 만든다, 36 박재인 |
| 33 | 주방도 무대가 된다 | discovery | 5 | 41-46 문선우 라인, 50 엔터가 아니라 생활권력 |
| 39 | 숫자가 커질수록 냄새도 짙어진다 | foreboding | 6 | 48 장부 속 이상한 흐름, 66 장부가 입을 열다 |
| 42 | 조용한 메뉴 테스트 | restraint | 4 | 45 문선우, 얼굴이 되다, 50 엔터가 아니라 생활권력 |
| 48 | 장부 속 이상한 흐름 | suspicion | 7 | 66 장부가 입을 열다, 68 시장을 움직이는 폭로 |
| 53 | 세계는 열렸고, 사람은 닫힌다 | strain | 7 | 60 세계 무대의 증명 |
| 62 | 공신들이 움직인다 | pressure | 7 | 65 반격의 방식, 68 시장을 움직이는 폭로 |

**판정**: 15건 모두 후속 블록에서 회수되는 정상적 buildup. 페어 03이
"buildup → payoff" 호흡을 준수하고 있음을 보여줌. 사이다 부재 결함 아님.

## 9. F Bucket — Suspicious Empty (6 blocks) — **재검토 결과: false positive**

이 6블록은 strict scoring에서 zero이지만 emotional_beat이 setup도 collapse도
아닌 (counterattack/revelation/confidence/reconstruction/loyalty), tension `>= 5`인
"의심" 후보들이었습니다. **산문을 직접 읽고 재검토한 결과, 6블록 모두 implicit
cider가 존재**하며 점수가 0인 이유는 strict 정규식이 페어 03의 산문 스타일
("보기 시작", "처음 의심", "올라간다", "확인한다", "회복", "단계로 올라간다")을
못 잡는 false negative입니다.

### 9.1 Block 2 [유령 회사에 남은 칼] — beat=revelation

- `reward`: "윤서아는 정식 오디션 콜백을 확보하고, 서민재는 사람 보는 눈만큼은
  이상하게 맞는다고 처음 의심한다... 강이현 무대의 후속 부킹 계약이 확정되어
  자본은 125억을 유지한다."
- `power_shift.protagonist`: "태하는 처음으로 누굴 버릴지가 아니라 누굴 남길지를
  결정하는 위치를 차지하고, 윤서아의 자리까지 다시 정해 준다."
- `opponent.weakness_exploited`: "배우를 비용으로만 보는 관점"
- **사이다**: 정식 오디션 콜백 확정 + 서민재의 첫 의심(=인정의 시작) + 적의 약점 노출
- **누락 사유**: "처음 의심한다"는 RECOGNITION_RE 정규식이 못 잡음 (`인정` 아닌 `의심`).

### 9.2 Block 7 [첫 판짜기] — beat=counterattack

- `reward`: "쇼케이스는 소수 관계자에게 강하게 먹히며 14억 규모의 후속 가능성을
  만든다. 오지혁은 태하를 입만 사는 도련님이 아니라 판을 짜는 보스 후보로 보기
  시작하고, 강이현도 처음으로 자기 자리를 고민해 주는 사람으로 태하를 의식한다."
- `capital_delta`: `+14억`
- `opponent.weakness_exploited`: "적은 비용으로도 강한 첫인상을 만들 수 있는 패키지 구성"
- **사이다**: 14억 후속 가능성 + 오지혁/강이현의 평가 변화 + 적의 약점 노출
- **누락 사유**: "보스 후보로 보기 시작" / "처음으로 자기 자리를 고민해 주는 사람으로
  태하를 의식" — 둘 다 implicit recognition이라 정규식이 못 잡음.

### 9.3 Block 17 [우회로] — beat=counterattack

- `reward`: "막혔던 일정 일부가 다시 살아나며 자본이 27억 회복된다. 오지혁은
  이때부터 사실상 태하의 현장 오른팔로 돌아서고, 한도윤은 태하가 생각보다 쉽게
  죽지 않는다는 걸 실감한다."
- `capital_delta`: `+27억`
- `opponent.weakness_exploited`: "그룹 본예산 바깥에서 움직일 수 있는 외부 계약 라인"
- **사이다**: 자본 +27억 회복 + 오지혁의 충성 굳어짐 + 적의 좌절 ("쉽게 죽지 않는다")
- **누락 사유**: "회복" / "오른팔로 돌아서고" / "쉽게 죽지 않는다" 모두 implicit.

### 9.4 Block 36 [박재인, 이름이 아니라 습관이 되다] — beat=confidence

- `reward`: "체류 시간과 재방문 지표가 붙으며 자본이 59억 상승한다. 태하는
  팬덤이 단순 응원 집단이 아니라 체류 시간과 소비 패턴으로 읽히는 자산이라는
  걸 분명히 이해한다."
- `power_shift.protagonist`: "태하는 트래픽보다 체류와 반복성을 자산으로 읽는
  단계로 올라간다."
- `power_shift.antagonist`: "권도현 라인은 아직 이 숫자의 가치를 제대로 이해하지
  못하고 뒤늦게 경계하기 시작한다."
- `capital_delta`: `+59억`
- **사이다**: 자본 +59억 상승 + 페어 03 cider_point의 "업계가 비웃던 변칙이 시장에서
  먼저 통하는" 핵심 패턴 (권도현 라인이 데이터 가치를 못 봄 + 태하만 봄)
- **누락 사유**: "단계로 올라간다" / "분명히 이해한다" / "뒤늦게 경계" 모두 implicit.

### 9.5 Block 49 [우리 것만 남긴다] — beat=reconstruction

- `reward`: "자본은 163억 회복하며 1104억으로 올라간다. 회사 내부에서도 태하가
  처음으로 크게 벌기보다 오래 남는 구조를 보는 사람처럼 보이기 시작한다."
- `power_shift.protagonist`: "태하는 공격적인 확장가에서 통제 가능한 판을 남기는
  장기전 사업가로 변한다."
- `capital_delta`: `+163억`
- **사이다**: 자본 +163억 회복 + 내부의 인지 전환 ("처음으로... 보는 사람처럼 보이기
  시작") + 사업가 정체성 진화
- **누락 사유**: "회복" / "올라간다" / "보기 시작" / "변한다" 모두 implicit.

### 9.6 Block 64 [남는 사람들] — beat=loyalty

- `reward`: "자본은 142억 회복된다. 무엇보다 태하는 자기가 만든 제국의 핵심이
  돈이 아니라 끝내 남는 사람이라는 걸 확인한다."
- `power_shift.protagonist`: "태하는 회사를 잃은 듯 보여도, 사람을 잃지 않았다는
  점에서 아직 끝나지 않는다."
- `power_shift.antagonist`: "공신 라인은 회사를 가져가도 영혼까지 가져간 건
  아니라는 불안이 생긴다."
- `capital_delta`: `+142억`
- **사이다**: 패배 직후의 emotional cider — 사람의 가치 확인 + 적의 불안. 페어 03에서
  유일한 "loyalty 비트" 사이다 형태.
- **누락 사유**: "확인한다" / "끝나지 않는다" / "불안이 생긴다" 모두 implicit.

### F 버킷 종합

| # | Score | 실제 사이다 | 마커 누락 사유 |
|---|---:|---|---|
| 2 | 0 | ✅ 콜백 확정 + 자본 유지 + 적의 약점 노출 | "처음 의심" implicit |
| 7 | 0 | ✅ 자본 +14억 + 평가 전환 ×2 + 적의 약점 | "보기 시작" / "의식한다" implicit |
| 17 | 0 | ✅ 자본 +27억 + 충성 굳어짐 + 적의 좌절 | "회복" / "돌아서고" implicit |
| 36 | 0 | ✅ 자본 +59억 + cider_point 핵심 패턴 회수 | "단계로 올라간다" / "이해한다" implicit |
| 49 | 0 | ✅ 자본 +163억 + 정체성 진화 | "회복" / "보기 시작" implicit |
| 64 | 0 | ✅ 자본 +142억 + emotional cider (loyalty) | "확인한다" / "불안이 생긴다" implicit |

**판정**: F 버킷 6건 모두 실제로는 사이다 보유. 페어 03 결함 아님. 측정 도구 한계.

## 10. 진짜 "사이다 부재" 결함 블록 카운트

페어 03 70블록 중 **narrative 결함으로서의 사이다 부재 블록: 0개**.

- A 14 + B 29 = **43블록 (61%)** 에 explicit cider 마커 존재
- F 6블록 = implicit cider 존재 (정규식 한계)
- D 15 / C 4 / E 2 = 21블록 = 의도된 buildup / collapse / pyrrhic mixed

→ **43 + 6 = 49블록 (70%)** 에 사이다 보유, **21블록 (30%)** 가 의도된 사이다
부재 (buildup/collapse/pyrrhic). 페어 03의 사이다 분포는 정상이며, 결함으로
지목할 블록은 발견되지 않았습니다.

## 11. 부수 발견 — Harness `RECOGNITION_RE` 의 페어 03 산문 스타일에 대한 보수성

운영 발견: harness의 `recognition_signal_blocks` 메트릭이 페어 03에서 `0` 으로
보고되는 이유는 페어 03이 "사이다가 없어서"가 아니라, 페어 03 산문이 사이다를
**implicit / 단계적 / 행동 변화 형태** 로 표현하는 경향이 강해 정규식이 못 잡기
때문입니다.

페어 03 산문 패턴 vs 정규식 매치 어휘:

| 페어 03 산문 패턴 | RECOGNITION_RE 매치 어휘 |
|---|---|
| "처음 의심한다" / "보기 시작한다" | 매치 안 됨 |
| "회복한다" / "올라간다" / "단계로 올라간다" | 매치 안 됨 |
| "변한다" / "굳어진다" / "굳혔다" | 매치 안 됨 |
| "확인한다" / "이해한다" / "분명히 본다" | 매치 안 됨 |
| "쉽게 죽지 않는다는 걸 실감" | 매치 안 됨 |
| "오른팔로 돌아서고" / "보스 후보로 본다" | 매치 안 됨 |
| (정규식 매치) "대단/인정/재평가/존중/믿게/다시 봤" 등 명시 어휘 | ✅ |

페어 03의 14개 strong cider 블록과 29개 mild cider 블록은 페어 02·05·07이 사용하는
명시적 "인정/존중" 어휘 대신 행동·상태 변화 동사로 사이다를 전달합니다. 이는
페어 03의 작가적 선택이지 결함이 아닙니다.

이 발견은 **페어 03의 readiness에 영향을 주지 않습니다** (`recognition_signal_blocks`
는 regressor 페어에만 hard gate가 적용되고 페어 03은 비회귀물이라 미적용). 다만
향후 cross-pair "사이다 밀도" 분석 wave에서 페어 03을 비교할 때, harness의
`recognition_signal_blocks` 단일 메트릭에만 의존하면 페어 03이 부당하게 낮게 평가될
위험이 있다는 점은 별도 운영 주의사항입니다.

## 12. Stop Gates Held

- 어떤 페어 03 파일도 수정하지 않음.
- 다른 페어 / 시스템 트랙 / `docs/temp/` 미접촉.
- 본 문서는 read-only 조사 결과만 담음. 사이다 보강 / 산문 재작성 / 블록 추가
  등 어떤 fix도 제안하지 않음 — 사용자가 별도 수정 오더를 내릴 경우에만 진행.
- harness `RECOGNITION_RE` 어휘 확장도 본 wave 범위 밖. cross-pair 영향이 있어
  단일 페어 audit에서 결정할 사안이 아님.

## 13. 한 줄 결론

**페어 03은 사이다 부재 결함 블록이 0개**이며, harness 메트릭이 0으로 보고하는
것은 페어 03 산문 스타일이 사이다를 명시 어휘 대신 행동·상태 변화로 전달하기
때문이다. 측정 도구의 한계이지 페어의 결함이 아니다.
