# OPUS TF 5-Terminal 디테일 전량 마스터 조사 오더 (2차)

> **작성일**: 2026-03-13
> **목적**: 1차 마스터 오더(거시 건강성)에서 누락된 세부 디테일 영역 전량 적출
> **배경**: 1차 감사에서 명시적으로 열거한 파일은 전체의 약 60%. 나머지 40%(미열거 모듈 23개, 미열거 테스트 229개, 미열거 스크립트 16개, 미열거 Config 23+개, 모델 계층, 전처리 SSOT 문서·스키마)가 감사 사각지대.
> **방법**: 각 터미널이 **자체 3PASS 감리**를 수행하여 오탐을 최소화한 후 보고

---

## 0. 1차 대비 2차 차이점

| 항목 | 1차 마스터 | 2차 마스터 (본 문서) |
|------|-----------|---------------------|
| 초점 | 핵심 프로덕션 모듈 (열거된 239 .py) | 1차에서 **미열거된** 모든 파일 + 1차 열거 파일의 **교차 경계 디테일** |
| 감리 | 마스터가 3PASS | **각 터미널이 자체 3PASS** + 마스터 최종 1PASS |
| 오탐 방지 | 금지사항 4개 | 금지사항 4개 + **자체 3PASS 오탐 제거 프로토콜** |
| 보고 형식 | `[TN-SEQ]` | `[D-TN-SEQ]` (Detail prefix) |

---

## 1. 자체 3PASS 감리 프로토콜 (전 터미널 공통)

> **핵심 원칙**: 발견 → 검증 → 확정. 3PASS를 거치지 않은 항목은 보고 금지.

### PASS 1 — 초벌 스캔 (발견)
- 담당 범위 전 파일을 읽고, 6-Point Inspection 적용
- 의심되는 결함을 **후보 목록**에 전부 기록 (오탐 가능성 높아도 일단 기록)
- 후보마다 `확신도: HIGH/MED/LOW` 태깅

### PASS 2 — 교차 검증 (검증)
- PASS 1 후보 각각에 대해:
  - **코드 증거 재확인**: 해당 라인을 다시 읽고, 호출자/피호출자까지 추적
  - **CLAUDE.md 대조**: 의도적 설계(문서화된 패턴)인지 확인 → 의도적이면 **오탐 제거**
  - **테스트 대조**: 관련 테스트가 이미 해당 분기를 검증하는지 확인 → 테스트 통과 중이면 근거 보강 또는 오탐 제거
  - **경계 파일 확인**: 다른 터미널 범위의 파일이 관련될 경우, 해당 파일도 읽어서 확인
- 확신도 재평가: `HIGH` 유지 항목만 PASS 3으로 진행. `MED`는 근거 보강 후 진행 여부 결정. `LOW`는 제거.

### PASS 3 — 최종 확정 (확정)
- PASS 2 통과 항목만 대상
- 각 항목의 **수정안 실현 가능성** 검토 (수정이 다른 곳을 깨뜨리지 않는지)
- 최종 Severity 배정 (P0~P3)
- **보고서 작성**: 확정된 항목만 `[D-TN-SEQ]` 형식으로 보고
- 보고서 말미에 **오탐 제거 로그** 첨부: `PASS 1에서 N개 후보 → PASS 2에서 M개 제거 → 최종 K개 확정`

### 오탐 판정 기준 (제거 사유)
| 코드 | 사유 | 예시 |
|------|------|------|
| FP-1 | CLAUDE.md 문서화된 의도적 설계 | NC-1 자동감점 없음은 대원칙 3 준수 |
| FP-2 | 테스트가 이미 해당 분기를 검증 | pytest passed 상태에서 정상 동작 확인 |
| FP-3 | 호출자 추적 결과 dead path 아님 확인 | 실제 런타임에서 도달 가능 |
| FP-4 | 다른 터미널 범위와 교차 확인 후 정상 | 경계 파일 양쪽 읽기 완료 |
| FP-5 | 코드 컨벤션/스타일 차이 (동작 무관) | 로깅 형식 차이 등 |

---

## 2. 터미널 영역 분할 (디테일 초점)

```
┌─────────────────────────────────────────────────────────────────────┐
│              2차 디테일 감사 — 5개 터미널 영역 지도                    │
├──────────────┬──────────────┬──────────────┬──────────────┬─────────┤
│  Terminal 1  │  Terminal 2  │  Terminal 3  │  Terminal 4  │ Term. 5 │
│ 미열거 인프라  │ 미열거 에이전트 │ 미열거 테스트  │ Config/계약   │ 스크립트 │
│ & 유틸리티    │ & 모델 계층   │ (229개 전수)  │ & SSOT 문서  │ & 프런트 │
│ 12개 모듈    │ 11개 모듈    │ 229개 테스트  │ 23+ Config   │ 16 스크립트│
│ + __init__   │ + models/*   │ + chaos/prop │ + 계약 스키마  │ + Desktop│
│ + 교차 경계   │ + 교차 경계   │ + e2e/integ  │ + 전처리 문서  │ + 교차   │
└──────────────┴──────────────┴──────────────┴──────────────┴─────────┘
```

---

## 3. Terminal 1 — 미열거 인프라 모듈 & 유틸리티

### 담당 범위

**미열거 Core 유틸리티** (1차에서 빠진 모듈)
| 파일 | 역할 (추정) |
|------|------------|
| `modules/core/arc_summary_utils.py` | Arc 요약 유틸리티 |
| `modules/core/config_manager.py` | 설정 관리자 |
| `modules/core/logging_keys.py` | 로깅 키 정의 |
| `modules/core/soft_failure.py` | 소프트 실패 처리 |
| `modules/core/state_text_verifier.py` | 상태 텍스트 검증 |
| `modules/core/studio_visualizer.py` | 스튜디오 시각화 |
| `modules/core/writer_prompt_builders.py` | Writer 프롬프트 빌더 |
| `modules/core/quality_signal_metrics.py` | 품질 시그널 메트릭 |
| `modules/core/reflexion_manager.py` | Reflexion 관리 |
| `modules/core/constitutional_checker.py` | 헌법적 준수 체크 |
| `modules/core/continuity_pin_guard.py` | 연속성 핀 가드 |
| `modules/core/investment_math_verifier.py` | 투자 수학 검증 (checker와 별개) |

**`__init__.py` 전량** (패키지 구조 정합성)
| 파일 |
|------|
| `modules/__init__.py` |
| `modules/core/__init__.py` |
| `modules/core/stage0/__init__.py` (774줄 — 실제 로직 포함) |
| `modules/core/genre_guards/__init__.py` |
| `modules/core/providers/__init__.py` |
| `modules/core/services/__init__.py` |
| `modules/domain/__init__.py` |
| `modules/domain/agents/__init__.py` |
| `modules/models/__init__.py` |
| `modules/protocols/__init__.py` |
| `modules/validation/__init__.py` |
| `modules/api/__init__.py` |

**교차 경계 검사**: 위 모듈들이 1차 감사 대상 모듈과 올바르게 연결되는지 (import 체인, 호출 관계)

### 핵심 검사 포인트

1. **생존 여부**: 각 모듈이 실제로 import되어 사용되는가, dead code인가
2. **`__init__.py` re-export**: 패키지 `__init__`에서 re-export하는 심볼이 실제 존재하는가
3. **stage0/__init__.py 774줄**: 1차에서 열거했지만 디테일 미검사 — 내부 로직의 None guard, 분기 정합성
4. **config_manager ↔ prompt_loader ↔ constants**: 설정 로딩 3중 경로 간 충돌·중복 없는가
5. **soft_failure ↔ error_helper**: 에러 처리 이중 경로 정합성
6. **investment_math_verifier ↔ investment_arithmetic_checker**: 두 모듈 역할 분리 명확한가, 중복 로직 없는가
7. **constitutional_checker ↔ quality_constitution**: 유사명 모듈 간 역할 구분

---

## 4. Terminal 2 — 미열거 에이전트 & 모델 계층

### 담당 범위

**미열거 Domain Agents**
| 파일 | 역할 (추정) |
|------|------------|
| `modules/domain/agents/consensus_validator.py` | 합의 검증 |
| `modules/domain/agents/constraint_compiler.py` | 제약 조건 컴파일 |
| `modules/domain/agents/critic.py` | 범용 비평 에이전트 |
| `modules/domain/agents/manager.py` | 매니저 에이전트 |
| `modules/domain/agents/preflight_checker.py` | 프리플라이트 체크 |
| `modules/domain/agents/weaver.py` | 위버 에이전트 |

**모델 계층** (1차 PASS 3에서 언급만, 줄수·디테일 미검사)
| 파일 | 역할 |
|------|------|
| `modules/models/arc.py` | Arc 데이터 모델 |
| `modules/models/blueprint.py` | Blueprint 데이터 모델 |
| `modules/models/manuscript.py` | Manuscript 데이터 모델 |
| `modules/models/npc.py` | NPC 데이터 모델 |
| `modules/models/__init__.py` | 모델 re-export |

**base_agent.py 디테일** (1차에서 T1 범위 제외, T3에 "부분" 배정)
| 파일 | 줄수 |
|------|------|
| `modules/domain/agents/base_agent.py` | ~1,820 |

**교차 경계 검사**: 에이전트 → 모델 → DB 계층 데이터 흐름 추적

### 핵심 검사 포인트

1. **에이전트 생존 여부**: 6개 미열거 에이전트가 실제 호출되는가, 어떤 Stage에서 사용되는가
2. **모델 스키마 정합성**: `arc.py`/`blueprint.py`/`manuscript.py`/`npc.py`의 필드가 DB 테이블 + LLM 응답 스키마와 1:1 대응하는가
3. **base_agent.py Context Caching**: 1,820줄 중 캐싱 로직(L1599-1820)의 TTL/eviction/에러 처리 디테일
4. **constraint_compiler ↔ blueprint_constraint_compiler**: 두 모듈 간 역할 분리, 중복 로직 여부
5. **critic.py ↔ arc_critic.py**: 범용 vs 특화 critic 역할 구분
6. **모델 필드명 주의**: `protagonist_items` vs `items_acquired` 폴백이 모델 계층에서도 처리되는가
7. **Pydantic/dataclass 검증**: 모델 클래스의 validation 로직이 런타임 데이터와 정합하는가

---

## 5. Terminal 3 — 미열거 테스트 전수 감사 (229개)

### 담당 범위

**1차에서 명시적으로 열거되지 않은 테스트 파일 전량** — 아래 카테고리별 전수 검사:

**Sweep/Fix/Patch 테스트** (~40개)
- `test_sweep*.py` (17~39 등 번호대별)
- `test_stage234_fixes.py`, `test_stage01_fixes.py`
- `test_warn234_fixes.py`, `test_phase5_hygiene.py`
- `test_inplace_reliability.py`, `test_pass_with_fix.py`

**에이전트/모듈 단위 테스트** (~60개)
- `test_arc_draft_validator.py`, `test_arc_patch_mode.py`, `test_arc_retry.py`
- `test_blueprint_patch_mode.py`, `test_blueprint_preflight.py`
- `test_chief_writer_context.py`, `test_chief_writer_quality.py`
- `test_truth_gate.py`, `test_flashback_verifier.py`
- `test_npc_drift_advisor.py`, `test_long_term_repetition.py`
- `test_fact_ledger.py`, `test_world_state_caps.py`
- `test_llm_router.py`, `test_llm_schema.py`
- `test_config_manager.py`, `test_session_logger.py`
- 기타 전량

**기능/통합 테스트** (~30개)
- `test_a2_open_review_cw.py`, `test_a3_fix_scope_tracking.py`, `test_a4_failure_pattern.py`
- `test_b4_motivation_critique.py`
- `test_tf10_episode_details.py`, `test_tf29_open_review.py`, `test_tf3_threshold_alignment.py`
- `test_v55_modules.py`, `test_v73_capital_fix.py`, `test_v74_treatment_flow.py`
- `test_v75b_escalation.py`, `test_v75c_contradiction_firewall.py`, `test_v75d_graduated_escalation.py`

**Chaos 테스트** (7개 전량)
- `tests/chaos/test_dead_npc_resurrection.py`
- `tests/chaos/test_blueprint_none_injection.py`
- `tests/chaos/test_partial_commit_recovery.py`
- `tests/chaos/test_rollback_boundary.py`
- `tests/chaos/test_feedback_loop.py`
- `tests/chaos/test_stage3_metrics.py`
- 기타

**Property 테스트** (4개 전량)
- `tests/property/` 하위 전량

**E2E/Smoke/Integration 테스트** (~15개)
- `tests/e2e/test_l3_golden_route.py`
- `tests/e2e/test_l3_stage2_realproject.py`
- `tests/e2e/test_lm_advisory_smoke.py`
- `tests/e2e/test_smoke_pipeline.py`
- `tests/integration/test_patch_wiring.py`
- `tests/integration/test_pipeline_smoke.py`

**미분류/신규** (~80개)
- 위 카테고리에 포함되지 않은 나머지 전량

### 핵심 검사 포인트

1. **Dead 테스트**: import 에러로 collect 단계에서 skip되는 테스트 파일이 있는가
2. **Mock 과잉**: MagicMock이 실제 프로덕션 동작을 완전히 대체하여 검증력이 0인 테스트
3. **Assertion 부재**: `assert` 없이 "실행만 되면 통과"하는 빈 테스트
4. **Fixture 부정합**: 테스트 fixture가 현재 프로덕션 코드의 시그니처와 불일치
5. **Chaos 테스트 실효성**: 실제 경계 조건을 테스트하는가, 아니면 형식만 갖춘 것인가
6. **E2E 테스트 환경 의존성**: 특정 DB/네트워크/API 키 없이 실행 가능한가
7. **중복 테스트**: 동일 분기를 여러 파일에서 반복 검증하는 비효율
8. **xfail 68개**: 각 xfail의 사유가 여전히 유효한가, 이미 수정되었지만 xfail이 남은 것은 없는가

---

## 6. Terminal 4 — Config, Contract, SSOT 문서 전수 감사

### 담당 범위

**미열거 Config 파일**
| 파일/경로 | 역할 (추정) |
|-----------|------------|
| `config/smart_retrieval/genre_hints.yaml` | 장르 힌트 설정 |
| `config/cash/style_seeds_final.txt` | 스타일 시드 데이터 |
| `config/style_references/investment/style_guide.json` | 투자물 스타일 가이드 |
| `config/style_references/investment/style_guide_test.json` | 테스트용 스타일 가이드 |
| `config/prompts/*.yaml` — 1차에서 4개만 명시, 나머지 ~39개 | 외부화 프롬프트 전량 |
| `config/genres/*.yaml` — 10개 장르 정의 | 장르별 YAML 전량 |
| `config/prompts/analyst_libraries_*.json` — 11개 | 장르별 분석 라이브러리 |

**Contract & 스키마** (1차에서 "9개"로 뭉뚱그린 것의 개별 검사)
| 파일 | 역할 |
|------|------|
| `전처리_ssot/contracts/artifact_contracts.json` | 아티팩트 계약 |
| `전처리_ssot/contracts/handoff_rules.json` | 핸드오프 규칙 |
| `전처리_ssot/contracts/quality_gates.json` | 품질 게이트 |
| `전처리_ssot/contracts/schema_version.json` | 스키마 버전 |
| `전처리_ssot/contracts/stage_machine.json` | 스테이지 머신 |
| `전처리_ssot/contracts/audit_status.schema.json` | 감사 상태 스키마 |
| `전처리_ssot/contracts/profile_catalog.json` | 프로파일 카탈로그 |
| `전처리_ssot/contracts/sequential_run_status.schema.json` | 순차 실행 상태 |
| 기타 계약 파일 전량 | |

**전처리 SSOT 문서** (코드와의 정합성 검사)
| 경로 | 수량 |
|------|------|
| `전처리_ssot/docs/blockguide/*.md` | ~28개 |
| `전처리_ssot/docs/SSOT_stage0_preprocess_integrated_order.md` | 1개 |
| `전처리_ssot/기획안/*.md` | ~10개 |

**API Contract**
| 파일 |
|------|
| `docs/implementation/api-contract-v1.yaml` |
| `docs/implementation/prompt-map-v1.json` |

**Work Guard YAML**
| 파일 |
|------|
| `work_guards/` 하위 전량 |

### 핵심 검사 포인트

1. **프롬프트 YAML 43개 전수**: 각 YAML의 키가 코드에서 `prompt_loader.load()`로 참조되는가, 미사용 키 없는가
2. **장르 YAML ↔ genre_guard**: 10개 장르 YAML의 필드가 대응 guard 클래스와 1:1 매핑되는가
3. **analyst_libraries JSON 11개**: 각 라이브러리의 구조가 `analyst.py`에서 기대하는 스키마와 일치하는가
4. **Contract JSON ↔ 코드**: 각 계약 파일의 필드가 실제 코드에서 읽히고 검증되는가, 형해화된 계약 없는가
5. **스키마 버전 관리**: `schema_version.json`이 실제 계약 스키마 변경과 동기화되는가
6. **SSOT 문서 ↔ 실제 코드 흐름**: blockguide 문서가 현재 코드의 실제 흐름과 일치하는가 (문서 부패)
7. **style_guide.json**: 스타일 가이드 필드가 `style_extractor.py` / `style_guard.py`에서 읽히는 구조와 일치하는가
8. **Work Guard YAML**: `work_guard.py`가 읽는 키와 실제 YAML 키가 일치하는가
9. **api-contract-v1.yaml ↔ bridge_server.py**: 전 엔드포인트 + 요청/응답 스키마 1:1 대응 (1차 검사 보강)

---

## 7. Terminal 5 — 스크립트, 프런트엔드, 루트 파일

### 담당 범위

**Scripts 디렉토리** (1차에서 거의 미검사)
| 파일 | 역할 (추정) |
|------|------------|
| `scripts/run_stage2_smoke.py` | Stage 2 스모크 테스트 |
| `scripts/run_stage3_smoke.py` | Stage 3 스모크 테스트 |
| `scripts/run_stage4_smoke.py` | Stage 4 스모크 테스트 |
| `scripts/validate_manual_sweep.py` | 수동 스윕 검증 |
| `scripts/tf_c1_patch.py` | TF-C1 패치 |
| `scripts/generate_tr_bibles.py` | TR 바이블 생성 |
| `scripts/process_and_audit_tr_bi_loop.py` | TR/BI 처리 루프 |
| `scripts/repair_tr_korean_utf8.py` | 한국어 UTF-8 복구 |
| `scripts/backfill_quality_sidecars.py` | 품질 사이드카 백필 |
| `scripts/run_stage4_canary.py` | Stage 4 카나리아 |
| `scripts/audit_bi_5pass.py` | BI 5pass 감사 |
| `scripts/build_bi_from_phase0_and_tr.py` | BI 빌드 |
| `scripts/build_chaebol_allowance_zero_assets.py` | 재벌 자산 빌드 |
| `scripts/build_fallen_prince_buys_joseon_assets.py` | 몰락왕자 자산 빌드 |
| `scripts/tr_batch_harness.py` | TR 배치 하네스 |
| `scripts/e2e_menu_smoke.ps1` | E2E 메뉴 스모크 (PowerShell) |

**루트 레벨 파일** (1차 미검사)
| 파일 | 역할 (추정) |
|------|------------|
| `generate_empire_reborn_tr70.py` | TR70 생성 스크립트 |
| `smoke_sc.py` | 스모크 테스트 스크립트 |
| `tmp_utf8_check.py` | UTF-8 임시 체크 |
| `main.js` | 루트 Electron 진입점 (?) |
| `temp-electron-paths.js` | 임시 Electron 경로 |
| `temp-proc-poll.ps1` | 임시 프로세스 폴링 |
| `temp-proc-poll-oswarn.ps1` | 임시 OS 경고 폴링 |
| `temp-proc-trace.ps1` | 임시 프로세스 추적 |
| `temp-run-packaged.ps1` | 임시 패키지 실행 |
| `temp-run-packaged-ascii.ps1` | 임시 ASCII 패키지 실행 |

**Desktop 디테일** (1차에서 줄수만 열거)
| 파일 | 검사 내용 |
|------|----------|
| `geuldobi-desktop/main.js` | 루트 main.js와 중복? 역할 분리? |
| `geuldobi-desktop/src/main.js` | renderer process 로직 |
| `geuldobi-desktop/src/preload.js` | IPC 보안 — contextIsolation, nodeIntegration |
| `geuldobi-desktop/src/index.html` | UI 구조, inline script 보안 |
| `geuldobi-desktop/package.json` | 의존성 버전, 보안 취약점 |
| `geuldobi-desktop/temp-electron-loadcheck.js` | 임시 로드 체크 |
| `geuldobi-desktop/temp-electron-paths.js` | 임시 경로 체크 |
| `geuldobi-desktop/DESKTOP-GUIDE.md` | 문서 ↔ 실제 동작 정합성 |

**Treatments & Projects** (프로덕션 데이터/설정)
| 경로 | 내용 |
|------|------|
| `treatments/*.json` | 12개 TR 블록 + phase0 설계 |
| `treatments/preprocess/` | 전처리된 TR 데이터 |
| `projects/00/`, `projects/01/`, `projects/03/`, `projects/0w/` | 프로젝트 데이터 |
| `projects/test_project/` | 테스트 프로젝트 |

**MagicMock 디렉토리** (git status에서 발견)
| 경로 | 의심 사항 |
|------|----------|
| `MagicMock/` | 테스트 아티팩트 유출? 프로덕션 오염? |

### 핵심 검사 포인트

1. **스크립트 안전성**: DB를 직접 수정하는 스크립트가 있는가, 실행 시 데이터 손실 위험
2. **스크립트 ↔ 프로덕션 코드 정합성**: 스크립트가 import하는 모듈 시그니처가 현재 코드와 일치하는가
3. **루트 temp 파일**: 커밋해야 할 것 vs 삭제해야 할 것 분류
4. **MagicMock 디렉토리**: 테스트 부작용으로 생성된 디렉토리인지, 의도적인지 확인 → P1 잠재 문제
5. **Desktop 이중 main.js**: 루트 `main.js` vs `geuldobi-desktop/main.js` vs `geuldobi-desktop/src/main.js` 3개 파일 역할 구분
6. **Electron 보안**: `nodeIntegration: false`, `contextIsolation: true` 확인, preload 화이트리스트 검증
7. **treatments JSON 스키마**: TR 블록 구조가 파이프라인이 기대하는 입력 스키마와 일치하는가
8. **프로젝트 데이터 무결성**: `projects/*/project_data.db` 스키마가 `db_manager.py` 정의와 일치하는가
9. **package.json 의존성**: 알려진 취약점 있는 패키지 버전 사용 여부

---

## 8. 각 터미널에 내릴 오더

### Terminal 1 오더

```
OPUS TF — Detail Terminal 1: 미열거 인프라 모듈 & 유틸리티 전량 조사

너는 글도비 시스템의 미열거 인프라 모듈 담당 OPUS TF다.
1차 마스터 감사에서 명시적으로 열거되지 않은 인프라 모듈을 전량 검사한다.

■ 범위:
  - 미열거 Core 모듈 12개: arc_summary_utils, config_manager, logging_keys, soft_failure,
    state_text_verifier, studio_visualizer, writer_prompt_builders, quality_signal_metrics,
    reflexion_manager, constitutional_checker, continuity_pin_guard, investment_math_verifier
  - __init__.py 전량 (12개 패키지): modules/, core/, stage0/, genre_guards/, providers/,
    services/, domain/, agents/, models/, protocols/, validation/, api/
  - 교차 경계: 위 모듈이 1차 감사 대상 모듈과 올바르게 연결되는지 import/호출 추적

■ 임무 (6-Point Inspection + 자체 3PASS):
1. 각 모듈을 1줄 단위로 읽고, 생존 여부 확인 (실제 import되어 사용되는가)
2. __init__.py re-export: 패키지에서 노출하는 심볼이 실제 존재하는가
3. stage0/__init__.py 774줄: 내부 로직의 None guard, 분기 정합성 디테일 검사
4. config_manager ↔ prompt_loader ↔ constants: 설정 로딩 3중 경로 충돌/중복
5. soft_failure ↔ error_helper: 에러 처리 이중 경로 정합성
6. investment_math_verifier ↔ investment_arithmetic_checker: 역할 분리, 중복 로직
7. constitutional_checker ↔ quality_constitution: 유사명 모듈 역할 구분

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 파일 초벌 스캔, 후보 목록 + 확신도(HIGH/MED/LOW)
  - PASS 2: 코드 증거 재확인 + CLAUDE.md 대조 + 테스트 대조 → 오탐 제거
  - PASS 3: 최종 확정 + Severity 배정 + 오탐 제거 로그 첨부

■ 보고: [D-T1-{SEQ}] 형식. Severity P0~P3.
  보고서 말미에 반드시: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md, 1차 마스터 오더 T1 범위 (경계 확인용)
```

### Terminal 2 오더

```
OPUS TF — Detail Terminal 2: 미열거 에이전트 & 모델 계층 전량 조사

너는 글도비 시스템의 미열거 에이전트 & 모델 계층 담당 OPUS TF다.
1차 마스터 감사에서 이름만 언급되거나 누락된 에이전트/모델을 전량 검사한다.

■ 범위:
  - 미열거 Domain Agents 6개: consensus_validator, constraint_compiler, critic,
    manager, preflight_checker, weaver
  - 모델 계층 5개: models/arc.py, models/blueprint.py, models/manuscript.py,
    models/npc.py, models/__init__.py
  - base_agent.py 디테일 (~1,820줄): 1차에서 "부분" 배정 → 전체 디테일 검사
  - 교차 경계: 에이전트 → 모델 → DB 데이터 흐름 추적

■ 임무 (6-Point Inspection + 자체 3PASS):
1. 미열거 에이전트 6개: 실제 호출 여부, 어떤 Stage에서 사용되는지 추적
2. 모델 스키마: arc/blueprint/manuscript/npc 필드 ↔ DB 테이블 ↔ LLM 응답 스키마 3자 대응
3. base_agent.py Context Caching (L1599-1820): TTL, eviction, 에러 처리 디테일
4. constraint_compiler ↔ blueprint_constraint_compiler: 역할 분리, 중복 로직
5. critic.py ↔ arc_critic.py: 범용 vs 특화 역할 구분
6. protagonist_items vs items_acquired: 모델 계층에서도 폴백 처리되는가
7. Pydantic/dataclass 검증: 모델 validation 로직 ↔ 런타임 데이터 정합

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 파일 초벌 스캔, 후보 목록 + 확신도(HIGH/MED/LOW)
  - PASS 2: 코드 증거 재확인 + CLAUDE.md 대조 + 테스트 대조 → 오탐 제거
  - PASS 3: 최종 확정 + Severity 배정 + 오탐 제거 로그 첨부

■ 보고: [D-T2-{SEQ}] 형식. Severity P0~P3.
  보고서 말미에 반드시: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
■ 금지: 구조 변경 제안, 대원칙 위반 수정, 직접 코드 수정.
■ 참조: CLAUDE.md (protagonist_items, Context Caching 섹션), 1차 T2/T3 범위
```

### Terminal 3 오더

```
OPUS TF — Detail Terminal 3: 미열거 테스트 전수 감사 (229개)

너는 글도비 시스템의 테스트 커버리지 감사 담당 OPUS TF다.
1차 마스터에서 명시적으로 열거된 ~39개 외 나머지 229개 테스트 파일을 전수 검사한다.

■ 범위:
  - tests/ 하위 전량 중 1차에서 미열거된 파일 (229개)
  - tests/chaos/ 전량, tests/property/ 전량
  - tests/e2e/ 전량, tests/integration/ 전량
  - tests/stage3_isolated_test/ 전량, tests/stage4_v2_test/ 전량
  - test_sweep*.py, test_v*.py, test_tf*.py 시리즈 전량

■ 임무 (자체 3PASS):
1. 각 테스트 파일을 열어서 다음 8가지 점검:
   a. Dead 테스트: import 에러로 collect skip되는 파일
   b. Mock 과잉: MagicMock이 검증력 0으로 만든 테스트
   c. Assertion 부재: assert 없는 "실행만 통과" 테스트
   d. Fixture 부정합: 현재 프로덕션 시그니처와 불일치
   e. Chaos 테스트 실효성: 실제 경계 조건 테스트 여부
   f. E2E 환경 의존성: API 키/DB 없이 실행 가능한지
   g. 중복 테스트: 동일 분기 반복 검증
   h. xfail 68개: 사유 여전히 유효한지, 이미 수정된 것은 없는지
2. 프로덕션 코드의 핵심 분기 중 테스트가 없는 것 식별 (커버리지 갭)
3. 테스트 파일명 ↔ 프로덕션 파일 매핑이 1:1인지, 고아 테스트 없는지

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 파일 초벌 스캔 (파일 열기 + 구조 파악), 의심 항목 후보 기록
  - PASS 2: 후보 각각의 assert/mock/fixture를 재확인, 실제 pytest 실행 결과와 대조
  - PASS 3: 최종 확정 (P2-MODERATE 이상만 보고, P3은 10건 이하로 제한)

■ 보고: [D-T3-{SEQ}] 형식. Severity P0~P3.
  보고서 말미에 반드시: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
  추가: "xfail 68개 중 X개는 이미 수정 완료 추정" 별도 섹션
■ 금지: 테스트 직접 수정, 테스트 삭제 제안, 프로덕션 코드 수정.
■ 참조: CLAUDE.md (테스트 기준선 3,847), pytest 출력
```

### Terminal 4 오더

```
OPUS TF — Detail Terminal 4: Config, Contract, SSOT 문서 전수 감사

너는 글도비 시스템의 설정·계약·SSOT 문서 정합성 담당 OPUS TF다.
코드가 아닌 설정/계약/문서 파일이 실제 코드와 정확히 동기화되는지 전수 검사한다.

■ 범위:
  - config/prompts/*.yaml 43개 전량
  - config/genres/*.yaml 10개 전량
  - config/prompts/analyst_libraries_*.json 11개 전량
  - config/smart_retrieval/, config/cash/, config/style_references/ 하위 전량
  - config/models.yaml, config/system.yaml, config/settings.json
  - config/settings/validation.yaml, config/settings/item_suffixes.yaml
  - config/tone_presets.json
  - 전처리_ssot/contracts/ 전량 (artifact_contracts, handoff_rules, quality_gates,
    schema_version, stage_machine, audit_status, profile_catalog, sequential_run_status 등)
  - 전처리_ssot/docs/blockguide/ ~28개 문서
  - 전처리_ssot/기획안/ ~10개 문서
  - docs/implementation/api-contract-v1.yaml, prompt-map-v1.json
  - work_guards/ 하위 전량

■ 임무 (자체 3PASS):
1. 프롬프트 YAML 43개: 각 키가 prompt_loader.load()로 참조되는지, 미사용 키 식별
2. 장르 YAML 10개: 필드 ↔ genre_guard 클래스 1:1 매핑 확인
3. analyst_libraries JSON 11개: 구조 ↔ analyst.py 기대 스키마 일치
4. Contract JSON: 각 계약 필드가 코드에서 읽히고 검증되는지, 형해화된 계약 식별
5. schema_version.json: 실제 스키마 변경과 동기화 여부
6. SSOT blockguide 문서: 현재 코드 흐름과 일치 여부 (문서 부패 탐지)
7. style_guide.json: style_extractor/style_guard가 읽는 구조와 일치 여부
8. work_guard YAML: work_guard.py가 읽는 키와 일치 여부
9. api-contract-v1.yaml: bridge_server.py 전 엔드포인트 + 스키마 재검증

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 파일 스캔 + 코드 참조 추적, 불일치 후보 기록
  - PASS 2: 코드 grep으로 실제 사용처 재확인, 의도적 미사용(예비 키) vs 진짜 누락 구분
  - PASS 3: 최종 확정 + 문서 부패 항목은 별도 "문서 동기화 필요" 섹션

■ 보고: [D-T4-{SEQ}] 형식. Severity P0~P3.
  보고서 말미에 반드시: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
  추가: "문서 부패 N건" 별도 섹션
■ 금지: Config 직접 수정, 문서 직접 수정, 프로덕션 코드 수정.
■ 참조: CLAUDE.md (Config SSOT, 장르 가드, prompt 섹션), prompt_loader.py, genre_guards/
```

### Terminal 5 오더

```
OPUS TF — Detail Terminal 5: 스크립트, 프런트엔드, 루트 파일 전수 감사

너는 글도비 시스템의 스크립트·프런트엔드·루트 파일 담당 OPUS TF다.
프로덕션 파이프라인 외부의 보조 파일 전량을 검사하여 안전성·정합성을 확인한다.

■ 범위:
  - scripts/ 하위 16개 Python + 1개 PowerShell 스크립트
  - 루트 레벨 Python: generate_empire_reborn_tr70.py, smoke_sc.py, tmp_utf8_check.py
  - 루트 레벨 임시 파일: main.js, temp-electron-paths.js, temp-proc-*.ps1, temp-run-*.ps1
  - Desktop 전량: geuldobi-desktop/ (main.js, src/main.js, src/preload.js, src/index.html,
    package.json, DESKTOP-GUIDE.md, temp-*.js)
  - Treatments: treatments/*.json (12 블록 + phase0), treatments/preprocess/
  - Projects 데이터: projects/00/, 01/, 03/, 0w/, test_project/
  - MagicMock/ 디렉토리 (의심 아티팩트)

■ 임무 (자체 3PASS):
1. 스크립트 안전성: DB 직접 수정 스크립트 식별, 실행 시 데이터 손실 위험 평가
2. 스크립트 ↔ 프로덕션 정합성: import하는 모듈 시그니처가 현재 코드와 일치하는가
3. 루트 temp 파일 분류: 커밋 대상 vs 삭제 대상 vs .gitignore 대상
4. MagicMock/ 디렉토리: 생성 원인 추적, 테스트 부작용이면 삭제 권고
5. Desktop 이중 main.js: 루트 vs geuldobi-desktop/ vs src/ 3개 파일 역할 구분
6. Electron 보안: nodeIntegration, contextIsolation, preload 화이트리스트
7. Treatments JSON 스키마: TR 블록 구조 ↔ 파이프라인 입력 스키마 일치
8. 프로젝트 데이터: project_data.db 스키마 ↔ db_manager.py 정의 일치
9. package.json 의존성: 알려진 취약점 있는 버전 사용 여부

■ 자체 3PASS 감리 필수:
  - PASS 1: 전 파일 스캔 + 안전성/정합성 후보 기록
  - PASS 2: 실제 코드 참조 + git blame으로 의도 확인 → 오탐 제거
  - PASS 3: 최종 확정 + "삭제 권고" vs "수정 필요" vs "정상" 3분류

■ 보고: [D-T5-{SEQ}] 형식. Severity P0~P3.
  보고서 말미에 반드시: "PASS1 N건 → PASS2 M건 제거 → 최종 K건 확정"
  추가: "삭제 권고 파일 목록" 별도 섹션
■ 금지: 파일 직접 삭제, 프로덕션 코드 수정, 패키지 업데이트 직접 실행.
■ 참조: CLAUDE.md, geuldobi-desktop/DESKTOP-GUIDE.md, package.json
```

---

## 9. 취합 프로세스

### 9.1 개별 터미널 완료 후

1. **P0 즉시 에스컬레이션**: P0 발견 시 즉시 보고
2. **교차 검증**: 터미널 경계 이슈 양쪽 대조
3. **중복 제거**: 가장 상세한 보고 채택
4. **1차 감사 발견사항과 대조**: 1차에서 이미 보고된 항목 중복 제거

### 9.2 최종 마스터 보고서

- **파일명**: `docs/2026-03-13/OPUS-TF-5terminal-detail-consolidated-findings.md`
- **구성**: P0→P1→P2→P3 순 정렬, 터미널별 섹션
- **오탐 통계**: 전 터미널 합산 "PASS1 총 N건 → 최종 K건 (오탐률 X%)"
- **삭제 권고 파일 통합 목록**
- **문서 부패 통합 목록**

---

## 10. 마스터 3PASS 감리 기록

### PASS 1 — 누락 영역 커버리지 (완료)
- [x] 1차 마스터에서 미열거된 프로덕션 모듈 23개 전량 배정 확인
- [x] 미열거 테스트 229개 전량 T3에 배정 확인
- [x] 미열거 Config/Contract/SSOT 문서 23+개 전량 T4에 배정 확인
- [x] 미열거 스크립트 16개 + 루트 파일 + Desktop + temp 파일 전량 T5에 배정 확인
- [x] MagicMock/ 디렉토리 의심 아티팩트 T5에 배정 확인
- **수정**: models/ 계층을 T1→T2로 이동 (에이전트와 밀접)

### PASS 2 — 오더 정합성 (완료)
- [x] 각 터미널 오더에 범위·임무·3PASS 프로토콜·보고형식·금지사항·참조 6요소 완비
- [x] 자체 3PASS 프로토콜이 5개 터미널 모두에 동일하게 명시
- [x] 오탐 판정 기준 5개(FP-1~5) 공통 섹션에 명시
- [x] 1차 감사와의 중복 제거 지침 취합 프로세스에 명시
- [x] 보고 형식 `[D-TN-SEQ]`로 1차 `[TN-SEQ]`와 구별
- **수정**: T3 오더에 "P3은 10건 이하로 제한" 추가 (테스트 파일 229개에서 P3 폭주 방지)

### PASS 3 — 최종 점검 (완료)
- [x] __init__.py 12개 패키지 전량 T1에 배정 확인
- [x] base_agent.py 디테일이 T2에 명시적 배정 확인
- [x] xfail 68개 검사가 T3에 명시 확인
- [x] 전처리_ssot 기획안 10개가 T4에 포함 확인
- [x] treatments/preprocess/ + projects/ 데이터가 T5에 포함 확인
- [x] 교차 경계 검사가 T1/T2에 양방향 명시 확인
- [x] 각 터미널 오더의 "자체 3PASS 감리 필수" 문구 + 보고 말미 오탐 로그 지침 확인
- **최종 확인**: 1차 미커버 영역 전량 + 자체 3PASS 프로토콜 + 오탐 방지 메커니즘 완비
