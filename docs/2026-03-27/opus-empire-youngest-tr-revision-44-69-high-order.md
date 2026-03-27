# OPUS Empire Youngest — Targeted TR Revision Order (Block 44-69 HIGH)

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `empire_youngest_allsector`
Predecessor chain:
1. `docs/2026-03-27/empire-youngest-truth-reaudit-report.md` (re-audit)
2. `docs/2026-03-27/empire-youngest-weakness-report.md` (5-axis gap catalog)
3. `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md` (Block 32-43 확장 완료)

## 1. Order Intent

This order fixes the target to `empire_youngest_allsector` Block 44-69 중 **HIGH priority 7블록**만 확장한다.

- `targeted TR revision — Block 44-69 HIGH priority`

대상 블록 (Revision Priority Matrix 순):

| rank | block_id | title | current chars | priority reason |
|------|----------|-------|--------------|-----------------|
| 1 | **Block 66** | 경영권 확보 51.3%. 이사회 첫 발언 | 416 | 12년 여정 payoff. Block 1 옥상→Block 66 이사회장 대칭. |
| 2 | **Block 54** | 금융+패션 완성. 이준혁 전화 | 200 | 짓는→구하는 전환점. 이준혁/최다은/정하윤 3 arc 교차. |
| 3 | **Block 59** | J제국홀딩스 설립 선언 | 383 | 서사 정점 선언. Block 1 "나 혼자 짓는다"의 공개 버전. |
| 4 | **Block 61** | 이준민 구속 | 280 | 형제 arc 해소. 마지막 적대자 퇴장. |
| 5 | **Block 63** | 에너지 완성. 채권단 협상 | 357 | 제국 최종전 opening shot. |
| 6 | **Block 64** | 레이첼+야마모토 10조 집행 | 339 | Block 62 정하윤 47분 확보의 실행 편. |
| 7 | **Block 58** | 이준혁 J캐피탈 방문 | 562 | 이미 중간 서사 보유. 물리적 묘사+회귀 callback 보강. |

이것은 content expansion order이다.
- 나머지 MEDIUM 9블록, LOW 5블록은 이번 런에서 수정하지 않는다.
- 이미 full narrative인 블록(46, 50, 52, 62, 65)은 수정하지 않는다.

## 2. Non-Negotiable Rules

- UTF-8 only
- one work, one owner, 7 blocks
- no same-work concurrent editing
- no code or system edits
- **수정 대상: Block 54, 58, 59, 61, 63, 64, 66만**
- 그 외 블록 일체 수정 금지
- block_id 번호 변경 금지
- 새 블록 추가 금지 (block count 70 유지)
- BI 수정 금지
- sequential_run_status / phase0 gate 수정 금지
- 기존 4-key JSON 구조(context / event_villain / solution / reward) 유지
- Block 32-43의 이번 세션 확장 결과를 훼손하지 말 것

## 3. Canonical Target

- work_id: `empire_youngest_allsector`
- TR (write target): `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`
- BI (reference only): `bible/_quarantine/0_bi_empire_youngest_allsector.json`

## 4. Quality Standard

Block 32-43 확장 후 달성된 기준과 동일:

| Metric | Target |
|--------|--------|
| content chars | **1,500-2,500** |
| tactile detail (장소+시간+감각) | **≥ 1** |
| character micro-moment | **≥ 1** |
| direct dialogue | **≥ 1** |
| conflict shown (not summarized) | **필수** |
| resolution with process beats | **필수** |

Block 58은 이미 562자이므로 확장 부담이 적지만, 품질 기준은 동일.

## 5. Per-Block Revision Guide

### Block 54 — 금융+패션 완성 / 이준혁 전화 (200자 → 확장)

**Priority Matrix #2. 감정 arc 교차점.**

- Current: "ARC-05 마감. 금융PE 15조. 패션 글로벌. 식품 아시아15국. SMR 착수. 총60조. 이준혁 전화: '아버지 편찮으셔.'"
- Restore:
  - ARC-05 마감 장면은 간결하게 (이미 Block 43에서 전환 선언)
  - **이준혁 전화 통화 전체 장면**: 전화가 울리는 순간, 이준혁 목소리, "아버지 편찮으셔" 대사, 준서의 반응 (감정 억제 — 그러나 Block 35의 알림 무시와 대비되는 변화)
  - **준서가 수화기를 내려놓은 뒤**: 미시 모먼트. 4초간 눈 감기? 캔커피? 또는 새로운 행동.
  - **최다은 감지**: 이 블록 또는 인접 블록에서 최다은이 준서의 표정/행동 변화를 알아채는 1-beat
  - **"다음."의 tone 변화**: Block 43의 "전부"에서 넘어온 뒤, 여기서의 "다음"은 처음으로 짓는 것이 아닌 구하는 것을 향함
- **정하윤 1-beat 삽입 권장**: 60조 도달에 대한 정하윤의 반응 (Block 50→61 = 11블록 공백 해소의 시작점). "11년입니다"(Block 62)의 전단계로서 무게.
- Anchor: 가족붕괴 기억 직접 활성화. Block 35 이준혁 1-beat의 payoff.

### Block 58 — 이준혁 J캐피탈 방문 (562자 → 보강)

**이미 중간 서사 보유. 물리적 묘사 + 회귀 callback 보강.**

- Current: 이준혁이 직접 찾아옴. "아버지 치매 초기 진단." 기본 대면 장면 존재.
- Restore:
  - **물리적 묘사**: 사무실 어디에 앉았나. 이준혁의 양복이 예전 같지 않은 디테일. 시선. 침묵의 길이.
  - **Inner monologue**: 5분간 형을 보는 동안 준서의 내면. 전생 기억 callback — "전생에서 형은 구속됐다. 이번 생에서는..."
  - **Block 1 회귀 callback**: 옥상에서 떨어지기 전 마지막으로 본 것이 제국그룹 빌딩이었다면, 지금 형이 앉아있는 이 사무실은 준서가 만든 빌딩이다.
  - **"2년 뒤에 내가 가겠다"**: 이 약속의 무게. 준서가 제국그룹을 먹겠다는 의미인지, 형을 구하겠다는 의미인지 의도적 모호함.
- Anchor: 가족붕괴 3축(반도체 지연 / 형제 갈등 / PF 위기) 중 형제축 직접 대면.

### Block 59 — J제국홀딩스 설립 선언 (383자 → 확장)

**Priority Matrix #3. 서사 정점 선언.**

- Current: "J제국홀딩스 설립 선언. 법인 등기만. '먹는다. 내 방식으로.'"
- Restore:
  - **물리적 상황**: 어디서 선언하는가? 혼자 사무실에서? 정하윤 앞에서? 법무법인에서 등기 서류 서명하며?
  - **Block 1 callback**: "제국그룹은 나 혼자 짓는다"(Block 1 내면) → "먹는다. 내 방식으로."(Block 59 공개). 동일한 의지의 외부화.
  - **"제국"이라는 이름**: 아버지의 제국그룹에서 이름을 가져온 것. 이것이 경의인지 도전인지 — 준서 본인도 답을 모르는 모호함.
  - **법인 등기 디테일**: 등기소에서 서류에 도장 찍는 물리적 행위. 200조 기업의 시작이 A4 한 장.
- Anchor: independent-capital → "내 방식으로"의 정의.

### Block 61 — 이준민 구속 (280자 → 확장)

**Priority Matrix #4. 형제 arc 마지막 적대자 퇴장.**

- Current: "이준민 분식회계로 구속. 제국 계열사 3곳 경영 공백. 주가 -20%."
- Restore:
  - **Block 41 연결**: 공매도 실패 후 이준민이 분식회계로 빠진 경로. "어떻게" 보다 "왜" — 패배한 자의 자기파괴.
  - **준서가 뉴스를 보는 장면**: 어디서? 무슨 표정? 감정 억제 — 그러나 이것은 형이 아닌 다른 형제의 구속이므로 복잡한 감정 (동정? 안도? 무감?)
  - **제국 계열사 3곳 경영 공백**: 이것이 Block 63 채권단 협상의 사전 조건이 됨. 공백이 곧 기회라는 준서의 판단.
  - **이준혁과의 대비**: Block 58에서 형은 도움을 청했고, 여기서 다른 형은 구속됨. 3형제의 운명이 갈라지는 순간.
- Anchor: 가족붕괴 3축. low-affect protagonist — 형제 구속에도 억제.

### Block 63 — 에너지 완성 / 채권단 협상 (357자 → 확장)

**Priority Matrix #7 (within HIGH). 제국 최종전 opening shot.**

- Current: "SMR 인허가 통과. 에너지 완성. 90조. 채권단 직접 협상 제안."
- Restore:
  - **채권단 회의실**: 물리적 묘사. 은행장들이 앉아있는 긴 테이블. 준서가 직접 프레젠테이션.
  - **"직접 협상"의 의미**: 중개자 없이 채권단 앞에 선다. 이것이 Block 1에서 맨몸으로 시작한 캐릭터의 일관성.
  - **90조 도달**: SMR 인허가가 에너지 포트폴리오 완성의 마지막 조각. 이것을 산술이 아닌 성취감으로.
  - **제국그룹 인수 로드맵 제시**: 채권단에게 "제가 살 수 있습니다"라는 첫 공식 제안.
- Anchor: independent-capital + "세 개씩" 교리 — 에너지까지 완성한 뒤에야 제국을 건드리는 순서.

### Block 64 — 레이첼+야마모토 10조 집행 (339자 → 확장)

**Block 62 정하윤 47분 확보의 실행 편.**

- Current: "레이첼 5조 + 야마모토 5조 = 10조 집행. 해운 JV."
- Restore:
  - **Block 62 callback**: 정하윤이 47분 만에 전화 두 통으로 10조를 확보한 장면의 이후. 실제 자금이 이체되는 순간의 무게.
  - **이자 5,000억 조건**: inner monologue — "5,000억은 1년 이자다. 제국을 사기 위한 비용이다." 이 계산을 받아들이는 준서의 판단.
  - **레이첼과 야마모토**: 두 사람의 신뢰가 돈으로 증명되는 순간. 야마모토는 Block 33, 40에서 쌓인 관계. 레이첼은 글로벌 네트워크.
  - **해운 JV**: 마지막 섹터 진입. "all-sector"의 마지막 조각.
- Anchor: 야마모토 동맹선 Block 33→40→62→64 연속체의 마감.

### Block 66 — 경영권 확보 51.3% / 이사회 첫 출석 (416자 → 확장)

**Priority Matrix #1. 12년 여정의 핵심 payoff.**

- Current: "지분 51.3%. 이사회 첫 출석. '정리하겠습니다.' 이사진 12명 침묵."
- Restore:
  - **이사회장 물리적 묘사**: 제국그룹 본사. 아버지가 앉았을 의장석. 벽에 걸린 그룹 연혁. 준서가 이 공간에 처음 들어서는 순간.
  - **Block 1 대칭**: 옥상에서 떨어지려던 남자가 이사회장에 들어선다. 2045년의 추락과 2037년의 착석.
  - **12명의 이사진**: 아버지의 사람들. 각자의 표정 — 경계, 체념, 호기심. "발언하시겠습니까?"
  - **"정리하겠습니다."**: 이 한 마디의 무게. 어떤 톤으로? low-affect protagonist의 12년이 이 한 문장에.
  - **침묵의 길이**: 12명이 아무도 말하지 않는 시간. 그것이 패배의 인정인지, 새 시대의 인정인지.
  - **최다은 1-beat 삽입 권장**: Block 62→70 = 8블록 공백. 이 블록에 최다은 1-beat. "밥은 먹고 다녀?" 류의 일상 문자. Block 70 "새해 복 많이 받아"의 emotional payoff를 높이는 setup.
- Anchor: 2045→2025 regression의 narrative payoff. 전생의 추락이 이생의 착석으로.

## 6. Emotional Arc Gap Closers

weakness report Axis 4에서 발견된 공백 해소:

| Character | Gap | Insertion Block | Beat |
|-----------|-----|-----------------|------|
| 최다은 | Block 62→70 (8블록) | **Block 66** | 이사회 직후 또는 당일 저녁 — 일상 문자 1-beat. "밥은 먹고 다녀?" "뉴스 봤어" 같은 대단한 말이 아닌 것. |
| 정하윤 | Block 50→61 (11블록) | **Block 54** | 60조 도달 시점 — 정하윤의 반응 1-beat. "11년입니다"(Block 62)의 전단계. |

삽입하되 각 블록의 주 서사를 방해하지 말 것. 1-2문장 수준.

## 7. Mandatory Reads

Read in this order:

1. `docs/2026-03-27/empire-youngest-weakness-report.md` — Section 2 (Block 44-69 inventory) + Section 4 (emotional arc gap) + Section 6 (priority matrix)
2. `docs/2026-03-27/empire-youngest-tr-revision-32-43-changelog.md` — Block 32-43 확장 결과 톤/밀도 참조
3. `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json` — 대상 7블록 현재 상태 + Block 1-5 밀도 참조 + Block 32-43 확장 결과 참조
4. `bible/_quarantine/0_bi_empire_youngest_allsector.json` — plot_roadmap 해당 블록 (reference only)

## 8. Fixed Creative Constraints

Do not wash out:

- 2045 → 2025 regression frame — **Block 66에서 직접 payoff** (옥상→이사회장)
- `세 개씩. 쉬지 않고.` — Block 54에서 전환 ("짓는→구하는")
- independent-capital rule — Block 63 채권단 협상에서 "자력 90조"의 무게
- family-collapse 3축 — Block 54(아버지), 58(이준혁), 61(이준민)에서 3축 모두 활성화
- low-affect protagonist — Block 61(형제 구속에도 억제), Block 66("정리하겠습니다."의 톤)
- all-sector rolling — Block 63(에너지 완성), Block 64(해운 마지막 조각)

Known patterns to avoid:
- 7블록이 모두 "감동적 대면→침묵→한 마디" 패턴으로 수렴하지 않도록 scene entry를 다양화
- Block 54, 58, 61이 연속 가족 블록이므로 각각의 감정 톤을 분명히 구분: 54(충격), 58(대면의 무게), 61(냉정한 관찰)
- 자본 수치는 유지하되 장면 속 대사/행동으로만 등장

## 9. Deliverables

수정된 TR 파일:
- `treatments/_quarantine/empire_youngest_allsector_tr_block_070_draft.json`

Block 54, 58, 59, 61, 63, 64, 66만 수정. 나머지 전체 원본 유지.

추가 산출물:
- `docs/2026-03-27/empire-youngest-tr-revision-44-69-high-changelog.md`

Changelog 형식:
```
# TR Revision Changelog — Block 44-69 HIGH Priority

## Per-Block Changes
| block_id | before chars | after chars | key additions |
|----------|-------------|------------|---------------|
| Block 54 | 200 | ... | 이준혁 통화, 최다은 감지, 정하윤 1-beat |
| Block 58 | 562 | ... | 물리적 묘사, 회귀 callback, inner monologue |
| ... | ... | ... | ... |

## Emotional Arc Gap Closers
- 최다은: inserted at Block ...
- 정하윤: inserted at Block ...

## Anchor Survival Check
- [ ] Block 66 ← Block 1 대칭 (옥상→이사회장)
- [ ] Block 54 "다음." 전환 (짓는→구하는)
- [ ] 가족 3축: 54(아버지) / 58(이준혁) / 61(이준민)
- [ ] low-affect tone: 61(구속 뉴스) / 66("정리하겠습니다.")
- [ ] domain-specific: 63(에너지/SMR) / 64(해운/JV)

## Quantitative Summary
| metric | before | after |
|--------|--------|-------|
| total content chars (7 blocks) | ... | ... |
| average chars per block | ... | ... |
| expansion ratio | — | ... |
```

## 10. Stop Conditions

Stop immediately if:
- TR file cannot be parsed as valid JSON after modification
- block boundary corruption detected
- revision drifts into MEDIUM/LOW blocks
- creative anchor washout detected
- Block 32-43 확장 결과가 훼손됨
- confidence in quality match drops below 90%

## 11. Expected Next Unit After This Order

- if HIGH 7블록 revision clean: `targeted TR revision — Block 44-69 MEDIUM priority` (9 blocks)
- if structural issues found: `TR architecture reassessment`
- if MEDIUM blocks judged unnecessary after HIGH restoration: `revival-stage probe`

## 12. Handoff Format

```text
work_id: empire_youngest_allsector
current_stage: targeted_revision
finished_unit: TR revision Block 44-69 HIGH priority
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 13. 3-Pass Self Audit

### Pass 1. Contract Alignment
- target: one work_id, 7 specific blocks only
- block count stays 70
- no BI/status/gate modification
- emotional arc gap closers authorized (최다은 Block 66, 정하윤 Block 54)
- Block 32-43 결과 보호

### Pass 2. Operational Usefulness
- per-block revision guide with specific gap descriptions
- revision priority matrix ordering respected
- emotional arc gap closers specified with placement
- scene entry 다양화 경고 포함

### Pass 3. Integrity
- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions
- bounded to 7 blocks only

Confidence:
- 96% that `targeted TR revision Block 44-69 HIGH` is the correct next unit
