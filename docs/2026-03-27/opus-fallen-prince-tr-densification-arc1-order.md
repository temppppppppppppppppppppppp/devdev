# OPUS Fallen Prince TR Densification Order — Arc 1

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `fallen_prince_buys_joseon`

## 1. Order Intent

This order fixes the target to `fallen_prince_buys_joseon` and asks OPUS to execute a bounded `spine-preserving TR densification` on Arc 1 (Block 1-10) only.

Current lane truth:
- family: `blockguide`
- entry type: existing `TR + BI` pair revival
- current pair location: `_quarantine`
- TR static audit verdict: `consumable but skeleton-likely`
- recommended action: spine-preserving TR densification before BI repair

This is a densification run, not a full TR regeneration. The spine is preserved; only prose fields are rewritten.

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder → TR audit report before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- **preserve all spine fields exactly** — do not modify title, deal_type, location, time_span, historical_event, source_binding, capital_before/after/delta, foreshadow, callback, relationship_delta, section_rotation, emotional_beat, tension_level, pov_character, opponent.name, block_no, block_id
- rewrite prose fields only: context, event_villain, solution, reward, stakes
- add missing fields: regression_hint, execution_doctrine variation
- expand: weakness_exploited per opponent (currently 1 template for 73%)
- scope: **Arc 1 only (Block 1-10)** — do not touch Block 11-70
- do not promote to active path in the same run
- do not run BI repair in the same run

## 3. Canonical Target

- work_id: `fallen_prince_buys_joseon`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json` (reference for protagonist config, genre constraints)

TR is the only file modified in this run, and only Block 1-10 entries.

## 4. Proven Prior Steps

1. Pair consumability survey:
   - `docs/2026-03-27/fallen-prince-pair-consumability-survey.md`
2. Consumability repair:
   - `docs/2026-03-27/fallen-prince-consumability-repair-report.md`
   - verdict: `pass` — 8/8 blockers resolved
3. TR static audit:
   - `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md`
   - verdict: `consumable but skeleton-likely`
   - 9축 평균: 4.1/10
   - spine 가치: deal_type 70종, location 69종, 역사 31년, source_binding AH-* 6개, 자본궤적 4억→1조6,400억
   - template 오염: event_villain 100%, solution 100%, stakes 100%, sceneability 1/10

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md` (전문 — spine inventory + template evidence)
5. `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json` (hard_constraints, 재료 출처)
6. `treatments/preprocess/fallen_prince_buys_joseon/material_bundle_summary.json` (available materials)

## 6. Immediate Goal

Arc 1 (Block 1-10)의 prose field를 spine 보존 densification으로 재작성한다.

이 10블록 densification은 **canary 성격**이다. Arc 1의 결과물 품질이 확인되면 나머지 Arc 2-7도 같은 방식으로 진행한다. Arc 1에서 방법론이 실패하면, 전면 TR 재생성으로 전환한다.

## 7. Arc 1 Context

TR audit에서 도출된 Arc 1 구조:

- **Arc 1: 황실 금고를 빼돌리다** (Block 1-10, 1907~1910)
- 자본 궤적: 4억 → ? (Block 10 도착점)
- 핵심 역사 이벤트: 헤이그 특사 실패 (1907.6), 고종 강제 퇴위 (1907.7), 정미7조약 (1907.7), 군대 해산 (1907.8), 합방 (1910.8)
- 핵심 병목: 황실 자산 장부, 내장원 금고, 궁내부 소유권, 초기 해외 도피 경로

## 8. Densification Spec

### 8.1 Fields to Preserve (절대 불변)

Block 1-10의 다음 필드는 현재 값을 그대로 유지:
- `block_id`, `block_no`, `title`
- `deal_type`, `location`, `time_span`, `in_story_time`
- `genre_ext.historical_event`, `genre_ext.source_binding`, `genre_ext.knowledge_used`
- `capital_before`, `capital_after`, `capital_delta`
- `foreshadow`, `callback`
- `relationship_delta`
- `section_rotation`, `emotional_beat`, `tension_level`
- `pov_character`, `opponent.name`

### 8.2 Fields to Rewrite (템플릿 → 고유 서술)

각 블록에 대해:

**context** (현재 ~126자, 목표 200자+):
- 첫 문장은 현재도 블록별 고유 — 보존하되 확장
- 구체적 오브젝트 추가 (장부, 인감, 편지, 전보, 계약서 등 시대 특정)
- 공간 묘사 추가 (경운궁 침전, 내장원 복도, 항구 하역장 등)
- 감각 단서 추가 (먹물 냄새, 장판 차가움, 가마 흔들림 등)

**event_villain** (현재 100% 템플릿, 목표 블록별 고유):
- 적대자의 **이 블록 안에서의 구체적 행동** 서술
- 적대자별 행동 패턴 차별화 (통감부 관리 vs 일본 재벌 vs 궁내부 보수파)
- "문서와 인허가, 가격표를 먼저 잠그려 든다" 템플릿 완전 제거

**solution** (현재 100% 템플릿, 목표 블록별 고유):
- 이강윤의 **이 블록 안에서의 구체적 행동** 서술
- 회귀 지식이 어떻게 이 특정 상황에서 작동하는지 보여줌
- "자신에게 유리한 순서로 재배치한다" 템플릿 완전 제거

**stakes** (현재 100% 템플릿, 목표 블록별 고유):
- 이 블록에서 실패하면 구체적으로 무엇을 잃는지
- "쪽으로 넘어간다" 템플릿 완전 제거

**reward** (현재 ~90% 템플릿, 목표 블록별 고유):
- 거래 결과 + 서사적 의미를 블록 고유하게 서술

### 8.3 Fields to Add (현재 부재)

**regression_hint** (Block 1-10 각각에 추가):
- `slip_up`: 이 블록에서 이강윤이 미래 지식을 과도하게 드러내는 구체적 순간
- `suspicion_source`: 누가 의심하는가, 어떤 단서로
- `suspicion_level`: low / medium / high
- pantech 선례: 10/10 블록에 regression_hint 존재

**execution_doctrine** (Block 1-10 각각에 고유화):
- 현재 70블록 동일 ("명분보다 병목, 충성보다 소유권...")
- Block 1-10 각각에 이 아크 안에서의 행동 원칙 변주
- 예: Block 1은 "금고부터 잠그라" → Block 5는 "밀사 경로를 먼저 열어라" → Block 10은 "합방 전에 장부를 끊어라"

**weakness_exploited** (적대자별 고유화):
- 현재 1종이 73% — Block 1-10에 등장하는 적대자별 고유 약점으로 교체

### 8.4 Optional Enhancement

**대화 마커** (dialogue markers):
- 현재 실제 인용 대화 0/70
- Block 1-10에 최소 1개씩 인물 고유 대사 삽입 (context 또는 solution 안에)
- 예: 이강윤의 내면 독백, 적대자의 위협/비아냥, 동맹자의 보고

## 9. Quality Benchmark

Densification 결과물은 pantech Arc 1 (Block 1-10)의 품질을 목표 앵커로 삼는다:

| Metric | pantech Arc 1 | fallen_prince 목표 |
|--------|---------------|-------------------|
| Context stdev | 42 | 30+ |
| event_villain template | 0/10 | 0/10 |
| solution template | 0/10 | 0/10 |
| Sceneability evidence | 10/10 블록에 장소+오브젝트 | 10/10 블록에 장소+오브젝트 |
| regression_hint | 10/10 | 10/10 |
| Dialogue markers | 10/10 | 8+/10 |

## 10. Creative Constraints

Do not wash out these anchors:

- **1907~1910 대한제국 말기 질감**: 경운궁, 내장원, 통감부, 황실 인감, 밀사, 가마, 전보, 먹물, 장판
- **황족 회귀자의 이중 정체**: 열일곱 황자가 1936년 금융 지식을 갖고 있다는 불가능한 조합
- **자산 빼돌리기 긴장**: 합방 시한(1910.8)이 다가오는 카운트다운
- **식민지 금융 메커니즘**: 내장원 소관 자산, 궁내부 vs 통감부 관할 경쟁, 토지 대장, 소작료 현금화 등
- **source_binding**: material_bank.db AH-* 소스의 구체적 사실을 서사에 녹여야 함 — 키워드 나열이 아닌 장면적 활용

If a densified block starts reading like modern business fiction instead of 1907 대한제국, flag it immediately.

## 11. Deliverable

Save two artifacts:

1. **Modified TR** (in-place):
   - `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
   - Block 1-10만 수정, Block 11-70은 원본 그대로

2. **Densification report**:
   - `docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md`
   - 포함: 블록별 before/after diff 요약, spine 보존 확인, 품질 메트릭 (context stdev, template 잔존율, sceneability, regression_hint 추가 현황), pantech 비교, 다음 아크 진행 가능 여부 판정

## 12. Stop Conditions

Stop immediately and report if any of the following occurs:

- spine field가 의도치 않게 변경됨
- source_manifest.hard_constraints와 충돌하는 서술이 발생
- 역사적 사실 오류가 발견됨 (연도, 사건, 인물 혼동)
- densification 결과가 pantech 앵커 대비 현저히 낮아 방법론 자체가 실패
- Block 11+ 에 의도치 않게 손을 댐
- confidence falls below 95%

## 13. Expected Next Unit After This Order

- if Arc 1 densification passes: `TR densification Arc 2-7` (나머지 60블록, 아크 단위로 분할 가능)
- if Arc 1 densification is mixed: 방법론 조정 후 재시도
- if Arc 1 densification fails: `full TR regeneration` with spine as structural input

최종 목표 경로: densification 완료 → BI repair (Step 3) → revival canary (Step 4) → 이후 래더 계속

## 14. Handoff Format

End with this exact flat report:

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR densification Arc 1
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 15. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target is fixed to one `work_id`
- order stays inside router + blockguide + revival-ladder boundaries
- densification scope is bounded to Arc 1 (Block 1-10) only
- spine fields are explicitly listed as immutable
- this is a ladder branch from "skeleton-likely" verdict, not a standard step skip

### Pass 2. Operational Usefulness

- the next unit is singular and concrete: `TR densification Arc 1`
- audit spine inventory is carried forward as preservation checklist
- quality benchmark against pantech provides clear success criteria
- creative constraints preserve 1907 대한제국 질감
- canary logic: Arc 1 result determines whether methodology scales to Arc 2-7

### Pass 3. Integrity

- saved under dated `docs/2026-03-27/`
- UTF-8 only
- no code-edit instructions (system code)
- no multi-unit overreach — Arc 1 only, not full 70-block densification

Confidence:
- 96% that bounded Arc 1 densification is the correct next unit
- 4% risk that spine-preserving approach may not produce sufficient quality, requiring full regeneration
