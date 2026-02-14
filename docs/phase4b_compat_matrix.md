# Phase 4B Compatibility Matrix: 구↔신 경로 매핑 + 시그니처 규칙

> 작성일: 2026-02-13
> SSOT: (1) 코드베이스 (커밋 `1b3de64`), (2) Phase 4B 문서군(`docs/phase4b_*.md`)
> 원칙: **호출자 무변경** — stage2/stage4 오케스트레이터의 `self.app.xxx()` 호출 경로 100% 보존

---

## 1. 경로 매핑 총괄표

### 1-1. AuditService (Batch 4B-1)

| 호출자 | 구 경로 (현재) | 신 경로 (4B 이후) | 시그니처 변경 |
|--------|-------------|-----------------|-------------|
| `stage2_orch:*` (36건) | `self.app._audit_event(type, msg, data)` | `self.app._audit_event(type, msg, data)` → Facade → `self._audit.audit_event(type, msg, data)` | **없음** |
| `stage2_orch:*` | `self.app._write_audit_summary(tag)` | Facade → `self._audit.write_audit_summary(tag)` | **없음** |
| `main_a.py` 내부 | `self._flush_audit_buffer()` | Facade → `self._audit.flush_audit_buffer()` | **없음** |

**Facade 스텁 (main_a.py 잔류)**:
```python
# main_a.py — Batch 4B-1 이후
def _audit_event(self, event_type, message, data=None):
    return self._audit.audit_event(event_type, message, data)
def _flush_audit_buffer(self):
    return self._audit.flush_audit_buffer()
def _write_audit_summary(self, tag="snapshot"):
    return self._audit.write_audit_summary(tag)
```

### 1-2. FeedbackEnricher (Batch 4B-2)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `stage4_orch:*` | `self.app._enrich_director_result(audit_result, stage, content_length)` | Facade → `self._feedback.enrich_director_result(audit_result, stage, content_length)` | **없음** |
| `stage4_orch:*` | `self.app._analyze_score_breakdown(breakdown)` | Facade → `self._feedback.analyze_score_breakdown(breakdown)` | **없음** |
| `stage4_orch:*` | `self.app._quantify_reject_feedback(reason, cl, ar)` | Facade → `self._feedback.quantify_reject_feedback(reason, cl, ar)` | **없음** |
| `stage2_orch:*` | `self.app._generate_structured_arc_feedback(...)` | Facade → `self._feedback.generate_structured_arc_feedback(...)` | **없음** |
| `stage2_orch:*` | `self.app._generate_arc_context_v60(...)` | Facade → `self._feedback.generate_arc_context_v60(...)` | **없음** |
| `stage4_orch:*` | `self.app._generate_writer_guidance_v60_8(...)` | Facade → `self._feedback.generate_writer_guidance_v60_8(...)` | **없음** |
| `stage4_orch:*` | `self.app._simplify_prompt_for_retry(...)` | Facade → `self._feedback.simplify_prompt_for_retry(...)` | **없음** |
| `stage4_orch:*` | `self.app._build_strong_kind_feedback(...)` | Facade → `self._feedback.build_strong_kind_feedback(...)` | **없음** |
| `stage4_orch:*` | `self.app._build_focused_context(...)` | Facade → `self._feedback.build_focused_context(...)` | **없음** |
| `stage4_orch:*` | `self.app._build_minimal_arc_context(...)` | Facade → `self._feedback.build_minimal_arc_context(...)` | **없음** |
| `stage4_orch:*` | `self.app._generate_arc_position_guide(...)` | Facade → `self._feedback.generate_arc_position_guide(...)` | **없음** |
| `stage4_orch:*` | `self.app._get_adaptive_feedback_intensity(...)` | Facade → `self._feedback.get_adaptive_feedback_intensity(...)` | **없음** |
| `stage4_orch:*` | `self.app._analyze_rejection_pattern_v60(...)` | Facade → `self._feedback.analyze_rejection_pattern_v60(...)` | **없음** |
| `stage4_orch:*` | `self.app._get_dynamic_critical_keywords()` | Facade → `self._feedback.get_dynamic_critical_keywords()` | **없음** |

### 1-3. NarrativeSummary (Batch 4B-2)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `stage4_orch:*` | `self.app._generate_narrative_summary(up_to_ep)` | Facade → `self._narrative.generate_narrative_summary(up_to_ep)` | **없음** |
| `stage4_orch:*` | `self.app._load_narrative_summaries()` | Facade → `self._narrative.load_narrative_summaries()` | **없음** |

### 1-4. ValidationHelpers (Batch 4B-3)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `stage2_orch:*` | `self.app._validate_arc_mapping(...)` | Facade → `self._validation.validate_arc_mapping(...)` | **없음** |
| `stage2_orch:*` | `self.app._validate_arc_data_fields(...)` | Facade → `self._validation.validate_arc_data_fields(...)` | **없음** |
| `stage2_orch:*` | `self.app._validate_arc_integrity(...)` | Facade → `self._validation.validate_arc_integrity(...)` | **없음** |
| `stage4_orch:*` | `self.app._load_genre_references()` | Facade → `self._validation.load_genre_references()` | **없음** |
| `stage2_orch:*` | `self.app._extract_pattern_keywords(...)` | Facade → `self._validation.extract_pattern_keywords(...)` | **없음** |
| `stage2_orch:*` | `self.app._pattern_presence_check(...)` | Facade → `self._validation.pattern_presence_check(...)` | **없음** |
| `stage4_orch:*` | `self.app._extract_npc_profiles(...)` | Facade → `self._validation.extract_npc_profiles(...)` | **없음** |
| `stage4_orch:*` | `self.app._get_character_traits()` | Facade → `self._validation.get_character_traits()` | **없음** |
| `stage4_orch:*` | `self.app._get_archetype_reference_for_npcs(...)` | Facade → `self._validation.get_archetype_reference_for_npcs(...)` | **없음** |
| `stage2_orch:*` | `self.app._build_validation_context(...)` | Facade → `self._validation.build_validation_context(...)` | **없음** |
| `stage2_orch:*` | `self.app._classify_rejection_feedback(...)` | Facade → `self._validation.classify_rejection_feedback(...)` | **없음** |
| `stage4_orch:*` | `self.app._validate_blueprint_integrity(...)` | Facade → `self._validation.validate_blueprint_integrity(...)` | **없음** |

### 1-5. DataManager (Batch 4B-3)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `_run_main_process:1891` | `self._reset_stage_2()` | Facade → `self._data_mgr.reset_stage_2()` | **없음** |
| `_run_main_process:1893` | `self._rewind_stage_2()` | Facade → `self._data_mgr.rewind_stage_2()` | **없음** |
| `_run_main_process:1887` | `self._rollback_episode()` | Facade → `self._data_mgr.rollback_episode()` | **없음** |
| `_run_main_process:1889` | `self._wipe_production_data()` | Facade → `self._data_mgr.wipe_production_data()` | **없음** |

### 1-6. Stage3Orchestrator (Batch 4B-4)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `_run_main_process:1879` | `self._stage_3_batch_blueprinting()` | Facade → `self._stage3_orch.stage_3_batch_blueprinting()` | **없음** |

### 1-7. Stage0Orchestrator (Batch 4B-4)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `_run_main_process:1866` | `self._phase_0_recovery()` | Facade → `self._stage0_orch.phase_0_recovery()` | **없음** |
| `_run_main_process:1868` | `self._stage_1_volumes()` | Facade → `self._stage0_orch.stage_1_volumes()` | **없음** |

### 1-8. AppBootstrap + StageDispatcher (Batch 4B-5)

| 호출자 | 구 경로 | 신 경로 | 시그니처 변경 |
|--------|--------|--------|-------------|
| `boot:886` | `self._run_main_process()` | Facade → `self._dispatcher.run_main_process()` | **없음** |
| `__main__:4402` | `SovereignApp().boot()` | `SovereignApp().boot()` → Facade → `self._bootstrap.boot()` | **없음** |

---

## 2. 시그니처 규칙

### 규칙 S1: 원본 시그니처 100% 보존

추출 모듈의 public 메서드는 원본 `main_a.py` 메서드와 **동일한 시그니처**를 유지해야 한다. 단, `self` 파라미터는 추출 모듈의 인스턴스를 가리킨다.

```python
# 원본 (main_a.py:281)
def _enrich_director_result(self, audit_result: dict, stage: int, content_length: int = 0) -> dict:

# 추출 후 (feedback_enricher.py)
def enrich_director_result(self, audit_result: dict, stage: int, content_length: int = 0) -> dict:
```

**언더스코어 제거 규칙**: 추출 모듈에서는 `_` 접두사를 제거한다 (private → public). Facade 스텁은 원본 이름을 유지한다.

### 규칙 S2: Facade 스텁은 `*args, **kwargs` 금지

Facade 스텁은 **명시적 파라미터**를 사용한다. `*args, **kwargs` 패스스루는 타입 검사를 무력화하므로 금지.

```python
# ✅ 올바른 Facade 스텁
def _enrich_director_result(self, audit_result: dict, stage: int, content_length: int = 0) -> dict:
    return self._feedback.enrich_director_result(audit_result, stage, content_length)

# ❌ 금지
def _enrich_director_result(self, *args, **kwargs):
    return self._feedback.enrich_director_result(*args, **kwargs)
```

**예외**: `_audit_event`은 `data=None` 기본값이 있으므로 명시적 3-파라미터 스텁 사용.

### 규칙 S3: 반환 타입 보존

추출 메서드의 반환 타입은 원본과 동일해야 한다. 특히 다음 메서드는 반환 타입이 호출자의 분기 로직에 직접 사용됨:

| 메서드 | 반환 타입 | 호출자 분기 |
|--------|----------|-----------|
| `_enrich_director_result` | `dict` | `stage4_orch`에서 `result["decision"]` 체크 |
| `_load_narrative_summaries` | `str` | `stage4_orch`에서 빈 문자열 체크 |
| `_validate_arc_integrity` | `bool` | `stage2_orch`에서 True/False 분기 |
| `_validate_blueprint_integrity` | `bool` | `stage3`에서 True/False 분기 |
| `_load_genre_references` | `tuple[list, list]` | 구조 분해 할당 |
| `_get_arc_context_for_episode` | `tuple[int\|None, dict\|None]` | None 체크 분기 |

---

## 3. 브리지 함수 상세

### 3-1. DI 조립 지점 (main_a.py `__init__`)

Phase 4B에서 `__init__`에 추가해야 할 서비스 인스턴스화:

```python
class SovereignApp:
    def __init__(self):
        # ... 기존 속성 (55개) 유지 ...

        # [Phase 4B] 추출 서비스 인스턴스화
        from modules.core.services.audit_service import AuditService
        from modules.core.feedback_enricher import FeedbackEnricher
        from modules.core.narrative_summary import NarrativeSummary
        from modules.core.validation_helpers import ValidationHelpers
        from modules.core.data_manager import DataManager

        self._audit = AuditService(self)           # Batch 4B-1
        self._feedback = FeedbackEnricher(self)     # Batch 4B-2
        self._narrative = NarrativeSummary(self)    # Batch 4B-2
        self._validation = ValidationHelpers(self)  # Batch 4B-3
        self._data_mgr = DataManager(self)          # Batch 4B-3

        # Batch 4B-4 (Stage 오케스트레이터는 boot() 시점에 생성)
        # Batch 4B-5 (Bootstrap/Dispatcher도 boot() 시점)
```

### 3-2. 추출 모듈의 `self.app` 참조 패턴

모든 추출 모듈은 `self.app` 참조를 통해 SovereignApp 속성에 접근한다 (V64 Facade 표준):

```python
class AuditService:
    def __init__(self, app):
        self.app = app  # SovereignApp 참조

    def audit_event(self, event_type, message, data=None):
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "type": event_type,
            "message": message,
            "data": data or {},
        }
        self.app.runtime_audit.append(event)   # self → self.app
        self.app._audit_buffer.append(event)    # self → self.app
```

### 3-3. 순환 참조 방지 규칙

추출 모듈 간 직접 import 금지. 크로스 참조는 `self.app` 경유:

```python
# ❌ 금지: 추출 모듈 간 직접 import
from modules.core.services.audit_service import AuditService  # validation_helpers.py에서

# ✅ 올바름: self.app 경유
class ValidationHelpers:
    def validate_arc_mapping(self, refined_arc, ...):
        self.app._audit_event("mapping_fix", ...)  # app의 Facade 스텁 경유
```

이는 Phase 4C에서 `self.app` 제거 시 Protocol 기반 DI로 전환할 기반을 마련한다.

---

## 4. 구/신 경로 공존 타임라인

```
Phase 4A (현재, 완료)
├── Protocol 정의만 존재
├── 실제 코드 경로: main_a.py 내부 메서드 직접 실행
└── self.app.xxx() → main_a.py 메서드 직접 실행

Phase 4B-1~4B-3 (구/신 공존 시작)
├── main_a.py: Facade 스텁 (3줄) + 추출 모듈 (실질 로직)
├── 호출 경로: self.app.xxx() → Facade 스텁 → self._xxx.method()
└── ⚠️ 오버헤드: 메서드 호출 1회 추가 (ns 단위, LLM 호출 대비 무시 가능)

Phase 4B-4~4B-5 (구/신 공존 최대)
├── main_a.py: ~1,200줄 (DI + Facade 스텁 ~200줄 + __init__ + _safe_commit)
├── 9개 추출 모듈: ~3,490줄 (실질 로직 전량)
└── 기존 호출 경로: 100% 유지

Phase 4C (공존 해소)
├── stage2/stage4: self.app.xxx() → self.service.method() 직접 호출
├── main_a.py: Facade 스텁 제거 → ~1,000줄
└── 최종 아키텍처: Protocol 기반 DI
```

---

## 5. Feature Flag / 브리지 함수 필요 여부

| 항목 | 필요 여부 | 근거 |
|------|----------|------|
| Feature flag | **불필요** | 브랜치 전략으로 충분. 런타임 분기는 복잡성만 증가 |
| 브리지 함수 (Facade 스텁) | **필수** | main_a.py에 66개 Facade 스텁 잔류 (Phase 4C까지) |
| import 호환성 shim | **불필요** | 추출 모듈은 신규 파일, 기존 import 경로 무변경 |
| 설정 파일 변경 | **불필요** | 런타임 설정 변경 없음 |
| DB 스키마 변경 | **불필요** | DB 구조 무변경 |

---

## 6. 검증 매트릭스

### Facade 스텁 정합성 검증 명령

```powershell
# 4B 완료 후 실행: Facade 스텁 수와 추출 메서드 수 일치 확인
$facade_count = (Select-String -Pattern '^\s+def _\w+\(self.*return self\._' main_a.py).Count
$extracted_count = 66  # phase4b_scope.md 합계
Write-Host "Facade: $facade_count / Expected: $extracted_count"
```

### 호출 경로 무변경 검증

```bash
# stage2/stage4에서 self.app 호출 패턴 변동 없음 확인
# Phase 4B 전후 동일해야 함
grep -c "self\.app\." modules/core/stage2_orchestrator.py  # 기대: 335
grep -c "self\.app\." modules/core/stage4_orchestrator.py  # 기대: 300
```
