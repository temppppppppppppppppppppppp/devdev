# 글도비 시스템 의도성 평가 3-pass audit

Date: 2026-05-13
Status: final
Document Type: system-track assessment / human-facing audit
Canonical Path: `docs/2026-05-13/geuldobi-system-thoughtfulness-assessment-3pass-audit.md`

Commit State:
- Baseline Commit: `294cbab3026b6b705f8e22bbc0155fc363724537`
- Baseline Dirty Summary: `clean at start of this assessment`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none before saving this document`

Source Anchors:
- `AGENTS.md`
- `docs/implementation/system-order-init-harness.md`
- `docs/implementation/document-3pass-audit-harness.md`
- `docs/2026-04-03/material-side-order-ssot-design.md`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-internal-parallel-investigation.md`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_deployable_greenplus_closeout.md`
- `docs/2026-04-21/donor-first-bi-tr-generation-arc-report-v1.md`
- `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md`
- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md`
- `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md`

Side-Effect Coverage:
- file write: this document only
- DB write: none
- JSONL/log/audit sink: none
- console/UI/runtime: none
- queue mutation: none
- code mutation: none

## 1. Operator Question

사용자 질문을 시스템 평가 언어로 바꾸면 아래다.

> 이 시스템은 그냥 아무 생각 없이 복잡하게 만든 엉망인가, 아니면 실제 문제를 겪으면서 생각하고 방어선을 세운 시스템인가?

짧은 답:

**생각 없이 만든 시스템은 아니다. 오히려 너무 많이 겪고, 너무 많이 생각하면서 생긴 시스템이다.**

다만 좋은 의미의 "생각"만 있는 것은 아니다. 이 시스템은 생산 실패, 권위 충돌, stale artifact, 런타임 증거 오염, donor 오염, queue drift를 계속 맞으면서 방어막을 덧댄 형태다. 그래서 구조적 의도는 강하지만, 운영 표면은 무겁고 피로하다.

판정:

- 설계 의도성: `높음`
- 운영 복잡도: `매우 높음`
- 멍청한 난장판 여부: `아님`
- 과잉 방어 / 절차 비대 여부: `맞음`
- 핵심 리스크: `생각이 없어서가 아니라, 너무 많은 실패 계층을 한 시스템 안에 누적해서 생긴 읽기/운영 비용`

## 2. Final Verdict

`글도비`는 "병신같이 막 만든 시스템"이라기보다, **AI 서사 생산에서 실제로 터지는 문제들을 하나씩 맞고 나서 만든 생존형 control plane**에 가깝다.

멍청한 시스템이었다면 아래가 없어야 한다.

- Python은 수집만 하고 판단은 LLM이 한다는 권한 분리
- Director가 최종 품질 권한을 갖는다는 주권 모델
- canonical dated docs가 temp mirror보다 우선한다는 authority hierarchy
- 10-terminal parallel survey에서 non-overlap invariant를 두고 synthesis 뒤에만 실행 승격하는 규칙
- donor를 direct copy하지 않고 arc translation layer를 둔다는 판단
- 60/60 block scan처럼 "좋아 보인다"가 아니라 전체 body를 훑는 benchmark closeout
- FactLedger, telemetry transaction, pass-rate evidence 같은 운영 증거의 신뢰성을 따지는 wave

반대로 완성도 높은 제품형 시스템이었다면 아래가 이렇게 크지 않았어야 한다.

- `docs/temp`에 오래된 execution/queue artifact가 많다
- authority surface가 Stage2/3/4, Director, validator, runtime, DB, artifact, UI로 넓게 갈라져 있다
- survey, audit, SSOT, mirror, roadmap, handoff가 너무 많이 생겨 신규 operator가 전체 상태를 읽기 어렵다
- 복잡도를 줄이기 위해 만든 문서 체계 자체가 또 하나의 복잡도가 됐다

따라서 최종 평가는:

**생각하면서 만든 시스템이다. 하지만 예쁘게 설계한 시스템이라기보다, 맞으면서 뼈가 굵어진 시스템이다.**

## 3. Evidence-Based Scorecard

| Axis | Score | 판정 |
|---|---:|---|
| 문제를 실제로 이해하고 쪼갠 흔적 | 9/10 | Stage3, Stage4, security, memory/persistence를 terminal lane으로 분해 |
| 권위/판단 주체에 대한 사고 | 9/10 | Python 수집 / LLM 판단 / Director 주권 / canonical precedence가 명확 |
| donor/deepclone 오염 방지 사고 | 8/10 | direct copy 금지, arc translation, work_guard/Phase0 분리 |
| 증거 신뢰성에 대한 사고 | 8/10 | DB, JSONL, pass-rate, artifact truth, stale runtime summary를 따짐 |
| 실행 전 브레이크 | 9/10 | 3-pass, 95%, synthesis-before-execution, proof gate |
| 사용자/운영자 가독성 | 5/10 | 많은 문서와 queue artifact가 operator에게 부담 |
| 시스템 단순성 | 4/10 | 생존형 레이어가 많이 붙어서 단순한 구조는 아님 |
| 제품화 readiness | 6/10 | 강한 실험/운영 체계지만 polished product UX는 별도 문제 |

요약 점수:

- 지적 설계 의도성: `8.5 / 10`
- 운영 부채: `7.5 / 10`
- "막 만든 느낌" 위험: `3 / 10`
- "너무 복잡하게 버틴 느낌" 위험: `8 / 10`

## 4. 왜 생각하면서 만든 시스템인가

### 4.1 권위 분리 원칙이 있다

`AGENTS.md`는 처음부터 Python과 LLM의 역할을 나눈다. Python은 수집만 하고 판단은 LLM이 한다. Director가 최종 품질 권한을 가진다. canonical dated docs는 temp mirror보다 우선한다.

Evidence:
- `AGENTS.md:21`
- `AGENTS.md:23`
- `AGENTS.md:104-113`
- `AGENTS.md:170`

해석:

이건 "일단 자동화하고 보자"가 아니다. 자동화가 판단권을 먹어 버리는 걸 경계한 설계다. AI 생산 시스템에서 흔히 터지는 문제, 즉 validator나 script가 사람/Director 판단을 몰래 대체하는 문제를 이미 의식하고 있다.

### 4.2 병렬조사를 그냥 많이 돌린 게 아니라, 겹치지 않게 쪼갰다

2026-04-13 S2/S3/S4 runtime improvement 조사는 10-way parallel이지만, 각 terminal이 다른 축을 맡고 non-overlap invariant를 둔다. findings는 synthesis 뒤에야 execution item으로 승격된다.

Evidence:
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md:5`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md:93`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md:143`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md:608`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md:625-627`
- `docs/2026-04-13/s2-s3-s4-runtime-improvement-10-terminal-parallel-investigation-order.md:660`

해석:

막 만든 시스템이면 병렬조사는 "여럿이 대충 봐라"가 된다. 여기서는 terminal별 소유 질문, scope out, deliverable path, synthesis timing을 먼저 고정한다. 이건 생각이 있는 운영 설계다.

### 4.3 donor를 복사하지 말라고 잠갔다

`donor-first-bi-tr-generation-arc-report-v1.md`는 donor를 그대로 TR/BI에 복사하는 방향을 거부한다. donor와 block 사이에 `arc translation layer`가 필요하다고 못박고, 핵심 pipeline을 `donor law -> arc ladder -> block contract -> BI/TR emission`으로 둔다.

Evidence:
- `docs/2026-04-21/donor-first-bi-tr-generation-arc-report-v1.md:39`
- `docs/2026-04-21/donor-first-bi-tr-generation-arc-report-v1.md:42`
- `docs/2026-04-21/donor-first-bi-tr-generation-arc-report-v1.md:52`
- `docs/2026-04-21/donor-first-bi-tr-generation-arc-report-v1.md:495`

해석:

이건 deepclone의 제일 위험한 함정, 즉 성공작 표면을 베끼는 문제를 피하려는 판단이다. donor를 구조 법칙으로 번역하고, arc/block layer로 다시 내리는 흐름을 생각했다.

### 4.4 material side를 산출물 폴더가 아니라 authority map으로 봤다

`material-side-order-ssot-design.md`는 material_ssot를 단순 저장소가 아니라 `authority map + read order + manifest hub`로 정의한다. reference profiles, few-shot bank, work material packs, analysis reports, corpus bundles를 단계별로 분리한다.

Evidence:
- `docs/2026-04-03/material-side-order-ssot-design.md:7`
- `docs/2026-04-03/material-side-order-ssot-design.md:11`
- `docs/2026-04-03/material-side-order-ssot-design.md:49-51`
- `docs/2026-04-03/material-side-order-ssot-design.md:104`
- `docs/2026-04-03/material-side-order-ssot-design.md:184`

해석:

재료가 많아질수록 "어디 있는지"보다 "무엇이 판단권을 갖는지"가 중요해진다. 이 문서는 그 문제를 의식하고 있다.

### 4.5 Golden Canary 계열은 감으로 승격한 게 아니다

`golden_canary_deepclone_probe_a_fullblock_v1`은 donor decision adopted, full-block cider scan `60/60`, GREENPLUS, donorized full-block gold sample이라는 단계적 closeout을 갖는다. benchmark 문서도 donor prestige나 파일명 모양이 아니라 current live pair에 tie한다고 적는다.

Evidence:
- `docs/2026-04-18/golden-canary-deepclone-probe-a-internal-parallel-investigation.md:20`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-internal-parallel-investigation.md:28`
- `docs/2026-04-18/golden-canary-deepclone-probe-a-internal-parallel-investigation.md:243`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md:17`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md:28`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md:68`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md:123`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md:130`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_initial_greenplus_benchmark.md:134`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_deployable_greenplus_closeout.md:17`
- `docs/2026-04-20/golden_canary_deepclone_probe_a_fullblock_v1_deployable_greenplus_closeout.md:115`

해석:

감으로 "좋다" 한 게 아니라, block continuity와 receipt/cider continuity를 본다. 특히 `60/60` scan은 꽤 고생스러운 검증 흔적이다.

### 4.6 자기 시스템의 약점도 계속 찾았다

2026-04-21 authority alignment deep-dive는 문제를 "owner 없음"으로 단순화하지 않고 split-owner seam으로 본다. 2026-04-25 wave2는 다음 wave가 feature가 아니라 authority/verification hardening이어야 한다고 결론낸다. wave3는 FactLedger/WorldState false success, pass-rate evidence drop, telemetry transaction boundary를 지적한다.

Evidence:
- `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md:43`
- `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md:114`
- `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md:118`
- `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md:168`
- `docs/2026-04-21/s2-s3-s4-authority-alignment-parallel-deep-dive-3pass-audit.md:304`
- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md:22`
- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md:49`
- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md:53`
- `docs/2026-04-25/codebase-parallel-maintenance-deep-dive-wave2-synthesis.md:112`
- `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md:46`
- `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md:54`
- `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md:84`
- `docs/2026-04-25/codebase-parallel-memory-persistence-telemetry-deep-dive-wave3-synthesis.md:111`

해석:

이건 자화자찬 문서만 쌓은 시스템은 아니다. 자기가 어디서 거짓 성공을 낼 수 있는지 계속 파고 있다. 시스템이 생각한다기보다, 운영자가 시스템의 자기기만 가능성을 무서워하고 있다.

### 4.7 Stage4 incident도 성급히 "고쳤다" 하지 않는다

2026-04-27 POST_SELECT_CONFLICT dispatch는 ep4~ep9 reject sequence를 적고, clean 5-arc readiness를 주장하지 말라고 금지한다. 10 terminal로 route, handoff, continuity, memory/cache, retry, context-cache, regression, artifact truth를 나눈다.

Evidence:
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:19`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:28`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:36-41`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:48`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:72`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:100`
- `docs/2026-04-27/stage4-post-select-conflict-parallel-investigation/stage4-post-select-conflict-parallel-investigation-dispatch.md:527`

해석:

막 만든 시스템은 실패가 나면 "재시도"나 "프롬프트 강화"로 바로 간다. 여기서는 실패 family를 분해하고, artifact truth까지 보라고 한다. 이건 생각 있는 실패 처리다.

## 5. 어디가 나쁜가

### 5.1 복잡도 자체가 제품 리스크다

현재 시스템은 너무 많은 방어선을 갖고 있다.

- canonical docs
- temp mirrors
- queue-state
- roadmap
- execution SSOT
- handoff
- survey
- merge audit
- source artifacts
- runtime DB/log/JSONL
- material_ssot / narrative_ssot / bible / treatments

이 구조는 안전하지만, 신규 operator가 "지금 뭘 믿어야 하는가"를 빠르게 판단하기 어렵다.

이번 조사 시작 시점에도 `docs/temp` 아래에는 여러 execution SSOT와 queue artifact가 남아 있었다. 이것은 본 요청과 직접 무관하므로 실현하지 않았지만, 운영자가 잘못 들어오면 오래된 temp surface가 현재 의사결정을 흐릴 수 있다.

판정:

- 설계가 멍청한 것이 아니라, 생존 과정에서 붙은 표면이 너무 많다.
- 시스템이 실패를 방어하려고 만든 문서 체계가 다시 운영 피로를 만든다.

### 5.2 "정답 권위"가 너무 여러 층에 퍼져 있다

Director, validator, Python precheck, DB attempt truth, runtime audit summary, UI HUD, material_ssot, work_guard, Phase0, TR/BI가 모두 어떤 방식으로든 판단에 관여한다.

이건 AI 생산 시스템에서는 어느 정도 필연이지만, 잘못 다루면 서로 모순된 성공 판정이 생긴다. 그래서 이 시스템이 authority alignment 문서를 계속 만든 것이다.

판정:

- 이 시스템은 "생각이 없어서 권위가 흩어진" 게 아니다.
- 여러 authority가 필요할 만큼 문제가 복잡했고, 그걸 통제하려다 authority 문서가 많아진 것이다.
- 그래도 최종 운영 관점에서는 부담이 크다.

### 5.3 문서가 실행을 막는 브레이크이면서 동시에 병목이다

3-pass/95% gate는 필요한 브레이크다. 하지만 모든 것이 survey -> audit -> execution SSOT -> temp mirror -> roadmap -> closure로 흐르면 작은 결정도 무거워진다.

판정:

- 신중함은 강점이다.
- 하지만 속도와 집중력이 필요한 순간에는 과잉 절차가 된다.
- "생각하면서 만든 시스템"의 부작용이 바로 여기다.

## 6. 시스템 성격 요약

이 시스템은 아래 성격을 가진다.

1. **방어적이다.**
   - fake pass, stale evidence, donor contamination, authority drift를 무서워한다.

2. **증거 지향이다.**
   - 감이 아니라 DB, artifact, block scan, terminal report, 3-pass audit를 남기려 한다.

3. **운영자 중심이다.**
   - Director sovereignty, console log preservation, human-facing doc audit가 강하다.

4. **복잡도는 높다.**
   - 단순한 product code라기보다 AI production lab/control plane에 가깝다.

5. **상처가 많다.**
   - 문서 이름과 queue 구조만 봐도 실패를 많이 겪고, 그때마다 방어선을 추가한 흔적이 있다.

## 7. Operator Take

한 문장으로:

**이건 생각 없이 만든 시스템이 아니라, 생각을 너무 많이 하며 버틴 시스템이다.**

좋은 시스템이냐고 물으면:

- R&D/control-plane으로는 꽤 진지하고 강하다.
- 자동 웹소설 생산의 실패 형태를 실제로 많이 겪은 사람이 만든 흔적이 있다.
- donor, authority, evidence, queue, runtime proof를 모두 신경 쓴다.

나쁜 시스템이냐고 물으면:

- product UX 관점에서는 무겁다.
- 신규 operator에게는 거의 미로다.
- 문서와 authority surface가 많아져서 "현재 정답"을 찾는 비용이 크다.
- 복잡도를 감당할 운영자가 없으면 시스템 자체가 버거워진다.

따라서 이 시스템은 "바보 같은 시스템"이 아니라 **고생해서 똑똑해졌지만, 그 고생의 흉터 때문에 무거운 시스템**이다.

## 8. What This Means Next

앞으로 이 시스템을 더 좋게 만들려면 새 기능보다 아래가 더 중요하다.

1. 현재 operator가 믿어야 하는 authority surface를 더 줄인다.
2. `docs/temp`와 canonical dated docs 사이의 현재성 표시를 더 선명하게 만든다.
3. material-side / system-track / runtime proof / narrative artifact authority를 한 장짜리 current map으로 압축한다.
4. deepclone/donor 계열은 지금처럼 direct copy 금지와 translation layer 원칙을 유지한다.
5. 병렬조사는 유지하되, synthesis 후 남는 문서/queue 찌꺼기를 더 강하게 청소한다.

## 9. Caveats

- 이 문서는 system-design assessment다. 특정 버그 fix의 closure audit가 아니다.
- production code를 수정하지 않았다.
- full test suite, live canary, fresh runtime은 실행하지 않았다.
- 판단은 현재 문서/운영 evidence 중심이다. 전체 runtime artifact body를 전수감리한 문서는 아니다.
- 사용자 질문의 구어적 표현은 본문에서 시스템 평가 언어로 바꾸어 다뤘다.

## 10. 3-Pass Audit Record

Pass 1. Structure and scope:

- 문서 유형을 system-track human-facing assessment로 고정했다.
- "생각 없이 만든 시스템인가 / 생각하면서 만든 시스템인가"를 design intent, authority, evidence, donor handling, operational debt로 분해했다.
- 실행 SSOT나 queue realization으로 확장하지 않았다.

Pass 2. Evidence and consistency:

- 주요 판단은 `AGENTS.md`, material-side SSOT, donor-first report, Golden Canary benchmark, 10-terminal dispatch, authority deep-dive, wave2/wave3 synthesis, Stage4 conflict dispatch에 연결했다.
- temp queue 존재는 확인했지만, 사용자 요청이 평가 문서 작성이므로 큐 실현으로 해석하지 않았다.
- "생각이 있다"는 긍정 판단과 "무겁고 복잡하다"는 부정 판단을 함께 기록했다.

Pass 3. Execution and readability:

- 결론을 맨 앞에 두고, 증거와 리스크를 뒤에 배치했다.
- 운영자가 바로 가져갈 수 있도록 scorecard와 next-shape를 넣었다.
- 과잉 미화와 과잉 비난을 모두 피하고, "생존형 control plane"이라는 평가로 닫았다.

Estimated Confidence: `96%`

Confidence limits:

- full live-run proof를 하지 않았으므로 product runtime quality 자체에 대한 최종 평가는 아니다.
- artifact body 전수감리 없이 대표 문서와 운영 산출물 중심으로 평가했다.
- 그래도 "생각 없이 만든 시스템인가"라는 질문에는 충분히 답할 수 있는 evidence가 있다.
