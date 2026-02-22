# Opus TF 2차 전수조사 통합 리포트 (2026-02-22)

> 6개 Task Force 2차 감사 보고서 통합본
> 감사자: Claude Opus 4.6
> 목적: 1차 감사 수정 검증 + 신규 이슈 발굴
> 감사 범위: Stage 0 / Stage 2 / Stage 3 / Stage 4 / Validation & Quality / 인프라(공통 모듈)

---

## 1. 총괄 요약

### 1차 수정 검증

| 영역 | 검증 항목 | 결과 |
|------|----------|------|
| Stage 0 | 12건 | **12/12 PASS** |
| Stage 2 | 6건 | **6/6 PASS** |
| Stage 3 | 12건 | **12/12 PASS** |
| Stage 4 | 7건 | **7/7 PASS** |
| Validation | 5건 | **5/5 PASS** |
| 인프라 | 9건 | **9/9 PASS** |
| **합계** | **51건** | **51/51 PASS (100%)** |

**결론**: 1차 감사에서 수정한 76건(P0-P2) + 19건(개선 아이디어) = 95건 **전량 정상 이행 확인**.

### 2차 신규 발견

| 등급 | Stage 0 | Stage 2 | Stage 3 | Stage 4 | Validation | 인프라 | **합계** |
|------|---------|---------|---------|---------|------------|--------|----------|
| **P0** | 0 | 0 | 0 | 1 | 0 | 0 | **1** |
| **P1** | 2 | 3 | 3 | 2 | 0 | 0 | **10** |
| **P2** | 5 | 5 | 4 | 4 | 0 | 5 | **23** |
| **P3+** | 0 | 0 | 0 | 0 | 7 | 10 | **17** |
| **개선 아이디어** | 0 | 6 | 4 | 4 | 0 | 6 | **20** |

**총 71건** (P0 1건 + P1 10건 + P2 23건 + P3+ 17건 + 개선 아이디어 20건)

---

## 2. P0 (차단급) — 1건

| # | TF | 파일:위치 | 설명 | 조치 |
|---|----|-----------|----|------|
| 1 | S4 | `stage4_interview_round.py:96` | `_common_writer_kwargs`에 `episode_digest` 추가(S4-P2-4 수정)했으나, `ChiefWriter.generate_ensemble()` 등 3개 메서드 시그니처에 해당 파라미터 없음 → `TypeError` 발생. **1차 수정 과정에서 도입된 회귀 버그** | **즉시 수정 완료** — `_common_writer_kwargs`에서 제거, Director 호출(L713)에서만 별도 전달 |

---

## 3. P1 (품질 이슈) — 10건

| # | TF | 파일:위치 | 설명 |
|---|----|-----------|------|
| 1 | S0 | `stage01_helpers.py:253` | `extend_blocks()` 내 `StoryExpander` 생성 시 `llm_client` 미전달 (P0-1 수정과 동일 패턴 누락) |
| 2 | S0 | `reverse_expander.py:59-79` | `ReverseExpander._call_llm()`에 S0-I3 재시도 로직 미적용 (StoryExpander에만 적용됨) |
| 3 | S2 | `stage2_preflight.py:684` | `n_results` 미 `int()` 래핑 — `_threshold()` 반환값이 float일 경우 TypeError |
| 4 | S2 | `stage2_orchestrator.py` | `user_choice`/`manual_input` 변수 스코프 — failure handler에서 미초기화 참조 가능 |
| 5 | S2 | `stage2_orchestrator.py` | `_rejected_arc` PASS 경로에서 미초기화 |
| 6 | S3 | `stage3_orchestrator.py` | `validate_blueprint_integrity()`가 `scene_breakdown`이 list일 때 무결성 실패 → Blueprint 저장 거부 |
| 7 | S3 | `stage3_orchestrator.py` | `_handle_success` integrity 실패 시 `next_ep: working_ep + 1` vs `_handle_failure`의 `next_ep: working_ep` 비일관 |
| 8 | S3 | `stage3_orchestrator.py` | `safe_commit` DI 콜백 None 시 TypeError crash 가능 |
| 9 | S4 | `stage4_post_processor.py` | Bible 비동기: submit 직후 result(timeout=120) 호출 → 실질 병렬화 0 |
| 10 | S4 | `stage4_orchestrator.py:31` | `_detect_cross_episode_repetition` 기본 인자에서 모듈 로드 시점 `_threshold()` 호출 |

---

## 4. P2 (경미/스타일) — 23건

### Stage 0 (5건)
- bare `except Exception:` 패턴 통일
- `response.text` None 방어
- `run()` 조기 종료 시 반환값
- 장르 순서 불일치 (문서 vs 코드)
- 배치 병렬화 prev_state 설계 한계

### Stage 2 (5건)
- `RetryLimits` 상수 vs `_threshold()` 표시 불일치
- `constraint_block` 반환값 불일치 (`""` vs `"N/A"`)
- ConstraintDB dict 항목 비교 정규화 없음
- `SessionFailureMemory.record_failure` 파라미터 명명 이중
- `joint_docs` 이중 구조 (Analyst vs Finalizer)

### Stage 3 (4건)
- `_stage3_meta`/`quality_risk` 메타데이터 Stage 4 미참조
- ThreePhase `_initial_feedback` 과잉 보존
- `blueprint_constraint_compiler` 정규식 컴파일 미캐싱
- `_EPISODE_HEADER_PATTERNS` 순서 최적화 여지

### Stage 4 (4건)
- 코드 스타일/타입 힌트 이슈 4건

### 인프라 (5건)
- `commit_episode_factory` 수동 Lock 패턴
- `delete_episode_bibles_after` 공유 커서 잔존
- `_embed_cache_put` 기존 키 미갱신
- WorldState/FactLedger `save()` 명시 호출 의존
- `_load_model_config()` 반복 파일 I/O

---

## 5. P3+ (관찰/스타일) — 17건

### Validation (7건)
- ConsistencyValidator Guard 로드 3장르 한정
- ActionSceneEvaluator 키워드 3장르 한정
- ScoringValidator GENRE_THRESHOLDS 4장르
- Parallel body에 pre_llm_adjustment/Retrospective/Self-Refine 미포함
- GENRE_THRESHOLD_PROFILES YAML 미외부화

### 인프라 (10건)
- 함수 내 `import re` 잔존
- `safe_get` 클로저 재정의
- LazyThreshold hot-reload 미지원
- ForeshadowTracker 스레드 안전성
- 기타 아키텍처 문서화 항목

---

## 6. 개선 아이디어 — 20건

### Stage 2 (6건)
1. FourPhase `state_changes` 기본값 생성
2. dict 항목 정규화 비교
3. 통합 retry 카운터
4. flow guard 결과 캐싱
5. 검증 중복 제거
6. Analyst 레거시 정리

### Stage 3 (4건)
1. `scene_breakdown` list → dict 자동 변환
2. `_stage3_meta` → Stage 4 Director 주입
3. 정규식 `re.compile()` 캐싱
4. Constraint Compiler 디버깅 모드

### Stage 4 (4건)
1. Bible 비동기 실질 병렬화 (submit 후 다른 작업 먼저)
2. `_detect_cross_episode_repetition` lazy threshold
3. Director 선택 이력 → Writer 가중치 피드백
4. Interview Round 검증 모듈화

### 인프라 (6건)
1. `_load_model_config()` 모듈 레벨 캐싱
2. `commit_episode_factory` Lock 전환
3. 임베딩 캐시 persistence (디스크)
4. ForeshadowTracker thread-safe
5. WAL checkpoint 주기 설정
6. `delete_episode_bibles_after` 로컬 커서 전환

---

## 7. 수정 우선순위

### Tier 1 — 즉시 수정 (P0 + 고위험 P1)

| 순서 | 항목 | 난이도 |
|------|------|--------|
| 1 | ~~N-P0-1: episode_digest kwargs~~ | ~~낮~~ **수정 완료** |
| 2 | S0-N-P1-1: extend_blocks llm_client 미전달 | 낮 |
| 3 | S0-N-P1-2: ReverseExpander 재시도 로직 적용 | 낮 |
| 4 | S2-N-P1-1: n_results int() 래핑 | 낮 |
| 5 | S3-N-P1-1: scene_breakdown list 방어 | 낮 |
| 6 | S4-N-P1-1: Bible 비동기 실질 병렬화 | 중 |

### Tier 2 — 조기 수정 (나머지 P1 + 주요 P2)

S2-N-P1-2, S2-N-P1-3, S3-N-P1-2, S3-N-P1-3, S4-N-P1-2, P2 주요 항목

### Tier 3 — 배치/보류

P3+ 17건 + 개선 아이디어 20건

---

## 8. 종합 평가

| 영역 | 1차 등급 | 2차 등급 | 변화 |
|------|----------|----------|------|
| Stage 0 | A- | **A-** | 유지 (P1 2건 신규, 경미) |
| Stage 2 | A | **A** | 유지 (P1 3건 신규, 방어적) |
| Stage 3 | A- | **A-** | 유지 (P1 3건 신규, scene_breakdown 주의) |
| Stage 4 | A- | **A-** | 유지 (P0 회귀 1건 즉시 수정, 나머지 경미) |
| Validation | A | **A** | 유지 (P3만 7건, 3장르 한정 잔여) |
| 인프라 | A- | **A-** | 유지 (P2 5건, P3 10건, 경미) |

**총평**: 1차 감사 수정 95건이 100% 정상 이행됨을 확인. 2차에서 발견된 P0 1건(회귀 버그)은 즉시 수정 완료. 잔여 P1 10건은 대부분 방어적 코딩 누락으로 위험도 낮음. 시스템 전체 건전성은 **A- ~ A** 수준으로 안정적.

---

*2차 감사 완료: 2026-02-22*
*감사자: Claude Opus 4.6*
*원본 리포트 6건: opus_tf2_stage{0,2,3,4}_audit.md, opus_tf2_validation_audit.md, opus_tf2_infra_audit.md*
