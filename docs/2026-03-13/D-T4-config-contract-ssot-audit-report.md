# [D-T4] Config, Contract, SSOT 문서 전수 감사 보고서

> **터미널**: Terminal 4
> **작성일**: 2026-03-13
> **범위**: config/ 전량, 전처리_ssot/contracts/ 전량, SSOT 문서, API Contract, Work Guards
> **방법**: 자체 3PASS 감리 (4개 병렬 에이전트 스캔 → 마스터 교차 검증)

---

## 확정 결함 목록

### [D-T4-01] P2 | api-contract-v1.yaml 엔드포인트 누락 4건

**파일**: `docs/implementation/api-contract-v1.yaml`
**비교 대상**: `modules/api/bridge_server.py`

| 엔드포인트 | YAML | bridge_server.py | 상태 |
|-----------|------|------------------|------|
| `POST /run` | ✓ | ✓ L1265 | 일치 |
| `POST /run/{run_id}/input` | ✓ | ✓ L1372 | 일치 |
| `POST /stop` | ✓ | ✓ L1402 | 일치 |
| `GET /status` | ✓ | ✓ L1420 | 일치 |
| `GET /quality/summary` | ✗ | ✓ L1438 | **누락** |
| `GET /quality/dashboard` | ✗ | ✓ L1455 | **누락** |
| `GET /safe-ops/preview` | ✗ | ✓ L1469 | **누락** |
| `POST /quality/review` | ✗ | ✓ L1485 | **누락** |

**영향**: Desktop UI가 이 엔드포인트들을 호출할 경우, API 스펙 문서만으로는 인터페이스 파악 불가.
**확신도**: HIGH — bridge_server.py에서 직접 확인.

---

### [D-T4-02] P2 | 전처리_ssot/contracts/ 8개 계약 파일 — 코드 미연동 (전량 Spec-Only)

**파일**: `전처리_ssot/contracts/` 하위 8개 JSON

| 계약 파일 | 필드 수 | Python 참조 | 상태 |
|-----------|---------|------------|------|
| `schema_version.json` | 11 | 0건 | Spec-Only |
| `artifact_contracts.json` | 27+ | 0건 | Spec-Only |
| `handoff_rules.json` | 5 stages | 0건 | Spec-Only |
| `quality_gates.json` | 4 gate types | 0건 | Spec-Only |
| `stage_machine.json` | 6 stages | 0건 | Spec-Only |
| `profile_catalog.json` | 7 profiles | 0건 | Spec-Only |
| `sequential_run_status.schema.json` | 9 keys | 0건 | Spec-Only |
| `audit_status.schema.json` | 13 keys | 0건 | Spec-Only |

**검증 방법**: `modules/` 전체에서 `artifact_contracts`, `handoff_rules`, `quality_gates`, `stage_machine`, `profile_catalog` grep → 0건.
**판정**: 현재 이 파일들은 **인간 운영자용 참조 문서**로 기능. Python 런타임에서 자동 검증 없음. 전처리 파이프라인이 수동 운영(하네스 스크립트 기반)이므로 현 시점에서는 설계 의도에 부합. 향후 자동화 시 연동 필요.
**확신도**: HIGH — grep 전수 확인.

---

### [D-T4-03] P3 | config/settings.json 부분 사멸 (costs 섹션)

**파일**: `config/settings.json`

```json
{
  "costs": {
    "max_retries": 3,      // ← 코드에서 미참조
    "temperature": 0.8     // ← 코드에서 미참조
  },
  "validation": {
    "use_v0128": true,             // ← director.py L41 에서 사용
    "scoring_threshold": 70,       // ← director_auditor.py에서 병합
    "use_self_consistency": true,   // ← director_auditor.py L272
    "consistency_votes": 3,         // ← director_auditor.py L273
    "use_retrospective": true       // ← director_auditor.py L274
  }
}
```

**활성**: `validation` 섹션 5개 키 → `director_auditor.py` L259-274에서 `settings.json` 로드 후 병합.
**사멸**: `costs` 섹션 2개 키 (`max_retries`, `temperature`) → 코드에서 미참조. `validation.yaml`의 `api_timeout_seconds` 등으로 대체된 것으로 추정.
**확신도**: HIGH — grep 교차 확인.

---

### [D-T4-04] P3 | config/tone_presets.json 프로덕션 미참조

**파일**: `config/tone_presets.json`

**현황**:
- 2개 프리셋만 정의 (카카오 사이다, 네이버 정통)
- `modules/` 전체 grep → **0건** (프로덕션 코드에서 미참조)
- 유일한 참조: `tests/stage3_isolated_test/test_stage3_production.py` L87-91 (테스트에서 로드)

**판정**: Stage 3 테스트에서만 사용되는 사실상 레거시 설정. 프로덕션 파이프라인에서 톤 설정은 별도 경로(장르 YAML + style_guide)로 처리.
**확신도**: HIGH — grep 전수 확인.

---

### [D-T4-05] P3 | prompt-map-v1.json 문서 전용 (코드 미로딩)

**파일**: `docs/implementation/prompt-map-v1.json`

**현황**:
- `run_validator.py` L4에서 주석으로 "키 근거" 참조만 존재
- 실제 `json.load()` 호출 0건, 파라미터 검증은 `run_validator.py`에 하드코딩
- 12개 메뉴 키 + step 정의가 있으나 코드와 분리

**판정**: API 계약 문서로서의 역할만 수행. 코드가 이 파일을 참조하여 자동 검증하지 않으므로, 문서가 코드와 분기될 위험.
**확신도**: HIGH — grep 전수 확인.

---

## 정상 확인 항목 (검사 통과)

### Config 체계

| 항목 | 파일 수 | 결과 |
|------|---------|------|
| **Prompt YAML** | 9개 도메인 | ✓ 전량 코드 참조 확인. `_version` 메타데이터 표준 준수. |
| **장르 YAML** | 10개 | ✓ 전량 BaseGuard._load_genre_yaml() 경유 로드. 필드↔Guard 1:1 매핑 완벽. |
| **analyst_libraries JSON** | 10개 | ✓ 전량 analyst.py genre_library_map 등록. 4-key 구조(narrative_archetypes/intro/ending/transition) 일관. |
| **genre_hints.yaml** | 10개 장르 | ✓ 전량 context_advisor.py _load_genre_hints()에서 로드. |
| **item_suffixes.yaml** | 10장르+_common | ✓ genre_schema_builder.get_item_suffixes() SSOT. 6개 소비자 모듈 확인. |
| **validation.yaml** | 1개 | ✓ _threshold() 함수 경유 전역 SSOT. 장르별 threshold 10종 정의. |
| **models.yaml** | 1개 | ✓ constants.py import-time 로드. 24개 에이전트 모델 배정 + fallback chain. |
| **system.yaml** | 1개 | ✓ thinking_budget_map + API settings + ensemble_timeouts 정의. |
| **style_guide.json** (investment) | 1개 | ✓ style_extractor.py + style_guard.py에서 읽히는 구조 일치. |
| **Work Guard YAML** | 1개 template | ✓ work_guard.py cfg.get() 패턴으로 missing keys 안전 처리. |

### Prompt YAML 키 매핑 (전량 정상)

| 도메인 YAML | 키 수 | 코드 참조 | 미사용 키 |
|------------|-------|----------|----------|
| analyst.yaml | 7 | analyst_prompt_api.py | 0 |
| arc_generator.yaml | 1 | four_phase_arc_generator.py | 0 |
| blueprint_generator.yaml | 2 | three_phase_blueprint_generator.py + stage4_orch | 0 |
| chief_writer.yaml | 9 | chief_writer.py + chief_writer_prompts.py | 0 |
| director.yaml | 5 | director_ensemble.py + director_continuity.py + director_auditor.py | 0 |
| ensemble.yaml | 2 | arc_ensemble.py + blueprint_ensemble.py | 0 |
| emotion_tracker.yaml | 2 | emotion_tracker.py | 0 |
| investment_math_verifier.yaml | 1 | investment_math_verifier.py | 0 |
| writing_directive.yaml | 1 | writing_directive_generator.py | 0 |

### 전처리 SSOT 문서

| 카테고리 | 파일 수 | 문서 부패 | 비고 |
|---------|---------|----------|------|
| blockguide/*.md | ~19개 | 0건 감지 | 최종 수정 2026-03-09~12, 교차참조 유효 |
| 기획안/*.md | 21개 | 해당없음 | 10개 장르 1:1 대응 + 11개 추가 컨셉 |
| SSOT_stage0_preprocess_integrated_order.md | 1개 | 0건 감지 | Stage 0 전처리 통합 오더 |

---

## 오탐 제거 로그

### PASS 1 → PASS 2 제거

| 후보 | 확신도 | 제거 사유 |
|------|--------|----------|
| "MANUSCRIPT_HISTORY_CONFLICT_PROMPT 미사용" | LOW | FP-3: director_continuity.py L466/L806에서 YAML 로드, director.py L12에서 Python fallback import. 양쪽 경로 모두 활성. |
| "DIRECTOR_AUDIT_PROMPT_V30 director.yaml에 없음" | LOW | FP-2: director.yaml L907에 존재 확인. 에이전트 오보. |
| "genre_hints.yaml '채본' 오타" | LOW | FP-2: 실제 파일 L13은 "채권" (정상). 에이전트 환각. |
| "item_suffixes.yaml 미사용" | LOW | FP-3: genre_schema_builder.get_item_suffixes() + 6개 소비자 모듈(arc_draft_validator, constraint_compiler, state_tracker_plots, arc_ensemble, prompt_builder, semantic_item_registry) 확인. |
| "genre_hints.yaml fantasy/cooking/medical 누락" | LOW | FP-2: 실제 파일에 10개 장르 전량 존재 (L19-60). |
| "Work Guard YAML 필드 부족" | MED | FP-1: cfg.get(key, default) 패턴으로 missing keys 안전 처리. 템플릿 설계 의도. |
| "settings.json validation 섹션 중복" | MED | FP-4: director_auditor.py가 settings.json에서 validation 키를 로드하여 default_config에 병합 (L259-274). 실제 사용 중. |

### 집계

**PASS 1**: 12건 후보 → **PASS 2**: 7건 오탐 제거 → **최종 5건 확정**

---

## 문서 부패 현황

**문서 부패 0건 감지.**

- blockguide 문서 19개: 전량 2026-03-09~12 작성, 교차 참조 유효
- 기획안 21개: 장르 매핑 정상
- SSOT 통합 오더: Stage 0 흐름과 일치

---

## 요약

| Severity | 건수 | 내용 |
|----------|------|------|
| P0 | 0 | - |
| P1 | 0 | - |
| P2 | 2 | api-contract 엔드포인트 누락 4건, 계약 JSON 8개 코드 미연동 |
| P3 | 3 | settings.json costs 사멸, tone_presets.json 미참조, prompt-map-v1.json 문서전용 |

**Config 체계 건강도**: 핵심 Config(prompts YAML 9개, genres YAML 10개, analyst_libraries 10개, validation.yaml, models.yaml, system.yaml, item_suffixes.yaml, genre_hints.yaml, style_guide.json) **전량 정상**. 코드↔Config 1:1 매핑 완벽.

**계약 체계**: 전처리 SSOT 계약 8개는 현재 인간 운영자용 참조 문서로 기능하며, 전처리가 수동 하네스 방식이므로 현 시점에서는 설계 의도에 부합.

**오탐률**: PASS1 12건 → 최종 5건 확정 (오탐률 58%)
