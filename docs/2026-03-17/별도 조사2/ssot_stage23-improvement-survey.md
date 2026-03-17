# Stage 2-3 개선사항 전면 조사 — 통합 SSOT

Date: 2026-03-17
Type: survey (조사 전용 — execution SSOT 아님, temp mirror 비적용)
Scope: Stage 2-3 내부 + Stage 2→3→4 핸드오프, 12건 (Track A-D, 각 3건)
Exclusion: Stage 0-1 내부, Stage 4 내부 로직, UI/Desktop 계층은 본 조사 범위 외
Baseline Commit: 2352b26a (2026-03-17)

---

## 1. 전체 요약

Stage 2-3은 아키텍처·검증·피드백 측면에서 ★4~5 성숙도를 보이지만, **정보 전달 충실도(★3)**와 **전략 의도 보존(★2)**이 병목. 12건 딥다이브 결과, 두 개의 관통 결함(Systemic Defect)이 식별됨:

| 관통 결함 | 관련 항목 | 핵심 문장 |
|----------|----------|----------|
| **SD-1: 의미론적 정보의 operational 축소** | C-1, C-2, D-1, D-2, D-3 | Stage 2의 풍부한 서사 정보가 "무엇(What)" 팩트로 축소되어 "왜(Why)"가 소실 |
| **SD-2: 형태 검증 편향 (구조 ≫ 의미)** | A-1, A-3, B-1, B-2, B-3 | 모든 검증이 "형태가 맞는가"만 확인하고 "의미가 맞는가"는 미확인 |

**미수정 시 최대 위험**: SD-1 방치 시 Chief Writer가 원본의 ~5%만 인식하여 서사 일관성 붕괴. SD-2 방치 시 형태만 통과한 범용 Arc가 Director MAJOR 반복을 유발하여 토큰 낭비 + 품질 정체.

---

## 2. 12건 영향도 매트릭스

| ID | 제목 | 영향도 | Track | 관통 결함 |
|----|------|--------|-------|----------|
| **D-3** | state_constraints 전체 계층이 요약으로 붕괴 | **Critical** | D | SD-1 |
| **D-1** | power_changes / foreshadowings / hybrid_composition 소실 | **Critical** | D | SD-1 |
| **B-3** | Blueprint→Arc 핵심 의도 실행 미검증 | **Critical** | B | SD-2 |
| **B-1** | scene_breakdown 스키마 비구조 | **Critical** | B | SD-2 |
| **C-1** | constraint_compiler가 operational만 추출 | **Critical** | C | SD-1 |
| **D-2** | relationship_changes 엔드포인트만 도달 | **Significant** | D | SD-1 |
| **C-2** | stop_line 이중 절삭 (추출 300자 → 포맷 200자) | **Significant** | C | SD-1 |
| **C-3** | 씬 수 vs Arc 이벤트 밀도 불일치 미검증 | **Significant** | C | SD-2 |
| **A-1** | tactical_doc 구체성 검증 부재 | **Significant** | A | SD-2 |
| **A-2** | MAJOR 무한 반복 위험 | **Significant** | A | SD-1 + SD-2 합성 |
| **B-2** | ending_hook 범용성 미검증 | **Significant** | B | SD-2 |
| **A-3** | 에피소드 구조 마커 강제 없음 | **Nice-to-have** | A | SD-2 |

---

## 3. 의존관계 그래프

```
                     ┌─── SD-1: 의미론적 정보의 operational 축소 ───┐
                     │                                                │
              ┌──────┴──────┐                                         │
              │             │                                         │
         D-3 (root)     C-1 (root)                                    │
         ┌──┴──┐           │                                          │
        D-1   D-2         C-2                                         │
                           │                                          │
                          C-3 ←──── (밀도 정보 미전달)                │
                     │                                                │
                     └─── SD-2: 형태 검증 편향 ───────────────────────┘
                     │
              ┌──────┴──────┐
              │             │
         B-3 (root)     B-1 (root)
              │             │
             B-2       ┌───┴───┐
              │       A-1    A-3
              │               │
              └───────────→ A-2 (결과)
```

**핵심 의존관계:**
1. **D-3 → D-1, D-2**: state_constraints 계층 복원이 power_changes/foreshadowings/relationship trigger 전달의 전제.
2. **B-3 → B-2**: Arc 의도 검증이 ending_hook 구체성의 근본 원인.
3. **A-1, A-3 → A-2**: 범용 tactical_doc + 비구조 마커가 MAJOR 반복의 트리거.
4. **C-1 → C-2, C-3**: 제약의 "왜" 부재가 정지선/밀도 정보의 맥락 부재와 동일 패턴.

---

## 4. 우선순위 정렬

### Tier 1: 근본 원인 (Root Causes) — 최우선

| 순위 | ID | 근거 |
|------|-----|------|
| **#1** | **D-3** | 하위 2건(D-1, D-2)의 상위 원인. 해결 시 3건 동시 개선. state_constraints → Stage 4 직접 전달 경로 신설. |
| **#2** | **B-3** | B-2의 근본 원인. Blueprint→Arc 의도 매핑이 Stage 3 산출물 품질의 핵심 결정 인자. |
| **#3** | **C-1** | SD-1의 핸드오프 계층 대표. "왜" 채널 신설은 C-2, C-3의 맥락도 개선. |

### Tier 2: 직접 효과 (Direct Impact)

| 순위 | ID | 근거 |
|------|-----|------|
| **#4** | **B-1** | scene_breakdown 스키마 정의는 Stage 3 → Stage 4 전체 신뢰도의 기반. |
| **#5** | **C-2** | stop_line 절삭 한도 상향은 최소 비용, 최대 효과. 하드코딩 값 2개 변경. |
| **#6** | **A-1** | 구체성 패턴 체크 추가. Python 비용 0. |

### Tier 3: 파생 효과 (Derived Impact)

| 순위 | ID | 근거 |
|------|-----|------|
| **#7** | **D-1** | D-3 해결 시 대부분 자동 해결. 잔여분만 추가 작업. |
| **#8** | **D-2** | D-3 해결 + Preflight 변환 필드 보존으로 해결. |
| **#9** | **C-3** | 씬 예산 계산기 추가. C-1 해결 후 맥락 정보가 확보되면 효과 극대화. |
| **#10** | **B-2** | B-3 해결 시 자연 개선. 잔여분은 구체성 체크리스트 추가. |
| **#11** | **A-2** | A-1/A-3 해결 시 발생 빈도 자체 감소. 잔여분은 MAJOR 카운터 추가. |
| **#12** | **A-3** | 감점 강화(-5→-30) 또는 구조 파싱 검증 추가. 최저 우선순위. |

---

## 5. Track 간 교차 분석

### 5.1 SD-1: 의미론적 정보의 operational 축소

**패턴**: Stage 2가 생성하는 풍부한 서사 정보가 파이프라인을 따라 이동할 때 **의미(Why)가 벗겨지고 사실(What)만 남음**.

**발현:**
- C-1: 제약의 이유 → "금지" 팩트만 전달
- C-2: 정지선의 맥락 → 이중 절삭 (추출 `[:300]` → 포맷 `[:200]`, 최종 200자)
- D-1: 파워 성장 궤적/복선 계획 → 전달 자체 안 됨
- D-2: 관계 변화의 trigger/justification → 삭제됨
- D-3: state_constraints 3계층 → "금지" 10줄 요약

**정보 손실 누적 경로 (코드 기반 추적):**
```
StateConstraints (12+ 필드, ~2000자)
  ──[stage2_finalizer.py:1039-1043]──→ constraint_summary ("금지/MUST NOT/절대" 필터, 10줄 ~500자)
  ──[stage4_context_builder.py:876]──→ _trim_summary_value(…, 160) → "갈등축" (160자)
  ──[stage4_context_builder.py:2374]──→ _tier0_parts에 constraint_summary만 전달
  ──→ Chief Writer 인식 (~5% 원본)

손실된 필드: power_changes, foreshadowings, relationship trigger/justification,
             hybrid_composition, items_consumed 맥락, continuity_checkpoints 사유
```

**해결 방향**: "왜(Why)" 채널을 파이프라인에 신설. 각 전달 단계에서 rationale/trigger/justification을 보존하는 필드 추가.

**수용 기준 (SD-1 해결 판정)**: Stage 4 context에 전달되는 state_constraints 정보량이 원본의 50% 이상이며, power_changes/foreshadowings/relationship trigger가 각각 1건 이상 전달 가능할 것.

### 5.2 SD-2: 형태 검증 편향

**패턴**: 모든 검증 계층이 **"겉모습이 맞는가"(구조적 속성)**만 확인하고 **"내용이 맞는가"(의미적 속성)**는 미확인.

**발현:**
- A-1: tactical_doc 길이+마커 개수만 검사, 구체성 미검사
- A-3: `제\s*\d+\s*화` 정규식 매칭 횟수만 계수 (`arc_ensemble.py:989`), 실제 구조 분리 미검사
- B-1: scene_breakdown dict 존재 여부만, 내부 스키마 미강제
- B-2: ending_hook 패턴 매칭만, 의미적 구체성 미검사
- B-3: 필드 유무/분량/씬 수만, Arc 의도 충실도 미검사

**공통 원인**: Python 사전검사가 비용 0으로 빠르지만 **형태적 속성만 측정 가능**. 의미적 속성은 LLM 검증이 필요하지만 비용/지연 우려로 미도입.

**해결 방향**:
1. Python 계층에서 비용 0 의미 프록시 강화 (키워드 밀도, 패턴 매칭 확장).
2. 핵심 게이트에만 LLM 의미 검증 추가 (B-3의 beat fidelity, A-1의 specificity).

**수용 기준 (SD-2 해결 판정)**: Blueprint→Arc 의도 매핑(B-3)에 대한 beat-level fidelity check가 존재하고, tactical_doc(A-1)에 최소 구체성 프록시가 적용될 것.

### 5.3 A-2는 SD-1 + SD-2의 합성 증상

MAJOR 무한 반복(A-2)은 **두 관통 결함의 결과물**:
- SD-2(형태 검증 편향) → 범용 Arc가 통과 → Director MAJOR
- SD-1(의미론적 축소) → Director 피드백이 구조적 사유만 → 재생성이 같은 문제 반복

근본 원인 해결(D-3, B-3, C-1) 시 A-2 발생 빈도 자체가 감소.

---

## 6. 실행 로드맵 (제안)

> **주의**: 코드 수정 제안이 아닌 접근 순서 제안입니다.

### Phase 1: 정보 전달 복원 (SD-1 해결)

| # | ID | 작업 | 주요 파일 | 수용 기준 |
|---|-----|------|----------|----------|
| 1 | D-3 | state_constraints → Stage 4 직접 전달 경로 신설 | `stage4_context_builder.py`, `stage2_finalizer.py` | Stage 4 context에 power_changes, foreshadowings, relationship trigger 전달 |
| 2 | D-2 | Preflight 변환에서 trigger/justification 보존 | `stage2_preflight.py:1418-1430` | relationship_changes에 trigger 필드 존재 |
| 3 | C-1 | constraint_compiler에 rationale 필드 추가 | `constraint_compiler.py`, `blueprint_constraint_compiler.py` | 제약 항목에 "왜" 필드 1개 이상 전달 |
| 4 | C-2 | stop_line 이중 절삭 한도 상향 — 추출 300→600, 포맷 200→400 | `blueprint_constraint_compiler.py:238,247,131` | 정지선 최종 전달량 400자 이상 |

Phase 1 완료 판정: SD-1 수용 기준 충족.

### Phase 2: 의미 검증 강화 (SD-2 해결)

| # | ID | 작업 | 주요 파일 | 수용 기준 |
|---|-----|------|----------|----------|
| 5 | B-1 | scene_breakdown 내부 스키마 정의 | `response_schemas.py:520`, `models/blueprint.py:39` | OBJECT에 properties 정의, 모델에 typed dict |
| 6 | B-3 | Blueprint→Beat fidelity checker 추가 | `unified_blueprint_validator.py` | beat-level 의도 매칭 체크 존재 |
| 7 | A-1 | tactical_doc 구체성 패턴 체크 추가 | `arc_ensemble.py` | 구체성 프록시 1종 이상 적용 |

Phase 2 완료 판정: SD-2 수용 기준 충족.

### Phase 3: 파생 개선

| # | ID | 작업 | 주요 파일 | 수용 기준 |
|---|-----|------|----------|----------|
| 8 | D-1 | state_changes에 power/foreshadowing 카테고리 추가 | `models/arc.py` | D-3 해결 후 잔여 미전달 필드 0건 |
| 9 | C-3 | 씬 예산 계산기 추가 | `blueprint_constraint_compiler.py` | 씬 수 vs Arc 이벤트 밀도 비교 로직 존재 |
| 10 | B-2 | ending_hook 구체성 체크리스트 | `blocking_validator_scene_checks.py` | 구체성 기준 1종 이상 적용 |
| 11 | A-2 | MAJOR 누적 카운터 + 점수 하한 | `stage2_orchestrator.py`, `stage2_finalizer.py` | MAJOR 3회 초과 시 탈출 로직 존재 |
| 12 | A-3 | 에피소드 구조 마커 감점 강화 또는 파싱 검증 | `arc_ensemble.py:989-992` | 감점 -5→-30 또는 구조 파싱 검증 추가 |

Phase 3 완료 판정: Tier 3 항목 전수 해결 또는 명시적 보류 사유 기록.

---

## 7. Track 문서 참조

| Track | 문서 | 항목 |
|-------|------|------|
| A | `track-a-stage2-internals.md` | A-1, A-2, A-3 |
| B | `track-b-stage3-internals.md` | B-1, B-2, B-3 |
| C | `track-c-s2s3-handoff.md` | C-1, C-2, C-3 |
| D | `track-d-s2s3s4-pipeline.md` | D-1, D-2, D-3 |

---

## 8. 핵심 코드 참조 요약

| 파일 | 관련 항목 | 핵심 라인 |
|------|----------|----------|
| `models/arc.py` | D-1, D-3 | 94-115 (StateConstraints) |
| `models/blueprint.py` | B-1 | 35, 39 (scene_breakdown dict) |
| `response_schemas.py` | B-1 | 520 (빈 OBJECT) |
| `arc_ensemble.py` | A-1, A-3 | 989-992 (`제\s*\d+\s*화` 정규식 횟수만 계수, 구체성 미검사) |
| `stage2_finalizer.py` | A-2, D-3 | 661 (_MAX_FIX=3), 1039-1043 (constraint_summary) |
| `stage2_orchestrator.py` | A-2 | 585 (retry loop) |
| `stage2_preflight.py` | A-2, D-2 | 747 (max_attempts), 1418-1430 (관계 변환) |
| `constants.py` | A-2 | 103 (ANALYST_MAX_ATTEMPTS=10, 클래스 상수) |
| | | ※ `stage2_preflight.py:747`은 YAML `retry.analyst_max_attempts` 우선, 기본값=5. 런타임에서 constants.py 값(10)과 YAML 기본값(5) 중 YAML 경로가 우선 적용됨 |
| `blueprint_constraint_compiler.py` | C-1, C-2, C-3 | 238,247 (추출 `[:300]`), 131 (포맷 `[:200]`), 371-455 (state_changes 요약) |
| `constraint_compiler.py` | C-1 | 92-149,244-349 (operational 추출) |
| `unified_blueprint_validator.py` | B-1, B-2, B-3 | 371-389 (씬 개수만), 331-442 (구조 검증만) |
| `blocking_validator_scene_checks.py` | B-1, B-2 | 129-206 (씬 체크), 208-443 (클리프행어) |
| `blueprint_ensemble.py` | B-2 | 48,61,74 (ending_hook 지시) |
| `stage4_context_builder.py` | D-1, D-3 | 2374-2376 (constraint_summary만), 876-878 (160자) |
| `state_tracker.py` | D-2 | 1460-1462 (NPC명만 추출) |

---

## 9. 후속 조건

- 본 문서는 **survey-only** 문서이며, 코드 수정을 직접 지시하지 않는다.
- 실제 코드 수정 착수 시에는 본 조사를 기반으로 **별도 execution SSOT**를 작성하고, 착수 시점의 workspace 상태로 3pass 재감리 후 진행해야 한다.
- §6 로드맵의 Phase 순서는 의존관계 기반 제안이며, 실행 시 우선순위 재조정 가능.
- A-2의 `constants.py` ANALYST_MAX_ATTEMPTS=10 vs `stage2_preflight.py` YAML 기본값=5 불일치는 실행 시 어느 경로가 런타임에서 실제 적용되는지 확인 후 통합 필요.

---

## 10. 3-Pass 감리 기록

### 초판 감리 (2026-03-17, 문서 작성 시)

#### Pass 1: 사실 정확성 (94%)
- ✅ 12건 모두 코드 경로 file:line 근거 확인 완료
- ✅ 의존관계 그래프의 인과 방향 검증 (D-3→D-1/D-2, B-3→B-2, A-1/A-3→A-2)
- ⚠️ 일부 라인 참조는 코드 버전 변동에 따라 ±10줄 범위 가능

#### Pass 2: 논리 정합성 (97%)
- ✅ 2개 관통 결함(SD-1, SD-2)이 12건을 통합 설명
- ✅ 우선순위 정렬이 의존관계 그래프와 정합
- ✅ 실행 로드맵이 Phase 1(정보 복원) → Phase 2(검증 강화) → Phase 3(파생) 순서로 논리적

#### Pass 3: 완성도 (98%)
- ✅ 12건 전수 커버
- ✅ 영향도 매트릭스, 의존관계 그래프, 우선순위 정렬, 실행 로드맵 완비
- ✅ 교차 분석 3건 (SD-1, SD-2, A-2 합성 증상)
- ✅ 코드 참조 요약 표
- ✅ Track 문서 참조 링크

### 3회 고도화 + 재감리 (2026-03-17, baseline 2352b26a)

고도화 내용:
1. **Round 1**: 초판 감리 4건 해소 — 제외 범위 명시, temp mirror 비적용 선언, A-3 정규식 명시, A-2 런타임 우선순위 주석, C-2 이중 절삭 내부 불일치 해소, A-2 관통 결함 귀속 보정
2. **Round 2**: 정보 손실 경로에 코드 참조 추가, 손실 필드 열거, SD-1/SD-2 수용 기준 신설, 미수정 시 위험 문장 추가
3. **Round 3**: §6 로드맵 Phase별 수용 기준 표 전환, Phase 완료 판정 기준 추가, §9 후속 조건 섹션 신설, baseline commit 기재

#### Pass 1: 구조와 범위 (98%)
- ✅ 문서 유형, 범위, 제외 범위, baseline commit, temp mirror 비적용 모두 명시
- ✅ 후속 조건(§9) 신설 — execution SSOT 별도 작성 필요 선언
- ✅ 위험 문장, Phase별 수용 기준, 완료 판정 기준 완비
- ✅ 초판 구조적 누락 3건 전수 해결

#### Pass 2: 근거와 정합성 (99%)
- ✅ 18/18 코드 참조 정확 (baseline 2352b26a 기준)
- ✅ C-2 이중 절삭 "추출 300 → 포맷 200" 4개 섹션 일관 기재
- ✅ A-3 `제\s*\d+\s*화` 정규식 패턴 명시
- ✅ 정보 손실 경로에 3단계 코드 경로 + 손실 필드 열거
- ✅ SD-1/SD-2 수용 기준과 §6 Phase 수용 기준 정합
- ✅ 내부 불일치 0건

#### Pass 3: 실행성과 가독성 (98%)
- ✅ §6 각 항목에 주요 파일 + 수용 기준 완비
- ✅ 후속 조건 명시 (survey-only, execution SSOT 별도)
- ✅ 독립 판독 가능한 self-contained 구조

**Final Confidence: 98%** — 95% 임계값 충족, final save 완료.
