# Codex Order C-1: SemanticPlotGuard 체인 수정

> 우선순위: 2 / 카테고리: 버그(CRITICAL) / 규모: 소~중 / 위험도: 낮음

---

## 문제 (Bug Chain 1)

SemanticPlotGuard가 "silent feature death" 상태:
1. `main_a.py` L1506-1512: `try/except → self.semantic_plot_guard = None` (bare except)
2. Guard가 생성되더라도 `_client = None` (google-genai 미설치 또는 API KEY 미설정)
3. `stage2_orchestrator.py` 4곳(L968, L1334, L2011, L2193): `getattr(self.app, "semantic_plot_guard", None)` 체크 → guard가 None이면 전체 skip
4. Guard가 존재해도 `_client = None`이면 `index_resolved_plots()` → return 0, `check_new_arc()` → return []
5. **결과: 플롯 중복 감지 0% — 아무 경고도 생성되지 않음**

---

## 수정 전략

**키워드 기반 폴백 가드** 도입: API 클라이언트 없이도 텍스트 매칭으로 기본 중복 감지.

이유:
- 임베딩 기반 시맨틱 비교는 google-genai API 의존 → 환경에 따라 불가
- 완전 비활성보다 키워드 기반이라도 동작하는 게 나음
- 기존 SemanticPlotGuard 인터페이스(index/check/format) 유지

---

## 작업 상세

### Step 1: SemanticPlotGuard에 키워드 폴백 추가

**파일**: `modules/core/semantic_plot_guard.py`

#### 1-a. `__init__` 수정 (L58-64)

**Before**:
```python
def __init__(self, api_key: str = ""):
    self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
    self._client = None
    self._resolved_embeddings: list[dict] = []
    self._init_attempted = False
    self._try_init_client()
```

**After**:
```python
def __init__(self, api_key: str = ""):
    self._api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
    self._client = None
    self._resolved_embeddings: list[dict] = []
    self._resolved_keywords: list[dict] = []  # [C-1] 키워드 폴백 저장소
    self._init_attempted = False
    self._try_init_client()
    if not self._client:
        logging.info("ℹ️ [V63] SemanticPlotGuard: API 미사용 — 키워드 폴백 모드")
```

#### 1-b. `index_resolved_plots` 수정 (L100-135)

**Before** (L110-111):
```python
if not self._client:
    return 0
```

**After**:
```python
if not self._client:
    return self._index_keyword_fallback(resolved_plots)
```

새 메서드 추가 (클래스 끝, L194 아래):

```python
def _index_keyword_fallback(self, resolved_plots: list[dict]) -> int:
    """[C-1] API 없을 때 키워드 기반 인덱싱"""
    indexed = 0
    for rp in resolved_plots:
        plot_name = rp.get("plot", "")
        resolution = rp.get("resolution", "")
        if not plot_name or len(plot_name) < 2:
            continue
        if any(k["plot"] == plot_name for k in self._resolved_keywords):
            continue
        # 핵심 키워드 추출: 2글자 이상 명사/동사구
        keywords = self._extract_keywords(f"{plot_name} {resolution}")
        self._resolved_keywords.append({
            "plot": plot_name,
            "resolution": resolution,
            "keywords": keywords,
        })
        indexed += 1
    if indexed > 0:
        logging.info(f"📊 [V63] SemanticPlotGuard(키워드): {indexed}개 플롯 인덱싱 (총 {len(self._resolved_keywords)}개)")
    return indexed

@staticmethod
def _extract_keywords(text: str) -> set[str]:
    """[C-1] 텍스트에서 핵심 키워드 추출 (2글자 이상)"""
    import re as _re
    # 한글 단어 + 영문 단어 추출
    words = _re.findall(r"[가-힣]{2,}", text) + _re.findall(r"[a-zA-Z]{3,}", text)
    # 불용어 제거
    stopwords = {"에서", "으로", "하고", "하는", "되는", "있는", "없는", "것이", "위해", "통해", "대한"}
    return {w for w in words if w not in stopwords and len(w) >= 2}
```

#### 1-c. `check_new_arc` 수정 (L137-181)

**Before** (L148-149):
```python
if not self._client or not self._resolved_embeddings:
    return []
```

**After**:
```python
if not self._client or not self._resolved_embeddings:
    # [C-1] 키워드 폴백
    if self._resolved_keywords:
        return self._check_keyword_fallback(tactical_doc, new_plot_names)
    return []
```

새 메서드 추가:

```python
def _check_keyword_fallback(self, tactical_doc: str = "", new_plot_names: list[str] | None = None) -> list[dict]:
    """[C-1] 키워드 기반 중복 검사"""
    if not self._resolved_keywords:
        return []

    warnings = []
    # 검사 대상 텍스트 수집
    check_texts = []
    if new_plot_names:
        check_texts.extend(new_plot_names)
    if tactical_doc:
        check_texts.append(tactical_doc[:3000])

    combined_text = " ".join(check_texts)
    new_keywords = self._extract_keywords(combined_text)

    if not new_keywords:
        return []

    for resolved in self._resolved_keywords:
        overlap = new_keywords & resolved["keywords"]
        if len(resolved["keywords"]) == 0:
            continue
        ratio = len(overlap) / len(resolved["keywords"])
        if ratio >= 0.5 and len(overlap) >= 2:
            warnings.append({
                "new_plot": f"키워드 일치: {', '.join(sorted(overlap)[:5])}",
                "similar_to": resolved["plot"],
                "similarity": round(ratio, 3),
            })

    return warnings
```

---

### Step 2: main_a.py 초기화 개선

**파일**: `main_a.py`

**Before** (L1505-1512):
```python
# [V66] SemanticPlotGuard 활성화
try:
    from modules.core.semantic_plot_guard import SemanticPlotGuard

    self.semantic_plot_guard = SemanticPlotGuard(api_key=os.getenv("GOOGLE_API_KEY", ""))
    self.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료")
except Exception:
    self.semantic_plot_guard = None
```

**After**:
```python
# [V66] SemanticPlotGuard 활성화
try:
    from modules.core.semantic_plot_guard import SemanticPlotGuard

    self.semantic_plot_guard = SemanticPlotGuard(api_key=os.getenv("GOOGLE_API_KEY", ""))
    if self.semantic_plot_guard._client:
        self.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료 (임베딩 모드)")
    else:
        self.ui.log("   📊 [V66] SemanticPlotGuard 초기화 완료 (키워드 폴백 모드)")
except Exception as e:
    logging.warning(f"⚠️ [V66] SemanticPlotGuard 초기화 실패: {str(e)[:80]}")
    self.semantic_plot_guard = None
```

핵심: **초기화 실패해도 None이 아닌 인스턴스 유지** (키워드 폴백 모드로 동작).
→ bare except에서 `except Exception as e`로 변경 + 로깅 추가.
→ `self.semantic_plot_guard = None`은 import 자체가 실패하는 극단적 경우에만.

---

### Step 3: stage2_orchestrator.py 가드 조건 개선

**파일**: `modules/core/stage2_orchestrator.py`

4곳의 `getattr(self.app, "semantic_plot_guard", None)` → `self.ctx.semantic_plot_guard` 사용.

**주의**: stage2_orchestrator는 이미 DI 전환 완료. `self.app`은 레거시 참조.
현재 코드에서 `self.app`으로 접근하는 것이 문제인지 확인:
- L968: `getattr(self.app, "semantic_plot_guard", None)` → self.app 사용 (DI 미전환 잔여)
- L1334: 동일
- L2011: 동일
- L2193: 동일 + `_resolved_embeddings`만 체크하는 버그

Stage2Context에 `semantic_plot_guard` 슬롯이 존재하는지 확인 필요.
→ Stage2Context.__slots__에 이미 `semantic_plot_guard`가 있음 (from_app에서 전달).

**수정**:

L968:
```python
# Before:
if _resolved and len(_resolved) >= 2 and getattr(self.app, "semantic_plot_guard", None):
# After:
if _resolved and len(_resolved) >= 2 and self.ctx.semantic_plot_guard:
```

L1334:
```python
# Before:
if getattr(self.app, "semantic_plot_guard", None) and self.ctx.state_tracker.resolved_plots:
# After:
if self.ctx.semantic_plot_guard and self.ctx.state_tracker.resolved_plots:
```

L2011:
```python
# Before:
if getattr(self.app, "semantic_plot_guard", None):
# After:
if self.ctx.semantic_plot_guard:
```

L2193-2194 (4번째 호출 — **오더 보강**):
```python
# Before:
_spg = getattr(self.app, "semantic_plot_guard", None)
if _spg and _spg._resolved_embeddings:
# After:
_spg = self.ctx.semantic_plot_guard
if _spg and (_spg._resolved_embeddings or _spg._resolved_keywords):
```

**주의**: L2194에서 `_resolved_embeddings`만 체크하면 키워드 폴백 모드에서 항상 skip됨.
`_resolved_keywords`도 OR 조건으로 추가해야 키워드 폴백이 실제 동작함.

---

### Step 4: 테스트

**파일**: `tests/test_semantic_plot_guard.py` (신규, ~100줄)

```python
"""[C-1] SemanticPlotGuard 키워드 폴백 + 체인 수정 테스트"""
import pytest
from unittest.mock import patch


class TestKeywordFallbackInit:
    """키워드 폴백 모드 초기화"""

    def test_init_without_genai(self):
        """google-genai 없어도 인스턴스 생성 성공"""
        with patch.dict("sys.modules", {"google": None, "google.genai": None}):
            # 이미 import된 모듈의 _GENAI_AVAILABLE 플래그를 직접 조작
            import modules.core.semantic_plot_guard as spg_mod
            original = spg_mod._GENAI_AVAILABLE
            spg_mod._GENAI_AVAILABLE = False
            try:
                guard = spg_mod.SemanticPlotGuard(api_key="test")
                assert guard._client is None
                assert guard._resolved_keywords == []
            finally:
                spg_mod._GENAI_AVAILABLE = original

    def test_init_without_api_key(self):
        """API 키 없어도 인스턴스 생성 성공"""
        import modules.core.semantic_plot_guard as spg_mod
        guard = spg_mod.SemanticPlotGuard(api_key="")
        assert guard._client is None  # genai 없으므로


class TestKeywordIndexing:
    """키워드 기반 인덱싱"""

    def _make_guard(self):
        import modules.core.semantic_plot_guard as spg_mod
        guard = spg_mod.SemanticPlotGuard.__new__(spg_mod.SemanticPlotGuard)
        guard._client = None
        guard._resolved_embeddings = []
        guard._resolved_keywords = []
        guard._init_attempted = True
        guard._api_key = ""
        return guard

    def test_index_basic(self):
        guard = self._make_guard()
        plots = [
            {"plot": "인수전 완료", "resolution": "주인공이 회사를 인수함"},
            {"plot": "복수 완수", "resolution": "원수를 처치함"},
        ]
        count = guard.index_resolved_plots(plots)
        assert count == 2
        assert len(guard._resolved_keywords) == 2

    def test_index_dedup(self):
        guard = self._make_guard()
        plots = [{"plot": "인수전 완료", "resolution": "주인공이 인수"}]
        guard.index_resolved_plots(plots)
        guard.index_resolved_plots(plots)  # 중복
        assert len(guard._resolved_keywords) == 1

    def test_index_empty_plot_skipped(self):
        guard = self._make_guard()
        plots = [{"plot": "", "resolution": ""}]
        count = guard.index_resolved_plots(plots)
        assert count == 0


class TestKeywordCheck:
    """키워드 기반 중복 검사"""

    def _make_indexed_guard(self):
        import modules.core.semantic_plot_guard as spg_mod
        guard = spg_mod.SemanticPlotGuard.__new__(spg_mod.SemanticPlotGuard)
        guard._client = None
        guard._resolved_embeddings = []
        guard._resolved_keywords = []
        guard._init_attempted = True
        guard._api_key = ""
        guard.index_resolved_plots([
            {"plot": "청풍산장 인수전", "resolution": "주인공이 청풍산장을 인수하여 장주가 됨"},
            {"plot": "흑풍과 복수전", "resolution": "흑풍에게 원수를 갚음"},
        ])
        return guard

    def test_similar_plot_detected(self):
        guard = self._make_indexed_guard()
        warnings = guard.check_new_arc(
            tactical_doc="주인공이 청풍산장 주변에서 인수 작전을 펼친다"
        )
        # "청풍산장"+"인수" 키워드 매칭 기대
        assert len(warnings) >= 1
        assert any("청풍산장" in w["similar_to"] for w in warnings)

    def test_unrelated_plot_no_warning(self):
        guard = self._make_indexed_guard()
        warnings = guard.check_new_arc(
            tactical_doc="주인공이 사막에서 보물을 찾는다"
        )
        assert len(warnings) == 0

    def test_check_with_plot_names(self):
        guard = self._make_indexed_guard()
        warnings = guard.check_new_arc(
            new_plot_names=["흑풍 복수전 재개", "흑풍 원수 처단"]
        )
        assert len(warnings) >= 1

    def test_format_warnings(self):
        guard = self._make_indexed_guard()
        warnings = [{"new_plot": "테스트", "similar_to": "기존", "similarity": 0.85}]
        text = guard.format_warnings(warnings)
        assert "시맨틱 플롯 중복 경고" in text


class TestExtractKeywords:
    """키워드 추출 헬퍼"""

    def test_korean_keywords(self):
        from modules.core.semantic_plot_guard import SemanticPlotGuard
        kw = SemanticPlotGuard._extract_keywords("청풍산장에서 인수전을 벌이다")
        assert "청풍산장" in kw or "인수전" in kw

    def test_stopwords_filtered(self):
        from modules.core.semantic_plot_guard import SemanticPlotGuard
        kw = SemanticPlotGuard._extract_keywords("위해 통해 대한")
        assert len(kw) == 0

    def test_short_words_filtered(self):
        from modules.core.semantic_plot_guard import SemanticPlotGuard
        kw = SemanticPlotGuard._extract_keywords("아 나 그")
        assert len(kw) == 0


class TestMainInitChain:
    """main_a.py 초기화 체인 검증"""

    def test_semantic_plot_guard_not_none_without_api(self):
        """API 없어도 guard 인스턴스는 생성됨 (키워드 모드)"""
        import modules.core.semantic_plot_guard as spg_mod
        guard = spg_mod.SemanticPlotGuard(api_key="")
        assert guard is not None
        # index/check 호출해도 에러 없음
        count = guard.index_resolved_plots([{"plot": "테스트", "resolution": "해결"}])
        assert isinstance(count, int)
        warnings = guard.check_new_arc(tactical_doc="테스트 내용")
        assert isinstance(warnings, list)
```

---

## 검증 게이트

```bash
# Gate 1: 모듈 import
python -c "from modules.core.semantic_plot_guard import SemanticPlotGuard; g = SemanticPlotGuard(); print(f'client={g._client}, kw={len(g._resolved_keywords)}')"

# Gate 2: SovereignApp import
python -c "from main_a import SovereignApp; print('OK')"

# Gate 3: 신규 테스트
set PYTHONIOENCODING=utf-8
pytest tests/test_semantic_plot_guard.py -v

# Gate 4: 기존 회귀
pytest tests/test_stage2_pipeline.py tests/test_stage4_orchestrator.py -v

# Gate 5: pre-commit
pre-commit run --files modules/core/semantic_plot_guard.py main_a.py modules/core/stage2_orchestrator.py tests/test_semantic_plot_guard.py
```

---

## 커밋

```
fix(C-1): add keyword fallback to SemanticPlotGuard (silent feature death chain)

- Add keyword-based fallback when embedding API unavailable
- Fix main_a.py bare except → explicit Exception + logging
- Fix stage2 self.app → self.ctx for semantic_plot_guard access
- Guard instance always created (keyword mode), never None
- Add 14 unit tests for keyword fallback

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## 수정 금지

- 임베딩 기반 코드 변경 금지 (API 있을 때의 기존 동작 유지)
- `SIMILARITY_THRESHOLD`, `EMBED_MODEL` 상수 변경 금지
- stage2_orchestrator의 try/except 구조 변경 금지
- 다른 stage 파일 수정 금지
