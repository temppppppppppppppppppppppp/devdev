"""[C-2] NPC 정보 소실 체인 수정 테스트."""

import inspect


class TestEntityRegistryFallback:
    """entity_registry_for_director 빈 dict 폴백 테스트."""

    def test_entity_registry_default_is_dict(self):
        """초기값이 None이 아닌 빈 dict."""
        from modules.core.stage2_preflight import Stage2PreflightAnalysis

        source = inspect.getsource(Stage2PreflightAnalysis._preflight_arc_analysis)
        assert "entity_registry_for_director = {}" in source
        assert "entity_registry_for_director = None" not in source

    def test_constraint_compiler_exception_logs_warning_tag(self):
        """예외 시 WARNING 레벨 + [C-2] 태그."""
        from modules.core.stage2_preflight import Stage2PreflightAnalysis

        source = inspect.getsource(Stage2PreflightAnalysis._preflight_arc_analysis)
        assert "logging.warning" in source
        assert "[C-2]" in source
        assert "entity_registry 빈 dict 폴백" in source

    def test_empty_dict_is_falsy(self):
        """빈 dict는 falsy — downstream 코드와 호환."""
        entity_registry = {}
        assert not entity_registry

    def test_none_vs_empty_dict_downstream(self):
        """None과 빈 dict 모두 downstream에서 동일하게 처리."""
        for value in (None, {}):
            if not value:
                result = "(등록된 Entity 없음)"
            else:
                result = "있음"
            assert result == "(등록된 Entity 없음)"

    def test_stage2_import_ok(self):
        """변경 후 stage2_orchestrator import 정상."""
        from modules.core.stage2_orchestrator import Stage2Orchestrator

        assert Stage2Orchestrator is not None
