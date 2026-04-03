Date: 2026-04-02
Status: final
Type: bounded survey
Scope: Stage0 BI generation vs legacy DNA sync/handoff vs Stage2 consumption
Baseline Commit: `aaf495d6`
Baseline Dirty Summary: workspace dirty; active Stage4 consumer-contract edits and demo canary artifacts present during survey
Evidence Artifact: `docs/2026-04-02/stage0-bible-generation-dna-sync-stage2-consume-evidence.json`
Side-Effect Coverage: file-backed BI artifacts, DB bible anchor writes, Stage0 persistence gate, Stage2 startup gate

# Answer First

`Stage0 bible 생성 과정`을 의심할 만한 이유는 있습니다. 다만 본체는 `최근 builder가 갑자기 이상해졌다`보다, `BI file / treatment / DB bible anchor`가 함께 권위를 나눠 가지는 split-truth 구조입니다.

현재 코드 기준으로는:

- 최신 routed BI builder는 `MasterBible.plot_roadmap`와 `MasterBible.protagonist_config`를 넣도록 설계돼 있다.
- 그런데 legacy Stage0 flow와 handoff는 생성 후에도 `plot_roadmap`를 treatment에서 다시 만들고 DB bible anchor를 덮어쓴다.
- Stage2는 raw BI file보다 DB anchor의 `plot_roadmap` readiness를 직접 믿고 진입한다.
- 실제 root `bible/0_bi_*.json` 샘플도 혼재돼 있다.
  - 4개 중 2개만 `plot_roadmap`와 `protagonist_config`를 가진다.
  - 즉 파일 산출물과 runtime-consumable state가 항상 일치하지 않는다.

한 줄 결론:

`최근 Stage0 문제`를 잡으려면 builder 한 점을 때리는 것보다, `BI file -> DNA sync/handoff -> Stage2 consume` 전체를 source-of-truth 관점으로 봐야 한다.

# Hard Conclusions

1. 최신 BI builder 계약은 생각보다 보수적이다.
   - `scripts/build_bi_from_phase0_and_tr.py:386-497`는 `MasterBible.protagonist_config`와 `MasterBible.plot_roadmap`를 둘 다 만든다.
   - 같은 스크립트의 main 경로는 treatment draft와 BI `plot_roadmap` hash가 정확히 일치해야 통과한다.
   - `scripts/build_wuxia_bi_from_phase0_and_tr.py:616-683`도 family-specific builder로 `plot_roadmap`를 treatment에서 직접 넣는다.

2. legacy Stage0는 생성 후 roadmap 권위를 다시 만진다.
   - `modules/core/project_manager.py:801-870`의 `force_sync_v25_dna()`는 bible file과 treatment file을 로드한 뒤 treatment에서 `plot_roadmap`를 재생성하고, 그 결과를 DB `bible` anchor에 저장한다.
   - 이 경로는 BI file을 그대로 authoritative source로 쓰는 것이 아니라, treatment를 재정규화한 결과를 runtime anchor에 주입한다.

3. handoff gate도 BI file 불변식을 보장하지 않는다.
   - `modules/core/stage0_handoff.py:215-227`의 `ensure_plot_roadmap()`는 기존 roadmap가 없으면 treatment나 saved arcs에서 roadmap를 backfill한다.
   - `modules/core/stage01_helpers.py:716-731`는 이 handoff 결과를 bible anchor 저장 전에 다시 적용한다.

4. Stage2는 raw BI file보다 DB bible anchor의 handoff 결과를 더 직접 소비한다.
   - `modules/core/stage2_orchestrator.py:289-307`에서 Stage2는 DB에서 `bible` anchor를 로드하고, `MasterBible.plot_roadmap`를 읽은 뒤 readiness를 hard gate로 건다.
   - `modules/core/stage2_preflight.py:470-488`은 별도로 `protagonist_config`를 Stage2 runtime guidance에 사용한다.

5. 실제 BI artifacts도 mixed-vintage 상태다.
   - root `bible/0_bi_*.json` 4개 중 2개만 `plot_roadmap`와 `protagonist_config`를 가진다.
   - `bible/0_bi_gatekeeper_heir.json`은 UTF-8/JSON은 정상인데 `plot_roadmap`와 `protagonist_config`가 없다.
   - 즉 실제 파일 산출물은 현재 Stage2 handoff contract와 완전히 동형이 아니다.

# Production Truth

현재 routed generation chain은 `build_narrative_bi.py`에서 family builder로 위임된다. 즉 `narrative router` 자체는 BI shape owner가 아니라, family-specific builder selector다.

현재 blockguide builder는 다음을 직접 책임진다.

- `ProjectData`, `FinanceHUD`, `WorldState`, `AssetLibrary`, `Seeds`, `HistoricalEvents`, `GenreRules`
- `protagonist_config`
- `plot_roadmap`

즉 코드만 보면 `Stage0 builder가 plot_roadmap를 잃어버리는 구조`는 아니다.

# Sync Truth

문제는 생성 후이다.

legacy/manual Stage0 메뉴 경로는 `modules/core/stage01_helpers.py:177-178`에서 `force_sync_v25_dna()`를 바로 호출한다. 이 경로는 BI file을 읽고 끝나는 것이 아니라, treatment를 다시 정규화해서 `plot_roadmap`를 DB anchor로 박는다.

또한 Stage0 extended persistence는 `modules/core/stage01_helpers.py:716-731`에서 `ensure_plot_roadmap()`를 한 번 더 돌린 뒤 bible anchor를 저장한다.

즉 runtime 관점에서 `Stage0 결과물`은 단일 artifact가 아니다.

- raw BI file
- treatment draft
- DB bible anchor

이 셋이 함께 최종 Stage2 handoff state를 만든다.

# Consumption Truth

Stage2 entry는 `plot_roadmap`가 없으면 바로 멈춘다.

- `modules/core/stage2_orchestrator.py:303-307`

그리고 Stage2는 이 roadmap를 Arc source로 읽은 뒤 tactical_doc/state_constraints/state_changes 중심으로 Stage2 runtime을 계속 전개한다.

즉 Stage0 suspicion이 맞다면, 핵심은 다음이다.

- BI prose가 예쁘냐보다
- Stage2가 읽는 `plot_roadmap`와 `protagonist_config`가 최종적으로 어디서 왔느냐

현재 구조에서는 그 owner가 raw BI file로 고정돼 있지 않다.

# Artifact Truth

대표 샘플에서 mixed-vintage가 확인됐다.

- `0_bi_chaebol_ent_empire.json`
  - `plot_roadmap` 있음
  - `protagonist_config` 있음
- `0_bi_wuxia_heavenly_physician.json`
  - `plot_roadmap` 있음
  - `protagonist_config` 있음
- `0_bi_gatekeeper_heir.json`
  - `plot_roadmap` 없음
  - `protagonist_config` 없음
- `0_bi_office_checkup_next_day.json`
  - `plot_roadmap` 없음
  - `protagonist_config` 없음

이건 중요한 신호다.

`최근 builder는 plot_roadmap/protagonist_config를 만들도록 되어 있는데, 실제 root BI corpus는 그 계약을 통일되게 만족하지 않는다.`

즉 사용자가 `최근 Stage0 bible 생성 과정을 의심`하는 감각은, 코드보다는 `artifact fleet heterogeneity`에 더 가까운 경고다.

# Contract Drift

이번 bounded survey에서 가장 큰 drift는 3개다.

1. `BI file truth`와 `DB anchor truth`가 다를 수 있다.
   - legacy DNA sync/handoff가 treatment 기반 roadmap를 anchor에 재주입한다.

2. `plot_roadmap owner`가 builder 단독이 아니다.
   - builder, dna sync, handoff backfill이 공동 소유한다.

3. `runtime-consumable Stage0 state`와 `repo-visible BI file`이 동형이 아니다.
   - 일부 BI는 Stage2-ready contract 필드를 raw file에 아예 갖고 있지 않다.

# Medium-Confidence Conclusions

1. 현재 Stage0 관련 운영 혼란은 `생성기 품질`보다 `소스 오브 트루스 분할`에서 더 많이 나온다.

2. 사용자가 BI file만 보고 Stage0 품질을 판정하면 runtime reality와 엇갈릴 가능성이 높다.

3. Stage2/3/4에서 보이는 일부 upstream 이상은 raw BI 내용보다 `Stage0 file -> treatment -> DB anchor` 변환 체인에서 생기는 구조 부채일 가능성이 높다.

# Open Questions

1. 현재 active project onboarding에서 `force_sync_v25_dna()`가 항상 보장되는가, 아니면 legacy/manual flow에서만 강하게 보장되는가?

2. `protagonist_config`가 없는 old-vintage BI는 runtime에서 항상 다른 경로로 보정되는가?

3. root `bible/0_bi_*.json`를 canonical artifact로 계속 볼 것인지, 아니면 일부를 archival/legacy로 재분류해야 하는가?

4. Stage0 source-of-truth normalization을 연 execution lane으로 올릴지, 아니면 Stage4 active wave 뒤 parked future wave로 둘지 판단이 필요하다.

# Recommended Reading Of The Suspicion

사용자 감각을 가장 정확히 다시 쓰면 이렇다.

`최근 Stage0 bible 생성이 이상한 것 같음`  
= `Stage0 산출 체계가 단일 생성 결과가 아니라, heterogeneous BI files + post-generation DNA sync + Stage2-ready handoff backfill로 운영되고 있어서, 파일만 봐서는 authoritative state를 확신하기 어려움`

즉 이 의심은 유효하다. 다만 표적은 `builder regression` 하나보다 `Stage0 source-of-truth split` 쪽이 더 맞다.

# Next Action

지금 단계에서는 survey만으로 충분하다.

다음 실행 후보를 연다면 이름은 대략 아래 수준이 맞다.

- `stage0-bible-source-of-truth-normalization-remediation`

범위는 builder 품질 개편이 아니라 아래 세 가지다.

- BI file vs treatment vs DB bible anchor owner 정리
- legacy `force_sync_v25_dna` 역할 축소 또는 명시화
- `Stage2-ready handoff`를 raw BI contract와 runtime contract로 분리 표기

# 3-Pass Audit

Pass 1. Structure/Scope
- bounded survey 타입 적합
- 생성기, sync/handoff, Stage2 consume, artifact truth 분리 완료

Pass 2. Evidence/Consistency
- builder, dna sync, handoff, Stage2 entry line anchor 재확인
- root BI artifact scan 수치 일치
- sample BI byte-level UTF-8 read-back 확인

Pass 3. Execution/Readability
- `builder suspicion`과 `source-of-truth split`를 분리해서 읽도록 정리
- 다음 액션은 survey-only 수준으로 제한

Confidence: 97%
