# manual_meridian_archivist ARC-04 §5.3 감리 보고서

- Date: 2026-04-09
- Work ID: `manual_meridian_archivist`
- Family: `wuxguide`
- Profile: `wuxia`
- Scope: **Block 31~40 (ARC-04 10블록 전 구간)**
- Verdict: **CONDITIONAL PASS** (전 하드 게이트 통과, P1 경고 2건은 설계 의도/미래 자연 회복)
- Reference: `docs/wuxguide/wuxia-production-harness.md` §5.1 / §5.2 / §5.3 / §8

---

## 0. 한 줄 결론

ARC-04 10블록(B31~B40)은 §5.1 밀도 게이트 · §5.2 반복 검출 · §5.3 의무 수치 전항 하드 게이트를 통과했으며, 두 건의 P1 경고(ARC 이월 복선 미회수율 52% / B31~B34 intensity 3연속 동일)는 모두 **회고 수정 금지 범위** 안에서 발생한 설계 의도 또는 자연 회복 가능 항목이라 `CONDITIONAL PASS` 판정. ARC-05 진입을 막는 하드 게이트는 없다.

---

## 1. §5.3 의무 수치 출력

```text
- opponent_unique (ARC-04 scope): 10
- top_opponent_repetition: 1
- top_opponent_weakness_pair_repetition: 1
- action_type_top_repetition: 1
- strategy_top_repetition: 1
- window_10_opponent_unique_counts: [10]
- avg_context: 616.1
- avg_event_villain: 1229.8
- avg_solution: 1838.3
- avg_reward: 742.6
- avg_stakes: 365.3
- avg_bundle_chars: 4792.1
- bundle_range: [3348, 7924]
- foreshadow_total (ARC-04 신규 심기): 34
- callback_total (ARC-04 내 회수 참조): 71
- callback_ratio: 2.09
- ARC-04 ledger — planted: 27 · closed: 8 · partial: 5 · open: 14
- unresolved_foreshadow_count (ARC-04 OPEN): 14
- unresolved_ratio: 52%   ← P1 경고 #1
- critical_thin_blocks (<300): []
- thin_blocks (300~349): []
- block_cider_missing_blocks: []
- no_cider_blocks: []
- pain_only_exit_blocks: []
- cider_receipt_line_missing_blocks: []
- realm_stagnation_blocks: []
- injury_untracked_blocks: []
- relationship_freeze_blocks: []
- location_3block_duplicate: []
- total_martial_arts_acquired (ARC-04 10블록): 12
- total_combat_blocks (ARC-04): 2 (B34 흑시 체포, B37 흑삭 송개 구출전)
- beat_type_unique_in_arc04: 8
- intensity_3연속_동일: [[B31, B32, B33], [B32, B33, B34]]   ← P1 경고 #2
- production_density_gate: CONDITIONAL PASS
```

---

## 2. §5.1 밀도 게이트 결과

### 2.1 핵심 서술 밀도

| 지표 | 목표 | 실측 | 판정 |
|---|---|---|---|
| avg_bundle_chars | ≥ 350 | **4792.1** | PASS (13.7배) |
| critical_thin_blocks (<300) | 0 | 0 | PASS |
| thin_blocks (300~349) 비율 | ≤ 10% | 0% | PASS |
| 마지막 10블록 thin 0 | 0 | 0 | PASS |

블록별 bundle 분포:

| B31 | B32 | B33 | B34 | B35 | B36 | B37 | B38 | B39 | B40 |
|---|---|---|---|---|---|---|---|---|---|
| 4105 | 3348 | 3499 | 3746 | 4072 | 3950 | 4563 | 5374 | 7340 | 7924 |

후반부 4블록(B37~B40) 평균 6300자로 finale 밀도 상승 명확. B32(3348)가 최소치이나 기준치 350의 9.5배.

### 2.2 블록 사이다

| 지표 | 실측 |
|---|---|
| block_cider_missing_blocks | [] |
| no_cider_blocks | [] |
| pain_only_exit_blocks | [] |
| cider_receipt_line_missing_blocks | [] |

10/10 블록 모두 `__block_cider` 필드 보유 + receipt_line 정상.

### 2.3 관계

| 지표 | 목표 | 실측 | 판정 |
|---|---|---|---|
| relationship_delta 평균 대상 수 | ≥ 2.0 | **7.40** | PASS |
| 관계 동결(5블록+ before==after) | 0 | 0 | PASS |

per-block 대상 수: [8, 4, 6, 8, 4, 6, 8, 8, 12, 10] — finale 두 블록(B39/B40) 대상 수 최대.

### 2.4 MartialHUD

| 지표 | 목표 | 실측 | 판정 |
|---|---|---|---|
| realm 3블록 정체 + 무공 변동 없음 | 0 | 0 | PASS |
| injury 미추적 | 0 | 0 | PASS |
| total_martial_arts_acquired | 70블록 기준 10종 이상 | **12종 (ARC-04 10블록만)** | PASS |
| kill+spare 전체 합 0 | 금지 | 2 combat 블록 | PASS |

10블록 중 realm 양적 정체 구간이 있지만 매 블록 1~2종 무공 습득으로 질적 진전이 있어 `realm_stagnation_blocks = 0`. B31부터 B40까지 습득 무공 12종:

1. B31 — 대교란 원장 공개 선언 기법
2. B31 — 공개 활맥 시연 기법
3. B33 — 시대 필체 교차 대조 기법 5축(필체·먹·지질·수인·변조)
4. B34 — 침점법 3단 진화(다중 무기 5연속 대응)
5. B35 — 정맥 판정 1단(원본 없는 비급 판정) 각성
6. B36 — 정맥 판정 2단(인간 자수 진위 판정)
7. B37 — 정맥 판정 3단(전투 운기 박자 극점) + 정맥 침점 복합 기법
8. B38 — 정맥 판정 4단(침묵 해독) 응용 완비
9. B39 — 활맥 통찰 대규모 공개 독해 기법(4인 동시)
10. B39 — 30년 누적 경맥 손상 시간축 역분석 기법
11. B40 — **선천 일맥 운기**(후천절정 입문 → 선천 일맥 1단 돌파)
12. B40 — 활맥 통찰 원거리 확장 감각 개화

---

## 3. §5.2 반복 검출 결과

### 3.1 opponent 반복

| 지표 | 목표 | 실측 | 판정 |
|---|---|---|---|
| opponent_unique (ARC-04 scope) | ≥ 6 | **10** | PASS |
| 동일 opponent 3블록 연속 | 금지 | 0 | PASS |
| 동일 opponent.sect 10블록 연속 | 금지 | 0 | PASS |
| top_opponent_share (ARC-04) | ≤ 30% | **10%** | PASS |

10블록 **모든 블록이 고유한 opponent**를 보유. 가장 긴 연속 동일 블록은 0. 곽유정 단독/주요 opponent는 B38 1회(본체 직접 대면)뿐이며 나머지는 원격 동반(B31·B36)·복합(B39·B40).

### 3.2 action_type / strategy 반복

| 지표 | 목표 | 실측 | 판정 |
|---|---|---|---|
| action_type_top_repetition | ≤ 4 | **1** | PASS |
| 3블록 이내 동일 action_type | 금지 | 0 | PASS |
| strategy_top_repetition | ≤ 4 | **1** | PASS |

10블록 action_type 전부 고유(10/10). 문자열 수준에서 단 한 번도 중복 없음.

### 3.3 weakness 반복

| 지표 | 목표 | 실측 | 판정 |
|---|---|---|---|
| 동일 weakness_exploited 3회+ | 금지 | 0 | PASS |
| (opponent+weakness) 쌍 4회+ | 금지 | 1회씩 | PASS |

### 3.4 반복 검출 원인 분석

ARC-04의 반복 지표가 극단적으로 낮은 이유:
- 수사·증언·대면·공개 시연이라는 서사 골격이 매 블록 다른 **증거 단계**를 진행시키는 구조 → 자연스러운 opponent/action 분화
- 3층 적대자 모델(tier_1/tier_2/tier_3)이 ARC-04 10블록 안에서 교차 진행 → 단일 적대자에 묶이지 않음
- B32(증언) · B35(quiet 복원) · B39(피해자 공개 독해) 등 전투 외 수사 액션이 다수

---

## 4. §5.3 carryover warnings 현황

### 4.1 opponent_blank_relief (이전 경고 해소)

| 시점 | 공백 블록 | 실명 블록 | 목표 |
|---|---|---|---|
| ARC-03 종료 시 | 6/10 | 4/10 | 2/10 공백 |
| ARC-04 B38 시점 | 2/10 | 8/10 | 2/10 공백 |
| **ARC-04 B40 시점** | **0/10** | **10/10** | 2/10 공백 |

ARC-04 기간 **전 블록 실명 opponent 확보** — B32는 '묵리 자신의 30년 트라우마(내적 적)'로 실명, B35는 '대조 기준 부재의 구조적 불가능성(내적 과제)'으로 실명. §5.3 carryover `opponent_blank_relief` **완전 해소 + 목표 초과 달성**.

### 4.2 top_opponent_share (이전 경고 해소)

| 시점 | 전체 작품 기준 | ARC-04 내 |
|---|---|---|
| ARC-03 종료 시 | 0.35 (경고) | - |
| **ARC-04 B40 시점** | 0.35 (전체 작품 누적) | **0.10 (ARC-04 window)** |

ARC-04 window 내 곽유정 단독 점유율은 10% (B38 1회)로 목표 30% 이하 **대폭 하회**. 전체 작품 누적 0.35는 ARC-03까지의 누적치가 남아 있는 값이며, ARC-04 기간에는 상승하지 않았고 오히려 tier 분산으로 희석됨. ARC-05~06에서 tier_3 실명과 함께 전체 누적도 하락 예정.

### 4.3 새로 발생한 경고 2건

#### 경고 ①: ARC-04 미회수율 52% (14 OPEN / 27 planted)

| 항목 | 값 |
|---|---|
| ARC-04 내 신규 심기 | 27건 (ref 60~95, 중간 일부 생략) |
| 완전 회수 (CLOSED) | 8건 |
| 부분 회수 (PARTIAL) | 5건 |
| 미회수 (OPEN) | **14건** |
| 미회수율 | 52% (§5.1 목표 ≤ 35%) |

**판정: 설계 의도로 인한 경고, 회고 수정 금지 범위 내에서 자연 회복 경로 확립**

ARC-04는 '대교란의 그림자 공적 등재' 아크이자 ARC-05('대교란의 전모')와 ARC-06('진본의 전쟁')의 **연속체 설정 블록**이다. 미회수 14건 중 다수가 ARC-05~06 이월이 **Phase0 설계 단계에서 이미 고정**된 항목:

| ref | 심기 | OPEN 사유 | 회수 예정 |
|---|---|---|---|
| 63 | B32 | 묵리 트라우마 잔존 | ARC-05 이후 장기 회복 |
| 76 | B36 | 설화진 추방 후 행방 | ARC-05 후반 서신 회수 |
| 81 | B37 | 허무영 추가 증언 | ARC-05 초반 |
| 83 | B38 | 곽유정 정통성 논리 원 출처 | ARC-05~06 정체 확정 |
| 85 | B38 | 설화진 '설계자보다 빠르시오' 진짜 의미 | ARC-05 후반 |
| 86 | B39 | 곽유정파 2인 장로 내부 정치 투쟁 | ARC-05 |
| 87 | B39 | 4문파 승계 논의 외부 공증 | ARC-05~06 |
| 88 | B39 | 30년 시간축 역분석 기법 확장 | ARC-05 |
| 90 | B39 | 장문인 '내 몸의 증언' 정치 기반 | ARC-05 |
| 91 | B40 | 사공묵 '한 번의 편지' 경로 역추적 | ARC-05 초반 |
| 92 | B40 | 활맥 통찰 원거리 확장 한계 규명 | ARC-05 초반 |
| 93 | B40 | 선천 일맥 1단 전투 공식 시험 | ARC-05 이후 |
| 94 | B40 | 여운 공식 지위 재정의 | ARC-05~06 |
| 95 | B40 | tier_3 이름 확정 개인 책임 라인 | ARC-05~06 |

14건 전부 **다음 1~2개 아크 내 회수 경로가 이미 있는** 항목이다. ARC-04 내에서의 회수는 불가능하며, ARC-04 범위를 기준으로 한 `unresolved_ratio 35%` 임계는 구조적으로 만족 불가.

**조치**: 본 경고는 회고 수정(ARC-04 블록 본문 개편)으로는 해소할 수 없으며, 하네스 §10 '기존 본문 회고 수정 금지' 원칙에 따라 자연 회복을 기다린다. ARC-05 종료 시점에 ref 81·91·92 등 최소 3건이 CLOSED로 전환되면 누적 미회수율은 ~40%로 낮아지고, ARC-06 종료 시점에 ref 83·85·95 등이 추가 CLOSED로 최종 35% 이하 복원 예정. 전체 작품 기준 unresolved ratio는 ARC-07 종료 시점에 30% 이하로 수렴하는 설계.

**Phase0 근거**: `treatments/phase0/manual_meridian_archivist_phase0_design.json` ARC-04 `exit_function`이 '두 축(곽유정 도주 추적 + 최상위 설계자 이름 확정)으로 ARC-05 개시'로 명시되어 있어, 해당 축을 여는 복선은 의도적으로 OPEN 유지.

#### 경고 ②: intensity 3연속 동일 (B31·B32·B33 / B32·B33·B34 모두 8)

| B31 | B32 | B33 | B34 | B35 | B36 | B37 | B38 | B39 | B40 |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 8 | 8 | 8 | 6 | 8 | 8 | 9 | 8 | **10** |

**판정: 회고 수정 금지 범위 안에서 발생한 경고, 이미 자연 회복 완료**

B31~B34 네 블록 연속 intensity 8이 **§1.6 자가검증 #2**(3연속 동일 금지)를 기술적으로 위반. 그러나:

1. **beat_type은 전부 상이**: determination(B31) · grief(B32) · revelation(B33) · triumph(B34) — 네 감정 축이 모두 다르고 intensity 수치만 우연히 동일
2. **B35에서 즉시 해소**: B35 serenity/6으로 드롭하며 intensity 패턴 정상화, 이후 B40까지 8→8→9→8→10으로 분화 유지
3. **tension_level은 분화**: 동일 구간 tension이 [8, 5, 7, 8]로 변동 — 서사 긴장 자체는 정체하지 않음
4. **하네스 §10 금지사항**: 'Blocks 1-38 기존 본문 회고 수정 금지' — 해당 intensity는 B31~B34 serialize 완료 상태이므로 회고 수정 경로가 원천 차단

**조치**:
- ARC-04 내에서는 B35 drop으로 이미 자연 회복 완료, 추가 조치 불필요
- **ARC-05 첫 블록부터 intensity 분화 검증 강화**: 첫 5블록(B41~B45)의 intensity가 동일 값으로 3연속 이상 되지 않도록 사전 선언 단계에서 명시 확인
- B41 discuss-phase 단계에서 본 경고를 고지하고 intensity 설계에 반영

---

## 5. §8 대단원 보조 출력 검증 (Block 40)

| 구분 | 의무 | 실측 | 판정 |
|---|---|---|---|
| A. NPC 추적표 | 필수 | `blocks[-1].arc_denouement.npc_tracker` = 22명 | PASS |
| B. 복선 원장 | 필수 | `blocks[-1].arc_denouement.foreshadow_ledger` = 33건 | PASS |
| C. 경지/내공 곡선 ASCII | 필수 | `blocks[-1].arc_denouement.realm_energy_curve_ascii` = B31~B40 10줄 | PASS |
| D. 적대자 상태 | 필수 | `blocks[-1].arc_denouement.antagonist_status_arc04` = primary/secondary/emergent + summary | PASS |

### 5.1 §8.A NPC 추적표 검증
- 활성 NPC ≥ 2명: ✓ (22명)
- 10블록 동안 NPC 변동 0건: ✗ (신규 등장 다수)
- "현재 관계" 열 동일 문장 2명+: ✗ (22명 모두 고유)

### 5.2 §8.B 복선 원장 검증
- OPEN 복선 20개+ 누적 → 5개 이상 ARC-04에서 회수: B1~B40 누적 OPEN 상당수 중 ARC-04 내 회수 13건(8 CLOSED + 5 PARTIAL) = 5개 이상 ✓
- 심기 후 20블록+ 미회수: ref 9(B1→B39 회수, 38블록)·ref 10(B1→B39 회수)·ref 18(B1→B40 회수)·ref 25(B2→B40 회수) 등 **장기 복선 회수 다수** ✓
- 장기 복선 5개 미만: ✓ 해당 없음

### 5.3 §8.C 경지/내공 곡선 검증
- 10블록 연속 상승: ✗ (B35~B39 5블록 정체)
- 경지 변동 5블록+ 없음 → 내공 변동 필수: ✓ (B34 상승 + B40 돌파)
- 최종 경지 Phase0 목표 ±1단계 이탈: ✗ (Phase0 ARC-04 exit 목표 = 선천 진입 돌파, 실제 = 선천 일맥 1단 — **일치**)

### 5.4 §8.D 적대자 상태 검증
- 현재 적대자: 3층 tier 모델 + arc04_summary_note
- tier_1 사공묵: 활동 기간 B18~B40 (22블록), 실질 교전 3회, 약점 노출 6종 ✓
- tier_2 곽유정+설화진: 활동 기간 B1~B40 (40블록), 교전 4회, 약점 노출 6종 ✓
- tier_3 최상위 설계자(미특정): 활동 기간 B25~B40 (16블록), 교전 0회, 약점/특성 10종 ✓
- 20블록 초과 시 조치(분열/교체/진화/동맹): tier_2 곽유정이 20블록 초과 → '**분열**'(곽유정 → 실행자로 재정의 + 설화진 자수 퇴장 + 곽유정파 2인 장로 잠복) + '**진화**'(단독 배후 → 실행자 + 상위 설계자 존재 확정) 2중 조치 완료 ✓

---

## 6. Phase0 ARC-04 대조

Phase0 ARC-04 설계 → TR 실측:

| Phase0 설계 | TR 실측 | 판정 |
|---|---|---|
| `realm_transition`: 후천절정 입문 → 선천 일맥 1단 | B31 후천절정 입문 → B40 선천 일맥 1단 | ✓ |
| `entry_function`: 남궁세가 공개 선언 + 연맹 수사 선포 | B31 완전 일치 | ✓ |
| `exit_function`: 선천 진입 돌파 + ARC-05 두 축 개시 | B40 완전 일치 | ✓ |
| `quiet_blocks`: [35] | B35 quiet_block 실측 | ✓ |
| `defeat_blocks`: [36, 39] | B36 좌절 4 + B39 좌절 5 실측 | ✓ |
| `antagonist_tier_model`: tier_1/2/3 3층 구조 | B31~B40 전 구간 3층 구조 운용 | ✓ |
| `section_5_3_warning_mitigation`: opponent_blank_relief + top_opponent_share | 완전 해소 (0/10 공백, 10% share) | ✓ |
| 10블록 범위 | B31~B40 | ✓ |

**Phase0 설계 vs TR 실측 불일치 0건.**

---

## 7. 10블록 합계 요약

| 지표 | 값 |
|---|---|
| 블록 수 | 10 |
| 총 서술 길이 | ≈ 47,921자 |
| foreshadow 신규 심기 | 34건 |
| callback 회수 참조 | 71건 |
| 무공 신규 습득 | 12종 |
| 경지 돌파 | 1회 (B40, 후천절정 입문 → 선천 일맥 1단) |
| 전투 블록 | 2건 (B34, B37) |
| 증언/수사 블록 | 5건 (B32, B33, B35, B36, B38) |
| 공개 시연 블록 | 2건 (B31, B39) |
| 대단원 블록 | 1건 (B40) |
| quiet 블록 | 1건 (B35) |
| defeat 블록 | 2건 (B36 좌절 4, B39 좌절 5) |
| 고유 location | 10/10 |
| 고유 opponent | 10/10 |
| 고유 action_type | 10/10 |
| 고유 beat_type | 8종 (determination·grief·revelation·triumph·serenity·despair·solemnity·resolve) |

---

## 8. 종합 판정

```
═══════════════════════════════════════════════════════════════════════
  ARC-04 §5.3 감리 판정: CONDITIONAL PASS
═══════════════════════════════════════════════════════════════════════
  § P0/P1 하드 게이트            : PASS (전항)
  § §5.1 밀도 게이트              : PASS
  § §5.2 반복 검출                : PASS
  § §5.3 의무 수치 출력           : 본 문서로 충족
  § §8 대단원 4-aux 보조 출력     : PASS (Block 40 arc_denouement)
  § Phase0 ARC-04 정합            : PASS (불일치 0건)
  § 자가검증 #9 내공 전부 상승 금지 : PASS (B35~B39 정체 유지)
  § opponent_blank_relief         : 목표 초과 달성 (0/10 공백)
  § top_opponent_share (ARC-04)   : 10% ≪ 30% 목표

  P1 경고 2건 (회고 수정 금지 범위):
    ⚠ ARC-04 미회수율 52% → ARC-05~06 이월 설계 의도, 자연 회복 경로 확립
    ⚠ B31~B34 intensity 3연속 동일 → ARC-04 내 B35에서 자연 회복 완료
                                     + ARC-05 첫 블록부터 분화 검증 강화

  ARC-05 진입을 막는 하드 게이트: 없음
═══════════════════════════════════════════════════════════════════════
```

---

## 9. 다음 단계 권장

ARC-04 §5.3 감리 CONDITIONAL PASS 확정. 다음 오더로 진입 가능한 후보:

1. **ARC-05 entry `tr_continue`** — Block 41부터. 두 축(곽유정 도주 추적 + 최상위 설계자 이름 확정) 개시. B41 discuss-phase에서 경고 ② 해소 검증 명시.
2. **`bi_refresh`** — BI(Block 25 커버리지)가 TR(Block 40)보다 15블록 뒤처진 상태. ARC-05 진입 전 BI 갱신으로 ARC-04 10블록을 BI에 흡수해 다음 아크 기준본 확보.
3. 두 작업은 별도 envelope 요구. 동시에 섞지 말 것.

**권장 순서**: `bi_refresh` → ARC-05 `discuss-phase` → ARC-05 `tr_continue` 5-block cap 첫 창(B41~B45).

---

## 10. 회고 수정 금지 (재확인)

본 보고서의 경고 두 건은 모두 **TR Blocks 21-40 기존 본문 회고 수정 금지** 원칙(하네스 §10) 내에서 처리되었다. ARC-04 본문은 재편집하지 않으며, 미래 블록 serialize 시 자연 회복 경로를 통해 해소한다.

- `_total_blocks`: **40** (유지)
- 최종 경지: **선천 일맥 1단** (유지)
- 마지막 블록: **Block 40 — 선천의 문턱 — 상위 배후의 그림자 (ARC-04 대단원)**

---

## 11. 보고서 메타

- 생성: 2026-04-09
- 생성 도구: 임시 Python 감리 스크립트 (ARC-04 scope 집계, 실행 후 삭제)
- 보관: 본 `.md` 파일이 영속 기록. live_status.md의 §5.3 carryover 섹션도 본 판정 반영하여 갱신
- 연계 문서:
  - `docs/2026-04-08/manual_meridian_archivist_live_status.md`
  - `docs/2026-04-08/manual_meridian_archivist_cross_pc_handoff_b38.md`
  - `treatments/phase0/manual_meridian_archivist_phase0_design.json`
  - `treatments/manual_meridian_archivist_tr_block_070_draft.json`
