# GDFS-T3 Config / Contract / SSOT Drift Findings

> 작성일: 2026-03-13
> 상태: `PASS3 confirmed`
> 조사 모드: `static / read-only / baseline-aware / UTF-8 only`
> 기준 오더: `docs/2026-03-13/global-detail-full-survey-master-audit-order.md`
> baseline 참조: `SSOT_stage0_preprocess_integrated_order.md`, `OPUS-TF-T1-infrastructure-findings.md`, `OPUS-TF-5terminal-detail-T5-findings.md`, `stage0-work-guard-style-cache-remediation-postfix-3pass-closure.md`, `ui-frontend-backend-connectivity-remediation-execution-ssot.md`

---

## 요약

이번 T3의 목적은 config/doc/contract 층에서 **"문서는 A를 SSOT라 하고, 실제 소비자는 B를 읽고, 테스트는 또 C를 잠그는"** 식의 live drift만 retained set으로 남기는 것이다.

결론:

- retained P1 2건, retained P2 2건을 확인했다.
- `Narrative AGENTS`의 stage detection과 `work_guard` runtime path는 현재 문서/코드가 정렬돼 있어 오탐으로 제거했다.

핵심은 아래 4건이다.

1. validation threshold는 아직도 `validation.yaml=60`과 `settings.json/orchestrator=70` 사이에서 이중 SSOT다.
2. `phase0_design` 계약은 wrapper/flat 2형식을 허용하지만 BI 생성 소비자는 wrapper만 받는다.
3. vector retrieval cap fallback과 정렬 테스트가 `validation.yaml` 최신값과 어긋난다.
4. preprocess 재개 README는 여전히 deprecated `sequential_run_status.md`를 먼저 읽으라고 유도한다.

---

## 조사 범위

- `config/settings.json`
- `config/settings/validation.yaml`
- `modules/domain/agents/director.py`
- `modules/domain/agents/director_auditor.py`
- `modules/validation/validation_orchestrator.py`
- `modules/core/stage2_preflight.py`
- `modules/core/stage3_orchestrator.py`
- `modules/core/stage4_context_builder.py`
- `scripts/build_bi_from_phase0_and_tr.py`
- `전처리_ssot/contracts/artifact_contracts.json`
- `전처리_ssot/contracts/handoff_rules.json`
- `전처리_ssot/README.md`
- `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md`
- `전처리_ssot/docs/blockguide/AGENTS.md`
- `work_guards/README.md`
- `treatments/defense_defect_engineer_phase0_design.json`
- 관련 테스트

---

## PASS 1 후보

1. validation threshold SSOT split
2. `phase0_design` contract vs BI consumer drift
3. Stage2/Stage3 retrieval fallback default drift
4. preprocess resume pointer JSON/MD 우선순위 drift
5. `전처리_ssot/docs/blockguide/AGENTS.md` stage detection 충돌 의심
6. `work_guard` runtime path drift 의심

---

## PASS 2 제거

### 제거 1. `전처리_ssot/docs/blockguide/AGENTS.md` stage detection 충돌 의심

- 초기 의심:
  - 파일 상단은 "시스템 오더는 `phase0_design` / `tr_block_070_draft` / `BI` 파일 존재로 단계를 판정하지 않는다"고 적고,
  - 하단은 narrative stage detection에서 파일 존재를 사용한다.
- 현재 문서 재해석:
  - `전처리_ssot/docs/blockguide/AGENTS.md:5-17`는 `글도비 시스템 오더`와 `서사 파이프라인 오더`를 분리한다.
  - 같은 파일 `:42-47`의 파일 존재 기반 stage detection은 narrative pipeline 전용 규칙이다.
- 판정:
  - `FP-1`
  - track split을 읽으면 모순이 아니라 scope 분리다.

### 제거 2. `work_guard` runtime path drift 의심

- 초기 의심:
  - `work_guard.yaml` 경로가 문서/코드마다 달라졌을 수 있음
- 현재 코드/문서:
  - `work_guards/README.md:5` — 런타임 적용 파일은 `{project}/config/work_guard.yaml`
  - `modules/core/stage0/__init__.py:95` — `_project_work_guard_path()`는 `config/work_guard.yaml`
  - `modules/core/project_support.py:247`, `modules/core/project_support.py:273` — 지원 surface도 `config/work_guard.yaml`
- 판정:
  - `FP-4`
  - 현재 live consumer와 운영 문서는 정렬돼 있다.

---

## PASS 3 확정 Findings

### [GDFS-T3-001] P1 | validation threshold SSOT가 아직도 `validation.yaml`과 `settings.json`/orchestrator로 갈라져 있다

1. ID
   - `GDFS-T3-001`
2. Severity
   - `P1`
3. 현상 요약
   - `validation.yaml`은 `scoring.default_pass_threshold = 60`으로 이미 내려갔지만,
   - `ValidationOrchestrator`는 여전히 `config.get("scoring_threshold", 70)`를 기본값으로 사용하고,
   - `DirectorAuditor`도 default config와 `config/settings.json` 병합을 통해 `scoring_threshold=70`을 계속 밀어 넣는다.
   - 같은 validation 계층 안에서도 Director base threshold는 YAML 60을 보고, orchestrator scoring threshold는 70을 보게 되는 이중 SSOT가 남아 있다.
4. 코드 근거
   - `config/settings/validation.yaml:35` — `default_pass_threshold: 60`
   - `modules/domain/agents/director.py:50` — `self.base_pass_threshold = _threshold("scoring.default_pass_threshold", 60)`
   - `modules/validation/validation_orchestrator.py:231`, `modules/validation/validation_orchestrator.py:271` — `config.get("scoring_threshold", 70)`
   - `config/settings.json:8` — `validation.scoring_threshold = 70`
   - `modules/domain/agents/director_auditor.py:248-279` — `scoring_threshold: 70` default config + `settings.json` 병합, 주석은 "`YAML/코드 일치`"라고 적혀 있음
5. downstream 영향 경계
   - Director audit / ValidationOrchestrator / settings-based bootstrap
   - 동일 원고가 어떤 entry path를 탔는지에 따라 pass threshold 해석이 달라질 수 있고, 운영자는 `validation.yaml`만 보고 현재 기준이 60으로 통일됐다고 오판할 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - `tests/test_config_manager.py:206-232`는 YAML lookup 자체만 검증한다.
   - `tests/test_validation.py:303-422`는 orchestrator 테스트에 계속 `scoring_threshold=70`을 주입한다.
   - `config={}` 또는 `DirectorAuditor` 경유 초기화가 실제로 YAML 60과 정렬되는지 잠그는 테스트는 찾지 못했다.
7. baseline과의 관계
   - `none`
   - 이번 전역 SSOT drift sweep에서 새로 고정한 contract mismatch
8. 권장 후속 조치
   - validation threshold의 단일 진실을 `validation.yaml`로 고정하거나
   - `settings.json` override를 공식 계약으로 인정한다면 문서와 주석에서 YAML 단일 SSOT 서술을 철회해야 한다.

### [GDFS-T3-002] P1 | `phase0_design` 계약은 2형식을 허용하지만 BI 생성 소비자는 wrapper만 받는다

1. ID
   - `GDFS-T3-002`
2. Severity
   - `P1`
3. 현상 요약
   - `artifact_contracts.json`는 `phase0_design`에 대해 wrapper shape와 legacy flat shape를 모두 허용한다.
   - 그러나 `scripts/build_bi_from_phase0_and_tr.py`는 wrapper 4섹션(`project`, `setting`, `protagonist`, `phase0_design`)이 없으면 즉시 실패한다.
   - 현재 workspace에는 `work_id`로 시작하는 flat `phase0_design` 파일도 남아 있으므로, 계약이 허용한다고 적힌 shape가 live consumer에서는 실제로 소비되지 않는다.
4. 코드 근거
   - `전처리_ssot/contracts/artifact_contracts.json:78-90` — `required_key_sets_any_of`로 wrapper/flat 2형식 허용
   - `scripts/build_bi_from_phase0_and_tr.py:519-529` — wrapper 4섹션을 hard require
   - `treatments/defense_defect_engineer_phase0_design.json:2` — active treatment surface에 `work_id` 기반 flat shape 존재
5. downstream 영향 경계
   - `phase0_design -> BI` handoff
   - 운영자는 계약상 허용된 phase0 artifact라고 생각해도 실제 BI 생성 경로에서는 reject를 만나고, 계약 문서가 허용한 legacy shape가 실사용 파이프라인에선 죽어 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 조사 범위에서 `scripts/build_bi_from_phase0_and_tr.py`가 flat/wrapper 2형식을 모두 소비하는지 잠그는 테스트는 찾지 못했다.
7. baseline과의 관계
   - `related-but-retained`
   - `OPUS-TF-5terminal-detail-T5-findings`의 `phase0_design` schema surface를 현재 계약/소비자 mismatch로 다시 고정한 current-form finding
8. 권장 후속 조치
   - 계약을 wrapper-only로 축소하거나
   - BI 생성기가 flat legacy shape를 wrapper로 normalize한 뒤 소비하도록 맞춰야 한다.

### [GDFS-T3-003] P2 | vector retrieval fallback과 정렬 테스트가 `validation.yaml` 최신값을 아직 못 따라간다

1. ID
   - `GDFS-T3-003`
2. Severity
   - `P2`
3. 현상 요약
   - `validation.yaml`는 `context.vector_max_results_s2=40`, `context.vector_max_results_s4=50`으로 이미 올라갔다.
   - 하지만 Stage2 fallback은 아직 16, Stage3는 Stage4 키를 공유한다고 적어 놓고도 fallback을 16으로 둔다.
   - 더 문제는 `tests/test_tf3_threshold_alignment.py`가 이 오래된 16/20 값을 여전히 "`YAML 값`"이라고 잠그고 있어, 정렬 테스트 자체가 stale narrative를 만든다.
4. 코드 근거
   - `config/settings/validation.yaml:86-87` — `vector_max_results_s4=50`, `vector_max_results_s2=40`
   - `modules/core/stage2_preflight.py:162`, `modules/core/stage2_preflight.py:1189` — S2 fallback `16`
   - `modules/core/stage3_orchestrator.py:1005-1006` — S3는 S4 키 공유 주석을 두고 fallback `16`
   - `modules/core/stage4_context_builder.py:1213`, `modules/core/stage4_context_builder.py:2467` — S4는 fallback `50`
   - `tests/test_tf3_threshold_alignment.py:8-16` — S2 `16`, S3 `16`, S4 `20`을 정렬값처럼 고정
   - `tests/test_stage4_context_builder.py:117-122`, `tests/test_stage4_interview_round.py:1173-1178` — 같은 S4 key를 `50`으로 잠금
5. downstream 영향 경계
   - config load failure / key 누락 fallback
   - alignment regression tests
   - Stage2/3만 YAML 미로드 시 낮은 recall로 떨어지고, 테스트는 그 lower fallback을 정상처럼 승인할 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 정렬 테스트가 아예 stale 값을 승인한다.
   - S2/S3 fallback이 `validation.yaml` 최신값과 같아야 한다는 단일 authoritative test는 없다.
7. baseline과의 관계
   - `none`
   - current SSOT drift surface
8. 권장 후속 조치
   - S2/S3/S4 fallback 기본값을 `validation.yaml` 최신 수치와 맞추고
   - `test_tf3_threshold_alignment.py`를 단일 truth 기준으로 재정렬해야 한다.

### [GDFS-T3-004] P2 | preprocess 재개 README는 아직도 deprecated MD-first 해석을 유도한다

1. ID
   - `GDFS-T3-004`
2. Severity
   - `P2`
3. 현상 요약
   - integrated order와 contract는 `sequential_run_status.json`을 primary resume pointer로 정의하고, `docs/sequential_run_status.md`는 유예 기간용 deprecated fallback으로만 둔다.
   - 그런데 `전처리_ssot/README.md`는 후반부에서 `sequential_run_status.md`를 왜 필요한지 길게 설명한 뒤, Production 재개 전에는 항상 그 MD를 읽으라고 적는다.
   - 같은 허브 문서군 안에서 operator-facing 재개 우선순위가 JSON-primary와 MD-first로 갈라져 있다.
4. 코드 근거
   - `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md:76-77` — JSON primary, MD deprecated fallback
   - `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md:106` — 읽기 우선순위 `JSON -> md fallback`
   - `전처리_ssot/contracts/handoff_rules.json:108-109` — `primary_resume_pointer` / `deprecated_resume_fallback`
   - `전처리_ssot/contracts/artifact_contracts.json:194` — MD는 JSON replacement target
   - `전처리_ssot/README.md:241-249`, `전처리_ssot/README.md:287` — `sequential_run_status.md` 필요성 강조 + Production 재개 전 MD 우선 독법
5. downstream 영향 경계
   - preprocess operator resume
   - context compaction 이후 재개 포인터 복원
   - 사람이 README를 따라가면 stale MD를 먼저 보고 JSON 최신 상태를 놓칠 수 있다.
6. 현재 테스트 근거 또는 테스트 부재
   - 문서 우선순위를 lint하거나 README 서술이 contract JSON과 일치하는지 검증하는 테스트는 없다.
7. baseline과의 관계
   - `operator-surface-mismatch`
   - contract layer는 JSON primary인데 human-facing guide가 다른 신호를 내는 표면 불일치
8. 권장 후속 조치
   - README의 재개 규칙을 integrated order와 동일하게 `JSON first, md fallback`으로 바꾸고
   - MD는 historical/deprecated pointer라는 점을 더 강하게 명시해야 한다.

---

## Current Phase / Resume Packet

1. `Current phase`
   - `T3 completed`
2. `Last completed pass`
   - `PASS3`
3. `Last completed surface`
   - `config / contract / SSOT drift`
4. `Next surface`
   - `T4 UI / API / desktop / operator surface`
5. `Reopen reason codes used`
   - `none`
6. `Stop gate or blocker`
   - `없음`

---

## 3PASS 요약

- `PASS1 6건 -> PASS2 2건 제거 -> PASS3 최종 4건 확정`
- 최종 retained set:
  - `P1 2건`
  - `P2 2건`
  - `P3 0건`
