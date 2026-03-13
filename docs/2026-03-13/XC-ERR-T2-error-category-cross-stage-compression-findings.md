# XC-ERR-T2: 에러 카테고리 스테이지간 압축

> 생성일: 2026-03-13
> 초점: Stage 2 validation → anchors DB → Stage 4 context builder 경로
> 방법론: 3-Pass

---

## 1. 에러 전파 경로 분석

### Stage 2 → DB 저장 경로
```
Stage2ValidationPipeline.run_validation()
  → Pre-Director 검증 체인 (4단계: B1/B2/B3/B4)
  → 반환: {action, refined_arc, draft_validator_passed, consensus_passed,
           suspected_duplicates, corrections_made, python_advisories}
  → Stage2Orchestrator → DB 저장
    → stage_attempts 테이블 (verdict, score, 메타데이터)
    → anchors 테이블 (arcs JSON)
```

### DB → Stage 4 소비 경로
```
Stage4ContextBuilder._build_continuity_packet()
  → world_state._state (WorldStateManager에서 로드)
  → fact_ledger._ledger (FactLedger에서 로드)
  → db.get_npc_history(), db.get_relationship_history()
  → db.get_canonical_facts()
  (Stage2 validation 에러 정보는 직접 소비하지 않음)
```

---

## 2. Findings

### [XC-ERR-012] P1 | Stage 2 validation 에러 디테일이 Stage 4 컨텍스트에 전달되지 않음

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-012 |
| Severity | P1 |
| 현상 요약 | Stage 2 Pre-Director 검증 체인의 python_advisories, corrections_made, suspected_duplicates가 DB에 저장되나 Stage 4 context builder가 이를 참조하지 않음 |
| 코드 근거 | `stage2_validation_pipeline.py:144-152` (반환), `stage4_context_builder.py` 전체 — `stage_attempts` 테이블 참조 0건 |
| 영향 경계 | Stage 4 — Stage 2에서 감지된 구조적 문제(중복 의심, 자동 교정 이력, advisory)를 모르고 원고 집필 |
| 테스트 근거 | Stage 4가 Stage 2 에러 컨텍스트를 소비하는 테스트 없음 |
| 기존 중복 여부 | MCS-T3 (stage4-to-stage2-semantic)와 관련되나 에러 전파 관점은 신규 |
| 권장 후속 조치 | Stage 4 context builder에 `stage_attempts` 최근 에러 요약 주입 검토 (4h) — 단, 대원칙 3(디렉터 주권) 존중 필요 |

**분석**: Stage 2의 `run_validation()`은 풍부한 에러 정보를 반환한다:
- `python_advisories`: 자동 감지된 구조적 문제 (severity MAJOR/INFO)
- `corrections_made`: ArcAutoCorrector가 수행한 자동 교정 내역
- `suspected_duplicates`: 중복 의심 Arc 목록

이 정보는 `stage_attempts` 테이블에 JSON으로 저장되지만, Stage 4의 `Stage4ContextBuilder`는 `stage_attempts`를 한 번도 참조하지 않는다. Stage 4는 arc 원본 데이터, world_state, fact_ledger만 소비한다.

**영향**: Stage 2에서 "이 Arc는 3번 자동 교정됨, 중복 의심 있음" 같은 정보가 있어도 Stage 4 Director/Chief Writer는 이를 모른다. 그러나 이는 설계 의도일 수 있다 — Stage 2 Director가 이미 최종 승인한 Arc이므로 Stage 4는 신뢰하고 집필하는 것이 디렉터 주권주의에 부합.

---

### [XC-ERR-013] P2 | Stage 2 → Stage 3 에러 컨텍스트 압축

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-013 |
| Severity | P2 |
| 현상 요약 | Stage 2 validation 결과의 구조적 에러가 Arc JSON에 포함되지 않으면 Stage 3 Blueprint 생성 시 참고 불가 |
| 코드 근거 | `stage3_orchestrator.py:729-736` — `arc_data`만 사용, validation 메타데이터 미참조 |
| 영향 경계 | Stage 3 Blueprint 품질 — Arc의 약점을 보완하는 Blueprint 생성 기회 상실 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | MCS-T2 (stage3-to-stage2-semantic)와 부분 중첩 |
| 권장 후속 조치 | Arc 저장 시 `_validation_summary` 필드 추가 검토 (2h) |

**분석**: Stage 3 `_process_single_episode()`은 `arc_data`(Arc JSON)만 사용한다. Stage 2에서 감지된 validation 이슈(자동 교정 3건, 중복 의심 등)가 Arc JSON에 `_validation_summary` 같은 메타필드로 포함되지 않으면 Stage 3는 Arc를 무결한 것으로 간주한다.

---

### [XC-ERR-014] P2 | stage_attempts 에러 분류 체계의 granularity 부족

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-014 |
| Severity | P2 |
| 현상 요약 | `stage_attempts` 테이블의 `verdict` 컬럼이 PASS/REJECT/ERROR 3단계만 지원 — 실패 원인의 세부 카테고리가 없음 |
| 코드 근거 | `db_manager.py:557-588` (테이블 스키마) |
| 영향 경계 | 실패 분석 — `failure_analyzer.py`가 verdict별 통계를 내지만 "왜 REJECT인지"는 별도 JSON 파싱 필요 |
| 테스트 근거 | `failure_analyzer.py` 테스트에서 verdict 분류는 커버 |
| 기존 중복 여부 | ROP-T3 (structured-sink-alignment)와 부분 관련 |
| 권장 후속 조치 | `failure_category` 컬럼 추가 + `_classify_stage3_failure_category` 패턴 확산 (3h) |

**분석**: Stage 3에는 `_classify_stage3_failure_category()`가 이미 존재하여 `generation_error`, `quality_gate`, `validation_contradiction`, `continuity`, `reject` 등으로 분류한다. 그러나 이 분류 결과가 `stage_attempts` 테이블에 별도 컬럼으로 저장되지 않으며, JSON 내부에 매몰된다.

---

### [XC-ERR-015] P3 | FailureAnalyzer의 sink_alignment_summary가 stage_attempts 로드 실패를 soft_failure로 리포트

| 필드 | 내용 |
|------|------|
| ID | XC-ERR-015 |
| Severity | P3 |
| 현상 요약 | `failure_analyzer.py:219-233`에서 `stage_attempts` 로드 실패 시 `report_soft_failure` + `logging.debug` — 이중 리포팅이나 양쪽 다 무시될 수 있음 |
| 코드 근거 | `failure_analyzer.py:219-233` |
| 영향 경계 | 실패 분석 품질 — 분석기 자체가 데이터를 못 읽으면 의미 없는 빈 결과 반환 |
| 테스트 근거 | 없음 |
| 기존 중복 여부 | 없음 (신규) |
| 권장 후속 조치 | 현행 유지 — 분석기 실패는 비차단 (0h) |

---

## 3. 에러 전파 흐름도

```
Stage 2 Validation
  ├─ python_advisories ──→ stage_attempts.meta (JSON) ──→ FailureAnalyzer만 소비
  ├─ corrections_made ──→ stage_attempts.meta (JSON) ──→ FailureAnalyzer만 소비
  ├─ suspected_duplicates ──→ stage_attempts.meta (JSON) ──→ 미소비
  └─ refined_arc ──→ anchors["arcs"] (JSON) ──→ Stage 3/4 소비 ✓

Stage 3 Blueprint
  ├─ pipeline_result ──→ stage_attempts.meta (JSON) ──→ FailureAnalyzer만 소비
  ├─ failure_category ──→ pipeline_result 내부 (JSON) ──→ 미구조화
  └─ blueprint ──→ blueprints 테이블 ──→ Stage 4 소비 ✓

※ 에러 디테일은 stage_attempts에 JSON으로 저장되나,
  다운스트림 스테이지(Stage 3/4)는 성공 결과물(arcs/blueprints)만 소비.
  에러 컨텍스트의 크로스 스테이지 전파는 없음.
```

---

## 4. Pass 3 최종 판정

| Finding | Pass 1 | Pass 2 | Pass 3 최종 |
|---------|--------|--------|------------|
| XC-ERR-012 | P1 HIGH | P1 — 구조적 갭 확인 | **P1** — 단, 디렉터 주권주의와의 긴장 관계 존재 |
| XC-ERR-013 | P2 MED | P2 확인 | **P2** |
| XC-ERR-014 | P2 MED | P2 확인 | **P2** |
| XC-ERR-015 | P3 LOW | P3 확인 | **P3** |

---

## 5. 설계 의도 고려사항

에러 컨텍스트가 크로스 스테이지로 전파되지 않는 것은 **의도적 설계**일 가능성이 높다:

1. **디렉터 주권주의**: Stage 2 Director가 PASS한 Arc는 "확정"으로 간주. Stage 4가 Stage 2의 에러 이력을 참조하면 Director 결정을 재심사하는 셈
2. **관심사 분리**: 각 Stage는 이전 Stage의 성공 결과물만 소비하는 것이 깔끔한 인터페이스
3. **복잡도 관리**: 에러 컨텍스트 전파를 추가하면 스테이지 간 결합도가 크게 증가

따라서 XC-ERR-012는 "구조적 갭"이나 "수정 필수"가 아닌 **"인지해야 할 설계 트레이드오프"**로 분류하는 것이 적절.
