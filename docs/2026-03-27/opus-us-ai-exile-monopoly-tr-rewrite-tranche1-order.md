# OPUS US AI Exile Monopoly TR Rewrite — Tranche 1 Order

Date: 2026-03-27
Track: narrative pipeline
Status: pending
Scope: single-work OPUS order for `us_ai_exile_monopoly`, Tranche 1 only

## 1. Order Intent

This order fixes the target to `us_ai_exile_monopoly` and asks OPUS to complete exactly one bounded unit:

- `TR rewrite — Tranche 1 (Block 21-30, ARC-03)`

Current lane truth:

- family: `blockguide`
- entry type: existing `TR + BI` pair in `_quarantine`
- source-TR weakness triage: **complete** (verdict: mixed)
- TR rewrite plan: **complete** (approved)
- the current task is the first execution tranche of that plan
- ARC-03 (Block 21-30) was chosen as Tranche 1 because it has the strongest surviving material and will establish the quality baseline for all subsequent tranches

This is not a planning order. This is a bounded rewrite execution order.

## 2. Authority Chain

This order inherits from:

1. `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md` — rewrite plan (SSOT for how to rewrite)
2. `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md` — triage findings (SSOT for what is wrong)
3. `docs/2026-03-27/opus-us-ai-exile-monopoly-tr-rewrite-plan-order.md` — plan order context

Do not re-plan. Follow the plan as written.

## 3. Non-Negotiable Rules

- UTF-8 only
- read plan + triage report before doing anything else
- one work, one owner, one tranche
- no same-work concurrent editing
- no code or system edits
- rewrite Block 21-30 only — do not touch Block 1-20 or Block 31-70
- do not redesign BI in this run
- do not promote to active path in this run
- do not change arc boundaries, opponent assignments, or block count
- preserve all 8 fixed creative anchors

## 4. Canonical Target

- work_id: `us_ai_exile_monopoly`
- TR: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json`
- BI: `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` (read-only reference)

Output: overwrite Block 21-30 (array index 20-29) in the canonical TR file.

## 5. ARC-03 Context

| Field | Value |
| ---- | ---- |
| Arc | ARC-03 |
| Blocks | 21-30 |
| Opponent | 화싱AI 한국법인 |
| Arc Title | 클라우드보다 가까운 접점을 먹다 |
| Salvageability (from plan) | Moderate edit — strongest band |
| Opponent Weakness Direction | 중국 본사 지시 vs. 한국 현지 규제의 이중 구속 |
| Doctrine Theme | 접점 확장 — 엣지, 통신, API로 관문 복수화 ("하나의 병목이 아니라 병목의 네트워크") |

## 6. Rewrite Contract (from Plan §4-5)

### 6.1 Mandatory Field Changes

Each of the 10 blocks (21-30) must have:

| Field | Requirement |
| ---- | ---- |
| `content.context` | 전면 리라이트. 감각 디테일 + 시간 압박 주입. 장소명만 나열 불가 |
| `content.event_villain` | 전면 리라이트. 화싱AI 내부의 구체적 인물, 행동, 동기로 교체 |
| `content.solution` | 전면 리라이트. 4대 코어 문장 전면 삭제. 대체 구조 적용 (구체적 전술 행동 / 상대 예상 대응과 좌절 / 비용·대가 / 다음 블록 레버리지 전달) |
| `content.reward` | Heavy edit. "관문으로 만드는 데 성공한다" 패턴 제거. 블록 고유 성취+대가 명시 |
| `stakes` | Heavy edit. 반복 패턴 제거. 블록 고유 위험 명시 |
| `power_shift` | Heavy edit. protagonist/antagonist 모두 블록 고유 변화 |
| `genre_ext.opponent.weakness_exploited` | 전면 리라이트. "기술보다 고용/인수/규제에 매달린다" 삭제. 화싱AI 고유 약점(중국 본사 vs 한국 규제 이중 구속) 적용 |
| `regression_ext.execution_doctrine` | 전면 리라이트. ARC-03 고유 doctrine 적용. 아크 내 초반/중반/후반 미세 변형 권장 |

### 6.2 보존 필드

| Field | Rule |
| ---- | ---- |
| `block_id` | 유지 (21-30) |
| `title` | 유지 — 기존 제목 보존 |
| `genre_ext.deal_type` | 유지 — 기존 값 보존 |
| `time_span` | 유지 — 기존 시간선 보존 |
| `pov_character` | 유지 — 윤지후 고정 |

### 6.3 Scene Injection Minimum

모든 10개 블록이 아래를 충족해야 한다:

| 요소 | 최소 요건 |
| ---- | ---- |
| 직접 대화 | 블록당 3회 이상 (윤지후 1, 상대 1, 제3자 1) |
| 공간/감각 묘사 | 블록당 2개 이상 감각 디테일 |
| 주인공 내면 | 블록당 1개 이상 (의심/비용 인식/긴장 포함. "차가운 확신"만 불가) |
| 상대 반응 | 블록당 1개 이상 (구체적 반응, 단순 패배 선언 불가) |
| 시간 압박 | 블록당 구체적 데드라인 1개 |

### 6.4 Repetition Kill Rules

이 Tranche에서 아래 문장이 단 한 번이라도 등장하면 **실패**:

1. `"해결의 핵심은 기술 설명이 아니라 문장 선점이다"`
2. `"검수·로그·지급·해지 조건을 한 묶음으로 재배치"`
3. `"규격·인증·조달 전장으로 판을 옮긴다"`
4. `"[X]를 잠가 [Y]이 끼어들 틈을 없앤다"`
5. `"모델을 공짜로 풀지 않고, 남이 움직일수록 사용료가 쌓이는 병목부터 잠근다"`
6. `"기술보다 고용, 인수, 규제 프레임에 먼저 매달린다는 점"`

## 7. ARC-03 Opponent Humanization

화싱AI 한국법인은 단일 엔티티가 아니다. 10블록에 걸쳐 아래와 같은 인물 분화가 필요:

- 한국법인 대표 (본사 지시 vs 현지 적응 딜레마)
- 기술 실무 리드 (윤지후의 기술을 인정하지만 경쟁해야 하는 위치)
- 본사 파견 감시자 (중국 본사 이해 대변)
- 한국 현지 영업/파트너십 담당 (규제 환경을 가장 잘 아는 인물)

최소 2명 이상의 개별 인물이 직접 대사를 갖고 등장해야 한다.

## 8. Fixed Creative Anchors — This Tranche

ARC-03에서 특히 관련 있는 앵커:

| Anchor | ARC-03 적용 |
| ---- | ---- |
| ReasonMesh / inference monopoly | 엣지 추론 접점 확장의 기술적 근거로 사용 |
| Contract language as power | 통신사/엣지 API 계약 장면에서 구현 |
| Standards / compliance battlefield | NPU 테스트, 통신 규격 인증 장면 |
| Cold-strategist + depth | 윤지후의 접점 복수화 전략 + 그 비용 인식 |

## 9. Mandatory Reads

Read these before rewriting:

1. `docs/2026-03-27/us-ai-exile-monopoly-tr-rewrite-plan.md` — 전체 플랜
2. `docs/2026-03-27/us-ai-exile-monopoly-tr-weakness-triage-report.md` — 진단 결과
3. `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` — 현재 TR (최소 Block 21-30 + 인접 블록 20, 31 컨텍스트)
4. `bible/_quarantine/0_bi_us_ai_exile_monopoly.json` — BI 참조 (read-only)

## 10. Deliverable

- 수정된 TR JSON: `treatments/_quarantine/us_ai_exile_monopoly_tr_block_070_draft.json` (Block 21-30 덮어쓰기)

산출물은 TR JSON 파일 수정 1건뿐이다. 별도 보고서는 이 Tranche에서 생산하지 않는다.

## 11. Quality Gate (Tranche 완료 시 자가 검증)

Tranche 1 완료 후 아래 6개 게이트를 자가 검증하라:

1. **템플릿 반복 0**: §6.4의 6개 금지 문장이 Block 21-30 어디에도 없음
2. **대화 최소치**: 10개 블록 전부 직접 화법 3회 이상
3. **감각 디테일 최소치**: 10개 블록 전부 감각 묘사 2개 이상
4. **주인공 내면 최소치**: 10개 블록 전부 내면 비트 1개 이상
5. **opponent 약점 고유성**: weakness_exploited가 화싱AI 고유 약점으로 교체됨
6. **execution_doctrine 고유성**: ARC-03 고유 doctrine 적용됨, 다른 아크의 현재 doctrine과 다름

6개 전부 통과 시에만 Tranche 1 완료로 인정.

## 12. Stop Conditions

Stop immediately and report if:

- Block 21-30의 기존 내용이 plan에서 기술한 것과 구조적으로 다른 경우 (예: 필드 이름 불일치)
- BI 참조 데이터가 ARC-03 블록과 비동기화된 경우
- solution 리라이트가 plot_roadmap의 해당 아크 시퀀스를 파괴하는 경우
- 리라이트 후 인접 블록(20, 31)과의 연결성이 끊기는 경우
- 어떤 블록에서든 quality gate를 통과하지 못하는 경우

## 13. Expected Next Unit After This Tranche

| 결과 | Next Unit |
| ---- | ---- |
| Tranche 1 quality gate 전부 통과 | **TR rewrite — Tranche 2 (Block 31-40, ARC-04)** |
| Quality gate 부분 실패 | Tranche 1 보수 후 재검증 |
| 구조적 blocker 발견 | Plan 수정 → 재계획 |

## 14. Handoff Format

```text
work_id: us_ai_exile_monopoly
current_stage: audit_or_repair
finished_unit: TR rewrite — Tranche 1 (Block 21-30, ARC-03)
changed_files: ...
quality_gate: [pass/fail per gate]
next_unit: ...
stop_reason: ...
```

## 15. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target: us_ai_exile_monopoly 단일 work_id 고정
- scope: Block 21-30 only — 다른 블록 수정 없음
- plan 상속: rewrite plan의 §4-5-6-7-8 지침을 구체화, 재계획 없음
- creative anchor 보존 체크리스트 포함

### Pass 2. Operational Usefulness

- 4대 반복 필드 교체 요건 명시
- 장면 주입 최소치 정량 지정
- 금지 문장 6개 명시적 열거
- opponent 인물 분화 요건 명시
- quality gate 6개 명시

### Pass 3. Integrity

- 산출물: TR JSON 파일 수정 1건만
- UTF-8 only
- 코드/시스템 수정 없음
- 1-tranche scope only

Confidence:
- 95% that Tranche 1 (Block 21-30, ARC-03) is the correct first rewrite unit
