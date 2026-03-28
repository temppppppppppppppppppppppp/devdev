from modules.core.prompt_loader import PromptLoader


_LOCAL_REJECT_FIX_PACK_RULE = (
    'REJECT 판정이면서 `fix_scope`가 `"inplace"` 또는 `"partial"`이면 구조화된 `fix_pack`을 반드시 함께 작성하라.'
)
_FIX_PACK_FIELDS_RULE = (
    '`patch_targets`, `must_fix`, `do_not_regress`, `success_condition`, `target_kind`를 모두 채워라.'
)


def _get_director_prompt(key: str) -> str:
    loader = PromptLoader()
    loader.invalidate_cache("director")
    return loader.get_raw("director", key) or ""


def test_ensemble_variable_prompt_requires_fix_pack_for_reject_local_scopes():
    prompt = _get_director_prompt("ENSEMBLE_VARIABLE_PROMPT")

    assert _LOCAL_REJECT_FIX_PACK_RULE in prompt
    assert _FIX_PACK_FIELDS_RULE in prompt


def test_ensemble_selection_prompt_requires_fix_pack_for_reject_local_scopes():
    prompt = _get_director_prompt("ENSEMBLE_SELECTION_PROMPT")

    assert _LOCAL_REJECT_FIX_PACK_RULE in prompt
    assert _FIX_PACK_FIELDS_RULE in prompt
