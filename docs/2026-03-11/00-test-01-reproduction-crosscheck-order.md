# 00_test_01 Reproduction Cross-Check Order

> 작성일: 2026-03-11  
> 상태: 비교군 공용 오더  
> 용도: Codex / OPUS 병렬 감리용  
> 성격: `reproduction verification + delta audit layer`  
> 비고: 기존 SSOT를 대체하지 않는다

---

## 0. 목적

이 문서는 `projects/00_test_01`이 `projects/00_test_00`의 `1 arc / ep_0001~ep_0004` 기준선을 **같은 재료, 같은 방식**으로 얼마나 충실하게 재현했는지 확인하기 위한 공용 오더다.

이번 비교의 핵심 질문은 아래 세 가지다.

1. `00_test_01`은 `00_test_00`의 technical validation baseline을 다시 재현했는가
2. 재현되었다면 어디까지가 `같은 사실`이고, 어디부터가 `허용 가능한 차이`인가
3. 현재 근거만으로 재현 판정의 확신도를 `95%`까지 올릴 수 있는가

이 오더의 목적은 `누가 더 잘 해석하느냐`를 겨루는 것이 아니라, 아래 셋을 분리하는 데 있다.

- 무엇이 **확실한 재현 사실**인가
- 무엇이 **허용 가능한 drift**인가
- 무엇이 **추가 조사 없이는 닫히지 않는 불확실성**인가

두 에이전트는 반드시 **같은 입력**, **같은 taxonomy**, **같은 표 구조**를 사용해야 한다.  
다른 해석이나 이견은 appendix에만 적는다.

---

## 1. 고정 입력과 비교 기준

### 1.1 기준선과 재현 후보

- 기준선: `docs/2026-03-11` 문서군에 고정된 `00_test_00` baseline
- 재현 후보: `projects/00_test_01`
- 비교 범위: `Arc 1 / ep_0001~ep_0004`

이번 오더에서 `00_test_00` baseline은 **현재 프로젝트 폴더의 live 상태가 아니라**, 2026-03-11에 고정된 SSOT/감리 문서와 session/log 근거로 해석한다.  
즉, `00_test_01`은 그 문서화된 기준선의 재현 성공 여부를 판단할 대상이다.

### 1.2 필수 입력

두 에이전트는 아래 입력만 사용한다.

#### `00_test_01` 필수 입력

- `projects/00_test_01/project_data.db`
- `projects/00_test_01/plans/arcs/arc_001.txt`
- `projects/00_test_01/plans/blueprints/blueprint_0001.txt`
- `projects/00_test_01/plans/blueprints/blueprint_0002.txt`
- `projects/00_test_01/plans/blueprints/blueprint_0003.txt`
- `projects/00_test_01/plans/blueprints/blueprint_0004.txt`
- `projects/00_test_01/drafts/ep_0001.txt`
- `projects/00_test_01/drafts/ep_0002.txt`
- `projects/00_test_01/drafts/ep_0003.txt`
- `projects/00_test_01/drafts/ep_0004.txt`
- `projects/00_test_01/logs/session_20260311_183911.log`
- `projects/00_test_01/logs/metrics/metrics_20260311_183915.json`
- `projects/00_test_01/logs/pass_rate_monitor.json`
- `projects/00_test_01/logs/quality_metrics.jsonl`
- `projects/00_test_01/logs/episode_production.jsonl`
- `projects/00_test_01/logs/runtime_audit.jsonl`
- `projects/00_test_01/logs/runtime_audit_summary.json`

#### `00_test_00` 비교 기준 입력

- `docs/2026-03-11/00-test-00-stage234-ssot-3pass.md`
- `docs/2026-03-11/00-test-00-manual-reading-audit.md`
- `docs/2026-03-11/ops-runtime-cost-crosscheck-codex.md`
- `docs/2026-03-11/ops-runtime-cost-reconciliation-codex.md`
- 보조 확인용: `projects/00_test_00/logs/session_20260311_112831.log`
- 보조 확인용: `projects/00_test_00/logs/metrics/metrics_20260311_112834.json`
- 보조 확인용: `projects/00_test_00/project_data.db`

주의:

- `projects/00_test_00`는 이후 reset/초기화로 live 산출물이 바뀌었을 수 있다.
- 따라서 `projects/00_test_00/drafts/ep_0001.txt` ~ `ep_0004.txt` 같은 live artifact는 **필수 입력으로 사용하지 않는다**.
- baseline 사실은 반드시 `SSOT + manual audit + pinned logs`를 우선 근거로 사용한다.

### 1.3 해석 규칙

- `00_test_00`는 `technical validation baseline`이다.
- 단, 이번 오더에서 그 baseline은 **live project tree**가 아니라 **문서와 pinned log**에 고정된 baseline을 뜻한다.
- `00_test_01`은 `real production validation`이 아니라 `baseline reproduction candidate`다.
- 이번 감리는 `Arc 1 / ep_0001~ep_0004`까지만 본다.
- `같은 재료, 같은 방식`이라는 전제는 사용자 진술을 기본값으로 사용하되, 로그/산출물/구조가 이를 뒤집으면 `material divergence`로 올린다.
- 코드 수정, 추가 런 실행, 대시보드 호출은 포함하지 않는다.

### 1.4 fail-closed 규칙

아래 규칙은 예외 없이 적용한다.

1. `00_test_01` 필수 입력이 하나라도 비어 있거나 누락되면, 그 누락 자체를 `material divergence` 후보로 올린다.
2. `00_test_00` 기준선은 반드시 `SSOT + manual audit + pinned logs`를 우선 사용한다. 이후 생성되거나 reset 이후 바뀐 live 산출물로 baseline을 덮어쓰면 안 된다.
3. 같은 사실을 확인할 때 소스가 충돌하면 우선순위는 아래와 같다.
   - `00_test_00-stage234-ssot-3pass.md`
   - `00_test_00-manual-reading-audit.md`
   - pinned session / metrics log
   - `project_data.db`
4. `확인 불가`인 항목은 억지 판정을 하지 말고 `hypothesis pending`으로 남긴다.
5. 재현 판정에 필요한 핵심 소스가 없으면 `95%` 판정을 내릴 수 없다.

---

## 2. 공통 taxonomy

본문에서 허용되는 taxonomy는 아래 네 개뿐이다.

- `confirmed reproduction`
- `acceptable drift`
- `material divergence`
- `hypothesis pending`

아래 단어는 본문에서 쓰지 않는다.

- `bug`
- `issue`
- `problem`

반드시 taxonomy 용어만 쓴다.

---

## 3. 공통 작업 명세

두 에이전트는 아래 3-pass를 **동일한 순서**로 수행한다.

### Pass 1. 재현 사실 고정

목표: `00_test_01`이 무엇을 실제로 생산했고, `00_test_00`와 어떤 기본 parity를 가지는지 해석 없이 고정한다.

필수 산출 표는 아래 두 개다.

#### 표 A. Artifact Parity

| layer | baseline_00_test_00 | candidate_00_test_01 | parity | source |
|---|---|---|---|---|

작성 규칙:

- `layer`는 아래만 허용한다.
  - `arc`
  - `blueprint`
  - `draft`
  - `db_rows`
  - `metrics`
  - `runtime_audit`
- `parity`는 아래만 허용한다.
  - `match`
  - `near-match`
  - `mismatch`
  - `not-comparable`
- 최소 항목:
  - `arc_001.txt`
  - blueprint 1~4
  - draft 1~4
  - `episode_quality_labels`
  - `episode_quality_signals`
  - `director_selections`
  - `stage_attempts`
  - metrics summary
  - runtime audit summary
- `arc`, `blueprint`, `draft`의 parity는 **파일 존재 여부 + 역할/범위 parity**를 함께 본다. prose의 완전 동일성은 요구하지 않는다.

#### 표 B. Run Summary

| project | scope | stage2 | stage3 | stage4 | artifacts_complete | major_counts | notes | source |
|---|---|---|---|---|---|---|---|---|

작성 규칙:

- `scope`는 `Arc 1 / ep_0001~0004`로 고정한다.
- `major_counts`에는 최소 아래 4개를 적는다.
  - `episode_quality_labels`
  - `episode_quality_signals`
  - `director_selections`
  - `stage_attempts`

### Pass 2. 차이 분해

목표: `00_test_01`이 `00_test_00`를 어디까지 동일하게 재현했고, 어떤 차이가 허용 가능한 drift인지 분리한다.

필수 산출 표는 아래 하나다.

#### 표 C. Delta Taxonomy

| id | taxonomy | evidence | current interpretation | impact on reproduction claim | next check point | confidence |
|---|---|---|---|---|---|---|

작성 규칙:

- `evidence`에는 반드시 파일/로그/산출물 경로를 적는다.
- `impact on reproduction claim`은 아래 중 하나로 적는다.
  - `none`
  - `low`
  - `medium`
  - `high`
- 최소 검토 축:
  - artifact existence parity
  - Stage 2/3/4 완료 여부
  - stage_attempts / director_selections 규모 차이
  - runtime_audit_summary 상태
  - manual reading 관점의 drift 여부
  - 비용/시간 차이가 reproduction 자체를 흔드는지 여부
- `manual reading 관점의 drift`는 `00_test_00` live draft가 아니라 `00-test-00-manual-reading-audit.md`에 고정된 text-level 기준을 사용한다.

### Pass 3. 확신도 판정

목표: 현재 근거만으로 `00_test_01` 재현 판정을 몇 % 확신도로 말할 수 있는지 고정한다.

필수 산출 표는 아래 하나다.

#### 표 D. Confidence Ladder

| claim | current status | blocker to 95% | confidence_now | confidence_if_resolved |
|---|---|---|---|---|

작성 규칙:

- 최소 claim은 아래 4개를 포함한다.
  - `Arc 1 artifact reproduction`
  - `Stage 2->3->4 pipeline reproduction`
  - `operator-readable observability parity`
  - `00_test_00 대비 baseline fidelity`
- 최종 본문에서는 반드시 아래 형식으로 한 줄 verdict를 낸다.
  - `현재 판정: 00_test_01은 00_test_00의 Arc 1 baseline을 [재현함 / 부분 재현함 / 재현 실패]`
- `95%`를 넘겨 말하려면 아래 조건을 모두 만족해야 한다.
  - 핵심 claim이 모두 `confirmed reproduction` 또는 `acceptable drift`
  - `material divergence`가 남아 있지 않음
  - `hypothesis pending`이 reproduction 핵심 판정을 흔들지 않음

---

## 4. 본문 구조 고정

Codex와 OPUS는 메인 바디를 아래 구조로 **완전히 동일하게** 작성한다.

1. `최종 한줄 판정`
2. `Pass 1. 재현 사실 고정`
3. `Pass 2. 차이 분해`
4. `Pass 3. 확신도 판정`
5. `비교용 요약`

`비교용 요약`은 아래 5문항에 대해 한 줄씩 답한다.

- `00_test_01`은 `00_test_00`를 어디까지 재현했는가
- 핵심 parity는 어디서 확인되는가
- 허용 가능한 drift는 무엇인가
- 재현 판정을 흔드는 material divergence가 있는가
- 현재 근거로 확신도 95%에 도달하는가

---

## 5. Appendix 규칙

appendix는 독립 허용이다. 다만 섹션명은 반드시 아래 둘만 사용한다.

### Appendix A. Agent-specific observations

- 각 에이전트가 본문에 넣지 않은 독자 관찰을 적는다.
- 본문 사실과 충돌하는 새 사실은 금지한다.

### Appendix B. 반례 / 이견 / 추가 가설

- 상대 에이전트와 갈릴 수 있는 해석만 적는다.
- 본문 taxonomy를 뒤집는 주장은 여기서만 허용한다.
- 근거 없는 추정은 금지한다.

---

## 6. 3-Pass 감리 기준

### Pass 1. 오더 문서 자체 감리

아래를 모두 만족해야 한다.

- 입력 파일 목록이 고정되어 있다
- 기준선과 재현 후보가 분리되어 있다
- 표 헤더가 고정되어 있다
- taxonomy가 4개로 고정되어 있다
- implementer가 추가 결정을 할 여지가 없다

### Pass 2. 비교 가능성 감리

아래를 모두 만족해야 한다.

- Codex와 OPUS가 같은 표 구조를 쓸 수 있다
- 사실과 해석이 분리되어 있다
- `00_test_00`와 `00_test_01`의 역할이 섞이지 않는다
- 같은 사실에 대한 다른 해석이 바로 보인다

### Pass 3. 과장 방지 감리

아래를 모두 만족해야 한다.

- `technical validation baseline`을 `real production baseline`으로 승격하지 않는다
- `artifact parity`를 곧바로 `사업성`으로 해석하지 않는다
- 비용/시간 차이가 있어도 reproduction 핵심과 별개면 `acceptable drift`로만 둔다
- `95% 확신도`는 조건 충족 시에만 허용한다
- prose가 다르다는 이유만으로 곧바로 `material divergence`로 승격하지 않는다
- 반대로 stage completeness, artifact count, 핵심 state parity가 어긋나면 문체 차이와 무관하게 `material divergence` 후보로 본다

---

## 7. 수용 기준

최종 결과 문서는 아래를 모두 만족해야 한다.

- 같은 입력 파일 목록을 사용한다
- 메인 바디 표 구조가 동일하다
- `00_test_00 = 기준선`, `00_test_01 = 재현 후보`가 명시되어 있다
- 최소 1개 `Artifact Parity` 표가 있다
- 최소 1개 `Delta Taxonomy` 표가 있다
- 최소 1개 `Confidence Ladder` 표가 있다
- 비교 시 `같은 사실 / 허용 drift / material divergence`가 바로 보인다
- 기존 SSOT를 대체하지 않고 `reproduction verification layer`로만 동작한다

---

## 8. 기본 가정

- 이번 비교는 `00_test_00`와 `00_test_01`의 `Arc 1 / ep_0001~ep_0004`만 대상으로 한다.
- `00_test_00`는 `technical validation baseline`이다.
- 그 baseline의 source of truth는 현재 `projects/00_test_00` live 상태가 아니라, 2026-03-11에 고정된 SSOT/감리 문서와 pinned logs다.
- `00_test_01`은 같은 재료, 같은 방식 재현 시도의 결과물이라는 사용자 설명을 기본값으로 한다.
- 메인 오더 문서는 한국어로 작성한다.
- appendix에서만 개별 에이전트의 관점 차이를 허용한다.
- 결과 비교의 목적은 우열 판정보다 `재현 사실 / drift / 불확실성`의 경계를 또렷하게 만드는 데 있다.

---

## 9. 오더 문서 감리 상태

- 최종 상태: 2026-03-11 기준 비교군 공용 오더 확정본
- 감리 수준: 3-pass 오더 감리 완료
- 비고: `00_test_00` 초기화 이후에도 baseline이 흔들리지 않도록 live tree 의존을 제거했다
