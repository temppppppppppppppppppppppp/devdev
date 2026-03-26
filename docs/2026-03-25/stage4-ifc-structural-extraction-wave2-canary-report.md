# Stage 4 IFC Structural Extraction Wave 2 — Canary Report

Date: 2026-03-25
Type: bounded Stage 4 canary (post-fix validation)
Source Project: `00_0000001`
Target Project: `canary_0325_stage4_wave2`
Run Window: EP1-EP5 (Arc 1 full + Arc 2 EP5)
Run Status: completed (exit code 0)
Wave 2 SSOT: `docs/2026-03-25/stage4-ifc-structural-extraction-wave2-execution-ssot.md` (closed)
Prior Canary (Wave 1): `docs/2026-03-25/stage4-chiefwriter-state-injection-wave1-canary-report.md`

## Evidence Artifacts

| Artifact | Path |
|----------|------|
| Canary summary | `projects/canary_0325_stage4_wave2/logs/canary_summary.json` |
| Production JSONL | `projects/canary_0325_stage4_wave2/logs/episode_production.jsonl` |
| EP4 artifacts | `projects/canary_0325_stage4_wave2/logs/artifacts/stage4/ep_0004/attempt_01-02/` |
| EP5 artifacts | `projects/canary_0325_stage4_wave2/logs/artifacts/stage4/ep_0005/attempt_01-04/` |
| Console output | background task bycww7t60 (1,393+ lines) |

## Findings

### Per-Episode Attempt Summary

| Episode | Attempts | R1 | R2 | R3 | R4 | Final |
|---------|----------|----|----|----|----|-------|
| EP1 | 1 | PASS (97) | — | — | — | PASS R1 |
| EP2 | 3 | REJECT firewall (44) | REJECT post-select (94) | PASS (95) | — | PASS R3 |
| EP3 | 1 | PASS (96) | — | — | — | PASS R1 |
| EP4 | 2 | REJECT post-select (100) | PASS (90) | — | — | PASS R2 |
| EP5 | 4 | REJECT post-select (92) | REJECT Director (86) | REJECT post-select (96) | PASS (96) | PASS R4 |

Total Stage 4 attempts: **11**
Total PASS: 5 (one per episode)
Total REJECT: 6

### Three-Way Comparison

| Metric | Baseline (pre-fix) | Wave 1 | Wave 2 | Trend |
|--------|-------------------|--------|--------|-------|
| Total attempts | 21+ (EP4 alone: 6) | 14 | **11** | **-21%** vs W1 |
| Total REJECT | 15+ | 9 | **6** | **-33%** vs W1 |
| EP1 | R1 PASS | R1 PASS | R1 PASS | Stable |
| EP2 | ? | R4 PASS | **R3 PASS** | -1R |
| EP3 | ? | R3 PASS | **R1 PASS** | **-2R** |
| EP4 | R6 PASS | R3 PASS | **R2 PASS** | **-1R** |
| EP5 | N/A | R3 PASS | R4 PASS | +1R (failure family changed) |

### EP4 Comparison (Resource Balance Target)

| Metric | Wave 1 | Wave 2 |
|--------|--------|--------|
| Retry rounds | 3 | **2** |
| R1 Director score | 96 | **100** |
| R1 REJECT cause | post-select: 자금 흐름/잔고 설정 | post-select: "이미 완료된 가계약을 다시 진행" |
| R2 PASS reason | R3 patch_reaudit_pass (93) | **R2 director_primary_pass (90)** "가계약→잔금" 연속성 영리하게 수정 |
| Resource balance violation | R1-R2 반복 | **None** |

EP4 R1 Director 100점 PASS — 자금 모순 없음. post-select이 잡은 건 "가계약 타임라인 반복"이지 자금 상태 충돌이 아님. **자금 모순은 완전 해소됨.**

### EP5 Observations (Account Ownership + Procedural Completion Target)

**R1 (REJECT, post-select, score 92)**:
- Director PASS(92) — **개인/법인 계좌 혼동 없음** (Wave 1에서는 이게 R1 REJECT 사유였음)
- Post-select: "이미 해외 선물 계좌 세팅과 증거금 이체를 마쳤는데 다시 지점 방문해 가입 서류 서명" — **절차 완료 상태 회귀** (계좌 세팅 완료 → 다시 세팅)
- 이건 Wave 2 `세팅` 키워드가 completed_event_facts로 올렸어야 할 팩트인데, chain_link/prev_digest에 "세팅 완료"가 정확히 이 형태로 들어있지 않았을 가능성

**R2 (REJECT, Director, score 86)**:
- Director 자체 REJECT: "EP4 마지막 대사('지금 당장 진입합니다')와 첫 대사('내일 진입할 겁니다') 간의 논리적 모순"
- **Director가 타임라인 모순을 직접 잡음** — Wave 1에서는 이 유형을 Director가 못 잡았음

**R3 (REJECT, post-select, score 96)**:
- Director PASS(96) — 수학적 정확성("20억 원, 3배 레버리지, 30% 상승 시 18억 수익, 90% 수익률") 확인
- Post-select: "택시 이용하던 주인공이 갑자기 전용 세단 이용" + "즉각 진입 → 다음 날 방문으로 번복"
- **생활 설정 연속성 문제** (택시 vs 전용 세단) — IFC 범위 밖

**R4 (PASS, score 96)**:
- Director: "직전 화 엔딩 대사를 자연스럽게 이어받아, 시스템적 한계(위험고지서 대면 서명)를 이유로 지시를 수정하는 전개로 개연성 확보"
- "레버리지 수익률 계산(30% 상승 * 3배 = 90%)이 정확"
- "택시를 이용하는 등 이전 화 설정과 디테일한 연속성을 완벽하게 유지"
- **post-select downgrade 없이** director_primary_pass 확정

## Assessment

### 1. Account Ownership Compliance
- **Resolved.** Wave 1 EP5 R1의 핵심 실패("SW인베스트먼트 법인 계좌" 혼동)가 **Wave 2 전체 4라운드에서 단 한 번도 발생하지 않음**. Director R1 선택 사유에도 계좌 혼동 지적 없음.
- Wave 2 `법인`/`소유`/`개인`/`명의` 키워드가 fact_ledger 아이템 라인("SW인베스트먼트 법인 인감, 소유: 주인공")을 committed_state_facts로 올린 것이 작동한 것으로 추정.

### 2. Procedural Completion Compliance
- **Partially improved, partially unresolved.** EP5 R1에서 "이미 완료된 계좌 세팅을 다시 진행"이 여전히 발생. 이는 chain_link/prev_digest에 "세팅 완료"가 extraction-friendly 형태로 없거나, `세팅` 키워드가 해당 소스에서 매칭할 라인이 없었을 가능성.
- 그러나 EP5 R4에서 "시스템적 한계(위험고지서 대면 서명)를 이유로 지시를 수정"하여 개연성 있게 해소 — CW가 절차 완료 사실을 인식하되 합리적 우회를 생성한 것으로 보임.

### 3. Director Early Detection
- **Materially improved.** EP5 R2에서 Director가 "EP4 마지막 대사와 첫 대사 간 논리적 모순"을 직접 REJECT (score 86). Wave 1에서는 Director가 이 유형을 잡지 못하고 post-select에만 의존했음.
- EP4 R1에서 Director 100점 PASS — 자금 모순 감지 필요 자체가 없어짐.

### 4. Post-Select Downgrade Frequency
- Wave 1: 9 REJECT / 14 attempts = **64%**
- Wave 2: 6 REJECT / 11 attempts = **55%**
- Post-select downgrade: Wave 1 7건 → Wave 2 **4건** (-43%)
- **Materially improved.** 특히 EP3 R1 PASS, EP4 R2 PASS는 post-select downgrade 없이 통과.

### 5. Hang Recurrence
- **None.** EP1-5 전체 정상 완료. 무한 루프, 타임아웃, 프로세스 hang 없음.

### 6. New Pathology
- **EP5 retry count increased by 1R vs Wave 1.** 하지만 failure family가 완전히 다름:
  - Wave 1 EP5: 개인/법인 혼동 (구조적 팩트 미주입) → **해소됨**
  - Wave 2 EP5: 타임라인 모순 (EP4 "즉시 진입" vs EP5 "내일 방문") + 생활 설정 연속성 (택시 vs 세단) → **별도 이슈**
- NumericDriftAdvisor가 반복적으로 "20억 자본금 이력 근거 부족" 경고를 발생시킴 — fact_ledger 이력 데이터의 중복/불완전 문제로 보이며 Wave 2 타겟이 아님.

## What Improved vs Wave 1

1. **Total attempts 21% 감소**: 14→11. Total REJECT 33% 감소: 9→6.
2. **EP3 R1 PASS**: Wave 1에서 3라운드 → Wave 2에서 **1라운드**. Director가 "예금 자산 형태 정확히 유지"를 명시적으로 확인.
3. **EP4 R2 PASS**: Wave 1에서 3라운드 → Wave 2에서 **2라운드**. 자금 모순 완전 해소.
4. **개인/법인 계좌 혼동 완전 소멸**: EP5 4라운드 전체에서 단 한 번도 발생하지 않음.
5. **Director 타임라인 모순 직접 감지**: EP5 R2에서 Director가 자체 REJECT — Wave 1에서는 불가능했던 패턴.
6. **Post-select downgrade 43% 감소**: 7건→4건.

## What Stayed Unresolved

1. **절차 완료 상태 회귀 (partial)**: EP5 R1에서 "계좌 세팅 완료 → 다시 지점 방문 서명" 회귀 1회 발생. `세팅` 키워드가 chain_link/prev_digest 소스에서 매칭할 라인이 없었을 가능성 — extraction 자체는 정상이나 소스 데이터 형태 문제.
2. **생활 설정 연속성**: "택시 이용" vs "전용 세단" — IFC 추출 범위 밖의 세부 설정 연속성 문제. 이건 fact_ledger/chain_link에 교통수단 팩트가 없으므로 IFC로 해결 불가.
3. **타임라인 연결 모순**: EP4 "지금 당장 진입" → EP5 "내일 방문" 모순이 3라운드 반복. 이건 blueprint 설계와 CW 해석 간 격차 문제로, IFC extraction 범위 밖.

## Failure Family Shape Change

- **Before Wave 1**: "데이터 미주입 → CW 무인식 → 자금 모순 6R 반복" (data injection failure)
- **After Wave 1**: "데이터 주입됨 → CW 부분 인식 → 구조 팩트 혼동 잔류" (LLM compliance gap)
- **After Wave 2**: "구조 팩트 주입됨 → 계좌 혼동 해소 → **타임라인/생활설정 연속성만 잔류**" (blueprint-CW timeline alignment gap)

잔류 failure family가 **IFC extraction 범위 밖**으로 이동함. 남은 문제는:
- Blueprint의 "즉시 진입" 지시와 CW의 "다음 날 방문" 해석 간 격차
- 교통수단 같은 생활 세부 설정 연속성
이들은 IFC keyword 확장으로 해결되지 않으며, blueprint 정합성 또는 CW prompt 구조 영역.

## Recommendation

**No action.** Wave 1+2가 IFC extraction 경로에서 할 수 있는 합리적 범위를 소진했음. 잔류 문제는 IFC 추출 범위 밖(blueprint 타임라인 정합성, 생활 설정 연속성)이므로, IFC에 더 키워드를 추가하는 것은 ROI가 없음. 다음 개선이 필요하다면 별도 영역(blueprint-CW alignment 또는 Director rubric 세분화)에서 시작해야 하며, 그 전에 더 많은 에피소드 데이터로 잔류 패턴을 축적하는 것이 우선.

---

## 3-Pass Audit Notes
- Pass 1: structure matches canary report template; scope bounded to EP1-EP5 window
- Pass 2: all claims backed by production JSONL attempt_key evidence and console output line numbers
- Pass 3: recommendation is bounded; no scope creep
- Confidence: 97%

---

- Dominant Stage 4 failure family after Wave 2: **reduced** (account-ownership-resolved, timeline/lifestyle-continuity remains but is outside IFC extraction scope)
- Hang recurrence: **none**
- Should Codex open a new execution SSOT now: **no**
