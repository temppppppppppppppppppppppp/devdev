# office_checkup_next_day Handoff And Next Order

작성일: 2026-03-30  
대상 작품: `office_checkup_next_day`  
트랙: 서사 파이프라인 / `blockguide`

## 1. 현재 진실

- source truth 파일
  - `C:\Users\wjjo\Desktop\글도비\treatments\office_checkup_next_day_phase0_design.json`
  - `C:\Users\wjjo\Desktop\글도비\treatments\office_checkup_next_day_tr_block_070_draft.json`
- 현재 `BI`는 없다.
  - `C:\Users\wjjo\Desktop\글도비\bible\0_bi_office_checkup_next_day.json` 없음
- 따라서 파일 존재 기준 stage는 원칙상 BI 직전처럼 보이지만, 실제 handoff gate 기준으로는 아직 `TR continuation`이다.
- 이유:
  - `tr_block_070_draft` 파일명과 달리 실제 블록 수는 `35`
  - source TR handoff gate를 아직 못 넘는다

## 2. 현재 작품 핵심 상태

- 현재 제목:
  - `검진 다음 날, 터질 게 보인다`
- 현재 premise 핵심:
  - 건강검진 다음 날부터 조직/프로젝트 감각이 발현된다
  - 시혁은 터질 프로젝트를 먼저 읽고, 숨겨진 숫자를 파고, 결재선을 거슬러 직보한다
  - 감각의 본질은 끝까지 애매하게 유지한다
- 현재 opening arc 리듬:
  - Block 1: `묻힌 보고서` / opening humiliation
  - Block 2: `검진 결과지` / 첫 사이다 / Lv1 -> Lv2
  - Block 3: `전무실 배석` / 두 번째 사이다 / CC 라인 비공식 진입
  - Block 7: `임원회의 아침` / ARC-01 대표 스파이크 / 전사 최대 프로젝트 저지
  - Block 8: `보상 4종` / 전사 메일 실명 언급 / TF 실무 간사 / 자리 이동 / 전무 직보 CC

## 3. 이미 끝난 것

- `phase0`는 repair 완료 상태다.
- `TR Block 1-10`도 bounded repair 완료 상태다.
- 아래는 다시 갈아엎지 않는다.
  - title sharpen
  - Block 2 = 첫 사이다
  - Block 3 = 두 번째 사이다
  - Block 7 = 대표 spike
  - Block 8 = 보상 4종

## 4. 현재 판단

- `Block 1-10` 오프닝 페이싱은 괜찮다.
- 병목은 오프닝이 아니라 `TR이 35블록에서 멈춰 있는 상태`다.
- 즉, 지금 가장 중요한 다음 작업은 `TR 36-70 완성`이다.
- BI 생성은 그 다음이다.

## 5. reference 재료 풀 상태

- reference card 수집은 완료됐다.
- manifest 기준:
  - `24 entries`
  - `status=audited: 24`
  - `audit_status=pass: 24`
- 관련 문서:
  - `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\2026-03-30_modern_business_reference_master_order.md`
  - `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_collection_index.md`

사용 원칙:

- reference 카드는 source truth가 아니다
- 이미 `office_checkup_next_day` phase0/TR에 반영된 리듬과 구조를 보강하는 참고축으로만 본다
- 새 엔진으로 갈아끼우는 근거로 쓰지 않는다

## 6. 메타 문구 주의

`foreshadow` / `callback` 안의 `Block 7 Block 1 spike` 같은 표현은 피하는 게 좋다.

이유:

- 파이프라인이 이 문구를 구조적으로 파싱하지 않는다
- 다음 LLM에게 raw context로만 흘러가므로, `블록 번호`와 `메타 라벨`을 섞으면 저신호가 된다

권장:

- `Block 7 임원회의 아침에서 대안을 올리는 경로로 재사용된다`
- 또는 `Block 7의 대표 스파이크에서 재사용된다`

## 7. 다음 실제 오더

### 7.1 지금 당장 실행할 오더

아래 오더를 그대로 사용한다.

```text
서사 파이프라인 production continuation 오더다.
이번 턴은 `office_checkup_next_day`의 BI가 아니라, 기존 TR draft를 35블록에서 70블록까지 완성하는 작업이다.
`chaebol_ent`는 다른 담당이 있으니 절대 건드리지 마라.

먼저 읽을 것:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
3. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\wjjo\Desktop\글도비\docs\blockguide\treatment-production-harness-v2.md

대상 파일:
- C:\Users\wjjo\Desktop\글도비\treatments\office_checkup_next_day_phase0_design.json
- C:\Users\wjjo\Desktop\글도비\treatments\office_checkup_next_day_tr_block_070_draft.json

현재 판정:
- 파일명은 `tr_block_070_draft`지만 실제 블록 수는 35개다
- source TR handoff gate FAIL
- 따라서 현재 실제 단계는 `TR production continuation`
- 이번 턴 목표는 `Block 36-70` 생산 완료 + handoff gate 충족이다
- BI 생성 금지

절대 규칙:
- 기존 `Block 1-35`는 전면 재작성 금지
- 이미 repair 완료된 opening promise, Block 1 humiliation, Block 2 첫 사이다, Block 3 두 번째 사이다, Block 7 대표 spike, Block 8 보상 4종은 유지
- 필요한 경우 later foreshadow/callback anchor만 최소 수정 허용
- `Block 36-70`만 새로 채워 넣는다
- `phase0_design`은 source truth로만 사용하고 필요 시 미세 sync만 허용
- `chaebol_ent` 수정 금지
- BI 생성 금지

고정 철학:
- protagonist-first
- 둥기둥기 first
- 성취 직후 인정/보상 필수
- 정보격차 필수
- 정보 은닉 유지
- no-romance 기본값
- 각 10block 단위마다 자체 감리 진행
- 이미 Block 1 spike는 확보됐으므로 이후 블록은 그 스파이크 확대/회수/권력화가 보여야 한다

이번 턴의 생산 목표:
1. `Block 36-70`을 기존 톤과 구조에 맞게 완성
2. 장현태/오세진/전무/대표 라인의 power map이 후반까지 자연스럽게 상승하도록 유지
3. ARC 후반에서 시혁의 감각이
   - 프로젝트 저지
   - 숫자 발굴
   - 결재선 우회
   - 권한/상신권/조직 장악
   으로 계속 확대되게 설계
4. 35블록 이후의 확장도 `더 큰 프로젝트`, `더 높은 결재선`, `더 위험한 숫자`, `더 큰 조직 저항`으로 키운다
5. 마지막까지 감각의 본질은 완전 확정하지 말고, 애매함을 유지한다

필수 산출:
- `office_checkup_next_day_tr_block_070_draft.json`을 실제 70블록으로 완성 저장
- handoff gate에 필요한 메타가 하네스 기준으로 있다면 함께 보강
- 10block 단위 자체 감리 결과를 남긴다
  - 최소: 40 / 50 / 60 / 70 시점
- 최종 보고에서 아래를 반드시 명시:
  - 총 블록 수
  - production_density_gate 충족 여부
  - avg_bundle_chars 확인 여부
  - source TR handoff gate PASS/FAIL
  - BI로 넘어갈 수 있는지 여부

진행 방식:
- `Block 36-40` 생산
- 자체 감리
- `Block 41-50` 생산
- 자체 감리
- `Block 51-60` 생산
- 자체 감리
- `Block 61-70` 생산
- 자체 감리
- 전체 handoff gate 재확인
- PASS/FAIL 보고 후 정지

금지:
- Block 1-35 갈아엎기
- 회귀/빙의/상태창/AI 등 새 엔진 주입
- 장현태 축을 갑자기 폐기
- 보상 없는 고통 펌프
- BI 섞기
- 70블록 완성 전에 완료 선언

산출물 형식:
1. Findings First
- 왜 지금 BI가 아니라 TR continuation인지 2~3개
- Block 36-70에서 무엇을 확대/회수하는지 3~5개

2. Production 실행
- `office_checkup_next_day_tr_block_070_draft.json` 저장

3. 최종 보고
- 총 블록 수
- 10block 자체 감리 결과 요약
- handoff gate 결과
- 다음 단계가 BI인지 아닌지 1문장으로 명시

문체:
- 한국어
- findings first
- 군더더기 없이
- 실전 production 톤
```

### 7.2 TR 70 완료 후에만 실행할 BI 오더

아래 오더는 `TR 70 완료 + handoff gate PASS` 이후에만 사용한다.

```text
서사 파이프라인 BI 생성 오더다.
이번 턴은 `office_checkup_next_day`의 BI를 생성한다.
삭제/재생성 금지. `chaebol_ent` 절대 수정 금지. phase0/TR 재작성 금지.

먼저 읽을 것:
1. C:\Users\wjjo\Desktop\글도비\AGENTS.md
2. C:\Users\wjjo\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md
3. C:\Users\wjjo\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md
4. C:\Users\wjjo\Desktop\글도비\docs\blockguide\treatment-production-harness-v2.md
5. C:\Users\wjjo\Desktop\글도비\docs\blockguide\bi-production-harness-v1.md

작품 정보:
- work_id: `office_checkup_next_day`
- stage 판정:
  - `phase0_design` 있음
  - `tr_block_070_draft` 있음
  - `0_bi_office_checkup_next_day.json` 없음
  - 단, source TR handoff gate는 PASS한 상태여야 한다

소스 진실:
- C:\Users\wjjo\Desktop\글도비\treatments\office_checkup_next_day_phase0_design.json
- C:\Users\wjjo\Desktop\글도비\treatments\office_checkup_next_day_tr_block_070_draft.json

출력 경로:
- C:\Users\wjjo\Desktop\글도비\bible\0_bi_office_checkup_next_day.json

핵심 원칙:
- BI는 새 창작이 아니라 기존 phase0 + TR의 구조화/동기화다
- 긴 한국어는 새로 쓰지 말고 source TR/phase0에서 가능한 한 복사·동기화한다
- reference 카드는 source truth가 아니라 참고축이다
- Block 7은 대표 간판 장면 anchor로 유지한다
- Block 8 보상 4종은 power/capital level up으로 반영한다
- 감각의 본질은 완전 확정하지 않는다

실행 순서:
1. source TR handoff gate 확인
2. canonical BI shape 확인
3. skeleton 생성
4. source phase0/TR 동기화
5. UTF-8 저장
6. 정합성 검증
7. 5-pass audit
8. PASS/FAIL 보고 후 정지
```

## 8. 타 PC에서 이어갈 때 체크리스트

1. `AGENTS.md`부터 읽는다.
2. narrative-router -> blockguide 순으로 읽는다.
3. `office_checkup_next_day_phase0_design.json`과 `office_checkup_next_day_tr_block_070_draft.json`을 UTF-8로 연다.
4. `TR` 실제 블록 수를 먼저 센다.
5. 35면 `TR continuation`, 70이고 handoff gate PASS면 `BI`.
6. `chaebol_ent`는 건드리지 않는다.

## 9. 한 줄 결론

`office_checkup_next_day`는 폐기/재생성이 아니라 repair 완료 상태의 `TR continuation` 작품이다.  
다음 정답은 `Block 36-70 완성`, 그 다음이 `BI 생성`이다.
