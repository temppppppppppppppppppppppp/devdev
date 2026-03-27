# fallen_prince_buys_joseon TR Densification Arc 1 Report

Date: 2026-03-27
Type: spine-preserving TR densification (Arc 1, Block 1-10)
Target: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`

---

## 1. Spine Preservation

All spine fields preserved across Block 1-10:
- title: 10/10 unchanged
- deal_type: 10/10 unchanged
- location: 10/10 unchanged
- time_span: 10/10 unchanged
- historical_event: 10/10 unchanged
- source_binding: 10/10 unchanged
- capital_before/after/delta: 10/10 unchanged
- foreshadow: 10/10 unchanged
- callback: 10/10 unchanged
- relationship_delta: 10/10 unchanged
- emotional_beat/tension_level: 10/10 unchanged

**Block 11-70 untouched**: solution template "자신에게 유리한 순서로 재배치" 60/60 유지 확인.

## 2. Template Elimination

| Template | Before (Block 1-10) | After |
|----------|---------------------|-------|
| event_villain "주도권을 넓히기 전에" | 10/10 | **0/10** |
| solution "자신에게 유리한 순서로 재배치" | 10/10 | **0/10** |
| stakes "쪽으로 넘어간다" | 10/10 | **0/10** |

**100% 템플릿 제거 완료.**

## 3. Quality Metrics

### Content Length

| Field | Before avg | Before stdev | After avg | After stdev |
|-------|-----------|-------------|-----------|-------------|
| context | 126 | 13 | 228 | **36** |
| solution | 155 | 10 | 240 | **37** |
| event_villain | 66 | 2 | 150 | **33** |

Context stdev: 13 → **36** (pantech 앵커 42에 근접). 템플릿 slot-fill에서 자연 변주로 전환됨.

### New Fields Added

| Field | Before | After |
|-------|--------|-------|
| regression_hint | 0/10 | **10/10** (slip_up + suspicion_source + suspicion_level) |
| execution_doctrine variation | 1종 70회 반복 | **10종 unique** |
| weakness_exploited variation | 1종 반복 | **10종 unique** (적대자별 고유화) |
| Dialogue markers (actual quotes) | 0/10 | **10/10** |

### Pantech Comparison

| Metric | pantech Arc 1 | fallen_prince Arc 1 (after) | Target met? |
|--------|---------------|----------------------------|-------------|
| Context stdev | 42 | 36 | Close (86%) |
| event_villain template | 0/10 | 0/10 | **YES** |
| solution template | 0/10 | 0/10 | **YES** |
| Sceneability (location+object) | 10/10 | 10/10 | **YES** |
| regression_hint | 10/10 | 10/10 | **YES** |
| Dialogue markers | 10/10 | 10/10 | **YES** |

## 4. Sceneability Evidence

### 구체적 오브젝트 (샘플)

- Block 1: 상소문 뭉치의 먹물, 석유 냄새 나는 등잔, 금괴 봉인 번호
- Block 3: 금괴 38봉, 은정 14매, 보석함 두 개, 이중 자물쇠
- Block 5: 논두렁 사이 흙길, 엽전과 제일은행권, 황자의 인장
- Block 6: 화약 연기, 면포와 소금 위장 상자, 연안 운송선
- Block 9: 겨울 바다 짠내, 속옷 안감에 꿰맨 어음, 서적 사이 문서

### 감각 단서

- Block 1: 쓸개즙 같은 맛 (미각), 장판 촉감, 먹물 마르지 않음
- Block 2: 수염 없는 얼굴, 가느다란 목소리, 발소리
- Block 3: 습기와 쇠 냄새, 등잔 불빛
- Block 7: 백동화 제일은행 줄, 분노의 공기
- Block 9: 짠내, 마르고 작은 몸

### 실제 인용 대화

- Block 1: "금고 분리 명부를 따로 만들어라."
- Block 2: "눈치채도 상관없어. 목록을 완성하지 못하면 되는 거야."
- Block 3: "보석은 눈에 보이지만, 장부는 눈에 보이지 않는다."
- Block 4: "독립 자금이 아니라 상업 송금이다."
- Block 7: "화폐가 바뀔 때 손해를 보는 건 마지막에 교환하는 사람이야."
- Block 8: "제일은행 안에 들어가면 나올 수 없어. 밖에서 돌려야 한다."
- Block 9: "판데르벨트에게 보여줄 것은 명함이 아니라 선복 계약서다."
- Block 10: "합방 당일, 이 장부에는 빈 칸만 남아야 한다."

## 5. Regression Hint Summary

| Block | slip_up | suspicion_source | level |
|-------|---------|-----------------|-------|
| 1 | 밀봉된 금고의 봉인 번호를 알고 있음 | 한예담 | low |
| 2 | 유럽 은행명을 즉시 언급 | 한예담 | low |
| 3 | 내장원 장부 복식부기 구조를 서기관급으로 설명 | 윤창식 | medium |
| 4 | 밀사 송금 경로 세부를 궁 안에서 앎 | 최무진 | low |
| 5 | 역둔토 국유화 일정을 정확히 앎 | 수납 서기 | low |
| 6 | 군대 해산 날짜와 의병 봉기 지점 예측 | 한예담 | medium |
| 7 | 화폐 교환 비율 최종 착지점 예측 | 객주 주인 | low |
| 8 | 한국은행→조선은행 전환 시점/절차를 미리 앎 | 최무진 | medium |
| 9 | 판데르벨트의 사업 규모를 처음 만나면서 정확히 앎 | 판데르벨트 | medium |
| 10 | 합방 공포일을 정확히 알고 며칠 전에 절단 완료 | 소피 아들러 | medium |

의심 누적: low→low→**medium**→low→low→**medium**→low→**medium**→**medium**→**medium**. Arc 1 후반으로 갈수록 medium이 누적되며 긴장이 상승.

## 6. Arc 1 Densification Verdict

**PASS — 방법론 유효.**

- 템플릿 100% 제거
- context stdev 13→36 (pantech 42의 86%)
- sceneability: 10/10 블록에 장소+오브젝트+대화+감각
- regression_hint 10/10 추가
- execution_doctrine 10종 unique
- weakness_exploited 10종 unique
- spine 100% 보존
- Block 11-70 무변경 확인
- 1907 대한제국 질감 유지 (내장원, 통감부, 백동화, 역둔토, 밀사 경로, 영일동맹)

**이 방법론은 Arc 2-7로 확장 가능하다.**

---

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR densification Arc 1
changed_files: treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json, docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md
next_unit: TR densification Arc 2-7 (remaining 60 blocks, arc-by-arc)
stop_reason: Arc 1 canary passed — methodology validated, template eliminated, sceneability restored, spine preserved
```
