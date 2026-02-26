# Opus TF 전수조사 결과 (2026-02-26)

> 4개 TF 병렬 감사 + 4개 TF 재감리 | 수정 금지, 문서화 전용
> 범위: Stage 0/2/3/4 + 크로스컷 + 에이전트 컨텍스트 + 공통 인프라

---

## 총계 (1차 감사 → 재감리 보정)

| TF | 범위 | 1차 P0 | 1차 P1 | 1차 P2 | 합계 |
|----|------|--------|--------|--------|------|
| TF-A | Stage 0 + Stage 2 | 1 | 9 | 7 | 17 |
| TF-B | Stage 3 | 3 | 13 | 5 | 21 |
| TF-C | Stage 4 + 검증 | 4 | 8 | 6 | 18 |
| TF-D | 크로스컷 + 인프라 | 0 | 7 | 12 | 19 |
| **1차 합계** | | **8** | **37** | **30** | **75** |

### 재감리 보정 결과

| 구분 | 건수 | 설명 |
|------|------|------|
| **실제 P0** | **0건** | 8건 전량 하향/오탐/의도적 |
| **실제 P1** | **3건** | TruthGate 사문화, rollback 누락, DBManager 공유커서 |
| **실제 P2** | **~20건** | dead code, 코드 정리, 방어 경로 edge case |
| **FALSE POSITIVE** | **~15건** | 코드에 이미 방어 존재 or TF 판단 오류 |
| **INTENTIONAL** | **~10건** | 대원칙 준수, 토큰 예산 관리, fail-open 설계 |

---

## P0 전량 (8건) — 재감리 판정

### P0-A1. `_python_validate` 개별 체크 예외 전파 (Stage 2)
- **파일**: `unified_arc_validator.py:539-566`
- **설명**: 9개 독립 체크 메서드 중 하나에서 예외 발생 시 나머지 전부 스킵.
- **재감리**: **P1 하향** — 각 `_check_*` 메서드 내부에 isinstance/None 방어 존재. L406 dict `.strip()` 위험은 호출자가 항상 `pre_collected_grants`를 전달하므로 폴백 경로 미도달. 발생 확률 극저.

### P0-B1. UNKNOWN 반환 시 무시 (Stage 3)
- **파일**: `three_phase_blueprint_generator.py:319`
- **설명**: `check_blueprint_continuity_with_cache`가 예외 시 "UNKNOWN" 반환, `== "REJECT"`만 체크.
- **재감리**: **INTENTIONAL (P2)** — fail-open 설계. UNKNOWN이면 후속 Director가 최종 판정. 대원칙 3(디렉터 주권주의) 정합. WARNING 로그도 남김.

### P0-B2. `fail_count >= 3` 안전장치 dead code (Stage 3)
- **파일**: `stage3_orchestrator.py:773-779`
- **설명**: `_handle_failure()`가 항상 `break: True` 반환 → fail_count 누적 불가.
- **재감리**: **P2 하향** — dead code 확인. TF-S3-02 주석("순차 의존성 보존")에 의한 의도적 즉시 중단. 기능 영향 없음.

### P0-B3. Pydantic `scene_breakdown` list→dict 데이터 손실 (Stage 3)
- **파일**: `models/blueprint.py:39`
- **설명**: LLM이 list 반환 시 Pydantic이 빈 dict로 교체 가능.
- **재감리**: **FALSE POSITIVE** — `validate_blueprint()` except 블록에서 원본 dict 그대로 반환. Pydantic v2 ValidationError 시 빈 dict 교체가 아닌 원본 유지. 데이터 손실 발생 안 함.

### P0-C1. ConsistencyValidator dead expression (Stage 4)
- **파일**: `consistency_validator.py:236`
- **설명**: `len(unjustifiable) > 0` 표현식 미할당.
- **재감리**: **P2 하향** — L255에서 `is_passed = len(unjustifiable) == 0`으로 재계산. 기능 영향 없음.

### P0-C2. BlockingValidator advisory 전환 (Stage 4)
- **파일**: `stage4_interview_round.py:495-520`
- **설명**: 사망 NPC 활동 원고가 Director에게 경고와 함께 전달됨.
- **재감리**: **INTENTIONAL (비이슈)** — V70.1 주석: "대원칙 준수: Python은 수집만, 판단은 Director(LLM)가". CLAUDE.md 대원칙 1+3 정합. Python이 경고를 warnings/focus_points에 추가하여 Director에 전달.

### P0-C3. Director 입력 크기 3배 확대 (Stage 4)
- **파일**: `director_continuity.py:81,494`
- **설명**: entity 검증 5K→15K, history conflict 12K→36K.
- **재감리**: **P2 이하 (비이슈)** — Gemini 1M+ 토큰 대비 15K/36K는 극소량(2% 미만). 의도적 컨텍스트 보강. 비용 영향 미미.

### P0-C4. NPC 사망 LLM 실패 시 미등록 (Stage 4)
- **파일**: `state_tracker_npc.py:610-620, 670-718`
- **설명**: LLM 실패 시 빈 set 반환 → 모든 NPC 사망 등록 실패.
- **재감리**: **FALSE POSITIVE** — `_verify_npc_names_llm()` 실패 시 모든 경로에서 `return candidates` (원본 전체 반환). 미등록이 아닌 **과등록** 방향. TF 판단 오류.

---

## P1 주요 항목 — 재감리 판정

### 핵심 7건

| # | 제목 | 파일 | 1차 판정 | 재감리 | 근거 |
|---|------|------|---------|--------|------|
| **D-1** | TruthGate 3/5 검사 무효화 | `truth_gate.py` | P1 | **CONFIRMED P1** | WorldStateManager에 4개 접근자 미구현. deceased는 npc_registry 경로로 부분 동작, karma는 정상 → 3/5 사문화 |
| **D-2** | rollback 누락 | `db_manager.py:1624-1660` | P1 | **CONFIRMED P1** | `vec_episodes`(rowid=ep_num), `foreshadow`(planted_ep) 삭제 가능하나 누락. `character_voice`는 ep_num 컬럼 없어 설계 한계 |
| **A-1** | BlockEnricher 스레드 안전 | `block_enricher.py:474-479` | P1 | **FALSE POSITIVE** | 단일 인스턴스, 순차 호출만. ThreadPoolExecutor에서 공유 안 됨 |
| **A-2** | 아이템 정규화 불일치 | `constraint_compiler.py` vs `unified_arc_validator.py` | P1 | **P2 하향** | str(dict) vs dict.get("name") 확인. 단 response_schema가 문자열 강제 → 정상 경로 발현 확률 극저 |
| **B-1** | 앙상블 response_schema 미사용 | `blueprint_ensemble.py:440-446` | P1 | **INTENTIONAL P2** | response_mime_type + robust parser + 필수 필드 체크로 보완. thinking 모드 호환성 문제 |
| **B-2** | Director 비교 시 1,500자 절삭 | `director_ensemble.py:111` | P1 | **INTENTIONAL P3** | 토큰 예산 관리. 3후보×5K=15K+전술서6K+프롬프트=25K+. 선택 후 원본 그대로 Stage 4 전달. 상세 분석 아래 참조 |
| **C-1** | hud_report.lower() 미할당 | `writer_prompt_builders.py:67` | P1 | **P2 하향** | 미할당 맞으나, 비교 대상 전부 한글(대소문자 무관) + re.IGNORECASE 사용 → 실제 동작 영향 없음 |

#### Director 1,500자 절삭 상세 분석

`integrated_scenario`는 Blueprint의 에피소드 전체 시나리오 서술문 (각 씬 전개, 대사 방향, 감정, 클라이맥스, 엔딩 기술. 보통 2,000~5,000자).

절삭 발생 지점: `director_ensemble.py:111` `compare_and_select_blueprint()` — **Stage 3에서 3개 후보 비교 선택 시에만** 적용.

Director가 받는 전체 정보:
- 각 후보의 `integrated_scenario` **앞 1,500자** (후반부 잘림)
- 메타: 씬 개수, 분량(자수), 시작/종료 위치, 시간 흐름
- 엔딩 훅 **100자**
- Arc 전술서 **6,000자** (별도 전달)
- 이전 Blueprint ending_hook + end_location

선택 후 Blueprint 원본은 잘리지 않고 그대로 Stage 4로 전달. 절삭은 "어느 후보를 고를지" 판단에만 적용.

### P1 나머지 30건 재감리 결과

| 범주 | CONFIRMED | FALSE POSITIVE | 비고 |
|------|-----------|---------------|------|
| Stage 0+2 (6건) | 4건 (전부 P2) | 2건 | unused var, protagonist_config 폴백 존재 |
| Stage 3 (8건) | 3건 (전부 P2) | 5건 | 정렬 폴백, _esc() 올바름, _ensemble_meta 미포함 |
| Stage 4 (6건) | 3건 (전부 P2) | 3건 | self-critique 4개 전량 실행, frozenset 중복 없음 |
| 크로스컷 (5건) | 2건 (P1 1건, P2 1건) | 3건 | VecMemory 단일 RLock, rollback 해석 일관 |

**주요 FALSE POSITIVE 목록** (1차 감사 오판):
- BlockEnricher 스레드 → 단일 스레드 호출만
- Pydantic list→dict 손실 → except에서 원본 반환
- NPC 사망 LLM 실패 → fail-open으로 전체 반환
- scene_breakdown 정렬 → else 0 폴백
- `_esc()` 이중 이스케이프 → 올바른 format() 패턴
- VecMemory lock ordering → 단일 RLock, 데드락 불가
- rollback 에피소드 해석 → 양쪽 모두 일관
- protagonist_config → try/except + 빈 dict 폴백
- `_ensemble_meta` 키 → scene_breakdown이 아닌 최상위 키
- self-critique 조기 종료 → 4개 체크 전량 실행
- `_COMMON_NOUN_NAMES` 중복 → 24개 항목 중복 없음

---

## 크로스컷 취약점 TOP 5 — 재감리 보정

| 순위 | 취약점 | 재감리 판정 | 심각도 |
|------|--------|-----------|--------|
| **1** | TruthGate 3/5 검사 무효화 (WorldStateManager 접근자 미구현) | **CONFIRMED** | **HIGH** |
| **2** | rollback 시 vec_episodes/foreshadow 미삭제 (character_voice는 설계 한계) | **CONFIRMED** | **MEDIUM** |
| **3** | 아이템 정규화 불일치 (str(dict) vs dict.name) | PARTIAL | LOW (schema 강제로 정상 경로 발현 극저) |
| **4** | scene_breakdown 타입 계약 (핵심 경로 대응 완료, 보조 경로 미대응) | PARTIAL | LOW |
| **5** | BlockingValidator advisory vs 대원칙 4번 | PARTIAL (의도적) | MEDIUM (V70.1 설계 결정) |

---

## 에이전트 컨텍스트 충분성 — 재감리 확정

| 에이전트 | 컨텍스트 | 판정 | 재감리 근거 |
|---------|---------|------|-----------|
| Analyst | Bible + Guard purism + 장르 라이브러리 | **충분** | |
| FourPhase | 이전 30 Arc + ConstraintDB + Director 피드백 | **충분** | |
| ArcEnsemble | 전략별 프롬프트 + 이전 Arc 전문 | **충분** | |
| BlueprintEnsemble | Arc tactical + 이전 Blueprint 30개 + Entity Registry | **충분** | |
| Director (Stage 2) | 최대 800K자 이전 Arc + Entity Registry | **과대** (비용) | 실제 상한 800K (200K 주석은 오래됨) |
| Director (Stage 3) | integrated[:1500] + 메타 + 전술서 6K | **의도적 절삭** | 토큰 예산 관리. 선택 후 원본 유지 |
| Director (Stage 4) | 원고 전문 + BP 전문 + 경고 전문 | **충분** | 잘림 없음 |
| ChiefWriter | scene_breakdown 전문 + 이전 원고 전문 + HUD + 피드백 | **충분** | 시스템 내 최풍부 컨텍스트 |
| StateTracker | 원고 전문 + HUD + 이전 상태 | **충분** | 잘림 없음 |
| TruthGate | NPC Registry + karma만 (3개 검사 비활성) | **부족 (미구현)** | WorldStateManager 확장 시 해소 |

---

## 수정 가치 있는 항목 (재감리 확정)

### 즉시 수정 권장 (P1 — 3건)

| # | 항목 | 난이도 |
|---|------|--------|
| 1 | **TruthGate** — WorldStateManager에 접근자 4개 추가 (`get_deceased_npcs`, `get_owned_items`, `get_destroyed_locations`, `get_known_skills`) | 중 |
| 2 | **rollback** — `reset_after()`에 `vec_episodes`/`foreshadow` DELETE 추가 | 소 |
| 3 | **DBManager 공유 커서** — 121건 잔존 (RLock 방어 중, 장기 기술 부채) | 대 |

### 코드 정리 권장 (P2 — 주요 건)

| # | 항목 | 난이도 |
|---|------|--------|
| 1 | `consistency_validator.py:236` dead expression 삭제 | 1줄 |
| 2 | `stage3_orchestrator.py:773-774` dead code 정리 | 2줄 |
| 3 | `writer_prompt_builders.py:67` `hud_report = hud_report.lower()` 또는 삭제 | 1줄 |
| 4 | `four_phase_arc_generator.py:213` dead expression 삭제 | 1줄 |

### 관찰 대기

- Director Stage 3 비교 시 1,500자 절삭 → 의도적이나, 후반부 품질 비교 제한. 필요 시 확대 검토
- 앙상블 response_schema 적용 → thinking 모드 호환성 확인 후 검토
- 아이템 정규화 통일 → schema가 문자열 강제하므로 현실적 우선순위 낮음
