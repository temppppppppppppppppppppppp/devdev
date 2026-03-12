from modules.core.pre_director_checklist import CheckSeverity, PreDirectorChecklist
from modules.core.pre_director_manuscript_checker import PreDirectorManuscriptChecker


def test_pre_director_dialogue_ratio_counts_smart_and_corner_quotes():
    checker = PreDirectorManuscriptChecker(PreDirectorChecklist())
    narrative = "서술" * 2000
    dialogue = "“중요한 대사다.” 「이 장면은 이어진다」 " * 6

    items = checker._check_dialogue_ratio(narrative + dialogue)

    assert items
    assert all("0개" not in item.message for item in items if getattr(item, "message", ""))
