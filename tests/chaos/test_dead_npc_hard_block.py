"""[P7-03] Dead NPC hard-block entity check tests.

Verifies that the CRITICAL blocking rule for deceased NPC resurrection
is enforced correctly (action/dialogue triggers REJECT; flashback/recall
patterns are allowed through).
"""

from modules.validation.blocking_validator import BlockingValidator


def _dead_npc_context(name: str, aliases: list | None = None) -> dict:
    """Build a minimal validation context with one deceased NPC."""
    return {
        "encyclopedia": {
            "npcs": [
                {
                    "name": name,
                    "status": "dead",
                    "aliases": aliases or [],
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Test 1: Deceased NPC performing an action results in passed=False
# ---------------------------------------------------------------------------

def test_dead_npc_action_is_hard_blocked():
    validator = BlockingValidator()
    name = "무영"
    # "말했다" is in _ACTION_PATTERNS — must trigger block
    manuscript = f'"{name}이 말했다. 이제 끝이다."'
    context = _dead_npc_context(name)

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is False, "Deceased NPC performing an action must be blocked"
    assert result["check"] == "dead_npc_resurrection"
    assert result["severity"] == "CRITICAL"


def test_dead_npc_walking_action_is_hard_blocked():
    validator = BlockingValidator()
    name = "혈마"
    # "걸어" is in _ACTION_PATTERNS
    manuscript = f"{name}이 천천히 걸어 들어왔다."
    context = _dead_npc_context(name)

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is False
    assert result["severity"] == "CRITICAL"


# ---------------------------------------------------------------------------
# Test 2: Deceased NPC mentioned only in flashback/recall text passes
# ---------------------------------------------------------------------------

def test_dead_npc_flashback_mention_is_allowed():
    validator = BlockingValidator()
    name = "무영"
    # "회상" is in _RECALL_PATTERNS — must be allowed
    manuscript = f"그는 회상 속에서 {name}의 마지막 말을 떠올렸다."
    context = _dead_npc_context(name)

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is True, "Deceased NPC in flashback context must pass"


def test_dead_npc_memory_recall_is_allowed():
    validator = BlockingValidator()
    name = "혈마"
    # "기억" is in _RECALL_PATTERNS
    manuscript = f"그 기억이 떠올랐다. {name}이 살아있을 때의 일이다."
    context = _dead_npc_context(name)

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is True


def test_dead_npc_eulogy_mention_is_allowed():
    validator = BlockingValidator()
    name = "백호"
    # "고인" and "생전에" are in _RECALL_PATTERNS
    manuscript = f"고인 {name}의 생전에 남긴 유언이었다."
    context = _dead_npc_context(name)

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is True


# ---------------------------------------------------------------------------
# Test 3: NPC not in encyclopedia (not tracked as dead) → should pass
# ---------------------------------------------------------------------------

def test_unknown_npc_action_not_blocked():
    validator = BlockingValidator()
    manuscript = "이름모를사람이 말했다. 조심해라."
    context = {"encyclopedia": {"npcs": []}}

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is True


# ---------------------------------------------------------------------------
# Test 4: Deceased NPC via alias — action on alias is also blocked
# ---------------------------------------------------------------------------

def test_dead_npc_alias_action_is_hard_blocked():
    validator = BlockingValidator()
    name = "혈의군주"
    alias = "혈마"
    manuscript = f"{alias}이 외쳤다. 감히!"
    context = _dead_npc_context(name, aliases=[alias])

    result = validator.entity_checks._check_dead_npc_resurrection(manuscript, context)

    assert result["passed"] is False
    assert result["severity"] == "CRITICAL"
