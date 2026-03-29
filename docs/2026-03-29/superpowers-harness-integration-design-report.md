## Superpowers Harness Integration Design Report

Date: 2026-03-29
Status: final (3-pass audited)
Track: system
Type: design report (execution SSOT 전환 대상)

---

### 1. Scope and Intent

obra/superpowers 프레임워크의 장점 5가지를 기존 ROL 하네스 체계에 선택적으로 이식한다.

목적: 기존 프로젝트 유지보수(survey/patch/refactor) 워크플로우에서 실행 품질을 높인다.

**이식 대상**: SessionStart hook, micro-plan 세분화, 서브에이전트 격리, spec compliance 리뷰, anti-rationalization 가드레일.

**이식 제외**: TDD 강제(서사 파이프라인 비적용), brainstorming 스킬(narrative router가 담당), git worktree 격리(Agent tool 내장), all-or-nothing 적용(gary advisory 샌드박스가 더 성숙).

**GSD와의 관계**: GSD는 신규 프로젝트 전용(milestone/phase 구조). 이 이식은 기존 프로젝트 ROL 실행 레이어에만 적용. GSD와 경합하지 않는다.

**GSD 비침범 보증**: 이 설계의 모든 변경은 GSD 파일/동작과 완전 독립임을 실사 확인.
- `.claude/settings.json`: GSD hook 코드(`gsd-check-update.js` 등)와 GSD 업데이트(`/gsd:update`)·설정(`/gsd:settings`) 어디서도 `settings.json`을 재생성하거나 덮어쓰지 않음 (grep 전수 확인). 기존 GSD hook 항목을 보존하고 SessionStart 배열에 별도 항목으로만 추가.
- `.claude/bootstrap.md`: GSD가 읽지 않는 신규 파일.
- `AGENTS.md`: GSD가 파싱하지 않음 (GSD는 `.planning/` 사용).
- `docs/implementation/` 신규·수정: GSD scope 밖.
- GSD 전용 파일(`.claude/hooks/gsd-*.js`, `.claude/get-shit-done/`, `.claude/gsd-*`, `.claude/commands/gsd/`)은 일절 접촉하지 않음.

---

### 2. Research Findings Summary

#### 2.1 Superpowers 핵심 패턴 (원본 SKILL.md 기반)

**writing-plans**: 태스크 단위 2-5분. 각 태스크에 `Create:`, `Modify:` (라인 범위 포함), `Test:` 파일 목록. 실제 코드 블록 필수 (TBD/TODO/placeholder 금지). Self-review 체크리스트 포함.

**subagent-driven-development**: 컨트롤러가 태스크 전문을 서브에이전트에 복붙 (서브에이전트가 plan 파일을 읽게 하지 않음). 3단 리뷰 체인: Implementer → Spec Reviewer → Code Quality Reviewer. 상태 프로토콜: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED. 모델 선택: 단순 1-2 파일 = cheap, 통합 = standard, 리뷰 = capable.

**using-superpowers**: SessionStart hook으로 세션 시작 시 자동 주입. "1%라도 관련 스킬이 있으면 invoke" 규칙. Red flags 테이블 12개로 합리화 차단.

**verification-before-completion**: "검증 증거 없이 완료 선언 금지." IDENTIFY → RUN → READ → VERIFY → CLAIM 순서 강제.

#### 2.2 현재 하네스 실행 레이어 갭 (companion harness 전량 분석)

현재 하네스 체인의 실행 세분도 6계층:

```
Layer 1: Orders & Dispatch (init harness)
Layer 2: Quality Gates (3-pass audit)
Layer 3: Synthesis & Staging (execution synthesis)
Layer 4: Queue & Ordering (temp queue roadmap)
Layer 5: Execution Tranches (SSOT template §8)  ← 여기서 끝남
Layer 6: Closure (execution closure)
```

**Layer 5와 Layer 6 사이에 구현 레벨 세분화가 없음.** Execution SSOT의 트랜치는 "RC-1 수정: _attempt_backup_recovery에 SessionLogger 추가" 수준이지, "base_agent.py L1530 이후에 이 코드를 삽입, 파라미터는 이것" 수준이 아님.

#### 2.3 SessionStart Hook 인프라 (Claude Code 네이티브)

`.claude/settings.json`의 `hooks.SessionStart` 섹션에 command type hook 등록. 스크립트가 stdout으로 출력한 내용이 세션 컨텍스트에 주입됨. `$CLAUDE_PROJECT_DIR` 환경변수 사용 가능. `startup|resume|compact` 매처로 세션 시작/재개/압축 시 자동 발동.

---

### 3. Design: 5-Point Integration Chain

```
  [1] SessionStart Hook
       ↓ (세션 시작 시 자동 발동)
  [2] Micro-Plan 세분화 Gate
       ↓ (execution SSOT 트랜치 → implementation-level 태스크)
  [3] 서브에이전트 격리 실행
       ↓ (micro-plan 단위 디스패치 + 상태 프로토콜)
  [4] Spec Compliance 리뷰
       ↓ (계획 대비 구현 일치 확인)
  [5] Anti-Rationalization 가드레일
       (전 단계에 걸쳐 합리화 방지)
```

---

### 4. 각 항목 상세 설계

#### 4.1 SessionStart Hook

**변경 대상**: `.claude/settings.json` (기존 파일에 hook 추가)

**현재 상태**: `.claude/settings.json`에 이미 GSD SessionStart hook이 등록됨 (`node .claude/hooks/gsd-check-update.js`). PostToolUse, PreToolUse hook도 존재. Hook 인프라가 이미 Windows(Git Bash/MINGW32)에서 동작 확인됨.

**메커니즘**: 기존 GSD SessionStart hook 배열에 우리 부트스트랩 hook을 추가. 세션 시작 시 GSD 업데이트 체크와 함께 init harness 핵심 지시가 stdout으로 주입됨.

**설계 결정 — 전문 주입 vs 요약 주입**:

init harness 전문(265줄)을 hook으로 주입하면 매 세션마다 컨텍스트 예산을 소비. Superpowers의 `using-superpowers`도 전문 주입이지만, 그 스킬은 메타-라우터 역할이라 분량이 적음.

채택: **요약 주입 + 전문 읽기 강제**. Hook이 50줄 이내의 부트스트랩 요약을 주입하고, 그 안에서 "시스템 오더면 init harness 전문을 반드시 읽어라"를 강제.

```
# .claude/bootstrap.md (50줄 이내)
## Session Bootstrap (auto-injected)
- 이 워크스페이스 SSOT: AGENTS.md
- Track split: 시스템 오더 vs 서사 파이프라인
- 시스템 오더 → docs/implementation/system-order-init-harness.md 전문 읽기 필수
- 서사 오더 → docs/narrative-router/SSOT_narrative-router-integrated-order.md 전문 읽기 필수
- 이 부트스트랩을 읽었으면 해당 harness 읽기 전에 응답하지 마라
```

**Hook 설정** (기존 settings.json의 SessionStart 배열에 추가):
```json
{
  "matcher": "startup|resume|compact",
  "hooks": [
    {
      "type": "command",
      "command": "cat \"$CLAUDE_PROJECT_DIR/.claude/bootstrap.md\""
    }
  ]
}
```

**GSD hook과의 공존**: GSD의 `gsd-check-update.js`는 매처 없이(모든 SessionStart에) 발동. 우리 hook은 `startup|resume|compact` 매처로 발동. 둘 다 SessionStart 배열의 별도 항목으로 등록되므로 충돌 없음.

**기존 체계 영향**: AGENTS.md의 "시스템 오더는 먼저 init harness를 읽는다" 지시는 유지. Hook은 이 지시를 강화하는 보조 장치이지 대체가 아님.

#### 4.2 Micro-Plan 세분화 Gate

**삽입 지점**: Execution SSOT Layer 5(트랜치 정의) → Realization 시작 사이.

**트리거 조건**: 코드 수정 작업에서, execution SSOT의 트랜치가 다음 중 하나에 해당하면 micro-plan 작성:
- 3개 이상 파일 수정 필요
- 변경 간 의존 관계 존재 (A의 결과가 B의 입력)
- 부작용 검증 필요 (sink, DB, 로그 변경)

트리거 조건 미달 시 (1-2 파일 단순 패치): micro-plan 없이 직접 실행. **과잉 프로세스 방지.**

**Micro-Plan 포맷** (Superpowers writing-plans 패턴 차용, 우리 문맥 적응):

```markdown
## Micro-Plan: [트랜치명]

Parent SSOT: docs/YYYY-MM-DD/xxx-execution-ssot.md
Status: draft | active | closed

### Tasks

#### Task 1: [제목] (~N분)
- Modify: `modules/domain/agents/base_agent.py` (L1530 부근)
- 변경 내용:
  ```python
  [실제 코드 — placeholder 금지]
  ```
- 검증: [구체적 검증 방법]

#### Task 2: [제목] (~N분)
...

### Acceptance
- [ ] 각 Task 검증 통과
- [ ] 기존 테스트 회귀 없음
- [ ] Parent SSOT acceptance criteria 충족
```

**기존 템플릿 변경**: `execution-ssot-template.md` §8(Execution Tranches) 이후에 micro-plan 링크 섹션 추가.

```markdown
## 8A. Micro-Plan Linkage
| Tranche | Micro-Plan 필요 | Path | Status |
|---------|----------------|------|--------|
```

#### 4.3 서브에이전트 격리 실행

**적용 시점**: Micro-plan이 존재하는 트랜치의 실행 단계에서만.

**디스패치 규칙** (Superpowers subagent-driven-development 패턴 차용):

1. 컨트롤러(부모 세션)가 micro-plan의 각 Task를 Agent tool로 디스패치
2. **서브에이전트에 전달하는 것**: Task 전문 (복붙, plan 파일 읽기 금지), 대상 파일 경로, 거버넌스 가드레일 요약, baseline commit
3. **서브에이전트에 전달하지 않는 것**: 다른 트랜치 컨텍스트, survey 전문, 큐 상태
4. **상태 프로토콜**: 서브에이전트는 완료 시 다음 중 하나로 보고:
   - `DONE` — 변경 완료, 검증 통과
   - `DONE_WITH_CONCERNS` — 완료했으나 주의 사항 있음
   - `NEEDS_CONTEXT` — 추가 정보 필요, 무엇이 필요한지 명시
   - `BLOCKED` — 진행 불가, 사유 명시
5. **병렬 디스패치 금지**: 같은 파일을 수정하는 Task는 순차 실행 (Superpowers 동일 규칙)
6. **모델 선택**: 단순 1-2 파일 수정 = sonnet, 통합/의존성 = opus, 리뷰 = opus

**기존 체계 영향**: ROL Mode A(Queue Realization)와 Mode C(Direct Focused Patch) 양쪽에 적용 가능. 하지만 Mode C는 micro-plan 트리거 조건 미달이 대부분이므로, 실질적으로 Mode A에서 주로 발동.

#### 4.4 Spec Compliance 리뷰

**삽입 지점**: 코드 3-pass gate (init harness Step 3D) 확장.

**현재 코드 3-pass**:
- Pass 1: 사전 authority/sink 감사
- Pass 2: 사후 diff 감사
- Pass 3: 검증

**변경 — Pass 2를 2A+2B로 분리**:
- Pass 2A (Spec Compliance): "micro-plan 또는 execution SSOT의 지시대로 구현했는가?"
  - 누락된 변경 항목 점검
  - 계획에 없는 추가 변경 점검 (scope creep)
  - 대상 파일/라인 범위 일치 확인
- Pass 2B (Code Quality): "구현 품질이 적절한가?"
  - authority/sink 무결성 (기존 Pass 2의 내용)
  - dead wrapper, duplicate definition, stale compat shell 검출

**Superpowers와의 차이**: Superpowers는 Spec Reviewer와 Code Quality Reviewer를 별도 서브에이전트로 분리. 우리는 같은 컨텍스트에서 pass 분리만 적용. 이유: 리뷰 서브에이전트 디스패치 오버헤드 대비 이점이 불확실하고, 우리 3-pass 체계가 이미 단일 컨텍스트에서 충분히 동작.

**서브에이전트 실행 시 적용**: 서브에이전트가 DONE 보고 후, 컨트롤러가 Pass 2A(spec compliance)를 직접 수행. 통과 시에만 다음 Task 디스패치.

#### 4.5 Anti-Rationalization 가드레일

**변경 대상**: AGENTS.md

**추가 섹션 — "Shortcut Rationalization Prevention"**:

```markdown
## Shortcut Rationalization Prevention

다음 합리화 패턴을 명시적으로 금지한다:

| 합리화 | 왜 금지인가 |
|--------|-----------|
| "시간이 없으니까 이번만 건너뛰자" | 시간 압박은 프로세스 생략의 근거가 아니다. 범위를 줄여라. |
| "어차피 비슷하니까 한꺼번에 하자" | 유사해 보이는 변경도 각각 검증해야 한다. |
| "테스트가 통과할 거니까 안 돌려도 된다" | 검증 증거 없는 완료 선언 금지. |
| "작은 변경이니까 리뷰 안 해도 된다" | 작은 변경이 큰 부작용을 만든다. 3-pass gate는 규모로 면제되지 않는다. |
| "이전에 비슷한 걸 했으니까 확인 안 해도 된다" | 이전 경험은 현재 검증을 대체하지 않는다. |
| "문서화는 나중에 하자" | 코드 변경과 문서 갱신은 같은 작업 단위다. |
```

**Superpowers와의 차이**: Superpowers는 Cialdini 설득 원칙(권위, 일관성, 희소성)을 사용한다고 주장하지만, 실제 구현은 위와 같은 합리화 테이블 + red flags 목록. 우리도 같은 패턴을 적용하되, 마케팅 용어 없이 실질 내용만.

---

### 5. 변경 대상 파일 총괄

| 파일 | 작업 | 신규/수정 |
|------|------|----------|
| `.claude/settings.json` | SessionStart hook 등록 | 신규 또는 수정 |
| `.claude/bootstrap.md` | 부트스트랩 요약 (50줄 이내) | 신규 |
| `AGENTS.md` | Anti-Rationalization 섹션 추가 | 수정 |
| `docs/implementation/system-order-init-harness.md` | Step 3D 코드 3-pass에 2A/2B 분리 추가, micro-plan gate 참조 추가 | 수정 |
| `docs/implementation/execution-ssot-template.md` | §8A Micro-Plan Linkage 섹션 추가 | 수정 |
| `docs/implementation/micro-plan-template.md` | Micro-plan 문서 템플릿 | 신규 |
| `docs/implementation/subagent-dispatch-contract.md` | 서브에이전트 디스패치 규칙 + 상태 프로토콜 + 컨텍스트 큐레이션 | 신규 |

**변경하지 않는 파일**: companion harness 16개(기존 구조 유지), 6개 계약 문서(기존 유지), 서사 파이프라인 관련 전체(scope 외).

---

### 6. Acceptance Criteria

1. 신규 세션 시작 시 bootstrap.md 내용이 자동으로 컨텍스트에 주입되는 것을 확인
2. resume/compact 시에도 hook이 재발동하는 것을 확인
3. Execution SSOT 작성 시 §8A micro-plan linkage 섹션이 포함되는 것을 확인
4. Micro-plan 트리거 조건 미달 시 micro-plan 없이 직접 실행 가능한 것을 확인 (과잉 프로세스 방지)
5. 서브에이전트 디스패치 시 상태 프로토콜(DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED)이 준수되는 것을 확인
6. 코드 3-pass gate에서 Pass 2A(spec compliance)가 Pass 2B(code quality) 이전에 수행되는 것을 확인
7. AGENTS.md anti-rationalization 테이블이 기존 대원칙/complexity guardrails와 충돌하지 않는 것을 확인

---

### 7. Risk Assessment

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| Hook이 Windows 환경에서 동작하지 않음 | ~~HIGH~~ **RESOLVED** | 실사 결과: GSD hook이 이미 `.claude/settings.json`에서 Windows(MINGW32/Git Bash)에서 동작 중. `cat` 명령 사용 가능 확인. bash(`/usr/bin/bash`), python 모두 사용 가능 |
| GSD SessionStart hook과 충돌 | **RESOLVED** | GSD hook은 매처 없이 발동, 우리 hook은 `startup\|resume\|compact` 매처. 같은 배열의 별도 항목으로 공존. GSD의 hooks/update/settings 코드 전수 grep 결과 `settings.json` 쓰기 없음 확인 |
| Micro-plan 작성이 과잉 프로세스가 됨 | MEDIUM | 트리거 조건 3가지(3+ 파일, 의존관계, 부작용 검증) 미달 시 면제 |
| 서브에이전트 디스패치 오버헤드가 이점보다 큼 | MEDIUM | 단순 패치는 직접 실행, micro-plan 대상만 격리 |
| Anti-rationalization이 실효성 없음 | LOW | 비용 제로(문구 추가). 효과 없어도 손해 없음 |
| 기존 companion harness와 충돌 | LOW | 신규 삽입 지점이 기존 체인 중간이 아닌 Layer 5-6 사이. 기존 harness 수정은 init harness의 Step 3D 확장과 SSOT 템플릿 §8A 추가뿐 |

---

### 8. Execution Tranches (SSOT 전환 대비)

#### Tranche 1: SessionStart Hook 구축
- `.claude/settings.json` hook 등록
- `.claude/bootstrap.md` 작성 (50줄 이내)
- Windows 환경 동작 검증
- 의존: 없음

#### Tranche 2: Anti-Rationalization 가드레일
- AGENTS.md에 섹션 추가
- 기존 대원칙/complexity guardrails와 충돌 검토
- 의존: 없음 (Tranche 1과 병렬 가능)

#### Tranche 3: Micro-Plan 인프라
- `docs/implementation/micro-plan-template.md` 신규 작성
- `docs/implementation/execution-ssot-template.md` §8A 추가
- `docs/implementation/system-order-init-harness.md`에 micro-plan gate 참조 추가
- 의존: 없음 (Tranche 1, 2와 병렬 가능)

#### Tranche 4: 서브에이전트 디스패치 계약
- `docs/implementation/subagent-dispatch-contract.md` 신규 작성
- 상태 프로토콜, 컨텍스트 큐레이션 규칙, 모델 선택 지침 포함
- 의존: Tranche 3 (micro-plan 포맷이 정해져야 디스패치 규칙 확정)

#### Tranche 5: Spec Compliance 리뷰 통합
- `docs/implementation/system-order-init-harness.md` Step 3D 확장 (Pass 2 → 2A + 2B)
- 의존: Tranche 3 (micro-plan이 spec compliance 기준이 됨)

---

### 9. Confidence Assessment

| 항목 | 확신도 | 근거 |
|------|--------|------|
| SessionStart hook 메커니즘 | 99% | Claude Code 네이티브 기능 + GSD hook이 동일 환경에서 이미 동작 중 확인 |
| Windows hook 동작 | 98% | GSD hook(`node .claude/hooks/gsd-check-update.js`)이 동일 `.claude/settings.json`에서 MINGW32 환경에서 동작 확인. bash 및 python 사용 가능 확인 |
| GSD hook 공존 | 97% | SessionStart 배열의 별도 항목, 매처 분리 |
| Micro-plan 포맷 적합성 | 95% | Superpowers writing-plans 검증됨, 우리 SSOT 체계와 호환 |
| Spec compliance 리뷰 가치 | 95% | Superpowers 핵심 설계 원칙, 우리 코드 3-pass에 자연 삽입 |
| 기존 하네스 비파괴 | 97% | 삽입 지점이 Layer 5-6 사이, 기존 chain 수정 최소 |
| 서브에이전트 격리 실효성 | 92% | Superpowers 실증 + Agent tool 내장. 우리 작업 규모에서 완전 실증은 미완이나, fallback observability gap 4항목 패치가 micro-plan + 서브에이전트 적합 사례 (3+ 파일, 의존관계 존재, sink 부작용 검증 필요) |
| Anti-rationalization 실효성 | 88% | 비용 제로. LLM 행동 변화 정량 검증 어려우나, Superpowers의 red flags 테이블이 106K stars 프로젝트에서 실전 검증됨 |
| **종합** | **95%** | 모든 항목 88% 이상, 하한 2개(서브에이전트 92%, anti-rationalization 88%) 모두 비용 대비 위험 수용 가능 |

---

### 10. Proof of Concept: Fallback Observability Gap → Micro-Plan 변환

직전 survey(`stage4-provider-fallback-observability-gap-full-survey.md`)의 Bounded Remediation Options 1-4를 micro-plan으로 변환한 예시. 이 예시가 서브에이전트 격리 실효성 판정 근거.

**Micro-plan 트리거 조건 점검**:
- 3+ 파일 수정: `base_agent.py`, `metrics_collector.py`, `session_logger.py` → ✓
- 변경 간 의존관계: RC-2(cost 계산)가 RC-1(로깅) 이후에 의미 있음 → ✓
- 부작용 검증: llm_io.jsonl, project_data.db, episode_production.jsonl sink 영향 → ✓
- **결론: micro-plan 대상**

**변환 예시**:

```
Task 1: RC-1 backup recovery SessionLogger 추가 (~5분)
- Modify: base_agent.py (L1530 부근, _attempt_backup_recovery)
- 변경: self.backup_model 성공 시 BaseAgent._session_logger_global.log_llm_call() 추가
- 검증: 기존 테스트 통과 + llm_io.jsonl에 backup success entry 존재 확인

Task 2: RC-2 cost 계산 모델 수정 (~3분)
- Modify: base_agent.py (L496, _session_token_cost_kwargs)
- 변경: getattr(self, "primary_model") → served model parameter 사용
- 검증: llm_io.jsonl의 cost 필드가 실제 served model 가격 반영

Task 3: RC-3 MetricsCollector model override (~5분)
- Modify: metrics_collector.py (end_call, L232 부근)
- 변경: served_model optional parameter 추가, metric.model 갱신
- Modify: base_agent.py (end_call 호출부)
- 변경: 호출 시 served_model=current_model 전달
- 검증: model_breakdown에 실제 served model로 토큰 귀속

Task 4: RC-4 Anthropic credit-exhaustion 분류 (~3분)
- Modify: base_agent.py (L1227, _classify_api_error_mode)
- 변경: "credit balance" 또는 "insufficient" 감지 → is_quota_exhausted = True
- 검증: 400 credit-exhaustion 에러가 Mechanism A(in-loop fallback)로 라우팅
```

**서브에이전트 디스패치 적합성**:
- Task 1, 2, 4: 단일 파일(base_agent.py) → 순차 실행 필수 (같은 파일 병렬 금지)
- Task 3: 2파일(metrics_collector.py + base_agent.py) → Task 2 이후 순차
- 각 Task 완료 후 컨트롤러가 Pass 2A(spec compliance) 수행
- 모델 선택: 모두 sonnet 적합 (단일-2파일, 명확한 변경 지시)

---

### 11. 3-Pass Audit Record

#### Pass 1 — Structure and Scope

- **범위 적절성**: Superpowers 전체 도입이 아닌 5가지 선택적 이식으로 한정. GSD와의 역할 분리 명시. 서사 파이프라인 제외. PASS
- **섹션 구성**: Intent → Research → Design → Detail → Files → Acceptance → Risk → Tranches → Confidence → PoC → Audit. execution SSOT 전환에 필요한 구조 완비. PASS
- **기존 체계 참조**: init harness, 코드 3-pass gate, SSOT 템플릿, companion harness 16개의 관계 명시. PASS
- **Pass 1 판정**: PASS

#### Pass 2 — Evidence and Consistency

- **Superpowers 원본 대조**: writing-plans, subagent-driven-development, using-superpowers, verification-before-completion SKILL.md 전문 조사 완료. 설계가 원본 패턴과 일치하되 TDD/brainstorming은 제외. PASS
- **현재 하네스 갭 대조**: companion harness 7개(survey, closure, 3-pass, synthesis, queue-roadmap, SSOT template, roadmap template) 전문 분석 완료. Layer 5-6 사이 갭 확인. PASS
- **Windows hook 실사**: `.claude/settings.json` 확인, GSD hook 동작 확인, bash/python 가용성 확인. Risk 테이블 갱신 완료. PASS
- **PoC 대조**: fallback observability gap survey의 4항목이 micro-plan 트리거 조건 3개 모두 충족. Task 분해 수준이 Superpowers writing-plans 포맷과 일치. PASS
- **수치 일관성**: 변경 파일 7개(신규 3 + 수정 4), 트랜치 5개, acceptance criteria 7개 — 상호 참조 일치. PASS
- **Pass 2 판정**: PASS

#### Pass 3 — Actionability and Overclaim

- **실행 가능성**: 각 트랜치가 독립 실행 가능하거나 의존관계 명시. Tranche 1-3 병렬, Tranche 4-5 순차 의존. PASS
- **과대 주장 점검**:
  - "anti-rationalization이 에이전트 행동을 바꾼다"고 주장하지 않음 — "비용 제로, 효과 불확실"로 한정. PASS
  - "서브에이전트가 항상 이점이 있다"고 주장하지 않음 — "단순 패치는 직접 실행" 면제 조건 명시. PASS
  - "Superpowers가 GSD보다 낫다"고 주장하지 않음 — "GSD는 신규 프로젝트, 이것은 유지보수"로 역할 분리. PASS
- **가드레일 점검**: micro-plan 트리거 조건 미달 시 면제(과잉 프로세스 방지), 병렬 디스패치 금지(충돌 방지), GSD hook 공존(충돌 방지). PASS
- **Pass 3 판정**: PASS

**종합 확신도: 95%**
