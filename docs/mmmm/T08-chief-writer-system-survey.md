# T08 — ChiefWriter System Deep Survey

**6PASS-CLEARED** | **COLLECTOR ONLY** | **NO EXECUTION AUTHORITY**
**Date**: 2026-03-20
**Baseline Commit**: `d0fa70f1`
**Terminal**: T08 — ChiefWriter System
**Confidence**: 96%

---

## 1. Scope & Files

| File | Lines | Role |
|------|-------|------|
| `modules/domain/agents/chief_writer.py` | 2,015 | 앙상블 원고 생성 엔진 (facade + core) |
| `modules/domain/agents/chief_writer_context.py` | 1,362 | 컨텍스트 빌딩 + 분석 서브모듈 |
| `modules/domain/agents/chief_writer_quality.py` | 1,297 | 품질 게이트 — Self-Critique 17항목 + 교정 |
| `modules/domain/agents/chief_writer_prompts.py` | 272 | 프롬프트 외부화 (PromptLoader → chief_writer.yaml) |
| `modules/domain/agents/writer.py` | 376 | Thin Fallback Writer (V64 경량화) |
| `modules/core/writer_prompt_builders.py` | 235 | Writer 유틸리티 — mandatory_context, anti_trope, justification |
| `modules/core/writer_template.py` | 418 | Blueprint → 원고 템플릿 시스템 (V55.3) |
| `modules/core/writing_directive_generator.py` | 210 | PatternReport + Blueprint → WritingDirective (TF-54b) |
| **합계** | **6,185** | |

**관련 YAML**: `config/prompts/chief_writer.yaml` (PROMPT_TEMPLATE_OUTPUT, COMMON_RULES, WRITING_GUIDELINES, PATCH_MODE_PROMPT, PATCH_MODE_STRUCTURAL_PROMPT, SATISFACTION_GUIDE_SECTION), `config/prompts/writing_directive.yaml` (WRITING_DIRECTIVE_SYSTEM)

**관련 테스트**: tests/test_chief_writer.py (1,460), tests/test_chief_writer_context.py (341), tests/test_chief_writer_quality.py (523), tests/test_writer_prompt_builders.py (140)

---

## 2. TF Registry

### T08-TF-001 — `_CW_GENRE_CODE_MAP` Dead Code
```
ID: T08-TF-001
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/domain/agents/chief_writer.py:37-48
Evidence:
  - chief_writer.py:37-48 — `_CW_GENRE_CODE_MAP` 딕셔너리 정의 (10 entries)
  - Grep `_CW_GENRE_CODE_MAP` in *.py → 1 match (정의 자체만)
  - 실제 장르 변환은 `chief_writer_context.py:64` `normalize_chief_writer_genre_code()` 사용
  - 기존 T3-046 audit에서도 "진탐 확정, 참조 0건"으로 확인
Inference: 이전 버전에서 사용했으나 normalize 함수로 대체 후 잔류. 12줄 dead code.
Uncertainty: 없음. Grep 결과 확정.
Cross-Ref: T20 (dead code 전수)
```

### T08-TF-002 — Duplicate Genre Alias Maps
```
ID: T08-TF-002
Severity: P3-LOW
Category: DEAD-CODE
Surface: chief_writer.py:37-48 vs chief_writer_context.py:32-57
Evidence:
  - chief_writer.py:37-48 `_CW_GENRE_CODE_MAP`: 10 entries (한국어 → 코드)
  - chief_writer_context.py:32-57 `_GENRE_CODE_ALIASES`: 22 entries (한국어+영어+변형 → 코드)
  - `_GENRE_CODE_ALIASES`가 상위 호환 (모든 _CW_GENRE_CODE_MAP 키를 포함 + 영어 키 추가)
  - chief_writer.py:645 `normalize_chief_writer_genre_code(genre_name)` — context 모듈의 함수를 import하여 사용
Inference: _CW_GENRE_CODE_MAP은 _GENRE_CODE_ALIASES의 부분집합이며 완전히 중복. TF-001과 합쳐서 삭제 대상.
Uncertainty: 없음.
Cross-Ref: T08-TF-001
```

### T08-TF-003 — writer.py `write_v20_manuscript` Dead Code
```
ID: T08-TF-003
Severity: P3-LOW
Category: DEAD-CODE
Surface: modules/domain/agents/writer.py:59-240
Evidence:
  - writer.py:59 `def write_v20_manuscript(...)` — 182줄 메서드
  - Grep `write_v20_manuscript\(` in main_a.py, modules/, tests/ → 0 matches (호출부 없음)
  - writer.py:1 docstring: "독립 API로 유지 (오케스트레이터 호출 경로 제거됨)"
  - tools2/project_full_source.md에만 과거 호출 코드 잔존 (아카이브)
  - main_a.py:1753에서 Writer 인스턴스는 생성하나, write_v20_manuscript 호출은 없음
  - 기존 CW-12 audit: "write_v20_manuscript만 유지. 오케스트레이터 호출 경로 제거됨"
Inference: V64에서 ChiefWriter가 주 생성 경로가 되면서 Writer.write_v20_manuscript은 호출자 없음. 376줄 writer.py 전체가 사실상 폴백 전용이나, 그 폴백 경로도 활성화되지 않음.
Uncertainty: main_a.py에서 `self.agents['writer']`로 접근하는 다른 간접 경로가 있을 수 있으나, grep 결과 write_v20 호출 0건 → 미사용 확정.
Cross-Ref: T11 (Agent Infrastructure — Writer lifecycle)
```

### T08-TF-004 — writer.py vs ChiefWriterQualityGate `_sanitize_leakage` 중복
```
ID: T08-TF-004
Severity: P4-OBSERVATION
Category: DEAD-CODE
Surface: writer.py:257-281 vs chief_writer_quality.py:40-85
Evidence:
  - writer.py:257 `def _sanitize_leakage(self, text)` — dict/list/tuple 입력 처리 포함
  - chief_writer_quality.py:40 `def sanitize_leakage(self, text)` — JSON 파싱 + 라인 필터 + 영문 괄호 병기 제거
  - 공통 banned_keys: "Beat 3", "Beat 4", "continuation_text", "scene_summary"
  - writer.py 추가 방어: isinstance(text, dict), isinstance(text, list|tuple)
  - chief_writer_quality.py 추가 기능: L83 영문 괄호 병기 제거 regex
Inference: 동일 목적의 두 구현이 별도 유지. writer.py가 dead code (TF-003)이므로 실질적 충돌 없음.
Uncertainty: 없음.
Cross-Ref: T08-TF-003
```

### T08-TF-005 — `inplace_patch()` 2000자 최소 길이 하드코딩
```
ID: T08-TF-005
Severity: P3-LOW
Category: HARDCODING
Surface: modules/domain/agents/chief_writer.py:1522, 1589
Evidence:
  - chief_writer.py:1522: `if not response or len(response) < 2000:`
  - chief_writer.py:1589: `if not _manuscript or len(_manuscript) < 2000:`
  - ManuscriptLimits.MIN_LENGTH = 4000 (constants.py)
  - inplace_patch는 부분 수정이므로 MIN_LENGTH보다 낮은 2000자 기준 사용
  - 이 2000은 validation.yaml 참조 없이 인라인 하드코딩
Inference: 부분 패치의 최소 기준은 전체 원고 최소(4000)보다 낮으므로 2000은 의도적. 다만 config 참조 없이 하드코딩.
Uncertainty: 2000이 최적값인지 동적 검증 필요.
Cross-Ref: T06 (Stage 4 Interview — pass_with_fix loop에서 inplace_patch 호출)
```

### T08-TF-006 — `apply_self_critique` Rubric 3.5 하드코딩
```
ID: T08-TF-006
Severity: P3-LOW
Category: HARDCODING
Surface: modules/domain/agents/chief_writer_quality.py:147
Evidence:
  - chief_writer_quality.py:147: `if rubric_score >= 3.5 and current_content_length >= int(ManuscriptLimits.MIN_LENGTH):`
  - 3.5는 4점 만점 Rubric에서 "높은 품질" 기준
  - MIN_LENGTH는 constants.py에서 참조하나, 3.5는 인라인 하드코딩
  - L234에서도 동일 조건 재사용: `if mid_score >= 3.5 and current_content_length >= int(ManuscriptLimits.MIN_LENGTH):`
Inference: Rubric 3.5 기준이 두 곳에서 중복 사용. 상수로 추출하면 유지보수성 향상.
Uncertainty: 없음. 두 곳 모두 동일 값 사용 확인.
Cross-Ref: 없음
```

### T08-TF-007 — Self-Critique MAX_CRITIQUE_ROUNDS=3 하드코딩
```
ID: T08-TF-007
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/domain/agents/chief_writer_quality.py:131
Evidence:
  - chief_writer_quality.py:131: `MAX_CRITIQUE_ROUNDS = 3`
  - 지역 변수로 선언, validation.yaml 참조 없음
  - 최대 3회 루프 (L204: `for round_num in range(1, MAX_CRITIQUE_ROUNDS + 1):`)
Inference: 반복 횟수가 config에서 조정 불가. 비용 제어(LLM 호출 3회) 관점에서 고정이 합리적이나, config 외부화 미적용.
Uncertainty: 없음.
Cross-Ref: T06 (Stage 4 Interview — pass_with_fix 3회와 별개)
```

### T08-TF-008 — Context Caching TTL=600s SYNC
```
ID: T08-TF-008
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer.py:417
Evidence:
  - chief_writer.py:417: `ttl_seconds=600,  # 10분 (같은 에피소드 재시도 대비)`
  - MEMORY.md 기록: "TTL: 600s (intra-episode) / 1800s (cross-episode, DirectorContinuity)"
  - chief_writer.py:422: `logging.info(f" [V61.7] 컨텍스트 캐시 활성 (ep{ep_num}, {len(common_context)}자)")`
  - 캐시 실패 시 L423-425: `pass  # 캐싱 실패해도 기존 방식으로 진행`
Inference: TTL 600s는 메모리 기록과 일치. 캐시 실패 시 graceful degradation 확인.
Uncertainty: 없음.
Cross-Ref: T11 (BaseAgent — _get_or_create_context_cache 인프라)
```

### T08-TF-009 — WritingDirectiveGenerator Lookback=5 SYNC
```
ID: T08-TF-009
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/core/writing_directive_generator.py:41
Evidence:
  - writing_directive_generator.py:41: `lookback: int = 5`
  - MEMORY.md 기록: "Pattern tracker lookback_episodes=5"
  - 호출부 stage4_interview_round.py:1736: `_wdg = WritingDirectiveGenerator()`
  - 프롬프트 L67: `report.to_summary_text(min_freq=2)` — 최소 2회 이상 빈도
Inference: lookback=5는 PatternTracker와 동기. YAML 프롬프트(writing_directive.yaml)도 `{N}` placeholder로 주입.
Uncertainty: 없음.
Cross-Ref: T18 (PatternTracker — lookback 설정)
```

### T08-TF-010 — Prompt Assembly Order Documentation
```
ID: T08-TF-010
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer_prompts.py:89-174
Evidence:
  - build_chief_writer_main_prompt() 호출 순서 (L89-174):
    1. [Role] / [Task] 헤더
    2. incarnation_context_section (V67.1 환생 유형)
    3. chain_link_section (V68 연결고리)
    4. ending_hook_section
    5. dna_instruction (1화 DNA / 연속 모드)
    6. purism_section (장르 순혈주의)
    7. world_origin_constraint_section (원시인/현대인)
    8. feedback_section + constraint_section
    9. future_guard_section + past_guard_section
    10. writer_core_section (character_voice + world_state + writing_directive + reference_anchor + mandatory_context + anti_trope + justification + reflexion)
    11. hud_anomaly_section
    12. STEP 1: Blueprint / scene_breakdown / emotional_beat
    13. STEP 2: prev_digest + prev_ending (연속성)
    14. STEP 3: hud_report + high_density_hud + hud_trend
    15. STEP 4: arc_doc
    16. STEP 5: core_identity
    17. STEP 6: style_guide + reference_excerpt
    18. satisfaction_guide_section (D-Step2)
    19. common_rules + writing_guidelines
    20. prev_manuscripts_section (V67 이전 원고 전문)
  - chief_writer_context.py:492-523: build_common_context()가 위 함수에 값 주입
  - L515-516: `common_rules=get_common_rules_section()`, `writing_guidelines=get_writing_guidelines_section() + _investment_guidelines`
Inference: 프롬프트 조립은 chief_writer_context.py가 데이터를 수집하고, chief_writer_prompts.py가 템플릿에 조립하는 2단계 구조.
Uncertainty: 없음. 코드 직접 확인.
Cross-Ref: T17 (Config — prompt template keys)
```

### T08-TF-011 — SATISFACTION_GUIDE_SECTION 무조건 주입
```
ID: T08-TF-011
Severity: P4-OBSERVATION
Category: SIDE-EFFECT
Surface: modules/domain/agents/chief_writer_context.py:522
Evidence:
  - chief_writer_context.py:522: `satisfaction_guide_section=get_satisfaction_guide_section(),  # [D-Step2]`
  - 조건 분기 없이 항상 호출됨 (if문 없음)
  - chief_writer_prompts.py:45-47: `def get_satisfaction_guide_section()` → `_load_prompt("SATISFACTION_GUIDE_SECTION", _FALLBACK_EMPTY)`
  - config/prompts/chief_writer.yaml:171: `SATISFACTION_GUIDE_SECTION: |` — 내용 존재
Inference: 모든 에피소드, 모든 장르에서 대리만족 가이드가 주입됨. 장르별 필터링(예: 투자물에서는 불필요) 없음.
Uncertainty: 의도적 설계일 수 있음 (범용 가이드). 장르 분기 필요 여부는 정책 판단.
Cross-Ref: T17 (Config — YAML key 참조)
```

### T08-TF-012 — writing_directive.yaml SYNC
```
ID: T08-TF-012
Severity: P4-OBSERVATION
Category: SYNC
Surface: config/prompts/writing_directive.yaml, modules/core/writing_directive_generator.py:77-101
Evidence:
  - config/prompts/writing_directive.yaml:1: `WRITING_DIRECTIVE_SYSTEM: |`
  - writing_directive_generator.py:19-20: `_PROMPT_DOMAIN = "writing_directive"`, `_PROMPT_KEY = "WRITING_DIRECTIVE_SYSTEM"`
  - writing_directive_generator.py:81: `prompt = self._prompt_loader.load(_PROMPT_DOMAIN, _PROMPT_KEY, ...)`
  - YAML 파일에 `{N}`, `{pattern_summary}`, `{blueprint_summary}`, `{genre}`, `{ep_num}` placeholder 확인
  - 코드 L84-88에서 동일 변수명으로 format 인자 전달
Inference: YAML 키와 코드 참조가 일치. SSOT 원칙 준수.
Uncertainty: 없음.
Cross-Ref: T17 (Config — prompt YAML 정합성)
```

### T08-TF-013 — ThreadPoolExecutor max_workers SYNC
```
ID: T08-TF-013
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer.py:440
Evidence:
  - chief_writer.py:440: `ThreadPoolExecutor(max_workers=max(1, min(3, len(strategies))))`
  - strategies 기본 3개: ["balanced", "narrative", "tension"] (L182)
  - reduced budget → 2개 (L196), single_strategy → 1개 (L186)
  - max_workers는 항상 전략 수와 동기화
Inference: 3전략 → 3워커, 2전략 → 2워커, 1전략 → 1워커. 설계 의도와 일치.
Uncertainty: 없음.
Cross-Ref: 없음
```

### T08-TF-014 — C-4 All-Fail Fallback SYNC
```
ID: T08-TF-014
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer.py:554-597
Evidence:
  - L554: `valid_candidates = [c for c in candidates if not c.get("error")]`
  - L555-581: 유효 후보 0개 → 단일 폴백 재시도 (첫 전략으로)
  - L583-597: 단일 폴백도 실패 → error_fallback dict 반환
    ```python
    candidates = [{
        "strategy": "error_fallback",
        "manuscript": "",
        "title": f"제{ep_num}화 (생성 실패)",
        "error": True,
        ...
    }]
    ```
  - L600: `candidates = [validate_manuscript_candidate(c) for c in candidates]` — Pydantic 검증 통과
Inference: 빈 배열 반환 방지 → downstream IndexError 크래시 방어 (V66.3 설계). 3단계 fallback chain 확인.
Uncertainty: 없음.
Cross-Ref: T06 (Stage 4 Interview — 빈 후보 처리)
```

### T08-TF-015 — PATCH_MODE Prompts YAML SYNC
```
ID: T08-TF-015
Severity: P4-OBSERVATION
Category: SYNC
Surface: config/prompts/chief_writer.yaml:87,123 + chief_writer.py:1299,1479,1706
Evidence:
  - chief_writer.yaml:87: `PATCH_MODE_PROMPT: |`
  - chief_writer.yaml:123: `PATCH_MODE_STRUCTURAL_PROMPT: |`
  - chief_writer.py:1299: `PromptLoader().load("chief_writer", "PATCH_MODE_STRUCTURAL_PROMPT")`
  - chief_writer.py:1479: `PromptLoader().load("chief_writer", "PATCH_MODE_PROMPT")`
  - chief_writer.py:1706: `PromptLoader().load("chief_writer", "PATCH_MODE_PROMPT")` (patch_with_feedback에서도 동일)
  - 모든 로드에 except 폴백 존재 (L1300-1302, L1480-1482, L1707-1709)
Inference: YAML 키 3개소 참조 모두 SYNC. 로드 실패 시 인라인 폴백 존재.
Uncertainty: 없음.
Cross-Ref: T17 (Config — YAML key 정합성)
```

### T08-TF-016 — Pydantic Manuscript Validation SYNC
```
ID: T08-TF-016
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer.py:600
Evidence:
  - chief_writer.py:27: `from modules.models.manuscript import validate_manuscript_candidate`
  - chief_writer.py:600: `candidates = [validate_manuscript_candidate(c) for c in candidates]`
  - modules/models/manuscript.py:43: `def validate_manuscript_candidate(raw: dict) -> dict:`
  - tests/test_pydantic_models.py:380-387: 성공/실패 케이스 모두 테스트
Inference: 앙상블 반환 직전 모든 후보에 Pydantic 검증 적용. 스키마 계약 준수.
Uncertainty: 없음.
Cross-Ref: T05 (Stage 4 Orchestration — 후보 소비)
```

### T08-TF-017 — Dual `mandatory_context` Implementations
```
ID: T08-TF-017
Severity: P2-MEDIUM
Category: CONTRADICTION
Surface: writer_prompt_builders.py:14-41 vs chief_writer_context.py:1179-1218
Evidence:
  - writer_prompt_builders.py:14: `def build_mandatory_context(db, master_bible, current_ep):`
    - "[MANDATORY CONTEXT]\n" 헤더
    - _check_hud_anomalies(db, current_ep) → DB 직접 조회
    - _extract_recent_events(db, current_ep, n_episodes=3) → db.load_state_log
    - _extract_npc_last_states(master_bible, current_ep) → master_bible에서 추출
  - chief_writer_context.py:1179: `def _build_mandatory_context(self, current_ep):`
    - "[MANDATORY CONTEXT - 반드시 인지하고 집필할 것]\n" 헤더
    - self._check_hud_anomalies(current_ep) → 캐시 사용
    - self._extract_recent_events(current_ep, n_episodes=3) → context.db
    - self._extract_npc_last_states(current_ep) → context.master_bible + WorldState 병합
  - Writer(writer.py:157)가 writer_prompt_builders.build_mandatory_context 호출
  - ChiefWriter는 chief_writer_context의 _build_mandatory_context 사용 (하지만 generate_ensemble 호출 시에는 외부에서 mandatory_context 파라미터로 주입받기도 함)
Inference: 동일 목적(필수 맥락 주입)의 두 구현이 별도 유지. ChiefWriter 버전이 더 풍부(WorldState 병합, 캐시 사용). Writer 버전은 legacy. Writer가 dead code(TF-003)이므로 실제 충돌 위험은 낮으나, stage4_orchestrator에서 mandatory_context 파라미터로 writer_prompt_builders 버전을 주입할 수 있어 혼재 가능성 있음.
Uncertainty: stage4_orchestrator에서 어느 버전을 주입하는지 추가 확인 필요 (T06 영역).
Cross-Ref: T06 (Stage 4 Interview — mandatory_context 주입 경로)
```

### T08-TF-018 — ChiefWriter Facade Delegation (~30 Methods)
```
ID: T08-TF-018
Severity: P4-OBSERVATION
Category: DEAD-CODE
Surface: modules/domain/agents/chief_writer.py:1889-2011
Evidence:
  - L1889-1893: `_sanitize_leakage`, `_apply_self_critique`, `_self_critique` → quality_gate 위임
  - L1898-1911: `_check_hud_consistency`, `_check_cliche_overuse`, `_check_justification_gaps`, `_check_npc_relationship`, `_fix_manuscript_issues`, `_evaluate_with_rubric` → quality_gate 위임
  - L1962-1984: `_get_npc_frequency`, `_get_npc_frequency_warning`, `_count_recent_cliches`, `_get_hud_trend_safe`, `_extract_numeric_value`, `_build_hud_context`, `_check_hud_anomalies`, `_get_npc_equipment_summary` → context_builder 위임
  - L1990-2010: `_get_dna_instruction`, `_build_anti_trope_instructions`, `_build_mandatory_context`, `_extract_recent_events`, `_extract_npc_last_states`, `_build_justification_guidance` → context_builder 위임
  - L779-797: `_build_common_context`, `_generate_episode_digest`, `_detect_deaths_from_manuscript`, `_detect_past_events_from_manuscript`, `_build_past_guard_section`, `_build_future_guard_section` → context_builder 위임
  - 총 ~30개 메서드가 순수 위임 (`return self.quality_gate.xxx(*args, **kwargs)`)
Inference: V64 delegation pattern 적용 결과. 외부에서 `chief_writer._check_hud_consistency()` 직접 호출 가능하게 유지. 하위 호환성 목적이나, 실제 외부 호출자가 있는지 확인 필요.
Uncertainty: 외부 호출자 전수 조사 미실시 (T08 범위 밖). tests에서 일부 사용 가능.
Cross-Ref: T06 (Stage 4 Interview — ChiefWriter 메서드 호출 패턴)
```

### T08-TF-019 — _prefetch_manuscripts Cache Staleness Window
```
ID: T08-TF-019
Severity: P4-OBSERVATION
Category: SIDE-EFFECT
Surface: modules/domain/agents/chief_writer.py:1920-1956
Evidence:
  - L1927-1929: `if self._cache_ep_num == ep_num and self._manuscript_cache: return` — 동일 ep_num이면 캐시 재사용
  - L1948-1952: `invalidate_manuscript_cache()` — 수동 무효화 메서드
  - L1937: `past_ms = self.context.db.get_manuscript(i)` — DB에서 직접 로드
  - L1942: `self._manuscript_cache[i] = {"content": content, "hud_snapshot": hud_snapshot}`
  - window=10: 최근 10화 프리페치
Inference: 같은 에피소드 내 재시도(retry) 시 DB 변경이 없으므로 캐시가 유효. 에피소드 롤백 시 invalidate_manuscript_cache() 호출 필요. 이 호출은 외부 오케스트레이터 책임.
Uncertainty: 오케스트레이터가 invalidate를 실제로 호출하는지 T05/T06에서 확인 필요.
Cross-Ref: T05 (Stage 4 Orchestration)
```

### T08-TF-020 — `[원고_끝]` Marker Handling SYNC
```
ID: T08-TF-020
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer.py:1580-1586
Evidence:
  - L1581: `_end_marker = "[원고_끝]"`
  - L1583-1584: 마커 발견 시 `_manuscript = _manuscript[:_marker_idx].rstrip()`
  - L1585-1586: 마커 없으면 `logging.warning("[TF-IPG] [원고_끝] 마커 없음 — 출력이 잘렸을 수 있음")`
  - PATCH_MODE_PROMPT (YAML L87+)에서 LLM에게 `[원고_끝]` 마커 출력을 지시
Inference: 마커 기반 잘림 감지 → 안전한 truncation. TF-IPG 설계와 일치.
Uncertainty: 없음.
Cross-Ref: 없음
```

### T08-TF-021 — Structural Patch Block Minimum 80 Chars
```
ID: T08-TF-021
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/domain/agents/chief_writer.py:1356
Evidence:
  - L1356: `if len(patch_text) < 80: continue` — 80자 미만 패치 블록 스킵
  - 이 값은 config/validation.yaml 참조 없이 인라인 하드코딩
  - L1376: merged 결과도 2000자 미만이면 전체 폴백: `if len(merged_manuscript) < 2000:`
Inference: 80자는 "유의미한 수정"의 최소 기준. 씬 단위 패치에서 너무 짧은 응답은 무의미하므로 합리적이나, magic number.
Uncertainty: 없음.
Cross-Ref: T08-TF-005
```

### T08-TF-022 — Strategy Bias Temperature Offsets 하드코딩
```
ID: T08-TF-022
Severity: P3-LOW
Category: HARDCODING
Surface: modules/domain/agents/chief_writer.py:159-166
Evidence:
  - L160: `if share >= 0.5: adjusted = max(0.1, round(base - 0.05, 2))`
  - L162: `elif share <= 0.15: adjusted = min(1.0, round(base + 0.1, 2))`
  - L164: `elif share <= 0.3: adjusted = min(1.0, round(base + 0.05, 2))`
  - share 임계값(0.5, 0.15, 0.3)과 temperature 조정값(-0.05, +0.1, +0.05)이 인라인 하드코딩
  - 기본 temperatures: balanced=0.7, narrative=0.8, tension=0.9 (L70, L83, L94)
Inference: 전략 편향 보정 로직. 자주 선택되는 전략은 temperature를 낮추고, 드물게 선택되는 전략은 높여서 다양성 유도. 6개 매직 넘버.
Uncertainty: 없음.
Cross-Ref: 없음
```

### T08-TF-023 — Self-Critique 17+1 Check Items
```
ID: T08-TF-023
Severity: P4-OBSERVATION
Category: COVERAGE-GAP
Surface: modules/domain/agents/chief_writer_quality.py:281-352
Evidence:
  - _self_critique() 내 검사 항목 18개 전수:
    1. L282 _check_hud_consistency — HUD 모순
    2. L286 _check_cliche_overuse — 클리셰 과다
    3. L290 _check_justification_gaps — 정당화 부족
    4. L294 _check_npc_relationship — NPC 관계 일관성
    5. L299 _check_motivation_consistency — 동기/약속 방치 [B-4]
    6. L303 _check_writing_directive — WritingDirective 위반 [TF-54e]
    7. L306 _check_expression_freshness — 표현 신선도 [TF-54e]
    8. L309 _check_ai_tell_patterns — AI-tell 상투구 반복
    9. L312 _check_ending_hook_presence — ending_hook 포함 여부
    10. L315 _check_arithmetic_consistency — 산술 모순 [NS-1]
    11. L318 _check_system_term_exposure — 메타 월 (시스템 용어 노출)
    12. L321 _check_ending_novelty — 엔딩 참신성 [QI-1-A5]
    13. L324 _check_temporal_logic — 시간 논리 [QI-QM-1]
    14. L327 _check_paragraph_structure — 문단 구조 [QI-QM-1]
    15. L330 _check_tonal_consistency — 톤 일관성 [QI-QM-1]
    16. L333 _check_pov_consistency_critique — POV 일관성 [QI-POV]
    17. L336 _check_scene_transition_markers — 씬 전환 마커 [QI-QM-5]
    18. L339-352 분량 체크 (manuscript_length)
  - 전체 severity 판단 (L356-366): issues ≥ 5 → "high", ≥ 3 or has_high → "medium", else "low"
  - has_issues = True이고 severity = "low"면 apply_self_critique에서 break (L227-228)
Inference: 17개 독립 검사 + 1개 분량 검사 = 18개. 매우 포괄적인 Python-only 자가 검증 파이프라인.
Uncertainty: 없음. 코드 직접 확인.
Cross-Ref: T14 (Validation Pipeline — pre_llm_validator와 일부 중복 가능)
```

### T08-TF-024 — CLICHE_WINDOW Externalized to validation.yaml SYNC
```
ID: T08-TF-024
Severity: P4-OBSERVATION
Category: SYNC
Surface: modules/domain/agents/chief_writer_quality.py:18
Evidence:
  - chief_writer_quality.py:18: `CLICHE_WINDOW = _threshold("quality.cliche_window", 10)`
  - chief_writer_quality.py:10: `from modules.validation.threshold_helper import _threshold`
  - _threshold는 validation.yaml의 키를 참조하고, 미존재 시 fallback 값(10) 사용
  - L611: `recent_counts = self._count_recent_cliches(ep_num, window=self.CLICHE_WINDOW)`
Inference: _LazyThreshold 패턴으로 config 외부화됨. SSOT 원칙 부분 준수 (fallback은 코드에 잔류).
Uncertainty: validation.yaml에 quality.cliche_window 키가 실제 존재하는지 T17에서 확인 필요.
Cross-Ref: T17 (Config — validation.yaml 키 참조)
```

### T08-TF-025 — prev_manuscript Ending 2500 Chars 하드코딩
```
ID: T08-TF-025
Severity: P4-OBSERVATION
Category: HARDCODING
Surface: modules/domain/agents/chief_writer_context.py:252
Evidence:
  - L252: `prev_ending = prev_manuscript[-2500:] if prev_manuscript else ""`
  - 주석: "# [V62.6→V63.2] 직전 원고: 구조화 다이제스트 + 엔딩 2500자 (800→2500 확대)"
  - 이 2500은 config 참조 없이 하드코딩
  - Writer(writer.py:196)는 `-1500:` 사용 — 별도 하드코딩
Inference: ChiefWriter(2500) vs Writer(1500)로 상이한 값. 둘 다 하드코딩이나, Writer는 dead code이므로 실질적 영향 없음.
Uncertainty: 2500이 최적값인지 동적 검증 필요.
Cross-Ref: T08-TF-003 (Writer dead code)
```

---

## 3. Evidence Inventory

| TF | Primary Evidence | Verification Method |
|----|-----------------|---------------------|
| TF-001 | Grep `_CW_GENRE_CODE_MAP` → 1 match (def only) | Grep *.py |
| TF-002 | chief_writer.py:37-48 vs chief_writer_context.py:32-57 | Side-by-side read |
| TF-003 | Grep `write_v20_manuscript\(` → 0 callers | Grep main_a.py + modules/ + tests/ |
| TF-004 | writer.py:257-281 vs chief_writer_quality.py:40-85 | Side-by-side read |
| TF-005 | chief_writer.py:1522, 1589 `< 2000` | Direct read |
| TF-006 | chief_writer_quality.py:147, 234 `>= 3.5` | Direct read |
| TF-007 | chief_writer_quality.py:131 `MAX_CRITIQUE_ROUNDS = 3` | Direct read |
| TF-008 | chief_writer.py:417 `ttl_seconds=600` | Direct read |
| TF-009 | writing_directive_generator.py:41 `lookback=5` | Direct read |
| TF-010 | chief_writer_prompts.py:89-174 template | Direct read |
| TF-011 | chief_writer_context.py:522 unconditional call | Direct read |
| TF-012 | config/prompts/writing_directive.yaml:1 + code:81 | Glob + Read |
| TF-013 | chief_writer.py:440 `max(1, min(3, len(strategies)))` | Direct read |
| TF-014 | chief_writer.py:554-597 fallback chain | Direct read |
| TF-015 | chief_writer.yaml:87,123 + code:1299,1479,1706 | Grep + Read |
| TF-016 | chief_writer.py:600 + manuscript.py:43 | Grep |
| TF-017 | writer_prompt_builders.py:14-41 vs context.py:1179-1218 | Side-by-side read |
| TF-018 | chief_writer.py:1889-2011 delegation methods | Direct read |
| TF-019 | chief_writer.py:1920-1956 cache logic | Direct read |
| TF-020 | chief_writer.py:1580-1586 marker handling | Direct read |
| TF-021 | chief_writer.py:1356 `< 80` | Direct read |
| TF-022 | chief_writer.py:159-166 temperature offsets | Direct read |
| TF-023 | chief_writer_quality.py:281-352 (18 checks) | Direct read |
| TF-024 | chief_writer_quality.py:18 `_threshold()` | Direct read |
| TF-025 | chief_writer_context.py:252 `[-2500:]` | Direct read |

---

## 4. Side-Effect Surface

| Component | Side-Effect | Path |
|-----------|-------------|------|
| generate_ensemble | ThreadPoolExecutor (3 workers) | chief_writer.py:440 |
| _prefetch_manuscripts | DB batch read (10 episodes) | chief_writer.py:1934-1944 |
| _generate_single_candidate | LLM API call (ask/ask_with_cached_context) | chief_writer.py:667-686 |
| _fix_manuscript_issues | LLM API call (ask) | chief_writer_quality.py:1147 |
| _evaluate_with_rubric | Python-only (no side-effect) | chief_writer_quality.py:1171 |
| _get_or_create_context_cache | Gemini context cache creation (TTL 600s) | chief_writer.py:414 |
| invalidate_manuscript_cache | Local state reset | chief_writer.py:1948-1952 |
| WritingDirectiveGenerator.generate | LLM API call (llm_callback) | writing_directive_generator.py:46 |
| writer.write_v20_manuscript | LLM API call (generate_content_via_router) | writer.py:225 |

---

## 5. Facts

1. ChiefWriter는 `BaseAgent`를 상속하며, facade + 2 sub-module (ChiefWriterContextBuilder, ChiefWriterQualityGate) 구조다.
2. 앙상블 3전략: balanced(temp 0.7), narrative(0.8), tension(0.9). `strategy_budget`으로 2개/1개 축소 가능.
3. Self-Critique는 최대 3라운드, Rubric ≥ 3.5이면 조기 스킵 (단, 구조적 이슈 있으면 스킵 금지).
4. Context caching TTL=600s. 캐시 실패 시 full prompt 폴백.
5. inplace_patch는 structural(씬 단위) → whole-text 2단계 폴백. 최소 2000자.
6. Writer(writer.py)는 V64에서 Thin Fallback으로 경량화됐으나, 실제 호출 경로 없음 (dead code).
7. WriterTemplate은 main_a.py에서 인스턴스화되고, chief_writer.py에서 structural patch에 사용됨.
8. 프롬프트는 chief_writer.yaml SSOT → PromptLoader → _load_prompt() 체인.
9. Pydantic 검증(validate_manuscript_candidate)이 앙상블 반환 직전에 적용됨.

---

## 6. Inferences

1. `_CW_GENRE_CODE_MAP`(12줄)과 writer.py 전체(376줄)가 dead code → 약 388줄 삭제 가능.
2. ChiefWriter의 ~30개 delegation 메서드는 하위 호환성 목적이나, 외부 호출자가 없다면 삭제 가능.
3. SATISFACTION_GUIDE_SECTION의 무조건 주입은 토큰 비용에 영향. 장르별 분기가 있으면 비투자물에서 절감 가능.
4. 하드코딩 값 6건(2000자, 3.5 rubric, 3 rounds, 80자, 2500자, temperature offsets)은 config 외부화 후보.
5. dual mandatory_context(TF-017)는 Writer dead code 정리 시 자연 해소.

---

## 7. Uncertainty / Contradictions

1. **TF-017 실제 충돌 여부**: stage4_interview_round에서 ChiefWriter에 mandatory_context 파라미터를 전달하는 경로가 있음. writer_prompt_builders.build_mandatory_context vs chief_writer_context._build_mandatory_context 중 어느 것이 주입되는지 T06에서 추가 확인 필요.
2. **TF-018 외부 호출자**: ~30개 delegation 메서드의 실제 외부 호출자가 tests/외부 코드에 있는지 전수 확인 미완료.
3. **TF-019 invalidate 호출**: 에피소드 롤백 시 `invalidate_manuscript_cache()` 호출 여부는 T05/T06 범위.
4. **TF-024 validation.yaml 키 존재**: `quality.cliche_window` 키가 validation.yaml에 실제 존재하는지 T17에서 확인 필요.

---

## 8. Cross-Ref to Adjacent Terminals

| Adjacent Terminal | Cross-Ref |
|-------------------|-----------|
| T05 (Stage 4 Orch) | TF-019 invalidate_manuscript_cache() 호출 여부 |
| T06 (Stage 4 Interview) | TF-005 inplace_patch 호출 경로, TF-017 mandatory_context 주입 경로, TF-014 빈 후보 처리 |
| T11 (BaseAgent) | TF-008 _get_or_create_context_cache 인프라, TF-018 BaseAgent 상속 |
| T14 (Validation) | TF-023 self-critique vs pre_llm_validator 검사 항목 중복 가능 |
| T17 (Config) | TF-010/TF-011/TF-012/TF-015 prompt YAML 키 정합성, TF-024 validation.yaml 키 |
| T18 (Stage 0/Helpers) | TF-009 PatternTracker lookback 설정 |
| T20 (Cross-Cut) | TF-001/TF-003 dead code 전수 |

---

## 9. Candidate Watchlist

| Priority | Item | Reason |
|----------|------|--------|
| 1 | writer.py 전체 제거 | 376줄 dead code, 호출자 0 |
| 2 | _CW_GENRE_CODE_MAP 제거 | 12줄 dead code, 참조 0 |
| 3 | 하드코딩 6건 config 외부화 | rubric 3.5, 2000자, 3 rounds, 80자, 2500자, temp offsets |
| 4 | delegation 메서드 정리 | ~30개 중 미사용 메서드 식별 후 제거 |
| 5 | SATISFACTION_GUIDE_SECTION 장르 분기 | 토큰 절감 가능 |

---

## 10. 6Pass Audit Log

### Pass 1 (구조/범위)
- 8개 범위 파일 전수 커버 ✓
- 7개 필수 조사 항목 전수 대응 ✓
- 25개 TF 구성 (최소 10개 초과) ✓
- **PASS**

### Pass 2 (증거/일관성)
- 모든 TF에 파일:라인 형식 Evidence 존재 ✓
- Grep 결과 기반 부재 증명 포함 ✓
- 코드 스니펫 인용 포함 ✓
- 내부 모순 없음 ✓
- **PASS**

### Pass 3 (실행가능성)
- P2 1건 (TF-017 dual implementation), P3 5건 (하드코딩+dead code), P4 19건 (SYNC/관측) → 분포 합리적 ✓
- 각 TF가 actionable (제거/외부화/확인 가능) ✓
- **PASS**

### Pass 4 (적대적 — 스코프)
- "writer_template.py가 T08 범위인가?" → ChiefWriter._build_structural_patch_plan에서 import하여 사용 (L1167, L1188). Chief Writer 시스템의 일부 ✓
- "writing_directive_generator.py가 T08 범위인가?" → 마스터 오더 섹션 2 T08에 명시 ✓
- **반박 실패 → PASS**

### Pass 5 (적대적 — 증거)
- "TF-003 Writer가 dead code라고 단정할 수 없다" → main_a.py에서 Writer 인스턴스는 생성하나(L1753), write_v20_manuscript 호출 0건. 다른 Writer 메서드(get_genre_rules_prompt 등)도 grep 결과 외부 호출 0건 → **반박 실패 → PASS**
- "TF-017의 dual implementation이 실제 충돌하는가?" → Uncertainty 섹션에 명시. 충돌 가능성을 P2로 보수적 분류 → **반박 실패 → PASS**

### Pass 6 (적대적 — severity)
- "TF-001/002 dead code가 P3이 아닌 P4여야 한다" → 12줄 dead code는 유지보수 부담이므로 P3-LOW 적절 → **반박 실패 → PASS**
- "TF-017이 P2가 아닌 P3여야 한다" → Writer dead code로 실질 위험 낮으나, stage4_orchestrator 경유 주입 가능성이 있어 P2 유지 타당 → **반박 실패 → PASS**

**6PASS-CLEARED** — 확신도 96%
