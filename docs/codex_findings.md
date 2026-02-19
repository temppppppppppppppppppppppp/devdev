# Codex Debug Sweep Findings

## 통계
- 총 발견: 5건 (CRITICAL: 0, HIGH: 2, MEDIUM: 3)
- 라운드 진행: 6/25

---

## Round 1 — modules/core/stage4_orchestrator.py

### 5-A. 파일 구조 요약
- `modules/core/stage4_orchestrator.py:214` `class Stage4Orchestrator` — Stage 4 원고 집필 오케스트레이션 진입점.
- `modules/core/stage4_orchestrator.py:221` `def __init__(self, app, *, context=None)` — app/context DI 및 lazy 구성요소 초기화.
- `modules/core/stage4_orchestrator.py:329` `def _run_interview_loop(self, session)` — 에피소드 단위 집필 루프, Blueprint/Arc 로드, 면담 루프 호출.
- `modules/core/stage4_orchestrator.py:567` `def _handle_round_outcome(self, *, round_ctx)` — 5회 면담 PASS/REJECT 수렴 처리.
- `modules/core/stage4_orchestrator.py:616` `def _prepare_stage4_session(self, *, limit_mode=False)` — 에이전트/검증기/스타일가이드/목표회차 세션 준비.
- `modules/core/stage4_orchestrator.py:787` `def stage_4_v2_chief_writer(self, limit_mode=False)` — Stage 4 공개 엔트리, 예외/중단 처리.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage4_orchestrator.py:351`  
> `max_loops = max(1, min((target_ep or total_planned_ep) - self.ctx.current_project.get_latest_episode_number() + 5, 100))`
>
> 실패 시나리오: `target_ep` 또는 `get_latest_episode_number()`가 비정상 타입이면 산술에서 `TypeError` 가능.
>
> 상류/하류 컨텍스트: 상류에서 `total_planned_ep`는 `modules/core/stage4_orchestrator.py:695`에서 DB 숫자값으로 로드되고, 하류에서 `next_ep`도 동일 소스(`modules/core/stage4_orchestrator.py:366`)로 비교에 사용됨(`modules/core/stage4_orchestrator.py:368`).
>
> **판정**: 안전(계약 기반) — 현재 코드 경로에선 DB 반환을 정수로 가정하는 계약과 `max(1, ...)` 하한 가드가 존재.

> **위험 지점 2**: `modules/core/stage4_orchestrator.py:432` ~ `modules/core/stage4_orchestrator.py:436`  
> `_ctx_prompts["reference_anchor_prompt"]` 등 딕셔너리 키 직접 인덱싱.
>
> 실패 시나리오: `build_mandatory_context()` 반환 키 누락 시 `KeyError`.
>
> 상류/하류 컨텍스트: 상류 함수에서 기본값을 먼저 초기화(`modules/core/stage4_context_builder.py:222`~`modules/core/stage4_context_builder.py:226`)하고, 반환 시 동일 5개 키를 항상 채워 반환(`modules/core/stage4_context_builder.py:518`~`modules/core/stage4_context_builder.py:523`).
>
> **판정**: 안전 — 현재 구현 계약상 키 누락 경로가 없다.

> **위험 지점 3**: `modules/core/stage4_orchestrator.py:544` ~ `modules/core/stage4_orchestrator.py:560`  
> PASS 후 `process_pass_result()` 실패 시 루프 제어.
>
> 실패 시나리오: 저장 실패 시 루프가 계속 돌면 중복 생성/상태 오염 가능.
>
> 상류/하류 컨텍스트: 실패 시 즉시 중단 로그 후 `break`(`modules/core/stage4_orchestrator.py:559`~`modules/core/stage4_orchestrator.py:560`), 루프 종료 후 공통 후처리 `run_post_episode_tasks()` 실행(`modules/core/stage4_orchestrator.py:563`).
>
> **판정**: 안전 — 저장 실패 시 재시도 루프가 아니라 종료 경로로 강제된다.

### 5-C. 발견된 버그
- 없음

---
## Round 1 완료

## Round 2 — modules/core/stage4_interview_round.py

### 5-A. 파일 구조 요약
- `modules/core/stage4_interview_round.py:8` `class Stage4InterviewRound` — 단일 면담 라운드 실행 모듈.
- `modules/core/stage4_interview_round.py:11` `def __init__(self, ctx)` — 컨텍스트 주입 및 시간선 경고 버퍼 초기화.
- `modules/core/stage4_interview_round.py:15` `def run(...)` — 후보 생성→Python 검증→Director 심사→PASS/REJECT 반환 전체 흐름.
- `modules/core/stage4_interview_round.py:65`~`modules/core/stage4_interview_round.py:207` `run()` 내부 후보 생성 블록 — patch/regenerate 분기 및 폴백 처리.
- `modules/core/stage4_interview_round.py:244`~`modules/core/stage4_interview_round.py:405` `run()` 내부 검증 블록 — manuscript/consistency/blocking/continuity 검증 병합.
- `modules/core/stage4_interview_round.py:626` `def _record_s4_attempt(...)` — PassRateMonitor 기록(비차단).

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage4_interview_round.py:104`  
> `_prev_score = int(previous_attempt.get("score", 0)) if previous_attempt else 0`
>
> 실패 시나리오: `score="N/A"` 같은 값이면 `ValueError` 가능.
>
> 상류/하류 컨텍스트: 바로 하류에서 예외를 흡수하고 0으로 보정(`modules/core/stage4_interview_round.py:105`~`modules/core/stage4_interview_round.py:106`), 이후 patch 모드 판단에 보정값 사용(`modules/core/stage4_interview_round.py:108`).
>
> **판정**: 안전 — 타입 불일치가 런타임 크래시로 전파되지 않음.

> **위험 지점 2**: `modules/core/stage4_interview_round.py:249`  
> `_recent_ms = self.ctx.current_project.db.get_recent_manuscripts(before_ep=next_ep, limit=5)`
>
> 실패 시나리오: DB 오류/스키마 오류 시 검증 입력 누락.
>
> 상류/하류 컨텍스트: 예외를 잡아 경고 후 빈 리스트 유지(`modules/core/stage4_interview_round.py:250`~`modules/core/stage4_interview_round.py:254`), 하류 `validate_all_candidates(..., recent_manuscripts=_recent_ms)` 호출 시 타입(list)은 유지(`modules/core/stage4_interview_round.py:255`~`modules/core/stage4_interview_round.py:260`).
>
> **판정**: 안전(정책성) — 검증 약화는 있으나 비차단 설계이며 즉시 크래시 경로는 아니다.

> **위험 지점 3**: `modules/core/stage4_interview_round.py:605`  
> `"best_manuscript": director_result.get("selected_candidate", {}).get("manuscript", ""),`
>
> 실패 시나리오: `selected_candidate`가 dict가 아니면 `.get()`에서 `AttributeError`.
>
> 상류/하류 컨텍스트: Director 선택 결과 생성부는 `selected_candidate`를 후보 dict 또는 `{}`로 구성(`modules/domain/agents/director_ensemble.py:364`, `modules/domain/agents/director_ensemble.py:395`, `modules/domain/agents/director_ensemble.py:456`). 동일 함수 내 다른 경로에서도 dict 정규화 방어 존재(`modules/core/stage4_interview_round.py:535`~`modules/core/stage4_interview_round.py:537`).
>
> **판정**: 안전(계약 의존) — 현재 계약 하에서는 안전하지만, Director 반환 스키마 변경 시 취약해질 수 있는 결합 지점.

### 5-C. 발견된 버그
- 없음

---
## Round 2 완료

## Round 3 — modules/core/stage4_context_builder.py + modules/core/stage4_post_processor.py

### 5-A. 파일 구조 요약
- `modules/core/stage4_context_builder.py:20` `class Stage4ContextBuilder` — Stage 4 컨텍스트 수집/주입 전담.
- `modules/core/stage4_context_builder.py:26` `def load_chain_link_section(self, next_ep)` — 직전 화 `chain_link`를 프롬프트 텍스트로 변환.
- `modules/core/stage4_context_builder.py:63` `def build_extended_lookback_digest(self, next_ep)` — 최근 10화 발췌 요약 구성.
- `modules/core/stage4_context_builder.py:112` `def prepare_episode_context(self, next_ep, arc_data, chief_writer)` — 에피소드 단위 입력 컨텍스트 집계.
- `modules/core/stage4_context_builder.py:204` `def build_mandatory_context(...)` — state/fact/memory/guard를 합쳐 mandatory context 생성.
- `modules/core/stage4_context_builder.py:524` `def build_round_context(...)` — `_RoundContext` 객체 생성.
- `modules/core/stage4_post_processor.py:14` `class Stage4PostProcessor` — PASS 후 저장/후처리 전담.
- `modules/core/stage4_post_processor.py:20` `def process_pass_result(...)` — DB 저장, HUD 반영, bible/world/fact/log 업데이트.
- `modules/core/stage4_post_processor.py:557` `def run_post_episode_tasks(self)` — 세션 종료 후 sync/요약 처리.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage4_post_processor.py:40`  
> `self.ctx.current_project.db.save_manuscript(...)` 후 같은 블록에서 `modules/core/stage4_post_processor.py:43` `update_martial_tracker(...)`, `modules/core/stage4_post_processor.py:46` `commit()` 수행.
>
> 실패 시나리오: `update_martial_tracker()`에서 예외가 나면(`martial_data` 타입/값 이상), `modules/core/stage4_post_processor.py:48`~`modules/core/stage4_post_processor.py:50`에서 `False` 반환만 하고 rollback이 없다.  
> 이후 DB close 시 `modules/core/db_manager.py:376`~`modules/core/db_manager.py:377`가 열린 트랜잭션을 commit해 `save_manuscript()` 결과만 늦게 반영될 수 있다.
>
> 상류/하류 컨텍스트: 상류에서 `save_manuscript()`는 즉시 커밋 보장 함수가 아니고(`modules/core/db_manager.py:401`~`modules/core/db_manager.py:408`), 하류 오케스트레이터는 이 경로를 “DB 저장 실패로 중단”으로 해석한다(`modules/core/stage4_orchestrator.py:545`~`modules/core/stage4_orchestrator.py:560`).
>
> **판정**: BUG (HIGH) — 실패 경로에서 원자성 보장이 깨질 수 있다.

> **위험 지점 2**: `modules/core/stage4_context_builder.py:114`  
> `arc_pos = next_ep - arc_data.get("ep_start", next_ep) + 1`
>
> 실패 시나리오: `ep_start`가 문자열이면 산술 `TypeError`.
>
> 상류/하류 컨텍스트: 호출 상류가 이미 `modules/core/stage4_orchestrator.py:383`에서 `a.get("ep_start", 0) <= next_ep <= a.get("ep_end", 0)` 비교를 수행해 숫자형 계약에 의존한다. 하류에서는 `arc_pos`가 `_RoundContext`에 그대로 주입된다(`modules/core/stage4_context_builder.py:558`).
>
> **판정**: 안전(상류 계약 의존) — 이 파일 단독 버그라기보다 입력 계약 위반 시 상류에서 먼저 깨지는 결합 지점.

> **위험 지점 3**: `modules/core/stage4_context_builder.py:579`  
> `reference_anchor_prompt=ctx_prompts["reference_anchor_prompt"]` (딕셔너리 키 직접 인덱싱)
>
> 실패 시나리오: `ctx_prompts` 키 누락 시 `KeyError`.
>
> 상류/하류 컨텍스트: `build_mandatory_context()`는 writer 유무와 무관하게 동일 키셋을 반환한다(`modules/core/stage4_context_builder.py:220`~`modules/core/stage4_context_builder.py:224`, `modules/core/stage4_context_builder.py:516`~`modules/core/stage4_context_builder.py:522`). 오케스트레이터도 해당 반환값을 그대로 전달한다(`modules/core/stage4_orchestrator.py:419`~`modules/core/stage4_orchestrator.py:427`, `modules/core/stage4_orchestrator.py:513`~`modules/core/stage4_orchestrator.py:516`).
>
> **판정**: 안전 — 현재 구현 계약상 키 누락 경로가 없다.

### 5-C. 발견된 버그

### [HIGH] modules/core/stage4_post_processor.py:40 — DB 실패 경로에서 부분 저장(commit 지연) 가능

**문제**: `save_manuscript()` 이후 `update_martial_tracker()`가 실패하면 rollback 없이 `False` 반환한다. 연결 종료 시 열린 트랜잭션이 commit되어 원래 실패 처리한 원고가 반영될 수 있다.

**문제 코드**:
```python
# modules/core/stage4_post_processor.py
self.ctx.current_project.db.save_manuscript(...)
if final_state_updates:
    self.ctx.current_project.db.update_martial_tracker(...)
self.ctx.current_project.db.conn.commit()
...
except Exception:
    return False

# modules/core/db_manager.py
def close(self):
    if self.conn.in_transaction:
        self.conn.commit()
```

**수정 제안**:
```python
try:
    ...
    self.ctx.current_project.db.conn.commit()
except Exception:
    try:
        self.ctx.current_project.db.conn.rollback()
    except Exception:
        pass
    return False
```

**확신도**: HIGH
**FP 체크**: FP-1(비차단 갱신) 아님. 해당 블록은 함수 주석상 “DB save failure 시 False 반환”을 약속하는 핵심 저장 경로.

---
## Round 3 완료

## Round 4 — modules/domain/agents/chief_writer.py + modules/domain/agents/chief_writer_quality.py

### 5-A. 파일 구조 요약
- `modules/domain/agents/chief_writer.py:34` `class ChiefWriter(BaseAgent)` — Stage 4 원고 후보 생성 주 에이전트.
- `modules/domain/agents/chief_writer.py:114` `def generate_ensemble(...)` — 3전략 병렬 생성 + 실패 대체 + 후보 검증.
- `modules/domain/agents/chief_writer.py:361` `def _generate_single_candidate(...)` — 단일 후보 생성, JSON 파싱, self-critique 적용.
- `modules/domain/agents/chief_writer.py:512` `def regenerate_with_feedback(...)` — Director 피드백 반영 재생성.
- `modules/domain/agents/chief_writer.py:630` `def patch_with_feedback(...)` — 원본 보존 patch 모드 생성.
- `modules/domain/agents/chief_writer.py:779` `def _prefetch_manuscripts(...)` — 최근 원고 캐시 구성.
- `modules/domain/agents/chief_writer_quality.py:12` `class ChiefWriterQualityGate` — quality/self-critique 게이트.
- `modules/domain/agents/chief_writer_quality.py:67` `def apply_self_critique(...)` — 최대 3라운드 자체 점검/수정.
- `modules/domain/agents/chief_writer_quality.py:279` `def _check_npc_relationship(...)` — NPC 관계 일관성 검사.
- `modules/domain/agents/chief_writer_quality.py:315` `def _fix_manuscript_issues(...)` — 이슈 수정 프롬프트 수행.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/chief_writer_quality.py:301`  
> `context_pattern = f"{name}.*{kw}|{kw}.*{name}"` 후 `modules/domain/agents/chief_writer_quality.py:302`에서 `re.search(...)` 수행.
>
> 실패 시나리오: NPC 이름에 정규식 메타문자(`[` 등)가 포함되면 `re.error` 발생.
>
> 상류/하류 컨텍스트: 상류에서 `name`은 외부 데이터(`encyclopedia["npcs"]`)를 그대로 사용하며 escape가 없다(`modules/domain/agents/chief_writer_quality.py:289`~`modules/domain/agents/chief_writer_quality.py:301`). 하류로는 예외가 전파되어 self-critique 라운드가 끊기고, `_generate_single_candidate()` 외곽 예외 처리로 후보 자체가 `None`으로 소거될 수 있다(`modules/domain/agents/chief_writer.py:484`~`modules/domain/agents/chief_writer.py:490`).
>
> 재현 근거(로컬 실행): `name='['`, `content='무시['`, `relationship_state='경외'` 입력 시 `unterminated character set` 예외 발생.
>
> **판정**: BUG (MEDIUM)

> **위험 지점 2**: `modules/domain/agents/chief_writer.py:461`~`modules/domain/agents/chief_writer.py:463`  
> `final_content = critiqued_data.get("content") or manuscript_content`  
> `final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))`
>
> 실패 시나리오: self-critique 결과 JSON에서 `content`가 dict/list, `state_updates`가 list/string이면 타입이 정규화되지 않은 채 후보로 반환됨.
>
> 상류/하류 컨텍스트: 상류에서 타입 강제 로직이 해당 구간 뒤에 없다(`modules/domain/agents/chief_writer.py:469`~`modules/domain/agents/chief_writer.py:475`). 하류 검증 호출은 `validate_manuscript_candidate()`인데, 검증 실패 시 원본을 그대로 통과시키므로 보호막이 아님(`modules/domain/agents/chief_writer.py:357`, `modules/models/manuscript.py:43`~`modules/models/manuscript.py:50`).
>
> 재현 근거(로컬 실행):  
> 1) `validate_manuscript_candidate({"state_updates":[1,2,3]})` 결과가 list 그대로 유지됨.  
> 2) `validate_manuscript_candidate({"manuscript":{"text":"x"}})` 결과가 dict 그대로 유지됨.  
> 3) 이 값이 Director 단계의 `c.get("manuscript", "")[:12000]`에 들어가면 `TypeError` 가능(`modules/domain/agents/director_ensemble.py:328`).
>
> **판정**: BUG (HIGH)

> **위험 지점 3**: `modules/domain/agents/chief_writer.py:323`~`modules/domain/agents/chief_writer.py:354`  
> 병렬 생성 실패 시 후보가 비어도 에러 후보를 강제로 1개 구성.
>
> 실패 시나리오: 모든 worker 실패로 후보 0건.
>
> 상류/하류 컨텍스트: 상류에서 `valid_candidates`가 비어 있으면 fallback 단일 생성을 재시도(`modules/domain/agents/chief_writer.py:324`~`modules/domain/agents/chief_writer.py:337`), 그마저 실패하면 에러 후보를 만들어 빈 리스트를 방지한다(`modules/domain/agents/chief_writer.py:341`~`modules/domain/agents/chief_writer.py:354`).
>
> **판정**: 안전 — 완전 빈 후보 배열로 인한 즉시 IndexError 경로는 차단되어 있다.

### 5-C. 발견된 버그

### [MEDIUM] modules/domain/agents/chief_writer_quality.py:301 — NPC 이름 regex 미이스케이프로 `re.error` 가능

**문제**: 관계 검증 시 NPC 이름을 regex 패턴에 그대로 삽입해 메타문자 포함 이름에서 예외가 발생한다.

**문제 코드**:
```python
context_pattern = f"{name}.*{kw}|{kw}.*{name}"
if re.search(context_pattern, content):
    ...
```

**수정 제안**:
```python
safe_name = re.escape(name)
safe_kw = re.escape(kw)
context_pattern = f"{safe_name}.*{safe_kw}|{safe_kw}.*{safe_name}"
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 설계 의도 여부와 무관하게 런타임 예외 재현 가능.

### [HIGH] modules/domain/agents/chief_writer.py:461 — self-critique 결과 타입 미정규화 + fail-open 검증으로 하류 크래시 전파

**문제**: self-critique 결과의 `content`/`state_updates` 타입을 보정하지 않고 반환하며, 검증 실패 시 원본 유지 정책 때문에 비정상 타입이 그대로 하류로 전달된다.

**문제 코드**:
```python
# modules/domain/agents/chief_writer.py
final_content = critiqued_data.get("content") or manuscript_content
final_state = critiqued_data.get("state_updates", data.get("state_updates", {}))
...
candidates = [validate_manuscript_candidate(c) for c in candidates]

# modules/models/manuscript.py
except Exception:
    return raw
```

**수정 제안**:
```python
if not isinstance(final_content, str):
    final_content = str(final_content) if final_content is not None else ""
if not isinstance(final_state, dict):
    final_state = {}
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 로컬 재현(검증 실패 후 원본 통과)과 하류 계약 충돌 근거가 모두 확인됨.

---
## Round 4 완료

## Round 5 — modules/domain/agents/chief_writer_context.py

### 5-A. 파일 구조 요약
- `modules/domain/agents/chief_writer_context.py:31` `class ChiefWriterContextBuilder` — ChiefWriter용 컨텍스트 조립/보조 분석 모듈.
- `modules/domain/agents/chief_writer_context.py:41` `def build_common_context(...)` — Stage 4 집필용 메인 컨텍스트 문자열 생성.
- `modules/domain/agents/chief_writer_context.py:332` `def _generate_episode_digest(...)` — 이전 화 핵심 상태를 정규식 기반으로 요약.
- `modules/domain/agents/chief_writer_context.py:552` `def _build_past_guard_section(...)` — 과거 침범 방지 섹션 조립.
- `modules/domain/agents/chief_writer_context.py:594` `def _build_future_guard_section(...)` — 미래 침범 방지 섹션 조립.
- `modules/domain/agents/chief_writer_context.py:690` `def _check_hud_anomalies(...)` — HUD 급변 감지 및 경고 텍스트 생성.
- `modules/domain/agents/chief_writer_context.py:836` `def _get_npc_frequency(...)` — 최근 화별 NPC 등장 빈도 집계.
- `modules/domain/agents/chief_writer_context.py:899` `def _get_dna_instruction(...)` — 1화/연속 집필 DNA 지시문 분기.
- `modules/domain/agents/chief_writer_context.py:969` `def _extract_recent_events(...)` — 최근 state_log 이벤트 추출.
- `modules/domain/agents/chief_writer_context.py:1028` `def _build_justification_guidance(...)` — HUD 제약 기반 정당화 가이드 생성.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/chief_writer_context.py:698`  
> `hud_snapshot = cached.get("hud_snapshot", {})` 기반으로만 HUD anomaly를 계산하고, 데이터가 없으면 즉시 빈 결과 반환(`modules/domain/agents/chief_writer_context.py:703`~`modules/domain/agents/chief_writer_context.py:704`).
>
> 실패 시나리오: HUD 급변이 실제로 있어도 anomaly 경고가 영구적으로 비활성화될 수 있음.
>
> 상류/하류 컨텍스트: 상류 캐시 적재부에서 `hud_snapshot`은 `manuscripts` 테이블에 컬럼이 없어 항상 `{}`가 된다고 명시돼 있음(`modules/domain/agents/chief_writer.py:799`~`modules/domain/agents/chief_writer.py:801`). 실제 스키마도 `manuscripts`는 `ep_num/title/content/created_at`만 보유(`modules/core/db_manager.py:153`~`modules/core/db_manager.py:158`).
>
> **판정**: BUG (MEDIUM) — 기능이 존재하지만 정상 경로에서 사실상 동작하지 않는 로직 공백.

> **위험 지점 2**: `modules/domain/agents/chief_writer_context.py:892`  
> `if int(ep_num) == 1:`
>
> 실패 시나리오: `ep_num`이 숫자 변환 불가 값이면 `ValueError`.
>
> 상류/하류 컨텍스트: 상류는 오케스트레이터에서 `next_ep` 정수 값을 전달(`modules/core/stage4_orchestrator.py:366`), `build_common_context()`도 동일 `ep_num`을 그대로 전달(`modules/domain/agents/chief_writer_context.py:263`).
>
> **판정**: 안전(입력 계약 의존) — 현재 호출 경로에선 정수 계약이 유지됨.

> **위험 지점 3**: `modules/domain/agents/chief_writer_context.py:14`~`modules/domain/agents/chief_writer_context.py:19`  
> `primitive_guard` import 실패 시 fallback 플래그로 분기.
>
> 실패 시나리오: 환경에 `primitive_guard`가 없으면 제약 섹션 누락 가능.
>
> 상류/하류 컨텍스트: 하류 분기에서 fallback 텍스트를 주입해 빈 섹션을 방지(`modules/domain/agents/chief_writer_context.py:153`~`modules/domain/agents/chief_writer_context.py:163`).
>
> **판정**: 안전 — graceful degradation 경로가 명시되어 있음.

### 5-C. 발견된 버그

### [MEDIUM] modules/domain/agents/chief_writer_context.py:698 — HUD anomaly 감지가 실질적으로 비활성화됨

**문제**: `_check_hud_anomalies()`는 `hud_snapshot` 캐시만 신뢰하지만, 캐시 생성부에서 해당 값이 항상 빈 dict가 되는 경로가 고정되어 있어 anomaly가 거의 영원히 감지되지 않는다.

**문제 코드**:
```python
# modules/domain/agents/chief_writer_context.py
cached = self.host._get_cached_manuscript(ep)
hud_snapshot = cached.get("hud_snapshot", {})
if not hud_history:
    return {"has_anomalies": False, ...}

# modules/domain/agents/chief_writer.py
# manuscripts 테이블에 hud_snapshot 컬럼 없음 -> 항상 {}
hud_snapshot = past_ms.get("hud_snapshot", {})
```

**수정 제안**:
```python
# 1) _prefetch_manuscripts에서 state_logs/martial_tracker 기반으로 hud_snapshot 구성
# 2) _check_hud_anomalies에서 hud_snapshot 부재 시 DB fallback 조회 추가
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 코드 주석/스키마/호출 흐름이 모두 동일 결론을 지지.

---
## Round 5 완료

## Round 6 — modules/core/stage4_context.py + modules/core/pass_rate_monitor.py

### 5-A. 파일 구조 요약
- `modules/core/stage4_context.py:4` `class Stage4Context` — Stage 4 DI 컨테이너.
- `modules/core/stage4_context.py:48` `def __init__(...)` — 필수/옵션 의존성 주입.
- `modules/core/stage4_context.py:106` `@classmethod from_app(...)` — `SovereignApp`로부터 컨텍스트 생성.
- `modules/core/pass_rate_monitor.py:66` `class PassRateMonitor` — Stage별 pass-rate 기록/분석.
- `modules/core/pass_rate_monitor.py:83` `def _load_records(...)` — JSON 로그 로드.
- `modules/core/pass_rate_monitor.py:97` `def _save_records(...)` — 로그 스냅샷 저장.
- `modules/core/pass_rate_monitor.py:120` `def record_attempt(...)` — 시도 1건 기록.
- `modules/core/pass_rate_monitor.py:176` `def get_stage_stats(...)` — Stage 통계 계산.
- `modules/core/pass_rate_monitor.py:321` `def get_summary(...)` — 요약 리포트 생성.
- `modules/core/pass_rate_monitor.py:535` `def get_monitor(...)` — 싱글턴 모니터 반환.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/pass_rate_monitor.py:91`  
> `AttemptRecord(**{...})` list comprehension 중 단일 레코드라도 필수 필드 누락이면 예외가 발생하고, 외곽 `except`에서 전체 `records`를 빈 리스트로 초기화(`modules/core/pass_rate_monitor.py:93`~`modules/core/pass_rate_monitor.py:95`).
>
> 실패 시나리오: 로그 파일 내 일부 레코드만 손상되어도 전체 과거 통계가 0건으로 날아감.
>
> 상류/하류 컨텍스트: 상류는 기존 JSON 전체를 그대로 읽고(`modules/core/pass_rate_monitor.py:88`), 하류는 실패 시 부분 복구 없이 전량 폐기한다(`modules/core/pass_rate_monitor.py:93`~`modules/core/pass_rate_monitor.py:95`).
>
> 재현 근거(로컬 실행): 필수 필드 누락 레코드 1건 포함한 JSON 로드 시 `loaded 0` 확인.
>
> **판정**: BUG (MEDIUM)

> **위험 지점 2**: `modules/core/stage4_context.py:70`~`modules/core/stage4_context.py:77`  
> 콜백 의존성(`flush_audit_buffer`, `safe_commit` 등)이 optional `None` 허용.
>
> 실패 시나리오: 호출부가 `None` 가드 없이 직접 호출하면 `TypeError`.
>
> 상류/하류 컨텍스트: `from_app()`는 해당 콜백을 `getattr(..., None)`으로 주입(`modules/core/stage4_context.py:132`~`modules/core/stage4_context.py:133`). 현재 주 애플리케이션은 콜백을 보유하지만, 재사용 환경에서는 계약이 깨질 수 있다.
>
> **판정**: 안전(환경 계약 의존) — 현 프로젝트 실행 경로에선 콜백이 존재.

> **위험 지점 3**: `modules/core/pass_rate_monitor.py:101`  
> 저장 시 `self.records[-1000:]`만 snapshot으로 저장하고, 로드 시 이 snapshot만 복원(`modules/core/pass_rate_monitor.py:91`).
>
> 실패 시나리오: 장기 운영 데이터가 재시작 이후 1000건으로 축소되어 추세 분석 왜곡 가능.
>
> 상류/하류 컨텍스트: 저장 파일에는 `total_records`를 기록하지만(`modules/core/pass_rate_monitor.py:110`) 로드시 이를 복원에 활용하지 않는다.
>
> **판정**: RISK (Design Check Needed) — 의도적 제한일 수 있으나 장기 통계 정확도와 트레이드오프.

### 5-C. 발견된 버그

### [MEDIUM] modules/core/pass_rate_monitor.py:91 — 부분 손상 로그 1건으로 전체 기록 로드 실패

**문제**: 레코드 단위 복구 없이 전체 list comprehension을 한 번에 생성해, 단일 불량 레코드가 전체 로드를 실패시킨다.

**문제 코드**:
```python
self.records = [
    AttemptRecord(**{k: v for k, v in r.items() if k in fields})
    for r in data.get("records", [])
]
...
except Exception:
    self.records = []
```

**수정 제안**:
```python
records = []
for r in data.get("records", []):
    try:
        records.append(AttemptRecord(**{k: v for k, v in r.items() if k in fields}))
    except Exception:
        continue  # 불량 레코드만 스킵
self.records = records
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 로컬 재현으로 “부분 손상 -> 전체 0건” 확인 완료.

---
## Round 6 완료

## Round 7 — modules/core/stage2_orchestrator.py

### 진행 통계 업데이트
- 총 발견: 5건 (CRITICAL: 0, HIGH: 2, MEDIUM: 3)
- 라운드 진행: 7/40

### 5-A. 파일 구조 요약
- `modules/core/stage2_orchestrator.py:19` `class Stage2Orchestrator` — Stage 2 전체 오케스트레이션.
- `modules/core/stage2_orchestrator.py:61` `def preflight(self)` — preflight 모듈 lazy 접근.
- `modules/core/stage2_orchestrator.py:70` `def finalizer(self)` — finalizer 모듈 lazy 접근.
- `modules/core/stage2_orchestrator.py:756` `def _preflight_state_setup(...)` — preflight 위임.
- `modules/core/stage2_orchestrator.py:801` `def _stage2_flow_guard(...)` — flow guard 위임.
- `modules/core/stage2_orchestrator.py:805` `def _stage2_flow_guard_legacy(...)` — 레거시 flow guard.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage2_orchestrator.py:554` `if _fin["action"] != "break" ...`  
> 실패 시나리오: finalizer 반환 dict에 `action` 키가 없으면 `KeyError`.  
> 상류/하류 컨텍스트: 상류 finalizer는 실패시에도 `{"action": "retry", ...}`를 반환(`modules/core/stage2_finalizer.py:304`), 하류 분기 역시 `"retry"/"next"/"break"`만 소비(`modules/core/stage2_orchestrator.py:563-580`).  
> **판정**: 안전(반환 계약 의존).

> **위험 지점 2**: `modules/core/stage2_orchestrator.py:311` `_success_indices = sorted(set(range(...)) - set(failed_indices))`  
> 실패 시나리오: `failed_indices`가 비-list면 `TypeError`.  
> 상류/하류 컨텍스트: 상류에서 recovery map 경로는 실패 인덱스 수집 이후에만 진입(`modules/core/stage2_orchestrator.py:288-304`), 하류는 복원 실패 시 해당 arc를 skip(`modules/core/stage2_orchestrator.py:321-324`).  
> **판정**: 안전(현재 흐름상 list 계약 유지).

> **위험 지점 3**: `modules/core/stage2_orchestrator.py:568-573` state_extractor 캐시 무효화 실패  
> 실패 시나리오: 캐시 invalidate 실패 시 stale state 재사용 가능성.  
> 상류/하류 컨텍스트: 예외를 잡고 경고로 강등(`modules/core/stage2_orchestrator.py:572-577`), 하류는 재시도 루프를 계속 수행(`modules/core/stage2_orchestrator.py:578-583`).  
> **판정**: RISK (Design Check Needed) — fail-open 설계.

### 5-C. 발견된 버그
- 없음

---
## Round 7 완료

## Round 8 — modules/core/stage2_preflight.py + modules/core/stage2_validation_pipeline.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 3, MEDIUM: 3)
- 라운드 진행: 8/40

### 5-A. 파일 구조 요약
- `modules/core/stage2_preflight.py:7` `class Stage2PreflightAnalysis` — Stage 2 preflight 분석기.
- `modules/core/stage2_preflight.py:17` `def _preflight_state_setup(...)` — arc_drive + preflight 병렬 계산.
- `modules/core/stage2_preflight.py:195` `def _preflight_arc_analysis(...)` — 제약 분석.
- `modules/core/stage2_preflight.py:417` `def _preflight_enrichment(...)` — FourPhase 생성 시도.
- `modules/core/stage2_validation_pipeline.py:13` `class Stage2ValidationPipeline` — draft/scoring/consensus 파이프라인.
- `modules/core/stage2_validation_pipeline.py:23` `def run_validation(...)` — Stage2 검증 통합 실행.
- `modules/core/stage2_validation_pipeline.py:597` `def _stage2_flow_guard(...)` — beat/flow 검증.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage2_validation_pipeline.py:604-606`  
> `ep_count = refined_arc.get("ep_count", 0)` + `max(3, ep_count)`  
> 실패 시나리오: `ep_count`가 `"5"` 같은 문자열이면 `TypeError`로 검증기 즉시 크래시.  
> 상류/하류 컨텍스트: 상류 Arc 응답은 LLM 파싱 결과를 그대로 포함할 수 있고(`modules/domain/agents/analyst.py:1039-1097`), 하류 `_extract_beat_text` 가드(`modules/core/stage2_validation_pipeline.py:614`)보다 먼저 산술이 실행된다.  
> **판정**: BUG.

> **위험 지점 2**: `modules/core/stage2_preflight.py:100-109` 병렬 future timeout/예외 시 강제 fallback  
> 실패 시나리오: preflight 결과가 항상 빈 값으로 떨어져 제약 품질 저하.  
> 상류/하류 컨텍스트: 예외 시 `arc_drive={}`, `_cached_preflight_result={}`로 대체(`modules/core/stage2_preflight.py:107-109`), 하류는 빈 상태로 생성 계속 진행(`modules/core/stage2_preflight.py:122-126`).  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/stage2_preflight.py:74-87` preflight analyze 예외 비차단  
> 실패 시나리오: preflight 분석 실패가 경고만 남고 본 파이프라인 계속 진행.  
> 상류/하류 컨텍스트: `except Exception as pf_err`에서 warning 후 return(`modules/core/stage2_preflight.py:85-87`), 하류는 `_pf_injection` 없는 기본 흐름으로 진행(`modules/core/stage2_preflight.py:87`).  
> **판정**: 안전(의도된 비차단 경로, FP-1 맥락).

### 5-C. 발견된 버그

### [HIGH][B-06] modules/core/stage2_validation_pipeline.py:606 — `ep_count` 문자열에서 `TypeError`

**문제**: `max(3, ep_count)`에서 `ep_count`가 문자열이면 비교 연산이 실패해 Stage2 검증이 중단된다.

**문제 코드**:
```python
ep_count = refined_arc.get("ep_count", 0)
if not isinstance(beats, list) or len(beats) < max(3, ep_count):
    ...
```

**수정 제안**:
```python
raw_ep_count = refined_arc.get("ep_count", 0)
try:
    ep_count = int(raw_ep_count)
except (TypeError, ValueError):
    ep_count = 0
if not isinstance(beats, list) or len(beats) < max(3, ep_count):
    ...
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현 근거(실행), 계약 위반 근거(숫자 비교 전 형 변환 부재) 충족.

---
## Round 8 완료

## Round 9 — modules/core/stage2_finalizer.py

### 진행 통계 업데이트
- 총 발견: 6건 (CRITICAL: 0, HIGH: 3, MEDIUM: 3)
- 라운드 진행: 9/40

### 5-A. 파일 구조 요약
- `modules/core/stage2_finalizer.py:10` `class Stage2Finalizer` — Stage2 PASS/REJECT 후처리.
- `modules/core/stage2_finalizer.py:17` `def ctx(self)` — host context accessor.
- `modules/core/stage2_finalizer.py:493` `def _record_s2_pass_metrics(...)` — PASS 메트릭 저장.
- `modules/core/stage2_finalizer.py:551` `def _record_s2_reject_metrics(...)` — REJECT 메트릭 저장.
- `modules/core/stage2_finalizer.py:188-245` joint_docs/status_shadow 보정 블록.
- `modules/core/stage2_finalizer.py:281-304` DB commit 실패 rollback + state_tracker 복구 블록.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage2_finalizer.py:199-233` physical_inventory 상속  
> 실패 시나리오: `prev_inventory`가 list가 아니면 상속 루프가 건너뛰어 inventory 손실 가능.  
> 상류/하류 컨텍스트: 상류 기본값은 list(`modules/core/stage2_finalizer.py:193`), 하류는 list일 때만 inherited 계산(`modules/core/stage2_finalizer.py:223-232`).  
> **판정**: RISK (Design Check Needed) — 타입 편차 시 데이터 소실 가능.

> **위험 지점 2**: `modules/core/stage2_finalizer.py:281-304` commit 실패 경로  
> 실패 시나리오: 저장 실패 후 in-memory state 오염.  
> 상류/하류 컨텍스트: 예외 시 `all_refined_arcs.pop()` + state_tracker snapshot 복원(`modules/core/stage2_finalizer.py:294-303`) 후 `{"action":"retry"}` 반환(`modules/core/stage2_finalizer.py:304`).  
> **판정**: 안전 — rollback 경로가 명시됨.

> **위험 지점 3**: `modules/core/stage2_finalizer.py:171-176` tactical_doc 길이 조건으로 enriched_block 반영  
> 실패 시나리오: 짧은 tactical_doc에서는 enriched data 반영이 누락될 수 있음.  
> 상류/하류 컨텍스트: 조건 불충족 시에도 필수 필드 보강 블록은 별도 실행(`modules/core/stage2_finalizer.py:188-245`), 하류 검증은 그대로 진행.  
> **판정**: 안전(정책성 조건 분기).

### 5-C. 발견된 버그
- 없음

---
## Round 9 완료

## Round 10 — modules/domain/agents/analyst.py

### 진행 통계 업데이트
- 총 발견: 7건 (CRITICAL: 0, HIGH: 4, MEDIUM: 3)
- 라운드 진행: 10/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/analyst.py:50` `class Analyst(BaseAgent)` — Arc 생성/정규화 핵심 에이전트.
- `modules/domain/agents/analyst.py:64` `def plan_single_volume_v20(...)` — 볼륨 전략 생성.
- `modules/domain/agents/analyst.py:166` `def _validate_arc_state_continuity_v60(...)` — arc 상태 연속성 검사.
- `modules/domain/agents/analyst.py:357` `def _auto_correct_joint_docs_v60(...)` — joint_docs 자동 보정.
- `modules/domain/agents/analyst.py:435` `def plan_single_arc_v20(...)` — 단일 Arc 생성 메인.
- `modules/domain/agents/analyst.py:1039` `def _normalize_arc_output(...)` — 출력 스키마 정규화.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/analyst.py:219-220`  
> `prev_set = set(prev_inventory)`, `curr_set = set(curr_inventory)`  
> 실패 시나리오: inventory list 안에 dict가 있으면 `TypeError: unhashable type: 'dict'`.  
> 상류/하류 컨텍스트: 상류에서 inventory를 str/list로만 정규화(`modules/domain/agents/analyst.py:215-217`)하며 list 내부 원소 타입 검증은 없음, 하류는 차집합 연산을 즉시 수행(`modules/domain/agents/analyst.py:222`).  
> **판정**: BUG.

> **위험 지점 2**: `modules/domain/agents/analyst.py:231-233` internal_energy 파싱  
> 실패 시나리오: `%`/문자 혼합 값에서 `int()` 실패.  
> 상류/하류 컨텍스트: `try` 내 변환 실패를 잡아 보정 처리(`modules/domain/agents/analyst.py:231-233`, `modules/domain/agents/analyst.py:235` 이후), 하류는 경고만 생성.  
> **판정**: 안전.

> **위험 지점 3**: `modules/domain/agents/analyst.py:430-431` top-level `joint_docs` 동기화  
> 실패 시나리오: `state_constraints["joint_docs"]` 미존재 시 `KeyError`.  
> 상류/하류 컨텍스트: 상류 auto-correct에서 `joint_docs`를 강제 구성(`modules/domain/agents/analyst.py:419-428`), 하류(finalizer/arc_corrector)는 top-level `joint_docs`를 읽는다.  
> **판정**: 안전(보정 후 동기화).

### 5-C. 발견된 버그

### [HIGH][B-07] modules/domain/agents/analyst.py:219 — inventory 원소 dict에서 set 변환 크래시

**문제**: 연속성 검증 중 inventory 요소를 그대로 `set()`으로 변환해 dict 원소에서 즉시 크래시한다.

**문제 코드**:
```python
prev_set = set(prev_inventory) if prev_inventory else set()
curr_set = set(curr_inventory) if curr_inventory else set()
```

**수정 제안**:
```python
def _item_key(x):
    return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)
prev_set = {_item_key(i) for i in prev_inventory} if prev_inventory else set()
curr_set = {_item_key(i) for i in curr_inventory} if curr_inventory else set()
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현(TypeError) + 계약 위반(컬렉션 원소 타입 미정규화) 확인.

### 오탐 재검증 (Round 10)
- `modules/domain/agents/arc_corrector.py:505-506` 변경비율 우회 이슈는 **오탐 전환**: 현재는 확장/축소 모두 비율 계산.
- `modules/core/stage2_finalizer.py:193` physical_inventory 기본값 string 주장 건은 **오탐 전환**: 실제 기본값 list(`["물품 미정"]`).
- `modules/domain/agents/analyst.py:430-431` `joint_docs` 누락 주장 건은 **오탐 전환**: 상류 보정 후 동기화.

---
## Round 10 완료

## Round 11 — modules/domain/agents/arc_corrector.py + arc_critic.py + arc_ensemble.py

### 진행 통계 업데이트
- 총 발견: 8건 (CRITICAL: 0, HIGH: 5, MEDIUM: 3)
- 라운드 진행: 11/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/arc_corrector.py:81` `class ArcCorrector` — Arc 자동 수정기.
- `modules/domain/agents/arc_corrector.py:125` `def correct(...)` — 이슈 단위 수정 루프.
- `modules/domain/agents/arc_corrector.py:495` `def _validate_change_ratio(...)` — 변경비율 한계 검사.
- `modules/domain/agents/arc_critic.py:123` `class ArcCritic` — Arc Python/LLM 비평기.
- `modules/domain/agents/arc_critic.py:254` `def _python_critique_fallback(...)` — 비평 폴백 규칙.
- `modules/domain/agents/arc_ensemble.py:58` `class ArcEnsembleGenerator` — 다중 전략 Arc 생성기.
- `modules/domain/agents/arc_ensemble.py:502` `def _ensure_required_fields(...)` — 생성 결과 필수 필드 보정.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/arc_critic.py:294,298`  
> `all_prev_items.update(items)` + `duplicates = set(current_items) & all_prev_items`  
> 실패 시나리오: `items/current_items`에 dict가 섞이면 `TypeError`.  
> 상류/하류 컨텍스트: 상류는 list 여부만 확인(`modules/domain/agents/arc_critic.py:293,297`), 하류는 중복 체크 결과를 critical issue로 사용(`modules/domain/agents/arc_critic.py:299-304`).  
> **판정**: BUG.

> **위험 지점 2**: `modules/domain/agents/arc_corrector.py:505-506` `change_ratio = diff_len / max(original_len, 1)`  
> 실패 시나리오: 과거에는 문자열 길이 증가 경로가 무조건 통과.  
> 상류/하류 컨텍스트: 현재 구현은 절대 차이를 기준으로 양방향 검사하며(`modules/domain/agents/arc_corrector.py:502-506`), 하류에서 `self.max_change_ratio`를 강제한다.  
> **판정**: 안전(기존 오탐 해소).

> **위험 지점 3**: `modules/domain/agents/arc_ensemble.py:513-520` state_constraints 강제 fallback  
> 실패 시나리오: LLM이 잘못된 타입을 반환하면 기본 상태로 덮여 실제 의도 정보가 유실될 수 있음.  
> 상류/하류 컨텍스트: 상류는 타입 불일치 방어 목적(`modules/domain/agents/arc_ensemble.py:513-515`), 하류 검증은 기본값을 정상값으로 간주할 가능성 존재.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그

### [HIGH][B-08] modules/domain/agents/arc_critic.py:298 — 아이템 중복검사 set 연산 크래시

**문제**: 이전/현재 아이템 리스트에 dict가 포함되면 set 연산에서 크래시한다.

**문제 코드**:
```python
all_prev_items.update(items)
duplicates = set(current_items) & all_prev_items
```

**수정 제안**:
```python
def _item_key(x):
    return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)
all_prev_items.update(_item_key(i) for i in items)
duplicates = {_item_key(i) for i in current_items} & all_prev_items
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현(TypeError) + 타입계약 위반 확인.

---
## Round 11 완료

## Round 12 — modules/domain/agents/arc_draft_validator.py + modules/core/stage2_context.py + modules/core/stage2_optimizer.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 12/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/arc_draft_validator.py:28` `class ArcDraftValidator` — 생성 Arc 초안 검증기.
- `modules/domain/agents/arc_draft_validator.py:70` `def validate(...)` — 필드/중복/연속성 검증 통합.
- `modules/domain/agents/arc_draft_validator.py:201` `def _validate_duplicate_acquisition(...)` — 획득 중복 체크.
- `modules/core/stage2_context.py:4` `class Stage2Context` — Stage2 DI 컨텍스트.
- `modules/core/stage2_optimizer.py:29` `class StateSnapshotInjector` — 이전 Arc 상태 주입 프롬프트 생성.
- `modules/core/stage2_optimizer.py:66` `def _collect_all_items(...)` — inventory/items 병합.
- `modules/core/stage2_optimizer.py:150` `class ArcAutoCorrector` — Arc 자동 보정기.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/arc_draft_validator.py:212,217`  
> `all_acquired.update(items)` / `all_acquired.update(inventory)`  
> 실패 시나리오: list 원소가 dict면 `TypeError`.  
> 상류/하류 컨텍스트: 상류는 list 타입만 검사(`modules/domain/agents/arc_draft_validator.py:211,216`)하고 원소 정규화 없음, 하류는 current_items 중복 판정에 집합을 직접 사용(`modules/domain/agents/arc_draft_validator.py:231`).  
> **판정**: BUG.

> **위험 지점 2**: `modules/core/stage2_optimizer.py:80` `return list(set(items))`  
> 실패 시나리오: `items`에 dict 원소 포함 시 `TypeError`.  
> 상류/하류 컨텍스트: 상류 `_collect_all_items`에서 inventory list를 그대로 확장(`modules/core/stage2_optimizer.py:75-78`), 하류는 이 함수 결과를 상태 주입 프롬프트에 사용.  
> **판정**: BUG.

> **위험 지점 3**: `modules/core/stage2_optimizer.py:106-107`  
> `all_items.update(state.get("items_acquired", []))` / `all_grants.update(...)`  
> 실패 시나리오: state 배열 원소가 dict면 `TypeError`.  
> 상류/하류 컨텍스트: 상류 state는 외부 LLM/정규화 결과의 혼합체이며 원소 타입 가드 없음(`modules/core/stage2_optimizer.py:105-107`), 하류는 prompt 생성 직전 집합 변환 수행.  
> **판정**: BUG.

### 5-C. 발견된 버그

### [HIGH][B-09] modules/domain/agents/arc_draft_validator.py:212 — 중복 획득 집계 중 unhashable 크래시

**문제**: `items_acquired`/`physical_inventory` 내부 dict 원소를 set에 직접 넣어 검증이 중단된다.

**문제 코드**:
```python
all_acquired.update(items)
all_acquired.update(inventory)
```

**수정 제안**:
```python
def _item_key(x):
    return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)
all_acquired.update(_item_key(i) for i in items)
all_acquired.update(_item_key(i) for i in inventory)
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현(TypeError) + 계약 위반 확인.

### [HIGH][B-10] modules/core/stage2_optimizer.py:80 — `_collect_all_items` 결과 set 변환 크래시

**문제**: inventory list 원소가 dict면 `list(set(items))`에서 즉시 크래시.

**문제 코드**:
```python
return list(set(items))
```

**수정 제안**:
```python
def _item_key(x):
    return x.get("name", x.get("item", "")) if isinstance(x, dict) else str(x)
return list({_item_key(i) for i in items if i})
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현(TypeError) 확인.

### [HIGH][B-11] modules/core/stage2_optimizer.py:106 — Arc 누적 set.update 크래시

**문제**: `items_acquired`/`grants_received`에 dict 원소가 있으면 `set.update()`가 실패.

**문제 코드**:
```python
all_items.update(state.get("items_acquired", []))
all_grants.update(state.get("grants_received", []))
```

**수정 제안**:
```python
all_items.update(_item_key(i) for i in state.get("items_acquired", []))
all_grants.update(_item_key(i) for i in state.get("grants_received", []))
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현(TypeError) + 타입 계약 위반 확인.

---
## Round 12 완료

## Round 13 — modules/domain/agents/director.py + director_ensemble.py + director_auditor.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 13/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/director.py:19` `class Director` — Director facade.
- `modules/domain/agents/director.py:134` `def audit_manuscript(...)` — 원고 심사 진입.
- `modules/domain/agents/director_ensemble.py:24` `class DirectorEnsembleSelector` — 후보 비교/선택.
- `modules/domain/agents/director_ensemble.py:244` `def select_and_judge_ensemble(...)` — 후보 심사 메인.
- `modules/domain/agents/director_auditor.py:31` `class DirectorQualityAuditor` — 품질 심사 구현체.
- `modules/domain/agents/director_auditor.py:322` `def audit_manuscript(...)` — 원고 심사 핵심.
- `modules/domain/agents/director_auditor.py:681` `def audit_strategic_plan(...)` — 전략 심사.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/director_ensemble.py:328`  
> `"manuscript": c.get("manuscript", "")[:12000]`  
> 실패 시나리오: manuscript가 dict/list면 슬라이싱에서 `TypeError`.  
> 상류/하류 컨텍스트: 상류 writer fail-open 경로에서 비문자 manuscript가 통과 가능(`modules/models/manuscript.py:50`), 하류는 타입 체크 없이 슬라이스 수행.  
> **판정**: RISK (Design Check Needed, B-02 연동).

> **위험 지점 2**: `modules/domain/agents/director_auditor.py:267` 광범위 예외 fallback  
> 실패 시나리오: 심사 실패 시 원인 손실/점수 왜곡.  
> 상류/하류 컨텍스트: `except Exception`에서 기본 REJECT 결과로 강등(`modules/domain/agents/director_auditor.py:267-274`), 하류는 이 값을 최종 결정 근거로 사용.  
> **판정**: 안전(비차단 의도) + 운영 리스크.

> **위험 지점 3**: `modules/domain/agents/director.py:126-130` facade 위임  
> 실패 시나리오: 하위 모듈 반환 스키마가 바뀌면 facade 레벨 가드 부족.  
> 상류/하류 컨텍스트: Director는 대부분 `return self._ensemble...` 직위임이며 타입 방어가 얇음, 하류 오케스트레이터는 dict 계약을 가정.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 13 완료

## Round 14 — modules/domain/agents/director_grading.py + director_continuity.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 14/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/director_grading.py:14` `class DirectorGradingSystem`.
- `modules/domain/agents/director_grading.py:68` `def grade_manuscript_v59(...)` — 점수/등급 산출.
- `modules/domain/agents/director_grading.py:189` `def generate_revision_guide_v59(...)`.
- `modules/domain/agents/director_grading.py:550` `def apply_adaptive_decision(...)`.
- `modules/domain/agents/director_continuity.py:15` `class DirectorContinuityValidator`.
- `modules/domain/agents/director_continuity.py:41` `def validate_entity_consistency(...)`.
- `modules/domain/agents/director_continuity.py:445` `def check_manuscript_history_with_cache(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/director_grading.py:159-163` 카테고리 점수 추출  
> 실패 시나리오: score/max 타입 불일치 시 점수 왜곡.  
> 상류/하류 컨텍스트: 변환 실패 시 해당 항목 skip 후 평균 계산(`modules/domain/agents/director_grading.py:159-163`), 하류 등급 산출은 기본 50점 폴백 사용.  
> **판정**: 안전(방어 로직 존재).

> **위험 지점 2**: `modules/domain/agents/director_continuity.py:60-68` entity_registry 없음 시 PASS  
> 실패 시나리오: 엔티티 불일치가 검증 자체에서 누락될 수 있음.  
> 상류/하류 컨텍스트: early return PASS(`modules/domain/agents/director_continuity.py:60-68`), 하류는 이 결정을 그대로 누적 판단에 반영.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/domain/agents/director_continuity.py:135-137` 예외 시 UNKNOWN 반환  
> 실패 시나리오: 검증 실패가 하드 fail이 아닌 중립값으로 전달되어 품질 누수 가능.  
> 상류/하류 컨텍스트: 예외를 잡아 `decision: UNKNOWN`으로 반환, 상위 심사는 경고 수준으로 취급 가능.  
> **판정**: 안전(비차단 설계) + 운영 리스크.

### 5-C. 발견된 버그
- 없음

---
## Round 14 완료

## Round 15 — modules/validation/validation_orchestrator.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 15/40

### 5-A. 파일 구조 요약
- `modules/validation/validation_orchestrator.py:130` `class ValidationOrchestrator`.
- `modules/validation/validation_orchestrator.py:207` `def validate(...)` — 동기 검증 엔트리.
- `modules/validation/validation_orchestrator.py:545` `def _evaluate_with_self_consistency(...)`.
- `modules/validation/validation_orchestrator.py:701` `def _generate_detailed_feedback(...)`.
- `modules/validation/validation_orchestrator.py:896` `def _record_failure_to_reflexion(...)`.
- `modules/validation/validation_orchestrator.py:949` 병렬 검증 경로(`validate_parallel_v59`) 핵심.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/validation/validation_orchestrator.py:960-964` + `977/988/999/...` + `1142`  
> 실패 시나리오: adaptive threshold를 올린 뒤 early return되면 원복(`1142`)이 실행되지 않아 다음 요청에 임계치가 누적될 수 있음.  
> 상류/하류 컨텍스트: 상류에서 threshold를 mutable 필드에 직접 대입(`modules/validation/validation_orchestrator.py:963`), 하류는 여러 조기 return 경로(`modules/validation/validation_orchestrator.py:977-1001`, `1064-1071`)를 가진다.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/validation/validation_orchestrator.py:1031-1042` 병렬 결과 예외 처리  
> 실패 시나리오: 특정 validator가 죽어도 `None`으로 바꿔 흐름 계속, 품질 저하가 누락될 수 있음.  
> 상류/하류 컨텍스트: `return_exceptions=True` + 예외를 warning 후 `None` 치환, 하류는 dict fallback 강제(`modules/validation/validation_orchestrator.py:1046-1051`).  
> **판정**: 안전(비차단 정책) + 운영 리스크.

> **위험 지점 3**: `modules/validation/validation_orchestrator.py:1124-1131` 최종 판정 임계치  
> 실패 시나리오: adaptive_threshold와 fixed 기준(85) 혼합으로 정책 해석 불일치 가능.  
> 상류/하류 컨텍스트: 상류에서 adaptive 계산(`modules/validation/validation_orchestrator.py:962`), 하류는 PASS/CONDITIONAL_PASS 경계가 이중 기준.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 15 완료

## Round 16 — modules/validation/scoring_validator.py + pre_llm_validator.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 16/40

### 5-A. 파일 구조 요약
- `modules/validation/scoring_validator.py:16` `class ScoringValidator`.
- `modules/validation/scoring_validator.py:101` `def validate(...)` — 점수 검증 엔트리.
- `modules/validation/scoring_validator.py:154` `def _calculate_llm_scores(...)`.
- `modules/validation/scoring_validator.py:274` `def _fallback_llm_scores(...)`.
- `modules/validation/pre_llm_validator.py:28` `class PreLLMValidator`.
- `modules/validation/pre_llm_validator.py:43` `def validate(...)` — LLM 이전 정적 검증.
- `modules/validation/pre_llm_validator.py:186` `def _check_extreme_sentence_length(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/validation/scoring_validator.py:259-263` score/max 정수 변환  
> 실패 시나리오: LLM이 문자열/None을 반환하면 점수 계산 오류.  
> 상류/하류 컨텍스트: 변환 실패를 잡고 0으로 보정(`modules/validation/scoring_validator.py:259-263`), 하류 총점 집계는 dict 가드와 함께 동작(`modules/validation/scoring_validator.py:127`).  
> **판정**: 안전.

> **위험 지점 2**: `modules/validation/scoring_validator.py:127`  
> `total_score = sum(v.get("score", 0) ... for v in all_scores.values())`  
> 실패 시나리오: 일부 카테고리 비정상 시 총점이 과소 계산될 수 있음.  
> 상류/하류 컨텍스트: 비정상 항목을 0으로 흡수해 fail-stop 대신 fail-soft, 하류는 threshold 비교만 수행.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/validation/pre_llm_validator.py:191-193` 문장 수 적을 때 early return  
> 실패 시나리오: 극단적으로 짧거나 포맷 깨진 텍스트가 일부 점검을 우회할 수 있음.  
> 상류/하류 컨텍스트: 상류 minimum-length는 다른 validator에서 처리되고, 하류 orchestrator에서 blocking/continuity가 추가 실행됨.  
> **판정**: 안전(다단계 검증 체인 의존).

### 5-C. 발견된 버그
- 없음

---
## Round 16 완료

## Round 17 — modules/validation/blocking_* + continuity_validator.py + consistency_validator.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 17/40

### 5-A. 파일 구조 요약
- `modules/validation/blocking_validator.py:16` `class BlockingValidator`.
- `modules/validation/blocking_validator.py:55` `def validate(...)` — 차단 규칙 통합.
- `modules/validation/blocking_validator_entity_checks.py:12` `class BlockingValidatorEntityChecks`.
- `modules/validation/blocking_validator_scene_checks.py:15` `class BlockingValidatorSceneChecks`.
- `modules/validation/blocking_validator_consistency_checks.py:22` `class BlockingValidatorConsistencyChecks`.
- `modules/validation/continuity_validator.py:24` `class ContinuityValidator`.
- `modules/validation/consistency_validator.py:16` `class ConsistencyValidator`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/validation/blocking_validator.py:90-103` degraded check 처리  
> 실패 시나리오: 관계/정보 consistency 검증이 degraded여도 실패가 아닌 warning으로만 처리되어 차단 누락 가능.  
> 상류/하류 컨텍스트: degraded 시 `warnings.append(...)`만 수행, 최종 passed는 `len(failures)==0` 기준(`modules/validation/blocking_validator.py:129-133`).  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/validation/continuity_validator.py:197-208` 이전 HUD 조회 실패  
> 실패 시나리오: DB 조회 실패 시 continuity 근거 데이터가 줄어든다.  
> 상류/하류 컨텍스트: 예외를 잡고 fallback (`martial_hud` 기반)로 전환(`modules/validation/continuity_validator.py:212`), 하류는 violation/warning을 계속 계산.  
> **판정**: 안전(비차단 설계).

> **위험 지점 3**: `modules/validation/consistency_validator.py:50-71` guard 로드 실패  
> 실패 시나리오: 장르 guard 미로드 시 규칙 검증 정확도 저하.  
> 상류/하류 컨텍스트: 예외를 로깅하고 기본 흐름으로 진행(`modules/validation/consistency_validator.py:71`), 하류는 다른 consistency 하위 검사로 일부 보완.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 17 완료

## Round 18 — modules/domain/agents/state_tracker.py + state_tracker_npc.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 18/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker.py:96` `class StateTracker`.
- `modules/domain/agents/state_tracker.py:184` `def full_extract_from_arcs(...)` — Arc 전체 재구축.
- `modules/domain/agents/state_tracker.py:352` `def create_episode_state(...)`.
- `modules/domain/agents/state_tracker_npc.py:70` `class StateTrackerNPC`.
- `modules/domain/agents/state_tracker_npc.py:199` `def check_npc_changes(...)`.
- `modules/domain/agents/state_tracker_npc.py:277` `def extract_npc_info_from_arc(...)`.
- `modules/domain/agents/state_tracker_npc.py:528` `def merge_npc_registry(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/state_tracker.py:194-210` 전체 재구축 단계별 예외 흡수  
> 실패 시나리오: 특정 추출 단계 실패가 누락된 상태로 누적되어 drift 발생 가능.  
> 상류/하류 컨텍스트: 단계별 `except Exception` 후 계속 진행, 하류 Stage3/4는 tracker 상태를 진실원천으로 사용.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/domain/agents/state_tracker_npc.py:532` `info.copy()`  
> 실패 시나리오: 중첩 구조(aliases/history 등)에서 shallow copy로 참조 공유 부작용 가능.  
> 상류/하류 컨텍스트: 상류 merge는 빈번히 호출되고, 하류에서 `existing.update(filtered)`를 수행(`modules/domain/agents/state_tracker_npc.py:541-548`).  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/domain/agents/state_tracker_npc.py:345` `_is_standalone_name` 수동 인덱스 루프  
> 실패 시나리오: 경계 인덱스 버그 가능성.  
> 상류/하류 컨텍스트: `while idx <= len(text) - len(name)` 경계 가드가 있고, match 실패 시 idx 증가로 종료 보장.  
> **판정**: 안전.

### 5-C. 발견된 버그
- 없음

---
## Round 18 완료

## Round 19 — modules/domain/agents/state_tracker_plots.py + state_extractor.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 19/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/state_tracker_plots.py:55` `class StateTrackerPlots`.
- `modules/domain/agents/state_tracker_plots.py:91` `def extract_resolved_plots_from_arc(...)`.
- `modules/domain/agents/state_tracker_plots.py:137` `def extract_entity_destructions_from_arc(...)`.
- `modules/domain/agents/state_tracker_plots.py:316` `def update_plot_mentions_from_arc(...)`.
- `modules/domain/agents/state_extractor.py:179` `class StateExtractor`.
- `modules/domain/agents/state_extractor.py:201` `def extract_state(...)`.
- `modules/domain/agents/state_extractor.py:263` `def extract_cumulative_state(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/state_extractor.py:374` `list(set(all_acquired))`  
> 실패 시나리오: inventory list에 dict가 섞이면 unhashable 예외 가능.  
> 상류/하류 컨텍스트: 상류에서 list inventory를 그대로 extend(`modules/domain/agents/state_extractor.py:319-320`), 하류 dedupe에서 set 변환 수행(`modules/domain/agents/state_extractor.py:374`).  
> **판정**: RISK (Design Check Needed, B-09/B-10 계열).

> **위험 지점 2**: `modules/domain/agents/state_tracker_plots.py:114,158` dedupe 키가 `name/plot + arc_no` 중심  
> 실패 시나리오: 동일 arc 내 episode 단위 중복 또는 세부 변화가 소실될 수 있음.  
> 상류/하류 컨텍스트: 상류에서 arc 단위로만 추출, 하류 summary는 arc 단위 문자열 출력(`modules/domain/agents/state_tracker_plots.py:127-129`).  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/domain/agents/state_extractor.py:214-216` cache key 생성  
> 실패 시나리오: arc_no 비정상값 hash 충돌 시 잘못된 cache hit 가능성.  
> 상류/하류 컨텍스트: 상류는 int가 아니면 hash(str) 사용, 하류는 hit 시 즉시 return.  
> **판정**: 안전(확률 낮음, 운영 감시 필요).

### 5-C. 발견된 버그
- 없음

---
## Round 19 완료

## Round 20 — modules/domain/agents/continuity_* + continuity_inspector.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 20/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/continuity_inspector.py:40` `class ContinuityInspector`.
- `modules/domain/agents/continuity_inspector.py:337` `def inspect(...)`.
- `modules/domain/agents/continuity_manuscript.py:157` `class ContinuityManuscriptValidator`.
- `modules/domain/agents/continuity_arc.py:203` `class ContinuityArcValidator`.
- `modules/domain/agents/continuity_blueprint.py:135` `class ContinuityBlueprintValidator`.
- `modules/domain/agents/continuity_tracker.py:25` `class ContinuityTrackerIntegration`.
- `modules/domain/agents/continuity_tracker.py:85` `def validate_with_trackers(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/continuity_arc.py:249-250`  
> `ep_count = current_arc.get("ep_count", 5)` / `ep_end = ... + ep_count - 1`  
> 실패 시나리오: `ep_count`가 문자열이면 산술 `TypeError`.  
> 상류/하류 컨텍스트: 상류 Arc 데이터는 LLM 정규화 결과 포함, 하류 precheck 로직은 산술 전 타입 보정이 없다.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/domain/agents/continuity_manuscript.py:236` 최소 길이 early reject  
> 실패 시나리오: 짧은 원고에서 세부 continuity 진단 누락.  
> 상류/하류 컨텍스트: early reject 후 상세 검사 생략, 하류에는 reject reason만 전달.  
> **판정**: 안전(정책성 차단).

> **위험 지점 3**: `modules/domain/agents/continuity_tracker.py:61-63` tracker init 실패 비차단  
> 실패 시나리오: tracker 기반 경고가 모두 빠질 수 있음.  
> 상류/하류 컨텍스트: init 실패 시 예외를 삼키고 진행, 하류는 LLM/기본 continuity만 사용.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

### 오탐 재검증 (Round 20)
- `modules/core/stage2_finalizer.py:281-304` commit 결과 무시 주장 건은 **오탐 유지**: 실패 시 pop/rollback/재시도 경로 존재.
- `modules/domain/agents/arc_corrector.py:495-506` 20% 제한 우회 주장 건은 **오탐 유지**: 현재 구현상 우회 불가.
- `modules/validation/validation_orchestrator.py` fail-open 검증 경로는 **BUG 미확정** 유지: 설계 의도 가능성이 높아 RISK로 분리.

---
## Round 20 완료

## Round 21 — modules/core/world_state.py + fact_ledger.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 21/40

### 5-A. 파일 구조 요약
- `modules/core/world_state.py:17` `class WorldStateManager`.
- `modules/core/world_state.py:75` `def update_from_state_changes(...)`.
- `modules/core/world_state.py:260` `def get_summary(...)`.
- `modules/core/fact_ledger.py:17` `class FactLedger`.
- `modules/core/fact_ledger.py:77` `def update_from_state_changes(...)`.
- `modules/core/fact_ledger.py:207` `def update_from_bible_delta(...)`.
- `modules/core/fact_ledger.py:353` `def to_summary(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/world_state.py:66-68` save 실패 비차단  
> 실패 시나리오: 최신 world state가 디스크에 반영되지 않은 채 진행.  
> 상류/하류 컨텍스트: 예외를 warning으로만 처리, 하류는 in-memory state를 계속 참조.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/fact_ledger.py:64-66` save 실패 비차단  
> 실패 시나리오: fact ledger 내구성 저하.  
> 상류/하류 컨텍스트: 예외를 warning 처리하고 계속 진행, 하류 continuity/fact 기반 프롬프트 품질 저하 가능.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/world_state.py:111-126` skill/event 누적  
> 실패 시나리오: 장기 운영 시 항목 증가로 메모리/요약 길이 부담.  
> 상류/하류 컨텍스트: `_MAX_SKILLS` 컷오프가 일부 존재(`modules/core/world_state.py:122`), 하지만 다른 누적 필드는 정책 제한이 약함.  
> **판정**: 안전(부분 보호 존재) + 운영 리스크.

### 5-C. 발견된 버그
- 없음

---
## Round 21 완료

## Round 22 — modules/core/db_manager.py + modules/domain/agents/base_agent.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 22/40

### 5-A. 파일 구조 요약
- `modules/core/db_manager.py:48` `class DBManager`.
- `modules/core/db_manager.py:61` `def _boot_db(...)` — 스키마/마이그레이션.
- `modules/core/db_manager.py:372` `def close(...)` — 연결 종료 처리.
- `modules/core/db_manager.py:389` `def execute_query(...)`.
- `modules/domain/agents/base_agent.py:123` `class BaseAgent`.
- `modules/domain/agents/base_agent.py:236` `def ask(...)` — 공통 LLM 호출 루프.
- `modules/domain/agents/base_agent.py:775` `def _validate_response(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/db_manager.py:376-377` `close()` 시 in_transaction이면 commit  
> 실패 시나리오: 상위 계층이 실패로 간주한 부분 트랜잭션이 종료 시 커밋될 수 있음.  
> 상류/하류 컨텍스트: 상류 일부 경로는 명시 rollback 없이 False 반환(B-01 맥락), 하류 프로세스 종료 시 `close()`가 호출된다.  
> **판정**: RISK (Design Check Needed, 중복 이슈 연계).

> **위험 지점 2**: `modules/domain/agents/base_agent.py:257-263` 키 회전 경쟁 구간  
> 실패 시나리오: 동시성 상황에서 client 교체 타이밍 불일치.  
> 상류/하류 컨텍스트: rotation lock을 사용하나 client 교체는 인스턴스 단위로 이뤄지며, 하류 호출 루프가 길다(`modules/domain/agents/base_agent.py:327+`).  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/domain/agents/base_agent.py:323-325` metrics startup fail-open  
> 실패 시나리오: 관측 누락으로 비용/호출 분석 공백.  
> 상류/하류 컨텍스트: 예외 시 debug 로그 후 pass, 하류 생성 품질에는 영향 없음.  
> **판정**: 안전(비핵심 관측 경로).

### 5-C. 발견된 버그
- 없음

---
## Round 22 완료

## Round 23 — modules/core/prompt_builder.py + project_manager.py + services/*

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 23/40

### 5-A. 파일 구조 요약
- `modules/core/prompt_builder.py:24` `class PromptBuilder`.
- `modules/core/prompt_builder.py:451` `def generate_writer_guidance_v60_8(...)`.
- `modules/core/project_manager.py:44` `class ProjectContext`.
- `modules/core/project_manager.py:455` `def commit_full_episode_data(...)`.
- `modules/core/services/state_service.py:18` `class StateService`.
- `modules/core/services/state_service.py:57` `def validate_arc_mapping(...)`.
- `modules/core/services/project_service.py:17` `class ProjectService`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/project_manager.py:129-131` DB 로드 예외 흡수  
> 실패 시나리오: 앵커 로드 실패 시 빈 상태로 이어져 후속 단계가 축약 컨텍스트로 동작.  
> 상류/하류 컨텍스트: 예외 시 기본값 유지, 하류는 동일 객체를 단일 진실원천으로 사용.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/services/state_service.py:70-76` ep_count 정규화  
> 실패 시나리오: 타입 이상치 시 잘못된 ep_count 전파.  
> 상류/하류 컨텍스트: `int()` 변환 실패 시 5로 보정(`modules/core/services/state_service.py:72-76`), 하류 mapping fix로 계속 진행.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/services/project_service.py:119-126` rollback 시 json.loads  
> 실패 시나리오: 손상 row에서 파싱 실패하면 일부 상태 복구 누락.  
> 상류/하류 컨텍스트: 외곽 try/except로 복구 루틴 자체는 유지, 하류 캐시 무효화가 별도 실행(`main_a.py:2685-2690`).  
> **판정**: 안전(복구 우선 설계).

### 5-C. 발견된 버그
- 없음

---
## Round 23 완료

## Round 24 — modules/core/genre_guards/base_guard.py + wuxia_guard.py + hunter_guard.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 24/40

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/base_guard.py:16` `class BaseGuard`.
- `modules/core/genre_guards/base_guard.py:34` `def _load_genre_yaml(...)`.
- `modules/core/genre_guards/base_guard.py:182` `def run_deep_validation(...)`.
- `modules/core/genre_guards/wuxia_guard.py:13` `class WuxiaGuard`.
- `modules/core/genre_guards/wuxia_guard.py:258` `def get_impossible_actions(...)`.
- `modules/core/genre_guards/hunter_guard.py:15` `class HunterGuard`.
- `modules/core/genre_guards/hunter_guard.py:227` `def get_impossible_actions(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/genre_guards/base_guard.py:39-46` YAML 로드 실패 시 `{}`  
> 실패 시나리오: 장르 규칙 파일 깨짐/누락 시 규칙 세트가 약화.  
> 상류/하류 컨텍스트: 예외를 흡수하고 빈 dict 반환, 하류 guard는 기본 상수 또는 빈 규칙으로 동작.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/genre_guards/base_guard.py:68-90` 숫자 파싱 보정  
> 실패 시나리오: 비정상 텍스트 수치가 0으로 수렴해 action 판정이 완화될 수 있음.  
> 상류/하류 컨텍스트: 파싱 실패 fallback은 의도적 안정화이며, 하류에서 추가 규칙 검증이 존재.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/genre_guards/wuxia_guard.py:267` / `hunter_guard.py:236` 상태 dict 키 의존  
> 실패 시나리오: HUD 키 누락 시 불가능 행동 탐지가 느슨해짐.  
> 상류/하류 컨텍스트: `.get(..., default)`로 크래시는 방지하나, 정책 강도는 낮아질 수 있다.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 24 완료

## Round 25 — modules/core/genre_guards/investment/fantasy/work/style + 확장 가드

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 25/40

### 5-A. 파일 구조 요약
- `modules/core/genre_guards/investment_guard.py:12` `class InvestmentGuard`.
- `modules/core/genre_guards/fantasy_guard.py:14` `class FantasyGuard`.
- `modules/core/genre_guards/work_guard.py:22` `class WorkGuard`.
- `modules/core/genre_guards/style_guard.py:22` `class StyleGuard`.
- `modules/core/genre_guards/actor_guard.py:12` `class ActorGuard`.
- `modules/core/genre_guards/alt_history_guard.py:12` `class AltHistoryGuard`.
- `modules/core/genre_guards/medical_guard.py:12` `class MedicalGuard`.
- `modules/core/genre_guards/sports_guard.py:12` `class SportsGuard`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/genre_guards/work_guard.py:61-68` `_load_yaml` 실패 시 `{}`  
> 실패 시나리오: 작품별 룰 파일 누락 시 확장 제약이 비활성화.  
> 상류/하류 컨텍스트: 예외/미존재를 빈 설정으로 처리, 하류는 base_guard 규칙만 수행.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/genre_guards/style_guard.py:97` `__getattr__` 위임  
> 실패 시나리오: base guard API 변경 시 style_guard가 런타임에 늦게 깨짐.  
> 상류/하류 컨텍스트: 대부분 메서드를 base에 위임(`modules/core/genre_guards/style_guard.py:51-93`), 타입 계약은 정적 검증이 약하다.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/genre_guards/investment_guard.py:237` / `fantasy_guard.py:184` 수치 상태 `.get()` 기반  
> 실패 시나리오: HUD 값 포맷 편차 시 guard 강도가 낮아질 수 있음.  
> 상류/하류 컨텍스트: 기본값으로 크래시는 피하지만, 검증 엄격도는 데이터 품질에 의존.  
> **판정**: 안전(크래시 방지 우선 설계).

### 5-C. 발견된 버그
- 없음

---
## Round 25 완료

## Round 26 — main_a.py (L1~1000)

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 26/40

### 5-A. 파일 구조 요약
- `main_a.py:167` `class SovereignApp` — 전체 앱 진입점.
- `main_a.py:170` `def __init__(self)` — 구성요소 초기화.
- `main_a.py:279` `def _safe_commit(self) -> bool`.
- `main_a.py:303` `async def _safe_commit_async(self) -> bool`.
- `main_a.py:842` `def boot(self)` — 프로젝트/장르/시스템 부팅.
- `main_a.py:952` `def _load_models_yaml(self) -> dict`.
- `main_a.py:980` `def _ignite_quad_cache_system(self)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `main_a.py:279-301` `_safe_commit()` 반환값 사용 일관성  
> 실패 시나리오: 상위 호출부가 bool 결과를 무시하면 commit 실패가 은닉될 수 있음.  
> 상류/하류 컨텍스트: 함수는 실패 시 rollback 후 False 반환, 하류 일부 경로는 결과를 확인하지만 전 경로 강제는 아님.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `main_a.py:891-896` 장르 불일치 사용자 입력 분기  
> 실패 시나리오: 비대화 환경에서 blocking 입력으로 부팅 중단.  
> 상류/하류 컨텍스트: mismatch 시 `input()` 호출, 하류는 `_emergency_shutdown()` 후 종료.  
> **판정**: RISK (운영환경 의존).

> **위험 지점 3**: `main_a.py:960-968` models.yaml 로드 예외 흡수  
> 실패 시나리오: 모델 설정 오류가 fallback으로 덮여 의도치 않은 모델 매핑 사용 가능.  
> 상류/하류 컨텍스트: 예외 시 warning 후 `{}` 반환, 하류 `_get_agent_model_map()`이 legacy fallback(`main_a.py:976-978`)을 사용.  
> **판정**: 안전(호환성 우선).

### 5-C. 발견된 버그
- 없음

---
## Round 26 완료

## Round 27 — main_a.py (L1001~2000)

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 27/40

### 5-A. 파일 구조 요약
- `main_a.py:1309` `def _attach_agents(self) -> bool`.
- `main_a.py:1743` `def _load_v50_history(self) -> None`.
- `main_a.py:1758` `def _get_protagonist_name(self) -> str`.
- `main_a.py:1788` `def _fix_entity_registry_protagonist(...)`.
- `main_a.py:1819` `def _run_main_process(self) -> None`.
- `main_a.py:1933` `def _shutdown_app(self)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `main_a.py:1319-1380` 대규모 agent 초기화 단일 try 블록  
> 실패 시나리오: 중간 실패 시 부분 초기화 상태가 남아 후속 참조 오류 가능.  
> 상류/하류 컨텍스트: 실패 시 `False` 반환으로 부팅 중단 경로가 존재(`main_a.py:946-948`), 하지만 디버깅/재시도 시 잔존 객체 주의 필요.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `main_a.py:1766-1786` 주인공 이름 추출 broad except  
> 실패 시나리오: 파싱 실패 시 기본값 `"주인공"`으로 수렴해 entity 정합성이 약화될 수 있음.  
> 상류/하류 컨텍스트: 하류 `main_a.py:1788`에서 protagonist 보정 로직이 추가로 방어.  
> **판정**: 안전(후속 보정 존재).

> **위험 지점 3**: `main_a.py:1954-1963` 종료 시 metrics thread timeout 처리  
> 실패 시나리오: 수집 도중 timeout이면 지표 저장 일부 유실 가능.  
> 상류/하류 컨텍스트: timeout을 허용하고 종료 우선, 하류 DB cost 기록은 별도 시도(`main_a.py:1966-1994`).  
> **판정**: RISK (운영 선택 이슈).

### 5-C. 발견된 버그
- 없음

---
## Round 27 완료

## Round 28 — main_a.py (L2001~2982)

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 28/40

### 5-A. 파일 구조 요약
- `main_a.py:2189` `def _stage_2_arcs(self)`.
- `main_a.py:2241` `def _validate_volume_boundaries(...)`.
- `main_a.py:2423` `def _stage_3_batch_blueprinting(self)`.
- `main_a.py:2434` `def _select_genre(self)`.
- `main_a.py:2667` `def _rewind_stage_2(self)`.
- `main_a.py:2724` `def _generate_narrative_summary(self, up_to_ep)`.
- `main_a.py:2902` `def _stage_4_v2_chief_writer(self, limit_mode=False)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `main_a.py:2206-2209` 이벤트 루프 실행 중 ThreadPool + timeout  
> 실패 시나리오: Stage2가 600초 초과 시 예외 전파로 실행 중단 가능.  
> 상류/하류 컨텍스트: 실행 중 loop 감지 시 우회 실행하지만 timeout 예외 처리 별도 가드가 없음.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `main_a.py:2675-2710` rollback 후 캐시 무효화 fail-open  
> 실패 시나리오: writer/director/state_extractor 캐시 일부가 남아 stale data 사용 가능.  
> 상류/하류 컨텍스트: 예외를 warning으로 강등하고 진행, 하류는 다음 stage에서 캐시 재사용 가능.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `main_a.py:2795-2843` narrative summary LLM 경로  
> 실패 시나리오: 요약 실패 시 anchor 미갱신으로 장기 컨텍스트 약화.  
> 상류/하류 컨텍스트: 예외를 잡아 로그 후 계속, 하류 `_load_narrative_summaries()`는 캐시/기존 anchor를 사용.  
> **판정**: 안전(비핵심 기능 비차단).

### 5-C. 발견된 버그
- 없음

---
## Round 28 완료

## Round 29 — modules/domain/agents/manuscript_validator.py + block_enricher.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 29/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/manuscript_validator.py:18` `class ManuscriptValidator`.
- `modules/domain/agents/manuscript_validator.py:71` `def validate_candidate(...)`.
- `modules/domain/agents/manuscript_validator.py:196` `def validate_all_candidates(...)`.
- `modules/domain/agents/manuscript_validator.py:722` `def _check_cross_episode_duplication(...)`.
- `modules/domain/agents/block_enricher.py:192` `class BlockEnricher`.
- `modules/domain/agents/block_enricher.py:287` `def enrich_block(...)`.
- `modules/domain/agents/block_enricher.py:571` `def enrich_all_blocks_parallel(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/manuscript_validator.py:277-308` scene coverage 추정  
> 실패 시나리오: 키워드 매칭 기반이라 실제 커버리지와 괴리 가능.  
> 상류/하류 컨텍스트: 상류 blueprint 구조를 읽고 heuristic 비율 계산, 하류 director 판단에 참고값으로 반영.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/domain/agents/block_enricher.py:337-411` enrich + director audit 묶음  
> 실패 시나리오: enrich 성공/감사 실패 시 재생성 프롬프트에 과도한 피드백이 누적될 수 있음.  
> 상류/하류 컨텍스트: reject 시 이슈 JSON을 다시 prompt에 주입(`modules/domain/agents/block_enricher.py:354-386`), 하류 반복 횟수 증가 가능.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/domain/agents/block_enricher.py:411` broad except fallback  
> 실패 시나리오: enrich 실패가 조용히 원본 유지로 끝나 품질 하락을 놓칠 수 있음.  
> 상류/하류 컨텍스트: 예외시 함수 레벨에서 안전 반환, 하류 파이프라인은 비차단 진행.  
> **판정**: 안전(운영상 비차단 의도).

### 5-C. 발견된 버그
- 없음

---
## Round 29 완료

## Round 30 — modules/domain/agents/blueprint_ensemble.py + four_phase_arc_generator.py + state_locked_arc_generator.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 30/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/blueprint_ensemble.py:94` `class BlueprintEnsembleGenerator`.
- `modules/domain/agents/blueprint_ensemble.py:111` `def generate_ensemble(...)`.
- `modules/domain/agents/four_phase_arc_generator.py:31` `class FourPhaseArcGenerator`.
- `modules/domain/agents/four_phase_arc_generator.py:113` `def generate(...)`.
- `modules/domain/agents/four_phase_arc_generator.py:393` `def patch_arc_with_feedback(...)`.
- `modules/domain/agents/state_locked_arc_generator.py:160` `class StateLockedArcGenerator`.
- `modules/domain/agents/state_locked_arc_generator.py:175` `def generate(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/blueprint_ensemble.py:179-225` 병렬 future timeout/예외  
> 실패 시나리오: 일부 후보만으로 판단해 다양성 저하.  
> 상류/하류 컨텍스트: timeout/예외를 로깅 후 부분 후보 유지, 하류 validator가 최종 품질 게이트 역할.  
> **판정**: 안전(비차단 설계) + 운영 리스크.

> **위험 지점 2**: `modules/domain/agents/four_phase_arc_generator.py:176-182` 이전 Arc 아이템/수여물 누적  
> 실패 시나리오: 입력 타입 편차 시 제약 프롬프트 왜곡 가능.  
> 상류/하류 컨텍스트: 상류에서 목록 수집 후 prompt 주입, 하류 unified validator가 일부 정합성 검사.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/domain/agents/state_locked_arc_generator.py:320-323` energy parse  
> 실패 시나리오: shadow 포맷 이상 시 파싱 실패.  
> 상류/하류 컨텍스트: 예외를 잡아 fallback 상태 유지(`modules/domain/agents/state_locked_arc_generator.py:323`), 하류 합성 단계 계속 진행.  
> **판정**: 안전.

### 5-C. 발견된 버그
- 없음

### 오탐 재검증 (Round 30)
- `modules/domain/agents/arc_corrector.py:495-506` 변경비율 우회 이슈는 여전히 **오탐**(대칭 비율 계산 확인).
- `modules/core/stage2_finalizer.py:188-245` `joint_docs` 누락 주장 건은 **오탐**(보강 블록 확인).
- `modules/domain/agents/director_ensemble.py:328` manuscript 슬라이싱 이슈는 **BUG 미확정 유지**(B-02 연동 조건 필요).

---
## Round 30 완료

## Round 31 — modules/core/stage0/reverse_expander.py + style_extractor.py + stage01_helpers.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 31/40

### 5-A. 파일 구조 요약
- `modules/core/stage0/reverse_expander.py:28` `class ReverseExpander`.
- `modules/core/stage0/reverse_expander.py:200` `def extract_bible(...)`.
- `modules/core/stage0/style_extractor.py:21` `class StyleGuide`.
- `modules/core/stage0/style_extractor.py:197` `class StyleExtractor`.
- `modules/core/stage0/style_extractor.py:209` `def extract_from_drafts(...)`.
- `modules/core/stage01_helpers.py:16` `class Stage01Helpers`.
- `modules/core/stage01_helpers.py:260` `def stage_0_extended(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage0/reverse_expander.py:79-90` JSON 파싱 실패 시 None  
> 실패 시나리오: 역설계 입력 손상 시 자동 복구 없이 추출 품질 급락.  
> 상류/하류 컨텍스트: 실패를 None으로 반환, 하류는 fallback 장르/기본값으로 진행.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/stage0/style_extractor.py:288-299` 통계 기반 문체 추정  
> 실패 시나리오: 샘플 편향 시 잘못된 style DNA 생성 가능.  
> 상류/하류 컨텍스트: 상류 curated sample을 사용하지만, 하류 writer prompt에 강하게 주입됨.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/stage01_helpers.py:550-597` 볼륨 생성 재시도 콜백  
> 실패 시나리오: 중간 실패 시 사용자 상호작용 흐름에서 상태 불일치 가능.  
> 상류/하류 컨텍스트: 콜백 기반으로 failure를 처리하며 stage 단위 재진입이 가능하도록 설계됨.  
> **판정**: 안전(운영형 인터랙션 설계).

### 5-C. 발견된 버그
- 없음

---
## Round 31 완료

## Round 32 — modules/core/quality_dashboard.py + pattern_tracker.py + manuscript_enhancer.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 32/40

### 5-A. 파일 구조 요약
- `modules/core/quality_dashboard.py:24` `class QualityDashboard`.
- `modules/core/quality_dashboard.py:106` `def record_validation(...)`.
- `modules/core/quality_dashboard.py:190` `def get_summary(...)`.
- `modules/core/pattern_tracker.py:19` `class PatternTracker`.
- `modules/core/pattern_tracker.py:137` `def analyze_manuscripts(...)`.
- `modules/core/manuscript_enhancer.py:34` `class ClicheBreaker`.
- `modules/core/manuscript_enhancer.py:182` `class SubtextExpander`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/quality_dashboard.py:58-63` line-by-line 로드 시 오류 무시  
> 실패 시나리오: 손상 레코드 누락이 누적되어 추세 왜곡 가능.  
> 상류/하류 컨텍스트: 개별 레코드 실패를 건너뛰는 대신 전체 로드는 유지.  
> **판정**: 안전(관측계 fail-soft 설계).

> **위험 지점 2**: `modules/core/pattern_tracker.py:449-463` DB save 실패  
> 실패 시나리오: 패턴 히스토리 저장 누락으로 다음 회차 sampling 품질 저하.  
> 상류/하류 컨텍스트: 예외를 로깅 후 False 반환, 하류는 메모리 내 report로 계속 동작.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/manuscript_enhancer.py:688-717` 평가 지표 산출  
> 실패 시나리오: heuristic score 과신 시 과도한 수정 지시 가능.  
> 상류/하류 컨텍스트: rule 기반 평가 결과를 advisory로 사용하며, 하류 최종 승인권은 director/validator에 있음.  
> **판정**: 안전.

### 5-C. 발견된 버그
- 없음

---
## Round 32 완료

## Round 33 — modules/core/adaptive_retry.py + feedback_system.py + relationship_tracker_factions.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 33/40

### 5-A. 파일 구조 요약
- `modules/core/adaptive_retry.py:70` `class AdaptiveRetryStrategy`.
- `modules/core/adaptive_retry.py:188` `def should_retry(...)`.
- `modules/core/adaptive_retry.py:214` `def get_retry_strategy(...)`.
- `modules/core/feedback_system.py:20` `class FeedbackSystem`.
- `modules/core/feedback_system.py:81` `def quantify_reject_feedback(...)`.
- `modules/core/feedback_system.py:364` `def generate_structured_arc_feedback(...)`.
- `modules/core/relationship_tracker_factions.py:42` `class RelationshipTrackerFactions`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/adaptive_retry.py:557-562` 실패 이력 보존 상한  
> 실패 시나리오: 에피소드 키가 대량일 때 오래된 실패 맥락이 빠르게 제거될 수 있음.  
> 상류/하류 컨텍스트: 메모리 보호를 위해 키 수 상한을 둠, 하류 정책이 최신 실패에 더 민감하게 반응.  
> **판정**: 안전(의도된 메모리 제한).

> **위험 지점 2**: `modules/core/feedback_system.py:224-229` 마지막 Arc 상태 참조  
> 실패 시나리오: 누락된 상태 필드에서 generic 피드백으로 과도 단순화 가능.  
> 상류/하류 컨텍스트: `.get(..., default)`로 크래시는 방지, 하류에서 보조 설명으로만 사용.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/relationship_tracker_factions.py:325-326` validation 실패 처리  
> 실패 시나리오: 관계 전이 거부가 잦을 경우 실제 스토리 전이가 과도 억제될 수 있음.  
> 상류/하류 컨텍스트: 전이 타당성 검증 실패 시 즉시 invalid 반환, 하류는 warning 중심으로 처리.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 33 완료

## Round 34 — modules/core/semantic_item_registry.py + genre_hud_manager.py + tree_of_thoughts.py

### 진행 통계 업데이트
- 총 발견: 11건 (CRITICAL: 0, HIGH: 8, MEDIUM: 3)
- 라운드 진행: 34/40

### 5-A. 파일 구조 요약
- `modules/core/semantic_item_registry.py:55` `class SemanticItemRegistry`.
- `modules/core/semantic_item_registry.py:203` `def register_item(...)`.
- `modules/core/semantic_item_registry.py:283` `def check_duplicate(...)`.
- `modules/core/genre_hud_manager.py:10` `class GenreHUDManager`.
- `modules/core/genre_hud_manager.py:73` `def update_physical_status(...)`.
- `modules/core/tree_of_thoughts.py:65` `class TreeOfThoughts`.
- `modules/core/tree_of_thoughts.py:183` `def explore(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/semantic_item_registry.py:187-201` 이름 유사도 계산  
> 실패 시나리오: 자모/짧은 문자열 중심 데이터에서 잘못된 유사 판정 가능.  
> 상류/하류 컨텍스트: union=0 가드가 있어 크래시는 방지(`modules/core/semantic_item_registry.py:193-194`), 하류 duplicate 판정 임계치에 의존.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/genre_hud_manager.py:25-31` 기본 이름 추출 예외 처리  
> 실패 시나리오: bible 구조 이상 시 기본 이름 사용으로 HUD 일관성 저하.  
> 상류/하류 컨텍스트: broad except로 fallback 이름 반환, 하류는 canonical map 기반 업데이트를 계속 수행.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/tree_of_thoughts.py:171-180` JSON parse 실패 fallback  
> 실패 시나리오: ToT 결과가 비구조 텍스트일 때 탐색 품질 저하.  
> 상류/하류 컨텍스트: parse 실패 시 단일 경로 fallback(`modules/core/tree_of_thoughts.py:325`)로 전환.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 34 완료

## Round 35 — modules/domain/agents/critic.py + unified_arc_validator.py + modules/core/agent_intelligence.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 9, MEDIUM: 3)
- 라운드 진행: 35/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/critic.py:22` `class Critic`.
- `modules/domain/agents/critic.py:40` `def critique_manuscript(...)`.
- `modules/domain/agents/unified_arc_validator.py:98` `class UnifiedArcValidator`.
- `modules/domain/agents/unified_arc_validator.py:109` `def validate(...)`.
- `modules/domain/agents/unified_arc_validator.py:339` `def _check_duplicate_items(...)`.
- `modules/core/agent_intelligence.py:48` `class AgentIntelligence`.
- `modules/core/agent_intelligence.py:227` `def get_few_shot_prompt(...)`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/unified_arc_validator.py:354`  
> `prev_items.update(item.strip() for item in acquired if item)`  
> 실패 시나리오: `acquired` list 원소가 dict면 `'dict' object has no attribute 'strip'`로 크래시.  
> 상류/하류 컨텍스트: 상류는 list 여부만 확인(`modules/domain/agents/unified_arc_validator.py:353`), 하류는 current item 비교 전에 바로 업데이트 수행.  
> **판정**: BUG.

> **위험 지점 2**: `modules/domain/agents/critic.py:61-67` JSON parse 실패 시 빈 content  
> 실패 시나리오: 실제 원고가 있어도 parse 실패 시 품질 진단이 과소화될 수 있음.  
> 상류/하류 컨텍스트: 예외를 잡아 빈 문자열로 진행, 하류는 최소 길이 체크(`modules/domain/agents/critic.py:67`) 후 경고 반환.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/agent_intelligence.py:436-567` 규칙/예시 기반 강화 프롬프트  
> 실패 시나리오: 도메인 텍스트 편향으로 특정 패턴 과적합 가능.  
> 상류/하류 컨텍스트: 장르별 exemplar/anti-pattern을 조합하며, 하류 실제 검증기는 별도로 존재한다.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그

### [HIGH][B-12] modules/domain/agents/unified_arc_validator.py:354 — dict 원소에서 `.strip()` 호출 크래시

**문제**: 이전 Arc의 `items_acquired`가 list[dict]인 경우 duplicate item 검사에서 즉시 예외가 난다.

**문제 코드**:
```python
acquired = prev.get("state_constraints", {}).get("items_acquired", [])
if isinstance(acquired, list):
    prev_items.update(item.strip() for item in acquired if item)
```

**수정 제안**:
```python
def _item_key(x):
    if isinstance(x, dict):
        return str(x.get("name", x.get("item", ""))).strip()
    return str(x).strip()
prev_items.update(_item_key(item) for item in acquired if item)
```

**확신도**: HIGH  
**FP 체크**: FP-1~FP-8 비해당. 재현(AttributeError) + 타입 계약 위반 근거 충족.

---
## Round 35 완료

## Round 36 — modules/core/stage3_orchestrator.py + pre_director_checklist.py + constitutional_checker.py + constraint_db.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 9, MEDIUM: 3)
- 라운드 진행: 36/40

### 5-A. 파일 구조 요약
- `modules/core/stage3_orchestrator.py:21` `class Stage3Orchestrator`.
- `modules/core/stage3_orchestrator.py:56` `def stage_3_batch_blueprinting(...)`.
- `modules/core/pre_director_checklist.py:84` `class PreDirectorChecklist`.
- `modules/core/pre_director_checklist.py:152` `def check(...)`.
- `modules/core/constitutional_checker.py:49` `class ConstitutionalChecker`.
- `modules/core/constitutional_checker.py:543` `def get_full_injection(...)`.
- `modules/core/constraint_db.py:46` `class ConstraintDB`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/stage3_orchestrator.py:163-169` notifier 호출 실패 비차단  
> 실패 시나리오: 운영 알림 손실.  
> 상류/하류 컨텍스트: 예외를 잡고 stage 로직은 계속 진행.  
> **판정**: 안전(부가 기능 비차단).

> **위험 지점 2**: `modules/core/pre_director_checklist.py:205-391` 체크리스트 임계값 기반  
> 실패 시나리오: 장르/작품별 편차를 충분히 반영하지 못하면 과검출/누락 가능.  
> 상류/하류 컨텍스트: blueprint/context를 읽어 보정하지만 정적 임계값 비중이 높다.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 3**: `modules/core/constraint_db.py:98-100` arc_no 캐스팅 실패 skip  
> 실패 시나리오: 잘못된 arc 데이터가 제약 DB에서 누락되어 후속 제약이 약화될 수 있음.  
> 상류/하류 컨텍스트: invalid arc는 조용히 건너뛰고 나머지 상태를 유지.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 36 완료

## Round 37 — modules/core/martial_manager.py + power_scaling.py + vec_memory.py + narrative_diversity.py + diversity_sampler.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 9, MEDIUM: 3)
- 라운드 진행: 37/40

### 5-A. 파일 구조 요약
- `modules/core/martial_manager.py:7` `class MartialManager`.
- `modules/core/power_scaling.py:65` `class PowerScalingTracker`.
- `modules/core/power_scaling.py:202` `def validate_growth(...)`.
- `modules/core/vec_memory.py:46` `class VecMemory`.
- `modules/core/vec_memory.py:235` `def retrieve_high_res_context(...)`.
- `modules/core/narrative_diversity.py:29` `class NarrativeDiversityEngine`.
- `modules/core/diversity_sampler.py:16` `class DiversitySampler`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/vec_memory.py:153-169` 임베딩 실패 fallback  
> 실패 시나리오: 긴 텍스트 분할 후에도 임베딩 실패 시 retrieval 품질 급락.  
> 상류/하류 컨텍스트: 예외를 잡아 `None` 반환, 하류는 벡터 컨텍스트 없이 기본 흐름으로 진행.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/power_scaling.py:455` 평균 성장 계산  
> 실패 시나리오: 기록 편향 시 성장 이상치 판정이 흔들릴 수 있음.  
> 상류/하류 컨텍스트: 최소 샘플 가드가 존재(`modules/core/power_scaling.py:446,451`), 하류는 advisory 중심.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/diversity_sampler.py:68-77` 샘플 생성 예외 처리  
> 실패 시나리오: 샘플 일부 실패 시 선택 다양성 축소.  
> 상류/하류 컨텍스트: 예외를 개별 샘플 단위로 흡수, 하류는 남은 샘플 중 best 선택.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 37 완료

## Round 38 — modules/domain/agents/three_phase_blueprint_generator.py + unified_blueprint_validator.py + *_compiler + preflight_checker.py + consensus_validator.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 9, MEDIUM: 3)
- 라운드 진행: 38/40

### 5-A. 파일 구조 요약
- `modules/domain/agents/three_phase_blueprint_generator.py:30` `class ThreePhaseBlueprintGenerator`.
- `modules/domain/agents/unified_blueprint_validator.py:40` `class UnifiedBlueprintValidator`.
- `modules/domain/agents/blueprint_constraint_compiler.py:22` `class BlueprintConstraintCompiler`.
- `modules/domain/agents/constraint_compiler.py:21` `class ConstraintCompiler`.
- `modules/domain/agents/preflight_checker.py:114` `class PreflightChecker`.
- `modules/domain/agents/consensus_validator.py:145` `class ConsensusValidator`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/domain/agents/unified_blueprint_validator.py:91-114` director 비교 선택 경로  
> 실패 시나리오: compare 결과 스키마 변경 시 선택/점수 필드 해석 오류 가능.  
> 상류/하류 컨텍스트: `_safe_int` 가드가 일부 존재하나 반환 키 계약에 강하게 의존.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/domain/agents/constraint_compiler.py:94-104` 아이템 수집  
> 실패 시나리오: 비문자 아이템이 문자열화되며 의미 정보(구조)가 손실될 수 있음.  
> 상류/하류 컨텍스트: None 방어는 충분하지만 정밀 추적보다 안정성 우선 설계.  
> **판정**: 안전.

> **위험 지점 3**: `modules/domain/agents/consensus_validator.py:206-265` 병렬 합의 예외 흡수  
> 실패 시나리오: 일부 투표 실패가 합의 신뢰도를 낮춤.  
> 상류/하류 컨텍스트: timeout/예외 시 완료된 결과만 사용, 하류에서 최소 투표 수 기준이 약함.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 38 완료

## Round 39 — modules/core/character_voice*.py + emotion_tracker.py + pacing_analyzer.py + foreshadow_tracker.py + information_diffusion.py

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 9, MEDIUM: 3)
- 라운드 진행: 39/40

### 5-A. 파일 구조 요약
- `modules/core/character_voice.py:68` `class CharacterVoiceTracker`.
- `modules/core/character_voice_profiler.py:48` `class CharacterVoiceProfiler`.
- `modules/core/emotion_tracker.py:11` `class EmotionArcTracker`.
- `modules/core/pacing_analyzer.py:79` `class PacingAnalyzer`.
- `modules/core/foreshadow_tracker.py:84` `class ForeshadowTracker`.
- `modules/core/information_diffusion.py:24` `class InformationDiffusion`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/character_voice_profiler.py:238` `return list(set(dialogues))`  
> 실패 시나리오: 대사 순서 정보가 사라져 화자 스타일 시계열 학습이 약화될 수 있음.  
> 상류/하류 컨텍스트: dedupe 목적은 달성하지만 하류 consistency 검사에서 시간성 맥락이 감소.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/pacing_analyzer.py:122-124` 짧은 텍스트 기본값 반환  
> 실패 시나리오: 아주 짧은 원고가 낮은 신뢰도 평가를 우회할 수 있음.  
> 상류/하류 컨텍스트: 최소 길이 가드로 크래시는 방지, 하류는 다른 validator에서 길이 차단을 수행.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/information_diffusion.py:44-69` 이벤트 로드 예외 처리  
> 실패 시나리오: 지식 확산 근거가 누락돼 NPC 지식 판정 품질 저하.  
> 상류/하류 컨텍스트: 예외를 warning 처리, 하류 should_npc_know는 보수적 기본값으로 동작.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

---
## Round 39 완료

## Round 40 — modules/core/lore_manager.py + semantic_cache.py + ab_testing.py + cross_agent_verifier.py + confidence_calibration.py + data_collector.py + 기타 소형 validators/agents

### 진행 통계 업데이트
- 총 발견: 12건 (CRITICAL: 0, HIGH: 9, MEDIUM: 3)
- 라운드 진행: 40/40

### 5-A. 파일 구조 요약
- `modules/core/lore_manager.py:6` `class LoreManager`.
- `modules/core/semantic_cache.py:65` `class SemanticCache`.
- `modules/core/ab_testing.py:17` `class ABTestingFramework`.
- `modules/core/cross_agent_verifier.py:51` `class CrossAgentVerifier`.
- `modules/core/confidence_calibration.py:65` `class ConfidenceCalibrator`.
- `modules/core/data_collector.py:17` `class DataCollector`.
- `modules/domain/agents/negative_example_injector.py:114` `class NegativeExampleInjector`.
- `modules/domain/agents/writer.py:34` `class Writer`.
- `modules/validation/retrospective_validator.py:12` `class RetrospectiveValidator`.
- `modules/validation/batch_validator.py:16` `class BatchValidator`.
- `modules/validation/action_scene_evaluator.py:10` `class ActionSceneEvaluator`.
- `modules/validation/advisory_validator.py:11` `class AdvisoryValidator`.
- `modules/validation/catharsis_timer.py:9` `class CatharsisTimer`.

### 5-B. 위험 지점 분석
> **위험 지점 1**: `modules/core/ab_testing.py:235` 표본 부족 통계 경로  
> 실패 시나리오: 샘플 수 부족에서 유의성 평가가 부정확해도 의사결정 문구가 출력될 수 있음.  
> 상류/하류 컨텍스트: 최소 샘플 조건은 체크하나, 하류 리포트 소비자가 이를 강제하지 않으면 오판 가능.  
> **판정**: RISK (Design Check Needed).

> **위험 지점 2**: `modules/core/cross_agent_verifier.py:139-156` LLM 결과 파싱 fallback  
> 실패 시나리오: parse 실패 시 준수 검증이 완화될 수 있음.  
> 상류/하류 컨텍스트: JSON parse 실패를 안전값으로 처리, 하류 quick_check와 병행해 일부 보완.  
> **판정**: 안전.

> **위험 지점 3**: `modules/core/data_collector.py:123-138,163-178` 파일 저장 실패 처리  
> 실패 시나리오: 학습 데이터 수집 손실.  
> 상류/하류 컨텍스트: 예외 시 cleanup 시도 후 종료, 본 생산 파이프라인과 분리되어 핵심 기능에는 비차단.  
> **판정**: RISK (Design Check Needed).

### 5-C. 발견된 버그
- 없음

### 오탐 재검증 (Round 40)
- Stage2 commit/rollback 관련 주장 중 `modules/core/stage2_finalizer.py:281-304`는 **오탐 유지**(실패 rollback + retry 경로 확인).
- `modules/domain/agents/arc_corrector.py:495-506` 변경비율 우회 이슈는 **오탐 유지**(현재 구현에서 우회 불가).
- `modules/validation/validation_orchestrator.py:960-1142` adaptive threshold 누수는 **RISK 유지**(구조상 우려 존재, 운영 설계 의도 검토 필요).
- 중복 병합 상태: B-06~B-12 신규 7건만 확정, 중복 제보는 기존 ID에 매핑.

---
## Round 40 완료

## 자체 검증 결과
- [x] 5-A 빈 라운드: 0개
- [x] 5-B 빈 라운드: 0개
- [x] FP 체크 누락: 0개
- [x] 라인 번호 누락: 0개
- [x] 총 위험 지점: 120개 이상 (Round 1~40 누적)
