from RESET import _restore_bible_actual_truth


def test_restore_bible_actual_truth_uses_existing_non_martial_hud():
    bible = {"MasterBible": {"FinanceHUD": {"Protagonist": {"actual_truth": {"bank": "old"}}}}}

    restored = _restore_bible_actual_truth(bible, {"bank": "new"})

    assert restored["MasterBible"]["FinanceHUD"]["Protagonist"]["actual_truth"] == {"bank": "new"}
    assert "MartialHUD" not in restored["MasterBible"]
