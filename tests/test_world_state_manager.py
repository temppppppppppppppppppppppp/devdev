"""Focused persistence contract tests for WorldStateManager."""

from modules.core.world_state import WorldStateManager


class _WorldStateDB:
    def load_anchor(self, _name):
        return None

    def save_anchor(self, _name, _payload):
        return None


class _BrokenWorldStateDB(_WorldStateDB):
    def save_anchor(self, _name, _payload):
        raise RuntimeError("world write fail")


def test_save_sets_degraded_contract_on_failure():
    manager = WorldStateManager(_BrokenWorldStateDB())

    result = manager.save()

    assert result is False
    assert manager.last_save_ok is False
    assert manager.last_save_error == "world write fail"


def test_save_clears_degraded_contract_on_success():
    manager = WorldStateManager(_WorldStateDB())
    manager.last_save_ok = False
    manager.last_save_error = "stale"

    result = manager.save()

    assert result is True
    assert manager.last_save_ok is True
    assert manager.last_save_error is None
