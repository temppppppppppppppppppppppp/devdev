# Runtime/Cost Cross-Check Reconciliation — OPUS 측

> 작성일: 2026-03-11
> 작성자: OPUS (Claude Opus 4.6)
> 비교 대상: `ops-runtime-cost-crosscheck-codex.md` (Codex) vs `ops-runtime-cost-crosscheck-report-OPUS.md` (OPUS)
> 원본 두 문서 수정 없음

---

## 1. 합의 사실

양쪽이 동일한 숫자·verdict·taxonomy로 기술한 항목.

### 1-1. 표 A (Episode × Round Breakdown) 합의

| 항목 | OPUS | Codex | 판정 |
|---|---|---|---|
| ep1 R1: PASS 96, 315s, 218161tok, $0.4398 | ✅ | ✅ (315.1s) | **완전 합의** |
| ep2 R1: PASS 98, 380s, 162518tok, $0.2903 | ✅ | ✅ (379.6s) | **완전 합의** |
| ep3 R1: REJECT 44, 398s | ✅ | ✅ (397.5s) | **완전 합의** |
| ep3 R2: PASS 98, 313s | ✅ | ✅ (312.9s) | **완전 합의** |
| ep4 R1: PASS 98, 451s, 198497tok, $0.3418 | ✅ | ✅ (450.8s) | **완전 합의** |
| ep5 R1: REJECT 90, 515s | ✅ | ✅ (515.5s) | **완전 합의** |
| ep5 R2: PASS 90, 210s | ✅ | ✅ (210.4s) | **완전 합의** |
| ep6 R1: REJECT 44, 568s | ✅ | ✅ (567.9s) | **완전 합의** |
| ep6 R2: REJECT 44, 447s | ✅ | ✅ (447.3s) | **완전 합의** |
| ep6 R3: PASS 100, 442s | ✅ | ✅ (442.0s) | **완전 합의** |
| ep7 R1: REJECT 44, 653s | ✅ | ✅ (652.5s) | **완전 합의** |
| ep7 R2: PASS_WITH_FIX 90 | ✅ | ✅ (183.5s) | **완전 합의** |

**Stage 4 전 12행의 verdict, score, duration이 소수점 이하 차이만 있고 실질적으로 일치.**

### 1-2. 표 B (Stage Summary) 합의

| 항목 | OPUS | Codex | 판정 |
|---|---|---|---|
| S4 Arc 1: attempts=5, pass=4, reject=1 | ✅ | ✅ | **완전 합의** |
| S4 Arc 1: duration 1857s | 1,857s | 1,856.0s | **완전 합의** (1s 차이) |
| S4 Arc 1: tokens ~887K | estimated 887,000 | 887,999 | **합의** (Codex가 더 정밀) |
| S4 Arc 1: cost $1.64 | estimated $1.64 | $1.6420 | **합의** (Codex가 더 정밀) |
| S4 Arc 2: attempts=7, pass=2(OPUS)/3(Codex), reject=4 | pass=2 | pass=3 | **차이 있음** (아래 §2 참조) |
| S2/S3 전량 first-attempt PASS | ✅ | ✅ | **완전 합의** |
| Stage 4가 전체 시간의 ~75-85% | ~85% | ~76.2% | **방향 합의** (수치 차이는 S2/S3 추정치 차이에서 기인) |

### 1-3. 표 C (Root-Cause Taxonomy) 합의

| 합의 내용 | OPUS | Codex | 판정 |
|---|---|---|---|
| Contradiction Firewall 반복 REJECT = confirmed bottleneck | RC-1 | RC-3 | **합의** (ID만 다름) |
| post-select continuity reject = confirmed bottleneck 또는 supporting contributor | RC-3 (supporting) | RC-2 (confirmed) | **방향 합의** (등급 차이, §2 참조) |
| scene coverage 0% / dialogue 0% / InfoParadox = false positive / noise | RC-6, RC-7 | RC-5 | **완전 합의** |
| per-round instrumentation 부족 = 관측성 한계 | RC-5 | RC-6 (supporting) | **합의** |

### 1-4. 표 D (Improvement Priority) 합의

| 합의 내용 | OPUS | Codex | 판정 |
|---|---|---|---|
| post-select reject → patch 직행 = P0 | P0 | P0 | **완전 합의** |
| per-round token/cost DB 저장 = 계측 우선 | P1/P2 | P2 | **방향 합의** |

### 1-5. 비교용 요약 합의

| 질문 | OPUS | Codex | 판정 |
|---|---|---|---|
| 시간은 어디서? | Stage 4 (~85%) | Stage 4 (~76.2%) | **합의** |
| 비용은 어디서? | Stage 4 CW (99.5% pro) | Stage 4 본체 | **합의** |
| 다음 배치 가장 싼 개선? | Firewall REJECT → InPlace | post-select → single-candidate patch | **합의** (표현 다름, 같은 방향) |

---

## 2. 해석 차이

양쪽이 같은 사실을 보고 다른 taxonomy 또는 다른 등급을 부여한 항목.

### 2-1. post-select continuity reject의 taxonomy 등급

| | OPUS | Codex |
|---|---|---|
| taxonomy | **supporting contributor** (RC-3) | **confirmed bottleneck** (RC-2) |
| 근거 | ep5 R1 한 건. Director 주권주의(대원칙 3)와의 긴장. 오탐 가능성 있음(수동 감사에서 미확인) | ep5 R1에서 Director PASS 90 이후 full-round 폐기. 이미 비싼 round를 통째로 버림 |
| 핵심 갈림 | A-3 오탐 가능성에 무게 | 발동 시 비용 폐기에 무게 |

**OPUS 소견**: Codex의 관점이 비용 분석 맥락에서 더 적확하다. "오탐이든 유효 차단이든 full-round 폐기가 비용 증폭의 직접 원인"이라는 점에서 `confirmed bottleneck`이 runtime/cost cross-check의 목적에 더 부합한다. 다만 **정확도 축에서는** A-3의 유효 차단 사례가 없어 오탐율을 단정할 수 없으므로, `supporting contributor`가 보수적으로 더 안전하다. 양쪽 모두 합리적.

### 2-2. single-round floor cost의 분류

| | OPUS | Codex |
|---|---|---|
| 별도 RC 항목 | **없음** | **RC-1 confirmed bottleneck** |
| Codex 해석 | — | 1회 round 자체가 315~568초(5~9분) 소요. 이 고정 비용이 retry 시 곱셈 증폭의 기저 |
| OPUS 해석 | RC-9(토큰 증가)에 간접 포함 | — |

**OPUS 소견**: Codex가 "round 1회의 기저 비용 자체가 높다"를 별도 bottleneck으로 분리한 것은 유효하다. OPUS는 retry 횟수(Firewall)에 집중하여 기저 비용을 독립 항목으로 다루지 않았다. **비용 = 기저 × 횟수** 구조에서, OPUS는 횟수 축만, Codex는 기저 축도 분리한 셈이다.

### 2-3. Stage 3 duration 추정치

| | OPUS | Codex |
|---|---|---|
| S3 Arc 1 duration | estimated 600s | estimated 320.6s |
| S3 Arc 2 duration | estimated 600s | estimated 345.9s |
| 차이 | ~280s (~4.7분) | — |

**OPUS 소견**: OPUS의 600s는 ep당 150s × 4ep으로 산출한 보수적 상한. Codex의 320.6s는 "로그의 visible max API span과 직후 Director/StateExtractor span만 합산한 보수적 추정"이라고 명시했다. Codex 방식이 로그 기반으로 더 정밀하다. **OPUS 추정이 과대**했을 가능성이 높다.

### 2-4. S4 Arc 2 pass_count

| | OPUS | Codex |
|---|---|---|
| S4 Arc 2 pass_count | 2 | 3 |
| 근거 | ep5 PASS + ep6 PASS = 2 (ep7 미완) | ep5 PASS + ep6 PASS + ep7 PASS_WITH_FIX = 3 |

**OPUS 소견**: ep7 R2의 PASS_WITH_FIX를 pass로 카운트할지 여부. Codex는 포함, OPUS는 미완료(log truncated)로 제외했다. `episode_production.jsonl`에 ep7 기록이 있다면 Codex가 정확하다.

### 2-5. PromptLoader 경고의 위치

| | OPUS | Codex |
|---|---|---|
| 위치 | 필수 검토 축 소결 (본문) | RC-7 hypothesis pending + Appendix A에서 "현재 causal set 앞줄에서 내려도 된다" |

**OPUS 소견**: 합의 — 이번 rerun에서는 PromptLoader 경고가 주 원인이 아니다. Codex의 "causal set에서 내려도 된다"는 판단에 동의.

### 2-6. Firewall 감도 vs 구조적 라우팅

| | OPUS | Codex |
|---|---|---|
| P0 해법 | Firewall REJECT 시 fix_scope="inplace" 허용 | post-select reject → single-candidate patch 직행 |
| P0 해법 2 | CW prior_attempts에 contradiction_types 명시 | exact-state gate를 앞단으로 이동 |

**OPUS 소견**: 같은 방향의 다른 표현. OPUS는 "Firewall이 InPlace를 허용하면 된다"(라우팅 변경), Codex는 "gate를 앞으로 옮기면 된다"(타이밍 변경). 둘 다 적용하면 상승 효과.

---

## 3. 편측 발견

한쪽만 발견하거나 다룬 항목.

### 3-1. OPUS만 발견

| 항목 | OPUS 위치 | 내용 | Codex에 없는 이유 추정 |
|---|---|---|---|
| RC-10: Director가 false positive로 판단한 Firewall REJECT | RC-10, Appendix B-1 | ep7 R1에서 Director pre_firewall_score=98인데 Firewall CRITICAL 1건으로 44 강제. Director 주권 충돌 | Codex는 Firewall 반복을 RC-3으로 통합 처리하여 개별 사례를 분리하지 않음 |
| RC-4: 후보 필터링 후 단일 후보 | RC-4 supporting contributor | ep5 R1에서 candidate_count=1, ep6 R1에서 2/3 auto-disqualified | Codex는 이를 RC-2(post-select)의 일부로 흡수 |
| RC-9: Arc 진행에 따른 토큰 증가 정량화 | RC-9 confirmed bottleneck | ep5 495K vs ep1 218K (+125%) | Codex RC-4에서 S2/S3 overhead를 다루었으나, S4 per-ep 토큰 증가는 별도 분리하지 않음 |
| 3개 세션 분리 관측 | Appendix A-1 | Session 1(S2+S3), Session 2(S4 ep1 9회), Session 3(rerun) 구분 | Codex도 Session 2를 인지하나 별도 섹션으로 정리하지 않음 |
| Session 2 ep1 9회 반복 근본 원인 4건 | Appendix A-2 | JSON mode, thinking level, self-critique loop, rubric threshold | Codex는 current rerun 범위로 한정하여 이전 세션 분석 생략 |
| P0: CW contradiction_types 피드백 강화 | 표 D P0 | A-4 활용 — CW에 모순 유형 명시 전달 | Codex는 failure bucket 개념을 언급하나 CW 피드백 경로까지 명시하지 않음 |
| P1: Firewall 트리거 시 Director 재확인 round | 표 D P1 | Director 주권 존중 + Firewall 안전망 유지 | Codex는 gate 위치 이동으로 해결하려 하여 재확인 경로 불필요로 판단한 것으로 추정 |

### 3-2. Codex만 발견

| 항목 | Codex 위치 | 내용 | OPUS에 없는 이유 |
|---|---|---|---|
| RC-1: single-round floor cost (5~9분) = confirmed bottleneck | RC-1 | 1회 round 자체의 고정 비용이 높다. retry 없어도 ep당 최소 5분 | OPUS는 retry 횟수에 집중하여 기저 비용을 독립 RC로 분리하지 않음 |
| RC-4: Stage 2+3 고정 오버헤드 (Arc당 12~13분) = supporting contributor | RC-4 | Arc 추가 시 S4 외에도 S2+S3로 12~13분 추가 | OPUS는 표 B에서 수치를 기술했으나 별도 RC로 승격하지 않음 |
| RC-6: interrupted session의 저장소 간 시차 = supporting contributor | RC-6 | stage_attempts vs episode_production.jsonl 간 시차 | OPUS는 관측성 한계를 RC-5(pass_rate_monitor)로만 다룸 |
| P1: 3-candidate fanout 축소 | 표 D P1 | 상황별 fanout 조정으로 single-round floor 자체를 낮춤 | OPUS는 Firewall 라우팅 변경에 집중하여 fanout 변경은 다루지 않음 |
| P1: self-critique/advisory depth 차등화 | 표 D P1 | failure bucket 기반 검사 깊이 조정 | OPUS는 P2 계측 항목으로만 언급 |
| 정밀한 Stage 3 duration 추정 | 표 B | 320.6s / 345.9s (로그 span 기반) | OPUS는 ep당 150s 고정 추정 사용 |
| quality_metrics.jsonl 관측 수치 | 관측 요약 | retrieval_observation=36+15, validation=29+10 | OPUS는 Appendix A-1 참조로만 언급 |

---

## 종합 판정

### 사실 층 (표 A/B)
**Stage 4 전 12행의 verdict/score/duration은 완전 합의.** 차이는 Stage 2/3 duration 추정 방법(OPUS 고정값 vs Codex 로그 span 기반)과 S4 Arc 2 pass_count(OPUS 2 vs Codex 3, ep7 PASS_WITH_FIX 카운트 여부)에 한정된다.

### 해석 층 (표 C)
**3대 bottleneck 방향은 합의**: Firewall 반복, post-select 폐기, Stage 4 비중. 차이는 기저 비용(Codex RC-1)의 독립 분류 여부와 post-select의 taxonomy 등급(OPUS supporting vs Codex confirmed).

### 개선 층 (표 D)
**P0 방향 합의**: post-select/Firewall REJECT 후 full rewrite 대신 patch 직행. OPUS는 라우팅 변경(InPlace 허용), Codex는 타이밍 변경(gate 앞단 이동)으로 접근. **둘 다 적용 시 상승 효과 기대.**

### OPUS가 Codex에서 수용할 항목
1. **RC-1 (single-round floor cost)**: 별도 confirmed bottleneck으로 승격 타당
2. **Stage 3 duration**: Codex의 로그 span 기반 추정이 더 정밀
3. **P1 fanout 축소**: 기저 비용 자체를 낮추는 구조적 개선으로 유효
4. **ep7 pass_count**: episode_production.jsonl 근거가 있다면 Codex의 3이 정확

### OPUS가 유지할 항목
1. **RC-10 (Director 주권 충돌)**: Firewall이 Director의 명시적 false positive 판단을 무시한 사례는 별도 분리할 가치가 있음
2. **RC-9 (토큰 증가 정량화)**: ep당 60~125% 증가는 비용 예측에 필수적 수치
3. **Session 분리 관측**: 3개 세션의 데이터 혼재를 명시하는 것은 cross-check 신뢰도에 기여
4. **P0 contradiction_types 피드백**: CW에 모순 유형을 명시 전달하는 것은 gate 이동과 독립적으로 유효
