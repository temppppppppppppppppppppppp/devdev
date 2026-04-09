# hoegui_surgeon — Blocks 41-50 10-Block Self-Audit

Date: 2026-04-09
Scope: harness v2 §1.1C 10-block self-audit (Block 50 완료 boundary)
Work ID: `hoegui_surgeon`
Audit class: mandatory pre-next-batch audit (Block 51 생산 금지 해제 조건)
Basis:
- `treatments/hoegui_surgeon_tr_block_020_draft.json` (Blocks 41-50, current)
- `treatments/phase0/hoegui_surgeon_phase0_design.json` (ARC-05 완료 + ARC-06 51-60 예정)
- `work_guards/12_hoegui_surgeon.yaml`
- `docs/2026-04-08/hoegui_surgeon_live_status.md` (주의: Block 40 기준, 동기화 미수행)
- `docs/2026-04-08/hoegui_surgeon_block_31_40_self_audit.md` (상위 연속 audit, 권장 사항 검증 대상)
- `docs/2026-04-08/hoegui_surgeon_cross_pc_handoff_block_46_50.md` (Block 46-50 생산 설계)
- `docs/blockguide/treatment-production-harness-v2.md` §1.1C

## 1. Audit Scope

- primary: Block 41-50 (ARC-05 전체 10블록)
- backward anchor: Block 40 말미 (ARC-04 exit 상태 — FS-02 full_payoff, 강태준 불편한 공존)
- forward anchor: Phase0 ARC-06 slot 51-60 (Block 51 진입 조건)
- out-of-scope: Blocks 1-40, Block 51+ 생산, Phase0/work_guard/harness 본문, BI, live_status 갱신

## 2. Block-by-Block Summary Table

| Block | Title | auth Δ | beat | tension | opponent | 기능 |
|---|---|---|---|---|---|---|
| 41 | 펠로우 첫날 | +2 | operational_debut | 5 | 행정 공백 (EMR 카테고리 등록 전) | ARC-05 진입, 특별 카테고리 펠로우 실질 가동 |
| 42 | 이상훈 | +1 | measured_encounter | 6 | 이상훈 (볼륨 가설 검증자) | FS-13 direct_entry, 원거리 → 대면 |
| 43 | 술식 개량 | +2 | hands_on_improvement | 7 | 좌간정맥 외측 분지 각도 변이 | FS-04 internal_realization, R5' 보강 |
| 44 | 병원장의 제안 | −1.5 | principled_refusal | 7 | 나경태 (홍보 캠페인 후원) | defeat, FS-24 seed, R2' 다른 각도 거절 |
| 45 | 후원 없는 길 | +0.5 | damage_containment | 6 | 병원장 라인 (분산 불이익) | defeat 흡수, FS-24 payoff, 7축 분리 |
| 46 | 팀 빌딩 | +1 | quiet_network_formation | 4 | 조직 이탈 프레임 리스크 | quiet, FS-08 재활성(I-31-40-B 해소), R3' 준수 |
| 47 | 이상훈의 도전 | +1.5 | accepted_challenge | 7 | 이상훈 (볼륨 가설 공개 검증 제안) | FS-22 payoff 경로 진입, FS-04 external_secondary |
| 48 | 데이터 대결 | +3 | framework_realignment | 8 | 이상훈 (볼륨 가설) | ARC-05 peak, FS-22 full_payoff, FS-04 external_tertiary, Phase0 이상훈 key_turning_point |
| 49 | 학회 주목 | +2 | academic_recognition | 7 | 학술 원로 초청 프레임 확장 리스크 | 권혁수 first_block 49, FS-25 payoff, FS-04 rediscovery |
| 50 | 조교수 후보 | +3 | structural_ascension | 7 | 전례 속도 우려 3인 | **ARC-05 exit**, exit_function 3축, Block 40 공존 verification, FS-26 seed |

- Total ARC-05 authority delta: **+14.5**
- Tension curve: **5-6-7-7-6-4-7-8-7-7** — prior audit §8.3 권장 곡선과 **정확 일치**
- Max tension: Block 48 (8) peak. Min tension: Block 46 (4) quiet.
- Defeat blocks: Block 44 단일 (Phase0 `defeat_blocks:[44]` 정확 준수)
- Quiet blocks: Block 46 단일 (Phase0 `quiet_blocks:[46]` 정확 준수)
- Beat type 중복 0 (10개 전부 다름: operational_debut / measured_encounter / hands_on_improvement / principled_refusal / damage_containment / quiet_network_formation / accepted_challenge / framework_realignment / academic_recognition / structural_ascension)
- Opponent 축 분산: 이상훈 3회(42/47/48) + 병원장 라인 2회(44/45) + 이상훈 외 7개 다른 축. 이상훈 3회 등장 공격/대응 각도 전부 상이 — 원거리→대면 관찰(42) → 공개 검증 제안(47) → 가설 폐기 양립 전환(48). 반복 아닌 점증+양립 전환 구조.

## 3. 6-Axis Check (harness §1.1C)

### Axis 1 — 주인공 우위와 간판 맛

- "차트가 맞는 R2 (특별 카테고리 펠로우)"가 "차트가 맞는 R2 + 학술 층 기록 + 조교수 후보 등재"로 자연 승격. 간판 코어 유지.
- 서동혁 직접 발화량: Block 41 0회(외래 판독 필기만) + Block 42 0회(상호 인식) + Block 43 0회(루틴 기록) + Block 44 거절 서한 공동 서명만 + Block 45 차트 노트만 + Block 46 4인 1:1 설명 중 "이 결에 맞아서" 1문단 + Block 47 수락 회신 3문장 + **Block 48 발표 15분 중 결정적 마지막 문단 1회(축 분리 발화) + 질의응답 답변 없음** + Block 49 권혁수 환담 "48시간 내 회신" 1문장 + 방문 중 "재발명" 1줄 + Block 50 과장실에서 수용 + 복도 0회. **10블록 총 발화 = 수락 회신 3문장 + Block 48 결정적 한 문단 + Block 49 1문장+1줄 + Block 46 1문단**. 능력 장광설 금지 완벽 준수. Block 48 peak의 결정적 한 문단도 "본인 수치 자기 상대화"라는 겸허 발화이지 능력 과시 아님.
- 간판 피로: ARC-04 "제도 구조 역이용 + 우회 재구성" 패턴에서 ARC-05는 "술식 개량 + 학술 층 공개 검증 + 학술 라인 자산 확보"로 패턴 축 전환. 같은 성공 반복 아님.

**PASS**

### Axis 2 — 성취 직후 보상/인정 리듬

- 성취 블록 전부 same-block 또는 연속 블록 receipt:
  - 41(펠로우 첫날) → same-block 환자 2 경로 전환 + 독립 외래 첫날 성과
  - 42(이상훈 대면) → same-block 논문 초안 교환 약속 + FS-13 direct_entry
  - 43(술식 개량) → same-block 3건 + 표준 회귀 1건 + 후속 논문 seed
  - 44(거절) → same-block 거절 서한 전달 완료 + 불이익 예고 수용
  - 45(흡수) → same-block 7축 분리 + 협진 호출 15% 증가 확인
  - 46(팀 빌딩 quiet) → same-block 4인 명단 + FS-08 재활성 + 내규 합법 확인
  - 47(수락) → same-block 수락 회신 발송 + 이상훈 즉답 동의
  - 48(학회 peak) → same-block 이상훈 공개 양립 전환 + 권혁수 메모 seed
  - 49(학회 주목) → same-block 방문 완료 + 학술 지지 의사 공식화 약속
  - 50(exit) → same-block 6:3 통과 + 차트 노트 ARC-05 exit 기록 + 강태준 복도 발화
- Defeat 블록 44도 receipt 있음:
  - 44: Block 45 흡수 예약 (즉각 반격 단계 + 44 내부에 "회신 수용" receipt)
  - 45: 흡수 자체가 receipt (표면 3축 수용 + 핵심 7축 유지 확인)
- work_guard "반격 예약 없는 손해 금지" 준수 ✓

**PASS**

### Axis 3 — 권한/장악 축 실제 성장

- ARC-04 말 권한 체인: 이식팀 공식 사전 판독 보조 + 독립 케이스 시리즈 논문 + 병원장 면담 프레임 제어 + 특별 카테고리 펠로우 자격 + 수술 교육 위원회 레지던트 대표 + 강태준 불편한 공존 (ARC-03 8축 + ARC-04 6축 = 14축)
- ARC-05 말 권한 체인 신규 추가 축 8개:
  1. **독립 외래 실질 가동**(41) — EMR 특별 카테고리 등록 + 환자 경로 전환 첫날 사례
  2. **이상훈 학술 라인 인식 → 공동 발표 → 양립 관계**(42-47-48) — 학술 층 외부 관계 축
  3. **좌간정맥 외측 분지 술식 개량 루틴**(43) — 수술 현장 방법론 축
  4. **병원장 라인 불이익 사정 범위 한정 확인**(44-45) — 7축 분리 문서 고정, 외부 자원 의존 축 한정성 실증
  5. **4인 카테고리 기준 보조 인력 관행 + FS-08 김수현 협진 공식 경로 재활성**(46) — 수술실 운영 인프라 + 타과 협진 축 복원
  6. **대한외과학회 춘계 심포지엄 공동 패널 공식 기록 + 인과/볼륨 프레임 분리 학회 기록**(48) — 학술 층 방법론 고정
  7. **권혁수 국내 외과학회 중진 학술 지지 의사 공식화 약속 + 서울 중앙병원 방문 1일 형식**(49) — 학술 라인 자산
  8. **외과 교수 인사 위원회 조교수 후보 등재 6:3 통과 (상위 심사 대기)**(50) — 서열 구조 ascension (임용 아님)
- 신규 축 8개 추가. **서열 축 자체의 전진**(R2 펠로우 → R2 상태 조교수 후보 등재)이 ARC-05의 차별점. ARC-04까지는 서열은 그대로인데 실질만 뒤집는 구조였다면, ARC-05는 실질 축 누적 위에 서열 축이 "후보 등재"라는 공식 형식으로 움직이기 시작.
- work_guard `custom_rules: 서열은 그대로인데 실질적 결정권이 뒤집히는 구조` — ARC-05에서도 유지: 조교수 후보 등재는 "후보"이지 "임용"이 아니며, R2 직급은 유지된다. 실제 임용은 ARC-06 이후 상위 인사 위원회 심사 대기 단계. **규모 과시 경계 유지**.

**PASS**

### Axis 4 — Opponent / Method / Stakes 반복 누적

- **이상훈 3회 등장 분해** (ARC-05 주요 반복 지점):
  - Block 42: 원거리 인식에서 첫 대면 + 논문 초안 교환 약속 (관찰자 대면)
  - Block 47: 외부 자문 회람 경유 공동 패널 발표 공식 제안 (검증자 제안)
  - Block 48: 학회 공개 가설 폐기 + 양립 전환 공개 선언 (양립자 전환)
  - 세 번 모두 **관계 위치, 서동혁 대응 설계, 이상훈 동기 표현이 상이**. 42는 "상호 관찰자 간 인식 교환", 47은 "검증 제안의 수락 설계", 48은 "양립 전환의 공간 제공". 반복 아닌 Phase0 key_turning_point 경로(검증→대결→양립)의 점증 작동.
- **병원장 라인 2회(44-45) vs Block 37 비교**: Block 37 1차 면담(조건 제한 수락, 프레임 제어)과 Block 44-45 2차(정중 거절 + 분산 불이익 흡수)의 거절 각도가 다름. Block 37은 "면담 제안 수락하되 조건 제한", Block 44는 "후원 제안 정중 거절 + 제도 경로 원칙 2차 확인". R2' 다른 각도 거절 요구 준수.
- Method 축 10블록 전부 다름: 의결 문서 즉시 송부(41), 객관 데이터 교환 관찰(42), 술식 개량 반복 구현(43), 정중 거절 + 서한(44), 공식 이의 회피 + 7축 분리(45), 카테고리 기준 운영 메모(46), 수락 회신 + 볼륨 열세 선제 인정 원칙(47), 발표 마지막 문단 축 분리 발화(48), 방문 형식 1일 한정(49), 추천서 7축 서면 고정(50)
- Stakes 축: "학술 층 공개 검증 + 병원장 라인 외곽 자산 + 서열 축 전진"의 3겹 구조. ARC-04 "제도 구조 역이용"과 확연히 다른 결.
- Beat type 10개 전부 다름.

**PASS**

### Axis 5 — Continuity & 열린 복선

- 블록 간 `authority_before` → 직전 블록 `authority_after` 의미 체인: 10블록 전부 이어짐(일부 축약 체이닝 존재, 기존 41-45 관례와 동일).
- **FS 완결/전진 상태:**
  - FS-04 경험의 한계: Block 36 seed → Block 42 external_validation → Block 43 internal_realization → Block 47 external_secondary → Block 48 external_tertiary → Block 49 rediscovery_axis (권혁수 루틴과 구조적 유사성). **5단 체인 누적**, Phase0 Block 65 full payoff까지 방해 없음. **R5' 중간 보강 완료** (prior audit 권장 초과 달성).
  - FS-08 김수현 협진 관계: Block 20 seed → ARC-02~04 비활성 → **Block 46 공식 경로 reactivation**. **I-31-40-B 해소 완료**. (prior audit 권장 정확 작동)
  - FS-13 이상훈 원거리 인식: Block 28 seed → **Block 42 direct_entry payoff**.
  - FS-22 이상훈 "다음 정면 대결": Block 42 seed → Block 47 payoff 경로 진입 → **Block 48 full_payoff** (단 "정면 대결"이 "공동 공개 검증 + 양립"으로 재프레임).
  - FS-23 후속 논문: Block 43 seed → Block 47 예비 논문 초안 단계 → **Block 48 학회 공개 발표 단계**.
  - FS-24 별도 사안 검토: Block 44 seed → **Block 45 full_payoff** (표면 3축 분산 불이익으로 가시화).
- **신규 seed (ARC-06 연결):**
  - **FS-25**: 권혁수 청중석 메모 (Block 48 seed) → **Block 49 payoff** (1블록 내 즉시 해소, Phase0 first_block 49 정확)
  - **FS-26**: 대학병원 상위 인사 위원회 조교수 임용 심사 대기 단계 (Block 50 seed) → ARC-06 후반 payoff 예정. 병원장 라인의 간접 개입 경로 남김.
- **FS-21 강태준 "초기 지도 방향 설정"**: ARC-05 내에 중간 리마인드 앵커 미삽입. **I-31-40-C carry-over** 유지 (audit 권장대로 ARC-06 Block 55-60 구간 처리).
- **장기 동결 / 대기 상태:**
  - FS-07 (단독 집도 유예 정식 심사): ARC-05 내내 미개최. 장기 동결 유지. ARC-06 재검토 필요.
  - FS-10 (단독 집도 유예 정식 심사 시한): 동일.
  - FS-20 (판독 기반 사전 설계 교육 커리큘럼화): Phase0 Block 60 payoff 대기. ARC-06 진입.
- Orphaned seed 없음.

**PASS**

### Axis 6 — 다음 10블록 (ARC-06 51-60) 확장축 / 위험축

**Phase0 ARC-06 정보:**
- title: 병원의 칼
- time_window: 2028년 7월 ~ 2029년 6월
- capital_target: 과 운영 실권 + 병원장 라인 독립 + 수술 교육 체계 재편 시작
- front_sectors: 간담도·췌장·상복부 종합 고난도 수술 + 병원 정치
- main_opponents: 나경태(병원장, **은폐**) / 외과 일부 교수진(기득권)
- new_npcs: 한미정(의료 전문 기자)
- emotion_curve: 조교수 임용 → 구조조정 시도 → 은폐 사건 발견 → 병원장 대립 → 학술 권위 획득 → 과 개편
- quiet_blocks: [56]
- defeat_blocks: [54, 55]
- slots: 51 조교수 임용 / 52 외과 실권 / 53 수술 방법론 재편 / 54 병원장의 견제 / 55 의료 사고 은폐 / 56 조사 준비 / 57 한미정 / 58 병원장 대립 / 59 학술 권위 / 60 교육 재편

**확장축:**
1. **조교수 실제 임용** (Block 51) — Block 50 후보 등재의 상위 인사 위원회 심사 통과 (FS-26 payoff). ARC-06 진입.
2. **외과 실권 + 방법론 재편** (Block 52-53) — 과 운영 단위 권한 확보 + 판독 기반 사전 설계 전 과 확산
3. **병원장 견제 2연속 defeat** (Block 54-55) — ARC-05 단일 defeat와 다시 결이 바뀌는 2연속 defeat (ARC-03/ARC-04 리듬 복귀). 은폐 사건 발견 구간.
4. **조사 준비 quiet** (Block 56) — Phase0 quiet. 은폐 사건 증거 수집 내부 설계.
5. **한미정 의료 전문 기자 등장** (Block 57) — Phase0 new_npcs first_block 미명시, Block 57 추정.
6. **병원장 대립** (Block 58) — FS-03 은폐 사건 표면화의 peak. Phase0 나경태 turning points [44, 54, **58**] 중 58이 ARC-06 peak.
7. **학술 권위 확보** (Block 59) — 권혁수 학술 지지가 ARC-06에서 작동하는 지점 (Block 49 자산의 payoff).
8. **교육 재편** (Block 60) — FS-20 payoff, 판독 기반 사전 설계 전 과 교육 체계 재편. **FS-21 리마인드 앵커 여기서 1회 삽입 권장 (I-31-40-C 처리)**.

**위험축 (ARC-06 생산 시 필수 고려):**
- **R1" (은폐 사건 프레임 경계)**: Block 54-55-58 은폐 사건 국면이 "의사 영웅담 + 내부 고발 미담"으로 변질되면 work_guard forbidden_flattenings "감동 의사물" 직격. 은폐 사건은 "합리적 병원 운영자 나경태의 리스크 관리 실패 + 서동혁의 구조적 대응"으로 설계해야 함. 나경태 캐리커처 금지.
- **R2" (한미정 캐리커처 방지)**: 의료 전문 기자가 "정의감 넘치는 폭로 기자" 캐리커처가 되면 ARC-06 전체가 값싸진다. 한미정은 "의료 기자로서 취재 축 확보를 위해 서동혁과 거래 관계를 설계하는 계산자"로. 서동혁 측 이익과 한미정 측 이익의 교환 구조 필수.
- **R3" (조교수 임용 규모 과시 경계)**: Block 51 실제 임용이 "국내 최연소 조교수 + 교수 세대 일순위" 같은 규모 과시 표현으로 풀리지 않도록. Block 50에서 "후보 등재 단계 한정" 원칙을 수립했으므로 Block 51도 "상위 심사 통과 + 임용 발령"의 공식 절차 기록 수준.
- **R4" (2연속 defeat 흡수 구조)**: Block 54-55가 2연속 defeat이므로 흡수 블록 필요. Phase0에 흡수 블록 명시 없음 — Block 56 quiet가 흡수 역할 겸한다는 구조로 해석 권장. Block 56에서 defeat 2건 흡수 + 조사 준비 설계.
- **R5" (FS-21 리마인드 앵커 Block 55-60 구간 처리 — I-31-40-C)**: 이전 audit 권장대로 ARC-06 중에 "초기 지도 방향 설정" 자기 보호 첨언 1회 리마인드. Block 60 "교육 재편" 구간에서 "강태준이 Block 40 자기 보호 첨언을 다시 떠올리는 장면" 삽입 권장.
- **R6" (권혁수 자산 재소환 형식)**: Block 49 권혁수 지지 의사가 Block 59 학술 권위 구간에서 작동할 때 "형식 한정" 원칙을 유지한 채 발동해야 함. 방문 2차가 아닌 학회 내부 지지 성명 혹은 학술지 서신 형태로. Block 49 "방문 1일 형식 한정"이 깨지면 안 됨.
- **R7" (한미정 first_block 설정)**: Phase0 ARC-06 new_npcs 한미정의 first_block이 명시돼 있지 않음. Block 57 "한미정" 슬롯이 first_block일 가능성 높으나 Block 55 은폐 사건 발견 이후 등장 논리가 더 자연스러울 수도. ARC-06 생산 시 Block 56 또는 Block 57 초반이 first_block 후보. 감리 주의.

**ARC-06 권장 tension 곡선 (추정):** 6-7-7-8-8-5-7-9-7-7
- Block 51 임용(6, structural 동반 안정), Block 52-53 외과 실권+방법론 재편(7), Block 54-55 defeat 2연속(8), Block 56 quiet 흡수(5), Block 57 한미정 등장(7), Block 58 병원장 대립 peak(**9** — ARC 전체 최고), Block 59 학술 권위(7), Block 60 교육 재편(7, structural exit).
- peak 조정: ARC-03 10, ARC-04 8, ARC-05 8, ARC-06 9. 단조 상승 회피 + ARC-03 10 재현 경계.

**PASS, 7개 위험축 식별**

## 4. Additional Checks

### 4.1 work_guard forbidden_flattenings 10블록 전수 재확인

- 무보상 희생 미담 펌프: 0건 ✓
- 감동 의사물: 0건 ✓ (Block 41 환자 2 진단 재확인도 환자 사연 없이 판독 노트 중심, Block 48 학회 peak도 청중 감동 0, 숫자와 프레임 분리만)
- 환자 구조 자체 첫 승리: 0건 ✓
- 의료 윤리 딜레마: 0건 ✓ (Block 44 거절도 원칙-편익 딜레마 아닌 조건 독립성 판단)
- 규모 과시: 0건 ✓ (권혁수 "국내 외과학회 중진" 한정, Block 48 "국내 상위권" 수준, Block 50 "후보 등재" 한정)
- 적대자 멍청한 악당: 0건 ✓ (이상훈 3회 전부 합리적 검증자, 나경태 Block 44 "합리적 후원 계산자", 병원장 라인 Block 45 분산 불이익 "합법 재량")
- 능력 장광설: 0건 ✓ (서동혁 발화 극소 유지, Block 48 결정적 문단도 자기 상대화 겸허 발화)
- 반격 예약 없는 손해: 0건 ✓ (44 → 45 흡수 즉각 예약)
- 보상이 생존/칭찬/감사 수준: 0건 ✓ (전부 서면 기록 + 공식 절차 + 권한 축 전진)
- 위기 때 빈손/무대응: 0건 ✓ (44 정중 거절 + 45 7축 분리)

### 4.2 Phase0 ARC-05 exit_function 3축 달성

Phase0 정의: "펠로우 → 조교수 후보 + 독립 수술팀 + 국내 학회 주목"
- **조교수 후보** ✓ (Block 50 6:3 통과 + 후보 등재 단계 한정)
- **독립 수술팀** ✓ (Block 46 4인 카테고리 기준 관행 — 공식 독립팀 회피, 관행 층 이식)
- **국내 학회 주목** ✓ (Block 48 춘계 심포지엄 공식 기록 + Block 49 권혁수 지지 의사 공식화 약속)

### 4.3 Phase0 NPC 정합성 확인

- **이상훈**: Phase0 turning points [**42**, **48**, 62]. Block 42 첫 대면 정확, Block 48 key_turning_point("데이터 검증 → 정면 대결 → 양립") **본문 전환 정확 작동**. Block 47은 Phase0 정의 외 등장이지만 "정면 대결 제안"의 자연 확장 — summary 곡선 내부.
- **나경태**: Phase0 turning points [**44**, 54, 58]. Block 44 후원 제안 정확 일치. 54/58은 ARC-06 소관.
- **권혁수**: Phase0 new_npcs ARC-05 지정, **first_block: 49 정확 일치**. Block 48 청중석 관찰자 seed가 first_block 직전 seed로 삽입되어 등장 논리 선명화. Phase0 role: "서동혁의 학술 권위를 뒷받침하는 학회 중진 — 국내 외과학회 라인" 정확 한정(규모 과시 없음).
- **조영채**: Phase0 turning points [6, 7, 18, 38, **50**]. Block 50 조교수 후보 추천 정확 일치. 그 외 빈번 등장은 조력자 라인 일상.
- **강태준**: Phase0 turning points [4, 12, 17, 23, 34, 40, 68]. ARC-05는 점유 없음 예정이었는데 Block 50 외과 교수 인사 위원회에서 **기권 + 복도 건조 발화**로 등장 — Phase0 정의 외 등장이지만 Block 40 불편한 공존 결의 "실질 작동 verification" 역할. 허용(summary 곡선 내부).
- **한미정**: Phase0 new_npcs ARC-06 지정, first_block 미명시. ARC-06 소관, 본 audit 스코프 밖이지만 Next 10 Focus §R7"에서 권장 명시.

### 4.4 Schema debt (I-02) 상태

- Blocks 41-50 전부 canonical `block_cider.*` 및 `capital_*` 미탑재. Blocks 1-40 관행 유지.
- Tier B migration debt 누적 유지 (Blocks 1-50 전부). 본 감리 스코프 밖.

### 4.5 핸드오프 설계 대비 실제 생산 정합성

`docs/2026-04-08/hoegui_surgeon_cross_pc_handoff_block_46_50.md` §4 설계 대비:
- Block 46 `팀 빌딩`: 4인 비공식 팀 + FS-08 재활성 + R3' 준수 → 본문 정확 반영 ✓
- Block 47 `이상훈의 도전`: 공동 패널 수락 + 볼륨 열세 선제 인정 + FS-04 external_secondary → 정확 ✓
- Block 48 `데이터 대결`: 본인 수치 자기 상대화 + 인과/볼륨 축 분리 + 이상훈 양립 전환 + 권혁수 메모 seed → 정확 ✓
- Block 49 `학회 주목`: 권혁수 first_block 49 + 방문 1일 형식 한정 + "국내 외과학회 중진" 규모 한정 → 정확 ✓
- Block 50 `조교수 후보`: 추천서 7축 + 6:3 통과 + 후보 등재 한정 + 강태준 공식 반대 부재 → 정확 ✓
- 설계-생산 gap 0건.

### 4.6 이전 audit(31-40) 권장사항 추적

| prior audit 권장 | 본 10블록 내 처리 | 상태 |
|---|---|---|
| R1' 이상훈 캐리커처 방지 | Block 42/47/48 전부 "합리적 검증자" 유지, Block 48 가설 폐기도 "합리적 수정" 결 | ✅ 준수 |
| R2' 병원장 거절 각도 차별화 | Block 44 "조건 독립성 침해" 거절 근거 — Block 27 수치 거절과 각도 상이 | ✅ 준수 |
| R3' 독립팀 조직 이탈 프레임 회피 | Block 46 카테고리 기준 관행 + 내규 4조 합법 확인 | ✅ 준수 |
| R4' 규모 확대 경계 | 권혁수 "국내 외과학회 중진" 한정, 학회 "국내 상위권" 수준, Block 50 후보 등재 단계 한정 | ✅ 준수 |
| R5' FS-04 중간 보강 | Block 43 internal_realization + Block 47 external_secondary + Block 48 external_tertiary + Block 49 rediscovery — **5단 체인 누적, 권장 초과 달성** | ✅ 초과 달성 |
| R6' 이상훈 간격 관리 | Block 47에서 이상훈이 논문 초안 전독해 명시(Block 43의 "원거리 감시") | ✅ 준수 |
| R7' defeat 단일 리듬 유지 | Block 44 단일 defeat + Block 45 단일 흡수 | ✅ 준수 |
| I-31-40-A Block 33 micro patch | 본 ARC-05 범위 밖 처리 — `tr_polish` 별도 envelope 대기 | carry-over |
| I-31-40-B FS-08 김수현 재활성 | **Block 46 공식 경로 reactivation 완료 — 해소** | ✅ **closed** |
| I-31-40-C FS-21 리마인드 앵커 | ARC-05 범위 밖, ARC-06 Block 55-60 구간 처리 권장 유지 | carry-over |

## 5. Issues Found

| id | severity | 내용 | 비고 |
|---|---|---|---|
| **I-41-50-A** | micro | **Block 49 권혁수 방문 요약 서술의 정보 밀도가 Block 48 peak 밀도보다 낮음**. 1개월 후 실제 방문 전개(약 3+1.5+1 시간 일정)가 단일 문단에 요약되어 있어, 판독 노트 공동 검토 + 경로 일치율 재검증의 실물 장면이 상대적으로 압축. 본문 모순은 없으나 Block 59(학술 권위) 재소환 시 Block 49 현장 장면 디테일이 약해 재활용 품질 저하 가능성. `tr_polish` 선택 대상. | 본 10-block audit |
| **I-41-50-B** | micro | **Block 46 quiet block이 Phase0 emotion_curve "독립팀 구축"을 "관행 층 이식"으로 재해석**. Phase0 표현 "비공식 독립 팀"과 본문 "공식 독립 팀 회피 + 카테고리 기준 관행"이 의미상 일치하지만 표면 워딩 차이가 Phase0 리뷰어 시각에서 해석 필요. R3' 준수를 위한 합리적 재해석이고 본문 논리 정합하므로 차단 아님. Phase0 handoff 메모에 "독립 수술팀 = 카테고리 기준 관행 4인 명단"이라는 매핑 한 줄 추가가 유용. | 본 10-block audit |
| **I-41-50-C** | micro | **Block 50 조영채 4단 운영 단서 중 "권혁수 교류 1일 방문 형식 이상 확장 금지"**가 ARC-06 Block 59 "학술 권위 획득" 구간에서 작동 형식을 선제 제약한다. 본 ARC-05 audit에서는 R6"(권혁수 자산 재소환 형식)으로 ARC-06 guardrail에 이월 권장 — Block 59 재소환 시 방문 2차 금지, 학회 내부 지지 성명 또는 학술지 서신 형태로 한정. | 본 10-block audit |
| I-31-40-A | carry-over | Block 33 micro patch | carry-over, 차단 아님 |
| I-31-40-B | **closed** | FS-08 김수현 재활성 — Block 46 공식 경로 reactivation 완료 ✓ | 본 audit에서 해소 |
| I-31-40-C | carry-over | FS-21 리마인드 앵커 — ARC-06 Block 55-60 처리 권장 유지 | carry-over |
| I-02 | minor | Tier B migration debt — Blocks 1-50 전체 canonical schema 백필 대기 | carry-over |
| I-03, I-04 | micro | 이전 audit 선택 polish — 미해소, 차단 아님 | carry-over |

신규 이슈: 3건 (I-41-50-A/B/C, 전부 micro)
해소된 이슈: 1건 (I-31-40-B FS-08 재활성)
차단 이슈: 0건

## 6. Repair Targets

| id | 수정 대상 | 권장 envelope | 우선순위 | 차단 여부 |
|---|---|---|---|---|
| I-41-50-A | Block 49 권혁수 방문 현장 디테일 보강 (판독 노트 공동 검토 1-2장면, 경로 일치율 재검증 구체 수치 언급) | `tr_polish` | 낮음 (Block 59 재소환 전 처리 권장) | 아님 |
| I-41-50-B | Phase0 handoff 메모에 "독립 수술팀 = 카테고리 기준 관행" 매핑 주석 | `phase0_patch` 선택 또는 handoff doc 주석 | 매우 낮음 | 아님 |
| I-41-50-C | ARC-06 Block 59 생산 guardrail에 "권혁수 재소환 형식 한정" 명시 | Block 51+ 생산 guardrail (본 audit §6 Next 10 Focus §R6"에 반영 완료) | 낮음 | 아님 |
| I-31-40-A | Block 33 micro patch | `tr_polish` | 매우 낮음 | 아님 |
| I-31-40-C | ARC-06 Block 55-60 구간에 FS-21 리마인드 앵커 1회 자연 삽입 | Block 55-60 생산 guardrail | 낮음 | 아님 |
| I-02 | Blocks 1-50 전체 canonical `block_cider.*` + `capital_*` 백필 | `schema_backfill` | 낮음 | 아님 |
| I-03, I-04 | micro polish | `tr_polish` 선택 | 매우 낮음 | 아님 |

본 10-block audit 쓰기 스코프는 본 메모 파일 1개로 한정. 모든 수정 deferred.

## 7. 10-Block Audit Result

**PASS**

- 핵심 6축 전부 PASS
- ARC-05 exit_function 3축 달성 (조교수 후보 + 독립 수술팀 관행 + 국내 학회 주목)
- work_guard forbidden_flattenings 10항목 0건
- Phase0 NPC turning points 정합 (이상훈 42/48 정확, 나경태 44 정확, 권혁수 first_block 49 정확, 조영채 50 정확)
- 이전 audit 지적 I-31-40-B FS-08 재활성 **해소**
- 이전 audit 권장 R1'~R7' 전부 준수, R5' FS-04 보강은 초과 달성(5단 체인)
- 신규 이슈 3건 전부 micro, Block 51 진입 차단 없음
- harness §1.1C "FAIL이면 같은 10블록 구간 안에서 필요한 블록을 먼저 수리" 조항 발동 없음

## 8. Next 10 Focus (Blocks 51-60 = ARC-06 "병원의 칼")

> **[2026-04-09 PATCH]** 본 §8은 Block 51 생산 직전 Phase0 원본 ARC-06 block_slots 재확인 결과 초안(handoff doc §10 sketch 기반)과 Phase0 원본 사이에 구조적 불일치가 발견되어 **Phase0 원본을 SSOT로 전면 재작성**함. 이전 초안은 Block 52를 "외과 실권", 54-55를 "병원장 견제 + 의료 사고 은폐 2연속 defeat", 57을 "한미정", 58을 "병원장 대립 peak", 59를 "학술 권위"로 기술했으나, Phase0 원본에 따르면 은폐 사건은 **Block 52에서 바로 발견**되고, peak 라인은 **Block 58 공개**이며, 권혁수 외부 검증 제안도 Block 58에서 발동된다. 본 패치 이후 본 §8이 공식 가이드.

### 8.1 확장축 우선 순위 (Phase0 원본 block_slots 기준)

1. **조교수 임용** (Block 51, `조교수`) — FS-26 payoff, 상위 인사 위원회 심사 통과, 외래·수술·연구·교육 4축 공식 운영권 자리 확보 **[완료 2026-04-09]**
2. **은폐 발견** (Block 52, `은폐`) — 과거 수술 데이터 검토 중 특정 교수의 합병증이 조직적으로 축소 보고된 흔적 발견. ARC-06 메인 서사 진입, FS-03 은폐 사건 축 본격 활성화.
3. **병원장의 벽** (Block 53, `병원장의 벽`) — 은폐 사건이 병원장 나경태 재임 시기와 겹침. 문제 제기 시 병원장 라인과 정면충돌 가능성이 드러남. FS-27(Block 51 seed) 조건부 승인 권고 서면의 의미가 실물화.
4. **인사 위협 defeat** (Block 54, `인사 위협`) — Phase0 `defeat_blocks:[54,55]` 첫 번째. 병원장이 조교수 재임용 심사를 압박 수단으로 사용. "은폐를 덮으면 안정, 건드리면 퇴출" 양자택일 구조. Phase0 나경태 turning points [54] 정확.
5. **환자 기록 defeat** (Block 55, `환자 기록`) — Phase0 `defeat_blocks:[54,55]` 두 번째. 은폐된 합병증 환자들의 후속 경과 추적 중 **의학적 근거 축적**(재수술/추가 치료 기록 조작 확인). defeat 중에도 증거 축은 쌓이는 이중 구조.
6. **증거 정리 quiet** (Block 56, `증거 정리`) — Phase0 `quiet_blocks:[56]`. 수집 데이터를 **개인 폭로 아닌 수술 교육 위원회 안건 형태로 정리**. Block 54-55 defeat 2연속 흡수 + 제도적 경로 설계 이중 기능.
7. **교육위 안건** (Block 57, `교육위 안건`) — 수술 교육 위원회에서 '합병증 보고 체계 재검토' 안건으로 상정. **은폐를 직접 지목하지 않고 제도 개선 형태로 문제 제기**. Block 39 교육위 의석 + Block 51 교육 축 공식 운영권의 본격 작동.
8. **공개 peak** (Block 58, `공개`) — ARC-06 peak. 교육위 논의 중 과거 데이터 이상이 표면화. 병원장 방어 시도 + **외과학회 중진 권혁수가 외부 검증 제안** — Block 49 권혁수 자산이 여기서 작동. Phase0 나경태 turning points [58] peak + 권혁수 재소환 지점.
9. **과 운영** (Block 59, `과 운영`) — 은폐 사건 수습 과정에서 외과 내부 개편. 서동혁이 과 운영 실무 담당. **공식 직책은 진료과장 아님, 실질적 운영권만**. Block 50/51 "과 운영 실권은 과장 영역" 원칙의 자연 확장(실권 이양이 아닌 실무 이양).
10. **교육 재편 exit** (Block 60, `교육 재편`) — Phase0 ARC-06 exit. FS-20 payoff (Block 39 seed 판독 기반 사전 설계 교육 커리큘럼화). 서동혁 방식이 외과 수련 교육 공식 제도로 편입. **I-31-40-C FS-21 리마인드 앵커 1회 삽입 권장 지점**.

### 8.2 필수 수위 조절 (위험축 대응, Phase0 원본 기준 재설계)

- **R1" 은폐 사건 감동 의사물화 경계**: Block 52-55-58 은폐 사건 국면 전체가 work_guard forbidden_flattenings "감동 의사물" + "내부 고발 미담" 직격 리스크. 나경태는 "리스크 관리 실패한 합리적 병원 운영자", 서동혁은 "제도 경로 설계자". **개인 폭로 프레임 금지** — Phase0 Block 56-57 "개인 폭로가 아니라 제도적 경로 / 직접 지목하지 않고 제도 개선 형태"가 은폐 사건 전 구간의 메타 원칙이다.
- **R2" 환자 이야기 감동 펌프 금지**: Block 55 환자 기록 추적 구간은 "재수술/추가 치료 기록 조작"이 **의학적 근거**로 사용돼야지 환자 사연/가족 눈물 서사로 변질되면 직격. 환자는 데이터 행이지 감정 주체가 아님.
- **R3" 나경태 캐리커처 방지**: Block 53-54-58 병원장 3회 등장. Block 37 "합리적 병원 운영자", Block 44 "합리적 후원 계산자", Block 51 "합법 행정 의견 제출자(FS-27)"의 결을 유지. Block 54 인사 위협도 "악의적 보복"이 아닌 "재임 시기 은폐 방어를 위한 합리적 압박 수단" — 악당 금지.
- **R4" 2연속 defeat(54-55) + 1 quiet 흡수(56) 리듬**: ARC-03 Block 23-24, ARC-04 Block 34-35의 defeat 2연속 + 별도 흡수 리듬으로 **복귀** (ARC-05 단일 defeat+흡수와 다름). Phase0 `defeat_blocks:[54,55]` + `quiet_blocks:[56]` 연속 배치는 의도된 구조. Block 56이 defeat 2건 흡수 + 증거 정리 이중 기능. Block 36 독립 데이터 quiet의 결(수집+재구성) 재사용 가능.
- **R5" Block 54-55 defeat 중 증거 축 누적 이중 구조**: Phase0 Block 55 명시 "의학적 근거가 쌓인다" — defeat이면서 동시에 자산 누적이 일어나는 **비전형 defeat**. 겉으로는 위협·조작 확인이라는 손해이지만 실질은 ARC-06 peak를 위한 탄약 축적. 감리 시 이 이중성 유지가 핵심.
- **R6" Block 58 공개 peak의 제도 경로 유지**: Phase0 Block 57 "은폐를 직접 지목하지 않고 제도 개선 형태"가 Block 58에서 "과거 데이터 이상 표면화"로 전환될 때 **여전히 직접 고발 프레임이 아닌 교육위 내부 논의 구조**여야 함. 권혁수 외부 검증 제안도 "학술 원로의 합리적 검증 요청"이지 "고발 지원 세력"이 아님. Block 49 권혁수 포지션("국내 외과학회 중진, 합리적 학술 판단") 유지.
- **R7" 권혁수 자산 재소환 형식 한정 (I-41-50-C 처리)**: Block 58 권혁수 외부 검증 제안 발동 시 **방문 2차 금지**. 학회 공식 경로(세션 발언 / 서면 의견 / 학술지 서신) 내에서만. Block 49 "1일 방문 형식 한정" + Block 51 권혁수 서신 교환 재확인의 원칙 유지.
- **R8" 서동혁 과 운영 실권 경계(Block 59)**: Phase0 Block 59 "공식 직책은 아직 진료과장이 아니지만 실질적 운영권". Block 50-51 "과 운영 실권은 조영채 과장 영역"과 충돌 없이 해석해야 함 — Block 59는 "은폐 사건 수습이라는 비상 국면의 실무 이양"이지 "과장 라인 교체"가 아님. 조영채 과장이 여전히 진료과장 직책 보유, 서동혁은 은폐 수습 TF 실무 책임자 수준. 규모 과시 경계 준수.
- **R9" FS-21 리마인드 앵커 (I-31-40-C 처리)**: Block 60 교육 재편 구간이 자연 삽입 지점. "강태준이 Block 40 자기 보호 첨언('초기 지도 방향 설정')을 다시 떠올리는 장면" 1회. 강태준은 Phase0 turning points [68]에서 퇴장 시 인정이 오므로 Block 60 교육 재편이 제도로 편입되는 장면이 FS-21의 사전 해체 지점이 된다.
- **R10" 한미정 first_block 문제**: ARC-06 new_npcs 한미정이 Phase0 block_slots에 **등장 슬롯 명시 없음**. ARC-06 10블록 전체에서 한미정이 자연 등장할 지점이 Phase0에 지정되지 않아, 본 Phase0는 한미정을 "ARC-06 등장은 확정하지만 슬롯 미정" 상태로 둔 것으로 보임. 해석 2가지: (a) 한미정은 ARC-06 내에서 **미등장 또는 seed만**, 실질 활성화는 ARC-07, (b) Block 58 공개 peak 시점에 **외부 취재 채널 경로로 자연 등장** 가능. 본 10-block audit 단계에서는 결정 유예, Block 55-58 생산 중 선택 권장. R2"(한미정 캐리커처 방지) 원칙은 어느 경로든 유지.
- **R11" Block 51에서 개시된 FS-27 병원장 모니터링 경로 작동**: Block 51 조건부 승인 권고 서면이 Block 52-54 구간에서 "과 내부 활동 기록 정보 요청"으로 실제 작동해야 seed가 소모됨. Block 52 은폐 발견 직후 병원장 라인이 서동혁의 "과거 데이터 검토 활동"에 대한 정보 요청을 조영채 과장 선에서 차단하는 장면이 FS-27 payoff의 자연 경로.

### 8.3 ARC-06 권장 tension 곡선 (Phase0 원본 기준 재설계)

`6-7-7-8-8-5-7-9-7-7`
- **Block 51**(6, formal_ascension) **[실측 완료]** — structural 안정 진입
- **Block 52**(7, investigative_discovery) — 은폐 첫 발견, 정보 층 충격
- **Block 53**(7, systemic_collision) — 나경태 재임 시기 중첩 확인
- **Block 54**(8, defeat 1) — 인사 위협 압박
- **Block 55**(8, defeat 2) — 환자 기록 조작 확인 + 증거 축적 이중 구조
- **Block 56**(5, quiet) — defeat 2건 흡수 + 교육위 안건 형태 정리
- **Block 57**(7) — 교육위 안건 상정, 제도 경로 작동
- **Block 58**(9, peak) — 공개, 권혁수 외부 검증 제안. ARC 전체 peak 후보
- **Block 59**(7) — 외과 내부 개편, 실무 운영권 이양
- **Block 60**(7, structural exit) — FS-20 payoff + FS-21 리마인드 앵커
- peak: Block 58(9). ARC-03 peak 10 대비 유지, ARC-05 peak 8 대비 +1, 단조 상승 회피
- valley: Block 56 quiet(5)
- ARC-06 exit (Block 60) tension 7

### 8.4 이월 권장 guardrails

- **I-41-50-A**: Block 49 디테일 보강은 Block 58 권혁수 재소환 전 `tr_polish`로 처리 권장. 차단 없음.
- **I-41-50-B**: Phase0 handoff doc 주석 추가(매우 낮음 우선순위).
- **I-41-50-C**: Block 58 권혁수 재소환 형식 한정 — 본 §8 R7"에 반영 완료.
- **I-31-40-A**: Block 33 micro patch — `tr_polish` 별도 envelope 대기 유지.
- **I-31-40-C**: Block 60 FS-21 리마인드 앵커 — 본 §8 R9"에 반영.
- **FS-27 처리 경로**: Block 51 신규 seed. Block 52 은폐 발견 직후 과장 선 차단 장면으로 payoff 설계 권장 — 본 §8 R11"에 반영.
- **신규 I-41-50-D(patch 사유)**: 본 §8의 최초 초안이 Phase0 원본이 아닌 handoff doc §10 sketch에 기반해 작성됐던 운영 실수. 재발 방지 메모: **10-block audit §8 Next N Focus 작성 시 handoff doc이 아닌 Phase0 원본을 1순위 SSOT로 참조할 것**. carry-over, 차단 없음, 본 패치로 실질 해소.

## 9. Summary

- audit_result: **PASS**
- ready_for_block_51: **yes**
- blocking issues: **none**
- new issues: 3 (I-41-50-A, B, C — 전부 micro)
- resolved issues: 1 (I-31-40-B FS-08 재활성 해소)
- carry-over issues: 4 (I-31-40-A, I-31-40-C, I-02, I-03/I-04)
- next immediate action: **(선행 권장)** `status_sync` — Block 40 기준 live_status를 Block 50 + ARC-05 exit + 본 10-block audit 결과로 동기화 / **(메인)** `tr_continue` 1-block envelope Block 51 `조교수 임용` (ARC-06 진입)
- 10-block self-audit trigger: 다음은 Block 60 완료 시점 (Blocks 51-60 self-audit)

---

_본 문서의 쓰기 스코프는 본 메모 파일 하나로 한정. TR 본문 · Phase0 · work_guard · live_status · harness · BI 일체 미수정._
