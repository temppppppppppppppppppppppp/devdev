# OPUS TF 5-Terminal 통합 조사 결과 보고서

> **작성일**: 2026-03-13
> **범위**: 프로덕션 134K lines (239 .py) + 테스트 68K lines (274 .py) + Config/Contract 전량
> **방법론**: 5개 터미널 × 6-Point Inspection + 개별 5Pass 감리 → 교차검증 + 중복제거

---

## 총괄 통계

| Severity | T1 | T2 | T3 | T4 | T5 | 중복제거 | **확정** |
|----------|----|----|----|----|----|---------:|--------:|
| **P0-CRITICAL** | 0 | 1 | 0 | 0 | 0 | 0 | **1** |
| **P1-IMPORTANT** | 1 | 1 | 3 | 7 | 1 | 0 | **13** |
| **P2-MODERATE** | 8 | 14 | 4 | 29 | 31 | -3 | **83** |
| **P3-MINOR** | 22 | 31 | 33 | 20 | 59 | 0 | **165** |
| **합계** | 31 | 47 | 40 | 56 | 91 | -3 | **262** |

---

## 교차검증 결과

### 1. T1-04 ↔ T5-API-03/04/05 — api-contract-v1.yaml 불일치 (중복, T5로 통합)
- **T1-04** (P2): 에러코드 3개 미선언 (`INTERNAL_ERROR`/`INVALID_PROJECT`/`INVALID_REQUEST`)
- **T5-API-03** (P2): 포트 8000 vs 실제 8300
- **T5-API-04** (P2): 동일 에러코드 3개 미등재
- **T5-API-05** (P2): 엔드포인트 4개 미등재
- **판정**: T1-04와 T5-API-04는 동일 이슈 → **T5-API-04에 통합**, T1-04 삭제. T5-API-03/05는 T1 미발견 추가 이슈로 유지.

### 2. T3-029 ↔ T4-P1-01/02/03/04 — 대원칙 3 (Director 주권) 위반 클러스터
- **T3-029** (P1): Stage3 continuity pin이 Director PASS Blueprint를 폐기
- **T4-P1-01** (P1): Stage3 ConsistencyValidator unjustifiable → auto REJECT
- **T4-P1-02** (P1): Stage3 RetrospectiveValidator CRITICAL → auto REJECT score=0
- **T4-P1-03** (P1): single BP Python-only PASS (Director LLM 미호출)
- **T4-P1-04** (P1): 적응형 PASS→REJECT (Python이 Director PASS를 뒤집음)
- **판정**: 모두 상이한 코드 경로에서 발생. 중복 없음. **전량 유지**. 대원칙 3 위반이 5건으로 가장 큰 결함 클러스터.

### 3. T3-003/004 ↔ T4 — 테스트 갭 교차영역
- **T3-003** (P1): Blueprint→Manuscript 핸드오프 통합 테스트 부재
- **T3-004** (P1): Advisory Chain 병렬 실행 테스트 부재
- **T4-P2-A01/A02**: Advisory 데이터 흐름 이슈 (다른 문제)
- **판정**: 각각 다른 이슈. 중복 없음.

### 4. T1-01/02/03 ↔ T5 — HUD 하드코딩 vs 장르
- **T1-01** (P1): RESET.py MartialHUD 하드코딩
- **T1-02/03** (P2): project_manager.py NPC_Martial_HUD / MartialHUD 하드코딩
- **T5**: Genre Guard 범위이나 HUD 관련 보고 없음
- **판정**: T1 고유 발견. 교차검증 충돌 없음.

### 5. T2-001 (P0) — Stage 2 진입 차단
- T3에서 "Stage 2 출력" 관련 검사했으나, Stage 2 자체 진입 불가 이슈는 T2 고유 범위.
- **판정**: 교차검증 추가 발견 없음.

---

## 중복제거 기록

| 삭제 항목 | 통합 대상 | 사유 |
|-----------|----------|------|
| T1-04 (P2) | T5-API-04 (P2) | 동일 이슈: api-contract 에러코드 3개 미선언. T5가 더 포괄적 |
| T1-04 건수 | T5-API-03~05 클러스터 | 포트/에러코드/엔드포인트를 T5가 일괄 커버 |
| T4-P2-CF01 "NC-3 17개→20개" | T3-040 (P3) | Self-Critique 개수 불일치 동일 근본 원인. T4가 director.yaml 4곳 특정으로 더 상세 → T4 유지, T3-040은 CLAUDE.md 문서 갱신으로 분리 |

**순 삭제: 3건** (T1-04 → T5 통합, T3-040 CLAUDE.md 부분은 T5 문서갱신에 통합)

---

## P0 — CRITICAL (1건)

### [T2-001] 컨셉 플로우 Treatment → plot_roadmap 미주입 — Stage 2 진입 불가
- **터미널**: T2
- **파일**: `modules/core/stage01_helpers.py` L501-538, `modules/core/stage0/story_expander.py` L229-253
- **현상**: 컨셉 플로우로 Bible+Treatment 생성 시 Treatment가 Bible의 `plot_roadmap`에 주입되지 않음. Stage 2가 빈 `[]`을 받아 "모든 아크 완료"로 즉시 종료.
- **근거**: `plot_roadmap`은 `force_sync_v25_dna()`(레거시)와 `_s0_handle_block_extension()`에서만 주입. 컨셉 플로우 경로에 0건.
- **수정안**: `_s0_save_results()` 내에서 treatment 존재 시 `bible["MasterBible"]["plot_roadmap"]` 주입.

---

## P1 — IMPORTANT (13건)

### 대원칙 3 위반 클러스터 (5건)

| # | ID | 파일 | 현상 |
|---|-----|------|------|
| 1 | **T3-029** | `stage3_orchestrator.py` L1479-1492 | Director PASS Blueprint를 continuity pin이 무효화 → fail_count+1, BP 미저장 |
| 2 | **T4-P1-01** | `validation_orchestrator.py` L468-482 | ConsistencyValidator unjustifiable → Stage3 경로에서 auto REJECT |
| 3 | **T4-P1-02** | `validation_orchestrator.py` L656-667 | RetrospectiveValidator CRITICAL → Stage3 경로에서 score=0 auto REJECT |
| 4 | **T4-P1-03** | `director_ensemble.py` L471-478 | 단일 BP가 기본 기준 충족 시 Director LLM 호출 없이 Python-only PASS |
| 5 | **T4-P1-04** | `director_ensemble.py` L1246-1256 | 적응형 PASS→REJECT: Director PASS를 Python score 기준으로 뒤집음 |

### 데이터 무결성 (3건)

| # | ID | 파일 | 현상 |
|---|-----|------|------|
| 6 | **T1-01** | `RESET.py` L86 | HUD 롤백이 MartialHUD 하드코딩 → 비무협 장르 KeyError/데이터 손상 |
| 7 | **T2-002** | `stage01_helpers.py` L370-424 | 역설계 플로우 plot_roadmap 미주입 → Stage 2 진입 불가 (P0보다 영향 적음) |
| 8 | **T5-WS-016** | `fact_ledger.py` L220-255 | FactLedger 사망NPC 가드 0건 (WorldState는 5개 섹션 전부 가드 존재) — 대원칙 4 관련 |

### 코드 품질 / 테스트 갭 (5건)

| # | ID | 파일 | 현상 |
|---|-----|------|------|
| 9 | **T3-003** | 테스트 전체 | Blueprint→Manuscript 핸드오프 통합 테스트 부재 |
| 10 | **T3-004** | `test_stage4_interview_round.py` | Advisory Chain 병렬 실행(ThreadPoolExecutor) 직접 테스트 부재 |
| 11 | **T4-P1-05** | `blocking_validator_scene_checks.py` L44-51 | `_check_required_scenes` 항상 passed=True — 비활성 dead code |
| 12 | **T4-P1-06** | `pre_director_manuscript_checker.py` L43-63 | 미사용 변수 3건 (dialogue_patterns, dialogue_count 덮어씌움, ratio_diff #noqa) |
| 13 | **T4-P1-07** | `test_continuity_validator.py` | ContinuityValidator 5/6 서브체크 직접 테스트 부재 |

---

## P2 — MODERATE (83건, 카테고리별 요약)

### 비무협 장르 오염 / HUD 하드코딩 (3건)
| ID | 파일 | 요약 |
|----|------|------|
| T1-02 | `project_manager.py` L504/538 | NPC_Martial_HUD 하드코딩 → 비무협 NPC HUD 변화 무시 |
| T1-03 | `project_manager.py` L227 | Bible 저장 시 MartialHUD 하드코딩 → 비무협 HUD 동기화 미실행 |
| T5-GG-001 | `fantasy_guard.py` L347 | `_is_figurative_use()` 필터 누락 → 비유적 사용 오탐 |

### API Contract 불일치 (5건)
| ID | 파일 | 요약 |
|----|------|------|
| T5-API-01 | `process_runner.py` / `api-contract-v1.yaml` | State enum 불일치 (starting/waiting_input) |
| T5-API-03 | `api-contract-v1.yaml` L6 | 포트 8000 vs 실제 8300 |
| T5-API-04 | `api-contract-v1.yaml` L190 | 에러코드 3개 미등재 (T1-04 통합) |
| T5-API-05 | `api-contract-v1.yaml` | 엔드포인트 4개 미등재 |
| T5-API-06 | `bridge_server.py` L605 | DBManager private 메서드 + raw SQL 접근 |

### DB / 데이터 흐름 (8건)
| ID | 파일 | 요약 |
|----|------|------|
| T1-06 | `db_manager.py` L1039 | execute_update() commit 누락 — 호출자 의존 |
| T1-07 | `db_manager.py` 다수 | 공유 cursor ~185회 사용 (레거시) |
| T1-09 | `project_service.py` L101-370 | raw cursor 15곳 — DBRepositoryProtocol 우회 |
| T2-022 | `reverse_expander.py` L1147 | save_anchor 이중 호출 |
| T2-023 | `stage01_helpers.py` L501 | genre_info anchor 비저장 |
| T5-NAR-06 | `foreshadow_tracker.py` L431 | DELETE+INSERT 트랜잭션 부분 실패 |
| T5-AUX-16 | `lore_manager.py` L209 | DBManager cursor 직접 접근 (lock 우회) |
| T5-AUX-18 | `quality_sidecar_bootstrap.py` L113 | DB private 멤버 직접 접근 |

### Stage 0→2 파이프라인 (8건)
| ID | 파일 | 요약 |
|----|------|------|
| T2-003 | `reverse_expander.py` L383 | `_extract_single_episode_bible` KeyError on missing ep_num |
| T2-004 | `story_expander.py` L210 | generate_bible() 반환 타입 None vs dict 불일치 |
| T2-005 | `analyst.py` L699 | Gemini 전용 config 타입 (멀티프로바이더 장애) |
| T2-011 | `arc_critic.py` L253 | falsy 빈 리스트 `or` 패턴 → 잘못된 리스트에서 아이템 제거 |
| T2-012 | `unified_arc_validator.py` L293 | `timeline` 미생성 (레거시 Analyst path) |
| T2-015 | `stage2_finalizer.py` L1337 | REJECT 메트릭 selected_strategy 항상 퇴화 |
| T2-019 | `stage0/__init__.py` L461 | 빈 bible_path → Path("") 플랫폼 의존 |
| T2-021 | `stage01_helpers.py` L370 | bible 변수 미초기화 → UnboundLocalError |

### Stage 3→4 파이프라인 (4건)
| ID | 파일 | 요약 |
|----|------|------|
| T3-006 | `unified_blueprint_validator.py` L413 | scene_keys 알파벳 정렬 (10+씬 오류) |
| T3-007 | `block_enricher.py` L480 | self.primary_model 스레드 안전 미비 |
| T3-018 | `chief_writer_quality.py` L766 | Self-Critique #6 str/dict 혼재 → severity 에스컬레이션 누락 |
| T3-019 | `chief_writer_quality.py` L791 | Self-Critique #7 동일 패턴 |

### Director / Validation (9건)
| ID | 파일 | 요약 |
|----|------|------|
| T4-P2-D01 | `director_grading.py` L686 | is_approved: rejected 있어도 applied>0이면 승인 |
| T4-P2-D02 | `director_ensemble.py` L443 | single BP 반환 dict 필드 누락 |
| T4-P2-D03 | `director_ensemble.py` L1092 | NC-3B 자동교정 상향 시 로깅 부재 |
| T4-P2-D04 | `director_auditor.py` L534 | Entity REJECT이 Director 본 감사 우회 |
| T4-P2-D05 | continuity 5파일 | 사망 캐릭터 직접 필터 부재 (다중 방어 존재) |
| T4-P2-V01 | `continuity_validator.py` L124 | DEGRADED fail-closed — ep=1에서도 passed=False |
| T4-P2-V03 | `validation_orchestrator.py` L1178 | PRE_LLM REJECT dead code |
| T4-P2-V04 | `validation_orchestrator.py` | UNCONDITIONAL_PASS_FLOOR=85 cliff edge |
| T4-P2-Q01 | `confidence_calibration.py` L181 | narration_ratio 음수 가능 |

### Continuity 체계 (4건)
| ID | 파일 | 요약 |
|----|------|------|
| T4-P2-C01 | `continuity_manuscript.py` L210 | inspect_manuscript 메인 파이프라인 미사용 dead code |
| T4-P2-C02 | `continuity_blueprint.py` L248 | Blueprint critical_violations 미병합 |
| T4-P2-C03 | `continuity_manuscript.py` L1167 | inspect_manuscript_v59에 entity_registry 미전달 |
| T4-P2-C04 | `continuity_manuscript.py` L199 | ACQUISITION_PATTERNS 2개 vs 4개 불일치 |

### Config / Prompt (4건)
| ID | 파일 | 요약 |
|----|------|------|
| T4-P2-CF01 | `director.yaml` 4곳 | NC-3 "17개" → 실제 20개 |
| T4-P2-CF02 | `director.yaml` L810-898 | STRATEGIC_AUDIT Output Format 불일치 |
| T4-P2-CF03 | `director.yaml` L1068 | DIRECTOR_AUDIT NC 관련 필드 불일치 |
| T4-P2-CF04 | `director.yaml` L871 | Ensemble 전용 공식 혼입 |

### Advisory / 품질 (6건)
| ID | 파일 | 요약 |
|----|------|------|
| T4-P2-A01 | `stage4_interview_round.py` L1528 | NumericConsistency advisory_summary 누락 |
| T4-P2-A02 | `stage4_interview_round.py` L3713 | validation_results dict 동시 스레드 접근 |
| T4-P2-Q02 | `quality_constitution.py` L279 | fantasy 장르 Amendment 누락 |
| T4-P2-Q03 | `quality_dashboard.py` L124 | 인스턴스 메서드 스레드 보호 없음 |
| T4-P2-Q04 | `quality_amplifier.py` L348 | 무협 전용 아이템 패턴이 비무협에도 적용 |
| T4-P2-Q05 | `quality_dashboard.py` L1209 | 싱글톤 project_path 변경 무시 |

### Genre Guard / Domain (7건)
| ID | 파일 | 요약 |
|----|------|------|
| T5-GG-004 | `hunter_guard.py` L644 | `_compare_ranks` ValueError → 0 (동등 판정) |
| T5-GG-014 | `work_guard.py` | `validate_v20_manuscript` 오버라이드 없음 |
| T5-GG-015 | `work_guard.py` L794 | warning_violations 반환 계약 불일치 |
| T5-GG-016 | `style_guard.py` L99 | WorkGuard warning 전량 소실 |
| T5-NAR-08 | `semantic_item_registry.py` L553 | "팽무진" 하드코딩 (3곳) |
| T5-NAR-09 | `semantic_item_registry.py` L451 | T5-NAR-08과 동일 |
| T5-NAR-13 | `information_diffusion.py` L392 | propagate_event 5→3단계 불일치 |

### 보조 모듈 (8건)
| ID | 파일 | 요약 |
|----|------|------|
| T5-AUX-01 | `adversarial_self_play.py` L267 | 빈 dict → 빈 JSON adversary loop 진입 |
| T5-AUX-05 | `cross_agent_verifier.py` L396 | 원고 8K 절삭 → 엔딩훅 누락 |
| T5-AUX-06 | `data_collector.py` L183 | thread-safety 없음 |
| T5-AUX-07 | `data_collector.py` L96 | stats 카운터 lock 밖에서 갱신 |
| T5-AUX-10 | `reference_anchor.py` L104 | BaseAgent private 메서드 호출 |
| T5-AUX-14 | `martial_manager.py` L369 | 내공 강제 회복 — 대원칙 1 경계 |
| T5-AUX-15 | `martial_manager.py` L409 | save_v20_anchor 존재 미검증 |
| T5-AUX-19 | `investment_arithmetic_checker.py` L303 | 배열 길이 불일치 시 불완전 합산 |

### Desktop / API 추가 (3건)
| ID | 파일 | 요약 |
|----|------|------|
| T5-API-02 | `geuldobi-desktop/src/main.js` L192 | startupTimer 미정리 → null 참조 |
| T5-API-07 | `geuldobi-desktop/main.js` | 구버전 dead file |
| T5-NAR-17 | `semantic_item_registry.py` L785 | 싱글톤 크로스프로젝트 오염 |

### 테스트 갭 (14건)
| ID | 파일 | 요약 |
|----|------|------|
| T1-13 | RESET.py | 테스트 부재 (P1 버그 regression 방지 필수) |
| T2-018 | `stage2_validation_pipeline.py` | retry 반환 계약 불명확 |
| T2-020 | `stage0/__init__.py` L651 | save_state OSError 방어 없음 |
| T2-052 | 테스트 전체 | Arc 에이전트 6개 핵심 모듈 전용 테스트 부재 |
| T4-P2-T01~T05 | 테스트 5건 | CatharsisTimer/BlockingValidator/DirectorContinuity/NumericConsistency 테스트 갭 |
| T4-P2-V02 | `test_consistency_validator.py` | ConsistencyValidator 5개 서브체크 통합 테스트 부재 |
| T5-WS-011 | `state_tracker.py` L187 | full_extract 핵심 4종 예외 시 전체 arc 중단 |
| T5-WS-020 | 테스트 전체 | rollback_to 테스트 부재 |
| T5-NAR-03 | `information_diffusion.py` L51 | O(N) DB 호출 100화+ 시 성능 |

---

## P3 — MINOR (165건, 터미널별 통계만)

| 터미널 | 건수 | 주요 카테고리 |
|--------|------|--------------|
| T1 | 22 | 독스트링 불일치, Protocol 시그니처, dead code, 스레드 형식적 안전성 |
| T2 | 31 | mojibake, dead code, 테스트 커버리지 갭, 문서화 부재 |
| T3 | 33 | 의도적 설계 하향 8건 + dead code 4건 + 문서 불일치 + 테스트 갭 |
| T4 | 20 | Dead code, 프롬프트 불일치, 비대칭 반환 |
| T5 | 59 | 테스트 커버리지 15건 + 코드 위생 + 하드코딩 모델명 + 문서 부정확 |

상세 내용은 각 터미널 보고서 참조:
- `OPUS-TF-T1-infrastructure-findings.md`
- `OPUS-TF-T2-stage0-to-stage2-consolidated-findings.md`
- `T3-stage3-4-pipeline-audit-report.md`
- `T4-quality-advisory-audit-findings.md`
- `OPUS-TF-T5-domain-auxiliary-findings.md`

---

## 대원칙 준수 현황 (전 터미널 교차검증)

| 대원칙 | 상태 | 위반 건수 | 비고 |
|--------|------|----------|------|
| **1. Python 수집만, 판단은 LLM** | 대체로 준수 | 경계 1건 | T5-AUX-14 내공 강제 회복 (P2) |
| **2. 팩트시트 수정은 LLM만** | **완전 준수** | 0건 | — |
| **3. Director 주권주의** | **위반 5건** | 5건 | T3-029, T4-P1-01/02/03/04 (최대 결함 클러스터) |
| **4. 사망 캐릭터** | 대체로 준수 | 1건 | T5-WS-016 FactLedger 가드 부재 (P1) |

---

## 문서 갱신 필요 항목

| 항목 | 현재 | 실제 | 출처 |
|------|------|------|------|
| CLAUDE.md protagonist_items | "14파일 21곳" | **18파일 35곳** | T5 전수조사 |
| CLAUDE.md 비무협 3단 방어 | "truth_gate.py P2" | **chief_writer_quality._check_system_term_exposure()** | T5 교차검증 |
| CLAUDE.md Self-Critique | "15개" | **17+1개 (18개)** | T3-040 |
| director.yaml NC-3 | "17개" | **20개** (4곳) | T4-P2-CF01 |

---

## 액션 플랜 — 수정 우선순위

### 즉시 (P0, 1건)

| 순위 | ID | 작업 | 예상 규모 |
|------|-----|------|----------|
| **1** | T2-001 | 컨셉 플로우 plot_roadmap 주입 — Stage 2 진입 차단 해소 | 5줄 |

### 1순위 (P1 대원칙 3 위반, 5건)

| 순위 | ID | 작업 | 예상 규모 |
|------|-----|------|----------|
| **2** | T3-029 | continuity pin이 Director PASS 무효화 방지 — pin 결과를 Director 심사 전 주입 또는 PASS BP 저장+경고 | 15줄 |
| **3** | T4-P1-04 | 적응형 PASS→REJECT 하향 제거 — Director PASS 존중 | 10줄 |
| **4** | T4-P1-01 | ConsistencyValidator unjustifiable → TF-36 advisory 변환 (Stage 3 경로) | 20줄 |
| **5** | T4-P1-02 | RetrospectiveValidator CRITICAL → TF-36 advisory 변환 (Stage 3 경로) | 15줄 |
| **6** | T4-P1-03 | single BP Python-only PASS → LLM 간소 판정 위임 | 15줄 |

### 2순위 (P1 데이터 무결성, 3건)

| 순위 | ID | 작업 | 예상 규모 |
|------|-----|------|----------|
| **7** | T1-01 | RESET.py HUD 하드코딩 → `HUDKeys.get_hud_root(genre)` | 5줄 |
| **8** | T2-002 | 역설계 플로우 plot_roadmap 주입 | 10줄 |
| **9** | T5-WS-016 | FactLedger 사망NPC 가드 5개 섹션 추가 | 10줄 |

### 3순위 (P1 테스트/코드 위생, 5건)

| 순위 | ID | 작업 | 예상 규모 |
|------|-----|------|----------|
| **10** | T3-003 | Blueprint↔Manuscript 필드 계약 테스트 신규 | 50줄 |
| **11** | T3-004 | Advisory Chain 병렬 실행 단위 테스트 신규 | 80줄 |
| **12** | T4-P1-07 | ContinuityValidator 5/6 서브체크 테스트 보강 | 100줄 |
| **13** | T4-P1-05 | _check_required_scenes dead code 축소 | 5줄 |
| **14** | T4-P1-06 | pre_director_manuscript_checker 미사용 변수 삭제 | 3줄 |

### 4순위 (P2 핵심, 영향도 순 상위 10건)

| 순위 | ID | 작업 |
|------|-----|------|
| **15** | T1-02/03 | project_manager HUD 하드코딩 → 동적 장르 키 |
| **16** | T2-011 | ArcCritic falsy 빈 리스트 or 패턴 수정 |
| **17** | T2-021 | bible 변수 미초기화 수정 |
| **18** | T5-GG-016 | StyleGuard warning_violations 전파 |
| **19** | T5-NAR-08/09 | "팽무진" 하드코딩 제거 |
| **20** | T5-NAR-13 | propagate_event 5→3단계 불일치 수정 |
| **21** | T3-007 | block_enricher 스레드 안전 수정 |
| **22** | T5-API-03~05 | api-contract-v1.yaml 현행화 |
| **23** | T4-P2-CF01 | director.yaml NC-3 20개로 수정 (4곳) |
| **24** | T3-018/019 | Self-Critique issues dict 형식 통일 |

### 5순위 (나머지 P2 73건 + P3 165건)
- 각 터미널 보고서의 우선순위 액션 플랜 참조
- P3 165건은 마스터 일괄 진행

---

*5-Terminal 통합 조사 완료. P0=1, P1=13, P2=83, P3=165. 총 262건 확정.*
