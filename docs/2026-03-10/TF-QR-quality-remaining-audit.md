# TF-QR 전수조사: 기존 2개 감사 외 잔여 퀄리티 개선 경로

> 작성: 2026-03-10
> 상태: 5pass 감리 완료 (오탐 6건 제거, 과장 3건 정정, 신규 확인 8건 유지)
> 전제: `TF-DB-quality-boost-audit.md`(DB 활용) + `quality-boost-beyond-db-audit.md`(DB 외 3대 방향) 양쪽에 **없는** 항목만 수록
> 방법: Stage0→Config→Ensemble→Guard 4개 영역 병렬 전수조사 → 코드 검증 → 5pass 오탐/과장 제거

---

## 공통 원칙

- **대원칙 1**: Python은 수집만, 판단은 LLM이
- **대원칙 3**: Director 주권주의 — advisory만 제공, REJECT 강제 금지
- 기존 동작 불변 — 추가/보강만, 기존 로직 변경 금지
- LLM 호출 최소화 — Python-only 우선

> `Codex 메모`
> `QR-2`, `QR-5`, `QR-7`은 "완전 부재"보다 "부분 존재하지만 목표 경로가 비어 있음"에 가깝다.
> - `QR-2`: Analyst와 Stage 3은 이미 `protagonist_config`를 읽는다. 남은 갭은 Stage 2 preflight compact summary + `pov` 강조다.
> - `QR-5`: Stage 4에는 최근 에피소드와의 씬 유사도 advisory가 있으나, 후보 A/B/C 간 pairwise 다양성 측정은 없다.
> - `QR-7`: Stage 4에는 `LOGIC_ERROR`/`reject_bucket`/모순 유형 연속 감지 휴리스틱이 있으나, 점수 하락/동점 plateau 감지는 없다.

---

## 오탐 제거 기록 (5pass 감리)

| 초기 후보 | 판정 | 근거 |
|-----------|------|------|
| StyleGuard `run_deep_validation()` stub | **오탐** | anti-AI 패턴 + 금지 표현 + 문장 길이 3개 검사 활성 확인 (`style_guard.py`) |
| Investment Guard 재산 한도 미검증 | **오탐** | `validate_investment_scale()` + `validate_leverage_return()` + `get_impossible_actions()` 3-level 시스템 완비 (`investment_guard.py`) |
| Continuity Packet §5-6 미구현 | **오탐** | §5 관계 변천사 + §6 수치 이력 전량 구현 확인 (`stage4_context_builder.py`) |
| Treatment Stage 2 미소비 | **오탐** | `analyst.py`가 `treatment_raw_part`를 수신하고 JSON 파싱 후 LLM 프롬프트에 주입 |
| ep_count 규칙 비통일 | **오탐** | TF-D 완료 — `constants.py` MAX_EP_COUNT=6, `ensemble.yaml:79` "3~6", `analyst.yaml:291/352` 전량 동기화 |
| CW 톤 비일관 | **오탐** | TF-E 완료 — "절대 금지"→"사용하지 마세요" 등 톤 조절 반영, 핵심 금지 3곳만 유지 |

---

## 카테고리 A: 데이터 흐름 단절 (Stage 0 → Stage 2/3)

### QR-1. StyleGuide — Stage 2/3 완전 미주입

**현황**:
- Stage 0: `style_extractor.py`에서 5-phase 분석 (통계/샘플/리듬/LLM심층/anti-AI 15패턴)
- Stage 4: `chief_writer.py`에서 `style_guide: str` 파라미터로 CW에 주입 ✅
- Stage 2: `analyst.py`, `stage2_orchestrator.py`, `stage2_preflight.py` — **style_guide 참조 0건** ❌
- Stage 3: `stage3_orchestrator.py` — **style_guide 참조 0건** ❌

**갭**: Analyst가 Arc 설계 시 대상 문체를 모름.
- Arc에 "서정적 독백 씬 3개" 설계 → 실제 문체는 "간결한 액션 위주" → CW가 뒤늦게 문체 적용하면 Arc 설계와 괴리
- Blueprint 생성기가 감정 비트 배치 시 anti-AI 패턴을 모름 → CW 단계에서 대량 수정 필요

**해법**:
- `stage2_preflight.py` `enhanced_context`에 `style_guide.to_prompt()` 요약(~500자) 주입
- Analyst가 Arc 설계 시 문체 방향성 인지
- Blueprint 생성기에도 anti-AI 패턴 키워드 주입

**우선순위**: P1
**파일**: `modules/core/stage2_preflight.py`, `modules/core/stage3_orchestrator.py`

---

### QR-2. Protagonist Config — Stage 2 preflight 미보강 (POV 누락 중심)

**현황**:
- Stage 0: `show_protagonist_config_menu()`에서 `world_origin`, `incarnation_type`, `pov` 수집
- Stage 2 Analyst: `analyst.py`가 Bible의 `protagonist_config`를 읽어 `world_origin`/`incarnation_type`를 프롬프트에 이미 주입 ✅
- `Stage2Context` (__slots__): **protagonist_config 슬롯 없음** — 필요 시 Bible/DB 동적 접근
- Stage 3: `stage3_orchestrator.py`가 `protagonist_config`를 전달하고, `blueprint_ensemble.py`가 `pov` 제약까지 사용 ✅
- Stage 2 preflight `enhanced_context`에는 protagonist_config compact summary가 아직 없음 ❌

**갭**: Analyst가 완전히 모르는 것은 아니지만, `enhanced_context` 상단에 compact summary가 없고 `pov`도 Stage 2 쪽에서 별도 강조되지 않는다.
- 재시도/압축 컨텍스트에서 `world_origin`/`incarnation_type`/`pov` 신호가 약해질 수 있음
- 1인칭 전용 설정인데 Stage 2 전술 설계 문맥에서 시점 제약이 희석될 수 있음

**해법**:
- `stage2_preflight.py` `enhanced_context`에 protagonist_config 3필드 주입 (`world_origin`, `incarnation_type`, `pov`)
- Bible에서 읽어 1~2줄 compact summary 추가

**우선순위**: P2 (기존 Guard/Validator가 사후 잡는 경우 많음)
**파일**: `modules/core/stage2_preflight.py`

---

## 카테고리 B: 앙상블/전략 최적화

### QR-3. Strategy Win Rates — Display-Only (미소비)

**현황**:
- `db_manager.get_strategy_win_rates()`는 최근 `PASS` 기록의 `selected_strategy` 분포를 반환
- 해당 값은 `stage4_interview_round.py`의 `[참고 — 판정 무관]` 블록에 주입됨 (정보 표시만)
- `arc_ensemble.py`: 3 고정 전략 (conservative/balanced/creative) 항상 생성
- `chief_writer.py`: 3 고정 전략 (balanced/narrative/tension) 항상 생성
- **어느 쪽도 과거 승률 데이터를 전략 선택에 활용하지 않음**

**갭**: 현재 지표는 엄밀한 "전략별 pass rate"라기보다 "최근 PASS 선택 비중"에 가깝지만, 그조차도 전략 fan-out 조정에는 쓰지 않는다.
- 최근 PASS에서 특정 전략 쏠림이 커도 항상 3전략을 동일 비중으로 생성
- reference-only 통계로 머물러 비효율 LLM 호출이 유지됨

**해법**:
- Arc 앙상블: 최근 PASS 선택 비중이 낮은 전략 → thinking_level="high" 또는 temperature 조정
- CW 앙상블: 최근 PASS 선택 비중이 높은 전략을 우선 생성하되, 저비중 전략 1개는 탐색용으로 유지
- Python-only, LLM 0회

**우선순위**: P1
**파일**: `modules/domain/agents/arc_ensemble.py`, `modules/domain/agents/chief_writer.py`

---

### QR-4. CW 온도 범위 과소 — 2개 고유값만

**현황**:
- balanced: temperature = **0.7**
- narrative: temperature = **0.8**
- tension: temperature = **0.8**
- **narrative와 tension이 동일 온도** → 실질적으로 2종류 후보만 생성

**갭**: 3후보 앙상블인데 2개가 같은 온도 → 후보 다양성 저하. Director 선택지 실질 축소.

**해법**:
- tension: 0.8 → **0.9** (긴장감 전략은 더 과감한 표현 허용)
- 또는 balanced: 0.7 → **0.6** (보수적 전략은 더 안정적으로)
- `chief_writer.py` 1줄 수정

**우선순위**: P1
**파일**: `modules/domain/agents/chief_writer.py`

---

### QR-5. 후보 다양성 미측정

**현황**:
- Arc 3후보: `_evaluate_candidate()`에서 JSON 유효성/필수 필드/캐릭터 일관성/tactical_doc 품질 검사
- CW 3후보: 개별 검증만, 후보 간 비교 없음
- Stage 4에는 최근 에피소드와의 씬 유사도 advisory가 있으나, **후보 A/B/C 간 pairwise 유사도 측정은 0건**

**갭**: 3후보가 사실상 동일 내용이면 앙상블 이점 0. Director 선택이 무의미.

**해법**:
- 후보 생성 후 pairwise 유사도 측정 (Python-only, 3-gram Jaccard)
- 유사도 > 70%인 쌍이 2개 이상 → Director advisory: `"[후보 다양성 경고] 3후보가 유사합니다"`
- 또는 유사도 높은 후보 1개를 temperature+0.2로 재생성

**우선순위**: P2 (구현 비용 중)
**파일**: `modules/domain/agents/arc_ensemble.py`, `modules/domain/agents/chief_writer.py`, `modules/core/stage4_interview_round.py`

---

### QR-6. 전원 동일 실패 미감지

**현황**:
- Director가 3후보를 개별 평가
- **3후보 전부 동일 위반** (예: 전부 "NPC 텔레포트") → Director가 패턴으로 인식 못 함
- 현재: 각 후보별 violation 개별 표시

**갭**: 3후보 전원 같은 문제 = Arc/Blueprint 설계 결함일 가능성 높음. Director에게 이 신호 미전달.

**해법**:
- `stage4_interview_round._run_pre_director_validation()` 내부에서 violation type Counter 집계
- 3후보 전원 동일 violation → `[⚠️ 전원 동일 위반: {type}]` Director MC 최상단 주입
- Python-only, ~20줄

**우선순위**: P2
**파일**: `modules/core/stage4_interview_round.py`

---

### QR-7. 재시도 수확체감 미감지

**현황**:
- Stage 4 retry 최대 ~5회 (V75-D 휴리스틱)
- `stage4_orchestrator.py`는 이미 `LOGIC_ERROR`/`reject_bucket`/모순 유형 연속 패턴을 추적해 블루프린트 에스컬레이션을 수행 ✅
- 재시도마다 동일 전략 선택 방식
- **점수 추이(하락/동점 plateau)는 미추적** — 시도 1(85점)→2(82점)→3(78점) 하락 추세여도 계속 시도

**갭**: 현재 휴리스틱은 "오류 유형 반복"은 보지만 "점수 개선 정체"는 보지 못한다.
- 3연속 점수 하락 = 현재 전략으로는 개선 불가일 수 있음
- 2연속 동점 = 동일 수정 루프를 맴돌고 있을 가능성 높음

**해법**:
- `stage4_orchestrator.py` 라운드 루프에서 점수 history 리스트 유지
- 3연속 하락 or 2연속 동점 → "plateau detected" advisory + fix_scope escalation 권고
- Python-only

**우선순위**: P2
**파일**: `modules/core/stage4_orchestrator.py`

---

## 카테고리 C: Guard/검증 잔여 갭

### QR-8. WorkGuard character_constraints — 프롬프트 주입만, 사후 검증 없음

**현황**:
- `work_guard.py`: YAML에서 `character_constraints` 로드
- `get_v20_purism_prompt()`: CW 프롬프트에 `[캐릭터별 제약]` 텍스트 주입 ✅
- `run_deep_validation()`: forbidden_terms/patterns만 검사, **character_constraints 미검증** ❌

**갭**: "주인공 나이 18~35세" 제약이 YAML에 정의되어 있어도, 원고에서 "50대 주인공" 등장 시 Guard가 안 잡음.

**해법**:
- `run_deep_validation()`에 character_constraints 기반 검증 추가
- 단, 기존 Guard 경로의 `HIGH/CRITICAL`은 `director_auditor.py`에서 `[CRITICAL 경고] ... 반드시 REJECT` 블록으로 승격되므로 그대로 쓰면 과도함
- 따라서 `WARNING`급 별도 필드/반환값을 추가하거나, `director_auditor.py`에 비강제 warning 전달 경로를 함께 추가해야 함
- NPC 이름 + 속성 키워드 매칭 (Python regex)

**⚠️ 오탐 방지 필수**: 빙의/환생/회귀 설정에서 "노인이 청년 몸에 들어옴" → 원고에 "60대의 기억" 등 서술 시 나이브 regex가 오탐 발생.
- `protagonist_config.incarnation_type`이 빙의/환생/회귀일 경우 → **나이 관련 character_constraints 검증 suppress**
- 또는 advisory 텍스트에 `(빙의/환생 설정 시 정상일 수 있음)` 면책 문구 추가
- 현재 구조상 잘못 구현하면 사실상 REJECT 압력으로 작동할 수 있으므로, 오탐률 최소화 + 비강제 전달 경로 분리가 필수

**우선순위**: P2 (작품별 Guard 사용 빈도 낮음)
**파일**: `modules/core/genre_guards/work_guard.py`, `modules/domain/agents/director_auditor.py`

---

## 우선순위 요약

### P1 (즉시 효과 — 저비용 고효과)

| ID | 항목 | 효과 | 비용 |
|----|------|------|------|
| QR-1 | StyleGuide S2/S3 주입 | Arc/Blueprint 문체 정합 | 낮 (~30줄) |
| QR-3 | Strategy win rates 소비 | 비효율 LLM 호출 감소 | 낮~중 |
| QR-4 | CW 온도 범위 확대 | 후보 다양성↑ | **극저** (1줄) |

### P2 (보강 — 중기 효과)

| ID | 항목 | 효과 | 비용 |
|----|------|------|------|
| QR-2 | Protagonist config S2 주입 | 설정 불일치 사전 방지 | 낮 |
| QR-5 | 후보 다양성 측정 | 앙상블 실효성↑ | 중 |
| QR-6 | 전원 동일 실패 감지 | Arc 설계 결함 조기 식별 | 낮 (~20줄) |
| QR-7 | 재시도 수확체감 감지 | 비효율 retry 조기 종료 | 낮~중 |
| QR-8 | WorkGuard 캐릭터 제약 강제 | 작품별 설정 위반 감지 | 낮 |

---

## 기존 2개 문서와의 관계

| 본 QR | TF-DB | Beyond-DB | 관계 |
|--------|-------|-----------|------|
| QR-1 (StyleGuide) | — | — | **신규** (데이터 흐름 단절) |
| QR-2 (Protagonist) | — | — | **신규** (데이터 흐름 단절) |
| QR-3 (Win rates) | — | — | **신규** (앙상블 최적화) |
| QR-4 (CW 온도) | — | — | **신규** (앙상블 최적화) |
| QR-5 (후보 다양성) | — | — | **신규** (앙상블 최적화) |
| QR-6 (전원 동일 실패) | — | QI-SNR-3 보완 | **보완** (advisory 모순 + 전원 동일 위반) |
| QR-7 (수확체감) | — | — | **신규** (retry 최적화) |
| QR-8 (WorkGuard) | — | — | **신규** (Guard 강화) |

---

## 파일 변경 목록 (예상)

| 파일 | 변경 | QR ID |
|------|------|-------|
| `modules/core/stage2_preflight.py` | StyleGuide 요약 + protagonist_config enhanced_context 주입 | QR-1, QR-2 |
| `modules/core/stage3_orchestrator.py` | StyleGuide anti-AI 키워드 Blueprint 컨텍스트 주입 | QR-1 |
| `modules/domain/agents/arc_ensemble.py` | 최근 PASS 선택 비중 기반 전략 가중치 조정 + 후보 다양성 점검 | QR-3, QR-5 |
| `modules/domain/agents/chief_writer.py` | tension 온도 0.8→0.9 + 최근 PASS 선택 비중 기반 전략 조정 + 후보 다양성 점검 | QR-3, QR-4, QR-5 |
| `modules/core/stage4_interview_round.py` | 후보 다양성 advisory + 전원 동일 위반 감지 | QR-5, QR-6 |
| `modules/core/stage4_orchestrator.py` | 재시도 점수 추적 + plateau 감지 | QR-7 |
| `modules/core/genre_guards/work_guard.py` | character_constraints 검증 추가 | QR-8 |
| `modules/domain/agents/director_auditor.py` | WorkGuard non-critical warning 전달 경로 추가 | QR-8 |

---

## 절대 하지 말 것

- 기존 3 전략 이름(conservative/balanced/creative, balanced/narrative/tension)을 변경하지 말 것
- `arc_ensemble._evaluate_candidate()` 점수 기준(30/20/15/25)을 변경하지 말 것
- StyleGuide `to_prompt()` 출력 포맷을 변경하지 말 것
- Genre Guard 기존 금지어/검증 로직을 변경하지 말 것
- 기존 advisory 체인 순서를 변경하지 말 것
- LLM 호출을 추가하지 말 것 (Python-only)

---

## 검증 기준

- `pytest tests/ -q` 전체 회귀 PASS
- `pytest --collect-only -q tests` 기준 전체 테스트 **3,785개 수집 유지** (2026-03-10 확인)
- `ruff check` 변경 파일 전량 0 violations
- CW 후보 간 유사도: 변경 전 < 변경 후 (다양성 증가 확인, QR-4/QR-5 적용 시)
- Director PASS rate: 변경 전 ≤ 변경 후 (하락 금지)
