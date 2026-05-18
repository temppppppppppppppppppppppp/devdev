# 글도비 본체 하이브리드 운영 결론 딥다이브

- 날짜: 2026-05-18
- 질문: 파이어플라이에서 얻은 결론, 즉 "프리파이프라인은 맛 증명, 본선 파이프라인은 장기 기억/저장/감리/운영"이라는 결론이 글도비 본체에도 적용되는가?
- 결론: 적용된다. 다만 본체에서는 용어와 위치가 한 칸 상류로 번역되어야 한다.
- 판정: `SAME_CONCLUSION_WITH_MAIN_REPO_TRANSLATION`

## 한 줄 결론

글도비 본체에서도 같은 결론이 나온다. 단, 본체의 결론은 `BI/TR 폐기`가 아니라 `BI/TR을 창작 원천이 아니라 검증된 맛을 싣는 장기 생산용 운반체로 재정의`하는 것이다.

즉 본체 운영식은 다음과 같다.

```text
실물 원고 귀납 / R&D 랩 / 프리파이프라인 / 마이크로 카나리
-> material_ssot 승격 판단
-> Phase0 + work_guard
-> TR 1-10
-> 10블록 감리
-> TR70 / BI 확장
-> 파이어플라이 S2-S3-S4 또는 기타 원고 생산 본선
```

## 오해 방지

- `5.5 Codex가 있으니 본체 파이프라인이 필요 없다`는 결론이 아니다.
- `BI/TR을 없애자`는 결론도 아니다.
- `프리파이프라인 산출물을 바로 정본 원고나 정본 재료로 쓰자`도 아니다.
- 맞는 결론은 `프리파이프라인으로 맛을 먼저 증명하고, 증명된 맛만 본체의 Phase0/work_guard/TR/BI에 태운다`이다.
- `TR70`은 첫 작업이 아니라 후속 확장이다. 처음부터 70블록을 만들면 기존 문제가 반복된다.
- `BI`는 새 창작층이 아니라 동기화, 증폭, 장기 운용층이다.

## 본체와 파플의 대응 관계

| 파이어플라이 표현 | 글도비 본체 번역 | 역할 |
|---|---|---|
| 프리파이프라인 | R&D 랩, 실물 원고 귀납, pitch/synthesis, B1-B2 또는 EP001 마이크로 카나리 | 맛 발견과 초기 장면 증명 |
| S2-S3-S4 본선 | 본체에서는 Phase0/work_guard/TR/BI 이후 downstream writer pipeline | 장기 생산, 기억, 저장, 검수, 재현성 |
| S4 writer context 개선 | 본체에서는 material-to-writer translation, scene-native bridge, S4 호환 재료화 | 작가가 바로 장면으로 쓸 수 있는 입력으로 번역 |
| 15화 카나리 | 본체에서는 B1-B2, EP001, 또는 TR 1-10 전의 작은 증명 | 큰 확장 전 유효성 검증 |
| 풀패킷 오해 | 본체에서도 production pipeline 대체가 아니라 pre-S4 translator 후보 | 기존 본선을 우회하지 않음 |

## 조사한 표면

이번 조사는 본체, material_ssot, blockguide, narrative-router, R&D 랩, GitHub issue #151을 나눠 병렬로 확인했다.

핵심 확인 경로:

- `C:\Users\User\Desktop\글도비\AGENTS.md`
- `C:\Users\User\Desktop\글도비\AGENTS.narrative-router.md`
- `C:\Users\User\Desktop\글도비\README.md`
- `C:\Users\User\Desktop\글도비\README.narrative-router.md`
- `C:\Users\User\Desktop\글도비\docs\narrative-router\SSOT_narrative-router-integrated-order.md`
- `C:\Users\User\Desktop\글도비\docs\narrative-router\what-how-craft-harness.md`
- `C:\Users\User\Desktop\글도비\docs\narrative-router\material-revival-ladder-harness.md`
- `C:\Users\User\Desktop\글도비\docs\blockguide\SSOT_blockguide-integrated-order.md`
- `C:\Users\User\Desktop\글도비\docs\blockguide\treatment-planning-harness.md`
- `C:\Users\User\Desktop\글도비\docs\blockguide\treatment-production-harness-v2.md`
- `C:\Users\User\Desktop\글도비\docs\blockguide\bi-production-harness-v1.md`
- `C:\Users\User\Desktop\글도비\material_ssot\README.md`
- `C:\Users\User\Desktop\글도비\material_ssot\00_governance\stage-read-order.md`
- `C:\Users\User\Desktop\글도비\material_ssot\00_governance\donor-review-and-adoption-contract-v1.md`
- `C:\Users\User\Desktop\글도비\C:\Users\User\Desktop\글도비_파이어플라이\docs\material_ssot\geuldobi_handoff\C:\Users\User\Desktop\글도비_파이어플라이\docs\material_ssot\geuldobi_handoff\00_governance\firefly-s4-scene-native-material-bridge-v1.md`
- `C:\Users\User\Desktop\글도비\material_ssot\C:\Users\User\Desktop\글도비_파이어플라이\docs\material_ssot\geuldobi_handoff\00_governance\firefly-b1-b2-micro-canary-before-70-harness-v1.md`
- `C:\Users\User\Desktop\재료 생산 R&D 랩\AGENTS.md`
- `C:\Users\User\Desktop\재료 생산 R&D 랩\docs\2026-05-16\full-packet-vs-existing-pipeline-correction-v0.md`
- `C:\Users\User\Desktop\재료 생산 R&D 랩\docs\2026-05-16\geuldobi-issue-151-full-packet-pipeline-correction-comment.md`
- GitHub issue #151: `[Roadmap] 중간표현층(S2-S3) 품질업 연구를 본체 파이프라인으로 반영`

## 증거 1: 본체의 공식 순서가 이미 "상류 창작 -> 운반체" 구조다

본체 `AGENTS.md`와 `material_ssot/README.md`는 공식 순서를 다음처럼 둔다.

```text
리서치 -> 기획안 -> Stage 0 preprocess -> Phase 0 design -> TR 생성 -> BI 생성 -> 글도비 파이프라인
```

이 말은 TR/BI가 첫 발명층이 아니라는 뜻이다. 먼저 리서치, 기획안, Stage0, Phase0, work_guard에서 작품의 맛과 운용 원리를 잡고, 그 다음 TR/BI가 장기 생산 가능한 형태로 싣는다.

따라서 본체 결론은 파플 결론보다 오히려 더 명확하다. 파플에서 `pre-pipeline vs S2-S3-S4`로 나뉘던 것이, 본체에서는 `R&D/실물 귀납/pitch/canary vs Phase0/work_guard/TR/BI`로 나뉜다.

## 증거 2: blockguide는 대량 자동 생산을 금지한다

`SSOT_blockguide-integrated-order.md`, `treatment-planning-harness.md`, `treatment-production-harness-v2.md`는 다음 판단을 일관되게 둔다.

- Phase0 없이 TR 금지.
- TR draft 없이 BI 금지.
- 한 번에 70블록 생성 금지.
- TR 생산 단위는 1블록이다.
- 같은 오더에서 최대 5블록까지만 진행한다.
- 010, 020 같은 10블록 지점에는 감리를 끼운다.
- TR block은 published episode 1화가 아니라 보통 2-6화 단위의 전개 묶음이다.
- 첫 블록은 "이 작품은 이 맛"을 증명해야 한다.

이것은 "본체도 프리파이프라인이 필요하다"는 증거다. 본체는 애초에 TR70 원샷을 정상 운영으로 보지 않는다. 작은 단위에서 맛과 페이싱을 증명하고, 그 다음 확장해야 한다.

## 증거 3: Firefly S4 bridge는 본체 안에 이미 들어와 있다

`firefly-s4-scene-native-material-bridge-v1.md`는 본체 재료가 파플 S4에서 깨지는 이유를 정확히 지적한다.

- 섹터 리스트는 장면이 아니다.
- 보상 라벨은 독자 보상이 아니다.
- 권한/접근/파일 같은 말은 인간 장면으로 번역되어야 한다.
- S4가 필요한 것은 다음 장면의 방, 사람, 압력, 저항 이유, 바뀌는 물건/태도/돈/일정이다.

이 문서는 `BI/TR/GUARD가 형태상 맞아도 Stage 4에서 글이 깨질 수 있다`고 본다. 따라서 본체의 개선 방향도 명확하다.

본체는 TR/BI를 없앨 것이 아니라, TR/BI에 들어가기 전 재료를 `scene-native`로 바꿔야 한다. 즉 S4가 장면으로 쓸 수 있는 재료만 TR/BI에 실어야 한다.

## 증거 4: B1-B2 마이크로 카나리 문서가 결론을 직접 말한다

`firefly-b1-b2-micro-canary-before-70-harness-v1.md`는 결론을 거의 그대로 말한다.

- B1-B2 또는 EP001 마이크로 카나리가 통과하기 전 full 70-block TR을 만들지 않는다.
- 통과 전 허용되는 것은 얇은 atlas, gate matrix, first two-arc checklist, opening seed, B1-B2 packet 정도다.
- 통과 후에도 바로 TR70이 아니라 Phase0, work_guard, TR 1-10, 10블록 감리 순서다.

이것은 파플에서 얻은 결론을 본체 운영 규칙으로 옮긴 형태다. 본체에서도 `작은 실물성 증명 -> 승격 -> 제한 확장 -> 감리 -> 장기 확장`이 맞다.

## 증거 5: R&D 랩은 정본 생산소가 아니라 증거 생산소다

`재료 생산 R&D 랩`의 AGENTS와 관련 문서는 역할을 분리한다.

- R&D 랩은 실제 원고 읽기, donor law 추출, canary, overlay, deep-cloning spec 실험을 담당한다.
- 글도비는 canonical material-side control plane이다.
- R&D 산출물은 글도비 정본 문서나 DB를 직접 바꾸지 않는다.
- 승격하려면 material_ssot의 규칙으로 번역되어야 한다.

즉 R&D 랩은 매우 중요하지만, 본선 대체물이 아니다. 인간 원고에서 배운 것을 직접 원고에 베껴 넣는 곳이 아니라, 본체가 먹을 수 있는 원리와 장면 재료로 번역하는 상류 실험실이다.

## 증거 6: issue #151도 같은 방향으로 정리되어 있다

issue #151의 핵심은 `중간표현층(S2-S3) 품질업 연구를 본체 파이프라인으로 반영`이다.

최근 정리는 다음에 가깝다.

- full packet은 기존 production pipeline 자체가 아니다.
- 실제 write context는 blueprint, 이전 원고/history, continuity/state, mandatory/work_guard/review surface다.
- 연구 결과의 통합 후보는 production code 대체가 아니라 pre-S4 `Director/BP -> Writer Context` translator 쪽이다.
- production pipeline은 검증 전에는 찢지 않는다.

이것 역시 파플 결론과 같다. 개선 대상은 "본선 제거"가 아니라 "본선에 들어가기 전 작가 입력의 번역 품질"이다.

## 본체에 적용되는 실제 운영안

### 1. 실물 귀납으로 맛을 먼저 잡는다

새 작품을 만들 때 첫 질문은 `TR70을 어떻게 채울까`가 아니다.

먼저 물어야 할 것은 다음이다.

- 독자는 1화 첫 화면에서 주인공에게 왜 붙는가?
- 주인공의 첫 손해, 첫 모욕, 첫 압박은 무엇인가?
- 주인공은 어떤 정보/감정안/판단으로 방 안의 힘을 바꾸는가?
- 상대는 왜 합리적으로 버티는가?
- 그 버팀 때문에 주인공이 더 유능해 보이는가?
- 1-3화 안에서 독자가 받는 첫 보상은 무엇인가?
- 다음 권한, 다음 방, 다음 사람은 무엇으로 열린다?

이 질문은 실물 원고를 가까이 읽어서 얻어야 한다. 멀리서 `보상`, `권한`, `착화` 같은 말을 붙이면 본문이 쉽게 굳는다.

### 2. pitch/canary 단계에서 장면으로 먼저 증명한다

본체의 새 표준은 다음이어야 한다.

```text
pitch canon
-> opening bundle seed
-> B1-B2 또는 EP001 micro-canary
-> Director readback
-> 대리만족/실물성 감리
-> 통과 시 Phase0/work_guard
```

여기서 중요한 것은 `기획이 말이 된다`가 아니라 `첫 장면이 실제 웹소설처럼 독자를 붙잡는다`이다.

### 3. 통과한 맛만 Phase0/work_guard에 고정한다

Phase0은 세계관 백과가 아니라 작품의 장기 운용 원리다.

work_guard는 full philosophy가 아니라 다음 단계가 흔들리지 않게 붙잡는 압축 규칙이어야 한다.

좋은 work_guard는 이런 말을 해야 한다.

- 이 작품의 주인공은 어떤 방식으로 이긴다.
- 어떤 장면은 금지다.
- 어떤 보상은 반드시 몇 화 안에 보여야 한다.
- 어떤 말투나 장면 처리에서 기계 냄새가 난다.
- 돈, 권위, 가족, 계열사, 역사 이벤트가 어떤 순서로 커져야 한다.

반대로 나쁜 work_guard는 추상 단어만 쌓는다.

### 4. TR은 처음부터 70이 아니라 1-10으로 간다

TR은 여전히 필요하다. 다만 `창작의 첫 장소`가 아니라 `검증된 맛의 장기 전개 운반체`다.

운영 순서는 다음이 낫다.

```text
TR 001
TR 002
TR 003
TR 004
TR 005
5블록 자체 점검
TR 006-010
10블록 감리
그 뒤 확장 판단
```

TR 1블록은 보통 2-6화 전개 단위로 본다. 따라서 70블록은 200화 이상 작품의 장기 지도에 가깝다. 처음부터 다 쓰면 페이싱과 실물성 검증이 늦어진다.

### 5. BI는 동기화와 장기 생산 기억으로 쓴다

BI는 버릴 대상이 아니다. 오히려 장편에서는 필요하다.

다만 BI가 새 이야기를 발명하면 안 된다. BI는 TR과 Phase0/work_guard에서 확정된 것을 다음 생산자가 실수하지 않게 정리하고 증폭하는 표면이다.

좋은 BI는 다음을 해준다.

- 인물 욕망과 관계를 장기적으로 유지한다.
- TR 전개를 런타임이 읽기 쉽게 재배열한다.
- 주인공 보상 루프와 권위 상승의 기준을 잃지 않게 한다.
- S2/S3/S4가 다음 회차에서 무엇을 기억해야 하는지 알려준다.

나쁜 BI는 TR과 별개의 새 로드맵을 만든다.

## 본체 결론의 가장 중요한 문장

본체에서 프리파이프라인은 본선의 대체물이 아니다. 본선에 태울 가치가 있는 맛을 증명하는 선별 장치다.

본체에서 Phase0/work_guard/TR/BI는 창작을 대신하는 기계가 아니다. 실물 원고에서 귀납한 맛을 장편 생산 중에 잃지 않게 해주는 기억 장치다.

## 현재 신규 재벌 3세 계열 작업에 대한 적용

현재 목표가 `독식하는 재벌 3세` 계열의 실물 맛을 참고해 `국제그룹/회귀/후계자/섹터 성장/돈/권위/대리만족` 작품을 만드는 것이라면 본체 운영은 다음이 맞다.

1. 실물 레퍼런스에서 1-3화의 독자 부착, 첫 모욕, 첫 유능함, 첫 권한 이동을 가까이 읽는다.
2. 소재만 발명하지 말고, 성공작이 쓰는 첫 방의 압력과 보상 순서를 일반화한다.
3. `국제그룹` 모티브에 맞춘 pitch canon을 만든다.
4. B1-B2 또는 EP001 마이크로 카나리를 먼저 쓴다.
5. PD 시선으로 "이게 실제 1화로 먹히는가"를 본다.
6. 통과하면 Phase0/work_guard로 고정한다.
7. TR 1-10까지만 먼저 만든다.
8. 10블록 감리 후 TR70/BI를 확장한다.
9. 파플 S2-S3-S4에는 이 재료를 `장면으로 쓸 수 있는 형태`로 넘긴다.

여기서 핵심은 `국제그룹의 역사 이벤트 목록`이 아니다. 그 목록이 매 화 독자의 100원 보상으로 바뀌는 방식이다.

## stage 축소에 대한 답

운영상 stage는 줄일 수 있다. 하지만 논리 stage는 없애면 안 된다.

줄일 수 있는 것:

- 초반에는 full Phase0 대신 opening Phase0 seed로 시작.
- 초반에는 TR70 대신 B1-B2, EP001, TR 1-5, TR 1-10으로 제한.
- 초반에는 production BI 대신 thin runtime BI 또는 BI seed로 제한.
- 감리 통과 전까지 정본 선언을 늦춤.

없애면 안 되는 것:

- 실물 귀납.
- pitch/canon 판단.
- B1-B2 또는 EP001 카나리.
- Phase0/work_guard의 작품별 금지와 운용 원리.
- TR의 장기 전개 기억.
- BI의 동기화와 장기 생산 기억.
- 파플 S2-S3-S4의 저장, continuity, review, export.

따라서 결론은 `stage 삭제`가 아니라 `초기 stage의 무게를 줄이고, 통과 후 확장`이다.

## decision table

| 상황 | 바로 할 일 | 하지 말 것 |
|---|---|---|
| 새 작품을 처음 만든다 | 실물 귀납, pitch, B1-B2/EP001 카나리 | TR70 원샷 |
| 카나리가 먹힌다 | Phase0/work_guard, TR 1-10 | 바로 BI 완성 선언 |
| TR 1-10이 페이싱을 유지한다 | 10블록 감리 후 확장 | 감리 없이 70까지 밀기 |
| 기존 TR/BI 쌍이 있다 | revival ladder로 lite audit, top repair, canary | 전면 폐기 또는 맹목 채택 |
| 파플 S4에서 글이 깨진다 | writer-facing context/scene-native bridge 보정 | S4 전체 폐기 |
| 기계적인 단어가 튄다 | 장면의 사람, 돈, 책임, 일정, 태도 변화로 번역 | 라벨을 더 붙이기 |

## 본체 issue #151에 남길 권장 결론

issue #151은 다음 문장으로 업데이트하는 것이 좋다.

```text
Firefly 연구 결론을 글도비 본체에 적용하면, 본선 폐기나 BI/TR 삭제가 아니라
pre-S4/pre-TR 맛 증명층을 공식화하고, 통과한 맛만 Phase0/work_guard/TR/BI로 승격하는
하이브리드 운영안이 된다.

즉 R&D/실물 귀납/B1-B2 카나리는 creative proof lane,
Phase0/work_guard/TR/BI는 canonical material carrier,
Firefly S2-S3-S4는 manuscript runtime/memory/audit lane으로 둔다.

다음 구현 단위는 production code 변경이 아니라
material_ssot read order와 issue #151에
GEULDOBI-HYBRID-MATERIAL-OPERATION-V0를 고정하는 문서화다.
```

## 남은 리스크

- `BI/TR은 운반체`라는 말을 너무 얇게 받아들이면 안 된다. TR은 장편 전개의 척추이고 BI는 런타임 기억이다.
- 반대로 `TR/BI가 중요하다`는 말을 다시 `TR70 먼저 쓰자`로 되돌리면 안 된다.
- R&D 랩의 donor 추출은 원고 카피가 아니라 기능 귀납이어야 한다. 승격 시 donor 고유명, 장면 순서, 문장, 고유 표면은 차단해야 한다.
- 파플의 S4 개선과 본체의 재료 개선은 연결되어 있지만 같은 작업은 아니다. 본체는 더 상류에서 재료를 만든다.
- 신규 재벌 3세 계열은 역사 이벤트와 거물 목록을 많이 넣을수록 좋아지는 것이 아니다. 독자 보상으로 변환되는 이벤트만 살아남겨야 한다.

## 3-pass audit

### Pass 1: evidence coverage

판정: PASS

본체 `AGENTS.md`, `material_ssot`, `blockguide`, `narrative-router`, `R&D 랩`, issue #151까지 확인했다. 결론은 한 표면에서만 나온 것이 아니라 여러 독립 표면에서 반복 확인된다.

### Pass 2: counterargument

판정: PASS_WITH_MODIFICATION

반론은 있다. 본체에서 TR/BI는 파플의 S2-S3-S4보다 더 상류에 있으므로, `본선은 저장/감리만 한다`고 단순화하면 틀린다. 본체의 TR은 장기 전개 척추이고 BI는 런타임 동기화 표면이다.

따라서 최종 결론은 `TR/BI thin carrier`가 아니라 `TR/BI structured carrier/amplifier`로 보정한다.

### Pass 3: operational safety

판정: PASS

이번 조사는 production code, DB, 원고, prompts를 변경하지 않았다. 결론은 문서화와 issue 정리 단계로 제한한다. 기존 dirty worktree의 다른 변경도 되돌리지 않는다.

### confidence

96%

이 결론은 현재 본체 문서와 R&D 문서, issue #151의 최신 방향과 충돌하지 않는다. 다만 실제 구현은 아직 문서/운영 규칙 확정 단계이며, production code 변경으로 들어가기 전에는 별도 설계가 필요하다.
