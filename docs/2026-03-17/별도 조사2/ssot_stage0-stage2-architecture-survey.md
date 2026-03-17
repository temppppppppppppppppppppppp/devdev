# Stage 0 + Stage 2 아키텍처 성숙도 전면 조사 — 통합 SSOT

Date: 2026-03-17
Scope: Stage 0 (프로젝트 초기화) + Stage 2 (Arc 설계) 전체 아키텍처
Original 3-Pass Audit: 93% → 96% → 97%
Re-Audit (5-Pass): 78% → 85% → 89% → 93% → 95%
Final Confidence: 95%

---

## 1. 조사 배경

기존 Stage 2-3 조사(12건, `ssot_stage23-improvement-survey.md`)에서 개별 이슈를 딥다이브했으나, **Stage 0과 Stage 2의 시스템 수준 성숙도**는 미평가. 이번 조사는:

- **Stage 0**: Bible/Treatment/스타일/프리셋 파이프라인 전체 아키텍처 평가
- **Stage 2**: 11개 검증 게이트 + 패치 모드 + 상태 관리의 시스템 수준 평가 (기존 Track A 개별 이슈와 별도)

---

## 2. Stage 0 아키텍처 현황

### 2.1 모듈 구조

| 모듈 | 파일 | 역할 |
|------|------|------|
| **StageZeroManager** | `stage0/__init__.py` (910줄) | 통합 관리자 — 메뉴 라우팅, 플로우 오케스트레이션 |
| **StoryExpander** | `stage0/story_expander.py` (601줄) | 컨셉 → Bible + Treatment 생성 |
| **ReverseExpander** | `stage0/reverse_expander.py` (1,212줄) | 기존 원고 → Bible/상태/스타일 역추출 |
| **PresetRegistry** | `stage0/preset_registry.py` (739줄) | 장르별 동적 스키마 관리 |
| **StyleExtractor** | `stage0/style_extractor.py` (1,227줄) | 참조 원고에서 문체 DNA 추출 |
| **Stage01Helpers** | `stage01_helpers.py` (926줄) | SovereignApp 브릿지 |

**총 Stage 0 코드**: ~5,615줄

### 2.2 데이터 흐름

```
[입력]                    [Stage 0]                       [출력]
컨셉 텍스트 ──→ StoryExpander ──→ Bible (MasterBible)
                     │              Treatment (60 블록)
                     │              PresetRegistry
                     └──→ _ensure_plot_roadmap() ──→ plot_roadmap
                          (Treatment 기반, __init__.py:451)

기존 원고 ────→ ReverseExpander ──→ Bible
                     │                Episode Bibles
                     │                StyleGuide
                     └──→ _ensure_plot_roadmap() ──→ plot_roadmap
                          (arc stubs 기반, reverse_expander.py:722)

참조 원고 ────→ StyleExtractor ──→ StyleGuide (캐시)
```

> **주의**: `_ensure_plot_roadmap`이 2개 존재한다. 컨셉 경로(`__init__.py`:451)는 Treatment 기반이고, 역설계 경로(`reverse_expander.py`:722)는 `_build_arc_stubs()`에서 독립 생성한다.

### 2.3 Stage 0 성숙도 평가

| 축 | 등급 | 근거 |
|----|------|------|
| **기능 완성도** | ★4 | 7개 메뉴 항목 모두 구현. 컨셉, 역설계, 임포트, 스타일, 프리셋, 작품가드, 블록 확장. |
| **오류 처리** | ★4 | EOFError, 인코딩 오류, LLM 실패 모두 방어. DraftEncodingError 커스텀 예외. 3회 재시도. |
| **검증 강건성** | ★2 | Bible/Treatment 생성 결과의 **내용 품질** 검증 없음. 구조(dict 여부, 키 존재) 수준만. |
| **S0→S2 계약** | ★3 | plot_roadmap 주입 로직 존재. 컨셉 경로는 Treatment 기반, 역설계 경로는 arc stubs 기반으로 독립 생성. |
| **테스트 커버리지** | ★3 | 6개 테스트 파일. 구조/인코딩/EOFError 커버. 생성 품질 테스트 없음. |

---

## 3. Stage 0 개선사항

### S0-1: Bible 생성 품질 검증 부재

**현황**: `story_expander.py`:198-256 — `generate_bible()`:
- 주인공 생성 실패 시 조기 종료 (line 208-211): `"name" not in protagonist → return {}`
- NPC 생성 실패 시 빈 목록 진행 (line 216-219)
- **성공 경로**: 구조 검증만 (dict 여부). 내용 품질 미검증.

**갭**:
- Bible의 `CoreIdentity`(edge/desire/crisis)가 비어있거나 범용적이어도 통과.
- NPC 8명 요청하지만 3명만 생성돼도 통과 (빈 목록만 아니면 OK).
- `WorldLaws`가 빈 리스트여도 통과.

**영향도**: **Significant** — Bible 품질이 Stage 2 Arc 설계의 기반. 빈약한 Bible → 빈약한 Arc.

**방향 스케치**:
- Bible 완성도 체크리스트: `protagonist.name`, `protagonist.core` 4필드, `NPC ≥ 5명`, `WorldLaws ≥ 1개`.
- 미달 시 LLM 재생성 1회 시도 또는 경고 표시.

### S0-2: Treatment 블록 간 연속성 미검증

**현황**: `story_expander.py`:305-313 — `generate_treatment()`:
- `_generate_skeleton()` → `_generate_details()` 2단계 생성.
- **초기 생성 시 블록 간 서사 연속성, 인물 동선 일관성 검증 없음**.

**세부 분석** (재감리에서 확인):
- `_generate_skeleton()` (line 441-476): 20블록 배치 생성. 이전 배치의 **마지막 5개 블록 제목만** 컨텍스트로 전달 (line 451-454). 내용/상태/NPC 정보는 미전달.
- `_generate_details()` (line 478-516): 10블록 배치. **배치 간 컨텍스트 전달 없음**. story_brief와 현재 배치 skeleton만 입력.
- `extend_treatment()` (line 315-390): **이 메서드만** 이전 5블록의 제목+내용 요약을 컨텍스트로 주입. 초기 생성과 확장의 연속성 수준이 비대칭.

**갭**:
- 초기 60블록이 사실상 독립적으로 생성. 블록 15에서 사망한 NPC가 블록 30에 재등장 가능.
- skeleton은 제목만 전달, details는 컨텍스트 제로 → 배치 경계에서 연속성 단절.
- 생성 후 NPC 사망/등장 일관성, 위치 동선, 타임라인 순서의 사후 검증 없음.

**영향도**: **Significant** — plot_roadmap의 품질이 Stage 2 Arc의 원재료.

**방향 스케치**:
- `_generate_details()` 배치 간 이전 배치 요약 주입 (extend_treatment 패턴 적용).
- 생성 후 연속성 스캔 (NPC 사망/등장 일관성, 위치 동선).

### S0-3: 컨셉 경로 plot_roadmap의 Treatment 의존성

**현황**: `__init__.py`:451-466 — `_ensure_plot_roadmap()` (컨셉 경로):
- `_build_plot_roadmap_from_treatment()` 호출 (`stage01_helpers.py`:604-618).
- Treatment가 없으면 plot_roadmap이 빈 리스트 → Stage 2 블록됨.

**역설계 경로는 독립적**: `reverse_expander.py`:722-744의 `_ensure_plot_roadmap()`은 `_build_arc_stubs()`에서 에피소드 분석 기반으로 plot_roadmap을 독립 생성. Treatment 불필요.

**갭**:
- **컨셉 경로 한정**: Treatment 생성 실패 시 빈 roadmap → Stage 2 진입 불가.
- `_build_plot_roadmap_from_treatment`는 Treatment 항목을 `{"block_no": N, ...}` 형태로 flat 변환만 수행. 내용 검증 없음.

**영향도**: **Significant** (~~Critical~~ 하향) — 역설계 경로는 독립 생성이 가능하므로 "전체 파이프라인 중단"은 컨셉 경로에만 해당.

**방향 스케치**:
- 컨셉 경로에서 Treatment 생성 실패 시 fallback (사용자 안내 또는 최소 skeleton 기반 roadmap 빌드).
- `_build_plot_roadmap_from_treatment` 위치 명확화: `stage01_helpers.py`:604-618 (Stage 0 모듈이 아닌 브릿지 헬퍼).

### S0-4: StyleGuide 캐시 무효화 전략 부재

**현황**: `style_extractor.py` — cache_mode: "use"(기본), "refresh", "reset".
- 캐시 TTL(만료 시간) 없음. "use" 모드에서 영구 캐시.
- 참조 원고가 변경돼도 캐시 자동 무효화 없음.

**갭**: 장르 참조 원고가 업데이트되면 수동으로 "refresh" 실행해야 함. 잊으면 오래된 스타일 가이드 사용.

**영향도**: **Nice-to-have** — 참조 원고 변경 빈도 낮음.

**방향 스케치**: 참조 원고 파일 해시 기반 자동 무효화.

### S0-5: POV × external_pov_insert_policy 조합 검증 미비

**현황**: `__init__.py` — 4개 POV × 3개 외부 시점 정책 = 12 조합.
- 모든 조합이 의미적으로 유효한지 미검증. 예: "1인칭" + "적극 허용"은 모순 가능.

**영향도**: **Nice-to-have** — 조합 오류 시 Stage 4 원고 스타일 불일치. 빈도 낮음.

---

## 4. Stage 2 아키텍처 현황

### 4.1 모듈 구조

| 모듈 | 파일 | 줄 수 | 역할 |
|------|------|-------|------|
| **Stage2Orchestrator** | `stage2_orchestrator.py` | 1,057 | 배치 + 순차 Arc 설계 루프 |
| **Stage2Preflight** | `stage2_preflight.py` | 1,671 | 사전 상태 설정, 제약 빌드, 컨텍스트 검색 |
| **Stage2Finalizer** | `stage2_finalizer.py` | 1,773 | Director 심사, 패치 루프, DB 커밋 |
| **Stage2ValidationPipeline** | `stage2_validation_pipeline.py` | 1,195 | 11개 검증 게이트 체인 |
| **Stage2Optimizer** | `stage2_optimizer.py` | 1,213 | 패치 모드, 자동 교정 |
| **Stage2Context** | `stage2_context.py` | 371 | DI 컨텍스트 (56+ 속성/콜백) |
| **Stage2Contracts** | `stage2_contracts.py` | 3 | 검증 임계값 |

**총 Stage 2 코드**: ~7,283줄

### 4.2 11개 검증 게이트

> **TF-25-08 적용**: Pre-Director 게이트의 REJECT는 모두 Advisory로 전환되어 Director에 `_python_advisories`로 전달된다.

| # | 게이트 | 위치 | 검증 내용 | 차단력 |
|---|--------|------|----------|--------|
| 1 | DraftValidator (1차) | validation_pipeline B1 | 필드 존재, 타입, 길이 | Advisory |
| 2 | SelfReflector | validation_pipeline B1 | LLM 자기비판 | Advisory |
| 3 | Consensus | validation_pipeline B1 | 3-LLM 합의 | Advisory |
| 4 | Flow Guard | validation_pipeline B2 | 서사 구조 분석 | Advisory |
| 5 | Duplicate Guard | validation_pipeline B2 | 0.92 유사도 중복 | Advisory (TF-25-08) |
| 6 | DraftValidator (전체) + ArcCorrector | validation_pipeline B3 | 전체 검증 + 자동 교정 | Advisory + 자동교정 (TF-25-08) |
| 7 | ContinuityInspector | validation_pipeline B4 | 교차 Arc 연속성 | Advisory |
| 8 | Tactical Arithmetic | finalizer pre-check | 숫자 일관성 (5% 허용) | Advisory |
| 9 | Asset Continuity | finalizer pre-check | 자산 전이 (±20% 허용) | Advisory |
| 10 | **Director Judgment** | finalizer | PASS/PASS_WITH_FIX/REJECT (0-100점) | **Blocking** |
| 11 | Quality Gate | finalizer post-Director | score < 90 + tactical_doc ≥ 1500자 → REJECT | Blocking |

### 4.3 Stage 2 성숙도 평가

| 축 | 등급 | 근거 |
|----|------|------|
| **아키텍처** | ★5 | 7개 모듈, 7,283줄. DI 컨텍스트(56+ 속성), 배치+순차 루프, 원자적 DB 커밋. |
| **검증 깊이** | ★4 | 11개 게이트. Pre-Director Advisory 9개 → `_python_advisories`로 Director 전달 + Director + Quality Gate. |
| **자동 교정** | ★4 | ArcCorrector, patch 모드 3회, PF-3 패치본 채택. |
| **상태 관리** | ★4 | StateTracker(NPC/재정, deepcopy 스냅샷+롤백), ConstraintDB(이력, 롤백 없음). |
| **정보 전달 충실도** | ★2 | 기존 조사 SD-1 발견: state_constraints 3계층→1차원 붕괴 (Track D). |
| **의미 검증** | ★2 | 기존 조사 SD-2 발견: 형태 검증 편향 (Track A, B). |
| **비용 효율** | ★3 | MAJOR 루프 최악 80 LLM 호출. 점수 하한/하강 추세 미감지 (A-2). |

---

## 5. Stage 2 시스템 수준 개선사항

> 기존 Track A(A-1~A-3) 개별 이슈와 중복되지 않는 **시스템 수준** 항목.

### S2-1: Advisory 게이트 누적의 가중치 부여 미비

**현황**: TF-25-08 적용으로 Pre-Director 게이트 9개가 모두 Advisory.
- Advisory 결과는 `_python_advisories` 리스트에 축적되어 Director 프롬프트에 **전달됨** (validation_pipeline line 58, 151).
- 단, advisory 건수 자체에 대한 **가중치 부여나 추가 경고 메커니즘은 없음**.

**갭**: Advisory 9개가 모두 경고를 발생시켜도 Director에 개별 전달될 뿐, **"다수 경고 누적"이라는 메타 시그널은 미생성**. advisory_count 자체가 품질 신호인데 활용되지 않음.

**영향도**: **Nice-to-have** (~~Significant~~ 하향) — Advisory→Director 전달 경로는 이미 작동 중. 가중치 부여만 미비.

**방향 스케치**:
- Advisory 카운터: `advisory_count >= 5`이면 Director 프롬프트에 "다수 경고 발생" 메타 삽입.
- 또는 advisory_count를 Quality Gate 점수에 반영 (예: advisory 1개당 -2점).

### S2-2: Preflight 컨텍스트 검색의 예산 관리 불투명

**현황**: `stage2_preflight.py` — `_execute_stage2_retrieval_plan()` (line 148):
- 하이브리드 검색 (dense/sparse/hybrid, line 217).
- 소스: VEC_MEMORY, DB_NPC_HISTORY, DB_NPC_RELATIONSHIP 등.
- **예산 기반 절삭** 존재 (line 248)하지만 예산 배분 로직이 코드 내부에 하드코딩.

**갭**: 어떤 소스에서 얼마나 검색할지의 **예산 배분이 투명하지 않음**. Arc 복잡도에 따라 NPC 히스토리가 더 필요할 수 있지만 정적 배분.

**영향도**: **Nice-to-have** — 현재 검색은 기능적으로 작동. 최적화 여지.

### S2-3: 배치 병렬 enrichment의 실패 복구 세분화 부족

**현황**: `stage2_orchestrator.py`:385-493 — 5개 Arc 병렬 enrichment:
- 실패 시 복구 메커니즘 존재 (`MAX_PARALLEL_RECOVERY = 2`, `constants.py`).
- **부분 실패**(5개 중 2개 실패) 시 성공한 3개만 진행.

**갭**: 실패한 Arc가 배치 내 **중간 위치**(예: Arc 3)면 Arc 4, 5의 stitching이 Arc 2→4로 건너뜀. 연속성 갭 발생 가능.

**영향도**: **Nice-to-have** — 실패 빈도 낮음. 발생 시 stitching 품질 저하.

### S2-4: ConstraintDB ↔ StateTracker 이중 상태 관리

**현황**:
- `ConstraintDB` (`constraint_db.py`:48-612): Arc 이력 기반 제약 생성. **snapshot/rollback 메서드 없음**.
- `StateTracker`: NPC/재정 상태 추적. **deepcopy 기반 스냅샷 + 명시적 롤백 존재** (`preflight.py`:1457-1487 스냅샷, `finalizer.py`:863-869 롤백).
- 두 시스템이 **독립적으로 상태를 관리**. 동기화 포인트는 finalizer의 PASS 커밋 시점.

**갭**: retry 중 StateTracker는 스냅샷 롤백(`finalizer.py`:863-869)되지만 ConstraintDB는 롤백 메커니즘 자체가 없음. 특히 PASS_WITH_FIX → 패치 → REJECT → retry 경로.

**현재 우연적 안전성**: `constraint_db.update_arc_state()`는 PASS 후 DB 커밋 이후에만 호출 (`finalizer.py`:1144-1151). REJECT 시에는 ConstraintDB에 기록하지 않으므로, 현재는 **우연히 동기화가 유지됨**. 그러나 ConstraintDB에 snapshot/rollback이 없는 구조 자체가 향후 변경 시 취약점이 될 수 있음.

**영향도**: **Significant** — 구조적 취약성. 현재 능동적 트리거는 없으나, 패치 루프에서 ConstraintDB 참조를 추가하는 등의 변경 시 즉시 발현.

**방향 스케치**: ConstraintDB에 `snapshot()` / `rollback(snapshot)` 메서드 추가. StateTracker 롤백 경로에서 동시 롤백.

### S2-5: Quality Gate 조건의 비대칭성

**현황**: `stage2_finalizer.py`:848-862:
- PASS이면서 `tactical_doc >= 1500자`이면서 `score < 90` → REJECT.
- **PASS_WITH_FIX에는 Quality Gate 미적용** (line 846 주석: "TF-46 PASS만 gate 적용", line 848 조건문 `_d_decision == "PASS"`).

**갭**: PASS_WITH_FIX는 패치 후 PASS로 승격될 수 있는데, 승격 시점에서 Quality Gate를 재적용하는지 불명확. 패치 후 score가 85여도 PASS로 통과할 수 있음.

**영향도**: **Significant** — PASS_WITH_FIX 경로가 Quality Gate를 우회하여 저점수 Arc 통과 가능.

**방향 스케치**: PASS_WITH_FIX → 패치 → PASS 승격 시에도 Quality Gate 재적용.

---

## 6. S0→S2 핸드오프 계약

### 6.1 현재 계약

| 데이터 | 소스 | 키 | Stage 2 읽기 지점 |
|--------|------|-----|-------------------|
| Bible | Stage 0 | `db.load_anchor("bible")` | `orchestrator.py`:245-246 |
| plot_roadmap | Stage 0 (Bible 내부) | `bible["MasterBible"]["plot_roadmap"]` | `orchestrator.py`:258-259 |
| Volumes | Stage 1 (선택적) | `db.load_anchor("volumes")` | `orchestrator.py`:247-248 |
| StyleGuide 요약 | Stage 0 | `build_style_guide_summary()` | `preflight.py`:337-343, 808 |

### 6.2 핸드오프 갭

**H-1: plot_roadmap 스키마 불명확**

`_build_plot_roadmap_from_treatment()` (`stage01_helpers.py`:604-618)가 생성하는 plot_roadmap 항목과 Stage 2의 Analyst가 기대하는 `raw_block` 스키마 간 **명시적 계약 없음**.

- Stage 0 생성: `{"block_no": N, ...treatment 블록 필드 전부}`
- Stage 2 기대: `enriched_block` (Analyst.enrich_raw_block_async가 변환)
- **Analyst가 어떤 필드를 기대하는지 Stage 0이 보장하지 않음**.

**H-2: Bible 품질이 Stage 2 품질의 천장**

Stage 0에서 빈약한 Bible → Stage 2 Analyst의 enrichment 입력이 빈약 → Arc 설계 품질 저하. 현재 이 **역방향 품질 압력**을 감지하는 메커니즘 없음.

**H-3: StyleGuide → Stage 2 세부 파라미터 미전달** (부분 해소)

~~StyleGuide는 Stage 2에서 참조되지 않음~~ → **수정**: `stage2_preflight.py`:808에서 `build_style_guide_summary()`를 호출하여 StyleGuide **텍스트 요약**을 Arc 설계 컨텍스트에 포함 중. 단, `StyleGuide` CLASS의 세부 파라미터(문장 길이 분포, 어휘 다양성 지수, 문체 DNA 등 구조화된 수치)는 Stage 4(`stage4_orchestrator.py`:1588, 1617)에서만 직접 임포트.

**잔여 갭**: Arc 설계 시 문체 **수치 제약**(평균 문장 길이, 대화 비율 등)을 반영하려면 요약이 아닌 구조화된 StyleGuide 접근이 필요. 현재는 텍스트 요약 수준의 참조만 존재.

**영향도**: **부분 해소** (기존 Nice-to-have → 요약 전달은 작동 중, 구조화 접근만 미비)

---

## 7. 통합 영향도 매트릭스

| ID | 제목 | Stage | 영향도 |
|----|------|-------|--------|
| **S2-5** | Quality Gate 조건의 비대칭성 | 2 | Significant |
| **S2-4** | ConstraintDB↔StateTracker 이중 상태 관리 | 2 | Significant (구조적, 현재 잠복) |
| **S0-1** | Bible 생성 품질 검증 부재 | 0 | Significant |
| **S0-2** | Treatment 블록 간 연속성 미검증 | 0 | Significant |
| **S0-3** | 컨셉 경로 plot_roadmap Treatment 의존성 | 0 | Significant (~~Critical~~ 하향) |
| **H-1** | plot_roadmap 스키마 불명확 | 0→2 | Significant |
| **H-2** | Bible 품질 → Stage 2 품질 천장 | 0→2 | Significant |
| **S2-1** | Advisory 게이트 누적 가중치 미비 | 2 | Nice-to-have (~~Significant~~ 하향) |
| **S2-2** | Preflight 컨텍스트 검색 예산 불투명 | 2 | Nice-to-have |
| **S2-3** | 배치 enrichment 실패 복구 세분화 | 2 | Nice-to-have |
| **S0-4** | StyleGuide 캐시 무효화 전략 부재 | 0 | Nice-to-have |
| **S0-5** | POV × 외부시점정책 조합 미검증 | 0 | Nice-to-have |
| **H-3** | StyleGuide → Stage 2 세부 파라미터 미전달 | 0→2 | 부분 해소 |

---

## 8. 기존 조사와의 관계

이번 조사는 기존 `ssot_stage23-improvement-survey.md`(12건)와 **상호 보완**:

| 기존 조사 | 이번 조사 |
|----------|----------|
| Stage 2 **개별 이슈** (A-1~A-3: tactical_doc, MAJOR, 마커) | Stage 2 **시스템 수준** (검증 게이트 구조, 상태 관리, Quality Gate) |
| Stage 2→3 **핸드오프** (C-1~C-3) | Stage 0→2 **핸드오프** (H-1~H-3) |
| Stage 2+3→4 **파이프라인** (D-1~D-3) | Stage 0 **내부** (S0-1~S0-5) |

**합산 현황**:
- Stage 0: 5개 개선사항 + 3개 핸드오프 이슈 = **8건** (H-3 부분 해소)
- Stage 2: 기존 3건(Track A) + 신규 5건(시스템 수준) = **8건**
- Stage 2→3: 기존 3건(Track C) = 3건
- Stage 2+3→4: 기존 3건(Track D) = 3건
- Stage 3 내부: 기존 3건(Track B) = 3건
- **전체**: 25건 (H-3 부분 해소 포함)

---

## 9. 우선순위 정렬

### Tier 1: 파이프라인 안정
1. **H-1** — plot_roadmap 스키마 계약 명시 (S0→S2 안정성)

### Tier 2: Stage 4 산출물 품질 직결
2. **S2-5** — Quality Gate PASS_WITH_FIX 우회 방지
3. **S2-4** — ConstraintDB↔StateTracker 동기화 (구조적 취약성 해소)
4. **S0-1** — Bible 생성 품질 검증
5. **S0-3** — 컨셉 경로 plot_roadmap Treatment 의존성

### Tier 3: 장기 품질 기반
6. **S0-2** — Treatment 블록 연속성
7. **H-2** — Bible 품질 → Stage 2 역방향 압력 감지
8. **S2-1** — Advisory 가중치 (전달은 작동 중, 가중치만 미비)

### Tier 4: 최적화 / 부분 해소
9. **S2-2**, **S2-3**, **S0-4**, **S0-5**
10. ~~H-3~~ — 부분 해소 (preflight에서 요약 사용 중)

---

## 10. 핵심 코드 참조

| 파일 | 관련 항목 | 핵심 라인 |
|------|----------|----------|
| `stage0/__init__.py` | S0-1~S0-5, H-1 | 451-466 (_ensure_plot_roadmap, 컨셉 경로), 488-491 (Bible 검증) |
| `stage0/story_expander.py` | S0-1, S0-2 | 198-256 (generate_bible), 305-313 (generate_treatment), 441-476 (_generate_skeleton, 제목만 연속성), 478-516 (_generate_details, 컨텍스트 없음), 315-390 (extend_treatment, full 연속성) |
| `stage0/reverse_expander.py` | S0-3 | 594+ (run), 722-744 (_ensure_plot_roadmap, arc stubs 기반 독립 생성) |
| `stage0/style_extractor.py` | S0-4 | cache_mode 처리 (1008, 1025, 1036-1061) |
| `stage01_helpers.py` | H-1 | 604-618 (_build_plot_roadmap_from_treatment) |
| `stage2_orchestrator.py` | S2-3 | 385-493 (병렬 enrichment), 585 (retry loop) |
| `stage2_preflight.py` | S2-2, H-3 | 148 (_execute_stage2_retrieval_plan), 337-343 (style_guide_summary), 808 (StyleGuide 요약 주입), 1457-1487 (StateTracker 스냅샷) |
| `stage2_finalizer.py` | S2-4, S2-5 | 848-862 (Quality Gate), 657-845 (패치 루프), 863-869 (StateTracker 롤백), 1144-1151 (ConstraintDB PASS 후 업데이트) |
| `stage2_validation_pipeline.py` | S2-1 | 58 (_python_advisories 축적), 151 (Director 전달), B1-B4 검증 체인 |
| `stage2_optimizer.py` | S2-4 | 95 (StateSnapshotInjector) |
| `stage2_context.py` | S2-4 | DI 컨텍스트 56+ 속성 (__slots__ 134-193) |
| `constraint_db.py` | S2-4 | 48-612 (ConstraintDB, snapshot/rollback 메서드 없음) |

---

## 11. 감리 기록

### 원본 3-Pass 감리 (초판)

| Pass | 확신도 | 요약 |
|------|--------|------|
| Pass 1 (사실 정확성) | 93% | 6개 모듈 파일, 게이트 코드 경로, Quality Gate 비적용 확인 |
| Pass 2 (논리 정합성) | 96% | S0-3→차단 위험, S2-5→저점수 통과, Advisory→판단력 약화 인과 건전 판정 |
| Pass 3 (완성도) | 97% | 8건+5건 커버, 기존 조사 관계, 성숙도 평가, 4-Tier 정렬 |

### 코드베이스 대조 재감리 (5-Pass)

| Pass | 확신도 | 핵심 발견 |
|------|--------|----------|
| Pass 1 (사실 정확성) | 78% | **8건 팩트 오류**: reverse_expander 755→1212줄, S0 총량 4458→5615줄, DuplicateGuard Blocking→Advisory(TF-25-08), StateTracker 롤백 779-788→863-868, Advisory→Director 전달 존재 확인, H-3 StyleGuide 요약 preflight 사용 중, S0-3 역설계 독립 생성 경로 발견, preset_registry/stage01_helpers 줄 수 과소 |
| Pass 2 (논리 정합성) | 85% | **2건 결론 무효화**: S2-1(Advisory 미전달→실제 전달됨, 가중치만 미비), H-3(미전달→요약 전달 중). **1건 결론 약화**: S0-3(Critical→역설계 독립 경로 존재) |
| Pass 3 (완성도) | 89% | TF-25-08 전역 적용 미반영, 게이트 분류표 stale, DI 컨텍스트 40+→56+ |
| Pass 4 (잔여 해소) | 93% | S0-3 `_ensure_plot_roadmap` 2개 존재 확인 (컨셉 vs 역설계), S2-5 PASS_WITH_FIX 우회 코드 직접 확인 |
| Pass 5 (개별 항목 재감리) | 95% | **S2-4**: ConstraintDB에 snapshot/rollback 메서드 없음 확인, 단 update_arc_state()가 PASS 시에만 호출되어 우연적 안전성 존재 (개별 97%). **S0-2**: skeleton은 제목만 전달, details는 컨텍스트 제로, extend_treatment만 full 연속성 확인 (개별 98%) |

### 수정 사항 요약

| # | 수정 유형 | 내용 |
|---|----------|------|
| 1 | 줄 수 보정 | reverse_expander 755→1212, preset_registry 500→739, stage01_helpers 650→926, S0 총량 4458→5615, DI 컨텍스트 40+→56+ |
| 2 | 게이트 분류 | DuplicateGuard Blocking→Advisory(TF-25-08), ArcCorrector Blocking(교정)→Advisory+교정(TF-25-08) |
| 3 | S2-1 재평가 | "Director에 미주입" → "전달됨, 가중치 미비". 영향도 Significant→Nice-to-have |
| 4 | S0-3 재평가 | "역설계→빈 리스트" → "컨셉 경로만 해당". 영향도 Critical→Significant |
| 5 | H-3 재평가 | "Stage 2 미전달" → "요약 전달 중, CLASS 직접 접근만 부재". 부분 해소 표기 |
| 6 | S2-4 정밀화 | 롤백 위치 779-788→863-869, ConstraintDB 우연적 안전성 명시 |
| 7 | S0-2 정밀화 | skeleton 제목만 전달, details 컨텍스트 제로, extend_treatment만 full 연속성 |
| 8 | 핸드오프 라인 | Bible 245-250→245-246, plot_roadmap 254-270→258-259, Volumes 247-258→247-248 |
| 9 | 우선순위 재정렬 | S0-3 Tier1→Tier2, S2-1 Tier2→Tier3, H-1 단독 Tier1 |
