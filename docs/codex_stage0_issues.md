# Stage 0 개선 이슈 목록

> 점검일: 2026-02-20  
> 대상 파일: `modules/core/stage0/` 전체 (6개 파일, ~4,200 LOC)

---

## 🔴 Critical — 즉시 수정 권장

### 1. 장르 목록 3곳 불일치

**문제**: 장르 코드가 3곳에서 각각 다르게 정의되어 있어, 선택한 장르가 다운스트림에서 미지원 장르로 처리될 수 있음.

| 위치 | 파일:라인 | 포함 장르 | 누락 장르 |
|------|----------|----------|----------|
| `StageZeroManager.SUPPORTED_GENRES` | [\_\_init\_\_.py:L46-58](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L46-L58) | `romance`, `politics`, `military` | `actor`, `alt_history` |
| `analyze_concept()` 프롬프트 | [story_expander.py:L113](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py#L113) | `alt_history`, `actor` | `romance`, `politics`, `military` |
| `detect_genre()` 프롬프트 | [reverse_expander.py:L174-185](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L174-L185) | `alt_history`, `actor`, `romance` | `politics`, `military` |
| `GenreTypes` (SSOT) | [constants.py:L15-42](file:///c:/Users/User/Desktop/글도비/modules/core/constants.py#L15-L42) | `actor`, `alt_history` | `romance`, `politics`, `military` |

**영향**: 사용자 메뉴에서 `romance`/`politics`/`military` 선택 → `GenreTypes`에 없음 → HUD 빌드 실패, `HUDKeys.get_hud_root()` 폴백으로 MartialHUD 사용.

**수정 방향**: `GenreTypes.all()`을 SSOT로 삼고 나머지 3곳을 동기화. `romance`/`politics`/`military`가 실제 지원 장르인지 아닌지 판단 후 constants.py에 추가하거나 Stage 0 메뉴에서 제거.

---

### 2. 하드코딩된 LLM 모델명

**문제**: `_call_llm()` 메서드에 `"gemini-2.5-flash"` 하드코딩. `AIModels` 상수를 사용하지 않음.

| 파일:라인 | 하드코딩 값 | 사용해야 할 상수 |
|----------|-----------|----------------|
| [story_expander.py:L60](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py#L60) | `"gemini-2.5-flash"` | `AIModels.SUMMARY_MODEL` |
| [reverse_expander.py:L63](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L63) | `"gemini-2.5-flash"` | `AIModels.SUMMARY_MODEL` |

**영향**: `constants.py`에서 모델을 변경해도 Stage 0은 반영 안 됨.

> [!NOTE]
> `StyleExtractor._llm_call`([style_extractor.py:L665](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/style_extractor.py#L665))도 하드코딩이지만, 여기는 3단계 폴백(`3-pro → 2.5-pro → 2.5-flash`)이 구현되어 있어 단순 상수 교체보다 복잡.

---

## 🟡 Medium — 개선 권장

### 3. LLM 호출 재시도/폴백 없음

**문제**: `StoryExpander._call_llm`([L51-70](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py#L51-L70))과 `ReverseExpander._call_llm`([L54-73](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L54-L73))에 retry 로직이 전혀 없음.

```python
# 현재: 1회 실패 → 빈 문자열 즉시 반환
except Exception as e:
    logging.warning(f"[X] LLM 오류: {e}")
    return ""
```

**영향**: Bible/Treatment/Episode Bible 생성 중 일시적 API 오류(429, 503) 시 빈 결과로 진행 → 빈 Bible이나 빈 Treatment 생성됨.

**대조**: `StyleExtractor._llm_call`([L659-681](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/style_extractor.py#L659-L681))은 3단계 모델 폴백이 구현되어 있음.

---

### 4. 에피소드 콘텐츠 과도한 절삭

**문제**: 원고 분석 시 에피소드 콘텐츠를 과도하게 잘라서 후반부 정보가 누락됨.

| 메서드 | 파일:라인 | 절삭 | 문제 |
|-------|----------|------|------|
| `extract_episode_bibles()` | [reverse_expander.py:L315](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L315) | `content[:3000]` | 5000자+ 원고의 후반부 사건/NPC 누락 |
| `_extract_episode_bibles_with_progress()` | [reverse_expander.py:L573](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L573) | `content[:3000]` | 동일 코드 중복 |
| `extract_bible()` | [reverse_expander.py:L206](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L206) | 첫 3화만, 각 `[:2000]` | 주인공 능력/NPC가 후반 화수에서 등장하면 누락 |

**수정 방향**: `content[:3000]`을 `smart_truncate(content, 8000, 3000)` 등으로 교체하여 앞뒤 모두 보존. Bible 추출 시 샘플 범위를 첫 3화 + 중간 + 최근 3화로 확대.

---

### 5. Treatment 스켈레톤 60블록 단일 호출

**문제**: `_generate_skeleton(60)`([story_expander.py:L364-378](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py#L364-L378))이 60개 블록을 **1회 LLM 호출**로 생성 시도.

```python
return self._parse_json(self._call_llm(prompt, max_tokens=20000)) or []
```

**영향**: `max_tokens=20000`이지만 실제 모델 출력 한계에 근접. 후반 블록들이 잘리거나 빈 리스트 반환 가능.

**대조**: `_generate_details()`([L380-415](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py#L380-L415))은 10개씩 배치 처리하여 안정적. 스켈레톤도 동일하게 배치 처리 권장.

---

### 6. Arc/Blueprint 매직넘버 `5`

**문제**: Arc 번호 계산에 `5`가 하드코딩. `VolumeSettings.EPISODES_PER_ARC = 5` 상수가 존재하는데 사용하지 않음.

| 파일:라인 | 코드 | 사용해야 할 상수 |
|----------|------|----------------|
| [reverse_expander.py:L823](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L823) | `(ep_num - 1) // 5 + 1` | `VolumeSettings.EPISODES_PER_ARC` |
| [reverse_expander.py:L860](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L860) | `(max_ep - 1) // 5 + 1` | 동일 |
| [reverse_expander.py:L863](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L863) | `(arc_no - 1) * 5 + 1` | 동일 |
| [reverse_expander.py:L864](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L864) | `min(arc_no * 5, max_ep)` | 동일 |
| [reverse_expander.py:L879](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L879) | `(arc_no - 1) // 5 + 1` | `VolumeSettings.ARCS_PER_VOLUME` |

---

## 🟢 Minor — 참고

### 7. `print()` vs `logging` 혼용

| 파일:라인 | 사용 | 주변 코드 |
|----------|------|----------|
| [\_\_init\_\_.py:L252](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L252) | `print("\\n  원고 경로 입력...")` | 나머지 메서드들은 `logging.info()` |
| [\_\_init\_\_.py:L285](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/__init__.py#L285) | `print("\\n  Bible JSON 경로 입력:")` | 동일 |

→ `input()` 직전의 안내 메시지라 의도적일 수 있으나, 일관성을 위해 통일 권장.

### 8. `_parse_json` 중복 구현 (3곳)

| 파일:라인 | 구현 |
|----------|------|
| [story_expander.py:L72-84](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/story_expander.py#L72-L84) | 기본 JSON 파싱 |
| [reverse_expander.py:L75-94](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/reverse_expander.py#L75-L94) | dict+list 보존 버전, docstring에 `[G23]` 주석 |
| [style_extractor.py:L683-701](file:///c:/Users/User/Desktop/글도비/modules/core/stage0/style_extractor.py#L683-L701) | 자가치유 포함 버전 |

→ 공통 유틸로 추출 가능. `reverse_expander` 버전이 가장 범용적.
