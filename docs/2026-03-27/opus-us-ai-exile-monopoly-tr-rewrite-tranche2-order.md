# OPUS US AI Exile Monopoly TR Rewrite — Tranche 2 Order

Date: 2026-03-27
Track: narrative pipeline
Status: pending
Scope: single-work OPUS order for `us_ai_exile_monopoly`, Tranche 2 only

## 1. Order Intent

This order fixes the target to `us_ai_exile_monopoly` and asks OPUS to complete exactly one bounded unit:

- `TR rewrite — Tranche 2 (Block 31-40, ARC-04)`

Current lane truth:

- family: `blockguide`
- triage: complete (verdict: mixed)
- rewrite plan: complete (approved)
- Tranche 1 (Block 21-30, ARC-03): **complete** — quality gate 6/6 passed
- Tranche 1 established the quality baseline — this tranche must match or exceed it
- ARC-04 is mid-band continuation, same salvageability tier as ARC-03 (Moderate edit)

## 2. Authority Chain

1. `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md` — rewrite plan SSOT
2. `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md` — triage findings
3. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-tranche1-order.md` — Tranche 1 order (quality baseline reference)

Do not re-plan. Follow the plan as written.

## 3. Non-Negotiable Rules

- UTF-8 only
- read plan + Tranche 1 결과 확인 후 작업 시작
- one work, one owner, one tranche
- no same-work concurrent editing
- no code or system edits
- rewrite Block 31-40 only — do not touch any other blocks
- do not redesign BI
- do not promote to active path
- do not change arc boundaries, opponent assignments, or block count
- preserve all 8 fixed creative anchors

## 4. Canonical Target

- work_id: `us_ai_exile_monopoly`
- TR: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` (read-only reference)

Output: overwrite Block 31-40 (array index 30-39) in the canonical TR file.

## 5. ARC-04 Context

| Field | Value |
| ---- | ---- |
| Arc | ARC-04 |
| Blocks | 31-40 |
| Opponent | 국가AI통합 컨소시엄 |
| Arc Title | 국가 AI 입찰과 규격 전쟁 |
| Salvageability (from plan) | Moderate edit — mid-band strength continues |
| Opponent Weakness Direction | 다수 참여자 합의 구조의 느린 의사결정, 정치적 포지셔닝 |
| Doctrine Theme | 규격 장악 — 국가 표준을 자사 기준으로 쓰기 ("시장이 아니라 규칙을 산다") |

### ARC-04 Narrative Position

- ARC-03에서 윤지후가 엣지/통신/API 접점을 복수화했음 → ARC-04에서 그 접점 네트워크를 국가 표준으로 격상시키는 단계
- opponent가 기업이 아니라 **컨소시엄** (다수 이해관계자 연합) → 적대 구조가 단일 기업 대립에서 다자 합의체 정치로 전환
- 이 아크는 "규격/인증/조달 전장"이 가장 직접적으로 구현되는 구간 — creative anchor #5 (standards/compliance/audit-log battlefield)의 핵심 무대

## 6. Tranche 1 Quality Baseline

Tranche 1 (ARC-03)이 확립한 기준:

- opponent 4인 분화 (류웨이/천하오/왕쥔/조현태) — 각각 직접 대사 보유
- execution_doctrine 3단계 변형 (초반 도전/중반 적응/후반 장악)
- 금지 문장 0건
- 전 블록 대화 3+ / 감각 2+ / 내면 1+ / 상대 반응 1+

**Tranche 2는 이 기준을 최소 충족해야 한다.**

## 7. Rewrite Contract

### 7.1 Mandatory Field Changes

Each of the 10 blocks (31-40) must have:

| Field | Requirement |
| ---- | ---- |
| `content.context` | 전면 리라이트. 정부 조달/입찰 현장의 감각 디테일 + 시간 압박 주입 |
| `content.event_villain` | 전면 리라이트. 컨소시엄 내부 구체적 인물의 행동과 정치적 동기로 교체 |
| `content.solution` | 전면 리라이트. 4대 코어 문장 삭제. 대체 구조 적용 (전술 행동 / 상대 좌절 / 비용 / 레버리지 전달) |
| `content.reward` | Heavy edit. 반복 패턴 제거. 블록 고유 성취+대가 명시 |
| `stakes` | Heavy edit. 반복 패턴 제거. 블록 고유 위험 명시 |
| `power_shift` | Heavy edit. protagonist/antagonist 블록 고유 변화 |
| `genre_ext.opponent.weakness_exploited` | 전면 리라이트. 컨소시엄 고유 약점(다자 합의 지연, 정치적 포지셔닝) 적용 |
| `regression_ext.execution_doctrine` | 전면 리라이트. ARC-04 고유 doctrine ("시장이 아니라 규칙을 산다") 적용. 초반/중반/후반 3단계 미세 변형 |

### 7.2 보존 필드

| Field | Rule |
| ---- | ---- |
| `block_id` | 유지 (31-40) |
| `title` | 유지 |
| `genre_ext.deal_type` | 유지 |
| `time_span` | 유지 |
| `pov_character` | 유지 |

### 7.3 Scene Injection Minimum

| 요소 | 최소 요건 |
| ---- | ---- |
| 직접 대화 | 블록당 3회 이상 (윤지후 1, 상대 1, 제3자 1) |
| 공간/감각 묘사 | 블록당 2개 이상 감각 디테일 |
| 주인공 내면 | 블록당 1개 이상 (의심/비용 인식 포함) |
| 상대 반응 | 블록당 1개 이상 (구체적 반응) |
| 시간 압박 | 블록당 구체적 데드라인 1개 |

### 7.4 Repetition Kill Rules

이 Tranche에서 아래 문장이 단 한 번이라도 등장하면 **실패**:

1. `"해결의 핵심은 기술 설명이 아니라 문장 선점이다"`
2. `"검수·로그·지급·해지 조건을 한 묶음으로 재배치"`
3. `"규격·인증·조달 전장으로 판을 옮긴다"`
4. `"[X]를 잠가 [Y]이 끼어들 틈을 없앤다"`
5. `"모델을 공짜로 풀지 않고, 남이 움직일수록 사용료가 쌓이는 병목부터 잠근다"`
6. `"기술보다 고용, 인수, 규제 프레임에 먼저 매달린다는 점"`

**추가**: Tranche 1에서 작성한 ARC-03의 doctrine/weakness 문구를 그대로 복사하는 것도 금지. ARC-04는 ARC-03과 반드시 변별되어야 한다.

## 8. ARC-04 Opponent Humanization

국가AI통합 컨소시엄은 다자 합의체 — 단일 기업보다 내부 정치가 복잡하다.

필요한 인물 분화:

- 컨소시엄 의장 또는 간사 (합의 도출 책임, 정치적 중립 유지 시도)
- 정부 측 실무자 (과기부/산업부 등, 정책 목표와 예산 집행의 딜레마)
- 대기업 대표 참여자 (자사 유리한 표준 밀어넣기 시도)
- 중소/스타트업 대표 참여자 (표준 비용 부담 vs. 시장 접근 기회)

최소 2명 이상 개별 인물이 직접 대사를 갖고 등장해야 한다.

컨소시엄의 드라마는 **외부 적대가 아니라 내부 분열**에서 온다 — 윤지후가 이 분열을 읽고 이용하는 것이 ARC-04의 핵심 전술.

## 9. ARC-03 → ARC-04 연속성

Block 30 (ARC-03 마지막)에서 Block 31 (ARC-04 첫 블록)로의 연속성을 확인하라:

- 자본 수치 연속 (Block 30 종료 자본 = Block 31 시작 자본)
- 전략적 맥락 연속: ARC-03에서 접점 네트워크를 확보한 윤지후가 ARC-04에서 그것을 국가 표준으로 격상시키는 자연스러운 진행
- relationship_delta 연속: ARC-03에서 형성된 관계(화싱AI 인물들과의 관계 변화)가 ARC-04 시작 시 참조 가능해야 함
- Tranche 1에서 리라이트된 Block 30의 실제 내용을 읽고, Block 31이 자연스럽게 이어지도록 작성하라

## 10. Fixed Creative Anchors — This Tranche

ARC-04에서 특히 관련 있는 앵커:

| Anchor | ARC-04 적용 |
| ---- | ---- |
| Standards / compliance / audit-log battlefield | **핵심 무대** — 국가 표준 입찰, 규격 인증, 감사 로그가 이 아크의 전장 |
| Contract language as power | 표준 규격 문서의 문구가 곧 시장 지배력인 상황 |
| ReasonMesh / inference monopoly | 추론 엔진 성능이 표준 벤치마크에서 증명되는 장면 |
| Cold-strategist + depth | 국가급 규격 전쟁에서의 전략 + 공공 이익과 사적 독점의 충돌에서 오는 내면 갈등 |

## 11. Mandatory Reads

1. `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md` — 전체 플랜
2. `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md` — 진단 결과
3. `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` — 현재 TR (Block 30-41 컨텍스트 포함 읽기)
4. `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` — BI 참조 (read-only)

## 12. Deliverable

- 수정된 TR JSON: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` (Block 31-40 덮어쓰기)

산출물은 TR JSON 파일 수정 1건뿐. 별도 보고서 없음.

## 13. Quality Gate (Tranche 완료 시 자가 검증)

| # | Gate | Criterion |
| --- | --- | --- |
| 1 | 템플릿 반복 0 | §7.4의 6개 금지 문장 + ARC-03 문구 복사 없음 |
| 2 | 대화 최소치 | 10개 블록 전부 직접 화법 3회 이상 |
| 3 | 감각 디테일 최소치 | 10개 블록 전부 감각 묘사 2개 이상 |
| 4 | 주인공 내면 최소치 | 10개 블록 전부 내면 비트 1개 이상 |
| 5 | opponent 약점 고유성 | weakness_exploited가 컨소시엄 고유, ARC-03과 변별 |
| 6 | doctrine 고유성 | execution_doctrine이 ARC-04 고유, ARC-03과 변별 |
| 7 | ARC-03→04 연속성 | Block 30→31 자본/맥락/관계 연속 확인 |

**7개 전부 통과 시에만 Tranche 2 완료.**

## 14. Stop Conditions

Stop immediately and report if:

- Block 31-40의 기존 필드 구조가 plan과 불일치
- Tranche 1에서 리라이트한 Block 30과의 연속성이 복원 불가
- solution 리라이트가 plot_roadmap 시퀀스를 파괴
- 어떤 블록에서든 quality gate 미통과

## 15. Expected Next Unit

| 결과 | Next Unit |
| ---- | ---- |
| Tranche 2 quality gate 전부 통과 | **TR rewrite — Tranche 3 (Block 1-10, ARC-01)** |
| Quality gate 부분 실패 | Tranche 2 보수 후 재검증 |

## 16. Handoff Format

```text
work_id: us_ai_exile_monopoly
current_stage: audit_or_repair
finished_unit: TR rewrite — Tranche 2 (Block 31-40, ARC-04)
changed_files: ...
quality_gate: [pass/fail per gate]
next_unit: ...
stop_reason: ...
```

## 17. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target: us_ai_exile_monopoly 단일 work_id
- scope: Block 31-40 only
- plan 상속 + Tranche 1 baseline 참조
- creative anchor 보존 체크리스트 포함

### Pass 2. Operational Usefulness

- 4대 반복 필드 교체 요건 + ARC-03 복사 금지
- 장면 주입 정량 요건
- opponent 인물 분화 (컨소시엄 내부 정치)
- ARC-03→04 연속성 요건 추가
- quality gate 7개 (Tranche 1의 6개 + 연속성 1개)

### Pass 3. Integrity

- 산출물: TR JSON 수정 1건만
- UTF-8 only
- 코드/시스템 수정 없음

Confidence:
- 95% that Tranche 2 (Block 31-40, ARC-04) is the correct next unit
