"""[C-1] SemanticPlotGuard 키워드 폴백 + 체인 수정 테스트."""

import inspect


class TestKeywordFallbackInit:
    """키워드 폴백 모드 초기화."""

    def test_init_without_genai_flag(self):
        """genai 비활성화 시 client 없이 키워드 모드로 초기화."""
        import modules.core.semantic_plot_guard as spg_mod

        original = spg_mod._GENAI_AVAILABLE
        spg_mod._GENAI_AVAILABLE = False
        try:
            guard = spg_mod.SemanticPlotGuard(api_key="test")
            assert guard._client is None
            assert guard._resolved_keywords == []
        finally:
            spg_mod._GENAI_AVAILABLE = original

    def test_init_without_api_key(self, monkeypatch):
        """API 키가 없어도 인스턴스는 생성됨."""
        import modules.core.semantic_plot_guard as spg_mod

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        guard = spg_mod.SemanticPlotGuard(api_key="")
        assert guard is not None
        assert guard._resolved_keywords == []


class TestKeywordIndexing:
    """키워드 기반 인덱싱."""

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
        guard.index_resolved_plots(plots)
        assert len(guard._resolved_keywords) == 1

    def test_index_empty_plot_skipped(self):
        guard = self._make_guard()
        plots = [{"plot": "", "resolution": ""}]
        count = guard.index_resolved_plots(plots)
        assert count == 0


class TestKeywordCheck:
    """키워드 기반 중복 검사."""

    def _make_indexed_guard(self):
        import modules.core.semantic_plot_guard as spg_mod

        guard = spg_mod.SemanticPlotGuard.__new__(spg_mod.SemanticPlotGuard)
        guard._client = None
        guard._resolved_embeddings = []
        guard._resolved_keywords = []
        guard._init_attempted = True
        guard._api_key = ""
        guard.index_resolved_plots(
            [
                {"plot": "청풍산장 인수전", "resolution": "주인공이 청풍산장을 인수하여 장주가 됨"},
                {"plot": "흑풍과 복수전", "resolution": "흑풍에게 원수를 갚음"},
            ]
        )
        return guard

    def test_similar_plot_detected(self):
        guard = self._make_indexed_guard()
        warnings = guard.check_new_arc(tactical_doc="주인공이 청풍산장 주변에서 인수 작전을 펼친다")
        assert len(warnings) >= 1
        assert any("청풍산장" in warning["similar_to"] for warning in warnings)

    def test_unrelated_plot_no_warning(self):
        guard = self._make_indexed_guard()
        warnings = guard.check_new_arc(tactical_doc="주인공이 사막에서 보물을 찾는다")
        assert len(warnings) == 0

    def test_check_with_plot_names(self):
        guard = self._make_indexed_guard()
        warnings = guard.check_new_arc(new_plot_names=["흑풍 복수전 재개", "흑풍 원수 처단"])
        assert len(warnings) >= 1

    def test_format_warnings(self):
        guard = self._make_indexed_guard()
        warnings = [{"new_plot": "테스트", "similar_to": "기존", "similarity": 0.85}]
        text = guard.format_warnings(warnings)
        assert "시맨틱 플롯 중복 경고" in text


class TestExtractKeywords:
    """키워드 추출 헬퍼."""

    def test_korean_keywords(self):
        from modules.core.semantic_plot_guard import SemanticPlotGuard

        keywords = SemanticPlotGuard._extract_keywords("청풍산장에서 인수전을 벌이다")
        assert "청풍산장" in keywords or "인수전" in keywords

    def test_stopwords_filtered(self):
        from modules.core.semantic_plot_guard import SemanticPlotGuard

        keywords = SemanticPlotGuard._extract_keywords("위해 통해 대한")
        assert len(keywords) == 0

    def test_short_words_filtered(self):
        from modules.core.semantic_plot_guard import SemanticPlotGuard

        keywords = SemanticPlotGuard._extract_keywords("아 나 그")
        assert len(keywords) == 0


class TestChainWiring:
    """main/stage2 체인 연결 검증."""

    def test_semantic_plot_guard_not_none_without_api(self, monkeypatch):
        """API 없어도 guard 인스턴스는 사용 가능."""
        import modules.core.semantic_plot_guard as spg_mod

        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        guard = spg_mod.SemanticPlotGuard(api_key="")
        assert guard is not None
        count = guard.index_resolved_plots([{"plot": "테스트", "resolution": "해결"}])
        assert isinstance(count, int)
        warnings = guard.check_new_arc(tactical_doc="테스트 내용")
        assert isinstance(warnings, list)

    def test_stage2_uses_ctx_and_keyword_fallback_condition(self):
        """4번째 호출에서 self.ctx + _resolved_keywords OR 조건 사용."""
        from modules.core.stage2_finalizer import Stage2Finalizer

        source = inspect.getsource(Stage2Finalizer)
        assert "_spg = self.ctx.semantic_plot_guard" in source
        assert "(_spg._resolved_embeddings or _spg._resolved_keywords)" in source
