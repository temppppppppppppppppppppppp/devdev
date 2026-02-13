# 코덱스 오더 — 오늘작업 잔여 4건 (2026-02-13 13:30)

> **배치**: 4개 태스크를 순서대로 실행
> **전제**: 이전 Step 1(base_agent, relationship_tracker, semantic_plot_guard), Step 2(hud_utils, prompt_builder, stage2 silent pass, PromptLoader) 완료 상태

---

## Task A: CLAUDE.md lazy init 메모 (SAFE, 1분)

### 변경 대상
`CLAUDE.md` L32

### 현재
```
- **약점**: NPC 연속성 추적 약함 (시나리오 24개 — 참고자료 3-C), 플롯 중복 감지 불안정 (Chain 1)
```

### 변경
```
- **약점**: NPC 연속성 추적 약함 (시나리오 24개 — 참고자료 3-C), 플롯 중복 감지 불안정 (Chain 1, lazy init + 재시도 1회 적용 완료)
```

### DoD
- L32에 `lazy init + 재시도 1회 적용 완료` 문구 추가됨

---

## Task B: bible_extractor.py Dead Code 삭제 확인 (SAFE, 2분)

### 배경
- `modules/domain/agents/bible_extractor.py` (598줄) — Dead Code로 판정됨
- `rg "bible_extractor" modules/` 결과: **자기 자신(L597 `create_bible_extractor`)** 외 import 0건
- 다른 모듈에서 import하거나 호출하는 곳 없음

### 작업
1. `rg "bible_extractor" modules/ --glob '!*bible_extractor*'` 으로 외부 참조 0건 재확인
2. `rg "bible_extractor" main_a.py` 로 메인 진입점 참조 확인
3. `rg "bible_extractor" tests/` 로 테스트 참조 확인
4. 외부 참조 0건 확인 후 → `modules/domain/agents/bible_extractor.py` 삭제
5. `modules/domain/agents/__pycache__/bible_extractor.cpython-*.pyc` 캐시도 삭제
6. `config/prompts/bible_extractor.yaml` 은 **삭제하지 않음** (다른 PromptLoader가 참조할 수 있음)
7. `python -m compileall modules/domain/agents -q` 에러 0건 확인

### DoD
- `bible_extractor.py` 파일 삭제됨
- 외부 참조 0건 확인 로그 남김
- `compileall` 에러 0건

> [!CAUTION]
> 만약 `rg` 결과에서 외부 참조가 1건이라도 발견되면 삭제하지 말고 보고만 할 것

---

## Task C: stage4_orchestrator.py voice/foreshadow silent pass → warning (MEDIUM, 10분)

### 변경 대상
`modules/core/stage4_orchestrator.py` L1355~1368

### 현재 코드 (L1355~1368)
```python
                        if V50_MODULES_AVAILABLE and self.app.character_voice:
                            try:
                                self.app.character_voice.analyze_manuscript(next_ep, final_manuscript)
                            except Exception:  # [V64.P4] OPTIONAL: voice analysis
                                pass
                            self.app.character_voice.save_to_json(os.path.join(logs_dir, "character_voice.json"))

                        if V50_MODULES_AVAILABLE and self.app.foreshadow_tracker:
                            # [V66] 원고에서 복선 자동 감지
                            try:
                                self.app.foreshadow_tracker.auto_detect_from_manuscript(next_ep, final_manuscript)
                            except Exception:  # [V66] OPTIONAL: foreshadow auto-detect
                                pass
                            self.app.foreshadow_tracker.save_to_json(os.path.join(logs_dir, "foreshadow.json"))
```

### 문제점
1. `except Exception: pass` → 실패해도 아무 로그 없음
2. **analyze_manuscript 실패 후에도 save_to_json 실행** → 빈/불완전 데이터 저장 가능
3. **auto_detect 실패 후에도 save_to_json 실행** → 동일 문제

### 변경 코드
```python
                        if V50_MODULES_AVAILABLE and self.app.character_voice:
                            try:
                                self.app.character_voice.analyze_manuscript(next_ep, final_manuscript)
                                self.app.character_voice.save_to_json(os.path.join(logs_dir, "character_voice.json"))
                            except Exception as e:
                                logging.warning(f"⚠️ [V64.P4-fix] character_voice 분석/저장 실패: {e}")

                        if V50_MODULES_AVAILABLE and self.app.foreshadow_tracker:
                            try:
                                self.app.foreshadow_tracker.auto_detect_from_manuscript(next_ep, final_manuscript)
                                self.app.foreshadow_tracker.save_to_json(os.path.join(logs_dir, "foreshadow.json"))
                            except Exception as e:
                                logging.warning(f"⚠️ [V66-fix] foreshadow 감지/저장 실패: {e}")
```

### 핵심 변경점
- `save_to_json`을 `try` 블록 안으로 이동 → 분석 실패 시 save 스킵
- `except Exception: pass` → `except Exception as e: logging.warning(...)` 로그 추가

### DoD
- `rg "except Exception:" modules/core/stage4_orchestrator.py` 로 L1355~1368 범위에 `pass` 없어야 함
- `python -m compileall modules/core/stage4_orchestrator.py -q` 에러 0건
- `save_to_json`이 `try` 블록 안에 위치 (분석 실패 시 save 스킵)

---

## Task D: genre_hud_manager.py 공통 함수 추출 (MEDIUM, 20분)

### 배경
`modules/core/genre_hud_manager.py` (1281줄)에 9개 장르 HUD 클래스 존재:
- HunterHUDManager (L53~168)
- FinanceHUDManager (L171~288)
- ComposerHUDManager (L291~412)
- CookingHUDManager (L415~537)
- JoseonHUDManager (L540~658)
- ActorHUDManager (L661~782)
- SportsHUDManager (L785~908)
- MedicalHUDManager (L911~1031)
- FantasyHUDManager (L1034~1158)

### 문제점
**모든 클래스의 `update_physical_status` 메서드가 99% 동일한 로직**:
1. `bible.get('{GenreName}HUD', ...)` 로 HUD 데이터 접근
2. `setdefault('{GenreName}HUD', {}).setdefault('Protagonist', {})`
3. `actual_truth` 추출
4. `canonical_map` 기반 키 매핑
5. 변경사항 있으면 `save_v20_anchor`

차이점은 오직 HUD 키 이름 (`'HunterHUD'`, `'FinanceHUD'`, ...) 뿐.

### 변경 계획
1. **부모 클래스 `GenreHUDManager`에 `hud_key` 속성 추가**:
```python
class GenreHUDManager(ABC):
    hud_key: str = ''  # 서브클래스에서 오버라이드
```

2. **부모에 공통 `update_physical_status` 구현**:
```python
    def update_physical_status(self, full_state_data: dict):
        """[V64.P4-refactor] 공통 상태 업데이트 — 서브클래스 중복 제거"""
        if not full_state_data:
            return []

        bible = self.context.master_bible.get('MasterBible', self.context.master_bible)
        pro = bible.setdefault(self.hud_key, {}).setdefault('Protagonist', {})
        actual = pro.setdefault('actual_truth', {})
        actual_in = full_state_data.get('actual_truth', full_state_data)

        changes = []
        for canonical_key, fallback_keys in self.canonical_map.items():
            val = None
            for incoming_key in fallback_keys:
                if incoming_key in actual_in:
                    val = actual_in[incoming_key]
                    break

            if val is not None:
                old_val = actual.get(canonical_key, "기록 없음")
                if str(old_val) != str(val):
                    actual[canonical_key] = val
                    changes.append(f"{canonical_key}: {old_val} → {val}")

        if changes:
            self.context.save_v20_anchor("bible", self.context.master_bible)

        return changes
```

3. **각 서브클래스에서**:
   - `hud_key` 설정: `hud_key = 'HunterHUD'`, `hud_key = 'FinanceHUD'`, ...
   - `update_physical_status` 메서드 **삭제** (부모에서 상속)
   - `__init__`에서 `self.hud_key` 설정하지 말고 **클래스 변수**로 선언

4. **`pro_root`에서도 `self.hud_key` 사용하도록 부모 공통화**:
   - 현재: `bible.get('HunterHUD', bible.get('hunter_hud', {}))` — 각 서브클래스마다 다른 키
   - 변경: `hud_key_alt` 속성 추가 (예: `hunter_hud`) 후 부모 공통 `pro_root` 구현
   - 단, `pro_root`는 기본값 구조가 장르마다 다름 → `_default_hud_data()` 추상 메서드 추가

5. **최종 구조**:

| 메서드 | 위치 | 비고 |
|--------|------|------|
| `update_physical_status` | 부모 `GenreHUDManager` | 9개 클래스에서 삭제 |
| `pro_root` | 부모 `GenreHUDManager` | `hud_key`, `hud_key_alt`, `_default_hud_data()` 사용 |
| `pro_data` | 부모 `GenreHUDManager` | 모든 서브클래스가 동일 (`return self.pro_root.get('actual_truth', self.pro_root)`) |
| `_default_hud_data` | 각 서브클래스 (추상) | 기본 HUD 딕셔너리 반환 |
| `get_v20_hud_report` | 각 서브클래스 | 장르별 고유 포맷 유지 |
| `get_critical_keys` | 각 서브클래스 | 장르별 고유 키 목록 유지 |

### DoD
- `rg "def update_physical_status" modules/core/genre_hud_manager.py` → **1건** (부모에만 존재)
- `rg "def pro_root" modules/core/genre_hud_manager.py` → **1건** (부모에만 존재)
- `rg "def pro_data" modules/core/genre_hud_manager.py` → **1건** (부모에만 존재)
- `python -m compileall modules/core/genre_hud_manager.py -q` 에러 0건
- 파일 줄 수 **800줄 이하** (현재 1281줄에서 약 400줄 감소 예상)
- `FantasyHUDManager.snapshot` 메서드는 **삭제하지 않음** (반드시 유지)

> [!IMPORTANT]
> `FantasyHUDManager`에만 있는 `snapshot` 메서드는 삭제 금지. 해당 클래스 고유이므로 유지해야 함.

---

## 실행 순서

```
1. Task A (CLAUDE.md lazy init 메모)              ~1분
2. Task B (bible_extractor.py 삭제)               ~2분
3. Task C (stage4 voice/foreshadow save 스킵)     ~10분
4. Task D (genre_hud_manager 공통 함수 추출)      ~20분
```

## 검증 명령 (전체 완료 후)

```bash
# 1. compileall 전체
python -m compileall modules/ -q

# 2. bible_extractor 삭제 확인
rg "bible_extractor" modules/ --glob '!*__pycache__*'

# 3. stage4 silent pass 확인
rg "except Exception:" modules/core/stage4_orchestrator.py

# 4. genre_hud 중복 제거 확인
rg "def update_physical_status" modules/core/genre_hud_manager.py
rg "def pro_root" modules/core/genre_hud_manager.py
rg "def pro_data" modules/core/genre_hud_manager.py

# 5. FantasyHUDManager.snapshot 유지 확인
rg "def snapshot" modules/core/genre_hud_manager.py
```
