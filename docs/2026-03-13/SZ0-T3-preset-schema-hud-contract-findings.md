# SZ0-T3 Preset Schema & HUD Contract Findings

> 작성일: 2026-03-13
> 상태: 3pass complete
> 조사 모드: static / read-only / code-and-test verification / source-report cross-check / UTF-8 only
> 대상 파일:
>   - `modules/core/stage0/preset_registry.py` (739줄) — PRIMARY
>   - `modules/core/stage0/__init__.py` (810줄) — StageZeroManager integration

---

## Executive Summary

preset_registry.py는 전반적으로 견고하게 구현되어 있다. mutable default 보호(deepcopy), 중복 추가 방지, 타입 강제 fallback 등 주요 계약은 잘 지켜진다. 다만 다음 문제가 확인됐다:

- **P2 1건**: `_enforce_type()`의 list/dict 얕은 복사가 중첩 구조(nested list/dict)에서 공유 참조를 남긴다.
- **P2 1건**: `_INCOMPATIBLE` 맵이 3개 장르만 커버하여, 13개 장르 중 10개가 비호환 검증 없이 동적 감지된다.
- **P3 1건**: `__init__.py` L317의 한글 인코딩 깨짐 — UI 문자열이 mojibake 상태로 사용자에게 노출된다.
- **P3 1건**: `reputation` 필드명이 COMMON_PRESET과 composer GENRE_PRESET 양쪽에 존재하여 composer 활성화 시 common 정의가 silently 덮어써진다.
- **P3 1건**: `_parse_korean_number()`가 음수/소수점 입력을 처리하지 못해 예외 없이 잘못된 값을 반환할 수 있다.

최종 retained: P2 2건, P3 3건. P0/P1 없음.

---

## PASS 1 — 후보 수집

### 1-1. `_enforce_type()` list/dict 얕은 복사 (L537, L541)

- `list(value)`와 `dict(value)`는 1-depth shallow copy만 수행한다.
- 만약 `value`가 `[{"a": 1}]` 같은 nested structure면 내부 dict는 원본과 공유된다.
- `build_initial_hud()`와 `build_npc_template()`은 `copy.deepcopy(field_def.default)`를 사용하므로 안전하지만, `normalize_hud()`와 `normalize_npc()`가 LLM 출력을 `_enforce_type()`으로 변환할 때 shallow copy 경로를 탄다.
- 후보 심각도: P2

### 1-2. `_INCOMPATIBLE` 맵 불완전 (L613-617)

- `investment`, `wuxia`, `hunter` 3개 장르만 비호환 관계가 정의되어 있다.
- 13개 장르(wuxia, hunter, investment, fantasy, composer, cooking, alt_history, actor, sports, medical, romance, politics, military) 중 10개가 비호환 검증 없이 키워드 3개 매칭만으로 동적 활성화될 수 있다.
- 예: `medical` 장르 활성 상태에서 "수술", "환자" 등 일상적 단어가 포함된 `cooking` 콘텐츠가 `medical` 감지를 유발할 수 있다. 반대도 마찬가지.
- 후보 심각도: P2

### 1-3. `__init__.py` L317 한글 인코딩 깨짐

- L317: `print("\n  [????쒖젏 ?쎌엯 ?뺤콉]")` — "외부시점 삽입 정책" 또는 유사한 한글이 mojibake 상태.
- L325: `raw_choice = input(f"    ?좏깮 (湲곕낯: {default_index}): ").strip()` — "선택 (기본: ...)" 역시 깨짐.
- 사용자에게 직접 노출되는 UI 문자열이다.
- 후보 심각도: P3

### 1-4. `reputation` 필드 충돌 — COMMON vs composer

- COMMON_PRESET L38: `"reputation": FieldDefinition("reputation", "dict", {}, description="평판")`
- composer GENRE_PRESET L119-120: `"reputation": FieldDefinition("reputation", "dict", {"public": 0, "industry": 0, "critic": 0}, description="명성 (대중/업계/평론)")`
- `get_active_fields()` L487-491에서 `fields.update(self.GENRE_PRESETS[preset_name])`으로 genre preset이 common을 덮어쓴다.
- composer 장르에서는 의도적일 수 있으나, 다른 장르에서 common의 `reputation: dict({})`를 기대하는 코드가 있으면 타입/구조가 달라진다.
- NPC_GENRE_PRESETS의 medical에서도 `reputation`이 `str` 타입으로 재정의된다(L393).
- 후보 심각도: P3

### 1-5. `_parse_korean_number()` 엣지 케이스

- 음수 입력("-5억"): 마이너스 부호가 `char.isdigit()` false → 무시됨 → 5억으로 파싱.
- 소수점("3.5억"): `.`이 무시되어 `35억`으로 파싱될 수 있다.
- 빈 문자열/단위만 입력("원", "만"): `current=0, sub_total=0` → `char='만'` → `current=1` → total=10000. 단순 "원"은 0 반환.
- 후보 심각도: P3

### 1-6. `normalize_hud()` 타입 강제의 원칙 위반 여부 (P2-4 사전 배정)

- `_enforce_type()`는 LLM 출력을 스키마 타입에 맞추는 정규화 레이어다.
- 대원칙 1("Python은 수집만, 판단은 LLM이")에 비추어: 타입 변환(str→int, 무효 enum→default)은 "포맷팅/전달" 범주에 해당하며, "오류인가?" 판단은 아니다.
- 단, enum 불일치 시 `copy.deepcopy(field_def.default)`로 silently fallback하는 것은 LLM이 의도한 값을 Python이 덮어쓰는 효과가 있다.
- 후보 심각도: P3 (원칙 위반이라기보다 silent data loss)

### 1-7. class-level mutable default in FieldDefinition

- COMMON_PRESET/GENRE_PRESETS의 FieldDefinition 인스턴스는 class attribute로 전역 공유된다.
- `default` 필드에 `{}`, `[]` 같은 mutable 값이 들어 있다.
- 그러나 모든 소비 경로가 `copy.deepcopy(field_def.default)` 또는 `_enforce_type()`을 거치므로 직접 변조 경로는 없다.
- 후보 심각도: 오탐 후보

### 1-8. `to_json()`/`from_json()` 라운드트립

- `to_json()`은 `base_genre`, `active_presets`, `discovered_fields`를 직렬화한다.
- `from_json()`은 `cls(base_genre=...)`로 새 인스턴스를 만들고 `activate_preset()`으로 순회한다.
- `__init__`이 이미 common + base_genre를 추가하므로, JSON의 active_presets에 추가 장르가 있을 때만 append된다. 순서는 보존된다.
- `discovered_fields`는 `_valid_keys` 필터링으로 안전하게 복원된다.
- 후보 심각도: 오탐 후보 (정상 동작)

### 1-9. 장르 프리셋 Python 하드코딩 (P3-11 사전 배정)

- 모든 장르 프리셋(GENRE_PRESETS, NPC_GENRE_PRESETS, FIELD_ALIASES 등)이 Python dict로 하드코딩되어 있다.
- 외부 config(YAML/JSON)가 아니므로 장르 추가/수정 시 코드 변경이 필요하다.
- 현재 10개 장르가 안정화되어 있고 "동적 장르 확장 폐기"가 확정되었으므로(CLAUDE.md), 실질적 위험은 낮다.
- 후보 심각도: P3 → 오탐 후보 (설계 의도)

---

## PASS 2 — 교차 검증

### 2-1. 1-1 (shallow copy) 검증

- `tests/test_sweep39.py:14-17`은 `_enforce_type` 내부에 `copy.deepcopy(field_def.default)`가 2회 이상 있는지만 검사한다. 이는 fallback 경로(exception/enum mismatch)의 deepcopy를 확인하는 것이지, 정상 경로의 `list(value)` / `dict(value)` shallow copy는 검증하지 않는다.
- 실제 호출 경로: `reverse_expander.py:410` → `normalize_hud()` → `_enforce_type()` — LLM이 반환한 nested dict/list가 shallow copy만 된다.
- `story_expander.py:227` → `build_initial_hud()` → `copy.deepcopy(field_def.default)` — 이 경로는 안전하다.
- **판정: retained P2**. 정상 타입 매칭 경로에서 nested 구조가 shallow copy되어 caller와 normalized 결과가 내부 객체를 공유한다.

### 2-2. 1-2 (_INCOMPATIBLE 불완전) 검증

- `state_tracker.py:310`이 유일한 `detect_new_genre()` 호출자.
- 키워드 기반 감지이므로 false positive 가능성은 항상 존재하나, `_INCOMPATIBLE`이 이를 완화하는 유일한 가드다.
- 현재 3/13 장르만 커버 → 나머지 10개 장르 조합에서 false positive 발동 시 불필요한 프리셋이 활성화되어 HUD 스키마가 오염될 수 있다.
- 다만 `matches >= 3` 임계값이 있고, 실제 운영은 단일 장르 프로젝트가 대부분이므로 발동 확률은 낮다.
- **판정: retained P2** (가드 커버리지 부족, 발동 시 HUD 스키마 오염 가능).

### 2-3. 1-3 (인코딩 깨짐) 검증

- `__init__.py` L317, L325의 문자열은 EUC-KR/CP949 인코딩된 바이트가 UTF-8로 해석된 전형적 mojibake다.
- `show_protagonist_config_menu()` 내부에서 직접 사용자에게 `print()`/`input()`으로 노출된다.
- 주변 코드(L303-316)의 한글은 정상이므로, 이 섹션만 잘못된 인코딩으로 저장된 것으로 보인다.
- MRL-T3 등 기존 문서에서 이 이슈를 다루지 않는다.
- **판정: retained P3**.

### 2-4. 1-4 (reputation 충돌) 검증

- `get_active_fields()` 구현상 genre preset이 common을 덮어쓰는 것은 의도된 설계다(L485-491 주석).
- 그러나 `reputation`이 common에서는 `dict({})`, composer에서는 `dict({"public": 0, ...})`, NPC medical에서는 `str("")`로 타입 자체가 다르다.
- `_enforce_type()`에서 타입 불일치 시 해당 타입으로 강제 변환하므로, common `reputation: {}`를 기대하는 코드에 composer의 `reputation: {"public": 0, ...}`가 들어가도 dict→dict으로 통과한다. 하지만 NPC medical의 `str` 재정의는 `normalize_npc()`에서 dict 입력을 `str()`로 변환해 데이터 손실 가능.
- **판정: retained P3** (silent 타입 변경으로 인한 잠재적 데이터 손실).

### 2-5. 1-5 (한글 숫자 파싱) 검증

- `_parse_korean_number()`는 `_enforce_type()`의 `int` 변환 경로에서만 호출된다.
- LLM 출력에서 "50억", "1000만원" 등의 문자열을 int로 변환하는 것이 주 용도.
- 음수("-5억" → 5억)는 투자물 장르에서 부채/손실 표현 시 부호 손실.
- 소수점은 int 타입 필드이므로 "3.5억"이 오는 것 자체가 LLM 스키마 불일치이나, graceful하게 처리하지 않는다.
- **판정: retained P3** (부호 손실은 투자물 장르에서 의미 왜곡 가능).

### 2-6. 1-6 (타입 강제의 원칙 위반) 재평가

- `_enforce_type()`의 역할은 LLM 출력 정규화이며, 대원칙 1의 "포맷팅/전달"에 해당한다.
- enum fallback(무효값→default)은 silent이지만, 이는 LLM 스키마 준수 실패에 대한 방어적 처리로 볼 수 있다.
- Director가 원고 품질을 판정하는 경로와 무관하며, HUD 데이터 정규화에 국한된다.
- **판정: 오탐 제거**. 원칙 위반 아님.

### 2-7. 1-7 (class-level mutable default) 재평가

- 모든 소비 경로(`build_initial_hud`, `build_npc_template`, `_enforce_type` fallback)가 `copy.deepcopy()`를 거친다.
- class attribute의 FieldDefinition.default를 직접 변조하는 코드 경로가 없다.
- **판정: 오탐 제거**. 보호됨.

### 2-8. 1-8 (round-trip) 재평가

- `from_json()`에서 `__init__`이 이미 common + base_genre를 추가한 뒤 JSON의 active_presets를 순회하므로, 추가 프리셋만 append된다.
- `activate_preset()`의 중복 방지 로직(L471)이 정상 동작한다.
- `discovered_fields` 복원도 `_valid_keys` 필터로 안전하다.
- **판정: 오탐 제거**. 정상 동작.

### 2-9. 1-9 (Python 하드코딩) 재평가

- CLAUDE.md에서 "동적 장르 확장 폐기" 확정. 10개 장르 안정화 상태.
- 하드코딩은 의도된 설계 결정이다.
- **판정: 오탐 제거**. 설계 의도.

### MRL-T3 교차 검증

- **MRL-T3-001 (P1)**: genre/preset truth-source split — 본 감사 범위와 직접 겹치지 않음. preset_registry 내부 계약이 아니라 boot 경로의 바인딩 문제. 재오픈하지 않음.
- **MRL-T3-002 (P2)**: destructive recovery partial-success masking — 본 감사 범위 밖(project_service 경로). 재오픈하지 않음.

---

## PASS 3 — 최종 확정 Findings

### [SZ0-T3-001] P2 | `_enforce_type()` 정상 경로 shallow copy — nested 구조 공유 참조

**Severity**: P2

**현상 요약**

`_enforce_type()` L537 `list(value)`, L541 `dict(value)`는 1-depth shallow copy만 수행한다. LLM이 반환한 nested 구조(예: `[{"종목": "삼성전자", "수량": 100}]`)가 `normalize_hud()` / `normalize_npc()`를 거치면, 정규화된 결과와 원본 raw_hud가 내부 객체를 공유한다. caller가 원본을 변경하면 정규화 결과도 오염된다.

**코드 근거**

- `preset_registry.py:537`: `return list(value)` — list 원소가 dict/list면 공유
- `preset_registry.py:541`: `return dict(value)` — dict value가 mutable이면 공유
- `preset_registry.py:506-521`: `normalize_hud()` → `_enforce_type()` 호출
- `preset_registry.py:669-682`: `normalize_npc()` → `_enforce_type()` 호출
- `reverse_expander.py:410`: `self.preset_registry.normalize_hud(result["hud_snapshot"])` — 실제 호출 경로

**기존 테스트 상태**

- `tests/test_sweep39.py:14-17`: `_enforce_type` 내 `copy.deepcopy` 존재만 확인. 정상 타입 매칭 경로(list→list, dict→dict)의 shallow copy는 미검증.

**권장 후속 조치**

- `_enforce_type()`의 list/dict 정상 경로를 `copy.deepcopy(value)`로 변경.
- 또는 `normalize_hud()` / `normalize_npc()` 최종 반환 시 전체 deepcopy.

---

### [SZ0-T3-002] P2 | `_INCOMPATIBLE` 맵이 3/13 장르만 커버 — 동적 감지 false positive 미차단

**Severity**: P2

**현상 요약**

`detect_new_genre()` 내부의 `_INCOMPATIBLE` 맵(L613-617)이 `investment/wuxia/hunter` 3개 장르 조합만 정의한다. 나머지 10개 장르(fantasy, composer, cooking, alt_history, actor, sports, medical, romance, politics, military)는 비호환 관계가 없어, 키워드 3개 매칭만으로 프리셋이 자동 활성화된다.

**코드 근거**

- `preset_registry.py:613-617`: `_INCOMPATIBLE` 정의 — 3개 장르만 커버
- `preset_registry.py:622-628`: 비호환 셋에 없으면 키워드 매칭만으로 통과
- `state_tracker.py:310-319`: `detect_new_genre()` → `activate_preset()` → `refresh_tracking_fields()` 체인

**downstream 영향**

- false positive 활성화 시 HUD 스키마에 불필요한 장르 필드가 추가되어 LLM 프롬프트 토큰 낭비 및 HUD 오염.
- `matches >= 3` 임계값과 단일 장르 운영이 완화 요인이나, 예를 들어 `alt_history` + `politics` 키워드 겹침("왕위", "권력", "파벌")은 3개 이상 쉽게 매칭.

**권장 후속 조치**

- 최소한 의미적으로 겹치는 장르 쌍(`alt_history↔politics`, `medical↔cooking`, `fantasy↔hunter`)을 `_INCOMPATIBLE`에 추가.
- 또는 임계값을 4~5로 상향하고, 활성화 전 사용자 확인 경로 추가.

---

### [SZ0-T3-003] P3 | `__init__.py` L317, L325 한글 인코딩 깨짐 (mojibake)

**Severity**: P3

**현상 요약**

`show_protagonist_config_menu()` 내부에서 "외부시점 삽입 정책" 관련 UI 문자열이 mojibake 상태로 하드코딩되어 있다.

**코드 근거**

- `__init__.py:317`: `print("\n  [????쒖젏 ?쎌엯 ?뺤콉]")` — 의도 추정: "외부시점 삽입 정책" 또는 유사 한글
- `__init__.py:325`: `input(f"    ?좏깮 (湲곕낯: {default_index}): ")` — 의도 추정: "선택 (기본: ...)"
- 주변 L303-316의 한글은 정상 → 이 섹션만 잘못된 인코딩으로 저장됨

**권장 후속 조치**

- L317, L325의 문자열을 정상 한글로 복원.
- 추정 원문: `"[외부시점 삽입 정책]"`, `"선택 (기본: {default_index}): "`.

---

### [SZ0-T3-004] P3 | `reputation` 필드 충돌 — COMMON/composer/NPC medical 타입 불일치

**Severity**: P3

**현상 요약**

`reputation` 필드가 COMMON_PRESET(`dict({})`), composer GENRE_PRESET(`dict({"public": 0, ...})`), NPC_GENRE_PRESETS medical(`str("")`)에서 각각 다른 타입/구조로 정의된다. `get_active_fields()`의 `dict.update()` 시맨틱에 의해 genre preset이 common을 silently 덮어쓴다.

**코드 근거**

- `preset_registry.py:38`: COMMON `reputation: dict({})`
- `preset_registry.py:119-120`: composer `reputation: dict({"public": 0, ...})`
- `preset_registry.py:393`: NPC medical `reputation: str("")`
- `preset_registry.py:487-491`: `fields.update(...)` — later preset wins

**downstream 영향**

- composer 장르에서 COMMON의 빈 `reputation: {}`를 기대하는 downstream이 있다면 구조 불일치.
- NPC medical에서 `normalize_npc()` 시 dict 값이 `str()`로 변환되어 `"{'key': 'value'}"` 같은 문자열이 저장될 수 있다.

**권장 후속 조치**

- 장르 고유 필드는 고유 이름 사용(예: `composer_reputation`, `medical_reputation`).
- 또는 COMMON에서 `reputation` 제거하고 장르별로만 정의.

---

### [SZ0-T3-005] P3 | `_parse_korean_number()` 음수/소수점 미처리 — 부호 손실

**Severity**: P3

**현상 요약**

`_parse_korean_number()`가 음수 부호(`-`)와 소수점(`.`)을 무시한다. 투자물 장르에서 부채/손실을 "-5억"으로 표현할 경우 `500000000`(양수)으로 파싱되어 의미가 반전된다.

**코드 근거**

- `preset_registry.py:558`: `text.replace(",", "").replace(" ", "")` — `-` 미처리
- `preset_registry.py:573-574`: `char.isdigit()` — `-`, `.` 모두 false → 무시
- `preset_registry.py:526-529`: `_enforce_type()` int 경로에서 `_parse_korean_number()` 호출

**재현 시나리오**

- 입력: `"-5억"` → 파싱: `-` 무시, `5` + `억` → `500000000` (양수)
- 입력: `"3.5억"` → 파싱: `3` → `.` 무시 → `5` → `억` → `(0+5)*100000000` = `500000000` (3.5억이 아닌 5억)

**권장 후속 조치**

- 선행 `-` 부호 감지 후 최종 결과에 부호 적용.
- 소수점은 int 필드 특성상 경고 로그 후 반올림 처리.

---

## 오탐 제거 요약

| PASS 1 후보 | 판정 | 이유 |
|------------|------|------|
| 1-6: `_enforce_type()` 타입 강제의 원칙 위반 (P2-4 사전 배정) | 오탐 | 포맷팅/전달 범주에 해당. enum fallback은 방어적 정규화이며 Director 판정 경로와 무관. |
| 1-7: class-level mutable default | 오탐 | 모든 소비 경로가 `copy.deepcopy()`를 거침. 직접 변조 경로 없음. |
| 1-8: `to_json()`/`from_json()` 라운드트립 | 오탐 | `activate_preset()` 중복 방지 + `_valid_keys` 필터로 정상 동작 확인. |
| 1-9: Python 하드코딩 (P3-11 사전 배정) | 오탐 | "동적 장르 확장 폐기" 확정(CLAUDE.md). 10개 장르 안정화 상태에서 의도된 설계. |

---

## 사전 배정 이슈 판정 요약

| 사전 배정 ID | 판정 | 매핑 |
|-------------|------|------|
| P2-4: `normalize_hud()` 타입 강제의 원칙 위반 | 오탐 | 포맷팅 범주. 단, shallow copy 문제는 별도 SZ0-T3-001로 retained. |
| P2-5: `_INCOMPATIBLE` 불완전 | retained | SZ0-T3-002 (P2) |
| P3-9: `__init__.py` L317 인코딩 깨짐 | retained | SZ0-T3-003 (P3) |
| P3-11: Python 하드코딩 | 오탐 | 설계 의도 (동적 장르 확장 폐기 확정) |

---

## Coverage Gap Log

| 주제 | 현재 상태 | 필요한 추가 근거 |
|------|-----------|------------------|
| `_enforce_type()` nested structure shallow copy | `test_sweep39.py`가 deepcopy 존재만 확인 | list-of-dict, dict-of-list 입력에 대한 mutation isolation 테스트 |
| `_INCOMPATIBLE` 장르 쌍 | 테스트 부재 | `alt_history` + `politics` 키워드 겹침 시 false positive 발동 여부 테스트 |
| `_parse_korean_number()` 엣지 케이스 | 테스트 부재 | 음수, 소수점, 빈 문자열, 단위만 입력 등 boundary 테스트 |
| `reputation` 필드 충돌 시 downstream | 테스트 부재 | composer 활성화 후 `normalize_hud()`에 common 기대 구조 입력 시 동작 검증 |
| `normalize_npc()` + NPC medical `reputation: str` | 테스트 부재 | dict 입력이 `str()` 변환 시 데이터 형태 검증 |

---

## MRL-T3 교차 참조

- MRL-T3-001 (P1, genre/preset truth-source split): 본 감사 범위 밖. 재오픈하지 않음.
- MRL-T3-002 (P2, destructive recovery masking): 본 감사 범위 밖. 재오픈하지 않음.
- 두 건 모두 preset_registry 내부 계약이 아닌 boot/recovery 경로 문제이므로 본 문서와 중복 없음.

## 최종 판정

- 최종 retained finding: **5건**
  - P0: 0건
  - P1: 0건
  - P2: 2건 (SZ0-T3-001, SZ0-T3-002)
  - P3: 3건 (SZ0-T3-003, SZ0-T3-004, SZ0-T3-005)
- 사전 배정 4건 중 retained 2건, 오탐 2건.
- 본 문서는 `3pass complete` 상태이며, `template / not executed`가 아니다.
