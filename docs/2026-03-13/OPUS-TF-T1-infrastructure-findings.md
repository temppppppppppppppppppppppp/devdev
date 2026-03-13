# OPUS TF — Terminal 1: 기반 인프라 & 데이터 레이어 전량 조사 보고서

> **조사일**: 2026-03-13
> **범위**: main_a.py, DB(db_manager/vec_memory/constraint_db), LLM 추상화(llm_*/providers/*),
>   프롬프트(prompt_builder/loader), DI Context(stage2/3/4_context), Protocol 정의,
>   서비스 레이어, 로깅/유틸, Config/Contract 파일 전량
> **방법론**: 6-Point Inspection (Null안전/분기정합/데이터흐름/에러처리/계약준수/테스트커버리지)
> **5Pass 감리**: 완료 — 오탐 3건 제거, 부분오탐 4건 등급 하향, 라인 번호 전량 교정

---

## 요약

| Severity | 건수 | 5Pass 전 | 변동 |
|----------|------|----------|------|
| **P0-CRITICAL** | 0 | 0 | — |
| **P1-IMPORTANT** | 1 | 1 | — |
| **P2-MODERATE** | 8 | 12 | -4 (오탐 1건 제거, 부분오탐 3건→P3 하향) |
| **P3-MINOR** | 22 | 20 | +2 (P2에서 하향 4건, 오탐 2건 제거) |
| **오탐 제거** | -3 | — | T1-12, T1-32a(_ok), T1-08(is_empty 의도적 설계) |
| **확정 합계** | **31** | 33 | |

---

## 5Pass 감리 기록

### PASS 1 — 코드 실물 대조 (P1+P2 HUD 계열)
- [x] T1-01: `RESET.py` L86 `bible_data["MasterBible"]["MartialHUD"]` 하드코딩 **확정**, 라인 정확
- [x] T1-02: `project_manager.py` L504 `"NPC_Martial_HUD" in new_npc` + L538 `setdefault("NPC_Martial_HUD")` **확정**, 라인 정확
- [x] T1-03: `project_manager.py` L227 `bible_root.get("MartialHUD", {})` **확정**, 라인 정확

### PASS 2 — 코드 실물 대조 (P2 batch 1: T1-04~08)
- [x] T1-04: api-contract-v1.yaml enum에 INTERNAL_ERROR/INVALID_PROJECT/INVALID_REQUEST 부재 **확정**
- [x] T1-05: run_validator L85 — process_runner.start()가 `_state != "idle"` 2차 방어 존재 → **부분오탐, P2→P3 하향**
- [x] T1-06: db_manager.py L1039-1047 execute_update() commit 없음. reflexion_manager가 수동 commit으로 우회 중 **확정**
- [x] T1-07: db_manager.py 공유 cursor `self.cursor.execute` ~185회 사용, L1533 포함 **확정**
- [x] T1-08: WritingDirective.is_empty() — `test_pipeline_wiring.py` L176에서 emotion_required only=empty를 **의도적 검증**. chief_writer_quality.py L759에서 `emotion_required` 별도 체크 → **부분오탐(의도적 설계), P2→P3 하향**

### PASS 3 — 코드 실물 대조 (P2 batch 2: T1-09~12)
- [x] T1-09: project_service.py cursor.execute **15곳** (발견보고 "16곳"→15곳 교정) **확정**
- [x] T1-10: state_service.py L325 falsy-check — 6개 required_keys 중 0이 유효값인 키 없음 (arc_no≥1, ep_start≥1) → **부분오탐, P2→P3 하향**
- [x] T1-11: llm_generate.py L21 — Gemini provider가 항상 raw 채움, 멀티 Provider 전환 시에만 잠재적 → **부분오탐, P2→P3 하향**
- [x] T1-12: prompt_builder.py L912-958 — `except Exception` 블록이 전체 감싸고 있어 app=None 시에도 크래시 안 함, 빈 context 안전 반환 → **오탐 제거**

### PASS 4 — 코드 실물 대조 (P3 주요 건)
- [x] T1-14: db_manager.py L2283 `commit: bool = True` 파라미터 미참조, L2330 무조건 commit **확정**
- [x] T1-15: constraint_db.py `if before_arc and ...` 패턴 3곳 — 현재 호출 경로에서 before_arc=0 불가, API 계약상 잠재 버그 **확정**
- [x] T1-23: stage3_context.py 독스트링 "속성 7종"→실제 9종, "콜백 10종"→실제 11종 **확정**
- [x] T1-24: stage2_context.py 독스트링 "확장 18종"→실제 20종, "콜백 21종"→실제 23종 **확정**
- [x] T1-25: app_services.py L62 Protocol에 tag 파라미터 누락 **확정**
- [x] T1-29: Stage4Context 테스트 존재(`test_stage4_context.py`), **Stage3Context만 전용 테스트 부재** → 부분오탐, 범위 축소

### PASS 5 — P3 일괄 항목 교차 검증
- [x] T1-32a: bridge_server `_ok()` data: None — 정상 사용, `_accepted`와 동일 계약 → **오탐 제거**
- [x] T1-32b: error_helper.py L268 severity_emoji 값 전부 빈 문자열 — **확정 (dead code)**
- [x] T1-32c: spinners.py L196 미할당 표현식 — **확정**

---

## P1 — IMPORTANT (1건)

### [T1-01] RESET.py: HUD 롤백이 MartialHUD에 하드코딩 — 비무협 장르 데이터 손상
- **Severity**: P1
- **파일**: `RESET.py` L86
- **5Pass**: 확정 ✅ (라인 정확)
- **현상**: `perform_selective_rewind()`에서 Bible의 HUD 롤백 시 `bible_data["MasterBible"]["MartialHUD"]["Protagonist"]["actual_truth"]`에 하드코딩. 장르 파라미터를 받지 않으며 장르 판별 로직이 전혀 없음. 비무협 장르에서 되감기 실행 시 존재하지 않는 `MartialHUD` 키 접근으로 `KeyError` 발생하거나, 빈 dict에 잘못된 데이터를 기록하여 HUD 롤백 실패.
- **근거**: `constants.py` `HUDKeys._GENRE_HUD_MAP`에 10개 장르별 HUD root가 정의되어 있고, `HUDKeys.get_hud_root(genre)` 헬퍼도 이미 존재함. RESET.py는 `projects/` 폴더의 모든 프로젝트에 범용으로 사용되는 도구.
- **수정안**: DB 또는 bible_data에서 장르를 판별한 뒤 `HUDKeys.get_hud_root(genre)` 결과를 사용하여 올바른 HUD 키에 접근.

---

## P2 — MODERATE (8건)

### [T1-02] project_manager.py: NPC HUD 키 하드코딩 (NPC_Martial_HUD)
- **Severity**: P2
- **파일**: `modules/core/project_manager.py` L504, L538
- **5Pass**: 확정 ✅ (라인 정확)
- **현상**: `commit_full_episode_data()` 내에서 NPC HUD 변화 추적 시 `"NPC_Martial_HUD" in new_npc`(L504)로만 검사하고, `target.setdefault("NPC_Martial_HUD", {})`(L538)로만 업데이트. 비무협 장르에서는 `NPC_Business_Profile`(투자), `NPC_Hunter_Status`(헌터) 등에 대한 변화 추적이 전부 무시됨 (silent data loss).
- **근거**: `constants.py` `NPCHUDKeys`에 10개 장르별 NPC HUD 키가 정의됨. `self.genre`(L77)에 접근 가능.
- **수정안**: `NPCHUDKeys.get_key(self.genre)`로 올바른 NPC HUD 키를 동적 결정.

### [T1-03] project_manager.py: Bible 저장 시 HUD 동기화도 MartialHUD 하드코딩
- **Severity**: P2
- **파일**: `modules/core/project_manager.py` L227
- **5Pass**: 확정 ✅ (라인 정확)
- **현상**: `save_v20_anchor()` Bible 저장 시 `bible_root.get("MartialHUD", {}).get("Protagonist", {})`로만 HUD 동기화. 비무협 장르에서는 빈 dict가 반환되어 `record_martial_stats()` 호출이 스킵됨 — HUD 테이블 동기화 미실행 (silent skip).
- **근거**: `self.genre`에 접근 가능. `HUDKeys.get_hud_root(self.genre)` 헬퍼 존재.
- **수정안**: `HUDKeys.get_hud_root(self.genre)` 사용.

### [T1-04] api-contract-v1.yaml에 3개 에러 코드 미선언
- **Severity**: P2
- **파일**: `docs/implementation/api-contract-v1.yaml` L190-200 (enum), `modules/api/bridge_server.py`
- **5Pass**: 확정 ✅
- **현상**: bridge_server.py가 반환하는 에러 코드 3개가 api-contract-v1.yaml의 `ErrorEnvelope.code` enum에 미선언:
  - `INTERNAL_ERROR`: L1349, L1360, L1447, L1464, L1480 (5곳, 500 응답)
  - `INVALID_PROJECT`: L1444, L1461, L1477 (3곳, /quality/*, /safe-ops/*)
  - `INVALID_REQUEST`: L1491, L1506 (2곳, /quality/review)
- **수정안**: api-contract-v1.yaml의 ErrorEnvelope.code enum에 3개 코드 추가.

### [T1-06] db_manager.py: execute_update() commit 누락 — 호출자 의존
- **Severity**: P2
- **파일**: `modules/core/db_manager.py` L1039-1047
- **5Pass**: 확정 ✅ (라인 정확)
- **현상**: `execute_update()`는 `cur.execute(sql, params)` 후 commit을 수행하지 않음. 다른 write 메서드(`save_manuscript`, `archive_seed` 등)는 일관되게 `if not nested: self.commit()` 패턴을 적용. 호출처인 `reflexion_manager.py` L99, L115에서 수동 `self.context.db.conn.commit()`을 호출하여 우회 중.
- **수정안**: 내부에 commit 패턴 추가하거나, 독스트링에 "commit은 호출자 책임"임을 명시.

### [T1-07] db_manager.py: 15개+ 메서드에서 공유 cursor 사용
- **Severity**: P2
- **파일**: `modules/core/db_manager.py` L1533 외 다수
- **5Pass**: 확정 ✅ (라인 정확, `self.cursor.execute` ~185회 사용)
- **현상**: 클래스 독스트링(L54-57)에서 "self.cursor는 backward compatibility용, 신규 코드에서는 로컬 cursor 사용"이라 명시했으나, L1443, L1457, L1537, L1549, L1566, L1579, L1847, L1854, L1873, L1882 등 일반 read/write 메서드에서 대량 사용. RLock이 reentrant이므로 같은 스레드 내 `commit_episode_factory()` 같은 중첩 호출 시 cursor 상태 간섭 이론적 가능.
- **수정안**: 점진적으로 `cur = self.conn.cursor()` + `try/finally: cur.close()` 패턴으로 전환.

### [T1-09] ProjectService: raw cursor 접근으로 DBRepositoryProtocol 우회 (15곳)
- **Severity**: P2
- **파일**: `modules/core/services/project_service.py` L101-370
- **5Pass**: 확정 ✅ (16곳→**15곳** 교정)
- **현상**: `project.db.cursor.execute(...)` 직접 접근 15곳:
  - `_clear_stage2_summary_anchors` (6곳)
  - `_clear_stage2_metadata` (7곳)
  - `reset_stage_2` (1곳)
  - `rollback_episode` (1곳, SELECT + fetchone)
- Protocol이 정의한 `execute_query`/`execute_update`를 사용하지 않음. DBManager 독스트링의 공유 cursor 금지 규칙도 위반.
- **수정안**: Protocol 메서드(`execute_query`/`execute_update`)로 교체.

### [T1-13] RESET.py 테스트 부재
- **Severity**: P2 ↑ (P3에서 승격 — T1-01 P1 버그의 regression 방지에 필수)
- **파일**: `RESET.py` (테스트 없음)
- **5Pass**: 확정 ✅
- **현상**: RESET.py에 대한 테스트가 전혀 없음. T1-01 비무협 장르 HUD 롤백 버그를 수정하더라도 regression 방지 장치가 없음.
- **수정안**: `tests/test_reset.py` 신설. `perform_selective_rewind()`의 장르별 HUD 롤백 분기 검증.

---

## P3 — MINOR (22건)

### [T1-05] run_validator: starting/stopping 상태에서 중복 실행 허용 ↓
- **Severity**: P3 (P2에서 하향)
- **파일**: `modules/api/run_validator.py` L85
- **5Pass**: 부분오탐 — `process_runner.start()`가 `_state != "idle"` 체크로 2차 방어, `bridge_server.py` L1351-1354가 RuntimeError→`RUN_ALREADY_ACTIVE` 409로 변환. 실제 중복 실행은 불가능.
- **현상**: validator 단에서 `runner_state == "running"`만 체크. starting/stopping 상태에서 요청이 통과하면 불필요한 runner.start() 호출 후 RuntimeError→409 변환 경로를 타게 됨.
- **수정안**: `runner_state not in ("idle", "error")`로 확대하면 깔끔하지만, 방어가 이미 존재하므로 저우선.

### [T1-08] WritingDirective.is_empty(): 8개 필드 중 3개만 검사 ↓
- **Severity**: P3 (P2에서 하향)
- **파일**: `modules/core/stage4_types.py` L90-91
- **5Pass**: 부분오탐 — `test_pipeline_wiring.py` L176에서 `emotion_required`만 있는 경우 `is_empty()==True`를 **의도적으로 검증**. `chief_writer_quality.py` L759에서 `emotion_required` 별도 체크. 의도된 설계로 확인됨.
- **현상**: `is_empty()`가 `ending_style`, `metaphor_avoid`, `expression_ban` 3개만 검사. `npc_directives`나 `metaphor_suggest`만 단독 설정되는 시나리오에서 이론적 오판 가능하나, WritingDirectiveGenerator가 이 필드들을 단독으로 설정하는 경로가 확인되지 않음.
- **수정안**: 현행 유지 가능. `npc_directives` 단독 설정 경로가 생기면 그때 확장.

### [T1-10] state_service.py: validate_arc_integrity falsy-check ↓
- **Severity**: P3 (P2에서 하향)
- **파일**: `modules/core/services/state_service.py` L325
- **5Pass**: 부분오탐 — 6개 required_keys(`arc_no`, `ep_start`, `ep_end`, `ep_count`, `tactical_doc`, `beat_sequence`) 중 0이 유효값인 키 없음. arc_no≥1, ep_start≥1, ep_count≥1. tactical_doc는 string(L336에서 len≥500 검사), beat_sequence는 list(L332에서 len≥1 검사).
- **현상**: `not arc_data.get(k)` 패턴은 코드 냄새이나, 현재 값 범위에서 실제 버그 시나리오 없음.
- **수정안**: `if arc_data.get(k) is None`로 변경하면 더 정확하지만, 저우선.

### [T1-11] generate_content_via_router: response.raw=None 잠재적 위험 ↓
- **Severity**: P3 (P2에서 하향)
- **파일**: `modules/core/llm_generate.py` L21
- **5Pass**: 부분오탐 — 유일한 운영 Provider(Gemini)가 `generate()`에서 항상 `raw=response_object`를 설정. Gemini SDK는 에러 시 예외를 던지므로 raw=None 시나리오 불가. 멀티 Provider 활성화 시에만 잠재적 위험.
- **현상**: `LLMResponse.raw` 기본값이 None이나, 현재 운영에서는 도달 불가.
- **수정안**: 멀티 Provider 전환 시 방어 코드 추가 (현재 Gemini-only에서는 저우선).

### [T1-14] db_manager.py: reset_after() commit 파라미터 미사용
- **Severity**: P3
- **파일**: `modules/core/db_manager.py` L2283
- **5Pass**: 확정 ✅ (L2283 시그니처 선언, L2330 무조건 commit)
- **현상**: `commit: bool = True` 파라미터가 존재하지만 본문에서 참조하지 않음.
- **수정안**: 파라미터 제거 또는 `if commit: self.conn.commit()` 조건 추가.

### [T1-15] constraint_db.py: before_arc=0 시 필터 미적용
- **Severity**: P3
- **파일**: `modules/core/constraint_db.py` L324, L348(→L360), L420
- **5Pass**: 확정 ✅ (3곳 모두 `if before_arc and ...` 패턴. 현재 호출 경로에서 before_arc≥1이므로 트리거 불가, 잠재 버그)
- **현상**: `if before_arc and arc_no >= before_arc: break`에서 `before_arc=0`이 falsy로 평가.
- **수정안**: `if before_arc is not None and arc_no >= before_arc: break`.

### [T1-16] vec_memory.py: _ensure_hybrid_tables() 초기화 시 lock 미보호
- **Severity**: P3
- **파일**: `modules/core/vec_memory.py` L170-193
- **현상**: `__init__` 중에만 호출되므로 실질 위험 낮으나, 다른 메서드와 패턴 불일치.
- **수정안**: `with self._db_lock():` 래핑 또는 주석 추가.

### [T1-17] db_manager.py: transaction() IntegrityError 핸들러만 in_transaction 추가 체크
- **Severity**: P3
- **파일**: `modules/core/db_manager.py` L2235-2240
- **현상**: IntegrityError만 `if self.conn.in_transaction:` 체크, 다른 핸들러(OperationalError, Exception)는 무조건 rollback. 패턴 불일치.
- **수정안**: 모든 except 블록에서 `if self.conn.in_transaction:` 패턴으로 통일.

### [T1-18] llm_router.py: _load_provider_configs YAML 실패 시 silent pass
- **Severity**: P3
- **파일**: `modules/core/llm_router.py` L45-46
- **현상**: config 로드 실패 시 로깅 없이 기본값으로 폴백.
- **수정안**: `logging.warning()` 추가.

### [T1-19] llm_router.py: disabled provider lazy-build 논리적 허점
- **Severity**: P3 (dead code 경로)
- **파일**: `modules/core/llm_router.py` L112-125
- **현상**: `get_provider_for_model()`에서 `_providers`에 없고 config가 있으면 enabled 재확인 없이 build. 생성자에서 enabled provider는 이미 등록되므로 사실상 도달 불가.
- **수정안**: `_build_provider` 호출 전 `if provider_config.get("enabled")` 조건 추가.

### [T1-20] llm_schema.py: 알 수 없는 type_name이 그대로 통과
- **Severity**: P3
- **파일**: `modules/core/llm_schema.py` L30
- **현상**: `_TYPE_NAME_TO_GEMINI.get(type_name, type_name)`에서 알 수 없는 타입이 그대로 전달.
- **수정안**: `logging.warning()` 또는 `ValueError` raise.

### [T1-21] prompt_loader.py: 커스텀 YAML 파서 제한사항 미문서화
- **Severity**: P3
- **파일**: `modules/core/prompt_loader.py` L97-165
- **현상**: `UPPER_CASE: |` 패턴만 인식하는 자체 파서. 의도적 설계이나 제한사항 주석 부재.
- **수정안**: 제한사항 주석 명시.

### [T1-22] llm_router.py: get_shared_llm_router 싱글톤 비원자적
- **Severity**: P3
- **파일**: `modules/core/llm_router.py` L134-138
- **현상**: check-then-write에 Lock 없음. GIL + 무상태 Router라 실질 문제 미미.
- **수정안**: `threading.Lock` 추가 (형식적 안전성).

### [T1-23] Stage3Context 독스트링 슬롯 수 불일치
- **Severity**: P3
- **파일**: `modules/core/stage3_context.py` L8-9
- **5Pass**: 확정 ✅ (속성 "7종"→실제 9종, 콜백 "10종"→실제 11종. `adversarial_self_play`, `pass_rate_monitor`, `session_logger` 누락)
- **수정안**: 독스트링 업데이트.

### [T1-24] Stage2Context 독스트링 콜백/확장 수 불일치
- **Severity**: P3
- **파일**: `modules/core/stage2_context.py` L24, L31
- **5Pass**: 확정 ✅ (확장 "18종"→실제 20종, 콜백 "21종"→실제 23종. `context_advisor`, `adversarial_self_play`, `sync_cache_key_to_app`, `session_logger` 누락)
- **수정안**: 독스트링 및 `__slots__` 주석 업데이트.

### [T1-25] AuditServiceProtocol.write_audit_summary 시그니처에 tag 파라미터 누락
- **Severity**: P3
- **파일**: `modules/protocols/app_services.py` L62
- **5Pass**: 확정 ✅
- **현상**: Protocol: `def write_audit_summary(self) -> None`. 구현체: `def write_audit_summary(self, tag: str = "snapshot") -> None`. Protocol을 통해 `tag` 전달 불가.
- **수정안**: Protocol에 `tag: str = "snapshot"` 추가.

### [T1-26] ProjectService.rollback_episode: Protocol에 없는 메서드 호출
- **Severity**: P3
- **파일**: `modules/core/services/project_service.py` L256
- **현상**: `project.get_latest_episode_number()` 호출이 ProjectRepositoryProtocol에 미정의.
- **수정안**: Protocol에 추가하거나 `project.db.get_latest_episode_number()`로 변경.

### [T1-27] ProjectService._clear_stage2_metadata: commit 계약 미문서화
- **Severity**: P3
- **파일**: `modules/core/services/project_service.py` L116-140
- **현상**: DELETE 실행 후 commit 없이 호출자에 의존. 계약이 암묵적.
- **수정안**: 독스트링에 "caller must commit" 명시.

### [T1-28] test_protocols_services: MockProject에 arcs setter 누락
- **Severity**: P3
- **파일**: `tests/test_protocols_services.py` L148-158
- **현상**: `arcs`가 read-only property. Protocol의 setter 계약 미검증.
- **수정안**: `@arcs.setter` 추가 + setter 테스트.

### [T1-29] Stage3Context from_app() 전용 테스트 부재
- **Severity**: P3
- **파일**: `tests/` (미존재)
- **5Pass**: 부분오탐 — Stage4Context는 `tests/test_stage4_context.py`에 10개+ 테스트 존재. **Stage3Context만 전용 테스트 부재**.
- **수정안**: `test_stage3_context.py` 신설 (Stage4 패턴 참고).

### [T1-30] state_service.py: blueprint 파라미터 타입 힌트 부정확
- **Severity**: P3
- **파일**: `modules/core/services/state_service.py` L130
- **현상**: `blueprint: dict = None` — 올바른 힌트는 `dict | None = None`.
- **수정안**: 타입 힌트 수정.

### [T1-31] constants.py: _LazyThreshold 멀티스레드 중복 계산
- **Severity**: P3
- **파일**: `modules/core/constants.py` L40-50
- **현상**: 8 advisory 병렬 실행 시 동일 값 중복 계산. GIL로 데이터 오염 없으나 미세한 성능 낭비.
- **수정안**: Lock 추가 또는 eager 평가 전환 (저우선).

### [T1-32] 기타 P3 항목 (4건 일괄)
- **bridge_server StatusEnvelope에 pid 필드 미선언** (`api-contract-v1.yaml`): `/status` 응답에 `pid` 포함되나 계약 미반영. 수정안: yaml에 `pid: {type: integer, nullable: true}` 추가.
- **logger.py _metrics 카운터 스레드 안전성** (L89): 진단용 메트릭, GIL로 실질 무해. 저우선.
- **error_helper.py severity_emoji 빈 문자열** (L268): 5Pass 확정 — dict 값 전부 `""`, dead code 잔류. 수정안: 매핑 로직 제거.
- **spinners.py _render 미사용 표현식** (L196): 5Pass 확정 — `now - StageSpinner._session_start` 결과 미할당, side-effect 없는 무의미 연산. 수정안: 해당 라인 제거.

---

## 정상 확인 항목

- **Config SSOT 3자 교차 검증**: `models.yaml` ↔ `constants.py` ↔ `base_agent.py` 정합 확인.
- **LLM Router fallback 체인**: primary→backup→추가폴백 3단계, 에러 타입별 분기 정상.
- **response_schemas.py direct generate_content()**: L769 독스트링 예제만. CLAUDE.md 허용 범위.
- **전처리_ssot/contracts 내부 정합성**: schema_version/stage_machine/quality_gates/handoff_rules/artifact_contracts 간 정합 양호.
- **main_a.py 초기화 순서**: dotenv → UI → Logger → System → Orchestrators → SessionLogger → Services → ProjectContext(DB) → agents → DI Context 순서 정상.
- **prompt_builder.py build_validation_context**: app=None 시 except Exception이 전체 감싸고 있어 크래시 안 함 (5Pass 오탐 확인).
- **bridge_server _ok() 반환값**: `data: None`은 정상 사용 (5Pass 오탐 확인).
- **대원칙 위반**: 감지 없음.
- **bare except**: 0건.

---

## 수정 우선순위 제안

| 순위 | 항목 | 이유 |
|------|------|------|
| **1** | T1-01, T1-02, T1-03 | **MartialHUD 하드코딩 3건** — 비무협 장르 운영 시 데이터 손상/손실. `HUDKeys.get_hud_root()` + `NPCHUDKeys.get_key()` 헬퍼가 이미 존재하므로 수정 용이. |
| **2** | T1-13 | **RESET.py 테스트 신설** — P1 수정의 regression 방지에 필수. |
| **3** | T1-04 | **API 계약 에러코드 3개 추가** — 클라이언트 호환성. yaml 수정만으로 해결. |
| **4** | T1-06, T1-07 | **DB 계층 일관성** — execute_update commit + 공유 cursor 전환. 점진적 작업. |
| **5** | T1-09 | **ProjectService Protocol 우회** — 15곳 cursor.execute → Protocol 메서드로 교체. |
| **6** | 나머지 P2 | 방어적 코딩 보강. |
| **7** | P3 전량 | 코드 위생 + 테스트 커버리지 + 독스트링 동기화. |
