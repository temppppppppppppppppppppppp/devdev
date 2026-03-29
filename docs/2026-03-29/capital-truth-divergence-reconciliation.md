# Capital Truth Divergence Reconciliation Survey

Date: 2026-03-29
Status: draft-for-audit
Scope: narrative pipeline — canary_0329_ep3_bp_patch_recheck, capital (자본금) truth source divergence
Canonical Path: `docs/2026-03-29/capital-truth-divergence-reconciliation.md`
Related: `docs/2026-03-29/bp-preflight-integrity-survey.md` (preflight report D-1 항목)

## 1. Purpose

BP preflight report에서 `TRUTH_SOURCE_DIVERGENCE`로 surface된 자본금 20억 vs 40억 불일치의 root cause를 식별하고, authoritative source를 판정하여 canary gating recommendation을 산출한다.

## 2. Truth Source Table

### 2.1 Manuscript Evidence (EP1~EP3 committed)

| Episode | Location | Exact Text | Capital Value |
| --- | --- | --- | --- |
| EP1 씬3 | `ep_0001.txt` L63 | `'20억.'` | 20억 원 |
| EP1 씬4 | `ep_0001.txt` L86 | `20억 원이 예치된 계좌의 OTP 카드` | 20억 원 |
| EP1 씬5 | `ep_0001.txt` L105 | `20억으로 60억 원 규모의 포지션을 구축한다` | 20억 원 (3X → 60억) |
| EP2 씬1 | `ep_0002.txt` L7-10 | OTP를 손에 쥐고 `20억 원이 예치된 법인 계좌` 참조 | 20억 원 |
| EP2 씬4 | `ep_0002.txt` L82-84 | `"정리하니 20억 원 정도 되더군요"` (한정호에게 직접 보고) | 20억 원 |
| EP3 씬3 | `ep_0003.txt` L59 | `잔고 '2,000,000,000원'` | 20억 원 |
| EP3 씬3 | `ep_0003.txt` L67 | `총자산 20억 중 15억을 증거금으로 사용` | 20억 원 |

**Manuscript verdict**: EP1~EP3 전 구간에서 자본금은 일관되게 **20억 원**. 증가/감소 이벤트 없음.

### 2.2 Persistent Store Evidence

| Store | Key | Value | Last EP | Notes |
| --- | --- | --- | --- | --- |
| fact_ledger | `numbers.capital.value` | **4,000,000,000** (40억) | 3 | `established_value: 2,000,000,000` (20억, ep1) |
| fact_ledger | `numbers.capital.history` | 8 entries (ep1~ep6 + duplicate ep1, ep3) | — | ep4~ep6 entries는 committed manuscript가 없는 canary 생성 episode |
| world_state | `protagonist.assets` | `""` (empty) | 3 | capital 수치 미기록 |
| world_state | `active_items` | OTP/인감 보유, 컴퓨터/모니터 소실 | 3 | 금액 수치 없음 |
| chain_link_1 | `pending_actions` | `20억 원의 자금 존재를 가족에게 숨겨야` | 1 | 20억 참조 |
| chain_link_2 | — | capital 수치 미언급 | 2 | — |
| chain_link_3 | — | capital 수치 미언급 | 3 | — |
| bible | — | capital 수치 미확인 | — | 프로젝트 설정 레벨 |

### 2.3 DB Artifact Evidence (canary-origin contamination markers)

| Artifact | Exists | Timestamp | Source |
| --- | --- | --- | --- |
| chain_link_4 | YES | 2026-03-23 22:25:08 | 원본 프로젝트 canary run |
| chain_link_5 | YES | 2026-03-23 22:40:33 | 원본 프로젝트 canary run |
| chain_link_6 | YES | 2026-03-23 22:58:41 | 원본 프로젝트 canary run |
| chain_link_7 | YES | 2026-03-23 23:40:48 | 원본 프로젝트 canary run |
| fact_ledger | — | 2026-03-29 04:31:43 | canary prep 시 재생성 |
| world_state | — | 2026-03-29 04:31:43 | canary prep 시 재생성 |

committed manuscript는 EP1~EP3 (3건)만 존재하나, DB에는 chain_link_4~7과 fact_ledger history ep4~ep6 entries가 남아 있다. 이는 원본 프로젝트(2026-03-23)의 canary run이 EP4~EP7까지 생성하면서 DB에 기록한 잔재이다.

## 3. Divergence Timeline

| Step | Timestamp | Event | Capital State |
| --- | --- | --- | --- |
| 1 | 2026-03-23 ~20:24 | 원본 프로젝트 최초 생성, EP1 run | fact_ledger capital = 20억 (established) |
| 2 | 2026-03-23 ~20:28–23:40 | 원본 프로젝트 EP2~EP7 연속 run (canary 포함) | fact_ledger history에 ep1~ep6 entries 누적 (6건) |
| 3 | 2026-03-29 ~02:54 | `canary_0329_ep3_bp_patch_recheck` 생성, EP1~EP3 재처리 시작 | chain_link_1 재생성 (02:54:55) |
| 4 | 2026-03-29 ~04:31 | EP3 commit 처리 완료, fact_ledger/world_state 재기록 | fact_ledger history에 ep1, ep3 entries **추가** (기존 6건 + 2건 = 8건) |
| 5 | 2026-03-29 ~04:31 | fact_ledger capital value = **40억** | **drift 발생 지점** |

## 4. Probable Drift Origin

### Primary Cause: Double-Extraction Accumulation

fact_ledger의 `numbers.capital` history에는 8건의 extraction 기록이 있다:
```
ep1, ep2, ep3, ep4, ep5, ep6  ← 원본 프로젝트 run (2026-03-23)
ep1, ep3                       ← canary prep re-run (2026-03-29)
```

canary prep 과정에서 EP1~EP3를 재처리할 때, fact_ledger의 기존 history를 초기화하지 않고 **append**했다. financial scalar extractor가 EP1 manuscript에서 "20억"을 재추출하면서, 기존 value(20억)에 **누적**하여 40억이 된 것으로 판단된다.

### Supporting Evidence

1. `established_value`(20억)와 `value`(40억)의 정확히 2배 관계 — 동일 source(EP1의 20억)가 2회 추출된 결과와 일치
2. EP1~EP3 manuscript 전 구간에서 자본금 증가 이벤트가 단 한 건도 없음 — 서사적으로 40억이 될 근거 없음
3. chain_link_4~7이 DB에 잔존 — fact_ledger의 ep4~ep6 history entries도 같은 원본 run에서 유래한 잔재
4. fact_ledger timestamp(04:31:43)이 chain_link_3(04:31:43), world_state(04:31:43)과 동일 — EP3 commit cycle에서 일괄 재기록됨

### Secondary Factor: Incomplete DB Reset

canary prep 시 chain_link_1~3은 재생성했으나, chain_link_4~7은 삭제하지 않았다. fact_ledger 역시 기존 history를 flush하지 않고 append했다. 이는 `prepare_canary`의 DB reset scope가 committed episode 관련 anchor만 덮어쓰고, fact_ledger의 내부 history array까지는 초기화하지 않기 때문으로 추정된다.

## 5. Authoritative Source Recommendation

| Priority | Source | Value | Verdict |
| --- | --- | --- | --- |
| 1 | Committed manuscript (EP1~EP3) | **20억 원** 일관 | **AUTHORITATIVE** |
| 2 | chain_link_1 | 20억 참조 | consistent with manuscript |
| 3 | fact_ledger | 40억 | **DRIFTED** — double-extraction artifact |
| 4 | world_state | 미기록 | N/A |

**Authoritative capital value: 20억 원 (2,000,000,000원)**

fact_ledger의 40억은 extraction pipeline artifact이며, 서사적 근거가 없다. Manuscript는 최고 우선순위 truth source이고, 3개 화에 걸쳐 6회 이상 20억을 일관되게 명시하고 있다.

## 6. Canary Gating Recommendation

### Before Next Canary

1. **fact_ledger capital 수정**: `numbers.capital.value`를 `2,000,000,000`으로 교정하고, history에서 중복/orphan entries를 제거해야 한다
2. **orphan chain_link 정리**: chain_link_4~7은 committed manuscript가 없는 잔재이므로 삭제 대상이다
3. **fact_ledger ep4~ep6 history entries 제거**: committed manuscript가 뒷받침하지 않는 extraction 기록이므로 제거 대상이다

### Gating Decision

| Condition | Canary OK? |
| --- | --- |
| fact_ledger 미교정 + BP 미패치 | **NO** — CF-1/CF-3/CF-6 + divergence blocking |
| BP 패치 완료 + fact_ledger 미교정 | **NO** — Director/ChiefWriter가 fact_ledger 40억을 참조하면 manuscript truth와 충돌하는 context를 받게 됨 |
| BP 패치 완료 + fact_ledger 교정 완료 | **YES** — canary 진행 가능 |
| fact_ledger 교정 완료 + BP 미패치 | **NO** — CF-1/CF-3/CF-6이 여전히 blocking |

**결론**: BP patch와 fact_ledger reconciliation이 **모두** 완료된 후에만 canary를 태워야 한다. 둘 중 하나만 수행하면 canary가 불일치한 truth context 위에서 동작하게 된다.

### Reconciliation Scope

- fact_ledger `numbers.capital`: value → 2,000,000,000, history deduplicate
- chain_link_4~7: delete (orphan)
- fact_ledger history: ep4~ep6 entries remove (orphan)
- 위 작업은 DB anchor 수정이며, Python 코드 수정이 아님
- 이 문서는 수정의 근거를 제공하지만, 수정 자체는 별도 execution turn에서 수행

## 7. Divergence Family Classification

| Family | Description | This Case |
| --- | --- | --- |
| **Extraction Accumulation** | 동일 source를 중복 추출하여 scalar가 n배로 팽창 | **YES** — 20억 × 2회 추출 = 40억 |
| Extraction Misparse | source text를 잘못 파싱하여 다른 수치 산출 | NO — 20억을 정확히 추출했으나 누적 로직이 문제 |
| Cross-Episode Confusion | 다른 episode의 수치를 현재 episode에 귀속 | NO — 모든 episode가 동일 수치(20억) |
| Canary Bleed-Through | canary-generated data가 committed truth store에 잔류 | **YES (secondary)** — ep4~ep6 history entries, chain_link_4~7 |
| Source Authority Conflict | 두 authoritative source가 다른 값을 주장 | NO — manuscript가 유일한 authoritative source, fact_ledger는 derived store |
