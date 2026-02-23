"""retrieval_mode routing unit tests (TF8-I-2, TF8R-1)."""

import unittest.mock as mock

from modules.core.stage4_context_builder import Stage4ContextBuilder


def _make_ctx():
    """Minimal Stage4 context mock."""
    ctx = mock.MagicMock()
    ctx.ui.log = mock.MagicMock()
    return ctx


def _make_plan(episode_num=5):
    """Minimal retrieval plan mock."""
    slot = mock.MagicMock()
    slot.priority = 2
    slot.source = "vec_memory"
    slot.category = "general"
    slot.query = "test query"
    slot.max_chars = 0

    plan = mock.MagicMock()
    plan.episode_num = episode_num
    plan.slots = [slot]
    return plan


def _make_memory():
    """Minimal vector-memory mock."""
    mem = mock.MagicMock()
    mem.retrieve_hybrid_context.return_value = "hybrid result"
    mem.retrieve_multi_query_context.return_value = "dense result"
    mem._fts_search.return_value = [{"ep_num": 1, "summary": "sparse summary"}]
    return mem


class TestRetrievalModeRouting:
    def test_hybrid_mode_calls_retrieve_hybrid_context(self):
        """retrieval_mode=hybrid calls retrieve_hybrid_context."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "hybrid" if "retrieval_mode" in k else d,
        ):
            builder._execute_retrieval_plan(plan)

        ctx.memory.retrieve_hybrid_context.assert_called_once()
        ctx.memory.retrieve_multi_query_context.assert_not_called()

    def test_sparse_mode_calls_fts_search(self):
        """retrieval_mode=sparse calls _fts_search."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "sparse" if "retrieval_mode" in k else d,
        ):
            builder._execute_retrieval_plan(plan)

        ctx.memory._fts_search.assert_called_once()
        ctx.memory.retrieve_hybrid_context.assert_not_called()

    def test_invalid_mode_falls_back_to_dense(self):
        """invalid retrieval_mode falls back to retrieve_multi_query_context."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "unknown_mode" if "retrieval_mode" in k else d,
        ):
            builder._execute_retrieval_plan(plan)

        ctx.memory.retrieve_multi_query_context.assert_called_once()
        ctx.memory.retrieve_hybrid_context.assert_not_called()

    def test_arc_no_propagated_to_hybrid(self):
        """arc_no is propagated to retrieve_hybrid_context."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "hybrid" if "retrieval_mode" in k else d,
        ):
            builder._execute_retrieval_plan(plan, arc_no=3)

        call = ctx.memory.retrieve_hybrid_context.call_args
        assert call.kwargs.get("current_arc_no") == 3, f"current_arc_no=3 not passed: {call}"

    def test_arc_no_propagated_to_dense(self):
        """arc_no is propagated to retrieve_multi_query_context."""
        ctx = _make_ctx()
        builder = Stage4ContextBuilder.__new__(Stage4ContextBuilder)
        builder.ctx = ctx
        ctx.memory = _make_memory()

        plan = _make_plan()
        with mock.patch(
            "modules.core.stage4_context_builder._threshold",
            side_effect=lambda k, d=None: "dense" if "retrieval_mode" in k else d,
        ):
            builder._execute_retrieval_plan(plan, arc_no=5)

        call = ctx.memory.retrieve_multi_query_context.call_args
        assert call.kwargs.get("current_arc_no") == 5, f"current_arc_no=5 not passed: {call}"
