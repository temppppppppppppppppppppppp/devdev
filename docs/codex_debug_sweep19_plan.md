# Debug Sweep 19 — 크래시 핸들러 + Falsy Zero + 데이터 손실

## Context

Sweep 18(7건) 완료 후, 5-에이전트 병렬 탐색으로 미탐색 대형 모듈 전면 스윕:
main_a.py, chief_writer, chief_writer_context, db_manager, project_manager, stage3_orchestrator, director_ensemble, repetition_guard, foreshadow_tracker.
수동 코드 검증으로 **확인된 실제 버그 8건** 정리.

---

## A-1 (HIGH): `main_a.py:1905` 크래시 핸들러에서 current_project null 접근

**파일**: `main_a.py:1905`

**문제**:
```python
except Exception as e:
    self.ui.log(f"🚨 [Critical Error] 시스템 오류 발생: {e}")
    import traceback
    error_log = self.current_project.paths.root / "logs" / "error.log"  # ← None 크래시
```
- 프로젝트 선택 전, 또는 `boot_v20_project` 실패 시 `self.current_project`가 None
- `None.paths.root` → `AttributeError` → 원래 에러가 묻힘
- **크래시 핸들러가 크래시** — 디버깅 불가능한 최악의 패턴

**수정**:
```python
except Exception as e:
    self.ui.log(f"🚨 [Critical Error] 시스템 오류 발생: {e}")
    import traceback

    try:
        if self.current_project and hasattr(self.current_project, "paths"):
            error_log = self.current_project.paths.root / "logs" / "error.log"
        else:
            error_log = Path("logs") / "error.log"
        error_log.parent.mkdir(exist_ok=True, parents=True)
    except Exception:
        error_log = Path("error.log")

    with open(error_log, "a", encoding="utf-8") as f:
```

**테스트**: `current_project=None` 상태에서 예외 발생 시 에러 로그가 `logs/error.log`에 안전하게 저장되는지 검증

---

## A-2 (MEDIUM): `db_manager.py:988-989` Falsy Zero — 카르마 데이터 덮어쓰기

**파일**: `modules/core/db_manager.py:988-989`

**문제**:
```python
mis = k.get("misunderstanding") or k.get("value") or k.get("point", 0)
obs = k.get("obsession") or k.get("point") or 0
```
- `misunderstanding=0`이면 falsy → `value` 키로 대체됨
- `k = {"misunderstanding": 0, "value": 5}` → `mis = 5` (의도: 0)
- `obsession=0`도 동일 패턴
- 카르마(NPC 관계) 수치가 오염될 수 있음

**수정**:
```python
mis = k.get("misunderstanding")
if mis is None:
    mis = k.get("value")
if mis is None:
    mis = k.get("point", 0)

obs = k.get("obsession")
if obs is None:
    obs = k.get("point")
if obs is None:
    obs = 0
```

**테스트**: `{"misunderstanding": 0, "value": 5}` 입력 시 `mis == 0` 검증

---

## A-3 (MEDIUM): `repetition_guard.py:68,112` 빈도수 데이터 소실 — threshold만 보고

**파일**: `modules/core/repetition_guard.py:68-69,112`

**문제**:
```python
# L68-69 — banned_phrases를 set으로 생성 → count 정보 소실
self.banned_phrases = {
    phrase for phrase, count in counter.items() if count >= self.threshold and len(phrase) > 5
}

# L112 — 실제 빈도수가 없으므로 threshold 상수를 대신 사용
"frequency": self.threshold,  # 이전 화에서 몇 번 나왔는지
```
- `banned_phrases`가 `set` → 빈도수 정보 소실
- 위반 보고에서 frequency가 항상 threshold 상수 → 실제 빈도를 알 수 없음
- Director에게 전달되는 경고 메시지의 정보 품질 저하

**수정**:
```python
# L68-69 — set → dict (빈도수 보존)
self.banned_phrases = {
    phrase: count for phrase, count in counter.items() if count >= self.threshold and len(phrase) > 5
}

# L112 — 실제 빈도수 사용
"frequency": self.banned_phrases[trigram],
```
- `trigram in self.banned_phrases` (L101) — dict에도 `in` 연산자 동일 동작 (키 검색)
- 기존 `self.banned_phrases` 사용처 전부 호환 (`for x in`, `if x in`, `not self.banned_phrases`)

**테스트**: `update_history` 후 `scan_manuscript` 반환의 frequency가 실제 출현 횟수와 일치하는지 검증

---

## A-4 (MEDIUM): `project_manager.py:424` `_normalize_seed_id` vid=None → TypeError

**파일**: `modules/core/project_manager.py:415,424`

**문제**:
```python
# L415 — None 키 포함 가능
valid_ids = {s.get("id"): s.get("id") for s in bible_seeds}
# s에 "id" 키가 없으면 → {None: None, "seed1": "seed1", ...}

# L424 — vid가 None이면 re.sub 크래시
clean_vid = re.sub(r"[^a-zA-Z0-9]", "", vid).upper()
# TypeError: expected string or bytes-like object, got 'NoneType'
```
- L440의 `sync_and_cleanup_seeds`는 `if s.get("id")` 필터 사용 (올바름)
- 동일 클래스 내 불일치

**수정** — L423 앞에 가드 추가:
```python
for vid in valid_ids:
    if not vid:
        continue
    clean_vid = re.sub(r"[^a-zA-Z0-9]", "", vid).upper()
```

**테스트**: `bible_seeds = [{"name": "A"}, {"id": "seed1"}]` (id 누락) 입력 시 크래시 없이 정상 동작 검증

---

## B-1 (LOW): `stage3_orchestrator.py:156,330` ctx.agents None 가드 누락

**파일**: `modules/core/stage3_orchestrator.py:156,330`

**문제**:
```python
# L156 — ctx.agents가 None이면 None.get() → AttributeError
if hasattr(ctx.agents.get("three_phase_bp"), "get_stats"):

# L330 — ctx.agents가 None이면 "x" in None → TypeError
if "state_extractor" in ctx.agents and ctx.current_project.arcs:
```
- `Stage3Context.__init__`에서 `agents=None` 기본값 (L46)
- 정상 흐름에서는 항상 초기화되지만, 에러 경로에서 None 가능

**수정**:
```python
# L156
if ctx.agents and hasattr(ctx.agents.get("three_phase_bp"), "get_stats"):

# L330
if ctx.agents and "state_extractor" in ctx.agents and ctx.current_project.arcs:
```

**테스트**: `ctx.agents=None`일 때 Stage 3 완료 통계/Entity Registry 경로에서 크래시 없는지 검증

---

## B-2 (LOW): `chief_writer.py:458` final_content None → len() 크래시

**파일**: `modules/domain/agents/chief_writer.py:458,476`

**문제**:
```python
# L458 — LLM이 {"content": null} 반환 시
final_content = critiqued_data.get("content", manuscript_content)
# → final_content = None (.get은 키 존재 시 값 반환, None이라도)

# L476 — len(None) → TypeError
"length": len(final_content),
```
- `critiqued_data.get("content", manuscript_content)` — 키 존재 + 값 null → None 반환
- 외부 except (L481)가 잡지만, 유효한 manuscript_content를 버리고 전체 후보 실패 처리
- LLM 호출 1회 낭비

**수정**:
```python
final_content = critiqued_data.get("content") or manuscript_content
```

**테스트**: `critiqued_data = {"content": None}` 입력 시 `manuscript_content`로 정상 폴백 검증

---

## B-3 (LOW): `main_a.py:847,2640` 빈 프로젝트 이름 가드 누락

**파일**: `main_a.py:847,2640`

**문제**:
```python
# L2638-2640 — _select_project()
if not projects:
    self.ui.log("❌ projects/ 폴더에 프로젝트가 없습니다.")
    return ""

# L847 — boot()에서 빈 문자열 가드 없음
project_name = self._select_project()
# project_name = "" → L866: boot_v20_project("") → 빈 이름 프로젝트 생성
```
- `projects/` 폴더가 비어있으면 `""` 반환
- `boot()` 가드 없이 계속 진행 → `.env` 로드 시도 + 빈 이름 프로젝트 부팅

**수정** — L848에 가드 추가:
```python
project_name = self._select_project()
if not project_name:
    self.ui.log("⚠️ 프로젝트가 선택되지 않았습니다. 종료합니다.")
    return
```

**테스트**: `_select_project()` 반환값이 빈 문자열일 때 boot() 조기 종료 검증

---

## B-4 (LOW): `director_ensemble.py:64,154,302` 성공/시작 이벤트가 WARNING 레벨

**파일**: `modules/domain/agents/director_ensemble.py:64,154,302`

**문제**:
```python
# L64 — 프로세스 시작 (warning → info)
logging.warning(f"🎭 [Director] {len(candidates)}개 후보 비교 중...")

# L154 — 후보 선택 성공 (warning → info)
logging.warning(f"🎯 [Director] 후보 {selected_idx + 1} 선택 ({decision}, 점수: {score})")

# L302 — 분량 통과 성공 (warning → info)
logging.warning(f"✅ [V60.97] 분량 통과 후보: {len(qualified_indices)}개 ...")
```
- 3개 모두 정상 동작 이벤트 → WARNING 부적절, INFO가 올바름

**수정**: 3곳 모두 `logging.warning` → `logging.info`

**테스트**: 소스 파일에서 해당 라인이 `logging.info` 호출인지 검증

---

## 수정 파일 총괄

| # | 파일 | 변경량 |
|---|------|--------|
| A-1 | `main_a.py` | ~8줄 수정 (크래시 핸들러 null guard) |
| A-2 | `modules/core/db_manager.py` | 2줄 → 8줄 (None 체크 전환) |
| A-3 | `modules/core/repetition_guard.py` | 2줄 수정 (set → dict + frequency) |
| A-4 | `modules/core/project_manager.py` | 2줄 추가 (None 가드) |
| B-1 | `modules/core/stage3_orchestrator.py` | 2줄 수정 (agents 가드) |
| B-2 | `modules/domain/agents/chief_writer.py` | 1줄 수정 (or 폴백) |
| B-3 | `main_a.py` | 3줄 추가 (빈 프로젝트 가드) |
| B-4 | `modules/domain/agents/director_ensemble.py` | 3줄 (warning→info) |

**총 ~25줄 변경**

---

## 오탐 제거 기록

| 보고 | 실제 | 이유 |
|------|------|------|
| `project_manager.py:873` max→min (rollback 방향) | ✗ 설계 | `max(origin_ep, current_ep - 3)` = 3화 이상 롤백 방지 제한. 의도된 안전 장치 |
| `main_a.py:2079,2083` shutdown null-check | ✗ 오탐 | `hasattr(None, "master_bible")` → False 반환. hasattr는 None 안전 |
| `director_auditor.py:397-402` story_context 누락 | ✗ 오탐 | `audit_manuscript` 시그니처에 story_context 파라미터 자체가 없음 |
| `chief_writer_context.py:1004` getattr default 우회 | ✗ 오탐 | L1003 `try:` 블록 내부 → AttributeError 시 except로 안전 처리 |
| `foreshadow_tracker.py:243-247` 상태 영구 변이 | ✗ 설계 | `is_overdue()` L74-79에서 status=PAYOFF/ABANDONED 필터 → 안전 |
| `project_manager.py:676 + db_manager.py:430` None 전파 | ✗ 설계 | 에피소드별 전체 행 교체 패턴. 부분 갱신이 아닌 완전 스냅샷 저장 |
| `chief_writer.py:304-307` Future.cancel() 무효 | ✗ 기존 | Sweep 3 G-2에서 이미 인지. 타임아웃으로 제한, cancel()은 best-effort |
| `prompt_loader.py:64-73` 캐시 미스 레이스 | ✗ 설계 | YAML 파일 로드는 멱등. 중복 로드 시 성능 낭비만 (데이터 손상 없음) |
| `db_manager.py` INSERT OR REPLACE 데이터 소실 | ✗ 설계 | 에피소드 단위 전체 행 저장 패턴. 호출자가 15개 필드 모두 전달 |

---

## 검증

```bash
PYTHONIOENCODING=utf-8 python -m pytest tests/test_stage3_orchestrator.py tests/test_chief_writer.py tests/test_repetition_guard.py -q -x
PYTHONIOENCODING=utf-8 python -m pytest tests/ -q -p no:capture
```

---

## Execution Status (2026-02-17)

- 완료: A-1 `main_a.py` critical-error null guard + boot empty-project guard
- 완료: A-2 `modules/core/db_manager.py` falsy-zero 보정 (`is None` 체인)
- 완료: A-3 `modules/core/repetition_guard.py` set -> dict + 실제 frequency 보고
- 완료: A-4 `modules/core/project_manager.py` `_normalize_seed_id`의 `vid` null guard
- 완료: B-1 `modules/core/stage3_orchestrator.py` `ctx.agents` null guard 2곳
- 완료: B-2 `modules/domain/agents/chief_writer.py` `final_content` fallback 보정
- 완료: B-3 `main_a.py` `_select_project()` 빈 문자열 반환 시 조기 종료
- 완료: B-4 `modules/domain/agents/director_ensemble.py` 정상 진행 로그 3건 `info`로 조정

### Tests Added/Updated

- 추가: `tests/test_sweep19.py`
  - main boot guard / critical handler guard
  - db_manager none-check chain
  - repetition_guard 실제 frequency 동작
  - project_manager seed-id null guard
  - stage3 orchestrator agents guard
  - chief_writer fallback line
  - director_ensemble info level line
- 수정: `tests/test_repetition_guard.py` (dict 기반 반환/상태에 맞게 기대값 갱신)

### Pytest Results

1. 1차 실행
   - `python -m pytest tests/test_stage3_orchestrator.py tests/test_chief_writer.py tests/test_repetition_guard.py tests/test_sweep19.py -q -x`
   - 결과: 1 failed, 109 passed
   - 원인: `build_banned_list([])`가 `set()` 반환
2. 수정 후 재실행
   - 동일 명령
   - 결과: 134 passed
3. 전체 실행
   - `python -m pytest tests/ -q -p no:capture`
   - 결과: 1963 passed, 68 xfailed, 1 warning
