Date: 2026-03-31
Status: preflight-watchlist (run-active)
Document Type: preflight watchlist
Mode: ROL live-merge
Run Status: ACTIVE (EP13 Round 1 director review in progress)

# Canary Stage34 Contract-Convergence Preflight Watchlist

## Q1. Context Hierarchy Authority

### Evidence

**Stage 3 Semantic Context Tier Ordering** (`stage3_orchestrator.py` L1198-1228)
- 명시적 prepend 패턴으로 권한 순서가 코드에 고정됨
- Tier 1 (최상위): World State Advisory
- Tier 2: Style Guide Advisory
- Tier 3: Fact Ledger Advisory
- Tier 4: Stale Seed Advisory
- Tier 5: Work Focus Advisory
- Tier 6: Smart Context / Vector Memory
- Tier 7: Treatment Block
- Tier 8 (최하위): Arc Time Markers
- 각 티어는 `_bp_semantic_ctx = _advisory + ("\n\n" + _bp_semantic_ctx if _bp_semantic_ctx else "")` 패턴으로 상위 삽입

**Stage 4 Mandatory Context Assembly** (`stage4_context_builder.py` L2182-2393)
- Tier 0 (절대 상위): Canonical NPC constraints + Canonical numerical facts → `insert(0, _l0_block)` (L2282)
- Tier 1: Continuity Packet → `insert(0, cp_text)` (L2318)
- Tier 2: Hierarchical summaries (series/volume/arc) → `append()`
- Tier 3: Treatment genre extension → `insert(2, ...)` (L2309)
- Tier 4: State Tracker summaries (16개) → `append()` + work_focus 우선순위
- Tier 5: Base mandatory context (HUD, previous episode state)
- Tier 6 (최하위): Advisory slots (ambient NPC, arc constraints)

**Blueprint 분리** (`stage4_interview_round.py` L1328-1340)
- Blueprint은 독립 dict key로 전달, mandatory_context 문자열에 embed 되지 않음

### Hypothesis (Provisional)

**H1-SAFE: 정적 계층 구조는 건전함**
- world_state/fact_ledger가 Stage 3에서 prepend, Stage 4에서 `insert(0, ...)` — 최상위 권한 확보
- Blueprint은 별도 키로 전달 — context string 오염 불가

**H1-WATCH: Retry 피드백 dict spread 경로에서 권한 혼합 가능성**
- `_common_writer_kwargs`에 `director_feedback`이 추가된 후 `**` spread로 전달 (L3809, L3826, L3840)
- 명시적 demarcation 없이 retry feedback과 blueprint이 같은 kwargs dict에 공존
- `_build_retry_advisory_digest()` (L66-95)가 advisory를 `director_feedback`에 병합 — fresh Director 판단과 이전 시도 히스토리 구분 불명

**H1-WATCH: stage_attempts → director_feedback 흐름에서 마커 부재**
- `stage_attempts` DB 데이터가 `director_feedback`에 합류 가능 (L2071-2081)
- 다음 라운드에서 "새로운 Director 피드백"과 "이전 시도 히스토리"를 구별하는 구조적 마커 없음

### Pending Live Confirmation

- [ ] EP11 4-round retry 과정에서 이전 시도 피드백이 blueprint authority를 오염시켰는지 artifact 비교 필요
- [ ] EP13 strong_advisory_escalation 시 director_feedback 내용이 blueprint 지시와 충돌하는지 확인 필요

---

## Q2. Director Contract Executability

### Evidence

**Verdict Enum** (`response_schemas.py` L134, L139)
- PASS, PASS_WITH_FIX, REJECT 3개 verdict 정의

**Stage 3 Validate Gate** (`stage3_orchestrator.py` L870-885)
- PASS/PASS_WITH_WARNING → `_handle_success()`
- REJECT/ERROR → `_handle_failure()`

**Stage 4 Verdict Gate** (`stage4_interview_round.py` L4285-4366)
- Quality Floor: PASS + score < 90 → REJECT 강제 하향 (L4316)
- PASS_WITH_FIX → `_evaluate_pass_with_fix_contract()` (L1898-1921)
  - fix_scope == "inplace" 검증 (L1902)
  - fix_pack.ready 검증 (L1909)
  - 미충족 시 → REJECT 하향 (L2003)

**fix_pack Contract 검증** (`stage4_interview_round.py` L1923-1936)
- 7개 실패 조건 정의: missing_fix_scope, non_local_fix_scope, missing_patch_targets, missing_must_fix, missing_do_not_regress, missing_success_condition, invalid_target_kind
- 모든 실패 → REJECT 하향

**Blank/Invalid Scope Gate** (`stage4_interview_round.py` L2098-2150, Lane2-G2)
- authoritative_fix_scope가 {inplace, partial, full} 외 → REJECT 강제
- blank_authoritative_fix_scope / invalid_authoritative_fix_scope 위반 유형 기록

**Patch Execution** (`stage4_retry_runtime.py` L185-331, L515-581)
- `chief_writer.inplace_patch(fix_pack=...)` 호출 (L533)
- 출력 비어있음 / 길이 < 2000 / change ratio > 30% → patch 실패 → REJECT
- Exception → `should_abort=True` → REJECT

### Hypothesis (Provisional)

**H2-SAFE: Director contract fail-closed 확인됨**
- PASS_WITH_FIX는 fix_scope="inplace" + fix_pack.ready일 때만 실행, 아니면 REJECT 하향
- blank/invalid scope → REJECT 강제 (fail-closed)
- 7개 fix_pack 실패 조건 모두 → REJECT
- patch 실행 실패 → REJECT

**H2-CONFIRMED-BY-LIVE: EP12 continuity_firewall 사례**
- EP12 R1: PASS_WITH_FIX 발급 후 score 44 + continuity_firewall → REJECT
- EP12 R2: PASS_WITH_FIX score 90, repair_scope=inplace → action items 발급 후 PASS
- fail-closed 경로가 실제 런타임에서 작동함을 확인

**H2-WATCH: EP13 missing_patch_targets**
- EP13 R1: strong_advisory_escalation이 fix_pack에서 missing_patch_targets → REJECT
- fix contract 준비 시점이 escalation 결정 시점보다 늦음 — contract 비완성 상태에서 escalation 트리거

### Pending Live Confirmation

- [ ] EP13 Round 2에서 fix_pack이 완성되어 PASS_WITH_FIX로 전환되는지 또는 full REJECT 유지되는지
- [ ] run 종료 시점의 director_selections DB 레코드와 artifact 대조

---

## Q3. Retry Convergence

### Evidence

**Stage 3 Hard Caps**
- Blueprint retries: max 10회 (0-9) (`three_phase_blueprint_runtime.py` L1542, L1572)
- PASS_WITH_FIX patches: max 3회 (L932)
- Score-stall early-exit (PF-EE): 점수 미개선 시 break (L971-978)
- Terminal failure fallback: score >= 60이면 PASS_WITH_WARNING (L1298)

**Stage 4 Hard Caps**
- Interview rounds: max 5회 (default, `stage4_orchestrator.py` L523)
- V75-D inplace blueprint patch: 스트림당 1회 (L906-916)
- V75-B blueprint regeneration: 스트림당 1회 (L917-927)

**Escalation Ladder** (`stage4_outcome_runtime.py` L841-936)
1. Level 0: 기본 REJECT + director feedback
2. Level 1: QR-7 Plateau Detection (L938-1025) — plateau 2회 반복 시 fix_scope="full", repair_scope="rewrite_regenerate"로 강제 전환
3. Level 2: V75-D Inplace Blueprint Patch (L906-916) — logic_error_streak >= threshold 시
4. Level 3: V75-B Blueprint Regeneration (L917-927) — inplace 실패 후 logic_error_streak >= threshold 시

**Pathology Detection** (`stage4_outcome_runtime.py` L1027-1205)
- Pathology fingerprint = reject_bucket + contradiction_type + fix_scope + firewall_triggered
- 반복 2회 이상 → STAGE4_RETRY_PATHOLOGY_REPEAT 이벤트 → QR-7 escalation 트리거
- Bucket streak 3회 이상 → TF-29 advisory (L765)
- Contradiction type streak 2회 + logic_error_streak 2회 → A-4 advisory (L815)

**Cross-Stage**
- Stage 4 max rounds 소진 → Stage 2 Arc 재생성 제안 (operator 결정)
- Stage 4 → Stage 3 역방향 피드백: `_build_stage4_to_3_reverse_feedback()` (L1215-1226)
- 무한 루프 방지: hard caps + escalation + score tracking으로 보장

### Hypothesis (Provisional)

**H3-SAFE: 수렴 보장됨 (hard cap 기준)**
- Stage 3: 10 retries + 3 PWF patches → 최악의 경우에도 종료
- Stage 4: 5 rounds → 최악의 경우에도 종료
- V75-D → V75-B 에스컬레이션 사다리 존재

**H3-CONFIRMED-BY-LIVE: EP11 수렴 사례**
- EP11: 4-round retry (R0 REJECT → R1 REJECT+plateau → R2 REJECT → R3 PASS)
- R1에서 V75-D blueprint inplace patch 적용 (change_ratio 0.1039)
- R2에서 plateau 감지되었으나 한 번 더 시도 후 R3에서 수렴
- 에스컬레이션 사다리가 실제로 작동함

**H3-CONFIRMED-BY-LIVE: EP12 firewall → patch → PASS 사례**
- EP12 R1: continuity_firewall (자본금 CRITICAL) → V75-D blueprint patch (change_ratio 0.1796) → R2 PASS_WITH_FIX
- firewall 트리거 → blueprint 수정 → 수렴 경로 확인

**H3-WATCH: EP13 escalation 패턴**
- EP13 R1: strong_advisory_escalation + missing_patch_targets → REJECT
- fix contract 미완성 상태에서 escalation — 다음 round에서 fix contract가 생성되는지, 또는 전략이 full regenerate로 전환되는지 미확인

### Pending Live Confirmation

- [ ] EP13 Round 2+에서 fix contract 완성 여부 또는 전략 전환 여부
- [ ] EP13이 max rounds (5) 소진 없이 수렴하는지
- [ ] EP14 Stage 4 진입 시 EP13에서의 에스컬레이션 히스토리가 깨끗하게 리셋되는지

---

## Q4. Persistence Continuity

### Evidence

**Post-PASS Persistence Sequence** (`stage4_post_processor.py` L917-1007, `stage4_post_pass_runtime.py` L1179-1227)

1. PRIMARY (atomic): Manuscript + HUD → `db.save_manuscript()` [동일 트랜잭션]
2. SECONDARY (non-transactional): Quality labels/signals → `db.save_episode_quality_label()` / `save_episode_quality_signal()`
3. TERTIARY (pipeline):
   - Episode Bible → `db.save_episode_bible(ep_num, bible_delta)` (L772)
   - World State + Fact Ledger → `_save_world_state_atomic()` (L1197)
     - Transaction mode: WorldState.save() + FactLedger.save() 동일 트랜잭션
     - Sequential mode: 각각 별도 트랜잭션 (partial failure 가능)
4. TELEMETRY (non-transactional): director_selections, stage_attempts → 별도 commit

**Cache Invalidation** (`db_manager.py` L634-637)
- `save_episode_bible()` 후 `_cumulative_bible_cache` 무효화
- commit 후 invalidation 순서 → 프로세스 크래시 시 stale cache 가능성 (낮음)

**Next Episode Context Rebuild** (`stage4_context_builder.py` L2098-2214)
- `db.get_cumulative_bible(next_ep - 1)` → 캐시 우선, miss 시 DB 점진적 rebuild
- `world_state.get_summary()` → 메모리 내 `_state` 읽기 (init 시 DB anchor에서 로드)
- `load_chain_link_section()` → `db.load_anchor(f"chain_link_{ep}")`

**World State / Fact Ledger Init** (`stage3_orchestrator.py` L735-769)
- `WorldStateManager(db)` → `db.load_anchor("world_state")` — DB anchor에서 직접 로드
- `FactLedger(db)` → `db.load_anchor("fact_ledger")` — DB anchor에서 직접 로드

### Hypothesis (Provisional)

**H4-SAFE: 정상 경로의 persistence 건전함**
- PASS 후 manuscript → bible → world_state → fact_ledger 순서 저장
- 다음 화 context rebuild가 동일 DB에서 읽음
- cache invalidation 존재

**H4-WATCH: Sequential Mode Partial Failure (SEAM #1)**
- `transaction()` 미사용 시 sequential_mode = True
- WorldState.save() 성공 → FactLedger.save() 실패 시 → WorldState만 갱신됨
- 다음 화: WorldState EP(N) + FactLedger EP(N-1) 불일치
- 현재 canary에서 실제 발생 여부 미확인

**H4-WATCH: In-Memory Mutation Before Save (SEAM #2)**
- `world_state.update_from_state_changes()` → 즉시 `_state` 변경 → 이후 `save()` 호출
- save() 실패 시 메모리 오염 (DB 로드로 복구 가능하나 같은 프로세스에서는 오염 상태 유지)

**H4-WATCH: Telemetry Gap (SEAM #3)**
- `director_selections` / `stage_attempts`가 별도 트랜잭션 — episode_bible 이후 실패 시 audit trail 불완전
- 서사 무결성에는 영향 없으나 분석/디버깅에 영향

**H4-CONFIRMED-BY-LIVE: EP10-12 Persistence 성공**
- EP10-12 모두 drafts/ 에 원고 저장 확인
- WorldState EP12 기준: 자본 33억 원, 금 현물 매집 채널 확보
- FactLedger EP12 기준: 자본 33억 원 고정
- state_changes.jsonl에 6건 기록 (EP10-12 각 2건)
- 저장 → 다음 화 컨텍스트 연결이 EP10→11→12 경로에서 작동함

### Pending Live Confirmation

- [ ] EP13 PASS 후 persistence sequence가 동일하게 실행되는지
- [ ] EP13→14 컨텍스트 전환 시 WorldState/FactLedger가 EP13 기준으로 갱신되었는지
- [ ] run 종료 후 DB anchor vs 마지막 state_changes.jsonl 대조
- [ ] sequential_mode 발생 여부 (runtime_audit에서 TF-C10 로그 검색)
