# [S-T0] Stage 0 Bible Failure vs System Failure Ambiguity 3-Pass Report

> 작성일: 2026-03-13
> 범위: Geuldobi Stage 0 handoff, `plot_roadmap` 계약, Stage 0 저장 경계, file/DB/in-memory SSOT 분기
> 목적: 왜 Stage 0에서는 `bible failure`와 `system failure`가 Stage 1~4보다 덜 깔끔하게 분리되는지 문서로 잠근다
> 방법: static / read-only / code + existing audit cross-check / 3-pass consolidation

---

## Executive Summary

Stage 0가 애매한 이유는 단순하지 않다. 핵심은 아래 4개가 겹치기 때문이다.

1. `plot_roadmap`가 Stage 0 전체 경로에서 균일한 hard contract로 잠기지 않고, 경로에 따라 생성 직후 또는 helper/save 경계에서 다시 보정된다.
2. Stage 0는 entry point가 많고, 각 entry point가 같은 Bible/Treatment 계약을 같은 강도로 보장하지 않는다.
3. Stage 0의 운영 SSOT가 하나로 고정되지 않는다. 같은 실행에서도 `in-memory`, `DB anchor`, `project-local file`이 서로 다른 시점에 갱신될 수 있다.
4. 저장 실패가 대체로 fail-closed가 아니라 `warning + continue`로 흐르는 경향이 있어, artifact 문제와 plumbing 문제의 경계가 흐려진다.

그래서 Stage 1~4처럼 "입력 산출물이 이미 정해져 있고, 실패 지점이 상대적으로 좁은" 구조와 달리, Stage 0는 아직도 `bible 자체가 나빠서 실패한 것인지`, `Stage 0 저장/동기화 경로가 꼬여서 실패한 것인지`가 같은 현상으로 보일 수 있다.

핵심 결론:

- Stage 0는 **artifact creation stage**이면서 동시에 **handoff wiring stage**다.
- 따라서 현행 코드 기준으로 Stage 0 실패는 아직 `bible failure`와 `system failure`가 완전히 분리되지 않는다.
- 애매함의 중심은 여전히 `plot_roadmap`와 저장 경계다.

---

## 최종 판정

### 판정 1. Stage 0는 `artifact validator`가 아니라 `artifact builder + contract normalizer`에 가깝다

- `StageZeroManager.generate_from_concept()`는 현재 concept path에서 `plot_roadmap`를 생성 후행 단계로 주입한다.
- 하지만 Stage 0 전체 경로가 같은 방식으로 잠기는 것은 아니다. helper/save 경계에서 다시 정규화되고 주입되는 경로가 여전히 함께 존재한다.
- 따라서 Stage 0에서 보이는 실패는 "생성물 품질 실패"와 "생성 후 주입/저장 실패"가 쉽게 섞인다.

### 판정 2. Stage 0는 entry path별 계약 강도가 다르다

- 컨셉 생성
- 역설계
- Bible 임포트
- Block 확장
- 스타일 분석

위 5개는 모두 Stage 0 메뉴 아래에 있지만, 실제로는 동일한 산출물 계약을 같은 수준으로 보장하지 않는다.

- 어떤 경로는 Bible/Treatment를 직접 생성한다.
- 어떤 경로는 저장된 arc stub이나 기존 file을 다시 올린다.
- 어떤 경로는 Bible보다 style_guide만 건드린다.

즉, Stage 0는 이름은 하나지만 실제로는 여러 sub-pipeline의 묶음에 가깝다.

### 판정 3. Stage 0는 `single durable truth`가 Stage 1~4보다 약하다

- Stage 0 문서상 산출물은 `stage0_output/bible.json`, `stage0_output/treatment.json`, `treatment_generated.json`, `treatment_extended.json`, DB `anchors["bible"]`, `preset_state`, `style_guide`까지 퍼져 있다.
- 문서도 `stage0_output/*.json`은 export/복구용이고 운영 중 primary source는 DB anchors라고 말하지만, 같은 Stage 0 helper 코드가 다시 project-local JSON도 직접 저장한다.
- 이 구조에서는 "지금 무엇을 truth로 보고 다음 스테이지가 진입했는가"가 경로에 따라 달라질 수 있다.

따라서 Stage 0는 실패를 artifact 문제로 볼지, persistence/handoff 문제로 볼지 즉시 나누기 어렵다.

---

## Evidence

### 1. `plot_roadmap`는 Stage 0 전체에서 generator-boundary hard contract로 통일돼 있지 않다

근거:

- [__init__.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage0/__init__.py#L404) `generate_from_concept()`
  - Bible 생성 후 Treatment를 만들고, 그 다음 `_ensure_plot_roadmap()`를 호출한다.
  - 즉 concept path조차 생성 직후 후행 주입을 거친다.
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L633) `_ensure_plot_roadmap()`
  - treatment에서 못 만들면 saved arcs에서 다시 stub roadmap을 만든다.
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L654) `_s0_save_results()`
  - DB 저장 직전에 다시 `_ensure_plot_roadmap()`를 호출한다.
- [stage2_orchestrator.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage2_orchestrator.py#L259)
  - Stage 2는 `bible_root.get("plot_roadmap", [])`를 직접 읽는다.

의미:

- concept path는 현재 부분 보강돼 있지만, Stage 0 전체 계약은 여전히 `generate -> normalize -> save` 여러 경계로 나뉘어 있다.
- Stage 2가 기대하는 입력 계약은 `plot_roadmap`인데, 이 필드가 모든 Stage 0 path에서 동일한 시점과 동일한 방식으로 잠기지 않는다.
- 따라서 Stage 0에서 `plot_roadmap` 문제가 보이면 그것이 생성 품질 문제인지, helper/save 경계 문제인지가 쉽게 섞인다.

### 2. Stage 0 helper는 여러 entry path를 하나의 공통 저장 함수에 얹고 있다

근거:

- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L407) `stage_0_extended()`
  - concept / reverse engineering / Bible import / block extension / style analysis / work guard를 모두 Stage 0 submenu로 묶는다.
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L425) `_s0_handle_concept()`
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L431) `_s0_handle_reverse_engineering()`
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L479) `_s0_handle_block_extension()`

의미:

- 이름은 Stage 0 한 단계지만, 실제로는 생성/복구/임포트/확장/스타일 분석이라는 다른 failure mode들이 섞여 있다.
- 그래서 "Stage 0가 실패했다"는 말만으로는 artifact failure인지 routing failure인지 곧바로 좁혀지지 않는다.

### 3. Stage 0는 file / DB / in-memory truth가 동시에 살아 있다

근거:

- [stage0.md](C:/Users/wjjo/Desktop/글도비/docs/stage_map/stage0.md#L65)
  - `stage0_output/*.json`, `treatment_generated.json`, `treatment_extended.json`, DB anchors를 모두 산출물로 둔다.
- [stage0.md](C:/Users/wjjo/Desktop/글도비/docs/stage_map/stage0.md#L118)
  - `treatment_generated.json`, `treatment_extended.json`은 자동 무효화 없이 최신 결과로 덮어쓴다고 명시한다.
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L685)
  - `_s0_save_results()`는 `treatment_generated.json`을 별도로 저장한다.
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L479)
  - block extension 경로는 `treatment_extended.json`을 따로 저장하고, Bible anchor에도 별도로 roadmap을 주입한다.
- [project_manager.py](C:/Users/wjjo/Desktop/글도비/modules/core/project_manager.py#L819)
  - treatment file을 읽어 `plot_roadmap`를 다시 만들어 DB `bible` anchor에 강제 주입하는 경로가 별도로 존재한다.

의미:

- Stage 0가 끝났을 때 "정답"이 DB anchor인지, local JSON인지, 현재 메모리의 `master_bible`인지가 경로마다 달라질 수 있다.
- 이 구조는 Stage 1~4처럼 input contract가 DB surface로 좁혀진 단계보다 실패 원인 구분이 어렵다.

### 4. 저장 실패가 강하게 fail-closed 되지 않는 지점이 남아 있다

근거:

- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L654)
  - Bible 저장 블록 전체가 broad `try/except`로 감싸져 있고, 실패 시 warning만 남긴다.
- [stage01_helpers.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage01_helpers.py#L679)
  - Treatment file 저장도 별도 `try/except`로 감싸져 있어 Bible anchor save와 분리된다.
- [reverse_expander.py](C:/Users/wjjo/Desktop/글도비/modules/core/stage0/reverse_expander.py#L794)
  - `persist_to_db()`는 manuscripts/state_logs/episode_bibles/blueprints/arcs를 하나의 트랜잭션으로 저장하지만, helper 레이어에서는 이 결과를 별도 Stage 0 저장과 다시 조합한다.

의미:

- 어떤 경로에서는 DB 저장 실패와 file 저장 성공이 공존할 수 있고, 어떤 경로에서는 reverse-engineered stub이 DB에 들어간 상태에서 helper 후처리가 다시 돈다.
- 그래서 실패 현상이 artifact 불량인지, Stage 0 저장 wiring 문제인지 분리하기가 어렵다.

### 5. Stage 0는 이미 helper/main path 중복으로 경로 드리프트와 실효 입력 불일치 경험이 있다

근거:

- [S-T1-stage0-ui-flow-deep-dive-findings.md](C:/Users/wjjo/Desktop/글도비/docs/2026-03-13/S-T1-stage0-ui-flow-deep-dive-findings.md)
  - helper 경로 정책 메뉴가 사용자 선택을 기본값으로 덮어쓰는 문제를 확정했다.
- [test_stage0_pov.py](C:/Users/wjjo/Desktop/글도비/tests/test_stage0_pov.py#L1)
  - 본체 `StageZeroManager` POV 경로는 테스트하지만 helper 중복 메뉴를 완전히 대체하지는 못한다.

의미:

- Stage 0에서는 artifact 자체보다 "어느 경로를 탔느냐"가 최종 저장값과 실효 입력을 바꾼 전례가 이미 있다.
- 이건 Stage 0가 artifact failure와 system failure를 분리하기 어렵다는 정황이 아니라, 이미 실제 사례가 있었던 구조적 근거다.

---

## Why Stage 1~4 Are Cleaner

비교 기준:

- Stage 1은 Bible을 읽지만 실패 surface가 `plot_roadmap 부재 / Analyst 품질 미달 / boundary reject`로 비교적 좁다.
- Stage 2는 이미 `MasterBible.plot_roadmap`를 입력 계약으로 전제하고 시작한다.
- Stage 3는 핵심 입력이 `arcs`라서 Bible failure와 직접 섞일 일이 적다.
- Stage 4는 핵심 입력이 `blueprints + arcs + manuscript history`라서 Bible은 품질 보조 컨텍스트에 더 가깝다.

즉 Stage 1~4는 "입력 계약이 이미 좁혀진 단계"인데, Stage 0는 그 입력 계약 자체를 만드는 단계이자 보정하는 단계라서 failure class가 더 혼합되어 있다.

---

## Failure Classification Guidance

Stage 0에서 아래는 아직 `bible failure`로 단정하면 안 된다.

- `plot_roadmap` 부재
- Stage 2 진입 시 Bible anchor는 있는데 roadmap이 비었음
- reverse engineering 후 다음 stage 시작점이 어긋남
- local `treatment_generated.json`과 DB `bible` anchor가 다름

이 경우 1차 분류는 아래처럼 잡는 편이 맞다.

- `artifact_failure_candidate`
  - 생성물 내부가 비었거나 구조가 약함
- `save_boundary_failure_candidate`
  - save-time patch, anchor write, reload 경계에서 어긋남
- `path_drift_failure_candidate`
  - concept/reverse/import/extend 중 어떤 Stage 0 path를 탔는지에 따라 계약이 달라짐
- `effective_input_mismatch_candidate`
  - 사용자가 보고 있는 산출물과 다음 stage가 실제로 읽는 산출물이 다름

즉 Stage 0는 아직 `bible failure`와 `system failure`를 binary로 나누기보다,
`artifact`, `save boundary`, `path drift`, `effective input mismatch`의 4축으로 보는 게 맞다.

---

## 3-Pass Log

### PASS 1 — 후보 가설 수집

초기 후보는 아래 7개였다.

- `plot_roadmap` save-time patch 의존
- Stage 0 multi-entry drift
- file/DB/in-memory truth split
- reverse engineering partial persistence ambiguity
- helper/main duplicate config drift
- effective input mismatch
- 단순 mojibake 표시 문제

### PASS 2 — 후보 제거 및 재분류

제거/축소:

- 단순 mojibake 표시 문제는 핵심 원인에서 제외
  - 표시 깨짐 자체보다 경로 드리프트와 저장값 불일치가 더 큰 원인이다.

재분류:

- reverse engineering partial persistence는 독립 루트코즈라기보다 `save boundary ambiguity`의 하위 사례로 통합

### PASS 3 — 최종 고정

최종 원인은 아래 4개로 고정한다.

1. `plot_roadmap` contract is not uniformly locked across Stage 0 paths
2. Stage 0 has multiple heterogeneous entry paths
3. Stage 0 truth surface is split across file / DB / memory
4. Stage 0 save failures do not always fail closed

---

## Final Conclusion

왜 Stage 0가 애매하냐는 질문의 답은 명확하다.

Stage 0는 아직 "좋은 Bible을 만들었는가"만 검증하는 단계가 아니다.  
동시에 "그 Bible을 어느 경로에서, 어느 저장 경계에서, 어떤 형태로 다음 스테이지에 넘겼는가"까지 함께 책임지는 단계다.

그래서 현행 Geuldobi에서 Stage 0는 다음처럼 봐야 한다.

- Stage 0 실패 = 아직 `artifact failure`와 `system failure`가 혼합될 수 있는 구간
- Stage 1~4 실패 = 상대적으로 입력 계약이 좁아져 있어 failure class 분리가 더 쉬운 구간

운영상의 실전 결론은 한 줄이다.

**Stage 0는 아직 `Bible failure vs system failure`를 완전히 분리하는 단계가 아니라, 그 분리를 가능하게 만드는 전처리/저장 경계 단계다.**

---

## Follow-up

우선순위:

1. `plot_roadmap`를 Stage 0 생성기 산출물 자체의 hard contract로 승격
2. Stage 0 entry paths를 `concept / reverse / import / extend`별로 계약 표로 분리
3. Stage 0 completion 조건을 `DB anchor sync complete` 기준으로 재정의
4. Stage 0 audit에서 `artifact vs save-boundary vs path-drift` 3축 판정을 표준화
