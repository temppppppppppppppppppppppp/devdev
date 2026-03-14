# [S-T0] Stage 0 Bible Failure vs System Failure Ambiguity 3-Pass Re-Audit

> 작성일: 2026-03-13
> 범위: Geuldobi Stage 0 handoff, `plot_roadmap` 계약, Stage 0 저장 경계, file/DB/in-memory SSOT 분기
> 목적: 왜 Stage 0에서는 `bible failure`와 `system failure`가 Stage 1~4보다 덜 깔끔하게 분리되는지, 현행 코드 기준으로 다시 잠근다
> 방법: static / read-only / source-report cross-check / targeted code verification / targeted regression check
> 재감리 상태: `pass-with-ledger-correction`
> 최종 확신도: `93%`

---

## Executive Summary

원문의 큰 문제의식은 유효하다. Stage 0는 여전히 **artifact builder**, **import/recovery hub**, **handoff wiring stage**가 겹쳐 있다. 그래서 Stage 1~4보다 실패 원인을 곧바로 `bible failure` 또는 `system failure`로 분리하기 어렵다.

다만 원문 그대로 유지할 수는 없다. 현재 코드 기준으로 `plot_roadmap`는 더 이상 concept/reverse path에서 **순수 save-time patch**에만 의존하지 않는다.

- [stage0/__init__.py](C:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L372) `generate_from_concept()`는 treatment 생성 직후 in-memory Bible에 `plot_roadmap`를 주입한다.
- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L722) 는 return/save 전에 arc stub 기반 `plot_roadmap`를 보장한다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L633) `_s0_save_results()`는 여전히 fallback `_ensure_plot_roadmap()`를 수행한다.
- [tests/test_stage01_helpers.py](C:/Users/User/Desktop/글도비/tests/test_stage01_helpers.py#L395) 와 [tests/test_reverse_expander_g2.py](C:/Users/User/Desktop/글도비/tests/test_reverse_expander_g2.py#L100) 가 이 보장을 회귀 테스트로 잠그고 있다.

따라서 현행 결론은 다음이다.

- **원문의 대주제는 유효하다.**
- **하지만 애매함의 중심을 `plot_roadmap` save-time patch 단일 이슈로 고정한 부분은 과하다.**
- 지금의 핵심은 **entry path별 계약 강도 차이**, **file/DB/memory truth split**, **완전 fail-closed가 아닌 저장 semantics**다.

---

## 유효성 판정

### 1. 핵심 논지: `confirmed`

- Stage 0는 Stage 1~4보다 failure class 분리가 어렵다.
- 이유는 Stage 0가 생성, 복구, 임포트, 저장, handoff를 함께 담당하기 때문이다.
- 이 큰 결론은 현재 코드와 문서 기준으로 유지 가능하다.

### 2. `plot_roadmap` 관련 근거: `partially_confirmed`

- 원문이 짚은 "`plot_roadmap`가 Stage 0 ambiguity의 핵심 축" 자체는 맞다.
- 하지만 "현재도 concept/reverse path가 save-time patch에서만 복구된다"는 식의 서술은 현행 코드 기준으로는 과장이다.
- 지금은 **생성기 내부 보장 + save-time fallback + 경로별 직접 주입**이 함께 존재하는 **다층 계약**에 가깝다.

### 3. 저장 실패/경계 서술: `partially_confirmed`

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L654) 는 Bible 저장 전체를 broad `try/except`로 감싸고 warning 후 계속 진행한다.
- 다만 같은 함수는 Bible 저장 실패 시 [treatment 저장을 건너뛰도록](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L685) 부분 fail-closed를 추가했다.
- 따라서 원문의 "warning + continue" 관찰은 맞지만, 현재는 일부 경계가 보강됐다.

### 4. 문서 표면 정합성: `rejected-as-written`

- 원문 링크 다수가 현재 워크스페이스가 아닌 `C:/Users/wjjo/...` 절대경로를 가리킨다.
- 현행 증거 문서로 유지하려면 현재 경로 `C:/Users/User/...` 기준으로 보정이 필요했다.

---

## 최종 판정

- `core_thesis = valid`
- `evidence_ledger = corrected`
- `current_root_of_ambiguity = heterogeneous_entry_contracts + split_truth_surface + soft_persistence_boundary`
- `historical_root_cause_status = plot_roadmap pure save-boundary bug는 concept/reverse flow 기준 상당 부분 완화`

즉, 이 문서는 **폐기 대상은 아니지만 현행 코드에 맞게 교정되어야만 SSOT 보조 문서로 유지 가능**하다.

---

## Evidence

### 1. `plot_roadmap`는 현재 "save-time only"가 아니라 "다층 계약"이다

직접 근거:

- [stage0/__init__.py](C:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L387)
  - `StageZeroManager._ensure_plot_roadmap()`가 treatment 기반 roadmap을 Bible에 주입한다.
- [stage0/__init__.py](C:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L404)
  - `generate_from_concept()`는 treatment 생성 직후 `_ensure_plot_roadmap()`를 호출한다.
- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L722)
  - 역설계 경로도 `_ensure_plot_roadmap()`로 arc stub 기반 roadmap을 return 전 보장한다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L633)
  - 공통 저장 훅은 한번 더 `_ensure_plot_roadmap()`를 호출해 fallback을 건다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L499)
  - block extension 경로는 공통 훅이 아니라 별도 direct write로 `plot_roadmap`를 저장한다.

해석:

- Stage 0의 문제는 더 이상 "`plot_roadmap`가 save-time에만 생긴다"가 아니다.
- 현재 문제는 **동일 계약이 한 레이어에서만 잠기지 않고, manager / reverse expander / helper fallback / block extension direct write에 흩어져 있다**는 점이다.

### 2. Stage 0는 entry path별 계약 강도가 여전히 다르다

직접 근거:

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L373) `stage_0_extended()`는 6개 entry path를 한 메뉴에 묶는다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L431) concept path는 Bible + treatment를 생성한다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L437) reverse path는 Bible + episode_bibles/style_guide + DB stub을 만든다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L494) import path는 기존 Bible만 읽는다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L499) block extension path는 별도 파일/DB write를 수행하고 공통 저장 체인을 우회한다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L540) style analysis / work guard는 Bible/Treatment handoff 자체가 목적이 아니다.

해석:

- "Stage 0 실패"라는 이름만으로는 artifact 문제인지 routing 문제인지 좁혀지지 않는다.
- 실제로는 **생성**, **복구**, **임포트**, **확장**, **분석/설정**이 같은 메뉴 아래에 공존한다.

### 3. Stage 0는 여전히 single durable truth가 약하다

직접 근거:

- [docs/stage_map/stage0.md](C:/Users/User/Desktop/글도비/docs/stage_map/stage0.md#L65)
  - 프로젝트 루트에 `treatment_generated.json`, `treatment_extended.json`이 남는다.
- [docs/stage_map/stage0.md](C:/Users/User/Desktop/글도비/docs/stage_map/stage0.md#L109)
  - 운영 중 primary source는 DB anchors / tables라고 명시한다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L691)
  - concept/common save path는 `treatment_generated.json`을 쓴다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L504)
  - block extension path는 `treatment_extended.json`을 별도로 쓴다.
- [project_manager.py](C:/Users/User/Desktop/글도비/modules/core/project_manager.py#L819)
  - treatment file을 다시 읽어 `plot_roadmap`를 Bible anchor에 강제 주입하는 경로가 남아 있다.

해석:

- Stage 0 종료 시 "정답"이 DB anchor인지, project-local JSON인지, 메모리의 `master_bible`인지가 경로에 따라 달라질 수 있다.
- 이 점은 Stage 1~4보다 Stage 0를 더 system-sensitive하게 만든다.

### 4. 저장 semantics는 부분 fail-closed지만, 여전히 완전 hard-stop은 아니다

직접 근거:

- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L656)
  - Bible 저장 실패는 warning으로 남고 예외를 다시 던지지 않는다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L685)
  - 다만 Bible 저장 실패 시 treatment 저장은 건너뛴다.
- [stage01_helpers.py](C:/Users/User/Desktop/글도비/modules/core/stage01_helpers.py#L698)
  - DB reload 실패도 warning 후 종료한다.
- [reverse_expander.py](C:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L801)
  - 역설계 DB 저장은 단일 트랜잭션으로 묶고 rollback 한다.

해석:

- Stage 0는 예전보다 fail-closed 쪽으로 이동했다.
- 그래도 여전히 "저장 실패 = 즉시 전체 Stage 0 실패 반환"처럼 강하게 잠겨 있지는 않다.
- 따라서 artifact failure와 persistence failure의 경계가 완전히 깨끗해지지는 않았다.

### 5. Stage 2 소비 지점은 여전히 `plot_roadmap`를 직접 읽는다

직접 근거:

- [stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py#L258)
  - Stage 2는 `bible_root.get("plot_roadmap", [])`를 직접 읽는다.

해석:

- Stage 0가 어떤 경로로 roadmap을 만들었는지와 무관하게, downstream contract는 여전히 `plot_roadmap` 존재를 요구한다.
- 그래서 roadmap contract가 Stage 0 ambiguity 분석에서 빠질 수는 없다.
- 다만 **현재는 "absence"보다 "which path wrote it, from which source, onto which durable surface"가 더 중요한 질문**이다.

---

## Entry Path Contract Matrix

| Stage 0 path | 산출물 성격 | `plot_roadmap` 보장 시점 | durable write surface | 현재 ambiguity 포인트 |
| ---- | ---- | ---- | ---- | ---- |
| concept | Bible + treatment 생성 | manager 내부에서 treatment 직후 | DB `bible`, `preset_state`, `style_guide?`, `treatment_generated.json` | manager 보장과 helper fallback이 둘 다 존재 |
| reverse engineering | Bible + episode_bibles + arc stub | reverse expander 내부에서 return 전 | DB tables + `arcs` + 이후 `bible` anchor | stub truth와 Bible truth가 공존 |
| Bible import | 기존 Bible 반입 | 별도 합성 없음 | `bible` anchor | imported artifact 품질에 크게 의존 |
| block extension | treatment 확장 | direct write 시점 | `treatment_extended.json` + `bible` anchor | 공통 저장 체인을 우회 |
| style analysis | style_guide 분석 | 해당 없음 | `style_guide` anchor | Bible/Treatment handoff와 무관 |
| work guard | 설정/가드 | 해당 없음 | config/work_guard | Bible/Treatment handoff와 무관 |

이 표가 보여 주는 결론은 단순하다. Stage 0는 하나의 "artifact validator"가 아니라, **서로 다른 계약을 가진 여러 서브파이프라인의 묶음**이다.

---

## Why Stage 1~4 Are Cleaner

- Stage 1~4도 물론 system failure가 있을 수 있다.
- 그러나 입력 계약은 Stage 0보다 훨씬 좁다.
- [stage2_orchestrator.py](C:/Users/User/Desktop/글도비/modules/core/stage2_orchestrator.py#L258) 처럼 Stage 2는 이미 `plot_roadmap`가 있는 Bible을 전제로 읽는다.
- Stage 3/4는 더 내려가며 `arcs`, `blueprints`, manuscript history처럼 더 좁은 surface를 주로 소비한다.

즉 Stage 1~4는 "준비된 입력을 소비"하는 단계고, Stage 0는 "그 준비된 입력 자체를 만든 뒤 저장하고 넘기는" 단계다. 이 차이가 failure class 분리 난도를 만든다.

---

## Failure Classification Guidance

Stage 0에서 아래 현상은 현행 코드 기준으로 바로 `bible failure`로 단정하면 안 된다.

- concept 또는 reverse flow 이후 Stage 2가 빈 roadmap을 읽음
- imported Bible에는 roadmap이 없는데 DB anchor에는 일부 stub만 존재
- local `treatment_generated.json`과 DB `bible` anchor가 다름
- block extension 이후 roadmap은 있으나 common save 경로 메타와 어긋남

1차 분류는 아래 4축이 더 안전하다.

- `artifact_failure_candidate`
  - 입력 Bible 자체가 비었거나 imported artifact 품질이 약함
- `path_contract_gap_candidate`
  - concept / reverse / import / extend 중 특정 경로 계약이 다르게 작동함
- `save_boundary_failure_candidate`
  - DB anchor write, reload, file save 경계에서 값이 어긋남
- `effective_truth_mismatch_candidate`
  - 사용자가 보는 파일과 다음 stage가 실제로 읽는 surface가 다름

보정 포인트:

- concept / reverse path의 roadmap 부재는 이제 "생성기 자체가 항상 비운다"보다 **regression, bypass, import path, 또는 저장 surface mismatch** 가능성을 먼저 의심하는 편이 맞다.

---

## Regression Check

직접 실행:

- `pytest tests/test_stage01_helpers.py::TestStage0RoadmapInjection::test_s0_save_results_injects_plot_roadmap_from_treatment`
- `pytest tests/test_stage01_helpers.py::TestStage0RoadmapInjection::test_s0_save_results_builds_stub_plot_roadmap_from_saved_arcs`
- `pytest tests/test_reverse_expander_g2.py::test_run_returns_plot_roadmap_before_save`

결과:

- `3 passed`

의미:

- concept/common save path의 roadmap 주입
- reverse path의 roadmap 선보장
- saved arcs fallback

위 3개는 현재 테스트로 재확인됐다.

---

## 3-Pass Re-Audit Log

### PASS 1 — 원문 주장 분해

후보는 아래 5개였다.

- Stage 0 failure class 혼합 구조
- `plot_roadmap` save-boundary 의존
- file / DB / memory truth split
- save semantics soft failure
- 절대경로/표면 정합성 드리프트

### PASS 2 — 코드/테스트 대조

재확인:

- Stage 0 multi-entry 구조는 유지
- truth split은 유지
- Stage 2의 `plot_roadmap` 직접 소비는 유지
- save warning 경계는 유지

보정:

- concept path는 이제 manager 내부에서 roadmap을 보장한다
- reverse path도 return 전 roadmap을 보장한다
- common save 훅은 fallback safety net로 남아 있다
- treatment save는 Bible save 실패 시 건너뛴다

### PASS 3 — 최종 고정

최종 결론은 아래 4개로 잠근다.

1. Stage 0는 여전히 `bible failure`와 `system failure`가 섞이기 쉬운 구간이다.
2. 하지만 그 주된 이유는 더 이상 "roadmap 부재 단일 버그"가 아니다.
3. 현재 중심 원인은 `entry path heterogeneity + truth surface split + soft persistence boundary`다.
4. `plot_roadmap`는 여전히 핵심 계약이지만, 현재는 **absence issue**보다 **cross-layer ownership issue**로 보는 편이 정확하다.

---

## Final Conclusion

왜 Stage 0가 애매하냐는 질문에 대한 현행 답은 다음과 같다.

Stage 0는 아직 "좋은 Bible을 만들었는가"만 검증하는 단계가 아니다. 동시에 "어떤 경로에서 만들었는가", "어느 surface에 저장했는가", "다음 stage가 실제로 무엇을 읽는가"까지 함께 책임지는 단계다.

그래서 현행 Geuldobi에서 Stage 0는 다음처럼 봐야 한다.

- Stage 0 실패 = 아직 `artifact failure`와 `system failure`가 혼합될 수 있는 구간
- 다만 현재 혼합의 중심은 `plot_roadmap` 누락 단일 이슈가 아니라 **경로별 계약 차이와 SSOT 분기**다
- Stage 1~4 실패 = 상대적으로 입력 계약이 좁아 failure class 분리가 더 쉬운 구간

운영 판단:

- **Stage 0 전면 리팩토링은 현재 기준 `no-go`다.**
- 이 문서가 지적하는 문제는 존재하지만, 지금 필요한 것은 대규모 구조 재작성보다 **국소 hardening / 계약 명시 / 상태 표면 문서화**다.
- 즉 이 보고서는 "리팩토링 추진 근거"가 아니라 **과잉 리팩토링 금지 근거**로 읽는 편이 맞다.

한 줄 결론:

**Stage 0는 여전히 `Bible failure vs system failure`를 완전히 분리하는 단계가 아니다. 다만 현재 애매함의 중심은 save-time roadmap 누락이 아니라, 여러 Stage 0 path가 서로 다른 계약층과 truth surface를 갖고 있다는 점이다.**

---

## Closure

이 문서는 아래 판단으로 닫는다.

- `전면 리팩토링`: `no-go`
- `희망사항 수준의 구조 재작성`: backlog 미편입
- `재오픈 조건`: 실제 운영에서 Stage 0 failure triage가 반복적으로 오판되거나, import/save boundary에서 새 P0/P1 회귀가 확인될 때만
- `허용되는 후속 작업`: 문서 표준화, machine-readable status 추가, import path hardening 같은 국소 수정만

정리:

- 이 보고서는 **구조적 애매함을 설명하는 문서**로는 유지
- 그러나 이를 근거로 한 **대규모 리팩토링 제안은 종료**
- 후속은 필요 시 작은 hardening 티켓으로만 분해한다
