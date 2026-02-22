# Opus TF Validation & Quality System Audit Report

**작성일**: 2026-02-22
**감사자**: Claude Opus 4.6 (자동화 코드 감사)
**범위**: Validation Pipeline 전체 (6-Tier) + Guard 체인 + Director 연계
**기준선**: 2,114 passed + 68 xfailed, Ruff 0 violations

---

## 1. 요약

글도비의 Validation & Quality 시스템은 6-Tier 파이프라인(PRE_LLM → CONTINUITY → BLOCKING → CONSISTENCY → SCORING → ADVISORY)으로 구성되어 있으며, 전반적으로 견고한 설계를 보여준다. 그러나 아래와 같은 이슈가 발견되었다.

| 심각도 | 건수 | 핵심 |
|--------|------|------|
| P0 (차단급) | 0건 | 즉시 수정 필요한 치명적 버그 없음 |
| P1 (품질 이슈) | 5건 | 장르 확장 미반영, 데드코드, 예외 흡수 등 |
| P2 (경미/스타일) | 4건 | 누락 설정 키, 미지원 장르 폴백 등 |
| 개선 아이디어 | 7건 | 팩토리 패턴 통일, 병렬화, 로깅 등 |

**결론**: P0 차단급 버그는 없으나, P1급 장르 확장 미반영 문제가 복수 지점에서 확인됨. 10개 장르 중 3개(wuxia/hunter/investment)만 완전 지원되는 구간이 있어 나머지 7개 장르에서 품질 열화 가능성이 있다.

---

## 2. P0 차단급 버그

**해당 없음** -- 현재 시점에서 데이터 손실이나 무한루프, 보안 취약점 등 즉시 수정이 필요한 P0 버그는 발견되지 않았다.

---

## 3. P1 품질 이슈

### P1-01: ScoringValidator._load_guard_for_genre() — 8개 장르 누락

**파일**: `modules/validation/scoring_validator.py` L62-79
**증상**: `_load_guard_for_genre()` 메서드가 `wuxia`와 `hunter`만 처리하고, 나머지 8개 장르(investment, fantasy, composer, cooking, alt_history, actor, sports, medical)는 `return None`으로 빠진다.

```python
def _load_guard_for_genre(self, genre: str):
    if not genre:
        return None
    try:
        if genre == "wuxia":
            from modules.core.genre_guards.wuxia_guard import WuxiaGuard
            return WuxiaGuard()
        elif genre == "hunter":
            from modules.core.genre_guards.hunter_guard import HunterGuard
            return HunterGuard()
        else:
            return None  # <-- 8개 장르가 여기로 빠짐
```

**영향**: `self.guard`가 `None`이면 `_generate_dynamic_context()`에서 장르별 검증 규칙이 LLM 프롬프트에 삽입되지 않는다. 채점 자체는 동작하지만 장르 특화 컨텍스트가 누락되어 LLM 채점 정확도가 저하된다.

**수정 제안**: `create_genre_guard()` 팩토리를 재활용한다.

```python
def _load_guard_for_genre(self, genre: str):
    if not genre:
        return None
    try:
        from modules.core.genre_guards import create_genre_guard
        return create_genre_guard(genre)
    except Exception as e:
        logging.warning(f"[WARNING] Guard 로드 실패 ({genre}): {e}")
        return None
```

---

### P1-02: ScoringValidator.GENRE_WEIGHTS — 7개 장르 누락

**파일**: `modules/validation/scoring_validator.py` L684-723
**증상**: `GENRE_WEIGHTS` 딕셔너리에 `wuxia`, `hunter`, `investment` 3개만 정의되어 있다. `validate_v59()`에서 미등록 장르는 wuxia 폴백으로 처리된다 (L746: `self.GENRE_WEIGHTS.get(genre, self.GENRE_WEIGHTS["wuxia"])`).

```python
GENRE_WEIGHTS = {
    "wuxia": { ... },
    "hunter": { ... },
    "investment": { ... },
    # fantasy, composer, cooking, alt_history, actor, sports, medical 누락
}
```

**영향**: 7개 장르에서 장르 특성과 무관한 무협 가중치가 적용된다. 예를 들어 의학 장르에서 `sensory_balance: 1.3`(무술 동작용)이 적용되고, 작곡 장르에서 `reader_satisfaction: 1.3`(경지돌파/복수용)이 적용된다.

**수정 제안**: 각 장르별 가중치 프로파일을 추가한다. 최소한 `fantasy`, `composer`, `cooking`, `alt_history`, `actor`, `sports`, `medical` 7개를 추가해야 한다.

---

### P1-03: ValidationOrchestrator.validate() — PreLLM 데드코드 (도달 불가 분기)

**파일**: `modules/validation/validation_orchestrator.py` L250-273
**증상**: PreLLMValidator는 V60.56에서 `passed: True`를 항상 반환하도록 변경되었다 (`pre_llm_validator.py` L132). 그러나 ValidationOrchestrator의 `validate()` 메서드(L255)와 `validate_parallel_v59()` 메서드(L1026)에서 여전히 `if not pre_llm_result["passed"]` 분기를 검사하여 REJECT를 반환하는 코드가 존재한다.

```python
# pre_llm_validator.py L132
"passed": True,  # [V60.56] 항상 통과, LLM이 최종 판단

# validation_orchestrator.py L255
if not pre_llm_result["passed"]:  # <-- 절대 True가 될 수 없음
    return { "final_decision": "REJECT", ... }
```

**영향**: 직접적인 기능 장애는 없다. 그러나:
1. 코드 리더에게 "PreLLM이 REJECT할 수 있다"는 잘못된 인상을 준다.
2. 향후 PreLLM을 다시 활성화할 때 이 분기가 자동으로 살아나는데, 의도적 설계 변경인지 데드코드인지 구분이 안 된다.
3. `_generate_pre_llm_feedback()` 등 관련 메서드도 호출될 수 없는 상태다.

**수정 제안**: 두 가지 중 하나를 선택한다:
- (A) 데드코드 제거: PreLLM 결과를 advisory 정보로만 활용하고, REJECT 분기를 삭제한다.
- (B) 의도적 유지: 주석으로 "V60.56에서 비활성화됨, 향후 재활성화 가능" 표시를 추가한다.

---

### P1-04: BlockingValidator — 관계/정보 일관성 검증 예외 흡수

**파일**: `modules/validation/blocking_validator.py` L178-190
**증상**: `_check_relationship_consistency()`와 `_check_information_consistency()`가 모든 예외를 catch하여 `passed: True, degraded: True`를 반환한다.

```python
def _check_relationship_consistency(self, manuscript: str, context: dict) -> dict:
    try:
        return self.consistency_checks._check_relationship_consistency(manuscript, context)
    except Exception as e:
        logging.warning(f"[C-3] relationship consistency check failed (degraded): {e}")
        return {"check": "relationship_consistency", "passed": True, "degraded": True, "error": str(e)}
```

**영향**: 이 두 검증기에서 `ImportError`, `TypeError`, `KeyError` 등 프로그래밍 오류가 발생해도 원고가 통과한다. `degraded` 플래그는 로그에 기록되지만, blocking 판정에는 `passed: True`로 반영되므로 실질적으로 무시된다.

**완화 요인**:
- `validate()` 메서드(L111-116)에서 두 검증 모두 degraded이면 경고 카운터를 증가시킨다.
- 이 패턴은 C-3 수정(Validator 체인 수정) 시 의도적으로 도입된 것이다.

**수정 제안**: 예외 유형을 세분화한다. `ImportError`/`AttributeError` 등 프로그래밍 오류는 re-raise하고, 데이터 기반 오류(`ValueError`, `KeyError`)만 degraded로 처리한다.

```python
except (ValueError, KeyError) as e:
    # 데이터 문제 → degraded
    return {"check": "...", "passed": True, "degraded": True, "error": str(e)}
except Exception:
    raise  # 프로그래밍 오류는 조기 발견
```

---

### P1-05: CatharsisTimer — 카타르시스/좌절 지표 장르 불완전

**파일**: `modules/validation/catharsis_timer.py` L22-61
**증상**: `CATHARSIS_INDICATORS`와 `FRUSTRATION_INDICATORS`에 `common`, `wuxia`, `hunter`, `investment` 4가지만 정의되어 있다. `fantasy`, `composer`, `cooking`, `alt_history`, `actor`, `sports`, `medical` 7개 장르의 장르별 카타르시스/좌절 키워드가 없다.

**영향**: 7개 장르에서는 `common` 키워드만으로 카타르시스 감지가 이루어진다. 예를 들어 스포츠 장르의 "우승", "MVP", "결승골" 같은 핵심 카타르시스 키워드가 누락되고, 의학 장르의 "수술 성공", "완치" 같은 키워드도 누락된다.

**수정 제안**: 7개 장르별 카타르시스/좌절 키워드 세트를 추가한다.

---

## 4. P2 경미/스타일 이슈

### P2-01: validation.yaml — advisory.pacing_para_limit 키 누락

**파일**: `config/settings/validation.yaml`
**참조**: `modules/validation/advisory_validator.py` L204
**증상**: AdvisoryValidator의 `_check_pacing()` 메서드가 `_threshold("advisory.pacing_para_limit", 2000)`으로 임계값을 로드하지만, `validation.yaml`에 이 키가 정의되어 있지 않다. 기본값 `2000`이 항상 사용된다.

**영향**: 기능적 문제 없음 (기본값이 적절). 그러나 validation.yaml이 "Single Source of Truth"를 표방하므로, 사용되는 모든 임계값이 명시되어야 일관성이 있다.

**수정 제안**: `validation.yaml`의 `advisory:` 섹션에 `pacing_para_limit: 2000`을 추가한다.

---

### P2-02: GENRE_THRESHOLD_PROFILES — 7개 장르 누락

**파일**: `modules/validation/validation_orchestrator.py` L80-102
**증상**: `GENRE_THRESHOLD_PROFILES`에 `wuxia`, `hunter`, `investment` 3개만 정의되어 있다. 미등록 장르는 L207에서 wuxia 폴백:

```python
self.threshold_profile = GENRE_THRESHOLD_PROFILES.get(genre, GENRE_THRESHOLD_PROFILES["wuxia"])
```

**영향**: 7개 장르에서 적응형 임계값의 base_threshold와 가중치가 무협 기준으로 적용된다. P1-02와 동일한 장르 확장 미반영 패턴.

---

### P2-03: ScoringValidator.GENRE_THRESHOLDS — 불완전한 장르 목록

**파일**: `modules/validation/scoring_validator.py` L29-33
**증상**: 클래스 변수 `GENRE_THRESHOLDS`에 `wuxia(70)`, `hunter(68)`, `investment(72)` 3개만 정의. `fantasy(70)`가 `validation.yaml`에는 있지만 코드에는 없다.

```python
# scoring_validator.py L29-33
GENRE_THRESHOLDS = {
    "wuxia": 70,
    "hunter": 68,
    "investment": 72,
    # fantasy: 70 — validation.yaml에만 존재, 코드 미반영
}
```

**영향**: `__init__`에서 `genre_thresholds` 딕셔너리를 빌드할 때 `GENRE_THRESHOLDS` 기반이므로, fantasy 장르는 `default_threshold(70)`로 폴백된다. 결과적으로 동일한 70점이 적용되어 실질적 차이는 없지만, YAML과 코드 간 불일치가 존재한다.

---

### P2-04: validate_v59 — weighted_percentage와 raw_total 단위 불일치 (저위험)

**파일**: `modules/validation/scoring_validator.py` L799-801
**증상**: `weighted_percentage`는 0-100 퍼센트이고 `raw_total`은 0-100 점수인데, 이 둘의 차이를 `_genre_delta`로 계산한다.

```python
_genre_delta = round(weighted_percentage) - raw_total
capped_score = raw_total + max(-1, min(1, _genre_delta))
```

**영향**: `max(-1, min(1, _genre_delta))`로 캡핑되어 있어 최대 +-1점 변동. TF-C02 의도대로 Python 판단 최소화가 적용되어 있으므로 실질적 위험은 매우 낮다.

**참고**: 가중치가 모두 1.0이면 `weighted_percentage == raw_total`이 되어 delta=0. 가중치가 다르면 delta가 발생하지만 +-1 캡핑으로 안전하다.

---

## 5. 연결성(Connectivity) 분석

### 5.1 Guard 체인: Genre -> Work -> Style (정상)

- `create_genre_guard()` 팩토리가 10개 장르 모두 지원 (`genre_guards/__init__.py` L22-56).
- `WorkGuard`가 GenreGuard를 래핑하여 작품별 금기어/패턴 추가 (`work_guard.py`).
- `StyleGuard`가 최종 래핑하여 문체 기반 검증 추가 (`style_guard.py`).
- Director의 `QualityAuditor`가 Guard의 `run_deep_validation()` 다형적 호출을 사용 (`director_auditor.py`).
- **결론**: Guard 체인은 완전하게 연결되어 있다.

### 5.2 validation.yaml -> threshold_helper -> 각 Validator (정상)

- `threshold_helper.py`가 `ConfigManager`를 lazy init하여 YAML 값을 제공.
- 키 누락 시 Python 기본값으로 안전 폴백.
- 모든 주요 Validator가 `_threshold()` 함수를 사용 중.
- **예외**: `advisory.pacing_para_limit` 키가 YAML에 없음 (P2-01 참조).

### 5.3 ValidationOrchestrator -> Director 전달 (정상)

- ValidationOrchestrator의 결과가 `final_decision`, `total_score`, `feedback`, `detailed_feedback` 등으로 구조화되어 Director에 전달된다.
- Director는 `_evaluate_with_director()` 호출로 LLM 기반 최종 판단을 수행하며, ValidationOrchestrator 결과를 참조 컨텍스트로 사용한다.
- Director 주권주의 원칙(대원칙 #3)이 잘 지켜지고 있다.

### 5.4 적응형 임계값 -> ScoringValidator (정상, 주의사항 있음)

- `calculate_adaptive_threshold_v59()`가 임계값을 계산한 후 `self.scoring.pass_threshold`를 직접 변경한다.
- 조기 반환 시와 정상 반환 시 모두 `_original_threshold`로 복원하는 코드가 있다 (TF-R2-XC-01, G11).
- **주의**: `validate_parallel_v59()`의 Stage 2 병렬 실행 중 예외 발생 시 임계값이 복원되지 않을 수 있다. try/finally 패턴이 아닌 수동 복원 패턴을 사용하고 있다.

### 5.5 품질 회귀 감지 / 크로스 에피소드 반복 / 만족도 추적 (미확인)

- `modules/core/quality_regression.py`, `modules/core/cross_episode_repetition.py`, `modules/core/satisfaction_tracker.py` 파일이 존재하지 않는다.
- `quality_regression` 설정이 `validation.yaml` L130-134에 정의되어 있으나, 이를 소비하는 Python 모듈이 확인되지 않았다.
- `cross_episode_repetition` 설정이 `validation.yaml` L155-160에 정의되어 있으나, 동일하게 소비 모듈 미확인.
- `satisfaction` 설정이 `validation.yaml` L163-165에 정의되어 있으나, 동일하게 소비 모듈 미확인.
- 관련 기능은 Stage4 오케스트레이터나 다른 모듈에 인라인으로 구현되어 있을 수 있다. (`stage4_post_processor.py`와 `quality_dashboard.py`에서 `quality_regression` 참조 확인됨.)

---

## 6. 개선 아이디어

### I-01: ScoringValidator에 create_genre_guard() 팩토리 도입

**현재**: `_load_guard_for_genre()`에서 if/elif로 wuxia/hunter만 수동 처리.
**제안**: `create_genre_guard()` 팩토리 함수를 호출하여 10개 장르 전체 자동 지원.
**효과**: P1-01 해결 + 향후 장르 추가 시 ScoringValidator 수정 불필요.
**난이도**: 낮음 (3줄 변경)

---

### I-02: 7개 장르 GENRE_WEIGHTS / GENRE_THRESHOLD_PROFILES / CatharsisTimer 확장

**현재**: wuxia/hunter/investment 3개만 장르별 가중치/프로파일/카타르시스 키워드 보유.
**제안**: fantasy, composer, cooking, alt_history, actor, sports, medical 7개 장르 프로파일 추가.
**효과**: P1-02, P1-05, P2-02 일괄 해결.
**난이도**: 중간 (각 장르별 가중치 튜닝 필요, 도메인 지식 필요)

---

### I-03: PreLLM 데드코드 정리 또는 재활성화 설계

**현재**: PreLLM은 항상 `passed: True`를 반환하지만, Orchestrator에 REJECT 분기가 남아 있다.
**제안 A**: 데드코드 제거 -- PreLLM 결과를 advisory 컨텍스트로만 활용.
**제안 B**: `validation.yaml`에 `pre_llm.can_reject: false` 플래그를 추가하고, Orchestrator에서 이를 참조하여 분기를 명시적으로 제어.
**효과**: 코드 가독성 향상 + 의도 명확화.

---

### I-04: BlockingValidator 예외 처리 세분화

**현재**: 모든 `Exception`을 catch하여 `passed: True`로 처리.
**제안**: `ValueError`/`KeyError` 같은 데이터 오류만 degraded 처리하고, `ImportError`/`AttributeError`/`TypeError` 같은 프로그래밍 오류는 re-raise.
**효과**: 프로그래밍 오류의 조기 발견 + 원고 품질 열화 방지.

---

### I-05: 적응형 임계값 복원에 try/finally 패턴 적용

**현재**: `validate()`와 `validate_parallel_v59()`에서 조기 반환마다 수동으로 `self.scoring.pass_threshold = _original_threshold`를 호출한다. 모든 경로에서 복원이 보장되지만, 향후 코드 변경 시 누락 위험이 있다.

**제안**: try/finally 패턴으로 임계값 복원을 보장한다.

```python
_original_threshold = self.scoring.pass_threshold
try:
    if self.use_adaptive_threshold:
        self.scoring.pass_threshold = adaptive_threshold
    # ... 검증 로직 ...
    return results
finally:
    self.scoring.pass_threshold = _original_threshold
```

---

### I-06: validation.yaml에 누락된 임계값 키 추가

**현재**: 코드에서 `_threshold()`로 참조하지만 YAML에 없는 키가 있다.
**확인된 누락 키**:
- `advisory.pacing_para_limit` (기본값 2000)

**제안**: YAML SSOT 원칙에 따라 모든 사용 키를 validation.yaml에 명시한다.

---

### I-07: 장르별 검증 커버리지 매트릭스 문서화

**현재**: 어떤 장르가 어떤 검증에서 장르 특화 처리를 받는지 한눈에 파악하기 어렵다.
**제안**: 다음과 같은 커버리지 매트릭스를 작성한다.

| 검증 모듈 | wuxia | hunter | investment | fantasy | composer | cooking | alt_history | actor | sports | medical |
|-----------|-------|--------|------------|---------|----------|---------|-------------|-------|--------|---------|
| Guard | O | O | O | O | O | O | O | O | O | O |
| ScoringValidator.guard | O | O | X | X | X | X | X | X | X | X |
| GENRE_WEIGHTS | O | O | O | X | X | X | X | X | X | X |
| GENRE_THRESHOLD_PROFILES | O | O | O | X | X | X | X | X | X | X |
| CatharsisTimer | O | O | O | X | X | X | X | X | X | X |
| GENRE_THRESHOLDS | O | O | O | X | X | X | X | X | X | X |

**효과**: 장르 추가 체크리스트(CLAUDE.md)에 Validation 항목이 추가되어 누락 방지.

---

## 7. 아키텍처 총평

### 7.1 강점

1. **6-Tier 파이프라인**: 명확한 계층 분리(차단 → 채점 → 권고)로 각 계층의 책임이 분명하다.
2. **적응형 임계값**: 에피소드 유형, 연속 통과/실패, 패턴 분석, 아크 위치 4가지 축으로 동적 조정하며, floor(60)/ceiling(90) 안전장치가 있다.
3. **Self-Consistency**: 애매한 구간(70-85)에서만 3-vote를 실행하는 조건부 방식으로 비용 60% 절감.
4. **Guard 체인**: Genre → Work → Style 3중 래핑으로 범용성과 작품 특화를 모두 지원.
5. **Director 주권주의**: Validator는 정보 제공만, 최종 판단은 Director LLM이 수행. 대원칙 #3 준수.
6. **TF-C02 +-1 캡**: 장르 가중치의 Python 판단 영향력을 +-1점으로 제한. 대원칙 #1 존중.
7. **threshold_helper**: 모든 임계값을 YAML에서 로드하되 기본값 폴백으로 안전성 확보.

### 7.2 주의 영역

1. **장르 확장 미반영**: Guard 체인은 10개 장르 완전 지원이지만, Scoring/Catharsis/ThresholdProfile은 3개 장르만 완전 지원. 장르 추가 체크리스트(CLAUDE.md)에 Validation 모듈 항목이 누락되어 있다.
2. **PreLLM 역할 모호**: V60.56에서 REJECT 권한을 제거했지만 Orchestrator 코드에 REJECT 분기가 남아 있어 의도가 불명확.
3. **예외 흡수 패턴**: BlockingValidator의 관계/정보 일관성 검증이 모든 예외를 흡수. 의도적 설계이나 프로그래밍 오류까지 흡수할 위험.

---

## 8. CLAUDE.md 장르 체크리스트 업데이트 권장

현재 CLAUDE.md의 "Genre Addition Integrity Checklist"(16개 항목)에 다음 항목을 추가할 것을 권장한다:

```
17. scoring_validator.py (GENRE_WEIGHTS + GENRE_THRESHOLDS + _load_guard_for_genre)
18. validation_orchestrator.py (GENRE_THRESHOLD_PROFILES)
19. catharsis_timer.py (CATHARSIS_INDICATORS + FRUSTRATION_INDICATORS)
```

---

## 9. 파일별 참조 목록

| 파일 | 이슈 | 비고 |
|------|------|------|
| `modules/validation/scoring_validator.py` | P1-01, P1-02, P2-03, P2-04 | 장르 확장 집중 |
| `modules/validation/validation_orchestrator.py` | P1-03, P2-02, I-05 | 데드코드 + 프로파일 |
| `modules/validation/blocking_validator.py` | P1-04 | 예외 흡수 |
| `modules/validation/catharsis_timer.py` | P1-05 | 카타르시스 키워드 |
| `modules/validation/advisory_validator.py` | P2-01 | pacing 키 |
| `modules/validation/pre_llm_validator.py` | P1-03 관련 | always True |
| `modules/validation/threshold_helper.py` | - | 정상 |
| `config/settings/validation.yaml` | P2-01 | 누락 키 |
| `modules/core/genre_guards/__init__.py` | - | 정상 (10개 완전) |
| `modules/core/genre_guards/base_guard.py` | - | 정상 |
| `modules/core/genre_guards/work_guard.py` | - | 정상 |
| `modules/core/genre_guards/style_guard.py` | - | 정상 |
| `modules/domain/agents/director.py` | - | 정상 |
| `modules/domain/agents/director_auditor.py` | - | 정상 |
| `modules/domain/agents/director_grading.py` | - | 정상 |
| `modules/core/foreshadow_tracker.py` | - | 정상 |
| `modules/core/semantic_plot_guard.py` | - | 정상 |
| `modules/core/vec_memory.py` | - | 정상 |

---

*End of Audit Report*
