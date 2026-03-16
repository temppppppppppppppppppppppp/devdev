<!-- [완료] -->
<\!-- [완료] -->
# Stage 4 메뉴 7번 — 아크 전환 Enter 스킵 가능성 3Pass 재감리 (최종판)

> 작성일: 2026-03-16
> 대상: 메뉴 7번 `_one_stop_pipeline_frontier_lag()` → 아크 간 Enter 프롬프트
> 질문: 아크 3개 분량 진행 시, 아크 간 Enter를 skip할 수 있는가?
> 재감리 사유: 1차 조사에서 `main_a.py`만 조사하여 `stage4_post_processor.py`의 하드코딩 `input()` 누락

---

## Pass 1: 호출 체인 완전 추적 (검증 완료)

### 1.1 실제 사용자 경험

```
메뉴 7번 선택
  ↓
"몇 개 Arc를 처리할까요?" → 사용자 "3" 입력
  ↓
Arc 1: Stage 2 설계 → Stage 3 블루프린트 → Stage 4 원고 (ep 1~N)
  ↓
"📋 Stage 4 집필 세션 종료."
"⏎ Enter를 누르면 메뉴로 돌아갑니다..."  ← Enter ①
  ↓
Arc 2: Stage 2 설계 → Stage 3 블루프린트 → Stage 4 원고
  ↓
"⏎ Enter를 누르면 메뉴로 돌아갑니다..."  ← Enter ②
  ↓
Arc 3: Stage 2 설계 → Stage 3 블루프린트 → Stage 4 원고
  ↓
"⏎ Enter를 누르면 메뉴로 돌아갑니다..."  ← Enter ③
  ↓
"[Enter] 메뉴로 돌아가기"  ← Enter ④ (frontier_lag 최종)
```

**3아크 = 4회 Enter** (아크별 1회 + 최종 1회)

### 1.2 호출 체인 (검증된 정확한 경로)

```
main_a.py L2503: choice == "7"
  → _one_stop_pipeline_frontier_lag()                    # L4148
    → L4278: 사용자 입력 "3" → requested_arc_limit = 3
    → L4299: for arc_offset in range(target_count):     # ← 3회 반복
      ├─ L4316-4361: Stage 2 아크 설계
      ├─ L4390-4444: Stage 3 블루프린트
      ├─ L4453: self._stage_4_v2_chief_writer(target_ep=...)
      │   → L4081: self._stage4_orch.stage_4_v2_chief_writer(...)
      │     → stage4_orchestrator.py L1661
      │       → L1680: self._run_interview_loop(session)
      │         → L678-920: while True 에피소드 루프
      │         → L922: self.post_processor.run_post_episode_tasks()  ★
      │           → stage4_post_processor.py L1402
      │             → L1412: input("⏎ Enter를 누르면 메뉴로 돌아갑니다...")
      │             → L1420-1426: 벡터 메모리 동기화 (noop)
      │
      └─ L4467: arcs_advanced += 1
    → L4511: if wait_for_menu_return: self._pause(...)   # 최종 Enter

```

### 1.3 Enter 프롬프트 소재지

| # | 위치 | 파일 | 라인 | 트리거 조건 |
|---|------|------|------|------------|
| ①②③ | `run_post_episode_tasks()` | `stage4_post_processor.py` | **L1412** | 매 아크 Stage 4 종료 시 (무조건) |
| ④ | `_pause()` | `main_a.py` | **L4511** | `wait_for_menu_return=True` (기본값) |

### 1.4 Enter 프롬프트 원문 코드 (검증 완료)

```python
# stage4_post_processor.py L1402-1427
def run_post_episode_tasks(self) -> None:
    """[4-R1-d] Session wrap-up: logs, vector sync."""
    self.ctx.ui.log(f"\n{'=' * 50}")
    self.ctx.ui.log("📋 Stage 4 집필 세션 종료.")
    try:
        import sys
        if sys.stdin and sys.stdin.isatty():
            input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")  # ← L1412 ★
        else:
            self.ctx.ui.log("   (비대화 모드 — 자동 진행)")
    except (EOFError, OSError):
        pass

    # 벡터 메모리 일괄 동기화 — 실제로는 noop
    if self.ctx.memory and self.ctx.memory.is_operational():
        try:
            self.ctx.ui.log("   🔄 벡터 메모리 일괄 동기화 중...")
            self.ctx.memory.sync_v20_drafts()  # ← drafts_path=None → 즉시 return
            ...
```

### 1.5 `run_post_episode_tasks()` 호출 지점 (전수)

| 호출 | 파일 | 라인 | 조건 |
|------|------|------|------|
| 정상 종료 | `stage4_orchestrator.py` | **L922** | 에피소드 루프 정상 완료 후 |
| 5회 실패 | `stage4_orchestrator.py` | **L886** | `_outcome.should_return=True` |

→ 2곳 모두 `skip_pause` 같은 분기 없이 **무조건 호출**.

---

## Pass 2: 사이드이펙트 완전 분석

### 2.1 `input()` 스킵 시 데이터 영향

| 항목 | 영향 | 근거 |
|------|------|------|
| DB 커밋 | **없음** | 모든 DB write는 `process_pass_result()` (L894-905)에서 완료. `run_post_episode_tasks()`보다 **앞에서** 실행됨 |
| 벡터 동기화 | **없음** | `sync_v20_drafts()` 인자 없이 호출 → `drafts_path is None` → 즉시 return (noop). L1171-1174 확인 |
| 파일 락 | **없음** | `run_post_episode_tasks()` 내 파일 I/O 없음 |
| 트랜잭션 | **없음** | 보류 중인 트랜잭션 없음 — 모두 이전 단계에서 완료 |
| 상태 정리 | **없음** | pause 중 정리되는 상태 없음 |
| 이벤트/시그널 | **없음** | `input()`은 raw stdin — 이벤트 시스템과 무관 |

### 2.2 데스크톱 앱 영향

| 항목 | 영향 | 근거 |
|------|------|------|
| Bridge Server | **없음** | L1412의 `input()`은 raw Python builtin — UIService 경유 안 함 → Bridge Server가 감지 불가 |
| WebSocket 이벤트 | **없음** | prompt_request 이벤트 미발생 |
| HTTP 응답 대기 | **없음** | `/run/{run_id}/input` 엔드포인트와 무관 |

### 2.3 타이밍/경합 조건

| 시나리오 | 위험도 | 분석 |
|----------|--------|------|
| Arc 1 완료 직후 Arc 2 시작 | **없음** | Stage 2는 새 아크 설계 — Stage 4와 독립적 |
| 메모리 압박 | **없음** | Stage4Orchestrator가 아크마다 새 세션 생성 (L1676) |
| DB 연결 | **없음** | SQLite 단일 연결, 순차 사용 |

### 2.4 기존 스킵 선례

| 선례 | 위치 | 설명 |
|------|------|------|
| `isatty()` 검사 | L1411 | 비대화 모드에서 이미 input() 스킵 — 문제 없음 증명 |
| 테스트 Mock | smoke tests L195, L189 | `run_post_episode_tasks` 자체를 MagicMock으로 교체 — 전체 스킵해도 문제 없음 증명 |
| `wait_for_menu_return` | L4153, L4511 | frontier_lag의 최종 Enter도 스킵 가능하도록 이미 설계됨 |

### 2.5 사이드이펙트 결론

**데이터 영향: ZERO.** `input()`은 순수 UX 목적. 스킵해도 어떤 데이터/상태에도 영향 없음.

---

## Pass 3: 수정 방안 + 사이드이펙트 최소화

### 3.1 설계 근본 원인

`run_post_episode_tasks()`는 **단독 Stage 4** (메뉴 4번) 용도로 설계:
- 세션 종료 = 메뉴 복귀 → Enter 프롬프트 자연스러움

**메뉴 7번 FrontierLag**에서 Stage 4를 **반복 호출**할 때:
- `run_post_episode_tasks()`가 아크마다 호출되어 **불필요한 Enter 반복**
- 메시지도 오해 유발: "메뉴로 돌아갑니다" → 실제로는 다음 아크로 진행

### 3.2 수정 방안 5개 비교

| 방안 | 변경 파일 | 변경 라인 | 사이드이펙트 | 기존 동작 보존 |
|------|-----------|-----------|-------------|---------------|
| **A. `skip_pause` 파라미터 전파** | 3개 | ~8줄 | 없음 | ✅ 기본값 False |
| **B. Stage4Context 슬롯 추가** | 3개 | ~5줄 | Context 오염 위험 | ⚠️ 세션 간 잔류 가능 |
| **C. system.yaml 설정** | 2개 | ~3줄 | 없음 | ✅ 설정 파일 |
| **D. PostProcessor 생성자 플래그** | 3개 | ~6줄 | lazy init 변경 | ⚠️ property 수정 |
| **E. 조건부 isatty 확장** | 1개 | ~2줄 | 단독 Stage4도 영향 | ❌ 메뉴 4도 스킵 |

### 3.3 권장: 방안 A — `skip_pause` 파라미터 전파 (가장 안전)

**이유**:
- 기본값 `False` → 기존 동작 100% 보존
- 명시적 의도 표현 (호출부에서 `skip_pause=True`)
- 메뉴 4번 (단독 Stage 4) 영향 없음
- 테스트 영향 없음 (기본값 유지)

**변경 계획**:

#### 파일 1: `modules/core/stage4_post_processor.py`

```python
# L1402: 파라미터 추가
def run_post_episode_tasks(self, *, skip_pause: bool = False) -> None:

# L1407-1416: 조건 분기
    if not skip_pause:
        try:
            import sys
            if sys.stdin and sys.stdin.isatty():
                input("   ⏎ Enter를 누르면 메뉴로 돌아갑니다...")
            else:
                self.ctx.ui.log("   (비대화 모드 — 자동 진행)")
        except (EOFError, OSError):
            pass
```

#### 파일 2: `modules/core/stage4_orchestrator.py`

```python
# L1661: 시그니처 추가
def stage_4_v2_chief_writer(self, limit_mode=False, *, target_ep=None, skip_pause=False):

# L886: 예외 경로
    self.post_processor.run_post_episode_tasks(skip_pause=skip_pause)

# L922: 정상 경로
    self.post_processor.run_post_episode_tasks(skip_pause=skip_pause)
```

#### 파일 3: `main_a.py`

```python
# L4008: wrapper 시그니처
def _stage_4_v2_chief_writer(self, limit_mode=False, *, target_ep=None, skip_pause=False):

# L4081: 위임 시 전달
    return self._stage4_orch.stage_4_v2_chief_writer(
        limit_mode=limit_mode, target_ep=target_ep, skip_pause=skip_pause
    )

# L4453: frontier_lag에서 호출 (메뉴 7)
    self._stage_4_v2_chief_writer(target_ep=frontier_plan["stage4_target"], skip_pause=True)

# L4697: one_stop에서 호출 (메뉴 6)
    self._stage_4_v2_chief_writer(target_ep=arc_ep_end, skip_pause=True)
```

### 3.4 사이드이펙트 최소화 체크리스트

| # | 체크 항목 | 결과 |
|---|----------|------|
| 1 | 메뉴 4번 (단독 Stage 4) 동작 변경? | ❌ 없음 — `skip_pause` 기본값 `False` |
| 2 | 기존 테스트 실패? | ❌ 없음 — Mock 대상, 파라미터 기본값 유지 |
| 3 | 데스크톱 앱 영향? | ❌ 없음 — raw `input()` 경로 변경 없음 |
| 4 | DB/파일 정합성? | ❌ 없음 — `input()` 이후 처리는 전부 noop |
| 5 | 벡터 메모리 동기화? | ❌ 없음 — `sync_v20_drafts()` 인자 없이 호출 = noop |
| 6 | Stage4Context 오염? | ❌ 없음 — Context 슬롯 변경 없음 |
| 7 | 다른 호출 경로 (`_run_interview_loop` 내부)? | ❌ 없음 — L886, L922 두 곳만 변경, 둘 다 `skip_pause` 전파 |
| 8 | `wait_for_menu_return` (최종 Enter)과 충돌? | ❌ 없음 — 별도 경로 (L4511), 독립적으로 동작 |

### 3.5 수정 후 사용자 경험

```
메뉴 7번 → "3" 입력

Arc 1: Stage 2 → Stage 3 → Stage 4 ✅
   "📋 Stage 4 집필 세션 종료."
   (Enter 없이 즉시 계속)

Arc 2: Stage 2 → Stage 3 → Stage 4 ✅
   "📋 Stage 4 집필 세션 종료."
   (Enter 없이 즉시 계속)

Arc 3: Stage 2 → Stage 3 → Stage 4 ✅
   "📋 Stage 4 집필 세션 종료."
   (Enter 없이 즉시 계속)

📊 파이프라인 완료 보고
"[Enter] 메뉴로 돌아가기"  ← 최종 Enter 1회만 (wait_for_menu_return=True)
```

**4회 → 1회로 축소** (또는 `wait_for_menu_return=False` 시 0회)

---

## 부록: 코드 위치 색인 (검증 완료)

| 기능 | 파일 | 라인 | 검증 |
|------|------|------|------|
| Enter 프롬프트 (원본) | `stage4_post_processor.py` | L1412 | ✅ 직접 읽음 |
| `run_post_episode_tasks()` 정의 | `stage4_post_processor.py` | L1402-1427 | ✅ 전문 읽음 |
| PostProcessor 생성자 | `stage4_post_processor.py` | L21-22 | ✅ ctx만 받음 |
| 정상 경로 호출 | `stage4_orchestrator.py` | L922 | ✅ 직접 읽음 |
| 예외 경로 호출 | `stage4_orchestrator.py` | L886 | ✅ 직접 읽음 |
| Orchestrator post_processor lazy init | `stage4_orchestrator.py` | L234-239 | ✅ 직접 읽음 |
| `stage_4_v2_chief_writer()` 정의 | `stage4_orchestrator.py` | L1661 | ✅ 직접 읽음 |
| main_a wrapper | `main_a.py` | L4008-4081 | ✅ 직접 읽음 |
| frontier_lag 내 Stage 4 호출 | `main_a.py` | L4453 | ✅ 직접 읽음 |
| one_stop 내 Stage 4 호출 | `main_a.py` | L4697 | ✅ grep 확인 |
| frontier_lag 최종 Enter | `main_a.py` | L4511 | ✅ 직접 읽음 |
| 아크 수 입력 | `main_a.py` | L4278-4283 | ✅ TF-1 확인 |
| 아크 루프 | `main_a.py` | L4299 | ✅ TF-1 확인 |
| `sync_v20_drafts()` noop 확인 | `vec_memory.py` | L1171-1174 | ✅ 직접 읽음 |
| Stage4Context __slots__ | `stage4_context.py` | L47-83 | ✅ 직접 읽음 |
| 테스트 Mock | `run_stage4_smoke.py` / `test_l3_stage4_smoke.py` | L195 / L189 | ✅ grep 확인 |
