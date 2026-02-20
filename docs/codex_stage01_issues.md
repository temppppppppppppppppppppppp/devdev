# 📋 Codex Stage 0/1 이슈 리포트

> **생성일**: 2026-02-20  
> **대상 범위**: `modules/core/stage01_helpers.py` (1개) + `modules/domain/agents/analyst.py` (1개) + `modules/domain/agents/analyst_prompts.py` (1개)  
> **총 코드량**: ~2,921 LOC (3개 파일)

---

## 이슈 요약

| # | 심각도 | 파일 | 이슈 | 라인 |
|---|--------|------|------|------|
| 1 | 🔴 Critical | `analyst.py` | `plan_single_arc_v20()` 609줄 — #레거시 태그이나 직접 호출 경로 유지 | L439-L1047 |
| 2 | 🟠 Medium | `analyst.py` | content extraction 블록 ~45줄 복사-붙여넣기 (2회) | L500-546 ≡ L568-612 |
| 3 | 🟠 Medium | `analyst.py` | library loading 3중 fallback 동일 에러처리 3회 반복 | L623-662 |
| 4 | 🟠 Medium | `analyst.py` | `_get_current_genre()` genre 하드코딩 9분기 if-elif + 폴백 `"wuxia"` | L1405-1435 |
| 5 | 🟠 Medium | `stage01_helpers.py` | `stage_0_extended()` 209줄 God method (6-way if-elif) | L260-L468 |
| 6 | 🟠 Medium | `stage01_helpers.py` | blocking `input()` 15+회 — CLI 의존, 비동기/GUI 전환 불가 | 전역 |
| 7 | 🟡 Minor | `stage01_helpers.py` | `print()` vs `app.ui.log()` 혼용 | `phase_0_recovery` vs `stage_1_volumes` |
| 8 | 🟡 Minor | `stage01_helpers.py` | `phase_0_recovery` → `self.app._stage_0_extended()` 캡슐화 우회 | L60-L73 |
| 9 | 🟡 Minor | `analyst.py` | `_SafeDict` 메서드 내부 클래스 — 모듈 레벨로 이동 가능 | L738-L740 |
| 10 | 🟡 Minor | `analyst.py` | `_validate_arc_with_state_tracker()` 빈 리스트 리턴 스텁 | L1461-L1466 |

- **Critical**: 1건 / **Medium**: 5건 / **Minor**: 4건  
- **총 10건**

---

## 상세 분석

### 🔴 Critical

#### 이슈 #1 — `plan_single_arc_v20()` 609줄 (#레거시이나 여전히 호출)

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/analyst.py` |
| **위치** | L439 – L1047 (609줄) |
| **심각도** | 🔴 Critical |

**현황**:
```python
# L439-455: 시그니처 13개 인자
def plan_single_arc_v20(
    self, arc_no, vol_strategy, prev_block, curr_block, next_block,
    ep_start, prev_arc_context="", assets=None, full_roadmap="",
    assigned_seeds=None, feedback="", recent_patterns=None,
    protagonist_name=None, state_tracker=None,
):
```

하나의 메서드에 다음 8단계가 전부 포함:
1. 패턴 금지 메시지 생성 (L469-488)
2. 페이싱 계산 + content extraction (L490-617) — **이 중 ~45줄이 2회 반복**
3. 장르 라이브러리 로드 3중 fallback (L619-662)
4. 주인공 이름 결정 (L664-680)
5. HUD 컨텍스트 구축 (L682-704)
6. 데이터셋 조립 (L706-725)
7. retry_with_feedback 루프 + Self-Critic (L727-900)
8. 상태 검증 + Joint Docs 보정 + state_changes 보장 (L902-1047)

`#레거시` 태그가 붙어 있으나 `plan_batch_arcs_v25` (L1145)가 이 메서드를 직접 호출함.  
추가로 `FourPhaseArcGenerator` 실패 시 이 메서드로 fallback된다는 주석 문구는 있으나, 현재 Stage 2 실행 경로(`stage2_preflight.py`)에서 직접 fallback 호출은 코드 실측상 확인되지 않음.

**리팩토링 제안**:
- `_extract_content_parts(block)` 헬퍼로 L500-546 / L568-612 통합
- `_load_genre_library(genre)` 헬퍼로 L619-662 분리
- `_build_hud_context(state_tracker, ep_start)` 헬퍼로 L682-704 분리
- `_resolve_protagonist_name(protagonist_name)` 헬퍼로 L664-680 분리
- `_post_process_arc(final_arc_data, ...)` 헬퍼로 L902-1047 분리

---

### 🟠 Medium

#### 이슈 #2 — content extraction 블록 복사-붙여넣기

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/analyst.py` |
| **위치** | L500-546 ≡ L568-612 |
| **심각도** | 🟠 Medium |

**현황**: 동일한 content extraction 로직 (~45줄)이 메서드 내에서 2회 복사-붙여넣기됨:

```python
# === 첫 번째 (L500-546): 페이싱 계산용 ===
if isinstance(curr_block, dict):
    content_parts = []
    for key in ["context", "event_villain", "solution", "reward"]:
        if curr_block.get(key) and isinstance(curr_block.get(key), str):
            content_parts.append(str(curr_block[key]))
    content_obj = curr_block.get("content", {})
    # ... raw_data, genre_ext 처리 ...
    content_len = len(content_sample)

# === 두 번째 (L568-612): 분량 경고용 ===
if isinstance(curr_block, dict):
    content_parts = []  # 동일한 코드 반복
    for key in ["context", "event_villain", "solution", "reward"]:
        # ... 완전 동일 ...
```

5가지 구조(top-level, content nested, raw_data, genre_ext, title)를 모두 처리하는 코드가 **한 글자도 다르지 않게** 2회 작성됨.

**리팩토링 제안**:
```python
def _extract_content_parts(self, block: dict) -> tuple[list[str], int]:
    """Block에서 content 파츠 추출 + 총 길이 반환"""
    parts = []
    # ... 5가지 구조 1회만 구현 ...
    return parts, len(" ".join(parts))
```

---

#### 이슈 #3 — library loading 3중 fallback 에러처리 반복

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/analyst.py` |
| **위치** | L623-662 |
| **심각도** | 🟠 Medium |

**현황**: 장르 라이브러리 로드 시 3가지 경로(장르별 → fallback → 빈 dict)에서 동일한 5-변수 할당 패턴이 3회 반복:

```python
# 패턴 1: L626-630 (장르 라이브러리 성공)
intro_lib_full = json.dumps(lib_data.get("intro_patterns", {}), ...)
dev_lib_full = json.dumps(lib_data.get("narrative_archetypes", {}), ...)
ending_lib_full = json.dumps(lib_data.get("ending_patterns", {}), ...)
trans_lib_full = json.dumps(lib_data.get("transition_patterns", {}), ...)
archetype_lib_full = dev_lib_full

# 패턴 2: L647-651 (기본 라이브러리 fallback) — 동일 코드
# 패턴 3: L635-636, L657-658, L661-662 (실패 시 빈 dict) — 동일 코드
```

**리팩토링 제안**:
```python
def _load_narrative_libraries(self, genre: str) -> dict[str, str]:
    """장르 라이브러리 로드 + fallback 체인"""
    for path in [self._get_genre_library_path(genre), self._get_fallback_lib_path()]:
        if path.exists():
            try:
                lib = json.loads(path.read_text(...))
                return {k: json.dumps(lib.get(v, {}), ...) for k, v in LIB_KEY_MAP.items()}
            except Exception:
                continue
    return {k: "{}" for k in LIB_KEY_MAP}
```

---

#### 이슈 #4 — `_get_current_genre()` genre 하드코딩 9분기

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/analyst.py` |
| **위치** | L1405-1435 |
| **심각도** | 🟠 Medium |

**현황**: Stage 3/4에서도 반복 지적된 genre 하드코딩 패턴이 Analyst에서도 동일하게 존재:

```python
def _get_current_genre(self) -> str:
    genre_name = self.context.guard.get_genre_name()
    if "hunter" in genre_name.lower() or "헌터" in genre_name:
        return "hunter"
    elif "invest" in genre_name.lower() or "투자" in genre_name:
        return "investment"
    elif "wuxia" in genre_name.lower() or "무협" in genre_name:
        return "wuxia"
    # ... 6개 더 ...
    return "wuxia"  # 기본값
```

9개 장르를 if-elif 체인으로 하드코딩 + fallback `"wuxia"`. Stage 3의 `blueprint_ensemble.py`와 동일 패턴.

**리팩토링 제안**: `GenreRegistry` 또는 `GENRE_ALIAS_MAP` 딕셔너리로 통합.

---

#### 이슈 #5 — `stage_0_extended()` 209줄 God method

| 항목 | 내용 |
|------|------|
| **파일** | `modules/core/stage01_helpers.py` |
| **위치** | L260-L468 (209줄) |
| **심각도** | 🟠 Medium |

**현황**: 6개 모드(컨셉→Bible, 역설계, Bible 임포트, Block 확장, 스타일 분석, 메뉴)를 500줄 단일 if-elif 체인으로 처리:

```python
def stage_0_extended(self, mode: int = 0):
    if choice == 1:      # 컨셉 → Bible (L303-305)
    elif choice == 2:    # 역설계 (L306-360) — 55줄
    elif choice == 3:    # Bible 임포트 (L361-363)
    elif choice == 4:    # Block 확장 (L364-408) — 45줄
    elif choice == 5:    # 스타일 분석 (L410-421)
    # ... 공통 후처리 L426-468
```

특히 `choice == 2` (역설계)는 vectordb 저장 + sqlite 저장 + stub 요약 출력을 37줄에 걸쳐 inline으로 처리.

**리팩토링 제안**: `_handle_concept_generation()`, `_handle_reverse_engineering()`, `_handle_bible_import()`, `_handle_block_extension()`, `_handle_style_analysis()` 5개 전용 핸들러로 분리.

---

#### 이슈 #6 — blocking `input()` 15+회

| 항목 | 내용 |
|------|------|
| **파일** | `modules/core/stage01_helpers.py` |
| **위치** | L54, L85, L98, L107, L116, L169, L214, L218, L228, L408, L420, L468, L481, L484, L493, L516, L650 |
| **심각도** | 🟠 Medium |

**현황**: `stage01_helpers.py` 전역에 걸쳐 17개의 blocking `input()` 호출:

| 용도 | 위치 | 예시 |
|------|------|------|
| 메뉴 선택 | L54, L481 | `input("선택 (기본: 1): ")` |
| 설정 입력 | L85, L98, L107, L116 | `input("  선택 (기본: 1): ")` |
| 확인/대기 | L169, L408, L420, L468, L484, L493, L516, L650 | `input("[Enter] 메뉴로 돌아가기")` |
| 데이터 입력 | L214, L218, L228 | `input("추가할 블록 수: ")` |

Stage 4의 `input()` 이슈(#4)와 동일 패턴. UI 레이어 분리 없이 비즈니스 로직에 직접 삽입.

**리팩토링 제안**: `app.ui.prompt("메시지", default="기본값")` 패턴으로 통합.

---

### 🟡 Minor

#### 이슈 #7 — `print()` vs `app.ui.log()` 혼용

| 항목 | 내용 |
|------|------|
| **파일** | `modules/core/stage01_helpers.py` |
| **위치** | `phase_0_recovery`(L29-169) vs `stage_1_volumes`(L473-650) |
| **심각도** | 🟡 Minor |

**현황**:
- `phase_0_recovery()`: 전부 `print()` 사용 (L33, L37, L42-52, L57, L81, ...)
- `stage_0_extended()`: 전부 `print()` 사용
- `extend_blocks()`: 전부 `print()` 사용
- `stage_1_volumes()`: `app.ui.log()` 사용 (L477, L480, L483, ...)

같은 클래스 내에서 출력 방식이 혼재. `app.ui.log()`가 파이프라인 표준인데 Stage 0 메서드들만 `print()` 사용.

---

#### 이슈 #8 — `phase_0_recovery` → `self.app._stage_0_extended()` 캡슐화 우회

| 항목 | 내용 |
|------|------|
| **파일** | `modules/core/stage01_helpers.py` |
| **위치** | L60-L73 |
| **심각도** | 🟡 Minor |

**현황**:
```python
# L60-73: 헬퍼가 다시 앱으로 콜백
elif p0_choice == "2" and STAGE0_AVAILABLE:
    self.app._stage_0_extended(mode=1)  # ← 앱의 private 메서드 호출
    return
```

`Stage01Helpers`가 `self.app._stage_0_extended()`를 호출하는데, 이 메서드는 다시 `Stage01Helpers.stage_0_extended()`를 호출할 가능성이 있음 (SovereignApp에서 위임 구조). 순환 의존 위험.

**리팩토링 제안**: `self.stage_0_extended(mode=1)` 직접 호출로 변경.

---

#### 이슈 #9 — `_SafeDict` 메서드 내부 클래스

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/analyst.py` |
| **위치** | L738-L740 |
| **심각도** | 🟡 Minor |

**현황**:
```python
def plan_single_arc_v20(self, ...):
    # ... 300줄 후 ...
    class _SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"
```

609줄 메서드 내부에 정의된 유틸리티 클래스. 매 호출 시 클래스가 재정의됨.

**리팩토링 제안**: 모듈 레벨 또는 `Analyst` 클래스 레벨로 이동.

---

#### 이슈 #10 — `_validate_arc_with_state_tracker()` 빈 리스트 스텁

| 항목 | 내용 |
|------|------|
| **파일** | `modules/domain/agents/analyst.py` |
| **위치** | L1461-L1466 |
| **심각도** | 🟡 Minor |

**현황**:
```python
def _validate_arc_with_state_tracker(self, arc_data: dict) -> list:
    """[V49.3] StateTracker를 사용하여 Arc 설계의 상태 일관성 검증"""
    # [V70] StateTracker는 preset_registry/llm_client 없이 의미 있는 검증 불가
    return []
```

주석에 따르면 의도적 비활성화이나, L935에서 여전히 호출되어 불필요한 함수 호출 오버헤드 발생. Dead code 후보.

---

## 전 스테이지 공통 패턴 (Stage 0/1 ~ Stage 4)

| 패턴 | Stage 0/1 | Stage 3 | Stage 4 |
|------|-----------|---------|---------|
| genre 하드코딩 | `_get_current_genre()` 9분기 | `blueprint_ensemble.py` L166/321 | — |
| 거대 메서드 | `plan_single_arc_v20` 609줄 | `generate()` 382줄 | `run()` 840줄 |
| blocking `input()` | 17회 | — | `run()` 내 1회 |
| content 로직 복사-붙여넣기 | ~45줄 × 2회 | TPE 보일러플레이트 × 2 | 20+ kwargs × 4회 |
| 출력 채널 혼재 | `print()` vs `app.ui.log()` | — | — |
