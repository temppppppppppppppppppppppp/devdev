# Phase 4B Call Graph: 메서드 수준 호출 그래프 + 부수효과

> 작성일: 2026-02-13
> SSOT: (1) 코드베이스 (커밋 `1b3de64`), (2) `docs/step4_blueprint.md`
> 표기법: `→` 호출, `[SE]` 부수효과, `[DB]` DB 위반, `[IO]` 파일 I/O, `[LLM]` API 호출

---

## 1. AuditService (Batch 4B-1)

```
_audit_event(event_type, message, data)          main_a.py:2992
├── [SE] self.runtime_audit.append(event)         :3003  — 메모리 리스트 추가
└── [SE] self._audit_buffer.append(event)         :3005  — 버퍼 리스트 추가

_flush_audit_buffer()                             main_a.py:3007
├── self.current_project.paths.root               :3015  — 경로 참조
├── [IO] log_path.open("a") → jsonl 기록          :3018  — 파일 append
└── [SE] self._audit_buffer.clear()               :3021  — 버퍼 초기화

_write_audit_summary(tag)                         main_a.py:3025
├── → _flush_audit_buffer()                       :3027  — 내부 호출
├── self.runtime_audit[-200:]                     :3037  — 최근 200건 참조
├── [IO] summary_path.write_text(json)            :3042  — JSON 파일 쓰기
└── self.ui.log(...)                              :3044  — UI 로그 (실패 시만)
```

**부수효과 요약**:
- 메모리: `runtime_audit` 리스트, `_audit_buffer` 리스트 변경
- 파일: `{project}/logs/runtime_audit.jsonl` (append), `runtime_audit_summary.json` (overwrite)
- DB: 없음
- LLM: 없음

**호출자** (추출 후에도 유지해야 할 경로):
- `stage2_orchestrator.py`: `self.app._audit_event()` — 36건
- `stage4_orchestrator.py`: `self.app._write_audit_summary()` — 간접 (flush 포함)
- `main_a.py` 내부: `_validate_arc_mapping`, `_validate_arc_data_fields` 등 12+ 메서드

---

## 2. FeedbackEnricher (Batch 4B-2)

### 실질 로직 메서드

```
_enrich_director_result(audit_result, stage, content_length)  main_a.py:281
├── audit_result dict 직접 변형                                :312  — [SE] dict mutation
├── → _analyze_score_breakdown(score_breakdown)                :384
│   └── 순수 함수 (dict → dict, 부수효과 없음)                 :424-510
├── → _quantify_reject_feedback(reason, content_length, ...)   :409
│   └── → self._feedback_system.quantify_reject_feedback()     :422  — 위임
├── audit_result["action_items"] = action_items                :379  — [SE] dict mutation
├── audit_result["responsibility"] = ...                       :401  — [SE] dict mutation
└── audit_result["quantified_feedback"] = quantified           :413  — [SE] dict mutation

_get_dynamic_critical_keywords()                               main_a.py:533
├── self.failure_learner.records                               :549  — V50 모듈 참조
└── 순수 계산 (list 반환)

_analyze_rejection_pattern_v60(rejection_history, arc_no)      main_a.py:614
├── → _normalize_rejection_reason(reason)                      :638
│   └── 순수 함수 (str → str)                                  :676-699
├── → _get_rejection_fix_guide(normalized_reason)              :662
│   └── 순수 함수 (str → str, dict lookup)                     :701-714
└── 순수 계산 (str 반환)
```

### Thin 위임 메서드 (11개)

```
_quantify_reject_feedback(...)       → self._feedback_system.quantify_reject_feedback()     :420
_simplify_prompt_for_retry(...)      → self._feedback_system.simplify_prompt_for_retry()    :513
_build_strong_kind_feedback(...)     → self._feedback_system.build_strong_kind_feedback()   :517
_build_focused_context(...)          → self._feedback_system.build_focused_context()         :521
_build_minimal_arc_context(...)      → self._feedback_system.build_minimal_arc_context()     :525
_generate_arc_position_guide(...)    → self._prompt_builder.generate_arc_position_guide()    :529
_generate_writer_guidance_v60_8(...) → self._prompt_builder.generate_writer_guidance_v60_8() :577
_generate_structured_arc_feedback(.) → self._feedback_system.generate_structured_arc_feedback():590
_gen_reverse_fb_stage4_to_3(...)     → self._feedback_system.generate_reverse_feedback_...() :596
_gen_reverse_fb_stage3_to_2(...)     → self._feedback_system.generate_reverse_feedback_...() :602
_generate_arc_context_v60(...)       → self._prompt_builder.generate_arc_context_v60()       :606
_get_adaptive_feedback_intensity(.)  → self._feedback_system.get_adaptive_feedback_intensity():610
```

**부수효과 요약**:
- 메모리: `audit_result` dict 직접 변형 (caller 소유 dict)
- 파일: 없음
- DB: 없음
- LLM: 없음 (위임 대상인 `_feedback_system`/`_prompt_builder`도 LLM 미호출)
- 외부 모듈 참조: `self._feedback_system`, `self._prompt_builder`, `self.failure_learner` (V50, optional)

**호출자**:
- `stage4_orchestrator.py`: `self.app._enrich_director_result()` — Director 결과 후처리 핵심 경로
- `stage2_orchestrator.py`: `self.app._generate_structured_arc_feedback()`, `self.app._generate_arc_context_v60()` 등

---

## 3. NarrativeSummary (Batch 4B-2)

```
_generate_narrative_summary(up_to_ep)                     main_a.py:4166
├── self.current_project.db.get_recent_manuscripts(...)   :4183  — DB 읽기
├── [LLM] self.sys.api_client.models.generate_content()   :4258  — Gemini Flash 요약
├── self.current_project.db.save_anchor(anchor_key, ...)   :4270  — DB 쓰기
├── [DB] self.current_project.db.conn.commit()             :4278  — ⚠️ DB 위반
├── [SE] self._narrative_summaries_cache = None            :4287  — 캐시 무효화
└── self.ui.log(...)                                       :4279

_load_narrative_summaries() → str                          main_a.py:4289
├── [SE] 캐시 히트 시 즉시 반환                             :4295-4296
├── self.current_project.db.load_anchor(...)               :4301  — DB 읽기 (5화 간격 루프)
├── self.current_project.load_v20_anchor("series_summary") :4310  — DB 읽기
├── self.current_project.load_v20_anchor(f"volume_summary_{n}") :4319  — DB 읽기 (최대 20회)
├── [SE] self._narrative_summaries_cache = result          :4340  — 캐시 저장
└── 문자열 반환
```

**부수효과 요약**:
- 메모리: `_narrative_summaries_cache` 변경
- 파일: 없음
- DB: `save_anchor` (정상), `conn.commit()` (위반 1건 — `:4278`)
- LLM: Gemini Flash 1회 호출 (`_generate_narrative_summary`)

---

## 4. ValidationHelpers (Batch 4B-3)

```
_validate_arc_mapping(refined_arc, enriched_block, ...)    main_a.py:2806
├── refined_arc["arc_no"] = expected_arc_no                :2816  — [SE] dict mutation
├── refined_arc["ep_start"] = expected_ep_start            :2833  — [SE] dict mutation
├── → self._extract_block_index(block_id)                  :2840
├── → self._audit_event(...)                               :2813,2828,2844  — 감사 이벤트
└── → self.ui.log(...)                                     :2812,2827,2842

_validate_arc_data_fields(arc_data, arc_idx)               main_a.py:3095
├── arc_data[field] = default_val                          :3129  — [SE] dict mutation (다수)
├── → self._audit_event(...)                               :3131
└── → self.ui.log(...)                                     :3130

_validate_arc_integrity(arc_data) → bool                   main_a.py:3199
├── → self._audit_event(...)                               :3216,3221,3225
└── → self.ui.log(...)                                     :3214,3220,3224

_validate_blueprint_integrity(blueprint) → bool            main_a.py:3229
├── → self._audit_event(...)                               :3243,3247,3251
└── → self.ui.log(...)                                     :3242,3246,3250

_load_genre_references() → tuple[list, list]               main_a.py:3151
├── self.selected_genre                                    :3167  — 장르 참조
├── [IO] Path("modules/core/laws/seeds/...").read_text()   :3183,3185
├── → self._audit_event(...)                               :3188
└── → self.ui.log(...)                                     :3187

_extract_pattern_keywords(pattern_profile) → list          main_a.py:2848
└── 순수 함수 (re.sub, re.split)

_pattern_presence_check(text, pattern_profile, min_hits)   main_a.py:2867
└── → _extract_pattern_keywords(...)                       :2870

_load_character_archetypes(genre) → dict                   main_a.py:2898
└── [IO] archetype_path.read_text(encoding="utf-8")        :2904

_get_archetype_reference_for_npcs(npc_profiles, genre)     main_a.py:2909
└── → _load_character_archetypes(genre)                    :2914

_build_validation_context(...)  → _prompt_builder 위임      main_a.py:2880
_extract_npc_profiles(...)      → _prompt_builder 위임      main_a.py:2890
_get_character_traits()         → _prompt_builder 위임      main_a.py:2894
_classify_rejection_feedback(.) → _feedback_system 위임     main_a.py:2988
```

**부수효과 요약**:
- 메모리: `refined_arc`/`arc_data` dict 직접 변형 (caller 소유)
- 파일: JSON 읽기 (archetypes, cliches, locations)
- DB: 없음
- LLM: 없음

---

## 5. DataManager (Batch 4B-3)

```
_reset_stage_2()                                           main_a.py:3907
├── input() — 사용자 확인                                   :3909
├── [DB] self.current_project.db.cursor.execute("DELETE")  :3912  — ⚠️ 직접 SQL
├── → self._safe_commit()                                  :3913
├── [SE] self.current_project.arcs = []                    :3916  — 메모리 초기화
└── → self.ui.log(...)

_rewind_stage_2()                                          main_a.py:3921
├── input() — 사용자 확인                                   :3930
├── self.current_project.save_v20_anchor("arcs", ...)      :3948  — 안전 API
├── [SE] self.current_project.arcs = updated_arcs          :3951  — 메모리 동기화
└── → self.ui.log(...)

_rollback_episode()                                        main_a.py:3957
├── self.current_project.get_latest_episode_number()       :3960
├── input() — 사용자 확인                                   :3968
│
├── [Phase 1: HUD 롤백]                                    :3995-4027
│   ├── [DB] db.cursor.execute("SELECT ... state_logs")    :3996  — ⚠️
│   ├── [DB] db.cursor.fetchone()                          :3997  — ⚠️
│   ├── [DB] db.cursor.execute("SELECT ... anchors")       :4004  — ⚠️
│   ├── [DB] db.cursor.fetchone()                          :4005  — ⚠️
│   ├── [SE] self.current_project.master_bible = ...       :4027  — 메모리 변형
│   └── [DB] db.cursor.execute("UPDATE anchors ...")       :4021  — ⚠️
│
├── [Phase 2: SQL 삭제 — 6테이블]                           :4036-4041
│   └── [DB] db.cursor.execute(f"DELETE FROM {t} ...")     :4040  — ⚠️ (6테이블 루프)
│
├── [Phase 3: Lore/Seeds 정리]                             :4043-4049
│   ├── [DB] db.cursor.execute("DELETE FROM encyclopedia")  :4044  — ⚠️
│   ├── [DB] db.cursor.execute("DELETE FROM karma_status") :4045  — ⚠️
│   └── [DB] db.cursor.execute("UPDATE seeds ...")         :4046  — ⚠️
│
├── [Phase 3.5: Episode Bibles 롤백]                       :4052
│   └── self.current_project.db.delete_episode_bibles_after():4052  — 안전 API
│
├── [Phase 4: sqlite_sequence 초기화]                       :4059
│   └── [DB] db.cursor.execute("DELETE FROM sqlite_seq..") :4059  — ⚠️
│
├── → self._safe_commit()                                  :4063
│
├── [Phase 5: 물리 파일 삭제]                               :4068-4076
│   └── [IO] f.unlink() — 원고 .txt 삭제                   :4073
│
├── [Phase 6: 벡터 DB 소거]                                :4079-4086
│   └── [SE] self.memory.collection.delete(...)            :4081  — VectorDB
│
├── [Phase 7: 데이터 리로드]                               :4089
│   └── [SE] self.current_project._load_from_db()          :4089  — 전체 리로드
│
└── → self.ui.log(...)

_wipe_production_data()                                    main_a.py:4101
├── input() — 사용자 확인                                   :4103
├── [Phase 1: 7테이블 삭제]                                :4131-4135
│   └── [DB] db.cursor.execute(f"DELETE FROM {t}")         :4135  — ⚠️ (7테이블 루프)
├── [Phase 2: Seeds 복구]                                  :4137-4139
│   ├── [DB] db.cursor.execute("UPDATE seeds ...")         :4138  — ⚠️
│   └── [DB] db.conn.commit()                              :4139  — ⚠️
├── [Phase 3: 파일 삭제]                                   :4142-4143
│   └── [IO] f.unlink() — 원고 .txt 삭제                   :4143
├── [Phase 4: VectorDB 초기화]                             :4147-4151
│   └── [SE] self.memory.collection.delete(...)            :4149
└── → self.ui.log(...)
```

**부수효과 요약**:
- 메모리: `current_project.arcs`, `current_project.master_bible` 변형
- 파일: 원고 `.txt` 파일 삭제
- DB: **직접 SQL 20건** — DELETE, UPDATE, SELECT (cursor.execute/fetchone)
- VectorDB: `memory.collection.delete()`
- LLM: 없음

---

## 6. Stage3Orchestrator (Batch 4B-4)

```
_stage_3_batch_blueprinting()                              main_a.py:3280
│
├── [Lazy Init Block]                                      :3296-3349
│   ├── StateTracker 초기화 (미존재 시)                     :3299-3312
│   │   └── [SE] self.state_tracker = StateTracker(...)    :3300
│   ├── WorldStateManager 초기화 (미존재 시)               :3317-3329
│   │   └── [SE] self.world_state = WorldStateManager(...) :3321
│   └── FactLedger 초기화 (미존재 시)                      :3334-3349
│       └── [SE] self.fact_ledger = FactLedger(...)        :3338
│
├── [범위 설정]                                            :3354-3396
│   ├── self.current_project.arcs[-1].get("ep_end")        :3354
│   ├── self.current_project.db.get_latest_blueprint_number() :3357
│   ├── → self._get_max_episode_from_manuscripts()         :3360
│   └── → self._get_int_input(...)                         :3371
│
├── [이전 Blueprint 로드]                                   :3388-3391
│   └── self.current_project.get_blueprint(prev_ep)        :3389  — DB 읽기 (최대 30회)
│
├── [에피소드 루프]                                         :3398-3647
│   ├── self.current_project.get_blueprint(working_ep)     :3402  — 스킵 체크
│   ├── → self._get_arc_context_for_episode(working_ep)    :3425
│   ├── → self._validate_arc_data_fields(arc_data, ...)    :3437
│   │
│   ├── [Entity Registry 추출]                             :3447-3481
│   │   ├── self.agents["state_extractor"].extract_...()   :3454  — [LLM]
│   │   ├── → self._get_protagonist_name()                 :3462
│   │   └── → self._fix_entity_registry_protagonist(...)   :3463
│   │
│   ├── [이전 원고 로드]                                   :3540-3555
│   │   └── self.current_project.db.get_manuscript(ep)     :3542  — DB (최대 30회)
│   │
│   ├── [Blueprint 생성]                                   :3557-3572
│   │   └── [LLM] self.agents["three_phase_bp"].generate()  — 12 파라미터
│   │
│   ├── [결과 처리]                                        :3591-3647
│   │   ├── → self._validate_blueprint_integrity(bp)       :3593
│   │   ├── self.current_project.save_episode_blueprint()  :3601  — DB 쓰기
│   │   ├── → self._safe_commit()                          :3602
│   │   └── → self._audit_event(...)                       :3614
│   │
│   └── [실패 처리 — 연속 3회 시 중단]                      :3643-3647
│
└── [완료 처리]                                            :3652-3679
    ├── → self._write_audit_summary("stage3_complete")     :3652
    └── [IO] notifier.send_notification(...)               :3672  — Slack 알림
```

**부수효과 요약**:
- 메모리: `self.state_tracker`, `self.world_state`, `self.fact_ledger` lazy init 가능, `self._entity_cache_arc_idx`, `self._cached_entity_registry` 변경
- 파일: Slack 알림 (외부 서비스)
- DB: `get_blueprint`, `get_manuscript`, `save_episode_blueprint`, `_safe_commit` (모두 안전 API)
- LLM: `agents["three_phase_bp"].generate()`, `agents["state_extractor"].extract_cumulative_state()`

---

## 7. Stage0Orchestrator 핵심 메서드 (Batch 4B-4)

```
_phase_0_recovery()                                        main_a.py:2022
├── self.current_project.master_bible                      :2030  — bible 존재 체크
├── → self._stage_0_extended()                             :2041  — 내부 호출
│   ├── → self._ui_select_bible()                          :2175
│   ├── → self._ui_select_treatment()                      :2195
│   ├── → self._enrich_treatment_blocks(...)               :2220
│   │   └── [LLM] self.agents["analyst"].generate(...)
│   ├── → self._extend_blocks(...)                         :2280
│   ├── self.current_project.db.save_anchor(...)           — DB 쓰기
│   └── → self._safe_commit()
│
├── self.agents["analyst"] 직접 사용                       — [LLM] 아크 분석
├── [SE] self.current_project.master_bible = ...            — 메모리 변형
└── → self._audit_event(...)

_stage_1_volumes()                                         main_a.py:2459
├── self.agents["analyst"].generate(...)                   — [LLM] 볼륨 전략 생성
├── [SE] self.current_project.volumes = [...]              — 메모리 변형
├── self.current_project.db.save_anchor("volumes", ...)    — DB 쓰기
├── → self._safe_commit()
├── → self._show_volume_table(volumes)                     — UI 출력
└── → self._validate_volume_boundaries(...)                — 검증
```

**부수효과 요약**:
- 메모리: `master_bible`, `volumes` 변형
- 파일: bible JSON 파싱
- DB: `save_anchor`, `_safe_commit`
- LLM: `agents["analyst"]` 다수 호출

---

## 8. AppBootstrap (Batch 4B-5)

```
boot()                                                     main_a.py:798
├── → self._select_genre()                                 :802  — UI 입력
├── → self._select_project()                               :804  — UI 입력
├── self.sys.boot_v20_project(project_name)                :823  — 프로젝트 초기화
├── [SE] self.current_project = self.sys.project           :824
├── [SE] self.current_project.genre = self.selected_genre  :827
├── self.current_project.db.load_anchor("genre_info")      :831  — DB 읽기
├── self.current_project.db.save_anchor("genre_info", ...) :847  — DB 쓰기
├── [SE] self.sys.hud = create_hud_manager(...)            :853
├── [SE] self.sys.guard = create_genre_guard(...)          :862
├── → self._check_vector_db_lock(project_name)             :867
├── [SE] self.memory = LongTermMemory(...)                 :871
├── [SE] self.blueprint_memory = BlueprintMemory(...)      :877
├── → self._attach_agents()                                :882  — 에이전트 전체 초기화
│   └── [413줄] 15 LLM 에이전트 + 31 V50 모듈 생성
│       ├── [SE] self.agents = {} — 15+ 에이전트 할당
│       ├── [SE] self.state_tracker = StateTracker(...)
│       ├── [SE] self._feedback_system = FeedbackSystem(...)
│       ├── [SE] self._prompt_builder = PromptBuilder(...)
│       ├── [SE] self.failure_learner = ... (V50)
│       └── ... (31개 V50 모듈)
└── → self._run_main_process()                             :886  — 메인 루프 진입

_ignite_quad_cache_system()                                main_a.py:916
├── self.current_project.db.load_anchor("sys_caches")      :955  — DB 읽기
├── [LLM] self.sys.api_client.caches.create(...)           :967,992,1016  — Gemini 캐시 3회
├── self.current_project.db.save_anchor("sys_caches", ...) :1032  — DB 쓰기
├── → self._safe_commit()                                  :1033
├── [SE] self.agents["writer"].cache_name = ...            :1052  — 에이전트 캐시 주입
└── → self._audit_event(...)                               :1035
```

**부수효과 요약**:
- 메모리: `self.current_project`, `self.selected_genre`, `self.sys.hud`, `self.sys.guard`, `self.memory`, `self.agents` (15+31개), `self.state_tracker`, `self._feedback_system`, `self._prompt_builder` 등 **55개 속성 중 대부분**
- 파일: 프로젝트별 `.env` 로드
- DB: `load_anchor`, `save_anchor`, `_safe_commit`
- LLM: Gemini Context Cache 3회 생성

---

## 9. StageDispatcher (Batch 4B-5)

```
_run_main_process()                                        main_a.py:1816
├── self.ui.console.clear()                                :1837  — UI
├── self.ui.title(...)                                     :1840
├── self.sys.check_v20_readiness()                         :1846  — 상태 체크
├── self.ui.menu(menu)                                     :1863  — 메뉴 표시
│
├── [디스패치]
│   ├── "0" → self._phase_0_recovery()                     :1866
│   ├── "1" → self._stage_1_volumes()                      :1868
│   ├── "2" → self._stage_2_arcs()                         :1876
│   ├── "3" → self._stage_3_batch_blueprinting()           :1879
│   ├── "4" → self._stage_4_v2_chief_writer(limit_mode)    :1882
│   ├── "5" → self._shutdown_app()                         :1884
│   ├── "44" → self._rollback_episode()                    :1887
│   ├── "77" → self._wipe_production_data()                :1889
│   ├── "88" → self._reset_stage_2()                       :1891
│   └── "99" → self._rewind_stage_2()                      :1893
│
├── [KeyboardInterrupt]                                    :1895
│   └── → self._shutdown_app()                             :1897
│
└── [Exception]                                            :1900
    ├── [IO] error_log 파일 쓰기                           :1909-1912
    └── → self._shutdown_app()                             :1918

_shutdown_app()                                            main_a.py:1927
├── → self._flush_audit_buffer()                           — 감사 로그 flush
├── → self._write_audit_summary("shutdown")                — 요약 기록
├── → self._safe_commit()                                  — DB 커밋
├── self.current_project.db.conn.close() (있을 경우)       :2006  — [DB] 위반 가능
└── → self.ui.log(...)
```

**부수효과 요약**:
- 메모리: 없음 (순수 디스패치)
- 파일: 에러 로그 (`{project}/logs/error.log`)
- DB: `_safe_commit` (shutdown 시)
- LLM: 없음 (각 Stage 내부에서 호출)

---

## 상태 변이 8건 총목록 (stage2에서 발견, stage4 0건)

| # | 변이 | 위치 | 모듈 | 유형 |
|---|------|------|------|------|
| 1 | `self.state_tracker = StateTracker(...)` | `main_a.py:3300` | Stage3 | lazy init |
| 2 | `self.world_state = WorldStateManager(...)` | `main_a.py:3321` | Stage3 | lazy init |
| 3 | `self.fact_ledger = FactLedger(...)` | `main_a.py:3338` | Stage3 | lazy init |
| 4 | `self._entity_cache_arc_idx = arc_idx` | `main_a.py:3474` | Stage3 | 캐시 마킹 |
| 5 | `self._cached_entity_registry = ...` | `main_a.py:3457` | Stage3 | 캐시 저장 |
| 6 | `self.current_project.arcs = []` | `main_a.py:3916` | DataMgr | 메모리 초기화 |
| 7 | `self.current_project.arcs = updated_arcs` | `main_a.py:3951` | DataMgr | 메모리 동기화 |
| 8 | `self.current_project.master_bible = bible_data` | `main_a.py:4027` | DataMgr | 메모리 동기화 |

→ 모두 `self.app` 경유 Facade 패턴으로 보존 가능. 추출 모듈에서 `self.app.state_tracker = ...` 형태로 할당.
