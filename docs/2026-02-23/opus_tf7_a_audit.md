# TF-7-A 감사 보고서 — Stage0 모듈 교차 버그

## 감사 파일 목록
- `modules/core/stage0/__init__.py`
- `modules/core/stage0/preset_registry.py`
- `modules/core/stage0/style_extractor.py`
- `modules/core/stage0/reverse_expander.py`
- `modules/core/stage0/story_expander.py`
- `modules/core/stage01_helpers.py` (caller-callee 추적용)
- `modules/core/genre_guards/__init__.py` (Guard 연동 경로 확인)
- `modules/core/genre_guards/style_guard.py` (연동 의도 확인)
- `modules/core/genre_guards/work_guard.py` (연동 의도 확인)
- `modules/validation/consistency_validator.py` (Guard 소비자)
- `modules/validation/scoring_validator.py` (Guard 소비자)

## 발견 이슈 (총 3건)

### [TF-7-A-1] ReverseExpander DB 저장이 단일 트랜잭션으로 보호되지 않음 (HIGH)
**파일**: `modules/core/stage01_helpers.py`  
**줄**: `modules/core/stage01_helpers.py:362`  
**현재 코드**:
```python
db_result = stage0_manager._reverse_expander.persist_to_db(app.current_project)
```

**파일**: `modules/core/stage0/reverse_expander.py`  
**줄**: `modules/core/stage0/reverse_expander.py:684`, `modules/core/stage0/reverse_expander.py:690`  
**현재 코드**:
```python
result = {
    "manuscripts": self._save_manuscripts_to_db(ctx),
    "state_logs": self._save_state_logs_to_db(ctx),
    "episode_bibles": self._save_episode_bibles_to_db(ctx),
    "blueprints": self._save_blueprint_stubs(ctx),
    "arcs": self._save_arc_stubs(ctx),
}
```

**파일**: `modules/core/stage0/reverse_expander.py`  
**줄**: `modules/core/stage0/reverse_expander.py:722`, `modules/core/stage0/reverse_expander.py:768`, `modules/core/stage0/reverse_expander.py:851`, `modules/core/stage0/reverse_expander.py:894`, `modules/core/stage0/reverse_expander.py:959`  
**현재 코드**:
```python
ctx.db.conn.commit()
```

**Caller-callee 계약 추적**:
- Caller: `Stage01Helpers._s0_handle_reverse_engineering()` → `persist_to_db()` 호출
- Callee: `persist_to_db()` → `_save_*()` 5개 저장 함수
- 각 `_save_*()`가 개별 `commit()` 수행

**문제**:
- 저장 단위가 테이블별로 쪼개져 있어 중간 단계 실패 시 부분 커밋 상태가 남는다.
- 역설계 결과는 manuscripts/state_logs/episode_bibles/blueprints/arcs가 세트로 일관돼야 하는데 원자성이 보장되지 않는다.

**영향**:
- Stage 2/3/4가 참조하는 상태가 부분적으로만 저장되어 회귀/재시작 시 불일치가 발생할 수 있다.

**Bug-vs-intent 판단**:
- 의도적으로 fail-soft를 쓰더라도, 이 경로는 결과 세트 저장 경로이며 단일 트랜잭션 부재는 설계 의도보다 데이터 일관성 위반 영향이 더 크다.

**권장 수정 방향**:
- `persist_to_db()` 상위에서 단일 트랜잭션(`BEGIN`/`COMMIT`/`ROLLBACK`)으로 묶고, 하위 `_save_*()` 내부 커밋 제거.

---

### [TF-7-A-2] 다중 프리셋 활성 시 필드 충돌 해소 순서가 비결정적임 (MEDIUM)
**파일**: `modules/core/stage0/preset_registry.py`  
**줄**: `modules/core/stage0/preset_registry.py:457`, `modules/core/stage0/preset_registry.py:479`  
**현재 코드**:
```python
self.active_presets: set[str] = {"common"}
for preset_name in self.active_presets:
    if preset_name in self.GENRE_PRESETS:
        fields.update(self.GENRE_PRESETS[preset_name])
```

**파일**: `modules/core/stage0/__init__.py`  
**줄**: `modules/core/stage0/__init__.py:353`, `modules/core/stage0/__init__.py:369`  
**현재 코드**:
```python
available = [g for g in PresetRegistry.GENRE_PRESETS.keys() if g not in self.preset_registry.active_presets]
self.preset_registry.activate_preset(preset)
```

**Caller-callee 계약 추적**:
- Caller: `StageZeroManager.manage_presets()`에서 복수 preset 활성화 가능
- Callee: `PresetRegistry.get_active_fields()`에서 set 순회 + `fields.update()`로 머지

**문제**:
- `active_presets`가 `set`이므로 순회 순서가 안정적으로 고정되지 않는다.
- 동일 키가 여러 preset에 있을 때(예: `rank`, `wealth`, `network`) 마지막 update 우선권이 실행마다 달라질 수 있다.

**영향**:
- HUD 기본값/스키마가 실행 환경에 따라 달라져 재현성 저하 및 상태 추적 불안정이 발생할 수 있다.

**Bug-vs-intent 판단**:
- 복수 preset 활성화는 UI에서 허용된다. 그런데 우선순위 규칙이 코드/주석에 정의되지 않아 의도라고 보기 어렵다.

**권장 수정 방향**:
- `active_presets`를 순서 보장 구조(list)로 바꾸고, 충돌 시 우선순위 규칙(예: base_genre 우선, 최근 활성화 우선)을 명시적으로 적용.

---

### [TF-7-A-3] StyleGuide/WorkGuard 체인이 실제 검증 경로에 연결되지 않음 (HIGH)
**파일**: `modules/core/stage01_helpers.py`  
**줄**: `modules/core/stage01_helpers.py:342`, `modules/core/stage01_helpers.py:472`  
**현재 코드**:
```python
app.current_project.save_v20_anchor("style_guide", sg_data)
app.current_project.save_v20_anchor("style_guide", stage0_manager.style_guide.to_dict())
```

**파일**: `modules/validation/consistency_validator.py`  
**줄**: `modules/validation/consistency_validator.py:53`  
**현재 코드**:
```python
guard = create_genre_guard(genre)
```

**파일**: `modules/validation/scoring_validator.py`  
**줄**: `modules/validation/scoring_validator.py:91`  
**현재 코드**:
```python
return create_genre_guard(genre)
```

**파일**: `modules/core/genre_guards/__init__.py`  
**줄**: `modules/core/genre_guards/__init__.py:22`, `modules/core/genre_guards/__init__.py:32`, `modules/core/genre_guards/__init__.py:56`  
**현재 코드**:
```python
def create_genre_guard(genre_type):
    if genre_type == "wuxia":
        return WuxiaGuard()
    ...
    else:
        return WuxiaGuard()
```

**파일**: `modules/core/genre_guards/work_guard.py`  
**줄**: `modules/core/genre_guards/work_guard.py:7`  
**현재 코드**:
```python
Guard 합성 체인: GenreGuard → WorkGuard → StyleGuard
```

**Caller-callee 계약 추적**:
- Caller(생성): Stage0 경로에서 `style_guide`는 anchor에 저장됨
- Callee(소비): 주요 검증기(`ConsistencyValidator`, `ScoringValidator`)는 `create_genre_guard()`만 호출
- `create_genre_guard()`는 base guard만 반환하며 `StyleGuard/WorkGuard` 래핑 인자도 받지 않음

**문제**:
- 문서화된 Guard 합성 체인과 실제 런타임 경로가 불일치한다.
- Stage0에서 추출한 style/work 규칙이 검증 단계에서 적용되지 않아 silent 품질 저하 경로가 된다.

**영향**:
- anti_ai_patterns/forbidden_expressions/work guard 규칙이 실제 차단/감점에 반영되지 않는다.

**Bug-vs-intent 판단**:
- 저장 경로와 검증 소비 경로가 둘 다 존재하지만 연결이 빠져 있어, 미구현 누락으로 보는 것이 타당하다.

**권장 수정 방향**:
- `create_genre_guard()`에 `style_guide`, `work_guard_path` 인자를 추가하고 `GenreGuard -> WorkGuard -> StyleGuard` 래핑을 기본 경로로 통합.

## [FP] 오탐 목록
- `modules/core/stage0/reverse_expander.py:130` / `modules/core/stage0/reverse_expander.py:193`: 원고 읽기에서 `encoding="utf-8"` 명시 + cp949/replace 폴백 존재, 인코딩 누락 이슈 아님.
- `modules/core/stage0/style_extractor.py:732`: `json.loads` 실패 시 코드블록 재파싱 후 `{}` 폴백 존재, 파싱 예외 미처리 이슈 아님.
- `modules/core/stage0/preset_registry.py:697`: `to_json()`이 `ensure_ascii=False` 사용, 한글 직렬화 손실 이슈 아님.

## Risk (추가 확인 필요)
- `modules/core/stage0/story_expander.py:249` / `modules/core/stage0/story_expander.py:212`: KeyNPCs 생성 스키마에 `deceased` 기본값이 명시되지 않음.  
  다만 본 감사 범위에서 직접 확인한 소비자 경로에 `deceased` 필수 계약이 명확히 보이지 않아 `Bug`가 아닌 `Risk`로 분류.

## 요약 테이블
| 심각도 | 건수 |
|--------|------|
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 1 |
| LOW | 0 |
| FP | 3 |
| Risk | 1 |

