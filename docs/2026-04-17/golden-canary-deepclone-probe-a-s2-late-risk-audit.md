# Golden Canary Deepclone Probe A — S2 Late-Risk Audit

- date: 2026-04-17
- scope: `golden_canary_deepclone_probe_a` opening truth -> `S2` packet -> `S3 must_focus/stop_line` transport seam
- mode: bounded static audit
- audit status: 3-pass adversarial audit complete
- confidence: 96%

## Verdict

`Probe A`의 opening truth는 upstream에서 분명히 강해졌다. 다만 `S2`에는 아직 하나의 실제 seam이 남아 있다. `work_focus`가 fallback으로 떨어지거나 `episode_details`가 느슨하게 요약되면, 이번에 강화한 `private receipt / named seat / access shift / priority lane`이 다시 `수익 증명 + 재평가` 수준의 generic packet으로 납작해질 수 있다.

반대로 말하면, 이 리스크는 `fatal drift`라기보다 `bounded late-risk`다. `episode_details`가 receipt-heavy line을 제대로 들고 있고 `work_focus`가 guard path에서 안정적으로 선택되면, 현재 extractor/constraint chain은 그 truth를 downstream으로 그대로 넘길 수 있다.

한 줄 결론:

- `upstream opening rewrite`: `PASS`
- `S2 packet transport`: `CAUTION`
- `stop-ship blocker`: `아님`
- `다음 런타임 wave`를 열 때는 `S2-generated episode_details / work_focus / must_focus`를 관찰 포인트로 고정해야 함

## Source Anchors

- `Phase0`
  - `treatments/phase0/golden_canary_deepclone_probe_a_phase0_design.json`
- `Probe A TR`
  - `treatments/golden_canary_deepclone_probe_a_tr_block_070_draft.json`
- `work_guard`
  - `work_guards/golden_canary_deepclone_probe_a.yaml`
- `S2/S3 transport code`
  - `modules/core/stage2_preflight.py`
  - `modules/core/tactical_utils.py`
  - `modules/domain/agents/blueprint_constraint_compiler.py`
  - `modules/domain/agents/arc_ensemble.py`
  - `modules/core/scene_obligation_heuristics.py`
  - `modules/domain/agents/unified_arc_validator.py`
- background survey
  - `docs/2026-04-17/stage234-s2-s3-s4-current-head-readiness-parallel-bounded-survey.md`
  - `docs/이전/2026-03-25/stage2-episode-details-specificity-floor-survey.md`

## Pass 1 — Where S2 Can Flatten Probe A

`Probe A Phase0`는 opening contract를 분명히 바꿨다. 목표는 `TR 2~6` 안에 `thesis -> proof -> receipt -> named seat -> next ticket` 체인을 독자에게 명확히 보여 주는 것이다. 같은 packet은 `work_guard`에서도 `public proof -> private receipt`, `named seat`, `예외 계좌`, `우선 응답권`을 opening reward의 정식 형태로 잠갔다.

문제는 `S2PreflightAnalysis`의 `work_focus` 조합 방식이다.

- `_compose_work_focus_text()`는 block 전체 surface를 합쳐 focus text를 만든다.
- `_build_raw_block_focus_candidates()`는 `stakes`, `block_theme`, `constraint_summary`, 일부 foreshadow/callback을 우선 tracking slot으로 뽑는다.
- `_build_fallback_work_retrieval_focus()`는 더 세게 줄어들어 `block_theme`, `plot_suspension`, 소수의 tracking slot, 그리고 최대 2개의 `mandatory_scene_engines`만 남긴다.
- `_resolve_work_retrieval_focus()`는 guard가 비어 있거나 실패하면 이 fallback으로 떨어진다.

직접 `Probe A`의 opening `TR 2~6` block을 넣어 본 결과, fallback focus는 실제로 `VIP 전담 라인`, `exception account`, `이름 붙은 좌석`, `큰형 내부 계산표`, `priority response list`보다 `stakes`, `뉴스`, `foreshadow`를 더 먼저 잡았다. 즉 `Probe A`가 이번 wave에서 만든 구조 자산형 receipt가 `fallback work_focus`에서는 우선 surface가 아니다.

## Pass 2 — Why This Matters Downstream

`S3` 쪽 transport priority는 `episode_details`에 매우 우호적이다.

- `extract_episode_tactical()`의 기본 우선순위는 `episode_details > regex slice > full tactical_doc fallback`이다.
- `BlueprintConstraintCompiler`의 `must_focus`와 `stop_line` 추출도 이 흐름을 그대로 따른다.

이 뜻은 단순하다. `tactical_doc` 어딘가에 rich receipt prose가 살아 있어도, `S2`가 먼저 만든 `episode_details`가 느슨하면 `S3`는 그 느슨한 TL;DR을 먼저 먹는다. 이번 `Probe A`처럼 opening reward를 `돈 -> 좌석/접근권/우선 응답권`으로 바꿔 놓은 경우에는 이 우선순위가 바로 late-risk seam이 된다.

반대로, `episode_details`가 receipt-heavy 문장을 제대로 들고 있으면 `extract_episode_tactical()`은 그 line을 그대로 보존한다. synthetic probe로 `VIP 전담 라인`, `exception account`, `이름 붙은 좌석`, `큰형 내부 계산표`, `priority response list`를 `episode_details.details`에 넣었을 때, extractor는 이를 그대로 `must_focus` 후보로 반환했다. 즉 문제는 extractor가 아니라 `S2가 무엇을 TL;DR로 올려 주느냐`다.

## Pass 3 — Why Existing Guards Do Not Fully Save It

현재 `arc_ensemble`과 validator 계층은 `episode_details`가 완전히 비거나 너무 generic한 경우는 막지만, `Probe A`가 요구하는 `receipt preservation`까지 보장하진 않는다.

- `_collect_episode_detail_actionability_issues()`는 actionability 부족을 본다.
- `has_actionable_obligation_text()`는 비교적 느슨한 heuristic이다.
- `_check_episode_details_contract()`는 coverage/presence 중심이다.

즉 지금 guardrail은 `아예 빈 요약`은 막아도, `수익 증명`만 남기고 `VIP 전담 라인/예외 계좌/좌석/우선 응답권`을 빼먹은 요약까지 강하게 걸러 주는 구조는 아니다.

이건 지금 시점에서 충분히 중요하다. `Probe A`의 실험 포인트는 단순히 돈을 빨리 버는 opening이 아니라, `opening reward를 구조 자산으로 번역`하는 데 있기 때문이다. 만약 `S2`가 다시 이를 `이익 실현 + 주변 재평가` 정도로 축약하면, 이번 deepclone 실험의 핵심 delta가 `S3`에 닿기 전에 희미해진다.

## Operational Reading

이번 bounded audit의 해석은 다음과 같다.

- `Probe A`는 이제 정적 기준으로는 살아 있는 upstream 실험군이다.
- 하지만 `S2`는 아직 `Probe A opening truth`를 자동으로 지켜 주는 단계는 아니다.
- 따라서 다음 runtime wave를 열 경우, `S2 packet inspection` 없이는 결과 해석을 과신하면 안 된다.

권장 운영 해석:

- `지금 당장 S2를 뜯어고쳐야만 한다`: 아님
- `다음 canary 전에 S2 risk를 없는 셈 치고 넘어간다`: 비추천
- `다음 canary를 열되 S2-generated episode_details/work_focus/must_focus를 watchpoint로 둔다`: 추천

## Recommended Next Unit

다음 한 단위는 둘 중 하나다.

1. `Probe A bounded canary`를 열되 `S2 episode_details / work_focus / S3 must_focus`만 증거 채집 대상으로 추가
2. 그 전에 `Probe A opening receipt preservation`만 겨냥한 소형 `S2 hardening proposal`을 문서화

이번 audit만 놓고 보면, 우선순위는 `1`이 더 높다. 이유는 현재 seam이 `실제 stop-ship blocker`라기보다 `runtime observation required` 성격에 가깝기 때문이다.
