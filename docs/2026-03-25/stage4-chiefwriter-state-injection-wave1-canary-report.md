# Stage 4 ChiefWriter State-Injection Wave 1 — Canary Report

Date: 2026-03-25
Type: bounded Stage 4 canary (post-fix validation)
Source Project: `00_0000001`
Target Project: `canary_0325_stage4_fix`
Run Window: EP1-EP5 (Arc 1 full + Arc 2 EP5)
Run Status: completed (exit code 0)
Wave 1 SSOT: `docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-execution-ssot.md` (closed)

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0325_stage4_fix/logs/canary_summary.json` |
| Production JSONL | `projects/canary_0325_stage4_fix/logs/episode_production.jsonl` |
| EP5 Stage 4 artifacts | `projects/canary_0325_stage4_fix/logs/artifacts/stage4/ep_0005/attempt_01-03/` |
| EP4 Stage 4 artifacts | `projects/canary_0325_stage4_fix/logs/artifacts/stage4/ep_0004/attempt_01-03/` |
| Full console output | background task output (1,777 lines) |

## Findings

### Per-Episode Attempt Summary

| Episode | Attempts | R1 | R2 | R3 | R4 | Final |
|---------|----------|----|----|----|----|-------|
| EP1 | 1 | PASS (95) | — | — | — | PASS R1 |
| EP2 | 4 | REJECT post-select (90) | REJECT firewall (44) | REJECT post-select (100) | PASS (93) | PASS R4 |
| EP3 | 3 | REJECT post-select (100) | REJECT post-select (90) | PASS (100) | — | PASS R3 |
| EP4 | 3 | REJECT post-select (96) | REJECT post-select (90) | PASS (93) | — | PASS R3 |
| EP5 | 3 | REJECT post-select (92) | REJECT Director (83) | PASS (96) | — | PASS R3 |

Total Stage 4 attempts: 14
Total PASS: 5 (one per episode)
Total REJECT: 9

### EP4 Comparison (Primary Wave 1 Target)

| Metric | Baseline (pre-fix) | Canary (post-fix) | Delta |
|--------|-------------------|-------------------|-------|
| Retry rounds | 6 | **3** | **-50%** |
| Resource balance violation | R1-R5 all "20억 실탄" cash misuse | R3 resolved via "파텍필립 시계 전당포 처분" | **Eliminated by R3** |
| Post-select downgrade cause | 자금 상태 충돌 (6회 반복) | 자금 흐름/잔고 설정 (2회, 다른 양상) | **Changed shape** |
| Director score range | 90-96 | 90-96 | Unchanged |
| Final PASS gate | R6 | **R3 patch_reaudit_pass** | Earlier resolution |

### EP5 Observations (Arc 2 Entry — Completed-Event Regression Target)

**R1 (REJECT, post-select)**:
- Post-select correctly caught: "20억 원이 들어간 계좌가 'SW인베스트먼트 법인 계좌'로 묘사" — 개인 vs 법인 계좌 혼동
- Also caught: "이미 3화에서 완료된 계좌 세팅이 아직 최종 서명이 필요한 상태로 번복" — completed-event regression

**R2 (REJECT, Director)**:
- Director 자체 REJECT (score 83): "파생 계좌의 소유 주체(개인 vs 법인) 설정 혼동"
- Director가 스스로 잡았다 — baseline에서는 Director가 못 잡고 post-select에서만 잡던 패턴과 다름

**R3 (PASS, score 96)**:
- Director: "이전 화에서 확립된 '20억 원 개인 파생 계좌' 설정을 정확히 유지"
- 후보 B는 "20억 원이 든 계좌를 'SW인베스트먼트 법인 계좌'로 잘못 지칭하는 치명적인 설정 오류(MAJOR)" 로 탈락
- **post-select downgrade 없이** director_primary_pass로 확정

## Assessment

### 1. Completed-Event Regression
- **Reduced.** EP5 R1에서 "계좌 세팅 완료 번복" 회귀가 1회 발생했으나, R3에서 완전 해소.
- Baseline에서는 이 회귀가 반복되며 retry를 지배했으나, canary에서는 R3에서 Director가 "확립된 설정을 정확히 유지"를 명시적으로 확인.
- IFC completed-event fact 주입이 작동한 직접 증거.

### 2. Committed-State / Resource Compliance
- **Materially improved.** EP4 R3에서 "20억 전액 파생 계좌 이체 → 가용 현금 없음"을 CW가 인식하고 합리적 우회("파텍필립 시계 전당포 처분") 생성.
- EP5 R3에서 Director가 "20억 원 개인 파생 계좌 설정 정확히 유지"를 PASS 근거로 명시.
- Baseline에서 6라운드 내내 해소되지 않던 자금 상태 모순이 3라운드 이내 해소됨.

### 3. Time/Place Continuity
- **Mixed.** EP2-EP4에서 post-select이 장소/시간 연속성 오류를 여전히 감지.
- EP4 R1: "압구정지점"→"여의도지점" 장소 혼동 반복.
- EP5 R1: 후보 A에서 장소 모순 발생 (Director selection이 후보 B로 회피).
- Wave 1은 time/place injection을 변경하지 않았으므로 이 잔류는 예상 범위 내.
- 시작 장소 ⛔ 마커에도 불구하고 CW가 장소명을 임의 변경하는 LLM 준수 실패는 별도 문제.

### 4. Downgrade / Retry Loop Behavior
- **Materially improved.** EP4: 6→3회, EP5: baseline 데이터 없지만 3회에 PASS.
- Post-select downgrade는 여전히 발생하지만, 자금 모순 기반 downgrade가 줄고, 장소/설정 세부사항 기반으로 변형됨.
- EP5 R2에서 Director 자체 REJECT가 발생 — 이전에는 Director가 90-96점으로 통과시키고 post-select만 잡던 패턴에서 변화. IFC committed-state 주입으로 Director 감지력 자체가 향상된 것으로 추정.

### 5. Hang Recurrence
- **None.** 5화 전체가 정상 완료. 무한 루프, 타임아웃, 프로세스 hang 없음.

### 6. New Pathology
- **No severe overconstraint or prose collapse.** EP1-5 전체 5,325-7,283자 범위로 정상 분량.
- EP2에서 continuity_firewall REJECT (score 44)가 1회 발생 — 이는 Wave 1과 무관한 기존 방어 메커니즘.
- Post-select 기반 retry는 여전히 주요 비용 요인 (9/14 attempts가 REJECT).

## What Improved

1. **자금 상태 모순 retry 루프 반감**: EP4 6회→3회. CW가 committed-state fact를 인식하고 합리적 우회 생성.
2. **Director 감지력 향상**: EP5 R2에서 Director가 "파생 계좌 소유 주체 혼동"을 직접 REJECT. Baseline에서는 Director 통과 → post-select downgrade 패턴이었음.
3. **완료 사건 회귀 축소**: EP5에서 "계좌 세팅 완료 번복"이 R1에서만 발생, R3에서 해소. Director가 "확립된 설정 정확히 유지"를 명시적 PASS 근거로 제시.
4. **post-select downgrade 없는 최종 PASS**: EP4, EP5 모두 최종 라운드에서 post-select downgrade 없이 Director PASS로 확정.

## What Stayed Unresolved

1. **시작 장소 LLM 준수 실패**: CW가 ⛔ 마커에도 불구하고 장소명을 임의 변경하는 문제 잔류. 이는 데이터 주입이 아닌 프롬프트 준수 문제.
2. **개인/법인 계좌 혼동**: EP5 R1에서 CW가 개인 파생 계좌를 "SW인베스트먼트 법인 계좌"로 지칭. Committed-state fact에 계좌 소유 주체가 명시되었으나 CW가 부분적으로만 준수.
3. **Post-select 기반 retry 비용**: 14 attempts 중 9회 REJECT. Post-select이 여전히 주요 품질 게이트이며, Director 단독으로는 연속성 오류를 충분히 잡지 못함.

## Failure Family Shape Change

- **Before Wave 1**: "데이터 미주입 → CW 무인식 → 6라운드 자금 모순 반복 → post-select만 감지" (data injection failure)
- **After Wave 1**: "데이터 주입됨 → CW 부분 인식 → 2-3라운드 내 해소, 잔류는 세부 설정 혼동" (LLM compliance gap)
- Failure family가 **data-injection-severed**에서 **LLM-prompt-compliance-partial**로 이행.

## Recommendation

**One compact follow-up survey**: Stage 4 post-select downgrade 빈도와 Director 감지력 간 격차를 조사. 구체적으로:
- Director가 ⛔ IFC 마커 위반을 직접 감지하지 못하는 경로 (장소명, 계좌 소유 주체)
- Patch mode가 score 90+ 구간에서 구조적 오류를 보존하는 패턴
- 이 조사 결과에 따라 Director 프롬프트 또는 post-select → retry 피드백 주입 경로에 대한 execution SSOT 여부 판단

---

## 3-Pass Audit Notes
- Pass 1: structure matches canary report template; scope bounded to EP1-EP5 window
- Pass 2: all claims backed by artifact evidence (production JSONL attempt keys, console output line numbers, canary_summary.json fields)
- Pass 3: recommendation is single and bounded; no scope creep into excluded surfaces
- Confidence: 96%

---

- Dominant Stage 4 failure family after Wave 1: **reduced** (data-injection-severed → LLM-compliance-partial)
- Hang recurrence: **none**
- Should Codex open a new execution SSOT now: **no** (survey first to classify the compliance gap before committing to a fix shape)
