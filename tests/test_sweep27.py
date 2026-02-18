from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from modules.domain.agents.director_auditor import DirectorQualityAuditor


def test_director_auditor_v0128_handles_missing_detailed_feedback_key():
    auditor = DirectorQualityAuditor.__new__(DirectorQualityAuditor)
    auditor._d = SimpleNamespace(client=MagicMock(), genre="wuxia")
    auditor.v0128_orchestrator = MagicMock()
    auditor.v0128_orchestrator.pre_llm = None
    auditor.v0128_orchestrator.validate.return_value = {
        "final_decision": "REJECT",
        "total_score": 35,
        "feedback": "CONTINUITY REJECT: mismatch found",
    }

    result = auditor.audit_manuscript_v0128(ep_num=7, manuscript="원고", validation_context={}, genre="wuxia")

    assert result["decision"] == "REJECT"
    assert "feedback" in result
    assert "CONTINUITY REJECT" in result["feedback"]


def test_stage3_orchestrator_total_planned_ep_has_empty_arcs_guard():
    source = Path("modules/core/stage3_orchestrator.py").read_text(encoding="utf-8")
    assert 'ctx.current_project.arcs[-1].get("ep_end", 50) if ctx.current_project.arcs else 50' in source
