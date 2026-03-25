# T1 — Run Chronology Evidence Ledger

Date: 2026-03-24
Lane: T1 Run Chronology
Evidence Run: `projects/0324_00_`

## JSONL Verdict Table (episode_production.jsonl)

28 records, 8 episodes. 홀수 record는 intermediate metadata (ep 필드 미포함, 생략).

| Rec | EP | Round (0-based) | Verdict | Score | Gate | Strategy |
|-----|-----|-----------------|---------|-------|------|----------|
| 0 | 1 | 0 | PASS | 95 | director_primary_pass | tension |
| 2 | 2 | 0 | REJECT | 96 | post_select_conflict | balanced |
| 4 | 2 | 1 | REJECT | 90 | post_select_conflict | balanced |
| 7 | 2 | 2 | REJECT | 96 | post_select_conflict | balanced |
| 9 | 2 | 3 | PASS | 96 | director_primary_pass | balanced |
| 10 | 3 | 0 | REJECT | 97 | post_select_conflict | tension |
| 12 | 3 | 1 | PASS | 90 | director_primary_pass | tension |
| 13 | 4 | 0 | PASS | 96 | director_primary_pass | balanced |
| 14 | 5 | 0 | REJECT | 93 | post_select_conflict | balanced |
| 16 | 5 | 1 | REJECT | 93 | post_select_conflict | inplace_patch |
| 18 | 5 | 2 | PASS | 95 | director_primary_pass | inplace_patch |
| 19 | 6 | 0 | REJECT | 78 | director_primary_reject | tension |
| 21 | 6 | 1 | REJECT | 44 | continuity_firewall | tension |
| 23 | 6 | 2 | PASS | 98 | director_primary_pass | balanced |
| 25 | 7 | 0 | PASS | 90 | director_primary_pass_with_fix | tension |
| 27 | 8 | 0 | PASS | 98 | director_primary_pass | balanced |

## Console Line Index

| Event | Console Line | Content (abbreviated) |
|-------|-------------|----------------------|
| EP1 R1 Director PASS | L602 | `Director 판정: PASS (score=95)` |
| EP1 R1 post-select PASS | L614 | `Round 1 PASS!` |
| EP2 R1 Director PASS | L688 | `Director 판정: PASS (score=96)` |
| EP2 R1 post-select history | L698-700 | 신탁 출처 어머니↔조부 |
| EP2 R1 TF-3 downgrade | L701 | `Provisional PASS → REJECT downgrade: 1 (history)` |
| EP2 R2 Director PASS | L774 | `Director 판정: PASS (score=90)` |
| EP2 R2 post-select history | L787-788 | 동일 provenance + 시드머니 20억 |
| EP2 R2 QR-7 plateau | L838 | `score plateau 96=96` |
| EP2 R3 TF-4 escalation | L844 | `patch_targets 연속 부재 → full rewrite` |
| EP2 R3 ASP | L845 | `레드팀 교정 발동, delta=+0` |
| EP2 R3 Director PASS | L887 | `Director 판정: PASS (score=96)` |
| EP2 R3 IFC | L900 | `IFC 시작계약위반/확정상태회귀/완료사건반복` |
| EP2 R3 TF-29 | L960 | `제약 위반 REJECT 3연속 → 블루프린트 문제 가능성` |
| EP2 R4 Director PASS | L1014 | `Director 판정: PASS (score=96)` |
| EP2 R4 post-select PASS | L1024 | `Round 4 PASS!` |
| EP3 R1 Director PASS | L1100 | `Director 판정: PASS (score=97)` |
| EP3 R1 continuity conflict | L1110-1112 | 노트 금고→서랍 + 시간 4:35→3:35 |
| EP3 R1 history conflict | L1113-1116 | 동일 2건 |
| EP3 R1 TF-3 downgrade | L1117 | `2 post-select conflicts (continuity, history)` |
| EP3 R2 Director PASS | L1193 | `Director 판정: PASS (score=90)` |
| EP3 R2 post-select PASS | L1203 | `Round 2 PASS!` |
| EP4 R1 Director PASS | L1509 | `Director 판정: PASS (score=96)` |
| EP4 R1 post-select PASS | L1519 | `Round 1 PASS!` |
| EP4 Flashback advisory | L1498-1499 | 시드머니 19억↔20억 (false alarm) |
| EP5 R1 Director PWF | L1612 | `Director 판정: PASS_WITH_FIX (score=93)` |
| EP5 R1 continuity conflict | L1628-1629 | 5천만 원 미차감 + 이체 시점 |
| EP5 R1 history conflict | L1630-1631 | EP4 법인설립비 미반영 |
| EP5 R1 TF-3 downgrade | L1632 | `2 post-select conflicts (continuity, history)` |
| EP5 R2 QR-7 plateau | L1717 | `score plateau 93=93` |
| EP5 R3 ASP | L1724 | `레드팀 교정 발동, delta=+13` |
| EP5 R3 Director PASS | L1772 | `Director 판정: PASS (score=95)` |
| EP5 R3 post-select PASS | L1780 | `Round 3 PASS!` |
| EP6 R1 Director REJECT | L1858 | `Director 판정: REJECT (score=78)` |
| EP6 R1 사유 | L1859 | 타임라인 2월→4월, 장소, 코트 |
| EP6 R2 Director REJECT | L1954 | `Director 판정: REJECT (score=44)` |
| EP6 R2 continuity_firewall | L1958 | `gate: continuity_firewall` |
| EP6 R2 capital 모순 | L1964-1966 | 가용현금 20억 불가 |
| EP6 R2 Conflict-first retry | L1969 | authoritative carryover 재작성 지시 |
| EP6 R2 A-4 continuity replay | L1971 | blueprint/frontier 교정 우선 |
| EP6 R3 ASP | L2035 | `레드팀 교정 발동, delta=+0` |
| EP6 R3 Director PASS | L2087 | `Director 판정: PASS (score=98)` |
| EP6 R3 post-select PASS | L2097 | `Round 3 PASS!` |
| EP6 R3 CoVe failure | L2100 | `CoVe LLM 실패 → Director PASS 유지` |
| EP7 R1 Director PWF | L2185 | `Director 판정: PASS_WITH_FIX (score=94)` |
| EP7 R1 TF-32-V patch | L2201 | `PASS_WITH_FIX patch #1/3` |
| EP7 R1 re-audit | L2202 | `재심사 #1: PASS (score=90)` |
| EP7 R1 확정 | L2203 | `원고 수정 완료 → PASS 확정` |
| EP8 R1 Director PASS | L2282 | `Director 판정: PASS (score=98)` |
| EP8 R1 post-select PASS | L2292 | `Round 1 PASS!` |
| EP8 반복 경고 | L2310-2312 | cross-episode 반복 4건 |
| Run 종료 | L2315 | `목표 회차(8화) 도달. 종료합니다.` |

## Aggregate Statistics

- Total production rounds: 16 (EP1:1 + EP2:4 + EP3:2 + EP4:1 + EP5:3 + EP6:3 + EP7:1 + EP8:1)
- Rescue rounds (non-first): 8 (EP2:3 + EP3:1 + EP5:2 + EP6:2)
- 1st-round pass rate: 50% (4/8: EP1, EP4, EP7*, EP8) (*EP7 = PASS_WITH_FIX patched)
- Strict 1st-round pass rate: 37.5% (3/8: EP1, EP4, EP8)
- Downgrade count: 8 (post_select_conflict: 6, director_primary_reject: 1, continuity_firewall: 1)
- Director PASS overridden by post-select: 6/8 downgrades
- Lowest score: 44 (EP6 R2, continuity_firewall)
- Highest final score: 98 (EP6 R3, EP8 R1)
- ASP 레드팀 발동: 3회 (EP2 R3, EP5 R3, EP6 R3), 유효 delta: EP5 +13
- Strategy 전환으로 탈출: EP6 (tension→balanced)
