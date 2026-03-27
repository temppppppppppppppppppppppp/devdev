# OPUS Empire Youngest — Targeted TR Revision Order (Block 32-43)

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `empire_youngest_allsector`
Predecessor chain:
1. `docs/2026-03-27/empire-youngest-truth-reaudit-report.md` (re-audit, verdict MIXED)
2. `docs/2026-03-27/empire-youngest-weakness-report.md` (5-axis gap catalog)

## 1. Order Intent

This order fixes the target to `empire_youngest_allsector` Block 32-43 and asks OPUS to complete exactly one bounded unit:

- `targeted TR revision — Block 32-43 compression zone`

The preceding weakness report cataloged:
- 12 blocks, all scene-deficit
- each block 400-700 chars (Block 1-5 standard: 2,000+ chars)
- common defects: (1) conflict → 1-line summary (2) resolution → meta-summary (3) character micro-moments absent (4) tactile detail absent
- Block 36: 타자 POV merge required
- 이준혁 arc gap (Block 20→52 = 32-block silence): 1-beat insertion needed in Block 35-40

This is a content expansion order.
This is not a structural redesign.
This is not a new block creation order (block count stays 70).

## 2. Non-Negotiable Rules

- UTF-8 only
- read weakness report per-block catalog before writing anything
- one work, one owner, one zone
- no same-work concurrent editing
- no code or system edits
- do not touch blocks outside 32-43
- do not change block_id numbering
- do not add new blocks (block count stays 70)
- do not alter BI in this run
- do not alter sequential_run_status or phase0 gate files
- do not promote to active path in this run
- preserve the existing 4-key JSON structure (context / event_villain / solution / reward) per block
- expand content within that structure — do not invent new JSON keys

## 3. Canonical Target

- work_id: `empire_youngest_allsector`
- TR: `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI (reference only): `bible/_quarantine/0_bi_empire_youngest_allsector.json`

Write changes to the TR file only.

## 4. Quality Standard

Each revised block must match the density of Block 1-5 (the early engine):

| Metric | Block 1-5 standard | Block 32-43 current | Target |
|--------|-------------------|--------------------|---------|
| content chars | 2,000-3,000 | 400-700 | **1,500-2,500** |
| tactile detail | 장소+시간+감각 | absent | **최소 1개** |
| character micro-moment | 4초간 눈 감기, 캔커피 등 | absent | **최소 1개** |
| conflict scene | 대면+심리전 | 1줄 요약 | **최소 1개 대면 대사** |
| resolution | 과정 서술 | "~로 처리한다" 메타요약 | **과정의 구체적 1-2 beat** |

Do not inflate beyond 2,500 chars. The goal is restoration, not bloat.

## 5. Per-Block Revision Guide

This is the weakness report's per-block gap catalog. Use it as the primary input.

### Block 32 — B2B SaaS / J-클라우드

- Current: 556 chars. 병원 데이터 유출 공포 2줄. 오승아 계약 장면 축약.
- Restore: 병원장 거부 → 오승아 화이트보드 격리 아키텍처 시연 → 설득 성공의 대면 장면.
- Anchor: 오승아의 법무 역량이 기술 영역으로 확장되는 모먼트.

### Block 33 — 야마모토 / 사무라이엔터 IP 800개

- Current: 528 chars. 도쿄 미팅 장면 부재. 이사회 설득 1줄.
- Restore: 도쿄 야간 미팅. 야마모토와의 실질적 전략 대화. 이사회 설득의 tactile beat.
- Anchor: 야마모토 동맹이 Block 40/62/65에 이어지므로 관계 foundation.

### Block 34 — 게임 개발팀 퇴사 / 영혼의 검 취소

- Current: 663 chars. 퇴사 현장 감정 부재. "Block 18 프레임 적용"이라는 메타 요약.
- Restore: PD 사직서 대면. "당신은 게임을 이해 못 한다" 대사. 준서 4초간 눈 감기(low-affect callback). "사람은 가도 IP는 남는다" 판단.
- Anchor: 인재 이탈 대 IP 우선의 냉정한 선택 = protagonist engine.
- Priority Matrix: #8.

### Block 35 — 권도준 영입 / 방산 포석

- Current: 558 chars. 권도준 거부 장면 축약.
- Restore: 을지로 술집. 권도준 "민간이 방산을 건드리면 사람이 죽는다." 준서가 NPU 스펙시트를 펼치는 장면.
- **이준혁 1-beat 삽입**: 이 블록 또는 Block 38-40 중 하나에 이준혁 arc gap closer 삽입. 권장: 준서가 제국그룹 뉴스를 보거나, 이준혁 부재중 전화를 무시하는 1-beat. Block 54 전화의 setup.

### Block 36 — K사 전략기획본부장 (현재 타자 POV)

- Current: 576 chars. 타자 POV — K사가 준서의 IP 장악을 논의.
- **구조 변경**: 타자 POV → 준서 POV로 merge. K사의 대응이 준서의 정보망으로 들어오는 형태. 준서가 K사 움직임을 인지하고 무시하는 장면.
- Weakness report 처방: "merge into protagonist POV — K사 대응이 준서의 정보망으로 들어오는 형태로 전환. 준서가 K사 움직임을 인지하고 무시하는 장면으로 바꾸면 agency 회복."
- Anchor: protagonist agency 유지.

### Block 37 — AI 완성 / J-클라우드 ARR 2,000억

- Current: 665 chars. 개인정보보호위 대응 1줄. 20조 도달 감정 부재.
- Restore: 오승아 200페이지 보고서 → 위원 당혹 장면. "다음." 미시 모먼트.
- Anchor: "세 개씩" 교리 + 오승아 법무 역량.

### Block 38 — K-pop 기획사 인수 / J캐피탈파트너스

- Current: 589 chars. 팬덤 반대운동 실체 없음. 이적 시도 차단 1줄.
- Restore: 팬덤 해시태그 전쟁 → 아티스트 본인의 "저는 남겠습니다" 라이브 선언.
- Anchor: all-sector rolling — 엔터 섹터의 고유 언어(팬덤, IP, 아티스트 자율성).

### Block 39 — OTT J-Stream 설립

- Current: 488 chars. 가장 압축된 블록 중 하나. 경쟁구도 1줄.
- Restore: J-Stream 론칭 나이트. 서버 이슈 또는 실시간 구독자 카운터. 김태석 CTO 긴급 대응.
- Anchor: 기술 장면에 김태석이 등장하면 supporting cast arc 강화.

### Block 40 — J-YAMA 아시아 펀드 2조

- Current: 476 chars. Content 최소 블록. LP 설득 1줄. 야마모토 발언 요약.
- Restore: 도쿄 야마모토 사무실. 일본 기관투자자 3명. "한국 GP에게 1조를?" 야마모토 직접 보증 장면.
- Anchor: 야마모토 동맹 심화 → Block 62/64/65의 setup.

### Block 41 — 이준민 공매도 연합

- Current: 577 chars. 쇼트 스퀴즈 사이다가 산술로 처리됨.
- Restore: 준서→정하윤 실적 발표 3일 앞당기기 지시. 공매도 세력 포지션 역전 실시간. 이준민 손실 청산 후 빈 사무실.
- Anchor: 가족 내 적대의 정점. Block 65 역스퀴즈의 prototype.
- Priority Matrix: #5.

### Block 42 — 공정위 M&A 3개월 동결

- Current: 548 chars. 3개월 규제 위기가 가장 약하게 처리됨.
- Restore: 공정위 심판정. 오승아 시장점유율 데이터 제시. 심판관 "어느 시장에서 독점이라는 겁니까" 대사. 법리 긴장.
- Anchor: 오승아 법무 역량 직접 장면 (Block 46 타자 POV의 사전 setup).
- Priority Matrix: #6.

### Block 43 — 이커머스+게임 완성 / 자산 35조

- Current: 564 chars. 정하윤 "다음은 뭡니까?" 감정 무게 대비 맥락 부족.
- Restore: J캐피탈 사무실 야경. 정하윤 스프레드시트 닫기. "다음은 뭡니까?" → "전부." → 정하윤의 모호한 표정(경외/체념).
- Anchor: "세 개씩" 교리의 완성 ritual. 정하윤 CFO→CIO 진화의 씨앗.

## 6. 이준혁 Arc Gap Closer

Block 20→52 = 32-block 공백. Weakness report 권장: Block 35-40 중 1곳에 1-beat 삽입.

권장 위치: **Block 35** (권도준 영입 장면 내부) 또는 **Block 38** (엔터 진입 시점).

1-beat 형태 (중 택 1):
- 준서가 제국그룹 뉴스(반도체 적자)를 타블렛에서 보고 넘기는 장면
- 이준혁 부재중 전화를 보고 무시하는 장면
- 뉴스 앵커가 "제국그룹 이준혁 부회장" 언급하는 배경음

삽입하되 블록의 주 서사를 방해하지 말 것. 1-2문장 수준.

## 7. Mandatory Reads

Read in this order:

1. `docs/2026-03-27/empire-youngest-weakness-report.md` — Section 1 (Block 32-43 per-block catalog)
2. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — Block 32-43 현재 상태 (full read of these blocks)
3. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — plot_roadmap Block 32-43 entries (reference only)
4. Block 1-5 of TR — density/tone reference standard

Block 1-5는 수정하지 말 것. 톤과 밀도의 기준점으로만 참조.

## 8. Fixed Creative Constraints

Do not wash out these anchors:

- 2045 → 2025 regression frame (Block 32-43은 2030-2031년대)
- credit-card `3,000만 원` BTC seed → 이 시점에서 이미 수조 규모이므로 직접 언급 불필요, 그러나 "자력으로 쌓은" 톤 유지
- `세 개씩. 쉬지 않고.` execution doctrine — Block 37, 43에서 "다음." ritual 유지
- all-sector rolling structure — 각 섹터 진입에 domain-specific 언어 필수
- independent-capital rule: no family money — 이 시점에서도 제국그룹 자금 미사용 명시
- family-collapse memory — Block 35 또는 38에서 이준혁 1-beat으로 간접 활성화
- low-affect protagonist — "4초간 눈 감기", 캔커피 등 micro-moment 유지. Block 34(퇴사 대면), Block 41(공매도 역공) 등 감정 자극 장면에서도 억제 톤 유지.

Known weakness to avoid creating:

- 각 블록이 같은 패턴(문제→해결→수치)으로 읽히지 않도록 scene entry point를 블록마다 다르게 할 것
- 오승아/정하윤/야마모토의 역할이 "~가 처리했다"로 요약되지 않도록 최소 1개 직접 대사 또는 행동 포함
- "다음." ritual이 Block 37, 43 두 곳에서 나오므로 tone을 달리 할 것 (37: 냉정한 체크, 43: 무게 있는 선언)

## 9. Deliverable

수정된 TR 파일:

- `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`

Block 32-43만 수정. 나머지 블록은 원본 그대로 유지.

추가 산출물:

- `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md`

Changelog 형식:
```
# TR Revision Changelog — Block 32-43

## Per-Block Changes
| block_id | before chars | after chars | key additions |
|----------|-------------|------------|---------------|
| Block 32 | 556 | ... | 병원장 대면 장면, 오승아 화이트보드 |
| ... | ... | ... | ... |

## 이준혁 1-beat
- inserted at: Block ...
- content: ...

## Block 36 POV Merge
- before: K사 전략기획본부장 타자 POV
- after: 준서 POV + K사 정보 수신

## Anchor Survival Check
- [x] low-affect micro-moments
- [x] "다음." ritual (Block 37, 43)
- [x] independent-capital tone
- [x] domain-specific language per sector
- [x] 이준혁 arc gap closer
```

## 10. Stop Conditions

Stop immediately and report if:

- TR file cannot be parsed as valid JSON after modification
- block boundary corruption detected
- expanding a block beyond 2,500 chars and still scene-deficit
- a creative anchor would be washed out by the revision
- revision drifts into Block 44+ territory
- confidence in quality match to Block 1-5 standard drops below 90%

## 11. Expected Next Unit After This Order

- if Block 32-43 revision is clean: `targeted TR revision — Block 44-69 HIGH priority` (7 blocks)
- if structural issues found during revision: `TR architecture reassessment`

## 12. Handoff Format

End with:

```text
work_id: empire_youngest_allsector
current_stage: targeted_revision
finished_unit: TR revision Block 32-43
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 13. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target: one work_id, one zone (Block 32-43)
- block count stays 70
- no BI/status/gate modification
- Block 36 POV merge authorized
- 이준혁 1-beat insertion authorized within Block 35-40

### Pass 2. Operational Usefulness

- per-block revision guide with specific gap descriptions and target scenes
- quality standard table with measurable metrics
- changelog format for verification
- stop conditions prevent bloat and scope creep

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- bounded to 12 blocks only

Confidence:
- 96% that `targeted TR revision Block 32-43` is the correct next OPUS unit
