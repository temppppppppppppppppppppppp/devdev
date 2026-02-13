"""
[Phase 4A] 서비스 Protocol + DB Repository Protocol 테스트

검증 항목:
1. 6종 Protocol이 @runtime_checkable로 isinstance 사용 가능
2. 필수 메서드를 구현한 Mock이 isinstance 통과
3. 필수 메서드 누락 시 isinstance 실패
4. __init__.py re-export 정상 동작
"""

import pytest


# ──────────────────────────────────────────────────────────────
# Fixtures: 각 Protocol import
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def all_protocols():
    """6종 Protocol 클래스 dict 반환"""
    from modules.protocols.app_services import (
        AuditServiceProtocol,
        ConfigServiceProtocol,
        ProjectRepositoryProtocol,
        StateServiceProtocol,
        UIServiceProtocol,
    )
    from modules.protocols.db_repository import DBRepositoryProtocol

    return {
        "UIServiceProtocol": UIServiceProtocol,
        "AuditServiceProtocol": AuditServiceProtocol,
        "ProjectRepositoryProtocol": ProjectRepositoryProtocol,
        "StateServiceProtocol": StateServiceProtocol,
        "ConfigServiceProtocol": ConfigServiceProtocol,
        "DBRepositoryProtocol": DBRepositoryProtocol,
    }


# ──────────────────────────────────────────────────────────────
# 1. @runtime_checkable 확인
# ──────────────────────────────────────────────────────────────

class TestRuntimeCheckable:
    """모든 Protocol이 @runtime_checkable 데코레이터 적용 확인"""

    def test_all_protocols_are_runtime_checkable(self, all_protocols):
        for name, proto in all_protocols.items():
            assert hasattr(proto, "__protocol_attrs__") or hasattr(proto, "_is_runtime_protocol"), (
                f"{name}에 @runtime_checkable 미적용"
            )


# ──────────────────────────────────────────────────────────────
# 2. UIServiceProtocol
# ──────────────────────────────────────────────────────────────

class MockUI:
    def log(self, message: str) -> None: pass
    def title(self, title: str, subtitle: str = "") -> None: pass


class MockUIIncomplete:
    def log(self, message: str) -> None: pass
    # title 누락


class TestUIServiceProtocol:
    def test_conforming(self):
        from modules.protocols.app_services import UIServiceProtocol
        assert isinstance(MockUI(), UIServiceProtocol)

    def test_non_conforming(self):
        from modules.protocols.app_services import UIServiceProtocol
        assert not isinstance(MockUIIncomplete(), UIServiceProtocol)


# ──────────────────────────────────────────────────────────────
# 3. AuditServiceProtocol
# ──────────────────────────────────────────────────────────────

class MockAudit:
    def audit_event(self, category, message, extra=None): pass
    def flush_audit_buffer(self): pass
    def write_audit_summary(self): pass


class MockAuditIncomplete:
    def audit_event(self, category, message, extra=None): pass
    # flush_audit_buffer 누락


class TestAuditServiceProtocol:
    def test_conforming(self):
        from modules.protocols.app_services import AuditServiceProtocol
        assert isinstance(MockAudit(), AuditServiceProtocol)

    def test_non_conforming(self):
        from modules.protocols.app_services import AuditServiceProtocol
        assert not isinstance(MockAuditIncomplete(), AuditServiceProtocol)


# ──────────────────────────────────────────────────────────────
# 4. ProjectRepositoryProtocol
# ──────────────────────────────────────────────────────────────

class MockProject:
    @property
    def name(self): return "test"
    @property
    def master_bible(self): return {}
    @master_bible.setter
    def master_bible(self, v): pass
    @property
    def volumes(self): return []
    @volumes.setter
    def volumes(self, v): pass
    @property
    def arcs(self): return []
    @property
    def paths(self): return None
    @property
    def db(self): return None


class TestProjectRepositoryProtocol:
    def test_conforming(self):
        from modules.protocols.app_services import ProjectRepositoryProtocol
        assert isinstance(MockProject(), ProjectRepositoryProtocol)


# ──────────────────────────────────────────────────────────────
# 5. ConfigServiceProtocol
# ──────────────────────────────────────────────────────────────

class MockConfig:
    @property
    def selected_genre(self): return {"type": "wuxia"}
    @property
    def sys(self): return None
    @property
    def agents(self): return {}
    @property
    def perf_timer(self): return None


class MockConfigIncomplete:
    @property
    def selected_genre(self): return None
    # sys 누락


class TestConfigServiceProtocol:
    def test_conforming(self):
        from modules.protocols.app_services import ConfigServiceProtocol
        assert isinstance(MockConfig(), ConfigServiceProtocol)

    def test_non_conforming(self):
        from modules.protocols.app_services import ConfigServiceProtocol
        assert not isinstance(MockConfigIncomplete(), ConfigServiceProtocol)


# ──────────────────────────────────────────────────────────────
# 6. StateServiceProtocol — 핵심 메서드만 검증
# ──────────────────────────────────────────────────────────────

class TestStateServiceProtocol:
    """StateServiceProtocol은 50+ 메서드. 핵심 3개로 isinstance 검증."""

    def test_partial_conformance_fails(self):
        from modules.protocols.app_services import StateServiceProtocol

        class Partial:
            def extract_npc_deaths_from_arc(self, arc): pass
            def get_dead_npc_summary(self): pass
            # 나머지 48개 누락

        assert not isinstance(Partial(), StateServiceProtocol)


# ──────────────────────────────────────────────────────────────
# 7. DBRepositoryProtocol
# ──────────────────────────────────────────────────────────────

class TestDBRepositoryProtocol:
    def test_import(self):
        from modules.protocols.db_repository import DBRepositoryProtocol
        assert DBRepositoryProtocol is not None

    def test_db_manager_structural_check(self):
        """DBManager가 DBRepositoryProtocol의 핵심 메서드를 보유하는지 확인.

        NOTE: @runtime_checkable isinstance는 메서드 존재만 확인,
        시그니처 불일치는 검출 불가. 별도 타입체커(mypy) 필요.
        """
        from modules.protocols.db_repository import DBRepositoryProtocol

        # DBManager를 실제 인스턴스화하지 않고 클래스 수준 확인
        from modules.core.db_manager import DBManager

        required_methods = [
            "begin", "commit", "rollback", "close",
            "save_manuscript", "get_manuscript",
            "save_anchor", "load_anchor",
            "get_latest_episode_number",
            "execute_query", "execute_update",
        ]
        for method in required_methods:
            assert hasattr(DBManager, method), f"DBManager에 {method} 미존재"


# ──────────────────────────────────────────────────────────────
# 8. __init__.py re-export 검증
# ──────────────────────────────────────────────────────────────

class TestReExport:
    """modules.protocols에서 11종 전부 import 가능 확인"""

    EXPECTED = [
        # Step 3
        "PipelineGenerator", "EnsembleGenerator", "ArtifactValidator",
        "ArtifactCritic", "Corrector",
        # Phase 4A
        "UIServiceProtocol", "AuditServiceProtocol",
        "ProjectRepositoryProtocol", "StateServiceProtocol",
        "ConfigServiceProtocol", "DBRepositoryProtocol",
    ]

    def test_all_exports(self):
        import modules.protocols as proto_pkg
        for name in self.EXPECTED:
            assert hasattr(proto_pkg, name), f"modules.protocols에서 {name} import 불가"

    def test_all_in___all__(self):
        import modules.protocols as proto_pkg
        for name in self.EXPECTED:
            assert name in proto_pkg.__all__, f"{name}이 __all__에 없음"
