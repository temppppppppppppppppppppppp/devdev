# Production Pair Opening Pacing Triage Wave

Date: 2026-04-10
Status: active operator wave
Scope: currently discoverable live `TR` inventory (`15` pairs)
Primary goal:
- `repair` wave에 들어가기 전에 `폐기 / 재감리 / 유지` 버킷을 먼저 고정한다.

---

## 1. Reading Rule

- 이 wave의 판정은 `benchmark alias`와 별개다.
- `RED / YELLOW / GREEN / UNTRIAGED`은 여기서 **opening pacing triage grade**를 뜻한다.
- `GREENPLUS / GREEN / RED` alias snapshot은 기존 benchmark surface이며, 이번 wave가 자동으로 alias filename을 바꾸지는 않는다.
- 단, `RED` triage는 operator 입장에서 `negative exemplar archive` 우선으로 읽는다.

---

## 2. Method

Execution runner:

- `scripts/production_pair_opening_pacing_triage_runner.py`

Current wave order:

1. `opening_contract_declared=true`면 declared contract gate를 그대로 읽는다.
2. 대부분의 live pair는 아직 opening contract field가 없으므로, 이번 wave는 주로 `legacy heuristic`을 쓴다.
3. 단, `B01~B10` opening window가 실제 payload에 완전하게 존재하지 않으면 `UNTRIAGED`로 보류한다.
4. legacy heuristic은 `location.place / location.type / title`에서 opening `macro battlefield`를 추정한다.
5. 그다음 아래를 본다.

- opening main macro battlefield overstay (`B02~B08`)
- first public signboard timing
- representative reevaluation timing
- next battlefield ticket timing

Current discard-first law:

- `RED`:
  - opening main macro battlefield overstay + public signboard `B09+`
  - 또는 declared contract 기준 `PACE-004`
- `UNTRIAGED`:
  - opening pacing triage에 필요한 `B01~B10` evidence window가 비어 있는 케이스
- `YELLOW`:
  - late signboard
  - late reevaluation
  - late ticket
  - overstay but 아직 discard 확정까지는 아닌 케이스
- `GREEN`:
  - 현 시점 evidence로는 discard-grade opening pacing failure가 보이지 않는 케이스

---

## 3. Current Result

Summary:

- `RED`: `3`
- `YELLOW`: `2`
- `GREEN`: `9`
- `UNTRIAGED`: `1`

Operator reading:

- `RED`: repair queue로 바로 보내지 않는다. 먼저 `negative exemplar archive`로 격리한다.
- `YELLOW`: 수리 후보는 맞지만, repair에 넣기 전에 `manual re-audit`를 한 번 더 거친다.
- `GREEN`: 현행 inventory에 남겨도 된다. 다만 이번 wave가 `legacy heuristic` 기반이면 opening exemplar 청결 인증과 동일시하지 않는다.
- `UNTRIAGED`: opening evidence window가 부족하므로 `repair / discard` 어느 쪽에도 아직 넣지 않는다.
- `kill-first review` queue는 `docs/2026-04-10/yellow-kill-first-spot-audit.md`의 수동 판정으로 최종 확정한다.
- `forensic re-audit` queue는 `docs/2026-04-10/jaebeol3se_loss_line_forensic_spot_audit.md` 같은 work-level spot audit으로 종료할 수 있다.

---

## 4. RED Archive Candidate

### 4.1 `chaebol_allowance_zero`

- triage grade: `RED`
- action: `negative_exemplar_archive`
- evidence: `legacy_heuristic`
- ruling:
  - main opening macro battlefield = `장례 운영축`
  - `B02~B08` overstay
  - first public signboard = `B09`

Shortest ruling:

`장례 운영축이 opening main battlefield를 오래 먹고 있고, signboard 폭발이 B09까지 밀려 repair보다 폐기/격리가 먼저다.`

This pair remains the anchor negative exemplar for the current false-pass memory.

### 4.2 `jangyeongshil_industrial_revolution`

- prior automated grade: `YELLOW`
- spot-audit override: `RED`
- action: `negative exemplar archive`
- artifact:
  - `docs/2026-04-10/yellow-kill-first-spot-audit.md`
- ruling:
  - work guard가 요구한 opening 영수증이 `B02/B03/B04`가 아니라 `B07/B09/B10`까지 밀린다.
  - 이 pair는 단순 late signboard가 아니라 work-level opening promise miss다.

Shortest ruling:

`jangyeongshil_industrial_revolution`은 historical positive alias와 별개로, 현재 opening pacing 운영 판단에서는 archive-first가 맞다.

### 4.3 `jaebeol3se_loss_line`

- prior automated grade: `YELLOW`
- spot-audit override: `RED`
- action: `negative exemplar archive`
- artifact:
  - `docs/2026-04-10/jaebeol3se_loss_line_forensic_spot_audit.md`
- ruling:
  - work guard는 `1화 내 첫 사이다`와 `3화 내 간판 폭발`을 요구하지만,
  - live opening receipt가 `B04 -> B06 -> B09 -> B11 -> B12 -> B13`으로 늘어진다.
  - 그리고 이 지연은 TR 흔들림이 아니라 Phase0 opening 설계 자체에 박혀 있다.

Shortest ruling:

`jaebeol3se_loss_line`은 forensic 보류보다 archive-first가 싸다.

---

## 5. YELLOW Split Queue

### 5.1 `jaebeol3se_loss_line`

- next battlefield ticket late: `B09`
- current ruling:
  - `RED`로 승격되어 YELLOW queue에서 제외

### 5.2 `jangyeongshil_industrial_revolution`

- signboard late: `B10`
- current ruling:
  - `RED`로 승격되어 YELLOW queue에서 제외

### 5.3 `office_checkup_next_day`

- main macro battlefield = `오피스/의사결정 축`
- overstay through `B08`
- reevaluation late: `B08`
- current ruling: `repair-first YELLOW`
- operator reading:
  - `02`처럼 곧바로 폐기할 정도는 아니지만, overstay형 opening 둔화 후보다.
  - dense 쪽이라 salvage value가 남아 있다.

### 5.4 `pantech_cyworld_reborn`

- prior automated reevaluation read: `B10`
- current ruling: `GREEN`
- operator reading:
  - same-day bounded repair made the existing early reevaluation surface explicit enough for the legacy heuristic to read `B02`
  - bounded cadence variation also differentiated the repeated mid/late pyrrhic conversion grammar
  - therefore the pair exits the active opening `YELLOW` queue and returns to provisional keep

### 5.5 `smart_new_hire`

- main macro battlefield = `오피스/의사결정 축`
- overstay through `B08`
- representative reevaluation missing
- current ruling: `repair-first YELLOW`
- operator reading:
  - opening overstay형 둔화 후보다.
  - dense 쪽이라 구조 수리 가치가 있다.

### 5.7 Working Disposition Split

`kill-first review`:

- none

`repair-first`:

- `office_checkup_next_day`
- `smart_new_hire`

`forensic re-audit`:

- none

---

## 6. GREEN Provisional Keep

Current provisional keep:

- `투자물_골든_카나리아 테스트_canonical_v1`
- `africa_farm_king`
- `chaebol_ent_empire`
- `defense_defect_engineer`
- `hoegui_surgeon`
- `manual_meridian_archivist`
- `pantech_cyworld_reborn`
- `quiet_chaebol_heir`
- `wuxia_heavenly_physician`

Important note:

- 여기서 `GREEN`은 `discard-grade opening pacing failure not found`를 뜻한다.
- 이것이 곧바로 `GREENPLUS alias reaffirmed`를 뜻하지는 않는다.
- `chaebol_ent_empire`는 2026-04-10 targeted opening compression repair 이후 `B08` signboard로 재판정되어 `YELLOW` queue에서 빠졌다.
- `pantech_cyworld_reborn`은 2026-04-10 bounded cadence + reevaluation-surface repair 이후 `B02` reevaluation으로 재판정되어 `YELLOW` queue에서 빠졌다.

---

## 7. UNTRIAGED Hold Queue

Current hold:

- `gulf_tycoon_heir`

Current ruling:

- payload 기준 opening window가 `B01~B05`까지만 존재한다.
- `B06~B10`이 비어 있어 signboard / reevaluation / ticket timing을 확정할 수 없다.
- 따라서 이번 wave에서는 `GREEN`이 아니라 `UNTRIAGED`로 보류한다.

---

## 8. Registry Rule

- schema-clean tracked pair는 `production-pair-operational-registry-v1.json/md`에 opening pacing triage field를 함께 기록한다.
- schema-clean registry 바깥 pair의 결과는 이 wave 문서에 우선 보존한다.
- `YELLOW` triage는 `opening exemplar use suspended pending manual re-audit`로 읽는다.
- `RED` triage는 `negative exemplar archive`로 읽는다.
- `UNTRIAGED`는 opening evidence window 부족으로 인한 `hold` 상태로 읽는다.

---

## 9. Next Admissible Step

1. `RED` pair는 archive / anti-benchmark surface에 고정
2. `kill-first review` queue는 repair budget 투입 전 `RED` 승격 여부를 먼저 판정
3. `forensic re-audit` queue는 현재 해소 완료 (`jaebeol3se_loss_line` -> `RED`)
4. `repair-first` queue만 실제 repair wave 후보로 진입
5. opening contract field가 실제 live pair에 확산되면, 다음 wave부터는 `legacy heuristic`가 아니라 declared contract로 재판정
6. current `YELLOW` shelf salvageability closeout lives at `docs/2026-04-10/current-yellow-salvageability-split.md`
  - result: `repair-worth-it 3 / kill-candidate 0`
