# OPUS Fallen Prince TR Densification Order — Arc 2-4

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `fallen_prince_buys_joseon`

## 1. Order Intent

This order fixes the target to `fallen_prince_buys_joseon` and asks OPUS to execute spine-preserving TR densification on **Arc 2-4 (Block 11-40)**.

Current lane truth:
- family: `blockguide`
- TR static audit verdict: `consumable but skeleton-likely`
- Arc 1 densification (Block 1-10): **PASS** — methodology validated
- remaining: Block 11-70 (60 blocks, 6 arcs)
- this run: Block 11-40 (30 blocks, 3 arcs)

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- **preserve all spine fields exactly** — same immutable list as Arc 1 order
- rewrite prose fields only: context, event_villain, solution, reward, stakes
- add missing fields: regression_hint, execution_doctrine variation, weakness_exploited per opponent
- scope: **Block 11-40 only** — do not touch Block 1-10 (already densified) or Block 41-70
- do not promote to active path
- do not run BI repair in the same run

## 3. Canonical Target

- work_id: `fallen_prince_buys_joseon`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json` (reference only)

TR is the only file modified. Only Block 11-40 entries.

## 4. Proven Prior Steps

1. Pair consumability survey → pass with warnings
2. Consumability repair → pass (8/8 blockers)
3. TR static audit → consumable but skeleton-likely (4.1/10)
4. TR densification Arc 1 (Block 1-10) → **PASS**
   - `docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md`
   - template 0/10, context stdev 36, regression_hint 10/10, 대화 10/10, 감각 10/10
   - spine 100% 보존 확인

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md` (spine inventory + template evidence)
5. `docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md` (proven methodology + quality anchor)
6. `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`

## 6. Immediate Goal

Block 11-40 (Arc 2-4)의 prose field를 Arc 1과 동일한 방법론으로 densification한다.

### Arc 2: 바다 위의 장부 (Block 11-20, 1910~1914)
- 핵심: 합방 직후 해운 진출, 일본 해운 카르텔 대항, 1차대전 직전 포지셔닝
- 역사 이벤트: 합방(1910), 신해혁명(1911), 1차대전 개전(1914)

### Arc 3: 전쟁이 낳은 화폐 (Block 21-30, 1914~1918)
- 핵심: 1차대전 활용 — 전시 해운 붐, 보험 시장, 유럽 금융 진출
- 역사 이벤트: 1차대전(1914-1918), 전시 경제 통제

### Arc 4: 등기부의 주인 (Block 31-40, 1920s)
- 핵심: 식민지 토지/철도 장악, 전후 불황 활용
- 역사 이벤트: 3.1운동(1919), 산미증식계획, 1920s 전후 해운 붐 붕괴

## 7. Densification Spec

**Arc 1과 동일한 spec을 그대로 적용한다.** 주요 요점만 재확인:

### 7.1 Spine 보존 (절대 불변)

Block 11-40의 모든 spine field: block_id, block_no, title, deal_type, location, time_span, in_story_time, genre_ext.historical_event, genre_ext.source_binding, genre_ext.knowledge_used, capital_before/after/delta, foreshadow, callback, relationship_delta, section_rotation, emotional_beat, tension_level, pov_character, opponent.name

### 7.2 Prose 재작성

- **context**: 200자+, 구체적 오브젝트, 공간 묘사, 감각 단서. 첫 문장(블록별 고유) 보존 확장
- **event_villain**: 적대자의 이 블록 구체적 행동. 템플릿 완전 제거
- **solution**: 이강윤의 이 블록 구체적 행동 + 회귀 지식 작동 방식. 템플릿 완전 제거
- **stakes**: 이 블록 실패 시 구체적 손실. 템플릿 완전 제거
- **reward**: 거래 결과 + 서사적 의미. 블록별 고유

### 7.3 신규 추가

- **regression_hint**: 블록별 slip_up, suspicion_source, suspicion_level
- **execution_doctrine**: 블록별 고유 행동 원칙 변주
- **weakness_exploited**: 적대자별 고유 약점

### 7.4 대화 마커 + 감각 단서

- 30블록 각각 최소 1개 인물 고유 대사
- 30블록 각각 최소 1개 감각 단서

## 8. Quality Benchmark

Arc 1 결과를 앵커로:

| Metric | Arc 1 결과 | Arc 2-4 목표 |
|--------|-----------|-------------|
| Template 잔존 | 0/10 | 0/30 |
| Context stdev | 36 | 30+ |
| regression_hint | 10/10 | 30/30 |
| execution_doctrine unique | 10종 | 30종 |
| 실제 인용 대화 | 10/10 | 28+/30 |
| 감각 단서 | 10/10 | 28+/30 |

## 9. Creative Constraints

아크별 시대 질감을 반드시 유지:

- **Arc 2 (1910~1914)**: 합방 직후 조선, 일본 해운 카르텔 (NYK/OSK), 인천·부산·시모노세키 항로, 조선총독부 초기 통치, 토지조사사업 시작
- **Arc 3 (1914~1918)**: 전시 해운 호황, 잠수함전, 전시 보험, 유럽 금융 혼란, 전쟁특수, 면방직 산업
- **Arc 4 (1920s)**: 전후 불황, 산미증식계획, 식민지 토지 재편, 철도 이권, 조선은행권, 금본위제 논쟁

1907 대한제국이 아닌 **각 아크 고유의 10년대 질감**이 서술에 드러나야 한다.

## 10. Deliverable

Save two artifacts:

1. **Modified TR** (in-place):
   - `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
   - Block 11-40만 수정, Block 1-10 (기 densified) 및 Block 41-70 무변경

2. **Densification report**:
   - `docs/2026-03-27/fallen-prince-tr-densification-arc2-4-report.md`
   - 포함: 아크별 before/after 요약, spine 보존 확인, 품질 메트릭, Arc 1 대비 품질 일관성, Arc 5-7 진행 가능 여부 판정

## 11. Stop Conditions

Arc 1과 동일:
- spine field 변경 감지
- source_manifest.hard_constraints 충돌
- 역사적 사실 오류
- Block 1-10 또는 Block 41-70 변경 감지
- confidence < 95%

추가:
- 30블록 중 5블록 이상에서 품질이 Arc 1 수준에 미달하면 중간 보고 후 방법론 재조정

## 12. Expected Next Unit

- if Arc 2-4 passes: `TR densification Arc 5-7` (Block 41-70)
- if mixed: 방법론 조정 후 재시도
- if fail: 해당 아크만 개별 재시도

## 13. Handoff Format

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR densification Arc 2-4
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment

- target fixed to one work_id
- scope bounded to Block 11-40
- spine immutable, prose-only rewrite
- no BI modification, no promotion

### Pass 2. Operational Usefulness

- Arc 1 proven methodology carried forward
- 아크별 시대 컨텍스트 명시 (Arc 2: 합방 후 해운, Arc 3: 1차대전, Arc 4: 1920s 토지)
- quality benchmark against Arc 1 결과

### Pass 3. Integrity

- dated docs/2026-03-27/
- UTF-8 only
- no code edits
- Block 1-10 및 41-70 불변

Confidence:
- 97% — Arc 1 methodology validated, 30-block batch is manageable
