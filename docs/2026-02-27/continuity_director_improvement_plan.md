# 연속성·모순 방지 및 Director 권한 강화 계획

> 작성일: 2026-02-27
> 목적: 상류→하류 데이터 오염, 동계층 정보 전달 오염 식별 + Director 강화 방안
> 제약: 코드 수정 금지 (설계/계획 문서)

---

## 핵심 요약

파이프라인 전체에 걸쳐 **3개 계층의 오염 경로**가 확인됨:

| 계층 | 오염 유형 | 심각도 | 핵심 원인 |
|------|---------|--------|---------|
| Stage 0 → Stage 2 | NPC 생사 이중 진실 | 🔴 HIGH | Bible과 StateTracker 비동기 |
| Stage 2 → Stage 4 | Blueprint 메타정보 미전달 | 🔴 HIGH | Arc 메모리 캐시, 프롬프트 누락 |
| Stage 4 내부 | 피드백 덮어쓰기, HUD 미동기 | 🔴 HIGH | 라운드 간 누적 구조 부재 |

**Director 현재 약점**: 검증은 하지만 강제 차단 불가 (advisory 모드), 재시도 증가 시 기준 완화.

---

## 1. Stage 0 → Stage 2 오염 지점

### 데이터 흐름 요약

```
Bible (JSON) → DB anchors → Stage2Context → FourPhaseArcGenerator
     ↑                           ↑
     고정 스냅샷            StateTracker (동적 누적)
     (ep=0 기준)            (ep=N 실시간 업데이트)
```

### 위험 지점

| ID | 위험도 | 문제 | 영향 |
|----|--------|------|------|
| **H1** | 🔴 | Bible.KeyNPCs.status와 StateTracker.npc_deaths 불일치 | 사망 NPC가 Arc에 "alive"로 등장 |
| **H2** | 🔴 | HUD 얕은 복사 — `list()` 사용으로 중첩 객체 공유 | 이전 Arc의 portfolio가 초기 HUD에 오염 |
| **H3** | 🔴 | AssetLibrary와 StateTracker 동시 전달 시 LLM 모순 신호 | 두 소스가 상반된 NPC 상태를 전달 |
| M1 | 🟡 | PresetRegistry 활성 필드 — snapshot 방식으로 동적 변경 미추적 | 신규 장르 도입 시 스키마 미반영 |
| M2 | 🟡 | 역설계 원고 벡터화 미실행 | Stage 2 벡터 컨텍스트 손실 |

### 근본 원인

**"이중 진실" 문제**: Bible이 SSOT로 설계되었지만 실제로는 고정(ep=0 스냅샷), StateTracker가 최신 상태를 보유. 두 소스를 동시에 LLM에 전달하면 모순 신호 발생.

---

## 2. Stage 2 → Stage 4 오염 지점

### 데이터 흐름 요약

```
Arc (메모리만!) → stage3_orchestrator → Blueprint (DB 저장)
                                              ↓
                   stage4_context_builder → Chief Writer 프롬프트
                   (NPC 3개 필드만 스캔)    (scene_breakdown만 명시)
```

### 위험 지점

| ID | 위험도 | 문제 | 영향 |
|----|--------|------|------|
| **#1** | 🔴 | Arc가 DB에 저장되지 않음 (메모리 캐시만) | 세션 재시작 시 Arc 소실, Stage 4에서 구 Arc 사용 |
| **#2** | 🔴 | NPC 로스터 수집 — npc_deaths/relationship_changes/injuries 3개 필드만 | 엑스트라 NPC 컨텍스트 누락 |
| **#3** | 🔴 | Blueprint 메타정보 미명시 — state_changes, key_npcs, emotional_beat | Chief Writer가 이 화의 핵심 변화를 모름 |
| #4 | 🟡 | Continuity Validator — 아이템/무기/부상/위치만 검증 | NPC 일관성, 스킬, 관계, 시간 미검증 |
| #5 | 🟡 | Chain Link 누락 시 조용한 실패 | 직전 화 결말 이어받기 실패 |

### 핵심 격차

```
Blueprint에 있는 정보:
  ├─ scene_breakdown  ← 프롬프트에 포함 ✓
  ├─ state_changes    ← 프롬프트에 없음 ✗
  ├─ key_npcs         ← 부분적 ✓/✗
  ├─ emotional_beat   ← 프롬프트에 없음 ✗
  └─ chain_link       ← 별도 DB 로드 (중복) ⚠️
```

Blueprint가 완전한 정보를 담고 있지만 Chief Writer 프롬프트가 일부만 활용함.

---

## 3. Stage 4 내부 동계층 오염 지점

### 에이전트 호출 순서

```
Context Builder
    ↓
Chief Writer (앙상블 3개) → Quality Gate (sanitize, critique)
    ↓
Validators (Manuscript / Consistency / Blocking / Continuity)
    ↓
Director 선택·심사
    ↓ PASS
Post-Processor (TruthGate → DB 저장 → HUD 갱신)
```

### 위험 지점

| ID | 위험도 | 문제 | 영향 |
|----|--------|------|------|
| **C1** | 🔴 | director_feedback 덮어쓰기 (누적 아님) | 라운드 N-1 지시사항이 라운드 N에서 소실 |
| **C2** | 🔴 | HUD는 PASS 후에만 갱신 — 재시도 중 Director가 구 HUD 참조 | "이 원고에서 아이템 X를 얻었다"는 맥락 없음 |
| **C3** | 🔴 | BlockingValidator가 advisory 모드 — 차단 불가 | Python 검증 경고가 LLM에만 전달, 무시 가능 |
| **C4** | 🔴 | Context Advisor 고정 슬롯 — Director가 상황별 쿼리 불가 | 필요한 맥락이 없어도 Director가 요청 못함 |
| **C5** | 🔴 | TruthGate가 저장 후 검증 (advisory) | 사망 NPC 원고가 DB에 저장된 후에야 경고 |
| M1 | 🟡 | previous_attempt 최신 라운드만 보존 | 2회 이상 재시도 시 패턴 파악 불가 |
| M2 | 🟡 | mandatory_context 크기 제한 없음 | LLM 토큰 초과 가능 |

---

## 4. Director 현재 역할과 약점

### 현재 역할

| 서브모듈 | 담당 |
|---------|------|
| DirectorGradingSystem | PASS/REJECT 판정, 수정 가이드 |
| DirectorContinuityValidator | Entity 일관성, 원고-Blueprint 연속성 |
| DirectorEnsembleSelector | 3개 후보 비교·선택 |
| DirectorQualityAuditor | 장르 특화, 캐릭터 논리 |
| DirectorCachingManager | 원고 캐시, protagonist_config |

### 핵심 약점

| 약점 | 현상 | 근본 원인 |
|------|------|---------|
| **검증 후 강제 불가** | 모순 감지해도 저장 허용 | TruthGate, BlockingValidator 모두 advisory |
| **재시도 기준 완화** | 3회 이상 재시도 시 점수 기준 -10점 | `get_adaptive_threshold()` 완화 설계 |
| **장기 설정 미검증** | 최근 30화만 참조 | history_check_max_episodes=30 |
| **수정 가이드 불명확** | "50% 씬 누락"만 알려줌, 어떤 씬인지 모름 | 의미론적 매칭 부재 |

---

## 5. Director 강화 아이디어

### 아이디어 1: CRITICAL HOLD (거부권 강화)

**개요**: 사망 NPC 행동·미보유 아이템 사용 등 CRITICAL 모순 감지 시, 기존 REJECT가 아닌 `CRITICAL_HOLD`로 반환. 이 상태에서는 재시도 기준 완화 불가.

**방식**:
- Director가 판정 시 `verdict: "CRITICAL_HOLD"` 반환 가능
- Stage4InterviewRound에서 CRITICAL_HOLD는 `adaptive_thresholds` 비활성화
- 수정 지침: "어떤 설정이 모순되고 어떻게 수정할지" 구체적 제시 필수

**난이도**: L | **효과**: Director 권한 강화 핵심

---

### 아이디어 2: Blocking TruthGate (저장 차단)

**개요**: TruthGate의 5개 검사 중 CRITICAL 항목(사망 NPC 행동)은 `blocking=True`로 전환. 저장 전 차단.

**방식**:
- `validate()` 반환값에 `blocking_violations` 필드 추가
- CRITICAL 목록: deceased_resurrection, unowned_item_use
- Stage4PostProcessor에서 blocking_violations 존재 시 저장 중단, Director 재심사 트리거

**난이도**: M | **효과**: 사망 NPC 원고 100% 방지

---

### 아이디어 3: 다층 히스토리 검증 (시간대별 계층화)

**개요**: 연속성 검증 범위를 계층화:
- 최근 10화: 전문 기반 검증 (현재)
- 11~30화: 요약 기반 검증 (구간 상태 변화)
- 초반 Arc 종료 시점: 장기 떡밥 핵심 설정만

**방식**:
- `check_manuscript_history_conflicts()` 개선
- episode_meta.summary 테이블 활용 (이미 존재)
- Tier 별로 다른 프롬프트 섹션

**난이도**: M | **효과**: 초반 설정과의 모순 감지 +40%

---

### 아이디어 4: Director 신뢰도 점수 (Confidence Score)

**개요**: 3개 후보의 점수 분산도로 신뢰도 계산. 분산이 작으면(후보들이 비슷) 신뢰도 낮음 → 추가 검토 권장.

**방식**:
- `director_selections` 테이블에 `confidence_score`, `confidence_reason` 컬럼 추가
- 신뢰도 < 70% → 해당 에피소드 플래그
- 후속 재시도 통계로 신뢰도 정확도 검증 가능

**난이도**: L | **효과**: 선택 품질 모니터링, 편향 감지

---

### 아이디어 5: Registry Governance (Entity 변경 Director 승인)

**개요**: NPC 속성·아이템·관계 변경을 Python이 자동 적용하는 대신, Director가 명시적으로 승인한 state_updates만 반영.

**방식**:
- Writer의 state_updates 제안 → Director 검증·승인 → 반영
- 승인 이력: `director_entity_approvals` 테이블
- CLAUDE.md 대원칙 2 완벽 이행 (팩트 수정 권한은 LLM만)

**난이도**: H | **효과**: 설정 일관성 100% 보장, 오염 원천 차단

---

### 아이디어 6: Scene Gap Analyzer (씬 누락 자동 분석)

**개요**: Blueprint 씬 반영률 미달 시 "어떤 씬이 누락됐는지" 의미론적 매칭으로 특정. Writer에게 구체적 수정 지침 제공.

**방식**:
- SemanticPlotGuard의 임베딩 모델 재활용 (이미 존재)
- Blueprint scene_breakdown vs 원고 문장 임베딩 매칭
- 매칭 미달 씬: "Scene 3 (대면·갈등) 누락 — 주인공이 X와 직접 대면하는 장면 필요"

**난이도**: H | **효과**: Writer 수정 정확도 +40%, 재시도 횟수 -30%

---

### 아이디어 7: director_feedback 누적 구조

**개요**: 현재 director_feedback은 라운드마다 덮어씌워짐. 누적 방식으로 전환하여 Chief Writer가 전체 수정 이력을 볼 수 있게 함.

**방식**:
- `director_feedback += f"\n[라운드{round_num}] {reason}"` 방식으로 전환
- 라운드별 지시사항 누적 → Chief Writer에게 전달
- 최대 누적 길이 제한 (토큰 예산)

**난이도**: L | **효과**: Chief Writer 혼란 방지, 재시도 효율 향상

---

## 6. 구현 우선순위

### Phase 1 — 즉시 (저난이도, 고효과)

| 순서 | 아이디어 | 난이도 | 핵심 효과 |
|------|---------|--------|---------|
| 1 | #7 director_feedback 누적 | L | 재시도 루프 안정화 |
| 2 | #1 CRITICAL HOLD | L | Director 거부권 강화 |
| 3 | #4 신뢰도 점수 | L | 선택 품질 모니터링 |

### Phase 2 — 단기 (중난이도, 핵심 구조)

| 순서 | 아이디어 | 난이도 | 핵심 효과 |
|------|---------|--------|---------|
| 4 | #2 Blocking TruthGate | M | 치명적 오류 저장 방지 |
| 5 | #3 다층 히스토리 | M | 초반 설정 보호 |

### Phase 3 — 장기 (고난이도, 아키텍처 개선)

| 순서 | 아이디어 | 난이도 | 핵심 효과 |
|------|---------|--------|---------|
| 6 | #5 Registry Governance | H | 설정 오염 원천 차단 |
| 7 | #6 Scene Gap Analyzer | H | Writer 수정 정확도 향상 |

---

## 7. 별도 검토 사항

### Arc DB 저장 (구조적 문제)

Arc가 메모리에만 존재하는 현재 설계는 세션 재시작 시 Arc 소실 위험이 있음. 단기적으로:
- `arcs` 테이블 생성 후 Stage 2 완료 시점에 Arc 전체 저장
- Stage 3~4에서 메모리 캐시가 아닌 DB 로드

### Blueprint 프롬프트 보강

`stage_changes`, `key_npcs`, `emotional_beat`를 Chief Writer 프롬프트에 명시적 섹션으로 추가:

```
### 📌 이 화의 핵심 변화
- 상태 변화: {state_changes}
- 주요 NPC: {key_npcs}
- 감정 비트: {emotional_beat}
```

현재 scene_breakdown JSON 안에 암묵적으로 포함되어 있어 Chief Writer가 간과 가능.

### NPC 생사 SSOT 단일화

두 가지 선택지:
- **A안**: StateTracker가 SSOT. Bible의 NPC 목록은 참조용, 생사 상태는 StateTracker만 권위 있음.
- **B안**: Bible 업데이트. NPC 사망 시 `update_npc_status()`로 Bible과 StateTracker 동시 갱신.

A안이 CLAUDE.md 원칙(팩트 수정은 LLM만)에 더 부합. B안은 Python이 자동으로 Bible을 수정하므로 원칙 위반.

---

## 8. 예상 효과

| 개선 후 | 변화 |
|---------|------|
| 사망 NPC 등장 | -100% (Blocking TruthGate) |
| 초반 설정과의 모순 | -40% (다층 히스토리) |
| Blueprint 미반영 원고 | -30% (Scene Gap Analyzer) |
| 재시도 루프 비효율 | -25% (feedback 누적 + CRITICAL HOLD) |
| Director 우회 원고 | -100% (Registry Governance) |
