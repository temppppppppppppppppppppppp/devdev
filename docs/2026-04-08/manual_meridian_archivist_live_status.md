# manual_meridian_archivist live status

Date: 2026-04-08
Status: current operator truth
Work ID: `manual_meridian_archivist`
Family: `wuxguide`

## 1. Operator Reading

- inventory role: `unslotted_live_pair`
- operational state: `new_live_pair`
- schema status: `pass`
- benchmark alias: `GREEN`
- benchmark freshness: `current`
- canonical registry anchor:
  - `material_ssot/00_governance/production-pair-operational-registry-v1.md`

## 2. Current Live Artifacts

- canon pitch:
  - `material_ssot/20_pitch/canon/manual_meridian_archivist.md`
- preprocess bundle:
  - `treatments/preprocess/manual_meridian_archivist/`
- root Phase0:
  - `treatments/phase0/manual_meridian_archivist_phase0_design.json`
- published work_guard:
  - `work_guards/11_manual_meridian_archivist.yaml`
- live TR:
  - `treatments/manual_meridian_archivist_tr_block_070_draft.json`
  - saved live boundary: **Block 1-47** (ARC-03 finale B30 + ARC-04 10블록 B31~B40 + **ARC-05 7블록 B41~B47 완료**, ARC-05 진행 7/10, 첫 5-block cap 창 B41~B45 5/5 완료 + **두 번째 5-block cap 창 B46~B50 2/5 진행(B46·B47)**, 여운 경지 **선천 일맥 1단 + 조맥 재편 입문 전조 감각 3회 심화(B44 첫 체감→B46 운용 원칙 확정→B47 안정 구간 한 호흡 박자 직전 일시 확장)**)
  - B46·B47 audit PASS (2026-04-09, 본 파일 §7): schema 무결 + tension/intensity 3연속 금지 룰 준수 + 5/5 차별화 B45↔B46↔B47 전량 충족 + realm 정체 정책 준수 + FS/CB 회계 정합(ref 1 46블록 호선 회수 + ref 109 단조 진행)
- live BI:
  - `bible/manual_meridian_archivist_bi.json`
  - BI refreshed: **2026-04-09** (`_last_updated`=2026-04-09, `projection_block_count`=40, `last_confirmed_block`=40)
  - plot_roadmap 1:1 TR 재투영 완료 (40블록 전량)
  - MartialHUD.Protagonist: 선천 일맥 1단(선천 초입) + 장로회 명의 ARC-05 수사 주체 공식 위임자 + martial_arts 37종 누적
  - WorldState: 2년차 초봄 중순 말 + 태허검문 본각 + internal_energy_curve B34~B40 갱신(B40 대도약=선천 진입)
  - ArcSheets[3] ARC-04: block_range=31-40 + 3층 tier 적대자 모델 등재 + B36/B39 defeat_blocks + §5.3 감리 CONDITIONAL PASS + arc_denouement_attached 메모
  - KeyNPCs final_status: 한설·설화진·도연화·곽유정·백사검·묵리·풍잔운·사공묵·허무영·이청하·진여운 11명 B40 endcap 갱신
  - FactionMap: allies 10개 채움(빈 상태 해소) + enemies tier_1/2/3 분화
  - _authority_chain / ProjectData / protagonist_config / Treasures(17) / HistoricalEvents(7) / GenreRules / KeyItems 미변경(무결성 유지)

## 3. Boundary Rule

- the live TR truth ends at **Block 47** — ARC-04 진행 10/10(종료) + **ARC-05 진행 7/10**, ARC-05 첫 5-block cap 창 B41~B45 완료 + 두 번째 5-block cap 창 B46~B50 2/5 진행 중(B46·B47 완료, B48~B50 남음)
- Block 30에 ARC-03 finale 4-aux dénouement(`arc_denouement`) 부착 완료
- Block 40에 ARC-04 finale 4-aux dénouement 적재 완료 (npc_tracker 22명 · foreshadow_ledger 33건 · realm_energy_curve_ascii B31~B40 10줄 · antagonist_status_arc04 3-tier 구조)
- Block 50에 ARC-05 finale 4-aux dénouement 적재 의무 예정 (다음 5-block cap 창 B46~B50 serialize 시)
- Phase0 ARC-04는 2026-04-08 reconciled 상태로 3층 적대자 모델(tier_1/tier_2/tier_3) 등재 완료
- 크로스 PC 핸드오프: `docs/2026-04-08/manual_meridian_archivist_cross_pc_handoff_b38.md`를 기준본으로 재개
- `docs/2026-04-06/manual_meridian_archivist_context_handoff_b22.md`와 `manual_meridian_archivist_context_handoff_b26.md`는 역사적 가이드, B22~B30 serialize로 완전 대체됨

## 4. Next Allowed Tasks

- 선행 조건 모두 충족 (2026-04-09 기준):
  - [x] wuxguide §5.3 감리 보고서 ARC-03 → **CONDITIONAL PASS** (전 하드 게이트 통과, 2건 P1 경고는 ARC-04 슬롯 배치로 자연 회복 중)
  - [x] Phase0 ARC-04 reconciled (B31 seam 수용 + 3층 적대자 모델 + quiet [35] + defeat [36, 39])
  - [x] **wuxguide §5.3 감리 보고서 ARC-04 → CONDITIONAL PASS** (2026-04-09, `docs/2026-04-08/manual_meridian_archivist_arc04_section53_audit.md`. 전 하드 게이트 통과, 2건 P1 경고 = ARC 이월 미회수율 52% + B31~B34 intensity 3연속 동일. 모두 회고 수정 금지 범위 내 설계 의도/자연 회복)
- **현재 진행**: ARC-05 `tr_continue` 두 번째 5-block cap 창 **B46~B50**, **2/5 완료** (B46·B47 머지, B48·B49·B50 남음)
- **한도 리셋 직후 B48 serialize 재개 예정, 크로스 PC 핸드오프: `docs/2026-04-09/manual_meridian_archivist_cross_pc_handoff_b47.md` 참조**
- 남은 오더:
  - B48 defeat 7 (곽유정파 진본 무장 역공 — 곽유정 실명 opponent 재등장으로 ARC-05 window opponent_blank 즉시 회복)
  - B49 묵리 각성 (떠돌이의 결의)
  - **B50 ARC-05 finale + `arc_denouement` 4-aux 의무 적재 + 선천중기 돌파 + 조맥 재편 입문 완전 각성**(ref 121·127 완전 회수 예정)
  - ARC-05 10블록 전 구간 완결 후 §5.3 감리 재실행 권장
  - `bi_refresh`는 ARC-05 완전 종료 후 별도 envelope로 재실행 가능
- ARC-05 B41~B47 요약:
  - **B41** 곽유정 도주 — 북서 방향 공적 확정 + 선천 원거리 확장 감각 기준선(안정 20리·한계 25리·두 시진 휴식) + 경맥 박자 서명 추적 기법 신규 + 연맹 판관부 긴급 공증으로 대교란 전모 강호 공개 첫 계기 + 종리 장로 단편 증언(tier_3 거처 방향 북서) → 두 축 경로 통합 가능성. ref 82 CLOSED, ref 86/91/92 PARTIAL
  - **B42** 정파 연맹 본부 7문파 공동 불매 대회의 → 한설 장로 '과거 불매 + 미래 공적 복원 신뢰 축' 이중 구조 제안 만장일치 가결 + 여운 **연맹 본부 공증 기록상 공식 복원 주체** 등재 + 복원 절차 공적 표준화 + 첫 대상 '점창파 비급' 공식 선택 + 정맥 판정 2단 정치 응용 각성. ref 94 CLOSED, ref 101~104 신규
  - **B43** 본각 앞마당 강호 공개 결단 선언 — 43건 누적 실적표 공개 + 무작위 7건 검증 + 복수 사본 대조 기법 실전 시연 + 강호 공증 증인(낙양 우자방) + 이중 공증 구조 완성 + 강호 공개 결단 선언 기법 신규 습득. ref 105~108 신규
  - **B44** 점창파 청풍검결 제3권 공개 복원·검증 세션 — 석무광 장문인 반 갑자 내공 차이 물리 증명 + 5중 공증 + B27 ref 48 공적 복권 물리 단계 + **조맥 재편 입문 전조 감각 첫 체감**(Phase0 `restoration_sense_transition` 첫 발현) + 변조 비급 복원 전후 시연 비교 검증 기법 신규. ref 93/105 PARTIAL, ref 109~113 신규
  - **B45 좌절 6** 곽유정 도주 후 첫 반격 — 낙양·항주·장안 3지역 '3점+1점 누락' 살상 위조 복원본 유포 + 낙양 중상 수련자 + 도연화 긴급 급파 + 본각 공개 진위 판정 세션 4축 구별점 공적 표준화 + **결맥 인장 B42 선제 진본 식별점 공적 공개** + 연맹 판관부 '위조본에 B43 공적 책임 미적용' 공식 판정 + **곽유정 측 본각 외부 강호 내부 정보 창구 공적 확정** → ARC-05 수사 세 번째 축 공식 개시 + 복원본 자기 명의 위조 역추적 기법 신규. ref 103/107 구조적 방어, ref 113 CLOSED, ref 114~118 신규
  - **B46 quiet_block** 문파의 선택 — 백사검 장문인 공식 퇴임(검법 붕괴 이후 문파 기준점을 새 자리로 이양) + 한설 장로 권한 대행 정식 취임 + **태허검문 「비급 총관(秘笈總管)」 직명 창설·여운 정식 임명**(외문 서고 비급 전부 + 강호 외부 공적 복원·검증 비급 전부의 수호·판정·전수 권한 통합) + 조맥 재편 입문 전조 감각 두 번째 내면 체감 + 안정 구간 측정(한 호흡 반~두 호흡) + 운용 원칙 확정. **ref 1 (B1 외문 서고지기) 46블록 호선 완전 회수**, ref 9/10/40/44/109/20 CLOSED, ref 119~123 신규. tension 3 / respite 4 (B45 좌절 6 직후 quiet 배치)
  - **B47** 비급 검증 체계 — 여운의 설계 — **강호 공식 비급 검증 체계 5부 구조**(제1부 복원 5단계 표준화 + 제2부 4축 구별점 + 제3부 결맥 인장 규정 + 제4부 3경로 접수 창구[연맹 본부·남궁세가·점창파] + 제5부 낙양 우자방 강호 자발 공증 증인 네트워크 공식 편입) 설계·반포 + **연맹 본부 맹주의 '결맥 인장 = 정통성 공식 증표' 인증 선언** + 4문파 전령 강호 전역 동시 반포 + 조맥 재편 입문 전조 감각 세 번째 시도에서 안정 구간 '한 호흡 박자 직전' 일시 확장(각성 기준점 1단계 도달). 과거 기법 B16·B33·B35·B42~B45 전량 5부 구조로 재통합. ref 42/44/45/46/105 CLOSED/편입, ref 109 PARTIAL 2단계, ref 124~128 신규. tension 5 / realization 6
- `bi_refresh`:
  - 별도 envelope에서 허용 (live TR이 Block 25 너머로 진전). `tr_continue`와 같은 오더에 섞지 말 것
- §5.3 carryover warnings (TR 21-40 회고 수정 금지, 미래 슬롯 배치로만 해소):
  - **opponent_blank_relief**: ARC-04 10블록 **실명 보유 10/10** (B32 내적 적 = 묵리 30년 트라우마 / B35 내적 과제 = 대조 기준 부재로 실명 처리) → **목표 초과 달성, 경고 완전 해소**
  - **top_opponent_share_relief**: ARC-04 window 내 곽유정 단독 점유율 **10%** (B38 본체 대면 1회만, B31·B36 원격, B39·B40 등장 없음). 30% 목표 대폭 하회, ARC-04 내에서는 해소. 전체 작품 누적 0.35는 ARC-05~06 tier_3 실명과 함께 하락 예정
  - **새 경고 ① ARC-04 미회수율 52%** (14 OPEN / 27 planted): ref 63/76/81/83/85/86/87/88/90/91/92/93/94/95 — 전 항목이 ARC-05~06 이월 설계 의도, Phase0 `exit_function` 및 `antagonist_tier_model`에 이미 고정된 구조. 회고 수정 금지 범위 내에서 ARC-05 serialize로 자연 회복 예정 (ARC-05 종료 시점 ~40%, ARC-06 종료 시점 35% 이하 복원 목표)
  - **새 경고 ② B31~B34 intensity 3연속 동일** (모두 8): beat_type은 determination/grief/revelation/triumph로 분화되어 있으나 intensity 수치만 우연히 동일. B35 serenity/6 drop으로 ARC-04 내 자연 회복 완료. ARC-05 B41부터 intensity 분화 검증 강화 (B41 discuss-phase 사전 선언 단계에서 명시)

## 4A. Antagonist Tier Model (ARC-04 진행 중)

- **tier_1 (field · 유통)**: 사공묵 + 흑시 실행부 + 적수(B26) + 철단사 조균(B34) + 흑삭 송개(B37). 전원 정파 연맹 감옥 이송 완료. **B40 사공묵 최종 자백 공증 완결** (연맹 판관부 3인 공동 서명 + 자발 청원 자백 + 친필 서신 1장 별도 동봉). tier_1 라인은 ARC-04로 공식 종결
- **tier_2 (executor · 문파 내부 지휘)**: 곽유정 + 설화진(도구-피해자). 해결 현황: B36 설화진 자수·퇴장 / B37 허무영 증언 / B38 곽유정 실행자 자복 + 침묵 자복 / B39 곽유정파 2인 장로 역공 프레임 공적 무력화(잠복). 곽유정 본인은 B39~B40 내내 원로원 금고 은거, ARC-05 B41 도주로 이월(여운 판단: '오늘 밤 또는 내일 새벽', 4문파 공동 경계 + 금고 감시 초소 포위망 완료)
- **tier_3 (top-tier designer · 한 세대 위, 미특정)**: 한청운 은퇴 강요 배후. **4경로 확증 공식 등재 완료** — (1) B33 필사체 B 세대 분해, (2) B37 허무영 직접 목격, (3) B38 곽유정 30 호흡 침묵의 묵시적 자복, (4) **B40 사공묵 최종 자백의 '한 세대 위에서 오는 한 장의 편지'**(태허검문 바깥 흑시 유통망에서 독립적으로 온 첫 확증). 인물 특성 10종 확보(기존 8종 + '30년간 사공묵·곽유정 통신을 지켜본 사람' + '30년 중 딱 한 번 곽유정을 거치지 않은 직접 지시 편지 1점 실물 이미 소각'). 이름 확정은 ARC-05~06 과제. 사공묵 친필 부탁 '그 윗사람이 누구인지 당신이 찾아 주시오'를 여운이 수락 → 개인적 책임 라인 고정

## 4A. Antagonist Tier Model (ARC-04 onwards)

- **tier_1 (field · 유통)**: 사공묵 + 흑시 실행부 + 적수. Resolution: ARC-04 B34 체포 + B40 자백.
- **tier_2 (executor · 문파 내부 지휘)**: 곽유정 (실행자) + 설화진 (도구-피해자). Resolution: ARC-04 B36 자수 + B37 증언 + B38 대면·침묵 + ARC-05 B41 도주.
- **tier_3 (top-tier designer · 한 세대 위)**: 미특정 (한청운 은퇴 강요 배후). Entry into Phase0: ARC-04 B33 변조 지문 세대 특징 + B37 허무영 증언 + B38 곽유정 침묵 + B40 사공묵 자백. Resolution: ARC-05 후반 ~ ARC-06 전반.

## 5. Known Non-Truth Docs

- `docs/2026-04-06/manual_meridian_archivist_context_handoff.md`
- `docs/2026-04-06/manual_meridian_archivist_context_handoff_b22.md`
- `docs/2026-04-06/manual_meridian_archivist_context_handoff_b26.md`
  - these remain useful guides but are not saved live truth by themselves

## 6. Delegation Rule

- use this file, the canon pitch, the root Phase0 file, the published work_guard, and the live TR file as the current-truth entry set
- do not describe this work as `Phase0/TR/BI not started`
- do not promote handoff-only Block 22-25 content into live truth without a merge step

## 7. B46·B47 Audit (2026-04-09)

- **Verdict**: PASS (무결, 회귀/드리프트/쓰기 중단 손상 없음)
- **Schema consistency**: B45·B46·B47 전량 동일 top-level 9키 + `content` 4키 + `genre_ext` 15키 + `martial_ext` 18키. 드리프트 0
- **Bundle chars (content+stakes)**: B45 6080 / B46 5132 / B47 6031. 세션 쓰기 로그와 JSON 실측 정확 일치
- **Tension/intensity drift (B41~B47)**: tension 10→8→7→6→9→3→5, intensity 9→8→7→7→9→4→6. 3연속 동일 금지 룰 준수(B43·B44 intensity 7은 2연속, 허용), B45 despair/9 직후 B46 respite/3 quiet 배치 + B47 realization/6 회복 곡선 ✓
- **5/5 차별화(cap 창 룰)**:
  - B46 vs B45: emo(despair→respite) · action(위조 대응→퇴임+직명 창설) · opponent(곽유정→없음 quiet) · location(3지역 현장→요양실+서고) · duration(4→7일) = 5/5
  - B47 vs B46: emo(respite→realization) · action(퇴임→체계 설계·반포) · opponent(없음→강호 비급 체계 구조적 불완전성) · location(요양실→총관 집무실+앞마당) · duration(7→5일) = 5/5
- **Realm 진행**: 선천 일맥 1단 B41~B47 전 구간 수치 유지(내공 정체 정책 + 곽유정 리밋 룰). 조맥 재편 입문 전조 감각 단계적 심화 — B44 첫 체감(ref 109 planted) → B46 두 번째 + 운용 원칙 확정(ref 121 기준점 정의) → B47 세 번째 + '한 호흡 박자 직전' 일시 확장(ref 109 PARTIAL 2단계, ref 127 완전 각성 B49/B50 예약)
- **Foreshadow/Callback 회계**:
  - B46 신규 FS ref 119~123(5건) · CB ref 1/9/10/20/40/44/109(7건) — **ref 1 (B1 외문 서고지기) 46블록 호선 완전 회수(외문 서고지기 → 비급 총관)**
  - B47 신규 FS ref 124~128(5건) · CB ref 16/33/35/42/44/45/46/102/105/109(10건) — 과거 기법 전량 5부 구조 재통합
  - ref 109 단조 진행(B44 planted → B46 기준점 수립 → B47 PARTIAL 2단계) ✓
  - ref 105 CLOSED (낙양 우자방 강호 공증 증인 네트워크 편입) · ref 102 구조적 완화
- **경고 (회고 수정 금지, 미래 슬롯 자연 회복)**:
  - opponent_blank_relief: B46 quiet_block(허용) + B47 "구조적 취약성"(실명 아님) → ARC-05 window 내 opponent_blank 누적 → **B48 defeat 7에서 곽유정 실명 재등장으로 즉시 회복 예정**
  - top_opponent_share (곽유정 단독): B46·B47 원격 행동도 없음 → ARC-05 내 누적 점유율 하락 방향(목표 ≤30%)
  - ARC-05 미회수율: FS 10건 신규 + CB 17건(일부 CLOSED/PARTIAL). **정체 없음, ref 1 46블록 호선 회수로 역대 최장 호선 클로즈**
