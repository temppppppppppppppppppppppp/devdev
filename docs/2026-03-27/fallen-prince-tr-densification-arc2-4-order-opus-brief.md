# Fallen Prince TR Densification Arc 2-4 — Order-OPUS Brief

Date: 2026-03-27
Audience: OPUS acting as the order/coordinator
Target work_id: `fallen_prince_buys_joseon`
Upstream: Arc 1 PASS, guard-alignment PASS

## 1. What You Are

You are the coordinator OPUS for Arc 2-4 densification (Block 11-40, 30 blocks).

Your job is:
- keep the run bounded to Block 11-40
- enforce guard-alignment: investment-primary + alt_history-overlay
- enforce Arc 1 quality floor (template 0%, stdev 30+, regression_hint 100%, dialogue 90%+)
- spine preservation is absolute
- return coherent Arc 5-7 readiness verdict

## 2. Fixed Scope

This run is only:
- `spine-preserving TR densification, Arc 2-4 (Block 11-40)`

Do not touch:
- Block 1-10 (already densified)
- Block 41-70 (next run)

## 3. Hard Constraint

One work_id, one final-writing owner. Parallel prose drafting allowed IF no two workers edit the same block range. Only coordinator merges into the single TR file.

## 4. Recommended Sub-OPUS Layout

### OPUS-Order (You)

Own:
- orchestration, block assignment
- guard-alignment + quality floor enforcement
- final TR merge (single writer)
- Arc 5-7 readiness verdict + report

### Sub-OPUS-G: Arc 2 Drafter (Block 11-20)

Task:
- densify Block 11-20 prose
- Arc 2 시대 질감: 1910~1914 합방 직후 해운, NYK/OSK 카르텔, 인천·부산 항로
- return JSON fragment, DO NOT write TR

### Sub-OPUS-H: Arc 3 Drafter (Block 21-30)

Task:
- densify Block 21-30 prose
- Arc 3 시대 질감: 1914~1918 1차대전, 잠수함전, 전시 보험, 전쟁특수
- return JSON fragment, DO NOT write TR

### Sub-OPUS-I: Arc 4 Drafter (Block 31-40)

Task:
- densify Block 31-40 prose
- Arc 4 시대 질감: 1920s 전후 불황, 산미증식, 토지/철도, 조선은행
- return JSON fragment, DO NOT write TR

### Sub-OPUS-J: Quality Validator

Read-only (runs after G+H+I return):
- per-block template check, context stdev, regression_hint, dialogue, sensory cues
- spine diff check (only prose fields changed)
- guard-alignment compliance (investment + overlay per block)
- Arc 1 parity check
- return per-arc + aggregate verdict

## 5. Parallelism Rule

Phase 1 (parallel):
- `G(Arc 2) || H(Arc 3) || I(Arc 4)`

Phase 2 (sequential, after G+H+I):
- Coordinator merges drafts into TR
- `J(quality validation)` runs on merged result

Phase 3 (sequential, after J):
- Coordinator writes final report

## 6. What Order-OPUS Must Watch

- spine mutation → stop
- template signature residue ("문서를 자신에게 유리한 순서로 재배치", "쪽으로 넘어간다") → flag
- modern business prose without period texture → flag
- period drama without financial engine → flag
- Block 1-10 or Block 41-70 touched → stop
- guard-alignment re-litigation → stop
- 5+ blocks below Arc 1 quality floor → pause and recalibrate

## 7. Guard-Alignment Operating Sentence

> `fallen_prince_buys_joseon`의 primary runtime guard는 `investment`다. `alt_history`는 mandatory overlay contract.

Every block must pass both:
- **investment test**: financial mechanism, capital logic, or bottleneck control foregrounded?
- **overlay test**: period institutions, historical events, era-specific texture embedded?

## 8. Files To Force Into Context

- `docs/2026-03-27/opus-fallen-prince-tr-densification-arc2-4-order.md`
- `docs/2026-03-27/fallen-prince-tr-densification-arc2-4-opus-context-memo.md`
- `docs/2026-03-27/fallen-prince-guard-alignment-note.md`
- `docs/2026-03-27/fallen-prince-tr-densification-arc1-report.md`
- `docs/2026-03-27/fallen-prince-tr-static-quality-audit.md`
- `treatments/_quarantine/05_fallen_prince_buys_joseon_tr_block_070_draft.json`
- `bible/_quarantine/05_fallen_prince_buys_joseon_bi.json`
- `treatments/preprocess/fallen_prince_buys_joseon/source_manifest.json`

## 9. Worker Prompt Snippets

### Prompt G

```text
너는 Sub-OPUS-G다. `fallen_prince_buys_joseon` TR Block 11-20 (Arc 2: 바다 위의 장부, 1910~1914) prose densify. spine 보존, 템플릿 제거, regression_hint/execution_doctrine/weakness_exploited 추가. guard: investment-primary + alt_history-overlay. 1910 합방 직후 해운 질감 필수. JSON fragment 반환, TR 직접 수정 금지.
```

### Prompt H

```text
너는 Sub-OPUS-H다. `fallen_prince_buys_joseon` TR Block 21-30 (Arc 3: 전쟁이 낳은 화폐, 1914~1918) prose densify. spine 보존, 템플릿 제거, regression_hint/execution_doctrine/weakness_exploited 추가. guard: investment-primary + alt_history-overlay. 1차대전 전시 경제 질감 필수. JSON fragment 반환, TR 직접 수정 금지.
```

### Prompt I

```text
너는 Sub-OPUS-I다. `fallen_prince_buys_joseon` TR Block 31-40 (Arc 4: 등기부의 주인, 1920s) prose densify. spine 보존, 템플릿 제거, regression_hint/execution_doctrine/weakness_exploited 추가. guard: investment-primary + alt_history-overlay. 1920s 전후 불황/토지/철도 질감 필수. JSON fragment 반환, TR 직접 수정 금지.
```

### Prompt J

```text
너는 read-only Sub-OPUS-J다. Block 11-40 densification 결과 검증. Arc 1 결과(template 0/10, stdev 36, 대화 10/10, regression_hint 10/10)를 quality floor로. 아크별 template 잔존/stdev/sceneability/regression_hint/dialogue/sensory 확인. spine 보존 diff 확인. guard-alignment 준수 확인. 아크별 + 전체 verdict 반환. 수정 금지.
```

## 10. Minimal Prompt

```text
너는 이번 런의 order-OPUS다. `docs/2026-03-27/opus-fallen-prince-tr-densification-arc2-4-order.md`와 `docs/2026-03-27/fallen-prince-tr-densification-arc2-4-opus-context-memo.md`, `docs/2026-03-27/fallen-prince-tr-densification-arc2-4-order-opus-brief.md`를 UTF-8로 읽고, `fallen_prince_buys_joseon` TR의 Arc 2-4 (Block 11-40) spine-preserving densification을 수행하라. guard binding은 `fallen-prince-guard-alignment-note.md`를 따르고, Arc 1 결과를 quality floor로 삼아라. 같은 work_id 안에서는 단 한 명만 최종 TR 파일을 쓰게 하고, prose 드래프팅은 `G(Arc 2) || H(Arc 3) || I(Arc 4)`로 병렬화하고, 검증은 `J`로 후행하라.
```

Confidence:
- 97% this is the correct delegation shape for 30-block batch densification
