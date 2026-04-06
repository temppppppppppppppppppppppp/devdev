# 결함이 보이는 방산 엔지니어 온보딩 프롬프트

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 목적: 컨텍스트가 없는 새 세션에서도 이 작품의 `Phase 0 -> TR -> BI -> 감리`를 하네스 기준으로 자동 진행시키기 위한 시작 프롬프트 모음
> 사용 대상 작품: `결함이 보이는 방산 엔지니어`
> work_id 권장값: `defense_defect_engineer`

---

## 1. 가장 권장하는 시작 프롬프트

아래 문장을 새 세션 첫 메시지로 그대로 붙여넣으면 된다.

```text
작품명은 `결함이 보이는 방산 엔지니어`.
work_id는 `defense_defect_engineer`로 고정한다.

먼저 아래 문서들을 UTF-8 기준으로 읽고, 이 문서들을 SSOT로 삼아 작업을 시작하라.
- `docs\blockguide\treatment-planning-harness.md`
- `docs\blockguide\treatment-production-harness-v2.md`
- `docs\blockguide\bi-production-harness-v1.md`
- `docs\2026-03-10\top3_replanning_brief_for_tr_bi.md`

위 문서 기준으로 `결함이 보이는 방산 엔지니어`의 해당 섹션을 찾아, 그 기획을 기반으로 자동 진행하라.

핵심 원칙은 아래와 같다.
- 주인공은 이득 중심, 자기중심이다.
- 선하거나 악할 필요는 없고, 도덕적 딜레마는 핵심 엔진이 아니다.
- 대상 독자는 삶에 찌든 30405060 남성 독자다.
- 대리만족이 최우선이다.
- 기술 설명보다 결함 독점, 시험평가 통제, 설계권 장악, 수주 구조, 협력사 라인, 수출 병목을 우선한다.
- 안전은 명분이고, 통제권과 규격 장악이 목적이라는 축을 유지한다.

운영 원칙은 아래와 같다.
- auto-run을 기본값으로 둬라.
- 내가 따로 멈추라고 하지 않으면 `Phase 0 -> TR 70블록 -> 3-pass 감리 -> BI -> BI 감리`까지 순차 진행하라.
- 컨텍스트 compaction이 발생해도 멈추지 말고, SSOT 파일을 다시 UTF-8로 열어 자동 재개하라.
- 강제 정지 게이트가 발생할 때만 멈춰라.
- 모든 파일 입출력과 감리는 UTF-8 only로 처리하라.
- `triple-question placeholder`, `double-question placeholder`, `replacement character`가 나오면 인코딩 오염으로 보고 즉시 중단 후 재생성하라.

산출물 경로는 아래처럼 고정한다.
- Phase 0: `treatments\defense_defect_engineer_phase0_design.json`
- TR draft: `treatments\04_defense_defect_engineer_tr_block_070_draft.json`
- BI: `bible\04_bi_defense_defect_engineer.json`

시작 순서는 아래와 같다.
1. 하네스 문서와 기획 문서를 UTF-8로 읽고 요약 확인
2. 작품 컨셉을 기준으로 Phase 0 설계
3. Phase 0 JSON 저장
4. TR 70블록을 하네스 기준으로 순차 생산
5. TR 3-pass 감리
6. BI 생성
7. BI 감리

지금 바로 1단계부터 시작하라.
```

---

## 2. 컨펌 직후 Phase 0만 먼저 뽑고 싶을 때

```text
작품명은 `결함이 보이는 방산 엔지니어`, work_id는 `defense_defect_engineer`이다.

아래 문서를 UTF-8 기준으로 읽어라.
- `docs\blockguide\treatment-planning-harness.md`
- `docs\2026-03-10\top3_replanning_brief_for_tr_bi.md`

위 문서를 SSOT로 삼아 이 작품의 Phase 0 설계만 진행하라.
출력은 `treatments\defense_defect_engineer_phase0_design.json`에 UTF-8로 저장하라.
아직 TR과 BI는 만들지 말고, Phase 0가 끝나면 멈춰라.
```

---

## 3. TR만 이어서 진행시키고 싶을 때

```text
작품명은 `결함이 보이는 방산 엔지니어`, work_id는 `defense_defect_engineer`이다.

아래 문서를 UTF-8 기준으로 읽어라.
- `docs\blockguide\treatment-production-harness-v2.md`
- `treatments\defense_defect_engineer_phase0_design.json`

위 문서를 SSOT로 삼아 TR 70블록을 자동 진행으로 끝까지 생산하라.
출력은 `treatments\04_defense_defect_engineer_tr_block_070_draft.json`에 UTF-8로 저장하라.
컨텍스트 compaction이 발생해도 직전 SSOT를 다시 열고 자동 재개하라.
TR 3-pass 감리까지 끝내고 멈춰라. BI는 아직 만들지 말라.
```

---

## 4. BI까지 이어서 진행시키고 싶을 때

```text
작품명은 `결함이 보이는 방산 엔지니어`, work_id는 `defense_defect_engineer`이다.

아래 문서를 UTF-8 기준으로 읽어라.
- `docs\blockguide\treatment-production-harness-v2.md`
- `docs\blockguide\bi-production-harness-v1.md`
- `treatments\defense_defect_engineer_phase0_design.json`
- `treatments\04_defense_defect_engineer_tr_block_070_draft.json`

위 문서를 SSOT로 삼아 BI를 생성하라.
출력은 `bible\04_bi_defense_defect_engineer.json`에 UTF-8로 저장하라.
`plot_roadmap`는 창작하지 말고 TR draft에서 동기화하라.
BI 5-pass 감리 또는 최소 3-pass 정합성 감리까지 끝내고 결과를 보고하라.
```

---

## 5. 중간에 세션이 끊겼을 때 재개 프롬프트

```text
이전 세션 맥락은 신뢰하지 말고, 아래 SSOT 파일들을 UTF-8 기준으로 다시 열어 현재 상태를 복구하라.

작품명: `결함이 보이는 방산 엔지니어`
work_id: `defense_defect_engineer`

SSOT 후보:
- `docs\blockguide\treatment-planning-harness.md`
- `docs\blockguide\treatment-production-harness-v2.md`
- `docs\blockguide\bi-production-harness-v1.md`
- `docs\2026-03-10\top3_replanning_brief_for_tr_bi.md`
- `treatments\defense_defect_engineer_phase0_design.json`
- `treatments\04_defense_defect_engineer_tr_block_070_draft.json`
- `bible\04_bi_defense_defect_engineer.json`

복구 순서:
1. 어떤 산출물이 이미 존재하는지 UTF-8로 확인
2. 가장 최신의 정상 SSOT를 기준으로 현재 단계를 판정
3. auto-run 기본값으로 다음 미완료 단계부터 재개
4. `triple-question placeholder`, `double-question placeholder`, `replacement character`, UTF-8 파싱 실패가 보이면 손상으로 간주하고 재생성

지금 상태를 먼저 판정한 뒤, 다음 미완료 단계부터 자동 진행하라.
```

---

## 6. 가장 짧은 실전용 한 줄

정말 짧게만 치고 싶으면 이 한 줄도 가능하다.

```text
`결함이 보이는 방산 엔지니어`를 `defense_defect_engineer`로 진행한다. `docs\blockguide\treatment-planning-harness.md`, `docs\blockguide\treatment-production-harness-v2.md`, `docs\blockguide\bi-production-harness-v1.md`, `docs\2026-03-10\top3_replanning_brief_for_tr_bi.md`를 UTF-8로 읽고 SSOT로 삼아 auto-run 기본값으로 `Phase 0 -> TR -> 감리 -> BI -> 감리`를 끝까지 순차 진행하라. compaction이 나도 멈추지 말고 SSOT 재오픈 후 재개하라. 모든 출력은 UTF-8 only로 저장하고 `triple-question placeholder`, `double-question placeholder`, `replacement character`가 나오면 중단 후 재생성하라.
```

---

## 7. 사용 팁

- 가장 안전한 건 `1번 프롬프트`다.
- 이미 Phase 0가 있으면 `3번`부터 써도 된다.
- TR까지 끝난 상태면 `4번`을 쓰면 된다.
- 세션이 끊겼거나 compaction이 있었으면 무조건 `5번`을 쓰는 편이 안전하다.
- 이 작품은 기술 설명보다 `결함 독점`, `시험평가 장악`, `규격 선점`, `수주 구조 재편`, `군·정부·대기업·해외 바이어를 동시에 협상 상대로 만드는 구조`를 계속 강조해야 한다.
