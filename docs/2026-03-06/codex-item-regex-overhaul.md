# 코덱스 오더: 소지품 Regex 안전망 운영 체계

> 작성일: 2026-03-06
> 근거: `pipeline-run-audit-00_20260306.md` BUG-3 (소지품 regex 무협 편향)
> 범위: regex 접미사 SSOT 통합 + 자동 갭 수집 체계 구축
> 목표: 수동 열거의 한계를 인정하되, 갭을 자동으로 가시화하여 주기적으로 안전망 확장

---

## 0. 항목별 상태

| ID | 항목 | 심각도 | 상태 | 비고 |
|----|------|--------|------|------|
| 3-A | `get_item_suffixes()` SSOT 함수 | P1 | **완료** | `genre_schema_builder.py:97` 이미 구현됨 (`_ITEM_SUFFIX_MAP` 10장르 + `_common`) |
| 3-B | `get_unmatched_items()` 자동 갭 수집 | P1 | 미구현 | `semantic_item_registry.py`에 추가 필요 |
| 3-C | `item_suffix_gap_report()` 리포트 | P2 | 미구현 | `failure_analyzer.py`에 추가 필요 |
| 3-D | 소비자 6곳 SSOT 전환 | P2 | **부분 완료** | `arc_draft_validator`/`state_tracker_plots`/`constraint_compiler` 3곳 소비 중, 잔여 3곳 미전환 |
| 3-E | LLM 심사 + YAML 자동 반영 | P2 | 미구현 | Flash 배치 심사 → APPROVE 시 YAML 자동 append (아래 §3-E 참조) |

---

## 1. 현황 진단

### 문제 핵심
소지품/아이템 매칭이 **한국어 접미사 하드코딩 regex**에 의존:
```python
# 현재: 접미사 열거 방식 -- 장르 추가마다 수동 확장 필요
r"([가-힣]+(?:도|검|창|궁|패|인장))"
```

BUG-3 패치로 투자물 접미사 13종 추가하여 긴급 위험은 해소됨.

### 구조적 한계 (왜 regex 만으로 완벽히 커버 불가능한가)
- LLM은 예측 불가능한 아이템명을 생성함 ("워크스테이션" 추가하면 다음엔 "맥북프로")
- 접미사 열거는 본질적으로 **과거 데이터 기반** -- 미래 LLM 출력을 커버할 수 없음
- `items_acquired`를 LLM이 안 주는 경우도 있음 (실 로그에서 확인됨)
- 따라서 regex는 **보조적 안전망**일 뿐, 최종 판단은 Director가 담당

### regex의 실제 역할
```
구조적 데이터(equipment[], items_acquired[]) 있을 때 --> 직접 대조 (regex 불필요)
구조적 데이터 없을 때                              --> regex fallback (보조 안전망)
최종 판단                                         --> Director (대원칙 3)
```

regex는 "있으면 좋고, 못 잡아도 Director가 잡는" 2차 방어선.
따라서 **완벽한 커버리지**가 아닌 **점진적 확장**이 올바른 전략.

### 영향받는 파일 (6개, 14곳)

| # | 파일 | 위치 | 역할 | 현재 방식 |
|---|------|------|------|-----------|
| 1 | `state_tracker_plots.py` | L34-45 | `_RE_ITEM_ACQUIRE/LOSE` 정의 | 컴파일된 regex 4개 (무협 접미사 15종) |
| 2 | `state_tracker_plots.py` | L638-677 | `_regex_extract_major_items()` | regex fallback (major_items 빈 경우) |
| 3 | `arc_ensemble.py` | L652 | 소지품 계승 검사 | `re.findall` + 접미사 패턴 |
| 4 | `arc_ensemble.py` | L623 | 금지 아이템 추출 | 마커 regex |
| 5 | `arc_draft_validator.py` | L38-42 | `acquire_patterns` 정의 | regex 3개 (무협 접미사) |
| 6 | `arc_draft_validator.py` | L45-50 | `grant_patterns` 정의 | regex 4개 |
| 7 | `arc_draft_validator.py` | L52-57 | `weapon_keywords` 정의 | 하드코딩 리스트 |
| 8 | `arc_draft_validator.py` | L709 | `_validate_against_constraints()` | 마커 regex |
| 9 | `arc_draft_validator.py` | L751-815 | `_is_same_item()` | 접미사 strip + fuzzy match |
| 10 | `constraint_compiler.py` | L30-39 | acquire/grant 패턴 정의 | regex (무협 접미사) |
| 11 | `constraint_compiler.py` | L82-100 | `_collect_all_items()` | 구조적 + regex 이중 경로 |
| 12 | `prompt_builder.py` | L18-21 | `ITEM_PATTERNS` | regex 2개 |
| 13 | `constraint_db.py` | L198-201 | 패턴 정의 | regex 2개 |
| 14 | `action_scene_evaluator.py` | L400 | 무술 스킬 패턴 | 변경 불필요 (무협 전용) |

---

## 2. 전략: 자동 갭 수집 + 주기적 안전망 확장

### 핵심 원리

LLM이 생성하는 아이템은 `SemanticItemRegistry`에 이미 전부 수집되고 있음
(`register_item()` via `load_from_arcs()` -- equipment, items_acquired, distributed_items 3경로).

이 데이터를 현재 regex 접미사와 **자동 대조**하면, "regex가 못 잡는 아이템"이 자동으로 가시화됨.

### 운영 사이클

```
[자동 수집]  SemanticItemRegistry.items (매 Arc마다 축적)
     |
[자동 대조]  get_unmatched_items(genre) -- 현재 suffix 목록에 매칭 안 되는 아이템 추출
     |
[가시화]     로그 또는 리포트로 미매칭 아이템 목록 출력
     |
[LLM 심사]  주기적 배치 — 미매칭 아이템에서 접미사 후보 추출 → LLM 판정 (§3-E)
     |
[자동 확장]  APPROVE된 접미사를 item_suffixes.yaml에 자동 append (HIL 없음)
     |
[자동 반영]  get_item_suffixes(genre)가 YAML 로드 --> 소비자 6곳 자동 적용
```

### 기존 3-Tier와의 관계

```
Tier 1 (구조적 대조) -- equipment[]/items_acquired[] 직접 비교. 가능할 때 사용.
                       단, LLM이 안 줄 수 있으므로 항상 가용한 것은 아님.
Tier 2 (SSOT 접미사) -- get_item_suffixes(genre). 자동 수집 피드백으로 점진 확장.
Tier 3 (범용 regex)  -- Tier 1/2 불가 시 최후 fallback.
최종 판단            -- Director (대원칙 3). regex가 못 잡아도 여기서 잡음.
```

---

## 3. 구현 계획

### 3-A. `genre_schema_builder.py` -- 접미사 SSOT 함수 [완료]

`genre_schema_builder.py:42-121`에 이미 구현됨.

```python
# genre_schema_builder.py L42-71: 10장르 접미사 맵
_ITEM_SUFFIX_MAP: dict[str, list[str]] = {
    "_common": ["패", "권", "인장", "서", "부"],
    "wuxia": [...],  # 15종
    "investment": [...],  # 15종
    "hunter": [...],  # 11종
    # ... 총 10개 장르
}

# genre_schema_builder.py L97-121: SSOT 함수
def get_item_suffixes(genre: str = "") -> list[str]:
    """장르별 아이템 접미사 리스트 반환 (SSOT). 미지 장르 -> 전 장르 union."""
```

소비자 3곳에서 이미 호출 중: `arc_draft_validator`, `state_tracker_plots`, `constraint_compiler`.

### 3-B. `semantic_item_registry.py` -- 자동 갭 수집 메서드 추가 [미구현]

SemanticItemRegistry에 이미 축적된 아이템 데이터를 현재 suffix와 대조.

```python
def get_unmatched_items(self, genre: str = "") -> list[str]:
    """현재 suffix 목록에 매칭되지 않는 등록 아이템명 반환.

    3-E review_and_apply_suffixes()에서 호출.
    미매칭 아이템 → 빈출 접미사 추출 → LLM 심사 → YAML 자동 append.
    """
    from modules.core.genre_schema_builder import get_item_suffixes

    suffixes = get_item_suffixes(genre)
    unmatched = []
    for canonical in self.items:
        name = canonical.strip()
        if not name or len(name) < 2:
            continue
        if not any(name.endswith(s) for s in suffixes):
            unmatched.append(name)
    return sorted(set(unmatched))
```

**순환 import 주의**: `genre_schema_builder` → `semantic_item_registry` 역방향 의존 없음 확인 필요. 현재 `genre_schema_builder`는 순수 데이터 모듈이므로 안전.

### 3-C. `failure_analyzer.py` -- 갭 리포트 통합 [미구현]

FailureAnalyzer에 아이템 갭 리포트 메서드 추가 (기존 분석 유틸과 같은 위치).

```python
def item_suffix_gap_report(self, registry, genre: str = "") -> dict:
    """아이템 접미사 안전망 갭 리포트.

    Returns:
        {"total_items": int, "unmatched": list[str], "suggested_suffixes": list[str]}
    """
    unmatched = registry.get_unmatched_items(genre)
    # 미매칭 아이템에서 빈출 접미사 후보 추출 (끝 1~3글자)
    suffix_candidates = {}
    for name in unmatched:
        for length in (1, 2, 3):
            if len(name) > length:
                suffix = name[-length:]
                suffix_candidates[suffix] = suffix_candidates.get(suffix, 0) + 1
    # 2회 이상 등장한 접미사만 제안
    suggested = [s for s, cnt in sorted(suffix_candidates.items(), key=lambda x: -x[1]) if cnt >= 2]
    return {
        "total_items": len(registry.items),
        "unmatched_count": len(unmatched),
        "unmatched": unmatched[:30],  # 최대 30개
        "suggested_suffixes": suggested[:10],  # 최대 10개
    }
```

### 3-D. 소비자 6곳 SSOT 전환 [부분 완료]

| 파일 | 변경 | 상태 |
|------|------|------|
| `arc_draft_validator.py` | `get_item_suffixes(genre)` 호출 | **완료** |
| `constraint_compiler.py` | `get_item_suffixes()` 호출 | **완료** |
| `state_tracker_plots.py` | `get_item_suffixes()` 호출 (전 장르 union fallback) | **완료** |
| `prompt_builder.py` | ITEM_PATTERNS 확장 | 미전환 |
| `constraint_db.py` | 패턴 확장 | 미전환 |
| `arc_ensemble.py` | 소지품 계승 regex 확장 | 미전환 |

### 3-E. LLM 심사 + YAML 자동 반영 [미구현]

#### 문제
`suggested_suffixes`를 무조건 안전망에 추가하면 오탐 위험 (예: "프로"가 "맥북프로"에서 추출되면 "XX프로" 전부 매칭).

#### 해법: 주기적 배치 LLM 심사 → YAML 자동 append (HIL 없음)

**핵심 변경**: `_ITEM_SUFFIX_MAP` 하드코딩 → `config/settings/item_suffixes.yaml` YAML 외부화.
LLM 심사 APPROVE된 접미사를 YAML에 자동 append → 다음 실행부터 자동 로드.
사람 개입 없음. 판단은 LLM이 하고, Python은 결과를 파일에 쓸 뿐 (대원칙 1 준수).

#### YAML 구조

```yaml
# config/settings/item_suffixes.yaml
_common: ["패", "권", "인장", "서", "부"]
wuxia: ["도", "검", "창", "봉", "궁", ...]
investment: ["통장", "계약서", "인감", ...]
# ... 10장르
```

#### `get_item_suffixes()` 변경

```python
# genre_schema_builder.py
_SUFFIX_YAML = Path("config/settings/item_suffixes.yaml")

def get_item_suffixes(genre: str = "") -> list[str]:
    """YAML에서 장르별 접미사 로드 (SSOT)."""
    if _SUFFIX_YAML.exists():
        data = yaml.safe_load(_SUFFIX_YAML.read_text(encoding="utf-8")) or {}
    else:
        data = _ITEM_SUFFIX_MAP  # 폴백: 기존 하드코딩
    common = list(data.get("_common", []))
    genre_key = genre.lower().replace(" ", "")
    specific = data.get(genre_key, [])
    if not specific:
        specific = [s for k, v in data.items() if k != "_common" for s in v]
    return list(set(common + specific))
```

#### 트리거 조건

```
택 1 (자동):
  - 프로젝트 완료 시 (전체 Arc 생성 종료 후)
  - 누적 unmatched 아이템 10건+ 도달 시

※ 매 아이템 매칭마다 호출하지 않음 (비용/지연 비효율)
```

#### 심사 + 자동 반영 플로우

```python
def review_and_apply_suffixes(self, registry, genre: str = ""):
    """미매칭 아이템 → LLM 심사 → APPROVE 시 YAML 자동 append."""
    report = self.item_suffix_gap_report(registry, genre)
    if report["unmatched_count"] < 10:
        return  # 임계값 미달, 스킵

    # 후보 구성 (접미사 + 등장 예시)
    candidates = []
    for suffix in report["suggested_suffixes"]:
        examples = [n for n in report["unmatched"] if n.endswith(suffix)][:3]
        candidates.append({"suffix": suffix, "examples": examples, "count": len(examples)})

    # Flash 1회 배치 심사
    prompt = f"""다음은 웹소설 아이템 regex 안전망에 추가할 접미사 후보입니다.
각 후보에 대해 "일반적인 아이템/도구/장비의 접미사로 적합한가?" 판정해 주세요.

판정 기준:
- APPROVE: 아이템 카테고리를 나타내는 접미사 (예: "칼", "서", "증")
- REJECT: 고유명사/브랜드/우연의 일치 (예: "프로", "플러스", "맥스")

후보: {json.dumps(candidates, ensure_ascii=False)}
JSON 배열로 응답: [{{"suffix": "...", "verdict": "APPROVE"|"REJECT", "reason": "..."}}]
"""
    results = self._ask_flash(prompt)  # Flash 1회

    # APPROVE만 YAML에 자동 append
    approved = [r["suffix"] for r in results if r.get("verdict") == "APPROVE"]
    if approved:
        _append_to_suffix_yaml(genre, approved)
        logging.info("[ItemGap] YAML 자동 추가: genre=%s, suffixes=%s", genre, approved)
```

#### 비용/빈도 추정
- Flash 1회: ~$0.002 (후보 10개 기준)
- 빈도: 프로젝트당 0~1회 (unmatched 10건 미달 시 스킵)
- 총 추가 비용: 무시 가능
- HIL: **없음** (LLM 판단 → 자동 반영)

---

## 4. 운영 절차

### 4-1. 실파이프라인 실행 후

```python
# 실행 후 갭 확인 (main_a.py 종료 직전 또는 수동)
registry = app.semantic_item_registry
report = FailureAnalyzer(db).item_suffix_gap_report(registry, genre="investment")
logging.info("[ItemGap] total=%d, unmatched=%d, suggested=%s",
             report["total_items"], report["unmatched_count"],
             report["suggested_suffixes"])
```

### 4-2. 자동 안전망 확장 (HIL 없음)

프로젝트 완료 시 또는 unmatched 10건+ 도달 시 자동 실행:

1. `item_suffix_gap_report()` → 미매칭 아이템 + 빈출 접미사 후보 추출
2. `review_and_apply_suffixes()` → Flash 1회 배치 심사
3. APPROVE된 접미사 → `item_suffixes.yaml` 자동 append
4. 다음 실행 시 `get_item_suffixes(genre)`가 YAML 로드 → 자동 적용

### 4-3. 신규 장르 추가 시

1. `_ITEM_SUFFIX_MAP`에 장르 키 + 초기 접미사 리스트 추가
2. 테스트 파이프라인 1회 실행
3. 갭 리포트로 누락 접미사 보강
4. 이후 운영 사이클로 자연 확장

---

## 5. 조치 우선순위

| 순서 | ID | 심각도 | 설명 | 파일 | 상태 |
|------|-----|--------|------|------|------|
| 1 | 3-A | P1 | `get_item_suffixes()` SSOT 함수 | genre_schema_builder.py | **완료** |
| 2 | 3-B | P1 | `get_unmatched_items()` 자동 갭 수집 | semantic_item_registry.py | 미구현 |
| 3 | 3-C | P2 | `item_suffix_gap_report()` 리포트 | failure_analyzer.py | 미구현 |
| 4 | 3-D | P2 | 소비자 6곳 SSOT 전환 | 6파일 (3곳 완료) | 부분 완료 |
| 5 | 3-E | P2 | LLM 접미사 심사 게이트 | (신규 또는 failure_analyzer) | 미구현 |

---

## 6. 테스트 계획

| # | 테스트 | 검증 내용 |
|---|--------|-----------|
| 1 | `test_get_item_suffixes_per_genre` | 10개 장르별 접미사 반환 확인 |
| 2 | `test_get_item_suffixes_unknown_genre` | 미지 장르 시 전 장르 union 반환 |
| 3 | `test_unmatched_items_detects_gap` | "맥북프로" 등록 시 unmatched에 포함 |
| 4 | `test_unmatched_items_known_suffix` | "법인인감" 등록 시 unmatched에 미포함 |
| 5 | `test_gap_report_suggests_suffixes` | 동일 접미사 2회+ 등장 시 suggested에 포함 |
| 6 | `test_validator_genre_patterns` | 투자물/요리/스포츠 장르별 아이템 매칭 |
| 7 | `test_no_false_positive_title` | BUG-1 회귀 없음 확인 |
| 8 | `test_review_suffix_approve_reject` | LLM 심사 APPROVE/REJECT 분류 확인 |

---

## 7. 제약 사항

- **대원칙 1 준수**: Python은 아이템 수집/대조만, "이 아이템이 정합한가?" 판단은 LLM(Director)
- **대원칙 3 준수**: Validator의 검사 결과는 advisory only. REJECT 권한은 Director에게만
- **열거의 한계 인정**: regex 접미사는 영원히 완벽할 수 없음. 자동 갭 수집으로 점진 확장이 현실적 최선
- **하위 호환**: 기존 regex 경로는 유지. SSOT 전환은 소비자별 점진 적용
- **LLM 심사는 배치**: 매 매칭마다 호출하면 비용/지연 과다. 프로젝트 완료 시 또는 unmatched 10건+ 도달 시에만 실행
- **자동 반영**: LLM APPROVE → `item_suffixes.yaml` 자동 append. 판단은 LLM, 쓰기는 Python (대원칙 1 준수). HIL 없음
- **Director가 뚫리면 답 없음**: regex 안전망은 어디까지나 보조. Director가 최종 판단이고, Director가 놓치면 regex가 있든 없든 동일. 따라서 이 시스템에 과도한 완벽성을 기대하지 않음
- **`action_scene_evaluator.py` L400**: 무술 스킬 패턴은 무협 전용이 맞으므로 변경 불필요

---

## 8. 리스크

| 리스크 | 대응 |
|--------|------|
| SSOT 함수 미호출 시 기존 하드코딩 잔존 | 소비자별 점진 전환, 기존 코드도 작동은 함 |
| `get_unmatched_items()` 오탐 (고유명사) | 고유명사는 접미사 매칭 대상 아님, unmatched 맞음. LLM 심사(3-E)에서 REJECT |
| `suggested_suffixes` 노이즈 | 2회+ 빈출 필터 + LLM 심사 (2중 필터). Director가 뚫리면 여기도 뚫림 — 보조 수단의 한계 인정 |
| 장르별 접미사 과다 시 regex 성능 | 전 장르 union 최대 ~80종, re.compile 1회 -- 무시 가능 |
| 순환 import | `genre_schema_builder`는 순수 데이터 모듈, 역방향 의존 없음 (안전) |
| LLM 심사 비용 증가 | Flash 1회/프로젝트, ~$0.002. 무시 가능 |
