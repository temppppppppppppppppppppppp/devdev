# 현대 현판 4작품 재료수집 마스터 오더 v1

> 인코딩: **UTF-8 only**
> 작성일: 2026-03-30
> 목적: 현대 현판 기업물/재벌 외피 레퍼런스 4작품의 A/B 재료수집 오더, 저장 sink, audit 재사용 규칙을 한 문서에 고정

---

## 0. 이 문서의 목적

이 문서는 아래 4작품의 재료수집을 `채팅 응답`이 아니라 `저장 가능한 reference card` 단위로 모으기 위한 운영 패키지다.

- `독식하는 재벌 3세`
- `금수저 투자백서`
- `김 대리는 벼락부자`
- `국세청 망나니`

핵심:

- 작품별 A/B 트랙을 분리한다
- 결과는 `few-shot-bank/cards/` 아래 파일로 모은다
- `reference_card_manifest.json`을 기준 집합판으로 쓴다
- 이후 Codex는 저장된 카드 파일만 읽고 audit / 재조합 / director synthesis를 수행한다

---

## 1. 수집 Sink

- card sink root:
  - `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards`
- collection manifest:
  - `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json`

저장 규칙:

- 트랙 1개 = 파일 1개
- 파일명: `{slug}_{track}.md`
- 채팅창 응답만 있고 sink 파일이 없으면 `미수집`
- 직접 저장이 안 되면 wrapper 응답을 저장한 뒤에만 수집 완료로 본다

manifest 상태 계약:

- `status`: `pending -> source_checked -> saved -> audited -> synthesized`
- 예외 `status`: `rejected`
- `audit_status`: `pending | pass | fail | needs_reaudit`
- `pending -> audited` 직접 점프 금지
- `audit_status = fail`이면 `status = audited`로 올리지 않는다

wrapper:

- `=== BEGIN CARD {slug}_{track} ===`
- 카드 본문
- `=== END CARD {slug}_{track} ===`

---

## 2. Source Preflight

모든 오더는 분석 전에 아래 4개를 먼저 확인한다.

1. 읽을 정확한 source path
2. 폴더/파일에서 검출한 정확한 작품명
3. `ep1`, `ep5`, `ep10`, `ep20`, `last` 또는 동급 체크포인트 접근 가능 여부
4. 이번 오더의 허용 source scope

즉시 FAIL:

- 작품명이 오더와 다르다
- 유사 제목 다른 작품을 대신 읽었다
- `Block 1`/`ep1`이 없는데 추정으로 채웠다
- 허용되지 않은 source scope를 썼다

---

## 3. Audit-ready 기준

Codex가 이후 audit/재조합에 쓸 수 있으려면 아래 6개가 필요하다.

1. sink 파일 존재
2. `SOURCE CHECK` 섹션 존재
3. `Findings First` + `Master Reference Card v1` 존재
4. `Slim Reference Card v1` 존재
5. `must_not_copy`, `contamination_risk`, `chapter_refs` 존재
6. `reference_card_manifest.json`의 해당 entry가 최소 `saved`, audit 뒤에는 `audited` 또는 `synthesized` 상태로 갱신

Codex audit 기본 체크:

- 소스 오염 여부
- `Block 1`/초반 보간 여부
- findings와 evidence 간 정합성
- 현대 현판 이식 가능 요소와 오염 요소 분리 여부
- `must_not_copy`가 고유 요소를 제대로 격리했는지
- `Slim Reference Card v1`이 실제 `source_manifest` handoff에 쓸 수 있을 만큼 압축돼 있는지

---

## 4. 수집 대상 표

| 작품 | 트랙 | source scope | source path | output path |
| --- | --- | --- | --- | --- |
| 독식하는 재벌 3세 | A | `local_only` | `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\재벌물_독식하는 재벌 3세` | `...\cards\dokshik_jaebeol3se_A.md` |
| 독식하는 재벌 3세 | B | `local_only` | `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\재벌물_독식하는 재벌 3세` | `...\cards\dokshik_jaebeol3se_B.md` |
| 금수저 투자백서 | A | `local_only` | `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\투자물_금수저 투자백서` | `...\cards\geumsujeo_tujabaekseo_A.md` |
| 금수저 투자백서 | B | `local_only` | `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\투자물_금수저 투자백서` | `...\cards\geumsujeo_tujabaekseo_B.md` |
| 김 대리는 벼락부자 | A | `nas_only` | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 벼락부자(글고래)\1_원고\epub` | `...\cards\gim_daerineun_byeorakbuja_A.md` |
| 김 대리는 벼락부자 | B | `nas_only` | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 벼락부자(글고래)\1_원고\epub` | `...\cards\gim_daerineun_byeorakbuja_B.md` |
| 국세청 망나니 | A | `nas_only` | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\국세청 망나니(동면거북이)\1_원고\기타\txt` | `...\cards\guksecheong_mangnani_A.md` |
| 국세청 망나니 | B | `nas_only` | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\국세청 망나니(동면거북이)\1_원고\기타\txt` | `...\cards\guksecheong_mangnani_B.md` |

---

## 5. 공통 오더 블록

각 오더 맨 앞에 아래 블록을 붙인다.

```text
공통 저장 규칙:
- save_target: {output_path}
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- source preflight PASS 시 manifest의 해당 entry status를 `source_checked`로 갱신하라.
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- self-audit PASS까지 끝나면 `audit_status = pass`, `status = audited`로 갱신하라.
- self-audit FAIL이면 `audit_status = fail`, 필요 시 `status = rejected` 또는 `status = saved` 유지 후 `audit_status = needs_reaudit`로 남겨라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD {slug}_{track} ===
- 카드 본문
- === END CARD {slug}_{track} ===

공통 카드 규칙:
- `Master Reference Card v1` 아래에 `Slim Reference Card v1`을 반드시 추가하라.
- `Slim Reference Card v1`은 `source_manifest`에 바로 옮길 10~14개 필드만 남긴 handoff 카드여야 한다.
- raw 원고에서 바로 slim만 만들지 말고, 저장 가능한 master card를 먼저 만들라.

공통 소스 규칙:
- source scope는 오더 본문에 적힌 범위만 허용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.
```

---

## 5A. Sonnet 4.6 Compact Launcher

Sonnet 4.6으로 작품별 A/B 카드를 돌릴 때는 아래 축약 런처를 쓴다.

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `{work_title}`의 `{track_label}`만 수행한다.
창작 금지. 기획안 제안 금지. 감상문 금지. 진행 보고 금지. 최종 답변만 출력.

정본 기준 문서:
C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\2026-03-30_modern_business_reference_master_order.md

반드시 따를 섹션:
- `## 1. 수집 Sink`
- `## 2. Source Preflight`
- `## 3. Audit-ready 기준`
- `{work_section}`
- `{track_section}`

핵심 규칙:
- source scope는 `{source_scope}`다.
- `{source_path}`만 사용한다.
- source preflight 없이 본분석 금지.
- 작품명이 1글자라도 다르면 즉시 FAIL.
- ep1/Block 1 접근 실패 시 추정/보간 금지.
- `Master Reference Card v1` + `Slim Reference Card v1` 둘 다 필수.
- 직접 저장 가능하면 `{output_path}`에 저장.
- manifest:
  - `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json`
- 직접 저장 불가면 wrapper 규칙으로만 반환.
- 이번 턴은 `{work_title} / {track}`만 수행하고 다른 작품/다른 트랙은 건드리지 마라.

반환 형식:
- PASS면 문서 규격 그대로 출력
- FAIL이면 아래 2줄만 출력
FAIL
reason: {정확한 실패 사유}
```

운용 메모:

- Sonnet은 `작품별 + 트랙별`로만 쪼개서 던진다
- source drift 위험이 높으면 먼저 `SOURCE CHECK`만 보게 하고 본분석은 다음 턴으로 넘긴다
- Sonnet 결과는 Codex audit 전까지 `saved`까지만 올리고, 재감리 후 `audited`로 올린다

---

## 5B. 추가 NAS 조사 후보 4개

아래 4개는 다음 확장 라운드의 정식 추가 후보군이다. 이 문서에 A/B 오더까지 포함해 한 번에 잠근다.

| 우선순위 | 작품 | 기능 | NAS 경로 |
| --- | --- | --- | --- |
| 1 | `대한민국 절대 재벌` | 정통 재벌 스케일, 국내 사업 지배력, 거물화 이미지 | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\대한민국 절대 재벌(백범(白凡))\1_원고` |
| 2 | `신흥재벌` | 성장형 재벌, 사업 확장, 신흥 세력의 상승 궤적 | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\신흥재벌(박재학)\1_원고` |
| 3 | `재벌생활기록부` | 재벌 외피, 운영/조직/생활밀착형 재벌 감각 | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\재벌생활기록부(백범)\1_원고` |
| 4 | `김 대리는 인생이 너무 가볍다` | 현대 직장인 톤, 가벼운 진입, 생활 감각형 현대 현판 | `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 인생이 너무 가볍다(차라리)\1_원고` |

선정 이유:

- 기존 세트가 약한 `정통 국내 재벌 스케일`, `성장형 재벌`, `재벌 운영/생활 감각`, `현대 직장인 톤`을 보강한다
- 모두 NAS `02_연재` 하위에서 `1_원고` 존재를 확인했다
- 다음 10개 풀로 확장할 때 기능 중복이 적다

예비 1순위:

- `검은 머리 미국 대재벌!`
  - 경로: `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\검은 머리 미국 대재벌!(흑곰작가)\1_원고`
  - 용도: 글로벌 재벌 스케일 / 국제 사업 / 해외 확장 보강

---

## 6. 독식하는 재벌 3세

### 6.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `독식하는 재벌 3세`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\dokshik_jaebeol3se_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD dokshik_jaebeol3se_A ===
- 카드 본문
- === END CARD dokshik_jaebeol3se_A ===

공통 소스 규칙:
- source scope는 `local_only`다.
- 이번 턴은 `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\재벌물_독식하는 재벌 3세`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- 유사 제목 다른 작품을 대신 읽으면 전체 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 간판 맛을 해체한다.
- 특히 `opening_humiliation`, `protagonist edge`, `Block 1 spike`, `first reward`, `growth_1_10`만 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- ep1_file_name
- ep5_file_name
- ep10_file_name
- ep20_file_name
- final source scope 판정 1줄

2. Findings First
- 초반부에서 현대 현판 기업물용으로 쓸 수 있는 구조 재료 5~6개
- 각 항목은 1~2문장
- 반드시 `왜 쓸모 있는지`까지 붙여라

3. 초반 전용 카드
- opening_humiliation
- starting_deficit
- protagonist_edge
- what
- how
- ep1_hook
- ep1_first_saida
- ep1_first_recognition
- ep1_end_hook
- block1_summary
- block1_spike_type
- first_reward
- reward_stay_method
- growth_1_10
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- opening_humiliation
- protagonist_edge
- what
- how
- block1_spike
- first_reward
- growth_axis
- authority_gain_route
- sector_expansion_path
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 마지막 3줄
- 초반부를 레퍼런스로 쓸 이유
- 가장 강한 Block 1 재료 1개
- 절대 베끼면 안 되는 초반 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 6.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `독식하는 재벌 3세`의 성장 구조와 거물화 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\dokshik_jaebeol3se_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD dokshik_jaebeol3se_B ===
- 카드 본문
- === END CARD dokshik_jaebeol3se_B ===

공통 소스 규칙:
- source scope는 `local_only`다.
- 이번 턴은 `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\재벌물_독식하는 재벌 3세`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- 유사 제목 다른 작품을 대신 읽으면 전체 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `돈 -> 권위 -> 지배력 -> 그룹 스케일`로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `sector_expansion_path`, `authority_gain_route`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- final source scope 판정 1줄

2. Findings First
- 현대 현판 기업물 장편 설계용으로 쓸 수 있는 구조 재료 5~6개
- 각 항목은 1~2문장
- 반드시 `왜 쓸모 있는지`까지 붙여라

3. 확장 구조 전용 카드
- core_fantasy
- money_flow
- power_flow
- deal_types
- stakeholders
- growth_11_30
- growth_31_60
- growth_61_100
- sector_expansion_path
- authority_gain_route
- control_levers
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- core_fantasy
- money_flow
- power_flow
- authority_gain_route
- sector_expansion_path
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 현대 현판 적용 분해
- 바로 이식 가능
- 변형 후 사용
- 폐기

6. 마지막 3줄
- 이 작품의 장편 구조를 레퍼런스로 쓰는 이유
- 가장 강한 거물화 재료 1개
- 절대 베끼면 안 되는 확장 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 7. 금수저 투자백서

### 7.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `금수저 투자백서`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\geumsujeo_tujabaekseo_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD geumsujeo_tujabaekseo_A ===
- 카드 본문
- === END CARD geumsujeo_tujabaekseo_A ===

공통 소스 규칙:
- source scope는 `local_only`다.
- 이번 턴은 `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\투자물_금수저 투자백서`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 간판 맛을 해체한다.
- 특히 `opening_humiliation`, `protagonist edge`, `Block 1 spike`, `first reward`, `growth_1_10`만 강하게 뽑는다.
- 투자물이라도 숫자만 보지 말고, 주인공 우위가 어떻게 권위/판세 장악으로 번지는지 보라.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- ep1_file_name
- ep5_file_name
- ep10_file_name
- ep20_file_name
- final source scope 판정 1줄

2. Findings First
- 초반부에서 현대 현판 기업물용으로 쓸 수 있는 구조 재료 5~6개

3. 초반 전용 카드
- opening_humiliation
- starting_deficit
- protagonist_edge
- what
- how
- ep1_hook
- ep1_first_saida
- ep1_first_recognition
- ep1_end_hook
- block1_summary
- block1_spike_type
- first_reward
- reward_stay_method
- growth_1_10
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- opening_humiliation
- protagonist_edge
- what
- how
- block1_spike
- first_reward
- growth_axis
- authority_gain_route
- sector_expansion_path
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 마지막 3줄
- 초반부를 레퍼런스로 쓸 이유
- 가장 강한 Block 1 재료 1개
- 절대 베끼면 안 되는 초반 요소 1개

한국어.
findings first.
줄거리 요약 금지.
고유 설정 복제 금지.
```

### 7.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `금수저 투자백서`의 성장 구조와 거물화 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\geumsujeo_tujabaekseo_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD geumsujeo_tujabaekseo_B ===
- 카드 본문
- === END CARD geumsujeo_tujabaekseo_B ===

공통 소스 규칙:
- source scope는 `local_only`다.
- 이번 턴은 `C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\원고\투자물_금수저 투자백서`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `정보격차 -> 돈 -> 협상력 -> 시장 지배력`으로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `sector_expansion_path`, `authority_gain_route`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.
- 투자물이더라도 주가놀이가 아니라, 기업/딜/사람/기관 장악 축이 어떻게 붙는지 보라.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- final source scope 판정 1줄

2. Findings First
- 현대 현판 기업물 장편 설계용으로 쓸 수 있는 구조 재료 5~6개

3. 확장 구조 전용 카드
- core_fantasy
- money_flow
- power_flow
- deal_types
- stakeholders
- growth_11_30
- growth_31_60
- growth_61_100
- sector_expansion_path
- authority_gain_route
- control_levers
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- core_fantasy
- money_flow
- power_flow
- authority_gain_route
- sector_expansion_path
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 현대 현판 적용 분해
- 바로 이식 가능
- 변형 후 사용
- 폐기

6. 마지막 3줄
- 이 작품의 장편 구조를 레퍼런스로 쓰는 이유
- 가장 강한 거물화 재료 1개
- 절대 베끼면 안 되는 확장 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 8. 김 대리는 벼락부자

### 8.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `김 대리는 벼락부자`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\gim_daerineun_byeorakbuja_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD gim_daerineun_byeorakbuja_A ===
- 카드 본문
- === END CARD gim_daerineun_byeorakbuja_A ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 벼락부자(글고래)\1_원고\epub`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 간판 맛을 해체한다.
- 특히 `opening_humiliation`, `protagonist edge`, `Block 1 spike`, `first reward`, `growth_1_10`을 강하게 뽑는다.
- 직장인 출발이 어떻게 사업가/운영자 감각으로 넘어가는지 보라.
- 돈만이 아니라 첫 인정, 첫 거래선, 첫 운영권, 첫 우위가 어떻게 붙는지 보라.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- ep1_file_name
- ep5_file_name
- ep10_file_name
- ep20_file_name
- final source scope 판정 1줄

2. Findings First
- 초반부에서 현대 현판 기업물용으로 쓸 수 있는 구조 재료 5~6개
- 각 항목은 1~2문장
- 반드시 `왜 쓸모 있는지`까지 붙여라

3. 초반 전용 카드
- opening_humiliation
- starting_deficit
- protagonist_edge
- what
- how
- ep1_hook
- ep1_first_saida
- ep1_first_recognition
- ep1_end_hook
- block1_summary
- block1_spike_type
- first_reward
- reward_stay_method
- growth_1_10
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- opening_humiliation
- protagonist_edge
- what
- how
- block1_spike
- first_reward
- growth_axis
- authority_gain_route
- sector_expansion_path
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 마지막 3줄
- 초반부를 레퍼런스로 쓸 이유
- 가장 강한 Block 1 재료 1개
- 절대 베끼면 안 되는 초반 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 8.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `김 대리는 벼락부자`의 성장 구조와 사업 확장 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\gim_daerineun_byeorakbuja_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD gim_daerineun_byeorakbuja_B ===
- 카드 본문
- === END CARD gim_daerineun_byeorakbuja_B ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 벼락부자(글고래)\1_원고\epub`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `회사원 출발 -> 현금흐름 확보 -> 사업 확장 -> 상권/브랜드/인맥 장악`으로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `sector_expansion_path`, `authority_gain_route`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.
- 숫자 증가보다 `운영권`, `거래선`, `상권`, `조직 통제`, `사업가 권위`가 어떻게 붙는지 보라.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- final source scope 판정 1줄

2. Findings First
- 현대 현판 기업물 장편 설계용으로 쓸 수 있는 구조 재료 5~6개
- 각 항목은 1~2문장
- 반드시 `왜 쓸모 있는지`까지 붙여라

3. 확장 구조 전용 카드
- core_fantasy
- money_flow
- power_flow
- deal_types
- stakeholders
- growth_11_30
- growth_31_60
- growth_61_100
- sector_expansion_path
- authority_gain_route
- control_levers
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- core_fantasy
- money_flow
- power_flow
- authority_gain_route
- sector_expansion_path
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 현대 현판 적용 분해
- 바로 이식 가능
- 변형 후 사용
- 폐기

6. 마지막 3줄
- 이 작품의 장편 구조를 레퍼런스로 쓰는 이유
- 가장 강한 거물화 재료 1개
- 절대 베끼면 안 되는 확장 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 9. 국세청 망나니

### 9.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `국세청 망나니`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\guksecheong_mangnani_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD guksecheong_mangnani_A ===
- 카드 본문
- === END CARD guksecheong_mangnani_A ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\국세청 망나니(동면거북이)\1_원고\기타\txt`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 간판 맛을 해체한다.
- 특히 `opening_humiliation`, `protagonist edge`, `Block 1 spike`, `first reward`, `growth_1_10`을 강하게 뽑는다.
- 핵심은 `권위 행사`, `게이트키퍼 압박`, `공개 굴욕 회수`, `제도권 안에서 상대를 찍어 누르는 맛`이다.
- 돈보다 `지위`, `압박력`, `말의 무게`, `상대가 겁먹는 구조`를 보라.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- ep1_file_name
- ep5_file_name
- ep10_file_name
- ep20_file_name
- final source scope 판정 1줄

2. Findings First
- 초반부에서 현대 현판 기업물용으로 쓸 수 있는 구조 재료 5~6개
- 각 항목은 1~2문장
- 반드시 `왜 쓸모 있는지`까지 붙여라

3. 초반 전용 카드
- opening_humiliation
- starting_deficit
- protagonist_edge
- what
- how
- ep1_hook
- ep1_first_saida
- ep1_first_recognition
- ep1_end_hook
- block1_summary
- block1_spike_type
- first_reward
- reward_stay_method
- growth_1_10
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- opening_humiliation
- protagonist_edge
- what
- how
- block1_spike
- first_reward
- growth_axis
- authority_gain_route
- sector_expansion_path
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 마지막 3줄
- 초반부를 레퍼런스로 쓸 이유
- 가장 강한 Block 1 재료 1개
- 절대 베끼면 안 되는 초반 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 9.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `국세청 망나니`의 성장 구조와 권력 확장 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\guksecheong_mangnani_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD guksecheong_mangnani_B ===
- 카드 본문
- === END CARD guksecheong_mangnani_B ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\국세청 망나니(동면거북이)\1_원고\기타\txt`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `정보 우위 -> 제도권 권한 -> 공개 압박 -> 위상 상승 -> 거물화`로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `authority_gain_route`, `control_levers`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.
- 사업물 재조합용이므로, 세무/조사 디테일 그 자체보다 `권위가 작동하는 방식`을 뽑아라.
- `상대가 왜 굴복하는지`, `주인공의 말과 행동이 왜 무게를 갖는지`, `조직 안팎에서 어떻게 세력이 붙는지`를 보라.

반환 형식:
1. SOURCE CHECK
- folder_path
- detected_work_title
- available_episode_range
- final source scope 판정 1줄

2. Findings First
- 현대 현판 기업물 장편 설계용으로 쓸 수 있는 구조 재료 5~6개
- 각 항목은 1~2문장
- 반드시 `왜 쓸모 있는지`까지 붙여라

3. 확장 구조 전용 카드
- core_fantasy
- money_flow
- power_flow
- deal_types
- stakeholders
- growth_11_30
- growth_31_60
- growth_61_100
- sector_expansion_path
- authority_gain_route
- control_levers
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- chapter_refs

4. Slim Reference Card v1
- source_label
- usable_lane
- usable_sector
- core_fantasy
- money_flow
- power_flow
- authority_gain_route
- sector_expansion_path
- tycoon_path
- endgame_image
- must_borrow
- must_not_copy
- contamination_risk
- source_manifest_ready_label

5. 현대 현판 적용 분해
- 바로 이식 가능
- 변형 후 사용
- 폐기

6. 마지막 3줄
- 이 작품의 장편 구조를 레퍼런스로 쓰는 이유
- 가장 강한 거물화 재료 1개
- 절대 베끼면 안 되는 확장 요소 1개

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 10. 대한민국 절대 재벌

### 10.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `대한민국 절대 재벌`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\daehanminguk_absolute_jaebeol_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD daehanminguk_absolute_jaebeol_A ===
- 카드 본문
- === END CARD daehanminguk_absolute_jaebeol_A ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\대한민국 절대 재벌(백범(白凡))\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 정통 재벌 간판 맛을 해체한다.
- 특히 `opening_humiliation`, `protagonist edge`, `Block 1 spike`, `first_reward`, `growth_1_10`을 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 초반 전용 카드
4. Slim Reference Card v1
5. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 10.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `대한민국 절대 재벌`의 성장 구조와 거물화 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\daehanminguk_absolute_jaebeol_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD daehanminguk_absolute_jaebeol_B ===
- 카드 본문
- === END CARD daehanminguk_absolute_jaebeol_B ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\대한민국 절대 재벌(백범(白凡))\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `돈 -> 권위 -> 지배력 -> 재벌 스케일`로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `sector_expansion_path`, `authority_gain_route`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 확장 구조 전용 카드
4. Slim Reference Card v1
5. 현대 현판 적용 분해
6. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 11. 신흥재벌

### 11.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `신흥재벌`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\sinheung_jaebeol_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD sinheung_jaebeol_A ===
- 카드 본문
- === END CARD sinheung_jaebeol_A ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\신흥재벌(박재학)\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 성장형 재벌 간판 맛을 해체한다.
- 특히 `opening_humiliation`, `protagonist_edge`, `Block 1 spike`, `first_reward`, `growth_1_10`을 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 초반 전용 카드
4. Slim Reference Card v1
5. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 11.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `신흥재벌`의 성장 구조와 사업 확장 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\sinheung_jaebeol_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD sinheung_jaebeol_B ===
- 카드 본문
- === END CARD sinheung_jaebeol_B ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\신흥재벌(박재학)\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `성장형 기업 -> 재벌화`로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `sector_expansion_path`, `authority_gain_route`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 확장 구조 전용 카드
4. Slim Reference Card v1
5. 현대 현판 적용 분해
6. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 12. 재벌생활기록부

### 12.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `재벌생활기록부`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\jaebeol_saenghwal_girokbu_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD jaebeol_saenghwal_girokbu_A ===
- 카드 본문
- === END CARD jaebeol_saenghwal_girokbu_A ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\재벌생활기록부(백범)\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 재벌 운영/생활 감각을 해체한다.
- 특히 `opening_humiliation`, `protagonist_edge`, `Block 1 spike`, `first_reward`, `growth_1_10`을 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 초반 전용 카드
4. Slim Reference Card v1
5. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 12.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `재벌생활기록부`의 성장 구조와 운영 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\jaebeol_saenghwal_girokbu_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD jaebeol_saenghwal_girokbu_B ===
- 카드 본문
- === END CARD jaebeol_saenghwal_girokbu_B ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\재벌생활기록부(백범)\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `재벌 외피 -> 운영권 -> 조직 장악`으로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `authority_gain_route`, `sector_expansion_path`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 확장 구조 전용 카드
4. Slim Reference Card v1
5. 현대 현판 적용 분해
6. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 13. 김 대리는 인생이 너무 가볍다

### 13.1 A 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `김 대리는 인생이 너무 가볍다`의 초반부만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\gim_daerineun_insaengi_neomu_gabyeopda_A.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD gim_daerineun_insaengi_neomu_gabyeopda_A ===
- 카드 본문
- === END CARD gim_daerineun_insaengi_neomu_gabyeopda_A ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 인생이 너무 가볍다(차라리)\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 1, 5, 10, 20화 중심
- 필요 시 30화까지 보조 확인

목표:
- 이 작품의 초반 클릭감과 현대 직장인 톤을 해체한다.
- 특히 `opening_humiliation`, `protagonist_edge`, `Block 1 spike`, `first_reward`, `growth_1_10`을 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 초반 전용 카드
4. Slim Reference Card v1
5. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

### 13.2 B 오더

```text
서사 파이프라인 재료수집 오더다.
이번 턴은 `김 대리는 인생이 너무 가볍다`의 성장 구조와 현대 현판 확장 축만 분석한다.
창작 금지. 기획안 제안 금지.

공통 저장 규칙:
- save_target: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\cards\gim_daerineun_insaengi_neomu_gabyeopda_B.md
- collection_manifest: C:\Users\wjjo\Desktop\글도비\docs\실물기반 사각지대 테스트\few-shot-bank\reference_card_manifest.json
- 직접 저장 가능하면 save_target에 저장하고, manifest의 해당 entry status를 `saved`로 갱신하라.
- 직접 저장 불가면 아래 wrapper로만 반환하라.
- === BEGIN CARD gim_daerineun_insaengi_neomu_gabyeopda_B ===
- 카드 본문
- === END CARD gim_daerineun_insaengi_neomu_gabyeopda_B ===

공통 소스 규칙:
- source scope는 `nas_only`다.
- 이번 턴은 `\\172.16.10.120\소설사업부\판무팀_ssot\02_연재\김 대리는 인생이 너무 가볍다(차라리)\1_원고`만 사용한다.
- 작품명이 1글자라도 다르면 즉시 FAIL이다.
- ep1/Block 1 접근 실패 시 추정/보간하지 말고 즉시 FAIL이다.

읽기 범위:
- 10, 20, 30, 40, 50, last available
- 필요 시 1~5화는 시작점 확인용으로만 참조

목표:
- 이 작품이 어떻게 `직장인 진입 -> 생활 감각 -> 현대 현판 확장`으로 커지는지 해체한다.
- 특히 `growth_11_30`, `growth_31_60`, `authority_gain_route`, `sector_expansion_path`, `tycoon_path`, `endgame_image`를 강하게 뽑는다.

반환 형식:
1. SOURCE CHECK
2. Findings First
3. 확장 구조 전용 카드
4. Slim Reference Card v1
5. 현대 현판 적용 분해
6. 마지막 3줄

한국어.
findings first.
줄거리 요약 금지.
감상문 금지.
고유 설정 복제 금지.
```

---

## 14. 3-Pass Self Audit

### Pass 1. 계약 정합성

- 12작품 풀 확장을 염두에 두고 8작품 A/B 오더, source scope, sink 경로, manifest 경로를 한 문서 안에서 충돌 없이 잠갔다.

### Pass 2. 실행 가능성

- 저장 권한이 있어도, 없어도 같은 sink 체계로 운영할 수 있게 wrapper 규칙을 넣었다.

### Pass 3. 재사용성

- 이후 Codex가 채팅 로그가 아니라 저장된 card 파일과 manifest를 기준으로 audit / synthesis / director recomposition을 수행할 수 있게 했다.
