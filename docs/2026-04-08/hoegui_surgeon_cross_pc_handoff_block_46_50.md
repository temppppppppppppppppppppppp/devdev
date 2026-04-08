# hoegui_surgeon — Cross-PC Handoff (Block 46-50 재개 컨텍스트)

Date: 2026-04-08
Status: **pause for cross-PC transfer**
Work ID: `hoegui_surgeon`
Current saved boundary: **Block 45** (ARC-05 진행 중, 5/10 완료)
Next pending batch: **Blocks 46-50 1개씩 순차 생성 → Block 50 완료 시 harness §1.1C 10-block self-audit 강제**

## 0. 핸드오프 목적

이전 세션에서 `hoegui_surgeon` TR 생산이 Block 45까지 진행됐고, 사용자의 다음 오더는 **"50까지 1개씩 정성껏 순차 생성 후 보고"** 였다. 이 오더는 수락된 상태에서 다른 PC로 전환을 위해 중단됐다. 본 문서는 새 PC의 Claude 세션이 동일 작업을 이어받을 수 있도록 필요한 컨텍스트를 전부 문서화한다.

수신자 (새 세션 Claude)는 이 문서 + 아래 §5의 필수 읽기 파일만 읽으면 Block 46부터 정확한 guardrail/결/톤으로 이어서 쓸 수 있어야 한다.

## 1. 현재 고정 상태

### 1.1 파일 상태

- 라이브 TR 파일: `treatments/hoegui_surgeon_tr_block_020_draft.json`
  - `_saved_block_boundary`: **45**
  - `_next_continuation_boundary`: **46**
  - `_arcs_covered`: `[ARC-01, ARC-02, ARC-03, ARC-04, ARC-05]`
  - 블록 수: 45
  - 마지막 검증: `python -c "import json; d=json.load(open('...','utf-8')); assert d['_saved_block_boundary']==45; assert len(d['blocks'])==45; print('ok')"` → ok
  - Blocks 1-45 전부 byte-equal invariant 유지 상태
- Phase0: `treatments/phase0/hoegui_surgeon_phase0_design.json` (변경 없음, root_admit 이후 고정)
- work_guard: `work_guards/12_hoegui_surgeon.yaml` (변경 없음)
- live_status: `docs/2026-04-08/hoegui_surgeon_live_status.md` — **Block 40 기준 상태** (Block 45 동기화 되지 않음, I-31-40 audit 이후 status_sync가 미수행)
- 최신 10-block audit: `docs/2026-04-08/hoegui_surgeon_block_31_40_self_audit.md` (PASS)

### 1.2 ARC 진행 상태

| ARC | 범위 | 상태 | 비고 |
|---|---|---|---|
| ARC-01 | 1-10 | ✅ 완료 | 차트가 먼저 맞는 R1 |
| ARC-02 | 11-20 | ✅ 완료 | M&M 회의록 기재, 타과 협진 호출권 |
| ARC-03 | 21-30 | ✅ 완료 | ARC-03 exit: R2 + 특수수술 + 학회 증례 + stay method 통과 |
| ARC-04 | 31-40 | ✅ 완료 | ARC-04 exit: 펠로우 조기 추천 + 교육위 + 강태준 불편한 공존 (FS-02 full payoff) |
| ARC-05 | 41-50 | 🟡 진행 중 (45/50) | 메스 하나로 올라간다 |
| ARC-06 | 51-60 | 대기 | 병원의 칼 |
| ARC-07 | 61-70 | 대기 | 왕좌 |

### 1.3 ARC-05 상세 (41-45 완료 / 46-50 미완료)

Blocks 41-45 요약:
| No | Title | Δ | tension | beat |
|---|---|---|---|---|
| 41 | 펠로우 첫날 | +2 | 5 | operational_debut |
| 42 | 이상훈 | +1 | 6 | measured_encounter |
| 43 | 술식 개량 | +2 | 7 | hands_on_improvement |
| 44 | 병원장의 제안 | −1.5 | 7 | principled_refusal (defeat) |
| 45 | 후원 없는 길 | +0.5 | 6 | damage_containment (defeat 흡수) |

- 누적 authority_delta (41-45): +4.0
- 권장 tension curve (audit §8.3): `5-6-7-7-6-4-7-8-7-7`
- 실측 (41-45): `5-6-7-7-6` ← 정확 일치
- 남은 (46-50) 권장: `4-7-8-7-7`

## 2. 운영 규율 (고정 원칙, 변경 금지)

사용자가 확정한 고정 방침 (이전 세션에서 설정됨):

1. **하네스 엄격 적용** — `docs/blockguide/treatment-production-harness-v2.md` §1.1B, §1.1C 준수
2. **1-block envelope 기본값** — 각 새 오더는 1블록만 전진, 저장 + boundary 갱신 + next gate 보고까지만 처리
3. **자동 연속 생산 금지** — 새 오더 없이 다음 블록 자동 진행 금지
4. **5-block cap (§1.1B)** — 1-block envelope 모드에서는 cap 소진 개념이 약해짐. 사용자가 "X까지 순차 생산" 지시 시 해당 범위만 한 턴에 배치 가능 (ARC-03, ARC-04 패턴 참고)
5. **10-block self-audit (§1.1C)** — Block 10/20/30/40/50/... 완료 시 강제. 다음 액션으로 즉시 audit 메모 작성. Block 41-50 audit은 **Block 50 생산 직후 필수**.
6. **Phase0/work_guard/harness/shared governance docs 수정 금지** (명시적 별도 오더 없이)
7. **Blocks 1-45 재작성 금지** — 기존 블록 byte-equal invariant 유지 (tr_polish/schema_backfill은 별도 envelope)
8. **파일 확장자·이름 변경 금지** (TR 파일명 `hoegui_surgeon_tr_block_020_draft.json` 그대로, 숫자 접미는 legacy이며 admit note에 설명)
9. **BI 생성 금지** — 명시적 `bi_refresh` 오더 없이

## 3. 현재 대기 오더 (이 핸드오프의 핵심)

**사용자 마지막 지시:** `"50까지 1개씩 정성껏 순차 생성 후 보고"`

**해석:**
- 목표 boundary: Block 50 (ARC-05 exit)
- 남은 블록: 5개 (46, 47, 48, 49, 50)
- 스타일 요구: "1개씩 정성껏" = 각 블록을 꼼꼼하게 작성. 이전 "35까지 순차 생산", "40까지 순차 진행" 오더에서도 단일 Python 스크립트 배치로 처리했으나, 이번은 "1개씩"과 "정성껏"을 명시 — 블록당 분량/품질/guardrail 준수가 여느 때보다 더 중요.
- Block 50 이후: harness §1.1C에 의해 **Blocks 41-50 10-block self-audit 강제**. audit 메모 파일 작성 필수.
- 보고 형식: 5블록 전부 완료 + 10-block audit까지 마친 후 통합 보고

**재개 시 권장 접근:**
- 단일 Python 스크립트로 5블록 append하는 기존 패턴은 가능하지만, 본 오더는 "1개씩 정성껏"을 강조했으므로 블록당 품질 검토를 더 엄격하게. 본문 분량은 이전 ARC-05 블록들(41-45)과 유사한 수준 유지 (content 필드 약 800-1500자 한국어).
- 5블록을 하나의 Python 스크립트로 처리하되, 각 블록 draft를 개별적으로 구체화한 뒤 조합할 것.
- Block 50 완료 후 같은 턴에 10-block audit 작성 여부는 현장 판단. 분량이 과다하면 생산 완료 보고 후 사용자 재지시 대기하는 것도 가능. 다만 harness §1.1C 강제이므로 audit은 반드시 다음 필수 액션으로 예약.

## 4. Block 46-50 구체 계획 (이전 세션 draft)

이전 세션에서 이미 각 블록의 phase0 slot + guardrail 분석 + 본문 구조 draft가 완성되어 있었다. 새 세션은 이 draft를 검토/조정 후 본문화할 수 있다.

### 4.1 Block 46 `팀 빌딩` (quiet block)

**Phase0 slot:** "서동혁이 자기 수술에 맞는 보조 인력(간호사, 마취과)을 점차 확보한다. 비공식 독립 수술팀의 형성."

**Time:** 2028년 2월 초 (Block 45 defeat 흡수 후 1-2주)

**핵심 설계:**
- quiet block (tension 4)
- 4인 비공식 팀 구성: 정재훈(마취 펠로우, Block 22/25/26/31 등 누적 관계) + 김혜원(수술 간호사, Block 22/25) + 김재원(이식팀 간담도 펠로우, Block 31/32/38 태도 전환 완료) + **김수현(소화기내과 펠로우, Block 20 첫 타과 협진 호출 이후 비활성 → 재활성)**
- **I-31-40-B 해소**: FS-08 (김수현 협진 관계)이 ARC-04에서 비활성 상태였음. Block 46에서 Block 43 술식 개량 소문 → 간세포암 수술 적합성 판정 케이스에 김수현이 서동혁 사전 판독 의뢰 재가동. FS-08 reactivation.
- **R3' 준수**: 공식 독립 팀이 아닌 "수술별 보조 인력 우선 배정 요청" 수준. 조직 이탈 프레임 회피. 조영채 과장도 이 방식이 병원 내규 안에서 합법임을 확인.
- authority_delta: +1
- beat: `quiet_network_formation` 또는 유사

**주요 영수증:**
- (A) 4인 비공식 팀 구성 + 서동혁 수술 배정 시 우선 배치 관행
- (B) 김수현 협진 채널 재활성 (FS-08, I-31-40-B 해소)
- (C) 조직 이탈 프레임 회피 (과장 공식 확인)

### 4.2 Block 47 `이상훈의 도전`

**Phase0 slot:** "이상훈이 동일 난이도 케이스에서 서동혁과 성과를 비교하는 학회 발표를 기획한다. 학계에서 '28세 세대 대결' 구도가 만들어진다."

**Time:** 2028년 3월 초

**핵심 설계:**
- 대한외과학회 춘계 심포지엄 5월 말 예정 → 이상훈이 '간담도 고난도 수술 술식 개량 케이스 데이터 비교' 주제로 공동 패널 발표 제안 공식 연락
- Block 42 첫 대면에서 예고된 "다음 정면 대결 시점"의 구체화 (FS-22 payoff)
- 이상훈의 가설 명시: "경험 기반 접근법의 평균 성과는 케이스 volume의 함수. 서동혁 펠로우의 volume 부족에도 우수 수치인 이유를 데이터로 검증하고 싶다."
- 서동혁 수락 근거: (1) 검증 수락 → 방법론 투명성 공식화, (2) 거절 → "검증 회피" 암시 여지
- 조영채 과장도 동의: "검증 회피하면 학회 내 재현 가능성 의심 남는다"
- **R6' 준수 (원거리 감시 간접 언급)**: 이상훈이 "Block 43 케이스 시리즈 3건 + 표준 회귀 1건 논문 초안 이미 읽었다" 발화. 네 번째 케이스의 표준 회귀가 이상훈 관심을 끌었음 명시 = **FS-04 external_secondary_validation**.
- authority_delta: +1.5
- tension: 7
- beat: `accepted_challenge` 또는 유사

**주요 영수증:**
- (A) 학회 춘계 공동 발표 확정
- (B) 이상훈이 Block 43 표준 회귀 재평가 포인트 명시 (FS-04 외부 재확인)
- (C) audit R6' 원거리 감시 간접 언급 완성 (Block 42-47 5블록 간격 채움)

### 4.3 Block 48 `데이터 대결` (ARC-05 peak)

**Phase0 slot:** "학회에서 두 사람의 수술 데이터가 나란히 발표된다. 서동혁의 합병증률과 재수술률이 유의미하게 낮다. 인과가 규모를 이긴다."

**Time:** 2028년 5월 말

**핵심 설계 (전환 주의):**
- 장소: 대한외과학회 춘계 심포지엄, 구두 발표 세션. 각자 15분 발표 + 질의응답 30분. 청중 약 200명 (권혁수 외과학회 중진 포함)
- **이상훈 발표 먼저**: 한림외과대학 동일 카테고리 68건 (최근 12개월). 평균 출혈량 178 mL, 수술 시간 172분, 합병증률 3.2%, 재수술률 1.8%. 국내 상위권. 가설: "케이스 volume이 클수록 평균 성과가 수렴, 적은 volume의 우수 수치는 통계적 편차 가능성."
- **서동혁 발표 두 번째**: 본인 집도 4건 + 사전 판독 보조 12건 = 16건 (최근 6개월). 평균 출혈량 118 mL, 수술 시간 147분, 합병증률 0%, 재수술률 0%.
- **★ 전환 지점 ★**: 서동혁이 발표 마지막에 본인 수치를 자기 손으로 상대화. "본 데이터 볼륨 16건으로 이상훈 교수 68건 대비 현저히 작음. 통계적 유의성 일반화 제한적. 다만 각 케이스 메타데이터 시각이 외부 서버 기록으로 인과 경로 확인됨. 본 발표의 주장은 〈볼륨 대비 우수 수치〉가 아니라 〈인과 경로 증거〉이며, 볼륨이 커지면 평균은 이상훈 교수 수치에 수렴할 가능성이 높다."
- **Phase0 slot 문장 "인과가 규모를 이긴다"는 프레임을 본문에서 직접 주장하지 않고**, 서동혁이 자기 수치를 상대화하는 방식으로 다른 축(인과 vs 볼륨 분리)으로 전환. Phase0 표현의 정신은 유지하되 문자 그대로는 주장 안 함 → 규모 과시 경계 준수, 겸허함이 더 강한 설득력을 만듦.
- 청중 질문: "두 데이터는 상호 보완적인가요?" → 이상훈 마이크 잡고 답변:
  - "처음에는 서동혁 펠로우의 수치가 volume 편차인지 검증하려 했다. 메타데이터 시각 증거 축 확인 후 제 가설 자체가 다른 축을 보고 있었음을 알았다. 두 데이터는 경쟁이 아니라 상호 보완. 볼륨이 큰 쪽은 인과 경로 증거를 놓치기 쉽고, 볼륨 작은 쪽은 통계 일반화 제한. 두 접근 합쳐져야 완성도 높아진다."
  - 이것이 **이상훈의 "양립" 전환** — Phase0 이상훈 `summary: 데이터 검증 → 정면 대결 → 양립` 경로의 Block 48 payoff (Phase0 NPC key_turning_point 정확 일치).
- 권혁수가 청중에서 이 질의응답을 조용히 메모 (Block 49 seed).
- authority_delta: +3
- tension: 8 (ARC-05 peak, audit §8.3 권장과 정확 일치)
- beat: `framework_realignment` 또는 유사

**주요 영수증:**
- (A) 학회 공식 구두 발표 + 본인 수치 상대화로 프레임 주도권 확보
- (B) 이상훈 "양립" 전환 — Phase0 Block 48 key_turning_point 정확 payoff
- (C) "인과 축 vs 볼륨 축" 프레임 분리가 학회 공개 기록으로 남음
- (D) 권혁수 주목 (Block 49 seed)

### 4.4 Block 49 `학회 주목`

**Phase0 slot:** "외과학회 중진 권혁수가 서동혁에게 관심을 보인다. '논문보다 수술을 먼저 보고 싶다'는 초대."

**Time:** 2028년 5월 말 (Block 48 세션 종료 직후 같은 날 오후) ~ 6월 말 (권혁수 방문)

**핵심 설계:**
- **권혁수 첫 등장** (Phase0 new_npcs ARC-05 지정, Phase0 first_block: 49 정확 일치)
- 권혁수 프로필: 외과학회 중진, 대한간담췌외과학회 부회장 역임, 서울 중앙병원 외과 원로 교수(정년 2년 앞). 학술 라인 영향력 있음 — **"세계 최고 권위자"가 아님** (audit R4' 규모 경계 준수, work_guard custom_rules 준수)
- 권혁수 접근: "서동혁 펠로우, 세션 잘 들었습니다. 청이 하나 있습니다. **논문보다 수술을 먼저 보고 싶습니다**. 다음 달 중 서울 중앙병원 방문 초청 + 저의 수술실에서 좌엽 외측 구역 절제 1건 참관 + 수술 전 판독 노트 공동 검토 가능할지요."
- 권혁수 동기: 학술 라인 원로로서 "종이와 실제의 괴리"를 여러 번 본 경험. 논문보다 수술 현장 우선 검증. 합리적 학술 원로의 검증 요청, **감화 아님**.
- 서동혁 수락. 조영채 과장 보고. 조영채: "병원장 라인과 엮이지 않도록 방문 형식을 외부 학회 교류 차원으로 한정." (Block 44-45 병원장 라인 불이익 사정 범위 바깥의 자원 확보 맥락)
- 1개월 후 2028년 6월 말 서동혁이 서울 중앙병원 방문 (본 블록 내에서 요약 기술). 방문 결과: 권혁수가 판독 노트 경로 직접 확인 → 학회 내부 서동혁 지지 의사 형성
- authority_delta: +2
- tension: 7
- beat: `academic_recognition` 또는 유사

**주요 영수증:**
- (A) 권혁수 학술 라인 주목 + 방문 초청
- (B) 학회 경로로 병원장 라인 불이익 사정 범위 외곽에서의 새 자산
- (C) Phase0 ARC-05 emotion_curve "학회 주목" 달성
- (D) 국내 외과학회 내부 지지 네트워크 seed

### 4.5 Block 50 `조교수 후보` (ARC-05 exit)

**Phase0 slot:** "조영채 과장이 서동혁을 조교수 후보로 공식 추천한다. 펠로우에서 조교수 후보까지의 속도가 전례 없이 빠르다."

**Time:** 2028년 6월 말 ~ 7월 초 (권혁수 방문 직후)

**핵심 설계:**
- 조영채 과장이 서동혁 조교수 후보 추천을 외과 교수 인사 위원회에 공식 제출
- 전례 없는 속도: 통상 펠로우 2년 + R3-R4 수료 필수지만 서동혁은 특별 카테고리 R2 펠로우 9개월 + 누적 근거 축 다수
- **강태준 반응**: 이번에는 공식 반대 없음. **Block 40 불편한 공존 관계의 실질 작동 확인**. 완전 지지도 아닌 중립 관찰자 위치 유지.
- 조영채 추천서 근거 축 7개:
  1. 특별 카테고리 펠로우 자격 9개월 운영 실적
  2. Block 43 술식 개량 케이스 시리즈 후속 논문
  3. Block 48 대한외과학회 춘계 심포지엄 공동 발표
  4. Block 49 권혁수 학회 중진 관심 표명
  5. 독립 외래 9개월 운영 통계 (환자 진단 경로 전환 케이스 포함)
  6. 이식팀 사전 판독 보조 누적 운영 실적
  7. 수술 교육 위원회 레지던트 대표 + 판독 기반 사전 설계 선택 모듈 제안
- 인사 위원회 표결: **6:3 통과**
- 단서: "R2 직급 유지 상태의 조교수 후보"는 전례 없는 형식 → 본 추천은 "후보 등재" 수준, 실제 조교수 임용 결정은 외부 상위 심사 기구 (대학병원 인사 위원회) 심사 대기. **즉각 임용 아님**.
- **ARC-05 exit_function 3축 달성**:
  - 조교수 후보 ← Block 50
  - 독립 수술팀 ← Block 46 (비공식 4인 팀)
  - 국내 학회 주목 ← Block 48-49 (데이터 대결 + 권혁수)
- authority_delta: +3
- tension: 7
- beat: `structural_ascension` 또는 유사

**주요 영수증:**
- (A) 외과 교수 인사 위원회 조교수 후보 등재 확정
- (B) ARC-05 exit_function 3축 달성
- (C) 강태준 공식 반대 부재 = Block 40 불편한 공존 실질 작동
- (D) 실제 임용은 ARC-06 이후 상위 심사 대기 상태 (규모 과시 경계 준수 — 즉각 임용 방지)

### 4.6 ARC-05 누적 수치 (예상)

| | |
|---|---|
| 총 authority delta | 41-50: ~+14.5 |
| tension curve (실측+예상) | `5-6-7-7-6-4-7-8-7-7` |
| defeat blocks | [44] (단일) |
| quiet blocks | [46] (단일) |
| Phase0 일치 | defeat 44 ✓, quiet 46 ✓ |
| ARC exit 3축 | 조교수 후보 + 독립 수술팀 + 학회 주목 ✓ |

## 5. 새 세션이 반드시 읽어야 할 파일 (순서)

**1. 본 핸드오프 문서** (이 파일)

**2. 핵심 현재 상태 문서:**
- `docs/2026-04-08/hoegui_surgeon_live_status.md` (주의: Block 40 기준, 45까지 동기화 안 됨)
- `docs/2026-04-08/hoegui_surgeon_block_31_40_self_audit.md` (최신 10-block audit, Blocks 41-50 guardrails 포함)

**3. 소스 SSOT:**
- `material_ssot/20_pitch/canon/hoegui_surgeon.md` (canon pitch)
- `treatments/phase0/hoegui_surgeon_phase0_design.json` (특히 ARC-05 slot 46-50 block_slots)
- `work_guards/12_hoegui_surgeon.yaml` (mandatory_lexicon, forbidden_flattenings, role_fit_constraints, custom_rules)

**4. 라이브 TR:**
- `treatments/hoegui_surgeon_tr_block_020_draft.json` (특히 마지막 5블록 41-45의 필드 구조·톤·authority_before/after 체인 확인)

**5. 하네스 (필요 시):**
- `docs/blockguide/delegation-bootstrap.md`
- `docs/blockguide/treatment-production-harness-v2.md` §1.1B, §1.1C, §0G (block_cider 섹션)
- `material_ssot/00_governance/delegation-envelope-spec-v1.md`
- `material_ssot/00_governance/production-pair-schema-standard-v1.md`

**6. 참고 (이전 배치 audit 메모):**
- `docs/2026-04-08/hoegui_surgeon_block_21_25_batch_audit.md`
- `docs/2026-04-08/hoegui_surgeon_block_21_30_self_audit.md`

## 6. 핵심 Foreshadow 상태 (Block 45 기준)

### Closed (ARC-01~05 중반까지)
- FS-01 차트 기록 무기화 → Block 16 payoff
- FS-02 강태준 부교수 딜레마 → Block 40 **full_payoff** (6블록 체인 완결)
- FS-03-seed → FS-03 direct_entry (Block 37) → FS-03 secondary_encounter (Block 44)
- FS-05, 06 (ARC-02 소규모 FS, 클로즈)
- FS-07 단독 집도 유예 → Block 23 payoff → Block 40 장기 동결 상태
- FS-09 조영채 권한 얹음 → Block 26 full_payoff
- FS-11 유예 사정 범위 바깥 → Block 26 full_payoff
- FS-12 응급 집도 성공 분기 → Block 26 resolution
- FS-13 이상훈 원거리 인식 → Block 42 direct_encounter_payoff
- FS-14 정소연 관찰 조건부 → Block 32 full_payoff
- FS-15 강태준 평가서 → Block 33 payoff
- FS-16 비공식 판독 노트 채널 → Block 32 full_payoff
- FS-17 펠로우 조기 추천 → Block 38 payoff
- FS-18 R2 연차 독자 판독 카테고리 → Block 38 payoff
- FS-19 케이스 스터디 메타데이터 증거 축 → Block 36 full_activation → Block 38 활용
- FS-24 별도 사안 검토 불이익 예고 → Block 45 payoff

### Open, 다음 블록(46-50)에서 처리 예정
- **FS-22** 이상훈 "다음 정면 대결" (Block 42 seed) → **Block 47 payoff** 예정
- **FS-23** 후속 논문 (Block 43 seed) → **Block 49 근거 자산** 예정
- **FS-08** 김수현 협진 관계 (Block 20 seed, ARC-04 비활성) → **Block 46 재활성 권장** (I-31-40-B 해소)

### Open, 장기 대기
- **FS-04 경험의 한계** → Block 36 자연 기재 → Block 42 external_validation → Block 43 internal_realization (3단 체인 진행 중). Phase0 Block 65 full payoff 대기. ARC-05 후반에 추가 보강 가능 (Block 48 데이터 대결에서 "볼륨 한계" 언급이 간접 보강 가능)
- **FS-10** 단독 집도 유예 정식 심사 시한 → 장기 동결 (ARC-06 이후 재검토)
- **FS-20** 판독 기반 사전 설계 교육 커리큘럼화 → Block 60 "교육 재편" payoff 대기
- **FS-21** 강태준 "초기 지도 방향 설정" 자기 보호 첨언 → Phase0 Block 68 payoff 대기 (audit I-31-40-C: Block 55-60 중간 리마인드 권장)

## 7. 캐리오버 이슈 (Block 46+ 생산 시 주의)

| id | 내용 | 처리 상태 | Block 46-50에서의 처리 권장 |
|---|---|---|---|
| I-02 | Tier B migration debt (`block_cider.*` + `capital_*` 미탑재, Blocks 1-45 전부) | carry-over, non-blocking | 무처리 (일괄 `schema_backfill` 별도 envelope 대기) |
| I-03 | Block 25 regression_hint 해설 톤 | carry-over, non-blocking | 선택 polish |
| I-04 | Block 20/21 authority_before 접미 정렬 | carry-over, non-blocking | 선택 polish |
| I-31-40-A | Block 33 5월 심사 결과 사후 노출 | carry-over (Block 40에서 정렬됨) | 선택 polish |
| I-31-40-B | FS-08 김수현 비활성 | carry-over | **Block 46 팀 빌딩에서 재활성 권장 (상세 §4.1 참조)** |
| I-31-40-C | FS-21 중간 리마인드 앵커 필요 | carry-over | Block 55-60에서 처리 (46-50 범위 밖) |

## 8. 필드 구조 레퍼런스 (블록당 필수 키)

Blocks 41-45와 동일 구조 유지:

```
block_id / block_no / title
content: {context, event_villain, solution, reward}
stakes
power_shift: {protagonist, antagonist}
relationship_delta: [{target, before, after}, ...]
foreshadow: [{id, type, description}, ...]
callback: [{id, type, description}, ...]
emotional_beat: {type, intensity}
tension_level
pov_character
location: {place, type}
time_span: {duration, in_story_time}
genre_ext: {
  type: "medical_authority",
  authority_before, authority_after, authority_delta,
  method, opponent: {name, type, weakness_exploited},
  medical_sector, section_rotation
}
regression_ext: {
  is_regressor: true,
  regression_type: "회귀",
  timeline_knowledge: {info_used, accuracy, source},
  butterfly_effect: {original_event, changed_event, ripple_effect},
  regression_hint: {slip_up, suspicion_from},
  incarnation_type: "회귀자",
  execution_doctrine
}
```

- **중요**: canonical `genre_ext.block_cider.*` 및 `capital_before/after/delta` 필드는 **탑재 금지** (Blocks 1-45 전부 미탑재 상태, 일관성 유지). `authority_before/after/delta`가 work-local 관행.

## 9. 쓰기 절차 (새 세션용)

### 9.1 사전 검증

```bash
python -c "
import json
p=r'C:/Users/wjjo/Desktop/글도비/treatments/hoegui_surgeon_tr_block_020_draft.json'
d=json.load(open(p,encoding='utf-8'))
assert d['_saved_block_boundary']==45
assert len(d['blocks'])==45
assert d['_next_continuation_boundary']==46
print('handoff state verified: boundary=45, ready for Block 46')
"
```

### 9.2 생산 스크립트 위치 (기존 관행)

- 작업 디렉토리: `C:/Users/wjjo/Desktop/글도비/.tmp_scripts/`
- 파일명: `append_blocks_46_50.py` 또는 블록별 분할
- 스크립트는 UTF-8 file로 작성 (bash heredoc은 한글에서 실패, Write 도구 사용)
- 실행 후 temp 파일 삭제 관행 (`rm .tmp_scripts/xxx.py && rmdir .tmp_scripts`)

### 9.3 스크립트 내부 invariants (반드시 확인)

```python
# 사전
before_blocks_serialized = json.dumps(d["blocks"], ensure_ascii=False, sort_keys=True)
assert len(d["blocks"]) == 45
assert d["_saved_block_boundary"] == 45

# 각 블록 필드 체크
for b in new_blocks:
    for k in ("block_id","block_no","title","content","stakes","power_shift",
              "relationship_delta","foreshadow","callback","emotional_beat",
              "tension_level","pov_character","location","time_span",
              "genre_ext","regression_ext"):
        assert k in b

# 사후 (Block 50까지)
d["blocks"].extend(new_blocks)
assert [b["block_no"] for b in d["blocks"]] == list(range(1, 51))
d["_saved_block_boundary"] = 50
d["_next_continuation_boundary"] = 51

# byte-equal invariant
assert json.dumps(d["blocks"][:45], ensure_ascii=False, sort_keys=True) == before_blocks_serialized
```

### 9.4 생산 후 검증 명령

```bash
python -c "
import json
p=r'C:/Users/wjjo/Desktop/글도비/treatments/hoegui_surgeon_tr_block_020_draft.json'
d=json.load(open(p,encoding='utf-8'))
assert d['_saved_block_boundary']==50
assert len(d['blocks'])==50
assert [b['block_no'] for b in d['blocks']] == list(range(1, 51))
print('Block 50 write validated')
"
```

### 9.5 Block 50 완료 직후 필수 액션

**harness §1.1C 강제**: Blocks 41-50 10-block self-audit 작성
- 파일 경로: `docs/2026-04-08/hoegui_surgeon_block_41_50_self_audit.md`
- 구조: 이전 `hoegui_surgeon_block_31_40_self_audit.md` 형식 따르기
- 6-axis check + work_guard forbidden_flattenings + ARC-05 exit_function + NPC 정합 + issues + next 10 focus (ARC-06 51-60)
- PASS/FAIL 판정 + ready_for_block_51

### 9.6 Block 51 진입 전 권장

- **선행**: `status_sync` envelope — `docs/2026-04-08/hoegui_surgeon_live_status.md`를 Block 50 경계 + ARC-05 exit + 본 10-block audit 결과로 동기화 (현재 Block 40 기준 상태)
- 이 status_sync는 Block 50 audit 이후 별도 턴/오더에서 수행 권장

## 10. ARC-06 (Block 51-60) 사전 노트 (10-block audit 시 반영)

ARC-06 `병원의 칼` 정보 (Phase0 참조):
- time_window: 2028년 7월 ~ 2029년 6월
- capital_target: 과 운영 실권 + 병원장 라인 독립 + 수술 교육 체계 재편 시작
- main_opponents: 나경태 (병원장, 은폐) / 외과 일부 교수진 (기득권)
- new_npcs: 한미정 (의료 전문 기자)
- quiet_blocks: [56]
- defeat_blocks: [54, 55]
- 주요 payoff: **FS-03 은폐 사건 표면화 Block 52-58** (Block 37/44 병원장 라인 중립 거리 유지가 ARC-06 전환), **FS-21 강태준 리마인드 Block 55-60 (audit I-31-40-C)**

ARC-06 진입 준비는 본 핸드오프 범위 밖이지만, Block 41-50 audit에서 "next 10 focus = ARC-06"로 다루게 됨.

## 11. 사용자 커뮤니케이션 스타일

사용자 특성 (메모리 + 본 작업 관찰 기반):
- 한국어, 단문 오더 선호 ("ㄱㄱ", "35까지", "이후 audit 알지?", "50까지 1개씩 정성껏")
- "하네스대로 치고"식 원칙 환기 방식
- 중간 확인 없이 진행 가능 + 완결 보고 선호
- 5블록 배치, 10블록 audit을 리듬으로 사용
- 사용자가 "이후 audit" 한 줄로 harness §1.1C 자동 실행 기대함

다음 턴 보고는:
- 변경 파일
- 새 saved boundary
- 각 블록 one-line receipt
- 주요 foreshadow 상태
- guardrail 준수 확인
- next gate

이전 턴 보고 스타일(예: Block 43-45 보고) 참조.

## 12. 재개 첫 응답 템플릿

새 세션 Claude의 첫 응답은 다음 중 하나:

**Option A** (즉시 생산 진입):
```
핸드오프 컨텍스트 수신 확인. Block 45 boundary 검증 완료.
Block 46-50 1-block envelope 순차 생산 진행.
[각 블록 생산 로그]
Block 50 완료 → harness §1.1C 10-block audit 진입.
[audit 메모 작성]
[통합 보고]
```

**Option B** (추가 확인 요청):
```
핸드오프 수신. Block 45 boundary 확인.
재개 전 확인 사항:
1. "1개씩 정성껏"의 해석 — 5블록 단일 스크립트 배치 vs 블록당 중간 확인 삽입
2. Block 50 직후 10-block audit 같은 턴 처리 여부
사용자 방향 확인 후 진행하겠습니다.
```

권장: **Option A**. 사용자 이전 패턴("35까지 순차 생산 후 대기", "40까지 순차 진행 이후 audit")이 모두 단일 배치 + 완결 보고였음. "1개씩 정성껏"은 블록 품질 강조이지 중간 확인 요청 아님. Block 50 완료 후 audit까지 같은 턴 처리가 하네스 강제와 부합.

## 13. 위험 요소 (새 세션이 피해야 할 것)

- **블록 축약 금지**: 이전 ARC-05 블록들(41-45)의 content 필드 분량(약 800-1500자)을 맞춰야 "정성껏"의 기준 충족. 줄이면 품질 저하로 인식됨.
- **Phase0 slot 본문 그대로 복사 금지**: Phase0 slot은 요약이고 TR은 장면이다. Phase0 "인과가 규모를 이긴다"(Block 48)를 문자 그대로 주장하면 규모 과시 경계 침범 위험. 정신은 유지하되 본문 표현은 우회 (서동혁 자기 상대화 방식 등).
- **강태준/나경태/이상훈/권혁수 캐리커처 방지**: 모두 합리적 동기. 특히 권혁수는 "세계 최고 권위자" 아님, "외과학회 중진" 수준으로 한정.
- **정소연 감화 금지 연장**: ARC-05 블록에서 정소연 재등장 시 계산 기반 결 유지.
- **서동혁 발화 최소**: Block 46-50 범위에서도 발화는 한 문단 수준, 능력 장광설 금지.
- **Block 50이 완전 임용 아님**: "조교수 후보 등재"까지만. 실제 임용은 ARC-06 이후 상위 심사 대기. 즉각 임용은 규모 과시 경계 침범 + Phase0 곡선 왜곡.
- **FS-08 김수현 Block 46 재활성**: 누락 시 I-31-40-B가 carry-over로 ARC-06까지 넘어감. 재활성은 본문에 자연 삽입 (억지 삽입 금지).
- **권혁수 Phase0 first_block 49 일치**: Block 48에서 "청중 메모"는 seed만, 직접 접근은 Block 49에서. first_block 정합성 유지.

## 14. 메모리 상태

`C:\Users\wjjo\.claude\projects\C--Users-wjjo-Desktop----\memory\` 메모리 시스템:
- MEMORY.md 인덱스 현재 유지
- 본 `hoegui_surgeon` 세션에서 새 메모리 저장 없음 (ARC 작업은 세션 단위 컨텍스트, 장기 메모리 대상 아님)
- 새 세션이 필요 시 `feedback_no_code_modification.md`, `feedback_remote_first.md` 등 기존 피드백 참조

## 15. 최종 체크리스트 (새 세션 재개 전)

- [ ] 본 핸드오프 문서 전체 1회독
- [ ] TR 파일 `_saved_block_boundary==45` 검증
- [ ] Blocks 41-45의 authority chain 및 톤 확인 (`genre_ext.authority_before/after/delta`)
- [ ] Phase0 ARC-05 slot 46-50 정독
- [ ] work_guard forbidden_flattenings + role_fit_constraints 재확인
- [ ] 최근 10-block audit (`block_31_40_self_audit.md`) §8 next 10 focus 재확인
- [ ] `.tmp_scripts/` 디렉토리 쓰기 가능 확인
- [ ] Block 46-50 생산 → byte-equal invariant → Block 50 audit → 통합 보고 순서 준비

---

_본 문서는 hoegui_surgeon ARC-05 생산의 중간 지점에서 다른 PC로 작업을 이어받기 위한 컨텍스트 묶음이다. 수신자는 이 문서 + §5의 필수 읽기 파일만 읽으면 Block 46부터 동일한 guardrail과 톤으로 이어서 쓸 수 있어야 한다._

_Author: Claude (source session, 2026-04-08)_
_Target: Claude (new PC session, any time after transfer)_
