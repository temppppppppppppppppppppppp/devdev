# Sonnet 4.6 Parallel Deployable GREENPLUS Orders

Date: 2026-04-10
Status: operator dispatch sheet
Scope:

- `GREENPLUS` historical shelf 재판정
- `deployable GREENPLUS` 병렬 감사
- terminal `1~5` 전용 오더

---

## 1. Dispatch Rule

이 문서는 `Sonnet 4.6` 병렬 터미널에 그대로 복붙하는 오더 시트다.

운영 원칙:

- 각 터미널은 **자기 번호 섹션만** 읽고 진행한다.
- 각 터미널은 **읽기 + 판정 + 지정 경로 문서 작성**만 한다.
- source 파일, registry, runtime, material governance 문서는 수정하지 않는다.
- 각 터미널의 산출물은 **자기 지정 경로의 markdown 1개**만 작성한다.
- 애매하면 무조건 `NO`다.
- `repair 제안` 금지.
- `좋은 점 위주 감상평` 금지.
- `historical GREENPLUS alias`와 `deployable GREENPLUS`를 절대 혼동하지 않는다.

---

## 2. Global Judgment Law

모든 터미널은 아래 법을 그대로 따른다.

- 목표는 `지금 당장 실전 판매용 top shelf 재료`인지 판정하는 것이다.
- 느슨한 판정 금지.
- 근거 없는 호의적 추정 금지.
- `조금 손보면 된다`, `잠재력 있다`, `대체로 좋다` 같은 중간지대 금지.
- 최종 결론은 반드시 둘 중 하나다:
  - `DEPLOYABLE GREENPLUS = YES`
  - `DEPLOYABLE GREENPLUS = NO`

다음 중 하나라도 명확히 걸리면 `NO`:

1. opening authority가 아직 `legacy heuristic` 수준이고, explicit closeout 없이도 명백하다고 말할 수 없다.
2. opening pacing이 `YELLOW/RED`이거나, 그에 준하는 구조 지연이 보인다.
3. whole-run에서 중후반 drag가 실전 판매 shelf를 해칠 정도로 보인다.
4. operator note/registry 기준으로 `repair-first`, `manual re-audit`, `whole-run YELLOW`, `UNTRIAGED`, `hold` 성격이 남아 있다.
5. "돈 걸린 실전 재료"라고 자신 있게 말할 강한 증거가 부족하다.

`YES`는 아래가 모두 닫혀야만 가능:

1. `benchmark_freshness = current`
2. opening pacing 현재 `GREEN`
3. opening authority ambiguity 해소
4. active hold / repair note 없음
5. whole-run drag 없음
6. 실전 판매용 top shelf라고 증거 기반으로 말할 수 있음

---

## 3. Output Contract

모든 터미널의 산출 문서는 반드시 markdown으로 작성한다.

문서 형식은 아래를 고정한다.

```text
# <work_id> Deployable GREENPLUS Audit

Date: 2026-04-10
Auditor: terminal <n> / Sonnet 4.6
Status: final

## 1. Verdict
- DEPLOYABLE GREENPLUS = YES|NO
- Confidence = high|medium|low

## 2. Why
- 3~6개 bullet만 쓴다.
- 각 bullet은 반드시 파일 근거 + 절대 블록번호 또는 문서 근거를 포함한다.

## 3. Critical Evidence
- opening signboard:
- representative reevaluation:
- next battlefield ticket:
- whole-run risk:
- operator blocker:

## 4. One-line Ruling
- 한 문장으로 끝낸다.
```

추가 강제 규칙:

- opening은 반드시 `B01~B12`를 직접 확인한다.
- whole-run 이슈가 의심되면 반드시 중후반 블록을 절대 번호로 찍는다.
- "증거 없음"은 그대로 적고 상상으로 메우지 않는다.
- `repair roadmap`, `추가 작업 제안`, `서사 요약`은 쓰지 않는다.
- 산출물은 반드시 아래 지정 경로에 저장한다.

---

## 4. Terminal 1 Order

산출물 경로:

- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_01_golden_canary_deployable_greenplus_audit.md`

복붙용 오더:

```text
넌 터미널 1이다. 아래 파일들을 읽고 진행해라.

역할:
너는 "deployable GREENPLUS 재판정 감사관"이다.
목표는 이 작품이 지금 당장 실전 판매용 top shelf 재료인지 판정하는 것이다.
애매하면 무조건 NO다.

절대 규칙:
- repair 제안 금지
- 감상평 금지
- historical GREENPLUS alias/file명에 속지 말 것
- 최종 결론은 `DEPLOYABLE GREENPLUS = YES` 또는 `DEPLOYABLE GREENPLUS = NO` 둘 중 하나만 허용
- opening은 반드시 B01~B12 직접 확인
- 절대 블록 번호 사용: B02, B08 같은 형식
- 산출물 외 파일 수정 금지
- 산출물은 반드시 아래 경로 markdown 1개로 저장

산출물 경로:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_01_golden_canary_deployable_greenplus_audit.md

읽을 파일:
- C:\Users\wjjo\Desktop\글도비\treatments\01_tr_투자물_골든_카나리아 테스트_canonical_v1.json
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.json
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\deployable-greenplus-closeout.md
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-08\pair01-strict-rebenchmark-greenplus-report.md

특별 지시:
- 이 pair는 추가 승격 유력 후보 중 하나다.
- 하지만 opening authority가 truly closed인지 엄격히 보라.
- "historical GREENPLUS"와 "deployable GREENPLUS"를 절대 혼동하지 마라.
- 애매하면 NO.

출력 형식:
# 투자물_골든_카나리아 테스트_canonical_v1 Deployable GREENPLUS Audit

Date: 2026-04-10
Auditor: terminal 1 / Sonnet 4.6
Status: final

## 1. Verdict
- DEPLOYABLE GREENPLUS = YES|NO
- Confidence = high|medium|low

## 2. Why
- 3~6개 bullet만
- 각 bullet은 반드시 파일 근거 + 절대 블록번호 또는 문서 근거 포함

## 3. Critical Evidence
- opening signboard:
- representative reevaluation:
- next battlefield ticket:
- whole-run risk:
- operator blocker:

## 4. One-line Ruling
- 한 문장으로 끝낼 것
```

---

## 5. Terminal 2 Order

산출물 경로:

- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_02_pantech_cyworld_deployable_greenplus_audit.md`

복붙용 오더:

```text
넌 터미널 2다. 아래 파일들을 읽고 진행해라.

역할:
너는 "deployable GREENPLUS 재판정 감사관"이다.
목표는 이 작품이 지금 당장 실전 판매용 top shelf 재료인지 판정하는 것이다.
애매하면 무조건 NO다.

절대 규칙:
- repair 제안 금지
- 감상평 금지
- historical GREENPLUS alias/file명에 속지 말 것
- 최종 결론은 `DEPLOYABLE GREENPLUS = YES` 또는 `DEPLOYABLE GREENPLUS = NO`
- opening은 반드시 B01~B12 직접 확인
- 절대 블록 번호 사용
- 산출물 외 파일 수정 금지
- 산출물은 반드시 아래 경로 markdown 1개로 저장

산출물 경로:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_02_pantech_cyworld_deployable_greenplus_audit.md

읽을 파일:
- C:\Users\wjjo\Desktop\글도비\treatments\08_pantech_cyworld_reborn_tr_block_070_draft.json
- C:\Users\wjjo\Desktop\글도비\work_guards\08_pantech_cyworld_reborn.yaml
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\yellow-kill-first-spot-audit.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.json
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\deployable-greenplus-closeout.md

특별 지시:
- kill-first false positive가 한 번 있었던 pair다.
- 그렇다고 느슨하게 보지 마라.
- `repair-first YELLOW`를 정말 벗어났는지 아닌지만 판단하라.
- opening B01~B06을 특히 엄격히 보라.

출력 형식:
# pantech_cyworld_reborn Deployable GREENPLUS Audit

Date: 2026-04-10
Auditor: terminal 2 / Sonnet 4.6
Status: final

## 1. Verdict
- DEPLOYABLE GREENPLUS = YES|NO
- Confidence = high|medium|low

## 2. Why
- 3~6개 bullet만
- 각 bullet은 반드시 파일 근거 + 절대 블록번호 또는 문서 근거 포함

## 3. Critical Evidence
- opening signboard:
- representative reevaluation:
- next battlefield ticket:
- whole-run risk:
- operator blocker:

## 4. One-line Ruling
- 한 문장으로 끝낼 것
```

---

## 6. Terminal 3 Order

산출물 경로:

- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_03_office_checkup_deployable_greenplus_audit.md`

복붙용 오더:

```text
넌 터미널 3이다. 아래 파일들을 읽고 진행해라.

역할:
너는 "deployable GREENPLUS 재판정 감사관"이다.
목표는 이 작품이 지금 당장 실전 판매용 top shelf 재료인지 판정하는 것이다.
애매하면 무조건 NO다.

절대 규칙:
- repair 제안 금지
- 감상평 금지
- historical GREENPLUS alias/file명에 속지 말 것
- 최종 결론은 `DEPLOYABLE GREENPLUS = YES` 또는 `DEPLOYABLE GREENPLUS = NO`
- opening은 반드시 B01~B12 직접 확인
- 절대 블록 번호 사용
- 산출물 외 파일 수정 금지
- 산출물은 반드시 아래 경로 markdown 1개로 저장

산출물 경로:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_03_office_checkup_deployable_greenplus_audit.md

읽을 파일:
- C:\Users\wjjo\Desktop\글도비\treatments\07_office_checkup_next_day_tr_block_070_draft.json
- C:\Users\wjjo\Desktop\글도비\work_guards\07_office_checkup_next_day.yaml
- C:\Users\wjjo\Desktop\글도비\treatments\preprocess\office_checkup_next_day\material_bundle_summary.json
- C:\Users\wjjo\Desktop\글도비\treatments\phase0\office_checkup_next_day_phase0_design.json
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.json
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\deployable-greenplus-closeout.md

특별 지시:
- 이 pair는 opening bundle contract 표면은 있지만 실제 pacing이 YELLOW다.
- 문서상 contract가 있다고 해서 통과시키지 마라.
- declared contract와 actual delivery가 진짜 일치하는지만 보라.

출력 형식:
# office_checkup_next_day Deployable GREENPLUS Audit

Date: 2026-04-10
Auditor: terminal 3 / Sonnet 4.6
Status: final

## 1. Verdict
- DEPLOYABLE GREENPLUS = YES|NO
- Confidence = high|medium|low

## 2. Why
- 3~6개 bullet만
- 각 bullet은 반드시 파일 근거 + 절대 블록번호 또는 문서 근거 포함

## 3. Critical Evidence
- opening signboard:
- representative reevaluation:
- next battlefield ticket:
- whole-run risk:
- operator blocker:

## 4. One-line Ruling
- 한 문장으로 끝낼 것
```

---

## 7. Terminal 4 Order

산출물 경로:

- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_04_chaebol_ent_empire_deployable_greenplus_audit.md`

복붙용 오더:

```text
넌 터미널 4다. 아래 파일들을 읽고 진행해라.

역할:
너는 "deployable GREENPLUS 재판정 감사관"이다.
목표는 이 작품이 지금 당장 실전 판매용 top shelf 재료인지 판정하는 것이다.
애매하면 무조건 NO다.

절대 규칙:
- repair 제안 금지
- 감상평 금지
- historical GREENPLUS alias/file명에 속지 말 것
- 최종 결론은 `DEPLOYABLE GREENPLUS = YES` 또는 `DEPLOYABLE GREENPLUS = NO`
- opening은 반드시 B01~B12 직접 확인
- 절대 블록 번호 사용
- 산출물 외 파일 수정 금지
- 산출물은 반드시 아래 경로 markdown 1개로 저장

산출물 경로:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_04_chaebol_ent_empire_deployable_greenplus_audit.md

읽을 파일:
- C:\Users\wjjo\Desktop\글도비\treatments\03_chaebol_ent_empire_tr_block_070_draft.json
- C:\Users\wjjo\Desktop\글도비\work_guards\03_chaebol_ent_empire.yaml
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.json
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\deployable-greenplus-closeout.md
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\production-pair-opening-pacing-triage-wave.md

특별 지시:
- 첫 signboard 지연이 정말 실전 shelf를 막는 수준인지 확인하라.
- opening authority, signboard timing, next-ticket timing을 절대 블록 번호로 찍어라.
- `repair-first YELLOW`를 뒤집을 정도의 강한 증거가 없으면 NO.

출력 형식:
# chaebol_ent_empire Deployable GREENPLUS Audit

Date: 2026-04-10
Auditor: terminal 4 / Sonnet 4.6
Status: final

## 1. Verdict
- DEPLOYABLE GREENPLUS = YES|NO
- Confidence = high|medium|low

## 2. Why
- 3~6개 bullet만
- 각 bullet은 반드시 파일 근거 + 절대 블록번호 또는 문서 근거 포함

## 3. Critical Evidence
- opening signboard:
- representative reevaluation:
- next battlefield ticket:
- whole-run risk:
- operator blocker:

## 4. One-line Ruling
- 한 문장으로 끝낼 것
```

---

## 8. Terminal 5 Order

산출물 경로:

- `C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_05_wuxia_heavenly_physician_deployable_greenplus_audit.md`

복붙용 오더:

```text
넌 터미널 5다. 아래 파일들을 읽고 진행해라.

역할:
너는 "deployable GREENPLUS 재판정 감사관"이다.
목표는 이 작품이 지금 당장 실전 판매용 top shelf 재료인지 판정하는 것이다.
애매하면 무조건 NO다.

절대 규칙:
- repair 제안 금지
- 감상평 금지
- historical GREENPLUS alias/file명에 속지 말 것
- 최종 결론은 `DEPLOYABLE GREENPLUS = YES` 또는 `DEPLOYABLE GREENPLUS = NO`
- opening은 반드시 B01~B12 직접 확인
- whole-run 이슈가 의심되면 반드시 중후반 블록을 절대 번호로 찍을 것
- 산출물 외 파일 수정 금지
- 산출물은 반드시 아래 경로 markdown 1개로 저장

산출물 경로:
C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\terminal_05_wuxia_heavenly_physician_deployable_greenplus_audit.md

읽을 파일:
- C:\Users\wjjo\Desktop\글도비\treatments\09_wuxia_heavenly_physician_tr_block_070_draft.json
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\green-whole-run-pacing-reaudit-wave.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.md
- C:\Users\wjjo\Desktop\글도비\material_ssot\00_governance\production-pair-operational-registry-v1.json
- C:\Users\wjjo\Desktop\글도비\docs\2026-04-10\deployable-greenplus-closeout.md
- 필요시 관련 benchmark 문서

특별 지시:
- opening이 아니라 whole-run blocker가 핵심이다.
- 특히 B61/B65/B66/B70 late drag를 직접 확인하라.
- opening이 좋아도 whole-run YELLOW면 무조건 NO다.

출력 형식:
# wuxia_heavenly_physician Deployable GREENPLUS Audit

Date: 2026-04-10
Auditor: terminal 5 / Sonnet 4.6
Status: final

## 1. Verdict
- DEPLOYABLE GREENPLUS = YES|NO
- Confidence = high|medium|low

## 2. Why
- 3~6개 bullet만
- 각 bullet은 반드시 파일 근거 + 절대 블록번호 또는 문서 근거 포함

## 3. Critical Evidence
- opening signboard:
- representative reevaluation:
- next battlefield ticket:
- whole-run risk:
- operator blocker:

## 4. One-line Ruling
- 한 문장으로 끝낼 것
```

---

## 9. Operator Note

현재 기본 기대치는 이렇다.

- terminal 1 `골든 카나리아`: 추가 승격 가능성 가장 높음
- terminal 2 `팬택/싸이월드`: false-positive 정리 여부 확인
- terminal 3 `office`: contract declared지만 actual delivery가 막히는지 확인
- terminal 4 `chaebol_ent_empire`: opening delay가 진짜 deployable blocker인지 확인
- terminal 5 `wuxia`: whole-run YELLOW 재확정 가능성 높음

이 문서의 목적은 `한꺼번에 올리기`가 아니라:

- `YES`는 매우 드물게 허용하고
- 나머지는 왜 `NO`인지 빠르게 폐쇄하는 것

즉, `느슨한 호평`이 아니라 `실전 판매 shelf 감사`다.
