# Geuldobi V2 Static Improvement Discovery Full Survey Audit Order

Date: 2026-03-18
Status: final (3-pass audited)
Mode: static survey only
Audience: OPUS
Canonical Path: `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-full-survey-audit-order.md`
Temp Mirror Path: `not applicable`
Temp Queue Snapshot: `docs/temp/ contains README.md only; no active execution SSOT mirrors`

Commit State:
- Baseline Commit: `d4e96804898491ae67085a327bf35b080ced4364`
- Baseline Dirty Summary: `dirty: 10 tracked, 7 untracked, 4 deleted; hotspots: stage3 schema fixes, projects/0_260318, docs/2026-03-11 PDFs, docs/2026-03-18/OPUS`
- Resume Commit: `same-as-baseline`
- Resume Drift Summary: `none`

## 1. Order Intent
이 오더의 목적은 현재 글도비 시스템 전반에서:

- 사용자가 이미 알고 있는 문제를 재확인하는 데 그치지 않고
- 사용자가 아직 질문하지 않았거나 상상하지 못했을 가능성이 큰 개선점
- 구조적, 운영적, 진단적, 계약적, UX적, 거버넌스적 개선 기회

를 정적 조사만으로 최대한 많이, 그리고 evidence-backed 방식으로 발굴하는 것이다.

핵심은 "known issue 재진술"이 아니라 "unknown unknown improvement discovery"다.

## 2. Absolute Guardrails
다음은 절대 위반 금지다.

1. 코드 수정 금지
   - `apply_patch`, 파일 덮어쓰기, 포맷터 실행, 자동수정, 코드 생성 패치 전부 금지
2. 런타임 실행 금지
   - `python main_a.py`, `pytest`, 서버 실행, 앱 실행, 빌드, 마이그레이션, live run 전부 금지
3. 상태 변이 금지
   - DB write, 로그 재생성, 산출물 재생성, 캐시 갱신, temp queue 생성/갱신 금지
4. 실행문서화 과잉 금지
   - execution SSOT, execution roadmap, execution closure를 새로 만들지 말 것
   - 이번 오더는 조사 전용이다
5. 외부 웹 조사 금지
   - 이번 오더는 현재 로컬 워크스페이스 정적 조사만 사용
6. 서사 파이프라인 작업으로 확장 금지
   - 작품 승인/기획/서사 수정으로 넘어가지 말 것

허용되는 것은 읽기 전용 조사뿐이다.

## 3. Allowed Evidence Sources
다음 소스만 읽기 전용으로 사용하라.

- `main_a.py`
- `modules/`
- `scripts/` 중 읽기/검사용
- `tests/`를 behavioral clue 용도로만
- `UI/`
- `geuldobi-desktop/`
- `docs/implementation/`
- `docs/20xx-xx-xx/`의 시스템 감사/조사 문서
- `projects/*/logs/`, `projects/*/plans/`, `projects/*/artifacts/`의 기존 생성 산출물
- `git status --short`, `git rev-parse HEAD` 같은 읽기 전용 git 메타데이터

기존 로그/산출물 열람은 허용되지만, 새 런을 만들어 증거를 갱신하면 안 된다.

## 4. Scope
이번 조사 범위는 다음을 모두 포함한다.

1. 코드 구조와 책임 분산
2. Stage 간 계약 정합성
3. 상태/사실/메타데이터의 authority 충돌 가능성
4. 재시도, fallback, quality gate, validation, scoring의 정적 설계
5. 로깅/관측성/사후진단 가능성
6. 운영 문서와 실제 코드의 drift 가능성
7. UI/Operator 경험의 정적 마찰 요소
8. dead surface, stale alias, low-value wrapper, 중복 추상화
9. 테스트 설계의 신호 품질
10. 향후 유지보수 비용을 키우는 비직관적 구조적 리스크

## 5. Explicit Non-Goals
다음은 이번 조사에서 하지 않는다.

- 실제 패치
- 실제 리팩터
- 성능 벤치마크 실행
- 실전 테스트 병행
- 모델 교체 실험
- 사용자가 이미 지정한 단일 버그의 수리
- 외부 서비스 비교 조사
- "당장 구현하라" 수준의 execution queue 생성

## 6. Primary Question
아래 질문에 답하는 것이 이번 오더의 본질이다.

"현 시스템에서, 사용자가 아직 명시적으로 요구하지 않았지만 장기적으로 큰 이득을 줄 수 있는 개선점은 무엇인가?"

이 질문에 답할 때 반드시 다음 성격의 아이디어를 우선 탐색하라.

- 구조 단순화
- 계약 명확화
- authority 일원화
- 실패 진단력 강화
- operator 실수 예방
- 문서/프로세스 드래그 제거
- dead surface 제거
- low-signal complexity 축소
- retry economics 개선
- model/provider drift 방어

## 7. Investigation Method
아래 순서로 진행하라.

### Pass A. System Topography
시스템의 주요 surface와 authority를 먼저 고정하라.

- entrypoint
- stage orchestration
- agent layer
- schema/model layer
- validation layer
- persistence/logging layer
- operator/UI layer
- desktop/app bridge layer
- process/document governance layer

이 단계에서는 "어디가 시스템의 진짜 결정권을 가지는가"를 먼저 정리하라.

### Pass B. Contract and Authority Audit
다음을 정적으로 추적하라.

- 하나의 사실을 여러 군데에서 따로 정의하는가
- schema, model, validator, prompt, sink가 서로 다른 진실을 말하는가
- final verdict, score, quality_risk 같은 핵심 메타가 sink마다 다르게 해석될 여지가 있는가
- Python과 LLM의 책임 경계가 흐려지는 지점이 있는가
- runtime truth와 document truth가 충돌할 위험이 있는가

### Pass C. Existing Failure History Mining
새 실행은 금지하되, 기존 로그와 산출물에서 반복 패턴을 찾아라.

- deterministic failure가 retry burn으로 위장되는가
- warning이 PASS로 흘러 operator가 놓치기 쉬운가
- 반대로 benign advisory가 과도한 risk flag를 남기는가
- artifact 저장은 성공했지만 metadata가 어긋나는 경우가 있는가
- UI 표시와 실제 내부 판정이 어긋날 수 있는가

### Pass D. Unknown-Unknown Discovery Lenses
다음 렌즈를 반드시 각각 독립적으로 적용하라.

1. `authority compression`
   - 동일 진실을 더 적은 surface에서 관리하도록 줄일 수 있는가
2. `failure diagnosability`
   - 실패 원인이 현재보다 훨씬 빨리 보이게 만들 수 있는가
3. `operator cognition`
   - 사용자가 지금보다 덜 헷갈리게 할 수 있는가
4. `surface retirement`
   - 실제 가치 없는 호환용/죽은 surface를 제거할 수 있는가
5. `contract hardening`
   - schema/model/prompt/validator 경계 중 어디가 가장 취약한가
6. `maintenance drag`
   - 앞으로 작업할수록 비용이 기하급수적으로 커질 구조는 어디인가
7. `log truth`
   - 나중에 사고가 나면 현재 로그만으로 사실을 복구할 수 있는가
8. `quality semantics`
   - PASS, PASS_WITH_FIX, PASS_WITH_WARNING, REJECT, FAILED의 의미가 surface마다 흐려지는가
9. `doc-process drag`
   - 문서 체계가 오히려 운영 판단을 늦추거나 왜곡하는가
10. `surprising leverage`
   - 작은 규약 변경만으로 큰 운영 개선을 낼 수 있는 지점이 있는가

### Pass E. Opportunity Ranking
발굴한 개선점을 단순 나열하지 말고 다음 기준으로 정렬하라.

- leverage
- novelty
- evidence density
- blast radius
- reversibility
- operator value
- implementation independence

## 8. Required Deliverables
이번 오더의 최종 산출물은 아래 2개다.

1. `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-evidence-manifest.md`
2. `docs/2026-03-18/OPUS/geuldobi-v2-static-improvement-discovery-3pass-audit.md`

둘 다 human-facing 문서이므로 3-pass audit과 95% confidence gate를 거친 뒤 저장하라.

이번 오더에서는 다음 문서를 만들지 말 것.

- execution SSOT
- execution roadmap
- execution closure
- temp mirror

## 9. Deliverable Structure
최종 `3pass-audit` 문서는 최소 아래 구조를 가져야 한다.

1. 조사 목적과 범위
2. 방법론과 금지사항 준수 여부
3. 시스템 authority map 요약
4. top surprising improvements
5. ranked opportunity inventory
6. cross-cut risk and drag patterns
7. open questions and confidence limits
8. next-step suggestions

`evidence-manifest`는 최소 아래를 포함해야 한다.

- inspected surfaces
- key files
- key docs
- key logs/artifacts
- claim-to-evidence mapping

## 10. Opportunity Inventory Contract
각 개선점은 아래 필드를 반드시 포함하라.

- `ID`
- `Title`
- `Category`
- `Why It Is Non-Obvious`
- `Evidence`
- `Affected Surfaces`
- `Expected Upside`
- `Risk / Tradeoff`
- `Static Confidence`
- `Suggested Next Verification`
- `Priority`

중요:
- "좋아 보인다" 수준의 감상은 금지
- 반드시 파일/문서/로그 anchor를 붙여라
- 근거가 약하면 사실처럼 쓰지 말고 hypothesis로 표기하라

## 11. Minimum Acceptance Criteria
이번 조사는 아래를 만족해야 완료로 본다.

1. evidence-backed opportunity 최소 12개 이상
2. 그중 `non-obvious` 또는 `counterintuitive`로 볼 만한 항목 최소 5개 이상
3. 코드 구조 외에 operator/process/observability 성격 항목 최소 3개 이상
4. current known issue의 파생 재진술이 아닌 항목이 상위권에 포함될 것
5. "왜 이게 지금까지 잘 안 보였는가" 설명이 있을 것
6. code modification 없이 완료될 것
7. live run 없이 완료될 것

## 12. Bias Controls
다음 편향을 의식적으로 피하라.

- 최근 Stage 3 이슈에 과도하게 고정되는 편향
- 코드 리팩터만 개선이라고 보는 편향
- "테스트 더 추가" 같은 상투 답변으로 도망가는 편향
- evidence 없는 architecture grand rewrite 제안
- implementation 욕구 때문에 static-only 제약을 무시하는 편향

## 13. Suggested High-Value Targets
우선순위가 높은 정적 조사 타깃은 아래다.

1. stage orchestration 간 메타데이터 의미 정합성
2. schema-model-validator-prompt 계약의 다중 authority
3. sink 간 final verdict, score, risk projection 정합성
4. retry/fallback/advisory의 semantic drift
5. operator-visible UI 문구와 내부 사실의 간극
6. project artifact truth vs metadata truth
7. docs/process governance가 실제 구현 판단에 주는 friction
8. dead compatibility surface와 stale doc authority
9. observability gap 때문에 root cause 시간이 길어지는 구조
10. low-value complexity가 큰 영역

## 14. Save Rules
문서를 저장할 때는 아래를 지켜라.

- canonical only
- `docs/temp/` mirror 금지
- draft -> pass1 -> pass2 -> pass3 -> confidence>=95 -> final save
- confidence 95% 미만이면 final save 금지

## 15. Final Instruction To OPUS
당신의 임무는 "문제를 고치는 사람"이 아니라 "아직 질문되지 않은 개선 기회를 발굴하는 정적 감사자"다.

이번 오더에서는:

- 패치하지 말고
- 실행하지 말고
- 대신 깊게 읽고, 연결하고, 분류하고, 우선순위를 세워라

가장 좋은 결과물은 "이미 알고 있던 문제를 길게 설명한 문서"가 아니라,
"왜 이 개선점이 지금까지 잘 안 보였는지까지 설명하는, 놀라움이 있는 조사 결과"다.
