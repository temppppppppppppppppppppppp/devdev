# Codex 오더: 300-Round Structured Sweep

> 코드베이스 전체 구조화 스윕. Dead Code + Error Handling + Config Drift + Logging + Hygiene.
> Section A → B → C → D → E → F → G 순차 실행. 각 섹션 후 테스트.
> **코드를 수정합니다.**

---

## 규칙

1. **총 300라운드** (R001-R300)
2. **R001-R200**: 무조건 실행
3. **R201-R300**: 섹션 내 3연속 "발견 없음 / 이상 없음 / 이미 처리됨" 시 해당 섹션 종료 → 다음 섹션으로 이동
4. **각 섹션 완료 후** ruff + pytest 실행
5. **기존 테스트 불변**: passed + xfailed 기준선 유지
6. **삭제 전 grep 재확인**: 파일/import/초기화 삭제 시 참조 0 재확인 필수
7. **Director 주권 유지**: Director 관련 코드는 로깅 추가만, 로직 변경 금지
8. **비차단 원칙**: 에러 핸들링 수정 시 파이프라인 중단 유발 금지

---

## 대원칙

- **Dead Code 삭제**: grep으로 참조 0 확인 후 삭제. 1건이라도 참조 있으면 유지.
- **Silent Failure 수정**: `except Exception: pass` → `logging.warning(f"[SilentPass:모듈명] {e!s:.100}")` 패턴.
- **하드코딩 전환**: `_threshold("section.key", default)` 패턴 사용. `from modules.validation.threshold_helper import _threshold`.
- **Orphaned Init 삭제**: `self.xxx = None` 선언 + 초기화 블록 + import 문 3종 삭제.
- **YAML 키 삭제**: Python 소비자 0인 키만 삭제. 주석으로 삭제 이유 남기지 않음 (깔끔 삭제).

---

## Section A: Dead Code 정리 (R001-R060)

### A-1: Dead Python 모듈 삭제 (R001-R019)

각 라운드 = 1파일 삭제. **삭제 전 `grep -r "파일명" modules/ main_a.py tests/`로 참조 0 재확인.**
참조가 1건이라도 있으면 삭제하지 말고 해당 import만 정리하거나 SKIP.

| Round | 파일 | 비고 |
|-------|------|------|
| R001 | `modules/core/ab_testing.py` | |
| R002 | `modules/core/arc_summary_utils.py` | |
| R003 | `modules/core/constraint_db.py` | |
| R004 | `modules/core/context_compression.py` | Phase 5에서 import 삭제됨 |
| R005 | `modules/core/data_collector.py` | |
| R006 | `modules/core/error_helper.py` | |
| R007 | `modules/core/escape_utils.py` | |
| R008 | `modules/core/finetuning_automation.py` | |
| R009 | `modules/core/genre_hud_manager.py` | |
| R010 | `modules/core/information_diffusion.py` | |
| R011 | `modules/core/jianghu_logic.py` | |
| R012 | `modules/core/justification_patterns.py` | |
| R013 | `modules/core/karma_service.py` | |
| R014 | `modules/core/lore_manager.py` | |
| R015 | `modules/core/material_db.py` | |
| R016 | `modules/core/pattern_tracker.py` | |
| R017 | `modules/core/reflexion_manager.py` | |
| R018 | `modules/domain/agents/manuscript_validator.py` | |
| R019 | `modules/core/hud_utils.py` | director.py에서 import 사용 — import 제거 후 삭제. 실제 호출 여부 확인 필수. |

### A-2: Dead Prompt YAML 삭제 (R020)

| Round | 파일 | 비고 |
|-------|------|------|
| R020 | `config/prompts/bible_extractor.yaml` | PromptLoader 참조 0 확인 후 삭제 |

### A-3: Orphaned main_a.py 초기화 정리 (R021-R035)

각 라운드 = 1개 모듈의 **`self.xxx = None` 선언 + 초기화 블록 + import 문** 3종 삭제/유지 판단.

**판단 기준**:
- Stage2/3/4 Context의 `__slots__`나 `from_app()`에서 참조되는가? → 유지
- 다른 파일에서 `app.xxx` 또는 `self.xxx`로 호출되는가? → 유지
- 위 둘 다 아니면 → 삭제

**삭제 시 3종 세트**:
1. `__init__` 상단 None 선언 (예: `self.quality_amplifier = None`)
2. 초기화 블록 (예: `self.quality_amplifier = QualityAmplifier(...)` + 직후 `ui.log()`)
3. import 문 (예: `from modules.core.quality_amplifier import QualityAmplifier`)

| Round | 속성 | grep 확인 패턴 | 예상 액션 |
|-------|------|---------------|----------|
| R021 | `self.tree_of_thoughts` | `tree_of_thoughts` | **유지** — CLAUDE.md에 "추후 연결" 명시됨 |
| R022 | `self.multi_agent_deliberation` | `multi_agent_deliberation` | **유지** — CLAUDE.md에 "추후 연결" 명시됨 |
| R023 | `self.constitutional_checker` | `constitutional_checker` | grep 후 판단 |
| R024 | `self.quality_amplifier` | `quality_amplifier` | grep 후 판단 — 0참조면 삭제 |
| R025 | `self.agent_intelligence` | `agent_intelligence` | grep 후 판단 |
| R026 | `self.character_voice` | `character_voice` | grep 후 판단 |
| R027 | `self.emotion_tracker` | `emotion_tracker` | grep 후 판단 — DB 로드 코드도 함께 삭제 |
| R028 | `self.power_scaling` | `power_scaling` | grep 후 판단 |
| R029 | `self.state_delta_tracker` | `state_delta_tracker` | grep 후 판단 |
| R030 | `self.semantic_item_registry` | `semantic_item_registry` | grep 후 판단 |
| R031 | `self.voice_profiler` | `voice_profiler` | grep 후 판단 |
| R032 | `self.self_reflector` | `self_reflector` | grep 후 판단 |
| R033 | `self.expert_mixture` | `expert_mixture` | grep 후 판단 |
| R034 | `self.writer_template` | `writer_template` | grep 후 판단 |
| R035 | `self.pass_rate_monitor` + `self.quality_dashboard` | 각각 grep | grep 후 판단 |

### A-4: Dead YAML Config 키 정리 (R036-R055)

**파일**: `config/settings/validation.yaml`

Python 코드에서 `_threshold()` 또는 `ConfigManager`로 소비하지 않는 YAML 키 섹션 정리.
각 라운드에서 해당 키를 grep (`_threshold("키이름"` 패턴)으로 재확인.

**소비 확인됨 (건드리지 않음)**:
- `advisory.*`, `context.*`, `continuity.*`, `cross_episode_repetition.*`
- `feature_flags.*`, `manuscript.*`, `npc_exposure.*`, `patch_mode.*`
- `pre_llm.repetition_score_threshold`, `premium.repetition.*`
- `quality_regression.*`, `satisfaction.*`, `scene.min_scene_length`
- `scoring.quality_gate_score`, `thresholds.hud_change`

**미소비 (정리 대상)**:

| Round | YAML 섹션 | 키 수 | 액션 |
|-------|-----------|-------|------|
| R036-R038 | `retry.*` (`director_max_attempts`, `analyst_max_attempts`, `architect_max_attempts`, `writer_max_attempts`, `blueprint_max_attempts`, `cache_ttl_seconds`, `api_timeout_seconds`) | 7 | 대응 하드코딩 있으면 연결, 없으면 삭제 |
| R039-R040 | `writing.*` (`max_retry_per_episode`, `min_episode_loop_guard`, `max_failure_streak`) | 3 | 대응 하드코딩 있으면 연결, 없으면 삭제 |
| R041-R043 | `volume.*` (`arcs_per_volume`, `episodes_per_arc`, `min_episodes_per_arc`, `max_episodes_per_arc`) | 4 | 대응 하드코딩 있으면 연결, 없으면 삭제 |
| R044-R047 | `thresholds.*` (`hud_change` 제외: `tactical_duplicate`, `pattern_min_hits`, `min_tactical_doc_length`, `max_tactical_doc_length`, `min_blueprint_length`, `max_blueprint_length`, `min_cache_content_length`) | 7 | 대응 하드코딩 있으면 연결, 없으면 삭제 |
| R048-R049 | `scoring.default_pass_threshold` + `scoring.genre_thresholds.*` | 5 | 대응 하드코딩 있으면 연결, 없으면 삭제 |
| R050-R051 | `scoring.breakdown.*` (6개 카테고리) | 6 | 삭제 or 연결 |
| R052-R053 | `premium.emotion.*` + `premium.anchor.*` | 12 | 삭제 or 연결 |
| R054 | `scene.target_count` + `scene.min_count` | 2 | 삭제 or 연결 |
| R055 | `scope.chars_per_scene` + `scope.overflow_ratio` | 2 | 삭제 or 연결 |

### A-5: Dead Import 정리 (R056-R060)

| Round | 파일 | 이슈 |
|-------|------|------|
| R056 | `main_a.py` L143 | `from google.genai import types` 중복 (L2796에서 로컬 재import) — L143 삭제 |
| R057-R060 | R001-R019에서 삭제한 모듈을 참조하는 잔여 import | grep `from modules.core.삭제된모듈` 전체 스윕 |

### Section A 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Section B: Error Handling & Safety (R061-R120)

### B-1: CRITICAL/HIGH Silent Failures (R061-R070)

| Round | 파일:줄 | 이슈 | 수정 방법 |
|-------|---------|------|----------|
| R061 | `modules/core/stage4_post_processor.py:52` | Rollback 실패 `except Exception: pass` | `logging.error(f"[CRITICAL:PostProcessor] DB rollback 실패: {e!s:.200}")` |
| R062 | `modules/domain/agents/continuity_tracker.py:154` | `arcs_data = []` 전체 데이터 소실 | `logging.error(f"[CRITICAL:ContinuityTracker] arc 데이터 조회 실패: {e!s:.200}")` + 부분 데이터 반환 검토 |
| R063 | `modules/domain/agents/analyst.py:945` | `issue['severity']` unguarded KeyError | `issue.get('severity', '').upper()` + `issue.get('description', '')` |
| R064 | `modules/core/adaptive_retry.py` | `_failures` 리스트 무한 성장 | 에피소드별 최대 50건 pruning: `self._failures = self._failures[-50:]` |
| R065 | `modules/domain/agents/base_agent.py:1079` | `_context_caches` dict 병렬 접근 무잠금 | `threading.Lock` 추가, cache read/write 감싸기 |
| R066 | `modules/domain/agents/base_agent.py` | `_quota_exhausted_models` dict 무잠금 | `threading.Lock` 추가 |
| R067 | `modules/core/db_manager.py` | `_cumulative_bible_cache` 무한 성장 | maxsize=200, 초과 시 oldest 제거 |
| R068 | `modules/core/stage2_preflight.py:105-106` | `.result(timeout=300)` 2개 future 개별 에러 처리 없음 | 각 `.result()`를 개별 try/except로 감싸기 |
| R069 | `modules/domain/agents/continuity_tracker.py:63` | `info_diffusion=None` silent | `logging.warning("[SilentPass:ContinuityTracker] info_diffusion 초기화 실패")` |
| R070 | `modules/core/stage0/style_extractor.py:656` | Client init 실패 silent pass | `logging.warning(f"[SilentPass:StyleExtractor] {e!s:.100}")` |

### B-2: MEDIUM Silent Failures (R071-R088)

각 라운드: `except Exception: pass` 또는 `except Exception: fallback` 패턴에 `logging.warning(f"[SilentPass:모듈명] {e!s:.100}")` 추가.

| Round | 파일:줄 | 이슈 |
|-------|---------|------|
| R071 | `modules/validation/retrospective_validator.py:269` | DB past_realms 읽기 실패 — exc_info=True 이미 있으나 레벨 검토 |
| R072 | `modules/validation/retrospective_validator.py:292` | DB past_items 읽기 실패 |
| R073 | `modules/validation/retrospective_validator.py:344` | DB resolved_conflicts 읽기 실패 |
| R074 | `modules/validation/continuity_validator.py:955` | satisfaction tags → `return []` |
| R075 | `modules/core/stage3_orchestrator.py:309` | protagonist config extraction silent |
| R076 | `modules/domain/agents/four_phase_arc_generator.py:157` | protagonist extraction #1 |
| R077 | `modules/domain/agents/four_phase_arc_generator.py:482` | protagonist extraction #2 |
| R078 | `modules/domain/agents/four_phase_arc_generator.py:577` | internal energy parse fallback |
| R079 | `modules/core/arc_summary_utils.py:64` | energy extraction fallback |
| R080 | `modules/domain/agents/manuscript_validator.py:67` | incarnation type silent |
| R081 | `modules/core/stage0/reverse_expander.py:93` | JSON parse → None |
| R082 | `modules/core/project_manager.py:655` | file-DB ep sync 실패 |
| R083 | `modules/domain/agents/director_auditor.py:400` | state extraction silent |
| R084 | `modules/domain/agents/writer.py:147` | ReferenceAnchor prompt silent |
| R085 | `modules/domain/agents/writer.py:301` | genre rules → "" |
| R086 | `modules/core/writer_prompt_builders.py:166` | anomaly detection → `{has_anomalies: False}` |
| R087 | `modules/core/hud_utils.py:264` | HUD trend → "안정적" |
| R088 | `modules/core/information_diffusion.py:133` | faction → "" |

**주의**: R079, R080, R087, R088은 Section A에서 삭제된 파일일 수 있음. 삭제됐으면 SKIP.

### B-3: Future Cancellation 패턴 통일 (R089-R094)

현재: `f.cancel()` 결과 미확인.
수정 패턴:
```python
for f in futures:
    if not f.done():
        cancelled = f.cancel()
        if not cancelled:
            logging.debug("[SilentPass:FutureCancel] 이미 실행 중인 future 취소 실패")
```

| Round | 파일 | 줄 |
|-------|------|-----|
| R089 | `modules/domain/agents/arc_ensemble.py` | L184 |
| R090 | `modules/domain/agents/chief_writer.py` | L308 |
| R091 | `modules/domain/agents/blueprint_ensemble.py` | L224 |
| R092 | `modules/domain/agents/consensus_validator.py` | L264 |
| R093 | `modules/domain/agents/director_auditor.py` | L895 |
| R094 | `modules/domain/agents/block_enricher.py` | L672 |

### B-4: PerfTimer except pass 통일 (R095-R100)

현재: `except Exception: pass`.
수정: `except Exception as e: logging.debug(f"[SilentPass:PerfTimer] {e!s:.50}")`.
**레벨 debug** — PerfTimer 실패는 비차단, 노이즈 방지.

| Round | 파일 | 위치 |
|-------|------|------|
| R095 | `modules/core/stage4_interview_round.py` | 4곳 전량 |
| R096 | `modules/domain/agents/arc_ensemble.py` | L196 |
| R097 | `modules/domain/agents/chief_writer.py` | L320 |
| R098 | `modules/domain/agents/blueprint_ensemble.py` | L236 |
| R099 | `modules/domain/agents/consensus_validator.py` | L276 |
| R100 | `modules/domain/agents/director_auditor.py` | L900 |

### B-5: Unbounded Collections (R101-R106)

| Round | 파일 | 이슈 | 수정 |
|-------|------|------|------|
| R101 | `modules/core/adaptive_retry.py` | `_failures` per-ep 통계 무한 성장 | per-ep 최대 50건: `self._failures = self._failures[-50:]` |
| R102 | `modules/core/vec_memory.py` | `surgery_logs` 테이블 무한 성장 | 주기적 pruning: `DELETE FROM surgery_logs WHERE rowid NOT IN (SELECT rowid FROM surgery_logs ORDER BY rowid DESC LIMIT 1000)` |
| R103 | `modules/core/db_manager.py` | `_cumulative_bible_cache` 무한 성장 | maxsize=200 적용 확인 |
| R104-R106 | 예비 | 스윕 중 추가 발견 시 사용 |

### B-6: Unsafe Dict/Type Access (R107-R112)

| Round | 파일 | 이슈 |
|-------|------|------|
| R107 | `modules/domain/agents/analyst.py:945` | bracket access `.get()` 패턴 스윕 |
| R108 | `modules/validation/blocking_validator_entity_checks.py` | bracket access 패턴 스윕 |
| R109 | `modules/validation/blocking_validator_consistency_checks.py` | 동일 |
| R110 | `modules/validation/consistency_validator.py` | 동일 |
| R111 | `modules/validation/continuity_validator.py` | 동일 |
| R112 | `modules/validation/retrospective_validator.py` | 동일 |

### B-7: 예비 (R113-R120)

섹션 B 스윕 중 추가 발견 항목용. 발견 없으면 SKIP.

### Section B 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Section C: Hardcoded Thresholds → _threshold() (R121-R170)

**공통 패턴**:
```python
from modules.validation.threshold_helper import _threshold

# Before:
threshold = 500
# After:
threshold = _threshold("blocking.minimum_length", 500)
```

validation.yaml에 대응 키가 없으면 바로 추가.

### C-1: blocking_validator_scene_checks.py (R121-R128)

| Round | 줄(확인) | 현재 | 전환 |
|-------|---------|------|------|
| R121 | L473 부근 | `threshold = 500` | `_threshold("blocking.minimum_length", 500)` |
| R122 | L493 부근 | `min_required = 4` | `_threshold("blocking.min_required_scenes", 4)` |
| R123 | L558 부근 | `>= 80` (cliffhanger A) | `_threshold("blocking.cliffhanger_grade_a", 80)` |
| R124 | L558 부근 | `>= 60` (B) | `_threshold("blocking.cliffhanger_grade_b", 60)` |
| R125 | L558 부근 | `>= 40` (C) / `>= 20` (D) | 동일 패턴 |
| R126-R128 | 전체 파일 | 추가 하드코딩 스윕 | 발견 시 전환 |

### C-2: pre_llm_validator.py (R129-R138)

| Round | 이슈 | 전환 키 |
|-------|------|--------|
| R129 | `+= 3` (dialogue_quality 감점) | `_threshold("pre_llm.penalty_dialogue", 3)` |
| R130 | `+= 2` (description_depth 감점) | `_threshold("pre_llm.penalty_description", 2)` |
| R131 | `+= 5` (action_clarity 감점) | `_threshold("pre_llm.penalty_action", 5)` |
| R132 | `+= 1` (pacing_rhythm 감점) | `_threshold("pre_llm.penalty_pacing", 1)` |
| R133 | `+= 4` (sensory_immersion 감점) | `_threshold("pre_llm.penalty_sensory", 4)` |
| R134 | `c > 15` (단어 빈도 임계) | `_threshold("pre_llm.word_frequency_threshold", 15)` |
| R135 | `> 0.3` (감탄부호 비율) | `_threshold("pre_llm.exclamation_ratio", 0.3)` |
| R136 | `> 3` (감각 누락 임계) | `_threshold("pre_llm.sensory_missing_threshold", 3)` |
| R137-R138 | 전체 파일 추가 스윕 | 발견 시 전환 |

### C-3: consistency_validator.py (R139-R145)

`score_penalty` 하드코딩 → `_threshold()` 전환. 파일 내 모든 감점 상수 스윕.

### C-4: scoring_validator.py (R146-R152)

| Round | 이슈 | 전환 |
|-------|------|------|
| R146 | `max_score = 100` | `_threshold("scoring.max_score", 100)` |
| R147 | pattern 가중치 6 | `_threshold("scoring.weight_pattern", 6)` |
| R148 | satisfaction 가중치 5 | `_threshold("scoring.weight_satisfaction", 5)` |
| R149-R150 | 기타 가중치 | 동일 패턴 |
| R151-R152 | 전체 파일 추가 스윕 | 발견 시 전환 |

### C-5: retrospective_validator.py (R153-R158)

심각도 임계값 (>=10 CRITICAL, >=5 HIGH, >=2 MEDIUM) → `_threshold()` 전환.

### C-6: validation.yaml 신규 키 추가 (R159-R165)

C-1~C-5에서 추가한 `_threshold()` 호출에 대응하는 YAML 키를 `config/settings/validation.yaml`에 추가.

섹션별 그룹핑:
```yaml
blocking:
  minimum_length: 500
  min_required_scenes: 4
  cliffhanger_grade_a: 80
  cliffhanger_grade_b: 60
  cliffhanger_grade_c: 40
  cliffhanger_grade_d: 20

pre_llm:
  penalty_dialogue: 3
  penalty_description: 2
  penalty_action: 5
  penalty_pacing: 1
  penalty_sensory: 4
  word_frequency_threshold: 15
  exclamation_ratio: 0.3
  sensory_missing_threshold: 3
```

### C-7: 기타 파일 하드코딩 스윕 (R166-R170)

validation/ 디렉토리 외 파일에서 하드코딩된 임계값 추가 스윕.

### Section C 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Section D: Logging & Observability (R171-R210)

### D-1: Critical Decision Point 로깅 보강 (R171-R185)

| Round | 파일 | 이슈 | 추가할 로그 |
|-------|------|------|-----------|
| R171 | `modules/core/stage2_orchestrator.py:656` 부근 | Arc 최종 결정(PASS/REJECT) 통합 로그 없음 | `logging.warning(f"[Stage2] Arc {arc_no} 최종: {'PASS' if passed else 'REJECT'}")` |
| R172 | `modules/core/stage4_orchestrator.py:632` 부근 | 원고 최종 판정 불명확 | `logging.warning(f"[Stage4] EP {ep} 최종: {'PASS' if final_manuscript else 'FAIL'}")` |
| R173 | `modules/domain/agents/director.py:241` 부근 | facade에 후보 선택 로깅 없음 | `logging.info(f"[Director] 후보 선택: {selected}")` |
| R174 | `modules/core/stage4_interview_round.py:131` 부근 | 패치 모드 결과(성공/실패) 미로깅 | 패치 후 `logging.info(f"[PatchMode] 결과: {len(candidates)}건 생성")` |
| R175 | `modules/domain/agents/chief_writer.py` 여러 곳 | except 후 폴백 트리거 미로깅 | 각 except에 `logging.info(f"[ChiefWriter] 폴백: {폴백경로}")` |
| R176 | `modules/core/stage2_preflight.py:290` 부근 | 빈 manuscripts 반환 시 미경고 | `if not _recent_ms: logging.warning("[Preflight] 최근 원고 없음")` |
| R177 | `modules/domain/agents/state_extractor.py` | 추출 실패 미로깅 | 주요 추출 메서드에 실패 logging 추가 |
| R178-R185 | 전체 modules/ 스윕 | 추가 결정 지점 발견 시 보강 |

### D-2: 로그 레벨 교정 (R186-R195)

에러 상황인데 `logging.info()`로 기록된 곳 → `logging.warning()` 교정.

| Round | 파일 | 현재 | 수정 |
|-------|------|------|------|
| R186 | `modules/core/adaptive_retry.py:208` | `logging.info("최대 재시도 도달")` | `logging.warning()` |
| R187 | `modules/validation/validation_orchestrator.py` | Tier 전환 info | 검토 후 유지 or warning |
| R188-R195 | 전체 modules/ | `logging.info` 중 에러 맥락인 것 스윕 | 교정 |

### D-3: Truncation 로깅 (R196-R205)

데이터 절삭(`[:N]`) 시 원본 길이가 N을 초과하면 debug 로그 추가.

```python
# 패턴
if len(text) > LIMIT:
    logging.debug(f"[모듈명] 절삭: {len(text)} → {LIMIT} chars")
text = text[:LIMIT]
```

| Round | 파일 | 이슈 |
|-------|------|------|
| R196 | `modules/domain/agents/state_extractor.py:830` | `manuscript[:3000]` — 상태 변경 손실 위험 |
| R197 | `modules/core/semantic_plot_guard.py:284` | `tactical_doc[:3000]` |
| R198 | `modules/core/stage0/reverse_expander.py:167,172` | 사용자 초안 절삭 |
| R199 | `modules/core/stage0/reverse_expander.py:206,275,288` | 추가 절삭 지점 |
| R200 | `modules/core/project_manager.py:838` | `summary = content[:1000]` |
| R201-R205 | 기타 파일 | `[:N]` 패턴 중 데이터 손실 위험 스윕 |

### D-4: 예비 (R206-R210)

### Section D 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Section E: Code Hygiene (R211-R260)

### E-1: Duplicated Logic 통합 (R211-R225)

| Round | 이슈 | 파일 |
|-------|------|------|
| R211-R215 | `_extract_keywords()` 중복 구현 | `blocking_validator_entity_checks.py` vs `blocking_validator_consistency_checks.py` — 공유 유틸 추출 검토 |
| R216-R220 | 상태 비교 로직 중복 | `consistency_validator.py` vs `continuity_validator.py` — 공유 가능 부분 식별 |
| R221-R225 | 점수 계산 패턴 중복 | `scoring_validator.py` vs `consensus_validator.py` — 가중치 체계 통일 검토 |

**주의**: 중복 통합은 리스크가 높음. 실제로 동일 로직인지 차이점 확인 후 판단. 차이 있으면 SKIP.

### E-2: 에러 메시지 형식 통일 (R226-R240)

**목표 표준**:
- 예외 핸들러: `[SilentPass:모듈명]`
- 정상 로직: `[모듈명]`
- 버전 태그 (`[V60.46]` 등): 기존 유지 (삭제하지 않음)

| Round | 범위 |
|-------|------|
| R226-R228 | `modules/core/stage2_*.py` 전체 |
| R229-R231 | `modules/core/stage4_*.py` 전체 |
| R232-R234 | `modules/validation/*.py` 전체 |
| R235-R237 | `modules/domain/agents/*.py` 전체 |
| R238-R240 | 예비 |

### E-3: Deprecated 파라미터 정리 (R241-R245)

| Round | 파일 | 이슈 |
|-------|------|------|
| R241 | `modules/core/stage2_optimizer.py:688` | `category` deprecated → `failure_type` 전환 경고 추가 or 제거 |
| R242-R245 | 전체 modules/ | `deprecated` 주석이 있는 파라미터 스윕 |

### E-4: LOW Silent Failures 선별 수정 (R246-R260)

36+ LOW 항목 중 **데이터 손실 가능성 > 0**인 것만 선별하여 `logging.warning` 추가.
순수 optional (PerfTimer, UI 장식 등)이면 SKIP.

| Round | 범위 |
|-------|------|
| R246-R250 | `modules/core/*.py` LOW 항목 |
| R251-R255 | `modules/domain/agents/*.py` LOW 항목 |
| R256-R260 | `modules/validation/*.py` LOW 항목 |

### Section E 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Section F: Dead Config 정리 & 연결 (R261-R285)

Section A-4에서 "삭제 or 연결" 판단한 YAML 키들의 실제 코드 작업.

### F-1: 삭제 확정 키 제거 (R261-R270)

A-4에서 "대응 하드코딩 없음" 판정된 YAML 키 삭제.
validation.yaml에서 해당 섹션 제거.

### F-2: 코드 연결 확정 키 (R271-R285)

A-4에서 "대응 하드코딩 있음" 판정된 키를 `_threshold()`로 실제 코드에 연결.

예시:
```python
# retry.director_max_attempts → stage2_finalizer.py의 max_attempts = 5
max_attempts = _threshold("retry.director_max_attempts", 5)
```

각 라운드 = 1개 YAML 키 연결. 대응 Python 코드의 하드코딩을 `_threshold()` 호출로 교체.

### Section F 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## Section G: Misc & Edge Cases (R286-R300)

### G-1: 파이프라인 수정 검증 (R286-R292)

Codex 파이프라인 효율성 수정(Phase 1~5) 결과물 교차 검증.

| Round | 검증 대상 |
|-------|----------|
| R286 | `Stage4Context.__slots__`에 5개 모듈 슬롯 존재 확인 + `from_app()` 주입 확인 |
| R287 | ASP(`adversarial_self_play`) 슬롯 + 주입 + `stage4_interview_round.py` 호출 코드 확인 |
| R288 | Quality Gate: `_threshold("scoring.quality_gate_score", 90)` 호출 확인 (stage4/stage2/stage3) |
| R289 | `ManuscriptLimits`, `PatchModeThresholds` → `_threshold()` 전환 확인 |
| R290 | `SemanticCache`, `ContextCompressor`, `ManuscriptEnhancer` 삭제 확인 (import + init + None) |
| R291 | 신규 코드의 `[SilentPass:*]` 로깅 패턴 준수 확인 |
| R292 | 신규 코드의 `except Exception as e:` 패턴 — bare except 0건 확인 |

### G-2: 크로스커팅 (R293-R300)

| Round | 이슈 |
|-------|------|
| R293 | `main_a.py` L143 duplicate `from google.genai import types` 삭제 확인 |
| R294 | `base_agent.py` `enable_cascade` 파라미터 잔여 확인 |
| R295 | `stage2_optimizer.py` deprecated `category` 파라미터 최종 확인 |
| R296-R300 | 스윕 중 축적된 잡항목 처리 |

### Section G 테스트

```bash
python -m ruff check modules/ main_a.py --no-fix
set PYTHONIOENCODING=utf-8 && python -m pytest tests/ -q --tb=short --capture=no
```

---

## 조기 종료 규칙

- **R001-R200**: 무조건 실행
- **R201-R300**: 섹션 내 3연속 "발견 없음 / 이상 없음 / 이미 처리됨" 시 해당 섹션 종료 → 다음 섹션으로 이동
- **전 섹션 조기 종료 시**: 전체 스윕 완료

---

## 주의사항

- Section 순서 엄수 (A → B → C → D → E → F → G)
- 각 섹션 완료 후 ruff + pytest 실행
- Dead file 삭제 시 반드시 grep 재확인 (탐색 시점과 실행 시점 사이에 변경 가능)
- `[SilentPass:모듈명]` 형식으로 모든 예외 로깅 (기존 패턴 준수)
- Section A에서 삭제한 파일을 Section B에서 수정하려 하면 SKIP
- validation.yaml 수정 시 기존 키 순서/그룹핑 유지
- 테스트 파일(`tests/`)에서 삭제된 모듈을 참조하는 import도 함께 정리
- Director 주권 절대 불가침: Director 관련 코드는 로깅 추가만, 로직 변경 금지
