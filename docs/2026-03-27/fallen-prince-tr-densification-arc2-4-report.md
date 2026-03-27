# fallen_prince_buys_joseon TR Densification Arc 2-4 Report

Date: 2026-03-27
Type: spine-preserving TR densification (Arc 2-4, Block 11-40)
Target: `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`

---

## 1. Spine Preservation

All spine fields preserved across Block 11-40 (30 blocks):
- title, deal_type, location, time_span, historical_event, source_binding, capital_before/after/delta, foreshadow, callback, relationship_delta, section_rotation, emotional_beat, tension_level, pov_character, opponent.name: **30/30 unchanged**

Adjacent blocks untouched:
- Block 1-10 (Arc 1, 기 densified): event_villain template 0/10 유지 확인
- Block 41-70 (미 densified): solution template 30/30 유지 확인

## 2. Template Elimination

| Template | Before (Block 11-40) | After |
|----------|---------------------|-------|
| event_villain "주도권을 넓히기 전에" | 30/30 | **0/30** |
| solution "자신에게 유리한 순서로 재배치" | 30/30 | **0/30** |
| stakes "쪽으로 넘어간다" | 30/30 | **0/30** |

**100% 템플릿 제거 완료.**

## 3. Quality Metrics

### Content Length

| Field | Before avg | Before stdev | After avg | After stdev |
|-------|-----------|-------------|-----------|-------------|
| context | 131 | 12 | 266 | **18** |
| solution | 159 | 10 | 236 | **18** |
| event_villain | 67 | 3 | 137 | **17** |

### Arc 1 vs Arc 2-4 Comparison

| Metric | Arc 1 | Arc 2-4 | Consistent? |
|--------|-------|---------|-------------|
| Template residual | 0/10 | 0/30 | YES |
| Context avg | 228 | 266 | YES (Arc 2-4 slightly longer) |
| Context stdev | 36 | 18 | Arc 2-4 more uniform — acceptable |
| regression_hint | 10/10 | 30/30 | YES |
| execution_doctrine unique | 10 | 30 | YES |
| weakness_exploited unique | 10 | 30 | YES |

### New Fields Added

| Field | Before | After |
|-------|--------|-------|
| regression_hint | 0/30 | **30/30** |
| execution_doctrine variation | 1종 반복 | **30종 unique** |
| weakness_exploited variation | ~3종 반복 | **30종 unique** |
| Dialogue markers | 0/30 | **30/30** |

## 4. Arc-Specific Quality

### Arc 2: 바다 위의 장부 (Block 11-20, 1910~1914)

시대 질감: 로테르담 조선소, 발틱거래소, Lloyd's, 앤트워프 재보험, 1차대전 개전 패닉
- 핵심 대결: 이강윤 vs 에드워드 블레이크 (영국 해운 재벌)
- setback: Block 15 (모라토리엄 → 88→76억) — 전시 유동성 위기
- 자본: 36억 → 240억 (6.7x)

### Arc 3: 총보다 증권이 오래 간다 (Block 21-30, 1918~1924)

시대 질감: 전후 매각장, 해운 붐→붕괴, 취리히 금융 구축, 상하이 조계, 조선은행 부실
- 핵심 전환: 유럽 해운→식민지 금융으로 축 이동
- setback: Block 25 (운임 붕괴 → 426→386억)
- 자본: 240억 → 840억 (3.5x)

### Arc 4: 총독부의 등기부를 사들이다 (Block 31-40, 1925~1928)

시대 질감: 경성 상사회관, 토지대장 열람실, 법원 게시판, 총독부 도면실, 경성역 창고
- 핵심 대결: 이강윤 vs 구도 겐이치 (총독부 경제국)
- setback: Block 35 (철도 예정선 → 1190→1140억) — 구도의 반격
- 자본: 840억 → 1,960억 (2.3x)

## 5. Suspicion Escalation

Arc 1 (Block 1-10): low×5 → medium×5
Arc 2 (Block 11-20): low→medium 상승, high 첫 등장
Arc 3 (Block 21-30): medium→high 지배, very high 등장
Arc 4 (Block 31-40): medium→very high 재상승

의심 누적이 아크를 따라 자연스럽게 상승.

## 6. Verdict

**PASS — Arc 2-4 densification 완료, 방법론 일관 유지.**

- 템플릿 100% 제거 (0/30)
- regression_hint 30/30 추가
- execution_doctrine 30종 unique
- weakness_exploited 30종 unique
- 대화 마커 30/30
- spine 100% 보존
- Block 1-10 및 41-70 무변경 확인
- 아크별 시대 질감 유지 (1910s 해운, 1914-18 전시, 1920s 식민지)

**Arc 5-7 진행 가능.**

---

```text
work_id: fallen_prince_buys_joseon
current_stage: audit_or_repair
finished_unit: TR densification Arc 2-4
changed_files: treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json, docs/2026-03-27/fallen-prince-tr-densification-arc2-4-report.md
next_unit: TR densification Arc 5-7 (Block 41-70)
stop_reason: Arc 2-4 passed — template eliminated, sceneability restored, spine preserved, methodology consistent with Arc 1
```
