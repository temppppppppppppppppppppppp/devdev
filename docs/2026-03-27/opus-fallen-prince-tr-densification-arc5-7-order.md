# OPUS Fallen Prince TR Densification Order — Arc 5-7

Date: 2026-03-27
Track: narrative pipeline
Status: active
Scope: single-work OPUS order for `fallen_prince_buys_joseon`

## 1. Order Intent

This order fixes the target to `fallen_prince_buys_joseon` and asks OPUS to execute spine-preserving TR densification on **Arc 5-7 (Block 41-70)** — the final 30 blocks.

Current lane truth:
- family: `blockguide`
- TR static audit verdict: `consumable but skeleton-likely`
- Arc 1 densification (Block 1-10): **PASS**
- Arc 2-4 densification (Block 11-40): **PASS**
- remaining: **Block 41-70 (30 blocks, 3 arcs)** — this is the last densification batch

## 2. Non-Negotiable Rules

- UTF-8 only
- read router → family SSOT → revival ladder before doing anything else
- one work, one owner, one unit
- no same-work concurrent editing
- no code or system edits
- **preserve all spine fields exactly**
- rewrite prose fields only: context, event_villain, solution, reward, stakes
- add missing fields: regression_hint, execution_doctrine variation, weakness_exploited per opponent
- scope: **Block 41-70 only** — do not touch Block 1-40 (already densified)
- do not promote to active path
- do not run BI repair in the same run

## 3. Canonical Target

- work_id: `fallen_prince_buys_joseon`
- TR: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- BI: `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json` (reference only)

TR is the only file modified. Only Block 41-70 entries.

## 4. Proven Prior Steps

1. Pair consumability survey → pass with warnings
2. Consumability repair → pass (8/8 blockers)
3. TR static audit → consumable but skeleton-likely (4.1/10)
4. TR densification Arc 1 (Block 1-10) → **PASS**
   - `docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md`
5. TR densification Arc 2-4 (Block 11-40) → **PASS**
   - `docs/2026-03-27/fallen-prince-tr-densification-arc2-4-report.md`
   - template 0/30, regression_hint 30/30, dialogue 30/30, spine 100% 보존

## 5. Mandatory Reads

Read these in order:

1. `docs/narrative-router/SSOT_narrative-router-integrated-order.md`
2. `docs/blockguide/SSOT_blockguide-integrated-order.md`
3. `docs/narrative-router/material-revival-ladder-harness.md`
4. `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md` (spine inventory + back-half context)
5. `docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md` (methodology anchor)
6. `docs/2026-03-27/fallen-prince-tr-densification-arc2-4-report.md` (직전 결과)
7. `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`

## 6. Immediate Goal

Block 41-70 (Arc 5-7)의 prose field를 Arc 1-4와 동일한 방법론으로 densification한다. 이 배치가 완료되면 **70블록 전체 densification이 종결**된다.

### Arc 5: 대공황을 사냥하다 (Block 41-50, 1929~1932)
- 핵심: 대공황 타이밍 활용 — 폭락 매집, 유럽 부실자산 인수, 금본위제 이탈 활용
- 역사 이벤트: 월가 대폭락(1929.10), 파운드 금본위 이탈(1931), 쌀값 폭락, 창고증권 제도화
- 장르 질감: 취리히·런던·로테르담 금융가, 경성 은행 거리, 조선총독부 산금정책

### Arc 6: 제국의 월세 (Block 51-60, 1932~1937)
- 핵심: 수익 체계 구축 — 5대 병목(해운·보험·철도·은행·광산) 수익화, 식민지 경제 내 실질 지배
- 역사 이벤트: 만주사변 여파, 조선산금령, 일본 군수경제 확대, 중일전쟁 전야
- 장르 질감: 경성 산업은행, 부산 부두, 광산촌, 보험 시장, 일본 재벌 vs 조선인 자본가 긴장

### Arc 7: 조선을 산다 (Block 61-70, 1937~1938)
- 핵심: 실소유주 선언 — 국가총동원 체제 속 최종 병목 장악, 전생 독살의 배후와 대면
- 역사 이벤트: 중일전쟁(1937), 국가총동원법(1938), 전시통제경제
- 장르 질감: 전시 배급, 군수 공장, 총독부 기업통제, 취리히 은행 금고, 독살 진실
- **특수 주의**: 이 아크는 TR audit에서 pantech 후반부처럼 "공공 인프라 추상화" 드리프트 리스크가 있었던 구간. 국가총동원/전시경제가 generic governance abstraction으로 빠지지 않도록, 이강윤 개인의 생존과 자산 전쟁으로 서술할 것

## 7. Densification Spec

Arc 1-4와 동일. 재확인:

### 7.1 Spine 보존 (절대 불변)
모든 spine field 불변 (block_id, block_no, title, deal_type, location, time_span, in_story_time, genre_ext.*, capital_*, foreshadow, callback, relationship_delta, section_rotation, emotional_beat, tension_level, pov_character, opponent.name)

### 7.2 Prose 재작성
- **context**: 200자+, 구체적 오브젝트, 공간 묘사, 감각 단서
- **event_villain**: 적대자의 이 블록 구체적 행동, 템플릿 완전 제거
- **solution**: 이강윤의 이 블록 구체적 행동 + 회귀 지식 작동, 템플릿 완전 제거
- **stakes**: 이 블록 실패 시 구체적 손실, 템플릿 완전 제거
- **reward**: 거래 결과 + 서사적 의미, 블록별 고유

### 7.3 신규 추가
- **regression_hint**: 블록별 slip_up, suspicion_source, suspicion_level
- **execution_doctrine**: 블록별 고유 행동 원칙
- **weakness_exploited**: 적대자별 고유 약점

### 7.4 대화 마커 + 감각 단서
- 30블록 각각 최소 1개 인물 고유 대사
- 30블록 각각 최소 1개 감각 단서

## 8. Quality Benchmark

| Metric | Arc 1 | Arc 2-4 | Arc 5-7 목표 |
|--------|-------|---------|-------------|
| Template residual | 0/10 | 0/30 | 0/30 |
| regression_hint | 10/10 | 30/30 | 30/30 |
| execution_doctrine unique | 10 | 30 | 30 |
| weakness_exploited unique | 10 | 30 | 30 |
| Dialogue markers | 10/10 | 30/30 | 28+/30 |
| Spine preserved | 100% | 100% | 100% |

## 9. Back-Half Drift Watch

TR audit §Axis 1에서 pantech 후반부 thematic drift가 지적되었고, fallen_prince도 동일 리스크가 있다:

- **Block 41-50 (대공황)**: 금융 추상화 리스크 — "포트폴리오 최적화" 같은 현대 금융 용어가 아닌, 1930년대 식민지 조선/유럽 금융의 구체적 메커니즘으로 서술
- **Block 51-60 (수익 체계)**: 경영 추상화 리스크 — "5대 병목 시너지" 같은 MBA 언어가 아닌, 부산 부두에서 쌀을 싣고 광산에서 금을 캐는 현장 질감
- **Block 61-70 (실소유주)**: 거버넌스 추상화 리스크 — 국가총동원이 generic policy discussion으로 빠지지 않도록, 이강윤이 전시통제 속에서 자산을 지키기 위해 벌이는 구체적 전쟁으로 서술

**만약 densification 중 3블록 이상에서 현대 금융/경영 추상어가 시대 질감을 압도하면, 중간 보고 후 재조정.**

## 10. Deliverable

Save two artifacts:

1. **Modified TR** (in-place):
   - `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
   - Block 41-70만 수정, Block 1-40 무변경

2. **Densification report**:
   - `docs/2026-03-27/fallen-prince-tr-densification-arc5-7-report.md`
   - 포함: 아크별 before/after 요약, spine 보존 확인, 품질 메트릭, Arc 1-4 대비 일관성, **70블록 전체 densification 종합 판정**, BI repair 진행 가능 여부

## 11. Stop Conditions

- spine field 변경 감지
- Block 1-40 변경 감지
- 역사적 사실 오류
- back-half drift (3+ blocks에서 현대 추상어 압도)
- confidence < 95%

## 12. Expected Next Unit

- if Arc 5-7 passes → **70블록 전체 densification 완료** → next: `BI repair` (ladder Step 3)
- if mixed: 해당 아크만 재시도
- if fail: 해당 아크 개별 조정

## 13. Handoff Format

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR densification Arc 5-7
changed_files: ...
next_unit: ...
stop_reason: ...
```

## 14. 3-Pass Self Audit

### Pass 1. Contract Alignment
- target fixed to one work_id
- scope bounded to Block 41-70
- spine immutable, prose-only rewrite
- no BI modification, no promotion

### Pass 2. Operational Usefulness
- Arc 1-4 proven methodology carried forward
- 아크별 시대 컨텍스트 명시 (Arc 5: 대공황, Arc 6: 수익 체계, Arc 7: 전시+독살)
- back-half drift watch 명시적으로 설정
- 이 배치 완료 시 전체 densification 종결 → BI repair 진입 판정

### Pass 3. Integrity
- dated docs/2026-03-27/
- UTF-8 only
- no code edits
- Block 1-40 불변

Confidence:
- 97% — methodology validated across 40 blocks, back-half drift is main risk
