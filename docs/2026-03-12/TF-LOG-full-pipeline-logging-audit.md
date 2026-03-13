# TF-LOG: 전체 파이프라인 로깅 체계 전수조사

> 상태: **CONFIRMED** (3-Pass 사실 검증 완료 2026-03-13)
> 작성일: 2026-03-13
> 범위: Stage 0 / Stage 2 / Stage 3 / Cross-cutting 모듈 (Stage 4는 TF-S4-LOG 참조)
> 제약: **코드 수정 절대 금지** (현황 기록 + 보강 방안 제안만)

---

## 0. Executive Summary

### 전체 로깅 인프라

```
Logger 설정: modules/core/logger.py (StudioLogger 싱글톤)
  ├─ 파일 핸들러: logs/session_{timestamp}.log (DEBUG 레벨, 전 모듈 통합)
  ├─ 포맷: [%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
  └─ StreamHandler 제거 (콘솔 이중 출력 방지)

영속 싱크 6종:
  1. session_*.log         — 텍스트 (DEBUG~ERROR, 전 모듈)
  2. episode_production.jsonl — Stage 4 전용 구조화 기록
  3. pass_rate_monitor.json  — 합격률 집계 (최근 1,000건)
  4. soft_failures.jsonl     — 비차단 오류 구조화 (throttled)
  5. metrics_{session}.json  — 토큰/비용 집계 (세션별)
  6. artifacts/stage{N}/     — 아티팩트 스냅샷
  + project_data.db          — SQLite SSOT (테이블 다수)
  + decisions.jsonl          — 세션 로거 판정 기록 (Stage 3)
```

### Stage별 로깅 수치 종합

| Stage | logging 호출 | print() | ui.log() | silent except | 구조화 로그 |
|-------|:---:|:---:|:---:|:---:|------|
| Stage 0 | 93 | 124 | 100 | 10 | 없음 |
| Stage 2 | 187 | 2 | 138 | 7 | DB(stage_attempts, director_selections) |
| Stage 3 | 112 | 47 | 46 | 3 | DB + decisions.jsonl + artifacts |
| Stage 4 | 175+ | 49 | 다수 | 4 | episode_production.jsonl + DB + artifacts |
| Cross-cutting | 174 | 14 | 0 | ~20 | DB + metrics JSON + soft_failures.jsonl |
| **합계** | **~741** | **~236** | **~284+** | **~44** | |

---

## 1. Stage 0 — 초기 설정 로깅 체계

### 1.1 관련 파일

| 파일 | 역할 | logging | print | ui.log | silent except |
|------|------|:---:|:---:|:---:|:---:|
| `modules/core/stage01_helpers.py` | Stage 0 퍼사드 | 12 (전부 warning) | 0 | 100 | 4 |
| `modules/core/stage0/__init__.py` | StageZeroManager 오케스트레이터 | 10 (전부 warning) | 67 | 0 | 3 |
| `modules/core/stage0/reverse_expander.py` | 역공학 (기존 원고→Bible) | 40 (21i+16w+2d+1e) | 0 | 0 | 2 |
| `modules/core/stage0/story_expander.py` | 컨셉→Bible+Treatment 생성 | 16 (7i+8w+1e) | 0 | 0 | 0 |
| `modules/core/stage0/style_extractor.py` | 문체 분석→StyleGuide | 14 (6i+7w+1d) | 9 | 0 | 1 |
| `modules/core/stage0/preset_registry.py` | 장르 스키마/HUD 관리 | 1 (warning) | 0 | 0 | 0 |
| `modules/core/stage0/spinner.py` | UI 스피너 유틸 | 0 | 48 | 0 | 0 |

### 1.2 데이터 영속 경로

```
Bible         → project_manager.save_v20_anchor("bible", data)
                → db_manager.save_anchor(key, data)
                ✗ 성공 로깅 없음 (실패만 warning)

Treatment     → JSON 파일 직접 쓰기
                ✗ DB anchor 미저장 (파일만)

Style Guide   → (1) 로컬 파일 캐시 + (2) save_v20_anchor("style_guide")
                ✓ 캐시 저장 성공 로깅 (info)
                ✗ DB anchor 저장 성공 로깅 없음

Manuscripts   → reverse_expander.persist_to_db()
                → db_manager.save_manuscript()
                ✗ 성공/실패 모두 로깅 없음

VecMemory     → reverse_expander.persist_to_vectordb()
                ✓ 진행 로깅 (info)
                ⚠️ 초기화 실패 시 warning 후 count=0 반환

Episode Bible → persist_to_db() → db_manager.save_episode_bible()
                ✗ 성공 로깅 없음
```

### 1.3 발견된 Gap

#### S0-G1. 구조화된 생산 로그 없음 — MEDIUM

**현상:** Stage 0에는 `episode_production.jsonl`이나 `decisions.jsonl` 같은 구조화된 이벤트 로그가 없음. Bible/Treatment 추출 결과, 스타일 분석 결과가 DB에 저장되지만 **과정 추적 로그가 없음**.

#### S0-G2. save_manuscript() 성공 로깅 없음 — MEDIUM

**위치:** `db_manager.py:save_manuscript()` (L1038 부근)

**현상:** INSERT OR REPLACE 수행 후 성공/실패 어느 쪽도 logging 호출 없음. 역공학으로 70화 원고를 DB에 쓸 때 어느 에피소드가 성공/실패했는지 추적 불가.

#### S0-G3. save_anchor() 성공 로깅 없음 — LOW

**위치:** `db_manager.py:save_anchor()` (L1530 부근)

**현상:** 실패 시 warning 있으나 성공 시 로깅 없음. Bible, Volumes, Arcs, Style Guide, Preset State 등 모든 앵커 저장이 조용히 성공.

#### S0-G4. 사용자 입력 타임아웃 silent pass — LOW

**위치:** `stage0/__init__.py:L128, 206, 383`

**현상:** 장르/컨셉/Bible 선택 메뉴에서 `except (ValueError, IndexError, EOFError): pass`로 입력 실패가 무시됨. 대화형 Stage 0 특성상 재시도가 즉시 이뤄지므로 심각도 낮음.

#### S0-G5. persist_to_db() 부분 실패 미검증 — LOW

**위치:** `stage01_helpers.py:L365-370`

**현상:** `persist_to_db()` 반환 dict에 테이블별 성공 건수가 있으나, 호출부에서 건수 검증/재시도 없이 ui.log()로 표시만 함.

---

## 2. Stage 2 — Arc/Blueprint 로깅 체계

### 2.1 관련 파일

| 파일 | 역할 | logging | print | ui.log | silent except |
|------|------|:---:|:---:|:---:|:---:|
| `stage2_orchestrator.py` | Arc 오케스트레이터 | 18 (1d+14i+3w) | 0 | 43 | 3 |
| `stage2_validation_pipeline.py` | 검증 파이프라인 | 34 (2d+16i+16w) | 0 | 36 | 1 |
| `stage2_finalizer.py` | Finalizer (Director+DB) | 50 (21d+8i+21w) | 2 | 31 | 1 |
| `stage2_preflight.py` | Preflight 분석 | 85 (22d+25i+37w+1e) | 0 | 28 | 0 |

### 2.2 데이터 영속 경로

```
Director 판정  → DB: director_selections 테이블
                  (verdict, score, reason, fix_scope, attempt_key, candidate_key, content_hash)
                → DB: stage_attempts 테이블
                  (verdict, failure_category, generation_method, selected_strategy, rejection_reason)
                ✓ attempt_key 상관 ID 사용

아크 아티팩트  → artifacts/{candidate_key}_{timestamp}.json
                ✓ 선택된 아크만 저장 (artifact_kind="final_arc")
                ✗ 앙상블 탈락 2후보 미저장

아크 데이터    → DB: arcs anchor (PASS 시)
                ✓ save_anchor("arcs", all_refined_arcs)
```

### 2.3 발견된 Gap

#### S2-G1. Stage 2 전용 JSONL 로그 없음 — MEDIUM

**현상:** Stage 4에는 `episode_production.jsonl`이 있으나, Stage 2에는 동등한 구조화 로그가 없음. 아크 생산 이력은 DB `stage_attempts` + `director_selections` 테이블로만 추적 가능.

**영향:** DB 쿼리 없이 아크 생산 과정을 빠르게 조회하기 어려움.

#### S2-G2. 앙상블 탈락 후보 미저장 — MEDIUM

**현상:** `arc_ensemble.py`에서 3전략(conservative/balanced/creative) 후보를 생성하나, Director 선택 후 탈락 2후보는 메모리에서 폐기. 선택된 1후보만 artifact 저장.

**영향:** "왜 conservative가 아닌 creative를 선택했는지" 사후 비교 불가.

#### S2-G3. Director 판정 프레임 print-only (Stage 2) — MEDIUM

**위치:** `director_ensemble.py:655-671`

**현상:** Stage 2 Director 판정도 Stage 4와 동일하게 print()로만 콘솔 출력. 9건의 print() 호출.

**참고:** DB `director_selections` 테이블에 verdict/score/reason은 저장되므로 Stage 4보다 gap이 작음. 단, 판정 프레임의 **세부 피드백(contradictions, fix_scope_reasoning)**은 DB에 미기록.

#### S2-G4. logging.error/critical 부재 — LOW

**현상:** Stage 2 전체 187건 logging 호출 중 error 0건, critical 0건. `stage2_preflight.py`에 error 1건만 존재. 실패 시에도 warning으로만 기록.

---

## 3. Stage 3 — Blueprint 로깅 체계

### 3.1 관련 파일

| 파일 | 역할 | logging | print | ui.log | silent except |
|------|------|:---:|:---:|:---:|:---:|
| `stage3_orchestrator.py` | Blueprint 오케스트레이터 | 39 (23d+4i+6w+6e) | 11 | 46 | 3 |
| `blueprint_ensemble.py` | 3전략 앙상블 생성 | 24 (5d+5i+10w+4e) | 7 | 0 | 0 |
| `director_ensemble.py` (S3 부분) | Director 선택+판정 | 49 (2d+21i+26w) | 29 | 0 | 0 |

### 3.2 데이터 영속 경로

```
Director 판정  → DB: stage_attempts + director_selections
                  ✓ attempt_key + session_id + candidate_key 상관 ID
                → decisions.jsonl (session_logger)
                  ✓ 구조화된 판정 기록 (stage="stage3", decision_type="blueprint")
                → artifacts/stage3/{scope}/attempt_{N}/final_blueprint__{strategy}.json
                  ✓ 선택된 Blueprint만 아티팩트 저장

비용 추적     → DB: cost_records
                ✓ event 메타데이터 포함

Blueprint 후보 → 메모리에서 3후보 유지 → Director 선택 후 2후보 폐기
                ✗ 탈락 후보 미저장
```

### 3.3 발견된 Gap

#### S3-G1. Blueprint 앙상블 탈락 후보 미저장 — MEDIUM

**현상:** `blueprint_ensemble.py`에서 3전략 후보 생성 후 Director가 1개 선택. 나머지 2개는 artifact 저장 없이 폐기.

#### S3-G2. Director Thinking print-only (Stage 3) — MEDIUM

**위치:** `director_ensemble.py:329`

**현상:** Stage 3 Director의 `_last_thinking`도 print()로만 콘솔 출력. Stage 4와 동일한 패턴.

#### S3-G3. Director 판정 프레임 print-only (Stage 3) — MEDIUM

**위치:** `director_ensemble.py:315-332`

**현상:** 9건의 print() 호출로 판정 프레임(verdict, score, contradictions, thinking) 콘솔 출력. DB에 verdict/score/reason은 저장되나, contradictions 등 세부 사항은 미기록.

#### S3-G4. Blueprint 앙상블 전략별 실패 원인 미영속 — LOW

**현상:** `blueprint_ensemble.py:L330`에서 disqualified 후보의 이유가 logging.info로 기록되나, 구조화 데이터(DB/JSONL)에는 미기록.

### 3.4 Stage 3 양호 사항

| 항목 | 근거 |
|------|------|
| **3-tuple 상관 ID** | session_id + attempt_key + candidate_key 완비 |
| **decisions.jsonl** | session_logger를 통한 구조화된 판정 기록 존재 |
| **artifact 스냅샷** | 선택된 Blueprint를 JSON 아티팩트로 저장 |
| **비용 추적** | cost_records DB 테이블에 Stage 3 이벤트 기록 |
| **error 레벨 사용** | stage3_orchestrator에 error 6건 (traceback 포함) — Stage 2보다 성숙 |
| **silent except 최소** | 3건 (2건 텔레메트리 setattr + 1건 session_logger.log_decision — 모두 비차단 의도적) |

---

## 4. Cross-cutting 모듈 로깅 체계

### 4.1 관련 파일

| 파일 | 역할 | logging | print | silent except |
|------|------|:---:|:---:|:---:|
| `base_agent.py` | AI 에이전트 베이스 | 59 (18d+17i+24w) | 11 | 2 |
| `db_manager.py` | SQLite SSOT | 81 (10d+15i+55w+1e) | 3 | 14 (except pass) |
| `failure_analyzer.py` | 실패 패턴 분석 | 29 | 1 | 다수 |
| `pass_rate_monitor.py` | 합격률 추적 | 2 (warning) | 0 | 0 |
| `metrics_collector.py` | 토큰/비용 집계 | 0 | 0 | 0 |
| `soft_failure.py` | 비차단 오류 리포팅 | 3 (warning) | 0 | 0 |
| `llm_router.py` | LLM 라우팅 | 0 | 0 | 1 |
| `llm_generate.py` | 공용 생성 헬퍼 | 0 | 0 | 0 |
| `gemini_provider.py` | Gemini API 래퍼 | 0 | 0 | 2 |
| `logger.py` | 로깅 설정 싱글톤 | — | — | — |

### 4.2 Logger 설정 (modules/core/logger.py)

```
StudioLogger (싱글톤)
  ├─ init_logger(log_dir, session_name)
  ├─ 파일 핸들러: logs/session_{timestamp}.log
  ├─ 포맷: [%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
  ├─ 기본 레벨: DEBUG
  ├─ StreamHandler 제거 (콘솔 이중 출력 방지)
  └─ retarget(new_log_dir) — 프로젝트 전환 시 로그 경로 변경
```

### 4.3 발견된 Gap

#### CC-G1. db_manager.py silent except 14건 — LOW (의도적)

**현상:** 14건의 `except ... pass` 블록 (로깅 없음). 대부분 `except sqlite3.OperationalError: pass`로 컬럼 마이그레이션 시도(ALTER TABLE ADD COLUMN) 시 "이미 존재" 오류를 무시. 별도로 로깅 포함 except 블록 ~45건, 기타 except 블록 ~18건이 존재하나 이들은 적절히 처리됨.

**판정:** 의도적 설계. 멱등적 마이그레이션 패턴으로, 컬럼이 이미 있으면 OperationalError → pass. 실제 데이터 손실 위험 없음.

#### CC-G2. LLM 라우팅 레이어 로깅 0건 — LOW

**현상:** `llm_router.py`, `llm_generate.py`, `gemini_provider.py` 3파일 모두 logging 호출 0건. 에러 핸들링을 상위(base_agent.py)에 위임.

**판정:** 순수 라우팅/래퍼 레이어. base_agent.py가 59건 로깅으로 충분히 커버. 다만 provider 레벨에서 API 오류 원인(rate limit vs auth fail vs network)을 구분하려면 provider에도 logging이 필요할 수 있음.

#### CC-G3. metrics_collector.py 자체 로깅 0건 — LOW

**현상:** 토큰/비용 집계 모듈인데 자체적으로 logging 호출이 0건. JSON 파일로 영속화는 하지만, 집계 오류/누락 시 추적 불가.

#### CC-G4. pass_rate_monitor.py 로깅 2건뿐 — LOW

**현상:** 1,000건 레코드 관리 모듈인데 로깅이 load 실패(warning) + save 실패(warning) 2건뿐. 레코드 추가/삭제/로테이션 시 로깅 없음.

---

## 5. 전 Stage 공통 패턴 분석

### 5.1 Director 판정 프레임 print-only (전 Stage 공통)

| Stage | 위치 | print 수 | DB 저장 | 세부 미기록 |
|-------|------|:---:|:---:|------|
| Stage 2 | director_ensemble.py:655-671 | 9 | verdict/score/reason ✅ | contradictions, thinking ❌ |
| Stage 3 | director_ensemble.py:315-332 | 9 | verdict/score/reason ✅ | contradictions, thinking ❌ |
| Stage 4 | director_ensemble.py:1212-1237 | 11 | verdict/score ✅ (JSONL) | thinking, fix_scope_reasoning ❌ |

**공통점:** 모든 Stage의 Director 판정이 print()로만 콘솔 출력. DB에 verdict/score/reason은 저장되나, **Director thinking, contradictions 상세, fix_scope_reasoning**은 전 Stage에서 미영속.

### 5.2 앙상블 탈락 후보 미보존 (전 Stage 공통)

| Stage | 앙상블 후보 수 | 저장되는 후보 | 폐기되는 후보 |
|-------|:---:|------|------|
| Stage 2 | 3 (conservative/balanced/creative) | 선택 1개 (artifact) | 2개 폐기 |
| Stage 3 | 3 (action/emotion/dialogue 등) | 선택 1개 (artifact) | 2개 폐기 |
| Stage 4 | 3 (전략별) | 선택 1개 + rejected_best (artifact) | 1~2개 폐기 |

### 5.3 상관 ID 현황

| Stage | attempt_key | session_id | candidate_key | JSONL 내 사용 |
|-------|:---:|:---:|:---:|------|
| Stage 0 | ❌ 없음 | ❌ 없음 | ❌ 없음 | 구조화 로그 자체 없음 |
| Stage 2 | ✅ DB | ✅ DB | ✅ DB | JSONL 없음, DB만 |
| Stage 3 | ✅ DB + decisions.jsonl | ✅ DB | ✅ DB + artifact | ✅ |
| Stage 4 | ✅ JSONL + DB | ✅ partial | ✅ JSONL | ✅ |

### 5.4 구조화 로그 현황

| Stage | episode_production.jsonl | decisions.jsonl | DB stage_attempts | DB director_selections |
|-------|:---:|:---:|:---:|:---:|
| Stage 0 | ❌ | ❌ | ❌ | ❌ |
| Stage 2 | ❌ | ❌ | ✅ | ✅ |
| Stage 3 | ❌ | ✅ | ✅ | ✅ |
| Stage 4 | ✅ (35 필드) | ❌ | ✅ | ✅ |

### 5.5 logging 레벨 분포

| Stage | debug | info | warning | error | critical |
|-------|:---:|:---:|:---:|:---:|:---:|
| Stage 0 | 3 | 34 | 54 | 2 | 0 |
| Stage 2 | 46 | 63 | 77 | 1 | 0 |
| Stage 3 | 30 | 30 | 42 | 10 | 0 |
| Stage 4 | 36+ | 20+ | 43+ | 1 | 0 |
| Cross-cutting | 27+ | 21+ | 94+ | 0 | 0 |
| **합계** | **~143** | **~179** | **~300** | **~15** | **0** |

**관찰:** `logging.critical` 전체 코드베이스에서 **0건**. `logging.error` 13건 (Stage 3에 집중). warning이 전체의 ~40%로 가장 많음.

---

## 6. 보강 우선순위 (전 Stage 통합)

### Tier 1: 전 Stage 공통 (높은 재사용 효과)

| 순위 | 항목 | 대상 | 작업량 |
|------|------|------|--------|
| 1 | **Director thinking 영속화** | S2/S3/S4 director_ensemble.py | ~10줄 (3개 메서드) |
| 2 | **Director contradictions 영속화** | S2/S3/S4 director_ensemble.py | ~10줄 |
| 3 | **앙상블 전후보 개발모드 저장** | S2 arc_ensemble + S3 blueprint_ensemble + S4 interview_round | ~30줄 |

### Tier 2: Stage별 개별

| 순위 | 항목 | 대상 | 작업량 |
|------|------|------|--------|
| 4 | **S0: 구조화 생산 로그** — Stage 0 완료 시 결과 JSONL 기록 | stage01_helpers.py | ~20줄 |
| 5 | **S0: save_manuscript 성공 로깅** | db_manager.py | ~3줄 |
| 6 | **S2: 아크 생산 JSONL** — stage_attempts 보충 | stage2_finalizer.py | ~30줄 |
| 7 | **CC: provider 레벨 에러 분류 로깅** | gemini_provider.py | ~10줄 |

---

## 부록 A: Stage 4 상세

→ `docs/2026-03-12/TF-S4-logging-reinforcement-audit.md` 참조 (11-Pass, 22건)

## 부록 B: 감리 과정

| Pass | 작업 | 결과 |
|------|------|------|
| 1차 | 4-agent 병렬 전수조사 (Stage 0 / Stage 2 / Stage 3 / Cross-cutting) | 파일별 logging/print/ui.log 수치 + silent except 수 + 데이터 영속 경로 |
| 2차 | 수치 교차 검증 + Gap 분류 + 전 Stage 공통 패턴 추출 | S0 5건 + S2 4건 + S3 4건 + CC 4건 = 17건 |
| 3차 | Pass 1 사실 검증 — 3-agent 병렬 코드 대조 (S0 9항목 전TRUE, S2 7항목 전TRUE, S3 6항목 2FALSE, CC 10항목 3FALSE) | 7건 오류 발견 |
| 4차 | Pass 2 수정 — S3 print 수치(2→11), S3 silent except 설명 보정, base_agent 내역(18d+17i+24w), db_manager 내역(10d+15i+55w+1e), db_manager silent except(973→14), spinner.py logging(20→0), S0 레벨분포(info↔warning 교정) | 7건 수정 |
| 5차 | Pass 3 정합성 확인 — 합계 행 재계산, 레벨 분포 교차 검증 | **사실 오류 0건, 17건 확정** |
