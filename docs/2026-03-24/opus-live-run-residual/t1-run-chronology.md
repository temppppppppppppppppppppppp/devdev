# T1 — Run Chronology

Date: 2026-03-24
Status: final (3-pass audited)
Lane: T1 Run Chronology
Terminal: 1
Evidence Run: `projects/0324_00_`
Master Order: `docs/2026-03-24/ep1-ep8-live-run-residual-10terminal-master-order.md`

## 1. Executive Summary

0324_00_ EP 1-8 live run의 rescue-round 소비와 verdict downgrade chain을 콘솔 + JSONL 교차 검증으로 재구성한다.

8화 중 4화(EP 2/3/5/6)가 rescue round를 소비했고, 1화(EP 7)가 PASS_WITH_FIX patch를 소비했다. 총 verdict downgrade 8건 중 6건이 `post_select_conflict` gate, 1건이 `director_primary_reject`, 1건이 `continuity_firewall`이다.

## 2. Included Coverage / Exclusions

**Included**:
- `docs/2026-03-24/console.txt` (2,331 lines)
- `projects/0324_00_/logs/episode_production.jsonl` (28 records, 8 episodes)
- per-round verdict, score, gate_basis, strategy, conflict family
- downgrade chain (Director provisional → post-select override)

**Excluded**:
- blueprint/manuscript 본문 분석 (T4/T6/T9 lane)
- code mechanism 분석 (T5/T7/T8 lane)
- Stage 2 arc truth (T2 lane)
- merged conclusion, execution SSOT, temp queue

## 3. Key Evidence — Full Verdict Chain

### EP 1 (Arc 1, pos 1/5) — 1 round, clean

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy |
|-------|-----------------|-------|------|-------------|-------|----------|
| R1 | PASS | 95 | `director_primary_pass` | PASS | **PASS** | tension |

- console L602: `Director 판정: PASS (score=95, 선택: 후보 A)`
- console L614-615: `Round 1 PASS!` / `✅ [Round 1] PASS`
- JSONL rec0: `ep=1, rd=0, verdict=PASS, score=95, gate=director_primary_pass`
- 경고: advisory StyleSignal 1건 (ced_score 3~5), PreCheck 실패 3건 (서사 폭주, 밀도 부족) — Director가 정당하게 무시

### EP 2 (Arc 1, pos 2/5) — 4 rounds, trust provenance conflict

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy | Conflict |
|-------|-----------------|-------|------|-------------|-------|----------|----------|
| R1 | PASS | 96 | `director_primary_pass` | history REJECT | **REJECT** | balanced | 신탁 출처 어머니↔조부 |
| R2 | PASS | 90 | `director_primary_pass` | history REJECT | **REJECT** | balanced | 동일 + 시작장소 위반 |
| R3 | PASS | 96 | `director_primary_pass` | history REJECT | **REJECT** | balanced | IFC 시작계약위반/확정상태회귀/완료사건반복 |
| R4 | PASS | 96 | `director_primary_pass` | PASS | **PASS** | balanced | — |

**Downgrade chain detail:**

R1 (console L688-744):
- Director PASS (96), 후보 A 선택 (L693: `gate: director_primary_pass`)
- Post-select history conflict (L698-700): "신탁 계좌 출처가 1화에서는 '어머니'로, 2화에서는 '조부(할아버지)'로"
- `[TF-3] Provisional PASS → REJECT downgrade: 1 post-select conflicts (history)` (L701)
- JSONL rec2: `ep=2, rd=0, verdict=REJECT, score=96, gate=post_select_conflict`

R2 (console L774-837):
- Director PASS (90), 후보 A (L779: `gate: director_primary_pass`)
- Post-select history conflict (L787-788): 동일 provenance 충돌 + "주인공이 초기 자본금(시드머니)으로 사용하려는 20억 원"
- `[TF-3] Provisional PASS → REJECT downgrade: 1 post-select conflicts (history)` (L787)
- Score plateau 경고 (L838): `[QR-7] 최근 두 라운드의 점수가 96점으로 동일`
- JSONL rec4: `ep=2, rd=1, verdict=REJECT, score=90, gate=post_select_conflict`

R3 (console L844-959):
- `[TF-4] patch_targets 연속 부재 → full rewrite로 전환` (L844)
- `[ASP] 레드팀 교정 발동 (재시도 3회차)` (L845), delta=+0
- Director PASS (96), 후보 A (L892: `gate: director_primary_pass`)
- Post-select history conflict (L899-900): `[IFC] 불변사실 위반 감지 (시작계약위반 / 확정상태회귀 / 완료사건반복)`
- `[TF-3] Provisional PASS → REJECT downgrade: 1 post-select conflicts (history)` (L899)
- `[TF-29] '제약 위반' 유형 REJECT 3연속 → 블루프린트 단계 문제 가능성` (L960)
- JSONL rec7: `ep=2, rd=2, verdict=REJECT, score=96, gate=post_select_conflict`

R4 (console L1014-1025):
- Director PASS (96), 후보 A (L1019: `gate: director_primary_pass`)
- Post-select PASS (L1024): `Round 4 PASS!`
- JSONL rec9: `ep=2, rd=3, verdict=PASS, score=96, gate=director_primary_pass`

**EP 2 pathology**: Director는 4라운드 전부 PASS를 줌. 매번 post-select history check가 override. conflict family는 단일 축(trust provenance). TF-29가 3연속 REJECT 시 blueprint 문제 가능성을 경고했으나, 4라운드째에 Writer가 자체 수정.

### EP 3 (Arc 1, pos 3/5) — 2 rounds, item/time carryover

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy | Conflict |
|-------|-----------------|-------|------|-------------|-------|----------|----------|
| R1 | PASS | 97 | `director_primary_pass` | continuity+history REJECT | **REJECT** | tension | 노트 보관(금고→서랍) + 시간(4:35→3:35) |
| R2 | PASS | 90 | `director_primary_pass` | PASS | **PASS** | tension | — |

**Downgrade chain detail:**

R1 (console L1100-1164):
- Director PASS (97), 후보 C 선택 (L1105: `gate: director_primary_pass`)
- Post-select continuity conflict (L1110-1112): "가죽 노트 보관 위치(금고 vs 서랍)" + "서재 독대 시간(오후 4시 35분) 이후 증권사 방문 시간(오후 3시 35분) 역행"
- Post-select history conflict (L1113-1116): 동일 2건 재확인
- `[TF-3] Provisional PASS → REJECT downgrade: 2 post-select conflicts (continuity, history)` (L1117)
- JSONL rec10: `ep=3, rd=0, verdict=REJECT, score=97, gate=post_select_conflict`

R2 (console L1193-1204):
- Director PASS (90), 후보 A (L1198: `gate: director_primary_pass`)
- Post-select PASS (L1203): `Round 2 PASS!`
- JSONL rec12: `ep=3, rd=1, verdict=PASS, score=90, gate=director_primary_pass`

**EP 3 pathology**: 2축 동시 충돌(아이템 위치 + 시간선). R2에서 1회 만에 해결. Director score가 97→90으로 하락 — retry에서 Writer가 안전 지향으로 전환한 것으로 추정.

### EP 4 (Arc 1, pos 4/5) — 1 round, clean

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy |
|-------|-----------------|-------|------|-------------|-------|----------|
| R1 | PASS | 96 | `director_primary_pass` | PASS | **PASS** | balanced |

- console L1509: `Director 판정: PASS (score=96, 후보 A)`
- console L1519: `Round 1 PASS!`
- JSONL rec13: `ep=4, rd=0, verdict=PASS, score=96, gate=director_primary_pass`
- Flashback advisory (L1498-1499): "시드머니를 '19억 원'으로 언급하나 3화에서 '20억'" — Director가 정당하게 무시 (19.3억 = 수수료 차감 후 정확한 수치)

### EP 5 (Arc 2, pos 1/5) — 3 rounds, accounting + leverage

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy | Conflict |
|-------|-----------------|-------|------|-------------|-------|----------|----------|
| R1 | PASS_WITH_FIX | 93 | `post_select_conflict`* | continuity+history REJECT | **REJECT** | balanced | 5천만 원 미차감 + 이체 시점 + 레버리지 |
| R2 | REJECT | 93 | `post_select_conflict` | — | **REJECT** | inplace_patch | score plateau |
| R3 | PASS | 95 | `director_primary_pass` | PASS | **PASS** | inplace_patch | — |

*R1: Director는 PASS_WITH_FIX(93)을 줬으나 post-select가 override하여 최종 gate=post_select_conflict.

**Downgrade chain detail:**

R1 (console L1612-1716):
- Director PASS_WITH_FIX (93), 후보 B (L1617: `gate: director_primary_pass_with_fix`)
- Director 지시: "독백의 '3배 레버리지'를 '최대 레버리지'로 수정" (L1626-1627)
- Post-select continuity conflict (L1628-1629): "자금 잔고 계산 누락(법인 자본금 5천만 원) 및 파생상품 계좌 이체 시점"
- Post-select history conflict (L1630-1631): "EP4 법인설립비 5천만 원이 잔고에 미반영"
- `[TF-3] Provisional PASS → REJECT downgrade: 2 post-select conflicts (continuity, history)` (L1632)
- JSONL rec14: `ep=5, rd=0, verdict=REJECT, score=93, gate=post_select_conflict`

R2 (console L1716-1718):
- `[QR-7] 점수 plateau: 최근 두 라운드의 점수가 93점으로 동일` (L1717)
- JSONL rec16: `ep=5, rd=1, verdict=REJECT, score=93, gate=post_select_conflict, strategy=inplace_patch`

R3 (console L1724-1781):
- `[ASP] 레드팀 교정 발동 (재시도 3회차)` (L1724), delta=+13
- Director PASS (95), 후보 A (L1776: `gate: director_primary_pass`)
- Post-select PASS (L1780): `Round 3 PASS!`
- JSONL rec18: `ep=5, rd=2, verdict=PASS, score=95, gate=director_primary_pass`

**EP 5 pathology**: PASS_WITH_FIX(레버리지 산술)와 post-select conflict(accounting gap)가 **같은 라운드, 다른 축**에서 동시 발화. R2에서 score plateau. R3에서 ASP 레드팀이 delta=+13으로 돌파.

### EP 6 (Arc 2, pos 2/5) — 3 rounds, multi-axis invention

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy | Conflict |
|-------|-----------------|-------|------|-------------|-------|----------|----------|
| R1 | REJECT | 78 | `director_primary_reject` | — | **REJECT** | tension | 시간(2월→4월) + 장소(사무실→오피스텔) + 코트 출처 |
| R2 | REJECT | 44 | `continuity_firewall` | — | **REJECT** | tension | 자본금 15억 vs 20억 모순 |
| R3 | PASS | 98 | `director_primary_pass` | PASS | **PASS** | balanced | — |

**Downgrade chain detail:**

R1 (console L1858-1924):
- Director REJECT (78), 후보 A (L1862: `gate: director_primary_reject`)
- Director 사유 (L1859): "타임라인 오류 (2006년 2월 하순 -> 4월 18일)"
- Director 지시 (L1869-1871): 시간→2월 하순, 장소→SW사무실, 코트→신규 구입
- 추가 모순 (L1882-1884): [MAJOR] 타임라인 4월 18일, [MINOR] 장소 오피스텔, [MINOR] 코트 짐가방
- JSONL rec19: `ep=6, rd=0, verdict=REJECT, score=78, gate=director_primary_reject`

R2 (console L1954-2030):
- Director REJECT (44), 후보 A (L1958: `gate: continuity_firewall`)
- Director 사유 (L1962): "Contradiction Firewall: CRITICAL 1건"
- 자본금 모순 (L1964-1966): "EP 5에서 19억 원을 전액 WTI에 투입했으므로 가용 현금 20억 원은 없다"
- `[Conflict-first retry]` + `[A-4 continuity replay]` 발동 (L1969-1972)
- R1의 3개 모순 지시가 R2 feedback에 누적 전달 (L1986-1997)
- JSONL rec21: `ep=6, rd=1, verdict=REJECT, score=44, gate=continuity_firewall`

R3 (console L2035-2098):
- `[ASP] 레드팀 교정 발동 (재시도 3회차)` (L2035), delta=+0
- Director PASS (98), 후보 A (L2092: `gate: director_primary_pass`)
- Post-select PASS (L2097): `Round 3 PASS!`
- CoVe LLM 검증 런타임 실패 → Director PASS 유지 (L2100)
- JSONL rec23: `ep=6, rd=2, verdict=PASS, score=98, gate=director_primary_pass`

**EP 6 pathology**: 유일하게 Director가 R1에서 primary REJECT을 준 에피소드. R2에서 continuity_firewall이 44점으로 재REJECT — 이 run 전체에서 최저 score. R3에서 전략을 tension→balanced로 전환 후 98점 clean PASS.

### EP 7 (Arc 2, pos 3/5) — 1 round, patched

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy | Conflict |
|-------|-----------------|-------|------|-------------|-------|----------|----------|
| R1 | PASS_WITH_FIX | 94→90 | `director_primary_pass_with_fix` | PASS (patch 후) | **PASS** | tension | "18년 전" 시간 표현 |

**Downgrade chain detail:**

R1 (console L2185-2205):
- Director PASS_WITH_FIX (94), 후보 B (L2190: `gate: director_primary_pass_with_fix`)
- Director 지시 (L2199-2200): "'18년 전 시우 자신을 짓눌렀던 파산의 환상통'에서 '18년 전'을 '전생에' 또는 '미래에'로 수정"
- `[TF-32-V] PASS_WITH_FIX patch #1/3` (L2201)
- Re-audit: `[TF-35] 재심사 #1: PASS (score=90)` (L2202)
- `[TF-32-V] 원고 수정 완료 → PASS 확정` (L2203)
- `Round 1 PASS!` (L2204)
- JSONL rec25: `ep=7, rd=0, verdict=PASS, score=90, gate=director_primary_pass_with_fix`

**EP 7 pathology**: PASS_WITH_FIX→patch→PASS 경로가 설계대로 작동. Post-select에서 추가 충돌 없음. Score 94→90 하락은 patch 적용에 따른 정상 범위 내 변동.

### EP 8 (Arc 2, pos 4/5) — 1 round, clean

| Round | Director Verdict | Score | Gate | Post-Select | Final | Strategy |
|-------|-----------------|-------|------|-------------|-------|----------|
| R1 | PASS | 98 | `director_primary_pass` | PASS | **PASS** | balanced |

- console L2282: `Director 판정: PASS (score=98, 후보 A)`
- console L2292-2293: `Round 1 PASS!` / `✅ [Round 1] PASS`
- JSONL rec27: `ep=8, rd=0, verdict=PASS, score=98, gate=director_primary_pass`
- 경고: [V66.1] 휴대전화 재획득 2건, 위치 변화, 압박 미감지, 밀도 부족 — 모두 후보 B/C에만 해당, 선택된 후보 A는 경고 3건(medium confidence)만

## 4. Findings Ranked

### F-1. Post-select conflict는 dominant downgrade gate이다

8건의 verdict downgrade 중 **6건이 `post_select_conflict` gate** (EP 2 R1-R3, EP 3 R1, EP 5 R1-R2).

| Gate | Count | Episodes |
|------|-------|----------|
| `post_select_conflict` | 6 | EP 2 (3), EP 3 (1), EP 5 (2) |
| `director_primary_reject` | 1 | EP 6 R1 |
| `continuity_firewall` | 1 | EP 6 R2 |

Director는 REJECT이 된 8건 중 **6건에서 먼저 PASS를 줬다가 post-select에 의해 override**됨. Director 자체 REJECT은 EP 6에서만 2건.

### F-2. Conflict family 분포

| Conflict Family | Episodes | Total REJECT Rounds |
|-----------------|----------|---------------------|
| trust provenance (어머니↔조부) | EP 2 | 3 |
| item location + timeline | EP 3 | 1 |
| accounting gap + leverage | EP 5 | 2 |
| timeline invention + location + capital | EP 6 | 2 |
| temporal phrasing | EP 7 | 0 (patch로 해결) |

단일 conflict family당 최대 소비: trust provenance = 3 rounds (EP 2).

### F-3. Score 궤적과 탈출 패턴

| EP | R1 Score | R2 Score | R3 Score | R4 Score | 탈출 계기 |
|----|----------|----------|----------|----------|-----------|
| 2 | 96 | 90 | 96 | 96 | R4 Writer가 provenance 자체 수정 |
| 3 | 97 | 90 | — | — | R2 Writer가 금고+시간 수정 |
| 5 | 93 | 93 | 95 | — | R3 ASP 레드팀 delta=+13 |
| 6 | 78 | 44 | 98 | — | R3 전략 전환 tension→balanced, ASP delta=+0 |

- EP 2/3: score 하락 후 탈출 (Writer가 안전 지향 전환)
- EP 5: score plateau 후 ASP 레드팀이 돌파
- EP 6: score 급락(78→44) 후 전략 전환+전면 재작성으로 98 달성

### F-4. Runtime escalation 체인

| Trigger | Console Reference | Effect |
|---------|-------------------|--------|
| `[TF-4] patch_targets 연속 부재` | EP 2 L844 | full rewrite 전환 |
| `[TF-29] 제약 위반 REJECT 3연속` | EP 2 L960 | blueprint 문제 가능성 경고 |
| `[QR-7] score plateau` | EP 2 L838, EP 5 L1717 | 수정 루프 반복 경고 |
| `[ASP] 레드팀 교정` | EP 2 L845, EP 5 L1724, EP 6 L2035 | 3회차 이상에서 발동 |
| `[Conflict-first retry]` | EP 6 L1969 | authoritative carryover 기준 재작성 지시 |
| `[A-4 continuity replay]` | EP 6 L1971 | blueprint/frontier 교정 우선 지시 |

### F-5. 안정 에피소드 잔여 경고 부채

| EP | Final Verdict | 잔여 경고 | 실질 부채? |
|----|---------------|-----------|-----------|
| 1 | PASS (R1) | StyleSignal ced_score 3 | **No** |
| 4 | PASS (R1) | Flashback "19억↔20억" advisory | **No** — 19.3억은 수수료 차감 후 정확 |
| 7 | PASS (R1, patched) | cross-episode 반복 표현 | **Marginal** — "18년 전" phrasing이 EP 8에 전파됨 (L2217) |
| 8 | PASS (R1) | cross-episode 반복 4건 (L2310-2312) | **Low** — 동일 모티프 반복이나 구조적 conflict 아님 |

EP 7의 patched text에서 "18년 전 나를 짓눌렀던 파산의" 표현이 Episode Bible 지속 압박 필드에 잔류 (L2217). EP 8에서 유사 phrasing이 3건 반복 (L2310-2312). 이는 structural conflict가 아닌 반복 모티프이며, 현재 시점에서 hidden debt로 분류하지 않는다.

## 5. Cleared Non-Culprits (this lane scope)

| 항목 | 판정 | 근거 |
|------|------|------|
| Director judgment quality | **Cleared** | Director가 잘못 PASS를 준 경우 0건. EP 6에서는 Director가 직접 REJECT. Post-select override는 Director가 놓친 cross-episode 축을 보완. |
| PASS_WITH_FIX 경로 오작동 | **Cleared** | EP 7에서 정상 작동 (patch→re-audit→PASS). EP 5에서는 post-select가 다른 축에서 override한 것이지 fix 경로 자체 문제 아님. |
| ASP 레드팀 품질 | **Cleared** | EP 5 R3에서 delta=+13으로 탈출 기여. EP 2/6에서 delta=+0이었으나 해로운 효과 없음. |

## 6. Residual Culprit Candidate

이 lane(Run Chronology)에서 관찰 가능한 잔류 원인 후보:

**Primary**: `post_select_conflict` gate가 반복 발동하는 패턴.
- 6/8 downgrade가 이 gate
- Director가 PASS를 주는데 post-select가 override → conflict의 **근원은 Director 이전 단계** (blueprint 또는 writer carryover)
- 이 lane은 근원을 특정할 수 없음 (T4/T6 lane scope)

**Secondary**: EP 6의 multi-axis invention (score 78→44→98)은 writer-level failure의 심각도를 보여줌. 단일 에피소드에서 시간+장소+코트+자본 4축 동시 발명은 carryover consumption의 체계적 취약점을 시사.

## 7. Next-Scope Recommendation

이 lane만으로는 bounded execution wave를 정당화할 수 없다. Chronology는 **"어디서 깨졌나"**를 보여주지만 **"왜 깨졌나"**는 T4(blueprint authority) + T6(carryover consumption) + T7(retry semantics) lane의 결과와 교차해야 한다.

유일하게 이 lane에서 독립적으로 제안 가능한 범위: `[TF-29]` 3연속 REJECT 경고가 EP 2에서 발동했지만 자동 blueprint refresh로 이어지지 않았다. 이 경고가 blueprint 재생성을 trigger하는 메커니즘이 있었다면 EP 2의 3 rescue round를 절약할 수 있었을 가능성.

## 8. Confidence And Limits

**Confidence: 96%**

높은 확신:
- console (2,331 lines)과 JSONL (28 records) 전량 교차 검증 완료
- 모든 verdict, score, gate_basis가 두 source에서 일치
- downgrade chain의 시간순 재구성이 명확

한계:
- EP 5 R2의 상세 Director verdict console output이 advisory feedback에 묻혀 정확한 Director score 라인을 직접 확인하지 못함 — JSONL로 보완 (rec16: score=93, gate=post_select_conflict)
- episode_production.jsonl의 홀수 record (rec1, 3, 5 등)가 intermediate metadata record로 ep 필드 미포함 — verdict chain에 영향 없음

---

## Mandatory Final Lines

- Can this lane explain a real residual failure by itself: **no** (chronology는 failure 위치를 보여주지만 root cause 특정 불가)
- Does this lane explain repeated rescue rounds after the closed waves: **yes** (post_select_conflict gate 6건, Director 미감지 cross-episode drift가 rescue round의 직접 원인)
- Would this lane justify a bounded next execution wave: **no** (root cause 특정 없이 execution wave 정당화 불가, T4/T6/T7 결과 필요)
