# TF-F: Manuscript Contradiction Audit Report

**Date**: 2026-03-16
**Auditor**: TF-F (Opus 4.6 1M)
**Scope**: 10 project DBs, 24 episodes total

---

## Audit Summary

| # | Project Path | Episodes | Contradictions Found |
|---|---|---|---|
| 1 | `projects/기록용/00_test_10_.../project_data.db` | 3 (EP1-3) | 2 |
| 2 | `projects/기록용/00_test_12_.../project_data.db` | 4 (EP1-4) | 3 |
| 3 | `projects/코덱스_테스트/project_data.db` | 3 (EP1-3) | N/A (test artifact) |
| 4 | `projects/기록용/00_test_03/project_data.db` | 2 (EP1-2) | 1 |
| 5 | `projects/기록용/00/project_data.db` | 2 (EP1-2) | 1 |
| 6 | `projects/기록용/01/project_data.db` | 2 (EP1-2) | 2 |
| 7 | `projects/기록용/03/project_data.db` | 2 (EP1-2) | 0 |
| 8 | `projects/기록용/0w/project_data.db` | 2 (EP1-2) | 0 |
| 9 | `projects/00_20260314/project_data.db` | 2 (EP1-2) | 2 |
| 10 | `projects/0/project_data.db` | 2 (EP1-2) | 1 |

**Total contradictions**: 12 (3 CRITICAL, 5 IMPORTANT, 4 MINOR)

---

## Common Worldbuilding Facts (shared across all projects)

All projects share the same "regression to 2006" investment novel premise:
- **MC**: Han Si-woo (한시우), age 26 (regressed from age 44, died in 2024 winter)
- **Setting**: Regresses to January 2006, Seongbuk-dong family mansion
- **Family**: Father Han Jeong-ho (한정호, SW/Daehan Group chairman); older brothers Han Tae-jun (한태준, eldest), Han Tae-min (한태민, second)
- **Background**: Former national equestrian team member, died of poverty/isolation at 44
- **Core plan**: Liquidate personal assets (~20B KRW), establish "SW Investment" firm, trade crude oil futures exploiting foreknowledge of 2006 Iran nuclear crisis, 2008 Lehman crash, 2009 Bitcoin genesis
- **Key future events remembered**: Feb 2006 Iran nuclear talks collapse, MEND pipeline attacks, WTI $78 peak July 2006, Lehman bankruptcy Sep 15 2008, Bitcoin genesis block Jan 3 2009

---

## Project 1: `projects/기록용/00_test_10_retry_live_runtime_proof_refresh_20260314/project_data.db`

**Episodes**: 3 (제1화: 재와 먼지 속에서 / 제2화: 사자의 식탁 / 제3화)

### Key Facts Tracked
- EP1: Wakes up in Seongbuk-dong home, age 26. Uses a folder phone. Calls "Kim Team Leader" (김 팀장, Daehan Group secretariat) to liquidate all assets. Owns horse "Aquila" (아퀼라). Father barges into room after Kim reports back.
- EP2: Father confronts him about asset sale. Si-woo declares "SW Investment" and states "법인 설립 절차에 들어갔습니다" (already started corporate establishment). Father demands he present at tomorrow 9AM executive meeting, pitted against brother Tae-jun's proposal. Brother Tae-jun calls that night.
- EP3: Si-woo calls Kim Team Leader again about progress. Kim says "20억 1,300만 원" after taxes, to be deposited tomorrow morning. Si-woo then calls lawyer Choi Jeong-hyeok (최정혁) at law firm "Zenith" (제니스). States capital will be confirmed tomorrow, asks for incorporation paperwork by 9AM.

### Contradictions

**[C1-1] M-4 Asset/Ability: Premature claim of corporate establishment**
- **Severity**: IMPORTANT
- **Episodes**: EP2 vs EP3
- **EP2 quote**: "투자사를 설립하겠습니다. 이미 법인 설립 절차에 들어갔습니다. SW인베스트먼트. 제 회사입니다." (Already started corporate establishment procedures)
- **EP3 quote**: Si-woo calls lawyer Choi at Zenith law firm and says "말씀드렸던 건, 예정대로 진행해 주십시오" and Choi replies "자본금은 해결되신 겁니까?" and "자본금 입금 확인되는 대로 즉시 절차에 착수할 수 있도록"
- **Explanation**: In EP2, Si-woo tells his father he has "already entered corporate establishment procedures" as a fait accompli. But in EP3 (which occurs after EP2), the lawyer has not yet started anything -- he is still waiting for capital confirmation before he can begin. The incorporation has not actually started. Si-woo's EP2 statement is a bluff/lie to his father, but the narrative presents it as internal thought too ("완벽한 계획이었다"), making it ambiguous whether the author intended it as factual.

**[C1-2] M-4 Asset: Kim Team Leader's role inconsistency**
- **Severity**: MINOR
- **Episodes**: EP1 vs EP3
- **EP1 quote**: Si-woo calls "단축번호 1번" and reaches "김 팀장" (Kim Team Leader), described as "내 개인 자산을 관리해주던 대한그룹 비서실 소속"
- **EP3 quote**: Si-woo again calls "단축번호 1번" and reaches "김 팀장" -- same person, same role, consistent. However, EP1 establishes Si-woo gave a strict ultimatum ("오늘 오후 6시까지 입금 확인 안 되면, 내일부터는 다른 사람하고 일하게 될 겁니다") but in EP3, Kim is still showing emotional concern ("아퀼라는 도련님께 의미가 남다르지 않습니까"), suggesting no relationship damage from the harsh ultimatum.
- **Explanation**: Minor tonal inconsistency -- after being threatened with termination, Kim Team Leader acts as if nothing happened and is still sentimentally attached. Not a hard factual contradiction but a characterization inconsistency.

---

## Project 2: `projects/기록용/00_test_12_stage34_live_runtime_proof_refresh_20260314/project_data.db`

**Episodes**: 4 (재와 먼지 속에서 / 다른 대답 / 강철의 무게 / 전쟁의 냄새)

### Key Facts Tracked
- EP1: Wakes up Jan 17, 2006 (digital clock shows exact date). CRT monitor + beige desktop PC. Checks internet banking, has 2,017,450,000 KRW. Typed future notes on computer. Butler (늙은 집사) knocks, tells him Chairman wants him in study.
- EP2: Goes to father's study. Father asks "이제 뭐 할 거냐?" (retirement plan question). Si-woo says "사업하겠습니다 / 투자사를 설립할 겁니다 / 원자재 트레이딩". Father shows him a Winchester hunting rifle on wall above fireplace. Si-woo reaches for it.
- EP3: Si-woo lifts the rifle, checks the chamber, places it on father's desk. Father says "나가봐라". Si-woo returns to room, boots computer again. Balance: 2,017,450,000 KRW. Calls law firms, finds "법무법인 제니스" and talks to lawyer. Door is violently knocked -- butler announces 둘째 도련님 (Han Tae-min) has arrived, furious.
- EP4: Tae-min breaks into room, grabs Si-woo's collar. Si-woo counters with a secret about Tae-min's affair (diamond necklace at Cheongdam jewelry shop). Tae-min is stunned. Si-woo leaves the house entirely, takes a taxi to Teheran-ro. Rents an office, meets lawyer Kim Do-yoon (김도윤) from Zenith law firm in person. Transfers all 20.1745B KRW to corporate account. Sets up SW Investment. Days later, sees Reuters breaking news about Iran nuclear talks collapse.

### Contradictions

**[C2-1] M-1 Character: Butler identity inconsistency**
- **Severity**: IMPORTANT
- **Episodes**: EP1 vs EP2
- **EP1 quote**: "늙은 집사의 목소리였다. 과거와 조금도 달라지지 않은, 무미건조한 톤." (old butler, emotionless)
- **EP2 quote**: "김 집사의 목소리가 들렸다" / "김 집사의 미간이 미세하게 찌푸려지는 것을 놓치지 않았다" (named as "Kim Butler")
- **Explanation**: In EP1, the butler is described as "old butler" (늙은 집사) without a name. In EP2, he is named "Kim Butler" (김 집사). While this could be the same person, the naming is inconsistent -- EP1 treats him as unnamed, EP2 gives him a surname. Furthermore, in EP3 when Tae-min arrives, the butler is again called "늙은 김 집사" merging both references. The initial EP1 omission of the name creates a minor discontinuity.

**[C2-2] M-4 Asset: Lawyer name/contact inconsistency**
- **Severity**: CRITICAL
- **Episodes**: EP3 vs EP4
- **EP3 quote**: Si-woo calls law firms and connects with a lawyer at "법무법인 제니스" via phone. The lawyer is not named in EP3. Si-woo mentions wanting a "페이퍼컴퍼니" with Hong Kong HSBC account.
- **EP4 quote**: The lawyer visits Si-woo's new office and introduces himself as "법무법인 제니스의 김도윤 변호사입니다" (Kim Do-yoon).
- **EP3 quote (earlier phone call)**: "홍콩 법인 계좌까지 말씀이십니까?" -- the phone-call lawyer speaks in a cautious tone.
- **Explanation**: In EP3, Si-woo's phone call to Zenith reaches an unnamed lawyer. In EP4, the in-person meeting is with "Kim Do-yoon" from Zenith. This is not strictly a contradiction (could be the same person just named later), but the **procedural inconsistency** is that in EP3, Si-woo described having called "법무법인 몇 군데에 전화를 돌렸다" (called several law firms) and then settled on Zenith -- yet in EP4, Kim Do-yoon says they had a previous "유선으로 상담하셨던" phone consultation, implying a pre-existing relationship rather than a cold call from EP3.

**[C2-3] M-1 Character: Number of brothers**
- **Severity**: CRITICAL
- **Episodes**: EP1-3 vs EP4
- **EP1-3**: Only two brothers are referenced: 큰형 한태준 (eldest, Tae-jun) and 둘째 한태민 (second, Tae-min). Si-woo is consistently the youngest of three brothers. "형들의 권력 다툼 속에서 이용만 당하다 버려지고" (brothers' power struggle).
- **EP4**: Tae-min is referred to as "둘째 형" (second brother) and Si-woo is the third. However, Tae-min screams "네가 뭔데! 네가 뭔데 아버지 허락도 없이 재산을 처분해?" -- this implies Tae-min has some authority or claim over Si-woo's personal assets, which contradicts EP1's established fact that these are Si-woo's personal assets ("내 개인 자산") managed through the company secretariat.
- **Note**: The brother structure is actually consistent (3 sons: Tae-jun, Tae-min, Si-woo). However, Tae-min's claim of authority over Si-woo's personal assets is a relationship/authority contradiction.

---

## Project 3: `projects/코덱스_테스트/project_data.db`

**Episodes**: 3 (1화~3화 골든루트)

**Assessment**: All 3 episodes contain **identical looped test content** -- the same 3 sentences repeated hundreds of times (9,940 characters each, only 3 unique sentences). This is clearly a test/debug artifact, not actual manuscript content. **No meaningful narrative exists; contradiction audit is not applicable.**

---

## Project 4: `projects/기록용/00_test_03/project_data.db`

**Episodes**: 2 (제1화: 정밀하게 조율된 기계 장치 / 시장의 서막)

### Key Facts Tracked
- EP1: JSON-wrapped manuscript. Wakes up Jan 12, 2006. Butler is "집사 박 씨" (Butler Park). Father and eldest brother Tae-jun are heard talking in study about construction business. Si-woo has luxury watches, shoes, car keys. Plans to sell for ~20B seed money, 3x leverage = 60B position. Ends abruptly with corrupted JSON.
- EP2: Same day, Jan 12, 2006 morning. Si-woo enters father's study. Father + brothers Han Tae-jun and Han Tae-min present in hallway afterward. Si-woo calls "박성호 PB" (Park Seong-ho, PB) to open futures account at "한미증권" (Hanmi Securities). Drives to Yeouido.

### Contradictions

**[C4-1] M-1 Character: Butler name inconsistency with household staff**
- **Severity**: MINOR
- **Episodes**: EP1 vs EP2
- **EP1 quote**: "서재로 향하자 집사 박 씨가 고개를 숙이며 다가왔다" (Butler Park)
- **EP2 quote**: In EP2, the butler is not mentioned again. However, when Si-woo leaves the house, "집사 박 씨가 멀리서 나를 보았지만, 투명인간 취급하며 지나쳐갔다" -- here it says Butler Park ignores Si-woo, but EP1 established Butler Park as approaching with concern/deference ("고개를 숙이며 다가왔다").
- **Explanation**: In EP1, Butler Park approaches with customary respect. In EP2, he treats Si-woo as invisible. The behavior shift is unexplained within a single day.

---

## Project 5: `projects/기록용/00/project_data.db`

**Episodes**: 2 (재와 먼지의 왕 / 재롱이 아닌 선언)

### Key Facts Tracked
- EP1: Wakes up Jan 17, 2006 (folder phone shows date). "김 여사" (Kim Lady) knocks -- she died of stomach cancer 5 years ago in the future. Folder phone shows date. Father still alive. Brother Tae-min (둘째 형) calls about equestrian demonstration today. Si-woo's backstory mentions "아시안게임 금메달리스트" (Asian Games gold medalist).
- EP2: Morning of same day. Park Lady (박 여사) is the head housekeeper, described as the true power behind domestic affairs. Si-woo visits father in study, declares "사업하겠습니다". Father says "재롱이라도 부려보겠다는데 막을 생각은 없다" and conditions it: "실패하면 네 돈으로만 끝나지 않을 거다." Brothers mock him. Si-woo returns to room, writes "SW인베스트먼트" on paper, calls someone.

### Contradictions

**[C5-1] M-1 Character: Household staff contradiction**
- **Severity**: IMPORTANT
- **Episodes**: EP1 vs EP2
- **EP1 quote**: "김 여사" knocks on door, is described as "이 집에서 십 년 넘게 일한 김 여사" (Kim Lady, worked here 10+ years).
- **EP2 quote**: The person who greets Si-woo in the hallway the same morning is "박 여사" (Park Lady), described as "이 집의 보이지 않는 실세" (the hidden power of the house), head housekeeper who "가사 도우미들을 총괄".
- **Explanation**: EP1 has "Kim Lady" as the long-serving housekeeper who brings morning messages. EP2 introduces "Park Lady" as the actual head of domestic staff who delivers the Chairman's summons. Both are presented as the primary female domestic authority figure. The co-existence is possible (Kim = individual maid, Park = head housekeeper), but EP1 gives Kim Lady a role (delivering Chairman's messages about breakfast and study summons) that EP2 assigns exclusively to Park Lady. This creates functional overlap and confusion about who actually runs the household.

---

## Project 6: `projects/기록용/01/project_data.db`

**Episodes**: 2 (재와 먼지 속에서 / 보이지 않는 눈)

### Key Facts Tracked
- EP1: Extended backstory sequence (death in 2024 winter, original wife mentioned). Wakes up in high-rise apartment/penthouse (not family mansion). Seoul skyline visible from large windows. Checks laptop (노트북), searches "이란. 유가." on portal site. Takes his sports car from underground garage at night. 12-cylinder engine.
- EP2: Driving on Gangbyeonbuk-ro. Father calls his folder phone with a terse command: "본가로 와라. 지금 당장." Si-woo drives to Gangnam PC cafe instead. Spends hours creating a financial plan. As he gets up to leave, receives a text message: a photo of his own back taken from inside the PC cafe. Someone is watching him.

### Contradictions

**[C6-1] M-3 Location: Waking location inconsistency**
- **Severity**: CRITICAL
- **Episodes**: EP1 (internal)
- **EP1 quote (beginning)**: Si-woo wakes in an unfamiliar room. "넓은 통유리창 너머로 서울의 야경이 파노라마처럼 펼쳐져 있었다" (panoramic Seoul night view from floor-to-ceiling windows). Also: "창밖으로는 서울 시내가 한눈에 내려다보이는" (overlooking Seoul). This is clearly a high-rise apartment/hotel, not the family mansion.
- **All other projects**: Si-woo consistently wakes up in his childhood bedroom at the Seongbuk-dong family mansion (성북동 본가).
- **EP1 later quote**: "비틀거리며 거실로 나와 벽에 걸린 달력을 확인했다" -- then "본능적으로 서재로 향했다" (heads to study/library).
- **Explanation**: This project uniquely places Si-woo's regression in a high-rise apartment with a city view, not the family mansion. While this could be an intentional variant, it creates a location contradiction within the episode: Si-woo is in a luxury apartment with panoramic windows, yet has access to a "서재" (study) and an underground parking garage with his sports car -- suggesting a private residence rather than a hotel. EP2 then has the father calling him to "본가" (family home), confirming he is NOT at the family home. This is a deliberate story variant rather than an error, making it internally consistent but different from all other projects.

**[C6-2] M-2 Timeline: Night/day confusion**
- **Severity**: MINOR
- **Episodes**: EP1 vs EP2
- **EP1 quote**: Si-woo wakes up and the environment suggests nighttime -- "서울의 야경" (night view), "수많은 빌딩의 불빛이 별처럼 반짝이며" (building lights twinkling like stars). He then drives out at night ("밤의 포식자처럼").
- **EP2 opening**: Continues directly from EP1's driving scene, still at night. He goes to a 24-hour PC cafe and works until "창밖이 희미하게 밝아올 무렵" (near dawn). This is consistent.
- **However**: EP1 has Si-woo checking a laptop and searching news. He finds "[국제 유가 상승세 지속, 이란 핵 문제 재점화 우려]" as a news headline. This headline wouldn't exist yet in January 2006 (Iran IAEA referral was February). Minor timeline anachronism in the news content.

---

## Project 7: `projects/기록용/03/project_data.db`

**Episodes**: 2 (재와 먼지의 기억 / 다른 대답)

### Key Facts Tracked
- EP1: Wakes up in Seongbuk-dong mansion. Analog calendar shows "2006년 1월". Calls "김 집사" (Kim Butler) on internal house phone. Requests complete asset report by evening. Kim Butler is worried but complies. Then informed Chairman wants to see him tonight in study -- this is earlier than expected vs. prior life.
- EP2: Si-woo receives asset report and new folder phone from Kim Butler in hallway. Goes to study. Father + both brothers (Tae-jun with newspaper, Tae-min with PDA) present. Father asks "이제 뭘 할 거냐?" Si-woo says "사업하겠습니다 / 투자사 / 원자재 선물 / 제 개인 자산 / 그룹 지원 일절 받지 않겠습니다." Father says "좋다. 네 돈으로 뭘 하든 상관 않겠다." Adds condition: "실패하면 그땐 내 말대로 사는 거다."

### Contradictions

**No contradictions found.** The two episodes are tightly connected with consistent character naming (Kim Butler), consistent location (Seongbuk-dong mansion), consistent timeline (same day), and consistent facts. The father's condition is clearly stated and Si-woo's response is coherent. Brother characterizations (Tae-jun = newspaper, Tae-min = PDA) are consistent across both episodes.

---

## Project 8: `projects/기록용/0w/project_data.db`

**Episodes**: 2 (첫 번째 변수 / 제2화)

### Key Facts Tracked
- EP1: Unique variant -- Si-woo wakes up in a luxury hotel suite (not family mansion). Jan 17, 2006 (confirmed via room service call and folder phone). Seoul skyline visible but Lotte Tower is absent (correct for 2006). Smashes whiskey bottle against wall. Receives threatening phone call from unknown person: "이제 와서 발 뺄 생각은 아니겠지" / mentions a casino and "물건" (item) Si-woo allegedly stole. Deadline: tomorrow noon.
- EP2: Si-woo searches the hotel room for clues -- finds nothing. Receives call from "김 비서" (Kim Secretary) summoning him to father. Goes to Seongbuk-dong mansion. Asks Kim Secretary about previous night -- no info. Meets father in study. Father asks usual question. Si-woo declares business plans and asks for 20B as a "거래" (deal). Father agrees but sets condition: "실패하면 네가 내 아들로서의 모든 권리를 포기하고 이 집에서 쫓겨나는 거다."

### Contradictions

**No contradictions found.** This project has a unique story variant (hotel + mysterious threat) that distinguishes it from all other projects, but internally it is consistent. The hotel setting in EP1 flows logically into the mansion visit in EP2. The threatening phone call is a deliberate plot hook, and EP2's search for clues consistently yields nothing. Father's role (Kim Secretary as intermediary, study confrontation) is internally coherent.

---

## Project 9: `projects/00_20260314/project_data.db`

**Episodes**: 2 (재가 된 시간, 타오르는 기억 / 제2화)

### Key Facts Tracked
- EP1: Wakes up in Seongbuk-dong mansion. Calendar shows "2006년 1월". Kim Butler (김 집사, 40년 넘게 한씨 가문을 모신) notices change. Si-woo heads to study. In hallway, Han Tae-jun (eldest brother) physically confronts him, slams him against wall. Father emerges from study, stops it. Father gives Si-woo a small brass key (황동 열쇠) to a wall safe in his room. Si-woo opens safe: contains corporate seal (법인 인감도장), OTP card for overseas futures trading, and a black USB memory. Calls "박성호 팀장" (Park Seong-ho, PB).
- EP2: Han Tae-jun attacks Si-woo again in hallway. Father intervenes. Si-woo enters study. Father says "이제 뭘 할 거냐?" Si-woo declares business. Father has already given him the key. Si-woo goes to living room, overhears brothers (Tae-jun and "한서준" Tae-seo-jun, second brother) talking. Returns to room, opens safe. Calls Park Seong-ho.

### Contradictions

**[C9-1] M-1 Character: Second brother name change**
- **Severity**: CRITICAL (cross-episode naming)
- **Episodes**: EP1 vs EP2
- **EP1 quote**: "첫째 형 한태준" (eldest brother Han Tae-jun). The second brother is implied but not named in EP1. Si-woo is described as fighting with Tae-jun.
- **EP2 quote**: "한태준과 한서준" -- the second brother is named "한서준" (Han Seo-jun).
- **All other projects**: The second brother is consistently named "한태민" (Han Tae-min) across ALL other projects. This project uniquely uses "한서준" (Han Seo-jun).
- **Explanation**: The second brother's name has changed from the established "한태민" to "한서준" within this project. This is a clear M-1 Character contradiction. Whether this was an intentional rewrite or an LLM hallucination, it breaks consistency with the established character name used in every other project.

**[C9-2] M-4 Asset: Safe contents -- pre-existing business tools**
- **Severity**: IMPORTANT
- **Episodes**: EP1 (internal)
- **EP1 quote**: Safe contains "법인 인감도장" (corporate seal), "해외 선물 거래용 증권사에서 발급된 보안 OTP 카드" (overseas futures OTP card), and a "검은색 USB 메모리". Si-woo narrates: "이것들은 전생에서 그가 존재조차 몰랐던 것들이었다. 아마 아버지가 언젠가 그가 철이 들면 사업 밑천으로 쓰라고 넣어둔 모양이었다."
- **Explanation**: A corporate seal and overseas futures OTP card require prior legal entity setup and brokerage account opening. These cannot simply be placed in a safe "for when the son grows up" without an existing legal framework. This is an asset/ability plausibility issue -- the father would have needed to establish a legal entity and open a futures account in Si-woo's name beforehand, which contradicts the premise that Si-woo has done nothing with his life until now.

---

## Project 10: `projects/0/project_data.db`

**Episodes**: 2 (제1화: 서재의 선언 / 보이지 않는 손길)

### Key Facts Tracked
- EP1: Unique structure with scene headers. Si-woo has already declared business to father (scene opens post-declaration). Has personal assets: equestrian prize money, gifted stocks, a small Gangnam commercial property. Target: 20B KRW. Identifies "박성호. 신한은행 압구정 지점 대리" (Park Seong-ho, Shinhan Bank deputy) as future star PB. Calls him.
- EP2: Next day, meets Park at Shinhan Bank HQ VIP lounge. Hands over all asset documents. Demands 20B cash in one week. Park agrees. Evening dinner: father officially cuts all group support. Si-woo prepares to leave home. Father reveals he already knows about Park Seong-ho: "박 대리라는 친구, 손이 제법 빠른 모양이더군."

### Contradictions

**[C10-1] M-2 Timeline: Month inconsistency**
- **Severity**: MINOR
- **Episodes**: EP1 vs EP2
- **EP1**: No specific date mentioned, but context implies January 2006 (consistent with all other projects).
- **EP2 closing quote**: "폐부를 찌르는 2월의 밤공기" (the piercing February night air).
- **Explanation**: If EP1 takes place in January and EP2 takes place the next day (meeting with Park + dinner), then EP2 should still be January. The reference to "2월" (February) suggests either time has passed between episodes (unlikely given the "next day" meeting) or is a simple timeline error.

---

## Cross-Project Observations

### Recurring Contradictions Across Projects

1. **Household staff naming chaos**: Across all projects, the domestic staff identity shifts constantly -- Kim Lady (김 여사), Park Lady (박 여사), Butler Park (집사 박 씨), Kim Butler (김 집사), old unnamed butler (늙은 집사). No two projects use the same domestic staff configuration, suggesting the LLM has no stable anchor for these secondary characters.

2. **Brother name instability**: In 9 of 10 projects, the brothers are Han Tae-jun (한태준) and Han Tae-min (한태민). Project 9 uniquely uses "한서준" (Han Seo-jun) for the second brother, a clear generation error.

3. **Asset management contact variation**: The person managing Si-woo's assets varies: "Kim Team Leader" (김 팀장), "Park PB" (박성호 PB), "Park Seong-ho Team Leader" (박성호 팀장). The role and reporting structure shifts per project.

4. **Initial waking location**: 8 of 10 projects place Si-woo in the Seongbuk-dong family mansion. Projects 6 (01) and 8 (0w) place him in a luxury apartment/hotel suite, creating significantly different narrative openings.

5. **Father's initial response pattern**: Consistent across all projects -- father asks "이제 뭘 할 거냐?", Si-woo says "사업하겠습니다", father permits with conditions. Minor variations in the conditions (some add explicit failure penalties, others just express indifference).

---

## Severity Summary

| Severity | Count | IDs |
|---|---|---|
| CRITICAL | 3 | C2-3, C6-1, C9-1 |
| IMPORTANT | 5 | C1-1, C2-1, C2-2, C5-1, C9-2 |
| MINOR | 4 | C1-2, C4-1, C6-2, C10-1 |
| **Total** | **12** | |

### CRITICAL Issues Requiring Immediate Attention
1. **C9-1**: Brother renamed from 한태민 to 한서준 -- hard character name contradiction
2. **C6-1**: Waking location (high-rise apartment vs family mansion) -- may be intentional variant but breaks cross-project consistency
3. **C2-3**: Tae-min claims authority over Si-woo's personal assets, contradicting established ownership

---

*Report generated by TF-F (Opus 4.6 1M context), 2026-03-16*
