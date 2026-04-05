# Blockguide 통합 오더 v1

> 인코딩: **UTF-8 only (기본값, 예외 없음)**
> 작성일: 2026-03-10
> 목적: `docs/blockguide` 안의 하네스 문서를 **읽는 순서, 단계 판정, 자동 진행 방식**까지 한 번에 고정
> 적용 대상: 기획안, `work_id`, `Phase 0`, `TR draft`, `BI`, `다음 스텝`, 감리 요청

---

## 0A. SSOT 장르 선언

현재 메인 시스템의 런타임 장르 슬롯, 일부 smoke test, 일부 코드 경로는 여전히 `investment` 명칭을 사용한다.
그러나 `docs/blockguide`의 SSOT 의미는 **현대판타지 all-genre general mode**다.

정확히는 글도비가 다루는 현대판타지 장르군 전체를 받는 공통 엔진이며, `기업 성장/지배력 장악물`은 그중 하나의 강한 프로파일이다.

공통 코어 계약:

- 주인공의 욕망, 결핍, 우위가 분명해야 한다.
- 작품마다 **측정 가능한 성장 자원**이 있어야 한다.
- 블록마다 **결정적 진행 액션**이 있어야 한다.
- 적대, 패배, 반격, 복선-회수의 연속성이 유지되어야 한다.
- 품질 원칙은 언제나 `quality-first`이며, 자동화는 보조 수단일 뿐이다.

경계:

- 순수 연애물, 순수 일상물, 순수 직장 드라마처럼 **측정 가능한 성장 축**이 없는 작품은 현재 파이프라인 바깥이다.
- 신입사원물도 예산, KPI, 결재선, 실적, 인사권, 프로젝트 오너십 같은 성장 축이 있으면 들어온다.

이 general mode는 아래 프로파일을 함께 받는다.

| 프로파일 | 핵심 자원 | 대표 액션 | 포함 기준 |
| ---- | ---- | ---- | ---- |
| `business_growth_profile` | 운영권, 현금흐름, 공급망, 반복 매출 | 운영권 인수, 정산 표준화, 공급망 장악 | 회사/사업 운영의 병목과 관문이 핵심 전장 |
| `investment_market_profile` | 자산, 지분, 수익률, 레버리지 | 지분 매입, 구조화 거래, M&A, 헤지 | 시장 가격과 금융 전략이 전장 |
| `entertainment_media_profile` | IP, 팬덤, 편성, 유통, 화제성 | 캐스팅, 편성 슬롯 선점, 저작권 묶음 확보 | 연예/방송/플랫폼/IP 확장이 핵심 |
| `medical_professional_profile` | 집도권, 케이스, 신뢰도, 병원 권한 | 수술권 확보, 프로토콜 개정, 연구/증례 선점 | 병원/의료 현장의 전문성과 권한이 전장 |
| `office_power_profile` | KPI, 예산, 결재선, 인사권, 프로젝트 통제 | KPI 재설계, 승인권 회수, 조직 재배치 | 조직 권력전과 실적 관리가 전장 |
| `tech_startup_profile` | 제품, 데이터, 특허, 라이선스, 사용자 기반 | 제품 출시, 라이선스, 특허/데이터 선점 | 기술 제품과 성장 모멘텀이 전장 |
| `urban_power_profile` | 전투력, 길드 자산, 던전 권리, 사회적 위상 | 레이드 배치, 독점권 확보, 팀 재편 | 현대 배경의 능력/길드/헌터 구조가 전장 |

호환성 불변조건:

- 런타임 장르 이름과 일부 기존 필드명은 당분간 유지한다.
- `genre_ext.capital_*`는 투자금 전용이 아니라 **주인공이 실질 통제하는 성장 자원**의 호환 필드로 읽는다.
- `deal_type`는 금융 거래형 전용이 아니라 **결정적 진행 액션 단위**로 읽는다.
- `FinanceHUD`는 키 이름만 유지하며, 문서상 의미는 **Resource-Power HUD**로 읽는다.
- `business_lines`는 키 이름만 유지하며, 문서상 의미는 **active domain lines**다.
- `company_state`는 키 이름만 유지하며, 문서상 의미는 **current operating arena / base state**다.

---

## 0B. 공통 코어와 프로파일 분리

모든 작품은 아래 둘로 나눠 해석한다.

1. **공통 코어**
   - 주인공 욕망/결핍/우위
   - 성장 자원
   - 적대 구조
   - 복선-회수
   - 패배/반격
   - 연속성/감리
2. **장르 프로파일**
   - 어떤 자원을 성장 자원으로 읽는가
   - 어떤 액션이 `deal_type`에 해당하는가
   - `business_lines`, `company_state`, `FinanceHUD`를 어떻게 해석하는가

원칙:

- 프로파일은 **주 프로파일 1개**를 반드시 고른다.
- 필요할 때만 **보조 프로파일 1개**를 추가한다.
- 코어 계약은 작품이 바뀌어도 유지한다. 바뀌는 것은 프로파일 해석뿐이다.

## 0C. 호환 필드 재해석

| 호환 키 | general mode 의미 |
| ---- | ---- |
| `capital` | 돈, 예산, 평판, 권한, 케이스, 팬덤, 라이선스, 길드 자산 등 **주인공이 실제로 굴릴 수 있는 성장 자원** |
| `deal_type` | 투자, 수술, 편성, 감사, 레이드, 법률 조항 발동, 조직 재배치 등 **판을 바꾸는 진행 액션** |
| `FinanceHUD` | 돈만 보여주는 HUD가 아니라 자원, 권력, 위상, 통제 상태를 함께 보여주는 **Resource-Power HUD** |
| `business_lines` | 사업부 전용 키가 아니라 작품의 **active domain lines**를 담는 호환 버킷. 예: 사업부, 진료과, 아티스트 라인업, 제품군, 길드 분대 |
| `company_state` | 회사 상태 전용 키가 아니라 현재 **운영 무대/거점 상태**를 담는 호환 버킷. 예: 그룹 운영 상태, 병원 권력 구도, 레이블 상태, 길드 등급 |
| `financial_status` | 숫자 자산만이 아니라 해당 프로파일에서 **즉시 동원 가능한 경제적/운영적 자원 상태**를 담는 최소 계약 레이어 |

## 0D. Stage 0 전처리 SSOT 선언

현재 `docs/blockguide`는 Planning / Production / BI 상위 오더를 다룬다.
그러나 이제 현대판타지 전 장르의 앞단에는 **필수 Stage 0 전처리 SSOT**가 선행한다.

정식 전처리 SSOT 경로:

- `전처리_ssot\docs\SSOT_stage0_preprocess_integrated_order.md`
- `전처리_ssot\docs\stage0_source_manifest_harness.md`
- `전처리_ssot\docs\stage0_profile_lock_harness.md`
- `전처리_ssot\docs\stage0_material_collection_harness.md`

원칙:

- 모든 현대판타지 작품은 `Stage 0 preprocess`를 먼저 지난다.
- `Stage 0 preprocess`가 끝나지 않으면 `phase0_design` 작성 금지
- `treatments/preprocess/{work_id}/phase0_ready_snapshot.json`의 `manual_audit_pass != true`면 Planning 진입 금지
- `modern_fantasy_material_harness.md`는 이제 경로 호환용 미러이며, 전처리 material collection의 현행 진실은 `전처리_ssot` 쪽이다

## 0. 이 문서를 언제 먼저 읽는가

아래 중 하나라도 해당하면, 다른 하네스보다 **이 문서를 가장 먼저** 읽는다.

1. 사용자가 작품명, `work_id`, 짧은 기획안, Bible 일부만 준 경우
2. 사용자가 `다음 스텝`, `계속`, `승인`처럼 짧은 진행 명령만 준 경우
3. 사용자가 `Phase 0`, `TR`, `BI`, 감리, 재검토, 정합성 체크를 요청한 경우
4. 현재 세션이 compaction 이후라 이전 상태를 기억만으로 복원하면 위험한 경우

핵심 원칙:

- 먼저 읽고, 그다음 판단한다.
- 기억으로 추정하지 말고, 파일 존재와 UTF-8 파싱으로 현재 단계를 판정한다.
- `docs/blockguide` 폴더 안 문서를 읽지 않고 바로 생산에 들어가면 무효로 본다.

---

## 1. 강제 읽기 순서

하네스 관련 작업은 아래 순서로 문서를 읽는다.

1. 현재 문서 `SSOT_blockguide-integrated-order.md`
2. `전처리_ssot\docs\SSOT_stage0_preprocess_integrated_order.md`
3. `treatment-planning-harness.md`
4. `treatment-production-harness-v2.md`
5. `bi-production-harness-v1.md`
6. `treatment-densification-harness-v1.md` — TR 밀도 부족 판정 시에만 진입 (§0C 진입 게이트 참조)
7. 구 경로를 참조하는 오래된 오더가 있으면 `modern_fantasy_material_harness.md`
8. 장르가 `alt_history`이거나 역사 재료 DB 조회가 필요하면 `alt_history_db_harness.md`

읽기 규칙:

1. 전부 **UTF-8로 읽는다.**
2. 다 읽은 뒤에 현재 단계만 골라 실행한다.
3. 현대판타지 일반 작품이면 `전처리_ssot` 엔트리를 통해 Stage 0 완료 여부를 먼저 판정한다.
4. `alt_history_db_harness.md`는 대체역사물일 때만 추가로 읽는다.
5. 문서를 다 읽었다고 해서 단계를 섞어 쓰지 않는다.
6. 지금 필요한 단계가 아니더라도 다음 handoff 규칙을 알기 위해 4번 문서까지 읽는다.

---

## 2. 현재 단계 판정법

파일 존재 여부와 상태로 현재 단계를 정한다.

| 조건 | 현재 단계 | 기본 행동 |
| ---- | --------- | --------- |
| `treatments/preprocess/{work_id}/source_manifest.json` 등 전처리 산출물 4개 중 하나라도 없음 | Stage 0 preprocess | `전처리_ssot` 문서 4개부터 다시 읽고 전처리 산출물을 만든다 |
| 전처리 산출물은 있으나 `phase0_ready_snapshot.manual_audit_pass != true` | Stage 0 preprocess | 전처리 수동 감리를 보강하고 snapshot을 다시 잠근다 |
| 전처리 산출물 4개가 있고 `phase0_design` 없음 | Planning | `treatment-planning-harness.md` 실행 |
| `phase0_design` 있음, `tr_block_070_draft` 없음 | Production | `treatment-production-harness-v2.md` 실행 |
| `tr_block_070_draft` 있음, `0_bi_{work_id}.json` 없음 | BI 생성 | `bi-production-harness-v1.md` 실행 |
| `tr_block_070_draft`와 `BI` 둘 다 있음 | 감리/재검토 | 최신 감리 상태 확인 후 필요한 단계만 재실행 |
| 파일은 있지만 UTF-8 파싱 실패 | 직전 단계로 후퇴 | 깨진 파일을 기준 SSOT로 쓰지 않음 |

기본 해석:

- 전처리 산출물이 없거나 수동 감리 PASS가 아니면 아직 Planning 단계도 아니다.
- `phase0_design`이 없으면 아직 생산 단계가 아니다.
- `tr_block_070_draft`가 없으면 아직 BI 단계가 아니다.
- `BI`가 있어도 감리 FAIL이면 완료가 아니다.

중간 산출물 격리 규칙:

- `phase0_design`은 중간 산출물이다. TR과 BI가 모두 존재하고 5-Pass 감리 PASS를 받으면,
  `phase0_design`은 `treatments/_quarantine/`로 이동한다.
- 이유: `phase0_design`의 역할은 TR/BI 생성의 입력이다. TR/BI가 완성되면 정본은 TR+BI이며,
  `phase0_design`은 더 이상 SSOT가 아니다. 격리하지 않으면 `phase0_design`과 TR/BI 사이에
  드리프트가 생길 때 어느 쪽이 정본인지 혼란이 발생한다.
- 격리 후에도 `phase0_design`은 삭제하지 않는다 — 디버깅/감리 이력 추적용으로 보존.
- 단계 판정에서 `phase0_design`이 `_quarantine`에 있고 TR+BI가 존재하면 **감리/재검토** 단계로 판정한다.

---

## 2A. Failure Triage 모드

아래 요청은 일반 production/BI auto-run으로 처리하지 않는다.

- 사용자가 `실패작`, `감리 FAIL`, `평가 메모`, `못 씀`, `왜 이런가`, `하네스 보강`을 말한 경우
- 특정 `TR`/`BI` 파일과 함께 구조적 실패 메모를 붙여 준 경우
- 기존 산출물 재사용 여부보다 **실패 원인 규명**이 먼저인 경우

이때는 현재 단계 판정보다 먼저 `Failure Triage` 루프로 들어간다.

고정 순서:

1. 실패 샘플 원본 읽기
2. 현재 운용본 대조
3. relevant harness 재오픈
4. 실패 유형 분류
5. 문서화
6. 3-pass 감리

실패 유형 분류값:

- `routing_gap`
- `schema_or_field_drift`
- `production_density_failure`
- `handoff_false_pass`

규칙:

- triage 완료 전에는 같은 작품의 Production/BI를 다시 돌리지 않는다.
- triage 결과가 `production_density_failure` 또는 `handoff_false_pass`면 하네스 보강 여부를 먼저 판정한다.
- triage 결과 문서가 없으면 실패 원인을 기억으로 요약하지 않는다.

---

## 2B. Existing Pair Repair 기본값

기존 `TR + BI` pair를 살리거나 승격시키는 요청은 fresh production 기본공정으로 처리하지 않는다.

원칙:

1. 먼저 router의 `shared pair-revival` 레이어를 탄다.
2. 기본값은 `lite audit -> top 3 repair -> recheck`다.
3. `top 10` 블록 수술이나 전 아크 재공사는 기본값이 아니다.

lite audit 기본 5축:

- 적대 / 압박원
- 승리의 비용
- 표면 반복
- 테마 carry
- 섹터 / 현장 질감

repair cap 기본값:

- quarantine salvage 확인: `top 3`까지만
- 승격 후보 / Stage 4 목표: `top 3` 재점검 후에만 `4-6` 확장 검토
- 확산형 문제면 salvage를 늘리지 말고 regenerate-first를 검토

운영 규칙:

- 기존 pair repair는 블록 1개씩 수동 진행한다.
- 방금 고친 체인을 보호하는 인접 블록이 있으면 순위보다 먼저 처리할 수 있다.
- pair-level 규칙이 비어 있으면 블록 추가 수리 전에 BI 강화 섹션을 먼저 잠근다.

즉:

- fresh build는 기존 production/BI 하네스를 따른다.
- existing pair salvage는 revival ladder를 따르고, blockguide 본체는 그 위에 family semantics만 제공한다.

---

## 3. 특정 기획안이 들어왔을 때의 자동 오더

사용자가 특정 기획안, 작품명, `work_id`를 던지면 아래 순서를 기본값으로 실행한다.
기본 문서 경로는 `docs\blockguide`, 전처리 경로는 `전처리_ssot`다.

1. 현재 문서와 `전처리_ssot/SSOT_stage0_preprocess_integrated_order.md`를 UTF-8로 연다.
2. 현재 작품의 전처리 산출물 4개, `phase0_design`, `TR draft`, `BI`, 감리 보고서 존재 여부를 확인한다.
3. 현재 단계 판정표로 지금 위치를 정한다.
4. `Stage 0 preprocess`면 전처리 SSOT 문서 4개를 먼저 따른다.
5. 그 외 단계면 해당 단계 문서의 **초저지능 LLM용 빠른 시작**과 **순차 진행 프로토콜**을 따른다.
6. 한 번에 단위 1개만 전진한다.
7. 단위 종료 후 결과 파일, 감리 상태, 다음 단위를 기록한다.
8. 정지 게이트가 없고 직전 단위의 수동 감리 메모가 남아 있으면 다음 단계나 다음 단위로 연속 진행한다.

중요:

- 사용자가 “알아서 진행”이라고 했으면, 질문부터 하지 말고 **현재 단계의 다음 필수 단위 1개**를 수행한다.
- 사용자가 `다음 스텝`만 반복해도 위 순서를 그대로 유지한다.
- 품질 게이트와 수동 감리가 auto-run보다 항상 상위다.
- 여기서 `auto-run`은 **작업 순서를 끊지 않고 이어 가는 것**을 뜻한다. Python 스크립트나 전체 파이프라인 실행 강제를 뜻하지 않는다.
- Production 단계의 기본 실행 단위는 항상 **블록 1개**다. 70블록 일괄 생성이나 10블록 일괄 생성은 금지한다.

### 3A. `seed_baseline_sync`와 `sequential_production`을 구분한다

Production을 시작하거나 compaction 뒤 재개할 때는 먼저
상태 파일을 읽는다.

읽기 우선순위:

1. `treatments/preprocess/{work_id}/sequential_run_status.json` (primary)
2. `treatments/preprocess/{work_id}/docs/sequential_run_status.md` (deprecated fallback, 유예 기간 내만 허용)
3. 둘 다 없으면 `status_missing` → `restart_at_block_001`

cutover 기준:

- 기존 작품: `run_class`가 `sequential_production`으로 전환 시 JSON 필수
- 신규 작품: Stage 0 완료 시 JSON 필수
- 유예: cutover 후 30일간 md 병행, 이후 JSON-only (md-only는 hard_fail)

run class는 아래 둘만 허용한다.

- `seed_baseline_sync`
  - 기존 canonical `TR`/`BI` 또는 검증된 작업물을 preprocess 작업공간으로 복제, 미러링, 정리한 상태
  - 참고용 seed이며 **production 진행률로 계산하지 않는다**
- `sequential_production`
  - `Block 001 -> 수동 감리 PASS -> Block 002`처럼 실제 순차 생성과 검수로 쌓은 상태
  - 이 경우에만 **실제 production 진행률**로 계산한다

재개 포인터 규칙:

- `run_class = sequential_production`이고 `last_sequential_block_pass = N`이며 `manual_audit_ready = true`일 때만 다음 단위를 `Block {N+1}`로 잡는다
- `run_class = seed_baseline_sync`면 `03_tr_blocks/` 아래에 70개 블록이 차 있어도 진행률로 계산하지 않는다
- `04_tr_final/` 존재, 최고 번호 block 디렉터리 개수, `tr_block_070_draft` 존재만으로는 재개 포인터를 정하지 않는다
- 상태 파일이 없으면 직전 block audit에서 `Run class: sequential_production`, `Sequential credit: true`, `Manual verdict: PASS`를 찾는다
- 위 근거가 없거나 모호하면 **무조건 `Block 001`부터 다시 시작**한다

---

## 4. 1턴 1단위 규칙

모든 단계는 한 턴에 **한 단위만** 전진한다.

| 단계 | 1단위의 정의 |
| ---- | ------------ |
| Planning | 설계 항목 1개 또는 `Phase 0` 시트 1개 |
| Production | 블록 1개 작성 + 수동 감리 1회 |
| BI | 스켈레톤 작성 1회, 동기화 1회, 감리 1회 중 하나 |
| Audit | 보고서 1회, 특정 위반군 재검토 1회, 또는 `10-block 자체 감리` 1회 |

금지:

- 계획과 생산과 BI를 한 턴에 다 밀어붙이기
- 실패한 단위를 건너뛰고 다음 단위로 넘어가기
- 이미 실패한 배치를 고치지 않고 전체를 완료 처리하기

---

## 5. 단계별 시작 체크리스트

### 5.1 Planning 시작 전

1. `treatments/preprocess/{work_id}/source_manifest.json` 존재 여부 확인
2. `treatments/preprocess/{work_id}/profile_lock.json` 존재 여부 확인
3. `treatments/preprocess/{work_id}/material_bundle_summary.json` 존재 여부 확인
4. `treatments/preprocess/{work_id}/phase0_ready_snapshot.json` 존재 여부 확인
5. `phase0_ready_snapshot.manual_audit_pass == true` 확인
6. 위 조건이 하나라도 깨지면 planning 진입 금지, `Stage 0 preprocess`로 전환
7. `phase0_design`이 없으면 planning 문서로 진입
8. 한 번에 설계 단위 1개만 출력

### 5.1A candidate→fixed→draft 상태 머신

Production과 BI 산출물은 아래 상태 머신을 따른다.

```
candidate → (self-check PASS + Python validation PASS) → fixed
fixed → (manual audit PASS) → production baseline
draft = ongoing work, not yet validated
```

상태 전이 규칙:

- `candidate`: 생성 직후 상태. self-check와 Python validation을 모두 통과해야 `fixed`로 승격한다.
- `fixed`: 자동 검증은 통과했으나 아직 수동 감리(manual audit)를 받지 않은 상태. 수동 감리 PASS 시 `production baseline`으로 확정한다.
- `draft`: 작업 중인 상태이며 아직 어떤 검증도 통과하지 않았다.

Rollback 규칙:

- `fixed`에서 오류 발견 시 `candidate`로 되돌리고 재생산한다. `fixed`를 직접 수정하지 않는다.
- `candidate`에서 오류 발견 시 해당 단위를 폐기하고 재생성한다.
- 어떤 상태에서든 직접 수정(in-place edit)보다 재생성을 우선한다.

### 5.2 Production 시작 전

1. `phase0_design` UTF-8 파싱 확인
2. 직전 `candidate/fixed/draft` 존재 여부 확인
3. 사용자 요청이 실패 분석/감리 FAIL 재검토면 production 진입 금지, `Failure Triage`로 전환
4. `phase0_design` 안에 적대자 아크 배분 정보와 weakness pool이 있는지 확인
5. 첫 블록(`Block 1`) 또는 아크 전환 직후 첫 블록(`11/21/31/41/51/61`)이면 더 느리게 간다.
6. 이번 턴 생산 단위는 블록 1개로 고정한다.
7. 직전 블록의 수동 감리 메모가 없으면 다음 블록으로 넘어가지 않는다.
8. 상태 파일을 먼저 읽는다: `sequential_run_status.json` (primary) → `.md` (deprecated fallback, 유예 기간 내만).
9. `run_class = seed_baseline_sync`면 기존 block 폴더와 `04_tr_final/`은 참고 seed로만 취급한다.
10. 최고 번호 block 디렉터리 개수나 final draft 존재만으로 진행률을 판정하지 않는다.
11. 재개 근거가 모호하면 `Block 001`부터 다시 시작한다.

### 5.3 BI 시작 전

1. `phase0_design` UTF-8 파싱 확인
2. `tr_block_070_draft` UTF-8 파싱 확인
3. source TR audit snapshot 존재 여부 확인
4. `production_density_gate`, `avg_bundle_chars`, `opponent_unique`, `deal_top_repetition`, `method_top_repetition` 또는 동등 반복 지표를 확인
5. source TR이 `skeleton draft`, 반복 FAIL, density FAIL이면 BI 진입 금지
6. 기존 BI 오염 여부 확인
7. 동기화 대상과 직접 작성 대상을 분리

---

## 6. 연속 진행 허용 모드 (Quality-First)

연속 진행은 허용되지만, 기본 철학은 auto-run이 아니라 **quality-first**다.
즉, 빨리 끝까지 미는 것보다 각 단위를 천천히 만들고 감리하는 것이 우선이다.

1. 현재 단계의 SSOT를 다시 연다.
2. 다음 미완료 단위 1개를 찾는다.
3. 그 단위를 실행한다.
4. UTF-8 저장과 검증을 한다.
5. 사람이 읽는 수동 감리 메모를 남긴다.
6. 정지 게이트가 없으면 다음 단위로 이동한다.

핵심 정의:

- `auto-run` = 다음 단위로 **순서상** 이어 가는 것
- `not auto-run` = 무조건 멈추고 사용자 승인만 기다리는 것
- `auto-run`은 **스크립트 실행 강제**가 아니다.
- Production에서는 `auto-run`이어도 `Block 1 -> 감리 -> Block 2 -> 감리`처럼 1개씩만 간다.
- 같은 운영 오더에서 자동 연속 가능한 최대치는 **5블록**이며, `Block 005/010/015...` 경계마다 새 오더가 필요하다.
- `Block 010/020/030...` 완료 뒤의 다음 필수 단위는 `Block 011/021/031...`이 아니라 직전 10블록에 대한 `10-block 자체 감리 1회`다.
- `10-block 자체 감리` PASS 전에는 다음 10블록 구간으로 진입하지 않는다.
- `seed_baseline_sync`는 참고용 seed이며 progress로 계산하지 않는다.
- progress는 `sequential_production`과 그에 연결된 수동 감리 PASS 기록에서만 나온다.

정지 게이트:

- UTF-8 파싱 실패
- `???`, `�` 탐지 <!-- utf8-hygiene: allow-line rationale: literal mojibake tokens are documented here as stop-gate examples. -->
- P0 또는 감리 FAIL
- 직전 SSOT 부재
- 직전 단위 수동 감리 메모 부재
- `Block 010/020/030...` 완료 후 `10-block 자체 감리` 미실시 또는 FAIL
- `sequential_run_status.json` (또는 .md deprecated fallback)와 실제 수동 감리 기록이 충돌
- `seed_baseline_sync`를 `sequential_production`처럼 취급하려는 시도
- 같은 운영 오더에서 5블록 창 소진
- 사용자가 방향 수정 또는 수동 검토를 명시

---

## 7. 저지능 LLM용 단순 규칙

판단이 흐리면 아래만 기억해도 된다.

1. 먼저 `docs/blockguide` 문서 4개를 UTF-8로 읽는다.
2. 현재 단계는 파일 존재로 정한다.
3. 한 번에 1단위만 진행한다.
4. 애매하면 더 작은 단위로 쪼갠다.
5. 실패하면 같은 단위를 다시 한다.
6. `Block 010/020/030...`마다 지난 10블록 자체 감리를 먼저 한다.
7. 기억보다 파일을 믿는다.
8. `Phase 0` 없이 TR 금지, `TR draft` 없이 BI 금지.
9. 실패작 요청은 일반 생산이 아니라 `Failure Triage`로 처리한다.
10. source TR audit 없이 BI handoff 금지.
11. 감리 PASS 전에는 완료 선언 금지.
12. opponent는 이름 목록이 아니라 아크 배분표로 확인한다.
13. weakness는 이름 치환이 아니라 구조 차이로 확인한다.
14. `auto-run`은 순서 자동 진행이지, 스크립트 자동 실행이 아니다.
15. Production은 항상 블록 1개씩 쌓고, 각 블록마다 수동 감리를 남긴다.

---

## 8. 최소 보고 형식

매 단위 종료 시 아래 4줄만 남기면 된다.

1. 현재 단계
2. 이번에 읽은 SSOT
3. 이번에 끝낸 단위
4. 다음 단위 또는 정지 사유

---

## 9. 자동 진행 정책

단계 전환은 정지 게이트가 아니다. Go 조건이 충족되면 멈추지 않고 다음 단계로 넘어간다.

project-only handoff mode:

- 사용자가 `work_id`나 특정 pair만 주면 먼저 live 파일과 최신 감리 산출물을 읽고 현재 단계를 판정한다.
- 다음 필수 단위가 명확하면 그 단위를 바로 진행한다.
- 단계나 대상이 모호할 때만 짧은 clarifying question 1회로 정리한다.
- 사용자가 단계를 직접 말하지 않았다는 이유만으로 멈추지 않는다.

Production/BI 자동 진행 경계:

- Production auto-run의 내부 단위는 항상 `Block 1개`다.
- 같은 운영 오더에서 자동 연속 가능한 최대치는 **5블록**이며, `Block 005/010/015...` 경계마다 새 오더가 필요하다.
- `Block 010/020/030...` 경계에서는 새 오더의 첫 필수 단위가 `10-block 자체 감리`다. PASS 전에는 다음 블록으로 넘어가지 않는다.
- BI auto-run은 **handoff 1사이클**까지만 허용한다. sync/audit PASS 또는 FAIL 보고가 끝나면 반드시 정지한다.

금지:
- "Stage 0 끝났습니다. Planning으로 갈까요?"
- "Phase 0 설계 완료했습니다. Production 시작할까요?"
- "TR 70블록 완료했습니다. BI 만들까요?"

허용:
- "Stage 0 완료. Planning 진입." (1줄 상태 보고 후 즉시 진행)
- "Block 4 완료. Block 5 시작." (같은 운영 오더 내 허용)
- "TR 70 완료. BI handoff 1사이클 진행." (상태 보고 후 바로 감리/동기화)

유일한 정지 조건:
- manual_audit_pass 필요 시 (Stage 0 → Planning 전환)
- context window 한계 도달
- 같은 운영 오더에서 5블록 창 소진
- `10-block 자체 감리` 대기 또는 FAIL
- BI handoff 1사이클 완료
- 사용자의 명시적 정지 지시
