# T1. Stage2 Upstream Specificity — Blueprint Clarity/Density 기여도 조사

Date: 2026-03-25
Lane: T1 (Stage2 Upstream Specificity)
Master Order: `docs/2026-03-25/bp-clarity-density-structural-improvement-4terminal-master-order.md`
Status: final (3-pass audited)

## 1. Governing Question

Stage 3 blueprint의 선명도(clarity)와 밀도(density)가 Stage 2 페이로드 품질에 의해 상한이 걸려 있는가?

## 2. Evidence Surfaces

### 2.1 Code Surfaces (직접 읽음)
- `modules/core/response_schemas.py` L347-497 — `ARC_DESIGN_SCHEMA`
- `modules/domain/agents/arc_ensemble.py` L1-100 — Arc 후보 생성
- `modules/domain/agents/four_phase_arc_generator.py` L1-100 — 3단계 Arc 파이프라인
- `modules/domain/agents/four_phase_arc_runtime.py` L1076-1078 — `episode_details` 보존
- `modules/domain/agents/blueprint_constraint_compiler.py` L1-410 — 제약 블록 컴파일
- `modules/domain/agents/blueprint_ensemble.py` L215-1020 — Blueprint 생성 프롬프트 조립
- `modules/core/tactical_utils.py` L1-74 — `extract_episode_tactical()` 추출 로직
- `modules/core/stage2_finalizer.py` L1045-1058 — `constraint_summary` 후처리
- `modules/core/stage3_orchestrator.py` L250-400 — Stage 3 arc_data 소비 흐름
- `config/prompts/ensemble.yaml` L264-304 — `BLUEPRINT_GENERATION_PROMPT` 템플릿

### 2.2 Artifact Surfaces (직접 읽음)
- `projects/canary_0325/project_data.db` → `anchors.arcs` — 실측 Arc 1/2 페이로드
- `projects/canary_0325/plans/arcs/arc_001.txt`, `arc_002.txt` — 저장 형태 확인
- `projects/canary_0325/plans/blueprints/blueprint_0005.txt` — 생성된 Blueprint 실물 비교
- `projects/canary_0325/logs/artifacts/stage3/ep_0007/` — EP7 final_blueprint JSON

## 3. Findings

### F-1. tactical_doc은 이미 narrative-grade 선명도를 가진다

| Arc | tactical_doc 길이 | 화당 평균 | 상태 브래킷 | 구체 수치/이름 |
|-----|-----------------|---------|-----------|-------------|
| Arc 1 (ep1-4) | 3,477자 | ~870자 | `[시작 상태]`/`[종료 상태]` 전화 완비 | 20억 원, SW인베스트먼트, WTI 6월물, 박성호, 한정호, 한태준, 한태민 |
| Arc 2 (ep5-9) | 4,627자 | ~925자 | 전화 완비 | 15억 원, 3배 레버리지, 한미증권, 에콰도르, 이란 핵, VIP룸 |

- 각 에피소드 섹션에 위치, 소지품, 심리/신체 상태가 `[시작 상태]`/`[종료 상태]` 태그로 명확히 기재
- 특정 금액, 기관명, 인물명, 물리적 장소, 심리적 상태 변화가 내러티브 수준으로 서술
- **결론**: tactical_doc 자체의 선명도는 blueprint가 필요로 하는 수준 이상

### F-2. episode_details는 존재하지만 tactical_doc의 부분집합

| Arc | episode_details | 화당 항목 수 | 항목 평균 길이 |
|-----|----------------|------------|-------------|
| Arc 1 | 4화 × 2항목 = 8항목 | 2 | ~50자 |
| Arc 2 | 5화 × 2항목 = 10항목 | 2 | ~50자 |

- `episode_details`는 `ARC_DESIGN_SCHEMA`에서 **optional** (required 아님)
- LLM(Gemini)이 생성하되, 항상 보장되지 않음
- 실측: 양 Arc 모두 생성됨 — 화당 2개 bullet, 각 30-80자
- 내용은 tactical_doc의 압축 요약이며 **tactical_doc에 없는 고유 정보를 추가하지 않음**
- `extract_episode_tactical()`에서 Priority 1으로 사용되지만, tactical_doc regex 폴백이 동일 내용을 추출

### F-3. beat_sequence는 최소 안전망 (tertiary fallback)

| Arc | beat_sequence 수 | 화당 1줄 | 사용 시점 |
|-----|-----------------|---------|---------|
| Arc 1 | 4 | ~80자 | episode_details + regex 모두 실패 시에만 |
| Arc 2 | 5 | ~80자 | 동일 |

- 극도로 압축된 1줄 요약 — "제 5화: 한시우가 차트를 파기하고 여의도 한미증권 VIP룸으로 이동하여 박성호 PB와 대면함"
- **specificity 기여도 최소** — 있어도 blueprint 선명도에 거의 영향 없음
- **역할**: episode_details와 regex 모두 실패하는 극단적 경우의 안전망

### F-4. constraint_summary는 Arc 1에서 부재 (Stage 2 → Stage 3 제약 전달 갭)

| Arc | constraint_summary | 생성 메커니즘 |
|-----|--------------------|-----------|
| Arc 1 | **absent** (len=0) | `stage2_finalizer.py:1058` — "금지"/"MUST NOT"/"절대" 라인 추출 |
| Arc 2 | present (624자) | 동일 |

- `stage2_finalizer.py:1058`: constraint_block에서 "금지"/"MUST NOT"/"절대" 키워드가 포함된 줄만 추출
- Arc 1에서 해당 키워드 라인이 없으면 → constraint_summary = ""
- Stage 3의 `blueprint_constraint_compiler.py:92-93`이 이를 감지하고 로그를 남기지만 (**비차단**)
- **영향**: Arc 1의 blueprint은 Stage 2에서 전달된 명시적 금지선 없이 생성됨
- **이것이 선명도 상한인가?**: 아니다. tactical_doc이 충분히 구체적이므로 "무엇을 하라"는 잘 전달됨. 다만 "무엇을 하지 말라"는 초기 arc에서 약함.

### F-5. semantic_carryover는 양 Arc 모두 부재

- 양 Arc 모두 `semantic_carryover: None`
- blueprint_constraint_compiler의 `[Arc Semantic Carryover]` 섹션이 비어 있음
- **이것이 선명도 상한인가?**: 이것은 cross-arc 연속성 문제이지 per-episode 선명도 문제가 아님

### F-6. arc_focus 이중 주입 (비유해하나 비효율)

`blueprint_ensemble.py:215-238` `_resolve_blueprint_arc_focus()`:

1. `constraint_block.must_focus.content`에서 arc_focus 추출 (이미 episode_details 또는 tactical_doc에서 온 것)
2. **다시** episode_details를 순회하여 `[{ep_num}화 추가 사건 (Arc 단계 보강)]`으로 PREPEND

결과: 동일한 정보가 다른 포맷으로 2회 주입됨.

- 유해하지 않음 (강화 효과)
- 그러나 프롬프트 토큰을 불필요하게 소비 (~200-400자)
- max_chars=15,000 트렁케이션 내에서 의미 있는 새 정보가 아닌 중복

### F-7. Blueprint이 upstream specificity를 소화하는 방식 — **선명도 손실은 downstream에서 발생**

**결정적 비교**:

| 항목 | tactical_doc (Stage 2 입력) | Blueprint (Stage 3 출력) |
|------|--------------------------|------------------------|
| EP7 핵심 사건 | "시선이 남미 대륙의 한 지점에 머물렀다. '에콰도르...'" | scene_5: "다가올 시장의 파도를 직감한다" |
| EP7 형들 반응 | "한태준은 어이가 없다는 듯 헛웃음... 한태민은 '깡통 차고 울고불고 난리를 치며'" | scene_3: "한태준과 한태민이 15억 투자를 비웃는다" |
| EP5 차트 파기 | "차트 뭉치를 거침없이 파쇄기에 밀어 넣었다. 종이가 갈려나가는 소리와 함께..." | scene_2(blueprint_0005.txt): 동일 수준 유지 |

- EP7 blueprint의 scene_5가 "에콰도르"라는 **구체적 타깃명을 탈락**시키고 generic한 "시장의 파도"로 대체
- EP7 blueprint의 scene_3이 형들의 **구체적 대사/반응**을 요약 수준으로 축소
- 반면 EP5의 차트 파기 장면은 blueprint에서도 구체성이 유지됨

**해석**: upstream tactical_doc은 충분히 구체적이나, blueprint 생성 과정에서 **선택적으로 구체성이 희석**됨. 이 희석은 Stage 2 입력 부족이 아니라 Stage 3 생성/스키마/authority mixing 측에서 발생.

## 4. Confidence and Limits

- **Confidence**: 90%
  - tactical_doc/episode_details/beat_sequence의 구조와 내용은 코드 + 실측 데이터 양쪽에서 확인
  - 선명도 손실 비교는 EP5/EP7 2개 에피소드에 기반 — 전 에피소드 전수 비교는 미수행
  - constraint_summary 부재의 실질적 영향은 해당 에피소드의 REJECT 이력이 없으므로 간접 추론

- **Limits**:
  - 이 레인은 Stage 2 → Stage 3 입력 흐름만 다룸; Stage 3 내부의 authority mixing (T2), prevalidation (T3)은 범위 밖
  - 다른 장르(무협, 판타지 등)에서의 upstream specificity는 canary 데이터가 투자 장르 전용이므로 미확인
  - LLM의 episode_details 생성 안정성(항상 생성하는지 vs 간헐 누락)은 단일 canary로 결론 불가

## 5. Mandatory Final Lines

- **Dominant limiter in this lane**: `none` — Stage 2 upstream specificity는 현재 blueprint 선명도/밀도의 주 제한 요인이 아님. tactical_doc은 이미 narrative-grade이며, 선명도 손실은 downstream(Stage 3)에서 발생.
- **Best bounded improvement candidate in this lane**: `constraint_summary 강건화` — 현재 "금지/MUST NOT/절대" 키워드 매칭에만 의존하는 constraint_summary 추출을 개선하여 Stage 2 → Stage 3 금지선 전달의 안정성을 높이는 것. 이는 선명도보다는 정합성에 가까우나, Stage 2 측에서 가장 ROI 높은 단일 개선점.
- **Should this lane alone trigger a new SSOT**: `no`
