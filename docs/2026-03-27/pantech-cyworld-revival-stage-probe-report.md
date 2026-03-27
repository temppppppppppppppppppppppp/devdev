# pantech_cyworld_reborn Revival-Stage Probe Report

Date: 2026-03-27
Type: bounded revival-stage probe (ladder Step 6)
Target pair:
- BI: `bible/_quarantine/07_pantech_cyworld_reborn_bi.json`
- TR: `treatments/_quarantine/07_pantech_cyworld_reborn_tr_block_070_draft.json`

Prior artifacts:
- Consumability repair: `docs/2026-03-26/pantech-cyworld-bi-tr-consumability-repair-report.md`
- TR static audit: `docs/2026-03-27/pantech-cyworld-tr-static-quality-audit.md`
- BI repair: `docs/2026-03-27/pantech-cyworld-bi-repair-note.md`
- Revival canary: `docs/2026-03-27/pantech-cyworld-revival-canary-report.md`

---

## 1. Runtime Admission (§8.1)

### 1.1 Pair Load

| Check | Result |
|-------|--------|
| TR JSON parse | **PASS** |
| BI JSON parse | **PASS** |
| TR block count | 70 |
| BI MasterBible top keys | 13 (9 baseline + 4 additive) |

### 1.2 plot_roadmap Readiness

| Check | Result |
|-------|--------|
| block_no coverage | 70/70 |
| block_no range | 1-70 |
| Title sync TR↔BI (Block 1-10) | **PASS** (0 mismatches) |

### 1.3 Protagonist-Facing Runtime Keys

| Key | Status |
|-----|--------|
| `protagonist_config.name` | OK (윤도현) |
| `protagonist_config.world_origin` | OK (현대인) |
| `protagonist_config.incarnation_type` | OK (회귀자) |
| `protagonist_config.pov` | OK (1인칭 제한 시점) |
| `protagonist_config.external_pov_insert_policy` | OK |
| `protagonist_config.regression_mechanic` | OK (5 sub-fields) |
| Protagonist consistency (CoreIdentity = FinanceHUD = config) | **PASS** (윤도현) |

### 1.4 Schema Drift

| Check | Result |
|-------|--------|
| Baseline 9 keys present | **PASS** (9/9) |
| Additive keys | `ArcStructure`, `OpponentTransitionPlan`, `BackHalfTechIdentityAnchors`, `PayoffTrack` |
| New key values JSON-safe | **PASS** |
| Regression codepath consistency | **PASS** (incarnation_type=회귀자, regression_mechanic present) |

### 1.5 TR Field Coverage (Block 1-10)

All 12 required block fields + 4 content sub-fields present across Block 1-10. **PASS**.

### Runtime Admission Verdict: **PASS**

---

## 2. Stage 2 Bounded Probe (§8.2)

### 2.1 Probe Window

Arc 1: **판 벌리기 — 팬택+싸이월드 결합체 구축** (Blocks 1-10, 0억 → 1,030억)

### 2.2 Arc Document

#### Arc 1 — 판 벌리기

**기간**: 2006년 1월 중순 ~ 2006년 5월 말 (약 5개월)
**자본 궤적**: 0억 → 350 → 290↓ → 430 → 505 → 455↓ → 620 → 560↓ → 700 → 880 → 1,030억
**패배 블록**: 3/10 (Block 2, 5, 7에서 자본 감소)

**핵심 전장 4축**:

1. **통신사 인증/규격 카르텔** (Block 4, 5, 6, 8)
   - 통신사별 인증 규격 차이가 시연 현장에서 연쇄 충돌로 터짐 (Block 5 코엑스 참사)
   - 312종 기기 충돌 로그 → 품질검증센터 인수로 병목을 내재화 (Block 5→6)
   - 통신사가 규격 변경 시점을 숨기고 윤도현 탓으로 전가 → 충돌 로그+내부 메일로 역추적 입증 (Block 8)
   - **구체적 오브젝트**: 312종 기기 충돌 로그, 통신사별 인증 변경 내부 메일, 정보통신부 시범 허가 문서

2. **앱 장터/첫 화면/결제 흐름** (Block 3, 4, 6, 9)
   - 싸이월드 도토리 결제 흐름을 외부 서비스가 붙을 수 있게 재설계 (Block 4)
   - 팬택 터치 UI + 싸이월드 일촌 + 도토리 결제를 한 화면으로 통합 (Block 3→6)
   - 베타폰 첫 화면: 켜자마자 친구 목록·사진·결제가 한 호흡 (Block 6)
   - **구체적 오브젝트**: 터치 UI 프로토타입, 경량 실행 틀 기술사용권, 베타폰 첫 화면 시안, 도토리 결제 연동

3. **재벌 승계/내부 감사 전쟁** (Block 1, 7, 10)
   - CB 발행으로 개인 책임 자금 조달 → 차우진 특별감사 공세 (Block 7)
   - ABS로 자금 흐름을 그룹 결재선 밖으로 분리 (Block 7)
   - 디지털 계열 분리 공식 안건 상정 (Block 10)
   - **구체적 오브젝트**: 전환사채 발행 조건서, 신탁사 자산유동화 계약서, 계열 분리안

4. **회귀자 엔진/의심 누적** (전 블록)
   - 아이폰 쇼크, 앱스토어 등장, 싸이월드 모바일 전환 실패 시점 지식이 모든 판단의 기저
   - "아직 일어나지 않은 일을 지나치게 정확히 말할 때마다 의심 누적" — regression_hint.slip_up 10개 블록에 걸쳐 작동
   - Block 1-10 구간: 정민석(의심 2회), 오세라(의심 2회)가 초기 의심 시드

**아크 해상도 — 장면으로 읽히는가?**

| Block | 핵심 장소 | 촉각적 오브젝트 | 대화 마커 |
|-------|-----------|-----------------|-----------|
| 1 | 세림그룹 본관 28층 전략회의실 | 일정표와 손익 구조, 개인 주식 담보 | 차우진 "도련님이 또 유행어 하나 주워 왔다" |
| 2 | 김포 팬택 연구개발센터 + 채권단 회의실 | 통신사 보조금 회의록, 터치 UI 프로토타입, 내부 인력 지도 | 오세라 "단말보다 주소록이 더 무섭다" |
| 3 | 서초 프론티어 원 + 싸이월드 협상 테이블 | 미니홈피 관계망 시안, 도토리 결제 기록 | 윤도현 "하드웨어만 살려서는 안 됩니다" |
| 4 | 대덕 미들웨어 연구실 + 회장실 | 경량 실행 틀 라이선스, 열린 도토리 결제 흐름 | "첫 화면을 누가 소유하느냐" |
| 5 | 코엑스 시연장 + 가산 품질검증센터 | 312종 기기 충돌 로그, 깨진 화면 | "망신은 컸지만 병목 데이터를 건졌다" |
| 6 | 송도 비공개 쇼케이스홀 + 부평 시제작 라인 | 베타폰 실물, 첫 화면 → 친구→사진→결제 시퀀스 | "한국에서 처음으로 첫 화면이 서비스와 붙었다" |
| 7 | 성북동 회장 저택 집무실 + 여의도 신탁사 | ABS 계약서, 자금 방화벽 구조도 | "감사하시라 하세요. 다만 돈은 이미 이쪽에 있습니다" |
| 8 | 과천 정보통신부 심의실 + 감사위원회 | 충돌 로그 vs 인증 변경 시점 대조표, 내부 메일 | 박기태의 증언 |
| 9 | 홍대 체험존 + 잠실 간담회장 | 얼리어답터 후기 화면, 사진 인화 + 음악 구독 묶음 | 입소문 "켜자마자 친구가 살아 움직인다" |
| 10 | 한빛전자마트 본사 + 전략조정실 | 소매 합작 계약서, 체험 부스 설계도, 계열 분리안 | 윤재문 "검토 안건으로 올려라" |

**복선-회수 체인 (Block 1-10)**:
- Block 1→2: 통신사 보조금 회의록 → 팬택 채권 인수 타이밍
- Block 1→3: "하드웨어만 살려서는 안 된다" → 팬택+싸이월드 통합 인수 명분
- Block 2→3: "단말보다 주소록이 더 무섭다" → 싸이월드 인수 핵심 문장
- Block 2→5: 터치 UI 프로토타입 → 앱 장터 시연 껍데기
- Block 3→6: 첫 홈 화면 시안 → 베타폰 공개 얼굴
- Block 4→5: 인증 규격 충돌 경고 → 코엑스 연쇄 오류
- Block 4→6: 도토리 결제 흐름 → 사전 등록 전환율
- Block 5→6: 살아남은 화면 조합 → 베타폰 최종 화면
- Block 5→8: 312종 충돌 로그 → 감사 역전 증거
- Block 6→7: 윤재문 별도 보고 지시 → 차우진 감사 공세
- Block 6→9: 얼리어답터 명단 → 입소문 도화선
- Block 7→10: 자금 방화벽 → 계열 분리 명분
- Block 8→9: 감사위 사용 영상 → 대중 후기 불씨
- Block 8→10: 시범 허가 문서 → 소매 계약 법적 방패

10개 블록 안에서 **14개 복선-회수 체인**. 평균 1.4회수/블록. 무작위가 아니라 인과적 체인.

### 2.3 Stage 2 판정

| 기준 | 결과 |
|------|------|
| 통신/인증/QA/앱/첫화면/결제 전장이 살아 있는가 | **YES** — 4축 전장 모두 구체적 오브젝트와 장소 포함 |
| 회귀 주인공 엔진이 명확히 읽히는가 | **YES** — 미래 지식 기반 판단이 모든 블록의 solution 엔진 |
| 결과물이 실제 장면 압력이 있는 아크 문서인가, 거래 요약인가 | **장면 압력 있음** — 10개 블록 모두 고유 장소, 촉각적 오브젝트, 대화 마커 존재 |
| 자본 궤적에 패배가 있는가 | **YES** — 3/10 블록에서 자본 감소 (Block 2: -60억, Block 5: -50억, Block 7: -60억) |
| 복선-회수 밀도 | **PASS** — 14개 인과 체인 / 10 블록 |

**Stage 2 Probe Verdict: PASS**

---

## 3. Stage 3 Bounded Probe (§8.3)

### 3.1 Episode 1 Blueprint

**Source Block**: Block 1 "벽돌 더미 속 미래 지도"
**에피소드 기획 범위**: Block 1 전체 (5일, 2006년 1월 중순)

---

#### Episode 1: 벽돌 더미 속 미래 지도

**에피소드 목표**: 회귀 순간부터 첫 자금 확보까지. 윤도현이 2024년 고독사에서 2006년 전략회의로 깨어나, CB 발행을 관철해 350억의 전시 자금을 확보한다.

**장면 구조**:

**Scene 1 — 깨어남 (회귀 순간)**
- 시점: 윤도현 1인칭
- 장소: 서울 중구 세림그룹 본관 28층 전략회의실. 겨울 아침 햇살이 유리 테이블에 반사. 회의 자료 표지에 '2006년 그룹 전략방향 수립'이라는 글자.
- 감각 단서: 유리창에 비친 서른한 살의 얼굴, 피처폰이 놓인 테이블, 노트북이 아닌 종이 바인더, 건물 밖 아직 스마트폰이 없는 서울 거리의 공기
- 내면: 2024년 임대 오피스텔에서 죽었던 기억. 팬택이 벽돌 더미가 된 날. 싸이월드가 미끄러진 날. 전부 기억한다.
- 단서 심기: 테이블 위 휴대폰은 팬택 피처폰. 아직 살아 있는 회사.

**Scene 2 — 전략회의 (적대 세력 첫 대면)**
- 시점: 윤도현 1인칭
- 장소: 같은 회의실. 윤재문 회장이 상석, 차우진 CFO가 슬라이드 제어기를 쥠. 각 계열 대표 8명.
- 대화:
  - 차우진: "도련님이 또 유행어 하나 주워 왔다." (슬라이드를 넘기며, IT 안건이 마지막 보고 뒤에 끼워진 것을 보여줌)
  - 윤재문: "휴대폰과 인터넷은 언젠가 해외 거인에게 먹힐 소모품이야."
- 감각 단서: 차우진이 슬라이드 제어기를 클릭하는 소리, 건설 계열 보고 때 고개 끄덕이던 임원들이 IT 안건에서 시선을 거두는 온도 변화
- 회귀 엔진 작동: 윤도현은 2007년 6월 아이폰이 나온 뒤 이 회의실 공기가 어떻게 바뀌었는지 안다. 하지만 지금 그걸 말하면 미친 사람이다.
- 전생 대비: 전생의 윤도현은 여기서 입을 다물었다. 유통 계열사로 밀려났고, 결국 고독사했다.

**Scene 3 — 역제안 (solution 실행)**
- 시점: 윤도현 1인칭
- 장소: 같은 회의실, 윤도현이 자리에서 일어남.
- 핵심 대사:
  - 윤도현: "2007년 여름이면 운영체제와 앱 유통 구조가 단말기보다 중요해집니다. 국내에는 아직 하드웨어와 사용자 관계망을 동시에 가진 사업자가 없습니다."
  - (회귀 slip-up 순간) 차우진의 눈이 좁아짐 — "2007년 여름이면"이라는 너무 구체적인 시점. 아직 아무도 모르는 미래.
  - 윤도현: "그룹 본체가 아니라 제 이름으로 합니다. 개인 주식 담보 180억, 실험 예산 170억. 실패하면 제 지분과 이사 자리로 책임집니다."
- 감각 단서: 윤도현이 꺼낸 A4 두 장 — 일정표와 손익 구조. 볼펜이 아닌 만년필로 적은 숫자 (전생에서 수백 번 계산한 숫자).
- 긴장: 윤재문이 안경 너머로 A4를 읽는 시간. 5초가 5분처럼.

**Scene 4 — 승인 (보상)**
- 시점: 윤도현 1인칭
- 장소: 회의실 → 복도. 윤재문이 나가며 뒤돌아봄.
- 핵심 대사:
  - 윤재문: "CB로 하자. 실패하면 네 지분이다." (비웃지만, 처음으로 A4를 들고 나온 손자에게 '판을 열어 준' 순간)
  - 차우진 (복도에서, 윤도현에게): "실무 자료는 접근해도 됩니다. 다만 그 일정표대로 안 되면 제가 직접 감사를 겁니다." (경계하면서도 숫자만큼은 인정)
- 감각 단서: 복도 유리창 너머로 보이는 서울 한강. 2006년의 서울. 이 도시에는 아직 스마트폰이 없다. 아이폰은 18개월 뒤.
- 회귀 엔진 마감: 윤도현의 주머니 속 팬택 피처폰이 진동한다. 정민석이 보낸 문자: 통신사 보조금 회의록 입수. (Block 2 복선)

**Scene 5 — 프론티어 원 설립 (에피소드 마감)**
- 시점: 윤도현 1인칭
- 장소: 서초동 임대 사무실. 프론티어 원 명판을 손으로 건드림.
- 내면 마감: "350억. 전생의 나는 0원으로 죽었다. 이번에는 이 돈이 팬택 채권과 싸이월드 협상 테이블에 동시에 꽂히는 첫 송곳이 된다."
- 시간 마커: 2006년 1월 하순. 아이폰 출시까지 18개월. 카운트다운 시작.
- 긴장 잔여: 차우진은 돌아서며 "그 일정표"를 기억할 것이다. 정민석의 문자가 진동한다. 싸움은 이제 시작.

---

### 3.2 Stage 3 판정

| 기준 | 결과 |
|------|------|
| 장면 구조가 있는가 | **YES** — 5장면, 각각 고유 목표·전환점·마감 |
| 캐릭터 목소리가 분리되는가 | **YES** — 윤도현(내면 회귀 지식), 차우진(비웃음→경계), 윤재문(냉소적 승인), 정민석(정보 연결) |
| 공간/감각 단서가 있는가 | **YES** — 회의실 유리 반사, 피처폰, A4 만년필, 복도 유리 너머 한강, 사무실 명판 |
| 2006 한국 모바일 전쟁 + 재벌 승계 압력이 살아 있는가 | **YES** — "아이폰 18개월 전", CB 발행, 통신사 보조금 회의록, 승계위원회 정치 |
| generic civic infrastructure 추상화로 빠졌는가 | **NO** — Block 1은 front half로 tech texture 최고 구간, 드리프트 없음 |

**Stage 3 Probe Verdict: PASS**

---

## 4. What Survived Runtime Translation

1. **통신/인증/QA 전장 — 완전 생존**
   - 312종 충돌 로그, 통신사별 규격 차이, 가산 품질검증센터 인수가 Block 5-8에서 핵심 플롯 엔진으로 작동
   - 정보통신부 심의실 장면에서 기술 정치 병목이 장면 수준으로 발현

2. **앱 장터/첫 화면/결제 전장 — 완전 생존**
   - Block 3-6에서 미니홈피 → 모바일 주소록, 도토리 → 결제 흐름, 첫 화면 점령이 구체적 오브젝트 수준으로 작동
   - "한국에서 처음으로 첫 화면이 서비스와 붙었다"는 문장이 장면 안에서 숨 쉼

3. **회귀 엔진 — 완전 생존**
   - Block 1 Scene 3의 "2007년 여름이면"이 slip-up으로 작동
   - 미래 지식 기반 판단이 모든 solution의 엔진
   - 의심 누적이 정민석·오세라 경로로 시작

4. **재벌 승계 전쟁 — 완전 생존**
   - CB 발행 → 감사 공세 → ABS 방화벽 → 계열 분리 체인이 Block 1→7→10으로 관통
   - 차우진의 아크가 "비웃음 → 감사 칼 → 규격 조작 배후 → 계열 분리 저지"로 명확히 발전

5. **자본 궤적 — 완전 생존**
   - 10개 블록에서 8종 deal_type (CB, 부실자산 인수, 우호적 M&A, 기술 라이선싱, 공급망 수직통합, JV, ABS, 정부 허가, 컨소시엄 입찰)
   - 3회 패배(자본 감소)가 모두 서사적 의미를 가짐

## 5. What Weakened or Flattened

1. **회귀 slip-up 구체화 정도 — 약간 약화**
   - TR에 `regression_hint` 필드가 존재하지만, Block 1-10 구간에서 직접 확인한 slip-up trigger와 suspicion_source가 TR 본문의 context/solution 내러티브 안에 직접 서술되기보다는 `regression_ext` 메타데이터에 분리되어 있음
   - BI의 `regression_mechanic`이 이를 보상하지만, 실제 원고 생성 시 Stage 4가 메타데이터를 장면 안으로 끌어와야 하는 추가 작업 발생 가능
   - **등급: 경미** — 구조적으로 존재하므로 Stage 4에서 처리 가능

2. **단일 POV — 구조적 한계 유지**
   - 10개 블록 전부 윤도현 POV. 차우진의 내면, 오세라의 내면, 정민석의 동기가 외부 행동으로만 추론됨
   - BI `external_pov_insert_policy`가 "적대자 내면 또는 동맹 시점 에피소드에서 제한적 허용"이라고 명시
   - **등급: 알려진 한계** — TR 구조적 제약. BI가 정책으로 보상하나 실효는 Stage 4에서 확인 필요

3. **숫자 구체성 — TR 본문에서 약함**
   - 투자 금액, 지분율, CB 조건 등이 `genre_ext` 메타데이터에 풍부하지만, context/solution 서술에서는 "350억", "180억" 같은 큰 숫자만 등장
   - 구체적인 CB 전환 조건, 지분율 수치, 밸류에이션 배수 등은 BI `FinanceHUD.portfolio_history`에 있으나 TR 서술에는 미내재화
   - **등급: 경미** — Stage 4가 BI FinanceHUD에서 가져오면 해소 가능

4. **후반부 드리프트는 이번 probe 범위 밖**
   - Block 1-10은 front half이므로 tech/startup texture가 최강 구간
   - 후반부(Block 40+) 드리프트는 TR static audit에서 이미 보고됨
   - BI `BackHalfTechIdentityAnchors`가 보상 구조를 제공하나, 실효는 후반 probe에서 확인해야 함
   - **등급: 알려진 리스크** — 이번 probe 범위 밖, 별도 후반 probe 또는 Stage 4 canary에서 확인

---

## 6. Final Verdict

**PASS**

근거:
- Runtime admission: clean zero-warning pass
- Stage 2: Arc 1 아크 문서가 4축 전장(통신/인증, 앱/결제, 재벌 승계, 회귀 엔진) 모두에서 장면 수준 압력을 유지
- Stage 3: Episode 1 블루프린트가 5장면 구조, 캐릭터 음성 분리, 공간/감각 단서, 2006 한국 모바일 전쟁 질감을 모두 갖춤
- 약화된 부분(slip-up 메타데이터 분리, 단일 POV, 숫자 서술 미내재화)은 모두 "경미" 또는 "알려진 한계"이며, Stage 4 단계에서 처리 가능한 수준

**이 pair는 active promotion 자격을 충족한다.**

---

## 7. Next Unit

**active promotion** — quarantine pair를 active candidate path로 복사/이동하고 promotion note를 남긴다.

---

```text
work_id: pantech_cyworld_reborn
current_stage: audit_or_repair
finished_unit: revival-stage probe
changed_files: docs/2026-03-27/pantech-cyworld-revival-stage-probe-report.md
next_unit: active promotion
stop_reason: probe passed — runtime admission clean, Stage 2 arc document retains scene-level pressure across 4 battlefield axes, Stage 3 blueprint delivers scene structure with separated voices and sensory cues
```
