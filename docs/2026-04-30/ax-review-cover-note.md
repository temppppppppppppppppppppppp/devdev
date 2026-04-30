# AX 검토 요청 커버노트

작성일: 2026-04-30
상태: 3pass 패킷 감리 완료 제출본
연결 이슈: GitHub #145, "AX팀 제공 자료 제작 및 3pass 감리"

## 전달용 메일 초안

안녕하세요, AX개발팀 윤정환님.

글도비 LLM pipeline 검토를 위해 요청 주신 자료를 아래와 같이 정리했습니다.

전달 자료:

1. `ax-system-architecture.md`
   - 시스템 구성도
   - Stage2/Stage3/Stage4 역할
   - Director/runtime/settlement 권한 분리
   - 장기기억/연속성 계층 구조

2. `ax-data-flow.md`
   - 주요 데이터 흐름
   - Stage4 생성/검증/재시도/정착 흐름
   - DB/log/artifact observability 흐름
   - cache/session sidecar 흐름

3. `ax-model-cost-token-surface.md`
   - 사용 모델/라우팅 정보
   - Stage4 local cost/token snapshot
   - context-cache evidence
   - 비용/응답지연/토큰 최적화 질문 목록

보조 근거 문서:

- `ax-bottleneck-deepdive-survey.md`
- `ax-long-memory-continuity-standards-survey.md`

검토 요청의 핵심은 "장기기억이 없다" 또는 "문체 polishing만 필요하다"가 아닙니다.

현재 시스템은 layered memory architecture를 이미 갖추고 있고, 감독형 실행 기준 15화 draft chain까지 생산했습니다. 다만 production-trust 관점에서는 아래 문제가 남아 있습니다.

1. Stage4 retry/post-select conflict로 인한 비용과 지연
2. Director verdict, runtime route verdict, settlement verdict의 권한 분리와 observability
3. Stage3/Stage4 accepted manuscript / blueprint lineage freshness
4. context cache / session memory의 비용 효율 및 stale-source suppression 검증
5. final accepted context, rollback sidecar, frontier stale contract 같은 authority-boundary hardening

따라서 AX팀에는 아래 관점의 리뷰를 부탁드리고 싶습니다.

- LLM pipeline 구조상 어디서 비용과 지연이 가장 크게 누적되는지
- 현재 Vertex/Gemini 모델 routing과 fallback/caching 정책이 비용 대비 적절한지
- cache/session memory를 canon이 아닌 sidecar로 쓸 때 필요한 telemetry와 invalidation fingerprint가 무엇인지
- post-select conflict를 더 이른/저렴한 단계에서 검출할 수 있는지
- AX 검토에 필요한 추가 redacted trace가 무엇인지

원문 원고, raw prompt, 비식별화되지 않은 LLM I/O, secret-like local config는 기본 제출 범위에서 제외했습니다. 필요하시면 redacted aggregate 또는 selected trace 형태로 추가 준비하겠습니다.

감사합니다.

## 내부 발송 메모

먼저 공유할 파일:

- `docs/2026-04-30/ax-system-architecture.md`
- `docs/2026-04-30/ax-data-flow.md`
- `docs/2026-04-30/ax-model-cost-token-surface.md`

상세 근거로 보관할 파일:

- `docs/2026-04-30/ax-bottleneck-deepdive-survey.md`
- `docs/2026-04-30/ax-long-memory-continuity-standards-survey.md`

기본적으로 보내지 않을 파일:

- `projects/0_카나리아/0_합본*.txt`
- raw project DB
- raw prompt log
- 비식별화되지 않은 `llm_io.jsonl`
- local environment file

## 짧은 설명 문장

짧은 framing이 필요하면 아래 문장을 사용합니다.

> 글도비는 장기연재용 layered memory architecture를 상당 부분 갖췄지만, production-trust 단계로 보려면 strict 5-arc proof와 cache/session causal benchmark, 그리고 일부 authority-boundary hardening이 더 필요합니다.

## 특히 강조할 검토 질문

1. 어떤 Stage4 check를 비싼 generation 이전으로 옮길 수 있는가?
2. 어떤 role에 실제로 `gemini-3.1-pro-preview`가 필요한가?
3. 현재 cache policy는 Vertex billing 기준으로 비용상 이득이 있는가?
4. stale-source reuse를 막으려면 어떤 cache lineage field가 필요한가?
5. API latency, retry overhead, continuation overhead, cache behavior를 분리하려면 어떤 telemetry가 빠져 있는가?
6. AX팀이 유의미하게 진단하려면 최소 어떤 redacted trace가 필요한가?

## 패킷 3pass 감리

1차 - 구조:

- 외부 메일 응답 형태에 맞췄습니다.
- AX팀이 요청한 세 가지 산출물을 명시했습니다.
- source survey는 메일 본문이 아니라 보조 근거로 분리했습니다.

2차 - 안전:

- raw prompt, 원고 전문, secret, raw DB를 기본 공유에서 제외했습니다.
- 필요 시 redacted trace를 별도로 준비한다고 명시했습니다.

3차 - 유용성:

- 바로 보낼 수 있을 정도로 짧게 유지했습니다.
- 요청 사항이 AX팀의 지원 범위인 pipeline/cost/latency/token review와 직접 연결됩니다.

추정 확신도: 96%
