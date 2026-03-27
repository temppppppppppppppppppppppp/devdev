# OPUS US AI Exile Monopoly TR Rewrite — Tranche 3 Order

Date: 2026-03-27
Track: narrative pipeline
Status: pending
Scope: single-work OPUS order for `us_ai_exile_monopoly`, Tranche 3 only

## 1. Order Intent

This order fixes the target to `us_ai_exile_monopoly` and asks OPUS to complete exactly one bounded unit:

- `TR rewrite — Tranche 3 (Block 1-10, ARC-01)`

Current lane truth:

- family: `blockguide`
- triage: complete (verdict: mixed)
- rewrite plan: complete (approved)
- Tranche 1 (Block 21-30, ARC-03): **complete** — quality gate 6/6 passed
- Tranche 2 (Block 31-40, ARC-04): **complete** — quality gate 7/7 passed
- this is the third execution tranche — **오프닝 훅**
- ARC-01은 작품의 첫인상을 결정한다. 128TB SSD 귀환 이미지가 여기서 장면으로 서야 한다
- plan 평가: Heavy edit, 난이도 ★★★

## 2. Authority Chain

1. `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md` — rewrite plan SSOT
2. `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md` — triage findings
3. Tranche 1-2 완료 결과 — 품질 baseline

## 3. Non-Negotiable Rules

- UTF-8 only
- one work, one owner, one tranche
- no same-work concurrent editing
- no code or system edits
- rewrite Block 1-10 only — do not touch Block 11-70
- do not redesign BI
- do not promote to active path
- do not change arc boundaries, opponent assignments, or block count
- preserve all 8 fixed creative anchors

## 4. Canonical Target

- work_id: `us_ai_exile_monopoly`
- TR: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` (read-only reference)

Output: overwrite Block 1-10 (array index 0-9) in the canonical TR file.

## 5. ARC-01 Context

| Field | Value |
| ---- | ---- |
| Arc | ARC-01 |
| Blocks | 1-10 |
| Opponent | 헬릭스마인드 잔류 라인 |
| Arc Title | 채용 제안서 대신 청구서 |
| Salvageability (from plan) | Heavy edit — opening hook (128TB SSD) is strong, but solution/doctrine are pure template |
| Opponent Weakness Direction | 본사-지사 분리 후 잔류 인력의 의사결정 공백, 이직 불안 |
| Doctrine Theme | 생존 독립 — 고용 거부, 최초 병목 선점 ("초기 생존 모드: 거절이 곧 전략") |
| 대리만족 쾌감 축 | **능력 과시 (첫 증명)** |

## 6. ARC-01 Special Requirements — Opening Hook

### 6.1 Block 1: 128TB SSD 귀환 장면

Block 1은 작품 전체의 첫인상이다. 이 블록에서 반드시:

- **128TB SSD 이미지가 감각적 장면으로 구현되어야 한다** — 인천공항 입국장에서 윤지후가 128TB SSD를 들고 나오는 장면은 추상 서술이 아니라 물리적 장면이어야 한다 (SSD의 무게, 케이스의 질감, 공항의 소리, 계절의 온도 등)
- 미국 빅테크 추방의 감각적 여운이 남아있어야 한다 — 비자 만료, 사물함 정리, 마지막 출근의 기억 등
- "고용 거부" 선언이 첫 대사 근처에서 등장해야 한다 — 이것이 작품의 정체성

### 6.2 과소평가→반전→경악 패턴 (ARC-01 적용)

Plan §5.3:
- **Block 1-3 (과소평가)**: 헬릭스마인드 잔류 라인이 윤지후를 "추방당한 전직 연구원" 정도로 과소평가. 한국 시장에서 혼자 뭘 할 수 있겠냐는 시선
- **Block 4-7 (전술 실행)**: 윤지후가 리즌메시 접근권을 무기로 첫 병목을 선점. 잔류 라인이 서서히 윤지후의 행보를 인식하기 시작
- **Block 8-10 (재평가/경악)**: 잔류 라인이 윤지후의 사용료 모델을 처음으로 체감. "고용하면 됐을 것을"이라는 후회와 "이미 늦었다"는 인식

### 6.3 주인공 첫인상 설계

이 아크에서 독자가 윤지후에 대해 형성하는 인상:

- 차가운 전략가이지만, 추방의 경험에서 오는 **분노와 결의**가 있는 인물
- "고용 거부"가 단순 오만이 아니라 **생존 전략**임을 보여줘야 한다
- Block 1에서 고독과 결의가 공존하는 순간 — 128TB SSD 하나 들고 인천공항을 나오는 사람의 내면

## 7. Rewrite Contract

### 7.1 Mandatory Field Changes

Tranche 1-2와 동일한 필드 변경 계약 + ARC-01 특화:

| Field | Requirement |
| ---- | ---- |
| `content.context` | 전면 리라이트. **Block 1은 128TB SSD 귀환 장면 필수**. 이후 블록은 마포 사무실/초기 사업장의 물리적 공간 |
| `content.event_villain` | 전면 리라이트. 헬릭스마인드 잔류 라인 내부의 구체적 인물, 행동, 과소평가 동기로 교체 |
| `content.solution` | 전면 리라이트. 4대 코어 문장 삭제. 대체 구조 적용 |
| `content.reward` | Heavy edit. 반복 패턴 제거. 블록 고유 성취+대가 |
| `stakes` | Heavy edit. 블록 고유 위험 |
| `power_shift` | Heavy edit. 블록 고유 변화 |
| `genre_ext.opponent.weakness_exploited` | 전면 리라이트. 헬릭스마인드 잔류 라인 고유 약점 (본사-지사 분리 후 의사결정 공백, 이직 불안) |
| `regression_ext.execution_doctrine` | 전면 리라이트. ARC-01 고유 doctrine ("거절이 곧 전략") + 초반/중반/후반 3단계 |

### 7.2 보존 필드

| Field | Rule |
| ---- | ---- |
| `block_id` | 유지 (1-10) |
| `title` | 유지 |
| `genre_ext.deal_type` | 유지 |
| `time_span` | 유지 |
| `pov_character` | 유지 |

### 7.3 Scene Injection Minimum

| 요소 | 최소 요건 |
| ---- | ---- |
| 직접 대화 | 블록당 3회 이상 |
| 공간/감각 묘사 | 블록당 2개 이상 |
| 주인공 내면 | 블록당 1개 이상 (Block 1은 추방 여운 + 결의 필수) |
| 상대 반응 | 블록당 1개 이상 |
| 시간 압박 | 블록당 구체적 데드라인 1개 |

### 7.4 Repetition Kill Rules

6개 금지 문장 동일 적용 + ARC-03/ARC-04 문구 복사 금지.

1. `"해결의 핵심은 기술 설명이 아니라 문장 선점이다"`
2. `"검수·로그·지급·해지 조건을 한 묶음으로 재배치"`
3. `"규격·인증·조달 전장으로 판을 옮긴다"`
4. `"[X]를 잠가 [Y]이 끼어들 틈을 없앤다"`
5. `"모델을 공짜로 풀지 않고, 남이 움직일수록 사용료가 쌓이는 병목부터 잠근다"`
6. `"기술보다 고용, 인수, 규제 프레임에 먼저 매달린다는 점"`

## 8. ARC-01 Opponent Humanization

헬릭스마인드 잔류 라인은 "본사가 떠난 뒤 남은 사람들" — 조직적 불안과 기회주의가 공존:

필요한 인물 분화:

- 잔류 라인 실질 리더 (본사 철수 후 자리를 지킨 사람, 윤지후를 다시 데려오려는 동기)
- 기술 실무자 (윤지후와 함께 일했던 전 동료, 개인적 감정과 조직 충성 사이)
- 사업개발 담당 (한국 시장에서 살아남아야 하는 현실적 압박)
- 본사 연락선 (미국 본사와의 보고 라인, ARC-05 레오 스톤 귀환의 복선)

최소 2명 이상 개별 인물이 직접 대사를 갖고 등장해야 한다.

**핵심**: 이들은 단순 악역이 아니다. 본사에 버림받은 채 한국에서 사업을 유지해야 하는 사람들 — 윤지후에 대한 감정이 "과소평가 → 경계 → 후회"로 변해야 한다.

## 9. ARC-01 → ARC-02 연속성

Block 10 (ARC-01 마지막) → Block 11 (ARC-02 첫 블록, 아직 미리라이트):

- 자본 수치 연속
- 전략적 맥락: ARC-01에서 "첫 병목 선점 + 고용 거부 확립"이 ARC-02의 "라이선스 잠금"으로 자연스럽게 이어져야 함
- Block 11은 아직 미리라이트 상태이므로, Block 10이 기존 Block 11의 시작점과 호환되도록 주의

## 10. Fixed Creative Anchors — This Tranche

ARC-01에서 모든 앵커가 최초로 등장하거나 확립된다:

| Anchor | ARC-01 적용 |
| ---- | ---- |
| **US big-tech exile → Korea return** | **Block 1 오프닝 — 작품의 시작점** |
| **128TB SSD return image** | **Block 1 핵심 이미지 — 감각적 장면으로 구현** |
| ReasonMesh / inference monopoly | 윤지후가 가져온 기술의 정체. 초반에 암시, 중반에 드러남 |
| **"I refuse employment, pay the fee"** | **ARC-01 핵심 선언 — Block 1-3에서 확립** |
| Standards / compliance battlefield | 아직 본격화 전이나, 윤지후의 "규격 문서로 싸우겠다"는 씨앗이 뿌려져야 함 |
| Korea-US AI bottleneck war | 헬릭스마인드 잔류 라인의 존재 자체가 이 전쟁의 전조 |
| Contract language as power | 첫 계약서 장면에서 확립 |
| **Cold-strategist + 추방의 분노/결의** | **작품 첫인상으로서의 주인공 정체성** |

## 11. Mandatory Reads

1. `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md`
2. `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md`
3. `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` — Block 1-11 컨텍스트
4. `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` — BI 참조

## 12. Deliverable

- 수정된 TR JSON: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` (Block 1-10 덮어쓰기)

산출물은 TR JSON 파일 수정 1건뿐. 별도 보고서 없음.

## 13. Quality Gate (7 gates)

| # | Gate | Criterion |
| --- | --- | --- |
| 1 | 템플릿 반복 0 | 6개 금지 문장 + ARC-03/04 문구 복사 없음 |
| 2 | 대화 최소치 | 10개 블록 전부 직접 화법 3회 이상 |
| 3 | 감각 디테일 최소치 | 10개 블록 전부 감각 묘사 2개 이상 |
| 4 | 주인공 내면 최소치 | 10개 블록 전부 내면 비트 1개 이상 |
| 5 | opponent 약점 고유성 | 헬릭스마인드 잔류 라인 고유, ARC-03/04와 변별 |
| 6 | doctrine 고유성 | ARC-01 고유 doctrine, ARC-03/04와 변별 |
| 7 | 128TB SSD 장면 | Block 1에 128TB SSD 귀환이 감각적 장면으로 구현됨 |

**7개 전부 통과 시에만 Tranche 3 완료.**

## 14. Stop Conditions

Stop immediately and report if:

- Block 1-10 기존 필드 구조가 plan과 불일치
- Block 10→11 (미리라이트 상태) 연속성이 완전 단절
- 128TB SSD 장면이 추상 서술로만 처리 가능한 경우
- 어떤 블록에서든 quality gate 미통과

## 15. Expected Next Unit

| 결과 | Next Unit |
| ---- | ---- |
| Tranche 3 quality gate 전부 통과 | **TR rewrite — Tranche 4 (Block 11-20, ARC-02)** |
| Quality gate 부분 실패 | Tranche 3 보수 후 재검증 |

## 16. Handoff Format

```text
work_id: us_ai_exile_monopoly
current_stage: audit_or_repair
finished_unit: TR rewrite — Tranche 3 (Block 1-10, ARC-01)
changed_files: ...
quality_gate: [pass/fail per gate]
next_unit: ...
stop_reason: ...
```

## 17. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target: us_ai_exile_monopoly 단일 work_id
- scope: Block 1-10 only
- plan 상속 + Tranche 1-2 baseline
- creative anchor 전체 8개 중 4개가 ARC-01에서 최초 확립 — 보존 필수

### Pass 2. Operational Usefulness

- 128TB SSD 장면 요건 별도 명시 (quality gate #7)
- 과소평가→반전→경악 패턴 적용 지침
- 주인공 첫인상 설계 지침
- opponent 인물 분화 + 감정 변화 궤적 명시

### Pass 3. Integrity

- 산출물: TR JSON 수정 1건만
- UTF-8 only
- 코드/시스템 수정 없음

Confidence:
- 94% that Tranche 3 (Block 1-10, ARC-01) is the correct next unit
- 난이도 ★★★ 인정 — 오프닝 품질이 작품 전체를 결정하므로 Tranche 1-2보다 높은 주의 필요
