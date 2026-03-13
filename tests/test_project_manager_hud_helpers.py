from modules.core.project_manager import ProjectContext


def test_project_context_reads_actual_truth_from_genre_specific_hud():
    ctx = ProjectContext.__new__(ProjectContext)
    ctx.genre = "investment"

    bible_root = {"FinanceHUD": {"Protagonist": {"actual_truth": {"bank": "프랙탈브릿지"}}}}

    actual_truth = ProjectContext._get_protagonist_actual_truth_node(ctx, bible_root)

    assert actual_truth == {"bank": "프랙탈브릿지"}


def test_project_context_uses_genre_specific_npc_hud_key():
    ctx = ProjectContext.__new__(ProjectContext)
    ctx.genre = "investment"

    assert ProjectContext._get_npc_hud_key(ctx) == "NPC_Business_Profile"
