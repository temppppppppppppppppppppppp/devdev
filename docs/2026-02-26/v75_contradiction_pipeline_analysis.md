# V75 — 모순 관리 파이프라인 설계 분석

> 2026-02-26 감리 결과 (2차 심층 감리 반영).
> C+LLM(State-Text Verifier) + B(역류 에스컬레이션) 동시 적용 시 충돌 분석.

---

## 1. 현재 모순 감지 레이어 현황

```
Stage 2 (Arc)       ⭐⭐   — 3후보 앙상블 + Director 1회 심사, 패치 모드 있음
Stage 3 (Blueprint) ⭐⭐⭐  — 3후보 앙상블 + Director 심사, 단 재시도 루프 없음
Stage 4 (Manuscript) ⭐⭐⭐⭐ — 9겹 검증 + 5라운드 루프 + CoVe + 패치 모드
SSOT (Post-PASS)    ⭐      — TruthGate advisory 5개 검사, 차단 없음
```

### 치명적 빈틈 5개

| # | 빈틈 | 위험도 | 현재 대응 |
|---|------|:---:|------|
| **G1** | state_changes ≠ 원고 텍스트 (Director가 서사만 보고 수치 불일치 승인) | CRITICAL | 없음 |
| **G2** | 역류 불가 (S4 Director가 Arc 결함 발견 → S4만 재시도) | HIGH | 없음 |
| **G3** | Arc ↔ Treatment 검증 없음 (Arc가 Treatment 의도를 이탈해도 무방) | HIGH | 없음 |
| **G4** | FactLedger + WorldState 이중 기록 (Director state vs Manager state 충돌 가능) | MEDIUM | 마지막 쓰기가 이김 |
| **G5** | cumulative_bible 캐시 무효화 누락 (Arc 재생성 시 stale) | MEDIUM | 없음 |

---

## 2. 제안 기능 2건

### Feature C+LLM: State-Text Verifier

**목적**: G1 해결 — state_changes의 숫자/이름이 원고 텍스트와 일치하는지 검증

**동작**:
```
Director PASS
    ↓
[Python 1차] state_changes에서 핵심값 추출 (NPC 이름, 금액, 아이템)
    ↓
[Gemini Flash 2차] "원고에서 이 값이 실제로 나타나는가?" 질문
    ↓
불일치 → advisory 경고 + Director 프롬프트에 주입
일치 → 그대로 SSOT 확정
```

**패턴**: TruthGate와 동일 (advisory, non-blocking)

**삽입 위치**: `stage4_post_processor.py` L210 이후, HUD 업데이트(L212) 이전

### Feature B: Upstream Escalation

**목적**: G2 해결 — Director REJECT 원인이 상류에 있으면 상류로 전파

**동작**:
```
Director REJECT (reason="논리 오류, 아크 설계 자체가 잘못됨")
    ↓
[Python] error_category 분석:
    QUALITY_ISSUE → S4 재시도 (현재와 동일)
    LOGIC_ERROR  → escalation_target 판단
    ↓
escalation_target = "stage3_blueprint"
    → S3 단일 에피소드 재생성 → S4 재시도
    ↓
escalation_target = "stage2_arc"
    → 사용자 확인 후 S2 재생성 → S3 재생성 → S4 재시도
```

**패턴**: 현재 없음 — 신규 패턴

---

## 3. 충돌 분석 매트릭스

### 3.1 C+LLM 단독 위험

| 항목 | 위험도 | 분석 |
|------|:---:|------|
| 동시성 | ✅ 없음 | 에피소드 순차 처리, 추가 잠금 불필요 |
| DB 정합성 | ✅ 없음 | advisory 패턴 — DB 쓰기 전 경고만, 저장 흐름 변경 없음 |
| LLM 비용 | ✅ 미미 | Gemini Flash 1회/에피소드, ~$0.001 |
| 에러 전파 | ✅ 안전 | LLM 실패 시 SilentPass (경고 로그, 저장 진행) |
| 기존 코드 충돌 | ✅ 없음 | TruthGate 옆에 병렬 삽입, 기존 시그니처 변경 없음 |
| 테스트 영향 | ✅ 없음 | feature flag OFF 시 기존 테스트 영향 0 |

**결론: C+LLM은 안전. 문제 없음.**

### 3.2 B(역류) 단독 위험

| 항목 | 위험도 | 분석 |
|------|:---:|------|
| 동시성 | ⚠️ 중간 | S4 진행 중 S3 재생성 → 이미 로드된 blueprint stale 위험 |
| DB 정합성 | ⚠️ 중간 | S3 재생성 시 blueprints 테이블 overwrite → 이미 쓴 에피소드 영향 없음(독립 row), 단 다음 에피소드 영향 |
| cumulative_bible | ⚠️ 중간 | Arc 재생성 시 캐시 무효화 필수 — 현재 자동 무효화 없음 |
| WorldState/FactLedger | ⚠️ 높음 | 이미 확정된 에피소드의 state는 롤백 불가 — 새 Arc가 과거 state와 충돌 가능 |
| 사용자 경험 | ⚠️ 중간 | "갑자기 Arc 재생성" → 사용자 혼란, 확인 필요 |
| 에러 전파 | ⚠️ 높음 | S2 재생성 실패 → S3/S4 모두 멈춤 (연쇄 장애) |

**결론: B(역류)는 위험 요소 있음. 완화 조건 필요.**

### 3.3 C+LLM과 B 동시 적용 시 교차 충돌

| 시나리오 | 위험도 | 분석 |
|----------|:---:|------|
| C가 불일치 감지 + B가 상류 에스컬레이션 | ✅ 보완적 | C가 "뭐가" 잘못인지 감지, B가 "어디서" 고칠지 결정 — 상호 보완 |
| C가 LLM 실패 + B가 에스컬레이션 판단 | ✅ 독립적 | C 실패는 advisory skip, B 판단은 Director error_category 기반 — 서로 의존 없음 |
| B가 Arc 재생성 → C가 이전 검증 결과와 충돌 | ✅ 없음 | C는 매 에피소드 독립 실행, 이전 결과 캐시 없음 |
| B가 Blueprint 재생성 → 이미 C가 검증한 에피소드 무효화 | ⚠️ 낮음 | 이미 확정된 에피소드는 영향 없음, 다음 에피소드부터 새 blueprint 사용 |

**결론: C+B 교차 충돌은 없음. 단 B 자체의 위험 완화가 필요.**

---

## 4. B(역류) 위험 완화 조건

### 필수 (구현하지 않으면 위험)

1. **cumulative_bible 캐시 무효화**
   - Arc/Blueprint 재생성 시 `db._cumulative_bible_cache.clear()` 호출
   - 위치: stage2_finalizer.py Arc 저장 직후, stage3_orchestrator.py Blueprint 저장 직후

2. **사용자 확인 게이트**
   - `escalation_target = "stage2_arc"` 시 자동 실행 금지
   - 반드시 사용자에게 "Arc를 재생성합니까?" 확인
   - 위치: stage4_orchestrator.py REJECT 처리 분기

3. **에스컬레이션 횟수 제한**
   - 같은 에피소드에서 상류 에스컬레이션 최대 1회
   - 2번째 LOGIC_ERROR → "수동 개입 필요" 안내
   - 위치: stage4_orchestrator.py 라운드 카운터 옆

4. **이미 확정된 에피소드 보호**
   - Arc 재생성 시 이미 manuscript PASS된 에피소드는 건드리지 않음
   - 새 Arc는 미작성 에피소드부터 적용
   - 위치: stage2_orchestrator.py 재생성 범위 제한

### 권장 (안전망)

5. **feature flag 기본 OFF**
   ```yaml
   feature_flags:
     enable_state_text_verifier: true   # C는 바로 켜도 안전
     enable_upstream_escalation: false   # B는 기본 OFF, 수동 활성화
   ```

6. **에스컬레이션 로그**
   - 모든 에스컬레이션을 DB에 기록 (ep_num, reason, target, result)
   - 디버깅 + 패턴 분석용

---

## 5. 구현 안전도 등급

| 기능 | 안전도 | 조건 |
|------|:---:|------|
| **C+LLM (State-Text Verifier)** | 🟢 안전 | feature flag만 추가하면 바로 적용 가능 |
| **B (Blueprint 에스컬레이션)** | 🟡 조건부 안전 | 완화조건 1-4 필수, 사용자 확인 게이트 필수 |
| **B (Arc 에스컬레이션)** | 🟠 주의 | 완화조건 전량 + 확정 에피소드 보호 필수, 테스트 충분히 |
| **C + B 동시** | 🟢 안전 | C→B 순서로 구현, 교차 충돌 없음 |

---

## 6. 권장 구현 순서

```
Step 1: C+LLM (State-Text Verifier) — advisory
        파일: stage4_post_processor.py, validation.yaml
        위험: 없음
        테스트: 검증 정확도 + SilentPass 폴백

Step 2: B-Light (Blueprint 에스컬레이션만)
        파일: stage4_orchestrator.py, stage3_orchestrator.py
        위험: 낮음 (캐시 무효화 필수)
        테스트: LOGIC_ERROR 시 S3 재호출 + 기존 에피소드 무영향

Step 3: B-Full (Arc 에스컬레이션, 사용자 확인 게이트)
        파일: stage4_orchestrator.py, stage2_orchestrator.py
        위험: 중간 (확정 에피소드 보호 필수)
        테스트: 카오스 테스트 — Arc 재생성 후 state 정합성

Step 4: C→B 연동 (C가 감지한 불일치를 B의 에스컬레이션 근거로 활용)
        파일: stage4_orchestrator.py
        위험: 없음 (이미 독립 동작 검증 완료 후)
```

---

## 7. 데이터 흐름 — 적용 후 구조

```
Treatment (불변)
    ↓
Stage 2: Arc ←──────────────────── [B] Arc 에스컬레이션 (사용자 확인 필수)
    ↓                                      ↑
Stage 3: Blueprint ←────────────── [B] Blueprint 에스컬레이션 (자동, 1회 제한)
    ↓                                      ↑
Stage 4: Manuscript ──→ Director ──→ REJECT 원인 분석
    ↓ PASS                            ├─ QUALITY_ISSUE → S4 재시도
    ↓                                 └─ LOGIC_ERROR → 상류 에스컬레이션
[C] State-Text Verifier
    ├─ 일치 → SSOT 확정
    └─ 불일치 → advisory 경고 (다음 라운드 Director에게 전달)
```

---

## 8. "확정된 잘못된 역사" 문제 결론

| 시나리오 | C+LLM으로 해결되는가 | B로 해결되는가 |
|----------|:---:|:---:|
| Writer가 state_changes에 잘못된 수치 → SSOT 오염 | ✅ | — |
| Arc가 Treatment 의도 이탈 → 전체 방향 틀어짐 | — | ✅ (Arc 재생성) |
| Blueprint가 Arc 범위 초과 → 구현 불가능한 씬 | — | ✅ (BP 재생성) |
| 원고가 Blueprint 무시 → Director가 잡음 | 기존 동작 | 기존 동작 |
| 이미 20화 확정 후 1화의 오류 발견 | ❌ 소급 불가 | ❌ 소급 불가 |

**마지막 행이 핵심**: 이미 확정된 역사는 C/B 어느 쪽으로도 소급 수정 불가.
이건 **에피소드 롤백**(project_manager.auto_backtrack_v35)으로만 해결 가능하며, 그것도 사용자 판단 영역.

---

## 부록: 관련 파일 맵

| 파일 | C 수정 | B 수정 |
|------|:---:|:---:|
| `modules/core/stage4_post_processor.py` | ✅ 검증 게이트 삽입 | — |
| `modules/core/stage4_orchestrator.py` | — | ✅ 에스컬레이션 분기 |
| `modules/core/stage3_orchestrator.py` | — | ✅ 단일 EP 재생성 호출 |
| `modules/core/stage2_orchestrator.py` | — | ✅ (Step 3) Arc 재생성 |
| `modules/core/db_manager.py` | — | ✅ 캐시 무효화 메서드 |
| `modules/domain/agents/director_auditor.py` | — | ✅ error_category 구조화 |
| `config/settings/validation.yaml` | ✅ feature flag | ✅ feature flag |
| `config/prompts/director.yaml` | — | ✅ escalation_target 출력 추가 |

---

## 9. [2차 심층 감리] 핵심 신규 발견사항

### 9.1 state_changes의 진짜 문제: 3중 추출, 무동기화

현재 state_changes를 추출하는 주체가 **3개**이며, 서로 동기화되지 않음:

| 추출자 | 필드 수 | 원고 직접 읽음? | SSOT에 쓰이는가 |
|--------|:---:|:---:|:---:|
| **Chief Writer** | 8개 (최소) | ❌ (프롬프트 출력의 일부) | ✅ Director가 "그대로 복사" |
| **Director** | 0개 (복사만) | ❌ (CW 결과 패스스루) | ✅ → HUD, WorldState, FactLedger |
| **Manager** | 30+개 (종합) | ✅ (원고 직접 분석) | ✅ → bible_delta → FactLedger |

```
Chief Writer: {"realm": "화경", "wealth": "30억"} ← 8필드, 불완전
    ↓ 그대로 복사
Director: {"realm": "화경", "wealth": "30억"} ← 검증 없이 통과
    ↓
SSOT: WorldState = "30억", HUD = "30억"

동시에:

Manager: {"actual_truth": {"wealth": "45억", "realm": "화경", ...}} ← 원고 직접 분석, 30+필드
    ↓
SSOT: bible_delta → FactLedger = "45억"

결과: WorldState="30억" vs FactLedger="45억" (충돌!)
```

**Director 프롬프트** (director.yaml L158):
```yaml
"state_updates": {{선택된 원고의 state_updates를 그대로 복사}},
```
Director는 **재추출하지 않고 CW 출력을 복사**할 뿐.

### 9.2 C+LLM 설계 수정 — 검증 대상 재정의

**기존 계획**: Director의 state_updates vs 원고 텍스트 대조
**수정된 계획**: **Manager의 종합 추출 결과** vs 원고 텍스트 대조

이유:
- CW의 8필드는 너무 빈약해서 "불일치"를 감지해도 의미 없음
- Manager가 30+필드를 원고 직독으로 추출 → 이것이 실질적 진실 원천
- Manager 결과가 bible_delta로 FactLedger에 확정되므로, 이것을 검증해야 함

**수정된 삽입 위치**: Manager 추출 완료 후(L413-424), bible_delta 저장 전(L552)

```
Manager 추출 완료 (L424)
    ↓
[V75 State-Text Verifier] Manager 결과 vs 원고 텍스트 대조
    ├─ 일치 → 그대로 진행
    └─ 불일치 → advisory 경고 + 불일치 필드를 원고 기준으로 보정 제안
    ↓
bible_delta 저장 (L552)
    ↓
FactLedger + WorldState 업데이트 (L614-658)
```

### 9.3 genre_ext 값은 전부 문자열 — 숫자 비교 불가

실제 데이터 (골든루트 60블록):
```json
"capital_before": "20억",                          // 숫자 아님, 문자열
"capital_after": "23억 (미실현 수익 포함)",          // 부가 설명 포함
"risk_level": "중위험 (15억 전액 손실 가능)"         // 의미론적 표현
```

**의미**: Python regex로 `capital_before`에서 "20억"을 추출해도, 원고에서 "이십억", "20억 원", "자본금이 스무 억" 등 다양한 표현과 매칭 불가.

**결론**: **LLM 검증이 필수.** Python은 후보 추출(숫자 패턴)만, 의미 비교는 LLM.

### 9.4 error_category가 이미 존재 — B 구현이 예상보다 쉬움

Director 출력 스키마에 이미 있음 (`response_schemas.py`):
```python
"error_category": Schema(type=STRING, enum=["QUALITY_ISSUE", "LOGIC_ERROR"])
```

`main_a.py` L416-431에서 이미 키워드 기반 분류:
```python
if "인과" in reason: error_category = "LOGIC_ERROR"
elif "분량" in reason: error_category = "QUALITY_ISSUE"
```

**B에 필요한 추가**: `escalation_target` 필드만 Director 스키마에 추가하면 됨.
기존 `error_category` 인프라 100% 재활용 가능.

### 9.5 Stage 3 단일 EP 재생성은 독립 호출 가능

`_process_single_episode(working_ep, target_ep, prev_blueprints, success, fail)`:
- Arc 데이터만 있으면 독립 호출 가능
- 이전 EP의 blueprint 필요 (순차 의존)
- DB에 직접 저장 (blueprints 테이블, per-ep row)
- **현재 EP의 blueprint만 교체**, 다른 EP 영향 없음

### 9.6 auto_backtrack_v35() 롤백 메커니즘 확인

| 대상 | 롤백 방식 |
|------|----------|
| manuscripts | ep ≥ target_ep 삭제 |
| blueprints | ep ≥ target_ep 삭제 |
| VecMemory | ep ≥ target_ep 삭제 |
| WorldState | episode_bibles 리플레이 (ep < target_ep까지) |
| FactLedger | episode_bibles 리플레이 (ep < target_ep까지) |

**B-Light에서 활용**: Blueprint 재생성 전, 해당 EP만 선택적 롤백 가능.
**단, "단일 EP" 롤백은 없음** — "from ep N onward" 모델.

---

## 10. [2차 감리] 수정된 위험 평가

### C+LLM 위험 (수정 없음 → 여전히 🟢)

추가 발견 사항은 삽입 위치만 변경 (L210→L424 이후). 위험 등급 동일.

### B 위험 (하향 조정 → 🟡에서 부분 🟢로)

| 항목 | 1차 평가 | 2차 평가 | 이유 |
|------|:---:|:---:|------|
| error_category 파싱 | 신규 구현 필요 | ✅ 이미 존재 | response_schemas.py + main_a.py |
| S3 단일 EP 재호출 | 불확실 | ✅ 가능 | _process_single_episode() 독립 호출 확인 |
| Director 피드백 번역 | S4→S3 변환 필요 | ⚠️ 여전히 필요 | S4 피드백은 원고 중심, S3는 구조 중심 |
| 캐시 무효화 | 필수 | 필수 | 변경 없음 |
| 확정 EP 보호 | 필수 | 필수 | 변경 없음 |

### 수정된 안전도 등급

| 기능 | 안전도 | 변경 |
|------|:---:|------|
| **C+LLM** | 🟢 안전 | 변경 없음 |
| **B-Light (BP만)** | 🟢→🟡 | error_category 이미 존재하므로 약간 상향 |
| **B-Full (Arc까지)** | 🟠 주의 | 변경 없음 — 확정 EP 보호가 핵심 위험 |

---

## 11. [2차 감리] 수정된 구현 계획

```
Step 1: C+LLM (State-Text Verifier) — advisory
        삽입: Manager 추출 완료 후 (L424), bible_delta 저장 전 (L552)
        대상: Manager의 종합 추출 결과 vs 원고 텍스트
        LLM: Gemini Flash 1회 (~$0.001)
        패턴: TruthGate advisory
        파일: stage4_post_processor.py, validation.yaml
        위험: 없음

Step 2: B-Light (Blueprint 에스컬레이션)
        조건: Director REJECT + error_category="LOGIC_ERROR" + 3라운드 연속 실패
        동작: 현재 EP의 blueprint만 재생성 (S3 _process_single_episode)
        필수: cumulative_bible 캐시 무효화
        파일: stage4_orchestrator.py, stage3_orchestrator.py, validation.yaml
        위험: 낮음 (캐시 무효화만 하면 OK)

Step 3: B-Full (Arc 에스컬레이션)
        조건: B-Light 실패 + 사용자 확인
        동작: 미작성 EP 범위에서만 Arc 재생성
        필수: 확정 EP 보호 + 사용자 게이트
        파일: stage4_orchestrator.py, stage2_orchestrator.py
        위험: 중간 (충분한 테스트 후)

Step 4: C→B 연동
        동작: C가 감지한 불일치 유형을 B의 escalation_target 판단에 활용
        위험: 없음
```

---

## 12. 미결 질문 (구현 전 결정 필요)

1. **C의 불일치 시 행동**: advisory 경고만? 아니면 Director에게 재심사 요청?
   - advisory만: 안전, 단 오류가 SSOT에 확정됨
   - 재심사: 안전, 단 1라운드 추가 (비용 ~$0.01)

2. **B-Light 트리거 조건**: LOGIC_ERROR 1회? 2회? 3회 연속?
   - 1회: 민감, 불필요한 재생성 위험
   - 3회: 보수적, 하지만 5라운드 중 3회면 늦을 수 있음
   - 권장: 2회 연속 LOGIC_ERROR

3. **B-Full 자동 vs 수동**: Arc 에스컬레이션을 자동으로 제안만? 실행까지?
   - 권장: "제안 + 사용자 확인" (자동 실행 금지)

4. **Manager vs Director state_changes 충돌 해소**: 누가 이기는가?
   - 현재: 마지막 쓰기가 이김 (FactLedger)
   - 권장: Manager 우선 (원고 직독이므로 더 정확)

---

## 13. [3차 정밀 감사] 안전성 최종 검증

### 13.1 C의 타이밍 문제 — "Post-PASS only"

**발견**: C는 Director PASS 후에 실행됨 → 현재 에피소드의 판정에 영향 불가.

```
Director PASS (판정 완료)
    ↓
CoVe 사후검증 (PASS→REJECT 가능) ← 여기서 걸리면 C는 실행 안 됨
    ↓
Post-Processor 시작
    ↓ L199: 원고 DB 저장
    ↓ L213: HUD 업데이트
    ↓ L306: TruthGate advisory (Python only, LLM 없음)
    ↓ L280: Manager 비동기 추출 시작
    ↓ L413: Manager 결과 수집
    ↓ L524: ★ C 삽입 지점 ★
    ↓ L528: bible_delta 조립
    ↓ L552: bible_delta DB 저장
    ↓ L625: WorldState 갱신
    ↓ L646: FactLedger 갱신
```

**의미**:
- C의 경고는 **현재 에피소드를 되돌리지 않음** (이미 원고 저장됨)
- C의 경고는 **다음 에피소드 Director 프롬프트에 주입 가능**
- 또는: **bible_delta 조립 전에 불일치 필드를 보정하여 SSOT 오염 방지**

**결정**: C가 불일치 발견 시 2가지 행동:
1. advisory 경고 로그 (다음 EP 참고용)
2. **bible_delta에서 불일치 필드를 원고 텍스트 기준으로 보정** ← 이게 핵심 가치

### 13.2 C의 Manager 실패 시 동작

Manager 추출 실패 경로 (L434-453):
```
Manager async 실패 → sync 재시도 → 재시도도 실패
    → bible_delta = None
    → L534 fallback: state_changes = final_state_updates (Director 복사본)
```

**C의 동작**:
- Manager 성공 시: Manager의 `actual_truth` vs 원고 대조
- Manager 실패 시: Director의 `final_state_updates` vs 원고 대조 (fallback)
- 둘 다 실패 시: SilentPass (건너뜀)

### 13.3 B-Light의 3대 블로커 (신규 발견)

| # | 블로커 | 설명 | 해결 방법 |
|---|--------|------|----------|
| **B1** | Blueprint가 라운드 루프 밖에서 1회만 로드됨 (L335) | 재생성 후에도 이전 blueprint 참조 | 재생성 후 명시적 reload 필요 |
| **B2** | Stage4Context에 Stage3 필수 콜백 3개 누락 | `get_arc_context_for_episode` 등 | self.app에서 Stage3Context 신규 생성 |
| **B3** | patch_mode가 blueprint 변경을 인지 못함 | 재생성 후 patch → 잘못된 blueprint 대상 수술 | blueprint 변경 시 patch_mode 강제 OFF |

### 13.4 B-Light 무한 루프 방지

```
Round 0: LOGIC_ERROR ← streak = 1
Round 1: LOGIC_ERROR ← streak = 2 → B-Light 발동
    → Blueprint 재생성
    → 재생성 실패 → 원래 blueprint로 복귀, streak 리셋
    → 재생성 성공 → 새 blueprint로 Round 2 진행
Round 2: LOGIC_ERROR ← streak = 1 (리셋됨)
Round 3: LOGIC_ERROR ← streak = 2 → B-Light 재발동?

문제: 에피소드당 2번 재생성 → 비용 폭증 + 무의미한 반복
```

**해결**: `_escalation_used = False` 플래그 → **에피소드당 최대 1회** 에스컬레이션

### 13.5 CoVe와의 상호작용 — 안전

```
CoVe REJECT (PASS→REJECT 전환) → Post-Processor 실행 안 됨 → C 실행 안 됨 ✅
CoVe PASS → Post-Processor 실행 → C 실행 ✅
```
C와 CoVe는 **순차 실행**, 충돌 없음.

### 13.6 WorldState vs FactLedger 비대칭 — Manager 우선의 실제 의미

현재 쓰기 순서:
```
WorldState  ← final_state_updates (Director 8필드 복사)
FactLedger  ← final_state_updates (Director) + bible_delta (Manager 30+필드)
```

**Manager 우선으로 바꾸려면**:
- WorldState도 Manager의 `actual_truth`로 갱신해야 함
- 현재 L625 `update_from_state_changes(final_state_updates)` →
  `update_from_state_changes(actual_truth or final_state_updates)` 변경 필요
- **1줄 수정**, 하지만 테스트 필요

### 13.7 테스트 영향 분석

| 대상 | 기존 테스트 수 | 영향 |
|------|:---:|------|
| stage4_post_processor | 93+ | C 삽입 시 기존 테스트 영향 0 (feature flag OFF 시) |
| stage4_orchestrator | 다수 | B-Light 삽입 시 기존 테스트 영향 0 (flag OFF 시) |
| stage3_orchestrator | 다수 | B-Light에서 _process_single_episode 호출 시 기존 테스트 영향 0 |

---

## 14. [3차 감사] 최종 안전도 등급 — 변경 없음

| 기능 | 등급 | 3차 감사 결과 |
|------|:---:|------|
| **C+LLM** | 🟢 안전 | 삽입 지점 L524 안전 확인, Manager 실패 fallback 확인, CoVe 순차 확인 |
| **B-Light** | 🟡 조건부 안전 | 블로커 3건 해결 필요 (B1~B3), 무한루프 방지 필수, 하지만 구조적 불가능은 아님 |
| **B-Full** | 🟠 주의 | 변경 없음 |
| **동시 적용** | 🟢 안전 | C→B 순서, 교차 의존 없음 확인 |

---

## 15. C의 보정 동작 상세 설계

C가 불일치 발견 시 **bible_delta 조립 전에 보정**:

```python
# L524 삽입 (bible_delta 조립 전)
if _threshold("feature_flags.enable_state_text_verifier", True):
    try:
        _verify_src = actual_truth if actual_truth else final_state_updates
        _c_result = _state_text_verifier.verify(final_manuscript, _verify_src)

        if not _c_result["passed"]:
            for _issue in _c_result["issues"]:
                logging.warning("[V75:StateText] %s", _issue["summary"])
                self.ctx.ui.log(f"   ⚠️ [StateText] {_issue['summary']}")

            # bible_delta에 반영할 보정값이 있으면 적용
            _corrections = _c_result.get("corrections", {})
            if _corrections and actual_truth:
                for _key, _corrected_val in _corrections.items():
                    actual_truth[_key] = _corrected_val
                    logging.info("[V75] actual_truth[%s] 보정: %s", _key, _corrected_val)
    except Exception as _c_err:
        logging.debug("[SilentPass:V75:StateText] %s", _c_err)
```

**핵심**: advisory + 보정. bible_delta가 원고와 일치하는 값으로 확정됨.
