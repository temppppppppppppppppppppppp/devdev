# 전 스테이지 딥다이브 — 수정 후보 SSOT

> Independent Re-Audit (Codex, 2026-03-16)
>
> Status: historical research memo, not live execution SSOT.
>
> Operational note: this document mixes the original 25 candidate table with later `[3PA]` / `[3PA-R2]` reclassification results on the same page, so the opening matrix is no longer safe to execute from directly.
>
> Confidence: 96% for memo-only use. Direct execution confidence is below 95% until each surviving item is revalidated against the current workspace and canonical roadmap.

| Field | Value |
|-------|-------|
| **Baseline** | `bbb00a77` |
| **Date** | 2026-03-15 |
| **Scope** | Stage 0/1/2/3/4 + Cross-stage 전체 파이프라인 |
| **조사 방법** | 소스 코드 직접 읽기 + 라인 번호 확인 |
| **총 발견** | 71건 (5개 스테이지 + 크로스스테이지) |
| **수정 후보** | 25건 (아래 선별 기준 적용) |

## 선별 기준

다음 중 하나 이상 해당하는 항목만 수정 후보로 선정:
1. **데이터 소실** — 사용자 입력/LLM 출력/상태가 조용히 사라짐
2. **연속성 파괴** — 에피소드 간 모순, 캐릭터/아이템/위치 불일치
3. **무한 루프/자원 낭비** — 의미 없는 재시도, 비용 폭주
4. **사후 분석 불가** — 로깅 부재로 문제 원인 추적 불가

스타일, 이론적 엣지케이스, 이미 advisory-only인 항목은 제외.

---

## 수정 후보 총괄 매트릭스

| ID | Stage | 심각도 | 제목 | 핵심 위험 | 파일:라인 |
|----|-------|--------|------|----------|----------|
| **S0-1** | 0 | HIGH | DNA sync 실패 시 무언 계속 | 프로젝트 초기화 불완전 상태 전파 | stage01_helpers.py:260-297 |
| **S0-2** | 0 | HIGH | protagonist_config 저장 실패 시 소실 | POV/환생/세계관 설정 유실 | stage01_helpers.py:260-296 |
| **S1-1** | 1 | MEDIUM | JSON 직렬화 에러 미처리 | Stage 1 크래시, 어느 Arc인지 불명 | stage01_helpers.py:809 |
| **S1-2** | 1 | MEDIUM | context_accumulator 무한 성장 | 100+ 권 프로젝트에서 OOM | stage01_helpers.py:889-905 |
| **S2-1** | 2 | CRITICAL | attempt 카운터 이중 증가 | max_attempts 우회 → 무한 재시도 | stage2_orchestrator.py:790-796 |
| **S2-2** | 2 | CRITICAL | DB 커밋 실패 시 StateTracker 미롤백 | 고스트 Arc NPC 오염 | stage2_finalizer.py:1085-1122 |
| **S2-3** | 2 | HIGH | Early return에서 ep_start 누락 | 에피소드 번호 겹침/갭 | stage2_finalizer.py:914,1025,1037 |
| **S2-4** | 2 | HIGH | constraint_block 아크 간 오염 | Arc N 제약이 Arc N+1에 유출 | stage2_orchestrator.py:688-699,778 |
| **S2-5** | 2 | MEDIUM | FourPhase None 반환 시 피드백 없음 | 동일 입력으로 무의미 재시도 | stage2_orchestrator.py:649-654 |
| **S2-6** | 2 | MEDIUM | DraftValidator advisory 조기 반환 시 소실 | Python 감지 이슈 미전파 | stage2_validation_pipeline.py:92-93 |
| **S3-1** | 3 | HIGH | prev_blueprints 30개 절삭 | 50+ 화 연재 시 Arc 패턴 학습 단절 | stage3_orchestrator.py:1256 |
| **S3-2** | 3 | HIGH | prev_manuscripts_text 하드 절삭 | 의미 경계 무시 중간 절단 | stage3_orchestrator.py:1213-1226 |
| **S3-3** | 3 | MEDIUM | 4씬 미만 후보 전량 탈락 | 비정형 에피소드 Director 심사 불가 | blueprint_ensemble.py:385-414 |
| **S3-4** | 3 | MEDIUM | 연속성 검증이 best_blueprint만 대상 | 차선 후보의 연속성 우위 미감지 | three_phase_bp_generator.py:366-387 |
| **S3-5** | 3 | MEDIUM | 장르 필터 불완전 (비무협 internal_energy) | 투자/판타지에 무협 전용 필드 유출 | three_phase_bp_generator.py:106-115 |
| **S4-1** | 4 | CRITICAL | 에스컬레이션 후 연속성 재검증 부재 | 교체 BP가 인접 EP와 모순 가능 | stage4_orchestrator.py:1246-1296 |
| **S4-2** | 4 | HIGH | V75-B prev_blueprints=[] + prev_ms 미전달 | 콘텐츠 드리프트 | stage4_orchestrator.py:1374-1428 |
| **S4-3** | 4 | HIGH | state_updates Director 경계에서 부분 소실 | HUD 상태 변경 누락 | stage4_interview_round.py:3272 |
| **S4-4** | 4 | MEDIUM-HIGH | 연속성 체크 round_num==0에서만 실행 | 재시도 라운드 연속성 미검증 | stage4_interview_round.py:2862-2868 |
| **S4-5** | 4 | MEDIUM | PASS_WITH_FIX 빈 피드백 시 조기 종료 | 패치 미수행 → 무언 REJECT 전환 | stage4_interview_round.py:3011 |
| **S4-6** | 4 | MEDIUM | CoVe REJECT streak 카운터 우회 | 반복 CoVe 실패 시 에스컬레이션 불가 | stage4_orchestrator.py:1029,1055,1076 |
| **X-1** | Cross | CRITICAL | Stage 4 완료 후 StateTracker write-back 없음 | 30+ 화 누적 NPC 상태 탈동기 | main_a.py:4004-4077 |
| **X-2** | Cross | HIGH | WorldState/FactLedger save() 실패 무시 | 팩트 원장 조용히 부패 | fact_ledger.py:114-119, world_state.py:99-105 |
| **X-3** | Cross | HIGH | 크래시 후 Resume 시 부분 EP 데이터 | StateTracker 불일치 | db_manager.py:50-77 |
| **X-4** | Cross | MEDIUM | WorkGuard가 Stage 4에서만 실행 | Stage 2/3 통과 후 Stage 4 거부 → 낭비 | work_guard.py:794-829 |

---

## Stage 0/1 — 수정 후보 상세

### S0-1 — DNA sync 실패 시 무언 계속 `HIGH`

- **파일**: `modules/core/stage01_helpers.py:260-297`
- **현상**: `force_sync_v25_dna()`가 `dna_success=False`를 반환해도 Stage 0가 계속 진행. Bible은 로드되었으나 초기화 불완전한 상태로 Stage 1에 전달.
- **결과**: Stage 1에서 "plot_roadmap missing" 크립틱 에러.
- **수정**: `dna_success=False`일 때 early return + UI 에러 메시지.

### S0-2 — protagonist_config 저장 실패 시 소실 `HIGH`

- **파일**: `modules/core/stage01_helpers.py:260-296`
- **현상**: L251-256에서 사용자 POV/환생/세계관 선택을 수집하고, L263-271에서 Bible에 저장 시도. 저장 실패 시 `logging.warning`만 남기고 config 소실. 재시도/복구 없음.
- **결과**: 사용자의 캐릭터 설정이 조용히 소실. ChiefWriter가 기본 POV로 원고 생성.
- **수정**: 저장 실패 시 재시도 1회 + 실패 시 UI 경고 + 메모리에 fallback 유지.

### S1-1 — JSON 직렬화 에러 미처리 `MEDIUM`

- **파일**: `modules/core/stage01_helpers.py:809`
- **현상**: `json.dumps(vol_arcs_chunk)` — LLM 출력에 비직렬화 객체 포함 시 `TypeError` 미처리.
- **수정**: try/except + 문제 Arc 식별 로그.

### S1-2 — context_accumulator 무한 성장 `MEDIUM`

- **파일**: `modules/core/stage01_helpers.py:889-905`
- **현상**: `context_accumulator`가 vol 3까지 무제한 성장. 100+ 권 프로젝트에서 LLM 컨텍스트 오염.
- **수정**: 초기부터 슬라이딩 윈도우 적용 (최근 N권만 유지).

---

## Stage 2 — 수정 후보 상세

### S2-1 — attempt 카운터 이중 증가 `CRITICAL`

- **파일**: `modules/core/stage2_orchestrator.py:790-796`
- **현상**: `retry`/`next` 액션에서 `attempt += 1; continue` 후 루프 끝의 `attempt += 1`이 dead code이지만, 액션 분기 내에서도 이중 증가 패턴 존재. max_attempts=5일 때 실제 3회만 시도 후 종료될 수 있음.
- **수정**: 각 분기의 increment 로직 정리. `continue` 전 증가 → 루프 끝 증가 제거.

### S2-2 — DB 커밋 실패 시 StateTracker 미롤백 `CRITICAL`

- **파일**: `modules/core/stage2_finalizer.py:1085-1122`
- **현상**: `all_refined_arcs.append(refined_arc)` 성공 → DB 커밋 실패 → `all_refined_arcs.pop()` 제거. 그러나 StateTracker는 이미 이 Arc의 NPC/아이템/관계를 반영. `st_snapshot` 롤백(L1113-1121)은 부분 복원만.
- **결과**: "고스트 Arc" — DB에 없지만 StateTracker에 흔적이 남은 Arc. 다음 Arc 생성 시 사망 NPC 데이터 등 오염.
- **수정**: StateTracker 전체 스냅샷 저장/복원 또는 Arc 단위 트랜잭션 도입.

### S2-3 — Early return에서 ep_start 누락 `HIGH`

- **파일**: `modules/core/stage2_finalizer.py:914, 1025, 1037, 1122`
- **현상**: `run_finalize()` 조기 반환 시 `{"action": "retry", "current_feedback": ...}`만 반환. `current_ep_start`, `last_refined_context` 등 누락 → Orchestrator가 `.get()` fallback으로 **이전 값** 사용 → 에피소드 번호 겹침.
- **수정**: 조기 반환 dict에 필수 키 포함 보장. 공통 반환 헬퍼 함수.

### S2-4 — constraint_block 아크 간 오염 `HIGH`

- **파일**: `modules/core/stage2_orchestrator.py:688-699, 778`
- **현상**: `constraint_block`이 Arc N 생성 중 in-place 변경됨 (advisories 추가). `next` 액션 시 리셋 없이 Arc N+1에 전달 → "Arc 5는 아이템 X 금지" 제약이 Arc 6에도 적용.
- **수정**: `next` 액션 시 constraint_block 초기화. 또는 deepcopy 후 변경.

### S2-5 — FourPhase None 반환 시 피드백 없음 `MEDIUM`

- **파일**: `modules/core/stage2_orchestrator.py:649-654`
- **현상**: FourPhase가 None 반환 → `attempt += 1; continue`. 피드백/컨텍스트 업데이트 없음 → 다음 시도도 동일 입력으로 동일 실패 반복.
- **수정**: None 반환 시 "FourPhase 생성 실패" 피드백을 constraint_block에 추가.

### S2-6 — DraftValidator advisory 조기 반환 시 소실 `MEDIUM`

- **파일**: `modules/core/stage2_validation_pipeline.py:92-93`
- **현상**: 검증 파이프라인이 조기 반환되면 Python 감지 이슈(사망 NPC, 중복 아이템 등)가 소실. 다음 시도에 전파 안 됨.
- **수정**: advisory 수집을 조기 반환 전에 완료. 또는 반환값에 advisories 포함.

---

## Stage 3 — 수정 후보 상세

### S3-1 — prev_blueprints 30개 절삭 `HIGH`

- **파일**: `modules/core/stage3_orchestrator.py:1256`
- **현상**: `prev_blueprints[-30:]` — 50+ 화 연재 시 Arc 1 BP가 잘림. 더 심한 것: L993에서 work focus는 `prev_blueprints[-5:]`만 사용.
- **결과**: 장기 연재에서 초기 Arc 패턴 학습 불가. 플롯 반복 감지 실패.
- **수정**: 절삭 대신 요약 기반 압축. 또는 Gemini 대용량 컨텍스트 활용 (이미 코드 코멘트에 언급됨).

### S3-2 — prev_manuscripts_text 하드 절삭 `HIGH`

- **파일**: `modules/core/stage3_orchestrator.py:1213-1226`
- **현상**: `MAX_CONTEXT_CHARS` 초과 시 `[:MAX_CONTEXT_CHARS] + "... (절삭)"`. 의미 경계 무시, 에피소드 중간에서 자름.
- **결과**: 절삭된 에피소드의 후반부 이벤트(클라이맥스, 캐릭터 사망 등) 소실 → LLM이 해당 이벤트 모른 채 BP 생성.
- **수정**: 에피소드 단위 경계 기반 절삭. 최근 N개 에피소드 우선.

### S3-3 — 4씬 미만 후보 전량 탈락 `MEDIUM`

- **파일**: `modules/domain/agents/blueprint_ensemble.py:385-414`
- **현상**: 3개 전략 모두 4씬 미만 생성 시 `return None, []`. Director 심사 기회 없이 즉시 실패.
- **결과**: 짧은 에피소드(전환 화, 에필로그)에서 BP 생성 반복 실패.
- **수정**: 최소 기준 완화 (2씬) 또는 최고 품질 후보를 Director에게 위임.

### S3-4 — 연속성 검증이 best_blueprint만 대상 `MEDIUM`

- **파일**: `modules/domain/agents/three_phase_blueprint_generator.py:366-387`
- **현상**: `check_blueprint_continuity_with_cache(new_blueprint=best_blueprint)` — best만 검증. 차선 후보가 연속성 더 나을 수 있음.
- **수정**: 상위 2-3개 후보에 연속성 검증 적용 후 최종 선택.

### S3-5 — 장르 필터 불완전 `MEDIUM`

- **파일**: `modules/domain/agents/three_phase_blueprint_generator.py:106-115`
- **현상**: `_genre` 로드 실패 시 "wuxia" 기본값. 투자/판타지 프로젝트에서 `internal_energy: 100%` 등 무협 전용 필드가 constraint에 유출.
- **수정**: 장르 불일치 필드 명시적 strip. 또는 장르 로드 실패 시 에러.

---

## Stage 4 — 수정 후보 상세

### S4-1 — 에스컬레이션 후 연속성 재검증 부재 `CRITICAL`

- **파일**: `modules/core/stage4_orchestrator.py:1246-1296`
- **현상**: V75-D/V75-B 후 교체된 BP가 `check_blueprint_continuity_with_cache` 없이 바로 ChiefWriter에 전달. 정상 경로(Stage 3)에서는 실행되는 검증이 에스컬레이션 경로에서 건너뜀.
- **상세**: [stage4-escalation-bp-fix-deepdive-tf.md TF-E9] 참조.
- **수정**: 에스컬레이션 후 연속성 게이트 추가.

### S4-2 — V75-B 컨텍스트 부족 `HIGH`

- **파일**: `modules/core/stage4_orchestrator.py:1374-1428`
- **현상**: `prev_blueprints=[]`, `prev_manuscripts_text` 미전달. Arc 패턴 학습 없이 재생성.
- **상세**: [stage4-escalation-bp-fix-deepdive-tf.md TF-E10] 참조.
- **수정**: DB에서 최근 3개 EP BP + 직전 원고 복원.

### S4-3 — state_updates Director 경계 부분 소실 `HIGH`

- **파일**: `modules/core/stage4_interview_round.py:3272`
- **현상**: Director LLM 응답의 `state_updates`가 후보 원본보다 필드가 적을 때, `or` 체인으로 부분 dict만 채택. 후보의 풍부한 상태 변경(wealth, internal_energy 등)이 소실.
- **수정**: Director 응답과 후보 state_updates를 병합 (`{**candidate_su, **director_su}`).

### S4-4 — 연속성 체크 round_num==0에서만 실행 `MEDIUM-HIGH`

- **파일**: `modules/core/stage4_interview_round.py:2862-2868`
- **현상**: `_run_continuity = round_num == 0 and next_ep > 1`. Round 1+ 재시도에서 연속성 미검증 → Round 0에서 잡힌 위치/시간 불일치가 재시도에서 재발해도 미감지.
- **수정**: `round_num <= 1` 또는 매 라운드 실행 (비용 고려 시 짝수 라운드만).

### S4-5 — PASS_WITH_FIX 빈 피드백 조기 종료 `MEDIUM`

- **파일**: `modules/core/stage4_interview_round.py:3011`
- **현상**: `if not _current_fb: break` — Director가 PASS_WITH_FIX 판정했으나 피드백이 빈 문자열이면 패치 미수행 → 무언 REJECT 전환.
- **수정**: 빈 피드백 시 Director 재호출 또는 "general improvement" 디폴트 피드백.

### S4-6 — CoVe REJECT streak 우회 `MEDIUM`

- **파일**: `modules/core/stage4_orchestrator.py:1029, 1055, 1076`
- **현상**: CoVe REJECT → `continue` → streak 카운터 평가 건너뜀. 반복 CoVe 실패 시 에스컬레이션 영구 미발동.
- **상세**: [stage4-escalation-bp-fix-deepdive-tf.md TF-E7] 참조.
- **수정**: CoVe 전용 streak + 임계값 경고.

---

## Cross-Stage — 수정 후보 상세

### X-1 — Stage 4 완료 후 StateTracker write-back 없음 `CRITICAL`

- **파일**: `main_a.py:4004-4077`
- **현상**: Stage 4 실행 중 StateTracker가 원고 기반 NPC 사망/스킬/관계를 갱신. 그러나 Stage 4 종료 시 `self.state_tracker`에 write-back 없음 → Stage4Context와 함께 폐기.
- **대조**: Stage 2는 `self.state_tracker = _s2_ctx.state_tracker` (L3173)로 write-back 수행.
- **결과**: 30+ 화 연재 시 NPC 상태 누적 탈동기. 에피소드 50에서 사망한 NPC가 에피소드 150에서 재등장.
- **수정**: Stage 4 종료 시 `self.state_tracker = stage4_ctx.state_tracker` write-back 추가.

### X-2 — WorldState/FactLedger save() 실패 무시 `HIGH`

- **파일**: `modules/core/fact_ledger.py:114-119`, `modules/core/world_state.py:99-105`
- **현상**: `save()` 내 모든 예외를 `_logger.warning`으로 삼키고 계속 진행. DB 앵커 저장 실패해도 메모리에만 존재 → 다음 세션에서 소실.
- **결과**: 팩트 원장이 조용히 부패. 30+ 화 후 모순 감지 실패 급증.
- **수정**: 저장 실패 시 재시도 1회 + 실패 시 WARNING 레벨 상향 + 세션 종료 시 강제 flush.

### X-3 — 크래시 후 Resume 부분 EP 데이터 `HIGH`

- **파일**: `modules/core/db_manager.py:50-77`
- **현상**: Stage 4가 에피소드 단위로 DB 저장. 크래시 시 EP 15/20 저장 → 재시작 시 EP 16부터 시작하나 StateTracker는 EP 15 기준. EP 16-20의 중간 상태 변경 소실.
- **수정**: 에피소드 저장 시 StateTracker 스냅샷 동시 저장. Resume 시 마지막 스냅샷에서 복원.

### X-4 — WorkGuard Stage 4 전용 `MEDIUM`

- **파일**: `modules/core/genre_guards/work_guard.py:794-829`
- **현상**: `work_guard.yaml`의 금기어/규칙이 Stage 4 `run_deep_validation()`에서만 검증. Stage 2/3는 GenreGuard만 사용 → Stage 2/3 통과 후 Stage 4에서 거부 → LLM 비용 낭비.
- **수정**: Stage 2 Arc 검증에 WorkGuard 경량 체크 추가 (최소한 extra_forbidden_terms).

---

## 우선순위별 실행 계획

### P0 — 즉시 수정 (데이터 소실/무결성)

| ID | 작업 | 예상 규모 |
|----|------|----------|
| **X-1** | Stage 4 종료 시 StateTracker write-back | 5줄 |
| **S4-1** | 에스컬레이션 후 연속성 재검증 게이트 | 15줄 |
| **S2-2** | DB 커밋 실패 시 StateTracker 전체 롤백 | 20줄 |

### P1 — 단기 수정 (연속성/비용)

| ID | 작업 | 예상 규모 |
|----|------|----------|
| **S2-1** | attempt 카운터 이중 증가 정리 | 10줄 |
| **S2-3** | Early return 필수 키 보장 | 15줄 |
| **S2-4** | constraint_block 아크 간 리셋 | 5줄 |
| **S4-2** | V75-B prev_blueprints + prev_ms 복원 | 15줄 |
| **S4-3** | state_updates 병합 로직 수정 | 5줄 |
| **X-2** | WorldState/FactLedger save 재시도 + 경고 | 15줄 |

### P2 — 중기 수정 (품질/효율)

| ID | 작업 | 예상 규모 |
|----|------|----------|
| **S0-1** | DNA sync 실패 early return | 5줄 |
| **S0-2** | protagonist_config 저장 재시도 | 10줄 |
| **S3-1** | prev_blueprints 요약 기반 압축 | 30줄 |
| **S3-2** | prev_manuscripts_text 에피소드 경계 절삭 | 20줄 |
| **S4-4** | 연속성 체크 재시도 라운드 확대 | 5줄 |
| **S4-5** | PASS_WITH_FIX 빈 피드백 fallback | 5줄 |
| **S4-6** | CoVe 전용 streak 카운터 | 10줄 |
| **X-3** | Resume StateTracker 스냅샷 | 25줄 |
| **X-4** | WorkGuard Stage 2 경량 체크 | 15줄 |

### P3 — 추후 검토

| ID | 작업 |
|----|------|
| **S1-1** | JSON 직렬화 에러 처리 |
| **S1-2** | context_accumulator 윈도우 |
| **S2-5** | FourPhase None 피드백 |
| **S2-6** | DraftValidator advisory 보존 |
| **S3-3** | 4씬 최소 기준 완화 |
| **S3-4** | 연속성 검증 다후보 |
| **S3-5** | 장르 필터 완전성 |

---

## 스테이지별 건강도 요약

| Stage | CRITICAL | HIGH | MEDIUM | 핵심 약점 |
|-------|----------|------|--------|----------|
| 0/1 | 0 | 2 | 2 | 초기화 실패 무시, config 소실 |
| 2 | 2 | 2 | 2 | 재시도 로직 결함, 상태 롤백 미흡 |
| 3 | 0 | 2 | 3 | 장기 연재 컨텍스트 절삭, 후보 필터 과격 |
| 4 | 1 | 2 | 3 | 에스컬레이션 후 검증 갭, state_updates 소실 |
| Cross | 1 | 2 | 1 | StateTracker write-back 부재, 팩트 원장 부패 |
| **합계** | **4** | **10** | **11** | |

---

---

## [3PA] 3-Pass Audit 감리 결과 (2026-03-16)

| ID | 원래 심각도 | 판정 | 확신도 | 사유 |
|----|-----------|------|--------|------|
| **S0-1** | HIGH | **[3PA] CONFIRMED** | 97% | `dna_success=False` 시 else 분기 없음 확인. |
| **S0-2** | HIGH | **[3PA] RECLASSIFIED→MEDIUM** | 90% | L266에서 in-memory dict 변형이 save 전에 발생 → 현재 세션 내 config 생존. 크로스 세션 위험만 잔존. |
| **S1-1** | MEDIUM | **[3PA] RECLASSIFIED→LOW** | 90% | 데이터 소스가 JSON 원점이므로 비직렬화 객체 발생 확률 극히 낮음. |
| **S1-2** | MEDIUM | **[3PA] FALSE-POSITIVE** | 99% | L890-905에 `MAX_CONTEXT_VOLUMES=3` 슬라이딩 윈도우 이미 구현. "무한 성장" 주장 반박. |
| **S2-1** | CRITICAL | **[3PA] FALSE-POSITIVE** | 99% | 모든 코드 경로에서 `attempt += 1` 정확히 1회. L796은 도달 불가 dead code. |
| **S2-2** | CRITICAL | **[3PA] RECLASSIFIED→HIGH** | 90% | 롤백 코드가 L1112-1121에 구현됨. 잔여 위험은 얕은 복사에 의한 중첩 객체 미복원. |
| **S2-3** | HIGH | **[3PA] FALSE-POSITIVE** | 95% | Orchestrator `.get()` fallback이 이전 값 정확 보존. 조기 반환 시 ep_start 미변경이 정확한 동작. |
| **S2-4** | HIGH | **[3PA] FALSE-POSITIVE** | 95% | `[TF-47]` 수정의 `_base_constraint_block` 패턴 + Python 문자열 불변성으로 원본 미오염. |
| **S2-5** | MEDIUM | **[3PA] CONFIRMED** | 85% | FourPhase None 시 진단 피드백 없이 동일 입력 재시도. |
| **S2-6** | MEDIUM | **[3PA] INCONCLUSIVE** | 75% | B2 조기 반환 시 advisory 소실 확인. 실제 발생 빈도 런타임 검증 필요. |
| **S3-1** | HIGH | **[3PA] CONFIRMED** | 95% | `[-30:]` 절삭 확인. L993의 `[-5:]`는 더 공격적. |
| **S3-2** | HIGH | **[3PA] CONFIRMED** | 90% | 하드 절삭 확인. 단, 최근 EP 우선 로딩으로 영향은 가장 오래된 EP에 집중. |
| **S3-3** | MEDIUM | **[3PA] CONFIRMED** | 90% | 4씬+500자 필터 확인. 비정형 에피소드에서 영향. |
| **S3-4** | MEDIUM | **[3PA] RECLASSIFIED→LOW** | 90% | Director LLM이 전체 후보를 연속성 포함 종합 평가. 전용 검사는 게이트(거부/계속) 역할. |
| **S3-5** | MEDIUM | **[3PA] RECLASSIFIED→LOW** | 90% | 장르 fallback은 DB 접근 실패 시에만 발동. Stage 3 시점에서 bible은 이미 메모리 적재. |
| **S4-1** | CRITICAL | **[3PA] RECLASSIFIED→HIGH** | 90% | V75-B의 `generate()` 내부에 Phase 3 연속성 검사 포함. V75-D만 진정한 갭. |
| **S4-2** | HIGH | **[3PA] CONFIRMED** | 97% | `prev_blueprints=[]`, `prev_manuscripts_text` 미전달 확인. |
| **S4-3** | HIGH | **[3PA] CONFIRMED** | 85% | `or` 체인 우선순위 확인. Director LLM 행동에 따라 영향 변동. |
| **S4-4** | MEDIUM-HIGH | **[3PA] CONFIRMED** | 80% | `round_num==0` 조건 확인. Director 스코어링이 부분 보상. |
| **S4-5** | MEDIUM | **[3PA] CONFIRMED** | 90% | 빈 피드백 → REJECT 전환 확인. |
| **S4-6** | MEDIUM | **[3PA] CONFIRMED** | 95% | 3개 `continue`가 streak 카운터 평가를 건너뜀. |
| **X-1** | CRITICAL | **[3PA] RECLASSIFIED→MEDIUM-HIGH** | 85% | Python 참조 전달로 write-back 불필요. 실제 이슈는 StateTracker가 원고 결과를 미반영하는 별도 문제. |
| **X-2** | HIGH | **[3PA] CONFIRMED** | 95% | 두 save() 모두 예외 삼키고 계속 진행 확인. |
| **X-3** | HIGH | **[3PA] RECLASSIFIED→MEDIUM** | 80% | 인용 라인(L50-77)은 `__init__` 코드이며 resume 로직 아님. entity_registry는 매 에피소드 DB에서 재구축. |
| **X-4** | MEDIUM | **[3PA] RECLASSIFIED→LOW** | 85% | WorkGuard는 원고 텍스트 분석용으로 설계. Stage 2(Arc)/Stage 3(Blueprint)는 적합한 입력이 아님. |

**요약**: 25건 중 CONFIRMED 12건, FALSE-POSITIVE 4건, RECLASSIFIED 9건.

*3-Pass Audit by Claude Opus 4.6 — 2026-03-16*

### [3PA-R2] 대원칙 적용 재감리 (2026-03-16)

대원칙 4개를 감사 렌즈로 추가 적용한 결과, 본 SSOT에서 5건 판정 변경 + 5건 확신도 상향.

| ID | R1 판정 | R2 판정 | R2 확신도 | 대원칙 | 사유 |
|----|---------|---------|-----------|--------|------|
| **S2-6** | INCONCLUSIVE (75%) | **RECLASSIFIED→LOW** | 93% | #1 | valid arc 발견 시 advisory 스킵 = 의도적 최적화. Python 수집 최적화. |
| **S4-3** | CONFIRMED (85%) | **CONFIRMED** | **95%** | — | Director LLM 응답의 `or` 체인 우선순위 재확인. 기술적 데이터 손실은 대원칙 범위 외. |
| **S4-4** | CONFIRMED (80%) | **CLOSED** | 95% | #3 | `round_num==0` 제한 = Director가 매 라운드 판정. 중복 검사 스킵은 비용 최적화. |
| **X-1** | RECLASSIFIED→MH (85%) | **RECLASSIFIED→MH** | **92%** | — | Python 참조 전달 확인. 실제 이슈는 manuscript outcome 미반영 (별도 문제). NEEDS-RUNTIME-VERIFICATION. |
| **X-3** | RECLASSIFIED→M (80%) | **FALSE-POSITIVE** | **98%** | — | 인용 라인(L50-77)은 `__init__` 코드. resume 로직은 `main_a.py` orchestration 레벨에서 처리. entity_registry는 매 EP DB 재구축. |
| S2-5 | CONFIRMED (85%) | 유지 | **90%** | — | FourPhase None 시 피드백 부재 확인. 발생 빈도 런타임 검증 필요. NEEDS-RUNTIME-VERIFICATION. |

**R2 요약**: 25건 중 CONFIRMED 11건, FALSE-POSITIVE **5건**(+1), RECLASSIFIED 8건, CLOSED **1건**(+1).

*3-Pass Audit R2 (대원칙) by Claude Opus 4.6 — 2026-03-16*
