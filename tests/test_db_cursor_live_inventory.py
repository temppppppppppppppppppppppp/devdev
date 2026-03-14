import ast
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/2026-03-13/db-cursor-live-inventory.json"
SOURCE_PATH = ROOT / "modules/core/db_manager.py"
SHARED_PATTERN = re.compile(r"self\.cursor\.(execute|executemany|fetchone|fetchall)")
REQUIRED_MUST_MIGRATE = {
    "save_anchor",
    "load_anchor",
    "save_llm_call",
    "save_stage_attempt",
    "transaction",
    "reset_after",
    "get_rollback_impact",
}


def _load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _method_text_inventory() -> tuple[dict[str, str], str]:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    lines = source.splitlines()
    module = ast.parse(source)
    methods: dict[str, str] = {}
    for node in ast.walk(module):
        if not isinstance(node, ast.FunctionDef):
            continue
        end_lineno = getattr(node, "end_lineno", node.lineno)
        methods[node.name] = "\n".join(lines[node.lineno - 1 : end_lineno])
    return methods, source


def _source_cursor_sets() -> tuple[dict[str, str], str, set[str], set[str]]:
    methods, source = _method_text_inventory()
    shared = {name for name, text in methods.items() if SHARED_PATTERN.search(text)}
    local = {name for name, text in methods.items() if "self.conn.cursor()" in text}
    return methods, source, shared, local


def _contract_shared_methods(contract: dict) -> set[str]:
    methods: set[str] = set()
    for surface in contract["legacy_shared_cursor_surfaces"]:
        methods.update(surface["methods"])
    return methods


def _contract_must_migrate_methods(contract: dict) -> set[str]:
    methods: set[str] = set()
    for surface in contract["legacy_shared_cursor_surfaces"]:
        if surface["classification"] == "must_migrate":
            methods.update(surface["methods"])
    return methods


def test_db_cursor_live_inventory_matches_db_manager_source() -> None:
    contract = _load_contract()
    _, _, shared, local = _source_cursor_sets()

    assert _contract_shared_methods(contract) == shared
    assert set(contract["current_preferred_local_cursor"]["methods"]) == local
    assert set(contract["source_scan_rules"]["mixed_bootstrap_methods"]) == shared & local
    assert contract["inventory_counts"] == {
        "shared_cursor_methods": len(shared),
        "local_cursor_methods": len(local),
        "mixed_bootstrap_methods": len(shared & local),
    }


def test_db_cursor_live_inventory_freezes_priority_split() -> None:
    contract = _load_contract()
    must_migrate = _contract_must_migrate_methods(contract)
    allowed_temporary: set[str] = set()
    seen: set[str] = set()

    for surface in contract["legacy_shared_cursor_surfaces"]:
        methods = surface["methods"]
        assert methods
        assert len(methods) == len(set(methods))
        assert surface["classification"] in {"allowed_temporary_legacy", "must_migrate"}
        assert surface["rationale"]
        for method in methods:
            assert method not in seen
            seen.add(method)
        if surface["classification"] == "allowed_temporary_legacy":
            allowed_temporary.update(methods)

    assert REQUIRED_MUST_MIGRATE <= must_migrate
    assert set(contract["must_migrate_priority_floor"]) <= must_migrate
    assert "_boot_db" in allowed_temporary
    assert must_migrate.isdisjoint(allowed_temporary)


def test_db_cursor_live_inventory_policy_aligns_with_source_note() -> None:
    contract = _load_contract()
    methods, source, shared, _ = _source_cursor_sets()

    assert "should NOT be used" in source
    assert "local cursor" in source
    assert contract["policy"]["preferred_pattern"] in {
        "with self._lock: cur = self.conn.cursor()",
    }
    assert contract["policy"]["legacy_pattern"] == "self.cursor.execute(...)"

    for method_name in contract["current_preferred_local_cursor"]["methods"]:
        assert "self.conn.cursor()" in methods[method_name]

    for method_name in REQUIRED_MUST_MIGRATE:
        assert method_name in shared
        assert SHARED_PATTERN.search(methods[method_name])
