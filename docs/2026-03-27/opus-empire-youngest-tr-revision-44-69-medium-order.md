# OPUS Empire Youngest — Targeted TR Revision Order (Block 44-69 MEDIUM)

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `empire_youngest_allsector`
Predecessor chain:
1. `docs/2026-03-27/empire-youngest-truth-reaudit-report.md` (re-audit, verdict MIXED)
2. `docs/2026-03-27/empire-youngest-weakness-report.md` (5-axis gap catalog)
3. `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md` (Block 32-43 확장 완료, ×2.51)
4. `docs/2026-03-27/empire-youngest-tr-revision-44-69-high-changelog.md` (Block 44-69 HIGH 7블록 확장 완료, ×3.79)

## 1. Order Intent

This order fixes the target to `empire_youngest_allsector` Block 44-69 중 **MEDIUM priority 9블록**만 확장한다.

- `targeted TR revision — Block 44-69 MEDIUM priority`

이 블록들은 **섹터 진입 블록**이다. 서사 spine(HIGH)은 이미 완료됨. 이번 런의 핵심 과제는 **domain texture 복원** — 각 섹터의 고유 언어, 장면, 기술 디테일을 살리는 것.

대상 블록:

| block_id | title | current chars | sector | core restoration need |
|----------|-------|--------------|--------|----------------------|
| **Block 44** | PE 1호 펀드 5조 | 230 | 금융/PE | 국민연금 LP 설득, 정하윤 기관 대면 |
| **Block 45** | PE 첫 딜: 새한저축은행 | 173 | 금융/핀테크 | 오승아 금융 인가, Block 46 setup |
| **Block 47** | K-럭셔리 + 파리 패션위크 | 147 | 패션/럭셔리 | 유럽 냉소→K-pop 역전, visual spectacle |
| **Block 53** | 코리아뉴클리어 인수 | **105** | 에너지/SMR | **content 최소 블록**. heavy-tech domain texture 0 |
| **Block 55** | 드론 스타이포스 | 344 | 방산 | 방위사업청 납품, AI 드론 시연 |
| **Block 56** | 서해안 해상풍력 | 256 | 에너지/풍력 | 입찰 경쟁, 현장 texture |
| **Block 57** | 반핵 시위 / SMR 좌절 | 391 | 에너지/규제 | 준서의 첫 타이밍 실패. "기다리지 않는다" 교리 시험 |
| **Block 60** | 전고체 배터리 솔리드파워 | 273 | EV/배터리 | 대기업 입찰 경쟁, 창업자 설득 |
| **Block 67** | 방산/우주 완성 + 구조조정 | 276 | 방산/구조조정 | 노조 대면, 부실 계열사 교체 |

## 2. Non-Negotiable Rules

- UTF-8 only
- one work, one owner, 9 blocks
- **수정 대상: Block 44, 45, 47, 53, 55, 56, 57, 60, 67만**
- 그 외 블록 일체 수정 금지 — 특히:
  - Block 32-43 (이전 확장 완료) 절대 수정 금지
  - Block 54, 58, 59, 61, 63, 64, 66 (HIGH 확장 완료) 절대 수정 금지
  - Block 46, 50, 52, 62, 65 (기존 full narrative) 수정 금지
  - Block 48, 49, 51, 68, 69 (LOW — 의도적 스킵) 수정 금지
- block_id 번호 변경 금지, 새 블록 추가 금지 (70 유지)
- BI / status / gate 수정 금지
- 코드 수정 금지
- 기존 4-key JSON 구조(context / event_villain / solution / reward) 유지

## 3. Canonical Target

- work_id: `empire_youngest_allsector`
- TR (write target): `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI (reference only): `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 4. Quality Standard

이전 두 차례 확장과 동일 기준:

| Metric | Target |
|--------|--------|
| content chars | **1,200-2,000** (MEDIUM은 HIGH보다 약간 짧아도 됨 — 주역이 아닌 섹터 블록) |
| tactile detail | **≥ 1** (장소, 시간, 감각) |
| domain-specific language | **≥ 2** (섹터 고유 용어, 기술 디테일, 업계 관행) |
| direct dialogue | **≥ 1** |
| character action (not summary) | **필수** |
| JSON structure | 4-key 유지 |

**MEDIUM 특수 기준**: 이 블록들의 핵심 가치는 protagonist engine이 아니라 **sector texture**. 각 블록이 해당 섹터에서만 나올 수 있는 장면/용어/긴장을 담아야 한다. "투자하고 성공했다"가 아니라 "이 섹터에서는 이런 일이 벌어진다"를 보여줘야 한다.

## 5. Per-Block Revision Guide

### Block 44 — PE 1호 펀드 5조 / GP 1조+LP 4조 (230자)

- Current: "PE 1호 펀드 5조. GP 1조+LP 4조. 정하윤 펀드레이징."
- Sector language: GP commitment, LP 앵커, blind pool, 빈티지, DPI, TVPI
- Restore:
  - 국민연금 또는 대형 연기금 앵커 LP 미팅. 기관 투자심의위원회의 보수적 질문.
  - 정하윤이 기관 LP를 직접 설득하는 첫 대면 — "산업 투자자가 GP가 되면 이해충돌 아닌가요?" 류의 질문에 답변.
  - J캐피탈이 산업 투자자에서 기관 GP로 진화하는 전환점.
- Supporting cast: **정하윤** 주도 장면.

### Block 45 — PE 첫 딜: 새한저축은행+J-핀테크 (173자)

- Current: "PE 첫 딜: 새한저축은행+J-핀테크. 금융 인가 3개월."
- Sector language: 금융 인가, 건전성 비율, BIS 비율, 여신전문, 금감원 사전심사
- Restore:
  - 오승아의 금융 인가 주도 — 금감원에 제출하는 서류, 심사 과정.
  - Block 46(타자 POV — 금감원 박정호/김수연이 놀라는 장면)의 직접 setup. Block 45에서 오승아가 어떤 서류를 준비했기에 Block 46에서 금감원이 "선례가 없다"고 하는지.
  - 새한저축은행 인수가 왜 전략적인지 — 결제 인프라 또는 고객 기반.
- Supporting cast: **오승아** 주도 장면.

### Block 47 — K-럭셔리 2개사 / 파리 패션위크 (147자)

- Current: "K-럭셔리 2개사 3,000억. 파리 패션위크. 스타빌드 아티스트 런웨이."
- Sector language: 메종, 오뜨 꾸뛰르, 프레타포르테, LVMH/케링, 바이어, 쇼노트
- Restore:
  - 파리 패션위크 현장. 유럽 패션 바이어/비평가의 냉소("한국 브랜드?") → 스타빌드 아티스트가 런웨이에 서는 순간 역전.
  - K-pop 팬덤이 패션 시장에서 발생시키는 경제적 파워 — SNS 실시간 반응.
  - 3,000억 인수의 구체적 대상 — 어떤 브랜드인지, 왜 인수 대상이 됐는지.
- Visual spectacle potential이 가장 높은 블록. 화려한 장면 1개 허용.

### Block 53 — 코리아뉴클리어 인수 3,000억 (105자 — **content 최소**)

- Current: "오승아 2년 준비. 코리아뉴클리어 인수 3,000억."
- Sector language: SMR, 소형모듈원자로, NRC/원안위 인허가, 핵연료 농축, 노형 설계, 냉각 방식, MW급
- Restore:
  - 오승아의 2년 준비가 구체적으로 뭐였는지 — 원안위 사전 협의? 기술 실사? 해외 규제 벤치마크?
  - 코리아뉴클리어가 어떤 회사인지 — 설계만 하는 곳? 시제품이 있는 곳? 왜 3,000억인지?
  - SMR의 heavy-tech 느낌 — 원자로 설계실, 엔지니어와의 대화, 기술의 무게.
  - Block 57(반핵 시위/인허가 유예)의 사전 조건. 여기서 SMR에 진입했기에 Block 57에서 좌절이 의미를 가짐.
- **105자 → 최소 1,200자**: 가장 큰 확장이 필요한 블록.
- Supporting cast: **오승아** 기술 실사 주도.

### Block 55 — 드론 스타트업 스카이포스 1,500억 (344자)

- Current: "드론 스타트업 스카이포스 1,500억. 권도준 납품 1호. AI NPU 탑재."
- Sector language: 방위사업청, 군용 드론, ISR(정보감시정찰), NPU, 자율비행, 보안인가, 방산 적합업체
- Restore:
  - 권도준이 방위사업청 납품을 성사시키는 과정 — 방산 적합업체 심사, 보안인가 절차.
  - AI 드론 시연 장면 — 시험 비행장, 자율비행 데모, 군 관계자의 반응.
  - Block 35(권도준 영입)의 payoff. "민간이 방산을 건드리면 사람이 죽는다"고 했던 권도준이 직접 납품을 이끄는 전환.
- Supporting cast: **권도준** 주도 장면.

### Block 56 — 서해안 해상풍력 500MW (256자)

- Current: "서해안 해상풍력 500MW. 베스타스 JV. 통합 에너지 제안."
- Sector language: 해상풍력, 모노파일, 자켓 기초, GW급, PPA(전력구매계약), REC, 풍황 데이터
- Restore:
  - 입찰 경쟁 — 한전/SK/GS 등과의 입찰에서 "통합 에너지"가 차별점.
  - 베스타스 JV 협상 — 덴마크 기업과의 기술 제휴가 왜 필요한지.
  - 현장 texture — 서해안 해상, 터빈 기초 공사, 또는 풍황 측정 현장.

### Block 57 — 반핵 시위 / SMR 인허가 18개월 유예 (391자)

- Current: "반핵 시위. 인허가 18개월 유예. 방산/EV로 선회."
- **이 블록은 준서의 첫 명확한 타이밍 실패.** "기다리지 않는다"는 교리의 시험.
- Restore:
  - 반핵 시위 현장 또는 뉴스. 국회 청문회. 사회적 압력의 구체적 모습.
  - 인허가 18개월 유예 통보 — 원안위에서 연락이 오는 장면. 또는 오승아가 보고하는 장면.
  - **준서의 판단 장면**: "기다리지 않는다." 18개월을 기다리는 대신 방산/EV로 선회. 이 교리가 여기서 직접 시험됨.
  - "세 개씩. 쉬지 않고."가 타이밍 실패에도 멈추지 않는다는 것의 의미.
- Anchor: `세 개씩` 교리 + protagonist engine(좌절에 대한 low-affect 반응).

### Block 60 — 전고체 배터리 솔리드파워코리아 5,000억 (273자)

- Current: "전고체 배터리 솔리드파워코리아 5,000억. LG/삼성SDI 경쟁."
- Sector language: 전고체(solid-state), 황화물계/산화물계, 에너지밀도, Wh/kg, 양산 로드맵, 파일럿 라인
- Restore:
  - 대기업(LG/삼성SDI) 입찰 경쟁 — "재벌이 5조 부르면 우리는 뭘로 이기나" 류의 긴장.
  - 독립 라이선싱 모델 — "우리는 사지 않는다. 라이선스한다." 차별화 전략.
  - 창업자 설득 장면 — 창업자가 왜 대기업 대신 J를 택하는지. 기술 자율성? 지분 유지?
  - 배터리 기술의 tactile detail — 파일럿 라인 방문, 셀 시연.

### Block 67 — 방산/우주 완성 + 구조조정 착수 (276자)

- Current: "방산/우주 완성. 구조조정 착수. 노조 반발. 재배치 프로그램."
- Sector language: 구조조정, 인력 재배치, 희망퇴직, 노사협의, 사업부 분할, 매각/청산
- Restore:
  - **제국 구조조정의 첫 실행** — Block 66(경영권 확보) 직후. "정리하겠습니다"를 실행하는 장면.
  - 노조 대표와의 대면 — 물리적 회의실, 노조 대표의 요구, 준서의 대응.
  - 부실 계열사 경영진 교체 — 아버지의 사람을 내보내는 것의 무게.
  - low-affect protagonist: 구조조정의 고통을 알면서도 실행하는 냉정함. 그러나 "재배치 프로그램"에는 사람을 버리지 않겠다는 최소 선.
- Block 66 callback: "정리하겠습니다" → Block 67에서 실제 정리.

## 6. Domain Texture 다양화 가이드

9블록이 모두 "미팅→협상→성사" 패턴으로 수렴하면 안 됨. 섹터별 장면 진입점을 다양화:

| block_id | 권장 scene entry |
|----------|-----------------|
| 44 | 투자심의위원회 회의실 (LP 질문 응대) |
| 45 | 금감원 서류 제출 (오승아 단독 행동) |
| 47 | 파리 패션위크 런웨이 (visual spectacle) |
| 53 | 원자로 설계실 또는 기술 실사 현장 (heavy-tech) |
| 55 | 시험 비행장 드론 시연 (야외/기술 시연) |
| 56 | 서해안 현장 또는 입찰 발표장 (자연/에너지) |
| 57 | TV 뉴스 시청 또는 원안위 통보 전화 (좌절의 수신) |
| 60 | 파일럿 라인 방문 또는 창업자 연구실 (기술 설득) |
| 67 | 노사 협의 회의실 (인간 대면의 무게) |

## 7. Mandatory Reads

Read in this order:

1. `docs/2026-03-27/empire-youngest-weakness-report.md` — Section 2 MEDIUM 테이블 + Section 5 sector texture list
2. `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md` — 톤/밀도 참조
3. `docs/2026-03-27/empire-youngest-tr-revision-44-69-high-changelog.md` — HIGH 확장 결과 참조 (특히 callback 구조)
4. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — 대상 9블록 현재 상태 + Block 1-5 & 확장 완료 블록 밀도 참조
5. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — plot_roadmap 해당 블록 (reference only)

## 8. Fixed Creative Constraints

- 2045 → 2025 regression: 직접 언급 불필요하나 "20년 데이터"의 산업 예지가 블록마다 자연스럽게 드러나야 함
- `세 개씩. 쉬지 않고.`: **Block 57에서 직접 시험** — 좌절에도 멈추지 않는 교리
- independent-capital: 전액 자력 + PE LP 자금. 제국 자금 미사용.
- all-sector rolling: **이번 런의 핵심**. 9개 섹터 각각의 고유 언어가 살아야 함.
- low-affect protagonist: Block 57(좌절), Block 67(구조조정)에서 감정 억제 유지.
- family-collapse: 이번 런에서는 직접 활성화 불필요 (HIGH에서 이미 처리됨).

## 9. Supporting Cast 등장 가이드

MEDIUM 블록에서 주요 supporting cast의 역할:

| Character | Blocks | Role |
|-----------|--------|------|
| 정하윤 | 44 | PE 펀드레이징 주도 — 기관 LP 대면의 첫 장면 |
| 오승아 | 45, 53 | 금융 인가 + SMR 기술 실사 — 법무+규제 역량 |
| 권도준 | 55 | 방산 납품 주도 — Block 35 영입의 payoff |
| 김태석 | (간접) | Block 55 AI NPU 기술 관련 간접 언급 가능 |

## 10. Deliverables

수정된 TR:
- `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`

Block 44, 45, 47, 53, 55, 56, 57, 60, 67만 수정. 나머지 전체 원본 유지.

추가 산출물:
- `docs/2026-03-27/empire-youngest-tr-revision-44-69-medium-changelog.md`

Changelog 형식:
```
# TR Revision Changelog — Block 44-69 MEDIUM Priority

## Per-Block Changes
| block_id | before chars | after chars | sector | key additions |
|----------|-------------|------------|--------|---------------|
| Block 44 | 230 | ... | 금융/PE | ... |
| ... | ... | ... | ... | ... |

## Domain Texture Check
| block_id | sector-specific terms used | scene entry type |
|----------|--------------------------|-----------------|
| ... | ... | ... |

## Supporting Cast Check
- 정하윤: Block 44 — ...
- 오승아: Block 45, 53 — ...
- 권도준: Block 55 — ...

## Anchor Survival Check
- [ ] all-sector rolling: 9개 섹터 각각 고유 언어 ≥2
- [ ] "세 개씩" 교리: Block 57 좌절에서 시험
- [ ] low-affect: Block 57(좌절), Block 67(구조조정) 억제 유지
- [ ] independent-capital: PE LP 구조 + 자력 유지

## Quantitative Summary
| metric | before | after |
|--------|--------|-------|
| total content chars (9 blocks) | ... | ... |
| average chars per block | ... | ... |
| expansion ratio | — | ... |
```

## 11. Stop Conditions

Stop immediately if:
- TR file cannot be parsed as valid JSON
- block boundary corruption
- Block 32-43 또는 HIGH 7블록 결과가 훼손됨
- 수정이 MEDIUM 이외 블록으로 확산
- domain texture 없이 "투자하고 성공했다" 요약 반복
- confidence 90% 미만

## 12. Expected Next Unit After This Order

- if MEDIUM 9블록 revision clean: **revival-stage probe** (LOW 5블록은 의도적 스킵)
- if structural issues found: `TR architecture reassessment`

## 13. Handoff Format

```text
work_id: empire_youngest_allsector
current_stage: targeted_revision
finished_unit: TR revision Block 44-69 MEDIUM priority
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment
- target: one work_id, 9 specific blocks only
- block count stays 70
- 이전 확장 결과(32-43, HIGH 7블록) 보호
- LOW 5블록 의도적 스킵

### Pass 2. Operational Usefulness
- per-block revision guide with sector-specific language lists
- scene entry 다양화 가이드
- supporting cast 등장 매핑
- domain texture check 템플릿

### Pass 3. Integrity
- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- bounded to 9 blocks only

Confidence:
- 96% that `targeted TR revision Block 44-69 MEDIUM` is the correct next unit
- LOW 5블록 스킵 후 revival-stage probe 진행이 정직한 경로
