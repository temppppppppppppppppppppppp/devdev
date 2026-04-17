# `불행을 보는 재벌집 손자` Session Context의 `글도비` 전용 활용 아이디어 보고서

Date: 2026-04-17
Status: final (3-pass audited idea report)
Canonical Path: `docs/2026-04-17/bulhaeng-session-context-geuldobi-transfer-idea-report.md`
Source Anchors:
- `C:\Users\wjjo\Desktop\재료 생산 R&D 랩\docs\2026-04-17\bulhaeng-chaebol-ep0052-0101-session-context.md`
- `C:\Users\wjjo\Desktop\글도비\AGENTS.md`
- `C:\Users\wjjo\Desktop\글도비\README.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-01\active-temp-execution-roadmap.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-14\0_0-stage3-state-arbiter-envelope-bounded-remediation-execution-ssot.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-14\0_0-stage234-global-authority-alignment-bounded-remediation-execution-ssot.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-16\stage234-s2-s3-s4-authority-alignment-post-merge-current-head-adversarial-3pass-audit.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-13\stage3-cross-pc-proof-rerun-handoff-context.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-16\stage234-arc23-postpatch-proof-session-context.md`
- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-17\stage234-arc23-stage34-single-episode-demo-frontier-context.md`
Document Audit:
- Pass 1: complete
- Pass 2: complete
- Pass 3: complete
- Estimated Confidence: 96%

## 1. Executive Verdict

`불행... session context`를 `글도비`에서 가장 잘 써먹는 방식은 `콘텐츠 donor`가 아니라 `운영 복구용 governance donor`로 이식하는 것이다.

핵심은 아래 한 줄이다.

- `execution SSOT`와 `active roadmap`이 이미 lane truth를 쥐고 있다면, `session context`는 그 위에 얹는 얇은 `세션 복구 레이어`로 쓰는 것이 가장 효율적이다.

즉 `글도비`에서의 최적 활용은:

1. 이번 세션이 어디서 시작했는지
2. 이번 세션에서 실제로 무엇이 닫혔는지
3. 무엇이 staged지만 아직 active가 아닌지
4. 다음 PC/다음 세션에서 정확히 어떤 순서로 재개해야 하는지

를 한 문서에 잠그는 것이다.

## 2. Donor 문서에서 가져올 진짜 가치

`불행... session context`의 힘은 요약력 자체보다 `복구 질서`에 있다. 실제로 그 문서는 아래 네 축을 동시에 잠근다.

- 세션 시작점
- 이번 세션의 closed span
- 이번 세션에서 새로 남긴 산출물
- 다음 세션의 deterministic resume order

이 패턴은 `글도비`에도 바로 맞는다. 이유는 `글도비` 역시 이미 아래 조건을 갖추고 있기 때문이다.

- 강한 canonical doc 문화
- `3pass 감리 후 저장` 규칙
- `execution SSOT + temp mirror + active roadmap` 구조
- `proof-pending / operator-gated` 같은 비승격 상태 관리
- cross-PC handoff와 bounded proof note를 부분적으로 이미 사용 중인 운영 습관

즉 `글도비`는 이 패턴을 받아들이기 위한 토양이 이미 있다. 부족한 것은 `세션 전체를 복구하는 상위 contract`의 정규화다.

## 3. 현재 `글도비`에서 이미 있는 것과 없는 것

### 이미 있는 것

- `AGENTS.md`가 문서 감리, authority, temp mirror, queue, operator gate를 강하게 통제한다.
- `active-temp-execution-roadmap.md`가 현재 front queue와 historical override를 장기적으로 관리한다.
- 각 lane의 `execution SSOT`가 구조적 next action과 landed tranche를 관리한다.
- `stage3-cross-pc-proof-rerun-handoff-context.md` 같은 cross-PC note가 이미 존재한다.
- `stage234-arc23-postpatch-proof-session-context.md`, `stage234-arc23-stage34-single-episode-demo-frontier-context.md`처럼 session-context에 가까운 짧은 note도 이미 존재한다.

### 아직 비어 있는 것

- `session context`의 형식이 표준화되어 있지 않다.
- 어떤 note는 `handoff context`, 어떤 note는 `frontier context`, 어떤 note는 `session context`라서 목적과 권한 경계가 문서명만으로는 일정하지 않다.
- 세션 단위로 `무엇이 닫혔고 무엇이 아직 안 닫혔는지`를 한 번에 복구하는 상위 문서가 부족하다.
- `staged but not active` 상태를 운영 문서에서 명시적으로 쓰는 규약이 약하다.
- `현재 canonical controller는 무엇이고, 이 note는 무엇을 대체하지 않는가`가 note마다 같은 강도로 적히지 않는다.

결론적으로 `글도비`는 `session context`와 완전히 무관한 상태가 아니라, 이미 유사체가 존재하지만 아직 `운영 표준`으로 승격되지는 않은 상태다.

## 4. 가장 유효한 활용 아이디어

### 아이디어 1. `Session Context`를 `execution SSOT` 위의 얇은 복구 레이어로 표준화

가장 먼저 도입할 것은 새 거대 문서가 아니다. 오히려 반대로, 아래 역할만 하는 얇은 문서를 표준화하는 것이다.

- 이번 세션이 어떤 canonical controller에서 시작됐는지
- 이번 세션 중 실제로 변한 사실만 무엇인지
- 다음 재개 순서가 무엇인지

중요한 점:

- `session context`는 `execution SSOT`를 대체하면 안 된다.
- `session context`는 `active roadmap`를 대체하면 안 된다.
- `session context`는 `이번 세션에서 생긴 delta만 요약하는 상위 복구 레이어`여야 한다.

이렇게 하면 `글도비`의 긴 roadmap와 깊은 SSOT를 다시 처음부터 훑지 않고도 세션 복구 시간이 급감한다.

### 아이디어 2. `accepted span` 개념을 `글도비`에서는 `closure frontier`로 변환

`불행...`에서는 `accepted span: ep0001-0101`처럼 선형 에피소드 범위를 잠근다.

`글도비`는 완전히 같은 문법을 쓸 필요는 없고, 대신 `closure frontier`를 아래 세 종류로 나눠 쓰는 게 맞다.

- proof frontier
  - 예: `Arc2/3 Stage2 proof green`, `exact-lineage Stage3 ep7 PASS`
- code frontier
  - 예: `Tranche A/B/C landed`, `no additional pre-proof tranche open`
- artifact frontier
  - 예: `blueprints through ep7`, `manuscripts through ep3`, `demo target r3 is partial only`

이 구조를 쓰면 `글도비` 특유의 `코드/증거/산출물`이 섞인 복합 상태를 한 줄로 잠글 수 있다.

### 아이디어 3. `active vs staged` 승격 규칙을 도입

donor 문서에서 특히 강한 부분은 `prefab은 staged지만 아직 active가 아니다`를 명확히 적는 방식이다.

이 개념은 `글도비`에 매우 잘 맞는다. 예시는 아래와 같다.

- 다음 canary target은 준비됐지만 아직 공식 next proof target은 아님
- 다음 execution SSOT는 써놨지만 roadmap front로 promote되진 않음
- 다음 Stage34 demo source는 만들어졌지만 frontier mismatch 때문에 active replay target은 아님
- material-side에서 다음 `work_guard / TR / BI` packet은 준비됐지만 아직 승격 전임

이 구분이 없으면 `준비된 자료`가 곧바로 `지금 써야 하는 자료`로 오독된다. `글도비`처럼 operator-gated 흐름이 많은 저장소에서는 이 오독이 특히 치명적이다.

### 아이디어 4. `deterministic resume order`를 note의 필수 필드로 고정

현재 `글도비` 문서는 읽을 가치가 높은 문서가 많지만, 다음 세션에서 `정확히 무슨 순서로 읽어야 하는지`는 note마다 다르다.

`불행...` 패턴을 이식하면 매 note 끝에 아래가 필수로 붙는다.

1. `git pull` 또는 현재 branch/head 확인
2. 읽어야 할 canonical docs 순서
3. 다음에 열어야 할 artifact anchor
4. 그 다음 실제 실행 순서

이 필드 하나만으로도 cross-PC 복구, branch 이동, 장기 중단 후 재개가 훨씬 안정된다.

### 아이디어 5. `이번 세션에 새로 생긴 산출물`을 문서/스크립트/증거로 분리 기록

`글도비`는 실무상 새로 생기는 것이 많다.

- audit 문서
- execution SSOT
- temp mirror
- 테스트
- canary project
- runtime evidence
- helper script

지금도 각 문서에는 일부 남아 있지만, `session context`에서는 이를 아래처럼 한 번에 분리 기록하는 것이 좋다.

- 새 canonical docs
- 새 temp mirrors
- 새 code/scripts/tests
- 새 proof artifacts / canary paths
- canonical이 아닌 scratch/untracked leftovers

이렇게 해야 다음 세션에서 `뭐가 authoritative인지`와 `뭐가 그냥 증거 부산물인지`를 빠르게 구분할 수 있다.

### 아이디어 6. `아직 안 한 것`과 `아직 authorize되지 않은 것`을 분리 기록

`글도비`는 단순 TODO보다 `not yet authorized`가 더 중요하다.

예를 들어 아래 둘은 전혀 다르다.

- 아직 안 썼다
- 써도 되지만 아직 안 썼다
- threshold는 넘었지만 operator gate가 아직 소비되지 않았다
- staged target은 있지만 active replay target으로 promote되진 않았다

donor 문서의 `아직 안 한 것`은 `글도비`에서 한 단계 더 진화시켜 아래 두 갈래로 적는 게 좋다.

- `Not Yet Done`
- `Not Yet Authorized`

이 구분은 roadmap의 historical override가 많은 `글도비`에서 특히 유용하다.

### 아이디어 7. material-side에도 같은 패턴을 이식

이 아이디어는 system-track에만 국한되지 않는다. 오히려 `글도비` README와 `AGENTS.md` 기준으로 보면 material-side에도 잘 맞는다.

적용 후보:

- 특정 `work_id`의 `Phase 0 -> work_guard -> TR -> BI` 진행 세션
- 여러 pair repair wave를 나눠 돌리는 세션
- benchmark / audit / repair batch가 섞인 material-side 운영

material-side에서는 `closure frontier`가 아래처럼 바뀐다.

- `phase frontier`
- `artifact frontier`
- `approval frontier`

예:

- `Phase 0 frozen`
- `work_guard WG-V2 freeze PASS`
- `TR blocks 1-70 drafted`
- `BI draft exists but audit FAIL`

즉 donor 문서의 힘은 actual-read에만 있는 것이 아니라, `단계형 narrative/material pipeline의 세션 복구 방식`에도 그대로 먹힌다.

## 5. `글도비`에서 실제로 박을 자리

### 추천 위치 1. dated canonical docs

가장 자연스러운 위치는 이미 쓰는 방식 그대로다.

- `docs/YYYY-MM-DD/*-session-context.md`

이름은 아래처럼 강제하는 것이 좋다.

- `{lane-name}-session-context.md`
- `{lane-name}-cross-pc-session-context.md`
- `{lane-name}-frontier-context.md`는 점진적으로 `session-context`로 수렴

핵심은 문서명이 `세션 복구 문서`라는 사실을 바로 드러내는 것이다.

### 추천 위치 2. `active-temp-execution-roadmap.md`에서 링크만 보유

roadmap 본문에 session context 내용을 다 넣으면 또 비대해진다. 그래서 roadmap는 아래만 하면 된다.

- 현재 front lane가 있다면 최신 session context 링크를 한 줄로 보유
- 이 문서는 `current workspace delta restore note`라고 명시

즉 roadmap는 큐를 쥐고, session context는 복구를 쥐는 분업이 맞다.

### 추천 위치 3. temp mirror는 기본 비사용

여기서는 donor를 그대로 들여오지 말고 오히려 `글도비` 룰에 맞게 더 보수적으로 가는 것이 좋다.

- 기본 원칙: `session context`는 temp mirror를 만들지 않는다.

이유:

- `session context`는 실행 큐 자체가 아니라 복구 note다.
- temp queue를 더 늘리면 queue/controller와 session note의 권한 경계가 흐려진다.

예외는 가능하지만 기본값은 `canonical only`가 더 안전하다.

## 6. 바로 써먹기 좋은 구체적 파일/기능 아이디어

### A. `session-context-template.md`

`docs/implementation/` 아래에 하나 두는 것이 가장 효율적이다.

들어가야 할 최소 항목:

```text
Title
Date
Status
Canonical Path
Audience
Commit/Branch/Dirty Summary
Start Controllers
What Closed This Session
What Landed This Session
What Is Staged But Not Active
What Is Not Yet Done
What Is Not Yet Authorized
Canonical Resume Order
Practical Next Action
Scratch / Non-Canonical Warning
3-Pass Audit Record
```

### B. `session-context-contract.md`

template만 두면 또 note가 제각각 된다. 짧은 contract도 필요하다.

필수 규칙:

- `execution SSOT` 대체 금지
- `active roadmap` 대체 금지
- `current controller` 명시
- `historical only`와 `current active` 구분
- `staged`와 `active` 구분
- `not yet authorized` 명시

### C. session-context index

나중에 가치가 커지는 옵션이다.

- 날짜순 index
- 각 lane별 latest session context만 모아두는 index

이건 스크립트 자동화가 붙으면 더 좋지만, 초기에는 수동 index만 있어도 충분하다.

### D. 첫 pilot에서 바로 만들 만한 실제 산출물

보고서 수준에서 끝내지 않으려면, 첫 pilot은 아래 3개만 만들어도 충분하다.

1. `docs/implementation/session-context-template.md`
2. `docs/implementation/session-context-contract.md`
3. live lane 1건의 표준형 session context

가장 쉬운 첫 pilot 후보는 아래 둘 중 하나다.

- `Stage34 Arc2/3` 계열 note를 표준형 session context로 재작성
- material-side 특정 `work_id`에 대해 `Phase 0 -> work_guard -> TR -> BI` 세션 복구 note 작성

핵심은 새 체계를 크게 여는 것이 아니라, 이미 존재하는 `handoff/frontier/session note` 중 하나를 표준형으로 다시 잠가서 효과를 보는 것이다.

## 7. 우선순위별 추천 적용 순서

### 1순위. proof-heavy system lane

가장 먼저 적용할 곳은 이미 session-like note가 있는 아래 계열이다.

- `Stage3 / Stage234 / Arc2/3 proof lanes`

이유:

- 이미 `handoff context`, `frontier context`, `session context note`가 존재한다.
- 표준화 이득이 바로 나온다.
- operator-gated / proof-pending / partial canary 같은 복합 상태를 가장 많이 다룬다.

특히 아래 조합은 거의 그대로 pilot 세트가 된다.

- `stage3-cross-pc-proof-rerun-handoff-context.md`
- `stage234-arc23-postpatch-proof-session-context.md`
- `stage234-arc23-stage34-single-episode-demo-frontier-context.md`

이 셋은 이미 session-context 유사체이므로, 새 시스템을 처음부터 발명하지 않고도 표준 contract로 수렴시키기 좋다.

### 2순위. material-side pipeline lane

그 다음은 아래다.

- `Phase 0 -> work_guard -> TR -> BI`

이유:

- `work_id` 단위로 stage frontier를 잠그기 좋다.
- 여러 파일이 섞이는 long session 복구 비용이 높다.
- 다른 PC나 다른 날에 같은 작품을 이어붙일 때 효과가 크다.

### 3순위. control-plane or desktop runtime lane

마지막은 아래다.

- desktop/control-plane debugging 세션

이쪽도 쓸모는 있지만, `proof lane`이나 `material lane`만큼 즉효는 아니다.

## 8. Adversarial 3-Pass Review

### Pass 1. 구조 감리

의심한 질문:

- 이 제안이 기존 `execution SSOT`와 roadmap를 중복 복제하는가?

판정:

- 중복 복제가 되면 실패다.
- 그래서 `session context`는 `이번 세션 delta + resume order`만 담당해야 한다.

수정된 결론:

- `얇은 상위 복구 레이어`로만 쓰는 것이 정답이다.

### Pass 2. 권한 감리

의심한 질문:

- session context가 나중에 roadmap나 execution SSOT보다 더 높은 권위처럼 읽히지 않는가?

판정:

- 그 위험이 실제로 있다.

완화책:

- 모든 session context에 `이 문서는 무엇을 대체하지 않는가`를 명시한다.
- `current controller`와 `historical/provenance only` 구분을 강제한다.
- `active vs staged`와 `not yet authorized`를 반드시 따로 적는다.

### Pass 3. 운영 비용 감리

의심한 질문:

- note를 표준화하면 문서만 하나 더 늘고 실제 효율은 없지 않은가?

판정:

- 무분별하게 만들면 진짜로 문서만 는다.

완화책:

- trigger를 제한해야 한다.

권장 trigger:

- cross-PC 이동이 예정된 세션
- queue controller가 바뀐 세션
- proof frontier나 code frontier가 실제로 닫힌 세션
- staged future target을 새로 만든 세션

즉 `모든 날 매번`이 아니라, `복구 비용이 큰 세션`에만 써야 한다.

## 9. 최종 제안

가장 좋은 도입 방식은 아래다.

1. `session-context-template.md`와 짧은 contract를 만든다.
2. `Stage3 / Stage234` proof lane에 먼저 pilot 적용한다.
3. 그 다음 material-side `Phase 0 / work_guard / TR / BI` lane으로 확장한다.
4. roadmap에는 최신 session context 링크만 얇게 남긴다.
5. `staged but not active`와 `not yet authorized`를 운영 표준 문구로 승격한다.

핵심 결론은 단순하다.

- `불행... session context`의 본질은 `좋은 요약문`이 아니라 `복구 질서를 잠그는 운영 contract`다.
- `글도비`는 이미 execution SSOT와 roadmap가 강해서, 이 contract를 얹을 준비가 돼 있다.
- 따라서 가장 큰 효용은 `새로운 큰 체계 추가`가 아니라 `기존 proof/handoff/session note를 하나의 표준 session-context 체계로 수렴`시키는 데서 나온다.

한 줄로 압축하면 아래다.

`글도비는 donor 문서의 내용을 복제할 필요가 없고, donor 문서의 복구 방식만 표준화해서 execution SSOT와 roadmap 사이에 얇은 session-context 레이어로 끼워 넣는 것이 가장 큰 ROI를 만든다.`
