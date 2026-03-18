# Real Manuscript Quality Corpus Usage Direction 3-Pass Audit

Date: 2026-03-18
Status: final
Canonical Path: `docs/2026-03-18/real-manuscript-quality-corpus-usage-direction-3pass-audit.md`
Document Type: survey + direction audit
Commit State:
- Baseline Commit: `d4e96804`
- Baseline Dirty Summary: `dirty: tracked Stage 3 schema-fix surfaces and related tests/docs; untracked docs/2026-03-18/* and project artifacts`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`
Confidence Target: `95%`
Current Confidence: `96%`

## 1. Intent

- `docs/실물기반 사각지대 테스트/` 자료가 현재 시스템에서 실제로 사용되는지 확인한다.
- 저 자료를 "좋은 원고"의 기준 자산으로 재정의할 수 있는지 판단한다.
- 코드 수정 없이, 정적 조사 기반의 활용 방향만 문서화한다.

## 2. Scope

포함:
- `main_a.py`
- `modules/`
- `scripts/`
- `tests/`
- `docs/2026-03-17/별도 조사/ssot_integrated-survey.md`
- `docs/실물기반 사각지대 테스트/`

제외:
- 앱 실행
- pytest 실행
- 코드 수정
- 외부 웹 조사
- 새 데이터 생성

## 3. Baseline Facts

- `docs/실물기반 사각지대 테스트/`는 현재 22개 작품, 890개 회차 txt, 11개 YAML, 5개 프로파일 문서, 4개 클리프행어 문서, 4개 화간 연결 문서, 2개 분석/GT 문서로 구성되어 있다.
- 현재 런타임(`main_a.py`, `modules/`, `geuldobi-desktop/`, `config/`, `UI/`)에서 이 디렉토리의 자료를 직접 `import/load/read`하는 경로는 이번 조사 범위에서 확인되지 않았다.
- 직접 생산 경로는 `scripts/extract_manuscript_samples.py:31` 하나가 명확하다. 이 스크립트는 EPUB 원문에서 txt를 추출해 해당 디렉토리 아래 `원고/`에 저장한다.
- 완전한 사장 자산은 아니다. `scripts/investment_corpus_support.py:1953`와 `scripts/build_title_style_control_dataset.py:1`은 이런 류의 원고 코퍼스를 style-control 데이터셋으로 가공할 수 있는 오프라인 도구 계층이다.
- 기존 survey authority인 `docs/2026-03-17/별도 조사/ssot_integrated-survey.md:195`는 이미 이 디렉토리를 "좋은 원고 정의 인프라"의 원재료 저장소로 규정하고, 28개 활용 경로를 열어 둔 상태다.

## 4. Pass 1 - Live Inventory

### 4.1 자료군 인벤토리

| 자료군 | 현재 규모 | 현재 직접 시스템 사용 | 가장 자연스러운 역할 |
| --- | --- | --- | --- |
| 실물 원고 txt | 22작품 / 890화 | 없음 | 오프라인 기준 코퍼스, 벤치마크, style-control 입력 |
| few-shot YAML | 11개 | 없음 | 프롬프트 exemplar bank, NPC 대사 bank |
| 문체 프로파일 | 5개 | 없음 | 장르별 정량 기준, anti-slop 기준 |
| 클리프행어 문서 | 4개 | 없음 | Director 상업성/엔딩 훅 rubric |
| 화간 연결 문서 | 4개 | 없음 | Stage 3/4 연결성 rubric |
| 모순 GT / 분석 문서 | 2개 | 없음 | validator recall benchmark, Director contradiction calibration |

### 4.2 실제 사용 현황 판정

판정은 둘로 나눠야 한다.

1. **직접 런타임 사용**
   현재는 없다.

2. **시스템이 바로 받아먹을 수 있는 인접 슬롯**
   이미 많다.

### 4.3 현재 시스템 안의 수용 슬롯

현재 시스템은 이미 아래 신호를 hardcoded heuristic으로 다루고 있다.

- 화 시작 후킹력 / 클리프행어 효과: `modules/core/quality_constitution.py:140`
- 장르별 품질 피드백과 투자물 논리성/클리프행어 가이드: `modules/validation/scoring_validator.py:1087`
- 직전 화 연결 앵커, closing hook, 씬 연결 강제: `modules/core/writer_template.py:64`
- 직전 화 cliffhanger 무시 금지, ending_hook 강제: `modules/core/constitutional_checker.py:110`
- blueprint의 ending_hook 존재 점검: `modules/core/cross_agent_verifier.py:202`
- 직전 화 연결 점수와 ending hook 존재 점수: `modules/core/confidence_calibration.py:199`, `modules/core/confidence_calibration.py:374`

즉, 현재 상태는 "자료가 없어서 못 쓴다"가 아니라 "자료를 시스템이 먹기 좋은 작은 계약으로 증류해 두지 않았다"에 가깝다.

### 4.4 Side-Effect Map

이번 조사에서 확인된 side-effect는 아래뿐이다.

- `scripts/extract_manuscript_samples.py`가 원고 txt와 `manifest.json`을 생성한다.
- `scripts/investment_corpus_support.py`와 `scripts/build_title_style_control_dataset.py`는 코퍼스를 JSONL/manifest로 가공하는 오프라인 tooling 경로다.
- 런타임 품질 판정, Stage 3/4 생성, Director 심사에 이 디렉토리 원문이 직접 유입되는 경로는 확인되지 않았다.

## 5. Pass 2 - Semantic Classification

이 디렉토리는 단순 참고자료 폴더가 아니다. 기능적으로는 아래 5층으로 분류하는 편이 맞다.

### 5.1 Raw Reference Corpus

- `원고/`는 "잘 팔리는 실물 원고의 분포"를 보여 주는 원재료다.
- 다만 이것을 절대적 gold truth로 취급하면 안 된다.
- 이유는 실물 원고 자체도 모순과 편차를 포함하기 때문이다. 이를 보여 주는 반증이 바로 `contradiction_ground_truth_dataset.md`다.

정리하면:
- **문장 그대로의 절대 정답**은 아님
- **성공한 상업 서사의 경험적 분포**를 주는 기준 데이터는 맞음

### 5.2 Distilled Quality Rubrics

아래 문서는 원고를 이미 1차 증류한 품질 기준서다.

- `cliffhanger_pattern_taxonomy.md`
- `분석결과_회차간_연결패턴_분석.md`
- `투자물_문체_정량_프로파일.md`
- `*_문체프로파일.md`
- `*_클리프행어.md`
- `*_화간연결.md`

이 레이어는 raw text보다 훨씬 시스템 친화적이다. 비용도 적고, prompt 오염 위험도 낮다.

### 5.3 Benchmark / Ground Truth Layer

- `contradiction_ground_truth_dataset.md`는 "좋은 원고처럼 보이지만 실제로는 어디서 모순이 나는가"를 정리한 예외 데이터다.
- 이건 생성 보조보다 검증 보조에 더 가치가 크다.
- 즉, 이 자료의 1순위 활용처는 Writer가 아니라 Validator/Director 쪽이다.

### 5.4 Prompt Exemplar Layer

- `few-shot-bank/*.yaml`은 직접 런타임에 연결되어 있지 않지만, 구조상 가장 쉽게 prompt asset으로 전환될 수 있다.
- 특히 NPC 대사 bank는 "좋은 원고"의 기준을 문체가 아니라 **역할별 발화 습관**으로 분해해 준다는 점에서 가치가 높다.

### 5.5 Offline Data Engineering Layer

- `scripts/investment_corpus_support.py`
- `scripts/build_title_style_control_dataset.py`

이 둘은 지금 당장 런타임 통합을 하지 않더라도, 코퍼스를 supervised-tuning 혹은 style-control JSONL로 변환할 수 있는 기존 자산이다.

## 6. Pass 3 - Direction

## 6.1 핵심 판단

`docs/실물기반 사각지대 테스트/`는 현재 **런타임 미사용**이 맞다.

하지만 운영 판단으로는 "죽은 자료"가 아니라 아래처럼 보는 게 더 정확하다.

- **현재 상태**: 오프라인 품질 기준 코퍼스
- **빠진 것**: runtime-consumable distilled contract
- **따라서 필요한 것**: raw direct wiring이 아니라 증류 계층

## 6.2 가장 좋은 사용 순서

권장 순서는 아래다.

1. **평가에 먼저 쓴다**
   raw corpus를 생성 프롬프트에 바로 넣기보다, Director/Validator의 rubric 보강에 먼저 쓴다.
2. **증류된 기준만 런타임에 넣는다**
   taxonomy, profile, GT를 작은 규칙/예시/threshold 자산으로 바꿔 넣는다.
3. **raw 원고는 오프라인 벤치마크로 유지한다**
   실제 원고 본문은 benchmark, calibration, fine-tuning 입력으로만 쓴다.
4. **생성 직접 주입은 맨 마지막 옵션으로 둔다**
   비용, 잡음, 과적합, 문체 모사 부작용이 크기 때문이다.

이 순서가 좋은 이유는 두 가지다.

- 품질 개선 ROI가 제일 높다.
- "좋은 원고의 분포"는 살리면서도 원문 직접 주입의 잡음을 피할 수 있다.

## 6.3 당장 써먹는 방법

### A. Judge-First Calibration

가장 먼저 써야 할 방식이다.

- 클리프행어 taxonomy를 Director commercial appeal rubric에 연결
- 화간 연결 분석을 Stage 3/4 continuity rubric에 연결
- 문체 프로파일을 anti-slop drift 기준으로 연결
- contradiction GT를 validator recall benchmark로 연결

장점:
- 생성 품질에 바로 영향
- 원문 대량 주입이 필요 없음
- 디렉터 주권주의와 잘 맞음

### B. Quality Threshold Calibration

현재 `quality_constitution.py`와 `scoring_validator.py`의 상당수 기준은 유의미하지만 경험적 범위가 약하다.

실물 자료로 아래를 보정할 수 있다.

- 문장 길이 분포
- 대사 비중
- opening hook 구성 요소
- ending hook 강도 분포
- 장르별 감정/설명/대화 비율

즉, "좋은 원고의 기준"을 감각적 문장 대신 **관측된 범위**로 낮출 수 있다.

### C. Blind Benchmark Harness

생성계에 직접 넣지 않고도 강력하다.

- 실물 원고 1편
- 생성 원고 1편
- 동일 rubric으로 blind 비교

이 방식은 "좋은 원고처럼 느껴지는가"를 운영 수준에서 계속 검증할 수 있다.

특히 다음을 측정하기 좋다.

- AI slop 감지
- 화간 연결 매끄러움
- cliffhanger 기대감
- 캐릭터 말투 분리
- 투자물 특유의 논리성/쾌감 균형

### D. Dialogue Voice Bank

`few-shot-bank/npc_dialogue_*.yaml`은 Writer 본문 전체보다 **캐릭터 음성 분리**에 더 직접적이다.

가장 좋은 활용은:

- NPC role-conditioned exemplar
- Director의 대사 품질 점검 기준
- Character voice profile benchmark

즉, 이 자료는 "문체 예쁘게 쓰기"보다 "인물 말이 살아 있는가" 쪽에서 더 잘 먹힌다.

### E. Style-Control / Tuning Dataset

이미 `scripts/investment_corpus_support.py`와 `scripts/build_title_style_control_dataset.py`가 존재하므로, 장기적으로는 가장 큰 활용처가 될 수 있다.

다만 이건 우선순위가 가장 높지는 않다.

이유:
- 데이터 정제 비용이 큼
- 장르별 확장 설계가 필요함
- raw corpus의 잡음을 먼저 정리해야 함

즉, 이건 "있으면 매우 강력"하지만 "당장 붙일 것"은 아니다.

## 7. Recommended Operating Model

권장 모델은 다음 한 줄로 요약된다.

**`실물기반 사각지대 테스트/`는 런타임 입력 폴더가 아니라, 좋은 원고 기준을 추출하는 오프라인 품질 코퍼스로 운영한다.**

이 모델에서의 역할 분담:

- raw 원고: 분포/예시/벤치마크 원천
- 프로파일/분석/분류 문서: 런타임에 들어갈 1차 증류 기준
- YAML bank: prompt exemplar 자산
- contradiction GT: 검증기 성능 측정 자산
- corpus tooling scripts: 장기적 데이터셋화 경로

## 8. What Not To Do

아래는 비권장이다.

- raw 원고 890화를 runtime prompt에 직접 붙이는 방식
- "실물 원고 = 무조건 정답"으로 취급하는 방식
- few-shot YAML을 검증 없이 곧바로 Writer prompt에 대량 주입하는 방식
- corpus 자료를 하나의 거대한 SSOT처럼 취급하는 방식

이 자료는 SSOT가 아니라 **evidence-rich source corpus**에 가깝다.

## 9. Practical Next Moves

코드 수정 없이 방향만 정리하면, 다음이 가장 합리적이다.

1. `좋은 원고 기준`을 5축으로 다시 묶는다.
   - opening hook
   - ending hook / cliffhanger
   - 회차 간 연결
   - 문체/리듬/대사 비율
   - 모순/정합성
2. 각 축마다 raw corpus가 아니라 distilled source를 지정한다.
   - taxonomy
   - profile
   - GT
   - YAML exemplar
3. 이후 실제 구현이 필요해질 때만 execution SSOT를 따로 세운다.

즉, 지금 단계의 최선은 "이 자료를 어디에 꽂을지"보다 먼저 "어떤 기준으로 증류해서 꽂을지"를 명확히 하는 것이다.

## 10. 3-Pass Audit Summary

### Pass 1 - Structure and Scope

- 문서 유형을 survey + direction audit로 고정했다.
- 조사 범위와 제외 범위를 분리했다.
- direct use와 potential use를 분리해 혼동을 줄였다.

### Pass 2 - Evidence and Consistency

- 직접 런타임 미사용 판정은 live grep 기준으로 재확인했다.
- producer/tooling 경로와 runtime slot을 분리해 기록했다.
- 기존 `ssot_integrated-survey.md`의 활용 주장과 현재 live workspace를 충돌 없이 정리했다.

### Pass 3 - Execution and Readability

- "써먹을 방법이 있나"에 대해 단순 예/아니오가 아니라 우선순위 있는 운영 방향을 제시했다.
- raw direct wiring을 비권장으로 명시했다.
- 다음 단계가 execution SSOT가 아니라 distilled criteria definition임을 명확히 했다.

최종 판단:

- **현재 직접 사용은 없음**
- **전략적 가치는 높음**
- **가장 좋은 활용은 생성 직접 주입이 아니라 평가/보정/벤치마크 우선**
